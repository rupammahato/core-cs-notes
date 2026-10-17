from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb
from db import prepare,connect,connection_info
from checks import Checks,equal,require
prepare()
checks=Checks('core')
observed={}
with connect() as conn:
    def rejected(operation,state):
        try: operation()
        except psycopg.Error as error:
            equal(error.sqlstate,state)
            return
        raise AssertionError('expected SQLSTATE '+state)
    def configuration():
        equal(conn.execute('SELECT current_user').fetchone()[0],'m13_app')
        flags=conn.execute('SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user').fetchone()
        equal(flags,(False,False,False))
        equal(conn.execute('SHOW default_transaction_isolation').fetchone()[0],'read committed')
        observed['server']={k:conn.execute('SHOW '+k).fetchone()[0] for k in ('server_version','default_transaction_isolation','fsync','synchronous_commit','ssl')}
    checks.check('application role is non-superuser and server configuration is recorded',configuration)
    def parameters():
        text="O'Reilly'; DROP TABLE lesson.products; --"
        row=conn.execute('INSERT INTO lesson.values_demo(label) VALUES (%s) RETURNING label',(text,)).fetchone()
        equal(row[0],text)
        equal(conn.execute('SELECT count(*) FROM lesson.products').fetchone()[0],2)
    checks.check('adversarial text is bound as a value without executing SQL',parameters)
    def identifier():
        row=conn.execute(sql.SQL('SELECT {} FROM {}.{} ORDER BY id LIMIT 1').format(
            sql.Identifier('label'),sql.Identifier('lesson'),sql.Identifier('values_demo'))).fetchone()
        require(row[0].startswith("O'Reilly"))
        equal(conn.execute('SELECT %s FROM lesson.products LIMIT 1',('available',)).fetchone()[0],'available')
    checks.check('Identifier composition selects a column while a bound value stays literal',identifier)
    def types():
        instant=datetime(2026,10,14,6,30,tzinfo=timezone.utc)
        value=conn.execute('INSERT INTO lesson.values_demo(label,amount,happened_at,metadata) VALUES (%s,%s,%s,%s) RETURNING amount,happened_at,metadata',
                           ('typed',Decimal('125.50'),instant,Jsonb({'tenant':'alpha','tags':['api']}))).fetchone()
        equal(value,(Decimal('125.50'),instant,{'tenant':'alpha','tags':['api']}))
        observed['typed_values']={'amount':str(value[0]),'timestamp':value[1].isoformat(),'metadata':value[2]}
    checks.check('numeric timestamptz and jsonb round-trip through real type adapters',types)
    checks.check('jsonb containment executes on PostgreSQL',lambda:equal(conn.execute('SELECT metadata @> %s FROM lesson.values_demo WHERE label=%s',(Jsonb({'tenant':'alpha'}),'typed')).fetchone()[0],True))
    def nulls():
        conn.execute('INSERT INTO lesson.values_demo(label) VALUES (NULL),(NULL)')
        equal(conn.execute('SELECT count(*) FROM lesson.values_demo WHERE label IS NULL').fetchone()[0],2)
    checks.check('ordinary UNIQUE permits multiple null values by default',nulls)
    checks.check('check constraint rejects negative stock',lambda:rejected(lambda:conn.execute("UPDATE lesson.products SET available=-1 WHERE tenant_id=1 AND sku='basic'"),'23514'))
    checks.check('unique constraint rejects duplicate tenant SKU',lambda:rejected(lambda:conn.execute("INSERT INTO lesson.products VALUES (1,'basic',1,1,'INR')"),'23505'))
    checks.check('not-null constraint rejects null SKU',lambda:rejected(lambda:conn.execute("INSERT INTO lesson.products VALUES (1,NULL,1,1,'INR')"),'23502'))
    checks.check('composite foreign key rejects a product from another tenant',lambda:rejected(lambda:conn.execute("INSERT INTO lesson.reservations(id,tenant_id,request_key,sku,quantity,status) VALUES (%s,1,'foreign','beta-only',1,'pending')",(uuid4(),)),'23503'))
    checks.check('application role cannot create tables in migration-owned schema',lambda:rejected(lambda:conn.execute('CREATE TABLE lesson.not_allowed(id int)'),'42501'))
    def tenant_scope():
        equal(conn.execute('SELECT count(*) FROM lesson.products').fetchone()[0],2)
        equal(conn.execute('SELECT count(*) FROM lesson.products WHERE tenant_id=%s',(1,)).fetchone()[0],1)
        observed['role_is_not_tenant_filter']=True
    checks.check('table grants do not replace application tenant predicates',tenant_scope)
    def indexes():
        definitions=[r[0] for r in conn.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='lesson' AND tablename='reservations'")]
        equal(len(definitions),2)
        require(all('sku' not in value for value in definitions))
        observed['reservation_indexes']=definitions
    checks.check('foreign key does not automatically add a referencing SKU index',indexes)
    def upsert():
        value=conn.execute('INSERT INTO lesson.accounts(id,balance) VALUES (%s,%s) ON CONFLICT (id) DO UPDATE SET balance=EXCLUDED.balance RETURNING balance',(1,7)).fetchone()[0]
        equal(value,7)
        equal(conn.execute('SELECT count(*) FROM lesson.accounts WHERE id=1').fetchone()[0],1)
    checks.check('ON CONFLICT updates the specified conflict target and RETURNING reports value',upsert)
    def sequence():
        try:
            with conn.transaction():
                first=conn.execute("INSERT INTO lesson.sequence_demo(note) VALUES ('rolled back') RETURNING id").fetchone()[0]
                raise ValueError('rollback')
        except ValueError: pass
        second=conn.execute("INSERT INTO lesson.sequence_demo(note) VALUES ('kept') RETURNING id").fetchone()[0]
        equal((first,second),(1,2))
        observed['sequence_gap']={'rolled_back_id':first,'next_id':second}
    checks.check('identity sequence allocation is not rolled back',sequence)
    def savepoint():
        with conn.transaction():
            try:
                with conn.transaction(): conn.execute("INSERT INTO lesson.products VALUES (1,'basic',1,1,'INR')")
            except psycopg.errors.UniqueViolation: pass
            conn.execute("INSERT INTO lesson.values_demo(label) VALUES ('savepoint-ok')")
        equal(conn.execute("SELECT count(*) FROM lesson.values_demo WHERE label='savepoint-ok'").fetchone()[0],1)
    checks.check('savepoint rollback permits the outer transaction to continue',savepoint)

def transaction_states():
    with connect(autocommit=False) as conn:
        conn.execute('SELECT 1')
        equal(conn.info.transaction_status,TransactionStatus.INTRANS)
        try: conn.execute("INSERT INTO lesson.products VALUES (1,'basic',1,1,'INR')")
        except psycopg.errors.UniqueViolation: pass
        else: raise AssertionError('expected unique error')
        equal(conn.info.transaction_status,TransactionStatus.INERROR)
        try: conn.execute('SELECT 1')
        except psycopg.errors.InFailedSqlTransaction as error: equal(error.sqlstate,'25P02')
        else: raise AssertionError('failed transaction accepted query')
        conn.rollback()
        equal(conn.info.transaction_status,TransactionStatus.IDLE)
        equal(conn.execute('SELECT 1').fetchone()[0],1)
checks.check('implicit SELECT transaction and failed state require deliberate rollback',transaction_states)

def password():
    params=conninfo_to_dict(connection_info())
    params['password']='wrong-public-fixture'
    try: psycopg.connect(**params)
    except psycopg.OperationalError: return
    raise AssertionError('incorrect password accepted')
checks.check('SCRAM host authentication rejects incorrect fixture password',password)

def ddl():
    with connect(admin=True) as conn:
        try:
            with conn.transaction():
                conn.execute('CREATE TABLE lesson.transient(id int)')
                raise ValueError('rollback DDL')
        except ValueError: pass
        equal(conn.execute("SELECT to_regclass('lesson.transient')").fetchone()[0],None)
checks.check('ordinary CREATE TABLE rolls back with its transaction',ddl)
checks.save(observations=observed)
