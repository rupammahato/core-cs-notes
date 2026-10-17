# Architecture and System Design Placement Handbook — Part 4
# A2: Data, Caching and Scaling

**Estimated time: 4–5 hours | Architecture numeric module: 2 | Requires: A0, basic DBMS; Resume M13–M15 refreshers**

---

## Why this module exists

“Use Redis,” “add read replicas” and “shard the database” name tools, but they do not explain which operation becomes better or whether the result remains correct. A design answer needs the query shape, the source of truth, the stale behavior users may see, and the bottleneck that justifies another component.

This chapter extends the private-note example with an owner-scoped recent-notes listing and read caching. It uses real SQLite query plans, measured SQLite VM instruction counts and deterministic asynchronous cache interleavings. Replication, sharding, Redis deployment and capacity planning are explained separately from the local mechanisms actually run.

**Organizing principle: define the operation and its freshness rule, measure the current work, then change the data path.**

The repository probe is Python with SQLite and the cache is process-local Python memory. It is a separate learning fixture, not a replacement for [A1's TypeScript/Express backend](/docs/system-design/application-architecture-service-boundaries). A1 still serves its original create/read/replace contract; A2 does not add a public list endpoint or authentication to it. Supplied tenant/owner values are trusted test context, not verified credentials.

The 30 Q&As are editorial placement practice, not a measured company-frequency ranking. A2 addresses the architecture bank's Q04 and Q09–Q15 at foundation depth; A3 deepens concurrency/workflows and A4 deepens operating evidence. Refresh [M13: PostgreSQL](/docs/resume-skills/postgresql-backend), [M14: MongoDB](/docs/resume-skills/mongodb-backend) and [M15: caching/jobs](/docs/resume-skills/caching-background-jobs-data-ingestion) for technology syntax.

---

## 1. Start with access patterns and data authority

An access pattern specifies the actor, filter, ordering, returned fields, page size, freshness and expected frequency. “We store notes” is insufficient to choose an index or cache key.

| Operation | Query or state requirement | Freshness/correctness rule |
| --- | --- | --- |
| Read a private note | Tenant + owner + note ID; return content and revision | Never return another owner's note; choose authoritative or explicitly stale path |
| List recent notes | Tenant + owner, descending creation time and ID, bounded metadata page | Stable tie-breaking; continuation semantics documented |
| Replace a note | Tenant + owner + ID + expected revision | Conditional authoritative write; stale cache cannot grant permission or approve the write |
| Retry create from A1 | Scoped operation key and exact input identity | Original outcome stored atomically with creation; not implemented again in A2 |
| Search text later | Text matching/ranking plus current access policy | Projection lag/revocation behavior requires a separate contract |

The canonical store owns note content and revision. A cache holds replaceable derived copies. A replica is another copy of canonical database state with a replication policy. A search index is a derived query representation. Treating all four as “databases” hides different authority and recovery responsibilities.

Write the permission scope into every relevant access path: direct get, list, cached get, background processing and search. A filtered SQL query does not protect a separate cache lookup that uses only a note ID.

---

## 2. Choose a data model before a database brand

| Need | Useful starting model | Questions to answer |
| --- | --- | --- |
| Ownership, relationships and atomic changes | Relational tables and constraints | Which rows must commit together? Which joins/queries matter? |
| Self-contained evolving documents | Document aggregates with explicit indexes | What belongs in one document? How are cross-document rules enforced? |
| Fast exact-key retrieval | Key/value access | What is the key scope? Which scans/ranges are still required? |
| Text/semantic discovery | Search/vector projection | What is canonical, how fresh is the projection, and how are permissions enforced? |
| Large binary content | Object storage plus metadata | Which component owns upload completion, access and cleanup? |

SQL and document models both require schema decisions, indexes, validation and consistency reasoning. A flexible document shape does not eliminate a contract. A relational database can also store JSON without making every query efficient. Choose from operations and invariants, then compare specific engines and operational constraints.

For this teaching workload, a relational notes table makes scoped predicates, ordering and revision conditions easy to inspect. SQLite provides a reproducible local probe. A deployed multi-instance backend might use PostgreSQL with asynchronous access and connection management; A2 does not claim that SQLite results transfer numerically to PostgreSQL.

Denormalization means duplicating a value or derived representation to improve an access path. It buys read convenience with update/repair obligations. If a note title is copied into a search projection, identify the source version, propagation path and rebuild policy. Do not let a copied field quietly become a competing writer of canonical state.

---

## 3. The running schema and workload

The fixture seeds **12,000 notes: four tenants × ten owners × 300 notes**. Note IDs repeat across tenants intentionally, so tenant scoping matters. Creation timestamps have groups of three ties, so timestamp-only pagination would be ambiguous.

```sql
PRIMARY KEY (tenant, id)
-- Canonical read:
SELECT id, title, content, created_at, revision
FROM notes WHERE tenant = ? AND owner = ? AND id = ?;

-- Recent listing, metadata only:
SELECT id, title, created_at, revision
FROM notes WHERE tenant = ? AND owner = ?
ORDER BY created_at DESC, id DESC LIMIT ?;
```

The primary key supports locating a note within a tenant, but it does not fully match an owner's ordered listing. Before the new index, SQLite can narrow by tenant and then filter/sort that tenant's notes. An existing index can help while still leaving unnecessary work.

The proposed listing index is:

```sql
CREATE INDEX notes_owner_recent
ON notes(tenant, owner, created_at DESC, id DESC);
```

Equality scope comes first; ordered continuation fields follow. The chosen query returns bounded metadata rather than loading all content and slicing in application memory. A larger covering index including title/revision could avoid some table lookups, but duplicates values and adds write/storage cost; this fixture deliberately measures the simpler index.

The data source accepts already validated write inputs from the harness. It is not a new public validation/authentication layer. The list method checks its page/cursor bounds, while original A1 handles its HTTP body/domain contract.

---

## 4. How indexes reduce work, and what they cost

A B-tree index orders keys so the engine can seek to a relevant range rather than inspect every possible row. The useful question is whether its key order matches the filter, range and ordering of this query. An index is additional maintained state, so writes, storage, cache footprint and maintenance must be considered.

For multicolumn B-tree indexes, equality on leading columns and then an ordered/range column is a common useful arrangement. Do not teach “an index is never usable without its first column” as a universal rule; planners and versions can use alternative strategies, including skip scans in appropriate circumstances. Inspect the actual plan. [PostgreSQL 18 multicolumn indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html).

In the notes query, the index groups one tenant/owner's rows and orders them by creation time and ID. A different query such as “all tenants' notes containing a word” needs different reasoning. Adding every field to one composite index does not solve arbitrary access patterns.

| Index choice | Benefit to evaluate | Cost or trap |
| --- | --- | --- |
| Primary/unique key | Exact lookup and duplicate prevention | Does not automatically optimize an unrelated list order |
| Composite ordered index | Scoped range and ordering | Key order matters; other workloads may need different paths |
| Covering index | Return selected fields without additional row fetches when supported | Bigger entries and duplicated frequently changed fields |
| Partial index | Index only rows meeting a predicate | Query must imply the predicate; not used in this fixture |
| Expression index | Match a derived query expression | Expression/operator/collation must fit; not used here |

An index can be unnecessary when a query touches most rows or a tiny table is cheaper to scan. “Full scan” is not automatically a bug. The plan should be assessed against actual row counts, selectivity, ordering and latency requirements.

---

## 5. Diagnose a slow query before changing the architecture

Use a concrete statement with realistic parameters. Check returned rows, selected columns, sort/join work, plan estimates, lock waits, network/pool wait and request-level query count. A fast individual query repeated once for every list item can still create a slow request through N+1 behavior.

In PostgreSQL, `EXPLAIN` describes a chosen plan; `EXPLAIN ANALYZE` executes the statement and reports observed work. Use it deliberately, especially for writes and volatile effects, and examine estimates versus actual rows and buffers rather than treating planner cost as milliseconds. [PostgreSQL EXPLAIN guidance](https://www.postgresql.org/docs/18/using-explain.html).

A useful diagnosis sequence:

1. Reproduce the slow operation with its actual filter/order/page size.
2. Separate pool wait, lock wait, execution and response transfer.
3. Inspect the plan and query count; compare estimated and actual cardinality where supported.
4. Reduce unnecessary rows/fields and remove repeated queries.
5. Add or adjust a justified index; update statistics when appropriate.
6. Compare equivalent results and the relevant work/latency distributions under a stated workload.

The local fixture records SQLite `EXPLAIN QUERY PLAN` and counts VM progress callbacks at an interval of one instruction. Those counters describe SQLite virtual-machine work in this run, not disk reads, rows scanned or production latency. SQLite's plan text is a debugging format that can change between versions; the teaching checks intentionally target the recorded runtime. [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html).

Observed before/after on the same 20-row result:

```json
{
  "seed_rows": 12000,
  "matching_owner_rows": 300,
  "before": {
    "plan": [
      "SEARCH notes USING INDEX sqlite_autoindex_notes_1 (tenant=?)",
      "USE TEMP B-TREE FOR ORDER BY"
    ],
    "sqlite_vm_instructions": 18427
  },
  "after": {
    "plan": [
      "SEARCH notes USING INDEX notes_owner_recent (tenant=? AND owner=?)"
    ],
    "sqlite_vm_instructions": 224
  },
  "same_results": true,
  "page_size": 20
}
```

The new plan uses `notes_owner_recent` and no temporary ordering B-tree. The instruction count falls while returned results remain equal. That supports this access-path change on this fixture; it does not establish an application-wide speedup or a production QPS capacity. Index building, write amplification and memory pressure require additional workload-specific measurements.

---

## 6. Pagination: stable order, offsets and keyset cursors

An offset says “skip N rows in the current result.” It is convenient for page numbers but deeper pages require skipping more work, and inserts/deletes can shift positions between requests. A keyset cursor says “continue after this ordering boundary.” It needs an explicit total order and does not provide arbitrary page-number jumps for free.

For descending `(created_at, id)` order:

```sql
SELECT id, title, created_at, revision
FROM notes
WHERE tenant = ? AND owner = ?
  AND (created_at, id) < (?, ?)
ORDER BY created_at DESC, id DESC
LIMIT ?;
```

The ID tie-breaker matters because several notes share a timestamp. The cursor boundary and sort directions must agree. The fixture walks all 300 notes for an owner without duplicates, then compares a deep offset page with the equivalent keyset page:

```json
{
  "notes_visited": 300,
  "unique_ids": 300,
  "cursor": [
    33,
    "n00_0100"
  ],
  "offset_rows_skipped": 200,
  "same_deep_page": true,
  "offset_vm_instructions": 1024,
  "keyset_vm_instructions": 334
}
```

It also inserts a new newest note between two page requests:

```json
{
  "inserted_between_pages": "n00_new",
  "offset_duplicate_ids": [
    "n00_0280"
  ],
  "keyset_duplicate_ids": [],
  "continuation_includes_newer_insert": false,
  "snapshot_guarantee": false
}
```

The offset continuation repeats a previously seen note; the keyset continuation avoids that specific duplicate because the original ordering values are immutable. The newer insert appears before the cursor and is not included in continuation. This is useful scroll behavior, not a frozen snapshot of the dataset.

If ordering by mutable `updated_at`, an edited item can move across the boundary. Deletion and permission changes also affect later pages. A snapshot/export requirement needs a separate design, such as a database snapshot or a bounded materialized export. A public cursor should carry query/order version and scope as appropriate, validate page size and reject tampering when needed. The fixture uses a typed Python tuple, not signed or opaque HTTP cursor tokens.

---

## 7. Consistency: specify the operation, not a vague database label

| Requirement | Concrete user-visible meaning | Possible data-path choice |
| --- | --- | --- |
| Read after own write | After an accepted edit, the editor should see that revision or newer | Authoritative read or explicit minimum-version routing |
| Monotonic reads | A session should not go from revision 5 back to revision 4 | Track a version requirement and choose an eligible source |
| Atomic conditional update | An old revision cannot overwrite a newer one | Predicate checked in authoritative transaction |
| Eventually fresh browsing | Another view may briefly show an older title under a stated policy | Cache/replica with lag handling and explicit freshness limits |
| Permission correctness | Revocation must not leak content through stale derived state | Current authority check or a deliberately designed authorization freshness contract |

“Strong consistency” needs a named guarantee and boundary. Database transaction isolation, replica freshness, cache validity and distributed linearizability are different questions. A transaction can correctly update canonical data while a separate cache returns an older copy.

The A2 write guard is the same basic invariant as A1: a conditional SQL update includes tenant, owner, ID and expected revision. Reads from a cache never approve the write. If a precheck reads revision 1 from memory and then the database performs an unconditional overwrite, the cached precheck did not prevent a lost update.

A minimum-version read can reject a cache/replica result below the client's acknowledged revision and fall back to the authority. That design still needs version scope, cache replacement rules, fallback capacity and a bounded wait/deadline. It is described here; the fixture does not implement a networked minimum-version router.

PostgreSQL's isolation levels define transaction behavior, including how snapshots and concurrent changes are handled. A stronger isolation setting can require transaction retries; it does not automatically invalidate an external cache. [PostgreSQL transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html).

---

## 8. Read replicas, failover and lag

Replication copies database state to additional nodes. It can support read distribution and recovery, depending on topology and durability settings. It does not partition one dataset into independent write owners. A replica may lag even while it is reachable and serving requests.

PostgreSQL streaming replication is asynchronous by default; synchronous configurations can wait for different acknowledgement stages. Waiting for remote receipt/flush and waiting for replay visibility are not interchangeable. Choose the commit acknowledgement contract and eligible read sources explicitly. [PostgreSQL standby/replication guidance](https://www.postgresql.org/docs/18/warm-standby.html).

Proposed note-read routing, not an implemented replica deployment:

```text
edit -> authoritative writer -> commit revision 7 -> acknowledge
                                   |
                                   +-- replication --> replica may still expose revision 6

editor's immediate read -> authority or source known to meet required version
other stale-tolerant browse -> eligible replica, with lag/degraded policy
```

Do not use a lagging replica to decide a permission revocation, account balance or reservation without an explicit correctness model. The cost of stale reads depends on the operation; an old dashboard count and an unauthorized private note are not equivalent.

Failover also requires deciding who is permitted to become writer and how the old writer is fenced from continuing writes. Asynchronous acknowledged writes may be absent from a promoted replica. These are recovery-point and split-brain concerns, not problems solved merely by adding a load balancer. A2 introduces the decisions; A3/A4 develop failure handling and operation.

Replica reads can move query load but still consume replication bandwidth, storage and maintenance work. They do not fix an N+1 request, an unsuitable index or an overloaded primary write path automatically.

---

## 9. Partitioning, sharding and hot tenants

| Mechanism | What changes | What it does not automatically do |
| --- | --- | --- |
| Table partitioning | A logical table is divided by a partition rule | Spread work across independent database hosts |
| Sharding | Different subsets are placed under different database/shard owners | Preserve cheap cross-shard joins/transactions |
| Replication | Additional copies of a dataset/shard | Divide a single write stream among independent owners |
| Application scale-out | More application instances | Increase database capacity or eliminate shared bottlenecks |

PostgreSQL table partitioning can support pruning, lifecycle operations and partition-specific management when query predicates align. It remains a different choice from distributing shards across independent servers. [PostgreSQL partitioning](https://www.postgresql.org/docs/18/ddl-partitioning.html).

A shard key should align common operations with locality while distributing actual work. Tenant-based placement keeps a tenant's notes and related operations together, but one very busy tenant can dominate one shard. Hashing distributes keys; it cannot divide the work of a single indivisible key.

The offline placement model uses a stable SHA-256 prefix modulo four shards. One tenant contributes 901 of 1000 hypothetical requests, and the other 99 contribute one each. The exact distribution is embedded with the scaling results in §16. It is deliberately simple modulo placement, not consistent hashing, a live router or a deployed storage cluster.

Potential responses to a hot tenant include a dedicated placement, a finer partition key such as tenant plus bucket, read caching for suitable data, or separating a heavy derived workload. Each changes routing, locality, migration or transaction requirements. Request salting can spread reads/writes only when the data model can locate/recombine the resulting buckets; adding randomness to keys is not a free fix.

DynamoDB guidance emphasizes distributing activity across partition keys, which illustrates why key count alone is insufficient to assess skew. Engine-specific partition limits and adaptive behavior require that engine's own design and measurements. [AWS partition-key guidance](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html).

Resharding requires a migration protocol: authoritative routing version, backfill, ongoing writes, verification, cutover and rollback. Changing `hash % 4` to `hash % 5` while old data stays in place loses the routing relationship. The model counts remapped tenant identities; it does not migrate data or claim the same fraction of bytes/traffic moves.

---

## 10. Cache-aside and the cache contract

Cache-aside normally checks a cache, loads from the source on a miss, and stores a derived value. On a write, the application commits canonical state and invalidates or updates the relevant cache according to a defined protocol. The pattern does not inherently guarantee that every read is current. [Microsoft Cache-Aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside).

```text
read -> scoped cache lookup --hit--> cached representation
                    |
                   miss
                    v
            authoritative scoped read -> cache insertion -> result

write -> authoritative conditional commit -> local invalidation
```

Before adding Redis or local memory, answer:

| Decision | A2 fixture choice | Production follow-up |
| --- | --- | --- |
| Key | Tuple `(tenant, owner, note_id)` | Include representation/query/permission version if required |
| Value | Immutable note representation with revision | Serialization/schema evolution and sensitive fields |
| Expiry | Fixed TTL from insertion; injected clock | Real monotonic expiry, jitter and refresh policy |
| Capacity | LRU bound on stored entry count | Byte/memory bound, value size and in-flight admission |
| Negative results | Missing/errors are not cached | A short negative TTL may help only under explicit creation/authorization policy |
| Coalescing | One in-flight load per key and local epoch | Cross-instance coordination if required |
| Invalidation | Writing instance removes key and advances local epoch | Distributed propagation, missed messages and recovery |
| Failure | Loader exception propagates; pending task released | Bounded fallback, deadlines and overload policy |

Including tenant and owner prevents namespace collisions in this immutable-ownership example. It does not verify credentials or solve dynamic sharing/revocation. If permissions change, a previously cached authorized value may no longer be safe; recheck authority or design permission-version/freshness behavior explicitly.

TTL limits the lifetime of an installed entry. It is not a universal bound on how old the underlying data is: a loader can take an old snapshot, pause, and install it later; a replica source may already lag; invalidation may be missed. Measure the actual freshness boundary and account for those delays.

---

## 11. Cache expiry, eviction, stampedes and hot keys

Expiry removes an entry from eligibility after time; eviction removes an entry to make room. A cache can evict a valid entry before TTL, and an expired entry may remain allocated until touched unless cleanup actively removes it. The local implementation bounds retained entries and checks expiry on access; it is not a background expiry daemon.

A stampede occurs when many callers miss an expensive key and all load the source. Single-flight coalesces concurrent local loads. TTL jitter spreads expiry times across different keys; it does not eliminate a single extremely hot key or coordinate multiple processes by itself.

The fixture pauses one real SQLite result with an `asyncio.Event`, starts ten readers, then releases it. Observed result:

```json
{
  "callers": 10,
  "database_reads": 1,
  "coalesced": 9,
  "stats": {
    "hits": 0,
    "misses": 10,
    "loads": 1,
    "coalesced": 9,
    "expired": 0,
    "evictions": 0,
    "fenced": 0,
    "invalidations": 0
  }
}
```

There are ten caller misses but one database load and nine coalesced callers. Distinguish caller miss rate from backend load rate when reading metrics. A high hit ratio can still hide an expensive miss path or unacceptable p99 latency.

Single-flight is not admission control: many different missing keys can still create many tasks. The fixture bounds stored entries, not total concurrent unique loads or byte usage. A deployed service needs request deadlines, bounded database concurrency, queue/admission limits and a policy for overload. Cancelling one waiter should not destroy shared work needed by another; the harness verifies that case and closes remaining tasks at cleanup.

Redis' cache-aside example shows cache lookup/fill, invalidation and stampede protection with Redis-specific mechanisms. A distributed lock needs safe ownership/release and expiry behavior; the process-local cache here does not implement those server-side semantics. [Redis cache-aside reference](https://redis.io/docs/latest/develop/use-cases/cache-aside/nodejs/).

Write-through updates canonical storage and cache under a chosen coordination policy; two different systems still do not become one atomic transaction automatically. Write-behind acknowledges before canonical persistence and therefore needs durable buffering, retry/order policy and loss handling. Do not use a volatile process dictionary as a durable write-behind queue for private notes.

---

## 12. Invalidation races and a deliberately limited local fix

Deleting a cache entry after a database write can race with an older in-flight reader. The harness forces this interleaving using a real database snapshot captured before the write:

```json
{
  "committed_revision": 2,
  "old_reader_revision": 1,
  "next_cached_revision": 1,
  "timeline": [
    "reader captures revision 1",
    "writer commits revision 2",
    "writer deletes cache entry",
    "reader fills revision 1 after invalidation"
  ]
}
```

Canonical revision is 2, but the old reader inserts revision 1 after invalidation. The next cached read is stale. “Commit, then delete” alone does not stop stale refill.

The local fix uses one generation counter, called an epoch:

1. A loader captures the cache's current epoch.
2. After the writer commits, invalidation deletes the key and increments the epoch.
3. In-flight work is keyed by `(scoped key, epoch)`, so a new caller cannot join an old-generation task.
4. A loader inserts only if its captured epoch is still current.
5. An overlapping caller retries at most once; repeated invalidation produces an explicit `Churn` outcome instead of unbounded retries.

Observed fixed interleaving:

```json
{
  "post_invalidation_reader": 2,
  "overlapping_reader": 2,
  "database_loads": 2,
  "stats": {
    "hits": 2,
    "misses": 2,
    "loads": 2,
    "coalesced": 0,
    "expired": 0,
    "evictions": 0,
    "fenced": 1,
    "invalidations": 1
  }
}
```

This scalar epoch deliberately fences unrelated in-flight loads too. It avoids an unbounded per-key tombstone map but can cause avoidable retries when writes are frequent. The cache is designed for one asyncio event loop and a cooperating local invalidation path; it is not thread-safe or a distributed fencing protocol.

Two independent cache objects, backed by two SQLite connections, demonstrate the remaining gap:

```json
{
  "writer_cache_revision": 2,
  "other_cache_before_expiry": 1,
  "other_cache_after_expiry": 2,
  "invalidation_broadcast": false
}
```

The writer's cache refreshes to revision 2 while the other cache remains at revision 1 until expiry. The two caches are in one verification process, not two deployed hosts, but their invalidation state is independent. A local fix cannot establish a cross-instance freshness guarantee.

Distributed choices include reliable invalidation/version propagation, a shared cache with a suitable update/fencing protocol, authoritative version checks, or bypassing derived state for strict reads. Each needs missed-message/reconnect behavior, lag policy and cost analysis. Delayed double-delete and short TTL can reduce stale windows but should not be claimed as complete race proofs without explicit timing assumptions.

---

## 13. Runnable data/index/pagination source

All files live under `examples/system-design/module-2-data-caching-scaling/`. Three exact runnable source files are embedded in this chapter. `verify.py` contains the named assertions and deterministic interleavings.

`data.py` uses real file-backed SQLite. `profile()` measures the selected query under a progress handler, then removes that handler in `finally`. The schema is new fixture data; it does not alter A1 databases or existing database services.

```python
"""Real SQLite query/index/pagination probe; supplied scope is NOT authentication."""
from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class Scope:
    tenant: str
    owner: str


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    content: str
    created_at: int
    revision: int


class Missing(Exception):
    pass


class Stale(Exception):
    pass


class Notes:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.reads = 0
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS notes (
                tenant TEXT NOT NULL, owner TEXT NOT NULL, id TEXT NOT NULL,
                title TEXT NOT NULL, content TEXT NOT NULL,
                created_at INTEGER NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
                PRIMARY KEY(tenant,id)
            ) STRICT;
        ''')

    def seed(self):
        # 4 tenants x 10 owners x 300 notes; timestamps deliberately have ties.
        rows = [(f't{t}', f'u{u}', f'n{u:02}_{i:04}', f'Note {i}', 'private text', i // 3, 1)
                for t in range(4) for u in range(10) for i in range(300)]
        with self.db:
            self.db.executemany('INSERT INTO notes VALUES(?,?,?,?,?,?,?)', rows)
        return len(rows)

    def add_listing_index(self):
        self.db.execute('''CREATE INDEX notes_owner_recent
            ON notes(tenant,owner,created_at DESC,id DESC)''')
        self.db.execute('ANALYZE')

    @staticmethod
    def query(scope, limit=20, cursor=None, offset=0):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('limit must be an integer in 1..100')
        if type(offset) is not int or offset < 0:
            raise ValueError('offset must be a nonnegative integer')
        if cursor is not None and offset:
            raise ValueError('choose cursor or offset')
        sql = 'SELECT id,title,created_at,revision FROM notes WHERE tenant=? AND owner=?'
        parameters = [scope.tenant, scope.owner]
        if cursor is not None:
            if not isinstance(cursor, tuple) or len(cursor) != 2 or type(cursor[0]) is not int or not isinstance(cursor[1], str):
                raise ValueError('cursor must be (created_at,id)')
            sql += ' AND (created_at,id) < (?,?)'
            parameters.extend(cursor)
        sql += ' ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?'
        return sql, [*parameters, limit, offset]

    def listing(self, scope, limit=20, cursor=None, offset=0):
        sql, parameters = self.query(scope, limit, cursor, offset)
        return [dict(row) for row in self.db.execute(sql, parameters)]

    def profile(self, scope, limit=20, cursor=None, offset=0):
        sql, parameters = self.query(scope, limit, cursor, offset)
        plan = [row['detail'] for row in self.db.execute('EXPLAIN QUERY PLAN '+sql, parameters)]
        instructions = 0

        def progress():
            nonlocal instructions
            instructions += 1
            return 0

        self.db.set_progress_handler(progress, 1)
        try:
            rows = [dict(row) for row in self.db.execute(sql, parameters)]
        finally:
            self.db.set_progress_handler(None, 0)
        return {'plan': plan, 'sqlite_vm_instructions': instructions, 'rows': rows}

    def get(self, scope, identity):
        self.reads += 1
        row = self.db.execute('''SELECT id,title,content,created_at,revision FROM notes
            WHERE tenant=? AND owner=? AND id=?''', (scope.tenant, scope.owner, identity)).fetchone()
        if row is None:
            raise Missing('not found')
        return Note(**dict(row))

    def replace(self, scope, identity, revision, title):
        # This repository probe accepts trusted, already validated write inputs.
        with self.db:
            changed = self.db.execute('''UPDATE notes SET title=?,revision=revision+1
                WHERE tenant=? AND owner=? AND id=? AND revision=?''',
                (title, scope.tenant, scope.owner, identity, revision)).rowcount
            if not changed:
                self.get(scope, identity)
                raise Stale('revision changed')
        return self.get(scope, identity)

    def close(self):
        self.db.close()
```

The metadata listing is bounded to 1–100 rows and filters both tenant and owner even when a cursor is present. A cursor selects a continuation boundary; it does not replace permission scope. A public API must also bind scope to verified identity rather than trusting those two supplied strings.

`created_at` is an integer solely to make ordering and ties obvious in the fixture. A deployed model needs timestamp precision, timezone/UTC semantics, source authority and a stable tie-breaker; wall-clock timestamps alone are not a globally unique order.

---

## 14. Runnable cache source

`cache.py` receives an asynchronous loader and a clock. Production would normally use a monotonic clock for duration-based local expiry; the harness supplies an advancing fake clock so expiry tests do not sleep.

```python
"""Bounded process-local cache with TTL, single-flight and local invalidation fencing."""
from collections import OrderedDict
import asyncio
import math


class Churn(Exception):
    pass


class CacheAside:
    def __init__(self, loader, clock, ttl=10, capacity=128):
        if not math.isfinite(ttl) or ttl <= 0 or type(capacity) is not int or capacity < 1:
            raise ValueError('positive finite TTL and capacity required')
        self.loader, self.clock, self.ttl, self.capacity = loader, clock, ttl, capacity
        self.entries = OrderedDict()
        self.pending = {}
        self.epoch = 0
        self.stats = {'hits': 0, 'misses': 0, 'loads': 0, 'coalesced': 0, 'expired': 0,
                      'evictions': 0, 'fenced': 0, 'invalidations': 0}

    @staticmethod
    def key(scope, identity):
        return scope.tenant, scope.owner, identity

    def invalidate(self, scope, identity):
        self.entries.pop(self.key(scope, identity), None)
        # A single global epoch avoids an ever-growing per-key generation map.
        # It conservatively fences unrelated in-flight loads too.
        self.epoch += 1
        self.stats['invalidations'] += 1

    async def _load(self, key, scope, identity, epoch):
        task_key = key, epoch
        try:
            self.stats['loads'] += 1
            value = await self.loader(scope, identity)
            if epoch != self.epoch:
                self.stats['fenced'] += 1
                return value
            # TTL begins at cache insertion, not at the database snapshot time.
            self.entries[key] = self.clock()+self.ttl, value
            self.entries.move_to_end(key)
            while len(self.entries) > self.capacity:
                self.entries.popitem(last=False)
                self.stats['evictions'] += 1
            return value
        finally:
            self.pending.pop(task_key, None)

    async def get(self, scope, identity):
        key = self.key(scope, identity)
        for _ in range(2):  # Bounded retry if a local write invalidates an active load.
            entry = self.entries.get(key)
            if entry is not None:
                expiry, value = entry
                if self.clock() < expiry:
                    self.entries.move_to_end(key)
                    self.stats['hits'] += 1
                    return value
                self.entries.pop(key)
                self.stats['expired'] += 1
            self.stats['misses'] += 1
            epoch = self.epoch
            task_key = key, epoch
            task = self.pending.get(task_key)
            if task is None:
                task = asyncio.create_task(self._load(key, scope, identity, epoch))
                # A cancelled waiter must not create an unobserved task exception.
                task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
                self.pending[task_key] = task
            else:
                self.stats['coalesced'] += 1
            value = await asyncio.shield(task)  # One cancelled caller does not cancel shared work.
            if epoch == self.epoch:
                return value
        raise Churn('local invalidation changed twice; caller must retry within its deadline')

    async def close(self):
        tasks = list(self.pending.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.entries.clear()
```

The loaded `Note` dataclass is immutable, so a caller cannot edit the shared cached representation accidentally. Mutable list/dict values would require a deliberate copy/serialization/immutability policy. The cache never stores a `Missing` exception as if it were a note.

The `asyncio.shield()` boundary keeps one cancelled waiter from cancelling the shared load. It does not give the loader an automatic deadline. The owning service must provide bounded dependency work and close/cancel tasks during shutdown. The loader in this fixture performs synchronous SQLite reads before optional event barriers, so this is controlled scheduling evidence, not non-blocking database performance evidence.

All writes in the local-fence scenario explicitly call invalidation after commit. A write through a different process, admin tool or independent cache object does not advance that local epoch. The two-cache experiment demonstrates precisely that limitation.

---

## 15. Scaling a backend without moving the bottleneck blindly

Scale up adds resources to a node; scale out adds nodes/instances. The deciding question is which resource or constraint is saturated: CPU, database work, lock contention, connections, storage I/O, network, provider quotas or an indivisible hot key.

| Observation | First hypothesis to investigate | Why another API instance may not solve it |
| --- | --- | --- |
| CPU saturation in independent request work | More CPU or application replicas | Shared dependencies may still cap throughput |
| Pool wait with long queries | Query/transaction time and concurrency budget | More replicas multiply possible database connections |
| One tenant or key dominates work | Key placement, work reduction or isolation | Uniform key distribution does not imply uniform demand |
| Expensive repeated read | Query optimization and suitable cache | Cold/failing cache can expose full source demand |
| Write lock contention | Transaction scope and authoritative state design | Replicas do not split one locked write owner |
| Large response/network time | Bound fields/pages and payload | More application CPU does not shrink bytes |

Stateless routing means a later request need not return to the same instance for correctness. Canonical notes, operation outcomes and accepted work must survive instance replacement according to their contracts. A local LRU cache may be lost safely only if the source can serve misses; its disappearance can still cause a capacity incident.

Budget connections across all application instances, workers, maintenance and operational access. `instances × maximum pool size` is a possible ceiling, not the actual active-query count. A pooler can change connection behavior but does not manufacture unlimited database CPU or remove transaction constraints.

Load balancing chooses eligible targets; health checks do not prove equal work or current replica state. A hot request can occupy more resources than a cheap request. Autoscaling should follow measured saturation/latency and bounded downstream demand, not only an increasing HTTP request counter.

---

## 16. Runnable load and placement arithmetic

`scaling.py` is an offline model. Request rates, cache hit fraction, pool sizes and connection headroom are hypothetical inputs, not observed production values. It also illustrates stable-hash modulo placement without deploying shards.

```python
"""Offline hypothetical load/placement arithmetic; no capacity or shard deployment test."""
from collections import Counter
from hashlib import sha256
import math


def demand(read_qps, hit_fraction, instances, pool_per_instance, db_budget, utilization=0.7):
    if type(read_qps) is not int or read_qps < 0 or not 0 <= hit_fraction <= 1:
        raise ValueError('invalid workload')
    if type(instances) is not int or instances < 1 or type(pool_per_instance) is not int or pool_per_instance < 1:
        raise ValueError('positive instance and pool counts required')
    if type(db_budget) is not int or db_budget < 1 or not 0 < utilization <= 1:
        raise ValueError('invalid database budget or utilization')
    return {'read_qps': read_qps, 'assumed_hit_fraction': hit_fraction,
            'estimated_db_read_qps': round(read_qps*(1-hit_fraction), 6),
            'maximum_application_connections': instances*pool_per_instance,
            'application_connection_budget': math.floor(db_budget*utilization)}


def place(tenant, shards):
    if type(shards) is not int or shards < 1:
        raise ValueError('positive shard count required')
    return int.from_bytes(sha256(tenant.encode('utf-8')).digest()[:8], 'big') % shards


def placement_demo(shards=4):
    # Each tenant has one synthetic request weight, not a measured trace.
    weights = {f'tenant_{i:03}': 1 for i in range(100)}
    weights['tenant_000'] = 901  # One tenant supplies 90.1% of the 1000 requests.
    by_shard = Counter()
    for tenant, weight in weights.items():
        by_shard[place(tenant, shards)] += weight
    moved = sum(place(tenant, shards) != place(tenant, shards+1) for tenant in weights)
    return {'tenants': len(weights), 'synthetic_requests': sum(weights.values()),
            'hot_tenant_requests': weights['tenant_000'],
            'requests_by_shard': {str(i): by_shard[i] for i in range(shards)},
            'tenants_remapped_on_modulo_resize': moved, 'remap_denominator_tenants': len(weights)}
```

Observed calculated output:

```json
{
  "warm_assumption": {
    "read_qps": 10000,
    "assumed_hit_fraction": 0.95,
    "estimated_db_read_qps": 500.0,
    "maximum_application_connections": 400,
    "application_connection_budget": 140
  },
  "cold_assumption": {
    "read_qps": 10000,
    "assumed_hit_fraction": 0,
    "estimated_db_read_qps": 10000,
    "maximum_application_connections": 400,
    "application_connection_budget": 140
  },
  "cold_to_warm_db_demand_ratio": 20.0,
  "placement": {
    "tenants": 100,
    "synthetic_requests": 1000,
    "hot_tenant_requests": 901,
    "requests_by_shard": {
      "0": 24,
      "1": 924,
      "2": 25,
      "3": 27
    },
    "tenants_remapped_on_modulo_resize": 83,
    "remap_denominator_tenants": 100
  }
}
```

At an assumed 10,000 reads/s and 95% cache hits, the simple model leaves 500 database reads/s. With a cold cache it leaves 10,000, a 20× demand difference. This does not mean the database can sustain either rate; it is demand arithmetic. It excludes coalescing, writes, refreshes, background work and variable query cost.

Twenty instances with a pool ceiling of twenty each can collectively request 400 connections. The selected illustrative budget is 70% of 200, or 140 for the application. That mismatch shows why adding replicas needs a shared budget; the remaining capacity is a chosen reserve, not an industry-prescribed percentage.

The placement model puts 924 synthetic requests on one shard because the 901-request tenant cannot be split by tenant-only placement. Resizing modulo placement from four to five changes 83 of 100 tenant locations in this run. Those denominators are identities, not bytes or request weights; neither number is a live balancing or migration benchmark. See [Resume M27](/docs/resume-skills/system-design-load-balancer) for the separate consistent-hashing mechanisms and evidence.

---

## 17. Failure policy, CAP and verification scope

### Cache or source unavailable

A cache outage can be survivable if bounded source fallback fits the source's capacity. Unbounded fail-open fallback can overload the database and turn a cache incident into a wider outage. Choose request deadlines, concurrency limits, load shedding and which stale reads are acceptable. Permission-sensitive content must not be served under an invented “stale is fine” rule.

The fixture propagates loader failure, removes its in-flight record and allows a later successful retry. It does not run a Redis outage or implement admission control. Its tests make local failure behavior observable without claiming a production fallback policy.

### CAP at an actual network partition

For an atomic/linearizable read-write service under a partition, a side unable to learn whether the other side accepted a write cannot guarantee both a current consistent result and completion of every request. CAP availability is a formal completion requirement, not an uptime percentage or merely returning an error. Identify the inaccessible communication and the affected operation before invoking the theorem. [Gilbert and Lynch, Perspectives on CAP](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf).

For private notes, a disconnected replica might return an old revision under a weaker browsing contract, or refuse/wait when an authoritative current result is required. Neither choice authorizes a stale permission decision. The fixture does not simulate a network partition or prove a distributed consistency model.

### Run and interpret the evidence

Verified on **2026-10-16** using **Python 3.12.10**, **SQLite 3.49.1**, and **Windows 11**. No third-party Python packages, Docker, Redis, PostgreSQL server, external credentials or listener are required.

From the repository root in PowerShell:

```powershell
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 'examples/system-design/module-2-data-caching-scaling/verify.py'
```

Or run `python verify.py` from the example directory with Python 3.12 or later. Every verification run creates a private temporary database directory, closes both connections and async cache tasks, and removes that directory. It does not mutate an existing database or start port 3000.

**91 local checks passed:** 12 queries, 16 pagination, 23 cache basics, 10 single flight, 11 invalidation, 4 multi cache, 2 cleanup, 13 scaling models. Three exact source files and nine exact observation blocks are embedded. `verification-results.json` records every assertion and its scope.

Observed expiry, scope and bounded entry behavior:

```json
{
  "database_calls_for_cold_warm_before_expiry_after_expiry": 2,
  "ttl_seconds": 10,
  "expires_at_equal_time": true,
  "owner_miss_not_cached": true,
  "bounded_cache_entries": 2,
  "evictions": 1
}
```

No wall-clock latency, throughput, distributed lock, replica failover, shard migration, network partition or production authentication was verified. A lower SQLite VM instruction count is evidence of less work for this query in this fixture. Hypothetical demand and placement numbers remain model outputs. Those distinctions should carry into your interview explanation.

---

## 18. Common interview questions with answer checkpoints

### Q1. How do you choose a database for a new backend?

Start with operations, relationships, invariants, query shapes, data volume, consistency and operational constraints. For private notes, scoped lookups and conditional writes fit a relational baseline. Explain the deciding requirements and an alternative rather than naming a fashionable database.

### Q2. What is an access pattern?

The actor, predicates, order, fields, page size, frequency and freshness of a query or mutation. “Recent notes for one tenant/owner, twenty metadata rows ordered by creation time and ID” is an actionable pattern; “we need fast reads” is not.

### Q3. Why did the primary key not fully optimize listing?

`(tenant,id)` supports one note within a tenant. It does not group by owner and provide the requested creation order. The actual pre-index plan narrows by tenant but still filters/sorts; the composite listing index matches more of the query.

### Q4. How do you choose composite index order?

Match equality scope, range and ordering for important queries, then inspect the actual planner behavior. Here tenant and owner lead, followed by descending creation time and ID. Avoid universal rules about unusable suffixes; engine/version strategies and selectivity matter.

### Q5. What does a covering index do?

It contains the fields a query can return without additional table/heap fetches under the engine's rules. It can reduce reads but increases entry size and update work. A2's listing index does not include every selected value and is not claimed to be covering.

### Q6. Why not index every column?

Each index consumes storage/memory and must be maintained on relevant writes. It may not match useful query shapes and can slow bulk changes. Prioritize measured access paths, uniqueness and maintenance cost rather than raw index count.

### Q7. How would you investigate a slow query?

Reproduce parameters, separate pool/lock/execution/transfer time, inspect plan and cardinality, check query count/N+1, bound rows/fields and compare equivalent results after a targeted change. Do not jump from one slow request to sharding without finding its work.

### Q8. What did the index experiment measure?

SQLite query-plan text and VM instruction callbacks for equal 20-row results. The plan removes temporary ordering and instruction work drops. It did not measure production latency, disk I/O, QPS capacity or another engine's planner.

### Q9. What is N+1 and how can you reduce it?

One list query followed by one query per item can make request work grow with page size. Consider joins, bounded batch fetches or suitable eager loading, while avoiding unbounded result multiplication. Measure request-level query count and returned data, not only each query's isolated speed.

### Q10. Offset or keyset pagination?

Offsets support convenient page numbers but skip work and drift when rows move. Keysets continue after an ordered boundary and suit sequential scrolling. The fixture uses creation time plus ID; keysets do not automatically provide a dataset snapshot or random page jumps.

### Q11. Why does a cursor need a tie-breaker?

Several rows can share a timestamp. Ordering and continuation by timestamp alone can omit or repeat tied rows. `(created_at,id)` supplies a total scoped order here, and the continuation predicate matches its descending direction.

### Q12. Does keyset pagination eliminate every consistency issue?

No. Newer inserts can remain outside continuation, deletes remove rows and mutable ordering fields can move items. The real insert test avoids an offset duplicate under immutable order, but does not establish snapshot semantics. State the product's scrolling/export promise.

### Q13. What is the difference between partitioning, sharding and replication?

Partitioning divides a logical dataset by a rule; sharding places subsets under different database owners/servers; replication creates additional copies. Each solves different placement/read/recovery problems, and combinations still need routing, ownership and failure policies.

### Q14. How do you choose a shard key?

Balance common-query locality, atomicity needs and actual work distribution. Tenant placement keeps tenant data together but can create a hot tenant shard. Evaluate skew and cross-shard operations, not only the number of distinct keys.

### Q15. Why can a good hash still produce a hot shard?

Hashing distributes identities, while workloads attach unequal weights to those identities. One tenant supplying 901 of 1000 requests stays on one shard in the model. A finer data partition or work-reduction/isolation policy is needed to address that indivisible load.

### Q16. Do read replicas guarantee read-after-write?

No. A reachable replica can lag the acknowledged write. Route strict reads to authority or an eligible source meeting a required position/version. The exact acknowledgement/replay policy matters; a generic “synchronous” label does not answer every read-visibility question.

### Q17. What happens during database failover?

The system chooses an eligible writer, fences the old authority and routes clients according to a recovery contract. An asynchronously replicated acknowledged write may be missing. Adding another node does not alone establish safe promotion or zero data loss.

### Q18. What is cache-aside?

Look up derived data in cache, load from the source on a miss and fill according to an expiry/consistency policy. Writes coordinate canonical commit and invalidation/update. Specify key scope, value, TTL, capacity, errors and source authority rather than assuming cached data is always current.

### Q19. Why include tenant and owner in a cache key?

The fixture permits identical note IDs across tenants and uses owner-private scope. A note-ID-only key could answer a different principal's request. Scoped keys prevent those collisions but do not authenticate the caller or solve dynamic permission revocation.

### Q20. Does a ten-second TTL mean data is at most ten seconds old?

Not universally. TTL measures eligibility since insertion; a paused loader or lagging replica can supply an older snapshot. Invalidation loss adds another freshness issue. Define and measure the source-to-observation boundary before promising a staleness bound.

### Q21. Expiry versus eviction?

Expiry makes an entry ineligible after its time bound. Eviction removes it to satisfy capacity, possibly before expiry. The local cache checks expiry on access and uses LRU entry eviction; it does not bound bytes or run a background cleanup service.

### Q22. What is a cache stampede?

Many concurrent misses trigger repeated source work for the same data. Local single-flight reduces ten simultaneous misses to one load in the fixture. Other processes, many unique keys and dependency timeouts still require coordination/admission decisions.

### Q23. What is the stale-refill race?

A reader captures old state, a writer commits and deletes the cache entry, then the old reader fills stale state after deletion. A2 reproduces revision 1 returning after revision 2 commits. Deletion after commit alone does not close that interleaving.

### Q24. How does the local epoch fix work?

Loads capture a generation, invalidation advances it, new callers do not join old-generation work and old loads cannot install values. Overlapping callers retry within a small bound. The scalar generation conservatively affects unrelated loads and applies only to one cooperating event loop/cache.

### Q25. Does local invalidation keep all application replicas fresh?

No. The independent-cache experiment shows another cache returning revision 1 until TTL despite canonical revision 2. A deployed design needs propagation/version checks, a suitable shared-cache protocol or a weaker documented freshness promise. Independent local correctness is not cross-instance coherence.

### Q26. What happens if the cache fails?

Choose bounded source fallback, stale service where permitted, or explicit rejection. Unlimited fallback can overload the database, especially when warm-cache assumptions hide cold demand. Permission-sensitive content requires its own current-authority policy.

### Q27. Why can scaling API instances overload the database?

More instances multiply possible connections and concurrent source work. The model's twenty pools of twenty yield a 400-connection ceiling against a selected 140-connection application budget. Budget globally and measure query/transaction work before adding replicas.

### Q28. What is a stateless application instance?

Correctness does not require the next request to return to that instance's private durable state. A disposable cache is compatible only when authoritative state is elsewhere and miss/recovery behavior is safe. Sticky routing does not replicate state or make failure recovery automatic.

### Q29. What does CAP mean for this notes design?

Identify a partition that prevents a read source from learning an accepted write. A strict current-read contract can require refusal/waiting, while stale browsing uses a weaker guarantee. This theoretical trade-off is not a cache-hit ratio, uptime percentage or excuse to serve revoked private content.

### Q30. What would you measure before adding another data component?

Query shape/count, cardinality, p95/p99 latency, pool/lock wait, source work, cache hits and coalesced loads, freshness, key skew, resource saturation and failure behavior. State assumptions, denominators and limits. A2 provides local mechanism evidence and model arithmetic, not production capacity claims.

---

## 19. Revision sheet and a 45-minute mock

| Prompt | Recall |
| --- | --- |
| Storage choice | Operations + invariants + authority + operational constraints |
| Index | Match scoped filter/range/order; measure work and write cost |
| Query diagnosis | Separate pool/locks/execution/transfer and count queries |
| Pagination | Total order + cursor direction; scrolling is not a snapshot |
| Replica | Copy with an explicit lag/commit/read contract |
| Shard | Subset ownership; key locality versus weighted skew |
| Cache | Derived copy with key, value, expiry, capacity and failure policy |
| Stampede | Coalesce suitable loads; bound other misses and dependencies |
| Stale refill | Old load can outlive deletion; local generation fences only local work |
| Scale-out | More API capacity also means more downstream demand |
| Consistency | Name the operation and which stale result is permitted |
| Evidence | SQLite VM work and deterministic cache traces; hypothetical placement/capacity inputs |

**Mock prompt:** “Our private-notes backend is slow. Users list recent notes, view content and edit from two devices. Explain the data path and a justified growth plan.”

| Segment | Minutes |
| --- | --- |
| Clarify operations, freshness and workload | 6 |
| Choose authority, schema and scoped queries | 8 |
| Inspect index and pagination choices | 8 |
| Trace cache read/write and stale refill | 10 |
| Discuss replica/shard/cold-cache follow-up | 8 |
| Recap measurements and limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I will first inspect the actual owner-scoped recent-list query and request-level work. A tenant/owner/creation-time/ID index matches the bounded ordering, and a cursor avoids deep offset work for sequential scrolling. Canonical writes retain the revision condition. Caching is optional derived state: it needs principal scope, a freshness policy and bounded miss work. Local single-flight and invalidation fencing solve specific local interleavings, but another instance still needs coordination or an explicitly stale contract. Replicas help eligible read workloads; sharding changes ownership and migration. I will choose the next component from measured saturation and correctness requirements.

Check whether your answer named a stale-data consequence, distinguished a replica from a shard, accounted for cold-cache demand and avoided turning the fixture's counters into production benchmarks.

---

## 20. Practice tasks

1. Write access-pattern rows for private get, recent listing, replace and text search. Include actor/scope, returned fields, ordering, page size and freshness.
2. Run the fixture and explain both query plans. Identify which predicate/order the new index supports and why the original primary key still helped partially.
3. Propose a covering index and a different query, such as searching titles across owners. Explain added write/storage cost and why one index need not optimize both patterns.
4. Reproduce keyset traversal over tied timestamps. Explain the between-page insert result and what changes if order uses mutable update time.
5. Draw three read-after-write timelines: authoritative get, lagging replica and independent local cache. Mark which path can satisfy a minimum acknowledged revision.
6. Trace the naive stale-refill test step by step, then explain the epoch fix and its global-generation performance trade-off.
7. Reproduce the ten-reader single-flight case. Explain caller misses versus source loads, cancelled-waiter behavior, and what remains unbounded for many distinct keys.
8. Design a permission-revocation policy for cached shared notes. Identify which authority/version must be checked and how stale search/cache results are rejected.
9. Change the hypothetical hit ratio, instance/pool sizes and tenant weights. Calculate cold demand and connection ceilings; label every assumed input and remapping denominator.
10. Complete the 45-minute mock and answer architecture-bank Q04 and Q09–Q15. Justify one next change and list the measurements needed before deployment.

---

## 21. Completion checklist

- [ ] I can choose data representations from operations and invariants.
- [ ] I can identify canonical state and derived copies.
- [ ] I can explain composite index order and maintenance costs.
- [ ] I can interpret the real SQLite plans without inventing latency claims.
- [ ] I can explain keyset ties, offset drift and snapshot limitations.
- [ ] I can distinguish transaction isolation, replica freshness and cache validity.
- [ ] I can compare partitioning, sharding and replication.
- [ ] I can explain why a hot tenant remains hot after hashing.
- [ ] I can reproduce scoped TTL/LRU and single-flight behavior.
- [ ] I can trace stale refill, the local fence and the independent-cache gap.
- [ ] I can budget cold source demand, connections and failure fallback.
- [ ] I can state CAP's actual partition boundary and complete a timed mock.

---

## 22. Research references and continuation

Primary sources reviewed on 2026-10-16. The fixture's schema, cache algorithm, interleavings and arithmetic are authored teaching examples; sources support the named mechanisms, not a claim that a vendor prescribes this complete design or that an interview question has a measured frequency.

| Primary reference | Relevant boundary |
| --- | --- |
| [SQLite query planning](https://www.sqlite.org/queryplanner.html) | Indexed searching/ordering and planner choices |
| [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) | Plan interpretation and unstable debug-output format |
| [PostgreSQL multicolumn indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html) | Composite B-tree predicates and version-specific strategies |
| [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) | Estimated plans versus executing/analyzing statements |
| [PostgreSQL isolation](https://www.postgresql.org/docs/18/transaction-iso.html) | Transaction snapshots/concurrency semantics |
| [PostgreSQL standby replication](https://www.postgresql.org/docs/18/warm-standby.html) | Replication/acknowledgement/read-visibility choices |
| [PostgreSQL partitioning](https://www.postgresql.org/docs/18/ddl-partitioning.html) | Table partitioning and pruning |
| [Microsoft Cache-Aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) | Cache/source coordination and consistency limitations |
| [Redis cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/nodejs/) | Redis-specific cache, invalidation and stampede mechanisms |
| [AWS partition keys](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) | Weighted activity distribution across keys |
| [Gilbert/Lynch CAP perspective](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf) | Formal consistency/availability trade-off under communication failure |

Return to the [architecture roadmap](/docs/system-design), [A0: Design method](/docs/system-design/design-method-estimation) or [A1: Application architecture](/docs/system-design/application-architecture-service-boundaries). Resume [M13](/docs/resume-skills/postgresql-backend), [M14](/docs/resume-skills/mongodb-backend), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion), [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance) and [M27](/docs/resume-skills/system-design-load-balancer) provide stack-specific refreshers.

**Next: [A3 — Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency)**, architecture part 5 / numeric module 3. It develops bounded retries, operation identity, constraints/versions/locks, durable delivery, outbox and recovery/compensation. A3 is now available with its own local transaction/recovery verification scope. A4 and the worked systems follow separately.
