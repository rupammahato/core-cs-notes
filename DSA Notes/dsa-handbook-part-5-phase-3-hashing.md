# DSA Placement Handbook (C++) — Part 5
# Phase 3: Hashing

**Module 3 · 6–8 hours · Tier 1 · Requires: Modules 0, 1, 2**

---

## Why this module is short but high-leverage

Hashing has very little theory. You need one idea (trade space for time by making lookup O(1)) and four patterns. The reason it earns Tier 1 status is not depth, it is **reach**: hashing appears inside problems from every other topic in the roadmap. Graph problems use it for visited sets on non-integer nodes, DP uses it for memoisation on sparse states, string problems use it for canonical keys, and array problems use it to collapse an O(n²) scan into a single pass.

This module also closes out the two problems Module 2 deliberately left open: Subarray Sum Equals K, and every "find a pair" question on unsorted input.

The organising principle for the whole module:

> **Whenever a brute force asks "does something I have already seen satisfy a relationship with what I am looking at now?", the answer is a hash map.**

The inner loop that searches backwards is exactly what the map replaces.

---

## 3.1 How a hash table works

### 1. What is it?

A structure that stores key-value pairs and finds a key in O(1) average time by computing the key's storage location directly from the key itself.

### 2. Why do we need it?

Because searching an unsorted array is O(n) and searching a sorted one is O(log n) plus the cost of sorting. A hash table gets O(1) with no ordering requirement at all.

### 3. Core idea

```
key "apple"
     |
     v  hash function
   4821
     |
     v  mod bucket_count (say 8)
  bucket 5
     |
     v
 buckets: [0][1][2][3][4][5][6][7]
                         |
                         v
                    ("apple", 3) -> ("grape", 9)      <- a collision chain
```

Three moving parts:

**The hash function** turns a key into a large integer. Good hash functions spread keys uniformly.

**The bucket array** holds the actual data. Bucket index is `hash(key) % bucket_count`.

**Collision handling.** Two keys can land in the same bucket. C++ resolves this by **chaining**: each bucket holds a linked list of entries, and lookup walks the chain comparing keys with `==`.

### 4. Where the complexities come from

| Situation | Chain length | Lookup |
|---|---|---|
| Keys spread evenly | O(1) | **O(1) average** |
| All keys collide | O(n) | **O(n) worst case** |

That is the entire explanation for "average O(1), worst O(n)", and it is the standard interview follow-up. Being able to draw the bucket picture and say "worst case every key lands in one chain, so it degrades to a linked list" is a complete answer.

**Load factor and rehashing.** When `size / bucket_count` exceeds a threshold (1.0 by default in C++), the table allocates more buckets and redistributes everything. That is O(n), but it happens rarely enough to amortise to O(1) per insert, by the same doubling argument as `vector::push_back` (Module 1, Section 1.6).

### 5. Must remember

1. Average O(1), worst case O(n). Never claim O(1) worst case.
2. C++ `unordered_map` uses **chaining**, not open addressing. The standard mandates a bucket interface, which forces chaining.
3. A key type needs two things to be usable: a **hash function** and `operator==`. Built-in types and `string` have both. `pair` has `==` but no hash, which is why `unordered_map<pair<int,int>, int>` fails to compile.
4. Rehashing invalidates all iterators. Erasing invalidates only the erased one.
5. `reserve(n)` before inserting n items avoids repeated rehashing and is a genuine speedup on large inputs.
6. On Codeforces, adversarial tests can force collisions and blow up `unordered_map`. The defence is a randomised hash seed. **This is not a concern in placements or OAs**, but know the answer if asked.

### 6. Common interview questions on this section

- *"What's the worst case?"* O(n), when all keys hash to one bucket.
- *"How does C++ handle collisions?"* Separate chaining.
- *"Why is it amortised O(1) if rehashing is O(n)?"* Geometric growth; total cost over n inserts is O(n).
- *"When would you not use a hash map?"* When keys are small bounded integers (an array is faster), when you need sorted order or nearest-key queries (use `map`), or when you need worst-case guarantees.

---

## 3.2 Choosing the container

Module 0 covered the syntax. This section covers the decision, which is the part that matters.

### The decision rule

```
Are the keys small, bounded, non-negative integers (or letters)?
├─ YES -> vector<int> / array.  Faster than any hash map. Do this.
└─ NO
    │
    Do you need ANY of: sorted iteration, lower_bound/nearest key,
    min/max element, or guaranteed O(log n) worst case?
    ├─ YES -> map / set
    └─ NO  -> unordered_map / unordered_set     <- the default
```

