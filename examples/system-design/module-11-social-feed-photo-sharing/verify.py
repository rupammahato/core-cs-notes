from feed import Feed, CURSOR_SECRET, dispatch, estimates
from verification import Fixture
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).resolve().parent
with Fixture('S6',BASE) as h:
    s = h.store(Feed)
    s.media_state('t1','photo','alice',1,'quarantined')
    h.denied('publication','quarantined media cannot publish',409,lambda:s.publish('t1','alice','early','photo',1,'caption'))
    s.media_state('t1','photo','alice',1,'ready')
    h.denied('publication','another owner cannot attach the media',409,lambda:s.publish('t1','bob','steal','photo',1,'caption'))
    h.denied('publication','another tenant cannot attach the media',409,lambda:s.publish('t2','alice','steal','photo',1,'caption'))
    h.denied('publication','wrong media version rejected',409,lambda:s.publish('t1','alice','wrong','photo',2,'caption'))
    h.denied('publication','caption limit enforced',400,lambda:s.publish('t1','alice','long','photo',1,'x'*281))
    h.denied('publication','invalid client key rejected',400,lambda:s.publish('t1','alice','../key','photo',1,''))
    s.follow('t1','bob','alice')
    first = s.publish('t1','alice','one','photo',1,'first')
    h.check('publication','post and pending push job commit together',s.db.execute('SELECT count(*) FROM jobs').fetchone()[0]==1)
    h.check('publication','same operation replays original post',s.publish('t1','alice','one','photo',1,'first')['id']==first['id'])
    h.denied('publication','changed post intent conflicts',409,lambda:s.publish('t1','alice','one','photo',1,'changed'))
    h.check('fanout','push feed can lag durable post publication',s.page('t1','bob')['posts']==[])
    h.check('fanout','author sees own push post without worker',s.page('t1','alice')['posts'][0]['id']==first['id'])
    h.check('fanout','batch inserts follower pointer',s.fanout(first['id'])==1)
    h.check('fanout','follower sees published post after batch',s.page('t1','bob')['posts'][0]['id']==first['id'])
    h.check('fanout','completed worker replay adds no duplicates',s.fanout(first['id'])==0 and s.db.execute("SELECT count(*) FROM inbox WHERE viewer='bob'").fetchone()[0]==1)
    rollback = h.store(Feed,'post-rollback')
    rollback.media_state('t1','photo','alice',1,'ready')
    rollback.db.execute("CREATE TRIGGER fail_job BEFORE INSERT ON jobs BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('publication','failed job insert rolls back published post',lambda:rollback.publish('t1','alice','op','photo',1,'photo'),
        lambda:rollback.db.execute('SELECT count(*) FROM posts').fetchone()[0]==0 and rollback.db.execute('SELECT count(*) FROM inbox').fetchone()[0]==0)
    batched = h.store(Feed,'batched')
    batched.media_state('t1','photo','alice',1,'ready')
    for viewer in ('bob','carol','dave','erin'):
        batched.follow('t1',viewer,'alice')
    post = batched.publish('t1','alice','op','photo',1,'batched')
    batched.db.execute("CREATE TRIGGER fail_pointer BEFORE INSERT ON inbox WHEN NEW.viewer='carol' BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('fanout','batch failure rolls back earlier pointer and cursor',lambda:batched.fanout(post['id'],2),
        lambda:batched.db.execute('SELECT cursor FROM jobs').fetchone()[0]=='' and batched.db.execute('SELECT count(*) FROM inbox').fetchone()[0]==1)
    batched.db.execute('DROP TRIGGER fail_pointer')
    h.check('fanout','retry resumes intact batch frontier',batched.fanout(post['id'],2)==2)
    batched.follow('t1','aaron','alice')
    h.check('fanout','new follower before batch cursor gets historical backfill',batched.page('t1','aaron')['posts'][0]['id']==post['id'])
    batches = h.race(lambda:Feed(h.root/'batched.sqlite'),[
        lambda item:item.fanout(post['id'],2),lambda item:item.fanout(post['id'],2)])
    h.check('concurrency','competing workers share one durable cursor',sum(batches)==2)
    h.check('concurrency','fanout and backfill have unique pointers',batched.db.execute('SELECT count(*) FROM inbox').fetchone()[0]==6)
    h.check('fanout','batch job eventually reaches done',batched.db.execute('SELECT state FROM jobs').fetchone()[0]=='done')
    s.author_mode('t1','carol','pull')
    s.media_state('t1','celebrity-photo','carol',1,'ready')
    s.follow('t1','bob','carol')
    pulled = s.publish('t1','carol','pull-one','celebrity-photo',1,'pull')
    h.check('hybrid','pull post creates no per-follower fanout job',s.db.execute('SELECT 1 FROM jobs WHERE post=?',(pulled['id'],)).fetchone() is None)
    merged = s.page('t1','bob')['posts']
    h.check('hybrid','read merges pull and pushed candidates once',[row['id'] for row in merged]==[pulled['id'],first['id']])
    s.author_mode('t1','alice','pull')
    h.check('hybrid','mode changes do not rewrite old posts',s.db.execute('SELECT mode FROM posts WHERE id=?',(first['id'],)).fetchone()[0]=='push')
    newest = s.publish('t1','alice','two','photo',1,'second')
    h.check('hybrid','new posts can adopt changed author mode',newest['mode']=='pull')
    h.observations['fanout'] = {'push_visible_before_batch':False,'push_visible_after_batch':True,
        'partial_batch_rollback_tested':True,'cursor_backfill_gap_closed':True,
        'parallel_batch_sizes_sorted':sorted(batches),'unique_inbox_pointers_after_backfill':6,
        'pull_post_creates_fanout_job':False,'mode_frozen_per_post':True,'ranking_engine_implemented':False}
    page = s.page('t1','bob',1)
    upper = page['high_water']
    s.publish('t1','alice','three','photo',1,'new arrival')
    second_page = s.page('t1','bob',50,page['next_cursor'])
    h.check('pagination','keyset continuation has no first-page duplicate',all(row['id']!=page['posts'][0]['id'] for row in second_page['posts']))
    h.check('pagination','snapshot high-water excludes new arrivals',second_page['high_water']==upper and all(row['id']<=upper for row in second_page['posts']))
    h.check('pagination','new first page discovers new arrival',s.page('t1','bob',1)['posts'][0]['id']>upper)
    h.denied('pagination','cursor is viewer scoped',403,lambda:s.page('t1','carol',1,page['next_cursor']))
    h.denied('pagination','cursor is tenant scoped',403,lambda:s.page('t2','bob',1,page['next_cursor']))
    h.denied('pagination','tampered cursor signature rejected',400,lambda:s.page('t1','bob',1,page['next_cursor']+'x'))
    h.denied('pagination','invalid page size rejected',400,lambda:s.page('t1','bob',0))
    s.follow('t1','bob','alice',False)
    h.check('visibility','unfollow hides stale push pointers',all(row['author']!='alice' for row in s.page('t1','bob')['posts']))
    h.check('visibility','pointer may physically remain after unfollow',s.db.execute('SELECT 1 FROM inbox WHERE viewer=? AND post=?',('bob',first['id'])).fetchone() is not None)
    s.follow('t1','bob','alice')
    h.check('visibility','refollow backfills retained pushed history',first['id'] in [row['id'] for row in s.page('t1','bob')['posts']])
    s.block('t1','alice','bob')
    h.check('visibility','author block hides push and pull posts',all(row['author']!='alice' for row in s.page('t1','bob')['posts']))
    s.block('t1','bob','alice',False)
    h.check('visibility','viewer cannot remove authors reverse block',all(row['author']!='alice' for row in s.page('t1','bob')['posts']))
    s.block('t1','alice','bob',False)
    s.block('t1','bob','carol')
    h.check('visibility','viewer block also applies to pull candidates',all(row['author']!='carol' for row in s.page('t1','bob')['posts']))
    s.block('t1','bob','carol',False)
    s.media_state('t1','photo','alice',1,'deleted')
    h.check('visibility','deleted media hides referencing posts',all(row['author']!='alice' for row in s.page('t1','bob')['posts']))
    s.media_state('t1','photo','alice',2,'ready')
    h.check('visibility','new media version does not reactivate old pins',all(row['author']!='alice' for row in s.page('t1','bob')['posts']))
    replacement = s.publish('t1','alice','replacement','photo',2,'replacement')
    h.check('visibility','explicit new post can pin ready replacement',replacement['id'] in [row['id'] for row in s.page('t1','bob')['posts']])
    s.delete('t1','alice',replacement['id'])
    h.check('visibility','post deletion hides current candidate',replacement['id'] not in [row['id'] for row in s.page('t1','bob')['posts']])
    h.check('visibility','original create replay does not resurrect deletion',s.publish('t1','alice','replacement','photo',2,'replacement')['state']=='deleted')
    h.denied('visibility','other owner cannot delete post',404,lambda:s.delete('t1','bob',first['id']))
    h.check('visibility','another tenant feed has no candidates',s.page('t2','bob')['posts']==[])
    h.observations['visibility_and_pagination'] = {'pointer_is_authorization':False,
        'unfollow_filters_stale_pointer':True,'bidirectional_block_checked':True,
        'media_version_replacement_reactivates_old_post':False,'delete_replay_resurrects_post':False,
        'new_insert_enters_old_cursor_window':False,'cursor_cross_viewer_status':403,
        'caption_or_media_already_delivered_retracted':False}
    racing = h.store(Feed,'racing')
    racing.media_state('t1','photo','alice',1,'ready')
    same = h.race(lambda:Feed(h.root/'racing.sqlite'),[
        lambda item:item.publish('t1','alice','same','photo',1,'same'),lambda item:item.publish('t1','alice','same','photo',1,'same')])
    h.check('concurrency','concurrent publish retries share one post ID',same[0]['id']==same[1]['id'])
    h.check('concurrency','concurrent publication creates one job',racing.db.execute('SELECT count(*) FROM jobs').fetchone()[0]==1)
    h.observations['concurrency'] = {'competing_worker_calls':4,'parallel_fanout_extra_recipients':sum(batches),
        'equivalent_post_calls':2,'created_posts':1,'created_jobs':1,'winner_order_assumed':False}
    web = h.store(Feed,'http')
    web.media_state('t1','photo','alice',1,'ready')
    port = h.serve(lambda:Feed(h.root/'http.sqlite'),dispatch)
    h.check('http','feed requires authentication',h.request(port,'GET','/feed',token='')[0]==401)
    h.check('http','follow endpoint derives viewer from credential',h.request(port,'PUT','/follows/alice',token='lesson-bob')[0]==200)
    value = {'client_id':'web','media_id':'photo','media_version':1,'caption':'photo'}
    created = h.request(port,'POST','/posts',value)
    h.check('http','real post creation accepts owned ready media',created[0]==201)
    h.check('http','other owner media attachment denied',h.request(port,'POST','/posts',value,token='lesson-bob')[0]==409)
    h.check('http','unknown tenant field cannot choose authority',h.request(port,'POST','/posts',{**value,'tenant':'t2'})[0]==400)
    web.fanout(created[2]['id'])
    feed = h.request(port,'GET','/feed?limit=1',token='lesson-bob')
    h.check('http','real feed returns canonical post after fanout',feed[0]==200 and feed[2]['posts'][0]['id']==created[2]['id'])
    h.check('http','private feed response is no-store',feed[1]['Cache-Control']=='no-store')
    h.check('http','other tenant sees empty feed',h.request(port,'GET','/feed',token='lesson-other')[2]['posts']==[])
    h.check('http','invalid limit rejected',h.request(port,'GET','/feed?limit=0')[0]==400)
    h.check('http','invalid cursor rejected',h.request(port,'GET','/feed?cursor=forged')[0]==400)
    h.request(port,'PUT','/blocks/alice',token='lesson-bob')
    h.check('http','real block immediately filters next local feed request',h.request(port,'GET','/feed',token='lesson-bob')[2]['posts']==[])
    h.check('http','foreign-owner delete is hidden',h.request(port,'DELETE','/posts/'+str(created[2]['id']),token='lesson-bob')[0]==404)
    h.check('http','owner deletion succeeds',h.request(port,'DELETE','/posts/'+str(created[2]['id']))[0]==200)
    h.observations['http_contract'] = {'create_status':201,'wrong_media_owner_status':409,
        'feed_status':200,'private_cache_control':'no-store','invalid_cursor_status':400,
        'next_feed_after_block_empty':True,'foreign_delete_status':404,
        'photo_bytes_or_S3_projection_integration_implemented':False}
    h.observations['estimates'] = estimates()
    h.check('estimates','push amplification units',estimates()['hypothetical_push_pointer_writes_per_second']==40000)
    h.check('estimates','celebrity pointer logical bytes',estimates()['logical_pointer_MB_for_one_celebrity_post']==64)
    h.check('estimates','no throughput claim',not estimates()['measured_capacity'])
h.report('Bounded local SQLite hybrid chronological feed and actual loopback JSON HTTP. Media state is a trusted metadata fixture, not image decoding, S3 integration or signed image delivery. No recommendation/ranking engine, production auth/TLS, distributed fanout/cache, global revocation or load benchmark. Visibility is rechecked for each local request; already delivered pages cannot be retracted.')
