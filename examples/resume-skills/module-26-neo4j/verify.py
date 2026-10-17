"""Real Neo4j/Bolt checks; synthetic graph, no hosted database or learned model."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import importlib.metadata
import json
import logging
import platform
from neo4j.exceptions import Neo4jError
from fixtures import CONCEPTS, seed
from runtime import temporary_graph
from service import Principal, evidence, prerequisites, upsert_concept

logging.getLogger('neo4j.notifications').setLevel(logging.ERROR)
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


def run(driver, cypher, **params):
    with driver.session(database='neo4j') as session:
        result = session.run('CYPHER 5 ' + cypher, **params)
        rows = result.data()
        return rows, result.consume()


def scalar(driver, query, **params):
    return next(iter(run(driver, query, **params)[0][0].values()))


def operators(plan):
    return [plan['operatorType']] + [name for child in plan.get('children', []) for name in operators(child)]


def main():
    with temporary_graph() as (driver, cleanup):
        versions = run(driver, 'CALL dbms.components() YIELD name,versions,edition RETURN name,versions,edition')[0]
        kernel = next(item for item in versions if item['name'] == 'Neo4j Kernel')
        check('engine', 'actual Community engine is the pinned version', kernel['versions'] == ['2026.09.0'] and kernel['edition'] == 'community')
        check('engine', 'server advertises Cypher 5 for executed queries', any(item['name'] == 'Cypher' and '5' in item['versions'] for item in versions))
        schema = [s.strip() for s in (BASE / 'schema.cypher').read_text(encoding='utf-8').split(';') if s.strip()]
        for query in schema:
            run(driver, query)
        with driver.session(database='neo4j') as session:
            session.execute_write(seed)
        check('model', 'fixture has eight tenant-scoped concepts', scalar(driver, 'MATCH (c:Concept) RETURN count(c)') == 8)
        check('model', 'fixture has two documents', scalar(driver, 'MATCH (d:Document) RETURN count(d)') == 2)
        check('model', 'typed directed prerequisite edges are stored', scalar(driver, 'MATCH ()-[r:REQUIRES]->() RETURN count(r)') == 9)
        check('model', 'composite identity permits same ID in different tenants', scalar(driver, "MATCH (c:Concept {id:'backend'}) RETURN count(c)") == 2)
        check('model', 'labels and properties are returned as declared', run(driver, "MATCH (c:Concept {tenant:'alpha',id:'http'}) RETURN labels(c) AS labels,c.title AS title")[0] == [{'labels': ['Concept'], 'title': 'HTTP'}])
        direction = run(driver, "MATCH (:Concept {tenant:'alpha',id:'backend'})-[:REQUIRES]->(c) RETURN c.id AS id ORDER BY id")[0]
        check('cypher', 'outgoing pattern follows declared direction', [r['id'] for r in direction] == ['database', 'http', 'network'])
        incoming = run(driver, "MATCH (c)-[:REQUIRES]->(:Concept {tenant:'alpha',id:'backend'}) RETURN c.id AS id")[0]
        check('cypher', 'incoming pattern returns the reverse perspective', incoming == [{'id': 'framework'}])
        optional = run(driver, "MATCH (c:Concept {tenant:'alpha',id:'network'}) OPTIONAL MATCH (c)-[:REQUIRES]->(n) RETURN c.id AS id,n.id AS neighbor")[0]
        check('cypher', 'OPTIONAL MATCH keeps unmatched node with null neighbor', optional == [{'id': 'network', 'neighbor': None}])
        count_null = run(driver, "MATCH (c:Concept {tenant:'alpha',id:'network'}) OPTIONAL MATCH (c)-[:REQUIRES]->(n) RETURN count(*) AS rows,count(n) AS neighbors")[0]
        check('cypher', 'count star and count nullable expression differ', count_null == [{'rows': 1, 'neighbors': 0}])
        check('cypher', 'missing property yields null', scalar(driver, "MATCH (c:Concept {tenant:'alpha',id:'http'}) RETURN c.nonexistent") is None)
        check('cypher', 'IS NULL handles missing property', scalar(driver, "MATCH (c:Concept {tenant:'alpha',id:'http'}) RETURN c.nonexistent IS NULL") is True)
        check('cypher', 'equality with null is not true', scalar(driver, 'RETURN null = null') is None)
        aggregation = run(driver, "MATCH (c:Concept) WITH c.tenant AS tenant,count(*) AS concepts WHERE concepts>=2 RETURN tenant,concepts ORDER BY tenant")[0]
        check('cypher', 'WITH aggregates and filters intermediate rows', aggregation == [{'tenant': 'alpha', 'concepts': 6}, {'tenant': 'beta', 'concepts': 2}])
        rows = run(driver, 'UNWIND $values AS value RETURN value ORDER BY value', values=[3, 1, 2])[0]
        check('cypher', 'UNWIND expands a parameterized list', rows == [{'value': 1}, {'value': 2}, {'value': 3}])
        injected = "backend'}) MATCH (n) DETACH DELETE n //"
        check('cypher', 'parameterized malicious text remains a literal value', run(driver, 'MATCH (c:Concept {tenant:$tenant,id:$id}) RETURN c.id', tenant='alpha', id=injected)[0] == [])
        check('cypher', 'parameterized injection attempt leaves graph unchanged', scalar(driver, 'MATCH (c:Concept) RETURN count(c)') == 8)
        observations['cypher'] = {'outgoing_backend': direction, 'incoming_backend': incoming, 'optional_network': optional,
            'optional_counts': count_null, 'concepts_by_tenant': aggregation, 'injection_matched_rows': 0}

        rejects('constraints', 'duplicate composite identity rejected by engine', lambda: run(driver, "CREATE (:Concept {tenant:'alpha',id:'http',title:'duplicate'})"), Neo4jError)
        constraints = run(driver, 'SHOW CONSTRAINTS YIELD name,type RETURN name,type ORDER BY name')[0]
        check('constraints', 'both identity constraints exist', {r['name'] for r in constraints} == {'concept_identity', 'document_identity'})
        alpha_writer = Principal('alpha', can_write=True)
        first = upsert_concept(driver, alpha_writer, 'new-topic', 'First title')
        second = upsert_concept(driver, alpha_writer, 'new-topic', 'Updated title')
        check('merge', 'identity-only MERGE updates mutable title', first['title'] == 'First title' and second['title'] == 'Updated title')
        check('merge', 'repeat upsert does not duplicate node', scalar(driver, "MATCH (c:Concept {tenant:'alpha',id:'new-topic'}) RETURN count(c)") == 1)
        check('merge', 'ON CREATE property is retained on later match', scalar(driver, "MATCH (c:Concept {tenant:'alpha',id:'new-topic'}) RETURN c.created_by") == 'fixture')
        rejects('merge', 'MERGE with mutable title in identity pattern conflicts with uniqueness', lambda: run(driver, "MERGE (:Concept {tenant:'alpha',id:'new-topic',title:'Another title'})"), Neo4jError)
        for _ in range(2):
            run(driver, "CREATE (:Unconstrained {id:'same'})")
        check('merge', 'CREATE repeats patterns without a constraint', scalar(driver, "MATCH (n:Unconstrained {id:'same'}) RETURN count(n)") == 2)
        for _ in range(2):
            run(driver, "MATCH (a:Concept {tenant:'alpha',id:'new-topic'}), (b:Concept {tenant:'alpha',id:'http'}) MERGE (a)-[:EXAMPLE {tenant:'alpha'}]->(b)")
        check('merge', 'bound-endpoint relationship MERGE is idempotent sequentially', scalar(driver, 'MATCH ()-[r:EXAMPLE]->() RETURN count(r)') == 1)
        run(driver, "CREATE (:Concept {tenant:'alpha',tag:'missing-id'}),(:Concept {tenant:'alpha',tag:'missing-id'})")
        check('constraints', 'uniqueness does not require missing property existence', scalar(driver, "MATCH (c:Concept {tag:'missing-id'}) RETURN count(c)") == 2)
        run(driver, "MATCH (c:Concept {tag:'missing-id'}) DELETE c")
        observations['merge'] = {'first_upsert': first, 'second_upsert': second, 'upsert_node_count': 1,
            'unconstrained_create_count': 2, 'sequential_relationship_merge_count': 1, 'constraints': constraints,
            'missing_id_nodes_accepted_then_removed': 2}

        alpha = Principal('alpha')
        one = prerequisites(driver, alpha, 'backend', depth=1)
        three = prerequisites(driver, alpha, 'backend', depth=3)
        check('traversal', 'one-hop traversal returns direct prerequisites', [r['id'] for r in one] == ['database', 'http', 'network'])
        check('traversal', 'bounded multihop traversal reaches transactions', [r['id'] for r in three] == ['database', 'http', 'network', 'transactions'])
        check('traversal', 'minimum hop aggregation deduplicates shared neighbor', len([r for r in three if r['id'] == 'network']) == 1 and next(r['hops'] for r in three if r['id'] == 'network') == 1)
        cycle = prerequisites(driver, alpha, 'database', depth=3)
        check('traversal', 'bounded cyclic graph excludes the root', [r['id'] for r in cycle] == ['transactions'])
        raw_paths = run(driver, "MATCH p=(:Concept {tenant:'alpha',id:'backend'})-[:REQUIRES*1..2]->(:Concept {tenant:'alpha',id:'network'}) RETURN length(p) AS hops ORDER BY hops")[0]
        check('traversal', 'multiple paths to one node remain separate before aggregation', raw_paths == [{'hops': 1}, {'hops': 2}])
        check('traversal', 'missing root returns an empty result', prerequisites(driver, alpha, 'missing') == [])
        check('traversal', 'application result cap is applied', len(prerequisites(driver, alpha, 'backend', depth=3, limit=2)) == 2)
        check('authorization', 'alpha root query contains no beta concept', all('Private' not in r['title'] for r in three))
        unsafe = run(driver, "MATCH p=(a:Concept {tenant:'alpha',id:'http'})-[:REQUIRES*1..2]->(b:Concept {tenant:'alpha'}) RETURN b.id AS id ORDER BY id")[0]
        check('authorization', 'endpoint-only scope demonstrates cross-tenant intermediate path', 'transactions' in [r['id'] for r in unsafe])
        safe = prerequisites(driver, alpha, 'http', depth=2)
        check('authorization', 'every-node path scope rejects beta intermediate', safe == [{'id': 'network', 'title': 'Networking', 'hops': 1}])
        run(driver, "MATCH (a:Concept {tenant:'alpha',id:'http'}),(b:Concept {tenant:'alpha',id:'database'}) CREATE (a)-[:REQUIRES {tenant:'beta',tag:'wrong-scope'}]->(b)")
        check('authorization', 'every-relationship scope rejects invalid edge tenant', prerequisites(driver, alpha, 'http', depth=1) == [{'id': 'network', 'title': 'Networking', 'hops': 1}])
        run(driver, "MATCH ()-[r:REQUIRES {tag:'wrong-scope'}]->() DELETE r")
        check('authorization', 'beta same root ID cannot traverse alpha graph', prerequisites(driver, Principal('beta'), 'backend') == [])
        rejects('authorization', 'missing read permission denied', lambda: prerequisites(driver, Principal('alpha', can_read=False), 'backend'), PermissionError)
        rejects('authorization', 'unknown trusted tenant denied', lambda: prerequisites(driver, Principal('outsider'), 'backend'), PermissionError)
        rejects('authorization', 'read-only application principal cannot write', lambda: upsert_concept(driver, alpha, 'forbidden', 'No'), PermissionError)
        rejects('bounds', 'unbounded requested depth rejected', lambda: prerequisites(driver, alpha, 'backend', depth=99))
        rejects('bounds', 'negative requested depth rejected', lambda: prerequisites(driver, alpha, 'backend', depth=-1))
        rejects('bounds', 'boolean depth rejected', lambda: prerequisites(driver, alpha, 'backend', depth=True))
        rejects('bounds', 'float depth rejected before query construction', lambda: prerequisites(driver, alpha, 'backend', depth=2.0))
        rejects('bounds', 'string depth rejected before query construction', lambda: prerequisites(driver, alpha, 'backend', depth='2'))
        rejects('bounds', 'oversized result request rejected', lambda: prerequisites(driver, alpha, 'backend', limit=21))
        rejects('bounds', 'identifier injection rejected by service boundary', lambda: prerequisites(driver, alpha, injected))
        observations['traversal'] = {'depth_1': one, 'depth_3': three, 'database_cycle_results': cycle,
            'raw_paths_to_network': raw_paths, 'endpoint_only_http_results': unsafe, 'fully_scoped_http_results': safe,
            'depth_cap': 3, 'result_cap': 20, 'query_timeout_seconds': 2}

        before = scalar(driver, 'MATCH (n) RETURN count(n)')
        with driver.session(database='neo4j') as session:
            tx = session.begin_transaction()
            tx.run("CYPHER 5 CREATE (:RollbackDemo {id:'explicit'})").consume()
            tx.rollback()
        check('transactions', 'explicit rollback removes uncommitted node', scalar(driver, 'MATCH (n) RETURN count(n)') == before)
        def fail_after_write(tx):
            tx.run("CYPHER 5 CREATE (:RollbackDemo {id:'managed'})").consume()
            raise ValueError('Injected application failure')
        def managed_failure():
            with driver.session(database='neo4j') as session:
                session.execute_write(fail_after_write)
        rejects('transactions', 'managed callback failure propagated', managed_failure)
        check('transactions', 'managed transaction rolled back prior write', scalar(driver, 'MATCH (:RollbackDemo) RETURN count(*)') == 0)
        def conflicting_write(tx):
            tx.run("CYPHER 5 CREATE (:RollbackDemo {id:'constraint'})").consume()
            tx.run("CYPHER 5 CREATE (:Concept {tenant:'alpha',id:'http'})").consume()
        def conflict():
            with driver.session(database='neo4j') as session:
                session.execute_write(conflicting_write)
        rejects('transactions', 'constraint failure aborts whole transaction', conflict, Neo4jError)
        check('transactions', 'earlier write absent after constraint failure', scalar(driver, 'MATCH (:RollbackDemo) RETURN count(*)') == 0)
        with ThreadPoolExecutor(max_workers=4) as pool:
            created = list(pool.map(lambda _: upsert_concept(driver, alpha_writer, 'concurrent', 'Concurrent'), range(8)))
        check('concurrency', 'all concurrent managed upserts complete', len(created) == 8)
        check('concurrency', 'uniqueness holds across concurrent upserts', scalar(driver, "MATCH (c:Concept {tenant:'alpha',id:'concurrent'}) RETURN count(c)") == 1)
        run(driver, "CREATE (:Counter {id:'local',value:0})")
        def increment(_):
            def write(tx):
                return tx.run("CYPHER 5 MATCH (c:Counter {id:'local'}) SET c.value=c.value+1 RETURN c.value AS value").single()['value']
            with driver.session(database='neo4j') as session:
                return session.execute_write(write)
        with ThreadPoolExecutor(max_workers=4) as pool:
            increments = list(pool.map(increment, range(20)))
        check('concurrency', 'all concurrent property increments finish', len(increments) == 20)
        check('concurrency', 'direct dependent-property update preserves all increments', scalar(driver, "MATCH (c:Counter {id:'local'}) RETURN c.value") == 20)
        observations['transactions'] = {'explicit_rollback_visible_rows': 0, 'callback_rollback_visible_rows': 0,
            'constraint_rollback_visible_rows': 0, 'concurrent_upsert_calls': 8, 'concurrent_identity_nodes': 1,
            'increment_calls': 20, 'final_counter': 20, 'workers': 4, 'retry_occurrence_measured': False}

        run(driver, 'CALL db.awaitIndexes(30)')
        explain = run(driver, 'EXPLAIN MATCH (c:Concept {tenant:$tenant,id:$id}) RETURN c.title', tenant='alpha', id='http')[1]
        plan = operators(explain.plan)
        check('plans', 'identity lookup uses unique index seek', any('NodeUniqueIndexSeek' in op for op in plan))
        profiled_rows, profile = run(driver, 'PROFILE MATCH (c:Concept {tenant:$tenant,id:$id}) RETURN c.title AS title', tenant='alpha', id='http')
        check('plans', 'PROFILE executes the identity lookup', profiled_rows == [{'title': 'HTTP'}] and profile.profile is not None)
        before_explain = scalar(driver, 'MATCH (:ExplainOnly) RETURN count(*)')
        run(driver, "EXPLAIN CREATE (:ExplainOnly {id:'not-created'})")
        check('plans', 'EXPLAIN does not execute the write', scalar(driver, 'MATCH (:ExplainOnly) RETURN count(*)') == before_explain == 0)
        _, created_summary = run(driver, "CREATE (:DeleteDemo {id:'parent'})-[:LINK]->(:DeleteDemo {id:'child'})")
        check('delete', 'query counters record actual node and relationship creation', created_summary.counters.nodes_created == 2 and created_summary.counters.relationships_created == 1)
        rejects('delete', 'DELETE of attached node rejected', lambda: run(driver, "MATCH (n:DeleteDemo {id:'parent'}) DELETE n"), Neo4jError)
        _, detached = run(driver, "MATCH (n:DeleteDemo {id:'parent'}) DETACH DELETE n")
        check('delete', 'DETACH DELETE removes node and attached relationship', detached.counters.nodes_deleted == 1 and detached.counters.relationships_deleted == 1)
        check('delete', 'detaching parent leaves neighbor node intact', scalar(driver, 'MATCH (:DeleteDemo) RETURN count(*)') == 1)
        run(driver, 'MATCH (n:DeleteDemo) DELETE n')
        observations['plans'] = {'identity_explain_operators': plan, 'identity_profile_operators': operators(profile.profile),
            'profile_returned_rows': profiled_rows, 'explain_created_nodes': 0,
            'detach_deleted_nodes': detached.counters.nodes_deleted, 'detach_deleted_relationships': detached.counters.relationships_deleted,
            'timing_benchmark_claim': False}

        current = evidence(driver, alpha, 'transactions')
        check('retrieval', 'graph evidence resolves current alpha source', current == [{'document': 'notes', 'revision': 1, 'text': 'Transactions group changes atomically.'}])
        check('retrieval', 'same document ID remains isolated for beta', evidence(driver, Principal('beta'), 'secret') == [{'document': 'notes', 'revision': 1, 'text': 'Private beta instructions.'}])
        check('retrieval', 'alpha cannot resolve beta secret concept', evidence(driver, alpha, 'secret') == [])
        run(driver, "MATCH (d:Document {tenant:'alpha',id:'notes'}) SET d.revision=2,d.text='Updated transaction explanation.'")
        check('retrieval', 'stale EXPLAINS revision excluded after source edit', evidence(driver, alpha, 'transactions') == [])
        run(driver, "MATCH (:Document {tenant:'alpha',id:'notes'})-[r:EXPLAINS]->() SET r.source_revision=2")
        updated = evidence(driver, alpha, 'transactions')
        check('retrieval', 'current relationship generation resolves updated source', updated[0]['revision'] == 2 and updated[0]['text'] == 'Updated transaction explanation.')
        run(driver, "MATCH (d:Document {tenant:'alpha',id:'notes'}) SET d.deleted=true")
        check('retrieval', 'source tombstone immediately excludes local graph evidence', evidence(driver, alpha, 'transactions') == [])
        check('retrieval', 'alpha deletion leaves beta evidence available', len(evidence(driver, Principal('beta'), 'secret')) == 1)
        observations['retrieval'] = {'initial_alpha_evidence': current, 'updated_alpha_evidence': updated,
            'stale_revision_results': [], 'deleted_alpha_results': [], 'beta_evidence_remaining': 1,
            'extraction_scope': 'Hand-authored concept links and source text; no entity-extraction model or answer generation'}
    check('cleanup', 'owned Java process exits cleanly', cleanup['process_exit_code'] == 0)
    check('cleanup', 'owned Bolt port closes', cleanup['listener_stopped'])
    check('cleanup', 'temporary Neo4j database removed', cleanup['temporary_directory_removed'])
    check('cleanup', 'installed services untouched', cleanup['system_services_touched'] is False)
    report = {'module': 26, 'verified_date': '2026-10-16', 'python': platform.python_version(), 'os': platform.platform(),
              'neo4j': kernel['versions'][0], 'edition': kernel['edition'], 'cypher': '5', 'java': cleanup['java'],
              'dependencies': {'neo4j': importlib.metadata.version('neo4j')}, 'counts': dict(Counter(c['group'] for c in checks)),
              'total': len(checks), 'checks': checks, 'observations': observations, 'cleanup': cleanup,
              'scope': 'Actual embedded Neo4j Community engine over loopback Bolt, official Python driver and synthetic graph. Application tenant checks only; DB auth/TLS disabled locally. No Aura/Enterprise RBAC/APOC/GDS/learned extraction/model inference/production performance test.'}
    (BASE / 'verification-results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (BASE / 'cleanup-results.json').write_text(json.dumps(cleanup, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'total': report['total'], 'counts': report['counts'], 'observations': observations,
                      'cleanup': {k: cleanup[k] for k in ('port', 'process_exit_code', 'listener_stopped', 'temporary_directory_removed')}}, indent=2))


if __name__ == '__main__':
    main()
