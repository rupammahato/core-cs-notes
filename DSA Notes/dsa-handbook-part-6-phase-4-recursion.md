# DSA Placement Handbook (C++) — Part 6
# Phase 4: Recursion Fundamentals

**Module 4 · 6–8 hours · Tier 1 · Requires: Modules 0, 1**

---

## Why this module sits here

In your original outline recursion came at Phase 6, after stacks and queues. I moved it forward for one concrete reason: **merge sort and quick sort are recursion problems wearing a sorting costume.** Their complexity is unreadable without recurrences, and Module 5 is next.

But the deeper reason is that recursion is load-bearing for four later modules:

| Module | What breaks without recursion |
|---|---|
| 5 — Sorting | Merge sort, quick sort, and the whole divide-and-conquer idea |
| 8 — Backtracking | Backtracking *is* recursion plus an undo step |
| 9 — Trees | Every tree solution is a recursive contract |
| 13 — DP | Memoisation is recursion with a cache; tabulation is that recursion unrolled |

This module also deliberately stops short of backtracking. Generating subsets and permutations gets a preview here and full treatment in Module 8, because by then you will have more maturity and the pruning ideas will land better.

**The goal is not to memorise recursive solutions.** It is to be able to construct one for a problem you have never seen. Section 4.3 is the section that does that work.

---

## 4.1 Recursion anatomy

### 1. What is it?

A function that solves a problem by calling itself on a smaller version of the same problem.

### 2. Why do we need it?

Because some structures are defined recursively and iterating over them is genuinely awkward. A tree is "a node with two subtrees, each of which is a tree". Writing that iteratively means managing your own stack; writing it recursively means writing down the definition.

Recursion is also the natural language for "try every option": each call makes one choice and delegates the rest.

### 3. Core idea

Every recursive function has exactly two parts:

```cpp
returnType f(parameters) {
    if (base case) return direct answer;     // 1. STOPS the recursion
    
    return combine(f(smaller input));        // 2. MOVES TOWARD the base case
}
```

Both parts are mandatory. Missing the base case is infinite recursion. Having a base case the recursion never reaches is also infinite recursion, and it is the subtler failure.

```cpp
int fact(int n) {
    if (n <= 1) return 1;          // base case
    return n * fact(n - 1);        // recursive case: n-1 moves toward 1
}
```

### 4. The three questions

Every recursive function you write should answer these before you type anything:

1. **What does this function promise to return?** State it in one sentence.
2. **What is the smallest input I can answer without recursing?**
3. **If the function already works for smaller inputs, how do I build the answer for this one?**

For `fact`: (1) "returns n factorial", (2) `n <= 1` gives 1, (3) `n × fact(n-1)`.

### 5. Complexity

Time: number of calls × work per call. Space: **recursion depth**, because each live call holds a stack frame.

`fact(n)` makes n calls with O(1) work each, so O(n) time. Depth is n, so O(n) space. It looks like an O(1)-space function and is not.

### 6. Must remember

1. Base case first, always. Write it before the recursive case.
2. The recursive call must move **toward** the base case. `f(n-1)` does; `f(n)` does not; `f(n/2)` does only if n is positive.
3. **Return the recursive call's value.** Writing `fact(n-1);` instead of `return n * fact(n-1);` compiles and returns garbage.
4. Recursion depth is space complexity. Always include it.
5. Depth beyond roughly 10⁵ overflows the stack and segfaults with no message.
6. Negative or zero inputs often need their own base case. `fact(-1)` with `if (n == 1)` recurses forever; `if (n <= 1)` does not.

### 7. Common mistakes

- No base case, or a base case the recursion skips past (using `==` where `<=` was needed).
- Forgetting `return` on the recursive call.
- The recursive call does not shrink the input.
- Passing a container by value into the recursion (Module 0, Section A4). Silent O(n) per call.
- Reporting O(1) space.

---

## 4.2 The call stack

### What actually happens

Each call pushes a **stack frame** holding that call's parameters, local variables, and the address to return to. The frame lives until the call returns.

```
fact(4)  called
┌──────────────┐
│ fact(4) n=4  │  waiting for fact(3)
├──────────────┤
│ fact(3) n=3  │  waiting for fact(2)
├──────────────┤
│ fact(2) n=2  │  waiting for fact(1)
├──────────────┤
│ fact(1) n=1  │  BASE CASE -> returns 1
└──────────────┘
      then frames pop upward:
      fact(2) returns 2*1 = 2
      fact(3) returns 3*2 = 6
      fact(4) returns 4*6 = 24
```

