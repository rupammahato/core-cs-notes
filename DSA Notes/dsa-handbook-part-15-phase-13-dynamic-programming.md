# DSA Placement Handbook (C++) — Part 15
# Phase 13: Dynamic Programming

**Module 13 · 30–35 hours · Tier 1 · Requires: Modules 0, 1, 2, 4, 11**

---

## How this module is different

Most DP material is a list of problems. That approach fails in interviews, because you will be handed a problem you have not memorised and asked to derive a recurrence in twenty minutes.

So this module teaches a **procedure** first — five steps that turn a problem statement into a recurrence — and then applies that procedure to each DP family in turn. Every worked example follows the same five steps in the same order. By the fourth family it should feel mechanical.

Two pieces of groundwork are already in place:

- **Module 4.9** showed memoisation as three lines added to a naive recursion. That is still the fastest way to get a first working DP.
- **Module 1.5** gave the complexity rule: **states × transition cost**. That lets you evaluate a DP formulation *before* writing any code, which is what makes the five-step method practical.

### Budget for the 32 hours

| Part | Hours | Content |
|---|---|---|
| A — Foundations and the framework | 5 | The five steps, memo vs tabulation, space optimisation |
| B1 — 1D linear | 3 | Fibonacci, house robber, decode ways |
| B2 — Knapsack | 7 | 0/1, subset sum, unbounded, coin change |
| B3 — Two strings | 5 | LCS, edit distance, and relatives |
| B4 — LIS | 2 | O(n²) and O(n log n) |
| B5 — Grid | 2 | Unique paths, min path sum |
| B6 — Interval | 4 | MCM, burst balloons, palindromes |
| B7 — Stock / state machine | 3 | The unified formulation |
| B8 — Bitmask | 1 | Advanced, read-only unless targeting hard OAs |

**Knapsack gets the most time on purpose.** Six or seven standard interview problems are knapsack wearing different clothes, and the forward/backward loop distinction in Section 13.8 is the highest-value single detail in the module.

---

# PART A — Foundations

## 13.1 What DP actually is

### 1. What is it?

Solving a problem by breaking it into overlapping subproblems, solving each **once**, and reusing the answers.

### 2. The two required conditions

**Overlapping subproblems.** The naive recursion solves the same subproblem many times. Naive Fibonacci computes `fib(3)` repeatedly; that duplication is what caching removes.

If subproblems do **not** overlap, caching gains nothing. Merge sort's two halves are disjoint, which is why merge sort is divide and conquer rather than DP.

**Optimal substructure.** An optimal solution is built from optimal solutions to subproblems. If the best way to make 11 from coins uses a 5, then the rest must be the best way to make 6.

This is shared with greedy. **The difference is that greedy proves one choice is safe and commits; DP tries every choice and compares** (Module 11.3). DP is the fallback when the greedy choice property fails.

### 3. Core idea

```
Naive recursion:  explores a tree with exponentially many nodes,
                  but only polynomially many DISTINCT nodes.

DP:               compute each distinct node once.

Time = (number of distinct states) × (cost per transition)
```

That last line is the whole of DP complexity analysis, and it is why defining the state carefully is the entire game.

### 4. How to identify a DP problem

The signals, roughly in order of reliability:

| Signal | Example phrasing |
|---|---|
| Asks for **count of ways** | "how many ways to...", "number of distinct..." |
| Asks for **min/max under constraints** | "minimum cost", "maximum value such that..." |
| Asks for **feasibility** | "is it possible to...", "can you partition..." |
| A **choice** at each step | take/skip, cut here or there, which character to match |
| **Greedy provably fails** | you found a counterexample in two minutes (Module 11.2) |
| **Constraints are small** | n ≤ 10³ with an O(n²) budget; n × target ≤ 10⁷ |
| **Subsequence** (not subarray) | contiguity absent means you cannot slide a window |

**The strongest single tell:** you can describe the problem as a sequence of decisions, and a decision made now affects what is available later. That is a DP.

**The strongest counter-tell:** a greedy with a valid exchange argument exists. Then use greedy; it is faster and simpler.

### 5. Must remember

1. DP needs **overlapping subproblems** and **optimal substructure**.
2. No overlap means divide and conquer, not DP.
3. Greedy commits; DP compares. Use DP when you cannot prove the greedy choice.
4. Complexity = states × transition cost.
5. "Count the ways", "min/max under a constraint", and "subsequence" are the strongest signals.
6. DP is never *wrong*, only sometimes slower than a provable greedy.

---

## 13.2 Memoisation vs tabulation

Two ways to implement the same recurrence.

### Memoisation (top-down)

Write the naive recursion, add a cache.

```cpp
vector<int> memo;

int solve(int i) {
    if (i <= 1) return i;                    // base case
    if (memo[i] != -1) return memo[i];        // cache hit
    return memo[i] = solve(i-1) + solve(i-2); // compute, store, return
}
// caller: memo.assign(n+1, -1);
```

### Tabulation (bottom-up)

Fill a table in an order that guarantees dependencies come first.

```cpp
vector<int> dp(n+1);
dp[0] = 0; dp[1] = 1;                        // base cases
for (int i = 2; i <= n; i++)
    dp[i] = dp[i-1] + dp[i-2];               // transition
return dp[n];
```

### Comparison

| | Memoisation | Tabulation |
|---|---|---|
| Direction | Top-down | Bottom-up |
| Written from | The naive recursion | The recurrence |
| Computes | Only **reachable** states | **All** states |
| Space | Table + O(depth) **recursion stack** | Table only |
| Stack overflow risk | **Yes**, at depth ~10⁵ | No |
| Space optimisation | Hard | **Easy** |
| Easier to derive | **Yes** | No |
| Constant factor | Worse (call overhead) | Better |

### The recommended workflow

1. **Write the naive recursion** using the contract method from Module 4.3. Get it correct.
2. **Add memoisation.** Three lines. Now it is fast enough to submit.
3. **Convert to tabulation** if you need space optimisation or you are worried about stack depth.

This order matters in an interview. Deriving tabulation directly requires you to already know the recurrence and the fill order; deriving the recursion first is far more reliable under pressure, and you can say "let me get this correct first, then optimise", which is exactly what an interviewer wants to hear.

**When memoisation is strictly better:** when the state space is large but only a small fraction is reachable. A tabulation fills everything; memoisation touches only what matters.

### Must remember

1. Same recurrence, two implementations.
2. Memoisation is easier to derive; tabulation is easier to space-optimise.
3. Memoisation carries recursion-stack space and a depth limit.
4. Memoisation skips unreachable states; tabulation does not.
5. Recursion → memoise → tabulate is the interview-safe order.
6. The memo must be keyed by **everything that varies**, passed by reference, with a sentinel that cannot be a legitimate answer.

