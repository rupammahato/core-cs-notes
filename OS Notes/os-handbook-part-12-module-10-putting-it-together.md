# Operating Systems Placement Handbook — Part 12
# Module 10: Putting It Together

**Module 10 · 1.5–2 hours · Tier 2 (integrative questions) / Tier 3 (virtualization) · Requires: M0–M9**

---

## Why this module exists

The strongest OS interviewers don't ask "define X". They ask **"what happens when…?"** and let you talk, probing wherever your explanation gets vague. These questions test whether the separate modules have joined into **one model of the machine**. This module rehearses the five that come up most, each as an end-to-end narrative with pointers back to the module that covers each step, followed by the virtualization questions (VMs vs containers) that now come up in passing at most product companies.

**How to answer these questions:** give the **skeleton** first (5–8 steps in one breath), then **go deep wherever the interviewer points**. Don't recite everything at the same depth; it takes too long and hides what you actually know.

The organising principle:

> **Every "what happens when" answer is the same few mechanisms in a new order: a trap into the kernel, a check against the process's credentials and memory map, a change to a table (page table, file table, process table), possibly a block-and-reschedule, and a return to user mode. Learn to see those mechanisms and you can answer questions you've never practised.**

---

## 10.1 What happens when you run `./a.out` in a shell

### The skeleton (say this first, in about 30 seconds)

*"The shell reads the command, forks a child, and the child calls execve. The kernel checks permissions, reads the ELF header, replaces the child's address space with mappings of the program's segments, sets up the stack with argv and the environment, and, for a dynamic executable, starts the dynamic linker, which maps libc and resolves symbols. Control reaches `_start`, then libc's startup, then `main`. Pages load lazily through page faults; the scheduler time-slices it with everything else; output goes through write system calls to the terminal driver. On exit the kernel frees its resources, the process becomes a zombie, and the shell's wait reaps it and prints the next prompt."*

### The deep version, step by step

| # | Step | What actually happens | Module |
|---|---|---|---|
| 1 | **Shell reads the line** | The shell is blocked in `read()` on the terminal; you press Enter; the tty driver gets a keyboard **interrupt**, buffers the line and wakes the shell (Waiting → Ready) | M0 §0.4, M1 §1.4 |
| 2 | **Parse and look up** | `./a.out` contains a slash, so no PATH search; the shell checks for builtins | — |
| 3 | **`fork()`** | The kernel creates a child: a new PID and PCB, **copies the page tables with copy-on-write**, copies the fd table (stdin, stdout and stderr still point at the terminal) | M1 §1.6, M7 §7.5 |
| 4 | **Child calls `execve("./a.out", argv, envp)`** | A **trap** into the kernel | M0 §0.3 |
| 5 | **Kernel validates** | Path lookup (directory entries → **inode**), checks the **execute permission** bit, and reads the first bytes: the **ELF magic** (`\x7fELF`) identifies the format | M8 §8.6 |
| 6 | **Tear down the old image** | The child's copy of the shell's address space is discarded (thanks to COW, almost nothing was ever copied) | M7 |
| 7 | **Map the new image** | Text segment `mmap`ed **read + execute** from the file, data segment **read + write (private)**, **BSS** mapped to zero-fill-on-demand pages, a fresh **heap** (`brk`) and **stack** created. **Nothing is read from disk yet**: these are just page-table and memory-map entries | M1 §1.2, M7 §7.10 |
| 8 | **Build the initial stack** | `argc`, `argv` strings, `envp`, and the auxiliary vector are pushed onto the new stack | M1 |
| 9 | **Dynamic linking** (most programs) | The ELF names an **interpreter** (`/lib64/ld-linux-x86-64.so.2`). The kernel starts it first; it `mmap`s **shared libraries** (libc, libstdc++) (their text pages are **shared** with every other process using them) and applies relocations, typically **lazy binding** through the PLT/GOT | M6 §6.4 (sharing) |
| 10 | **Return to user mode at the entry point** | `execve` **never returns** to the old code; the CPU starts at `_start` → `__libc_start_main` → **C++ global constructors** run (OOP M1 §1.5) → `main(argc, argv, envp)` | M0 §0.2 |
| 11 | **Running** | The first touch of every code, data or stack page → a **page fault** → loaded from the page cache or disk (minor or major fault). The **scheduler** gives it time slices; the **timer interrupt** preempts it; it **blocks** on I/O | M7 §7.3, M3 |
| 12 | **`printf("hi\n")`** | Formats into the **stdio buffer** (stdout to a terminal is line-buffered, so the newline flushes) → **`write(1, …)` system call** → the tty driver → the terminal emulator draws it | M0 §0.3, M9 |
| 13 | **`return 0` from `main`** | `exit(0)`: **C++ static destructors**, `atexit` handlers, flush the stdio buffers → **`exit_group` system call** | M1 §1.9 |
| 14 | **Kernel cleanup** | Frees the address space (frames whose share count hits zero), **closes all fds**, releases locks; the process becomes a **zombie** holding only its exit status; **SIGCHLD** is sent to the shell | M1 §1.8, M9 §9.6 |
| 15 | **Shell reaps it** | The shell was blocked in **`waitpid()`**; it wakes, collects the status (into `$?`), the zombie disappears, and the shell prints the prompt and blocks in `read()` again | M1 |

