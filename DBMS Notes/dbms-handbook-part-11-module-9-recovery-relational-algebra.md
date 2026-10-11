# DBMS Placement Handbook — Part 11
# Module 9: Recovery and Relational Algebra

**Module 9 · 3 hours · Tier 2 · Requires: M8 (transactions, strict schedules), M4 (SQL). Links to OS M8 (file systems, journaling)**

---

## Why this module matters

Two unrelated topics share this file because each is about half a day's work and neither carries a whole module.

**Recovery** is the other half of M8. M8 was about *isolation* — keeping concurrent transactions out of each other's way. This is about *atomicity and durability* — what happens when the power goes out. It is examined as one specific numerical, **"given this log, which transactions are redone and which are undone"**, plus one conceptual question, **"how does a database survive a crash mid-transaction?"** Both are completely learnable in an hour.

**Relational algebra** is the formal foundation under SQL. It appears in written tests and GATE as "translate this query", and it is where the optimiser's rewrites from M7 come from. Interviewers rarely ask it directly, but **division** — the "for all" operator — is the exception, because it is the one query shape most candidates cannot write in SQL.

The organising principle:

> **Recovery works because the log is written before the data, so the database always has enough information to finish what was committed and erase what was not. Relational algebra works because every SQL query is a tree of six primitive operators, which is exactly why a query can be rewritten into a faster but equivalent form.**

**How this module was verified.** Two toolkits:

1. **`recover.py`** — a log-based recovery simulator that computes the redo and undo lists by Korth's algorithm, then runs the redo and undo passes and compares the recovered state against the only possible correct answer: the effect of the committed transactions and nothing else. Tested on **20,000 random logs × 2 update policies = 40,000 recoveries.** It also produced a result I did not plan for, in §9.6.
2. **`ra.py`** — every relational-algebra operator implemented over sets of tuples, with **16 algebra expressions cross-checked against the equivalent SQL** executed in SQLite. All 16 match. Division is checked three separate ways.

Plus a **real crash**: a child process that physically wrote uncommitted data into the database file and then died, verified byte-by-byte before and after recovery.

---

## 9.1 Why a log has to exist

The answer is not obvious until you see where the data actually is. From M7: the database reads and writes **pages through a buffer pool** in memory. Two policies decide what the recovery manager must handle:

| Policy | Meaning | Consequence |
|---|---|---|
| **Steal** | A dirty page of an *uncommitted* transaction may be written to disk (because the buffer pool needs the frame) | Uncommitted data reaches the disk ⟹ **UNDO is required** |
| **No-steal** | Never write an uncommitted page | No undo needed, but the buffer pool must hold every uncommitted page |
| **Force** | All of a transaction's pages are written to disk at commit | No redo needed, but commit becomes slow and random |
| **No-force** | Commit does not write the data pages | Committed data may not be on disk ⟹ **REDO is required** |

Real databases use **steal / no-force**, because it is the only combination that performs. And steal/no-force is exactly the combination that needs **both undo and redo**. That is the whole reason this module exists.

### Verified: uncommitted data really does reach the disk

To prove the "steal" half rather than assert it, I ran a child process with a deliberately tiny page cache (`PRAGMA cache_size = 8`), updated 3,000 rows inside a transaction so the dirty pages could not all fit, and killed the process with `os._exit(1)` — no commit, no cleanup.

```
baseline db: {'m9b.db': 692224}   contains b'DIRTY'? False

   child: 3000 rows updated inside the transaction; cache too small to hold
   child: them, so dirty pages were already written INTO the db file.
   child: dying now, with no COMMIT.

after the crash, BEFORE anyone reopens the database:
  files: {'m9b.db': 692224, 'm9b.db-journal': 718352}
  db file contains b'DIRTY'?     True  <- uncommitted data IS in the db file
  db file contains b'ORIGINAL'?  True
```

Read the raw bytes line again. **The string `DIRTY` was physically inside the database file, from a transaction that never committed.** If the database were simply reopened and trusted, it would serve that data forever. The journal file sitting next to it — 718 KB of before-images — is the only thing standing between that and corruption.

```
now a new connection opens it -- SQLite finds the hot journal and replays it:
  first query: (3000, 'ORIGINAL')
  files after recovery: {'m9b.db': 692224}
  db file contains b'DIRTY'?     False  <- undone
  db file contains b'ORIGINAL'?  True
```

The journal was replayed, the file was deleted, and the raw bytes no longer contain `DIRTY` anywhere. That is atomicity, implemented, and visible at the byte level.

### The two journal files, verified

```
=== rollback journal mode: the journal appears only during a transaction ===
 idle           : {'m9.db': 118784}
 mid-transaction: {'m9.db': 118784, 'm9.db-journal': 66176}  <- BEFORE images (undo)
 after commit   : {'m9.db': 118784}  <- journal deleted; the change is in the db file

=== WAL mode: new pages go to the -wal file FIRST ===
 journal_mode -> wal
 after inserts   : {'m9.db': 4096, 'm9.db-wal': 2286632}  <- AFTER images (redo)
 wal frames      : (0, 555, 555)
 after checkpoint: {'m9.db': 118784, 'm9.db-wal': 2286632}  <- db file now holds them
```

Two different strategies, visible as two different files, and the contrast is the clearest way to understand undo versus redo:

- **Rollback journal**: write the **old** values aside, then modify the database file in place. To abort, copy the old values back. This is an **undo** log.
- **WAL**: leave the database file alone and write the **new** pages into a separate log. To commit, just record that the log is valid; readers consult the log first. This is a **redo** log, and a checkpoint is what copies the pages back into the main file.

Note in the WAL run that the database file was still **4096 bytes — one page** after 500 inserts. All the data was in the `-wal` file. That is also why WAL mode made readers and writers stop blocking each other in M8 §8.13: the writer appends to the log while readers keep reading the untouched main file.

---

## 9.2 Write-ahead logging

**The WAL rule, and it is the single most important sentence in this module:**

> **The log record describing a change must reach stable storage *before* the changed data page does, and all of a transaction's log records must reach stable storage *before* the commit is acknowledged.**

Everything else is bookkeeping. If the log is always ahead of the data, then after any crash the log contains enough information to finish or erase every transaction, whatever state the data pages are in.

