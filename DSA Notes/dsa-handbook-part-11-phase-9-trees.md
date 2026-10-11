# DSA Placement Handbook (C++) — Part 11
# Phase 9: Trees and Binary Search Trees

**Module 9 · 18–22 hours · Tier 1 · Requires: Modules 0, 1, 4, 7**

---

## How to think about this module

Trees look like twenty different problems. They are mostly **one problem with twenty stories**, and the unifying idea comes from Module 4:

> Write down what the function promises to return for an arbitrary subtree, assume it works on the children, and combine.

Almost every tree solution is one sentence of contract plus three lines of code. If you are tracing recursion by hand on tree problems, you have not written the contract clearly enough.

There is exactly one pattern beyond that which you have to learn separately, and it is Section 9.9: **return one thing upward while tracking another globally.** Diameter, maximum path sum, and several others are impossible until you see it, and obvious afterwards.

### Budget for the 20 hours

| Part | Hours | Content |
|---|---|---|
| A — Fundamentals | 1 | Terminology, tree types |
| B — Traversals | 4 | Four traversals, recursive and iterative, Morris |
| C — Core DFS problems | 6 | Height, diameter, max path sum, LCA |
| D — Positional / BFS problems | 3 | Views, vertical order, zigzag, boundary |
| E — Construction | 2 | Build from traversals, serialize |
| F — BST | 4 | Search, insert, delete, validate, k-th, successor |

---

# PART A — Fundamentals

## 9.1 Terminology and tree types

### The node

```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};
```

### Vocabulary

| Term | Meaning |
|---|---|
| Root | The node with no parent |
| Leaf | A node with no children |
| Internal node | A node with at least one child |
| Depth of a node | Edges from the **root** to it (root has depth 0) |
| Height of a node | Edges on the longest path down to a **leaf** (leaf has height 0) |
| Height of the tree | Height of the root |
| Level | Depth + 1, in most textbook usage |
| Subtree | A node plus all its descendants |
| Ancestor / descendant | On the path up to the root / down from a node |

**Depth counts downward from the root; height counts upward from the leaves.** They are frequently confused, and interviewers occasionally ask. Note that LeetCode's "maximum depth" is defined in **nodes**, not edges, so an empty tree is 0 and a single node is 1. Different sources differ by one; when it matters, state your convention before coding.

### Tree types (the ones interviewers name)

| Type | Definition | Key property |
|---|---|---|
| **Full** (strict) | Every node has 0 or 2 children | No node has exactly one child |
| **Complete** | All levels filled except possibly the last, which fills left to right | Can be stored in an array: children of `i` are `2i+1`, `2i+2`. **This is what a heap is** (Module 10) |
| **Perfect** | All internal nodes have 2 children and all leaves are at the same level | Exactly `2^h − 1` nodes for height h |
| **Balanced** | Height of every node's two subtrees differs by at most 1 | Height is O(log n), which is what keeps operations fast |
| **Degenerate** (skewed) | Every node has one child | Height is n; behaves as a linked list |

Relationships: perfect ⟹ complete ⟹ (not necessarily full or balanced). Perfect ⟹ full. A complete tree is always balanced; the converse is false.

### Counting facts

| Fact | Value |
|---|---|
| Max nodes at level `d` (0-indexed) | 2^d |
| Max nodes in a tree of height `h` | 2^(h+1) − 1 |
| Min height for n nodes | ⌊log₂ n⌋ |
| Max height for n nodes | n − 1 (skewed) |
| In a full binary tree with `L` leaves | `L − 1` internal nodes |
| Nodes in a perfect tree of height h | 2^(h+1) − 1 |

### Why height matters

Every BST operation is O(height). Balanced means O(log n); skewed means O(n). This single fact is why `std::set` and `std::map` use red-black trees (self-balancing) rather than plain BSTs, and it is the standard answer to "what is the worst case of a BST?"

### Must remember

1. Depth counts from the root, height counts from the leaves.
2. LeetCode's "maximum depth" counts **nodes**, so a single node is 1. State your convention.
3. Complete tree ⟹ array-storable with `2i+1` / `2i+2`. That is exactly a heap.
4. Balanced ⟹ height O(log n) ⟹ operations O(log n).
5. A skewed BST degrades to a linked list: all operations O(n).
6. Perfect tree of height h has `2^(h+1) − 1` nodes.

---

## 9.2 The recursive contract on trees

This is the meta-skill for the whole module. From Module 4.3, applied here:

**Step 1.** Write one sentence: *"`f(node)` returns X for the subtree rooted at `node`."*
**Step 2.** Answer the empty tree (`node == nullptr`).
**Step 3.** Assume `f(node->left)` and `f(node->right)` are correct, and combine.

```cpp
ReturnType f(TreeNode* node) {
    if (!node) return /* the answer for an empty tree */;

    ReturnType L = f(node->left);
    ReturnType R = f(node->right);

    return /* combine L, R, and node->val */;
}
```

That skeleton solves height, node count, sum, minimum, maximum, balanced-check, same-tree, symmetric, invert, and a dozen others. **Never trace it.** If you find yourself following calls three levels deep, go back and sharpen the contract.

### Worked contracts

| Problem | Contract | Empty case | Combine |
|---|---|---|---|
| Height | "returns the height of this subtree" | 0 | `1 + max(L, R)` |
| Node count | "returns the number of nodes" | 0 | `1 + L + R` |
| Sum | "returns the sum of all values" | 0 | `node->val + L + R` |
| Invert | "returns the root of this subtree, inverted" | `nullptr` | swap children, return node |
| Max value | "returns the largest value" | `INT_MIN` | `max(node->val, L, R)` |

### Invert a binary tree (LC 226), as an illustration

```cpp
TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    TreeNode* l = invertTree(root->left);
    TreeNode* r = invertTree(root->right);
    root->left = r;
    root->right = l;
    return root;
}
```

Three lines, no tracing. The contract was *"returns this subtree with everything mirrored"*, and once you assume it holds for the children, swapping them is all that remains.

---

# PART B — Traversals

## 9.3 The three DFS traversals

### The definitions

The names describe **when the root is visited** relative to its subtrees.

```cpp
void preorder(TreeNode* r, vector<int>& out) {     // ROOT, left, right
    if (!r) return;
    out.push_back(r->val);
    preorder(r->left, out);
    preorder(r->right, out);
}

void inorder(TreeNode* r, vector<int>& out) {      // left, ROOT, right
    if (!r) return;
    inorder(r->left, out);
    out.push_back(r->val);
    inorder(r->right, out);
}

void postorder(TreeNode* r, vector<int>& out) {    // left, right, ROOT
    if (!r) return;
    postorder(r->left, out);
    postorder(r->right, out);
    out.push_back(r->val);
}
```

