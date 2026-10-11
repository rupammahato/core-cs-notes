# DBMS Placement Handbook — Part 7
# Module 5: SQL II — Joins, Subqueries and Windows

**Module 5 · 5 hours · Tier 1 · Requires: M4 (execution order, aggregates), M1 (NULL semantics)**

---

## Why this module matters

This is the module the SQL round is made of. Everything up to here was setup; the queries interviewers actually ask live in this file.

The good news is that the asked questions are a **small, stable set**. Compilations of SQL rounds at Amazon, Google, Meta and Microsoft keep returning the same handful: Nth highest salary, employees earning more than their manager, department-wise maximum, duplicates, consecutive rows, running totals. Two tools answer nearly all of them — **the self-join and the window function** — so this module teaches those properly and then drills the patterns.

The organising principle:

> **A join matches rows from two row sets and then decides what to do with the ones that didn't match — that single decision is the entire difference between inner, left, right and full. A subquery computes a value or a set for the outer query to use. A window function is the one tool that computes across other rows while keeping the current row, which is why it solves every "rank", "previous", "running" and "top-N per group" question that `GROUP BY` cannot.**

**Every query in this module was executed** (Python 3.12 `sqlite3`, SQLite 3.49.1) against the M4 dataset. All results are real output — including two cases where my own query exposed a subtlety I then had to explain rather than hide (§5.4 and §5.11).

---

## 5.0 The dataset (from M4)

```
dept                                 emp
did | dname       | city             eid | name  | did  | salary | manager_id | hired      | commission
----+-------------+-------           ----+-------+------+--------+------------+------------+-----------
10  | Engineering | Pune             1   | Asha  | 10   | 90000  | NULL       | 2019-03-01 | NULL
20  | Sales       | Delhi            2   | Ravi  | 10   | 75000  | 1          | 2020-07-15 | 5000
30  | HR          | Pune             3   | Meera | 10   | 75000  | 1          | 2021-01-20 | NULL
40  | Research    | NULL             4   | Dev   | 20   | 60000  | 1          | 2020-11-05 | 8000
                                     5   | Sara  | 20   | 85000  | 4          | 2018-06-10 | NULL
                                     6   | Imran | 20   | 60000  | 4          | 2022-02-28 | 3000
                                     7   | Nita  | 30   | 50000  | 1          | 2023-09-01 | NULL
                                     8   | Omar  | NULL | 95000  | 1          | 2017-04-12 | NULL
```

The two planted mismatches do all the work below: **Omar has no department** (an `emp` row with no `dept` match) and **Research has no employees** (a `dept` row with no `emp` match). Salary ties at 75000 and 60000 expose the ranking functions. The `manager_id` column makes `emp` self-joinable.

---

## 5.1 Joins

```
           emp                    dept
        ┌────────┐             ┌────────┐
        │ 7 rows │             │ 3 rows │
        │ match  │◄── ON ─────►│ match  │
        ├────────┤             ├────────┤
        │ Omar   │             │Research│
        │(no dept)│            │(no emp) │
        └────────┘             └────────┘
             ▲                      ▲
             │                      │
     kept by LEFT/FULL      kept by RIGHT/FULL
     dropped by INNER       dropped by INNER
```

| Join | Keeps | On our data |
|---|---|---|
| `INNER JOIN` | Only matching pairs | **7 rows** |
| `LEFT JOIN` | All left rows + matches | **8 rows** (Omar, `dname` NULL) |
| `RIGHT JOIN` | All right rows + matches | **8 rows** (Research, `name` NULL) |
| `FULL OUTER JOIN` | Everything | **9 rows** (both) |
| `CROSS JOIN` | Every combination | **32 rows** (8 × 4) |

All five counts verified. **Being able to state the row count before running the query is the skill** — it is how you catch a wrong join in an interview.

### Verified output

```sql
SELECT e.name, d.dname FROM emp e JOIN dept d ON e.did = d.did ORDER BY e.name;
```
```
    Asha Engineering | Dev Sales | Imran Sales | Meera Engineering
    Nita HR | Ravi Engineering | Sara Sales                            (7 rows)
```
**Omar and Research are both gone.** An inner join silently discards unmatched rows on both sides — the most common cause of "my report is missing people".

```sql
SELECT e.name, d.dname FROM emp e LEFT JOIN dept d ON e.did = d.did ORDER BY e.name;
```
```
    name  | dname
    ------+------------
    ...
    Omar  | NULL          <- kept, with NULLs for every dept column
    ...                                                               (8 rows)
```

```sql
SELECT e.name, d.dname FROM emp e RIGHT JOIN dept d ON e.did = d.did ORDER BY d.dname, e.name;
```
```
    NULL  | Research      <- the empty department survives            (8 rows)
```

```sql
SELECT e.name, d.dname FROM emp e FULL OUTER JOIN dept d ON e.did = d.did
ORDER BY d.dname, e.name;
```
```
    Omar  | NULL          <- unmatched employee
    NULL  | Research      <- unmatched department                     (9 rows)
```

**`LEFT` vs `RIGHT`:** `A RIGHT JOIN B` ≡ `B LEFT JOIN A`. They are the same operation with the tables swapped, which is why most codebases use `LEFT JOIN` exclusively — reading a query where the preserved side flips halfway through is needless work. **MySQL has no `FULL OUTER JOIN`**; emulate it with `LEFT JOIN ... UNION ... RIGHT JOIN ...`.

### Joining on NULL never matches

Omar's `did` is NULL, and `NULL = 10` is unknown, so he matches no department — not even one with a NULL `did`, since `NULL = NULL` is also unknown (M1, §1.8). **This is the same rule as everywhere else**, and it explains outer-join behaviour completely: an unmatched row is one whose `ON` predicate was never TRUE.