### Log record format

```
  <T1, start>
  <T1, A, 100, 150>        transaction, item, OLD value (before-image),
                                              NEW value (after-image)
  <T1, commit>
  <T1, abort>
  <checkpoint, {T2, T3}>   the list of transactions ACTIVE at the checkpoint
```

The before-image enables **undo**; the after-image enables **redo**. A log carrying both supports steal/no-force, which is why real log records carry both.

| | What it does | Needs | Used for |
|---|---|---|---|
| **UNDO** | Restore the **before**-image | Old value | Erasing an uncommitted transaction |
| **REDO** | Re-apply the **after**-image | New value | Finishing a committed transaction whose pages never reached disk |

**Why commit is cheap:** a commit writes a tiny sequential log record and forces it to disk. It does *not* write the data pages, which may be scattered all over the file. Sequential, small and one I/O versus random, large and many — that is why no-force is worth the cost of needing redo. The same argument, in the same words, is why a **journaling file system** writes its journal before its metadata in **OS M8**.

### Idempotence

Recovery must survive crashing *during recovery*. Both passes are therefore written to be **idempotent**: redoing "set A = 150" twice leaves A = 150, and undoing "restore A = 100" twice leaves A = 100. This is why log records store **values rather than operations** — "A = 150" is idempotent, "add 50 to A" is not.

---

## 9.3 Deferred vs immediate update

Two policies for when the modification reaches the database.

| | **Deferred update** (NO-UNDO/REDO) | **Immediate update** (UNDO/REDO) |
|---|---|---|
| When the data page changes | Only **after** commit | As soon as the operation runs |
| Log needs before-images | ❌ No | ✅ Yes |
| Recovery needs UNDO | ❌ **Never** — uncommitted work never reached the DB | ✅ Yes |
| Recovery needs REDO | ✅ Yes | ✅ Yes |
| Buffer pool | Must hold all of a transaction's updates | No constraint |
| Long transactions | Cannot (runs out of memory) | Fine |
| Used in practice | No | **Yes** |

Deferred update is simpler and is why it is taught, but it cannot support a transaction larger than memory, so nothing real uses it. **The verified traces below are run under both policies**, which makes the difference concrete: the recovered state is identical, but the *state at the crash* differs, and only immediate update ever needs the undo pass to do anything.

---

## 9.4 Checkpoints

Without checkpoints, recovery would have to scan the log back to the beginning of time. A **checkpoint** writes a marker that bounds the work:

```
  1. Stop accepting new transactions momentarily.
  2. Force all log records in memory out to the log.
  3. Force all dirty buffer pages out to the database.
  4. Write <checkpoint, {list of currently active transactions}> and force it.
```

After step 3, every transaction that committed before the checkpoint is **known to be on disk**, so it can never need redo. Recovery therefore starts at the last checkpoint, not at the start of the log.

A **fuzzy checkpoint** avoids the stall in step 1 by letting the system keep running while the dirty pages trickle out, recording where the checkpoint began. Real systems do this; name it and move on.

The cost trade-off, worth a sentence: **frequent checkpoints make recovery fast and normal operation slower** (all those forced writes); rare checkpoints do the reverse. The tuning knob is "how long may recovery take", because that is the downtime after a crash.

---

## 9.5 The recovery algorithm, with verified traces

### The procedure

> **Analysis pass** — scan forward from the last checkpoint:
> - `undo-list` := the transactions listed as active in the checkpoint record
> - on `<Ti, start>` → add Ti to `undo-list`
> - on `<Ti, commit>` → move Ti from `undo-list` to `redo-list`
> - on `<Ti, abort>` → remove Ti from `undo-list` (it was already rolled back at runtime)
>
> At the end: `redo-list` = committed, `undo-list` = in flight at the crash.
>
> **Redo pass** — scan **forward** from the checkpoint, re-applying the after-image of every write by a transaction in `redo-list`.
>
> **Undo pass** — scan **backward** over the log, restoring the before-image of every write by a transaction in `undo-list`.

Three details that get marks:

- **Redo forward, undo backward.** Redo must replay in original order so the last write wins; undo must unwind in reverse so the earliest before-image is restored last.
- **Redo runs before undo** in this (classical) algorithm: first bring the database to the state at the crash, then erase what should not be there.
- **An aborted transaction appears in neither list.** Its rollback already happened while the system was running.

### Trace 1 — a checkpoint, a commit before it, and a transaction still running

```
    start T1
    write T1 A 100 150
    commit T1
    start T2
    write T2 B 200 250
    ckpt T2
    start T3
    write T3 C 300 350
    commit T2
    start T4
    write T4 A 150 999
    write T3 B 250 275
    commit T3
    <<< CRASH >>>

  initial: {'A': 100, 'B': 200, 'C': 300}
  immediate update (UNDO/REDO)
    redo list = ['T2', 'T3']    undo list = ['T4']
    state at crash  : {'A': 999, 'B': 275, 'C': 350}
    after recovery  : {'A': 150, 'B': 275, 'C': 350}
    committed-only  : {'A': 150, 'B': 275, 'C': 350}   match=True
  deferred update (REDO only)
    redo list = ['T2', 'T3']    undo list = ['T4']
    state at crash  : {'A': 150, 'B': 275, 'C': 350}
    after recovery  : {'A': 150, 'B': 275, 'C': 350}
    committed-only  : {'A': 150, 'B': 275, 'C': 350}   match=True
```

Four things to extract:

- **T1 is in neither list.** It committed *before* the checkpoint, so the checkpoint already forced its pages to disk — redoing it would be wasted work. This is the entire point of a checkpoint, and it is the step most people get wrong.
- **T2 is in the redo list** even though it *started* before the checkpoint, because it committed after it.
- **T4 is in the undo list**, and `A` goes from 999 back to 150 — not to 100. The before-image of T4's write was 150, which is T1's committed value. Undo restores the before-image, not the original.
- Under **deferred update** the crash state already matches, so the undo pass has nothing to do. Same final answer, different amount of work.

### Trace 2 — no checkpoint at all

