# Operating Systems Placement Handbook — Part 3
# Module 1: Processes

**Module 1 · 3–4 hours · Tier 1 · Requires: M0**

---

## Why this module is the foundation

"Process" is the OS's central abstraction, and the questions built on it are some of the most frequently asked: program vs process, process states, PCB, context switch, `fork()` output, zombie vs orphan. Every later module refers back to it. Scheduling decides which *process* runs, synchronization coordinates *processes and threads*, and memory management gives each *process* its own address space.

The organising principle:

> **A process is a program in execution: code plus everything the OS needs to pause it and resume it later as if nothing happened, meaning its registers, memory map, open files and state. That "everything" is stored in the PCB. A context switch saves one PCB and loads another. Every process concept is a variation on "save state, restore state".**

---

## 1.1 Program vs process

### 1. What is it?

| | Program | Process |
|---|---|---|
| What | A **passive** file on disk containing instructions (an executable) | An **active** instance of a program **in execution** |
| Lives in | Storage | Memory, plus CPU registers when running |
| Lifetime | Permanent until deleted | Created, runs, terminates |
| Resources | None | CPU time, memory, open files, I/O devices |
| Multiplicity | One file | **Many processes can run the same program** (three terminal windows = three `bash` processes, one `/bin/bash` file) |
| State | None | Program counter, registers, stack, heap, process state |

**Analogy:** a program is a recipe; a process is someone cooking it. Three cooks can follow the same recipe at once, each at a different step with their own ingredients.

### 2. Process types (vocabulary)

| Type | Meaning |
|---|---|
| **CPU-bound** | Spends most of its time computing (video encoding, compiling); long CPU bursts |
| **I/O-bound** | Spends most of its time waiting for I/O (editors, web servers); short CPU bursts |
| **Foreground / background** | Attached to a terminal and interactive / not |
| **Daemon** (Unix) / **service** (Windows) | A background process that provides a system service (`sshd`, `cron`) |

The CPU-bound vs I/O-bound distinction matters for scheduling (M3): good schedulers favour I/O-bound processes so that devices stay busy.

---

## 1.2 Process memory layout

### 1. The picture (Linux, typical)

```
 high addresses
 +--------------------------+
 |  kernel space            |  mapped in every process, inaccessible from user mode
 +--------------------------+
 |  command-line args, env  |
 +--------------------------+
 |  STACK                   |  local variables, function parameters, return addresses
 |    | grows DOWN          |  one per THREAD (M2)
 |    v                     |
 |                          |
 |  memory-mapped region    |  shared libraries (libc.so), mmap'd files, thread stacks
 |                          |
 |    ^                     |
 |    | grows UP            |
 |  HEAP                    |  dynamic allocation: malloc / new
 +--------------------------+
 |  BSS                     |  UNinitialised (zero-initialised) globals/statics: int count;
 +--------------------------+
 |  DATA                    |  INITIALISED globals/statics: int limit = 100;
 +--------------------------+
 |  TEXT (code)             |  machine instructions; read-only, shareable between processes
 +--------------------------+
 low addresses
```

### 2. Which segment holds what? (a quick drill)

```cpp
int a = 10;            // DATA (initialised global)
int b;                 // BSS  (uninitialised global, zero-filled)
static int c = 5;      // DATA
const char* s = "hi";  // pointer s in DATA; the literal "hi" in a read-only data section
int main() {
    int x = 1;         // STACK
    static int y;      // BSS  (static local, uninitialised)
    int* p = new int;  // p on the STACK; the int it points to on the HEAP
}
```

### 3. Why BSS exists separately from DATA

Initialised data must be stored **in the executable file** (the initial values have to come from somewhere). Uninitialised data needn't be: the file records only "this much zeroed space", and the OS provides zero-filled pages at load time. A program with `int big[10'000'000];` as a global doesn't produce a 40 MB executable.

### 4. Must remember

1. Text (code, read-only) → data → BSS → heap (grows up) → … → stack (grows down).
2. Heap and stack grow toward each other. Stack overflow = runaway recursion hitting the stack limit (often 8 MB by default on Linux).
3. Text segments of the same program can be **shared** between processes (read-only).
4. Each **thread** has its own stack; all threads share the heap, data and text (M2).

---

