# DBMS Placement Handbook — Part 3
# Module 1: The Relational Model and Keys

**Module 1 · 2–3 hours · Tier 1 · Requires: M0**

---

## Why this module matters

This is the module people skip, and skipping it is why normalization later feels like memorising rules. **2NF, 3NF and BCNF are all defined in terms of candidate keys.** If "candidate key" is a vague word, every normal form becomes a chant instead of a decision you can make.

It is also pure interview currency on its own: the key family is asked in some form in nearly every core-CS segment, and the NULL traps in §1.9 are the questions interviewers use to separate people who have *written* SQL from people who have *read about* SQL.

The organising principle:

> **There is exactly one way a relational database identifies a row — a set of attributes guaranteed unique. Every key name (super, candidate, primary, alternate, composite, surrogate) is just a label describing which of those sets you are talking about and what role it plays. Foreign keys then let one table point at another table's chosen identifier, and the DBMS guarantees that pointer is never dangling.**

**Every SQL statement and every count in this module was executed** — SQL against SQLite 3.49.1, the super-key counts by brute-force enumeration. Outputs are real, and the two places where SQLite's behaviour differs from the SQL standard are labelled where they appear.

---

## 1.1 The relational model

A **relation** is a table. The formal vocabulary exists because the model came from set theory, and interviewers do use the formal words.

```
                 attributes (columns, fields)
                 ──────────────────────────────
                 roll      name      dept
               ┌─────────┬─────────┬────────┐
    tuples     │  101    │ Asha    │  CSE   │   <- one tuple = one row = one record
   (rows,      ├─────────┼─────────┼────────┤
   records)    │  102    │ Ravi    │  ECE   │
               ├─────────┼─────────┼────────┤
               │  103    │ Meera   │  CSE   │
               └─────────┴─────────┴────────┘
                 ▲
                 └─ the domain of `roll` is "positive integers":
                    the set of values the attribute may take
```

| Formal term | Everyday term | Definition |
|---|---|---|
| **Relation** | Table | A set of tuples over the same attributes |
| **Tuple** | Row, record | One entity instance |
| **Attribute** | Column, field | One named property |
| **Domain** | Column type + rule | The set of permitted atomic values for an attribute |
| **Relation schema** | Table structure | `student(roll, name, dept)` — the name plus its attributes |
| **Relation instance** | Table contents | The set of tuples right now (M0, §0.8) |
| **Degree** (arity) | Number of **columns** | 3 above |
| **Cardinality** | Number of **rows** | 3 above |

**Degree and cardinality get swapped constantly.** The memory hook: *degree* is about the *design* (it changes only when you alter the table); *cardinality* counts *contents* (it changes on every insert).

### Properties of a relation — and the one that matters

| Property | Consequence |
|---|---|
| **Every value is atomic** | No lists, no nested tables in a cell. **This is exactly what 1NF demands** (M3) |
| **No duplicate tuples** | A relation is a *set*. In theory every table has a key automatically |
| **Tuple order is irrelevant** | There is no "third row" without an `ORDER BY` |
| **Attribute order is irrelevant** | `SELECT *` column order is a convenience, not meaning |
| **Each attribute has a distinct name** | Hence table aliases when joining a table to itself (M5) |
| **All values in a column come from one domain** | The basis of domain integrity |

**The honest caveat, worth saying in an interview:** real SQL tables are *bags*, not sets — without a primary key, SQL will happily store two identical rows, and `SELECT` returns duplicates unless you ask for `DISTINCT`. The relational *model* forbids duplicates; the SQL *implementation* permits them. Knowing where theory and practice part company is the kind of thing that reads as experience.

---

## 1.2 The key family, as one picture

Seven names, one idea. Build them in this order and they stop being confusable.

