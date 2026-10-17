"""Real PostgreSQL/pgvector mechanics with authored vectors; no model/provider calls."""
from collections import Counter
from dataclasses import replace
from pathlib import Path
import importlib.metadata
import json
import math
import platform
import random
import psycopg
from cluster import temporary_cluster
from vectors import SPACE, cosine, dot, l2, literal, normalize, recall_at_k
from store import scoped, publish, search, delete_document
from pinecone_contract import namespace_for, record_id, upsert_body, query_body, delete_body

BASE = Path(__file__).resolve().parent
checks = []
observations = {}


def check(group, name, condition):
    checks.append({'group': group, 'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)


def rejects(group, name, fn, error=ValueError):
    try:
        fn()
    except error:
        check(group, name, True)
    else:
        check(group, name, False)


def scalar(conn, statement, params=()):
    return conn.execute(statement, params).fetchone()[0]


def plan_names(node):
    names = [node.get('Index Name', node['Node Type'])]
    for child in node.get('Plans', []):
        names.extend(plan_names(child))
    return names


def run_ann(admin):
    rng = random.Random(24)
    vectors = [[round(rng.uniform(-1, 1), 6) for _ in range(8)] for _ in range(1000)]
    admin.execute('CREATE TABLE ann_vectors (id integer PRIMARY KEY, category text NOT NULL, embedding vector(8) NOT NULL)')
    with admin.cursor() as cur:
        cur.executemany('INSERT INTO ann_vectors VALUES (%s,%s,%s::vector)',
                        [(i, 'rare' if i % 20 == 0 else 'common', literal(v)) for i, v in enumerate(vectors)])
    admin.execute('ANALYZE ann_vectors')
    queries = [vectors[i] for i in (1, 55, 200, 444, 700)]
    def nearest(query, category=None):
        where = 'WHERE category=%s' if category else ''
        params = (category, literal(query)) if category else (literal(query),)
        return [r[0] for r in admin.execute(f'SELECT id FROM ann_vectors {where} ORDER BY embedding <=> %s::vector LIMIT 5', params)]
    exact = [nearest(q) for q in queries]
    rare_exact = nearest(queries[0], 'rare')
    check('ann', 'exact ground truth has five unique neighbors for each query', all(len(set(ids)) == 5 for ids in exact))
    check('ann', 'self neighbor is nearest under exact cosine', [ids[0] for ids in exact] == [1, 55, 200, 444, 700])
    exact_plan = plan_names(admin.execute('EXPLAIN (FORMAT JSON) SELECT id FROM ann_vectors ORDER BY embedding <=> %s::vector LIMIT 5',
                                         (literal(queries[0]),)).fetchone()[0][0]['Plan'])
    check('ann', 'exact query plan scans and sorts without an ANN index', 'Seq Scan' in exact_plan and 'Sort' in exact_plan)
    admin.execute('SET max_parallel_maintenance_workers=0')
    admin.execute('CREATE INDEX ann_hnsw ON ann_vectors USING hnsw (embedding vector_cosine_ops)')
    admin.execute('SET enable_seqscan=off')
    admin.execute('SET hnsw.ef_search=100')
    hnsw = [nearest(q) for q in queries]
    hplan = plan_names(admin.execute('EXPLAIN (FORMAT JSON) SELECT id FROM ann_vectors ORDER BY embedding <=> %s::vector LIMIT 5',
                                    (literal(queries[0]),)).fetchone()[0][0]['Plan'])
    check('ann', 'HNSW operator query actually uses ann_hnsw', 'ann_hnsw' in hplan)
    hrecall = [recall_at_k(a, b) for a, b in zip(exact, hnsw)]
    check('ann', 'HNSW sampled recall is within valid range and at least 0.8', all(0.8 <= r <= 1 for r in hrecall))
    check('ann', 'HNSW returns five neighbors on these unfiltered queries', all(len(ids) == 5 for ids in hnsw))
    admin.execute('SET hnsw.ef_search=10')
    admin.execute('SET hnsw.iterative_scan=off')
    rare_limited = nearest(queries[0], 'rare')
    admin.execute('SET hnsw.iterative_scan=strict_order')
    admin.execute('SET hnsw.max_scan_tuples=20000')
    rare_iterative = nearest(queries[0], 'rare')
    check('ann', 'selective filter demonstrates underfilled noniterative ANN', len(rare_limited) < 5)
    check('ann', 'iterative HNSW supplies five filtered neighbors on fixture', len(rare_iterative) == 5)
    check('ann', 'iterative filtered results obey predicate', all(i % 20 == 0 for i in rare_iterative))
    check('ann', 'iterative filtered recall does not regress on fixture', recall_at_k(rare_exact, rare_iterative) >= recall_at_k(rare_exact, rare_limited))
    bad_plan = plan_names(admin.execute('EXPLAIN (FORMAT JSON) SELECT id FROM ann_vectors ORDER BY 1 - (embedding <=> %s::vector) DESC LIMIT 5',
                                       (literal(queries[0]),)).fetchone()[0][0]['Plan'])
    check('ann', 'rewritten similarity sort does not use the ANN distance index', 'ann_hnsw' not in bad_plan)
    admin.execute('DROP INDEX ann_hnsw')
    admin.execute('CREATE INDEX ann_ivf ON ann_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists=10)')
    admin.execute('SET ivfflat.probes=4')
    ivf = [nearest(q) for q in queries]
    iplan = plan_names(admin.execute('EXPLAIN (FORMAT JSON) SELECT id FROM ann_vectors ORDER BY embedding <=> %s::vector LIMIT 5',
                                    (literal(queries[0]),)).fetchone()[0][0]['Plan'])
    check('ann', 'IVFFlat operator query actually uses ann_ivf', 'ann_ivf' in iplan)
    irecall = [recall_at_k(a, b) for a, b in zip(exact, ivf)]
    check('ann', 'IVFFlat sampled recall is valid and at least 0.4', all(0.4 <= r <= 1 for r in irecall))
    admin.execute('SET enable_indexscan=off')
    admin.execute('SET enable_bitmapscan=off')
    admin.execute('SET enable_seqscan=on')
    rechecked = [nearest(q) for q in queries]
    check('ann', 'sequential ground truth unchanged after ANN index creation', rechecked == exact)
    check('ann', 'recall counts relevant IDs rather than arbitrary similarity scores', recall_at_k([1, 2, 3, 4, 5], [1, 2, 99]) == 0.4)
    observations['ann'] = {'rows': 1000, 'dimensions': 8, 'queries': 5, 'k': 5,
        'exact_plan': exact_plan, 'hnsw_plan': hplan, 'ivfflat_plan': iplan,
        'hnsw_ef_search': 100, 'hnsw_recall_at_5': hrecall,
        'ivfflat_lists': 10, 'ivfflat_probes': 4, 'ivfflat_recall_at_5': irecall,
        'filtered_exact': rare_exact, 'filtered_noniterative': rare_limited,
        'filtered_iterative': rare_iterative, 'rewritten_sort_plan': bad_plan,
        'planner_note': 'enable_seqscan=off used only to demonstrate actual index paths; no latency/capacity claim'}


def main():
    q = [1, 0, 0]
    points = {'near': [0.8, 0.2, 0], 'large': [10, 1, 0], 'opposite': [-1, 0, 0]}
    ranks = {
        'cosine': sorted(points, key=lambda key: -cosine(q, points[key])),
        'dot': sorted(points, key=lambda key: -dot(q, points[key])),
        'l2': sorted(points, key=lambda key: l2(q, points[key])),
    }
    check('math', 'dot magnitude calculation', dot(q, points['large']) == 10)
    check('math', 'cosine ignores positive scaling', math.isclose(cosine(q, [3, 0, 0]), 1))
    check('math', 'opposite vectors cosine minus one', cosine(q, [-1, 0, 0]) == -1)
    check('math', 'orthogonal vectors cosine zero', cosine(q, [0, 1, 0]) == 0)
    check('math', 'L2 is symmetric', l2(q, points['large']) == l2(points['large'], q))
    check('math', 'identical vectors distance zero', l2(q, q) == 0)
    check('math', 'metric changes rankings when magnitudes vary', ranks['cosine'] != ranks['l2'])
    check('math', 'normalized L2 squared equals twice cosine distance', math.isclose(l2(normalize(q), normalize(points['near'])) ** 2, 2 * (1 - cosine(q, points['near']))))
    check('math', 'normalized dot equals cosine', math.isclose(dot(normalize(q), normalize(points['near'])), cosine(q, points['near'])))
    rejects('math', 'normalizing zero rejected', lambda: normalize([0, 0, 0]))
    rejects('math', 'mismatched dot dimensions rejected', lambda: dot([1], [1, 2]))
    rejects('math', 'mismatched L2 dimensions rejected', lambda: l2([1], [1, 2]))
    observations['math'] = {'query': q, 'vectors': points, 'rankings': ranks,
        'large_dot': dot(q, points['large']), 'large_cosine': round(cosine(q, points['large']), 6),
        'near_l2': round(l2(q, points['near']), 6)}
    check('space', 'compatible dimensions accepted', SPACE.validate(q, SPACE.key) == [1.0, 0.0, 0.0])
    for name, vector in [('short', [1, 2]), ('zero', [0, 0, 0]), ('NaN', [math.nan, 1, 0]),
                         ('Infinity', [math.inf, 1, 0]), ('string', ['1', 0, 0]), ('boolean', [True, 0, 0])]:
        rejects('space', name + ' rejected by application', lambda v=vector: SPACE.validate(v, SPACE.key))
    for field, value in [('model', 'different'), ('revision', 'v2'), ('preprocessing', 'lowercase'), ('metric', 'dot')]:
        rejects('space', field + ' mismatch rejected even at same dimensions', lambda f=field, v=value: SPACE.validate(q, replace(SPACE, **{f: v}).key))
    body = upsert_body('alpha', 'notes', 2, 0, q)
    qb = query_body('alpha', q, 5)
    db = delete_body('alpha', 'notes', 2, [0, 1])
    check('contract', 'upsert body selects trusted namespace', body['namespace'] == namespace_for('alpha'))
    check('contract', 'namespaces differ between authenticated tenants', namespace_for('alpha') != namespace_for('beta'))
    check('contract', 'versioned deterministic record IDs', record_id('notes', 2, 0) == record_id('notes', 2, 0) == 'notes:r2:c0')
    check('contract', 'new revision has distinct record IDs', record_id('notes', 3, 0) != record_id('notes', 2, 0))
    check('contract', 'query carries mandatory filters', len(qb['filter']['$and']) == 2)
    check('contract', 'query omits values and requests metadata', qb['includeValues'] is False and qb['includeMetadata'] is True)
    check('contract', 'delete explicitly names owned record IDs', db['ids'] == ['notes:r2:c0', 'notes:r2:c1'])
    rejects('contract', 'unknown namespace denied', lambda: query_body('attacker', q), PermissionError)
    rejects('contract', 'invalid record ID rejected', lambda: record_id('../notes', 1, 0))
    rejects('contract', 'empty delete does not become deleteAll', lambda: delete_body('alpha', 'notes', 1, []))
    rejects('contract', 'top_k application cap enforced', lambda: query_body('alpha', q, 101))
    rejects('contract', 'incompatible space cannot be upserted', lambda: upsert_body('alpha', 'notes', 1, 0, q, 'wrong'))
    observations['pinecone_contract'] = {'upsert': body, 'query': qb, 'delete': db,
        'executed_scope': 'JSON request-body construction only; no SDK, HTTP or hosted Pinecone'}
    with temporary_cluster() as (params, cleanup):
        with psycopg.connect(**params, autocommit=True) as admin, psycopg.connect(
                **{**params, 'user': 'm24_app', 'password': 'public-local-app-demo'}, autocommit=True) as app:
            check('engine', 'actual pgvector extension version', cleanup['pgvector'] == '0.8.6')
            check('engine', 'local role cannot bypass RLS', scalar(admin, "SELECT NOT rolsuper AND NOT rolbypassrls FROM pg_roles WHERE rolname='m24_app'"))
            metrics = admin.execute("SELECT '[1,0,0]'::vector <-> '[0.8,0.2,0]'::vector, '[1,0,0]'::vector <#> '[10,1,0]'::vector, '[1,0,0]'::vector <=> '[10,1,0]'::vector").fetchone()
            check('engine', 'engine L2 agrees with Python within float32 tolerance', math.isclose(metrics[0], l2(q, points['near']), abs_tol=1e-6))
            check('engine', 'inner product operator returns negative dot', metrics[1] == -10)
            check('engine', 'cosine distance agrees with Python', math.isclose(metrics[2], 1-cosine(q, points['large']), abs_tol=1e-6))
            for value in ('[NaN,1,0]', '[Infinity,1,0]', '[-Infinity,1,0]'):
                rejects('engine', 'pgvector rejects ' + value, lambda v=value: scalar(admin, 'SELECT %s::vector', (v,)), psycopg.Error)
            rejects('engine', 'vector column cast rejects dimension mismatch', lambda: scalar(admin, "SELECT '[1,2]'::vector(3)"), psycopg.Error)
            check('engine', 'raw cosine zero vector distance is NaN', math.isnan(scalar(admin, "SELECT '[0,0,0]'::vector <=> '[1,0,0]'::vector")))
            check('engine', 'raw NULL distance stays NULL', scalar(admin, "SELECT NULL::vector <=> '[1,0,0]'::vector") is None)
            admin.execute("INSERT INTO documents VALUES ('alpha','notes',1,false),('beta','notes',1,false),('alpha','other',1,false)")
            check('lifecycle', 'publish alpha revision 1', publish(app, 'alpha', 'notes', 1, [('near text', points['near']), ('large text', points['large']), ('opposite text', points['opposite'])]))
            check('lifecycle', 'publish beta private content', publish(app, 'beta', 'notes', 1, [('private beta', q)]))
            check('lifecycle', 'publish another alpha document', publish(app, 'alpha', 'other', 1, [('orthogonal', [0, 1, 0])]))
            results = search(app, 'alpha', q, 5)
            check('retrieval', 'exact search sorted by cosine with deterministic tie break', [r['content'] for r in results] == ['large text', 'near text', 'orthogonal', 'opposite text'])
            check('retrieval', 'alpha cannot retrieve the closest beta vector', all('beta' not in r['content'] for r in results))
            check('retrieval', 'top_k bounds quantity', len(search(app, 'alpha', q, 2)) == 2)
            check('retrieval', 'threshold can return no matches', search(app, 'alpha', q, 5, 1) == [])
            check('retrieval', 'threshold and top_k are different constraints', len(search(app, 'alpha', q, 5, 0.98)) == 1)
            rejects('retrieval', 'bad top_k rejected', lambda: search(app, 'alpha', q, 0))
            rejects('retrieval', 'NaN query rejected before SQL', lambda: search(app, 'alpha', [math.nan, 0, 0]))
            rejects('retrieval', 'incompatible model query rejected', lambda: search(app, 'alpha', q, space_key='wrong'))
            check('authorization', 'unset application tenant sees no documents', scalar(app, 'SELECT count(*) FROM documents') == 0)
            with app.transaction():
                scoped(app, 'alpha')
                check('authorization', 'RLS hides beta even without explicit tenant WHERE', scalar(app, 'SELECT count(*) FROM documents') == 2)
                check('authorization', 'RLS blocks direct beta lookup', scalar(app, "SELECT count(*) FROM chunks WHERE tenant_id='beta'") == 0)
                check('authorization', 'RLS rejects cross-tenant update by hiding row', app.execute("UPDATE documents SET revision=99 WHERE tenant_id='beta'").rowcount == 0)
            rejects('authorization', 'RLS WITH CHECK denies cross-tenant insert', lambda: app.execute("INSERT INTO documents VALUES ('beta','intruder',1,false)"), psycopg.Error)
            check('authorization', 'transaction-local tenant does not persist', scalar(app, "SELECT coalesce(current_setting('app.tenant',true),'')") == '')
            check('authorization', 'same connection can safely switch to beta', [r['content'] for r in search(app, 'beta', q)] == ['private beta'])
            rejects('authorization', 'backend refuses unknown authenticated tenant', lambda: search(app, 'outsider', q), PermissionError)
            observations['retrieval'] = {'alpha_cosine_results': results, 'threshold_0_98': search(app, 'alpha', q, 5, 0.98),
                'beta_results': search(app, 'beta', q), 'scope_after_transaction': scalar(app, "SELECT coalesce(current_setting('app.tenant',true),'')")}
            # Error after DELETE/first INSERT must restore the previous generation.
            rejects('lifecycle', 'failed publication rolls back replacement', lambda: publish(app, 'alpha', 'notes', 1, [('temporary', q), (None, q)]), psycopg.Error)
            check('lifecycle', 'original vector rows survive publication rollback', search(app, 'alpha', q) == results)
            admin.execute("UPDATE documents SET revision=2 WHERE tenant_id='alpha' AND document_id='notes'")
            check('lifecycle', 'stale revision is hidden before new publication', [r['content'] for r in search(app, 'alpha', q)] == ['orthogonal'])
            check('lifecycle', 'late revision 1 worker rejected', publish(app, 'alpha', 'notes', 1, [('late', q)]) is False)
            check('lifecycle', 'revision 2 publishes atomically', publish(app, 'alpha', 'notes', 2, [('current', q)]))
            check('lifecycle', 'retry same deterministic generation does not duplicate rows', publish(app, 'alpha', 'notes', 2, [('current', q)]) and scalar(admin, "SELECT count(*) FROM chunks WHERE tenant_id='alpha' AND document_id='notes'") == 1)
            delete_document(app, 'alpha', 'notes')
            check('lifecycle', 'deleted document never enters search', [r['content'] for r in search(app, 'alpha', q)] == ['orthogonal'])
            check('lifecycle', 'late worker cannot resurrect tombstone', publish(app, 'alpha', 'notes', 2, [('resurrected', q)]) is False)
            check('lifecycle', 'deletion removes only the target tenant vectors', scalar(admin, "SELECT count(*) FROM chunks WHERE tenant_id='alpha' AND document_id='notes'") == 0 and scalar(admin, "SELECT count(*) FROM chunks WHERE tenant_id='beta'") == 1)
            observations['lifecycle'] = {'deleted_document': admin.execute("SELECT revision,deleted FROM documents WHERE tenant_id='alpha' AND document_id='notes'").fetchone(),
                'remaining_alpha_vectors': scalar(admin, "SELECT count(*) FROM chunks WHERE tenant_id='alpha'"),
                'remaining_beta_vectors': scalar(admin, "SELECT count(*) FROM chunks WHERE tenant_id='beta'"),
                'failed_publication_rolled_back': True, 'late_worker_accepted': False}
            run_ann(admin)
    check('cleanup', 'owned PostgreSQL listener stopped', cleanup['listener_stopped'])
    check('cleanup', 'temporary cluster removed', cleanup['temporary_cluster_removed'])
    check('cleanup', 'existing service untouched', cleanup['existing_service_touched'] is False)
    report = {'module': 24, 'verified_date': '2026-10-15', 'python': platform.python_version(), 'os': platform.platform(),
              'postgresql': cleanup['server_version'], 'pgvector': cleanup['pgvector'],
              'dependencies': {name: importlib.metadata.version(name) for name in ('psycopg', 'psycopg-binary')},
              'counts': dict(Counter(item['group'] for item in checks)), 'total': len(checks), 'checks': checks,
              'observations': observations, 'cleanup': {**cleanup, 'loopback_ports_closed': [cleanup['port']]},
              'scope': 'Real native PostgreSQL/pgvector; authored 3D/8D vectors. Pinecone JSON bodies only. No learned embeddings, inference, hosted API, Docker or production benchmark.'}
    (BASE / 'verification-results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (BASE / 'cleanup-results.json').write_text(json.dumps(report['cleanup'], indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'total': report['total'], 'counts': report['counts'], 'ann': observations['ann'], 'cleanup': {
        key: cleanup[key] for key in ('listener_stopped', 'temporary_cluster_removed', 'existing_service_touched')}}, indent=2))


if __name__ == '__main__':
    main()
