# DBMS Placement Handbook — Part 13
# Consolidation: Revision Sheets, Rapid-Fire and the Query Drill Bank

**Part 13 · 2 hours per pass · Requires: everything**

---

## How to use this file

This is not a teaching file. It is what you read the night before, and the only file you read on the morning of an interview. Nothing here is new; everything is compressed.

Six sections, in the order you should use them:

| Section | Use it for | Time |
|---|---|---|
| §13.1 **SQL syntax sheet** | "How do I write a window function again?" | 10 min |
| §13.2 **Confusable pairs** | Every "X vs Y" in the subject, in one table | 25 min |
| §13.3 **Numericals procedures** | The seven computational questions, each as steps | 20 min |
| §13.4 **70 rapid-fire** | Self-test. Cover the right column | 30 min |
| §13.5 **25-query drill bank** | The SQL round. Every query executed | 45 min |
| §13.6 **Final exit checklist** | Am I done? | 10 min |

**The honest triage, if you have one day:** §13.3 and §13.5, then the Tier 1 rows of §13.2. Those three cover the written test and the SQL round, which is most of the marks.

**Every query in §13.5 was executed** (Python 3.12 `sqlite3`, SQLite 3.49.1) against the dataset printed at the top of that section, and every result shown is real output — including three places where the output is *not* what a candidate expects, which are called out rather than smoothed over.

---

## 13.1 SQL syntax sheet

```sql
-- ============ DDL
CREATE TABLE emp(
  eid     INTEGER PRIMARY KEY,
  name    TEXT NOT NULL,
  did     INTEGER,
  salary  INTEGER DEFAULT 30000 CHECK (salary > 0),
  hired   DATE,
  CONSTRAINT fk_dept FOREIGN KEY (did) REFERENCES dept(did)
            ON DELETE SET NULL ON UPDATE CASCADE
);
ALTER TABLE emp ADD COLUMN city TEXT;
ALTER TABLE emp RENAME COLUMN city TO location;
ALTER TABLE emp DROP COLUMN location;
ALTER TABLE emp ADD CONSTRAINT chk CHECK (...);   -- not in SQLite
DROP TABLE emp;              -- table gone
TRUNCATE TABLE emp;          -- rows gone, DDL, resets identity, no triggers
DELETE FROM emp WHERE ...;   -- rows gone, DML, rollback-able, fires triggers

CREATE INDEX idx_name      ON emp(name);
CREATE UNIQUE INDEX ...    ON emp(email);
CREATE INDEX idx_composite ON emp(did, salary DESC);   -- leftmost-prefix applies
CREATE INDEX idx_expr      ON emp(lower(name));        -- expression index
DROP INDEX idx_name;

CREATE VIEW v AS SELECT ... WITH CHECK OPTION;
CREATE MATERIALIZED VIEW mv AS SELECT ...;   -- Postgres/Oracle; not MySQL/SQLite
REFRESH MATERIALIZED VIEW mv;

-- ============ query skeleton, in LOGICAL execution order
SELECT   DISTINCT col, agg(col) AS a          -- 5. and 6.
FROM     t1 JOIN t2 ON t1.k = t2.k            -- 1.
WHERE    predicate                            -- 2.  (no aliases, no aggregates)
GROUP BY col                                  -- 3.
HAVING   agg(col) > 10                        -- 4.  (aggregates allowed)
ORDER BY a DESC, id                           -- 7.  (aliases allowed; add a tiebreak)
LIMIT    10 OFFSET 20;                        -- 8.

-- ============ joins
FROM a JOIN  b ON ...          -- inner: matches only
FROM a LEFT  JOIN b ON ...     -- + unmatched LEFT rows, NULL-padded
FROM a RIGHT JOIN b ON ...     -- + unmatched RIGHT rows
FROM a FULL  OUTER JOIN b ON ...
FROM a CROSS JOIN b            -- every pair
FROM a, b WHERE a.k = b.k      -- old-style inner join
FROM a NATURAL JOIN b          -- joins on ALL same-named columns: avoid
FROM emp e JOIN emp m ON e.manager_id = m.eid     -- self-join (needs aliases)
-- an outer-join filter belongs in ON, not WHERE:
FROM a LEFT JOIN b ON a.k = b.k AND b.x = 1       -- keeps unmatched a rows
FROM a LEFT JOIN b ON a.k = b.k WHERE b.x = 1     -- silently becomes an INNER join

-- ============ anti-join (4 ways; the first two are NULL-safe)
WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.k = a.k)
LEFT JOIN b ON b.k = a.k WHERE b.k IS NULL
WHERE a.k NOT IN (SELECT k FROM b WHERE k IS NOT NULL)   -- guard is REQUIRED
EXCEPT

-- ============ predicates and NULL
WHERE x BETWEEN 1 AND 10            -- inclusive both ends
WHERE x IN (1,2,3)                  -- NOT IN + a NULL in the list => no rows ever
WHERE name LIKE 'a%'   -- prefix: indexable      '%a' -- not indexable
WHERE x IS NULL / IS NOT NULL       -- never  x = NULL
COALESCE(x, 0)                      -- first non-NULL
NULLIF(a, b)                        -- NULL when a = b
CASE WHEN c1 THEN v1 WHEN c2 THEN v2 ELSE v3 END

-- ============ aggregates
COUNT(*)        -- all rows
COUNT(col)      -- non-NULL values only
COUNT(DISTINCT col)
SUM / AVG / MIN / MAX        -- all SKIP NULLs: AVG(col) != AVG(COALESCE(col,0))
GROUP_CONCAT(col, ',')       -- STRING_AGG in Postgres/SQL Server

-- ============ set operators  (need union-compatible SELECTs)
UNION          -- deduplicates: slower
UNION ALL      -- keeps duplicates: prefer when you know there are none
INTERSECT
EXCEPT         -- MINUS in Oracle

-- ============ CTE and recursive CTE
WITH high AS (SELECT * FROM emp WHERE salary > 80000),
     cnt  AS (SELECT did, COUNT(*) n FROM high GROUP BY did)
SELECT * FROM cnt;

WITH RECURSIVE sub(eid, name, lvl) AS (
    SELECT eid, name, 0 FROM emp WHERE manager_id IS NULL   -- anchor
  UNION ALL
    SELECT e.eid, e.name, s.lvl + 1                         -- recursive member
    FROM emp e JOIN sub s ON e.manager_id = s.eid
)
SELECT * FROM sub;

-- ============ window functions   (CANNOT appear in WHERE or HAVING)
ROW_NUMBER() OVER (PARTITION BY did ORDER BY salary DESC, eid)   -- 1,2,3,4 always
RANK()       OVER (ORDER BY salary DESC)   -- ties share, then SKIP:  1,2,2,4
DENSE_RANK() OVER (ORDER BY salary DESC)   -- ties share, no skip:    1,2,2,3
LAG(x, 1)  OVER (ORDER BY d)      LEAD(x, 1) OVER (ORDER BY d)
SUM(x) OVER (ORDER BY d ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) -- running
AVG(x) OVER (ORDER BY d ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)         -- moving
COUNT(*) OVER ()                  -- the whole result set
NTILE(4) OVER (ORDER BY salary)   -- quartiles
-- default frame is RANGE UNBOUNDED PRECEDING ... CURRENT ROW: ties are lumped
-- always give the window ORDER BY a unique tiebreaker

-- ============ DML, TCL, DCL
INSERT INTO t(a,b) VALUES (1,2), (3,4);
INSERT INTO t SELECT ... ;
UPDATE t SET a = a + 1 WHERE ...;          -- atomic read-modify-write: use this
DELETE FROM t WHERE ...;
BEGIN; SAVEPOINT sp; ROLLBACK TO sp; RELEASE sp; COMMIT; ROLLBACK;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SELECT ... FOR UPDATE;       -- pessimistic row lock
GRANT SELECT, INSERT ON t TO role;    REVOKE INSERT ON t FROM role;

-- ============ programmability
CREATE TRIGGER trg AFTER UPDATE OF bal ON acct
BEGIN INSERT INTO audit VALUES (old.id, old.bal, new.bal); END;
CREATE TRIGGER v_ins INSTEAD OF INSERT ON a_view BEGIN ... END;  -- writable view

-- ============ never build SQL by concatenation
cur.execute("SELECT * FROM users WHERE name = ?", (name,))   -- parameterized
EXPLAIN / EXPLAIN QUERY PLAN / EXPLAIN ANALYZE                -- read the plan
```