---

## 5.2 The classic outer-join mistake: `ON` vs `WHERE`

**This is the single most instructive thing in the module.** Both queries below look like "departments and their high earners". One of them silently throws away two departments.

```sql
SELECT d.dname, e.name FROM dept d LEFT JOIN emp e ON e.did = d.did
WHERE e.salary > 70000 ORDER BY d.dname;
```
```
    dname       | name
    ------------+------
    Engineering | Asha
    Engineering | Ravi
    Engineering | Meera
    Sales       | Sara                                                (4 rows)
```

**HR and Research are gone, despite the `LEFT JOIN`.** Why: the join produced `(HR, Nita)` and `(Research, NULL)`, then `WHERE e.salary > 70000` evaluated `50000 > 70000` = FALSE and `NULL > 70000` = UNKNOWN. `WHERE` keeps only TRUE (M1, §1.8), so both rows were discarded. **A `WHERE` condition on the optional side of an outer join converts it into an inner join.**

Put the condition in `ON` instead:

```sql
SELECT d.dname, e.name FROM dept d LEFT JOIN emp e ON e.did = d.did AND e.salary > 70000
ORDER BY d.dname, e.name;
```
```
    dname       | name
    ------------+------
    Engineering | Asha
    Engineering | Meera
    Engineering | Ravi
    HR          | NULL      <- preserved, with no matching employee
    Research    | NULL      <- preserved
    Sales       | Sara                                                (6 rows)
```

> **The rule:** on an outer join, `ON` decides **what counts as a match**; `WHERE` filters **the result after the join**. A condition on the preserved side belongs in `WHERE`; a condition on the optional side belongs in `ON`.
>
> **The exception that's actually a tool:** `WHERE e.eid IS NULL` *is* meant to run after the join — that is the anti-join (§5.3).

---

## 5.3 Anti-joins: "rows in A with nothing in B"

Four ways to ask for departments with no employees. Verified:

| Form | Result |
|---|---|
| `LEFT JOIN ... WHERE e.eid IS NULL` | `['Research']` ✓ |
| `NOT EXISTS (SELECT 1 FROM emp e WHERE e.did = d.did)` | `['Research']` ✓ |
| `NOT IN (SELECT did FROM emp WHERE did IS NOT NULL)` | `['Research']` ✓ |
| `NOT IN (SELECT did FROM emp)` — **unguarded** | **`[]`** ✗ |

```sql
-- the broken one
SELECT d.dname FROM dept d WHERE d.did NOT IN (SELECT did FROM emp);
-- returns NOTHING, because Omar's NULL did poisons the NOT IN (M1, §1.9)
```

> **`NOT EXISTS` is the default answer.** It is NULL-safe, it reads as the question, and on most engines it optimises as well as the join. Reach for `NOT IN` only when the column is `NOT NULL`, and say that out loud.

---

## 5.4 `NATURAL JOIN` and comma joins: two things to avoid

**The comma join** is just an inner join with the condition in `WHERE`:

```sql
SELECT e.name, d.dname FROM emp e, dept d WHERE e.did = d.did AND d.city = 'Pune';
-- Asha, Meera, Nita, Ravi                                           (4 rows)
```

It works, but it cannot express an outer join and it makes a forgotten condition produce a silent cross join. Use explicit `JOIN ... ON`.

**`NATURAL JOIN` joins on every column the two tables share, by name.** On our schema it happens to be fine, because `did` is the only shared name. Change the schema slightly — rename `dept.dname` to `dept.name`, so both tables have a `name` column — and verified:

```sql
-- dept(did, name)   emp(eid, name, did)
SELECT * FROM emp NATURAL JOIN dept;
```
```
    eid | name  | did
    ----+-------+----
    3   | Sales | 20                                                  (1 row!)
```

**One row.** It joined on `did` *and* `name`, so the only match was the employee whose name happens to equal their department's name. The intended query returns three rows:

```sql
SELECT e.eid, e.name, d.name AS dept FROM emp e JOIN dept d ON e.did = d.did;
-- (1, Asha, Engineering) (2, Ravi, Engineering) (3, Sales, Sales)    (3 rows)
```

> **`NATURAL JOIN` makes the meaning of your query depend on column *names* you didn't write down.** Someone adds a `created_at` column to both tables and every natural join in the codebase silently changes. Never use it in production; recognise it in an exam. `USING (did)` is the safe middle ground — explicit about the column, still shorter than `ON`.

---

## 5.5 The self-join

A table joined to itself, with two aliases. **This is the interview workhorse** — any question comparing one row to another row of the same table is a self-join.

```sql
SELECT e.name AS employee, m.name AS manager
FROM emp e LEFT JOIN emp m ON e.manager_id = m.eid ORDER BY e.name;
```
```
    employee | manager
    ---------+--------
    Asha     | NULL        <- LEFT JOIN keeps the CEO
    Dev      | Asha
    Imran    | Dev
    Meera    | Asha
    Nita     | Asha
    Omar     | Asha
    Ravi     | Asha
    Sara     | Dev                                                    (8 rows)
```

**`LEFT` matters here:** with an inner join Asha disappears, because she has no manager. "Where did the CEO go?" is a standard follow-up.

### The classic: employees earning more than their manager

```sql
SELECT e.name AS employee, e.salary, m.name AS manager, m.salary AS mgr_salary
FROM emp e JOIN emp m ON e.manager_id = m.eid
WHERE e.salary > m.salary ORDER BY e.name;
```
```
    employee | salary | manager | mgr_salary
    ---------+--------+---------+-----------
    Omar     | 95000  | Asha    | 90000
    Sara     | 85000  | Dev     | 60000
```