Three identical functions; only the position of one line changes.

```
        1
       / \
      2   3
     / \
    4   5

preorder:  1 2 4 5 3      (root first: copy/serialize a tree)
inorder:   4 2 5 1 3      (root middle: SORTED order in a BST)
postorder: 4 5 2 3 1      (root last: delete a tree, compute from children up)
```

### When to use which

| Traversal | Use it when |
|---|---|
| **Preorder** | You need to process a node **before** its children: copying, serialising, path-from-root problems |
| **Inorder** | The tree is a **BST** and you want sorted order. This is the defining BST property |
| **Postorder** | You need results **from the children** before deciding: height, diameter, deletion, most "compute upward" problems |
| **Level order** | Anything positional or level-based: views, zigzag, minimum depth, level sums |

**Postorder is the most common shape in interview problems**, even when nobody calls it that. Any solution of the form "recurse on both children, then combine" is postorder.

### Complexity

All four: O(n) time. Space is O(h) for the recursion stack, which is O(log n) balanced and **O(n) for a skewed tree**. Level order is O(w) where w is the maximum width, which can be n/2 at the last level, so also O(n).

### Must remember

1. The prefix names where the **root** is visited.
2. Inorder on a BST gives sorted order. That one fact solves validate-BST, k-th smallest, and several others.
3. Postorder is the natural shape for "compute from the children upward".
4. Recursive traversal is O(h) space, which is O(n) worst case. Do not claim O(1).
5. All four traversals visit every node exactly once: O(n).

---

## 9.4 Iterative traversals

Interviewers ask for these to check whether you understand the call stack, and because they come up when recursion depth is a risk.

### Iterative preorder (easiest)

```cpp
vector<int> preorderTraversal(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    stack<TreeNode*> st;
    st.push(root);

    while (!st.empty()) {
        TreeNode* n = st.top(); st.pop();
        res.push_back(n->val);
        if (n->right) st.push(n->right);     // RIGHT first
        if (n->left)  st.push(n->left);      // so LEFT pops first
    }
    return res;
}
```

Push right before left, because a stack reverses order.

### Iterative inorder (the one to memorise)

```cpp
vector<int> inorderTraversal(TreeNode* root) {
    vector<int> res;
    stack<TreeNode*> st;
    TreeNode* cur = root;

    while (cur || !st.empty()) {
        while (cur) {                        // go as far LEFT as possible
            st.push(cur);
            cur = cur->left;
        }
        cur = st.top(); st.pop();            // visit
        res.push_back(cur->val);
        cur = cur->right;                    // then go right
    }
    return res;
}
```

The loop condition is `cur || !st.empty()`: you are not finished while either there is a node to descend into or unvisited ancestors remain. This is the template to have memorised; it also underpins the iterative BST k-th smallest.

### Iterative postorder (via reversed preorder)

```cpp
vector<int> postorderTraversal(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    stack<TreeNode*> st;
    st.push(root);

    while (!st.empty()) {
        TreeNode* n = st.top(); st.pop();
        res.push_back(n->val);
        if (n->left)  st.push(n->left);      // LEFT first this time
        if (n->right) st.push(n->right);
    }
    reverse(res.begin(), res.end());         // root-right-left reversed = left-right-root
    return res;
}
```

Postorder is `left, right, root`. Its reverse is `root, right, left`, which is a preorder with the children swapped. So: do that, then reverse. Far easier than the genuine single-stack postorder, and a perfectly good interview answer as long as you explain the trick.

### Must remember

1. Preorder: push right then left.
2. Inorder: descend left pushing, pop and visit, then go right. Loop while `cur || !st.empty()`.
3. Postorder: modified preorder (left pushed first), then reverse the result.
4. All iterative versions are O(n) time and O(h) space, the same as recursive. The stack moves from the call stack to the heap, which has far more room.
5. The reason to know these: recursion depth limits, and interviewers asking directly.

---

## 9.5 Level order (BFS)

### The template

```cpp
vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;

    queue<TreeNode*> q;
    q.push(root);

    while (!q.empty()) {
        int sz = q.size();                   // SNAPSHOT the level size
        vector<int> level;

        for (int i = 0; i < sz; i++) {
            TreeNode* n = q.front(); q.pop();
            level.push_back(n->val);
            if (n->left)  q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(level);
    }
    return res;
}
```

**`int sz = q.size()` before the inner loop is the entire technique.** It captures how many nodes belong to the current level before you start adding the next level's nodes. Using `q.size()` directly in the loop condition reads a growing value and merges all levels into one.

This snapshot pattern reappears throughout Module 12 for BFS on graphs.

### What level order unlocks

| Problem | Change to the template |
|---|---|
| Right side view | Record the **last** node of each level |
| Left side view | Record the **first** node of each level |
| Zigzag traversal | Reverse alternate levels |
| Maximum width | Track index positions |
| Level averages/sums | Aggregate instead of collecting |
| Minimum depth | Return the first level containing a leaf |
| Top / bottom view | Add a horizontal-distance coordinate |

### Minimum depth, and why BFS wins

```cpp
int minDepth(TreeNode* root) {
    if (!root) return 0;
    queue<TreeNode*> q;
    q.push(root);
    int depth = 1;

    while (!q.empty()) {
        int sz = q.size();
        for (int i = 0; i < sz; i++) {
            TreeNode* n = q.front(); q.pop();
            if (!n->left && !n->right) return depth;   // first leaf found
            if (n->left)  q.push(n->left);
            if (n->right) q.push(n->right);
        }
        depth++;
    }
    return depth;
}
```

DFS would explore an entire deep subtree before finding a shallow leaf elsewhere. **BFS finds the shallowest leaf first and returns immediately.** This is the tree version of "BFS finds shortest paths", and it is the clearest case where the choice of traversal matters for efficiency rather than just style.

### Must remember

1. Snapshot `q.size()` before the level loop.
2. Only push non-null children, or add explicit null checks when popping.
3. BFS is the right tool for anything about levels, depth, or width.
4. Minimum depth: BFS returns early; DFS must explore everything.
5. Space is O(w), the maximum width, which is up to n/2.

---

## 9.6 Morris traversal

**Medium priority.** It is the O(1)-space inorder traversal, worth knowing as a "can you do better on space" answer.

### The idea

