# DBMS Placement Handbook — Part 6
# Module 4: SQL I — Querying

**Module 4 · 3 hours · Tier 1 · Requires: M1 (keys, NULL semantics)**

---

## Why this module matters

From here on, DBMS stops being a theory subject. Product companies put a table in front of you and ask for queries, and the SQL round is where preparation is visible within thirty seconds.

This module builds the foundation that M5 (joins, subqueries, windows) stands on, and it does it around **one diagram**: the logical order of execution. That single picture answers `WHERE` vs `HAVING`, why you can't put an aggregate in `WHERE`, why a `SELECT` alias works in `ORDER BY` but not in `WHERE`, and why `DISTINCT` can't see a column you didn't select. Learn the order and most SQL confusion evaporates.

The organising principle:

> **A `SELECT` is not read top to bottom. The engine builds a row set with `FROM`, throws away rows with `WHERE`, collapses what's left into groups with `GROUP BY`, throws away groups with `HAVING`, and only then computes the columns you asked for. Every rule about what you may write where follows from that sequence.**

**Everything below was executed** (Python 3.12 `sqlite3`, SQLite 3.49.1) against one dataset, printed below. Results are real output. Three places where SQLite is more permissive than standard SQL are labelled where they occur — including one that most study material gets wrong.

---

## 4.0 The dataset

Used for this module and M5. It deliberately contains NULLs (a department-less employee, a manager-less CEO, missing commissions), salary ties, and an empty department.

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

Four things planted on purpose: **Omar has no department**, **Asha has no manager**, **five of eight commissions are NULL**, **Research (40) has no employees**, and **salaries 75000 and 60000 are each shared by two people**. Every one of those creates a question interviewers ask.

---

## 4.1 The logical order of execution

**The single most useful diagram in SQL.** This is the *logical* order — what the result must be equivalent to. The optimizer may physically do something else entirely (M7), but the answer always matches this sequence.

```
   written order                       EXECUTION order
   ─────────────                       ───────────────
   SELECT    ─────┐                 1. FROM / JOIN      build the working row set
   FROM      ─────┼──►              2. WHERE            discard ROWS
   WHERE     ─────┤                 3. GROUP BY         collapse rows into groups
   GROUP BY  ─────┤                 4. HAVING           discard GROUPS
   HAVING    ─────┤                 5. SELECT           compute output columns + aliases
   ORDER BY  ─────┤                 6. DISTINCT         remove duplicate output rows
   LIMIT     ─────┘                 7. ORDER BY         sort the result
                                    8. LIMIT / OFFSET   cut the window
```

### Five consequences, each one a real interview question

| Consequence | Why |
|---|---|
| **`WHERE` can't use an aggregate** | Aggregates don't exist until step 3–4. Verified: `WHERE COUNT(*) > 1` → `OperationalError: misuse of aggregate: count()`. **That is the entire reason `HAVING` exists.** |
| **`HAVING` can use aggregates** | It runs after grouping |
| **`SELECT` aliases work in `ORDER BY`** | `ORDER BY` (7) runs after `SELECT` (5). Verified below |
| **`SELECT` aliases do *not* work in `WHERE`** | `WHERE` (2) runs before `SELECT` (5) — **standard SQL; see the dialect note** |
| **`DISTINCT` applies to the selected columns only** | It runs after `SELECT`, so it can't see columns you didn't output |

Verified — the alias works in `ORDER BY`:

```sql
SELECT name, salary*12 AS annual FROM emp ORDER BY annual DESC LIMIT 3;
```
```
    name | annual
    -----+--------
    Omar | 1140000
    Asha | 1080000
    Sara | 1020000
```

### Dialect note — and this one matters

**SQLite accepts a `SELECT` alias in `WHERE`.** Verified: `WHERE annual > 1000000` ran fine and returned Asha and Sara. **This is a SQLite leniency, not standard SQL.** In MySQL, PostgreSQL and SQL Server the same query is an error (`Unknown column 'annual' in 'where clause'`).

