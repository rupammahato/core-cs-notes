# Resume Skills Placement Handbook — Part 28
# Module 26: Neo4j and Graph-Backed Applications

**Estimated time: 4–5 hours | Tier: 2 | Requires: DBMS indexes/transactions, DSA graphs; M8 tenant boundaries and M23–M24 retrieval help**

---

## Why this module exists

“I used Neo4j” should lead to an explanation of the entities, relationships and queries that made a graph model useful. Be ready to explain a Cypher pattern, distinguish a path from a returned row, defend an index, handle duplicate identities and show how another tenant's nodes stay outside a traversal.

This chapter builds a small prerequisite/evidence graph for the placement-note assistant. It uses actual Neo4j execution and an official driver, then develops architecture and interview follow-ups from those results. The questions are selected useful fundamentals, not a measured company-frequency ranking.

**Organizing principle: model the relationship meaning, anchor the traversal, and accept only current permitted evidence.**

---

## 1. What Neo4j is and why a backend might use it

Neo4j is a graph database that stores entities and relationships and provides Cypher for querying them. In its property-graph model, nodes represent entities, labels classify nodes, relationships connect nodes with a type/direction, and properties hold values on nodes or relationships.

For a placement assistant, concepts such as HTTP and transactions can be nodes. `REQUIRES` can connect a topic to a prerequisite. A document can connect to a concept through `EXPLAINS`, with the source revision recorded so outdated associations are rejected.

```text
(Frameworks)-[:REQUIRES]->(Backend)-[:REQUIRES]->(Databases)
                              |                      |
                          REQUIRES                REQUIRES
                              v                      v
                            (HTTP)              (Transactions)
                              |                      ^
                          REQUIRES                   |
                              v                   EXPLAINS
                         (Networking)             (Notes r1)
```

A graph representation is useful when questions repeatedly follow relationships: prerequisites of prerequisites, common collaborators, dependency impact, or paths connecting entities. It is not automatically better for a simple key lookup, payroll aggregation or document blob. Begin with the actual query workload.

