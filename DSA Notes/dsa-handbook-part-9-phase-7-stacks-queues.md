# DSA Placement Handbook (C++) — Part 9
# Phase 7: Stacks and Queues

**Module 7 · 10–12 hours · Tier 1 · Requires: Modules 0, 1, 2**

---

## Where the 12 hours go

The containers themselves take twenty minutes. `push`, `pop`, `top`, done. If that were the module it would be a footnote.

The actual content is two patterns:

**The monotonic stack** (Section 7.5), which is behind next-greater-element, daily temperatures, stock span, largest rectangle in histogram, and trapping rain water. It is the single most under-recognised pattern in interview DSA: candidates who have not met it will write O(n²) and never see the linear solution.

**The monotonic deque** (Section 7.10), which finally settles Sliding Window Maximum, the problem Module 2 left as a preview.

Both look quadratic and are linear, and being able to say *why* in one sentence is what gets tested. That sentence is: **each element is pushed once and popped at most once, so the total work is O(n)** — the amortisation argument from Module 1, Section 1.6.

Budget roughly: 2 hours on the basics and design questions, 6 on monotonic stack, 3 on queues and the monotonic deque.

---

# PART A — Stacks

## 7.1 Stack

### 1. What is it?

A last-in-first-out container. You can add to the top, remove from the top, and look at the top. Nothing else.

### 2. Why do we need it?

Because a surprising number of problems reduce to **"remember things until I find their match"**, and the match is always for the most recent unmatched thing. That is exactly LIFO. Parentheses, function calls, undo history, expression evaluation, and monotonic scanning are all this shape.

### 3. Core idea

The restriction is the feature. A stack cannot let you look at the middle, and that constraint is what makes the algorithms built on it O(1) per operation.

The deeper framing: **a stack is the memory of things you have seen but not yet resolved.** In parentheses matching it holds unclosed brackets. In a monotonic stack it holds elements still waiting for their next greater element. If you can phrase a problem that way, a stack is the answer.

### 4. When should I use it?

| Signal | Why a stack |
|---|---|
| "Matching" pairs: brackets, tags, quotes | Most recent unmatched is what you need |
| "Undo", "back button", "previous state" | LIFO is literally the semantics |
| Recursion converted to iteration | You are rebuilding the call stack |
| Expression evaluation, postfix | Operands wait for their operator |
| "Next/previous greater or smaller" | Monotonic stack (7.5) |
| DFS without recursion | Module 12 |
| "Collision", "cancel out", "collapse adjacent" | Push, and pop when the new element annihilates the old |

### 5. STL usage

```cpp
stack<int> st;
st.push(x);        // O(1)
st.pop();          // O(1), returns VOID
st.top();          // O(1), read the top
st.empty();
st.size();
```

`pop()` returns nothing. Read with `top()` first. Calling `top()` or `pop()` on an empty stack is **undefined behaviour**, not an exception, so every read is guarded:

```cpp
while (!st.empty() && condition(st.top())) { ... }
```

That `!st.empty() &&` prefix appears in every monotonic stack you will ever write. It is not defensive coding; it is required.

### 6. Implementing one yourself

Occasionally asked. Both are five lines.

```cpp
// Array-backed: a vector IS a stack
class ArrayStack {
    vector<int> data;
public:
    void push(int x) { data.push_back(x); }
    void pop()       { if (!data.empty()) data.pop_back(); }
    int  top()       { return data.back(); }
    bool empty()     { return data.empty(); }
};
```

In practice, **a `vector` used with `push_back` / `pop_back` / `back()` is a faster stack than `std::stack`** and many competitive programmers use nothing else. Either is fine in an interview.

### 7. Complexity

All operations O(1). Space O(n).

### 8. Must remember

1. `pop()` returns void. Read `top()` first.
2. `top()` on an empty stack is undefined behaviour. Always guard with `!st.empty()`.
3. `stack` is an adapter over `deque` by default. You cannot iterate it. If you need to inspect the middle, you picked the wrong container.
4. A `vector` works as a stack and is faster.
5. The call stack is a stack. Any recursion can be rewritten with an explicit one (Module 4.10).

### 9. Common mistakes

- `int x = st.pop();` — compile error, `pop` returns void.
- Reading `top()` after `pop()` and getting the wrong element.
- Forgetting `!st.empty()` in a while condition, crashing on the last iteration.
- Trying to iterate a `stack`.

---

## 7.2 Balanced parentheses

The canonical "stack as memory of unresolved things" problem.

```cpp
bool isValid(const string& s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') {
            st.push(c);
        } else {
            if (st.empty()) return false;              // closer with nothing open
            char open = st.top();
            if ((c == ')' && open != '(') ||
                (c == ']' && open != '[') ||
                (c == '}' && open != '{')) return false;
            st.pop();
        }
    }
    return st.empty();                                 // NOT `return true`
}
```

