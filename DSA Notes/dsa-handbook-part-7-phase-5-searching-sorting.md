# DSA Placement Handbook (C++) — Part 7
# Phase 5: Searching and Sorting

**Module 5 · 12–15 hours · Tier 1 · Requires: Modules 0, 1, 2, 4**

---

## How to spend the 15 hours

Roughly: **4 hours on sorting, 11 on binary search.** That split is deliberate and not what most study plans do.

Sorting matters, but in an interview you will type `sort(v.begin(), v.end())` and move on. What gets tested about sorting is conceptual: stability, worst cases, when a non-comparison sort applies, and above all **recognising that sorting is the move that unlocks the actual solution**. You need to know merge sort and quick sort well enough to write and analyse them, which after Module 4 is a short job.

Binary search is the opposite. It is five lines long, everyone thinks they know it, and it produces more wrong submissions than any other single technique. Two reasons: the boundary conditions are genuinely fiddly, and **binary search on the answer** is a distinct skill that most candidates never learn to recognise. Section 5.11 is the highest-value section in this module and possibly in the first half of the handbook.

---

# PART A — Sorting

## 5.1 Sorting as an enabling move

Module 2.10 introduced this. The short version, because it is the thing you are actually tested on:

**Sorting is rarely the answer. It is what makes the answer possible.**

| After sorting you get | Which unlocks |
|---|---|
| Monotonic order | Two pointers, binary search |
| Duplicates adjacent | O(n) dedup, grouping |
| Extremes at the ends | Greedy pairing |
| Intervals in start order | Merge intervals, sweep line (Module 11) |
| Neighbour comparison valid | Minimum difference, closest pair |

The test for whether sorting is allowed: **if reordering the input cannot change the answer, sorting is free.** If the problem asks for original indices, sorting destroys them and you need a hash map or `(value, index)` pairs instead.

---

## 5.2 The quadratic sorts

You will not implement these in an interview. You will be asked *about* them. This section is the facts that get tested, compressed.

### Selection sort

Repeatedly find the minimum of the unsorted portion and swap it into place.

```cpp
for (int i = 0; i < n - 1; i++) {
    int minIdx = i;
    for (int j = i + 1; j < n; j++)
        if (a[j] < a[minIdx]) minIdx = j;
    swap(a[i], a[minIdx]);
}
```

O(n²) **always**, including on already-sorted input, because it scans the remaining array regardless. Not stable (the long-range swap can jump an equal element over another). Makes at most n−1 swaps, which is its one genuine advantage: if writes are expensive and comparisons are cheap, selection sort minimises writes.

### Bubble sort

Repeatedly swap adjacent out-of-order pairs so large elements "bubble" to the end.

```cpp
for (int i = 0; i < n - 1; i++) {
    bool swapped = false;
    for (int j = 0; j < n - 1 - i; j++)
        if (a[j] > a[j + 1]) { swap(a[j], a[j + 1]); swapped = true; }
    if (!swapped) break;                  // the early-exit flag
}
```

O(n²) worst and average. **O(n) best case, but only with the `swapped` flag.** Without it, bubble sort is O(n²) even on sorted input, and "what is bubble sort's best case" is a trick question that depends entirely on whether the flag is there. Stable.

### Insertion sort

Take each element and insert it into its correct place among those already sorted.

```cpp
for (int i = 1; i < n; i++) {
    int key = a[i], j = i - 1;
    while (j >= 0 && a[j] > key) { a[j + 1] = a[j]; j--; }
    a[j + 1] = key;
}
```

O(n²) worst, **O(n) best** on sorted or nearly-sorted input, stable, in place. This is the one that matters in practice: real sorting libraries, including `std::sort`, switch to insertion sort for small subarrays because its constant factor is tiny and its best case is common after partitioning.

### The comparison

| | Best | Average | Worst | Stable | Swaps | Notable |
|---|---|---|---|---|---|---|
| Selection | O(n²) | O(n²) | O(n²) | No | O(n) | Same cost on sorted input |
| Bubble | O(n) * | O(n²) | O(n²) | Yes | O(n²) | *only with the early-exit flag |
| Insertion | O(n) | O(n²) | O(n²) | Yes | O(n²) | Best on nearly-sorted; used inside real sorts |

### Must remember

1. Selection sort is O(n²) on already-sorted input. Bubble and insertion are O(n).
2. Bubble sort's O(n) best case requires the `swapped` flag. Without it there is no best case.
3. Selection sort is **not stable**; bubble and insertion are.
4. Selection sort minimises swaps (O(n)). That is its only real selling point.
5. Insertion sort is what production sorts fall back to for small arrays.

---

## 5.3 Merge Sort

### 1. What is it?

Divide the array in half, sort each half recursively, then merge the two sorted halves in linear time.

### 2. Why do we need it?

It is the guaranteed-O(n log n) comparison sort, it is stable, and its merge step is a reusable technique in its own right (counting inversions, merging k sorted lists, external sorting). It is also the cleanest illustration of divide and conquer, which is why it comes right after Module 4.

### 3. Core idea

```
              [5, 2, 8, 1, 9, 3]
             /                  \
      [5, 2, 8]              [1, 9, 3]
       /      \               /      \
    [5]     [2, 8]         [1]     [9, 3]
             /   \                  /   \
           [2]   [8]              [9]   [3]

  then merge upward:
           [2, 8]                [3, 9]
      [2, 5, 8]              [1, 3, 9]
              [1, 2, 3, 5, 8, 9]
```

The recursion does no work. **All the work is in the merge**, and merging two sorted lists is linear because you only ever compare the two front elements.

### 4. When should I use it?

- You need a **guaranteed** O(n log n), not an average one.
- You need **stability**.
- Linked lists: merge sort is the natural choice because it needs no random access (Module 6).
- Counting inversions, or any problem where the merge step can be instrumented to compute something.
- External sorting, where data does not fit in memory.

### 5. C++ template