## 1.3 The Process Control Block (PCB)

### 1. What is it?

The kernel data structure that represents a process: **everything needed to suspend and resume it**. On Linux it's `struct task_struct`.

### 2. Contents (asked as a list)

| Field group | Contents |
|---|---|
| **Identification** | PID, parent PID, user and group IDs |
| **Process state** | New / Ready / Running / Waiting / Terminated |
| **CPU context** | **Program counter**, stack pointer, general-purpose registers, flags; saved here when the process is not running |
| **Scheduling info** | Priority, scheduling-queue pointers, CPU time used, time-slice info |
| **Memory-management info** | Page-table base pointer, memory limits / segment info |
| **I/O and file info** | **Open file table** (file descriptors), pending I/O requests, current directory |
| **Accounting** | CPU time used, start time, resource limits |
| **Signal / IPC info** | Pending signals, signal handlers |
| **Links** | Parent, children, pointers for queues |

### 3. Must remember

1. PCB = the process's identity + saved CPU context + resources + scheduling and memory info.
2. The **program counter and registers** are saved into the PCB on a context switch.
3. PCBs live in **kernel memory**, which a process can't modify directly.
4. Linux: `task_struct`; it's used for threads too (M2).

---

## 1.4 Process states

### 1. The five-state model (draw this in the interview)

```
             admitted                 dispatch (scheduler picks it)
   [NEW] -------------> [READY] ---------------------------------> [RUNNING] ----exit----> [TERMINATED]
                          ^   ^                                       |   |
                          |   |      interrupt / time slice expired   |   |
                          |   +---------------------------------------+   |
                          |                                               |  I/O request or
                          |   I/O completes / event occurs                |  wait for an event
                          +------------------[WAITING / BLOCKED]<---------+
```

| State | Meaning |
|---|---|
| **New** | Being created (PCB allocated, not yet admitted to the ready queue) |
| **Ready** | Has everything except the CPU; waiting in the ready queue |
| **Running** | Executing on a CPU (at most one process per core) |
| **Waiting (Blocked)** | Can't continue until an event: I/O completion, a lock, a signal, a child's exit |
| **Terminated** | Finished; its PCB may linger until the parent collects the exit status (zombie, §1.8) |

### 2. The transitions, and what causes each

| Transition | Cause |
|---|---|
| New → Ready | The OS admits the process (long-term scheduler) |
| Ready → Running | The **short-term scheduler** dispatches it |
| Running → Ready | **Preemption**: the time slice expires (timer interrupt) or a higher-priority process becomes ready |
| Running → Waiting | The process requests I/O, waits for a lock, `sleep()`s, `wait()`s for a child |
| Waiting → Ready | The event occurs (device interrupt signals I/O completion, lock released) |
| Running → Terminated | `exit()`, return from `main`, or killed by a signal |

**Trick question: "Can a process go directly from Waiting to Running?"** **No.** When the event occurs it moves to **Ready**, and must be dispatched by the scheduler like any other ready process. **"From Ready to Waiting?"** **No.** Only a *running* process can request I/O or block on something, because it has to be executing to make the request.

### 3. Suspended states (the seven-state model, briefly)

When memory is short, the **medium-term scheduler** may swap a process out to disk, giving **Ready-Suspended** and **Blocked-Suspended** states. Mention them if asked "what is swapping?" or "what is the medium-term scheduler?".

### 4. Queues and schedulers

```
   job queue (all processes) --long-term--> READY QUEUE --short-term--> CPU
                                               ^   \
                                               |    \ I/O request
                                               |     v
                                               +-- DEVICE QUEUES (one per device / event)
```

| Scheduler | Decides | Runs | Controls |
|---|---|---|---|
| **Long-term** (job scheduler) | Which new jobs are admitted to memory | Rarely (seconds/minutes) | **Degree of multiprogramming**; the CPU-bound vs I/O-bound mix |
| **Short-term** (CPU scheduler) | Which ready process runs next | **Very often** (milliseconds), so it must be fast | CPU allocation (M3) |
| **Medium-term** | Which processes to swap out or back in | Occasionally | Memory pressure, thrashing (M7) |

Modern general-purpose OSes have essentially no long-term scheduler (every program you launch is admitted). The short-term scheduler is the one that matters.

### 5. Must remember

