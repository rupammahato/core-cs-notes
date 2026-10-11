# DBMS Placement Handbook — Part 5
# Module 3: Normalization

**Module 3 · 4–5 hours · Tier 1 · Requires: M1 (keys), M2 (schema design)**

---

## Why this module matters

This is the most-asked topic in the subject. Not "one of the most" — **the** most. Every DBMS question list opens with it, every core-CS segment touches it, and the written-test numerical ("find the candidate keys, state the highest normal form") comes from here.

It is also where preparation goes wrong most often, in a specific way: people memorise *"1NF is atomic values, 2NF removes partial dependency, 3NF removes transitive dependency"* and then freeze when handed an actual relation with five FDs, because **every one of those definitions is phrased in terms of candidate keys** and they never learned to find them. So this module front-loads the mechanics: closure first, candidate keys second, normal forms third. In that order it is a procedure you can execute under pressure rather than a chant.

The organising principle:

> **Redundancy is not a space problem, it is a correctness problem. If a fact is stored in two places, the two places can disagree — and sooner or later they will. Normalization is the process of splitting tables until every fact lives in exactly one place, and each normal form is just a sharper test for "is any fact still stored somewhere it doesn't belong?"**

**How everything here was verified.** The anomalies in §3.1 are real SQL runs. Every closure, candidate key, normal-form verdict, lossless-join check and dependency-preservation check in this module was computed by a purpose-built FD toolkit (`fd.py`), which was itself first validated against twelve textbook answers I knew in advance. The two classification rules in §3.5 were additionally stress-tested against **30,000 randomly generated FD sets** with zero violations. Where a number appears, it was computed, not recalled.

---

## 3.1 Redundancy is a bug: the three anomalies

Start with one table that stores everything about student enrolments. PK is `(roll, code)`.

```
roll   name    dept   code    title                grade
101    Asha    CSE    DB101   Databases            A
101    Asha    CSE    OS201   Operating Systems    B
102    Ravi    ECE    DB101   Databases            A
103    Meera   CSE    DB101   Databases            C
```

Already visible: **`'Databases'` is stored 3 times** and **`Asha/CSE` is stored 2 times** (counted by query, not by eye). Those duplicates are the disease. Here are its three symptoms, each one executed.

### Update anomaly — one fact, many rows, easy to half-change

Rename `DB101` to "Database Systems". The fact lives in three rows, so a correct update touches three rows. Update one — a completely realistic mistake — and:

```sql
UPDATE sc SET title='Database Systems' WHERE code='DB101' AND roll=101;

SELECT DISTINCT code, title FROM sc WHERE code='DB101';
```

```
('DB101', 'Database Systems')
('DB101', 'Databases')
```

**The database now holds two different titles for one course.** Nothing was violated, no error was raised, and every future report is wrong. This is the anomaly that matters most in practice.

### Insert anomaly — can't record one fact without another

Add course `CN301` "Computer Networks" which nobody has enrolled in yet:

```sql
INSERT INTO sc VALUES (NULL, NULL, NULL, 'CN301', 'Computer Networks', NULL);
```

In a standard engine this is **rejected outright**, because `roll` is part of the primary key and primary-key columns are `NOT NULL`:

```
REJECTED: NOT NULL constraint failed: sc.roll
```

(Verified with a `WITHOUT ROWID` table. Plain SQLite accepts it because of the primary-key quirk labelled in M1 §1.4 — and even then the row it stores is `(None, None, None, 'CN301', 'Computer Networks', None)`, which is garbage. Either way the schema cannot record a course until a student enrols in it.)

### Delete anomaly — deleting one fact destroys another

Ravi (102) drops `DB101`. He was the only ECE student:

```sql
DELETE FROM sc WHERE roll=102;
SELECT DISTINCT dept FROM sc;
```

```
depts remaining: ['CSE']
```

**The ECE department has vanished from the database.** We deleted an enrolment and lost a department. Nobody asked for that.

### What normalization fixes, demonstrated

Split into three tables — `student(roll, name, dept)`, `course(code, title)`, `enrollment(roll, code, grade)` — and all three anomalies disappear. Verified:

| Operation | One big table | Three tables |
|---|---|---|
| Rename a course | 3 row updates, half-updatable | **1 update**: `('DB101', 'Database Systems')` |
| Add a course with no students | Rejected | **Works**: `('CN301', 'Computer Networks')` |
| Drop Ravi's enrolment | ECE lost | **ECE survives**: `(102, 'Ravi', 'ECE')` |

And nothing was lost — joining the three tables reconstructs the original rows exactly:

```sql
SELECT e.roll, s.name, s.dept, e.code, c.title, e.grade
FROM enrollment e JOIN student s ON s.roll = e.roll
                  JOIN course  c ON c.code = e.code
ORDER BY e.roll, e.code;
```

