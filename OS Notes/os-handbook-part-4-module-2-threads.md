# Operating Systems Placement Handbook — Part 4
# Module 2: Threads

**Module 2 · 2 hours · Tier 1 · Requires: M1**

---

## Why this module matters

**"What is the difference between a process and a thread?"** is the most frequently asked OS interview question. It looks easy, so it's graded strictly. "A thread is a lightweight process" alone is a weak answer. The strong answer is precise about **what is shared and what is private**, and explains *why* threads are cheaper and *what risk* the sharing creates.

This module also sets up M4: as soon as threads share memory, **race conditions** appear. You'll run one at the end of this module and watch it give the wrong answer.

The organising principle:

> **A process is a container of resources: an address space, open files, credentials. A thread is a flow of execution inside that container: a program counter, registers and a stack. Threads in one process share the container, which makes them cheap to create and fast to switch between, and also lets them corrupt each other's data.**

---

## 2.1 What a thread is

### 1. What is it?

A **thread** is the smallest unit of execution that the OS schedules. A process starts with one thread (the main thread) and can create more; all of them run within the process's address space.

### 2. What is shared, and what is private (the core of the answer)

```
                    ONE PROCESS
 +-------------------------------------------------------------+
 |  SHARED by all threads:                                     |
 |    code (text)   global/static data   HEAP                  |
 |    open files (fd table)   current dir   signal handlers    |
 |    address space (page tables)   PID   user/group IDs       |
 |                                                             |
 |   Thread 1          Thread 2          Thread 3              |
 |   +----------+      +----------+      +----------+          |
 |   | thread ID|      | thread ID|      | thread ID|  PRIVATE |
 |   | PC       |      | PC       |      | PC       |  to each |
 |   | registers|      | registers|      | registers|  thread  |
 |   | STACK    |      | STACK    |      | STACK    |          |
 |   | errno,   |      | errno,   |      | errno,   |          |
 |   | TLS, mask|      | TLS, mask|      | TLS, mask|          |
 |   +----------+      +----------+      +----------+          |
 +-------------------------------------------------------------+
```

| Shared (per process) | Private (per thread) |
|---|---|
| Code segment | **Thread ID** |
| Global and static variables | **Program counter** |
| **Heap** | **Registers** (including the stack pointer) |
| Open file descriptors | **Stack** (local variables, call frames) |
| Address space / page tables | Thread-local storage (`thread_local`), `errno` |
| Signal handlers, PID, credentials | Signal mask, scheduling priority/state |

**The key subtlety:** each thread's stack is *private by convention, not by protection*. All the stacks are in the same address space, so a thread *could* access another thread's locals through a pointer. Nothing in the hardware stops it. That's why passing a pointer to a local variable to another thread is a classic bug: the local dies when its function returns.

### 3. Why do threads exist? (four benefits)

| Benefit | Explanation | Example |
|---|---|---|
| **Responsiveness** | One thread can block (I/O, computation) while others keep working | A UI thread stays responsive while a worker downloads a file |
| **Resource sharing** | Threads share memory by default, with no IPC setup needed | Worker threads all read one in-memory cache |
| **Economy** | Creating and switching threads is much cheaper than for processes | Thread creation avoids copying page tables and file tables |
| **Scalability** | Threads of one process run **in parallel** on multiple cores | A parallel sort uses all 8 cores |

---

## 2.2 Process vs thread (the comparison)

