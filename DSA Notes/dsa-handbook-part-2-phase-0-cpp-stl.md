# DSA Placement Handbook (C++) — Part 2
# Phase 0: C++ Essentials and STL for DSA

**Module 0 · 8–10 hours · Tier 1 · No prerequisites**

---

## How this module is formatted

Your 11-section note format is built for *techniques* (sliding window, Dijkstra). Applied to "what is an if statement" it would waste your time. So this module does two things:

- **Full 11-section treatment** for the pieces that actually cause bugs and lost interview time: parameter passing, `vector`, `string`, `priority_queue`, `map` vs `unordered_map`, `set`, and custom comparators.
- **Compressed reference blocks** for syntax you will recognise on sight (loops, conditionals, I/O). Read once, move on.

Everything from Module 1 onward uses the full format throughout.

**What this module is not:** a C++ course. Nothing here about inheritance, virtual functions, templates you write yourself, smart pointers, move semantics, exceptions, or the standard library beyond what DSA uses. If you find yourself curious about `std::optional`, close the tab and come back.

**Exit condition:** you can write any of the templates in Section E from memory, and you can predict the complexity of any STL call you make.

---

## 0.0 The file you type every time

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // solve here

    return 0;
}
```

Three notes:

`#include <bits/stdc++.h>` pulls in the whole standard library. It is a GCC extension, not standard C++. It works on Codeforces, LeetCode, GeeksforGeeks, CodeChef, and almost every OA platform. It does not work on MSVC or macOS Clang by default. If a judge rejects it, include `<iostream> <vector> <algorithm> <string> <map> <set> <queue> <stack> <climits>` instead.

`using namespace std;` is bad practice in production code and completely fine in a 60-line interview solution. Do not let anyone waste your time arguing about it.

The two `ios_base` lines make `cin`/`cout` roughly as fast as `scanf`/`printf`. On problems with 10⁵+ input values this is the difference between passing and a time-limit exceeded verdict. **Once you add these, never mix `cin` with `scanf` in the same program.** The synchronisation you just turned off is exactly what made mixing safe.

On LeetCode you do not write `main` at all, you fill in a method. The fast-I/O lines are irrelevant there.

---

# Section A — Language essentials

## A1. Types, overflow, and limits

### What is it?

C++ integers are fixed-width. `int` is 32 bits, `long long` is 64 bits. When a computation exceeds the width, it silently wraps around instead of erroring. This is the single most common source of "my logic is right but the answer is wrong" in coding rounds.

### The numbers you must know

| Type | Bits | Max value | Rough magnitude |
|---|---|---|---|
| `int` | 32 | 2,147,483,647 | ~2 × 10⁹ |
| `long long` | 64 | 9,223,372,036,854,775,807 | ~9 × 10¹⁸ |
| `unsigned int` | 32 | 4,294,967,295 | ~4 × 10⁹ |
| `double` | 64 | exact integers up to 2⁵³ | ~9 × 10¹⁵ |

`INT_MAX`, `INT_MIN`, `LLONG_MAX`, `LLONG_MIN` live in `<climits>`.

### When do I need `long long`?

Reach for it the moment any of these is true:

- You are summing an array. `n = 10⁵` elements each up to `10⁹` gives `10¹⁴`, which overflows `int`.
- You are multiplying two values that can each reach `10⁵` or more.
- The problem statement says answers can be large, or constraints mention `10⁹` anywhere.
- You are computing `a * b` where `a` and `b` are `int` and the result feeds a comparison.

The trap: **the multiplication happens in `int` before the assignment.**

```cpp
int a = 100000, b = 100000;
long long bad  = a * b;              // overflow: computed as int, then widened
long long good = (long long)a * b;   // correct: one operand promoted first
```

### Core idea

The type of an expression is decided by its operands, not by where the result is stored. Cast on the left of the operation, not at the assignment.

### Must remember

1. `1 << 31` is undefined behaviour for `int`. Use `1LL << 31` whenever the shift can reach 31 or beyond.
2. Integer division truncates toward zero: `-7 / 2 == -3`, not `-4`.
3. `%` follows division, so `-7 % 2 == -1` in C++. In Python it is `1`. If a problem needs a non-negative remainder, write `((x % m) + m) % m`.
4. `INT_MAX + 1` overflows. For "infinity" sentinels use `1e9` (fits comfortably in `int`) or `LLONG_MAX / 2` (safe to add to).
5. `.size()` on any STL container returns an **unsigned** type. `v.size() - 1` on an empty vector is not `-1`, it is about 1.8 × 10¹⁹. This is a real crash, not a theoretical one.
6. `double` cannot hold all 64-bit integers exactly. Never use `double` for exact integer arithmetic.

### Common mistakes

- `int mid = (lo + hi) / 2;` in binary search. When `lo` and `hi` are near `INT_MAX` this overflows. Always `lo + (hi - lo) / 2`.
- `for (int i = 0; i < v.size() - 1; i++)` with an empty `v`. Fix: `for (int i = 0; i + 1 < (int)v.size(); i++)`.
- Comparing signed and unsigned: `if (i < v.size())` where `i` is a negative `int` compares as a huge unsigned number. Cast: `(int)v.size()`.
- Using `int` for a prefix-sum array over large values.

---

## A2. Input and output

### The three patterns you need

```cpp
// 1. Fixed count, known in advance
int n;  cin >> n;
vector<int> v(n);
for (int i = 0; i < n; i++) cin >> v[i];

// 2. Read until end of input
int x;
while (cin >> x) { /* ... */ }

// 3. A whole line, spaces included
string line;
getline(cin, line);
```

### The `getline` trap

```cpp
int n;
cin >> n;                 // leaves the newline sitting in the buffer
string line;
getline(cin, line);       // reads that leftover newline: line is empty
```

Fix by consuming the newline first:

```cpp
cin >> n;
cin.ignore();             // discards one character (the newline)
getline(cin, line);
```

### Output

```cpp
cout << x << "\n";        // prefer "\n" over endl
```

`endl` flushes the output buffer on every call. Inside a loop printing 10⁵ lines that is measurably slow. Use `"\n"` and let the buffer flush at program end.

For floating-point output with fixed precision:

```cpp
cout << fixed << setprecision(6) << ans << "\n";
```

### Must remember

1. `cin >> s` for a `string` stops at whitespace. It reads one word, not one line.
2. `cin >> c` for a `char` skips whitespace. If you need to read spaces as characters, use `getline` or `cin.get(c)`.
3. On LeetCode there is no input parsing at all. All of this matters for OA platforms, Codeforces, and GeeksforGeeks.

---

## A3. Control flow (compressed)

Nothing here should surprise you. Skim and move on.

```cpp
if (cond) { } else if (cond2) { } else { }

for (int i = 0; i < n; i++) { }
for (int i = n - 1; i >= 0; i--) { }
while (cond) { }
do { } while (cond);

for (int x : v) { }              // copy of each element
for (int& x : v) x *= 2;         // modifies v
for (const auto& x : v) { }      // no copy, read-only: use this by default

switch (x) {
    case 1: /* ... */ break;
    default: break;
}
```

`break` exits the innermost loop. `continue` skips to the next iteration. There is no labelled break in C++; to escape nested loops either use a flag, a `goto` (legal, occasionally the cleanest option), or extract the loops into a function and `return`.

**The one real trap:** the range-for `for (int x : v)` copies each element. For `vector<string>` or `vector<vector<int>>` that copy is expensive and, more importantly, writes to `x` do not affect `v`. Default to `const auto&` for reading and `auto&` for writing.

---

## A4. Functions and parameter passing

### 1. What is it?