### The case people get wrong

The most common mistake in this module is reaching for `unordered_map` out of habit when an array would do.

```cpp
// Counting characters: array wins, easily
vector<int> freq(26, 0);
for (char c : s) freq[c - 'a']++;

// NOT this
unordered_map<char, int> freq;
for (char c : s) freq[c]++;
```

Both are O(n). The array is several times faster (no hashing, no allocation, perfect cache locality) and comparison of two frequency arrays with `==` is one line. Use the map only when the key space is genuinely unbounded.

Same logic applies to visited arrays in graphs: if nodes are `0..n-1`, use `vector<bool>` or `vector<char>`, not `unordered_set<int>`.

### When you genuinely need `map` over `unordered_map`

| Need | Why only `map` works |
|---|---|
| Iterate keys in sorted order | `unordered_map` has no order at all |
| "Smallest key ≥ x" | `lower_bound` is a member of `map` only |
| Smallest / largest key | `map.begin()` / `map.rbegin()` |
| A custom struct key with `operator<` but no hash | Writing a hash is extra work |
| Guaranteed O(log n) worst case | Hash tables degrade to O(n) |

Everything else: `unordered_map`.

### set vs map

Use `set` / `unordered_set` when the only question is **"have I seen this?"**. Use `map` / `unordered_map` when you need to store something alongside the key: a count, an index, a list.

That distinction maps directly onto the patterns below:

| Pattern | Container | Stores |
|---|---|---|
| Duplicate detection | `unordered_set` | nothing, membership only |
| Frequency counting | `unordered_map<T,int>` | count |
| Two Sum | `unordered_map<int,int>` | value → index |
| Prefix sum counting | `unordered_map<ll,int>` | prefix → how many times seen |
| Longest subarray | `unordered_map<ll,int>` | prefix → **earliest** index |
| Grouping | `unordered_map<string, vector<T>>` | key → members |

---

## 3.3 Pattern: frequency counting and duplicate detection

### 1. What is it?

Counting occurrences, or checking membership, in one pass.

### 2. Why do we need it?

"Does this array contain a duplicate" is O(n²) with nested loops, O(n log n) with sorting, and O(n) with a set. "Which element appears most often" has the same three tiers. The hash version is usually optimal and always the shortest to write.

### 3. Core idea

Make the value the key. Lookup becomes O(1), so the inner loop disappears.

### 4. When should I use it?

- "Does X appear more than once", "find the duplicate", "find the missing element".
- "How many times does each element occur", "most/least frequent".
- "Is one array a permutation of another".
- Any time you would otherwise write a nested loop comparing every element to every other element.

### 5. How to recognise the pattern

Signals: "duplicate", "unique", "distinct", "appears exactly/at least k times", "most frequent", "first non-repeating", "anagram", "permutation of".

### 6. C++ templates

```cpp
// Seen-set: duplicate detection
bool containsDuplicate(const vector<int>& a) {
    unordered_set<int> seen;
    for (int x : a) {
        if (seen.count(x)) return true;    // count(), not [], for existence
        seen.insert(x);
    }
    return false;
}

// Frequency map
unordered_map<int,int> freq;
for (int x : a) freq[x]++;

// Most frequent element
int best = -1, bestCount = 0;
for (auto& [val, cnt] : freq)
    if (cnt > bestCount) { bestCount = cnt; best = val; }

// First non-repeating character (two passes, order preserved by the array)
int firstUniqChar(const string& s) {
    vector<int> freq(26, 0);
    for (char c : s) freq[c - 'a']++;
    for (int i = 0; i < (int)s.size(); i++)
        if (freq[s[i] - 'a'] == 1) return i;
    return -1;
}
```

Note the last one: the **order comes from scanning the original string**, not from the map. A hash map cannot give you "first" anything. If you need order, the second pass goes over the input, not the container.

### 7. Example

Given `[1,2,3,1]`, the seen-set returns true at index 3. One pass, O(n) time, O(n) space, versus O(n²) for the nested loop.

### 8. Complexity

O(n) time average, O(n) space. Compare: sorting gives O(n log n) time but O(1) space, which is the right answer when the interviewer adds "in O(1) space".

### 9. Must remember