Recursive and stack-based inorder both need O(h) space to remember how to get back up. Morris traversal removes that by **temporarily rewiring the tree**: before descending left, it makes the rightmost node of the left subtree (the inorder predecessor) point back to the current node. After coming back through that thread, it removes it.

```cpp
vector<int> morrisInorder(TreeNode* root) {
    vector<int> res;
    TreeNode* cur = root;

    while (cur) {
        if (!cur->left) {
            res.push_back(cur->val);             // no left subtree: visit and go right
            cur = cur->right;
        } else {
            TreeNode* pred = cur->left;          // find the inorder predecessor
            while (pred->right && pred->right != cur) pred = pred->right;

            if (!pred->right) {
                pred->right = cur;               // CREATE the thread
                cur = cur->left;
            } else {
                pred->right = nullptr;           // REMOVE the thread (we've been here)
                res.push_back(cur->val);         // visit
                cur = cur->right;
            }
        }
    }
    return res;
}
```

### Complexity

O(n) time (each edge is traversed at most three times), **O(1) space**.

### Must remember

1. O(1) space, achieved by temporarily modifying the tree.
2. The thread must be removed, or you leave the tree corrupted with cycles.
3. `pred->right != cur` is the check that distinguishes "not threaded yet" from "already threaded".
4. It is still O(n) time despite the predecessor search, because each edge is visited a constant number of times.
5. **Answer this correctly when asked**: "inorder in O(1) space is Morris traversal, which threads the tree and unthreads it as it goes." Even if you would not write it by default, knowing it exists is the point.
6. Not thread-safe and destructive mid-traversal. If another thread reads the tree during the traversal it sees a corrupted structure.

---

# PART C — Core DFS problems

## 9.7 Height, depth, and balance

### Height

```cpp
int maxDepth(TreeNode* root) {
    if (!root) return 0;
    return 1 + max(maxDepth(root->left), maxDepth(root->right));
}
```

Contract: *"returns the depth in nodes of this subtree."* O(n) time, O(h) space.

### Balanced check, the naive way (O(n²))

```cpp
bool isBalanced(TreeNode* root) {                 // DON'T do this
    if (!root) return true;
    if (abs(maxDepth(root->left) - maxDepth(root->right)) > 1) return false;
    return isBalanced(root->left) && isBalanced(root->right);
}
```

`maxDepth` is O(n) and it is called at every node, giving O(n²). Correct, and the answer an interviewer will ask you to improve.

### Balanced check, the O(n) way

Return the height, but use a sentinel to signal failure:

```cpp
int check(TreeNode* r) {              // returns height, or -1 if unbalanced anywhere below
    if (!r) return 0;

    int lh = check(r->left);
    if (lh == -1) return -1;          // propagate failure immediately

    int rh = check(r->right);
    if (rh == -1) return -1;

    if (abs(lh - rh) > 1) return -1;
    return 1 + max(lh, rh);
}

bool isBalanced(TreeNode* root) { return check(root) != -1; }
```

One pass, O(n). The technique — **encode "failure" in the return value so you compute the answer and the check simultaneously** — is worth generalising. It appears again in validate-BST and in several "check a property" problems.

### Must remember

1. Height is `1 + max(left, right)`; the empty tree is 0.
2. The naive balance check is O(n²). Interviewers ask for the O(n) version.
3. The `-1` sentinel merges the height computation and the balance check into one pass.
4. Propagate the failure **immediately**, before recursing on the second child, to avoid wasted work.
5. O(h) space, which is O(n) for a skewed tree.

---

## 9.8 The "return one thing, track another" pattern

**The one genuinely new idea in this module.** Learn it here and three hard problems become routine.

### The problem it solves

Consider diameter: the longest path between any two nodes, which may or may not pass through the root.

The difficulty is that a node needs to report two different things:

- **Upward to its parent:** the longest downward path from here, because that is what the parent can extend.
- **Globally:** the longest path *through* this node, which uses both children and therefore cannot be extended upward at all.

A function returns one value. So: **return the extendable value, and record the non-extendable one in a variable outside the recursion.**

### Diameter (LC 543)

```cpp
class Solution {
    int best = 0;

    int depth(TreeNode* r) {                 // RETURNS height
        if (!r) return 0;
        int l = depth(r->left);
        int rt = depth(r->right);

        best = max(best, l + rt);            // TRACKS the path through this node

        return 1 + max(l, rt);               // returns only what the parent can use
    }
public:
    int diameterOfBinaryTree(TreeNode* root) {
        depth(root);
        return best;
    }
};
```

Two lines carry the whole idea: `best = max(best, l + rt)` records, and `return 1 + max(l, rt)` reports. The returned value uses **one** child (a path going up can only come from one side); the recorded value uses **both**.

Note `l + rt` counts **edges**. If the problem wants nodes, it is `l + rt + 1`. Read the statement.

### Maximum path sum (LC 124)

Same pattern, plus one twist: values can be negative, so a subtree that contributes a negative amount should be discarded entirely.

```cpp
class Solution {
    long long best = LLONG_MIN;

    int gain(TreeNode* r) {
        if (!r) return 0;

        int l  = max(0, gain(r->left));      // discard negative contributions
        int rt = max(0, gain(r->right));

        best = max(best, (long long)r->val + l + rt);   // path THROUGH this node

        return r->val + max(l, rt);          // path going UP: one side only
    }
public:
    int maxPathSum(TreeNode* root) {
        gain(root);
        return (int)best;
    }
};
```

Three things that go wrong here:

**`max(0, ...)`** is how you say "if this subtree hurts, do not include it". Without it, a negative subtree drags down every answer.

**`best` initialised to a true minimum**, not 0. An all-negative tree has a negative answer, and initialising to 0 returns 0.

**The returned value adds only one child.** A path that continues to the parent enters this node once and leaves once; it cannot use both children.

### The pattern, stated generally

| | Returned upward | Tracked globally |
|---|---|---|
| Diameter | Height (one side) | `l + r` through this node |
| Max path sum | `val + max(l, r)` | `val + l + r` |
| Longest ZigZag | Length in one direction | Best over all nodes |
| Largest BST subtree | Validity info + range | Largest size seen |

**Recognition signal:** the answer can be "centred" anywhere in the tree, not just at the root, and the thing a parent needs is different from the thing being measured.

### Must remember

1. Return what the parent can extend; track what the parent cannot use.
2. The returned value uses **one** child; the recorded value uses **both**.
3. For sums, `max(0, child)` discards harmful subtrees.
4. Initialise the global tracker to a real minimum (`INT_MIN` / `LLONG_MIN`), not 0, when values can be negative.
5. Check whether the problem counts edges or nodes. It changes the formula by 1.
6. A member variable, a reference parameter, or a lambda capture all work for the tracker. Avoid true globals in interview code.

