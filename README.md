# Core CS Notes

Five handbooks on the core computer-science subjects, written for technical interviews and
readable as a website.

| Subject | Parts | Lines | Covers |
| --- | --- | --- | --- |
| **DSA** | 17 | 17,589 | Complexity, arrays, hashing, linked lists, stacks and queues, recursion, sorting, backtracking, trees, heaps, tries, greedy, graphs, dynamic programming |
| **OOP** | 13 | 8,806 | Classes, constructors and copying, encapsulation, inheritance, polymorphism, UML, the modern C++ object model, SOLID, design patterns, low-level design |
| **OS** | 13 | 6,341 | Processes, threads, CPU scheduling, synchronization, deadlocks, memory management, virtual memory, file systems, I/O |
| **DBMS** | 13 | 9,613 | Relational model, ER design, normalization, SQL from joins to window functions, DDL and views, indexing, transactions, recovery, relational algebra, NoSQL and scaling |
| **CN** | 13 | 9,322 | Layering, framing and error control, Ethernet and ARP, IP and subnetting, routing, TCP and UDP, congestion control, DNS, HTTP, TLS, and the end-to-end URL walkthrough |

**69 files, 51,671 lines.** Each subject opens with a roadmap — syllabus, dependency map, priority
tiers, a question map and study schedules — and closes with a consolidation file holding revision
sheets, a confusable-pairs table, rapid-fire questions and worked numericals.

## The one thing that makes these different

**Nothing computable is asserted from memory.** Every numerical, query, trace and measurement was
produced by running code, and the real output is what went into the notes:

- **SQL** — every query executed against SQLite 3.49 and its actual result embedded
- **C++** — every program compiled and run with g++ 12
- **Numericals** — subnetting, CRC, Hamming, sliding windows, congestion windows, candidate keys,
  normal forms, serializability, crash recovery and B+ tree arithmetic, all computed
- **Live network state** — real DNS lookups, TLS handshakes, HTTP responses, routing tables and
  `netstat` output from the machine the notes were written on

The tools that produce those answers were **self-tested against independently known results before
being trusted** — a functional-dependency toolkit checked against twelve textbook answers and then
30,000 random FD sets; a schedule analyser against sixteen hand-worked cases; a crash-recovery
simulator across 40,000 recoveries; subnetting checked against Python's `ipaddress` on 50,000
random address/prefix pairs; Dijkstra cross-checked against distance-vector on 3,000 random graphs;
and a from-scratch CRC-32 checked against `zlib` plus 27,000 injected single-bit Hamming errors.

Where something **could not** be verified, the notes say so and explain why, rather than presenting
a textbook diagram as an observation. Several sections exist because running the code contradicted
what was about to be written down.

## Reading them

The handbooks are plain Markdown in `DSA Notes/`, `OOP Notes/`, `OS Notes/`, `DBMS Notes/` and
`CN Notes/` — readable directly on GitHub, in any editor, or as a website:

    cd study-guide
    npm install
    npm run study      # build and serve at http://localhost:3000

`study-guide/` is a Next.js + Fumadocs site that renders the notes with a per-subject sidebar and
full-text search. It only ever **reads** the Markdown; the notes stay the single source of truth.
See [`study-guide/README.md`](study-guide/README.md) for the details, including deployment.

## Layout

    DSA Notes/ OOP Notes/ OS Notes/ DBMS Notes/ CN Notes/   the handbooks
    *-Notes-Plan.md                                         the plan each was written against
    study-guide/                                            the site that renders them