---

## 13.2 Confusable pairs — the master table

The whole subject's "X vs Y" questions. Cover the right column and work down.

| Pair | The distinction in one line |
|---|---|
| **DBMS vs RDBMS** | An RDBMS is a DBMS whose data model is relations with keys and constraints; every RDBMS is a DBMS, not conversely |
| **Schema vs instance** | Schema is the structure (rarely changes); instance is the data in it at a moment |
| **Logical vs physical data independence** | Logical: change the logical schema without touching applications (harder). Physical: change storage without touching the logical schema (easier) |
| **2-tier vs 3-tier** | 2-tier: client talks to the database. 3-tier: an application server sits between, so the DB is never exposed |
| **DDL vs DML vs DCL vs TCL** | Structure / contents / permissions / when changes become real |
| **Super key vs candidate key** | Candidate key is a **minimal** super key — remove any attribute and it stops identifying |
| **Candidate vs primary vs alternate key** | All candidates identify; you pick one as primary; the rest are alternates |
| **Primary key vs unique** | PK: one per table, no NULLs, usually clustered. UNIQUE: many allowed, NULLs permitted (one in SQL Server, many elsewhere) |
| **Composite vs compound key** | Used interchangeably in practice; if pressed, composite = multiple attributes as one key, compound = a key made of two keys |
| **Surrogate vs natural key** | Surrogate is a meaningless generated id (stable, narrow, no business meaning); natural carries meaning (readable, but changes) |
| **Foreign key vs referential integrity** | The FK is the declaration; referential integrity is the property it enforces |
| **`ON DELETE CASCADE` vs `SET NULL` vs `RESTRICT`** | Delete the children / orphan them with NULL / refuse the delete |
| **Entity vs entity set** | The thing vs the collection of things of that type — row vs table |
| **Weak vs strong entity** | A weak entity has no key of its own; it needs the owner's key plus a partial key, and total participation in an identifying relationship |
| **Cardinality ratio vs participation** | How many (1:1, 1:N, M:N) vs whether it is mandatory (total vs partial) |
| **Total vs partial participation** | Total = every entity must participate (double line) → `NOT NULL` on the FK |
| **Generalization vs specialization** | Bottom-up (merge similar entities into a parent) vs top-down (split a parent into subtypes) |
| **Aggregation vs generalization** | Aggregation treats a *relationship* as an entity; generalization is an is-a hierarchy |
| **Degree vs cardinality (relation)** | Degree = number of **columns**; cardinality = number of **rows** |
| **Trivial vs non-trivial FD** | X→Y is trivial when Y ⊆ X |
| **Partial vs transitive dependency** | Partial: a non-prime attribute depends on *part* of a candidate key (kills 2NF). Transitive: non-prime → non-prime (kills 3NF) |
| **Prime vs non-prime attribute** | Prime = appears in *some* candidate key |
| **2NF vs 3NF** | 2NF removes partial dependencies; 3NF also removes transitive ones |
| **3NF vs BCNF** | BCNF requires every determinant to be a super key; 3NF permits a violation when the dependent side is prime. 3NF is always dependency-preserving, BCNF may not be |
| **Lossless vs dependency-preserving** | Lossless: the join of the pieces returns exactly the original (non-negotiable). Dependency-preserving: every FD is checkable on one piece (sometimes impossible at BCNF) |
| **4NF vs BCNF** | 4NF additionally removes non-trivial multivalued dependencies |
| **Normalization vs denormalization** | Remove redundancy for write correctness vs reintroduce it deliberately for read speed |
| **`WHERE` vs `HAVING`** | `WHERE` filters rows before grouping (no aggregates); `HAVING` filters groups after (aggregates allowed) |
| **`COUNT(*)` vs `COUNT(col)`** | All rows vs non-NULL values of that column |
| **`UNION` vs `UNION ALL`** | Deduplicates (sort/hash cost) vs keeps everything (faster) |
| **`INTERSECT` vs `INNER JOIN`** | Set operation on whole rows vs matching on a condition, and a join can multiply rows |
| **`EXCEPT` vs `NOT IN` vs `NOT EXISTS`** | All three express anti-joins; `NOT IN` is the one broken by NULLs |
| **`IN` vs `EXISTS`** | `IN` compares against a value list, `EXISTS` tests for a row. On modern optimizers the plans usually converge; `EXISTS` is NULL-safe |
| **Correlated vs non-correlated subquery** | Correlated references the outer row, so conceptually it runs per row; non-correlated runs once |
| **Derived table vs CTE vs view** | Inline subquery in `FROM` / named inline block, reusable within the statement and able to recurse / a stored, named, reusable definition |
| **View vs materialized view** | Stored SQL re-run every time (always fresh, no speed gain) vs stored results (fast, stale, needs refresh) |
| **`DELETE` vs `TRUNCATE` vs `DROP`** | Rows with `WHERE`, logged, rollback-able, fires triggers / all rows, DDL, fast, resets identity, no triggers / the table itself |
| **Procedure vs function** | An action you `CALL` that can do DML and control transactions vs a value usable inside an expression |
| **`BEFORE` vs `AFTER` trigger** | Validate or modify and possibly veto vs react to a completed change |
| **Implicit vs explicit cursor** | Created by the engine for each statement vs declared, opened, fetched and closed by you |
| **`ROW_NUMBER` vs `RANK` vs `DENSE_RANK`** | 1,2,3,4 always / ties share then skip (1,2,2,4) / ties share, no gaps (1,2,2,3) |
| **`GROUP BY` vs window function** | `GROUP BY` collapses rows into one per group; a window keeps every row and adds a computed column |
| **`ROWS` vs `RANGE` frame** | `ROWS` counts physical rows; `RANGE` includes all peers with the same `ORDER BY` value. **`RANGE` is the default** |
| **Clustered vs non-clustered index** | Leaves *are* the rows (one per table) vs leaves hold a locator (an extra hop, many per table) |
| **Dense vs sparse index** | One entry per record vs one per block — the latter requires sorted data |
| **Primary vs secondary index** | On the ordering key of the file vs on any other attribute |
| **B-tree vs B+ tree** | Data pointers at every level vs only at the leaves, with the leaves linked — hence higher fan-out and cheap range scans |
| **B+ tree vs hash index** | Ranges, ordering and prefixes vs `O(1)` equality and nothing else |
| **Index scan vs index seek** | `SCAN` reads the whole index; `SEARCH`/seek navigates. Only the second is the win |
| **Covering index vs ordinary index** | Contains every column the query needs, so the table is never read |
| **Sargable vs non-sargable** | The indexed column appears bare and comparable vs wrapped in a function or arithmetic |
| **OLTP vs OLAP** | Many small read-write transactions, normalized, row store vs few huge analytical scans, denormalized/star, column store |
| **Row store vs column store** | Whole rows contiguous (fetch a record cheaply) vs whole columns contiguous (aggregate and compress cheaply) |
| **Atomicity vs consistency** | All-or-nothing vs constraints holding before and after |
| **Consistency (ACID) vs consistency (CAP)** | Constraints are valid vs every read sees the latest write (linearizability). Unrelated |
| **Isolation vs serializability** | Isolation is the property; serializability is its definition — equivalent to *some* serial order |
| **Conflict vs view serializability** | Testable in polynomial time by precedence graph vs strictly broader and NP-complete; blind writes separate them |
| **Recoverable vs cascadeless vs strict** | No committed transaction rests on undone work / no dirty **reads**, so no cascade / no dirty reads **or writes**, so rollback is a simple restore |
| **Dirty read vs non-repeatable read** | Reading **uncommitted** data vs reading two different **committed** values for the same row |
| **Non-repeatable read vs phantom** | The same **row** changed vs the same **range** gained or lost rows — the second needs a range lock |
| **Lost update vs dirty write** | Two read-modify-writes where one write disappears vs overwriting an uncommitted value |
| **Shared vs exclusive lock** | Many readers compatible vs incompatible with everything |
| **Basic vs strict vs rigorous vs conservative 2PL** | Two phases / exclusive locks held to commit / all locks held to commit / all locks taken up front (the only deadlock-free one) |
| **Optimistic vs pessimistic concurrency** | Proceed and check a version at write time, retrying vs lock at read time and make others wait |
| **Deadlock vs starvation** | A cycle where nobody can proceed vs one transaction repeatedly chosen as victim and never finishing |
| **Wait–die vs wound–wait** | Older waits and the **younger dies** (non-preemptive) vs the older **wounds** the younger (preemptive). Older has priority in both |
| **Deadlock detection vs prevention** | Let it happen, find the cycle, abort a victim (what databases do, because rollback is free) vs structure requests so it cannot occur (what an OS prefers) |
| **2PL vs timestamp ordering** | Lock-based, can deadlock, fewer aborts vs no locks, no deadlock, more aborts |
| **Snapshot isolation vs serializable** | Prevents all four classic anomalies but permits **write skew** |
| **MVCC vs locking** | Readers and writers never block each other, at the cost of version storage and cleanup vs mutual blocking with no garbage |
| **Undo vs redo** | Restore the before-image to erase uncommitted work vs re-apply the after-image to complete committed work |
| **Deferred vs immediate update** | Data changes only at commit (never needs undo, cannot exceed memory) vs as it happens (what real systems do) |
| **Steal vs no-steal, force vs no-force** | Uncommitted pages may be evicted (needs undo) vs may not; commit writes all pages (no redo) vs does not (needs redo). Real: steal/no-force |
| **WAL vs shadow paging** | Log the change before modifying in place vs copy-on-write pages plus an atomic page-table swap. WAL won on concurrency and locality |
| **Checkpoint vs commit** | A system-wide marker that bounds recovery work vs one transaction's durability point |
| **Relational algebra vs calculus** | Procedural (how) vs declarative (what); equal expressive power by Codd's theorem |
| **σ vs π** | Selects **rows** vs selects **columns** (and removes duplicates) |
| **Natural join vs theta join** | Equates all same-named attributes and keeps one copy vs an arbitrary condition keeping both |
| **Cartesian product vs join** | A join *is* `σ_condition(R × S)` |
| **Division vs `GROUP BY HAVING COUNT`** | The algebra operator for "related to **all**" vs its usual SQL implementation |
| **Vertical vs horizontal partitioning** | Split **columns** vs split **rows** |
| **Partitioning vs sharding** | Splitting data within one database vs across machines |
| **Partitioning vs replication** | Different data in different places vs the same data copied to several places |
| **Range vs hash sharding** | Efficient range queries but hot-spots on monotonic keys vs even distribution but scattered range queries |
| **Scale up vs scale out** | A bigger machine, no code change, hard ceiling vs more machines, code changes, the only way to scale writes |
| **Read replica vs shard** | Scales reads and adds lag vs scales writes and removes joins |
| **Strong vs eventual consistency** | Reads always see the latest write (`W+R>N`) vs replicas converge with no time bound |
| **CP vs AP** | During a partition, refuse requests to stay consistent vs serve possibly stale data to stay available |
| **CAP vs PACELC** | What you give up during a partition vs that **plus** latency-versus-consistency when there is no partition |
| **ACID vs BASE** | Transactional guarantees vs basically available, soft state, eventually consistent |
| **SQL vs NoSQL** | Declared schema, joins, mature multi-row transactions, ad-hoc queries vs flexible documents, built-in horizontal scaling, one planned access pattern |
| **Schema-on-write vs schema-on-read** | The database enforces the structure vs your application does, so versions coexist unenforced |
| **Cache-aside vs write-through vs write-behind** | App fills the cache on a miss / write both synchronously / write the cache and flush later |