### Common mistakes

- Returning `l + r` instead of `max(l, r)`, producing paths that pass through a node twice.
- Initialising the tracker to 0 on a tree with negative values.
- Forgetting `max(0, ...)` in the sum version.
- Off by one between edges and nodes.

### Practice

- Diameter of Binary Tree (LC 543, Easy)
- Binary Tree Maximum Path Sum (LC 124, Hard)
- Longest ZigZag Path (LC 1372, Medium) — optional, same pattern with direction state

---

## 9.9 Lowest Common Ancestor

### General binary tree (LC 236)

```cpp
TreeNode* lca(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (!root || root == p || root == q) return root;

    TreeNode* l = lca(root->left,  p, q);
    TreeNode* r = lca(root->right, p, q);

    if (l && r) return root;          // p and q are on opposite sides: THIS is the LCA
    return l ? l : r;                 // otherwise pass up whichever was found
}
```

Five lines. The reason it works is entirely in the contract, which is subtle enough to state carefully:

> *"`lca(root, p, q)` returns: the LCA if both `p` and `q` are in this subtree; otherwise whichever of `p` or `q` is present; otherwise `nullptr`."*

That three-way contract is what makes the combine step trivial:

- If both child calls returned non-null, then `p` and `q` were found in different subtrees, so this node is the split point and therefore the LCA.
- If only one returned non-null, pass it up. It is either one of the targets or an already-found LCA; in both cases the parent handles it correctly.
- If neither, return null.

**The assumption:** both `p` and `q` exist in the tree. If that is not guaranteed, the function returns a node even when only one is present, and you need a second pass to verify. Ask about this in an interview; it is the follow-up question.

O(n) time, O(h) space.

### BST version (LC 235)

A BST gives you far more, so the solution is simpler and iterative:

```cpp
TreeNode* lcaBST(TreeNode* root, TreeNode* p, TreeNode* q) {
    while (root) {
        if (p->val < root->val && q->val < root->val)      root = root->left;
        else if (p->val > root->val && q->val > root->val) root = root->right;
        else return root;              // the split point
    }
    return nullptr;
}
```

The LCA is the first node where `p` and `q` fall on opposite sides (or one of them **is** the node). O(h) time, **O(1) space**.

### Must remember

1. The general LCA works because of a three-way contract. Be able to state it.
2. `if (l && r) return root` is the split-point check.
3. `root == p || root == q` returns early, which correctly handles the case where one target is an ancestor of the other.
4. BST LCA is iterative, O(h) time, O(1) space. Do not use the general algorithm on a BST.
5. Both algorithms assume the targets exist. Say so.
6. The parent-pointer variant (if nodes have `parent`) reduces to finding the intersection of two linked lists, which is Module 6.7.

---

## 9.10 Structural comparisons

### Same tree (LC 100)

```cpp
bool isSameTree(TreeNode* a, TreeNode* b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return a->val == b->val && isSameTree(a->left, b->left)
                            && isSameTree(a->right, b->right);
}
```

The two-line null handling is the template: **both null is success, exactly one null is failure.** Reversing the order or merging them into one check is a common bug.

### Symmetric tree (LC 101)

Symmetry is "the tree is a mirror of itself", so compare left against right **crosswise**:

```cpp
bool mirror(TreeNode* a, TreeNode* b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return a->val == b->val && mirror(a->left,  b->right)     // CROSSED
                            && mirror(a->right, b->left);
}

bool isSymmetric(TreeNode* root) {
    return !root || mirror(root->left, root->right);
}
```

The only difference from `isSameTree` is the crossing. Writing `mirror(a->left, b->left)` gives you `isSameTree` and quietly wrong answers.

### Subtree of another tree (LC 572)

```cpp
bool isSubtree(TreeNode* root, TreeNode* sub) {
    if (!root) return false;
    if (isSameTree(root, sub)) return true;
    return isSubtree(root->left, sub) || isSubtree(root->right, sub);
}
```

O(n·m) in the worst case. The O(n+m) solution serialises both trees and does string matching, which is Tier 3 and worth mentioning rather than writing.

### Must remember

1. Both-null is success, one-null is failure. Two separate checks, in that order.
2. Symmetric crosses the children; same-tree does not.
3. Subtree matching is O(n·m) naively. Mention the serialisation approach as the improvement.
4. Compare node **pointers** for identity, node **values** for equality. They are different questions.

---

# PART D — Positional problems

## 9.11 Views

### Right side view (LC 199)

**BFS version:** take the last node of each level.

```cpp
vector<int> rightSideView(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    queue<TreeNode*> q;
    q.push(root);

    while (!q.empty()) {
        int sz = q.size();
        for (int i = 0; i < sz; i++) {
            TreeNode* n = q.front(); q.pop();
            if (i == sz - 1) res.push_back(n->val);       // last of this level
            if (n->left)  q.push(n->left);
            if (n->right) q.push(n->right);
        }
    }
    return res;
}
```

**DFS version**, shorter and worth knowing: visit **right first**, and record the first node seen at each depth.

```cpp
void dfs(TreeNode* r, int depth, vector<int>& res) {
    if (!r) return;
    if (depth == (int)res.size()) res.push_back(r->val);   // first at this depth
    dfs(r->right, depth + 1, res);                          // RIGHT first
    dfs(r->left,  depth + 1, res);
}
```

`depth == res.size()` is a neat trick: the result vector's length is exactly the number of depths recorded so far, so this condition is true precisely the first time a depth is reached.

Left side view: swap `right` and `left` in the DFS, or take `i == 0` in the BFS.

### Top and bottom view

These need a **horizontal distance** coordinate: root is 0, left child is `hd − 1`, right child is `hd + 1`.

```cpp
vector<int> topView(TreeNode* root) {
    map<int,int> m;                                  // hd -> value, sorted by hd
    queue<pair<TreeNode*,int>> q;
    if (root) q.push({root, 0});

    while (!q.empty()) {
        auto [n, hd] = q.front(); q.pop();
        if (!m.count(hd)) m[hd] = n->val;            // TOP view: keep the FIRST
        if (n->left)  q.push({n->left,  hd - 1});
        if (n->right) q.push({n->right, hd + 1});
    }

    vector<int> res;
    for (auto& [k, v] : m) res.push_back(v);         // map iterates hd ascending
    return res;
}
```

