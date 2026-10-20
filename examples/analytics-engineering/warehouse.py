"""Owned in-memory warehouse: bounded raw prefix, candidate checks and atomic publication."""
import json
from pathlib import Path
import sqlite3
from datetime import date

BASE=Path(__file__).resolve().parent


class QualityError(ValueError):
    pass


def fixture():
    return json.loads((BASE/'fixture.json').read_text(encoding='utf-8'))


def rows(db,sql,params=()):
    return [dict(row) for row in db.execute(sql,params)]


def connect():
    db=sqlite3.connect(':memory:',isolation_level=None)
    db.row_factory=sqlite3.Row
    try:
        db.executescript((BASE/'schema.sql').read_text(encoding='utf-8'))
        db.executemany('INSERT INTO order_lines VALUES(?,?,?,?)',fixture()['illustrative_order_lines'])
        return db
    except BaseException:
        db.close();raise


def normalized(change):
    required={'delivery_id','stream','tenant_id','entity_id','source_version','payload'}
    if set(change)!=required:raise ValueError('Unexpected envelope fields')
    for key in ['delivery_id','tenant_id','entity_id']:
        if not isinstance(change[key],str) or not change[key].strip():raise ValueError('Nonempty identities required')
    if change['entity_id']=='__unknown__':raise ValueError('Reserved warehouse identity')
    version=change['source_version'];payload=change['payload']
    if isinstance(version,bool) or not isinstance(version,int) or version<1:raise ValueError('Positive source version required')
    if not isinstance(payload,dict) or payload.get('schema_version')!=1:raise ValueError('Unsupported payload schema version')
    if change['stream']=='customers':
        date.fromisoformat(payload['effective_from'])
        if not isinstance(payload['plan'],str) or not payload['plan']:raise ValueError('Plan required')
    elif change['stream']=='orders':
        date.fromisoformat(payload['order_day'])
        if payload['op'] not in ['U','D'] or payload['status'] not in ['paid','cancelled']:raise ValueError('Invalid operation/status')
        if not isinstance(payload['customer_id'],str) or not payload['customer_id']:raise ValueError('Customer required')
        amount=payload['billed_cents']
        if amount is not None and (isinstance(amount,bool) or not isinstance(amount,int)):raise ValueError('Integer cents or NULL required')
        # Negative source amounts land in raw; publication rejects them as a semantic failure.
    else:raise ValueError('Unsupported stream')
    return (change['delivery_id'],change['stream'],change['tenant_id'],change['entity_id'],version,
            json.dumps(payload,sort_keys=True,separators=(',',':')))


def ingest(db,changes):
    added=0;db.execute('BEGIN')
    try:
        for change in changes:
            values=normalized(change)
            old=db.execute('SELECT delivery_id,stream,tenant_id,entity_id,source_version,payload_json FROM raw_changes WHERE delivery_id=?',(values[0],)).fetchone()
            if old:
                if tuple(old)!=values:raise ValueError('Delivery identity reused with different content')
                continue
            db.execute('INSERT INTO raw_changes(delivery_id,stream,tenant_id,entity_id,source_version,payload_json) VALUES(?,?,?,?,?,?)',values)
            added+=1
        db.execute('COMMIT');return added
    except BaseException:
        db.execute('ROLLBACK');raise


def state(db):
    return dict(db.execute('SELECT * FROM pipeline_state').fetchone())


def mart(db,run_id=None):
    run_id=run_id or state(db)['active_run']
    return rows(db,'SELECT tenant_id,order_day,plan,paid_orders,known_bill_cents,missing_bills,complete_bill_cents FROM mart_daily WHERE run_id=? ORDER BY tenant_id,order_day,plan',(run_id,))


def facts(db):
    return rows(db,'SELECT f.*,d.plan FROM fact_orders f JOIN dim_customer d USING(tenant_id,customer_sk) ORDER BY f.tenant_id,f.order_id')


def bounded_candidates(db,upper):
    for name in ['bounded_changes','blocked_entities','valid_changes','next_dim','next_fact','next_mart']:
        db.execute(f'DROP TABLE IF EXISTS temp.{name}')
    db.execute('CREATE TEMP TABLE bounded_changes AS SELECT * FROM raw_changes WHERE ingest_seq<=?',(upper,))
    db.execute('''CREATE TEMP TABLE blocked_entities AS
      SELECT DISTINCT stream,tenant_id,entity_id FROM (
       SELECT stream,tenant_id,entity_id,source_version FROM bounded_changes
       GROUP BY stream,tenant_id,entity_id,source_version HAVING COUNT(DISTINCT payload_json)>1)''')
    db.execute('''CREATE TEMP TABLE valid_changes AS
      SELECT b.* FROM bounded_changes b WHERE NOT EXISTS(
       SELECT 1 FROM blocked_entities x WHERE x.stream=b.stream AND x.tenant_id=b.tenant_id AND x.entity_id=b.entity_id)
      AND b.ingest_seq=(SELECT MIN(r.ingest_seq) FROM bounded_changes r
       WHERE r.stream=b.stream AND r.tenant_id=b.tenant_id AND r.entity_id=b.entity_id AND r.source_version=b.source_version)''')
    db.execute('CREATE TEMP TABLE next_dim AS '+(BASE/'models/customer_dimension.sql').read_text(encoding='utf-8'))
    db.execute('CREATE TEMP TABLE next_fact AS '+(BASE/'models/order_facts.sql').read_text(encoding='utf-8'))
    db.execute('CREATE TEMP TABLE next_mart AS '+(BASE/'models/daily_mart.sql').read_text(encoding='utf-8'))


