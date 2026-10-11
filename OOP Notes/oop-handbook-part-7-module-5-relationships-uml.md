# OOP Placement Handbook (C++) — Part 7
# Module 5: Object Relationships and UML

**Module 5 · 1.5–2 hours · Tier 1 (relationships) / Tier 2 (UML) · Requires: M0–M4**

---

## Why this module matters more than its size suggests

Two things in this module appear constantly:

1. **"Association vs aggregation vs composition"** is one of the standard OOP theory questions, and it's usually answered with vague words ("weak has-a", "strong has-a") and no test for telling them apart. This module gives you the test.
2. **Every LLD round starts with a class diagram.** If you can't draw relationships with the right arrows and multiplicities, the interviewer can't follow your design, and the round goes badly before you write any code.

It also answers a judgement question product companies like: *"Why favour composition over inheritance?"*

The organising principle:

> **Relationships between objects are about two things: who knows about whom, and who owns whose lifetime. Association is knowing. Aggregation is a whole-part relationship without lifetime ownership. Composition is a whole-part relationship where the whole owns the part's lifetime. Ask "if the whole is destroyed, does the part die?" and the classification is usually decided.**

---

## 5.1 The relationship spectrum

From weakest to strongest coupling:

```
 Dependency  ->  Association  ->  Aggregation  ->  Composition  ->  Inheritance
 "uses          "knows            "has-a,          "has-a,           "is-a"
  briefly"        about"           shared /         owns the
                                   independent"     lifetime"
 weakest coupling  ------------------------------------------------>  strongest coupling
```

| Relationship | Meaning | Lifetime | Example |
|---|---|---|---|
| **Dependency** | A uses B temporarily (a parameter or local) | Unrelated | `Printer::print(const Document&)` |
| **Association** | A knows about B and holds a reference to it | Independent | `Teacher` ↔ `Student` |
| **Aggregation** | A *has* B as a part, but B exists independently and can be shared | Independent | `Team` has `Player`s; `Department` has `Professor`s |
| **Composition** | A *owns* B; B is created and destroyed with A and isn't shared | **B dies with A** | `House` has `Room`s; `Order` has `OrderLine`s |
| **Inheritance** | A is a kind of B | A contains B (M3) | `Car` is a `Vehicle` |

Aggregation and composition are both **special kinds of association**. All three are "has a reference to" relationships, distinguished by ownership.

---

## 5.2 Association

### 1. What is it?

A structural relationship where objects of one class **know about** objects of another and can interact with them, **without ownership**. Both have independent lifetimes.

### 2. Examples

- A `Teacher` teaches many `Student`s; a `Student` has many `Teacher`s (many-to-many).
- A `Doctor` treats `Patient`s.
- A `Driver` drives a `Car`.

Neither creates nor destroys the other. Delete a teacher and the students remain.

### 3. Direction and multiplicity

