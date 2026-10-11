# DSA Placement Handbook (C++) — Part 13
# Phase 11: Greedy Algorithms and Intervals

**Module 11 · 8–10 hours · Tier 2 · Requires: Modules 0, 1, 5, 10**

---

## Why this module inverts the usual emphasis

Greedy solutions are short. Activity selection is four lines. Gas Station is six. Jump Game is three. If this module were about code it would take an afternoon.

The difficulty is entirely elsewhere: **knowing whether the greedy choice is actually safe.** A greedy algorithm that looks reasonable and is wrong produces plausible answers on small tests and fails on the ones you did not think of. And unlike a bug, you cannot find it by tracing — you have to reason about it.

So this module spends its time on three things:

**The exchange argument** (Section 11.2), which is the standard way to justify a greedy choice and the thing interviewers want to hear when they ask "why does that work?"

**The interval family** (Sections 11.4 to 11.6), which is by far the most-asked greedy topic in placements, and where the entire algorithm is often the choice of what to sort by.

**When greedy fails** (Section 11.12), which is the setup for Module 13. Recognising "this needs DP, not greedy" early saves twenty minutes in an interview.

**Tier 2 note:** the interval problems are effectively Tier 1 by frequency — merge intervals and its relatives come up constantly. Huffman coding and job sequencing are lower priority. If time is short, do Sections 11.1 through 11.6 and 11.9 through 11.12 properly, and skim the rest.

---

## 11.1 What greedy means

### 1. What is it?

An algorithm that builds a solution by repeatedly making the choice that looks best **right now**, never reconsidering.

### 2. Why do we need it?

When it works, it is dramatically cheaper than the alternatives. Activity selection by greedy is O(n log n); by brute force it is O(2ⁿ); by DP it is O(n²). The whole value is skipping the search.

### 3. The two conditions

A greedy algorithm is correct only if both hold:

**Greedy choice property.** A globally optimal solution can be reached by making a locally optimal choice. Formally: there exists an optimal solution that **contains** the greedy choice. This is the condition that fails most often, and proving it is what the exchange argument does.

**Optimal substructure.** After making the greedy choice, the remaining problem is a smaller instance of the same problem, and combining the greedy choice with an optimal solution to the remainder gives an optimal overall solution.

Optimal substructure is shared with DP. **The greedy choice property is what distinguishes them.** DP considers all choices at each step because it cannot prove any single one is safe; greedy proves one is safe and commits.

### 4. The shape of almost every greedy solution

```cpp
sort(items.begin(), items.end(), byTheRightKey);

for (auto& item : items) {
    if (isCompatibleWithWhatIveTaken(item)) {
        take(item);
        updateState();
    }
}
```

**Sorting is usually the algorithm.** Once the right ordering is chosen, the loop is mechanical. Which means the real question in most greedy problems is *what do I sort by?*, and Section 11.6 is about answering that.

### 5. Must remember

1. Greedy requires the greedy choice property **and** optimal substructure. DP requires only the second.
2. Greedy never reconsiders. That is its speed and its risk.
3. The sort key is usually the whole algorithm.
4. "It looks right on the examples" is not a justification. Either construct the exchange argument or find a counterexample.
5. Typical complexity is O(n log n), dominated by the sort.

---

## 11.2 The exchange argument

**The section that matters most.** This is how you justify a greedy choice, and it is what an interviewer is asking for with "why is that optimal?"

### The structure

To show the greedy choice is safe:

1. Take any optimal solution `OPT`.
2. Suppose `OPT` does **not** contain the greedy choice `g`.
3. Show you can **swap** something in `OPT` for `g` and get a solution that is still valid and **no worse**.
4. Therefore there exists an optimal solution containing `g`, so taking `g` loses nothing.
5. Recurse on the remainder.

The word "exchange" is literal: you exchange one element of the hypothetical optimum for your greedy choice and show nothing breaks.

### Worked example: activity selection

*Given activities with start and end times, select the maximum number of non-overlapping ones.*

**Greedy choice:** take the activity that **finishes earliest**.

**The argument.** Let `OPT` be an optimal selection, and let `a` be its first activity (by finish time). Let `g` be the globally earliest-finishing activity.

If `a == g`, done.

Otherwise, `g` finishes no later than `a` (by definition of `g`). Replace `a` with `g` in `OPT`. The rest of `OPT` starts after `a` ends, and `g` ends no later than `a`, so nothing in the rest now overlaps. The result is valid and has the **same size**, so it is also optimal.

Therefore some optimal solution starts with `g`. Take it, delete everything that overlaps it, and repeat on what remains.