Cypher is declarative: describe the pattern/results wanted, while the engine plans its execution. That differs from writing an explicit BFS loop over an in-memory adjacency list, although both rely on graph concepts. [Cypher overview](https://neo4j.com/docs/cypher-manual/current/introduction/cypher-overview/)

---

## 2. What was actually verified

Recorded **16 October 2026** on Windows:

| Component | Recorded version/context |
| --- | --- |
| Python | 3.12.10 |
| Neo4j | 2026.09.0, community |
| Query language | Explicit `CYPHER 5` |
| Python driver | 6.4.1 |
| Java | openjdk version "21.0.12.1" 2026-08-18 LTS |
| JVM heap / page cache | 256 MiB maximum heap / 64 MiB page cache |

**76 actual local checks passed.** They use the real Community engine over loopback Bolt: property/label patterns, nulls and optional matches, constraints, `CREATE`/`MERGE`, bounded paths, tenant guards, rollback, concurrent writes, query plans, deletion and source-generation acceptance.

The graph is synthetic. Its concept links and document text are **hand-authored fixtures**. No learned entity extractor, language model, remote vector store, Aura account, Enterprise authorization, APOC procedure library or Graph Data Science algorithm was executed. The small concurrent tests are correctness scenarios, not throughput/latency benchmarks.

### Reproduce

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-26-neo4j/.venv
& examples/resume-skills/module-26-neo4j/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-26-neo4j/requirements-lock.txt
& examples/resume-skills/module-26-neo4j/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-26-neo4j/prepare_runtime.py
& examples/resume-skills/module-26-neo4j/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-26-neo4j/verify.py
```

The runtime helper downloads pinned Neo4j Community and Azul Zulu Java ZIPs from their vendors, checks recorded SHA-256 hashes and extracts them only into the example's ignored `.runtime/` directory. Licenses remain in the archives/extracted distributions. It performs no system installer, Java-path change or Windows-service registration. [Neo4j Java requirements](https://neo4j.com/docs/operations-manual/current/installation/requirements/)

The Java helper uses the documented embedded engine with a Bolt connector. Python therefore executes actual driver/database operations while the verifier owns one native Java process and a temporary data directory. Shutdown is signaled over stdin; the helper calls `dbms.shutdown()`, and the verifier waits for exit, probes the port and removes the owned data. [Embedded Bolt connector](https://neo4j.com/docs/java-reference/current/java-embedded/bolt/)

Authentication and TLS are disabled **only for this isolated loopback fixture**. Application principal checks are tested; database-enforced tenant/RBAC isolation is not. The driver credential must not be exposed to untrusted clients in a deployed service. No existing database service is touched. Docker and port 3000 remain stopped.

The runtime reports both Cypher 5 and 25 support. Every executed fixture query selects Cypher 5 explicitly, including the `[:REQUIRES*1..3]` variable-length syntax. Newer-language features are outside this execution contract.

| Check group | Passing checks |
| --- | --- |
| engine | 2 |
| model | 5 |
| cypher | 11 |
| constraints | 3 |
| merge | 6 |
| traversal | 7 |
| authorization | 8 |
| bounds | 7 |
| transactions | 5 |
| concurrency | 4 |
| plans | 3 |
| delete | 4 |
| retrieval | 7 |
| cleanup | 4 |

---

## 3. Nodes, labels, relationships, properties and identity

| Element | Meaning | Fixture example |
| --- | --- | --- |
| Node | One entity | HTTP concept or notes document |
| Label | Node classification used by patterns/schema | `Concept`, `Document` |
| Relationship type | Meaning of the connection | `REQUIRES`, `EXPLAINS` |
| Relationship direction | How the connection is stored/interpreted | Topic points to prerequisite |
| Property | Stored attribute | `tenant`, `id`, `title`, `source_revision` |
| Path | Alternating sequence of nodes and relationships | Backend → HTTP → Networking |

Choose relationship direction consistently. `(Backend)-[:REQUIRES]->(HTTP)` means HTTP is a prerequisite of Backend. Reversing that interpretation in a query can produce the opposite study plan without any syntax error.

Nodes can carry multiple labels. A label is not an automatic declaration that every node has the same properties. Relationships have their own properties and identity: an `EXPLAINS` edge's revision is a claim about a particular derived association, not a substitute for the document's current revision.

Property values have defined supported types; the property graph is not an unrestricted nested JSON document store. A map parameter can provide values for `SET c=row`, as in the fixture, without implying an arbitrary map can be stored as one property. Verify type support for your installed version/edition. [Property, structural and constructed values](https://neo4j.com/docs/cypher-manual/current/values-and-types/property-structural-constructed/)

### Application identity versus internal IDs

Use stable application identifiers for URLs, ingestion manifests and upserts. Our identity is `(tenant, id)`, so alpha and beta can both have a concept named `backend` and a document named `notes` without being the same entity.

Do not build durable application identity around an internal numeric ID or assume `elementId()` is a permanent business key. The official reference recommends application-generated IDs and describes the limited guarantees of element IDs. [Neo4j elementId](https://neo4j.com/docs/cypher-manual/current/functions/scalar/#functions-elementid)

---

## 4. Graph database versus SQL, documents and vectors

| Store/model | Useful native question | Design consideration |
| --- | --- | --- |
| Relational tables | Which rows satisfy predicates/joins/aggregations? | Strong relational integrity and flexible SQL; recursive queries can represent graph traversal |
| Document store | Which related attributes belong in one document? | Embedding/read locality versus cross-document relationships |
| Property graph | Which entities/paths satisfy relationship patterns? | Relationship semantics, starting-node selectivity, traversal fan-out |
| Vector search | Which compatible representations are nearest? | Metric, approximation, relevance and metadata scope |

SQL can model many-to-many relationships with link tables and traverse them with recursive queries. A graph database's advantage is a good fit for a relationship-heavy workload and its query/modeling ergonomics, not that relational joins are inherently incapable of representing graphs.

A vector neighbor and a domain relationship also mean different things. Semantic proximity can suggest related passages without expressing “requires.” A hand-authored `REQUIRES` edge expresses that relation but may still be wrong or stale. Neither should be treated as an automatically verified fact.

Three graph meanings now appear in this handbook: Neo4j stores domain relationships, LangGraph from M25 represents execution transitions, and HNSW from M24 navigates vector proximity. Explain which graph is meant when discussing your architecture.

---

## 5. Executed schema and fixture graph

The identity constraints protect the keys used by the service. They are created before loading the graph.

### `schema.cypher`

```cypher
CREATE CONSTRAINT concept_identity IF NOT EXISTS
FOR (c:Concept) REQUIRE (c.tenant, c.id) IS UNIQUE;

CREATE CONSTRAINT document_identity IF NOT EXISTS
FOR (d:Document) REQUIRE (d.tenant, d.id) IS UNIQUE;
```

These are uniqueness constraints, not existence constraints. The engine test intentionally inserts two Concept nodes without `id`, observes that uniqueness alone allows them, and removes them. The application validates complete keys; do not claim this schema independently requires every identity property to exist. Constraint capabilities differ by type and edition. [Creating constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/)

### `fixtures.py`

```python
"""Synthetic prerequisite graph with a cycle, shared neighbor and invalid cross-tenant edges."""
CONCEPTS = [
    {'tenant': 'alpha', 'id': 'backend', 'title': 'Backend'},
    {'tenant': 'alpha', 'id': 'http', 'title': 'HTTP'},
    {'tenant': 'alpha', 'id': 'network', 'title': 'Networking'},
    {'tenant': 'alpha', 'id': 'database', 'title': 'Databases'},
    {'tenant': 'alpha', 'id': 'transactions', 'title': 'Transactions'},
    {'tenant': 'alpha', 'id': 'framework', 'title': 'Frameworks'},
    {'tenant': 'beta', 'id': 'backend', 'title': 'Private beta backend'},
    {'tenant': 'beta', 'id': 'secret', 'title': 'Private beta procedure'},
]
EDGES = [('backend', 'http'), ('backend', 'database'), ('http', 'network'),
         ('database', 'transactions'), ('transactions', 'database'), ('framework', 'backend'),
         ('backend', 'network')]


def seed(tx):
    tx.run('CYPHER 5 UNWIND $rows AS row CREATE (c:Concept) SET c=row', rows=CONCEPTS).consume()
    tx.run('''CYPHER 5 UNWIND $edges AS edge
        MATCH (a:Concept {tenant:'alpha',id:edge[0]}), (b:Concept {tenant:'alpha',id:edge[1]})
        CREATE (a)-[:REQUIRES {tenant:'alpha'}]->(b)''', edges=EDGES).consume()
    tx.run('''CYPHER 5 MATCH (a:Concept {tenant:'alpha',id:'http'}),
        (b:Concept {tenant:'beta',id:'secret'}), (c:Concept {tenant:'alpha',id:'transactions'})
        CREATE (a)-[:REQUIRES {tenant:'alpha'}]->(b)-[:REQUIRES {tenant:'alpha'}]->(c)''').consume()
    tx.run('''CYPHER 5 CREATE
        (a:Document {tenant:'alpha',id:'notes',revision:1,deleted:false,text:'Transactions group changes atomically.'}),
        (b:Document {tenant:'beta',id:'notes',revision:1,deleted:false,text:'Private beta instructions.'})
        WITH a,b
        MATCH (c:Concept {tenant:'alpha',id:'transactions'}), (d:Concept {tenant:'beta',id:'secret'})
        CREATE (a)-[:EXPLAINS {tenant:'alpha',source_revision:1}]->(c),
               (b)-[:EXPLAINS {tenant:'beta',source_revision:1}]->(d)''').consume()
```

The initial graph has eight concepts, two documents, nine `REQUIRES` edges and two `EXPLAINS` edges. Seven prerequisite edges describe alpha's graph. Two intentionally invalid edges pass through beta's private node and return to alpha.

There is also a database/transactions cycle and two paths from Backend to Networking. These cases reveal why a traversal must control depth, repeated paths, output identity and permissions; they are not presented as a well-curated prerequisite DAG.

For a real study curriculum, decide whether prerequisites must form a DAG. If they do, validate cycles when writing/importing edges. A relationship type named `REQUIRES` does not enforce acyclicity by itself.

---

## 6. Cypher basics: MATCH, WHERE, RETURN and parameters

Parentheses describe nodes, square brackets describe relationships, and arrows specify direction. A variable binds a matched element for later clauses. Labels/types narrow the pattern; property values and `WHERE` predicates constrain matches. `RETURN` projects results.

The verifier executes these query forms:

```cypher
CYPHER 5
MATCH (:Concept {tenant:'alpha',id:'backend'})-[:REQUIRES]->(c)
RETURN c.id AS id ORDER BY id;

CYPHER 5
MATCH (c)-[:REQUIRES]->(:Concept {tenant:'alpha',id:'backend'})
RETURN c.id AS id;
```

The first follows outgoing prerequisite edges; the second finds the topic that depends on Backend. Querying an undirected relationship pattern is another choice, but it changes the question and can expand results in both directions. [Cypher MATCH](https://neo4j.com/docs/cypher-manual/current/clauses/match/)

### Parameters keep values separate from query structure

The driver passes `tenant`, `id`, titles and limits as parameters. A malicious-looking identifier passed to a fixed lookup query remains data and matches no concept; it does not execute a second deletion statement. The application also restricts its public identifier syntax. [Cypher parameters](https://neo4j.com/docs/cypher-manual/current/syntax/parameters/)

Parameters do not automatically make arbitrary query structure safe. In the service, the traversal-depth syntax is built from an **integer allowlist** of 1, 2 or 3. Booleans, floats, strings and other depths are rejected before construction. Users cannot submit a relationship type or a complete Cypher string.

Use fixed query templates or supported safe dynamic constructs with explicit allowlists when structure must vary. Do not use “the model generated it” as a reason to execute unrestricted Cypher.

---

## 7. OPTIONAL MATCH, nulls, WITH and UNWIND

`OPTIONAL MATCH` preserves the current row when an optional pattern is absent, supplying null for the missing match. The predicate attached to that optional match participates in its matching semantics, so clause placement matters. [OPTIONAL MATCH](https://neo4j.com/docs/cypher-manual/current/clauses/optional-match/)

In the fixture, Networking has no outgoing prerequisite. Its optional neighbor is null. `count(*)` counts the preserved row, while `count(n)` counts non-null neighbor values and returns zero. A missing property returns null, and `null = null` is not true; use `IS NULL` when testing absence. [Working with null](https://neo4j.com/docs/cypher-manual/current/values-and-types/working-with-null/)

`WITH` carries selected variables/intermediate values to the next stage and can aggregate before another filter or match. The test groups concepts by tenant and filters the grouped count. Avoid losing a tenant/source variable needed later, or accidentally multiplying rows before aggregation. [WITH](https://neo4j.com/docs/cypher-manual/current/clauses/with/)

`UNWIND` expands a list into rows. The fixture uses it to import supplied concepts/edge pairs. A large import still needs batching and transaction-size decisions; list expansion is not a durability or memory policy.

### Actual basic-query observations

```json
{
  "outgoing_backend": [
    {
      "id": "database"
    },
    {
      "id": "http"
    },
    {
      "id": "network"
    }
  ],
  "incoming_backend": [
    {
      "id": "framework"
    }
  ],
  "optional_network": [
    {
      "id": "network",
      "neighbor": null
    }
  ],
  "optional_counts": [
    {
      "rows": 1,
      "neighbors": 0
    }
  ],
  "concepts_by_tenant": [
    {
      "tenant": "alpha",
      "concepts": 6
    },
    {
      "tenant": "beta",
      "concepts": 2
    }
  ],
  "injection_matched_rows": 0
}
```

The `ORDER BY` clauses make these outputs stable. Without an ordering contract, do not assume a query returns nodes in insertion order or a driver result is an ordered study plan.

---

## 8. CREATE versus MERGE and stable upsert identity

`CREATE` creates the described pattern. `MERGE` matches the complete specified pattern or creates it when absent, with optional `ON CREATE`/`ON MATCH` actions. Define identity carefully: including a mutable title in the merge pattern asks for a different pattern after the title changes. [MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/)

Our upsert merges only `(tenant,id)`, then sets `title`. The second call updates one node and retains its create-only marker. Attempting to merge the same constrained identity plus a different title fails rather than magically updating the old title.

Bind known endpoint nodes first, then merge the intended relationship. Merging a large pattern can create more of that pattern than expected when the complete match is absent. Split operations according to the identities/invariants you want.

### Concurrency is a separate question

Sequentially retrying a relationship merge produces one edge in this fixture. That does not prove every arbitrary relationship shape remains unique under concurrent imports. The node upsert concurrency test uses an identity uniqueness constraint. If a relationship represents a uniquely identified event/operation, model and constrain that identity where supported rather than assuming all edge patterns have the same guarantee.

### Actual upsert and constraint output

```json
{
  "first_upsert": {
    "id": "new-topic",
    "title": "First title"
  },
  "second_upsert": {
    "id": "new-topic",
    "title": "Updated title"
  },
  "upsert_node_count": 1,
  "unconstrained_create_count": 2,
  "sequential_relationship_merge_count": 1,
  "constraints": [
    {
      "name": "concept_identity",
      "type": "UNIQUENESS"
    },
    {
      "name": "document_identity",
      "type": "UNIQUENESS"
    }
  ],
  "missing_id_nodes_accepted_then_removed": 2
}
```

`CREATE` without a relevant constraint produces two `Unconstrained` nodes with the same application property. A graph database does not infer that two nodes with equal names must be the same entity.

---

## 9. Bounded traversal, multiple paths and cycles

The Cypher 5 pattern `[:REQUIRES*1..3]` requests paths of one through three relationships. The service starts at a tenant/id lookup, checks every node and relationship in each path, excludes the root, then groups candidates using the minimum observed path length.

These are **minimum hops among eligible matched paths within the depth bound**, not weighted shortest-path distances or an unlimited reachability result. A relevant node beyond the cap is intentionally absent. Path semantics can also vary with language/match mode; this fixture selects Cypher 5's ordinary pattern behavior. [Variable-length paths](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-paths/)

Networking is reachable both directly from Backend and via HTTP. A raw path query returns two rows; grouping by the candidate and taking `min(length(p))` returns one candidate with one hop. Decide whether the product wants distinct entities, all connecting paths or one chosen explanation path.

Cycles can revisit nodes, so excluding the root and bounding length are deliberate choices. Do not assume the graph is a tree just because the UI displays it hierarchically. DSA concepts—visited sets, BFS distance, branching and cycle detection—remain useful for reasoning about database queries.

---

## 10. Executed service: scope, budgets and source acceptance

### `service.py`

```python
"""Fixed parameterized queries; principal comes from a trusted backend boundary."""
from dataclasses import dataclass
import re
from neo4j import Query


@dataclass(frozen=True)
class Principal:
    tenant: str
    can_read: bool = True
    can_write: bool = False


def authorize(principal, write=False):
    if principal.tenant not in ('alpha', 'beta') or not principal.can_read or (write and not principal.can_write):
        raise PermissionError('Graph operation denied')


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9_-]{1,50}', value):
        raise ValueError('Invalid application identifier')
    return value


