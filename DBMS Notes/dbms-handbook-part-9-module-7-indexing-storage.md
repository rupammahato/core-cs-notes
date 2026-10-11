# DBMS Placement Handbook — Part 9
# Module 7: Indexing and Storage

**Module 7 · 4 hours · Tier 1/2 · Requires: M1 (keys), M4 (queries). Links to DSA Part 11 (trees) and Part 5 (hashing)**

---

## Why this module matters

Every other module is about getting the *right* answer. This one is about getting it *fast*, and it is where a DBMS interview separates people who have used a database from people who have read about one.

Three questions carry the module, and they are asked almost verbatim:

- **"What is an index, and which data structure does it use — and why that one?"** (the B+ tree answer)
- **"Clustered vs non-clustered index."**
- **"When does an index make things worse?"** — the one that filters candidates, because it needs you to understand the cost side.

Behind them sits the open-ended favourite: **"a query is slow, what do you do?"** You need a procedure for that, not a guess.

The organising principle:

> **An index is a redundant, ordered copy of some columns, maintained automatically, that converts "look at every row" into "navigate to the rows". It is bought with disk space and write speed. It only pays off when the query is selective, and it can only be navigated when the predicate is expressed as a plain comparison on the indexed column in the order the index stores it.**

**How this module was verified.** The height and fan-out arithmetic is computed, not recalled. Every plan and every timing came from a real **200,000-row table** in SQLite 3.49.1 under Python 3.12, read with `EXPLAIN QUERY PLAN`. One of those results **contradicted the rule I was about to write down**, and §7.8 tells you what happened rather than hiding it.

A fair warning about engine scope: SQLite has no clustered-index concept in the SQL Server sense, no hash indexes and no hash joins. Those sections are therefore **marked as not executed** and explained from documentation and arithmetic. Everything else is real output.

---

## 7.1 How a table actually sits on disk

```
                         DISK
 +------------------------------------------------------+
 |  block (= page)  typically 4 KB or 8 KB              |  <- the unit of I/O.
 |  +------------+------------+------------+---------+  |     You never read one
 |  |  record 1  |  record 2  |  record 3  |   ...   |  |     row; you read the
 |  +------------+------------+------------+---------+  |     whole block it is in.
 +------------------------------------------------------+

 memory:  BUFFER POOL  <- blocks cached here. A hit costs ~nanoseconds,
                          a miss costs an I/O (~100 µs on SSD, ~10 ms on disk).
```

Three consequences that the whole module rests on:

1. **The block is the unit of cost.** Query cost is counted in *block accesses*, not rows. If 100 rows fit in a block, reading 100 rows costs 1 access, not 100.
2. **Sequential beats random.** Reading 1,000 consecutive blocks is far cheaper per block than 1,000 scattered ones. This is why a full scan sometimes beats an index that would need 1,000 random lookups.
3. **The buffer pool is the real performance story.** The same query is fast or slow depending on whether its blocks are cached — exactly like page faults in **OS M7**. The replacement policy is LRU-like for the same reason.

**Row store vs column store, in one paragraph.** A row store keeps a whole row contiguous, so fetching one complete record is one block read — right for OLTP, where queries touch few rows but many of their columns. A column store keeps each column contiguous, so `AVG(salary)` over 50 million rows reads only the salary column, and because neighbouring values are similar, compression is dramatic — right for OLAP/analytics. Classic relational engines are row stores; Redshift, BigQuery, ClickHouse and Parquet files are column stores. If an interviewer asks "why is an analytics warehouse columnar", that is the answer.

---

## 7.2 What an index is

```
  TABLE emp (unordered, as inserted)        INDEX on name (ordered copy)
  block 1 | Omar   95000 |                  name      -> pointer
          | Asha   90000 |                  ------------------------
  block 2 | Ravi   75000 |                  Asha      -> block 1, slot 2
          | Meera  75000 |                  Dev       -> block 3, slot 1
  block 3 | Dev    60000 |                  Imran     -> block 4, slot 1
          | Sara   85000 |                  Meera     -> block 2, slot 2
  block 4 | Imran  60000 |                  Nita      -> block 4, slot 2
          | Nita   50000 |                  Omar      -> block 1, slot 1
                                            Ravi      -> block 2, slot 1
                                            Sara      -> block 3, slot 2
```

Two facts follow immediately:

- The index is **sorted**, so it can be searched without reading it all. The table is not.
- The index is **narrow** — two columns instead of twelve — so far more entries fit in a block, so far fewer blocks need reading.

An index is not magic. It is the same trick as the back of a textbook: a sorted, smaller, redundant copy with pointers to the real content.

### Verified: what an index is actually worth

Same query, same 200,000-row table, before and after one `CREATE INDEX`:

```
BEFORE index:
  Q: select eid, name, salary from emp where name = ?
     -> SCAN emp
     time: 5.915 ms/query

AFTER create index idx_name on emp(name):
  Q: select eid, name, salary from emp where name = ?
     -> SEARCH emp USING INDEX idx_name (name=?)
     time: 0.002 ms/query   -> 2429x faster
```

Note the two words that matter in every plan you will read for the rest of your life:

- **`SCAN`** — read the whole thing.
- **`SEARCH`** — navigate to it.

Getting from `SCAN` to `SEARCH` is the entire job of indexing.

---

## 7.3 Why a B+ tree — and not a BST, and not a plain B-tree

This is the module's headline question. Build the answer in three steps.

### Step 1: why not a binary search tree?

A BST (or AVL, or red-black) makes **one comparison per node**, so a node holds one key. With one key per node, the node is *far* smaller than a disk block — you pay a whole block read to learn one comparison's worth of information.

Height for 1,000,000 keys, computed:

```
  1,000,000 records -> BST height ~ log2 =  20  vs B+ tree height 3
  1,000,000,000 records -> BST height ~ log2 = 30  vs B+ tree height 4
```

**20 block reads versus 3.** The BST is asymptotically fine — `O(log n)` either way — but the constant is the disk, and the disk is what you are paying. This is the single sentence to deliver: *"in-memory structures minimise comparisons; on-disk structures minimise block reads, so you want the fattest possible node — exactly one block wide."*

### Step 2: fan-out arithmetic (the numerical they set)

An internal node with `n` pointers holds `n − 1` keys, so:

```
  (n - 1) * key_size  +  n * pointer_size  <=  block_size
```

Verified for four standard exam configurations:

```
  block=4096B key=8B  ptr=8B  ->  order n = 256  (256 pointers, 255 keys)
  block=4096B key=16B ptr=8B  ->  order n = 171  (171 pointers, 170 keys)
  block=8192B key=8B  ptr=8B  ->  order n = 512  (512 pointers, 511 keys)
  block=1024B key=10B ptr=6B  ->  order n = 64   (64 pointers,  63 keys)
```

