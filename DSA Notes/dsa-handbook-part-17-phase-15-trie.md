# DSA Placement Handbook (C++) — Part 17
# Phase 15: Trie (Prefix Tree)

**Module 15 · 5–6 hours · Tier 3 · Requires: Modules 0, 3, 9, 14**

*The last teaching module. This is the roadmap's Trie module, moved after Trees so that it takes three hours instead of six.*

---

## What this module is really about

A trie is a tree with 26 children. Structurally there is almost nothing to learn once Module 9 is done — insert walks down creating nodes, search walks down checking them, and both are ten lines.

The content that actually matters is **judgement**: a trie is frequently the wrong answer. For exact lookup a hash map is faster, simpler, and uses a fraction of the memory. The trie earns its place only when **prefixes** matter, and Section 15.5 is about recognising when that is true.

Beyond that, two applications are worth the time: **Word Search II**, where a trie turns an intractable k-word grid search into one pass, and the **XOR trie**, which is a genuinely different use of the same structure and the one place where Module 14's bit operations pay off in an interview.

**Tier 3 note:** tries appear in interviews, but not often. If you are short on time, learn Sections 15.1 to 15.5 (one hour), know that Word Search II and the XOR trie exist, and spend the rest elsewhere. If you have the time, the module is cheap and the XOR trie is a satisfying result.

---

## 15.1 What a trie is

### 1. What is it?

A tree where each **edge** is a character and each **path from the root** spells a prefix. Words sharing a prefix share the path for that prefix.

### 2. Why do we need it?

Because a hash map stores strings as opaque keys. It can tell you "is `apple` present?" in O(1), but it cannot tell you "which stored words start with `app`?" without scanning everything. A trie makes that second question O(prefix length), independent of how many words are stored.

### 3. Core idea

```
Words: "cat", "car", "card", "dog"

              (root)
             /      \
            c        d
            |        |
            a        o
           / \       |
          t*  r*     g*
              |
              d*

  * marks isEnd: a word terminates here
```

Two things to notice:

**The shared prefix is stored once.** `cat`, `car`, and `card` share `ca`. That is the space win and the reason prefix queries are cheap.

**`isEnd` is essential.** Without it you cannot distinguish "`car` is a stored word" from "`car` is merely a prefix of `card`". The node for `r` is both, which is exactly why the flag is needed.

### 4. The key property

**Operations cost O(L), where L is the word length — independent of `n`, the number of words stored.**

A trie with a million words answers a five-character prefix query in five steps. That independence from `n` is the whole selling point.

### 5. Must remember

1. Edges are characters; paths are prefixes.
2. `isEnd` distinguishes a stored word from a prefix of one. Never omit it.
3. All operations are O(L), independent of the number of stored words.
4. Shared prefixes are stored once.
5. A trie is a tree. Everything from Module 9 about traversal applies.

---

## 15.2 Node design

### The array form (lowercase letters)

```cpp
struct TrieNode {
    TrieNode* child[26] = {nullptr};
    bool isEnd = false;
};
```

Fast: indexing is `c - 'a'`, an O(1) array access with no hashing.

Costly: **26 pointers per node, 208 bytes on a 64-bit system**, whether or not they are used. A trie of `n` words of length `L` can reach `n × L` nodes, so 10⁵ words of length 10 is up to 10⁶ nodes and 200 MB. That is a real memory-limit failure, and it is the trie's main practical weakness.

### The map form (large or unknown alphabets)

```cpp
struct TrieNode {
    unordered_map<char, TrieNode*> child;
    bool isEnd = false;
};
```

Uses memory proportional to the children that actually exist. Slower per step (hashing) but far smaller on sparse tries. Use this for Unicode, mixed case, or any alphabet beyond a few dozen symbols.

### Which to use

| Situation | Node type |
|---|---|
| Lowercase a–z, dense | `child[26]` |
| Digits only | `child[10]` |
| Binary (XOR trie) | `child[2]` |
| Mixed case, punctuation, Unicode | `unordered_map` |
| Memory is tight and the trie is sparse | `unordered_map` |

### A useful extra field

Storing `int count` (how many words pass through this node) or `string word` (the complete word, at terminal nodes) turns several problems into one-liners. Word Search II uses the second; deletion uses the first.

### Must remember

1. `child[26]` is fast and memory-hungry; `unordered_map` is the reverse.
2. 26 pointers is roughly 208 bytes per node. Do the arithmetic before allocating.
3. `= {nullptr}` in the member initialiser zeroes the whole array. Forgetting it leaves garbage pointers.
4. Extra fields (`count`, `word`) often simplify the problem more than they cost.