- **Unidirectional:** only A knows B (`Order → Customer`: the order knows its customer, the customer doesn't keep a list of orders).
- **Bidirectional:** both know each other. This is harder to keep consistent, so prefer unidirectional unless you need both directions.
- **Multiplicity:** how many objects take part at each end: `1`, `0..1`, `*` (many), `1..*` (at least one).

### 4. In C++

Non-owning references: raw pointers, references, `weak_ptr`, or IDs.

```cpp
class Student;                         // forward declaration
class Teacher {
    string name;
    vector<Student*> students;         // non-owning: Teacher never deletes them
public:
    void addStudent(Student* s) { students.push_back(s); }
};
```

---

## 5.3 Aggregation

### 1. What is it?

A **whole-part** relationship (has-a) in which the part **can exist independently of the whole** and may be **shared** by several wholes. Also called *weak has-a*.

### 2. Examples

| Whole | Part | Why it's aggregation |
|---|---|---|
| `Team` | `Player` | Disband the team and the players still exist; a player can move to another team |
| `Department` | `Professor` | Close a department and the professors move elsewhere |
| `Playlist` | `Song` | Delete a playlist and the songs stay in the library; a song can be in many playlists |
| `Library` | `Book` | Books can be transferred to another library |

### 3. In C++

The part is created **outside** the whole and passed in. The whole holds a non-owning pointer or reference (or a `shared_ptr` if ownership is genuinely shared).

```cpp
class Player { string name; public: explicit Player(string n) : name(n) {} };

class Team {
    vector<Player*> roster;                 // does NOT own the players
public:
    void add(Player* p) { roster.push_back(p); }
    ~Team() { /* does NOT delete players */ }
};

Player virat("Virat");
{
    Team rcb;
    rcb.add(&virat);
}                                            // rcb destroyed; virat still alive
```

---

## 5.4 Composition

### 1. What is it?

A whole-part relationship in which the whole **owns** the part: the part is created with the whole, destroyed with it, and **not shared**. Also called *strong has-a*.

### 2. Examples

| Whole | Part | Why it's composition |
|---|---|---|
| `House` | `Room` | A room can't exist without its house; demolish the house and the rooms go with it |
| `Order` | `OrderLine` | Order lines have no meaning outside their order |
| `Human` | `Heart` | (The textbook example) |
| `Document` | `Paragraph` | Delete the document and its paragraphs are gone |
| `Car` | `Engine` | Usually composition in a car-modelling app. In a garage/inventory app where engines are swapped and tracked separately, it's aggregation: the domain decides |

### 3. In C++

The part is a **member by value**, or held by `unique_ptr` (needed when it's polymorphic, optional, or large).

```cpp
class Room { string label; public: explicit Room(string l) : label(l) {} };

class House {
    vector<Room> rooms;                      // by value: Rooms live and die with the House
    unique_ptr<class Roof> roof;             // owned, polymorphic or optional: unique_ptr
public:
    House() { rooms.emplace_back("Kitchen"); rooms.emplace_back("Bedroom"); }
};                                           // ~House destroys rooms and roof automatically
```

The whole usually **creates** its parts itself (in its constructor or factory methods), rather than receiving them from outside. That's a good heuristic.

---

## 5.5 Association vs aggregation vs composition (the comparison)

### 1. The decisive test

> **"If the whole is destroyed, are the parts destroyed too?"**
> Yes → **composition**. No → **aggregation** (if it's whole-part) or **association** (if it's not whole-part at all).

Secondary test: **"Can the part be shared by several wholes at the same time?"** Yes → not composition.

### 2. The table

| | Association | Aggregation | Composition |
|---|---|---|---|
| Relationship | "knows / uses" | "has-a" (weak) | "has-a / part-of" (strong) |
| Whole-part? | No | Yes | Yes |
| Ownership | None | None (or shared) | **Exclusive** |
| Lifetime | Independent | Independent | **Part dies with the whole** |
| Part shareable? | Yes | **Yes** | **No** |
| Who creates the part | Someone else | Usually someone else | Usually the whole |
| UML symbol | Plain line / arrow | **Hollow** diamond ◇ at the whole | **Filled** diamond ◆ at the whole |
| C++ member | Raw pointer / reference / `weak_ptr` / ID | Raw pointer / reference / `shared_ptr` | **Value member** or `unique_ptr` |
| Example | Teacher – Student | Team – Player | House – Room |

### 3. The model answer (about 40 seconds)

*"All three describe one object holding a reference to another; they differ in ownership. Association is just knowing about another object, like a teacher and student, with independent lifetimes. Aggregation is a whole-part relationship where the part can exist without the whole and can be shared; a team has players, but if the team is disbanded the players still exist. Composition is a whole-part relationship with exclusive ownership; a house's rooms are destroyed with the house. The test I use is: if the whole is destroyed, do the parts go too? In C++, composition maps to value members or unique_ptr, and aggregation or association to non-owning pointers or references."*

### 4. Common wrong answers

- "Aggregation is when the class has a pointer; composition is when it has an object." Close, but the *implementation* follows the *ownership* decision, not the other way round. A `unique_ptr` member is a pointer and still composition.
- Giving an example without a lifetime argument. Always state what happens when the whole is destroyed.
- Treating examples as absolute. `Car`–`Engine` depends on the domain; saying so shows maturity.

---

## 5.6 Dependency

The weakest relationship: A **uses** B briefly, as a parameter, a local variable or a return type, but doesn't keep a reference to it.

```cpp
class ReportGenerator {
public:
    string generate(const Database& db) {      // depends on Database only during this call
        return db.query("...");
    }
};
```

UML: a **dashed arrow** from A to B. In design reviews, dependencies are the cheapest coupling. Prefer them over stored associations when the relationship really is short-lived.

---

## 5.7 Favour composition over inheritance

### 1. The principle

> *"Favour object composition over class inheritance."* (Gang of Four, *Design Patterns*, 1994)

Get reuse and variation by **holding** objects that provide behaviour (has-a), rather than by **being** a subclass (is-a), unless the relationship is a genuine, substitutable is-a.

### 2. Why: the problems inheritance causes

| Problem | Explanation |
|---|---|
| **Class explosion** | Two independent dimensions of variation multiply. 3 fly behaviours × 3 quack behaviours = 9 subclasses |
| **Fixed at compile time** | An object can't change its base class at runtime; it can swap a member object |
| **Fragile base class** | A change in the base ripples into every subclass, sometimes silently |
| **Breaks encapsulation** | Subclasses depend on the base's protected internals |
| **Inherits everything** | Including methods that make no sense for the subclass (M3 P9: `Stack : vector`) |

### 3. Worked refactor: the duck problem

**Inheritance version: the explosion.**

```
                    Duck
        +-----------+-----------+-----------+
   MallardDuck  RubberDuck  WoodenDuck  RobotDuck ...
   (flies,      (no fly,    (no fly,    (flies with rockets,
    quacks)      squeaks)    silent)     beeps)
```

Behaviours get copied between siblings (`RobotDuck` and `MallardDuck` both fly, differently), or pushed into the base where they're wrong for some subclasses (`RubberDuck::fly()` overridden to do nothing, which is an LSP smell, M7).

**Composition version: behaviours as members.**

```cpp
struct FlyBehaviour   { virtual void fly() const = 0;   virtual ~FlyBehaviour() = default; };
struct QuackBehaviour { virtual void quack() const = 0; virtual ~QuackBehaviour() = default; };

struct FlyWithWings : FlyBehaviour   { void fly() const override   { cout << "flap\n"; } };
struct NoFly        : FlyBehaviour   { void fly() const override   { } };
struct Quack        : QuackBehaviour { void quack() const override { cout << "quack\n"; } };
struct Squeak       : QuackBehaviour { void quack() const override { cout << "squeak\n"; } };

class Duck {
    unique_ptr<FlyBehaviour>   flyB;          // HAS-A fly behaviour   (composition)
    unique_ptr<QuackBehaviour> quackB;        // HAS-A quack behaviour
public:
    Duck(unique_ptr<FlyBehaviour> f, unique_ptr<QuackBehaviour> q)
        : flyB(std::move(f)), quackB(std::move(q)) {}
    void performFly()   const { flyB->fly(); }
    void performQuack() const { quackB->quack(); }
    void setFly(unique_ptr<FlyBehaviour> f) { flyB = std::move(f); }   // change at RUNTIME
};

Duck mallard(make_unique<FlyWithWings>(), make_unique<Quack>());
Duck rubber (make_unique<NoFly>(),        make_unique<Squeak>());
rubber.setFly(make_unique<FlyWithWings>());     // impossible with inheritance
```

N fly behaviours + M quack behaviours = **N + M classes** instead of N × M. Behaviour can change at runtime. Each behaviour is testable on its own. This is the **Strategy pattern** (M8). Note that inheritance is still used, for the *interfaces*. The guideline isn't "never inherit"; it's "inherit interfaces, compose behaviour".

### 4. When inheritance is still right

- A genuine, substitutable **is-a** (passes LSP, M7).
- You need **polymorphism** through a common interface (abstract base classes and interfaces).
- Frameworks designed for extension through subclassing (the Template Method pattern).

### 5. Must remember

1. Composition = has-a, flexible, changeable at runtime, loosely coupled.
2. Inheritance = is-a, fixed at compile time, tightly coupled.
3. The duck example: N × M subclasses vs N + M behaviour classes.
4. "Inherit interfaces, compose implementations."

### 6. Interview question

- *"Why favour composition over inheritance?"* Inheritance couples the subclass tightly to the base's implementation, is fixed at compile time, and leads to class explosion when behaviour varies along several dimensions. Composition holds behaviours as member objects behind interfaces, so they can be mixed, swapped at runtime and tested independently. Inheritance is still right for genuine is-a relationships with substitutability. *Follow-up: "Which design pattern is this?"* Strategy.

---

## 5.8 UML class diagrams

You need just enough UML to draw a clear diagram in an LLD round, either on a whiteboard or as ASCII in a shared doc.

### 1. The class box

```
+---------------------------------+
|          ParkingLot             |   <- name (italic or <<abstract>> if abstract)
+---------------------------------+
| - id : string                   |   <- attributes:  visibility name : type
| - floors : List<Floor>          |
| - instance : ParkingLot         |   <- static: underlined (or marked {static})
+---------------------------------+
| + parkVehicle(v : Vehicle) : Ticket |  <- methods: visibility name(params) : return
| + unpark(t : Ticket) : double   |
| # computeFee(t : Ticket) : double |
+---------------------------------+
```

| Symbol | Visibility |
|---|---|
| `+` | public |
| `-` | private |
| `#` | protected |
| `~` | package (Java; rarely used for C++) |

Interfaces are marked `<<interface>>` above the name; abstract classes `<<abstract>>` or with an italic name.

### 2. The arrows (the part to memorise)

```
 Association        A ------------> B        A knows / uses B (plain line; arrow = navigability)
 Aggregation        A <>-----------  B        hollow diamond at the WHOLE (A has B, B independent)
 Composition        A <#>----------  B        filled diamond at the WHOLE (A owns B's lifetime)
 Inheritance        A ------------|> B        solid line, hollow triangle at the PARENT (A is-a B)
 Realization        A - - - - - - |> B        dashed line, hollow triangle (A implements interface B)
 Dependency         A - - - - - - -> B        dashed arrow (A uses B temporarily)
```

(In ASCII, `<>` = hollow diamond ◇, `<#>` = filled diamond ◆, `|>` = hollow triangle ▷.)

**The diamond goes on the whole's side; the triangle goes on the parent's side.** Getting these reversed is the commonest diagram mistake.

### 3. Multiplicity

Written near the end of the line it describes:

| Notation | Meaning |
|---|---|
| `1` | Exactly one |
| `0..1` | Zero or one (optional) |
| `*` or `0..*` | Zero or more |
| `1..*` | One or more |
| `2..4` | A range |

```
 Library <#>--------- 1..*  Shelf        a library has at least one shelf; shelves die with it
 Shelf   <>---------- 0..*  Book         a shelf holds any number of books; books outlive shelves
 Member  1 ------------ 0..5 Loan         a member can have at most 5 active loans
```

### 4. A complete small example: a library system

```
                      <<interface>>
                       Searchable
                     + search(q) : List<Book>
                            ^
                            :  (realization, dashed)
                            :
 +-------------+ 1    1..*  +-------------+  1     0..*  +------------+
 |   Library   |<#>---------|    Shelf    |<>------------|    Book    |
 +-------------+            +-------------+              +------------+
 | - name      |                                         | - isbn     |
 | + search()  |                                         | - title    |
 +-------------+                                         +------------+
        | 1                                                    ^ 1
        |                                                      |
        | 0..*                                                 |
 +-------------+ 1     0..5  +-------------+ 0..*              |
 |   Member    |-------------|    Loan     |-------------------+
 +-------------+             +-------------+
 | - memberId  |             | - dueDate   |
 +-------------+             +-------------+
        ^
        | (inheritance)
 +-------------+
 | PremiumMember|   (overrides the loan limit)
 +-------------+
```

Reading it: a Library *implements* Searchable, *owns* its shelves, and *has* members. Shelves *aggregate* books. A Member *is associated with* up to 5 Loans, and each Loan refers to exactly one Book. PremiumMember *is a* Member.

### 5. LLD tips

1. Draw the **core entities and relationships first**; add attributes and methods afterwards.
2. Write the multiplicities. They are often where requirements get clarified ("can a vehicle occupy two spots?").
3. Keep it to 6–10 classes on the board. You can mention more but needn't draw them.
4. Use interfaces at the points where variation is expected (payment, pricing strategy, notification channel). That's where the interviewer's "now add X" will land.

### 6. Must remember

1. `+ - #` = public, private, protected.
2. Hollow diamond = aggregation, filled = composition, **both at the whole**.
3. Hollow triangle with a solid line = inheritance; with a dashed line = realization; **at the parent or interface**.
4. Dashed arrow = dependency.
5. Always annotate multiplicity.

---

## 5.9 Consolidation

### Must remember (module)

1. Spectrum: dependency < association < aggregation < composition < inheritance (coupling increases).
2. Association = knows about, independent lifetimes, no ownership.
3. Aggregation = whole-part, part independent and shareable (Team–Player).
4. Composition = whole-part, part's lifetime owned by the whole, not shared (House–Room).
5. **Test: destroy the whole; do the parts die?**
6. C++: composition → value members or `unique_ptr`; aggregation/association → non-owning pointers/references (or `shared_ptr` for genuinely shared ownership).
7. Domain decides borderline cases (Car–Engine).
8. Composition over inheritance: avoids class explosion, allows runtime change, loose coupling. Strategy pattern.
9. UML: diamond at the whole, triangle at the parent, dashed for realization/dependency, multiplicities on the ends.

### Common wrong answers (module)

- Defining aggregation and composition only as "weak" and "strong" has-a, without the lifetime test.
- "Composition means the member is an object, aggregation means it's a pointer." Ownership decides, not syntax.
- "Composition over inheritance means never use inheritance."
- Diamonds or triangles drawn at the wrong end.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| Association vs aggregation vs composition? | Knows vs has-a (independent) vs owns (part dies with whole); the test is destroying the whole | Implement each in C++ |
| Example of aggregation? | Team–Player: players outlive the team and can switch teams | Of composition? (House–Room) |
| Is Car–Engine aggregation or composition? | Depends on the domain: composition if engines aren't tracked separately, aggregation if they're swapped/inventoried | |
| What is dependency? | Temporary use via a parameter or local, no stored reference | UML symbol? (Dashed arrow) |
| Why favour composition over inheritance? | Loose coupling, runtime flexibility, no class explosion | Which pattern? (Strategy) |
| When is inheritance right? | Genuine substitutable is-a, polymorphic interfaces | LSP (M7) |
| UML symbol for composition? | Filled diamond at the whole | For realization? (Dashed line, hollow triangle) |

### Practice

**P1.** Classify each as association, aggregation or composition. Justify with the lifetime test.
1. University – Department
2. Department – Professor
3. Customer – Order (in an e-commerce app)
4. Order – OrderItem
5. Pilot – Aeroplane
6. Folder – File (in a file system where deleting a folder deletes its files)
7. Playlist – Song
8. Bank – Account
9. Student – Course
10. Window – Button (in a GUI)

<details><summary>Answer</summary>

1. **Composition**: dissolve the university and its departments go with it.
2. **Aggregation**: professors exist independently and can move departments.
3. **Association**: neither owns the other. (Some designs say Customer aggregates Orders. Either is defensible if you argue lifetimes: orders usually persist for accounting even if the customer account is deleted, which argues against composition.)
4. **Composition**: order items are meaningless without their order.
5. **Association**: a pilot flies aeroplanes; neither owns the other.
6. **Composition**: by the stated rule, files die with the folder.
7. **Aggregation**: songs exist independently and can be in many playlists.
8. **Composition** (typical): accounts can't exist without the bank. Arguable if accounts are transferable between banks.
9. **Association** (many-to-many): neither owns the other.
10. **Composition**: the window creates and destroys its buttons.
</details>

**P2.** Draw a UML class diagram (ASCII) for: *"A hospital has many departments. Each department has many doctors; a doctor belongs to exactly one department but continues to exist if the department closes. Doctors treat many patients, and patients can see many doctors. Both doctors and patients are persons with a name and an age."*

<details><summary>Answer</summary>

```
 +-----------+ 1     1..* +-------------+ 1      0..* +----------+  0..*    0..*  +-----------+
 | Hospital  |<#>---------| Department  |<>-----------|  Doctor  |----------------|  Patient  |
 +-----------+            +-------------+             +----------+     treats     +-----------+
                                                            |                           |
                                                            +------------+--------------+
                                                                         |  (inheritance, hollow triangle)
                                                                         v
                                                                  +-------------+
                                                                  |   Person    |
                                                                  | - name      |
                                                                  | - age       |
                                                                  +-------------+
```

Hospital ◆ Department (composition), Department ◇ Doctor (aggregation: doctors survive a closure), Doctor–Patient (many-to-many association), Doctor and Patient ▷ Person (inheritance).
</details>

**P3.** A game has `Character`s with weapons (`Sword`, `Bow`, `Staff`) and movement types (`Walk`, `Fly`, `Swim`). A junior developer proposes subclasses like `FlyingArcher`, `SwimmingSwordsman` and so on. How many classes would that need, and what's the better design?

<details><summary>Answer</summary>

3 × 3 = **9** subclasses, growing multiplicatively. Better: `Character` holds `unique_ptr<Weapon>` and `unique_ptr<Movement>` (composition + Strategy), with 3 + 3 = 6 small classes and the ability to change weapon or movement at runtime.
</details>

**P4.** For each C++ member, say which relationship it most likely implements:
`vector<Wheel> wheels;` · `Customer* customer;` · `unique_ptr<Engine> engine;` · `vector<shared_ptr<Song>> songs;` · `void render(const Theme& t);`

<details><summary>Answer</summary>

Composition · Association (non-owning) · Composition · Aggregation with shared ownership · Dependency.
</details>

---

## Exit checklist

```
[ ] I can order dependency < association < aggregation < composition < inheritance
[ ] I can apply the "destroy the whole" test and the "shareable?" test
[ ] I can give two examples each of aggregation and composition with lifetime arguments
[ ] I can map each relationship to a C++ member type
[ ] I can explain composition over inheritance with the duck example (N×M vs N+M)
[ ] I can draw UML class boxes with visibility and the six relationship arrows correctly
[ ] I annotate multiplicities without being prompted
[ ] P1–P4 done
```

---

## Next

**Part 8: M6 — The Modern C++ Object Model.** It covers smart pointers as the language of ownership (`unique_ptr`, `shared_ptr`, `weak_ptr`, and the cycle leak), the four C++ casts and when `dynamic_cast` is justified, RTTI and `typeid`, exceptions and objects (catching by reference, exception-safety guarantees), and static vs dynamic polymorphism (CRTP vs virtual).