Note the shape: **the comparison lives in `WHERE`, between the two aliases.** Here an inner join is correct — someone with no manager cannot out-earn one.

---

## 5.6 Subqueries

| Kind | Returns | Usable in |
|---|---|---|
| **Scalar** | One row, one column | Anywhere a value goes: `SELECT`, `WHERE`, `ON` |
| **Row** | One row, many columns | `WHERE (a,b) = (SELECT …)` |
| **Table** | Many rows | `FROM` (derived table), `IN`, `EXISTS` |

### Non-correlated — runs once, independent of the outer query

```sql
SELECT name, salary FROM emp WHERE salary > (SELECT AVG(salary) FROM emp)
ORDER BY salary DESC;
-- Omar 95000 | Asha 90000 | Sara 85000 | Ravi 75000 | Meera 75000    (5 rows)
```

The average (73750) is computed once. You can run the inner query on its own — that is the test for non-correlated.

### Correlated — references the outer row, conceptually re-evaluated per row

```sql
SELECT name, did, salary FROM emp e
WHERE salary = (SELECT MAX(salary) FROM emp x WHERE x.did = e.did)
ORDER BY did;
```
```
    name | did | salary
    -----+-----+-------
    Asha | 10  | 90000
    Sara | 20  | 85000
    Nita | 30  | 50000
```

**This is the correct answer to the top-earner-per-department question** that the bare-column trick in M4 §4.4 got wrong. The inner query mentions `e.did`, so it cannot run alone — that is the test for correlated.

Note Omar is absent: his `did` is NULL, so `x.did = e.did` is never TRUE and the subquery returns NULL, and `salary = NULL` is unknown. **Correct per the rules, probably not what a manager wanted** — exactly the kind of thing to flag out loud.

### `EXISTS` — asks "any row at all?"

```sql
SELECT d.dname FROM dept d
WHERE EXISTS (SELECT 1 FROM emp e WHERE e.did = d.did AND e.salary > 80000)
ORDER BY d.dname;
-- Engineering, Sales
```

`SELECT 1` is idiomatic: `EXISTS` only cares *whether* a row comes back, never what is in it. It can short-circuit on the first match.

### Scalar subqueries in `SELECT`

```sql
SELECT (SELECT COUNT(*) FROM emp) AS employees, (SELECT COUNT(*) FROM dept) AS departments;
-- 8 | 4
```

Handy, but a correlated scalar subquery in `SELECT` runs once per output row — the N+1 problem in SQL form (M10). A join or window function is usually better.

---

## 5.7 `IN` vs `EXISTS` vs `JOIN`

All three answer "departments with someone over 80000", and all three returned `['Engineering', 'Sales']` ✓ verified:

```sql
-- JOIN (needs DISTINCT: a dept with two high earners would appear twice)
SELECT DISTINCT d.dname FROM dept d JOIN emp e ON e.did = d.did WHERE e.salary > 80000;

-- IN
SELECT dname FROM dept WHERE did IN (SELECT did FROM emp WHERE salary > 80000);

-- EXISTS
SELECT dname FROM dept d WHERE EXISTS
  (SELECT 1 FROM emp e WHERE e.did = d.did AND e.salary > 80000);
```

| | `IN` | `EXISTS` | `JOIN` |
|---|---|---|---|
| Shape | Value against a list | Correlated existence test | Matches rows |
| Duplicate rows in output | No | No | **Yes — needs `DISTINCT`** |
| NULL-safe when negated | **No** (`NOT IN` breaks) | **Yes** (`NOT EXISTS`) | Yes |
| Columns from the inner table | Not available | Not available | **Available** |
| Typically better when | The inner list is small | The inner table is large / you want early exit | **You need inner columns** |

**The honest performance answer**, which is what a good interviewer is listening for: *"On modern optimizers — MySQL 8, Postgres, SQL Server — `IN`, `EXISTS` and a semi-join are usually transformed into the same plan, so pick for clarity and NULL-safety, not for speed. The real differences are that `NOT IN` is unsafe with NULLs and that a join needs `DISTINCT`."* Older MySQL (5.5 and earlier) genuinely executed `IN` subqueries badly, which is where the folklore comes from. Needing a column from the inner table settles it: use a join.

---

## 5.8 Derived tables and CTEs

**A derived table** is a subquery in `FROM`. It must be aliased:

```sql
SELECT dname, headcount FROM
  (SELECT did, COUNT(*) AS headcount FROM emp GROUP BY did) t
JOIN dept d ON d.did = t.did
WHERE headcount > 1 ORDER BY dname;
-- Engineering 3 | Sales 3
```

**A CTE** (`WITH`) is the same thing, named up front, and reads top to bottom:

```sql
WITH dept_stats AS (
  SELECT did, COUNT(*) AS headcount, AVG(salary) AS avg_sal FROM emp GROUP BY did)
SELECT d.dname, s.headcount, ROUND(s.avg_sal) AS avg_sal
FROM dept_stats s JOIN dept d ON d.did = s.did
ORDER BY s.avg_sal DESC;
```
```
    dname       | headcount | avg_sal
    ------------+-----------+--------
    Engineering | 3         | 80000.0
    Sales       | 3         | 68333.0
    HR          | 1         | 50000.0
```

| | Derived table | CTE |
|---|---|---|
| Readability | Nests inward, read inside-out | **Linear, named** |
| Reusable in the same query | No — repeat it | **Yes, reference it twice** |
| Recursion | No | **Yes** |

**Use a CTE by default.** It also gives you a place to put a meaningful name, which is most of what makes SQL readable. (Historical footnote for completeness: MySQL gained CTEs in 8.0; Postgres used to materialize them as an optimization fence, relaxed in version 12.)

---

## 5.9 Recursive CTEs

