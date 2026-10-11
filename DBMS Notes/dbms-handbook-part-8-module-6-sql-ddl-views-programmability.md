# DBMS Placement Handbook — Part 8
# Module 6: SQL III — DDL, Constraints, Views and Programmability

**Module 6 · 3 hours · Tier 1/2 · Requires: M1 (keys and constraints), M4 (query basics), M5 (joins, for view definitions)**

---

## Why this module matters

M4 and M5 were about *reading* data. This module is about everything else SQL does: creating the structures, protecting them with constraints, hiding them behind views, attaching behaviour with triggers, handing out permissions — and the one security topic that comes up in DBMS interviews far more often than its size suggests, **SQL injection**.

The weighting here is unusual, so be deliberate about it:

- **`DELETE` vs `TRUNCATE` vs `DROP`** is probably the single most-asked DBMS one-liner in Indian placement interviews. It is worth memorising cold.
- **Views** and **SQL injection** are near-certain follow-ups.
- **Triggers, stored procedures, cursors** get asked as "what is X and when would you use it" — you need a crisp definition and one honest opinion, not syntax mastery.
- **`GRANT`/`REVOKE`** is usually one sentence.

So this is a **small-effort, high-yield module**. Learn the tables, run the injection demo once, and move on.

The organising principle:

> **DDL changes the shape of the database, DML changes the contents, DCL changes who may touch it, and TCL decides when changes become real. A view is a stored query, not stored data. A trigger is code the database runs for you whether you wanted it to or not — which is both its value and its danger. And every injection vulnerability in history comes from the same mistake: building SQL by concatenating strings instead of sending values as parameters.**

**Everything in §6.1–§6.5 and §6.7–§6.8 was executed** (Python 3.12 `sqlite3`, SQLite 3.49.1). Where SQLite genuinely cannot do something — `TRUNCATE`, stored procedures, `GRANT` — it is **labelled as not executed** and the dialect syntax is given from documentation. Nothing is presented as verified when it is not.

---

## 6.1 DDL: `CREATE`, `ALTER`, `DROP`

The four command families from M0, in one reminder:

```
DDL  CREATE  ALTER  DROP  TRUNCATE  RENAME        structure
DML  SELECT  INSERT  UPDATE  DELETE               contents
DCL  GRANT  REVOKE                                permissions
TCL  COMMIT  ROLLBACK  SAVEPOINT                  when changes become real
```

(`SELECT` is sometimes called DQL and split out. If an interviewer insists on four families with `SELECT` inside DML, agree and move on — it is a naming convention, not a concept.)

### A `CREATE TABLE` with every clause worth knowing

```sql
CREATE TABLE emp(
  eid     INTEGER PRIMARY KEY,
  name    TEXT NOT NULL,
  did     INTEGER,
  salary  INTEGER DEFAULT 30000 CHECK (salary > 0),
  CONSTRAINT fk_dept FOREIGN KEY (did) REFERENCES dept(did) ON DELETE SET NULL
);
```

Five things are happening: a **primary key**, a **`NOT NULL`**, a **`DEFAULT`**, a **`CHECK`**, and a **named foreign key with a referential action**. Verified that the default actually applies when the column is omitted:

```
DEFAULT: [(1, 30000, 1)]        -- id given, salary and timestamp filled by DEFAULT
```

A `DEFAULT` may be a literal or an expression (`DEFAULT (datetime('now'))`). It fires **only when the column is absent from the `INSERT`** — inserting an explicit `NULL` stores `NULL`, it does not trigger the default. That is a common trap.

### `ALTER TABLE` — and the part nobody tells you

The standard operations:

```sql
ALTER TABLE emp ADD COLUMN city TEXT DEFAULT 'Pune';
ALTER TABLE emp RENAME COLUMN city TO location;
ALTER TABLE emp DROP COLUMN location;
ALTER TABLE dept RENAME TO department;
```

All four verified in SQLite 3.49.1:

```
-- after ADD COLUMN: [(1, 'Asha', 'Pune'), (2, 'Ravi', 'Pune'), (3, 'Dev', 'Pune')]
-- sqlite_master names: ['department', 'emp']
-- after DROP COLUMN: ['eid', 'name', 'did', 'salary']
```

One pleasant surprise worth knowing: **renaming a table fixes the foreign keys that point at it.** After `ALTER TABLE dept RENAME TO department`, the stored DDL of `emp` had been rewritten:

```
fk_dept foreign key (did) references "department"(did) on delete set null
```

And the limits — these three were **rejected**:

```
REJECTED: alter table emp alter column salary text  -> near "alter": syntax error
REJECTED: alter table emp modify salary text        -> near "modify": syntax error
REJECTED: alter table emp add constraint chk_name check (length(name) > 1)
                                                    -> near "constraint": syntax error
```

So SQLite can add, drop and rename columns, but **cannot change a column's type and cannot add a constraint after the fact**. The workaround is the "12-step dance" from the SQLite docs: create a new table with the right shape, `INSERT INTO new SELECT ... FROM old`, drop the old, rename the new.

### `ALTER` support by engine

| Operation | SQLite | MySQL | PostgreSQL | Oracle |
|---|---|---|---|---|
| Add column | ✅ `ADD COLUMN` | ✅ `ADD COLUMN` | ✅ `ADD COLUMN` | ✅ `ADD` |
| Drop column | ✅ (3.35+) | ✅ | ✅ | ✅ |
| Rename column | ✅ (3.25+) | ✅ `RENAME COLUMN` (8.0+) | ✅ | ✅ |
| Change column type | ❌ | ✅ `MODIFY` / `CHANGE` | ✅ `ALTER COLUMN ... TYPE` | ✅ `MODIFY` |
| Add constraint later | ❌ | ✅ `ADD CONSTRAINT` | ✅ `ADD CONSTRAINT` | ✅ `ADD CONSTRAINT` |
| Drop constraint | ❌ | ✅ | ✅ | ✅ |

**Interview-safe answer:** `ALTER TABLE` adds, drops, renames and retypes columns and adds or drops constraints — with SQLite the notable exception, since it cannot retype a column or add a constraint and needs a table rebuild instead.

---