def prerequisites(driver, principal, concept_id, depth=2, limit=10):
    authorize(principal)
    identifier(concept_id)
    if isinstance(depth, bool) or not isinstance(depth, int) or depth not in (1, 2, 3):
        raise ValueError('Depth outside application limit')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('Result limit outside application limit')
    # Only the allowlisted integer controls query structure; all data are parameters.
    query = Query(f'''CYPHER 5
        MATCH p=(root:Concept {{tenant:$tenant,id:$id}})-[:REQUIRES*1..{depth}]->(candidate:Concept)
        WHERE candidate <> root
          AND all(n IN nodes(p) WHERE n.tenant=$tenant)
          AND all(r IN relationships(p) WHERE r.tenant=$tenant)
        RETURN candidate.id AS id, candidate.title AS title, min(length(p)) AS hops
        ORDER BY hops,id LIMIT $limit''', timeout=2)
    with driver.session(database='neo4j') as session:
        return session.run(query, tenant=principal.tenant, id=concept_id, limit=limit).data()


def evidence(driver, principal, concept_id):
    authorize(principal)
    identifier(concept_id)
    query = Query('''CYPHER 5
        MATCH (d:Document {tenant:$tenant})-[r:EXPLAINS]->(c:Concept {tenant:$tenant,id:$id})
        WHERE r.tenant=$tenant AND NOT d.deleted AND d.revision=r.source_revision
        RETURN d.id AS document, d.revision AS revision, d.text AS text
        ORDER BY document LIMIT 10''', timeout=2)
    with driver.session(database='neo4j') as session:
        return session.run(query, tenant=principal.tenant, id=concept_id).data()