### Likely deep-dive follow-ups

- *"Why fork and then exec instead of one call?"* So the child can redirect its fds between them (M1 §1.6).
- *"Is the whole program loaded into memory at exec?"* No. It's mapped, and **demand paging** loads pages as they're touched.
- *"Why is the second run faster?"* The executable and the libraries are already in the **page cache**, so the page faults are minor (no disk I/O).
- *"What's `ld-linux.so`?"* The dynamic linker/loader; statically linked binaries skip it.
- *"Where do C++ global constructors run?"* Before `main`, called from libc's startup code.

---

## 10.2 What happens when you press Ctrl+C

```
 1. Keyboard interrupt -> keyboard driver -> TERMINAL (tty) line discipline
 2. The line discipline recognises the special INTR character (Ctrl+C, configurable: stty -a)
 3. The kernel sends SIGINT to every process in the terminal's FOREGROUND PROCESS GROUP
    (not just one process: a whole pipeline like  cat f | grep x | wc  gets it)
 4. Each process: if it has a SIGINT handler, the handler runs (e.g. save state, set a stop flag);
    otherwise the DEFAULT action = terminate
 5. The terminated processes become zombies -> the shell's waitpid() reaps them -> new prompt
 The shell itself survives: it is NOT in the foreground group while a job runs (and it ignores SIGINT)
```

Related: **Ctrl+Z** sends **SIGTSTP** (stop; then `fg`/`bg` with SIGCONT); **Ctrl+\\** sends **SIGQUIT** (core dump); **Ctrl+D** is **not a signal**, it's an end-of-file condition on the terminal's input (`read` returns 0).

---

## 10.3 What happens when you call `malloc(1 GB)` and then use it

```
 1. malloc sees a large request (glibc default threshold 128 KB) -> an anonymous mmap() system call
 2. The kernel creates a VIRTUAL memory area of 1 GB. No physical frames are assigned,
    page-table entries are "not present". With overcommit (Linux default), this succeeds even if
    free RAM is smaller
 3. malloc returns immediately. Cheap: no memory was actually used yet
 4. The program writes to p[0] -> PAGE FAULT -> the kernel assigns ONE zeroed frame, maps it, and
    restarts the instruction
 5. Touching all 1 GB -> ~262,144 page faults (4 KB pages): RSS grows gradually
    (huge pages: far fewer faults and TLB misses)
 6. If RAM + swap run out while touching it -> heavy swapping / thrashing, then the OOM KILLER
    picks a victim (possibly this process): "Killed" with no C++ exception
 7. free(p) -> munmap() -> the frames go back to the kernel immediately
    (small allocations, by contrast, return to malloc's free lists and are reused within the process)
```

Modules: M0 (`malloc` vs system calls), M7 §7.2–7.4, §7.10, M6 (TLB, huge pages).

