# DBMS Placement Handbook — Part 1: Master Roadmap

*Your roadmap for the DBMS portion of technical interviews: what to learn, in what order, how deep, which queries and numericals to practise, and which interview questions each module answers. Later parts teach each module in full.*

---

## 0. How this handbook is built

This is the fourth handbook, after DSA, OOP and OS, and it uses the same structure: Part 1 is the roadmap, and each later part is one module.

**This handbook is for interviews, not for GATE or university exams.** That decides the depth:

- **Concepts and trade-offs come first.** Most DBMS interview questions are "explain", "what's the difference", and "design the schema for X". These are covered in full.
- **SQL is a skill, not a topic.** Three of the thirteen parts are SQL, because product companies hand you a table and ask for queries. Definitions of `SELECT` are worth nothing; writing a correct self-join under pressure is worth a lot.
- **Numericals only where interviews use them:** finding candidate keys from functional dependencies, naming the highest normal form, checking a decomposition, testing a schedule for conflict serializability, and B+ tree height / block-access arithmetic. GATE-only material (relational calculus, 5NF and DKNF proofs, full ARIES) is marked Tier 3 or Tier 4.
- **Mechanism over vocabulary.** "An index speeds up queries" is a non-answer. "A non-clustered index on `email` is a B+ tree whose leaves hold `email` plus a row pointer, so a lookup costs about 3 block reads instead of scanning 10,000" is an answer.

### Note format

Same as the OOP and OS handbooks, with the numerical slot doing double duty as a query slot:

1. **What is it?**
2. **Why does it exist?**
3. **Core idea** (diagram)
4. **How it works** (mechanism step by step; SQL where relevant)
5. **Worked example** — a real query with its real output, or a worked numerical
6. **Comparison** with its confusable neighbour
7. **Must remember**
8. **Common wrong answers**
9. **Interview questions** (question → crisp answer → likely follow-up)
10. **Practice**

### How SQL is verified

- Every SQL statement in this handbook is **executed before it is written down**, using Python 3.12's built-in `sqlite3` module (SQLite 3.49.1), which supports CTEs, recursive CTEs, window functions and `FULL OUTER JOIN`. **The result tables you see are real program output, not hand-written expectations.**
- Where a problem has several standard solutions (the Nth-highest-salary question has four), all of them are run against the same table, and the notes show that they agree — then compare them on readability and on what happens with ties, which is the follow-up interviewers ask.
- The FD and serializability numericals are checked by small scripts (attribute closure; precedence-graph cycle detection), the same way the OS handbook checked Banker's algorithm and the scheduling Gantt charts.
- **Two honest exceptions.** SQLite has its own locking model and no procedural language, so (a) isolation-level anomalies are taught as interleaving **timeline tables** — which is how interviewers draw them anyway — and (b) stored procedures, triggers and cursors are shown in **MySQL syntax, marked syntax-only**. Anything not machine-verified says so on the spot.

### Dialect

SQL is written in **MySQL flavour**, which is what most interviews and most campus material assume. Where Postgres, Oracle or SQL Server differ in a way that actually gets asked — `LIMIT` vs `TOP` vs `ROWNUM`, `AUTO_INCREMENT` vs `SERIAL`, `IFNULL` vs `COALESCE` — there is a one-line note. There is no parallel dialect track.

---

## 1. The master syllabus

13 parts.

| Part | Module | Hours | Tier | Answers questions like |
|---|---|---|---|---|
| 1 | Master roadmap | — | — | — |
| 2 | **M0** DBMS fundamentals | 2 | 1 | Why not just use files? What is data independence? DDL vs DML vs DCL vs TCL |
| 3 | **M1** Relational model and keys | 2–3 | 1 | Super vs candidate vs primary vs foreign key, integrity constraints, NULL |
| 4 | **M2** ER model and schema design | 3 | 1 | Design the schema for X. How do you convert an M:N relationship to tables? |
| 5 | **M3** Normalization | 4–5 | 1 | 1NF to BCNF, partial vs transitive dependency, find the candidate keys |
| 6 | **M4** SQL I — querying | 3 | 1 | `WHERE` vs `HAVING`, `GROUP BY`, `UNION` vs `UNION ALL`, NULL traps |
| 7 | **M5** SQL II — joins, subqueries, windows | 5 | 1 | All join types, self-join, `IN` vs `EXISTS`, Nth highest salary |
| 8 | **M6** SQL III — DDL, views, programmability | 2–3 | 1/2 | `DELETE` vs `TRUNCATE` vs `DROP`, views, triggers, SQL injection |
| 9 | **M7** Indexing and storage | 4 | 1/2 | Why B+ trees? Clustered vs non-clustered. When does an index hurt? |
| 10 | **M8** Transactions and concurrency | 5 | 1 | ACID, the four anomalies, isolation levels, 2PL, MVCC, DB deadlock |
| 11 | **M9** Recovery and relational algebra | 3 | 2 | What is WAL? Redo vs undo. Write this query in relational algebra |
| 12 | **M10** NoSQL, scaling and SQL vs NoSQL | 2–3 | 2 | SQL vs NoSQL, CAP, sharding, replication, the N+1 problem |
| 13 | **Consolidation** | 2 | — | SQL syntax sheet, confusable pairs, 70 rapid-fire Q&A, 25-query drill bank |