1. Five states: New, Ready, Running, Waiting, Terminated.
2. Running → Ready = **preemption**; Running → Waiting = **blocking**; Waiting → Ready = **event done**.
3. No direct Waiting → Running, and no Ready → Waiting.
4. Short-term (frequent, fast), long-term (degree of multiprogramming), medium-term (swapping).

---

## 1.5 Context switch

### 1. What is it?

**Saving the state of the currently running process (or thread) and restoring the saved state of the next one**, so the CPU can switch between them and each resumes exactly where it stopped.

### 2. When does it happen?

- A **timer interrupt** ends the time slice (preemption).
- The running process **blocks** (I/O, lock, sleep).
- A higher-priority process becomes ready (in preemptive schedulers).
- The running process **exits**.

(A **system call by itself is a mode switch, not a context switch**: the same process just enters kernel mode. A context switch happens only if the kernel then decides to run a different process.)

### 3. The steps

```
  Process A running
     |  timer interrupt (or A blocks)
     v
  1. CPU enters kernel mode; A's user registers saved
  2. Kernel saves A's full CPU context into PCB(A); A.state = READY (or WAITING)
  3. Scheduler picks B from the ready queue
  4. Kernel loads B's context from PCB(B); switches the ADDRESS SPACE
     (page-table base register -> B's page table)
  5. B.state = RUNNING; return-from-interrupt into B's user code
     |
     v
  Process B running (as if it never stopped)
```

### 4. Why it's expensive (the real follow-up)

| Cost | Kind | Explanation |
|---|---|---|
| Save and restore registers, run the scheduler | **Direct** | Pure overhead: no user work is done meanwhile |
| Switch page tables | Direct | Change the address space |
| **TLB flush / misses** | **Indirect** | Translation caches belong to the old address space; tagging with ASIDs/PCIDs avoids a full flush, but the new process still starts cold |
| **CPU cache pollution** | **Indirect**, often the biggest | B's data isn't in the L1/L2 caches; many cache misses after the switch |
| Pipeline flush, branch-predictor state | Indirect | Lost speculative work and predictions |

**Typical order of magnitude:** the direct cost is around a microsecond or a few microseconds on modern hardware; the indirect costs from cold caches can be larger and depend heavily on the workload. **Context switching is pure overhead.** That's why time slices can't be made arbitrarily small (Round Robin quantum, M3).

### 5. Process switch vs thread switch

| | Process context switch | Thread context switch (same process) |
|---|---|---|
| Registers, PC, stack pointer | Saved and restored | Saved and restored |
| Address space (page tables) | **Switched** | **Not switched** (shared) |
| TLB impact | Large | Small |
| Cost | Higher | **Lower** |

This is one of the main reasons threads are "lighter" than processes (M2).

### 6. Mode switch vs context switch (asked often)

| | Mode switch | Context switch |
|---|---|---|
| What changes | CPU privilege mode (user ↔ kernel) | Which **process/thread** runs |
| Example | Every system call | Time slice expiry, blocking on I/O |
| Same process before and after? | **Yes** | **No** |
| Cost | Lower | Higher (includes a mode switch plus much more) |

### 7. Must remember

1. Context switch = save PCB(A) + scheduler + load PCB(B) + address-space switch.
2. Triggered by timer interrupts, blocking, preemption or exit, **not** by a system call alone.
3. Costs: direct (registers, scheduler) + indirect (TLB, caches, pipeline); pure overhead.
4. A thread switch within one process is cheaper (no address-space change).

### 8. Interview question

- *"What is a context switch and why is it expensive?"* Saving the running process's CPU state into its PCB and loading another's, including switching the address space. It's overhead because no useful work happens meanwhile, and the indirect costs (flushed TLB entries and cold caches for the new process) often exceed the direct cost of saving registers. *Follow-up: "Is a thread switch cheaper?"* Yes. Threads of the same process share the address space, so there's no page-table switch and less TLB disruption.

---

## 1.6 Process creation: `fork`, `exec`, `wait`

### 1. `fork()`

Creates a **new process (the child) that is a near-exact copy of the caller (the parent)**: same code, a copy of the data, heap and stack, a copy of the file-descriptor table, and the same program counter. Both continue from the instruction after `fork()`.