---

## 13.3 The five-step framework

**The core of this module.** Every worked example below follows these five steps explicitly.

### Step 1 — Define the state

> **What parameters uniquely determine a subproblem's answer?**

Write it as an English sentence: `dp[i][j] = the ... considering ...`. If you cannot write that sentence, you do not have a state yet, and writing code will not help.

The state must be **sufficient**: two situations with the same state values must have the same answer. If they do not, you are missing a parameter.

The state must be **minimal**: extra parameters multiply the complexity for nothing.

### Step 2 — Define the transition

> **How does this state's answer follow from smaller states?**

This is where the "choice" lives. Usually: enumerate the options at this state, recurse on each, combine with `max`, `min`, or `+`.

- `max` / `min` → optimisation problems
- `+` → counting problems
- `||` → feasibility problems

### Step 3 — Define the base cases

> **Which states can I answer without recursing?**

Usually the empty case: index past the end, capacity 0, empty string. **Get these right first** — a wrong base case gives plausible wrong answers everywhere, and they are invisible in the transition.

### Step 4 — Determine the computation order

> **In what order do I fill the table so dependencies are already computed?**

For memoisation this is automatic. For tabulation:

- If `dp[i]` depends on `dp[i-1]`, iterate **forward**.
- If `dp[i]` depends on `dp[i+1]`, iterate **backward**.
- If `dp[i][j]` depends on shorter intervals, iterate **by length** (Section 13.12).

### Step 5 — Optimise space (if needed)

> **Which rows or columns do I actually still need?**

See Section 13.4.

### The worked example: Climbing Stairs

*You can climb 1 or 2 steps at a time. How many distinct ways to reach step n?*

**Step 1 — State.** `dp[i]` = the number of distinct ways to reach step `i`.

**Step 2 — Transition.** You arrive at `i` either from `i-1` (one step) or from `i-2` (two steps). Those are disjoint sets of ways, so:
`dp[i] = dp[i-1] + dp[i-2]`

**Step 3 — Base cases.** `dp[0] = 1` (one way to be at the start: do nothing), `dp[1] = 1`.

**Step 4 — Order.** `dp[i]` needs smaller indices, so iterate forward from 2.

**Step 5 — Space.** Only the last two values are ever read, so two variables suffice.

```cpp
int climbStairs(int n) {
    if (n <= 2) return n;
    int prev2 = 1, prev1 = 2;
    for (int i = 3; i <= n; i++) {
        int cur = prev1 + prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
```

O(n) time, O(1) space. **Say the five steps out loud in an interview.** It structures your explanation and demonstrates method rather than recall.

### Must remember

1. Write the state as an English sentence before writing code.
2. A state must be sufficient (captures everything that matters) and minimal (nothing more).
3. `max`/`min` for optimisation, `+` for counting, `||` for feasibility.
4. Base cases first. A wrong base case corrupts everything silently.
5. Fill order is dictated by the direction of the dependency.
6. Complexity = states × transition cost, known as soon as Step 2 is done.

---

## 13.4 Space optimisation

### The rule

**Look at what the transition reads.** If `dp[i]` only reads `dp[i-1]` and `dp[i-2]`, you never need the whole array.

| Transition reads | Keep |
|---|---|
| `dp[i-1]`, `dp[i-2]` | Two variables |
| `dp[i-1][*]` (previous row only) | Two rows, or one row with care |
| `dp[i-1][j]` and `dp[i][j-1]` | One row |
| All previous rows | The full table |

### The 2D → 1D conversion, and the direction trap

When `dp[i][j]` depends only on row `i-1`, you can reuse a single row. But **the iteration direction decides which row you are actually reading**:

```cpp
// dp[i][j] depends on dp[i-1][j] and dp[i-1][j-w]      (PREVIOUS row)
for (int j = W; j >= w; j--)          // BACKWARD: dp[j-w] is still row i-1
    dp[j] = max(dp[j], dp[j-w] + v);

// dp[i][j] depends on dp[i-1][j] and dp[i][j-w]        (CURRENT row)
for (int j = w; j <= W; j++)          // FORWARD: dp[j-w] is already row i
    dp[j] = max(dp[j], dp[j-w] + v);
```

This is not a stylistic choice. **Backward means "each item used at most once" (0/1 knapsack); forward means "each item reusable" (unbounded knapsack).** Section 13.8 develops this properly, but it is the most important consequence of space optimisation in the whole module.

### When not to optimise

If the problem asks you to **reconstruct** the actual solution (which items, which subsequence), you need the full table to trace back. Optimise space only after the answer is correct, and mention the trade-off.

### Must remember

1. Drop dimensions the transition never reads.
2. In a 1D rolling array, **direction determines which row you read**.
3. Backward = previous row = each item once. Forward = current row = reuse allowed.
4. Space optimisation destroys the information needed to reconstruct the solution.
5. Optimise last, after correctness. Say so in an interview.

---

# PART B — The DP families

## 13.5 Family 1: linear 1D DP

**Shape:** `dp[i]` depends on a constant number of earlier indices.

### House Robber (LC 198)

*Maximum sum from a row of houses, no two adjacent.*

**Step 1 — State.** `dp[i]` = the maximum money robbable from houses `0..i`.

**Step 2 — Transition.** At house `i` you either rob it (and must skip `i-1`) or skip it:
`dp[i] = max(dp[i-1], dp[i-2] + a[i])`

**Step 3 — Base.** `dp[0] = a[0]`, `dp[1] = max(a[0], a[1])`.

**Step 4 — Order.** Forward.

**Step 5 — Space.** Two variables.

```cpp
int rob(const vector<int>& a) {
    int prev2 = 0, prev1 = 0;                 // dp[i-2], dp[i-1]
    for (int x : a) {
        int cur = max(prev1, prev2 + x);
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
```

Starting both at 0 handles the empty and single-element cases without special-casing.

### House Robber II (LC 213): circular

First and last houses are now adjacent, so they cannot both be robbed. Split into two linear problems:

```cpp
int rob2(const vector<int>& a) {
    int n = a.size();
    if (n == 1) return a[0];
    return max(robRange(a, 0, n-2), robRange(a, 1, n-1));
}
```

**The reduction is the insight**, not the DP. "Circular" problems frequently reduce to two linear ones by fixing a decision about the wrap-around point.

### Decode Ways (LC 91)

*How many ways to decode a digit string, where 1–26 map to A–Z?*

**State.** `dp[i]` = number of ways to decode the first `i` characters.

**Transition.** The `i`-th character can stand alone (if not '0'), or join the previous one (if the two-digit value is 10–26):

