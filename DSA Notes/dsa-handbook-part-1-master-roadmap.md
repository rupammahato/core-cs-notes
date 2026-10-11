# DSA Placement Handbook (C++) — Part 1: Master Roadmap

*Your personal roadmap, dependency map, priority ranking, and pattern index. Later parts fill in each module using the note format you specified.*

---

## 0. How this handbook is built

This is Part 1 of a multi-part handbook. It contains no teaching, only structure: what to learn, in what order, why that order, how long each piece takes, and how the problem-solving patterns map onto the syllabus.

When you say **"Start Phase 0"**, I teach that module in full using your 11-section note format (what it is, why, core idea, when to use, recognition signals, C++ template, example, complexity, must-remember, common mistakes, practice problems). One module per request. The modules stack into the final handbook.

The final cheat sheets (roadmap, complexity, STL, patterns, algorithms, templates, mistakes, DP, graphs, checklist) come at the end, after the modules exist to summarise.

---

## 1. What I changed from your outline, and why

Your phase list is solid. Four changes make the dependencies cleaner:

**Hashing moves up, from Phase 7 to right after Arrays & Strings.** Roughly half of all "optimal" array and string solutions are a brute force plus a hash map. Teaching arrays first and hashing five phases later means you learn array problems twice: once the slow way, once again after you meet `unordered_map`. Prefix-sum-plus-hashmap (subarray sum equals K) is an array pattern that literally cannot be taught without hashing.

**Recursion fundamentals split off from backtracking and move before sorting.** Merge sort and quick sort are recursion problems wearing a sorting costume. You cannot understand why merge sort is O(n log n) without being able to read a recurrence. So: recursion anatomy, call stack, recursion tree, and recurrence complexity go before Searching & Sorting. Backtracking (subsets, N-Queens, Sudoku) stays where you put it, after stacks, because it is a much harder skill and benefits from more maturity.

**Bit manipulation becomes a parallel side-module instead of Phase 14.** It is small, self-contained, depends on nothing, and is needed earlier than Phase 14 (subset generation via bitmask shows up in backtracking). Do it as a two-evening filler any time after complexity analysis.

**Trie moves after Trees, not after DP.** A trie is a tree with 26 children. Learning it right after tree traversal is a 3-hour job; learning it cold is a 6-hour job.

Everything else keeps your ordering, which already respects the real dependencies.

---

## 2. The master syllabus

17 modules. "Hours" assumes rebuilding from a half-forgotten base, including problem solving. "Problems" is the target count for that module: small, deliberately chosen, each teaching something different.

| # | Module | Your phase | Hours | Problems | Tier |
|---|--------|-----------|-------|----------|------|
| 0 | C++ essentials + STL for DSA | 0 | 8–10 | 0 (drills) | 1 |
| 1 | Complexity analysis | 1 | 3–4 | 0 (drills) | 1 |
| 2 | Arrays & Strings | 2 | 20–25 | 28 | 1 |
| 3 | Hashing | 7 | 6–8 | 10 | 1 |
| 4 | Recursion fundamentals | 6a | 6–8 | 8 | 1 |
| 5 | Searching & Sorting | 3 | 12–15 | 16 | 1 |
| 6 | Linked Lists | 4 | 8–10 | 12 | 1 |
| 7 | Stacks & Queues (incl. monotonic) | 5 | 10–12 | 14 | 1 |
| 8 | Backtracking | 6b | 10–12 | 12 | 2 |
| 9 | Trees & BST | 8 | 18–22 | 24 | 1 |
| 10 | Heaps & Priority Queue | 9 | 8–10 | 10 | 1 |
| 11 | Greedy & Intervals | 10 | 8–10 | 12 | 2 |
| 12 | Graphs | 11 | 22–28 | 24 | 1 |
| 13 | Dynamic Programming | 12 | 30–35 | 30 | 1 |
| S | Bit manipulation (side module) | 14 | 4–5 | 8 | 2 |
| 14 | Trie | 13 | 5–6 | 6 | 3 |
| 15 | Advanced & optional | 15 | 10–15 | 8 | 3/4 |

**Core total (modules 0–13 + side): roughly 150–180 hours, about 185 problems.**
With modules 14–15: roughly 170–200 hours.

At 3 hours a day that is about 8 weeks of focused work. At 2 hours a day alongside other placement prep, about 12 weeks. Neither number includes revision passes, which add 25–30% on top.