**Follow-up: "Why didn't `new` throw `bad_alloc`?"** Because the virtual allocation succeeded. The failure happens later, at the first touch, as an OOM kill. That's overcommit.

---

## 10.4 Why is my multithreaded program slower than the single-threaded one?

A favourite product-company question, because the answer touches scheduling, synchronization and memory at once.

| Cause | Mechanism | Fix | Module |
|---|---|---|---|
| **Lock contention** | Threads spend their time waiting for one mutex, so the work is effectively serial, plus sleep/wake costs | Finer-grained locks, per-thread data + a final merge, lock-free/atomics, shorter critical sections | M4 |
| **False sharing** | Different threads write **different variables on the same 64-byte cache line**; the line bounces between cores (cache-coherence traffic) | Pad or align the hot variables to separate cache lines (`alignas(64)`); per-thread accumulators | below |
| **Oversubscription** | More runnable threads than cores → constant context switches, cold caches | Thread pool sized to the core count (CPU-bound work) | M2 §2.6, M1 §1.5 |
| **Amdahl's law** | The serial fraction dominates; the threading overhead exceeds the parallel gain for small work | Parallelise only large enough work; reduce serial sections | M2 §2.5 |
| **Memory bandwidth** | All cores stream data from RAM, so the bus is saturated | Improve locality, block/tile the computation | M6 |
| **Thread creation cost** | Spawning a thread per small task | Thread pool | M2 |
| **Hidden locks** | `malloc`, I/O streams (`cout`), and logging take global locks | Thread-local buffers; scalable allocators | M4 |

### False sharing, measured

```cpp
struct Packed { atomic<long long> a{0}; atomic<long long> b{0}; };                       // same cache line
struct Padded { alignas(64) atomic<long long> a{0}; alignas(64) atomic<long long> b{0}; };  // separate lines

// two threads; thread 1 increments ONLY .a, thread 2 ONLY .b, 50,000,000 times each
// (the threads never touch the same VARIABLE, so there's no race and no lock)
```

**Measured on the machine these notes were prepared on** (g++ 12, `-O2`, three runs):

```
sizeof Packed=16 Padded=128
same line: 1118 ms   separate lines: 220 ms
same line: 1061 ms   separate lines: 218 ms
same line: 1115 ms   separate lines: 294 ms
```

**About 4–5× slower** purely because two independent counters shared a cache line. The CPU's cache-coherence protocol (MESI) gives a core **exclusive** ownership of a whole line before it can write, so each write by one core invalidates the other core's copy, even though they never touch the same variable. (Exact ratios vary by CPU; the effect is always large.)

---

## 10.5 How does the OS isolate processes from each other?

| Mechanism | Prevents | Module |
|---|---|---|
| **Separate virtual address spaces** (per-process page tables) | Reading or writing another process's memory: it can't even name it | M6, M7 |
| **User vs kernel mode** | Executing privileged instructions, touching devices or page tables directly | M0 §0.2 |
| **Page protection bits** (R/W/X, user/supervisor) | Writing code pages, executing data (NX), user access to kernel pages | M6 §6.4 |
| **System-call validation** | Passing kernel pointers or other processes' handles in arguments | M0 §0.3 |
| **Timer interrupt + preemptive scheduling** | Monopolising the CPU | M0, M3 |
| **User IDs and permissions** on files and processes | Accessing others' files, or signalling others' processes | M8 |
| **Per-process fd tables** | Using another process's open files | M8 §8.3 |
| **Resource limits** (`ulimit`, cgroups) | Exhausting memory, CPU or PIDs for everyone | §10.6 |

**One line:** *"Hardware enforces it: user mode prevents privileged instructions, per-process page tables mean a process can't address another's memory, and the timer interrupt guarantees the kernel regains the CPU. The kernel then enforces permissions on everything shared, like files and signals."*

---

## 10.6 Virtual machines vs containers (Tier 3)

### 1. The picture

