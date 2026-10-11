# OOP Placement Handbook (C++) — Part 8
# Module 6: The Modern C++ Object Model

**Module 6 · 2–3 hours · Tier 2 · Requires: M0–M5**

---

## What this module adds

M0–M5 covered OOP as every language teaches it. This module covers the parts of OOP that are **specific to modern C++**, the ones interviewers use to check whether your C++ is from this decade:

- **Smart pointers.** "How do you avoid memory leaks in C++?" is the most common question here, and `unique_ptr`/`shared_ptr`/`weak_ptr` is the expected answer.
- **Casts and RTTI.** `dynamic_cast` and when needing it signals a design problem.
- **Exceptions and objects.** Catch by reference (slicing again) and exception-safety guarantees.
- **Static vs dynamic polymorphism.** CRTP vs `virtual`.

**If you're short on time**, do §6.1–6.5 (smart pointers) and §6.8 (catch by reference), and skim the rest.

The organising principle:

> **In modern C++ the type of a pointer documents and enforces ownership. `unique_ptr` means "I alone own this", `shared_ptr` means "we jointly own this", `weak_ptr` and raw pointers or references mean "I only look at this". Choose the type, and the compiler handles the `delete`.**

---

## 6.1 Why raw owning pointers are a problem

```cpp
void process() {
    Widget* w = new Widget();
    if (!w->valid()) return;     // LEAK: early return skips delete
    w->run();                    // if run() throws: LEAK
    delete w;
}
```

| Problem with raw `new`/`delete` | What goes wrong |
|---|---|
| **Leak** | A path (early return, exception) skips `delete` |
| **Double delete** | Two owners both delete (M1 shallow copy) |
| **Dangling pointer** | Used after another owner deleted it |
| **Unclear ownership** | `Widget* getWidget()`: must the caller delete it? The type doesn't say |
| **Exception unsafety** | Any throw between `new` and `delete` leaks |

Smart pointers apply **RAII** (M1 §1.15) to heap memory: the pointer object's destructor does the `delete`, so every exit path is covered.

---

## 6.2 `unique_ptr`: exclusive ownership

### 1. What is it?

A smart pointer that **solely owns** an object and deletes it when the `unique_ptr` is destroyed. It **can't be copied**, because two unique owners would be a contradiction, but it **can be moved**, which transfers ownership.

### 2. How it works

```cpp
#include <memory>

auto w = std::make_unique<Widget>(42);     // C++14: preferred way to create
w->run();                                   // use like a pointer
Widget& ref = *w;

// auto w2 = w;                             // ERROR: copy constructor is deleted
auto w2 = std::move(w);                     // ownership transferred; w is now nullptr

w2.reset();                                 // deletes the Widget now; w2 becomes nullptr
Widget* raw = w2.get();                     // non-owning raw access (don't delete it!)
```

```cpp
void process() {
    auto w = std::make_unique<Widget>();
    if (!w->valid()) return;     // ~unique_ptr deletes: no leak
    w->run();                    // throws? stack unwinding deletes: no leak
}                                // normal exit: deleted
```

### 3. Properties

| Property | Detail |
|---|---|
| Copyable | **No** (copy operations are `= delete`d) |
| Movable | Yes: transfers ownership; the source becomes `nullptr` |
| Size | **Same as a raw pointer** with the default deleter: zero overhead |
| Arrays | `unique_ptr<int[]> a = make_unique<int[]>(n);` calls `delete[]` (but prefer `vector`) |
| Custom deleter | `unique_ptr<FILE, decltype(&fclose)> f(fopen("x", "r"), &fclose);` for non-memory resources |
| Converts to `shared_ptr` | Yes: `shared_ptr<T> s = std::move(u);` |

### 4. Use it for

- **The default choice** for any owning pointer.
- Polymorphic objects: `vector<unique_ptr<Shape>>` (avoids slicing, M3).
- Factory return types: `unique_ptr<Shape> makeShape(string kind);`. The caller gets clear ownership and can convert it to `shared_ptr` if needed.
- Pimpl (M2 §2.7).
- A class with a `unique_ptr` member is automatically **move-only**, the correct behaviour for a unique owner (rule of zero, M1).