Two phases worth naming, because they explain a lot of confusing behaviour:

**The way down** (calls being made, frames pushed). Anything you do *before* the recursive call happens here, in order from the outermost call inward.

**The way up** (calls returning, frames popped). Anything you do *after* the recursive call happens here, in reverse order.

```cpp
void f(int i, int n) {
    if (i == n) return;
    cout << i << " ";      // on the way DOWN:  0 1 2 3
    f(i + 1, n);
    cout << i << " ";      // on the way UP:    3 2 1 0
}
// f(0, 4) prints:  0 1 2 3 3 2 1 0
```

This is the entire mechanism behind printing a linked list in reverse, postorder tree traversal, and the "undo" step in backtracking. If the down/up distinction is not automatic for you, trace this function by hand once. It is five minutes well spent.

### Stack limits

| | Typical size | Holds |
|---|---|---|
| Call stack | 1–8 MB | Frames: parameters, locals, return addresses |
| Heap | System RAM | `new`, and the contents of every STL container |

A frame with a few `int`s is roughly 50–100 bytes, so depth of ~10⁵ is usually survivable and ~10⁶ usually is not. A frame holding a `vector` by value is far larger, which is the second reason (after the copying cost) that Module 0's parameter-passing rules matter.

**Stack overflow presents as a segfault with no useful message.** If a recursive solution crashes on a large test and works on small ones, suspect depth before you suspect logic.

### Must remember

1. Work done before the recursive call happens top-down; work after happens bottom-up.
2. Each frame lives until its call returns. Depth, not total call count, is the space cost.
3. A recursion tree with 2ⁿ nodes uses O(n) space, not O(2ⁿ), because only one root-to-leaf path is live at a time.
4. Local variables are per-frame. Each call has its own copy, which is why recursion can "remember" state without you managing it.
5. Anything you want shared across calls must be passed by reference or be global.

---

## 4.3 The recursive contract (how to construct solutions)

This is the most important section in the module. Most people learn recursion by memorising five solutions and then freeze on the sixth. The fix is a repeatable procedure.

### 1. Core idea

**Write down what the function promises, then trust it.**

The mental move is: assume the function already works correctly for any smaller input. Do not trace the recursion. Do not try to hold four levels of calls in your head. Just ask: *given a correct answer for the smaller problem, how do I produce the answer for this one?*

This is sometimes called the "leap of faith" or "the recursive contract". It is not a trick; it is induction. If the base case is right, and the step from "works for smaller" to "works for this" is right, the whole thing is right.

### 2. The procedure

**Step 1 — State the contract in one sentence.**

> `int maxDepth(TreeNode* root)` returns the height of the tree rooted at `root`.

Be precise. "Returns the height" is a contract. "Does the tree thing" is not.

**Step 2 — Identify the smallest input and answer it directly.**

> An empty tree (`root == nullptr`) has height 0.

**Step 3 — Assume the function works on smaller inputs, and combine.**

> If `maxDepth(root->left)` and `maxDepth(root->right)` are correct, then the height here is `1 + max(left, right)`.

**Step 4 — Write it.**

```cpp
int maxDepth(TreeNode* root) {
    if (!root) return 0;                                    // Step 2
    return 1 + max(maxDepth(root->left), maxDepth(root->right));  // Step 3
}
```

You never traced a single call. That is the point.

### 3. Worked example: reverse a string in place

**Contract:** `rev(s, l, r)` reverses the portion of `s` between indices `l` and `r`.

**Smallest input:** when `l >= r` there is nothing to do (zero or one character).

**Combine:** swap the outer pair, then trust the function to reverse the inside.

```cpp
void rev(string& s, int l, int r) {
    if (l >= r) return;
    swap(s[l], s[r]);
    rev(s, l + 1, r - 1);
}
```

### 4. Worked example: sum of an array

**Contract:** `sum(a, i)` returns the sum of `a[i..end]`.

**Smallest input:** `i == a.size()` means an empty range, sum 0.

**Combine:** `a[i] + sum(a, i+1)`.

```cpp
int sum(const vector<int>& a, int i) {
    if (i == (int)a.size()) return 0;
    return a[i] + sum(a, i + 1);
}
```

Note the `const&`. Passing `a` by value would copy the whole array on every call, turning O(n) into O(n²). This is the mistake from Module 0 Section A4, and recursion is where it does the most damage.

### 5. Worked example: palindrome check

**Contract:** `isPal(s, l, r)` returns whether `s[l..r]` is a palindrome.

