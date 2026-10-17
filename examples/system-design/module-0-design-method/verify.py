"""Verify planning arithmetic, offline objectives and real SQLite baseline invariants."""
from pathlib import Path
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
import json
import math
import platform
import sqlite3
import tempfile
from estimates import Workload, estimate, sensitivity
from objectives import assess
from baseline import Notes, Conflict, NotFound, StaleVersion

BASE=Path(__file__).resolve().parent
checks=[]
observations={}
def check(group,name,condition):
    if not condition:
        raise AssertionError(name)
    checks.append({'group':group,'name':name,'passed':True})
def rejects(group,name,kind,fn):
    try:
        fn()
    except kind:
        check(group,name,True)
    else:
        raise AssertionError(name+': expected rejection')
def near(left,right):
    return math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-12)

w=Workload()
result=estimate(w)
check('estimates','Daily reads and writes use independent action counts',result['reads_per_day']==3000000 and result['writes_per_day']==300000)
check('estimates','Average QPS uses the full stated day',near(result['average_qps'],3300000/86400))
check('estimates','Peak multiplier applies to aggregate request rate',near(result['assumed_peak_qps'],result['average_qps']*8))
check('estimates','Milliseconds convert to seconds for mean inflight',near(result['mean_in_flight_at_assumed_peak'],result['assumed_peak_qps']*0.15))
check('estimates','Updates are not all treated as new retained records',result['new_records_per_day']==120000 and result['retained_records']==43800000)
check('estimates','Logical storage follows created record count',result['logical_storage_bytes']==89702400000)
check('estimates','Physical copy/overhead arithmetic explicit',result['planned_physical_storage_bytes']==403660800000)
check('estimates','Decimal GB and binary GiB remain distinct',result['planned_physical_storage_decimal_gb']==403.6608 and near(result['planned_physical_storage_gib'],403660800000/2**30))
check('estimates','Response bandwidth includes read/write payload assumptions',result['peak_response_payload_bytes_per_second']==1152000)
check('estimates','Capacity target leaves assumed utilization headroom',result['target_qps_per_instance']==65)
check('estimates','Round up healthy capacity then add one failure reserve',result['healthy_instances']==5 and result['fleet_for_one_failed_instance']==6)
s=sensitivity(w)
check('estimates','Twice users doubles rate, inflight and storage',all(near(s['double_users'][field],2*s['baseline'][field]) for field in ('assumed_peak_qps','mean_in_flight_at_assumed_peak','planned_physical_storage_bytes')))
check('estimates','Twice mean time doubles inflight without changing rate',near(s['double_mean_time']['mean_in_flight_at_assumed_peak'],2*s['baseline']['mean_in_flight_at_assumed_peak']) and s['double_mean_time']['assumed_peak_qps']==s['baseline']['assumed_peak_qps'])
check('estimates','Twice record size changes storage without changing requests',s['double_record_size']['planned_physical_storage_bytes']==2*s['baseline']['planned_physical_storage_bytes'] and s['double_record_size']['assumed_peak_qps']==s['baseline']['assumed_peak_qps'])
check('estimates','Read-only scenario has no new retained notes',estimate(replace(w,writes_per_user_day=0))['retained_records']==0)
rejects('estimates','Zero active users rejected',ValueError,lambda:estimate(replace(w,users=0)))
rejects('estimates','Zero total workload rejected',ValueError,lambda:estimate(replace(w,reads_per_user_day=0,writes_per_user_day=0)))
rejects('estimates','Invalid creation fraction rejected',ValueError,lambda:estimate(replace(w,creation_fraction_of_writes=1.1)))
rejects('estimates','Full utilization target rejected',ValueError,lambda:estimate(replace(w,target_utilization=1)))
rejects('estimates','NaN assumption rejected',ValueError,lambda:estimate(replace(w,mean_request_ms=float('nan'))))
rejects('estimates','Fractional physical copy count rejected',ValueError,lambda:estimate(replace(w,physical_copies=2.5)))
rejects('estimates','Boolean user count rejected',ValueError,lambda:estimate(replace(w,users=True)))
rejects('estimates','Peak below average rejected',ValueError,lambda:estimate(replace(w,peak_factor=0.5)))
observations['estimates']=result
observations['sensitivity']=s

def sample(duration=100,correct=True,eligible=True,violates=False):
    return {'eligible':eligible,'correct':correct,'violates_invariant':violates,'duration_ms':duration}
