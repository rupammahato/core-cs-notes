# Operating Systems Placement Handbook — Part 7
# Module 5: Deadlocks

**Module 5 · 3 hours · Tier 1 · Requires: M4 (locks, semaphores, dining philosophers)**

---

## Why this module is high-yield

Deadlock questions follow a fixed script, and every step is predictable:

```
"What is a deadlock?"  ->  "What are the four necessary conditions?"
   ->  "How do you prevent / avoid / detect it?"  ->  "Explain Banker's algorithm"
      ->  numerical: "is this state safe? can this request be granted?"
         ->  "deadlock vs starvation vs livelock?"  ->  "how do you avoid deadlock in real code?"
```

Learn the four conditions, the four strategies and Banker's procedure cold, and this whole topic becomes reliable marks.

**The numericals in this module (Banker's safety, request handling and the detection algorithm) were computed with code, not by hand.**

The organising principle:

> **A deadlock needs four conditions at once: mutual exclusion, hold and wait, no preemption and circular wait. Every strategy is a decision about those four: prevention removes one forever, avoidance refuses requests that could lead to a cycle, detection lets the cycle form and then breaks it, and the "ostrich" approach bets it won't happen.**

---

## 5.1 What a deadlock is

### 1. Definition

A set of processes (or threads) is **deadlocked** when **each one is waiting for an event (usually the release of a resource) that only another process in the same set can cause**. None of them can ever proceed.

### 2. The minimal example: two locks taken in opposite order

```cpp
mutex A, B;
void thread1() { lock_guard<mutex> l1(A); /* ... */ lock_guard<mutex> l2(B); }   // holds A, wants B
void thread2() { lock_guard<mutex> l1(B); /* ... */ lock_guard<mutex> l2(A); }   // holds B, wants A
```

```
   thread1 --holds--> [A]          thread1 waits for B (held by thread2)
   thread2 --holds--> [B]          thread2 waits for A (held by thread1)
                                   -> cycle -> both wait forever
```

It doesn't happen on every run, only when both threads take their first lock before either takes its second. That's why deadlocks slip through testing and appear under production load.

**The real-world shape:** transferring money between two accounts, locking `from` then `to`. Transfer A→B and B→A at the same moment and you have exactly this deadlock (§5.9 shows the fix, compiled and run).

### 3. Resources (vocabulary)

- **Reusable** resources (locks, devices, memory) vs **consumable** ones (messages, signals).
- **Single-instance** (one printer) vs **multi-instance** (5 identical tape drives, N buffer slots). This distinction decides which detection method applies (§5.3, §5.7).
- Use protocol: **request → use → release**.

---

## 5.2 The four necessary conditions (Coffman conditions)

**All four must hold at the same time for a deadlock to occur.** Asked verbatim. Memorise them with an example each.

| # | Condition | Meaning | In the two-lock example |
|---|---|---|---|
| 1 | **Mutual exclusion** | At least one resource is non-shareable: only one process can use it at a time | A mutex can be held by only one thread |
| 2 | **Hold and wait** | A process holds at least one resource while waiting for another | thread1 holds A and waits for B |
| 3 | **No preemption** | Resources can't be forcibly taken away; they're released only voluntarily | You can't rip A away from thread1 |
| 4 | **Circular wait** | A cycle P₀ → P₁ → … → Pₙ → P₀ where each waits for a resource the next holds | thread1 → thread2 → thread1 |

**Precision points (they impress):**
- These are **necessary** conditions. If any one is absent, deadlock is impossible.
- For **single-instance** resources, they're also **sufficient**: a cycle means deadlock.
- Circular wait implies hold and wait, so the conditions aren't fully independent. Prevention usually targets circular wait or hold-and-wait, because those are the practical ones to break.

**Memory hook:** **M**y **H**ouse **N**eeds **C**leaning: Mutual exclusion, Hold and wait, No preemption, Circular wait.

---

## 5.3 Resource-allocation graphs (RAG)

### 1. Notation

```
   (P)       process (circle)
   [R ••]    resource type (box); each dot = one instance
   P ---> R  REQUEST edge: P is waiting for an instance of R
   R ---> P  ASSIGNMENT edge: an instance of R is held by P
```

### 2. Reading a RAG

| Graph | Conclusion |
|---|---|
| **No cycle** | **No deadlock** (always) |
| Cycle, and **every resource in the cycle has one instance** | **Deadlock** (cycle ⇔ deadlock) |
| Cycle, but some resource has **multiple instances** | **Possibly** a deadlock: the cycle is necessary but **not sufficient** |

### 3. The multi-instance case: a cycle without deadlock

```
        R1 [• •]                              Cycle: P1 -> R1 -> P3 -> R2 -> P1
       /  ^    \                              But:  P2 holds an instance of R1 and isn't waiting.
   holds  |  holds                                  P2 finishes and releases its R1 instance,
     v    |    v                                    P1 gets it, the cycle breaks.
   (P2)  (P1)  (P3)                           -> NOT deadlocked.
          ^ \    |
     holds|  \   | requests                   (P4 similarly holds an R2 instance and isn't waiting.)
          |   v  v
        R2 [• •] ---holds---> (P4)
```

**Rule:** with multiple instances, a cycle means "check further". Use the detection algorithm (§5.7).

### 4. Wait-for graph (single-instance resources)

Collapse the resource nodes: draw **Pᵢ → Pⱼ** if Pᵢ waits for a resource that Pⱼ holds. **Deadlock ⇔ a cycle in the wait-for graph.** Detecting it is **directed-graph cycle detection** with DFS and three colours (white/grey/black), the same algorithm as DSA Part 14 §12.7, in O(V + E).

---

## 5.4 The four strategies

| Strategy | Idea | Cost | Used by |
|---|---|---|---|
| **Ignore it (ostrich algorithm)** | Assume deadlocks are rare; reboot or kill when one happens | None until it happens | **Most general-purpose OSes** (Linux, Windows) for application-level deadlocks |
| **Prevention** | Design the system so that one of the four conditions **can never hold** | Lower resource utilisation, restrictions on programmers | Coding conventions (lock ordering), some embedded systems |
| **Avoidance** | Decide **per request**, using advance knowledge of maximum needs, whether granting it could lead to deadlock (**Banker's**) | Needs maximum needs in advance; runtime cost per request | Rare in general OSes; some specialised systems |
| **Detection and recovery** | Allow deadlocks, **detect** them periodically, then **recover** | Detection overhead + the cost of recovery (killed work) | **Databases** (wait-for graph, abort a victim transaction) |

**"Which does Linux use?"** For user-space locks, essentially **none**: the kernel doesn't stop your program from deadlocking its own mutexes (the ostrich approach). Inside the kernel, developers follow strict **lock-ordering rules**, and debug tools (`lockdep`) detect ordering violations. That's a strong, honest answer.

---

## 5.5 Deadlock prevention: break one condition

| Condition to break | How | Practical? | Downside |
|---|---|---|---|
| **Mutual exclusion** | Make resources shareable (read-only files, lock-free structures) or use **spooling** (a printer daemon owns the printer; processes write to a spool queue) | Only for some resources | Many resources are inherently exclusive (mutexes, write access) |
| **Hold and wait** | (a) Request **all** resources at once, before starting; or (b) request resources only when holding **none** (release everything, then re-request) | Partly (`std::scoped_lock` acquires all-or-none) | Poor utilisation (holding things before you need them); **starvation** of processes needing many popular resources |
| **No preemption** | If a request can't be granted, **release everything held** and retry later; or let the OS preempt resources from waiting processes | For resources whose state can be saved/restored (CPU registers, memory pages) | Impossible for locks mid-update or printers mid-job; livelock risk (§5.8) |
| **Circular wait** | Impose a **global total order** on resources; always request in **increasing order** | **Yes: the most practical and widely used** | Requires discipline; the order may not match the natural code flow |

**Why ordering prevents circular wait (a one-line proof):** suppose a cycle P₀ → … → Pₙ → P₀ existed. Each process waits for a resource ranked **higher** than one it holds, so the ranks strictly increase around the cycle and must return to the start, giving r₀ < r₁ < … < r₀, a contradiction.

This is exactly the **dining-philosophers resource-ordering fix** (M4 §4.10): lower-numbered fork first.

---

## 5.6 Deadlock avoidance and Banker's algorithm

### 1. Safe state

A state is **safe** if there exists **at least one order** (a **safe sequence**) in which every process can obtain its **maximum** remaining need from (currently available + resources released by processes earlier in the sequence), finish, and release everything.

```
   +---------------------------------------------+
   |  ALL STATES                                 |
   |   +---------------------+                   |
   |   |  SAFE               |   UNSAFE          |
   |   |  (never deadlock if |   +-----------+   |
   |   |   we stay here)     |   | DEADLOCK  |   |
   |   +---------------------+   +-----------+   |
   +---------------------------------------------+
```

| Statement | True? |
|---|---|
| Safe ⇒ no deadlock | **Yes** |
| Unsafe ⇒ deadlock | **No.** Unsafe means deadlock is *possible* (processes might not actually request their maximum) |
| Deadlock ⇒ unsafe | **Yes** |

**Avoidance = never grant a request that would move the system into an unsafe state.**

### 2. Banker's algorithm: data structures

For **n** processes and **m** resource types:

| Structure | Meaning |
|---|---|
| `Available[m]` | Free instances of each resource type |
| `Max[n][m]` | Maximum each process may ever request (declared in advance) |
| `Allocation[n][m]` | Currently held by each process |
| **`Need[n][m] = Max − Allocation`** | What each process may still request |

### 3. Safety algorithm

```
 Work = Available;  Finish[i] = false for all i
 repeat:
     find i with  Finish[i] == false  AND  Need[i] <= Work   (component-wise)
     if found:  Work = Work + Allocation[i]   // Pi runs to completion and releases everything
                Finish[i] = true;  append Pi to the safe sequence
 until no such i
 SAFE  iff  Finish[i] == true for all i
```

Complexity: **O(m × n²)**.

### 4. Resource-request algorithm (when Pᵢ requests vector `Request`)

```
 1. if Request > Need[i]       -> ERROR (exceeds its declared maximum)
 2. if Request > Available     -> Pi must WAIT (resources not free right now)
 3. PRETEND to grant:
        Available  -= Request
        Allocation[i] += Request
        Need[i]    -= Request
 4. run the SAFETY algorithm on the pretend state:
        safe   -> GRANT (keep the changes)
        unsafe -> DENY: roll back, Pi waits
```

### 5. Worked numerical (the classic textbook example)

5 processes, 3 resource types. **Total: A = 10, B = 5, C = 7.**

| Process | Allocation (A B C) | Max (A B C) | **Need = Max − Alloc** |
|---|---|---|---|
| P0 | 0 1 0 | 7 5 3 | **7 4 3** |
| P1 | 2 0 0 | 3 2 2 | **1 2 2** |
| P2 | 3 0 2 | 9 0 2 | **6 0 0** |
| P3 | 2 1 1 | 2 2 2 | **0 1 1** |
| P4 | 0 0 2 | 4 3 3 | **4 3 1** |

**Available** = Total − sum of Allocation = (10−7, 5−2, 7−5) = **(3, 3, 2)**

**Safety check** (scan P0 → P4 repeatedly, taking the first process that fits):

| Step | Candidate | Need ≤ Work? | Work after (Work + Alloc) |
|---|---|---|---|
| start | — | — | (3, 3, 2) |
| 1 | P0 (7,4,3) | No | — |
| | **P1** (1,2,2) | **Yes** | (3,3,2)+(2,0,0) = **(5, 3, 2)** |
| | P2 (6,0,0) | No (6 > 5) | — |
| 2 | **P3** (0,1,1) | **Yes** | (5,3,2)+(2,1,1) = **(7, 4, 3)** |
| 3 | **P4** (4,3,1) | **Yes** | (7,4,3)+(0,0,2) = **(7, 4, 5)** |
| 4 | **P0** (7,4,3) | **Yes** | (7,4,5)+(0,1,0) = **(7, 5, 5)** |
| 5 | **P2** (6,0,0) | **Yes** | (7,5,5)+(3,0,2) = **(10, 5, 7)** |

**Safe sequence: ⟨P1, P3, P4, P0, P2⟩. The state is SAFE.** (Other valid sequences exist, such as ⟨P1, P3, P4, P2, P0⟩. Any one valid sequence proves safety. The final Work always equals the Total, which is a free arithmetic check.)

**Request 1: P1 requests (1, 0, 2).**
1. ≤ Need(P1) = (1,2,2)? Yes. 2. ≤ Available (3,3,2)? Yes.
3. Pretend: Available = **(2, 3, 0)**; Alloc(P1) = (3,0,2); Need(P1) = (0,2,0).
4. Safety: P1 (0,2,0) ≤ (2,3,0) → Work (5,3,2) → P3 → (7,4,3) → P4 → (7,4,5) → P0 → (7,5,5) → P2 → (10,5,7). **Safe ⟨P1, P3, P4, P0, P2⟩ → GRANT.**

**Then (in the new state), P4 requests (3, 3, 0):** Available is (2, 3, 0), and 3 > 2 for A → **must WAIT** (step 2: not enough available).

**Then P0 requests (0, 2, 0):** ≤ Need(P0) (7,4,3) ✓; ≤ Available (2,3,0) ✓. Pretend: Available = **(2, 1, 0)**. Safety: P0 needs (7,2,3), P1 (0,2,0), P2 (6,0,0), P3 (0,1,1), P4 (4,3,1). **None fit** in (2,1,0) (P1 needs B = 2 > 1, and P3 needs C = 1 > 0). **UNSAFE → DENY**, even though the resources are physically available. This is the key insight of avoidance.

### 6. Limitations of Banker's (asked as a follow-up)

1. Processes must **declare maximum needs in advance**, which is rarely known in practice.
2. The **number of processes and resources must be fixed**.
3. **O(m·n²) per request** is too slow for a general OS.
4. It's **conservative**: it may refuse requests that wouldn't actually deadlock.
5. Processes must release everything in finite time.

That's why general-purpose OSes don't use it, and why it's mainly a teaching and interview algorithm.

**Banker's analogy:** a bank has limited cash and knows each customer's credit limit. It grants a loan only if, afterwards, it can still guarantee **some** order in which every customer could draw their full limit and repay.

---

## 5.7 Deadlock detection and recovery

### 1. Detection: single-instance resources

Maintain the **wait-for graph** and periodically run **cycle detection** (DFS, O(V + E)). A cycle means a deadlock, and the processes on the cycle are the deadlocked ones.

### 2. Detection: multi-instance resources

The same shape as Banker's safety algorithm, but using the **current requests** instead of the maximum needs, and **optimistically** assuming that processes whose requests can be satisfied will finish:

```
 Work = Available
 Finish[i] = true if Allocation[i] == 0, else false     // holding nothing -> can't be part of a deadlock
 repeat: find i with Finish[i] == false AND Request[i] <= Work
         -> Work += Allocation[i]; Finish[i] = true
 Every i with Finish[i] == false at the end is DEADLOCKED
```

**Worked example.** Resources A = 7, B = 2, C = 6. **Available = (0, 0, 0).**

| Process | Allocation | Request (current) |
|---|---|---|
| P0 | 0 1 0 | 0 0 0 |
| P1 | 2 0 0 | 2 0 2 |
| P2 | 3 0 3 | 0 0 0 |
| P3 | 2 1 1 | 1 0 0 |
| P4 | 0 0 2 | 0 0 2 |

Run: P0 (request 0) → Work (0,1,0) → P2 → (3,1,3) → P3 → (5,2,4) → P4 → (5,2,6) → P1 → (7,2,6). Everyone finishes, so **no deadlock** (sequence ⟨P0, P2, P3, P4, P1⟩).

**Now P2 requests one more C:** Request(P2) = (0, 0, 1). Run: P0 → Work (0,1,0). Nobody else fits: P2 needs C = 1 > 0, P1 needs (2,0,2), P3 needs A = 1 > 0, P4 needs C. **Deadlocked: {P1, P2, P3, P4}.** P0 can finish, but its release isn't enough to break the rest.

### 3. When to run detection

| Option | Trade-off |
|---|---|
| On **every** request that can't be granted immediately | Catches deadlock instantly and identifies the culprit; expensive |
| **Periodically** (every few minutes) or when **CPU utilisation drops** (deadlocked processes idle the CPU) | Cheaper; a deadlock may persist for a while, and the original cause is harder to pinpoint |

### 4. Recovery

**Option A: terminate processes**

| Method | Trade-off |
|---|---|
| Kill **all** deadlocked processes | Simple and certain; loses the most work |
| Kill **one at a time** until the cycle breaks | Less lost work; must re-run detection after each kill |

**Choosing the victim:** lowest priority, least CPU time used (least work lost), fewest resources held, most resources still needed, interactive vs batch, how many processes must be killed.

**Option B: preempt resources**

1. **Select a victim** (minimise cost).
2. **Rollback**: return the victim to a safe earlier state (checkpoint), or restart it entirely (total rollback).
3. **Avoid starvation**: the same process mustn't be chosen as the victim every time. Include the **number of rollbacks** in the cost function.

**Databases do exactly this:** they keep a wait-for graph of transactions waiting for locks; on a cycle they **abort one transaction** (the victim, with an error like "deadlock detected", e.g. SQL Server's error 1205), roll it back, and the application retries.

---

## 5.8 Deadlock vs starvation vs livelock

| | Deadlock | Starvation | Livelock |
|---|---|---|---|
| What happens | Processes are **blocked**, each waiting for another in a cycle | A process **waits indefinitely** while others proceed | Processes are **active**, constantly changing state in response to each other, but **make no progress** |
| CPU usage | None (blocked) | Others use it | **High**: busy doing useless work |
| Anyone progressing? | No one in the set | Yes, everyone except the victim | No one |
| Cause | Circular wait over held resources | Unfair scheduling or priority policy | Over-eager recovery or politeness (back off and retry in lockstep) |
| Can resolve by itself? | **Never** | Possibly (if load changes) | Possibly, by chance |
| Fix | Prevention, avoidance, detection | **Aging**, fair queues | **Randomised backoff**, priority, ordering |
| Analogy | 4 cars at a 4-way stop, each waiting for the one on its right | A person who never gets served because VIPs keep cutting in | Two people in a corridor stepping side to side to let each other pass, forever |

### Livelock in code (back-off in lockstep)

```cpp
// Each thread: take my first lock, TRY the second; if busy, release and retry
// If both threads run in perfect lockstep, they keep releasing and retrying forever.
while (true) {
    lock_guard<mutex> a(first);
    if (second.try_lock()) { /* work */ second.unlock(); break; }
    // couldn't get it: release 'first' (end of scope) and retry immediately -> livelock risk
}
// Fix: random backoff before retrying, or a global lock order (no need to back off at all)
```

**Note:** "release everything and retry" is how you break **no preemption** in prevention (§5.5), and livelock is the risk that strategy brings. Ethernet's CSMA/CD solved the same problem with **randomised exponential backoff**.

---

## 5.9 Avoiding deadlock in real code

This is what product-company interviewers mean by "how do you avoid deadlocks in practice?":

| Technique | How |
|---|---|
| **Global lock ordering** | Every code path acquires locks in one agreed order (by address, ID or level). The most important rule |
| **Acquire multiple locks atomically** | `std::scoped_lock(m1, m2, ...)` (C++17) uses a deadlock-avoidance algorithm |
| **Hold one lock at a time** | Restructure so a thread never holds a lock while acquiring another |
| **Timeouts** | `try_lock_for`, then back off (with random jitter) and retry or report |
| **Never call unknown code while holding a lock** | Callbacks, virtual functions or observers (OOP M8) may take locks in a different order |
| **Lock hierarchies with tooling** | Linux `lockdep`, ThreadSanitizer's deadlock detector, and database deadlock graphs |
| **Avoid shared mutable state** | Message passing, immutability, one owner per piece of data (no locks, no deadlock) |

### The bank-transfer fix, compiled and run

```cpp
struct Account { int id; long long balance; mutex m; };

// SAFE version 1: lock both atomically
void transfer(Account& from, Account& to, long long amt) {
    if (&from == &to) return;                 // locking the same mutex twice would deadlock
    scoped_lock lk(from.m, to.m);             // deadlock-avoiding multi-lock
    if (from.balance >= amt) { from.balance -= amt; to.balance += amt; }
}

// SAFE version 2: global lock order by account id
void transferOrdered(Account& from, Account& to, long long amt) {
    if (&from == &to) return;
    Account& first  = from.id < to.id ? from : to;
    Account& second = from.id < to.id ? to : from;
    lock_guard<mutex> l1(first.m), l2(second.m);
    if (from.balance >= amt) { from.balance -= amt; to.balance += amt; }
}

// test: two threads x 200,000 transfers in OPPOSITE directions, for each version
// -> "a=1000000 b=1000000 total=2000000"   (no deadlock; money conserved; verified)
```

The naive version (`lock_guard l1(from.m); lock_guard l2(to.m);`) deadlocks as soon as A→B and B→A run concurrently.

---

## 5.10 Consolidation

### Must remember (module)

1. Deadlock = each process in a set waits for an event only another member can cause.
2. Four conditions: **mutual exclusion, hold and wait, no preemption, circular wait**. All necessary; sufficient for single-instance resources.
3. RAG: no cycle → no deadlock; cycle + single instances → deadlock; cycle + multiple instances → maybe.
4. Wait-for graph cycle detection = DFS three-colour (DSA §12.7).
5. Strategies: ignore (most OSes), prevention, avoidance (Banker's), detection + recovery (databases).
6. Prevention: break circular wait with a **global resource order** (the practical one); hold-and-wait with all-at-once acquisition.
7. Safe ⇒ no deadlock; unsafe ⇏ deadlock; avoidance stays in safe states.
8. Banker's: **Need = Max − Allocation**; safety = repeatedly find Need ≤ Work, then Work += Allocation; request = check ≤ Need, ≤ Available, pretend, run safety.
9. Banker's limitations: maximum needs required in advance, fixed process count, O(m·n²), conservative.
10. Detection with multiple instances uses **Request** instead of Need; recovery = kill (all or one at a time) or preempt with rollback; avoid repeatedly victimising the same process.
11. Deadlock (blocked, cycle) vs starvation (one never served) vs livelock (busy, no progress).
12. In code: lock ordering, `scoped_lock`, try-lock with randomised backoff, no callbacks under locks.

### Common wrong answers (module)

- "An unsafe state is a deadlock."
- "A cycle in the resource-allocation graph always means deadlock." (Only with single instances.)
- "Deadlock and starvation are the same."
- "Linux uses Banker's algorithm."
- "Prevention and avoidance are the same thing." (Static design rule vs dynamic per-request check.)
- Computing Need as Max + Allocation, or forgetting that Work grows by the **Allocation** (not the Need) of a finished process.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is a deadlock? | Processes waiting in a cycle for resources held by each other | Example? (Two locks taken in opposite order) |
| Four necessary conditions? | Mutual exclusion, hold and wait, no preemption, circular wait | Which is easiest to break in practice? (Circular wait, by ordering) |
| Prevention vs avoidance? | Design-time removal of a condition vs runtime check that keeps the system safe | Example of each? |
| Explain Banker's algorithm | Need = Max − Alloc; grant only if a safe sequence still exists | Walk through a numerical |
| Safe vs unsafe state? | A safe sequence exists vs not; unsafe ≠ deadlocked | |
| How to detect a deadlock? | Wait-for graph cycle (single instance) / detection algorithm (multi-instance) | How often to run it? |
| How to recover? | Kill processes (all / one by one) or preempt with rollback | Victim selection? |
| Deadlock vs starvation vs livelock? | Blocked cycle vs one never served vs busy without progress | Fix for livelock? (Randomised backoff) |
| How do you avoid deadlocks in your code? | Lock ordering, `scoped_lock`, timeouts, no callbacks under locks | Bank-transfer example |
| What does Linux do about deadlocks? | Ignores them for user locks (ostrich); lock ordering + `lockdep` inside the kernel | |

### Practice numericals

**N1.** Total: A = 9, B = 3, C = 6. Four processes:

| Process | Allocation | Max |
|---|---|---|
| P1 | 1 0 0 | 3 2 2 |
| P2 | 6 1 2 | 6 1 3 |
| P3 | 2 1 1 | 3 1 4 |
| P4 | 0 0 2 | 4 2 2 |

(a) Compute Need and Available. (b) Is the state safe? (c) Can P2's request (0,0,1) be granted? (d) Starting again from the original state, can P4's request (0,1,0) be granted? (e) And P1's request (0,1,1)?

<details><summary>Answer</summary>

(a) Need: P1 (2,2,2), P2 (0,0,1), P3 (1,0,3), P4 (4,2,0). Available = (9−9, 3−2, 6−5) = **(0, 1, 1)**.

(b) P2 (0,0,1) ≤ (0,1,1) → Work (6,2,3) → P3 (1,0,3) ≤ (6,2,3) → (8,3,4) → P4 (4,2,0) → (8,3,6) → P1 (2,2,2) → (9,3,6). **Safe: ⟨P2, P3, P4, P1⟩.**

(c) (0,0,1) ≤ Need (0,0,1) ✓, ≤ Available ✓. Pretend Available = (0,1,0); P2's Need becomes (0,0,0), so P2 can finish → same safe sequence. **Grant.**

(d) (0,1,0) ≤ Need P4 (4,2,0) ✓, ≤ Available ✓. Pretend Available = (0,0,1); P2 (0,0,1) fits → (6,1,3) → P3 → (8,2,4) → P4 (now needs 4,1,0) → (8,3,6) → P1 → (9,3,6). **Safe → Grant.**

(e) (0,1,1) ≤ Need P1 (2,2,2) ✓, ≤ Available (0,1,1) ✓. Pretend Available = **(0,0,0)**. Nobody's Need is (0,0,0) → **unsafe → Deny.**
</details>

**N2.** (a) A system has 3 identical printers, and 4 processes each need at most 2 printers. Can deadlock occur? (b) What if there are 3 processes and 4 printers? (c) What is the minimum number of printers that guarantees no deadlock for 4 processes needing at most 2 each?

<details><summary>Answer</summary>

**The rule:** with **n** processes, each needing at most **k** instances, deadlock is impossible if and only if **R ≥ n(k − 1) + 1**. Worst case: every process holds k − 1 instances and waits for one more. If even one instance is still free at that point, some process can finish and release its instances, and the others follow.

(a) **Yes, deadlock can occur.** Three of the processes each take 1 printer, which uses all 3, and each then waits for a second. No printer is free, so they wait forever. Check against the rule: 4(2 − 1) + 1 = 5 > 3.

(b) **No.** In the worst case each of the 3 processes holds 1 printer, which uses 3 of the 4. The 4th printer lets one process finish and release its two printers, and the rest follow. Rule: 3(2 − 1) + 1 = 4 ≤ 4.

(c) **5** printers: 4(2 − 1) + 1.
</details>

**N3.** Single-instance resources. Wait-for edges: P1→P2, P2→P3, P3→P4, P4→P2, P5→P1. Which processes are deadlocked?

<details><summary>Answer</summary>

Cycle **P2 → P3 → P4 → P2** → **P2, P3, P4 are deadlocked.** P1 and P5 aren't on the cycle but are **blocked forever** behind it (P1 waits for P2; P5 waits for P1). Many textbooks count them as affected, or "deadlocked" in the broad sense. Say both precisely.
</details>

**N4.** Which deadlock condition does each technique break? (a) Spooling printer output. (b) Acquiring all locks with `scoped_lock`. (c) Always locking accounts in increasing ID order. (d) If a lock isn't available, releasing everything and retrying.

<details><summary>Answer</summary>

(a) Mutual exclusion (the device is effectively shared via the spool). (b) Hold and wait (all-or-none). (c) Circular wait. (d) No preemption (voluntary self-preemption), at the risk of livelock.
</details>

---

## Exit checklist

```
[ ] I can define deadlock and give the two-lock / bank-transfer example
[ ] I can state the 4 Coffman conditions with an example each, and know "necessary" vs "sufficient"
[ ] I can read a RAG and know the single- vs multi-instance cycle rule
[ ] I can compare the 4 strategies and say what Linux and databases actually do
[ ] I can explain how each prevention technique breaks a condition, and prove why ordering works
[ ] I can distinguish safe / unsafe / deadlocked states
[ ] I can run Banker's safety algorithm and request algorithm on paper without errors
[ ] I can list Banker's limitations
[ ] I can run the multi-instance detection algorithm and name recovery options and victim criteria
[ ] I can compare deadlock vs starvation vs livelock with analogies
[ ] I can write deadlock-free multi-lock code (scoped_lock / ordering)
[ ] N1–N4 done
```

---

## Next

**Part 8: M6 — Memory Management.** It covers logical vs physical addresses and the MMU, contiguous allocation (first/best/worst fit), internal vs external fragmentation, paging and page tables (with address-translation numericals), the TLB and **effective-access-time numericals**, multi-level and inverted page tables, segmentation, and paging vs segmentation.