A leaf block holds `(block − next_pointer) / (key + record_pointer)` entries — 255 for the 4 KB / 8 B / 8 B case.

Now the height table, computed:

```
            1,000 records ->          4 leaf blocks, height 2, lookup = 2 + 1 = 3 reads
          100,000 records ->        393 leaf blocks, height 3, lookup = 3 + 1 = 4 reads
        1,000,000 records ->      3,922 leaf blocks, height 3, lookup = 3 + 1 = 4 reads
       10,000,000 records ->     39,216 leaf blocks, height 3, lookup = 3 + 1 = 4 reads
    1,000,000,000 records ->  3,921,569 leaf blocks, height 4, lookup = 4 + 1 = 5 reads
```

Stare at the middle three rows. **A hundredfold increase in data — 100,000 to 10,000,000 rows — did not change the height at all.** That is what a fan-out of 256 buys you: `log₂₅₆` grows so slowly that essentially every real table is 3 or 4 levels deep. And the top levels are so small and so hot that they live permanently in the buffer pool, so a "4-read" lookup is usually **one** actual disk read.

The procedure for the exam question:

> 1. `n` from `(n−1)·key + n·ptr ≤ block`.
> 2. Leaf capacity `L` from `(block − ptr) / (key + rec_ptr)`.
> 3. Leaves `= ⌈records / L⌉`.
> 4. Divide by `n` repeatedly until you reach 1; count the levels.
> 5. Point lookup `= height + 1` (the last read fetches the data row — unless the index is covering, §7.6).

And the comparison that makes the point:

```
  1,000,000 rows, 100 rows per block:
  full table scan      = 10,000 block reads
  B+ tree point lookup =      4 block reads
  ratio                =  2,500x fewer
```

### Step 3: why B+ and not B?

Both are multi-way balanced trees. The difference is where the data lives.

```
B-TREE: data pointers at EVERY level
                  [ 50* | 100* ]            * = also carries a record pointer
                 /      |       \
        [20*|35*]    [70*|85*]    [120*|150*]

B+ TREE: keys upstairs are signposts only; ALL data at the leaves,
         and the leaves are linked
                  [  50 | 100  ]
                 /      |       \
        [20|35|50] -> [70|85|100] -> [120|150|...]
        ^                                        ^
        +----- doubly linked list of leaves -----+
```

| | B-tree | B+ tree |
|---|---|---|
| Record pointers | At every node | **Leaves only** |
| Keys may repeat | No | Yes (a separator also appears in a leaf) |
| Internal node fan-out | Lower — each key drags a data pointer | **Higher** — keys and child pointers only |
| Height for the same data | Taller | **Shorter** |
| Point lookup | Can stop early, at any level | Always goes to a leaf |
| **Range scan** | Must traverse back up and down repeatedly | **Walk the linked leaves** — sequential |
| Full scan in key order | Awkward | Read the leaf list end to end |
| Used by real databases | Rarely | **Almost universally** |

So there are exactly **two** reasons, and you should give both:

1. **Higher fan-out, so a shorter tree.** Internal nodes carry no data pointers, so more keys fit per block.
2. **Range scans are a linked-list walk.** `WHERE salary BETWEEN 50000 AND 80000`, `ORDER BY`, `>`, `<`, `LIKE 'abc%'`, `GROUP BY` on the indexed column — all of those become "seek to the start, then follow the leaf chain". In a B-tree each next key may be anywhere in the tree.

A bonus third if pressed: **predictable performance**, since every lookup costs exactly the height — no early-exit variance, which matters for latency guarantees.

The DSA link is direct: this is your **multi-way tree** from DSA Part 11, sized so a node is one disk block, with the same intuition as the **trie's** wide nodes in Part 17.

---

## 7.4 Index taxonomy

```
                           INDEX
                             |
        +--------------------+--------------------+
        |                                         |
   by what it indexes                      by structure
        |                                         |
   primary  (on the ordering key)           B+ tree  (ordered, ranges OK)
   secondary(on any other column)           hash     (equality only)
   clustering(on a non-key ordering field)  bitmap   (low cardinality, OLAP)
        |
   dense (one entry per record) / sparse (one entry per block)
```

### Dense vs sparse

```
DENSE index on a sorted file         SPARSE index on the same file
one entry per RECORD                one entry per BLOCK

  10 -> r1    block 1: 10, 20        10 -> block 1
  20 -> r2                           30 -> block 2
  30 -> r3    block 2: 30, 40        50 -> block 3
  40 -> r4
  50 -> r5    block 3: 50, 60
  60 -> r6
```

| | Dense | Sparse |
|---|---|---|
| Entries | One per record | One per block |
| Size | Large | Small |
| Lookup | Direct | Find the largest key ≤ target, then scan within the block |
| Requires sorted data | No | **Yes** |
| Can index a non-key field | Yes | Not usefully |

A sparse index is only possible when the file is ordered by that field — which is why **you can have at most one sparse (primary/clustered) index per table**, and every other index must be dense. That is the structural reason behind the clustered-index rule in §7.5.

**Multilevel index:** if a sparse index is itself too big to search by scanning, build a sparse index *on the index*, and repeat. Do this to the fixed point and you have reinvented the B+ tree — which is a tidy way to introduce it in an interview.

### Hash index — and what it cannot do

**Not executed** — SQLite has no hash indexes. From documentation (MySQL `MEMORY`/`NDB`, PostgreSQL `USING hash`, and most key-value stores):

| | B+ tree index | Hash index |
|---|---|---|
| Equality `=` | ✅ `O(log n)` block reads | ✅ ~`O(1)`, usually 1 read |
| Range `<`, `>`, `BETWEEN` | ✅ | ❌ **Impossible** — hashing destroys order |
| `ORDER BY` from the index | ✅ | ❌ |
| `LIKE 'abc%'` | ✅ (prefix is a range) | ❌ |
| Leftmost-prefix of a composite | ✅ | ❌ — hashes the whole key |
| `MIN` / `MAX` shortcut | ✅ | ❌ |
| Behaviour as it fills | Graceful | Degrades on collisions; needs rehashing |

The one-liner: **a hash index is faster for exact lookups and useless for everything else**, which is why B+ trees are the default even though hashing has the better complexity. Your DSA Part 5 hashing module is the same structure; the database just cares about the ordering it threw away.

**Bitmap index** (Tier 3, one line): one bitmap per distinct value, so `WHERE gender='F' AND state='MH'` becomes a bitwise `AND`. Excellent for low-cardinality columns in a read-mostly warehouse, terrible under concurrent writes. Oracle and most column stores have them; MySQL and SQLite do not.

