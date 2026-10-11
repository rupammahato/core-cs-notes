# DSA Placement Handbook (C++) — Part 12
# Phase 10: Heaps and Priority Queues

**Module 10 · 8–10 hours · Tier 1 · Requires: Modules 0, 1, 5, 9**

---

## What this module closes out

Three loops left open in earlier modules:

- **K-th largest** (Module 5 gave you quickselect; this gives the heap answer, and the comparison).
- **Merge k sorted lists** (flagged in Module 6).
- **Top-K frequent** (touched in Module 3 with bucketing; this is the general tool).

A heap is a small idea with a large surface area. The structure itself takes an hour. The rest of the module is four patterns — Top-K, merge-k, two-heaps, and heap-with-sorting for scheduling — plus one judgement call that interviewers probe directly: **when is a heap better than just sorting?**

Section 10.6 contains the thing most people get backwards on first contact: **k-th largest uses a min-heap.** If that already sounds wrong, this module is worth the full ten hours.

---

## 10.1 What a heap actually is

### 1. What is it?

A **complete binary tree** (Module 9.1) where every parent satisfies an ordering relation with its children:

- **Max-heap:** every parent ≥ its children. The maximum is at the root.
- **Min-heap:** every parent ≤ its children. The minimum is at the root.

It is stored in an array, not with pointers.

### 2. Why do we need it?

For the question "give me the best element, repeatedly, while the collection keeps changing", sorting is the wrong tool. Sorting costs O(n log n) up front and is invalidated by a single insertion. A heap maintains just enough order to answer that one question cheaply, and it repairs itself in O(log n) after any change.

The trade is deliberate: **a heap gives up full ordering to get cheap maintenance.**

### 3. Core idea: the array embedding

Because the tree is complete, it maps onto an array with no gaps:

```
        10                index:  0   1  2  3  4  5
       /  \               array: [10, 8, 9, 4, 7, 3]
      8    9
     / \  /
    4  7 3

parent(i) = (i - 1) / 2
left(i)   = 2i + 1
right(i)  = 2i + 2
```

This is why Module 9 flagged the complete-tree indexing fact. No pointers, no allocation per node, perfect cache locality. A heap is a tree that is really an array.

### 4. The weak invariant

The heap property is **local**: each parent beats its children. It says nothing about siblings or about cousins. In the example above, 8 and 9 are in the "wrong" order globally and the heap is perfectly valid.

That weakness is the point. Maintaining a full sort costs O(n) per insertion; maintaining "every parent beats its children" costs O(log n), because a violation can only propagate along one root-to-leaf path.

**Consequence:** a heap tells you the extreme in O(1) and tells you nothing else. You cannot search it, you cannot ask for the second largest without popping, and you cannot ask whether an arbitrary value is present in better than O(n).

### 5. Must remember

1. A heap is a complete binary tree stored in an array. `(i-1)/2`, `2i+1`, `2i+2`.
2. The heap property is local: parent versus children only. Siblings are unordered.
3. Height is always ⌊log₂ n⌋ because the tree is complete. There is no "unbalanced heap".
4. The root is the extreme; everything else is unsorted.
5. You cannot search a heap efficiently. If you need that, use a `set` or `map`.
6. Min-heap and max-heap differ only in the comparison. Negating all values converts between them.

---

## 10.2 Heap operations

### Sift up (used by insert)

Place the new element at the end, then bubble it up while it beats its parent.

```cpp
void siftUp(vector<int>& h, int i) {                  // max-heap
    while (i > 0) {
        int p = (i - 1) / 2;
        if (h[p] >= h[i]) break;                      // parent wins: done
        swap(h[p], h[i]);
        i = p;
    }
}

void push(vector<int>& h, int x) {
    h.push_back(x);
    siftUp(h, h.size() - 1);
}
```

### Sift down (used by extract)

Move the element down while a child beats it, always swapping with the **better** child.

```cpp
void siftDown(vector<int>& h, int i, int n) {         // max-heap
    while (true) {
        int best = i;
        int l = 2 * i + 1, r = 2 * i + 2;
        if (l < n && h[l] > h[best]) best = l;
        if (r < n && h[r] > h[best]) best = r;
        if (best == i) break;                         // heap property restored
        swap(h[i], h[best]);
        i = best;
    }
}
```