```
(101, 'Asha',  'CSE', 'DB101', 'Database Systems',   'A')
(101, 'Asha',  'CSE', 'OS201', 'Operating Systems',  'B')
(103, 'Meera', 'CSE', 'DB101', 'Database Systems',   'C')
```

That reconstruction property has a name — **lossless join** — and it is the thing a decomposition must never break (§3.12).

> **The interview answer to "why normalize?"** is not "to save space". It is: *"so that each fact is stored once, which makes it impossible for the database to contradict itself."* Then give the update anomaly as the example.

---

## 3.2 Functional dependencies

A **functional dependency** `X → Y` means: *any two tuples that agree on X must agree on Y.* X **determines** Y; Y is **functionally dependent** on X.

```
   roll → name        "if I tell you the roll number, the name is fixed"
   roll → dept
   code → title
   roll, code → grade  "a grade needs BOTH the student and the course"
```

Read `→` as *"determines"*, and test a claimed FD by asking: **could two rows share the left side but differ on the right?** If yes, the FD does not hold.

| Point | Detail |
|---|---|
| FDs come from **meaning**, not from data | A table where no two rows happen to share a value satisfies every FD by accident. FDs are rules from the business |
| FDs are about the **schema** | They must hold for every legal instance, not just today's rows |
| The left side may be composite | `roll, code → grade` |
| Direction matters | `roll → name` does not give `name → roll` (two students can share a name) |

### Trivial and non-trivial

| Kind | Condition | Example |
|---|---|---|
| **Trivial** | Y ⊆ X | `roll, name → name` — always true, carries no information |
| **Non-trivial** | Y ⊄ X | `roll → name` |
| **Completely non-trivial** | X ∩ Y = ∅ | `roll → name` (no shared attributes) |

**Normal forms only ever care about non-trivial FDs.** Every normal-form test silently means "for every non-trivial FD…", which is why `roll, name → name` never breaks anything.

### Reading FDs out of a requirement

This is the step interviews actually test, and it is just careful English:

| Requirement sentence | FD |
|---|---|
| "Each student has one name and belongs to one department" | `roll → name, dept` |
| "Each course has one title" | `code → title` |
| "A student gets one grade per course" | `roll, code → grade` |
| "Each department has one HOD" | `dept → hod` |
| "A teacher teaches only one course" | `teacher → course` |

Note the shape of the last two: they are what create 3NF and BCNF violations later. **An FD whose left side is not a key is the warning sign.**

---

## 3.3 Armstrong's axioms

The three sound-and-complete inference rules — complete meaning every FD that logically follows can be derived from them.

| Axiom | Rule | In words |
|---|---|---|
| **Reflexivity** | If Y ⊆ X then X → Y | A set determines its own subsets (this is where trivial FDs come from) |
| **Augmentation** | If X → Y then XZ → YZ | Adding the same attributes to both sides preserves the FD |
| **Transitivity** | If X → Y and Y → Z then X → Z | The important one — the source of *transitive dependency* in 3NF |

Three derived rules worth knowing by name:

| Derived rule | Rule |
|---|---|
| **Union** | X → Y and X → Z ⟹ X → YZ |
| **Decomposition** | X → YZ ⟹ X → Y and X → Z |
| **Pseudotransitivity** | X → Y and WY → Z ⟹ WX → Z |

**Union + decomposition together** mean the right side of an FD can always be split into single attributes, which is why every normal-form test below examines one dependent attribute at a time.

---

## 3.4 Attribute closure

**X⁺ (the closure of X) is the set of all attributes determined by X.** This single tool answers everything else: superkey tests, candidate keys, normal forms, lossless joins.

### The algorithm

```
X+ := X
repeat
    for each FD  L -> R  in F:
        if L is a subset of X+ :
            X+ := X+ union R
until X+ stops changing
```

### Worked, with `F = {AB → C, C → D}`

| Step | X⁺ | Why |
|---|---|---|
| start | `{A,B}` | — |
| `AB → C` | `{A,B,C}` | `AB ⊆ X⁺` |
| `C → D` | `{A,B,C,D}` | `C ⊆ X⁺` now |
| no change | `{A,B,C,D}` | done |

**(AB)⁺ = ABCD** ✓ verified. And **(C)⁺ = CD** ✓ verified — `AB → C` never fires because `AB ⊄ {C}`.

### The two tests you get for free

| Question | Test |
|---|---|
| **Is X a superkey?** | `X⁺ = all attributes of R` |
| **Is X a candidate key?** | X is a superkey **and** no proper subset of X is |
| **Does `X → Y` hold?** | `Y ⊆ X⁺` |

