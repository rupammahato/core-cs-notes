# OOP Placement Handbook (C++) — Part 3
# Module 1: Constructors, Destructors, and Copying

**Module 1 · 3–4 hours · Tier 1 · Requires: M0**

---

## Why this module is the most C++-specific one

Java and Python interviews barely touch this material, because their garbage collectors make destructors and copying someone else's problem. C++ interviews lean on it heavily, for one reason: **in C++ the programmer owns the lifetime of every resource**. Constructors acquire resources, destructors release them, and copying decides whether two objects end up fighting over the same resource.

Most C++ output-prediction questions come from this module: which constructor runs, in what order, and how many times.

The organising principle:

> **An object's lifetime is a contract: the constructor establishes the invariant and acquires resources; the destructor releases them. Copying must preserve that contract, so that each object still owns its own resources. Every rule in this module (deep copy, rule of three, RAII) exists to keep that contract intact.**

---

## 1.1 What a constructor is

### 1. What is it?

A special member function that runs automatically when an object is created. Its job is to put the object into a valid state.

### 2. Why does it exist?

Without constructors, every object would start as raw memory and every user would have to remember to call `init()`. One forgotten call means an object with garbage fields. A constructor makes initialisation impossible to skip.

### 3. Properties (asked as a list)

| Property | Answer | Reason |
|---|---|---|
| Name | Same as the class | That's how the compiler identifies it |
| Return type | **None**, not even `void` | It creates an object; it doesn't compute a value |
| Called | Automatically on creation | Initialisation can't be forgotten |
| Can be overloaded | **Yes** | Several ways to create an object |
| Can have default arguments | Yes | |
| Can be `private` | **Yes** | Singleton, factory functions, non-instantiable classes (M8) |
| Can be `virtual` | **No** | See §1.13 |
| Can be `static` / `const` | No | It works on a specific object that is still being built |
| Inherited | **Not by default** | `using Base::Base;` (C++11) opts in |
| Can throw | **Yes** | It's the only way a constructor can report failure (§1.13) |
| Address can be taken | No | |

### 4. Must remember

1. No return type at all. `void A()` is a regular function named `A`, not a constructor.
2. Private constructors are legal and useful.
3. Constructors cannot be virtual.

---

## 1.2 Types of constructors

### 1. The catalogue

```cpp
class Student {
    string name;
    int roll;
public:
    Student() : name("unknown"), roll(0) {}                     // 1. default
    Student(string n, int r) : name(n), roll(r) {}              // 2. parameterised
    Student(const Student& o) : name(o.name), roll(o.roll) {}   // 3. copy
    Student(Student&& o) noexcept                                // 4. move (C++11)
        : name(std::move(o.name)), roll(o.roll) {}
    Student(string n) : Student(n, -1) {}                       // 5. delegating (C++11)
};
// 6. conversion constructor: any constructor callable with ONE argument,
//    e.g. Student(string n) above, also acts as an implicit string -> Student conversion (§1.11)
```

| Type | Signature shape | Runs when |
|---|---|---|
| **Default** | `X()` or all parameters defaulted | `X a;`, `X a{};`, `new X`, array elements, members without an initialiser |
| **Parameterised** | `X(args...)` | `X a(1, 2);` |
| **Copy** | `X(const X&)` | A new object is created from an existing **lvalue** (§1.6) |
| **Move** | `X(X&&)` | A new object is created from an **rvalue** (a temporary, or `std::move(x)`) (§1.10) |
| **Delegating** | `X(...) : X(other args) {}` | Reuses another constructor of the same class |
| **Conversion** | Callable with one argument, not `explicit` | Implicit conversion from that argument type (§1.11) |

### 2. When does the compiler generate a default constructor?

**Only if you declare no constructor at all.** Declaring *any* constructor, even a parameterised one, suppresses it:

```cpp
class A { public: A(int x) {} };
A a;            // COMPILE ERROR: no default constructor
A b(5);         // fine

class B { public: B(int x) {} B() = default; };   // fix: ask for it back explicitly
```

This is one of the most common compile errors in output-prediction questions.

### 3. What does the generated default constructor do?

It default-initialises each member: class-type members get their own default constructor, but **built-in members (`int`, pointers) are left with garbage values** unless they have a default member initialiser (`int x = 0;`).

```cpp
struct P { int x; string s; };
P p1;          // p1.x is GARBAGE, p1.s is ""
P p2{};        // value-initialisation: p2.x is 0, p2.s is ""
```

Using default member initialisers (`int x = 0;`) avoids this class of bugs entirely.

### 4. Must remember

1. Any user-declared constructor suppresses the implicit default constructor.
2. The implicit default constructor leaves built-in members uninitialised.
3. `= default` brings back the compiler's version; `= delete` forbids one (§1.12).
4. Delegating constructors (C++11) remove duplication: one "master" constructor, the others forwarding to it.

---