---

## 15.3 Insert, search, and startsWith

### The full implementation (LC 208)

```cpp
class Trie {
    struct Node {
        Node* child[26] = {nullptr};
        bool isEnd = false;
    };
    Node* root;

    // Walk down the trie following `s`. Returns the final node, or nullptr.
    Node* walk(const string& s) {
        Node* cur = root;
        for (char c : s) {
            int i = c - 'a';
            if (!cur->child[i]) return nullptr;
            cur = cur->child[i];
        }
        return cur;
    }

public:
    Trie() { root = new Node(); }

    void insert(const string& w) {
        Node* cur = root;
        for (char c : w) {
            int i = c - 'a';
            if (!cur->child[i]) cur->child[i] = new Node();   // create as needed
            cur = cur->child[i];
        }
        cur->isEnd = true;                                    // mark the terminal
    }

    bool search(const string& w) {
        Node* n = walk(w);
        return n != nullptr && n->isEnd;                      // must be a WORD
    }

    bool startsWith(const string& p) {
        return walk(p) != nullptr;                            // prefix is enough
    }
};
```

**The single difference between `search` and `startsWith` is the `isEnd` check.** Both walk the same path; one demands a terminal marker and the other does not. Being able to state that cleanly is what the problem is testing.

Factoring the walk into a helper removes the duplication and is the version to write in an interview.

### Complexity

| Operation | Time | Space |
|---|---|---|
| `insert` | O(L) | O(L) new nodes worst case |
| `search` | O(L) | O(1) |
| `startsWith` | O(L) | O(1) |
| Total space | — | O(total characters × alphabet) |

Every operation is independent of the number of stored words.

### Must remember

1. Insert creates missing nodes; search does not.
2. `search` checks `isEnd`; `startsWith` does not.
3. `c - 'a'` assumes lowercase. Check the constraints.
4. Factor out the walk. Three methods, one loop.
5. All operations are O(L), never O(n).
6. Interview implementations rarely free memory; do not spend time on destructors unless asked.

---

## 15.4 Deletion

The one non-trivial operation, and the one most people get wrong.

### The difficulty

You cannot simply remove the path. Consider a trie holding `car` and `card`. Deleting `car` must **not** remove the `c-a-r` nodes, because `card` still needs them. Deleting `card` must remove only the `d` node.

**A node can be deleted only if it has no children and is not the end of another word.**

### The recursive version

```cpp
bool isLeaf(Node* n) {
    for (int i = 0; i < 26; i++) if (n->child[i]) return false;
    return true;
}

// Returns true if the CHILD node can be deleted by the caller.
bool remove(Node* cur, const string& w, int i) {
    if (i == (int)w.size()) {
        if (!cur->isEnd) return false;              // the word was never stored
        cur->isEnd = false;                          // unmark it
        return isLeaf(cur);                          // deletable only if childless
    }

    int c = w[i] - 'a';
    if (!cur->child[c]) return false;                // word not present

    if (remove(cur->child[c], w, i + 1)) {
        delete cur->child[c];
        cur->child[c] = nullptr;
        return !cur->isEnd && isLeaf(cur);           // can I be deleted too?
    }
    return false;
}
```

The return value carries "you may delete me" upward, and each level re-checks its own two conditions. The deletion unwinds as far up as it safely can and stops.

### The simpler alternative: reference counting

Store a `count` on each node recording how many words pass through it. Insert increments along the path, delete decrements, and a node with count 0 is removable.

```cpp
struct Node {
    Node* child[26] = {nullptr};
    int count = 0;      // words passing through
    bool isEnd = false;
};
```

**This is easier to get right and worth preferring** when the problem needs deletion at all. Many problems only need a soft delete — set `isEnd = false` and leave the nodes — which is a legitimate answer if you say so.

### Must remember

1. A node is deletable only if it is childless **and** not the end of another word.
2. The recursive form propagates "deletable" upward.
3. Reference counting is easier and less error-prone.
4. Soft deletion (`isEnd = false`) is often acceptable; state the trade-off.
5. Deletion is rarely asked. Know the rule; do not over-invest.

---

## 15.5 When a trie beats a hash map

**The judgement section, and the most valuable part of this module.**

### The comparison