**Say this out loud in an interview.** "Sorting by end time is safe because the earliest-finishing activity leaves the most room for everything after it — if an optimal solution doesn't use it, you can swap it in without breaking anything." That is a complete justification in one sentence.

### The counterexample test

Before writing a greedy solution, spend two minutes trying to **break** it.

- Sort by start time instead? `[0,10], [1,2], [3,4]` — greedy takes the long one and gets 1; optimal is 2. **Start time fails.**
- Sort by shortest duration? `[0,5], [4,6], [5,10]` — greedy takes `[4,6]` (length 2) and blocks both others, getting 1; optimal is `[0,5]` and `[5,10]`, which is 2. **Duration fails.**
- Sort by end time? No counterexample exists, and the exchange argument proves it.

**If you can construct a counterexample in two minutes, greedy is wrong and you need DP.** If you can articulate an exchange argument, greedy is right. If neither, you do not yet understand the problem well enough to commit.

### Must remember

1. Exchange argument: assume an optimal solution lacking the greedy choice, swap it in, show nothing gets worse.
2. "Leaves the most room for what follows" is the intuition behind most interval greedies.
3. Spend two minutes trying to break your greedy before writing it.
4. A counterexample is a proof of failure. An exchange argument is a proof of correctness. One informal example of success is neither.
5. Interviewers ask "why does that work?" precisely to see whether you can do this.

---

## 11.3 Greedy or DP?

### The fork

| | Greedy | DP |
|---|---|---|
| Choices per step | One, committed | All, compared |
| Reconsiders | Never | Yes, via subproblems |
| Requires | Greedy choice property | Overlapping subproblems |
| Typical time | O(n log n) | O(n·something) |
| Typical space | O(1) | O(states) |
| Fails when | A local choice can be regretted | Rarely; it is the safe default |

### The practical tests

**Test 1: can you break it?** Try to build a small input where the locally best choice leads to a globally worse answer. Success means DP.

**Test 2: does the problem ask for a count or an exact total?** "How many ways", "the minimum number of coins with arbitrary denominations", "the maximum value under a hard capacity" — these smell like DP. "The maximum number of non-overlapping X", "the minimum number of Y to remove", "can I reach the end" — these smell greedy.

**Test 3: is there a hard capacity with indivisible items?** That is almost always knapsack DP. Fractional items make it greedy; indivisible ones do not.

**Test 4: what do the constraints say?** n = 10⁵ rules out an O(n²) DP and points at greedy or a greedy-plus-heap solution. n = 10³ with a target of 10³ suggests a 2D DP table.

### Pairs that differ by one word

| Greedy | DP | The difference |
|---|---|---|
| **Fractional** knapsack | **0/1** knapsack | Divisible items let you fill the capacity exactly |
| Coin change with **canonical** coins (1, 2, 5, 10…) | Coin change with **arbitrary** coins | Canonical systems happen to make greedy safe |
| Longest increasing **subarray** | Longest increasing **subsequence** | Contiguity removes the choice |
| Activity selection (**max count**) | Weighted activity selection (**max value**) | Weights break the exchange argument |

That last row is worth dwelling on. Maximum **number** of non-overlapping intervals is greedy by end time. Maximum **total weight** of non-overlapping intervals is DP, because a single heavy interval can be worth more than three light ones and the earliest-finishing choice is no longer safe.

### Must remember

1. Greedy commits; DP compares. That is the whole difference.
2. Adding weights to a counting problem usually breaks greedy.
3. Divisible items → greedy. Indivisible items with a capacity → DP.
4. If you cannot prove the greedy choice, use DP. DP is never wrong, only slower.
5. Constraints are a hint: n = 10⁵ rules out most DP formulations.

---

## 11.4 Activity selection and non-overlapping intervals

### The canonical problem

*Select the maximum number of mutually non-overlapping intervals.*

```cpp
int maxNonOverlapping(vector<vector<int>>& iv) {
    sort(iv.begin(), iv.end(), [](const vector<int>& a, const vector<int>& b) {
        return a[1] < b[1];                       // sort by END time
    });

    int count = 0, lastEnd = INT_MIN;
    for (auto& x : iv) {
        if (x[0] >= lastEnd) {                    // no overlap with the last kept
            count++;
            lastEnd = x[1];
        }
    }
    return count;
}
```

Four lines of logic. The proof is Section 11.2.

### Non-overlapping Intervals (LC 435)

*Minimum number of intervals to **remove** so the rest do not overlap.*

This is the same problem restated: removals = total − maximum kept.

```cpp
int eraseOverlapIntervals(vector<vector<int>>& iv) {
    return iv.size() - maxNonOverlapping(iv);
}
```