**Swap with the larger child, not the first one that beats you.** Swapping with the smaller child breaks the heap property on the other side, and the bug shows up several operations later.

### Extract the root

```cpp
int pop(vector<int>& h) {
    int top = h[0];
    h[0] = h.back();            // move the last element to the root
    h.pop_back();
    siftDown(h, 0, h.size());   // sink it to its place
    return top;
}
```

Moving the **last** element to the root is what preserves completeness. Any other choice leaves a hole in the middle of the array.

### Complexity

| Operation | Time | Why |
|---|---|---|
| `top` / peek | O(1) | It is `h[0]` |
| `push` | O(log n) | One sift-up along the height |
| `pop` | O(log n) | One sift-down along the height |
| Search for a value | **O(n)** | No ordering to exploit |
| Delete an arbitrary element | O(n) to find, O(log n) to fix | Which is why you avoid it |
| **Build from an array** | **O(n)** | See 10.3 |

---

## 10.3 Build-heap and why it is O(n)

### The operation

```cpp
void buildHeap(vector<int>& h) {
    int n = h.size();
    for (int i = n / 2 - 1; i >= 0; i--)     // start at the last internal node
        siftDown(h, i, n);
}
```

Start at the last non-leaf node (`n/2 - 1`) and sift down, working backwards to the root. Leaves are trivially valid heaps of size one, so there is nothing to do for the second half of the array.

### Why not O(n log n)?

The obvious analysis is "n calls to an O(log n) operation", giving O(n log n). That is a correct upper bound and a loose one.

**The actual argument:** sift-down's cost depends on the node's **height**, not the tree's height. And in a complete tree, almost all nodes are near the bottom, where the height is almost zero.

| Level | Node count | Height of those nodes | Work |
|---|---|---|---|
| Leaves | n/2 | 0 | 0 |
| One above | n/4 | 1 | n/4 |
| Two above | n/8 | 2 | 2n/8 |
| … | … | … | … |
| Root | 1 | log n | log n |

Total work is `Σ (n / 2^(h+1)) × h`, which is `n × Σ h/2^(h+1)`. That series converges to a constant (it sums to 1), so the total is **O(n)**.

**The intuition to state in an interview:** half the nodes are leaves and cost nothing; only one node costs log n. The expensive cases are rare and the cheap cases dominate.

### Why it matters practically

```cpp
priority_queue<int> pq(v.begin(), v.end());    // O(n)

priority_queue<int> pq;                         // O(n log n)
for (int x : v) pq.push(x);
```

Same result, different cost. Use the range constructor when you have the data up front.

### Must remember

1. Build-heap is O(n), not O(n log n). Be able to give the "half the nodes are leaves" argument.
2. Start at `n/2 - 1`, the last internal node, and go backwards.
3. Build-heap uses sift-**down**. Repeated sift-up insertion is genuinely O(n log n).
4. `priority_queue(begin, end)` uses the O(n) construction.
5. This does **not** contradict the Ω(n log n) sorting bound. Building a heap does not sort; extracting all n elements afterwards is what costs the log factor.

---

## 10.4 Heap sort

```cpp
void heapSort(vector<int>& a) {
    int n = a.size();

    for (int i = n / 2 - 1; i >= 0; i--)      // 1. build a max-heap:    O(n)
        siftDown(a, i, n);

    for (int i = n - 1; i > 0; i--) {          // 2. extract repeatedly: O(n log n)
        swap(a[0], a[i]);                      // largest goes to its final place
        siftDown(a, 0, i);                     // restore the heap on the prefix
    }
}
```

Build a max-heap, then repeatedly swap the root with the last unsorted position and shrink. The array fills from the back with the largest elements.

| | |
|---|---|
| Time | O(n log n), **all cases** |
| Space | **O(1)**, fully in place |
| Stable | No |

### Why it matters

Heap sort is the only comparison sort that is **both** O(n log n) guaranteed **and** O(1) space. Merge sort gives the guarantee but needs O(n); quick sort gives the space but not the guarantee.