**Smallest input:** `l >= r` is trivially a palindrome.

**Combine:** the ends must match, **and** the inside must be a palindrome.

```cpp
bool isPal(const string& s, int l, int r) {
    if (l >= r) return true;
    if (s[l] != s[r]) return false;
    return isPal(s, l + 1, r - 1);
}
```

### 6. When should I use this?

Every time you write a recursive function. It is a procedure, not a concept, and it works on problems you have never seen. In an interview, saying the contract out loud before coding ("this function will return the height of the subtree rooted here") is also an unusually strong signal, because it shows you are designing rather than recalling.

### 7. Must remember

1. State the contract in one sentence before writing any code.
2. Trust the recursive call. Do not trace it. Tracing more than one level deep is a sign you have not stated the contract clearly.
3. The base case is "the smallest input where I can answer without recursing", not "n equals zero" by reflex.
4. If the combine step feels impossible, your contract is probably wrong. Try a different return value, or add a parameter.
5. Trace by hand **only** when debugging, and only two levels.

### 8. Common mistakes

- Trying to hold the whole call tree in your head instead of trusting the contract.
- A vague contract, which makes the combine step impossible to write.
- Choosing a base case that the recursion never reaches.
- Writing the recursive case first and then trying to reverse-engineer a base case.

---

## 4.4 The two shapes: return-value vs accumulator

### 1. What is it?

Two ways to carry information through a recursion. Knowing both, and which to reach for, removes most of the awkwardness people feel with recursion.

### 2. Shape A: return-value ("functional") recursion

The answer is **built on the way up**. Each call returns something; the parent combines.

```cpp
int sum(const vector<int>& a, int i) {
    if (i == (int)a.size()) return 0;
    return a[i] + sum(a, i + 1);          // combine on the way up
}
```

### 3. Shape B: accumulator ("parameterised") recursion

The answer is **carried on the way down** as a parameter. The base case reports it.

```cpp
void sum(const vector<int>& a, int i, int acc, int& result) {
    if (i == (int)a.size()) { result = acc; return; }
    sum(a, i + 1, acc + a[i], result);    // carry down
}
```

### 4. Which to use

| | Return-value | Accumulator |
|---|---|---|
| Answer built | On the way up | On the way down |
| Return type | Meaningful | Often `void` |
| Reads like | A mathematical definition | A process |
| Natural for | Computing one value: sums, heights, counts | Collecting many results, tracking a path |
| Used by | Tree problems, divide and conquer, DP | Backtracking, path printing, subset generation |

**Default to return-value recursion.** It is shorter, easier to reason about, and composes better. Switch to the accumulator shape when you need to know the *path taken to get here*, which is exactly what backtracking needs.

### 5. Why this matters for Module 8

Subset generation is the canonical accumulator recursion, and it comes in two flavours that look similar and behave differently:

```cpp
// Flavour 1: pass the partial result BY VALUE. Undo is automatic.
void gen(int i, const string& s, string cur, vector<string>& out) {
    if (i == (int)s.size()) { out.push_back(cur); return; }
    gen(i + 1, s, cur, out);              // skip s[i]
    gen(i + 1, s, cur + s[i], out);       // take s[i]
}

// Flavour 2: pass BY REFERENCE. You must undo manually. This is BACKTRACKING.
void gen(int i, const string& s, string& cur, vector<string>& out) {
    if (i == (int)s.size()) { out.push_back(cur); return; }
    gen(i + 1, s, cur, out);              // skip
    cur.push_back(s[i]);                  // choose
    gen(i + 1, s, cur, out);              // explore
    cur.pop_back();                       // UNDO  <- the backtracking step
}
```

Flavour 1 copies the string at every call, costing O(n) per node. Flavour 2 mutates one shared buffer and undoes the change on the way back up, which is O(1) per node. **That undo line is the entire difference between recursion and backtracking**, and it is why Module 8 exists as a separate module.

Both are correct. Flavour 2 is what you want in interviews once the inputs get large.

### 6. Must remember

1. Return-value recursion builds up; accumulator recursion carries down.
2. Prefer return-value unless you need the path.
3. Shared state in accumulator recursion must be passed by **reference**, or nothing propagates.
4. If you mutate shared state, you must undo it after the recursive call returns. That is backtracking.
5. Passing the partial result by value gives automatic undo at the cost of a copy per node.

### 7. Common mistakes

- Passing shared state by value and wondering why the result is empty.
- Mutating shared state and forgetting to undo, so later branches see contamination from earlier ones.
- Using `void` with an accumulator when a simple return value would have been half the code.