**Recognising the restatement is the skill.** "Minimum to remove" and "maximum to keep" are the same question, and one of them has an obvious greedy.

### Minimum Number of Arrows to Burst Balloons (LC 452)

*Each arrow bursts all balloons whose interval it pierces. Minimum arrows?*

Also the same problem. The minimum number of arrows equals the maximum number of pairwise **non-overlapping** intervals, because each disjoint group needs its own arrow and one arrow handles an entire overlapping cluster.

```cpp
int findMinArrowShots(vector<vector<int>>& points) {
    sort(points.begin(), points.end(), [](const vector<int>& a, const vector<int>& b) {
        return a[1] < b[1];
    });
    int arrows = 1;
    long long lastEnd = points[0][1];
    for (auto& p : points) {
        if (p[0] > lastEnd) { arrows++; lastEnd = p[1]; }   // strict: touching counts as hit
        }
    return arrows;
}
```

**The boundary convention differs between problems.** Here `[1,2]` and `[2,3]` are considered overlapping (one arrow at x=2 hits both), so the test is `p[0] > lastEnd`. In LC 435 they are considered non-overlapping, so the test is `x[0] >= lastEnd`. **Read the statement for whether endpoints touching counts as an overlap.** This single comparison operator is the difference between accepted and wrong answer.

Also note `long long` for `lastEnd`: LC 452's coordinates reach `INT_MAX` and the comparison can overflow.

### Must remember

1. Maximum non-overlapping intervals: sort by **end**, greedily take.
2. "Minimum to remove" = total − "maximum to keep". Same problem.
3. "Minimum arrows" = maximum non-overlapping intervals. Same problem.
4. Check whether touching endpoints count as overlapping. `>` versus `>=`.
5. Sorting by start time, or by duration, is **wrong**. Have the counterexamples ready.

---

## 11.5 The interval family

The most-asked greedy topic in placements. Five problems, three sort keys.

### Merge Intervals (LC 56): sort by START

```cpp
vector<vector<int>> merge(vector<vector<int>>& iv) {
    sort(iv.begin(), iv.end());                       // by start (pair/vector default)

    vector<vector<int>> res;
    for (auto& x : iv) {
        if (res.empty() || res.back()[1] < x[0]) {
            res.push_back(x);                          // no overlap: start a new block
        } else {
            res.back()[1] = max(res.back()[1], x[1]);  // overlap: extend
        }
    }
    return res;
}
```

**`max` is mandatory in the extend step.** An interval can be entirely contained in the previous one: merging `[1,10]` with `[2,3]` must give `[1,10]`, not `[1,3]`. Writing `res.back()[1] = x[1]` passes many tests and fails on containment.

**Why start time here, when activity selection used end time?** Different goals. Merging needs intervals in the order they *begin*, so overlaps are adjacent and a single pass suffices. Selecting needs the one that *frees up soonest*. The goal determines the key.

### Insert Interval (LC 57): three phases, no sort

The input is already sorted, so this is O(n):

```cpp
vector<vector<int>> insert(vector<vector<int>>& iv, vector<int> ni) {
    vector<vector<int>> res;
    int i = 0, n = iv.size();

    while (i < n && iv[i][1] < ni[0])                 // 1. entirely before
        res.push_back(iv[i++]);

    while (i < n && iv[i][0] <= ni[1]) {              // 2. overlapping: absorb
        ni[0] = min(ni[0], iv[i][0]);
        ni[1] = max(ni[1], iv[i][1]);
        i++;
    }
    res.push_back(ni);

    while (i < n) res.push_back(iv[i++]);             // 3. entirely after
    return res;
}
```

Three loops, each with a clear meaning. Trying to do it in one loop with flags is where this problem goes wrong.

### Meeting Rooms (LC 252): can one person attend all?

```cpp
bool canAttendMeetings(vector<vector<int>>& iv) {
    sort(iv.begin(), iv.end());
    for (int i = 1; i < (int)iv.size(); i++)
        if (iv[i][0] < iv[i-1][1]) return false;
    return true;
}
```

### Meeting Rooms II / Minimum Platforms: maximum concurrency

Module 10.9 gave the heap version. The **two-pointer sweep** is the O(1)-extra-space alternative and is worth knowing:

```cpp
int minPlatforms(vector<int> arr, vector<int> dep) {
    sort(arr.begin(), arr.end());
    sort(dep.begin(), dep.end());

    int i = 0, j = 0, cur = 0, best = 0;
    while (i < (int)arr.size()) {
        if (arr[i] <= dep[j]) { cur++; i++; best = max(best, cur); }  // arrival
        else                  { cur--; j++; }                          // departure
    }
    return best;
}
```