For **bottom view**, change one line: always overwrite with `m[hd] = n->val`, so the last node at each horizontal distance wins.

**Use BFS, not DFS.** With DFS you might reach a deep node at some horizontal distance before a shallower node at the same distance, and the top view would be wrong. BFS guarantees shallower nodes are processed first. This is the detail that gets tested.

**Use `map`, not `unordered_map`.** You need the horizontal distances in sorted order for the output, and `map` gives that for free.

### Vertical order traversal (LC 987)

The strict version: sort by column, then by row, then by value for ties.

```cpp
vector<vector<int>> verticalTraversal(TreeNode* root) {
    map<int, map<int, multiset<int>>> nodes;         // col -> row -> values

    function<void(TreeNode*, int, int)> dfs = [&](TreeNode* n, int row, int col) {
        if (!n) return;
        nodes[col][row].insert(n->val);
        dfs(n->left,  row + 1, col - 1);
        dfs(n->right, row + 1, col + 1);
    };
    dfs(root, 0, 0);

    vector<vector<int>> res;
    for (auto& [col, rows] : nodes) {
        vector<int> column;
        for (auto& [row, vals] : rows)
            column.insert(column.end(), vals.begin(), vals.end());
        res.push_back(column);
    }
    return res;
}
```

The triple-nested container looks heavy but each layer earns its place: `map` on column for sorted output, `map` on row for top-to-bottom, `multiset` for the value tiebreak with duplicates allowed. **Read the tiebreak rule in the statement carefully** — different versions of this problem break ties differently, and it is the whole difficulty.

### Zigzag level order (LC 103)

```cpp
vector<vector<int>> zigzagLevelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q;
    q.push(root);
    bool leftToRight = true;

    while (!q.empty()) {
        int sz = q.size();
        vector<int> level(sz);
        for (int i = 0; i < sz; i++) {
            TreeNode* n = q.front(); q.pop();
            int pos = leftToRight ? i : sz - 1 - i;     // write into the right slot
            level[pos] = n->val;
            if (n->left)  q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(level);
        leftToRight = !leftToRight;
    }
    return res;
}
```

Writing directly into the correct index avoids a `reverse` call. Reversing also works and is fine.

**Do not try to alternate the push order into the queue.** That changes which nodes are adjacent at the next level and breaks the traversal. Only the output order flips.

### Boundary traversal

Anti-clockwise: left boundary (excluding leaves), then all leaves left to right, then right boundary reversed (excluding leaves).

The three parts are collected separately. The details that cause bugs:

- A leaf must appear **exactly once**, so the boundary walks exclude leaves.
- The right boundary is collected top-down and then reversed, or collected bottom-up.
- The root is included once, at the start.
- Single-node trees and trees with only one side need explicit handling.

This is a GeeksforGeeks staple more than a LeetCode one. **Medium priority**: know the decomposition into three parts; the implementation is fiddly rather than deep.

### Must remember

1. Right view via DFS: go right first, record when `depth == res.size()`.
2. Top and bottom view need horizontal distance and **must use BFS**.
3. Top view keeps the first node per horizontal distance; bottom view keeps the last.
4. Use `map` (not `unordered_map`) so horizontal distances come out sorted.
5. Zigzag flips the **output order**, never the queue push order.
6. Vertical traversal tiebreak rules differ between problem versions. Read carefully.
7. Boundary traversal is left boundary + leaves + reversed right boundary, with leaves excluded from the two boundary walks.

---

# PART E — Construction and serialization

## 9.12 Building a tree from traversals

### Preorder + Inorder (LC 105)

**The idea.** Preorder gives you the root first. Finding that root in the inorder array splits it into the left subtree's elements and the right subtree's elements. Recurse.

```cpp
class Solution {
    unordered_map<int,int> idx;      // value -> index in inorder
    int pi = 0;

    TreeNode* build(const vector<int>& pre, int l, int r) {
        if (l > r) return nullptr;

        int val = pre[pi++];                       // next preorder element is this root
        TreeNode* node = new TreeNode(val);
        int m = idx[val];                          // its position in inorder

        node->left  = build(pre, l, m - 1);        // LEFT first: preorder demands it
        node->right = build(pre, m + 1, r);
        return node;
    }
public:
    TreeNode* buildTree(vector<int>& preorder, vector<int>& inorder) {
        for (int i = 0; i < (int)inorder.size(); i++) idx[inorder[i]] = i;
        return build(preorder, 0, inorder.size() - 1);
    }
};
```

**The hash map is what makes this O(n).** Searching the inorder array linearly at each node gives O(n²). Interviewers ask for this improvement.

**`pi` must be shared across calls** (member variable or reference), and the left subtree must be built **before** the right, because preorder consumes elements in exactly that order.

### Inorder + Postorder (LC 106)

Same idea mirrored: postorder gives the root **last**, so consume from the back and build the **right** subtree first.

### Which pairs work

| Pair | Uniquely determines the tree? |
|---|---|
| Preorder + Inorder | **Yes** |
| Postorder + Inorder | **Yes** |
| Preorder + Postorder | **No**, ambiguous for nodes with one child |
| Level order + Inorder | Yes |

**Preorder + Postorder is the classic viva question.** For a root with a single child, those two traversals cannot tell you whether the child is on the left or the right. (It *is* unique for full binary trees, where every node has 0 or 2 children.) Being able to say that precisely is a good answer.

### Must remember

1. Inorder is required to split left from right. Without it, you cannot locate the boundary.
2. Preorder + Postorder is ambiguous in general; unique only for full binary trees.
3. Build a hash map from value to inorder index for O(n). Linear search gives O(n²).
4. The preorder index must be shared state; build left before right (and the reverse for postorder).
5. This assumes **distinct values**. With duplicates the reconstruction is ambiguous.

---

## 9.13 Serialize and deserialize (LC 297)

```cpp
class Codec {
public:
    string serialize(TreeNode* root) {
        string s;
        function<void(TreeNode*)> dfs = [&](TreeNode* n) {
            if (!n) { s += "#,"; return; }              // null marker
            s += to_string(n->val) + ",";
            dfs(n->left);
            dfs(n->right);
        };
        dfs(root);
        return s;
    }

    TreeNode* deserialize(string data) {
        int i = 0;
        function<TreeNode*()> build = [&]() -> TreeNode* {
            string tok;
            while (data[i] != ',') tok += data[i++];
            i++;                                        // skip the comma
            if (tok == "#") return nullptr;
            TreeNode* n = new TreeNode(stoi(tok));
            n->left  = build();
            n->right = build();
            return n;
        };
        return build();
    }
};
```