---

## 13.3 Numericals procedure sheet

Seven computational question types. Each is a procedure, not an insight — follow the steps and the answer appears.

### A. Attribute closure `X⁺`

```
1. X+ := X
2. repeat: for every FD  L -> R  with  L subset of X+ ,  X+ := X+ union R
3. until nothing changes
```

### B. All candidate keys

```
1. Attributes appearing ONLY on the left of FDs (or in no FD)  -> must be in EVERY key.
   Call that set L. If L+ = R, then L is the ONLY candidate key. Stop.
2. Attributes appearing ONLY on the right -> in NO candidate key.
3. Otherwise extend L with combinations of the "both sides" attributes,
   smallest first; keep any whose closure is R; discard any that contains
   a smaller one already found (minimality).
```
*(This procedure was verified over 30,000 random FD sets with zero violations — M3.)*

### C. Highest normal form

```
1. Find all candidate keys (B).  2. Prime = attributes in any candidate key.
3. For each non-trivial FD  X -> Y  with  Y not subset of X:
      X is a super key?                    -> fine for BCNF
      else Y entirely prime?               -> fine for 3NF, violates BCNF
      else X a PROPER SUBSET of some key?  -> violates 2NF (partial dependency)
      else                                 -> violates 3NF (transitive dependency)
4. The answer is the highest form with no violation: BCNF > 3NF > 2NF > 1NF.
```

