# DSA Placement Handbook (C++) — Part 10
# Phase 8: Backtracking

**Module 8 · 10–12 hours · Tier 2 · Requires: Modules 0, 1, 4**

---

## What this module adds to recursion

Module 4 ended with a preview: the difference between passing the partial result by value (automatic undo, but a copy at every node) and passing it by reference with an explicit undo. That undo line is backtracking, and this module is built on it.

The reason it deserves twelve hours despite being "just recursion" is that three specific things go wrong and none of them are obvious:

**Duplicate handling.** Combination Sum II and Permutations II look like small variations on problems you already solved. They are not, and the skip conditions are genuinely subtle. Section 8.6 exists entirely for this.

**Pruning.** An unpruned backtracking solution is often correct and still times out. Knowing where to cut is what separates an accepted solution from a TLE, and it is the part interviewers probe.

**Two different goals.** "Find all solutions" and "find one solution" produce different code shapes (void versus bool, explore everything versus return early). Mixing them up produces solutions that work but are exponentially slower than needed.

**Tier 2 note:** subsets, permutations, and combination sum are asked regularly and you should know them cold. N-Queens and Sudoku are asked less often, mostly at product companies, and mostly as "do you recognise the shape". If you are short on time, do Sections 8.1 through 8.7 thoroughly and treat 8.8 and 8.9 as read-only.

---

## 8.1 Recursion vs backtracking

### 1. What is it?

Backtracking is recursion that **explores a tree of choices**, undoing each choice before trying the next, and abandoning branches that cannot lead to a valid answer.

### 2. The distinction

Every backtracking algorithm is recursive. Not every recursion is backtracking.

| | Recursion | Backtracking |
|---|---|---|
| Goal | Compute one value | Enumerate or find configurations |
| Shape | `return combine(f(smaller))` | `choose → explore → un-choose` |
| State | Returned upward, or copied down | Shared, mutated, restored |
| Explores | One path | A tree of paths |
| Abandons branches | No | Yes, via pruning |
| Typical output | A number | A list of solutions, or a boolean |
| Examples | Factorial, tree height, merge sort | Subsets, N-Queens, Sudoku |

**The one-line version:** backtracking is recursion with an undo.

### 3. Why the undo exists

You maintain one shared buffer representing the current partial solution. Before recursing you add a choice to it; after the recursive call returns, that entire subtree has been explored, so the choice must be removed before you try a different one.

```cpp
cur.push_back(x);        // CHOOSE:   cur now represents "we picked x"
backtrack(...);          // EXPLORE:  every completion with x picked
cur.pop_back();          // UNCHOOSE: cur is restored for the next sibling
```

If you forget the `pop_back`, the next branch inherits choices from the previous one and every answer after the first is wrong.

### 4. Why not just copy?

```cpp
// Flavour A: copy, automatic undo
backtrack(i + 1, cur);                        // cur passed BY VALUE
backtrack(i + 1, cur_with_x_appended);

// Flavour B: mutate, manual undo
cur.push_back(x); backtrack(i + 1, cur); cur.pop_back();   // cur BY REFERENCE
```

Both are correct. Flavour A copies the partial solution at every node, costing O(n) per node and O(n) extra space per level. Flavour B mutates one buffer, O(1) per node.

At 2ⁿ nodes the difference is real. **Use flavour B.** Flavour A is worth knowing because it explains what the undo is compensating for.

### 5. Must remember

1. Backtracking = recursion + undo.
2. The undo restores the state for **sibling** branches, not for the parent.
3. Shared state must be passed by **reference**, or nothing propagates and nothing needs undoing.
4. The undo must exactly mirror the choose. Push/pop, set true/set false, place/remove.
5. Copying the partial solution is correct but costs a factor of n.

---

## 8.2 The universal template

Every problem in this module is this shape:

```cpp
void backtrack(/* current state */) {
    if (isComplete(state)) {
        result.push_back(current);        // record a full solution
        return;
    }

    for (each candidate choice) {
        if (!isValid(choice)) continue;   // PRUNE: skip impossible branches

        make(choice);                     // CHOOSE
        backtrack(/* advanced state */);  // EXPLORE
        undo(choice);                     // UNCHOOSE
    }
}
```

### The five questions

Before writing any backtracking solution, answer these. It takes thirty seconds and prevents most of the bugs.

1. **What is a complete solution?** This is the base case.
2. **What are the choices at each step?** This is the loop.
3. **What makes a choice invalid?** This is the pruning.
4. **What state changes when I make a choice?** This is what you must undo.
5. **Am I finding all solutions, or just one?** This decides `void` versus `bool`.

### All solutions vs one solution

These produce different code, and using the wrong one costs you exponentially.