| Clause | Standard / MySQL / Postgres | SQLite |
|---|---|---|
| Alias in `WHERE` | **Error** | Allowed (verified) |
| Alias in `GROUP BY` | MySQL yes, Postgres yes | Allowed |
| Alias in `HAVING` | **MySQL yes, Postgres no** | Allowed |
| Alias in `ORDER BY` | Yes everywhere | Allowed |

**In an interview, answer for standard SQL:** the alias is unavailable in `WHERE` because `WHERE` is evaluated before `SELECT`; repeat the expression, or wrap the query in a derived table (M5). Reasoning from the execution order gets you the right answer on every engine; memorising SQLite's behaviour gets you a wrong one.

---

## 4.2 `WHERE` vs `HAVING`

> **`WHERE` filters rows before grouping. `HAVING` filters groups after aggregation.**

Baseline — group by department:

```sql
SELECT did, COUNT(*) AS headcount, AVG(salary) AS avg_sal
FROM emp GROUP BY did ORDER BY did;
```
```
    did  | headcount | avg_sal
    -----+-----------+------------------
    NULL | 1         | 95000.0
    10   | 3         | 80000.0
    20   | 3         | 68333.33333333333
    30   | 1         | 50000.0
```

**Note the `NULL` group**: `GROUP BY` collects all NULLs into one group (M1, §1.9, trap 4), so Omar forms a department-less group of his own. Interviewers plant exactly this.

**`WHERE` — filter rows first.** Excluding everyone under 60000 removes Nita, and HR disappears entirely because it had no other employees:

```sql
SELECT did, AVG(salary) AS avg_sal FROM emp
WHERE salary >= 60000 GROUP BY did ORDER BY did;
```
```
    did  | avg_sal
    -----+------------------
    NULL | 95000.0
    10   | 80000.0
    20   | 68333.33333333333
```

**`HAVING` — filter groups.** Every employee is still counted; only whole departments are dropped:

```sql
SELECT did, AVG(salary) AS avg_sal FROM emp
GROUP BY did HAVING AVG(salary) >= 70000 ORDER BY did;
```
```
    did  | avg_sal
    -----+---------
    NULL | 95000.0
    10   | 80000.0
```

**Both together** — rows filtered, then grouped, then groups filtered:

```sql
SELECT did, COUNT(*) AS n FROM emp
WHERE salary > 55000 GROUP BY did HAVING COUNT(*) > 1 ORDER BY did;
```
```
    did | n
    ----+--
    10  | 3
    20  | 3
```

| | `WHERE` | `HAVING` |
|---|---|---|
| Acts on | Individual **rows** | **Groups** |
| Runs | Before `GROUP BY` | After `GROUP BY` |
| Aggregates allowed | **No** | **Yes** |
| Without `GROUP BY` | Normal filter | Treats the whole table as one group |
| Performance | **Preferred** — fewer rows to group | Only when the condition needs an aggregate |

**The practical rule:** if a condition can go in `WHERE`, put it there. Filtering early means less data to sort, group and aggregate. Putting a non-aggregate condition in `HAVING` usually works and is usually slower.

---

## 4.3 Aggregate functions and NULL

```sql
SELECT COUNT(*) AS count_star, COUNT(commission) AS count_comm,
       SUM(commission) AS sum_comm, AVG(commission) AS avg_comm,
       AVG(COALESCE(commission,0)) AS avg_with_zeros,
       MIN(commission) AS min_c, MAX(commission) AS max_c
FROM emp;
```
```
    count_star | count_comm | sum_comm | avg_comm          | avg_with_zeros | min_c | max_c
    -----------+------------+----------+-------------------+----------------+-------+------
    8          | 3          | 16000    | 5333.333333333333 | 2000.0         | 3000  | 8000
```

**Read that row carefully — it contains four exam questions:**

| Observation | Rule |
|---|---|
| `COUNT(*)` = 8 but `COUNT(commission)` = 3 | `COUNT(*)` counts rows; `COUNT(col)` counts non-NULLs |
| `SUM` = 16000 over 3 values | NULLs skipped, not treated as 0 |
| `AVG` = **5333.33**, not 2000 | **`AVG` divides by the non-NULL count (16000/3), not by 8** |
| `AVG(COALESCE(commission,0))` = **2000** | 16000/8 — the answer the business usually wants |

