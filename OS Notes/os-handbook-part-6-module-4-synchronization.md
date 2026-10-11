# Operating Systems Placement Handbook — Part 6
# Module 4: Synchronization

**Module 4 · 5–6 hours · Tier 1 (concepts, producer-consumer) / Tier 2 (coding drills) · Requires: M2 (threads, the data race)**

---

## Why this is the centrepiece

Synchronization generates more OS interview questions than any other topic: race condition, critical section, mutex vs semaphore, binary vs counting semaphore, spinlock vs mutex, producer-consumer, readers-writers, dining philosophers. It's also where product companies have moved from "explain" to "**write the code**": print odd and even numbers with two threads, implement a bounded blocking queue, make this class thread-safe.

M2 ended with a broken program: two threads incrementing a shared counter lost roughly half the increments. This module is the toolkit that fixes it, from first principles (why the naive fixes fail) up to production C++.

**Every C++ program in this module was compiled (g++ 12, `-std=c++20 -O2 -pthread`) and run.** All of them produced the correct results shown. One note on tooling: the C++20 `std::counting_semaphore` in this MinGW GCC 12 build **hung** in a 100,000-item producer-consumer test, although a 1,000-item test passed. So this module teaches a **hand-written semaphore** (mutex + condition variable), which passed every test, and mentions `std::counting_semaphore` as the standard equivalent with the same `acquire`/`release` shape.

The organising principle:

> **A race condition happens when the correctness of shared-data updates depends on how threads interleave. Every synchronization tool exists to forbid the bad interleavings: mutual exclusion forbids overlapping critical sections, and signalling (semaphores, condition variables) forbids proceeding before a condition is true. Choose the tool by asking "am I protecting data, or waiting for a condition?"**

---

## 4.1 Race conditions and the critical section

### 1. Definitions

| Term | Definition |
|---|---|
| **Race condition** | The result depends on the **relative timing** (interleaving) of threads accessing shared data, with at least one writing |
| **Data race** (C++ term) | Two threads access the same memory location concurrently, at least one writes, without synchronization. **Undefined behaviour** in C++ |
| **Critical section (CS)** | The code segment that accesses shared data and must not be executed by more than one thread at a time |
| **Mutual exclusion** | At most one thread is in its critical section at any time |

### 2. The structure of every solution

```
 do {
     [ ENTRY SECTION ]     <- request permission (acquire)
       CRITICAL SECTION    <- touch shared data
     [ EXIT SECTION ]      <- release permission
       REMAINDER SECTION   <- everything else
 } while (true);
```

### 3. Recall the lost update (M2 §2.6)

`counter++` = load, add, store. Two threads interleaving those three steps lose increments. Real runs gave 1,029,738 to 1,294,530 instead of 2,000,000.

---

## 4.2 The three requirements of a critical-section solution

**Asked verbatim. Memorise all three plus the assumption.**

| Requirement | Meaning | What breaks without it |
|---|---|---|
| **1. Mutual exclusion** | If one thread is in its CS, no other thread may be in its CS | Data corruption (the race itself) |
| **2. Progress** | If no thread is in its CS and some want to enter, the choice of who enters next can't be postponed indefinitely, and only threads trying to enter take part in the decision | **Deadlock-like stalls**: the CS is free but nobody can enter |
| **3. Bounded waiting** | After a thread requests entry, there's a **bound** on how many times others can enter before it does | **Starvation** of an unlucky thread |
| *Assumption* | No assumptions about relative thread **speeds** or the number of CPUs | Solutions that work only "if thread A is fast" |

**Memory hook:** **M**utual exclusion, **P**rogress, **B**ounded waiting: "**M**y **P**rocess **B**locks".

---

## 4.3 Software solutions (and why the naive ones fail)

### 1. Attempt: a single lock flag (fails mutual exclusion)

```cpp
bool locked = false;
void enter() { while (locked) {} locked = true; }   // check-then-act RACE
void leave() { locked = false; }
```

Both threads can see `locked == false`, then both set it to true, and both enter. **The lock itself has the same race it was meant to prevent.** Checking and setting must be **one atomic step**, which is the motivation for hardware support (§4.4).

### 2. Attempt: strict alternation with `turn` (fails progress)

```cpp
int turn = 0;
// thread i:  while (turn != i) {}  /* CS */  turn = 1 - i;
```

Mutual exclusion holds, but the threads **must alternate**. If thread 0 wants to enter twice while thread 1 is busy elsewhere, thread 0 waits for a thread that isn't even trying. That violates **progress**.

### 3. Peterson's solution (2 threads, correct)

Combines **intent flags** with a **turn** variable, used as a tie-breaker:

```cpp
atomic<bool> flagP[2] = {false, false};    // flagP[i]: thread i wants to enter
atomic<int> turn{0};                        // whose turn it is when BOTH want in
int petersonCount = 0;                      // shared data

void peterson(int self, int n) {
    int other = 1 - self;
    for (int i = 0; i < n; i++) {
        flagP[self] = true;                      // ENTRY: I want to enter...
        turn = other;                            // ...but I politely let you go first
        while (flagP[other] && turn == other) {} // wait only if you want in AND it's your turn
        petersonCount++;                         // CRITICAL SECTION
        flagP[self] = false;                     // EXIT
    }
}
// two threads x 1,000,000 iterations each  ->  "peterson counter = 2000000"  (verified)
```

**Why it works (the interview explanation):**
- **Mutual exclusion:** for both to be inside, both flags must be true, and each must have seen `turn` equal to itself. But `turn` holds one value, and whichever thread wrote it **last** gave the turn away, so that thread waits.
- **Progress:** if the other thread doesn't want in (`flagP[other] == false`), you enter immediately.
- **Bounded waiting:** after the other thread leaves and tries to re-enter, it sets `turn = self` (yours), so it can't overtake you twice. The bound is one entry.

**The modern caveat (it shows depth):** with **plain `bool`/`int`** variables, Peterson's algorithm **fails on modern CPUs and compilers**. Store-load reordering lets each thread read the other's flag before its own write becomes visible. It works here only because `std::atomic` defaults to **sequentially consistent** ordering, which inserts the necessary memory barriers. It's also a **busy-wait** and handles only 2 threads (Lamport's **bakery algorithm** generalises it to n). **In practice, nobody uses Peterson's.** It's taught to show that the requirements are achievable in software, and why hardware support is used instead.

---

## 4.4 Hardware support: atomic instructions

### 1. Disabling interrupts (and why it's not the answer)

On a **single** CPU, disabling interrupts during the CS prevents preemption, so nothing can interleave. But:
- It's a **privileged** instruction (user code can't do it).
- It **doesn't work on multiprocessors**: other cores keep running.
- Long critical sections would freeze the system (timer, I/O).

The kernel uses it only for very short sections on the local core.

### 2. Atomic read-modify-write instructions

Modern CPUs provide instructions that **read and write a memory location as one indivisible step**, even across cores:

| Instruction | Semantics (done atomically) | C++ |
|---|---|---|
| **Test-and-Set (TAS)** | Set the flag to true; **return the old value** | `atomic_flag::test_and_set()` |
| **Compare-and-Swap (CAS)** | If `*addr == expected`, set `*addr = desired` and return true; else load the current value into `expected` and return false | `atomic<T>::compare_exchange_weak/strong()` |
| **Fetch-and-Add** | Add and return the old value | `atomic<int>::fetch_add()`, `++` |

### 3. A spinlock from test-and-set

```cpp
class Spinlock {
    atomic_flag f = ATOMIC_FLAG_INIT;
public:
    void lock()   { while (f.test_and_set(memory_order_acquire)) { /* spin */ } }
    void unlock() { f.clear(memory_order_release); }
};
Spinlock spin; int spinCount = 0;
void incSpin(int n) { for (int i = 0; i < n; i++) { lock_guard<Spinlock> g(spin); spinCount++; } }
// two threads x 1,000,000  ->  "spinlock counter = 2000000"  (verified)
```

`test_and_set` returns the **old** value. If it was false, the lock was free and **you** just set it, so you're in. If it was true, someone holds it, so keep spinning. Check and set happen in one indivisible step, which fixes the naive flag from §4.3.

`lock_guard<Spinlock>` works because the class provides `lock()`/`unlock()`, so RAII applies to any lockable type (OOP M1).

### 4. CAS: the basis of lock-free programming

```cpp
// lock-free "update max" (used in the semaphore test below)
int prev = maxInside.load();
while (now > prev && !maxInside.compare_exchange_weak(prev, now)) {
    // CAS failed: another thread changed it; prev now holds the fresh value; retry
}
```

**Lock-free** algorithms retry CAS loops instead of locking. A stalled thread can't block the others, but such algorithms are hard to get right (the **ABA problem**: a value changes A→B→A, and CAS can't tell). Mention lock-free as Tier 3 depth; don't write it in interviews unless asked.

### 5. Must remember

1. Checking and setting a lock must be **one atomic operation**.
2. TAS, CAS and fetch-and-add are hardware atomic read-modify-writes; C++ exposes them through `std::atomic`.
3. Disabling interrupts works only on one CPU and only in kernel mode.
4. `volatile` is **not** a synchronization tool in C++. It doesn't make operations atomic or ordered between threads; use `std::atomic`.

---

## 4.5 Mutex (lock)

### 1. What is it?

A **mutual-exclusion lock** with two operations, `lock()` (acquire) and `unlock()` (release), and **ownership**: only the thread that locked it may unlock it. If it's already locked, `lock()` **blocks**: the thread sleeps (the kernel parks it) instead of spinning.

### 2. C++ usage (the fixed counter)

```cpp
int counter = 0;
mutex counterMtx;
void incLocked(int n) {
    for (int i = 0; i < n; i++) {
        lock_guard<mutex> g(counterMtx);   // lock in constructor, unlock in destructor
        counter++;                          // critical section
    }
}
// two threads x 1,000,000  ->  "mutex counter = 2000000"  (verified)
```