## 6.2 `DELETE` vs `TRUNCATE` vs `DROP` — the one to memorise

This is the most-asked question in the module. Learn the table, not a paragraph.

| | `DELETE FROM t` | `TRUNCATE TABLE t` | `DROP TABLE t` |
|---|---|---|---|
| **Command family** | DML | DDL | DDL |
| **Removes** | Rows (chosen by `WHERE`) | All rows | Rows **and** the table itself |
| **`WHERE` allowed** | ✅ Yes | ❌ No | ❌ No |
| **Table exists after** | ✅ Yes, empty | ✅ Yes, empty | ❌ Gone |
| **Structure / indexes / constraints** | Kept | Kept | Gone |
| **Views and privileges on it** | Kept | Kept | Dropped or left invalid |
| **Speed on a big table** | Slow — row by row | Fast — deallocates pages | Fast |
| **Logging** | Each row logged individually | Minimal (page deallocation) | Minimal |
| **Fires `DELETE` triggers** | ✅ Yes | ❌ No | ❌ No |
| **Rollback-able** | ✅ Always | Engine-dependent (see below) | Engine-dependent |
| **Resets `AUTO_INCREMENT`/identity** | ❌ No | ✅ Yes | n/a — table gone |
| **Blocked by an inbound FK** | Only if a row is referenced | Usually blocked outright | Blocked unless `CASCADE` |

### Verified: `DELETE` is transactional and keeps the counter

```
-- rows: [(1, 'a'), (2, 'b'), (3, 'c')]
-- sqlite_sequence after insert: [('t', 3)]
-- mid-transaction after DELETE one row: [(1, 'a'), (3, 'c')]
-- after ROLLBACK -> DELETE was undone: [(1, 'a'), (2, 'b'), (3, 'c')]
-- after DELETE FROM t (all rows): []
-- sqlite_sequence still remembers: [('t', 3)]
-- next insert reuses counter -> id: [(4, 'd')]
```

Read the last three lines carefully: after deleting *every* row, the next inserted row got **`id = 4`, not `id = 1`**. `DELETE` does not touch the identity counter. `TRUNCATE` does — that is one of the real behavioural differences, not just a performance note.

Also verified that the schema survives:

```
schema survives DELETE: (3,)     -- 3 columns still defined after DELETE FROM e
```

### Verified: SQLite has no `TRUNCATE`

```
REJECTED: truncate table t -> near "truncate": syntax error (SQLite has no TRUNCATE)
```

SQLite's optimiser instead has a **"truncate optimization"**: a `DELETE FROM t` with no `WHERE` and no triggers is internally executed as a bulk page drop rather than row-by-row. So you get `TRUNCATE`'s speed from `DELETE`'s syntax — but still with `DELETE`'s semantics (rollback-able, counter not reset).

### Verified: `DROP`, and DDL rollback

```
-- tables after DROP: ['sqlite_sequence']
REJECTED: select from dropped table -> no such table: t
-- DROP inside a transaction, rolled back -> table back?: ['sqlite_sequence', 'keepme']
```

That last line is the dialect point from M0 again, now shown for `DROP`: in **SQLite and PostgreSQL, DDL is transactional**, so a `DROP TABLE` inside a transaction can be rolled back and the table comes back. In **MySQL and Oracle, DDL causes an implicit commit** — the `DROP` is permanent the instant it runs, and any `ROLLBACK` afterwards has nothing left to undo.

| Engine | Can you roll back `TRUNCATE`? | Can you roll back `DROP TABLE`? |
|---|---|---|
| **PostgreSQL** | ✅ Yes (DDL is transactional) | ✅ Yes |
| **SQLite** | n/a (no `TRUNCATE`) | ✅ Yes |
| **SQL Server** | ✅ Yes, inside an explicit transaction | ✅ Yes |
| **MySQL / InnoDB** | ❌ No — implicit commit | ❌ No — implicit commit |
| **Oracle** | ❌ No — implicit commit | ❌ No — implicit commit |

**How to answer when asked "is `TRUNCATE` rollback-able?"** Say: *"`TRUNCATE` is DDL, so in MySQL and Oracle it causes an implicit commit and cannot be rolled back; in PostgreSQL and SQL Server, where DDL is transactional, it can be. The textbook answer taught in India is 'no', because it is based on Oracle and MySQL."* That answer is correct everywhere and shows you know why the textbook says what it says.

---

## 6.3 Constraints in practice

M1 covered what constraints *mean*. Here is how they are written and what happens when each is violated — all verified against one real schema:

```sql
CREATE TABLE enroll(
  roll INTEGER, cid TEXT, grade TEXT,
  CONSTRAINT pk_enroll PRIMARY KEY (roll, cid),
  CONSTRAINT fk_roll   FOREIGN KEY (roll) REFERENCES student(roll) ON DELETE CASCADE,
  CONSTRAINT fk_cid    FOREIGN KEY (cid)  REFERENCES course(cid)  ON DELETE RESTRICT,
  CONSTRAINT chk_grade CHECK (grade IN ('A','B','C','D','F'))
);
```

Four deliberate violations, four real error messages:

```
REJECTED [duplicate composite PK]: UNIQUE constraint failed: enroll.roll, enroll.cid
REJECTED [CHECK violation]:        CHECK constraint failed: chk_grade
REJECTED [FK violation (no student 9)]: FOREIGN KEY constraint failed
REJECTED [ON DELETE RESTRICT]:     FOREIGN KEY constraint failed
-- ON DELETE CASCADE removed Asha's enrolments: [(2, 'CS101', 'C')]
-- named constraint visible in DDL: True
```

### Why you should name your constraints

Compare the two error messages above. `CHECK constraint failed: chk_grade` tells you exactly which rule broke. An unnamed check gives you something like `CHECK constraint failed: enroll` — the table, not the rule. On a table with six checks, that is the difference between a one-minute fix and a twenty-minute hunt.

Naming also gives you a handle to drop it later: `ALTER TABLE enroll DROP CONSTRAINT chk_grade` (in engines that support it).

### Column-level vs table-level

```sql
-- column-level: applies to the one column it sits on
salary INTEGER CHECK (salary > 0)

-- table-level: required when the rule spans columns
CONSTRAINT chk_dates CHECK (end_date > start_date)
CONSTRAINT pk_enroll PRIMARY KEY (roll, cid)
```