| Operation | `unordered_set<string>` | Trie |
|---|---|---|
| Insert | O(L) hash + O(L) store | O(L) |
| Exact lookup | **O(L) hash, O(1) buckets** | O(L) |
| **Does any word start with `p`?** | **O(n·L)** scan everything | **O(L)** |
| **All words starting with `p`** | O(n·L) | O(L + output) |
| Lexicographic iteration | Requires a sort, O(n L log n) | **Free**: DFS in child order |
| Longest common prefix of all words | O(n·L) | **O(L)**: walk while one child |
| Wildcard / fuzzy matching | Not possible | Natural (Section 15.6) |
| Memory | Lower | **Much higher** |
| Implementation effort | Zero | ~20 lines |

### The rule

> **Use a trie only when prefixes matter. Otherwise use a hash map.**

For "is this word in the dictionary", a hash map wins on every axis: faster in practice, one line of code, and a fraction of the memory. Reaching for a trie there is over-engineering, and interviewers notice both directions of that mistake.

### The signals for a trie

| Signal | Example |
|---|---|
| "prefix" appears in the statement | "words with the given prefix" |
| Autocomplete, search suggestions | LC 1268 |
| Wildcard matching against a dictionary | LC 211 |
| Many words searched against one structure | Word Search II |
| Lexicographically ordered output required | Search suggestions |
| Longest common prefix across many strings | LC 14 |
| **Maximum XOR pair** | LC 421 — a binary trie |
| Dictionary with repeated prefix queries | Spell check, routing tables |

### The signals against

- Exact lookup only → hash map.
- Few words, short queries → hash map; the trie's constant factor loses.
- Memory constrained with a large alphabet → hash map, or a map-based trie.
- The strings are unrelated with no shared prefixes → the trie degenerates into a linked list per word and wastes memory.

### Must remember

1. Trie only when **prefixes** matter.
2. For exact lookup, a hash map is faster and simpler.
3. The trie's win is that prefix queries are O(L), not O(n·L).
4. Lexicographic order comes free from a DFS in child order.
5. Memory is the trie's weakness: 26 pointers per node.
6. Say the trade-off out loud. "A hash map handles exact lookup, but this needs prefix queries, so a trie is the right structure" is a complete justification.

---

## 15.6 Wildcard search

### Design Add and Search Words (LC 211)

*Support `addWord` and `search`, where `.` in a search matches any single character.*

```cpp
class WordDictionary {
    struct Node {
        Node* child[26] = {nullptr};
        bool isEnd = false;
    };
    Node* root;

    bool dfs(Node* cur, const string& w, int i) {
        if (!cur) return false;
        if (i == (int)w.size()) return cur->isEnd;

        if (w[i] != '.')
            return dfs(cur->child[w[i] - 'a'], w, i + 1);    // one path

        for (int c = 0; c < 26; c++)                         // try ALL children
            if (dfs(cur->child[c], w, i + 1)) return true;
        return false;
    }

public:
    WordDictionary() { root = new Node(); }

    void addWord(const string& w) { /* standard insert */ }

    bool search(const string& w) { return dfs(root, w, 0); }
};
```

**The wildcard turns a walk into a search.** A concrete character follows one child; a `.` branches into all 26 and succeeds if any branch does. The null check at the top means you never have to test children before recursing.

**Complexity:** O(L) when there are no dots, degrading to O(26^d · L) where `d` is the number of dots. With a leading dot this is effectively a full traversal — which is why the problem caps the number of dots.

**This is a trie problem that a hash map cannot solve at all.** Wildcards require walking the structure, and that is the cleanest possible demonstration of when a trie is genuinely necessary.

### Must remember

1. A concrete character follows one child; `.` branches into all of them.
2. Null-check at the top of the recursion, not before each call.
3. Complexity degrades to O(26^d) with `d` wildcards.
4. Hash maps cannot do this. It is the clearest "why a trie" example.

---

## 15.7 Word Search II

**The best trie problem in the set**, because the improvement over the naive approach is enormous and the reason is easy to state.

### The problem

*Given a grid of letters and a list of words, return every word that can be formed by a path of adjacent cells.*

### Why the naive approach fails

Running Module 8's Word Search once per word costs O(k · m · n · 4^L) for `k` words. With 3 × 10⁴ words that is hopeless.

**The fix: search the grid once, carrying a trie node alongside the position.** At each step, if no word in the dictionary has the current path as a prefix, the trie node is null and the entire branch dies immediately. One DFS prunes against all words simultaneously.

### The implementation