---

## 7.5 Clustered vs non-clustered

```
CLUSTERED INDEX                        NON-CLUSTERED (SECONDARY) INDEX
the leaves ARE the table rows          the leaves hold pointers to the rows

     [ 50 | 100 ]                          [ Dev | Nita ]
    /     |      \                        /      |       \
 [1:Asha][50:Ravi][100:Omar]       [Asha->rid7][Dev->rid3][Nita->rid1]
  ^ the row data is here                             |
                                                     v  extra hop
                                          the clustered index / heap
```

| | Clustered | Non-clustered |
|---|---|---|
| Leaf contains | **The row itself** | A key + a row locator |
| Reads per lookup | Height | Height **+ 1 hop** to fetch the row |
| How many per table | **Exactly one** | Many (dozens if you insist) |
| Physical row order | Defined by this index | Unrelated to it |
| Range scan | Excellent — rows are adjacent | Random I/O per row fetched |
| Extra storage | None — it *is* the table | A full copy of the indexed columns |
| Insert cost | Can cause page splits; random keys fragment | Appends to the index |

**Why only one?** Because clustering means *the rows are physically stored in this order*, and the rows can only be in one physical order at a time. Two clustered indexes would require two copies of the table. That is the whole answer, and it is a one-liner: **"a clustered index is not a copy of the data, it is the arrangement of the data — and data can only be arranged one way."**

By engine:

| Engine | Clustered by |
|---|---|
| **MySQL / InnoDB** | Always the primary key. No PK? It uses a `UNIQUE NOT NULL` column, else a hidden 6-byte rowid. Secondary indexes store the **PK value** as the locator, so every secondary lookup goes index → PK → clustered index |
| **SQL Server** | Optional — `CREATE CLUSTERED INDEX`. Without one the table is a *heap* and locators are physical `RID`s |
| **PostgreSQL** | **No clustered indexes.** All indexes are secondary; `CLUSTER table USING idx` physically reorders once and does not maintain it |
| **Oracle** | Heap by default; index-organized tables (IOT) are the clustered equivalent |
| **SQLite** | Rowid tables are clustered by the implicit `rowid`; `WITHOUT ROWID` clusters by the declared primary key |

### Verified: the clustered saving is real

Two tables, same 50,000 rows, same page size, on real files:

```
  rowid table (PK = separate index)
     pages=932    page_size=4096  file=3728 KiB   plan: SEARCH t USING INDEX sqlite_autoindex_t_1 (k=?)
  WITHOUT ROWID (PK index IS the table)
     pages=760    page_size=4096  file=3040 KiB   plan: SEARCH t USING PRIMARY KEY (k=?)
```

Two things in that output. The **file is 18% smaller** because the key is stored once instead of twice (once in the table, once in its automatic PK index). And the plan changes from `USING INDEX sqlite_autoindex_t_1` — a separate B-tree — to `USING PRIMARY KEY`, the table's own B-tree. That is clustered vs non-clustered, demonstrated at the storage layer.

**The practical consequence worth saying out loud:** in InnoDB, because secondary indexes store the primary key as the locator, a **wide primary key makes every index on the table bigger**. A 36-byte UUID primary key is copied into every secondary index of every row. That is the real argument for a narrow surrogate key (M1, §surrogate vs natural) — and random UUIDs also scatter inserts across the clustered index instead of appending, causing page splits. The usual answer is a `BIGINT` auto-increment, or a time-ordered UUIDv7 if you must have a UUID.

---

## 7.6 Composite indexes and the leftmost-prefix rule

An index on `(did, city, salary)` sorts by `did`, then within equal `did` by `city`, then by `salary` — like a phone book sorted by surname, then first name, then street.

```
  (did, city, salary)
   7, Bengaluru,  40000
   7, Bengaluru, 120000
   7, Delhi,      55000
   7, Pune,       95000
   8, Chennai,    60000     <- to find all 'Pune' rows you would have to look
   8, Pune,       72000        inside every did group: there is no single place
   9, Delhi,      48000        where the Pune entries live
```

You can seek with a **prefix** of the columns, left to right: `(did)`, `(did, city)`, `(did, city, salary)`. You cannot seek on `(city)` alone, because the `city` values are scattered across every `did` group — exactly like looking for everyone named "Ravi" in a phone book sorted by surname.

### Verified

```
  SEEK        1st only                SEARCH emp USING COVERING INDEX idx_dcs (did=?)
  SEEK        1st+2nd                 SEARCH emp USING COVERING INDEX idx_dcs (did=? AND city=?)
  SEEK        all three               SEARCH emp USING COVERING INDEX idx_dcs (did=? AND city=? AND salary>?)
  SEEK        1st+3rd (2nd skipped)   SEARCH emp USING COVERING INDEX idx_dcs (did=?)
```

Look closely at the fourth line. `WHERE did = 7 AND salary > 100000` used the index — **but only for `did = 7`**. The parenthesis says `(did=?)` and nothing about salary. The engine seeks to the `did = 7` block of the index and then filters every entry there for the salary condition. So a gap in the middle of the index does not make it useless; it **truncates** how much of it can be used for seeking. That distinction — "which columns did the plan actually seek on" — is the thing to read in a real `EXPLAIN`.

**Column order is therefore a design decision:**

| Rule | Why |
|---|---|
| Equality columns before range columns | `WHERE a = ? AND b > ?` wants `(a, b)`. With `(b, a)` the range on `b` ends the seek immediately |
| Most selective first — *only* among equalities | Fewer rows survive the first seek |
| Put the common query's columns leftmost | One index on `(a, b)` serves `a` and `a, b` — two indexes for the price of one |
| `(a, b)` makes a separate index on `a` redundant | …but **not** one on `b`. Drop the redundant one |

So `(a, b, c)` serves `a`, `(a,b)`, `(a,b,c)` — and does **not** serve `b`, `c`, or `(b,c)` by seeking.

### The honest version: skip-scan, and the rule my own output broke

While writing this section I ran `WHERE city = 'Pune'` against the `(did, city, salary)` index expecting a scan, and got this:

```
  SEEK  2nd only  SEARCH emp USING COVERING INDEX idx_dcs (ANY(did) AND city=?)
```

`ANY(did)` — the optimiser *did* seek, without the leading column. That is **skip-scan**: when the leading column has very few distinct values, the engine loops over each of them and does a separate seek for each. So the flat claim "the index cannot be used without its leading column" is, on a modern optimiser, not quite true.

I then isolated exactly when it happens — three tables, identical except for how many distinct values the leading column has:

```
leading column has ~50 distinct values
   before ANALYZE: SCAN t
   after  ANALYZE: SEARCH t USING COVERING INDEX ix (ANY(a) AND b=?)
   sqlite_stat1  : [('t', 'ix', '200000 4000 1334 4')]

leading column has ~20,000 distinct values
   before ANALYZE: SCAN t
   after  ANALYZE: SCAN t
   sqlite_stat1  : [('t', 'ix', '200000 11 4 1')]

leading column has ~200,000 distinct values
   before ANALYZE: SCAN t
   after  ANALYZE: SCAN t
```

Both conditions are required: **statistics must exist** (`ANALYZE` had been run, so `sqlite_stat1` shows ~4,000 rows per distinct leading value) **and the leading column must have low cardinality**. With 20,000 distinct values the optimiser went straight back to a scan, because 20,000 separate seeks is worse than reading the table once.

**How to answer the interview question.** Give the rule, then the nuance:

> *"An index can only be seeked on a leftmost prefix of its columns, so an index on `(a,b,c)` does not help a query filtering on `b` alone. The exception is skip-scan, which Oracle, MySQL 8.0.13+ and SQLite implement: if the leading column has very few distinct values, the optimiser can loop over them and seek once per value. It needs up-to-date statistics and low cardinality, so it is a fallback, not something to design around."*

That answer is strictly better than the textbook one, and the reason I can give it is that the output disagreed with what I was about to write.

### Covering index

An index **covers** a query when every column the query needs is in the index, so the table is never touched — the lookup saves the final `+1` read.

Verified:

```
  Q: select did, salary from emp where did = 7
     -> SEARCH emp USING COVERING INDEX idx_cover (did=?)

  Q: select did, salary, city from emp where did = 7
     -> SEARCH emp USING COVERING INDEX idx_dcs (did=?)
```

The word **`COVERING`** in the plan is the thing to look for. Adding one column to the `SELECT` list can silently remove it, turning an index-only read into index + table lookups for every matched row — which is why `SELECT *` is a genuine performance problem and not only a style complaint.

SQL Server and PostgreSQL let you add payload columns that are stored at the leaves but not sorted on (`INCLUDE (...)`), which gives covering without widening the search key.

---

## 7.7 SARGability: why a function on a column kills the index

**SARG** = Search ARGument. A predicate is **sargable** if the engine can turn it into a seek range on the indexed column. The rule has one cause:

> **An index stores `column`, not `f(column)`. The moment the column is wrapped in anything, the stored order no longer corresponds to the values being compared, so there is nothing to seek on — only to scan and test.**

Verified on a dedicated index on `salary`:

```
  SEEK        select eid from emp where salary = 100000
              SEARCH emp USING COVERING INDEX idx_salary (salary=?)
  INDEX-SCAN  select eid from emp where salary + 0 = 100000
              SCAN emp USING COVERING INDEX idx_salary
  INDEX-SCAN  select eid from emp where salary * 2 = 200000
              SCAN emp USING COVERING INDEX idx_salary
  SEEK        select eid from emp where salary = 200000 / 2
              SEARCH emp USING COVERING INDEX idx_salary (salary=?)
  INDEX-SCAN  select eid from emp where abs(salary) = 100000
              SCAN emp USING COVERING INDEX idx_salary
  SEEK        select eid from emp where salary between 100000 and 100500
              SEARCH emp USING COVERING INDEX idx_salary (salary>? AND salary<?)
  SEEK        select eid from emp where salary > 199000
              SEARCH emp USING COVERING INDEX idx_salary (salary>?)
```

Lines 3 and 4 are the pair to remember. `salary * 2 = 200000` and `salary = 200000 / 2` return **the same 568 rows**; one scans and one seeks:

```
   0.178 ms  select eid from emp where salary = 100000
   4.904 ms  select eid from emp where salary * 2 = 200000
   same rows? (568,) (568,)
```

**28× slower for an algebraically identical query.** The fix is always the same shape: **keep the column bare on one side and move the arithmetic to the other.**

### The sargable rewrite table

| Not sargable | Sargable rewrite |
|---|---|
| `WHERE salary * 12 = 600000` | `WHERE salary = 600000 / 12` |
| `WHERE YEAR(hired) = 2023` | `WHERE hired >= '2023-01-01' AND hired < '2024-01-01'` |
| `WHERE UPPER(name) = 'ASHA'` | Case-insensitive collation on the column, or an index on `UPPER(name)` |
| `WHERE SUBSTR(name,1,4) = 'emp1'` | `WHERE name >= 'emp1' AND name < 'emp2'` |
| `WHERE name LIKE '%asha%'` | Nothing — a leading wildcard is unindexable. Use full-text search |
| `WHERE DATEDIFF(day, hired, NOW()) < 30` | `WHERE hired > NOW() - INTERVAL 30 DAY` |
| `WHERE did + 0 = 7` (a real "disable the index" trick) | `WHERE did = 7` |
| `WHERE CAST(id AS TEXT) = '42'` | Fix the type on the other side: `WHERE id = 42` |

The prefix rewrite, verified:

```
  bad : SCAN emp USING COVERING INDEX idx_name          -- substr(name,1,4) = 'emp1'
  good: SEARCH emp USING COVERING INDEX idx_name (name>? AND name<?)
                                                         -- name >= 'emp1' and name < 'emp2'
```

### `LIKE` and the index

```
  INDEX-SCAN  select eid from emp where name like 'emp1500%'
  INDEX-SCAN  select eid from emp where name like '%150000'
  SEEK        select eid from emp where name glob 'emp1500*'
  SEEK        select eid from emp where name >= 'emp1500' and name < 'emp1501'
```

Two separate lessons here, and the first one is a SQLite specific worth labelling:

- **A trailing wildcard `'abc%'` is a range**, so it *should* seek — and it does under `GLOB`, and under the manual `>=`/`<` rewrite. It did **not** seek under `LIKE` because SQLite's default `LIKE` is **case-insensitive for ASCII**, while the index is built on a case-sensitive (`BINARY`) collation, so the index order does not match the comparison. Confirmed by flipping the pragma:

```
  with PRAGMA case_sensitive_like = ON:
  SEEK  select eid from emp where name like 'emp1500%'
        SEARCH emp USING COVERING INDEX idx_name (name>? AND name<?)
```

  The general lesson generalises beyond SQLite: **an index is only usable if its collation matches the comparison's collation.** In MySQL, a `utf8mb4_general_ci` column compared under a different collation, or joined to a column with another collation, loses its index the same way.

- **A leading wildcard `'%abc'` can never seek.** No rewrite exists, because the index is sorted by first character. That is what full-text indexes (`FTS5`, `MATCH`, GIN/trigram indexes) are for.

