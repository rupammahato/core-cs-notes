# Operating Systems Placement Handbook — Part 10
# Module 8: Storage and File Systems

**Module 8 · 3 hours · Tier 2 (Tier 1 for inodes and hard vs soft links) · Requires: M1 (file descriptors, fork), M7 (page cache, mmap)**

---

## What this module covers, and what's asked

Storage questions in interviews cluster around four things:

1. **Disk scheduling numericals** (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK): common in written tests.
2. **Inodes and hard vs soft links**: the most common file-system questions at product companies, especially Linux-oriented ones.
3. **How a file read actually works**: file descriptors, open-file tables, the page cache.
4. **RAID levels and journaling**: occasional "do you know more" questions.

Allocation methods and directory structures are mostly exam material, so they're covered briefly.

**Disk-scheduling totals in this module were computed with code**, and the conventions (which direction, whether the C-SCAN return seek counts) are stated, because those are exactly where answers differ between sources.

The organising principle:

> **A file system turns a flat array of disk blocks into named, protected, growable files. Names point to inodes, inodes point to blocks, and the kernel caches all three. Disk scheduling exists because moving a hard disk's head is millions of times slower than computing, and it all but vanishes on SSDs, which have no head.**

---

## 8.1 Storage devices: HDD vs SSD

### 1. Hard disk drive (HDD) structure

```
        spindle
          |            platter (two surfaces)
     +----+----+       track = one ring on a surface
    /  .-----.  \      sector = a slice of a track (512 B / 4 KB)
   |  (   o   )  |     cylinder = the same track on all surfaces
    \  '-----'  /      arm moves the heads across tracks (SEEK)
     +---------+  <--- read/write head on the arm
```

**Access time = seek time + rotational latency + transfer time**

| Component | Meaning | Typical |
|---|---|---|
| **Seek time** | Move the head to the right track (cylinder) | ~3–10 ms (the **dominant** cost) |
| **Rotational latency** | Wait for the sector to rotate under the head; average = **half a rotation** | 7200 RPM → 60/7200 = 8.33 ms per rotation → **≈ 4.17 ms average** |
| **Transfer time** | Actually read the bits | Small for one block |

Disk scheduling (§8.2) minimises **seek time**: the order in which requests are served changes the total head movement.

### 2. Solid-state drive (SSD)

| | HDD | SSD |
|---|---|---|
| Mechanism | Spinning platters, moving head | Flash memory, no moving parts |
| Random access | **Slow** (seek + rotation: milliseconds) | **Fast** (tens of µs; NVMe even faster) |
| Seek-order sensitivity | High, so scheduling matters | **None**: "nearby" blocks aren't faster |
| Write behaviour | Overwrite in place | **Erase-before-write** in large erase blocks; a **Flash Translation Layer (FTL)** remaps writes |
| Wear | Mechanical failure | Limited program/erase cycles per cell → **wear levelling** spreads writes |
| Special features | — | **TRIM** (the OS tells the SSD which blocks are free), **write amplification** |

**Consequence:** classic seek-minimising algorithms matter for HDDs. On Linux, SSDs and NVMe typically use the **`none`** or **`mq-deadline`** I/O scheduler (minimal reordering), while HDDs may use **`mq-deadline`** or **`bfq`**.

---

## 8.2 Disk scheduling

### 1. The standard problem (used for every algorithm)

```
 Cylinders: 0 - 199
 Head starts at: 53
 Request queue (in arrival order): 98, 183, 37, 122, 14, 124, 65, 67
 Metric: total head movement (cylinders) = sum of |next - current|
```

### 2. FCFS: serve in arrival order

```
 53 -> 98 -> 183 -> 37 -> 122 -> 14 -> 124 -> 65 -> 67
 = 45 + 85 + 146 + 85 + 108 + 110 + 59 + 2 = 640
```

**Total: 640.** Fair, no starvation, but wild swings.

### 3. SSTF (Shortest Seek Time First): always go to the closest pending request

```
 53 -> 65 (12) -> 67 (2) -> 37 (30) -> 14 (23) -> 98 (84) -> 122 (24) -> 124 (2) -> 183 (59)
```

**Total: 236.** Much better than FCFS, but **starvation**: requests far from a busy region can wait indefinitely (like SJF, M3). It's also not optimal; it's greedy.