**Total: about 28–32 hours.** Tier 1 alone (M0–M5, M8) is about 21–24 hours.

---

## 2. Dependency map

```
                 [M0] DBMS fundamentals
                          |
                 [M1] Relational model & keys
                          |
          +---------------+----------------+
          |                                |
 [M2] ER model                      [M4] SQL I: querying
          |                                |
 [M3] Normalization   <- centrepiece 1     |
          |                        [M5] SQL II: joins   <- centrepiece 2
          |                                |
          |                        [M6] SQL III: DDL & views
          |                                |
          +---------------+----------------+
                          |
                 [M7] Indexing & storage
                          |
                 [M8] Transactions & concurrency   <- centrepiece 3
                          |
          +---------------+----------------+
          |                                |
 [M9] Recovery & rel. algebra      [M10] NoSQL & scaling
          |                                |
          +---------------+----------------+
                          |
                 [Consolidation]
```

The two halves — **design** (M2, M3) and **SQL** (M4, M5, M6) — are independent after M1, so they can be done in either order or interleaved. M7 needs M4 (you have to know what a query looks like before you can speed one up). M8 needs M1 only, so it can be pulled forward if an interview is close.

### The dependencies that actually bite

| To learn | You genuinely need | Why |
|---|---|---|
| Any normal form | Functional dependencies + candidate keys | 2NF/3NF/BCNF are defined *in terms of* candidate keys. Skipping keys is why normalization feels like memorisation |
| Finding candidate keys | Attribute closure | It's a mechanical algorithm, not intuition |
| BCNF vs 3NF | Prime vs non-prime attributes | The whole difference is whether the right side is prime |
| Lossless decomposition | Superkey | Binary decomposition is lossless iff the shared attributes form a superkey of one piece |
| ER to tables | Cardinality and participation | Which side gets the foreign key is decided by the cardinality ratio |
| `HAVING` | Logical order of execution | `HAVING` filters after grouping; `WHERE` filters before. One diagram settles a dozen questions |
| Self-join | Join semantics on a single table | Everything about hierarchies and comparisons between rows is a self-join |
| `EXISTS` vs `IN` | Correlated subqueries + NULL semantics | `NOT IN` with a NULL returning nothing is the classic trap |
| Window functions | `GROUP BY` | A window keeps the rows; a group collapses them. That's the entire distinction |
| Why B+ trees | DSA trees, and disk block sizes | Height ≈ log of fan-out. Fan-out is high because a node is a disk block |
| Clustered vs non-clustered | Physical row order | A clustered index *is* the table's order, which is why you get one |
| SARGability | How an index lookup works | A function on the indexed column destroys the ordering the index relies on |
| Isolation levels | The four anomalies | A level is defined by which anomalies it still permits |
| 2PL | Shared vs exclusive locks | 2PL is a discipline about *when* you may acquire and release them |
| MVCC | Dirty reads + versions | "Readers don't block writers" only makes sense once you know what a reader would otherwise block on |
| DB deadlock | OS deadlock (OS M5) | Same four Coffman conditions; the DBMS resolves by aborting a victim instead of preventing |
| Sharding | Normalization + joins | Sharding breaks cross-shard joins, which is *why* denormalization follows it |

---

## 3. Priority tiers

### Tier 1 — must master