The tool for hierarchies — org charts, category trees, bill-of-materials, graph paths. Structure is always the same: a **base case**, `UNION ALL`, and a **recursive step** that joins back to the CTE.

```sql
WITH RECURSIVE chain(eid, name, manager_id, level, path) AS (
    SELECT eid, name, manager_id, 0, name FROM emp WHERE manager_id IS NULL   -- base
  UNION ALL
    SELECT e.eid, e.name, e.manager_id, c.level+1, c.path || ' > ' || e.name  -- step
    FROM emp e JOIN chain c ON e.manager_id = c.eid)
SELECT level, name, path FROM chain ORDER BY level, name;
```
```
    level | name  | path
    ------+-------+-------------------
    0     | Asha  | Asha
    1     | Dev   | Asha > Dev
    1     | Meera | Asha > Meera
    1     | Nita  | Asha > Nita
    1     | Omar  | Asha > Omar
    1     | Ravi  | Asha > Ravi
    2     | Imran | Asha > Dev > Imran
    2     | Sara  | Asha > Dev > Sara
```

Reverse the join direction to walk **upward** instead:

```sql
WITH RECURSIVE up(eid, name, manager_id, depth) AS (
    SELECT eid, name, manager_id, 0 FROM emp WHERE name = 'Imran'
  UNION ALL
    SELECT e.eid, e.name, e.manager_id, u.depth+1
    FROM emp e JOIN up u ON u.manager_id = e.eid)
SELECT depth, name FROM up ORDER BY depth;
-- 0 Imran | 1 Dev | 2 Asha
```

| Point | Detail |
|---|---|
| `UNION ALL`, not `UNION` | `UNION` dedupes on every iteration — slower, and usually not what you want |
| Termination | The step must eventually return no rows. **A cycle in the data loops forever** — guard with a depth limit or a visited path |
| Keyword | `RECURSIVE` required in SQLite and Postgres; **MySQL and SQL Server omit it** (`WITH RECURSIVE` is accepted in MySQL 8) |
| `level` / `path` | Carry them through the recursion; they cost nothing and make the output readable |

---

## 5.10 Window functions

**The one thing `GROUP BY` cannot do: compute across a set of rows while keeping every row.**

```
   GROUP BY  : 8 rows ──► 4 rows   (collapses; the individual rows are gone)
   WINDOW    : 8 rows ──► 8 rows   (keeps every row, adds a computed column)
```

Anatomy:

```sql
function() OVER (PARTITION BY col   -- optional: restart per group
                 ORDER BY col       -- optional: order within the partition
                 ROWS BETWEEN …)    -- optional: the frame
```

### The ranking trio — and the tie behaviour that is the question

```sql
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn,
       RANK()       OVER (ORDER BY salary DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS dense
FROM emp ORDER BY salary DESC, name;
```
```
    name  | salary | rn | rnk | dense
    ------+--------+----+-----+------
    Omar  | 95000  | 1  | 1   | 1
    Asha  | 90000  | 2  | 2   | 2
    Sara  | 85000  | 3  | 3   | 3
    Meera | 75000  | 5  | 4   | 4      <- tied
    Ravi  | 75000  | 4  | 4   | 4      <- tied
    Dev   | 60000  | 6  | 6   | 5      <- tied
    Imran | 60000  | 7  | 6   | 5      <- tied
    Nita  | 50000  | 8  | 8   | 6
```

| Function | On ties | After a tie |
|---|---|---|
| `ROW_NUMBER()` | **Different** numbers (arbitrary order) | Continues: 4, 5, 6 |
| `RANK()` | **Same** number | **Skips**: 4, 4, **6** |
| `DENSE_RANK()` | **Same** number | **No gap**: 4, 4, **5** |

**Look at Meera and Ravi closely.** Meera got `rn = 5` and Ravi `rn = 4`, yet the display shows Meera first — because the outer `ORDER BY salary DESC, name` and the window's `ORDER BY salary DESC` broke the tie *differently*. The window had no tie-breaker, so it chose arbitrarily.

> **Same lesson as pagination in M4 §4.8: an `ORDER BY` without a unique tie-breaker is non-deterministic.** Write `OVER (ORDER BY salary DESC, eid)` and the numbering becomes reproducible. This bit me while writing this module, which is a decent sign of how easily it slips past.

**Which to use for "Nth highest":** `DENSE_RANK`. With `RANK`, the 5th-highest salary may not exist (rank 5 was skipped); with `ROW_NUMBER`, tied people get different ranks so you may return only one of two equal earners.

### `PARTITION BY`

```sql
SELECT d.dname, e.name, e.salary,
       ROW_NUMBER() OVER (PARTITION BY e.did ORDER BY e.salary DESC) AS rn_in_dept
FROM emp e JOIN dept d ON d.did = e.did ORDER BY d.dname, rn_in_dept;
```
```
    dname       | name  | salary | rn_in_dept
    ------------+-------+--------+-----------
    Engineering | Asha  | 90000  | 1
    Engineering | Ravi  | 75000  | 2
    Engineering | Meera | 75000  | 3
    HR          | Nita  | 50000  | 1
    Sales       | Sara  | 85000  | 1
    Sales       | Dev   | 60000  | 2
    Sales       | Imran | 60000  | 3
```

**`PARTITION BY` is "`GROUP BY` that doesn't collapse".** The numbering restarts per department.

### `LAG` and `LEAD` — reach into another row

