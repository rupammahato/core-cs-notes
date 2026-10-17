from pathlib import Path
from search import Search, dispatch, estimates
from runtime import Error
from verification import Fixture

BASE = Path(__file__).resolve().parent
with Fixture('S9',BASE) as h:
    s = h.store(Search)
    def events(doc):
        return [r[0] for r in s.db.execute('SELECT id FROM events WHERE doc=? ORDER BY version',(doc,))]
    def index_all():
        for row in s.db.execute('SELECT id FROM events WHERE done=0 ORDER BY id').fetchall():
            s.apply(row[0])
    def ids(result):
        return [x['id'] for x in result['items']]
    doc = s.create('t1','alice','create','Scheduler basics','Durable queue and leases',False)
    h.check('outbox','source and event committed',len(events(doc['id']))==1)
    h.check('outbox','new source absent before projection',s.find('t1','alice','Scheduler')['returned']==0)
    h.check('outbox','event projects source',s.apply(events(doc['id'])[0])=='applied')
    h.check('outbox','event replay',s.apply(events(doc['id'])[0])=='replay')
    h.check('retrieval','owner can search private source',ids(s.find('t1','alice','scheduler'))==[doc['id']])
    h.check('authorization','other reader filtered',s.find('t1','bob','scheduler')['returned']==0)
    h.check('authorization','other tenant filtered',s.find('t2','alice','scheduler')['returned']==0)
    h.check('identity','create replay does not duplicate',s.create('t1','alice','create','Scheduler basics','Durable queue and leases',False)['id']==doc['id'])
    h.denied('identity','changed create conflicts',409,lambda:s.create('t1','alice','create','Other','',False))
    h.denied('identity','nonowner edit hidden',404,lambda:s.edit('t1','bob',doc['id'],1,'Other',''))
    h.denied('identity','nonowner share hidden',404,lambda:s.grant('t1','bob',doc['id'],'carol',True))
    s.grant('t1','alice',doc['id'],'bob',True)
    h.check('authorization','grant enables search immediately',ids(s.find('t1','bob','scheduler'))==[doc['id']])
    h.check('retrieval','title token autocomplete',ids(s.find('t1','bob','sched','prefix'))==[doc['id']])
    h.check('retrieval','body token does not autocomplete title',s.find('t1','bob','durab','prefix')['returned']==0)
    h.check('retrieval','full text body term',ids(s.find('t1','bob','durable'))==[doc['id']])
    s.grant('t1','alice',doc['id'],'bob',False)
    h.check('authorization','revocation hides full result and snippet',s.find('t1','bob','scheduler')=={'items':[],'returned':0,'has_more':False})
    h.check('authorization','revocation hides suggestion',s.find('t1','bob','sched','prefix')['returned']==0)
    h.check('authorization','revocation needs no index mutation',s.db.execute('SELECT count(*) FROM search WHERE doc=?',(doc['id'],)).fetchone()[0]==1)
    h.observations['permissions']={'private_owner_results':1,'private_other_reader_results':0,'after_grant_results':1,
        'after_revoke':s.find('t1','bob','scheduler'),'after_revoke_prefix_results':0,
        'projection_row_still_present':True,'cross_tenant_results':0}
    revised = s.edit('t1','alice',doc['id'],1,'Worker architecture','New body')
    h.check('versions','source version advances',revised['version']==2)
    h.check('versions','old title hidden before update indexed',s.find('t1','alice','scheduler')['returned']==0)
    h.check('versions','new title absent until projected',s.find('t1','alice','worker')['returned']==0)
    h.denied('versions','stale expected version conflicts',409,lambda:s.edit('t1','alice',doc['id'],1,'Lost edit',''))
    s.apply(events(doc['id'])[1])
    h.check('versions','new version searchable',ids(s.find('t1','alice','worker'))==[doc['id']])
    h.check('identity','create replay after edit returns same identity',s.create('t1','alice','create','Scheduler basics','Durable queue and leases',False)['version']==2)
    deleted = s.delete('t1','alice',doc['id'])
    h.check('versions','delete is source tombstone',deleted['deleted']==1 and deleted['version']==3)
    h.check('authorization','delete hides stale indexed title',s.find('t1','alice','worker')['returned']==0)
    h.check('authorization','delete hides prefix',s.find('t1','alice','work','prefix')['returned']==0)
    h.check('versions','delete replay no extra event',s.delete('t1','alice',doc['id'])['version']==3 and len(events(doc['id']))==3)
    h.denied('versions','deleted source cannot edit',410,lambda:s.edit('t1','alice',doc['id'],3,'Revived',''))
    s.apply(events(doc['id'])[2])
    h.check('versions','delete removes projection row',s.db.execute('SELECT count(*) FROM search WHERE doc=?',(doc['id'],)).fetchone()[0]==0)
    late = s.create('t1','alice','late','Old title','',True)
    s.edit('t1','alice',late['id'],1,'New title','')
    newest = events(late['id'])[1]
    s.apply(newest)
    h.check('versions','out of order old upsert fenced',s.apply(events(late['id'])[0])=='stale')
    h.check('versions','latest title preserved',ids(s.find('t1','bob','new'))==[late['id']])
    resurrect = s.create('t1','alice','resurrect','Ghost title','',True)
    s.delete('t1','alice',resurrect['id'])
    s.apply(events(resurrect['id'])[1])
    h.check('versions','old upsert after delete fenced',s.apply(events(resurrect['id'])[0])=='stale')
    h.check('versions','no resurrection',s.find('t1','bob','ghost')['returned']==0)
    h.observations['version_fences']={'old_title_before_index_update':0,'new_title_before_index_update':0,
        'new_title_after_index_update':1,'deleted_title_before_delete_event':0,
        'old_upsert_after_newer_version':'stale','old_upsert_after_tombstone':'stale','resurrection_results':0}
    high = s.create('t1','alice','rank_title','Ledger','Small guide',True)
    low = s.create('t1','alice','rank_body','Basics','Ledger',True)
    secret = s.create('t1','alice','secret','Ledger private','Ledger ledger',False)
    unicode = s.create('t1','alice','unicode','Café notes','Unicode tokenizer',True)
    index_all()
    ranked = ids(s.find('t1','bob','ledger'))
    h.check('retrieval','selected title boost judgement',ranked==[high['id'],low['id']])
    h.check('authorization','ACL before top k retains authorized hit',ids(s.find('t1','bob','ledger',limit=1))==[high['id']])
    h.check('retrieval','authorized has more',s.find('t1','bob','ledger',limit=1)['has_more'])
    h.check('authorization','no unfiltered count exposed',set(s.find('t1','bob','ledger'))=={'items','returned','has_more'})
    h.check('retrieval','unicode61 accent behavior',ids(s.find('t1','bob','cafe'))==[unicode['id']])
    h.check('retrieval','literal syntax cannot select all',s.find('t1','bob','ledger OR ghost')['returned']==0)
    h.check('retrieval','wildcard syntax is not accepted as operator',s.find('t1','bob','led*')['returned']==0)
    h.check('retrieval','prefix mode supplies controlled operator',high['id'] in ids(s.find('t1','bob','led','prefix')))
    for name,action in [('empty query',lambda:s.find('t1','bob','')),('punctuation only',lambda:s.find('t1','bob','***')),
        ('too many terms',lambda:s.find('t1','bob','a b c d e')),('oversize limit',lambda:s.find('t1','bob','a',limit=21)),
        ('boolean limit',lambda:s.find('t1','bob','a',limit=True)),('unknown mode',lambda:s.find('t1','bob','a','regex')),
        ('oversize title',lambda:s.create('t1','alice','oversize','a'*121,'',True)),
        ('nonboolean visibility',lambda:s.create('t1','alice','visibility','title','',1))]:
        h.denied('bounds',name,400,action)
    h.observations['retrieval']={'selected_corpus_title_hit_before_body_hit':ranked==[high['id'],low['id']],
        'authorized_returned_with_limit_one':1,'has_more':True,'unicode61_cafe_matches_accented_title':True,
        'raw_FTS_OR_interpreted_as_operator':False,'autocomplete_scope':'title token prefix','universal_relevance_claim':False}
    before = s.db.execute('SELECT count(*) FROM documents').fetchone()[0]
    s.db.execute("CREATE TRIGGER stop_outbox BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','source and idempotency rollback with outbox',lambda:s.create('t1','alice','fault','Rollback','',True),
        lambda:s.db.execute('SELECT count(*) FROM documents').fetchone()[0]==before
        and s.db.execute("SELECT count(*) FROM creates WHERE operation='fault'").fetchone()[0]==0)
    s.db.execute('DROP TRIGGER stop_outbox')
    fault = s.create('t1','alice','fault','Rollback','',True)
    event = events(fault['id'])[0]
    s.db.execute("CREATE TRIGGER stop_watermark BEFORE INSERT ON watermarks BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','projection event and watermark rollback together',lambda:s.apply(event),
        lambda:s.db.execute('SELECT count(*) FROM search WHERE doc=?',(fault['id'],)).fetchone()[0]==0
        and s.db.execute('SELECT done FROM events WHERE id=?',(event,)).fetchone()[0]==0)
    s.db.execute('DROP TRIGGER stop_watermark')
    results = h.race(lambda:Search(h.root/'main.sqlite'),[lambda x:x.apply(event),lambda x:x.apply(event)])
    h.check('concurrency','competing projectors converge',sorted(results)==['applied','replay'])
    h.check('concurrency','single projection after competing apply',s.db.execute('SELECT count(*) FROM search WHERE doc=?',(fault['id'],)).fetchone()[0]==1)
    pending = s.create('t1','alice','rebuild','Rebuild latest','',True)
    s.edit('t1','alice',pending['id'],1,'Rebuild current','')
    rebuilt = s.rebuild('t1')
    h.check('rebuild','rebuild indexes source current version',pending['id'] in ids(s.find('t1','bob','current')))
    h.check('rebuild','old pending event cannot overwrite rebuild',s.apply(events(pending['id'])[0])=='stale')
    h.check('rebuild','same version pending event ignored',s.apply(events(pending['id'])[1])=='stale')
    h.check('rebuild','rebuild preserves tombstones',s.find('t1','alice','ghost')['returned']==0)
    s.close()
    s = h.store(Search)
    h.check('rebuild','index survives reopen',pending['id'] in ids(s.find('t1','bob','current')))
    h.observations['rollback_rebuild']={'source_outbox_rollback_tested':True,'projection_watermark_event_rollback_tested':True,
        'competing_projector_results':sorted(results),'rebuild_source_rows':rebuilt,
        'late_events_after_rebuild':'stale','local_atomic_rebuild':True,'online_blue_green_rebuild':False}
    port = h.serve(lambda:Search(h.root/'main.sqlite'),dispatch)
    response = h.request(port,'POST','/docs',{'title':'HTTP Autocomplete','body':'Endpoint notes','public':False},headers={'Idempotency-Key':'http'})
    oid = response[2]['id']
    s.apply(events(oid)[0])
    h.check('http','document create',response[0]==201)
    h.check('http','authenticated full text query',h.request(port,'GET','/search?q=autocomplete')[2]['returned']==1)
    h.check('http','authenticated title prefix',h.request(port,'GET','/search?q=auto&mode=prefix&limit=1')[2]['returned']==1)
    h.check('http','private other reader hidden',h.request(port,'GET','/search?q=autocomplete',token='lesson-bob')[2]['returned']==0)
    h.check('http','tenant boundary',h.request(port,'GET','/search?q=autocomplete',token='lesson-other')[2]['returned']==0)
    h.check('http','anonymous query denied',h.request(port,'GET','/search?q=autocomplete',token=None)[0]==401)
    h.check('http','duplicate query parameter rejected',h.request(port,'GET','/search?q=a&q=b')[0]==400)
    h.check('http','invalid numeric limit rejected',h.request(port,'GET','/search?q=a&limit=NaN')[0]==400)
    h.check('http','unknown query parameter rejected',h.request(port,'GET','/search?q=a&tenant=t2')[0]==400)
    h.check('http','owner grants reader',h.request(port,'PUT','/docs/'+oid+'/grants/bob')[0]==200)
    h.check('http','granted reader can query',h.request(port,'GET','/search?q=autocomplete',token='lesson-bob')[2]['returned']==1)
    h.check('http','owner revokes reader',h.request(port,'DELETE','/docs/'+oid+'/grants/bob')[0]==200)
    h.check('http','revoked reader cannot autocomplete',h.request(port,'GET','/search?q=auto&mode=prefix',token='lesson-bob')[2]['returned']==0)
    h.check('http','delete hides index immediately',h.request(port,'DELETE','/docs/'+oid)[0]==200 and h.request(port,'GET','/search?q=autocomplete')[2]['returned']==0)
    h.observations['http_contract']={'create':201,'full_text_owner_results':1,'prefix_owner_results':1,
        'private_other_reader_results':0,'cross_tenant_results':0,'anonymous':401,
        'duplicate_query_parameter':400,'revoked_prefix_results':0,'deleted_before_index_event_results':0,'real_loopback_HTTP':True}
    h.observations['estimates'] = estimates()
h.report('Actual SQLite FTS5 full text and title-token prefix search; canonical ACL, tenant and version checks before top-k results, versioned outbox, stale/tombstone fences, rollback, two projector calls, local atomic rebuild and real HTTP. Selected relevance judgements only; no external search cluster, semantic ranking, online reindex or performance benchmark.')