```cpp
int numDecodings(const string& s) {
    int n = s.size();
    if (s[0] == '0') return 0;

    int prev2 = 1, prev1 = 1;                 // dp[0] = 1, dp[1] = 1
    for (int i = 2; i <= n; i++) {
        int cur = 0;
        if (s[i-1] != '0') cur += prev1;                          // single digit
        int two = (s[i-2] - '0') * 10 + (s[i-1] - '0');
        if (two >= 10 && two <= 26) cur += prev2;                 // two digits
        if (cur == 0) return 0;                                    // dead end
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
```

**Zeros are the whole difficulty.** '0' can never stand alone and can only be part of "10" or "20". The problem is asked precisely because of this edge case, so enumerate it deliberately.

### The family

| Problem | State | Transition |
|---|---|---|
| Climbing Stairs (70) | ways to reach `i` | `dp[i-1] + dp[i-2]` |
| Min Cost Climbing Stairs (746) | min cost to reach `i` | `min(dp[i-1]+c[i-1], dp[i-2]+c[i-2])` |
| House Robber (198) | max from `0..i` | `max(dp[i-1], dp[i-2]+a[i])` |
| House Robber II (213) | — | two linear runs |
| Decode Ways (91) | ways for first `i` chars | one-digit + two-digit |
| Fibonacci (509) | `fib(i)` | `dp[i-1] + dp[i-2]` |

### Must remember

1. Linear DP is almost always space-optimisable to two or three variables.
2. Initialising both accumulators to 0 avoids special-casing short inputs.
3. Circular variants usually reduce to two linear runs.
4. Counting problems add; optimisation problems take `max`/`min`.
5. In Decode Ways, zeros are the problem. Handle them explicitly.

---

## 13.6 Family 2: the Knapsack family

**The highest-value family in the module.** Six or more standard interview problems are this one pattern.

### The two archetypes

| | 0/1 Knapsack | Unbounded Knapsack |
|---|---|---|
| Each item | used **at most once** | used **any number of times** |
| 2D transition reads | `dp[i-1][w - wt]` | `dp[i][w - wt]` |
| 1D loop direction | **Backward** | **Forward** |
| Examples | Subset sum, partition, target sum | Coin change, rod cutting |

**That table is the family.** Everything else is a relabelling.

### 0/1 Knapsack: the 2D form

*Items with weight and value, capacity W, each item used at most once. Maximise value.*

**Step 1 — State.** `dp[i][w]` = the maximum value using the first `i` items with capacity exactly at most `w`.

**Step 2 — Transition.** For item `i`, skip it or take it:
```
dp[i][w] = dp[i-1][w]                                        // skip
dp[i][w] = max(that, val[i] + dp[i-1][w - wt[i]])            // take, if it fits
```

**Step 3 — Base.** `dp[0][w] = 0` for all `w`: no items means no value.

**Step 4 — Order.** Increasing `i`, any order of `w`.

```cpp
int knapsack(int W, const vector<int>& wt, const vector<int>& val) {
    int n = wt.size();
    vector<vector<int>> dp(n+1, vector<int>(W+1, 0));

    for (int i = 1; i <= n; i++)
        for (int w = 0; w <= W; w++) {
            dp[i][w] = dp[i-1][w];                                   // skip
            if (wt[i-1] <= w)
                dp[i][w] = max(dp[i][w], val[i-1] + dp[i-1][w - wt[i-1]]);
        }
    return dp[n][W];
}
```

O(n·W) time and space. Note `wt[i-1]` because the table is 1-indexed on items and the array is 0-indexed — the off-by-one that causes half the bugs here.

**Step 5 — Space: the 1D form**

```cpp
int knapsack(int W, const vector<int>& wt, const vector<int>& val) {
    vector<int> dp(W+1, 0);
    for (int i = 0; i < (int)wt.size(); i++)
        for (int w = W; w >= wt[i]; w--)                    // BACKWARD
            dp[w] = max(dp[w], val[i] + dp[w - wt[i]]);
    return dp[W];
}
```

### Why backward, and why it matters

This is the detail to internalise.

In the 1D array, `dp[w]` holds row `i-1`'s value until you overwrite it.

- Going **backward**, when you compute `dp[w]` you read `dp[w - wt[i]]` at a **smaller** index, which you have **not yet touched** this round. So it still holds row `i-1`: item `i` has not been used. **Each item once.**
- Going **forward**, `dp[w - wt[i]]` was **already updated** this round, so it may already include item `i`. Using it again reuses the item. **Unlimited copies.**

The direction is not an implementation detail. It *is* the difference between the two problems.

### Unbounded Knapsack / Coin Change

```cpp
// Minimum number of coins to make `amount`
int coinChange(const vector<int>& coins, int amount) {
    const int INF = 1e9;
    vector<int> dp(amount+1, INF);
    dp[0] = 0;                                              // 0 coins make 0

    for (int c : coins)
        for (int a = c; a <= amount; a++)                   // FORWARD: reuse allowed
            if (dp[a-c] != INF)
                dp[a] = min(dp[a], dp[a-c] + 1);

    return dp[amount] == INF ? -1 : dp[amount];
}
```

The `dp[a-c] != INF` guard prevents `INF + 1` from masquerading as a real answer.

### The loop-order trap: combinations vs permutations

**Coin Change II (LC 518)** counts the number of ways to make an amount. The loop order silently changes what you are counting.

```cpp
// COMBINATIONS: {1,2} and {2,1} count as ONE way.  Coin loop OUTSIDE.
for (int c : coins)
    for (int a = c; a <= amount; a++)
        dp[a] += dp[a-c];

// PERMUTATIONS: {1,2} and {2,1} count as TWO.      Amount loop OUTSIDE.
for (int a = 1; a <= amount; a++)
    for (int c : coins)
        if (c <= a) dp[a] += dp[a-c];
```

**Coin outer ⇒ combinations. Amount outer ⇒ permutations.** LC 518 wants combinations; LC 377 (Combination Sum IV) despite its name wants permutations. Both compile, both run, and one is wrong. Read the examples in the statement to determine which.

**Why:** with the coin loop outside, each coin is fully processed before the next is considered, so coins are always used in a fixed order and no reordering is ever counted twice. With the amount loop outside, every coin is tried at every amount, so orderings are distinguished.

### The disguises

| Problem | Really is | Target |
|---|---|---|
| Subset Sum (GFG) | 0/1, feasibility | boolean |
| Partition Equal Subset Sum (416) | 0/1, feasibility | `sum/2` |
| Target Sum (494) | 0/1, counting | `(sum+target)/2` |
| Last Stone Weight II (1049) | 0/1, minimise the gap | `sum/2` |
| Coin Change (322) | Unbounded, minimise | amount |
| Coin Change II (518) | Unbounded, count combinations | amount |
| Combination Sum IV (377) | Unbounded, count **permutations** | target |
| Perfect Squares (279) | Unbounded, minimise | n |
| Rod Cutting (GFG) | Unbounded, maximise | length |

