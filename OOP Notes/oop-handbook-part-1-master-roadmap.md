# OOP Placement Handbook (C++) — Part 1: Master Roadmap

*Your roadmap for the object-oriented programming round: what to learn, in what order, how deep, and which interview questions each module answers. Later parts teach each module in full.*

---

## 0. How this handbook is built

This is the companion to the DSA handbook. It uses the same structure: Part 1 is the roadmap, and every later part is one module.

The DSA handbook stopped at a deliberate line. Part 2, Section A6, says: *"inheritance, virtual functions, polymorphism, operator overloading beyond comparison, copy constructors, rule of three/five, friend functions… belong to the OOP round."* This handbook starts at that line. Nothing here repeats the DSA material, and nothing there is needed here except basic C++ syntax.

**The focus is concepts.** OOP rounds at product companies are mostly verbal: "explain", "what's the difference", "what does this print", "why would you". Code in these notes is kept short, and each snippet demonstrates one concept. The exception is low-level design (M9a/M9b), where you write real classes.

Theory subjects need a slightly different note format from algorithms. Each concept uses:

1. **What is it?**
2. **Why does it exist?**
3. **Core idea** (with a diagram whenever there is a structure to see)
4. **How it works** (C++ code)
5. **Example / trace** (usually output prediction)
6. **Comparison** with its confusable neighbour
7. **Must remember**
8. **Common wrong answers** (what candidates say that loses marks)
9. **Interview questions** (question → crisp answer → likely follow-up)
10. **Practice**

Small topics use a compressed version, as in the DSA notes.

---

## 1. The master syllabus

13 parts. Hours include reading, writing the snippets yourself, and doing the practice. They assume you know C++ syntax from the DSA handbook.

| Part | Module | Hours | Tier | Answers questions like |
|---|---|---|---|---|
| 1 | Master roadmap | — | — | — |
| 2 | **M0** Classes and objects | 2–3 | 1 | struct vs class, `this`, static members, `sizeof` an empty class |
| 3 | **M1** Constructors, destructors, copying | 3–4 | 1 | Shallow vs deep copy, rule of three, why is the copy constructor's parameter a reference |
| 4 | **M2** Encapsulation and abstraction | 1.5–2 | 1 | Abstraction vs encapsulation, does `friend` break encapsulation |
| 5 | **M3** Inheritance | 3 | 1 | Types of inheritance, diamond problem, object slicing, protected inheritance |
| 6 | **M4** Polymorphism | 4–5 | 1 | Overloading vs overriding, vtable, virtual destructor, abstract class |
| 7 | **M5** Object relationships and UML | 1.5–2 | 1/2 | Aggregation vs composition, composition over inheritance |
| 8 | **M6** Modern C++ object model | 2–3 | 2 | `unique_ptr` vs `shared_ptr`, `dynamic_cast`, exceptions in constructors |
| 9 | **M7** SOLID and design principles | 2 | 2 | Explain SOLID with an example, LSP violation |
| 10 | **M8** Design patterns | 3–4 | 2/3 | Thread-safe Singleton, Factory, Strategy vs State, Observer |
| 11 | **M9a** LLD: method + Parking Lot, LRU Cache, Splitwise | 4–5 | 2 | "Design a parking lot" |
| 12 | **M9b** LLD: Snake & Ladder, Elevator, BookMyShow | 3–4 | 2/3 | Machine-coding rounds |
| 13 | **Consolidation** | 2 | — | Cheat sheets, output-prediction drill bank, rapid-fire Q&A |

**Total: about 30–37 hours.** Tier 1 alone (M0–M5) is about 15–19 hours.

---

## 2. Dependency map

```
               [M0] Classes & objects
                        |
               [M1] Constructors, destructors, copying
                        |
               [M2] Encapsulation & abstraction
                        |
               [M3] Inheritance
                        |
               [M4] Polymorphism          <- the centrepiece
                        |
          +-------------+--------------+
          |                            |
 [M5] Relationships & UML      [M6] Modern C++ object model
          |                       (skippable under time pressure)
          |
 [M7] SOLID
          |
 [M8] Design patterns
          |
 [M9a] LLD method + 3 designs
          |
 [M9b] 3 more designs
          |
 [Consolidation]
```