### The three failure modes, and the three checks

| Failure | Example | Caught by |
|---|---|---|
| Closer with nothing open | `")("` | `if (st.empty()) return false` |
| Wrong type of closer | `"(]"` | the type comparison |
| Openers left unclosed | `"(("` | `return st.empty()` at the end |

**`return st.empty()` rather than `return true` is the mistake people make.** A string of only opening brackets passes every in-loop check and is still invalid.

### A cleaner variant

```cpp
bool isValid(const string& s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(') st.push(')');                    // push the EXPECTED closer
        else if (c == '[') st.push(']');
        else if (c == '{') st.push('}');
        else {
            if (st.empty() || st.top() != c) return false;
            st.pop();
        }
    }
    return st.empty();
}
```

Pushing the expected closing bracket collapses three comparisons into one. Worth knowing; interviewers notice the simplification.

### Practice

- Valid Parentheses (LC 20, Easy)
- Minimum Remove to Make Valid Parentheses (LC 1249, Medium) — same idea, tracking indices

---

## 7.3 Expression notation and evaluation

**Medium priority.** Postfix evaluation is asked reasonably often; infix-to-postfix conversion is asked mostly in university vivas and service-company written rounds. Know the first well, the second conceptually.

### The three notations

| Notation | Form | Example (`3 + 4 × 2`) |
|---|---|---|
| Infix | operator between operands | `3 + 4 * 2` |
| Prefix (Polish) | operator before operands | `+ 3 * 4 2` |
| Postfix (Reverse Polish) | operator after operands | `3 4 2 * +` |

The point of prefix and postfix: **no parentheses needed and no precedence rules.** The order is unambiguous from the structure alone, which is why compilers and calculators convert to postfix internally.

### Evaluating postfix

```cpp
int evalRPN(const vector<string>& tokens) {
    stack<long long> st;
    for (const string& t : tokens) {
        if (t == "+" || t == "-" || t == "*" || t == "/") {
            long long b = st.top(); st.pop();          // SECOND operand pops first
            long long a = st.top(); st.pop();
            if      (t == "+") st.push(a + b);
            else if (t == "-") st.push(a - b);
            else if (t == "*") st.push(a * b);
            else               st.push(a / b);
        } else {
            st.push(stoll(t));
        }
    }
    return (int)st.top();
}
```

**The operand order is the bug.** The stack pops in reverse, so the first `pop` gives the *right* operand. Getting it backwards is invisible for `+` and `*` and wrong for `-` and `/`, which means it passes half the tests.

### Infix to postfix (shunting yard), in brief

Scan left to right:
- Operand → output it.
- Operator → pop operators of **greater or equal precedence** off the stack to the output, then push this one.
- `(` → push.
- `)` → pop to output until `(`, then discard the `(`.
- At the end, pop everything remaining.

For right-associative operators like `^`, pop only strictly greater precedence.

That is the whole algorithm. Implement it once if your target companies include service-based firms with written rounds; otherwise knowing the shape is enough.

### Must remember

1. In postfix evaluation, the **second** operand pops first.
2. Postfix needs no parentheses and no precedence table. That is its purpose.
3. Use `long long` for intermediate results.
4. Integer division in C++ truncates toward zero, which matches most problem statements but not all. Check.
5. Prefix evaluation is the same algorithm scanning **right to left**, with the operand order flipped.

### Practice

- Evaluate Reverse Polish Notation (LC 150, Medium)
- Basic Calculator II (LC 227, Medium) — optional, infix with precedence

---

## 7.4 Stack design questions

Three standard ones. They test whether you can reason about invariants rather than recall an algorithm.

### Min Stack (LC 155): O(1) minimum

Keep a second stack holding the minimum at each point in time.

```cpp
class MinStack {
    stack<int> st, mins;
public:
    void push(int x) {
        st.push(x);
        if (mins.empty() || x <= mins.top()) mins.push(x);
    }
    void pop() {
        if (st.top() == mins.top()) mins.pop();
        st.pop();
    }
    int top()    { return st.top(); }
    int getMin() { return mins.top(); }
};
```

**`x <= mins.top()` with `<=`, not `<`.** With strict `<`, pushing two copies of the minimum records it once, and popping the first copy removes it from `mins` while a copy is still in `st`. The minimum then reports wrongly. This single character is what the problem is testing.

The O(1)-extra-space variant (storing encoded differences) exists and is clever, but the two-stack version is the expected answer.

### Queue using two stacks (LC 232)

```cpp
class MyQueue {
    stack<int> in, out;
    void shift() {
        if (out.empty())
            while (!in.empty()) { out.push(in.top()); in.pop(); }
    }
public:
    void push(int x) { in.push(x); }
    int  pop()  { shift(); int v = out.top(); out.pop(); return v; }
    int  peek() { shift(); return out.top(); }
    bool empty() { return in.empty() && out.empty(); }
};
```