```cpp
void mergeHalves(vector<int>& a, int lo, int mid, int hi) {
    vector<int> tmp;
    tmp.reserve(hi - lo + 1);
    int i = lo, j = mid + 1;

    while (i <= mid && j <= hi) {
        if (a[i] <= a[j]) tmp.push_back(a[i++]);   // <= preserves STABILITY
        else              tmp.push_back(a[j++]);
    }
    while (i <= mid) tmp.push_back(a[i++]);        // drain the leftovers
    while (j <= hi)  tmp.push_back(a[j++]);

    for (int k = 0; k < (int)tmp.size(); k++) a[lo + k] = tmp[k];
}

void mergeSort(vector<int>& a, int lo, int hi) {
    if (lo >= hi) return;                          // 0 or 1 element
    int mid = lo + (hi - lo) / 2;
    mergeSort(a, lo, mid);
    mergeSort(a, mid + 1, hi);
    mergeHalves(a, lo, mid, hi);
}
```

The `<=` in the merge is what makes it stable. With `<`, an element from the right half jumps ahead of an equal element from the left, and stability is gone. One character.

### 6. Why it is O(n log n)

T(n) = 2T(n/2) + O(n). From Module 4.6's table, or by the recursion tree: each level merges O(n) total elements, and there are log₂n levels. Every level does n work, so n log n. This is the explanation to give out loud.

### 7. Complexity

| | |
|---|---|
| Time | O(n log n) **in all cases** |
| Space | O(n) for the merge buffer, plus O(log n) stack |
| Stable | Yes |
| In place | No |

### 8. Must remember

1. O(n log n) best, average, and worst. No adversarial input exists.
2. **Stable**, provided the merge uses `<=`.
3. O(n) extra space is its cost. This is why `std::sort` uses introsort instead.
4. Merge sort is the preferred sort for **linked lists**: no random access needed, and the O(n) buffer disappears because you relink instead of copying.
5. The merge step generalises. Counting inversions is merge sort with a counter in the `else` branch: when `a[j]` is taken before `a[i]`, it is smaller than all of `a[i..mid]`, so add `mid - i + 1`.
6. `mergeSort(a, mid + 1, hi)`, never `mergeSort(a, mid, hi)`. The second recurses forever when `hi == lo + 1`.

### 9. Common mistakes

- Overlapping halves (`mid` instead of `mid + 1`), giving infinite recursion.
- Using `<` in the merge and silently losing stability.
- Forgetting one of the two drain loops.
- Copying back with the wrong offset: it is `a[lo + k]`, not `a[k]`.
- Allocating the temp buffer inside the merge for every call. Correct but slow; a single reused buffer is the optimisation.

### 10. Practice

- Sort an Array (LC 912) — implement merge sort, do not call `sort`
- Count Inversions (GeeksforGeeks) — the instrumented merge
- Merge Sorted Array (LC 88) — the merge step alone, backwards

---

## 5.4 Quick Sort

### 1. What is it?

Pick a pivot, partition the array so smaller elements are left of it and larger are right, then recurse on both sides. The pivot lands in its final position after partitioning.

### 2. Why do we need it?

