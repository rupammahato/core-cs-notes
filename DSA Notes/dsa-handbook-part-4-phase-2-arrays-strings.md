# DSA Placement Handbook (C++) — Part 4
# Phase 2: Arrays and Strings

**Module 2 · 20–25 hours · Tier 1 · Requires: Modules 0, 1**

---

## Why this is the biggest module

Arrays and strings produce more interview questions than any other topic, and not by a small margin. But the reason to spend 25 hours here is not coverage. It is that **five patterns born in this module reappear everywhere else**:

- Two pointers becomes fast/slow pointers in linked lists (Module 6) and the merge step in merge sort (Module 5).
- Sliding window becomes the monotonic deque (Module 7).
- Prefix sums become 2D prefix sums, difference arrays, and the setup for Fenwick trees (Module 15).
- Kadane's algorithm is your first real dynamic program, three modules before DP is formally introduced.
- Sorting-then-scanning is the backbone of every greedy interval problem (Module 11).

Learn these properly here and later modules get shorter. Skim them and you will be relearning them under time pressure in week 8.

**Structure of this module:** Part A is foundations and vocabulary. Part B is the six core patterns, each in full 11-section format. Part C is 2D. Part D is strings. Part E consolidates into a recognition guide and problem set.

---

# PART A — Foundations

## 2.1 The mental model

An array is a contiguous block of memory. That single fact explains every complexity in the table:

```
index:     0     1     2     3     4
         +-----+-----+-----+-----+-----+
a:       |  7  |  2  |  9  |  4  |  1  |
         +-----+-----+-----+-----+-----+
address: 1000  1004  1008  1012  1016     (4 bytes per int)
```

`a[i]` is O(1) because the machine computes `base + i × 4` and jumps there. Insertion in the middle is O(n) because everything after it must physically move. There is no third option; the layout dictates the costs.

Two consequences that matter in practice:

**Arrays are cache-friendly.** Sequential access reads memory the CPU has already prefetched. This is why an O(n log n) `sort` on a `vector` routinely beats an O(n log n) algorithm built on `map`, despite identical asymptotics. When a solution is borderline on time, switching from node-based containers to contiguous ones is a real fix.

**The index is information.** In a `vector<int>`, the position carries meaning for free. Frequency counting, prefix sums, and bucket-based techniques all exploit this: they use the index as the key and pay nothing for the lookup.

---

## 2.2 Traversal, insertion, deletion, and in-place work

### The operations

```cpp
// Traversal
for (int i = 0; i < (int)a.size(); i++) { }     // when you need the index
for (int x : a) { }                              // when you don't
for (int& x : a) x *= 2;                         // when you're modifying
for (int i = a.size() - 1; i >= 0; i--) { }      // backwards

// Insertion / deletion
a.push_back(x);              // O(1) amortised
a.pop_back();                // O(1)
a.insert(a.begin() + i, x);  // O(n)  avoid in loops
a.erase(a.begin() + i);      // O(n)  avoid in loops
```

### The write-pointer idiom

This is the most reusable in-place technique in the module, and it is the template behind Move Zeroes, Remove Duplicates, Remove Element, and a dozen others.

```cpp
int k = 0;                               // next position to write
for (int i = 0; i < n; i++) {            // i reads
    if (keep(a[i])) a[k++] = a[i];       // write survivors to the front
}
// a[0..k-1] is the filtered array; k is the new length
```

Two pointers, both moving forward, one reading and one writing. Never do this with `erase` in a loop: that is O(n²) for the same result.

### In-place reversal and the rotation trick

```cpp
// reverse a[l..r]
while (l < r) swap(a[l++], a[r--]);

// rotate right by k, in O(n) time and O(1) space
k %= n;                                  // ALWAYS do this first
reverse(a.begin(), a.end());
reverse(a.begin(), a.begin() + k);
reverse(a.begin() + k, a.end());
```

Why the triple reversal works: reversing the whole array puts the last `k` elements at the front but in reverse order; reversing each piece separately fixes the order within each. Worth being able to explain, because "rotate an array in O(1) space" is a standard question and the three-reversal answer is the expected one.

### Must remember

1. `erase` or `insert` inside a loop is O(n²). Use the write-pointer idiom instead.
2. Always `k %= n` before rotating. `k` can exceed `n` and the constraints often allow it.
3. Iterating backwards is the right move when you are writing into the array from the end, as in Merge Sorted Array.
4. Modifying a vector's size while range-for iterating is undefined behaviour.

---

## 2.3 Subarray vs substring vs subsequence vs subset

This vocabulary decides which pattern applies. Getting it wrong sends you down the wrong path for twenty minutes.

For `a = [1, 2, 3]`:

| Term | Contiguous? | Order preserved? | Count | Example | Non-example |
|---|---|---|---|---|---|
| **Subarray** / **substring** | Yes | Yes | n(n+1)/2 = 6 | `[2,3]` | `[1,3]` |
| **Subsequence** | No | **Yes** | 2ⁿ = 8 | `[1,3]` | `[3,1]` |
| **Subset** | No | No (a set) | 2ⁿ = 8 | `{3,1}` | — |

"Substring" is just "subarray" for strings. "Subsequence" for strings means the same thing: delete characters, keep the order of what remains.

### Why this matters

| If the problem says | The count of candidates is | So the technique is |
|---|---|---|
| Subarray / substring | O(n²) | Sliding window, prefix sum, two pointers |
| Subsequence | O(2ⁿ) | Dynamic programming (Module 13) or greedy |
| Subset | O(2ⁿ) | Backtracking (Module 8) or bitmask |

**The word "contiguous" in a problem statement is a sliding-window signal.** Its absence, combined with "subsequence", is a DP signal. Longest Increasing *Subsequence* is a hard DP problem; longest increasing *subarray* is a trivial linear scan. Same words except one, completely different problems.

### Must remember

