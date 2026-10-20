"""Render worked chapters from exact solution files and independently verified SQL rows."""
from datetime import datetime,timezone
import json
from pathlib import Path
from lab import BASE,connect,load_fixture

ROOT=BASE.parents[1]
NOTES=ROOT/'SQL Interview Notes'

def table(rows):
    if not rows:return '_No rows._'
    columns=list(rows[0])
    def shown(value):
        return ('NULL' if value is None else str(value)).replace('|','\\|').replace('\n',' ')
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join('---' for _ in columns)+' |']
    lines+=['| '+' | '.join(shown(row[key]) for key in columns)+' |' for row in rows]
    return '\n'.join(lines)

groups=[
 ('joins',3,'joins-grain-and-null-semantics','Joins, Grain and NULL','Q01-Q08: preserve the intended population and add each measure once.',
  'The first eight tasks make row retention and measure grain explicit. State the difference between no order, cancelled work, an unknown bill and an observed zero. The supplied payment ledger is treated as complete; a real incomplete extract requires another completeness policy.'),
 ('windows',4,'windows-and-time-series','Windows and Time Series','Q09-Q16: rank ties, select stable rows and reason about calendar time.',
  'Different tasks need different ordering contracts. Keep all tied value tiers with DENSE_RANK, but choose one latest row with a deterministic ROW_NUMBER tie-breaker. Dense date spines make calendar windows meaningful; historical dimension selection avoids using future state.'),
 ('analytics',5,'funnels-cohorts-and-retention','Funnels, Cohorts and Retention','Q17-Q24: define behavior, observation maturity and receipt-time knowledge.',
  'The customer signup anchors are UTC midnight in this fixture. State whether a task measures an ordered first-start funnel, an exact-day return, an any-week return or a cart outcome. Hold the behavioral period fixed when studying late knowledge. These synthetic rates do not establish causal product effects.'),
 ('quality',6,'reconciliation-and-query-plans','Reconciliation and Query Plans','Q25-Q30: expose source exceptions and explain the actual access path.',
  'Diagnostics are useful only under a stated authority and source contract. Q26 is an authorized ingestion audit, not a tenant-facing endpoint. Billing, line amounts, confirmed payments and refunds are separate facts; reconcile them before recommending a business action.')]

def build():
    problems=json.loads((BASE/'problems.json').read_text(encoding='utf-8'))
    output=json.loads((BASE/'query-output.json').read_text(encoding='utf-8'))
    proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
    assert proof['total']==86 and proof['observations']==output
    for group,part,slug,title,description,intro in groups:
        chunks=[f'# SQL Interview Problem Book — Part {part}: {title}',f'**{description}**',
                'Verified on Python 3.13.15 / SQLite 3.50.4, 20 October 2026. The full lab passes 86 checks. Inputs are invented; the SQL shown is the exact executed solution.',
                intro,'Read the [dataset and solving contract](/docs/sql-interview/dataset-and-solving-method) before attempting these problems. Use the shared bound parameters from parameters.json.']
        for problem in [row for row in problems if row['group']==group]:
            key=problem['id'];sql=(BASE/problem['query']).read_text(encoding='utf-8').rstrip()
            chunks.extend([f"## {key}. {problem['title']}",problem['prompt'],
                           f"**Hint:** {problem['hint']}",'### Worked query',f'```sql\n{sql}\n```',
                           '### Verified output',table(output[key]),'### Why it works',problem['reasoning'],
                           f"**Common wrong answer:** {problem['trap']}",f"**Interview follow-up:** {problem['follow_up']}"])
        if group=='quality':
            plans=json.loads((BASE/'query-plans.json').read_text(encoding='utf-8'))
            chunks.extend(['## Actual plan evidence for Q30',
                           'A separate in-memory connection adds 10,000 older rows outside the report interval. Before the matching composite index, the engine scans the existing order primary-key index and uses a temporary B-tree for sorting. After the new index it performs a covering search. Both return o01, o02 and o03.',
                           '### Before the composite index',table(plans['before']),
                           '### After the composite index',table(plans['after']),
                           "The verified index definition is:\n\n```sql\nCREATE INDEX orders_customer_time ON orders(customer_id, ordered_ts, order_id);\n```",
                           'EXPLAIN QUERY PLAN text is engine/version-specific and can change. This is local access-path evidence, not a timing benchmark. [SQLite plan output](https://www.sqlite.org/eqp.html), [query planner](https://www.sqlite.org/queryplanner.html).'])
        chunks.extend(['## Practice checkpoint',
                       '- [ ] I can write these queries before reading the solutions.\n- [ ] I can state the output grain and a counterexample to the tempting wrong answer.\n- [ ] I can adapt one boundary or missingness rule and explain the changed result.',
                       'Return to the [roadmap](/docs/sql-interview) or continue with [consolidation and mocks](/docs/sql-interview/consolidation-and-mocks).'])
        (NOTES/f'sql-interview-handbook-part-{part}-{slug}.md').write_text('\n\n'.join(chunks)+'\n',encoding='utf-8')
    method=NOTES/'sql-interview-handbook-part-2-dataset-and-solving-method.md'
    start='<!-- BEGIN SQL FIXTURE TABLES -->';end='<!-- END SQL FIXTURE TABLES -->'
    source=method.read_text(encoding='utf-8').split(start)[0].rstrip()
    chunks=[start,'## 11. Inspect the actual source rows',
            'The tables below are the complete fixture, not abbreviated samples. Timestamp columns are displayed as UTC text for reading; fixture.json and the database store the corresponding integer epoch seconds. NULL remains an unknown value.']
    db=connect()
    try:
        for name,rows in load_fixture()['tables'].items():
            columns=[row['name'] for row in db.execute(f'PRAGMA table_info({name})')]
            display=[]
            for values in rows:
                display.append({column+' (UTC)' if column.endswith('_ts') else column:
                                datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if column.endswith('_ts') else value
                                for column,value in zip(columns,values)})
            chunks.extend([f'### {name}',table(display)])
    finally:db.close()
    chunks.extend([end])
    method.write_text(source+'\n\n'+'\n\n'.join(chunks)+'\n',encoding='utf-8')
    print('Rendered four worked-query chapters and the complete fixture tables.')

if __name__=='__main__':build()