1. Use `count()` or `find()` to test existence, never `[]`. `mp[key]` **inserts** a default value when the key is absent, which grows the container during what you thought was a read.
2. `unordered_map` iteration order is arbitrary and can differ between runs. Never rely on it for "first" or "order of appearance"; scan the input instead.
3. For bounded keys (letters, digits, small ints) use an array. Faster and comparable with `==`.
4. Two frequency arrays compare in one line: `have == need`. Two frequency *maps* also compare with `==`, and it works, but it is O(n) and order-independent, which is fine.
5. When you need frequency **and** order, pair the map with a vector, or make a second pass over the input.

### 10. Common mistakes

- `if (mp[x])` as an existence check, silently inserting `x`.
- Relying on `unordered_map` iteration order.
- Using a map where a 26-element array was obvious.
- Forgetting that `freq[c - 'a']` assumes lowercase-only input.

### 11. Practice

- Contains Duplicate (LC 217, Easy)
- Valid Anagram (LC 242, Easy)
- First Unique Character in a String (LC 387, Easy)
- Top K Frequent Elements (LC 347, Medium) — frequency map plus bucket sort or a heap; previews Module 10

---

## 3.4 Pattern: complement lookup (the Two Sum family)

### 1. What is it?

While scanning, ask the map whether the **complement** of the current element has already been seen. If yes, you have found your pair in one pass.

### 2. Why do we need it?

It is the canonical O(n²) → O(n) conversion, and Two Sum is plausibly the most-asked interview question in existence. More importantly, the *shape* generalises: any problem of the form "find two things whose combination hits a target" is a candidate.

### 3. Core idea

```
a = [2, 7, 11, 15]   target = 9

i=0: x=2, need 7. seen = {}          -> not found. store 2 -> 0
i=1: x=7, need 2. seen = {2:0}       -> FOUND. return {0, 1}
```

The key insight: **you only need to look backwards**, and the map remembers everything backwards for free. A pair `(i, j)` with `i < j` will be found when you reach `j`.

### 4. When should I use it?

- "Two numbers that sum to target", on **unsorted** input, or when you must return **original indices**.
- Any "does a matching partner exist" question: pairs with a given difference, pairs that sum to a multiple, complementary bitmasks.
- As the inner engine of harder problems: 4Sum II splits four arrays into two halves and matches sums across them.

### 5. How to recognise the pattern

Signals: "two elements such that", "a pair whose sum/difference is", "return the indices", "unsorted array". 

**The fork versus two pointers** (Module 2.7):

| | Hash map | Sort + two pointers |
|---|---|---|
| Input sorted? | Irrelevant | Required |
| Time | O(n) | O(n log n) |
| Space | O(n) | O(1) |
| Original indices | **Preserved** | Destroyed |
| Returns | Indices or values | Values |

If the problem asks for indices, the hash map is the answer. If it asks for values and wants O(1) space, sorting is the answer. **Say the trade-off out loud**; interviewers ask "can you do better on space?" precisely to see whether you know there are two solutions.

### 6. C++ template

```cpp
vector<int> twoSum(const vector<int>& a, int target) {
    unordered_map<int,int> seen;                 // value -> index
    for (int i = 0; i < (int)a.size(); i++) {
        int need = target - a[i];
        if (seen.count(need)) return {seen[need], i};
        seen[a[i]] = i;                          // store AFTER checking
    }
    return {};
}
```

**Store after checking, not before.** Storing first means an element can match itself when `target == 2 * a[i]`.

### 7. Example: pairs with a given difference

```cpp
// Count pairs (i, j) with a[j] - a[i] == k
int countPairs(const vector<int>& a, int k) {
    unordered_map<int,int> freq;
    int res = 0;
    for (int x : a) {
        res += freq.count(x - k) ? freq[x - k] : 0;
        freq[x]++;
    }
    return res;
}
```

Same shape: check the complement, then record the current element.

### 8. Complexity

O(n) time average, O(n) space. Worst case O(n²) if every key collides, which does not happen in practice on placement tests.

### 9. Must remember

1. Check the complement **before** inserting the current element. Otherwise an element pairs with itself.
2. Store value → index when you must return indices; store value → count when you must count pairs.
3. With duplicates and a count-based version, the "check then insert" order also prevents double counting.
4. `target - a[i]` can overflow `int` if values are large. Cast to `long long` when constraints allow it.
5. This pattern only finds pairs. For triplets, fix one element with an outer loop and apply it to the rest, giving O(n²) — though for 3Sum, sort plus two pointers (Module 2.7) is cleaner because deduplication is easier.