### D. Lossless join (binary decomposition)

```
R1, R2 is lossless  <=>  (R1 n R2) is a SUPER KEY of R1 or of R2
i.e. compute (R1 n R2)+ : it must contain all of R1, or all of R2.
For 3+ pieces: the chase/tableau method.
Dependency-preserving: project the FDs onto each piece; the union must imply
every original FD. Check with F+ on the projected set.
```

### E. Counting super keys

```
A super key is any attribute set that CONTAINS a whole candidate key.
One candidate key K over n attributes:   2^(n - |K|)
Several keys: inclusion-exclusion.
  |A u B| = 2^(n-|K1|) + 2^(n-|K2|) - 2^(n-|K1 u K2|)
```

### F. Conflict serializability

```
1. List conflicting pairs: DIFFERENT transactions, SAME item, at least one WRITE.
   (R-R never conflicts.)
2. Edge Ti -> Tj for each pair where Ti's operation comes FIRST.
3. Nodes are TRANSACTIONS. Acyclic  <=>  conflict serializable.
4. If acyclic, any topological order is an equivalent serial schedule.
DO NOT judge by how interleaved it looks -- draw the graph.
Recoverability, separately:
   irrecoverable: Tj reads from Ti and COMMITS before Ti
   cascadeless  : reads only committed values
   strict       : neither reads nor writes an uncommitted item
```

### G. Crash recovery lists

```
1. undo-list := the active list inside the LAST checkpoint record
2. scan forward:  <Ti start> -> add to undo-list
                  <Ti commit> -> move Ti to redo-list
                  <Ti abort>  -> remove (already rolled back at runtime)
3. REDO forward from the checkpoint (after-images of redo-list)
4. UNDO backward over the log (before-images of undo-list)
A transaction that committed BEFORE the checkpoint is in neither list.
An aborted transaction is in neither list.
Undo restores the BEFORE-IMAGE, not the original value.
```

### H. B+ tree order, height and block accesses

```
order n:        (n-1)*key + n*pointer  <=  block        -> n
leaf capacity:  (block - pointer) / (key + record_ptr)  -> L
leaves:         ceil(records / L)
height:         divide the leaf count by n repeatedly until 1; count levels
point lookup:   height + 1   (the +1 fetches the row; 0 if the index covers)
full scan:      total_records / records_per_block  block reads
Reference point: 4KB block, 8B key, 8B pointer -> n = 256, L = 255,
  and the height is 3 for anything from 100k to 10M records.
```

---

## 13.4 Seventy rapid-fire questions

Cover the right-hand column. One line each is enough; if you need two, you do not know it yet.