**The insight: arrivals and departures do not need to stay paired.** You only care how many events of each type have happened by each moment, so sorting the two arrays independently is valid. That decoupling is what makes the sweep work, and it surprises people.

`arr[i] <= dep[j]` means a train arriving exactly when another departs still needs its own platform — the standard convention in the GeeksforGeeks version. LeetCode 253 uses the opposite convention. **Check.**

### Partition Labels (LC 763)

*Split a string so each letter appears in at most one part, maximising the number of parts.*

```cpp
vector<int> partitionLabels(const string& s) {
    vector<int> last(26);
    for (int i = 0; i < (int)s.size(); i++) last[s[i] - 'a'] = i;   // last occurrence

    vector<int> res;
    int start = 0, end = 0;
    for (int i = 0; i < (int)s.size(); i++) {
        end = max(end, last[s[i] - 'a']);      // extend the current part
        if (i == end) { res.push_back(end - start + 1); start = i + 1; }
    }
    return res;
}
```

This is an interval problem in disguise: each letter defines an interval from its first to its last occurrence, and you are merging overlapping ones. Recognising that is the whole problem.

### The sort-key summary

| Problem | Sort by | Greedy step |
|---|---|---|
| Merge intervals | **Start** | Extend or start a new block |
| Insert interval | (already sorted) | Three phases |
| Max non-overlapping / min removals / min arrows | **End** | Take if it starts after the last kept ends |
| Can attend all meetings | Start | Check adjacent pairs |
| Minimum rooms / platforms | Starts and ends **separately** | Sweep, counting concurrency |
| Partition labels | (last-occurrence array) | Extend until `i == end` |

### Must remember

1. **Merging sorts by start. Selecting sorts by end.** The goal decides.
2. `max(res.back()[1], x[1])` when merging — containment is real.
3. Insert Interval is three phases and needs no sort.
4. Minimum platforms: sort arrivals and departures independently and sweep.
5. Always check the touching-endpoints convention.
6. Partition Labels is interval merging on first/last occurrences.

---

## 11.6 Choosing the sort key

Since the sort key usually *is* the algorithm, here is how to choose it.

### The question to ask

> **"Which item, if I take it now, constrains my future choices the least?"**

That item should come first.

| Goal | Sort by | Because |
|---|---|---|
| Maximum count of non-overlapping | End time, ascending | Finishing earliest leaves the most room |
| Merge overlapping regions | Start time, ascending | Overlaps become adjacent |
| Maximum value per unit capacity | Value/weight ratio, descending | Each unit of capacity buys the most |
| Minimum number of groups | Depends: sweep the events | Concurrency is what you are measuring |
| Maximise profit with deadlines | Profit, descending | Fit the most valuable jobs first, as late as possible |
| Pair extremes (boats, two-sum-like) | Value, then two pointers | Pair the hardest item with the most helpful one |
| Minimum total waiting time | Duration, ascending | Short jobs first minimises cumulative wait |

### The candidate keys, and how to eliminate them

For any interval problem there are four plausible keys: start ascending, end ascending, duration ascending, duration descending. **Try to break each with a three-interval counterexample.** It takes two minutes and it is exactly the reasoning an interviewer wants to see.

For activity selection:

| Key | Counterexample | Result |
|---|---|---|
| Start ascending | `[0,10] [1,2] [3,4]` | Greedy 1, optimal 2 ❌ |
| Duration ascending | `[0,5] [4,6] [5,10]` | Greedy 1, optimal 2 ❌ |
| End ascending | none exists | ✅ provable |

### Must remember

1. Ask which choice constrains the future least.
2. Enumerate the plausible keys and try to break each.
3. Sorting by "the obvious thing" (start time, largest value) is usually wrong for selection problems.
4. Use a comparator with strict `<`, never `<=` (Module 0, Section C4).
5. If no sort key survives the counterexample test, the problem is DP.

---

## 11.7 Knapsack: where greedy works and where it breaks

### Fractional knapsack (greedy, correct)

*Items have value and weight, capacity W, items may be **split**.*

```cpp
double fractionalKnapsack(int W, vector<pair<int,int>> items) {   // {value, weight}
    sort(items.begin(), items.end(), [](const auto& a, const auto& b) {
        return (long long)a.first * b.second > (long long)b.first * a.second;  // v1/w1 > v2/w2
    });

    double total = 0;
    for (auto& [v, w] : items) {
        if (W >= w) { total += v; W -= w; }
        else { total += (double)v * W / w; break; }   // take the fraction that fits
    }
    return total;
}
```