```
    start T1 / write T1 A 100 150 / start T2 / write T2 B 200 250
    commit T1 / write T2 A 150 777   <<< CRASH >>>

    redo list = ['T1']    undo list = ['T2']
    state at crash  : {'A': 777, 'B': 250, 'C': 300}
    after recovery  : {'A': 150, 'B': 200, 'C': 300}   match=True
```

Note that T2 had written `A` **after** T1 committed it, and the undo pass correctly returned `A` to 150 rather than 100, using T2's own before-image.

### Trace 3 — a transaction that aborted before the crash

```
    start T1 / write T1 A 100 150 / start T2 / write T2 B 200 250
    abort T2 / commit T1 / start T3 / write T3 C 300 350   <<< CRASH >>>

    redo list = ['T1']    undo list = ['T3']
    state at crash  : {'A': 150, 'B': 200, 'C': 350}
    after recovery  : {'A': 150, 'B': 200, 'C': 300}   match=True
```

T2 is in **neither** list, and `B` is already 200 at the crash — its rollback happened at runtime.

### Trace 4 — a checkpoint with nothing active

```
    start T1 / write T1 A 100 150 / commit T1 / ckpt -
    start T2 / write T2 B 200 250 / write T2 A 150 160   <<< CRASH >>>

    redo list = -    undo list = ['T2']
    state at crash  : {'A': 160, 'B': 250, 'C': 300}
    after recovery  : {'A': 150, 'B': 200, 'C': 300}   match=True
```

An **empty redo list** is a perfectly good answer. Everything committed was already forced by the checkpoint; all the work is undo.

---

## 9.6 The result I was not looking for: naive undo needs strict schedules

The self-test asserts that the recovered state equals "the committed transactions' writes, in log order, and nothing else", over 20,000 random logs under both update policies. It did not pass at first, and the reason turned out to be worth more than the test.

```
  20,000 random logs x 2 update policies = 40,000 recoveries
  strict logs: 12122    non-strict (dirty writes): 7878
  mismatches on STRICT logs    : 0        <- must be 0
  mismatches on NON-STRICT logs: 2244   <- expected: naive undo
     is unsafe when a transaction overwrote an uncommitted value
```

**Zero mismatches on the 12,122 strict logs. 2,244 mismatches on the non-strict ones.** The smallest hand-made case shows exactly why:

```
the cascading shape: T2 overwrites an item T1 wrote, then T1 never commits
    start T1
    write T1 A 100 111
    start T2
    write T2 A 111 222
    commit T2
    <<< CRASH >>>

    redo list = ['T2']    undo list = ['T1']
    state at crash  : {'A': 222, 'B': 200, 'C': 300}
    after recovery  : {'A': 100, 'B': 200, 'C': 300}
    committed-only  : {'A': 222, 'B': 200, 'C': 300}   match=False
```

Follow it: redo sets `A = 222` (T2 committed, so its write must survive). Then the undo pass restores T1's before-image, `A = 100` — **wiping out T2's committed write.** The database ends up with `A = 100` when the only correct answer is 222. Atomicity has been broken *by the recovery manager itself*.

The culprit is the **dirty write**: T2 overwrote a value T1 had written but not committed. This is precisely what **strictness** forbids (M8 §8.6), and here is the payoff for that definition:

> **Strict schedules are not an aesthetic preference. They are the precondition that makes before-image undo correct.** Allow dirty writes and the undo pass can destroy committed data. This is why real engines use **strict 2PL** — holding exclusive locks until commit — rather than basic 2PL: it makes a dirty write impossible, so the simple recovery algorithm is sound.

The pieces now fit together: M8's isolation mechanism exists partly to make M9's recovery mechanism correct. If an interviewer asks "why strict 2PL and not plain 2PL?", this is the deepest available answer, and the output above is why I can state it with confidence rather than repeat it.

(The 2,244 figure also deserves an honest reading: it is not a bug count. It is a measure of how often naive undo *would* corrupt the database if the concurrency controller let dirty writes happen. Roughly 28% of the non-strict logs.)

---

## 9.7 Shadow paging

An alternative to logging, worth one page because it gets asked as a contrast.

```
  BEFORE                              DURING the transaction
  current page table                  current table (unchanged)   shadow table (copy)
     p1 -> block 7                       p1 -> block 7               p1 -> block 7
     p2 -> block 9                       p2 -> block 9               p2 -> block 22  <- new copy
                                                                                        of p2

  COMMIT = atomically switch the on-disk pointer to the shadow table (one write).
  ABORT  = discard the shadow table. The original pages were never touched.
```

A modified page is never overwritten; a **copy** is written elsewhere and the shadow page table points at the copy. Commit is a single pointer swap, which makes it atomic by construction.

| | Shadow paging | Log-based (WAL) |
|---|---|---|
| Undo on abort | **Free** — discard the shadow table | Replay before-images |
| Redo after crash | **Not needed** | Required |
| Commit cost | One pointer write | One sequential log force |
| Concurrent transactions | Very hard — each would need its own page table | Natural |
| Data locality | **Destroyed** — logically adjacent pages scatter | Preserved |
| Garbage | Old pages must be collected | The log is truncated at checkpoints |
| Used in practice | No (but the copy-on-write idea lives in LMDB, ZFS, Btrfs) | **Yes, universally** |

**Why it lost:** it cannot handle concurrent transactions cleanly, and it fragments the file so badly that every sequential scan slows down. Say those two reasons and the question is answered.

## 9.8 ARIES, in one paragraph

The recovery algorithm real systems actually implement (IBM, and the model for SQL Server and others). Three ideas beyond the classical algorithm: **repeating history** — the redo pass replays *everything* since the checkpoint, including the writes of transactions that will then be undone, so that recovery starts from a precisely known state; **log sequence numbers (LSNs)** stamped on every page, so recovery can tell whether a page already contains a given update and skip it, which is what makes the passes idempotent in practice; and **compensation log records (CLRs)** written during undo, so that a crash *during* recovery does not undo the same work twice. Three passes: analysis (find the dirty pages and the loser transactions), redo (repeat history), undo (roll back the losers). That paragraph is Tier 3 and more than enough.

---

## 9.9 Relational algebra

SQL is a *language*; relational algebra is the *mathematics* it compiles to. Six primitive operators, and everything else is built from them.