### The dependencies that actually bite

| To learn | You genuinely need | Why |
|---|---|---|
| Deep copy | Constructors + destructors + pointers | The bug deep copy fixes is a double `delete` in the destructor |
| Rule of three | Copy constructor + copy assignment + destructor | It is a rule *about* those three |
| Diamond problem | Inheritance + constructor order | Virtual inheritance changes who constructs the shared base |
| vtable | Inheritance + `virtual` | It is the mechanism behind overriding |
| Virtual destructor | Polymorphism + destructor order | The bug only appears when deleting through a base pointer |
| Object slicing | Inheritance + copy constructor | Slicing *is* the base class's copy constructor running |
| Composition over inheritance | Inheritance's limits + relationships | You must know what inheritance costs |
| SOLID | Polymorphism + abstract classes | Four of the five principles are about using interfaces well |
| Design patterns | SOLID + composition | Every pattern is a SOLID principle applied to a recurring problem |
| LLD | All of the above + UML | LLD is where you are graded on actually using it |

---

## 3. Priority tiers

### Tier 1 — must master (asked everywhere, including service companies)

| Topic | Why |
|---|---|
| Four pillars with real examples | The opening question of nearly every OOP round |
| Class vs object, struct vs class | Warm-up questions; a fumble here sets a bad tone |
| Constructor types, destructor, order of calls | Output-prediction questions are built on this |
| Shallow vs deep copy, copy constructor | The most common "C++-specific" OOP question |
| Abstraction vs encapsulation | The most common "difference between" question |
| Inheritance types and access modes | Asked as a table; easy marks if memorised |
| Diamond problem + virtual inheritance | The standard multiple-inheritance question |
| Overloading vs overriding | Asked in nearly every OOP round |
| Virtual functions, vtable/vptr | The question that separates product-company candidates |
| Virtual destructor | Short, frequent, and an easy follow-up to the vtable |
| Abstract class vs interface | Asked with a Java flavour even in C++ rounds |
| Aggregation vs composition | Frequently asked; also needed for LLD |

### Tier 2 — high priority at product companies

| Topic | Why |
|---|---|
| Rule of three / five / zero, move semantics basics | Shows real C++ understanding |
| Object slicing, name hiding | Classic trick questions |
| Smart pointers | "How do you avoid memory leaks in C++?" |
| SOLID | Standard at product companies, and the vocabulary of LLD rounds |
| Singleton, Factory, Strategy, Observer | The four patterns freshers are actually asked |
| LLD: Parking Lot, LRU Cache, Splitwise | The three most common LLD prompts |

### Tier 3 — good to know

| Topic | Why |
|---|---|
| Builder, Decorator, Adapter, State | Occasionally asked; useful vocabulary in LLD |
| `dynamic_cast`, RTTI, CRTP / static polymorphism | Deep-C++ interviewers only |
| Elevator, BookMyShow, Snake & Ladder LLD | Machine-coding companies (Flipkart, Swiggy, Razorpay, Uber, PhonePe and similar) |
| Exceptions in constructors and destructors | One good answer impresses; rarely asked |

### Tier 4 — skip for placements

Template metaprogramming, the full GoF catalogue (23 patterns), multiple dispatch, allocator design, ABI details beyond "vptr is usually the first word".

**If you have under two weeks:** do M0–M4 thoroughly, read M5, and do the Consolidation part. That covers the large majority of OOP questions asked of freshers.

---

## 4. Interview orientation (what the research says)