**Why preorder with null markers is the right choice.** Preorder alone is ambiguous (Section 9.12), but recording nulls explicitly removes the ambiguity: the structure is fully encoded because every missing child is written down. The deserializer consumes tokens in exactly the order the serializer produced them, so no index arithmetic is needed.

Level order with null markers works equally well and is what LeetCode's own display format uses.

### Must remember

1. Null markers are what make preorder sufficient. Without them, the structure is lost.
2. Serialize and deserialize must use the **same** traversal order.
3. Use a delimiter and handle multi-digit and negative values. `to_string(-12)` is three characters, not one.
4. `function<TreeNode*()>` is needed for a recursive lambda (Module 0, Section C3).
5. Level order with nulls is an equally valid answer; say which you chose and why.

---

# PART F — Binary Search Trees

## 9.14 BST properties, search, insert, delete

### The invariant

For every node: **all values in the left subtree are smaller, all values in the right subtree are larger.**

The invariant is about entire **subtrees**, not just immediate children. That distinction is the whole content of Section 9.15.

**The consequence that matters:** inorder traversal of a BST produces sorted output. Most BST problems are that fact in disguise.

### Search

```cpp
TreeNode* searchBST(TreeNode* root, int val) {
    while (root && root->val != val)
        root = (val < root->val) ? root->left : root->right;
    return root;
}
```

O(h). Iterative, O(1) space. Note it is binary search on a tree.

### Insert

```cpp
TreeNode* insertIntoBST(TreeNode* root, int val) {
    if (!root) return new TreeNode(val);
    if (val < root->val)      root->left  = insertIntoBST(root->left,  val);
    else if (val > root->val) root->right = insertIntoBST(root->right, val);
    return root;                                  // duplicates ignored
}
```

The `root->left = insert(...)` idiom is the standard way to modify a tree recursively: the child reassigns itself, and unchanged subtrees are simply reassigned to themselves. It looks wasteful and is not.

New nodes always become **leaves**. Insertion never restructures the tree, which is why an unbalanced BST stays unbalanced.

### Delete (LC 450)

The one with real case analysis.

```cpp
TreeNode* deleteNode(TreeNode* root, int key) {
    if (!root) return nullptr;

    if (key < root->val)      root->left  = deleteNode(root->left,  key);
    else if (key > root->val) root->right = deleteNode(root->right, key);
    else {
        if (!root->left)  return root->right;     // 0 or 1 child: splice
        if (!root->right) return root->left;

        TreeNode* succ = root->right;             // 2 children: inorder successor
        while (succ->left) succ = succ->left;     // leftmost of the right subtree

        root->val = succ->val;                    // copy the value up
        root->right = deleteNode(root->right, succ->val);   // delete the successor
    }
    return root;
}
```

**The three cases:**

| Children | Action |
|---|---|
| 0 | Return `nullptr` (covered by the 1-child case) |
| 1 | Return the single child; the parent splices it in |
| 2 | Replace the value with the inorder successor, then delete the successor |

**Why the inorder successor works.** It is the smallest value in the right subtree, so it is larger than everything on the left and smaller than everything else on the right. Substituting it preserves the BST invariant. The inorder **predecessor** (largest in the left subtree) works equally well; pick one and be consistent.

The successor has at most one child (it has no left child by construction), so deleting it recursively hits one of the easy cases.

### Must remember

1. The BST invariant applies to whole subtrees, not just immediate children.
2. Inorder on a BST is sorted. This is the key to most BST problems.
3. All operations are O(h): O(log n) balanced, **O(n) skewed**.
4. Insertion always creates a leaf and never rebalances.
5. Deletion with two children: replace with the inorder successor (leftmost of the right subtree), then delete that successor.
6. The `root->left = recurse(...)` reassignment idiom is how you modify trees recursively.
7. `std::set` and `std::map` are red-black trees, which self-balance and guarantee O(log n).

---

## 9.15 Validate BST

### The wrong solution

```cpp
bool isValidBST(TreeNode* root) {                  // WRONG
    if (!root) return true;
    if (root->left  && root->left->val  >= root->val) return false;
    if (root->right && root->right->val <= root->val) return false;
    return isValidBST(root->left) && isValidBST(root->right);
}
```

This checks only immediate children, and it accepts trees like:

```
      5
     / \
    1   7
       / \
      3   8       <- 3 < 5 but sits in the RIGHT subtree of 5. Invalid.
```

Every parent-child pair is locally correct, so the check passes. The tree is not a BST.

**This is the single most common wrong answer in tree interviews**, and it is why the problem is asked.

### The range solution

Every node must lie within a range inherited from its ancestors:

```cpp
bool valid(TreeNode* r, long long lo, long long hi) {
    if (!r) return true;
    if (r->val <= lo || r->val >= hi) return false;
    return valid(r->left,  lo, r->val)        // left: upper bound becomes this value
        && valid(r->right, r->val, hi);       // right: lower bound becomes this value
}

bool isValidBST(TreeNode* root) {
    return valid(root, LLONG_MIN, LLONG_MAX);
}
```

Going left tightens the upper bound; going right tightens the lower bound. In the counter-example above, node 3 would be called with `lo = 5`, and `3 <= 5` fails immediately.

**Use `long long` for the bounds.** A node with value `INT_MIN` or `INT_MAX` breaks the comparison if the sentinels are `INT_MIN` / `INT_MAX`. This is a real test case on LeetCode and a deliberate trap.

### The inorder solution

Since inorder on a BST is sorted, check that it is strictly increasing:

```cpp
class Solution {
    TreeNode* prev = nullptr;
public:
    bool isValidBST(TreeNode* root) {
        if (!root) return true;
        if (!isValidBST(root->left)) return false;
        if (prev && prev->val >= root->val) return false;   // not strictly increasing
        prev = root;
        return isValidBST(root->right);
    }
};
```

No sentinel values needed, so the `INT_MIN` problem disappears. Both solutions are O(n) time, O(h) space. **Know both**; the inorder one is often the cleaner answer and it generalises to "recover a BST with two swapped nodes" (LC 99).

### Must remember

1. Checking only immediate children is **wrong**. Be ready to give the counter-example.
2. The range propagates: left tightens `hi`, right tightens `lo`.
3. Use `long long` bounds, or use the inorder approach to avoid sentinels entirely.
4. Inorder must be **strictly** increasing; equal values make it invalid under the usual definition.
5. Both approaches are O(n) time, O(h) space.

---

## 9.16 K-th smallest, predecessor, successor