| Operator | Symbol | Arity | What it does | SQL |
|---|---|---|---|---|
| **Select** | σ (sigma) | unary | Keeps the **rows** satisfying a condition | `WHERE` |
| **Project** | π (pi) | unary | Keeps the named **columns**, removing duplicates | `SELECT DISTINCT` |
| **Rename** | ρ (rho) | unary | Renames a relation or its attributes | `AS` |
| **Cartesian product** | × | binary | Every row of R paired with every row of S | `FROM a, b` |
| **Union** | ∪ | binary | All rows in either | `UNION` |
| **Set difference** | − | binary | Rows in R not in S | `EXCEPT` |

Derived (definable from the six, kept for convenience): **intersection** `R ∩ S = R − (R − S)`, **joins** (a product followed by a selection), **division**, and the aggregation/outer-join extensions.

**The one thing to remember about the model:** a relation is a **set**, so relational algebra has **no duplicates** and **no ordering**. SQL deviates from the algebra on exactly those two points — it is a *bag* (multiset) language with `ORDER BY`. That is why `π` corresponds to `SELECT DISTINCT` and not to `SELECT`.

Verified, since the distinction is the single most common slip:

```
  projection WITHOUT distinct is not the same thing:
   SQL without DISTINCT: ['CSE', 'CSE', 'ECE', 'ME']
   RA pi_{dept}        : [('CSE',), ('ECE',), ('ME',)]
```

### The dataset for the rest of this section

```
student(roll, sname, dept) = { (1,Asha,CSE), (2,Ravi,CSE), (3,Meera,ECE), (4,Dev,ME) }
course(cid, title, credits) = { (C1,DBMS,4), (C2,OS,4), (C3,CN,3) }
enroll(roll, cid, grade)    = { (1,C1,A), (1,C2,B), (1,C3,A),
                                (2,C1,B), (2,C2,A), (3,C3,C), (4,C1,A) }
```

Planted deliberately: **Asha (1) is enrolled in all three courses**, Ravi (2) in the two 4-credit ones, Meera and Dev in one each — which is what makes division interesting.

### σ and π — verified

```
   sigma_{dept='CSE'}(student) = { (1,Asha,CSE), (2,Ravi,CSE) }
  [MATCH] vs  select roll,sname,dept from student where dept='CSE'

   pi_{dept}(student) = { (CSE), (ECE), (ME) }
  [MATCH] vs  select distinct dept from student

   pi_{sname}(sigma_{dept='CSE'}(student)) = { (Asha), (Ravi) }
  [MATCH] vs  select distinct sname from student where dept='CSE'
```

### × and the fact that a join *is* a restricted product — verified

```
   |student| = 4, |course| = 3, |student x course| = 12
  [MATCH] vs  select ... from student, course
```

A Cartesian product of an *m*-row and an *n*-row relation has `m × n` rows and `degree(R) + degree(S)` columns. A join is `σ_condition(R × S)` — which is both the formal definition and the reason a missing join condition produces the accidental cross join from M5.

### Natural join vs theta join — verified

```
  [MATCH] enroll |X| course
  [MATCH] enroll |X|_{cid=ccid} rho_{cid->ccid}(course)
   theta-join schema: ('roll','cid','grade','ccid','title','credits')
                       <- cid appears twice; natural join merges it
```

That printed schema is the whole difference: a **natural join** equates all same-named attributes and keeps **one** copy; a **theta join** applies an arbitrary condition and keeps **both** columns. It is the formal version of M5's `NATURAL JOIN` trap — the natural join's behaviour is determined by the *names*, which is why adding a column can silently change the result.

### ρ and why a self-join needs it — verified

```
   classmates = pi_{n1,n2}( sigma_{d1=d2 and r1<r2}( rho_1(student) x rho_2(student) ) )
              = { (Asha,Ravi) }
  [MATCH] vs  select distinct a.sname, b.sname from student a join student b
              on a.dept = b.dept and a.roll < b.roll
```

In the algebra a self-join is *impossible* without rename: `student × student` would have two attributes called `roll` and no way to refer to either. The SQL aliases `a` and `b` **are** ρ. That is the honest answer to "why do I need an alias in a self-join".

### Set operations — verified

```
   A = pi_roll(sigma_{dept=CSE}(student)) = { (1), (2) }
   B = pi_roll(sigma_{cid=C1}(enroll))    = { (1), (2), (4) }

   A union B     = { (1), (2), (4) }   [MATCH]
   A intersect B = { (1), (2) }        [MATCH]
   A - B         = {}                  [MATCH]
   B - A         = { (4) }             [MATCH]
```

Note `A − B ≠ B − A`: difference is **not** commutative, and asking for the wrong direction is a classic exam trap.

All three require **union compatibility** — same degree, same domains, in order:

```
   union(student, course) -> AssertionError: union needs identical schemas
```

---

## 9.10 Division — the "for all" operator

The one worth real effort, because it is the SQL query most candidates cannot write.

> **R ÷ S** = the tuples over the attributes of `R − S` that, in `R`, appear paired with **every** tuple of `S`.

Use it for every query of the form "find X that are related to **all** Y".

```
  pi_{roll,cid}(enroll)         pi_{cid}(course)
  { (1,C1), (1,C2), (1,C3),     { (C1), (C2), (C3) }
    (2,C1), (2,C2),
    (3,C3), (4,C1) }        ÷                        =   { (1) }

  roll 1 appears with C1, C2 and C3 -> survives
  roll 2 appears with C1, C2 only   -> dropped (missing C3)
  rolls 3 and 4 have one each       -> dropped
```

### Verified three independent ways

```
   pi_{roll,cid}(enroll) / pi_{cid}(course) = { (1) }

  [MATCH] division: enrolled in every course (vs double NOT EXISTS)
  [MATCH] division (vs GROUP BY HAVING COUNT)
```

The two SQL formulations it was checked against — both of which you should be able to write:

```sql
-- 1. the double NOT EXISTS: "no course exists that this student did not take"
SELECT DISTINCT e.roll FROM enroll e
WHERE NOT EXISTS (
    SELECT 1 FROM course c
    WHERE NOT EXISTS (
        SELECT 1 FROM enroll e2
        WHERE e2.roll = e.roll AND e2.cid = c.cid));

-- 2. the counting trick: "took as many of them as there are"
SELECT roll FROM enroll
WHERE cid IN (SELECT cid FROM course)
GROUP BY roll
HAVING COUNT(DISTINCT cid) = (SELECT COUNT(*) FROM course);
```

| | Double `NOT EXISTS` | Counting with `HAVING` |
|---|---|---|
| Mirrors the algebra | ✅ Exactly ("for all" = "no counterexample") | ❌ No |
| Readable | Hard | **Easy** |
| Needs the `cid IN (...)` guard | No | **Yes** — otherwise unrelated rows inflate the count |
| Duplicate-safe | Yes | Only with `COUNT(DISTINCT ...)` |
| What to write in an interview | Mention it as the textbook form | **Write this one**, then say you know the other |

Note the two easily-forgotten details in the counting version: without `WHERE cid IN (SELECT cid FROM course)` a student enrolled in three *other* courses would pass the count test, and without `DISTINCT` a duplicated enrolment row would too.

**Dividing by a subset** — verified, and the nicest demonstration that division is parameterised by its divisor:

```
   pi_cid(sigma_{credits=4}(course)) = { (C1), (C2) }
   enroll / that = { (1), (2) }      [MATCH]
```

Divide by all three courses and only Asha qualifies; divide by just the two 4-credit courses and Ravi joins her. **Same dividend, different divisor, different answer** — which is how an exam varies the question.

**And the identity that proves division is derived, not primitive** — verified:

```
   R / S  =  pi_X(R) - pi_X( (pi_X(R) x S) - R )          where X = attributes(R) - attributes(S)

   LHS = [(1,)]    RHS = [(1,)]    equal = True
```

Read the right-hand side as: take every candidate paired with every divisor tuple (`π_X(R) × S`), subtract the pairs that actually exist in R, and whatever candidates remain were **missing** something — so remove them from the candidate list. That construction is also why division is expensive, and why SQL never gave it an operator.

---

## 9.11 Translating queries, and where the optimiser's rewrites come from

### Both directions — verified

```
   SQL : select s.sname from student s join enroll e on e.roll = s.roll
         where e.grade='A' and s.dept='CSE'

   RA  : pi_{sname}( sigma_{grade='A' and dept='CSE'}( student |X| enroll ) )
       = { (Asha), (Ravi) }
  [MATCH]
```

The translation is mechanical, and this is the mapping to memorise:

```
   SELECT  columns        ->  pi   (outermost, applied last)
   FROM    a, b           ->  x    or |X|   (innermost, applied first)
   WHERE   condition      ->  sigma
   DISTINCT               ->  already implied by pi
   JOIN ... ON c          ->  |X|_c
   UNION / INTERSECT / EXCEPT  ->  union / intersect / -
   GROUP BY / aggregates  ->  the extended operator  gamma  (script G)
   ORDER BY               ->  NOTHING -- the algebra has no order
```

Write it as a tree, bottom-up, and the correspondence to the **logical order of execution** from M4 is exact: `FROM` at the leaves, then `σ`, then `π` at the root. The M4 execution order is not an arbitrary rule to memorise — it is the shape of the algebra tree.

### Predicate pushdown, derived rather than asserted

```
   pi_{sname}( sigma_{dept='CSE'}(student) |X| sigma_{grade='A'}(enroll) )
       = { (Asha), (Ravi) }
   same answer: True   <- this equivalence IS predicate pushdown (M7)
```

Two different algebra expressions, **verified to give the same set**. The second filters each relation *before* joining, so the join handles fewer rows. That is exactly the optimiser rewrite from M7 §7.9, and now you can see where its licence comes from: the two expressions are provably equivalent in the algebra, so the engine may substitute one for the other freely.

The equivalences an optimiser uses are all of this kind:

| Rule | Equivalence |
|---|---|
| Selections are commutative | `σ₁(σ₂(R)) ≡ σ₂(σ₁(R))` |
| Conjunctive selections split | `σ_{a∧b}(R) ≡ σ_a(σ_b(R))` |
| **Pushdown** | `σ_a(R ⋈ S) ≡ σ_a(R) ⋈ S` when `a` only mentions R's attributes |
| Projections cascade | `π_a(π_b(R)) ≡ π_a(R)` when `a ⊆ b` |
| Joins are commutative and associative | `R ⋈ S ≡ S ⋈ R`; `(R ⋈ S) ⋈ T ≡ R ⋈ (S ⋈ T)` — **this is join reordering** |

### Relational calculus (named only)

Relational algebra is **procedural** — it says *how* to compute the answer, as a sequence of operators. Relational **calculus** is **declarative** — it describes *what* the answer satisfies, as a logical formula, in two flavours: **tuple relational calculus** (`{ t | t ∈ student ∧ t.dept = 'CSE' }`) and **domain relational calculus** (`{ ⟨r,s,d⟩ | ⟨r,s,d⟩ ∈ student ∧ d = 'CSE' }`).

The single fact that gets asked: **algebra and (safe) calculus have exactly the same expressive power** — this is Codd's theorem, and it is why SQL can be declarative while the engine executes algebra. A language with that power is called **relationally complete**. One sentence is the whole requirement here.

---

## Must remember