1. Number of subarrays of length n is `n(n+1)/2`. This is why brute-forcing all subarrays is O(n²) at best, O(n³) if you also sum each one.
2. Number of subsequences is `2ⁿ`. Enumerating them is only viable for n ≤ 20 (Module 1's constraint table).
3. Empty subarray and the full array both count as subarrays. Check whether the problem allows the empty one; Kadane's answer changes if it does.
4. A subsequence keeps relative order. A subset does not care. In practice most "subset" problems in DSA are generated in index order, so the distinction rarely changes your code, only your vocabulary.

---

## 2.4 Frequency counting

### Core idea

Convert "how many times does X occur" into an array index or a map key, so counting is O(1) per element.

```cpp
// Bounded small values (lowercase letters): use an array
vector<int> freq(26, 0);
for (char c : s) freq[c - 'a']++;

// Bounded ASCII: 128 entries covers it safely
vector<int> freq(128, 0);
for (char c : s) freq[c]++;

// Unbounded values: use a hash map (Module 3 covers this properly)
unordered_map<int, int> freq;
for (int x : a) freq[x]++;
```

### When to use which

| Value range | Use | Why |
|---|---|---|
| 0–25 (lowercase letters) | `vector<int>(26)` | Fastest, and comparing two frequency arrays is O(26) = O(1) |
| ASCII / mixed case | `vector<int>(128)` | Avoids the "I assumed lowercase" bug |
| Small bounded integers (say ≤ 10⁶) | `vector<int>(maxVal + 1)` | Direct indexing, no hashing overhead |
| Unbounded or negative | `unordered_map<int,int>` | Only option |

### Must remember

1. Prefer the array over the map whenever values are bounded. It is several times faster and comparison is trivial.
2. `freq[c - 'a']` assumes lowercase. Read the constraints. If mixed case or punctuation is possible, use 128 entries.
3. Two strings are anagrams iff their frequency arrays are equal. Comparing two `vector<int>` with `==` does this in one line.
4. A frequency array of size 26 makes "are these two windows equal" an O(26) check, which is O(1). This is what makes the fixed-window anagram problems linear.

---

# PART B — The core patterns

## 2.5 Prefix Sum

### 1. What is it?

A precomputed array where `pre[i]` holds the sum of the first `i` elements. Any range sum then becomes a single subtraction.

### 2. Why do we need it?

Because summing a range naively is O(n) per query. With `q` queries that is O(n·q), which dies at n = q = 10⁵. Prefix sums make it O(n) once and O(1) per query forever after.

### 3. Core idea

```
a    =  [ 3,  1,  4,  1,  5 ]
pre  = [0, 3,  4,  8,  9, 14 ]
        ^
        pre[0] = 0, the sentinel that removes all the special cases

sum(a[1..3]) = pre[4] - pre[1] = 9 - 3 = 6     (1 + 4 + 1) ✓
```

The offset-by-one sizing (`n+1`, with `pre[0] = 0`) is not a stylistic choice. It removes the `if (l == 0)` special case, which is where the off-by-one bugs live. Always size it `n+1`.

### 4. When should I use it?

- Multiple range-sum queries on a static array.
- Any problem where you need "sum of everything before index i" or "sum of everything after".
- As the setup for prefix-sum-plus-hashmap (Module 3), which is how you count subarrays with a given sum.
- Counting: a prefix sum over a 0/1 array counts occurrences in a range.

### 5. How to recognise the pattern

Signals: "sum of the subarray from l to r", "multiple queries", "range sum", "how many X between index i and j", "the array does not change". The phrase **"q queries"** with a static array is nearly always prefix sums.

### 6. C++ template

```cpp
// Build: O(n)
vector<long long> pre(n + 1, 0);
for (int i = 0; i < n; i++)
    pre[i + 1] = pre[i] + a[i];

// Query sum of a[l..r] inclusive: O(1)
long long rangeSum(int l, int r) {
    return pre[r + 1] - pre[l];
}
```

**Prefix and suffix together**, the Product of Array Except Self shape:

```cpp
vector<int> res(n, 1);
int prefix = 1;
for (int i = 0; i < n; i++)  { res[i] = prefix; prefix *= a[i]; }
int suffix = 1;
for (int i = n - 1; i >= 0; i--) { res[i] *= suffix; suffix *= a[i]; }
```

Two passes, O(1) extra space beyond the output. This "everything before × everything after" idea generalises well.

### 7. Example

`a = [3,1,4,1,5]`, query sum of indices 1 to 3.
`pre = [0,3,4,8,9,14]`, answer `pre[4] - pre[1] = 9 - 3 = 6`.

### 8. Complexity

Build O(n) time, O(n) space. Query O(1). Total for q queries: O(n + q) instead of O(n·q).

### 9. Must remember

1. **Use `long long` for the prefix array.** n = 10⁵ values up to 10⁹ sums to 10¹⁴, which overflows `int`. This is the most common wrong-answer bug in prefix-sum problems.
2. Size it `n+1` with `pre[0] = 0`. The alternative (`pre[i] = sum of first i+1`) forces a special case at `l == 0`.
3. Inclusive range `[l, r]` is `pre[r+1] - pre[l]`. Write this down; the indices are easy to swap under pressure.
4. Prefix sums require a **static** array. If values change between queries, you need a Fenwick or segment tree (Module 15, Tier 4).
5. The same idea works for prefix XOR, prefix max (of a fixed direction), prefix product, and prefix counts.
6. Prefix sum plus a hash map counts subarrays with a target sum in O(n). That is Module 3, and it is the single highest-value application.

### 10. Common mistakes

- `vector<int> pre` instead of `long long`. Silent overflow.
- Off-by-one: writing `pre[r] - pre[l]` (exclusive of `r`) when you meant inclusive.
- Rebuilding the prefix array inside a query loop, turning O(1) queries back into O(n).
- Using prefix sums on an array that gets updated.

### 11. Practice

- Running Sum of 1d Array (LC 1480, Easy)
- Range Sum Query - Immutable (LC 303, Easy)
- Product of Array Except Self (LC 238, Medium)
- Find Pivot Index (LC 724, Easy)

---

## 2.6 Difference Array

### 1. What is it?

The inverse of a prefix sum. It makes **range updates** O(1) at the cost of one O(n) pass at the end to read the final array.

### 2. Why do we need it?

Prefix sums give O(1) range *queries* on a static array. Difference arrays give O(1) range *updates* when you only need to read the result once, at the end. Doing `q` range updates naively is O(n·q); with a difference array it is O(n + q).

### 3. Core idea

To add `v` to every element in `a[l..r]`, mark the boundaries instead of touching the interior:

```
diff[l]   += v        "start adding v here"
diff[r+1] -= v        "stop adding v after here"
```

Then a running prefix sum over `diff` reconstructs the accumulated additions.

```
n = 5, add 3 to a[1..3]:

diff  = [0, +3, 0, 0, -3, 0]
             ^            ^
             l           r+1

running sum: 0, 3, 3, 3, 0     <- exactly the amount added at each index ✓
```

### 4. When should I use it?

- Many range updates, then one final read. Booking systems, flight seat counts, marking intervals.
- Counting how many intervals cover each point. (Set `v = 1` for every interval.)
- The "minimum number of platforms / maximum overlapping meetings" family, when times are small integers.

### 5. How to recognise the pattern

Signals: "add v to all elements between l and r", "given a list of bookings/reservations/intervals, return the final count", "q updates then print the array". The giveaway is **updates outnumber reads**, and all the reads come at the end.

If updates and queries are interleaved, you need a Fenwick tree instead (Tier 4).

### 6. C++ template

```cpp
vector<long long> diff(n + 1, 0);     // n+1 so r+1 == n is always safe

// Apply an update: O(1)
void update(int l, int r, long long v) {
    diff[l] += v;
    diff[r + 1] -= v;
}

// Reconstruct the final array: O(n)
vector<long long> build(int n, const vector<long long>& diff) {
    vector<long long> a(n);
    long long running = 0;
    for (int i = 0; i < n; i++) {
        running += diff[i];
        a[i] = running;
    }
    return a;
}
```

### 7. Example

Corporate Flight Bookings: given `[[1,2,10],[2,3,20]]` over 3 flights, add 10 to flights 1–2 and 20 to flights 2–3.

```
diff = [10, 10, -10, -20]   (1-indexed shifted to 0-indexed)
running sums: 10, 30, 20
answer: [10, 30, 20]
```

Two O(1) updates instead of five element writes. At scale, this is the difference between passing and timing out.

### 8. Complexity

O(1) per update, O(n) to build the result, O(n) space. Total O(n + q).

### 9. Must remember

1. Size the array `n+1`, not `n`. Otherwise `diff[r+1]` is out of bounds when `r == n-1`. This is the bug everyone hits once.
2. Difference array and prefix sum are exact inverses. Prefix sum of a difference array recovers the original.
3. It only works when all updates happen before all reads. Interleaved updates and queries need a Fenwick tree.
4. Use `long long` for the same overflow reason as prefix sums.
5. Watch for 1-indexed problem statements. Flight and booking problems are usually 1-indexed; convert once, at the boundary, and comment it.

### 10. Common mistakes

- Sizing the array `n` and writing out of bounds at `r+1`.
- Forgetting to run the final prefix pass, and returning the difference array itself.
- Mixing up 1-indexed input with 0-indexed storage.
- Reaching for a difference array when queries are interleaved with updates.

### 11. Practice

- Corporate Flight Bookings (LC 1109, Medium)
- Range Addition (LC 370, Medium, premium; the pure form of the pattern)
- Car Pooling (LC 1094, Medium)

---

## 2.7 Two Pointers

### 1. What is it?

Two indices moving through the array under a rule, so that you examine O(n) positions instead of the O(n²) pairs.

Two distinct shapes:

- **Opposite ends:** `l` starts at 0, `r` at n−1, they move toward each other.
- **Same direction:** both move forward, one leading and one trailing. (The write-pointer idiom in 2.2 is this shape; so is sliding window, which is important enough to get its own section.)

### 2. Why do we need it?

The brute force for pair problems is a double loop, O(n²). When the array is sorted, comparing `a[l] + a[r]` against the target tells you which pointer to move, and each pointer moves at most n times total. O(n²) becomes O(n).

### 3. Core idea (opposite ends)

On a **sorted** array looking for a pair summing to `target`:

```
a = [1, 3, 5, 7, 9]   target = 12
     l           r      sum = 10 < 12  -> l++  (need bigger; r-- would only shrink)
        l        r      sum = 12       -> found

Why it's safe: if a[l] + a[r] < target, then a[l] paired with ANY
smaller element is also too small. So a[l] is useless entirely: discard it.
```

That last line is the proof, and it is what an interviewer wants to hear. Each step eliminates a whole row or column of the implicit n² grid.

### 4. When should I use it?

- The array is **sorted** (or you can afford to sort it), and you need pairs or triplets with a sum property.
- You are comparing elements from both ends: palindromes, container with most water, trapping rain water.
- You need an **in-place** O(1)-space transformation: reversing, partitioning, removing elements.
- You are merging two sorted sequences.

### 5. How to recognise the pattern

Signals: "sorted array", "find a pair/triplet such that", "two numbers that add to", "in-place", "O(1) extra space", "palindrome", "from both ends", "container/area between two lines". The combination of **sorted input** and **a pair** is the strongest signal in DSA.

If the array is unsorted and you need a pair sum, the answer is usually a hash map (Module 3), not two pointers. If sorting is allowed and you need to return *values* rather than original indices, sorting plus two pointers is O(n log n) with O(1) space; a hash map is O(n) with O(n) space. Both are valid; say the trade-off out loud.

### 6. C++ templates

**Opposite ends, pair sum:**

```cpp
// a must be sorted
pair<int,int> twoSumSorted(const vector<int>& a, int target) {
    int l = 0, r = (int)a.size() - 1;
    while (l < r) {
        int sum = a[l] + a[r];
        if (sum == target) return {l, r};
        if (sum < target) l++;
        else r--;
    }
    return {-1, -1};
}
```

**Same direction, write pointer:**

```cpp
int removeElement(vector<int>& a, int val) {
    int k = 0;
    for (int i = 0; i < (int)a.size(); i++)
        if (a[i] != val) a[k++] = a[i];
    return k;
}
```

**Three pointers, Dutch national flag** (Sort Colors, one pass, O(1) space):

```cpp
void sortColors(vector<int>& a) {
    int low = 0, mid = 0, high = (int)a.size() - 1;
    while (mid <= high) {
        if (a[mid] == 0)      swap(a[low++], a[mid++]);
        else if (a[mid] == 1) mid++;
        else                  swap(a[mid], a[high--]);   // note: mid does NOT advance
    }
}
```

The invariant: everything before `low` is 0, everything between `low` and `mid` is 1, everything after `high` is 2. `mid` does not advance in the last case because the element swapped in from the back has not been examined yet. Missing that is the classic bug.

**Sort plus two pointers, the 3Sum shape:**

```cpp
vector<vector<int>> threeSum(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size();
    vector<vector<int>> res;
    for (int i = 0; i + 2 < n; i++) {
        if (i > 0 && a[i] == a[i-1]) continue;          // skip duplicate anchors
        int l = i + 1, r = n - 1;
        while (l < r) {
            long long sum = (long long)a[i] + a[l] + a[r];
            if (sum == 0) {
                res.push_back({a[i], a[l], a[r]});
                while (l < r && a[l] == a[l+1]) l++;     // skip duplicate lefts
                while (l < r && a[r] == a[r-1]) r--;     // skip duplicate rights
                l++; r--;
            }
            else if (sum < 0) l++;
            else r--;
        }
    }
    return res;
}
```

This is the single most important template in the section. It is O(n²), it is asked constantly, and the duplicate-skipping is where almost everyone gets it wrong. Note the three separate dedup steps: one for the anchor, two inside the match branch.

### 7. Example

Container With Most Water: `l` and `r` at the ends, area is `min(h[l], h[r]) × (r - l)`. Always move the **shorter** side inward. Why: the width can only shrink, so keeping the shorter wall guarantees the area can never improve. Moving the taller wall might reduce the height, and definitely reduces the width, so it can never help.

### 8. Complexity

| Shape | Time | Space |
|---|---|---|
| Opposite ends on sorted input | O(n) | O(1) |
| With a sort first | O(n log n) | O(1) or O(n) depending on sort |
| 3Sum (anchor + two pointers) | O(n²) | O(1) excluding output |
| Write pointer | O(n) | O(1) |

### 9. Must remember

1. Opposite-ends two pointers **requires sorted input** (or some other monotonic structure). On unsorted data the movement rule is meaningless.
2. `while (l < r)` versus `while (l <= r)`: use `<` when you need two *distinct* elements (pair sums, palindromes), `<=` when a single middle element is still meaningful (some search and partition problems). Getting this wrong is an off-by-one that passes small tests.
3. In Dutch national flag, do not advance `mid` after a swap with `high`. The incoming element is unexamined.
4. Dedup by skipping equal neighbours **after** sorting. Using a set to dedup works but costs a log factor and signals you did not see the cleaner approach.
5. Two pointers gives O(1) space; a hash map gives O(n) space but does not need sorting. If the problem asks for original indices, the hash map is usually the right call because sorting destroys them.
6. Sum of three `int`s can overflow. Cast to `long long` when the constraints allow large values.

### 10. Common mistakes

- Running opposite-ends two pointers on unsorted input.
- Forgetting to dedup in 3Sum, returning duplicate triplets.
- Advancing `mid` after the `high` swap in Dutch national flag.
- Moving the taller wall in Container With Most Water.
- Sorting when the problem needs original indices.
- Using `while (l <= r)` for a pair problem and comparing an element with itself.

### 11. Practice

- Two Sum II - Input Array Is Sorted (LC 167, Easy)
- Valid Palindrome (LC 125, Easy)
- Move Zeroes (LC 283, Easy)
- Container With Most Water (LC 11, Medium)
- Sort Colors (LC 75, Medium)
- 3Sum (LC 15, Medium)
- Trapping Rain Water (LC 42, Hard) — the two-pointer version, once the rest are solid

---

## 2.8 Sliding Window

This is the highest-yield pattern in the module. It gets extra space because there are two variants with genuinely different code shapes, and confusing them is the most common failure.

### 1. What is it?

A window `[l, r]` over a **contiguous** range. `r` expands to include new elements; `l` contracts to restore some property. Each index enters and leaves the window at most once, so the whole scan is O(n) despite the nested loop.

### 2. Why do we need it?

Checking every subarray is O(n²) to enumerate and O(n³) if you also recompute a sum for each. Sliding window reuses the previous window's work, turning the whole thing linear.

### 3. Core idea

```
Array:  [a, b, c, a, d, e]
         l--------r           window is s[l..r]

r moves right: add a[r] to the window state
l moves right: remove a[l] from the window state

Each index is added once and removed once  ->  O(n) total  (Module 1, Rule 6)
```

The window "state" is whatever you need to judge validity: a running sum, a frequency map, a count of distinct characters, a count of zeros.

### 4. Variant A: fixed-size window

The window is always exactly `k` wide. No `while` loop; you add one and drop one each step.

```cpp
// Maximum sum of any subarray of size k
long long maxSumK(const vector<int>& a, int k) {
    long long sum = 0, best = LLONG_MIN;
    for (int i = 0; i < (int)a.size(); i++) {
        sum += a[i];
        if (i >= k) sum -= a[i - k];       // drop the element leaving the window
        if (i >= k - 1) best = max(best, sum);  // window is full: record
    }
    return best;
}
```

The two guards are where the off-by-ones live. `i >= k` means the window has overflowed and the element at `i-k` must go. `i >= k-1` means the window is exactly full and the answer is valid.

### 5. Variant B: variable-size window (the important one)

The window grows and shrinks based on a condition. Two sub-shapes, and **which one you need depends on whether you want the longest or the shortest window**.

**B1 — Longest valid window: shrink while INVALID, record after shrinking.**

```cpp
int longestWindow(const vector<int>& a) {
    int l = 0, best = 0;
    /* window state */ long long cur = 0;

    for (int r = 0; r < (int)a.size(); r++) {
        cur += a[r];                          // 1. expand: include a[r]

        while (l <= r && isInvalid(cur)) {    // 2. shrink until valid again
            cur -= a[l];
            l++;
        }

        best = max(best, r - l + 1);          // 3. window is valid: record
    }
    return best;
}
```

**B2 — Shortest valid window: shrink while VALID, record inside the loop.**

```cpp
int shortestWindow(const vector<int>& a, int target) {
    int l = 0, best = INT_MAX;
    long long cur = 0;

    for (int r = 0; r < (int)a.size(); r++) {
        cur += a[r];                          // 1. expand

        while (cur >= target) {               // 2. while STILL valid
            best = min(best, r - l + 1);      // 3. record BEFORE shrinking
            cur -= a[l];
            l++;
        }
    }
    return best == INT_MAX ? 0 : best;
}
```

Memorise the distinction:

| Goal | `while` condition | Record the answer |
|---|---|---|
| **Longest** valid window | while **invalid**, shrink | **after** the while loop |
| **Shortest** valid window | while **valid**, shrink | **inside** the while loop |

Writing B1's shape for a "minimum size subarray" question gives wrong answers on every test. This single table saves more debugging time than anything else in the module.

### 6. How to recognise the pattern

Very strong signals:

- The word **"contiguous"**, or "subarray", or "substring".
- "Longest / shortest / maximum / minimum" combined with a constraint.
- "At most k distinct", "at most k replacements", "no repeating characters", "sum ≥ target", "contains all characters of t".
- All values non-negative, in sum-based window problems.

**The critical precondition for sum-based windows:** all values must be **non-negative**. With negative numbers, adding an element can *decrease* the sum, so shrinking no longer monotonically restores validity, and the whole argument collapses. Sum problems with negatives need prefix sums plus a hash map (Module 3) instead. Interviewers ask about this specifically.

Frequency-based windows (distinct characters, anagrams, replacements) do not have this restriction, because counts only ever go up when you expand.

### 7. Worked template: longest substring without repeating characters

```cpp
int lengthOfLongestSubstring(const string& s) {
    vector<int> count(128, 0);
    int l = 0, best = 0;

    for (int r = 0; r < (int)s.size(); r++) {
        count[s[r]]++;                        // expand

        while (count[s[r]] > 1) {             // invalid: a duplicate exists
            count[s[l]]--;                    // shrink from the left
            l++;
        }

        best = max(best, r - l + 1);          // record
    }
    return best;
}
```

Note the shrink condition checks only the character just added. That is sufficient, because the window was valid before this step, so `s[r]` is the only possible source of a duplicate.

### 8. Worked template: fixed window with frequency matching

Find All Anagrams in a String, the canonical fixed-window-plus-frequency problem:

```cpp
vector<int> findAnagrams(const string& s, const string& p) {
    int n = s.size(), k = p.size();
    vector<int> res;
    if (n < k) return res;

    vector<int> need(26, 0), have(26, 0);
    for (char c : p) need[c - 'a']++;

    for (int i = 0; i < n; i++) {
        have[s[i] - 'a']++;
        if (i >= k) have[s[i - k] - 'a']--;
        if (i >= k - 1 && have == need) res.push_back(i - k + 1);
    }
    return res;
}
```

`have == need` compares two 26-element vectors, which is O(26) = O(1). That constant-size comparison is what keeps this linear.

### 9. Complexity

| Variant | Time | Space |
|---|---|---|
| Fixed window | O(n) | O(1) or O(alphabet) |
| Variable window | O(n) | O(1) or O(distinct elements) |
| With a 26-array comparison per step | O(26n) = O(n) | O(1) |

Both pointers move forward only and each advances at most n times, so the total pointer movement is 2n. This is the amortisation argument from Module 1, Section 1.6, and you should be able to state it in one sentence.

### 10. Must remember

1. **Longest: shrink while invalid, record after. Shortest: shrink while valid, record inside.** The most valuable two lines in this module.
2. Sum-based sliding windows require **non-negative** values. With negatives, use prefix sum plus hash map.
3. Window length is `r - l + 1`. Off-by-one here is the second most common bug.
4. Sliding window is O(n), not O(n²), even though there is a `while` inside a `for`. Each index enters and leaves once.
5. When shrinking, always update the window state *before* incrementing `l`. Reversing those two lines corrupts the state silently.
6. For Longest Repeating Character Replacement, the window uses `windowLength - maxFreq > k` as the invalid test, where `maxFreq` is the count of the most frequent character. The subtlety is that `maxFreq` is never decreased; the window simply never shrinks below its best, which is correct because we only care about the maximum.
7. `have == need` on two `vector<int>` does element-wise comparison. Use it; hand-written 26-iteration loops are noise.

### 11. Common mistakes

- Using the "longest" shape for a "shortest" problem, or vice versa.
- Computing length as `r - l`.
- Applying a sum-based window to an array containing negatives.
- Forgetting to shrink at all, giving O(n²) or wrong answers.
- Updating `l` before removing `a[l]` from the state.
- On fixed windows, using `i >= k-1` and `i >= k` in the wrong places.
- Recomputing the window sum from scratch each step, which defeats the whole point.

### 12. Practice

- Maximum Average Subarray I (LC 643, Easy) — fixed window
- Longest Substring Without Repeating Characters (LC 3, Medium) — the canonical variable window
- Max Consecutive Ones III (LC 1004, Medium) — window with a budget
- Longest Repeating Character Replacement (LC 424, Medium) — the maxFreq subtlety
- Find All Anagrams in a String (LC 438, Medium) — fixed window + frequency
- Minimum Size Subarray Sum (LC 209, Medium) — the shortest-window shape
- Minimum Window Substring (LC 76, Hard) — the boss fight; do this last

---

## 2.9 Kadane's Algorithm

### 1. What is it?

A linear scan that finds the maximum-sum contiguous subarray. It is also your first dynamic program, three modules early.

### 2. Why do we need it?

Brute force over all subarrays is O(n²) with prefix sums, O(n³) without. Kadane is O(n) with O(1) space, and the reasoning generalises to a whole family of "best ending here" problems.

### 3. Core idea

Define `cur` = the maximum sum of a subarray **ending exactly at index i**. At each step there are only two options:

- Extend the previous best subarray: `cur + a[i]`
- Start fresh at `a[i]`: `a[i]`

Take the better one. The global answer is the maximum of `cur` over all `i`.

```
a   = [-2,  1, -3,  4, -1,  2,  1, -5,  4]
cur = [-2,  1, -2,  4,  3,  5,  6,  1,  5]
best=  -2   1   1   4   4   5   6   6   6   -> 6
```

The insight worth stating in an interview: **if the running sum ever goes negative, it can only hurt whatever comes next, so discard it and restart.** That is the whole algorithm.

### 4. When should I use it?

"Maximum sum subarray", "maximum product subarray" (with a twist), "best time to buy and sell stock" (which is Kadane on the difference array), and anything phrased as "the best contiguous run".

### 5. How to recognise the pattern

Signals: "maximum/largest sum", "contiguous subarray", "at least one element", an array that **contains negative numbers**. That last one matters: if all values are positive, the answer is trivially the whole array and the problem would not be asked.

### 6. C++ template

```cpp
long long maxSubArray(const vector<int>& a) {
    long long best = a[0], cur = a[0];       // start at a[0], NOT at 0
    for (int i = 1; i < (int)a.size(); i++) {
        cur = max((long long)a[i], cur + a[i]);
        best = max(best, cur);
    }
    return best;
}
```

**With indices**, when the problem asks which subarray:

```cpp
int bestL = 0, bestR = 0, curL = 0;
long long best = a[0], cur = a[0];
for (int i = 1; i < n; i++) {
    if (a[i] > cur + a[i]) { cur = a[i]; curL = i; }
    else cur += a[i];
    if (cur > best) { best = cur; bestL = curL; bestR = i; }
}
```

### 7. Example: Best Time to Buy and Sell Stock

```cpp
int maxProfit(const vector<int>& prices) {
    int minSoFar = INT_MAX, best = 0;
    for (int p : prices) {
        minSoFar = min(minSoFar, p);
        best = max(best, p - minSoFar);
    }
    return best;
}
```

This is Kadane in disguise: the maximum profit is the maximum-sum subarray of the daily differences. Recognising that connection is the kind of thing that lands well in an interview.

### 8. Complexity

O(n) time, O(1) space. Single pass, no extra storage.

### 9. Must remember

1. **Initialise `best = a[0]`, not `best = 0`.** With an all-negative array, initialising to 0 returns 0, which is wrong when the problem requires a non-empty subarray. This is the number-one Kadane bug.
2. Check whether the empty subarray is allowed. If it is, `best = 0` is correct. The problem statement decides; read it.
3. Use `long long` for the running sum when values are large.
4. Kadane is DP with the state `dp[i] = max sum ending at i`, space-optimised to a single variable. Saying this out loud shows you understand rather than recall.
5. **Maximum Product Subarray needs both a running max and a running min**, because a negative number swaps them. Do not try to adapt Kadane directly; track two variables and swap them when `a[i] < 0`.
6. Kadane assumes contiguity. For the non-contiguous version (maximum-sum subsequence) the answer is trivially the sum of all positive elements.

### 10. Common mistakes

- `best = 0` with all-negative input.
- Resetting `cur = 0` instead of `cur = a[i]` when restarting.
- Trying to use plain Kadane for maximum product.
- Forgetting `long long` and overflowing on large sums.
- Confusing subarray with subsequence.

### 11. Practice

- Maximum Subarray (LC 53, Medium)
- Best Time to Buy and Sell Stock (LC 121, Easy)
- Maximum Product Subarray (LC 152, Medium) — the min/max twist
- Maximum Sum Circular Subarray (LC 918, Medium) — optional, total minus minimum-subarray

---

## 2.10 Sorting-based techniques

### 1. What is it?

Not an algorithm but a move: sort first, and a hard problem becomes an easy scan. Module 5 covers how sorting works; this section is about when to reach for it.

### 2. Why do we need it?

Sorting costs O(n log n) once and buys you monotonicity, which unlocks two pointers, binary search, greedy scanning, and adjacency of duplicates. Very often the entire difficulty of a problem is "what order should I look at these in".

### 3. What sorting unlocks

| After sorting, you get | Which enables |
|---|---|
| Monotonic order | Two pointers, binary search |
| Duplicates become adjacent | O(n) dedup, `unique` |
| Extremes at the ends | Greedy pairing (largest with smallest) |
| Intervals in start order | Merge intervals, sweep line (Module 11) |
| Ability to compare neighbours | Closest pair, minimum difference |

### 4. How to recognise it

Signals: "find the k-th", "pairs with a given difference", "minimum difference between any two", "group by", "merge overlapping", "can you partition into pairs", "the answer does not depend on the input order". That last one is the general test: **if reordering the input cannot change the answer, sorting is free.**

The counter-signal: if the problem asks for **original indices**, sorting destroys them. Either store `(value, index)` pairs before sorting, or use a hash map instead.

### 5. C++ patterns

```cpp
sort(a.begin(), a.end());                      // ascending
sort(a.begin(), a.end(), greater<int>());      // descending

// Sort with indices preserved
vector<pair<int,int>> vp;
for (int i = 0; i < n; i++) vp.push_back({a[i], i});
sort(vp.begin(), vp.end());                    // by value, then index

// Dedup
sort(a.begin(), a.end());
a.erase(unique(a.begin(), a.end()), a.end());

// Coordinate compression (maps large values to 0..k-1)
vector<int> vals = a;
sort(vals.begin(), vals.end());
vals.erase(unique(vals.begin(), vals.end()), vals.end());
for (int& x : a) x = lower_bound(vals.begin(), vals.end(), x) - vals.begin();

// Minimum difference between any two elements
sort(a.begin(), a.end());
int best = INT_MAX;
for (int i = 1; i < n; i++) best = min(best, a[i] - a[i-1]);
```

Coordinate compression is worth knowing even now: it turns "values up to 10⁹" into "values up to n", which makes array-indexed techniques (frequency arrays, difference arrays, Fenwick trees) usable.

### 6. Complexity

`sort` is O(n log n). Anything you do after it is usually O(n), so the sort dominates. Always report it as the bottleneck: "O(n log n), dominated by the sort."

### 7. Must remember

1. Sorting destroys original indices. Store them explicitly if you need them.
2. Sorting is O(n log n), so if you need better than that overall, sorting is off the table. Check the constraints first.
3. `pair` sorts by first then second, so `sort` on `vector<pair<int,int>>` needs no comparator.
4. Comparators must use strict `<`, never `<=` (Module 0, Section C4).
5. The minimum difference between any two elements is always between **adjacent** elements after sorting. Obvious once stated, easy to miss.
6. When values are small and bounded, counting sort is O(n) and beats `sort`. Module 5 covers it.

### 8. Common mistakes

- Sorting when the problem needs original indices.
- Sorting inside a loop, turning O(n log n) into O(n² log n).
- Assuming `sort` is stable. It is not; use `stable_sort` if equal elements must keep their order.
- Sorting a `vector<vector<int>>` of intervals and forgetting that the default compares element by element, which happens to be the start-time order you wanted, but only by luck. Be explicit with a comparator.

### 9. Practice

- Merge Sorted Array (LC 88, Easy) — backward two pointers, no sort needed
- Minimum Absolute Difference (LC 1200, Easy)
- Two Sum II (LC 167, Easy) — sorted input as a gift
- 3Sum (LC 15, Medium) — sort to enable two pointers

---

# PART C — Matrices and 2D arrays

## 2.11 2D arrays

### Declaration and traversal

```cpp
vector<vector<int>> g(n, vector<int>(m, 0));

for (int i = 0; i < n; i++)
    for (int j = 0; j < m; j++)
        /* g[i][j] */;
```

**Row-major versus column-major matters for speed.** Iterating `i` then `j` walks contiguous memory; iterating `j` then `i` jumps `m` elements each step and thrashes the cache. Same asymptotics, several times the runtime on large matrices. Default to row-major.

### The four-direction idiom

You will write this in every grid problem from Module 12 onward:

```cpp
int dx[] = {-1, 1, 0, 0};
int dy[] = {0, 0, -1, 1};

for (int d = 0; d < 4; d++) {
    int ni = i + dx[d], nj = j + dy[d];
    if (ni < 0 || ni >= n || nj < 0 || nj >= m) continue;   // bounds first, always
    // visit g[ni][nj]
}
```

For eight directions (including diagonals), use `dx[] = {-1,-1,-1,0,0,1,1,1}` and `dy[] = {-1,0,1,-1,1,-1,0,1}`.

**Bounds check before access, every time.** Out-of-range access on a `vector<vector<int>>` is undefined behaviour, not an exception.

### Transpose and rotation

```cpp
// Transpose in place (square matrix only)
for (int i = 0; i < n; i++)
    for (int j = i + 1; j < n; j++)      // j starts at i+1, NOT 0
        swap(g[i][j], g[j][i]);

// Rotate 90 degrees clockwise = transpose, then reverse each row
for (auto& row : g) reverse(row.begin(), row.end());

// Rotate 90 counter-clockwise = transpose, then reverse the order of rows
reverse(g.begin(), g.end());
```

Starting `j` at `0` instead of `i+1` swaps every pair twice and leaves the matrix unchanged. That is the bug.

### Spiral traversal

```cpp
vector<int> spiralOrder(vector<vector<int>>& g) {
    vector<int> res;
    if (g.empty()) return res;
    int top = 0, bottom = g.size() - 1, left = 0, right = g[0].size() - 1;

    while (top <= bottom && left <= right) {
        for (int j = left; j <= right; j++) res.push_back(g[top][j]);
        top++;
        for (int i = top; i <= bottom; i++) res.push_back(g[i][right]);
        right--;
        if (top <= bottom) {                                   // guard
            for (int j = right; j >= left; j--) res.push_back(g[bottom][j]);
            bottom--;
        }
        if (left <= right) {                                   // guard
            for (int i = bottom; i >= top; i--) res.push_back(g[i][left]);
            left++;
        }
    }
    return res;
}
```

The two guards are mandatory. Without them, a single remaining row or column gets traversed twice. This is the entire difficulty of the problem and the reason it is asked.

### 2D prefix sum

```cpp
// Build: pre is (n+1) x (m+1)
vector<vector<long long>> pre(n + 1, vector<long long>(m + 1, 0));
for (int i = 0; i < n; i++)
    for (int j = 0; j < m; j++)
        pre[i+1][j+1] = g[i][j] + pre[i][j+1] + pre[i+1][j] - pre[i][j];

// Sum of the rectangle (r1,c1) to (r2,c2) inclusive: O(1)
long long rectSum(int r1, int c1, int r2, int c2) {
    return pre[r2+1][c2+1] - pre[r1][c2+1] - pre[r2+1][c1] + pre[r1][c1];
}
```

The `- pre[i][j]` in the build and the `+ pre[r1][c1]` in the query are inclusion-exclusion: the overlapping corner gets subtracted twice, so it must be added back once. Draw the rectangle if it does not click; it is a five-second sketch.

### Must remember

1. Row-major iteration (`i` outer, `j` inner) is cache-friendly. Prefer it.
2. Bounds-check before every grid access, and put the bounds check first in the condition so short-circuiting protects the access.
3. Transpose loop starts at `j = i + 1`.
4. Rotate clockwise = transpose + reverse each row. Counter-clockwise = transpose + reverse row order. Derive it once, then memorise.
5. Spiral traversal needs the two guards for the bottom row and left column.
6. 2D prefix sums are inclusion-exclusion: subtract two, add one back.
7. `vector<vector<int>> g(n)` creates n *empty* rows. Indexing `g[i][j]` on it is out of bounds. Always give the inner size.
8. A 10⁴ × 10⁴ `int` matrix is 400 MB. Check the memory budget before allocating.

### Common mistakes

- Transposing with `j = 0` and getting the original matrix back.
- Missing the spiral guards, emitting duplicated elements on single-row or single-column remainders.
- Accessing `g[i][j]` before the bounds check.
- Swapping the roles of `n` and `m` (rows versus columns). Name them `rows` and `cols` if you keep slipping.
- Using `g[0].size()` on a possibly empty grid.

### Practice

- Spiral Matrix (LC 54, Medium)
- Rotate Image (LC 48, Medium)
- Set Matrix Zeroes (LC 73, Medium) — the O(1)-space version uses the first row and column as markers
- Search a 2D Matrix (LC 74, Medium) — preview of Module 5, treat it as a flattened sorted array

---

# PART D — Strings

## 2.12 Strings are arrays

The central claim of this section: **you have already learned most string techniques.** A string is `vector<char>`. Two pointers, sliding window, prefix sums, and frequency counting all transfer unchanged. What follows is the handful of genuinely string-specific ideas.

### Palindrome

```cpp
bool isPalindrome(const string& s) {
    int l = 0, r = (int)s.size() - 1;
    while (l < r) {
        if (s[l] != s[r]) return false;
        l++; r--;
    }
    return true;
}
```

O(n) time, O(1) space. The version that reverses a copy and compares is O(n) space and a worse answer in an interview.

**With filtering** (Valid Palindrome, LC 125), the shape people get wrong:

```cpp
bool isPalindrome(const string& s) {
    int l = 0, r = (int)s.size() - 1;
    while (l < r) {
        while (l < r && !isalnum(s[l])) l++;      // inner guards need l < r too
        while (l < r && !isalnum(s[r])) r--;
        if (tolower(s[l]) != tolower(s[r])) return false;
        l++; r--;
    }
    return true;
}
```

The `l < r` inside the skip loops is not optional. Without it, a string of only punctuation runs off the end.

### Longest palindromic substring: expand around centre

```cpp
string longestPalindrome(const string& s) {
    int n = s.size(), bestL = 0, bestLen = 1;
    if (n == 0) return "";

    auto expand = [&](int l, int r) {
        while (l >= 0 && r < n && s[l] == s[r]) { l--; r++; }
        int len = r - l - 1;                     // l and r have overshot by one
        if (len > bestLen) { bestLen = len; bestL = l + 1; }
    };

    for (int c = 0; c < n; c++) {
        expand(c, c);        // odd length, centred on a character
        expand(c, c + 1);    // even length, centred between characters
    }
    return s.substr(bestL, bestLen);
}
```

O(n²) time, O(1) space. **You must handle both odd and even centres**; forgetting the even case is the standard bug and it fails on `"abba"`.

There is an O(n) algorithm (Manacher's). It is Tier 4 and essentially never required in placements. Knowing that it exists is enough; say so and move on.

### Anagram

```cpp
bool isAnagram(const string& s, const string& t) {
    if (s.size() != t.size()) return false;      // cheap early exit
    vector<int> freq(26, 0);
    for (char c : s) freq[c - 'a']++;
    for (char c : t) if (--freq[c - 'a'] < 0) return false;
    return true;
}
```

O(n) time, O(1) space (26 is a constant). The alternative, sorting both strings and comparing, is O(n log n) but is one line and perfectly acceptable if you say why it is slower.

**Canonical key for grouping**, which bridges to Module 3:

```cpp
// Key by sorted string: O(k log k) per word
string key = word;
sort(key.begin(), key.end());

// Key by frequency signature: O(k) per word
string key(26, '0');
for (char c : word) key[c - 'a']++;
```

### String building

```cpp
string res;
res.reserve(n);                 // optional but free
for (char c : s) res += c;      // O(1) amortised each, O(n) total

// NEVER:
for (char c : s) res = res + c; // O(n) each, O(n²) total
```

### Substrings and subsequences in strings

Same distinction as 2.3. `substr(i, len)` is O(len) and allocates, so generating all substrings explicitly is O(n³). Carry `(l, r)` indices instead whenever you can.

Number of substrings of a length-n string is `n(n+1)/2`. Number of distinct substrings requires a suffix structure (Tier 4).

### Must remember

1. Every array technique works on strings. Do not treat them as a separate category.
2. Palindrome check with two pointers is O(1) space. The reverse-and-compare version is O(n) space.
3. Expand-around-centre must handle odd **and** even centres.
4. `s += c` is amortised O(1); `s = s + c` is O(n). The second one turns loops quadratic.
5. `substr` allocates and copies. Avoid it inside loops; pass indices.
6. `freq[c - 'a']` assumes lowercase only. Use 128 entries when the constraints allow anything else.
7. Comparing two strings with `==` is O(n), not O(1).
8. `s.find(t)` returns `string::npos`, an unsigned value, not −1.

### Common mistakes

- Missing the even-length centre in longest-palindrome.
- Omitting the `l < r` guard in the filtered-palindrome skip loops.
- Building strings with `+` in a loop.
- Assuming lowercase input.
- Using `substr` to enumerate substrings, producing an extra factor of n.
- Comparing `s.find(t) >= 0`, which is always true.

### Practice

- Valid Palindrome (LC 125, Easy)
- Valid Anagram (LC 242, Easy)
- Longest Palindromic Substring (LC 5, Medium)
- Longest Common Prefix (LC 14, Easy)
- Group Anagrams (LC 49, Medium) — the canonical-key idea, revisited in Module 3

---

## 2.13 String hashing (basics)

### 1. What is it?

Mapping a string to an integer so that comparing two strings becomes comparing two numbers, in O(1) instead of O(n).

### 2. Why do we need it?

For placements: rarely. This section is **medium priority**, included because Rabin-Karp occasionally appears and because the idea underpins several Tier 4 techniques. If you are short on time, read the concept and skip the implementation.

### 3. Core idea: polynomial rolling hash

Treat the string as a number in base `B`, modulo a large prime `M`:

```
hash("abc") = (a·B² + b·B + c) mod M
```

Because it is positional and polynomial, the hash of a substring can be extracted from prefix hashes in O(1).

### 4. C++ template

```cpp
const long long B = 131, M = 1000000007LL;

// Precompute: O(n)
vector<long long> h(n + 1, 0), pw(n + 1, 1);
for (int i = 0; i < n; i++) {
    h[i + 1] = (h[i] * B + s[i]) % M;
    pw[i + 1] = pw[i] * B % M;
}

// Hash of s[l..r] inclusive: O(1)
long long sub(int l, int r) {
    long long res = (h[r + 1] - h[l] * pw[r - l + 1]) % M;
    return (res + M) % M;              // the modulo can go negative in C++
}
```

The `(res + M) % M` is mandatory. C++ `%` returns a negative result for negative operands (Module 0, Section A1), and skipping this line produces intermittent wrong answers that are painful to debug.

### 5. Complexity

O(n) precompute, O(1) per substring hash, O(n) space.

### 6. Must remember

1. Hash collisions are possible. Equal hashes mean *probably* equal strings. For contests, use two different moduli (double hashing) to make collisions negligible.
2. `(res + M) % M` after any subtraction. Non-negotiable.
3. Use `long long` throughout; `h[i] * B` overflows `int` immediately.
4. Choose `M` around 10⁹ and prime, `B` a prime larger than the alphabet size.
5. In an interview, the honest answer to "compare many substrings efficiently" is usually hashing *or* a suffix structure, and stating the collision caveat is what shows understanding.

### 7. Priority note

**Medium priority.** Know the concept and the collision caveat. Implement it once so it is not mysterious, then move on. Rabin-Karp, KMP, and Z-algorithm are covered in Module 15 with a priority classification.

---

## 2.14 Basic pattern matching

### The naive approach

```cpp
int naiveSearch(const string& s, const string& p) {
    int n = s.size(), m = p.size();
    for (int i = 0; i + m <= n; i++) {
        int j = 0;
        while (j < m && s[i + j] == p[j]) j++;
        if (j == m) return i;
    }
    return -1;
}
```

O(n·m) worst case, O(n + m) in practice on typical text. For n, m ≤ 10⁴ this is fine.

### What to use in practice

```cpp
size_t pos = s.find(p);
if (pos != string::npos) { /* found at pos */ }
```

`std::string::find` is O(n·m) worst case but heavily optimised. In an interview, using it is correct unless the question is explicitly about implementing pattern matching.

### Priority note

**KMP, Z-algorithm, and Rabin-Karp are Tier 3 to 4.** They are standard in competitive programming and occasionally asked at stronger product companies, almost always as "have you heard of it" rather than "implement it now". The right allocation for placement prep:

1. Know that naive matching is O(n·m).
2. Know that KMP achieves O(n + m) by precomputing a prefix-function array that tells you how far to jump on a mismatch, so the text pointer never moves backwards.
3. Implement one of them only after Tier 1 and Tier 2 are solid.

Module 15 revisits this with the full classification.

---

# PART E — Consolidation

## 2.15 Pattern recognition guide

This is the section to reread before a coding round.

### The decision flow

```
Is the answer a CONTIGUOUS range (subarray / substring)?
│
├─ YES
│   │
│   ├─ Asking for longest/shortest/count with a CONSTRAINT?
│   │   └─ All values non-negative, or constraint is frequency-based?
│   │       ├─ YES -> SLIDING WINDOW
│   │       └─ NO (negatives + sum) -> PREFIX SUM + HASHMAP (Module 3)
│   │
│   ├─ Asking for maximum/minimum SUM?
│   │   └─ KADANE
│   │
│   ├─ Many range-sum QUERIES, array static?
│   │   └─ PREFIX SUM
│   │
│   └─ Many range UPDATES, one read at the end?
│       └─ DIFFERENCE ARRAY
│
└─ NO (not contiguous)
    │
    ├─ Input sorted, or sorting is allowed?
    │   ├─ Looking for a pair/triplet with a sum property? -> SORT + TWO POINTERS
    │   └─ Need order/adjacency/extremes?                  -> SORT + SCAN
    │
    ├─ Need original indices, or O(n) required?
    │   └─ HASH MAP (Module 3)
    │
    └─ Is it a SUBSEQUENCE problem?
        └─ DYNAMIC PROGRAMMING (Module 13)
```

### Signal words table

| The statement says | Reach for | Why |
|---|---|---|
| "contiguous", "subarray", "substring" | Sliding window or prefix sum | Contiguity is the precondition |
| "longest/shortest ... such that" | Variable sliding window | Constraint + extremum = window |
| "at most k distinct / k replacements / k zeros" | Sliding window with a budget | The budget is the validity test |
| "subarray of size k" | Fixed sliding window | Size given up front |
| "maximum sum subarray" | Kadane | Textbook trigger |
| "sum of range l to r", "q queries" | Prefix sum | Static array, repeated queries |
| "add v to all elements in l..r" | Difference array | Updates dominate |
| "sorted array" + "pair/triplet" | Two pointers from both ends | Monotonicity enables the move rule |
| "in-place", "O(1) extra space" | Two pointers / write pointer / swapping | No room for auxiliary structures |
| "palindrome" | Two pointers, or expand around centre | Symmetry from both ends |
| "anagram", "permutation of" | Frequency array (26) | Order-independent comparison |
| "count occurrences", "duplicates" | Frequency counting | Direct |
| "subsequence" (not contiguous) | DP (Module 13) | 2ⁿ candidates |
| "k-th largest / smallest" | Sort, or heap (Module 10) | Partial order suffices |
| "minimum difference between any two" | Sort, then scan neighbours | Optimum is always adjacent |
| "merge overlapping intervals" | Sort by start, then scan (Module 11) | Order unlocks the greedy |

### The negative-numbers rule

Worth isolating because interviewers probe it:

| Problem shape | Values non-negative | Values may be negative |
|---|---|---|
| Longest subarray with sum ≤ target | Sliding window, O(n) | Prefix sum + map / other |
| Subarray with sum exactly K | Sliding window works | **Prefix sum + hashmap required** |
| Maximum sum subarray | Trivially the whole array | **Kadane** |

Sliding window needs the invariant that expanding increases the metric and shrinking decreases it. Negative numbers break that monotonicity. Say this in interviews; it is exactly the kind of precondition analysis that distinguishes strong candidates.

---

## 2.16 Comparison tables

### Two pointers vs sliding window

| | Two pointers (opposite) | Sliding window |
|---|---|---|
| Direction | Toward each other | Both forward |
| Requires sorted input | Usually yes | No |
| Answer shape | A pair, or a boundary | A contiguous range |
| Typical use | Pair sums, palindromes, area | Longest/shortest valid subarray |
| Complexity | O(n) | O(n) |

Sliding window is technically a two-pointer variant. Keeping them separate in your head is still useful because the recognition signals differ.

### Prefix sum vs difference array

| | Prefix sum | Difference array |
|---|---|---|
| Optimises | Range **queries** | Range **updates** |
| Build cost | O(n) | O(1) per update |
| Query / read cost | O(1) | O(n) once, at the end |
| Array must be | Static | Updated, then read once |
| Relationship | Inverses of each other | |

If you need both fast updates **and** fast queries, neither works. That is a Fenwick tree (Module 15, Tier 4).

### Frequency array vs hash map

| | `vector<int>(26)` | `unordered_map<int,int>` |
|---|---|---|
| Value range | Small and bounded | Any |
| Lookup | O(1), no hashing | O(1) average |
| Speed | Several times faster | Slower constant |
| Whole-container comparison | `==` in O(26) | Awkward |
| Use when | Letters, digits, bounded ints | Arbitrary values |

---

## 2.17 Must remember (consolidated)

The facts from this module most likely to cost you a submission.

1. **Longest window: shrink while invalid, record after. Shortest window: shrink while valid, record inside.**
2. Sum-based sliding windows require **non-negative** values.
3. Window length is `r - l + 1`.
4. Kadane initialises `best = a[0]`, never `0`, unless the empty subarray is allowed.
5. Prefix sums use `long long` and are sized `n+1` with `pre[0] = 0`.
6. Range sum `[l, r]` inclusive is `pre[r+1] - pre[l]`.
7. Difference arrays are sized `n+1` so `diff[r+1]` is always in bounds.
8. Opposite-ends two pointers requires sorted input.
9. 3Sum needs three separate duplicate-skips: the anchor, and both pointers after a match.
10. Dutch national flag does not advance `mid` after swapping with `high`.
11. Sliding window and two pointers are O(n), not O(n²). Each index enters and leaves once.
12. Transpose loops start at `j = i + 1`.
13. Rotate clockwise = transpose + reverse each row.
14. Spiral traversal needs guards before the bottom row and left column.
15. `s += c` is O(1) amortised; `s = s + c` is O(n).
16. `substr` is O(len) and allocates. Carry indices instead.
17. Expand-around-centre must handle both odd and even centres.
18. Subarray is contiguous; subsequence is not. The word "contiguous" is the fork in the road.
19. Always `k %= n` before rotating.
20. Sorting destroys original indices.

---

## 2.18 Common mistakes (consolidated)

**Wrong answer**
- Kadane initialised to 0 with all-negative input.
- Sliding window with the wrong shape (longest vs shortest).
- Sliding window applied to an array with negatives.
- Missing duplicate-skips in 3Sum.
- Missing the even-length centre in longest palindrome.
- Advancing `mid` after the `high` swap in Dutch flag.
- Transposing with `j = 0`.
- Missing spiral guards on the final row or column.
- Forgetting `k %= n` when rotating.

**Time limit exceeded**
- `erase` or `insert` inside a loop.
- `s = s + c` string building.
- `substr` inside a nested loop.
- Recomputing the window sum from scratch each step.
- Sorting inside a loop.

**Overflow**
- `int` prefix sums.
- `int` for the sum of three elements in 3Sum.
- Kadane's running sum in `int`.

**Runtime error**
- Missing `l < r` guard in filtered-palindrome skip loops.
- Grid access before the bounds check.
- `diff[r+1]` with the array sized `n`.
- `g[0].size()` on an empty grid.

---

## 2.19 Problem set

29 problems, layered. Each teaches something the others do not. Do them in order within each level.

### Level 1 — Concept (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Running Sum of 1d Array (LC 1480) | Easy | Prefix sum | The build loop, nothing else |
| Two Sum II - Sorted (LC 167) | Easy | Two pointers | Why sorted input lets you discard a whole row |
| Move Zeroes (LC 283) | Easy | Write pointer | In-place filtering without `erase` |
| Valid Palindrome (LC 125) | Easy | Two pointers on strings | The `l < r` guard inside skip loops |
| Maximum Subarray (LC 53) | Medium | Kadane | "Best ending here"; your first DP |

### Level 2 — Pattern (10)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Best Time to Buy and Sell Stock (LC 121) | Easy | Kadane variant | Recognising Kadane in disguise |
| Maximum Average Subarray I (LC 643) | Easy | Fixed window | The two guard conditions |
| Container With Most Water (LC 11) | Medium | Two pointers | The greedy move-the-shorter-wall argument |
| Product of Array Except Self (LC 238) | Medium | Prefix + suffix | Two-pass, no division, O(1) extra |
| Sort Colors (LC 75) | Medium | Three pointers | Dutch flag invariant |
| Rotate Array (LC 189) | Medium | Reversal trick | O(1)-space rotation |
| Longest Substring Without Repeating (LC 3) | Medium | Variable window | The canonical expand-shrink-record loop |
| Max Consecutive Ones III (LC 1004) | Medium | Window with budget | Constraint as a counter |
| Longest Repeating Char Replacement (LC 424) | Medium | Window + maxFreq | Why maxFreq need not decrease |
| Find All Anagrams in a String (LC 438) | Medium | Fixed window + freq | O(26) comparison keeps it linear |

### Level 3 — Interview (10)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| 3Sum (LC 15) | Medium | Sort + two pointers | Duplicate handling, the most-asked medium here |
| Minimum Size Subarray Sum (LC 209) | Medium | Shortest window | The other window shape |
| Merge Sorted Array (LC 88) | Easy | Backward two pointers | Writing from the end to avoid a buffer |
| Next Permutation (LC 31) | Medium | In-place manipulation | A precise multi-step array algorithm |
| Spiral Matrix (LC 54) | Medium | 2D boundaries | The two guards |
| Rotate Image (LC 48) | Medium | 2D transpose | Transpose + reverse |
| Set Matrix Zeroes (LC 73) | Medium | 2D, O(1) space | Using the array itself as storage |
| Longest Palindromic Substring (LC 5) | Medium | Expand around centre | Odd and even centres |
| Group Anagrams (LC 49) | Medium | Canonical key | Bridges into Module 3 |
| Subarray Sum Equals K (LC 560) | Medium | Prefix + hashmap | **Preview.** Attempt it, then revisit in Module 3 |

### Level 4 — Advanced (4, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Minimum Window Substring (LC 76) | Hard | Shortest window + freq | The hardest standard window problem |
| Trapping Rain Water (LC 42) | Hard | Two pointers / prefix max | Three valid approaches, compare them |
| Corporate Flight Bookings (LC 1109) | Medium | Difference array | The pattern in its pure form |
| Sliding Window Maximum (LC 239) | Hard | Monotonic deque | **Preview only.** Proper treatment in Module 7 |

**Do not grind past this list.** Twenty-nine problems done properly, with the pattern named out loud before coding, beats two hundred done mechanically. If you can solve all of Level 3 cold, this module is finished.

---

## Exit checklist

```
[ ] I can state the difference between subarray, subsequence, and subset
[ ] I write prefix sums with long long and n+1 sizing without thinking
[ ] I know range sum [l,r] = pre[r+1] - pre[l]
[ ] I can write a difference array and know why it's sized n+1
[ ] I can write opposite-ends two pointers and explain WHY the move is safe
[ ] I can write 3Sum with correct duplicate handling, from scratch
[ ] I know the Dutch flag invariant and why mid doesn't advance
[ ] I can write both sliding window shapes from memory
[ ] I know which shape is for longest and which is for shortest
[ ] I know sliding window needs non-negative values for sum problems
[ ] I can write Kadane and explain it as DP
[ ] I know why best = a[0] and not 0
[ ] I can transpose and rotate a matrix in place
[ ] I can write spiral traversal with the guards
[ ] I can write 2D prefix sum and explain the inclusion-exclusion
[ ] I can check a palindrome in O(1) space
[ ] I can write expand-around-centre with both centre types
[ ] I can name the pattern for an unseen array problem in under 60 seconds
[ ] Level 1 and 2 problems solved
[ ] Level 3 problems solved
```

The second-to-last box is the one that matters. Reread Section 2.15 until the mapping from signal words to technique is automatic.

---

## Next

Say **"Start Phase 3"** for Hashing (6–8 hours). It is a short module that pays off immediately: it closes out the array problems this module deliberately left open (Subarray Sum Equals K, and every "find a pair" problem on unsorted input), and it establishes the prefix-sum-plus-hashmap pattern that turns a whole family of O(n²) solutions linear.