---

## 3. Dependency map

Arrows mean "you will be confused without this first." Modules on the same row can be done in either order.

```
                        [0] C++ & STL
                              |
                        [1] Complexity
                              |
              +---------------+---------------+
              |                               |
      [2] Arrays & Strings              [S] Bit manipulation
              |                          (parallel, anytime)
        [3] Hashing
              |
      [4] Recursion fundamentals
              |
      +-------+--------+---------------+
      |                |               |
 [5] Search &    [6] Linked      [7] Stack &
     Sort            Lists           Queue
      |                |               |
      |                +-------+-------+
      |                        |
      |                 [8] Backtracking
      |                        |
      +---------+--------------+
                |
          [9] Trees & BST
                |
        +-------+--------+--------+
        |                |        |
  [10] Heaps      [14] Trie   [11] Greedy
        |                          |
        +-------+------------------+
                |
          [12] Graphs
                |
        [13] Dynamic Programming
                |
        [15] Advanced topics
```

### The dependencies that actually bite

| To learn | You genuinely need | Why |
|---|---|---|
| Sliding window | Two pointers | Window is a constrained two-pointer walk |
| Subarray sum = K | Prefix sum + hashing | The map stores prefix frequencies |
| Merge / quick sort | Recursion + recurrences | Complexity is unreadable otherwise |
| Binary search on answer | Plain binary search + monotonic predicates | You search a value range, not an array |
| Trees | Recursion | Every tree solution is a recursive contract |
| Backtracking | Recursion + subsets | Backtracking is recursion that undoes |
| Heaps | Trees (array-embedded) | Heapify is a tree operation on a vector |
| Dijkstra | BFS + priority queue | It is BFS with a heap instead of a queue |
| Kruskal | Sorting + DSU | Sort edges, then union |
| Topological sort | BFS/DFS + in-degree | Kahn is BFS with a counter |
| DP | Recursion + memoisation | Tabulation is a recursion you unrolled |
| Trie | Trees + hashing intuition | A node is a 26-way branch |
| Bitmask DP | Bit manipulation + DP | State is a subset encoded as an integer |

---

## 4. Placement priority tiers

### Tier 1 — must master (non-negotiable)

| Topic | Why |
|---|---|
| Arrays & Strings | The single largest source of interview questions and the base for two pointers, sliding window, prefix sums |
| Hashing | Turns most O(n²) brute forces into O(n); appears inside problems from every other topic |
| Complexity analysis | Interviewers ask for complexity on every problem; getting it wrong invalidates a correct solution |
| Binary search (incl. on answer) | High frequency, and "binary search on answer" is the most common medium-level trick candidates miss |
| Sorting (concepts + `std::sort`) | Prerequisite for greedy, intervals, two pointers on unsorted input |
| Recursion | Load-bearing for trees, backtracking, DP, divide and conquer |
| Linked Lists | Classic OA and interview filler; tests pointer discipline and edge cases |
| Stacks & monotonic stack | Next greater element, histogram, expression evaluation |
| Trees & BST | Combines recursion, traversal, structural reasoning; extremely common in interviews |
| Heaps / Top-K | The "k-th something" and "merge k sorted" family |
| Graphs: BFS, DFS, topological sort, DSU | Grid problems, dependency problems, connectivity |
| DP: 1D, knapsack, grid, LCS/edit distance | The topic that separates offers; heavily weighted at product companies |

### Tier 2 — high priority

| Topic | Why |
|---|---|
| Backtracking | Subsets, permutations, combination sum are standard; N-Queens/Sudoku appear less often but test recursion depth |
| Greedy & intervals | Merge intervals, meeting rooms, activity selection recur constantly; also teaches when greedy fails |
| Dijkstra | Common enough in weighted-graph rounds at product companies |
| Bit manipulation | Small time cost, appears in XOR tricks, subset generation, and quick OA questions |
| Sliding window (advanced variants) | Longest substring variants show up in nearly every string-heavy round |
| Deque / monotonic queue | Sliding window maximum is a standard medium |

### Tier 3 — good to know

| Topic | Why |
|---|---|
| Trie | Appears in autocomplete/word-search questions and XOR-max problems; cheap to learn once trees are done |
| Bellman-Ford, Floyd-Warshall | Occasionally asked conceptually; rarely coded in interviews |
| Prim / Kruskal (MST) | Asked at some product companies; DSU is the more valuable half |
| Morris traversal | One-off O(1)-space trick; good as a "do you know more" answer |
| Counting/radix sort | Concept questions about non-comparison sorting |
| Bitmask DP | Shows up in harder OAs and TSP-flavoured questions |