### Subset Sum and Partition

```cpp
bool canPartition(const vector<int>& a) {
    int sum = accumulate(a.begin(), a.end(), 0);
    if (sum % 2) return false;                        // odd sum: impossible

    int target = sum / 2;
    vector<bool> dp(target+1, false);
    dp[0] = true;                                     // empty subset makes 0

    for (int x : a)
        for (int t = target; t >= x; t--)             // BACKWARD (0/1)
            dp[t] = dp[t] || dp[t-x];

    return dp[target];
}
```

**The odd-sum check first** is both a correctness requirement and the kind of early observation interviewers like.

### Target Sum (LC 494)

*Assign + or − to each number so the total equals `target`. Count the ways.*

**The reduction** is the whole problem. Let `P` be the sum of the positive group and `N` the sum of the negative group:

```
P − N = target
P + N = sum
-------------------
2P = sum + target   ->   P = (sum + target) / 2
```

So this is: **count the subsets summing to `(sum + target) / 2`** — a 0/1 counting knapsack.

```cpp
int findTargetSumWays(const vector<int>& a, int target) {
    int sum = accumulate(a.begin(), a.end(), 0);
    if (abs(target) > sum || (sum + target) % 2) return 0;    // impossible

    int P = (sum + target) / 2;
    vector<int> dp(P+1, 0);
    dp[0] = 1;

    for (int x : a)
        for (int t = P; t >= x; t--)                          // BACKWARD (0/1)
            dp[t] += dp[t-x];

    return dp[P];
}
```

Both guards are needed: `(sum+target)` must be non-negative and even.

### Must remember

1. **Backward = 0/1. Forward = unbounded.** The most valuable single line in this module.
2. 2D: 0/1 reads `dp[i-1][...]`, unbounded reads `dp[i][...]`.
3. **Coin loop outside = combinations. Amount loop outside = permutations.**
4. Base case `dp[0]`: `0` for minimisation, `1` for counting, `true` for feasibility.
5. Target Sum reduces to subset-count with `P = (sum + target) / 2`, with parity and range guards.
6. Partition requires an even sum. Check first.
7. Complexity is O(n · target). If `target` is large (10⁹), knapsack DP is not the intended solution.
8. Guard against `INF + 1` in minimisation problems.

### Common mistakes

- Wrong loop direction: 0/1 becoming unbounded or vice versa.
- Wrong loop order in counting problems, giving permutations for combinations.
- `wt[i-1]` versus `wt[i]` in the 2D form.
- Forgetting `dp[0] = 1` in counting versions.
- Not checking the parity/range guards in Target Sum.
- `INF + 1` overflowing or producing a fake answer.

---

## 13.7 Family 3: two-string DP

**Shape:** `dp[i][j]` = the answer for the first `i` characters of `a` and the first `j` of `b`.

Every problem in this family shares one transition skeleton:

```
if (a[i-1] == b[j-1])   dp[i][j] = <something> + dp[i-1][j-1];      // characters match
else                    dp[i][j] = <combine> (dp[i-1][j], dp[i][j-1]);
```

### Longest Common Subsequence (LC 1143)

```cpp
int lcs(const string& a, const string& b) {
    int n = a.size(), m = b.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));

    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= m; j++) {
            if (a[i-1] == b[j-1]) dp[i][j] = 1 + dp[i-1][j-1];
            else                  dp[i][j] = max(dp[i-1][j], dp[i][j-1]);
        }
    return dp[n][m];
}
```

**State:** `dp[i][j]` = length of the LCS of `a[0..i-1]` and `b[0..j-1]`.
**Transition:** if the last characters match, they belong to the LCS (provably safe), so extend the diagonal. If not, drop the last character of one string or the other and take the better.
**Base:** `dp[0][*] = dp[*][0] = 0`.

O(n·m) time and space; O(m) space with two rows.

### Longest Common **Substring**: one line different

```cpp
if (a[i-1] == b[j-1]) dp[i][j] = 1 + dp[i-1][j-1];
else                  dp[i][j] = 0;                 // RESET, not max
best = max(best, dp[i][j]);
```

Substrings must be **contiguous**, so a mismatch ends the run. The `else` resets to 0 instead of carrying a maximum forward, and the answer is the maximum cell rather than `dp[n][m]`.

**This one-line difference between subsequence and substring is a favourite interview follow-up.**

### Edit Distance (LC 72)

*Minimum insertions, deletions, and replacements to turn `a` into `b`.*

```cpp
int minDistance(const string& a, const string& b) {
    int n = a.size(), m = b.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));

    for (int i = 0; i <= n; i++) dp[i][0] = i;         // delete everything
    for (int j = 0; j <= m; j++) dp[0][j] = j;         // insert everything

    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= m; j++) {
            if (a[i-1] == b[j-1]) {
                dp[i][j] = dp[i-1][j-1];               // free: no operation
            } else {
                dp[i][j] = 1 + min({ dp[i-1][j-1],     // replace
                                     dp[i-1][j],       // delete from a
                                     dp[i][j-1] });    // insert into a
            }
        }
    return dp[n][m];
}
```

**The base cases are not zeros.** Turning a string of length `i` into an empty string costs `i` deletions. Initialising them to 0 gives wrong answers that look plausible on matched-length inputs.

**Know which neighbour means which operation:**

| Cell read | Operation |
|---|---|
| `dp[i-1][j-1]` | Replace `a[i-1]` with `b[j-1]` |
| `dp[i-1][j]` | Delete `a[i-1]` |
| `dp[i][j-1]` | Insert `b[j-1]` |

Interviewers ask this directly.

### The family

| Problem | Match case | Mismatch case | Answer |
|---|---|---|---|
| LCS (1143) | `1 + dp[i-1][j-1]` | `max(dp[i-1][j], dp[i][j-1])` | `dp[n][m]` |
| Longest Common Substring | `1 + dp[i-1][j-1]` | `0` | max cell |
| Edit Distance (72) | `dp[i-1][j-1]` | `1 + min(3 neighbours)` | `dp[n][m]` |
| Distinct Subsequences (115) | `dp[i-1][j-1] + dp[i-1][j]` | `dp[i-1][j]` | `dp[n][m]` |
| Shortest Common Supersequence (1092) | — | — | `n + m − LCS` |
| Delete Operation for Two Strings (583) | — | — | `n + m − 2·LCS` |

The last two rows are worth noticing: **several problems reduce to LCS plus arithmetic.** Spotting that saves deriving a new recurrence.

### Must remember

