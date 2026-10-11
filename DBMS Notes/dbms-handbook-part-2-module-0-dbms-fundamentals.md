# DBMS Placement Handbook — Part 2
# Module 0: DBMS Fundamentals

**Module 0 · 2 hours · Tier 1 · Requires: nothing**

---

## Why this module matters

This module is the vocabulary everything else is phrased in. On its own it answers maybe three interview questions — "what is a DBMS", "DDL vs DML", "what is data independence" — and they are warm-up questions. But three ideas from here reappear in every later module: **the database is described by a schema that is separate from its data**, **there are three levels of description and applications only ever see the top one**, and **a transaction is the unit that either happens completely or not at all**.

Get those three and the rest of the handbook is detail. Miss them and normalization looks like arbitrary rules.

The organising principle:

> **A DBMS exists to put one managed layer between an application and its bytes on disk. Everything it gives you — no duplicate copies, enforced rules, safe concurrent access, crash recovery, and the freedom to reorganise storage without rewriting applications — follows from the application never touching the file directly.**

**Every SQL statement in this module was executed** (Python 3.12 `sqlite3`, SQLite 3.49.1). Outputs are real.

---

## 0.1 Why not just use files?

The honest answer to "why do we need a DBMS" starts by building the alternative badly. Suppose a college keeps everything in CSV files, with one file per department:

```
cse_students.csv      ece_students.csv      library_members.csv
roll,name,phone,...   roll,name,phone,...   roll,name,phone,...
```

Six problems appear, and each one names a DBMS feature:

| Problem with files | What goes wrong concretely | The DBMS answer |
|---|---|---|
| **Data redundancy** | A student's phone number sits in three files | One table, referenced by others (M1, M3) |
| **Inconsistency** | The phone changes in one file only; now two "truths" exist | Normalization + foreign keys |
| **No enforced rules** | Nothing stops `age = -5`, a blank roll number, or two students with the same roll | Constraints (M1) |
| **Hard to query** | "Students who borrowed a book and are in CSE" needs a custom program | SQL: one declarative query (M4, M5) |
| **No concurrency control** | Two clerks edit the same row; one overwrites the other silently | Transactions and locking (M8) |
| **No recovery** | Power cut halfway through "deduct fee, mark paid" leaves money gone and fee unpaid | Write-ahead log, atomicity (M8, M9) |
| **No security granularity** | File permissions are all-or-nothing; a clerk who can read fees can read marks | `GRANT`/`REVOKE` per table or column (M6) |

**That is the whole answer to the question.** When asked "why DBMS over a file system", do not list adjectives — name two concrete failures (the lost-update and the half-finished transfer) and say which DBMS feature fixes each.

### Terms, precisely

| Term | Meaning |
|---|---|
| **Data** | Raw facts: `'Asha'`, `9000000001` |
| **Information** | Data in a context that answers a question: "Asha's phone is 9000000001" |
| **Database** | An organised, related collection of data |
| **DBMS** | The *software* that stores, retrieves and manages that data (MySQL, Postgres, Oracle, SQLite) |
| **Database system** | The database + the DBMS + the applications on top |

A common trap: *"is MySQL a database?"* Strictly, MySQL is a **DBMS**; the database is the data it manages. Say that once and move on — the interviewer is checking whether you are precise, not pedantic.

---

## 0.2 What a DBMS gives you — and what it costs

| Advantage | Mechanism behind it |
|---|---|
| Controlled redundancy | One fact in one place, joined on demand |
| Consistency and integrity | Constraints checked by the engine, not by every application |
| Multi-user concurrent access | Isolation via locking or MVCC (M8) |
| Atomicity and durability | Transactions + write-ahead log (M8, M9) |
| Declarative querying | You state *what* you want; the optimizer decides *how* (M7) |
| Data independence | The three-level architecture (§0.4) |
| Security and auditing | Privileges per user, per object |
| Backup and recovery | Built in, point-in-time restore |

**And the honest costs**, which candidates almost never mention and interviewers like hearing:

- **Cost and complexity.** A DBMS is software to license, tune, back up and staff.
- **Overhead.** For a single-user, append-only log of 200 rows, a flat file genuinely is faster and simpler.
- **It becomes the bottleneck.** One database behind many servers is the classic scaling wall, which is the whole subject of M10.
- **Rigid schema.** Changing a column on a 500-million-row table is an operation you plan, not a thing you type. This is the pressure that NoSQL exists to relieve.