```cpp
// ALL solutions: void, explore everything
void backtrack(...) {
    if (complete) { res.push_back(cur); return; }
    for (choice : choices) {
        make(choice);
        backtrack(...);
        undo(choice);
    }
}

// ONE solution: bool, return early
bool backtrack(...) {
    if (complete) return true;
    for (choice : choices) {
        if (!valid(choice)) continue;
        make(choice);
        if (backtrack(...)) return true;    // SHORT-CIRCUIT: stop everything
        undo(choice);
    }
    return false;                            // no choice worked: dead end
}
```

Subsets, permutations, and N-Queens (all boards) use the first. Sudoku, Word Search, and Rat-in-a-Maze (any path) use the second. **Sudoku written with the `void` shape explores every solvable arrangement instead of stopping at the first, which is the difference between instant and never.**

---

## 8.3 Subsets

### 1. What is it?

Generate all 2ⁿ subsets of a set. The foundational problem of the module.

### 2. Why do we need it?

Every other backtracking problem is a constrained version of this. Combinations are subsets of a fixed size. Combination Sum is subsets with a target. Permutations are subsets with ordering. Learn the two formulations here and the rest are small edits.

### 3. Formulation A: pick / not-pick

```cpp
void solve(int i, const vector<int>& nums, vector<int>& cur, vector<vector<int>>& res) {
    if (i == (int)nums.size()) {           // decided on every element
        res.push_back(cur);
        return;
    }

    solve(i + 1, nums, cur, res);          // NOT pick nums[i]

    cur.push_back(nums[i]);                // CHOOSE
    solve(i + 1, nums, cur, res);          // EXPLORE
    cur.pop_back();                        // UNCHOOSE
}
```

Binary decision at every index. The recursion tree is a perfect binary tree of depth n with 2ⁿ leaves, one per subset.

```
                    []
           /                  \
      skip 1                pick 1
     /      \              /       \
  skip 2   pick 2      skip 2     pick 2
   []       [2]         [1]       [1,2]
```

### 4. Formulation B: the loop form

```cpp
void solve(int start, const vector<int>& nums, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);                    // EVERY node is a valid subset

    for (int i = start; i < (int)nums.size(); i++) {
        cur.push_back(nums[i]);            // CHOOSE
        solve(i + 1, nums, cur, res);      // EXPLORE (i+1: no reuse)
        cur.pop_back();                    // UNCHOOSE
    }
}
```

Here every node of the recursion tree is itself an answer, so you record on entry rather than at the leaves.

### 5. Which formulation to use

| | Pick / not-pick | Loop form |
|---|---|---|
| Reads like | A binary decision per element | "Pick the next element from those remaining" |
| Extends to combinations | Awkwardly | **Naturally** (`cur.size() == k`) |
| Extends to combination sum | Awkwardly | **Naturally** (`i` vs `i+1` controls reuse) |
| Duplicate handling | Harder | **Natural** (`i > start` skip) |
| Best for | Understanding the 2ⁿ structure | Everything else in this module |

**Learn both, default to the loop form.** It is the one that generalises to combinations, combination sum, palindrome partitioning, and the duplicate variants. The pick/not-pick form is the better mental model for *why* there are 2ⁿ subsets, and it is the one that maps directly onto knapsack DP in Module 13.

### 6. The `start` parameter

The single most important idea in the loop form.

`start` means **"only consider elements from index `start` onward"**. It is what prevents `[1,2]` and `[2,1]` from both appearing, which is exactly the difference between a subset and a permutation.

| Recursive call | Meaning |
|---|---|
| `solve(i + 1, ...)` | Each element used **at most once**; no reuse |
| `solve(i, ...)` | Each element may be **reused** (Combination Sum) |
| No `start` at all, loop from 0 | **Permutations**: order matters, every element available at every level |

That three-row table explains the structural difference between the three biggest problems in this module.

### 7. Complexity

| | |
|---|---|
| Time | O(2ⁿ · n) — 2ⁿ subsets, each copied in O(n) |
| Space | O(n) recursion depth, plus O(2ⁿ · n) for the output |

The `· n` factor comes from `res.push_back(cur)`, which copies. People report O(2ⁿ) and get corrected.

### 8. Must remember

