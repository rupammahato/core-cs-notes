# DBMS Placement Handbook — Part 12
# Module 10: NoSQL, Scaling and the SQL-vs-NoSQL Answer

**Module 10 · 3 hours · Tier 2 · Requires: M3 (normalization), M8 (ACID). Links to the HLD/system-design round**

---

## Why this module matters

Everything so far assumed one database on one machine. This module is about what happens when that stops being enough, and it is the bridge between DBMS and the **system-design round** — which is why it is worth more than its three hours suggest even though it is Tier 2.

The questions are predictable and they are all opinion-plus-fact:

- **"SQL vs NoSQL — which would you choose and why?"** The single most common DBMS question in interviews that are not written tests. It is a trap when answered as a loyalty test.
- **"Explain CAP."** Usually asked by someone who half-remembers it, so the misreading in §10.4 is worth more than the theorem.
- **"How would you scale this database?"** Wants vertical → read replicas → partitioning → sharding, in that order, with reasons.
- **"What is sharding and how do you pick a shard key?"**
- **"What is the N+1 problem?"** — an easy one that a surprising number of candidates miss.

The organising principle:

> **A single relational database is the right default, and almost every scaling technique is a specific, measured retreat from one of its guarantees: a read replica gives up read consistency, denormalization gives up update integrity, sharding gives up cross-shard joins and transactions, and NoSQL gives up the relational model itself. The engineering question is never "which is better" — it is "which guarantee can this workload afford to lose, and what does it buy".**

**How this module was verified.** The computable parts are computed: the **N+1 cost**, the **skew of six candidate shard keys** over 200,000 rows, the **key movement on resharding** under naive modulo versus consistent hashing with and without virtual nodes, the effect of **vertical and horizontal partitioning**, and the **quorum arithmetic**. CAP, the NoSQL families and the decision table are architecture, and are presented as reasoning rather than dressed up as measurements.

---

## 10.1 Scaling, in the order you should actually try it

```
  1. MAKE THE QUERIES BETTER      <- M7. Free. Do this first, always.
         indexes, sargability, N+1, SELECT *, pagination
                |
  2. SCALE UP (vertical)          <- more RAM/CPU/SSD on one box.
         boring, instant, no code change. Ceiling: one machine's limit + cost curve.
                |
  3. CACHE                        <- Redis / app cache for hot reads.
         huge win, new problem: invalidation.
                |
  4. READ REPLICAS                <- scale READS. Writes still go to one primary.
         cost: replication lag -> eventual consistency for readers.
                |
  5. PARTITION within one DB      <- table partitioning, vertical column split.
         still one machine, but less data touched per query.
                |
  6. SHARD (horizontal, many DBs) <- the only thing that scales WRITES.
         cost: cross-shard joins and transactions become your problem.
                |
  7. CHANGE THE DATA MODEL        <- NoSQL for the part of the workload that
         genuinely does not fit relational.
```

**Why the order matters more than the list.** Each step down is harder to reverse and loses a guarantee. Step 1 is free and often enough; step 6 is a one-way door. A candidate who answers "how would you scale this?" with "shard it" has skipped five cheaper options — and the right answer begins "first I'd find out *what* is slow", because a missing index has been mistaken for a scaling problem more times than anything else in this field.

**Vertical vs horizontal, as a table**, since the terms get asked directly:

| | Vertical (scale up) | Horizontal (scale out) |
|---|---|---|
| Method | A bigger machine | More machines |
| Code changes | None | Significant |
| Limit | The largest machine available | Effectively none |
| Cost curve | Super-linear — the top end is very expensive | Roughly linear |
| Failure | Single point of failure | Survives a node loss |
| Consistency | Trivially strong | Hard; the whole of §10.4 |
| Scales writes | Yes, up to the ceiling | **Yes, and it is the only thing that does** |

---

## 10.2 The two cheap wins: N+1 and connection pooling

### The N+1 query problem — measured

Lazy loading in an ORM turns one logical query into one query for the list plus one per item:

```python
authors = session.query(Author).all()           # 1 query
for a in authors:
    print(a.name, len(a.books))                 # 1 MORE query, per author
```

Verified against 500 authors and 2,000 books:

```
  N+1 (lazy loading)     queries=501   rows=500      1.62 ms
  one JOIN (eager)       queries=1     rows=500      0.43 ms
  (both return the same data)
  same answer: True
```

Only 3.8× here — and that number is deliberately unflattering, because the database was **in the same process, in memory**. The real cost is the round trip:

```
   N+1        501 queries x 0.5 ms RTT =    250.5 ms of pure waiting
   one JOIN   1 queries x 0.5 ms RTT =      0.5 ms of pure waiting
```

**That is the actual shape of the problem: 500 network round trips.** The database is not slow; the latency is paid 501 times. This is why N+1 is invisible in development against localhost and catastrophic in production.

Fixes: eager loading (`JOIN FETCH`, `selectinload`, `.includes`), a single query with a join, or batching the children into one `WHERE id IN (...)` — which is `2` queries rather than `N+1`, and usually the best balance. Detect it by **counting queries per request**, not by reading code.

### Connection pooling

Opening a database connection is expensive — TCP handshake, TLS, authentication, session setup, and server-side memory per connection. A **pool** keeps a small set of established connections and lends them out.

