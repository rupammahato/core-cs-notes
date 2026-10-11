# Operating Systems Placement Handbook — Part 1: Master Roadmap

*Your roadmap for the OS portion of technical interviews: what to learn, in what order, how deep, which numericals to practise, and which interview questions each module answers. Later parts teach each module in full.*

---

## 0. How this handbook is built

This is the third handbook, after DSA and OOP, and it uses the same structure: Part 1 is the roadmap, and each later part is one module.

**This handbook is for interviews, not for GATE or university exams.** That decides the depth:

- **Concepts and trade-offs come first.** Most OS interview questions are "explain", "what's the difference", and "what happens when". These are covered in full.
- **Numericals only where interviews use them:** CPU scheduling (Gantt charts), page replacement, Banker's algorithm, effective access time with a TLB, and disk scheduling. GATE-style arithmetic puzzles (multi-level page-table sizing with odd parameters, and so on) are marked Tier 3.
- **Concurrency code you can actually write.** Product companies increasingly ask candidates to *code* synchronization: odd/even printing with two threads, producer-consumer, a thread-safe queue. All such code is in C++ (`std::thread`, `std::mutex`, `std::condition_variable`), matching the DSA and OOP handbooks.
- **POSIX system calls in C** (`fork`, `exec`, `wait`, `pipe`), because that's what interviewers write on the board.

### Note format

Same as the OOP handbook, plus a **numerical** slot:

1. **What is it?**
2. **Why does it exist?**
3. **Core idea** (diagram)
4. **How it works** (mechanism step by step; code where relevant)
5. **Worked example / numerical**
6. **Comparison** with its confusable neighbour
7. **Must remember**
8. **Common wrong answers**
9. **Interview questions** (question → crisp answer → likely follow-up)
10. **Practice**

### How code was verified

- C++ threading code was compiled and run (g++ 12, `-std=c++17 -pthread`), and outputs shown are from real runs. Where output is nondeterministic (races), the notes say so and show sample runs.
- `fork()` process-count answers were checked with a small simulator that enumerates every process as its unique sequence of fork results. The POSIX `fork`/`exec`/`pipe` programs themselves are standard textbook code that couldn't be executed on this Windows machine, so they're written carefully against the POSIX specification.

---

## 1. The master syllabus

13 parts.

| Part | Module | Hours | Tier | Answers questions like |
|---|---|---|---|---|
| 1 | Master roadmap | — | — | — |
| 2 | **M0** OS fundamentals | 2 | 1 | What is a kernel? User vs kernel mode? What is a system call? |
| 3 | **M1** Processes | 3–4 | 1 | Process states, PCB, context switch, fork output, zombie vs orphan |
| 4 | **M2** Threads | 2 | 1 | Process vs thread (the top OS question), user vs kernel threads |
| 5 | **M3** CPU scheduling | 4 | 1 | FCFS/SJF/RR/priority with Gantt charts, starvation, convoy effect |
| 6 | **M4** Synchronization | 5–6 | 1 | Race condition, mutex vs semaphore, producer-consumer, coding drills |
| 7 | **M5** Deadlocks | 3 | 1 | Four conditions, Banker's algorithm, deadlock vs starvation |
| 8 | **M6** Memory management | 4 | 1 | Paging vs segmentation, fragmentation, TLB, effective access time |
| 9 | **M7** Virtual memory | 3–4 | 1 | Page fault steps, FIFO/LRU/Optimal, Belady's anomaly, thrashing |
| 10 | **M8** Storage and file systems | 3 | 2 | Inodes, hard vs soft links, disk scheduling, RAID |
| 11 | **M9** IPC and I/O | 2 | 2 | Pipes vs shared memory vs sockets, DMA, buffering vs spooling |
| 12 | **M10** Putting it together | 1.5–2 | 2/3 | "What happens when you run a program?", containers vs VMs |
| 13 | **Consolidation** | 2 | — | Numericals formula sheet, confusable pairs, rapid-fire Q&A |

**Total: about 32–36 hours.** Tier 1 alone (M0–M7) is about 26–29 hours.

---

## 2. Dependency map

```
                 [M0] OS fundamentals
                          |
                 [M1] Processes
                          |
                 [M2] Threads
                          |
          +---------------+----------------+
          |                                |
 [M3] CPU scheduling             [M4] Synchronization      <- the centrepiece
          |                                |
          |                         [M5] Deadlocks
          |                                |
          +---------------+----------------+
                          |
                 [M6] Memory management
                          |
                 [M7] Virtual memory
                          |
          +---------------+----------------+
          |                                |
 [M8] Storage & file systems      [M9] IPC & I/O
          |                                |
          +---------------+----------------+
                          |
                 [M10] Putting it together
                          |
                 [Consolidation]
```

