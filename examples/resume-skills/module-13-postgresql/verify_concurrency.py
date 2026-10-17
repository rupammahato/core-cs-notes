from psycopg import IsolationLevel, errors
from db import prepare,connect,make_pool
from checks import Checks,equal,require
from coordination import wait_blocked,background_update,finish
from retry import serializable
prepare()
checks=Checks('concurrency')
observed={}

def reset_accounts():
    with connect() as conn: conn.execute('UPDATE lesson.accounts SET balance=100')

def dirty():
    with connect(autocommit=False) as a,connect(autocommit=False) as b:
        a.execute('UPDATE lesson.accounts SET balance=333 WHERE id=1')
        equal(b.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],100)
        a.rollback()
        b.rollback()
checks.check('ordinary SELECT does not read another transaction uncommitted write',dirty)

def snapshots(level,expected):
    reset_accounts()
    with connect(autocommit=False) as a,connect(autocommit=False) as b:
        a.isolation_level=level
        first=a.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
        b.execute('UPDATE lesson.accounts SET balance=200 WHERE id=1')
        b.commit()
        second=a.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
        equal([first,second],expected)
        a.rollback()
        observed[level.name.lower()]=[first,second]
checks.check('Read Committed successive statements see a newly committed value',lambda:snapshots(IsolationLevel.READ_COMMITTED,[100,200]))
checks.check('Repeatable Read keeps the transaction snapshot across statements',lambda:snapshots(IsolationLevel.REPEATABLE_READ,[100,100]))

def lock_wait():
    reset_accounts()
    with connect(autocommit=False,name='m13-lock-a') as a,connect(autocommit=False,name='m13-lock-b') as b,connect(admin=True) as observer:
        a.execute('SELECT balance FROM lesson.accounts WHERE id=1 FOR UPDATE')
        thread,done,box=background_update(b,'UPDATE lesson.accounts SET balance=balance+1 WHERE id=1')
        try:
            wait_blocked(observer,b.info.backend_pid,a.info.backend_pid)
            require(not done.is_set())
            equal(observer.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],100)
            a.commit()
        finally:
            a.rollback()
            finish(thread,done,b)
        require('error' not in box,repr(box.get('error')))
        equal(box['rowcount'],1)
        equal(observer.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],101)
        observed['row_lock']={'wait_observed':True,'plain_read_during_wait':100,'after_release':101}
checks.check('FOR UPDATE really blocks a competing writer until transaction release',lock_wait)

def nowait():
    with connect(autocommit=False) as a,connect(autocommit=False) as b:
        a.execute('SELECT id FROM lesson.accounts WHERE id=1 FOR UPDATE')
        try: b.execute('SELECT id FROM lesson.accounts WHERE id=1 FOR UPDATE NOWAIT')
        except errors.LockNotAvailable as error: equal(error.sqlstate,'55P03')
        else: raise AssertionError('NOWAIT acquired locked row')
        b.rollback(); a.rollback()
        observed['nowait_sqlstate']='55P03'
checks.check('NOWAIT rejects a held row lock with its SQLSTATE',nowait)

def skip():
    with connect(autocommit=False) as a,connect(autocommit=False) as b:
        a.execute('SELECT id FROM lesson.jobs WHERE id=1 FOR UPDATE')
        row=b.execute("SELECT id FROM lesson.jobs WHERE status='ready' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED").fetchone()[0]
        equal(row,2)
        b.rollback(); a.rollback()
        observed['skip_locked']={'locked_id':1,'selected_id':row}
checks.check('SKIP LOCKED chooses another available job row',skip)

def lock_timeout():
    with connect(autocommit=False) as a,connect() as b:
        a.execute('SELECT id FROM lesson.accounts WHERE id=1 FOR UPDATE')
        b.execute("SET lock_timeout='100ms'")
        try: b.execute('UPDATE lesson.accounts SET balance=balance+1 WHERE id=1')
        except errors.LockNotAvailable as error: equal(error.sqlstate,'55P03')
        else: raise AssertionError('lock deadline did not reject')
        a.rollback()
checks.check('lock_timeout bounds waiting for a held row lock',lock_timeout)

def statement_timeout():
    with connect() as conn:
        conn.execute("SET statement_timeout='50ms'")
        try: conn.execute('SELECT pg_sleep(5)')
        except errors.QueryCanceled as error: equal(error.sqlstate,'57014')
        else: raise AssertionError('statement deadline did not cancel')
        equal(conn.execute('SELECT 1').fetchone()[0],1)
checks.check('statement_timeout cancels a long statement and autocommit session recovers',statement_timeout)

def lost_update():
    reset_accounts()
    with connect(autocommit=False) as a,connect(autocommit=False) as b:
        first=a.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
        second=b.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
        a.execute('UPDATE lesson.accounts SET balance=%s WHERE id=1',(first-10,)); a.commit()
        b.execute('UPDATE lesson.accounts SET balance=%s WHERE id=1',(second-20,)); b.commit()
    with connect() as conn: final=conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
    equal(final,80)
    observed['stale_absolute_writes']={'read_values':[first,second],'final':final}