### 10. Common mistakes

- Inserting before checking, returning `{i, i}`.
- Using `seen[need]` to test existence, inserting a spurious key.
- Overflow in `target - a[i]`.
- Reaching for a hash map on already-sorted input where two pointers gives O(1) space.

### 11. Practice

- Two Sum (LC 1, Easy)
- 4Sum II (LC 454, Medium) — split into two halves, hash the first, look up the second
- Two Sum II (LC 167, Easy) — solve it both ways and compare the trade-off out loud

---

## 3.5 Pattern: prefix sum + hash map

**This is the most important section in the module.** It is the pattern that Module 2 deliberately deferred, and it converts an entire family of O(n²) subarray problems into O(n).

### 1. What is it?

Combine prefix sums (Module 2.5) with a hash map so that "how many subarrays have property P" becomes a single pass.

### 2. Why do we need it?

Sliding window handles contiguous-range problems only when values are non-negative (Module 2.8). The moment negatives appear, shrinking no longer restores validity and the window breaks. Prefix sum plus hash map has no such restriction. It is the general tool.

### 3. Core idea

Recall that the sum of `a[l..r]` is `pre[r+1] - pre[l]`. Rearranged:

```
sum(l..r) == k
pre[r+1] - pre[l] == k
pre[l] == pre[r+1] - k
```

So while scanning with a running prefix sum, the question "does a subarray ending here have sum k?" becomes **"have I seen the prefix value `sum - k` before?"** That is a hash lookup.

```
a = [1, 2, 3],  k = 3

i   a[i]  sum   sum-k   map before this step        found
0    1      1     -2    {0:1}                       no
1    2      3      0    {0:1, 1:1}                   YES (count 1)  -> [1,2]
2    3      6      3    {0:1, 1:1, 3:1}              YES (count 1)  -> [3]

answer: 2
```

### 4. The seed that everyone forgets

```cpp
cnt[0] = 1;
```

This represents the **empty prefix**, and it is what lets a subarray starting at index 0 be counted. Without it, `[1,2]` in the example above is missed, because `sum - k == 0` has no match.

For the index-based variant the equivalent seed is:

```cpp
first[0] = -1;
```

Index −1 means "the position before the array starts", so `i - (-1) = i + 1` gives the correct length for a prefix that starts at 0.

**These two lines are the single highest-value thing to memorise in this module.**

### 5. The two variants (do not mix them up)

| Goal | Map stores | Insert rule | Record |
|---|---|---|---|
| **Count** subarrays with sum k | prefix → **how many times seen** | always `cnt[sum]++` | `res += cnt[sum - k]` |
| **Longest** subarray with sum k | prefix → **earliest index** | only `if (!mp.count(sum))` | `best = max(best, i - mp[sum-k])` |

The insert rule is the crux. For counting you want every occurrence. For longest you want only the **first** occurrence of each prefix value, because the earliest left boundary gives the longest span. Overwriting with later indices silently produces shorter answers.

### 6. C++ templates

**Count subarrays with sum exactly k** (LC 560):

```cpp
int subarraySum(const vector<int>& a, int k) {
    unordered_map<long long,int> cnt;
    cnt[0] = 1;                                 // empty prefix
    long long sum = 0;
    int res = 0;
    for (int x : a) {
        sum += x;
        auto it = cnt.find(sum - k);
        if (it != cnt.end()) res += it->second;
        cnt[sum]++;
    }
    return res;
}
```

**Longest subarray with sum exactly k**:

```cpp
int longestSubarraySum(const vector<int>& a, long long k) {
    unordered_map<long long,int> first;
    first[0] = -1;                              // empty prefix at index -1
    long long sum = 0;
    int best = 0;
    for (int i = 0; i < (int)a.size(); i++) {
        sum += a[i];
        auto it = first.find(sum - k);
        if (it != first.end()) best = max(best, i - it->second);
        if (!first.count(sum)) first[sum] = i;  // EARLIEST only
    }
    return best;
}
```

**Count subarrays with sum divisible by k** (LC 974):

```cpp
int subarraysDivByK(const vector<int>& a, int k) {
    unordered_map<int,int> cnt;
    cnt[0] = 1;
    int sum = 0, res = 0;
    for (int x : a) {
        sum += x;
        int r = ((sum % k) + k) % k;            // C++ % goes negative
        res += cnt[r];
        cnt[r]++;
    }
    return res;
}
```