### Or index the expression

```
  Q: select eid from emp where lower(name) = 'emp150000'
     -> SEARCH emp USING COVERING INDEX idx_lower_name (<expr>=?)
```

`CREATE INDEX idx_lower_name ON emp(lower(name))` makes a non-sargable predicate sargable by storing exactly what the query asks for. SQLite, PostgreSQL and Oracle support expression indexes; MySQL 8.0.13+ does via functional key parts. The catch: the index is only used when the expression in the query **matches the indexed expression exactly**.

---

## 7.8 When an index makes things worse

The question that separates candidates. Five real costs:

### 1. Every write pays

Verified — the same 100,000 inserts with 0, 1, 2 and 3 secondary indexes:

```
  0 secondary indexes: 100,000 inserts in      71 ms   (1.00x)
  1 secondary indexes: 100,000 inserts in     105 ms   (1.48x)
  2 secondary indexes: 100,000 inserts in     151 ms   (2.14x)
  3 secondary indexes: 100,000 inserts in     203 ms   (2.88x)
```

Nearly linear in the number of indexes, and that is with everything in memory — on real storage, with each index's pages randomly scattered, it is worse. **An `INSERT` into a table with eight indexes is nine writes.** Every `UPDATE` of an indexed column is a delete-plus-insert in that index.

### 2. Low selectivity: the index is used and does not help

`active` has 2 distinct values over 200,000 rows:

```
  SEEK        select name from emp where active = 1
              SEARCH emp USING INDEX idx_active (active=?)

      47.52 ms  low cardinality (index exists)
      46.53 ms  forced to use idx_active
      42.34 ms  index forbidden (plain scan)
       0.004 ms  high cardinality, same index machinery
   rows matched: 99918 of 200000
```

Read that carefully, because it is better evidence than the usual hand-waving. The optimiser *chose* the index — and the plain scan was **faster** (42 ms vs 47 ms). Matching 99,918 of 200,000 rows means walking the index and then fetching half the table one row at a time, in index order rather than disk order. The index did nothing but add work, plus the write cost from (1), plus its disk footprint.

The same machinery on a high-cardinality column answered in **0.004 ms**. Identical structure, four orders of magnitude apart — **selectivity is the whole story.**

Rule of thumb: an index helps when the predicate selects roughly **under 5–10%** of the table. Past that, a sequential scan wins, because sequential I/O is cheap and random I/O is not.

### 3. The optimiser can choose wrongly

A stale or missing statistic makes the engine misjudge selectivity and pick the wrong plan. The §7.6 skip-scan result is the mirror image: `ANALYZE` *enabled* a better plan. Statistics are part of the index's cost — they have to be maintained (`ANALYZE`, `ANALYZE TABLE`, autovacuum).

### 4. Small tables

If the whole table is 3 blocks, a scan costs 3 reads and nothing can beat it. Indexes on small lookup tables are pure overhead. The optimiser usually knows, which is why `EXPLAIN` on a 10-row table often ignores your index — that is correct behaviour, not a bug.

### 5. Disk, memory and maintenance

An index on a wide column can approach the size of the table. Indexes compete for the **same buffer pool** as the data, so a useless index evicts useful pages. And in InnoDB every secondary index carries a copy of the primary key per entry (§7.5).

### The checklist to recite

```
Index when:            the column appears in WHERE / JOIN / ORDER BY / GROUP BY,
                       is selective, and the table is large and read-heavy
Do NOT index when:     low cardinality, small table, write-heavy table,
                       a column that is almost always wrapped in a function,
                       or a prefix already covered by an existing composite index
Then:                  measure with EXPLAIN. Drop indexes nothing uses --
                       an unused index is all cost and no benefit
```

---

## 7.9 Reading `EXPLAIN`, and what the optimiser does

### The vocabulary

| SQLite | MySQL | PostgreSQL | Meaning |
|---|---|---|---|
| `SCAN t` | `type: ALL` | `Seq Scan` | Read every row. Fine on a small table, a red flag on a large one |
| `SCAN t USING INDEX ix` | `type: index` | `Index Scan` (full) | Read the whole index. Narrower than the table, still not a seek |
| `SEARCH t USING INDEX ix (c=?)` | `type: ref` | `Index Scan` with a condition | **A seek.** What you want |
| `SEARCH ... USING COVERING INDEX` | `Extra: Using index` | `Index Only Scan` | Seek, and the table is never touched |
| `SEARCH t USING INTEGER PRIMARY KEY (rowid=?)` | `type: eq_ref` / `const` | `Index Scan` on the PK | Single-row lookup by key |
| `USE TEMP B-TREE FOR ORDER BY` | `Extra: Using filesort` | `Sort` | The sort could not be served by an index |
| `USE TEMP B-TREE FOR GROUP BY` | `Extra: Using temporary` | `HashAggregate` | Grouping needed a scratch structure |

What to check, in order: (1) is there a `SCAN` on a big table? (2) does the `SEARCH` seek on as many columns as you expected, or did the parenthesis stop early? (3) is `COVERING` there? (4) is there a sort or temp B-tree you could remove with an index?

### `ORDER BY` served by an index — verified

An index is sorted, so it can sometimes replace the sort entirely:

```
  no index:
     -> SCAN t
     -> USE TEMP B-TREE FOR ORDER BY            <- 50,000 rows sorted at query time

  with index on a:
     -> SCAN t USING COVERING INDEX ix_a        <- no sort step at all

  descending:
     -> SCAN t USING COVERING INDEX ix_a        <- a B+ tree leaf chain reads backwards too

  order by a, b with index on a only:
     -> SCAN t USING INDEX ix_a
     -> USE TEMP B-TREE FOR LAST TERM OF ORDER BY   <- partial help: 'a' free, 'b' sorted

  after index on (a, b):
     -> SCAN t USING COVERING INDEX ix_ab       <- fully served

  mixed directions, order by a ASC, b DESC on index (a, b):
     -> SCAN t USING COVERING INDEX ix_ab
     -> USE TEMP B-TREE FOR LAST TERM OF ORDER BY
```

Four facts in that output:

1. An index removes the sort — which is why `ORDER BY ... LIMIT 10` on an indexed column is nearly free: read the first 10 leaf entries and stop. (Without the index, you sort 50,000 rows to return 10 — compare the top-N discussion in **DSA Part 12**, heaps.)
2. **`DESC` is just as good** — leaves are doubly linked, so the chain reads backwards.
3. A partial match helps partially: "last term of ORDER BY" means `a` came free and only `b` needed sorting.
4. **Mixed directions break it.** `ORDER BY a ASC, b DESC` cannot be served by `(a, b)` ascending. The fix is an index declared `(a ASC, b DESC)`, which SQLite, PostgreSQL and MySQL 8.0+ all support.