---

## 4.5 Recursion on arrays, strings, and numbers

The mechanical part: what "smaller input" means for each data type.

### Arrays and strings: shrink by index

**Never pass subarrays.** Pass the full container by `const&` plus an index or index pair.

```cpp
// From the front
f(a, i + 1)                      // process a[i], recurse on the rest

// From both ends
f(a, l + 1, r - 1)               // palindromes, reversal

// Split in half
f(a, lo, mid);  f(a, mid + 1, hi)  // divide and conquer
```

```cpp
// WRONG: O(n) copy per call, turns O(n) into O(n²)
int sum(vector<int> a) {
    if (a.empty()) return 0;
    int first = a[0];
    a.erase(a.begin());          // O(n) as well
    return first + sum(a);
}
```

### Numbers: shrink by digit or by halving

```cpp
// Sum of digits: strip one digit per call
int digitSum(int n) {
    if (n == 0) return 0;
    return n % 10 + digitSum(n / 10);       // O(log n) depth
}

// Halving: O(log n) depth
int countBits(long long n) {
    if (n == 0) return 0;
    return (n & 1) + countBits(n >> 1);
}
```

Halving gives log-depth recursion, which is why binary search and fast exponentiation are cheap.

### Recursive binary search

```cpp
int bsearch(const vector<int>& a, int lo, int hi, int target) {
    if (lo > hi) return -1;                       // base case: empty range
    int mid = lo + (hi - lo) / 2;                 // not (lo+hi)/2
    if (a[mid] == target) return mid;
    if (a[mid] < target) return bsearch(a, mid + 1, hi, target);
    return bsearch(a, lo, mid - 1, target);
}
```

T(n) = T(n/2) + O(1) → **O(log n)** time, O(log n) space for the stack. Module 5 covers the iterative version, which is O(1) space and what you should usually write.

### Must remember

1. Pass containers by `const&` with indices. Never slice or copy.
2. `l >= r` is the base case for two-ended recursion; `i == n` for one-ended.
3. Halving gives O(log n) depth; decrementing gives O(n) depth.
4. `lo > hi` (not `lo == hi`) is the correct empty-range base case for binary search.
5. Recursive binary search is O(log n) space; the iterative version is O(1). Mention this if asked.

---

## 4.6 Multiple recursion and the recursion tree

### 1. What is it?

A function that calls itself more than once per invocation. The call structure becomes a tree rather than a chain, and the cost analysis changes completely.

### 2. Core idea

```cpp
int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}
```

```
                    fib(5)
              /              \
          fib(4)            fib(3)
         /     \           /     \
     fib(3)  fib(2)    fib(2)  fib(1)
     /   \    /   \     /  \
  fib(2) f(1) f(1) f(0) f(1) f(0)
   /  \
 f(1) f(0)
```

Look at `fib(3)`: computed twice. `fib(2)`: three times. This duplication is exponential, and it is the problem memoisation solves.

### 3. Cost analysis

**Time = number of nodes × work per node.**
**Space = depth of the tree** (not node count).

| Recurrence | Shape | Time | Space |
|---|---|---|---|
| T(n) = T(n−1) + O(1) | Chain | O(n) | O(n) |
| T(n) = 2T(n−1) + O(1) | Binary tree, depth n | **O(2ⁿ)** | O(n) |
| T(n) = 2T(n/2) + O(1) | Binary tree, depth log n | O(n) | O(log n) |
| T(n) = 2T(n/2) + O(n) | Binary tree, linear merge | O(n log n) | O(log n) + merge buffer |

The fork that matters: **`T(n−1)` twice is exponential; `T(n/2)` twice is not.** Two calls on an input smaller by one gives depth n and 2ⁿ nodes. Two calls on half the input gives depth log n and only n leaves. This is the entire difference between naive fibonacci and merge sort.

### 4. Tower of Hanoi

The classic multiple-recursion problem, and a good contract exercise.

**Contract:** `hanoi(n, from, to, aux)` moves `n` disks from peg `from` to peg `to`, using `aux` as scratch.

**Base case:** zero disks, nothing to do.

**Combine:** move the top `n−1` out of the way, move the big disk, move the `n−1` back.

```cpp
void hanoi(int n, char from, char to, char aux) {
    if (n == 0) return;
    hanoi(n - 1, from, aux, to);                       // n-1 out of the way
    cout << "Move disk " << n << ": " << from << " -> " << to << "\n";
    hanoi(n - 1, aux, to, from);                       // n-1 back on top
}
```