```
        VIRTUAL MACHINES                             CONTAINERS
 +---------+ +---------+ +---------+       +---------+ +---------+ +---------+
 |  App A  | |  App B  | |  App C  |       |  App A  | |  App B  | |  App C  |
 | bins/lib| | bins/lib| | bins/lib|       | bins/lib| | bins/lib| | bins/lib|
 |GUEST OS | |GUEST OS | |GUEST OS |       +---------+ +---------+ +---------+
 | (kernel)| | (kernel)| | (kernel)|       |   container runtime (Docker, containerd)|
 +---------+ +---------+ +---------+       +-----------------------------------------+
 |        HYPERVISOR                 |       |   ONE shared HOST KERNEL (namespaces,   |
 +-----------------------------------+       |   cgroups)                              |
 |        HARDWARE                   |       +-----------------------------------------+
 +-----------------------------------+       |   HARDWARE                              |
                                             +-----------------------------------------+
```

### 2. Comparison

| | Virtual machine | Container |
|---|---|---|
| What's virtualised | **Hardware** (each VM has its own kernel) | **The OS view** (processes share the host kernel) |
| Isolation | **Strong** (a separate kernel; the hypervisor boundary) | Weaker (a kernel bug can affect every container) |
| Boot time | Seconds to minutes (boots an OS) | **Milliseconds to seconds** (just starts processes) |
| Size | GBs (a full OS image) | MBs (app + libraries) |
| Overhead | Higher (a guest kernel per VM; hardware-assisted virtualisation keeps it moderate) | **Near-native** |
| Density | Tens per host | Hundreds to thousands per host |
| Different OS kernels | **Yes** (Windows VM on a Linux host) | **No** (Linux containers need a Linux kernel; Docker Desktop on Windows/macOS runs a small Linux VM underneath) |
| Built from | Hypervisor + hardware virtualisation (Intel VT-x, AMD-V) | Linux **namespaces + cgroups** + layered file systems |
| Use when | Strong multi-tenant isolation, different OSes | Packaging and deploying microservices; CI; dev environments |

### 3. How containers work (three kernel features)

| Feature | Provides |
|---|---|
| **Namespaces** | **Isolation of what a process can see**: PID (own PID 1), mount (own file-system view), network (own interfaces/ports), UTS (hostname), IPC, user (UID mapping), cgroup |
| **cgroups** (control groups) | **Limits on what it can use**: CPU shares/quotas, memory limit (an OOM kill inside the container), I/O bandwidth, PID count |
| **Union / overlay file systems** | Image **layers** shared between containers; a thin writable layer per container (copy-on-write at the file level) |

**A container is just a process** (or group of processes) with its own namespaces and cgroup limits. `ps` on the host shows it. That's the line that shows real understanding.

### 4. Hypervisor types

| | Type 1 (bare-metal) | Type 2 (hosted) |
|---|---|---|
| Runs on | Directly on the hardware | On top of a host OS |
| Examples | VMware ESXi, Xen, Microsoft Hyper-V, KVM (Linux kernel module, effectively type 1) | VirtualBox, VMware Workstation |
| Used for | Data centres, cloud | Desktops, development |

---

## 10.7 More integrative questions (short skeletons)

**"What happens when a process reads a file for the first time vs the second time?"**
First: `read` → fd → inode → page-cache miss → I/O scheduler → disk (DMA) → interrupt → page cache → copy to the user buffer (M8 §8.3). Second: a page-cache hit, so a memory copy only, orders of magnitude faster.

**"What happens on a context switch, including hardware state?"**
Timer interrupt → kernel mode → save registers into the PCB → the scheduler picks the next task → switch the page-table base (CR3 on x86), keep or flush the TLB depending on PCID → restore registers → return to user mode in the new task. Then cold caches (M1 §1.5).

**"How does `sleep(1)` work?"**
A system call: the kernel marks the thread **Waiting**, sets a timer, and schedules someone else. The timer interrupt fires after about 1 s, the thread moves to Ready, and it runs when scheduled, so it sleeps **at least** 1 s (M1, M3). It isn't a busy loop.

**"Why can't a user program disable interrupts to make a critical section?"**
It's a privileged instruction (it traps); it wouldn't stop other cores anyway; and it would let any program freeze the system (M0, M4 §4.4).