```sql
SELECT name, salary,
       LAG(salary)  OVER (ORDER BY salary DESC) AS prev_salary,
       salary - LAG(salary) OVER (ORDER BY salary DESC) AS diff,
       LEAD(name)   OVER (ORDER BY salary DESC) AS next_person
FROM emp ORDER BY salary DESC, name;
```
```
    name  | salary | prev_salary | diff   | next_person
    ------+--------+-------------+--------+------------
    Omar  | 95000  | NULL        | NULL   | Asha
    Asha  | 90000  | 95000       | -5000  | Sara
    Sara  | 85000  | 90000       | -5000  | Ravi
    Meera | 75000  | 75000       | 0      | Dev
    Ravi  | 75000  | 85000       | -10000 | Meera
    ...
```

The first row's `LAG` is NULL — there is no previous row. (`LAG(salary, 1, 0)` supplies a default.) And the tie again: Meera's `prev_salary` is 75000, Ravi's own salary, because the window ordered Ravi before her.

**`LAG`/`LEAD` replace a self-join on "the previous row"**, which otherwise needs a correlated subquery and is both slower and harder to read.

### Frames: running totals and moving averages

```sql
SELECT name, hired, salary,
       SUM(salary) OVER (ORDER BY hired ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
         AS running_payroll,
       ROUND(AVG(salary) OVER (ORDER BY hired ROWS BETWEEN 2 PRECEDING AND CURRENT ROW))
         AS moving_avg_3
FROM emp ORDER BY hired;
```
```
    name  | hired      | salary | running_payroll | moving_avg_3
    ------+------------+--------+-----------------+-------------
    Omar  | 2017-04-12 | 95000  | 95000           | 95000.0
    Sara  | 2018-06-10 | 85000  | 180000          | 90000.0
    Asha  | 2019-03-01 | 90000  | 270000          | 90000.0
    Ravi  | 2020-07-15 | 75000  | 345000          | 83333.0
    Dev   | 2020-11-05 | 60000  | 405000          | 75000.0
    Meera | 2021-01-20 | 75000  | 480000          | 70000.0
    Imran | 2022-02-28 | 60000  | 540000          | 65000.0
    Nita  | 2023-09-01 | 50000  | 590000          | 61667.0
```

| Frame | Meaning |
|---|---|
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | Everything up to here — **running total** |
| `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` | A 3-row sliding window — **moving average** |
| `RANGE BETWEEN …` | By **value**, not row count — ties share a frame |
| Default with `ORDER BY` | `RANGE UNBOUNDED PRECEDING AND CURRENT ROW` — **so tied rows get the same running total**, which surprises people |

**`ROWS` vs `RANGE` is a real interview question**: `ROWS` counts rows, `RANGE` groups by value. With duplicate order keys they give different answers, and the default is `RANGE`.

### An aggregate as a window: every row keeps its context

```sql
SELECT d.dname, e.name, e.salary,
       ROUND(AVG(e.salary) OVER (PARTITION BY e.did)) AS dept_avg,
       e.salary - ROUND(AVG(e.salary) OVER (PARTITION BY e.did)) AS vs_dept_avg
FROM emp e JOIN dept d ON d.did = e.did ORDER BY d.dname, e.salary DESC;
```
```
    dname       | name  | salary | dept_avg | vs_dept_avg
    ------------+-------+--------+----------+------------
    Engineering | Asha  | 90000  | 80000.0  | 10000.0
    Engineering | Ravi  | 75000  | 80000.0  | -5000.0
    Engineering | Meera | 75000  | 80000.0  | -5000.0
    Sales       | Sara  | 85000  | 68333.0  | 16667.0
    Sales       | Dev   | 60000  | 68333.0  | -8333.0
    Sales       | Imran | 60000  | 68333.0  | -8333.0
```

**Each employee beside their department's average, in one pass, with no self-join and no `GROUP BY`.** With `GROUP BY` you would get the averages but lose the people, then need to join back. This is the pattern to reach for whenever a question says "compared to".

**Where windows may appear:** `SELECT` and `ORDER BY` only — **never in `WHERE`, `GROUP BY` or `HAVING`**, because windows are computed at step 5 of the execution order (M4, §4.1), after filtering. To filter on a window result, wrap it in a CTE or derived table and filter outside. That single fact explains the shape of almost every window query you will write.

---

## 5.11 The query drill bank

The patterns that get asked by name. **All outputs verified.**

### Drill 1 — Nth highest salary, four ways

Distinct salaries descending: `95000, 90000, 85000, 75000, 60000, 50000`. For **N = 2** all four methods returned **90000** ✓:

```sql
-- 1. correlated subquery: "exactly N-1 distinct salaries are above me"
SELECT DISTINCT salary FROM emp e
WHERE 1 = (SELECT COUNT(DISTINCT salary) FROM emp x WHERE x.salary > e.salary);

-- 2. LIMIT / OFFSET  (MySQL, Postgres, SQLite)
SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1;

-- 3. DENSE_RANK  (the modern answer)
SELECT salary FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) r FROM emp) t
WHERE r = 2 LIMIT 1;

-- 4. MAX of everything below the MAX  (only works for N = 2)
SELECT MAX(salary) FROM emp WHERE salary < (SELECT MAX(salary) FROM emp);
```

For **N = 4**, which lands on the 75000 tie, the three general methods all returned **75000** ✓, and method 4 does not generalise.

| Method | Generalises to any N | Needs windows | Notes |
|---|---|---|---|
| Correlated subquery | Yes | No | The classic; O(n²) in the worst case |
| `LIMIT`/`OFFSET` | Yes | No | Simplest. **Not portable** to Oracle/SQL Server syntax |
| `DENSE_RANK` | Yes | **Yes** | Best answer where windows exist; handles ties correctly |
| `MAX` of the rest | **No** | No | N = 2 only — fine if that's the question |