T(n) = 2T(n−1) + 1, giving exactly 2ⁿ − 1 moves. O(2ⁿ) time, O(n) space.

This problem is worth doing because it is impossible to solve by tracing and trivial to solve by contract. If you can write it from the three questions in Section 4.3, the method has landed.

### 5. Must remember

1. Time is node count; space is depth. Never confuse them.
2. `2T(n−1)` is exponential. `2T(n/2)` is not.
3. Repeated subproblems in the tree are the signal for memoisation (Section 4.9) and, eventually, DP.
4. Hanoi takes exactly 2ⁿ − 1 moves. Occasionally asked directly.
5. The recursion tree is the right tool for analysis, not for understanding correctness. Use the contract for correctness.

### 6. Common mistakes

- Reporting O(2ⁿ) space for naive fibonacci. It is O(n).
- Treating `2T(n−1)` as `2T(n/2)` and claiming O(n log n).
- Trying to trace a multiple recursion by hand past depth two.
- Forgetting the work-per-node factor: generating 2ⁿ subsets and copying each one is O(2ⁿ · n), not O(2ⁿ).

---

## 4.7 Divide and conquer

### 1. What is it?

A recursion shape with three explicit steps: **divide** the problem into independent subproblems, **conquer** them recursively, **combine** the results.

### 2. Why do we need it?

It is the structure of merge sort, quick sort, and binary search, all of which arrive in Module 5. Recognising the shape means you can write those from first principles rather than from memory.

### 3. The skeleton

```cpp
Result solve(int lo, int hi) {
    if (lo == hi) return base(lo);              // 1. base: one element

    int mid = lo + (hi - lo) / 2;               // 2. divide
    Result left  = solve(lo, mid);              // 3. conquer
    Result right = solve(mid + 1, hi);

    return combine(left, right);                // 4. combine
}
```

**The combine step is where the algorithm actually lives.** Divide and conquer problems differ only in what `combine` does:

| Algorithm | Combine step | Cost of combine | Total |
|---|---|---|---|
| Binary search | Pick one side, discard the other | O(1), and only one recursive call | O(log n) |
| Merge sort | Merge two sorted halves | O(n) | O(n log n) |
| Quick sort | Nothing (partition happens before) | O(1), but partition is O(n) | O(n log n) avg |
| Max of array | `max(left, right)` | O(1) | O(n) |
| Count inversions | Merge, counting cross-pairs | O(n) | O(n log n) |

### 4. Worked example: maximum of an array

```cpp
int maxOf(const vector<int>& a, int lo, int hi) {
    if (lo == hi) return a[lo];
    int mid = lo + (hi - lo) / 2;
    return max(maxOf(a, lo, mid), maxOf(a, mid + 1, hi));
}
```

T(n) = 2T(n/2) + O(1) → O(n). Same as a simple loop, but the shape is the point. Change `combine` from `max` to "merge" and you have merge sort.

### 5. How to recognise it

Signals: "the problem splits naturally into halves", "the answer for the whole can be built from the answers for the parts", "sorted input" (binary search), "count something across all pairs" (inversions). The precondition is that the **subproblems are independent**. If they overlap, you want DP instead (Module 13).

### 6. Complexity

Use the recurrence table from Section 4.6, or Master Theorem (Module 1, Section 1.5). The common case, `2T(n/2) + O(n)`, is O(n log n) and worth recognising instantly.

### 7. Must remember

1. Divide, conquer, combine. The combine step is the algorithm.
2. `mid = lo + (hi - lo) / 2`, never `(lo + hi) / 2`.
3. Divide and conquer requires **independent** subproblems. Overlapping ones mean DP.
4. Binary search is divide and conquer with only one recursive call, which is why it is O(log n) rather than O(n).
5. `2T(n/2) + O(n)` is O(n log n). Memorise it; it is merge sort, and it appears everywhere.

### 8. Common mistakes

- Overlapping ranges: `solve(lo, mid)` and `solve(mid, hi)` instead of `mid + 1`. Infinite recursion when `hi = lo + 1`.
- `lo == hi` base case with an empty input, where `lo > hi` was needed.
- Applying divide and conquer to overlapping subproblems and getting exponential time.

---

## 4.8 Worked example: fast exponentiation

Worth its own section because it is asked directly, it teaches the halving pattern, and it contains a mistake that is easy to make and hard to see.

### The problem

Compute `b^e`, often modulo `m`, with `e` up to 10⁹.

