"""Execute original teaching models and check resume-source provenance."""
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from contextlib import ExitStack
import hashlib
import json
import platform
import sqlite3
import sys
import tempfile
from hierarchy import reports
from sla import business_due, initialize as init_sla, transition, scan
from sheet_sync import initialize as init_sheet, sync_batch, utc_timestamp, merge_patch
from costs import normalized_cost, settle_estimate, relative_growth

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
checks, observations = [], {}


def check(group, name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({'group': group, 'name': name, 'passed': True})


def rejects(group, name, kind, function):
    try:
        function()
    except kind:
        check(group, name, True)
    else:
        raise AssertionError(name + ': expected rejection')


people = {'m': 'alpha', 'a': 'alpha', 'b': 'alpha', 'c': 'alpha', 'x': 'beta'}
links = [('m', 'a', 'line'), ('m', 'b', 'line'), ('a', 'c', 'escalation'), ('b', 'c', 'line'), ('c', 'm', 'line')]
visible = reports('alpha', 'm', people, links)
check('hierarchy', 'Breadth-first order with indirect report', visible == ['a', 'b', 'c'])
check('hierarchy', 'Cycle does not re-add root', 'm' not in visible)
check('hierarchy', 'Diamond does not duplicate shared report', visible.count('c') == 1)
check('hierarchy', 'Leaf has no reports', reports('alpha', 'a', people, []) == [])
check('hierarchy', 'Duplicate relation does not duplicate report', reports('alpha', 'm', people, links + [('m', 'a', 'line')]) == visible)
rejects('hierarchy', 'Cross-tenant root rejected', PermissionError, lambda: reports('beta', 'm', people, links))
rejects('hierarchy', 'Unknown root rejected', PermissionError, lambda: reports('alpha', 'missing', people, links))
rejects('hierarchy', 'Cross-tenant intermediate edge rejected', PermissionError, lambda: reports('alpha', 'm', people, [('m', 'x', 'line'), ('x', 'c', 'line')]))
rejects('hierarchy', 'Missing referenced person rejected', PermissionError, lambda: reports('alpha', 'm', people, [('m', 'absent', 'line')]))
rejects('hierarchy', 'Unknown polymorphic type rejected', ValueError, lambda: reports('alpha', 'm', people, [('m', 'a', 'unreviewed')]))
rejects('hierarchy', 'Traversal overflow returns no partial policy set', ValueError, lambda: reports('alpha', 'm', people, links, max_nodes=3))
rejects('hierarchy', 'Invalid traversal bound rejected', ValueError, lambda: reports('alpha', 'm', people, links, max_nodes=0))
observations['hierarchy'] = {'manager': 'm', 'tenant': 'alpha', 'breadth_first_reports': visible, 'cross_tenant_edge': 'rejected', 'scope': 'Hand-authored graph; line and escalation are illustrative allowed relations, not recovered project semantics.'}

friday = date(2026, 10, 16)
check('sla', 'Zero working days keeps start', business_due(friday, 0) == friday)
check('sla', 'Weekend skipped', business_due(friday, 1) == date(2026, 10, 19))
check('sla', 'Explicit holiday skipped', business_due(friday, 2, {date(2026, 10, 20)}) == date(2026, 10, 21))
rejects('sla', 'Negative working-day count rejected', ValueError, lambda: business_due(friday, -1))
rejects('sla', 'Datetime cannot silently replace business date', ValueError, lambda: business_due(datetime(2026, 10, 16), 1))

temporary_path = None
connections = []
try:
    with ExitStack() as stack:
        temporary = stack.enter_context(tempfile.TemporaryDirectory(prefix='m28-', dir=BASE))
        temporary_path = Path(temporary)
        sla_path = temporary_path / 'sla.sqlite3'
        db = sqlite3.connect(sla_path); connections.append(db); stack.callback(db.close); init_sla(db)
        with db:
            db.executemany('INSERT INTO tasks(tenant,id,due,state) VALUES (?,?,?,?)', [('alpha', 't1', '2026-10-20', 'open'), ('beta', 't1', '2026-10-20', 'open'), ('alpha', 'complete', '2026-10-20', 'done')])
        check('sla', 'Before deadline emits no alerts', scan(db, date(2026, 10, 19)) == 0)
        check('sla', 'Due day emits no overdue alerts', scan(db, date(2026, 10, 20)) == 0)
        check('sla', 'First late scan queues per-tenant tier-one rows', scan(db, date(2026, 10, 21)) == 2)
        check('sla', 'Repeated scan creates no duplicate tier', scan(db, date(2026, 10, 21)) == 0)
        check('sla', 'Completed task excluded', db.execute("SELECT COUNT(*) FROM alerts WHERE task='complete'").fetchone()[0] == 0)
        db.close(); connections.remove(db)
        db = sqlite3.connect(sla_path); connections.append(db); stack.callback(db.close)
        check('sla', 'Fresh connection retains dedupe state', scan(db, date(2026, 10, 22)) == 0)
        check('sla', 'Later tier independently queues once', scan(db, date(2026, 10, 23)) == 2)
        transition(db, 'alpha', 't1', 0, 'in_progress')
        check('sla', 'Valid transition advances version', db.execute("SELECT state,version FROM tasks WHERE tenant='alpha' AND id='t1'").fetchone() == ('in_progress', 1))
        rejects('sla', 'Stale expected version rejected', ValueError, lambda: transition(db, 'alpha', 't1', 0, 'done'))
        rejects('sla', 'Unsupported state reversal rejected', ValueError, lambda: transition(db, 'alpha', 't1', 1, 'open'))
        rejects('sla', 'Foreign-tenant task not found', LookupError, lambda: transition(db, 'gamma', 't1', 1, 'done'))
        # An existing audit key forces the dependent insert to fail after UPDATE.
        with db:
            db.execute("INSERT INTO audit VALUES ('alpha','t1','in_progress','done',2)")
        rejects('sla', 'Audit constraint failure rejects transaction', sqlite3.IntegrityError, lambda: transition(db, 'alpha', 't1', 1, 'done'))
        check('sla', 'Failed audit insert rolls back task update', db.execute("SELECT state,version FROM tasks WHERE tenant='alpha' AND id='t1'").fetchone() == ('in_progress', 1))
        with db:
            db.execute("DELETE FROM audit WHERE tenant='alpha' AND task='t1' AND version=2")
        transition(db, 'alpha', 't1', 1, 'done')
        check('sla', 'Successful terminal transition audited', db.execute("SELECT COUNT(*) FROM audit WHERE tenant='alpha' AND task='t1'").fetchone()[0] == 2)
        check('sla', 'Next scan does not create more alerts for done task', scan(db, date(2026, 10, 24)) == 0)
        rejects('sla', 'Scan refuses implicit datetime policy', ValueError, lambda: scan(db, datetime(2026, 10, 24)))
        observations['sla'] = {'working_day_example': {'start': friday.isoformat(), 'days': 2, 'explicit_holiday': '2026-10-20', 'due': business_due(friday, 2, {date(2026, 10, 20)}).isoformat()}, 'alerts': [list(row) for row in db.execute('SELECT tenant,task,tier,business_date,status FROM alerts ORDER BY tenant,tier')], 'final_alpha_task': list(db.execute("SELECT state,version FROM tasks WHERE tenant='alpha' AND id='t1'").fetchone()), 'scope': 'Real SQLite transactions and reopen persistence. Toy calendar/date and tier policy; no real bureau rules, timezone scheduling or external alert delivery.'}

        sheet = sqlite3.connect(temporary_path / 'sheet.sqlite3'); connections.append(sheet); stack.callback(sheet.close); init_sheet(sheet)
        check('sheet', 'Blank timestamp normalizes to null', utc_timestamp('') is None)
        check('sheet', 'Explicit offset converts to UTC', utc_timestamp('2026-10-16T10:00:00+05:30') == '2026-10-16T04:30:00+00:00')
        rejects('sheet', 'Naive timestamp rejected without source policy', ValueError, lambda: utc_timestamp('2026-10-16T10:00:00'))
        check('sheet', 'Explicit naive-source offset applied', utc_timestamp('2026-10-16T10:00:00', timedelta(hours=5, minutes=30)) == '2026-10-16T04:30:00+00:00')
        rejects('sheet', 'Malformed timestamp rejected', ValueError, lambda: utc_timestamp('not-a-time'))
        first = {'external_id': 'r1', 'timestamp': '', 'patch': {'name': 'one', 'scores': {'a': 1, 'b': 2}, 'children': [{'id': 'c1'}]}}
        sync_batch(sheet, 'alpha', 'sheet1', [first])
        sync_batch(sheet, 'alpha', 'sheet1', [{'external_id': 'r1', 'timestamp': '', 'patch': {'scores': {'a': 3}}}])
        payload = json.loads(sheet.execute("SELECT payload FROM records WHERE tenant='alpha'").fetchone()[0])
        check('sheet', 'Blank-timestamp stable ID updates one row', sheet.execute("SELECT COUNT(*) FROM records WHERE tenant='alpha'").fetchone()[0] == 1)
        check('sheet', 'Nested omitted score survives patch', payload['scores'] == {'a': 3, 'b': 2})
        check('sheet', 'Omitted child collection survives patch', payload['children'] == [{'id': 'c1'}])
        check('sheet', 'Array replacement is explicit policy', merge_patch(payload, {'children': []})['children'] == [])
        check('sheet', 'Null is stored rather than implicit deletion', merge_patch({'x': 1}, {'x': None}) == {'x': None})
        sync_batch(sheet, 'beta', 'sheet1', [first])
        check('sheet', 'Equal external IDs isolated by tenant', sheet.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 2)
        sync_batch(sheet, 'alpha', 'sheet2', [first])
        check('sheet', 'Equal external IDs isolated by source', sheet.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 3)
        rejects('sheet', 'Missing stable identity rejected', ValueError, lambda: sync_batch(sheet, 'alpha', 'sheet1', [{'patch': {}}]))
        stamp = '2026-10-16T04:30:00Z'
        sync_batch(sheet, 'alpha', 'sheet1', [{'external_id': 'r1', 'timestamp': stamp, 'patch': {}}])
        rejects('sheet', 'Conflicting timestamp identity fails closed', ValueError, lambda: sync_batch(sheet, 'alpha', 'sheet1', [{'external_id': 'r2', 'timestamp': stamp, 'patch': {}}]))
        sync_batch(sheet, 'alpha', 'sheet1', [{'external_id': 'r1', 'timestamp': '', 'patch': {'name': 'two'}}])
        check('sheet', 'Blank patch timestamp preserves previous timestamp', sheet.execute("SELECT observed_at FROM records WHERE tenant='alpha' AND source='sheet1'").fetchone()[0] == '2026-10-16T04:30:00+00:00')
        bad_batch = [{'external_id': 'r1', 'timestamp': '', 'patch': {'name': 'should-rollback'}}, {'external_id': '', 'patch': {}}]
        rejects('sheet', 'Invalid later batch row rejects whole transaction', ValueError, lambda: sync_batch(sheet, 'alpha', 'sheet1', bad_batch))
        final_payload = json.loads(sheet.execute("SELECT payload FROM records WHERE tenant='alpha' AND source='sheet1'").fetchone()[0])
        check('sheet', 'Earlier row change rolled back with batch', final_payload['name'] == 'two')
        rejects('sheet', 'Missing tenant rejected', ValueError, lambda: sync_batch(sheet, '', 'sheet1', [first]))
        observations['sheet'] = {'utc_offset_example': utc_timestamp('2026-10-16T10:00:00+05:30'), 'alpha_sheet1': {'external_id': 'r1', 'observed_at': '2026-10-16T04:30:00+00:00', 'payload': final_payload}, 'rows_across_tenants_and_sources': sheet.execute('SELECT COUNT(*) FROM records').fetchone()[0], 'scope': 'Real SQLite batch rollback and scoped external-ID upserts. Partial unique nonblank timestamp is a toy source contract; no original MongoDB/OneDrive sync was reproduced.'}
        for connection in connections:
            connection.close()
        connections.clear()
finally:
    for connection in connections:
        connection.close()
    cleanup = {'temporary_directory_removed': temporary_path is None or not temporary_path.exists(), 'sqlite_connections_closed': True, 'persistent_listener_started': False}
    (BASE / 'cleanup-results.json').write_text(json.dumps(cleanup, indent=2) + '\n', encoding='utf-8')

check('costs', 'Input-token unit denominator applied', normalized_cost('1200', '2', '1000000') == Decimal('0.0024'))
check('costs', 'Output-token rate remains separate', normalized_cost('300', '8', '1000000') == Decimal('0.0024'))
check('costs', 'Per-image charge uses per-image units', normalized_cost('2', '0.04', '1') == Decimal('0.08'))
estimate = settle_estimate([('1200', '2', '1000000'), ('300', '8', '1000000'), ('2', '0.04', '1')])
check('costs', 'Mixed unit lines sum to synthetic total', estimate['unrounded_usd'] == '0.0848')
check('costs', 'Settlement rounds at declared microdollar precision', estimate['settled_usd'] == '0.084800')
rejects('costs', 'Binary float rate rejected', ValueError, lambda: normalized_cost('1', 0.1, '1'))
rejects('costs', 'Negative usage rejected', ValueError, lambda: normalized_cost('-1', '1', '1'))
rejects('costs', 'Zero denominator rejected', ValueError, lambda: normalized_cost('1', '1', '0'))
rejects('costs', 'Nonfinite decimal rejected', ValueError, lambda: normalized_cost('NaN', '1', '1'))
rejects('costs', 'Malformed decimal rejected', InvalidOperation, lambda: normalized_cost('bad', '1', '1'))
check('costs', 'Zero usage has zero cost', normalized_cost('0', '5', '1') == 0)
check('costs', 'Round total rather than each tiny line', settle_estimate([('1', '0.0000004', '1')] * 3)['settled_usd'] == '0.000001')
check('metrics', 'Synthetic growth example equals reported percentage only arithmetically', relative_growth('10000', '14270') == Decimal('42.700'))
check('metrics', 'Decrease has negative growth', relative_growth('100', '80') == Decimal('-20.0'))
rejects('metrics', 'Zero baseline cannot produce percent growth', ValueError, lambda: relative_growth('0', '10'))
rejects('metrics', 'Nonfinite baseline rejected', ValueError, lambda: relative_growth('NaN', '10'))
check('metrics', '45 of 49 commit ratio does not equal work fraction', Decimal(45) / Decimal(49) > Decimal('0.9'))
observations['costs'] = {'synthetic_lines': [{'kind': 'input_tokens', 'usage': '1200', 'usd_per_million': '2'}, {'kind': 'output_tokens', 'usage': '300', 'usd_per_million': '8'}, {'kind': 'images', 'usage': '2', 'usd_per_image': '0.04'}], 'estimate': estimate, 'scope': 'Invented teaching prices, not live provider rates or the resume USD 0.05 claim.'}
observations['metrics'] = {'synthetic_growth': {'before': 10000, 'after': 14270, 'percent': str(relative_growth('10000', '14270'))}, 'reported_commit_ratio': {'numerator': 45, 'denominator': 49, 'percent_arithmetic': str(Decimal(45) / Decimal(49) * 100)}, 'scope': 'Growth counts are invented examples, not Megalith analytics. Commit-count ratio is arithmetic over a reported claim, not independent Git evidence or effort attribution.'}

catalogue = json.loads((BASE / 'resume-evidence.json').read_text(encoding='utf-8'))
for source in catalogue['sources']:
    check('evidence', source['file'] + ' checksum matches user PDF', hashlib.sha256((ROOT / source['file']).read_bytes()).hexdigest() == source['sha256'])
    check('evidence', source['file'] + ' contains seven distinct projects', len(source['excerpts']) == len({e['project_id'] for e in source['excerpts']}) == 7)
    check('evidence', source['file'] + ' keeps reported scope explicit', all(e['evidence_class'] == 'resume-reported' and not e['original_code_or_metrics_reproduced'] for e in source['excerpts']))
for identity in ('neosophical', 'datsol', '10x', 'zyke', 'load-balancer', 'megalith', 'membition'):
    check('evidence', identity + ' has both resume excerpts', all(any(e['project_id'] == identity and e['text'].startswith(e['anchor']) for e in s['excerpts']) for s in catalogue['sources']))
counts = {group: sum(c['group'] == group for c in checks) for group in dict.fromkeys(c['group'] for c in checks)}
proof = {'module': 28, 'verified_date': '2026-10-16', 'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version, 'os': platform.platform(), 'total': len(checks), 'counts': counts, 'checks': checks, 'observations': observations, 'cleanup': cleanup, 'scope': 'Original teaching models over hand-authored inputs and real local SQLite transactions; resume catalogue fidelity. No original employer/project code, production metrics, provider calls or payroll compliance reproduced.'}
(BASE / 'verification-results.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'total': proof['total'], 'counts': counts, 'observations': observations, 'cleanup': cleanup}, indent=2))
