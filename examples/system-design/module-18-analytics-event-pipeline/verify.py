from pathlib import Path
import json
from pipeline import Pipeline, timestamp, iso, WINDOW, LATENESS, dispatch, estimates
from verification import Fixture

BASE = Path(__file__).resolve().parent
START = timestamp('2026-10-18T00:00:00Z')


def event(eid,subject='u1',kind='page_view',at=10,channel='organic'):
    return {'id':eid,'subject':subject,'kind':kind,'channel':channel,
        'event_time':iso(START+at),'schema_version':1}


def organic(item,tenant='t1'):
    return item.dashboard(tenant,START,1)['rows'][0]


with Fixture('S13',BASE) as h:
    s = h.store(Pipeline)
    s.setup('t1')
    s.setup('t2')
    h.check('time','window start aligned',START%WINDOW==0)
    h.check('time','explicit offsets normalize to same UTC second',timestamp('2026-10-18T05:30:10+05:30')==START+10)
    for name,value in [('naive timestamp','2026-10-18T00:00:00'),('invalid date','2026-02-30T00:00:00Z'),
        ('fractional timestamp','2026-10-18T00:00:00.1Z'),('nonstring timestamp',True)]:
        h.denied('time',name,400,lambda value=value:timestamp(value))
    payload = [event('view'),event('signup1',kind='signup',at=20),event('act1',kind='activation',at=30),
        event('signup2','u2','signup',40),event('orphan','u9','activation',50),
        event('act1_again',kind='activation',at=35),event('signup1_again',kind='signup',at=21)]
    accepted = s.append('t1','alice',payload,START+600)
    h.check('intake','durable batch acceptance',len(accepted)==7 and all(not e['replay'] for e in accepted))
    h.check('intake','source accepted before projection',s.dashboard('t1',START,1)['pending_events']==7 and organic(s)['page_view_events']==0)
    h.check('intake','idempotent batch replay',all(e['replay'] for e in s.append('t1','alice',payload,START+601)))
    equivalent = dict(payload[0],event_time='2026-10-18T05:30:10+05:30')
    h.check('intake','normalized-time replay matches intent',s.append('t1','alice',[equivalent],START+602)[0]['seq']==accepted[0]['seq'])
    h.denied('intake','changed same event identity conflicts',409,lambda:s.append('t1','alice',[dict(payload[0],subject='other')],START+602))
    s.append('t2','alice',[payload[0]],START+600)
    h.check('scope','event identity scoped to tenant',s.db.execute("SELECT count(*) FROM events WHERE event_id='view'").fetchone()[0]==2)
    s.append('t1','bob',[event('producer_local','u4')],START+600)
    h.check('scope','independent producer identity',s.append('t1','carol',[event('producer_local','u5')],START+600)[0]['replay'] is False)
    for name,values in [('empty batch',[]),('large batch',[event(str(i)) for i in range(17)]),
        ('schema boolean',[dict(event('bad'),schema_version=True)]),('unsupported version',[dict(event('bad'),schema_version=2)]),
        ('unknown kind',[dict(event('bad'),kind='purchase')]),('unknown channel',[dict(event('bad'),channel='unbounded')]),
        ('nested unrecognized field',[dict(event('bad'),properties={'nested':[1,2]})]),
        ('future skew',[event('future',at=1000)])]:
        h.denied('validation',name,400,lambda values=values:s.append('t1','alice',values,START+600))
    before = s.db.execute('SELECT count(*) FROM events').fetchone()[0]
    h.denied('atomicity','changed identity rolls back earlier batch insert',409,
        lambda:s.append('t1','alice',[event('rolledback'),dict(payload[0],subject='changed')],START+600))
    h.check('atomicity','no partial event from conflicted batch',s.db.execute('SELECT count(*) FROM events').fetchone()[0]==before)
    first = s.process('t1',2,START+610)
    h.check('projection','bounded batch advances two records',first['processed']==2 and first['last_seq']==accepted[1]['seq'])
    h.check('projection','partial dashboard reports pending source',s.dashboard('t1',START,1)['pending_events']==7)
    h.denied('watermarks','cannot finalize ahead of pending local source',409,lambda:s.watermark('t1',START+419,START+620))
    h.denied('rebuild','cannot rebuild ahead of pending source',409,lambda:s.rebuild('t1',START+620))
    results = h.race(lambda:Pipeline(h.root/'main.sqlite'),[lambda x:x.process('t1',32,START+620),lambda x:x.process('t1',32,START+620)])
    h.check('concurrency','competing workers drain each row once',sum(x['processed'] for x in results)==7)
    h.check('concurrency','frontiers converge after competing batches',s.dashboard('t1',START,1)['pending_events']==0)
    row = organic(s)
    h.check('metrics','all page views counted',row['page_view_events']==3)
    h.check('metrics','duplicate semantic signups distinct by subject',row['signed_up_subjects']==2)
    h.check('metrics','only signup cohort activation enters numerator',row['activated_signup_subjects']==1 and row['activation_rate']==0.5)
    h.check('metrics','undefined denominator is null',s.dashboard('t1',START,1)['rows'][1]['activation_rate'] is None)
    h.check('scope','other tenant projection still independent',organic(s,'t2')['page_view_events']==0)
    s.process('t2',32,START+620)
    h.check('scope','other tenant has only its event',organic(s,'t2')['page_view_events']==1)
    s.append('t1','alice',[event('act2','u2','activation',25)],START+650)
    s.process('t1',32,START+650)
    h.check('late_data','out of order within mutable window corrects metric',organic(s)['activation_rate']==1.0)
    s.watermark('t1',START+419,START+700)
    h.check('watermarks','one second before final boundary still mutable',not organic(s)['finalized_under_policy'])
    s.append('t1','alice',[event('allowed_late','u2',at=50)],START+701)
    s.process('t1',32,START+701)
    h.check('late_data','allowed late event updates prior window',organic(s)['page_view_events']==4)
    s.watermark('t1',START+420,START+800)
    h.check('watermarks','finalizes at end plus lateness boundary',organic(s)['finalized_under_policy'])
    h.denied('watermarks','watermark cannot regress',409,lambda:s.watermark('t1',START+419,START+800))
    h.denied('watermarks','watermark cannot exceed server now',400,lambda:s.watermark('t1',START+901,START+900))
    late = s.append('t1','alice',[event('too_late','u3','signup',60)],START+810)[0]
    s.process('t1',32,START+810)
    h.check('late_data','too late receipt retained outside aggregate',s.db.execute('SELECT decision FROM events WHERE seq=?',(late['seq'],)).fetchone()[0]=='late_excluded')
    h.check('late_data','finalized metric not silently changed',organic(s)['signed_up_subjects']==2 and organic(s)['page_view_events']==4)
    h.observations['time_metrics']={'UTC_window_start':iso(START),'window_seconds':WINDOW,'allowed_lateness_seconds':LATENESS,
        'signup_subjects':2,'activated_signup_subjects_before_late':1,'activation_rate_before_late':0.5,
        'activation_rate_after_in_window_late':1.0,'page_views_after_allowed_late':4,
        'too_late_decision':'late_excluded','empty_cohort_rate':None,'watermark_is_trusted_fixture_control':True}
    before = organic(s)
    generation = s.rebuild('t1',START+820)
    h.check('rebuild','new generation activated',generation==2 and s.checkpoint('t1')['generation']==2)
    h.check('rebuild','rebuild preserves included decisions after watermark advance',organic(s)==before)
    h.check('rebuild','rebuild retains late exclusion',s.db.execute("SELECT count(*) FROM effects WHERE tenant='t1' AND generation=2 AND decision='late_excluded'").fetchone()[0]==1)
    s.db.execute("CREATE TRIGGER stop_generation BEFORE UPDATE ON active BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','rebuild aggregate and generation switch rollback',lambda:s.rebuild('t1',START+830),
        lambda:s.checkpoint('t1')['generation']==2 and s.db.execute("SELECT count(*) FROM checkpoints WHERE tenant='t1' AND generation=3").fetchone()[0]==0)
    s.db.execute('DROP TRIGGER stop_generation')
    h.check('rebuild','failed rebuild preserves serving metrics',organic(s)==before)
    h.observations['rebuild']={'active_generation_after_rebuild':2,'metric_values_preserved':True,
        'historical_inclusion_decisions_reused':True,'late_exclusions_preserved':1,
        'failed_generation_flip_rolled_back':True,'online_external_rebuild':False}
    atomic = h.store(Pipeline,'atomic')
    atomic.setup('t1')
    atomic.append('t1','alice',[event('one'),event('two','u2','signup',20)],START+600)
    atomic.db.execute("CREATE TRIGGER stop_frontier BEFORE UPDATE ON checkpoints BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','counts receipts decisions and frontier rollback together',lambda:atomic.process('t1',32,START+610),
        lambda:atomic.checkpoint('t1')['last_seq']==0 and atomic.db.execute('SELECT count(*) FROM effects').fetchone()[0]==0
        and atomic.db.execute('SELECT count(*) FROM counts').fetchone()[0]==0 and atomic.db.execute('SELECT count(*) FROM events WHERE decision IS NOT NULL').fetchone()[0]==0)
    atomic.db.execute('DROP TRIGGER stop_frontier')
    h.check('atomicity','retry after rollback processes accepted source',atomic.process('t1',32,START+611)['processed']==2)
    duplicate = event('race_id','u7',at=500)
    receipts = h.race(lambda:Pipeline(h.root/'main.sqlite'),[
        lambda x:x.append('t1','alice',[duplicate],START+900)[0],lambda x:x.append('t1','alice',[duplicate],START+900)[0]])
    h.check('concurrency','competing intake shares one durable identity',receipts[0]['seq']==receipts[1]['seq'] and sorted(x['replay'] for x in receipts)==[False,True])
    s.process('t1',32,START+901)
    h.observations['recovery']={'projection_batch_rollback_tested':True,'accepted_events_survive_projection_fault':True,
        'competing_source_insert_rows':1,'competing_projection_calls':2,'effects_and_frontier_atomic':True}
    forget = s.forget('t1','u1',START+910)
    h.check('privacy','forget removes retained source rows',forget['removed_event_rows']==5 and s.db.execute("SELECT count(*) FROM events WHERE tenant='t1' AND subject='u1'").fetchone()[0]==0)
    h.check('privacy','forget removes subjects across old generations',s.db.execute("SELECT count(*) FROM participants WHERE tenant='t1' AND subject='u1'").fetchone()[0]==0)
    h.check('privacy','aggregate rebuilt with remaining cohort',organic(s)['signed_up_subjects']==1 and organic(s)['activated_signup_subjects']==1)
    h.denied('privacy','erasure marker blocks old event replay',410,lambda:s.append('t1','alice',[payload[0]],START+920))
    h.check('privacy','privacy operation scoped to tenant',s.db.execute("SELECT count(*) FROM events WHERE tenant='t2' AND subject='u1'").fetchone()[0]==1)
    h.check('privacy','forget replay no extra deletion',s.forget('t1','u1',START+921)['removed_event_rows']==0)
    h.observations['privacy']={'removed_source_rows':forget['removed_event_rows'],'remaining_signup_cohort':1,
        'remaining_activated_cohort':1,'erased_subject_replay_status':410,'other_tenant_untouched':True,
        'old_generation_participant_rows_removed':True,'backups_or_disk_securely_erased':False}
    s.close()
    s = h.store(Pipeline)
    h.check('persistence','frontier and projection survive reopen',s.checkpoint('t1')['generation']==2 and organic(s)['signed_up_subjects']==1)
    h.denied('bounds','limit boolean rejected',400,lambda:s.process('t1',True,START+950))
    h.denied('bounds','dashboard rejects unaligned start',400,lambda:s.dashboard('t1',START+1,1))
    h.denied('bounds','dashboard rejects unbounded span',400,lambda:s.dashboard('t1',START,13))
    h.check('metrics','dashboard includes freshness and definition',s.dashboard('t1',START,1)['metric_definition']=='same_window_same_channel_signup_activation_v1' and s.dashboard('t1',START,1)['projection_updated_at']==START+921)
    port = h.serve(lambda:Pipeline(h.root/'main.sqlite'),lambda item,u,m,p,raw,hd:dispatch(item,u,m,p,raw,hd,lambda:START+1200))
    response = h.request(port,'POST','/events',{'events':[event('http','http_subject',at=1000)]})
    h.check('http','durable intake accepted',response[0]==202 and len(response[2]['accepted'])==1)
    h.check('http','equivalent HTTP retry same sequence',h.request(port,'POST','/events',{'events':[event('http','http_subject',at=1000)]})[2]['accepted'][0]['seq']==response[2]['accepted'][0]['seq'])
    path = '/dashboard?start='+str(START+900)+'&buckets=1'
    h.check('http','dashboard pending marker before worker',h.request(port,'GET',path)[2]['pending_events']==1)
    s.process('t1',32,START+1201)
    dash = h.request(port,'GET',path)
    h.check('http','materialized dashboard endpoint',dash[0]==200 and dash[2]['rows'][0]['page_view_events']==1)
    h.check('http','foreign tenant aggregate isolated',h.request(port,'GET',path,token='lesson-other')[2]['rows'][0]['page_view_events']==0)
    h.check('http','anonymous dashboard denied',h.request(port,'GET',path,token=None)[0]==401)
    h.check('http','client tenant override rejected',h.request(port,'POST','/events',{'events':[],'tenant':'t2'})[0]==400)
    h.check('http','duplicate query parameter rejected',h.request(port,'GET',path+'&buckets=2')[0]==400)
    h.check('http','unbounded query span rejected',h.request(port,'GET','/dashboard?start='+str(START)+'&buckets=99')[0]==400)
    h.check('http','worker control not public',h.request(port,'POST','/process',{})[0]==404)
    h.check('http','privacy control not public',h.request(port,'DELETE','/subjects/u2')[0]==404)
    h.check('http','cache policy explicit',dash[1]['Cache-Control']=='no-store')
    h.observations['http_contract']={'POST_events':202,'dashboard':200,'anonymous':401,'tenant_override':400,
        'duplicate_query_parameter':400,'public_worker_control':404,'public_privacy_control':404,
        'metric_freshness_reported':True,'real_loopback_HTTP':True,'Kafka_Beam_or_browser_dashboard_executed':False}
    h.observations['estimates'] = estimates()
h.report('Local SQLite durable event batches, scoped immutable event identity, offset checkpoint/effect atomicity, event-time cohorts, explicit watermark/late policy, generation rebuild, subject erasure marker, four competing calls, fault rollback/reopen and actual aggregate HTTP. No Kafka/Beam cluster, automatic watermark estimation, browser chart, external spreadsheet connector, secure disk/backup erasure or production capacity claim.')
proof_path = BASE/'verification-results.json'
proof = json.loads(proof_path.read_text(encoding='utf-8'))
proof['verified_date'] = '2026-10-18'
proof_path.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