**Amortised O(1).** Each element moves from `in` to `out` exactly once in its lifetime, so n operations cost O(n) total. This is the same amortisation argument as `vector::push_back`, and stating it is the expected answer to "isn't that O(n)?"

**Only shift when `out` is empty.** Shifting on every call destroys the ordering and the complexity.

### Stack using two queues

Less common. Push is O(1) and pop is O(n) (rotate the queue), or push is O(n) and pop is O(1). Know that the trade-off exists; the queue-from-stacks direction is the one that actually gets asked.

### Practice

- Min Stack (LC 155, Medium)
- Implement Queue using Stacks (LC 232, Easy)

---

## 7.5 Monotonic Stack

**The centrepiece of this module.** If you learn one thing from Phase 7, learn this.

### 1. What is it?

A stack whose contents are kept in sorted order (always increasing or always decreasing from bottom to top). You enforce this by popping elements that would violate the order before pushing a new one.

### 2. Why do we need it?

A whole family of problems asks "for each element, find the nearest element to its left or right that is greater or smaller". The brute force is a nested loop, O(n²). The monotonic stack solves all four variants in O(n), and the code is six lines.

Crucially, **candidates who have not seen this pattern do not find it under interview pressure.** It is not something you derive on the spot. This is why it is worth six hours.

### 3. Core idea

The insight is about **who can never be an answer again**.

Suppose you are scanning right to left looking for each element's next greater element. You hold a stack of candidates. When you reach element `x`, any candidate on the stack that is **smaller than or equal to `x`** can never be the answer for anything further left: `x` is closer and at least as large, so it wins every time. Those candidates are permanently useless and you pop them.

What remains is a stack in decreasing order, and its top is exactly the answer for `x`.

```
a = [2, 1, 2, 4, 3]     next greater element for each

i=4 (3): stack empty          -> res[4] = -1,  push 3    stack: [3]
i=3 (4): pop 3 (3 <= 4)       -> res[3] = -1,  push 4    stack: [4]
i=2 (2): top is 4 > 2         -> res[2] = 4,   push 2    stack: [4,2]
i=1 (1): top is 2 > 1         -> res[1] = 2,   push 1    stack: [4,2,1]
i=0 (2): pop 1 (1 <= 2)       -> res[0] = 4,   push 2    stack: [4,2]

result: [4, 2, 4, -1, -1]
```

### 4. Why it is O(n)

Each index is pushed exactly once and popped at most once. The `while` loop inside the `for` looks quadratic, but the total number of pops across the entire run is bounded by n. So the whole thing is O(n).

**Rehearse this sentence.** "Each element is pushed once and popped at most once, so the total work is linear." It is the exact answer to the complexity question, and it is Module 1's amortisation argument applied.

### 5. The four variants (the table to memorise)

Two independent choices: **direction** decides next vs previous, **comparison** decides greater vs smaller.

| Want | Iterate | Pop while stack top is | Stack ends up |
|---|---|---|---|
| **Next greater** | right → left | `<= a[i]` | decreasing |
| **Next smaller** | right → left | `>= a[i]` | increasing |
| **Previous greater** | left → right | `<= a[i]` | decreasing |
| **Previous smaller** | left → right | `>= a[i]` | increasing |

Note the pattern: **direction of iteration flips next/previous; direction of the comparison flips greater/smaller.** Nothing else changes. One template, four problems.

Use strict `<` or `>` in the pop condition when you want to treat equal elements as valid answers; use `<=` / `>=` when you do not. For most problems either works; for counting problems (like Sum of Subarray Minimums) the choice prevents double counting.

### 6. C++ template

```cpp
// NEXT GREATER ELEMENT for every index
vector<int> nextGreater(const vector<int>& a) {
    int n = a.size();
    vector<int> res(n, -1);
    stack<int> st;                                  // holds INDICES

    for (int i = n - 1; i >= 0; i--) {              // right to left
        while (!st.empty() && a[st.top()] <= a[i])  // pop the useless
            st.pop();
        res[i] = st.empty() ? -1 : a[st.top()];     // top is the answer
        st.push(i);
    }
    return res;
}
```

Four lines inside the loop: **pop, read, push.** Change the iteration direction and the comparison operator to get the other three variants.

**Store indices, not values.** You almost always need the distance (`i - st.top()`) or need to index back into the array. Daily Temperatures needs exactly this.

### 7. Worked example: Daily Temperatures (LC 739)

*For each day, how many days until a warmer temperature?*

This is "next greater element", returning the **distance** rather than the value.

```cpp
vector<int> dailyTemperatures(const vector<int>& t) {
    int n = t.size();
    vector<int> res(n, 0);
    stack<int> st;

    for (int i = n - 1; i >= 0; i--) {
        while (!st.empty() && t[st.top()] <= t[i]) st.pop();
        res[i] = st.empty() ? 0 : st.top() - i;     // DISTANCE, not value
        st.push(i);
    }
    return res;
}
```

