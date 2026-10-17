from psycopg_pool import PoolTimeout,PoolClosed
from psycopg.pq import TransactionStatus
from db import prepare,make_pool
from checks import Checks,equal,require
prepare()
checks=Checks('pool')
observed={}

def reuse():
    with make_pool(max_size=1) as pool:
        with pool.connection() as conn: first=conn.info.backend_pid
        with pool.connection() as conn:
            equal(conn.info.backend_pid,first)
            equal(conn.execute('SELECT current_user').fetchone()[0],'m13_app')
    observed['backend_reused']=True
checks.check('returning a lease permits reuse of the same database session',reuse)

def capacity():
    with make_pool(max_size=2) as pool:
        with pool.connection() as a,pool.connection() as b:
            require(a.info.backend_pid!=b.info.backend_pid)
            observed['simultaneous_backends']=2
checks.check('two checked-out leases use two different PostgreSQL sessions',capacity)

def exhaust():
    with make_pool(max_size=2) as pool:
        with pool.connection() as a,pool.connection() as b:
            try:
                with pool.connection(timeout=0.05): pass
            except PoolTimeout: pass
            else: raise AssertionError('exhausted pool returned another connection')
        with pool.connection() as conn: equal(conn.execute('SELECT 1').fetchone()[0],1)
    observed['exhaustion']='PoolTimeout'
checks.check('pool capacity and acquisition deadline bound a third borrower',exhaust)

def rollback():
    with make_pool(max_size=1) as pool:
        try:
            with pool.connection() as conn,conn.transaction():
                conn.execute("INSERT INTO lesson.values_demo(label) VALUES ('not-committed')")
                raise ValueError('request failed')
        except ValueError: pass
        with pool.connection() as conn:
            equal(conn.info.transaction_status,TransactionStatus.IDLE)
            equal(conn.execute("SELECT count(*) FROM lesson.values_demo WHERE label='not-committed'").fetchone()[0],0)
checks.check('failed transactional lease returns without committing its partial write',rollback)

def session_state():
    with make_pool(max_size=1) as pool:
        with pool.connection() as conn: conn.execute("SET application_name='leaked-request-state'")
        with pool.connection() as conn:
            equal(conn.execute('SHOW application_name').fetchone()[0],'leaked-request-state')
    observed['nonlocal_setting_persisted']=True
checks.check('ordinary pool return does not erase arbitrary session SET state',session_state)

def local_state():
    with make_pool(max_size=1,name='m13-local-default') as pool:
        with pool.connection() as conn:
            with conn.transaction():
                conn.execute("SET LOCAL application_name='one-request'")
                equal(conn.execute('SHOW application_name').fetchone()[0],'one-request')
        with pool.connection() as conn: equal(conn.execute('SHOW application_name').fetchone()[0],'m13-local-default')
    observed['local_setting_cleared']=True
checks.check('SET LOCAL request state expires at its transaction boundary',local_state)

def reset():
    def reset_settings(conn): conn.execute('RESET ALL')
    with make_pool(max_size=1,reset=reset_settings,name='m13-reset-default') as pool:
        with pool.connection() as conn: conn.execute("SET application_name='temporary'")
        with pool.connection() as conn: equal(conn.execute('SHOW application_name').fetchone()[0],'m13-reset-default')
    observed['explicit_guc_reset']=True
checks.check('explicit reset callback clears the tested session setting',reset)

def closed():
    pool=make_pool(max_size=1)
    pool.close()
    try:
        with pool.connection(): pass
    except PoolClosed: return
    raise AssertionError('closed pool permitted a new lease')
checks.check('closed pool rejects new acquisition',closed)
observed['capacity_example']={'replicas':3,'workers_per_replica':2,'pool_max':2,'maximum_client_connections':3*2*2}
checks.save(observations=observed,scope='Actual Psycopg pool and PostgreSQL sessions; no PgBouncer or load benchmark')
