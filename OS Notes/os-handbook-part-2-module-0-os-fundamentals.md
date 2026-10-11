# Operating Systems Placement Handbook — Part 2
# Module 0: OS Fundamentals

**Module 0 · 2 hours · Tier 1 · Requires: nothing**

---

## Why this module exists

Interviewers open the OS segment with "what is an operating system?" or "what is a kernel?", and follow with the question that actually separates candidates: **"what happens when your program calls `read()`?"** Answering it requires three ideas from this module: **two CPU modes**, **system calls as controlled entry points into the kernel**, and **interrupts**. Every later module depends on them:

- Scheduling (M3) works because a **timer interrupt** returns control to the kernel.
- Synchronization (M4) needs **atomic instructions** and the kernel's ability to block threads.
- Memory protection (M6–M7) works because only **kernel mode** can change page tables.

The organising principle:

> **An operating system is the one program that runs in the CPU's privileged mode. Every other program runs restricted, and can reach hardware, memory it doesn't own, or other processes only by asking the kernel through a system call, or by being interrupted. Everything an OS does is a consequence of that boundary.**

---

## 0.1 What an operating system is

### 1. What is it?

Software that **manages hardware resources** and **provides services and abstractions** to programs. It sits between applications and hardware.

```
   +---------------------------------------------------+
   |  Applications (browser, compiler, your a.out)     |   user mode
   +---------------------------------------------------+
   |  System libraries (libc, libstdc++)               |   user mode
   +===================================================+  <- system call boundary
   |  Kernel: scheduler, memory manager, file systems, |   kernel mode
   |          drivers, network stack, IPC              |
   +---------------------------------------------------+
   |  Hardware: CPU, RAM, disk, NIC, devices           |
   +---------------------------------------------------+
```

### 2. Two views (a good way to open your answer)

| View | Meaning | Example |
|---|---|---|
| **Resource manager** | Decides who gets the CPU, memory, disk and devices, when, and how much; enforces fairness and protection | The scheduler shares one CPU among 200 processes |
| **Extended machine (abstraction)** | Hides ugly hardware details behind clean abstractions | "Files" instead of disk sectors, "processes" instead of raw CPU state, "sockets" instead of NIC registers |

### 3. Functions of an OS (asked as a list)

| Function | What it involves | Module |
|---|---|---|
| **Process management** | Create, schedule, terminate processes and threads | M1–M3 |
| **Synchronization and IPC** | Coordination, communication, deadlock handling | M4, M5, M9 |
| **Memory management** | Allocate memory, protect it, provide virtual memory | M6, M7 |
| **File system management** | Files, directories, permissions, storage allocation | M8 |
| **I/O and device management** | Drivers, buffering, scheduling of devices | M8, M9 |
| **Protection and security** | Isolation between processes, users, permissions | throughout |
| **User interface** | Shell (CLI) or GUI, technically outside the kernel | — |

### 4. OS vs kernel

| | Operating system | Kernel |
|---|---|---|
| Scope | Kernel + system libraries + system utilities + shell/GUI | The core part that runs in kernel mode |
| Example | Ubuntu, Windows 11, Android | Linux kernel, Windows NT kernel |
| Always resident in memory | Not all of it | Yes (core parts) |

**Android and Ubuntu both use the Linux kernel but are very different operating systems.** This one line shows you understand the distinction.

### 5. Must remember

1. OS = resource manager + extended machine.
2. The kernel is the privileged core; the OS includes more (libraries, utilities, shell).
3. The OS's main jobs: process, memory, file, I/O management, and protection.

---

## 0.2 User mode vs kernel mode

### 1. What is it?

The CPU has (at least) two privilege levels, selected by a **mode bit** in a CPU register:

| | User mode | Kernel mode (supervisor / privileged) |
|---|---|---|
| Who runs here | Applications, libraries | The kernel |
| Privileged instructions | **Forbidden**: attempting one traps to the kernel | Allowed |
| Memory access | Only the process's own mapped memory | All memory |
| Crash impact | Only that process dies | The whole system can crash (kernel panic / blue screen) |
| x86 name | Ring 3 | Ring 0 |