> **Interview-ready one-liner:** "A DBMS is the right choice as soon as more than one writer, more than one kind of query, or any correctness requirement exists. Below that, a file is fine."

---

## 0.3 DBMS vs RDBMS

| | DBMS | RDBMS |
|---|---|---|
| Data stored as | Files, hierarchies, any structure | **Tables (relations)** of rows and columns |
| Relationships | Implicit, in application code | Explicit, via **keys** |
| Normalization | Not supported as a concept | Supported |
| Constraints | Minimal | Rich (PK, FK, unique, check) |
| Multi-user | Usually limited | Designed for it |
| Query language | Varies | **SQL** |
| Examples | File managers, dBase, early systems | MySQL, PostgreSQL, Oracle, SQL Server, SQLite |

**Every RDBMS is a DBMS; the reverse is not true.** The relational model (M1) is what makes an RDBMS relational — tables plus keys plus set-based operations, not merely "it stores tables".

Where the modern systems sit: a document store like MongoDB is a DBMS and not an RDBMS. That is not an insult — it is a different set of trade-offs, taken up properly in M10.

---

## 0.4 The three-schema architecture and data abstraction

The core structural idea in the subject, from the ANSI/SPARC three-level architecture. A database is described at **three levels**, and each level hides the one below.

```
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  External 1  │  │  External 2  │  │  External 3  │   <- VIEW LEVEL
   │ (clerk sees  │  │ (student     │  │ (auditor     │      many per DB;
   │  no salary)  │  │  sees own    │  │  sees totals │      one per user group
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      "what a user may see"
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │     Conceptual     │              <- LOGICAL LEVEL
                  │  tables, columns,  │                 exactly one;
                  │  keys, constraints │                 the DBA's design
                  └─────────┬──────────┘                 "what data is stored"
                            │
                  ┌─────────▼──────────┐
                  │      Internal      │              <- PHYSICAL LEVEL
                  │ files, pages, B+   │                 exactly one;
                  │ trees, compression │                 "how it is stored"
                  └────────────────────┘
```

| Level | Also called | Describes | How many |
|---|---|---|---|
| **External** | View level | What a particular user or application sees | Many |
| **Conceptual** | Logical level | All tables, columns, keys, constraints, relationships | One |
| **Internal** | Physical level | Files, pages, record layout, indexes, compression | One |

**Data abstraction** is just the name for this hiding. A user writing `SELECT name FROM v_staff` does not know whether the data is in one table or five, on one disk or ten, B+ tree indexed or not.

### Why interviewers ask this

Because the follow-up is the real question: **"what is data independence?"**

---

## 0.5 Data independence (the part that gets asked)

**Data independence = the ability to change one level without having to change the level above it.**

| | **Logical data independence** | **Physical data independence** |
|---|---|---|
| Change made to | The **conceptual** schema | The **internal** schema |
| Without disturbing | **External** schemas and applications | The **conceptual** schema |
| Example change | Split a table in two, add a column, rename a column | Add an index, move to a different disk, change the file organisation or page size |
| Achieved with | **Views** | The storage engine |
| **Harder to achieve** | **Yes** — a real structural change often does reach the application | No — applications never referenced storage anyway |

**The fact worth remembering:** *logical* independence is the harder of the two, which is the opposite of what the names suggest to most people. Physical independence is nearly free, because nothing above the internal level ever mentioned pages or indexes. Logical independence has to be engineered, usually with a view.

### Demonstrated (verified)

Here is logical data independence as an actual before-and-after. The application only ever runs `SELECT * FROM v_staff ORDER BY eid`.

**Before** — one denormalized table, plus a view:

```sql
CREATE TABLE employee(
  eid  INTEGER PRIMARY KEY, name TEXT, dept TEXT, city TEXT);
INSERT INTO employee VALUES (1,'Asha','Eng','Pune'),(2,'Ravi','Sales','Delhi');

CREATE VIEW v_staff AS SELECT eid, name, dept FROM employee;
```

```
app runs: SELECT * FROM v_staff ORDER BY eid
          [(1, 'Asha', 'Eng'), (2, 'Ravi', 'Sales')]
```