---

## 6.3 `shared_ptr`: shared ownership

### 1. What is it?

A smart pointer that allows **multiple owners**. It keeps a **reference count**, and the object is deleted when the **last** `shared_ptr` to it is destroyed or reset.

### 2. How it works

```cpp
auto p = std::make_shared<int>(5);   // count = 1
{
    auto q = p;                      // copy: count = 2
}                                    // q destroyed: count = 1
cout << p.use_count();               // 1
p.reset();                           // count = 0 -> int deleted
```

```
   p ---+                         control block (heap)
        +----> +-------------------+------------------+
   q ---+      | strong count = 2  | weak count = 0   |
               | deleter, ...      |                  |
               +-------------------+------------------+
               |       the managed object            |   <- same allocation with make_shared
               +-------------------------------------+
```

### 3. The control block and `make_shared`

Each managed object has a **control block** holding the strong count (owners), the weak count (observers) and the deleter.

| | `shared_ptr<T>(new T(...))` | `make_shared<T>(...)` |
|---|---|---|
| Heap allocations | **Two** (object + control block) | **One** (both together) |
| Exception safety | Weaker in some older call patterns | Safe |
| Cache locality | Worse | Better |
| Use | Only for custom deleters or adopting existing pointers | **Default** |

### 4. Costs and caveats

| Point | Detail |
|---|---|
| Size | **Two pointers** (object + control block) |
| Count updates | **Atomic**, so copying a `shared_ptr` costs more than copying a raw pointer |
| Thread safety | The **reference count** is thread-safe. The **pointed-to object is not**; you still need a mutex to modify it from several threads |
| Double control block bug | `Widget* raw = new Widget; shared_ptr<Widget> a(raw), b(raw);` creates two independent counts, so it's a **double delete**. Never build two `shared_ptr`s from one raw pointer |
| `this` problem | To get a `shared_ptr` to yourself inside a member function, inherit `enable_shared_from_this<T>` and call `shared_from_this()` (Tier 3) |
| **Cycles leak** | §6.4 |

### 5. Use it for

Genuinely shared ownership, where no single owner outlives all the others: a cache entry used by several clients, nodes in a graph structure shared by several holders, or an asynchronous callback that must keep an object alive. **Don't use it by default.** It hides ownership design and costs more.

---

## 6.4 `weak_ptr` and the cycle leak

### 1. The cycle problem

```cpp
struct Node {
    string name;
    shared_ptr<Node> other;
    Node(string s) : name(s) {}
    ~Node() { cout << "~" << name << " "; }
};

{
    auto a = make_shared<Node>("a");
    auto b = make_shared<Node>("b");
    a->other = b;              // b's count = 2
    b->other = a;              // a's count = 2
}   // locals a, b destroyed -> both counts drop to 1, never 0
    // NOTHING is printed: both Nodes leak
```

```
    a (local) --X                       b (local) --X       <- gone at scope end
                 \                                 /
                  v                               v
              +--------+   other (shared)    +--------+
              | Node a | ------------------> | Node b |
              | cnt=1  | <------------------ | cnt=1  |
              +--------+   other (shared)    +--------+
                    each keeps the other alive forever
```

Reference counting **cannot reclaim cycles**. This is the main weakness of `shared_ptr`, and a classic interview question.

### 2. `weak_ptr`: the fix

A `weak_ptr` **observes** an object managed by `shared_ptr`s **without owning it**: it doesn't increase the strong count.

```cpp
struct Node {
    string name;
    weak_ptr<Node> other;          // non-owning back-reference
    Node(string s) : name(s) {}
    ~Node() { cout << "~" << name << " "; }
};
// same code as above -> prints "~b ~a": both freed
```

**Using a `weak_ptr`:** it can't be dereferenced directly, because the object might already be gone. Promote it with `lock()`:

```cpp
weak_ptr<int> w = sp;
if (auto s = w.lock()) {           // shared_ptr, or empty if the object is dead
    cout << *s;                    // safe: s keeps it alive for this block
}
w.expired();                       // true if the object has been destroyed
```

### 3. The typical pattern: parent owns, child observes