## 1.3 Initialiser lists

### 1. What is it?

The `: member(value), ...` part between the constructor's signature and its body. It **initialises** members, whereas assignment in the body **overwrites** members that have already been initialised.

### 2. Why does it matter?

```cpp
class Person {
    string name;
public:
    Person(string n) { name = n; }       // name default-constructed to "", THEN assigned
    Person(string n) : name(n) {}        // name constructed ONCE, directly with n
};
```

The body version does two operations and the list version does one. For a `string` that is a minor inefficiency. For some members the body version **cannot compile at all**.

### 3. When the initialiser list is mandatory

| Member kind | Why assignment in the body can't work |
|---|---|
| `const` member | A const can't be assigned after creation |
| Reference member (`int& r`) | A reference must be bound when it's created and can't be re-bound |
| Member of a class type **without a default constructor** | The compiler would need to default-construct it before the body runs |
| **Base class** without a default constructor (M3) | Same reason, for the base sub-object |

```cpp
class Config {
    const int maxUsers;
    int& counter;
    Student owner;                  // Student has no default constructor (say)
public:
    Config(int m, int& c, Student s)
        : maxUsers(m), counter(c), owner(s) {}      // the only way
};
```

### 4. The order trap (a classic)

**Members are initialised in the order they are declared in the class, not the order you write them in the initialiser list.**

```cpp
class Range {
    int lo;                          // declared FIRST
    int hi;                          // declared SECOND
public:
    Range(int x) : hi(x), lo(hi - 10) {}     // looks fine...
};
Range r(100);    // lo = garbage - 10 (undefined behaviour!), hi = 100
```

`lo` is initialised first, using `hi`, which hasn't been initialised yet. GCC and Clang warn about this with `-Wreorder` (enabled by `-Wall`). The fix is to write the list in declaration order and never make one member's initialiser depend on a later member.

### 5. Must remember

1. Four mandatory cases: **const members, reference members, members without a default constructor, bases without a default constructor**.
2. Initialisation order = **declaration order**, always.
3. Prefer the initialiser list for every member. It is never worse and often required.
4. Default member initialisers (`int x = 0;` in the class) apply when a constructor's list doesn't mention that member.

---

## 1.4 Destructors

### 1. What is it?

A special member function, `~ClassName()`, that runs automatically when an object's lifetime ends. Its job is to release whatever the object acquired: memory, file handles, locks, sockets.

### 2. When does it run?

| Object kind | Destructor runs |
|---|---|
| Local (stack) object | At the closing `}` of its scope, in **reverse order of construction** |
| Heap object | When you call `delete` (never automatically) |
| Global / namespace-scope object | After `main` returns, in reverse order of construction |
| `static` local object | After `main` returns, in reverse order of construction |
| Temporary | At the end of the full expression that created it (with lifetime-extension exceptions) |
| Member / base sub-object | After the owning object's destructor body finishes |
| Array elements | Last element first |

### 3. Properties

| Property | Answer |
|---|---|
| Parameters | **None** |
| Overloadable | **No**: exactly one destructor per class |
| Return type | None |
| Can be `virtual` | **Yes**, and it must be for polymorphic base classes (M4) |
| Can be `private` | Yes (rare; forces objects onto the heap or controls deletion) |
| Can throw | It shouldn't. Destructors are implicitly `noexcept` since C++11, so a throw calls `std::terminate` |
| Can be called explicitly | Yes, `obj.~X()`, but only with placement new; otherwise you get a double destruction |
| Generated by the compiler | Yes, if you don't declare one; it destroys members and bases |

### 4. Why destructors must not throw

If a destructor throws during **stack unwinding**, while another exception is already propagating, C++ has two exceptions in flight and no way to handle both. It calls `std::terminate`. Since C++11, destructors are `noexcept` by default, so *any* exception escaping a destructor terminates the program. Catch and log inside the destructor if cleanup can fail.

### 5. Must remember

1. One destructor, no parameters, no overloading.
2. Stack objects are destroyed in **reverse** order of construction.
3. Heap objects are destroyed only by `delete`. Forgetting it leaks the memory *and* skips the destructor.
4. Never let an exception escape a destructor.
5. Polymorphic base class ⇒ virtual destructor (full explanation in M4).

---

## 1.5 Order of construction and destruction

This is the engine of most output-prediction questions.

### 1. The rules

**Construction of one object:**
1. Base classes (M3), in the order they are listed in the class declaration
2. Data members, in **declaration order**
3. The constructor **body**

**Destruction is exactly the reverse:**
1. The destructor **body**
2. Data members, in **reverse** declaration order
3. Base classes, in reverse order

**Across objects:** locals are destroyed in reverse order of construction. Globals are constructed before `main` and destroyed after it. Static locals are constructed the first time control reaches them and destroyed after `main`, interleaved with globals in reverse order of construction.

### 2. Trace: members