Now the DBA **normalizes the conceptual schema** — `employee` becomes two tables — and redefines the view to match:

```sql
CREATE TABLE dept(did INTEGER PRIMARY KEY, dname TEXT);
CREATE TABLE emp_new(
  eid INTEGER PRIMARY KEY, name TEXT,
  did INTEGER REFERENCES dept(did), city TEXT);
-- ... data migrated, old table dropped ...

CREATE VIEW v_staff AS
  SELECT e.eid, e.name, d.dname AS dept
  FROM emp_new e JOIN dept d ON e.did = d.did;
```

```
app runs the SAME query, unchanged:
          [(1, 'Asha', 'Eng'), (2, 'Ravi', 'Sales')]
```

The schema underneath changed shape completely — one table became two, joined on a foreign key — and not one character of the application changed. **That is logical data independence, and the view is the mechanism.** This is also the honest reason production systems expose views to reporting tools instead of base tables.

---

## 0.6 Two-tier vs three-tier architecture (a different thing entirely)

This gets confused with the three-schema architecture constantly, because both say "three". They are unrelated: three-*schema* is about **levels of description**; *n*-tier is about **where the software runs**.

| | **1-tier** | **2-tier** | **3-tier** |
|---|---|---|---|
| Shape | Everything on one machine | Client ↔ Database server | Client ↔ Application server ↔ Database server |
| Client talks to the DB | Directly | Directly (via a driver/ODBC) | **Never** |
| Business logic lives | Anywhere | In the client (fat client) | In the middle tier |
| Example | SQLite inside a desktop app; `mysql` CLI on the server | A campus Java app with a JDBC connection to MySQL | Any web application: browser → API server → Postgres |
| Scales | Not at all | Poorly (every client holds a connection) | Well (pooling, caching, multiple app servers) |
| Security | N/A | DB credentials sit on every client | DB reachable only from the app tier |

**The interview point:** 3-tier wins for anything web-facing, for two reasons worth saying out loud — **the database is never exposed to the client**, and **connections are pooled in the middle tier** instead of one per user. That second point returns in M10.

---

## 0.7 The data models, in one table

A **data model** is the set of concepts you are allowed to describe data with. You need these only as history plus one sentence each — except the relational row, which is the rest of the handbook.

| Model | Structure | Weakness that killed it | Era / survivor |
|---|---|---|---|
| **Hierarchical** | Tree; each child has one parent | No M:N without duplication; navigation is manual | IBM IMS; XML and JSON echo it |
| **Network** | Graph; a child may have several parents | M:N works, but queries are pointer-chasing code | CODASYL |
| **Relational** | Tables + keys; set-based operations | — | **Everything: MySQL, Postgres, Oracle** |
| **Entity-Relationship** | Entities, attributes, relationships | A *design* model, not a storage model | Used to design relational schemas (M2) |
| **Object-oriented / object-relational** | Objects, classes, inheritance | Impedance mismatch solved mostly by ORMs instead | Postgres types, ORMs |
| **Document / key-value / column-family / graph** | JSON documents, KV pairs, wide columns, nodes+edges | Weaker guarantees, weaker ad-hoc querying | MongoDB, Redis, Cassandra, Neo4j (M10) |

**The one-line history worth being able to say:** hierarchical and network models made you *navigate* to your data with code; the relational model let you *describe* it with a query and leave the navigation to the optimizer. That shift is why SQL survived.

---

## 0.8 Schema vs instance

| | **Schema** | **Instance** (or state) |
|---|---|---|
| What it is | The **structure**: tables, columns, types, constraints | The **data** in the tables at one moment |
| Changes | Rarely (a migration) | Constantly (every insert) |
| Analogy | A C++ class declaration | A particular object at runtime |
| Analogy 2 | The form's blank fields | One filled-in form |

```
SCHEMA                                  INSTANCE (today, 11:04)
student(roll INT PK, name TEXT,         (101, 'Asha',  'CSE')
        dept TEXT)                      (102, 'Ravi',  'ECE')

                                        INSTANCE (today, 11:05 — one insert later)
                                        (101, 'Asha',  'CSE')
                                        (102, 'Ravi',  'ECE')
                                        (103, 'Meera', 'CSE')
```

The schema did not change when the row arrived. Related terms:

- **Metadata** — data about the data: the schema itself, column types, constraints, statistics.
- **Data dictionary / system catalog** — where the DBMS stores that metadata, in tables you can query. SQLite exposes `sqlite_master`; MySQL and Postgres expose `information_schema`.

```sql
SELECT name FROM sqlite_master WHERE type = 'table';   -- SQLite's catalog
```

**Interview framing:** "the schema is compile-time, the instance is run-time" lands immediately with anyone who writes code, and it is accurate.

---

## 0.9 The SQL command families: DDL, DML, DCL, TCL

| Family | Stands for | Commands | Acts on | Rollback-able? |
|---|---|---|---|---|
| **DDL** | Data **Definition** | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME` | The **schema** | **Depends on the engine** — see below |
| **DML** | Data **Manipulation** | `INSERT`, `UPDATE`, `DELETE` (and `SELECT`, see note) | The **data** | Yes |
| **DCL** | Data **Control** | `GRANT`, `REVOKE` | **Privileges** | Engine-dependent |
| **TCL** | **Transaction** Control | `COMMIT`, `ROLLBACK`, `SAVEPOINT`, `SET TRANSACTION` | **Transactions** | — |

**Note on `SELECT`.** Many textbooks and Indian university syllabi split it out as a fifth family, **DQL** (Data Query Language). Others count it as DML. If asked, say "`SELECT` is usually called DQL, though some books put it under DML" — that answers the question *and* shows you know why the lists differ.

### TCL, demonstrated (verified)

A money transfer, rolled back:

```sql
CREATE TABLE acct(id INT PRIMARY KEY, bal INT);
INSERT INTO acct VALUES (1,1000),(2,500);

BEGIN;
  UPDATE acct SET bal = bal - 200 WHERE id = 1;
  UPDATE acct SET bal = bal + 200 WHERE id = 2;
  -- inside the transaction:
  SELECT * FROM acct ORDER BY id;     -- [(1, 800), (2, 700)]
ROLLBACK;

SELECT * FROM acct ORDER BY id;       -- [(1, 1000), (2, 500)]
```

Both updates vanished together. That is **atomicity**, and it is the entire reason transactions exist (M8).

`SAVEPOINT` gives you a partial undo inside one transaction:

```sql
BEGIN;
  UPDATE acct SET bal = 0 WHERE id = 1;
  SAVEPOINT sp1;
  UPDATE acct SET bal = 0 WHERE id = 2;
  SELECT * FROM acct ORDER BY id;     -- [(1, 0), (2, 0)]
ROLLBACK TO sp1;
  SELECT * FROM acct ORDER BY id;     -- [(1, 0), (2, 500)]   <- only the second undone
ROLLBACK;
  SELECT * FROM acct ORDER BY id;     -- [(1, 1000), (2, 500)] <- all the way back
```

**`ROLLBACK TO sp1` does not end the transaction** — it rewinds to the savepoint and leaves you inside it. That is the detail interviewers probe.

### Can DDL be rolled back?

Verified in SQLite:

```sql
BEGIN;
  CREATE TABLE scratch(x INT);