Naive multiplication is O(e), which is 10⁹ operations. Too slow.

### The insight

```
b^e = (b^(e/2))²           if e is even
b^e = b × (b^(e/2))² ...   if e is odd    [integer division]
```

Each step halves the exponent, so there are O(log e) steps.

```cpp
long long power(long long b, long long e, long long m) {
    if (e == 0) return 1;
    long long half = power(b, e / 2, m);     // compute ONCE
    long long res = half * half % m;
    if (e & 1) res = res * b % m;
    return res;
}
```

### The mistake

```cpp
// WRONG: two recursive calls means the tree has 2^(log e) = e nodes
return power(b, e/2, m) * power(b, e/2, m) % m;     // O(e), not O(log e)
```

The recurrence becomes `T(e) = 2T(e/2) + O(1)`, which is O(e) by the table in 4.6. Storing the result in a variable makes it `T(e) = T(e/2) + O(1)`, which is O(log e). One line, an enormous difference. This is the same duplicated-subproblem issue as naive fibonacci, showing up in a place people do not expect it.

### The iterative version

```cpp
long long power(long long b, long long e, long long m) {
    long long res = 1;
    b %= m;
    while (e > 0) {
        if (e & 1) res = res * b % m;
        b = b * b % m;
        e >>= 1;
    }
    return res;
}
```

O(log e) time, O(1) space. Worth memorising; it appears in modular arithmetic problems, in computing combinations, and in Module 14.

### Must remember

1. Compute the half **once** and store it. Two recursive calls destroy the complexity.
2. Use `long long` throughout. `half * half` overflows `int` immediately.
3. Take `% m` after every multiplication, not just at the end.
4. `e & 1` tests oddness; `e >>= 1` halves. Both are Module 14 material, previewed here.
5. `b^0 = 1`, including `0^0 = 1` by convention in these problems.

---

## 4.9 Memoisation: the bridge to DP

### 1. What is it?

Caching the result of each distinct recursive call so that repeated subproblems are computed once.

### 2. Why do we need it?

Section 4.6 showed naive fibonacci recomputing `fib(3)` twice and `fib(2)` three times. At `n = 45` that duplication is over a billion calls. Caching makes it n calls.

### 3. Core idea

```cpp
long long fib(int n, vector<long long>& memo) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n];            // already computed: return it
    return memo[n] = fib(n-1, memo) + fib(n-2, memo);   // compute, store, return
}

// caller:
vector<long long> memo(n + 1, -1);
cout << fib(n, memo);
```

Three lines added to the naive version. The complexity goes from O(2ⁿ) to O(n).

### 4. Why the complexity collapses

**Time = (number of distinct states) × (work per state).**

This is the rule from Module 1, Section 1.5, and it is the single most useful complexity rule in the handbook. Naive fibonacci has 2ⁿ *calls* but only n *distinct states* (`n = 0, 1, 2, ... n`). Memoisation makes each state cost O(1) and each state be computed exactly once, so the total is O(n).

Every DP problem in Module 13 is this rule applied to a more complicated state.

### 5. The recipe

1. Write the naive recursion using the contract method from 4.3.
2. Identify what uniquely determines the answer of a call. That is the **state**.
3. Make a cache indexed by the state, filled with a sentinel meaning "not computed".
4. Check the cache at the top; write to it before returning.

That is all of top-down DP. Module 13 adds tabulation, space optimisation, and a catalogue of state designs, but the core move is this one.

### 6. Complexity

| | Naive | Memoised |
|---|---|---|
| Fibonacci | O(2ⁿ) time, O(n) space | O(n) time, O(n) space |
| Grid paths | O(2^(n+m)) | O(n·m) |
| Any recursion with overlapping subproblems | Exponential | States × transition |

### 7. Must remember

1. Memoisation only helps when subproblems **overlap**. Merge sort's subproblems are disjoint, so caching does nothing for it.
2. The cache must be keyed by **everything that varies** across calls. Missing a parameter gives wrong answers, not just slow ones.
3. Choose a sentinel that cannot be a valid answer. `-1` works for non-negative results; use a separate `bool computed[]` array when any value is possible.
4. Pass the cache by **reference**. By value it is copied every call, which is worse than no cache at all.
5. `return memo[n] = ...` both stores and returns in one line. Idiomatic and worth adopting.
6. Memoisation still uses recursion, so the stack depth still applies. For n = 10⁶ you need tabulation instead.

### 8. Common mistakes