1. `res.push_back(cur)` copies, which is the `· n` in the complexity.
2. In the loop form you record at **every** node, not just at leaves.
3. `solve(i + 1)` prevents reuse; `solve(i)` permits it.
4. Subsets are order-independent, which is why `start` exists.
5. 2ⁿ subsets means n ≤ 20 or so (Module 1's constraint table). If n is larger, backtracking is not the intended solution.

### 9. Common mistakes

- Forgetting `cur.pop_back()`, contaminating sibling branches.
- Using `solve(start + 1)` instead of `solve(i + 1)`, which re-explores the same elements.
- Recording only at leaves in the loop form, missing most subsets.
- Reporting O(2ⁿ) instead of O(2ⁿ · n).

### 10. Practice

- Subsets (LC 78, Medium) — write both formulations
- Letter Combinations of a Phone Number (LC 17, Medium) — the same shape with a per-digit choice set

---

## 8.4 Permutations

### 1. What is it?

Generate all n! orderings of a set.

### 2. Core idea

The structural difference from subsets: **order matters, so there is no `start` index.** At every level, every unused element is a candidate. You need a `used[]` array to track which ones are already in the current arrangement.

### 3. Template A: the `used` array

```cpp
void solve(const vector<int>& nums, vector<int>& cur,
           vector<bool>& used, vector<vector<int>>& res) {
    if (cur.size() == nums.size()) {
        res.push_back(cur);
        return;
    }

    for (int i = 0; i < (int)nums.size(); i++) {    // from 0 EVERY time
        if (used[i]) continue;

        used[i] = true;                              // CHOOSE
        cur.push_back(nums[i]);

        solve(nums, cur, used, res);                 // EXPLORE

        cur.pop_back();                              // UNCHOOSE
        used[i] = false;                             // BOTH parts of the undo
    }
}
```

**Two things are chosen, so two things must be undone.** Forgetting `used[i] = false` means elements get permanently consumed and you produce a fraction of the permutations. This is the signature bug of this problem.

### 4. Template B: the swap method

```cpp
void solve(int idx, vector<int>& nums, vector<vector<int>>& res) {
    if (idx == (int)nums.size()) {
        res.push_back(nums);
        return;
    }

    for (int i = idx; i < (int)nums.size(); i++) {
        swap(nums[idx], nums[i]);          // CHOOSE: put nums[i] at position idx
        solve(idx + 1, nums, res);         // EXPLORE
        swap(nums[idx], nums[i]);          // UNCHOOSE
    }
}
```

No `used` array and no `cur` buffer: the array itself is the state. O(1) extra space beyond the output and the stack.

Trade-offs: it does not produce lexicographic order, and duplicate handling is harder (you need a per-level `set` of already-tried values rather than the sort-and-skip trick). **Use Template A by default.**

### 5. Complexity

| | |
|---|---|
| Time | O(n! · n) — n! permutations, each copied in O(n) |
| Space | O(n) for depth and `used`, plus the output |

n! grows brutally: 10! is 3.6 million, 12! is 479 million. **n ≤ 10 or so**, which matches Module 1's constraint table.

### 6. Must remember

1. Permutations have **no `start` index**; the loop runs from 0 every level.
2. The `used[]` array is what prevents reuse, and it needs an undo too.
3. Base case is `cur.size() == nums.size()`, not an index reaching the end.
4. The swap method is O(1) space but loses lexicographic order.
5. `next_permutation` from `<algorithm>` generates permutations iteratively in lexicographic order. Valid, but interviewers usually want the recursion.
6. n! means n ≤ 10. If the constraint is larger, this is not the intended solution.

### 7. Common mistakes

- Forgetting `used[i] = false` in the undo.
- Adding a `start` parameter, producing combinations instead of permutations.
- Undoing only one of the two state changes.
- Using the swap method and then struggling with duplicates.

### 8. Practice

- Permutations (LC 46, Medium)
- Permutations II (LC 47, Medium) — after Section 8.6

---

## 8.5 Combinations and Combination Sum

### Combinations (LC 77): choose k from 1..n

The loop form with a size-based base case:

```cpp
void solve(int start, int n, int k, vector<int>& cur, vector<vector<int>>& res) {
    if ((int)cur.size() == k) {
        res.push_back(cur);
        return;
    }

    for (int i = start; i <= n; i++) {
        cur.push_back(i);
        solve(i + 1, n, k, cur, res);
        cur.pop_back();
    }
}
```

**With pruning** (Section 8.7 covers why this matters):

```cpp
int need = k - cur.size();
for (int i = start; i <= n - need + 1; i++) { ... }
```

If fewer than `need` numbers remain, the branch cannot possibly complete. Stopping early prunes a large fraction of the tree for free.

### Combination Sum (LC 39): unlimited reuse

*Given distinct candidates and a target, find all combinations summing to the target. Each candidate may be used unlimited times.*

```cpp
void solve(int start, const vector<int>& cand, int target,
           vector<int>& cur, vector<vector<int>>& res) {
    if (target == 0) { res.push_back(cur); return; }

    for (int i = start; i < (int)cand.size(); i++) {
        if (cand[i] > target) break;            // PRUNE (requires sorted input)

        cur.push_back(cand[i]);
        solve(i, cand, target - cand[i], cur, res);   // i, NOT i+1: reuse allowed
        cur.pop_back();
    }
}
// caller: sort(cand.begin(), cand.end());
```

**`solve(i, ...)` instead of `solve(i + 1, ...)` is the entire problem.** Passing `i` lets the same candidate be chosen again at the next level; passing `i + 1` moves on permanently. One character.

The `break` (not `continue`) works because the array is sorted: if `cand[i]` already exceeds the target, so does everything after it.

### Combination Sum II (LC 40): each used once, duplicates in input

```cpp
void solve(int start, const vector<int>& cand, int target,
           vector<int>& cur, vector<vector<int>>& res) {
    if (target == 0) { res.push_back(cur); return; }

    for (int i = start; i < (int)cand.size(); i++) {
        if (i > start && cand[i] == cand[i - 1]) continue;   // skip duplicates
        if (cand[i] > target) break;

        cur.push_back(cand[i]);
        solve(i + 1, cand, target - cand[i], cur, res);      // i+1: no reuse
        cur.pop_back();
    }
}
```

Two changes from LC 39: `i + 1` for no reuse, and the duplicate skip. Section 8.6 explains why the skip condition is `i > start`.

### The comparison that makes it click

| Problem | Recursive call | Duplicate skip | Base case |
|---|---|---|---|
| Subsets | `solve(i + 1)` | none | `i == n` (record everywhere) |
| Subsets II | `solve(i + 1)` | `i > start && a[i]==a[i-1]` | record everywhere |
| Combinations | `solve(i + 1)` | none | `cur.size() == k` |
| Combination Sum | **`solve(i)`** | none (distinct input) | `target == 0` |
| Combination Sum II | `solve(i + 1)` | `i > start && a[i]==a[i-1]` | `target == 0` |
| Permutations | no `start`, loop from 0 | none | `cur.size() == n` |
| Permutations II | no `start`, loop from 0 | `i>0 && a[i]==a[i-1] && !used[i-1]` | `cur.size() == n` |

**This table is the module.** Seven problems, one template, three independent knobs: the recursive index, the duplicate rule, and the base case. Memorising the table is far more useful than memorising seven solutions.

### Must remember

1. `solve(i)` allows reuse; `solve(i + 1)` does not. This is the Combination Sum I versus II difference.
2. Sort the candidates so `break` (rather than `continue`) is valid as a prune.
3. Combinations prune with `i <= n - (k - cur.size()) + 1`.
4. Combination Sum has no upper bound on the number of picks, so the tree depth is `target / min(cand)`, not n.
5. Watch for `target` going negative when candidates are not sorted or the prune is missing.

---

## 8.6 Duplicate handling

**The section that causes the most wrong answers.** The rules look arbitrary until you see the tree.

### The universal prerequisite: sort first

Duplicate skipping relies on identical elements being adjacent. **Sort the input before starting.** Without that, no skip condition works.

### Rule 1: subsets and combinations — `i > start`

```cpp
if (i > start && nums[i] == nums[i - 1]) continue;
```

**Why `i > start` and not `i > 0`.** Consider `nums = [1, 2, 2]`:

```
At the top level (start = 0), the loop tries i = 0, 1, 2:
    i=1 picks the first 2   -> explores [2], [2,2]
    i=2 picks the second 2  -> would explore [2], [2,2] AGAIN   <- skip this

One level down, inside the branch that picked the first 2 (start = 2):
    i=2 picks the second 2  -> gives [2,2]                      <- MUST ALLOW
```

The same value at the **same level** is a duplicate branch. The same value at a **deeper level** is a legitimate second use of a different element.

`i > start` distinguishes exactly these two cases: `i == start` is the first candidate at this level (always allowed), `i > start` means we have already tried a sibling at this level.

Using `i > 0` forbids the deeper use and you lose `[2,2]` entirely. Using no condition produces `[2]` twice.

### Rule 2: permutations — `!used[i-1]`

```cpp
if (used[i]) continue;
if (i > 0 && nums[i] == nums[i - 1] && !used[i - 1]) continue;
```

Permutations have no `start`, so Rule 1 does not apply. Instead you enforce a **canonical order among identical elements**: the second `2` may only be used if the first `2` is already in the current arrangement.

`!used[i-1]` means the identical predecessor is *not* currently in use, which means we are starting a fresh branch with a duplicate value at this level. Skip it.

If `used[i-1]` is true, we are deeper inside a branch that already placed the first `2`, and placing the second one is legitimate.

The condition looks backwards the first time you read it. Trace `[1,1,2]` by hand once; it is the fastest way to make it stick.

### The two rules side by side

| | Subsets / Combinations | Permutations |
|---|---|---|
| Prerequisite | sorted | sorted |
| Skip condition | `i > start && a[i]==a[i-1]` | `i > 0 && a[i]==a[i-1] && !used[i-1]` |
| Prevents | Same value twice at the same level | Identical elements used out of canonical order |
| Wrong version | `i > 0` — loses legitimate repeats | `used[i-1]` — produces duplicates |

### The lazy alternative, and why not to use it

You can deduplicate afterwards with a `set<vector<int>>`. It works and it is a legitimate fallback if you are stuck in an interview. But it costs O(log) per insertion on top of already-exponential work, and it signals that you did not see the structural fix. Offer it only after saying "the cleaner way is to skip duplicates during generation, like this".

### Must remember

1. **Sort first.** Every skip rule depends on it.
2. Subsets and combinations: `i > start`, never `i > 0`.
3. Permutations: `!used[i-1]`, and the `used[i]` check is separate and comes first.
4. Same value at the same level is a duplicate branch; same value deeper is a legitimate second element.
5. Deduplicating with a set afterwards is a fallback, not the answer.

### Practice

Do these three consecutively. They are the same lesson three times.

- Subsets II (LC 90, Medium)
- Combination Sum II (LC 40, Medium)
- Permutations II (LC 47, Medium)

---

## 8.7 Pruning

### 1. What is it?

Abandoning a branch as soon as you can prove it cannot produce a valid solution.

### 2. Why do we need it?

Because an unpruned backtracking solution is frequently **correct and too slow**. The search tree is exponential; pruning cuts entire subtrees. In N-Queens and Sudoku it is the difference between milliseconds and never finishing.

This is also the part interviewers probe. "Your solution works, can you make it faster?" on a backtracking problem almost always means "where can you prune?"

### 3. The five kinds

**Feasibility pruning.** The current partial solution already violates a constraint.

```cpp
if (cand[i] > target) break;         // remaining sum can only overshoot
```

**Bound pruning.** Not enough candidates remain to complete a solution.

```cpp
for (int i = start; i <= n - (k - cur.size()) + 1; i++)   // Combinations
```

**Constraint propagation.** Maintain data structures that make validity checks O(1) instead of O(n).

```cpp
if (col[c] || diag1[r + c] || diag2[r - c + n - 1]) continue;   // N-Queens
```

**Duplicate pruning.** Section 8.6. Skipping duplicate branches is pruning.

**Ordering.** Sorting the candidates enables `break` instead of `continue`, which prunes all remaining siblings rather than one.

### 4. `break` vs `continue`

A small distinction with a large effect.

```cpp
if (cand[i] > target) continue;      // skip THIS candidate
if (cand[i] > target) break;         // skip this and ALL remaining
```

`break` is only valid on sorted input, where everything after `cand[i]` is also too large. When it applies it is strictly better: it prunes the rest of the level instead of one node.

### 5. Where pruning matters most

| Problem | Without pruning | With pruning |
|---|---|---|
| Combination Sum | Explores far past the target | Cuts as soon as the sum overshoots |
| Combinations | Builds branches that can never reach size k | Stops when too few candidates remain |
| N-Queens | O(n) safety check per cell | O(1) with three boolean arrays |
| Sudoku | Effectively unsolvable | Solves in milliseconds |
| Word Search | Explores every path | Fails immediately on a character mismatch |

### 6. Must remember

1. Prune as **early** as possible. A check before the recursive call beats one at the top of the callee.
2. Sort to enable `break`. It converts one-node pruning into whole-level pruning.
3. Constraint propagation (keeping O(1)-checkable state) is the highest-value prune in constraint problems.
4. Pruning does not change the worst-case complexity; it changes the practical runtime, often by orders of magnitude. Be honest about that distinction when asked.
5. "Can you make it faster?" on a backtracking problem means "where can you prune?"

### 7. Common mistakes

- Checking validity after recursing instead of before.
- Using `continue` where `break` was valid.
- Forgetting to sort, making the `break` prune incorrect.
- Recomputing an O(n) validity check at every node instead of maintaining O(1) state.

---

## 8.8 Grid backtracking

### Word Search (LC 79)

*Does a word exist in a grid, formed by adjacent cells without reusing a cell?*

```cpp
bool dfs(vector<vector<char>>& g, const string& w, int r, int c, int k) {
    if (k == (int)w.size()) return true;                       // matched everything
    if (r < 0 || r >= (int)g.size() || c < 0 || c >= (int)g[0].size()) return false;
    if (g[r][c] != w[k]) return false;                         // PRUNE immediately

    char saved = g[r][c];
    g[r][c] = '#';                                             // CHOOSE: mark visited

    bool found = dfs(g, w, r + 1, c, k + 1) || dfs(g, w, r - 1, c, k + 1)
              || dfs(g, w, r, c + 1, k + 1) || dfs(g, w, r, c - 1, k + 1);

    g[r][c] = saved;                                           // UNCHOOSE: restore
    return found;
}

bool exist(vector<vector<char>>& g, const string& word) {
    for (int r = 0; r < (int)g.size(); r++)
        for (int c = 0; c < (int)g[0].size(); c++)
            if (dfs(g, word, r, c, 0)) return true;
    return false;
}
```

Three things worth noting:

**In-place marking.** Overwriting the cell with `'#'` and restoring it afterwards replaces a separate `visited` grid. It is the same choose/unchoose discipline applied to the input.

**Bounds check before the character check.** Reversing them reads out of bounds.

**The `||` short-circuits**, so as soon as one direction succeeds the others are not explored. This is the "find one solution" shape from 8.2.

Complexity: O(m · n · 4^L) where L is the word length, since each of m·n starting cells branches four ways to depth L. In practice the character mismatch prunes almost everything immediately.

### Rat in a Maze (GeeksforGeeks)

*Find all paths from top-left to bottom-right in a grid with blocked cells, moving in allowed directions.*

Same shape, but collecting **all** paths rather than returning on the first:

```cpp
void solve(vector<vector<int>>& g, int r, int c, string& path,
           vector<string>& res, vector<vector<bool>>& vis) {
    int n = g.size();
    if (r == n - 1 && c == n - 1) { res.push_back(path); return; }

    const int dr[] = {1, 0, 0, -1};
    const char dch[] = {'D', 'L', 'R', 'U'};
    const int dc[] = {0, -1, 1, 0};

    for (int d = 0; d < 4; d++) {
        int nr = r + dr[d], nc = c + dc[d];
        if (nr < 0 || nr >= n || nc < 0 || nc >= n) continue;
        if (vis[nr][nc] || g[nr][nc] == 0) continue;

        vis[nr][nc] = true;                      // CHOOSE
        path.push_back(dch[d]);
        solve(g, nr, nc, path, res, vis);        // EXPLORE
        path.pop_back();                         // UNCHOOSE
        vis[nr][nc] = false;
    }
}
```

The direction arrays are ordered `D, L, R, U` because the standard version of this problem wants paths in lexicographic order.

Note that a `visited` array is necessary here and **must be undone**, unlike in a plain graph DFS (Module 12) where visited is never reset. That difference is worth holding onto: **graph traversal marks permanently; backtracking marks temporarily.**

### Must remember

1. Bounds check before accessing the cell, always.
2. In-place marking (overwrite and restore) avoids a separate visited array.
3. Backtracking un-marks visited cells; graph DFS does not. Mixing them up gives wrong answers in both directions.
4. `||` short-circuiting gives you the early return for free in "find one path" problems.
5. The direction arrays `dr[]` / `dc[]` are the same idiom from Module 2.11 and reappear throughout Module 12.

---

## 8.9 Constraint satisfaction

### N-Queens (LC 51)

*Place n queens on an n×n board so none attack each other.*

**The first insight** reduces the search space enormously: exactly one queen per row. So instead of choosing n cells from n², you choose one column per row. The recursion goes row by row and the row constraint is satisfied automatically.

**The second insight** makes the safety check O(1). A queen at `(r, c)` attacks:

- Column `c`.
- The main diagonal, on which `r - c` is constant.
- The anti-diagonal, on which `r + c` is constant.

So three boolean arrays replace an O(n) scan.

```cpp
class Solution {
    int n;
    vector<string> board;
    vector<vector<string>> res;
    vector<bool> col, diag, anti;

    void solve(int r) {
        if (r == n) { res.push_back(board); return; }

        for (int c = 0; c < n; c++) {
            int d = r - c + n - 1;                  // shift to keep the index >= 0
            int a = r + c;
            if (col[c] || diag[d] || anti[a]) continue;      // O(1) PRUNE

            col[c] = diag[d] = anti[a] = true;               // CHOOSE
            board[r][c] = 'Q';

            solve(r + 1);                                     // EXPLORE

            board[r][c] = '.';                                // UNCHOOSE
            col[c] = diag[d] = anti[a] = false;
        }
    }

public:
    vector<vector<string>> solveNQueens(int nn) {
        n = nn;
        board.assign(n, string(n, '.'));
        col.assign(n, false);
        diag.assign(2 * n, false);
        anti.assign(2 * n, false);
        solve(0);
        return res;
    }
};
```

`r - c` ranges from `-(n-1)` to `n-1`, so adding `n - 1` shifts it into `[0, 2n-2]`. Forgetting that offset gives a negative index and undefined behaviour.

Complexity: O(n!) as a loose upper bound. With the O(1) pruning the real tree is far smaller, which is why n = 9 is instant despite 9! being 362,880.

### Sudoku Solver (LC 37)

The "find one solution" shape:

```cpp
bool valid(vector<vector<char>>& b, int r, int c, char d) {
    for (int i = 0; i < 9; i++) {
        if (b[r][i] == d) return false;                      // row
        if (b[i][c] == d) return false;                      // column
        if (b[3 * (r / 3) + i / 3][3 * (c / 3) + i % 3] == d) return false;  // box
    }
    return true;
}

bool solve(vector<vector<char>>& b) {
    for (int r = 0; r < 9; r++)
        for (int c = 0; c < 9; c++) {
            if (b[r][c] != '.') continue;

            for (char d = '1'; d <= '9'; d++) {
                if (!valid(b, r, c, d)) continue;

                b[r][c] = d;                     // CHOOSE
                if (solve(b)) return true;       // EXPLORE, short-circuit on success
                b[r][c] = '.';                   // UNCHOOSE
            }
            return false;                        // no digit fits: dead end
        }
    return true;                                 // no empty cells left: solved
}
```

Two details:

**The `return false` after the digit loop is essential.** If no digit works in this cell, the branch is dead and the caller must undo its own choice. Omitting it lets the search continue into nonsense.

**`return true` on success propagates all the way up**, stopping the search immediately. Written with a `void` return it would keep exploring after finding the answer.

The box index formula `3*(r/3) + i/3` and `3*(c/3) + i%3` walks the 3×3 block containing `(r, c)`. Derive it once rather than memorising it.

Complexity: O(9^m) where m is the number of empty cells, as an upper bound. Pruning makes it trivial in practice.

### Must remember

1. N-Queens: one queen per row removes a whole dimension of the search.
2. Diagonals are identified by `r - c` (offset by `n-1`) and `r + c`.
3. Three boolean arrays turn an O(n) safety check into O(1). This is the prune that matters.
4. Sudoku returns `bool` and short-circuits. The `return false` after the digit loop is mandatory.
5. Sudoku box index: `3*(r/3) + i/3`, `3*(c/3) + i%3`.
6. Both problems are "known shapes". Interviewers ask them to see whether you recognise the structure, not to watch you derive it live.

---

## 8.10 Complexity of backtracking

### The general rule

**(branching factor)^(depth) × (work per node)**

| Problem | Branching | Depth | Complexity |
|---|---|---|---|
| Subsets | 2 | n | O(2ⁿ · n) |
| Combinations (n choose k) | ≤ n | k | O(C(n,k) · k) |
| Permutations | n, n−1, … | n | O(n! · n) |
| Combination Sum | ≤ len(cand) | target / min | exponential |
| N-Queens | ≤ n | n | O(n!) loose |
| Sudoku | ≤ 9 | empty cells | O(9^m) loose |
| Word Search | 4 | word length | O(m·n·4^L) |

**The `· n` factor is the output copy.** Every time you `res.push_back(cur)`, you copy a vector of length up to n. People forget this and get corrected.

### Space

O(depth) for the recursion stack plus O(depth) for the current partial solution. **The output is usually not counted** as auxiliary space, but say so explicitly: "O(n) extra space, not counting the output, which is exponential by necessity."

### What the constraints tell you

From Module 1's table:

| Constraint | Suggests |
|---|---|
| n ≤ 10 | Permutations, O(n!) |
| n ≤ 20 | Subsets, O(2ⁿ) |
| n ≤ 25 | Meet in the middle, or bitmask DP |
| n larger | Backtracking is **not** the intended solution |

If a problem smells like backtracking but n is 10⁵, you are looking at a greedy or DP problem instead. That inference is worth making explicitly before you start writing.

### Must remember

1. Branching^depth × work per node.
2. Include the output-copy factor.
3. Pruning improves the practical runtime, not the worst-case bound. Say both.
4. n ≤ 20 means subsets; n ≤ 10 means permutations; larger means a different technique entirely.

---

## 8.11 Consolidation

### Recognition guide

| The statement says | Technique |
|---|---|
| "all subsets", "power set" | Subsets template |
| "all combinations of size k" | Loop form + size base case |
| "all permutations", "all orderings" | `used[]` array, no `start` |
| "combinations that sum to target", reuse allowed | `solve(i, ...)` |
| "each number used once", duplicates in input | `solve(i+1, ...)` + `i > start` skip |
| "all valid arrangements/placements" | Constraint backtracking (N-Queens) |
| "does a path exist", "can we complete" | Bool-returning backtracking, short-circuit |
| "all paths in a grid" | Grid backtracking with undone visited marks |
| "partition the string into valid pieces" | Backtracking over cut positions |
| "generate all valid X" | Backtracking with a validity prune |
| n ≤ 20, exponential answer expected | Backtracking or bitmask |
| n large, "count the number of ways" | **DP, not backtracking** (Module 13) |

That last row matters. "Count the ways" with a large n is a DP problem. Backtracking enumerates; DP counts. If you only need the count, enumerating is exponential waste.

### The knob table, restated

| Knob | Setting | Effect |
|---|---|---|
| Recursive index | `solve(i + 1)` | No reuse |
| | `solve(i)` | Reuse allowed |
| | no `start`, loop from 0 | Permutations |
| Duplicate rule | none | Input has no duplicates |
| | `i > start && a[i]==a[i-1]` | Subsets, combinations |
| | `i > 0 && a[i]==a[i-1] && !used[i-1]` | Permutations |
| Return type | `void`, explore all | All solutions |
| | `bool`, short-circuit | One solution |
| Record point | at leaves | Fixed-size answers |
| | at every node | Subsets |

### Must remember (consolidated)

1. Backtracking = recursion + undo.
2. Choose, explore, unchoose. The undo mirrors the choose exactly.
3. Undo **everything** you changed. Two changes means two undos.
4. Shared state must be passed by reference.
5. `solve(i)` reuses; `solve(i + 1)` does not; no `start` means permutations.
6. Sort before any duplicate skipping.
7. Subsets/combinations skip on `i > start`. Permutations skip on `!used[i-1]`.
8. All solutions → `void`. One solution → `bool` with short-circuit.
9. Sudoku needs `return false` after the digit loop.
10. Prune before recursing, not after.
11. Sort to turn `continue` into `break`.
12. N-Queens: one queen per row; diagonals are `r-c+n-1` and `r+c`.
13. Grid backtracking un-marks visited; graph DFS does not.
14. Complexity is branching^depth × work per node, including the output copy.
15. n ≤ 20 → subsets; n ≤ 10 → permutations; larger → different technique.

### Common mistakes (consolidated)

**Wrong answer**
- Missing the undo, contaminating sibling branches.
- Undoing only part of the state (`cur.pop_back()` without `used[i] = false`).
- `i > 0` instead of `i > start` in duplicate skipping, losing valid answers.
- Not sorting before skipping duplicates.
- `solve(i + 1)` where reuse was intended, or vice versa.
- Recording only at leaves in the subsets loop form.
- Missing `return false` in Sudoku.

**Time limit exceeded**
- No pruning at all.
- Validity check after recursing rather than before.
- O(n) safety checks instead of maintained O(1) state.
- Using `continue` where `break` was valid.
- `void` return in a find-one-solution problem, exploring past the answer.
- Copying the partial solution at every node instead of mutating one buffer.

**Runtime error**
- Negative diagonal index in N-Queens (missing the `+ n - 1` offset).
- Grid access before the bounds check.
- Stack overflow on a deep, unpruned search.

**Analysis errors**
- Reporting O(2ⁿ) instead of O(2ⁿ · n).
- Claiming pruning improves the worst case.
- Counting the output in the space complexity without saying so.

---

## 8.12 Problem set

Twelve core problems plus three optional. **Do them in the order given** — the duplicate variants only make sense after their base versions.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Subsets (LC 78) | Medium | Both formulations | The foundation; write pick/not-pick and the loop form |
| Combinations (LC 77) | Medium | Loop form + size base | `start`, and the bound prune |
| Letter Combinations of a Phone Number (LC 17) | Medium | Per-level choice set | Choices come from a mapping, not the array |

### Level 2 — Pattern (4)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Permutations (LC 46) | Medium | `used[]`, no `start` | Two state changes, two undos |
| Combination Sum (LC 39) | Medium | `solve(i)` reuse | The one-character difference, and sorted pruning |
| Generate Parentheses (LC 22) | Medium | Constraint-driven choices | Pruning by counting, not by checking afterwards |
| Subsets II (LC 90) | Medium | `i > start` skip | The duplicate rule, in its simplest setting |

### Level 3 — Interview (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Combination Sum II (LC 40) | Medium | `i+1` + duplicate skip | Both knobs changed at once |
| Permutations II (LC 47) | Medium | `!used[i-1]` skip | The rule that looks backwards; trace it by hand |
| Word Search (LC 79) | Medium | Grid + in-place marking | Bool short-circuit, and un-marking |
| Palindrome Partitioning (LC 131) | Medium | Backtracking over cuts | Choices are split points, not elements |
| N-Queens (LC 51) | Hard | Constraint propagation | O(1) safety via three boolean arrays |

### Level 4 — Advanced (3, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Sudoku Solver (LC 37) | Hard | Find-one + heavy pruning | The `return false` that people omit |
| Rat in a Maze (GeeksforGeeks) | Medium | Grid, all paths | Visited marks that get undone |
| Word Break II (LC 140) | Hard | Backtracking + memo | Where backtracking meets DP |

**LC 22 is quietly the best problem here.** Generate Parentheses cannot be solved by generating everything and filtering; you have to prune *while building*, using the counts of open and close brackets placed so far. That is the mental shift from "enumerate then check" to "only construct valid things", which is what pruning really means.

---

## Exit checklist

```
[ ] I can state the difference between recursion and backtracking in one line
[ ] I write choose / explore / unchoose without thinking
[ ] I undo EVERY state change I made
[ ] I pass shared state by reference
[ ] I can write Subsets both ways from memory
[ ] I know solve(i) vs solve(i+1) vs no-start, and what each produces
[ ] I can write Permutations with used[] from memory
[ ] I sort before any duplicate skipping
[ ] I know why the skip is i > start and not i > 0
[ ] I can explain the !used[i-1] rule in Permutations II
[ ] I know when to use void vs bool return
[ ] I prune BEFORE recursing
[ ] I sort to turn continue into break
[ ] I can write N-Queens with the three boolean arrays
[ ] I know the diagonal index formulas
[ ] I know grid backtracking un-marks visited but graph DFS does not
[ ] I report complexity as branching^depth x work-per-node, including the copy
[ ] I check n against the constraint table before choosing backtracking
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 9"** for Trees (18–22 hours, Tier 1). It is the second-largest module in the roadmap and the one where Module 4's recursive-contract method pays off most: nearly every tree solution is one sentence of contract plus three lines of code.

The module covers terminology and the tree types interviewers name, all four traversals recursively and iteratively, the view and boundary problems, LCA, diameter, maximum path sum, serialization, building a tree from traversals, Morris traversal, and then BSTs as a separate half with validation, deletion, k-th smallest, and predecessor/successor.