**"What's the difference between a user stack and a kernel stack?"**
Each thread has a **user stack** (in its address space) and a small **kernel stack** (in kernel memory, typically 8–16 KB on Linux). On a system call or interrupt, the CPU switches to the kernel stack, so the kernel never trusts or depends on user stack memory.

**"Why does a `fork` bomb (`:(){ :|:& };:`) hang a machine, and how is it prevented?"**
It creates processes exponentially until the process table or PIDs are exhausted (M1). Prevented with per-user process limits (`ulimit -u`, cgroup `pids.max`).

---

## 10.8 Consolidation

### Must remember (module)

1. Answer "what happens when" questions as a **skeleton first**, then go deep on request.
2. `./a.out`: read → fork (COW) → execve (inode, permission, ELF, map segments lazily, stack) → dynamic linker (shared libs) → `_start` → constructors → `main` → page faults + scheduling → `write` → exit (destructors, flush) → zombie → SIGCHLD → `waitpid` reaps.
3. Ctrl+C: tty line discipline → SIGINT to the **foreground process group**; Ctrl+Z = SIGTSTP; Ctrl+D = EOF (not a signal).
4. `malloc(1 GB)`: `mmap` → virtual only → frames on the first touch → overcommit → OOM killer.
5. Slower with threads: contention, **false sharing** (measured 4–5×), oversubscription, Amdahl, memory bandwidth, hidden locks.
6. Isolation = user mode + per-process page tables + protection bits + the timer + permissions.
7. VMs virtualise hardware (own kernel, strong isolation); containers virtualise the OS view (**namespaces** = what you see, **cgroups** = what you use; shared kernel; just processes).

### Interview Q&A bank

| Question | Skeleton |
|---|---|
| What happens when you run a program? | §10.1 skeleton (fork, exec, map, link, main, faults, exit, reap) |
| What happens when you press Ctrl+C? | tty → SIGINT to the foreground group → handler or terminate → reap |
| `malloc(1 GB)` on a 512 MB machine? | Virtual succeeds; frames on touch; swap/thrash; OOM killer |
| Why is my threaded code slower? | Contention, false sharing, oversubscription, Amdahl |
| What is false sharing? | Independent variables on one cache line; coherence ping-pong; pad to 64 B |
| How does the OS isolate processes? | Modes + page tables + protection bits + timer + permissions |
| VM vs container? | Hardware vs OS-level virtualisation; own kernel vs shared kernel |
| How are containers implemented? | Namespaces + cgroups + overlay FS; they're just processes |
| How does `sleep` work? | Block + timer interrupt + reschedule; at least the duration |

### Practice: speak each one aloud, timed

1. "What happens when you run `./a.out`?": the skeleton in **30 s**, then the full version in **3 min**.
2. "What happens when you type `ls | wc -l` and press Enter?" (combine §10.1 with M9 §9.2).
3. "Your service gets slower when you increase threads from 8 to 64 on an 8-core machine. Diagnose it." (§10.4: oversubscription + contention + false sharing; how you'd measure each: `perf`, lock profiling, context-switch counts.)
4. "Explain to a non-engineer why Docker containers start faster than VMs." (§10.6.)

---

## Exit checklist

```
[ ] I can give the ./a.out skeleton in 30 s and the full version in 3 min, citing each mechanism
[ ] I can explain Ctrl+C / Ctrl+Z / Ctrl+D precisely
[ ] I can trace malloc(1 GB) through mmap, page faults, overcommit and OOM
[ ] I can list the causes of multithreaded slowdowns and explain false sharing with numbers
[ ] I can explain process isolation as a set of hardware + kernel mechanisms
[ ] I can compare VMs and containers and explain namespaces vs cgroups
[ ] Practice 1–4 done out loud
```

---

## Next

**Part 13: Consolidation.** The final part of the OS handbook: cheat sheets for every module, the **numericals formula sheet** with a quick drill set, the confusable-pairs master table, and rapid-fire Q&A covering the whole handbook.