**Return value, which is the only way to tell them apart:**

| Returned to | Value |
|---|---|
| Parent | The **child's PID** (> 0) |
| Child | **0** |
| Parent, on failure | **−1** (no child is created) |

```c
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main(void) {
    int x = 5;
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");                         // failed: no child exists
        return 1;
    } else if (pid == 0) {
        x++;                                    // child modifies ITS copy
        printf("child: x=%d pid=%d parent=%d\n", x, getpid(), getppid());
    } else {
        x--;                                    // parent modifies ITS copy
        wait(NULL);                             // wait for the child to finish
        printf("parent: x=%d child=%d\n", x, pid);
    }
    return 0;
}
// Output (the child prints first here because the parent waits):
// child: x=6 pid=<child pid> parent=<parent pid>
// parent: x=4 child=<child pid>
```

**After `fork`, parent and child have separate address spaces.** A change to `x` in one is invisible to the other. That's the first thing fork questions test.

**What the child inherits vs not:**

| Inherited (copied) | Not inherited / different |
|---|---|
| Memory contents (text, data, heap, stack) | PID (new), parent PID |
| Open file descriptors (**sharing the same file offsets**) | Pending signals (cleared) |
| Current directory, environment, user IDs | Resource-usage counters (reset) |
| Signal handlers | File locks held by the parent (`fcntl` locks) |
| | Only the **calling thread** is copied in a multithreaded process (M2) |

### 2. Copy-on-write (COW): why `fork` is cheap

Copying gigabytes of memory on every `fork` would be wasteful, especially since the child usually calls `exec` immediately and throws the copy away. Instead:

1. `fork` copies only the **page tables**, and marks every page **read-only** in both processes, shared.
2. When either process **writes** to a page, the CPU raises a page fault (M7); the kernel then **copies just that page**, gives the writer its private copy, and makes it writable.
3. Pages never written are never copied.