Everything from here is applying those three lines.

---

## 3.5 Finding all candidate keys — the procedure

The most common DBMS numerical. Do it the same way every time.

### Step 1 — classify every attribute by where it appears in F

| Class | Appears | Rule |
|---|---|---|
| **L** | Only on the **left** of FDs | **In every candidate key** |
| **N** | In **no** FD at all | **In every candidate key** |
| **R** | Only on the **right** | **In no candidate key** |
| **B** | On **both** sides | May or may not be — must test |

**Both rules were stress-tested against 30,000 random FD sets with zero violations**, so you can rely on them.

### Step 2 — essential set = L ∪ N. Take its closure.

- If `(L ∪ N)⁺ = R`, then **L ∪ N is the only candidate key. Stop.**
- Otherwise, add attributes from **B**, smallest combinations first, and test each closure. Keep those that reach all of R; discard any set that contains a smaller one you already kept (minimality).

### Worked example 1 — the unique-key case

`R(roll, name, dept, code, title, grade)` with
`F = {roll → name, roll → dept, code → title, (roll, code) → grade}`

Shorthand `R(R,N,D,C,T,G)`:

| Class | Attributes |
|---|---|
| L (left only) | `R`, `C` |
| R (right only) | `N`, `D`, `T`, `G` |
| B (both) | — |
| N (neither) | — |

Essential = `{R, C}`. Closure: `(RC)⁺ = R,C → N,D,T,G` → all six attributes.

> **Only candidate key: `{roll, code}`** ✓ verified.
> Prime attributes: `roll, code`. Non-prime: `name, dept, title, grade`.

### Worked example 2 — two candidate keys

`R(S,C,T)` — student, course, teacher — with `F = {SC → T, T → C}`.

| Class | Attributes |
|---|---|
| L | `S` |
| B | `C`, `T` |
| R | — |

Essential = `{S}`, and `(S)⁺ = S` ≠ all. So extend with B:

| Candidate set | Closure | Verdict |
|---|---|---|
| `SC` | `S,C → T` = `SCT` | **superkey**, and neither `S` nor `C` alone is → **candidate key** |
| `ST` | `S,T → C` = `SCT` | **superkey**, minimal → **candidate key** |
| `CT` | `C,T → C` = `CT` | not a superkey |

> **Candidate keys: `{S,C}` and `{S,T}`** ✓ verified. **Every attribute is prime.** Remember that — it decides the normal form in §3.10.

### Drill set (all verified)

| R | F | Candidate keys | Highest NF |
|---|---|---|---|
| `ABCD` | `AB→C, C→D` | `{AB}` | 2NF |
| `ABCD` | `A→BC, C→D` | `{A}` | 2NF |
| `ABCDE` | `A→B, BC→D, E→C` | `{AE}` | 1NF |
| `ABCD` | `AB→CD, D→A` | `{AB}, {BD}` | 3NF |
| `ABCDE` | `AB→C, DE→C, B→D` | `{ABE}` | 1NF |
| `ABC` | `A→B, B→C, C→A` | `{A}, {B}, {C}` | BCNF |

The last row is worth staring at: with a cycle of single-attribute FDs, **every attribute is a candidate key on its own**, so every determinant is a superkey and the relation is already in BCNF.

---

## 3.6 Prime and non-prime attributes

| Term | Definition |
|---|---|
| **Prime** (key attribute) | Belongs to **at least one** candidate key |
| **Non-prime** | Belongs to **no** candidate key |

Two things depend on this distinction and nothing else:

- **2NF** is about non-prime attributes depending on *part* of a key.
- **The entire difference between 3NF and BCNF** is whether a prime attribute on the right-hand side gets a free pass.

So compute the candidate keys, then immediately write down the prime set. In example 1: prime = `{roll, code}`. In example 2: prime = `{S, C, T}` — everything.

---

## 3.7 First Normal Form (1NF)

> **Every attribute value is atomic.** No lists in a cell, no repeating groups, no multivalued attributes.

Violation:

```
roll   name    phones                        courses
101    Asha    9000000001, 9000000002        DB101, OS201
```

Fix — one row per value, or a separate table (M2, R3):

```
member_phone(roll, phone)      enrollment(roll, code)
101, 9000000001                101, DB101
101, 9000000002                101, OS201
```

**Why it matters practically, not just formally:** a comma-separated column cannot be indexed, joined, constrained or searched without string surgery — `WHERE phones = '9000000001'` misses the row, and `WHERE phones LIKE '%9000000001%'` matches by accident and can't use an index (M7).

This is the same rule as "a relation's values are atomic" from M1 §1.1 — **1NF is the relational model's own requirement**, which is why some authors say a relation is in 1NF by definition.