```cpp
struct TreeNode {
    vector<shared_ptr<TreeNode>> children;   // parent OWNS children
    weak_ptr<TreeNode> parent;               // child only OBSERVES parent
};
```

Other `weak_ptr` uses: **caches** (hold entries weakly, so they disappear when nobody else uses them) and **observers** (the Observer pattern, M8, where subjects shouldn't keep dead listeners alive).

### 4. A memory detail (Tier 3)

With `make_shared`, the object and control block share one allocation. When the strong count reaches 0, the object's **destructor** runs immediately, but the **memory block** is released only when the weak count also reaches 0. Long-lived `weak_ptr`s to large `make_shared` objects can therefore hold memory longer than expected.

### 5. Must remember

1. `shared_ptr` cycles never reach count 0, so they **leak**.
2. `weak_ptr` doesn't increase the strong count; it breaks cycles.
3. Use `lock()` to access, and check the result. `expired()` tells you whether the object is gone.
4. Ownership goes downward (`shared_ptr`/`unique_ptr` to children); back-references are `weak_ptr` or raw.

---

## 6.5 Choosing and passing smart pointers

### 1. Choosing

| Situation | Use |
|---|---|
| Single owner (the vast majority of cases) | `unique_ptr` |
| Genuinely shared ownership, no clear single owner | `shared_ptr` |
| Observer of a `shared_ptr`-managed object that may die, or a cycle breaker | `weak_ptr` |
| Non-owning access where the object surely outlives you | Raw pointer `T*` (nullable) or reference `T&` |
| An array of values | `vector`, not a smart pointer |
| No heap allocation needed at all | A plain object (best of all) |

### 2. Passing to functions (asked at deeper interviews)

| Signature | Meaning |
|---|---|
| `void f(Widget&)` / `void f(const Widget&)` | Uses the object; **doesn't care about ownership**. Use this most of the time |
| `void f(Widget*)` | Same, but nullable |
| `void f(unique_ptr<Widget>)` | **Takes ownership** (caller must `std::move`) |
| `void f(shared_ptr<Widget>)` | **Shares ownership** (keeps it alive after return, e.g. stores it) |
| `void f(const shared_ptr<Widget>&)` | Might copy it to share; usually a sign `Widget&` would do |
| `unique_ptr<Widget> make()` | Factory: transfers ownership to the caller |

**Rule:** don't pass smart pointers to functions that only *use* the object. Pass a reference.

### 3. Comparison table

| | `unique_ptr` | `shared_ptr` | `weak_ptr` |
|---|---|---|---|
| Ownership | Exclusive | Shared (counted) | None |
| Copyable | No (move only) | Yes | Yes |
| Size | 1 pointer | 2 pointers | 2 pointers |
| Overhead | None | Control block, atomic counts | Same control block |
| Deletes the object | When it dies | When the last owner dies | Never |
| Dereference directly | Yes | Yes | **No**, `lock()` first |
| Typical use | Default owner, factories, Pimpl | Shared caches, graphs | Back-pointers, caches, observers |

### 4. Interview questions

- *"How do you prevent memory leaks in C++?"* RAII: never manage heap memory with raw `new`/`delete`. Use `unique_ptr` for single ownership, `shared_ptr` only for genuinely shared ownership, and containers like `vector` for arrays. Destructors then free everything on every path, including exceptions. *Follow-up: "Can `shared_ptr` leak?"* Yes, with reference cycles. Break them with `weak_ptr`.
- *"`unique_ptr` vs `shared_ptr`?"* Exclusive vs shared ownership; move-only vs copyable; zero overhead vs a control block with atomic reference counts. Default to `unique_ptr`.
- *"Is `shared_ptr` thread-safe?"* The reference count is (its updates are atomic). Access to the managed object is not.

---

## 6.6 The four C++ casts

### 1. The table

| Cast | Purpose | Checked | Typical use |
|---|---|---|---|
| `static_cast<T>(x)` | Well-defined conversions known at compile time | Compile time only | Numeric conversions (`double` → `int`), `void*` → `T*`, **upcasts**, downcasts you've *proven* are safe |
| `dynamic_cast<T>(x)` | Safe downcast or cross-cast in a polymorphic hierarchy | **Runtime** (uses RTTI) | "Is this `Shape*` actually a `Circle*`?" |
| `const_cast<T>(x)` | Add or remove `const`/`volatile` | Compile time | Calling a legacy API that takes `char*` but doesn't modify it |
| `reinterpret_cast<T>(x)` | Reinterpret the bits as an unrelated type | None | Low-level code: pointer ↔ integer, byte buffers |
| C-style `(T)x` | Tries const, static and reinterpret casts in turn | Barely | **Avoid**: hides intent, can silently do a reinterpret, and is hard to grep for |

### 2. `dynamic_cast` in detail

```cpp
struct Shape  { virtual ~Shape() = default; };        // MUST be polymorphic
struct Circle : Shape { double r = 1; };
struct Square : Shape {};

Shape* s = new Circle;

Circle* c = dynamic_cast<Circle*>(s);     // valid pointer: s really is a Circle
Square* q = dynamic_cast<Square*>(s);     // nullptr: it isn't a Square

Shape& ref = *s;
Square& sq = dynamic_cast<Square&>(ref);  // throws std::bad_cast (references can't be null)
```

| Rule | Detail |
|---|---|
| Source type must be polymorphic | At least one virtual function; otherwise compile error. It reads the RTTI through the vptr |
| On failure with a pointer | Returns `nullptr` |
| On failure with a reference | Throws `std::bad_cast` |
| Cost | A runtime type-hierarchy walk; much slower than `static_cast` |
| Disabled | With `-fno-rtti` (common in games and embedded code) |

### 3. `static_cast` downcasts are unchecked

```cpp
Shape* s = new Square;
Circle* c = static_cast<Circle*>(s);      // compiles; using c is UNDEFINED BEHAVIOUR
```

Use `static_cast` for a downcast only when the type is guaranteed by construction.

### 4. `const_cast` caveat

Removing `const` and then **modifying an object that was originally declared const** is undefined behaviour. `const_cast` is legal only when the underlying object isn't actually const.

### 5. The design point (what the interviewer wants to hear)

**Frequent `dynamic_cast` is a design smell.** Code like this:

```cpp
if (auto c = dynamic_cast<Circle*>(s)) drawCircle(c);
else if (auto q = dynamic_cast<Square*>(s)) drawSquare(q);
```

is a `switch` on type: every new shape means editing this code, which violates the Open/Closed Principle (M7). The polymorphic fix is a virtual `draw()` in `Shape`. `dynamic_cast` is justified at boundaries, for example checking whether an object supports an optional interface (`if (auto p = dynamic_cast<Printable*>(obj))`).

### 6. Must remember

1. Four casts: static (compile-time conversions), dynamic (checked downcast), const (constness), reinterpret (bits).
2. `dynamic_cast` needs a polymorphic type; it gives `nullptr` for pointers and throws `bad_cast` for references.
3. A `static_cast` downcast is unchecked: UB if wrong.
4. Avoid C-style casts.
5. Many `dynamic_cast`s mean a missing virtual function.

---

## 6.7 RTTI and `typeid`

**RTTI (Run-Time Type Information)** is the type information the compiler stores (usually reachable through the vtable) so that `dynamic_cast` and `typeid` work.

```cpp
#include <typeinfo>

Shape* s = new Circle;
typeid(*s) == typeid(Circle);    // true: polymorphic type, so the DYNAMIC type
typeid(s)  == typeid(Shape*);    // true: the pointer itself has static type Shape*
typeid(*s).name();               // implementation-defined string (GCC: mangled, e.g. "6Circle")

struct A {}; struct B : A {};    // NOT polymorphic
B b; A& r = b;
typeid(r) == typeid(A);          // true: no vptr, so only the STATIC type is available
```

| Must remember |
|---|
| `typeid` on a **polymorphic** object (through a reference or dereferenced pointer) gives the **dynamic** type; on a non-polymorphic one, the **static** type |
| `type_info::name()` is implementation-defined; don't parse it or rely on it |
| RTTI can be disabled (`-fno-rtti`); then `dynamic_cast` and polymorphic `typeid` don't work |
| Branching on `typeid` has the same smell as branching on `dynamic_cast`; prefer virtual functions |

---

## 6.8 Exceptions and objects

### 1. Throw by value, catch by const reference

```cpp
struct AppError { virtual const char* what() const { return "AppError"; } virtual ~AppError() = default; };
struct DbError : AppError { const char* what() const override { return "DbError"; } };

try { throw DbError(); }
catch (AppError e)        { cout << e.what(); }   // "AppError"  <- SLICED (M3)

try { throw DbError(); }
catch (const AppError& e) { cout << e.what(); }   // "DbError"   <- polymorphism preserved
```

Catching by value **copies** the exception into a base-class object, which slices it: the derived type and its overrides are lost. Catching by reference also avoids an extra copy. **Always `catch (const T&)`.**

Also: order `catch` blocks from **most derived to most general**. A `catch (const AppError&)` placed before `catch (const DbError&)` would catch everything first. (`std::exception` is the usual root; derive your own exceptions from it.)

### 2. Constructors that throw (recap from M1, now with proof)

```cpp
struct M { M() { cout << "M "; } ~M() { cout << "~M "; } };
struct T {
    M m;
    int* raw;
    T() : raw(new int[10]) { cout << "T-body "; throw runtime_error("x"); }
    ~T() { cout << "~T "; delete[] raw; }
};
try { T t; } catch (...) { cout << "caught"; }
```

**Output:** `M T-body ~M caught`

- `~T` **never runs**, because `T` was never fully constructed.
- The fully constructed member `m` **is** destroyed (`~M`).
- `raw`'s array **leaks**, because a raw pointer has no destructor.

**The fix:** make every resource an RAII member (`unique_ptr<int[]>` or `vector<int>`). Then it's a fully constructed member and is cleaned up automatically.

### 3. Exception-safety guarantees

What a function promises if an exception escapes it:

| Guarantee | Promise | Example |
|---|---|---|
| **No-throw** (`noexcept`) | Never throws | Destructors, swaps, move constructors (ideally) |
| **Strong** | If it throws, the state is **unchanged** (commit or roll back) | Copy-and-swap assignment (M1 §1.8); `vector::push_back` when the element's move is noexcept or it's copyable |
| **Basic** | If it throws, there are no leaks and invariants hold, but the state may have changed | Most operations |
| None | Anything can happen | Bad code |

The copy-and-swap idiom from M1 gives the **strong** guarantee: all the throwing work (the copy) happens before anything in `*this` changes, and the swap can't throw.

### 4. Must remember

1. **Catch by `const&`**: catching by value slices.
2. Order catch blocks from derived to base.
3. A throwing constructor: no destructor call for that object, but its built members are destroyed. Hold resources in RAII members.
4. Destructors are `noexcept` (M1).
5. Guarantees: no-throw > strong > basic. Copy-and-swap gives strong.

---

## 6.9 Static vs dynamic polymorphism (CRTP)

### 1. CRTP: polymorphism without virtual

The **Curiously Recurring Template Pattern**: the base class is a template parameterised by the derived class, so it can call derived methods with **no vtable**:

```cpp
template <class Derived>
struct Shape {
    double area() const {
        return static_cast<const Derived*>(this)->areaImpl();   // resolved at COMPILE time
    }
};
struct Square : Shape<Square> {
    double s = 3;
    double areaImpl() const { return s * s; }
};

template <class T>
void print(const Shape<T>& sh) { cout << sh.area(); }   // 9 for a Square

Square q; print(q);
```

### 2. Comparison

| | Dynamic (`virtual`) | Static (templates / CRTP) |
|---|---|---|
| Dispatch | Runtime, through the vtable | Compile time |
| Speed | Indirect call, usually not inlined | Direct call, inlinable: zero overhead |
| Heterogeneous containers | **Yes**: `vector<unique_ptr<Shape>>` holds circles and squares together | **No**: `Shape<Circle>` and `Shape<Square>` are unrelated types |
| New types added | Without recompiling the users (plugins, libraries) | All types must be known at compile time |
| Code size | One copy of each function | One copy per instantiated type (bloat) |
| Error messages | Clear | Template errors, sometimes cryptic |
| Use when | You need runtime choice and mixed collections (the usual OOP case) | Hot loops where performance matters, with types fixed at compile time |

A third option (Tier 3): `std::variant<Circle, Square>` + `std::visit`, a **closed** set of types with no inheritance and value semantics. It's good when the set of types is fixed and you're adding operations rather than types.

### 3. Must remember

1. Virtual = runtime flexibility and mixed containers, at a small per-call cost.
2. CRTP and templates = zero overhead, but every type is fixed at compile time and there are no mixed containers.
3. The default for OOP design is virtual; CRTP is an optimisation.

---

## 6.10 Consolidation

### Must remember (module)

1. Pointer type = ownership statement. `unique_ptr` default; `shared_ptr` only for real sharing; `weak_ptr`/raw/reference for observing.
2. `make_unique` / `make_shared`; never two `shared_ptr`s from one raw pointer.
3. `unique_ptr`: move-only, zero overhead. `shared_ptr`: control block, atomic counts, two pointers in size.
4. `shared_ptr`'s count is thread-safe; the object isn't.
5. `shared_ptr` cycles leak; `weak_ptr` breaks them; `lock()` before use.
6. Pass `T&` to functions that only use the object; pass smart pointers only to transfer or share ownership.
7. Four casts. `dynamic_cast` needs a virtual function, gives nullptr for pointers and throws `bad_cast` for references. `static_cast` downcasts are unchecked.
8. `typeid` gives the dynamic type only for polymorphic types.
9. Many `dynamic_cast`/`typeid` branches = a missing virtual function (OCP violation).
10. Catch exceptions by `const&` (slicing!), derived types first.
11. Throwing constructor: no destructor for the object, members cleaned up; use RAII members.
12. Exception guarantees: no-throw, strong (copy-and-swap), basic.
13. CRTP = compile-time polymorphism: fast, but no heterogeneous containers.

### Common wrong answers (module)

- "`shared_ptr` is the safe default." `unique_ptr` is.
- "`shared_ptr` is thread-safe." Only its control block is.
- "Smart pointers can never leak." Cycles can.
- "`weak_ptr` can be dereferenced." Only after `lock()`.
- "`dynamic_cast` works on any class." It needs a polymorphic type.
- "Catch by value is fine." It slices.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What are smart pointers? | RAII wrappers that own heap objects and delete them automatically | Which three? |
| `unique_ptr` vs `shared_ptr`? | Exclusive and move-only with zero overhead vs shared, reference-counted with a control block | When `shared_ptr`? |
| What is `weak_ptr` for? | Non-owning observation; breaking `shared_ptr` cycles | Show the cycle |
| Why `make_shared`? | One allocation instead of two; exception-safe | Any downside? (Memory held while weak refs remain) |
| Is `shared_ptr` thread-safe? | The count is; the object isn't | |
| Types of casts? | static, dynamic, const, reinterpret | When does `dynamic_cast` fail? |
| `static_cast` vs `dynamic_cast`? | Compile-time, unchecked vs runtime-checked, polymorphic types only | Cost? |
| What is RTTI? | Runtime type info backing `dynamic_cast`/`typeid` | Can it be disabled? |
| Why catch by reference? | Avoids slicing and copying | Order of catch blocks? |
| What happens if a constructor throws? | No destructor for that object; built members destroyed | How to avoid leaks? |
| Exception-safety guarantees? | No-throw, strong, basic | Which idiom gives strong? |
| Static vs dynamic polymorphism? | Templates/CRTP at compile time vs virtual at runtime | Trade-offs |

### Practice: predict the output

**P1.**
```cpp
auto p = make_shared<int>(5);
cout << p.use_count() << " ";
{ auto q = p; cout << p.use_count() << " "; }
cout << p.use_count() << " ";
weak_ptr<int> w = p;
cout << p.use_count() << " " << w.expired() << " ";
p.reset();
cout << w.expired() << " " << (w.lock() == nullptr);
```
<details><summary>Answer</summary>

`1 2 1 1 0 1 1`. A `weak_ptr` doesn't change `use_count`. After `reset`, the int is destroyed, so `expired()` is true and `lock()` returns empty.
</details>

**P2.** What is printed at the end of each block, and why?
```cpp
struct Node{ string n; shared_ptr<Node> other; Node(string s):n(s){} ~Node(){cout<<"~"<<n<<" ";} };
{ auto a=make_shared<Node>("a"); auto b=make_shared<Node>("b"); a->other=b; b->other=a; cout<<a.use_count()<<" "; }
cout << "| ";
// same again, but with weak_ptr<Node> other;
```
<details><summary>Answer</summary>

`2 | 1 ~b ~a`. The `shared_ptr` cycle keeps both alive (count 2, then 1, never 0), so no destructors run. With `weak_ptr`, counts stay at 1, so both are freed: locals are destroyed in reverse order, so `b` first.
</details>

**P3.**
```cpp
struct A{ virtual ~A()=default; }; struct B:A{}; struct C:A{};
A* p = new B;
cout << (dynamic_cast<B*>(p) != nullptr) << (dynamic_cast<C*>(p) == nullptr);
try { (void)dynamic_cast<C&>(*p); } catch (const bad_cast&) { cout << " bad_cast"; }
```
<details><summary>Answer</summary>

`11 bad_cast`
</details>

**P4.**
```cpp
struct E{ virtual const char* what() const { return "E"; } virtual ~E()=default; };
struct F:E{ const char* what() const override { return "F"; } };
try{ throw F(); } catch(E e){ cout<<e.what()<<" "; }
try{ throw F(); } catch(const E& e){ cout<<e.what(); }
```
<details><summary>Answer</summary>

`E F`. Catch by value slices.
</details>

**P5.**
```cpp
struct M{ M(){cout<<"M ";} ~M(){cout<<"~M ";} };
struct T{ M m; int* raw; T(): raw(new int[10]) { cout<<"T-body "; throw runtime_error("x"); } ~T(){ cout<<"~T "; delete[] raw; } };
try { T t; } catch(...) { cout<<"caught"; }
```
What leaks, and how do you fix it?
<details><summary>Answer</summary>

`M T-body ~M caught`. `~T` never runs, so the `int[10]` leaks. Fix: `std::unique_ptr<int[]> raw;` or `std::vector<int> raw;`, which are fully constructed members and are cleaned up.
</details>

**P6.** Choose the right type for each and justify it: (a) a `Car` owns its `Engine`; (b) a `Document` cache shared by several editor windows, with no window outliving the others; (c) a `TreeNode`'s pointer to its parent; (d) a function `void render(??? shape)` that only draws the shape; (e) a factory `??? createShape(string type)`.

<details><summary>Answer</summary>

(a) `unique_ptr<Engine>` or a plain `Engine` member. (b) `shared_ptr<Document>`. (c) `weak_ptr<TreeNode>` (if nodes are shared_ptr-managed) or a raw `TreeNode*`. (d) `const Shape&`. (e) `unique_ptr<Shape>`.
</details>

---

## Exit checklist

```
[ ] I can list the problems with raw owning pointers
[ ] I can explain unique_ptr (move-only, zero overhead) and use make_unique
[ ] I can explain shared_ptr's control block and why make_shared is preferred
[ ] I can draw the shared_ptr cycle and fix it with weak_ptr + lock()
[ ] I can choose the right pointer type for a given ownership situation
[ ] I know how to pass smart pointers (reference unless transferring or sharing ownership)
[ ] I can compare the four casts and state dynamic_cast's failure behaviour
[ ] I can explain why dynamic_cast chains are a design smell
[ ] I know typeid gives the dynamic type only for polymorphic types
[ ] I catch by const& and can explain why
[ ] I can name the three exception-safety guarantees
[ ] I can compare CRTP with virtual dispatch
[ ] P1–P6 done
```

---

## Next

**Part 9: M7 — SOLID and Design Principles.** Each of the five principles is shown as a broken C++ design, then the fix, then a one-line interview answer. It also covers DRY, KISS, YAGNI, the Law of Demeter, and how SOLID shows up in LLD rounds.