> **`AVG` is the single most common NULL mistake in SQL.** "Average commission" has two different correct answers and you must say which you computed. Raising that ambiguity unprompted is a strong interview signal.

`MIN`/`MAX` also ignore NULLs. And on an empty set: **`COUNT` returns 0, every other aggregate returns NULL** — not 0. That is why `SUM` of no rows is NULL and needs `COALESCE(SUM(x),0)` if you want a number.

```sql
SELECT COUNT(DISTINCT salary) AS distinct_salaries, COUNT(salary) AS all_salaries FROM emp;
```
```
    distinct_salaries | all_salaries
    ------------------+-------------
    6                 | 8
```

Eight salaries, six distinct — the two ties (75000 twice, 60000 twice) collapse. `DISTINCT` inside an aggregate is the clean way to count unique values.

---

## 4.4 `GROUP BY` rules, and the bare-column trap

**The rule in standard SQL:** every column in `SELECT` must either appear in `GROUP BY` or be inside an aggregate. Anything else is ambiguous — a group has many rows, so "the name" of a group is undefined.

**MySQL 5.7+ enforces this by default** (`ONLY_FULL_GROUP_BY`) and rejects the query. **SQLite does not.** Verified:

```sql
SELECT did, name, MAX(salary) FROM emp GROUP BY did ORDER BY did;
```
```
    did  | name | max(salary)
    -----+------+------------
    NULL | Omar | 95000
    10   | Asha | 90000
    20   | Sara | 85000
    30   | Nita | 50000
```

That looks *right* — Asha really does earn 90000. Which is exactly what makes the trap dangerous: SQLite has a documented special case where, with a single `MIN()` or `MAX()`, bare columns are taken from the matching row. **Change the aggregate and the illusion collapses.** Verified:

```sql
SELECT did, name, AVG(salary) AS avg_sal FROM emp GROUP BY did ORDER BY did;
```
```
    did  | name | avg_sal
    -----+------+------------------
    10   | Asha | 80000.0          <- Asha earns 90000, not the average
    20   | Dev  | 68333.33333333333
```

And asking for two extremes at once makes it unambiguous — `name` cannot possibly match both:

```sql
SELECT did, name, MAX(salary) AS top, MIN(salary) AS bottom FROM emp GROUP BY did ORDER BY did;
```
```
    did  | name | top   | bottom
    -----+------+-------+-------
    10   | Ravi | 90000 | 75000     <- Ravi earns 75000; "top" is Asha's salary
    20   | Dev  | 85000 | 60000     <- Dev earns 60000; "top" is Sara's salary
```

**Dept 10 reports Ravi next to a top salary of 90000, which is Asha's.** The row is a fabrication stitched from two different employees.

> **The lesson:** never select a bare non-grouped column. To get *the employee who earns the most per department* you need a window function or a correlated subquery — that is the "top-N per group" problem, and it is M5's centrepiece. **A bare column is not a shortcut to it; it is a wrong answer that sometimes looks right.**

Other `GROUP BY` facts worth holding:

- `GROUP BY` puts **all NULLs in one group**.
- You may group by an expression: `GROUP BY strftime('%Y', hired)` (MySQL: `YEAR(hired)`).
- Grouping by multiple columns groups by the **combination**.
- `GROUP BY` output is **not** sorted — add `ORDER BY` if you need order. (Older MySQL sorted as a side effect; relying on that broke when it stopped.)

---

## 4.5 Operators

```sql
SELECT name, salary FROM emp WHERE salary BETWEEN 60000 AND 85000 ORDER BY salary, name;
```
```
    Dev 60000 | Imran 60000 | Meera 75000 | Ravi 75000 | Sara 85000      (5 rows)
```

**`BETWEEN` is inclusive on both ends** — both 60000 and 85000 appear. The classic off-by-one bug is using `BETWEEN` on dates with a time component: `BETWEEN '2026-01-01' AND '2026-01-31'` silently excludes everything after midnight on the 31st. Use `>= '2026-01-01' AND < '2026-02-01'` for date ranges.

