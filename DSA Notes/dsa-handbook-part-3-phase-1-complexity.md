# DSA Placement Handbook (C++) — Part 3
# Phase 1: Complexity Analysis

**Module 1 · 3–4 hours · Tier 1 · Requires: Module 0**

---

## Why this module is short but non-negotiable

Complexity analysis is the smallest module in the roadmap and the one with the highest return per hour. Three reasons:

**Interviewers ask for it on every single problem.** "What's the time complexity?" is the question that follows every solution you write. Getting it wrong turns a correct solution into a shaky one. Interviewers frequently care more about whether you can *reason* about cost than whether you found the optimal answer.

**It tells you the answer before you solve the problem.** Constraints are a hint, not decoration. If `n ≤ 20`, the intended solution is exponential and you should stop looking for a clever polynomial one. If `n ≤ 10⁵`, an O(n²) approach will fail no matter how elegant it is. Section 1.8 turns this into a lookup table. Used properly it cuts your time-to-approach on unseen problems by a large margin.

**It is the vocabulary for everything that follows.** "Why is merge sort O(n log n)" and "why is memoisation faster than plain recursion" are both complexity questions. Without this module those explanations are just claims you memorise.

What this module deliberately skips: formal limit definitions, proofs of the Master Theorem, complexity classes (P, NP), and amortised analysis via the potential method. None of it appears in placement interviews.

---

## 1.1 Time complexity

### 1. What is it?

A description of how the number of operations an algorithm performs grows as the input grows. It is not a measurement in seconds. It is a growth rate.

### 2. Why do we need it?

Because runtime in seconds depends on the machine, the compiler, the load on the judge, and the language. Growth rate does not. An O(n²) algorithm loses to an O(n log n) one at large n on every machine ever built, so growth rate is the only comparison that transfers.

### 3. Core idea

Count the operations as a function of input size `n`, then throw away everything that stops mattering as `n` grows: constant multipliers and lower-order terms.

```
3n² + 500n + 9000   →   O(n²)
```

At `n = 10`, the `9000` dominates completely. At `n = 10⁶`, the `3n²` term is 3 × 10¹² and everything else is noise. Asymptotic analysis is a statement about large `n`, and large `n` is what breaks solutions.

### 4. When should I use it?

Three moments, every problem:

- **Before coding**, to read the constraints and pick a target complexity.
- **After coding**, to verify you hit the target.
- **Out loud in an interview**, unprompted, the moment you finish explaining an approach.

### 5. How to recognise what matters

The dominant term is the one attached to the most deeply nested loop or the widest recursion tree. Find that, and you have the complexity. Everything else is bookkeeping.

### 6. The counting rules

```cpp
// Rule 1: sequential blocks ADD, so take the max
for (int i = 0; i < n; i++) { }        // O(n)
for (int i = 0; i < n * n; i++) { }    // O(n²)
// total: O(n + n²) = O(n²)

// Rule 2: nested loops MULTIPLY
for (int i = 0; i < n; i++)
    for (int j = 0; j < m; j++) { }    // O(n * m)

// Rule 3: an index that doubles or halves gives log n
for (int i = 1; i < n; i *= 2) { }     // O(log n)
while (n > 0) n /= 2;                  // O(log n)

// Rule 4: triangular loops are still quadratic
for (int i = 0; i < n; i++)
    for (int j = i; j < n; j++) { }    // n(n+1)/2 ≈ n²/2 → O(n²)

// Rule 5: a loop that runs a fixed number of times is O(1)
for (int i = 0; i < 26; i++) { }       // O(1), not O(26)
```

**Rule 6, the one people get wrong:**

```cpp
int j = 0;
for (int i = 0; i < n; i++) {
    while (j < n && cond(j)) j++;      // j is NEVER reset
}
```

This looks like O(n²) because of the nesting. It is **O(n)**. `j` only moves forward and can advance at most `n` times across the entire outer loop, so the inner work is `n` total, not `n` per iteration. This is exactly why two pointers, sliding window, and monotonic stacks are linear despite having a loop inside a loop. If you cannot see this, you will misjudge the complexity of half the patterns in Module 2 and Module 7.

The test: **does the inner variable reset each outer iteration?** If yes, multiply. If no, add.

### 7. Example

```cpp
int count = 0;
for (int i = 0; i < n; i++)            // n times
    for (int j = 0; j < n; j++)        // n times each
        if (a[i] + a[j] == target)     // O(1)
            count++;
```

n × n × O(1) = **O(n²)** time, O(1) extra space.

### 8. Complexity of the common shapes