### 2. Why does it exist?

**Protection.** If any program could execute any instruction, one buggy or malicious program could overwrite another's memory, disable interrupts and freeze the machine, or read the disk directly and bypass file permissions. Dual mode makes the kernel the only code that can do dangerous things, and forces everyone else to ask.

### 3. Privileged instructions (examples interviewers like)

- Performing I/O directly on devices
- Modifying page tables / the memory-management unit (MMU) registers
- Setting the timer
- Enabling or disabling interrupts
- Halting the CPU
- Switching the mode bit itself

### 4. How the mode changes

```
   user mode ----- system call (trap instruction) ----> kernel mode
   user mode ----- interrupt (timer, device)      ----> kernel mode
   user mode ----- exception (page fault, /0)     ----> kernel mode
   kernel mode --- return-from-trap instruction   ----> user mode
```

**User code can never simply set the mode bit itself.** The only ways into kernel mode go through **entry points the kernel registered in advance** (the interrupt/trap vector table), so the kernel always controls what code runs with privilege.

### 5. Must remember

1. A mode bit selects user vs kernel mode. x86: ring 3 vs ring 0.
2. Privileged instructions in user mode cause a trap, not execution.
3. Entry into kernel mode happens only via system calls, interrupts or exceptions, always to kernel-defined handlers.

---

## 0.3 System calls

### 1. What is it?

**The programming interface through which a user program requests a service from the kernel**: reading a file, creating a process, allocating memory, sending network data.

### 2. Why does it exist?

User programs can't do privileged work themselves (§0.2). The system call is the **controlled doorway**: the program states what it wants, the kernel checks permissions, does the work in kernel mode, and returns.

### 3. How it works, step by step (the core answer)

What happens when your C program calls `read(fd, buf, 100)`:

```
 USER MODE                                     KERNEL MODE
 ---------                                     -----------
 1. your code calls read(fd, buf, 100)
    (a libc wrapper function)
 2. wrapper puts the syscall NUMBER
    (read = 0 on x86-64 Linux) in a register,
    and the arguments in other registers
 3. executes the trap instruction  ---------->  4. CPU switches to kernel mode, saves user
    ('syscall' on x86-64)                          registers, jumps to the kernel's entry point
                                                5. kernel looks up handler in the
                                                   SYSTEM CALL TABLE by number
                                                6. handler validates arguments
                                                   (is fd open? is buf a valid USER address?)
                                                7. does the work (may BLOCK the process
                                                   until disk/network data arrives -> M1, M3)
                                                8. puts the return value in a register
 10. wrapper returns the value to your  <------ 9. return-from-trap ('sysret'): restore
     code (or -1 and sets errno)                   registers, switch back to user mode
```

### 4. Why a system call costs more than a function call

| Cost | Why |
|---|---|
| Mode switch | Trap entry and exit, saving and restoring registers |
| Validation | The kernel must check every pointer and argument (never trust user input) |
| Cache and TLB effects | Kernel code and data evict user data; with kernel page-table isolation (a Meltdown mitigation), extra address-space switching |
| Possible blocking | A `read` may put the process to sleep, which means a context switch (M1) |

**Typical order of magnitude:** a plain function call costs a few nanoseconds; a minimal system call costs roughly a hundred nanoseconds to around a microsecond, depending on hardware and mitigations. This is why buffered I/O exists: `printf`/`fwrite` collect bytes in a user-space buffer and call `write()` once per buffer, not once per character.

### 5. Library function vs system call

| | Library function (`printf`, `fopen`, `malloc`) | System call (`write`, `open`, `brk`/`mmap`) |
|---|---|---|
| Runs in | User mode | Kernel mode |
| Cost | Cheap | Expensive (mode switch) |
| Portability | Portable (C standard) | OS-specific (POSIX, Win32) |
| Relationship | **Often wraps** system calls and adds buffering | The actual kernel service |