| Topic | Why |
|---|---|
| Keys: super, candidate, primary, foreign, composite | Prerequisite for literally everything else |
| Normalization 1NF → BCNF, with an example per form | The most-asked DBMS topic, every year, every company |
| Finding candidate keys from FDs; highest normal form | The most common DBMS numerical |
| Insert / update / delete anomalies | The "why" that makes normalization answerable in one sentence |
| ER to table conversion | "Design a schema for a library / BookMyShow / Uber" is a standard prompt |
| All join types, and self-join especially | Guaranteed in a SQL round |
| `WHERE` vs `HAVING`, `GROUP BY` rules | Short, constant |
| Subqueries, `IN` vs `EXISTS` vs `JOIN` | Standard follow-up to joins |
| Nth highest salary, department-wise max, duplicates | The three queries you will be asked by name |
| `DELETE` vs `TRUNCATE` vs `DROP` | Tiny topic, enormous frequency |
| ACID, with what enforces each letter | Always asked |
| The four anomalies and the isolation-level table | Always asked, and the table is 4×4 — just learn it |
| Indexing: what it is, clustered vs non-clustered, when it hurts | Always asked; "when it hurts" is the discriminator |
| Why B+ trees underlie indexes | The expected depth at product companies |
| SQL vs NoSQL, in one decision-shaped answer | Asked as a closer in most core-CS segments |
| NULL semantics (`NOT IN`, `COUNT`, `NULL = NULL`) | The trap questions |

### Tier 2 — high priority at product companies