Its practical weakness is cache behaviour: sift-down jumps around the array, so despite matching asymptotics it loses to quicksort in wall-clock time. That is why `std::sort` uses introsort with heapsort only as a **fallback** when quicksort's recursion runs too deep (Module 5.6). Heap sort is the safety net that gives C++ its worst-case guarantee.

### Must remember

1. O(n log n) all cases, O(1) space, not stable.
2. The only sort with both the guarantee and O(1) space.
3. Slower than quicksort in practice because of poor cache locality.
4. It is introsort's fallback, which is how `std::sort` gets its worst-case guarantee.
5. Build is O(n); the extraction loop is what costs O(n log n).

---

## 10.5 priority_queue in C++

Module 0, Section B5 covered the syntax. The two declarations, once more, because they are the most-forgotten lines in C++ DSA:

```cpp
priority_queue<int> maxHeap;                                  // largest on top
priority_queue<int, vector<int>, greater<int>> minHeap;       // smallest on top
```

```cpp
pq.push(x);      // O(log n)
pq.top();        // O(1)
pq.pop();        // O(log n), returns VOID
pq.size();  pq.empty();

priority_queue<int> pq(v.begin(), v.end());   // O(n) build
```

### Custom ordering

```cpp
// Min-heap on the second field of a pair
struct Cmp {
    bool operator()(const pair<int,int>& a, const pair<int,int>& b) const {
        return a.second > b.second;        // "a has LOWER priority than b"
    }
};
priority_queue<pair<int,int>, vector<pair<int,int>>, Cmp> pq;
```

**The comparator is inverted relative to `sort`.** `cmp(a,b) == true` means `a` comes out *later*. A comparator that looks like "sort ascending" produces a max-heap. This is why `greater<int>` gives a min-heap, and it is a top-five C++ interview bug.

### What a heap cannot do

| You want | `priority_queue` | Use instead |
|---|---|---|
| The extreme | ✅ O(1) | |
| Insert / remove the extreme | ✅ O(log n) | |
| Search for a value | ❌ | `set` / `unordered_set` |
| Remove an arbitrary element | ❌ | `multiset` |
| The k-th element | ❌ | `nth_element`, or an order-statistic tree |
| Iterate in sorted order | ❌ | `set`, or sort |
| Update a key in place | ❌ | See lazy deletion below |

**Lazy deletion**, the standard workaround when you need to "update" an entry: push the new version, and when you pop, discard entries you can detect as stale.

```cpp
while (!pq.empty() && isStale(pq.top())) pq.pop();
```

This is exactly how Dijkstra is written in practice (Module 12), because C++ gives you no decrease-key operation.

### Must remember

1. `greater<int>` gives a **min**-heap. Three template arguments, always.
2. `priority_queue` comparators are inverted relative to `sort`.
3. `pop()` returns void. Read `top()` first, and guard with `!empty()`.
4. The range constructor is O(n); n pushes is O(n log n).
5. No search, no arbitrary deletion, no key update. Lazy deletion is the workaround.
6. A `multiset` gives you heap-like access (`*begin()`, `*rbegin()`) **plus** arbitrary deletion, at O(log n) with a worse constant. It is the right choice when you need to remove specific elements.

---

## 10.6 The Top-K pattern

**The most important section in the module.**

### 1. What is it?

Maintaining a heap of **fixed size k** so that after one pass over n elements, the heap holds exactly the k best.

### 2. Why do we need it?

Sorting to find the k largest is O(n log n) and computes far more order than you asked for. A size-k heap does it in O(n log k). When k is small and n is large — which is the usual setup — that is a large win. It also works on **streams**, where sorting is not even possible.

### 3. The direction rule (read this twice)

> **K-th largest → min-heap of size k.**
> **K-th smallest → max-heap of size k.**

This feels backwards on first contact. The reasoning:

You are keeping the k largest seen so far. When a new element arrives and the heap is full, you must evict the **worst** of your current k — which is the **smallest** of them. So the element you need instant access to is the minimum, which means a min-heap.

At the end, the heap holds the k largest, and its top — the smallest of those k — is exactly the k-th largest.

