# DSA Placement Handbook (C++) — Part 8
# Phase 6: Linked Lists

**Module 6 · 8–10 hours · Tier 1 · Requires: Modules 0, 4**

---

## What this module is actually testing

Linked list problems have almost no algorithmic depth. There is no clever insight in reversing a list. What they test is different, and worth naming explicitly because it changes how you should practise:

**Pointer discipline.** Can you manipulate three pointers at once without losing the list?

**Edge-case rigour.** Empty list, single node, two nodes, operating on the head, operating on the tail. Interviewers pick linked list questions precisely because these cases are easy to miss and easy to check.

**Clean code under pressure.** A correct linked list solution is short. A messy one is twice as long and full of special cases. The dummy-node technique in Section 6.3 is the single biggest lever here.

So the practice advice is unusual for this module: **do not rush to the next problem.** Write each solution, then deliberately test it on an empty list, a one-node list, and a case that modifies the head. That habit is what the module is for.

The module also contains one genuinely deep idea (Floyd's cycle detection and why the math works) and one classic design question (LRU cache) that appears constantly in placements.

---

## 6.1 Arrays vs linked lists

### The trade-off

| | Array / `vector` | Linked list |
|---|---|---|
| Access by index | **O(1)** | O(n) |
| Search | O(n) | O(n) |
| Insert / delete at front | O(n) | **O(1)** |
| Insert / delete at back | O(1) amortised | O(1) with a tail pointer |
| Insert / delete in middle | O(n) | **O(1) if you already have the node** |
| Memory layout | Contiguous, cache-friendly | Scattered, pointer-chasing |
| Extra memory | None | One pointer per node |

### The honest assessment

In real engineering, `vector` wins almost always. The O(1) middle insertion that linked lists advertise requires you to **already hold a pointer to that position**, and getting there is O(n). Meanwhile the cache behaviour of contiguous memory beats pointer-chasing by a factor that asymptotics do not show.

Linked lists earn their place when:
- You genuinely have the node already (LRU cache, intrusive lists in kernels).
- You are splicing whole sublists.
- You cannot afford the reallocation pause of a growing vector.

Say this if asked "when would you use a linked list over a vector". The expected bad answer is "insertion is O(1)". The good answer includes "only if I already have the node, otherwise finding it is O(n)".

### Must remember

1. Linked lists have no random access. `list[5]` does not exist; you walk.
2. O(1) middle insertion requires already holding the pointer.
3. Binary search is impossible on a linked list, which is why merge sort (not quick sort) is the sorting algorithm for lists.
4. `std::list` exists but you will essentially never use it. Interview problems give you raw `ListNode*` because the pointer work is the point.

---

## 6.2 Node definitions and basics

### The definitions to memorise

```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

struct DListNode {                       // doubly linked
    int val;
    DListNode *prev, *next;
    DListNode(int x) : val(x), prev(nullptr), next(nullptr) {}
};
```

You will retype `ListNode` many times in this module. Write it from memory now.

### Traversal

```cpp
for (ListNode* cur = head; cur != nullptr; cur = cur->next)
    cout << cur->val << " ";
```

`cur` is a **copy** of the head pointer. Moving it does not move `head`, which is exactly what makes traversal safe. This is worth being explicit about, because "I lost the head" is a common beginner failure and the reason it does not happen here is that pointers are passed by value.

### Insertion and deletion

```cpp
// Insert newNode AFTER node
newNode->next = node->next;
node->next = newNode;               // ORDER MATTERS: reverse it and you lose the tail

// Delete the node AFTER prev
ListNode* doomed = prev->next;
prev->next = doomed->next;
delete doomed;                      // optional in interviews
```

**The order of those two lines in insertion is not negotiable.** Writing `node->next = newNode;` first orphans everything after `node`, and the list silently loses its tail. Whenever you are relinking, ask: "what am I about to overwrite, and have I saved it?"

### Finding the length, the tail, and the k-th node

```cpp
int length(ListNode* head) {
    int n = 0;
    for (ListNode* cur = head; cur; cur = cur->next) n++;
    return n;
}

ListNode* tail(ListNode* head) {
    if (!head) return nullptr;
    ListNode* cur = head;
    while (cur->next) cur = cur->next;     // stop AT the last, not past it
    return cur;
}
```

Note the difference: `while (cur)` walks off the end; `while (cur->next)` stops on the last node. Which one you want depends on whether you need the last node or just to visit everything.

### Must remember

1. Always null-check before dereferencing. `cur->next->val` requires both `cur` and `cur->next` to be non-null.
2. When relinking, save what you are about to overwrite.
3. `while (cur)` visits every node; `while (cur->next)` stops at the last one.
4. Moving a local pointer does not move the caller's `head`. To change the head, return the new one.
5. `nullptr`, not `NULL`.

---

## 6.3 The dummy node technique

### 1. What is it?

A fake node placed before the real head, so that every real node has a predecessor. You return `dummy.next` at the end.

### 2. Why do we need it?

Because roughly half of all linked list bugs are the special case "what if the node I'm operating on is the head?" The head has no predecessor, so any code shaped as `prev->next = ...` breaks on it, and you end up writing an `if (node == head)` branch that duplicates logic.

A dummy node gives the head a predecessor and **deletes the special case entirely**. This is the single highest-leverage technique in the module.

### 3. Core idea

```
Without dummy:        head -> 1 -> 2 -> 3 -> null
                      (removing 1 needs special handling)

With dummy:   dummy -> head -> 1 -> 2 -> 3 -> null
                       ^
              now node 1 has a predecessor, like everyone else
```

### 4. Template

```cpp
ListNode* someOperation(ListNode* head) {
    ListNode dummy(0);                  // stack-allocated: no leak, no delete
    dummy.next = head;
    ListNode* prev = &dummy;

    while (prev->next) {
        if (shouldRemove(prev->next)) prev->next = prev->next->next;
        else                          prev = prev->next;
    }

    return dummy.next;                  // the possibly-new head
}
```

`ListNode dummy(0);` on the stack is cleaner than `new ListNode(0)` because there is nothing to free. Both are accepted; the stack version is one less thing to get wrong.

### 5. When should I use it?

**Whenever the head might change or be removed.** Specifically:

- Removing nodes by value or condition (the head might be removed).
- Removing the n-th node from the end (it might be the head).
- Merging two lists (you do not know which head wins).
- Building any new list (you need somewhere to attach the first node).
- Partitioning a list.

### 6. Example: remove all nodes with a given value

```cpp
ListNode* removeElements(ListNode* head, int val) {
    ListNode dummy(0);
    dummy.next = head;
    ListNode* prev = &dummy;

    while (prev->next) {
        if (prev->next->val == val) prev->next = prev->next->next;
        else                        prev = prev->next;
    }
    return dummy.next;
}
```

Six lines, no special cases, correct on an empty list and on a list that is entirely the target value. Without the dummy this needs a separate loop to strip leading matches first.

### 7. Must remember

1. Use a dummy whenever the head might change. It is not optional style; it removes a whole class of bugs.
2. **Return `dummy.next`, not `head`.** `head` may be stale or deleted. This is the mistake people make right after learning the technique.
3. Do not advance `prev` when you remove a node. The next node has shifted into position, and advancing skips it.
4. `ListNode dummy(0);` on the stack avoids the allocation entirely.
5. When building a new list, keep a separate `tail` pointer so appending stays O(1).

### 8. Common mistakes

- Returning `head` instead of `dummy.next`.
- Advancing `prev` after a removal, skipping the next node.
- Forgetting `dummy.next = head` at the start.
- Using a dummy but still writing a `if (node == head)` branch, which defeats the purpose.

### 9. Practice

- Remove Linked List Elements (LC 203, Easy)
- Remove Duplicates from Sorted List (LC 83, Easy)

---

## 6.4 Reversal

### 1. What is it?

Turning `1 → 2 → 3 → null` into `3 → 2 → 1 → null` by flipping every `next` pointer.

### 2. Why do we need it?

It is asked directly, and it is a sub-step in palindrome checking, reordering, reversing in groups, and adding numbers. It is also the cleanest test of whether you can juggle three pointers.

### 3. Core idea

You cannot flip `cur->next` without first saving where it pointed, or you lose the rest of the list.

```
prev   cur   nxt
null    1  →  2  →  3  →  null

step 1: save nxt = cur->next
step 2: cur->next = prev          (the flip)
step 3: prev = cur                (advance)
step 4: cur = nxt                 (advance)

after one iteration:
       prev  cur
null ←  1     2  →  3  →  null
```

### 4. Template (memorise the four lines in order)

```cpp
ListNode* reverseList(ListNode* head) {
    ListNode* prev = nullptr;
    ListNode* cur = head;

    while (cur) {
        ListNode* nxt = cur->next;    // 1. SAVE
        cur->next = prev;             // 2. REVERSE
        prev = cur;                   // 3. ADVANCE prev
        cur = nxt;                    // 4. ADVANCE cur
    }
    return prev;                      // prev is the new head
}
```

**Save, reverse, advance, advance.** Say it out loud while writing. The order cannot change: reversing before saving loses the list, advancing before reversing flips the wrong pointer.

**Return `prev`, not `cur`.** When the loop ends, `cur` is null and `prev` is the last node processed, which is the new head. Returning `cur` returns null, and the bug looks like "my function returns an empty list".

### 5. Recursive version

```cpp
ListNode* reverseList(ListNode* head) {
    if (!head || !head->next) return head;      // 0 or 1 node

    ListNode* newHead = reverseList(head->next);  // trust: rest is reversed
    head->next->next = head;                      // make the next node point back
    head->next = nullptr;                         // this node is now the tail
    return newHead;                               // head never changes going up
}
```

Contract (Module 4.3): *"returns the head of the reversed version of the list starting at `head`."* Assume it works on `head->next`, then `head->next` is now the **tail** of the reversed portion, so pointing it at `head` appends `head` to the end.

O(n) time, **O(n) space** for the stack. The iterative version is O(1) space and is what you should default to. Know both; interviewers sometimes ask for the recursive one specifically.

### 6. Reverse in groups of k (LC 25)

```cpp
ListNode* reverseKGroup(ListNode* head, int k) {
    // 1. Check that k nodes exist
    ListNode* node = head;
    for (int i = 0; i < k; i++) {
        if (!node) return head;               // fewer than k left: leave as is
        node = node->next;
    }

    // 2. Recursively reverse the rest; it returns the head of the reversed remainder
    ListNode* prev = reverseKGroup(node, k);

    // 3. Reverse this group, attaching it in front of the remainder
    ListNode* cur = head;
    for (int i = 0; i < k; i++) {
        ListNode* nxt = cur->next;
        cur->next = prev;
        prev = cur;
        cur = nxt;
    }
    return prev;
}
```

Elegant because step 3 is the standard reversal loop with `prev` **initialised to the already-reversed remainder** instead of `nullptr`. That one change does all the stitching. O(n) time, O(n/k) stack space.

### 7. Complexity

| Version | Time | Space |
|---|---|---|
| Iterative | O(n) | **O(1)** |
| Recursive | O(n) | O(n) |
| In groups of k | O(n) | O(n/k) |

### 8. Must remember

1. Save, reverse, advance, advance. In that order.
2. Return `prev`, never `cur`.
3. `prev` starts at `nullptr`, which is what terminates the reversed list correctly.
4. Recursive reversal is O(n) space. Mention this if the interviewer asks for O(1).
5. In group reversal, check that k nodes exist **before** reversing anything, or you will reverse a partial group.
6. Initialising `prev` to something other than `nullptr` is how you stitch a reversed segment onto an existing list.

### 9. Common mistakes

- Reversing before saving `next`, losing everything after `cur`.
- Returning `cur` (null) instead of `prev`.
- Initialising `prev = head` instead of `nullptr`, creating a cycle.
- Reversing a partial final group in the k-group problem.
- Forgetting `head->next = nullptr` in the recursive version, which creates a two-node cycle.

### 10. Practice

- Reverse Linked List (LC 206, Easy) — write both versions
- Reverse Linked List II (LC 92, Medium) — reverse a sublist; dummy node essential
- Reverse Nodes in k-Group (LC 25, Hard) — after the rest are solid

---

## 6.5 Fast and slow pointers

**The centrepiece of this module.** One idea handles finding the middle, finding the n-th from the end, detecting a cycle, and locating the cycle's start.

### 1. What is it?

Two pointers traversing the list at different speeds, or offset by a fixed gap. The relationship between them reveals structural information in a single pass.

### 2. Why do we need it?

The obvious solutions need two passes (count the length, then walk half of it) or O(n) extra space (store visited nodes in a set). Fast/slow gets the same answers in **one pass with O(1) space**, which is what the interviewer is fishing for when they say "can you do it in one pass?"

### 3. The two shapes

**Shape A: different speeds.** `slow` moves one step, `fast` moves two. Used for the middle and for cycle detection.

**Shape B: fixed gap.** `fast` starts n steps ahead, then both move at the same speed. Used for the n-th node from the end.

### 4. Finding the middle

```cpp
ListNode* middleNode(ListNode* head) {
    ListNode *slow = head, *fast = head;
    while (fast && fast->next) {          // ORDER MATTERS: short-circuit protects fast->next
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}
```

When `fast` reaches the end, it has travelled twice as far, so `slow` is at the halfway point.

**On even-length lists this returns the *second* middle.** For `[1,2,3,4]` it returns `3`. If you need the first middle (which palindrome checking does), change the condition:

```cpp
while (fast->next && fast->next->next) { ... }   // returns the FIRST middle
```

Know both. Which one you need depends on the problem, and picking the wrong one is an off-by-one that passes odd-length tests.

**`fast && fast->next` order is mandatory.** Testing `fast->next` first crashes when `fast` is null. C++ short-circuits `&&` left to right, which is what keeps this safe.

### 5. N-th node from the end

```cpp
ListNode* removeNthFromEnd(ListNode* head, int n) {
    ListNode dummy(0);
    dummy.next = head;
    ListNode *fast = &dummy, *slow = &dummy;

    for (int i = 0; i < n; i++) fast = fast->next;   // open a gap of n

    while (fast->next) {                             // move together until fast is last
        fast = fast->next;
        slow = slow->next;
    }

    slow->next = slow->next->next;                   // slow is just BEFORE the target
    return dummy.next;
}
```

The gap of n means that when `fast` is on the last node, `slow` is n+1 from the end, which is exactly the predecessor of the node to remove.

**The dummy is essential here.** Removing the n-th from the end can mean removing the head (when n equals the length), and without a dummy that needs a special case.

### 6. Cycle detection (Floyd's algorithm)

```cpp
bool hasCycle(ListNode* head) {
    ListNode *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;                    // fast hit null: no cycle
}
```

**Why they must meet.** Once both pointers are inside the cycle, `fast` gains exactly one position on `slow` per step. The gap between them shrinks by one each iteration, so it must eventually reach zero. They cannot "jump over" each other, because the gap decreases by exactly one. If there is no cycle, `fast` reaches null and the loop ends.

This is the argument to give when asked why it works. It is short and complete.

### 7. Finding where the cycle starts (LC 142)

```cpp
ListNode* detectCycle(ListNode* head) {
    ListNode *slow = head, *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;

        if (slow == fast) {                  // meeting point found
            ListNode* p = head;
            while (p != slow) {              // both move ONE step now
                p = p->next;
                slow = slow->next;
            }
            return p;                        // they meet at the cycle start
        }
    }
    return nullptr;
}
```

### 8. Why the cycle-start trick works

You asked for the reasoning behind algorithms, and this one is worth doing properly because it looks like magic otherwise.

```
head ──── L ────> S ────k────> M
                  ^            |
                  |            |
                  └──── C-k ───┘

L = distance from head to the cycle start S
C = cycle length
M = the meeting point, k steps into the cycle from S
```

When the pointers meet:

- `slow` has travelled `L + k`.
- `fast` has travelled `L + k + mC` for some whole number of extra loops `m ≥ 1`.
- `fast` moves twice as fast, so `L + k + mC = 2(L + k)`.

Rearranging: **`mC = L + k`**, so **`L = mC − k`**.

Now interpret that. A pointer starting at `M` (which is `k` steps into the cycle) and walking `mC − k` steps lands at position `k + mC − k = mC`, which is 0 modulo C, which is exactly the cycle start `S`.

And `mC − k` equals `L`, which is the distance from `head` to `S`.

So: **a pointer from `head` and a pointer from `M`, both moving one step at a time, arrive at `S` simultaneously.** That is the algorithm.

### 9. Removing the cycle

Find the start, then walk to the node just before it and cut:

```cpp
ListNode* start = detectCycle(head);
if (start) {
    ListNode* p = start;
    while (p->next != start) p = p->next;    // find the last node in the cycle
    p->next = nullptr;                        // cut
}
```

### 10. Complexity

| Operation | Time | Space |
|---|---|---|
| Middle | O(n) | O(1) |
| N-th from end | O(n) | O(1) |
| Cycle detection | O(n) | O(1) |
| Cycle start | O(n) | O(1) |

The hash-set alternative for cycle detection is also O(n) time but O(n) space. Floyd's is the answer when O(1) space is requested.

### 11. Must remember

1. `while (fast && fast->next)` in that exact order. Short-circuiting is what prevents the null dereference.
2. Even-length lists: `fast && fast->next` gives the **second** middle; `fast->next && fast->next->next` gives the **first**.
3. Use a dummy for n-th-from-end, because the head may be the target.
4. Floyd's works because the gap shrinks by exactly one per step inside the cycle.
5. Cycle start: reset one pointer to `head`, then move **both one step at a time**. Not two.
6. `L = mC − k` is the identity behind it. If you can state it, you understand it.
7. A hash set solves cycle detection in O(n) space and is a valid first answer. Floyd's is the follow-up.

### 12. Common mistakes

- `fast->next && fast` (wrong order), crashing on the last node.
- Moving the reset pointer two steps in the cycle-start phase.
- Returning the wrong middle for even lengths.
- Off-by-one in the n-th-from-end gap: it is `n` steps, not `n-1` or `n+1`.
- Starting `slow` and `fast` at different nodes. Both start at `head` for cycle detection.
- Traversing a list that has a cycle with a plain loop, hanging forever.

### 13. Practice

- Middle of the Linked List (LC 876, Easy)
- Linked List Cycle (LC 141, Easy)
- Remove Nth Node From End of List (LC 19, Medium)
- Linked List Cycle II (LC 142, Medium) — the one to understand, not memorise

---

## 6.6 Merging and sorting

### Merge two sorted lists (LC 21)

```cpp
ListNode* mergeTwoLists(ListNode* a, ListNode* b) {
    ListNode dummy(0);
    ListNode* tail = &dummy;

    while (a && b) {
        if (a->val <= b->val) { tail->next = a; a = a->next; }
        else                  { tail->next = b; b = b->next; }
        tail = tail->next;
    }
    tail->next = a ? a : b;              // attach whatever remains, in one line

    return dummy.next;
}
```

O(n + m) time, O(1) space. The final line is the neat part: at most one list has leftovers, and it is already sorted and correctly linked, so you attach it wholesale rather than looping.

This is the merge step from Module 5.3, done by relinking instead of copying, which is why it costs no extra space.

### Sort a linked list (LC 148)

Merge sort is **the** sorting algorithm for linked lists. Quick sort needs random access for a good pivot; merge sort needs only sequential access, and the O(n) merge buffer disappears because you relink.

```cpp
ListNode* sortList(ListNode* head) {
    if (!head || !head->next) return head;

    // 1. Split at the middle (FIRST middle, so both halves are non-empty)
    ListNode *slow = head, *fast = head->next;      // note: fast starts one ahead
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    ListNode* second = slow->next;
    slow->next = nullptr;                            // CUT the list in two

    // 2. Sort each half
    ListNode* left  = sortList(head);
    ListNode* right = sortList(second);

    // 3. Merge
    return mergeTwoLists(left, right);
}
```

**`slow->next = nullptr` is mandatory.** Without the cut, both recursive calls see the same full list and you get infinite recursion. This is the bug in this problem.

**`fast = head->next`** rather than `head` guarantees `slow` stops at the first middle, so a two-node list splits into 1+1 rather than 0+2. A 0+2 split recurses forever.

O(n log n) time, O(log n) stack space.

### Must remember

1. Merge two sorted lists with a dummy and a `tail` pointer.
2. `tail->next = a ? a : b` attaches the remainder in one line.
3. For list merge sort, **cut the list** with `slow->next = nullptr`.
4. Start `fast` at `head->next` so the split is balanced on two-node lists.
5. Merge sort, not quick sort, for linked lists. Be ready to say why: no random access needed, and the merge is O(1) space when relinking.
6. Merge k sorted lists is Module 10 (heap) or divide-and-conquer pairwise merging.

### Practice

- Merge Two Sorted Lists (LC 21, Easy)
- Sort List (LC 148, Medium)
- Merge k Sorted Lists (LC 23, Hard) — preview; proper treatment with heaps in Module 10

---

## 6.7 Intersection of two lists (LC 160)

Given two lists that may merge at some node, find the merge point.

The obvious approaches: hash set of one list's nodes (O(n) space), or compute both lengths and advance the longer one by the difference (two passes, O(1) space, perfectly good).

The elegant one:

```cpp
ListNode* getIntersectionNode(ListNode* a, ListNode* b) {
    ListNode *p = a, *q = b;
    while (p != q) {
        p = p ? p->next : b;         // at the end of A, jump to B
        q = q ? q->next : a;         // at the end of B, jump to A
    }
    return p;                        // the intersection, or nullptr
}
```

**Why it works.** Let list A have length `m` before the junction and list B have length `n` before it, with a shared tail of length `c`. Pointer `p` travels `m + c + n` before reaching the junction on its second pass. Pointer `q` travels `n + c + m`. Those are equal, so they arrive simultaneously.

If there is no intersection, both become `nullptr` at the same time (after `m + n + 2` steps each) and the loop exits with `p == q == nullptr`. The no-intersection case needs no special handling, which is the point.

**The subtle bit:** you must jump to the *other* list's head, and you must allow `p` to become `nullptr` before jumping. Writing `p = p->next ? p->next : b` skips the null state and breaks the no-intersection case by looping forever.

### Must remember

1. Both pointers travel `m + n + c` total, so they meet at the junction.
2. Allow the pointer to become `nullptr` before switching lists, or the no-intersection case hangs.
3. Compare **node pointers**, not values. Two nodes with equal values are not the same node.
4. The length-difference approach is equally valid and easier to explain. Offer it first, then the elegant one.

---

## 6.8 Palindrome linked list (LC 234)

A good problem because it composes three techniques from this module: find the middle, reverse a half, compare.

```cpp
bool isPalindrome(ListNode* head) {
    if (!head || !head->next) return true;

    // 1. Find the FIRST middle
    ListNode *slow = head, *fast = head;
    while (fast->next && fast->next->next) {
        slow = slow->next;
        fast = fast->next->next;
    }

    // 2. Reverse the second half
    ListNode* second = reverseList(slow->next);

    // 3. Compare the two halves
    ListNode *p = head, *q = second;
    bool ok = true;
    while (q) {                              // second half is shorter or equal
        if (p->val != q->val) { ok = false; break; }
        p = p->next;
        q = q->next;
    }

    // 4. Restore (good practice; some interviewers ask)
    slow->next = reverseList(second);

    return ok;
}
```

O(n) time, O(1) space. The O(n)-space alternative is copying values into a vector and using two pointers, which is a completely acceptable first answer. Give it, then offer this when asked to reduce space.

**Loop on `q`, not `p`.** On odd-length lists the first half is one node longer, so iterating until `p` is null overruns. Iterating until `q` is null naturally ignores the middle element, which is correct.

**Restoring the list** matters if the interviewer asks, and mentioning it unprompted is a small positive signal: you destroyed the caller's data structure and put it back.

---

## 6.9 Doubly and circular linked lists

### Doubly linked list

Each node has `prev` and `next`.

```cpp
// Insert n after node
n->next = node->next;
n->prev = node;
if (node->next) node->next->prev = n;
node->next = n;

// Delete node  (O(1) with no predecessor lookup)
if (node->prev) node->prev->next = node->next;
if (node->next) node->next->prev = node->prev;
```

**The point of a doubly linked list: O(1) deletion given only the node.** In a singly linked list you need the predecessor, which costs O(n) to find. This is exactly why the LRU cache needs a doubly linked list.

Cost: one extra pointer per node, and every operation touches twice as many pointers, so twice as many chances to get it wrong.

### Sentinel nodes

The dummy-node idea, applied at both ends:

```cpp
head <-> tail                    // two sentinels, list is empty
head <-> A <-> B <-> tail        // list with two real nodes
```

With sentinels, **every real node has both a `prev` and a `next`**, so insertion and deletion need no null checks at all:

```cpp
void remove(Node* n) {
    n->prev->next = n->next;
    n->next->prev = n->prev;     // no null checks needed
}
```

This is what makes the LRU cache implementation short. Use sentinels whenever you build a doubly linked list yourself.

### Circular linked list

The last node points back to the first.

```cpp
// Traversal: use a do-while, or stop when you return to the start
ListNode* cur = head;
do {
    visit(cur);
    cur = cur->next;
} while (cur != head);
```

A plain `while (cur)` never terminates. Detecting circularity is Floyd's algorithm from 6.5.

Circular lists show up in round-robin scheduling and the Josephus problem. They are low frequency in placements.

### Must remember

1. Doubly linked lists give O(1) deletion when you already hold the node. That is their entire justification.
2. Sentinel nodes at both ends remove all null checks.
3. Every doubly-linked operation updates **four** pointers. Missing one corrupts the list in a way that shows up much later.
4. Never traverse a circular list with `while (cur)`. Use `do-while` against the start node.
5. `std::list` is a doubly linked list with sentinels. Interview problems make you build it yourself because that is what is being tested.

---

## 6.10 LRU Cache (LC 146)

### 1. What is it?

A fixed-capacity cache where `get` and `put` are both O(1), and when the cache is full the **least recently used** entry is evicted.

### 2. Why do we need it?

It appears constantly in placement interviews, at both product and service companies, as a design-flavoured coding question. It is also the clearest example of combining two data structures to get properties neither has alone.

### 3. Core idea

You need three things simultaneously:

| Requirement | Given by |
|---|---|
| O(1) lookup by key | Hash map |
| O(1) reordering on access | Doubly linked list |
| O(1) eviction of the oldest | Tail of that list |

**Hash map → node pointer. Doubly linked list → recency order.**

The map finds the node in O(1). The doubly linked list lets you unlink that node in O(1) (because you have both neighbours) and re-insert it at the front. The least recently used item is always at the tail.

A singly linked list does not work: unlinking a node from the middle needs its predecessor, which is O(n) to find. That is the reason for the "doubly".

```
        MRU                                LRU
head <-> [k3] <-> [k1] <-> [k7] <-> [k2] <-> tail
          ^
   map: {k3: ptr, k1: ptr, k7: ptr, k2: ptr}
```

### 4. Implementation

```cpp
class LRUCache {
    struct Node {
        int key, val;
        Node *prev, *next;
        Node(int k, int v) : key(k), val(v), prev(nullptr), next(nullptr) {}
    };

    int cap;
    unordered_map<int, Node*> mp;
    Node *head, *tail;                       // sentinels

    void unlink(Node* n) {
        n->prev->next = n->next;
        n->next->prev = n->prev;
    }

    void pushFront(Node* n) {
        n->next = head->next;
        n->prev = head;
        head->next->prev = n;
        head->next = n;
    }

public:
    LRUCache(int capacity) : cap(capacity) {
        head = new Node(0, 0);
        tail = new Node(0, 0);
        head->next = tail;
        tail->prev = head;
    }

    int get(int key) {
        auto it = mp.find(key);
        if (it == mp.end()) return -1;
        Node* n = it->second;
        unlink(n);
        pushFront(n);                        // touching it makes it most recent
        return n->val;
    }

    void put(int key, int value) {
        auto it = mp.find(key);
        if (it != mp.end()) {                // existing key: update and promote
            Node* n = it->second;
            n->val = value;
            unlink(n);
            pushFront(n);
            return;
        }

        if ((int)mp.size() == cap) {         // full: evict the LRU
            Node* lru = tail->prev;
            unlink(lru);
            mp.erase(lru->key);              // THIS is why the node stores its key
            delete lru;
        }

        Node* n = new Node(key, value);
        mp[key] = n;
        pushFront(n);
    }
};
```

### 5. The two details that catch people

**The node must store its own key.** When you evict, you have a pointer to the node from the list, and you need to remove its entry from the map. Without `key` stored in the node, you cannot find the map entry, and the map grows forever while the list stays bounded. This is the classic bug in this problem.

**`put` on an existing key must promote it.** Updating the value without moving the node to the front means the recency order is wrong, and you evict the wrong entry later. Easy to miss because it only shows up on a specific test sequence.

### 6. The STL shortcut

If you are allowed to use the library:

```cpp
list<pair<int,int>> dll;                            // (key, value), front = MRU
unordered_map<int, list<pair<int,int>>::iterator> mp;

// promote:
dll.splice(dll.begin(), dll, mp[key]);              // O(1), iterator stays valid
```

`std::list::splice` moves a node in O(1) without invalidating its iterator, which is exactly what this needs. Shorter to write, but **write the manual version at least once**. Interviewers frequently ask you to implement the list yourself, and the manual version is what demonstrates you understand why a doubly linked list is required.

### 7. Complexity

`get` O(1), `put` O(1), space O(capacity).

### 8. Must remember

1. Hash map plus doubly linked list. Neither alone is enough.
2. The doubly linked list is required for O(1) unlinking from the middle.
3. **The node stores its key**, so eviction can clean up the map.
4. `put` on an existing key must promote it, not just update the value.
5. Sentinel head and tail remove all null checks from `unlink` and `pushFront`.
6. Most recent at the front, least recent at the tail (or the reverse; just be consistent).
7. LFU cache is the harder cousin, adding a frequency dimension. Know that it exists; it is asked far less often.

### 9. Common mistakes

- Using a singly linked list, making eviction or promotion O(n).
- Not storing the key in the node, leaking map entries.
- Forgetting to promote on a `put` to an existing key.
- Off-by-one on capacity: evict when `size == cap` **before** inserting, not after.
- Forgetting to update all four pointers in the doubly-linked operations.

---

## 6.11 Comparison tables

### Which technique for which problem

| Problem shape | Technique |
|---|---|
| Head might change or be removed | Dummy node |
| Find the middle | Fast/slow, different speeds |
| N-th from the end | Fast/slow, fixed gap of n |
| Detect a cycle | Floyd's, different speeds |
| Find cycle start | Floyd's, then reset one to head |
| Reverse the list | Three-pointer iterative |
| Reverse a sublist or group | Iterative reversal with a non-null starting `prev` |
| Check palindrome | Middle + reverse second half + compare |
| Merge sorted lists | Dummy + tail pointer |
| Sort a list | Merge sort (split, cut, sort, merge) |
| Find intersection | Two-pointer list switching |
| O(1) delete given a node | Doubly linked list |
| LRU cache | Hash map + doubly linked list |

### Fast/slow variants

| Goal | Initialisation | Loop condition | Answer |
|---|---|---|---|
| Second middle | both at `head` | `fast && fast->next` | `slow` |
| First middle | both at `head` | `fast->next && fast->next->next` | `slow` |
| Balanced split | `slow=head`, `fast=head->next` | `fast && fast->next` | cut after `slow` |
| Cycle detection | both at `head` | `fast && fast->next` | `slow == fast` |
| N-th from end | both at dummy, advance `fast` n | `fast->next` | `slow` is the predecessor |

### Linked list vs array, restated

| Need | Use |
|---|---|
| Random access, binary search | Array |
| Frequent insertion/deletion **with the node in hand** | Linked list |
| Cache performance | Array |
| Unknown size, no reallocation pauses | Linked list |
| Sorting | Array (any sort) / Linked list (merge sort) |

---

## 6.12 Must remember (consolidated)

1. Null-check before every dereference. `cur->next->val` needs two checks.
2. `while (fast && fast->next)` in that order. Short-circuiting is load-bearing.
3. Use a dummy node whenever the head might change, and return `dummy.next`.
4. Do not advance `prev` after removing a node.
5. Reversal is save, reverse, advance, advance. Return `prev`.
6. Recursive reversal is O(n) space; iterative is O(1).
7. Even-length middle: `fast && fast->next` gives the second, `fast->next && fast->next->next` gives the first.
8. Cycle start: reset one pointer to head, then move **both one step**.
9. The cycle identity is `L = mC − k`.
10. In list merge sort, cut with `slow->next = nullptr` or you recurse forever.
11. Start `fast = head->next` for a balanced split on two-node lists.
12. In intersection, allow the pointer to become null before switching lists.
13. In palindrome, loop on the second-half pointer, not the first.
14. Doubly linked lists give O(1) deletion given the node. That is why LRU needs one.
15. Sentinel nodes at both ends eliminate all null checks.
16. LRU nodes must store their key so eviction can clean the map.
17. Compare node **pointers**, not values, when asking "is this the same node".

---

## 6.13 Common mistakes (consolidated)

**Segfault**
- Dereferencing null: `cur->next->val` without checking `cur->next`.
- `fast->next && fast` instead of `fast && fast->next`.
- Operating on an empty list without an early return.
- Accessing a node after `delete`.

**Infinite loop**
- Forgetting `slow->next = nullptr` when splitting for merge sort.
- Splitting a two-node list into 0+2.
- Traversing a circular or cyclic list with `while (cur)`.
- `p = p->next ? p->next : b` in the intersection problem.
- Setting `prev = head` instead of `nullptr` at the start of reversal.

**Wrong answer**
- Returning `head` instead of `dummy.next`.
- Returning `cur` instead of `prev` from reversal.
- Advancing `prev` after a removal, skipping a node.
- Wrong middle on even-length lists.
- Off-by-one in the n-th-from-end gap.
- Not promoting on an LRU `put` to an existing key.
- Comparing values when you meant to compare node identity.

**Memory / structural**
- Relinking in the wrong order and orphaning the tail.
- Updating only two of the four pointers in a doubly linked operation.
- LRU map growing unboundedly because nodes do not store their key.

---

## 6.14 Problem set

Twelve core problems. For each one, after you get it accepted, **run it mentally on an empty list, a one-node list, and a two-node list.** That habit is most of what this module teaches.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Reverse Linked List (LC 206) | Easy | Three-pointer reversal | The four lines, in order. Write both versions |
| Middle of the Linked List (LC 876) | Easy | Fast/slow | The loop condition and the even-length question |
| Merge Two Sorted Lists (LC 21) | Easy | Dummy + tail | Why `tail->next = a ? a : b` works |

### Level 2 — Pattern (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Linked List Cycle (LC 141) | Easy | Floyd's | Why the gap shrinks by one |
| Remove Nth Node From End (LC 19) | Medium | Fixed gap + dummy | Why the dummy is not optional |
| Remove Duplicates from Sorted List (LC 83) | Easy | Traversal + relink | Not advancing after removal |
| Intersection of Two Linked Lists (LC 160) | Easy | Pointer switching | Node identity vs value equality |
| Palindrome Linked List (LC 234) | Easy | Middle + reverse + compare | Composing three techniques |

### Level 3 — Interview (4)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Linked List Cycle II (LC 142) | Medium | Floyd's + reset | The `L = mC − k` derivation. Understand, don't memorise |
| Add Two Numbers (LC 2) | Medium | Dummy + carry | Carry handling and unequal lengths |
| Sort List (LC 148) | Medium | Merge sort on lists | The cut, and the balanced split |
| **LRU Cache (LC 146)** | Medium | Hash map + DLL | The most-asked design question in this module |

### Level 4 — Advanced (3, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Reverse Nodes in k-Group (LC 25) | Hard | Grouped reversal | Non-null starting `prev` does the stitching |
| Reorder List (LC 143) | Medium | Middle + reverse + merge | Three techniques again, harder assembly |
| Copy List with Random Pointer (LC 138) | Medium | Interleaving or hash map | Two approaches; the O(1)-space one is clever |

**LC 146 is the one to over-prepare.** Write it from scratch, without the STL shortcut, until you can do it in ten minutes with sentinels and correct eviction. It comes up often enough to be worth that investment.

---

## Exit checklist

```
[ ] I can write ListNode and DListNode from memory
[ ] I null-check before every dereference
[ ] I use a dummy node whenever the head might change
[ ] I return dummy.next, not head
[ ] I can write iterative reversal from memory: save, reverse, advance, advance
[ ] I return prev, not cur
[ ] I can write recursive reversal and state its space cost
[ ] I write while (fast && fast->next) in that order, automatically
[ ] I know which loop condition gives the first vs second middle
[ ] I can explain WHY Floyd's algorithm terminates
[ ] I can derive L = mC - k and explain the cycle-start reset
[ ] I can merge two sorted lists with a dummy and tail
[ ] I remember to cut the list when splitting for merge sort
[ ] I can explain why intersection two-pointer switching works
[ ] I know why LRU needs a DOUBLY linked list
[ ] I know why the LRU node must store its key
[ ] I can write LRU Cache from scratch in under 15 minutes
[ ] I test every solution on empty, one-node, and two-node lists
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 7"** for Stacks and Queues (10–12 hours). The basic containers take twenty minutes; the module is really about the **monotonic stack**, which is the technique behind next-greater-element, largest-rectangle-in-histogram, and stock-span problems, and the **monotonic deque**, which finally settles Sliding Window Maximum from Module 2.

Both look O(n²) and are O(n), and being able to explain why in one sentence is the thing that gets tested.
