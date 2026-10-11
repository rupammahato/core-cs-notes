# DBMS Placement Handbook — Part 4
# Module 2: ER Model and Schema Design

**Module 2 · 3 hours · Tier 1 · Requires: M1 (keys, foreign keys, constraints)**

---

## Why this module matters

"Design the schema for a library / cinema / Splitwise / Uber" is a standard interview prompt, and it is the one where preparation shows most clearly. Candidates who have only read definitions produce a pile of columns. Candidates who know the conversion rules produce tables with the right keys in the right places in about ten minutes, and can defend every one.

That is the real content of this module: **ER diagrams are not the deliverable — tables are.** The ER model is the thinking tool you use on the way, and the conversion rules (§2.6) are mechanical enough to execute under pressure.

This is also the module that makes M3 possible. Normalization fixes a schema that has redundancy; good ER modelling avoids creating most of it, and a schema built by these rules is usually already in 3NF.

The organising principle:

> **Entities become tables. Relationships become either a foreign key or a whole table, and which one it becomes is decided entirely by the cardinality ratio: 1:1 and 1:N fold into a foreign key, M:N needs a table of its own. Everything else in ER modelling — participation, weak entities, multivalued attributes, ISA — is a rule about where the key goes.**

**Both worked schemas in this module were created, populated and queried** (Python 3.12 `sqlite3`, SQLite 3.49.1, `PRAGMA foreign_keys = ON`). Every result shown is real output, including one design flaw I left in deliberately and then fixed, because it is exactly the flaw interviewers look for.

---

## 2.1 What the ER model is for

ER is a **design** model, not a storage model (M0, §0.7). You use it to talk to humans about requirements, then convert it to the relational model to actually store anything.

```
  requirements (English)
          │
          ▼
    ER diagram            <- you think here; the interviewer watches you think
          │
          ▼  conversion rules (§2.6)
   relational schema      <- what you actually build
          │
          ▼  normalization (M3)
   final tables
```

**Three building blocks and nothing else:** entities, attributes, relationships.

| Symbol | Means |
|---|---|
| Rectangle | Entity set |
| **Double** rectangle | **Weak** entity set |
| Ellipse | Attribute |
| **Double** ellipse | **Multivalued** attribute |
| **Dashed** ellipse | **Derived** attribute |
| <u>Underlined</u> attribute | Key attribute |
| Dashed-underlined | Partial key (of a weak entity) |
| Diamond | Relationship set |
| **Double** diamond | **Identifying** relationship |
| Line | Participation (single = partial, **double = total**) |

A compact ASCII rendering, used throughout this module:

```
   ┌──────────┐                          ┌──────────┐
   │ MEMBER   │ 1              N         │  LOAN    │
   │ *mid     ├────────◇ borrows ◇───────┤  issued  │
   │  name    │                          │  due     │
   └──────────┘                          └──────────┘
     * = key attribute      1 / N = cardinality ratio
```

---

## 2.2 Entities and attributes

| Term | Meaning | Example |
|---|---|---|
| **Entity** | One distinguishable thing | the student with roll 101 |
| **Entity type / set** | The category, and the set of all its instances | `STUDENT` |
| **Attribute** | A property of an entity | `name`, `dob` |

### The attribute types that get asked

| Type | Meaning | Example | Conversion consequence |
|---|---|---|---|
| **Simple (atomic)** | Indivisible | `age`, `roll` | One column |
| **Composite** | Decomposes into parts | `address` → (`street`, `city`, `pin`) | **Flatten**: one column per leaf |
| **Multivalued** | Several values per entity | `phone` (a member has 2 numbers) | **Its own table** |
| **Derived** | Computable from other data | `age` from `dob`; `total` from line items | **Don't store it** (normally) |
| **Key** | Uniquely identifies | `roll` | Becomes the PK |
| **Complex** | Composite *and* multivalued | several addresses, each structured | Its own table with the parts as columns |

**Why derived attributes aren't stored:** a stored `age` is wrong the day after you store it, and a stored `total` disagrees with the line items the moment one changes. Either compute it in the query, use a generated/computed column, or — if reads dominate and the cost is real — store it deliberately as **denormalization** and own the job of keeping it correct (M3, M10). Saying it that way shows you know it is a trade-off, not a rule.