| Operator | Verified example | Result |
|---|---|---|
| `LIKE '%a%'` | contains "a" | 7 of 8 names (all but Dev) |
| `LIKE '_a%'` | **second** letter is "a" | `Ravi`, `Sara` |
| `IN (10,30)` | `did` in a list | Asha, Meera, Nita, Ravi |
| `IS NULL` | `did IS NULL` | `Omar` |
| `IS NOT NULL` | `commission IS NOT NULL` | Dev, Imran, Ravi |

**Wildcards:** `%` = any number of characters (including none), `_` = exactly one. To search for a literal `%`, use `LIKE '%\%%' ESCAPE '\'`.

**`LIKE` and case:** MySQL's default collation is case-**insensitive**; Postgres is case-**sensitive** (`ILIKE` for insensitive); SQLite is case-insensitive for ASCII only. Never assume — and know that a leading-wildcard `LIKE '%a%'` **cannot use an index** (M7, SARGability).

---

## 4.6 `CASE`

SQL's conditional expression. Usable anywhere an expression is allowed — `SELECT`, `WHERE`, `ORDER BY`, and inside aggregates.

```sql
SELECT name, salary,
       CASE WHEN salary >= 90000 THEN 'senior'
            WHEN salary >= 70000 THEN 'mid'
            ELSE 'junior' END AS band
FROM emp ORDER BY salary DESC, name;
```
```
    name  | salary | band
    ------+--------+-------
    Omar  | 95000  | senior
    Asha  | 90000  | senior
    Sara  | 85000  | mid
    Meera | 75000  | mid
    Ravi  | 75000  | mid
    Dev   | 60000  | junior
    Imran | 60000  | junior
    Nita  | 50000  | junior
```

Conditions are evaluated **in order** and the first match wins — which is why the `>= 70000` branch never steals Asha, even though 90000 also satisfies it. Reorder the branches and the query breaks. Without `ELSE`, unmatched rows get NULL.

### `CASE` inside an aggregate: the pivot pattern

**Worth memorising** — it turns rows into columns, and it is how you answer "show me counts side by side":

```sql
SELECT d.dname,
       SUM(CASE WHEN e.salary >= 75000 THEN 1 ELSE 0 END) AS high_paid,
       SUM(CASE WHEN e.salary <  75000 THEN 1 ELSE 0 END) AS rest
FROM dept d LEFT JOIN emp e ON e.did = d.did
GROUP BY d.did ORDER BY d.dname;
```
```
    dname       | high_paid | rest
    ------------+-----------+-----
    Engineering | 3         | 0
    HR          | 0         | 1
    Research    | 0         | 0        <- empty dept survives, thanks to LEFT JOIN
    Sales       | 1         | 2
```

Two things in one query: the pivot, and the reason it uses `LEFT JOIN` — **Research has no employees, and an inner join would have dropped it entirely.** Reporting zero is almost always what the business wants. (Joins are M5; this is the preview.)

`COUNT(CASE WHEN cond THEN 1 END)` works identically, exploiting the fact that `COUNT` ignores NULLs — no `ELSE` needed.

---

## 4.7 Set operators

| Operator | Returns | Duplicates |
|---|---|---|
| `UNION` | Rows in either | **Removed** (costs a sort/hash) |
| `UNION ALL` | Rows in either | **Kept** (cheaper — prefer it when duplicates are impossible or harmless) |
| `INTERSECT` | Rows in both | Removed |
| `EXCEPT` (Oracle: `MINUS`) | In the first, not the second | Removed |

Verified — Asha is in dept 10 *and* earns over 80000, so she is the duplicate that shows the difference:

```sql
SELECT name FROM emp WHERE did = 10
UNION
SELECT name FROM emp WHERE salary > 80000 ORDER BY name;
-- Asha, Meera, Omar, Ravi, Sara                    (5 rows)
```
```sql
... UNION ALL ...
-- Asha, Asha, Meera, Omar, Ravi, Sara              (6 rows)
```