| Complexity | Name | Typical source |
|---|---|---|
| O(1) | Constant | Array index, hash lookup, arithmetic, heap top |
| O(log n) | Logarithmic | Binary search, balanced tree op, heap push/pop |
| O(n) | Linear | Single pass, two pointers, BFS/DFS on a list |
| O(n log n) | Linearithmic | Sorting, heap of n elements, divide and conquer with linear merge |
| O(n²) | Quadratic | Nested loop over all pairs, simple DP over two indices |
| O(n³) | Cubic | Triple loop, Floyd-Warshall, matrix chain multiplication |
| O(2ⁿ) | Exponential | All subsets, naive recursion with two branches |
| O(n!) | Factorial | All permutations, brute-force travelling salesman |

### 9. Must remember

1. **Constants are dropped, but they still exist.** O(n) with a 100× constant loses to O(n log n) at realistic sizes. Asymptotics tell you which wins eventually, not which wins today. Interviewers know this; mentioning it shows depth.
2. **The base of the logarithm is irrelevant.** `log₂n` and `log₁₀n` differ by a constant factor. In DSA, unqualified `log n` means base 2, because we halve things.
3. `log₂(10⁹) ≈ 30`. `log₂(10⁶) ≈ 20`. `log₂(10⁵) ≈ 17`. Memorise these three; they let you estimate in your head.
4. **Define what `n` is before you state a complexity.** For a string, `n` is the length. For a graph it is `V` and `E` separately, and O(V + E) is not O(n). For an `n × m` grid it is O(n·m). Saying "O(n)" for a grid traversal is ambiguous and interviewers notice.
5. A loop bounded by a constant (26 letters, 32 bits, 10 digits) contributes O(1), not O(26). But if the alphabet size appears in the constraints, keep it symbolic: O(n·k).
6. Number of subarrays of an array of size n is `n(n+1)/2 = O(n²)`. Number of subsequences is `2ⁿ`. Number of permutations is `n!`. Knowing these tells you the cost of "try everything" instantly.

### 10. Common mistakes

- Multiplying nested loops when the inner index never resets (Rule 6). Calling sliding window O(n²).
- Forgetting that an STL call inside a loop carries its own cost. `for (int i = 0; i < n; i++) mp[i]++;` with a `map` is O(n log n), not O(n).
- Calling `sort` inside a loop and reporting O(n log n) for the whole thing. It is O(n² log n).
- Reporting the complexity of your intended algorithm rather than the code you actually wrote. Check what you typed.
- Ignoring the cost of `substr`, string concatenation, or copying a vector. These are O(n) operations hiding inside what looks like one statement.

### 11. Practice

Analysis drills, not coding. Answers in Section 1.10.

1. `for (i=0;i<n;i++) for (j=0;j<n;j++) for (k=0;k<n;k++)` → ?
2. `for (i=1;i<=n;i*=2) for (j=0;j<n;j++)` → ?
3. `for (i=0;i<n;i++) { sort(v.begin(), v.end()); }` → ?
4. `for (i=0;i<n;i++) s = s + v[i];` where `s` is a string → ?

---

## 1.2 Big O, Big Theta, Big Omega

### 1. What is it?

Three notations describing three different kinds of bound on a function's growth.

| Notation | Meaning | Plain English |
|---|---|---|
| O(f) | Upper bound | Grows **no faster than** f |
| Ω(f) | Lower bound | Grows **at least as fast as** f |
| Θ(f) | Tight bound | Grows **exactly like** f (both bounds hold) |

### 2. Why do we need it?

Strictly, you need Θ to describe an algorithm precisely. In practice everyone says "O" and means "Θ", and that is accepted everywhere including interviews. The distinction matters for exactly two things: answering a viva question correctly, and describing algorithms whose best and worst cases genuinely differ.

### 3. Core idea

O is a ceiling, Ω is a floor, Θ is both at once.

Because O is only a ceiling, **an O(n) algorithm is also correctly O(n²), O(n³), and O(2ⁿ)**. All of those are true upper bounds. They are just uselessly loose. This is the trick question: "is binary search O(n)?" The technically correct answer is yes, and the useful answer is that it is Θ(log n).

### 4. When should I use which?

Use O in conversation, which is what everyone expects. Use Θ when you want to be precise, or when an interviewer is probing whether you know the difference. Ω comes up almost exclusively in one context: the statement that comparison-based sorting is Ω(n log n), meaning no comparison sort can do better. That is a lower bound on the *problem*, not on any particular algorithm, and it is worth knowing because it explains why counting sort and radix sort are interesting (they are not comparison-based, so the bound does not apply).

### 5. Example

For linear search in an unsorted array of size n:

- Best case: target is at index 0 → Ω(1)
- Worst case: target is absent → O(n)
- There is no single Θ for "linear search" without specifying the case. For the worst case specifically, it is Θ(n).

### 6. Must remember