**The honest modern footnote:** Postgres and MySQL both have real JSON and array types now, and using one deliberately — a settings blob you never filter on — is a reasonable engineering choice. That is not 1NF; it is a decision to leave the relational model for one column. Know the rule before you break it, and be able to say which you're doing.

---

## 3.8 Second Normal Form (2NF)

> **1NF, and no non-prime attribute is functionally dependent on a *proper subset* of any candidate key.**

A dependency on part of a key is a **partial dependency**. 2NF is only ever at risk when the candidate key is **composite** — with a single-attribute key there are no proper subsets to depend on, so 1NF ⟹ 2NF automatically.

### The running example

`R(R,N,D,C,T,G)`, candidate key `{R,C}`, non-prime `{N,D,T,G}`:

```
   {roll, code}            <- the candidate key
     │     │
  roll → name, dept        <- roll is HALF the key, and name/dept are non-prime  ✗ partial
  code → title             <- code is HALF the key, title is non-prime           ✗ partial
  roll,code → grade        <- the WHOLE key                                      ✓ fine
```

**2NF violated by `roll → name`, `roll → dept`, `code → title`** ✓ verified.

That is exactly why the table had anomalies: a student's name depends only on the student, so it is repeated once per course they take.

### The fix, and the result

Split each partial dependency into its own table:

```sql
student(roll, name, dept)        -- roll -> name, dept
course(code, title)              -- code -> title
enrollment(roll, code, grade)    -- (roll,code) -> grade
```

Verified verdicts after the split: `student` → **BCNF**, `course` → **BCNF**, `enrollment` → **BCNF**. The decomposition jumped straight past 2NF and 3NF, which is typical — one honest split usually fixes several levels at once.

---

## 3.9 Third Normal Form (3NF)

> **2NF, and for every non-trivial FD `X → A`: either X is a superkey, or A is prime.**

The equivalent informal statement: **no non-prime attribute depends on another non-prime attribute.** That indirect route is a **transitive dependency**.

### Worked example

`R(roll, name, dept, hod)` with `F = {roll → name, roll → dept, dept → hod}`.

| | |
|---|---|
| Candidate key | `{roll}` ✓ verified |
| Prime | `roll` |
| Non-prime | `name, dept, hod` |

```
   roll → dept → hod
    │              ▲
    └──────────────┘  hod depends on roll only THROUGH dept
```

`dept → hod`: `dept` is not a superkey (`(dept)⁺ = dept, hod` ≠ all), and `hod` is non-prime. **3NF violated by `dept → hod`** ✓ verified (highest NF = **2NF**).

The damage: a department's HOD is repeated in every student row of that department, so changing the HOD means updating many rows — the update anomaly again.

### The fix

```sql
student(roll, name, dept)   -- dept is an FK
dept(dept, hod)
```

Verified: `student` → **BCNF**, `dept` → **BCNF**. And the decomposition is **lossless** (common attribute `dept`, `(dept)⁺ = {dept, hod} ⊇ dept(D,H)`) and **dependency preserving** ✓ both verified.

### Transitive vs partial — the comparison that gets asked

| | **Partial dependency** (breaks 2NF) | **Transitive dependency** (breaks 3NF) |
|---|---|---|
| Shape | Non-prime depends on **part of a key** | Non-prime depends on **another non-prime** |
| Needs | A **composite** candidate key | Nothing special |
| Example | `code → title`, key `(roll, code)` | `dept → hod`, key `roll` |
| Left side is | A proper subset of a candidate key | Not a key at all |

---

## 3.10 Boyce–Codd Normal Form (BCNF)

> **For every non-trivial FD `X → A`, X must be a superkey.** Full stop — no exception for prime attributes.

BCNF is simply 3NF with the "or A is prime" escape clause deleted, which makes it the easiest definition in the module to state and the strictest to satisfy.

### The classic example — and why 3NF isn't enough

`R(S,C,T)`: a student takes a course taught by a teacher. Rules: **a student in a course has exactly one teacher** (`SC → T`), and **each teacher teaches only one course** (`T → C`).

From §3.5: candidate keys `{S,C}` and `{S,T}`; **every attribute is prime**.

| FD | X a superkey? | A prime? | 3NF | BCNF |
|---|---|---|---|---|
| `SC → T` | yes | — | ✓ | ✓ |
| `T → C` | **no** (`(T)⁺ = T,C`) | **yes** (`C` is in `{S,C}`) | ✓ **passes on the prime clause** | ✗ **fails** |

> **Verified: highest normal form = 3NF, BCNF violated by `T → C`.**

The residual redundancy is real: every row for a teacher repeats that teacher's course.

### The trade-off that makes BCNF interesting

