from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
import os
from store import connect,prepare
from ingestion import import_csv,InvalidFile
from fixtures import csv_bytes,row
from checks import Checks,equal,require,rejects

checks=Checks('ingestion');observed={};filename=Path(os.environ['M15_DATABASE']);prepare(filename)
data=csv_bytes([row('a'),row('b'),row('c')])
with connect(filename) as conn:
    def reset():conn.execute('DELETE FROM imports');conn.execute('DELETE FROM records')
    def load(key='file-1',tenant=1,content=data,**kwargs):return import_csv(conn,tenant_id=tenant,import_key=key,data=content,**kwargs)
    def complete():
        reset();equal(load(),3);equal(conn.execute('SELECT checkpoint,state FROM imports').fetchone()[:],(3,'complete'))
        equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],3)
    checks.check('batch import commits all source records and complete checkpoint',complete)
    def replay():
        equal(load(),3);equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],3)
    checks.check('same immutable file replay does not duplicate records',replay)
    checks.check('same import key with changed source bytes is rejected',lambda:rejects(ValueError,lambda:load(content=csv_bytes([row('a',amount='9')]))))
    def tenant():
        load(tenant=2);equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],6)
    checks.check('identical external source IDs remain independent across tenants',tenant)
    def newer():
        load('newer',content=csv_bytes([row('a',amount='20000',version='2')]))
        equal(conn.execute('SELECT amount_minor,source_version FROM records WHERE tenant_id=1 AND external_id=?',('a',)).fetchone()[:],(20000,2))
    checks.check('higher source version updates the existing scoped record',newer)
    def older():
        load('older',content=csv_bytes([row('a',amount='1',version='0')]))
        equal(conn.execute('SELECT amount_minor FROM records WHERE tenant_id=1 AND external_id=?',('a',)).fetchone()[0],20000)
    checks.check('out-of-order older source version cannot overwrite newer data',older)
    def conflict():
        rejects(ValueError,lambda:load('conflict',content=csv_bytes([row('a',amount='30000',version='2')])))
        equal(conn.execute('SELECT checkpoint FROM imports WHERE import_key=?',('conflict',)).fetchone()[0],0)
        equal(conn.execute('SELECT amount_minor FROM records WHERE tenant_id=1 AND external_id=?',('a',)).fetchone()[0],20000)
    checks.check('same source version with changed content fails without advancing checkpoint',conflict)
    def before_commit():
        reset();rejects(RuntimeError,lambda:load(fail_batch=0))
        equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],0)
        equal(conn.execute('SELECT checkpoint FROM imports').fetchone()[0],0)
    checks.check('failure within a batch rolls back records and checkpoint together',before_commit)
    def resume():
        reset()
        def interrupted(end):
            if end==2:raise RuntimeError('stop after committed batch')
        rejects(RuntimeError,lambda:load(after_commit=interrupted))
        before=conn.execute('SELECT checkpoint FROM imports').fetchone()[0]
        equal(before,2);equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],2)
        equal(load(),3);equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],3)
        observed['resume']={'committed_checkpoint_before_restart':before,'final_checkpoint':3,'final_records':3}
    checks.check('restart resumes from durable checkpoint after a committed batch',resume)
    def concurrent():
        reset();barrier=Barrier(2)
        def worker(_):
            with connect(filename) as local:
                barrier.wait(5);return import_csv(local,tenant_id=1,import_key='shared',data=data,batch_size=1)
        with ThreadPoolExecutor(max_workers=2) as pool:equal(list(pool.map(worker,[1,2])),[3,3])
        equal(conn.execute('SELECT count(*) FROM records').fetchone()[0],3);equal(conn.execute('SELECT count(*) FROM imports').fetchone()[0],1)
        observed['concurrent_restart']={'callers':2,'imports':1,'records':3}
    checks.check('concurrent same-file importers reload checkpoint inside the serialized transaction',concurrent)
    def preflight():
        reset();rejects(InvalidFile,lambda:load(content=csv_bytes([row(amount='bad')])))
        equal(conn.execute('SELECT count(*) FROM imports').fetchone()[0],0)
    checks.check('whole-file validation rejects bad input before database mutation',preflight)
    checks.check('invalid batch size and boolean tenant fail early',lambda:(rejects(ValueError,lambda:load(batch_size=True)),rejects(ValueError,lambda:load(tenant=True))))
checks.save(observations=observed,scope='Real SQLite conditional upserts checkpoints rollback and concurrent connections; injected application interruptions, not machine-crash recovery')