1. Saying "the worst case is O(n)" and "the worst case is Θ(n)" are both fine. Saying "the algorithm is Θ(n)" without naming a case is sloppy when best and worst differ.
2. O(1) ⊂ O(log n) ⊂ O(n) ⊂ O(n log n) ⊂ O(n²) ⊂ O(2ⁿ) ⊂ O(n!). Every containment is strict.
3. Comparison-based sorting is Ω(n log n). This is the standard follow-up to "can you sort faster than n log n" and the answer is "not by comparing, but yes by counting, if the values are bounded".
4. Nobody in a coding interview will correct you for saying O when you mean Θ. Do not over-engineer your vocabulary mid-explanation.

### 7. Common mistakes

- Believing O means worst case and Ω means best case. They are independent concepts. You can state an upper bound on the best case.
- Answering "no" to "is O(n²) a valid bound for this O(n) algorithm?"

---

## 1.3 Best, average, and worst case

### 1. What is it?

The same algorithm can cost different amounts depending on *which* input of size n you hand it. Best, average, and worst case name the cheapest, typical, and most expensive inputs.

### 2. Why do we need it?

Because the gap is sometimes enormous and sometimes decisive. Quicksort and merge sort are both O(n log n) on average, but quicksort degrades to O(n²) on adversarial input while merge sort never does. That single fact drives real engineering choices.

### 3. The table worth memorising

| Algorithm / structure | Best | Average | Worst |
|---|---|---|---|
| Linear search | O(1) | O(n) | O(n) |
| Binary search | O(1) | O(log n) | O(log n) |
| Bubble / insertion sort | O(n) | O(n²) | O(n²) |
| Selection sort | O(n²) | O(n²) | O(n²) |
| Merge sort | O(n log n) | O(n log n) | O(n log n) |
| Quick sort | O(n log n) | O(n log n) | **O(n²)** |
| Heap sort | O(n log n) | O(n log n) | O(n log n) |
| `std::sort` (introsort) | O(n log n) | O(n log n) | O(n log n) |
| Hash map lookup | O(1) | O(1) | **O(n)** |
| BST (unbalanced) search | O(log n) | O(log n) | **O(n)** |
| Balanced BST (`set`, `map`) | O(log n) | O(log n) | O(log n) |

The three bolded cells are the ones interviewers ask about.

### 4. Must remember

1. **Default to reporting the worst case** unless asked otherwise. That is the convention in interviews and the safe answer.
2. Insertion sort is O(n) on already-sorted input. Selection sort is O(n²) on everything, because it scans the remaining array regardless. This is why insertion sort is used as the base case inside real sorting libraries.
3. `std::sort` avoids quicksort's worst case by switching to heapsort when recursion gets too deep. That is what "introsort" means, and it is why the C++ standard guarantees O(n log n).
4. Unbalanced BST degrades to a linked list when you insert sorted data. `std::set` and `std::map` are red-black trees, so they self-balance and never degrade.
5. Hash map worst case is O(n) per operation under collisions. Average case O(1) is what you quote, worst case O(n) is the follow-up answer.

### 5. Common mistakes

- Claiming quicksort is O(n log n) worst case. It is not.
- Claiming `unordered_map` is O(1) worst case. It is not.
- Confusing average case with amortised. They are different ideas; see 1.7.

---

## 1.4 Space complexity

### 1. What is it?

How much extra memory an algorithm uses as a function of input size.

### 2. Why do we need it?

Memory limits are real on judges, typically 256 MB. More importantly, space is a legitimate axis of optimisation that interviewers ask about constantly: "can you do this in O(1) space?" is a standard follow-up, and for many array and linked-list problems it is the whole point of the question.

### 3. Core idea

Count only what you allocate, not the input itself. This is **auxiliary space**, and it is what people mean by "space complexity" unless they say otherwise.

```cpp
// O(1) auxiliary: a few scalars regardless of n
int sum(const vector<int>& v) {
    int total = 0;
    for (int x : v) total += x;
    return total;
}

// O(n) auxiliary: allocates proportional to input
vector<int> doubled(const vector<int>& v) {
    vector<int> res;
    for (int x : v) res.push_back(x * 2);
    return res;
}
```

### 4. The rule people forget: recursion costs space

**Every recursive call holds a stack frame until it returns.** Recursion depth `d` means O(d) space, even if the function allocates nothing.

```cpp
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);          // depth n → O(n) space
}
```

This looks like an O(1)-space function. It is O(n). Consequences you will meet later:

| Algorithm | Space | Why |
|---|---|---|
| Recursive tree traversal | O(h), h = height | Stack depth, O(n) for a skewed tree, O(log n) balanced |
| Merge sort | O(n) | The merge buffer dominates the O(log n) stack |
| Quick sort | O(log n) average | Recursion stack only, partitioning is in place |
| DFS on a graph | O(V) | Stack depth plus visited array |
| BFS on a graph | O(V) | Queue can hold a whole level |
| Recursive fibonacci | O(n) | Depth, not the 2ⁿ node count: only one root-to-leaf path is alive at a time |