```sql
SELECT did FROM emp WHERE salary > 70000
INTERSECT
SELECT did FROM emp WHERE commission IS NOT NULL;
-- 10, 20
```

```sql
SELECT did FROM dept
EXCEPT
SELECT did FROM emp WHERE did IS NOT NULL ORDER BY did;
-- 40          <- Research: a department with no employees
```

That `EXCEPT` is the **anti-join** pattern again (M1, §1.9) — and note the `WHERE did IS NOT NULL` guard, which keeps Omar's NULL out of the subtracted set.

**Rules for all set operators:** both queries need the **same number of columns** with compatible types; column names come from the **first** query; and a single `ORDER BY` goes at the very end, applying to the combined result.

> **`UNION` vs `JOIN`**, asked surprisingly often: `UNION` stacks results **vertically** (more rows, same columns); a join combines them **horizontally** (more columns, matched rows).

---

## 4.8 `ORDER BY`, `LIMIT` and `DISTINCT`

```sql
SELECT name, salary FROM emp ORDER BY salary DESC LIMIT 2 OFFSET 2;
```
```
    Sara | 85000
    Ravi | 75000
```

Rows 3–4 by salary. **But there is a bug waiting here:** Ravi and Meera both earn 75000, so which one lands in position 4 is **not defined**. Page 2 of a listing can show a row that page 1 also showed, or skip one. **Always add a tie-breaker to make pagination deterministic:** `ORDER BY salary DESC, eid`. This is a real production bug and a good thing to mention unprompted.

### NULL ordering

```sql
SELECT name, commission FROM emp ORDER BY commission LIMIT 4;
-- Asha NULL | Meera NULL | Sara NULL | Nita NULL      <- NULLs FIRST ascending
SELECT name, commission FROM emp ORDER BY commission DESC LIMIT 4;
-- Dev 8000 | Ravi 5000 | Imran 3000 | Asha NULL       <- NULLs last descending
```

| Engine | Default for `ORDER BY col ASC` |
|---|---|
| SQLite, MySQL, SQL Server | NULLs **first** |
| PostgreSQL, Oracle | NULLs **last** |

Postgres and Oracle support explicit `NULLS FIRST` / `NULLS LAST`; in MySQL you emulate it with `ORDER BY col IS NULL, col`. **Don't rely on the default across engines.**

Other notes: `LIMIT n OFFSET m` is MySQL/Postgres/SQLite; SQL Server uses `OFFSET … FETCH NEXT`, Oracle uses `FETCH FIRST` (or `ROWNUM` in older code). Large `OFFSET` values are slow because the engine still generates and discards those rows — keyset pagination (`WHERE id > :last_seen`) is the scalable fix.

`DISTINCT` applies to the **whole selected row**, not one column: `SELECT DISTINCT did, salary` gives distinct *pairs*. There is no "distinct on one column" in standard SQL — that is `GROUP BY`, or Postgres's `DISTINCT ON`.

---

## 4.9 Consolidation

### Must remember (module)

1. **Execution order: `FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT`.** Derive, don't memorise, everything below.
2. **`WHERE` can't contain an aggregate** — verified error. That is why `HAVING` exists.
3. `WHERE` filters rows, `HAVING` filters groups. **Prefer `WHERE`** when the condition allows it.
4. A `SELECT` alias is usable in `ORDER BY` but **not in `WHERE`** in standard SQL/MySQL/Postgres. *(SQLite permits it — verified — but answer for the standard.)*
5. **`COUNT(*)` counts rows; `COUNT(col)` counts non-NULLs; `AVG` divides by the non-NULL count.**
6. On an empty set, `COUNT` = 0 and **every other aggregate = NULL**. Use `COALESCE(SUM(x),0)`.
7. `GROUP BY` puts **all NULLs in one group**; `DISTINCT` keeps one NULL.
8. **Never select a bare non-grouped column.** MySQL rejects it; SQLite silently fabricates a row — verified producing Ravi's name beside Asha's salary.
9. `GROUP BY` does **not** sort. Add `ORDER BY`.
10. **`BETWEEN` is inclusive.** Don't use it on dates with times.
11. `LIKE`: `%` = any run of characters, `_` = exactly one. A leading `%` cannot use an index.
12. `CASE` branches are evaluated **in order**; first match wins; no `ELSE` means NULL.
13. **`SUM(CASE WHEN … THEN 1 ELSE 0 END)` is the pivot pattern.** Learn it as one unit.
14. `UNION` dedupes, `UNION ALL` doesn't and is cheaper. Same column count, types from the first query, one `ORDER BY` at the end.
15. `UNION` stacks vertically; a join combines horizontally.
16. **`LIMIT`/`OFFSET` without a unique tie-breaker in `ORDER BY` is non-deterministic.** Real pagination bug.
17. NULL sort order differs by engine: first in MySQL/SQLite/SQL Server, last in Postgres/Oracle.

