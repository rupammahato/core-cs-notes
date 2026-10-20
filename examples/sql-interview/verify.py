"""Real SQLite outputs, independent reference, changed inputs and plan evidence."""
from copy import deepcopy
import hashlib
import json
import platform
import sqlite3
from lab import BASE,connect,load_fixture,parameters,query
from reference import expected

checks=[];closed=0
def check(group,name,actual,want):
    assert actual==want,(name,actual,want)
    checks.append({'group':group,'name':name,'passed':True})

fixture=load_fixture();params=parameters();answers=expected(fixture,params)
sources=[BASE/'fixture.json',BASE/'parameters.json',BASE/'schema.sql',BASE/'lab.py',BASE/'reference.py',*sorted((BASE/'queries').glob('*.sql'))]
hashes={str(path.relative_to(BASE)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
observations={}
for reverse in [False,True]:
    db=connect(fixture,reverse=reverse)
    try:
        for n in range(1,31):
            key=f'Q{n:02}';actual=query(db,n,params)
            check('query-output' if not reverse else 'insertion-order',key+(' baseline' if not reverse else ' reversed insertion'),actual,answers[key])
            if not reverse:observations[key]=actual
    finally:db.close();closed+=1

def mutation(name,changed,selected,settings=None):
    global closed
    settings=settings or params;reference=expected(changed,settings);db=connect(changed)
    try:
        got={f'Q{n:02}':query(db,n,settings) for n in selected}
        want={f'Q{n:02}':reference[f'Q{n:02}'] for n in selected}
        check('mutation',name,got,want)
    finally:db.close();closed+=1

f=deepcopy(fixture);f['tables']['customers'].append(['c10','t1',params['event_cutoff']-86400])
mutation('New no-order customer remains visible',f,[1,2,8])
f=deepcopy(fixture);f['tables']['exclusions'].append([None])
mutation('Additional NULL exclusion does not poison anti-join',f,[8])
f=deepcopy(fixture);r=deepcopy(f['tables']['raw_events'][0]);r[0]='another-a1';r[5]+=500;f['tables']['raw_events'].append(r)
mutation('Duplicate delivery does not add sessions or users',f,[15,17,18,21])
f=deepcopy(fixture);f['tables']['orders'].append(['tie','c4',params['start']+86400,'paid',3000,None])
mutation('A tied top revenue tier retains every tied customer',f,[9])
f=deepcopy(fixture);next(r for r in f['tables']['orders'] if r[0]=='o08')[4]=0
mutation('Unknown billing changed to known zero restores completeness',f,[3,11,28])
f=deepcopy(fixture);next(r for r in f['tables']['raw_events'] if r[1]=='a3')[4]-=1
mutation('Exactly 1800 seconds does not start a session',f,[15])
f=deepcopy(fixture);next(r for r in f['tables']['raw_events'] if r[1]=='v6')[4]-=1
mutation('One second before exclusive funnel end becomes eligible',f,[17,24])
p=dict(params,knowledge_cutoff=params['later_knowledge'])
mutation('Late knowledge revises historical retention',fixture,[19],p)
f=deepcopy(fixture);next(r for r in f['tables']['carts'] if r[0]=='r4')[2]=params['event_cutoff']-3600
mutation('Exactly completed cart horizon is mature',f,[23])
f=deepcopy(fixture);next(r for r in f['tables']['items'] if r[0]=='i07')[3]=1500
mutation('Repairing a line mismatch removes only that exception',f,[29])
mutation('Other tenant receives only its own aggregate population',fixture,[1,2,9,16,17,30],dict(params,tenant='t2'))
mutation('Empty tenant has no users and no fabricated conversion rate',fixture,[1,9,17,30],dict(params,tenant='absent'))

counterexamples={};db=connect()
try:
    wrong=db.execute("SELECT c.customer_id FROM customers c LEFT JOIN orders o USING(customer_id) WHERE c.tenant_id=:tenant AND o.status='paid' AND o.ordered_ts>=:start AND o.ordered_ts<:end GROUP BY c.customer_id",params).fetchall()
    check('counterexample','WHERE filter drops preserved zero-order customers',len(wrong),6)
    counterexamples['outer_join_where']={'wrong_customers':len(wrong),'correct_customers':len(observations['Q01'])}
    wrong=db.execute("SELECT COUNT(*) FROM customers c LEFT JOIN orders o ON o.customer_id=c.customer_id AND o.status='paid' WHERE c.customer_id='c6'").fetchone()[0]
    check('counterexample','COUNT star counts an unmatched customer row',wrong,1)
    counterexamples['count_star']={'wrong_count':wrong,'correct_paid_orders':0}
    wrong=db.execute("SELECT SUM(DISTINCT billed_cents) FROM orders WHERE customer_id='c1' AND status='paid' AND ordered_ts>=:start AND ordered_ts<:end",params).fetchone()[0]
    check('counterexample','SUM DISTINCT loses legitimate equal-value orders',wrong,3000)
    counterexamples['sum_distinct']={'wrong_cents':wrong,'correct_cents':4000}
    wrong=db.execute("SELECT customer_id FROM customers WHERE tenant_id=:tenant AND customer_id NOT IN (SELECT customer_id FROM exclusions)",params).fetchall()
    check('counterexample','NOT IN NULL produces no included customers',len(wrong),0)
    counterexamples['not_in_null']={'wrong_customers':0,'correct_customers':len(observations['Q08'])}
    wrong=db.execute("SELECT SUM(p.amount_cents),SUM(r.amount_cents) FROM payments p JOIN refunds r USING(order_id) WHERE p.order_id='o01' AND p.status='succeeded'").fetchone()
    check('counterexample','Two child facts multiply payments and refunds',list(wrong),[2000,200])
    counterexamples['two_fact_join']={'wrong_confirmed_cents':wrong[0],'wrong_refund_cents':wrong[1],'correct_confirmed_cents':1000,'correct_refund_cents':100}
    wrong=db.execute("WITH d AS (SELECT date(o.ordered_ts,'unixepoch') day,COALESCE(SUM(o.billed_cents),0) value FROM orders o JOIN customers c USING(customer_id) WHERE c.tenant_id=:tenant AND o.status='paid' GROUP BY day) SELECT SUM(value) OVER(ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) total FROM d ORDER BY day DESC LIMIT 1",params).fetchone()[0]
    correct=expected(fixture,dict(params,report_end_day='2026-10-12'))['Q12'][-1]['rolling_known']
    check('counterexample','Seven sparse revenue rows differ from seven calendar days',[wrong,correct],[11100,1900])
    counterexamples['sparse_window']={'wrong_seven_rows_cents':wrong,'correct_seven_days_cents':correct}
    check('constraint','Foreign-key enforcement is enabled',db.execute('PRAGMA foreign_keys').fetchone()[0],1)
    for name,sql in [('Orphan order rejected',"INSERT INTO orders VALUES ('bad','missing',0,'paid',1,NULL)"),
                     ('Negative billed amount rejected',"INSERT INTO orders VALUES ('bad','c1',0,'paid',-1,NULL)"),
                     ('Duplicate order identity rejected',"INSERT INTO orders SELECT * FROM orders WHERE order_id='o01'")]:
        try:db.execute(sql)
        except sqlite3.IntegrityError:check('constraint',name,True,True);db.rollback()
        else:raise AssertionError(name)
finally:db.close();closed+=1

db=connect()
try:
    # Owned in-memory historical rows strengthen access-path evidence, not a benchmark.
    db.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)',
                   [(f'history-{n}','c1' if n%2 else 'c8',params['start']-1000000-n,'paid',1,None) for n in range(10000)])
    source=(BASE/'queries/q30.sql').read_text(encoding='utf-8')
    before=[dict(row) for row in db.execute('EXPLAIN QUERY PLAN '+source,params)]
    original=query(db,30,params)
    check('query-plan','Unindexed selective order lookup scans orders',any('SCAN o' in row['detail'] for row in before),True)
    db.execute('CREATE INDEX orders_customer_time ON orders(customer_id,ordered_ts,order_id)')
    after=[dict(row) for row in db.execute('EXPLAIN QUERY PLAN '+source,params)]
    check('query-plan','Composite covering index supports selective lookup',any('SEARCH o' in row['detail'] and 'orders_customer_time' in row['detail'] for row in after),True)
    check('query-plan','Index preserves ordered results',query(db,30,params),original)
    plans={'additional_historical_rows':10000,'before':before,'after':after,'result':original,
           'scope':'Actual local SQLite plan evidence; no production timing or cross-engine plan claim'}
finally:db.close();closed+=1
check('preservation','Fixture, parameters, query and reference sources unchanged',
      {str(path.relative_to(BASE)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},hashes)
proof={'verified_date':'2026-10-20','python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
       'total':len(checks),'checks':checks,'observations':observations,'source_sha256':hashes,
       'connections_closed':closed,'persistent_database_created':False,'persistent_listener_started':False,
       'external_services_called':False,'postgresql_executed':False,
       'scope':'30 actual SQLite queries against synthetic data, independent Python reference, reversed insertion, changed-input cases, constraints and local plan evidence; not company question-frequency or production performance verification.'}
for name,data in [('query-output.json',observations),('counterexamples.json',counterexamples),('query-plans.json',plans),('verification-results.json',proof)]:
    (BASE/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'queries':30,'python':proof['python'],'sqlite':proof['sqlite'],
                  'connections_closed':closed,'plans':plans},indent=2))