**The core is stable across sources.** 2026 question banks agree on the same top ten: the four pillars with examples, abstraction vs encapsulation, overloading vs overriding, the diamond problem, abstract class vs interface, access specifiers, constructor types, the `this` pointer, virtual vs pure virtual functions, and runtime polymorphism ([NextStep core-CS guide](https://gs.dnextstep.in/guides/core-cs-subjects-guide)).

**Product companies probe one level deeper.** They expect SOLID, design patterns, association vs aggregation vs composition, composition over inheritance, and language internals such as the C++ vtable ([GoodSpace, Aug 2026](https://goodspace.ai/blogs/379439/oops-interview-questions)). In a C++ interview, "how is runtime polymorphism implemented internally?" is the question to prepare hardest.

**LLD is a real round, but not for every fresher.** Low-level design and machine-coding rounds are common at product companies and are reported even at SDE-1 level. Typical prompts are a parking lot, expense splitting, an inventory system, a rate limiter and an elevator. Graders look at object modelling, entity relationships, extensibility, and how you respond when requirements change ([GreatFrontEnd, 2026](https://www.greatfrontend.com/blog/machine-coding-interview-questions-for-freshers-2026); [InterviewBit LLD guide](https://www.interviewbit.com/low-level-design-interview-questions/)). Pure campus fresher rounds lean more toward DSA, which is why LLD is Tier 2 here.

**Three practical points:**

1. **Every definition needs an example.** "Encapsulation is wrapping data and methods together" scores half marks. Add "for example, a `BankAccount` keeps `balance` private so that nobody can set it negative, and only `deposit` and `withdraw` can change it" and you get full marks.
2. **Output-prediction questions are common in written tests and OAs.** They test constructor order, virtual dispatch, slicing and hiding. The drill bank in the Consolidation part exists for this.
3. **Interviewers chain questions.** "What is polymorphism?" leads to "how is it implemented?", then "what is in the vtable?", then "why should the destructor be virtual?". Every module's Q&A section lists the follow-up, so you can practise the chain rather than isolated answers.

---

## 5. Question map

The 40 most frequent OOP questions, and where each is answered. Use this as a revision index.

| # | Question | Module |
|---|---|---|
| 1 | What is OOP? Why use it over procedural programming? | M0 |
| 2 | Class vs object | M0 |
| 3 | struct vs class in C++ | M0 |
| 4 | What is the `this` pointer? | M0 |
| 5 | Static data members and static member functions | M0 |
| 6 | Size of an empty class, and why it is not 0 | M0 |
| 7 | Const member functions | M0 |
| 8 | `new` vs `malloc` | M0 |
| 9 | What is a constructor? Its types? | M1 |
| 10 | Can a constructor be private / virtual / overloaded? | M1 |
| 11 | Copy constructor: when is it called? Why is its parameter a reference? | M1 |
| 12 | Shallow vs deep copy | M1 |
| 13 | Copy constructor vs assignment operator | M1 |
| 14 | Rule of three / five / zero | M1 |
| 15 | Initialiser list: when is it mandatory? | M1 |
| 16 | Destructor: can it be overloaded? Can it throw? | M1 |
| 17 | RAII | M1 |
| 18 | Encapsulation with an example | M2 |
| 19 | Abstraction with an example | M2 |
| 20 | Abstraction vs encapsulation | M2 |
| 21 | Friend function: does it break encapsulation? | M2 |
| 22 | Types of inheritance | M3 |
| 23 | Public vs protected vs private inheritance | M3 |
| 24 | Order of constructor and destructor calls in inheritance | M3 |
| 25 | Diamond problem and how C++ solves it | M3 |
| 26 | Object slicing | M3 |
| 27 | What is polymorphism? Compile-time vs runtime | M4 |
| 28 | Overloading vs overriding | M4 |
| 29 | How do virtual functions work (vtable/vptr)? | M4 |
| 30 | Why do we need a virtual destructor? | M4 |
| 31 | Pure virtual function, abstract class | M4 |
| 32 | Abstract class vs interface | M4 |
| 33 | Can a constructor be virtual? Calling a virtual from a constructor? | M4 |
| 34 | Association vs aggregation vs composition | M5 |
| 35 | Composition over inheritance: why? | M5 |
| 36 | Smart pointers | M6 |
| 37 | SOLID with examples | M7 |
| 38 | Implement a thread-safe Singleton | M8 |
| 39 | Factory vs Strategy, Observer use cases | M8 |
| 40 | Design a parking lot | M9a |

---

## 6. Schedules

Hours are OOP only, alongside your DSA work.

### 2 weeks (~1 h/day, ~14 h)

| Days | Focus |
|---|---|
| 1–2 | M0 |
| 3–5 | M1 (the copy sections twice) |
| 6 | M2 |
| 7–8 | M3 |
| 9–12 | M4 |
| 13 | M5 (read only) |
| 14 | Consolidation: drill bank + rapid-fire Q&A |

Skip: M6–M9b.

### 1 month (~1 h/day, ~28 h)

| Week | Modules |
|---|---|
| 1 | M0, M1, M2 |
| 2 | M3, M4 |
| 3 | M5, M7, M8 (Tier 2 patterns only) |
| 4 | M9a, Consolidation |

Skip or skim: M6, M9b.

### 2–3 months (~1 h on alternate days, alongside OS) — recommended

All 13 parts in order. Write every snippet yourself, compile it, and check the output against your prediction before reading the answer.

### Revision passes

| Pass | What you do | When |
|---|---|---|
| 1 | Read the module and type every snippet | During the module |
| 2 | Answer the module's Q&A out loud, without notes, and time yourself (aim for 60–90 s per answer) | End of the module |
| 3 | Output-prediction drill bank (Consolidation), on paper first | Weekly after M4 |
| 4 | Mock: someone asks 10 random questions from §5, including follow-ups | Final two weeks |
| 5 | Cheat sheets and confusable-pairs table only | Last 2–3 days |

Pass 2 matters most. OOP rounds are spoken, and knowing an answer is not the same as being able to say it cleanly.

---

## 7. Rules I will follow in every module

1. Concept first, code second. Code exists only to make a concept concrete.
2. C++17, plain style. No template tricks unless the topic is templates.
3. Every definition comes with a real-world example *and* a code example.
4. Every "difference between" question gets a comparison table.
5. Output-prediction examples show the exact output, with the reason for each line.
6. "Must remember" lists only non-obvious facts.
7. "Common wrong answers" covers what candidates actually say that is wrong or incomplete.
8. Interview Q&A answers are short enough to say in under a minute, and each includes the likely follow-up.
9. Java differences get a one-line note where interviewers commonly ask about them.
10. Implementation-defined details (exact `sizeof` values, vtable layout) are labelled as typical, not guaranteed.

---

## 8. Progress checklist

```
[ ] M0   Classes and objects
[ ] M1   Constructors, destructors, copying
[ ] M2   Encapsulation and abstraction
[ ] M3   Inheritance
[ ] M4   Polymorphism
[ ] M5   Object relationships and UML
[ ] M6   Modern C++ object model
[ ] M7   SOLID
[ ] M8   Design patterns
[ ] M9a  LLD: method, Parking Lot, LRU Cache, Splitwise
[ ] M9b  LLD: Snake & Ladder, Elevator, BookMyShow
[ ] Consolidation

Cross-cutting:
[ ] I can answer all 40 questions in §5 out loud in under 90 s each
[ ] I can predict the output of 30/30 drill-bank snippets
[ ] I can draw the vtable picture for a 2-class hierarchy from memory
[ ] I can design a parking lot in 45 minutes with a class diagram and core code
```

---

## Next

**Part 2: M0 — Classes and Objects.** It covers the warm-up questions that open almost every OOP round, the `this` pointer, static members, const member functions, and object memory layout (including why an empty class has size 1).

---

### Sources used for the interview-orientation section

- NextStep, *Core CS Subjects Interview Preparation Guide* (priority tables and most-asked questions)
- GoodSpace, *OOPs Interview Questions and Answers 2026*, Aug 2026
- GreatFrontEnd, *Machine Coding Interview Questions for Freshers (2026 Guide)*
- InterviewBit, *Low Level Design Interview Questions*

Frequency claims from prep platforms are directional, not precise.