A **composite** primary key, unique or foreign key *must* be table-level — there is no way to write a two-column constraint on one column.

### `DEFERRABLE` constraints (Tier 3, one line)

PostgreSQL and Oracle let a foreign key be `DEFERRABLE INITIALLY DEFERRED`, meaning it is checked at `COMMIT` rather than per statement — which is how you insert two rows that reference each other. SQLite supports `DEFERRABLE INITIALLY DEFERRED` on foreign keys too; MySQL ignores it. Mention it only if asked about circular references.

---

## 6.4 Views

A **view** is a named stored query. It stores the SQL text, not the rows.

```sql
CREATE VIEW v_simple AS
  SELECT eid, name, salary FROM emp WHERE salary > 70000;

CREATE VIEW v_agg AS
  SELECT d.dname, COUNT(*) n, AVG(e.salary) avg_sal
  FROM dept d JOIN emp e ON e.did = d.did
  GROUP BY d.dname;
```

Querying them, verified:

```
-- v_simple: [(1, 'Asha', 90000), (2, 'Ravi', 75000)]
-- v_agg: [('Engineering', 2, 82500.0), ('Sales', 1, 60000.0)]
```

### A view is a query, not a copy — proof

Give Dev a raise from 60000 to 99000, then re-read the view **without touching it**:

```
-- v_simple after Dev's raise: [(1, 'Asha', 90000), (2, 'Ravi', 75000), (3, 'Dev', 99000)]
```

Dev appeared in the view because the view's `WHERE salary > 70000` is re-evaluated on every read. This is the whole mental model: **a view is substituted into your query like a macro.** If you remember that, every other fact about views follows.

### Why views exist — four real reasons

| Reason | What it buys you |
|---|---|
| **Security** | Grant access to `v_emp_public` (name, department) instead of `emp` (which has salary). Column- and row-level security without changing the table. |
| **Simplification** | A six-table join that analysts need weekly becomes `SELECT * FROM v_monthly_report`. |
| **Logical data independence** | Split a table in two, redefine the view to join them, and every query written against the view keeps working. This is the M0 demonstration — views are *the mechanism* that makes the three-schema architecture real. |
| **Backward compatibility** | Renamed a column? Keep a view with the old name so old code keeps running while you migrate. |

What views do **not** buy you: speed. A normal view runs its definition every time, so it is exactly as fast as the query inside it. If someone says "I made it a view so it's faster", they are wrong — unless they mean a *materialized* view.

### When is a view updatable?

Verified in SQLite — all four attempts rejected:

```
REJECTED [INSERT through a view]: cannot modify v_simple because it is a view
REJECTED [UPDATE through a view]: cannot modify v_simple because it is a view
REJECTED [DELETE through a view]: cannot modify v_simple because it is a view
REJECTED [UPDATE through an aggregate view]: cannot modify v_agg because it is a view
```

**SQLite views are always read-only.** That is a SQLite restriction, not a general rule, so do not learn the lesson from that output. The general rule — the one to give in an interview — is:

> A view is updatable when the database can translate one row of the view back to **exactly one row of exactly one base table**. Anything that destroys that one-to-one mapping makes it read-only.

What destroys it:

| Feature in the view | Updatable? | Why |
|---|---|---|
| Single table, plain columns, `WHERE` | ✅ Yes | One view row ↔ one base row |
| `DISTINCT` | ❌ No | One view row may stand for many base rows |
| `GROUP BY` / `HAVING` / aggregate | ❌ No | One view row summarises many base rows |
| Window function | ❌ No | Value depends on other rows |
| `UNION` / `UNION ALL` | ❌ No | Which branch would the write go to? |
| Join of two tables | ⚠️ Sometimes | PostgreSQL: no (without a rule/trigger). MySQL: yes, if the write touches only one table |
| A derived/computed column (`salary*12`) | ⚠️ That column no | You cannot write to `salary*12`; other columns may still be writable |
| Missing a `NOT NULL` base column with no default | ⚠️ `INSERT` no | The hidden column would have to be `NULL` |

### `WITH CHECK OPTION`

A subtle trap worth one sentence. A view defined as `WHERE salary > 70000` will, by default, happily let you `UPDATE` a row to `salary = 100` — and the row then **vanishes from the view**. `WITH CHECK OPTION` forbids any write that would produce a row the view cannot see:

```sql
CREATE VIEW v_rich AS SELECT * FROM emp WHERE salary > 70000
  WITH CHECK OPTION;
```

(Not executable in SQLite, which has no updatable views at all. MySQL, PostgreSQL, Oracle and SQL Server all support it.)

### Making a read-only view writable: `INSTEAD OF` triggers

SQLite's own escape hatch, and the standard answer to "can you update a complex view?" — **verified**:

```sql
CREATE TRIGGER v_simple_ins INSTEAD OF INSERT ON v_simple
BEGIN
  INSERT INTO emp(eid, name, did, salary) VALUES (new.eid, new.name, 10, new.salary);
END;
```

```
-- emp after insert through the view:
   [(1,'Asha',10,90000), (2,'Ravi',10,75000), (3,'Dev',20,99000), (4,'Nita',10,80000)]
-- v_simple: [(1,'Asha',90000), (2,'Ravi',75000), (3,'Dev',99000), (4,'Nita',80000)]
```

An `INSTEAD OF` trigger replaces the write entirely: the database does not attempt the view write at all, it just runs your code. This is how any view — joins, unions, aggregates — can be made writable: **you supply the mapping the database could not infer.** PostgreSQL does the same thing with `INSTEAD OF` triggers or `CREATE RULE`.

### Materialized views

A **materialized view** stores the *result*, not the query. Reads are fast because nothing is recomputed; the cost is **staleness** and a refresh.

SQLite has none — verified:

```
REJECTED: create materialized view -> near "materialized": syntax error
```

So here it is emulated with a table, which is exactly what the feature does internally:

```
-- mv_agg (snapshot): [('Engineering', 3, 81666.67), ('Sales', 1, 99000.0)]
   ... then Dev's salary drops to 10000 ...
-- live view after change : [('Engineering', 3, 81666.67), ('Sales', 1, 10000.0)]
-- snapshot is now stale  : [('Engineering', 3, 81666.67), ('Sales', 1, 99000.0)]
-- after refresh          : [('Engineering', 3, 81666.67), ('Sales', 1, 10000.0)]
```

The stale line is the whole point of the concept. A materialized view is a **cache**, with every trade-off a cache has.

| | View | Materialized view |
|---|---|---|
| Stores | The SQL text | The result rows |
| Read cost | Runs the query every time | A table scan / index read |
| Freshness | Always current | As of the last refresh |
| Disk | ~0 | Full result size |
| Needs refresh | No | Yes — manual, scheduled, or incremental |
| Can be indexed | Only via the base tables | ✅ Yes, directly |
| Support | Everywhere | PostgreSQL, Oracle, SQL Server (as an indexed view); **MySQL and SQLite: no** |

Use a materialized view when the query is expensive, read often, and tolerates being a few minutes old — dashboards, daily reports, rollups.

---

## 6.5 Programmability: procedures, functions, triggers, cursors

### Stored procedure vs function

**Not executable in SQLite** — it has no procedural language at all. The syntax below is MySQL's, given from documentation and marked as unverified. The *comparison*, which is what gets asked, is dialect-independent.

```sql
-- MySQL (NOT executed here)
DELIMITER //
CREATE PROCEDURE give_raise(IN p_eid INT, IN p_pct INT)
BEGIN
  UPDATE emp SET salary = salary * (1 + p_pct/100) WHERE eid = p_eid;
END //
DELIMITER ;

CALL give_raise(2, 10);

CREATE FUNCTION annual(p_salary INT) RETURNS INT DETERMINISTIC
  RETURN p_salary * 12;

SELECT name, annual(salary) FROM emp;      -- usable inside a query
```

| | Stored procedure | Function |
|---|---|---|
| **Called with** | `CALL p(...)` — a statement of its own | Inside an expression: `SELECT f(x) ...` |
| **Returns** | Zero, one or many values via `OUT` params; can return result sets | Exactly one value (or a table, in some engines) |
| **Usable in `SELECT`/`WHERE`** | ❌ No | ✅ Yes |
| **Can modify data (DML)** | ✅ Yes — that is the usual purpose | ❌ Usually not (Postgres functions can; MySQL forbids it in a function called from a query) |
| **Transaction control inside** | ✅ Can `COMMIT`/`ROLLBACK` | ❌ No |
| **Parameters** | `IN`, `OUT`, `INOUT` | `IN` only |
| **Typical use** | A business operation: "transfer money", "close the month" | A computation: "annualise this", "format this name" |

**One-line interview answer:** *"A procedure is an action you call; a function is a value you use in an expression. Procedures can write and control transactions, functions are meant to compute and be callable from a query."*

Honest opinion worth having ready, because good interviewers ask for it: **stored procedures are much less fashionable than they were.** Putting business logic in the database makes it hard to version-control, test, and deploy alongside application code, and it ties you to one vendor's procedural dialect. They are still right for logic that must be atomic and close to the data, or where many different applications share one database. If asked "would you use them?", that is the answer — not a flat yes or no.

### Triggers

A trigger is code the database runs automatically on an event. Six firing points: `BEFORE`/`AFTER` × `INSERT`/`UPDATE`/`DELETE` (plus `INSTEAD OF` on views).

Verified — an audit trigger and a validation trigger:

```sql
CREATE TRIGGER trg_audit AFTER UPDATE OF balance ON account
BEGIN
  INSERT INTO audit VALUES (..., old.aid, old.balance, new.balance, 'update');
END;

CREATE TRIGGER trg_no_negative BEFORE UPDATE OF balance ON account
WHEN new.balance < 0
BEGIN
  SELECT RAISE(ABORT, 'balance cannot go negative');
END;
```

```
-- accounts: [(1, 'Asha', 4000), (2, 'Ravi', 3500)]
-- audit log: [(1, 1, 5000, 4000, 'update'), (2, 2, 3000, 3500, 'update')]
REJECTED by BEFORE trigger: balance cannot go negative
-- balance unchanged after abort: [(1, 'Asha', 4000)]
-- audit got no row for the aborted update: (2,)
-- audit after delete: [..., (3, 2, 3500, None, 'delete')]
```

Three things that output proves:

1. **`old` and `new` are how you see the row.** `old` exists for `UPDATE` and `DELETE`, `new` for `INSERT` and `UPDATE`. Asking for `new` in a `DELETE` trigger is an error.
2. **A `BEFORE` trigger can veto the operation.** `RAISE(ABORT, ...)` stopped the update; the balance is untouched.
3. **The audit table got no row for the aborted update** — count stayed at 2. The trigger and the statement are in **one transaction**: abort the statement, and the trigger's own writes roll back too. That is a real interview question ("if a trigger fails, is the original statement rolled back?") and the answer is yes.

**`BEFORE` vs `AFTER`:** use `BEFORE` to validate or modify the row on its way in (it can still be stopped); use `AFTER` for consequences — audit rows, denormalized counters, notifications — because by then the row is known to be good.

#### A finding worth knowing: multi-trigger order is not defined

I created two `AFTER INSERT` triggers on the same table and checked which ran first:

```
('b_first', 'a_second') -> fired: ['a_second', 'b_first']
('a_first', 'b_second') -> fired: ['b_second', 'a_first']
('zzz',     'aaa')      -> fired: ['aaa', 'zzz']
```

Not alphabetical, not creation order — SQLite fired the **most recently created trigger first**, consistently. The SQL standard leaves the order of multiple triggers on the same event **unspecified**, and engines differ: MySQL fires them in creation order and offers `FOLLOWS`/`PRECEDES` to control it; SQLite, as shown, is reverse-creation and documents the order as undefined.

**Practical rule:** never write two triggers on the same event that depend on running in a particular order. If the order matters, make it one trigger.

#### Why triggers get a bad reputation

Worth being able to say out loud, because "when would you *not* use a trigger?" is the real question:

- **Invisible control flow.** A simple `UPDATE` silently causes five more writes. Nothing in the application code hints at it, so debugging means knowing to go look.
- **Hidden cost.** A trigger on a hot table multiplies every write.
- **Cascades.** A trigger that writes to a table with its own trigger… SQLite guards this with `PRAGMA recursive_triggers` (off by default) and a depth limit; other engines error at a nesting cap.
- **Bulk-load surprise.** `TRUNCATE` skips `DELETE` triggers entirely (§6.2), so an audit trail built on triggers has a hole in it exactly when someone clears the table.

Good uses: audit trails, enforcing an invariant that a `CHECK` cannot express, and `INSTEAD OF` on views. Bad uses: business logic, anything the application could do explicitly.

### Cursors

A **cursor** is a pointer that walks a result set one row at a time, so procedural code can process rows individually.

```sql
-- MySQL-flavour sketch (NOT executed; SQLite has no procedural cursors)
DECLARE cur CURSOR FOR SELECT eid, salary FROM emp;
OPEN cur;
read_loop: LOOP
  FETCH cur INTO v_eid, v_salary;
  ...
END LOOP;
CLOSE cur;
```

| | Implicit cursor | Explicit cursor |
|---|---|---|
| Declared by | The engine, for every DML statement | You, with `DECLARE` |
| Control | None | `OPEN` / `FETCH` / `CLOSE` |
| Use | Automatic | Row-at-a-time processing |

The only opinion you need: **a cursor is almost always the wrong tool.** SQL is set-based; a cursor turns one set operation into *n* round trips. "Row-by-agonising-row" (RBAR) is the standard joke. Use a single `UPDATE ... WHERE`, a `CASE`, or a window function instead. Legitimate cursor uses are rare: calling an external service per row, or a migration that must be chunked to avoid one enormous transaction.

Note the word is overloaded — the `cursor` object in Python's DB-API (used throughout this handbook) is a client-side result handle, not a server-side SQL cursor. If an interviewer says "cursor", they mean the SQL one.

---

## 6.6 TCL: `COMMIT`, `ROLLBACK`, `SAVEPOINT`

Full treatment is M8. Here is the syntax layer, verified:

```sql
BEGIN;
  INSERT INTO t VALUES ('one');
  SAVEPOINT sp1;
  INSERT INTO t VALUES ('two');
  SAVEPOINT sp2;
  INSERT INTO t VALUES ('three');
  ROLLBACK TO sp2;      -- undoes 'three' only
  ROLLBACK TO sp1;      -- undoes 'two' as well
COMMIT;                 -- 'base' and 'one' survive
```

```
-- before any rollback: ['base', 'one', 'two', 'three']
-- rollback to sp2     : ['base', 'one', 'two']
-- rollback to sp1     : ['base', 'one']
-- after commit        : ['base', 'one']
```

A `SAVEPOINT` is a **partial rollback point inside** a transaction. `ROLLBACK TO sp` undoes everything after `sp` but leaves the transaction open and running — unlike a plain `ROLLBACK`, which ends it. `RELEASE sp` discards the savepoint without undoing anything.

The practical use: a long transaction where one optional step may fail. Set a savepoint, try the step, roll back to the savepoint if it fails, and carry on with the rest of the transaction rather than losing all the work.

---

## 6.7 DCL: `GRANT` and `REVOKE`

**Not executable in SQLite** — verified, with the reason:

```
REJECTED: grant select on t to analyst -> near "grant": syntax error
```

SQLite is a library writing to a file, not a server. It has no concept of a database user, so permissions are the *file system's* job. Every server engine has DCL:

```sql
-- NOT executed here; standard/MySQL syntax
GRANT SELECT, INSERT ON company.emp TO 'analyst'@'localhost';
GRANT SELECT (name, did) ON company.emp TO 'intern'@'%';   -- column-level
GRANT ALL PRIVILEGES ON company.* TO 'admin'@'localhost' WITH GRANT OPTION;

CREATE ROLE reporting;
GRANT SELECT ON company.v_monthly TO reporting;
GRANT reporting TO 'analyst'@'localhost';

REVOKE INSERT ON company.emp FROM 'analyst'@'localhost';
```

Three terms that get asked:

- **`WITH GRANT OPTION`** — the grantee may pass the privilege on to others. Revoking from the middle person cascades: the privileges they granted disappear too.
- **A role** is a named bundle of privileges granted to users, so you manage one role instead of fifty accounts. The reason roles exist is the same reason groups exist in an OS.
- **Principle of least privilege** — the application's database user should have exactly the rights the application needs. The application almost never needs `DROP`. This is also the second line of defence against SQL injection: even a successful injection cannot drop a table the account cannot drop.

---

## 6.8 SQL injection and prepared statements

High-yield, cheap to learn, and the one place in DBMS where a wrong answer looks genuinely bad. Everything below is **real output**.

### The vulnerable function

```python
def unsafe_login(conn, u, p):
    q = f"select uid, uname, role from users where uname = '{u}' and pwd = '{p}'"
    return conn.execute(q).fetchall()
```

The flaw is one idea: the user's input is **pasted into the SQL text**, so the input can stop being data and start being code.

The table:

```
users
uid | uname | pwd     | role
----+-------+---------+-------
1   | asha  | s3cret  | admin
2   | ravi  | hunter2 | user
3   | dev   | letmein | user
```

### a) Honest use — both work

```
SQL sent: select uid, uname, role from users where uname = 'asha' and pwd = 's3cret'
-- unsafe: [(1, 'asha', 'admin')]
-- safe  : [(1, 'asha', 'admin')]
```

```
SQL sent: ... where uname = 'asha' and pwd = 'wrong'
-- unsafe: []
-- safe  : []
```

So far indistinguishable. Vulnerabilities are invisible until someone looks for them — which is why "it works" is not evidence.

### b) The tautology: password = `' OR '1'='1`

```
SQL sent: select uid, uname, role from users where uname = 'asha' and pwd = '' OR '1'='1'
-- unsafe: [(1, 'asha', 'admin'), (2, 'ravi', 'user'), (3, 'dev', 'user')]
-- safe  : []
```

Read the generated SQL. The attacker's quote closed the `pwd` string early, and `OR '1'='1'` became part of the `WHERE` clause. **The entire user table came back with no valid password.** The parameterized version returned nothing at all, because it looked for a user whose literal password is the string `' OR '1'='1`.