The key change: bucket by **remainder** rather than by the sum itself. Two prefixes with the same remainder differ by a multiple of k. The `((x % k) + k) % k` normalisation is mandatory because C++ `%` returns a negative result for negative operands (Module 0, Section A1), and skipping it produces wrong answers only on inputs containing negatives.

**Longest subarray with equal 0s and 1s** (LC 525):

```cpp
int findMaxLength(const vector<int>& a) {
    unordered_map<int,int> first;
    first[0] = -1;
    int sum = 0, best = 0;
    for (int i = 0; i < (int)a.size(); i++) {
        sum += (a[i] == 1 ? 1 : -1);            // the transform
        auto it = first.find(sum);
        if (it != first.end()) best = max(best, i - it->second);
        else first[sum] = i;
    }
    return best;
}
```

The trick worth internalising: **map 0 to −1, and "equal counts" becomes "sum equals zero"**. This transform recurs constantly. Any "equal number of X and Y" problem becomes a sum-zero problem by scoring +1 and −1.

Note that here `sum - k` with `k = 0` is just `sum`, so we look up the same value we are about to store, and the `else` branch handles the earliest-only rule in one line.

### 7. Example

`a = [1, -1, 5, -2, 3]`, longest subarray with sum 3.
Prefixes: 0, 1, 0, 5, 3, 6. At `i = 3` (prefix 3), we need `3 - 3 = 0`, first seen at index −1, so length `3 - (-1) = 4`. The subarray is `[1,-1,5,-2]`. ✓

### 8. Complexity

O(n) time average, O(n) space. Compare with the O(n²) brute force over all subarrays, or O(n³) if you also re-sum each.

### 9. Must remember

1. **`cnt[0] = 1`** for counting, **`first[0] = -1`** for longest. Without them, subarrays starting at index 0 are missed.
2. **Counting stores frequencies and always inserts. Longest stores the earliest index and inserts only if absent.** Mixing these is the standard bug.
3. Use `long long` for the running prefix sum.
4. Normalise modulo with `((x % k) + k) % k` whenever negatives are possible.
5. "Equal numbers of A and B" → score +1 / −1 → "sum equals zero".
6. This pattern works with negative numbers; sliding window does not. That is the whole reason it exists, and it is the interview answer to "why not use a sliding window here?"
7. A zero-sum subarray exists iff some prefix value repeats. Same machinery, `k = 0`.

### 10. Common mistakes

- Omitting the `cnt[0] = 1` or `first[0] = -1` seed.
- Overwriting the earliest index in the longest variant.
- Using `int` for the prefix sum.
- Forgetting the modulo normalisation with negative values.
- Applying a sliding window to a sum problem that contains negatives.
- Confusing the count variant's `res += cnt[sum-k]` with `res++`.

### 11. Practice

- Subarray Sum Equals K (LC 560, Medium) — the canonical one
- Contiguous Array (LC 525, Medium) — the +1/−1 transform
- Subarray Sums Divisible by K (LC 974, Medium) — remainder bucketing
- Longest Subarray with Sum K (GeeksforGeeks) — the earliest-index variant, with negatives allowed

---

## 3.6 Pattern: canonical key / grouping

### 1. What is it?

Map every item to a **canonical form**, then group items by that form. Two items belong together iff their canonical forms are identical.

### 2. Why do we need it?

Comparing every pair to see if they belong together is O(n²) comparisons, each possibly O(k). Canonicalising is O(n·k) total and the grouping is free.

### 3. Core idea

```
"eat"  -> sort -> "aet"  \
"tea"  -> sort -> "aet"   > all land in the same bucket
"ate"  -> sort -> "aet"  /
"tan"  -> sort -> "ant"  \
"nat"  -> sort -> "ant"   > different bucket
```

The canonical form is whatever makes equivalent things identical. For anagrams it is the sorted string, or the character-count signature. For "equivalent up to rotation" it might be the lexicographically smallest rotation. For numbers it might be the prime factorisation.

### 4. When should I use it?

Signals: "group by", "find all X that are Y-equivalent", "anagrams", "how many pairs are permutations of each other", "collect duplicates together".

### 5. C++ template