| # | Question | Answer |
|---|---|---|
| 1 | Why a DBMS over files? | Controlled redundancy, enforced integrity, concurrency control, recovery, ad-hoc querying, access control |
| 2 | Three-schema architecture? | Physical (storage), logical (whole-database structure), view (per-user subsets) — enabling data independence |
| 3 | Which data independence is harder? | Logical, because applications are written against the logical schema |
| 4 | Degree and cardinality? | Columns and rows |
| 5 | Candidate key? | A minimal super key |
| 6 | Why can't a PK be NULL? | It must identify a row; NULL means unknown, which cannot identify |
| 7 | PK vs UNIQUE? | One per table, no NULLs, usually clustered vs many, NULLs allowed |
| 8 | Surrogate key — why? | Stable, narrow and meaningless, so a business change never changes the key |
| 9 | `NULL = NULL`? | `UNKNOWN`, not true. Use `IS NULL` |
| 10 | Why does `NOT IN` with a NULL return nothing? | Every comparison becomes `UNKNOWN`, so no row qualifies |
| 11 | Four integrity constraints? | Domain, entity (PK), referential (FK), key (uniqueness) |
| 12 | Weak entity? | No key of its own; identified by the owner's key plus a partial key, with total participation |
| 13 | M:N in ER → tables? | A third table holding both foreign keys as a composite primary key |
| 14 | 1:1 → tables? | Merge into one table, or put the FK on the side with total participation and make it `UNIQUE` |
| 15 | Three anomalies? | Update (change one fact in many rows), insert (cannot record one fact without another), delete (removing one fact loses another) |
| 16 | 1NF? | Atomic values, no repeating groups |
| 17 | 2NF? | 1NF plus no partial dependency of a non-prime attribute on part of a key |
| 18 | 3NF? | 2NF plus no transitive dependency — no non-prime determining a non-prime |
| 19 | BCNF? | Every non-trivial determinant is a super key |
| 20 | A relation in 3NF but not BCNF? | `R(S,C,T)` with `SC→T`, `T→C`: keys `{SC},{ST}`; `T→C` has a non-super-key determinant but `C` is prime |
| 21 | Why not always BCNF? | BCNF may not be dependency-preserving; 3NF always is |
| 22 | Lossless-join test for two pieces? | The common attributes must be a super key of at least one piece |
| 23 | 4NF? | BCNF plus no non-trivial multivalued dependency |
| 24 | When is denormalizing right? | Measured bottleneck, read-heavy, one writer, tolerable divergence, written repair path |
| 25 | SQL logical execution order? | `FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT` |
| 26 | Why can't `WHERE` use a `SELECT` alias? | `WHERE` is evaluated before `SELECT`, so the alias does not exist yet |
| 27 | `WHERE` vs `HAVING`? | Rows before grouping vs groups after; only `HAVING` takes aggregates |
| 28 | `COUNT(*)` vs `COUNT(col)`? | All rows vs non-NULL values |
| 29 | Does `AVG` ignore NULLs? | Yes — `AVG(col)` and `AVG(COALESCE(col,0))` differ, and the divisor is the difference |
| 30 | `UNION` vs `UNION ALL`? | Deduplicates (costly) vs keeps duplicates (faster) |
| 31 | Inner vs left join? | Matches only vs matches plus unmatched left rows, NULL-padded |
| 32 | Filter on the right table of a left join — where? | In `ON`. In `WHERE` it silently becomes an inner join |
| 33 | Why avoid `NATURAL JOIN`? | It joins on every same-named column, so adding a column changes the result silently |
| 34 | Self-join use? | Comparing rows of one table — employee against manager, pairs within a group |
| 35 | Correlated subquery? | One that references the outer row, so conceptually it is evaluated per row |
| 36 | `IN` vs `EXISTS`? | Value list vs row test. Plans usually converge; `EXISTS` is NULL-safe |
| 37 | CTE vs derived table? | A CTE is named, reusable within the statement, and can be recursive |
| 38 | Recursive CTE parts? | An anchor member, `UNION ALL`, and a recursive member referencing the CTE |
| 39 | `GROUP BY` vs window function? | Collapses rows vs keeps every row and adds a column |
| 40 | `RANK` vs `DENSE_RANK`? | Ties share a rank and the next value skips vs no gap |
| 41 | Can a window function go in `WHERE`? | No — windows are computed after `WHERE`. Wrap it in a subquery or CTE |
| 42 | Default window frame? | `RANGE UNBOUNDED PRECEDING TO CURRENT ROW` — ties are lumped together, so use `ROWS` for a true running total |
| 43 | Nth highest salary? | `DENSE_RANK() = N` in a subquery, or `LIMIT N` descending then `MIN`, or the correlated-count form |
| 44 | Find duplicates? | `GROUP BY col HAVING COUNT(*) > 1` |
| 45 | Delete duplicates keeping one? | `DELETE WHERE id NOT IN (SELECT MIN(id) ... GROUP BY key)` |
| 46 | Consecutive rows? | The gap trick: group by `value − ROW_NUMBER()`, which is constant along a run |
| 47 | `DELETE` vs `TRUNCATE`? | DML with `WHERE`, logged, rollback-able, fires triggers, keeps the identity counter vs DDL, all rows, fast, resets it, no triggers |
| 48 | Which resets `AUTO_INCREMENT`? | `TRUNCATE` |
| 49 | Can `TRUNCATE` be rolled back? | In PostgreSQL and SQL Server yes; in MySQL and Oracle no, because DDL causes an implicit commit |
| 50 | Why use a view? | Security, simplification, logical data independence, backward compatibility |
| 51 | When is a view updatable? | When one view row maps to exactly one base-table row — broken by `DISTINCT`, `GROUP BY`, aggregates, windows, `UNION` |
| 52 | `WITH CHECK OPTION`? | Rejects writes through the view that would produce a row the view cannot see |
| 53 | Procedure vs function? | An action you `CALL` that can do DML and control transactions vs a value usable in an expression |
| 54 | Trigger, good and bad use? | Good: audit trails, invariants a `CHECK` cannot express. Bad: business logic, because it is invisible control flow |
| 55 | Prevent SQL injection? | Parameterized statements — the query is parsed before any value arrives, so input cannot change its structure |
| 56 | Why isn't escaping quotes enough? | A numeric field is interpolated unquoted, so `2 or 1=1` needs no quote |
| 57 | Can you parameterize a table name? | No — a placeholder is a value, never an identifier. Use a whitelist |
| 58 | Why B+ trees? | Node = one block, so hundreds of comparisons per read; no data pointers upstairs, so higher fan-out and a shorter tree; linked leaves, so range scans are sequential |
| 59 | Height for 1 million rows? | Three or four levels with a realistic fan-out — and a lookup is height + 1 block reads |
| 60 | Clustered vs non-clustered? | Leaves are the rows, one per table vs leaves hold a locator, an extra hop, many per table |
| 61 | Why only one clustered index? | It defines the physical row order, and rows have one order |
| 62 | Leftmost-prefix rule? | An index on `(a,b,c)` can be seeked on `a`, `(a,b)` or `(a,b,c)` — not on `b` alone |
| 63 | Covering index? | Contains every column the query needs, so the table is never touched |
| 64 | Why does a function on a column kill the index? | The index stores `col`, not `f(col)`, so there is no order to seek on |
| 65 | When does an index hurt? | Write-heavy tables, low-cardinality columns, small tables, stale statistics, buffer-pool competition |
| 66 | Explain ACID. | Atomicity (log + undo), consistency (constraints + your logic), isolation (locks/MVCC), durability (log forced at commit) |
| 67 | Four anomalies? | Lost update, dirty read, non-repeatable read, phantom |
| 68 | Isolation levels table? | Read uncommitted permits all three; read committed stops dirty reads; repeatable read also stops non-repeatable reads; serializable also stops phantoms |
| 69 | Why does 2PL still deadlock? | It constrains when locks may be acquired, not the order different transactions acquire them in |
| 70 | What is MVCC? | New versions instead of overwrites, so each transaction reads a snapshot; readers never block writers, at the cost of storing and cleaning old versions |

---

## 13.5 The 25-query drill bank

**Every query below was executed; every result is real output.** Work through them with the output covered — this is the single highest-value exercise in the handbook for the SQL round.

### The dataset

```
dept                              emp
did | dname       | city          eid | name  | did  | salary | manager_id | hired      | commission
----+-------------+------         ----+-------+------+--------+------------+------------+-----------
10  | Engineering | Pune          1   | Asha  | 10   | 90000  | NULL       | 2019-03-01 | NULL
20  | Sales       | Delhi         2   | Ravi  | 10   | 75000  | 1          | 2020-07-15 | 5000
30  | HR          | Pune          3   | Meera | 10   | 75000  | 1          | 2021-01-20 | NULL
40  | Research    | NULL          4   | Dev   | 20   | 60000  | 1          | 2020-11-05 | 8000
                                  5   | Sara  | 20   | 85000  | 4          | 2018-06-10 | NULL
login(uid, day)                   6   | Imran | 20   | 60000  | 4          | 2022-02-28 | 3000
 1: Mar 1,2,3,5                   7   | Nita  | 30   | 50000  | 1          | 2023-09-01 | NULL
 2: Mar 1,3                       8   | Omar  | NULL | 95000  | 1          | 2017-04-12 | NULL
 3: Mar 1,2,3,4
                                  sale(sid, cust, product, qty, amount, ts)
product(pname)                     A: pen 100 (Jan), book 400 (Jan), bag 900 (Feb)
 pen, book, bag                    B: pen 250 (Jan), book 800 (Feb)
                                   C: pen 50 (Feb), pen 150 (Mar)
dup(id, email, name)               D: bag 1800 (Mar)
 1 a@x.com, 2 b@x.com, 3 a@x.com, 4 c@x.com, 5 b@x.com, 6 a@x.com
```

Planted on purpose: **Omar has no department**, **Asha has no manager**, **Research has no employees**, five of eight commissions are NULL, and there are salary ties at 75000 and 60000.

---

**D1. Nth highest salary (N = 3) — three ways**

```sql
-- (a) window function: the one to write first
SELECT DISTINCT salary FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) r FROM emp
) WHERE r = 3;

-- (b) no window functions available
SELECT MIN(salary) FROM (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 3);

-- (c) correlated subquery: the classic
SELECT DISTINCT salary FROM emp e
WHERE 2 = (SELECT COUNT(DISTINCT salary) FROM emp e2 WHERE e2.salary > e.salary);
```

```
all three ->  salary = 85000
```

Three notes. Use `DENSE_RANK`, not `ROW_NUMBER` — with ties, `ROW_NUMBER` makes the "3rd highest" depend on an arbitrary tiebreak. Use `N−1` in form (c), which is the classic off-by-one. And if N exceeds the number of distinct salaries, (a) and (c) return no rows while (b) returns the lowest salary — a real behavioural difference worth mentioning.