```cpp
struct M {
    string n;
    M(string s) : n(s) { cout << "M" << n << " "; }
    ~M()               { cout << "~M" << n << " "; }
};
struct X {
    M a{"1"};
    M b{"2"};
    X()  { cout << "X "; }
    ~X() { cout << "~X "; }
};
int main() { X x; }
```

**Output:** `M1 M2 X ~X ~M2 ~M1`

Members are built before the body runs, so the body can use them. On destruction the body runs first, while the members are still alive, and then the members are destroyed in reverse.

**Why this order?** Each step can rely on everything built before it. The constructor body can use the members, and the destructor body can still use them because they're destroyed only afterwards.

### 3. Trace: globals, statics, locals

```cpp
struct T {
    string n;
    T(string s) : n(s) { cout << "+" << n << " "; }
    ~T()               { cout << "-" << n << " "; }
};
T g("G");
void f() { static T s("S"); T l("L"); }
int main() { cout << "main "; f(); f(); cout << "end "; }
```

**Output:** `+G main +S +L -L +L -L end -S -G`

| Line | Why |
|---|---|
| `+G` before `main` | Globals are constructed before `main` starts |
| `+S` once | Static local, constructed on the *first* call only |
| `+L -L` twice | Ordinary local, created and destroyed on each call |
| `-S` before `-G` | After `main`: reverse order of construction (S was built after G) |

### 4. Must remember

1. Bases → members (declaration order) → body. Destruction is the mirror image.
2. Static locals are constructed **once**, lazily, on first use.
3. Globals and statics are destroyed after `main`, in reverse construction order.
4. The *static initialisation order fiasco*: the order of globals across **different .cpp files** is unspecified, so one global's constructor must not use a global from another file. A function-local static fixes it (Meyers Singleton, M8).

---

## 1.6 The copy constructor

### 1. What is it?

The constructor that creates a **new** object as a copy of an existing one: `X(const X& other)`.

### 2. When is it called? (a frequent interview question)

| Situation | Example |
|---|---|
| Initialising a new object from an existing one | `X b = a;` or `X b(a);` or `X b{a};` |
| Passing an object **by value** | `void f(X x); f(a);` |
| Returning an object **by value** | `X g() { X t; return t; }`, unless elided (§1.14) |
| Copying into a container | `v.push_back(a);` with `a` an lvalue |
| Throwing or catching by value | `catch (X e)` |

**Not called** for `b = a;` when `b` already exists. That's the **copy assignment operator** (§1.8). **`X b = a;` uses the copy constructor despite the `=`**, which is the classic trick question.

### 3. Why must the parameter be a reference?

```cpp
X(X other);        // ill-formed: the compiler rejects it
```

To pass `other` by value, C++ would have to copy the argument, which means calling the copy constructor, which takes its parameter by value, which means copying again, forever. **Infinite recursion.** The language makes this signature a compile error.

### 4. Why `const`?

1. It lets you copy **const objects**: `const X a; X b = a;` needs `const X&`.
2. It lets you copy from **temporaries** (rvalues), which bind to `const&` but not to a non-const `&`.
3. It documents, and the compiler enforces, that copying doesn't modify the source.

`X(X& other)` compiles, but it can't copy const objects. It's legal but wrong.

### 5. The implicit copy constructor

If you don't write one, the compiler generates one that copies **each member** (memberwise copy) using that member's own copy constructor. For an `int` or a pointer, that means copying the bits. This is perfectly correct for most classes, and **disastrous for classes that own a raw resource**, which is the subject of the next section.

### 6. Must remember