Identical structure, one line different. That is the payoff of learning the template rather than the problem.

### 8. The left-to-right formulation

An equivalent and very common way to write "next greater", scanning forward and **resolving elements as they get popped**:

```cpp
vector<int> nextGreater(const vector<int>& a) {
    int n = a.size();
    vector<int> res(n, -1);
    stack<int> st;

    for (int i = 0; i < n; i++) {
        while (!st.empty() && a[st.top()] < a[i]) {
            res[st.top()] = a[i];                   // a[i] IS the next greater for st.top()
            st.pop();
        }
        st.push(i);
    }
    return res;
}
```

Same complexity, same result. The mental model differs: here you are saying *"the current element resolves everything smaller waiting on the stack"*. Some problems (histogram, trapping water) need this formulation because the work happens **at the moment of popping**, when you know both boundaries.

Know both. The right-to-left one is easier for plain next-greater; the left-to-right one is required for the area problems below.

### 9. Circular arrays (LC 503)

When the array wraps, iterate twice over `2n` indices using `i % n`, and only record answers on the second pass (or record on the first `n` and let the second pass fill gaps):

```cpp
for (int i = 2 * n - 1; i >= 0; i--) {
    while (!st.empty() && a[st.top()] <= a[i % n]) st.pop();
    if (i < n) res[i] = st.empty() ? -1 : a[st.top()];
    st.push(i % n);
}
```

### 10. Complexity

O(n) time, O(n) space for the stack. The space is genuinely O(n) in the worst case (a strictly sorted array pushes everything before popping anything).

### 11. Must remember

1. **Each element pushed once, popped at most once → O(n).** Say it exactly like that.
2. Store **indices**, not values.
3. Direction of iteration flips next/previous. Direction of comparison flips greater/smaller. Four problems, one template.
4. Always guard with `!st.empty() &&` before reading `st.top()`.
5. Two formulations exist: right-to-left (read the answer from the top) and left-to-right (assign the answer when popping). Area problems need the second.
6. `<=` vs `<` in the pop condition determines how equal elements are treated. It matters for counting problems.
7. Circular arrays: iterate `2n` with `i % n`.

### 12. Common mistakes

- Storing values instead of indices, then being unable to compute a distance.
- Missing the `!st.empty()` guard.
- Reporting the complexity as O(n²) because of the nested `while`.
- Wrong comparison direction, producing next-smaller when you wanted next-greater.
- Forgetting to handle "no such element" (the `-1` or `0` default).
- Using the right-to-left formulation on a histogram problem where you need both boundaries at pop time.

### 13. Practice

- Next Greater Element I (LC 496, Easy) — the pattern in isolation
- Daily Temperatures (LC 739, Medium) — the distance variant
- Next Greater Element II (LC 503, Medium) — circular
- Asteroid Collision (LC 735, Medium) — a stack where pushes annihilate

---

## 7.6 Histogram and area problems

The hardest application of monotonic stacks, and a recurring hard-level interview question.

### Largest Rectangle in Histogram (LC 84)

*Given bar heights, find the largest rectangle that fits entirely under the histogram.*

**The key reframing:** for each bar, the largest rectangle **using that bar as its height** extends left until a shorter bar and right until a shorter bar. So the problem is "find the previous smaller and next smaller for every bar", which is a monotonic stack.

```cpp
int largestRectangleArea(const vector<int>& h) {
    int n = h.size();
    stack<int> st;                                  // increasing heights
    long long best = 0;

    for (int i = 0; i <= n; i++) {                  // note: i goes to n
        int cur = (i == n) ? 0 : h[i];              // sentinel: flushes the stack

        while (!st.empty() && h[st.top()] >= cur) {
            int height = h[st.top()];
            st.pop();
            int left = st.empty() ? -1 : st.top();  // previous smaller
            long long width = i - left - 1;         // i is the next smaller
            best = max(best, (long long)height * width);
        }
        st.push(i);
    }
    return (int)best;
}
```

Three things make this work, and all three are where it goes wrong:

**The sentinel.** Running `i` to `n` with `cur = 0` forces every remaining bar off the stack at the end. Without it, bars never popped are never measured, and an increasing histogram returns 0.

**The width formula.** When you pop a bar, `i` is its next smaller element and `st.top()` (after popping) is its previous smaller. The rectangle spans indices `left+1` to `i-1`, so the width is `i - left - 1`. Deriving this on paper once is worth more than memorising it.

**Popping after the pop.** `left` must be read **after** removing the current bar, because the previous smaller is whatever is beneath it.

O(n) time, O(n) space.

### Trapping Rain Water (LC 42), stack version

Module 2 gave the two-pointer solution. The stack version computes water in **horizontal layers**:

```cpp
int trap(const vector<int>& h) {
    stack<int> st;
    int water = 0;

    for (int i = 0; i < (int)h.size(); i++) {
        while (!st.empty() && h[st.top()] < h[i]) {
            int bottom = st.top(); st.pop();
            if (st.empty()) break;                  // no left wall: no water
            int left = st.top();
            int width = i - left - 1;
            int height = min(h[left], h[i]) - h[bottom];
            water += width * height;
        }
        st.push(i);
    }
    return water;
}
```

Both approaches are O(n). **The two-pointer version is O(1) space and is the better interview answer**; the stack version is worth knowing because it generalises to the histogram family and because interviewers sometimes ask for a second approach.

### Maximal Rectangle (LC 85)

*Largest rectangle of 1s in a binary matrix.*

Treat each row as the base of a histogram: the height at each column is the number of consecutive 1s ending at that row. Run the histogram algorithm on every row.

```cpp
int maximalRectangle(const vector<vector<char>>& g) {
    if (g.empty()) return 0;
    int m = g[0].size(), best = 0;
    vector<int> heights(m, 0);

    for (const auto& row : g) {
        for (int j = 0; j < m; j++)
            heights[j] = (row[j] == '1') ? heights[j] + 1 : 0;   // reset on 0
        best = max(best, largestRectangleArea(heights));
    }
    return best;
}
```

O(n·m). The reduction (2D problem → n instances of a 1D problem) is the insight, and it is worth internalising as a general move.

### Must remember

1. Histogram framing: for each bar, extend to the previous smaller and the next smaller.
2. The sentinel (`i == n`, height 0) is mandatory to flush the stack.
3. Width is `i - left - 1`, with `left` read **after** popping.
4. Maximal Rectangle reduces to running the histogram algorithm once per row.
5. For trapping rain water, two pointers is O(1) space and the preferred answer; the stack version is the layer-by-layer alternative.
6. Use `long long` for areas when heights and widths can both reach 10⁵.

---

# PART B — Queues

## 7.7 Queue and circular queue

### Basic queue

```cpp
queue<int> q;
q.push(x);       // enqueue at back
q.pop();         // dequeue from front, returns VOID
q.front();       // read front
q.back();        // read back
q.empty();  q.size();
```

Same rules as `stack`: `pop()` returns void, and reading an empty queue is undefined behaviour.

**The primary use of a queue in this handbook is BFS** (Module 12). Everything about level-order tree traversal, shortest paths in unweighted graphs, and multi-source flood fill runs on a queue. Everything else here is preparation for that.

### Circular queue (LC 622)

A fixed-size buffer where the front wraps around, so you never shift elements.

```cpp
class MyCircularQueue {
    vector<int> buf;
    int head = 0, count = 0, cap;
public:
    MyCircularQueue(int k) : buf(k), cap(k) {}

    bool enQueue(int v) {
        if (count == cap) return false;
        buf[(head + count) % cap] = v;              // the wrap
        count++;
        return true;
    }
    bool deQueue() {
        if (count == 0) return false;
        head = (head + 1) % cap;
        count--;
        return true;
    }
    int Front() { return count ? buf[head] : -1; }
    int Rear()  { return count ? buf[(head + count - 1) % cap] : -1; }
    bool isEmpty() { return count == 0; }
    bool isFull()  { return count == cap; }
};
```

**Track `count`, not just `head` and `tail`.** With only two indices, "full" and "empty" both look like `head == tail` and you cannot distinguish them. The classic textbook workaround is wasting one slot; keeping a count is cleaner and is the better answer.

Circular queues matter in practice for ring buffers and fixed-memory producer-consumer systems. In interviews they are a moderate-frequency design question.

### Must remember

1. `pop()` returns void; guard reads with `empty()`.
2. Queue is the BFS container. That is its main job.
3. In a circular queue, track a `count` to disambiguate full from empty.
4. `(head + count) % cap` for the next write position; `(head + count - 1) % cap` for the rear.

---

## 7.8 Deque

A double-ended queue: O(1) insertion and removal at **both** ends, plus random access.

```cpp
deque<int> dq;
dq.push_back(x);   dq.push_front(x);
dq.pop_back();     dq.pop_front();
dq.front();        dq.back();
dq[i];                                // random access works, unlike stack/queue
```

A deque can act as a stack, a queue, or both at once. It is not contiguous in memory (it is a sequence of fixed-size blocks), so random access is slightly slower than `vector` and you cannot pass `&dq[0]` to something expecting a C array.

### Why it exists in this module

One reason: **the monotonic deque**. You need to remove from the front (expiring elements that have left the window) and from the back (maintaining monotonicity) at the same time. A stack cannot do the first; a queue cannot do the second.

### When to use which

| Need | Container |
|---|---|
| Add/remove at one end only | `stack` or `queue` |
| Add/remove at both ends | `deque` |
| Both, plus ordering maintained | **Monotonic deque** |
| Add anywhere, read by index | `vector` |
| Always retrieve the extreme, arbitrary insertion order | `priority_queue` (Module 10) |