- Forgetting to write to the cache, so it never hits.
- Caching on an incomplete state.
- Passing the memo by value.
- Using `0` as the sentinel when `0` is a legitimate answer.
- Applying memoisation to a recursion with no overlapping subproblems and expecting a speedup.

---

## 4.10 Recursion vs iteration

### When recursion is the right choice

- The data structure is recursive: trees, tries, nested lists.
- You are exploring choices: subsets, permutations, paths.
- Divide and conquer.
- The iterative version would require you to manage an explicit stack anyway.

### When iteration is better

- Simple linear traversal. Recursive array summing is elegant and pointless.
- Depth could exceed ~10⁵.
- The problem is tail-recursive (see below), where the loop is strictly simpler.
- O(1) space is required.

### Converting recursion to iteration

Any recursion can be made iterative with an explicit stack. You are doing manually what the call stack did automatically.

```cpp
// Recursive DFS on a tree
void dfs(TreeNode* node) {
    if (!node) return;
    visit(node);
    dfs(node->left);
    dfs(node->right);
}

// Iterative equivalent
void dfs(TreeNode* root) {
    if (!root) return;
    stack<TreeNode*> st;
    st.push(root);
    while (!st.empty()) {
        TreeNode* node = st.top(); st.pop();
        visit(node);
        if (node->right) st.push(node->right);   // right FIRST
        if (node->left)  st.push(node->left);    // so left pops first
    }
}
```

Push right before left, because a stack reverses order. Module 9 covers the iterative traversals properly.

### Tail recursion

A call is **tail recursive** when the recursive call is the very last operation, with nothing left to do afterwards.

```cpp
int f(int n, int acc) {
    if (n == 0) return acc;
    return f(n - 1, acc + n);      // tail: nothing happens after the call
}

int g(int n) {
    if (n == 0) return 0;
    return n + g(n - 1);           // NOT tail: the addition happens after
}
```

Some compilers optimise tail calls into loops, eliminating the stack growth. **You cannot rely on this in C++.** It depends on the optimisation level and is not guaranteed by the standard. If you need guaranteed O(1) space, write the loop yourself.

Worth knowing as a concept because it is a common viva question, not because it changes what you write.

### Must remember

1. Any recursion can become iteration with an explicit stack.
2. Push children in reverse order when converting DFS, because a stack reverses.
3. Tail-call optimisation is not guaranteed in C++. Do not depend on it.
4. Recursion costs O(depth) space; the iterative version with an explicit stack costs the same, but on the heap where there is far more room.
5. Choose recursion for clarity on recursive structures, iteration for linear work and deep inputs.

---

## 4.11 Comparison tables

### Recursion vs iteration

| | Recursion | Iteration |
|---|---|---|
| Space | O(depth), on the stack | O(1), or O(depth) on the heap with explicit stack |
| Depth limit | ~10⁵ frames | None practically |
| Readability on trees/graphs | Much better | Worse |
| Readability on linear scans | Worse | Better |
| Failure mode | Segfault, no message | Infinite loop, usually visible |

### Recursion vs backtracking (previewing Module 8)

| | Recursion | Backtracking |
|---|---|---|
| What it is | A function calling itself | Recursion + explicit undo |
| State | Often passed by value or returned | Shared, mutated, restored |
| Explores | One path to an answer | All paths, abandoning bad ones |
| Signature move | `return combine(f(smaller))` | `choose → explore → un-choose` |
| Typical problems | Factorial, tree height, merge sort | Subsets, permutations, N-Queens, Sudoku |

Every backtracking algorithm is recursive. Not every recursion is backtracking. The distinguishing line is the undo.

### The four recursion shapes

| Shape | Recurrence | Time | Example |
|---|---|---|---|
| Linear | T(n−1) + O(1) | O(n) | Factorial, array sum |
| Halving | T(n/2) + O(1) | O(log n) | Binary search, fast power |
| Binary split | 2T(n/2) + O(n) | O(n log n) | Merge sort |
| Binary branch | 2T(n−1) + O(1) | O(2ⁿ) | Fibonacci, subsets, Hanoi |

---

## 4.12 Must remember (consolidated)