| Topic | Why |
|---|---|
| Window functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`/`LEAD`) | Increasingly the expected solution to top-N and streak problems |
| CTEs and recursive CTEs | Hierarchy questions (manager chains, category trees) |
| Composite index and the leftmost-prefix rule | Separates "I've used indexes" from "I understand indexes" |
| SARGability and reading `EXPLAIN` | The natural "how would you make this faster?" follow-up |
| Conflict serializability and the precedence graph | Common written-test numerical |
| 2PL, strict 2PL, and why basic 2PL still deadlocks | The depth product companies probe |
| MVCC | Modern, and asked because Postgres and InnoDB use it |
| Views and materialized views | Short, frequent |
| Lossless join and dependency preservation | Appears whenever normalization goes one level deeper |
| WAL, redo vs undo, checkpoints | "How does the DB survive a crash mid-transaction?" |
| CAP, BASE, sharding, replication | The bridge into system design |
| SQL injection and prepared statements | Asked more often than people expect, and quick |
| Relational algebra basics | Still used in written tests |

### Tier 3 — good to know

| Topic | Why |
|---|---|
| 4NF, 5NF, multivalued dependencies | Named, rarely pursued |
| View serializability | Asked in GATE-style tests, almost never in interviews |
| Timestamp ordering, Thomas's write rule | Same |
| Shadow paging, ARIES | One-paragraph awareness is enough |
| Two-phase commit (distributed) | Comes up only if you mention microservices |
| Hashed, bitmap and inverted indexes | Context: "when is a hash index better than a B+ tree?" |
| Stored procedures, triggers, cursors | Definitions and one syntax example each |
| PACELC | Only if you raised CAP first |
| Row vs column stores, OLTP vs OLAP | One table, useful if you mention analytics |

### Tier 4 — skip for placements

Relational calculus (tuple and domain), DKNF, full data-warehouse and OLAP cube design, query-optimizer cost formulas in depth, DB administration (backup strategies, user management, replication setup), the internals of any one vendor's optimizer, and the hierarchical and network data models beyond their names.

---

## 4. Interview orientation (what the research says)

**The core list is stable and shorter than the syllabus.** 2026 preparation guides converge on: normalization and the normal forms with examples, denormalization, keys, ACID, transactions, indexing (with B+ trees or hashing underneath), joins, concurrency control, and schema design ([GeeksforGeeks, *Commonly Asked DBMS Interview Questions*](https://www.geeksforgeeks.org/dbms/commonly-asked-dbms-interview-questions/); [InterviewBit, *75+ DBMS Interview Questions*, Feb 2026](https://www.interviewbit.com/dbms-interview-questions/); [DataCamp, *Top 40 DBMS Interview Questions in 2026*](https://www.datacamp.com/blog/dbms-interview-questions)).

**A live SQL round is standard, and it's pattern-based.** Compilations of SQL questions from Amazon, Google, Meta and Microsoft interviews keep returning the same small set: Nth highest salary, employees earning more than their manager, department-wise maximum, duplicate rows, consecutive or streak rows, and running totals. **Self-joins and window functions are the two tools that appear over and over** ([38 SQL queries for Amazon / Google / Meta / Microsoft](https://www.linkedin.com/posts/common-jobs.in_sql-interview-queries-activity-7450835510551416833-wOBD); [LeetCode, *Top 60 DBMS interview questions*](https://leetcode.com/discuss/post/3669608/top-60-dbms-interview-questions-basic-to-high-level-questions-must-read/)).

**How DBMS is asked differs by company type.** Service companies ask definitions and differences — "what is normalization", "what is a foreign key". Product companies do three things instead: they **make you write SQL**, they **chain a concept into a mechanism** ("you added an index and it got slower — why?"), and they **turn a design question into a schema** ("model Splitwise"). Like OS, DBMS usually arrives as a 10–15 minute core-CS segment inside a technical round rather than a round of its own.

**Four practical points:**

1. **Answer with a schema or a query whenever you can.** For a question about M:N relationships, the winning answer draws three tables. For a question about `HAVING`, it writes two lines of SQL.
2. **Numericals are about method, not arithmetic.** For candidate keys, the interviewer watches whether you compute closures systematically instead of guessing. Make the layout mechanical.
3. **Interviewers chain questions.** "What is an index?" → "what structure?" → "why B+ and not a BST?" → "clustered or non-clustered?" → "when would it slow things down?" → "why doesn't `WHERE YEAR(joined)=2024` use it?". Every module lists the likely chain.
4. **The DBMS answer that impresses is a trade-off, not a fact.** Normalization vs denormalization, index vs write cost, strong vs eventual consistency — say what you'd give up and why.

Frequency claims from preparation sites are self-reported and directional.

---

## 5. Question map

The 50 most frequent DBMS questions, and where each is answered.

| # | Question | Module |
|---|---|---|
| 1 | What is a DBMS? Why not just use files? | M0 |
| 2 | DBMS vs RDBMS | M0 |
| 3 | What is the three-schema architecture? | M0 |
| 4 | Logical vs physical data independence | M0 |
| 5 | DDL vs DML vs DCL vs TCL | M0 |
| 6 | Schema vs instance | M0 |
| 7 | What is a relation? Degree and cardinality | M1 |
| 8 | Super key vs candidate key vs primary key vs alternate key | M1 |
| 9 | What is a foreign key? What is referential integrity? | M1 |
| 10 | Primary key vs unique key | M1 |
| 11 | Can a primary key be NULL? Why not? | M1 |
| 12 | What happens to child rows on `ON DELETE CASCADE`? | M1 |
| 13 | What is a composite key? A surrogate key? | M1 |
| 14 | Entity vs entity set; weak entity | M2 |
| 15 | Cardinality ratios and participation constraints | M2 |
| 16 | How do you convert a 1:N / M:N relationship into tables? | M2 |
| 17 | Generalization vs specialization vs aggregation | M2 |
| 18 | Design the schema for a library / cinema / ride-hailing app | M2 |
| 19 | What is normalization? Why do it? | M3 |
| 20 | Insert, update and delete anomalies | M3 |
| 21 | What is a functional dependency? | M3 |
| 22 | Explain 1NF, 2NF, 3NF and BCNF with examples | M3 |
| 23 | Partial vs transitive dependency | M3 |
| 24 | Find all candidate keys of R given these FDs | M3 |
| 25 | What is the highest normal form of this relation? | M3 |
| 26 | Is this decomposition lossless? Is it dependency-preserving? | M3 |
| 27 | What is denormalization, and when is it correct? | M3 |
| 28 | `WHERE` vs `HAVING` | M4 |
| 29 | What is the logical order of execution of a `SELECT`? | M4 |
| 30 | `UNION` vs `UNION ALL`; `INTERSECT`, `EXCEPT` | M4 |
| 31 | `COUNT(*)` vs `COUNT(col)`; what do aggregates do with NULL? | M4 |
| 32 | Why does `NOT IN` return nothing when the subquery has a NULL? | M4 |
| 33 | Explain every join type; `LEFT` vs `INNER` on missing rows | M5 |
| 34 | What is a self-join, and when do you need one? | M5 |
| 35 | Correlated vs non-correlated subquery | M5 |
| 36 | `IN` vs `EXISTS` vs `JOIN` — which and why? | M5 |
| 37 | Find the 2nd / Nth highest salary (and handle ties) | M5 |
| 38 | Find duplicate rows; delete duplicates keeping one | M5 |
| 39 | Highest-paid employee per department | M5 |
| 40 | `ROW_NUMBER` vs `RANK` vs `DENSE_RANK` | M5 |
| 41 | `DELETE` vs `TRUNCATE` vs `DROP` | M6 |
| 42 | What is a view? Can you update through one? Materialized views | M6 |
| 43 | Stored procedure vs function; what is a trigger? | M6 |
| 44 | What is SQL injection and how do you prevent it? | M6 |
| 45 | What is an index? Which data structure, and why B+ tree? | M7 |
| 46 | Clustered vs non-clustered index; why only one clustered? | M7 |
| 47 | When does an index make things *worse*? | M7 |
| 48 | Explain ACID; what enforces durability? | M8 |
| 49 | Dirty read, non-repeatable read, phantom — and the isolation levels | M8 |
| 50 | SQL vs NoSQL: which would you choose, and why? | M10 |

Plus three that span modules and get their own treatment: **"your query is slow, what do you do?"** (M7), **"is this schedule serializable?"** (M8), and **"how does the database survive a crash mid-transaction?"** (M9).

---

## 6. Numericals and query patterns you must be able to do

### Numericals

| Numerical | Module | Method to memorise |
|---|---|---|
| Attribute closure X⁺ | M3 | Repeatedly add right sides of FDs whose left side is already inside X |
| All candidate keys from FDs | M3 | Classify attributes: appearing only on the left are in every key; only on the right are in none. Build from the left-only set and test closures |
| Highest normal form | M3 | Find candidate keys → check each FD: left side a superkey? → BCNF. Right side prime? → 3NF. Else check partial dependency for 2NF |
| Lossless-join check (binary) | M3 | R₁ ∩ R₂ must be a superkey of R₁ or of R₂ |
| Dependency preservation | M3 | Every FD of R must be derivable from the FDs projected onto the pieces |
| Tables after ER conversion | M2 | 1 per entity set + 1 per M:N relationship + 1 per multivalued attribute; 1:N folds the FK into the N side |
| Conflict serializability | M8 | Draw a precedence graph for conflicting pairs (RW, WR, WW); serializable iff acyclic. Topological order = the equivalent serial schedule |
| Anomalies permitted by an isolation level | M8 | The 4×4 table: read uncommitted → read committed → repeatable read → serializable |
| B+ tree order and height | M7 | Order from block size and key+pointer size; height ≈ log_fanout(records) |
| Block accesses with and without an index | M7 | Full scan = total blocks; index lookup = height + 1 |
| Which transactions to redo / undo after a crash | M9 | From the last checkpoint: committed in the log → redo; started but no commit → undo |

### Query patterns

Each of these is solved, executed and compared against alternatives in M5, and all of them reappear in the Consolidation drill bank.

| Pattern | Tools |
|---|---|
| Nth highest / lowest value | Correlated subquery · `LIMIT/OFFSET` · `DENSE_RANK` · self-join count |
| Top-N per group | Window function, or a correlated subquery |
| Row compared to another row (manager, previous month) | Self-join, or `LAG`/`LEAD` |
| Find / delete duplicates | `GROUP BY ... HAVING COUNT(*) > 1`, then `ROW_NUMBER` to keep one |
| Rows present in A but not B | `LEFT JOIN ... IS NULL` · `NOT EXISTS` · `EXCEPT` |
| Running total, moving average | `SUM() OVER (ORDER BY ...)` |
| Consecutive / streak rows | `LAG`, or the row-number-minus-sequence gap trick |
| Pivot a column into columns | `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` |
| Hierarchy traversal (manager chain) | Recursive CTE |
| Fill a gap / find missing IDs | Self-join on `id + 1`, or a generated sequence |

Everything is collected in the Consolidation part: formulas, a SQL syntax sheet and the 25-query drill bank.

---

## 7. Schedules

Hours are DBMS only, alongside DSA.

### 2 weeks (~1 h/day, ~14 h)

| Days | Focus |
|---|---|
| 1 | M0 (skim) + M1 (keys cold) |
| 2–3 | M3 normalization — including the candidate-key drills |
| 4–5 | M4 SQL I |
| 6–8 | M5 SQL II — type every query, don't read them |
| 9 | M2 ER → tables (conversion rules only) |
| 10–11 | M8 transactions: ACID, anomalies, isolation table, 2PL |
| 12 | M7 indexing: Tier 1 sections only |
| 13 | M6 `DELETE`/`TRUNCATE`/`DROP` + views; M10 SQL vs NoSQL answer |
| 14 | Consolidation: rapid-fire Q&A + drill bank |

Skip: M9, and everything Tier 3.

### 1 month (~1 h/day, ~28 h)

| Week | Modules |
|---|---|
| 1 | M0, M1, M2 |
| 2 | M3, M4 |
| 3 | M5, M6 |
| 4 | M7, M8, M10, Consolidation |

M9 if there's room; read its Q&A table regardless.

### 2–3 months (~1 h on alternate days, alongside DSA) — recommended

All 13 parts in order. **Keep one SQLite file open the whole time** and run every query yourself before reading the output — then deliberately break each one (drop the `GROUP BY`, swap `LEFT` for `INNER`, add a NULL row) and see what changes. That single habit is worth more than re-reading any module.

### Revision passes

| Pass | What you do | When |
|---|---|---|
| 1 | Read the module, draw every diagram and type every query | During the module |
| 2 | Answer the module's Q&A out loud, timed (60–90 s each) | End of the module |
| 3 | Redo the numericals on paper without notes | Weekly after M3 |
| 4 | Write 10 drill-bank queries from scratch, no reference | Weekly after M5 |
| 5 | Design one schema end to end from a one-line prompt, in 15 minutes | Final two weeks |
| 6 | Syntax sheet + confusable pairs + rapid-fire only | Last 2–3 days |

---

## 8. Rules I will follow in every module

1. Mechanism before definition. Explain *how* it works, not just what it's called.
2. Every query shown is executed first, and the output printed is the real one. Anything unverifiable in SQLite is labelled on the spot.
3. Every "difference between" gets a comparison table.
4. Every design rule gets a worked schema, not just a rule.
5. Numericals are worked step by step with a fixed layout you can reuse under pressure.
6. MySQL is the reference dialect; other dialects get a one-line note only where it's asked.
7. Numbers that depend on the engine or hardware (block sizes, fan-outs, index overhead) are given as typical orders of magnitude, labelled as such.
8. "Must remember" lists only non-obvious facts.
9. "Common wrong answers" covers what candidates actually say that loses marks.
10. Q&A answers fit in under a minute, with the likely follow-up.
11. Where a topic was already covered in the DSA, OOP or OS handbooks, the notes link to it instead of re-teaching it.

---

## 9. Progress checklist

```
[ ] M0   DBMS fundamentals
[ ] M1   Relational model and keys
[ ] M2   ER model and schema design
[ ] M3   Normalization
[ ] M4   SQL I — querying
[ ] M5   SQL II — joins, subqueries, windows
[ ] M6   SQL III — DDL, views, programmability
[ ] M7   Indexing and storage
[ ] M8   Transactions and concurrency
[ ] M9   Recovery and relational algebra
[ ] M10  NoSQL, scaling and SQL vs NoSQL
[ ] Consolidation

