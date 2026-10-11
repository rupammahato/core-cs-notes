# Operating Systems Placement Handbook — Part 11
# Module 9: Inter-Process Communication and I/O

**Module 9 · 2 hours · Tier 2 · Requires: M1 (fork, file descriptors), M4 (synchronization), M7 (mmap)**

---

## What this module covers

Processes are isolated by design (M6/M7): each has its own address space. **IPC** is the set of controlled ways to break that isolation deliberately. Interviewers ask "what IPC mechanisms do you know?", "pipe vs shared memory?" and "shared memory vs message passing?", and occasionally want to see `pipe()` + `fork()` code.

The second half covers how the OS talks to **devices**: polling, interrupts, **DMA**, and the buffering, caching and spooling trio that is regularly asked as a "difference between" question.

**Note on code:** the POSIX programs here (`pipe`, `shm_open`, signals) are standard Linux code written against the POSIX specification. They couldn't be executed on the Windows machine these notes were prepared on, so they're kept short and conventional. Compile them on Linux or WSL with `gcc file.c` (add `-lrt` for `shm_open` on older glibc).

The organising principle:

> **IPC comes in two models. Message passing: the kernel copies data between processes (pipes, message queues, sockets), which is simple and safe but costs a system call and a copy per message. Shared memory: the kernel maps the same physical frames into both processes once, so there's no copy afterwards and it's the fastest, but synchronization becomes your job.**

---

## 9.1 Why IPC, and the two models

