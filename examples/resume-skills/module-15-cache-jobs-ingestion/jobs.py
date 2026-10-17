import json
from uuid import uuid4
from store import transaction

def backoff(attempt,*,base=2,cap=8):
    if type(attempt) is not int or attempt<1:raise ValueError('invalid attempt')
    return min(cap,base*2**min(attempt-1,20))

def enqueue(conn,*,tenant_id,operation_key,amount,now):
    if type(tenant_id) is not int or tenant_id<1 or type(amount) is not int or not 1<=amount<=1000:
        raise ValueError('invalid payload')
    if type(operation_key) is not str or not 1<=len(operation_key)<=80:raise ValueError('invalid key')
    payload=json.dumps({'amount':amount},sort_keys=True)
    with transaction(conn):
        conn.execute('INSERT INTO jobs(id,tenant_id,operation_key,payload,state,available_at) VALUES(?,?,?,?,?,?) ON CONFLICT(tenant_id,operation_key) DO NOTHING',
                     (str(uuid4()),tenant_id,operation_key,payload,'ready',now))
        row=conn.execute('SELECT * FROM jobs WHERE tenant_id=? AND operation_key=?',(tenant_id,operation_key)).fetchone()
        if row['payload']!=payload:raise ValueError('idempotency payload conflict')
        return row['id']

def claim(conn,*,now,lease_seconds=10,max_attempts=3):
    if lease_seconds<=0 or type(max_attempts) is not int or max_attempts<1:raise ValueError('invalid lease policy')
    with transaction(conn):
        conn.execute("UPDATE jobs SET state='failed',token=NULL,lease_until=NULL,last_error='attempts_exhausted' WHERE state='running' AND lease_until<=? AND attempts>=?",(now,max_attempts))
        row=conn.execute("SELECT * FROM jobs WHERE attempts<? AND ((state='ready' AND available_at<=?) OR (state='running' AND lease_until<=?)) ORDER BY available_at,id LIMIT 1",(max_attempts,now,now)).fetchone()
        if row is None:return None
        token=str(uuid4())
        conn.execute("UPDATE jobs SET state='running',attempts=attempts+1,token=?,lease_until=? WHERE id=?",(token,now+lease_seconds,row['id']))
        return dict(conn.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone())

def finish(conn,owned,*,now,fail_before_commit=False):
    with transaction(conn):
        row=conn.execute("SELECT * FROM jobs WHERE id=? AND tenant_id=? AND token=? AND state='running' AND lease_until>?",
                         (owned['id'],owned['tenant_id'],owned['token'],now)).fetchone()
        if row is None:return False
        amount=json.loads(row['payload'])['amount']
        conn.execute('INSERT INTO effects VALUES(?,?,?) ON CONFLICT(tenant_id,operation_key) DO NOTHING',
                     (row['tenant_id'],row['operation_key'],amount))
        if fail_before_commit:raise RuntimeError('injected before local effect/job commit')
        conn.execute("UPDATE jobs SET state='done',token=NULL,lease_until=NULL,last_error=NULL WHERE id=?",(row['id'],))
        return True

def fail(conn,owned,*,now,retryable=True,max_attempts=3):
    with transaction(conn):
        row=conn.execute("SELECT * FROM jobs WHERE id=? AND token=? AND state='running' AND lease_until>?",(owned['id'],owned['token'],now)).fetchone()
        if row is None:return False
        terminal=not retryable or row['attempts']>=max_attempts
        conn.execute('UPDATE jobs SET state=?,available_at=?,lease_until=NULL,token=NULL,last_error=? WHERE id=?',
                     ('failed' if terminal else 'ready',now+backoff(row['attempts']),'permanent' if not retryable else 'transient',row['id']))
        return True