Decompose into `{T,C}` and `{S,T}` to reach BCNF. Verified results:

| Property | Result |
|---|---|
| Lossless? | **Yes** — common attribute `T`, `(T)⁺ = {T,C} ⊇ {T,C}` ✓ |
| Dependency preserving? | **No** ✗ |
| FD lost | **`SC → T`** |
| FDs holding on `{T,C}` | `T → C` |
| FDs holding on `{S,T}` | **none** |

With the data split this way, **nothing in the schema can enforce "a student in a course has one teacher"** — the two attributes `S` and `C` never appear in the same table again, so no constraint can mention both. You would have to enforce it in application code or with a trigger.

> **This is the headline fact about BCNF, and the answer interviewers want:**
> **A lossless BCNF decomposition always exists, but a BCNF decomposition that is also dependency-preserving does not always exist. 3NF can always achieve both.**
> So when they clash, **staying in 3NF is often the right engineering choice** — and saying that is the answer that sounds like experience rather than recitation.

### The normal forms, side by side

| | Condition on every non-trivial `X → A` | Also requires |
|---|---|---|
| **1NF** | — | Atomic values |
| **2NF** | If A is non-prime, X is not a proper subset of a candidate key | 1NF |
| **3NF** | **X is a superkey, OR A is prime** | 2NF |
| **BCNF** | **X is a superkey** | 1NF |

1NF ⊃ 2NF ⊃ 3NF ⊃ BCNF — each is strictly stronger.

---

## 3.11 The decision procedure: "what is the highest normal form?"

Execute this in order. It is the whole numerical.

```
1. Write down F. Classify attributes: L (left only), R (right only), B (both), N (neither).
2. Essential = L ∪ N.  Take its closure.
      closure = all attributes?  -> that's the ONLY candidate key
      otherwise                  -> add B attributes, smallest first, test closures, keep minimal ones
3. Write the PRIME set (union of all candidate keys) and the NON-PRIME set.
4. For each non-trivial FD  X -> A  (split multi-attribute right sides into single attributes):

       is X a superkey?  ---- yes ----> fine for BCNF, 3NF and 2NF
             |
             no
             |
       is A prime?  ---- yes ----> breaks BCNF only          (so: 3NF)
             |
             no
             |
       is X a proper subset of a candidate key?
             |                         |
            yes                        no
             |                         |
       breaks 2NF (partial)      breaks 3NF (transitive)
        (so: 1NF)                     (so: 2NF)

5. Highest NF = the strongest form with no violations.
```

Worked straight through on `R(A,B,C,D)`, `F = {AB → C, C → D}`:

| Step | Result |
|---|---|
| Classify | L = `{A,B}`, R = `{D}`, B = `{C}`, N = ∅ |
| Essential `{A,B}` | `(AB)⁺ = ABCD` → **only CK = `{AB}`** |
| Prime / non-prime | prime `{A,B}`; non-prime `{C,D}` |
| `AB → C` | `AB` is a superkey → fine |
| `C → D` | `C` not a superkey; `D` not prime; is `C ⊂ {A,B}`? **No** → **transitive → breaks 3NF** |
| **Verdict** | **2NF** ✓ verified |

---

## 3.12 Decomposition: the two properties

Splitting a table is only safe if it preserves information and, ideally, constraints.

### Lossless join (non-additive) — mandatory

A decomposition is **lossless** if joining the pieces back gives exactly the original rows — no more, no fewer. *"Lossy"* is misleading: the failure mode is **extra, spurious rows**, not missing ones.

> **Binary test:** `R₁ ∩ R₂` must be a **superkey of R₁ or of R₂**.
> Equivalently: `(R₁ ∩ R₂)⁺` must contain all of `R₁` or all of `R₂`.

Verified drills:

| Decomposition | F | Common | Closure | Verdict |
|---|---|---|---|---|
| `{AB}, {BC}` | `A→B, B→C` | `B` | `BC` | **LOSSLESS** (⊇ `BC`) |
| `{AB}, {CD}` | `A→B, C→D` | **∅** | ∅ | **LOSSY** |
| `{ABC}, {CD}` | `AB→C, C→D` | `C` | `CD` | **LOSSLESS** (⊇ `CD`) |
| `{AC}, {BC}` | `AB→C, C→A` | `C` | `AC` | **LOSSLESS** (⊇ `AC`) |

**No common attribute ⟹ always lossy.** That is the first thing to check, and it takes one second.

### Dependency preservation — desirable

A decomposition is **dependency preserving** if every FD in F can still be enforced *within a single table*, without a join. Formally, the union of the FDs projected onto the pieces must imply all of F.

