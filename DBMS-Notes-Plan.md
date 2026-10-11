# Plan: DBMS Placement Handbook

*Read this and approve it, or change it. No module gets written until you say so.*

---

## 0. What carries over from the DSA / OOP / OS handbooks

Everything. Same system, no new conventions to learn:

| Existing trait | How it applies here |
|---|---|
| Part 1 is a roadmap with no teaching | Same |
| One module per file, `dbms-handbook-part-N-module-X-topic.md` | Same |
| Header line: `Module 3 · 4 hours · Tier 1 · Requires: M0, M1` | Same |
| Opening "why this module matters" + one organising principle in a blockquote | Same |
| Numbered sub-sections, ASCII diagrams, trace tables | Same. Diagrams for B+ trees, ER, precedence graphs, lock timelines |
| Comparison table for every confusable pair | Even more important here — DBMS is almost entirely "difference between X and Y" |
| Must remember / common wrong answers / interview Q&A bank / practice / exit checklist / Next | Same |
| Everything executable is executed before it goes in the notes | **Every SQL query is run against SQLite 3.49 and its real output embedded** (§3) |
| Tier marking, Tier 3 = skippable | Same |

Verified on this machine: Python 3.12.10 with `sqlite3` 3.49.1, which supports CTEs, recursive CTEs, window functions and `FULL OUTER JOIN`. So the SQL modules can be verified the same way the OS numericals were.

---

## 1. What the research says interviewers actually ask

The lists agree closely, and they are shorter than the GATE syllabus:

**The non-negotiable core.** Normalization and the normal forms with examples, denormalization, keys (candidate / primary / foreign / super), ACID, transactions, indexing (and that B+ trees or hashing sit underneath), joins, concurrency control, and schema design. [GeeksforGeeks](https://www.geeksforgeeks.org/dbms/commonly-asked-dbms-interview-questions/); [InterviewBit, Feb 2026](https://www.interviewbit.com/dbms-interview-questions/); [DataCamp, 2026](https://www.datacamp.com/blog/dbms-interview-questions)

**A live SQL round is standard.** Product companies hand you a table and ask for queries, not definitions. The recurring set: Nth highest salary, employees earning more than their manager, department-wise maximum, duplicate rows, consecutive/streak rows, running totals. Self-joins and window functions are the two tools that keep appearing. [38 SQL queries for Amazon / Google / Meta / Microsoft](https://www.linkedin.com/posts/common-jobs.in_sql-interview-queries-activity-7450835510551416833-wOBD); [LeetCode top-60 DBMS thread](https://leetcode.com/discuss/post/3669608/top-60-dbms-interview-questions-basic-to-high-level-questions-must-read/)

**What the lists underweight, and I'm adding:**

- **ER to relational table conversion.** Asked constantly ("design the schema for X"), rarely in the question lists.
- **Finding candidate keys from a set of FDs, and naming the highest normal form.** The single most common DBMS *numerical*, and mechanical once you know attribute closure.
- **Conflict serializability via a precedence graph.** The other common numerical.
- **Why an index can make things slower**, and why `WHERE YEAR(joined) = 2024` cannot use an index on `joined`. Separates people who memorised "indexes make queries fast" from people who understand them.
- **`DELETE` vs `TRUNCATE` vs `DROP`.** Trivially small, asked constantly.

---

## 2. Scope decisions

- **SQL dialect:** ANSI SQL written in MySQL flavour (what most interviews and most campus material assume). Where Postgres/Oracle/SQL Server differ in a way that gets asked (`LIMIT` vs `TOP` vs `ROWNUM`, `AUTO_INCREMENT` vs `SERIAL`), that is a one-line note, not a parallel track.
- **Interview-oriented, not GATE-oriented.** Numericals cover candidate keys, normal forms, lossless decomposition, serializability and B+ tree fan-out. Pure-GATE material (relational calculus, 5NF/DKNF proofs, full ARIES) is Tier 3 and short.
- **Relational algebra is included but Tier 2** — some interviewers and most written tests still ask for it; nobody asks for it in a coding round.
- **NoSQL / CAP / sharding is one Tier 2 module**, deliberately thin. It exists to answer "SQL vs NoSQL, which would you pick and why" and to be the bridge into an HLD handbook later. It is not a NoSQL course.
- **Out of scope:** DB administration, tuning a real server, PL/SQL depth, data warehousing and OLAP beyond a definition, big-data tooling.

---

## 3. How SQL gets verified

The same method that worked for the OS numericals, adapted:

1. Each module's tables and seed rows go in one scratchpad Python script using `sqlite3`.
2. Every query in the notes is executed against it, and the **actual printed output** is what goes in the file. No hand-written "expected" result tables.
3. Where several solutions exist (Nth highest salary has four), all of them run, and the notes show that they agree — then compare them on readability and behaviour on ties, which is the follow-up interviewers ask.
4. FD/candidate-key and serializability numericals get tiny verifier scripts (attribute closure; precedence-graph cycle check), exactly as `banker.py` and `sched.py` did for OS.

**Honest limit, stated up front:** SQLite cannot demonstrate isolation levels or stored procedures — it has its own locking model and no procedural language. So isolation anomalies (dirty read, non-repeatable read, phantom) are taught with interleaving **timeline tables**, which is how interviewers draw them anyway, and are marked as not machine-verified. Stored procedures, triggers and cursors are shown in MySQL syntax and marked syntax-only.

---

## 4. Module plan

**Folder:** `DBMS Notes/` · **About 28–32 hours** · 13 files

| Part | Module | Contents | Hours | Tier |
|---|---|---|---|---|
| 1 | Master roadmap | Syllabus, dependency map, tiers, research, schedules, progress checklist | — | — |
| 2 | **M0 DBMS fundamentals** | File system vs DBMS (the redundancy / consistency / concurrency argument), DBMS advantages, three-schema architecture (physical / logical / view) and **data abstraction**, logical vs physical **data independence**, 2-tier vs 3-tier, data models (hierarchical → network → relational → object → NoSQL), schema vs instance, `DDL`/`DML`/`DCL`/`TCL`, DBA role, ACID named only (full treatment in M8) | 2 | 1 |
| 3 | **M1 Relational model and keys** | Relation / tuple / attribute / domain, degree and cardinality, properties of a relation; **super → candidate → primary → alternate → composite → surrogate → foreign key** as one picture; integrity constraints (domain, entity, referential, key); **NULL semantics and three-valued logic**; referential actions (`CASCADE` / `SET NULL` / `RESTRICT`) | 2–3 | 1 |
| 4 | **M2 ER model and schema design** | Entity vs entity set, attribute types (simple, composite, multivalued, derived, key), relationship degree, **cardinality ratios and participation (total vs partial)**, weak entities and identifying relationships, generalization / specialization / aggregation; **the ER → table conversion rules as a drill** (1:1, 1:N, M:N, multivalued, weak, ISA); two worked schemas end to end | 3 | 1 |
| 5 | **M3 Normalization (centrepiece 1)** | Why redundancy is a bug: insert / update / delete anomalies; **functional dependencies**, trivial vs non-trivial, Armstrong's axioms; **attribute closure and finding all candidate keys** (mechanical procedure plus verified drills); prime vs non-prime; 1NF → 2NF → 3NF → BCNF, each framed as "the anomaly it kills"; partial vs transitive dependency; **decomposition: lossless join and dependency preservation** (and the BCNF-vs-dependency-preservation trade-off); 4NF/5NF one page each (Tier 3); **denormalization and when it is correct**; "highest normal form" numericals | 4–5 | 1 |
| 6 | **M4 SQL I — querying** | **Logical order of execution** (`FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY` → `LIMIT`) as the mental model everything else hangs off; `WHERE` vs `HAVING`; aggregates and what they do with `NULL`; `GROUP BY` rules; `DISTINCT`; `LIKE` / `IN` / `BETWEEN` / `IS NULL`; `CASE`; `UNION` vs `UNION ALL` vs `INTERSECT` vs `EXCEPT`; **the NULL traps** (`NOT IN` with a NULL, `COUNT(*)` vs `COUNT(col)`, `NULL = NULL`) | 3 | 1 |
| 7 | **M5 SQL II — joins, subqueries, windows (centrepiece 2)** | All join types with row-level traces, `JOIN` vs `WHERE`-join, natural and cross joins, **self-join** (the interview workhorse), joining on `NULL`; correlated vs non-correlated subqueries, **`IN` vs `EXISTS` vs `JOIN`** and when each is right; derived tables; CTEs and **recursive CTEs** (employee hierarchy); window functions — `ROW_NUMBER` / `RANK` / `DENSE_RANK`, `PARTITION BY`, `LAG` / `LEAD`, running totals; **the query drill bank**: Nth highest salary (4 ways, compared on ties), duplicates, department-wise max, employees above their manager, consecutive rows, gaps, top-N per group. Every query executed | 5 | 1 |
| 8 | **M6 SQL III — DDL, constraints, views, programmability** | `CREATE` / `ALTER` / `DROP`; **`DELETE` vs `TRUNCATE` vs `DROP`** (full comparison table); constraints, composite and named constraints; **views** — why they exist, when a view is updatable, materialized views; stored procedures vs functions; triggers; cursors; `GRANT` / `REVOKE`; `COMMIT` / `ROLLBACK` / `SAVEPOINT`; **SQL injection and prepared statements** (asked more often than people expect) | 2–3 | 1/2 |
| 9 | **M7 Indexing and storage** | How a table actually sits on disk (pages and blocks, row vs column stores in one paragraph); **why B+ trees and not BSTs or B-trees** — fan-out, height arithmetic, leaf-linked range scans (links straight to your DSA trees module); dense vs sparse; **clustered vs non-clustered** (and why only one per table); primary / secondary / multilevel; **composite indexes and the leftmost-prefix rule**; covering index; hash index and what it cannot do; **when an index hurts** (write cost, low cardinality, small tables); **SARGability** — why a function on a column kills the index; reading `EXPLAIN`; query-optimization basics (predicate pushdown, join order, nested-loop vs hash vs merge join) | 4 | 1/2 |
| 10 | **M8 Transactions and concurrency (centrepiece 3)** | **ACID properly** — each letter, what enforces it, what breaks without it; transaction states; schedules, serial vs concurrent; **conflict serializability and precedence-graph numericals**; view serializability (brief); recoverable / cascadeless / strict schedules; **the four anomalies** — lost update, dirty read, non-repeatable read, phantom — each as an interleaving timeline; **isolation levels × anomalies table**; shared vs exclusive locks and lock compatibility; **2PL, strict and rigorous 2PL**, and why basic 2PL still deadlocks; **deadlock in a DBMS** — wait-for graph, wait-die vs wound-wait, timeouts (explicit contrast with your OS M5); timestamp ordering; **MVCC** and why readers do not block writers | 5 | 1 |
| 11 | **M9 Recovery and relational algebra** | Why a log exists; **WAL**, undo vs redo, deferred vs immediate update; checkpoints; a worked **crash-recovery trace** (which transactions redo, which undo); shadow paging; ARIES in one paragraph (Tier 3). Then **relational algebra**: σ, π, ⋈, ρ, set operations, division, and translating a query both ways; relational calculus named only | 3 | 2 |
| 12 | **M10 NoSQL, scaling and the SQL-vs-NoSQL answer** | Where a single relational DB stops being enough; **SQL vs NoSQL** as a decision table, not a loyalty test; the four NoSQL families (key-value, document, column-family, graph) with one real use case each; **CAP** and the common misreading of it, PACELC in a line, **BASE vs ACID**; horizontal vs vertical partitioning, **sharding** and shard-key choice, replication and read replicas, eventual consistency; connection pooling; **the ORM N+1 problem**; when denormalizing is the right call | 2–3 | 2 |
| 13 | **Consolidation** | One-page SQL syntax sheet; confusable-pairs master table (~30 rows); numericals procedure sheet (candidate keys, normal forms, lossless check, serializability, B+ tree height); **70 rapid-fire Q&A**; **25-query drill bank** with solutions, all executed; final exit checklist | 2 | — |

**Dependency chain:** M0 → M1 → (M2 → M3) and (M4 → M5 → M6). M7 after M1 and M4. M8 after M1. M9 after M8. M10 after M3 and M8. Consolidation last.

**If you only have a week:** M1, M3, M4, M5, M8 — plus the `DELETE`/`TRUNCATE` table from M6 and the "when an index hurts" section from M7. That is the 80%.

---

## 5. Links back to your existing handbooks

| DBMS topic | Builds on |
|---|---|
| B+ tree indexes, fan-out, height | DSA Part 11 (trees); Part 17 (trie) for the multi-way-node idea |
| Hash indexes, `GROUP BY` internals | DSA Part 5 (hashing) |
| Precedence graph and wait-for graph cycle detection | DSA Part 14, §12.7 (directed cycle detection) |
| Top-N per group, `ORDER BY ... LIMIT` | DSA Part 12 (heaps) |
| 2PL, lock compatibility, DB deadlock | OS M4 (synchronization) and M5 (deadlocks) — same four Coffman conditions, different resolution policy |
| Buffer pool and page eviction | OS M7 (virtual memory, LRU replacement) |
| WAL and durability | OS M8 (file systems, journaling) |
| Entity modelling for a schema | OOP M5 (relationships, UML) — an ER diagram and a class diagram are the same skill twice |
| SQL injection, prepared statements | New |

These cross-references get written into the notes, not just listed here. It is the cheapest way to make the fourth subject feel like revision of the first three.

---

## 6. Site integration

One entry in `SUBJECTS` in `study-guide/scripts/sync-notes.mjs` plus a tag in `components/search-dialog.tsx`; the home page picks it up on its own. Proposed sidebar groups:

| Group | Chapters |
|---|---|
| Foundations | M0, M1, M2 |
| Normalization | M3 |
| SQL | M4, M5, M6 |
| Internals | M7 |
| Transactions | M8, M9 |
| Scaling & Revision | M10, consolidation |

Four subjects still fit the sidebar dropdown fine.

---

## 7. How we'll work

1. You approve or edit this plan.
2. I write **Part 1 (master roadmap)**.
3. Then you say "start M0" or "do the next 3", and modules get written in order — roughly 400–700 lines each, same depth and voice as the OS handbook, every query executed before it lands.

---

## 8. Open decisions — tell me if you disagree

1. **MySQL flavour** for all SQL, with one-line notes where Postgres/Oracle differ. Pick MySQL unless your target companies are Postgres shops.
2. **M10 (NoSQL/CAP) stays thin and Tier 2** — a stub for the HLD handbook, not a subject of its own.
3. **Relational algebra kept** in M9 rather than dropped, because written tests still use it. Say the word and it moves to an appendix.
4. **Batch size:** 3 modules per batch, as with OOP and OS.