| C++ tool | Use |
|---|---|
| `lock_guard<mutex>` | Simple scoped lock (RAII): the default choice |
| `unique_lock<mutex>` | Movable, can unlock early, re-lock, defer; **required by condition variables** |
| `scoped_lock<M1, M2, ...>` (C++17) | Locks **several mutexes at once without deadlock** (§4.12, M5) |
| `shared_mutex` + `shared_lock` / `unique_lock` | Readers-writer lock (§4.11) |
| `recursive_mutex` | The same thread may lock it repeatedly (usually a design smell) |
| `timed_mutex::try_lock_for` | Give up after a timeout |

**Never call `m.lock()` / `m.unlock()` by hand.** An exception or early `return` between them leaves the mutex locked forever (RAII, OOP M1 §1.15).

### 3. How a mutex works internally (one paragraph)

Modern mutexes (Linux **futex**-based) are **hybrid**: the uncontended path is a single atomic CAS **entirely in user space** (no system call). Only when the lock is contended does the thread make a system call to **sleep in the kernel**, and `unlock` wakes a waiter only if one exists. Many implementations also **spin briefly** before sleeping, in case the holder is about to release. That's why uncontended locking is cheap and contention is what's expensive.

### 4. Spinlock vs mutex

| | Spinlock | Mutex (blocking) |
|---|---|---|
| Waiting thread | **Busy-waits** (burns CPU, checking in a loop) | **Sleeps** (descheduled; the CPU does other work) |
| Context switch on contention | No | Yes (sleep and wake) |
| Best when | Critical sections are **very short**, and on **multicore** | Critical sections are longer, or may block on I/O |
| On a single core | **Wasteful**: the holder can't run while you spin (until preempted) | Fine |
| Used in | OS kernels (interrupt handlers can't sleep), short hot paths | Application code (the default) |
| Can you sleep or block while holding it? | **Never** (others spin the whole time) | Avoid, but possible |

**Interview line:** *"A spinlock busy-waits and avoids the cost of a context switch, so it's good for very short critical sections on multicore machines, especially in kernels where you can't sleep. A mutex puts waiting threads to sleep, so it suits longer sections. Spinning on a single core is pure waste, because the lock holder can't run while you spin."*

---

## 4.6 Semaphores

### 1. What is it?

A **semaphore** (Dijkstra, 1965) is an integer **S** accessed only through two atomic operations:

| Operation | Other names | Meaning |
|---|---|---|
| **wait(S)** | P (Dutch *proberen*), down, acquire | If S > 0: decrement and continue. If S == 0: **block** until it's positive, then decrement |
| **signal(S)** | V (*verhogen*), up, release, post | Increment S, and wake one blocked waiter if there is one |

### 2. Binary vs counting

| | Binary semaphore | Counting semaphore |
|---|---|---|
| Values | 0 or 1 | 0 … N |
| Typical use | Mutual exclusion, or one-shot signalling | **A pool of N identical resources** (N DB connections, N buffer slots); counting events |
| Initial value | 1 (lock) or 0 (signal) | N (resources) or 0 (events) |

### 3. The three idioms (know all three)

| Idiom | Init | Pattern |
|---|---|---|
| **Mutual exclusion** | 1 | `wait(s); CS; signal(s);` |
| **Resource pool (limit concurrency to N)** | N | `wait(s); use one resource; signal(s);` |
| **Ordering / signalling** ("B must happen after A") | **0** | Thread 1: `A; signal(s);` Thread 2: `wait(s); B;` |

### 4. Implementation: a blocking semaphore from a mutex and a condition variable

A common interview request: "implement a semaphore".

```cpp
class Semaphore {
    mutex m; condition_variable cv; int count;
public:
    explicit Semaphore(int initial) : count(initial) {}
    void wait() {                                    // P / down / acquire
        unique_lock<mutex> lk(m);
        cv.wait(lk, [&] { return count > 0; });      // sleeps; re-checks after every wake-up
        count--;
    }
    void signal() {                                  // V / up / release
        { lock_guard<mutex> lk(m); count++; }
        cv.notify_one();
    }
};
```

**Verified test:** 10 threads each `wait()`, hold the "resource" for 20 ms, then `signal()` on a `Semaphore(3)`. The maximum number observed inside at once was **3**.

**Busy-waiting vs blocking implementations:** Dijkstra's original definition busy-waits (`while (S <= 0);`), which is a "spinlock semaphore". Real OS semaphores keep a **queue of blocked processes**: `wait` adds the caller to the queue and blocks it, and `signal` removes one and makes it ready. With that implementation, S can also be read as negative: **|S| = the number of waiting processes**. That's a common textbook detail.

**Standard C++20:** `std::counting_semaphore<N>` and `std::binary_semaphore`, with `acquire()` / `release()` / `try_acquire_for()`. (See this module's introduction for the toolchain note.)

### 5. Mutex vs semaphore (the most-asked question in this module)

| | Mutex | Semaphore |
|---|---|---|
| What it is | A **lock** (locking mechanism) | A **counter** with wait/signal (signalling mechanism) |
| **Ownership** | **Yes**: only the locking thread may unlock | **No**: any thread may signal |
| Value | Locked / unlocked | 0 … N |
| Allows N concurrent holders | No (exactly 1) | **Yes** (counting) |
| Typical purpose | **Protect shared data** (mutual exclusion) | **Manage N resources**, or **signal events between threads** |
| Signalling across threads ("A done, B may go") | Not its purpose (unlocking from another thread is an error) | **Designed for it** (init 0) |
| Priority inheritance possible | Yes (it knows its owner) | Generally no (no owner) |
| Misuse risk | Forgetting to unlock (use RAII) | **Easy to misuse**: an extra signal silently raises the count |

**"Isn't a binary semaphore the same as a mutex?"** Functionally similar for mutual exclusion, but **not the same**: a mutex has **ownership** (only the owner unlocks; this enables priority inheritance and error checking), while a binary semaphore can be signalled by any thread, which makes it suitable for signalling but error-prone as a lock.

**Model answer:** *"A mutex is a lock with ownership: one thread acquires it, the same thread releases it, and it protects a critical section. A semaphore is a counter with atomic wait and signal and no ownership. A counting semaphore lets up to N threads use a pool of N resources, and a semaphore initialised to 0 lets one thread signal another that something happened. Use a mutex to protect data and a semaphore to count resources or signal events."*

---

## 4.7 Condition variables and monitors

### 1. Condition variable: wait for a condition, not just a lock

A mutex answers "**who** may touch the data?". Often a thread also needs "**wait until** the data is in some state" (the queue is non-empty, it's my turn). Spinning on the condition while repeatedly re-locking wastes CPU. A **condition variable** lets a thread **sleep until notified**.

```cpp
unique_lock<mutex> lk(m);
cv.wait(lk, [&] { return !q.empty(); });   // 1. checks the predicate; if false:
                                           // 2. ATOMICALLY releases lk and sleeps
                                           // 3. on wake-up, RE-ACQUIRES lk and re-checks the predicate
// here: lock held AND predicate true
```

### 2. The rules that cause real bugs

| Rule | Why |
|---|---|
| **Always wait with a predicate** (or in a `while` loop), never with a bare `if` | **Spurious wake-ups** (a waiter can wake without a notify) and **stolen wake-ups** (another thread consumed the item first) |
| Modify the shared state **under the same mutex** the waiter uses | Otherwise a **lost wake-up**: the notify happens between the waiter's check and its sleep |
| `notify_one()` wakes one waiter; `notify_all()` wakes all | Use `notify_all` when several waiters may need to re-evaluate different conditions (as in odd/even, §4.13) |
| You may notify after unlocking | Avoids waking a thread that immediately blocks on the still-held mutex (a small optimisation, used in the code below) |
| Waiting releases the mutex atomically | That's the entire reason `wait` takes the lock as a parameter |

### 3. Monitors

A **monitor** is a language-level construct that bundles **shared data + the procedures that access it + automatic mutual exclusion + condition variables**. Only one thread can be active inside the monitor at a time.

- **Java:** every object is a monitor. `synchronized` methods get the lock automatically, with `wait()` / `notify()` / `notifyAll()` as its condition variable.
- **C++:** no monitor keyword; a class with a private `mutex` + `condition_variable`, locking in every public method, **is** a monitor by construction. `BoundedQueue` (§4.8) is one.

| | Semaphore | Monitor |
|---|---|---|
| Level | Low-level primitive | High-level construct (data + operations + lock + conditions) |
| Mutual exclusion | Manual: you must pair every wait/signal correctly | **Automatic** for every monitor procedure |
| Error-proneness | High (a forgotten signal leads to deadlock; a misplaced signal breaks exclusion) | Lower |

---

## 4.8 Producer-consumer (bounded buffer)

### 1. The problem

Producers put items into a **fixed-size buffer**; consumers take them out. Constraints:
1. A producer must **wait if the buffer is full**.
2. A consumer must **wait if the buffer is empty**.
3. Buffer updates must be **mutually exclusive**.

It's everywhere in practice: thread pools (task queues), logging pipelines, network packet queues, Unix pipes.

### 2. The classic semaphore solution

```
 semaphore mutex = 1;      // protects the buffer
 semaphore empty = N;      // counts EMPTY slots
 semaphore full  = 0;      // counts FULL slots

 producer:                         consumer:
   item = produce();                 wait(full);       // wait for an item
   wait(empty);    // a free slot    wait(mutex);
   wait(mutex);                      item = remove();
   insert(item);                     signal(mutex);
   signal(mutex);                    signal(empty);    // one more free slot
   signal(full);   // one more item  consume(item);
```

**C++ version** (with the verified `Semaphore` class from §4.6; a ring buffer of 5):

```cpp
const int N = 5;
int ring[N]; int inIdx = 0, outIdx = 0;
Semaphore emptySlots(N);     // free slots
Semaphore fullSlots(0);      // filled slots
mutex ringMtx;

void producerSem(int count) {
    for (int i = 1; i <= count; i++) {
        emptySlots.wait();                                                   // wait(empty)
        { lock_guard<mutex> g(ringMtx); ring[inIdx] = i; inIdx = (inIdx + 1) % N; }
        fullSlots.signal();                                                  // signal(full)
    }
}
long long consumedSum = 0;
void consumerSem(int count) {
    for (int i = 0; i < count; i++) {
        fullSlots.wait();                                                    // wait(full)
        int x;
        { lock_guard<mutex> g(ringMtx); x = ring[outIdx]; outIdx = (outIdx + 1) % N; }
        emptySlots.signal();                                                 // signal(empty)
        consumedSum += x;
    }
}
// producer and consumer, 100,000 items  ->  "semaphore pc sum = 5000050000"  (= 1+2+...+100000, verified)
```

### 3. The ordering trap (asked as "what happens if you swap these two lines?")

If the producer does **`wait(mutex)` before `wait(empty)`** and the buffer is full:
- The producer holds the mutex, then blocks on `empty`.
- The consumer needs the mutex to remove an item (and signal `empty`), so it blocks on `mutex`.
- **Deadlock.** Each waits for the other forever.

**Rule: wait on the counting semaphore first, then on the mutex.** (Swapping the two `signal`s is harmless, at most slightly less efficient.)

### 4. The condition-variable version: a reusable blocking queue

This is what you'd actually write in C++, and it's the answer to *"implement a thread-safe bounded blocking queue"*:

```cpp
template <class T>
class BoundedQueue {
    queue<T> q; size_t cap;
    mutex m; condition_variable notFull, notEmpty;
public:
    explicit BoundedQueue(size_t c) : cap(c) {}
    void put(T x) {
        unique_lock<mutex> lk(m);
        notFull.wait(lk, [&] { return q.size() < cap; });   // block while full
        q.push(move(x));
        lk.unlock();
        notEmpty.notify_one();
    }
    T take() {
        unique_lock<mutex> lk(m);
        notEmpty.wait(lk, [&] { return !q.empty(); });      // block while empty
        T x = move(q.front()); q.pop();
        lk.unlock();
        notFull.notify_one();
        return x;
    }
};

// test: capacity 4, one producer puts 1..100000 then a -1 sentinel; one consumer sums until -1
// -> "bounded queue sum = 5000050000 (expected 5000050000)"   (verified)
```

**Why two condition variables?** Producers wait for "not full" and consumers for "not empty". Separate CVs mean a `notify_one` always wakes the right kind of thread. (With one CV and `notify_one`, a producer could wake another producer, and with both sides waiting this can stall. One CV works with `notify_all`, at the cost of extra wake-ups.)

**Shutdown:** real queues need a way to stop consumers. The test uses a **sentinel value** (−1). Alternatives are a `closed` flag checked in the predicate, or `std::stop_token` (C++20).

---

## 4.9 Readers-writers

### 1. The problem

Shared data (a config, a cache, a database table) is **read often and written rarely**. Concurrent **readers are safe** together; a **writer needs exclusive access** (no readers, no other writers).

### 2. Variants and their starvation problems

| Variant | Rule | Who can starve |
|---|---|---|
| **First readers-writers** (reader preference) | No reader waits unless a writer is **already writing** | **Writers** (a steady stream of readers keeps them out forever) |
| **Second readers-writers** (writer preference) | Once a writer is waiting, **no new readers** start | **Readers** |
| Fair (FIFO) | Arrival order respected | No one, but less concurrency |

### 3. The classic reader-preference solution

```
 semaphore rw_mutex = 1;   // exclusive access for writers (and the first/last reader)
 semaphore mutex = 1;      // protects read_count
 int read_count = 0;

 writer:                          reader:
   wait(rw_mutex);                  wait(mutex);
   write();                         read_count++;
   signal(rw_mutex);                if (read_count == 1) wait(rw_mutex);   // FIRST reader locks out writers
                                    signal(mutex);
                                    read();                               // many readers here at once
                                    wait(mutex);
                                    read_count--;
                                    if (read_count == 0) signal(rw_mutex); // LAST reader lets writers in
                                    signal(mutex);
```

The key idea: **the first reader in locks out writers, and the last reader out lets them in.**

### 4. In C++: `std::shared_mutex`

```cpp
class Config {
    mutable shared_mutex rw; map<string, string> data;
public:
    string get(const string& k) const {
        shared_lock<shared_mutex> l(rw);         // SHARED: many readers at once
        auto it = data.find(k); return it == data.end() ? "" : it->second;
    }
    void set(const string& k, const string& v) {
        unique_lock<shared_mutex> l(rw);         // EXCLUSIVE: one writer, no readers
        data[k] = v;
    }
};
// 8 reader threads x 10,000 gets, concurrent with a writer doing 1,000 sets
// -> "readers-writers reads = 80000"   (every read succeeded; no torn reads; verified)
```

(The mutex is `mutable` so that `get()` can be `const`: locking is bookkeeping, not logical state. See OOP M0 §0.7.)

**When a readers-writer lock is *not* worth it:** it costs more than a plain mutex. If the critical section is tiny, or writes are frequent, a plain `mutex` is often faster. Don't reach for `shared_mutex` reflexively.

---

## 4.10 Dining philosophers

### 1. The problem

Five philosophers sit at a round table with **five forks**, one between each pair. To eat, a philosopher needs **both** adjacent forks. Design a protocol with **no deadlock and no starvation**.

```
            P0
       F4        F0
    P4              P1
     F3            F1
       P3   F2   P2
```

### 2. The naive solution deadlocks

```
 philosopher i:  pick up left fork; pick up right fork; eat; put both down
```

If all five pick up their **left** fork at the same moment, everyone waits forever for their right fork, which is held by a neighbour. That's a textbook **circular wait** (M5).

### 3. Solutions

| Solution | How | Breaks which deadlock condition (M5) |
|---|---|---|
| **Resource ordering** | Number the forks; always pick up the **lower-numbered fork first** (so the last philosopher picks right-then-left) | **Circular wait** |
| **Acquire both atomically** | Take both forks together or neither: `std::scoped_lock`, or check both under a monitor | **Hold and wait** |
| **At most 4 at the table** | A counting semaphore initialised to 4 (n − 1) | Circular wait (the pigeonhole principle guarantees one philosopher gets both) |
| **Asymmetric** | Odd philosophers take left first; even ones take right first | Circular wait |
| **Waiter / arbitrator** | Ask a central waiter (mutex) for permission | Hold and wait (centralised) |

### 4. C++: both deadlock-free versions, verified

```cpp
// A) resource ordering: lower-numbered fork first
void dineOrdered(int philosophers, int meals, vector<int>& eaten) {
    vector<mutex> fork(philosophers);
    vector<thread> ts;
    for (int i = 0; i < philosophers; i++) {
        ts.emplace_back([&, i] {
            int a = i, b = (i + 1) % philosophers;
            int first = min(a, b), second = max(a, b);   // GLOBAL ORDER
            for (int k = 0; k < meals; k++) {
                lock_guard<mutex> l1(fork[first]);
                lock_guard<mutex> l2(fork[second]);
                eaten[i]++;
            }
        });
    }
    for (auto& t : ts) t.join();
}

// B) acquire both atomically
//    inside the loop:  scoped_lock both(left, right);  eaten[i]++;
```

**Verified output** (5 philosophers × 10,000 meals each):
```
philosophers (scoped_lock): 10000 10000 10000 10000 10000
philosophers (ordered):     10000 10000 10000 10000 10000
```

Both completed every meal, with no deadlock. (A demonstration isn't a proof. The proof is that each solution breaks a necessary condition for deadlock, M5. Concurrency bugs are timing-dependent, so "it ran fine" is never sufficient on its own.)

**Starvation note:** deadlock freedom doesn't guarantee **fairness**. A philosopher could repeatedly lose the race for forks. Fair solutions add ordering (tickets/FIFO) or a waiter that queues requests.

---

## 4.11 Coding drill: print odd and even numbers with two threads

**The most common concurrency coding question for freshers.** Thread A prints odd numbers and thread B prints even ones, in order 1, 2, 3, … N.

```cpp
class OddEven {
    mutex m; condition_variable cv; int next = 1; int limit;
public:
    explicit OddEven(int l) : limit(l) {}
    void run(bool odd, string& out) {
        while (true) {
            unique_lock<mutex> lk(m);
            cv.wait(lk, [&] { return next > limit || (next % 2 == 1) == odd; });   // my turn, or finished
            if (next > limit) { cv.notify_all(); return; }                       // wake the other so it exits too
            out += to_string(next) + " ";
            next++;
            cv.notify_all();                                                     // hand over the turn
        }
    }
};

OddEven oe(10); string out;
thread o([&] { oe.run(true, out); }), e([&] { oe.run(false, out); });
o.join(); e.join();
// -> "odd/even: 1 2 3 4 5 6 7 8 9 10"   (verified)
```

**What makes it correct, and what interviewers check:**
1. **One shared state** (`next`) decides whose turn it is, read and written only under the mutex.
2. **A predicate wait**: no spurious-wake-up bug, no busy loop.
3. **A termination condition in the predicate**: without `next > limit`, the last thread waits forever once the other exits.
4. Writing to `out` is safe because only the thread holding the mutex appends to it.

**Semaphore alternative** (two semaphores handing the turn back and forth):
```
 semaphore oddTurn = 1, evenTurn = 0;
 odd thread:  for i = 1, 3, 5...:  wait(oddTurn);  print i;  signal(evenTurn);
 even thread: for i = 2, 4, 6...:  wait(evenTurn); print i;  signal(oddTurn);
```

**Variations to practise:** print 1..N with **three** threads in round-robin; LeetCode 1114 *Print in Order*, 1115 *Print FooBar Alternately*, 1116 *Print Zero Even Odd*, 1117 *Building H2O* (a semaphore-counting exercise).

---

## 4.12 Atomics, memory ordering, and what not to do (Tier 2/3)

| Point | Detail |
|---|---|
| `std::atomic<T>` | Indivisible operations + visibility guarantees between threads; lock-free for small types on mainstream CPUs |
| Atomic ≠ the whole operation is safe | `if (x.load() > 0) x--;` is still check-then-act. Use a CAS loop or a mutex |
| Default memory order is `seq_cst` | The easiest to reason about; `acquire`/`release` are the efficient pair used by locks (as in the spinlock) |
| `volatile` | For memory-mapped hardware registers, **not** thread synchronization in C++ (unlike Java, where `volatile` does give visibility) |
| Double-checked locking | Correct in C++ only with atomics; prefer function-local statics or `std::call_once` (OOP M8 Singleton) |
| Lock granularity | One big lock is simple but serialises everything; fine-grained locks scale but risk deadlock (M5). Start coarse, then measure |
| Hold locks briefly | Never do I/O, sleep, or call unknown code (callbacks) while holding a lock |

---

## 4.13 Choosing the right tool

```
 Protecting shared data from concurrent modification?
 ├── A simple counter or flag?                    -> std::atomic
 ├── Mostly reads, rare writes, non-trivial CS?   -> std::shared_mutex (readers-writer)
 ├── Very short CS, multicore, can't sleep?       -> spinlock
 └── Otherwise                                    -> std::mutex + lock_guard
 Waiting until some condition becomes true?       -> condition_variable (with predicate)
 Limiting concurrent access to N resources?       -> counting semaphore
 One thread signalling another that X happened?   -> semaphore (init 0) or condition_variable
 Locking several mutexes together?                -> std::scoped_lock (or a fixed global order)
```

---

## 4.14 Consolidation

### Must remember (module)

1. Race condition = outcome depends on interleaving; a data race in C++ is UB.
2. CS requirements: **mutual exclusion, progress, bounded waiting** (no speed assumptions).
3. A naive flag fails because check-then-set isn't atomic; strict alternation fails progress.
4. Peterson's: flags + turn; correct for 2 threads with sequentially consistent memory; busy-waits; not used in practice.
5. Hardware: TAS, CAS, fetch-add, all atomic RMW. Disabling interrupts is single-core and kernel-only. `volatile` ≠ synchronization.
6. Mutex: lock with **ownership**; blocking; RAII (`lock_guard`, `unique_lock`, `scoped_lock`); futex fast path in user space.
7. Spinlock: busy-wait; short sections, multicore, kernels; never on a single core; never sleep while holding one.
8. Semaphore: counter with atomic wait/signal, **no ownership**. Init 1 = lock, N = pool, 0 = signal.
9. **Mutex vs semaphore** = ownership + purpose (protect data vs count/signal).
10. Condition variable: `wait` atomically releases the lock and sleeps; **always use a predicate** (spurious and stolen wake-ups).
11. Monitor = data + procedures + automatic mutual exclusion + condition variables (Java `synchronized`).
12. Producer-consumer: `empty = N`, `full = 0`, `mutex = 1`; **wait on the counting semaphore before the mutex** or you deadlock.
13. Readers-writers: the first reader locks out writers, the last lets them in; reader preference starves writers; `std::shared_mutex`.
14. Dining philosophers: the naive version is a circular wait; fixes are ordering, atomic acquisition (`scoped_lock`), n−1 seats, asymmetry, a waiter.
15. Odd/even: one shared turn variable + a predicate wait + a termination condition + `notify_all`.

### Common wrong answers (module)

- "A binary semaphore and a mutex are identical." (Ownership.)
- "A spinlock is always faster than a mutex."
- "`volatile` makes a variable thread-safe."
- "`std::atomic` makes any sequence of operations atomic."
- Using `if` instead of a predicate/`while` around `cv.wait`.
- `wait(mutex)` before `wait(empty)` in the producer.
- "It ran 10 times without failing, so it's correct."
- Holding a lock while doing I/O or calling callbacks.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is a race condition? | Result depends on interleaving of unsynchronized shared accesses | Example? (`counter++`: load-add-store) |
| Critical-section requirements? | Mutual exclusion, progress, bounded waiting | Which does strict alternation violate? (Progress) |
| Explain Peterson's solution | Intent flags + turn tie-breaker; the last writer of `turn` yields | Does it work on modern CPUs? (Only with barriers / seq_cst atomics) |
| What is test-and-set / CAS? | Atomic hardware read-modify-write instructions | Build a spinlock with one |
| Mutex vs semaphore? | Lock with ownership for data protection vs counter without ownership for resources/signalling | Binary semaphore vs mutex? |
| Spinlock vs mutex? | Busy-wait vs sleep; short vs long sections | Why are spinlocks bad on one core? |
| What is a condition variable? | Sleep until a condition holds; `wait` releases the lock atomically | Why use a while loop / predicate? |
| What is a monitor? | Data + operations + automatic lock + condition variables | Java equivalent? |
| Producer-consumer with semaphores? | `empty = N`, `full = 0`, `mutex = 1`, correct wait order | What if you swap the waits? (Deadlock) |
| Readers-writers? | Concurrent readers, exclusive writers; preference → starvation | C++ tool? (`shared_mutex`) |
| Dining philosophers? | Naive = circular wait; resource ordering / atomic pickup / n−1 seats | Which deadlock condition does each break? |
| Implement a thread-safe queue | Mutex + two condition variables (BoundedQueue) | How do you shut it down? |
| Print odd/even with two threads | Shared turn + CV predicate + notify_all + termination | Generalise to 3 threads |

### Practice

**P1.** Two threads run `x = x + 1` 3 times each on a shared `x = 0`, with no synchronization. What are the minimum and maximum final values of `x`?
<details><summary>Answer</summary>

**Max 6** (no overlap). **Min 2**, which is subtle: thread A loads 0 and stalls; B completes two increments (x = 2); A stores 1 (x = 1); B loads 1 for its third increment and stalls; A completes its remaining two increments (x = 3); B stores 2. Final **2**. Lost updates can be far worse than "off by one".
</details>

**P2.** Which critical-section requirement does each violate? (a) Strict alternation with `turn`. (b) A lock that lets the same thread re-enter forever while others wait. (c) A naive `while (locked); locked = true;`.
<details><summary>Answer</summary>

(a) Progress. (b) Bounded waiting (starvation). (c) Mutual exclusion.
</details>

**P3.** Using semaphores, ensure statement `S2` in thread B runs only after statement `S1` in thread A.
<details><summary>Answer</summary>

`semaphore s = 0;` Thread A: `S1; signal(s);` Thread B: `wait(s); S2;`. This is the ordering idiom (init 0).
</details>

**P4.** A parking lot has 50 spaces. Cars are threads that must wait when the lot is full. Which primitive, initialised to what?
<details><summary>Answer</summary>

A **counting semaphore initialised to 50**: `wait()` on entry, `signal()` on exit. (Any extra bookkeeping, such as which spot, still needs a mutex.)
</details>

**P5.** Find the bug:
```cpp
void take(queue<int>& q, mutex& m, condition_variable& cv) {
    unique_lock<mutex> lk(m);
    if (q.empty()) cv.wait(lk);
    int x = q.front(); q.pop();
}
```
<details><summary>Answer</summary>

`if` instead of a loop or predicate. After a **spurious wake-up**, or when another consumer **stole** the item first, `q` can still be empty, so `front()` on an empty queue is UB. Fix: `cv.wait(lk, [&]{ return !q.empty(); });`.
</details>

**P6.** Extend the odd/even printer to three threads printing 1..N in round-robin (thread 0 prints 1, 4, 7…; thread 1 prints 2, 5, 8…; thread 2 prints 3, 6, 9…).
<details><summary>Answer</summary>

Same structure, with the turn predicate changed to `(next - 1) % 3 == id`:
```cpp
void run(int id, int k /* threads */, string& out) {
    while (true) {
        unique_lock<mutex> lk(m);
        cv.wait(lk, [&] { return next > limit || (next - 1) % k == id; });
        if (next > limit) { cv.notify_all(); return; }
        out += to_string(next++) + " ";
        cv.notify_all();               // must be ALL: only one specific thread can proceed
    }
}
```
</details>

---

## Exit checklist

```
[ ] I can define race condition, data race, critical section, mutual exclusion
[ ] I can state the 3 CS requirements and identify which a broken solution violates
[ ] I can explain why the naive flag and strict alternation fail
[ ] I can write and explain Peterson's solution, including the memory-ordering caveat
[ ] I can explain TAS/CAS and write a spinlock with atomic_flag
[ ] I can compare spinlock vs mutex, and mutex vs semaphore (ownership!)
[ ] I can implement a semaphore with mutex + condition_variable
[ ] I know the 3 semaphore idioms (1 / N / 0)
[ ] I can explain condition-variable rules (predicate, atomic release, lost wake-ups)
[ ] I can write producer-consumer with semaphores AND with condition variables
[ ] I can explain the wait-order deadlock in producer-consumer
[ ] I can solve readers-writers (and name who starves) and use shared_mutex
[ ] I can give 4 deadlock-free dining-philosopher solutions and what each breaks
[ ] I can write odd/even printing from memory, and generalise to k threads
[ ] P1–P6 done
```

---

## Next

**Part 7: M5 — Deadlocks.** It covers the four Coffman conditions, resource-allocation graphs (cycle detection, using DSA graph skills), the four strategies (prevention, avoidance, detection and recovery, and ignoring the problem), **Banker's algorithm with a fully worked safe-sequence numerical and request handling**, and deadlock vs starvation vs livelock, with lock-ordering in real code.