1. `X b = a;` is copy construction, not assignment.
2. The parameter must be a reference (by value would recurse infinitely, so it's a compile error), and should be `const`.
3. The default copy is a memberwise, **shallow** copy for pointers.
4. Pass by `const&` to avoid copies in function parameters.

---

## 1.7 Shallow copy vs deep copy (the centrepiece)

### 1. What is it?

- **Shallow copy:** copy the pointer. Both objects point to the **same** resource.
- **Deep copy:** allocate a **new** resource and copy the *contents*. Each object owns its own.

### 2. The bug, drawn out

```cpp
class Buffer {
    int* data;
    size_t n;
public:
    Buffer(size_t n) : data(new int[n]()), n(n) {}
    ~Buffer() { delete[] data; }
    // no copy constructor written -> compiler's shallow copy
};

int main() {
    Buffer a(3);
    Buffer b = a;          // shallow: b.data = a.data
}                          // b destroyed: delete[] data   (frees the array)
                           // a destroyed: delete[] data   (frees it AGAIN) -> UB, usually a crash
```

```
  after  Buffer b = a;  (shallow)

   a: [ data ●──┐  n=3 ]
                ├──────> heap: [0][0][0]
   b: [ data ●──┘  n=3 ]

   Problems:
   1. Double delete at destruction        -> undefined behaviour (crash, heap corruption)
   2. a.data[0] = 9  also changes b        -> unintended aliasing
   3. After one is destroyed, the other's pointer dangles
```

```
  after  Buffer b = a;  (deep)

   a: [ data ●── n=3 ] ──> heap: [0][0][0]
   b: [ data ●── n=3 ] ──> heap: [0][0][0]    <- separate copy
```

### 3. The fix: a deep-copy constructor

```cpp
Buffer(const Buffer& o) : data(new int[o.n]), n(o.n) {
    std::copy(o.data, o.data + n, data);
}
```

### 4. When do you need a deep copy?

**Exactly when the class owns a resource through a raw handle**: a raw pointer to heap memory it allocated, a file descriptor, a socket. If every member is a value type or a self-managing type (`int`, `string`, `vector`, `unique_ptr`), the default memberwise copy is already correct, because those members deep-copy themselves (or, for `unique_ptr`, refuse to be copied).

This is why `vector` and `string` are so useful: they do the deep copy for you.

### 5. Comparison

| | Shallow copy | Deep copy |
|---|---|---|
| What is copied | Pointer values (addresses) | The pointed-to data, into new memory |
| Objects share data | Yes | No |
| Default in C++ | Yes (memberwise copy) | No, you must write it |
| Cost | O(1) | O(size of data) |
| Danger | Double free, dangling pointer, aliasing | None if written correctly |
| Correct when | No owned raw resources, or sharing is intended (and reference-counted) | The class owns a raw resource |

### 6. Common wrong answers

- "Shallow copy copies only some members." No: it copies **all** members, but copies pointers as addresses.
- "C++ does a deep copy by default." No.
- "Deep copy is always better." It costs time and memory. Sometimes sharing is intended, and then you want reference counting (`shared_ptr`, M6), not two independent copies.

### 7. Interview questions

- *"Shallow vs deep copy?"* Shallow copies the pointer, so both objects share the resource. Deep copies the resource itself, so each owns its own. The default copy constructor is shallow for pointer members, which causes a double free if both destructors delete the memory. *Follow-up: "How do you avoid writing deep copies?"* Don't own raw resources. Use `vector`, `string` or smart pointers, and the defaults become correct (the rule of zero, §1.9).

---

## 1.8 Copy assignment operator

### 1. What is it?

`X& operator=(const X& other)`, called when an **already existing** object is given another object's value: `b = a;`.

### 2. Why is it harder than the copy constructor?

The copy constructor fills a blank object. The assignment operator overwrites a **live** object that already owns resources, so it must:

1. **Release** the old resource, or it leaks.
2. **Handle self-assignment** (`a = a;`), because freeing first would destroy the very data you're about to copy.
3. **Return `*this` by reference**, to allow chaining (`a = b = c;`).

### 3. The safe version

```cpp
Buffer& operator=(const Buffer& o) {
    if (this != &o) {                          // 1. self-assignment guard
        int* fresh = new int[o.n];             // 2. allocate FIRST (if this throws,
        std::copy(o.data, o.data + o.n, fresh);//    *this is still intact)
        delete[] data;                         // 3. then release the old resource
        data = fresh;
        n = o.n;
    }
    return *this;                              // 4. enable chaining
}
```

Allocating before deleting gives you **exception safety**: if `new` throws, the object is unchanged.

### 4. The copy-and-swap idiom (the elegant answer)

```cpp
Buffer& operator=(Buffer o) {      // parameter BY VALUE: the copy constructor does the copying
    std::swap(data, o.data);       // take o's fresh buffer
    std::swap(n, o.n);
    return *this;
}                                  // o's destructor frees our OLD buffer
```

It is self-assignment safe, exception safe, and reuses the copy constructor and destructor, so there's no duplicated logic. Mention it by name in interviews.

### 5. Copy constructor vs copy assignment

| | Copy constructor | Copy assignment operator |
|---|---|---|
| Signature | `X(const X&)` | `X& operator=(const X&)` |
| Target object | **New**, being created | **Existing**, already initialised |
| Must release old resources | No (there are none) | **Yes** |
| Self-assignment check | Not possible / not needed | **Needed** (or use copy-and-swap) |
| Returns | Nothing | `*this` by reference |
| Triggered by | `X b = a;`, `X b(a);`, pass/return by value | `b = a;` with `b` already existing |

### 6. Must remember

1. `X b = a;` → constructor. `b = a;` → assignment.
2. Assignment = free old + copy new + guard self-assignment + return `*this`.
3. Allocate the new resource **before** freeing the old one.
4. Copy-and-swap handles everything in three lines.

---

## 1.9 The rule of three, five, and zero

### 1. Rule of three

> **If a class needs a user-written destructor, copy constructor, or copy assignment operator, it almost certainly needs all three.**

Why: needing any one of them means the class manages a resource by hand. The destructor frees it, so the copy operations must deep-copy it, or two objects will free the same resource.

### 2. Rule of five (C++11)

Add the **move constructor** and **move assignment operator**. If you write the three, also write the two moves. Otherwise moves silently fall back to copies, and the class works but is slower (see the table below).

### 3. Rule of zero (the modern goal)

> **Write none of the five.** Make every member manage itself (`vector`, `string`, `unique_ptr`, `shared_ptr`), and the compiler-generated versions are automatically correct.

```cpp
// Rule of five: manual, error-prone
class Buffer { int* data; size_t n; /* + 5 special members */ };

// Rule of zero: no special members needed at all
class Buffer { std::vector<int> data; };
```

**The interview line:** *"Rule of zero is what I'd write in practice; rule of three or five is what I'd write if I had to manage a raw resource myself."*

### 4. What the compiler generates, and when

| You declare... | Default ctor | Copy ctor / copy assign | Move ctor / move assign | Destructor |
|---|---|---|---|---|
| Nothing | Generated | Generated | Generated | Generated |
| Any constructor | **Not generated** | Generated | Generated | Generated |
| Destructor | Generated | Generated (deprecated behaviour) | **Not declared** → moves fall back to copies | — |
| Copy ctor or copy assign | Not generated (if copy ctor) | — | **Not declared** → moves fall back to copies | Generated |
| Move ctor or move assign | Not generated (if move ctor) | **Deleted** | — | Generated |

The two rows to remember: **declaring a destructor or a copy operation silently disables the implicit moves**, and **declaring a move operation deletes the implicit copies**.

### 5. Must remember

1. Three: destructor, copy constructor, copy assignment.
2. Five: plus move constructor and move assignment.
3. Zero: use self-managing members and write none.
4. Writing a destructor silently removes the implicit moves.

---

## 1.10 Move semantics (essentials only)

### 1. What is it?

Transferring a resource from an object that's about to die, instead of copying it. Moving a vector of a million elements copies three pointers instead of a million ints.

### 2. Lvalues and rvalues (just enough)

| | lvalue | rvalue |
|---|---|---|
| Meaning | Has a name / an identity; you can take its address | A temporary, about to disappear |
| Examples | `a`, `v[0]`, `*p` | `Buffer(5)`, `a + b`, `f()` returning by value, `std::move(a)` |
| Binds to | `T&` and `const T&` | `T&&` and `const T&` |

### 3. The move constructor

```cpp
Buffer(Buffer&& o) noexcept : data(o.data), n(o.n) {   // steal the pointer
    o.data = nullptr;                                   // leave the source empty but valid
    o.n = 0;
}
```

The source must be left **destructible**: `delete[] nullptr` is a safe no-op, so its destructor does nothing harmful.

### 4. `std::move` doesn't move

`std::move(x)` is just a **cast** to an rvalue reference. It says "you may steal from `x`". The actual stealing happens only if the receiving type has a move constructor or move assignment. After a move, `x` is in a **valid but unspecified** state: you may assign to it or destroy it, but don't read its value.

```cpp
string a = "hello";
string b = std::move(a);   // b == "hello"; a is valid but unspecified (in practice usually "")
```

### 5. Why `noexcept` matters

When a `vector` grows, it must transfer its elements to new memory. If the element's move constructor might throw, a throw halfway through would leave the elements split between two buffers with no way back. So `vector` **copies** instead, unless the move constructor is `noexcept`. Forgetting `noexcept` on a move constructor quietly makes `vector<YourType>` slower.

### 6. Must remember

1. Move = steal the resource, then null out the source.
2. `std::move` is a cast; it moves nothing by itself.
3. A moved-from object is valid but unspecified: only assign to it or destroy it.
4. Mark move constructors and move assignment `noexcept`.

---

## 1.11 `explicit` and conversion constructors

### 1. The problem

Any constructor callable with one argument doubles as an **implicit conversion**:

```cpp
class Buffer {
public:
    Buffer(size_t n);          // also an implicit size_t -> Buffer conversion
};
void process(const Buffer& b);

process(42);                   // compiles! silently builds a 42-element Buffer
Buffer b = 10;                 // compiles too
```

That's almost never what the caller meant.

### 2. The fix

```cpp
class Buffer {
public:
    explicit Buffer(size_t n);
};
process(42);                   // compile error: good
process(Buffer(42));           // fine: the intent is now visible
Buffer b = 10;                 // compile error
Buffer c(10);                  // fine
```

### 3. Must remember

1. **Mark single-argument constructors `explicit` by default.** Leave a constructor implicit only when the conversion is genuinely natural (for example, a `BigInt` built from an `int`).
2. The copy and move constructors are not marked explicit.
3. `explicit` also applies to conversion operators: `explicit operator bool() const`.

---

## 1.12 `= default` and `= delete`

```cpp
class FileHandle {
    int fd;
public:
    explicit FileHandle(const char* path);
    ~FileHandle();

    FileHandle(const FileHandle&) = delete;              // non-copyable:
    FileHandle& operator=(const FileHandle&) = delete;   // two owners of one fd would be a bug

    FileHandle(FileHandle&&) noexcept;                   // but movable: ownership transfers
    FileHandle& operator=(FileHandle&&) noexcept;
};

class Point {
public:
    Point(int x, int y);
    Point() = default;                                   // bring back the default constructor
};
```

| | `= default` | `= delete` |
|---|---|---|
| Meaning | "Generate the compiler's version" | "This function must not be callable" |
| Typical use | Bring back a default constructor suppressed by another constructor; make a default explicit | Make a class **non-copyable**; block unwanted overloads (`void f(double) = delete;`) |
| Before C++11 | Not available | Declare the function private and never define it |

**Non-copyable but movable** is the pattern for every unique owner: `unique_ptr`, `thread`, `fstream`, `mutex` (a mutex is not even movable).

---

## 1.13 Constructor and destructor trick questions

### Can a constructor be virtual?

**No.** Virtual dispatch looks up the function through the object's vptr, but the vptr is set up *by* the constructor, so it doesn't exist yet. More fundamentally, to construct something you must already know its exact type, and virtual dispatch is for when you don't. If you need "virtual construction", use a factory (M8) or a virtual `clone()` method (M4).

### Can a destructor be virtual?

**Yes**, and it **must** be in any class meant to be deleted through a base pointer. Full explanation in M4.

### Can a constructor throw? What happens?

Yes; it's the standard way to report that an object couldn't be created. If it throws:
- The object is **never considered constructed**, so **its destructor does not run**.
- Members and bases that were **already fully constructed are destroyed**, in reverse order.
- Memory from `new X` is freed automatically.

The danger is a raw resource acquired in the constructor body before the throw: nothing releases it. The fix is to hold every resource in an RAII member (§1.15), so that member's destructor runs.

### Can a destructor throw?

It shouldn't. Destructors are implicitly `noexcept`, so an escaping exception calls `std::terminate` (§1.4).

### Can you call a constructor explicitly?

`X(5)` creates a temporary object; it doesn't re-run a constructor on an existing one. Constructing an object in memory you already have is done with *placement new* (`new (ptr) X(5)`), which is outside placement scope.

### Can a class have a private destructor?

Yes. Then objects can't be created on the stack (the compiler couldn't destroy them at scope end), so they must be created on the heap and destroyed through a member or friend function. It's rare; mention it only if asked.