M8 and M9 can be read any time after M1. M3 and M4 can be done in either order.

### The dependencies that actually bite

| To learn | You genuinely need | Why |
|---|---|---|
| Context switch | Process states + PCB | A context switch *is* saving one PCB and loading another |
| Thread vs process | Process memory layout | The answer is "which parts of the layout are shared" |
| Preemptive scheduling | Interrupts (timer) | Preemption is the timer interrupt taking the CPU back |
| Race conditions | Threads sharing memory | No shared memory, no race |
| Semaphores | Critical-section requirements | Semaphores are one solution to that problem |
| Deadlock | Locks and semaphores | Deadlock is what happens when locking goes wrong |
| Banker's algorithm | Deadlock conditions + resource allocation | It avoids the circular-wait outcome by simulation |
| Virtual memory | Paging | Demand paging = paging + "not all pages are in RAM" |
| Page replacement | Page faults | Replacement happens only on a fault with no free frame |
| Thrashing | Page replacement + multiprogramming | Too many processes for the frames, so constant faults |
| Copy-on-write | `fork` + paging | COW is why `fork` is cheap |
| "What happens when you run a program" | Everything | The integrative question |

---

## 3. Priority tiers

### Tier 1 — must master

| Topic | Why |
|---|---|
| Process vs thread | The single most-asked OS question |
| Process states + PCB + context switch | Standard, with a diagram |
| `fork()` semantics and output counting | Common in written tests and interviews |
| Zombie vs orphan | Short, frequent |
| CPU scheduling algorithms with Gantt-chart numericals | Asked conceptually everywhere and numerically in tests |
| Race condition, critical section, mutex vs semaphore | The most-asked synchronization questions |
| Producer-consumer (concept **and** code) | The classic; product companies may ask for code |
| Deadlock: 4 conditions, prevention vs avoidance vs detection | Always asked |
| Banker's algorithm (safe sequence numerical) | Frequently asked as a numerical |
| Paging vs segmentation, fragmentation | Standard comparison |
| Virtual memory and the page-fault sequence | Standard, and the basis for "what happens when" |
| Page replacement (FIFO, LRU, Optimal) + Belady's anomaly | Numerical + concept |
| Thrashing | Frequent short question |
| TLB + effective access time | Common numerical at product companies |
| User mode vs kernel mode, system calls | Fundamentals |

### Tier 2 — high priority at product companies

| Topic | Why |
|---|---|
| Concurrency coding drills (odd/even, bounded queue, readers-writers) | Product companies test whether you can write correct concurrent code |
| Spinlock vs mutex, condition variables, monitors | Deeper synchronization questions |
| Dining philosophers, readers-writers | Classic problems |
| Copy-on-write, `exec`, `wait` | Follow-ups to `fork` |
| User vs kernel threads, threading models | Follow-ups to process vs thread |
| Multilevel feedback queue | "How do real schedulers work?" |
| Inodes, hard vs soft links | Linux-flavoured questions |
| Disk scheduling (SCAN, C-SCAN, LOOK) | Numericals in some tests |
| IPC mechanisms | Pipes, shared memory, message queues, sockets |
| "What happens when you run a program / type a command" | The integrative question |

### Tier 3 — good to know

| Topic | Why |
|---|---|
| Peterson's solution, test-and-set, CAS internals | Theory depth; occasionally asked |
| Multi-level and inverted page tables | Conceptual questions |
| RAID levels | Occasionally asked |
| Linux CFS scheduler | "Do you know how Linux actually schedules?" |
| Containers vs VMs, hypervisors | Increasingly asked in passing |
| File allocation methods | Mostly exams |
| Kernel architecture details (microkernel internals) | Rare |

### Tier 4 — skip for placements

GATE-style page-table arithmetic puzzles, detailed I/O subsystem internals, real-time scheduling theory (rate-monotonic proofs), distributed OS algorithms, kernel programming.

**If you have under two weeks:** M1, M2, M3, M4 (concepts + producer-consumer), M5, M6, M7, then the Consolidation part. That covers the large majority of OS interview questions.

---

## 4. Interview orientation (what the research says)