So `fork` costs roughly the size of the page tables, not of the memory. (Historical: `vfork` was a cheaper `fork` from before COW; the child borrowed the parent's memory until `exec`.)

### 3. `exec()`: replace the program

The `exec` family **replaces the current process's memory image with a new program**. Same PID, new code, data, heap and stack. **On success it never returns**, because the code that called it no longer exists.

| Variant letters | Meaning |
|---|---|
| `l` (`execl`) | Arguments as a **list**: `execl(path, arg0, arg1, ..., NULL)` |
| `v` (`execv`) | Arguments as a **vector** (array): `execv(path, argv)` |
| `p` (`execlp`, `execvp`) | Search the **PATH** for the program name |
| `e` (`execle`, `execve`) | Pass an explicit **environment** |

`execve` is the actual system call; the others are library wrappers.

### 4. `wait()` / `waitpid()`

The parent **blocks until a child terminates** and collects its **exit status**, which also frees the child's remaining kernel entry (§1.8).

### 5. The fork + exec + wait pattern (how a shell runs a command)

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>

// Roughly what a shell does for:  ls -l > out.txt
int main(void) {
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); exit(1); }

    if (pid == 0) {                                   // CHILD
        int fd = open("out.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd < 0) { perror("open"); _exit(1); }
        dup2(fd, STDOUT_FILENO);                      // redirect stdout to the file...
        close(fd);
        execlp("ls", "ls", "-l", (char*)NULL);        // ...then become 'ls' (keeps the fds)
        perror("execlp");                             // reached ONLY if exec failed
        _exit(127);                                   // _exit: don't flush stdio buffers twice
    }

    int status;                                       // PARENT (the shell)
    waitpid(pid, &status, 0);
    if (WIFEXITED(status))
        printf("child exited with %d\n", WEXITSTATUS(status));
    return 0;
}
```

**Why are `fork` and `exec` separate calls?** Between them, the child can **set up its environment**: redirect file descriptors (`dup2`), change directory, change user, close files, set limits. The new program inherits all of it without knowing. This is how shells implement `>`, `<` and `|`. That makes for a strong interview answer. (Windows' `CreateProcess` combines both into one call with many parameters.)

**Why `_exit` in the child after a failed `exec`?** `exit()` flushes stdio buffers; the child inherited a copy of the parent's unflushed buffer, so `exit` could print the parent's pending output a second time. `_exit` terminates immediately.

### 6. `fork` vs `exec`

| | `fork()` | `exec()` |
|---|---|---|
| Creates a new process | **Yes** | **No** |
| PID | New PID for the child | **Same PID** |
| Program | Same program (a copy) | **Different program** replaces the current one |
| Returns | Twice (0 in the child, the PID in the parent) | **Never** on success; −1 on failure |
| Typical use | Together: `fork`, then `exec` in the child | |

---

## 1.7 `fork()` output drills

These counts were checked with a simulator that enumerates every process as its unique sequence of `fork()` results.

### The rule

**Each `fork()` executed by k processes produces k new processes.** n `fork()` calls in sequence (with no conditions) give **2ⁿ processes** in total, that is **2ⁿ − 1 children**.

**F1.**
```c
fork(); fork();
printf("hi\n");
```
<details><summary>Answer</summary>

**4** lines. 1 → 2 → 4 processes; each prints once.
</details>

**F2.**
```c
for (int i = 0; i < 3; i++) fork();
printf("x\n");
```
<details><summary>Answer</summary>

**8**: 2³ processes. 7 of them are new (children).
</details>

**F3.**
```c
int x = 5;
if (fork() == 0) x++; else x--;
printf("%d\n", x);
```
<details><summary>Answer</summary>

Prints **6** (child) and **4** (parent), in either order. Separate address spaces.
</details>

**F4.**
```c
if (fork() && fork()) fork();
printf("x\n");
```
<details><summary>Answer</summary>

**4** processes. `&&` short-circuits:
- Original P: first `fork()` returns the child's PID (true), so P evaluates the second `fork()`.
  - P's first child C1 gets 0 (false), so it skips the rest.
  - The second `fork()` creates C2, which gets 0 (false), so it skips `fork()` #3. P gets true, so P runs `fork()` #3, creating C3.
- Processes: P, C1, C2, C3 → **4 prints**.
</details>

**F5.**
```c
fork() || fork();
printf("x\n");
```
<details><summary>Answer</summary>

**3** processes. In P, the first fork returns non-zero (true), so `||` short-circuits. In the child C1, it returns 0 (false), so C1 runs the second `fork()`, creating C2. Processes: P, C1, C2.
</details>

**F6 (the classic).**
```c
fork();
fork() && fork() || fork();
fork();
printf("x\n");
```
<details><summary>Answer</summary>

**20**. The middle line is `(fork() && fork()) || fork()`. Starting from **one** process, it produces **5**:
- A = first fork. Parent (A true) evaluates B:
  - B parent (true): `A && B` is true → skips C. **(1 process)**
  - B child (false): evaluates C → creates 1 more → **(2 processes)**
- A child (A false, B skipped): evaluates C → **(2 processes)**
- Total: 1 + 2 + 2 = 5.

So: 1 → (fork) 2 → (×5) 10 → (fork) **20**.
</details>

**F7 (the buffering trap).**
```c
printf("A");          // note: NO newline
fork();
printf("B\n");
```
<details><summary>Answer</summary>

**`AB` is printed twice**, so "A" appears twice even though `printf("A")` ran only once. "A" sat in the **stdio buffer** (no newline, so a line-buffered terminal hadn't flushed it), and `fork` copied the buffer into the child. Both processes later flush `"A" + "B\n"`.

With `printf("A\n")` and output to a **terminal**: "A" appears once (flushed at the newline). With output **redirected to a file** (fully buffered): "A" appears **twice** even with the newline. The fix is `fflush(stdout)` before `fork()`.
</details>

**F8.**
```c
for (int i = 0; i < 2; i++) {
    fork();
    printf("-");      // no newline
}
```
<details><summary>Answer</summary>

**8 dashes**, not 6. Counting *executions* of `printf`: 2 processes at i=0 plus 4 at i=1 = 6. But without a newline, the "-" printed at i=0 is still in the buffer when the second `fork` copies it, so the 4 final processes each flush "--": 4 × 2 = **8**. With `printf("-\n")` to a terminal, it's **6**. (This is a well-known placement question.)
</details>

**F9.** How many **child** processes does `for (i = 0; i < n; i++) fork();` create?
<details><summary>Answer</summary>

**2ⁿ − 1** (2ⁿ processes in total, minus the original).
</details>

---

## 1.8 Zombie and orphan processes

### 1. Zombie (defunct) process

A process that **has terminated, but whose parent hasn't yet called `wait()`** to collect its exit status.

- Its memory and resources are **freed**; only the **process-table entry** (PID + exit status) remains, kept so the parent can read it.
- Shown by `ps` as state **`Z`** or `<defunct>`.
- **A few are harmless** (every child is briefly a zombie). **Many are a problem**: they use up PIDs and process-table slots, so new processes eventually can't be created.
- **You can't kill a zombie**: it's already dead. You make the parent reap it, or kill the parent (then init adopts and reaps it).

**Fixes:** the parent calls `wait`/`waitpid`; or it handles **`SIGCHLD`** (sent to the parent when a child exits) and reaps in the handler; or it sets `SIGCHLD` to `SIG_IGN` (Linux then reaps automatically).

### 2. Orphan process

A process whose **parent terminated while it was still running**.

- It is **re-parented** (adopted) by **init / systemd, PID 1** (or a designated "subreaper" process), which periodically `wait`s on its children.
- Orphans keep running normally. **Not harmful.**
- Daemons are created as orphans *deliberately* (the double-fork technique) so they detach from the terminal.

### 3. Comparison

| | Zombie | Orphan |
|---|---|---|
| Child's state | **Terminated** | **Still running** |
| Parent's state | Alive, but hasn't called `wait()` | **Terminated** |
| Resources held | Only the process-table entry (PID, exit status) | All its normal resources (it's alive) |
| Who cleans up | The parent (`wait`) | Adopted by **init (PID 1)**, which reaps it when it exits |
| Harmful? | Only in large numbers (PID exhaustion) | No |
| `ps` state | `Z` / `<defunct>` | Normal states; PPID becomes 1 (or the subreaper's PID) |

**Can a process be both?** In sequence, yes: an orphan is adopted by init, and when it exits it's briefly a zombie until init reaps it, which happens almost immediately.

### 4. Interview line

*"A zombie is a child that has exited but whose parent hasn't called wait(), so its PID and exit status stay in the process table; many of them can exhaust PIDs, and the fix is reaping via wait or a SIGCHLD handler. An orphan is a child whose parent died while it was still running; init, PID 1, adopts it and reaps it when it exits, so it's harmless."*

---

## 1.9 Process termination (briefly)

- **Normal:** `return` from `main` or `exit(status)`: flushes stdio buffers, runs `atexit` handlers, then `_exit`.
- **`_exit(status)`:** terminates immediately without flushing stdio (the system call).
- **Abnormal:** killed by a signal (`SIGKILL`, `SIGSEGV` from an invalid memory access, `SIGABRT` from `abort()`).
- **Cascading termination:** some systems kill a process's children when it dies. On Unix, children are **not** killed by default; they become orphans.
- **Exit status:** 0 = success, non-zero = failure; collected by the parent through `wait`.

---

## 1.10 Consolidation

### Must remember (module)

1. Program = passive file; process = program in execution with state. Many processes per program.
2. Layout: text → data → BSS → heap ↑ … ↓ stack. BSS isn't stored in the file.
3. PCB (`task_struct`): PID, state, PC + registers, scheduling, memory (page-table pointer), open files, accounting.
4. States: New, Ready, Running, Waiting, Terminated. No Waiting→Running, no Ready→Waiting.
5. Short-term scheduler (frequent), long-term (degree of multiprogramming), medium-term (swapping).
6. Context switch: save PCB, schedule, load PCB, switch address space. Direct + indirect (TLB, cache) costs. A system call alone is a mode switch, not a context switch.
7. `fork` returns 0 to the child, the PID to the parent, −1 on error; separate address spaces; COW makes it cheap.
8. `exec` replaces the image (same PID) and never returns on success. Separate fork/exec enables redirection.
9. n sequential forks → 2ⁿ processes; short-circuit `&&`/`||` changes the count; unflushed stdio buffers are duplicated by fork.
10. Zombie = dead child not yet reaped (fix: `wait`/`SIGCHLD`). Orphan = live child with a dead parent (adopted by PID 1).

### Common wrong answers (module)

- "A program and a process are the same."
- "A process goes from Waiting straight back to Running."
- "Every system call causes a context switch."
- "`fork` copies all memory immediately." (COW.)
- "The child shares the parent's variables after fork."
- "`exec` creates a new process."
- "You can kill a zombie with `kill -9`."
- "Orphans are killed when the parent dies."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| Program vs process? | Passive executable vs active instance with state and resources | Can one program have many processes? |
| Process memory layout? | Text, data, BSS, heap (up), stack (down) | Where do static locals go? |
| What is a PCB? | Kernel structure with everything needed to suspend and resume a process | What's saved on a context switch? |
| Process states? | New, Ready, Running, Waiting, Terminated + transitions | Can Waiting go directly to Running? |
| Context switch? | Save/restore process state + address-space switch; overhead | Why expensive? Thread vs process switch? |
| What does `fork` return? | 0 in the child, the child's PID in the parent, −1 on failure | Do they share memory? |
| `fork` vs `exec`? | New process (copy) vs replace the program (same PID) | Why separate? |
| What is COW? | Pages shared read-only after fork; copied on first write | Why does it matter? |
| Zombie vs orphan? | Dead, unreaped vs alive, parentless (adopted by PID 1) | How to prevent zombies? |
| Types of schedulers? | Long-, short- and medium-term | Which runs most often? |

### Practice

**P1.** Assign each to its segment (text, data, BSS, heap, stack):
`int g;` · `int h = 3;` · a local `char buf[64];` · `malloc(100)` · `static double d = 1.5;` inside a function · the code of `main`.
<details><summary>Answer</summary>

BSS · data · stack · heap (the pointer itself is on the stack) · data · text.
</details>

**P2.** A process is Running and calls `read()` on a socket with no data available. List its state transitions until it runs again after data arrives.
<details><summary>Answer</summary>

Running → (system call, data not available) **Waiting** → (NIC interrupt; the kernel copies the data and wakes the process) **Ready** → (the scheduler dispatches it) **Running**.
</details>

**P3.** How many times is "hello" printed?
```c
int main() { for (int i = 0; i < 4; i++) if (i % 2 == 0) fork(); printf("hello\n"); }
```
<details><summary>Answer</summary>

`fork` runs at i = 0 and i = 2 only: 2 sequential forks → **4** processes → **4** prints.
</details>

**P4.** A web server forks a child per request but never calls `wait()`. After a day it can't create new processes. Why, and what are two fixes?
<details><summary>Answer</summary>

Every finished child stays a **zombie**, holding a PID and a process-table slot, until the PID space or process limit is exhausted. Fixes: install a `SIGCHLD` handler that calls `waitpid(-1, &st, WNOHANG)` in a loop; or set `SIGCHLD` to `SIG_IGN` so the kernel auto-reaps. (A thread pool instead of fork-per-request also avoids the issue entirely.)
</details>

**P5.** Explain why `ls > out.txt` needs `fork` and `exec` to be separate system calls.
<details><summary>Answer</summary>

After `fork`, the child (still running shell code) opens `out.txt` and `dup2`s it onto file descriptor 1. Then it `exec`s `ls`, which inherits the redirected stdout without knowing. With a combined create-and-run call, the shell would need a parameter for every possible piece of setup.
</details>

---

## Exit checklist

```
[ ] I can distinguish program vs process with an analogy
[ ] I can draw the memory layout and place variables in segments
[ ] I can list PCB contents
[ ] I can draw the 5-state diagram with every transition and its cause
[ ] I can answer the Waiting->Running and Ready->Waiting trick questions
[ ] I can explain the three schedulers
[ ] I can describe a context switch step by step and its direct/indirect costs
[ ] I can distinguish a mode switch from a context switch
[ ] I know fork's return values, what is inherited, and how COW works
[ ] I can write fork + exec + wait with redirection and explain why fork/exec are separate
[ ] I can solve fork-count questions including && / || and the buffering trap
[ ] I can compare zombie vs orphan and give fixes for zombies
[ ] P1–P5 and F1–F9 done
```

---

## Next

**Part 4: M2 — Threads.** It answers the single most-asked OS question, **process vs thread**: what threads share, why they're cheaper, user-level vs kernel-level threads and threading models, concurrency vs parallelism, Amdahl's law, and C++ `std::thread` basics, including a data race you can run and watch go wrong.
