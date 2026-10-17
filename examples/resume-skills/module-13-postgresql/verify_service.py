from threading import Thread,Event
from psycopg.pq import TransactionStatus
from db import prepare,connect
from reservation import reserve,InvalidRequest,OutOfStock,IdempotencyConflict
from coordination import wait_blocked,finish
from checks import Checks,equal,require
prepare()
checks=Checks('service')
observed={}
first={}

def stock(conn,tenant=1,sku='basic'):
    return conn.execute('SELECT available FROM lesson.products WHERE tenant_id=%s AND sku=%s',(tenant,sku)).fetchone()[0]

def request(conn,key='initial',quantity=2,**extra):
    return reserve(conn,tenant_id=1,request_key=key,sku='basic',quantity=quantity,**extra)

def success():
    with connect() as conn:
        value=request(conn)
        first.update(value)
        equal((value['quantity'],value['total_minor'],value['currency'],value['replayed']),(2,25000,'INR',False))
        equal(stock(conn),8)
        equal(conn.execute("SELECT count(*) FROM lesson.reservations WHERE status='reserved'").fetchone()[0],1)
        equal(conn.execute('SELECT count(*) FROM lesson.outbox').fetchone()[0],1)
        observed['successful_reservation']={key:value[key] for key in ('quantity','total_minor','currency','replayed')}
checks.check('trusted price stock reservation and outbox commit together',success)

def replay():
    with connect() as conn:
        value=request(conn)
        equal(value['reservation_id'],first['reservation_id'])
        equal(value['replayed'],True)
        equal(stock(conn),8)
        equal(conn.execute('SELECT count(*) FROM lesson.outbox').fetchone()[0],1)
checks.check('sequential replay returns the same reservation without another stock effect',replay)

def conflict():
    with connect() as conn:
        try: request(conn,quantity=3)
        except IdempotencyConflict: pass
        else: raise AssertionError('changed payload accepted for same key')
        equal(stock(conn),8)
checks.check('same idempotency key with different payload is rejected',conflict)

def tenant():
    with connect() as conn:
        value=reserve(conn,tenant_id=2,request_key='initial',sku='beta-only',quantity=1)
        require(value['reservation_id']!=first['reservation_id'])
        equal(stock(conn,2,'beta-only'),9)
        equal(stock(conn),8)
        equal(conn.execute("SELECT payload->>'tenant_id' FROM lesson.outbox WHERE reservation_id=%s",(value['reservation_id'],)).fetchone()[0],'2')
checks.check('idempotency and inventory scope include the trusted tenant',tenant)

def invalid():
    with connect() as conn:
        before=conn.execute('SELECT count(*) FROM lesson.reservations').fetchone()[0]
        for value in (True,'2',2.0,0,11,None):
            try: request(conn,key='invalid',quantity=value)
            except InvalidRequest: pass
            else: raise AssertionError('invalid quantity accepted')
            equal(conn.info.transaction_status,TransactionStatus.IDLE)
        equal(conn.execute('SELECT count(*) FROM lesson.reservations').fetchone()[0],before)
        equal(stock(conn),8)
checks.check('invalid quantity types bounds and booleans are rejected before state changes',invalid)

def foreign():
    with connect() as conn:
        try: reserve(conn,tenant_id=1,request_key='foreign',sku='beta-only',quantity=1)
        except OutOfStock: pass
        else: raise AssertionError('cross-tenant product accepted')
        equal(conn.execute("SELECT count(*) FROM lesson.reservations WHERE request_key='foreign'").fetchone()[0],0)
        equal(stock(conn),8)
checks.check('known composite foreign-key failure becomes unavailable and rolls back claim',foreign)

def insufficient():
    with connect() as conn:
        try: request(conn,key='insufficient',quantity=10)
        except OutOfStock: pass
        else: raise AssertionError('insufficient stock accepted')
        equal(stock(conn),8)
        equal(conn.execute("SELECT count(*) FROM lesson.reservations WHERE request_key='insufficient'").fetchone()[0],0)
checks.check('insufficient stock rolls back the idempotency claim',insufficient)