**D2. Find duplicates**

```sql
SELECT email, COUNT(*) n FROM dup GROUP BY email HAVING COUNT(*) > 1 ORDER BY email;
```
```
email   | n
--------+--
a@x.com | 3
b@x.com | 2
```

**D3. Delete duplicates, keeping the lowest id**

```sql
DELETE FROM dup WHERE id NOT IN (SELECT MIN(id) FROM dup GROUP BY email);
```
```
id | email   | name
---+---------+-----
1  | a@x.com | Asha
2  | b@x.com | Ravi
4  | c@x.com | Dev
```
In **MySQL** this exact statement fails — you cannot select from the table you are deleting from in a subquery. Wrap it: `... NOT IN (SELECT id FROM (SELECT MIN(id) id FROM dup GROUP BY email) t)`.

**D4. Employees earning more than their manager**

```sql
SELECT e.name employee, e.salary, m.name manager, m.salary mgr_salary
FROM emp e JOIN emp m ON e.manager_id = m.eid
WHERE e.salary > m.salary;
```
```
employee | salary | manager | mgr_salary
---------+--------+---------+-----------
Sara     | 85000  | Dev     | 60000
Omar     | 95000  | Asha    | 90000
```
The inner join is correct here: Asha has no manager, so she cannot qualify.

**D5. Highest-paid employee per department, *with the name***

```sql
SELECT d.dname, e.name, e.salary FROM emp e JOIN dept d ON d.did = e.did
WHERE e.salary = (SELECT MAX(salary) FROM emp x WHERE x.did = e.did)
ORDER BY d.dname, e.name;
```
```
dname       | name | salary
------------+------+-------
Engineering | Asha | 90000
HR          | Nita | 50000
Sales       | Sara | 85000
```
**Two things in this output.** First, this is the query that `SELECT did, name, MAX(salary) ... GROUP BY did` gets wrong — that version returns an arbitrary name beside the maximum (verified in M4). Second, **Omar is missing**, because `x.did = e.did` is `UNKNOWN` when both are NULL. If departmentless employees should appear, use `x.did IS e.did` (SQLite/Postgres `IS NOT DISTINCT FROM`) or handle them separately.

**D6. Top 2 earners per department**

```sql
SELECT dname, name, salary FROM (
  SELECT d.dname, e.name, e.salary,
         DENSE_RANK() OVER (PARTITION BY e.did ORDER BY e.salary DESC) r
  FROM emp e JOIN dept d ON d.did = e.did
) WHERE r <= 2 ORDER BY dname, salary DESC, name;
```
```
dname       | name  | salary
------------+-------+-------
Engineering | Asha  | 90000
Engineering | Meera | 75000
Engineering | Ravi  | 75000
HR          | Nita  | 50000
Sales       | Sara  | 85000
Sales       | Dev   | 60000
Sales       | Imran | 60000
(7 rows)
```
**Seven rows for "top 2".** That is correct and it is the point: with `DENSE_RANK`, a tie at rank 2 returns three employees. Decide deliberately — `DENSE_RANK` for "everyone tied for the top 2 places", `ROW_NUMBER` for "exactly two rows per department, pick arbitrarily among ties".

**D7. Employees who manage nobody**

```sql
SELECT name FROM emp
WHERE eid NOT IN (SELECT manager_id FROM emp WHERE manager_id IS NOT NULL)
ORDER BY name;
```
```
Imran, Meera, Nita, Omar, Ravi, Sara    (6 rows)
```
The `IS NOT NULL` guard is **mandatory**: Asha's `manager_id` is NULL, and without the guard `NOT IN` returns zero rows (verified in M5).

**D8. Departments with no employees**

```sql
SELECT d.dname FROM dept d LEFT JOIN emp e ON e.did = d.did WHERE e.eid IS NULL;
```
```
Research
```
Equivalent: `WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.did = d.did)`, or `EXCEPT`, or a NULL-guarded `NOT IN`.

**D9. Employee count per department, including empty ones**

```sql
SELECT d.dname, COUNT(e.eid) n FROM dept d LEFT JOIN emp e ON e.did = d.did
GROUP BY d.did ORDER BY n DESC, d.dname;
```
```
dname       | n
------------+--
Engineering | 3
Sales       | 3
HR          | 1
Research    | 0
```
`COUNT(e.eid)` gives 0 for Research; `COUNT(*)` would give **1**, counting the NULL-padded row. That one-character difference is the most commonly failed detail in this query.

**D10. Running total**

```sql
SELECT name, hired, salary,
       SUM(salary) OVER (ORDER BY hired, eid
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) running
FROM emp ORDER BY hired;
```
```
name  | hired      | salary | running
------+------------+--------+--------
Omar  | 2017-04-12 | 95000  | 95000
Sara  | 2018-06-10 | 85000  | 180000
Asha  | 2019-03-01 | 90000  | 270000
Ravi  | 2020-07-15 | 75000  | 345000
Dev   | 2020-11-05 | 60000  | 405000
Meera | 2021-01-20 | 75000  | 480000
Imran | 2022-02-28 | 60000  | 540000
Nita  | 2023-09-01 | 50000  | 590000
```
`ROWS`, not the default `RANGE`: with `RANGE`, tied `ORDER BY` values all receive the same total.

**D11. Three-row moving average**

```sql
SELECT name, hired, salary,
       ROUND(AVG(salary) OVER (ORDER BY hired, eid
                               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),1) mov3
FROM emp ORDER BY hired;
```
```
Omar 95000.0 | Sara 90000.0 | Asha 90000.0 | Ravi 83333.3
Dev  75000.0 | Meera 70000.0 | Imran 65000.0 | Nita 61666.7
```
The first two rows average over fewer than three values — the frame is clipped, not NULL.

**D12. `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`**

```sql
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC, eid) rn,
       RANK()       OVER (ORDER BY salary DESC)      rk,
       DENSE_RANK() OVER (ORDER BY salary DESC)      dr
FROM emp ORDER BY salary DESC, eid;
```
```
name  | salary | rn | rk | dr
------+--------+----+----+---
Omar  | 95000  | 1  | 1  | 1
Asha  | 90000  | 2  | 2  | 2
Sara  | 85000  | 3  | 3  | 3
Ravi  | 75000  | 4  | 4  | 4
Meera | 75000  | 5  | 4  | 4
Dev   | 60000  | 6  | 6  | 5
Imran | 60000  | 7  | 6  | 5
Nita  | 50000  | 8  | 8  | 6
```
Memorise this table. `rk` jumps 4 → 6 and 6 → 8 (ties consume the ranks); `dr` never gaps; `rn` is always consecutive and therefore arbitrary among ties.

**D13. Salary against the department average, keeping every row**