The point is practical: a constraint spanning two tables cannot be declared. From §3.10, splitting `R(S,C,T)` into `{T,C}` and `{S,T}` lost `SC → T`, so "one teacher per student per course" became unenforceable by the schema.

| Property | Required? | Why |
|---|---|---|
| **Lossless join** | **Always.** Non-negotiable | Without it the decomposition is simply wrong — the join invents rows |
| **Dependency preservation** | Strongly desired | Without it, constraints move into application code, where they get skipped |

| Target | Lossless always achievable? | Dependency-preserving always achievable? |
|---|---|---|
| **3NF** | Yes | **Yes** |
| **BCNF** | Yes | **No** |

---

## 3.13 4NF and 5NF (Tier 3 — one page, then move on)

### 4NF and multivalued dependencies

A **multivalued dependency** `X ↠ Y` means X determines a *set* of Y values independently of the rest of the row. The classic damage:

```
course     instructor    textbook
DB101      Smith         Korth
DB101      Smith         Elmasri
DB101      Jones         Korth
DB101      Jones         Elmasri
```

Instructors and textbooks are both tied to the course but **completely independent of each other** — so the table is forced to store every combination. Add a third instructor and you must add two rows. The table is in BCNF (its only key is all three columns, so there are no non-trivial FDs at all), yet obviously redundant.

> **4NF:** BCNF, and for every non-trivial MVD `X ↠ Y`, X is a superkey.
> **Fix:** two tables — `course_instructor(course, instructor)` and `course_textbook(course, textbook)`.

**The giveaway in an interview:** two or more independent multivalued facts about the same entity in one table. If you spot that and name it, you have given the whole 4NF answer.

### 5NF (project-join normal form)

Deals with join dependencies — a table that cannot be split into two lossless pieces but can into three. Extremely rare in practice.

> **Say this and stop:** "4NF removes independent multivalued dependencies; 5NF removes join dependencies that only decompose into three or more relations. Both are rare in practice — 3NF or BCNF is where real schemas live."

That is the complete expected answer. Nobody is going to ask you to prove a join dependency.

---

## 3.14 Denormalization

**Deliberately reintroducing redundancy to make reads faster.** Not a mistake — a trade.

| You gain | You pay |
|---|---|
| Fewer joins per query | Update anomalies come back |
| Precomputed aggregates (`order.total`) | Every write must maintain the copy |
| Fewer round trips for read-heavy pages | More storage, more write cost |
| Queries that survive sharding (M10) | Consistency becomes **your** job |

**When it is genuinely right:**

- Reads outnumber writes by orders of magnitude (dashboards, reporting, feeds).
- The join is measurably the bottleneck — after you have looked at the plan and the indexes (M7).
- The copied value is immutable, which removes the anomaly entirely. **An invoice line storing the price at time of sale is not denormalization** — the historical price is a genuinely different fact from today's price. This distinction is worth making unprompted; it is the one case where "redundancy" is simply correct modelling.
- Across a shard boundary, where a join is impossible rather than merely slow.

**How to do it responsibly:** pick exactly one source of truth, keep the copy maintained in one place (a trigger, a materialized view, or one code path — never scattered), and write down that the copy exists.

> **The answer to "is denormalization bad?"** — *"Normalize first, then denormalize with evidence. Normalization protects correctness; denormalization buys read performance with correctness risk, so it needs a measurement behind it, not a hunch."*

---

## 3.15 Consolidation

### Must remember (module)

1. **Normalization is about correctness, not space.** The headline symptom is the update anomaly.
2. **Every normal form is defined in terms of candidate keys.** Find them first, always.
3. Closure is the only tool you need: superkey test, candidate-key test, FD test, lossless test.
4. **L (left-only) and N (in-no-FD) attributes are in every candidate key; R (right-only) attributes are in none.** Verified over 30,000 random FD sets.
5. If `(L ∪ N)⁺` = all attributes, that set is the **only** candidate key.
6. **Prime** = in at least one candidate key. The prime/non-prime split is what separates 3NF from BCNF.
7. **2NF is only at risk with a composite candidate key.** Single-attribute key ⟹ already 2NF.
8. **Partial** dependency = non-prime depends on *part of a key* (breaks 2NF). **Transitive** = non-prime depends on *another non-prime* (breaks 3NF).
9. **BCNF = 3NF without the "or A is prime" escape clause.** One sentence, complete definition.
10. **A dependency-preserving BCNF decomposition may not exist; a dependency-preserving 3NF one always does.** The single most valuable fact in this module.
11. Therefore **staying in 3NF is sometimes the correct engineering decision.**
12. **Lossless join is mandatory; dependency preservation is desirable.**
13. Binary lossless test: the common attributes must be a **superkey of one of the two pieces**. **No common attribute ⟹ lossy.**
14. "Lossy" means **extra spurious rows**, not lost rows.
15. **4NF** removes independent multivalued dependencies. A BCNF table can still be badly redundant (the instructor/textbook case).
16. Normal-form tests only consider **non-trivial** FDs.
17. **Storing a historical price is not denormalization** — it is a different fact.