1. `dp[i][j]` over prefixes; the table is `(n+1) × (m+1)`.
2. `a[i-1]` and `b[j-1]`, because the table is 1-indexed and the strings are not.
3. Subsequence takes `max` on mismatch; **substring resets to 0**.
4. Edit Distance base cases are `i` and `j`, not 0.
5. Know which of the three neighbours means insert, delete, and replace.
6. Several problems reduce to `n + m − LCS` or `n + m − 2·LCS`.
7. O(n·m) time; O(min(n,m)) space with rolling rows.

---

## 13.8 Family 4: Longest Increasing Subsequence

### The O(n²) DP

```cpp
int lengthOfLIS(const vector<int>& a) {
    int n = a.size();
    vector<int> dp(n, 1);                     // dp[i] = LIS ENDING at i

    for (int i = 1; i < n; i++)
        for (int j = 0; j < i; j++)
            if (a[j] < a[i])
                dp[i] = max(dp[i], dp[j] + 1);

    return *max_element(dp.begin(), dp.end());
}
```

**`dp[i]` is the LIS *ending at* `i`, not the LIS of the prefix.** That distinction is what makes the transition work — you need to know the last element to decide whether you can extend. The answer is therefore the maximum over all `i`, not `dp[n-1]`.

This "best ending here" framing is the same one from Kadane (Module 2.9), and it is a recurring DP state design.

### The O(n log n) method

```cpp
int lengthOfLIS(const vector<int>& a) {
    vector<int> tails;                        // tails[k] = smallest tail of an LIS of length k+1

    for (int x : a) {
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);   // extends the longest
        else *it = x;                                 // improves a tail
    }
    return tails.size();
}
```

**`tails` is not the LIS.** It is a list of the smallest possible tail for each achievable length, and it happens to be sorted, which is what allows the binary search. The *length* is correct; the contents are generally not a valid subsequence of the input. Claiming otherwise is a common error.

**Why keeping the smallest tail is right:** a smaller tail can be extended by more future elements, and it never hurts. That is an exchange argument (Module 11.2) hiding inside a DP.

For **non-decreasing** subsequences (equal values allowed), use `upper_bound` instead of `lower_bound`.

### The family

| Problem | Reduction |
|---|---|
| LIS (300) | Direct |
| Russian Doll Envelopes (354) | Sort by width ascending, **height descending** for ties, then LIS on heights |
| Longest String Chain (1048) | Sort by length, DP with a hash map on predecessors |
| Maximum Length of Pair Chain (646) | Greedy by end time, or LIS |
| Number of LIS (673) | Track length **and** count per index |

**Russian Doll Envelopes has a genuinely clever trick.** Sorting heights *descending* within equal widths ensures two envelopes of the same width can never both appear in the increasing subsequence, which enforces the strict-width requirement for free.

### Must remember

1. `dp[i]` is the LIS **ending at** `i`. The answer is the max over all `i`.
2. O(n²) DP is fine for n ≤ 2500; use O(n log n) above that.
3. `tails` gives the correct **length** but is not the subsequence itself.
4. `lower_bound` for strictly increasing, `upper_bound` for non-decreasing.
5. Russian Doll: ascending width, **descending** height for ties.
6. "Best ending here" is a reusable state design (see also Kadane).

---

## 13.9 Family 5: grid DP

**Shape:** `dp[i][j]` depends on `dp[i-1][j]` and `dp[i][j-1]`. The simplest family.

### Unique Paths (LC 62)

```cpp
int uniquePaths(int n, int m) {
    vector<int> dp(m, 1);                     // first row: one way to each cell
    for (int i = 1; i < n; i++)
        for (int j = 1; j < m; j++)
            dp[j] += dp[j-1];                 // dp[j] is the row above; dp[j-1] is the left
    return dp[m-1];
}
```

The 1D form works because when you reach `dp[j]`, it still holds row `i-1` and `dp[j-1]` already holds row `i`. That is exactly what the transition needs — the same direction reasoning as Section 13.4.

### Minimum Path Sum (LC 64)

```cpp
int minPathSum(vector<vector<int>>& g) {
    int n = g.size(), m = g[0].size();
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            if (i == 0 && j == 0) continue;
            else if (i == 0) g[i][j] += g[i][j-1];             // top row
            else if (j == 0) g[i][j] += g[i-1][j];             // left column
            else g[i][j] += min(g[i-1][j], g[i][j-1]);
        }
    return g[n-1][m-1];
}
```

Modifying the grid in place gives O(1) extra space. Mention that you are destroying the input.

### Triangle (LC 120)

Work **bottom-up**, which removes all the boundary special cases:

```cpp
int minimumTotal(vector<vector<int>>& t) {
    vector<int> dp = t.back();                 // last row
    for (int i = t.size() - 2; i >= 0; i--)
        for (int j = 0; j <= i; j++)
            dp[j] = t[i][j] + min(dp[j], dp[j+1]);
    return dp[0];
}
```

**Choosing the direction is the design decision here.** Top-down needs edge handling at both ends of each row; bottom-up needs none, because every cell has exactly two children.

### The family

| Problem | Transition |
|---|---|
| Unique Paths (62) | `dp[i-1][j] + dp[i][j-1]` |
| Unique Paths II (63) | Same, with `dp = 0` on obstacles |
| Minimum Path Sum (64) | `g[i][j] + min(up, left)` |
| Triangle (120) | Bottom-up, `min(dp[j], dp[j+1])` |
| Maximal Square (221) | `1 + min(up, left, diagonal)` if the cell is 1 |
| Cherry Pickup (741) | Two simultaneous paths: a 3D state |

**Maximal Square is worth doing** because the `min` of three neighbours plus one is non-obvious and genuinely teaches something about state design.

### Must remember

1. Grid DP is the easiest family; use it to practise the five steps cleanly.
2. 1D rolling works when the transition reads only the previous row and the current-row left neighbour.
3. Obstacles set `dp = 0` and propagate naturally.
4. Bottom-up on Triangle removes all boundary cases.
5. In-place modification gives O(1) extra space but destroys the input.
6. O(n·m) time.

---

## 13.10 Family 6: interval DP

**Shape:** `dp[i][j]` = the answer for the range `[i..j]`, computed by splitting at every interior point.

**The order rule: iterate by interval length**, because `dp[i][j]` depends on strictly shorter intervals.

### Matrix Chain Multiplication

*Given matrix dimensions, find the minimum scalar multiplications to multiply the chain.*

```cpp
int mcm(const vector<int>& p) {                    // p[i-1] x p[i] is matrix i
    int n = p.size() - 1;
    vector<vector<int>> dp(n+2, vector<int>(n+2, 0));

    for (int len = 2; len <= n; len++)             // LENGTH outermost
        for (int i = 1; i + len - 1 <= n; i++) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; k++)            // try every split point
                dp[i][j] = min(dp[i][j],
                               dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]);
        }
    return dp[1][n];
}
```