**Multivalued is the one that creates a table**, and the reason is 1NF: a cell must hold one atomic value (M1, §1.1). `phone = '9000000001, 9000000002'` is a bug that will cost you a correct `WHERE` clause within a week.

---

## 2.3 Relationships

### Degree — how many entity sets take part

| Degree | Name | Example |
|---|---|---|
| 1 | **Unary** / recursive | `EMPLOYEE` manages `EMPLOYEE` |
| 2 | **Binary** | `STUDENT` enrols in `COURSE` |
| 3 | **Ternary** | `DOCTOR` prescribes `DRUG` to `PATIENT` |

Binary covers almost everything. A ternary relationship is usually better modelled as its own entity — and if an interviewer offers you one, saying "I'd promote `prescription` to an entity so it can have its own date and dosage" is the senior answer.

### Cardinality ratio — the rule that decides your schema

**This is the single most important thing in the module**, because it is what §2.6 switches on.

| Ratio | Reads as | Example | Becomes |
|---|---|---|---|
| **1:1** | one ↔ one | employee ↔ parking space | FK on either side + `UNIQUE` |
| **1:N** | one → many | department → employees | **FK on the N side** |
| **M:N** | many ↔ many | students ↔ courses | **A junction table** |

```
   1:1    [EMPLOYEE] 1 ──── 1 [PARKING]      one FK, made UNIQUE
   1:N    [DEPT]     1 ──── N [EMPLOYEE]     FK lives on EMPLOYEE
   M:N    [STUDENT]  M ──── N [COURSE]       new table: enrollment(roll, code)
```

**The question to ask yourself, out loud, in both directions:** "Can one department have many employees? Yes. Can one employee be in many departments? No." → 1:N, FK on employee. Interviewers specifically listen for you checking both directions, because that is where requirements get misread.

### Participation — total or partial

| Participation | Means | Enforced by |
|---|---|---|
| **Total** (mandatory, double line) | **Every** entity on this side must participate | `NOT NULL` on the FK |
| **Partial** (optional, single line) | Some may not participate | FK nullable |

Example: every `LOAN` must involve a `MEMBER` (total — a loan with no borrower is nonsense, so `loan.mid` is `NOT NULL`), but not every `MEMBER` has a loan (partial).

**This is where participation stops being vocabulary and becomes a column definition.** Total participation = `NOT NULL`. That is the whole translation.

### Relationship attributes

A relationship can carry its own data: `enrollment` has a `grade`; `borrows` has `issue_date`. These attributes belong to the **relationship**, not to either entity — the grade is not a property of the student or of the course, but of that student *in* that course. They land in the junction table.

---

## 2.4 Weak entity sets

A **weak entity** cannot be identified by its own attributes alone. It needs its owner.

```
   ┌──────────┐                   ╔════════════╗
   │  BOOK    │ 1    ╔════════╗ N ║   COPY     ║
   │ *isbn    ├──────║ has    ║───║ -copy_no   ║     ╔═══╗ double = weak /
   │  title   │      ╚════════╝   ║  shelf     ║     ╚═══╝ identifying
   └──────────┘   identifying     ╚════════════╝
                  relationship
   PK of COPY = (isbn, copy_no)      -copy_no = partial key (discriminator)
```

| Term | Meaning |
|---|---|
| **Owner / identifying entity** | The strong entity it depends on (`BOOK`) |
| **Identifying relationship** | The relationship to the owner (always **total** on the weak side) |
| **Partial key / discriminator** | Distinguishes weak entities *within one owner* (`copy_no`) |
| **Primary key** | **owner's PK + partial key** → `(isbn, copy_no)` |

**The test for a weak entity:** "does this thing's identity make sense without naming its parent?" Copy number 2 is meaningless — copy 2 *of which book?* A room number needs its building; an order line needs its order.

**And the consequence worth stating:** a weak entity is precisely the case where `ON DELETE CASCADE` is correct (M1, §1.6). Deleting a book must delete its copies, because a copy cannot exist without the book. This is the clean answer to "when would you actually use `CASCADE`?"

---

## 2.5 Extended ER: generalization, specialization, aggregation

### Specialization and generalization (the ISA hierarchy)

