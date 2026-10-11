# Operating Systems Placement Handbook — Part 13
# Consolidation: Cheat Sheets, Formula Sheet, Drills, Rapid-Fire Q&A

**For the final 7–10 days before interviews · Requires: the modules you've done**

---

## How to use this part

There's no new teaching here. It compresses Parts 2–12 into the forms you'll use when time is short:

| Section | Use it for | When |
|---|---|---|
| 13.1 Cheat sheets | Re-reading each module in 2–3 minutes | Daily in the final week |
| 13.2 Formula sheet | Every numerical formula in one place | Before any written test |
| 13.3 Numerical drill set | 11 mixed problems (answers computed with code) | Timed: 30 minutes |
| 13.4 Confusable pairs | The "difference between X and Y" questions | Every other day |
| 13.5 Rapid-fire Q&A | Spoken answers under 30 seconds | Have someone quiz you |
| 13.6 "What happens when" chains | The integrative questions | Twice, out loud |

---

## 13.1 Cheat sheets

### M0 — Fundamentals

- OS = resource manager + extended machine; the kernel is the privileged core (Android and Ubuntu share the Linux kernel).
- User mode (ring 3) vs kernel mode (ring 0); privileged instructions trap in user mode.
- Kernel entry only via **system call (trap), interrupt, or exception**, to kernel-registered handlers.
- System call: number + arguments in registers → trap → system call table → validate → work → `sysret`. Far costlier than a function call. `printf` → `write`; `malloc` often makes no system call.
- Interrupt = asynchronous (hardware) vs trap/exception = synchronous (instruction). **The timer interrupt enables preemption.**
- Monolithic (Linux, modular) vs microkernel (QNX, Minix, seL4) vs hybrid (Windows NT, macOS).
- Multiprogramming (CPU use, switch on I/O) vs multitasking (time slices, responsiveness).
- Boot: firmware (BIOS/UEFI) → bootloader → kernel → PID 1 → services.

### M1 — Processes

- Program (passive) vs process (active, with state). Layout: text, data, BSS, heap ↑, stack ↓.
- PCB: PID, state, PC + registers, scheduling, memory (page-table pointer), open files.
- States: New, Ready, Running, Waiting, Terminated. **No Waiting→Running; no Ready→Waiting.**
- Context switch: save PCB → schedule → load PCB → switch the address space; direct + indirect (TLB, cache) costs. A system call alone is a mode switch.
- `fork`: 0 to the child, the PID to the parent, −1 on failure; separate memory; **COW**. `exec` replaces the image and never returns on success. `wait` reaps.
- n sequential forks → 2ⁿ processes; `&&`/`||` short-circuit; the unflushed stdio buffer is duplicated (the `printf("A")` trap).
- Zombie = exited, not reaped (fix: `wait`, SIGCHLD). Orphan = parent died; adopted by PID 1.

### M2 — Threads

- Shared: code, globals, **heap**, files, address space. Private: **stack**, registers, PC, TID, TLS.
- Threads: cheap to create and switch, but one crash kills the process; sharing needs synchronization.
- ULT (no parallelism, one block blocks all) vs KLT; models 1:1 (Linux, `std::thread`), M:1, M:N (Go, Java virtual threads).
- Concurrency (interleaving) vs parallelism (simultaneous). Amdahl: 1 / ((1−p) + p/n).
- `std::thread`: join or detach (else terminate); arguments copied (`std::ref`); `jthread` auto-joins.
- `counter++` = load-add-store, so updates are lost (measured ~1.0–1.3 M of 2 M).

### M3 — CPU scheduling

- TAT = CT − AT; WT = TAT − BT; RT = first run − AT.
- FCFS (convoy effect), SJF (optimal non-preemptive average WT), **SRTF (optimal average WT)**, Priority (starvation → aging; inversion → inheritance), **RR (best response, worst WT/TAT)**, MLFQ (learns; the basis of real OSes). Linux: CFS (vruntime, red-black tree) → EEVDF.
- Quantum: ≫ context-switch cost; ~80% of bursts fit; too large → FCFS.
- Burst prediction: τₙ₊₁ = α·tₙ + (1−α)·τₙ.