---

## 7.9 Monotonic Deque and Sliding Window Maximum

### 1. What is it?

A deque holding indices whose corresponding values are kept monotonic, with expired indices removed from the front. It maintains the maximum (or minimum) of a sliding window in O(1) per step.

### 2. Why do we need it?

Sliding Window Maximum (LC 239) is the problem Module 2 flagged as a preview. The obvious solutions:

| Approach | Time | Problem |
|---|---|---|
| Recompute max per window | O(n·k) | Too slow for n = 10⁵, k = 10⁴ |
| `multiset` with insert/erase | O(n log k) | Works, acceptable answer |
| **Monotonic deque** | **O(n)** | The expected answer |

The `multiset` solution is genuinely fine and worth offering first. The deque is the follow-up when asked to do better.

### 3. Core idea

Same insight as the monotonic stack, plus expiry.

**Who can never be the maximum again?** If element `a[j]` is at the back of the deque and `a[i] >= a[j]` with `i > j`, then `a[j]` is both older and smaller. Any window containing `a[j]` from now on also contains `a[i]`, which is at least as large. So `a[j]` is permanently useless: pop it.

What remains is a deque in decreasing order, whose **front is the window maximum**.

```
a = [1, 3, -1, -3, 5, 3, 6, 7],  k = 3

i=0 (1):  dq = [0]                          window not full
i=1 (3):  pop 0 (1<=3), dq = [1]            window not full
i=2 (-1): dq = [1,2]                        max = a[1] = 3
i=3 (-3): dq = [1,2,3]                      max = a[1] = 3
i=4 (5):  pop 3,2,1 (all <=5), dq = [4]     max = a[4] = 5
i=5 (3):  dq = [4,5]                        max = a[4] = 5
i=6 (6):  pop 5,4, dq = [6]                 max = a[6] = 6
i=7 (7):  pop 6, dq = [7]                   max = a[7] = 7

result: [3, 3, 5, 5, 6, 7]
```

### 4. C++ template

```cpp
vector<int> maxSlidingWindow(const vector<int>& a, int k) {
    deque<int> dq;                                      // INDICES, values decreasing
    vector<int> res;

    for (int i = 0; i < (int)a.size(); i++) {
        // 1. EXPIRE: drop the front if it has left the window
        if (!dq.empty() && dq.front() <= i - k) dq.pop_front();

        // 2. MAINTAIN: drop back elements that can never be the max again
        while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();

        // 3. PUSH
        dq.push_back(i);

        // 4. RECORD, once the window is full
        if (i >= k - 1) res.push_back(a[dq.front()]);
    }
    return res;
}
```

**The order of the four steps is fixed: expire, maintain, push, record.** Expiring after pushing can drop the element you just added. Recording before pushing misses the current element.

**Store indices, not values.** The expiry check `dq.front() <= i - k` needs the index. This is why you cannot get away with a deque of values.

For sliding window **minimum**, flip one comparison: `a[dq.back()] >= a[i]`.

### 5. Complexity

O(n) time: each index is pushed once and popped at most once, from either end. O(k) space: the deque never holds more than k indices.

Compare with the `multiset` approach at O(n log k). For k = 10⁵ that log factor is 17×, which matters on tight limits.

### 6. When to recognise it

Signals: "maximum/minimum of every window of size k", "sliding window" combined with an extremum rather than a sum or a count. Also appears as a subroutine in some DP optimisation problems ("sliding window maximum DP"), where the deque maintains the best transition candidate.

Contrast with the Module 2 sliding window: that one tracked a **sum or a count**, which updates in O(1) on both add and remove. A **maximum** does not: removing the current maximum leaves you needing the next one, which plain accumulators cannot recover. The deque exists exactly to solve that.

### 7. Must remember

1. Order: expire, maintain, push, record.
2. Store **indices**. Expiry needs them.
3. Expiry condition is `dq.front() <= i - k`.
4. Record only when `i >= k - 1`.
5. Decreasing deque → maximum. Increasing deque → minimum. Flip one comparison.
6. O(n) by the push-once, pop-once argument. O(k) space.
7. A `multiset` gives O(n log k) and is a perfectly acceptable first answer.

### 8. Common mistakes

- Wrong order of the four steps.
- Storing values, making expiry impossible.
- Off-by-one in the expiry check (`< i - k` instead of `<= i - k`).
- Recording from `i >= k` instead of `i >= k - 1`.
- Using a `queue` or `stack` and discovering you need both ends.
- Reporting O(n·k) because of the nested `while`.

### 9. Practice

- Sliding Window Maximum (LC 239, Hard)
- Shortest Subarray with Sum at Least K (LC 862, Hard) — optional; monotonic deque over prefix sums, and the reason it beats a plain sliding window is that the array has negatives