How a function receives its arguments. C++ gives you three choices: by value (a copy), by reference (an alias to the caller's object), and by const reference (a read-only alias).

### 2. Why do we need it?

Because passing a `vector<int>` of 10⁵ elements by value copies 10⁵ integers on **every call**. Inside a recursion that runs 10⁵ times, you have just turned an O(n) algorithm into O(n²) without writing a single extra loop. This is the most common accidental-TLE in all of DSA, and it is invisible in the code unless you know to look for it.

### 3. Core idea

```cpp
void byValue(vector<int> v);        // copies. Caller's vector unchanged.
void byRef(vector<int>& v);         // alias. Modifications visible to caller.
void byConstRef(const vector<int>& v); // alias, read-only. No copy, no modification.
```

An `int`, `char`, `bool`, or pointer is cheap to copy. Pass those by value. Anything that owns memory (`vector`, `string`, `map`, `set`, a large `struct`) should be passed by reference or const reference.

### 4. When should I use which?

| Situation | Use |
|---|---|
| Small built-in type (`int`, `char`, `double`, pointer) | by value |
| Container you only read | `const T&` |
| Container you modify, or shared recursion state | `T&` |
| A `TreeNode*` or `ListNode*` | by value (it is just a pointer) |

### 5. How to recognise the problem

You wrote a recursive function whose parameter list contains a `vector`, `string`, `map`, or `set` without an `&`. That is the signal. Check every recursive signature you write.

### 6. C++ template

```cpp
// Shared state passed by reference, per-call state by value
void solve(int index, const vector<int>& nums,
           vector<int>& current, vector<vector<int>>& result) {
    if (index == (int)nums.size()) {
        result.push_back(current);      // copy is intentional here
        return;
    }
    solve(index + 1, nums, current, result);
    current.push_back(nums[index]);
    solve(index + 1, nums, current, result);
    current.pop_back();                 // undo
}
```

`nums` is read-only input, so `const&`. `current` and `result` are shared mutable state, so `&`. `index` is an `int`, so by value. This exact signature shape reappears in every backtracking problem in Module 8.

### 7. Example

```cpp
int sumSlow(vector<int> v) { /* copies n ints on entry */ }
int sumFast(const vector<int>& v) { /* copies nothing */ }
```

Called 10⁵ times with `n = 10⁵`, the first is 10¹⁰ operations and the second is 10⁵.

### 8. Complexity

Pass by value: O(size of object) time and space, per call.
Pass by reference or const reference: O(1) time and space, per call.

### 9. Must remember

1. Missing `&` on a recursive container parameter is the most expensive one-character bug in DSA.
2. Returning a local `vector` by value is **fine**. The compiler moves it rather than copying (return value optimisation). Do not contort your code to avoid it.
3. `const T&` also lets the function accept temporaries: `f({1,2,3})` compiles with `const vector<int>&` but not with `vector<int>&`.
4. A reference must be initialised when declared and can never be reseated. `int& r = a;` then `r = b;` assigns `b`'s value into `a`, it does not rebind `r`.
5. Default arguments go in the declaration only, not the definition, if you split them.
6. A function that modifies its argument should say so by taking `T&`. An interviewer reading `void f(vector<int> v)` will assume you did not mean to copy.

### 10. Common mistakes

- `void dfs(vector<vector<int>> adj, ...)` inside a graph traversal. Silent O(V × E) blowup.
- Passing by value and then wondering why the caller's array is unchanged.
- Taking `const vector<int>&` and then trying to `push_back` to it (compile error, at least this one is caught).
- Returning a reference to a local variable. Dangling reference, undefined behaviour. Return by value instead.

### 11. Practice

These are drills, not LeetCode problems. Write each in under 3 minutes.

1. Write `void addOne(vector<int>& v)` that increments every element, and verify the caller sees it.
2. Write the same with `vector<int> v` and observe that it does not.
3. Write a recursive `int sum(const vector<int>& v, int i)` that sums from index `i` to the end.
4. Write `void swapTwo(int& a, int& b)` without a temp variable using a reference, then with.

---

## A5. Pointers and references (the DSA subset)

### 1. What is it?

A pointer holds a memory address. A reference is an alias for an existing object. For DSA you need exactly one use case for each: pointers for linked structures (linked lists, trees, tries), references for avoiding copies.

### 2. Why do we need it?

Because a linked list node has to point to another node, and a tree node has to point to its children. There is no way to express "the next one" without an address. Everything else people teach about pointers (arithmetic, arrays decaying, `void*`, manual `new`/`delete` in loops) is irrelevant to interview DSA.

### 3. Core idea

```cpp
int a = 5;
int* p = &a;     // p holds the address of a
cout << *p;      // 5   dereference: "the value at that address"
*p = 7;          // a is now 7

int& r = a;      // r IS a, another name for it
r = 9;           // a is now 9
```

A pointer can be null and can be reassigned. A reference can be neither.

### 4. When should I use it?

| You need | Use |
|---|---|
| Next node in a list, child of a tree node | pointer (`ListNode*`, `TreeNode*`) |
| Avoid copying a container into a function | reference |
| An "empty / does not exist" value | pointer, set to `nullptr` |
| Modify a caller's variable | reference |

You will essentially never write `new` and `delete` yourself in an interview, except to build a `TreeNode` or a `TrieNode`. Memory leaks in a 40-minute interview are not a scored criterion, and most interviewers will not raise them. Do not let it distract you.

### 5. The `->` operator

```cpp
node->val          // shorthand for (*node).val
```

That is the entire syntax you need. `node->next->next` walks two steps forward.

### 6. C++ template

```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};
```

Memorise both. You will retype them constantly in Modules 6 and 9.

### 7. Example

```cpp
ListNode* head = new ListNode(1);
head->next = new ListNode(2);
head->next->next = new ListNode(3);

for (ListNode* cur = head; cur != nullptr; cur = cur->next)
    cout << cur->val << " ";        // 1 2 3
```

### 8. Complexity

Dereferencing is O(1). Allocation with `new` is O(1) amortised but with a real constant cost, which is why array-backed structures beat pointer-backed ones in practice.

### 9. Must remember

1. `nullptr`, not `NULL`, not `0`. Same behaviour, but `nullptr` is type-safe and what an interviewer expects in modern C++.
2. **Always null-check before dereferencing.** `if (node != nullptr)` or just `if (node)`. Dereferencing null is a segfault, the most common runtime error in linked-list and tree problems.
3. `ListNode* cur = head;` copies the pointer, not the list. Moving `cur` does not move `head`. This is exactly what makes traversal safe.
4. To modify the *pointer itself* inside a function, you need `ListNode*&` (a reference to a pointer) or you must return the new pointer. Returning is cleaner and what most interview solutions do.
5. Stack memory (local variables, recursion frames) is limited, typically 1 MB to 8 MB. Heap memory (`new`, and the internals of every STL container) is limited by system RAM. This is why 10⁶-deep recursion crashes but a 10⁶-element vector does not.
6. A struct declared inside a function cannot be used as a template argument in older standards. Declare node structs at file scope.

### 10. Common mistakes

- Dereferencing a node without checking for null, especially `cur->next->val` when `cur->next` might be null.
- Losing the head pointer by advancing it during traversal, then being unable to return the list.
- Mixing up `node->next = x` (relink) with `node = x` (just move the local pointer, list unchanged).
- Using `*` and `&` from memory rather than reading the declaration. If confused, read right to left: `int* p` is "p is a pointer to int".

### 11. Practice

1. Build a 5-node list by hand with `new`, print it forward.
2. Write a loop that finds the last node.
3. Write a function that takes `ListNode* head` and returns the length.
4. Deliberately dereference a null pointer once, in a scratch file, so you recognise the crash when it happens for real.

---

## A6. Structs and classes for DSA

You need three uses. That is all.

**1. Node types.** Shown above. Use `struct` (members public by default) rather than `class`. Less typing, no reason for encapsulation in a 40-line solution.

**2. Grouping values.** When `pair` is not enough:

```cpp
struct Edge {
    int from, to, weight;
};
vector<Edge> edges;
edges.push_back({1, 2, 5});     // aggregate initialisation
```

**3. Comparator objects.** Covered in full in Section C4.

**Constructor shorthand** worth knowing, because it makes node creation a one-liner:

```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};
```

The `: val(x), left(nullptr)` part is an initialiser list. It assigns members before the constructor body runs.

**What you can skip entirely for placements:** inheritance, virtual functions, polymorphism, operator overloading beyond comparison, copy constructors, rule of three/five, friend functions. Those belong to the OOP round, which is a separate topic with a separate answer, not to DSA.

**One exception.** If you want a `set` or `map` keyed by your own struct, you need a way to order it. Two options:

```cpp
// Option A: operator< inside the struct
struct P {
    int x, y;
    bool operator<(const P& other) const {
        if (x != other.x) return x < other.x;
        return y < other.y;
    }
};
set<P> s;   // now works

// Option B: external comparator (Section C4)
```

The `const` after the parameter list is required. Forgetting it produces a compiler error that is genuinely hard to read.

---

## A7. Recursion mechanics (preview)

Module 4 teaches recursion properly. Here is only the machine-level piece, because it explains a crash you will hit before then.

Every function call pushes a **stack frame** holding the parameters, local variables, and return address. The frame pops when the function returns. Recursion depth `d` means `d` frames alive at once.

```
factorial(4)
  factorial(3)
    factorial(2)
      factorial(1)   <- base case, starts returning
```

The call stack is typically 1 MB to 8 MB. A frame with a few `int`s is maybe 50 to 100 bytes, so depth of ~10⁵ is usually survivable and ~10⁶ usually is not. A frame holding a `vector` by value is far larger, which is the second reason (after the copying cost) that A4 matters.

**Stack overflow presents as a segfault with no useful message.** If a recursive solution crashes on a large test and works on small ones, suspect depth before you suspect logic. The fix is either converting to an iterative form with an explicit `stack<>`, or memoising so the recursion tree collapses.

Minimum anatomy:

```cpp
int fact(int n) {
    if (n <= 1) return 1;        // base case: stops the recursion
    return n * fact(n - 1);      // recursive case: moves toward the base
}
```

Every recursive function needs both. A missing or unreachable base case is infinite recursion, which is a stack overflow, which is a segfault.

---

# Section B — STL containers

## B1. vector

### 1. What is it?

A dynamic array. Contiguous memory, random access by index, grows automatically when you push past its capacity. It is the default container for essentially every DSA problem.

### 2. Why do we need it?

Raw C arrays need a compile-time size, do not know their own length, and cannot grow. `vector` fixes all three at zero meaningful cost. There is no situation in interview DSA where a raw array is the better choice.

### 3. Core idea

The vector keeps a block of memory with some spare capacity. `push_back` writes into the spare space in O(1). When the space runs out it allocates a block twice as large and copies everything over, which is O(n). Because doublings are rare, the **amortised** cost of `push_back` is O(1). Module 1 covers why amortised analysis is valid.

### 4. When should I use it?

Always, unless you specifically need one of: O(1) insertion at the front (use `deque`), sorted order maintained under insertion (use `set`), or key-value lookup (use `map`).

### 5. Declaration and initialisation

```cpp
vector<int> a;                       // empty
vector<int> b(n);                    // n zeros
vector<int> c(n, -1);                // n copies of -1
vector<int> d = {1, 2, 3};           // literal
vector<int> e(d);                    // copy of d
vector<int> f(d.begin() + 1, d.end()); // {2, 3}

vector<vector<int>> grid(n, vector<int>(m, 0));   // n x m matrix of zeros
vector<vector<int>> adj(n);                        // n empty adjacency lists
```

Memorise the 2D form. You will write it in every graph and grid problem.

### 6. C++ template: operations you actually use

```cpp
v.push_back(x);       // append                  O(1) amortised
v.pop_back();         // remove last             O(1)
v.back();             // last element            O(1)
v.front();            // first element           O(1)
v[i];                 // access, no bounds check O(1)
v.size();             // count (unsigned!)       O(1)
v.empty();            // size == 0               O(1)
v.clear();            // remove all              O(n)
v.resize(k);          // grow/shrink to k        O(|k - n|)
v.assign(n, val);     // refill with n copies    O(n)

sort(v.begin(), v.end());                        // O(n log n)
reverse(v.begin(), v.end());                     // O(n)
v.erase(v.begin() + i);                          // O(n)  shifts everything after
v.insert(v.begin() + i, x);                      // O(n)
```

### 7. Example

```cpp
vector<int> v = {5, 2, 8, 1};
sort(v.begin(), v.end());          // 1 2 5 8
v.push_back(3);                    // 1 2 5 8 3
cout << v.back();                  // 3
cout << v.size();                  // 5
```

### 8. Complexity

| Operation | Time |
|---|---|
| `v[i]`, `back`, `front`, `size` | O(1) |
| `push_back`, `pop_back` | O(1) amortised |
| `insert`, `erase` at position i | O(n − i) |
| Search for a value (unsorted) | O(n) |
| `sort` | O(n log n) |

Space: O(n), contiguous. Capacity may exceed size.

### 9. Must remember

1. `v[i]` does **not** bounds check. Out-of-range access is undefined behaviour: sometimes a crash, sometimes silent garbage. `v.at(i)` throws instead, but nobody uses it in contests.
2. `v.size()` is unsigned. See A1, mistake 2.
3. `erase` and `insert` in the middle are O(n). A loop that erases from the middle is O(n²). If you are filtering, build a new vector or use the erase-remove idiom:
   ```cpp
   v.erase(remove(v.begin(), v.end(), x), v.end());   // O(n) total
   ```
4. `push_back` may reallocate, which **invalidates all iterators, pointers, and references** into the vector. Never hold a reference to an element across a `push_back`.
5. `vector<bool>` is a special-cased bit-packed type, not a normal vector. You cannot take a reference to its elements. If anything behaves strangely, switch to `vector<char>` or `vector<int>`.
6. Two vectors compare with `==` element-wise, and with `<` lexicographically. This makes `sort` on `vector<vector<int>>` work out of the box.
7. `emplace_back(args...)` constructs in place instead of constructing then copying. For `vector<pair<int,int>>` it lets you write `v.emplace_back(1, 2)` instead of `v.push_back({1, 2})`. Minor, but cleaner.

### 10. Common mistakes

- Modifying a vector while iterating over it with a range-for. Undefined behaviour if reallocation occurs.
- `for (int i = 0; i <= v.size(); i++)`. Off by one, reads past the end.
- Passing a large vector by value into a recursive function (A4).
- Building a 2D vector as `vector<vector<int>> g(n)` and then indexing `g[i][j]` without ever sizing the inner vectors. Each inner vector is empty.
- Assuming `v.clear()` frees memory. It sets size to 0 but keeps capacity.

### 11. Practice

1. Build an n × m grid of zeros, fill it with `i * m + j`, print it.
2. Given `vector<int>`, remove all even numbers in O(n) using erase-remove.
3. Reverse a vector in place with two pointers, without `reverse`.
4. Write a function that returns the max of a vector, taking it by const reference.

---

## B2. pair and tuple (compressed)

```cpp
pair<int, int> p = {3, 5};
p.first;  p.second;

make_pair(3, 5);          // older style, {3, 5} is fine
vector<pair<int,int>> vp;
vp.push_back({1, 2});

// Structured bindings (C++17), very readable:
auto [a, b] = p;
for (auto& [key, value] : someMap) { }
```

**The key fact:** `pair` has a built-in `<` that compares `first`, then breaks ties with `second`. So `sort` on a `vector<pair<int,int>>` sorts by first ascending, then second ascending, with no comparator needed. This shows up constantly: intervals, edges with weights, (value, index) pairs.

`tuple<int,int,int>` exists for three values. Access is `get<0>(t)`, which is ugly. For three or more fields prefer a small `struct` with named members. Interviewers read your code, and `e.weight` beats `get<2>(e)`.

---

## B3. string

### 1. What is it?

A dynamic array of characters with string-specific operations bolted on. Mentally, it is `vector<char>` plus `substr`, `find`, and `+`.

### 2. Why do we need it?

String problems are roughly a third of array-and-string interview questions. Being fluent with the operations saves minutes you do not have.

### 3. Core idea

Every technique that works on `vector<int>` (two pointers, sliding window, prefix sums, frequency counting) works unchanged on `string`. Treat it as an array of small integers and most string problems stop being a separate category.

### 4. When should I use it?

For text input. Also, occasionally, as a cheap way to hash a small structure: converting a character-count array into a string key is a standard trick for grouping anagrams (Module 3).

### 5. Operations

```cpp
string s = "hello";
s.size(); s.length();       // identical, both O(1)
s[i];                       // char at i
s.push_back('x');  s += "yz";
s.substr(i);                // from i to end          O(n)
s.substr(i, len);           // len characters from i  O(len)
s.find("ll");               // first index, or string::npos if absent
s.empty();  s.back();  s.pop_back();

reverse(s.begin(), s.end());
sort(s.begin(), s.end());   // sorts characters: standard anagram key

stoi(s);  stoll(s);  to_string(42);

// char helpers, from <cctype>
isalpha(c); isdigit(c); isalnum(c); tolower(c); toupper(c);
```

### 6. Character arithmetic

```cpp
c - '0'          // digit char to int:  '7' - '0' == 7
c - 'a'          // lowercase to 0..25 index
'a' + i          // index back to char (cast to char if assigning)
```

The `c - 'a'` idiom is how you index a 26-element frequency array. You will use it in every anagram and character-count problem:

```cpp
vector<int> freq(26, 0);
for (char c : s) freq[c - 'a']++;
```

### 7. Example

```cpp
string s = "racecar";
string t = s;
reverse(t.begin(), t.end());
bool isPal = (s == t);        // true
```

(That is the O(n) space version. Module 2 does it with two pointers in O(1) space.)

### 8. Complexity

| Operation | Time |
|---|---|
| `s[i]`, `size`, `back` | O(1) |
| `push_back`, `+=` single char | O(1) amortised |
| `s + t` (creates new string) | O(\|s\| + \|t\|) |
| `substr(i, len)` | O(len) |
| `find` | O(n × m) worst case |
| Comparison `==`, `<` | O(n) |

### 9. Must remember

1. **`substr` allocates and copies.** Calling it inside a loop is a hidden O(n²). Prefer carrying `(left, right)` indices.
2. `s.find(t)` returns `string::npos` (a huge unsigned value) when absent, not `-1`. Check with `if (s.find(t) != string::npos)`.
3. Building a string with `s = s + c` in a loop is O(n²) because each `+` makes a new string. Use `s += c` or `s.push_back(c)`, both amortised O(1).
4. Comparing strings with `==` is O(n), not O(1). Inside a nested loop that is an extra factor you may not have budgeted for.
5. `sort(s.begin(), s.end())` gives you a canonical anagram key in O(n log n). A 26-count array gives the same key in O(n) when you need the speed.
6. `string::npos` is unsigned. Never compare it against a signed variable without a cast.

### 10. Common mistakes

- Comparing `s.find(t) >= 0`, which is always true because the return type is unsigned.
- Using `substr` to generate all substrings, giving O(n³) when O(n²) was intended.
- Forgetting that `s[i]` is a `char`, so `s[i] * 2` is arithmetic on its ASCII code.
- Assuming characters are lowercase. Check the constraints; mixed case and non-letters break a 26-element frequency array. Use 128 or 256 entries when unsure.

### 11. Practice

1. Count the frequency of every character in a string using a 26-element array.
2. Check palindrome with two pointers, no extra string.
3. Reverse the words in a sentence.
4. Convert `"1234"` to an integer without `stoi`.

---

## B4. stack, queue, deque

These three are grouped because the syntax is trivial. Their *use* is Module 7. Here you only need the API.

### stack (LIFO)

```cpp
stack<int> st;
st.push(x);
st.pop();        // removes top, returns NOTHING
st.top();        // reads top
st.empty();  st.size();
```

### queue (FIFO)

```cpp
queue<int> q;
q.push(x);       // enqueue at back
q.pop();         // dequeue from front, returns NOTHING
q.front();       // read front
q.back();        // read back
q.empty();  q.size();
```

### deque (both ends)

```cpp
deque<int> dq;
dq.push_back(x);   dq.push_front(x);
dq.pop_back();     dq.pop_front();
dq.front();  dq.back();
dq[i];             // random access works, unlike stack/queue
```

### Comparison

| | Insert/remove front | Insert/remove back | Random access | Use for |
|---|---|---|---|---|
| `stack` | no | O(1) | no | DFS, monotonic stack, parentheses, undo |
| `queue` | O(1) remove | O(1) insert | no | BFS, level order |
| `deque` | O(1) | O(1) | O(1) | monotonic queue, sliding window max |
| `vector` | O(n) | O(1) | O(1) | everything else |

### Must remember

1. **`pop()` returns `void` in all three.** You must read with `top()` or `front()` *before* popping. Writing `int x = st.pop();` is a compile error; forgetting to read before popping is a logic bug.
2. **Calling `top()` or `front()` on an empty container is undefined behaviour**, not an exception. Always guard with `while (!st.empty())`.
3. `stack` and `queue` are *adapters*. They wrap another container (`deque` by default) and deliberately expose a restricted interface. You cannot iterate over them. If you need to inspect the middle, you picked the wrong container.
4. `deque` is not contiguous in memory. It is a sequence of fixed-size blocks. Random access works but is slightly slower than `vector`, and you cannot pass `&dq[0]` to something expecting a C array.
5. A `vector` used with `push_back`/`pop_back`/`back()` is a perfectly good stack and is faster. Many competitive programmers never use `stack<>` at all. Either is fine in an interview.

### Common mistakes

- Popping an empty stack after a loop condition that did not check `empty()`.
- Using `queue` for DFS or `stack` for BFS. They are interchangeable in code shape and produce completely different traversals.
- Reading `st.top()` after `st.pop()` and getting the wrong element.

---

## B5. priority_queue (heap)

### 1. What is it?

A binary heap wrapped in a container interface. It gives you the largest element (by default) in O(1) and lets you insert or remove in O(log n).

### 2. Why do we need it?

Because for "give me the best element repeatedly while the set keeps changing", sorting is wrong. Sorting costs O(n log n) up front and breaks the moment you insert. A heap keeps the invariant cheaply under insertion. This powers Top-K, merge-k-sorted, streaming median, scheduling, and Dijkstra.

### 3. Core idea

A heap is a complete binary tree stored in an array, where every parent beats its children. It does **not** keep the whole set sorted. It only guarantees the root is the extreme. That weaker promise is why it is cheaper than sorting.

### 4. When should I use it?

Reach for a heap when the problem says "k-th largest", "top k", "merge k sorted", "median of a stream", "always take the smallest remaining", or "schedule by earliest finishing". Module 10 covers this properly.

### 5. Declarations (memorise these two lines)

```cpp
priority_queue<int> maxHeap;                                   // largest on top
priority_queue<int, vector<int>, greater<int>> minHeap;        // smallest on top
```

The second one is the single most-forgotten piece of syntax in C++ DSA. Write it out twenty times. The three template arguments are: element type, underlying container, comparator.

### 6. C++ template

```cpp
priority_queue<int> pq;
pq.push(x);       // O(log n)
pq.top();         // O(1)   read the extreme
pq.pop();         // O(log n)  remove the extreme, returns nothing
pq.size();  pq.empty();

// Heap of pairs: sorts by first, then second
priority_queue<pair<int,int>> pqp;

// Min-heap of pairs (the Dijkstra shape)
priority_queue<pair<int,int>, vector<pair<int,int>>, greater<pair<int,int>>> pqd;
```

### 7. Example: k-th largest with a min-heap of size k

```cpp
int kthLargest(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> pq;   // min-heap
    for (int x : nums) {
        pq.push(x);
        if ((int)pq.size() > k) pq.pop();   // drop the smallest
    }
    return pq.top();
}
```

The heap holds the k largest seen so far, with the smallest of them on top. O(n log k) time, O(k) space, better than sorting when k is small.

### 8. Complexity

| Operation | Time |
|---|---|
| `push` | O(log n) |
| `pop` | O(log n) |
| `top` | O(1) |
| Build from a vector at construction | O(n) |

Space O(n).

```cpp
priority_queue<int> pq(v.begin(), v.end());   // O(n), faster than n pushes
```

### 9. Must remember

1. `greater<int>` gives a **min**-heap. It reads backwards from intuition. The comparator describes the ordering, and the top is the maximum *under that ordering*.
2. A custom comparator for `priority_queue` is **inverted** relative to `sort`. If `cmp(a, b)` returns true, `a` has **lower** priority than `b`. So a comparator that looks like a "sort ascending" comparator produces a max-heap.
3. `pop()` returns void. Read `top()` first.
4. You cannot iterate a `priority_queue`, search it, or update an arbitrary element. If you need to decrease a key (as in textbook Dijkstra), the standard workaround is to push a duplicate and skip stale entries when you pop. Module 12 shows the exact pattern.
5. Constructing from a range is O(n). Pushing n times is O(n log n). Use the constructor when you have the data up front.
6. `priority_queue<pair<int,int>>` compares `first` first. To order by the second field you need a comparator.

### 10. Common mistakes

- Writing `priority_queue<int, greater<int>>` (two arguments). The container type is mandatory in the middle.
- Getting a max-heap when you wanted a min-heap, then patching it by negating all values. That works, and is a legitimate trick, but do not do it by accident.
- Writing a comparator by copying your `sort` comparator, and getting the opposite heap.
- Calling `top()` on an empty heap after popping in a loop.

### 11. Practice

1. Write both declarations from memory, no reference.
2. K-th largest element in an array (LeetCode 215).
3. Push 5 pairs and pop them all, predicting the order before you run it.
4. Build a min-heap ordered by the second element of a pair, using a struct comparator.

---

## B6. set and multiset

### 1. What is it?

`set` stores unique elements in sorted order, backed by a self-balancing binary search tree (a red-black tree). `multiset` is the same but allows duplicates.

### 2. Why do we need it?

When you need three things at once: uniqueness, sorted order, and O(log n) insert/erase/search. A sorted `vector` gives you two of the three but insertion is O(n). A hash set gives you two of the three but loses the ordering.

### 3. Core idea

Everything is kept in sorted order at all times. That is why iteration gives you sorted output for free, and why you get `lower_bound` and `upper_bound` as O(log n) member functions.

### 4. When should I use it?

- You need the smallest or largest element of a changing collection, *and* you need to remove from the middle. (A heap cannot remove from the middle.)
- You need "the smallest element greater than x" repeatedly. This is the `lower_bound` use case and it is the single strongest reason to pick `set` over `unordered_set`.
- You need sorted iteration.

If you only need "have I seen this before", use `unordered_set`. It is faster.

### 5. Operations

```cpp
set<int> s;
s.insert(x);              // O(log n)
s.erase(x);               // erase by value,  O(log n)
s.erase(it);              // erase by iterator, amortised O(1)
s.count(x);               // 0 or 1,          O(log n)
s.find(x);                // iterator or s.end()
s.size();  s.empty();  s.clear();

*s.begin();               // smallest         O(1)
*s.rbegin();              // largest          O(1)

auto it = s.lower_bound(x);   // first element >= x   O(log n)
auto it2 = s.upper_bound(x);  // first element >  x   O(log n)
```

### 6. C++ template: the "nearest neighbour" pattern

```cpp
set<int> s = {10, 20, 30, 40};

auto it = s.lower_bound(25);        // points to 30
if (it != s.end())   cout << *it;   // 30: smallest element >= 25
if (it != s.begin()) cout << *prev(it);  // 20: largest element < 25
```

This is the shape you use for "find the closest value", interval insertion, and several greedy problems.

### 7. Example

```cpp
multiset<int> ms;
ms.insert(5); ms.insert(5); ms.insert(3);
cout << ms.size();          // 3, duplicates kept
ms.erase(ms.find(5));       // removes ONE 5
cout << ms.count(5);        // 1
ms.erase(5);                // removes ALL remaining 5s
cout << ms.count(5);        // 0
```

### 8. Complexity

| Operation | Time |
|---|---|
| `insert`, `erase(value)`, `find`, `count` | O(log n) |
| `lower_bound`, `upper_bound` | O(log n) |
| `*begin()`, `*rbegin()` | O(1) |
| Iteration over all | O(n), in sorted order |
| Access k-th element | **O(k)**, there is no random access |

Space: O(n), with pointer overhead per node (a set of ints uses far more than 4 bytes per element).

### 9. Must remember

1. **`ms.erase(value)` on a multiset erases every copy.** To erase one, use `ms.erase(ms.find(value))`. This is a classic wrong-answer bug.
2. Use the **member** `s.lower_bound(x)`, not `std::lower_bound(s.begin(), s.end(), x)`. The free function on a set is O(n) because set iterators are not random access. Same trap with `std::find`: use `s.find(x)`.
3. There is no `s[k]`. Getting the k-th smallest is `*next(s.begin(), k)`, which is O(k). If you need k-th smallest repeatedly, you need an order-statistic tree or a Fenwick tree (Tier 4).
4. `set` erases only invalidate the erased iterator. All others stay valid. This is unlike `vector` and makes erase-while-iterating safer, though you still need the `it = s.erase(it)` idiom.
5. A `set` of a custom type needs `operator<` or a comparator. Two elements where neither is less than the other are treated as **the same element**. A comparator that only compares one field will silently drop entries.
6. `s.count(x)` on a plain `set` is 0 or 1 only. On a `multiset` it is O(log n + count).

### 10. Common mistakes

- `multiset::erase(value)` wiping out more than intended.
- Using `std::lower_bound` on a set and quietly getting O(n).
- Expecting `set` to preserve insertion order. It does not, ever.
- Using a `set` where an `unordered_set` would do, adding a log factor for no reason.
- Writing a comparator without the trailing `const`.

### 11. Practice

1. Insert 10 random numbers and print them sorted, with no call to `sort`.
2. For each query x, find the closest value in the set.
3. Maintain a multiset while removing exactly one occurrence at a time.
4. Explain out loud why `*next(s.begin(), k)` is O(k) and not O(log n).

---

## B7. map

### 1. What is it?

A sorted associative container: keys are unique and kept in sorted order, each mapped to a value. Same red-black tree as `set`, storing pairs.

### 2. Why do we need it?

Whenever data is naturally keyed rather than indexed. Character to count, node to distance, value to list of indices.

### 3. Core idea

`map<K, V>` is `set<pair<K, V>>` ordered by key, with convenience syntax. Iterating gives keys in ascending order.

### 4. When should I use it?

Use `map` over `unordered_map` when you need sorted key order, `lower_bound` on keys, or guaranteed O(log n) worst case. Otherwise use `unordered_map`, which is faster in practice.

### 5. Operations

```cpp
map<string, int> mp;
mp["apple"] = 3;              // insert or overwrite
mp["apple"]++;                // now 4
int x = mp["banana"];         // CREATES "banana" with value 0, then reads it

mp.count("apple");            // 0 or 1, the safe existence check
mp.find("apple");             // iterator, or mp.end()
mp.erase("apple");
mp.size();  mp.empty();

for (auto& [key, value] : mp) cout << key << " " << value << "\n";   // sorted by key
```

### 6. C++ template: frequency counting

```cpp
map<int, int> freq;
for (int x : nums) freq[x]++;        // default-constructs 0, then increments

for (auto& [val, cnt] : freq)
    cout << val << " appears " << cnt << " times\n";   // ascending by val
```

`freq[x]++` on a missing key works because `operator[]` default-constructs the value, and `int{}` is 0. This is the most used two-line pattern in all of DSA.

### 7. Example

```cpp
map<char, int> m;
string s = "aabbbc";
for (char c : s) m[c]++;
// m = {'a':2, 'b':3, 'c':1}, iterated in that order
```

### 8. Complexity

| Operation | Time |
|---|---|
| `mp[key]`, `insert`, `erase`, `find`, `count` | O(log n) |
| `lower_bound` / `upper_bound` on keys | O(log n) |
| Iteration | O(n), sorted by key |

Space O(n) plus significant per-node overhead.

### 9. Must remember

1. **`mp[key]` inserts when the key is absent.** Reading `mp["x"]` on a missing key silently adds it with a default value. This grows your map during a read loop and breaks `mp.size()`. Use `mp.count(key)` or `mp.find(key)` to test existence.
2. `mp[key]` on a `const map&` does not compile, for exactly that reason. Use `mp.at(key)` (throws if absent) or `find`.
3. Iteration order is sorted by key, always. If a problem needs insertion order, `map` cannot give it to you; use a `vector<pair<K,V>>` or a map plus a separate order vector.
4. `map<int, vector<int>>` works directly: `mp[k].push_back(v)` creates the empty vector on first touch.
5. Erasing while iterating needs the returned iterator:
   ```cpp
   for (auto it = mp.begin(); it != mp.end(); ) {
       if (shouldRemove(it->first)) it = mp.erase(it);
       else ++it;
   }
   ```
6. `it->first` is the key, `it->second` is the value. With structured bindings you can skip that syntax entirely.

### 10. Common mistakes

- Using `mp[key]` to check existence, thereby creating the key.
- Assuming `unordered_map` iterates in insertion order (it does not) or sorted order (it does not).
- Forgetting that a `map` key must be orderable. A `pair` or `string` key is fine; a custom struct needs `operator<`.
- Using `map` when `vector` would do. If keys are small integers `0..n`, a `vector<int>` of size n is faster and simpler.

### 11. Practice

1. Count word frequency in a sentence and print in alphabetical order.
2. Given an array, print each distinct value with its count, ascending.
3. Build a `map<int, vector<int>>` of value to list of indices.
4. Demonstrate to yourself that reading a missing key grows the map.

---

## B8. unordered_map and unordered_set

### 1. What is it?

Hash-table-backed versions of `map` and `set`. Average O(1) operations, no ordering.

### 2. Why do we need it?

Because O(1) beats O(log n) and, more importantly, because a very large share of "optimise this O(n²) brute force" answers are "put it in a hash map". Module 3 is built on this.

### 3. Core idea

A hash function converts the key into a bucket index. Lookup jumps straight to the bucket. Collisions are handled by chaining. When the load factor gets too high the table rehashes, which is O(n) but amortises away.

### 4. When should I use it?

Default to `unordered_map` and `unordered_set` for lookup, counting, and seen-checks. Switch to the ordered versions only when you actually need order or `lower_bound`.

### 5. Operations

The API is nearly identical to `map` and `set`:

```cpp
unordered_map<int, int> ump;
ump[x]++;
ump.count(x);  ump.find(x);  ump.erase(x);

unordered_set<int> us;
us.insert(x);
us.count(x);   // the "have I seen this" check
us.erase(x);
```

Missing compared to the ordered versions: `lower_bound`, `upper_bound`, `rbegin` in any meaningful sense, and sorted iteration.

### 6. C++ template: seen-set and complement lookup

```cpp
// Two Sum, the canonical hash map pattern
vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int, int> seen;              // value -> index
    for (int i = 0; i < (int)nums.size(); i++) {
        int need = target - nums[i];
        if (seen.count(need)) return {seen[need], i};
        seen[nums[i]] = i;
    }
    return {};
}
```

O(n) time, O(n) space. Module 3 generalises this shape.

### 7. Custom key types

`unordered_map` needs a hash function. It ships with hashes for the built-in types and `string`, but **not for `pair`**. This fails to compile:

```cpp
unordered_map<pair<int,int>, int> bad;    // no hash for pair
```

Three fixes, in order of preference for interviews:

```cpp
// 1. Use map instead (adds a log factor, costs zero thought)
map<pair<int,int>, int> ok;

// 2. Encode the pair into a single long long
unordered_map<long long, int> encoded;
encoded[(long long)a * 1000000 + b] = v;   // works when b is bounded

// 3. Write a hash functor
struct PairHash {
    size_t operator()(const pair<int,int>& p) const {
        return hash<long long>()(((long long)p.first << 32) ^ (unsigned int)p.second);
    }
};
unordered_map<pair<int,int>, int, PairHash> custom;
```

### 8. Complexity

| Operation | Average | Worst case |
|---|---|---|
| `insert`, `erase`, `find`, `count`, `[]` | O(1) | **O(n)** |
| Iteration | O(n), arbitrary order | O(n) |

Space O(n), typically with a larger constant than `map` due to bucket overhead.

### 9. Must remember

1. Worst case really is O(n) per operation. With adversarial input designed to collide, `unordered_map` degrades to a linked list. This is exploited on Codeforces ("hacking"), where the standard defence is a randomised hash seed. **It is not a concern in placement interviews or OAs**, so do not spend time on it, but know the answer if asked "what is the worst case".
2. `unordered_map` has no ordering of any kind. Not sorted, not insertion order. Do not rely on iteration order for anything.
3. Same `operator[]` insertion trap as `map`. Reading a missing key creates it.
4. No `lower_bound`. If you find yourself wanting "nearest key", you need `map` or a sorted `vector`.
5. `reserve(n)` before inserting n elements avoids repeated rehashing and is a real speedup on large inputs: `ump.reserve(n);`
6. For keys that are small non-negative integers, a plain `vector<int>` of size n beats any hash map. Do not reach for a map out of habit.

### 10. Common mistakes

- Using `unordered_map<pair<int,int>, int>` and being confused by a wall of template errors.
- Relying on iteration order and getting a different answer on a different compiler.
- Using `unordered_map` when the keys are `0..n-1` and an array was the obvious choice.
- Existence-checking with `[]` instead of `count`.

### 11. Practice

1. Two Sum (LeetCode 1). Write it from scratch.
2. Contains Duplicate (LeetCode 217) with an `unordered_set`.
3. Group anagrams using `map<string, vector<string>>` with a sorted-string key (LeetCode 49).
4. Store a `pair<int,int>` key three different ways and compare the code.

---

# Section C — Iterators, algorithms, lambdas, comparators

## C1. Iterators (compressed)

An iterator is a generalised pointer. `*it` reads the element, `++it` advances.

```cpp
v.begin()     // first element
v.end()       // ONE PAST the last element, never dereference it
v.rbegin()    // last element, for reverse iteration
v.rend()      // one before the first

auto it = v.begin();
*it;  ++it;  it + 3;        // random access: only for vector, string, deque, arrays
next(it, k);  prev(it);     // works on any iterator, O(k) for non-random-access
```

You almost never write raw iterator loops. You need iterators for exactly three reasons:

1. Passing ranges to algorithms: `sort(v.begin(), v.end())`.
2. Receiving the result of `find`, `lower_bound`, `upper_bound`.
3. Erasing while iterating.

### Must remember

1. `end()` is one past the end. Dereferencing it is undefined behaviour. **Always check `it != container.end()` before using `*it`.** This is the number-one iterator bug.
2. Converting an iterator to an index (vector only): `it - v.begin()`.
3. `set` and `map` iterators are **bidirectional**, not random access. `it + 3` does not compile; `next(it, 3)` does, at O(3).
4. Invalidation rules, which you do need to know:

| Container | What invalidates iterators |
|---|---|
| `vector` | any `insert`/`erase`/`push_back` that reallocates; everything from the erase point onward |
| `deque` | most insertions and erasures |
| `map`, `set` | only the erased element's iterator |
| `unordered_map`, `unordered_set` | rehashing invalidates all; erase invalidates only the erased one |

5. Erase-while-iterating idiom, for any associative container:
   ```cpp
   for (auto it = c.begin(); it != c.end(); ) {
       if (cond(*it)) it = c.erase(it);
       else ++it;
   }
   ```
   Writing `c.erase(it); ++it;` is undefined behaviour: you incremented a dead iterator.

---

## C2. The `<algorithm>` functions worth knowing

```cpp
sort(v.begin(), v.end());                    // O(n log n), introsort
sort(v.begin(), v.end(), greater<int>());    // descending
stable_sort(v.begin(), v.end());             // O(n log n), preserves equal order

reverse(v.begin(), v.end());                 // O(n)
max_element(v.begin(), v.end());             // iterator to max, O(n)
min_element(v.begin(), v.end());             // iterator to min, O(n)
accumulate(v.begin(), v.end(), 0LL);         // sum, from <numeric>
count(v.begin(), v.end(), x);                // O(n)
find(v.begin(), v.end(), x);                 // O(n), returns iterator or end()

lower_bound(v.begin(), v.end(), x);          // first >= x,  O(log n), SORTED input only
upper_bound(v.begin(), v.end(), x);          // first >  x,  O(log n), SORTED input only
binary_search(v.begin(), v.end(), x);        // bool,        O(log n), SORTED input only

unique(v.begin(), v.end());                  // dedupes ADJACENT equals, returns new end
next_permutation(v.begin(), v.end());        // next lexicographic arrangement
swap(a, b);
max(a, b);  min(a, b);
max({a, b, c});                              // initializer-list form
__gcd(a, b);                                 // GCD, GCC builtin
nth_element(v.begin(), v.begin() + k, v.end());  // k-th element in place, O(n) average
```

### The index idioms

```cpp
int idx = lower_bound(v.begin(), v.end(), x) - v.begin();   // first index with v[i] >= x
int cnt = upper_bound(...) - lower_bound(...);              // occurrences of x in sorted v
int maxVal = *max_element(v.begin(), v.end());              // note the leading *
```

### Sort then unique, the dedupe idiom

```cpp
sort(v.begin(), v.end());
v.erase(unique(v.begin(), v.end()), v.end());
```

`unique` only removes *adjacent* duplicates and does not shrink the container. It shuffles the survivors to the front and returns the new logical end. You must `erase` the tail yourself. Sorting first is what makes duplicates adjacent.

### Must remember

1. `lower_bound`, `upper_bound`, and `binary_search` **require sorted input**. On unsorted input they return garbage with no warning. This has cost more submissions than almost any other single fact.
2. `accumulate(v.begin(), v.end(), 0)` sums into an `int` and overflows. Write `0LL`.
3. `max_element` returns an *iterator*. Dereference it.
4. `sort` is introsort: quicksort with a heapsort fallback, so O(n log n) worst case, not the O(n²) of naive quicksort. It is not stable. Use `stable_sort` when equal elements must keep their relative order.
5. `nth_element` gives you the k-th smallest in O(n) average without fully sorting. It is the right answer to "find the k-th smallest" when you are allowed to use the library, though an interviewer usually wants the heap or quickselect version.
6. `__builtin_popcount(x)` counts set bits in O(1). `__builtin_popcountll` for `long long`. GCC-specific but available everywhere that accepts `bits/stdc++.h`.

---

## C3. Lambdas

### What is it?

An anonymous function you can define inline, optionally capturing variables from the surrounding scope.

```cpp
auto add = [](int a, int b) { return a + b; };
cout << add(2, 3);       // 5
```

### Anatomy

```
[capture](parameters) -> returnType { body }
```

The return type is almost always deducible, so you omit it.

### Captures

```cpp
int k = 5;
auto byValue = [k](int x)  { return x + k; };   // copies k
auto byRef   = [&k](int x) { k += x; return k; }; // references k
auto allRef  = [&](int x)  { return x + k; };   // captures everything by reference
auto allVal  = [=](int x)  { return x + k; };   // captures everything by value
```

For DSA, `[&]` is the pragmatic default: it captures whatever you reference, by reference, with no copying. The lifetime problems that make `[&]` dangerous in production code do not arise when the lambda is used immediately and locally.

### Where you actually use lambdas

**1. Custom sort comparators** (the main use, see C4).

**2. Recursive lambdas for self-contained solutions.** This is worth memorising because it lets you write a DFS inside a LeetCode method without declaring a separate helper:

```cpp
function<void(int, int)> dfs = [&](int node, int parent) {
    for (int next : adj[node])
        if (next != parent) dfs(next, node);
};
dfs(0, -1);
```

`function<void(int,int)>` from `<functional>` is needed because `auto` cannot deduce a type that refers to itself. It is slightly slower than a plain function due to type erasure, which never matters at interview scale.

### Must remember

1. `[&]` captures by reference. If the lambda outlives the captured variable you have a dangling reference. For local use this never happens.
2. A lambda that modifies a by-value capture needs `mutable`. You will rarely want this.
3. `function<...>` is required for recursion; plain `auto` will not compile.
4. Lambdas are objects, so a lambda comparator passed to `priority_queue` or `set` must be passed to the constructor as well as named in the template argument. `sort` does not have this problem.

---

## C4. Custom comparators

This section exists because comparator syntax is the most commonly botched piece of C++ in interviews, and because the rules differ between `sort`, `priority_queue`, and `set`.

### 1. What is it?

A function, lambda, or struct that tells the library how to order two elements.

### 2. Why do we need it?

Default ordering handles `int`, `string`, and `pair`. The moment you sort intervals by end time, or order a heap by the second field, or sort by frequency descending with ties broken by value ascending, you need your own rule.

### 3. Core idea

A comparator answers exactly one question: **"does `a` come before `b`?"** Return `true` if yes. Everything else follows from that, including the counterintuitive `priority_queue` behaviour.

### 4. The three forms

**For `sort`: a lambda, almost always.**

```cpp
// Sort intervals by end time ascending
sort(intervals.begin(), intervals.end(),
     [](const vector<int>& a, const vector<int>& b) {
         return a[1] < b[1];
     });

// Sort by frequency descending, ties broken by value ascending
sort(v.begin(), v.end(), [&](int a, int b) {
    if (freq[a] != freq[b]) return freq[a] > freq[b];
    return a < b;
});
```

**For `priority_queue`: a struct (or a lambda plus `decltype`).**

```cpp
struct Cmp {
    bool operator()(const pair<int,int>& a, const pair<int,int>& b) const {
        return a.second > b.second;     // smaller .second has HIGHER priority
    }
};
priority_queue<pair<int,int>, vector<pair<int,int>>, Cmp> pq;
```

With a lambda:

```cpp
auto cmp = [](const pair<int,int>& a, const pair<int,int>& b) {
    return a.second > b.second;
};
priority_queue<pair<int,int>, vector<pair<int,int>>, decltype(cmp)> pq(cmp);
```

Note the lambda is passed to the constructor, not just named in the template.

**For `set` and `map`: a struct.**

```cpp
struct Cmp {
    bool operator()(const pair<int,int>& a, const pair<int,int>& b) const {
        return a.second < b.second;     // order by second field
    }
};
set<pair<int,int>, Cmp> s;
```

### 5. The inversion rule (read this twice)

For `sort`, `cmp(a, b) == true` means **a comes first in the output**.

For `priority_queue`, `cmp(a, b) == true` means **a has lower priority than b**, so a comes out *later*.

The consequence:

| Comparator body | With `sort` | With `priority_queue` |
|---|---|---|
| `return a < b;` | ascending order | **max**-heap |
| `return a > b;` | descending order | **min**-heap |

This is why `greater<int>` gives a min-heap. Copying a comparator between `sort` and `priority_queue` without flipping it is a top-five interview bug.

### 6. Complexity

The comparator itself must be O(1), or you multiply the sort cost by its complexity. A comparator that calls `substr` or compares long strings turns O(n log n) into something much worse.

### 7. Must remember

1. **The comparator must implement a strict weak ordering.** In practice: use `<` or `>`, never `<=` or `>=`. A comparator that returns `true` for two equal elements makes `std::sort` read out of bounds and crash. This is a genuine runtime error, not a wrong answer, and it is one of the hardest bugs to diagnose because the code looks correct.
2. The `const` after `operator()(...)` in a struct comparator is required. Omitting it produces a long, unhelpful error.
3. `sort` is not stable. If equal elements must keep their input order, either add a tiebreaker to the comparator or use `stable_sort`.
4. For `set` and `map`, two elements that compare equivalent (neither is less than the other) are treated as the **same key**. A comparator on one field means a set keyed by that field alone, silently dropping the rest.
5. Take parameters by `const&` for non-trivial types. Passing `vector<int>` by value into a comparator called O(n log n) times is a real cost.
6. `greater<int>()` and `less<int>()` from `<functional>` cover descending and ascending. Use them instead of hand-writing trivial lambdas.

### 8. Common mistakes

- `return a <= b;` inside a `sort` comparator. Crashes on large inputs, passes on small ones.
- Forgetting the trailing `const` in the struct form.
- Using the `sort` version of a comparator in a `priority_queue` and getting the wrong heap.
- Building a `set` with a single-field comparator and losing elements that share that field.
- Capturing by value in a comparator lambda that reads a large external array.

### 9. Practice

1. Sort a `vector<pair<int,int>>` by second ascending, then first descending.
2. Sort strings by length, ties alphabetically.
3. Build a min-heap of pairs ordered by the second element, both ways (struct and lambda).
4. Write a comparator with `<=` and run it on 10⁵ elements to see the crash. Once is enough.

---

# Section D — Comparison tables

### map vs unordered_map

| | `map` | `unordered_map` |
|---|---|---|
| Backing structure | Red-black tree | Hash table |
| Average lookup | O(log n) | O(1) |
| Worst lookup | O(log n) | O(n) |
| Ordering | Sorted by key | None |
| `lower_bound` | Yes | No |
| Memory | Lower per element | Higher (buckets) |
| Custom key | Needs `operator<` | Needs a hash function |
| Use when | Order matters, or you need nearest-key | Pure lookup or counting |

**Default: `unordered_map`.** Switch to `map` when you need order.

### set vs unordered_set

Identical trade-offs. `set` if you need sorted iteration, the min/max, or `lower_bound`. `unordered_set` for "have I seen this".

### vector vs array vs deque vs list

| | Random access | Insert front | Insert back | Insert middle | Contiguous |
|---|---|---|---|---|---|
| C array | O(1) | n/a | n/a | n/a | yes |
| `vector` | O(1) | O(n) | O(1) amortised | O(n) | yes |
| `deque` | O(1) | O(1) | O(1) | O(n) | no |
| `list` | **O(n)** | O(1) | O(1) | O(1) with iterator | no |

`std::list` is almost never the right answer in interview DSA. You implement linked lists by hand with `ListNode*` instead, because that is what the problems are testing.

### Stack memory vs heap memory

| | Stack | Heap |
|---|---|---|
| What lives there | Local variables, function parameters, recursion frames | `new`, and the contents of every STL container |
| Size limit | ~1 MB to 8 MB | System RAM |
| Allocation cost | Free (pointer bump) | Slower |
| Lifetime | Until the function returns | Until you free it |
| Failure mode | Stack overflow (segfault) | Bad alloc / out of memory |

Why this matters: `int arr[1000000];` as a local variable overflows the stack and crashes. The same array as a global, or as `vector<int> v(1000000);`, is fine, because globals live in static storage and a vector's data lives on the heap.

### Pass by value vs reference vs const reference

| | Copies? | Caller sees changes? | Accepts temporaries? | Use for |
|---|---|---|---|---|
| `T` | yes | no | yes | `int`, `char`, pointers |
| `T&` | no | yes | no | containers you modify |
| `const T&` | no | no | yes | containers you read |

---

# Section E — STL complexity cheat sheet

| Container | Access | Search | Insert | Erase | Ordered? | Notes |
|---|---|---|---|---|---|---|
| `vector` | O(1) | O(n) | O(1) back, O(n) middle | O(1) back, O(n) middle | insertion order | contiguous; reallocation invalidates iterators |
| `string` | O(1) | O(n·m) | O(1) back | O(n) middle | insertion order | `substr` is O(len) |
| `deque` | O(1) | O(n) | O(1) both ends | O(1) both ends | insertion order | not contiguous |
| `stack` | top O(1) | no | O(1) | O(1) | LIFO | adapter, not iterable |
| `queue` | front/back O(1) | no | O(1) | O(1) | FIFO | adapter, not iterable |
| `priority_queue` | top O(1) | no | O(log n) | O(log n) | by priority | O(n) build from range |
| `set` / `multiset` | no `[]` | O(log n) | O(log n) | O(log n) | sorted | member `lower_bound` |
| `map` / `multimap` | O(log n) | O(log n) | O(log n) | O(log n) | sorted by key | `[]` inserts on read |
| `unordered_set` | no `[]` | O(1) avg, O(n) worst | O(1) avg | O(1) avg | none | needs a hash for custom keys |
| `unordered_map` | O(1) avg | O(1) avg, O(n) worst | O(1) avg | O(1) avg | none | `[]` inserts on read |

| Algorithm | Time | Notes |
|---|---|---|
| `sort` | O(n log n) | introsort, not stable |
| `stable_sort` | O(n log n) | needs extra memory |
| `nth_element` | O(n) average | partial ordering only |
| `lower_bound` / `upper_bound` / `binary_search` | O(log n) | sorted input required |
| `reverse` | O(n) | |
| `accumulate` | O(n) | pass `0LL` for sums |
| `max_element` / `min_element` / `count` / `find` | O(n) | return iterators |
| `unique` | O(n) | adjacent only, must sort first |
| `next_permutation` | O(n) | |
| `__gcd` | O(log min(a,b)) | |
| `__builtin_popcount` | O(1) | |

---

# Section F — Phase 0 must-remember (consolidated)

The 15 facts from this module most likely to cost you a submission. If you remember nothing else, remember these.

1. Cast **before** the multiplication: `(long long)a * b`, not `long long x = a * b`.
2. `mid = lo + (hi - lo) / 2`, never `(lo + hi) / 2`.
3. `.size()` is unsigned. `v.size() - 1` on an empty container is catastrophic.
4. Missing `&` on a container parameter in a recursive function silently adds a factor of n.
5. `priority_queue<int, vector<int>, greater<int>>` is the min-heap. Three template arguments, always.
6. `priority_queue` comparators are **inverted** relative to `sort` comparators.
7. `sort` comparators must use strict `<` or `>`. A `<=` comparator crashes at scale.
8. `mp[key]` **inserts** a default value when the key is absent. Check existence with `count` or `find`.
9. `multiset::erase(value)` removes **all** copies. Use `erase(find(value))` for one.
10. Use `s.lower_bound(x)` (member) on a set, never `std::lower_bound(s.begin(), ...)` which is O(n).
11. `lower_bound` / `upper_bound` / `binary_search` require **sorted** input and fail silently otherwise.
12. `accumulate(..., 0)` overflows. Use `0LL`.
13. `s.find(t)` returns `string::npos`, not `-1`. Compare against `npos`.
14. `pop()` returns void on `stack`, `queue`, and `priority_queue`. Read `top()`/`front()` first, and never call either on an empty container.
15. Recursion depth beyond roughly 10⁵ overflows the stack and segfaults with no message. Suspect depth before logic when a large test crashes but small ones pass.

---

# Section G — Common mistakes (consolidated)

Grouped by how they present, so you can diagnose from the symptom.

**Symptom: wrong answer on large tests, correct on small ones**
- Integer overflow (`int` where `long long` was needed).
- `accumulate` with a `0` seed.
- Unsigned underflow from `.size() - 1`.

**Symptom: time limit exceeded with a correct algorithm**
- Container passed by value into recursion.
- `substr` or string concatenation inside a loop.
- `erase`/`insert` in the middle of a vector inside a loop.
- `std::lower_bound` on a `set`.
- Using `endl` instead of `"\n"` in a large output loop.
- Missing the fast-I/O lines on an input-heavy problem.

**Symptom: runtime error or segfault**
- Dereferencing a null `ListNode*` or `TreeNode*`.
- `top()` / `front()` on an empty container.
- Out-of-bounds `v[i]`.
- Dereferencing `end()`.
- Comparator using `<=`.
- Deep recursion overflowing the stack.
- Large local array declared inside a function.

**Symptom: logic looks right but the output is subtly off**
- `mp[key]` creating entries during a read loop.
- `multiset::erase(value)` removing too much.
- `priority_queue` comparator inverted, giving the wrong heap.
- Range-for by value when you meant to modify.
- `unique` without sorting first, or without the trailing `erase`.
- Relying on `unordered_map` iteration order.
- `set` with a partial comparator silently dropping elements.

**Symptom: will not compile**
- Missing `const` on a struct comparator's `operator()`.
- `unordered_map` with a `pair` key.
- `priority_queue` with two template arguments.
- Recursive lambda declared `auto` instead of `function<...>`.
- `mp[key]` on a `const map&`.

---

# Section H — Drills

No LeetCode grind yet. Module 0 is about fluency, so these are timed typing exercises. Do each from memory, then check. Target: all of them inside 45 minutes total, on your second attempt.

| # | Drill | Tests |
|---|---|---|
| 1 | Write the file header and fast-I/O block from memory | Setup |
| 2 | Read n, then n integers, print their sum as `long long` | I/O + overflow |
| 3 | Declare an n × m grid of zeros and print it | 2D vector |
| 4 | Count character frequency with a 26-element array and with a `map` | Both counting idioms |
| 5 | Sort a `vector<pair<int,int>>` by second descending, ties by first ascending | Comparator |
| 6 | Declare a max-heap and a min-heap, push 5 values into each, pop all | `priority_queue` syntax |
| 7 | Build a min-heap of pairs ordered by `.second`, using a struct comparator | Custom comparator |
| 8 | Insert into a `set`, then find the smallest element greater than x | `lower_bound` |
| 9 | Erase every even key from a `map` while iterating | Iterator invalidation |
| 10 | Write `ListNode` and `TreeNode` definitions from memory | Node structs |
| 11 | Write a recursive lambda that prints 1 to n | `function<>` syntax |
| 12 | Dedupe a vector with sort + unique + erase | The idiom |

Then four real problems, chosen because each is really an STL exercise in disguise:

| Problem | Platform | Difficulty | What it teaches |
|---|---|---|---|
| Two Sum | LeetCode 1 | Easy | `unordered_map` complement lookup, the single most reused pattern in DSA |
| Contains Duplicate | LeetCode 217 | Easy | `unordered_set` as a seen-set |
| Valid Anagram | LeetCode 242 | Easy | Frequency array vs sorted-string key; two valid approaches with different complexities |
| Group Anagrams | LeetCode 49 | Medium | `map<string, vector<string>>`, building a canonical key, nested containers |

Solve them with the STL, not with hand-rolled arrays. The point is fluency, not cleverness. You will meet all four again in Module 3 with the patterns made explicit.

---

# Exit checklist

```
[ ] I can write the file header and fast-I/O block from memory
[ ] I know when int overflows and I reach for long long automatically
[ ] I always cast before multiplying
[ ] I write mid = lo + (hi - lo) / 2 without thinking
[ ] I pass containers by const& or & and never by value into recursion
[ ] I can declare a min-heap from memory, first try
[ ] I know priority_queue comparators are inverted from sort comparators
[ ] I never use <= in a comparator
[ ] I check map existence with count/find, not []
[ ] I use the member lower_bound on sets
[ ] I know that lower_bound requires sorted input
[ ] I can write ListNode and TreeNode from memory
[ ] I can write a sort comparator with a tiebreaker in under 30 seconds
[ ] I can predict the complexity of any STL call I make
[ ] Drills 1-12 done from memory
[ ] All four practice problems solved
```

---

## Next

Say **"Start Phase 1"** for Complexity Analysis (3–4 hours): Big O / Theta / Omega, how to read complexity off loops and recursion, amortised analysis, and the constraint-to-complexity table that tells you which algorithm the problem is asking for before you have solved anything.