**Three loops: length, start, split.** The state is O(n²) and the transition is O(n), so the total is **O(n³)** — exactly the "states × transition cost" rule from Module 1.5.

**Why length-first.** `dp[i][j]` reads `dp[i][k]` and `dp[k+1][j]`, both of which are shorter intervals. Iterating `i` and `j` directly would read cells that have not been filled. This is the same discipline as `k`-outermost in Floyd-Warshall (Module 12.13).

### Burst Balloons (LC 312)

*Bursting balloon `i` earns `a[i-1] * a[i] * a[i+1]`. Maximise the total.*

**The reframing is the entire problem.** Thinking "which balloon do I burst first?" fails, because bursting changes the neighbours and the subproblems are not independent.

Instead ask: **"which balloon do I burst LAST in this range?"** If `k` is last in `[i..j]`, then everything in `[i..k-1]` and `[k+1..j]` is already gone, so `k`'s neighbours at that moment are the boundaries `i-1` and `j+1`, which are fixed. The subproblems become independent.

```cpp
int maxCoins(vector<int> a) {
    int n = a.size();
    a.insert(a.begin(), 1);
    a.push_back(1);                                // sentinels
    vector<vector<int>> dp(n+2, vector<int>(n+2, 0));

    for (int len = 1; len <= n; len++)
        for (int i = 1; i + len - 1 <= n; i++) {
            int j = i + len - 1;
            for (int k = i; k <= j; k++)           // k is burst LAST
                dp[i][j] = max(dp[i][j],
                               dp[i][k-1] + a[i-1]*a[k]*a[j+1] + dp[k+1][j]);
        }
    return dp[1][n];
}
```

**"Which one is last" instead of "which one is first" is a reusable interval-DP move.** When the obvious framing creates dependent subproblems, try reversing the order of the decision.

### Palindrome Partitioning II (LC 132)

*Minimum cuts so every piece is a palindrome.*

Precompute `isPal[i][j]` with an interval DP, then a 1D DP over cut positions. Precomputing the palindrome table turns an O(n³) solution into O(n²).

### Must remember

1. Interval DP iterates by **length**, outermost.
2. State O(n²), transition O(n), total **O(n³)**.
3. MCM's cost term is `p[i-1] * p[k] * p[j]`. Derive it rather than memorise.
4. Burst Balloons: think **last**, not first. Add sentinels.
5. Precompute palindrome tables to drop a factor of n.
6. `n ≤ 100–500` in a problem about ranges or splits is the interval-DP constraint signal.

---

## 13.11 Family 7: palindromic DP

### Longest Palindromic Subsequence (LC 516)

**The one-line solution:** `LPS(s) = LCS(s, reverse(s))`. Worth knowing and worth stating.

The direct interval DP:

```cpp
int longestPalindromeSubseq(const string& s) {
    int n = s.size();
    vector<vector<int>> dp(n, vector<int>(n, 0));

    for (int i = 0; i < n; i++) dp[i][i] = 1;          // single characters

    for (int len = 2; len <= n; len++)
        for (int i = 0; i + len - 1 < n; i++) {
            int j = i + len - 1;
            if (s[i] == s[j]) dp[i][j] = 2 + dp[i+1][j-1];
            else              dp[i][j] = max(dp[i+1][j], dp[i][j-1]);
        }
    return dp[0][n-1];
}
```

**Careful with `len == 2`:** when `i+1 > j-1` the inner cell is an empty range, which must read as 0. Sizing the table `n × n` with zero-initialisation handles this, but if you index `dp[i+1][j-1]` with `i+1 > j-1` you are reading a cell below the diagonal, which stays 0. That works here; be aware of why.

### Related

| Problem | Approach |
|---|---|
| Longest Palindromic Substring (5) | **Expand around centre**, O(n²) O(1) space — Module 2.12 |
| Longest Palindromic Subsequence (516) | Interval DP, or LCS with the reverse |
| Palindromic Substrings (647) | Count with expand-around-centre |
| Palindrome Partitioning II (132) | Precomputed `isPal` + 1D cut DP |
| Minimum Insertions for Palindrome (1312) | `n − LPS(s)` |

**Substring problems prefer expand-around-centre; subsequence problems need DP.** That split mirrors the general subarray/subsequence rule from Module 2.3.

---

## 13.12 Family 8: state-machine DP (stocks)

**Shape:** a fixed number of states per day, with defined transitions between them. Once you see this framing, six stock problems collapse into one.

### The general formulation

At each day you are in one of a small set of states: holding, not holding, in cooldown, or "having completed `j` transactions". The DP tracks the best value for each state.

### Unlimited transactions (LC 122)

```cpp
int maxProfit(const vector<int>& p) {
    int hold = INT_MIN, free_ = 0;                  // holding / not holding
    for (int x : p) {
        int prevFree = free_;
        free_ = max(free_, hold + x);               // sell today
        hold  = max(hold, prevFree - x);            // buy today
    }
    return free_;
}
```

(The greedy "sum all positive differences" gives the same answer and is shorter, but the state machine generalises and the greedy does not.)

### At most k transactions (LC 188, and LC 123 with k=2)

```cpp
int maxProfit(int k, const vector<int>& p) {
    int n = p.size();
    if (k >= n / 2) {                               // effectively unlimited
        int profit = 0;
        for (int i = 1; i < n; i++) profit += max(0, p[i] - p[i-1]);
        return profit;
    }

    vector<int> buy(k+1, INT_MIN), sell(k+1, 0);
    for (int x : p)
        for (int j = 1; j <= k; j++) {
            buy[j]  = max(buy[j],  sell[j-1] - x);  // buy the j-th stock
            sell[j] = max(sell[j], buy[j] + x);     // sell it
        }
    return sell[k];
}
```

**The `k >= n/2` shortcut matters.** With n days you can make at most n/2 transactions, so beyond that the constraint is vacuous and you fall back to the unlimited case. Without this, LC 188 with k = 10⁹ allocates an impossible array.

### With cooldown (LC 309)

Three states: holding, just sold (cooling down), resting.

```cpp
int maxProfit(const vector<int>& p) {
    int hold = INT_MIN, sold = 0, rest = 0;
    for (int x : p) {
        int prevSold = sold;
        sold = hold + x;                            // sell today
        hold = max(hold, rest - x);                 // buy today (must have rested)
        rest = max(rest, prevSold);                 // rest today
    }
    return max(sold, rest);
}
```

**`prevSold` is essential.** All three states must be updated from the *previous* day's values simultaneously. Overwriting `sold` before `rest` reads it lets the same day's sale feed into the same day's rest, which breaks the cooldown rule.

### The family

| Problem | States |
|---|---|
| Best Time I (121) | Running minimum (special case) |
| Best Time II (122) | hold / free |
| Best Time III (123) | 4 states (2 transactions) |
| Best Time IV (188) | 2k states |
| With Cooldown (309) | hold / sold / rest |
| With Fee (714) | hold / free, subtract the fee on sale |

