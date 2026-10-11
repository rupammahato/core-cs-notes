# Operating Systems Placement Handbook — Part 5
# Module 3: CPU Scheduling

**Module 3 · 4 hours · Tier 1 · Requires: M1 (states, context switch), M0 (timer interrupt)**

---

## Why this module is numerical-heavy

Scheduling is asked two ways:

1. **Conceptually** in interviews: "compare FCFS and Round Robin", "what is starvation?", "how do you choose the time quantum?", "what's the convoy effect?".
2. **Numerically** in written tests and OAs: "given these arrival and burst times, draw the Gantt chart and find the average waiting time".

Both are mechanical once you have a fixed method. This module gives you one layout, uses **one process set for every algorithm** (so the comparisons are direct), and states the tie-breaking conventions explicitly, since that's where most numerical mistakes come from.

**Every Gantt chart and average in this module was computed by a simulator** that implements each algorithm with the conventions stated below.

The organising principle:

> **Every scheduling algorithm is an answer to one question: when the CPU becomes free, or a process arrives, which ready process should run? FCFS answers "the oldest", SJF "the shortest", Priority "the most important", Round Robin "the next one in line, for a fixed slice". Each answer optimises one metric and pays for it with another.**

---

## 3.1 Basic concepts

### 1. CPU–I/O burst cycle

Processes alternate between **CPU bursts** (computing) and **I/O bursts** (waiting for a device). Most CPU bursts are short; a few are long. I/O-bound processes have many short bursts; CPU-bound processes have few long ones (M1 §1.1). Scheduling exists because the CPU sits idle during I/O unless another process is ready to use it.

### 2. When scheduling decisions happen

1. A process switches from **Running → Waiting** (I/O request, `wait()`)
2. A process switches from **Running → Ready** (timer interrupt)
3. A process switches from **Waiting → Ready** (I/O completion)
4. A process **terminates**

### 3. Preemptive vs non-preemptive