def injected():
    with connect() as conn:
        try: request(conn,key='injected',quantity=1,fail_after_stock=True)
        except RuntimeError as error: equal(str(error),'injected before reservation/outbox completion')
        else: raise AssertionError('injected failure not raised')
        equal(stock(conn),8)
        equal(conn.execute("SELECT count(*) FROM lesson.reservations WHERE request_key='injected'").fetchone()[0],0)
        equal(conn.execute('SELECT count(*) FROM lesson.outbox').fetchone()[0],2)
checks.check('failure after stock update rolls back stock reservation and outbox',injected)

def start(conn,key,hook=None):
    box={}; done=Event()
    def work():
        try: box['value']=request(conn,key=key,quantity=1,after_claim=hook)
        except Exception as error: box['error']=error
        finally: done.set()
    thread=Thread(target=work,daemon=True)
    thread.start()
    return thread,done,box

def race(same_key):
    with connect() as setup: setup.execute("UPDATE lesson.products SET available=1 WHERE tenant_id=1 AND sku='basic'")
    claimed=Event(); release=Event()
    with connect(name='m13-reserve-a') as a,connect(name='m13-reserve-b') as b,connect(admin=True) as observer:
        def hold(conn):
            if not same_key: conn.execute("SELECT available FROM lesson.products WHERE tenant_id=1 AND sku='basic' FOR NO KEY UPDATE")
            claimed.set()
            if not release.wait(5): raise AssertionError('test gate deadline')
        key_a='same-key-race' if same_key else 'race-a'
        key_b=key_a if same_key else 'race-b'
        ta,da,ba=start(a,key_a,hold)
        tb=db=bb=None
        try:
            require(claimed.wait(5),'claim gate not reached')
            tb,db,bb=start(b,key_b)
            wait_blocked(observer,b.info.backend_pid,a.info.backend_pid)
            waiting_query=observer.execute('SELECT query FROM pg_stat_activity WHERE pid=%s',(b.info.backend_pid,)).fetchone()[0]
            require(('INSERT INTO lesson.reservations' if same_key else 'UPDATE lesson.products') in waiting_query)
            if same_key:
                equal(observer.execute('SELECT count(*) FROM lesson.reservations WHERE request_key=%s',(key_a,)).fetchone()[0],0)
        finally:
            release.set()
            finish(ta,da,a)
            if tb is not None: finish(tb,db,b)
        require('error' not in ba,repr(ba.get('error')))
        equal(stock(observer),0)
        if same_key:
            require('error' not in bb,repr(bb.get('error')))
            equal(ba['value']['reservation_id'],bb['value']['reservation_id'])
            equal(sorted([ba['value']['replayed'],bb['value']['replayed']]),[False,True])
        else: require(isinstance(bb.get('error'),OutOfStock))
        count=observer.execute('SELECT count(*) FROM lesson.reservations WHERE request_key=ANY(%s)',([key_a,key_b],)).fetchone()[0]
        outbox=observer.execute('SELECT count(*) FROM lesson.outbox o JOIN lesson.reservations r ON r.id=o.reservation_id WHERE r.request_key=ANY(%s)',([key_a,key_b],)).fetchone()[0]
        equal((count,outbox),(1,1))
        observed['same_key_race' if same_key else 'last_unit_race']={
            'wait_observed':True,'blocked_statement':'idempotency INSERT' if same_key else 'conditional stock UPDATE','remaining_stock':0,'reservations':count,'outbox_rows':outbox,
            'outcome':'one new and one replay' if same_key else 'one reserved and one unavailable'}
checks.check('competing last-unit requests cannot both reserve stock',lambda:race(False))
checks.check('concurrent duplicate key waits then replays one committed reservation',lambda:race(True))

def sold_out_replay():
    with connect() as conn:
        value=request(conn,key='same-key-race',quantity=1)
        equal(value['replayed'],True)
        equal(stock(conn),0)
checks.check('replay succeeds after stock is exhausted because claim precedes stock work',sold_out_replay)

def retry_failed():
    with connect() as conn:
        conn.execute("UPDATE lesson.products SET available=10 WHERE tenant_id=1 AND sku='basic'")
        value=request(conn,key='insufficient',quantity=10)
        equal(value['replayed'],False)
        equal(stock(conn),0)
checks.check('rolled-back unavailable key can later succeed after fixture restock',retry_failed)
checks.save(observations=observed,scope='Real PostgreSQL transactions and coordinated two-session service races; no HTTP/payment/delivery worker')