```
  ALL attribute sets that are guaranteed UNIQUE  =  SUPER KEYS
  ┌──────────────────────────────────────────────────────────────┐
  │  {roll}  {roll,name}  {roll,dept}  {roll,name,dept}          │
  │  {email} {email,name} ...                                    │
  │                                                              │
  │   remove every set with a redundant attribute                │
  │   ↓                                                          │
  │  ┌────────────────────────────────────────────────┐          │
  │  │  MINIMAL super keys = CANDIDATE KEYS           │          │
  │  │        {roll}        {email}                   │          │
  │  │          │               │                     │          │
  │  │   pick exactly one       └── the rest are      │          │
  │  │          ↓                   ALTERNATE KEYS    │          │
  │  │   ┌──────────────┐                             │          │
  │  │   │ PRIMARY KEY  │  = {roll}                   │          │
  │  │   └──────────────┘                             │          │
  │  └────────────────────────────────────────────────┘          │
  └──────────────────────────────────────────────────────────────┘
```

| Key | Definition | Test for it |
|---|---|---|
| **Super key** | Any attribute set that uniquely identifies a tuple | "Can two rows share these values?" No → super key |
| **Candidate key** | A **minimal** super key — remove any attribute and uniqueness breaks | "Is every attribute in it doing work?" |
| **Primary key** | The candidate key the designer **chooses** as the official identifier | A design decision, not a mathematical fact |
| **Alternate key** | The candidate keys **not** chosen | "Candidate, minus primary" |
| **Composite key** | Any key made of **two or more** attributes | Describes shape, not role |
| **Simple key** | A key of one attribute | — |
| **Surrogate key** | A system-generated, meaningless identifier (auto-increment ID, UUID) | "Does this value mean anything outside the DB?" No → surrogate |
| **Natural key** | A key drawn from real-world data (email, ISBN, Aadhaar) | — |
| **Foreign key** | An attribute set in one relation that references a candidate key (normally the PK) of another | §1.5 |

**The two sentences that answer most key questions:**

> Every candidate key is a super key; not every super key is a candidate key (minimality).
> Every primary key is a candidate key; the others become alternate keys.

### Surrogate vs natural: the real trade-off

Interviewers ask "should the primary key be the email or an auto-increment ID?" and want reasoning, not a rule.

| | **Natural key** (e.g. `email`) | **Surrogate key** (e.g. `user_id`) |
|---|---|---|
| Meaning | Carries real-world meaning | None |
| Stability | **Risky** — people change email, companies renumber products | Never changes |
| Size in child tables | Wide (a text column repeated in every FK) | Narrow (4–8 bytes) |
| Uniqueness guaranteed by | The real world (and it lies) | The DB |
| Exposes information | Yes (an email in a URL leaks a user) | Sequential IDs leak row counts; UUIDs don't |
| Still needs the natural column? | — | Yes, as a **`UNIQUE` alternate key** |

**The answer to give:** "Surrogate primary key, with a `UNIQUE` constraint on the natural key." You get a stable, narrow identifier for foreign keys *and* keep the real-world uniqueness rule enforced. Changing an email then updates one row instead of cascading through every child table — which is precisely the kind of pain a stable key prevents.

---

## 1.3 Counting super keys (the standard numerical)

Given the candidate keys, count the super keys. The logic: **a set is a super key exactly when it contains at least one whole candidate key.** Everything else is combinatorics.

**All counts below were verified by enumerating every subset.**

### Case 1 — one candidate key of one attribute

`R(A,B,C,D)`, candidate key `{A}`. A super key is any subset containing `A`; the other 3 attributes are each in or out:

> **2^(n−1) = 2³ = 8**

```
A, AB, AC, AD, ABC, ABD, ACD, ABCD        (8 — verified)
```

### Case 2 — one candidate key of k attributes

`R(A,B,C)`, candidate key `{A,B}`. Both `A` and `B` must be present; the remaining `n−k` attributes are free:

> **2^(n−k) = 2^(3−2) = 2**

```
AB, ABC                                    (2 — verified)
```

### Case 3 — two candidate keys (inclusion–exclusion)

`R(A,B,C,D)`, candidate keys `{A}` and `{B}`. Count sets containing `A`, plus sets containing `B`, minus those counted twice:

> **2³ + 2³ − 2² = 8 + 8 − 4 = 12**

```
A, B, AB, AC, AD, BC, BD, ABC, ABD, ACD, BCD, ABCD      (12 — verified)
```

### Case 4 — mixed sizes

`R(A,B,C,D,E)`, candidate keys `{A}` and `{B,C}`:

| | Count |
|---|---|
| Contains `A` | 2⁴ = 16 |
| Contains `{B,C}` | 2³ = 8 |
| Contains both `A` and `{B,C}` | 2² = 4 |
| **Total** | 16 + 8 − 4 = **20** ✓ verified |

**The method, not the formulas:** write "contains CK₁" + "contains CK₂" − "contains both", where each term is 2 raised to (number of attributes still free). It generalises to any number of candidate keys, and it is faster than recalling four special cases.

---

## 1.4 Primary key vs unique key

| | **PRIMARY KEY** | **UNIQUE** |
|---|---|---|
| Duplicates | Rejected | Rejected |
| NULLs | **Not allowed** | **Allowed** |
| How many per table | **One** | Many |
| Index created | Yes — **clustered** by default in MySQL/InnoDB and SQL Server | Yes — non-clustered (M7) |
| Role | *The* identifier; the FK target | An enforced business rule |

### Verified: duplicates and NULLs

```sql
CREATE TABLE emp(id INT PRIMARY KEY, name TEXT);
INSERT INTO emp VALUES (1,'A');     -- ok
INSERT INTO emp VALUES (1,'B');     -- REJECTED: UNIQUE constraint failed: emp.id
```

```sql
CREATE TABLE u(id INT PRIMARY KEY, email TEXT UNIQUE);
INSERT INTO u VALUES (1,'a@x.com');  -- ok
INSERT INTO u VALUES (2,'a@x.com');  -- REJECTED: UNIQUE constraint failed: u.email
INSERT INTO u VALUES (3, NULL);      -- ok     <- UNIQUE permits NULL
INSERT INTO u VALUES (4, NULL);      -- ok     <- and permits a SECOND NULL
-- table now: [(1, 'a@x.com'), (3, None), (4, None)]
```

**Why two NULLs are allowed under `UNIQUE`:** uniqueness is tested with `=`, and `NULL = NULL` is *unknown*, not true (§1.8). Two unknowns are not provably equal, so neither violates the constraint. This is the single most satisfying NULL question to answer well, because the explanation falls straight out of three-valued logic.

**Dialect warning — this one actually differs:**

| Engine | Multiple NULLs in a `UNIQUE` column |
|---|---|
| MySQL, PostgreSQL, Oracle, SQLite | **Allowed** (many NULLs) |
| **SQL Server** | **Only one NULL** permitted |

### SQLite's primary-key quirk, labelled

A rule you should state as absolute in an interview — *"a primary key can never be NULL, because entity integrity requires every row be identifiable"* — and SQLite breaks it:

```sql
CREATE TABLE emp(id INT PRIMARY KEY, name TEXT);
INSERT INTO emp VALUES (NULL,'C');   -- ACCEPTED by SQLite (!)
-- table now: [(1, 'A'), (None, 'C')]
```

This is a documented long-standing SQLite deviation, kept for backward compatibility. It disappears with a standard-conforming table:

```sql
CREATE TABLE emp2(id INT PRIMARY KEY, name TEXT) WITHOUT ROWID;
INSERT INTO emp2 VALUES (NULL,'C');  -- REJECTED: NOT NULL constraint failed: emp2.id
```

**What to say in an interview:** a primary key is `NOT NULL` + `UNIQUE`, always. MySQL, Postgres, Oracle and SQL Server all enforce it. Mention SQLite's exception only if someone asks about SQLite specifically — it is a quirk, not a counter-argument.

---

## 1.5 Foreign keys and referential integrity

A **foreign key** is an attribute set in the *child* (referencing) table whose values must exist in the *parent* (referenced) table's candidate key — or be NULL.

```
        parent / referenced                child / referencing
        ┌──────────────────┐               ┌───────────────────────┐
        │ dept             │               │ employee              │
        │ did (PK)  dname  │◄──────────────│ eid (PK)  name   did  │
        │  10       Sales  │   references  │  1        Asha    10  │  ok
        │  20       Eng    │               │  2        Ravi    20  │  ok
        └──────────────────┘               │  3        Meera   99  │  ← REJECTED
                                           │  4        Dev    NULL │  ← allowed
                                           └───────────────────────┘
```

**Referential integrity** is the guarantee that no such pointer dangles.