def upsert_concept(driver, principal, concept_id, title):
    authorize(principal, write=True)
    identifier(concept_id)
    if not isinstance(title, str) or not 1 <= len(title) <= 100:
        raise ValueError('Bad title')
    def write(tx):
        result = tx.run('''CYPHER 5 MERGE (c:Concept {tenant:$tenant,id:$id})
            ON CREATE SET c.created_by='fixture'
            SET c.title=$title RETURN c.id AS id,c.title AS title''',
            tenant=principal.tenant, id=concept_id, title=title)
        return result.single().data()
    with driver.session(database='neo4j') as session:
        return session.execute_write(write)
```

`Principal` is a synthetic trusted application context. A real backend must construct it from authenticated membership and current policy; accepting a client-supplied tenant object would invalidate the boundary.

`prerequisites` uses fixed relationship semantics, integer-only depth selection, a result cap and a query timeout. `evidence` requires matching tenant, a non-deleted source and an edge generation equal to the current document revision. `upsert_concept` requires a write-capable principal and keeps mutable title outside its merge identity.

The driver targets a named database and closes each session. Queries return plain projected values rather than exposing database internals to clients. The write callback performs only database work, allowing the managed-transaction retry contract to be handled without repeating an external effect.

### Actual traversal observations

```json
{
  "depth_1": [
    {
      "id": "database",
      "title": "Databases",
      "hops": 1
    },
    {
      "id": "http",
      "title": "HTTP",
      "hops": 1
    },
    {
      "id": "network",
      "title": "Networking",
      "hops": 1
    }
  ],
  "depth_3": [
    {
      "id": "database",
      "title": "Databases",
      "hops": 1
    },
    {
      "id": "http",
      "title": "HTTP",
      "hops": 1
    },
    {
      "id": "network",
      "title": "Networking",
      "hops": 1
    },
    {
      "id": "transactions",
      "title": "Transactions",
      "hops": 2
    }
  ],
  "database_cycle_results": [
    {
      "id": "transactions",
      "title": "Transactions",
      "hops": 1
    }
  ],
  "raw_paths_to_network": [
    {
      "hops": 1
    },
    {
      "hops": 2
    }
  ],
  "endpoint_only_http_results": [
    {
      "id": "network"
    },
    {
      "id": "transactions"
    }
  ],
  "fully_scoped_http_results": [
    {
      "id": "network",
      "title": "Networking",
      "hops": 1
    }
  ],
  "depth_cap": 3,
  "result_cap": 20,
  "query_timeout_seconds": 2
}
```

The endpoint-only HTTP query finds Transactions through beta's private intermediate node. The fully scoped query rejects that route and returns only Networking. The tests also insert a relationship with the wrong tenant between alpha nodes and verify that the relationship predicate rejects it.

---

## 11. Tenant boundaries and query-work limits

Tenant checks belong to the entire access path: select the authenticated tenant, anchor the root, constrain intermediate nodes/edges, resolve permitted source text and reauthorize any citation endpoint. Applying a tenant condition only to the returned endpoint can expose private paths or unsupported associations through other tenants.

The fixture deliberately bypasses the normal service when seeding incorrect cross-tenant links. A production writer should prevent those edges, while readers still defend against corrupt imports, old bugs or later policy changes. Write-time validation and read-time scope solve different failure cases.

### Application scope is not database RBAC

These tests prove selected application queries reject unauthorized scope. They do not prove the database account itself cannot read beta: authentication is disabled in the isolated engine, and a direct unrestricted Cypher query can inspect everything. A deployed service needs authenticated/TLS database access, appropriate least-privilege credentials and an isolation strategy supported by its edition/deployment. [Neo4j authentication and authorization](https://neo4j.com/docs/operations-manual/current/authentication-authorization/)

Do not expose a generic public `runCypher` endpoint under a powerful backend credential. An LLM-generated query is also untrusted input. Prefer narrow operations with fixed templates, validated parameters and current authorization; any broader query-generation design needs its own enforceable safety boundary.

### LIMIT is a result bound, not a complete work bound

Returning twenty rows can still require exploring many candidate paths, grouping and sorting them. In a high-degree graph, a three-hop traversal may expand dramatically. Bound starting entities, depth, allowed types, source scope, query time, concurrent work and response size. The service's two-second timeout is configured, but the verifier does not force a timeout or measure termination latency. [Cypher LIMIT](https://neo4j.com/docs/cypher-manual/current/clauses/limit/)

For a simple branching estimate, if each step offers `b` neighbors, depth `d` can expose roughly `b + b² + ... + bᵈ` candidate walks before deduplication and semantic constraints. This explains risk qualitatively; it is not a measured Neo4j cardinality formula.

---

## 12. Transactions, managed retries and concurrent updates

Graph writes belong in transactions when they must succeed or fail together. The verifier inserts a node and rolls back explicitly, raises an application exception after a managed write, and triggers a uniqueness violation after another write. All three leave the earlier test node absent.

The Python driver's managed transaction callback may be retried for retryable failures. Keep it free of non-idempotent external effects such as charging a customer or sending a message. Consume/project database results within the callback/session scope rather than returning a lazy result whose transaction has closed. [Python managed and explicit transactions](https://neo4j.com/docs/python-manual/current/transactions/)

### Actual rollback and concurrency observations

```json
{
  "explicit_rollback_visible_rows": 0,
  "callback_rollback_visible_rows": 0,
  "constraint_rollback_visible_rows": 0,
  "concurrent_upsert_calls": 8,
  "concurrent_identity_nodes": 1,
  "increment_calls": 20,
  "final_counter": 20,
  "workers": 4,
  "retry_occurrence_measured": false
}
```

Eight concurrent upserts run through four workers and leave one constrained concept identity. Twenty direct `SET c.value=c.value+1` updates leave a counter of twenty. The property update is evaluated inside the database write, where the engine's locking semantics protect the dependent update in this tested pattern. [Concurrent data access](https://neo4j.com/docs/operations-manual/current/database-internals/concurrent-data-access/)

This does not imply a separate application read followed later by `SET value=$previous_plus_one` is safe. Another writer can change the value in between. Use an atomic server-side update, an appropriate transaction/locking pattern or a validated version predicate for the intended invariant.

The fixture does not instrument whether a retry happened, inject a deadlock or benchmark write throughput. It verifies final state for these specific operations. Production workflows also need retry budgets, contention monitoring and reconciliation where a remote effect cannot share the database transaction.

---

## 13. Indexes, EXPLAIN, PROFILE and cardinality

An index helps find a selective starting set by label/property. Once a starting node is found, the traversal follows relationship patterns. A useful graph query often needs both an efficient anchor and controlled expansion; a property index does not make unlimited traversal cheap.

The fixture's composite uniqueness constraint supplies an index-backed identity lookup. `EXPLAIN` shows `NodeUniqueIndexSeek`; `PROFILE` executes the lookup and returns HTTP. `EXPLAIN CREATE` creates no node. [Query-plan interpretation](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/)

```cypher
CYPHER 5
EXPLAIN MATCH (c:Concept {tenant:$tenant,id:$id}) RETURN c.title;