**The follow-ups you will get, with answers ready:**
- *"What if two people share the 2nd highest salary?"* — `DISTINCT`/`DENSE_RANK` treat it as one salary and return both people if you select names. `ROW_NUMBER` would pick one arbitrarily.
- *"What if N exceeds the number of distinct salaries?"* — all three return no rows. Good: NULL via an outer query if the caller needs a row.
- *"Do it without `LIMIT`."* — method 1 or 3.

### Drill 2 — duplicates

```sql
SELECT salary, COUNT(*) AS n, GROUP_CONCAT(name, ', ') AS people
FROM emp GROUP BY salary HAVING COUNT(*) > 1 ORDER BY salary DESC;
```
```
    salary | n | people
    -------+---+------------
    75000  | 2 | Ravi, Meera
    60000  | 2 | Dev, Imran
```

**Deleting duplicates, keeping one** — the real question. Verified on a scratch table with a genuinely duplicated row (9 rows, 3 at 75000 → 8 rows, 2 at 75000):

```sql
DELETE FROM dup WHERE rowid NOT IN
  (SELECT MIN(rowid) FROM dup GROUP BY salary, name);
```

| Engine | Row identity to use |
|---|---|
| SQLite | `rowid` |
| MySQL | the primary key; or `ROW_NUMBER()` in a CTE (8.0+) |
| Postgres | `ctid`, or `ROW_NUMBER()` in a CTE |

The portable modern form:

```sql
WITH ranked AS (
  SELECT eid, ROW_NUMBER() OVER (PARTITION BY salary, name ORDER BY eid) AS rn FROM emp)
DELETE FROM emp WHERE eid IN (SELECT eid FROM ranked WHERE rn > 1);
```

**MySQL gotcha worth knowing:** you cannot `DELETE FROM t WHERE … (SELECT … FROM t)` directly — it errors with "You can't specify target table for update in FROM clause". Wrap the subquery in another derived table.

### Drill 3 — top N per group

```sql
WITH ranked AS (
  SELECT e.did, e.name, e.salary,
         DENSE_RANK() OVER (PARTITION BY e.did ORDER BY e.salary DESC) AS r
  FROM emp e)
SELECT d.dname, r.name, r.salary, r.r FROM ranked r JOIN dept d ON d.did = r.did
WHERE r.r <= 2 ORDER BY d.dname, r.r, r.name;
```
```
    dname       | name  | salary | r
    ------------+-------+--------+--
    Engineering | Asha  | 90000  | 1
    Engineering | Meera | 75000  | 2
    Engineering | Ravi  | 75000  | 2      <- DENSE_RANK keeps BOTH tied employees
    HR          | Nita  | 50000  | 1
    Sales       | Sara  | 85000  | 1
    Sales       | Dev   | 60000  | 2
    Sales       | Imran | 60000  | 2
```

And without windows, for an interviewer who asks for it:

```sql
SELECT d.dname, e.name, e.salary FROM emp e JOIN dept d ON d.did = e.did
WHERE (SELECT COUNT(DISTINCT x.salary) FROM emp x
       WHERE x.did = e.did AND x.salary > e.salary) < 2
ORDER BY d.dname, e.salary DESC;
```

Same 7 rows ✓. The correlated subquery reads as "fewer than 2 distinct salaries beat mine inside my department".

> **Note the `WHERE r.r <= 2` is outside the CTE.** You cannot filter on a window function in the same `SELECT` that computes it — §5.10.

### Drill 4 — employees with no subordinates (self anti-join)

```sql
SELECT e.name FROM emp e
WHERE NOT EXISTS (SELECT 1 FROM emp s WHERE s.manager_id = e.eid) ORDER BY e.name;
-- Imran, Meera, Nita, Omar, Ravi, Sara                              (6 rows)
```

Asha and Dev are the only managers, so the other six are leaves.

### Drill 5 — gaps and consecutive runs

`visit(day)` = `1, 2, 3, 7, 8, 11`. **The gap trick: `value − ROW_NUMBER()` is constant within a consecutive run.**

```sql
SELECT day, day - ROW_NUMBER() OVER (ORDER BY day) AS grp FROM visit ORDER BY day;
```
```
    day | grp
    ----+----
    1   | 0        ┐
    2   | 0        ├ run 1
    3   | 0        ┘
    7   | 3        ┐ run 2
    8   | 3        ┘
    11  | 5          run 3
```

Then group by that synthetic key:

```sql
SELECT MIN(day) AS run_start, MAX(day) AS run_end, COUNT(*) AS len
FROM (SELECT day, day - ROW_NUMBER() OVER (ORDER BY day) AS grp FROM visit)
GROUP BY grp ORDER BY run_start;
```
```
    run_start | run_end | len
    ----------+---------+----
    1         | 3       | 3
    7         | 8       | 2
    11        | 11      | 1
```

**This one pattern answers a whole family of questions:** longest login streak, consecutive wins, unbroken attendance, contiguous free seats. Memorise it as a unit.

Finding where the gaps start, without windows:

```sql
SELECT v.day + 1 AS missing_from FROM visit v
WHERE NOT EXISTS (SELECT 1 FROM visit x WHERE x.day = v.day + 1)
  AND v.day < (SELECT MAX(day) FROM visit);
-- 4, 9
```

### Drill 6 — running total

§5.10's frame example. The one-liner to remember:

```sql
SUM(x) OVER (ORDER BY d ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```

### Drill 7 — each row against its group's aggregate

§5.10's last example: `AVG(salary) OVER (PARTITION BY did)`. Any question phrased "compared to their department / category / month average" is this.

---

## 5.12 Consolidation

### Must remember (module)