ROLLBACK;
SELECT name FROM sqlite_master WHERE type='table';   -- ['acct']  <- scratch is gone
```

So in SQLite, yes. **This is one of the biggest dialect differences in the subject, so learn all three answers:**

| Engine | DDL inside a transaction |
|---|---|
| **MySQL (InnoDB)** | **Cannot be rolled back.** A DDL statement causes an **implicit `COMMIT`** of whatever transaction was open. MySQL 8.0 made individual DDL statements atomic, but they still commit the surrounding transaction |
| **PostgreSQL** | Fully transactional DDL — `CREATE`, `ALTER`, `DROP` all roll back |
| **SQLite** | Transactional DDL, as shown above |
| **Oracle** | Implicit commit before and after DDL |

If the interviewer asks "can you roll back a `CREATE TABLE`?" the complete answer is: **"In MySQL and Oracle no, because DDL forces an implicit commit. In Postgres and SQLite yes."** Most candidates give one half.

---

## 0.10 Who does what

| Role | Responsibility |
|---|---|
| **DBA** (database administrator) | Schema changes, users and privileges, backups, performance tuning, capacity |
| **Database designer** | The conceptual schema: entities, relationships, normalization (M2, M3) |
| **Application developer** | Queries and transactions against the external schema |
| **End user** | Naive (uses an app), or sophisticated (writes ad-hoc SQL) |

Worth one line because "what does a DBA do" is an occasional easy question, and because **privileges are the DBA's job, not the application's** — which is the setup for SQL injection in M6.

---

## 0.11 ACID, named here and deferred

You will be asked ACID in nearly every interview, and it gets a full module (M8). For now, hold the one-line version so the term is not new when transactions arrive:

| Letter | Property | One line |
|---|---|---|
| **A** | Atomicity | All of a transaction happens, or none of it does |
| **C** | Consistency | A transaction moves the DB from one valid state to another valid state |
| **I** | Isolation | Concurrent transactions do not see each other's half-finished work |
| **D** | Durability | Once committed, it survives a crash |

The transfer in §0.9 showed **A**. The constraints in M1 are **C**. **I** and **D** are M8.

---

## 0.12 Consolidation

### Must remember (module)

1. **Logical data independence is harder to achieve than physical**, and views are how you get it. The names mislead almost everyone.
2. Three-**schema** architecture (external / conceptual / internal) and *n*-**tier** architecture (client / app / DB) are unrelated ideas that both say "three".
3. There is **one** conceptual and **one** internal schema, but **many** external schemas.
4. MySQL is a DBMS; the database is the data. Every RDBMS is a DBMS, not the reverse.
5. `SELECT` is classified as **DQL** by most Indian syllabi, and as DML by some books. Know that the disagreement exists.
6. **`TRUNCATE` is DDL, not DML** — the single most common classification mistake. Full comparison in M6.
7. **DDL rollback is dialect-dependent:** impossible in MySQL/Oracle (implicit commit), fine in Postgres/SQLite.
8. `ROLLBACK TO savepoint` rewinds but **keeps the transaction open**.
9. A DBMS is not always right: for a single writer with no correctness requirement, a file is cheaper and faster. Saying so reads as judgement, not ignorance.
10. The system catalog is itself stored as tables (`information_schema`, `sqlite_master`), which is why you can query your own metadata.

### Common wrong answers

| Candidate says | Why it loses marks | Say instead |
|---|---|---|
| "A DBMS removes redundancy" | It **controls** redundancy; some is deliberate (indexes, denormalization, replicas) | "It controls redundancy — you choose where to keep copies, instead of accumulating them accidentally" |
| "DBMS is for small data, RDBMS for big data" | Nothing to do with size | Answer in terms of tables, keys and SQL |
| "Physical data independence is harder" | Backwards | Logical is harder; physical is nearly free |
| "Three-tier means external, conceptual, internal" | Conflates the two architectures | Three-tier = client / app server / DB server |
| "`TRUNCATE` is DML because it deletes rows" | Classified as DDL; it deallocates pages rather than logging per-row deletes | "`TRUNCATE` is DDL — and in most engines it can't be rolled back" |
| "You can always roll back DDL" | False in MySQL and Oracle | Give the dialect split |
| "Schema and database mean the same thing" | In MySQL `CREATE SCHEMA` *is* an alias for `CREATE DATABASE`, but conceptually a schema is the structure | "Conceptually the schema is the structure; confusingly, MySQL uses the word as a synonym for database" |
| "A view stores a copy of the data" | A plain view is a stored **query**; only a *materialized* view stores rows (M6) | — |

### Interview Q&A bank

**Q1. Why use a DBMS instead of files?**
Files give you redundancy, inconsistency, no enforced rules, no concurrency control and no recovery. Two concrete failures: two clerks editing the same record silently overwrite each other, and a power cut halfway through a transfer loses money. A DBMS fixes those with transactions and constraints.
*Follow-up:* "When would you still use a file?" → Single writer, append-only, no query needs: logs, config.

**Q2. DBMS vs RDBMS?**
An RDBMS stores data as tables with explicit key-based relationships and is queried with SQL; a DBMS is the general category. Every RDBMS is a DBMS.
*Follow-up:* "Is MongoDB an RDBMS?" → No — a document store, no relational keys or joins in the relational sense (M10).

**Q3. Explain the three-schema architecture.**
External (what each user group sees, many of them), conceptual (all tables, keys and constraints, exactly one), internal (files, pages, indexes, exactly one). Each level hides the one below — that is data abstraction.
*Follow-up:* "What does it buy you?" → Data independence.

**Q4. Logical vs physical data independence?**
Logical: change the conceptual schema (split a table, add a column) without changing applications — achieved with views. Physical: change storage (add an index, move disks) without changing the conceptual schema. **Logical is the harder one.**
*Follow-up:* "Give me an example of logical independence." → Normalizing one table into two and redefining the view so the application's query is untouched (§0.5).

**Q5. Schema vs instance?**
The schema is the structure and changes rarely; the instance is the data at a moment and changes constantly. Class declaration vs object at runtime.

**Q6. DDL vs DML vs DCL vs TCL — with examples.**
DDL defines structure (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`); DML changes data (`INSERT`, `UPDATE`, `DELETE`); DCL grants privileges (`GRANT`, `REVOKE`); TCL bounds transactions (`COMMIT`, `ROLLBACK`, `SAVEPOINT`). `SELECT` is usually called DQL.
*Follow-up:* "Which family is `TRUNCATE`?" → DDL.