### M4 — Synchronization

- CS requirements: **mutual exclusion, progress, bounded waiting**.
- Peterson's: flags + turn; needs sequentially consistent atomics on modern CPUs. Hardware: TAS, CAS. `volatile` ≠ synchronization.
- Mutex (ownership, sleeps) vs spinlock (busy-waits; short sections, multicore) vs **semaphore (counter, no ownership: 1 = lock, N = pool, 0 = signal)**.
- Condition variable: `wait` atomically releases the lock; **always use a predicate** (spurious/stolen wake-ups). Monitor = data + lock + CVs.
- Producer-consumer: empty = N, full = 0, mutex = 1; **wait on the counting semaphore before the mutex**.
- Readers-writers: the first reader locks out writers; reader preference starves writers; `shared_mutex`.
- Philosophers: ordering / `scoped_lock` / n−1 seats / asymmetry / waiter.
- Odd/even: shared turn + predicate + termination + `notify_all`.

### M5 — Deadlocks

- Conditions: **mutual exclusion, hold and wait, no preemption, circular wait** (all necessary).
- RAG: no cycle → no deadlock; cycle + single instances → deadlock; multiple instances → maybe.
- Strategies: ignore (most OSes), prevention (break a condition; **ordering** is the practical one), avoidance (Banker's), detection + recovery (databases).
- Banker's: Need = Max − Alloc; safety: find Need ≤ Work, then Work += Alloc; request: ≤ Need, ≤ Available, pretend, check safety. Safe ⇒ no deadlock; unsafe ⇏ deadlock.
- n processes needing at most k: deadlock-free iff R ≥ n(k−1) + 1.
- Deadlock (blocked) vs starvation (one never served) vs livelock (busy, no progress).

### M6 — Memory management

- Logical vs physical; the MMU translates on every access. Base + limit = relocation + protection.
- First / best / worst fit; internal (inside a block) vs external (scattered holes) fragmentation; compaction.
- Paging: page | offset → frame | offset; offset bits = log₂(page size). No external fragmentation; on average half a page internal.
- PTE: frame, valid, protection, dirty, referenced.
- TLB: EAT = h(t+m) + (1−h)(t+2m). Multi-level tables (x86-64: 4 × 9 + 12). Inverted = one entry per frame.
- Segmentation: ⟨s, d⟩, limit check, external fragmentation. Paging vs segmentation.

### M7 — Virtual memory

- Demand paging; the invalid bit → page fault.
- **Fault steps:** trap → legal? (else SIGSEGV) → frame (evict; write back if dirty) → disk read (block) → PTE valid → **restart the instruction**.
- EAT = (1−p)·m + p·F; p must be ~10⁻⁶.
- FIFO / OPT / LRU (15/12/9 on the standard string); **Belady's anomaly** (FIFO 9 → 10 with more frames); stack algorithms are immune.
- Clock / second chance approximates LRU; prefer clean (0,0) victims.
- **Thrashing:** Σ working sets > RAM; fix by reducing multiprogramming, working-set/PFF allocation, local replacement, more RAM.
- `mmap`; `malloc` uses `brk` (small) and `mmap` (large); frames on first touch; overcommit + OOM killer.

### M8 — Storage

- HDD: seek + rotational latency (half a rotation) + transfer. SSD: no seek, FTL, wear levelling, TRIM.
- Disk scheduling (53; 98, 183, 37, 122, 14, 124, 65, 67): FCFS 640, SSTF 236, SCAN↓ 236, C-SCAN 382, LOOK↓ 208, C-LOOK 322.
- fd table (per process) → open-file entry (**offset**) → inode; fork and dup share offsets.
- Inode = metadata + block pointers + link count, **not the name**. Data freed at link count 0 **and** no open fds.
- Hard link (same inode, survives deletion, no cross-FS or directories) vs soft link (path, dangles, can cross FS).
- Journaling (write-ahead log) vs fsck vs CoW file systems. RAID 0/1/5/6/10; RAID ≠ backup.

### M9 — IPC and I/O

- Message passing (kernel per message, works across machines) vs shared memory (setup only, fastest, synchronise yourself).
- Pipes: one-way byte stream, related processes; **close unused ends**; SIGPIPE; ≤ 4096-byte writes are atomic. FIFO = named. Message queue = boundaries + priorities.
- Signals: SIGKILL/SIGSTOP uncatchable; SIGTERM is polite; handlers set a flag.
- Polling vs interrupts vs **DMA** (one interrupt per block). `epoll` for many connections.
- Buffering (transit) vs caching (reuse copy) vs spooling (job queue for an exclusive device).

### M10 — Integration

- `./a.out`: fork → exec (inode, permission, ELF, lazy mmap, stack) → dynamic linker → `_start` → constructors → `main` → faults and scheduling → `write` → exit → zombie → reap.
- Ctrl+C → SIGINT to the foreground process group. `malloc(1 GB)` → virtual only until touched.
- Threads slower: contention, **false sharing (measured 4–5×)**, oversubscription, Amdahl.
- VMs (own kernel, hardware virtualisation) vs containers (shared kernel; namespaces = view, cgroups = limits).

---

## 13.2 Formula sheet

### Scheduling

```
TAT = CT - AT          WT = TAT - BT          RT = first CPU time - AT
Averages = sum / n     Throughput = processes completed / total time
Exponential averaging: tau(n+1) = alpha * t(n) + (1 - alpha) * tau(n)
RR overhead fraction  = switch / (q + switch)   (when every process uses its full quantum)
```

### Threads

```
Amdahl speedup = 1 / ((1 - p) + p / n)          max as n -> infinity: 1 / (1 - p)
```

### Deadlock

```
Need = Max - Allocation         Available = Total - sum(Allocation)
Safety: Work = Available; repeat { find i: !Finish[i] && Need[i] <= Work;  Work += Allocation[i] }
Final Work must equal Total (free arithmetic check)
Deadlock-free with n processes, max k instances each, R instances total:  R >= n(k - 1) + 1
```

### Paging and the TLB

```
offset bits        = log2(page size)
page-number bits   = logical address bits - offset bits
# pages            = 2^(page-number bits) = logical space / page size
# frames           = physical memory / frame size
frame-number bits  = log2(# frames)
page-table size    = # pages x PTE size
physical address   = frame x page size + offset
internal fragmentation (last page) = pages x page size - process size   (average: half a page)
EAT (TLB, 1-level) = h(t + m) + (1 - h)(t + 2m)
EAT (TLB, k-level) = h(t + m) + (1 - h)(t + (k + 1)m)
EAT (if TLB time ignored) = h*m + (1 - h)*2m
```

### Virtual memory

```
EAT with faults = (1 - p) * m + p * F              (F = fault service time, ms-scale)
Max fault rate for EAT <= E:   p <= (E - m) / (F - m)
Proportional frame allocation: a_i = (s_i / sum(s)) * m_frames
```

### Disk

```
Access time       = seek + rotational latency + transfer
Avg rot. latency  = 0.5 x (60 / RPM) seconds          (7200 RPM -> 4.17 ms)
Total head movement = sum |next - current|   (state direction, edge touch, return counting)
```

### File systems

```
pointers per block = block size / pointer size  (= P)
max file size      = (direct + P + P^2 + P^3) x block size
bitmap size        = (disk size / block size) bits
```

---

## 13.3 Numerical drill set (answers computed with code)

Do all 11 in 30 minutes. Write the layout (Gantt chart / frame table / work vector), not just the number.

**D1.** Processes (AT, BT): P1 (0, 5), P2 (1, 3), P3 (2, 1), P4 (3, 2). Average WT and TAT for FCFS, SRTF and RR (q = 2).
<details><summary>Answer</summary>

- **FCFS:** P1 0–5, P2 5–8, P3 8–9, P4 9–11 → avg WT **4.00**, avg TAT **6.75**.
- **SRTF:** P1 0–1, P2 1–2, P3 2–3, P2 3–5, P4 5–7, P1 7–11 → avg WT **2.25**, avg TAT **5.00**, avg RT 0.50.
- **RR q=2:** P1 0–2, P2 2–4, P3 4–5, P1 5–7, P4 7–9, P2 9–10, P1 10–11 → avg WT **4.50**, avg TAT **7.25**, avg RT 1.75.
</details>

**D2.** TLB 10 ns, memory 80 ns, hit ratio 95%, single-level paging. EAT?
<details><summary>Answer</summary>

0.95 × 90 + 0.05 × 170 = **94 ns**.
</details>

**D3.** 32-bit logical addresses, 16 KB pages, 4-byte PTEs. Offset bits, page-number bits, page-table size?
<details><summary>Answer</summary>

Offset = log₂(16384) = **14**; page bits = **18**; entries 2¹⁸ = 262,144 × 4 B = **1 MB**.
</details>

**D4.** Reference string 1 3 0 3 5 6 3, 3 frames. Faults for FIFO, LRU, OPT?
<details><summary>Answer</summary>

FIFO **6**, LRU **5**, OPT **5**.
</details>

**D5.** Total (10, 5, 7). Allocation: P0 (0,1,0), P1 (2,0,0), P2 (3,0,2). Max: P0 (7,5,3), P1 (3,2,2), P2 (9,0,2). Safe?
<details><summary>Answer</summary>

Need: P0 (7,4,3), P1 (1,2,2), P2 (6,0,0). Available = (5, 4, 5). P1 → Work (7,4,5) → P2 → (10,4,7) → P0 → (10,5,7). **Safe: ⟨P1, P2, P0⟩.**
</details>

**D6.** Head at 100, cylinders 0–199, queue 23, 89, 132, 42, 187. Total movement for FCFS, SSTF, LOOK (moving up)?
<details><summary>Answer</summary>

FCFS **421**; SSTF (89, 132, 187, 42, 23) **273**; LOOK up (132, 187, 89, 42, 23) **251**.
</details>

**D7.** Memory 100 ns, page fault 5 ms, fault rate 1 in 10,000. EAT?
<details><summary>Answer</summary>

0.9999 × 100 + 0.0001 × 5,000,000 = **≈ 600 ns** (6× slower).
</details>

**D8.** 80% parallel code on 4 cores. Speedup?
<details><summary>Answer</summary>

1 / (0.2 + 0.2) = **2.5×**.
</details>

**D9.** How many processes in total?
```c
for (int i = 0; i < 3; i++) if (fork() == 0) break;
```
<details><summary>Answer</summary>

**4.** Each child breaks out immediately, so only the original parent keeps forking: 1 parent + 3 children.
</details>

**D10.** 8 KB blocks, 4-byte pointers, an inode with 12 direct + single + double indirect. Maximum file size?
<details><summary>Answer</summary>

P = 2048. 12 × 8 KB + 2048 × 8 KB + 2048² × 8 KB = 96 KB + 16 MB + **32 GB** ≈ **32 GB**.
</details>

**D11.** 5 processes each need at most 3 tape drives. What's the minimum number of drives that guarantees no deadlock?
<details><summary>Answer</summary>

5 × (3 − 1) + 1 = **11**.
</details>

---

## 13.4 Confusable pairs: master table

| Pair | One-line distinction | Module |
|---|---|---|
| OS vs kernel | Whole system software vs its privileged core | M0 |
| User mode vs kernel mode | Restricted vs privileged CPU mode | M0 |
| System call vs library function | Trap into the kernel vs user-space code (may wrap a system call) | M0 |
| Interrupt vs trap | Asynchronous hardware vs synchronous instruction-caused | M0 |
| Monolithic vs microkernel | Everything in the kernel vs minimal kernel + user servers | M0 |
| Multiprogramming vs multitasking | Switch on I/O for utilisation vs time slices for responsiveness | M0 |
| Program vs process | Passive file vs active execution | M1 |
| Mode switch vs context switch | Same process changes privilege vs a different process runs | M1 |
| `fork` vs `exec` | New process (copy) vs replace the image (same PID) | M1 |
| Zombie vs orphan | Dead, unreaped vs alive, parent dead | M1 |
| Process vs thread | Resource container vs execution unit sharing it | M2 |
| User vs kernel threads | Library-managed vs kernel-scheduled | M2 |
| Concurrency vs parallelism | Interleaving vs simultaneous | M2 |
| Preemptive vs non-preemptive | CPU can be taken vs only on block/exit | M3 |
| SJF vs SRTF | Non-preemptive vs preemptive shortest | M3 |
| Starvation vs aging | The problem vs its fix | M3 |
| Priority inversion vs inheritance | High blocked via low+medium vs temporary priority boost | M3 |
| Race condition vs data race | Timing-dependent result vs unsynchronised conflicting access (UB in C++) | M4 |
| Mutex vs semaphore | Lock with ownership vs counter without ownership | M4 |
| Binary semaphore vs mutex | No ownership (signalling) vs ownership | M4 |
| Spinlock vs mutex | Busy-wait vs sleep | M4 |
| Semaphore vs monitor | Low-level primitive vs data + automatic lock + CVs | M4 |
| `notify_one` vs `notify_all` | Wake one waiter vs all (re-check predicates) | M4 |
| Deadlock vs starvation vs livelock | Blocked cycle vs one never served vs busy without progress | M5 |
| Prevention vs avoidance | Design rule vs per-request safety check | M5 |
| Safe vs unsafe state | A safe sequence exists vs not (unsafe ≠ deadlock) | M5 |
| Logical vs physical address | CPU-generated vs RAM location | M6 |
| Internal vs external fragmentation | Inside a block vs between blocks | M6 |
| Paging vs segmentation | Fixed, invisible vs variable, logical | M6 |
| TLB vs page table vs cache | Translation cache vs translation table in RAM vs data cache | M6 |
| Page fault vs segmentation fault | Legal but not resident vs illegal access | M7 |
| Minor vs major fault | No disk I/O vs disk read | M7 |
| FIFO vs LRU vs OPT | Arrival order vs past use vs future use | M7 |
| Virtual memory vs swap | The translation abstraction vs a backing store | M7 |
| Thrashing vs high load | Paging dominates execution vs busy, but productive | M7 |
| Hard link vs soft link | Same inode vs a path file | M8 |
| SCAN vs C-SCAN vs LOOK | Sweep both ways to the end vs one way + return vs only to the last request | M8 |
| Journaling vs fsck | Replay a log vs scan everything | M8 |
| RAID 0 vs 1 vs 5 | Speed vs mirror vs parity | M8 |
| Pipe vs FIFO | Anonymous (related processes) vs named | M9 |
| Shared memory vs message passing | Setup-only kernel vs kernel per message | M9 |
| SIGTERM vs SIGKILL | Catchable vs uncatchable | M9 |
| Polling vs interrupts vs DMA | CPU waits vs CPU notified vs device moves the data | M9 |
| Buffering vs caching vs spooling | Transit vs reuse copy vs job queue | M9 |
| VM vs container | Own kernel vs shared kernel | M10 |
| Namespaces vs cgroups | What a process can see vs what it can use | M10 |

---

## 13.5 Rapid-fire Q&A

Answer each in under 30 seconds, out loud.

### Fundamentals and processes

| # | Question | Answer |
|---|---|---|
| 1 | What is a kernel? | The privileged core of the OS: scheduling, memory, drivers, file systems |
| 2 | Why dual mode? | Protection: only the kernel can run privileged instructions |
| 3 | How does a program enter the kernel? | System call (trap), interrupt or exception |
| 4 | Is `printf` a system call? | No; a buffered library function that calls `write` |
| 5 | Why does the OS need a timer interrupt? | To regain the CPU (preemption) |
| 6 | What's in a PCB? | PID, state, PC/registers, scheduling, memory, files |
| 7 | Can Waiting go to Running? | No, it goes to Ready first |
| 8 | Why is a context switch expensive? | Saving state + address-space switch + cold TLB and caches |
| 9 | `fork` return values? | 0 child, PID parent, −1 error |
| 10 | Why is `fork` cheap? | Copy-on-write |
| 11 | Zombie vs orphan? | Dead, unreaped vs alive, adopted by PID 1 |
| 12 | `fork(); fork(); fork();` processes? | 8 |

### Threads and scheduling

| # | Question | Answer |
|---|---|---|
| 13 | Process vs thread? | Own address space vs shared; cost vs isolation |
| 14 | What's private to a thread? | Stack, registers, PC, TID |
| 15 | If one thread segfaults? | The whole process dies |
| 16 | Concurrency vs parallelism? | Interleaved vs simultaneous |
| 17 | Optimal average waiting-time algorithm? | SRTF (SJF if non-preemptive) |
| 18 | Best response time? | Round Robin |
| 19 | Convoy effect? | Short jobs stuck behind a long one under FCFS |
| 20 | Fix for starvation? | Aging |
| 21 | Quantum too large? | Degenerates into FCFS |
| 22 | How does MLFQ avoid knowing bursts? | Demote on full quantum; keep on early block |
| 23 | Priority inversion fix? | Priority inheritance |

### Synchronization and deadlock

| # | Question | Answer |
|---|---|---|
| 24 | Three CS requirements? | Mutual exclusion, progress, bounded waiting |
| 25 | Why is `counter++` unsafe? | Load-add-store interleaving |
| 26 | Mutex vs semaphore? | Ownership vs counting/signalling |
| 27 | When to use a spinlock? | Very short sections, multicore, can't sleep |
| 28 | Why a predicate in `cv.wait`? | Spurious and stolen wake-ups |
| 29 | Producer-consumer semaphores? | empty = N, full = 0, mutex = 1 |
| 30 | Swap wait(empty) and wait(mutex)? | Deadlock when the buffer is full |
| 31 | Readers-writers starvation? | Reader preference starves writers |
| 32 | Dining philosophers fix? | Lock ordering / atomic pickup / n−1 seats |
| 33 | Four deadlock conditions? | Mutual exclusion, hold and wait, no preemption, circular wait |
| 34 | Most practical prevention? | Global lock ordering (breaks circular wait) |
| 35 | Is an unsafe state a deadlock? | No, only possibly |
| 36 | Banker's Need? | Max − Allocation |
| 37 | Why don't OSes use Banker's? | Needs maximum needs in advance; fixed processes; slow |
| 38 | What does Linux do about deadlock? | Ignores it for user locks; lockdep in the kernel |
| 39 | Livelock example? | Two threads backing off in lockstep |

### Memory

| # | Question | Answer |
|---|---|---|
| 40 | Paging fragmentation? | Internal only (last page) |
| 41 | Segmentation fragmentation? | External |
| 42 | What does a TLB cache? | Page→frame translations |
| 43 | Why multi-level page tables? | Don't allocate tables for unused regions |
| 44 | Inverted page table? | One entry per physical frame |
| 45 | What is virtual memory? | Per-process address spaces decoupled from RAM |
| 46 | Page fault steps? | Trap, legal?, frame, read, PTE, restart |
| 47 | Belady's anomaly? | FIFO: more frames, more faults |
| 48 | Which algorithms are immune? | LRU, OPT (stack algorithms) |
| 49 | How is LRU approximated? | Reference bits + clock |
| 50 | What is thrashing? | More paging than executing; Σ WS > RAM |
| 51 | Fix for thrashing? | Reduce multiprogramming; working set / PFF; more RAM |
| 52 | Why does `malloc(1 GB)` succeed instantly? | Virtual only; frames on touch (overcommit) |

### Storage, IPC, integration

| # | Question | Answer |
|---|---|---|
| 53 | What's in an inode? | Metadata + block pointers + link count, not the name |
| 54 | Hard vs soft link? | Same inode vs path; survives vs dangles |
| 55 | Why no hard links to directories? | Cycles in the tree |
| 56 | SSTF problem? | Starvation |
| 57 | Disk algorithm with uniform waits? | C-SCAN / C-LOOK |
| 58 | Is deleted space freed immediately? | Only when link count = 0 and no open fds |
| 59 | What do fork/dup share for files? | The open-file entry, hence the offset |
| 60 | Fastest IPC? | Shared memory |
| 61 | Why close unused pipe ends? | EOF needs every write end closed |
| 62 | Uncatchable signals? | SIGKILL, SIGSTOP |
| 63 | What is DMA? | The device moves blocks to RAM; one interrupt per block |
| 64 | Buffering vs caching? | Transit smoothing vs reuse copy |
| 65 | What does Ctrl+C do? | SIGINT to the foreground process group |
| 66 | What is false sharing? | Independent variables on one cache line; pad to 64 B |
| 67 | Container vs VM? | Shared kernel (namespaces + cgroups) vs own kernel |
| 68 | How is a process isolated? | User mode + own page tables + protection bits + timer |

---

## 13.6 "What happens when" chains (rehearse out loud)

```
RUN ./a.out      read -> fork(COW) -> execve(inode, perm, ELF) -> mmap segments lazily -> stack
                 -> ld.so maps libs -> _start -> ctors -> main -> page faults + scheduling
                 -> printf -> write -> tty -> exit(dtors, flush) -> zombie -> SIGCHLD -> waitpid

PAGE FAULT       invalid PTE -> trap -> legal? (no: SIGSEGV) -> free frame? (no: replace;
                 dirty -> write back) -> disk read (block) -> interrupt -> PTE valid -> restart

read(fd)         trap -> fd table -> open-file (offset) -> inode -> page cache? hit: copy
                 miss: I/O scheduler -> DMA -> interrupt -> cache -> copy -> offset += n

CONTEXT SWITCH   timer interrupt -> kernel mode -> save regs to PCB -> scheduler picks ->
                 switch page tables (TLB flush/PCID) -> restore regs -> return to user

Ctrl+C           keyboard interrupt -> tty line discipline -> SIGINT to foreground group ->
                 handler or terminate -> zombie -> shell reaps -> prompt

DEADLOCK         mutual exclusion + hold&wait + no preemption + circular wait -> ignore /
                 prevent (order locks) / avoid (Banker's) / detect (wait-for cycle) + recover
```

---

## Final checklist: OS handbook complete

```
[ ] All module exit checklists ticked (M0-M10)
[ ] Numerical drill set: 10+/11 correct in 30 minutes, with layouts drawn
[ ] Rapid-fire: 64+/68 answered correctly out loud
[ ] Without notes: process vs thread (45 s), mutex vs semaphore (40 s), page-fault steps (45 s),
    deadlock conditions + Banker's (2 min), ./a.out end to end (30 s skeleton, 3 min full)
[ ] Wrote producer-consumer and odd/even from memory, compiled and ran them
[ ] Re-read 13.1, 13.2 and 13.4 the day before the interview
```

---

## What's next

The DSA, OOP and OS handbooks are complete. The same structure (Part 1 roadmap → modules → consolidation) can be applied to the remaining core-CS subjects interviewers pair with OS, namely **DBMS** (SQL, normalisation, transactions, indexing) and **Computer Networks** (TCP/IP, HTTP, DNS, "what happens when you type a URL"), whenever you want to start them.