```
                 ┌──────────────┐
                 │   PERSON     │   <- superclass: shared attributes
                 │ *pid  name   │
                 └──────┬───────┘
                       ISA
               ┌────────┴────────┐
        ┌──────▼─────┐    ┌──────▼──────┐
        │  STUDENT   │    │  FACULTY    │   <- subclasses: specific attributes
        │  roll  cgpa│    │ empid  dept │
        └────────────┘    └─────────────┘
```

| Direction | Means |
|---|---|
| **Specialization** | Top-down: split `PERSON` into `STUDENT` and `FACULTY` |
| **Generalization** | Bottom-up: notice `STUDENT` and `FACULTY` share attributes, factor out `PERSON` |

Same structure, opposite thought process. Two constraints get asked:

| Constraint | Options |
|---|---|
| **Disjoint vs overlapping** | Can one person be both a student and faculty? Disjoint = no, overlapping = yes |
| **Total vs partial** | Must every person be one of the subclasses, or can a person be neither? |

If OOP M3 (inheritance) is fresh: ISA *is* inheritance, and the "is-a vs has-a" test from OOP M5 applies unchanged. An ER diagram and a UML class diagram are the same skill twice.

### Aggregation

Treating a whole relationship as one abstract entity so another relationship can point at it. Standard example: `(EMPLOYEE works-on PROJECT)` is itself *monitored by* a `MANAGER` — the manager monitors the assignment, not the employee and not the project.

Tier 3 in practice: say what it is, note that you would usually promote the relationship to a real entity (`assignment`) and attach the FK to that, and move on. Interviewers rarely pursue it, and "promote it to an entity" is the answer they want anyway.

---

## 2.6 ER → relational: the conversion rules

**Learn these as a drill.** Given any ER diagram, apply them in order and the schema falls out. This is the highest-value section in the module.

### R1 — Strong entity set → one table

PK = the key attribute.

```sql
-- MEMBER(*mid, name, join_date)
CREATE TABLE member(mid INTEGER PRIMARY KEY, name TEXT NOT NULL, join_date TEXT NOT NULL);
```

### R2 — Composite attribute → flatten to its leaves

```
address(street, city, pin)  ->  street TEXT, city TEXT, pin TEXT
```

No `address` column exists. (Store it as JSON only if you will never filter or join on the parts — and say so if you do.)

### R3 — Multivalued attribute → its own table