### Common wrong answers

| Candidate says | Why it loses marks | Say instead |
|---|---|---|
| "`WHERE` and `HAVING` are the same, `HAVING` is just for `GROUP BY`" | Misses that `HAVING` can aggregate and `WHERE` cannot | "`WHERE` filters rows before grouping; `HAVING` filters groups after, and only `HAVING` may use aggregates" |
| Writes `WHERE COUNT(*) > 1` | Hard error | Use `HAVING` |
| "`COUNT(*)` and `COUNT(col)` are the same" | Differ whenever the column has NULLs | — |
| "`AVG` treats NULL as 0" | It excludes the row from the divisor | "16000/3, not 16000/8 — `COALESCE` if you want zeros counted" |
| "`SUM` of an empty set is 0" | It's NULL | — |
| Selects a bare column with `GROUP BY` | Ambiguous; wrong in MySQL, misleading in SQLite | "Use a window function or correlated subquery for top-N per group" |
| "`UNION` and `UNION ALL` are the same but one is faster" | Different results, not just speed | "`UNION` removes duplicates — that's why it costs more" |
| "`UNION` joins two tables" | Confuses vertical with horizontal | — |
| "`BETWEEN` excludes the endpoints" | It includes both | — |
| "`DISTINCT col1, col2` gives distinct values of each" | It gives distinct **pairs** | — |
| Relies on `GROUP BY` for ordering | Not guaranteed | Add `ORDER BY` |
| Paginates with `LIMIT/OFFSET` on a non-unique sort | Rows repeat or vanish between pages | Add a unique tie-breaker |

### Interview Q&A bank