```sql
CREATE TABLE dept(did INT PRIMARY KEY, dname TEXT);
CREATE TABLE e(eid INT PRIMARY KEY, did INT REFERENCES dept(did));
INSERT INTO dept VALUES (10,'Sales');

INSERT INTO e VALUES (1, 99);   -- REJECTED: FOREIGN KEY constraint failed
```

### Verified SQLite gotcha: foreign keys are OFF by default

Running the exact same statements with the pragma off and on:

```
foreign_keys = OFF   (SQLite's default):
    INSERT INTO e VALUES (1, 99)  ->  ok            ← constraint silently ignored
foreign_keys = ON:
    INSERT INTO e VALUES (1, 99)  ->  REJECTED: FOREIGN KEY constraint failed
```

So every script in this handbook starts with `PRAGMA foreign_keys = ON`. MySQL/InnoDB and Postgres enforce foreign keys by default; MySQL's older MyISAM engine *parsed and ignored* them, which is a historical reason people distrusted FKs.

### Facts about foreign keys that get asked

1. **A foreign key may be NULL** (unless separately declared `NOT NULL`) — it means "no parent yet", like an employee not assigned to a department.
2. **A foreign key may be duplicated.** Many employees in dept 10. Only the *parent* side must be unique.
3. **The referenced column must be a PK or `UNIQUE`.** Pointing at a non-unique column is meaningless and the engine rejects it.
4. **A foreign key may reference its own table** — `employee.manager_id → employee.eid`. This is the self-referencing FK behind every manager-chain question (M5).
5. **A composite FK references a composite PK**, column for column, in order.
6. Foreign keys cost something on writes (a parent lookup per insert) — the honest reason some high-throughput systems enforce them in the application instead. Say that *after* you have shown you know what they guarantee.

---

## 1.6 Referential actions: what happens when the parent goes away

Declared per foreign key as `ON DELETE <action>` / `ON UPDATE <action>`. **All four outcomes below were executed**, deleting `dept 10` while employees 1 and 2 pointed at it and employee 3 pointed at dept 20:

| Action | Delete `dept 10` | Resulting `employee` table | Use it when |
|---|---|---|---|
| **`CASCADE`** | allowed | `[(3, 20)]` — rows 1, 2 **deleted too** | The child cannot exist alone: order items, a book's copies |
| **`SET NULL`** | allowed | `[(1, None), (2, None), (3, 20)]` | The link is optional: employee survives, department unassigned |
| **`RESTRICT`** | **rejected** | unchanged | Deleting a referenced parent is a mistake — protect it |
| **`NO ACTION`** | **rejected** | unchanged | The **default** |
| `SET DEFAULT` | allowed | FK set to its column default | Rare; needs a default that exists in the parent |

```
ON DELETE CASCADE:    allowed; employee = [(3, 20)]
ON DELETE SET NULL:   allowed; employee = [(1, None), (2, None), (3, 20)]
ON DELETE RESTRICT:   REJECTED (FOREIGN KEY constraint failed)
ON DELETE NO ACTION:  REJECTED (FOREIGN KEY constraint failed)
```

**`RESTRICT` vs `NO ACTION`** — the honest answer: in most engines, including SQLite and MySQL, the observable effect is identical, as the run above shows. The specified difference is *timing*: `RESTRICT` rejects immediately, while `NO ACTION` defers the check to the end of the statement (and in Postgres, to the end of the transaction if the constraint is `DEFERRABLE`). That deferral matters for cyclic updates — swapping two rows' keys. Say "practically the same; `NO ACTION` can be deferred" and you are ahead of the usual answer.

**Interview warning about `CASCADE`:** it is the convenient choice and the dangerous one. One `DELETE FROM customer WHERE id=7` can silently remove orders, order items, payments and reviews. The safe default is `RESTRICT` plus a deliberate application-level cleanup; reach for `CASCADE` only where the child genuinely has no independent existence — which, not coincidentally, is exactly the **weak entity** of M2.

---

## 1.7 The integrity constraints

| Constraint | Rule | Enforced by |
|---|---|---|
| **Domain integrity** | Every value lies in its attribute's domain | Data type, `CHECK`, `NOT NULL`, `DEFAULT` |
| **Entity integrity** | No primary key value is NULL, and none repeats | `PRIMARY KEY` |
| **Referential integrity** | Every foreign key value exists in the parent, or is NULL | `FOREIGN KEY` |
| **Key integrity** | Declared candidate keys stay unique | `UNIQUE` |

