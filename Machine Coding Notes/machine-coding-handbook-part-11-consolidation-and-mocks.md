# Machine Coding Practice — Part 11: Consolidation and Mocks

**Revision: explain the invariant, implement the transition and test the failure.**

## 1. Eight models in one view

| Exercise | Authoritative state | Dangerous transition | First regression test |
| --- | --- | --- | --- |
| KV | Current map and snapshot stack | Inner commit inside an outer transaction | Outer rollback restores pre-outer data |
| Limiter | Per-key accepted timestamps | Expiration at the open left boundary | A timestamp at now-window expires |
| Event bus | Active subscriptions and owned dispatch snapshot | Unsubscribe during callback execution | Removed handler still runs in current snapshot |
| Scheduler | Status map and ordered queued entries | Cancelled task still in heap | Tombstone never executes |
| Vending | Stock, machine cash and customer escrow | Sale cannot make exact change | All session and machine state survives rejection |
| Booking | Booking IDs and assigned intervals | No room for replacement | Failed move preserves the old booking |
| Search | Document frequencies and derived postings | Replacing an old document | Old terms stop matching |
| Flags | Versioned tenant/flag configuration | Same-version conflicting update | Conflict preserves the last valid policy |

## 2. Ten confusable pairs

| Pair | Distinction to explain |
| --- | --- |
| Invariant / precondition | Valid stored state versus permission to perform one operation |
| Commit / durability | Closing a local transaction boundary versus surviving a crash |
| Quota denial / invalid call | Valid policy result versus rejected contract input |
| Snapshot unsubscribe / immediate cancellation | Future dispatch membership versus stopping an already chosen recipient |
| Scheduled / executed | Eligibility and ordering versus an actual side effect |
| Cancelled entry / removed heap node | Authoritative tombstone versus physical queue deletion |
| Escrow / machine cash | Current customer's refundable money versus machine-owned funds |
| Failure-safe move / delete then create | Preserving a valid old state versus needing compensation after deletion |
| Boolean matching / ranking | Which documents qualify versus how qualified documents are ordered |
| Rollout / authorization | Product cohort selection versus permission to access a resource |

## 3. Thirty answered oral checks

### O01. What do you clarify before choosing classes?

Inputs, visible behavior, IDs, duplicates, time/money units, failure semantics, scale and excluded infrastructure. A class model follows those choices rather than replacing them.

### O02. What is the minimum useful executable slice?

One complete command path that parses input, calls the model and reports a result, plus one test that can reject a plausible bug. Compile that before expanding the surface.

### O03. Why separate the adapter from the model?

The CLI owns text parsing and JSON responses. The model owns domain rules, making it reusable from tests or a later HTTP adapter without teaching business logic about CLI tokens.

### O04. Why not start with many interfaces?

Interfaces help at real substitution boundaries. Speculative layers can consume coding time and hide the invariant. Start with concrete types and extract an interface when the use case justifies one.

### O05. What makes a failed-operation test meaningful?

It checks both the rejection and retained state, followed by another valid operation. An error message alone cannot detect partial mutation.

### O06. What does the snapshot stack remember?

Each frame remembers the current map at that BEGIN. Closing a child affects only its frame; the parent still refers to its original entry state.

### O07. Why is a snapshot COMMIT not constant work overall?

Removing a frame destroys an owned map. The logical pop is simple, but reclaiming all of its entries costs time proportional to its size.

### O08. What is the limiter's exact window?

(now-window, now]. Requests on the left boundary expire, requests at now count, and duplicate timestamps can represent distinct accepted requests.

### O09. What is amortized deque cleanup?

One call may remove many old timestamps, but each accepted timestamp is appended once and removed at most once. Key-map lookup and string costs remain separate.

### O10. What happens to inactive limiter keys?

Their history and key entry remain until revisited, and entries are never evicted. The implementation is bounded per key but not by total distinct keys.

### O11. What does an event snapshot own?

Copies of the callable wrappers and their value-captured state. A captured reference or raw pointer still requires its target to outlive callback use.

### O12. Does callback error isolation undo its side effects?

No. It catches the failure and continues delivery. Effects before the throw remain; transactional delivery would need a much stronger domain protocol.

### O13. Why use a scope guard for dispatch?

The destructor restores the flag on normal or exceptional exit. Manual reset statements can be skipped by an exception or an added return path.

### O14. What is the scheduler's comparison tuple?

Due time ascending, priority descending, insertion sequence ascending. The comparator implements that precedence and the trace tests both direction and stability.

### O15. Why reserve task IDs permanently?

The heap may still contain obsolete entries. Reusing an ID without a generation token risks interpreting an old entry as the new task.

### O16. What if a scheduler callback calls schedule again?

The running guard rejects scheduler mutation. An uncaught rejection makes that callback's task fail; later due tasks continue. This is an explicit teaching contract.

### O17. Does the scheduler guarantee external exactly-once work?

No. It prevents rerunning a terminal task in one live object. Crash/retry behavior and external side-effect deduplication are not implemented.

### O18. What preserves money during a rejected vend?

The machine computes change using a candidate pool before updating stock or owned cash. If no subset exists, customer escrow stays intact for cancellation or another attempt.

### O19. Why can bounded change need DP?

Greedy largest-first can choose a coin that blocks a feasible combination of smaller coins, especially when denominations and available counts are arbitrary.