---

# PART C — Consolidation

## 7.10 When to use which structure

You asked for this explicitly, so it gets its own section.

```
Do I need the element I added MOST recently?
└─ YES -> STACK
          (matching, undo, DFS, expression evaluation)

Do I need the element I added FIRST?
└─ YES -> QUEUE
          (BFS, level order, scheduling in arrival order)

Do I need to add/remove at BOTH ends?
└─ YES -> DEQUE
          (monotonic deque, window problems)

Do I need "for each element, the nearest bigger/smaller one"?
└─ YES -> MONOTONIC STACK
          (next greater, histogram, stock span, trapping water)

Do I need the max/min of every window of fixed size k?
└─ YES -> MONOTONIC DEQUE

Do I need the largest/smallest element, with arbitrary insertion?
└─ YES -> PRIORITY QUEUE (Module 10)

Do I need the k-th, or sorted order, or nearest value?
└─ YES -> set / map / sorting (Modules 0, 5)
```

### The distinctions people confuse

| Confused pair | The difference |
|---|---|
| Stack vs queue | LIFO vs FIFO. Same code shape, completely different traversal (DFS vs BFS) |
| Monotonic stack vs monotonic deque | Stack: nearest greater/smaller. Deque: extremum of a **fixed-size window** |
| Monotonic deque vs priority queue | Deque: O(1), but only for a sliding window. Heap: O(log n), works for arbitrary insertion/removal patterns |
| Sliding window (Module 2) vs monotonic deque | Sums and counts update in O(1); maxima do not, which is why the deque exists |
| Stack vs recursion | The same thing. Converting one to the other is mechanical (Module 4.10) |

### Signal words

| Statement says | Reach for |
|---|---|
| "valid parentheses", "balanced", "matching" | Stack |
| "undo", "backtrack to previous" | Stack |
| "evaluate expression", "postfix" | Stack |
| "next greater / smaller", "previous greater / smaller" | Monotonic stack |
| "days until warmer", "stock span" | Monotonic stack |
| "largest rectangle", "maximal area under bars" | Monotonic stack |
| "collide", "annihilate", "collapse adjacent" | Stack |
| "remove k digits to make smallest" | Monotonic stack |
| "level by level", "shortest path unweighted" | Queue (Module 12) |
| "maximum of every window of size k" | Monotonic deque |
| "first in first out", "ring buffer" | Queue / circular queue |

---

## 7.11 Comparison tables

### The four containers

| | Insert | Remove | Peek | Iterate | Random access |
|---|---|---|---|---|---|
| `stack` | back O(1) | back O(1) | `top()` | No | No |
| `queue` | back O(1) | front O(1) | `front()`, `back()` | No | No |
| `deque` | both O(1) | both O(1) | `front()`, `back()` | Yes | Yes |
| `priority_queue` | O(log n) | O(log n) | `top()` | No | No |

### Monotonic stack variants, restated

| Want | Direction | Pop while top is | Answer read |
|---|---|---|---|
| Next greater | right → left | `<= a[i]` | `st.top()` after popping |
| Next smaller | right → left | `>= a[i]` | `st.top()` after popping |
| Previous greater | left → right | `<= a[i]` | `st.top()` after popping |
| Previous smaller | left → right | `>= a[i]` | `st.top()` after popping |

### Approaches to Sliding Window Maximum

| Approach | Time | Space | Verdict |
|---|---|---|---|
| Recompute each window | O(n·k) | O(1) | Too slow |
| `multiset` | O(n log k) | O(k) | Acceptable, easy to write |
| Monotonic deque | **O(n)** | O(k) | The expected answer |
| Heap with lazy deletion | O(n log n) | O(n) | Works, more code |

---

## 7.12 Must remember (consolidated)

1. `pop()` returns void on `stack`, `queue`, and `priority_queue`. Read first.
2. `top()` / `front()` on an empty container is undefined behaviour. Guard with `!empty() &&`.
3. Balanced parentheses ends with `return st.empty()`, not `return true`.
4. Min Stack uses `x <= mins.top()`, with `<=`, to handle duplicate minima.
5. Queue-from-two-stacks is amortised O(1): each element moves between stacks once. Only shift when `out` is empty.
6. **Monotonic stack: each element pushed once, popped at most once → O(n).**
7. Store **indices** in monotonic stacks and deques, never values.
8. Direction of iteration flips next/previous; direction of comparison flips greater/smaller.
9. Histogram needs the sentinel at `i == n` with height 0 to flush the stack.
10. Histogram width is `i - left - 1`, with `left` read after popping.
11. Maximal Rectangle = histogram algorithm run once per row.
12. Monotonic deque order: expire, maintain, push, record.
13. Expiry condition is `dq.front() <= i - k`; record when `i >= k - 1`.
14. Decreasing deque gives the maximum; increasing gives the minimum.
15. Circular queue tracks a `count` to distinguish full from empty.
16. A `vector` works as a stack and is faster than `std::stack`.