```sql
SELECT name, salary, did,
       ROUND(AVG(salary) OVER (PARTITION BY did),1) dept_avg,
       CASE WHEN salary > AVG(salary) OVER (PARTITION BY did)
            THEN 'above' ELSE 'at/below' END flag
FROM emp ORDER BY did IS NULL, did, salary DESC;
```
```
name  | salary | did  | dept_avg | flag
------+--------+------+----------+---------
Asha  | 90000  | 10   | 80000.0  | above
Ravi  | 75000  | 10   | 80000.0  | at/below
Meera | 75000  | 10   | 80000.0  | at/below
Sara  | 85000  | 20   | 68333.3  | above
Dev   | 60000  | 20   | 68333.3  | at/below
Imran | 60000  | 20   | 68333.3  | at/below
Nita  | 50000  | 30   | 50000.0  | at/below
Omar  | 95000  | NULL | 95000.0  | at/below
```
`PARTITION BY did` groups all NULL `did` values together — windows treat NULLs as equal peers, unlike `=`. Omar forms his own partition of one.

**D14. The same, without window functions**

```sql
SELECT e.name, e.salary FROM emp e
WHERE e.salary > (SELECT AVG(salary) FROM emp x WHERE x.did IS e.did)
ORDER BY e.name;
```
```
Asha 90000 | Sara 85000
```
`IS` instead of `=` so the NULL department is handled. In standard SQL that is `IS NOT DISTINCT FROM`; MySQL spells it `<=>`.

**D15. Users with three or more consecutive days — the gap trick**

```sql
SELECT uid, COUNT(*) streak, MIN(day) from_day, MAX(day) to_day FROM (
  SELECT uid, day,
         JULIANDAY(day) - ROW_NUMBER() OVER (PARTITION BY uid ORDER BY day) grp
  FROM login
) GROUP BY uid, grp HAVING COUNT(*) >= 3 ORDER BY uid;
```
```
uid | streak | from_day   | to_day
----+--------+------------+-----------
1   | 3      | 2026-03-01 | 2026-03-03
3   | 4      | 2026-03-01 | 2026-03-04
```
**The single most reusable trick in this file.** Along a consecutive run, `value − ROW_NUMBER()` is constant, so it becomes a group key. User 1 logged in on the 1st, 2nd, 3rd and 5th and correctly yields a streak of 3, not 4.

**D16. Gaps: where the runs break**

```sql
SELECT uid, day prev_day, nxt next_day FROM (
  SELECT uid, day, LEAD(day) OVER (PARTITION BY uid ORDER BY day) nxt FROM login
) WHERE nxt IS NOT NULL AND JULIANDAY(nxt) - JULIANDAY(day) > 1 ORDER BY uid;
```
```
uid | prev_day   | next_day
----+------------+-----------
1   | 2026-03-03 | 2026-03-05
2   | 2026-03-01 | 2026-03-03
```

**D17. Pivot with `CASE`**

```sql
SELECT cust,
       SUM(CASE WHEN product='pen'  THEN amount ELSE 0 END) pen,
       SUM(CASE WHEN product='book' THEN amount ELSE 0 END) book,
       SUM(CASE WHEN product='bag'  THEN amount ELSE 0 END) bag,
       SUM(amount) total
FROM sale GROUP BY cust ORDER BY cust;
```
```
cust | pen | book | bag  | total
-----+-----+------+------+------
A    | 100 | 400  | 900  | 1400
B    | 250 | 800  | 0    | 1050
C    | 200 | 0    | 0    | 200
D    | 0   | 0    | 1800 | 1800
```
`SUM(CASE WHEN ...)` is the portable pivot and works in every engine. The columns must be known in advance — a dynamic pivot needs generated SQL, which is where the whitelist rule from M6 applies.

**D18. Month-over-month change with `LAG`**

```sql
SELECT m, total, LAG(total) OVER (ORDER BY m) prev,
       total - LAG(total) OVER (ORDER BY m) delta
FROM (SELECT SUBSTR(ts,1,7) m, SUM(amount) total FROM sale GROUP BY 1) ORDER BY m;
```
```
m       | total | prev | delta
--------+-------+------+------
2026-01 | 750   | NULL | NULL
2026-02 | 1750  | 750  | 1000
2026-03 | 1950  | 1750 | 200
```
The first row's `delta` is NULL, not 0. Use `LAG(total, 1, 0)` if you want zero.

**D19. Share of total**

```sql
SELECT product, SUM(amount) amt,
       ROUND(100.0 * SUM(amount) / (SELECT SUM(amount) FROM sale), 1) pct
FROM sale GROUP BY product ORDER BY amt DESC;
```
```
bag 2700 60.7 | book 1200 27.0 | pen 550 12.4
```
`100.0` and not `100`: integer division would give 0. The window alternative is `SUM(amount) OVER ()` as the denominator.

**D20. Median**

```sql
SELECT AVG(salary) median FROM (
  SELECT salary, ROW_NUMBER() OVER (ORDER BY salary) rn, COUNT(*) OVER () n FROM emp
) WHERE rn IN ((n+1)/2, (n+2)/2);
```
```
median = 75000.0
```
The two-index trick handles both parities: with an odd count both expressions pick the same row, and with an even count they pick the middle two and `AVG` splits them.

**D21. Mode — the most frequent value**

```sql
SELECT salary, COUNT(*) n FROM emp GROUP BY salary
HAVING COUNT(*) = (SELECT MAX(c) FROM (SELECT COUNT(*) c FROM emp GROUP BY salary));
```
```
salary | n
-------+--
60000  | 2
75000  | 2
```
Two rows, because the mode is genuinely not unique. `ORDER BY COUNT(*) DESC LIMIT 1` would have hidden that.

**D22. Customers who bought every product — relational division**

```sql
SELECT cust FROM sale WHERE product IN (SELECT pname FROM product)
GROUP BY cust HAVING COUNT(DISTINCT product) = (SELECT COUNT(*) FROM product);
```
```
cust = A
```
Both guards matter: `product IN (...)` stops unrelated purchases inflating the count, and `COUNT(DISTINCT ...)` stops repeat purchases of the same product doing it. Customer C bought `pen` twice and correctly does not qualify.

**D23. The management chain above one employee — recursive CTE, upwards**

```sql
WITH RECURSIVE chain(eid, name, manager_id, lvl) AS (
    SELECT eid, name, manager_id, 0 FROM emp WHERE name = 'Imran'
  UNION ALL
    SELECT e.eid, e.name, e.manager_id, c.lvl + 1
    FROM emp e JOIN chain c ON e.eid = c.manager_id
)
SELECT lvl, name FROM chain ORDER BY lvl;
```
```
lvl | name
----+------
0   | Imran
1   | Dev
2   | Asha
```
Walking **up**: join `e.eid = c.manager_id`.

**D24. The whole org tree under one employee — recursive CTE, downwards**