```cpp
vector<vector<string>> groupAnagrams(const vector<string>& words) {
    unordered_map<string, vector<string>> groups;

    for (const string& w : words) {
        string key = w;
        sort(key.begin(), key.end());          // canonical form
        groups[key].push_back(w);
    }

    vector<vector<string>> res;
    res.reserve(groups.size());
    for (auto& [k, v] : groups) res.push_back(move(v));
    return res;
}
```

`groups[key].push_back(w)` works on a missing key because `operator[]` default-constructs the empty vector first. This is the one place where the insert-on-read behaviour of `[]` is exactly what you want.

**The O(k) key variant**, when words are long enough that the sort matters:

```cpp
string countKey(const string& w) {
    vector<int> c(26, 0);
    for (char ch : w) c[ch - 'a']++;
    string key;
    for (int i = 0; i < 26; i++) {
        key += '#';                            // separator is REQUIRED
        key += to_string(c[i]);
    }
    return key;
}
```

The separator matters. Without it, counts `[1, 11]` and `[11, 1]` both render as `"111"`. A tempting shortcut is `string key(26, '0'); key[c - 'a']++;` which stores counts directly as characters, but that silently breaks once any count exceeds the char range. Use the separator version, or just sort the string.

### 6. Complexity

| Approach | Time | Notes |
|---|---|---|
| Sorted-string key | O(n · k log k) | n words of length k; simplest, usually fine |
| Count-signature key | O(n · k) | Faster asymptotically, more code |

Space O(n · k) for the groups.

### 7. Must remember

1. `mp[key].push_back(x)` is the idiomatic grouping line and relies on `operator[]` default-constructing.
2. The canonical form must be **identical** for equivalent items, not merely similar. A hash of the counts is not a canonical form; it is a hash, and it can collide.
3. Use a separator in any concatenated-count key.
4. Sorted-string keys are O(k log k) each but take one line. Prefer them unless the constraints say otherwise.
5. `unordered_map<string, vector<string>>` is fine; `string` has a built-in hash.
6. `move(v)` when extracting groups avoids copying every vector. Minor, but free.

### 8. Common mistakes

- Concatenating counts without a separator.
- Using `string key(26,'0')` with `key[c-'a']++` and overflowing the char on long words.
- Sorting the original word instead of a copy, destroying the input.
- Building the result by iterating the map and expecting a particular order.

### 9. Practice

- Group Anagrams (LC 49, Medium)
- Find All Anagrams in a String (LC 438, Medium) — revisit from Module 2, now with the key idea explicit

---

## 3.7 Pattern: set-based scanning

A smaller pattern, but it produces one of the most instructive problems in the module.

### Longest Consecutive Sequence (LC 128)

Given an unsorted array, find the length of the longest run of consecutive integers. Sorting gives O(n log n). The hash solution is O(n).

```cpp
int longestConsecutive(const vector<int>& a) {
    unordered_set<int> s(a.begin(), a.end());
    int best = 0;

    for (int x : s) {
        if (s.count(x - 1)) continue;          // x is not a sequence START, skip
        int cur = x, len = 1;
        while (s.count(cur + 1)) { cur++; len++; }
        best = max(best, len);
    }
    return best;
}
```

**Why this is O(n) despite the nested loop.** The inner `while` only runs for elements `x` where `x - 1` is absent, meaning `x` starts a sequence. Every element is walked over by exactly one such run. Total inner-loop work across the whole function is O(n). This is the same amortisation argument as the monotonic stack (Module 1, Section 1.6), and it is precisely what the interviewer is checking when they ask for the complexity.

Remove the `if (s.count(x - 1)) continue;` line and the algorithm becomes O(n²) while still producing correct answers. That single guard is the whole problem.

### Must remember

1. The "only start from sequence beginnings" guard is what makes it linear.
2. Iterate the **set**, not the array, to avoid repeating work on duplicates.
3. The complexity argument is "each element is visited by exactly one run". Rehearse saying it.

---

## 3.8 C++ pitfalls specific to hashing

Consolidated, because these cause real bugs.

### 1. `operator[]` inserts

```cpp
unordered_map<int,int> mp;
if (mp[5] > 0) { }        // mp now contains key 5 with value 0
cout << mp.size();        // 1, not 0
```

Use `mp.count(5)` or `mp.find(5) != mp.end()`. This also means `mp[key]` does not compile on a `const unordered_map&`; use `mp.at(key)` (throws if absent) or `find`.