**Q7. Can you roll back a `CREATE TABLE`?**
In MySQL and Oracle no — DDL causes an implicit commit. In PostgreSQL and SQLite yes, DDL is transactional.

**Q8. What does `ROLLBACK TO SAVEPOINT` do?**
Undoes work back to the savepoint and leaves the transaction open, so you can continue or commit the earlier part.

**Q9. Two-tier vs three-tier?**
Two-tier: the client connects to the DB directly, holding credentials and a connection each. Three-tier: an application server sits between, so the DB is never exposed to clients and connections are pooled.

**Q10. What is metadata? Where does the DBMS keep it?**
Data about the data — schema, types, constraints, statistics — stored in the system catalog, itself queryable as tables (`information_schema`, `sqlite_master`).

**Q11. Name the data models and why relational won.**
Hierarchical (tree, no M:N), network (graph, pointer-chasing), relational (tables + keys + SQL), object-oriented, and the NoSQL families. Relational won because you *describe* the result instead of *navigating* to it.

**Q12. What are the disadvantages of a DBMS?**
Cost and administration, overhead for trivial workloads, schema rigidity at scale, and it becomes a central bottleneck — which is what sharding and replication address (M10).

### Practice

1. Take a college result sheet kept as three spreadsheets (students, marks, fees). Name one *specific* anomaly each of the six file-system problems in §0.1 would cause.
2. Classify each as DDL, DML, DCL, TCL or DQL: `ALTER TABLE`, `GRANT SELECT`, `SAVEPOINT a`, `TRUNCATE TABLE`, `UPDATE`, `SELECT`, `DROP VIEW`, `COMMIT`.
3. Your application runs `SELECT id, total FROM v_order_summary`. The DBA wants to split `orders` into `orders` + `order_items`. What must the DBA do so your code is untouched, and which kind of data independence is that?
4. Run the savepoint example yourself, then predict the state before each `SELECT` and check.
5. Someone claims "we added an index, so now the application must be changed". Which kind of data independence proves them wrong?
6. Which of these are schema changes and which are instance changes: adding a column; inserting 10,000 rows; renaming a table; deleting all rows; adding a `CHECK` constraint.

---

## Exit checklist

```
[ ] I can give two concrete file-system failures and the DBMS feature that fixes each
[ ] I can draw the three-schema architecture and say how many of each level exist
[ ] I can define both kinds of data independence and say which is harder, and why
[ ] I can explain logical data independence with the view example
[ ] I can distinguish three-SCHEMA from three-TIER without hesitating
[ ] I can classify any SQL statement into DDL / DML / DCL / TCL / DQL
[ ] I know TRUNCATE is DDL
[ ] I can state the DDL-rollback answer for MySQL, Oracle, Postgres and SQLite
[ ] I can say what ROLLBACK TO SAVEPOINT leaves behind
[ ] I can name three honest disadvantages of using a DBMS
```

---

## Next

**Part 3: M1 — Relational Model and Keys.** The relational model properly: relations, tuples, degree and cardinality; then the whole key family (super → candidate → primary → alternate → composite → surrogate → foreign) as a single picture rather than seven definitions; the four integrity constraints; **NULL and three-valued logic**, including why `NOT IN` with a NULL silently returns nothing; and the referential actions (`CASCADE`, `SET NULL`, `RESTRICT`) with each one's effect demonstrated.