Cross-cutting:
[ ] I can answer all 50 questions in §5 out loud in under 90 s each
[ ] I can find all candidate keys and the highest normal form of any relation, on paper
[ ] I can draw a precedence graph and decide serializability, on paper
[ ] I can write every query pattern in §6 from scratch, with no reference
[ ] I can design a normalized schema from a one-line prompt in 15 minutes
[ ] I can explain why an index made a query slower, and name three causes
[ ] I can give the SQL-vs-NoSQL answer as a trade-off in under 90 seconds
```

---

## Next

**Part 2: M0 — DBMS Fundamentals.** It covers why file-based storage fails (redundancy, inconsistency, no concurrency, no recovery), what a DBMS adds, the three-schema architecture and data abstraction, logical vs physical data independence, 2-tier vs 3-tier, the data models in one table, schema vs instance, and the four SQL command families — with ACID named and deferred to M8.

---

### Sources used for the interview-orientation section

- GeeksforGeeks, *Commonly Asked DBMS Interview Questions*
- InterviewBit, *Top 75+ DBMS Interview Questions and Answers* (updated Feb 2026)
- DataCamp, *Top 40 DBMS Interview Questions in 2026*
- Tutorsbot, *DBMS Interview Questions 2026* (normalization / ACID / indexing weighting)
- Community compilations of SQL rounds at Amazon, Google, Meta and Microsoft (LinkedIn, LeetCode discuss)

Frequency data from preparation platforms is directional, not precise.