CYPHER 5
PROFILE MATCH (c:Concept {tenant:$tenant,id:$id}) RETURN c.title AS title;
```

Look for starting scans/seeks, rows produced at each stage, expansions, filters, aggregation/sort work and discrepancies between estimates and actual rows. `PROFILE` executes the statement, so profiling a write has real effects. Use an appropriate test transaction/environment when inspecting mutating queries.

### Actual plan and deletion observations

```json
{
  "identity_explain_operators": [
    "ProduceResults@neo4j",
    "Projection@neo4j",
    "NodeUniqueIndexSeek@neo4j"
  ],
  "identity_profile_operators": [
    "ProduceResults@neo4j",
    "Projection@neo4j",
    "NodeUniqueIndexSeek@neo4j"
  ],
  "profile_returned_rows": [
    {
      "title": "HTTP"
    }
  ],
  "explain_created_nodes": 0,
  "detach_deleted_nodes": 1,
  "detach_deleted_relationships": 1,
  "timing_benchmark_claim": false
}
```

Operator names belong to this recorded engine/runtime and may change. A successful unique seek does not establish a production latency bound. Measure representative graph degree, filters, concurrency, cache state and payload before reporting a performance claim.

Disconnected patterns can multiply rows. For example, matching many `a` nodes and many `b` nodes before connecting/filtering them can create a large intermediate combination. A declarative query that looks short can still do substantial work. Keep entity identity and relationship direction explicit.

---

## 14. Deletion, updates and derived-edge lifecycle

Plain `DELETE` rejects a node that still has relationships. `DETACH DELETE` removes that node and its attached relationships; it does not recursively delete neighboring nodes. The verifier creates a two-node example, observes the rejected deletion, detaches the parent and confirms the child survives. [Cypher DELETE](https://neo4j.com/docs/cypher-manual/current/clauses/delete/)

Do not use detach deletion as an authorization shortcut. Validate the target and understand the effect on attached edges, including edges created by another subsystem. A domain-level “delete document” operation may instead set a tombstone, reject stale jobs and schedule cleanup of derived relationships.

The assistant's `Document.revision` is authoritative within this local graph. `EXPLAINS.source_revision` identifies which source generation supports an association. Advancing the document revision immediately excludes old associations from the evidence query until they are rebuilt/published.

### Actual evidence lifecycle output

```json
{
  "initial_alpha_evidence": [
    {
      "document": "notes",
      "revision": 1,
      "text": "Transactions group changes atomically."
    }
  ],
  "updated_alpha_evidence": [
    {
      "document": "notes",
      "revision": 2,
      "text": "Updated transaction explanation."
    }
  ],
  "stale_revision_results": [],
  "deleted_alpha_results": [],
  "beta_evidence_remaining": 1,
  "extraction_scope": "Hand-authored concept links and source text; no entity-extraction model or answer generation"
}
```

The updated source becomes visible after the edge generation catches up. A tombstone then removes it from accepted evidence, while beta's same-named document remains available. This verifies local query acceptance; it does not remove retained copies from every cache, vector store, backup or LangGraph checkpoint.

Track graph generation, entity-resolution version and extraction provenance when associations are derived automatically. A late ingestion worker must compare the current source/generation before publishing, as in M23–M25. Merely upserting an old edge again can resurrect obsolete meaning even when the node IDs remain stable.

---

## 15. Graph-backed retrieval and GraphRAG fundamentals

Graph-backed retrieval uses entities/relationships to select evidence. For “what should I understand before backend frameworks?”, identify the intended concept, expand permitted prerequisites, and resolve supporting passages. Vector search can supply candidate passages or entity seeds; graph expansion can add relationship context.

```text
Question -> identify candidate entity/topic
                  |
          tenant-scoped bounded expansion
                  |
          current source relationships
                  |
          permitted passages + provenance
                  |
         rerank/context/answer pipeline from M23
