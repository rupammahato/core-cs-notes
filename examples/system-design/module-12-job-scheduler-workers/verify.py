from pathlib import Path
import sqlite3
from scheduler import Scheduler, dispatch, estimates
from verification import Fixture

BASE = Path(__file__).resolve().parent
with Fixture('S7',BASE) as h:
    s = h.store(Scheduler)
    job = s.enqueue('t1','alice','first',7,100,20000)
    h.check('identity','durable pending job',job['state']=='pending' and job['attempts']==0)
    h.check('identity','equivalent create replay',s.enqueue('t1','alice','first',7,100,20000)['id']==job['id'])
    h.denied('identity','changed job conflicts',409,lambda:s.enqueue('t1','alice','first',8,100,20000))
    h.denied('identity','owner hidden',404,lambda:s.owned('t1','bob',job['id']))
    h.denied('identity','tenant hidden',404,lambda:s.owned('t2','alice',job['id']))
    for name,args in [('boolean delta',(True,0,100)),('zero delta',(0,0,100)),('negative due',(1,-1,100)),('empty interval',(1,10,10))]:
        h.denied('identity',name,400,lambda args=args:s.enqueue('t1','alice','bad',*args))
    h.denied('identity','reserved occurrence namespace',400,lambda:s.enqueue('t1','alice','schedule_fake',1,0,100))
    h.check('leases','not before due',s.claim(99) is None)
    first = s.claim(100)
    h.check('leases','first claim bounded',first['id']==job['id'] and first['lease_until']==2100 and first['attempts']==1)
    h.check('leases','cannot acknowledge missing effect',not s.ack(first,101))
    h.check('effects','effect applied',s.effect(first,101)=='applied')
    h.check('effects','same lease effect replay',s.effect(first,102)=='replay')
    # Deliberately omit ACK, close/reopen the store; not an actual killed process.
    s.close()
    s = h.store(Scheduler)
    h.check('effects','committed effect survives reopen',s.owned('t1','alice',job['id'])['effect_applied']==1)
    second = s.claim(2100)
    h.check('leases','expired claim has new token',second['token']!=first['token'] and second['attempts']==2)
    h.check('leases','stale worker fenced',s.effect(first,2101)=='stale' and not s.ack(first,2101))
    h.check('effects','reclaimed effect deduplicated',s.effect(second,2101)=='replay')
    h.check('effects','reclaimed acknowledgement succeeds',s.ack(second,2102))
    h.check('effects','counter incremented once',s.db.execute('SELECT value FROM counters').fetchone()[0]==7)
    h.check('leases','terminal worker cannot renew',s.renew(second,2103) is False)
    h.denied('effects','cancel cannot undo effect',409,lambda:s.cancel('t1','alice',job['id']))
    h.observations['effect_recovery']={'effect_before_ack':'applied','reopen_after_omitting_ack':True,
        'new_claim_token':second['token']!=first['token'],'old_worker_effect':'stale',
        'new_worker_effect':'replay','counter':7,'final_state':s.owned('t1','alice',job['id'])['state'],
        'actual_process_kill':False}
    r = h.store(Scheduler,'retry')
    original = r.enqueue('t1','alice','retry',1,0,30000)
    active = r.claim(0)
    h.check('retries','bounded renewal',r.renew(active,1000,5000)==6000)
    h.check('retries','renewal hard duration cap',r.renew(active,2000,5000)==6000)
    h.check('retries','cannot revive expired lease',r.renew(active,6000) is False)
    active = r.claim(6000)
    h.denied('retries','reject excessive retry delay',400,lambda:r.fail(active,6001,True,1001))
    h.check('retries','retry scheduled',r.fail(active,6001,True,1000))
    h.check('identity','retry preserves original intent replay',r.enqueue('t1','alice','retry',1,0,30000)['id']==original['id'])
    h.check('retries','delayed retry not claimed early',r.claim(7000) is None)
    active = r.claim(7001)
    h.check('retries','third attempt allowed',active['attempts']==3)
    h.check('retries','third failure terminal',r.fail(active,7002,True) and r.owned('t1','alice',active['id'])['state']=='failed')
    cancelled = r.enqueue('t1','alice','cancel',1,8000,20000)
    running = r.claim(8000)
    h.check('retries','running cancellation',r.cancel('t1','alice',cancelled['id'])['state']=='cancelled')
    h.check('retries','cancel fences running effect',r.effect(running,8001)=='stale')
    h.check('retries','cancel replay terminal',r.cancel('t1','alice',cancelled['id'])['state']=='cancelled')
    due = r.enqueue('t1','alice','deadline',2,9000,9500)
    running = r.claim(9000)
    h.check('leases','deadline bounds lease',running['lease_until']==9500)
    h.check('effects','effect before deadline',r.effect(running,9499)=='applied')
    r.claim(9500)
    final = r.owned('t1','alice',due['id'])
    h.check('effects','failed can have committed effect',final['state']=='failed' and final['effect_applied']==1)
    h.check('leases','deadline boundary rejects ack',not r.ack(running,9500))
    h.observations['retry_deadline']={'max_attempts':3,'renewal_hard_cap_ms':6000,
        'deadline_state':final['state'],'deadline_effect_applied':bool(final['effect_applied']),
        'failed_proves_no_effect':False,'original_intent_replay_after_retry':True}
    f = h.store(Scheduler,'fairness')
    for tenant in ('a','b','c'):
        for n in range(2):
            f.enqueue(tenant,'alice','j'+str(n),1,0,20000)
    raced = h.race(lambda:Scheduler(h.root/'fairness.sqlite'),[lambda x:x.claim(0),lambda x:x.claim(0)])
    h.check('concurrency','two claims admit distinct tenants',len({x['tenant'] for x in raced})==2)
    h.check('concurrency','global inflight bound',f.claim(0) is None)
    for x in raced:
        f.effect(x,1)
        f.ack(x,2)
    third = f.claim(3)
    h.check('concurrency','round robin advances to third tenant',third['tenant']=='c')
    h.check('concurrency','tenant cannot hold second live slot',f.claim(3)['tenant']!='c')
    h.observations['admission']={'first_two_tenants':sorted(x['tenant'] for x in raced),
        'third_tenant':third['tenant'],'global_cap':2,'tenant_cap':1,'concurrent_claims':2}
    z = h.store(Scheduler,'atomic')
    row = z.enqueue('t1','alice','atomic',9,0,30000)
    run = z.claim(0)
    z.db.execute("CREATE TRIGGER stop_counter BEFORE INSERT ON counters BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','effect marker rolls back with counter',lambda:z.effect(run,1),
        lambda:z.db.execute('SELECT count(*) FROM effects').fetchone()[0]==0)
    z.db.execute('DROP TRIGGER stop_counter')
    h.check('atomicity','effect recovers after rollback',z.effect(run,2)=='applied' and z.ack(run,3))
    schedule = z.schedule('t2','alice','hourly',1,1000,1000)
    h.check('scheduling','tick not early',z.tick(999)==[])
    z.db.execute("CREATE TRIGGER stop_job BEFORE INSERT ON jobs BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','occurrence and frontier rollback',lambda:z.tick(4500),
        lambda:z.db.execute('SELECT next_due FROM schedules WHERE id=?',(schedule,)).fetchone()[0]==1000)
    z.db.execute('DROP TRIGGER stop_job')
    ids = z.tick(4500)
    occurrence = z.owned('t2','alice',ids[0])
    h.check('scheduling','misses coalesced to newest slot',len(ids)==1 and occurrence['due']==4000)
    h.check('scheduling','tick replay creates none',z.tick(4500)==[])
    h.check('scheduling','next frontier persisted',z.db.execute('SELECT next_due FROM schedules').fetchone()[0]==5000)
    h.check('scheduling','next interval is new occurrence',z.tick(5000)[0]!=ids[0])
    h.observations['scheduling']={'missed_slots':[1000,2000,3000,4000],'coalesced_created_slots':[4000],
        'next_due_after_first_tick':5000,'tick_replay_created':0,'occurrence_frontier_rollback_tested':True}
    port = h.serve(lambda:Scheduler(h.root/'main.sqlite'),dispatch)
    response = h.request(port,'POST','/jobs',{'delta':3,'due':0,'deadline':10000},headers={'Idempotency-Key':'http'})
    hid = response[2]['id']
    h.check('http','accepted durable create',response[0]==202 and response[2]['state']=='pending')
    h.check('http','cache prevention',response[1]['Cache-Control']=='no-store')
    h.check('http','owner GET',h.request(port,'GET','/jobs/'+hid)[0]==200)
    h.check('http','other owner hidden',h.request(port,'GET','/jobs/'+hid,token='lesson-bob')[0]==404)
    h.check('http','other tenant hidden',h.request(port,'GET','/jobs/'+hid,token='lesson-other')[0]==404)
    h.check('http','anonymous denied',h.request(port,'GET','/jobs/'+hid,token=None)[0]==401)
    h.check('http','worker API not public',h.request(port,'POST','/claim',{})[0]==404)
    h.check('http','unknown field rejected',h.request(port,'POST','/jobs',{'delta':1,'due':0,'deadline':2,'tenant':'t2'},headers={'Idempotency-Key':'x'})[0]==400)
    h.check('http','malformed body rejected',h.request(port,'POST','/jobs',b'{')[0]==400)
    h.check('http','owner cancellation',h.request(port,'DELETE','/jobs/'+hid)[2]['state']=='cancelled')
    h.observations['http_contract']={'POST_jobs':202,'GET_owner':200,'GET_other_owner':404,
        'GET_other_tenant':404,'anonymous':401,'public_claim_endpoint':404,'cancel_state':'cancelled','real_loopback_HTTP':True}
    h.observations['estimates'] = estimates()
h.report('Local SQLite scheduling, coalesced interval occurrences, two-slot tenant admission, fenced leases, local transactional effect dedupe, bounded retries, rollback and actual loopback HTTP. Explicit time inputs; no cron daemon, broker, external effect or production load test.')