```cpp
struct Node {
    Node* child[26] = {nullptr};
    string word;                        // non-empty at terminal nodes
};

class Solution {
    void dfs(vector<vector<char>>& g, int r, int c, Node* node, vector<string>& res) {
        char ch = g[r][c];
        if (ch == '#') return;                          // already on the path
        Node* next = node->child[ch - 'a'];
        if (!next) return;                              // NO word has this prefix: prune

        if (!next->word.empty()) {
            res.push_back(next->word);
            next->word.clear();                         // dedupe: found once is enough
        }

        g[r][c] = '#';                                  // mark
        int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1};
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr < 0 || nr >= (int)g.size() || nc < 0 || nc >= (int)g[0].size()) continue;
            dfs(g, nr, nc, next, res);
        }
        g[r][c] = ch;                                   // UNMARK: backtracking
    }

public:
    vector<string> findWords(vector<vector<char>>& g, vector<string>& words) {
        Node* root = new Node();
        for (const string& w : words) {                 // build the trie
            Node* cur = root;
            for (char c : w) {
                if (!cur->child[c-'a']) cur->child[c-'a'] = new Node();
                cur = cur->child[c-'a'];
            }
            cur->word = w;
        }

        vector<string> res;
        for (int r = 0; r < (int)g.size(); r++)
            for (int c = 0; c < (int)g[0].size(); c++)
                dfs(g, r, c, root, res);
        return res;
    }
};
```

### The three details that make it work

**`if (!next) return;`** is the pruning, and it is the entire speedup. The moment the current path is not a prefix of any word, the branch stops.

**Storing the word at the terminal node** avoids rebuilding the string character by character during the DFS.

**`next->word.clear()` after finding it** prevents the same word being reported twice when it appears in multiple places. Using a `set` for the results also works and is slower.

**The mark/unmark is backtracking** (Module 8), not graph traversal — the cell must be reusable by a different path. This is the distinction flagged in Module 12.4, and this problem is exactly where it bites.

### Must remember

1. Build the trie from the words, then DFS the grid **once**.
2. A null child prunes the whole branch. That is the entire optimisation.
3. Store the word at the terminal node.
4. Clear the word after reporting it to avoid duplicates.
5. Mark and **unmark** the cell: this is backtracking, not graph traversal.
6. This is the clearest case where a trie changes the achievable complexity, not just the constant.

---

## 15.8 Autocomplete and prefix collection

The natural trie application, and the basis of several "design" questions.

### Collecting all words under a prefix

```cpp
void collect(Node* cur, string& path, vector<string>& out, int limit) {
    if ((int)out.size() >= limit) return;
    if (cur->isEnd) out.push_back(path);

    for (int c = 0; c < 26; c++) {                      // 0..25 = lexicographic order
        if (!cur->child[c]) continue;
        path.push_back('a' + c);
        collect(cur->child[c], path, out, limit);
        path.pop_back();                                 // backtracking again
    }
}

vector<string> autocomplete(Node* root, const string& prefix, int limit) {
    Node* cur = walk(prefix);
    if (!cur) return {};
    string path = prefix;
    vector<string> out;
    collect(cur, path, out, limit);
    return out;
}
```

**Iterating children `0..25` gives lexicographic order for free.** A hash map would need an explicit sort; the trie's child array is already in alphabetical order, so a DFS emits words sorted. That is a genuine structural advantage and worth mentioning.

The `limit` check prunes once enough suggestions are collected — real autocomplete returns the top few, not everything.

### Search Suggestions System (LC 1268)

Return the three lexicographically smallest matching words after each character typed. Two valid approaches:

- **Trie:** walk one character per keystroke and collect three words from that node.
- **Sort plus binary search:** sort the words once, then `lower_bound` the prefix and take the next three that still match.

The second is shorter and often faster in practice. **Mention both** — recognising that a trie is not always the best trie-shaped answer is the kind of judgement interviewers reward.

---

## 15.9 The XOR trie

**A genuinely different use of the structure**, and the place where Module 14 pays off.

### Maximum XOR of Two Numbers (LC 421)

*Given an array, find the maximum XOR of any pair.*

Brute force is O(n²). With n = 2 × 10⁵ that is 4 × 10¹⁰ — impossible.

### The idea

Store each number as a **binary trie**: 32 levels, two children per node, bits inserted from the most significant down.

To maximise `x ^ y`, walk the trie greedily from the top bit: **at each level, prefer the child holding the opposite bit.** A match at bit `b` contributes `2^b`, which is more than every lower bit combined, so taking it is always correct.