### c) Commenting out the rest: username = `asha'--`

```
SQL sent: select uid, uname, role from users where uname = 'asha'--' and pwd = 'anything'
-- unsafe: [(1, 'asha', 'admin')]
-- safe  : []
```

`--` starts a SQL comment, so **the password check no longer exists**. Logged in as the admin with no password at all. This is the classic auth bypass.

### d) `UNION` injection — reading data the query never mentioned

```
SQL sent: select uid, uname, role from users
          where uname = 'x' union select uid, pwd, role from users --' and pwd = 'y'
-- unsafe LEAKED PASSWORDS: [(1, 's3cret', 'admin'), (2, 'hunter2', 'user'), (3, 'letmein', 'user')]
```

Every password in the table, returned through a login form. A `UNION` needs matching column counts and compatible types, which is exactly what an attacker probes for first. Note the escalation: (b) and (c) were an auth bypass; this is **data exfiltration**, and the same hole gives you both.

### e) The stacked statement — and a lesson about defence depth

```
SQL sent: select uid, uname, role from users where uname = 'x'; drop table users; --' and pwd = 'y'
   sqlite3 execute() refused: ProgrammingError You can only execute one statement at a time.
-- users table still there: (3,)
   but executescript() (multi-statement) would run it:
-- tables: ['users', 'pwned']
```

This is the honest version of the famous `'; DROP TABLE users; --`. Python's `sqlite3.execute()` **refuses to run two statements**, so the drop failed — a *driver* protection, not a fix for the vulnerability. Switch to a multi-statement API (`executescript`, or MySQL with `CLIENT_MULTI_STATEMENTS` enabled) and the same input destroys the table. The code was equally broken in both cases; one driver just happened to be in the way.

### f) Why hand-escaping quotes is not the fix

```
SQL sent: select uid, uname, role from users where uid = 2
-- unsafe_numeric('2'): [(2, 'ravi', 'user')]

SQL sent: select uid, uname, role from users where uid = 2 or 1=1
-- unsafe_numeric('2 or 1=1'): [(1, 'asha', 'admin'), (2, 'ravi', 'user'), (3, 'dev', 'user')]
```

A numeric field is interpolated **without quotes**, so there is nothing to escape and `2 or 1=1` walks straight in. Any "I escape quotes" or "I strip apostrophes" defence dies here. Blacklisting is the same story: you are trying to enumerate every way to write an attack, and the attacker only needs one you missed.

### The fix: parameterized (prepared) statements

```python
def safe_login(conn, u, p):
    q = "select uid, uname, role from users where uname = ? and pwd = ?"
    return conn.execute(q, (u, p)).fetchall()
```

Every attack above returned `[]` against this.

**Why it works, and this is the sentence to say in an interview:** the SQL string with its placeholders is sent to the database and **parsed into a query plan first**. The parameters are supplied afterwards, as *values* bound into that already-fixed plan. There is no later moment at which the database re-reads the input as SQL — so no input, however crafted, can change the structure of the query. It is not about escaping dangerous characters; it is that **data and code travel separately**.

Placeholder syntax by driver: `?` (SQLite, JDBC), `%s` (Python MySQL/psycopg2 — *not* Python `%` formatting, pass a tuple), `:name` (Oracle, named style), `$1` (PostgreSQL wire protocol).

A free bonus: a prepared statement can be parsed once and executed many times with different parameters, so the loop that inserts 10,000 rows is also faster.

### What a parameter cannot do

```
REJECTED: select * from ? -> OperationalError near "?": syntax error
```

**A placeholder stands in for a value, never for an identifier.** You cannot parameterize a table name, a column name, `ASC`/`DESC`, or the column in `ORDER BY`. Those are structure, and structure is fixed at parse time — which is the same reason parameters are safe.

So when you genuinely need a dynamic column name (a sortable table UI), the only safe approach is a **whitelist**:

```python
SORTABLE = {"name", "salary", "hired"}          # allow-list, not escaping
if col not in SORTABLE:
    raise ValueError(col)
q = f"select * from emp order by {col} desc"    # safe: col is one of three known strings
```

### Defence in depth — the full answer

Prepared statements are the fix. These reduce the damage when something else goes wrong:

| Layer | What it does |
|---|---|
| **Parameterized statements** | The actual fix. Non-negotiable. |
| **Least privilege** (§6.7) | The app's user cannot `DROP`, cannot read other schemas. An injection that does get through hits a wall. |
| **Input validation** | An `age` field should be an integer. Validate type and range because it is correct, not as a security control. |
| **Stored procedures** | Help only if they parameterize internally. A procedure that concatenates its arguments into dynamic SQL is just as vulnerable. |
| **ORMs / query builders** | Parameterize by default — but `raw()` / `.query(f"...")` escape hatches are a very common real-world hole. |
| **Generic error messages** | Verbose SQL errors tell an attacker your column names and types. |
| **WAF** | Catches known patterns. Bypassable. Never the primary defence. |
| **Hash passwords** | Orthogonal, but note that in demo (d) the leak was plaintext passwords. With `bcrypt` the leak is far less useful. |

---

## Must remember