That last row is worth pausing on. A recursion tree with 2ⁿ nodes does **not** use 2ⁿ space. The tree is explored depth-first, so only one path is on the stack at any moment. Time is O(2ⁿ), space is O(n). Conflating the two is a common interview slip.

### 5. Conventions

- The **output** usually does not count toward auxiliary space. Returning a vector of n results from an otherwise O(1) algorithm is still described as O(1) auxiliary, with the output noted separately. Say it explicitly: "O(1) extra space, not counting the output."
- The **input** never counts.
- "In-place" means O(1) auxiliary space.

### 6. Must remember

1. Recursion depth is space. Always include it.
2. A 2ⁿ-time recursion is usually O(n) space, not O(2ⁿ).
3. Memoisation trades space for time. A DP with 2D state is O(n·m) space, which is often the thing you optimise away next (Module 13 covers rolling arrays).
4. `vector<int>` of size 10⁶ is about 4 MB. `vector<vector<int>>` of size 10⁴ × 10⁴ is 400 MB and will exceed the limit. Do the arithmetic before allocating a large 2D array.
5. Stack memory is typically 1–8 MB while heap is system RAM. A local `int arr[10⁶]` crashes; a global one or a `vector` does not. (Module 0, Section D.)
6. "Can you do it in O(1) space?" almost always means one of: two pointers, in-place swapping, bit manipulation, or reusing the input array as storage.

### 7. Common mistakes

- Reporting O(1) space for a recursive function.
- Counting the output array and calling an in-place algorithm O(n).
- Forgetting the `visited` array in a graph traversal's space cost.
- Allocating a 2D DP table when the transition only needs the previous row.

---

## 1.5 Recursive complexity

### 1. What is it?

Working out the cost of a function that calls itself. Two techniques cover everything you will meet: the recursion tree, and pattern-matching a small set of recurrences.

### 2. Why do we need it?

Because half the algorithms in this handbook are recursive, and "why is merge sort n log n" is a guaranteed interview question.

### 3. Core idea

**Total cost = (number of nodes in the recursion tree) × (work done at each node).**

When work per node varies, sum level by level instead.

### 4. Method 1: the recursion tree

Merge sort on n elements:

```
                    n                <- 1 node,  n work   = n
            n/2           n/2        <- 2 nodes, n/2 each = n
        n/4    n/4    n/4    n/4     <- 4 nodes, n/4 each = n
         ...                         <- log n levels
        1  1  1  1  ...  1  1        <- n nodes, 1 each   = n
```

Every level does O(n) total work. There are log₂n levels, because the size halves each time and halving stops at 1. Total: **O(n log n)**.

Compare naive fibonacci:

```
                 f(5)
          f(4)          f(3)
      f(3)   f(2)    f(2)   f(1)
    f(2) f(1) ...
```

Branching factor 2, depth n, so roughly 2ⁿ nodes, O(1) work each → **O(2ⁿ)** time, O(n) space. Memoisation collapses this to n distinct states, which is the entire idea behind Module 13.

### 5. Method 2: the recurrence patterns

Memorise these six. They cover essentially every recursive algorithm in placement DSA.

| Recurrence | Complexity | Example |
|---|---|---|
| T(n) = T(n−1) + O(1) | O(n) | Linear recursion, list traversal |
| T(n) = T(n−1) + O(n) | O(n²) | Selection-sort style, quicksort worst case |
| T(n) = T(n/2) + O(1) | O(log n) | Binary search |
| T(n) = 2T(n/2) + O(1) | O(n) | Tree traversal, counting nodes |
| T(n) = 2T(n/2) + O(n) | O(n log n) | Merge sort, quicksort average |
| T(n) = 2T(n−1) + O(1) | O(2ⁿ) | Subsets, naive fibonacci |

The distinction that trips people up: `T(n/2)` **divides** the problem, giving a log-depth tree. `T(n−1)` **shrinks** it by one, giving a linear-depth tree. Two recursive calls on half the input is O(n log n); two recursive calls on n−1 is exponential.

### 6. Method 3: Master Theorem (the simple form)

For `T(n) = a·T(n/b) + O(n^d)` with a ≥ 1, b > 1:

| Condition | Result |
|---|---|
| d > log_b a | O(n^d) |
| d = log_b a | O(n^d log n) |
| d < log_b a | O(n^(log_b a)) |

Merge sort: a = 2, b = 2, d = 1. log₂2 = 1 = d → O(n log n). ✓
Binary search: a = 1, b = 2, d = 0. log₂1 = 0 = d → O(log n). ✓

Worth knowing the form, not worth memorising the proof. If you can pattern-match the six recurrences above, you will rarely need this.

### 7. Backtracking and DP complexity

Two more rules that are really the same rule:

**Backtracking: (branching factor)^(depth) × work per node.**

| Problem | Branches | Depth | Complexity |
|---|---|---|---|
| All subsets | 2 (take / skip) | n | O(2ⁿ · n) |
| All permutations | n, n−1, n−2, … | n | O(n! · n) |
| N-Queens | ≤ n | n | O(n!) loose, far less with pruning |

The extra `· n` is the cost of copying each completed answer into the result.

**DP: (number of distinct states) × (cost per transition).**

This is the single most useful complexity rule in the handbook. It means you can state a DP's complexity the moment you have defined the state, before writing any code.

| DP | States | Transition | Complexity |
|---|---|---|---|
| Fibonacci | n | O(1) | O(n) |
| 0/1 Knapsack | n × W | O(1) | O(n·W) |
| LCS | n × m | O(1) | O(n·m) |
| Matrix chain multiplication | n² | O(n) | O(n³) |
| Bitmask DP (TSP) | 2ⁿ × n | O(n) | O(2ⁿ · n²) |

### 8. Must remember

1. Recursion tree node count × work per node. When work varies, sum by level.
2. `T(n/2)` gives log depth; `T(n−1)` gives linear depth. This distinction is the whole difference between O(n log n) and O(2ⁿ).
3. Memoisation turns "number of calls" into "number of distinct states". That is why it works.
4. DP complexity = states × transition cost. Define the state, get the complexity for free.
5. A 2ⁿ-time recursion uses O(n) space, not O(2ⁿ).
6. Halving from n reaches 1 in log₂n steps. This is why anything that repeatedly halves is logarithmic.

### 9. Common mistakes

- Treating `2T(n−1)` as if it were `2T(n/2)`, reporting O(n log n) for an exponential algorithm.
- Forgetting the per-node work. `O(2ⁿ)` subsets is really `O(2ⁿ · n)` once you copy each subset out.
- Reporting memoised DP complexity as if it were still the naive recursion.
- Ignoring that a recursive call inside a loop multiplies the branching factor.

---

## 1.6 Amortised complexity

### 1. What is it?

The average cost per operation over a **worst-case sequence** of operations, when occasional expensive operations are paid for by many cheap ones.

### 2. Why do we need it?

Because several structures you use constantly have an occasional expensive step, and treating that step as the per-operation cost badly overestimates the total. `vector::push_back` is the standard example; the monotonic stack is the one that actually shows up in interview problems.

### 3. Core idea, via `push_back`

A vector doubles its capacity when full. Most `push_back` calls are O(1). The doubling ones are O(n) because everything gets copied.

Pushing n elements, the copies happen at sizes 1, 2, 4, 8, … n:

```
1 + 2 + 4 + 8 + ... + n  <  2n
```

Total cost for n pushes is O(n). Cost per push is O(1) **amortised**. No single push is guaranteed O(1), but any sequence of n pushes costs O(n).

### 4. Amortised vs average case

These are different and the distinction is a good interview answer.

| | Averaged over | Guarantee |
|---|---|---|
| **Average case** | Random inputs | Probabilistic. An adversary can break it. |
| **Amortised** | A sequence of operations | Deterministic. Holds for every sequence. |

`unordered_map` is O(1) **average** (an adversary can force collisions). `vector::push_back` is O(1) **amortised** (no input can make n pushes cost more than O(n)).

### 5. Where you will meet it

| Structure / technique | Amortised cost | Why |
|---|---|---|
| `vector::push_back` | O(1) | Doubling, geometric series |
| Monotonic stack | O(n) total | Each element pushed once and popped once |
| Two pointers / sliding window | O(n) total | Each pointer advances at most n times |
| DSU with path compression + union by rank | O(α(n)) ≈ O(1) | Compression flattens the tree |
| `unordered_map` rehashing | O(1) | Same doubling argument |

The monotonic-stack row is the one that matters for interviews. The code has a `while` loop inside a `for` loop and looks quadratic:

```cpp
for (int i = 0; i < n; i++) {
    while (!st.empty() && a[st.top()] < a[i]) st.pop();
    st.push(i);
}
```

Each index is pushed exactly once and popped at most once, so the total number of pops across the whole run is at most n. **O(n), not O(n²).** You will need to defend this out loud in Module 7.

### 6. Must remember

1. Amortised is a worst-case guarantee over a sequence, not a probabilistic one.
2. The argument is always the same: count the total work over n operations, divide by n.
3. "Each element enters and leaves the structure at most once" is the standard proof sentence for stacks, queues, and two-pointer walks. Learn to say it.
4. α(n), the inverse Ackermann function, is below 5 for any n you will ever see. Treat DSU as effectively O(1) but know the precise answer.
5. `v.reserve(n)` before n pushes eliminates the reallocations entirely. Worth mentioning as an optimisation.

### 7. Common mistakes

