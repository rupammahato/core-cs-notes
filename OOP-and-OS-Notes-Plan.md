# Plan: OOP and Operating Systems Placement Handbooks

*Read this and approve it, or change it. No module gets written until you say so.*

---

## 0. What I learned from the DSA handbook (and will copy)

Your DSA notes follow a consistent system. Both new handbooks keep it:

| DSA handbook trait | How it carries over |
|---|---|
| **Part 1 is a roadmap with no teaching.** It covers the syllabus, dependency map, priority tiers, research-backed interview orientation, schedules, rules and a progress checklist | Each subject gets its own Part 1 roadmap in the same shape |
| **One module per file**, named `dsa-handbook-part-N-phase-X-topic.md` | `oop-handbook-part-N-module-X-topic.md` and `os-handbook-part-N-module-X-topic.md` |
| **Header line**: `Module 3 · 6–8 hours · Tier 1 · Requires: Modules 0, 1, 2` | Same |
| **An opening "why this module" section with one organising principle in a blockquote** | Same |
| **A numbered sub-format per concept** (What is it / Why / Core idea / When / Recognise / Template / Example / Complexity / Must remember / Mistakes / Practice) | Adapted for theory subjects (see §3) |
| ASCII diagrams, step-by-step trace tables, short C++ that you could write from memory | Same. OS gets many more diagrams (process states, page tables, Gantt charts) |
| Comparison tables for every confusable pair | These matter even more here, because most OOP and OS questions are phrased as "difference between X and Y" |
| "Must remember" holds only non-obvious facts, and "Common mistakes" holds real failure modes | Same. For theory, the mistakes are the wrong answers candidates give out loud |
| Consolidated must-remember, mistakes and problem set at the end, plus an exit checklist and a "Next" section | Same, plus an **interview Q&A bank** in each module |
| Cross-references such as "Module 1, Section 1.6" | Same, including links back into DSA (LRU cache, heaps, graph cycle detection) |
| Tier 4 or optional content clearly marked as skippable | Same |

One thing the DSA notes already decided affects this plan. Section A6 of the C++ module says: *"inheritance, virtual functions, polymorphism, operator overloading, copy constructors, rule of three/five, friend functions… belong to the OOP round."* The OOP handbook picks up exactly where that line stops, so there is no overlap.

---

## 1. What the research says interviewers actually ask

