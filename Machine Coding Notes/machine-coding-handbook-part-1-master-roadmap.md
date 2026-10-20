# Machine Coding Practice — Part 1: Master Roadmap

**An eleven-part companion for turning requirements into working, tested C++17 programs. Authoring status: complete.**

## 1. What this track adds

Machine coding asks you to deliver a working model of a small system: clarify its behavior, choose state and APIs, implement the core path, test failures, and explain extensions. Low-level design helps with responsibilities and relationships; machine coding adds the obligation to make those choices executable within a time budget.

The existing OOP track already implements parking lots, LRU, Splitwise, snake and ladders, elevators and BookMyShow. This companion adds eight different exercises with state-history tests and exact runnable transcripts. Read the old [LLD method](/docs/oop/lld-method-parking-lru-splitwise) first if you need practice identifying responsibilities.

These are curated practice problems, not a measured ranking of the most frequent company questions. As one employer example, [Atlassian's engineering interview guide](https://www.atlassian.com/company/careers/resources/interviewing/engineering) includes code design alongside data structures and discusses reasoning about trade-offs. Interview formats and permitted languages vary; the exercises and timings here are editorial practice choices.

## 2. Complete syllabus

| Part | Module | Main skill | Read |
| --- | --- | --- | --- |
| 1 | Roadmap | Choose a study route and understand evidence | This page |
| 2 | M0 | Scope, contracts, invariants, harness and verification | [Solving Method and Test Harness](/docs/machine-coding/solving-method-and-test-harness) |
| 3 | M1 | Nested state restoration | [Transactional Key-Value Store](/docs/machine-coding/transactional-key-value-store) |
| 4 | M2 | Exact time boundaries and quota policy | [Sliding Window Rate Limiter](/docs/machine-coding/sliding-window-rate-limiter) |
| 5 | M3 | Callback mutation, ownership and failures | [Event Bus and Callback Lifecycle](/docs/machine-coding/event-bus-and-callback-lifecycle) |
| 6 | M4 | Ordering, cancellation and task outcomes | [Virtual Time Task Scheduler](/docs/machine-coding/virtual-time-task-scheduler) |
| 7 | M5 | Money, inventory and a commit boundary | [Vending Machine and Exact Change](/docs/machine-coding/vending-machine-and-exact-change) |
| 8 | M6 | Intervals, allocation and failure-safe replacement | [Meeting Room Booking](/docs/machine-coding/meeting-room-booking) |
| 9 | M7 | Derived index maintenance and query semantics | [In-Memory Document Search](/docs/machine-coding/in-memory-document-search) |
| 10 | M8 | Stable cohorts and versioned configuration | [Feature Flag Evaluator](/docs/machine-coding/feature-flag-evaluator) |
| 11 | Revision | Thirty oral checks, comparisons and two timed mocks | [Consolidation and Mocks](/docs/machine-coding/consolidation-and-mocks) |

Every worked exercise contains a concrete prompt, agreed API, invariants, exact compiled class listing, four verified traces, complexity, architecture follow-ups, eight answered interview questions and four practice tasks. Across M1–M8: **eight implementations, 32 traces, 64 interview Q&As and 32 practice tasks**.

## 3. Prerequisites and study order

Know C++ classes, references, value versus reference capture, optional, maps, vectors, deques and heap ordering. Review [constructors and copying](/docs/oop/constructors-destructors-copying), [the modern C++ object model](/docs/oop/modern-cpp-object-model) and [complexity](/docs/dsa/complexity) when needed. Each class deliberately favors a small concrete model over a large inheritance hierarchy.

For a first pass, follow the syllabus in order. KV and the limiter make validation and state boundaries visible. The bus introduces user-supplied code; the scheduler adds time ordering. Vending and booking emphasize failure-safe updates. Search maintains derived state, and flags combine deterministic evaluation with versioning.

For limited time, prioritize M0, M1, M2 and M6, then attempt Mock A. For callback/backend roles, add M3 and M4. For product-facing state and retrieval systems, add M5, M7 and M8. These priorities are study guidance, not employer frequency claims.

## 4. A repeatable practice session

Read only the prompt and contract first. Explain the state and invariants aloud. Write a small happy path, then the most dangerous failure path. Compile before adding optional features. Run a trace, inspect the state and compare with the expected response. Finally explain one architecture extension while naming what the local model cannot guarantee.

Rebuild from a blank file on a later day. Reading an answer is not the same as producing it under time pressure. Leave the learner tasks unchecked until you actually implement or explain them yourself.

## 5. Runnable evidence

From the repository root:

```powershell
python examples/machine-coding/verify.py
python examples/machine-coding/verify.py --trace T01
```

The recorded authoring run used g++ 12.2.0, C++17, Python 3.13.15 and warnings treated as errors. **57 verification groups passed**, covering **5,900 command responses**, **14 direct API assertions** and all 32 worked traces. Full details and source hashes are in `examples/machine-coding/verification-results.json`; exact recorded outputs are in `observations.json`.

Reference models use complete accepted logs, sorted pending jobs, discrete occupied slots, full document scans and exhaustive bounded-change enumeration where applicable. Tests are deterministic and finite. They do not prove every possible history or concurrency interleaving.

The programs are single-threaded and in memory. No database server, message broker, hardware dispenser, remote configuration service or distributed worker runs here. No performance benchmark, sanitizer run or allocation-failure injection is claimed. Architecture extensions are explained, not represented as completed infrastructure.

## 6. Completion checklist

- [ ] Explain the contract of each of the eight exercises without reading its implementation.
- [ ] Reimplement at least one stateful exercise from a blank file and run its traces.
- [ ] Explain one rejected-operation invariant for each exercise.
- [ ] Attempt both sixty-minute mocks and record your own score using the rubric.
- [ ] Describe one concurrency/persistence extension and the additional mechanism it would require.

Start with [Solving Method and Test Harness](/docs/machine-coding/solving-method-and-test-harness).