### 4. Template

```cpp
int findKthLargest(const vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> pq;    // MIN-heap

    for (int x : nums) {
        pq.push(x);
        if ((int)pq.size() > k) pq.pop();                 // evict the smallest
    }
    return pq.top();                                       // smallest of the k largest
}
```

Five lines. Memorise them; the whole family is variations on this.

### 5. Complexity

| | |
|---|---|
| Time | **O(n log k)** |
| Space | **O(k)** |

Compare with sorting at O(n log n) and O(1) extra, and quickselect at O(n) average and O(1).

When k = 5 and n = 10⁶: log k is about 2, log n is about 20. A tenfold difference in the dominant factor.

### 6. Worked example: Top K Frequent Elements (LC 347)

```cpp
vector<int> topKFrequent(const vector<int>& nums, int k) {
    unordered_map<int,int> freq;
    for (int x : nums) freq[x]++;

    // min-heap on count; pair sorts by first, so {count, value} orders by count
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<pair<int,int>>> pq;

    for (auto& [val, cnt] : freq) {
        pq.push({cnt, val});
        if ((int)pq.size() > k) pq.pop();
    }

    vector<int> res;
    while (!pq.empty()) { res.push_back(pq.top().second); pq.pop(); }
    return res;
}
```

Module 3's hash map plus this module's heap. O(n + m log k), where m is the number of distinct values.

**The O(n) alternative:** bucket sort by frequency. Counts are bounded by n, so make `n+1` buckets and walk them from the back. Mention it when asked to beat O(n log k).

### 7. Worked example: K Closest Points to Origin (LC 973)

K **closest** means k smallest distances, so by the direction rule this is a **max**-heap:

```cpp
vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
    priority_queue<pair<int, int>> pq;                   // MAX-heap: {dist, index}

    for (int i = 0; i < (int)points.size(); i++) {
        int d = points[i][0]*points[i][0] + points[i][1]*points[i][1];
        pq.push({d, i});
        if ((int)pq.size() > k) pq.pop();                // evict the farthest
    }

    vector<vector<int>> res;
    while (!pq.empty()) { res.push_back(points[pq.top().second]); pq.pop(); }
    return res;
}
```

**Skip the square root.** Comparing squared distances gives the same ordering and avoids floating point entirely. Interviewers notice.

### 8. Must remember

1. **K-th largest → min-heap. K-th smallest → max-heap.** Burn this in.
2. The heap holds the k best; its top is the worst of those, which is the answer.
3. Push then pop-if-oversized. Both orders work, but this one is uniform across variants.
4. O(n log k) time, O(k) space.
5. For distances, compare squares and skip the `sqrt`.
6. Heaps handle streams; sorting does not.
7. Quickselect (Module 5.4) gives O(n) average for a **one-shot** query. The heap wins on streams and when k is small.

### 9. Common mistakes

- Using a max-heap for k-th largest, which keeps the wrong k elements.
- Forgetting the size check, degrading to O(n log n) and O(n) space.
- Popping before pushing, so the heap never reaches size k.
- Taking `sqrt` unnecessarily.
- Claiming O(n log n) when the fixed-size heap makes it O(n log k).

### 10. Practice

- Kth Largest Element in an Array (LC 215, Medium) — compare with quickselect
- Kth Largest Element in a Stream (LC 703, Easy) — where sorting genuinely cannot work
- Top K Frequent Elements (LC 347, Medium)
- K Closest Points to Origin (LC 973, Medium)

---

## 10.7 Merge K sorted sequences

### 1. The problem

Given k sorted lists (or arrays) with N elements in total, merge them into one sorted sequence.

### 2. Core idea

At every step, the next element of the output is the smallest among the **current heads** of the k lists. A min-heap of size k gives you that in O(log k). After taking an element, push its successor from the same list.

### 3. Template