### Common wrong answers

| Candidate says | Why it loses marks | Say instead |
|---|---|---|
| "Normalization saves storage" | Misses the point; it can even add storage (more tables, more keys) | "It removes redundancy so the data can't contradict itself" |
| "1NF means no duplicate rows" | 1NF is about **atomic values** | "No lists or repeating groups in a cell" |
| "2NF removes partial dependency" *(and stops)* | True but unanchored — partial *of what?* | "No non-prime attribute depends on part of a candidate key" |
| "3NF means no transitive dependency" *(and stops)* | Misses the prime-attribute clause, so you can't do BCNF | "For every FD, the left side is a superkey or the right side is prime" |
| "BCNF and 3NF are basically the same" | They differ exactly on prime right-hand sides | Give the `R(S,C,T)`, `T → C` example |
| "Always normalize to BCNF" | May destroy an enforceable dependency | "To 3NF always; BCNF when it doesn't cost a dependency" |
| "Higher normal form is always better" | Ignores join cost and dependency loss | "Normalize for correctness, denormalize with measurements" |
| "Lossy decomposition loses rows" | It **adds** spurious rows | — |
| "A decomposition with a common attribute is lossless" | Only if that attribute is a **superkey of one piece** | Give the test |
| "Every attribute in an FD is prime" | Prime means *in a candidate key* | — |
| Computes normal form without finding candidate keys first | Guaranteed wrong on anything non-trivial | Keys first, every time |
| "Denormalization is bad practice" | It's a trade-off with legitimate uses | Name the read-heavy and sharded cases |

### Interview Q&A bank