```sql
WITH RECURSIVE sub(eid, name, manager_id, lvl, path) AS (
    SELECT eid, name, manager_id, 0, name FROM emp WHERE name = 'Asha'
  UNION ALL
    SELECT e.eid, e.name, e.manager_id, s.lvl + 1, s.path || ' > ' || e.name
    FROM emp e JOIN sub s ON e.manager_id = s.eid
)
SELECT lvl, path FROM sub ORDER BY path;
```
```
lvl | path
----+-------------------
0   | Asha
1   | Asha > Dev
2   | Asha > Dev > Imran
2   | Asha > Dev > Sara
1   | Asha > Meera
1   | Asha > Nita
1   | Asha > Omar
1   | Asha > Ravi
```
Walking **down**: join `e.manager_id = s.eid` — the mirror image of D23. The accumulated `path` column is both useful output and the standard way to detect a cycle (stop if the new node already appears in the path).

**D25. NULL audit — the aggregate trap in one row**

```sql
SELECT COUNT(*) rows_, COUNT(commission) non_null_comm, SUM(commission) sum_comm,
       ROUND(AVG(commission),2) avg_over_nonnull,
       ROUND(AVG(COALESCE(commission,0)),2) avg_over_all
FROM emp;
```
```
rows_ | non_null_comm | sum_comm | avg_over_nonnull | avg_over_all
------+---------------+----------+------------------+-------------
8     | 3             | 16000    | 5333.33          | 2000.0
```
**`5333.33` versus `2000.0` for the same column.** `AVG` divides by the count of non-NULL values (3), not by the row count (8). Both are defensible answers to different questions — "the average commission among those who earn one" and "the average commission across all employees" — and silently returning the wrong one is the most common NULL bug in reporting SQL.

---

## 13.6 Final exit checklist for the subject

```
FOUNDATIONS
[ ] I can argue for a DBMS over files, and name its costs too
[ ] Three-schema architecture, and which data independence is harder
[ ] Key family: super -> candidate -> primary -> alternate -> composite -> surrogate -> foreign
[ ] I can count super keys with inclusion-exclusion
[ ] NULL: three-valued logic, the NOT IN trap, IS NULL, and NULL in aggregates
[ ] Four integrity constraints and all three referential actions
[ ] ER -> relational conversion for 1:1, 1:N, M:N, multivalued, weak, ISA
[ ] I can design a schema end to end and then attack my own design

NORMALIZATION
[ ] The three anomalies, each with a concrete example
[ ] Attribute closure, and all candidate keys mechanically
[ ] 1NF -> 2NF -> 3NF -> BCNF, each as the anomaly it kills
[ ] Partial vs transitive dependency
[ ] The lossless-join test, and dependency preservation
[ ] A 3NF-not-BCNF example, and why BCNF can lose a dependency
[ ] When denormalizing is correct -- all five conditions

SQL
[ ] Logical order of execution, and the five things it explains
[ ] WHERE vs HAVING; aggregates and NULL; the GROUP BY bare-column trap
[ ] Every join type, and ON vs WHERE on an outer join
[ ] Anti-joins four ways, and which are NULL-safe
[ ] Correlated vs non-correlated; IN vs EXISTS vs JOIN honestly
[ ] CTEs and recursive CTEs, both directions
[ ] Windows: the ranking trio, frames, ROWS vs RANGE, the unique tiebreaker
[ ] All 25 drills in 13.5, from memory
[ ] DELETE vs TRUNCATE vs DROP, all nine rows
[ ] Views: the four reasons, updatability, WITH CHECK OPTION, materialized
[ ] Procedures vs functions; triggers and when NOT to use one
[ ] SQL injection: an attack, the fix, and WHY the fix works

PERFORMANCE
[ ] Why B+ trees -- all three arguments, with the height numbers
[ ] Fan-out, leaf capacity and height from block/key/pointer sizes
[ ] Clustered vs non-clustered, and why only one clustered
[ ] Leftmost prefix, seek truncation, and the skip-scan exception
[ ] Covering indexes, and how SELECT * breaks one
[ ] SARGability, and six rewrites on sight
[ ] All five ways an index hurts, with the measured numbers
[ ] Reading a plan: SCAN vs SEARCH vs COVERING vs a sort
[ ] The three join algorithms and when each wins
[ ] The eight-step "my query is slow" procedure, in order

TRANSACTIONS
[ ] ACID with the enforcing mechanism for each letter
[ ] Precedence graphs, and that cycles -- not interleaving -- are the test
[ ] View serializability, blind writes, and why no engine implements it
[ ] Recoverable / cascadeless / strict, and that strictness makes undo correct
[ ] All four anomaly timelines, plus write skew
[ ] The isolation-levels table, and the real engine defaults
[ ] Lock compatibility; 2PL and its four variants; why it still deadlocks
[ ] Wait-for graphs, wait-die vs wound-wait, and why a DB detects where an OS prevents
[ ] Timestamp ordering and Thomas's write rule
[ ] MVCC: both "never blocks" guarantees, the costs, and why it is not serializable

RECOVERY AND THEORY
[ ] Steal/no-force, and why each implies a recovery pass
[ ] The WAL rule in one sentence; undo vs redo; why commit is cheap
[ ] Checkpoints, and redo/undo lists from any log
[ ] Shadow paging and the two reasons it lost
[ ] The six algebra primitives; pi is SELECT DISTINCT
[ ] Division, and both SQL forms with their guards
[ ] Translating SQL to an algebra tree, and predicate pushdown as an equivalence

SCALING
[ ] The seven-step scaling ladder, in order, with reasons
[ ] N+1: what it is, why it hides locally, how to detect it
[ ] Partitioning vs sharding vs replication
[ ] Shard key: cardinality, distribution, and the monotonic-key hot shard
[ ] Consistent hashing and why virtual nodes exist
[ ] Seven things sharding takes away
[ ] CAP stated correctly, and why "pick two" is the misreading
[ ] PACELC, W+R>N, eventual consistency, read-your-own-writes
[ ] The four NoSQL families, and the SQL-vs-NoSQL answer with a default
```

---

## Where this handbook sits

Four subjects are now done in this format, and they interlock deliberately:

| Handbook | What it gives this one |
|---|---|
| **DSA** | B+ trees (Part 11), hashing (Part 5), cycle detection for precedence and wait-for graphs (Part 14), heaps for top-N (Part 12) |
| **OOP** | Entity modelling — an ER diagram and a class diagram are the same skill (Part on relationships/UML) |
| **OS** | Synchronization and readers–writer locks (M4), deadlock and the Coffman conditions (M5), virtual memory and page replacement for the buffer pool (M7), journaling file systems for WAL (M8) |
| **DBMS** | The schema design, SQL, indexing and transaction reasoning that the system-design round builds on |

**The remaining gaps for a product-company SDE interview**, in the order they are worth doing: **Computer Networks** (same format, and the last of the four classic core subjects), then a **thin HLD/system-design handbook** — which this module's §10.3 and §10.4 already start. Aptitude needs volume practice rather than a handbook.

**And the standing advice for this subject specifically:** of everything here, the SQL round is what you will actually be tested on most often, and §13.5 is the file to re-run. Open a SQLite shell, retype the dataset, and write all 25 from memory. If you can do that, the round is yours.