### 4. SCAN (the elevator algorithm): sweep to one end, then reverse

Assume the head is moving **toward 0**:

```
 53 -> 37 -> 14 -> 0 (end of disk) -> reverse -> 65 -> 67 -> 98 -> 122 -> 124 -> 183
 = (53 - 0) + (183 - 0) = 53 + 183 = 236
```

**Total: 236.** (Moving toward 199 first instead: 53 → 65 … 183 → 199 → 37 → 14 = 146 + 185 = **331**. **Always state the direction.**)

- No starvation; bounded wait.
- Requests just behind the head wait for a full round trip. Cylinders at the edges are visited less often than the middle.

### 5. C-SCAN (Circular SCAN): sweep in one direction only, jump back, repeat

Moving **toward 199**:

```
 53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 199 (end) -> JUMP to 0 -> 14 -> 37
```

| Convention | Total |
|---|---|
| Counting the return seek 199 → 0 | (199 − 53) + 199 + 37 = **382** |
| Not counting the return (it's a fast return without servicing) | 146 + 37 = **183** |

**More uniform wait times** than SCAN: the disk is treated as a circular list, so every cylinder is served once per sweep in the same direction.

### 6. LOOK and C-LOOK: like SCAN and C-SCAN, but only go as far as the last request

**LOOK** (moving toward 0):
```
 53 -> 37 -> 14 -> reverse (no need to touch 0) -> 65 -> 67 -> 98 -> 122 -> 124 -> 183
 = (53 - 14) + (183 - 14) = 39 + 169 = 208
```

**Total: 208.** (Toward 199 first: 299.)

**C-LOOK** (moving toward 199):
```
 53 -> 65 -> ... -> 183 -> JUMP to 14 -> 37
```

| Convention | Total |
|---|---|
| Counting the jump 183 → 14 | 130 + 169 + 23 = **322** |
| Not counting the jump | 130 + 23 = **153** |

### 7. Summary for this problem (verified)

| Algorithm | Order of service | Total movement |
|---|---|---|
| FCFS | 98, 183, 37, 122, 14, 124, 65, 67 | **640** |
| SSTF | 65, 67, 37, 14, 98, 122, 124, 183 | **236** |
| SCAN (toward 0) | 37, 14, [0], 65 … 183 | **236** |
| C-SCAN (toward 199, return counted) | 65 … 183, [199], [0], 14, 37 | **382** |
| LOOK (toward 0) | 37, 14, 65 … 183 | **208** |
| C-LOOK (toward 199, jump counted) | 65 … 183, 14, 37 | **322** |

### 8. Comparison

| Algorithm | Starvation? | Pros | Cons |
|---|---|---|---|
| FCFS | No | Fair, simple | Huge seeks |
| SSTF | **Yes** | Low average seek | Starvation; greedy, not optimal |
| SCAN | No | Bounded wait | Goes to the disk end unnecessarily; uneven waits |
| C-SCAN | No | **Uniform** wait times | Extra return travel |
| LOOK | No | SCAN without the useless trips to the end | |
| C-LOOK | No | Uniform waits + no useless trips | |

**Exam conventions to state:** the initial direction, whether 0 and the maximum cylinder are touched (SCAN/C-SCAN do, LOOK/C-LOOK don't), and whether the return jump counts.

---

## 8.3 Files and how the kernel tracks open files

### 1. File attributes (metadata)

Name, identifier (inode number), type, location (block pointers), size, protection (permissions, owner, group), timestamps (access, modification, status change), link count.

### 2. Operations

`create`, `open`, `read`, `write`, `lseek` (reposition), `close`, `unlink` (delete), `truncate`, plus metadata operations (`stat`, `chmod`, `rename`).

### 3. The three tables (an important Linux question)

```
  Process A                        System-wide                     In-memory
  fd table                         open-file table                 inode table
  +----+---------+                 +---------------------+         +-----------------+
  | 0  | stdin --+---------------->| offset, mode, flags |-------->| inode 1234      |
  | 1  | stdout  |                 | refcount            |         | (size, perms,   |
  | 2  | stderr  |                 +---------------------+         |  block ptrs)    |
  | 3  | --------+---+             +---------------------+    +--->|                 |
  +----+---------+   +------------>| offset = 4096       |----+    +-----------------+
                                   | refcount = 2        |    |
  Process B (child after fork)     +---------------------+    |
  +----+---------+                         ^                  |
  | 3  | --------+-------------------------+                  |
  +----+---------+                                            |
  Process C: open() the same file again -> NEW open-file entry (own offset) -> same inode
```

| Table | Scope | Holds |
|---|---|---|
| **File descriptor table** | Per process | Small integers (0, 1, 2, 3, …) → pointers to open-file entries |
| **Open-file table** (file description) | System-wide | **Current offset**, access mode, reference count |
| **Inode table** (v-node) | System-wide, one per file | The file's metadata and block locations |

**Consequences (asked as follow-ups):**
- After **`fork`**, parent and child **share open-file entries**, so they **share the file offset**. A write by one advances the position for both (M1 §1.6).
- **`dup`/`dup2`** create another fd pointing to the **same** open-file entry (the basis of shell redirection, M1).
- Two independent **`open()`** calls on the same file get **separate offsets**.
- File descriptors 0, 1, 2 = stdin, stdout, stderr. `open` returns the **lowest** free descriptor.

### 4. What happens on `read(fd, buf, n)` (connects M0, M6, M7)

```
 system call (trap, M0) -> fd table -> open-file entry (offset) -> inode -> which block?
   -> is that block in the PAGE CACHE (RAM)?
        yes: copy to buf (fast)                      <- most reads end here
        no : issue a disk read (I/O scheduler, 8.2), process BLOCKS (M1), interrupt on
             completion, the data lands in the page cache, then copy to buf
   -> advance the offset -> return the byte count
```

The **page cache** is why the second read of a file is far faster than the first, and why "free" memory on Linux looks low (it's used as cache, and released on demand).

---

## 8.4 Directory structures (brief)

| Structure | Description | Problem |
|---|---|---|
| **Single-level** | One directory for everyone | Name collisions; no grouping |
| **Two-level** | One directory per user | No sub-grouping; sharing is awkward |
| **Tree** | Arbitrary subdirectories; absolute and relative paths | Sharing a file between two places isn't possible |
| **Acyclic graph** | A tree plus **links**, so a file or directory can appear in several places | Deletion (dangling links), traversal counting files twice |
| **General graph** | Links can create **cycles** | Traversal loops; garbage collection needed. That's why Unix forbids hard links to directories |

---

## 8.5 File allocation methods

How a file's blocks are located on disk:

| Method | How | Pros | Cons | Real use |
|---|---|---|---|---|
| **Contiguous** | Start block + length; blocks adjacent | Fast sequential and **direct** access; minimal seeks | **External fragmentation**; files can't grow easily | CD/DVD (ISO 9660); extents in modern FSes |
| **Linked** | Each block points to the next | No external fragmentation; easy growth | **Sequential access only** (direct access is O(n)); a pointer in every block; one bad pointer loses the rest | **FAT**: the pointers are kept in a separate table (the File Allocation Table), cached in RAM |
| **Indexed** | An **index block** lists all of the file's blocks | Direct access; no external fragmentation | Index-block overhead; large files need multi-level indexes | **Unix inodes**, ext2/3 |

**Modern file systems (ext4, NTFS, XFS, APFS) use extents**: contiguous runs of blocks recorded as (start, length). That's contiguous allocation's speed with indexed allocation's flexibility.

---

## 8.6 Inodes

### 1. What is an inode?

An **index node**: the on-disk structure that stores **everything about a file except its name and its data**.

| An inode contains | An inode does NOT contain |
|---|---|
| File type (regular, directory, symlink, device…) | **The file name** |
| Permissions (rwx for owner/group/others), owner UID, group GID | The data itself (except tiny inline data in some FSes) |
| Size | |
| Timestamps: **atime** (access), **mtime** (content modified), **ctime** (inode changed) | |
| **Link count** (the number of hard links / directory entries) | |
| **Pointers to data blocks** (direct, single/double/triple indirect) | |

**Where's the name?** In the **directory**. A directory is a special file that maps **names → inode numbers**. `ls -i` shows the inode numbers.

### 2. Classic Unix block pointers and maximum file size

```
 inode
 +--------------------+
 | 12 direct pointers | ---> 12 data blocks
 | single indirect    | ---> [block of pointers] ---> data blocks
 | double indirect    | ---> [ptrs] -> [ptrs] ---> data blocks
 | triple indirect    | ---> [ptrs] -> [ptrs] -> [ptrs] ---> data blocks
 +--------------------+
```

**Numerical:** 4 KB blocks, 4-byte pointers → **1024 pointers per block**.

| Level | Blocks addressable | Data |
|---|---|---|
| 12 direct | 12 | 48 KB |
| Single indirect | 1024 | 4 MB |
| Double indirect | 1024² ≈ 1 M | 4 GB |
| Triple indirect | 1024³ ≈ 1 G | 4 TB |
| **Maximum file size** | | **≈ 4 TB** (+ 4 GB + 4 MB + 48 KB) |

**Why this design:** most files are small and are served entirely by the direct pointers (fast). Large files pay the extra lookups only for their later blocks.

### 3. Inode facts that show depth

- A file system has a **fixed number of inodes** (decided at format time on ext2/3/4). You can run out of inodes with free space left (millions of tiny files): `df -i`.
- **Deleting** a file = `unlink`: remove the directory entry and decrement the link count. The inode and data are freed only when **link count = 0 and no process has the file open**. That's why deleting a large log file that a process still has open frees no space until the process closes it.
- `mv` within one file system just changes directory entries (fast; the inode is unchanged). Across file systems it's a copy plus a delete.

---

## 8.7 Hard links vs soft (symbolic) links

### 1. The picture

```
 HARD LINK:  ln original.txt hard.txt
   directory entries:  original.txt ---+
                                        +---> inode 1234 (link count = 2) ---> data blocks
                       hard.txt -------+

 SOFT LINK:  ln -s original.txt soft.txt
   soft.txt ---> inode 5678 (type: symlink, contents: "original.txt")
                     | path lookup at access time
                     v
   original.txt ---> inode 1234 ---> data blocks
```

### 2. The comparison (asked often)

| | Hard link | Soft (symbolic) link |
|---|---|---|
| What it is | **Another directory entry (name) for the same inode** | **A separate file (own inode)** whose content is a **path** |
| Inode number | **Same** as the original | **Different** |
| If the original name is deleted | **Data survives** (the link count drops; the data stays while count > 0) | **Dangling link**: points to a path that no longer exists |
| Across file systems / partitions | **No** (inode numbers are per file system) | **Yes** (it's just a path) |
| To directories | **Not allowed** (normally, to prevent cycles) | **Allowed** |
| Increases the link count | **Yes** | No |
| Size | No extra data (just a directory entry) | Small (the length of the path) |
| Performance | Direct | One extra path resolution |
| Command | `ln target name` | `ln -s target name` |
| Windows analogue | NTFS hard links | Symbolic links / junctions / (loosely) shortcuts |

**Model answer:** *"A hard link is just another name for the same inode, so both names are equal, the data survives until the last name is removed, but it can't cross file systems or point to directories. A soft link is a separate small file that stores a path; it can point anywhere, including directories and other file systems, but it breaks if the target is moved or deleted."*

### 3. Quick drill

```
$ echo hi > a.txt
$ ln a.txt h.txt          # hard link
$ ln -s a.txt s.txt       # soft link
$ rm a.txt
$ cat h.txt               # -> hi                    (same inode still has a name)
$ cat s.txt               # -> No such file or directory (dangling: "a.txt" no longer exists)
```

---

## 8.8 Free-space management (brief)

| Method | How | Notes |
|---|---|---|
| **Bitmap (bit vector)** | One bit per block (1 = free, or the opposite) | Easy to find contiguous free blocks; the bitmap must be in RAM (1 TB disk with 4 KB blocks → 2²⁸ bits = **32 MB**) |
| **Linked list** | Free blocks chained together | No extra space, but slow to traverse |
| **Grouping** | The first free block stores the addresses of n free blocks | Faster than a plain list |
| **Counting** | Store (start, count) runs of free blocks | Compact when free space is contiguous (extent-style) |

---

## 8.9 Crash consistency: journaling (Tier 2)

### 1. The problem

Creating a file updates several structures (the inode, the directory, the free-space bitmap). A **crash in the middle** leaves them inconsistent: a block marked used but owned by no file, or a directory entry pointing to an unallocated inode.

### 2. Solutions

| Approach | How | Trade-off |
|---|---|---|
| **fsck** (file system check) | Scan the **entire** disk after a crash and repair it | Very slow on large disks (hours) |
| **Journaling** (write-ahead logging) | First write the intended changes to a **journal**; then apply them; on a crash, **replay** (or discard) the journal | Fast recovery (seconds); some extra writes |
| **Copy-on-write file systems** | Never overwrite in place; write new blocks, then atomically switch a root pointer | Always consistent; enables cheap **snapshots** (ZFS, Btrfs, APFS) |

**ext4's default** is **metadata journaling in "ordered" mode**: data blocks are written before the metadata that points to them is committed, so metadata never points to garbage. Full **data journaling** is safer but writes everything twice.

---

## 8.10 RAID (Tier 2/3)

**Redundant Array of Independent Disks:** combine disks for **performance**, **redundancy**, or both. N = number of disks.

| Level | Technique | Usable capacity | Survives | Read | Write | Min disks |
|---|---|---|---|---|---|---|
| **RAID 0** | **Striping** (blocks split across disks) | N (100%) | **0 failures**: any failure loses everything | Fast | Fast | 2 |
| **RAID 1** | **Mirroring** (identical copies) | N/2 (for pairs) | 1 per mirror set | Fast (read from either) | Same as one disk | 2 |
| **RAID 5** | Striping + **distributed parity** | N − 1 | **1** failure | Fast | **Slower** (read-modify-write parity) | 3 |
| **RAID 6** | Striping + **double parity** | N − 2 | **2** failures | Fast | Slower than RAID 5 | 4 |
| **RAID 10 (1+0)** | Mirrors, then stripe across them | N/2 | 1 per mirror pair (possibly more) | Fast | Fast | 4 |

**Parity in one line:** parity = XOR of the data blocks in a stripe, so any **one** missing block = XOR of the remaining blocks plus the parity (the XOR property `a ^ a = 0`, DSA Part 16).

**Two points worth saying:**
- **RAID is not a backup.** It protects against disk failure, not against deletion, corruption, ransomware or fire.
- **The RAID 5 rebuild risk:** rebuilding a large array reads every surviving disk, and a second failure or unreadable sector during the rebuild loses the array. That's why large arrays prefer RAID 6 or RAID 10.

---

## 8.11 Consolidation

### Must remember (module)

1. HDD access = seek + rotational latency (half a rotation on average: 4.17 ms at 7200 RPM) + transfer; seek dominates. SSDs have no seek; FTL, wear levelling, TRIM.
2. Disk scheduling (head 53; 98, 183, 37, 122, 14, 124, 65, 67): **FCFS 640, SSTF 236, SCAN (toward 0) 236, C-SCAN 382 (return counted), LOOK (toward 0) 208, C-LOOK 322 (jump counted).** State the direction and conventions.
3. SSTF starves; SCAN/LOOK are elevators; C-SCAN/C-LOOK give uniform waits; SSDs use minimal reordering.
4. Three tables: per-process fd → system-wide open-file entry (**offset**) → inode. Fork and dup **share offsets**; separate opens don't.
5. `read`: page cache hit → copy; miss → disk I/O, block, interrupt, cache, copy.
6. Allocation: contiguous (fast, external fragmentation), linked/FAT (sequential), indexed/inode (direct access); modern FSes use extents.
7. Inode = metadata + block pointers + link count, **not the name**; the directory maps names → inodes.
8. 4 KB blocks, 4 B pointers: max file ≈ 4 TB with 12 direct + single/double/triple indirect.
9. Data is freed when link count = 0 **and** no open file descriptors remain.
10. Hard link = same inode, survives deletion of the original, no cross-FS, no directories. Soft link = path file, can dangle, can cross FS and point to directories.
11. Journaling (write-ahead log) vs fsck vs copy-on-write file systems.
12. RAID 0/1/5/6/10: capacity and fault tolerance; RAID ≠ backup.

### Common wrong answers (module)

- "The inode stores the file name."
- "Deleting the original breaks a hard link."
- "Soft links share the inode of the target."
- "SSTF is optimal." (It's greedy and starves requests.)
- "Disk scheduling matters just as much on SSDs."
- "Deleting a file immediately frees its space." (Not while it's still open.)
- "RAID 1 is a backup."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| Disk scheduling algorithms? | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK; minimise seeks | Compute total head movement |
| Why does SSTF starve? | Requests near the head keep winning | Which algorithm fixes it? (SCAN) |
| What's an inode? | On-disk metadata + block pointers, without the name | Where is the name stored? |
| Hard vs soft link? | Same inode vs a path file; survives deletion vs dangles | Why no hard links to directories? (Cycles) |
| What happens when you delete an open file? | The name is removed; data freed when the last fd closes | How do you find such files? (`lsof +L1`) |
| What do fork and dup share? | Open-file entries, hence offsets | And two separate opens? |
| What is journaling? | Write-ahead log of changes for fast crash recovery | ext4 modes? CoW file systems? |
| RAID levels? | 0 stripe, 1 mirror, 5 parity, 6 double parity, 10 mirror+stripe | Which for a database? (10) RAID vs backup? |
| HDD vs SSD for the OS? | Seek-free random access; different I/O scheduling | What is TRIM? |

### Practice numericals

**N1.** Head at 50, cylinders 0–199, queue: 82, 170, 43, 140, 24, 16, 190. Compute total movement for FCFS, SSTF, SCAN (toward 199), C-SCAN (toward 199, return counted) and LOOK (toward 199).

<details><summary>Answer</summary>

- **FCFS:** 50→82→170→43→140→24→16→190 = 32+88+127+97+116+8+174 = **642**
- **SSTF:** 50→43 (7) →24 (19) →16 (8) →82 (66) →140 (58) →170 (30) →190 (20) = **208**
- **SCAN up:** 50→82→140→170→190→199→43→24→16 = (199−50) + (199−16) = 149 + 183 = **332**
- **C-SCAN up (return counted):** 50→…→190→199→0→16→24→43 = 149 + 199 + 43 = **391**
- **LOOK up:** 50→…→190→43→24→16 = (190−50) + (190−16) = 140 + 174 = **314**
</details>

**N2.** A disk spins at 10,000 RPM with an average seek of 4 ms. What's the average time to read one random 4 KB block, ignoring transfer time?
<details><summary>Answer</summary>

One rotation = 60/10,000 s = 6 ms → average rotational latency = **3 ms**. Total ≈ 4 + 3 = **7 ms**.
</details>

**N3.** Blocks are 1 KB and pointers 4 B. An inode has 10 direct pointers and one single-indirect pointer. What's the maximum file size?
<details><summary>Answer</summary>

Pointers per block = 1024/4 = 256. Max = (10 + 256) × 1 KB = **266 KB**.
</details>

**N4.** `a.txt` has link count 1. You run `ln a.txt b.txt`, then `ln -s a.txt c.txt`, then `rm a.txt`. What are the link count of the original inode, and the result of `cat b.txt` and `cat c.txt`?
<details><summary>Answer</summary>

After `ln`: count 2. The symlink doesn't change it. After `rm a.txt`: **count 1**. `cat b.txt` → the contents (same inode). `cat c.txt` → **error** (dangling: "a.txt" no longer exists).
</details>

---

## Exit checklist

```
[ ] I can explain HDD access time components and compute average rotational latency
[ ] I can contrast HDD and SSD (seek, FTL, wear levelling, TRIM, scheduler choice)
[ ] I can compute total head movement for all six disk algorithms and state the conventions
[ ] I can explain the three open-file tables and what fork/dup share
[ ] I can trace a read() through the page cache to disk and back
[ ] I can compare contiguous, linked/FAT, indexed allocation and mention extents
[ ] I can list inode contents (not the name!) and compute the max file size from pointer levels
[ ] I can explain when deleted data is actually freed
[ ] I can deliver the hard vs soft link comparison and predict the rm drill
[ ] I can explain journaling vs fsck vs copy-on-write file systems
[ ] I can compare RAID 0/1/5/6/10 and say why RAID isn't a backup
[ ] N1–N4 done
```

---

## Next

**Part 11: M9 — IPC and I/O.** It covers pipes (with `pipe` + `fork` code), named pipes, message queues, shared memory, sockets, signals, shared memory vs message passing, polling vs interrupts vs DMA, and buffering, caching and spooling.