```
DDL CREATE/ALTER/DROP/TRUNCATE | DML SELECT/INSERT/UPDATE/DELETE
DCL GRANT/REVOKE               | TCL COMMIT/ROLLBACK/SAVEPOINT

DELETE   DML, WHERE allowed, fires triggers, rollback-able, keeps identity counter, slow
TRUNCATE DDL, all rows, no triggers, usually no rollback, RESETS identity, fast
DROP     DDL, removes table + indexes + constraints + privileges

DEFAULT applies only when the column is OMITTED -- an explicit NULL stores NULL
Name your constraints: the error message then names the rule, not just the table
Composite PK / UNIQUE / FK must be written table-level

A view is stored SQL, not stored rows -- substituted into your query like a macro
A view is updatable iff one view row maps to exactly one base-table row
   killed by: DISTINCT, GROUP BY, aggregate, window, UNION, (usually) joins
WITH CHECK OPTION: refuse writes that would make the row leave the view
Materialized view = cached result: fast reads, stale data, needs refresh
   PostgreSQL/Oracle/SQL Server yes; MySQL and SQLite no

Procedure = an action you CALL; function = a value you use in an expression
   procedure: can do DML + transaction control, IN/OUT/INOUT, not in SELECT
   function:  one return value, usable in SELECT/WHERE, no transaction control
Trigger: BEFORE/AFTER x INSERT/UPDATE/DELETE, plus INSTEAD OF on views
   old.* for UPDATE/DELETE, new.* for INSERT/UPDATE
   BEFORE can veto; a failing trigger rolls back the whole statement
   multi-trigger order is UNDEFINED by the standard -- never depend on it
Cursor: row-at-a-time, almost always the wrong tool (RBAR), use set operations

SQL injection = input concatenated into SQL text, so data becomes code
Fix = parameterized statements: query parsed FIRST, values bound AFTER
   so no input can change query structure. Not escaping -- separation.
A placeholder is a value, never an identifier. Dynamic column name -> whitelist.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "`TRUNCATE` is just a fast `DELETE`" | Also: DDL not DML, no `WHERE`, skips triggers, resets the identity counter, and usually cannot be rolled back. Four behavioural differences, not one speed difference |
| "`TRUNCATE` can never be rolled back" | True in MySQL and Oracle (implicit commit); false in PostgreSQL and SQL Server, where DDL is transactional |
| "`DROP` deletes all the rows" | It deletes the **table** — rows, structure, indexes, constraints, triggers and privileges |
| "A view is a copy of the data" | A view is stored *SQL*. It is re-evaluated on every read — demonstrated in §6.4 |
| "Views make queries faster" | A plain view has zero performance effect. A *materialized* view is the one that trades freshness for speed |
| "You can never update a view" | You can, when the row maps one-to-one to a base table; and with an `INSTEAD OF` trigger you can update any view |
| "Materialized views are always up to date" | They are a cache. Verified stale in §6.4 until refreshed |
| "A function and a procedure are the same with different names" | A function returns one value and is callable inside a query; a procedure is a statement that can do DML and control transactions |
| "If a trigger fails the statement still commits" | No — trigger and statement share one transaction. Verified: the aborted update left no audit row |
| "Triggers on the same event run in the order you created them" | Undefined by the standard. SQLite fired the newest first; MySQL uses creation order. Verified in §6.5 |
| "Escaping quotes prevents injection" | Not for numeric fields — `2 or 1=1` needs no quote. Verified in §6.8(f) |
| "Prepared statements work by escaping the input" | They work by **separating** code from data: the plan is fixed before the values arrive |
| "Stored procedures are immune to injection" | Only if they parameterize internally. A procedure building dynamic SQL from its arguments is just as vulnerable |
| "You can parameterize a table name" | No — verified rejected. Placeholders are values only; use a whitelist for identifiers |

---

## Interview Q&A bank

**Q1. `DELETE` vs `TRUNCATE` vs `DROP`?**
`DELETE` is DML: it removes selected rows with a `WHERE`, logs each row, fires `DELETE` triggers, can be rolled back, and keeps the table and its identity counter. `TRUNCATE` is DDL: it removes all rows by deallocating pages — fast, no `WHERE`, no triggers, resets the identity counter, and in MySQL/Oracle causes an implicit commit so it cannot be rolled back. `DROP` is DDL and removes the table itself along with its indexes, constraints, triggers and privileges.

**Q2. Which of them resets `AUTO_INCREMENT`?**
`TRUNCATE`. Verified that after deleting every row with `DELETE`, the next insert continued at 4, not 1.

**Q3. Why is `TRUNCATE` faster than `DELETE`?**
`DELETE` processes and logs row by row so it can be undone and can fire triggers. `TRUNCATE` deallocates the table's data pages and logs that, which is nearly constant-time regardless of row count.

**Q4. What is a view and why would you use one?**
A named stored query. Four reasons: security (expose some columns, hide others), simplification (name a complex join), logical data independence (restructure the tables and keep the view's interface stable), and backward compatibility during a migration.

**Q5. Does a view store data?**
No — it stores SQL. Verified: a raise given to a base-table row immediately changed what the view returned, with no action on the view.

**Q6. When can you update through a view?**
When the database can map one view row back to exactly one row of one base table. `DISTINCT`, `GROUP BY`, aggregates, window functions and `UNION` break that mapping and make the view read-only; joins are engine-dependent. An `INSTEAD OF` trigger lets you define the mapping yourself and makes any view writable.

**Q7. What does `WITH CHECK OPTION` do?**
It rejects any insert or update through the view that would produce a row the view's `WHERE` clause cannot see — preventing rows from silently disappearing from the view you just wrote them through.

**Q8. View vs materialized view?**
A view re-runs its query every time: always fresh, no storage, no speed benefit. A materialized view stores the result: fast to read and indexable, but stale until refreshed. Use the materialized form for expensive, frequently-read, slightly-stale-tolerant queries like dashboards.

**Q9. Stored procedure vs function?**
A procedure is invoked as a statement (`CALL`), can do DML, can control transactions, supports `IN`/`OUT`/`INOUT`, and cannot be used inside a query. A function returns a single value, is used inside expressions like `SELECT f(x)`, and cannot control transactions.

**Q10. Would you put business logic in stored procedures?**
Usually not today: it is hard to version-control, test and deploy with the application, and it is vendor-specific. It is still justified when many applications share one database, or when logic must run atomically next to the data.

**Q11. What is a trigger? Give a good and a bad use.**
Code the database runs automatically on an insert, update or delete. Good: audit trails, invariants a `CHECK` cannot express, `INSTEAD OF` on views. Bad: business logic — it is invisible control flow, so a one-line `UPDATE` quietly causes five writes nobody reading the application code can see.

**Q12. `BEFORE` vs `AFTER` trigger?**
`BEFORE` runs before the row is written, so it can validate, modify the incoming values, or abort the statement. `AFTER` runs once the row is committed to the operation, so it is for consequences — audit, counters, notifications.

**Q13. If a trigger throws an error, is the original statement rolled back?**
Yes. The trigger runs inside the statement's transaction, so an abort undoes the statement *and* anything the trigger had already written. Verified: an aborted update left the balance unchanged and added no audit row.

**Q14. What is a cursor and why avoid it?**
A pointer that walks a result set one row at a time. Avoid it because SQL is set-based: a cursor converts one optimised set operation into *n* iterations. Prefer a single `UPDATE ... WHERE`, a `CASE`, or a window function.

**Q15. `GRANT` and `REVOKE`?**
DCL. `GRANT` gives privileges on an object to a user or role; `REVOKE` takes them back. `WITH GRANT OPTION` lets the grantee pass the privilege on, and revoking from them cascades. Roles bundle privileges so you manage one role rather than many accounts.

**Q16. What is SQL injection?**
When user input is concatenated into a SQL string, the input can stop being data and become part of the query. A password of `' OR '1'='1` turns a login check into a tautology — verified returning every row in the user table.

**Q17. How do you prevent it?**
Parameterized (prepared) statements. The SQL is parsed into a plan before any user value arrives; the values are then bound into that fixed plan, so no input can alter the query's structure. Behind that, least privilege for the application's database account, input validation, and non-verbose error messages.

**Q18. Why isn't escaping quotes enough?**
Because a numeric field is interpolated without quotes, so there is nothing to escape. Verified: `uid = 2 or 1=1` returned the whole table. Blacklists lose the same way — you must enumerate every attack, the attacker needs one you missed.

**Q19. Can you parameterize a table or column name?**
No — verified rejected. A placeholder is a value, never an identifier, for exactly the reason parameters are safe: structure is fixed at parse time. For a dynamic column name, validate against a whitelist of permitted names.

**Q20. `DELETE` fired triggers but `TRUNCATE` doesn't — why does that matter?**
Because an audit trail implemented with `DELETE` triggers has a silent hole: the one operation that removes every row records nothing.

---

## Practice

1. Write a `CREATE TABLE` for `booking(bid, show_id, seat_no, user_id, amount)` with: a surrogate primary key, a named unique constraint stopping the same seat being sold twice for one show, a check that `amount > 0`, and a foreign key to `users` that nulls the column if the user is deleted.
2. You must remove all 50 million rows of a logging table nightly, and the table has a `DELETE` trigger writing to an archive. Which of `DELETE`/`TRUNCATE` do you use, and what has to change first?
3. Give a view definition that is updatable, and change one thing to make it read-only. Name the rule you broke.
4. `CREATE VIEW v AS SELECT * FROM emp WHERE did = 10;` — a user runs `UPDATE v SET did = 20 WHERE eid = 2`. What happens, and what would `WITH CHECK OPTION` do?
5. You need a dashboard showing per-department totals over 40 million rows, refreshed hourly. View, materialized view, or a summary table maintained by triggers? Justify in three lines.
6. Write a trigger that keeps `dept.emp_count` correct. How many triggers do you need, and name the case most people forget.
7. `SELECT * FROM users WHERE name = '<input>'` — give three distinct inputs that break it in three different ways, and say what each achieves.
8. The code is `f"... WHERE id = {user_id}"` and someone argues it is safe because `user_id` comes from a dropdown. Give the counter-argument in two sentences.
9. An application needs `SELECT`, `INSERT` and `UPDATE` on four tables and nothing else. Write the `GRANT` statements, then say what attack this blocks.
10. Why can a prepared statement not parameterize `ORDER BY ?`, and what do you do instead?

**Answers to 2, 4 and 6** (the three that most often go wrong):

> **2.** `TRUNCATE` for the speed, but it **will not fire the `DELETE` trigger**, so the archive silently stops being written. Fix the archiving first — `INSERT INTO archive SELECT * FROM log` as an explicit statement, then `TRUNCATE` — and delete the trigger, which is now both redundant and misleading.
>
> **4.** By default the update succeeds and **the row vanishes from the view** (it is now `did = 20`, which the view's `WHERE` excludes) — so a user updates a row through a view and it disappears. `WITH CHECK OPTION` rejects the update instead.
>
> **6.** Three triggers, not two: `AFTER INSERT` (+1), `AFTER DELETE` (−1), and the forgotten one — **`AFTER UPDATE OF did`**, which must decrement the old department and increment the new one. An employee transferring between departments changes no row count, so people miss it.

---

## Exit checklist

```
[ ] I can give the DELETE / TRUNCATE / DROP table from memory, all nine rows
[ ] I can say which one resets the identity counter and which fires triggers
[ ] I can give the honest "can TRUNCATE be rolled back" answer with the dialect split
[ ] I know DEFAULT does not apply to an explicitly inserted NULL
[ ] I can say why constraints should be named
[ ] I can state the four reasons views exist
[ ] I can explain "a view is stored SQL" and predict what a base-table change does to it
[ ] I can state the updatability rule and list what breaks it
[ ] I know what WITH CHECK OPTION prevents
[ ] I can compare a view and a materialized view on four axes
[ ] I can make a complex view writable and name the mechanism
[ ] I can give four differences between a procedure and a function
[ ] I have an honest opinion on business logic in the database
[ ] I can write a trigger with old./new. and say which exists for which event
[ ] I know BEFORE can veto, and that a failing trigger rolls back the statement
[ ] I know multi-trigger order is undefined and never rely on it
[ ] I can say what a cursor is and why I would avoid it
[ ] I can explain GRANT, REVOKE, roles and WITH GRANT OPTION
[ ] I can write an injection that bypasses auth and one that exfiltrates data
[ ] I can explain WHY prepared statements work -- parse first, bind after
[ ] I can refute "escaping quotes is enough" with the numeric-field case
[ ] I know a placeholder cannot be an identifier, and that a whitelist is the fix
```

---

## Next

**Part 9: M7 — Indexing and Storage.** The performance module. How a table actually sits on disk; **why B+ trees and not BSTs or B-trees**, with the fan-out and height arithmetic worked out; dense vs sparse; **clustered vs non-clustered** and why there is only one clustered index; composite indexes and the **leftmost-prefix rule**; covering indexes; hash indexes and what they cannot do; **when an index makes things worse**; **SARGability** — why a function on a column kills the index; reading `EXPLAIN`; and the basics of what the query optimiser does. It links straight back to DSA Part 11 on trees.