1. **Inner 7, left 8, right 8, full 9, cross 32** on this dataset — be able to predict a join's row count before running it.
2. `A RIGHT JOIN B` ≡ `B LEFT JOIN A`. **MySQL has no `FULL OUTER JOIN`** — emulate with `LEFT UNION RIGHT`.
3. **Joining on NULL never matches**, including NULL to NULL.
4. **A `WHERE` condition on the optional side of an outer join silently makes it an inner join.** Conditions on the optional side go in `ON`.
5. `WHERE … IS NULL` after a `LEFT JOIN` is the **anti-join**, and is the one case where filtering after the join is the point.
6. **`NOT EXISTS` is the default anti-join.** `NOT IN` breaks on NULLs — verified returning zero rows.
7. **`NATURAL JOIN` joins on every shared column name** — verified collapsing 3 rows to 1 wrong row. Never use it; `USING (col)` is the safe shorthand.
8. A **self-join** answers every "row compared to another row of the same table" question. Use `LEFT` to keep the row with no partner (the CEO).
9. **Correlated** subqueries reference the outer row and can't run alone; **non-correlated** ones can.
10. `IN`, `EXISTS` and a join usually produce the same plan on modern optimizers. **Choose for clarity and NULL-safety**; a join needs `DISTINCT`; use a join when you need the inner table's columns.
11. `SELECT 1` inside `EXISTS` — the column list is irrelevant.
12. **CTEs over derived tables**: named, linear, reusable, and the only route to recursion.
13. Recursive CTE = base case + `UNION ALL` + step joining back to the CTE. **`UNION ALL`, not `UNION`.** A data cycle loops forever.
14. **`GROUP BY` collapses rows; a window keeps them.** That is the whole reason windows exist.
15. **`ROW_NUMBER` / `RANK` / `DENSE_RANK`: different-on-ties / same-then-skip / same-then-no-gap.** Use `DENSE_RANK` for "Nth highest".
16. **A window `ORDER BY` without a unique tie-breaker is non-deterministic** — verified giving Meera `rn=5` and Ravi `rn=4` arbitrarily.
17. **Windows are not allowed in `WHERE`/`HAVING`** — wrap in a CTE and filter outside.
18. Default window frame with `ORDER BY` is **`RANGE`**, so tied rows share a running total. Use `ROWS` when you mean row counts.
19. `LAG`/`LEAD` replace a correlated "previous row" subquery.
20. **The gap trick — `value − ROW_NUMBER()` is constant within a run** — answers every consecutive/streak question.

### Common wrong answers

| Candidate says / writes | Why it loses marks | Instead |
|---|---|---|
| Uses `INNER JOIN` for "all departments and their headcount" | Drops departments with no employees | `LEFT JOIN` from `dept` |
| Puts the optional side's filter in `WHERE` on a `LEFT JOIN` | Turns it into an inner join — verified losing HR and Research | Move it into `ON` |
| "`LEFT JOIN` returns more rows than `INNER` always" | Equal when every left row matches | "Never fewer; more only when something is unmatched" |
| `NOT IN` with a nullable subquery column | Silently returns nothing | `NOT EXISTS` |
| Uses `NATURAL JOIN` | Depends on column names you didn't write | `ON` or `USING` |
| "`EXISTS` is always faster than `IN`" | Usually the same plan now | Give the clarity/NULL-safety answer |
| Forgets `DISTINCT` on a join used as a semi-join | Duplicate rows | Or use `EXISTS` |
| `RANK()` for "Nth highest" | Rank N may not exist after a tie | `DENSE_RANK()` |
| `ROW_NUMBER()` for "all top earners" | Returns only one of the tied employees | `DENSE_RANK()`/`RANK()` |
| Filters on a window function in `WHERE` | Error — windows run after `WHERE` | Wrap in a CTE |
| Bare column with `GROUP BY` for top-per-group | Wrong (M4 §4.4) | Window or correlated subquery |
| `UNION` in a recursive CTE | Dedupes each iteration; slower and may alter results | `UNION ALL` |
| Self-join with one alias | Ambiguous column error | Two distinct aliases |

### Interview Q&A bank

**Q1. Explain every join type.**
Inner keeps matching pairs; left keeps all left rows; right keeps all right rows; full keeps both unmatched sides; cross is every combination. On an 8-row `emp` and 4-row `dept` with one unmatched row each: 7, 8, 8, 9, 32.

**Q2. `LEFT JOIN` vs `INNER JOIN` — when does it matter?**
Whenever the left table has rows with no match. "Departments and their headcount" needs `LEFT`, or empty departments vanish.

**Q3. Difference between a condition in `ON` and in `WHERE` for an outer join?**
`ON` decides what counts as a match and preserves unmatched rows; `WHERE` filters after the join and will discard the NULL-extended rows, degrading the outer join to an inner one.
*Follow-up:* "So how do you find unmatched rows?" → Deliberately: `WHERE b.key IS NULL`.

**Q4. What is a self-join? Give a use.**
A table joined to itself with two aliases — employees with their managers, or employees earning more than their manager. Use `LEFT` to keep the manager-less CEO.

**Q5. Employees earning more than their manager?**
```sql
SELECT e.name FROM emp e JOIN emp m ON e.manager_id = m.eid WHERE e.salary > m.salary;
```
Returns Omar (95000 vs Asha 90000) and Sara (85000 vs Dev 60000).

**Q6. Correlated vs non-correlated subquery?**
A correlated subquery references the outer row and conceptually runs per row; a non-correlated one is independent and runs once. Test: can the inner query run on its own?

**Q7. `IN` vs `EXISTS` vs `JOIN`?**
Same results here. `IN` compares to a list, `EXISTS` tests existence and can short-circuit, a join gives access to the inner table's columns but needs `DISTINCT`. Modern optimizers usually produce the same plan, so choose for clarity — and remember `NOT IN` is NULL-unsafe.