---

## 7.13 Common mistakes (consolidated)

**Runtime error**
- `top()` or `front()` on an empty container.
- Missing `!st.empty() &&` in a monotonic-stack while condition.
- `int x = st.pop();`

**Wrong answer**
- `return true` instead of `return st.empty()` in parentheses matching.
- `<` instead of `<=` in Min Stack, breaking on duplicate minima.
- Operand order reversed in postfix evaluation (invisible for `+` and `*`).
- Missing the histogram sentinel, so an increasing histogram returns 0.
- Reading `left` before popping in the histogram loop.
- Wrong order of the four monotonic-deque steps.
- Off-by-one in deque expiry or in the record condition.
- Wrong comparison direction, getting next-smaller when you wanted next-greater.

**Time limit exceeded**
- Not recognising the monotonic stack pattern and writing O(n²).
- Shifting on every call in queue-from-two-stacks.
- Recomputing the window maximum from scratch.

**Analysis errors**
- Calling a monotonic stack or deque O(n²) because of the nested `while`.
- Claiming O(1) space for a monotonic stack; it is O(n).

---

## 7.14 Problem set

Fourteen core problems. The monotonic stack is over-represented on purpose.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Valid Parentheses (LC 20) | Easy | Stack as unresolved memory | `return st.empty()`, and the three failure modes |
| Min Stack (LC 155) | Medium | Auxiliary stack | The `<=` that handles duplicate minima |
| Implement Queue using Stacks (LC 232) | Easy | Two-stack amortisation | Why it is amortised O(1) |

### Level 2 — Pattern (5)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Next Greater Element I (LC 496) | Easy | Monotonic stack | The template in isolation |
| Daily Temperatures (LC 739) | Medium | Monotonic stack | The distance variant; one line different |
| Next Greater Element II (LC 503) | Medium | Circular monotonic stack | The `2n` with `i % n` trick |
| Evaluate Reverse Polish Notation (LC 150) | Medium | Stack evaluation | Operand pop order |
| Design Circular Queue (LC 622) | Medium | Ring buffer | Why you track `count` |

### Level 3 — Interview (4)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Asteroid Collision (LC 735) | Medium | Stack with annihilation | A non-monotonic stack use that still reads as "resolve against the top" |
| Remove K Digits (LC 402) | Medium | Monotonic stack (greedy) | Building the smallest result by popping larger digits |
| **Largest Rectangle in Histogram (LC 84)** | Hard | Monotonic stack + geometry | Sentinel, width formula, the hardest standard application |
| **Sliding Window Maximum (LC 239)** | Hard | Monotonic deque | The four steps, in order |

### Level 4 — Advanced (2, optional)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Maximal Rectangle (LC 85) | Hard | Histogram per row | 2D reduced to n instances of 1D |
| Sum of Subarray Minimums (LC 907) | Medium | Monotonic stack + counting | Where `<` vs `<=` decides double counting |

**LC 84 and LC 239 are the two to over-prepare.** They are the standard hard questions from this module, they appear regularly, and both are unreachable if you have not internalised the pattern. Solve LC 496 and 739 first so the template is automatic, then attack them.

---

## Exit checklist

```
[ ] I guard every top()/front() with !empty()
[ ] I know pop() returns void
[ ] Valid Parentheses ends with return st.empty()
[ ] I know why Min Stack needs <= and not <
[ ] I can explain why queue-from-two-stacks is amortised O(1)
[ ] I can write the monotonic stack template from memory
[ ] I store indices, not values
[ ] I know the 2x2: direction -> next/previous, comparison -> greater/smaller
[ ] I can say "pushed once, popped once, therefore O(n)" without hesitating
[ ] I know both monotonic stack formulations (right-to-left and left-to-right)
[ ] I can write Largest Rectangle in Histogram with the sentinel
[ ] I can derive the width formula i - left - 1
[ ] I know Maximal Rectangle is the histogram run per row
[ ] I can write the monotonic deque with the four steps in order
[ ] I know why the deque stores indices
[ ] I can explain why sliding window sums are easy but maxima need a deque
[ ] I can pick between stack, queue, deque, monotonic stack, monotonic deque on sight
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 8"** for Backtracking (10–12 hours, Tier 2). It picks up exactly where Module 4 left off: recursion plus an explicit undo step.

The module covers the choose-explore-unchoose template that solves subsets, permutations, and combination sum with one shape, the duplicate-handling rules that cause most wrong answers, pruning (which is what separates a solution that passes from one that times out), and the constraint-satisfaction problems — N-Queens, Sudoku, Word Search — that are the standard hard questions.

Alternatively, if you would rather keep momentum on the Tier 1 path, say **"Start Phase 9"** and take Trees next; backtracking is not a prerequisite for it.