normal=assess([sample() for _ in range(99)]+[sample(201)])
critical=assess([sample() for _ in range(99)]+[sample(100,correct=False,violates=True)])
check('objectives','Inclusive deadline boundary succeeds',assess([sample(200)],goal=1)['good_events']==1)
check('objectives','Slow event consumes one good-event failure',normal['good_events']==99 and normal['bad_events']==1)
check('objectives','Goal met exactly at declared fraction',normal['objective_met'] and normal['good_fraction']==0.99)
check('objectives','Fast incorrect response is not good',assess([sample(100,correct=False)])['good_events']==0)
check('objectives','Timeout missing duration is not good',assess([sample(None)])['bad_events']==1)
check('objectives','Ineligible event does not dilute denominator',assess([sample(),sample(1,correct=False,eligible=False)])['eligible_events']==1)
check('objectives','No eligible events produces no fabricated success',assess([])['good_fraction'] is None and not assess([])['objective_met'])
check('objectives','Aggregate goal cannot excuse a critical invariant violation',critical['objective_met'] and critical['invariant_violations']==1 and not critical['design_gate_passed'])
check('objectives','Invariant violations counted even outside eligible latency traffic',assess([sample(),sample(1,eligible=False,violates=True)])['invariant_violations']==1)
rejects('objectives','Negative sample duration rejected',ValueError,lambda:assess([sample(-1)]))
rejects('objectives','Implicit truthy classification rejected',ValueError,lambda:assess([{'eligible':1,'correct':True,'violates_invariant':False,'duration_ms':100}]))
rejects('objectives','Impossible goal rejected',ValueError,lambda:assess([],goal=1.1))
observations['objectives']={'slow_sample':normal,'critical_sample':critical}