`printf` → formats into a buffer → eventually `write()`. `malloc` → manages a user-space heap → calls `brk`/`mmap` only when it needs more memory from the kernel. **Most `malloc` calls make no system call at all.** That's a good detail to mention.

### 6. Categories of system calls

| Category | POSIX examples | Windows examples |
|---|---|---|
| Process control | `fork`, `exec`, `exit`, `wait`, `kill` | `CreateProcess`, `ExitProcess`, `WaitForSingleObject` |
| File management | `open`, `read`, `write`, `close`, `lseek` | `CreateFile`, `ReadFile`, `WriteFile`, `CloseHandle` |
| Device management | `ioctl`, `read`, `write` | `DeviceIoControl` |
| Information | `getpid`, `time`, `uname` | `GetCurrentProcessId`, `GetSystemTime` |
| Communication | `pipe`, `socket`, `shmget`, `mmap` | `CreatePipe`, `CreateFileMapping` |
| Protection | `chmod`, `chown`, `umask` | `SetFileSecurity` |

### 7. Must remember

1. A system call is a **trap** into the kernel through a numbered table; arguments are passed in registers.
2. The kernel **validates** every argument, especially user pointers.
3. It's expensive compared with a function call (mode switch, validation, cache effects, possible blocking).
4. Library functions often wrap system calls with buffering (`printf` → `write`).
5. `malloc` usually doesn't make a system call.

### 8. Interview questions

- *"What is a system call?"* The interface for a user program to request a kernel service. The program places a call number and arguments in registers and executes a trap instruction; the CPU switches to kernel mode and runs the handler from the system call table, which validates the arguments, does the work and returns. *Follow-up: "Why not just call kernel functions directly?"* User code can't execute privileged instructions or touch kernel memory. The trap is the only controlled entry, which is what makes protection possible.
- *"Is `printf` a system call?"* No. It's a library function that formats into a buffer and eventually calls the `write` system call.

---

## 0.4 Interrupts, traps, and exceptions

### 1. What is it?

Events that make the CPU **stop what it's doing and jump to a kernel handler**.

| | Interrupt (hardware) | Trap / software interrupt | Exception (fault) |
|---|---|---|---|
| Source | External device: timer, keyboard, disk, NIC | **Deliberate** instruction in the program | **Error** caused by the current instruction |
| Timing | **Asynchronous**: can arrive at any time | **Synchronous**: at that instruction | **Synchronous** |
| Example | Timer tick, "disk read finished", packet arrived | System call (`syscall` instruction), debugger breakpoint | Divide by zero, invalid opcode, **page fault**, segmentation violation |
| After handling | Resume the interrupted instruction stream | Resume after the trap instruction | Retry the instruction (page fault) or kill the process (illegal access) |

Terminology varies between textbooks (some call all of these "interrupts"). The essential distinction is **asynchronous (device-caused) vs synchronous (instruction-caused)**.

### 2. How an interrupt is handled

```
 1. Device raises an interrupt line (or an instruction traps)
 2. CPU finishes the current instruction (for hardware interrupts)
 3. CPU saves the minimal state (PC, flags) and switches to kernel mode
 4. CPU indexes the INTERRUPT VECTOR TABLE (x86: IDT) with the interrupt number
 5. Jumps to the interrupt service routine (ISR / handler)
 6. Handler saves remaining registers, services the device (e.g. copies data,
    marks a waiting process READY), acknowledges the interrupt
 7. Restore state; return-from-interrupt -> resume (possibly a DIFFERENT process,
    if the scheduler decided to switch: M1, M3)
```

### 3. Why interrupts matter for the rest of the course

- **The timer interrupt makes preemption possible.** Without it, a process in an infinite loop would never give the CPU back. The kernel sets a timer before running a process; when it fires, the kernel regains control and can schedule another (M3).
- **I/O completion interrupts** let the CPU do useful work while a disk is busy, instead of **polling** (repeatedly checking the device). That's the basis of multiprogramming (§0.6) and of DMA (M9).
- **Page faults** are exceptions; demand paging (M7) is built on them.

### 4. Polling vs interrupts