```

Do not infer that a relationship automatically proves a statement. The edge might be extracted incorrectly, represent an opinion, omit a qualification or refer to an old source. Preserve supporting document/revision/location and resolve the passage before using it in an answer.

### Entity resolution matters

“JS,” “JavaScript” and “Java” should not be merged merely because their strings look related. Decide canonical entity IDs, aliases, type/tenant boundaries and disambiguation rules. If extraction is model-assisted, validate proposed identities and relations before canonical publication, and retain uncertainty/provenance where the product needs it.

The fixture has hand-authored links and exact concept IDs. It runs no entity linker, extraction model, graph/vector fusion or answer generator. It proves the local traversal and source-acceptance pieces only.

### Evaluate the additional step

Compare lexical/vector retrieval against graph-expanded retrieval on labeled questions. Include direct definitions, multi-hop questions, ambiguous entity names, wrong/stale edges, inaccessible intermediate nodes and unanswerable cases. Measure passage relevance, relation correctness, source support, context size and end-to-end cost/latency separately.

Graph expansion can improve coverage for relationship questions, but it can also add irrelevant neighbors and amplify an extraction error. A larger connected subgraph is not automatically better context.

---

## 16. Architectural understanding: build a graph-backed study planner

Begin with one authenticated backend and a canonical graph model for concepts, prerequisites and source associations. Keep uploaded source processing asynchronous when parsing or extraction can be slow. Expose narrow application operations instead of database query text.

### APIs and data model

| Interface | Important contract |
| --- | --- |
| `GET /concepts/:id/prerequisites` | Server-derived tenant, bounded depth/count, stable ordering |
| `GET /concepts/:id/evidence` | Current permitted source revisions and citation locations |
| `PUT /concepts/:id` | Authorized writer, immutable identity, validated mutable fields |
| `POST /prerequisite-links` | Both endpoints authorized, meaningful relation, optional cycle policy |
| `DELETE /documents/:id` | Canonical tombstone and durable derived-data cleanup intent |

For a real planner, add learner progress separately from the knowledge graph: `COMPLETED`, assessment results or confidence values have their own ownership and update rules. “Read the notes” is not the same as “mastered the concept.” Do not mark the user's learning checklist complete because these chapters have been authored.

### Write path

Authenticate the writer, validate both endpoint identities and tenant ownership, enforce any DAG policy, write the intended relation within a transaction and record provenance. An ingestion worker should stage extracted proposals, compare source revisions/generations and publish a coherent accepted association set.

If source metadata is canonical in PostgreSQL while Neo4j is a derived graph, use a durable outbox/job and deterministic generation identities. A SQL commit and a remote Neo4j write are not one transaction by default. Reconcile ambiguous outcomes and reject graph results whose canonical source has changed.

### Read path

Authenticate, choose an anchored topic, perform bounded authorized traversal, resolve current source evidence, deduplicate passages and return a stable projected response. If generation is added, use the context/citation acceptance rules from M23 and the budgets from M22/M25.

The local service verifies graph query semantics and source acceptance. It is not an HTTP API, queue, full study-plan scheduler, multi-store sync engine or deployed authorization service. Those are explicit implementation extensions.

### Failure cases worth explaining

| Failure | Desired response |
| --- | --- |
| Import repeats an entity | Stable constrained identity and idempotent writes |
| Two writers create the same concept | Uniqueness plus transaction/retry policy |
| Wrong cross-tenant edge enters storage | Writer validation and reader path/source checks |
| A cycle enters a prerequisite DAG | Reject or flag according to the domain policy |
| High-degree node expands too many paths | Depth/type/work/concurrency budgets and plan inspection |
| Source changes during relation extraction | Generation guard rejects obsolete publication |
| One store updates and another write fails | Durable retry/reconciliation with canonical acceptance checks |
| Model proposes destructive Cypher | Do not execute it through an unrestricted application credential |

---

## 17. Operations, editions and deployment boundaries

The official Python driver manages connectivity/pooling. Reuse an appropriately configured driver per process and use a separate session for each independent concurrent operation; the fixture's worker threads create their own sessions. Close sessions, consume results and close the driver on shutdown. [Python transaction/session guidance](https://neo4j.com/docs/python-manual/current/transactions/)

For deployment, choose supported Java/server versions, configure heap/page cache from the actual workload, restrict network access, enable appropriate authentication/TLS, manage secrets and test recovery. The fixture's small heap/cache values support a tiny example; they are not production sizing advice.

Community, Enterprise, Aura and optional libraries do not have interchangeable feature sets. Verify the edition/version for constraints, fine-grained privileges, clustering, backup/recovery and administrative operations before designing around them. APOC adds procedures; Graph Data Science provides algorithm tooling over graph data; neither is required for the Cypher queries executed here. [Neo4j security](https://neo4j.com/docs/operations-manual/current/authentication-authorization/), [Graph Data Science introduction](https://neo4j.com/docs/graph-data-science/current/introduction/)

Observe query shape, degree/cardinality, timeouts, transaction retries/deadlocks, pool pressure, heap/page-cache behavior, ingestion lag and stale-source rejections. Keep logs useful without publishing private graph properties or entire source passages.

Backups and retention must cover the canonical data and any derived graph/index/checkpoint state needed for recovery. Test restore with matching compatible runtime/schema rather than assuming a copied file or a successful backup command proves usability.

### Executed native host

`LocalGraphServer.java` is the exact helper used by the Python verifier:

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Path;
import org.neo4j.configuration.GraphDatabaseSettings;
import org.neo4j.configuration.connectors.BoltConnector;
import org.neo4j.configuration.helpers.SocketAddress;
import org.neo4j.dbms.api.DatabaseManagementService;
import org.neo4j.dbms.api.DatabaseManagementServiceBuilder;

/** Actual embedded Community engine with loopback Bolt and a clean stdin shutdown. */
public class LocalGraphServer {
    public static void main(String[] args) throws Exception {
        Path home = Path.of(args[0]).toAbsolutePath();
        int port = Integer.parseInt(args[1]);
        DatabaseManagementService dbms = new DatabaseManagementServiceBuilder(home)
            .setConfig(GraphDatabaseSettings.auth_enabled, false)
            .setConfig(GraphDatabaseSettings.pagecache_memory, 64L * 1024 * 1024)
            .setConfig(BoltConnector.enabled, true)
            .setConfig(BoltConnector.listen_address, new SocketAddress("127.0.0.1", port))
            .setConfig(BoltConnector.advertised_address, new SocketAddress("127.0.0.1", port))
            .setConfig(BoltConnector.encryption_level, BoltConnector.EncryptionLevel.DISABLED)
            .build();
        try {
            System.out.println("M26_READY " + home);
            System.out.flush();
            new BufferedReader(new InputStreamReader(System.in)).readLine();
        } finally {
            dbms.shutdown();
        }
    }
}
```

The helper reads one shutdown signal, then closes the engine in `finally`. `runtime.py` owns process/readiness/driver cleanup and validates the temporary path before removing it. It does not install Neo4j as a service or start Docker.

---

## 18. Common misconceptions and resume connection

| Incorrect claim | Better explanation |
| --- | --- |
| Graph databases are always faster than SQL | Compare representative relationship queries and operational costs |
| A label implies every node has every property | Identity/existence/type rules need explicit enforcement |
| MERGE updates all changed fields automatically | It matches the full pattern; choose stable identity then set mutable fields |
| Uniqueness requires the property to exist | Missing identity properties are a separate invariant |
| One endpoint tenant check secures a path | Intermediate nodes, edges and source resolution also matter |
| LIMIT makes an arbitrary traversal cheap | Expansion/grouping/sorting can still do extensive work |
| DETACH DELETE recursively removes neighbors | It deletes the target node and attached relationships |
| A graph relationship is a validated fact | Check provenance, revision and domain meaning |
| LangGraph is a graph database | It models execution transitions, a different graph role |
| A managed transaction callback runs only once | Retryable errors may cause another callback execution |

When defending Neo4j on a resume, name the modeled entities/relations and show one query that justified the choice. Explain how identities were constrained, how data entered the graph, whether links were curated or extracted, which store was canonical and how the query stayed authorized/bounded.

The fixture is a learning implementation. Do not claim its concurrency checks, graph provenance or tenant protections existed in an earlier project unless its code demonstrates them. A convincing interview answer distinguishes implemented behavior from proposed improvements.

---

## 19. Interview questions and answers

### Q1. What is Neo4j?

It is a graph database with a property-graph model and Cypher queries. Nodes represent entities, typed relationships connect them, and properties hold attributes. Explain a relationship-heavy question your application needs to answer, not only the product name. Our actual example models prerequisites and the current documents explaining a concept.

### Q2. What are nodes, labels and relationships?

A node is an entity, a label classifies it, and a relationship connects two nodes with a type and direction. Both nodes and relationships can have properties. In the fixture, Concept and Document are labels, REQUIRES describes prerequisites, and EXPLAINS associates source evidence with a concept generation.

### Q3. Why does relationship direction matter?

It encodes the intended meaning. Backend pointing to HTTP through REQUIRES means HTTP is a prerequisite of Backend. Reversing the pattern asks which concepts depend on Backend. Cypher can query either perspective; a syntactically valid query can still answer the wrong product question if the interpretation is inconsistent.