1. Base case first, and it must be reachable. Use `<=` rather than `==` when inputs might undershoot.
2. **Return** the recursive call's value.
3. Recursion depth is space complexity. A 2ⁿ-time recursion is O(n) space.
4. Pass containers by `const&` with indices. Never copy or slice.
5. State the contract in one sentence, then trust the recursive call. Do not trace.
6. Work before the call happens top-down; work after happens bottom-up.
7. `2T(n−1)` is exponential; `2T(n/2)` is not.
8. Compute a repeated recursive call **once** and store it (fast power, fibonacci).
9. Return-value recursion builds up; accumulator recursion carries down and needs references.
10. Mutating shared state requires an undo after the call. That is backtracking.
11. Memoisation collapses complexity to states × transition cost.
12. The memo must be keyed by everything that varies, passed by reference, with a sentinel that cannot be a real answer.
13. `mid = lo + (hi - lo) / 2` and `solve(mid + 1, hi)`, never `solve(mid, hi)`.
14. Depth beyond ~10⁵ segfaults with no message.
15. Tail-call optimisation is not guaranteed in C++.

---

## 4.13 Common mistakes (consolidated)

**Infinite recursion / stack overflow**
- No base case, or one the recursion steps over.
- The recursive call does not shrink the input.
- Overlapping ranges in divide and conquer (`solve(mid, hi)`).
- Depth exceeding the stack on large inputs.

**Wrong answer**
- Missing `return` on the recursive call.
- Base case returns the wrong value (0 vs 1 for products).
- Shared state mutated without undo, contaminating sibling branches.
- Memo keyed on an incomplete state.
- Sentinel value that collides with a legitimate answer.

**Time limit exceeded**
- Container passed by value into the recursion.
- The same recursive call evaluated twice instead of stored.
- No memoisation on a recursion with overlapping subproblems.
- `erase(a.begin())` inside a recursion.

**Analysis errors**
- Reporting O(1) space for a recursive function.
- Reporting O(2ⁿ) space for a 2ⁿ-time recursion.
- Treating `2T(n−1)` as `2T(n/2)`.
- Forgetting the per-node work factor.

---

## 4.14 Problem set

Nine problems. This module is about fluency with the construction method, so for each one **write the contract sentence before you write any code.**

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Fibonacci Number (LC 509) | Easy | Binary branch | Write it naive, measure it, then memoise. The whole DP story in one problem |
| Reverse String (LC 344) | Easy | Two-ended recursion | `l >= r` base case, in-place mutation |
| Sum of digits / array sum (drill) | Easy | Linear recursion | Contract practice; do both by hand |

### Level 2 — Pattern (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Pow(x, n) (LC 50) | Medium | Halving | Compute the half once; negative exponents; overflow |
| Binary Search (LC 704) | Easy | Divide and conquer | Recursive vs iterative space trade-off |
| Climbing Stairs (LC 70) | Easy | Binary branch + memo | Identical structure to fibonacci, different story |

### Level 3 — Interview (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Tower of Hanoi (GeeksforGeeks) | Medium | Multiple recursion | Impossible to trace, trivial by contract. The method's proof |
| Subsets (LC 78) | Medium | Accumulator + undo | Preview of backtracking; try both flavours from 4.4 |
| Kth Symbol in Grammar (LC 779) | Medium | Recursive structure | Finding the recursive relation is the entire problem |

**Do LC 509 properly.** Write the naive version, run it for n = 40 and notice how long it takes, then add three lines of memoisation and run it again. That contrast is worth more than reading the DP module twice.

---

## Exit checklist

```
[ ] I write the base case before the recursive case
[ ] I state the contract in one sentence before coding
[ ] I trust the recursive call instead of tracing it
[ ] I can explain work-on-the-way-down vs work-on-the-way-up
[ ] I always return the recursive call's value
[ ] I pass containers by const& with indices, never by value
[ ] I include recursion depth in space complexity
[ ] I know 2T(n-1) is exponential and 2T(n/2) is not
[ ] I can write fast exponentiation and explain the one-call trap
[ ] I can write recursive binary search with lo > hi as the base
[ ] I can solve Tower of Hanoi from the contract alone
[ ] I can add memoisation to any naive recursion in three lines
[ ] I know memo complexity = states x transition cost
[ ] I know the difference between recursion and backtracking (the undo)
[ ] I can convert a recursive DFS to an iterative one with a stack
[ ] All nine problems solved, each with a written contract
```

---

## Next

Say **"Start Phase 5"** for Searching and Sorting (12–15 hours). Now that recursion is in place, merge sort and quick sort become five-line algorithms rather than things to memorise.

The module covers the sorting algorithms and when each matters, `std::sort` and comparators in anger, and then spends most of its time on binary search: the boundary conditions that cause more wrong submissions than any other single topic, lower/upper bound, search in rotated arrays, and **binary search on the answer**, which is the highest-value technique in the module and the one most candidates never learn to recognise.