---

## 1.14 Copy elision (why output questions can surprise you)

The compiler is allowed, and since C++17 in some cases **required**, to skip copies and moves entirely by building the object directly in its final location.

```cpp
struct A {
    A()           { cout << "D "; }
    A(const A&)   { cout << "C "; }
    A(A&&)        { cout << "M "; }
};
A make()  { return A(); }        // returning a temporary (prvalue)
A make2() { A t; return t; }     // returning a named local

int main() {
    A x = make();    // C++17: prints "D " only. Elision is GUARANTEED for prvalues.
    A y = make2();   // usually "D " only (NRVO). Permitted, NOT guaranteed; without it: "D M "
}
```

| Case | Name | C++17 status |
|---|---|---|
| `return A();` / `A a = A();` | RVO / prvalue elision | **Guaranteed**; the copy and move constructors aren't even needed |
| `A t; return t;` | NRVO (named return value optimisation) | Allowed, almost always done, not guaranteed |

**For output questions:** if a question returns by value and asks how many times the copy constructor prints, the precise answer is "with C++17 and a normal compiler, zero for a returned temporary; zero for a named local in practice, due to NRVO; one copy or move if elision is disabled with `-fno-elide-constructors`". Interviewers who set these questions usually accept "zero, due to RVO", and naming the optimisation earns credit.