**OOP.** Sources agree on the core: the four pillars, constructors and destructors, access specifiers, overloading vs overriding, abstract class vs interface, virtual and pure virtual functions, and the diamond problem. **Product companies go one level deeper.** They ask about vtable/vptr internals, virtual destructors, shallow vs deep copy, composition over inheritance, association vs aggregation vs composition, SOLID, and a handful of design patterns (Singleton, Factory, Observer, Strategy). [GoodSpace, Aug 2026](https://goodspace.ai/blogs/379439/oops-interview-questions); [NextStep core-CS guide](https://gs.dnextstep.in/guides/core-cs-subjects-guide)

**Low-level design (LLD).** This is fair game for SDE-1 at Amazon and some other product companies. The usual prompts are a parking lot, Splitwise, an elevator, a rate limiter and an inventory system. The interviewer grades object modelling, entity relationships, extensibility, and how you handle a requirement that changes mid-round. Pure campus fresher rounds lean more toward DSA, so LLD is **Tier 2** in this plan, not Tier 1. [GreatFrontEnd, 2026](https://www.greatfrontend.com/blog/machine-coding-interview-questions-for-freshers-2026); [InterviewBit LLD](https://www.interviewbit.com/low-level-design-interview-questions/)

**OS.** The high-priority list is very stable across sources: process vs thread, process states and PCB, context switch, CPU scheduling (with numericals), synchronization (mutex, semaphore, critical section, producer-consumer), deadlock (the four conditions and Banker's algorithm), paging vs segmentation, virtual memory, page replacement, and thrashing. File systems, disk scheduling and system calls (`fork`/`exec`/`wait`) are medium priority. [NextStep](https://gs.dnextstep.in/guides/core-cs-subjects-guide); [GeeksforGeeks OS questions](https://www.geeksforgeeks.org/operating-systems/operating-systems-interview-questions/); [InterviewBit OS](https://www.interviewbit.com/operating-system-interview-questions/)

**What I added on top of the lists.** Product companies also ask a few things these lists underweight:
- **Concurrency you actually code.** Examples: print odd/even with two threads, a thread-safe bounded queue, and fixing a race condition in given code.
- **`fork()` output prediction.** "How many times does this print?" comes up all the time.
- **Integrative questions**, such as "what happens when you run `./a.out`?" or "what happens on a page fault?". These test whether you can connect the modules.

---

## 2. Language and scope decisions

- **C++ throughout**, to match the DSA handbook. OS concurrency code uses `std::thread`, `std::mutex` and `std::condition_variable`. `fork`/`exec` examples use POSIX C, because that is what interviewers write on the board.
- **OOP is taught as C++ OOP.** When Java behaves differently and interviewers commonly ask about it (interfaces, multiple inheritance, GC vs destructors), I add a one-line "in Java…" note. I won't write a parallel Java track.
- **The OS handbook is for interviews, not the GATE syllabus.** Numericals cover only what interviews use: scheduling Gantt charts, page replacement, Banker's, effective access time with a TLB, and disk scheduling. Topics that are mostly GATE (heavy segmentation arithmetic, multi-level page table sizing puzzles) are marked Tier 3.
- DBMS and Computer Networks are **out of scope** for this plan. The same structure can be reused for them later.

---

## 3. The note format for theory subjects

DSA concepts were algorithms, so they had templates and complexity. OOP and OS concepts are mechanisms and trade-offs, so the 11-section format becomes:

1. **What is it?** Two sentences at most.
2. **Why does it exist?** The problem it solves.
3. **Core idea**, with an ASCII diagram whenever there is a structure to show (vtable layout, process state machine, page table walk).
4. **How it works.** The mechanism step by step, with C++ code for OOP and a code or worked numerical for OS.
5. **Example / trace.** For OOP, an output-prediction example. For OS, a worked numerical or timeline.
6. **Comparison table** against its confusable neighbour(s).
7. **Must remember.** Non-obvious facts only.
8. **Common wrong answers.** Things candidates say that lose marks.
9. **Interview questions.** The question, a crisp 2–4 line answer, and the likely follow-up.
10. **Practice.** For OOP: output-prediction snippets and "fix this class" tasks. For OS: numericals and small concurrency programs.

Small topics get the compressed form, as in the DSA notes ("A3. Control flow (compressed)").

---

## 4. OOP handbook: module plan

**Folder:** `OOP Notes/` · **About 25–30 hours** · 12 files

| Part | Module | Contents | Hours | Tier |
|---|---|---|---|---|
| 1 | Master roadmap | Syllabus, dependency map, tiers, research, schedules, checklist | — | — |
| 2 | **M0 Classes and objects** | Procedural vs OOP, class vs object, `struct` vs `class`, access specifiers, `this`, `static` members, `const` member functions, object memory layout and `sizeof` (padding, empty class = 1 byte) | 2–3 | 1 |
| 3 | **M1 Constructors, destructors, copying** | Constructor types, initialiser lists (and when they're mandatory), construction/destruction order, copy constructor, shallow vs deep copy, rule of 3/5/0, move semantics (essentials only), `explicit`, RAII | 3–4 | 1 |
| 4 | **M2 Encapsulation and abstraction** | Invariants, getters/setters done right, **abstraction vs encapsulation** (the most-asked confusable), `friend` functions and classes, and why friend doesn't break encapsulation | 1.5–2 | 1 |
| 5 | **M3 Inheritance** | 5 types, the access-mode table (public/protected/private inheritance), constructor chaining, **diamond problem and virtual inheritance**, object slicing, is-a vs has-a, Java's stance on multiple inheritance | 3 | 1 |
| 6 | **M4 Polymorphism (centrepiece)** | Compile-time (function and operator overloading, templates briefly) vs runtime; `virtual`, `override`, `final`; **vtable/vptr internals with diagrams**; virtual destructor; pure virtual and abstract classes; interfaces in C++; early vs late binding; overloading vs overriding vs **hiding**; trick questions (virtual constructor? virtual call inside a constructor? default arguments on virtuals?) | 4–5 | 1 |
| 7 | **M5 Object relationships** | Association, aggregation, composition (with lifetime as the test); composition over inheritance; reading and drawing UML class diagrams (needed for LLD) | 1.5–2 | 1/2 |
| 8 | **M6 Modern C++ object model** | Smart pointers (`unique`/`shared`/`weak`) as ownership language, `static_cast` vs `dynamic_cast`, RTTI, exceptions in constructors and destructors, `mutable`, static (template) vs dynamic (virtual) polymorphism | 2–3 | 2 |
| 9 | **M7 SOLID** | Each principle as a broken C++ class, then the fix, then how to say it in one line in an interview. Also DRY, KISS, YAGNI | 2 | 2 |
| 10 | **M8 Design patterns** | Tier 2: Singleton (Meyers and thread-safe), Factory, Strategy, Observer. Tier 3: Builder, Decorator, Adapter. For each: problem, UML, C++ skeleton, real example, when *not* to use | 3–4 | 2/3 |
| 11 | **M9 LLD / machine coding** | The 5-step method (requirements → entities → relationships → class diagram → code → extend). Worked in full: **Parking Lot**, **LRU Cache** (links to DSA hashing and linked lists), **Splitwise-lite**. Prompts only: Elevator, Snake & Ladder, Rate Limiter | 4–5 | 2 |
| 12 | **Consolidation** | Cheat sheet, confusable-pairs master table, 30-snippet **output-prediction drill bank** (each snippet verified by compiling it), 63 rapid-fire Q&A, final checklist | 2 | — |

**OOP dependency chain:** M0 → M1 → M2 → M3 → M4 → M5 → (M6, M7) → M8 → M9. M6 can be skipped if time is short.

---

## 5. OS handbook: module plan

**Folder:** `OS Notes/` · **About 30–35 hours** · 13 files

| Part | Module | Contents | Hours | Tier |
|---|---|---|---|---|
| 1 | Master roadmap | Same shape as the others | — | — |
| 2 | **M0 OS fundamentals** | What an OS does, user vs kernel mode, **system calls** (and why they cost more than a function call), interrupts and traps, kernel types (monolithic, micro, hybrid), OS types (batch → multiprogramming → multitasking → real-time), booting in brief | 2 | 1 |
| 3 | **M1 Processes** | Program vs process, memory layout (text/data/heap/stack), PCB, **state diagram**, context switch (what is saved and why it is expensive), `fork`/`exec`/`wait`, **zombie vs orphan**, **fork-output prediction drills** | 3–4 | 1 |
| 4 | **M2 Threads** | **Process vs thread** (the top OS question), what threads share and what they don't, user vs kernel threads, threading models, concurrency vs parallelism, multithreading vs multiprocessing vs multitasking, `std::thread` basics | 2 | 1 |
| 5 | **M3 CPU scheduling** | Criteria and formulas (TAT, WT, RT); FCFS (convoy effect), SJF/SRTF, Priority (starvation → aging), Round Robin (choosing the quantum), MLQ/MLFQ; Gantt-chart numericals for each; a one-paragraph note on Linux CFS | 4 | 1 |
| 6 | **M4 Synchronization (centrepiece)** | Race condition, critical-section requirements, Peterson's solution, hardware support (test-and-set, CAS), **mutex vs semaphore vs spinlock vs condition variable**, monitors. Classic problems with C++ code: **producer-consumer**, readers-writers, dining philosophers. Coding drills: odd/even printer, thread-safe bounded queue, find the race | 5–6 | 1 |
| 7 | **M5 Deadlocks** | The 4 Coffman conditions, resource-allocation graph (cycle detection links to DSA graphs), prevention vs **avoidance (Banker's, with numericals)** vs detection vs recovery vs ignoring it; deadlock vs starvation vs livelock; lock ordering in real code | 3 | 1 |
| 8 | **M6 Memory management** | Logical vs physical address, MMU, contiguous allocation (first/best/worst fit), internal vs external fragmentation, **paging**, page table, **TLB and effective-access-time numericals**, multi-level and inverted page tables, segmentation, **paging vs segmentation** | 4 | 1 |
| 9 | **M7 Virtual memory** | Demand paging, **the page-fault sequence step by step**, page replacement (FIFO, OPT, LRU, with numericals), **Belady's anomaly**, **thrashing** and working set, copy-on-write (ties back to `fork`), memory-mapped files | 3–4 | 1 |
| 10 | **M8 Storage and file systems** | File allocation (contiguous, linked, indexed), inodes, directory structures, hard vs soft links, **disk scheduling** (FCFS, SSTF, SCAN, C-SCAN, LOOK, with numericals), RAID 0/1/5 in brief | 3 | 2 |
| 11 | **M9 IPC and I/O** | Pipes, shared memory, message queues, sockets, signals; shared memory vs message passing; buffering, caching and spooling; DMA; polling vs interrupts | 2 | 2 |
| 12 | **M10 Putting it together** | Integrative interview questions such as "what happens when you run a program", "what happens on `malloc`", and "why is my program slow with more threads". Virtualisation vs containers (Tier 3) | 1.5–2 | 2/3 |
| 13 | **Consolidation** | **Numericals formula sheet**, confusable-pairs master table, top-70 rapid-fire Q&A, final checklist | 2 | — |

**OS dependency chain:** M0 → M1 → M2 → (M3, M4) → M5. Then M6 → M7. M8–M9 can come any time after M1. M10 comes last.

---

## 6. Links back to your DSA handbook

| New topic | Uses this from DSA |
|---|---|
| LRU page replacement / LRU Cache LLD | Hashing (Part 5) + doubly linked list (Part 8, §6.9) |
| Deadlock detection on a resource-allocation graph | Directed cycle detection (Part 14, §12.7) |
| SJF / priority scheduling simulation | Heaps (Part 12) |
| Banker's safety algorithm | Greedy-style repeated scan (Part 13) |
| Comparators, functors, `operator<` | C++ module A6 / C4 (Part 2) |

---

## 7. Fitting this alongside DSA

| Your runway | Suggested split |
|---|---|
| **2 weeks** (triage) | OOP M0–M4 + OS M1–M7, Tier 1 only. Read the Q&A sections and do the numericals. Skip LLD and patterns |
| **1 month** | OOP M0–M5, M7, M8 (Tier 2 patterns only). All OS Tier 1 + M8. About 1 hour a day beside DSA |
| **2–3 months** (recommended) | Everything, including LLD. Alternate: OOP on even days and OS on odd days, 1 hour a day |

Each module is about 1–2 evenings. The consolidation parts are built for the final week.

---

## 8. How we'll work

1. You approve or edit this plan.
2. I write **OOP Part 1 (roadmap)** and **OS Part 1 (roadmap)**.
3. Then you say **"Start OOP M0"** / **"Start OS M0"** (or "do the next 3"), and I write modules in order. Each one is a full file of roughly 600–1200 lines, in the same depth and voice as your DSA notes.

---

## 9. Decisions (approved)

1. **Language:** C++ OOP, with the focus on concepts. Code stays short and serves the concept.
2. **LLD depth:** expanded to cover companies with machine-coding rounds. M9 is split into two files. **M9a** covers the method plus Parking Lot, LRU Cache and Splitwise. **M9b** covers Snake & Ladder, Elevator and BookMyShow. Rate Limiter remains a prompt only. The OOP handbook is now 13 files.
3. **Pace:** several modules per batch, with accuracy checked.
4. **Order:** the whole OOP handbook first, then OS.