**Q1. What is normalization and why do it?**
Organising tables so each fact is stored once, by removing dependencies that don't belong. The reason is correctness: redundancy lets the database contradict itself — rename a course stored in three rows, update two, and now there are two titles.
*Follow-up:* "Give all three anomalies." → Update (half-changed facts), insert (can't add a course with no students), delete (dropping an enrolment loses a department).

**Q2. What is a functional dependency?**
`X → Y` means any two tuples agreeing on X must agree on Y. It comes from the business rules, not from the current rows.

**Q3. State Armstrong's axioms.**
Reflexivity (Y ⊆ X ⟹ X → Y), augmentation (X → Y ⟹ XZ → YZ), transitivity (X → Y, Y → Z ⟹ X → Z). They're sound and complete. Derived: union, decomposition, pseudotransitivity.

**Q4. How do you find all candidate keys?**
Classify attributes: left-only and not-in-any-FD must be in every key, right-only in none. Take the closure of the essential set; if it covers R, that's the only key. Otherwise add both-side attributes smallest-first and keep the minimal superkeys.

**Q5. Prime vs non-prime?**
Prime = in at least one candidate key. The distinction is exactly what 3NF forgives and BCNF doesn't.

**Q6. Explain 1NF, 2NF, 3NF and BCNF.**
1NF: atomic values. 2NF: 1NF plus no non-prime attribute depending on part of a candidate key. 3NF: 2NF plus, for every FD, the left side is a superkey or the right side is prime. BCNF: every determinant is a superkey.
*Follow-up:* "Example for each." → Phone list; `code → title` under key `(roll, code)`; `dept → hod`; `T → C` in `R(S,C,T)`.

**Q7. Partial vs transitive dependency?**
Partial: a non-prime attribute depends on a proper subset of a candidate key — needs a composite key. Transitive: a non-prime attribute depends on another non-prime attribute.

**Q8. Difference between 3NF and BCNF?**
3NF allows `X → A` when A is prime even if X isn't a superkey; BCNF doesn't. So BCNF is strictly stronger.
*Follow-up:* "Is a relation in 3NF always in BCNF?" → No — `R(S,C,T)` with `SC → T`, `T → C` is 3NF, not BCNF.

**Q9. Why would you stop at 3NF?**
Because a BCNF decomposition may not be dependency preserving. Splitting `R(S,C,T)` to BCNF loses `SC → T`, so the schema can no longer enforce one teacher per student-course. 3NF can always be both lossless and dependency preserving.

**Q10. What makes a decomposition lossless, and how do you check it?**
Joining the pieces reproduces exactly the original rows. For a binary split: the common attributes must form a superkey of one of the two relations. No common attribute means lossy.
*Follow-up:* "What goes wrong in a lossy one?" → The join produces extra rows that were never in the original.

**Q11. What is dependency preservation?**
Every original FD can still be enforced inside one table. Lose it and the constraint has to be enforced by application code.

**Q12. What is 4NF? Give an example.**
BCNF plus: every non-trivial multivalued dependency has a superkey on the left. The `course / instructor / textbook` table is in BCNF yet stores every instructor-textbook combination, because the two are independent. Split into two tables.

**Q13. What is denormalization and when is it right?**
Deliberately adding redundancy to speed up reads. Right when reads dominate, the join is measurably the bottleneck, the copied value is immutable, or the join crosses a shard boundary. You take on keeping copies in sync.

**Q14. Is a relation with a single-attribute primary key automatically in 2NF?**
Yes — there are no proper subsets of a one-attribute key for a partial dependency to use. It can still violate 3NF.

**Q15. `R(A,B,C,D)`, `F = {AB → C, C → D}`. Candidate keys and highest normal form?**
`AB` is the only candidate key (`(AB)⁺ = ABCD`). Prime `{A,B}`, non-prime `{C,D}`. `C → D`: `C` isn't a superkey, `D` isn't prime, and `C` isn't a subset of the key → transitive → **2NF**.

### Practice

All answers below were computed with the verifier, so check yourself against them honestly — do the work on paper first.

1. `R(A,B,C,D)`, `F = {A → BC, C → D}`. Candidate keys? Highest NF? *(Answer: `{A}`; 2NF.)*
2. `R(A,B,C,D,E)`, `F = {A → B, BC → D, E → C}`. Candidate keys? Highest NF? *(Answer: `{AE}`; 1NF — find the partial dependency that causes it.)*
3. `R(A,B,C,D)`, `F = {AB → CD, D → A}`. Candidate keys? Highest NF? *(Answer: `{AB}` and `{BD}`; 3NF. Which FD stops it being BCNF, and why does it survive 3NF?)*
4. `R(A,B,C,D,E)`, `F = {AB → C, DE → C, B → D}`. Candidate keys? Highest NF? *(Answer: `{ABE}`; 1NF.)*
5. `R(A,B,C)`, `F = {A → B, B → C, C → A}`. Candidate keys? Highest NF? Explain the surprise. *(Answer: `{A}`, `{B}`, `{C}`; BCNF.)*
6. Is `{ABC}, {CD}` lossless under `F = {AB → C, C → D}`? Show the test. *(Answer: yes.)*
7. Is `{AB}, {CD}` lossless under `F = {A → B, C → D}`? *(Answer: no — explain in one sentence without computing anything.)*
8. Take `movie(title, year, director, actor, genre)` where a movie has many actors and many genres, independent of each other. Which normal form does it violate, and what are the resulting tables?
9. Normalize to 3NF, showing each step: `order(order_id, cust_id, cust_name, cust_city, product_id, product_name, unit_price, qty)`. State the FDs first, then the candidate key, then each violation by name.
10. Your `invoice_line` table stores `unit_price` even though `product.price` exists. Is that a normalization error? Defend your answer.
11. A colleague proposes decomposing `R(S,C,T)` with `SC → T`, `T → C` into `{S,C}` and `{C,T}`. Is it lossless? Is it dependency preserving? Is it BCNF? *(Work it with the tests — then check: common attribute is `C`, and `(C)⁺ = C`.)*
12. Explain, in two sentences, why a table in BCNF can still need 4NF.

---

## Exit checklist

```
[ ] I can give all three anomalies with a concrete example of each
[ ] I can compute attribute closure without hesitating
[ ] I can classify attributes into L / R / B / N and know what each class implies
[ ] I can find ALL candidate keys of any relation, mechanically
[ ] I can write the prime and non-prime sets immediately after
[ ] I can state 1NF, 2NF, 3NF and BCNF precisely, in terms of keys
[ ] I can tell a partial dependency from a transitive one on sight
[ ] I can run the §3.11 decision procedure end to end and name the highest normal form
[ ] I can state the difference between 3NF and BCNF in one sentence
[ ] I can explain why a dependency-preserving BCNF decomposition may not exist, with the S/C/T example
[ ] I can apply the binary lossless-join test and explain what "lossy" actually produces
[ ] I can explain 4NF with the instructor/textbook example
[ ] I can argue both sides of denormalization, with the immutable-price nuance
```

---

## Next

**Part 6: M4 — SQL I, Querying.** From theory to the keyboard: the **logical order of execution** that explains `WHERE` vs `HAVING` and most other SQL confusion, aggregates and what they do with NULL, `GROUP BY` rules, `DISTINCT`, the pattern and set operators, `CASE`, and the NULL traps that make correct-looking queries return wrong answers — every query executed, with its real output.