---

## 1.15 RAII

### 1. What is it?

**Resource Acquisition Is Initialisation.** Tie every resource to an object's lifetime: acquire it in the constructor and release it in the destructor. Then the resource is released automatically when the object goes out of scope, **including when an exception is thrown**.

### 2. Why does it exist?

```cpp
void bad() {
    mtx.lock();
    doWork();             // if this throws, unlock() never runs -> deadlock forever
    mtx.unlock();
}

void good() {
    std::lock_guard<std::mutex> g(mtx);   // locks in constructor
    doWork();                              // if this throws...
}                                          // ...g's destructor still unlocks during stack unwinding
```

Destructors of stack objects run during **stack unwinding**, so cleanup is guaranteed however the scope is left: by normal return, early return or exception. C++ has no `finally` and doesn't need one.

### 3. RAII in the standard library

| Resource | RAII type |
|---|---|
| Heap memory | `unique_ptr`, `shared_ptr`, `vector`, `string` |
| Mutex lock | `lock_guard`, `unique_lock`, `scoped_lock` |
| File | `ifstream`, `ofstream` |
| Thread | `jthread` (C++20) joins in its destructor |

### 4. Must remember

1. Constructor acquires, destructor releases.
2. It works because stack destructors always run, including during exception unwinding.
3. RAII is *why* C++ doesn't need garbage collection for most code, and why it doesn't need `finally`.
4. RAII + rule of zero = classes that are leak-free with no special member functions written.

