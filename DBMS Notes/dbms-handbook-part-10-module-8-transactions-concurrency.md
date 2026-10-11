# DBMS Placement Handbook — Part 10
# Module 8: Transactions and Concurrency

**Module 8 · 5 hours · Tier 1 · Requires: M1 (keys, NULL). Deliberate contrast with OS M4 (synchronization) and OS M5 (deadlocks)**

---

## Why this module matters

This is the third centrepiece and, outside of SQL itself, the most heavily examined module in the subject. It is also the one where theory and practice meet: **ACID** and **serializability** are textbook topics that get asked in written tests, while **isolation levels**, **the four anomalies** and **MVCC** are the ones a working engineer is asked about in an interview.

The question distribution, from compiled interview sets:

- **"Explain ACID"** — near-guaranteed. Needs more than the four words.
- **"Dirty read / non-repeatable read / phantom — and which isolation level permits which"** — the 4×4 table. Asked constantly.
- **"Is this schedule serializable?"** — the precedence-graph numerical. Written tests and GATE.
- **"What is 2PL and why does it still deadlock?"**
- **"What is MVCC and why don't readers block writers?"** — the modern favourite, because it is what PostgreSQL and InnoDB actually do.

The organising principle:

> **A transaction is a unit of work that the database promises to treat as if it were alone and as if it were instantaneous. Those two promises are isolation and atomicity, and every mechanism in this module — locks, timestamps, versions, logs — exists to keep one of them while still letting transactions run at the same time. Serializability is the definition of "as if alone"; the isolation levels are the price list for giving some of it up.**

**How this module was verified.** Two separate pieces of work:

1. A **schedule-analysis toolkit** (`sched.py`) that builds precedence graphs, detects cycles by DFS, decides view serializability by brute force over every serial order, and classifies recoverability. It is **self-tested against 16 cases worked out by hand — all 16 pass**, including the theorem "conflict serializable ⟹ view serializable" checked on every case. Every verdict in §8.4–§8.6 is its output.
2. **Nine live concurrency demonstrations** against real SQLite files and processes — a rollback, a genuine process kill mid-transaction, a real lost update, three different fixes for it, a reader blocking a writer, a true deadlock cycle, snapshot isolation under WAL, and a real **dirty read**.

Two of my own hand-computed answers in the self-test were **wrong**, and §8.4 explains what I got wrong and why, because it is the exact mistake this numerical is designed to catch.

**Honest scope note:** SQLite offers only serializable (rollback-journal mode) and snapshot (WAL mode) isolation. So **the weaker isolation levels and the anomalies they permit are documented, not executed** — except the dirty read, which I reached via a non-default pragma, and the lost update, which is an application-level race and reproduces anywhere.

---

## 8.1 What a transaction is

A **transaction** is a sequence of operations treated as a single logical unit of work. The canonical example:

```
BEGIN
  UPDATE account SET balance = balance - 500 WHERE aid = 1;   -- debit
  UPDATE account SET balance = balance + 500 WHERE aid = 2;   -- credit
COMMIT
```

Between those two statements the database is **inconsistent** — 500 rupees exist nowhere. The entire point of a transaction is that nobody is allowed to see that state, and that it can never be left behind permanently.

### Transaction states

```
                    +-------------+
       BEGIN  --->  |   ACTIVE    |  <--- reads and writes happen here
                    +-------------+
                      |         |
         last op done |         | error / explicit ROLLBACK
                      v         v
          +------------------+  +---------+
          | PARTIALLY        |  | FAILED  |
          | COMMITTED        |  +---------+
          +------------------+       |
                 |                   v
      log forced |            +------------+
      to disk    |            |  ABORTED   |
                 v            +------------+
          +------------+         |        |
          | COMMITTED  |      rollback  kill
          +------------+     (restart)  (give up)
                 |
                 v
          +------------+
          | TERMINATED |
          +------------+
```

The state worth knowing by name is **partially committed**: the last operation has executed but the log records are not yet safely on disk. A crash here means the transaction is *not* committed and must be undone. **Committed** means exactly one thing — the log is durably written. Not "the data pages are written"; that can happen much later (M9).

### Why concurrency at all?