**Cooperating processes** share information, speed up computation (parallel pipelines), and modularise systems (a browser's renderer and network processes; a shell pipeline).

| | Message passing | Shared memory |
|---|---|---|
| How | `send` / `receive` through the kernel | A memory region mapped into several address spaces |
| Kernel involvement | **Every** message (a system call + a copy) | Only at **setup**; then plain loads and stores |
| Speed | Slower (copies, system calls) | **Fastest** IPC |
| Synchronization | Built in (`receive` blocks until data arrives) | **Your responsibility** (semaphores or mutexes in the shared region, M4) |
| Data boundaries | Message or stream semantics provided | Raw bytes: you design the layout |
| Across machines | **Yes** (sockets) | **No** (same machine only) |
| Ease and safety | Easier, less error-prone | Harder (races, layout) |
| Examples | Pipes, FIFOs, message queues, sockets | POSIX `shm_open` + `mmap`, System V `shmget` |

**Interview line:** *"Message passing goes through the kernel on every message, so it's simpler and works across machines but costs copies and system calls. Shared memory involves the kernel only at setup, so it's the fastest, but the processes must synchronise access themselves."*

---

## 9.2 Pipes

### 1. Anonymous pipe

A **unidirectional byte stream** through a kernel buffer, with a **read end** and a **write end**. Usually used between **related** processes (parent and child), because the file descriptors are inherited through `fork`.

```
  parent                                   child
  write(fd[1]) ---> [ kernel pipe buffer ] ---> read(fd[0])
                    (Linux default capacity 64 KB)
```

### 2. `pipe` + `fork`: parent sends a message to the child

```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

int main(void) {
    int fd[2];                       // fd[0] = read end, fd[1] = write end
    if (pipe(fd) == -1) { perror("pipe"); return 1; }

    pid_t pid = fork();
    if (pid == 0) {                  // CHILD: reader
        close(fd[1]);                // close the UNUSED write end
        char buf[64];
        ssize_t n;
        while ((n = read(fd[0], buf, sizeof buf - 1)) > 0) {   // read returns 0 at EOF
            buf[n] = '\0';
            printf("child got: %s\n", buf);
        }
        close(fd[0]);
        return 0;
    }
    close(fd[0]);                    // PARENT: writer, closes the UNUSED read end
    const char* msg = "hello via pipe";
    write(fd[1], msg, strlen(msg));
    close(fd[1]);                    // -> the child's read() returns 0 (EOF)
    wait(NULL);
    return 0;
}
```

### 3. The rules that cause real bugs

| Rule | Why |
|---|---|
| **Close the unused ends** in each process | `read` returns EOF (0) only when **all** write ends are closed. If the reader still holds a write end, it **waits forever** |
| Reading from an empty pipe **blocks** | Until data arrives or every writer closes |
| Writing to a **full** pipe blocks | Until the reader drains it (natural flow control) |
| Writing with **no readers left** → **SIGPIPE** (kills the process by default); the write returns `EPIPE` if the signal is ignored | That's why `yes \| head -1` terminates `yes` |
| Writes of ≤ **PIPE_BUF** (4096 bytes on Linux) are **atomic** | Several writers' small messages won't interleave |
| A pipe is a **byte stream** | No message boundaries: two writes may arrive in one `read` |

### 4. How the shell implements `ls | wc -l`

```
 shell: pipe(fd)
   fork -> child 1: dup2(fd[1], STDOUT); close both fds; exec("ls")    // stdout -> pipe
   fork -> child 2: dup2(fd[0], STDIN);  close both fds; exec("wc", "-l")  // stdin <- pipe
   shell: close both fds (or wc never sees EOF!); wait for both children
```

This combines everything from M1: `fork`, `dup2` redirection, `exec`, and closing unused descriptors.

### 5. Named pipes (FIFOs)

```bash
mkfifo /tmp/myfifo            # creates a special file in the file system
cat /tmp/myfifo &             # reader (blocks until a writer opens it)
echo "hi" > /tmp/myfifo       # writer
```

| | Anonymous pipe | Named pipe (FIFO) |
|---|---|---|
| Has a name in the file system | No | **Yes** |
| Usable by unrelated processes | No (needs fd inheritance) | **Yes** |
| Lifetime | Until all ends close | The file persists until deleted (the data doesn't persist) |
| Direction | Unidirectional | Unidirectional (open two FIFOs for two-way) |

---

## 9.3 Message queues

A kernel-maintained queue of **discrete messages** (with boundaries and optional **priorities**).

```c
// POSIX message queue (sketch)
mqd_t q = mq_open("/jobs", O_CREAT | O_RDWR, 0600, NULL);
mq_send(q, "task-42", 8, /*priority*/ 5);
char buf[8192]; unsigned prio;
mq_receive(q, buf, sizeof buf, &prio);      // highest-priority message first
mq_close(q); mq_unlink("/jobs");
```

| vs a pipe | Message queue |
|---|---|
| Byte stream | **Discrete messages** (boundaries preserved) |
| FIFO only | **Priorities** |
| Related processes (anonymous) | Any process that knows the name |
| Gone when closed | **Persists** in the kernel until unlinked (or reboot) |

---

## 9.4 Shared memory

### 1. POSIX shared memory

```c
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

// writer process
int main(void) {
    int fd = shm_open("/demo_shm", O_CREAT | O_RDWR, 0600);   // named shared-memory object
    ftruncate(fd, 4096);                                        // set its size
    char* p = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    strcpy(p, "hello from shared memory");                      // plain memory write: NO system call
    munmap(p, 4096); close(fd);
    // a reader does shm_open("/demo_shm", O_RDWR, 0), mmap(..., MAP_SHARED, ...) and reads p
    // shm_unlink("/demo_shm") when everyone is done
    return 0;
}
```

```
  Process A page table ---\
                            >---> the SAME physical frames <---  Process B page table
  (different virtual addresses possible in each process)
```

### 2. Synchronization is required

Shared memory gives **no** coordination: two processes updating a shared counter have exactly the race from M2. Options:
- A **POSIX semaphore** placed **in** the shared region (`sem_init(&s, /*pshared=*/1, 1)`), or a named one (`sem_open`).
- A **process-shared mutex** (`pthread_mutexattr_setpshared(..., PTHREAD_PROCESS_SHARED)`).
- **Lock-free** structures with atomics (a single-producer/single-consumer ring buffer).

**Pointers inside shared memory are a trap:** the region may be mapped at **different virtual addresses** in each process, so store **offsets**, not raw pointers.

### 3. Why it's the fastest

After setup, communication is ordinary memory access, with **no system calls and no kernel copies**. Message passing copies user → kernel → user, and costs a system call per message.

---

## 9.5 Sockets

An endpoint for communication, **bidirectional**, and usable **across machines**.

| Type | Scope | Notes |
|---|---|---|
| **Unix domain sockets** (`AF_UNIX`) | Same machine, addressed by a file-system path | Faster than TCP loopback; can pass **file descriptors** between processes; used by Docker, X11, databases |
| **TCP sockets** (`AF_INET`, `SOCK_STREAM`) | Network; reliable byte stream | The basis of client-server systems |
| **UDP sockets** (`SOCK_DGRAM`) | Network; datagrams, no delivery guarantee | Low latency (DNS, games, streaming) |

The server sequence is `socket → bind → listen → accept → read/write`, and the client's is `socket → connect → read/write` (details belong to Computer Networks).

---

## 9.6 Signals

### 1. What is a signal?

An **asynchronous software notification** sent to a process: a minimal form of IPC that carries only a signal number. The process **handles** it (with a custom handler), **ignores** it, or takes the **default action** (terminate, terminate with a core dump, stop, continue, or ignore).

### 2. Signals to know (numbers are for Linux on x86/ARM)

| Signal | # | Default | Sent when |
|---|---|---|---|
| `SIGHUP` | 1 | Terminate | The terminal hangs up; daemons often use it as "reload config" |
| `SIGINT` | 2 | Terminate | **Ctrl+C** |
| `SIGQUIT` | 3 | Core dump | Ctrl+\ |
| `SIGKILL` | 9 | Terminate | `kill -9`; **cannot be caught, blocked or ignored** |
| `SIGSEGV` | 11 | Core dump | Invalid memory access (M7) |
| `SIGPIPE` | 13 | Terminate | Writing to a pipe or socket with no reader |
| `SIGALRM` | 14 | Terminate | A timer set by `alarm()` |
| `SIGTERM` | 15 | Terminate | `kill` (the default): a **polite** request to exit |
| `SIGCHLD` | 17 | Ignore | A child stopped or exited (M1: reap zombies here) |
| `SIGCONT` | 18 | Continue | Resume a stopped process |
| `SIGSTOP` | 19 | Stop | **Cannot be caught or ignored** |
| `SIGTSTP` | 20 | Stop | **Ctrl+Z** |

### 3. `kill` vs `kill -9` (asked often)

| `kill PID` (SIGTERM, 15) | `kill -9 PID` (SIGKILL, 9) |
|---|---|
| Can be **caught**: the process can clean up (flush files, release locks, remove temp files) and exit gracefully | **Cannot** be caught: the kernel terminates it immediately |
| The process might ignore it | Always works (except on a process stuck in uninterruptible kernel sleep (state `D`), or one that's already a zombie) |
| **Try first** | Last resort: no cleanup, so you may leave corrupted files or stale locks |

### 4. Handler rules

```c
#include <signal.h>
volatile sig_atomic_t stop = 0;
void onInt(int sig) { (void)sig; stop = 1; }       // just set a flag
int main(void) {
    struct sigaction sa = {0};
    sa.sa_handler = onInt;
    sigaction(SIGINT, &sa, NULL);                  // prefer sigaction over signal()
    while (!stop) { /* work */ }
    /* clean shutdown here, in normal code */
}
```

Handlers run **asynchronously**, interrupting the program at any instruction, so they may call only **async-signal-safe** functions (`write`, `_exit`; **not** `printf` or `malloc`, which may be mid-update with a lock held). The safe pattern is to **set a flag** of type `volatile sig_atomic_t` and act on it in the main loop.

---

## 9.7 IPC comparison table

| Mechanism | Direction | Related processes only? | Boundaries | Across machines | Speed | Typical use |
|---|---|---|---|---|---|---|
| Anonymous pipe | One-way | **Yes** | Byte stream | No | Medium | Shell pipelines, parent → child |
| Named pipe (FIFO) | One-way | No | Byte stream | No | Medium | Simple unrelated producer/consumer |
| Message queue | Many-to-many | No | **Messages + priority** | No | Medium | Job queues between services on one host |
| Shared memory | Any | No | None (raw memory) | No | **Fastest** | High-volume data (databases, video, browsers) |
| Unix socket | Two-way | No | Stream or datagram | No | Fast | Local client-server (Docker, PostgreSQL) |
| TCP/UDP socket | Two-way | No | Stream / datagram | **Yes** | Network-bound | Distributed systems |
| Signal | One-way | No | Just a number | No | — | Notifications (terminate, reload, child exited) |
| Memory-mapped file | Any | No | None | No | Fast | Sharing file-backed data (M7) |

---

## 9.8 I/O: how the OS talks to devices

### 1. Three ways to do I/O

```
 POLLING (programmed I/O)        INTERRUPT-DRIVEN                 DMA
 CPU: is it ready? no            CPU: start the I/O, go do        CPU: tell the DMA controller
      is it ready? no                 other work                       "copy N bytes from device
      is it ready? yes ->        device: done -> INTERRUPT              to memory address X"
      copy byte by byte          CPU: handler copies the data      DMA: moves the whole block
 (CPU busy the whole time)        (one interrupt per word/block)        by itself
                                                                    DMA: ONE interrupt when done
```

| | Polling | Interrupt-driven | DMA |
|---|---|---|---|
| CPU busy while waiting | **Yes** (busy-wait) | No | No |
| CPU moves the data | Yes | **Yes** (in the handler) | **No** (the DMA controller does) |
| Interrupts | None | **One per unit** of data | **One per block** |
| Best for | Very fast or very frequent devices; short waits | Slow devices with small transfers (keyboard) | **Bulk transfers** (disk, network, GPU) |

### 2. DMA step by step

```
 1. The device driver programs the DMA controller: source (device), destination (RAM address),
    byte count, direction
 2. The CPU continues running other processes
 3. The DMA controller transfers the data directly between the device and RAM over the bus
    ("cycle stealing": it occasionally takes memory-bus cycles, slightly slowing the CPU's own accesses)
 4. When the count reaches zero, the DMA controller raises ONE interrupt
 5. The interrupt handler marks the waiting process READY (M1)
```

**Why it matters:** without DMA, a 1 GB disk read would have the CPU copying (or handling interrupts for) every word. With DMA, the CPU is involved only at the start and the end.

### 3. Blocking, non-blocking and asynchronous I/O

| Model | Behaviour | Example |
|---|---|---|
| **Blocking** | The call returns only when the I/O is done; the thread sleeps | Default `read()` |
| **Non-blocking** | Returns immediately with whatever's available (or `EAGAIN`) | `O_NONBLOCK` |
| **I/O multiplexing** | One thread waits on **many** descriptors; it's told which are ready | `select`, `poll`, **`epoll`** (Linux), `kqueue` (BSD/macOS) |
| **Asynchronous** | Start the I/O and get notified on **completion** | Linux **`io_uring`**, Windows IOCP |

**Why `epoll` matters:** one thread can handle tens of thousands of connections (the "C10K problem") without a thread per connection. That's how **nginx, Redis and Node.js** work: an event loop over `epoll`.

### 4. Buffering vs caching vs spooling (a classic "difference" question)

| | Buffering | Caching | Spooling |
|---|---|---|---|
| Purpose | Smooth out **speed/size mismatches** between producer and consumer during a transfer | Keep a **copy** of frequently used data in faster storage for **reuse** | Queue whole jobs for a device that can serve **only one at a time** |
| Is the data a copy? | Often the **only** copy while in transit | **Always a copy** (the original lives elsewhere) | The job is stored on disk until the device takes it |
| Example | stdio buffer before `write()`; **double buffering** (fill one buffer while the other is processed); network card ring buffers | **Page cache**, CPU caches, TLB, browser cache | **Print spooler**: many programs "print" at once, and jobs queue on disk for the single printer |
| Key benefit | Fewer, larger operations; decoupled speeds | Faster repeated access | A non-shareable device is shared; programs don't wait for it |

**Spooling** = *Simultaneous Peripheral Operations On-Line*. It's also how spooling breaks **mutual exclusion** for deadlock prevention (M5 §5.5): only the spooler daemon touches the printer.

---

## 9.9 Consolidation

### Must remember (module)

1. Two IPC models: **message passing** (kernel copies, system call per message, works across machines) vs **shared memory** (kernel only at setup, fastest, you synchronise).
2. Pipe: unidirectional byte stream, kernel buffer (64 KB on Linux), related processes. **Close unused ends** (EOF needs every writer closed); a write with no reader → SIGPIPE; ≤ 4096-byte writes are atomic.
3. Shell pipeline = `pipe` + `fork` + `dup2` + `exec` + closing descriptors.
4. FIFO = a named pipe for unrelated processes. Message queues keep boundaries and priorities and persist until unlinked.
5. Shared memory = `shm_open` + `ftruncate` + `mmap(MAP_SHARED)`; needs semaphores or process-shared mutexes; store offsets, not pointers.
6. Sockets: Unix domain (local, fast, can pass fds) vs TCP/UDP (network).
7. Signals: SIGINT (Ctrl+C), SIGTERM (polite, catchable), **SIGKILL/SIGSTOP uncatchable**, SIGCHLD (reap), SIGSEGV, SIGPIPE. Handlers must be async-signal-safe: set a flag.
8. Polling (CPU busy) vs interrupts (CPU free, one interrupt per unit) vs **DMA** (the device moves the data, one interrupt per block).
9. Blocking / non-blocking / multiplexing (`epoll`) / async (`io_uring`).
10. Buffering (transit, speed mismatch) vs caching (reuse copy) vs spooling (queue jobs for an exclusive device).

### Common wrong answers (module)

- "Pipes are bidirectional." (Anonymous pipes are one-way; use two, or a socketpair.)
- "Shared memory needs no synchronization."
- "`kill -9` lets the process clean up."
- "Signals can be used to send data."
- "DMA means the CPU isn't involved at all." (It sets up the transfer and handles the completion interrupt.)
- "Buffering and caching are the same."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What IPC mechanisms exist? | Pipes, FIFOs, message queues, shared memory, sockets, signals, mapped files | Which is fastest? (Shared memory) |
| Shared memory vs message passing? | Kernel at setup only vs on every message; speed vs simplicity | How do you synchronise shared memory? |
| How does `ls \| wc` work? | `pipe` + two forks + `dup2` + `exec` | Why close the unused ends? |
| Pipe vs FIFO? | Anonymous (related processes) vs named (any process) | Message queue vs pipe? |
| SIGTERM vs SIGKILL? | Catchable, graceful vs uncatchable, immediate | Which signals can't be caught? |
| What is a signal handler allowed to do? | Only async-signal-safe calls; set a flag | Why not `printf`? |
| What is DMA? | The controller transfers blocks device↔RAM, with one interrupt at the end | vs interrupt-driven I/O? |
| Polling vs interrupts? | Busy-wait vs notification | When is polling better? (Very fast devices) |
| Buffering vs caching vs spooling? | Transit smoothing vs reuse copy vs job queue for an exclusive device | Example of each |
| How does nginx handle many connections? | Event loop over `epoll` (I/O multiplexing) | |

### Practice

**P1.** A parent creates a pipe, forks, and the child reads until EOF, but the program hangs forever after the parent finishes writing and closes its write end. What's the most likely bug?
<details><summary>Answer</summary>

The **child didn't close its own copy of the write end** (`fd[1]`). EOF is delivered only when **all** write ends are closed, and the child itself still holds one, so its `read` blocks forever.
</details>

**P2.** Two processes increment a counter in shared memory 1,000,000 times each. The final value is ~1.3 million. Explain why, and fix it.
<details><summary>Answer</summary>

It's the same lost-update race as threads (M2/M4): load-add-store interleavings. Fix: protect the increment with a process-shared semaphore or mutex placed in the shared region, or use an atomic fetch-add on the shared variable.
</details>

**P3.** For each, choose a mechanism: (a) a shell pipeline between two commands; (b) a video frame (8 MB) passed 60 times a second between two local processes; (c) telling a daemon to reload its config; (d) a client on another machine querying a server; (e) a job queue with priorities between local services.
<details><summary>Answer</summary>

(a) Anonymous pipe. (b) Shared memory (with a semaphore or ring buffer for synchronization). (c) A signal (SIGHUP by convention). (d) A TCP socket. (e) A message queue.
</details>

**P4.** Why can't a process catch SIGKILL, and why is that a deliberate design choice?
<details><summary>Answer</summary>

The kernel handles SIGKILL itself and never delivers it to user code. If processes could catch or ignore every signal, a misbehaving or malicious process could make itself unkillable. SIGKILL (and SIGSTOP) guarantee that the administrator always has the final say.
</details>

---

## Exit checklist

```
[ ] I can compare message passing vs shared memory
[ ] I can write pipe + fork code and explain why unused ends must be closed
[ ] I can explain how the shell builds a pipeline with dup2 + exec
[ ] I can compare pipe, FIFO, message queue, shared memory, sockets and signals in one table
[ ] I know which signals can't be caught, kill vs kill -9, and the handler safety rule
[ ] I can explain polling vs interrupts vs DMA, and DMA step by step
[ ] I can explain blocking / non-blocking / epoll / async I/O and why epoll scales
[ ] I can compare buffering, caching and spooling with examples
[ ] P1–P4 done
```

---

## Next

**Part 12: M10 — Putting It Together.** It covers the integrative questions that test the whole handbook at once: **what happens when you run `./a.out`**, end to end; what happens on Ctrl+C; why a multithreaded program can be slower (with a measured false-sharing benchmark); how the OS isolates processes; and VMs vs containers.