- Reporting O(n²) for a monotonic stack, sliding window, or two-pointer solution because of the nested loop.
- Saying `unordered_map` is "amortised O(1)" when the correct word is "average".
- Assuming amortised means the expensive operation never happens. It does happen; it is just rare enough to pay for itself.

---

## 1.7 Reading constraints: the table that does the work

### 1. What is it?

A mapping from the input limits in a problem statement to the complexity the setter intended.

### 2. Why do we need it?

Because it converts a guessing game into a lookup. The constraints are the strongest hint in any problem statement, and most candidates ignore them entirely.

### 3. Core idea

Judges and OA platforms allow roughly **10⁸ simple operations per second** for C++. With a typical 1–2 second limit, target around **10⁷ to 10⁸ operations total**. Work backwards from `n` to the complexity that lands in that budget.

### 4. The table

| Constraint on n | Target complexity | Typical technique |
|---|---|---|
| n ≤ 10–12 | O(n!) | Permutations, brute-force TSP |
| n ≤ 20–25 | O(2ⁿ) or O(2ⁿ · n) | Subsets, bitmask DP, meet in the middle |
| n ≤ 100 | O(n³) or O(n⁴) | Floyd-Warshall, interval DP, matrix chain |
| n ≤ 500 | O(n³) | Interval DP, some graph DP |
| n ≤ 2,000–5,000 | O(n²) | 2D DP (LCS, edit distance), all-pairs loops |
| n ≤ 10⁵ | O(n log n) | Sorting, heap, binary search, set/map, divide and conquer |
| n ≤ 10⁶ | O(n) or O(n log n) tight | Single pass, two pointers, sliding window, prefix sums, counting |
| n ≤ 10⁸ | O(n) with a tiny constant | Simple loop, no allocations, no STL containers |
| n ≤ 10⁹ or 10¹⁸ | O(log n) or O(1) | Binary search on answer, math formula, fast exponentiation |

### 5. How to actually use it

You read the constraints **first**, before thinking about the algorithm.

- `n = 10⁵` and you are considering a nested loop: stop. O(n²) is 10¹⁰ operations, roughly 100 seconds. It will not pass. You need sorting, a hash map, two pointers, or binary search.
- `n = 20` and you are hunting for a polynomial solution: stop. The setter chose 20 because 2²⁰ ≈ 10⁶ is fine. The answer is subsets or bitmask DP.
- `n = 100` in a graph problem: O(n³) is 10⁶. Floyd-Warshall is on the table.
- `n = 10⁹` and an array is never mentioned: you cannot even iterate. The answer is binary search on the answer, or a closed-form formula.

**Say this out loud in interviews.** "The constraint is 10⁵, so I'm targeting n log n or better, which rules out the pairwise approach" is a strong opening sentence. It shows you are engineering, not pattern-matching.

### 6. The growth table, for intuition

Operations performed, by complexity and input size:

| n | log₂n | n | n log n | n² | n³ | 2ⁿ |
|---|---|---|---|---|---|---|
| 10 | 3 | 10 | 33 | 100 | 1,000 | 1,024 |
| 100 | 7 | 100 | 664 | 10⁴ | 10⁶ | 10³⁰ |
| 1,000 | 10 | 10³ | 10⁴ | 10⁶ | 10⁹ | — |
| 10⁵ | 17 | 10⁵ | 1.7×10⁶ | 10¹⁰ | — | — |
| 10⁶ | 20 | 10⁶ | 2×10⁷ | 10¹² | — | — |
| 10⁹ | 30 | 10⁹ | — | — | — | — |

Read the row for your `n` and find the rightmost column still under 10⁸. That is your budget.

### 7. Must remember

1. ~10⁸ simple operations per second in C++. This is a rule of thumb, not a guarantee; STL-heavy code with maps and allocations runs several times slower per operation.
2. n = 10⁵ with O(n²) is 10¹⁰. Always fails. This single fact rules out more wrong approaches than any other.
3. n ≤ 20 is a deliberate signal for exponential. Setters do not choose 20 by accident.
4. n ≤ 100 with a graph almost always means Floyd-Warshall or O(n³) DP.
5. If `n` is 10⁹ or larger, you cannot touch every element. The answer involves binary search, maths, or bit tricks.
6. A `map` or `set` operation is O(log n) with a *large* constant (pointer chasing, cache misses). O(n log n) via `sort` on a vector is usually several times faster than O(n log n) via `map`. When a solution is borderline, switching from `map` to a sorted vector often saves it.

### 8. Common mistakes

- Not reading the constraints at all, then optimising the wrong thing.
- Assuming O(n log n) always passes at n = 10⁶. With a heavy constant (a `map` in the inner loop) it can still time out.
- Seeing n ≤ 20 and searching for a polynomial solution that does not exist.
- Forgetting that the number of test cases multiplies everything. `T ≤ 10⁴` with `n ≤ 10⁵` means the *sum* of n is usually bounded; check whether the statement says so.