That "a higher bit outweighs all lower bits" argument is the greedy justification — an exchange argument (Module 11.2) in a different setting.

### The implementation

```cpp
struct BinNode {
    BinNode* child[2] = {nullptr, nullptr};
};

void insert(BinNode* root, int num) {
    BinNode* cur = root;
    for (int b = 31; b >= 0; b--) {                     // MOST significant first
        int bit = (num >> b) & 1;
        if (!cur->child[bit]) cur->child[bit] = new BinNode();
        cur = cur->child[bit];
    }
}

int maxXorWith(BinNode* root, int num) {
    BinNode* cur = root;
    int res = 0;
    for (int b = 31; b >= 0; b--) {
        int bit = (num >> b) & 1;
        int want = bit ^ 1;                              // the OPPOSITE bit
        if (cur->child[want]) {
            res |= (1 << b);                             // this bit contributes
            cur = cur->child[want];
        } else {
            cur = cur->child[bit];                       // forced to match
        }
    }
    return res;
}

int findMaximumXOR(const vector<int>& nums) {
    BinNode* root = new BinNode();
    for (int x : nums) insert(root, x);

    int best = 0;
    for (int x : nums) best = max(best, maxXorWith(root, x));
    return best;
}
```

O(32n) for both phases, so **O(n)** with a constant of 32. Space O(32n) nodes.

### Three details

**Insert from bit 31 down**, not up. The greedy depends on deciding high bits first.

**Only insert as many bits as the values need.** For values up to 10⁹, 30 bits suffice; using 32 is harmless but wasteful.

**`res |= (1 << b)`** records that this bit position contributes to the XOR. Use `1LL << b` if `b` can reach 31 in a signed context (Module 14.7).

### Variants

| Problem | Change |
|---|---|
| Maximum XOR (421) | The base case above |
| Maximum XOR With an Element From Array (1707) | Sort queries, insert incrementally |
| Count pairs with XOR in a range | Count nodes during the walk |
| Maximum XOR subarray | Insert prefix XORs instead of values |

That last one is worth noticing: **prefix XOR plus a binary trie** is the XOR analogue of prefix-sum-plus-hashmap from Module 3.5.

### Must remember

1. Binary trie: 32 levels, 2 children, most significant bit first.
2. Greedily prefer the opposite bit; a higher bit outweighs all lower ones.
3. Fall back to the same bit when the opposite child is missing.
4. O(32n) = O(n), versus O(n²) brute force.
5. Prefix XOR into the trie handles subarray XOR problems.
6. This is the only common trie problem that does not involve strings.

---

## 15.10 Consolidation

### Recognition guide

| The statement says | Technique |
|---|---|
| "words with a given prefix" | Trie |
| "autocomplete", "search suggestions" | Trie, or sort + binary search |
| "wildcard `.` matching a dictionary" | Trie with branching DFS |
| "find all words in a grid" (many words) | **Trie + backtracking** |
| "longest common prefix" | Trie, or vertical scan |
| "maximum XOR pair" | **Binary trie** |
| "maximum XOR subarray" | Prefix XOR + binary trie |
| "is this exact word present" | **Hash map**, not a trie |
| "group anagrams" | Hash map with a canonical key (Module 3.6) |
| "count distinct substrings" | Suffix structure — Tier 4 |

### Comparison tables

**Trie vs hash map**

| | Trie | Hash map |
|---|---|---|
| Exact lookup | O(L) | O(L) hash, faster constant |
| Prefix query | **O(L)** | O(n·L) |
| Sorted output | Free | Needs a sort |
| Wildcards | Supported | Impossible |
| Memory | High (26 ptr/node) | Low |
| Code | ~20 lines | 1 line |

**Array children vs map children**

| | `child[26]` | `unordered_map` |
|---|---|---|
| Step cost | O(1), no hashing | O(1) average, hashing |
| Memory per node | 26 pointers always | Only existing children |
| Alphabet | Small and known | Any |
| Use for | a–z problems | Unicode, sparse tries |

### Must remember (consolidated)

1. A trie is a tree with one child per alphabet symbol; paths spell prefixes.
2. `isEnd` distinguishes a word from a prefix. Never omit it.
3. All operations are O(L), independent of the number of words.
4. `search` checks `isEnd`; `startsWith` does not.
5. Use a trie **only when prefixes matter**. Otherwise use a hash map.
6. 26 pointers per node is roughly 208 bytes. Memory is the real constraint.
7. Deletion removes a node only if it is childless and not another word's end. Reference counting is simpler.
8. Wildcards branch into all 26 children; complexity degrades to O(26^d).
9. Word Search II: build the trie, DFS once, prune on a null child.
10. Mark and **unmark** grid cells — trie grid search is backtracking.
11. Store the word at the terminal node and clear it after reporting.
12. Iterating children `0..25` yields lexicographic order for free.
13. XOR trie: 32 levels, most significant bit first, greedily take the opposite bit.
14. Prefix XOR plus a binary trie solves subarray XOR problems.