def quality(db):
    tests={
      'duplicate_fact_keys':'''SELECT COUNT(*) FROM (SELECT tenant_id,order_id FROM next_fact GROUP BY tenant_id,order_id HAVING COUNT(*)<>1)''',
      'negative_bills':'''SELECT COUNT(*) FROM next_fact WHERE billed_cents<0''',
      'missing_dimension_references':'''SELECT COUNT(*) FROM next_fact f WHERE NOT EXISTS(SELECT 1 FROM next_dim d WHERE d.tenant_id=f.tenant_id AND d.customer_sk=f.customer_sk)''',
      'invalid_dimension_intervals':'''SELECT COUNT(*) FROM next_dim WHERE valid_to<=valid_from''',
      'overlapping_dimension_intervals':'''SELECT COUNT(*) FROM next_dim a JOIN next_dim b ON a.tenant_id=b.tenant_id AND a.customer_id=b.customer_id AND a.valid_from<b.valid_from AND a.is_unknown=0 AND b.is_unknown=0 AND (a.valid_to IS NULL OR b.valid_from<a.valid_to)''',
      'duplicate_dimension_keys':'''SELECT COUNT(*) FROM(SELECT tenant_id,customer_sk FROM next_dim GROUP BY tenant_id,customer_sk HAVING COUNT(*)<>1)''',
      'paid_count_reconciliation':'''SELECT ABS((SELECT COUNT(*) FROM next_fact WHERE status='paid')-COALESCE((SELECT SUM(paid_orders) FROM next_mart),0))''',
      'known_amount_reconciliation':'''SELECT ABS(COALESCE((SELECT SUM(billed_cents) FROM next_fact WHERE status='paid'),0)-COALESCE((SELECT SUM(known_bill_cents) FROM next_mart),0))''',
    }
    return {name:db.execute(sql).fetchone()[0] for name,sql in tests.items()}


def publish(db,run_id,force_full=False,fail_after_replace=False):
    db.execute('BEGIN')
    try:
        prior=state(db);upper=db.execute('SELECT COALESCE(MAX(ingest_seq),0) FROM raw_changes').fetchone()[0]
        existing=db.execute('SELECT * FROM runs WHERE run_id=?',(run_id,)).fetchone()
        if existing:
            if existing['upper_seq']!=upper:raise ValueError('Run identity cannot be reused for a different raw prefix')
            db.execute('COMMIT');return {'already_published':True,'run_id':run_id}
        old=facts(db)
        bounded_candidates(db,upper)
        report=quality(db)
        if any(report.values()):raise QualityError(json.dumps(report,sort_keys=True))
        new=rows(db,'SELECT f.*,d.plan FROM next_fact f JOIN next_dim d USING(tenant_id,customer_sk) ORDER BY f.tenant_id,f.order_id')
        old_map={(r['tenant_id'],r['order_id']):r for r in old};new_map={(r['tenant_id'],r['order_id']):r for r in new}
        changed={key for key in old_map.keys()|new_map.keys() if old_map.get(key)!=new_map.get(key)}
        affected={(r['tenant_id'],r['order_day']) for key in changed for r in [old_map.get(key),new_map.get(key)] if r and r['status']=='paid'}
        full=rows(db,'SELECT * FROM next_mart ORDER BY tenant_id,order_day,plan')
        selected=full if force_full or prior['active_run'] is None else [r for r in mart(db) if (r['tenant_id'],r['order_day']) not in affected]+[r for r in full if (r['tenant_id'],r['order_day']) in affected]
        selected=sorted(selected,key=lambda r:(r['tenant_id'],r['order_day'],r['plan']))
        if selected!=full:raise QualityError('Incremental result differs from full candidate')
        db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(run_id,prior['committed_seq'],upper,'full' if force_full else 'partition_refresh','paid-billing-v1'))
        for row in selected:
            db.execute('INSERT INTO mart_daily VALUES(?,?,?,?,?,?,?,?)',(run_id,*row.values()))
        db.execute('DELETE FROM fact_orders');db.execute('DELETE FROM dim_customer')
        db.execute('INSERT INTO dim_customer SELECT * FROM next_dim')
        db.execute('INSERT INTO fact_orders SELECT * FROM next_fact')
        if fail_after_replace:raise RuntimeError('Injected failure after candidate replacement, before pointer/checkpoint commit')
        db.execute('UPDATE pipeline_state SET committed_seq=?,active_run=? WHERE singleton=1',(upper,run_id))
        db.execute('COMMIT')
        return {'run_id':run_id,'lower_seq':prior['committed_seq'],'upper_seq':upper,
                'affected_partitions':[{'tenant_id':t,'order_day':d} for t,d in sorted(affected)],
                'changed_order_keys':len(changed),'quality_failures':report,
                'unknown_fact_rows':sum(r['customer_sk']=='unknown' for r in new),
                'quarantined_entities':db.execute('SELECT COUNT(*) FROM blocked_entities').fetchone()[0],
                'incremental_equals_full':True}
    except BaseException:
        db.execute('ROLLBACK');raise