### Must remember

1. Identify the states, then write one transition per state.
2. Update all states from the **previous** day's values. Save anything you overwrite.
3. `k >= n/2` reduces to the unlimited case.
4. Initialise "holding" to a true minimum (`INT_MIN`), not 0.
5. Watch for `INT_MIN - price` overflowing. Use `long long` or guard it.
6. State-machine DP appears well beyond stocks: any problem with a small set of modes and defined transitions.

---

## 13.13 Family 9: bitmask DP

**Advanced. Tier 3–4.** Read it, implement one, move on unless you are targeting hard OAs.

### When it applies

The constraint `n ≤ 20` is the signal (Module 1.7). The state includes "which subset of items has been used", encoded as an integer where bit `i` means item `i` is used.

### The TSP shape

```cpp
// dp[mask][i] = minimum cost to have visited exactly `mask`, currently at i
vector<vector<int>> dp(1<<n, vector<int>(n, INF));
dp[1][0] = 0;                                       // start at city 0

for (int mask = 1; mask < (1<<n); mask++)
    for (int i = 0; i < n; i++) {
        if (!(mask & (1<<i))) continue;             // i must be in the mask
        if (dp[mask][i] == INF) continue;
        for (int j = 0; j < n; j++) {
            if (mask & (1<<j)) continue;            // j already visited
            int next = mask | (1<<j);
            dp[next][j] = min(dp[next][j], dp[mask][i] + cost[i][j]);
        }
    }
```

O(2ⁿ · n²) time, O(2ⁿ · n) space. At n = 20 that is about 4 × 10⁸ — borderline but feasible.

### The bit operations (Module 14 covers these properly)

```cpp
mask & (1 << i)          // is bit i set?
mask | (1 << i)          // set bit i
mask & ~(1 << i)         // clear bit i
__builtin_popcount(mask) // count set bits
```

### Where it shows up

Assignment problems ("assign n tasks to n workers"), TSP, "minimum number of groups", counting Hamiltonian paths, and some scheduling problems. **Low placement priority** except at companies with genuinely hard online assessments.

---

# PART C — Consolidation

## 13.14 The DP pattern recognition guide

**The deliverable of this module.** Given an unfamiliar problem, this table should get you to a state definition.

| Signal in the statement | Family | State shape | Typical complexity |
|---|---|---|---|
| "ways to reach step/position n" | 1D linear | `dp[i]` | O(n) |
| "no two adjacent" | 1D linear | `dp[i]` | O(n) |
| "decode / parse the string" | 1D linear | `dp[i]` | O(n) |
| "subset summing to target", "partition" | 0/1 knapsack | `dp[i][target]` | O(n·T) |
| "each item at most once" + capacity | 0/1 knapsack | `dp[i][w]` | O(n·W) |
| "unlimited copies", "coins", "rod cutting" | Unbounded knapsack | `dp[w]` | O(n·W) |
| "minimum number of X to reach a total" | Unbounded knapsack | `dp[amount]` | O(n·A) |
| "number of ways to make an amount" | Unbounded, counting | `dp[amount]` | O(n·A) |
| Two strings, "common", "transform", "match" | Two-string | `dp[i][j]` | O(n·m) |
| "edit / insert / delete / replace" | Two-string | `dp[i][j]` | O(n·m) |
| "longest increasing subsequence" | LIS | `dp[i]` ending at i | O(n²) or O(n log n) |
| "paths in a grid", "minimum path" | Grid | `dp[i][j]` | O(n·m) |
| "split the range", "merge the piles", "burst" | Interval | `dp[i][j]` | O(n³) |
| "palindromic subsequence" | Interval / LCS | `dp[i][j]` | O(n²) |
| "buy and sell", "at most k transactions" | State machine | states per day | O(n·k) |
| n ≤ 20, "which subset is used" | Bitmask | `dp[mask][i]` | O(2ⁿ·n²) |
| Tree structure, "for each subtree" | Tree DP | `dp[node][state]` | O(n) |

### The constraint-to-family shortcut

| Constraint | Suggests |
|---|---|
| n ≤ 20 | Bitmask DP |
| n ≤ 100–500 | Interval DP, O(n³) |
| n ≤ 10³–5×10³ | Two-string or O(n²) DP |
| n ≤ 10⁵ with a small target | Knapsack, O(n·T) |
| n ≤ 10⁵, no second dimension | 1D linear DP, or greedy |
| n ≤ 10⁶ | O(n) DP with O(1) space, or not DP at all |

### The state-design checklist

When stuck, ask in order:

1. **What varies between subproblems?** Every varying quantity is a candidate state dimension.
2. **What decision am I making at each step?** That is the transition.
3. **Is my state sufficient?** Could two situations share these values and need different answers? If yes, add a dimension.
4. **Is my state minimal?** Could I drop one and still be correct?
5. **What is states × transition cost?** Does it fit the constraints?

If step 5 fails, the state is wrong. Redesign before coding.

---

## 13.15 Must remember (consolidated)

1. DP needs overlapping subproblems **and** optimal substructure.
2. Complexity = **states × transition cost**. Know it before you code.
3. Write the state as an English sentence first.
4. Recursion → memoise → tabulate is the interview-safe order.
5. Base cases first. A wrong base case corrupts everything silently.
6. **Backward loop = 0/1 knapsack. Forward loop = unbounded.**
7. **Coin loop outside = combinations. Amount loop outside = permutations.**
8. `dp[0]` is `0` for minimisation, `1` for counting, `true` for feasibility.
9. LCS takes `max` on mismatch; longest common **substring** resets to 0.
10. Edit Distance base cases are `i` and `j`, not 0.
11. LIS `dp[i]` is the LIS **ending at** `i`; the answer is the maximum over all `i`.
12. The O(n log n) LIS `tails` array gives the length, not the subsequence.
13. Interval DP iterates by **length**, outermost.
14. Burst Balloons: decide which balloon is burst **last**.
15. State-machine DP updates all states from the **previous** step's values.
16. `k >= n/2` collapses the k-transaction stock problem to unlimited.
17. Space optimisation destroys the ability to reconstruct the solution.
18. Target Sum reduces to counting subsets with `P = (sum + target)/2`.
19. Guard minimisation DPs against `INF + 1`.
20. n ≤ 20 means bitmask; n ≤ 100 means interval; n ≤ 10³ means O(n²).

---

## 13.16 Common mistakes (consolidated)

