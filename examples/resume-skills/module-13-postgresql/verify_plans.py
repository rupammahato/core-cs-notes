from db import prepare,connect
from checks import Checks,equal,require
prepare()
checks=Checks('plans')
observed={}
QUERY="""SELECT id,created_at,payload FROM lesson.events
WHERE tenant_id=%s AND status=%s ORDER BY created_at DESC,id DESC LIMIT 20"""

def nodes(plan):
    yield plan
    for child in plan.get('Plans',[]): yield from nodes(child)

def summary(document):
    keys=['Node Type','Index Name','Plan Rows','Actual Rows','Actual Loops',
          'Rows Removed by Filter','Shared Hit Blocks','Shared Read Blocks']
    return [{key:node[key] for key in keys if key in node} for node in nodes(document['Plan'])]

with connect(admin=True) as conn:
    conn.execute('CREATE TABLE lesson.events (id bigint PRIMARY KEY,tenant_id int NOT NULL,status text NOT NULL,created_at timestamptz NOT NULL,payload text NOT NULL)')
    conn.execute("""INSERT INTO lesson.events SELECT g,(g%100)+1,
        CASE WHEN (g/100)%10<2 THEN 'open' ELSE 'closed' END,
        TIMESTAMPTZ '2026-01-01 00:00:00+00'+g*INTERVAL '1 second',repeat('x',200)||g::text
        FROM generate_series(1,50000) AS g""")
    conn.execute('ANALYZE lesson.events')
    conn.execute('SET max_parallel_workers_per_gather=0')  # Simplify this fixture's plan tree.
    before=conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+QUERY,(7,'open')).fetchone()[0][0]
    expected=conn.execute(QUERY,(7,'open')).fetchall()
    checks.check('unindexed selective ordered fixture naturally scans and sorts',
                 lambda:require(any(n['Node Type']=='Seq Scan' for n in nodes(before['Plan'])) and any(n['Node Type']=='Sort' for n in nodes(before['Plan']))))
    conn.execute('CREATE INDEX events_lookup ON lesson.events (tenant_id,status,created_at DESC,id DESC)')
    conn.execute('ANALYZE lesson.events')
    after=conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+QUERY,(7,'open')).fetchone()[0][0]
    checks.check('composite index preserves the actual result rows',lambda:equal(conn.execute(QUERY,(7,'open')).fetchall(),expected))
    checks.check('planner naturally uses the composite index without a Sort node',
                 lambda:require(any(n.get('Index Name')=='events_lookup' for n in nodes(after['Plan'])) and all(n['Node Type']!='Sort' for n in nodes(after['Plan']))))
    broad=conn.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM lesson.events WHERE status='closed'").fetchone()[0][0]
    checks.check('broad fixture still naturally chooses a sequential scan',
                 lambda:require(any(n['Node Type']=='Seq Scan' for n in nodes(broad['Plan']))))
    observed.update(fixture_rows=conn.execute('SELECT count(*) FROM lesson.events').fetchone()[0],
                    matching_rows=conn.execute("SELECT count(*) FROM lesson.events WHERE tenant_id=7 AND status='open'").fetchone()[0],
                    result_limit=len(expected),before=summary(before),after=summary(after),broad=summary(broad),
                    raw_before=before,raw_after=after,raw_broad=broad,
                    planner_settings={'enable_seqscan':conn.execute('SHOW enable_seqscan').fetchone()[0],'max_parallel_workers_per_gather':0})
    def plain():
        conn.execute('EXPLAIN UPDATE lesson.accounts SET balance=balance+1 WHERE id=1').fetchall()
        equal(conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],100)
    checks.check('plain EXPLAIN does not execute the UPDATE',plain)
    def analyze_write():
        try:
            with conn.transaction():
                conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) UPDATE lesson.accounts SET balance=balance+1 WHERE id=1').fetchall()
                equal(conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],101)
                raise ValueError('rollback fixture mutation')
        except ValueError: pass
        equal(conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],100)
    checks.check('EXPLAIN ANALYZE executes the UPDATE; explicit transaction rollback restores it',analyze_write)
    def concurrent_index():
        from psycopg.errors import ActiveSqlTransaction
        try:
            with conn.transaction(): conn.execute('CREATE INDEX CONCURRENTLY not_created ON lesson.events(status)')
        except ActiveSqlTransaction as error: equal(error.sqlstate,'25001')
        else: raise AssertionError('concurrent index accepted transaction block')
    checks.check('CREATE INDEX CONCURRENTLY is rejected inside a transaction block',concurrent_index)
checks.save(observations=observed,scope='Actual PostgreSQL plans on a 50000-row fixture; counts/plans, not a benchmark')
