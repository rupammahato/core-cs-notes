"""Durable interval/one-off jobs, tenant admission and a local idempotent effect."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
import json
import re
import uuid
from runtime import Database, Error, document, identity, number, require


class Scheduler(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,tenant TEXT,owner TEXT,operation TEXT,
            delta INTEGER,due INTEGER,original_due INTEGER,deadline INTEGER,state TEXT,attempts INTEGER,
            token TEXT,lease_until INTEGER,started INTEGER,reason TEXT,
            UNIQUE(tenant,owner,operation));
        CREATE INDEX IF NOT EXISTS job_due ON jobs(state,due,lease_until);
        CREATE TABLE IF NOT EXISTS turns(id INTEGER PRIMARY KEY,last_tenant TEXT);
        INSERT INTO turns VALUES(1,'') ON CONFLICT DO NOTHING;
        CREATE TABLE IF NOT EXISTS effects(job TEXT PRIMARY KEY,tenant TEXT,owner TEXT,delta INTEGER);
        CREATE TABLE IF NOT EXISTS counters(tenant TEXT,owner TEXT,value INTEGER,PRIMARY KEY(tenant,owner));
        CREATE TABLE IF NOT EXISTS schedules(id TEXT PRIMARY KEY,tenant TEXT,owner TEXT,name TEXT,
            delta INTEGER,interval_ms INTEGER,next_due INTEGER,UNIQUE(tenant,owner,name));
    '''

    def _insert(self,tenant,owner,operation,delta,due,deadline):
        old = self.db.execute('SELECT * FROM jobs WHERE tenant=? AND owner=? AND operation=?',(tenant,owner,operation)).fetchone()
        if old:
            if (old['delta'],old['original_due'],old['deadline']) != (delta,due,deadline):
                raise Error(409,'changed_job_intent')
            return dict(old)
        if self.db.execute('SELECT count(*) FROM jobs').fetchone()[0]>=256:
            raise Error(503,'lesson_job_retention_cap')
        job_id = uuid.uuid4().hex
        self.db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,'pending',0,NULL,0,0,NULL)",
                        (job_id,tenant,owner,operation,delta,due,due,deadline))
        return dict(self.db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone())

    def enqueue(self,tenant,owner,operation,delta,due,deadline):
        for value in (tenant,owner,operation):
            identity(value)
        if operation.startswith('schedule_'):
            raise Error(400,'reserved_operation_prefix')
        number(delta,1,1000)
        number(due)
        number(deadline,due+1)
        with self.transaction():
            return self._insert(tenant,owner,operation,delta,due,deadline)

    def owned(self,tenant,owner,job_id):
        row = self.db.execute('SELECT j.*,EXISTS(SELECT 1 FROM effects e WHERE e.job=j.id) AS effect_applied FROM jobs j WHERE tenant=? AND owner=? AND id=?',
                              (identity(tenant),identity(owner),identity(job_id))).fetchone()
        if row is None:
            raise Error(404,'job_not_found')
        return dict(row)

    def schedule(self,tenant,owner,name,delta,interval_ms,first_due):
        for value in (tenant,owner,name):
            identity(value)
        number(delta,1,1000)
        number(interval_ms,1000,86400000)
        number(first_due)
        with self.transaction():
            if self.db.execute('SELECT count(*) FROM schedules').fetchone()[0]>=16:
                raise Error(503,'lesson_schedule_cap')
            schedule_id = uuid.uuid4().hex
            self.db.execute('INSERT INTO schedules VALUES(?,?,?,?,?,?,?)',(schedule_id,tenant,owner,name,delta,interval_ms,first_due))
            return schedule_id

    def tick(self,now):
        number(now)
        created = []
        with self.transaction():
            rows = self.db.execute('SELECT * FROM schedules WHERE next_due<=? ORDER BY next_due,id LIMIT 16',(now,)).fetchall()
            for row in rows:
                # Coalesce missed intervals: one most-recent occurrence, not every miss.
                slot = row['next_due']+(now-row['next_due'])//row['interval_ms']*row['interval_ms']
                operation = 'schedule_'+row['id']+'_'+str(slot)
                created.append(self._insert(row['tenant'],row['owner'],operation,row['delta'],slot,slot+row['interval_ms'])['id'])
                self.db.execute('UPDATE schedules SET next_due=? WHERE id=?',(slot+row['interval_ms'],row['id']))
        return created

    def claim(self,now):
        number(now)
        with self.transaction():
            self.db.execute("UPDATE jobs SET state='failed',token=NULL,reason='deadline_or_attempts_exhausted' WHERE state IN ('pending','running') AND (deadline<=? OR (state='running' AND lease_until<=? AND attempts>=3))",(now,now))
            live = self.db.execute("SELECT tenant,count(*) AS n FROM jobs WHERE state='running' AND lease_until>? GROUP BY tenant",(now,)).fetchall()
            if sum(row['n'] for row in live)>=2:
                return None
            busy = {row['tenant'] for row in live}
            rows = self.db.execute("SELECT * FROM jobs WHERE due<=? AND deadline>? AND attempts<3 AND (state='pending' OR (state='running' AND lease_until<=?)) ORDER BY tenant,due,id",(now,now,now)).fetchall()
            tenants = sorted({row['tenant'] for row in rows}-busy)
            if not tenants:
                return None
            last = self.db.execute('SELECT last_tenant FROM turns WHERE id=1').fetchone()[0]
            chosen = next((tenant for tenant in tenants if tenant>last),tenants[0])
            row = next(row for row in rows if row['tenant']==chosen)
            token = uuid.uuid4().hex
            until = min(now+2000,row['deadline'])
            self.db.execute("UPDATE jobs SET state='running',attempts=attempts+1,token=?,lease_until=?,started=? WHERE id=?",(token,until,now,row['id']))
            self.db.execute('UPDATE turns SET last_tenant=? WHERE id=1',(chosen,))
            return dict(self.db.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone())

    def live(self,job,now):
        number(now)
        return self.db.execute("SELECT * FROM jobs WHERE id=? AND state='running' AND token=? AND lease_until>? AND deadline>?",(job['id'],job['token'],now,now)).fetchone()

    def renew(self,job,now,extension_ms=2000):
        number(extension_ms,1,5000)
        with self.transaction():
            row = self.live(job,now)
            if row is None:
                return False
            until = min(max(row['lease_until'],now+extension_ms),row['started']+6000,row['deadline'])
            self.db.execute('UPDATE jobs SET lease_until=? WHERE id=?',(until,row['id']))
            return until

    def effect(self,job,now):
        with self.transaction():
            row = self.live(job,now)
            if row is None:
                return 'stale'
            if self.db.execute('SELECT 1 FROM effects WHERE job=?',(row['id'],)).fetchone():
                return 'replay'
            self.db.execute('INSERT INTO effects VALUES(?,?,?,?)',(row['id'],row['tenant'],row['owner'],row['delta']))
            self.db.execute('INSERT INTO counters VALUES(?,?,?) ON CONFLICT(tenant,owner) DO UPDATE SET value=value+excluded.value',
                            (row['tenant'],row['owner'],row['delta']))
            return 'applied'

    def ack(self,job,now):
        with self.transaction():
            if self.live(job,now) is None or not self.db.execute('SELECT 1 FROM effects WHERE job=?',(job['id'],)).fetchone():
                return False
            self.db.execute("UPDATE jobs SET state='succeeded',token=NULL WHERE id=?",(job['id'],))
            return True

    def fail(self,job,now,retryable,delay_ms=0):
        if type(retryable) is not bool:
            raise Error(400,'invalid_failure_class')
        with self.transaction():
            row = self.live(job,now)
            if row is None:
                return False
            number(delay_ms,0,min(4000,500*2**(row['attempts']-1)))
            retry = retryable and row['attempts']<3 and now+delay_ms<row['deadline']
            self.db.execute('UPDATE jobs SET state=?,due=?,token=NULL,reason=? WHERE id=?',
                ('pending' if retry else 'failed',now+delay_ms,'retry_scheduled' if retry else 'terminal_failure',row['id']))
            return True

    def cancel(self,tenant,owner,job_id):
        with self.transaction():
            row = self.owned(tenant,owner,job_id)
            if row['effect_applied']:
                raise Error(409,'effect_already_applied')
            if row['state'] in ('pending','running'):
                self.db.execute("UPDATE jobs SET state='cancelled',token=NULL WHERE id=?",(job_id,))
            return self.owned(tenant,owner,job_id)


def estimates():
    return {'jobs_per_day':864000,'average_arrivals_per_second':10,
        'assumed_mean_job_seconds':0.5,'mean_busy_slots_at_average':5,
        'one_hour_backlog_at_10_per_second':36000,'drain_seconds_at_15_service_10_arrival':7200,
        'fixture_global_inflight_cap':2,'fixture_per_tenant_inflight_cap':1,'measured_capacity':False}


def dispatch(item,user,method,path,raw,headers):
    tenant,owner = require(user)
    if path=='/jobs' and method=='POST':
        value = document(raw,['delta','due','deadline'])
        return 202,item.enqueue(tenant,owner,headers.get('Idempotency-Key',''),**value)
    match = re.fullmatch(r'/jobs/([a-f0-9]{32})',path)
    if match and method=='GET':
        return 200,item.owned(tenant,owner,match[1])
    if match and method=='DELETE':
        return 200,item.cancel(tenant,owner,match[1])
    raise Error(404,'unknown_route')