### O20. Why iterate amount downward for each physical coin?

It prevents a newly reached amount from reusing that same coin again during its own pass. Upward iteration would implement an unbounded-reuse behavior.

### O21. What is the interval-overlap predicate?

start1 < end2 and start2 < end1 for valid half-open intervals. It accepts adjacency and rejects every positive-length intersection.

### O22. What is the move commit point?

After a valid replacement room is found. The old booking remains until then, and self-occupancy is excluded from candidate checks.

### O23. Is best fit globally optimal?

No. It is a deterministic local allocation policy. Future requests, fairness and revenue may justify a different objective; there is no future-workload optimization proof here.

### O24. Why does search need a reverse document view?

It identifies a document's old terms for deletion or replacement, avoiding stale postings without scanning the entire vocabulary.

### O25. How are repeated query terms handled?

They are deduplicated. Eligibility uses the distinct set and score sums each matching term's document frequency once.

### O26. What is missing from the search score?

Length normalization, collection frequency, phrase positions and a relevance evaluation. Raw frequency is an explicit small-model contract, not an asserted production ranking quality.

### O27. Why specify hash encoding and width?

Stable cohorts across runs or languages require identical bytes and arithmetic. Unspecified text boundaries or implementation-dependent hashing can move users unexpectedly.

### O28. Why does a larger rollout retain an enabled user?

With unchanged hashing inputs the user's bucket stays fixed. Raising only the comparison threshold cannot exclude a bucket already below the old threshold.

### O29. Why is a duplicate config not always an error?

The same authoritative version and value is a harmless retry. A different value under the same version is a conflict and must not silently win by arrival order.

### O30. What does the verification evidence actually establish?

The specified builds, fixed cases, finite reference histories and website checks passed on the recorded environment. It does not establish production performance, crash recovery, arbitrary allocation-failure safety or concurrent correctness.

## 4. Mock A — transactional state and exact time, 60 minutes

**Prompt:** Implement a nested transactional KV store from a blank file. Support SET, GET, ERASE, BEGIN, COMMIT and ROLLBACK. Reserve the final ten minutes to specify and test an accepted-only per-key sliding limiter, using pseudocode if the KV implementation needs the remaining coding time.

**Clarification targets:** Missing versus empty value, inner commit behavior, absent transaction errors, serial-session scope, limiter endpoints and time source. Ask these before seeing the answer chapters. Use the M0 time budget as guidance; the duration is an editorial practice choice.

**Acceptance tests:** Inner COMMIT followed by outer ROLLBACK restores the original value. A deleted key returns after rollback. COMMIT without BEGIN preserves state. An empty value remains distinct from missing. For the limiter, use L=2/W=10 at times 0, 9, 9 and 10 and explain admission at the boundary.

**Expected design:** Current map plus snapshot stack is an acceptable first implementation. Explain its copy/destruction costs. The limiter owns accepted timestamp histories and prunes <=now-window. Claim only serial, in-memory semantics. A correct simple model scores better than an incomplete optimized log.

**Follow-up:** Replace snapshots with an undo log on paper. Explain parent/child merge when both change the same key. Then explain why assigning a separate session ID is necessary before discussing multi-client isolation.

## 5. Mock B — booking updates and derived search, 60 minutes

**Prompt:** Implement BOOK, MOVE, CANCEL and STATE for the supplied A/B/C rooms. Reserve the final ten minutes to design a mutable document index supporting PUT, ERASE and AND search, with particular attention to replacement.

**Clarification targets:** Half-open intervals, capacity, tie break, duplicate booking IDs, move failure, tokenization, repeated query words and stale postings. The final search design can be pseudocode if needed; record what was implemented separately from what was explained.

**Acceptance tests:** Adjacent meetings share A. Two overlapping four-person meetings take B and C. A third fails. A failed move retains its original record. Moving within one's old interval ignores self. In the search design, replacing old with new must make old stop matching; AND with a missing term must return empty.

**Expected design:** Candidate-room selection precedes replacement. Availability checks ignore only the moved booking. Search keeps a per-document term view and inverted postings, with one analyzer shared between writes and queries. Explain why concurrent database writers need shared enforcement beyond a local availability check.

**Follow-up:** Add idempotent booking request identity and document versions on paper. State how identical retries differ from conflicting payloads and how stale updates could otherwise revive deleted content.

## 6. Scoring rubric for either mock

| Dimension | Points | Evidence |
| --- | --- | --- |
| Requirements | 0–4 | Clear endpoints, IDs, duplicates and scope |
| Model and invariants | 0–4 | State ownership and failure-safe transition |
| Executable core | 0–6 | Compiles and satisfies the primary API |
| Verification | 0–4 | Happy path, boundary, rejected-state and history tests |
| Explanation | 0–2 | Accurate complexity and one scoped extension |

Maximum 20. Do not give full core credit to code that loses a valid booking on failed MOVE or makes an outer rollback unable to undo a child commit. Record a score only after attempting the mock. These are study rubrics, not hiring thresholds or claims about a company's scoring.

## 7. Learner record

- [ ] Mock A attempted from a blank file; date, score and failures recorded separately.
- [ ] Mock B attempted from a blank file; date, score and failures recorded separately.
- [ ] One failed test corrected with a short explanation of the violated invariant.
- [ ] One unimplemented architecture extension described without overstating local guarantees.

Return to [Master Roadmap](/docs/machine-coding).