### Join strategy — verified

```
  no index on emp.did:
     -> SEARCH d USING INTEGER PRIMARY KEY (rowid=?)
     -> SCAN e                                     <- 100,000 rows scanned per outer row

  with index on emp.did:
     -> SEARCH d USING INTEGER PRIMARY KEY (rowid=?)
     -> SEARCH e USING INDEX ix_emp_did (did=?)    <- seek instead

  no WHERE, whole join:
     -> SCAN e USING COVERING INDEX ix_emp_did
     -> SEARCH d USING INTEGER PRIMARY KEY (rowid=?)
     -> USE TEMP B-TREE FOR GROUP BY
```

Note in the third plan that the optimiser **reordered the tables** — it drives from `emp` and looks up `dept`, which is the opposite of the written order, because `dept`'s primary key makes it the cheaper inner side. That is join-order selection, visible in the plan.

**Honest scope note:** SQLite implements **only nested-loop joins** — verified, no hash or merge join exists in it. So the three join algorithms below are documented, not executed here:

| Algorithm | How | Best when |
|---|---|---|
| **Nested loop** | For each outer row, look up matches in the inner table | Outer side is small **and** the inner side is indexed on the join column. Without the index it is `O(n×m)` |
| **Hash join** | Build a hash table on the smaller input, probe with the larger | Large unsorted inputs, **equality** join only. Needs memory; spills to disk if it does not fit |
| **Sort-merge join** | Sort both inputs, walk them together | Inputs already sorted (e.g. both sides indexed), or very large; works for inequality joins |

Nested loop with an indexed inner side is the OLTP workhorse; hash join is the analytics workhorse. **MySQL had no hash join until 8.0.18** and used nested loop with a block buffer, which is why "add an index on the join column" is such reliable MySQL advice.

### What the optimiser does (four ideas, enough for an interview)

1. **Predicate pushdown** — apply filters as early as possible, so later stages handle fewer rows. (This is why the logical order of execution from M4 is *logical*: the engine is free to reorder as long as the result is identical.)
2. **Join reordering** — choose which table drives, using statistics. Seen above.
3. **Access-path selection** — scan, index seek, or index-only scan, costed per table.
4. **Cost-based decisions from statistics** — row counts, distinct values, histograms. Hence `ANALYZE`; hence the skip-scan result in §7.6 depending entirely on whether statistics existed.

### "Your query is slow. What do you do?" — the procedure

This is asked constantly. Have an ordered answer, not a list of tricks:

```
1. Measure. Which query, how slow, how often? Use the slow query log
   / pg_stat_statements. Do not optimise by guessing.
2. EXPLAIN it. Look for SCAN on a large table, a missing COVERING,
   a sort, a nested loop with an unindexed inner side.
3. Check the predicate is sargable (7.7). A function on the column is
   the single most common cause, and it is free to fix.
4. Check an index exists on what is filtered and joined; check the
   composite column order matches the query (7.6).
5. Check statistics are current -- ANALYZE.
6. Reduce what comes back: avoid SELECT *, so a covering index can work;
   paginate with a key, not a large OFFSET (M5).
7. Only then change the query shape: rewrite a correlated subquery as a
   join, split one monster query, materialize a repeated aggregate (M6).
8. Only then change the schema: denormalize deliberately (M3), partition,
   add a cache, add a read replica (M10).
```

The order matters more than the content: the cheap, reversible, measurable fixes come first, and schema surgery is last.

---

## Must remember