### Q4. When would you use a graph database instead of SQL?

When repeated relationship/path questions fit the graph model and its query/operational trade-offs. SQL can represent relationships and recursive traversal too. Compare representative queries, integrity requirements, team expertise and operational cost. A blanket claim that graph queries always beat joins is not justified by this tiny correctness fixture.

### Q5. How does a graph relationship differ from vector similarity?

A graph edge expresses a modeled relation such as REQUIRES or EXPLAINS. Vector similarity compares compatible numeric representations and can suggest semantic neighbors. Neither automatically establishes truth. A retrieval system can use vectors for candidates and graph expansion for relational context, then resolve current supporting passages.

### Q6. Is LangGraph a graph database?

No. It models workflow execution state and transitions. Neo4j stores domain entities/relations; HNSW represents vector-neighbor navigation. These graphs solve different problems. Explain which graph owns application control flow, which stores knowledge and which accelerates similarity search rather than treating their names as interchangeable.

### Q7. What does MATCH do?

It matches a declared graph pattern and binds variables for later clauses. Labels, relationship types/directions and predicates restrict matches; RETURN projects the output. Cypher is declarative, so inspect the execution plan for how the engine finds and expands candidates. An anchored identity lookup is different from scanning every node.

### Q8. Why use query parameters?

They keep data values separate from fixed query syntax and avoid building user text into query code. Our malicious-looking identifier matches no node and deletes nothing. Structural choices still need safe construction: the service interpolates only an integer depth selected from an allowlist and parameterizes tenant, IDs, titles and result limits.

### Q9. What is OPTIONAL MATCH?

It preserves a current row when an optional pattern is absent and supplies null for missing elements. Our Networking node has no outgoing prerequisite, so its neighbor is null. Predicate placement matters because WHERE belongs to the corresponding optional match. Do not assume it behaves like an unrelated post-filter after every clause.

### Q10. How do nulls and counts behave?

A missing property evaluates to null, and equality with null is not true. Use IS NULL for absence. In the optional-neighbor example, count(*) is one because the row survives, while count(n) is zero because no non-null neighbor exists. This distinction prevents incorrect relationship counts and missing-value logic.

### Q11. What are WITH and UNWIND used for?

WITH carries selected variables/intermediate results and can aggregate before a later filter or match. UNWIND expands list values into rows, useful for parameterized imports. Watch variable scope and intermediate row multiplication. Neither clause defines import batching, memory limits or retry/idempotency policy on its own.

### Q12. How do CREATE and MERGE differ?

CREATE creates the specified pattern; MERGE matches the complete pattern or creates it when absent. A changed mutable property in the merge pattern can request a different pattern rather than an update. Our service merges stable tenant/ID and then sets title, while a conflicting full-pattern merge fails under uniqueness.

### Q13. Does MERGE remove the need for constraints?

No. Protect the intended identity with a relevant constraint, particularly under concurrent writes. Our concurrent node upserts retain one constrained tenant/ID. Sequential relationship idempotency is a separate tested case; it does not prove arbitrary edge patterns are uniquely identified under every concurrent import design.

### Q14. Does uniqueness require a property to exist?

Not in the uniqueness constraint tested here. The engine accepts two Concept nodes missing ID, then the verifier removes them. Existence/key/type rules and edition support need separate consideration. The application validates complete identity before upsert; do not describe that as independent database enforcement of non-null identity fields.

### Q15. Why use application-generated IDs?

They give the product stable identities for URLs, source manifests and upserts. Internal element IDs have limited mapping guarantees and should not become durable business keys. Our composite tenant/ID lets different tenants use backend or notes without collision. Identity should remain stable when a display title changes.

### Q16. What is a variable-length traversal?

It matches paths over a range of relationship counts. The fixture explicitly uses Cypher 5 and REQUIRES*1..3. It returns candidates from eligible paths within that bound, not unlimited reachability. Newer language/match features have their own semantics, so state the engine/language context when explaining a path query.

### Q17. Why can one concept appear multiple times in query results?

Different matching paths can reach it. Backend reaches Networking directly and through HTTP, producing two path rows. Grouping by candidate and taking minimum path length yields one candidate with one hop. Choose whether the product wants entities, all explanations or one selected path; DISTINCT alone does not explain every ranking requirement.

### Q18. How do cycles affect graph queries?

The graph may revisit nodes through different relationships, so a hierarchy assumption can be wrong and expansion can grow. Bound traversal, define root/candidate behavior and enforce a DAG policy if prerequisites require one. Our database/transactions cycle is handled within the depth cap and the root is excluded; no schema rule automatically makes REQUIRES acyclic.

### Q19. Does LIMIT make a traversal cheap?

No. Expansion, filtering, aggregation and sorting can occur before the limited results are returned. Anchor a selective root and constrain depth/types/scope, query time, concurrency and output size. Our cap is twenty results and three hops, with a configured timeout; the suite does not establish a production latency or cancellation guarantee.

### Q20. How do you enforce multitenancy during traversal?

Derive tenant from trusted authentication, scope the root, every intermediate node/edge and evidence resolution, and reauthorize source access. Endpoint-only checks can still follow private intermediate nodes. Our invalid beta bridge demonstrates this. The fixture verifies application guards, while database auth/TLS is disabled locally and does not enforce tenant isolation itself.

### Q21. What are EXPLAIN and PROFILE?

EXPLAIN returns a plan without executing the statement. PROFILE executes it and provides runtime-plan information. Our identity query uses NodeUniqueIndexSeek, while EXPLAIN CREATE creates no node. Profiled writes still have effects, so use the right transaction/environment. An index seek alone is not a production performance measurement.

### Q22. What role do indexes play in a graph query?

They can find selective starting entities by properties/labels, after which relationship expansion follows the pattern. Our composite identity constraint supplies the indexed anchor. Indexes do not remove the cost of broad neighborhoods or high-degree traversals. Inspect cardinality, expansions and intermediate row work as well as the first seek.

### Q23. How do transactions protect graph writes?

They group changes into a commit/rollback boundary. The fixture proves explicit rollback, rollback after an application callback error and rollback after a later uniqueness violation. All leave earlier test writes absent. If an external notification/payment is involved, it does not share this graph transaction automatically; use an appropriate intent/idempotency/reconciliation design.

### Q24. What is the risk of managed transaction retries?

The driver may rerun a callback for retryable errors. Keep external effects out of it or protect them with the correct destination contract. The callback here performs database work and projects its result before the session closes. The concurrent tests verify final state but do not measure whether retries occurred.

### Q25. How do you avoid lost updates on a counter?

Evaluate the dependent update inside the database with an appropriate atomic/locking pattern, such as the tested SET c.value=c.value+1. Twenty concurrent calls leave twenty. A separate read followed by setting a previously computed value is a different pattern and can lose another writer's update. Version predicates are another option for suitable invariants.