### 2. `pair` keys do not compile

```cpp
unordered_map<pair<int,int>, int> bad;        // no std::hash for pair
```

Three fixes, in interview-preference order:

```cpp
// A. Use map instead. Costs a log factor, costs zero thought.
map<pair<int,int>, int> ok;

// B. Encode into one integer, when one component is bounded
unordered_map<long long,int> enc;
enc[(long long)r * COLS + c] = v;              // grid cells

// C. Write a hash functor
struct PairHash {
    size_t operator()(const pair<int,int>& p) const {
        return hash<long long>()(((long long)p.first << 32) ^ (unsigned)p.second);
    }
};
unordered_map<pair<int,int>, int, PairHash> custom;
```

Option B is the one to reach for in grid problems: `r * cols + c` flattens a cell into a single integer, and the same trick turns a `vector<vector<bool>>` visited grid into a `vector<bool>`.

### 3. No ordering, ever

`unordered_map` iteration order is unspecified and can differ between compilers, runs, and standard library versions. If a problem expects output in a particular order, sort at the end or track order separately.

### 4. No `lower_bound`

If you catch yourself wanting "the nearest key", you need `map` or a sorted vector plus `std::lower_bound`.

### 5. Erasing while iterating

```cpp
for (auto it = mp.begin(); it != mp.end(); ) {
    if (shouldRemove(it->first)) it = mp.erase(it);
    else ++it;
}
```

`mp.erase(it); ++it;` is undefined behaviour. The returned iterator is the only safe way forward.

### 6. `reserve` for speed

```cpp
unordered_map<int,int> mp;
mp.reserve(n);                 // avoids repeated rehashing
```

Free performance on large inputs. Worth mentioning in an interview as an optimisation you know about.

### 7. Custom struct keys need both

A hash **and** `operator==`. Providing only one produces a confusing compiler error. If you need a struct key, `map` with `operator<` is usually less work.

---

## 3.9 Comparison tables

### Sliding window vs prefix sum + hash map

This is the fork you will face most often, so it deserves its own table.

| | Sliding window | Prefix sum + hash map |
|---|---|---|
| Values may be negative | **No** (for sum problems) | **Yes** |
| Space | O(1) or O(alphabet) | O(n) |
| Natural questions | Longest / shortest valid window | Count of subarrays, longest with exact sum |
| "At most k" constraints | Natural fit | Awkward |
| "Exactly k" sum | Only if non-negative | Natural fit |
| Time | O(n) | O(n) |

Rule of thumb: **"at most / at least" with non-negative values → window. "Exactly k" or negatives present → prefix + map.**

### Hash map vs sorting

| | Hash map | Sorting |
|---|---|---|
| Time | O(n) average | O(n log n) |
| Space | O(n) | O(1) possible |
| Preserves indices | Yes | No |
| Gives order | No | Yes |
| Worst case | O(n²) | O(n log n) guaranteed |

When an interviewer says "now do it in O(1) space", they are asking you to switch from the map to sorting (and usually two pointers).

### Array vs hash map for counting

| | `vector<int>(k)` | `unordered_map` |
|---|---|---|
| Keys | Small, bounded, non-negative | Anything |
| Constant factor | Very small | Several times larger |
| Whole-container compare | `==`, O(k) | `==`, works but slower |
| Memory | k ints | n entries + buckets |

Default to the array whenever the key space allows it.

---

## 3.10 Must remember (consolidated)

1. `cnt[0] = 1` for counting subarrays; `first[0] = -1` for longest subarray. Missing seeds are the module's signature bug.
2. Counting variant: store frequencies, always insert. Longest variant: store **earliest** index, insert only if absent.
3. Check the complement **before** inserting the current element in Two Sum.
4. `mp[key]` inserts. Use `count` or `find` to test existence.
5. Average O(1), worst O(n). C++ resolves collisions by chaining.
6. `unordered_map` has no ordering. Never rely on iteration order.
7. No `lower_bound` on unordered containers; that is what `map` is for.
8. `unordered_map<pair<int,int>, int>` needs a custom hash, or encode the pair as `r * cols + c`, or use `map`.
9. Normalise modulo with `((x % k) + k) % k` when negatives are possible.
10. "Equal number of A and B" → score +1/−1 → "sum equals zero".
11. Use `long long` for prefix sums.
12. For bounded keys, an array beats any hash map.
13. Prefix + hash map works with negatives; sliding window does not.
14. In Longest Consecutive Sequence, the "only start at sequence beginnings" guard is what makes it O(n).
15. `reserve(n)` before bulk insertion avoids rehashing.