### K-th smallest (LC 230)

Inorder gives sorted order, so stop at the k-th element.

```cpp
class Solution {
    int k, ans = -1;
    void inorder(TreeNode* r) {
        if (!r || k < 0) return;
        inorder(r->left);
        if (--k == 0) { ans = r->val; return; }
        inorder(r->right);
    }
public:
    int kthSmallest(TreeNode* root, int kk) { k = kk; inorder(root); return ans; }
};
```

O(h + k), not O(n), because you stop early.

**Iterative version**, which stops cleanly and is the better answer:

```cpp
int kthSmallest(TreeNode* root, int k) {
    stack<TreeNode*> st;
    TreeNode* cur = root;
    while (cur || !st.empty()) {
        while (cur) { st.push(cur); cur = cur->left; }
        cur = st.top(); st.pop();
        if (--k == 0) return cur->val;
        cur = cur->right;
    }
    return -1;
}
```

This is the iterative inorder template from 9.4 with a counter.

**K-th largest** is the same with a reverse inorder (right, root, left).

**The follow-up:** *"what if the tree is modified frequently and k-th smallest is queried often?"* The answer is to store a subtree-size count in each node, which makes each query O(h). Knowing that answer matters more than writing it.

### Inorder successor (LC 285)

The smallest value greater than a target.

```cpp
TreeNode* inorderSuccessor(TreeNode* root, TreeNode* p) {
    TreeNode* succ = nullptr;
    while (root) {
        if (p->val < root->val) {
            succ = root;              // candidate: remember it, look for something smaller
            root = root->left;
        } else {
            root = root->right;       // too small: must go right
        }
    }
    return succ;
}
```

O(h) time, O(1) space. Predecessor is the mirror image: when `p->val > root->val`, record and go right.

This is structurally identical to `lower_bound` (Module 5.9): walk down, record candidates, narrow. The same "remember the best candidate seen" idea as the stored-answer binary search template.

### Must remember

1. K-th smallest is inorder with a counter; stop early for O(h + k).
2. K-th largest is reverse inorder (right, root, left).
3. The iterative inorder template is the cleanest way to stop early.
4. Successor: go left recording candidates, go right without recording.
5. The frequent-modification follow-up is answered by storing subtree sizes in the nodes.
6. `set` and `map` give you `lower_bound` directly; this is the same algorithm the library runs.

---

# PART G — Consolidation

## 9.17 DFS or BFS? Recursion or iteration?

You asked for this explicitly.

### DFS vs BFS

| Use DFS when | Use BFS when |
|---|---|
| The answer combines results from subtrees | The answer is about **levels** |
| Height, diameter, sum, path sums | Level order, zigzag, level sums |
| Path-from-root problems | Views (right, left, top, bottom) |
| Structural checks (same, symmetric, valid BST) | **Minimum** depth (early exit) |
| Serialization, construction | Maximum width |
| LCA | Anything needing a horizontal-distance coordinate |

**The tell:** if the word "level", "depth", "view", or "width" appears in the problem, reach for BFS. If the answer is computed from children upward, reach for DFS.

**One case where it genuinely matters for efficiency:** minimum depth. BFS returns at the first leaf; DFS must explore everything. Maximum depth is the opposite — DFS is natural and BFS gains nothing.

### Recursion vs iteration

| Prefer recursion | Prefer iteration |
|---|---|
| Almost always for trees | When asked for it explicitly |
| Contract-based solutions | When depth could overflow the stack (very deep skewed trees) |
| Height, LCA, diameter, validate | Inorder for k-th smallest with early exit |
| Anything with a clean combine step | BST search, insert, LCA (O(1) space) |
| Construction, serialization | Morris traversal (O(1) space) |

**Default to recursion for trees.** The iterative versions exist for specific reasons: O(1) space on BSTs, stack-depth safety, and interviewer requests. Depth is O(h), which for a skewed tree of 10⁵ nodes is a real risk (Module 4.2).

### Space complexity, restated

| Approach | Space |
|---|---|
| Recursive DFS | O(h): O(log n) balanced, **O(n) skewed** |
| Iterative DFS with a stack | O(h), on the heap |
| BFS | O(w), maximum width, up to n/2 |
| Morris traversal | **O(1)** |
| BST iterative search/insert/LCA | O(1) |

---

## 9.18 Comparison tables

### The four traversals

| Traversal | Order | Iterative difficulty | Use for |
|---|---|---|---|
| Preorder | Root, L, R | Easy (push R then L) | Copy, serialize, root-down |
| Inorder | L, Root, R | Medium (the template) | **Sorted order in a BST** |
| Postorder | L, R, Root | Medium (reversed preorder) | Compute from children up |
| Level order | By level | Easy (queue + size snapshot) | Levels, views, width |

### Binary tree vs BST

| | Binary tree | BST |
|---|---|---|
| Ordering | None | Left < root < right, subtree-wide |
| Search | O(n) | O(h) |
| Inorder gives | Arbitrary order | **Sorted** |
| LCA | O(n) recursive, three-way contract | O(h) iterative, split point |
| K-th smallest | Sort everything, O(n log n) | Inorder with a counter, O(h + k) |
| Worst-case height | n − 1 | n − 1 (skewed) |

### Tree types

| Type | Every node has | Leaves | Nodes |
|---|---|---|---|
| Full | 0 or 2 children | anywhere | any |
| Complete | filled left to right | last two levels | any |
| Perfect | 2 children (internal) | all at one level | 2^(h+1) − 1 |
| Balanced | subtree heights differ ≤ 1 | anywhere | height O(log n) |

---

## 9.19 Must remember (consolidated)

1. Write the contract in one sentence. Never trace a tree recursion.
2. Depth counts from the root; height counts from the leaves. LeetCode's "depth" counts nodes.
3. Inorder on a BST gives sorted order. Most BST problems are this fact in disguise.
4. Level order: snapshot `q.size()` before the level loop.
5. Iterative inorder: descend left pushing, pop and visit, go right. Loop while `cur || !st.empty()`.
6. Iterative postorder: modified preorder, then reverse.
7. Balanced check uses the `-1` sentinel for O(n); the naive version is O(n²).
8. **Return one thing upward, track another globally.** Returned value uses one child; tracked value uses both.
9. Max path sum needs `max(0, child)` and a tracker initialised to a true minimum.
10. General LCA: `if (l && r) return root`, otherwise pass up whichever is non-null.
11. BST LCA is iterative and O(1) space. Do not use the general version on a BST.
12. Symmetric crosses the children; same-tree does not.
13. Top and bottom view need BFS plus a horizontal distance, and `map` for sorted output.
14. Zigzag flips the output order, never the queue push order.
15. Validate BST needs a **propagating range**, not a parent-child check. Use `long long` bounds or the inorder method.
16. BST delete with two children: copy the inorder successor's value, then delete the successor.
17. Preorder + Inorder determines a tree; Preorder + Postorder does not (except for full trees).
18. Serialization needs null markers, and the same order on both sides.
19. Build-from-traversals needs a hash map for O(n).
20. Recursive tree solutions are O(h) space, which is O(n) for a skewed tree. Never claim O(1).