**The core list is very stable across sources.** 2026 preparation guides converge on the same high-priority topics: process management (process vs thread, states, PCB, context switching), CPU scheduling (FCFS, SJF, Round Robin, Priority, multilevel queues), process synchronization (critical section, semaphores, mutex, monitors, deadlock) and memory management (paging, segmentation, virtual memory, page replacement), with file systems, disk scheduling and system calls (`fork`, `exec`, `wait`) at medium priority. The most-asked individual questions are process vs thread, process states, the deadlock conditions, Banker's algorithm, paging vs segmentation, virtual memory, scheduling algorithms, thrashing, binary vs counting semaphores, and producer-consumer ([NextStep core-CS guide](https://gs.dnextstep.in/guides/core-cs-subjects-guide); [GeeksforGeeks OS interview questions](https://www.geeksforgeeks.org/operating-systems/operating-systems-interview-questions/); [InterviewBit, 2026](https://www.interviewbit.com/operating-system-interview-questions/)).

**How OS is asked differs by company type.** Service companies tend to ask definitions and differences. Product companies (the same NextStep guide lists Google, Microsoft, Amazon, Flipkart and Paytm) chain questions into mechanisms ("what exactly happens on a page fault?"), use numericals in written rounds, and increasingly ask you to **write** small concurrent programs. Candidates report OS and DBMS questions mixed into DSA rounds rather than asked in a separate round, so expect a 10–15 minute core-CS segment inside a technical interview.

**Three practical points:**

1. **Every answer needs a mechanism or an example.** "A semaphore is a synchronization tool" is half an answer. "A semaphore is an integer with atomic wait and signal; a counting semaphore initialised to 3 lets at most 3 threads use a pool of 3 database connections" is a full one.
2. **Numericals are about method, not arithmetic.** Interviewers watch whether you draw the Gantt chart, track the reference string correctly and state the formula. Practise the layout until it's mechanical.
3. **Interviewers chain questions.** "What is virtual memory?" leads to "how is an address translated?", then "what's a TLB?", then "what happens on a TLB miss?", then "and if the page isn't in memory?". Every module lists the likely follow-up chain.

Frequency claims from preparation sites are self-reported and directional.

---

## 5. Question map

The 45 most frequent OS questions, and where each is answered.

| # | Question | Module |
|---|---|---|
| 1 | What is an OS? What are its functions? | M0 |
| 2 | What is a kernel? Monolithic vs microkernel | M0 |
| 3 | User mode vs kernel mode | M0 |
| 4 | What is a system call? How does it work? | M0 |
| 5 | Interrupt vs trap (exception) | M0 |
| 6 | What happens when a computer boots? | M0 |
| 7 | Program vs process | M1 |
| 8 | Process memory layout | M1 |
| 9 | What is a PCB? | M1 |
| 10 | Process states and transitions | M1 |
| 11 | What is a context switch? Why is it expensive? | M1 |
| 12 | What does `fork()` return? How many times is "hello" printed? | M1 |
| 13 | `fork` vs `exec` | M1 |
| 14 | Zombie vs orphan process | M1 |
| 15 | Process vs thread | M2 |
| 16 | What do threads share? | M2 |
| 17 | User-level vs kernel-level threads | M2 |
| 18 | Concurrency vs parallelism | M2 |
| 19 | Preemptive vs non-preemptive scheduling | M3 |
| 20 | Scheduling criteria (TAT, WT, RT) | M3 |
| 21 | FCFS, SJF, SRTF, Priority, RR with Gantt charts | M3 |
| 22 | Starvation and aging | M3 |
| 23 | Convoy effect | M3 |
| 24 | How do you choose the time quantum in RR? | M3 |
| 25 | Race condition, critical section | M4 |
| 26 | Requirements of a critical-section solution | M4 |
| 27 | Mutex vs semaphore | M4 |
| 28 | Binary vs counting semaphore | M4 |
| 29 | Spinlock vs mutex | M4 |
| 30 | Producer-consumer problem (with code) | M4 |
| 31 | Readers-writers, dining philosophers | M4 |
| 32 | What is deadlock? The four conditions | M5 |
| 33 | Deadlock prevention vs avoidance vs detection | M5 |
| 34 | Banker's algorithm | M5 |
| 35 | Deadlock vs starvation vs livelock | M5 |
| 36 | Logical vs physical address | M6 |
| 37 | Internal vs external fragmentation | M6 |
| 38 | Paging vs segmentation | M6 |
| 39 | What is a TLB? Effective access time | M6 |
| 40 | What is virtual memory? | M7 |
| 41 | What happens on a page fault? | M7 |
| 42 | Page replacement algorithms; Belady's anomaly | M7 |
| 43 | What is thrashing? How to prevent it? | M7 |
| 44 | Hard link vs soft link; what is an inode? | M8 |
| 45 | What happens when you run a program? | M10 |