### Q26. What does DETACH DELETE do?

It deletes the target node and attached relationships. It does not recursively delete neighboring nodes. The test observes plain DELETE failing for an attached parent, then detach deletion removing one node/edge while its child survives. Validate ownership and the impact on attached data before exposing this as a domain operation.

### Q27. What is graph-backed retrieval or GraphRAG?

It uses entities and relationships to select evidence, possibly combined with vector/lexical candidates and language generation. Resolve current supporting passages and preserve relation/source provenance. Our graph retrieves authored concept evidence but runs no extraction or answer model. A stored edge is not automatic proof that a generated claim is supported.

### Q28. How do you keep graph evidence fresh?

Track canonical source revision and the generation supporting each derived association. Reject stale edges and deleted sources during read acceptance, and guard publication against late workers. The fixture edits a document, excludes its old edge generation, updates the edge and later excludes the tombstoned source. Other stores/caches/checkpoints require coordinated lifecycle work.

### Q29. How would you build a graph-backed study planner?

Use stable concepts, meaningful prerequisite edges, source provenance and separate learner progress. Expose authenticated, bounded prerequisite/evidence APIs, validate edge writes and any DAG policy, and manage ingestion asynchronously. If PostgreSQL is canonical and Neo4j derived, use durable jobs/outbox reconciliation and canonical result acceptance across the service boundary.

### Q30. How would you defend Neo4j on your resume?

Describe the actual entities/relations, one query that justified a graph, identity constraints, data-ingestion/provenance, authorization and measured limits. Separate implemented behavior from hypothetical improvements. This learning fixture's tenant guards, concurrency checks and source lifecycle are not evidence that every earlier project already implemented those features.

---

## 20. Practice tasks

1. Draw a five-concept prerequisite model and define the direction of every relation. Write outgoing and incoming queries and explain their different product meanings.
2. Model the same entities/links in relational tables. Write the equivalent bounded recursive query and compare maintainability/query plans without claiming an unmeasured winner.
3. Try repeated CREATE, identity-only MERGE and MERGE with a changed mutable field. Observe which cases duplicate, update or fail under a uniqueness constraint.
4. Add explicit identity validation to an import boundary and test missing tenant/ID values. Explain which rule is enforced by the application versus the database edition/schema.
5. Add a diamond and cycle to the fixture. Compare path rows, distinct entity rows and minimum-hop results under several bounded depths.
6. Create an invalid cross-tenant intermediate node and an invalid relationship tenant. Demonstrate why endpoint-only checks fail, then verify the whole path/source policy.
7. Exercise concurrent versioned edits to one concept. Show which operation wins or rejects a stale version, and distinguish that invariant from the direct counter-update test.
8. Load a representative degree distribution and inspect EXPLAIN/PROFILE for an anchored query and a broad pattern. Record cardinality and work before reporting latency or capacity.
9. Design source-revision publication and deletion across PostgreSQL, Neo4j and a vector index. Include late workers, outbox retries, tombstones and canonical read acceptance.
10. Build a labeled retrieval set with ambiguous entities, multi-hop questions, stale/wrong edges and tenant distractors. Compare lexical/vector candidates with graph expansion, including answer-source support.

---

## 21. Revision checklist

- [ ] I can explain nodes, labels, typed relationships, direction and properties.
- [ ] I can distinguish a domain graph, workflow graph and vector-index graph.
- [ ] I can justify graph versus relational/document/vector modeling for a concrete query.
- [ ] I can read a MATCH/WHERE/RETURN pattern and reverse its direction deliberately.
- [ ] I can explain OPTIONAL MATCH, nulls, WITH and UNWIND using actual outputs.
- [ ] I can separate stable identity from mutable values in MERGE.
- [ ] I can distinguish uniqueness, existence and application input validation.
- [ ] I can reason about bounded paths, duplicate candidates, cycles and fan-out.
- [ ] I can apply tenant checks to intermediate nodes, edges and source evidence.
- [ ] I can explain transaction rollback, managed retries and atomic dependent updates.
- [ ] I can inspect an index seek and distinguish EXPLAIN from executing PROFILE.
- [ ] I can design graph-source provenance, freshness, deletion and a bounded API boundary.

---

## 22. Primary sources and verification artifacts

Version-sensitive sources were checked on **16 October 2026**. The actual engine is Neo4j Community 2026.09.0 with explicitly selected Cypher 5, not a claim about every current Cypher 25/Enterprise feature.

| Topic | Primary reference |
| --- | --- |
| Runtime and native embedding | [Java requirements](https://neo4j.com/docs/operations-manual/current/installation/requirements/), [embedded engine](https://neo4j.com/docs/java-reference/current/java-embedded/), [Bolt connector](https://neo4j.com/docs/java-reference/current/java-embedded/bolt/) |
| Query fundamentals | [Cypher overview](https://neo4j.com/docs/cypher-manual/current/introduction/cypher-overview/), [MATCH](https://neo4j.com/docs/cypher-manual/current/clauses/match/), [parameters](https://neo4j.com/docs/cypher-manual/current/syntax/parameters/) |
| Intermediate results | [OPTIONAL MATCH](https://neo4j.com/docs/cypher-manual/current/clauses/optional-match/), [WITH](https://neo4j.com/docs/cypher-manual/current/clauses/with/), [nulls](https://neo4j.com/docs/cypher-manual/current/values-and-types/working-with-null/) |
| Model and identity | [Value types](https://neo4j.com/docs/cypher-manual/current/values-and-types/property-structural-constructed/), [element IDs](https://neo4j.com/docs/cypher-manual/current/functions/scalar/#functions-elementid) |
| Writes/schema | [MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/), [constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/), [DELETE](https://neo4j.com/docs/cypher-manual/current/clauses/delete/) |
| Traversal/plans | [Variable-length paths](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-paths/), [query plans](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/execution-plans/), [LIMIT](https://neo4j.com/docs/cypher-manual/current/clauses/limit/) |
| Driver/concurrency | [Python transactions](https://neo4j.com/docs/python-manual/current/transactions/), [concurrent data access](https://neo4j.com/docs/operations-manual/current/database-internals/concurrent-data-access/) |
| Security/optional tooling | [Authentication/authorization](https://neo4j.com/docs/operations-manual/current/authentication-authorization/), [Graph Data Science](https://neo4j.com/docs/graph-data-science/current/introduction/) |

Artifacts are under `examples/resume-skills/module-26-neo4j/`: four exact sources embedded above, `verify.py`, owned runtime/process helpers, vendor package/checksum provenance, dependency lock/check, `verification-results.json`, `cleanup-results.json` and content/site validation evidence. The verification report names every passing assertion and preserves observed query results/plans and cleanup status.

**Next: [M27: System-design bridge through your load balancer](/docs/resume-skills/system-design-load-balancer).** That chapter connects requirements, routing, consistent hashing, health checks and failure handling to the wider architecture companion.