### Tier 4 — advanced, mostly competitive programming

| Topic | Why |
|---|---|
| Segment tree, Fenwick tree (BIT) | Range-query heavy; rarely in placement interviews, standard in CP |
| Sparse table | Range minimum queries; CP |
| KMP, Z algorithm, Rabin-Karp, rolling hash | Pattern matching; occasionally asked at strong product companies, common in CP |
| Bridges, articulation points, SCC (Tarjan/Kosaraju) | Rare in placements, standard in CP |
| Network flow, heavy-light decomposition, computational geometry | Skip for placements unless you are targeting ICPC/Codeforces |

**If you have under a month, skip all of Tier 4 and most of Tier 3.** Do Tier 1 thoroughly and Tier 2 partially. A candidate with airtight Tier 1 beats one with patchy Tier 1 plus a segment tree.

---

## 5. Interview orientation (what the research says)

Frequency rankings from multiple 2026 interview-prep sources converge on roughly the same ordering: arrays and strings first, then hash maps and sets, linked lists, binary search, trees, heaps, then graphs, DP, greedy, and backtracking, with tries, advanced graph algorithms, and segment trees clustered at the bottom as competitive-programming or specialist territory ([Thita.ai, Feb 2026](https://thita.ai/blog/dsa/most-important-dsa-topics-for-coding-interviews-ranked-by-frequency)). That matches the tier ranking above.

Two structural points about Indian placement season worth planning around:

**OA/coding rounds and interviews test differently.** Coding rounds have converged on a short auto-graded format, commonly 1–3 problems in 60–90 minutes at service companies and 2–3 medium-to-hard problems in 45–90 minutes at product companies, with arrays, strings, trees, and DP forming the shared core across both tiers ([PapersAdda, Sep 2026](https://papersadda.com/article/must-do-coding-questions-placements-2026/)). Interviews add the parts an auto-grader cannot check: stating the brute force first, naming the bottleneck, justifying the optimisation, and giving complexity out loud.

**Service companies filter on aptitude before they ever see your code.** TCS, Infosys, Wipro and Cognizant eliminate a large majority of candidates at the aptitude round ([TaskVeda, 2026](https://www.taskveda.in/blog/how-to-prepare-for-placements.html)). If service companies are in your target set, DSA depth past Tier 1 has lower marginal value than aptitude practice. Product companies invert this: coding-first selection, with algorithmic depth tested from the first technical round ([FacePrep, May 2026](https://faceprep.in/article/differences-between-product-based-companies-and-service-based-companies/)).

Practical read: **Tier 1 plus Tier 2 covers both tracks.** Push into Tier 3/4 only if you are specifically targeting strong product companies and already have Tier 1 solid under timed conditions. I will not predict specific company questions; frequency data from prep sites is self-reported and noisy, and pattern coverage generalises better than question lists.

---

## 6. Pattern roadmap

The patterns, in the order the syllabus unlocks them. Full recognition-signal treatment comes with each module; this is the index so you know what is coming and when.

| # | Pattern | Unlocked in | One-line recognition trigger | Typical complexity |
|---|---|---|---|---|
| 1 | Frequency counting | 2 / 3 | "how many times", anagram, duplicates | O(n) |
| 2 | Two pointers | 2 | Sorted array, pair/triplet sum, in-place partition | O(n) |
| 3 | Sliding window | 2 | "longest/shortest subarray or substring such that..." | O(n) |
| 4 | Prefix sum | 2 | Repeated range sums, "subarray sum equals K" | O(n) build, O(1) query |
| 5 | Difference array | 2 | Many range updates, one final read | O(n + q) |
| 6 | Hashmap lookup | 3 | "has this been seen", complement search | O(n) |
| 7 | Prefix sum + hashmap | 3 | Count subarrays with a given sum/property | O(n) |
| 8 | Divide and conquer | 4 / 5 | Split, solve halves, merge | O(n log n) usually |
| 9 | Binary search | 5 | Sorted input, or a monotonic predicate | O(log n) |
| 10 | Binary search on answer | 5 | "minimum X such that feasible", `can(x)` is monotonic | O(n log(range)) |
| 11 | Sort + scan | 5 / 11 | Order unlocks a linear pass | O(n log n) |
| 12 | Fast/slow pointers | 6 | Cycle, middle node, n-th from end | O(n), O(1) space |
| 13 | In-place list reversal | 6 | Reverse whole list or a sublist/group | O(n), O(1) space |
| 14 | Monotonic stack | 7 | Next/previous greater or smaller, histogram | O(n) |
| 15 | Monotonic queue (deque) | 7 | Max/min of every sliding window | O(n) |
| 16 | Backtracking | 8 | Enumerate all subsets/permutations/valid boards | Exponential, prune hard |
| 17 | Tree DFS (recursive contract) | 9 | Answer at a node = combine(left, right) | O(n) |
| 18 | Tree BFS (level order) | 9 | Level-by-level, views, shortest depth | O(n) |
| 19 | Heap / Top-K | 10 | "k-th largest", "top k", "merge k sorted", streaming median | O(n log k) |
| 20 | Merge intervals | 11 | Overlapping ranges, meeting rooms, platforms | O(n log n) |
| 21 | Greedy exchange argument | 11 | Local choice provably safe (sort by end time, ratio) | O(n log n) |
| 22 | Graph BFS | 12 | Shortest path in unweighted graph, grid, multi-source | O(V + E) |
| 23 | Graph DFS | 12 | Connectivity, components, cycle detection, islands | O(V + E) |
| 24 | Topological sort | 12 | Dependencies, prerequisites, ordering in a DAG | O(V + E) |
| 25 | Union-Find (DSU) | 12 | Dynamic connectivity, merging groups, Kruskal | near O(1) amortised |
| 26 | Dijkstra | 12 | Weighted shortest path, non-negative weights | O(E log V) |
| 27 | DP on sequences (1D) | 13 | Choice at each index, "max/min/count ways" | O(n) |
| 28 | DP knapsack family | 13 | Pick or skip under a capacity/target budget | O(n × target) |
| 29 | DP on two strings | 13 | LCS, edit distance, alignment | O(n × m) |
| 30 | DP on grids | 13 | Paths in a matrix with constraints | O(n × m) |
| 31 | Interval DP | 13 | Split a range at every point, combine | O(n³) |
| 32 | Bitmask DP | S + 13 | n ≤ 20, state is "which subset is used" | O(2ⁿ × n) |
| 33 | XOR tricks | S | Pairs cancel, unique element, missing number | O(n) |
| 34 | Trie / prefix tree | 14 | Shared prefixes, autocomplete, max-XOR pair | O(length) per op |

The goal for the whole handbook: given an unfamiliar problem, you should reach a shortlist of 2–3 of these within 60 seconds, from the shape of the constraints and the wording.

---

## 7. Schedules

All four assume you have aptitude, core CS, projects, and HR prep competing for time. Hours shown are DSA only.

### 2 weeks (emergency triage, ~4 h/day, ~55 h)

Accept that you will not cover graphs or DP properly. Optimise for not failing the OA.

| Days | Focus |
|---|---|
| 1 | Module 0 (STL only, skip C++ basics) + Module 1 |
| 2–4 | Module 2: two pointers, sliding window, prefix sum, Kadane |
| 5 | Module 3: hashing |
| 6–7 | Module 5: binary search + binary search on answer, `sort` with comparators |
| 8 | Module 6: linked lists, fast/slow |
| 9 | Module 7: stack, monotonic stack |
| 10–11 | Module 9: tree traversals, height, diameter, LCA, level order |
| 12 | Module 12: BFS/DFS on grids only (islands, rotten oranges, flood fill) |
| 13 | Module 13: DP essentials only (climbing stairs, house robber, 0/1 knapsack, coin change, LCS) |
| 14 | Timed mock: 3 problems in 90 minutes, then review mistakes |

Skip: backtracking, heaps, greedy proofs, Dijkstra, MST, trie, everything Tier 3/4.

### 1 month (~3 h/day, ~85 h)

| Week | Modules |
|---|---|
| 1 | 0, 1, 2 (full), start 3 |
| 2 | 3, 4, 5, 6 |
| 3 | 7, 9, 10, plus side module S |
| 4 | 12 (BFS/DFS/topo/DSU), 13 (1D + knapsack + LCS + grid), two timed mocks |

Skip or skim: 8 (backtracking, do subsets and permutations only), 11 (do merge intervals only), 14, 15.

### 2 months (~2.5 h/day, ~140 h) — recommended default

| Week | Modules |
|---|---|
| 1 | 0, 1 |
| 2 | 2 (arrays) |
| 3 | 2 (strings), 3 |
| 4 | 4, 5 |
| 5 | 6, 7 |
| 6 | 8, S, 9 (start) |
| 7 | 9 (finish), 10, 11 |
| 8 | 12 |
| 9 | 13 (this week overruns; 2 months is really 9 weeks) |
| — | Revision passes 3 and 4 folded into weeks 8–9 |

Covers all of Tier 1 and Tier 2, plus trie if time allows.

### 3 months (~2 h/day, ~170 h) — comfortable

Same order as the 2-month plan, stretched, with these additions:
- Week-end review sessions: re-solve two old problems from memory, no notes.
- Weeks 10–11: Tier 3 topics (trie, Bellman-Ford, Floyd-Warshall, MST, Morris), plus one CP-flavoured topic if you want it (KMP or Fenwick tree).
- Week 12: revision only. Notes, templates, mistake log, patterns. No new topics. Three full timed mocks.

### Revision passes (applies to every schedule)

| Pass | What you do | When |
|---|---|---|
| 1 | Understand the concept, write the template once by hand | During the module |
| 2 | Solve the module's problem set | During the module |
| 3 | Pattern recognition drill: read 20 problem statements, name the pattern in 60 seconds each, do not solve | End of each phase group |
| 4 | Timed solving: 2–3 problems in 90 minutes, mixed topics, no hints | Weekly from week 4 |
| 5 | Notes, templates, mistake log, cheat sheets only | Final 7–10 days |

Pass 3 is the one most people skip and the one that produces the "I recognised it immediately" effect in interviews.

---

## 8. Rules I will follow in every module

So you know what to expect and can push back if a module drifts:

1. Intuition before code. Why the algorithm works, not just the steps.
2. C++ only, modern but plain. No template metaprogramming, no clever one-liners.
3. Every template short enough to write from memory under pressure.
4. Complexity stated for everything, time and space.
5. Recognition signals given as concrete phrases you will see in problem statements.
6. Confusable pairs get a comparison table (`map` vs `unordered_map`, recursion vs backtracking, BFS vs DFS, subarray vs subsequence, Dijkstra vs Bellman-Ford).
7. "Must remember" lists only non-obvious facts. No textbook filler.
8. "Common mistakes" means bugs that fail submissions, not style advice.
9. Problem sets stay small. 3–7 per topic, each teaching something different, layered Concept → Pattern → Interview → Advanced.
10. Advanced and optional content marked clearly so you can skip it without guilt.

---

## 9. Progress checklist

Tick as you finish each module. A module is "done" when you can write its templates from memory and explain the core idea without notes.

```
[ ] 0   C++ essentials + STL
[ ] 1   Complexity analysis
[ ] 2   Arrays & Strings
[ ] 3   Hashing
[ ] 4   Recursion fundamentals
[ ] S   Bit manipulation
[ ] 5   Searching & Sorting
[ ] 6   Linked Lists
[ ] 7   Stacks & Queues
[ ] 8   Backtracking
[ ] 9   Trees & BST
[ ] 10  Heaps & Priority Queue
[ ] 11  Greedy & Intervals
[ ] 12  Graphs
[ ] 13  Dynamic Programming
[ ] 14  Trie
[ ] 15  Advanced (optional)

Cross-cutting:
[ ] Can state time and space complexity for every template I know
[ ] Can name the pattern for 20/20 unseen problem statements in 60s each
[ ] Completed 5 timed mocks (3 problems / 90 min)
[ ] Mistake log has 30+ entries and I have re-read it twice
```

---

## Next step

Say **"Start Phase 0"** and I will teach C++ essentials and STL for DSA in full detail, using the 11-section note format.

If you would rather reorder something first, or you want to tell me your actual deadline and target companies so I can pick one of the four schedules for you, say that instead.

---

### Sources used for the interview-orientation section

- Thita.ai, *Most Important DSA Topics for Coding Interviews (Ranked by Frequency)*, Feb 2026
- PapersAdda, *Must Do Coding Questions for Placements 2026*, Sep 2026
- TaskVeda, *How to Prepare for Placements (2026)*
- FacePrep, *Product-Based vs Service-Based Companies*, May 2026

Frequency data from prep platforms is self-reported and should be treated as directional, not precise.