**Q8. Why is `NOT EXISTS` preferred over `NOT IN`?**
If the subquery yields a NULL, `NOT IN` evaluates to UNKNOWN for every row and returns nothing, with no error. `NOT EXISTS` is NULL-safe.

**Q9. CTE vs subquery?**
A CTE is named, reads linearly, can be referenced more than once, and supports recursion. A derived table nests and must be repeated.

**Q10. How do you query a hierarchy?**
Recursive CTE: base case (`manager_id IS NULL`), `UNION ALL`, step joining the CTE to the table. Carry a `level` and a `path` column. Guard against cycles.

**Q11. `GROUP BY` vs window function?**
`GROUP BY` collapses rows into one per group; a window computes over a set of rows and keeps every row. "Each employee next to their department average" needs a window.

**Q12. `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`?**
On ties: different numbers / same then skip / same then no gap. Our 75000 tie gives rn 4 and 5, rank 4 and 4 then 6, dense 4 and 4 then 5.

**Q13. Second highest salary — give me two ways, and handle ties.**
`DENSE_RANK() = 2` in a CTE, or `SELECT DISTINCT salary … ORDER BY salary DESC LIMIT 1 OFFSET 1`. Both give 90000. Ties are handled because `DISTINCT`/`DENSE_RANK` rank salaries, not people — select names to return everyone on that salary.

**Q14. Top 2 earners per department?**
`DENSE_RANK() OVER (PARTITION BY did ORDER BY salary DESC)` in a CTE, filtered `<= 2` outside it. `DENSE_RANK` returns both tied employees; `ROW_NUMBER` would return one.

**Q15. Can you use a window function in `WHERE`?**
No — windows are computed after `WHERE`. Wrap the query in a CTE or derived table and filter there.

**Q16. Find and delete duplicate rows keeping one.**
Find: `GROUP BY cols HAVING COUNT(*) > 1`. Delete: keep `MIN(rowid)`/`MIN(pk)` per group, or `ROW_NUMBER() … rn > 1` in a CTE. In MySQL, wrap the subquery in a derived table or it rejects the self-reference.

**Q17. Running total in SQL?**
`SUM(x) OVER (ORDER BY d ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`. Note the default frame is `RANGE`, which gives tied rows the same total.

**Q18. Find consecutive runs / the longest streak.**
`value − ROW_NUMBER() OVER (ORDER BY value)` is constant within a run; group by it and take `MIN`, `MAX`, `COUNT`.

### Practice

Use the §5.0 dataset. Predict the row count before running each one.

1. Every department with its headcount and average salary, **including empty departments showing 0**. Which join, and why does `COUNT(*)` give the wrong answer for Research?
2. Employees with no department **and** departments with no employees, in **one** result set with a `kind` column saying which.
3. For each employee: their name, their manager's name, and their manager's manager's name. (Two self-joins — mind the NULLs.)
4. Departments where **every** employee earns above 55000. *(Hint: there's no `FOR ALL` in SQL — use `NOT EXISTS` of a counterexample.)*
5. The 3rd highest **distinct** salary, three different ways. Then the 3rd highest *employee* by salary — explain why the answers differ.
6. Each employee's salary as a percentage of their department's total payroll, to one decimal place.
7. Employees hired within 6 months of the person hired immediately before them. *(`LAG` on `hired`.)*
8. Pairs of employees in the same department earning the same salary, each pair listed once. *(Self-join — what stops you getting both `(Ravi, Meera)` and `(Meera, Ravi)`, plus `(Ravi, Ravi)`?)*
9. Rewrite `SELECT … WHERE did IN (SELECT did FROM dept WHERE city='Pune')` as a join and as an `EXISTS`. Which would you ship, and why?
10. The full management chain for every employee as a string, plus their depth. Then break it: give Dev a `manager_id` pointing at Sara and explain exactly what happens when you re-run it.
11. In `visit(day) = 1,2,3,7,8,11`, find the **longest** consecutive run, returning its start, end and length.
12. Why does the correlated top-earner query in §5.6 omit Omar, and what would you change if the business wants him listed?

---

## Exit checklist

```
[ ] I can predict the row count of any join on this dataset before running it
[ ] I can explain why an unmatched row happens, from NULL comparison rules
[ ] I can explain ON vs WHERE on an outer join and show the failure
[ ] I can write an anti-join three ways and say which is NULL-safe
[ ] I can explain why NATURAL JOIN is dangerous with a concrete example
[ ] I can write a self-join for managers, and know why it needs LEFT
[ ] I can tell a correlated subquery from a non-correlated one instantly
[ ] I can give the honest IN vs EXISTS vs JOIN answer, including the plan point
[ ] I can write a recursive CTE for a hierarchy, both directions, and name the cycle risk
[ ] I can state the GROUP BY vs window distinction in one sentence
[ ] I can produce the ROW_NUMBER / RANK / DENSE_RANK table on tied data
[ ] I know windows can't go in WHERE, and why, and what to do instead
[ ] I know the default frame is RANGE, not ROWS
[ ] I can write Nth highest salary four ways and discuss ties and missing N
[ ] I can do top-N per group with and without window functions
[ ] I can find and delete duplicates, and know the MySQL self-reference gotcha
[ ] I can write a running total and a moving average from memory
[ ] I can do the value-minus-row_number gap trick without hesitating
```

---

## Next

**Part 8: M6 — SQL III: DDL, Constraints, Views and Programmability.** The other half of SQL: `CREATE`/`ALTER`/`DROP`, the full **`DELETE` vs `TRUNCATE` vs `DROP`** comparison, constraints in practice, **views** and when one is updatable, materialized views, stored procedures vs functions, triggers, cursors, `GRANT`/`REVOKE`, and **SQL injection with prepared statements** — which is asked far more often than its size suggests.