Plus the one that is not in the classic list but is the most useful in practice:

| | |
|---|---|
| **`CHECK`** | An arbitrary row-level predicate: `CHECK (salary > 0)`, `CHECK (end_date >= start_date)` |

A table showing all of them together:

```sql
CREATE TABLE enrollment(
  roll     INT  NOT NULL,                        -- domain
  course   TEXT NOT NULL,
  grade    TEXT CHECK (grade IN ('A','B','C','F')),  -- domain (CHECK)
  marks    INT  CHECK (marks BETWEEN 0 AND 100),     -- domain (CHECK)
  PRIMARY KEY (roll, course),                    -- entity (composite PK)
  FOREIGN KEY (roll)   REFERENCES student(roll)      ON DELETE CASCADE,   -- referential
  FOREIGN KEY (course) REFERENCES course(code)       ON DELETE RESTRICT
);
```

Read that table out loud and it states the business rules: a student takes a course at most once, grades come from a fixed set, marks are percentages, deleting a student removes their enrolments, and a course with enrolments cannot be deleted. **A constraint is documentation the database actually enforces** — which is why "put it in the application instead" is usually the wrong trade: applications are many and change often; the schema is one.

---

## 1.8 NULL and three-valued logic

`NULL` is **not** zero and **not** an empty string. It is a marker meaning *no value here*, and it can mean several real things — unknown (phone not recorded), inapplicable (an employee's manager, for the CEO), or not yet supplied.

Because a comparison with an unknown is itself unknown, SQL has **three** truth values: TRUE, FALSE, **UNKNOWN**. Verified:

| Expression | Result | Why |
|---|---|---|
| `NULL = NULL` | `NULL` (unknown) | Two unknowns are not provably equal |
| `NULL <> NULL` | `NULL` | Nor provably different |
| `NULL IS NULL` | `1` (true) | `IS NULL` is the *only* way to test for NULL |
| `1 + NULL` | `NULL` | Arithmetic propagates NULL |
| `'a' \|\| NULL` | `NULL` | So does concatenation |
| `NULL AND 0` | `0` (false) | **False dominates AND** — one false makes it false regardless |
| `NULL OR 1` | `1` (true) | **True dominates OR** |

The last two are the interesting ones. The truth tables:

```
   AND │ T    F    U            OR  │ T    F    U            NOT │
   ────┼───────────────         ────┼───────────────         ────┼─────
    T  │ T    F    U             T  │ T    T    T             T  │  F
    F  │ F    F    F             F  │ T    F    U             F  │  T
    U  │ U    F    U             U  │ T    U    U             U  │  U
```

**The rule that follows, and it governs every `WHERE` clause you will ever write:**

> **A `WHERE` clause keeps a row only when the predicate is TRUE. UNKNOWN is discarded, exactly like FALSE.**

That one sentence explains every NULL surprise in the next section.

---

## 1.9 The NULL traps (asked on purpose)

Table used for all of this — note the NULL bonus:

```sql
CREATE TABLE s(name TEXT, bonus INT);
INSERT INTO s VALUES ('A',100),('B',NULL),('C',300);
```

### Trap 1 — aggregates ignore NULL, except `COUNT(*)`

| Query | Result | Explanation |
|---|---|---|
| `COUNT(*)` | `3` | Counts **rows** |
| `COUNT(bonus)` | `2` | Counts **non-NULL values** |
| `SUM(bonus)` | `400` | NULL skipped, not treated as 0 |
| `AVG(bonus)` | `200.0` | **400 / 2, not 400 / 3** |
| `COUNT(DISTINCT bonus)` | `2` | NULL not counted as a distinct value |

**`AVG` is the one that bites.** It divides by the count of non-NULL values. If NULL means "no bonus paid", the business answer is 400/3 ≈ 133.3, and you must write `AVG(COALESCE(bonus,0))` to get it. Deciding which average the question wants is a genuine modelling choice — and a good thing to raise out loud in an interview.

### Trap 2 — `<>` silently drops NULL rows

```sql
SELECT name FROM s WHERE bonus <> 100;    -- [('C',)]
```

Row `B` is missing. Not because its bonus equals 100 — because `NULL <> 100` is UNKNOWN, and `WHERE` keeps only TRUE. **"Everyone except those on 100" needs** `WHERE bonus <> 100 OR bonus IS NULL`.

### Trap 3 — `NOT IN` with a NULL returns *nothing at all*

The classic. Two tables, where `dept.did` contains a NULL:

```sql
dept.did values: [10, 20, NULL]
emp rows:        (1,10) (2,20) (3,30) (4,40)
```

Employees in no valid department are obviously 3 and 4. Four ways to ask, and **one of them is silently wrong**:

| Query | Result |
|---|---|
| `WHERE did NOT IN (SELECT did FROM dept)` | **`[]` — empty!** |
| `WHERE did NOT IN (SELECT did FROM dept WHERE did IS NOT NULL)` | `[3, 4]` ✓ |
| `WHERE NOT EXISTS (SELECT 1 FROM dept d WHERE d.did = e.did)` | `[3, 4]` ✓ |
| `LEFT JOIN dept d ON e.did = d.did WHERE d.did IS NULL` | `[3, 4]` ✓ |

**Why.** `NOT IN (10, 20, NULL)` expands to `did <> 10 AND did <> 20 AND did <> NULL`. That last term is UNKNOWN, and `TRUE AND TRUE AND UNKNOWN` = UNKNOWN. Verified directly:

```sql
SELECT 30 NOT IN (10,20,NULL);   -- NULL  (unknown)
SELECT 30 NOT IN (10,20);        -- 1     (true)
```

So no row can ever satisfy it, whatever the data. **The query returns an empty set and no error** — which is why this bug reaches production.

**The lesson to state:** `NOT EXISTS` is NULL-safe and `NOT IN` is not. Prefer `NOT EXISTS` for anti-joins unless you know the column is `NOT NULL`. This comes back in M5 with the performance angle.

### Trap 4 — `GROUP BY` and `ORDER BY` *do* group NULLs together

Consistency breaks here, and it is worth knowing: `GROUP BY` treats all NULLs as **one group**, and `DISTINCT` keeps **one** NULL — even though `NULL = NULL` is unknown. Those operators use "not distinct from" semantics rather than `=`. In sorting, SQLite and MySQL put NULLs **first** ascending; Oracle puts them **last**; Postgres defaults to last and supports `NULLS FIRST`/`NULLS LAST` explicitly.

### Handling NULL deliberately

| Function | Does |
|---|---|
| `COALESCE(a, b, c)` | First non-NULL argument. **Standard SQL, works everywhere** |
| `IFNULL(a, b)` | Two-argument version (MySQL, SQLite) |
| `NVL(a, b)` | Oracle's version |
| `ISNULL(a, b)` | SQL Server's version |
| `NULLIF(a, b)` | NULL if `a = b`, else `a` — the inverse, useful to avoid divide-by-zero: `x / NULLIF(y,0)` |

Prefer `COALESCE`: it is standard and takes any number of arguments.

---

## 1.10 Consolidation

### Must remember (module)

1. **Degree = columns, cardinality = rows.** Degree changes only when you alter the table.
2. A candidate key is a **minimal** super key. Minimality is the entire difference.
3. Primary key choice is a **design decision**; the unchosen candidates are alternate keys.
4. A set is a super key iff it **contains a whole candidate key** — that is the counting method, and it beats memorising formulas.
5. `PRIMARY KEY` = `UNIQUE` + `NOT NULL`, one per table. `UNIQUE` allows NULLs — **multiple** of them in MySQL/Postgres/Oracle/SQLite, but **only one** in SQL Server.
6. Two NULLs don't violate `UNIQUE` because `NULL = NULL` is unknown, not true.
7. A foreign key **may be NULL and may repeat**; only the parent side must be unique. It may reference its own table.
8. `ON DELETE` defaults to `NO ACTION` (rejects). `CASCADE` is convenient and dangerous — restrict it to children with no independent existence.
9. **`WHERE` keeps a row only when the predicate is TRUE.** UNKNOWN is thrown away just like FALSE. This single rule explains every NULL trap.
10. **`NOT IN` with a NULL in the subquery returns an empty set, silently.** Use `NOT EXISTS`.
11. `COUNT(*)` counts rows; `COUNT(col)` counts non-NULLs; `AVG` divides by the non-NULL count.
12. `GROUP BY` and `DISTINCT` *do* treat NULLs as equal to each other, unlike `=`. The inconsistency is real; learn it rather than reasoning from it.
13. **SQLite-only quirks** (never assert these as general truths): foreign keys are off by default, and a non-`WITHOUT ROWID` table permits NULL in a `PRIMARY KEY` column.
14. Real SQL tables are bags, not sets — duplicates are possible without a key, though the relational model forbids them.

### Common wrong answers

| Candidate says | Why it loses marks | Say instead |
|---|---|---|
| "Super key and candidate key are the same" | Misses minimality | "A candidate key is a minimal super key" |
| "A table can have many primary keys" | Confuses PK with candidate key | "One primary key — possibly composite — and many candidate keys" |
| "A composite key means two primary keys" | A composite key is **one** key of several attributes | — |
| "A unique key can't be NULL" | It can, and usually more than once | Give the SQL Server exception as the contrast |
| "A foreign key must be unique" | Only the referenced side is | "FKs repeat — that's how 1:N works" |
| "A foreign key can't be NULL" | It can, meaning 'no parent yet' | — |
| "NULL means zero / empty string" | It is the absence of a value | "`0` is a value; NULL is the absence of one — `0 = 0` is true, `NULL = NULL` is unknown" |
| "`WHERE bonus <> 100` returns everyone not on 100" | Drops the NULL rows | Add `OR bonus IS NULL` |
| "`NOT IN` and `NOT EXISTS` are interchangeable" | Differ on NULLs, and the failure is silent | "`NOT EXISTS` is NULL-safe" |
| "`AVG` ignoring NULLs is a bug" | It is specified behaviour | "`AVG` divides by the non-NULL count — use `COALESCE` if NULL should mean 0" |
| "`CASCADE` is the safe default" | It deletes data you didn't name | "`RESTRICT` by default; `CASCADE` only for dependent children" |

### Interview Q&A bank

**Q1. Super key vs candidate key vs primary key vs alternate key?**
A super key is any attribute set that's unique. A candidate key is a minimal super key — drop any attribute and uniqueness fails. The primary key is the candidate key chosen as the identifier; the others are alternate keys.
*Follow-up:* "`{roll, name}` — which is it?" → A super key but not candidate, since `roll` alone suffices, so `name` is redundant.

**Q2. `R(A,B,C,D)` with candidate keys `{A}` and `{B}`. How many super keys?**
Sets containing `A`: 2³ = 8. Containing `B`: 8. Containing both: 2² = 4. Total 8 + 8 − 4 = **12**.

**Q3. Primary key vs unique key?**
Both reject duplicates. PK rejects NULLs and there's one per table (usually the clustered index); `UNIQUE` permits NULLs and you can have many.
*Follow-up:* "Why does `UNIQUE` allow two NULLs?" → Uniqueness is tested with `=`, and `NULL = NULL` is unknown, so neither row provably duplicates the other.

**Q4. Can a primary key be NULL?**
No — entity integrity requires every row be identifiable. PK is `NOT NULL` + `UNIQUE`.

**Q5. What is referential integrity?**
Every foreign key value must exist in the referenced table's key, or be NULL. It stops dangling references — an order pointing at a customer who was deleted.
*Follow-up:* "How is it enforced on delete?" → The referential action: `CASCADE`, `SET NULL`, `RESTRICT`/`NO ACTION`.

**Q6. Can a foreign key be NULL or duplicated?**
Both. NULL means no parent assigned; duplication is what makes a 1:N relationship work.

**Q7. Difference between `ON DELETE CASCADE` and `ON DELETE SET NULL`?**
`CASCADE` deletes the child rows with the parent; `SET NULL` keeps them and nulls the link. Use `CASCADE` when the child can't exist alone (order items), `SET NULL` when it can (employee without a department).

**Q8. Surrogate or natural primary key — which, and why?**
Surrogate PK plus a `UNIQUE` constraint on the natural key. Surrogates are stable and narrow in foreign keys; natural keys change in the real world, and changing one would cascade through every child table.

**Q9. Four integrity constraints?**
Domain (values in their type/`CHECK`), entity (PK not null, unique), referential (FKs resolve), key (declared candidates stay unique).

**Q10. What does `NULL` mean, and how do you test for it?**
Absence of a value — unknown, inapplicable or not yet supplied. Test with `IS NULL`; `= NULL` is always unknown.

**Q11. Why does `SELECT ... WHERE col NOT IN (subquery)` sometimes return nothing?**
If the subquery yields a NULL, `NOT IN` expands to a chain of `<>` including `col <> NULL`, which is UNKNOWN, so the whole predicate is UNKNOWN and no row qualifies. Use `NOT EXISTS`, or filter the NULL out.
*Follow-up:* "And does it error?" → No, silently empty. That's why it reaches production.

**Q12. `COUNT(*)` vs `COUNT(col)`?**
Rows vs non-NULL values in that column.

**Q13. Degree and cardinality?**
Degree = number of attributes (columns); cardinality = number of tuples (rows).

**Q14. Can a table have no primary key?**
In SQL yes, and then duplicate rows are possible. The relational model says every relation has a key, since a relation is a set. In practice: always declare one.

### Practice

1. `R(A,B,C,D,E)`, candidate keys `{A,B}` and `{C}`. Count the super keys. *(Check: contains AB → 2³; contains C → 2⁴; contains both → 2²; total 8 + 16 − 4 = 20.)*
2. For `student(roll, email, aadhaar, name, dept)` where roll, email and aadhaar are each unique: list all candidate keys, pick a primary key with a one-line justification, name the alternate keys, and say how many super keys exist.
3. Write the DDL for `loan(member_id, isbn, issue_date, due_date)` so that: a member may borrow the same book again later but not twice on one day, `due_date` cannot precede `issue_date`, deleting a member deletes their loans, and a book with outstanding loans cannot be deleted.
4. Predict each result, then run it against `s(name, bonus)` = `('A',100),('B',NULL),('C',300)`:
   `SELECT SUM(bonus) FROM s;` · `SELECT AVG(bonus) FROM s;` · `SELECT COUNT(bonus) FROM s;` · `SELECT name FROM s WHERE bonus > 50;` · `SELECT name FROM s WHERE bonus NOT IN (100);`
5. Rewrite "employees whose department doesn't exist in `dept`" three ways (`NOT IN` made safe, `NOT EXISTS`, `LEFT JOIN`), then insert a NULL into `dept.did` and re-run all three. Which breaks?
6. `employee(eid PK, name, manager_id → employee.eid)`. Can `manager_id` be NULL? Should it be? What does `ON DELETE SET NULL` mean here in business terms?
7. A table has 4 candidate keys. How many alternate keys does it have? How many primary keys?
8. `AVG(bonus)` returned 200 but the finance team expected 133.33. Explain the difference in one sentence, and fix the query.

---

## Exit checklist

```
[ ] I can define all seven key types and give the test for each
[ ] I can count super keys for any set of candidate keys, using contains-a-whole-CK + inclusion-exclusion
[ ] I can state the PK vs UNIQUE table from memory, including the SQL Server NULL exception
[ ] I can explain WHY UNIQUE permits two NULLs, from three-valued logic
[ ] I can argue surrogate vs natural key with the stability and FK-width reasons
[ ] I can name all referential actions and what each does to the child rows
[ ] I know ON DELETE defaults to NO ACTION, and why CASCADE is risky
[ ] I can write the AND/OR/NOT three-valued truth tables
[ ] I can state the rule "WHERE keeps only TRUE" and derive every NULL trap from it
[ ] I can explain the NOT IN / NULL trap and give two NULL-safe rewrites
[ ] I know COUNT(*) vs COUNT(col) vs AVG behaviour with NULLs
[ ] I can write DDL using all four integrity constraints plus CHECK
```

---

## Next

**Part 4: M2 — ER Model and Schema Design.** How to get from a one-line prompt ("model a library") to tables: entity sets and attribute types, cardinality ratios and participation, weak entities, generalization and aggregation — then **the ER-to-relational conversion rules as a mechanical drill** (1:1, 1:N, M:N, multivalued, weak, ISA), and two full worked schemas built and queried end to end.