| | Polling (busy-waiting) | Interrupt-driven |
|---|---|---|
| How | CPU repeatedly checks the device status | Device notifies the CPU when ready |
| CPU use while waiting | Wasted | Free for other work |
| Latency | Can be lowest (no handler overhead) | Handler overhead |
| Good for | Very fast devices or very frequent events (high-speed networking uses hybrid polling) | Most devices |

### 5. Must remember

1. Interrupt = asynchronous, from hardware. Trap/exception = synchronous, from the current instruction.
2. System calls are implemented as traps; page faults are exceptions.
3. The interrupt vector table maps interrupt numbers to handlers.
4. The timer interrupt is what lets the OS preempt processes.

### 6. Interview question

- *"Difference between an interrupt and a trap?"* An interrupt is an asynchronous signal from hardware (timer, disk, keyboard) unrelated to the current instruction. A trap is synchronous, caused by the instruction being executed: deliberately for a system call, or by an error such as divide-by-zero or a page fault. Both switch to kernel mode and run a handler from the vector table. *Follow-up: "Why does the OS need a timer interrupt?"* To regain control from a process that never yields, which is the basis of preemptive scheduling.

---

## 0.5 Kernel architectures

### 1. The options

```
  MONOLITHIC                      MICROKERNEL                       HYBRID
  +-------------------------+     +------+ +------+ +------+        +-------------------------+
  | user apps               |     |  FS  | |driver| | net  | user   | user apps   | some     |
  +=========================+     |server| |server| |server| mode   |             | servers  |
  | ONE big kernel:         |     +--+---+ +--+---+ +--+---+        +=========================+
  | scheduler, memory, FS,  |        |  IPC messages |              | kernel: core + many    |
  | drivers, network, IPC   |     +==+=============+=====+ kernel   | services (FS, drivers) |
  | (all in kernel mode)    |     | tiny kernel: IPC,    | mode     | for speed              |
  +-------------------------+     | scheduling, memory   |          +-------------------------+
                                  +----------------------+
```

| | Monolithic | Microkernel | Hybrid |
|---|---|---|---|
| What runs in kernel mode | Everything: scheduler, memory, file systems, drivers, networking | Only the minimum: IPC, basic scheduling, address spaces | A core plus selected services |
| Communication between parts | Direct function calls | **Message passing (IPC)** between user-mode servers | Mixed |
| Performance | **Fast** (no IPC overhead) | Slower (each service request crosses address spaces) | Close to monolithic |
| Reliability and isolation | A driver bug can crash the whole kernel | A crashed driver server can be **restarted**; the kernel survives | In between |
| Size of trusted code | Large | **Small** (easier to verify; seL4 is formally verified) | Medium |
| Examples | **Linux** (monolithic but **modular**: loadable kernel modules), traditional Unix | Minix 3, QNX, seL4 | **Windows NT** family, **macOS XNU** |

**Linux nuance worth saying:** Linux is monolithic, but drivers can be **loadable kernel modules** (`insmod`/`modprobe`), loaded at runtime. They still run in kernel mode, so this is about *modularity*, not *isolation*.

### 2. Interview line

*"A monolithic kernel runs all OS services in kernel mode with direct calls between them, so it's fast but a buggy driver can crash everything. Linux is the main example, though it supports loadable modules. A microkernel keeps only IPC, scheduling and memory management in the kernel and runs drivers and file systems as user-mode servers communicating by messages. That's more robust and secure, but slower. Windows and macOS are hybrids."*

---

## 0.6 Types of operating systems

The historical progression explains *why* modern OS features exist:

| Type | Idea | Problem it solved | Limitation |
|---|---|---|---|
| **Batch** | Jobs collected and run one after another, with no interaction | Manual setup between jobs | CPU idles during I/O; no interactivity |
| **Multiprogramming** | Several jobs in memory; when one waits for I/O, run another | **CPU idle during I/O** → better CPU utilisation | No responsiveness guarantee; a CPU-bound job can hog the CPU |
| **Multitasking / time-sharing** | Multiprogramming + **preemption with time slices** (timer interrupt) | **Interactivity**: many users or programs feel simultaneous | Context-switch overhead |
| **Multiprocessing** | Several CPUs/cores share memory | More throughput; parallelism | Synchronization complexity (M4) |
| **Distributed** | Many networked machines appear as one system | Scale, fault tolerance | Network failures, consistency |
| **Real-time (RTOS)** | Guarantees that tasks finish **within deadlines** | Predictability for control systems | Throughput is secondary |
| **Embedded** | Minimal OS for a dedicated device | Small footprint | Limited features |