---

## 6. Numericals you must be able to do

| Numerical | Module | Formula / method to memorise |
|---|---|---|
| Scheduling: average waiting / turnaround time | M3 | TAT = CT − AT; WT = TAT − BT; RT = first run − AT |
| Banker's safe sequence | M5 | Need = Max − Allocation; repeatedly find a process with Need ≤ Work |
| Effective access time with TLB | M6 | EAT = h(t + m) + (1 − h)(t + 2m) for one-level paging |
| Page-table size / address split | M6 | offset bits = log₂(page size); page number bits = address bits − offset bits |
| Page faults for FIFO / LRU / Optimal | M7 | Track frames step by step; count misses |
| Effective access time with page faults | M7 | EAT = (1 − p) × mem + p × fault service time |
| Disk scheduling total head movement | M8 | Sum of absolute differences along the service order |

All formulas are collected in one sheet in the Consolidation part.

---

## 7. Schedules

Hours are OS only, alongside DSA and OOP.

### 2 weeks (~1 h/day, ~14 h)

| Days | Focus |
|---|---|
| 1 | M0 (skim) + M1 |
| 2 | M1 (fork drills) + M2 |
| 3–4 | M3 (do all the numericals) |
| 5–7 | M4 (concepts + producer-consumer code) |
| 8 | M5 (Banker's numerical) |
| 9–10 | M6 |
| 11–12 | M7 |
| 13–14 | Consolidation: formula sheet + rapid-fire Q&A |

Skip: M8–M10 (read only their Q&A tables).

### 1 month (~1 h/day, ~28 h)

| Week | Modules |
|---|---|
| 1 | M0, M1, M2 |
| 2 | M3, M4 |
| 3 | M4 (coding drills), M5, M6 |
| 4 | M7, M8 (links + disk scheduling), Consolidation |

### 2–3 months (~1 h on alternate days, alongside OOP) — recommended

All 13 parts in order. Type and run every C++ concurrency program; deliberately break it (remove a lock) and watch it fail.

### Revision passes

| Pass | What you do | When |
|---|---|---|
| 1 | Read the module, draw every diagram yourself | During the module |
| 2 | Answer the module's Q&A out loud, timed (60–90 s each) | End of the module |
| 3 | Redo every numerical on paper without notes | Weekly after M3 |
| 4 | Explain "what happens when you run a program" end to end, in 3 minutes | Final two weeks |
| 5 | Formula sheet + confusable pairs + rapid-fire only | Last 2–3 days |

---

## 8. Rules I will follow in every module

1. Mechanism before definition. Explain *how* it works, not just what it's called.
2. Every concept gets an ASCII diagram where there is a structure or timeline to see.
3. Every "difference between" gets a comparison table.
4. Numericals are worked step by step with a fixed layout you can reuse.
5. Concurrency code is C++17, compiled and run; nondeterministic results are labelled.
6. Linux is the reference system; Windows equivalents get a one-line note where commonly asked.
7. Numbers that vary by hardware (context-switch cost, page sizes, latencies) are given as typical orders of magnitude, labelled as such.
8. "Must remember" lists only non-obvious facts.
9. "Common wrong answers" covers what candidates actually say that loses marks.
10. Q&A answers fit in under a minute, with the likely follow-up.

---

## 9. Progress checklist

```
[ ] M0   OS fundamentals
[ ] M1   Processes
[ ] M2   Threads
[ ] M3   CPU scheduling
[ ] M4   Synchronization
[ ] M5   Deadlocks
[ ] M6   Memory management
[ ] M7   Virtual memory
[ ] M8   Storage and file systems
[ ] M9   IPC and I/O
[ ] M10  Putting it together
[ ] Consolidation

Cross-cutting:
[ ] I can answer all 45 questions in §5 out loud in under 90 s each
[ ] I can do every numerical type in §6 on paper without notes
[ ] I can write producer-consumer with mutex + condition_variable from memory
[ ] I can explain "what happens when you run ./a.out" end to end in 3 minutes
```

---

## Next

**Part 2: M0 — OS Fundamentals.** It covers what an OS does, user vs kernel mode, how a system call actually works (and why it costs more than a function call), interrupts vs traps, kernel architectures, the types of OS, and the boot sequence.

---

### Sources used for the interview-orientation section

- NextStep, *Core CS Subjects Interview Preparation Guide* (OS priority table and most-asked questions)
- GeeksforGeeks, *Operating System Interview Questions*
- InterviewBit, *70+ Operating System Interview Questions (2026)*

Frequency data from preparation platforms is directional, not precise.