Two numbers worth knowing: a connection costs the server real memory (PostgreSQL forks a process per connection, so a few hundred is a lot), and the right pool size is roughly `cores × 2 + effective_spindles` — small, not large. The classic production failure is an application with a 500-connection pool on a database that performs best at 20: everything queues inside the database instead of politely queuing in the pool. PgBouncer and ProxySQL exist to fix exactly that.

---

## 10.3 Partitioning and sharding

### The vocabulary, which is routinely muddled

| Term | What it means |
|---|---|
| **Vertical partitioning** | Splitting a table's **columns** across tables — hot narrow columns here, rarely-read blobs there |
| **Horizontal partitioning** | Splitting a table's **rows** across tables, usually by range of a key — still **one database** |
| **Sharding** | Horizontal partitioning across **different machines** |
| **Replication** | Copies of the **same** data on several machines — the orthogonal axis |

So: partitioning splits data, replication duplicates it, and sharding is partitioning that crosses a machine boundary. Most real systems do both.

### Vertical partitioning — verified

One wide table `product(pid, name, price, description)` where `description` is 2 KB, split into `product_core(pid, name, price)` and `product_detail(pid, description)`:

```
     1.551 ms  select sum(price) from product
     0.478 ms  select sum(price) from product_core
```

**3.2× on a query that touches no wide column at all**, because the hot columns now occupy far fewer pages — a lot more rows per block (M7 §7.1). The costs are a join when you *do* need the description, and two tables to keep consistent. This is the row-store-versus-column-store argument from M7, applied by hand.

### Horizontal partitioning — verified, including what did *not* work

Splitting orders by year and stitching them back with a view:

```
   sum over the view (both partitions):  0.704 ms
   sum over one partition            :  0.224 ms
```

3.1× for a query that only needs one partition. But look at the plan for a query that *should* be prunable:

```
   Q: select sum(price) from orders where oid > 15000
      -> CO-ROUTINE orders
      -> COMPOUND QUERY
      -> LEFT-MOST SUBQUERY
      -> SCAN orders_2024          <- scanned anyway, though no row can match
      -> UNION ALL
      -> SCAN orders_2025
```

**SQLite scanned the 2024 partition even though `oid > 15000` cannot match anything in it.** That is the honest finding: a hand-rolled `UNION ALL` view gives you no automatic **partition pruning**. Real partitioning does — PostgreSQL declarative partitioning and MySQL `PARTITION BY RANGE` both know each partition's bounds and skip the ones that cannot match.

So the benefits of true partitioning are: **pruning** (a query restricted to one partition never touches the others), **cheap bulk deletion** (`DROP PARTITION` instead of a huge `DELETE`), and smaller indexes per partition. The cost: the partition key is effectively frozen, and queries that do not mention it get *slower*, because now every partition is scanned.

### Sharding and the shard key

The shard key decides which machine a row lives on, and it is **the highest-stakes decision in the whole system** — changing it later means moving all the data.

Two strategies:

| | Range sharding | Hash sharding |
|---|---|---|
| Rule | Shard 1 gets A–F, shard 2 G–M… | `hash(key) % n` |
| Range queries | ✅ Efficient — adjacent keys are together | ❌ Scattered across all shards |
| Even distribution | ❌ Needs care | ✅ Automatic |
| Hot spots | ✅ Likely on a monotonic key | Unlikely |
| Rebalancing | Split a range | Hard — see §10.3's movement figures |

#### Verified: six candidate shard keys, 200,000 rows, 8 shards

```
  hash(user_id)            [good]    min=24787   max=25251   hottest/ideal =  1.01x
  hash(country)            [bad]     min=0       max=140036  hottest/ideal =  5.60x
  hash(status)             [awful]   min=0       max=169858  hottest/ideal =  6.79x
  hash(tenant)             [bad]     min=0       max=96683   hottest/ideal =  3.87x
  hash(created month)      [bad]     min=9929    max=39811   hottest/ideal =  1.59x
  hash(user_id, country)   [good]    min=24664   max=25264   hottest/ideal =  1.01x
```

Read the `min=0` entries: with two distinct `status` values hashed across eight shards, **five shards hold nothing at all** and one holds 85% of the data. The "hottest/ideal" column is the number that matters — it is the factor by which the worst shard is overloaded, and it is the capacity you must provision everywhere.

**The rule that falls out of those numbers: a shard key needs high cardinality.** `country` fails not because countries are a bad idea but because there are five of them and the distribution is skewed. `tenant` fails for the classic multi-tenant reason — one customer is 40% of your data, so one shard is 40% of your load. The composite key `(user_id, country)` is fine, because `user_id` already supplies the entropy.

#### Verified: range sharding and the hot-shard problem

```
  range(user_id) over all data       min=25000   max=25000   hottest/ideal =  1.00x
  but the most recent 25,000 inserts land like this: {7: 25000}
```

Look at those two lines together. **The historical distribution is perfectly even, and 100% of new writes go to a single shard.** Range sharding on anything monotonically increasing — an auto-increment id, a timestamp, a ULID — concentrates the entire write load on the newest shard while the other seven idle. The data looks balanced in a capacity report and the system is on fire.

This is also the real reason to prefer a random UUID over a sequential id *for a shard key*, and it is in direct tension with M7's advice to prefer a sequential primary key for clustered-index locality. **Both are correct in their own layer**, and saying so is a better answer than either rule alone.

#### Verified: why resharding hurts, and what consistent hashing fixes

Naive `hash(key) % n_shards`:

```
    8 -> 9 shards:  88,737 of 100,000 keys move  ( 88.7%)
    8 -> 16 shards: 50,064 of 100,000 keys move  ( 50.1%)
    4 -> 5 shards:  80,087 of 100,000 keys move  ( 80.1%)
```