temporary_path=None
worker_results=[]
try:
    with ExitStack() as stack:
        temporary=stack.enter_context(tempfile.TemporaryDirectory(prefix='a0-',dir=BASE))
        temporary_path=Path(temporary)
        database=temporary_path/'notes.sqlite3'
        ids=iter(['note-1','note-2','fault-note','note-after-fault'])
        repo=Notes(database,id_factory=lambda:next(ids)); stack.callback(repo.close)
        repo.initialize()
        first=repo.create('alpha','alice','create-1','HTTP','request trace')
        check('baseline','Create persists revision one',first['note']=={'id':'note-1','title':'HTTP','content':'request trace','revision':1} and not first['replayed'])
        check('baseline','Owner reads the persisted representation',repo.get('alpha','alice','note-1')==first['note'])
        replay=repo.create('alpha','alice','create-1','HTTP','request trace')
        check('baseline','Same scoped operation returns stored outcome',replay['replayed'] and replay['note']==first['note'])
        check('baseline','Replay creates no extra physical note',repo.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0]==1)
        rejects('baseline','Same operation with different input conflicts',Conflict,lambda:repo.create('alpha','alice','create-1','changed','request trace'))
        rejects('baseline','Other owner cannot read',NotFound,lambda:repo.get('alpha','bob','note-1'))
        rejects('baseline','Other tenant cannot read',NotFound,lambda:repo.get('beta','alice','note-1'))
        rejects('baseline','Absent and invisible reads share failure class',NotFound,lambda:repo.get('alpha','alice','absent'))
        rejects('baseline','Other owner cannot edit',NotFound,lambda:repo.update('alpha','bob','note-1',1,'bad','bad'))
        edited=repo.update('alpha','alice','note-1',1,'HTTP v2','current trace')
        check('baseline','Matching expected revision updates exactly once',edited['revision']==2 and edited['title']=='HTTP v2')
        rejects('baseline','Old expected revision rejects overwrite',StaleVersion,lambda:repo.update('alpha','alice','note-1',1,'lost','lost'))
        check('baseline','Rejected stale edit preserves current content',repo.get('alpha','alice','note-1')==edited)
        old_create=repo.create('alpha','alice','create-1','HTTP','request trace')
        check('baseline','Create replay retains original result after later edit',old_create['note']['revision']==1 and repo.get('alpha','alice','note-1')['revision']==2)
        second=repo.create('beta','alice','create-1','Other tenant','scoped operation')
        check('baseline','Operation identity is scoped by tenant and owner',second['note']['id']=='note-2' and not second['replayed'])
        rejects('baseline','Injected failure rejects create transaction',RuntimeError,lambda:repo.create('alpha','alice','fault','Fail','rollback',fail_after_insert=True))
        check('baseline','Failure rolls back note and operation together',repo.db.execute("SELECT COUNT(*) FROM notes WHERE id='fault-note'").fetchone()[0]==0 and repo.db.execute("SELECT COUNT(*) FROM operations WHERE operation_id='fault'").fetchone()[0]==0)
        retried=repo.create('alpha','alice','fault','Fail','rollback')
        check('baseline','Retry after rolled-back create can succeed',retried['note']['id']=='note-after-fault' and not retried['replayed'])
        rejects('baseline','Oversized UTF-8 content rejected by bytes',ValueError,lambda:repo.create('alpha','alice','huge','title','\u00e9'*2049))
        rejects('baseline','Whitespace-only title rejected',ValueError,lambda:repo.create('alpha','alice','blank','   ','text'))
        rejects('baseline','Boolean revision rejected',ValueError,lambda:repo.update('alpha','alice','note-1',True,'x','y'))
        rejects('baseline','Malformed identity rejected',ValueError,lambda:repo.get('alpha','alice','../note-1'))
        def violate_storage_rule():
            with repo.db:
                repo.db.execute("INSERT INTO notes VALUES ('alpha','invalid','alice','title','x',0)")
        rejects('baseline','Storage itself rejects nonpositive revision',sqlite3.IntegrityError,violate_storage_rule)
        repo.close()
        reopened=Notes(database); stack.callback(reopened.close)
        check('baseline','Fresh connection retains committed edit',reopened.get('alpha','alice','note-1')==edited)

        barrier=Barrier(2)
        def concurrent_create():
            worker=Notes(database,id_factory=lambda:'parallel-note')
            try:
                barrier.wait(timeout=5)
                result=worker.create('alpha','alice','parallel','Concurrent','same create')
                return {'replayed':result['replayed'],'id':result['note']['id']}
            finally:
                worker.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures=[executor.submit(concurrent_create) for _ in range(2)]
            creates=[future.result(timeout=10) for future in futures]
        worker_results.extend(creates)
        check('concurrency','Concurrent duplicate creates yield one new result and one replay',sorted(r['replayed'] for r in creates)==[False,True] and all(r['id']=='parallel-note' for r in creates))
        check('concurrency','Concurrent duplicate creates persist one note and operation',reopened.db.execute("SELECT COUNT(*) FROM notes WHERE id='parallel-note'").fetchone()[0]==1 and reopened.db.execute("SELECT COUNT(*) FROM operations WHERE operation_id='parallel'").fetchone()[0]==1)
        barrier=Barrier(2)
        def concurrent_edit(title):
            worker=Notes(database)
            try:
                barrier.wait(timeout=5)
                try:
                    result=worker.update('alpha','alice','parallel-note',1,title,'one wins')
                    return {'outcome':'accepted','revision':result['revision']}
                except StaleVersion:
                    return {'outcome':'stale'}
            finally:
                worker.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures=[executor.submit(concurrent_edit,title) for title in ('edit-a','edit-b')]
            edits=[future.result(timeout=10) for future in futures]
        worker_results.extend(edits)
        check('concurrency','Two edits of revision one yield one accepted and one stale',sorted(r['outcome'] for r in edits)==['accepted','stale'])
        final=reopened.get('alpha','alice','parallel-note')
        check('concurrency','Concurrent edits increment revision once',final['revision']==2 and final['title'] in ('edit-a','edit-b'))
        observations['baseline']={'created':first,'replayed':replay,'edited':edited,'replayed_create_after_edit':old_create,'rollback_retry':retried,'concurrent_creates':sorted(creates,key=lambda r:r['replayed']),'concurrent_edits':sorted(edits,key=lambda r:r['outcome']),'final_concurrent_revision':final['revision'],'scope':'Real SQLite file transactions, reopen persistence and two independent connections per concurrent pair. Direct repository calls with supplied identities; no HTTP/authentication/TLS, production throughput or full service deployment.'}
finally:
    cleanup={'temporary_database_directory_removed':temporary_path is None or not temporary_path.exists(),'sqlite_connections_closed':True,'concurrent_worker_calls_completed':len(worker_results),'persistent_listener_started':False}
    (BASE/'cleanup-results.json').write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
assert cleanup['temporary_database_directory_removed'] and cleanup['concurrent_worker_calls_completed']==4
counts={group:sum(check['group']==group for check in checks) for group in dict.fromkeys(check['group'] for check in checks)}
proof={'module':0,'label':'A0','verified_date':'2026-10-16','python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'os':platform.platform(),'total':len(checks),'counts':counts,'checks':checks,'observations':observations,'cleanup':cleanup,'scope':'Planning arithmetic, hand-authored SLI classification and a real SQLite repository probe. No HTTP service, authentication implementation, hosted resources, model/provider calls or production benchmark.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':proof['total'],'counts':counts,'observations':observations,'cleanup':cleanup},indent=2))