**Cross-multiply instead of dividing.** `a.first * b.second > b.first * a.second` is the same comparison as `a.v/a.w > b.v/b.w` without floating-point error. Interviewers notice.

**Why greedy is correct here:** because items are divisible, the capacity is always filled exactly. Any solution that uses a unit of capacity on a lower-ratio item can be improved by swapping that unit for a higher-ratio one. That is the exchange argument, and the divisibility is what makes the swap possible at any granularity.

### 0/1 knapsack (greedy fails)

Items are indivisible. Watch the ratio greedy break:

```
Capacity W = 50
Item A: value 60,  weight 10   ratio 6.0
Item B: value 100, weight 20   ratio 5.0
Item C: value 120, weight 30   ratio 4.0

Greedy by ratio:  A (10) + B (20) = 30 used, value 160.
                  C needs 30, only 20 left, cannot split. Total = 160.

Optimal:          B (20) + C (30) = 50 used exactly. Total = 220.
```

The greedy commits to A because its ratio is highest, and that decision wastes capacity that B and C would have used perfectly. **Indivisibility breaks the exchange argument**: you cannot take "part of C" to fill the leftover 20.

This is the cleanest illustration in the handbook of why greedy needs proof. It is also the setup for Module 13, where 0/1 knapsack is the central DP.

### Must remember

1. Fractional knapsack is greedy by value/weight ratio, descending.
2. 0/1 knapsack is **DP**. Have the counterexample above memorised.
3. Divisibility is what makes the ratio greedy safe.
4. Cross-multiply to compare ratios and avoid floating point.
5. "Can I take part of an item?" is the question that decides greedy versus DP.

---

## 11.8 Job sequencing with deadlines

*Each job has a deadline and a profit, takes one unit of time, and must finish by its deadline. Maximise total profit.*

**Greedy:** sort by profit descending, and schedule each job in the **latest free slot** at or before its deadline.

```cpp
int jobScheduling(vector<array<int,2>> jobs, int maxDeadline) {   // {deadline, profit}
    sort(jobs.begin(), jobs.end(), [](const auto& a, const auto& b) {
        return a[1] > b[1];                            // profit descending
    });

    vector<bool> slotUsed(maxDeadline + 1, false);
    int total = 0;

    for (auto& [d, p] : jobs) {
        for (int t = min(d, maxDeadline); t >= 1; t--) {   // LATEST free slot
            if (!slotUsed[t]) { slotUsed[t] = true; total += p; break; }
        }
    }
    return total;
}
```

**Why the latest slot.** Scheduling a job as late as its deadline allows keeps the earlier slots free for jobs with tighter deadlines. Taking the earliest free slot instead can block a job that has no later option. This is "constrains the future least" again.