---

## 3.11 Common mistakes (consolidated)

**Wrong answer**
- Missing `cnt[0] = 1` or `first[0] = -1`.
- Overwriting the earliest index in the longest-subarray variant.
- Inserting before checking in Two Sum, matching an element with itself.
- Negative modulo without normalisation.
- Relying on `unordered_map` iteration order for "first" or "smallest".
- Concatenated count keys without a separator.

**Time limit exceeded**
- Dropping the sequence-start guard in Longest Consecutive Sequence, making it O(n²).
- Using `map` where `unordered_map` would do, in a tight loop.
- Using a hash map where a bounded array would do.
- Rebuilding a frequency map inside a loop.

**Overflow**
- `int` prefix sums.
- `target - a[i]` with large values.

**Compile error**
- `unordered_map` with a `pair` or struct key and no hash.
- `mp[key]` on a `const` map.
- Custom key with a hash but no `operator==`.

**Undefined behaviour**
- `mp.erase(it); ++it;`
- Holding an iterator across an insertion that triggers rehashing.

---

## 3.12 Problem set

Ten core problems plus two optional. Each teaches something distinct.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Two Sum (LC 1) | Easy | Complement lookup | The O(n²) → O(n) conversion; check-then-insert |
| Contains Duplicate (LC 217) | Easy | Seen set | Membership, and `count` vs `[]` |
| Valid Anagram (LC 242) | Easy | Frequency array | Why the array beats the map here |

### Level 2 — Pattern (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Group Anagrams (LC 49) | Medium | Canonical key | `mp[key].push_back`, and what "canonical" means |
| Top K Frequent Elements (LC 347) | Medium | Frequency + selection | Frequency map plus bucketing; previews heaps |
| First Unique Character (LC 387) | Easy | Frequency + ordered scan | Order comes from the input, not the map |

### Level 3 — Interview (4)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Subarray Sum Equals K (LC 560) | Medium | Prefix + hash (count) | The `cnt[0] = 1` seed; the module's centrepiece |
| Contiguous Array (LC 525) | Medium | +1/−1 transform | Turning "equal counts" into "sum zero" |
| Subarray Sums Divisible by K (LC 974) | Medium | Remainder bucketing | Negative modulo normalisation |
| Longest Consecutive Sequence (LC 128) | Medium | Set scanning | Why the start-guard makes it linear |

### Level 4 — Optional (2)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| 4Sum II (LC 454) | Medium | Split + hash | Meet-in-the-middle with a map |
| Longest Subarray with Sum K (GFG) | Medium | Prefix + hash (longest) | The earliest-index insert rule, with negatives |

Solve LC 560 and the GFG longest-subarray problem **back to back**. They look nearly identical and require different insert rules. Doing them consecutively is the fastest way to make that distinction permanent.

---

## Exit checklist

```
[ ] I can draw the bucket/chain picture and explain average O(1), worst O(n)
[ ] I know C++ uses chaining for collisions
[ ] I default to unordered_* and know exactly when map is required
[ ] I use an array instead of a map whenever keys are bounded
[ ] I test existence with count/find, never with []
[ ] I can write Two Sum from memory and explain check-then-insert
[ ] I can state the hash-map vs sort+two-pointers trade-off out loud
[ ] I can write subarraySum (count) with cnt[0] = 1 from memory
[ ] I can write longest-subarray-with-sum-k with first[0] = -1 from memory
[ ] I know which variant stores counts and which stores earliest index
[ ] I know the +1/-1 transform for "equal number of A and B"
[ ] I normalise negative modulo
[ ] I can explain why prefix+hash handles negatives but sliding window doesn't
[ ] I can explain why Longest Consecutive Sequence is O(n)
[ ] I know three ways to handle a pair key
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 4"** for Recursion Fundamentals (6–8 hours). This is the module I moved forward from your original outline, because merge sort and quick sort in Phase 5 are recursion problems wearing a sorting costume, and their complexity is unreadable without recurrences.

It covers recursion anatomy and the call stack, how to construct a recursive solution rather than memorise one, the "recursive contract" mindset that makes trees easy later, recursion tree analysis, and the tail end of the module introduces memoisation, which is the bridge to dynamic programming in Module 13.