**Wrong answer**
- Wrong loop **direction**, turning 0/1 into unbounded.
- Wrong loop **order**, counting permutations instead of combinations.
- Edit Distance base cases initialised to 0.
- `max` instead of reset in longest common substring.
- Returning `dp[n-1]` for LIS instead of the maximum.
- Overwriting a state before another transition reads it (stock cooldown).
- State missing a dimension, so two different situations collide.
- `dp[0] = 0` in a counting problem where it should be 1.
- Forgetting the parity guard in Target Sum.

**Time limit exceeded**
- Naive recursion with no memoisation.
- A state with a redundant dimension, multiplying the work.
- Not precomputing (for example, palindrome checks inside the DP loop).
- O(n²) LIS when n = 10⁵.

**Runtime error / overflow**
- `INT_MIN - price` overflowing in stock DP.
- `INF + 1` in minimisation.
- Array indexing off by one between the 1-indexed table and 0-indexed strings.
- Stack overflow from deep memoised recursion.
- Allocating a `k`-dimension array when `k` is 10⁹.

**Analysis errors**
- Reporting the naive recursion's complexity for the memoised version.
- Forgetting the transition cost (interval DP is O(n³), not O(n²)).
- Claiming O(1) space for a memoised solution (the stack is O(depth)).

---

## 13.17 Problem set

Thirty problems, grouped by family. **Do them family by family, not level by level** — the point is to see each family's shape repeat.

### Family 1 — Linear 1D (5)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Climbing Stairs (LC 70) | Easy | The five steps, cleanly |
| Min Cost Climbing Stairs (LC 746) | Easy | Base cases with two valid starts |
| House Robber (LC 198) | Medium | The take/skip transition |
| House Robber II (LC 213) | Medium | Circular → two linear runs |
| Decode Ways (LC 91) | Medium | Zeros as the whole difficulty |

### Family 2 — Knapsack (7)

| Problem | Difficulty | What it teaches |
|---|---|---|
| 0/1 Knapsack (GFG) | Medium | The 2D form, then the backward 1D |
| Subset Sum (GFG) | Medium | Feasibility instead of value |
| Partition Equal Subset Sum (LC 416) | Medium | The odd-sum early exit |
| **Target Sum (LC 494)** | Medium | The `(sum+target)/2` reduction |
| Coin Change (LC 322) | Medium | Unbounded, forward loop, INF guard |
| **Coin Change II (LC 518)** | Medium | Combinations: coin loop outside |
| Combination Sum IV (LC 377) | Medium | Permutations: amount loop outside |

**Do LC 518 and LC 377 back to back.** They are the same recurrence with the loops swapped, and solving them consecutively is the fastest way to make the distinction permanent.

### Family 3 — Two strings (5)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Longest Common Subsequence (LC 1143) | Medium | The family's skeleton |
| Longest Common Substring (GFG) | Medium | The one-line difference: reset vs max |
| **Edit Distance (LC 72)** | Medium | Non-zero base cases; three operations |
| Distinct Subsequences (LC 115) | Hard | Counting instead of optimising |
| Delete Operation for Two Strings (LC 583) | Medium | Reduces to `n + m − 2·LCS` |

### Family 4 — LIS (3)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Longest Increasing Subsequence (LC 300) | Medium | Both the O(n²) and O(n log n) methods |
| Russian Doll Envelopes (LC 354) | Hard | The descending-height tiebreak |
| Longest String Chain (LC 1048) | Medium | LIS over a hash map |

### Family 5 — Grid (4)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Unique Paths (LC 62) | Medium | The 1D rolling form |
| Unique Paths II (LC 63) | Medium | Obstacles propagating zeros |
| Minimum Path Sum (LC 64) | Medium | In-place, O(1) extra |
| Maximal Square (LC 221) | Medium | `1 + min` of three neighbours |

### Family 6 — Interval (3)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Matrix Chain Multiplication (GFG) | Hard | Length-first iteration; O(n³) |
| **Burst Balloons (LC 312)** | Hard | Think **last**, not first |
| Palindrome Partitioning II (LC 132) | Hard | Precompute to drop a factor of n |

### Family 7 — Palindromic (2)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Longest Palindromic Subsequence (LC 516) | Medium | Interval DP, or LCS with the reverse |
| Palindromic Substrings (LC 647) | Medium | Expand-around-centre beats DP here |

### Family 8 — Stock / state machine (4)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Best Time to Buy and Sell Stock II (LC 122) | Medium | Two states |
| Best Time III (LC 123) | Hard | Four states |
| **Best Time with Cooldown (LC 309)** | Medium | Three states; the `prevSold` trap |
| Best Time IV (LC 188) | Hard | k states; the `k >= n/2` shortcut |

### Optional — Bitmask (2)

| Problem | Difficulty | What it teaches |
|---|---|---|
| Travelling Salesman (GFG) | Hard | The `dp[mask][i]` shape |
| Partition to K Equal Sum Subsets (LC 698) | Medium | Bitmask over subsets |

**For every problem, write the five steps in a comment before writing code.** By problem fifteen it will be internalised; until then, writing it down is what converts the framework from something you read into something you use.

---

## Exit checklist

```
[ ] I can state the two conditions DP requires
[ ] I know complexity = states x transition cost
[ ] I write the state as an English sentence before coding
[ ] I can walk through all five steps out loud
[ ] I write the naive recursion first, then memoise, then tabulate
[ ] I know when memoisation beats tabulation and vice versa
[ ] I can space-optimise a 2D DP to 1D
[ ] I know BACKWARD = 0/1 and FORWARD = unbounded
[ ] I know coin-outer = combinations, amount-outer = permutations
[ ] I can write 0/1 knapsack in both 2D and 1D from memory
[ ] I can derive the Target Sum reduction
[ ] I can write LCS and Edit Distance from memory
[ ] I know the substring-vs-subsequence one-line difference
[ ] I know Edit Distance base cases are i and j, not 0
[ ] I can write LIS both ways and know tails isn't the subsequence
[ ] I know interval DP iterates by length
[ ] I can explain the "burst last" reframing
[ ] I can write the stock state machine and know why prevSold matters
[ ] I can pick a DP family from the constraints alone
[ ] I can derive a recurrence for a problem I have never seen
[ ] At least 20 of the 30 problems solved
```

That second-to-last box is the one that matters. Everything else is scaffolding for it.

---

## Next

Two short modules remain, and either order works.

Say **"Start Phase 14"** for Bit Manipulation (4–5 hours, Tier 2). It is the side module from the roadmap: small, self-contained, and it closes out the bitmask machinery this module just used. XOR tricks, the set-bit operations, and a compact cheat sheet.

Or say **"Start Phase 15"** for Trie (5–6 hours, Tier 3), which is a short module now that trees are done — a trie is a tree with 26 children, and the interesting part is knowing when it beats a hash map.

After both, the roadmap's Phase 15 (advanced topics, priority-classified) and the ten final cheat sheets are all that remain.