---

## 1.8 STL complexity reference

Repeated from Module 0 because you will look it up from here.

| Container | Access | Search | Insert | Erase | Notes |
|---|---|---|---|---|---|
| `vector` | O(1) | O(n) | O(1) back*, O(n) middle | O(1) back, O(n) middle | *amortised |
| `string` | O(1) | O(n·m) | O(1) back* | O(n) middle | `substr` is O(len) |
| `deque` | O(1) | O(n) | O(1) both ends | O(1) both ends | not contiguous |
| `stack` / `queue` | O(1) at the end | — | O(1) | O(1) | adapters |
| `priority_queue` | O(1) top | — | O(log n) | O(log n) | O(n) build from range |
| `set` / `map` | O(log n) | O(log n) | O(log n) | O(log n) | sorted, `lower_bound` O(log n) |
| `unordered_set` / `unordered_map` | O(1) avg | O(1) avg, O(n) worst | O(1) avg | O(1) avg | no ordering |

| Algorithm | Complexity |
|---|---|
| `sort` | O(n log n) |
| `stable_sort` | O(n log n), O(n) extra space |
| `nth_element` | O(n) average |
| `lower_bound` / `upper_bound` / `binary_search` | O(log n), sorted input |
| `accumulate`, `count`, `find`, `max_element` | O(n) |
| `unique` | O(n), adjacent only |
| `next_permutation` | O(n) |
| `__gcd` | O(log min(a,b)) |
| `__builtin_popcount` | O(1) |

**The rule that catches people:** an STL call inside a loop multiplies. `for (int i = 0; i < n; i++) st.insert(x);` is O(n log n). `for (int i = 0; i < n; i++) mp.count(k);` is O(n log n) with `map`, O(n) with `unordered_map`.

---

## 1.9 Comparison tables

### Big O vs Big Theta vs Big Omega

| | Bound | Says | Used for |
|---|---|---|---|
| O(f) | Upper | No worse than f | Everyday use, worst-case claims |
| Ω(f) | Lower | At least f | Problem lower bounds (sorting is Ω(n log n)) |
| Θ(f) | Tight | Exactly f | Precise statements when both bounds match |

### Average case vs amortised

| | Averaged over | Adversary-proof? | Example |
|---|---|---|---|
| Average case | Random inputs | No | `unordered_map` lookup |
| Amortised | A sequence of operations | Yes | `vector::push_back`, monotonic stack, DSU |

### Time vs space trade-off, the standard moves

| Trade | Cost | Gain | Example |
|---|---|---|---|
| Hash map instead of nested loop | O(n) space | O(n²) → O(n) | Two Sum |
| Memoisation | O(states) space | Exponential → polynomial | Any DP |
| Prefix sums | O(n) space | O(n) per query → O(1) | Range sum |
| Sorting first | O(1) or O(n) space | Enables two pointers, binary search | 3Sum, intervals |
| Two pointers instead of hash map | — | O(n) space → O(1) | Pair sum in a sorted array |

---

## 1.10 Practice: analyse these

Work each out before reading the answer. Target: 30 seconds each. This is the single highest-value drill in the module.

```cpp
// 1
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++) count++;

// 2
for (int i = 1; i <= n; i *= 2)
    for (int j = 0; j < n; j++) count++;

// 3
for (int i = 0; i < n; i++) sort(v.begin(), v.end());

// 4
string s;
for (int i = 0; i < n; i++) s = s + v[i];     // s is a string

// 5
int j = 0;
for (int i = 0; i < n; i++) {
    while (j < n && a[j] < a[i]) j++;
}

// 6
for (int i = 0; i < n; i++)
    for (int j = i; j < n; j++) count++;

// 7
map<int,int> mp;
for (int i = 0; i < n; i++) mp[a[i]]++;

// 8
void f(int n) { if (n <= 1) return; f(n/2); f(n/2); }

// 9
void g(int n) { if (n <= 1) return; g(n-1); g(n-1); }

// 10
for (int i = 0; i < n; i++)
    for (int j = 1; j < n; j *= 2) count++;

// 11
int fib(int n) { if (n <= 1) return n; return fib(n-1) + fib(n-2); }
// time? space?

// 12
for (int i = 0; i < n; i++) {
    vector<int> temp = v;       // v has n elements
    temp.push_back(i);
}
```

### Answers