---

## 9.20 Common mistakes (consolidated)

**Wrong answer**
- Validating a BST by checking only immediate children.
- `INT_MIN` / `INT_MAX` sentinels in validate-BST failing on extreme node values.
- Returning `l + r` instead of `max(l, r)` in the diameter or path-sum pattern.
- Initialising the global tracker to 0 when values can be negative.
- Forgetting `max(0, child)` in maximum path sum.
- Using `q.size()` directly in the level loop, merging all levels.
- Not crossing the children in the symmetric check.
- Using DFS for top or bottom view.
- Alternating the queue push order for zigzag.
- Building the right subtree before the left in preorder reconstruction.
- Off by one between edges and nodes in diameter.

**Time limit exceeded**
- Naive O(n²) balance check.
- Linear search in the inorder array during tree construction.
- Traversing the whole tree for k-th smallest instead of stopping early.

**Runtime error**
- Dereferencing a null child without checking.
- Stack overflow on a deep skewed tree.
- Accessing `q.front()` on an empty queue.

**Analysis errors**
- Claiming O(1) space for a recursive traversal.
- Claiming O(log n) space without saying "if balanced".
- Reporting O(n) for k-th smallest when the early exit makes it O(h + k).

---

## 9.21 Problem set

Twenty-four problems. Do the levels in order; several Level 3 problems assume patterns established in Level 2.

### Level 1 — Concept (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Maximum Depth of Binary Tree (LC 104) | Easy | Contract recursion | The three-line skeleton |
| Invert Binary Tree (LC 226) | Easy | Contract recursion | Trusting the recursive call |
| Same Tree (LC 100) | Easy | Dual recursion | Both-null / one-null handling |
| Binary Tree Inorder Traversal (LC 94) | Easy | Iterative DFS | The stack template to memorise |
| Binary Tree Level Order Traversal (LC 102) | Medium | BFS | The `q.size()` snapshot |

### Level 2 — Pattern (7)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Symmetric Tree (LC 101) | Easy | Mirror recursion | The crossing |
| Balanced Binary Tree (LC 110) | Easy | Sentinel return | O(n²) → O(n) with `-1` |
| Diameter of Binary Tree (LC 543) | Easy | **Return one, track another** | The module's key pattern |
| Binary Tree Right Side View (LC 199) | Medium | BFS last / DFS right-first | Two valid approaches |
| Path Sum II (LC 113) | Medium | Root-to-leaf backtracking | Trees meet Module 8 |
| Binary Tree Zigzag Level Order (LC 103) | Medium | BFS + output flip | Why you don't flip the queue |
| Search + Insert into a BST (LC 700, 701) | Easy | BST descent | The reassignment idiom |

### Level 3 — Interview (8)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Lowest Common Ancestor (LC 236) | Medium | Three-way contract | Five lines that look like magic until you state the contract |
| Validate Binary Search Tree (LC 98) | Medium | Propagating range | The most common wrong answer in tree interviews |
| Kth Smallest in a BST (LC 230) | Medium | Inorder + counter | Early exit, O(h + k) |
| LCA of a BST (LC 235) | Medium | Split point | Why BSTs make this O(1) space |
| Construct Tree from Preorder + Inorder (LC 105) | Medium | Divide and conquer | Hash map for O(n); shared index |
| Binary Tree Maximum Path Sum (LC 124) | Hard | Return one, track another | The negative-value twist |
| Serialize and Deserialize (LC 297) | Hard | Preorder + null markers | Why nulls remove the ambiguity |
| Delete Node in a BST (LC 450) | Medium | Case analysis | The inorder-successor substitution |

### Level 4 — Advanced (4, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Vertical Order Traversal (LC 987) | Hard | Coordinates + sorting | Reading tiebreak rules carefully |
| Flatten Binary Tree to Linked List (LC 114) | Medium | Reverse postorder | In-place restructuring |
| Boundary Traversal (GeeksforGeeks) | Medium | Three-part decomposition | Avoiding duplicate leaves |
| Morris Inorder Traversal (drill) | Hard | Threading | The O(1)-space answer |

**Three to over-prepare:** LC 236 (LCA), LC 98 (validate BST), and LC 124 (max path sum). They are the highest-frequency hard-ish tree questions and each teaches something that transfers. LC 543 is easy but teaches the pattern that LC 124 depends on, so do it first.

---

## Exit checklist

```
[ ] I write the contract sentence before coding any tree problem
[ ] I never trace tree recursion by hand
[ ] I know depth vs height, and LeetCode's node-counting convention
[ ] I can define full, complete, perfect, balanced
[ ] I can write all three DFS traversals from memory
[ ] I can write iterative inorder from memory
[ ] I know the iterative postorder trick
[ ] I snapshot q.size() in level order, automatically
[ ] I know inorder on a BST is sorted
[ ] I can write the O(n) balanced check with the -1 sentinel
[ ] I can explain "return one thing, track another"
[ ] I can write diameter and max path sum from the same pattern
[ ] I can state the three-way LCA contract
[ ] I know the BST LCA is iterative and O(1) space
[ ] I can give the counter-example to the naive validate-BST
[ ] I know why validate-BST needs long long bounds
[ ] I can write BST delete with all three cases
[ ] I know preorder + postorder does NOT determine a tree
[ ] I know why serialization needs null markers
[ ] I can pick DFS vs BFS from the problem statement
[ ] I never claim O(1) space for recursive traversal
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 10"** for Heaps and Priority Queues (8–10 hours, Tier 1). It is a short module that closes several loops: k-th largest (which you met as quickselect in Module 5), merge k sorted lists (flagged in Module 6), and the Top-K family generally.

It covers what a heap actually is (a complete binary tree in an array, which is why Section 9.1's array-indexing fact matters), heapify and build-heap and why building is O(n) rather than O(n log n), the fixed-size-heap trick that makes Top-K O(n log k), the two-heap technique for streaming medians, and the rule for when a heap beats sorting.