```cpp
struct Cmp {
    bool operator()(ListNode* a, ListNode* b) const { return a->val > b->val; }  // min-heap
};

ListNode* mergeKLists(vector<ListNode*>& lists) {
    priority_queue<ListNode*, vector<ListNode*>, Cmp> pq;

    for (ListNode* l : lists)
        if (l) pq.push(l);                       // skip empty lists

    ListNode dummy(0);
    ListNode* tail = &dummy;

    while (!pq.empty()) {
        ListNode* n = pq.top(); pq.pop();
        tail->next = n;
        tail = n;
        if (n->next) pq.push(n->next);           // advance that list
    }
    tail->next = nullptr;
    return dummy.next;
}
```

The dummy node is Module 6.3; the heap is this module. **The heap never holds more than k nodes**, one per list, which is what keeps the space bounded.

### 4. Complexity

| Approach | Time | Space |
|---|---|---|
| Heap | **O(N log k)** | O(k) |
| Divide and conquer (pairwise merge) | O(N log k) | O(1) extra, O(log k) stack |
| Merge one at a time | O(N·k) | O(1) |
| Concatenate then sort | O(N log N) | O(N) |

The heap and the divide-and-conquer approaches tie asymptotically. **Divide and conquer is the better answer for linked lists** (no extra structure, reuses the merge-two function from Module 6.6); the heap is better when the sequences arrive as a stream or when k is large and you want a uniform interface.

Note the log is over **k**, not N. Merging 10⁶ elements across 10 lists costs about 3.3 comparisons per element, not 20.

### 5. Must remember

1. The heap holds one node per list: at most k entries.
2. Push a list's successor immediately after popping from it.
3. Skip null lists when seeding, or you crash on `pq.top()->val`.
4. Set `tail->next = nullptr` at the end, or the last node may keep a stale pointer.
5. O(N log k), where the log is over the number of lists.
6. Divide and conquer pairwise merging achieves the same bound with less machinery.

### 6. Practice

- Merge k Sorted Lists (LC 23, Hard) — write both approaches
- Smallest Range Covering Elements from K Lists (LC 632, Hard) — optional; the same heap with a window on top

---

## 10.8 Two heaps: the running median

### 1. What is it?

Split the data into a lower half and an upper half, each in its own heap, so the median is always at one or both tops.

### 2. Why do we need it?

The median needs the middle element, which requires order. Sorting after every insertion is O(n log n) per query. Two heaps give O(log n) insertion and **O(1) median**.

### 3. Core idea

```
        lo (MAX-heap)              hi (MIN-heap)
     [ smaller half ]           [ larger half ]
              ^   top = largest of the small half
                  top = smallest of the large half  ^

Invariant 1 (ordering): everything in lo <= everything in hi
Invariant 2 (size):     lo.size() == hi.size(), or lo.size() == hi.size() + 1

Median = lo.top()                      if sizes differ
       = (lo.top() + hi.top()) / 2     if sizes are equal
```

### 4. Template

```cpp
class MedianFinder {
    priority_queue<int> lo;                                 // max-heap, lower half
    priority_queue<int, vector<int>, greater<int>> hi;      // min-heap, upper half

public:
    void addNum(int num) {
        lo.push(num);                    // 1. always insert into lo
        hi.push(lo.top()); lo.pop();     // 2. funnel lo's largest across to hi
        if (hi.size() > lo.size()) {     // 3. rebalance if hi got too big
            lo.push(hi.top());
            hi.pop();
        }
    }

    double findMedian() {
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + hi.top()) / 2.0;
    }
};
```

**The three-line funnel is the whole trick.** Instead of case analysis on where the new number belongs, always push into `lo`, immediately move `lo`'s top into `hi` (which guarantees the ordering invariant regardless of the value), then rebalance sizes if needed. No comparisons against the current median, no branches to get wrong.

Most people's first attempt is `if (num <= lo.top()) lo.push(num); else hi.push(num);` followed by rebalancing. That works but has more cases, including the empty-heap case. The funnel version has none.

### 5. Complexity

`addNum` O(log n), `findMedian` O(1), space O(n).

### 6. Where else two heaps appear

The technique generalises to any "maintain a boundary within a changing collection":

| Problem | The two heaps hold |
|---|---|
| Running median | Lower half / upper half |
| Sliding Window Median (LC 480) | Same, plus lazy deletion for expiring elements |
| IPO (LC 502) | Affordable projects / not-yet-affordable projects |
| Maximum capital / scheduling variants | Available now / available later |