If transactions ran strictly one at a time, none of this module would exist. They do not, for two reasons: **throughput** (a transaction waiting on disk I/O should not stop the CPU doing someone else's work) and **latency** (a 10-minute report must not block every one-millisecond payment behind it). Concurrency is not a feature anyone wanted; it is the price of utilisation — exactly the argument for multiprogramming in **OS M1**.

---

## 8.2 ACID, properly

Four properties, and for each one you should be able to say **what it promises, what enforces it, and what breaks without it.**

| | Promises | Enforced by | Without it |
|---|---|---|---|
| **A**tomicity | All operations happen, or none do | The **log** + rollback (undo) | Money debited and never credited |
| **C**onsistency | A transaction moves the DB from one valid state to another | **Constraints** (PK, FK, CHECK) + application correctness | Negative balances, orphan rows |
| **I**solation | Concurrent transactions produce the same result as *some* serial order | **Concurrency control**: locks, timestamps, MVCC | Lost updates, dirty reads |
| **D**urability | Once committed, it survives a crash | The log forced to disk at commit (**WAL**) | "Payment successful", then a reboot loses it |

### Atomicity — verified

```
  before: [(1, 'Asha', 1000), (2, 'Ravi', 1000)]
  mid-transaction (debit applied, credit not yet): [(1, 'Asha', 500), (2, 'Ravi', 1000)]
  after rollback: [(1, 'Asha', 1000), (2, 'Ravi', 1000)]
  -> all or nothing: the half-done transfer left no trace
```

### Atomicity and durability under a real crash — verified

A rollback is a polite abort. The real test is a process that dies without cleaning up, so I ran one: a child process that writes inside a transaction and then calls `os._exit(1)` — no commit, no close, no rollback, no exception handling.

```
  UNCOMMITTED work:
   child: wrote inside the transaction, now dying without COMMIT
   survivor state: [(1, 'Asha', 1000), (2, 'Ravi', 1000)]
  COMMITTED work:
   child: COMMITted, now dying
   survivor state: [(1, 'Asha', 1000), (2, 'Ravi', 4242)]
```

The uncommitted update **and** the uncommitted `INSERT` of row 3 both vanished; the committed update survived a process that was killed immediately afterwards. That is atomicity and durability demonstrated with an actual crash rather than asserted.

What made it work is the journal file on disk, which the next connection found and used to recover. **That mechanism is M9's subject**, and the division of labour is worth stating now: this module is about *isolation*, M9 is about *atomicity and durability*.

### The two letters people get wrong

**Consistency is the weakest letter**, and saying so is a good signal. Atomicity, isolation and durability are enforced by the database. Consistency is only as good as the constraints you declared plus the correctness of your own transaction logic — the database will happily let a correct, atomic, isolated, durable transaction compute the wrong bonus. The "C" in ACID is also not the "C" in CAP (M10); conflating them is a classic error.

**Isolation is the letter that is routinely traded away.** Full isolation is expensive, so every engine ships with weaker isolation by default and lets you pay for more. That trade-off is §8.8, and it is the most practically important table in the module.

---

## 8.3 Schedules

A **schedule** is an interleaving of the operations of several transactions, preserving each transaction's own internal order.

```
SERIAL schedule                  CONCURRENT schedule
T1 ------------>                 T1 --->    --->     --->
              T2 ------------>   T2    --->     --->
one at a time, no overlap        interleaved
always correct, poor throughput  needs proof of correctness
```

Notation used throughout: `R1(A)` = transaction 1 reads item A, `W2(B)` = transaction 2 writes item B, `C1` = T1 commits, `A1` = T1 aborts.

**The correctness criterion:** a concurrent schedule is acceptable if its effect is equivalent to *some* serial schedule. Not a particular one — any one. That is **serializability**, and it is the definition of the "I" in ACID.

Two operations **conflict** if they are from different transactions, on the same data item, and at least one is a write:

| Pair | Conflict? | Why |
|---|---|---|
| `R`–`R` | ❌ No | Reading does not change anything; order is irrelevant |
| `R`–`W` | ✅ Yes | Whether the read sees the old or new value depends on order |
| `W`–`R` | ✅ Yes | Same reason |
| `W`–`W` | ✅ Yes | Which value is left behind depends on order |

Everything else in this section is machinery built on that one table.

---

## 8.4 Conflict serializability and the precedence graph

### The procedure

> 1. List every **conflicting pair** of operations, in schedule order.
> 2. For each pair, draw an edge **Tᵢ → Tⱼ** where Tᵢ's operation comes first.
> 3. The schedule is **conflict serializable iff the graph is acyclic.**
> 4. If acyclic, a **topological order** of the graph is an equivalent serial schedule.

The graph is also called the **precedence graph** or **serialization graph**. Nodes are transactions, not operations — a common slip.

### Verified drills

Each line below is output from the toolkit. Edges are labelled with the conflict type and item.

**D1 — the classic lost update**

```
D1:  R1(A) R2(A) W1(A) W2(A) C1 C2
  edges: T1->T2 [RW(A),WW(A)], T2->T1 [RW(A)]
  conflict serializable: False   cycle: T1 -> T2 -> T1
  view serializable:     False
  recoverable=True  cascadeless=True  strict=False
```

Both read, then both write. `R1(A)` before `W2(A)` gives T1→T2; `R2(A)` before `W1(A)` gives T2→T1. A two-node cycle, so not serializable — and §8.7 shows this exact schedule losing real money.

**D2 — serial**

```
D2:  R1(A) W1(A) C1 R2(A) W2(A) C2
  edges: T1->T2 [RW(A),WR(A),WW(A)]
  conflict serializable: True   equivalent serial order(s): T1 -> T2
  recoverable=True  cascadeless=True  strict=True
```

**D3 — interleaved, and nevertheless fine**

```
D3:  R1(A) W1(A) R2(A) W2(A) R1(B) W1(B) R2(B) W2(B) C1 C2
  edges: T1->T2 [RW(A),RW(B),WR(A),WR(B),WW(A),WW(B)]
  conflict serializable: True   equivalent serial order(s): T1 -> T2
```

**This is the one I got wrong.** Writing the self-test, I predicted "not serializable" because the schedule is thoroughly interleaved and T1 comes back after T2 has run. Then I made the tool print every conflict pair:

```
   RW on A:  T1 -> T2     WR on A:  T1 -> T2     WW on A:  T1 -> T2
   RW on B:  T1 -> T2     WR on B:  T1 -> T2     WW on B:  T1 -> T2
```

**Every single edge points T1 → T2.** No cycle, so the schedule is equivalent to running T1 then T2 — despite never looking like it. The lesson is the whole reason this numerical exists:

> **Interleaving is not the test. Cycles are the test.** A heavily interleaved schedule can be perfectly serializable, and a barely interleaved one can fail. Do not eyeball it; draw the graph.

(I got a second one wrong the same way: `R1(A) W1(A) R2(A) R1(B) W2(A) W1(B)` — all three conflicts are on A and all point T1→T2, and the T1 operations on B conflict with nothing. Serializable. Both of my errors were the same bias, which is exactly what an examiner is testing.)

**D4 — the real cycle**

```
D4:  R1(A) W1(A) R2(A) W2(A) R2(B) W2(B) R1(B) W1(B) C1 C2
  edges: T1->T2 [RW(A),WR(A),WW(A)], T2->T1 [RW(B),WR(B),WW(B)]
  conflict serializable: False   cycle: T1 -> T2 -> T1
```

Compare D3 and D4 character by character. The *only* difference is that in D4, T2 does its B operations **before** T1 does. That single swap creates the T2→T1 edge, closing the cycle. **Two nearly identical schedules, opposite answers** — which is precisely how this is set in an exam.

**D6 — three transactions, several valid orders**

```
D6:  R1(A) R2(B) W1(A) R3(C) W2(B) W3(C) R1(B) W1(B) C1 C2 C3
  edges: T2->T1 [RW(B),WR(B),WW(B)]
  conflict serializable: True
  equivalent serial order(s): T2 -> T1 -> T3; T2 -> T3 -> T1; T3 -> T2 -> T1
  recoverable=False  cascadeless=False  strict=False
```

Note two things. Only *one* edge exists, because T3 touches only C, which nobody else touches — so T3 is unordered relative to everyone. And **three** serial orders are equivalent, so if asked "give the equivalent serial schedule", any topological order is a correct answer.

**D11 — GATE-style**

```
D11: R2(X) W2(X) R1(X) R1(Y) W1(X) R2(Y) W2(Y)
  edges: T1->T2 [RW(Y)], T2->T1 [RW(X),WR(X),WW(X)]
  conflict serializable: False   cycle: T1 -> T2 -> T1
  recoverable=True  cascadeless=False  strict=False
```

The single edge T1→T2 comes from `R1(Y)` preceding `W2(Y)` — one read of a second item is enough to close the cycle. When you do these by hand, the edge you miss is almost always a read.

**D12 — read-only**

```
D12: R1(A) R2(A) R3(A) C1 C2 C3
  edges: (none)
  conflict serializable: True   equivalent serial order(s): all 6 permutations
```

No writes, no conflicts, no constraints on order. Worth saying in an interview: **read-only transactions never conflict with each other**, which is why read replicas scale so well (M10).

### The exam checklist

```
[ ] nodes are TRANSACTIONS, not operations
[ ] only pairs on the SAME item count
[ ] R-R is never a conflict (the most common wasted edge)
[ ] direction = whichever operation appears FIRST in the schedule
[ ] self-pairs (both ops from the same transaction) are not conflicts
[ ] cycle => not conflict serializable. Acyclic => topological order is the answer
[ ] a cycle of length 2 is still a cycle
[ ] do not eyeball interleaving -- draw the graph (see D3)
```

---

## 8.5 View serializability

Conflict serializability is a **sufficient but not necessary** condition. Some schedules are correct in effect while having a cyclic graph. The broader criterion is **view serializability**: schedule S is view equivalent to serial schedule S′ if

1. each transaction reads the **same values** in both (the "reads-from" relation matches), and
2. the **final write** of each data item is by the same transaction.

**D5 — the standard blind-write example, verified**

```
D5:  R1(A) W2(A) W1(A) W3(A) C1 C2 C3
  edges: T1->T2 [RW(A)], T1->T3 [RW(A),WW(A)], T2->T1 [WW(A)], T2->T3 [WW(A)]
  conflict serializable: False   cycle: T1 -> T2 -> T1
  view serializable:     True   as T1 -> T2 -> T3
```

Cyclic graph, yet view serializable as T1 → T2 → T3. The reason is the **blind write**: `W2(A)` writes A without reading it, and `W1(A)` immediately overwrites it, so T2's write is never observed by anyone. A conflict-based analysis has to assume every write matters; a view-based analysis can see that this one did not.

The toolkit decides this by brute force over all `n!` serial orders, comparing the reads-from relation and the final writers. That is deliberate: **view serializability testing is NP-complete**, so no polynomial procedure exists, and brute force over a small `n` is the only honest implementation.

The containment, verified on all 16 self-test cases:

```
  theorem check: conflict serializable implies view serializable
  held on all cases
```

```
            +-----------------------------------+
            |        all schedules              |
            |   +---------------------------+   |
            |   |   view serializable       |   |
            |   |   +-------------------+   |   |
            |   |   | conflict          |   |   |
            |   |   | serializable      |   |   |
            |   |   |  +-----------+    |   |   |
            |   |   |  |  serial   |    |   |   |
            |   |   |  +-----------+    |   |   |
            |   |   +-------------------+   |   |
            |   +---------------------------+   |
            +-----------------------------------+
```

**What to say in an interview:** *"Conflict serializability is what databases actually enforce, because it is testable in polynomial time with a precedence graph. View serializability is strictly more permissive and would accept more schedules, but deciding it is NP-complete, so no real system uses it. The gap between the two consists of schedules with blind writes."*

---

## 8.6 Recoverability: recoverable, cascadeless, strict

Serializability is about *correctness under concurrency*. Recoverability is about *what happens when a transaction aborts*. A schedule can be perfectly serializable and still be a disaster when something rolls back.

| Class | Definition | Problem it removes |
|---|---|---|
| **Irrecoverable** | Tⱼ reads from Tᵢ and **commits before** Tᵢ does — then Tᵢ aborts | Tⱼ is committed and built on a value that never existed. Unfixable |
| **Recoverable** | If Tⱼ reads from Tᵢ, then Tᵢ commits **before** Tⱼ commits | Nothing is unfixable, but an abort may **cascade** |
| **Cascadeless (ACA)** | A transaction only reads **committed** values | No cascading rollbacks |
| **Strict** | A transaction neither reads **nor writes** an item until its last writer commits | Rollback is trivial — just restore the before-image |

```
  all schedules  >  recoverable  >  cascadeless (ACA)  >  strict  >  serial
```

### Verified

```
D7 dirty read then abort:  W1(A) R2(A) W2(A) C2 A1
  recoverable=False  cascadeless=False  strict=False
```

T2 read T1's uncommitted A, **committed**, and only then T1 aborted. T2's commit is already durable and is based on a value that was undone. Irrecoverable — which is why no real engine permits this ordering.

```
D8 recoverable not ACA:  W1(A) R2(A) W2(A) C1 C2
  recoverable=True  cascadeless=False  strict=False
```

The same dirty read, but T1 commits first, so T2's commit is safe. Recoverable — yet **if T1 had aborted, T2 would have had to be rolled back too.** That is a cascading rollback, and it can propagate through a chain of transactions.

```
D9 strict:  W1(A) C1 R2(A) W2(A) C2
  recoverable=True  cascadeless=True  strict=True
```

```
D10 dirty write:  W1(A) W2(A) C1 C2
  recoverable=True  cascadeless=True  strict=False
```

D10 is the one that catches people. There is no dirty *read* anywhere — T2 never reads A — so it is cascadeless. But T2 **wrote over** T1's uncommitted value, so it is not strict. If T1 now aborted, restoring T1's before-image would also wipe out T2's write. That is why strictness forbids dirty **writes** as well as dirty reads, and why "cascadeless" and "strict" are genuinely different.

Also worth noticing in §8.4: **D1, the non-serializable lost update, is classified `recoverable=True cascadeless=True`.** The two hierarchies are orthogonal — a schedule can be recoverable and still wrong, or serializable and irrecoverable (D7). Do not let one imply the other.

**Why strict matters in practice:** *strict* is what lets the recovery manager undo a transaction by simply writing back the before-image from the log, with no need to check whether anyone else has since touched the item. Strict 2PL (§8.10) delivers exactly this, which is why it, and not basic 2PL, is what real systems implement.

---

## 8.7 The four anomalies

These are the concrete failures that isolation prevents. Each one is a timeline, and you should be able to draw all four from memory.

### 1. Lost update (write–write)

```
   T1                         T2                     balance
   ------------------------------------------------- 1000
   read balance  -> 1000                              1000
                              read balance -> 1000    1000
   compute 1000+100 = 1100                            1000
                              compute 1000-300 = 700  1000
   write 1100                                         1100
                              write 700               700   <-- T1's +100 gone
```

**Verified, with real money:**

```
  start: (1000,)
  T1 read 1000, computed 1100   T2 read 1000, computed 700
  final: (700,)  expected 1000 + 100 - 300 = 800
  -> T1's +100 was LOST: it was overwritten by a value computed before it existed
```

This is the most dangerous anomaly because **no error is raised anywhere**. Both transactions committed successfully and the data is simply wrong. It is also the one that survives in modern applications, because read-modify-write in application code defeats the database's protection: the read and the write are separate statements, and the database is not told they are related.

**Three fixes, all verified:**

```
  fix 1: let the database do the arithmetic (atomic read-modify-write)
  final: (800,)  expected 800
```

`UPDATE account SET balance = balance + 100 WHERE aid = 1` — the read and the write are one statement, so the engine's own row lock makes it atomic. **This is the fix to reach for first**, and it is free.

```
  fix 2: optimistic concurrency with a version column
  T1 read (bal=1000, ver=0)   T2 read (bal=1000, ver=0)
  T1 writes: 1 row(s) updated
  T2 writes: 0 row(s) updated  <- rejected, stale version
  state: (1100, 1)
```

`UPDATE ... SET balance = ?, ver = ver + 1 WHERE aid = ? AND ver = ?` — the stale write matched **zero rows**, so the application detects it (`rowcount == 0`) and retries with fresh data. Nothing is lost silently. This is what every ORM's `@Version` annotation does, and it is the right answer when the read and the write are separated by a user thinking (an edit form).

```
  fix 3: pessimistic -- take the write lock before reading
  T2 blocked while T1 holds the write lock: database is locked
  final: (800,)  expected 800
```

`SELECT ... FOR UPDATE` (or SQLite's `BEGIN IMMEDIATE`) takes the write lock *before* reading, so the second transaction waits instead of racing. Correct, but it serialises the hot row and risks deadlock, so prefer the first two.

| | Optimistic | Pessimistic |
|---|---|---|
| Mechanism | Version check at write time | Lock at read time |
| Cost when there is no conflict | ~zero | A lock held for the whole transaction |
| Cost when there is a conflict | Retry the whole transaction | Waiting |
| Right when | Conflicts are rare; a human is in the loop | Conflicts are common; the critical section is short |

### 2. Dirty read (read uncommitted data)

```
   T1                              T2
   ----------------------------------------------------
   write balance = 999
                                   read balance -> 999      <-- dirty
                                   act on 999 (send email)
   ROLLBACK  (balance is 100 again)
                                   T2's work is based on a value
                                   that never existed
```

**Verified** — reachable in SQLite only with a non-default pragma, which is itself the point:

```
  writer has UPDATEd to 999 and NOT committed
  reader with read_uncommitted=1 sees: (999,)
  writer rolled back; the real value is: (100,)
  -> the reader acted on 999, a value that never existed. That is a dirty read.
```

### 3. Non-repeatable read (same row, two different values)

```
   T1                              T2
   ----------------------------------------------------
   read salary of Asha -> 90000
                                   update Asha's salary = 95000
                                   COMMIT
   read salary of Asha -> 95000    <-- same query, different answer,
                                       inside ONE transaction
```

The difference from a dirty read: the value T1 sees the second time is **committed and legitimate**. The problem is only that T1's own view of the world changed underneath it, so any calculation spanning both reads is inconsistent.

### 4. Phantom read (same range, different set of rows)

```
   T1                                     T2
   -----------------------------------------------------------
   SELECT COUNT(*) WHERE did = 10  -> 3
                                          INSERT a 4th row with did = 10
                                          COMMIT
   SELECT COUNT(*) WHERE did = 10  -> 4   <-- a row appeared from nowhere
```

A phantom is the *insert/delete* version of a non-repeatable read. The distinction matters because the cures are different: locking the rows you read stops a non-repeatable read, but it cannot stop an `INSERT` of a row that **did not exist to be locked**. That needs a **range lock** (a *next-key lock* in InnoDB, predicate locking in general), which is why serializable costs more than repeatable read.

**Verified — both the presence and the absence:**

```
  (a) inside one transaction (snapshot held):
      read 1: (2, 2000)
      another connection inserted a row and changed a balance, committed
      read 2: (2, 2000) <- unchanged: no non-repeatable read, no phantom
  (b) the same two reads WITHOUT holding a transaction (autocommit):
      read 1: (3, 1501)
      read 2: (4, 1601) <- changed: count AND sum moved
```

Both the row count and the sum moved in (b) and neither moved in (a). That is the cleanest possible statement of what a transaction *is*: **(b) is what the world looks like without one.**

### 5. Write skew (the one nobody mentions)

Worth knowing because it is how you show you understand that snapshot isolation is not serializable:

```
   Rule: at least one doctor must always be on call.
   Currently Asha and Ravi are both on call.

   T1 (Asha)                              T2 (Ravi)
   -----------------------------------------------------------
   SELECT count(*) on-call -> 2           SELECT count(*) on-call -> 2
   "2 > 1, safe to go off"                "2 > 1, safe to go off"
   UPDATE Asha: on_call = false           UPDATE Ravi: on_call = false
   COMMIT                                 COMMIT
   -> nobody is on call. Neither transaction wrote what the other read,
      so no write-write conflict exists and snapshot isolation allows it.
```

Snapshot isolation prevents all four classic anomalies and still permits this. PostgreSQL's `SERIALIZABLE` adds **Serializable Snapshot Isolation (SSI)** to catch it; InnoDB's `SERIALIZABLE` uses locks instead. If an interviewer asks "is snapshot isolation the same as serializable?", **write skew is the answer: no.**

---

## 8.8 Isolation levels

The SQL standard defines four levels purely by **which anomalies they permit**. This is the table to memorise.

| Isolation level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| **READ UNCOMMITTED** | ✅ possible | ✅ possible | ✅ possible |
| **READ COMMITTED** | ❌ prevented | ✅ possible | ✅ possible |
| **REPEATABLE READ** | ❌ prevented | ❌ prevented | ✅ possible |
| **SERIALIZABLE** | ❌ prevented | ❌ prevented | ❌ prevented |

Read it as a staircase: **each level removes exactly one more anomaly, in the order dirty → non-repeatable → phantom.** If you remember the order, you can reconstruct the whole table under pressure.

How the levels are achieved with locks (the classical implementation):

| Level | Write locks | Read locks | Range locks |
|---|---|---|---|
| READ UNCOMMITTED | Held to commit | **None** | No |
| READ COMMITTED | Held to commit | Taken and **released immediately** | No |
| REPEATABLE READ | Held to commit | **Held to commit** | No |
| SERIALIZABLE | Held to commit | Held to commit | **Yes** |

Which explains every row of the anomaly table. No read locks → you can read uncommitted data. Read locks released early → the row can change before you read it again. Read locks held but no range lock → an existing row cannot change, but a new row can appear.

### What the engines actually do

| Engine | Default level | Notes |
|---|---|---|
| **PostgreSQL** | READ COMMITTED | Implemented with MVCC. `READ UNCOMMITTED` is accepted but behaves as READ COMMITTED — it genuinely has no dirty reads. `SERIALIZABLE` uses SSI and can abort a transaction with a serialization failure |
| **MySQL / InnoDB** | **REPEATABLE READ** | Unusual among engines. Its RR uses MVCC for reads and **next-key locks** for writes, so it blocks most phantoms too — stricter than the standard requires |
| **Oracle** | READ COMMITTED | Only two levels: READ COMMITTED and SERIALIZABLE (which is really snapshot isolation) |
| **SQL Server** | READ COMMITTED | Lock-based by default; `READ_COMMITTED_SNAPSHOT` switches it to MVCC |
| **SQLite** | **SERIALIZABLE** | One writer at a time. In WAL mode readers get snapshot isolation |

Two points worth having ready, because they show real knowledge:

- **The defaults are not serializable**, anywhere except SQLite. Every production database you will use is running at READ COMMITTED or REPEATABLE READ and permitting anomalies, by design. Interviewers like candidates who know this.
- **"Repeatable read" means different things in different engines.** Standard RR permits phantoms; InnoDB's mostly does not. Naming a level is not enough — you have to say which engine.

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;      -- per transaction
SELECT ... FOR UPDATE;        -- take write locks on the rows you read
SELECT ... FOR SHARE;         -- take read locks (LOCK IN SHARE MODE in MySQL)
```

**How to choose:** stay on the engine's default, and reach for an explicit lock on the specific transaction that needs it. Raising the global isolation level to fix one race is a sledgehammer that costs every other transaction.

---

## 8.9 Locks

### Lock compatibility matrix

The whole of lock-based concurrency control in four cells:

```
                    requested
                 S(hared)   X(clusive)
     held  S       ✅ yes      ❌ no
           X       ❌ no       ❌ no
```

Shared locks (read) are compatible with each other; anything involving an exclusive lock (write) conflicts. That is identical to a **readers–writer lock** in **OS M4** — many readers or one writer.

Real engines add intention locks for multiple granularity (`IS`, `IX`, `SIX`) so a transaction can lock a whole table without checking every row's lock individually. Tier 3; mention the name and move on.

### Verified: a reader blocks a writer

```
  reader reads: [(1, 'Asha', 1000), (2, 'Ravi', 1000)]
  reader now holds a SHARED lock and has not committed
  writer refused: OperationalError - database is locked
  after the reader committed, the writer went through: (1,)
```

That is the S–X conflict in the matrix, happening for real. Note the cost: a transaction that merely *read* and then sat idle stopped a writer completely. **That single observation is the entire motivation for MVCC** (§8.13).

### Lock granularity

```
  database  >  table  >  page  >  row
  <----- less overhead, less concurrency
                      more overhead, more concurrency ----->
```

Coarse locks are cheap to manage and kill concurrency; fine locks are the reverse. Engines **escalate** — if one transaction takes 10,000 row locks, converting them to one table lock is cheaper than tracking them all. (The trade-off mirrors page size in **OS M7**.)

---

## 8.10 Two-phase locking

Taking and releasing locks correctly is not enough — the *shape* of the lock schedule matters. **2PL** requires every transaction to have two phases:

```
  locks
  held
    |        /-----------\
    |       /             \          GROWING: may acquire, may NOT release
    |      /               \         SHRINKING: may release, may NOT acquire
    |     /                 \
    +----------------------------> time
          ^                 ^
       first lock      first unlock = the LOCK POINT
```

**Theorem:** 2PL guarantees conflict serializability. The intuition is that once a transaction releases its first lock it can never acquire another, so the order of transactions' **lock points** is a valid serial order.

### The three variants

| Variant | Rule | Guarantees | Cost |
|---|---|---|---|
| **Basic 2PL** | Two phases | Serializability | Can cascade; **deadlock possible** |
| **Strict 2PL** | All **exclusive** locks held until commit/abort | Serializability + **strict** schedules | Less concurrency; deadlock still possible |
| **Rigorous 2PL** | **All** locks (S and X) held until commit/abort | Same, simpler to reason about | Least concurrency; deadlock still possible |
| **Conservative 2PL** | Acquire **all** locks before starting | **Deadlock-free** | Needs the full lock set up front — usually impractical |

Note the pattern: **only conservative 2PL prevents deadlock, and it is the one nobody uses.** Strict 2PL is the real-world choice, because its guarantee — no dirty reads *or* dirty writes — is what makes rollback cheap (§8.6).

### Why basic 2PL still deadlocks

Because 2PL constrains *when* a transaction may acquire locks, not *what order* different transactions acquire them in:

```
   T1                            T2
   ------------------------------------------------
   lock-X(A)   granted
                                 lock-X(B)   granted
   lock-X(B)   WAIT for T2
                                 lock-X(A)   WAIT for T1
   -> both in the growing phase, both legal under 2PL, both stuck forever
```

Both transactions are perfectly obeying 2PL. **Deadlock is not a violation of 2PL; it is a consequence of it.** That is the answer to "why does 2PL still deadlock", and it is asked often.

### Verified: a real deadlock cycle

```
  both A and B hold SHARED (read) locks
  A UPDATE -> got RESERVED (write intent)
  B UPDATE -> OperationalError: database is locked   (only one writer allowed)
  now A tries to COMMIT, which needs EXCLUSIVE -- but B still holds SHARED:
  A COMMIT -> OperationalError: database is locked

  the wait-for graph at this instant:
     A holds RESERVED, waits for EXCLUSIVE  <- blocked by B's SHARED
     B holds SHARED,   waits for RESERVED   <- blocked by A's RESERVED
     A -> B -> A : a cycle. Neither can proceed.

  once B released its lock, A's commit went through: (1001,)
```

A genuine two-node cycle in the wait-for graph, produced by two transactions that each did nothing wrong — both read, both tried to write. **Lock upgrade (shared → exclusive) is the classic deadlock generator**, which is exactly why `SELECT ... FOR UPDATE` exists: it takes the exclusive lock at read time so there is no upgrade to deadlock on.

---

## 8.11 Deadlock in a DBMS

Same four Coffman conditions as **OS M5** — mutual exclusion, hold and wait, no preemption, circular wait. What differs is the **response**, and the contrast is worth making explicitly because it reveals *why* the two subsystems chose differently.

| | Operating system (OS M5) | Database (here) |
|---|---|---|
| Detection structure | Resource-allocation graph | **Wait-for graph** (transactions only — resources are collapsed out) |
| Detection algorithm | Cycle detection / Banker's | Cycle detection (DSA Part 14, §12.7) |
| Preferred strategy | **Avoidance / prevention** — killing a process loses its work | **Detection and recovery** — aborting a transaction is *free*, because atomicity means rollback is already implemented |
| Recovery | Kill a process, often restart the machine | **Abort a victim and retry it**, usually invisibly |
| Typical frequency | Rare and serious | Routine; engines handle thousands per hour silently |

> **The one-sentence insight:** a database can afford the cheapest deadlock strategy — let them happen, detect them, kill one — precisely *because* it has atomicity. The OS cannot roll a process back, so it must prevent instead. ACID is what makes the easy answer available.

### The wait-for graph

```
   T1 --waits for--> T2
   ^                 |
   |                 v
   T4 <--waits for-- T3        a cycle: T1,T2,T3,T4 are deadlocked
```

Build it by adding an edge Tᵢ → Tⱼ whenever Tᵢ waits for a lock held by Tⱼ. Run cycle detection periodically, or on every wait. A cycle means deadlock; pick a **victim** and abort it.

Victim selection uses: least work done so far, fewest locks held, fewest rollbacks already suffered (to avoid **starvation**, where the same transaction is always chosen), or least undo cost. InnoDB rolls back the transaction with the fewest rows modified.

### Prevention schemes (timestamp-based)

Both give each transaction a timestamp `TS` at start — smaller means older.

| Scheme | Tᵢ wants a lock held by Tⱼ | Effect |
|---|---|---|
| **Wait–die** | If Tᵢ is **older**, it waits. If younger, it **dies** (aborts and retries with the same timestamp) | Non-preemptive: the younger one yields |
| **Wound–wait** | If Tᵢ is **older**, it **wounds** Tⱼ (aborts it). If younger, Tᵢ waits | Preemptive: the older one wins |

Both are deadlock-free, because a cycle would need an older transaction waiting for a younger *and* vice versa, and each scheme permits only one direction. Neither starves, because an aborted transaction **keeps its original timestamp** and therefore becomes the oldest over time and eventually wins.

Memory hook: **"wait–die: the young die. wound–wait: the old wound."** In both, the older transaction has priority — it has done more work, so it is worth more.

| | Wait–die | Wound–wait |
|---|---|---|
| Who aborts | Younger | Younger (preempted by the older) |
| Preemptive | No | Yes |
| Aborts | More | Fewer |
| Waiting | Less | More |

**Timeouts** are the third option and the one most used in practice (and by SQLite, verified above): if a lock wait exceeds *n* seconds, abort. No graph to maintain, works in a distributed setting where a global wait-for graph is impractical. The downsides are that it kills some transactions that were not deadlocked, and picking *n* is a guess.

---

## 8.12 Timestamp ordering (non-lock-based)

Locks are not the only way. **Timestamp ordering** assigns each transaction a timestamp and forces the execution to match timestamp order, with no locks and therefore **no deadlock** at all.

Each item X carries two values:

- `R-TS(X)` — the largest timestamp of any transaction that has read X
- `W-TS(X)` — the largest timestamp of any transaction that has written X

```
  Ti wants to READ X:
      if TS(Ti) < W-TS(X):   REJECT, abort Ti    (a younger txn already wrote it:
                                                  Ti needs a value that is gone)
      else:                  allow; R-TS(X) = max(R-TS(X), TS(Ti))

  Ti wants to WRITE X:
      if TS(Ti) < R-TS(X):   REJECT, abort Ti    (a younger txn already read the
                                                  old value; this write is too late)
      if TS(Ti) < W-TS(X):   REJECT, abort Ti    (an obsolete write)
      else:                  allow; W-TS(X) = TS(Ti)
```

**Thomas's write rule** refines the last case: if `TS(Ti) < W-TS(X)`, the write is obsolete — a younger transaction has already written a newer value — so instead of aborting Ti, simply **ignore the write**. Nobody will ever read the value Ti wanted to leave. That is exactly the blind-write insight from §8.5, turned into an algorithm, and it makes the protocol accept some view-serializable-but-not-conflict-serializable schedules.

| | Lock-based (2PL) | Timestamp ordering |
|---|---|---|
| Deadlock | Possible | **Impossible** |
| Starvation | Possible (victim selection) | Possible (a transaction repeatedly restarted) |
| Aborts | Fewer | More — a conflict means abort, not wait |
| Schedules | Strict with strict 2PL | Not recoverable without extra buffering |
| Used in practice | Yes, widely | Rarely alone; the ideas live on in **MVCC** |

---

## 8.13 MVCC — multiversion concurrency control

The observation from §8.9 is the motivation: a transaction that merely **read** a row blocked a writer completely. In a read-heavy system that is intolerable.

MVCC's idea: **never overwrite in place; write a new version.** An `UPDATE` creates a new version of the row stamped with the writing transaction's identity; the old version stays. Every reader is then given the newest version that was committed **as of the moment its own transaction started** — a *snapshot*.

```
   row "Asha", versions over time
   +------------------+------------------+------------------+
   | balance = 1000   | balance = 7777   | balance = 9000   |
   | created by T5    | created by T9    | created by T12   |
   | expired by T9    | expired by T12   | live             |
   +------------------+------------------+------------------+
        ^                    ^
        |                    |
   a transaction that     a transaction that
   started before T9      started after T9 committed
   sees 1000              sees 7777

   Consequence: READERS NEVER BLOCK WRITERS, AND WRITERS NEVER BLOCK READERS.
   Only writer-writer pairs on the same row still conflict.
```

### Verified

```
  journal_mode: wal
  reader's first read: (1000,)
  writer committed 7777 WHILE the reader's transaction is open (no block)
  reader reads again: (1000,) <- same value: a stable snapshot
  reader after committing and re-reading: (7777,)
```

Compare that output with §8.9 line by line. **Same database, same two connections, same operations** — the only change is WAL mode. In §8.9 the writer was refused with "database is locked". Here it committed immediately, while the reader carried on seeing a consistent older snapshot, and saw the new value only once it started a fresh transaction. That is MVCC in miniature, and it is the clearest possible demonstration of what it buys.

### Costs

| Benefit | Cost |
|---|---|
| Readers never block writers | Old versions must be **stored** |
| Writers never block readers | They must be **cleaned up** — PostgreSQL's `VACUUM`, InnoDB's purge thread |
| Consistent snapshot per transaction, no read locks | A long-running transaction pins old versions and causes **bloat** |
| Read-only transactions are essentially free | Writer–writer conflicts still need locks or abort-and-retry |
| | Snapshot isolation is **not** serializable — write skew (§8.7) survives |

Implementations: PostgreSQL stores versions in the heap with `xmin`/`xmax` and needs `VACUUM`. InnoDB keeps the current row in place and old versions in an **undo log**, following rollback pointers backwards — which is why its undo log serves both MVCC and rollback. Oracle uses undo segments and can raise the famous "snapshot too old" when a version a long query needs has already been recycled.

**The interview answer:** *"MVCC gives each transaction a consistent snapshot by keeping multiple versions of each row instead of overwriting them, so readers never block writers and writers never block readers. Only writer–writer conflicts remain. The cost is storing and later cleaning up old versions, which is what `VACUUM` does in PostgreSQL, and a long-running transaction makes that worse by holding versions alive. It gives snapshot isolation, which prevents all four classic anomalies but still permits write skew — so it is not the same as serializable."*

---

## Must remember

```
TRANSACTION = a unit of work treated as atomic and as if running alone.
States: active -> partially committed -> committed; or failed -> aborted.
COMMITTED means the LOG is durably on disk -- not that data pages are written.

ACID    what it promises             enforced by
  A     all or nothing               log + undo (rollback)
  C     valid state -> valid state   constraints + your own logic (the WEAKEST letter)
  I     as if serial                 locks / timestamps / MVCC
  D     survives a crash             log forced to disk at commit (WAL)
ACID's C is NOT CAP's C.

CONFLICT: different transactions, same item, at least one WRITE.  R-R never conflicts.
PRECEDENCE GRAPH: node per TRANSACTION; edge Ti->Tj if Ti's conflicting op is FIRST.
  acyclic <=> conflict serializable; topological order = equivalent serial schedule
  INTERLEAVING IS NOT THE TEST -- CYCLES ARE. (verified: a fully interleaved
  schedule whose every edge ran T1->T2 was serializable)

serial  <  conflict serializable  <  view serializable  <  all schedules
view serializability: same reads-from + same final writes. NP-complete to decide.
  the gap between the two is schedules with BLIND WRITES.

RECOVERABILITY (orthogonal to serializability!)
  irrecoverable: Tj reads from Ti and commits BEFORE Ti  -> unfixable
  recoverable:   Ti commits before Tj  -> cascading rollback still possible
  cascadeless:   reads only COMMITTED values -> no cascade
  strict:        no reading OR WRITING an uncommitted item -> rollback = restore image
  all > recoverable > cascadeless > strict > serial

THE FOUR ANOMALIES (+1)
  lost update        W-W  two read, both write, one write vanishes. NO ERROR RAISED.
  dirty read         R-W  read uncommitted data that is then rolled back
  non-repeatable     R-W  same row read twice, two different committed values
  phantom            R-W  same range read twice, different SET of rows (needs range lock)
  write skew              snapshot isolation permits it -> SI is NOT serializable

ISOLATION LEVELS      dirty   non-rep   phantom
  READ UNCOMMITTED      Y        Y         Y
  READ COMMITTED        N        Y         Y
  REPEATABLE READ       N        N         Y
  SERIALIZABLE          N        N         N
  staircase: removes dirty -> non-repeatable -> phantom, in that order
  defaults: Postgres/Oracle/SQL Server = READ COMMITTED, MySQL = REPEATABLE READ
  no read locks -> dirty; read locks released early -> non-repeatable;
  read locks held but no range lock -> phantom

LOCKS   S/X compatibility: S+S only. Same as a readers-writer lock (OS M4).
granularity: db > table > page > row. Coarse = cheap + less concurrent.

2PL: growing phase (acquire only) then shrinking (release only). Lock point = first
  unlock. Guarantees serializability. STILL DEADLOCKS -- that is a consequence, not
  a violation. Lock UPGRADE (S->X) is the classic deadlock generator.
  strict 2PL: X locks to commit (-> strict schedules).  rigorous: all locks to commit.
  conservative (all locks up front) is the only deadlock-free one, and nobody uses it.

DEADLOCK: same 4 Coffman conditions as OS M5, opposite strategy.
  OS prevents (cannot roll back a process); a DB DETECTS and aborts a victim,
  because atomicity makes rollback free. Wait-for graph + cycle detection.
  wait-die:    older waits, YOUNGER DIES        (non-preemptive)
  wound-wait:  older WOUNDS younger, younger waits (preemptive)
  both deadlock-free; aborted txn keeps its timestamp, so no starvation.
  timeouts: what SQLite and most real systems actually use.

TIMESTAMP ORDERING: R-TS/W-TS per item; reject out-of-order ops. NO DEADLOCK,
  more aborts. Thomas's write rule: IGNORE an obsolete write instead of aborting.

MVCC: write a new version, never overwrite. Each txn sees a snapshot as of its start.
  READERS NEVER BLOCK WRITERS, WRITERS NEVER BLOCK READERS. Only W-W conflicts remain.
  Cost: version storage + cleanup (VACUUM / purge / undo log); long txns cause bloat.
  Gives SNAPSHOT isolation, which still permits WRITE SKEW.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "ACID: atomicity, consistency, isolation, durability" and nothing more | Name what *enforces* each and what breaks without it. The four words alone are not an answer |
| "Consistency means the data is correct" | It means constraints hold and your transaction logic is right. It is the only letter the database does not fully own |
| "ACID's C and CAP's C are the same" | Unrelated. CAP's C is about all replicas agreeing; ACID's C is about constraints |
| "Committed means written to the data file" | Committed means the **log** is durably on disk. Data pages may be written much later (M9) |
| "An interleaved schedule isn't serializable" | Verified wrong: a fully interleaved schedule whose every edge pointed T1→T2 was serializable. Draw the graph |
| "Two reads of the same item conflict" | `R`–`R` never conflicts. It is the most common wasted edge in the exam |
| "The precedence graph has a node per operation" | A node per **transaction** |
| "Any cycle longer than 2 is needed for a deadlock" | A 2-cycle is a cycle. Verified: T1→T2→T1 in both the schedule drills and the live deadlock |
| "Conflict serializable and view serializable are the same" | Conflict ⟹ view, not the reverse. Blind writes live in the gap. View serializability is NP-complete, so no engine implements it |
| "A serializable schedule is always recoverable" | Orthogonal. D7 is serializable and irrecoverable; D1 is recoverable and not serializable |
| "Cascadeless and strict are the same" | Verified different: `W1(A) W2(A) C1 C2` has no dirty read, so it is cascadeless, but the dirty **write** means it is not strict |
| "A lost update raises an error" | It raises nothing. Both transactions commit happily and the data is simply wrong — verified: 700 where 800 was correct |
| "A dirty read and a non-repeatable read are the same" | A dirty read sees **uncommitted** data; a non-repeatable read sees two different **committed** values |
| "Repeatable read prevents phantoms" | Not per the standard. InnoDB's implementation mostly does, via next-key locks — which is an engine detail, not the level's definition |
| "Everyone runs at serializable" | Nobody does. PostgreSQL, Oracle and SQL Server default to READ COMMITTED; MySQL to REPEATABLE READ |
| "Snapshot isolation is serializable" | It permits **write skew**. PostgreSQL needs SSI on top to be truly serializable |
| "2PL prevents deadlock" | It guarantees serializability and nothing about deadlock. Only *conservative* 2PL is deadlock-free, and it is impractical |
| "Strict 2PL means you take all locks at the start" | That is conservative 2PL. Strict 2PL means you *hold* exclusive locks until commit |
| "Databases prevent deadlocks like an OS does" | They deliberately do not: they detect and abort a victim, because atomicity makes a rollback cheap. Verified on a real cycle |
| "In wait–die the older transaction dies" | The **younger** dies. In wound–wait the older wounds the younger. The older always has priority in both |
| "MVCC removes all locking" | Writer–writer conflicts still need locks or abort-and-retry. Only the reader/writer interference goes away |
| "MVCC is free" | Old versions must be stored and cleaned up; a long-running transaction pins them and bloats the table |

---

## Interview Q&A bank

**Q1. What is a transaction?**
A sequence of operations treated as one logical unit, which the database guarantees to apply completely or not at all, and to behave as if it ran alone.

**Q2. Explain ACID.**
Atomicity: all or nothing, enforced by the log and rollback. Consistency: valid state to valid state, enforced by constraints plus correct application logic. Isolation: concurrent execution is equivalent to some serial order, enforced by locks, timestamps or MVCC. Durability: once committed it survives a crash, enforced by forcing the log to disk at commit.

**Q3. Which ACID property is weakest, and why?**
Consistency, because the database can only enforce the constraints you declared. An atomic, isolated, durable transaction can still compute the wrong value.

**Q4. What exactly does "committed" mean?**
That the transaction's log records are durably on disk. The modified data pages may still be in memory and written much later — which is what makes crash recovery necessary.

**Q5. When do two operations conflict?**
Different transactions, same data item, at least one write. Read–read never conflicts.

**Q6. How do you test whether a schedule is serializable?**
Build the precedence graph: one node per transaction, an edge Tᵢ→Tⱼ for each conflicting pair where Tᵢ's operation comes first. The schedule is conflict serializable if and only if the graph is acyclic, and any topological order is an equivalent serial schedule.

**Q7. A schedule is heavily interleaved. Is it serializable?**
You cannot tell without the graph. Verified: a schedule where T1 and T2 alternate on two items throughout was serializable, because every edge pointed T1→T2. Interleaving is not the test; cycles are.

**Q8. Conflict vs view serializability?**
Conflict serializability is decided in polynomial time with a precedence graph and is what engines enforce. View serializability is strictly broader — it only requires the same reads-from relation and the same final writes — but deciding it is NP-complete. The gap consists of schedules with blind writes.

**Q9. Give a schedule that is view serializable but not conflict serializable.**
`R1(A) W2(A) W1(A) W3(A)` — verified: cyclic graph, yet view equivalent to T1→T2→T3, because T2's blind write is immediately overwritten and never read.

**Q10. What are recoverable, cascadeless and strict schedules?**
Recoverable: if Tⱼ reads from Tᵢ then Tᵢ commits first, so nothing committed is ever based on undone work. Cascadeless: transactions read only committed values, so no abort cascades. Strict: no item is read *or written* until its last writer commits, which makes rollback a simple restore of the before-image.

**Q11. Difference between cascadeless and strict?**
Cascadeless forbids dirty reads; strict also forbids dirty writes. Verified: `W1(A) W2(A) C1 C2` is cascadeless but not strict — nobody read the uncommitted value, but T2 overwrote it, so rolling T1 back would clobber T2's write.

**Q12. Name the four anomalies.**
Lost update: two transactions read then both write, and one write is silently overwritten. Dirty read: reading uncommitted data that is later rolled back. Non-repeatable read: the same row read twice gives two different committed values. Phantom read: the same range read twice returns a different set of rows.

**Q13. Dirty read vs non-repeatable read?**
A dirty read sees data that was never committed and may be rolled back. A non-repeatable read sees two legitimately committed values — the problem is that the transaction's own view changed underneath it.

**Q14. Why does preventing phantoms cost more than preventing non-repeatable reads?**
Because you cannot lock a row that does not exist yet. Stopping a non-repeatable read needs locks on the rows you read; stopping a phantom needs a lock on the *range*, which is why serializable requires range or next-key locking.

**Q15. Give the isolation-levels table.**
READ UNCOMMITTED permits all three. READ COMMITTED prevents dirty reads. REPEATABLE READ also prevents non-repeatable reads. SERIALIZABLE prevents phantoms as well. Each level removes exactly one more anomaly.

**Q16. What are the defaults in real engines?**
PostgreSQL, Oracle and SQL Server default to READ COMMITTED; MySQL/InnoDB to REPEATABLE READ; SQLite is effectively serializable. So production systems are permitting anomalies by design.

**Q17. A lost update happens at READ COMMITTED. How do you fix it without changing the isolation level?**
Three ways, all verified. Let the database do the arithmetic — `SET balance = balance + 100` — so read and write are one atomic statement. Or use optimistic concurrency with a version column, where the stale write updates zero rows and the application retries. Or take the lock at read time with `SELECT ... FOR UPDATE`.

**Q18. Optimistic vs pessimistic concurrency control?**
Optimistic assumes conflicts are rare: proceed and check a version at write time, retrying on failure. Pessimistic locks up front and makes others wait. Optimistic wins when conflicts are rare or a human is in the loop; pessimistic wins when conflicts are frequent and the critical section is short.

**Q19. Give the lock compatibility matrix.**
Shared–shared is compatible; shared–exclusive, exclusive–shared and exclusive–exclusive all conflict. It is the readers–writer lock from operating systems.

**Q20. What is 2PL and what does it guarantee?**
Every transaction acquires all its locks in a growing phase and releases them in a shrinking phase, never acquiring after releasing. The order of transactions' lock points then gives a valid serial order, so 2PL guarantees conflict serializability.

**Q21. Why does 2PL still deadlock?**
Because it constrains *when* a transaction may acquire locks, not the *order* in which different transactions acquire them. T1 holding A and wanting B while T2 holds B and wants A obeys 2PL perfectly and is deadlocked. Verified on a real lock cycle.

**Q22. Strict vs rigorous vs conservative 2PL?**
Strict holds exclusive locks until commit, giving strict schedules and cheap rollback. Rigorous holds all locks until commit. Conservative acquires every lock before starting and is the only deadlock-free variant — and the only one nobody uses, since the full lock set is rarely known in advance.

**Q23. How does a database handle deadlock, and why differently from an OS?**
It maintains a wait-for graph, detects cycles, and aborts a victim, which is then retried. An OS prefers prevention because it cannot roll a process back; a database can, because atomicity already provides rollback. The cheapest strategy is available to the database precisely because it is ACID.

**Q24. Wait–die vs wound–wait?**
Both timestamp the transactions. In wait–die, if the requester is older it waits, otherwise it dies. In wound–wait, if the requester is older it aborts the holder, otherwise it waits. Both are deadlock-free because only one waiting direction is ever allowed, and an aborted transaction keeps its timestamp so it eventually becomes oldest and cannot starve.

**Q25. What is timestamp ordering, and Thomas's write rule?**
Each item keeps the largest read and write timestamps; an operation that would violate timestamp order is rejected and the transaction aborted. No locks, so no deadlock, at the price of more aborts. Thomas's write rule says an obsolete write — one where a younger transaction has already written — can simply be **ignored** instead of causing an abort, since nobody can ever read it.

**Q26. What is MVCC?**
Instead of overwriting a row, the engine writes a new version and gives each transaction a snapshot of what was committed when it began. Readers never block writers and writers never block readers; only writer–writer conflicts remain. Verified: in WAL mode a writer committed a new value while an open reader continued to see the old one consistently.

**Q27. What does MVCC cost?**
Old versions must be stored and later reclaimed — `VACUUM` in PostgreSQL, the purge thread and undo log in InnoDB. A long-running transaction pins old versions alive and bloats the table, and an old version a long query still needs may already be gone, which is Oracle's "snapshot too old".

**Q28. Is snapshot isolation the same as serializable?**
No. It prevents all four classic anomalies but permits **write skew**: two transactions each read a condition, each write a different row, and together they break an invariant neither broke alone. PostgreSQL's SERIALIZABLE adds Serializable Snapshot Isolation to catch it.

---

## Practice

For 1–6, draw the precedence graph, state whether the schedule is conflict serializable, and give an equivalent serial order if one exists.

1. `R1(A) R2(A) W1(A) W2(A)`
2. `R1(A) W1(A) R2(A) W2(A) R1(B) W1(B) R2(B) W2(B)`
3. `R1(A) W1(A) R2(A) W2(A) R2(B) W2(B) R1(B) W1(B)`
4. `R2(X) W2(X) R1(X) R1(Y) W1(X) R2(Y) W2(Y)`
5. `R1(A) R2(B) W1(A) R3(C) W2(B) W3(C) R1(B) W1(B)`
6. `R1(A) W2(A) W1(A) W3(A)` — and additionally, is it view serializable?

7. For each of `W1(A) R2(A) W2(A) C2 A1`, `W1(A) R2(A) W2(A) C1 C2`, `W1(A) C1 R2(A) W2(A) C2` and `W1(A) W2(A) C1 C2`, classify as irrecoverable / recoverable / cascadeless / strict, and say which problem each one leaves open.
8. Draw the timeline for each of the four anomalies, and for each one name the isolation level that is the lowest one preventing it.
9. A booking system at READ COMMITTED oversells the last seat. Name the anomaly and give three fixes, ordered cheapest first.
10. Two transactions run `UPDATE account SET balance = balance - 100 WHERE aid = 1` and `... WHERE aid = 2`, then each updates the other row. Draw the wait-for graph, say what InnoDB does, and give one schema-free way to make it never happen.
11. Why is `SELECT ... FOR UPDATE` often *better* than raising the isolation level to SERIALIZABLE?
12. An analytics transaction runs for 40 minutes against a PostgreSQL OLTP database. Name three distinct problems this causes, each from a different section of this module.
13. Explain to a backend developer, in four sentences and without the word "version", why their read-modify-write loop loses updates and what to write instead.
14. Give a concrete business invariant that snapshot isolation would break, and say what you would do about it.

**Answers to 7, 10 and 12:**

> **7.** (a) **Irrecoverable** — T2 read T1's uncommitted value and committed before T1 aborted, so a committed transaction rests on data that never existed; nothing can fix it. (b) **Recoverable, not cascadeless** — safe, but had T1 aborted, T2 would have had to be rolled back too. (c) **Strict** — T1 committed before T2 touched A, so rollback is trivial. (d) **Cascadeless but not strict** — no dirty read, but the dirty *write* means undoing T1 would also erase T2's write.
>
> **10.** T1 holds a lock on row 1 and waits for row 2; T2 holds row 2 and waits for row 1 — a 2-cycle, `T1 → T2 → T1`. InnoDB detects it almost immediately and rolls back the transaction that modified the fewest rows, returning error 1213, which the application should simply retry. The schema-free fix is to make every transaction lock rows in a **consistent order** (always ascending `aid`), which removes the circular-wait condition entirely — the same prevention strategy as ordered resource acquisition in OS M5.
>
> **12.** One: it pins old row versions alive for 40 minutes, so `VACUUM` cannot reclaim them and the table bloats (§8.13). Two: if it holds a snapshot and conflicts, it may be the deadlock victim or hit a serialization failure, and 40 minutes of work is thrown away (§8.11). Three: it may *need* a version that has already been recycled, giving a snapshot-too-old style failure. The fix is to run analytics against a read replica or a snapshot, not the OLTP primary (M10).

---

## Exit checklist

```
[ ] I can define a transaction and name the transaction states
[ ] I can say what "committed" actually means
[ ] I can give ACID with the enforcing mechanism and the failure for each letter
[ ] I can say why consistency is the weakest letter, and that ACID's C != CAP's C
[ ] I can state the conflict rule and know R-R is not a conflict
[ ] I can build a precedence graph correctly, nodes = transactions
[ ] I know a 2-cycle is a cycle
[ ] I will NOT judge serializability by how interleaved a schedule looks
[ ] I can give the topological order as the equivalent serial schedule
[ ] I can define view serializability and give the blind-write example
[ ] I know conflict => view, and that view serializability is NP-complete
[ ] I can classify a schedule as irrecoverable / recoverable / cascadeless / strict
[ ] I know cascadeless vs strict differ on dirty WRITES, with an example
[ ] I know recoverability and serializability are orthogonal
[ ] I can draw all four anomaly timelines from memory
[ ] I can explain why a lost update raises no error
[ ] I can give three fixes for a lost update, cheapest first
[ ] I can compare optimistic and pessimistic concurrency control
[ ] I can reproduce the 4x4 isolation-levels table
[ ] I can explain each row from which locks are held and for how long
[ ] I know the real defaults in Postgres, MySQL, Oracle and SQL Server
[ ] I can give the S/X compatibility matrix and link it to a readers-writer lock
[ ] I can draw the 2PL phase graph and define the lock point
[ ] I can explain why 2PL still deadlocks, with a two-transaction example
[ ] I can distinguish basic / strict / rigorous / conservative 2PL
[ ] I know lock upgrade is the classic deadlock generator
[ ] I can draw a wait-for graph and explain victim selection and starvation
[ ] I can explain why a DB detects deadlock where an OS prevents it
[ ] I can state wait-die and wound-wait correctly and say who aborts
[ ] I can give the timestamp-ordering rules and Thomas's write rule
[ ] I can explain MVCC, its two "never blocks" guarantees, and its costs
[ ] I can explain write skew and why snapshot isolation is not serializable
```

---

## Next

**Part 11: M9 — Recovery and Relational Algebra.** The other half of the transaction story: why a log exists at all; **write-ahead logging**, undo vs redo, deferred vs immediate update; checkpoints; a **worked crash-recovery trace** deciding exactly which transactions get redone and which undone; shadow paging; ARIES in one paragraph. Then the formal foundation of SQL: **relational algebra** — σ, π, ⋈, ρ, set operations, division — and translating queries in both directions, which is where the optimiser's rewrites from M7 come from.