### Common mistakes (consolidated)

**Wrong answer**
- Omitting `isEnd`, so `search("car")` returns true when only `card` was inserted.
- Using `startsWith` logic for `search`.
- Deleting nodes that other words still need.
- Not deduplicating results in Word Search II.
- Forgetting to unmark the grid cell, so paths cannot revisit.
- Inserting XOR trie bits from least significant to most.

**Time limit exceeded**
- Running Word Search once per word instead of using a trie.
- Scanning all stored words for a prefix query instead of using the trie.
- Brute-forcing maximum XOR pairs in O(n²).

**Memory limit exceeded**
- `child[26]` on a large alphabet or a very large word list.
- Building a trie when a hash map would have done.

**Runtime error**
- Missing `= {nullptr}` on the child array, leaving garbage pointers.
- Dereferencing a null child before checking.
- `1 << 31` in the XOR trie without `1LL`.

---

## 15.11 Problem set

Six core problems plus two optional. Small module, small set.

### Level 1 — Concept (2)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Implement Trie (LC 208) | Medium | Insert / search / startsWith | The structure, and the `isEnd` distinction |
| Longest Common Prefix (LC 14) | Easy | Prefix walk | Solvable without a trie; compare both |

### Level 2 — Pattern (2)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Design Add and Search Words (LC 211) | Medium | Wildcard DFS | The clearest "a hash map cannot do this" case |
| Replace Words (LC 648) | Medium | Shortest-prefix lookup | Stopping the walk at the first `isEnd` |

### Level 3 — Interview (2)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| **Word Search II (LC 212)** | Hard | Trie + backtracking | Pruning against all words at once |
| **Maximum XOR of Two Numbers (LC 421)** | Medium | Binary trie | The bit-greedy argument; Module 14 applied |

### Optional (2)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Search Suggestions System (LC 1268) | Medium | Autocomplete | Trie vs sort + binary search |
| Implement Magic Dictionary (LC 676) | Medium | One-character mismatch | Wildcard DFS with a budget |

**LC 212 and LC 421 are the two that matter.** They are the only problems where a trie changes the achievable complexity rather than merely offering a different structure, and both are memorable enough that solving them once tends to stick.

---

## Exit checklist

```
[ ] I can write a Trie node and the three core operations from memory
[ ] I know why isEnd is necessary
[ ] I know search checks isEnd and startsWith does not
[ ] I can state when a trie beats a hash map, and when it does not
[ ] I know the memory cost of child[26] and when to use a map instead
[ ] I know the deletion rule (childless AND not another word's end)
[ ] I can write the wildcard search with branching DFS
[ ] I can explain why Word Search II needs one DFS, not k
[ ] I remember to unmark grid cells (backtracking, not graph traversal)
[ ] I know iterating children 0..25 gives lexicographic order free
[ ] I can write the XOR trie insert and query
[ ] I can explain why the greedy opposite-bit choice is correct
[ ] I know prefix XOR + binary trie handles subarray XOR problems
[ ] Level 1-3 problems solved
```

---

## The teaching modules are done

That completes every module in the roadmap. Fifteen parts, from C++ fundamentals to tries.

Two things remain, and you can take them in either order or skip the first:

**Say "advanced topics"** for the Phase 15 survey from your original outline: segment trees, Fenwick trees, sparse tables, KMP, Z-algorithm, Rabin-Karp, rolling hash, network flow, computational geometry, heavy-light decomposition, and the advanced graph algorithms. Each classified as essential, high, medium, low, or competitive-programming-only, with an honest verdict on whether you need it for typical software placements. This is deliberately a survey, not a teaching module — roughly two hours to read.

**Say "cheat sheets"** for the ten final one-page references: the roadmap, complexity, STL, patterns, algorithms, C++ templates, interview mistakes, DP patterns, graph algorithms, and the final revision checklist. These are the documents you actually carry into the last week before placements.

If you would rather do something else with the remaining time — a revision plan calibrated to a specific deadline, a mock-interview format, or a deeper pass on any module — say that instead.