**Q1. What's the logical order of execution of a `SELECT`?**
`FROM`/`JOIN` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT`. It's logical, not physical — the optimizer can reorder as long as the result matches.
*Follow-up:* "So why can't `WHERE` use an aggregate?" → Aggregates don't exist until grouping, two steps later.

**Q2. `WHERE` vs `HAVING`?**
Rows before grouping vs groups after aggregation; only `HAVING` may use aggregates. Prefer `WHERE` for anything non-aggregate, because filtering early means less to group.

**Q3. Can you use a column alias in `WHERE`? In `ORDER BY`?**
Not in `WHERE` (it's evaluated before `SELECT`); yes in `ORDER BY`. Repeat the expression or wrap it in a derived table.

**Q4. `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`?**
Rows; non-NULL values; distinct non-NULL values. On our data: 8, 3, and 6 distinct salaries from 8.

**Q5. How do aggregates treat NULL?**
All of them ignore NULLs except `COUNT(*)`. So `AVG` divides by the count of non-NULLs — `AVG(commission)` = 5333.33, while `AVG(COALESCE(commission,0))` = 2000. Say which you intend.

**Q6. What does `SUM` return over zero rows?**
NULL, not 0. `COUNT` is the only aggregate that returns 0.

**Q7. Why is `SELECT did, name, MAX(salary) ... GROUP BY did` wrong?**
A group has many names, so `name` is undefined. MySQL rejects it under `ONLY_FULL_GROUP_BY`; SQLite returns an arbitrary row's name — asking for `MAX` and `MIN` together shows a name matching neither. For the actual top earner per department, use a window function or a correlated subquery.

**Q8. `UNION` vs `UNION ALL`?**
Both stack results; `UNION` removes duplicates and therefore sorts or hashes, `UNION ALL` doesn't. Use `UNION ALL` unless you need dedup.

**Q9. How do you pivot rows into columns in plain SQL?**
`SUM(CASE WHEN cond THEN 1 ELSE 0 END) AS label` per output column, with `GROUP BY` on the row dimension.

**Q10. How do you find values in table A not in table B?**
`EXCEPT`, `NOT EXISTS`, or `LEFT JOIN ... IS NULL`. Avoid `NOT IN` unless the column is `NOT NULL` (M1, §1.9).

**Q11. `BETWEEN` — inclusive or exclusive?**
Inclusive both ends. Avoid on timestamps: use `>= start AND < next_day`.

**Q12. Where do NULLs sort?**
Engine-dependent: first in MySQL/SQLite/SQL Server, last in Postgres/Oracle. Be explicit with `NULLS FIRST`/`NULLS LAST` where supported.

**Q13. What's wrong with `ORDER BY salary DESC LIMIT 10 OFFSET 10` for page 2?**
If salaries tie across the page boundary, the order within the tie is undefined, so rows can repeat or be skipped. Add a unique tie-breaker like `eid`.

### Practice

Run these against the §4.0 dataset and check your prediction against the output.

1. Average salary per department, **only for departments averaging above 65000**, showing the department *name*. Which clause does the 65000 filter go in?
2. Headcount per city. (Careful: Research has `city = NULL` and no employees — decide what your query should report, then make it do that.)
3. Everyone whose commission is **not** 5000, **including** those with no commission recorded. Why does the obvious query miss four people?
4. Count employees hired per year, highest first. *(Hint: `strftime('%Y', hired)` in SQLite, `YEAR(hired)` in MySQL.)*
5. One row per department with three columns: `seniors` (≥90000), `mids` (70000–89999), `juniors` (<70000). Include empty departments showing zeros.
6. The two distinct highest salaries in the company — **distinct values**, so the 75000 tie counts once. *(Without window functions; M5 gives you more tools.)*
7. Predict then verify: `SELECT COUNT(commission), COUNT(*), AVG(commission), SUM(commission)/COUNT(*) FROM emp;` — explain why the third and fourth columns differ.
8. Why does `SELECT did, COUNT(*) FROM emp GROUP BY did` return four rows when `dept` has four rows — but a *different* four? Name both discrepancies.
9. Write a query that is correct in MySQL but errors in Postgres, using only this module's material. *(Hint: `HAVING` and an alias.)*
10. Employees sharing a salary with at least one other employee, with that salary. Which clause does the "at least one other" condition belong in?

---

## Exit checklist

```
[ ] I can write the eight-step execution order from memory
[ ] I can derive the WHERE/HAVING/alias rules from it instead of recalling them
[ ] I know an aggregate in WHERE is an error, and why
[ ] I can state what each aggregate does with NULL, including AVG's divisor and empty-set NULL
[ ] I can explain the bare-column trap and why SQLite's output is misleading
[ ] I know GROUP BY collects all NULLs into one group and does not sort
[ ] I can write the SUM(CASE WHEN ...) pivot without looking it up
[ ] I know when to use UNION vs UNION ALL, and the column/type/ORDER BY rules
[ ] I can list three ways to express an anti-join and say which is NULL-safe
[ ] I know BETWEEN is inclusive and why that breaks on timestamps
[ ] I can explain why LIMIT/OFFSET pagination needs a unique tie-breaker
[ ] I know NULL sort order differs by engine
```

---

## Next

**Part 7: M5 — SQL II: Joins, Subqueries and Windows.** The centrepiece of the SQL round: every join type traced row by row, the self-join, `IN` vs `EXISTS` vs `JOIN`, correlated subqueries, CTEs and recursive CTEs for hierarchies, window functions, and **the query drill bank** — Nth highest salary four ways compared on ties, duplicates, top-N per group, employees earning more than their manager, consecutive rows and running totals. Every query executed.