### Multiprogramming vs multitasking (asked often)

| | Multiprogramming | Multitasking (time-sharing) |
|---|---|---|
| Goal | **Maximise CPU utilisation** | **Minimise response time** (interactivity) |
| Switch happens when | The running job **waits for I/O** (voluntary) | The **time slice expires** (preemptive) or it waits |
| Needs a timer interrupt | No | **Yes** |
| User experience | Batch-like | Feels simultaneous |

### Hard vs soft real-time

| | Hard real-time | Soft real-time |
|---|---|---|
| Missing a deadline | **System failure** | Degraded quality, tolerated occasionally |
| Examples | Airbag controller, pacemaker, anti-lock brakes | Video streaming, online games, audio playback |

### Symmetric vs asymmetric multiprocessing

**SMP** (symmetric): every core runs the kernel and user processes as peers. This is what modern OSes do. **AMP** (asymmetric): one master core runs the OS and the others run assigned tasks; simpler, but the master is a bottleneck.

---

## 0.7 What happens when a computer boots

```
 1. Power on -> CPU starts executing FIRMWARE (BIOS or, on modern machines, UEFI)
    stored in non-volatile memory on the motherboard
 2. POST (power-on self-test): check RAM, CPU, basic devices
 3. Firmware finds a boot device (order configured in firmware settings)
      BIOS: loads the first sector (MBR) -> a tiny first-stage bootloader
      UEFI: reads the EFI system partition and runs a bootloader program (.efi)
 4. BOOTLOADER (e.g. GRUB on Linux, Windows Boot Manager) loads the KERNEL image
    (and, on Linux, an initial RAM disk, initramfs) into memory, then jumps to it
 5. KERNEL initialises: CPU and memory management (page tables), interrupt
    handlers, scheduler, drivers; mounts the ROOT file system
 6. Kernel starts the first user-space process, PID 1 (systemd / init on Linux)
 7. PID 1 starts system services (daemons), networking, and the login manager / shell
```

| Must remember |
|---|
| Firmware (BIOS/UEFI) → bootloader → kernel → init (PID 1) → services → login |
| The bootloader exists because firmware is too simple to understand file systems and kernel formats in full |
| PID 1 is the ancestor of every user process, and adopts orphans (M1) |
| UEFI replaced legacy BIOS: GPT disks larger than 2 TB, Secure Boot, a faster boot |

---

## 0.8 Consolidation

### Must remember (module)

1. OS = resource manager + extended machine; the kernel is its privileged core.
2. Dual mode: user (ring 3) vs kernel (ring 0); privileged instructions trap in user mode.
3. Entry into kernel mode only via system calls, interrupts or exceptions, to kernel-registered handlers.
4. System call: number + arguments in registers → trap → system call table → validate → work → return. Costs far more than a function call.
5. `printf`/`malloc` are library functions that sometimes make system calls (`write`, `brk`/`mmap`).
6. Interrupt (asynchronous, hardware) vs trap/exception (synchronous, instruction). The timer interrupt enables preemption.
7. Monolithic (Linux, modular) vs microkernel (QNX, Minix, seL4) vs hybrid (Windows NT, macOS).
8. Multiprogramming maximises CPU use; multitasking adds time slices for responsiveness.
9. Boot: firmware → bootloader → kernel → PID 1 → services.

### Common wrong answers (module)