1. **O(n³).** Three independent nested loops.
2. **O(n log n).** Outer doubles (log n iterations), inner is n.
3. **O(n² log n).** The sort is O(n log n) and runs n times. A classic accidental blowup.
4. **O(n²).** `s + v[i]` builds a whole new string each time. `s += v[i]` would be O(n) total.
5. **O(n).** `j` never resets and advances at most n times overall. The sliding-window shape.
6. **O(n²).** Triangular: n(n+1)/2 iterations, which is still quadratic.
7. **O(n log n).** Each `map` operation is O(log n). With `unordered_map` it would be O(n) average.
8. **O(n).** T(n) = 2T(n/2) + O(1). Node count doubles while size halves, giving n leaves and O(1) per node.
9. **O(2ⁿ).** T(n) = 2T(n−1) + O(1). Branching 2 with depth n. Compare with 8: this is the `n/2` versus `n−1` distinction.
10. **O(n log n).** Outer n, inner doubles.
11. **Time O(2ⁿ)** (technically O(φⁿ), often written 2ⁿ), **space O(n)** for the recursion depth. Do not say O(2ⁿ) space.
12. **O(n²).** The copy `temp = v` is O(n) and happens n times. The kind of cost that hides inside one innocent line.

If you got 10 or more right, move on. If you missed 5, 8, 9, or 11, reread Sections 1.1 (Rule 6) and 1.5, because those four are the ones that matter downstream.

---

## 1.11 Saying it out loud

A small thing that changes how interviews go. When you finish describing an approach, volunteer the analysis in this shape:

> "Time is O(n log n), dominated by the sort. Space is O(n) for the hash map, or O(1) extra if we're allowed to modify the input. With n up to 10⁵ that's around 1.7 million operations, comfortably within limits."

Three parts: the complexity, **what causes it**, and whether it fits the constraints. Naming the dominant operation is what separates "I memorised that merge sort is n log n" from "I understand where the cost comes from". Interviewers are listening for the second thing.

If best and worst differ, say so unprompted: "average O(1) for the hash lookups, worst case O(n) if everything collides, which won't happen here."

---

## Must remember (consolidated)

1. Drop constants and lower-order terms; keep the dominant one.
2. Nested loops multiply **only if the inner index resets**. If it does not, the total is linear.
3. `log₂(10⁵) ≈ 17`, `log₂(10⁶) ≈ 20`, `log₂(10⁹) ≈ 30`.
4. Recursion depth is space. A 2ⁿ-time recursion is O(n) space.
5. `T(n/2)` gives log depth; `T(n−1)` gives linear depth. That is the O(n log n) versus O(2ⁿ) fork.
6. DP complexity = number of states × cost per transition.
7. Amortised is a worst-case guarantee over a sequence; average case is probabilistic and breakable.
8. Monotonic stack, sliding window, and two pointers are all O(n) by the "each element enters and leaves once" argument.
9. Quicksort worst case is O(n²); `std::sort` is O(n log n) guaranteed; `unordered_map` worst case is O(n).
10. Comparison sorting is Ω(n log n). Counting and radix sort escape this by not comparing.
11. ~10⁸ operations per second. n = 10⁵ with O(n²) never passes.
12. Define what `n` refers to before quoting a complexity, especially for graphs (V and E) and grids (n·m).

---

## Common mistakes (consolidated)

- Calling sliding window or monotonic stack O(n²) because of the nested loop.
- Reporting O(1) space for a recursive function.
- Reporting O(2ⁿ) space for a 2ⁿ-time recursion.
- Treating `2T(n−1)` as `2T(n/2)`.
- Ignoring the cost of STL calls, `substr`, string concatenation, or vector copies inside loops.
- Sorting inside a loop and reporting the sort's complexity as the total.
- Saying `unordered_map` or quicksort is worst-case optimal when neither is.
- Analysing the algorithm you meant to write rather than the code on the screen.
- Not reading the constraints before choosing an approach.
- Using "average case" and "amortised" interchangeably.

---

## Exit checklist

```
[ ] I state complexity unprompted after every solution
[ ] I read constraints BEFORE choosing an approach
[ ] I know the constraint -> complexity table cold
[ ] I can tell a resetting inner loop from a non-resetting one
[ ] I can draw the merge sort recursion tree and explain n log n
[ ] I know the six standard recurrences
[ ] I include recursion depth in space complexity
[ ] I know DP complexity = states x transition cost
[ ] I can explain amortised vs average case
[ ] I can explain why a monotonic stack is O(n)
[ ] I know the three worst-case gotchas (quicksort, unordered_map, unbalanced BST)
[ ] I scored 10+ on the Section 1.10 drill
```

---

## Next

Say **"Start Phase 2"** for Arrays and Strings (20–25 hours, the largest Tier 1 module). It covers traversal and in-place operations, prefix sums and difference arrays, frequency counting, Kadane's algorithm, and the two patterns that generate more interview questions than anything else: two pointers and sliding window. Every pattern gets the recognition-signal treatment, so this is where the "I know what kind of problem this is" skill starts being built.

It is a big module. If you would rather split it, say "Start Phase 2, arrays only" and I will hold the string half for a separate pass.