### 7. Must remember

1. `lo` is a **max**-heap (lower half), `hi` is a **min**-heap (upper half). Getting these backwards is the standard bug.
2. Two invariants: ordering (everything in `lo` ≤ everything in `hi`) and size (differ by at most one).
3. The funnel — push to `lo`, move `lo.top()` to `hi`, rebalance — avoids all case analysis.
4. Use `/ 2.0`, not `/ 2`. Integer division silently truncates the median.
5. `lo.top() + hi.top()` can overflow `int` for large values. Cast to `long long` or `double`.
6. For a **sliding** window median, a `multiset` with iterator-based deletion is easier than two heaps with lazy deletion. Say so.

### 8. Practice

- Find Median from Data Stream (LC 295, Hard)
- IPO (LC 502, Hard) — optional; two heaps with a different split rule

---

## 10.9 Heaps with sorting: scheduling problems

A recurring combination: **sort by start, heap on end.** Module 11 covers greedy interval problems properly; this is the subset where a heap does the work.

### Meeting Rooms II (LC 253)

*Given meeting intervals, how many rooms are needed?*

```cpp
int minMeetingRooms(vector<vector<int>>& intervals) {
    sort(intervals.begin(), intervals.end());                  // by start time

    priority_queue<int, vector<int>, greater<int>> pq;         // min-heap of END times

    for (auto& iv : intervals) {
        if (!pq.empty() && pq.top() <= iv[0]) pq.pop();        // a room has freed up
        pq.push(iv[1]);                                         // occupy a room
    }
    return pq.size();                                           // rooms in use at the peak
}
```

**The heap holds the end times of meetings currently in progress**, and its top is the one finishing soonest. If that meeting ends before the next one starts, the room is reusable. The heap's final size is the maximum concurrency.

Sorting establishes the order to process events in; the heap answers "which room frees up first?" That division of labour is the pattern.

Note the alternative: sort start times and end times separately and sweep with two pointers, O(n log n) with O(1) extra space. Both are correct; the heap version is more obviously correct and the sweep is leaner.

### Task Scheduler (LC 621)

*Given tasks and a cooldown n between identical tasks, find the minimum total time.*

The heap approach: count frequencies, always schedule the most frequent available task, and hold cooling-down tasks in a waiting queue.

There is also a closed-form answer: `max(total_tasks, (maxFreq - 1) * (n + 1) + countOfMaxFreq)`. The formula is faster to write and harder to derive on the spot. **Know the heap simulation** — it generalises — and mention the formula as an optimisation.

### The general shape

| Problem | Sort by | Heap holds | Answer |
|---|---|---|---|
| Meeting Rooms II | Start time | End times in progress | Heap size |
| Minimum platforms | Arrival time | Departure times | Heap size |
| Task Scheduler | (frequency) | Remaining counts | Simulated time |
| Merge intervals | Start time | (no heap needed) | Module 11 |

### Must remember

1. Sort by start, heap the ends. The heap answers "what finishes soonest?"
2. Pop **before** pushing, so a freed room is reused rather than double-counted.
3. The heap size at the end is the peak concurrency.
4. A two-pointer sweep over separately sorted starts and ends is the O(1)-space alternative.
5. Task Scheduler has a formula, but the heap simulation is the transferable answer.

---

## 10.10 Heap or sort or quickselect?

You asked for this explicitly, and it is a common interview follow-up.

### The decision

```
Do I need the FULL sorted order?
└─ YES -> SORT. O(n log n), and you get everything.

Do I need just the extreme, ONCE?
└─ YES -> min_element / max_element. O(n), no structure needed.

Do I need the k-th (or top k), ONE TIME, all data available?
└─ YES -> QUICKSELECT / nth_element. O(n) average, O(1) space.

Do I need the extreme REPEATEDLY while the collection CHANGES?
└─ YES -> HEAP. O(log n) per update.

Is the data a STREAM (I can't see it all at once)?
└─ YES -> HEAP. Sorting isn't possible.

Do I also need to SEARCH or DELETE ARBITRARY elements?
└─ YES -> multiset / set. O(log n), with a worse constant.
```