PK = (owner's PK, the value). The FK cascades, because a phone number without its owner is garbage.

```sql
CREATE TABLE member_phone(
  mid   INTEGER REFERENCES member(mid) ON DELETE CASCADE,
  phone TEXT,
  PRIMARY KEY (mid, phone));
```

### R4 — Derived attribute → don't store it

Compute in the query, or use a generated column. Store it only as deliberate denormalization.

### R5 — 1:1 relationship → FK on one side, with `UNIQUE`

Put the FK on the side with **total participation** (so it can be `NOT NULL`), and make it `UNIQUE` — that `UNIQUE` is what enforces the "1" on the other end. Without it you have built a 1:N.

```sql
-- every PARKING space is assigned to exactly one EMPLOYEE; not every employee has one
CREATE TABLE parking(
  slot_no INTEGER PRIMARY KEY,
  eid     INTEGER NOT NULL UNIQUE REFERENCES employee(eid));
```

### R6 — 1:N relationship → FK on the **N** side

The commonest rule in the subject. Relationship attributes go on the N side too.

```sql
-- DEPT 1 ---- N EMPLOYEE
CREATE TABLE employee(
  eid  INTEGER PRIMARY KEY,
  name TEXT,
  did  INTEGER REFERENCES dept(did));     -- NOT NULL if participation is total
```

**Never** put a list of employees on the department. **Never** create a third table for a 1:N — a junction table for a 1:N is the single most common beginner error, and it costs you a join forever.

### R7 — M:N relationship → junction table

PK = both FKs together. Relationship attributes become columns.

```sql
-- STUDENT M ---- N COURSE, with a grade on the relationship
CREATE TABLE enrollment(
  roll   INTEGER REFERENCES student(roll),
  code   TEXT    REFERENCES course(code),
  grade  TEXT,
  PRIMARY KEY (roll, code));              -- composite PK = one enrolment per pair
```

That composite PK is doing real work: it states "a student takes a course at most once". If a student *may* repeat a course, the PK must grow (add `semester`) — and noticing that is exactly the kind of requirement clarification interviewers reward.

### R8 — Weak entity set → table keyed by owner + partial key

```sql
CREATE TABLE copy(
  isbn    TEXT REFERENCES book(isbn) ON DELETE CASCADE,
  copy_no INTEGER,
  shelf   TEXT,
  PRIMARY KEY (isbn, copy_no));
```

### R9 — Ternary relationship → table with three FKs

PK = all three FKs (or a subset, if the cardinality allows).

### R10 — Unary / self relationship → FK to the same table

```sql
CREATE TABLE employee(
  eid        INTEGER PRIMARY KEY,
  name       TEXT,
  manager_id INTEGER REFERENCES employee(eid));   -- NULL for the CEO
```

Nullable on purpose: somebody has no manager. This is the table behind every manager-chain and recursive-CTE question in M5.

### R11 — ISA hierarchy → one of three strategies

| Strategy | Shape | Good when | Cost |
|---|---|---|---|
| **Single table** (one table, a `type` column, nullable subclass columns) | `person(pid, name, type, roll, cgpa, empid, dept)` | Few subclass-specific attributes; overlapping subclasses | Lots of NULLs; `CHECK` constraints must police which columns apply to which type |
| **Table per subclass, sharing the PK** | `person(pid,name)` + `student(pid→person, roll, cgpa)` + `faculty(pid→person, empid, dept)` | **Usually the best** — disjoint or overlapping, clean constraints | A join to see the whole entity |
| **Table per concrete subclass** (no superclass table) | `student(pid,name,roll,cgpa)` + `faculty(pid,name,empid,dept)` | Subclasses never queried together; total and disjoint | Shared attributes duplicated; no single place to FK "a person" |

Default to the middle one and say why: **it keeps a single `person` identity other tables can reference**, which the third strategy loses.

### The table-counting numerical

"How many tables does this ER diagram produce?"

> **1 per entity set (strong and weak) + 1 per M:N relationship + 1 per multivalued attribute + 1 per ternary relationship.**
> **1:1 and 1:N relationships add no tables** — they add a column.

Worked: 3 entity sets, one M:N between two of them, one 1:N, one multivalued attribute →
**3 + 1 + 0 + 1 = 5 tables.**

---

## 2.7 Worked schema 1 — a library

**Requirements.** Members have a name, a join date and possibly several phone numbers. Books have an ISBN, title and year, and are written by one or more authors (an author writes several books). The library holds several physical copies of each book, numbered within the book. A member borrows a copy, with an issue date and a due date.

**Modelling decisions, with the reasoning you would say out loud:**

| Decision | Why |
|---|---|
| `phone` is **multivalued** → its own table (R3) | Several numbers per member, and 1NF forbids a list in a cell |
| `BOOK ↔ AUTHOR` is **M:N** → junction table (R7) | A book has many authors *and* an author has many books — check both directions |
| `COPY` is a **weak entity** of `BOOK` (R8) | "Copy 2" means nothing without the book; PK = `(isbn, copy_no)` |
| `LOAN` references the **copy**, not the book | You lend a physical object. Lending "the ISBN" cannot track which copy is out |
| `loan.mid` is `NOT NULL` | Total participation: a loan must have a borrower |
| `ON DELETE CASCADE` on `copy`, `RESTRICT`-by-default on `loan → member` | A copy can't outlive its book; a member with loans shouldn't vanish silently |

### The schema (created and populated)

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE member(
  mid       INTEGER PRIMARY KEY,
  name      TEXT NOT NULL,
  join_date TEXT NOT NULL);

CREATE TABLE member_phone(                      -- R3: multivalued
  mid   INTEGER REFERENCES member(mid) ON DELETE CASCADE,
  phone TEXT,
  PRIMARY KEY (mid, phone));

CREATE TABLE book(
  isbn  TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  year  INTEGER);

CREATE TABLE author(
  aid   INTEGER PRIMARY KEY,
  aname TEXT NOT NULL);

CREATE TABLE book_author(                       -- R7: M:N junction
  isbn TEXT    REFERENCES book(isbn),
  aid  INTEGER REFERENCES author(aid),
  PRIMARY KEY (isbn, aid));

CREATE TABLE copy(                              -- R8: weak entity
  isbn    TEXT REFERENCES book(isbn) ON DELETE CASCADE,
  copy_no INTEGER,
  shelf   TEXT,
  PRIMARY KEY (isbn, copy_no));

CREATE TABLE loan(                              -- R6: 1:N, with relationship attributes
  isbn       TEXT,
  copy_no    INTEGER,
  mid        INTEGER REFERENCES member(mid),
  issue_date TEXT NOT NULL,
  due_date   TEXT NOT NULL,
  PRIMARY KEY (isbn, copy_no, issue_date),      -- same copy may be re-issued later
  FOREIGN KEY (isbn, copy_no) REFERENCES copy(isbn, copy_no));   -- composite FK
```

Note the **composite foreign key** on `loan`: because `copy`'s PK is two columns, anything referencing a copy must reference both, in order (M1, §1.5).

### It works — verified queries

**Authors per book** (walking the M:N junction):

```sql
SELECT b.title, GROUP_CONCAT(a.aname, ', ') AS authors
FROM book b JOIN book_author ba ON b.isbn = ba.isbn
            JOIN author a       ON a.aid  = ba.aid
GROUP BY b.isbn ORDER BY b.title;
```

```
('Introduction to Algorithms', 'Cormen, Leiserson')
('The C Programming Language', 'Kernighan, Ritchie')
```

**Who holds which copy** (joining through a weak entity):

```sql
SELECT m.name, b.title, l.copy_no, l.due_date
FROM loan l JOIN member m ON m.mid = l.mid
            JOIN book b   ON b.isbn = l.isbn
ORDER BY m.name;
```

```
('Asha', 'The C Programming Language', 1, '2026-09-15')
('Ravi', 'Introduction to Algorithms', 1, '2026-10-04')
```

**Members with no loans** (the anti-join from M1, §1.9):

```sql
SELECT m.name FROM member m
LEFT JOIN loan l ON l.mid = m.mid
WHERE l.mid IS NULL ORDER BY m.name;
```

```
('Meera',)
```

**Each member's phone numbers** (the multivalued table, `LEFT JOIN` so phoneless members survive):

```
('Asha',  '9000000001 / 9000000002')
('Meera', None)
('Ravi',  '9000000003')
```

**The cascade, checked rather than assumed** — deleting the C book removed both its copies, leaving only the other book's copy:

```
copies left: [('978-0262033848', 1, 'B-1')]
```

---

## 2.8 Worked schema 2 — cinema booking, and a flaw worth seeing

**Requirements.** Movies play as shows on screens. A screen has numbered seats of different classes. A customer makes a booking for a show, holding one or more seats.

**The decision that matters:** a **seat belongs to the screen, not to the show.** Seat A1 is a physical chair that exists for every show on that screen. Model it per-show and you duplicate every seat for every showing forever. This is the most common mistake on this prompt.

```sql
CREATE TABLE movie(mid INTEGER PRIMARY KEY, title TEXT, mins INTEGER);
CREATE TABLE screen(sid INTEGER PRIMARY KEY, name TEXT, capacity INTEGER);

CREATE TABLE seat(                              -- weak entity of SCREEN
  sid     INTEGER REFERENCES screen(sid),
  seat_no TEXT,
  class   TEXT,
  PRIMARY KEY (sid, seat_no));

CREATE TABLE show(                              -- 1:N child of BOTH movie and screen
  show_id   INTEGER PRIMARY KEY,
  mid       INTEGER REFERENCES movie(mid),
  sid       INTEGER REFERENCES screen(sid),
  starts_at TEXT,
  UNIQUE (sid, starts_at));                     -- one screen can't host two shows at once

CREATE TABLE customer(cid INTEGER PRIMARY KEY, name TEXT);

CREATE TABLE booking(
  bid       INTEGER PRIMARY KEY,
  cid       INTEGER REFERENCES customer(cid),
  show_id   INTEGER REFERENCES show(show_id),
  booked_at TEXT);

CREATE TABLE booking_seat(                      -- M:N between a booking and seats
  bid     INTEGER REFERENCES booking(bid) ON DELETE CASCADE,
  sid     INTEGER,
  seat_no TEXT,
  PRIMARY KEY (bid, sid, seat_no),
  FOREIGN KEY (sid, seat_no) REFERENCES seat(sid, seat_no));
```

That `UNIQUE (sid, starts_at)` on `show` is worth pointing out unprompted: it is a business rule — *one screen cannot run two films at the same time* — enforced by the schema instead of by hope.

**Free seats for a show** (verified; seats A1 and A2 are booked under booking 500):

```sql
SELECT s.seat_no, s.class FROM seat s
WHERE s.sid = (SELECT sid FROM show WHERE show_id = 100)
  AND NOT EXISTS (SELECT 1 FROM booking_seat bs JOIN booking b ON b.bid = bs.bid
                  WHERE b.show_id = 100 AND bs.sid = s.sid AND bs.seat_no = s.seat_no)
ORDER BY s.seat_no;
```

```
('B1', 'silver')
('B2', 'silver')
```

And the same seats are free for the *later* show on the same screen, confirming seats are per-screen, not per-show:

```
free_in_show_101 = 4
```

### The flaw — and this is the interview moment

The `booking_seat` PK is `(bid, sid, seat_no)`. It stops the *same booking* holding seat A1 twice:

```
INSERT INTO booking_seat VALUES (500,1,'A1');   -- rejected:
                                UNIQUE constraint failed: booking_seat.bid, booking_seat.sid, booking_seat.seat_no
```

But it does **not** stop two *different* bookings from taking seat A1 for the same show. Tested with bookings 500 and 501, both on show 100:

```
PK (bid,sid,seat_no) only        ->  seat A1 sold TWICE for show 100   *** flaw ***
```

**Why the constraint misses it:** uniqueness is scoped to the booking, but the rule the business needs is scoped to the **show** — and `show_id` isn't in the table. The fix is to carry `show_id` into the junction and constrain on it:

```sql
CREATE TABLE booking_seat(
  bid     INTEGER REFERENCES booking(bid) ON DELETE CASCADE,
  show_id INTEGER REFERENCES show(show_id),         -- carried down deliberately
  sid     INTEGER,
  seat_no TEXT,
  PRIMARY KEY (bid, sid, seat_no),
  UNIQUE (show_id, sid, seat_no),                   -- <- one seat, one sale, per show
  FOREIGN KEY (sid, seat_no) REFERENCES seat(sid, seat_no));
```

Verified:

```
+ unique(show_id,sid,seat_no)    ->  second sale rejected:
                                UNIQUE constraint failed: booking_seat.show_id, booking_seat.sid, booking_seat.seat_no
```

**Two things to take from this.** First, `show_id` is now stored in both `booking` and `booking_seat` — a controlled, deliberate redundancy, and you should name it as such, adding that a `CHECK` or trigger (or a composite FK to `booking(bid, show_id)`) keeps the two in step. Second, and more important: **"which seat can be sold twice?" is exactly how interviewers probe a schema.** Walk your own design and ask what bad state it still permits. That habit is the difference between drawing tables and designing a schema.

---

## 2.9 The five-step method for a design prompt

When an interviewer says "design a schema for X", do this visibly. Ten to twelve minutes, out loud.

| Step | What you do | What it sounds like |
|---|---|---|
| **1. Clarify scope** | Ask 2–3 questions, state assumptions | "Do we track individual copies or just titles? I'll assume copies." |
| **2. List entities** | The nouns that have identity | "Member, Book, Author, Copy, Loan." |
| **3. Attributes and keys** | Per entity; flag multivalued and derived | "Phones are multivalued, so a separate table." |
| **4. Relationships** | For each pair: cardinality **in both directions**, then participation | "A book has many authors and an author many books → M:N." |
| **5. Convert and state keys** | Apply R1–R11; say each PK and FK aloud | "Junction table `book_author`, PK both columns." |
| **6. Attack your own schema** | Name a bad state it still allows, and fix it | "Two bookings could take the same seat — I'd add `UNIQUE(show_id, seat)`." |

Step 6 is optional in textbooks and decisive in interviews.

**Prompts worth practising by hand:** library, cinema booking, Splitwise (expense sharing), food delivery, ride hailing, hospital appointments, parking lot, URL shortener, and a college result system. The parking lot and Splitwise ones double as LLD prompts — compare what you build here with OOP M9a, where the same two problems are modelled as *classes*. Seeing the same requirements as tables and as objects is one of the fastest ways to make both subjects click.

---

## 2.10 Consolidation

### Must remember (module)

1. **Cardinality decides everything:** 1:1 → FK + `UNIQUE`; 1:N → FK on the **N** side; M:N → **junction table**.
2. A junction table for a **1:N** is a mistake, not a style choice.
3. For 1:1, the `UNIQUE` is what makes it 1:1. Omit it and you have built a 1:N.
4. **Total participation = `NOT NULL` on the FK.** That is the whole translation.
5. **Multivalued attribute → its own table.** Never a comma-separated column.
6. **Composite attribute → flatten** into one column per leaf.
7. **Derived attribute → don't store**, unless you are denormalizing on purpose and own the consistency.
8. **Weak entity PK = owner's PK + partial key**, and its identifying relationship is always total — the one place `ON DELETE CASCADE` is clearly right.
9. Referencing a weak entity needs a **composite foreign key**.
10. Table count = entity sets + M:N relationships + multivalued attributes + ternary relationships. **1:1 and 1:N add none.**
11. Relationship attributes live in the junction table (M:N) or on the N side (1:N).
12. ISA: default to **table-per-subclass sharing the superclass PK**, because it keeps one identity to reference.
13. A junction table's **composite PK encodes a rule** ("at most once per pair"). If repeats are allowed, the PK must grow.
14. Seats belong to the screen, not the show; order lines to the order, not the customer. **Attach a child to the thing it genuinely depends on.**
15. A schema built properly from ER is usually already in 3NF — M3 then mostly confirms it.

### Common wrong answers

| Candidate says / does | Why it loses marks | Instead |
|---|---|---|
| Creates a third table for a 1:N | Unnecessary join forever | FK on the N side |
| 1:1 with a plain FK, no `UNIQUE` | Permits many children — it's a 1:N | Add `UNIQUE` |
| `phone VARCHAR(100)` holding "num1, num2" | Violates 1NF; can't index, join or validate | Separate table |
| Stores `age` | Wrong tomorrow | Store `dob`, compute age |
| Stores `total` with no mention of the trade-off | Silent inconsistency risk | "Derived — I'd compute it, or denormalize deliberately and keep it in sync" |
| Weak entity given its own surrogate ID with no owner reference | Loses the dependency; permits orphans | PK = owner PK + partial key |
| "A weak entity is one with no primary key" | It has one — just a borrowed one | "It has no key *of its own*; its PK includes the owner's" |
| Confuses cardinality **ratio** with **participation** | Different questions: *how many* vs *must it at all* | 1:N is the ratio; total/partial is participation |
| Checks cardinality in one direction only | Where M:N gets misread as 1:N | State both directions out loud |
| "ER diagrams are the final design" | ER is a thinking tool | Tables are the deliverable |
| Never questions the finished schema | Misses the bad states it permits | Attack it yourself (step 6) |

### Interview Q&A bank

**Q1. Entity vs entity set vs attribute?**
An entity is one thing; an entity set is the category and all its instances; attributes are its properties. `STUDENT` is the set, roll 101 is an entity, `name` is an attribute.

**Q2. What are the attribute types?**
Simple, composite, multivalued, derived, key, complex. The ones with conversion consequences: composite flattens into columns, multivalued becomes its own table, derived isn't stored.

**Q3. How do you convert a 1:N relationship to tables?**
Put a foreign key on the N side, pointing at the 1 side's PK, plus any relationship attributes. No third table.
*Follow-up:* "And if participation is total on the N side?" → Make the FK `NOT NULL`.

**Q4. How do you convert M:N?**
A junction table whose PK is both foreign keys, plus the relationship's own attributes.
*Follow-up:* "What if the pair can repeat?" → Widen the PK (add `semester`, `issue_date`) or use a surrogate PK plus a `UNIQUE` on the real combination.

**Q5. How do you convert 1:1, and what's the catch?**
FK on either side — preferably the one with total participation so it can be `NOT NULL` — **with a `UNIQUE` constraint**. Without `UNIQUE` you've built 1:N.

**Q6. What is a weak entity? Give an example and its key.**
An entity that can't be identified without its owner. `COPY` of a `BOOK`: PK = `(isbn, copy_no)`, where `copy_no` is the partial key. Its identifying relationship is total, and `ON DELETE CASCADE` is appropriate.

**Q7. Cardinality ratio vs participation constraint?**
Ratio is how many entities relate (1:1, 1:N, M:N). Participation is whether an entity *must* relate at all (total vs partial). Ratio shapes the tables; participation decides `NOT NULL`.

**Q8. Generalization vs specialization vs aggregation?**
Specialization is top-down (split a superclass), generalization bottom-up (factor out shared attributes) — same structure, opposite direction. Aggregation treats a whole relationship as an entity so something else can relate to it; in practice, promote it to a real entity.

**Q9. Three ways to map an ISA hierarchy, and which you'd pick?**
Single table with a type column and nullable attributes; table per subclass sharing the superclass PK; table per concrete subclass. Default to the second — other tables can still reference one `person` identity.

**Q10. How many tables will this ER diagram produce?**
One per entity set, plus one per M:N relationship, plus one per multivalued attribute, plus one per ternary. 1:1 and 1:N contribute columns, not tables.

**Q11. Why not store a multivalued attribute as a comma-separated string?**
It breaks 1NF, so you can't index it, join on it, constrain it or query one value without string surgery. A separate table makes every one of those a normal query.

**Q12. Design the schema for a library. (Walk me through it.)**
Use §2.9: clarify copies vs titles, list entities, flag phone as multivalued, state `BOOK↔AUTHOR` as M:N and `COPY` as weak, then produce the seven tables of §2.7 naming each key — then point out one bad state and fix it.

**Q13. Would your schema let the same seat be sold twice?**
(§2.8.) Scope the uniqueness to the show, not the booking: carry `show_id` into the junction table and add `UNIQUE(show_id, sid, seat_no)`. Note the controlled redundancy and how you'd keep it consistent.

### Practice

1. Convert: `DEPARTMENT (1) ── (N) EMPLOYEE`, where every employee must belong to a department but a department may be empty. Write the DDL, and say which constraint encodes each participation.
2. Convert: `STUDENT (M) ── (N) COURSE` with attributes `grade` and `semester`, where a student may repeat a course in a later semester. What exactly is the PK?
3. `HOTEL` has `ROOM`s numbered within the hotel. A `GUEST` books a room for a date range. Identify the weak entity, give every PK, and write the DDL.
4. Count the tables: 4 entity sets; one M:N; two 1:N; one multivalued attribute; one weak entity (already counted among the 4); one ternary relationship.
5. Model Splitwise: users, groups, expenses, who paid, who owes what share. Where does the M:N go, and what stops the shares of one expense summing to more than the total? (Be honest about which rule the schema can and cannot enforce.)
6. `EMPLOYEE` 1:1 `PARKING_SLOT`. Someone writes `parking_slot(slot_no PK, eid REFERENCES employee(eid))` with no `UNIQUE`. Give the exact `INSERT` sequence that breaks the 1:1.
7. Take the library schema in §2.7 and name two bad states it still permits. (Hints: can a copy be on loan to two members at once? Can `due_date` precede `issue_date`?) Write the constraints that fix them.
8. Redraw the cinema schema with seats modelled per *show* instead of per screen. How many seat rows exist after a year of 5 shows a day on a 200-seat screen, and what breaks when management renames seat A1?

---

## Exit checklist

```
[ ] I can list the ER symbols and what double/dashed shapes mean
[ ] I can name all six attribute types and the conversion consequence of each
[ ] I always check cardinality in BOTH directions before deciding the ratio
[ ] I can state R1-R11 from memory and apply them to a fresh diagram
[ ] I know 1:1 needs UNIQUE, and why
[ ] I know total participation becomes NOT NULL
[ ] I can identify a weak entity, give its PK, and reference it with a composite FK
[ ] I can count the tables an ER diagram produces
[ ] I can give the three ISA mappings and defend my default
[ ] I can design a library schema end to end in 10 minutes, naming every key
[ ] I can attack my own schema and name a bad state it still permits
[ ] I can explain why seats belong to the screen and not the show
```

---

## Next

**Part 5: M3 — Normalization.** The centrepiece, and the most-asked DBMS topic: insert/update/delete anomalies, functional dependencies and Armstrong's axioms, **attribute closure and the mechanical procedure for finding every candidate key**, prime vs non-prime attributes, then 1NF → 2NF → 3NF → BCNF each framed as the anomaly it eliminates, lossless-join and dependency-preserving decomposition (and the trade-off between them), 4NF/5NF briefly, and when denormalization is the right call.