**Why profit descending is safe.** Exchange argument: if an optimal schedule omits the highest-profit job that greedy takes, you can remove one of its scheduled jobs and insert the higher-profit one in that slot (it fits, because the slot is at or before the greedy job's deadline). Profit does not decrease.

Complexity: O(n log n + n·d) with this implementation. A DSU (Module 12) tracking "the next free slot at or before t" reduces it to near O(n log n). **Mention the DSU optimisation; do not write it unless asked.**

**Priority: medium.** This is a GeeksforGeeks and service-company staple more than a LeetCode one.

---

## 11.9 Gas Station

**The greedy with the least obvious proof**, which is why it is asked.

*n stations in a circle. Station i has `gas[i]` fuel and costs `cost[i]` to reach station i+1. Find a starting station that lets you complete the circuit, or −1.*

```cpp
int canCompleteCircuit(const vector<int>& gas, const vector<int>& cost) {
    int total = 0, tank = 0, start = 0;

    for (int i = 0; i < (int)gas.size(); i++) {
        int diff = gas[i] - cost[i];
        total += diff;
        tank  += diff;

        if (tank < 0) {            // cannot reach i+1 from the current start
            start = i + 1;         // so try starting fresh at i+1
            tank = 0;
        }
    }
    return total >= 0 ? start : -1;
}
```

Six lines, one pass, O(1) space. Two claims make it correct.

### Claim 1: if the total is non-negative, a solution exists

Total fuel minus total cost is fixed regardless of where you start. If it is negative, no circuit is possible. If it is non-negative, some starting point works — and the algorithm finds it.

### Claim 2: if you run dry at station `i` starting from `s`, no station in `[s, i]` can be a valid start

This is the part worth being able to argue.

Suppose you start at `s` and the tank first goes negative at station `i`. Then for every `j` strictly between `s` and `i`, the tank was **non-negative** on arrival at `j` (otherwise `i` would not be the first failure).

Now consider starting at `j` instead. You would arrive at `i` having accumulated only the fuel from `j` to `i` — which is exactly what you accumulated when starting from `s`, **minus** the non-negative amount you were carrying when you reached `j`. So starting at `j` leaves you with less than or equal fuel at every point, and you fail at `i` too, or earlier.

Therefore the entire range `[s, i]` is eliminated in one step, which is why a single pass suffices.

### Must remember

1. Two variables: `total` decides *whether* a solution exists, `tank` finds *where*.
2. When the tank goes negative, reset the start to `i + 1` and the tank to 0.
3. The whole range from the old start to the failure point is eliminated at once. Be able to say why.
4. One pass, O(n) time, O(1) space. No need to try every start.
5. The answer is unique when the total is non-negative, which the problem usually guarantees.

---

## 11.10 Jump Game

Two problems, two greedies, both with clean arguments.

### Jump Game (LC 55): can you reach the end?

```cpp
bool canJump(const vector<int>& a) {
    int reach = 0;
    for (int i = 0; i < (int)a.size(); i++) {
        if (i > reach) return false;          // this index is unreachable
        reach = max(reach, i + a[i]);
    }
    return true;
}
```

**The insight: track the furthest reachable index, not the path.** You never need to know *how* you got somewhere, only whether you can. If every index up to `n-1` is reachable, you are done.

The check `if (i > reach) return false` fires the moment you hit a gap. Everything after a gap is unreachable, so you can stop immediately.

### Jump Game II (LC 45): minimum number of jumps

```cpp
int jump(const vector<int>& a) {
    int jumps = 0, curEnd = 0, farthest = 0;

    for (int i = 0; i + 1 < (int)a.size(); i++) {     // stop BEFORE the last index
        farthest = max(farthest, i + a[i]);

        if (i == curEnd) {                            // exhausted the current level
            jumps++;
            curEnd = farthest;
        }
    }
    return jumps;
}
```

**This is breadth-first search without a queue.** `curEnd` marks the end of the current "level" (everything reachable in `jumps` jumps), and `farthest` accumulates the end of the next level. When you reach the end of a level, you increment the jump count and move to the next.

**`i + 1 < n` is the loop bound, not `i < n`.** If the last index happens to coincide with `curEnd`, iterating over it would count one jump too many.

### Must remember

1. Jump Game I: track the furthest reachable index. Fail the moment `i > reach`.
2. Jump Game II: level-by-level, incrementing when `i == curEnd`. It is implicit BFS.
3. Loop to `n - 2` in Jump Game II, or you overcount by one.
4. Both are O(n) time, O(1) space. The DP versions are O(n²) and are the wrong answer.
5. Greedy is safe here because reachability is monotonic: if you can reach index `i`, you can reach everything before it.

---

## 11.11 Huffman coding

**Low-to-medium priority.** Know the idea and the greedy choice; implementation is rarely required.

### The problem

Assign variable-length binary codes to symbols so that frequent symbols get short codes and the total encoded length is minimised. Codes must be **prefix-free** (no code is a prefix of another) so decoding is unambiguous.

### The greedy

Repeatedly merge the **two least frequent** symbols into a single node whose frequency is their sum. Push it back. Repeat until one node remains; that is the root of the code tree. Left edges are 0, right edges are 1.

```cpp
// sketch
priority_queue<pair<int,Node*>, vector<...>, greater<...>> pq;   // min-heap by frequency
while (pq.size() > 1) {
    auto a = pq.top(); pq.pop();
    auto b = pq.top(); pq.pop();
    pq.push({a.first + b.first, new Node(a.second, b.second)});
}
```

O(n log n) with a heap, which is why it sits next to Module 10.

### Why the greedy choice is correct

The two least frequent symbols must be at the **deepest** level of an optimal tree, and they can be made **siblings**. Exchange argument: if the two deepest siblings in an optimal tree are not the two least frequent symbols, swapping them in does not increase the total cost, because you are moving lower-frequency symbols to deeper positions and higher-frequency ones to shallower positions. Merging them is therefore safe.

### Must remember

1. Merge the two smallest frequencies repeatedly; a min-heap does the work.
2. Produces a prefix-free code, which is what makes decoding unambiguous.
3. O(n log n), with `n - 1` merges.
4. Greedy is correct because the least frequent symbols belong deepest.
5. This is the classic "greedy plus heap" algorithm and worth recognising by name.

---

## 11.12 When greedy fails

### The catalogue

| Problem | Greedy gives | Why it fails | Correct approach |
|---|---|---|---|
| 0/1 Knapsack | 160 on the Section 11.7 example | Cannot split; capacity is wasted | DP |
| Coin Change, arbitrary coins | `{1,3,4}`, target 6: takes 4+1+1 = 3 coins | Optimal is 3+3 = 2 coins | DP |
| Longest Increasing Subsequence | Taking every increase | A small early element may beat a large one | DP / patience sorting |
| Weighted activity selection | Earliest finish | One heavy interval can beat three light ones | DP |
| Shortest path, negative edges | Dijkstra | A cheap later edge can undo an early commitment | Bellman-Ford |
| Travelling salesman | Nearest neighbour | Local shortcuts create expensive returns | DP (bitmask) / heuristics |
| Making change for the fewest **notes** in a non-canonical system | Largest first | Same as coin change | DP |

### The coin change counterexample, worked

This is the one to have ready, because the greedy feels so natural.

```
Coins: {1, 3, 4}      Target: 6

Greedy (largest first):  4, then 1, then 1  ->  3 coins
Optimal:                 3, then 3          ->  2 coins
```

The greedy takes the 4 because it is the largest that fits, and that commitment leaves a remainder of 2 which can only be made from 1s. Nothing about the local choice reveals this.

**Why real currency systems are greedy-safe:** denominations like `{1, 2, 5, 10, 20, 50}` are constructed so the greedy works (they are "canonical"). Problems deliberately use non-canonical sets to break it. Being able to say "greedy works for canonical coin systems but the general problem is DP" is a strong answer.

### The general warning sign

Greedy tends to fail when:

- Items are **indivisible** and there is a **hard capacity**.
- Choices are **weighted** rather than counted.
- An early commitment can **waste** a resource that a later combination would use exactly.
- The problem asks "how many **ways**" rather than "how many at most".

### Must remember

1. Coin change `{1,3,4}` with target 6 is the counterexample to memorise.
2. 0/1 knapsack with `W=50` and items `(60,10), (100,20), (120,30)` is the other.
3. Weights, indivisibility, and hard capacities are the warning signs.
4. DP is never wrong, only slower. When in doubt, use DP.
5. Being able to say *why* greedy fails is worth as much as knowing it fails.

---

## 11.13 Consolidation

### Recognition guide

| The statement says | Technique |
|---|---|
| "maximum number of non-overlapping" | Sort by end, greedy take |
| "minimum removals so nothing overlaps" | Same, as total − kept |
| "minimum arrows / minimum groups to cover" | Same |
| "merge overlapping intervals" | Sort by start, extend or push |
| "insert into a sorted interval list" | Three-phase scan, no sort |
| "minimum rooms / platforms / machines" | Sweep, or heap of end times |
| "can one person attend all" | Sort by start, check adjacent |
| "items can be **split**" | Greedy by ratio |
| "items **cannot** be split, hard capacity" | **DP** |
| "minimum coins", arbitrary denominations | **DP** |
| "can I reach the end" | Greedy furthest-reach |
| "minimum jumps" | Greedy levels (implicit BFS) |
| "circular route, will I run out" | Gas Station: total plus running tank |
| "assign / pair to maximise count" | Sort both, two pointers |
| "schedule to minimise waiting" | Sort by duration ascending |
| "merge the two smallest repeatedly" | Huffman / heap greedy |

### Must remember (consolidated)

1. Greedy needs the greedy choice property **and** optimal substructure. DP needs only the second.
2. The exchange argument: assume an optimal solution without your greedy choice, swap it in, show nothing worsens.
3. Spend two minutes trying to break a greedy before trusting it.
4. **Merging sorts by start. Selecting sorts by end.**
5. Use `max()` when extending a merged interval — containment is real.
6. Check the touching-endpoint convention: `>` versus `>=`.
7. Minimum platforms: sort arrivals and departures **independently** and sweep.
8. Fractional knapsack is greedy; 0/1 knapsack is DP. Divisibility is the reason.
9. Cross-multiply to compare ratios, avoiding floating point.
10. Job sequencing: profit descending, latest free slot before the deadline.
11. Gas Station: `total` decides existence, `tank` finds the start, and a failure eliminates the whole range.
12. Jump Game II loops to `n - 2` and is BFS in disguise.
13. Coin change with `{1,3,4}` and target 6 breaks the greedy.
14. Weights, indivisibility, and hard capacities are the signs that greedy will fail.
15. Comparators use strict `<`, never `<=`.

### Common mistakes (consolidated)

**Wrong answer**
- Sorting by start when the problem needs end (or vice versa).
- `res.back()[1] = x[1]` instead of `max(...)` when merging.
- Wrong touching-endpoint convention.
- Using greedy where DP is required (0/1 knapsack, arbitrary coin change).
- Off by one in Jump Game II (looping to `n - 1`).
- Scheduling jobs in the earliest free slot rather than the latest.
- Forgetting that `total >= 0` is what decides solvability in Gas Station.

**Time limit exceeded**
- O(n²) DP where an O(n) greedy exists (both Jump Game problems).
- Re-sorting inside a loop.
- Trying every starting point in Gas Station.

**Overflow**
- `lastEnd` as `int` in LC 452, where coordinates reach `INT_MAX`.
- Ratio comparison by multiplication without casting to `long long`.

**Justification failures**
- "It works on the examples" offered as a proof.
- Not being able to say why sorting by end is correct.
- Not recognising that a weighted version breaks the unweighted greedy.

---

## 11.14 Problem set

Twelve core problems. The interval family is over-represented because it is over-represented in interviews.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Merge Intervals (LC 56) | Medium | Sort by start | The `max()` in the extend step |
| Assign Cookies (LC 455) | Easy | Sort both, two pointers | The simplest exchange argument |
| Lemonade Change (LC 860) | Easy | Greedy denomination choice | Give the large note first; why it is safe |

### Level 2 — Pattern (4)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Insert Interval (LC 57) | Medium | Three-phase scan | Why three loops beat one loop with flags |
| Non-overlapping Intervals (LC 435) | Medium | Sort by end | The canonical greedy and its proof |
| Minimum Arrows to Burst Balloons (LC 452) | Medium | Sort by end | Same problem, different story, flipped boundary |
| Jump Game (LC 55) | Medium | Furthest reach | Track reachability, not paths |

### Level 3 — Interview (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| **Jump Game II (LC 45)** | Medium | Greedy levels | BFS without a queue; the `n-2` bound |
| **Gas Station (LC 134)** | Medium | Two-variable scan | The least obvious proof in the module |
| Meeting Rooms II (LC 253) | Medium | Sweep or heap | Two valid approaches; compare them |
| Partition Labels (LC 763) | Medium | Intervals in disguise | Recognising a hidden interval problem |
| Task Scheduler (LC 621) | Medium | Greedy + counting | Revisit from Module 10 with greedy framing |

### Level 4 — Advanced (4, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Candy (LC 135) | Hard | Two-pass greedy | When one pass cannot satisfy both directions |
| Job Sequencing with Deadlines (GFG) | Medium | Profit desc + latest slot | The "schedule late" insight |
| Fractional Knapsack (GFG) | Medium | Ratio greedy | The contrast with 0/1, before Module 13 |
| Minimum Platforms (GFG) | Medium | Independent sweep | Decoupling arrivals from departures |

**For every problem in this set, write one sentence justifying the greedy choice before you write code.** That habit is the module. If you cannot write the sentence, you do not yet know whether your solution is correct, and finding out by submitting is the wrong way round.

---

## Exit checklist

```
[ ] I can state the two conditions greedy requires
[ ] I can construct an exchange argument
[ ] I try to BREAK a greedy for two minutes before trusting it
[ ] I can explain why activity selection sorts by end time
[ ] I have counterexamples for sorting by start and by duration
[ ] I know merging sorts by start and selecting sorts by end
[ ] I use max() when extending a merged interval
[ ] I check the touching-endpoint convention every time
[ ] I can write Insert Interval as three phases
[ ] I can do minimum platforms both ways (heap and sweep)
[ ] I know why arrivals and departures can be sorted independently
[ ] I can explain why fractional knapsack is greedy and 0/1 is not
[ ] I have the 0/1 knapsack counterexample memorised
[ ] I have the coin change {1,3,4} counterexample memorised
[ ] I can explain both claims in Gas Station
[ ] I know Jump Game II is BFS in disguise and loops to n-2
[ ] I know the warning signs: weights, indivisibility, hard capacity
[ ] I write a one-sentence justification before coding any greedy
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 12"** for Graphs (22–28 hours, Tier 1). It is the largest module after DP and it reuses more of the handbook than anything so far: BFS runs on Module 7's queue, DFS on Module 4's recursion, Dijkstra on Module 10's heap, and Kruskal on Module 5's sorting.

It covers representation (and why adjacency lists win), BFS and DFS with the grid problems that dominate interviews, cycle detection in both directed and undirected graphs, topological sorting and the course-schedule family, the four shortest-path algorithms and when each applies, minimum spanning trees, and Union-Find — with the advanced topics (bridges, articulation points, SCC) clearly marked by placement priority so you can skip them without guilt.