### The comparison table

| | Heap (size k) | Full sort | Quickselect | `multiset` |
|---|---|---|---|---|
| Top-k | O(n log k) | O(n log n) | O(n) avg | O(n log n) |
| Works on streams | **Yes** | No | No | Yes |
| Insert after the fact | O(log n) | O(n) | No | O(log n) |
| Delete arbitrary | No | — | No | **O(log n)** |
| Search | No | O(log n) | No | O(log n) |
| Space | O(k) | O(1) | O(1) | O(n) |
| Worst case | O(n log k) | O(n log n) | **O(n²)** | O(n log n) |

### The honest summary

**A heap wins when k ≪ n, when data streams, or when insertions interleave with queries.** Those three conditions cover most Top-K interview problems, which is why the heap is the expected answer.

**Sorting wins when you need the order anyway**, when k is close to n, or when the next step is two pointers or binary search on the sorted array.

**Quickselect wins for a single offline k-th query**, at O(n) average. Its O(n²) worst case and its inability to handle streams are why it is not the default.

**`multiset` wins when you need heap behaviour plus arbitrary deletion**, which is exactly the sliding-window-median situation.

### Must remember

1. Heap beats sorting when k ≪ n: O(n log k) versus O(n log n).
2. Heap is the only option for streams.
3. Quickselect is O(n) average for a one-shot k-th, and is what `nth_element` does.
4. A heap cannot search or delete arbitrary elements. `multiset` can.
5. If the next step needs sorted order anyway, just sort.
6. Say the trade-off out loud. "A heap gives O(n log k) and works on a stream; quickselect gives O(n) average but needs all the data up front" is a complete answer.

---

## 10.11 Consolidation

### Recognition guide

| The statement says | Reach for |
|---|---|
| "k-th largest", "top k largest" | **Min**-heap of size k |
| "k-th smallest", "k closest", "k cheapest" | **Max**-heap of size k |
| "merge k sorted lists/arrays" | Min-heap of heads, or pairwise D&C |
| "median of a stream", "running median" | Two heaps |
| "find X in a data stream" | Heap (sorting is impossible) |
| "minimum number of rooms/platforms/machines" | Sort by start, min-heap of ends |
| "always process the highest priority next" | Priority queue, by definition |
| "schedule tasks with cooldown" | Heap simulation |
| "shortest path with weights" | Dijkstra = BFS + heap (Module 12) |
| "k-th smallest, one query, offline" | `nth_element` / quickselect |
| "smallest element, plus arbitrary deletion" | `multiset`, not a heap |

### Must remember (consolidated)

1. A heap is a complete binary tree in an array: `(i-1)/2`, `2i+1`, `2i+2`.
2. The heap property is local. Siblings are unordered; only the root is meaningful.
3. `push` and `pop` are O(log n); `top` is O(1); build is **O(n)**.
4. Build-heap is O(n) because half the nodes are leaves and cost nothing.
5. `priority_queue<int, vector<int>, greater<int>>` is the min-heap. Three arguments.
6. `priority_queue` comparators are inverted relative to `sort`.
7. **K-th largest uses a min-heap; k-th smallest uses a max-heap.**
8. Fixed-size-k heap gives O(n log k) time and O(k) space.
9. Merge-k: heap of heads, one entry per list, O(N log k).
10. Two heaps: `lo` is max, `hi` is min; funnel every insertion through `lo`.
11. Median: `/ 2.0`, and watch for overflow in the sum.
12. Scheduling: sort by start, min-heap on end, pop before push, answer is the heap size.
13. Heap sort is O(n log n) with O(1) space and is introsort's fallback.
14. A heap cannot search, cannot delete arbitrary elements, cannot update keys. Lazy deletion is the workaround.
15. Compare squared distances; skip the `sqrt`.

### Common mistakes (consolidated)

**Wrong answer**
- Max-heap for k-th largest (the direction reversed).
- `lo` and `hi` swapped in the two-heap median.
- Integer division `/ 2` for the median.
- Pushing before popping in the scheduling loop, double-counting rooms.
- Comparator copied from `sort`, producing the opposite heap.
- Not clearing `tail->next` in merge-k.