| | Non-preemptive (cooperative) | Preemptive |
|---|---|---|
| The CPU is taken away when... | **Only** when the process blocks or terminates (cases 1 and 4) | Also on a timer interrupt or when a better process arrives (cases 2 and 3) |
| Needs a timer interrupt | No | **Yes** |
| Responsiveness | Poor: one long process blocks everyone | Good |
| Overhead | Fewer context switches | More context switches |
| Synchronization concern | Lower (a process can't be interrupted mid-update in user code) | **Race conditions** on shared data (M4) |
| Algorithms | FCFS, SJF, non-preemptive Priority | SRTF, preemptive Priority, Round Robin, MLFQ |

All modern general-purpose OSes are preemptive.

### 4. The dispatcher

The module that actually hands the CPU to the chosen process: context switch, switch to user mode, jump to the right instruction. **Dispatch latency** is the time it takes, which is pure overhead.

---

## 3.2 Scheduling criteria and formulas

| Criterion | Definition | Goal |
|---|---|---|
| **CPU utilisation** | % of time the CPU is busy | Maximise |
| **Throughput** | Processes completed per unit time | Maximise |
| **Turnaround time (TAT)** | Submission to completion | Minimise |
| **Waiting time (WT)** | Total time spent **in the ready queue** | Minimise |
| **Response time (RT)** | Submission to **first** time on the CPU | Minimise (interactive systems) |

### The formulas (memorise exactly)

```
Completion Time  (CT)  = when the process finishes (read from the Gantt chart)
Turnaround Time  (TAT) = CT - AT                       (AT = arrival time)
Waiting Time     (WT)  = TAT - BT                      (BT = burst time)
Response Time    (RT)  = (first time on CPU) - AT

Averages: sum over all processes / number of processes
```

`WT = TAT − BT` works for every algorithm (with no I/O inside the burst), because the only time a process spends in the system without running is time spent waiting.

### The method (use the same layout every time)

1. Draw a **time axis** and fill the **Gantt chart** step by step, re-deciding at every arrival and every completion (and every slice end for RR).
2. Read the **CT** of each process off the chart.
3. Fill a table: **AT, BT, CT, TAT, WT, RT**.
4. Average.

---

## 3.3 The process set used throughout

| Process | Arrival (AT) | Burst (BT) |
|---|---|---|
| P1 | 0 | 8 |
| P2 | 1 | 4 |
| P3 | 2 | 9 |
| P4 | 3 | 5 |

**Tie-breaking conventions** (state them in a written answer if the question doesn't):
- If two processes tie on the scheduling key, the one that **arrived first** wins; then the lower process number.
- In Round Robin, a process **arriving at the same instant** that another's slice ends is placed in the queue **before** the preempted process. (Some textbooks use the opposite convention. Both are accepted if stated.)

---

## 3.4 FCFS: First Come, First Served

### 1. Rule

Run processes **in order of arrival**, each to completion. Non-preemptive; a simple FIFO queue.

### 2. Worked example

```
Gantt:  | P1      | P2   | P3        | P4    |
        0         8      12          21      26
```

| Process | AT | BT | CT | TAT = CT−AT | WT = TAT−BT | RT |
|---|---|---|---|---|---|---|
| P1 | 0 | 8 | 8 | 8 | 0 | 0 |
| P2 | 1 | 4 | 12 | 11 | 7 | 7 |
| P3 | 2 | 9 | 21 | 19 | 10 | 10 |
| P4 | 3 | 5 | 26 | 23 | 18 | 18 |
| **Average** | | | | **15.25** | **8.75** | **8.75** |

### 3. The convoy effect

When a **long CPU-bound** process runs first, every short process behind it waits, like cars stuck behind a slow truck. The I/O devices also sit idle, because the I/O-bound processes can't get the CPU long enough to issue their next I/O request.

```
All arrive at 0.  P1 = 24, P2 = 3, P3 = 3

Long first:   | P1 (24)                  | P2 | P3 |    WT = 0, 24, 27 -> avg 17
              0                          24   27   30

Short first:  | P2 | P3 | P1 (24)                  |    WT = 0, 3, 6   -> avg 3
              0    3    6                          30
```

**Same jobs, same FCFS rule, average wait 17 vs 3**, depending only on arrival order. That sensitivity is FCFS's core weakness.

### 4. Assessment

| Pros | Cons |
|---|---|
| Simplest; no starvation (everyone eventually runs) | **Convoy effect**; high average waiting time |
| Fair in the "first come" sense | Non-preemptive, so bad for interactive systems |

---

## 3.5 SJF: Shortest Job First (non-preemptive)

### 1. Rule

When the CPU is free, pick the ready process with the **smallest burst time**. It runs to completion.

### 2. Worked example

At t=0 only P1 is present, so it runs 0–8 (non-preemptive: the shorter jobs that arrive meanwhile must wait). At t=8, the ready processes are P2(4), P3(9) and P4(5); the shortest is P2. Then P4, then P3.

```
Gantt:  | P1      | P2   | P4    | P3        |
        0         8      12      17          26
```

| Process | AT | BT | CT | TAT | WT | RT |
|---|---|---|---|---|---|---|
| P1 | 0 | 8 | 8 | 8 | 0 | 0 |
| P2 | 1 | 4 | 12 | 11 | 7 | 7 |
| P3 | 2 | 9 | 26 | 24 | 15 | 15 |
| P4 | 3 | 5 | 17 | 14 | 9 | 9 |
| **Average** | | | | **14.25** | **7.75** | **7.75** |

### 3. Key facts

- **SJF is optimal for average waiting time** among non-preemptive algorithms, given the set of ready jobs (provable by an exchange argument, the same reasoning as greedy in DSA Part 13: moving a short job ahead of a long one reduces the short job's wait by more than it increases the long one's).
- **The catch: burst times aren't known in advance.** Real systems **predict** the next burst from past ones using exponential averaging:

  ```
  tau(n+1) = alpha * t(n) + (1 - alpha) * tau(n)        0 <= alpha <= 1 (commonly 0.5)
  t(n) = actual length of the most recent burst; tau(n) = previous prediction
  ```

- **Starvation:** a long job can wait forever if short jobs keep arriving.

---

## 3.6 SRTF: Shortest Remaining Time First (preemptive SJF)

### 1. Rule

At every arrival (and completion), run the process with the **smallest remaining time**. A newly arrived shorter job **preempts** the running one.

### 2. Worked example (trace every decision point)

```
t=0  : only P1 (rem 8) -> run P1
t=1  : P2 arrives (rem 4) < P1 (rem 7) -> PREEMPT, run P2
t=2  : P3 arrives (9); P2 has rem 3 -> keep P2
t=3  : P4 arrives (5); P2 has rem 2 -> keep P2
t=5  : P2 done. Ready: P1(7), P3(9), P4(5) -> run P4
t=10 : P4 done. Ready: P1(7), P3(9) -> run P1
t=17 : P1 done -> run P3
t=26 : P3 done

Gantt:  |P1| P2   | P4    | P1        | P3        |
        0  1      5       10          17          26
```

| Process | AT | BT | CT | TAT | WT | RT |
|---|---|---|---|---|---|---|
| P1 | 0 | 8 | 17 | 17 | 9 | 0 |
| P2 | 1 | 4 | 5 | 4 | 0 | 0 |
| P3 | 2 | 9 | 26 | 24 | 15 | 15 |
| P4 | 3 | 5 | 10 | 7 | 2 | 2 |
| **Average** | | | | **13.00** | **6.50** | **4.25** |

### 3. Key facts

- **SRTF gives the minimum average waiting time of all** (preemptive or not), under the same "burst times known" assumption.
- Costs: more context switches, starvation of long jobs, and remaining time must still be predicted.
- RT ≠ WT here: P1 started at 0 (RT 0) but waited 9 in total after being preempted.

---

## 3.7 Priority scheduling

### 1. Rule

Each process has a **priority**; the highest-priority ready process runs. **Convention used here: a lower number means higher priority** (as in Linux nice values and many textbooks). Always state your convention. It can be non-preemptive or preemptive.

SJF is a special case of priority scheduling (priority = predicted burst length).

### 2. Worked example (a separate process set with priorities)

| Process | AT | BT | Priority |
|---|---|---|---|
| P1 | 0 | 4 | 3 |
| P2 | 1 | 3 | 1 (highest) |
| P3 | 2 | 1 | 4 |
| P4 | 3 | 5 | 2 |
| P5 | 4 | 2 | 5 (lowest) |

**Non-preemptive:**
```
Gantt:  | P1   | P2  | P4    |P3| P5 |
        0      4     7       12 13   15
```

| Process | CT | TAT | WT |
|---|---|---|---|
| P1 | 4 | 4 | 0 |
| P2 | 7 | 6 | 3 |
| P3 | 13 | 11 | 10 |
| P4 | 12 | 9 | 4 |
| P5 | 15 | 11 | 9 |
| **Average** | | **8.20** | **5.20** |

**Preemptive:**
```
t=1: P2 (pri 1) arrives, beats P1 (pri 3) -> preempt.  t=4: P2 done; P4 (pri 2) best.
t=9: P4 done; P1 (3) beats P3 (4) and P5 (5).  Then P3, then P5.

Gantt:  |P1| P2  | P4    | P1  |P3| P5 |
        0  1     4       9     12 13   15
```

| Process | CT | TAT | WT | RT |
|---|---|---|---|---|
| P1 | 12 | 12 | 8 | 0 |
| P2 | 4 | 3 | 0 | 0 |
| P3 | 13 | 11 | 10 | 10 |
| P4 | 9 | 6 | 1 | 1 |
| P5 | 15 | 11 | 9 | 9 |
| **Average** | | **8.60** | **5.60** | **4.00** |

### 3. Starvation and aging (always asked together)

**Starvation (indefinite blocking):** a low-priority process may **never run** if higher-priority processes keep arriving. (A probably apocryphal story says that when MIT's IBM 7094 was shut down in 1973, a low-priority job submitted in 1967 still hadn't run.)

**Aging:** **gradually increase the priority of processes that wait a long time**, for example raising the priority by 1 for every 15 minutes of waiting. Eventually even the lowest-priority process becomes the highest and runs.

### 4. Priority inversion (Tier 2, a great "do you know more" answer)

A **high-priority** task waits for a lock held by a **low-priority** task, which is itself preempted by a **medium-priority** task, so the high-priority task is effectively blocked by the medium one.

```
 H: needs lock L ---- blocked, waiting for L ----------------------->
 M:                 runs (doesn't need L), preempting L ------------>
 L: holds lock L, preempted, can't release it
```

**Fix: priority inheritance.** While L holds a lock that H needs, L temporarily **inherits H's priority**, so M can't preempt it. L finishes, releases the lock, and drops back. This famously affected the **Mars Pathfinder** rover (1997), whose repeated system resets were fixed by enabling priority inheritance remotely.

---

## 3.8 Round Robin (RR)

### 1. Rule

A FIFO ready queue; each process runs for at most one **time quantum** (time slice) **q**. If it isn't finished, it's **preempted** and goes to the **back** of the queue. Designed for **time-sharing**.

### 2. Worked example, q = 2

Queue evolution (arrivals during a slice join *before* the preempted process):

```
t=0  : Q=[P1]                 run P1 0-2   (rem 6). Arrivals by t=2: P2, P3 -> Q=[P2,P3,P1]
t=2  : run P2 2-4  (rem 2). Arrival P4 -> Q=[P3,P1,P4,P2]
t=4  : run P3 4-6  (rem 7)              -> Q=[P1,P4,P2,P3]
t=6  : run P1 6-8  (rem 4)              -> Q=[P4,P2,P3,P1]
t=8  : run P4 8-10 (rem 3)              -> Q=[P2,P3,P1,P4]
t=10 : run P2 10-12 DONE                -> Q=[P3,P1,P4]
t=12 : run P3 12-14 (rem 5)             -> Q=[P1,P4,P3]
t=14 : run P1 14-16 (rem 2)             -> Q=[P4,P3,P1]
t=16 : run P4 16-18 (rem 1)             -> Q=[P3,P1,P4]
t=18 : run P3 18-20 (rem 3)             -> Q=[P1,P4,P3]
t=20 : run P1 20-22 DONE                -> Q=[P4,P3]
t=22 : run P4 22-23 DONE                -> Q=[P3]
t=23 : run P3 23-26 DONE

Gantt: |P1|P2|P3|P1|P4|P2|P3|P1|P4|P3|P1|P4|P3 |
       0  2  4  6  8  10 12 14 16 18 20 22 23  26
```

| Process | AT | BT | CT | TAT | WT | RT |
|---|---|---|---|---|---|---|
| P1 | 0 | 8 | 22 | 22 | 14 | 0 |
| P2 | 1 | 4 | 12 | 11 | 7 | 1 |
| P3 | 2 | 9 | 26 | 24 | 15 | 2 |
| P4 | 3 | 5 | 23 | 20 | 15 | 5 |
| **Average** | | | | **19.25** | **12.75** | **2.00** |

**Same set with q = 4:** Gantt `P1 0-4 | P2 4-8 | P3 8-12 | P4 12-16 | P1 16-20 | P3 20-24 | P4 24-25 | P3 25-26`, giving avg TAT 18.25, avg WT 11.75, avg RT 4.50.

### 3. Compare all algorithms on the same set

| Algorithm | Avg TAT | Avg WT | Avg RT | Comment |
|---|---|---|---|---|
| FCFS | 15.25 | 8.75 | 8.75 | Simple; convoy-prone |
| SJF (non-preemptive) | 14.25 | 7.75 | 7.75 | Better waiting |
| **SRTF** | **13.00** | **6.50** | 4.25 | Best average waiting / turnaround |
| RR, q=2 | 19.25 | 12.75 | **2.00** | **Best response time**, worst waiting |
| RR, q=4 | 18.25 | 11.75 | 4.50 | Larger q: closer to FCFS |

**This table is the interview insight:** RR has the **worst average waiting and turnaround** but the **best response time**. Optimising for interactivity (response) and for throughput or turnaround are different goals.

### 4. Choosing the time quantum (always asked)

| q too large | q too small |
|---|---|
| RR degenerates into **FCFS** (every process finishes within its slice) | **Context-switch overhead** dominates: if a switch costs 0.1 ms and q = 0.1 ms, half the CPU time is overhead |
| Poor response time | Good responsiveness, terrible efficiency |

**Rule of thumb:** q should be **large compared with the context-switch time**, and about **80% of CPU bursts should finish within one quantum**. Typical values in general-purpose systems are on the order of **10–100 ms**, while a context switch takes microseconds.

### 5. Assessment

| Pros | Cons |
|---|---|
| **No starvation**: every process gets a turn within (n−1)·q time | Higher average waiting/turnaround than SJF |
| Good response time; fair | Performance hinges on q |
| Simple | Context-switch overhead |

---

## 3.9 Multilevel Queue and Multilevel Feedback Queue

### 1. Multilevel Queue (MLQ)

The ready queue is split into **several queues by process type**, each with its own algorithm, and with **fixed** membership:

```
 highest  [ system processes      ]  -> e.g. priority
          [ interactive processes ]  -> RR, small q
          [ batch processes       ]  -> FCFS
 lowest   [ student / background  ]  -> FCFS
```

Scheduling *between* queues: **fixed priority** (a lower queue runs only if all higher queues are empty, so lower queues can starve) or **time slicing** (e.g. 80% of CPU to foreground, 20% to background).

**Limitation:** a process can't move between queues, so a misclassified process stays misclassified.

### 2. Multilevel Feedback Queue (MLFQ): what real schedulers are based on

Processes **move between queues based on their observed behaviour**:

```
 Q0: RR, q = 8 ms     <- new processes start here (highest priority)
       | used the whole quantum (looks CPU-bound) -> DEMOTE
 Q1: RR, q = 16 ms
       | used the whole quantum again -> DEMOTE
 Q2: FCFS             (lowest priority)

 - A process that BLOCKS for I/O before its quantum ends stays (it looks interactive)
 - AGING / periodic boost: processes waiting too long move UP (prevents starvation)
```

**Why it's clever:** it doesn't need to know burst times in advance. It **learns**. Short and interactive jobs finish quickly in the top queues (approximating SJF and giving good response); CPU-bound jobs sink to lower queues (good throughput); aging prevents starvation.

**Parameters that define an MLFQ:** the number of queues, the algorithm and quantum per queue, when to promote, when to demote, and which queue a new process enters.

### 3. How Linux actually schedules (one paragraph is enough)

From 2.6.23 (2007) Linux used the **Completely Fair Scheduler (CFS)**: instead of fixed time slices it tracks each task's **virtual runtime** (CPU time used, weighted by priority/nice value) and always runs the task with the **smallest vruntime**, kept in a **red-black tree** (O(log n) pick and insert). Kernel 6.6 (2023) replaced CFS with **EEVDF** (Earliest Eligible Virtual Deadline First), which keeps the fairness idea and handles latency more directly. Real-time tasks use separate `SCHED_FIFO`/`SCHED_RR` policies with strict priority. Saying "fair share via virtual runtime in a red-black tree" shows you know real systems go beyond textbook algorithms.

---

## 3.10 Multiprocessor scheduling (brief)

| Concept | Meaning |
|---|---|
| **Per-CPU run queues** | Each core has its own ready queue (avoids contention on one global queue) |
| **Processor affinity** | Keep a process on the same core so its **cache stays warm** (soft affinity = preferred; hard affinity = pinned with `sched_setaffinity`) |
| **Load balancing** | **Push** (move tasks from overloaded cores) / **pull** (idle cores steal tasks), in tension with affinity |
| **NUMA awareness** | Prefer cores near the memory the process uses |

---

## 3.11 Algorithm comparison table

| Algorithm | Preemptive? | Starvation? | Strength | Weakness | Best for |
|---|---|---|---|---|---|
| FCFS | No | No | Simple | Convoy effect, high WT | Batch |
| SJF | No | **Yes** | Optimal avg WT (non-preemptive) | Needs burst prediction | Batch with known jobs |
| SRTF | Yes | **Yes** | **Optimal avg WT overall** | Prediction, overhead, starvation | Theoretical benchmark |
| Priority | Either | **Yes** (fix: aging) | Expresses importance | Starvation, priority inversion | Real-time, OS tasks |
| Round Robin | Yes | No | **Best response time**, fair | High avg TAT/WT; q-sensitive | Time-sharing, interactive |
| MLQ | Either | Yes (fixed priority) | Different policies per class | Rigid classification | Mixed workloads with known classes |
| MLFQ | Yes | No (with aging) | Adapts without knowing bursts | Many parameters to tune | **General-purpose OSes** |

---

## 3.12 Consolidation

### Must remember (module)

1. TAT = CT − AT; WT = TAT − BT; RT = first run − AT.
2. Non-preemptive switches only on block/exit; preemptive also on timer/arrival (needs a timer interrupt).
3. FCFS: simple, **convoy effect** (avg WT 17 vs 3 depending on order).
4. SJF optimal for average WT among non-preemptive algorithms; SRTF optimal overall; both need predicted bursts (exponential averaging) and starve long jobs.
5. Priority: starvation → **aging**. Priority inversion → **priority inheritance** (Mars Pathfinder).
6. RR: best response, worst average TAT/WT; q too large → FCFS, too small → overhead; q ≫ switch time, ~80% of bursts < q.
7. MLFQ learns behaviour: demote on full quantum, keep on early block, boost to prevent starvation.
8. Linux: CFS (vruntime + red-black tree), replaced by EEVDF in 6.6.
9. **State your tie-breaking conventions** in numericals.

### Common wrong answers (module)

- "SJF has no starvation."
- "Round Robin minimises waiting time." (It optimises response time.)
- "A smaller quantum is always better."
- "WT = start time − arrival time" (true only for non-preemptive algorithms; in general WT = TAT − BT).
- "Starvation and deadlock are the same" (M5).
- Forgetting to re-check the ready queue at every arrival in SRTF and preemptive priority.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| Preemptive vs non-preemptive? | CPU taken only on block/exit vs also on timer or arrival | What makes preemption possible? (Timer interrupt) |
| What is the convoy effect? | Short jobs stuck behind a long one under FCFS | Which algorithm avoids it? |
| Why is SJF optimal, and why isn't it used directly? | Short-first minimises total waiting; bursts are unknown, so predict with exponential averaging | Formula? |
| Starvation and its fix? | Low-priority jobs never run; aging | Which algorithms starve? |
| How do you choose an RR quantum? | Large vs context-switch cost, small enough for response; ~80% of bursts fit | What if q is very large? (FCFS) |
| What is MLFQ? | Multiple queues; processes move by behaviour; approximates SJF without knowing bursts | How does it prevent starvation? |
| Priority inversion? | High waits for low, which is preempted by medium; fix: priority inheritance | Real example? (Mars Pathfinder) |
| Which algorithm gives the best response time? | Round Robin | And the best average waiting time? (SRTF) |
| How does Linux schedule? | CFS: smallest virtual runtime in a red-black tree; EEVDF since 6.6 | |

### Practice numericals (compute, then check)

**N1.** FCFS, SJF (non-preemptive), SRTF and RR (q = 2) for:

| Process | AT | BT |
|---|---|---|
| A | 0 | 3 |
| B | 2 | 6 |
| C | 4 | 4 |
| D | 6 | 5 |
| E | 8 | 2 |

<details><summary>Answers</summary>

Using this module's conventions (ties to the earlier arrival; RR arrivals queue before the preempted process):

- **FCFS:** A 0–3, B 3–9, C 9–13, D 13–18, E 18–20. WT: A 0, B 1, C 5, D 7, E 10 → **avg WT 4.6**, avg TAT 8.6.
- **SJF:** A 0–3, B 3–9; at 9 ready: C(4), D(5), E(2) → E 9–11, C 11–15, D 15–20. WT: A 0, B 1, C 7, D 9, E 1 → **avg WT 3.6**, avg TAT 7.6.
- **SRTF:** A 0–3, B 3–4 (B rem 5); at 4 C(4) < B(5) → C 4–8; at 8, B(5), D(5), E(2) → E 8–10; then B (ties with D on remaining 5; B arrived first) 10–15, D 15–20. WT: A 0, B 7, C 0, D 9, E 0 → **avg WT 3.2**, avg TAT 7.2.
- **RR q=2:** A 0–2, B 2–4, A 4–5, C 5–7, B 7–9, D 9–11, C 11–13, E 13–15, B 15–17, D 17–19, D 19–20. CT: A 5, B 17, C 13, D 20, E 15. WT: A 2, B 9, C 5, D 9, E 5 → **avg WT 6.0**, avg TAT 10.0.
</details>

**N2.** Three processes arrive at t=0 with bursts 10, 1, 2 and priorities 3, 1, 2 (lower = higher). Non-preemptive priority. Average waiting time?

<details><summary>Answer</summary>

Order: P2 (1), P3 (2), P1 (3). Gantt: P2 0–1, P3 1–3, P1 3–13. WT: P2 0, P3 1, P1 3 → **avg 1.33**.
</details>

**N3.** Predict the next CPU burst with α = 0.5, initial τ₀ = 10, and actual bursts 6, 4, 6.

<details><summary>Answer</summary>

τ₁ = 0.5·6 + 0.5·10 = 8; τ₂ = 0.5·4 + 0.5·8 = 6; τ₃ = 0.5·6 + 0.5·6 = **6**.
</details>

**N4.** With RR, a context switch costs 1 ms and q = 4 ms. What fraction of CPU time is overhead if every process uses its full quantum? What if q = 99 ms?

<details><summary>Answer</summary>

1 / (4 + 1) = **20%**. With q = 99: 1 / 100 = **1%**. That's why q must be much larger than the switch cost.
</details>

---

## Exit checklist

```
[ ] I can state TAT/WT/RT formulas and the 5 criteria
[ ] I can compare preemptive vs non-preemptive and name the algorithms in each
[ ] I can draw Gantt charts for FCFS, SJF, SRTF, Priority (both kinds) and RR without errors
[ ] I state tie-breaking conventions in written answers
[ ] I can explain the convoy effect with the 24/3/3 example
[ ] I can explain SJF optimality and burst prediction (exponential averaging)
[ ] I can explain starvation vs aging and priority inversion vs inheritance
[ ] I can discuss quantum selection with numbers
[ ] I can explain MLFQ rules and why they approximate SJF
[ ] I can describe CFS/EEVDF in two sentences
[ ] N1–N4 done
```

---

## Next

**Part 6: M4 — Synchronization.** This is the centrepiece of the OS handbook: race conditions, the critical-section problem and its three requirements, Peterson's solution, hardware atomics (test-and-set, CAS), mutex vs semaphore vs spinlock vs condition variable, monitors, the classic problems (producer-consumer, readers-writers, dining philosophers) and concurrency coding drills, all in C++, compiled and run.