```
Cost is measured in BLOCK ACCESSES, not rows. Block = unit of I/O = 4-8 KB.
Sequential reads are cheap, random reads are not. That is why scans sometimes win.

Index = redundant sorted copy of some columns + pointers, maintained automatically.
SCAN = read it all.  SEARCH = seek.  Going SCAN -> SEARCH is the whole job.

Why B+ tree:
  not a BST: 1 key/node wastes a whole block read. 1M keys -> height 20 vs 3.
  higher fan-out than a B-tree (no data pointers upstairs) -> shorter tree
  leaves are LINKED -> range scans, ORDER BY, BETWEEN, prefix LIKE are sequential
  fan-out n from (n-1)*key + n*ptr <= block;  4KB/8B/8B -> n = 256
  height is 3-4 for anything from 100k to 10M rows. Point lookup = height + 1.

dense = one entry per record; sparse = one entry per block, needs sorted data,
  hence at most ONE sparse/clustered index per table
multilevel index taken to its limit IS a B+ tree
hash index: O(1) equality, USELESS for ranges / ORDER BY / prefix / leftmost-prefix

Clustered: leaves ARE the rows. One per table -- data has one physical order.
Non-clustered: leaves hold a locator; +1 hop. Many per table.
  InnoDB: always clustered by PK; secondary indexes store the PK as locator,
          so a wide PK bloats every index. Postgres has no clustered indexes.

Leftmost prefix: (a,b,c) can be SEEKED on a / (a,b) / (a,b,c). Not b, c, (b,c).
  a gap truncates the seek: WHERE a=? AND c>? seeks on a only, then filters
  equality columns before range columns in the index definition
  skip-scan is the real exception: needs statistics AND low leading cardinality
COVERING index = all needed columns in the index, table never touched. SELECT * kills it.

SARGable = the column appears bare, so the predicate becomes a seek range.
  f(col) = x  never seeks. Move the arithmetic to the other side.
  YEAR(d)=2023 -> d >= '2023-01-01' AND d < '2024-01-01'
  LIKE 'abc%' can seek (if collations match); LIKE '%abc' never can.
  collation mismatch disables an index just as surely as a function does.

When an index HURTS:
  every write pays (verified 2.9x for 3 indexes), low cardinality (verified the
  plain scan was FASTER), small tables, stale statistics, buffer-pool competition
  Rule of thumb: an index pays when the predicate selects < ~5-10% of rows.

Joins: nested loop (indexed inner side -> OLTP), hash (equality, big unsorted
  inputs -> analytics), sort-merge (pre-sorted or inequality).
Optimiser: predicate pushdown, join reordering, access-path choice, all cost-based
  from statistics -- which is why ANALYZE matters.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "Indexes make the database faster" | They make *selective reads* faster and *all writes* slower. Verified: 2.88× insert cost with three indexes |
| "Databases use B-trees" | B**+** trees. The difference — data only at the leaves, leaves linked — is exactly what makes range scans and `ORDER BY` cheap |
| "A BST would be fine, it's also O(log n)" | Same complexity, 20 block reads instead of 3. On-disk structures minimise *block reads*, not comparisons |
| "A B+ tree is deep for a big table" | Height 3 for 1 million rows and 4 for a billion. Verified arithmetic |
| "You can have several clustered indexes" | Exactly one: a clustered index *is* the physical order of the rows, and rows have one order |
| "Clustered and non-clustered are the same speed" | Non-clustered adds a hop per row to fetch the row, and that hop is random I/O |
| "An index on `(a,b,c)` helps a query on `b`" | Not by seeking — only a leftmost prefix can. The exception is skip-scan, which needs statistics and low leading cardinality |
| "I'll index every column, just in case" | Each one slows every write, consumes buffer pool, and may be chosen wrongly. Index what queries actually filter on |
| "An index on a flag column speeds up `WHERE active = 1`" | Verified: the index *was* used and the plain scan was faster. Matching half the table means a random fetch per row |
| "`WHERE salary * 2 = 200000` uses the index on salary" | Verified: full index scan, 28× slower than the identical `salary = 100000` |
| "`LIKE '%abc%'` can use an index if I add one" | A leading wildcard is unindexable in principle. That is what full-text search is for |
| "The optimiser always picks the best plan" | It picks the cheapest plan *according to its statistics*. Stale statistics give wrong plans — the skip-scan case flipped on `ANALYZE` alone |
| "Query tuning means rewriting the SQL" | Start with `EXPLAIN`, sargability and indexes. Rewriting comes seventh in the list, schema changes eighth |
| "A covering index is a special kind of index" | It is a *relationship* between an index and a query. The same index covers one query and not another — adding a column to `SELECT` can end it |

---

## Interview Q&A bank

**Q1. What is an index?**
A redundant, sorted copy of one or more columns together with pointers to the rows, maintained automatically by the database. It converts "examine every row" into "navigate to the rows", at the cost of disk space and slower writes.

**Q2. Which data structure, and why?**
A B+ tree. Nodes are sized to one disk block so each block read yields hundreds of comparisons instead of one; data pointers live only at the leaves, so internal nodes have a higher fan-out and the tree is shorter; and the leaves are linked, so range scans and `ORDER BY` are sequential walks.

**Q3. Why not a binary search tree or an AVL tree?**
Both minimise comparisons, which is the wrong cost model on disk. One key per node means paying a full block read per comparison: height 20 for a million keys against height 3 for a B+ tree.

**Q4. B-tree vs B+ tree?**
A B-tree stores record pointers at every level, so lookups can stop early but internal fan-out is lower and the tree is taller. A B+ tree keeps all data at the leaves and links them, giving higher fan-out, uniform lookup cost, and efficient range scans. Databases use B+ trees.

**Q5. Compute the height of a B+ tree for 10 million records, 4 KB blocks, 8-byte keys, 8-byte pointers.**
Fan-out: `(n−1)·8 + n·8 ≤ 4096` → `n = 256`. Leaf capacity: `(4096−8)/16 = 255`. Leaves `= ⌈10,000,000/255⌉ = 39,216`. Then `39,216 → 154 → 1`, so three levels. A point lookup is 3 index reads plus 1 data read.

**Q6. Dense vs sparse index?**
Dense has one entry per record and works on unsorted data; sparse has one entry per block, is much smaller, and requires the file to be sorted on that field — which is why a table can have at most one sparse index.

**Q7. Clustered vs non-clustered?**
A clustered index's leaves *are* the table rows, so there can be only one and range scans are sequential. A non-clustered index's leaves hold a locator, costing an extra hop per row; you can have many. InnoDB always clusters on the primary key; PostgreSQL has no clustered indexes at all.

**Q8. Why only one clustered index per table?**
Because it defines the physical order of the rows, and rows can only be stored in one order. Two would mean two copies of the table.

**Q9. Why does a wide primary key matter in MySQL?**
InnoDB stores the primary key value as the row locator inside every secondary index, so a 36-byte UUID primary key is duplicated into every index of every row — bloating all of them. Random UUIDs also scatter inserts in the clustered index and cause page splits.

**Q10. Leftmost-prefix rule?**
A composite index on `(a,b,c)` sorts by `a`, then `b`, then `c`, so it can be seeked on `a`, `(a,b)` or `(a,b,c)` — not on `b` alone, because `b` values are scattered across every `a` group. A gap truncates the seek: `WHERE a=? AND c>?` seeks on `a` and then filters.

**Q11. So an index on `(a,b,c)` is never usable for a filter on `b`?**
By seeking, no — except via skip-scan, where the optimiser loops over each distinct value of `a` and seeks once per value. Verified: it required both current statistics and a low-cardinality leading column; with 20,000 distinct leading values the optimiser went back to a table scan.

**Q12. How do you order columns in a composite index?**
Equality-filtered columns first, range-filtered last, because a range ends the seek. Among the equality columns, the most selective first. Match the ordering to the queries you actually run, and remember `(a,b)` already serves `a`.

**Q13. What is a covering index?**
One that contains every column a query needs, so the table is never read — the plan says `COVERING` / `Index Only Scan`. It is a property of the index-plus-query pair, so adding a column to the `SELECT` list can destroy it.

**Q14. What is SARGability?**
Whether a predicate can be converted into a seek range on an indexed column. Wrapping the column in a function or arithmetic breaks it, because the index stores `column`, not `f(column)`. Verified: `salary*2 = 200000` scanned and ran 28× slower than the identical `salary = 100000`.

**Q15. Make `WHERE YEAR(hired) = 2023` sargable.**
`WHERE hired >= '2023-01-01' AND hired < '2024-01-01'`. Or index the expression — `CREATE INDEX ... ON emp(YEAR(hired))` — but the query must then use that exact expression.

**Q16. When does an index make things worse?**
Five cases: write-heavy tables (verified 2.88× insert cost at three indexes); low-cardinality columns, where the index is used but a plain scan is faster (verified, 47 ms vs 42 ms, matching half the table); small tables; stale statistics causing bad plans; and buffer-pool competition that evicts useful pages.

**Q17. Roughly how selective does a predicate have to be?**
Under about 5–10% of the table. Beyond that, a sequential scan's cheap I/O beats one random fetch per matched row.

**Q18. Can an index remove a sort?**
Yes — an index is already sorted, so `ORDER BY` on its columns needs no sort step, and `DESC` works too because the leaves are doubly linked. Verified. It fails for mixed directions (`a ASC, b DESC`) unless the index itself is declared that way.

**Q19. Name the three join algorithms and when each wins.**
Nested loop — small outer side with an indexed inner side, the OLTP default. Hash join — large unsorted inputs, equality joins only, the analytics default. Sort-merge — inputs already sorted or very large, and it handles inequality joins.

**Q20. What does the optimiser actually do?**
Pushes predicates down so later stages see fewer rows, picks the join order, chooses an access path per table (scan / seek / index-only), and costs the alternatives using statistics. Which is why `ANALYZE` matters — a plan is only as good as the row-count estimates behind it.

**Q21. A query is slow. Walk me through it.**
Measure first and confirm it is actually this query. `EXPLAIN` it and look for a scan on a large table, a missing covering index, or a sort. Check the predicate is sargable. Check the right index exists and its column order matches. Refresh statistics. Reduce the data returned. Only then rewrite the query, and only last change the schema.

**Q22. How do you know an index is useless?**
Ask the engine which indexes have been used — `sys.schema_unused_indexes` in MySQL, `pg_stat_user_indexes.idx_scan = 0` in PostgreSQL. An index no query uses is pure cost: writes, disk and buffer pool for nothing.

---

## Practice

1. 4 KB blocks, 12-byte keys, 8-byte pointers, 2,000,000 records, 20-byte record pointers at the leaves. Compute fan-out, leaf capacity, number of leaves, height, and the block accesses for a point lookup.
2. Same table, 50 rows per block, no index. What does a point lookup cost? What does it cost once a B+ tree index exists? Express the saving as a ratio.
3. You have `INDEX(did, city, salary)`. For each of these, say whether it seeks, and on which columns: (a) `did=7 AND city='Pune'` (b) `city='Pune' AND salary>5` (c) `did=7 AND salary>5` (d) `did IN (1,2) AND city='Pune'` (e) `ORDER BY did, city`.
4. A table has `INDEX(a)`, `INDEX(a,b)` and `INDEX(b,a)`. Which one is redundant and why? Which of the remaining two serves `WHERE b = 5 ORDER BY a`?
5. `SELECT * FROM orders WHERE status = 'PENDING'` on 50 million rows, with 200 pending. Should `status` be indexed? What if 25 million were pending? What if the query also had `ORDER BY created_at LIMIT 20`?
6. Rewrite each to be sargable: (a) `WHERE MONTH(dob) = 5` (b) `WHERE salary/12 > 5000` (c) `WHERE CONCAT(first,' ',last) = 'Asha Rao'` (d) `WHERE CAST(user_id AS CHAR) = '42'`.
7. A write-heavy table has 11 indexes and 15 columns. You are asked to make inserts faster without losing query performance. What do you look at, in what order?
8. `EXPLAIN` shows `SCAN emp` then `USE TEMP B-TREE FOR ORDER BY` for `SELECT name, salary FROM emp WHERE did = 7 ORDER BY salary DESC LIMIT 10`. Give one index that fixes both lines and explain which of its properties fixes which.
9. Why is `ORDER BY ... LIMIT 10` on an indexed column nearly free, while the same query on an unindexed column costs a full sort? Connect it to heaps from DSA Part 12.
10. A join between two 10-million-row tables, no index on either join column, in MySQL 5.7 versus MySQL 8.0.18+. What is the difference, and what would you add either way?

**Answers to 3, 4 and 8** (the three worth checking):

> **3.** (a) seeks on `did` and `city`. (b) no seek by the leftmost-prefix rule; only skip-scan if `did` has few distinct values and statistics exist. (c) seeks on `did` only, then filters on salary. (d) seeks twice — once per value in the `IN` list — on `(did, city)`. (e) no filter at all, but the index is in exactly that order, so it serves the `ORDER BY` without a sort.
>
> **4.** `INDEX(a)` is redundant: `(a,b)` already serves every seek on `a` alone. `(b,a)` is not redundant, since nothing else can seek on `b`. For `WHERE b = 5 ORDER BY a`, `(b,a)` serves both — seek on `b = 5`, and within that the entries are already ordered by `a`, so no sort.
>
> **8.** `CREATE INDEX ON emp(did, salary DESC)` — or `(did, salary)`, since a B+ tree reads backwards. The leading `did` turns the `SCAN` into a `SEARCH`; having `salary` next means the matching entries are already in salary order, which removes the temp B-tree. Add `name` as a third column, or as an `INCLUDE`, and the index also covers the query so the table is never touched.

---

## Exit checklist

```
[ ] I can explain why cost is counted in block accesses, not rows
[ ] I can say in one sentence why an analytics store is columnar
[ ] I can define an index and name both of its costs
[ ] I can read SCAN vs SEARCH in a plan and say which one I want
[ ] I can give three reasons for B+ trees over BSTs with the height numbers
[ ] I can give the two reasons for B+ over B, including the leaf chain
[ ] I can compute fan-out, leaf capacity and height from block/key/pointer sizes
[ ] I can state why height stays 3-4 across 100k to 10M rows
[ ] I can explain dense vs sparse, and why that limits you to one sparse index
[ ] I can say that a multilevel index taken to the limit is a B+ tree
[ ] I can list what a hash index cannot do, and why
[ ] I can explain clustered vs non-clustered and why there is only one clustered
[ ] I can say what InnoDB stores as the locator and why a wide PK hurts
[ ] I can apply the leftmost-prefix rule to any predicate instantly
[ ] I know a gap TRUNCATES the seek rather than disabling the index
[ ] I can state the skip-scan exception and its two preconditions
[ ] I can order the columns of a composite index and justify it
[ ] I can define a covering index and say how SELECT * breaks it
[ ] I can explain SARGability from "the index stores col, not f(col)"
[ ] I can rewrite six non-sargable predicates on sight
[ ] I know why LIKE 'abc%' can seek and '%abc' can never
[ ] I know a collation mismatch disables an index like a function does
[ ] I can give all five ways an index makes things worse, with the numbers
[ ] I can state the 5-10% selectivity rule of thumb and why it exists
[ ] I can name the three join algorithms and when each wins
[ ] I can list the four things the optimiser does
[ ] I can deliver the 8-step "my query is slow" procedure in order
```

---

## Next

**Part 10: M8 — Transactions and Concurrency.** The third centrepiece and the heaviest Tier 1 module. **ACID properly** — each letter, what enforces it, what breaks without it; transaction states; serial vs concurrent schedules; **conflict serializability with precedence-graph numericals**; recoverable, cascadeless and strict schedules; **the four anomalies** — lost update, dirty read, non-repeatable read, phantom — each as an interleaving timeline; the **isolation levels × anomalies table**; lock compatibility; **2PL, strict and rigorous 2PL** and why basic 2PL still deadlocks; **deadlock in a DBMS** with the explicit contrast against OS M5; timestamp ordering; and **MVCC** — why readers do not block writers.