| | Process | Thread |
|---|---|---|
| Definition | A program in execution, a **container of resources** | A **unit of execution** within a process |
| Address space | **Own**, isolated | **Shared** with the process's other threads |
| Memory sharing | Needs explicit IPC (pipes, shared memory, sockets) | Automatic: same heap and globals |
| Creation cost | **High** (new address space, page tables, fd table; COW helps) | **Low** (a new stack + registers + kernel thread struct) |
| Context switch | **Expensive** (address-space switch, TLB impact) | **Cheaper** within a process (no address-space switch) |
| Isolation and fault tolerance | A crash affects only that process | **A crash (e.g. a segfault) kills the whole process**, all threads |
| Synchronization needed | Rarely (memory isn't shared by default) | **Constantly**: shared data means races (M4) |
| Communication | Slower (kernel-mediated IPC) | Fast (direct memory access) |
| Unix creation call | `fork()` | `pthread_create()` / `std::thread` (Linux: `clone()` with sharing flags) |
| Identifier | PID | TID (and the shared PID) |

### The model answer (about 45 seconds)

*"A process is an independent program in execution with its own address space and resources: memory, open files, credentials. A thread is a unit of execution within a process. Threads share the process's code, heap, globals and open files, but each has its own stack, registers and program counter. So threads are much cheaper to create and switch between, since there's no address-space change, and they communicate directly through shared memory. The cost is isolation: one thread crashing brings down the whole process, and shared data needs synchronization to avoid race conditions. Processes are isolated and robust but communicate through slower IPC. That's why Chrome, for example, uses separate processes per site for isolation and many threads within each process."*

### When to use which

| Use processes when | Use threads when |
|---|---|
| **Isolation / fault tolerance** matters (browser tabs, worker crashes must not kill the server) | Tasks share lots of data and need fast communication |
| **Security** boundaries are needed (different privileges) | Low overhead matters (many short tasks) |
| Running different programs | Parallelising one computation across cores |
| Example: Chrome's process-per-site, PostgreSQL's process per connection, `nginx` worker processes | Example: a game engine's render/physics/audio threads, a web server's thread pool, parallel algorithms |

---

## 2.3 User-level vs kernel-level threads

### 1. The distinction

| | User-level threads (ULT) | Kernel-level threads (KLT) |
|---|---|---|
| Managed by | A **user-space library** (runtime); the kernel doesn't know they exist | The **kernel**: each has a kernel structure and is scheduled by the OS |
| Creation and switch cost | **Very cheap**: no system call, just a library function swapping registers | More expensive: system call, kernel involvement |
| If one thread makes a blocking system call | **The entire process blocks**, because the kernel sees only one thread | Only that thread blocks; the others keep running |
| Multicore parallelism | **No**: the kernel schedules the process as one unit on one core | **Yes**: threads run on different cores |
| Scheduling | Customisable by the application | The OS's policy |
| Examples | Early Java "green threads", GNU Portable Threads | Linux pthreads (NPTL), Windows threads, C++ `std::thread` |

### 2. Threading models (mapping user threads to kernel threads)

```
   MANY-TO-ONE                 ONE-TO-ONE                  MANY-TO-MANY
   U  U  U  U                  U   U   U                   U  U  U  U  U
    \  \ /  /                  |   |   |                    \ | X  | /
       K                       K   K   K                      K   K   K
```

| Model | Description | Pros | Cons | Examples |
|---|---|---|---|---|
| **Many-to-one** | Many user threads on one kernel thread | Cheap switching | One block blocks all; no parallelism | Green threads (historical) |
| **One-to-one** | Each user thread is a kernel thread | True parallelism; blocking is isolated | Kernel cost per thread; limits on thread count | **Linux NPTL, Windows, `std::thread`** (the dominant model) |
| **Many-to-many** (M:N) | M user threads multiplexed on N kernel threads | Many cheap threads **and** parallelism | Complex runtime scheduling | **Go goroutines**, Java virtual threads (JDK 21+), Erlang processes |

**Modern relevance:** OS threads are one-to-one, but language runtimes have brought back M:N for massive concurrency. Go runs hundreds of thousands of goroutines on a handful of OS threads, and the runtime switches a goroutine out when it blocks. Mentioning this shows current knowledge.

### 3. On Linux: threads are tasks

Linux doesn't fundamentally distinguish processes and threads in the kernel. Both are **tasks** (`task_struct`), created by `clone()`. The flags decide what is shared:
- `fork()` ≈ `clone()` sharing nothing (copy-on-write copies of everything).
- `pthread_create()` ≈ `clone(CLONE_VM | CLONE_FILES | CLONE_FS | CLONE_SIGHAND | CLONE_THREAD | ...)`, which shares the address space, files and signal handlers.

So on Linux, "a thread is a process that shares its address space" is literally how it's implemented.

### 4. `fork()` in a multithreaded process (trick question)

**Only the calling thread is duplicated** in the child. The other threads don't exist there, but memory is copied, including any **mutex they were holding**. If another thread held a lock at the moment of `fork`, the child's copy of that lock is locked forever, with no owner to release it. Hence the rule: **in a multithreaded program, the child should call only async-signal-safe functions and then `exec` right away.**

---

## 2.4 Concurrency vs parallelism

| | Concurrency | Parallelism |
|---|---|---|
| Meaning | **Dealing with** many tasks at once: progress interleaves | **Doing** many tasks at the same instant |
| Requires multiple cores | **No**: one core can interleave via context switches | **Yes** |
| About | Structure (how a program is organised) | Execution (simultaneous computation) |
| Analogy | One cook alternating between two dishes | Two cooks, each making a dish |

```
 Concurrency on 1 core:     T1 ██░░██░░██     (time-sliced, interleaved)
                            T2 ░░██░░██░░
 Parallelism on 2 cores:    T1 ██████████     core 0
                            T2 ██████████     core 1
```

**One-liner:** *"Concurrency is about dealing with lots of things at once; parallelism is about doing lots of things at once."* (Rob Pike.) Concurrency is possible without parallelism; parallelism implies concurrency.

### The "multi-" vocabulary (asked as a set)

| Term | Meaning |
|---|---|
| **Multiprogramming** | Several programs in memory; the CPU switches when one waits for I/O (M0) |
| **Multitasking** | Several tasks share the CPU via **time slices** (preemptive) |
| **Multithreading** | Several threads within **one process** |
| **Multiprocessing** | Several **CPUs/cores** executing simultaneously |
| **Hyper-threading / SMT** | One physical core presents 2 logical cores, sharing its execution units; it helps when one thread stalls, but isn't 2× a real core |

---

## 2.5 How much speedup do threads give? Amdahl's law

If a fraction **p** of a program can be parallelised and it runs on **n** cores:

```
                  1
 Speedup = ----------------
            (1 - p) + p / n
```

**Example:** 90% parallelisable (p = 0.9) on 8 cores: 1 / (0.1 + 0.9/8) = 1 / 0.2125 ≈ **4.7×**, not 8×. Even with infinitely many cores: 1 / 0.1 = **10×** at most.

**The point interviewers want:** the serial part dominates. Adding cores has diminishing returns, and synchronization (M4) adds more serial sections (locks). That's why "just add threads" doesn't scale linearly.

---

## 2.6 C++ threads in practice

### 1. Creating, joining, passing arguments

```cpp
#include <bits/stdc++.h>
using namespace std;

void worker(int id, const string& msg) { cout << "thread " << id << ": " << msg << "\n"; }
void addTo(int& total, int x) { total += x; }

int main() {
    thread t1(worker, 1, "hello");          // starts running immediately
    t1.join();                              // wait for it to finish

    thread t2([] { cout << "lambda thread\n"; });
    t2.join();

    int total = 0;
    thread t3(addTo, ref(total), 5);        // arguments are COPIED unless wrapped in std::ref
    t3.join();
    cout << "total = " << total << "\n";
}
```

**Output:**
```
thread 1: hello
lambda thread
total = 5
```

### 2. Rules that cause real bugs

| Rule | Why |
|---|---|
| **Every `std::thread` must be `join()`ed or `detach()`ed before its destructor runs** | Otherwise the destructor calls `std::terminate()` and the program aborts |
| `join()` = wait for completion; `detach()` = let it run independently | A detached thread must not use anything that may be destroyed (locals of the creating function, or globals at exit) |
| Arguments are **copied** into the thread | Passing `int&` without `std::ref` makes a copy, or doesn't compile; changes don't reach the caller |
| Never pass a pointer or reference to a **local** to a thread that may outlive the function | Dangling stack reference (§2.1) |
| C++20 `std::jthread` **joins automatically** in its destructor | It's RAII for threads (OOP M1), and also supports cooperative cancellation |
| `thread::hardware_concurrency()` | Hint for the number of hardware threads (may return 0 if unknown) |

### 3. The data race: run this and watch it fail

```cpp
int counter = 0;                                     // shared, unprotected
void incrementMany(int n) { for (int i = 0; i < n; i++) counter++; }

atomic<int> safeCounter{0};
void incrementAtomic(int n) { for (int i = 0; i < n; i++) safeCounter++; }

int main() {
    thread a(incrementMany, 1000000), b(incrementMany, 1000000);
    a.join(); b.join();
    cout << "racy counter = " << counter << " (expected 2000000)\n";

    thread c(incrementAtomic, 1000000), d(incrementAtomic, 1000000);
    c.join(); d.join();
    cout << "atomic counter = " << safeCounter << "\n";
}
```

**Three real runs** (g++ 12, `-O0`, multicore machine):
```
racy counter = 1110614 (expected 2000000)      atomic counter = 2000000
racy counter = 1029738 (expected 2000000)      atomic counter = 2000000
racy counter = 1294530 (expected 2000000)      atomic counter = 2000000
```

The racy result is **different every run** and always too low. The atomic one is always exact.

### 4. Why `counter++` loses updates

`counter++` is not one operation. It's **three**: load, add, store.

```
 counter = 41
 Thread A                      Thread B
 load  counter -> reg (41)
                               load  counter -> reg (41)
 add   reg = 42
                               add   reg = 42
 store reg -> counter (42)
                               store reg -> counter (42)     <- one increment LOST
 counter = 42, should be 43
```

This is a **race condition**: the result depends on the timing of the interleaving. Formally, unsynchronized concurrent access where at least one access is a write is a **data race**, which in C++ is **undefined behaviour**. Optimised builds can do even stranger things, such as keeping `counter` in a register for the whole loop. Fixes, all covered in M4:
- `std::atomic<int>`: the hardware performs the read-modify-write **atomically** (e.g. `lock xadd` on x86).
- A `std::mutex` around the critical section.
- Avoid sharing: each thread counts locally and the totals are added at the end. This is the fastest option.

### 5. Thread pools (why, in one paragraph)

Creating a thread per task costs a system call, stack allocation and kernel bookkeeping. Under heavy load, unbounded thread creation exhausts memory and thrashes the scheduler. A **thread pool** creates a fixed number of worker threads (often ≈ the number of cores for CPU-bound work, more for I/O-bound work) that take tasks from a **shared queue**. That queue is a producer-consumer problem (M4), and building a small thread pool is a common product-company exercise.

---

## 2.7 Consolidation

### Must remember (module)

1. Thread = PC + registers + stack inside a process; the process is the resource container.
2. **Shared:** code, globals, heap, open files, address space, signal handlers. **Private:** TID, PC, registers, stack, TLS/`errno`, signal mask.
3. Threads are cheaper to create and switch (no address-space change), but **one crash kills the process**, and sharing needs synchronization.
4. ULT: cheap, but one blocking call blocks all and there's no parallelism. KLT: parallel, kernel cost. Models: many-to-one, **one-to-one (Linux, Windows, `std::thread`)**, many-to-many (Go, Java virtual threads).
5. Linux: threads and processes are both tasks via `clone()` with different sharing flags.
6. `fork` in a multithreaded process copies only the calling thread; held locks can be stuck. Exec soon.
7. Concurrency = interleaving (possible on 1 core); parallelism = simultaneous execution (needs several cores).
8. Amdahl: speedup = 1 / ((1 − p) + p/n); the serial fraction caps it.
9. `std::thread` must be joined or detached; arguments are copied (use `std::ref`); `jthread` auto-joins.
10. `counter++` is load-add-store: unsynchronized concurrent increments lose updates (a data race = UB in C++).

### Common wrong answers (module)

- "A thread is a lightweight process", with nothing else.
- "Threads have their own heap." (They share the heap; each has its own *stack*.)
- "If one thread crashes, the others continue." (A segfault kills the whole process.)
- "User-level threads run in parallel on multiple cores."
- "Concurrency and parallelism are the same."
- "`counter++` is atomic because it's one line of code."
- "8 cores means 8× speedup."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| Process vs thread? | Resource container with its own address space vs execution unit sharing it; cost, isolation, communication trade-offs | What exactly do threads share? |
| What do threads share / not share? | Share code, heap, globals, files; private stack, registers, PC, TID | Can a thread access another's stack? (Yes, same address space; unsafe) |
| Why are threads cheaper? | No new address space; a thread switch doesn't change page tables | When would you prefer processes? |
| User vs kernel threads? | Library-managed (cheap, no parallelism, blocking blocks all) vs kernel-scheduled (parallel) | Threading models? |
| Concurrency vs parallelism? | Interleaved progress vs simultaneous execution | Can you have concurrency on one core? |
| What happens if one thread segfaults? | The whole process is terminated | How does Chrome isolate tabs? (Processes) |
| `fork` in a multithreaded program? | Only the calling thread is copied; locks may be stuck; exec soon | |
| Amdahl's law? | Speedup is limited by the serial fraction | Calculate for p = 0.9, n = 8 (≈ 4.7) |
| Why is `counter++` unsafe across threads? | Load-add-store interleavings lose updates | How to fix it? (atomic, mutex, local accumulation) |

### Practice

**P1.** For each item, say whether two threads of the same process share it: (a) a global `int`, (b) a local `int` in a function both are running, (c) an object created with `new` in one thread whose pointer is given to the other, (d) the file descriptor for an open log file, (e) the program counter, (f) a `static` local variable.

<details><summary>Answer</summary>

(a) shared, (b) **not** shared (each thread has its own stack frame, so its own copy), (c) shared (heap), (d) shared, (e) not shared, (f) **shared** (statics live in data/BSS, one copy per process). That makes it a race risk, apart from C++11's thread-safe *initialisation* of static locals.
</details>

**P2.** A program is 75% parallelisable. What's the maximum speedup on 4 cores, and on unlimited cores?

<details><summary>Answer</summary>

4 cores: 1 / (0.25 + 0.75/4) = 1 / 0.4375 ≈ **2.29×**. Unlimited: 1 / 0.25 = **4×**.
</details>

**P3.** What's wrong with this code?
```cpp
void start() {
    int data = 42;
    std::thread t([&] { std::cout << data; });
    t.detach();
}
```
<details><summary>Answer</summary>

The lambda captures `data` **by reference**, and the thread is **detached**. `start()` may return, destroying `data`, before the thread reads it: a dangling reference and undefined behaviour. Fix: capture by value (`[data]`) or `join()` before returning.
</details>

**P4.** Explain why a user-level-thread library can't make use of 4 cores, and why one blocking `read()` stalls every thread.

<details><summary>Answer</summary>

The kernel sees the whole process as **one** schedulable entity (one kernel thread), so it runs on one core at a time. When any user thread makes a blocking system call, the kernel blocks that single kernel thread, and with it every user thread multiplexed on it. Runtimes like Go solve this with M:N scheduling plus non-blocking I/O under the hood.
</details>

**P5.** Fix the racy counter in three different ways, and say which one is fastest and why.

<details><summary>Answer</summary>

(1) `std::atomic<int> counter;`. (2) A `std::mutex` with `lock_guard` around `counter++`. (3) Each thread increments a **local** variable and adds it to the shared total once at the end (under a lock or atomically). **(3) is fastest**: there's no contention per increment. Atomics are next (still cache-line contention between cores on every increment). The mutex per increment is slowest.
</details>

---

## Exit checklist

```
[ ] I can deliver the process vs thread answer in ~45 s with the shared/private split
[ ] I can draw the shared-vs-private diagram
[ ] I can say when to prefer processes vs threads, with real examples
[ ] I can compare user-level vs kernel-level threads and the three models (with modern examples)
[ ] I can explain how Linux implements threads (clone flags)
[ ] I can answer "what happens on fork in a multithreaded program"
[ ] I can distinguish concurrency/parallelism and the multi- terms
[ ] I can compute Amdahl's law speedups
[ ] I can write std::thread code correctly (join/detach, std::ref) and explain jthread
[ ] I can explain why counter++ loses updates, with the interleaving diagram
[ ] P1–P5 done
```

---

## Next

**Part 5: M3 — CPU Scheduling.** It covers scheduling criteria and formulas, preemptive vs non-preemptive, FCFS (and the convoy effect), SJF and SRTF, Priority (and starvation and aging), Round Robin (choosing the quantum), multilevel and multilevel feedback queues, with a worked Gantt-chart numerical for every algorithm and a short note on how Linux actually schedules.