It is in place (O(log n) space versus merge sort's O(n)), it has excellent cache behaviour, and its average case beats merge sort's constant factor. It is the default in most standard libraries for exactly these reasons. Its partition step also gives you **quickselect**, which finds the k-th smallest element in O(n) average.

### 3. Core idea

```
[5, 2, 8, 1, 9, 3]   pivot = 3

partition ->  [2, 1, | 3 | 8, 9, 5]
               <3       ^      >3
                     final position

then recurse on [2,1] and [8,9,5] independently
```

Unlike merge sort, **all the work is in the partition** and the combine step is nothing. The two algorithms are mirror images in that sense.

### 4. C++ template (Lomuto partition)

```cpp
int partition(vector<int>& a, int lo, int hi) {
    int pivot = a[hi];                             // pivot is the last element
    int i = lo;                                    // boundary of the "< pivot" region
    for (int j = lo; j < hi; j++)
        if (a[j] < pivot) swap(a[i++], a[j]);
    swap(a[i], a[hi]);                             // put the pivot in place
    return i;
}

void quickSort(vector<int>& a, int lo, int hi) {
    if (lo >= hi) return;
    int p = partition(a, lo, hi);
    quickSort(a, lo, p - 1);                       // pivot itself is EXCLUDED
    quickSort(a, p + 1, hi);
}
```

**Randomised pivot**, which is the fix for the worst case:

```cpp
int randomPartition(vector<int>& a, int lo, int hi) {
    int r = lo + rand() % (hi - lo + 1);
    swap(a[r], a[hi]);
    return partition(a, lo, hi);
}
```

### 5. The worst case

If the pivot is always the smallest or largest element, the partition splits into sizes 0 and n−1, giving T(n) = T(n−1) + O(n) = **O(n²)**.

When does this happen with the last-element pivot? On **already-sorted input**, which is the input people test with. That is the whole reason randomisation exists. Say this in an interview: "quicksort degrades to O(n²) on sorted input with a naive pivot, so you randomise or use median-of-three."

### 6. Quickselect

The k-th smallest element in O(n) average, by recursing on **one side only**:

```cpp
int quickSelect(vector<int>& a, int lo, int hi, int k) {   // k is 0-indexed
    if (lo == hi) return a[lo];
    int p = randomPartition(a, lo, hi);
    if (p == k) return a[p];
    if (k < p) return quickSelect(a, lo, p - 1, k);
    return quickSelect(a, p + 1, hi, k);
}
```

T(n) = T(n/2) + O(n) = **O(n)** average, O(n²) worst. This is the answer to "find the k-th largest without sorting", alongside the heap approach from Module 10. `std::nth_element` is this algorithm.

### 7. Complexity

| | |
|---|---|
| Time | O(n log n) average, **O(n²) worst** |
| Space | O(log n) average stack, O(n) worst |
| Stable | **No** |
| In place | Yes |

### 8. Must remember

1. Worst case is O(n²), triggered by sorted input with a naive pivot. Randomise.
2. **Not stable.** The partition swaps jump elements over each other.
3. In place: O(log n) space versus merge sort's O(n). This is the trade-off to state.
4. The pivot is in its final position after partitioning, which is why you recurse on `[lo, p-1]` and `[p+1, hi]`, excluding it.
5. Quickselect gives the k-th smallest in O(n) average by recursing on one side.
6. Lomuto partition (shown here) is simpler; Hoare partition is faster but fiddlier. Lomuto is fine for interviews.

### 9. Common mistakes

- Including the pivot in a recursive call (`quickSort(a, lo, p)`), causing infinite recursion.
- Claiming O(n log n) worst case.
- Using `a[j] <= pivot` in the partition loop, which breaks on arrays of all-equal elements by pushing everything to one side.
- Forgetting that it is unstable when the problem needs stability.

### 10. Practice

- Sort an Array (LC 912) — implement quick sort with a random pivot
- Kth Largest Element in an Array (LC 215) — quickselect, then compare with the heap solution in Module 10
- Sort Colors (LC 75) — revisit from Module 2; it is a specialised three-way partition

---

## 5.5 Non-comparison sorts

### The lower bound

Any sort that works by **comparing** elements needs Ω(n log n) comparisons in the worst case. The proof sketch: there are n! possible orderings, each comparison gives one bit, so you need at least log₂(n!) ≈ n log n comparisons.

Counting sort and radix sort beat this by not comparing at all. They index instead.

### Counting sort

```cpp
void countingSort(vector<int>& a, int maxVal) {
    vector<int> cnt(maxVal + 1, 0);
    for (int x : a) cnt[x]++;
    int idx = 0;
    for (int v = 0; v <= maxVal; v++)
        while (cnt[v]-- > 0) a[idx++] = v;
}
```

O(n + k) time and O(k) space, where k is the value range. **Only viable when k is comparable to n.** Sorting 10⁵ values in the range 0 to 10⁹ would allocate a billion counters.

Where it genuinely wins: sorting ages, exam scores, characters, small bounded IDs. It is also how "sort by frequency" problems get to O(n) (bucket by count).

### Radix sort

Sort by the least significant digit first, then the next, using a stable sort at each pass. O(d × (n + b)) where d is the number of digits and b the base.

Worth knowing exists. **Rarely implemented in placements.** The one fact that gets asked: radix sort requires a **stable** sort at each digit pass, otherwise earlier passes are undone.

### Must remember

1. Comparison sorting is Ω(n log n). Counting and radix escape it by not comparing.
2. Counting sort is O(n + k) and only sensible when k is small. Check the value range before proposing it.
3. Counting sort is stable if implemented with a prefix-sum placement pass; the simple version above loses identity but is fine for plain integers.
4. Radix sort needs a stable per-digit sort.
5. "Can you sort faster than n log n?" → "Not by comparing. If the values are bounded integers, counting sort is O(n + k)." That is the complete answer.

### Priority

**Counting sort: know it and be able to write it.** It appears in Top K Frequent Elements and other bucket problems. **Radix sort: know the concept only.** Medium-to-low priority for placements.

---

## 5.6 std::sort in practice

```cpp
sort(v.begin(), v.end());                        // ascending
sort(v.begin(), v.end(), greater<int>());        // descending
stable_sort(v.begin(), v.end());                 // stable, O(n) extra memory
partial_sort(v.begin(), v.begin() + k, v.end()); // smallest k in order, O(n log k)
nth_element(v.begin(), v.begin() + k, v.end());  // k-th in place, O(n) average
```

### What `std::sort` actually is

**Introsort**: quicksort until the recursion gets too deep, then heapsort as a fallback, with insertion sort for small subarrays. The heapsort fallback is what gives C++ its O(n log n) **guarantee** despite using quicksort. Not stable.

This is a good interview answer: "`std::sort` is introsort, so it gets quicksort's constant factor with heapsort's worst-case guarantee."

### Custom comparators

Covered fully in Module 0, Section C4. The two rules that cost submissions:

1. **Use strict `<` or `>`, never `<=`.** A comparator that returns true for equal elements violates strict weak ordering and makes `std::sort` read out of bounds. It crashes at scale and passes on small tests.
2. Take parameters by `const&` for non-trivial types.

```cpp
// Sort by frequency descending, ties by value ascending
sort(v.begin(), v.end(), [&](int a, int b) {
    if (freq[a] != freq[b]) return freq[a] > freq[b];
    return a < b;
});
```

### Sorting comparison table

| Algorithm | Best | Average | Worst | Space | Stable | In place | Use when |
|---|---|---|---|---|---|---|---|
| Selection | O(n²) | O(n²) | O(n²) | O(1) | No | Yes | Writes are expensive |
| Bubble | O(n)* | O(n²) | O(n²) | O(1) | Yes | Yes | Teaching only |
| Insertion | O(n) | O(n²) | O(n²) | O(1) | Yes | Yes | Small or nearly-sorted |
| Merge | O(n log n) | O(n log n) | O(n log n) | O(n) | **Yes** | No | Guarantees, stability, linked lists |
| Quick | O(n log n) | O(n log n) | **O(n²)** | O(log n) | No | Yes | General purpose, in place |
| Heap | O(n log n) | O(n log n) | O(n log n) | O(1) | No | Yes | Guarantees with O(1) space (Module 10) |
| Counting | O(n+k) | O(n+k) | O(n+k) | O(k) | Yes† | No | Small bounded integer range |
| `std::sort` | O(n log n) | O(n log n) | O(n log n) | O(log n) | No | Yes | Always, in practice |

\* with the early-exit flag. † with the prefix-sum placement version.

---

## 5.7 Recognising "sort plus something"

You asked for heavy emphasis here, so this is its own section.

The skill is noticing that a problem becomes easy **after** sorting, when it looks hard before. The signal is usually that the problem is about **relationships between elements** rather than their positions.

| Problem shape | After sorting, use | Example |
|---|---|---|
| Pair/triplet with a target sum | Two pointers | 3Sum, Two Sum II |
| Minimum difference between any two | Scan adjacent pairs | Minimum Absolute Difference |
| Group equal or equivalent items | Scan, or `unique` | Dedup, Group by value |
| Overlapping ranges | Sweep in start order | Merge Intervals (Module 11) |
| "Maximum number of non-overlapping" | Greedy by end time | Activity Selection (Module 11) |
| "Can I pair everything up" | Two pointers from both ends | Boats to Save People |
| "k-th largest / smallest" | `nth_element`, or a heap | Kth Largest |
| "Count elements less than x" per query | Binary search on the sorted array | Various |
| Values bounded and small | Counting sort / bucketing | Top K Frequent |
| "Closest value to x" | Binary search | Search Insert Position |

### The test

Ask: **"if I shuffled the input, would the answer change?"**

- No → sorting is free, and is probably the move.
- Yes → the answer depends on position, so sorting destroys information. You need a hash map, a prefix sum, or a scan.

### When not to sort

- Original indices are part of the answer (Two Sum, not Two Sum II).
- You need O(n) and n log n is too slow (rare at interview constraints, common on Codeforces).
- The data arrives as a stream.
- Only the k largest matter, and k is small: a heap is O(n log k) which beats O(n log n).

---

# PART B — Binary Search

## 5.8 Binary search fundamentals

### 1. What is it?

Repeatedly halve a search space by using a property that lets you discard one half with certainty.

### 2. Why do we need it?

O(log n) instead of O(n). At n = 10⁹ that is 30 steps instead of a billion. But the deeper reason is that binary search generalises far past "find a value in a sorted array", and that generalisation (Section 5.11) is where most of the interview value lives.

### 3. Core idea

```
a = [1, 3, 5, 7, 9, 11, 13]   target = 11

lo=0, hi=6, mid=3 -> a[3]=7  < 11  ->  discard [0..3], lo=4
lo=4, hi=6, mid=5 -> a[5]=11 == 11 ->  found
```

The guarantee that makes it correct: **the array is sorted, so `a[mid] < target` implies every element at or before `mid` is also less than the target.** You are not guessing; you are proving half the array irrelevant.

### 4. The exact-match template

```cpp
int binarySearch(const vector<int>& a, int target) {
    int lo = 0, hi = (int)a.size() - 1;          // INCLUSIVE range [lo, hi]
    while (lo <= hi) {                            // <= because [x,x] is non-empty
        int mid = lo + (hi - lo) / 2;             // overflow-safe
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;        // mid EXCLUDED
        else                 hi = mid - 1;        // mid EXCLUDED
    }
    return -1;
}
```

Three things make this correct, and all three are where bugs come from:

**The invariant.** `[lo, hi]` is inclusive, so a single-element range `[5,5]` is still a valid search space. That is why the condition is `lo <= hi` and not `lo < hi`.

**Progress.** Both updates use `mid + 1` or `mid - 1`, never `mid`. If you write `lo = mid` and the range shrinks to two elements, `mid` computes to `lo` and nothing changes: infinite loop.

**Overflow safety.** `lo + (hi - lo) / 2`, never `(lo + hi) / 2`. With large indices the sum overflows `int`.

### 5. The template I actually recommend

The exact-match version above only answers "is it there". Most real questions are boundary questions: first occurrence, last occurrence, first element ≥ x, minimum feasible value. The following **"store the answer" template handles all of them uniformly**, and it is what I would have you memorise:

```cpp
// Find the FIRST index in [lo, hi] where pred(i) is true.
// Requires pred to be monotonic: false, false, ..., false, true, true, ..., true
int firstTrue(int lo, int hi) {
    int ans = hi + 1;                    // sentinel: "no such index"
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (pred(mid)) {
            ans = mid;                   // record this candidate
            hi = mid - 1;                // and look for an earlier one
        } else {
            lo = mid + 1;
        }
    }
    return ans;
}
```

Why this is better than clever `lo < hi` variants: it is **impossible to get an off-by-one wrong**. The loop always terminates (both branches move a pointer past `mid`), and the answer is whatever you last recorded. You never have to reason about whether `lo` or `hi` holds the answer at the end.

The mirror version for "last index where `pred` is true": record and set `lo = mid + 1`.

### 6. Complexity

O(log n) time, O(1) space iterative, O(log n) space recursive. Prefer iterative.

### 7. Must remember

1. `mid = lo + (hi - lo) / 2`. Never `(lo + hi) / 2`.
2. `lo <= hi` with an inclusive range. `lo < hi` with an inclusive range skips the last element.
3. Both updates must exclude `mid`, or the loop can hang.
4. The array **must be sorted** for the plain version. `lower_bound` and friends silently return garbage on unsorted input.
5. The "store the answer" template removes the entire class of boundary bugs. Learn one template properly rather than four fragile ones.
6. Binary search needs a **monotonic predicate**, not literally a sorted array. That distinction is Section 5.10.

### 8. Common mistakes

- `(lo + hi) / 2` overflowing.
- `lo = mid` or `hi = mid` with an inclusive range, causing an infinite loop.
- `lo < hi` where `lo <= hi` was needed, missing the last element.
- Running binary search on unsorted input.
- Returning `lo` or `hi` at the end and guessing which one is right. Use the stored answer instead.

---

## 5.9 lower_bound, upper_bound, and occurrences

### The definitions

On a **sorted** array:

| Function | Returns |
|---|---|
| `lower_bound(x)` | First index with `a[i] >= x` |
| `upper_bound(x)` | First index with `a[i] > x` |

Both return `a.end()` (or index `n`) if no such element exists.

```
a =     [1, 3, 3, 3, 5, 7]
index:   0  1  2  3  4  5

lower_bound(3) -> index 1      upper_bound(3) -> index 4
lower_bound(4) -> index 4      upper_bound(4) -> index 4
lower_bound(9) -> index 6      upper_bound(9) -> index 6
```

### The derived queries

```cpp
int lb = lower_bound(a.begin(), a.end(), x) - a.begin();
int ub = upper_bound(a.begin(), a.end(), x) - a.begin();

int count      = ub - lb;                         // occurrences of x
int firstOcc   = (lb < n && a[lb] == x) ? lb : -1;
int lastOcc    = (ub > lb) ? ub - 1 : -1;
int countLess  = lb;                              // elements strictly < x
int countLessEq= ub;                              // elements <= x
```

`ub - lb` for the count is worth memorising. It appears constantly.

### Writing them yourself

Interviewers sometimes ask you to implement these rather than call them. With the `firstTrue` template it is two lines of difference:

```cpp
// lower_bound: first index where a[i] >= x
int lowerBound(const vector<int>& a, int x) {
    int lo = 0, hi = (int)a.size() - 1, ans = a.size();
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] >= x) { ans = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return ans;
}

// upper_bound: change >= to >
```

That is the whole difference between them: `>=` versus `>`. Being able to say that cleanly is a good sign in an interview.

### Must remember

1. `lower_bound` is `>=`; `upper_bound` is `>`. One character apart.
2. Count of `x` is `upper_bound - lower_bound`.
3. Last occurrence is `upper_bound - 1`, and only valid if `upper_bound > lower_bound`.
4. Both require **sorted** input and both return `end()` when nothing qualifies. Check before dereferencing.
5. On a `set` or `map`, use the **member** `s.lower_bound(x)`. The free function is O(n) on those containers (Module 0, Section B6).
6. To search descending-sorted data, pass `greater<int>()` as the fourth argument, or negate the values.

### Practice

- Find First and Last Position of Element in Sorted Array (LC 34, Medium)
- Search Insert Position (LC 35, Easy) — this is exactly `lower_bound`

---

## 5.10 Binary search on a monotonic predicate

This is the conceptual bridge to the next section, and it is short but important.

### The generalisation

Binary search does not need a sorted array. It needs a **monotonic predicate**: a yes/no question whose answer flips exactly once as you move across the search space.

```
index:  0  1  2  3  4  5  6  7
pred:   F  F  F  F  T  T  T  T
                    ^
              the boundary you are finding
```

A sorted array is just the special case where `pred(i)` is `a[i] >= target`, which is monotonic *because* the array is sorted.

Once you see it this way, three things become searchable that do not look sorted at all:

| Search space | Predicate | Problem |
|---|---|---|
| Array indices | `a[i] >= x` | Standard binary search |
| Array indices | `a[i] > a[i+1]` | Find Peak Element |
| Answer values | `feasible(v)` | Binary search on answer (5.11) |
| Time | `possible by time t` | Scheduling problems |

### Find Peak Element (LC 162)

The clearest example of binary search on unsorted input.

```cpp
int findPeakElement(const vector<int>& a) {
    int lo = 0, hi = (int)a.size() - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < a[mid + 1]) lo = mid + 1;   // ascending: a peak lies right
        else                     hi = mid;        // descending or peak: mid or left
    }
    return lo;
}
```

**Why this works on completely unsorted data.** The invariant is not "the array is sorted", it is "**a peak exists somewhere in `[lo, hi]`**". If `a[mid] < a[mid+1]`, then the right side is ascending from `mid+1`, and an ascending run must eventually peak (either at a local maximum or at the array's edge). So a peak exists in `[mid+1, hi]` and the left half can be discarded.

Note this uses `lo < hi` with `hi = mid`, not the inclusive template. That is correct here because the range always contains an answer, so it can safely shrink to a single element. Two valid templates exist; know which one you are using.

### Must remember

1. Binary search needs monotonicity, not sortedness.
2. If you can phrase a yes/no question that goes F...F T...T across the space, you can binary search it.
3. Find Peak Element works on unsorted input. Being able to explain why is a strong interview moment.
4. When the search space is guaranteed to contain the answer, `lo < hi` with `hi = mid` is safe. When it might not, use the inclusive template with a stored answer.

---

## 5.11 Binary Search on the Answer

**The highest-value section in this module.** Most candidates never learn to recognise this, and it turns problems that look like hard optimisation or DP into fifteen lines.

### 1. What is it?

Instead of searching an array for a value, you search the **range of possible answers**, asking a feasibility question at each step.

### 2. Why do we need it?

Because a large family of problems phrased as "find the minimum X such that Y is achievable" have no obvious greedy or DP solution, but do have an easy *checking* function. If checking is easy and the feasibility is monotonic, you binary search the answer space and get O(n log(range)).

### 3. Core idea

```
Answer space:  1   2   3   4   5   6   7   8   9  10
can(x)?        F   F   F   F   T   T   T   T   T   T
                               ^
                          the answer

can(x) is monotonic: if capacity 5 works, capacity 6 certainly works.
So binary search the answer space instead of the input array.
```

Two conditions must hold, and you should verify both explicitly before committing:

1. **Feasibility is monotonic.** If `x` works, every larger `x` works (or every smaller, for maximisation problems).
2. **You can check feasibility efficiently**, usually in O(n) with a greedy pass.

### 4. How to recognise the pattern

This is the part to internalise. Signals:

- "**Minimum** X such that..." or "**maximum** X such that..."
- "Minimise the **maximum**" or "maximise the **minimum**"
- "Smallest capacity / speed / divisor / time that allows..."
- The answer is a **number in a range**, not an element of the array.
- A greedy check is obvious, but constructing the optimum directly is not.
- Constraints have a large answer range (up to 10⁹) but a small array (10⁵). That mismatch is a tell: O(n log(range)) is exactly the intended complexity.

**"Minimise the maximum" and "maximise the minimum" are almost always this pattern.** If you see either phrase, start here.

### 5. The template

```cpp
// Minimise x subject to can(x)
int lo = MIN_POSSIBLE, hi = MAX_POSSIBLE, ans = -1;
while (lo <= hi) {
    int mid = lo + (hi - lo) / 2;
    if (can(mid)) { ans = mid; hi = mid - 1; }   // feasible: try smaller
    else           lo = mid + 1;                  // infeasible: need bigger
}
return ans;
```

It is the `firstTrue` template from 5.8 with the predicate being feasibility. **Learn one template, apply it everywhere.**

For maximisation, flip: `if (can(mid)) { ans = mid; lo = mid + 1; }`.

### 6. Worked example: Koko Eating Bananas (LC 875)

*Koko eats bananas from piles at speed k per hour, one pile at a time. Find the minimum k that lets her finish all piles within h hours.*

**Answer space:** k from 1 to `max(piles)`. Eating faster than the largest pile is pointless.

**Feasibility:** at speed k, pile p takes `ceil(p / k)` hours. Sum them and compare to h.

**Monotonic?** Higher speed means fewer or equal hours. Yes.

```cpp
int minEatingSpeed(const vector<int>& piles, int h) {
    auto hoursNeeded = [&](int k) {
        long long total = 0;
        for (int p : piles) total += (p + k - 1) / k;     // ceil division
        return total;
    };

    int lo = 1, hi = *max_element(piles.begin(), piles.end()), ans = hi;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (hoursNeeded(mid) <= h) { ans = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return ans;
}
```

O(n log(max pile)). The ceiling-division idiom `(p + k - 1) / k` is worth memorising; it appears in nearly every problem in this family.

### 7. Worked example: Split Array Largest Sum (LC 410)

*Split an array into k contiguous subarrays, minimising the largest subarray sum.*

This looks like a DP problem, and there is an O(n²k) DP solution. Binary search on the answer gives O(n log(sum)) in fifteen lines.

**Answer space:** from `max(a)` (a single element must fit) to `sum(a)` (one subarray).

**Feasibility:** given a cap, greedily fill subarrays until adding the next element would exceed it, then start a new one. Count the subarrays used; feasible if that count ≤ k.

```cpp
int splitArray(const vector<int>& a, int k) {
    auto piecesNeeded = [&](long long cap) {
        int pieces = 1;
        long long cur = 0;
        for (int x : a) {
            if (cur + x > cap) { pieces++; cur = x; }
            else cur += x;
        }
        return pieces;
    };

    long long lo = *max_element(a.begin(), a.end());
    long long hi = accumulate(a.begin(), a.end(), 0LL);
    long long ans = hi;
    while (lo <= hi) {
        long long mid = lo + (hi - lo) / 2;
        if (piecesNeeded(mid) <= k) { ans = mid; hi = mid - 1; }
        else lo = mid + 1;
    }
    return (int)ans;
}
```

The lower bound is `max(a)`, not 0. A cap below the largest element makes the problem infeasible at any k, and starting from 0 either wastes iterations or produces an infinite loop depending on your `can` function. **Getting the bounds right is half of these problems.**

### 8. The family

Once you see the shape, these all look identical:

| Problem | Answer space | Feasibility check |
|---|---|---|
| Koko Eating Bananas (875) | Speed 1..max pile | Hours needed ≤ h |
| Capacity to Ship Packages (1011) | max(w)..sum(w) | Days needed ≤ D |
| Split Array Largest Sum (410) | max(a)..sum(a) | Pieces needed ≤ k |
| Minimum Days to Make Bouquets (1482) | 1..max(bloomDay) | Bouquets makeable ≥ m |
| Find Smallest Divisor (1283) | 1..max(a) | Sum of ceilings ≤ threshold |
| Aggressive Cows (GFG) | 1..max−min | Cows placeable ≥ c (maximise) |
| Sqrt(x) (LC 69) | 0..x | mid × mid ≤ x |

### 9. Complexity

O(n × log(range)), where the log is over the **answer range**, not the array size. With a range up to 10⁹ that log is about 30, so the whole thing is roughly 30 passes over the array.

### 10. Must remember

1. **Verify monotonicity before you commit.** If feasibility is not monotonic, this does not apply and you will get plausible wrong answers.
2. Get the bounds right. `lo` is usually the minimum that could possibly work (often `max(a)`, not 0), `hi` the trivially-sufficient value (often `sum(a)`).
3. Use the stored-answer template. Do not try to return `lo` and reason about which side it landed on.
4. Ceiling division is `(p + k - 1) / k`. Memorise it.
5. Use `long long` for the bounds when they come from a sum.
6. "Minimise the maximum" and "maximise the minimum" are the two phrases that should trigger this immediately.
7. The feasibility check is usually a simple greedy pass. If checking is as hard as solving, this is the wrong pattern.

### 11. Common mistakes

- Applying it to a non-monotonic feasibility function.
- Starting `lo` at 0 or 1 when the true minimum is `max(a)`.
- Integer division instead of ceiling division in the check.
- Overflow in `sum(a)` as the upper bound.
- Getting the direction backwards on maximisation problems (recording then moving `hi` instead of `lo`).
- Not recognising the pattern at all, and spending twenty minutes on a DP that is not needed.

### 12. Practice

Do these in order. They are nearly the same problem four times, which is the point.

- Sqrt(x) (LC 69, Easy) — the simplest possible answer space
- Koko Eating Bananas (LC 875, Medium) — the canonical one
- Capacity to Ship Packages Within D Days (LC 1011, Medium) — same shape, different story
- Split Array Largest Sum (LC 410, Hard) — looks like DP, is not
- Aggressive Cows (GeeksforGeeks) — the maximisation direction

---

## 5.12 Rotated sorted arrays

### 1. What is it?

A sorted array rotated at an unknown pivot: `[4,5,6,7,0,1,2]`. Still searchable in O(log n), because **at least one half is always properly sorted**.

### 2. Core idea

```
[4, 5, 6, 7, 0, 1, 2]
 lo       mid       hi

a[lo]=4 <= a[mid]=7  ->  LEFT half [4,5,6,7] is sorted
                          so we can test the target against its range exactly
```

At every step, compare `a[lo]` with `a[mid]` to decide which half is sorted. Then check whether the target falls inside that sorted half's range. If yes, search there; if no, search the other half.

### 3. Search in Rotated Sorted Array (LC 33)

```cpp
int search(const vector<int>& a, int target) {
    int lo = 0, hi = (int)a.size() - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;

        if (a[lo] <= a[mid]) {                          // left half is sorted
            if (a[lo] <= target && target < a[mid]) hi = mid - 1;
            else                                    lo = mid + 1;
        } else {                                        // right half is sorted
            if (a[mid] < target && target <= a[hi]) lo = mid + 1;
            else                                    hi = mid - 1;
        }
    }
    return -1;
}
```

The `<=` in `a[lo] <= a[mid]` matters: when the range has two elements, `mid == lo`, and `<` would send you down the wrong branch.

### 4. Find Minimum in Rotated Sorted Array (LC 153)

```cpp
int findMin(const vector<int>& a) {
    int lo = 0, hi = (int)a.size() - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] > a[hi]) lo = mid + 1;     // min is strictly right of mid
        else                hi = mid;          // mid could BE the min
    }
    return a[lo];
}
```

**Compare against `a[hi]`, not `a[lo]`.** This is the detail that catches people. Comparing with `a[lo]` fails on a non-rotated array like `[1,2,3,4,5]`: there `a[mid] > a[lo]` suggests going right, but the minimum is at index 0. Comparing with `a[hi]` handles the non-rotated case correctly with no special-casing.

Note `hi = mid`, not `mid - 1`, because `mid` itself might be the minimum.

### 5. With duplicates (LC 81, LC 154)

When `a[lo] == a[mid] == a[hi]`, you cannot tell which half is sorted. The only safe move is to shrink by one:

```cpp
if (a[lo] == a[mid] && a[mid] == a[hi]) { lo++; hi--; continue; }
```

This makes the **worst case O(n)**, for example on `[1,1,1,1,1,0,1]`. That is unavoidable, and stating it is the expected answer: "with duplicates, the worst case degrades to O(n) because equal endpoints give no information."

### 6. Must remember

1. At least one half of a rotated sorted array is always sorted. Identify which, then test the target against its range.
2. `a[lo] <= a[mid]` with `<=`, for the two-element case.
3. For finding the minimum, compare with `a[hi]`, never `a[lo]`.
4. `hi = mid`, not `mid - 1`, when `mid` might be the answer.
5. Duplicates break the O(log n) guarantee. Worst case O(n).
6. An alternative approach is to find the pivot first, then binary search the correct segment. It is two passes but easier to reason about, and it is a perfectly good interview answer.

### 7. Common mistakes

- Using `<` instead of `<=` when testing which half is sorted.
- Comparing with `a[lo]` in the find-minimum version.
- `hi = mid - 1` where `hi = mid` was needed, skipping the answer.
- Claiming O(log n) with duplicates present.

### 8. Practice

- Find Minimum in Rotated Sorted Array (LC 153, Medium) — do this **before** LC 33
- Search in Rotated Sorted Array (LC 33, Medium)
- Search in Rotated Sorted Array II (LC 81, Medium) — the duplicates case

---

## 5.13 Search in a 2D matrix

Two different problems that look identical. Read the constraints carefully.

### Type 1: fully sorted (LC 74)

Each row is sorted, and the first element of each row exceeds the last of the previous row. The matrix is one sorted array folded into a grid.

```cpp
bool searchMatrix(const vector<vector<int>>& g, int target) {
    int n = g.size(), m = g[0].size();
    int lo = 0, hi = n * m - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        int val = g[mid / m][mid % m];              // flatten: row = mid/m, col = mid%m
        if (val == target) return true;
        if (val < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return false;
}
```

O(log(n·m)). The `mid / m` and `mid % m` conversion is the whole trick.

### Type 2: rows and columns sorted independently (LC 240)

Each row is sorted left to right and each column top to bottom, but rows do not chain. Flattening does not give a sorted array, so binary search on the flattened index is wrong.

The answer is the **staircase walk** from the top-right corner:

```cpp
bool searchMatrix(const vector<vector<int>>& g, int target) {
    int r = 0, c = (int)g[0].size() - 1;            // start top-RIGHT
    while (r < (int)g.size() && c >= 0) {
        if (g[r][c] == target) return true;
        if (g[r][c] > target) c--;                  // too big: whole column below is bigger
        else                  r++;                  // too small: whole row left is smaller
    }
    return false;
}
```

O(n + m). Why top-right: from there, moving left strictly decreases and moving down strictly increases, so each comparison eliminates an entire row or column. Starting from top-left or bottom-right gives you two directions that both increase, which eliminates nothing.

### Must remember

1. **Check the constraints to tell the two types apart.** "First integer of each row is greater than the last of the previous row" means Type 1 and flattening works. Without that guarantee it is Type 2.
2. Flattened index conversion: `row = idx / cols`, `col = idx % cols`.
3. Type 2 starts at top-right (or bottom-left), never at a corner where both directions move the same way.
4. Type 2 is O(n + m), not O(log(nm)). Do not claim the better bound.

---

# PART C — Consolidation

## 5.14 Recognition guide

### When to binary search

```
Is the input sorted?
├─ YES -> standard binary search / lower_bound / upper_bound
│
├─ ROTATED sorted -> identify the sorted half, then search
│
└─ NO
    │
    Can I phrase a yes/no question that is F...F then T...T
    across some range?
    ├─ Over array indices  -> binary search on index (Find Peak)
    ├─ Over answer VALUES   -> BINARY SEARCH ON ANSWER
    └─ No monotonicity      -> binary search does not apply
```

### Signal words

| Statement says | Technique |
|---|---|
| "sorted array", "find element" | Standard binary search |
| "first/last occurrence", "count of x" | lower_bound / upper_bound |
| "insert position" | lower_bound |
| "rotated sorted array" | Rotated binary search |
| "peak", "local maximum" | Binary search on a monotonic predicate |
| **"minimum X such that"**, **"maximum X such that"** | **Binary search on answer** |
| **"minimise the maximum"**, **"maximise the minimum"** | **Binary search on answer** |
| "smallest capacity/speed/divisor/time" | Binary search on answer |
| Answer range up to 10⁹, array only 10⁵ | Binary search on answer |
| "k-th smallest" | `nth_element` / quickselect / heap |
| "minimum difference between any two" | Sort, then scan neighbours |
| "pair/triplet with sum" | Sort, then two pointers |
| "values bounded and small" | Counting sort / bucketing |

### Complexity targets from constraints

Recall Module 1's table. In this module specifically:

| n | Binary search gives | Sorting gives |
|---|---|---|
| 10⁵ | O(n log n) comfortably | O(n log n) comfortably |
| 10⁶ | O(n log n) tight but fine | O(n log n) tight |
| 10⁹ (value range, not array) | O(log n) = 30 steps | impossible |

If the array is 10⁵ but the answer range is 10⁹, that mismatch is the binary-search-on-answer signal.

---

## 5.15 Comparison tables

### Binary search variants

| Variant | Loop condition | Update on match | Returns |
|---|---|---|---|
| Exact match | `lo <= hi` | `return mid` | index or −1 |
| First true (stored answer) | `lo <= hi` | `ans = mid; hi = mid - 1` | first qualifying index |
| Last true (stored answer) | `lo <= hi` | `ans = mid; lo = mid + 1` | last qualifying index |
| Converging (`lo < hi`) | `lo < hi` | `hi = mid` | `lo` at the end |

The stored-answer forms are the safest. Use them by default.

### Quick sort vs merge sort

| | Quick sort | Merge sort |
|---|---|---|
| Average | O(n log n) | O(n log n) |
| Worst | **O(n²)** | O(n log n) |
| Space | O(log n) | O(n) |
| Stable | No | Yes |
| In place | Yes | No |
| Cache behaviour | Excellent | Good |
| Work happens in | Partition (before recursion) | Merge (after recursion) |
| Best for | General purpose, arrays | Guarantees, stability, linked lists |

### Binary search vs two pointers

| | Binary search | Two pointers |
|---|---|---|
| Requires | Monotonic predicate | Sorted input (usually) |
| Time | O(log n) per query | O(n) total |
| Finds | A boundary or a value | A pair or a range |
| Use when | Single lookup, or searching an answer space | Scanning for pairs, windows |

---

## 5.16 Must remember (consolidated)

1. `mid = lo + (hi - lo) / 2`, always.
2. Both updates exclude `mid` in the inclusive template, or the loop hangs.
3. `lo <= hi` for inclusive ranges; `lo < hi` only when the range is guaranteed to contain the answer and you use `hi = mid`.
4. Use the **stored-answer** template. It makes off-by-one errors structurally impossible.
5. `lower_bound` is `>=`, `upper_bound` is `>`. Count of x is `ub - lb`.
6. Binary search needs **monotonicity**, not sortedness.
7. "Minimise the maximum" or "maximise the minimum" means binary search on the answer.
8. In binary-search-on-answer, get the bounds right: `lo` is often `max(a)`, not 0.
9. Ceiling division is `(p + k - 1) / k`.
10. In rotated arrays, compare `a[lo] <= a[mid]` to find the sorted half; compare with `a[hi]` to find the minimum.
11. Duplicates degrade rotated search to O(n).
12. Merge sort is O(n log n) guaranteed and stable; quick sort is O(n²) worst and unstable.
13. `std::sort` is introsort: quicksort with a heapsort fallback, so O(n log n) guaranteed, not stable.
14. Comparison sorting is Ω(n log n); counting sort escapes it at O(n + k) when k is small.
15. Selection sort is O(n²) even on sorted input and is not stable.
16. Comparators use strict `<`, never `<=`.
17. 2D search: flattened binary search only when rows chain; otherwise the top-right staircase, O(n + m).

---

## 5.17 Common mistakes (consolidated)

**Infinite loop**
- `lo = mid` or `hi = mid` in the inclusive template.
- `(lo + hi) / 2` overflowing to a negative index.
- Including the pivot in a quicksort recursive call.
- Overlapping halves in merge sort (`mid` instead of `mid + 1`).

**Wrong answer**
- `lo < hi` where `lo <= hi` was needed, missing the last element.
- Binary search on unsorted input.
- Comparing with `a[lo]` when finding the minimum of a rotated array.
- `<` instead of `<=` when identifying the sorted half.
- Wrong bounds in binary-search-on-answer (starting `lo` at 0).
- Integer division where ceiling division was needed.
- Using `<` in the merge step and losing stability.
- Flattened binary search on a Type 2 matrix.

**Time limit exceeded**
- Not recognising binary search on the answer, and writing an O(n²) DP.
- Quicksort with a naive pivot on sorted input.
- Counting sort with a value range of 10⁹.
- Sorting inside a loop.

**Runtime error**
- Comparator using `<=`.
- Dereferencing `lower_bound`'s result without checking it is not `end()`.

---

## 5.18 Problem set

Sixteen core problems plus optional. Binary search is weighted heavily on purpose.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Binary Search (LC 704) | Easy | Exact match | The template, written from memory |
| Search Insert Position (LC 35) | Easy | lower_bound | Boundary rather than exact match |
| Sqrt(x) (LC 69) | Easy | Binary search on answer | The simplest possible answer space |

### Level 2 — Pattern (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| First and Last Position (LC 34) | Medium | lower/upper bound | Two searches, `ub - 1` for the last |
| Find Minimum in Rotated Array (LC 153) | Medium | Rotated | Why you compare with `a[hi]` |
| Search in Rotated Array (LC 33) | Medium | Rotated | Identifying the sorted half |
| Find Peak Element (LC 162) | Medium | Monotonic predicate | Binary search on unsorted input |
| Search a 2D Matrix (LC 74) | Medium | Flattened index | `mid / m`, `mid % m` |

### Level 3 — Interview (6)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Koko Eating Bananas (LC 875) | Medium | **Binary search on answer** | The canonical one. Do it until automatic |
| Capacity to Ship Packages (LC 1011) | Medium | Binary search on answer | Same shape, different story |
| Split Array Largest Sum (LC 410) | Hard | Binary search on answer | Looks like DP, is fifteen lines |
| Search a 2D Matrix II (LC 240) | Medium | Staircase walk | Why top-right, and why not binary search |
| Sort an Array (LC 912) | Medium | Merge + quick sort | Implement both, compare |
| Kth Largest Element (LC 215) | Medium | Quickselect | O(n) average; revisit with heaps in Module 10 |

### Level 4 — Advanced (4, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Aggressive Cows (GeeksforGeeks) | Medium | Maximise the minimum | The other direction of the template |
| Minimum Days to Make m Bouquets (LC 1482) | Medium | Binary search on answer | Feasibility check with a scan |
| Count Inversions (GeeksforGeeks) | Medium | Instrumented merge | The merge step doing extra work |
| Median of Two Sorted Arrays (LC 4) | Hard | Partition binary search | Only after everything else is solid |

**Do LC 875, 1011, and 410 consecutively.** They are the same problem told three ways, and solving them back to back is what converts binary search on the answer from "a thing I read about" into a pattern you spot in ten seconds.

---

## Exit checklist

```
[ ] I write mid = lo + (hi - lo) / 2 automatically
[ ] I can write the stored-answer binary search template from memory
[ ] I know why both updates must exclude mid
[ ] I know lower_bound is >= and upper_bound is >
[ ] I know count of x = upper_bound - lower_bound
[ ] I can implement lower_bound myself
[ ] I can explain why Find Peak Element works on unsorted input
[ ] I recognise "minimise the maximum" as binary search on answer
[ ] I can write the binary-search-on-answer template from memory
[ ] I get the bounds right (lo is often max(a), not 0)
[ ] I know ceiling division is (p + k - 1) / k
[ ] I can search a rotated array and explain the sorted-half logic
[ ] I know to compare with a[hi] when finding the rotated minimum
[ ] I can write merge sort and explain n log n via the recursion tree
[ ] I can write quick sort with a random pivot and explain the O(n^2) case
[ ] I know which sorts are stable and which are not
[ ] I know std::sort is introsort
[ ] I can tell a Type 1 from a Type 2 sorted matrix
[ ] I ask "would shuffling change the answer?" before sorting
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 6"** for Linked Lists (8–10 hours). It is a smaller module and a change of pace: less algorithmic depth, more pointer discipline and edge-case rigour, which is exactly what it is testing.

The centrepiece is the fast/slow pointer pattern, which handles cycle detection, finding the middle, and n-th from the end with one idea. The module also covers the dummy-node technique that removes most linked-list edge cases, in-place reversal in all its variants, and ends with the LRU cache, which combines a hash map with a doubly linked list and is one of the most commonly asked design questions in placements.