checks.check('two overlapping Read Committed transactions can lose a stale absolute update',lost_update)

def relative():
    reset_accounts()
    with connect() as a,connect() as b:
        a.execute('UPDATE lesson.accounts SET balance=balance-10 WHERE id=1')
        b.execute('UPDATE lesson.accounts SET balance=balance-20 WHERE id=1')
        equal(a.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],70)
        observed['relative_updates_final']=70
checks.check('SQL relative updates preserve both fixture decrements',relative)

def optimistic():
    reset_accounts()
    with connect() as a,connect() as b:
        first=a.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
        second=b.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0]
        equal(a.execute('UPDATE lesson.accounts SET balance=90 WHERE id=1 AND balance=%s',(first,)).rowcount,1)
        equal(b.execute('UPDATE lesson.accounts SET balance=80 WHERE id=1 AND balance=%s',(second,)).rowcount,0)
        equal(a.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],90)
checks.check('conditional predicate rejects a stale compare-and-set writer',optimistic)

def skew():
    with connect() as conn: conn.execute('UPDATE lesson.doctors SET on_call=true')
    with connect(autocommit=False) as a,connect(autocommit=False) as b:
        a.isolation_level=b.isolation_level=IsolationLevel.REPEATABLE_READ
        equal(a.execute('SELECT count(*) FROM lesson.doctors WHERE on_call').fetchone()[0],2)
        equal(b.execute('SELECT count(*) FROM lesson.doctors WHERE on_call').fetchone()[0],2)
        a.execute('UPDATE lesson.doctors SET on_call=false WHERE id=1'); a.commit()
        b.execute('UPDATE lesson.doctors SET on_call=false WHERE id=2'); b.commit()
    with connect() as conn: remaining=conn.execute('SELECT count(*) FROM lesson.doctors WHERE on_call').fetchone()[0]
    equal(remaining,0)
    observed['repeatable_read_write_skew_remaining']=remaining
checks.check('Repeatable Read permits the disjoint-row write-skew fixture',skew)

def serial_retry():
    with connect() as conn: conn.execute('UPDATE lesson.doctors SET on_call=true')
    attempts=[]
    failures=[]
    with make_pool(max_size=1) as pool:
        def operation(a):
            attempts.append('attempt')
            remaining=a.execute('SELECT count(*) FROM lesson.doctors WHERE on_call').fetchone()[0]
            if len(attempts)==1:
                # A separate competing serializable transaction, controlled by the test.
                with connect(autocommit=False) as b:
                    b.isolation_level=IsolationLevel.SERIALIZABLE
                    equal(b.execute('SELECT count(*) FROM lesson.doctors WHERE on_call').fetchone()[0],2)
                    b.execute('UPDATE lesson.doctors SET on_call=false WHERE id=2')
                    b.commit()
            if remaining>1:
                a.execute('UPDATE lesson.doctors SET on_call=false WHERE id=1')
                return True
            return False
        equal(serializable(pool,operation,attempts=3,on_retry=failures.append),False)
        equal(failures,['40001'])
    equal(len(attempts),2)
    with connect() as conn: remaining=conn.execute('SELECT count(*) FROM lesson.doctors WHERE on_call').fetchone()[0]
    equal(remaining,1)
    observed['serializable_retry']={'attempts':len(attempts),'remaining_on_call':remaining,'final_change_allowed':False,'retry_sqlstates':failures}
checks.check('Serializable failure retries the whole transaction and rechecks the invariant',serial_retry)

def deadlock():
    reset_accounts()
    with connect(autocommit=False) as a,connect(autocommit=False) as b,connect(admin=True) as observer:
        a.execute('SELECT id FROM lesson.accounts WHERE id=1 FOR UPDATE')
        b.execute('SELECT id FROM lesson.accounts WHERE id=2 FOR UPDATE')
        thread,done,box=background_update(a,'UPDATE lesson.accounts SET balance=balance+1 WHERE id=2')
        states=[]
        try:
            wait_blocked(observer,a.info.backend_pid,b.info.backend_pid)
            try:
                b.execute('UPDATE lesson.accounts SET balance=balance+1 WHERE id=1')
                b.commit()
            except errors.DeadlockDetected as error:
                states.append(error.sqlstate)
                b.rollback()
        finally:
            b.rollback()
            finish(thread,done,a)
        if 'error' in box: states.append(box['error'].sqlstate)
        equal(states,['40P01'])
        equal(observer.execute('SELECT sum(balance) FROM lesson.accounts').fetchone()[0],201)
        observed['deadlock']={'aborted_sqlstate':states[0],'committed_updates':1,'victim_identity_not_assumed':True}
checks.check('opposite lock ordering causes a real deadlock and one transaction abort',deadlock)
checks.save(observations=observed,scope='Real separate PostgreSQL sessions; coordinated snapshots and observed lock waits')