**Time limit exceeded**
- No size cap on the Top-K heap: O(n log n) instead of O(n log k).
- n pushes instead of the O(n) range constructor.
- Searching a heap linearly for a value.
- Sorting inside a loop when a heap would maintain the answer.

**Runtime error**
- `top()` on an empty heap.
- Seeding merge-k with null list heads.

**Analysis errors**
- Claiming build-heap is O(n log n).
- Claiming O(n log n) for a fixed-size-k heap.
- Claiming O(1) worst case for quickselect as the heap alternative.

---

## 10.12 Problem set

Ten core problems plus three optional.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Last Stone Weight (LC 1046) | Easy | Plain max-heap | The API, nothing else |
| Kth Largest Element in a Stream (LC 703) | Easy | Fixed-size min-heap | Where sorting genuinely cannot work |
| Kth Largest Element in an Array (LC 215) | Medium | Fixed-size min-heap | The direction rule; compare with quickselect |

### Level 2 — Pattern (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Top K Frequent Elements (LC 347) | Medium | Hash map + heap | Modules 3 and 10 combined; the bucket alternative |
| K Closest Points to Origin (LC 973) | Medium | Fixed-size max-heap | The reversed direction; skipping `sqrt` |
| Merge k Sorted Lists (LC 23) | Hard | Heap of heads | Write the heap and the D&C versions |

### Level 3 — Interview (4)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| **Find Median from Data Stream (LC 295)** | Hard | Two heaps | The funnel that removes all case analysis |
| Meeting Rooms II (LC 253) | Medium | Sort + heap of ends | Division of labour between sorting and the heap |
| Task Scheduler (LC 621) | Medium | Heap simulation | Greedy scheduling; the formula as an aside |
| Reorganize String (LC 767) | Medium | Max-heap by frequency | "Take the two most frequent" greedy |

### Level 4 — Advanced (3, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Sliding Window Median (LC 480) | Hard | Two heaps + lazy deletion | Why `multiset` is easier here |
| IPO (LC 502) | Hard | Two heaps, different split | The technique beyond medians |
| Smallest Range Covering K Lists (LC 632) | Hard | Merge-k + window | Combining two patterns |

**LC 295 is the one to over-prepare.** It is the standard hard heap question, the funnel trick is genuinely non-obvious, and the two-heap idea generalises to a family of problems. LC 215 is worth solving three ways — sort, heap, quickselect — and being able to state which you would choose and why, because that comparison is a standard follow-up.

---

## Exit checklist

```
[ ] I can explain a heap as a complete binary tree in an array
[ ] I know parent/left/right index formulas
[ ] I can write siftUp and siftDown
[ ] I know build-heap is O(n) and can explain why
[ ] I can write both priority_queue declarations from memory
[ ] I know pq comparators are inverted relative to sort
[ ] I know k-th LARGEST uses a MIN-heap, and why
[ ] I can write the fixed-size Top-K template from memory
[ ] I report Top-K as O(n log k), not O(n log n)
[ ] I can write merge-k with a heap of heads
[ ] I can write the two-heap median with the funnel
[ ] I know lo is the max-heap and hi is the min-heap
[ ] I remember / 2.0 for the median
[ ] I can write Meeting Rooms II with sort + heap
[ ] I can state when a heap beats sorting, and when it doesn't
[ ] I know a heap can't search or delete arbitrarily, and what to use instead
[ ] I know heap sort is O(1) space and introsort's fallback
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 11"** for Greedy Algorithms and Intervals (8–10 hours, Tier 2). It is the module where "why does this work?" matters more than the code, because greedy solutions are three lines long and the entire difficulty is knowing whether the greedy choice is actually safe.

It covers the exchange argument (the standard proof technique, and what interviewers want to hear), the interval family — merge intervals, non-overlapping intervals, meeting rooms, minimum platforms — which is by far the most-asked greedy topic, the classic problems (activity selection, fractional knapsack, job sequencing, gas station, jump game), and critically, **when greedy fails and you need DP instead**, which is the setup for Module 13.