```
WHY A LOG EXISTS: real engines use STEAL / NO-FORCE.
  steal    -> uncommitted pages reach disk -> UNDO needed  (verified: b'DIRTY'
              was physically in the db file after a crash)
  no-force -> committed pages may NOT be on disk -> REDO needed
  no-steal removes undo but needs infinite buffer; force removes redo but makes
  commit slow and random. Nobody uses either.

WAL RULE: the log record reaches stable storage BEFORE the data page, and all of a
  transaction's records before the commit is acknowledged. That one rule is enough.
Log record: <T, item, OLD, NEW>  -- old = before-image = UNDO; new = after = REDO.
Commit writes a tiny SEQUENTIAL log force, not the scattered data pages. Hence no-force.
Log records store VALUES, not operations, so both passes are IDEMPOTENT.
rollback journal = an UNDO log (before-images; db modified in place)
WAL file         = a REDO log (after-images; db untouched until checkpoint)
  verified: after 500 inserts in WAL mode the db file was still ONE page

deferred update  (NO-UNDO/REDO): data changes only at commit. Never needs undo.
                                 Cannot handle a transaction bigger than memory.
immediate update (UNDO/REDO):    data changes as it happens. What real systems do.

CHECKPOINT: force the log, force dirty pages, write <ckpt, active txns>.
  everything committed BEFORE the checkpoint can never need redo.
  frequent = fast recovery, slower normal running.

RECOVERY
  analysis: undo-list := active list in the checkpoint record
            <Ti start> -> add to undo-list
            <Ti commit> -> move to redo-list
            <Ti abort>  -> remove (already rolled back at runtime)
  redo:  FORWARD from the checkpoint, apply after-images of the redo-list
  undo:  BACKWARD over the log, restore before-images of the undo-list
  redo forward / undo backward / redo pass runs first
  an aborted transaction is in NEITHER list
  a transaction that committed before the checkpoint is in NEITHER list
  undo restores the BEFORE-IMAGE, not the original value

STRICTNESS IS A RECOVERY REQUIREMENT, not an aesthetic one. (verified: 0 mismatches
  on 12,122 strict logs; 2,244 on non-strict ones. A dirty write makes the undo pass
  erase a COMMITTED value.) This is why real engines use STRICT 2PL.

SHADOW PAGING: copy-on-write pages + a shadow page table; commit = one pointer swap.
  free undo, no redo -- but hopeless with concurrency and it destroys locality.
ARIES: repeat history on redo, LSNs per page, compensation log records. 3 passes.

RELATIONAL ALGEBRA -- six primitives: sigma, pi, rho, x, union, minus
  derived: intersect = R - (R - S); joins = sigma(R x S); division
  A RELATION IS A SET: no duplicates, no order. pi == SELECT DISTINCT, not SELECT.
  SQL is a BAG language with ORDER BY -- that is the deviation.
  |R x S| = |R| * |S|, degree = degree(R) + degree(S)
  natural join merges same-named attributes; theta join keeps both copies
  rho is why a self-join needs an alias: student x student is otherwise unaddressable
  union/intersect/minus need UNION COMPATIBILITY.  R - S != S - R.

DIVISION R/S = tuples over attrs(R)-attrs(S) paired with EVERY tuple of S.
  "find X related to ALL Y".   R/S = pi_X(R) - pi_X((pi_X(R) x S) - R)   [verified]
  SQL: double NOT EXISTS (mirrors the algebra) or
       GROUP BY ... HAVING COUNT(DISTINCT y) = (SELECT COUNT(*) FROM Y)
       -- the counting form NEEDS the "y IN (SELECT ...)" guard and DISTINCT

TRANSLATION: SELECT->pi (last), FROM->x or join (first), WHERE->sigma,
  GROUP BY->gamma, ORDER BY-> nothing. The M4 execution order IS the algebra tree.
Optimiser rewrites are algebra EQUIVALENCES: pushdown, split conjunctions,
  cascade projections, commute/associate joins (= join reordering).
Relational calculus: declarative, tuple and domain flavours. Codd's theorem --
  same expressive power as the algebra ("relationally complete").
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "The log exists in case of a crash" | More precisely: because engines use **steal/no-force**, uncommitted data reaches disk and committed data may not. Verified: `DIRTY` bytes were in the file after a crash |
| "Commit writes the data to disk" | Commit forces the **log**. The data pages are written later — that is what no-force means, and it is why commit is fast |
| "WAL means writing the data before the log" | The opposite: the **log** goes first. That is the entire rule |
| "Undo and redo are alternatives" | Steal/no-force needs **both**. Only deferred update avoids undo, and nothing real uses it |
| "Redo re-runs the transaction" | It re-applies the stored **after-image**. Re-running is not idempotent; applying a value is |
| "Recovery scans the whole log" | From the last **checkpoint**. That is what checkpoints are for |
| "A transaction that committed before the checkpoint must be redone" | Never. The checkpoint already forced its pages to disk. Verified in trace 1 |
| "An aborted transaction goes in the undo list" | Neither list — its rollback happened at runtime |
| "Undo restores the original value" | It restores the **before-image** of that write. Verified: `A` went back to 150, not 100 |
| "Undo runs forward like redo" | Redo forward, undo **backward** |
| "Strict schedules are just good practice" | They are what makes before-image undo **correct**. Verified: 2,244 corruptions out of the non-strict logs |
| "Shadow paging is better — no log needed" | It cannot handle concurrent transactions and it destroys locality. Which is why nothing uses it |
| "Relational algebra and SQL are the same" | The algebra is set-based with no order; SQL is bag-based with `ORDER BY`. `π` is `SELECT DISTINCT` |
| "Projection just picks columns" | It also **removes duplicates**. Verified: SQL gave `CSE, CSE, ECE, ME`, π gave `CSE, ECE, ME` |
| "A natural join and a theta join on the same condition are the same" | The natural join merges the shared column; the theta join keeps both. Verified in the printed schemas |
| "`R − S` is the same as `S − R`" | Difference is not commutative. Verified: `A−B = {}` while `B−A = {4}` |
| "Any two relations can be unioned" | They must be union-compatible — same degree and domains |
| "Division is a primitive operator" | It is derived: `π_X(R) − π_X((π_X(R) × S) − R)`, verified equal |
| "`GROUP BY ... HAVING COUNT(*) = n` is division" | Only with the `IN (SELECT ...)` guard and `COUNT(DISTINCT ...)`; otherwise unrelated or duplicated rows pass |
| "`ORDER BY` becomes an algebra operator" | The algebra has no ordering at all |
| "Relational calculus is more powerful than the algebra" | Equal expressive power — Codd's theorem |

---

## Interview Q&A bank

**Q1. How does a database survive a crash in the middle of a transaction?**
Through write-ahead logging. Every change is recorded in the log, with its before- and after-images, and the log record reaches disk before the data page does; all of a transaction's records reach disk before its commit is acknowledged. After a crash, the log is replayed: committed transactions are redone and in-flight ones are undone.

**Q2. Why is a log needed at all — can't the database just write carefully?**
Because engines use steal/no-force. Steal means a dirty page of an uncommitted transaction can be evicted to disk, so uncommitted data genuinely reaches the file — verified, the string `DIRTY` was physically present after a crash. No-force means commit does not write the data pages, so committed data may be missing. The log is what resolves both.

**Q3. State the WAL rule.**
The log record describing a change must be on stable storage before the changed data page, and all of a transaction's log records before the commit returns.

**Q4. What is in a log record?**
Transaction id, data item, the old value (before-image) and the new value (after-image), plus `start`, `commit`, `abort` and `checkpoint` records. The before-image enables undo and the after-image enables redo.

**Q5. Undo vs redo?**
Undo restores before-images to erase a transaction that had not committed. Redo re-applies after-images to complete a transaction that committed but whose pages had not reached disk.

**Q6. Why are log records values rather than operations?**
So the passes are idempotent. Recovery can itself crash and restart, and applying "A = 150" twice is harmless while applying "add 50 to A" twice is not.

**Q7. Deferred vs immediate update?**
Deferred writes to the database only at commit, so recovery never needs undo — but a transaction cannot exceed the buffer pool. Immediate writes as the operations run and needs both undo and redo. Real systems use immediate.

**Q8. What is a checkpoint and why does it help?**
It forces the log and all dirty pages to disk and records which transactions are active. Everything committed before it is guaranteed on disk, so recovery starts there instead of at the beginning of the log. Frequent checkpoints make recovery fast and normal operation slower.

**Q9. Given a log, how do you build the redo and undo lists?**
Start the undo list from the active list in the last checkpoint record, then scan forward: a `start` adds to the undo list, a `commit` moves the transaction to the redo list, and an `abort` removes it since it was already rolled back. Then redo forward from the checkpoint and undo backward over the log.

**Q10. In trace 1, why is T1 in neither list?**
It committed before the checkpoint, so the checkpoint already forced its pages to disk. Redoing it would be pure waste. That is the point of a checkpoint.

**Q11. Which pass runs first, and in which direction?**
Redo first and forward, so the database reaches the state it was in at the crash; then undo, backward, to erase the uncommitted work. Forward for redo so the last write wins; backward for undo so the earliest before-image ends up in place.

**Q12. Why do real engines use strict 2PL rather than basic 2PL?**
Because strictness is what makes before-image undo correct. Verified: with dirty writes allowed, the undo pass restores a before-image and destroys a *committed* value — 2,244 corruptions across the non-strict logs, and zero across the 12,122 strict ones. Strict 2PL makes dirty writes impossible, so the simple recovery algorithm is sound.

**Q13. What is shadow paging, and why is it not used?**
Pages are never overwritten; a copy is written elsewhere and a shadow page table points at it, so commit is a single atomic pointer swap and abort is free. It is unused because it cannot support concurrent transactions cleanly and it scatters logically adjacent pages, destroying sequential-scan performance.

**Q14. What is ARIES?**
The recovery algorithm real systems implement: three passes (analysis, redo, undo), with redo *repeating history* — replaying everything since the checkpoint, including work that will then be undone — plus log sequence numbers on each page so updates are not applied twice, and compensation log records so a crash during recovery does not re-undo work.

**Q15. How does database recovery relate to a journaling file system?**
Identically. Both write a description of the change to a sequential journal before modifying the real structure in place, and replay the journal after a crash. Same problem, same solution, different layer — the OS M8 version of this module.

**Q16. Name the six primitive relational-algebra operators.**
Select (σ), project (π), rename (ρ), Cartesian product (×), union (∪) and set difference (−). Intersection, joins and division are derived.

**Q17. How does relational algebra differ from SQL?**
A relation is a set, so the algebra has no duplicates and no ordering. SQL is a multiset language with `ORDER BY`. Hence π corresponds to `SELECT DISTINCT`, not `SELECT` — verified, where SQL returned `CSE, CSE, ECE, ME` and π returned three values.

**Q18. What is the relationship between a join and a Cartesian product?**
A join is a product followed by a selection: `R ⋈_c S = σ_c(R × S)`. That is also why a missing join condition degenerates into a cross join.

**Q19. Natural join vs theta join?**
A natural join equates all identically-named attributes and keeps one copy of each; a theta join applies an arbitrary condition and keeps both columns. Verified in the resulting schemas, where the theta join had `cid` twice.

**Q20. Why does a self-join need a rename?**
Because `student × student` would have two attributes called `roll` with no way to address either. ρ gives them distinct names, and SQL's table aliases are exactly that operator.

**Q21. What is union compatibility?**
Two relations can be unioned, intersected or subtracted only if they have the same degree and corresponding attributes drawn from the same domains.

**Q22. What is division and when do you use it?**
`R ÷ S` returns the tuples over `attrs(R) − attrs(S)` that appear in `R` paired with every tuple of `S`. It answers every "find X related to **all** Y" query.

**Q23. Write "students enrolled in every course" in SQL.**
Either as the double negative — select students for which no course exists that they did not enrol in, `NOT EXISTS (... NOT EXISTS ...)` — or by counting: group enrolments restricted to those courses by student and require `COUNT(DISTINCT cid)` to equal the total number of courses. Both verified to return the same single student.

**Q24. What goes wrong with the counting form?**
Without restricting to the divisor set, a student with three *other* enrolments passes the count; and without `COUNT(DISTINCT ...)`, duplicated rows do.

**Q25. Is division primitive?**
No. `R ÷ S = π_X(R) − π_X((π_X(R) × S) − R)` — verified equal. It is kept as a named operator because the derived form is unreadable and expensive.

**Q26. Translate a SQL query to algebra.**
`FROM` becomes the product or join at the leaves, `WHERE` becomes σ above it, `GROUP BY` becomes the extended γ operator, `SELECT` becomes π at the root, and `ORDER BY` has no counterpart. The tree's bottom-up shape is exactly the logical order of execution from M4.

**Q27. What is predicate pushdown in algebra terms?**
The equivalence `σ_a(R ⋈ S) ≡ σ_a(R) ⋈ S` when `a` mentions only R's attributes. Verified: both expressions returned the same set, which is the optimiser's licence to substitute the cheaper one.

**Q28. Relational algebra vs relational calculus?**
The algebra is procedural — an expression says how to compute the result. The calculus is declarative — a formula says what the result satisfies, in tuple or domain form. By Codd's theorem they have equal expressive power, which is why SQL can be declarative while the engine runs algebra.

---

## Practice

For 1–4, the initial state is `A = 100, B = 200, C = 300`. Give the redo list, the undo list, and the final recovered value of each item.

1. ```
   start T1 / write T1 A 100 110 / start T2 / write T2 B 200 210 / commit T1
   ckpt T2 / start T3 / write T3 C 300 310 / commit T3 / write T2 A 110 120
   ```
2. ```
   start T1 / write T1 A 100 150 / ckpt T1 / commit T1
   start T2 / write T2 A 150 160 / start T3 / write T3 B 200 250 / commit T2
   ```
3. ```
   start T1 / write T1 C 300 999 / abort T1 / start T2 / write T2 C 300 350
   ckpt T2 / write T2 B 200 250 / commit T2 / start T3 / write T3 A 100 500
   ```
4. The same log as 3, but under **deferred update**. Which value differs at the moment of the crash, and does the final answer change?
5. Explain, in three sentences, why a `COMMIT` can be fast even though the modified pages are scattered across a 50 GB file.
6. A system is configured **no-steal / force**. Which recovery passes become unnecessary, and what two costs have you accepted?
7. Here is a log fragment: `start T1 / write T1 A 10 20 / start T2 / write T2 A 20 30 / commit T2`, then a crash. Compute the recovered value of `A` by the algorithm, then state the correct value, then name the concurrency-control property whose absence caused the discrepancy.
8. Give the algebra for: "names of students in CSE who have an A grade in a 4-credit course".
9. Give the algebra and both SQL forms for: "students enrolled in every 4-credit course".
10. `π_{sname}(σ_{dept='CSE'}(student) ⋈ σ_{grade='A'}(enroll))` versus `π_{sname}(σ_{dept='CSE' ∧ grade='A'}(student ⋈ enroll))` — are they equivalent, which is cheaper, and what is the rule called?
11. Why can `ORDER BY` not be expressed in relational algebra, and what does that tell you about where sorting happens in a query plan?
12. Write `R ∩ S` using only the six primitives.

**Answers to 1, 7 and 9:**

> **1.** Scan forward. `ckpt T2` resets the undo list to `{T2}` — so **T1, which committed before the checkpoint, is in neither list**. Then `start T3` adds T3, and `commit T3` moves it to redo. Final: **redo = {T3}, undo = {T2}**. Recovery redoes `C = 310`, then undoes T2's writes backwards: `A` back to 110 and `B` back to 200. Result: **A = 110, B = 200, C = 310** — T1's committed 110 survives because it was in the database before the checkpoint.
>
> **7.** The algorithm gives redo = {T2}, undo = {T1}. Redo sets `A = 30`; then undo restores T1's before-image, `A = 10`. **The algorithm yields 10.** The correct answer is **30**, since T2 committed. The discrepancy is caused by the **dirty write** — T2 overwrote T1's uncommitted value — which a **strict** schedule forbids. This is the §9.6 result in miniature, and it is why strict 2PL is used.
>
> **9.** Algebra: `π_{roll,cid}(enroll) ÷ π_{cid}(σ_{credits=4}(course))`, verified to give `{1, 2}`. SQL by counting: `SELECT roll FROM enroll WHERE cid IN (SELECT cid FROM course WHERE credits=4) GROUP BY roll HAVING COUNT(DISTINCT cid) = (SELECT COUNT(*) FROM course WHERE credits=4)`. SQL by double negation: `SELECT DISTINCT e.roll FROM enroll e WHERE NOT EXISTS (SELECT 1 FROM course c WHERE c.credits=4 AND NOT EXISTS (SELECT 1 FROM enroll e2 WHERE e2.roll=e.roll AND e2.cid=c.cid))`.

---

## Exit checklist

```
[ ] I can explain steal/no-force and why each implies a recovery pass
[ ] I can state the WAL rule in one sentence
[ ] I can give the log record format and say which field drives undo vs redo
[ ] I can explain why a commit is fast
[ ] I can say why log records hold values, not operations
[ ] I can explain the difference between a rollback journal and a WAL file
[ ] I can compare deferred and immediate update and say which is used
[ ] I can list the four steps of a checkpoint and what it guarantees
[ ] I can state the checkpoint trade-off in one sentence
[ ] I can build redo and undo lists from any log, with a checkpoint
[ ] I know an aborted transaction appears in neither list
[ ] I know a pre-checkpoint commit appears in neither list
[ ] I know redo is forward, undo is backward, redo runs first
[ ] I know undo restores the before-image, not the original value
[ ] I can explain why strictness is a RECOVERY requirement, with the failing case
[ ] I can describe shadow paging and give the two reasons it lost
[ ] I can say what ARIES adds in three terms
[ ] I can connect all of this to journaling file systems (OS M8)
[ ] I can name the six primitive algebra operators
[ ] I can say why pi is SELECT DISTINCT and not SELECT
[ ] I know a relation is a set: no duplicates, no order
[ ] I can express a join as a product plus a selection
[ ] I can state the difference between natural and theta join in schema terms
[ ] I can explain why a self-join needs rho
[ ] I can state union compatibility and know R-S != S-R
[ ] I can define division and recognise a "for all" query instantly
[ ] I can write division in SQL both ways, with the guard and the DISTINCT
[ ] I can give the derived form of division
[ ] I can translate SQL to an algebra tree and back
[ ] I can state predicate pushdown as an algebra equivalence
[ ] I can say what Codd's theorem asserts
```

---

## Next

**Part 12: M10 — NoSQL, Scaling and the SQL-vs-NoSQL Answer.** Where one relational database stops being enough: **SQL vs NoSQL as a decision table rather than a loyalty test**; the four NoSQL families with one real use case each; **CAP and the way it is usually misread**, PACELC, BASE vs ACID; vertical and horizontal partitioning; **sharding and how to choose a shard key** (with the skew computed); replication, read replicas and eventual consistency; connection pooling; **the ORM N+1 problem** measured; and when denormalizing is the right call.