**Adding one shard to eight moves 89% of the data.** The modulus changed, so almost every key's answer changed. (Note `8 → 16` only moves 50%: doubling is the special case where every key either stays or moves to exactly one new shard — which is why capacity is often doubled rather than incremented.)

Consistent hashing, 150 virtual nodes per physical node:

```
    8 -> 9 shards:  10,094 keys move  ( 10.1%)   theoretical minimum = 11.1%
    8 -> 16 shards: 48,349 keys move  ( 48.3%)   theoretical minimum = 50.0%
    4 -> 5 shards:  20,218 keys move  ( 20.2%)   theoretical minimum = 20.0%
```

**10% instead of 89%**, and essentially at the information-theoretic minimum — the new node has to own *some* share of the keyring, and it takes almost exactly that and nothing more.

And the reason virtual nodes exist, verified:

```
  balance with 150 vnodes: min=11,265 max=13,503 hottest/ideal=1.080x
  balance with   1 vnode : min=90     max=26,711 hottest/ideal=2.137x
```

With one point per node on the ring, the arcs come out wildly unequal — one shard got **90 keys and another 26,711**. Placing each physical node at 150 random points averages the arc lengths out and brings the worst shard to 1.08× ideal. That is the whole trick, and it is why DynamoDB, Cassandra and Riak all use it.

#### What sharding costs you

The part candidates forget, and the part interviewers are listening for:

| Lost | Why |
|---|---|
| **Cross-shard joins** | The two tables are on different machines. You join in the application, or denormalize so you do not have to |
| **Cross-shard transactions** | ACID across machines needs two-phase commit, which is slow and blocks on a coordinator failure. Most systems simply forbid it |
| **Global `AUTO_INCREMENT`** | Each shard would reuse ids. You need UUIDs, a Snowflake-style id, or per-shard offsets |
| **Global uniqueness** | A `UNIQUE` constraint across shards is not enforceable by one database |
| **Cheap aggregates** | `COUNT(*)` becomes scatter-gather across every shard |
| **`ORDER BY ... LIMIT 10`** | Each shard must return its top 10 and the application merges — and `OFFSET 10000` becomes genuinely painful |
| **Operational simplicity** | Schema migrations, backups and restores now run *n* times |

**So the honest summary: shard last.** It is the only thing that scales writes, and it imports a permanent tax on every query that does not include the shard key.

---

## 10.4 CAP, and the way it is usually misread

**The theorem (Brewer, proved by Gilbert and Lynch):** a distributed data store can provide at most two of:

- **C**onsistency — every read sees the most recent write (this is *linearizability*, **not** ACID's C)
- **A**vailability — every request receives a non-error response
- **P**artition tolerance — the system keeps working when the network drops messages between nodes

### The misreading

> **"Pick two of three" is wrong, and saying so is the best thing you can do with this question.**

Network partitions are **not a design choice**. Cables fail, switches reboot, data centres lose links. If your system runs on more than one machine, **P is mandatory**. So the theorem's real content is much narrower:

> **When a partition happens, you must choose: refuse requests (keep C, lose A) or answer from possibly stale data (keep A, lose C).**

"CA" systems do not exist in any distributed setting. A single-node database is trivially CA, which is a statement about not being distributed rather than a point on the triangle.

```
                        a partition happens
                                |
              +-----------------+-----------------+
              |                                   |
        refuse to answer                   answer anyway
        (consistency)                      (availability)
              |                                   |
        CP: the minority side                AP: both sides serve, and
        returns errors until it              diverge; reconcile later
        rejoins the majority                 (last-write-wins, CRDTs,
                                             vector clocks, manual merge)
              |                                   |
        HBase, Zookeeper,                    Cassandra, DynamoDB,
        etcd, MongoDB (default),             Riak, CouchDB
        a Postgres primary with
        synchronous replication
```

**PACELC** is the refinement worth naming, because it covers the 99.9% of the time when there is no partition: *if there is a **P**artition, choose **A** or **C**; **E**lse, choose **L**atency or **C**onsistency.* A system that is CP during a partition still has to decide, in normal operation, whether to wait for a quorum (consistency) or answer from the nearest replica (latency). Cassandra is PA/EL; a strongly-consistent store is PC/EC. Naming PACELC is a strong signal in an interview because it shows you know CAP's limits.

### Quorum arithmetic — verified

With `N` replicas, `W` acknowledgements required for a write and `R` replicas consulted for a read:

```
   N=3 W=1 R=1:  W+R=2 <= N  -> EVENTUAL   write survives 2 node loss, read survives 2
   N=3 W=2 R=2:  W+R=4 >  N  -> STRONG     write survives 1 node loss, read survives 1
   N=3 W=3 R=1:  W+R=4 >  N  -> STRONG     write survives 0 node loss, read survives 2
   N=3 W=1 R=3:  W+R=4 >  N  -> STRONG     write survives 2 node loss, read survives 0
   N=5 W=3 R=3:  W+R=6 >  N  -> STRONG     write survives 2 node loss, read survives 2
   N=5 W=2 R=2:  W+R=4 <= N  -> EVENTUAL   write survives 3 node loss, read survives 3
```

The rule is **`W + R > N` ⟹ a read is guaranteed to see the latest write**, because the read set and the write set must overlap in at least one node. The table makes the trade-off concrete and tunable: `W=3, R=1` gives fast strong reads and fragile writes; `W=1, R=3` the reverse; `W=R=⌈(N+1)/2⌉` is the usual balance. **This is the knob that CAP is actually about**, and being able to write `W+R>N` is a much better answer than reciting three letters.

### BASE vs ACID

| ACID | BASE |
|---|---|
| **A**tomicity | **B**asically **A**vailable — responds, possibly with stale data |
| **C**onsistency | **S**oft state — state may change without input, as replicas converge |
| **I**solation | **E**ventually consistent — given no new writes, replicas converge |
| **D**urability | |

BASE is a deliberately cheeky backronym, not a theory. The useful content: **eventual consistency is a guarantee, not an absence of one** — it promises convergence, just not *when*. The practical question to ask of any eventually-consistent system is "eventually how long?", because the answer determines whether your application can live with it. Milliseconds of replica lag is invisible; thirty seconds is a bug report.

### The one that bites in practice: read-your-own-writes

The most common real failure from read replicas needs no theory at all: a user updates their profile (write → primary), is redirected, and the page reads from a replica that has not caught up — so they see their **old** profile and conclude the save failed. Fixes: route reads to the primary for a few seconds after a write (**sticky reads**), read from the primary for that specific user's own data, or pass the write's log position and wait for the replica to reach it. **Naming this scenario is worth more than reciting CAP**, because it is the version of eventual consistency that appears in real tickets.

---

## 10.5 The four NoSQL families

| Family | Model | Query by | Real use case | Products |
|---|---|---|---|---|
| **Key–value** | `key → opaque blob` | Key only | Sessions, caches, feature flags, rate limiters | Redis, Memcached, DynamoDB |
| **Document** | `key → JSON document` | Key, or any field inside the document | Product catalogues, user profiles, CMS content — where each item has different fields | MongoDB, CouchDB, Firestore |
| **Column-family** | `row key → column families`, sparse and wide | Row key, then column range | Time series, event logs, metrics at huge write volume | Cassandra, HBase, Bigtable |
| **Graph** | nodes and edges, both with properties | Traversal | Social graphs, fraud rings, recommendations, "friends of friends who…" | Neo4j, Neptune, JanusGraph |

Two of these deserve a sentence beyond the table, because they are where the real arguments are:

**Document stores are where the "schemaless" claim is tested.** There is no *declared* schema, but your application still has one — it is just implicit and unenforced, so version 1 documents and version 7 documents coexist and every reader must cope with both. The honest framing is **"schema-on-read instead of schema-on-write"**: you have not eliminated the schema, you have moved the enforcement from the database into the application, where it is less reliable. That is sometimes the right trade (genuinely heterogeneous items, rapid early iteration) and often just deferred pain.

**Graph databases are the one family with a genuine algorithmic advantage.** "Friends of friends of friends" is three self-joins in SQL and the cost explodes; a graph database stores adjacency directly, so a traversal follows pointers. If a candidate can name *one* query shape where NoSQL is not merely a scaling choice but an asymptotic improvement, this is it.

---

## 10.6 SQL vs NoSQL — the decision table

Answering this as a preference is the mistake. Answer it as a table and then commit to a default.

| Dimension | Relational | NoSQL |
|---|---|---|
| Schema | Declared and enforced | Flexible / enforced by the application |
| Relationships | Joins, declared foreign keys | Embedded documents, or joined in the application |
| Transactions | **Mature multi-row ACID** | Usually single-document/row; improving but weaker |
| Query language | **SQL — declarative, with an optimiser** | Product-specific APIs; limited ad-hoc querying |
| Ad-hoc analytics | **Excellent** | Often needs a pre-planned access pattern |
| Horizontal write scaling | Harder — sharding is manual | **Built in** |
| Consistency | Strong by default | Frequently tunable or eventual |
| Data integrity | Constraints in the database | Your application's job |
| Best at | Related, structured data with invariants | One access pattern at enormous scale, or genuinely irregular documents |

### The answer to give

> *"Relational is my default, because a declared schema, joins and real transactions prevent entire classes of bug, and SQL lets me answer questions I did not anticipate when I designed the schema. A single Postgres instance handles far more than most people assume, so 'we might need scale' is not by itself a reason to leave it. I would choose NoSQL when the workload genuinely does not fit: a key–value store for sessions and caches, a document store when items really are heterogeneous, a column-family store for write-heavy time series beyond what one machine can take, and a graph database for deep traversals, which is the one case where it is an asymptotic win rather than a scaling choice. And it is not either/or — most real systems are a relational database of record plus Redis plus maybe a search index."*

That answer wins because it has a default, names the exceptions concretely, and refuses the false dichotomy. Three things to be ready for as follow-ups:

- **"NoSQL is faster"** — for its intended access pattern, often yes; for an unanticipated query, usually much worse, because there is no optimiser and no index you did not plan.
- **"NoSQL scales, SQL doesn't"** — relational databases shard too (Vitess, Citus, CockroachDB, Spanner), and modern distributed SQL offers horizontal scaling *with* transactions. The dichotomy is a decade out of date.
- **"NoSQL means no schema"** — it means the schema is unenforced, which is a different and usually worse thing. Covered in §10.5.

---

## 10.7 Denormalization and caching, revisited at scale

M3 established *why* normalization matters. At scale, deliberately breaking it becomes defensible — but only on the terms set out there:

```
Denormalize when ALL of these hold:
  1. you have MEASURED the join as the bottleneck
  2. the workload is read-heavy
  3. the redundancy has exactly ONE writer, or a reliable propagation path
  4. you can tolerate the window where the copies disagree
  5. you have written down how the copy gets fixed when it drifts
```

Common and legitimate forms: a stored `comment_count` instead of `COUNT(*)` on every page load; a denormalized `author_name` on a posts table to avoid a join in a feed; a materialized view for a dashboard (M6); the data duplicated across shards so a join is never needed.

And the distinction from M3 worth repeating, because it is the one people get wrong in both directions: **storing the price that was paid at order time is not denormalization.** The order's price and the product's current price are *different facts*; copying a historical value is correct modelling, not redundancy. Redundancy is when the same fact lives in two places and they can disagree.

**Caching** is denormalization's cousin and the same discipline applies. The hard part is never the cache, it is the **invalidation** — and the three patterns to be able to name are *cache-aside* (read-through; the app checks the cache, then the DB, then fills), *write-through* (write to both synchronously, consistent and slower) and *write-behind* (write to cache, flush later; fastest and can lose data). Plus the two failure modes with memorable names: a **cache stampede**, where a popular key expires and a thousand requests hit the database simultaneously, and a **thundering herd** after a cache restart.

---

## Must remember

```
SCALING ORDER (the order IS the answer):
  1 fix the queries (free, M7)  2 scale up  3 cache  4 read replicas
  5 partition  6 shard  7 change the data model
  each step down is harder to reverse and loses a guarantee. "Shard it" as a
  first answer means five cheaper options were skipped.
vertical = bigger machine (no code change, hard ceiling, super-linear cost)
horizontal = more machines (code changes, no ceiling, THE ONLY WAY TO SCALE WRITES)

N+1: 1 query for the list + 1 per item. Verified 501 vs 1 query for the same data.
  In-process it was only 3.8x; at 0.5 ms RTT it is 250 ms vs 0.5 ms. The cost is
  ROUND TRIPS, which is why it is invisible on localhost.
  fix: eager loading / a join / batch into WHERE id IN (...). Detect by COUNTING queries.
Connection pool: right size is small (~cores*2), not large. A 500-connection pool
  on a DB that peaks at 20 just moves the queue inside the database.

vertical partitioning   = split COLUMNS (hot narrow vs cold wide). Verified 3.2x.
horizontal partitioning = split ROWS, same database
sharding                = horizontal partitioning ACROSS MACHINES
replication             = COPIES of the same data (the orthogonal axis)
true partitioning gives PRUNING; a hand-rolled UNION ALL view does NOT
  (verified: SQLite scanned a partition that could not match)
partitioning also gives cheap bulk delete (DROP PARTITION) and smaller indexes;
  it costs you: the key is frozen, and queries not mentioning it get slower

SHARD KEY needs HIGH CARDINALITY and EVEN DISTRIBUTION. Verified over 200k rows:
  hash(user_id)  1.01x hottest/ideal      hash(country)  5.60x, 3 shards EMPTY
  hash(status)   6.79x                    hash(tenant)   3.87x (one big customer)
range sharding on a monotonic key: distribution looks PERFECT (1.00x) while
  100% of new writes hit ONE shard. Verified. The report says balanced; it is on fire.
resharding: naive hash % n moved 88.7% of keys for 8->9 (50% for 8->16 -- doubling
  is the special case). Consistent hashing moved 10.1%, ~the theoretical minimum.
virtual nodes: 1 vnode -> worst shard 2.14x ideal (90 vs 26,711 keys);
  150 vnodes -> 1.08x. That is why vnodes exist.
SHARDING COSTS: no cross-shard joins or transactions, no global AUTO_INCREMENT,
  no global UNIQUE, scatter-gather COUNT, painful ORDER BY/OFFSET, n-times ops.

CAP: Consistency (linearizability, NOT ACID's C) / Availability / Partition tolerance.
  "PICK TWO" IS THE MISREADING. P is not optional -- networks fail. The real
  statement: WHEN a partition happens, choose C (refuse) or A (serve stale).
  CA does not exist distributed; a single node is CA by not being distributed.
  CP: HBase, Zookeeper, etcd, MongoDB default.   AP: Cassandra, DynamoDB, Riak.
PACELC: if Partition -> A or C; Else -> Latency or Consistency. Covers normal operation.
QUORUM: W + R > N  =>  a read sees the latest write (the sets must overlap).
  N=3,W=2,R=2 strong.  N=3,W=1,R=1 eventual.  W=R=ceil((N+1)/2) is the usual balance.
BASE: Basically Available, Soft state, Eventually consistent. Eventual consistency
  is a GUARANTEE (convergence) with no time bound -- so always ask "eventually how long?"
READ-YOUR-OWN-WRITES is the anomaly that actually bites: user saves, is redirected,
  reads a lagging replica, sees the old value. Fix: sticky reads to the primary.

FOUR NOSQL FAMILIES
  key-value     key -> blob         sessions, cache, rate limits   Redis, DynamoDB
  document      key -> JSON         catalogues, profiles, CMS      MongoDB, Firestore
  column-family wide sparse rows    time series, event logs        Cassandra, HBase
  graph         nodes + edges       social, fraud, recommendations Neo4j, Neptune
  "schemaless" = schema-on-READ: the schema still exists, unenforced, in your app.
  graph is the ONE family with an asymptotic win, not just a scaling choice.

SQL vs NoSQL: relational is the DEFAULT (declared schema, joins, real transactions,
  ad-hoc queries). Go NoSQL for a specific misfit, name which family and why.
  It is not either/or -- most systems are relational + Redis + a search index.
  "NoSQL scales, SQL doesn't" is a decade out of date: Vitess, Citus, CockroachDB, Spanner.

DENORMALIZE only with: measured bottleneck, read-heavy, ONE writer or a reliable
  propagation path, tolerable divergence window, and a written repair path.
  Storing the price PAID is not denormalization -- it is a different fact.
CACHING patterns: cache-aside / write-through / write-behind. The hard part is
  INVALIDATION. Failure modes: cache stampede, thundering herd.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "We need scale, so NoSQL" | Scale is step 6 or 7. Indexes, a bigger box, a cache and read replicas come first, and one relational instance handles more than most people assume |
| "How would I scale it? Shard it." | Name the ordered ladder and say you would measure first. Sharding is the one-way door |
| "Read replicas scale writes" | They scale **reads**. Every write still goes to one primary, and the replicas add lag |
| "Replication and sharding are the same" | Replication **copies** the same data; sharding **splits** different data. Orthogonal axes, usually both used |
| "Vertical partitioning splits rows" | Columns. Horizontal splits rows |
| "A UNION ALL view gives me partitioning" | You get the split, not the **pruning**. Verified: SQLite scanned a partition that could not contain a match |
| "Any high-cardinality column works as a shard key" | It must also be **evenly distributed**. Verified: `tenant` had 20 values and still gave 3.87× skew, because one customer was 40% of the data |
| "My shards are balanced, so my shard key is fine" | Check the **write** distribution, not the stored distribution. Verified: a perfectly balanced 1.00× range shard took 100% of new writes on one shard |
| "Adding a shard moves 1/n of the data" | With naive `hash % n` it moved **88.7%** going from 8 to 9. Consistent hashing is what gets you near the minimum |
| "Consistent hashing alone distributes evenly" | Not without virtual nodes. Verified: 1 vnode gave 90 keys on one shard and 26,711 on another |
| "Sharding just needs a key and some routing" | It costs cross-shard joins, cross-shard transactions, global auto-increment, global uniqueness, cheap counts and easy pagination |
| "CAP says pick two of three" | P is not a choice — networks partition. The theorem is about what you give up **during** a partition: refuse requests or serve stale data |
| "We built a CA system" | Not if it is distributed. A single node is CA by virtue of not being distributed |
| "CAP's C is ACID's C" | CAP's C is linearizability — every read sees the latest write. ACID's C is constraint validity |
| "Eventually consistent means sometimes wrong" | It guarantees convergence with no time bound. The useful question is "eventually how long?" |
| "W=1, R=1 with 3 replicas is safe" | `W+R = 2 ≤ 3`, so a read can miss the latest write. Strong reads need `W+R > N` |
| "NoSQL has no schema" | It has an unenforced one — schema-on-read. Version 1 and version 7 documents coexist and every reader must handle both |
| "NoSQL is faster" | For the access pattern it was designed around. For an unanticipated query it is usually far worse, with no optimiser to help |
| "MongoDB has no transactions" | It has had multi-document transactions since 4.0. The older claim is out of date |
| "Denormalize for performance" | Only with a measured bottleneck, a read-heavy workload, one writer, a tolerable divergence window and a written repair path |
| "Storing the order's price duplicates the product price" | They are different facts — what was paid versus what it costs now. Not redundancy |
| "N+1 is a minor inefficiency" | It is 500 extra **round trips**. Invisible on localhost, 250 ms in production |

---

## Interview Q&A bank

**Q1. How would you scale a database that is struggling?**
Measure first — the most common "scaling problem" is a missing index. Then in order: fix the queries, scale the machine up, add a cache, add read replicas for read load, partition within the database, shard across machines, and only then change the data model. Each step is harder to reverse and gives up a guarantee, so stop at the first one that works.

**Q2. Vertical vs horizontal scaling?**
Vertical is a bigger machine: no code changes, instant, but it has a hard ceiling and a super-linear cost curve. Horizontal is more machines: significant code changes, essentially unlimited, and it is the only way to scale writes.

**Q3. What is the N+1 problem?**
An ORM loads a list in one query and then issues one more query per item. Verified: 501 queries instead of 1 for the same data. The real cost is the round trips — at 0.5 ms each that is 250 ms of pure waiting versus 0.5 ms — which is why it never shows up in local development.

**Q4. How do you detect and fix N+1?**
Detect it by counting queries per request, not by reading code. Fix it with eager loading, a single join, or batching the children into one `WHERE id IN (...)`, which turns N+1 into 2.

**Q5. Why is a large connection pool a bad idea?**
Each connection costs server memory, and a database has a throughput peak well below the connection count applications typically configure. A 500-connection pool on a database that peaks at 20 just relocates the queue from the pool into the database, where it is worse. Roughly `cores × 2` is the starting point.

**Q6. Vertical vs horizontal partitioning, and how is sharding different?**
Vertical splits a table's columns, horizontal splits its rows, and both can live in one database. Sharding is horizontal partitioning spread across separate machines. Replication is the orthogonal axis — copies of the same data.

**Q7. What does partitioning actually buy you?**
Pruning, so a query confined to one partition never touches the others; cheap bulk deletion via `DROP PARTITION` instead of a huge `DELETE`; and smaller per-partition indexes. The costs are that the partition key becomes very hard to change and queries that do not mention it get slower.

**Q8. Can I get partitioning by making a `UNION ALL` view over several tables?**
You get the split but not the pruning. Verified: with a predicate that no row in the older partition could satisfy, SQLite still scanned it. Real declarative partitioning knows each partition's bounds and skips it.

**Q9. How do you choose a shard key?**
It needs high cardinality and even distribution, and it should appear in the queries you run most, so they hit one shard. Verified over 200,000 rows: `user_id` gave 1.01× skew while `country` gave 5.60× with three shards completely empty, and `tenant` gave 3.87× because one customer was 40% of the data.

**Q10. My shards all hold the same amount of data. Is my shard key good?**
Not necessarily — check the **write** distribution. Verified: range sharding on a monotonically increasing id was perfectly balanced at 1.00× across the stored data while **every** new insert landed on a single shard.

**Q11. Range vs hash sharding?**
Range keeps adjacent keys together, so range queries are efficient, but it hot-spots on monotonic keys. Hash distributes evenly and automatically, but scatters range queries across every shard.

**Q12. What happens when you add a shard?**
With naive `hash(key) % n`, almost everything moves — verified, 88.7% of keys for 8 to 9 shards. Consistent hashing moves only the share the new node must own: 10.1% for the same change, against a theoretical minimum of 11.1%.

**Q13. Why does consistent hashing need virtual nodes?**
Because with one ring position per node the arcs are very uneven. Verified: one shard received 90 keys while another received 26,711, a worst case of 2.14× ideal. With 150 virtual nodes per physical node the worst case fell to 1.08×.

**Q14. What do you lose by sharding?**
Cross-shard joins and transactions, global auto-increment ids, global uniqueness constraints, cheap `COUNT(*)`, straightforward `ORDER BY ... LIMIT`, and operational simplicity, since migrations and backups now run per shard.

**Q15. Explain CAP.**
At most two of consistency, availability and partition tolerance. But "pick two" is a misreading: partitions are not a design choice, so P is mandatory for any distributed system. The real content is that **during** a partition you choose between refusing requests to stay consistent and answering from possibly stale data to stay available.

**Q16. So what is a CA system?**
A single-node system. It is CA by virtue of not being distributed, not by occupying a point on the triangle.

**Q17. Is CAP's C the same as ACID's C?**
No. CAP's C is linearizability — every read observes the most recent write. ACID's C is that constraints hold.

**Q18. What is PACELC?**
If there is a partition, choose availability or consistency; else, choose latency or consistency. It covers normal operation, which CAP says nothing about, and it is why a strongly-consistent store is slower even when nothing is broken.

**Q19. What does `W + R > N` mean?**
With `N` replicas, `W` write acknowledgements and `R` replicas read, if `W + R > N` the read set and write set must overlap in at least one node, so a read is guaranteed to see the latest write. `N=3, W=2, R=2` is strong; `N=3, W=1, R=1` is eventual.

**Q20. What is eventual consistency, and what should you ask about it?**
A guarantee that replicas converge once writes stop, with no bound on when. So the question to ask is "eventually how long?", because milliseconds of lag is invisible and thirty seconds is a bug report.

**Q21. Give the most common real problem caused by read replicas.**
Read-your-own-writes. A user saves a change to the primary, is redirected, reads from a lagging replica and sees the old value, concluding the save failed. Fix it with sticky reads to the primary for a short window after a write, or by routing a user's own data to the primary.

**Q22. ACID vs BASE?**
ACID guarantees atomic, consistent, isolated and durable transactions. BASE — basically available, soft state, eventually consistent — describes systems that trade immediate consistency for availability and latency, converging afterwards.

**Q23. Name the four NoSQL families with a use case each.**
Key–value for sessions and caches; document for heterogeneous items like catalogues and profiles; column-family for write-heavy time series and event logs; graph for deep traversals like social networks and fraud rings.

**Q24. When is NoSQL genuinely better rather than just different?**
A graph database for deep traversals — "friends of friends of friends" is three self-joins in SQL with exploding cost, while a graph store follows adjacency pointers. That is an asymptotic difference rather than a scaling preference.

**Q25. Is "schemaless" an advantage?**
It is schema-on-read rather than no schema: the structure still exists but is enforced by your application, so documents written in different versions coexist and every reader must handle all of them. Useful for genuinely irregular data and early iteration, and usually deferred pain otherwise.

**Q26. SQL or NoSQL for a new product?**
Relational by default — a declared schema, joins and real transactions prevent whole classes of bug, and SQL answers questions you did not foresee. Add a key–value store for sessions and caching. Reach for a different model only when a specific workload genuinely misfits, and name which family and why.

**Q27. "NoSQL scales and SQL doesn't" — respond.**
Out of date. Relational systems shard too — Vitess, Citus — and distributed SQL databases like CockroachDB and Spanner offer horizontal scaling with transactions. The trade-off today is about data model and consistency, not about whether scaling is possible.

**Q28. When is denormalizing the right call?**
When the join is a measured bottleneck, the workload is read-heavy, the redundant copy has a single writer or a reliable propagation path, you can tolerate the window where copies disagree, and you have written down how drift gets repaired. Anything less is just a future bug.

**Q29. Name the three caching write patterns and the main difficulty.**
Cache-aside, write-through and write-behind. The difficulty is invalidation, not the cache itself — and the two named failure modes are the cache stampede, when a hot key expires and every request hits the database at once, and the thundering herd after a cache restart.

---

## Practice

1. An API endpoint takes 1.8 s. The database shows 240 fast queries for that one request. Name the problem, the diagnostic that revealed it, and two fixes.
2. A read-heavy product has one Postgres instance at 80% CPU. Give the first four things you would try, in order, with a reason for each ordering decision.
3. You must shard a table of 500 million orders. Candidate keys: `order_id` (auto-increment), `user_id`, `created_at`, `country`, `status`. Rank them and justify the top choice and the worst.
4. Your shard key is `created_at` with range sharding. Capacity reports show all eight shards evenly filled. Why might the system still be in trouble, and how would you confirm it?
5. You run 8 shards with `hash(user_id) % 8` and need to add a ninth. Estimate how much data moves, and describe a migration that does not require downtime.
6. Why is 150 the kind of number people pick for virtual nodes, rather than 1 or 10,000?
7. A system is advertised as "CA". What has the author almost certainly got wrong, and what two questions would you ask?
8. With `N = 5`, give `(W, R)` for: (a) strong reads with the cheapest possible writes, (b) strong reads with the cheapest possible reads, (c) a balanced choice, (d) maximum availability regardless of staleness.
9. A user updates their avatar and the next page shows the old one. Explain the mechanism and give three fixes with their trade-offs.
10. Pick a data store and justify it for each: (a) 50 million IoT sensor readings per day, queried by device and time range; (b) shopping-cart sessions; (c) a bank's ledger; (d) "which accounts are within three transfers of this flagged one"; (e) a product catalogue where each category has entirely different attributes.
11. A colleague wants to store `comment_count` on the posts table instead of running `COUNT(*)`. Write the five conditions you would require, and say what you would do about the count drifting.
12. Explain why M7 recommends a sequential primary key while §10.3 warns against a monotonic shard key, and why both are right.

**Answers to 3, 4 and 12:**

> **3.** Best is **`user_id`**: high cardinality, roughly even (verified 1.01× skew), and most queries are "this user's orders", so they hit one shard. `order_id` is a close second for distribution under *hashing* but makes every user's order history a scatter-gather. Worst is **`status`** — a handful of values, massively skewed (verified 6.79×, with most shards empty); `country` is nearly as bad (5.60×). `created_at` is the trap: fine for distribution, catastrophic for write hot-spotting.
>
> **4.** Because an even *stored* distribution says nothing about the *write* distribution: with range sharding on time, every new row lands in the newest shard. Verified — a 1.00× balanced range shard took 100% of recent inserts on one shard. Confirm it by measuring writes per second and CPU **per shard**, not bytes stored per shard.
>
> **12.** They optimise different layers. M7's argument is about the **clustered index on one machine**: a sequential key appends to the right-hand edge of the B+ tree, avoiding page splits and keeping inserts local. §10.3's argument is about **distribution across machines**: a monotonic key sends every new row to one shard. Both hold simultaneously, and the usual resolution is a key that is *random across shards and sequential within one* — for example a Snowflake-style id whose high bits are time but which is hashed for routing, or a per-shard sequence.

---

## Exit checklist

```
[ ] I can give the seven-step scaling ladder in order and justify the ordering
[ ] I can compare vertical and horizontal scaling on six axes
[ ] I know horizontal is the only thing that scales WRITES
[ ] I can explain N+1, say why it hides on localhost, and give the round-trip numbers
[ ] I can say how to DETECT N+1 (count queries) and three ways to fix it
[ ] I can say why a big connection pool is harmful and roughly how to size one
[ ] I can distinguish vertical / horizontal partitioning / sharding / replication
[ ] I know what partitioning buys (pruning, DROP PARTITION, smaller indexes) and costs
[ ] I know a UNION ALL view does not give pruning, with the verified plan
[ ] I can state the two requirements for a shard key and cite the measured skew
[ ] I know an evenly filled set of shards can still have a 100%-write hot shard
[ ] I can compare range and hash sharding
[ ] I know naive modulo resharding moves ~89% of keys, and why 8->16 is special
[ ] I can explain consistent hashing and quote the 10% figure
[ ] I can explain why virtual nodes exist, with the 90-vs-26,711 case
[ ] I can list seven things sharding takes away from me
[ ] I can state CAP correctly AND explain why "pick two" is the misreading
[ ] I can say what a CA system really is
[ ] I know CAP's C is linearizability, not ACID's C
[ ] I can state PACELC and say what it adds
[ ] I can derive W + R > N and give strong and eventual examples
[ ] I can define eventual consistency as a guarantee and ask the right question of it
[ ] I can describe read-your-own-writes and three fixes
[ ] I can give ACID vs BASE
[ ] I can name the four NoSQL families with a product and a use case each
[ ] I can explain schema-on-read honestly
[ ] I can name the one family with an asymptotic advantage and why
[ ] I can deliver the SQL-vs-NoSQL answer with a default and named exceptions
[ ] I can rebut "NoSQL scales, SQL doesn't" with current examples
[ ] I can state the five conditions for denormalizing
[ ] I know why a historical price is not denormalization
[ ] I can name the three cache write patterns and the two failure modes
```

---

## Next

**Part 13: Consolidation.** The revision file: a one-page **SQL syntax sheet**; the **confusable-pairs master table** covering every "X vs Y" in the subject; a **numericals procedure sheet** (candidate keys, normal forms, lossless check, super-key counting, serializability, recovery lists, B+ tree height); **70 rapid-fire questions** with one-line answers; a **25-query drill bank** with every query executed and its real output; and the final exit checklist for the whole subject.
