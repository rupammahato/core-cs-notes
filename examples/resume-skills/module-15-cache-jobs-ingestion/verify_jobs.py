from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
import os
from store import connect,prepare
from jobs import enqueue,claim,finish,fail,backoff
from checks import Checks,equal,require,rejects

checks=Checks('jobs');observed={};filename=Path(os.environ['M15_DATABASE']);prepare(filename)
with connect(filename) as conn:
    def reset():conn.execute('DELETE FROM jobs');conn.execute('DELETE FROM effects')
    def put(key='a',tenant=1,amount=7,now=0):return enqueue(conn,tenant_id=tenant,operation_key=key,amount=amount,now=now)
    def dedupe():
        reset();equal(put(),put());equal(conn.execute('SELECT count(*) FROM jobs').fetchone()[0],1)
    checks.check('tenant operation key deduplicates producer requests durably',dedupe)
    checks.check('same producer key with changed payload is rejected',lambda:rejects(ValueError,lambda:put(amount=8)))
    def scope():
        put(tenant=2);equal(conn.execute('SELECT count(*) FROM jobs').fetchone()[0],2)
    checks.check('another tenant has an independent operation identity',scope)
    checks.check('boolean amount is rejected before enqueue',lambda:rejects(ValueError,lambda:put('bad',amount=True)))
    def scheduled():
        reset();put(now=10);equal(claim(conn,now=9),None);require(claim(conn,now=10) is not None)
    checks.check('future scheduled work is ineligible until its due time',scheduled)
    def competing():
        reset();put();barrier=Barrier(2)
        def worker(_):
            with connect(filename) as local:barrier.wait(5);return claim(local,now=0)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,[1,2]))
        equal(sum(row is not None for row in results),1)
        observed['concurrent_claims']={'callers':2,'owners':1}
    checks.check('separate concurrent SQLite connections give one active job owner',competing)
    def reclaimed():
        reset();put();first=claim(conn,now=0);second=claim(conn,now=10)
        require(first['token']!=second['token']);equal(second['attempts'],2)
        equal(finish(conn,first,now=11),False);equal(fail(conn,first,now=11),False)
        equal(finish(conn,second,now=11),True)
        observed['lease_fencing']={'reclaimed_attempt':2,'stale_owner_rejected':True}
    checks.check('expired lease rotates ownership and rejects old completion and failure',reclaimed)
    def duplicate_finish():
        reset();put();owned=claim(conn,now=0);equal(finish(conn,owned,now=1),True)
        equal(finish(conn,owned,now=2),False)
        equal(conn.execute('SELECT sum(amount) FROM effects').fetchone()[0],7)
        equal(conn.execute('SELECT state FROM jobs').fetchone()[0],'done')
    checks.check('local business effect and job completion commit once together',duplicate_finish)
    def rollback():
        reset();put();owned=claim(conn,now=0)
        rejects(RuntimeError,lambda:finish(conn,owned,now=1,fail_before_commit=True))
        equal(conn.execute('SELECT count(*) FROM effects').fetchone()[0],0)
        equal(conn.execute('SELECT state FROM jobs').fetchone()[0],'running')
        replacement=claim(conn,now=10);finish(conn,replacement,now=11)
        equal(conn.execute('SELECT count(*) FROM effects').fetchone()[0],1)
    checks.check('failure between effect and done rolls both back then permits lease recovery',rollback)
    def retry():
        reset();put();owned=claim(conn,now=0);fail(conn,owned,now=1)
        equal(claim(conn,now=2),None);require(claim(conn,now=3) is not None)
        observed['backoff']=[backoff(i) for i in range(1,5)];equal(observed['backoff'],[2,4,8,8])
    checks.check('transient failure schedules capped backoff instead of immediate retry',retry)
    def permanent():
        reset();put();owned=claim(conn,now=0);fail(conn,owned,now=1,retryable=False)
        equal(claim(conn,now=100),None);equal(conn.execute('SELECT state FROM jobs').fetchone()[0],'failed')
    checks.check('permanent failure becomes terminal without an endless retry',permanent)
    def exhausted():
        reset();put()
        for now in (0,10,20):require(claim(conn,now=now) is not None)
        equal(claim(conn,now=30),None);equal(conn.execute('SELECT state,attempts FROM jobs').fetchone()[:],('failed',3))
        observed['exhausted_attempts']=3
    checks.check('abandoned leases eventually reach the configured attempt limit',exhausted)
    def reopen():
        reset();put();owned=claim(conn,now=0);finish(conn,owned,now=1)
        with connect(filename) as another:
            equal(another.execute('SELECT state FROM jobs').fetchone()[0],'done')
            equal(another.execute('SELECT count(*) FROM effects').fetchone()[0],1)
    checks.check('committed job state and effect are visible through a new connection',reopen)
checks.save(observations=observed,scope='Real file-backed SQLite transactions and concurrent connections; logical lease clock, no managed queue or power-loss test')