### 5. Interview question

- *"What is RAII?"* Binding a resource's lifetime to an object: acquire in the constructor, release in the destructor. Stack objects are always destroyed when their scope ends, even when an exception is thrown, so the resource can't leak. Examples: `lock_guard` for mutexes, `unique_ptr` for memory. *Follow-up: "How does Java handle this?"* Java's GC handles memory, but it doesn't run destructors deterministically, so other resources need try-with-resources or `finally`. RAII covers *every* resource deterministically.

---

## 1.16 Consolidation

### Must remember (module)

1. Constructors: no return type; can be overloaded and private; **not** virtual.
2. Declaring any constructor suppresses the implicit default constructor.
3. The implicit default constructor leaves `int`s and pointers uninitialised.
4. Initialiser list is mandatory for const members, references, members without a default constructor, and bases without one.
5. Members are initialised in **declaration order**, whatever the list order.
6. Construction: bases → members → body. Destruction: body → members (reverse) → bases (reverse).
7. Static locals: constructed once, on first use; destroyed after `main`.
8. `X b = a;` is the **copy constructor**; `b = a;` is **assignment**.
9. The copy constructor's parameter must be a reference (by value recurses infinitely); make it `const`.
10. Default copy is memberwise, so it is **shallow** for raw pointers → double free.
11. Copy assignment: self-assignment guard, allocate before free, return `*this`. Or copy-and-swap.
12. Rule of three → five → **zero**.
13. Declaring a destructor or copy operation disables the implicit moves.
14. `std::move` is a cast. Moved-from objects are valid but unspecified. Mark moves `noexcept`.
15. `explicit` on single-argument constructors.
16. Destructors must not throw; they are `noexcept` by default.
17. A throwing constructor means the destructor doesn't run, but already-built members are destroyed.
18. C++17 guarantees elision for prvalues; NRVO is optional.
19. RAII: acquire in the constructor, release in the destructor, guaranteed by stack unwinding.

### Common wrong answers (module)