- "The OS and the kernel are the same thing."
- "`printf` is a system call."
- "User programs can switch to kernel mode by setting a flag."
- "Linux is a microkernel because it has modules."
- "Multiprogramming and multitasking are the same."
- "Interrupts and traps are the same." (Asynchronous vs synchronous.)

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is an OS? | Software that manages hardware resources and provides abstractions to programs; resource manager + extended machine | Functions of an OS? |
| What is a kernel? | The core of the OS running in privileged mode: scheduling, memory, drivers, file systems | Monolithic vs micro? |
| User vs kernel mode? | Mode bit; privileged instructions and all memory only in kernel mode; protection | How does a program enter kernel mode? |
| What is a system call? | Controlled request to the kernel through a trap and a numbered table | Why is it expensive? |
| Interrupt vs trap? | Asynchronous hardware event vs synchronous instruction-caused event | Why does the OS need a timer interrupt? |
| Monolithic vs microkernel? | All services in the kernel (fast) vs minimal kernel + user servers via IPC (robust) | Example of each? |
| Multiprogramming vs multitasking? | CPU utilisation via switching on I/O vs responsiveness via time slices | What makes multitasking possible? (Timer) |
| Hard vs soft real-time? | A missed deadline is failure vs degraded quality | Examples |
| Boot process? | Firmware → POST → bootloader → kernel → PID 1 → services | What is PID 1? |

### Practice

**P1.** Classify each as a privileged or a non-privileged instruction: (a) add two registers, (b) disable interrupts, (c) read the system clock, (d) set the timer, (e) load a value into the page-table base register, (f) execute the `syscall` instruction.

<details><summary>Answer</summary>

Privileged: (b), (d), (e). Non-privileged: (a), (c) (reading the time is typically allowed, often via a fast user-space path), and (f) (executing `syscall` is how user code *enters* the kernel, so it must be allowed in user mode).
</details>

**P2.** A program calls `printf("x")` 1,000 times in a loop, writing to a file. Roughly how many `write` system calls happen, and why not 1,000?

<details><summary>Answer</summary>

Typically **one or a few**. When stdout goes to a file it is **fully buffered** (a buffer of several KB), so `printf` copies into the user-space buffer and calls `write()` only when the buffer fills or the program exits. To a terminal, stdout is **line-buffered** (flushed at each newline). This buffering exists precisely because system calls are expensive.
</details>

**P3.** Classify each event as an interrupt, a trap or an exception: (a) a key press, (b) `read()` called by a program, (c) dividing by zero, (d) accessing a page not currently in RAM, (e) a network packet arriving, (f) the scheduler's time slice ending.

<details><summary>Answer</summary>

(a) interrupt, (b) trap (system call), (c) exception, (d) exception (page fault), (e) interrupt, (f) interrupt (timer).
</details>

**P4.** Why is a buggy network driver more dangerous on Linux than on a microkernel OS like QNX?

<details><summary>Answer</summary>

On Linux, drivers run in kernel mode inside the kernel's address space, so a bad pointer can corrupt kernel memory and crash the whole system (kernel panic). On a microkernel, the driver is a user-mode server: a crash kills only that process, which can be restarted while the kernel keeps running.
</details>

---

## Exit checklist

```
[ ] I can define an OS two ways (resource manager, extended machine) and distinguish OS from kernel
[ ] I can explain user vs kernel mode, the mode bit, and list 4 privileged instructions
[ ] I can walk through a read() system call step by step, user mode to kernel mode and back
[ ] I can explain why system calls cost more than function calls, and why buffered I/O exists
[ ] I can distinguish library functions from system calls (printf -> write, malloc -> brk/mmap)
[ ] I can compare interrupts, traps and exceptions, and explain the timer interrupt's role
[ ] I can compare monolithic, micro and hybrid kernels with examples
[ ] I can compare multiprogramming vs multitasking, and hard vs soft real-time
[ ] I can describe the boot sequence from power-on to login
[ ] P1–P4 done
```

---

## Next

**Part 3: M1 — Processes.** It covers program vs process, the process memory layout, the PCB, the process state diagram, schedulers and queues, the context switch (and what makes it expensive), `fork`/`exec`/`wait` with **fork-output drills**, and zombie vs orphan processes.