- "`X b = a;` calls the assignment operator."
- "The default copy constructor does a deep copy."
- "A constructor can return a value / has void return type."
- "Constructors can be virtual."
- "Members are initialised in the order of the initialiser list."
- "`std::move` moves the object."
- "If the constructor throws, the destructor cleans up."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is a constructor? | Special function, same name as the class, no return type, runs on creation to make the object valid | Can it be virtual? (No; the vptr doesn't exist yet and the type must be known) |
| Types of constructors? | Default, parameterised, copy, move, delegating; any single-argument one is also a conversion constructor | When is the default generated? |
| When is the copy constructor called? | New object from an existing one; pass by value; return by value (unless elided) | Why is its parameter a reference? |
| Why a reference parameter? | By value would need a copy to make the copy, so infinite recursion, so it's ill-formed | Why const? |
| Shallow vs deep copy? | Pointer copied vs pointee copied; shallow causes double free | How to avoid writing it? (Rule of zero) |
| Copy constructor vs assignment? | Creates a new object vs overwrites an existing one (free old, self-check, return `*this`) | What is copy-and-swap? |
| Rule of three? | Need one of destructor, copy constructor, copy assignment → need all three | Rule of five, rule of zero |
| When is an initialiser list required? | const, reference, no-default-constructor member, base without default constructor | What order are members initialised in? |
| Destructor overloadable? Can it throw? | No; it shouldn't (`noexcept`, so terminate) | Virtual destructor (M4) |
| What happens if a constructor throws? | Destructor not called; built members destroyed; memory freed | How do you prevent leaks? (RAII members) |
| What is RAII? | Resource lifetime bound to object lifetime | Examples, and the Java comparison |
| What does `explicit` do? | Blocks implicit conversion through a one-argument constructor | Example of a bug it prevents |
| What is move semantics? | Steal resources from rvalues instead of copying | Why `noexcept`? |

### Practice: predict the output or the error

**P1.**
```cpp
struct A {
    A()                  { cout << "D "; }
    A(const A&)          { cout << "C "; }
    A& operator=(const A&) { cout << "A "; return *this; }
};
void f(A x) {}
void g(A& x) {}
int main() { A a; A b = a; A c; c = a; f(a); g(a); }
```
<details><summary>Answer</summary>

`D C D A C`. `a`→D. `b = a` at declaration→C. `c`→D. `c = a`→A. `f(a)` by value→C. `g(a)` by reference→nothing.
</details>

**P2.**
```cpp
class B { public: B(int x) {} };
int main() { B b; }
```
<details><summary>Answer</summary>

**Compile error.** The user-declared `B(int)` suppresses the implicit default constructor.
</details>

**P3.**
```cpp
struct N { string s; N(string x):s(x){cout<<s;} ~N(){cout<<"~"<<s;} };
struct H { N b{"b"}; N a{"a"}; H(){cout<<"H";} ~H(){cout<<"~H";} };
int main(){ H h; cout << "|"; }
```
<details><summary>Answer</summary>

`baH|~H~a~b`. Members are built in declaration order (b, then a), and destroyed in reverse after the destructor body.
</details>

**P4.**
```cpp
class R { int x; int y; public: R(int v) : y(v), x(y * 2) {} void p(){cout<<x<<" "<<y;} };
int main() { R r(5); r.p(); }
```
<details><summary>Answer</summary>

`x` is garbage (undefined behaviour), `y` is 5. `x` is declared first, so it's initialised first, from the uninitialised `y`.
</details>

**P5.** What happens?
```cpp
class S { char* p; public: S(const char* s){ p = new char[strlen(s)+1]; strcpy(p, s);} ~S(){ delete[] p; } };
int main() { S a("hi"); S b = a; }
```
<details><summary>Answer</summary>

Undefined behaviour: **double delete**. The implicit copy constructor copies the pointer, and both destructors `delete[]` the same memory. Fix: rule of three (deep-copy constructor + assignment), or better, use `std::string` (rule of zero).
</details>

**P6.**
```cpp
struct T { T(){cout<<"D ";} T(const T&){cout<<"C ";} T(T&&){cout<<"M ";} };
T make(){ return T(); }
int main(){ T x = make(); T y = std::move(x); }
```
<details><summary>Answer</summary>

`D M`. `make()` returns a prvalue, so C++17 guarantees elision (D only). `std::move(x)` makes an rvalue, so the move constructor runs.
</details>

**P7.**
```cpp
class V { public: explicit V(int n) {} };
void use(V v) {}
int main() { use(3); }
```
<details><summary>Answer</summary>

**Compile error.** The `explicit` constructor blocks the implicit int→V conversion. `use(V(3))` works.
</details>

**P8.**
```cpp
struct T { string n; T(string s):n(s){cout<<"+"<<n<<" ";} ~T(){cout<<"-"<<n<<" ";} };
T g1("G1");
int main() { T a("a"); { static T s("s"); T b("b"); } T c("c"); }
T g2("G2");
```
<details><summary>Answer</summary>

`+G1 +G2 +a +s +b -b +c -c -a -s -G2 -G1`. Globals in one file are built in definition order before `main`. `b` dies at its inner `}`. At the end of `main`: `c`, then `a`. After `main`: reverse order of construction among statics and globals. `s` was built last, so it goes first, then G2, then G1.
</details>

**P9.** Write `class IntArray` that owns a raw `int*` of size `n`, with a correct destructor, deep-copy constructor, and copy assignment using copy-and-swap. Then rewrite it following the rule of zero.

<details><summary>Answer</summary>

```cpp
class IntArray {
    int* d; size_t n;
public:
    explicit IntArray(size_t n) : d(new int[n]()), n(n) {}
    ~IntArray() { delete[] d; }
    IntArray(const IntArray& o) : d(new int[o.n]), n(o.n) { std::copy(o.d, o.d + n, d); }
    IntArray& operator=(IntArray o) { std::swap(d, o.d); std::swap(n, o.n); return *this; }
};

// Rule of zero:
class IntArray2 {
    std::vector<int> d;
public:
    explicit IntArray2(size_t n) : d(n) {}
};
```
</details>

---

## Exit checklist

```
[ ] I can list constructor properties (no return type, overloadable, private OK, not virtual)
[ ] I know when the default constructor is and is not generated
[ ] I can name the four cases that require an initialiser list
[ ] I know members initialise in declaration order and can spot the reorder bug
[ ] I can predict construction/destruction order for members, locals, statics and globals
[ ] I can list when the copy constructor runs, and explain why its parameter is const&
[ ] I can draw the shallow-copy double-free picture
[ ] I can write a deep-copy constructor and a safe copy assignment (and copy-and-swap)
[ ] I can state the copy constructor vs assignment table
[ ] I can explain rule of three, five and zero, and which defaults disable the moves
[ ] I can explain std::move as a cast and why move constructors should be noexcept
[ ] I know why constructors can't be virtual and destructors shouldn't throw
[ ] I can explain RAII with lock_guard as the example
[ ] P1–P9 done
```

---

## Next

**Part 4: M2 — Encapsulation and Abstraction.** It's short, but it settles the most-asked "difference between" question in OOP. It covers what encapsulation actually protects (invariants), why getters and setters alone are not encapsulation, abstraction at the design level, a precise abstraction vs encapsulation table, and friend functions and classes (including whether they break encapsulation).
