# OOP Placement Handbook (C++) — Part 6
# Module 4: Polymorphism

**Module 4 · 4–5 hours · Tier 1 · Requires: M0–M3**

---

## Why this is the centrepiece

Every OOP interview reaches polymorphism, and in C++ interviews the questions follow a predictable chain:

```
"What is polymorphism?"
   -> "Compile-time vs runtime?"
      -> "How is runtime polymorphism implemented?"          <- the vtable
         -> "What happens when you delete through a base pointer?"   <- virtual destructor
            -> "What is an abstract class? An interface?"
               -> trick questions (virtual in constructor, default arguments, ...)
```

Candidates who can draw the vtable and explain the virtual destructor clear the bar that separates product-company C++ rounds from service-company ones. This module is built around that chain.

The organising principle:

> **Polymorphism means one interface, many behaviours. In compile-time polymorphism the compiler picks the function from the static types it can see. In runtime polymorphism the choice is deferred to the moment of the call, and made by following a pointer stored inside the object (the vptr) to a table of the real class's functions (the vtable).**

---

## 4.1 What polymorphism is

### 1. What is it?

*Poly* = many, *morph* = form. The same name or interface behaves differently depending on the types involved.

### 2. Why does it exist?

To write code **once**, against a general interface, and have it work correctly for every specific type, **including types written later**:

```cpp
void renderAll(const vector<unique_ptr<Shape>>& shapes) {
    for (auto& s : shapes) s->draw();     // Circle draws a circle, Square a square
}
```

`renderAll` never changes when someone adds `Triangle`. Without polymorphism you'd have a `switch` on a type tag in every function that handles shapes, and every new shape would mean editing all of them.

### 3. The two kinds

| | Compile-time (static) | Runtime (dynamic) |
|---|---|---|
| Also called | Static binding, early binding | Dynamic binding, late binding, dynamic dispatch |
| Decided | By the compiler | When the call executes |
| Based on | Static types of the arguments | **Actual (dynamic) type of the object** |
| Mechanisms in C++ | Function overloading, operator overloading, templates | **Virtual functions** (with pointers or references) |
| Cost | Zero runtime cost; can be inlined | One indirect call through the vtable; usually not inlined |
| Flexibility | All types known at compile time | Works with types unknown when the calling code was compiled |
| Example | `print(int)` vs `print(string)` | `shape->area()` on a `Circle` vs a `Square` |

### 4. Real-world example (have one ready)

*A person behaves differently depending on context: as a customer in a shop, an employee at the office, a parent at home. Same person, same "respond" interface, different behaviour.* For code: *a `Notification` with `send()`, which sends an email, an SMS or a push notification depending on the actual object.*

---

## 4.2 Function overloading (compile-time)

### 1. What is it?

Several functions in the same scope with the **same name but different parameter lists**. The compiler picks one from the arguments at each call site.

```cpp
int    area(int side)              { return side * side; }
int    area(int l, int b)          { return l * b; }
double area(double r)              { return 3.14159 * r * r; }
```

### 2. What can and cannot distinguish overloads

| Can differ by | Cannot differ by only |
|---|---|
| Number of parameters | **Return type** |
| Types of parameters | Parameter *names* |
| Order of parameter types | Top-level `const` on a by-value parameter (`f(int)` vs `f(const int)` are the same) |
| `const` / `&` / `&&` qualification of a **member** function | A `typedef` / `using` alias of the same type |
| Pointer/reference to `const` vs non-const (`f(int&)` vs `f(const int&)`) | Default arguments |

**Why not return type alone?** In a call like `f(5);` with the result unused, the compiler would have nothing to choose with.

```cpp
int    f(int x);
double f(int x);     // ERROR: ambiguating new declaration of 'double f(int)'
```

### 3. Overload resolution (just enough)

The compiler ranks candidates by how much conversion each argument needs:

1. **Exact match** (including trivial ones like array → pointer)
2. **Promotion** (`char`/`short` → `int`, `float` → `double`, `bool` → `int`)
3. **Standard conversion** (`int` → `double`, `double` → `int`, `int` → `long`, derived pointer → base pointer)
4. **User-defined conversion** (via constructors or conversion operators)
5. Ellipsis (`...`)

If two candidates tie at the best level, the call is **ambiguous**, which is a compile error.

```cpp
void h(int);  void h(double);  void h(char);
h(5);       // int     (exact)
h(5.0f);    // double  (float -> double is a promotion)
h('a');     // char    (exact)

void k(int);  void k(long);
k('a');     // k(int)  (char -> int is a promotion; char -> long is only a conversion)
k(3.5);     // ERROR: ambiguous (double -> int and double -> long are both conversions)
```

### 4. How it works: name mangling

The compiler gives each overload a unique internal name that encodes its parameter types (with GCC, `area(int)` becomes `_Z4areai` and `area(int,int)` becomes `_Z4areaii`). The linker sees distinct names. This is also why C++ functions called from C need `extern "C"`, which turns mangling off. C has no overloading for exactly this reason.

### 5. Default arguments and ambiguity

```cpp
void g(int a, int b = 0);
void g(int a);
g(5);       // ERROR: ambiguous, both match exactly
```

### 6. Must remember

1. Overloads differ by **parameter list**, never by return type alone.
2. Resolution order: exact → promotion → conversion → user-defined; a tie means ambiguous.
3. Implemented by **name mangling**, so it costs nothing at runtime.
4. Overloads must be in the **same scope**. A derived-class function with the same name *hides* the base ones, it doesn't overload them (M3, §3.6).

---

## 4.3 Operator overloading (compile-time)

### 1. What is it?

Giving operators (`+`, `==`, `<<`, `[]`, ...) a meaning for user-defined types, so that they read naturally: `a + b` instead of `a.add(b)`.

### 2. Example

```cpp
class Complex {
    double re, im;
public:
    Complex(double r = 0, double i = 0) : re(r), im(i) {}

    Complex operator+(const Complex& o) const { return {re + o.re, im + o.im}; }   // member
    bool operator==(const Complex& o) const   { return re == o.re && im == o.im; }
    Complex& operator+=(const Complex& o)     { re += o.re; im += o.im; return *this; }

    friend ostream& operator<<(ostream& os, const Complex& c) {   // non-member friend
        return os << c.re << "+" << c.im << "i";
    }
};

Complex a(1, 2), b(3, 4);
cout << a + b;          // 4+6i   ->  a.operator+(b), then operator<<(cout, result)
```

`a + b` is literally `a.operator+(b)`, a function call with an operator spelling.

### 3. Member vs non-member

| Make it a member when... | Make it a non-member (often a friend) when... |
|---|---|
| The left operand is always your class | The **left operand is not your class**: `cout << x`, `2 * v` |
| It modifies the object: `+=`, `++`, `=` | You want **symmetric** conversions: with a member `operator+`, `c + 1` compiles but `1 + c` doesn't |
| The language **requires** it: `=`, `[]`, `()`, `->` | |

### 4. Rules (asked as a list)

| Rule | Detail |
|---|---|
| **Cannot overload** | `::`  `.`  `.*`  `?:`  `sizeof`  `typeid`  `alignof` and the cast keywords |
| Must be members | `=`  `[]`  `()`  `->` |
| Cannot create new operators | No `**` or `<>` |
| Cannot change precedence, associativity or arity | `a + b * c` still parses as `a + (b * c)` |
| At least one operand must be a user-defined type | You can't redefine `int + int` |
| Short-circuiting is lost | An overloaded `&&` or `\|\|` evaluates **both** operands, so avoid overloading them |

**Why can't `.` be overloaded?** `.` is how you reach members, including any overloaded operators. If `.` itself could be redefined, there'd be no reliable way left to access members.

### 5. Prefix vs postfix `++`

```cpp
struct Counter {
    int v;
    Counter& operator++()    { ++v; return *this; }                     // prefix: ++c
    Counter  operator++(int) { Counter old = *this; ++v; return old; }  // postfix: c++
};                                     // ^ dummy int parameter only distinguishes the two

Counter x{5};
Counter y = x++;    // y.v == 5, x.v == 6
Counter z = ++x;    // z.v == 7, x.v == 7
```

Prefix returns a reference to the updated object. Postfix returns a **copy of the old value**, so it costs an extra copy, which is why `++it` is preferred over `it++` for iterators.

### 6. Must remember

1. `a + b` ≡ `a.operator+(b)` or `operator+(a, b)`.
2. Can't overload: `::  .  .*  ?:  sizeof  typeid`.
3. `=`, `[]`, `()`, `->` must be members; `<<` for streams must be a non-member.
4. Postfix takes a dummy `int` and returns the old value by copy.
5. Keep the natural meaning. `+` shouldn't modify its operands; `==` should be symmetric.

---

## 4.4 Templates: the other compile-time polymorphism (brief)

```cpp
template <typename T>
T maxOf(T a, T b) { return a > b ? a : b; }

maxOf(3, 7);          // compiler generates maxOf<int>
maxOf(2.5, 1.5);      // compiler generates maxOf<double>
```

One piece of source, many behaviours, resolved at compile time: this is **parametric polymorphism**. Compared with virtual functions, templates are faster (no indirection, inlinable) but cause code bloat (one copy per type) and need every type to be known at compile time. Details of static vs dynamic polymorphism are in M6.

---

## 4.5 Runtime polymorphism: virtual functions

### 1. What is it?

A member function declared `virtual` in a base class is chosen at runtime according to the **actual type of the object**, when it's called through a base **pointer or reference**.

### 2. The two requirements

Dynamic dispatch happens only when **both** hold:
1. The function is `virtual` in the base.
2. It is called through a **pointer or reference** to the base.

Break either one and you get static binding.

### 3. Trace

```cpp
struct B {
    virtual void f() { cout << "B::f "; }
    void g()         { cout << "B::g "; }       // NOT virtual
    virtual ~B() = default;
};
struct D : B {
    void f() override { cout << "D::f "; }
    void g()          { cout << "D::g "; }       // hides B::g, doesn't override it
};

D d;
B* p = &d;   B& r = d;   B b = d;

p->f();      // D::f   virtual + pointer         -> dynamic type D
p->g();      // B::g   not virtual               -> static type B
r.f();       // D::f   virtual + reference       -> dynamic type D
b.f();       // B::f   an OBJECT, sliced (M3)    -> it really is a B
d.g();       // D::g   static type is D
p->B::f();   // B::f   explicit qualification turns OFF virtual dispatch
```

**Output:** `D::f B::g D::f B::f D::g B::f`

### 4. Static type vs dynamic type

| | Static type | Dynamic type |
|---|---|---|
| What | The declared type of the expression | The type of the object actually there at runtime |
| `B* p = new D;` | `B*` | `D` |
| Decides | Non-virtual calls, name lookup, access checks, **default arguments** | Virtual function calls |

### 5. Rules for overriding

- The function in the derived class must have the **same name, parameters and cv/ref-qualifiers**.
- The return type must be the same, or **covariant** (§4.14).
- `virtual` in the derived class is optional: once virtual, always virtual down the hierarchy.
- The access specifier can differ, but access is checked on the **static** type (§4.14).

### 6. Must remember

1. `virtual` + pointer/reference = dynamic dispatch. Missing either = static.
2. Calling through an **object** never dispatches dynamically.
3. `Base::f()` qualification forces the base version.
4. Once virtual, a function stays virtual in every derived class.

---

## 4.6 `override` and `final` (C++11)

### 1. `override`: catch silent mistakes

```cpp
struct B { virtual void f() const; };
struct D : B {
    void f();                // NOT an override: missing const, so this is a NEW function that hides B::f
    void f() override;       // ERROR: 'void D::f()' marked 'override', but does not override
};
```

Without `override`, a tiny signature mismatch (const, `int` vs `long`, a typo) silently creates a separate function, and polymorphism quietly stops working. With `override`, it's a compile error. **Always write `override`.**

### 2. `final`: stop further overriding or derivation

```cpp
struct B { virtual void f() final; };     // no class may override f further
struct D : B { void f() override; };      // ERROR: overriding final function

struct Leaf final {};                     // no class may derive from Leaf
struct X : Leaf {};                       // ERROR: cannot derive from 'final' base
```

Uses: protect an invariant-critical method, mark a class as a leaf, and let the compiler **devirtualise** calls (if `f` is final, `d.f()` through a `D*` can be a direct call).

### 3. Must remember

1. Write `override` on every override.
2. `final` on a function stops overriding; on a class it stops derivation.
3. Both are contextual keywords: they have special meaning only in those positions.

---

## 4.7 The vtable and vptr (the most important section)

### 1. The question

*"How is runtime polymorphism implemented in C++?"* The compiler sees only `p->f()` and a `B*`. How does the program find `D::f` at runtime?

### 2. The mechanism

> The C++ standard doesn't mandate vtables, but every major compiler uses them. Say "typically implemented with" in interviews.

**Two structures:**

1. **vtable (virtual table):** one per **class** that has virtual functions. It's a static array of function pointers, one slot per virtual function, holding the address of the version that class uses. It's built at **compile time** and stored in read-only static memory.
2. **vptr (virtual pointer):** one hidden pointer per **object**, typically the first member, pointing to its class's vtable. It's set by the **constructor**.

```cpp
struct Base {
    virtual void speak();      // slot 0
    virtual void move();       // slot 1
    void eat();                // non-virtual: not in the vtable
    int hp;
    virtual ~Base();
};
struct Dog : Base {
    void speak() override;     // overrides slot 0
    // move() not overridden   -> slot 1 keeps Base::move
    int tricks;
};
```

```
   OBJECTS (one vptr each)                 VTABLES (one per class, static memory)

   Base b                                  Base's vtable
   +-----------+                           +------------------+
   | vptr  ●---+-------------------------->| [0] &Base::speak |
   | hp        |                           | [1] &Base::move  |
   +-----------+                           | [2] &Base::~Base |
                                           +------------------+
   Dog d
   +-----------+                           Dog's vtable
   | vptr  ●---+-------------------------->+------------------+
   | hp        |                           | [0] &Dog::speak  |  <- overridden
   | tricks    |                           | [1] &Base::move  |  <- inherited
   +-----------+                           | [2] &Dog::~Dog   |
                                           +------------------+
```

### 3. What `p->speak()` compiles to

```cpp
Base* p = &d;
p->speak();
// becomes, roughly:
// (*(p->vptr)[0])(p);     // 1. read the vptr from the object
                           // 2. index slot 0 in the vtable it points to
                           // 3. call that function, passing p as 'this'
```

The compiler knows at compile time that `speak` is **slot 0**; that's fixed by the class layout. What it doesn't know is **which table** to look in, and the object tells it through its vptr. That's the whole trick: the dispatch decision is stored inside the object.

### 4. When things happen

| Event | What happens |
|---|---|
| Compile time | One vtable per polymorphic class is generated; each virtual call becomes "load vptr, index slot k, call" |
| Object construction | Each constructor in the chain sets the vptr to **its own** class's vtable; the most-derived constructor runs last, so the final value is the most-derived class's table |
| Object destruction | Each destructor resets the vptr to its own class's vtable before its body runs |
| Call | Two memory loads and an indirect call |

The construction and destruction rows explain §4.8.

### 5. Costs

| Cost | Size |
|---|---|
| Memory per object | **One pointer** (8 bytes on 64-bit), however many virtual functions there are |
| Memory per class | One vtable (one pointer per virtual function), shared by all objects |
| Time per call | An extra load + indirect call: a few nanoseconds; can mispredict |
| Lost optimisation | Virtual calls usually **can't be inlined** (unless the compiler can prove the type, e.g. with `final`) |

```cpp
struct Empty {};                                     // sizeof 1
struct OneV  { virtual void f(); };                  // sizeof 8  (vptr)
struct ManyV { int x; virtual void a(); virtual void b(); virtual void c(); };
                                                     // sizeof 16 (vptr + int + padding)
```

### 6. Multiple inheritance (one line is enough)

With multiple polymorphic bases, an object has **several vptrs**, one per polymorphic base sub-object, and converting `Derived*` to the second base's pointer adjusts the address. Know that it exists; details are rarely asked.

### 7. Must remember

1. **vtable: one per class**, static, built at compile time, an array of function pointers.
2. **vptr: one per object**, hidden, usually first, set by the constructor.
3. Call = load vptr → index a fixed slot → indirect call.
4. Size cost: one pointer per object, regardless of how many virtual functions.
5. Non-virtual functions are not in the vtable.
6. An overridden slot points to the derived version; a non-overridden slot keeps the base version.
7. The standard doesn't require vtables; say "typically".

### 8. Interview questions

- *"How does a virtual function work internally?"* Each class with virtual functions has a vtable, a static array of pointers to the versions of its virtual functions that this class uses. Each object has a hidden vptr pointing to its class's vtable, set by the constructor. A virtual call loads the vptr, indexes the slot for that function (known at compile time), and calls through it, so the object's real class decides. *Follow-up: "How many vtables and vptrs exist for 3 classes and 100 objects?"* Up to 3 vtables (one per polymorphic class) and 100 vptrs (one per object, or more with multiple inheritance). *Follow-up: "Where is the vtable stored?"* In static, typically read-only, data. It's not on the heap and not in the object.
- *"What's the overhead of virtual functions?"* One pointer per object, one table per class, and an indirect call that usually can't be inlined.

---

## 4.8 Virtual calls inside constructors and destructors

### 1. The rule

**Inside a constructor or destructor, virtual calls resolve to the class currently being constructed or destroyed, not to the most-derived class.**

```cpp
struct B {
    B()          { cout << "Bctor:"; hello(); }
    virtual void hello() { cout << "B "; }
    virtual ~B() { cout << "Bdtor:"; hello(); }
};
struct D : B {
    D()  { cout << "Dctor:"; hello(); }
    void hello() override { cout << "D "; }
    ~D() { cout << "Ddtor:"; hello(); }
};
int main() { D d; }
```

**Output:** `Bctor:B Dctor:D Ddtor:D Bdtor:B`

### 2. Why

While `B()` runs, the `D` part **doesn't exist yet**: its members are uninitialised. Calling `D::hello()` could read garbage. So C++ treats the object as a `B` during `B`'s constructor. Mechanically, `B()` has set the vptr to **B's vtable**, and `D()` resets it to D's afterwards. The destructor is the mirror image: by the time `~B()` runs, the `D` part has already been destroyed.

### 3. The pure virtual trap

If the function is **pure virtual** in `B` and `B`'s constructor calls it (even indirectly, through another member function), the behaviour is **undefined**. In practice the program usually crashes with *"pure virtual method called"*.

### 4. Must remember

1. Virtual calls in constructors and destructors don't reach derived overrides.
2. Reason: the derived part doesn't exist yet, or no longer exists; the vptr points to the current class's table.
3. Calling a pure virtual function from a constructor or destructor is undefined behaviour.
4. If derived-specific initialisation is needed, use a factory function or two-phase initialisation.

---

## 4.9 The virtual destructor

### 1. The bug

```cpp
struct Base { ~Base() { cout << "~Base "; } };           // NOT virtual
struct Derived : Base {
    int* buf = new int[1000];
    ~Derived() { delete[] buf; cout << "~Derived "; }
};

Base* p = new Derived;
delete p;        // UNDEFINED BEHAVIOUR; typically prints only "~Base " -> buf leaks
```

`delete p` calls the destructor through a `Base*`. The destructor isn't virtual, so it's **statically bound** to `~Base`, and `~Derived` never runs. The standard calls this **undefined behaviour**. A leaked buffer is the *typical* symptom, but anything may happen, including a corrupted heap when the bases are laid out at offsets.

### 2. The fix

```cpp
struct Base { virtual ~Base() { cout << "~Base "; } };
// Derived as before
Base* p = new Derived;
delete p;        // ~Derived ~Base   <- dynamic dispatch picks ~Derived, which then chains to ~Base
```

### 3. The rule

> **If a class has any virtual function (that is, it is meant to be used polymorphically), give it a public virtual destructor.**

The refined rule (Herb Sutter): *a base class destructor should be either **public and virtual**, or **protected and non-virtual***. The protected version forbids `delete` through a base pointer altogether.

Also:
- A virtual destructor makes the class polymorphic (adds a vptr), even if it has no other virtual functions.
- `virtual ~Base() = default;` is the usual way to write it.
- **Never inherit publicly from classes without a virtual destructor** if you'll delete through a base pointer: `std::vector`, `std::string` and `std::map` have none (M3, P9).

### 4. Pure virtual destructor

```cpp
struct Shape {
    virtual ~Shape() = 0;          // makes Shape abstract even with no other pure functions
};
Shape::~Shape() {}                 // MUST still be defined; derived destructors call it
```

It's legal and occasionally used to make a class abstract when it has no other natural pure function. **It must have a body**: every derived destructor calls the base destructor, so leaving it undefined is a linker error.

### 5. Must remember

1. Deleting a derived object through a base pointer without a virtual destructor is **undefined behaviour** (typically a leak).
2. Polymorphic base ⇒ `virtual ~Base() = default;`.
3. A pure virtual destructor still needs a definition.
4. Don't publicly derive from STL containers for polymorphic use.

### 6. Interview question

- *"Why do we need a virtual destructor?"* When you delete a derived object through a base pointer, the destructor call is dispatched through the pointer's type. If it isn't virtual, only the base destructor runs, which is undefined behaviour and typically leaks the derived class's resources. Making it virtual dispatches to the derived destructor, which then chains to the base. *Follow-up: "Can a constructor be virtual?"* No. Virtual dispatch needs a vptr, which the constructor sets up, and to construct you must know the exact type anyway (M1 §1.13). *Follow-up: "Can a destructor be pure virtual?"* Yes, but it must still be defined.

---

## 4.10 Pure virtual functions and abstract classes

### 1. What is it?

A **pure virtual function** is declared with `= 0`: "every concrete derived class must provide this". A class with at least one pure virtual function (declared or inherited, and not yet overridden) is an **abstract class**, and **cannot be instantiated**.

```cpp
class Shape {                                   // abstract
protected:
    string name;                                // abstract classes CAN have data
public:
    Shape(string n) : name(n) {}                // ...and constructors
    virtual double area() const = 0;            // pure virtual
    virtual double perimeter() const = 0;
    void describe() const {                     // ...and concrete functions
        cout << name << ": area " << area() << "\n";   // calls the derived version
    }
    virtual ~Shape() = default;
};

class Circle : public Shape {                   // concrete: overrides ALL pure functions
    double r;
public:
    Circle(double r) : Shape("circle"), r(r) {}
    double area() const override      { return 3.14159 * r * r; }
    double perimeter() const override { return 2 * 3.14159 * r; }
};

Shape s("x");                   // ERROR: cannot declare variable 's' to be of abstract type 'Shape'
Shape* p = new Circle(1);       // OK: pointers and references to abstract types are fine
p->describe();                  // circle: area 3.14159
```

### 2. Why does it exist?

To define a **contract**: an interface that derived classes must fulfil, while forbidding objects of the incomplete base. "A shape" in the abstract has no area formula; only specific shapes do. This is **abstraction** (M2) made concrete in the language.

`describe()` above is also a small example of the **Template Method** pattern: the base defines the algorithm, and the derived classes fill in the steps.

### 3. Rules

| Question | Answer |
|---|---|
| Can you create an object of an abstract class? | **No** |
| Can you have a pointer or reference to one? | **Yes**, and that's the whole point |
| Can it have a constructor? | **Yes**; it's called when a derived object is built |
| Can it have data members and concrete functions? | **Yes** |
| If a derived class doesn't override every pure function? | The derived class is **also abstract** |
| Can a pure virtual function have a body? | **Yes**, defined outside the class; callable explicitly as `Base::f()` (a "default implementation you must opt into") |
| Can a destructor be pure virtual? | Yes, but it needs a body (§4.9) |

```cpp
double Shape::area() const { return 0; }   // body for a pure virtual: legal
// In a derived class:  return s * s + Shape::area();   // explicit call works
```

### 4. Must remember

1. `= 0` makes a function pure virtual; one or more makes the class abstract.
2. Abstract classes can have constructors, data and concrete methods; they just can't be instantiated.
3. Not overriding every pure virtual function leaves the derived class abstract.
4. Pure virtual functions can have bodies.

---

## 4.11 Interfaces in C++, and abstract class vs interface

### 1. C++ has no `interface` keyword

An "interface" in C++ is a convention: **an abstract class with only pure virtual functions, a virtual destructor, and no data members.**

```cpp
class Printable {
public:
    virtual void print() const = 0;
    virtual ~Printable() = default;
};
class Serializable {
public:
    virtual string serialize() const = 0;
    virtual ~Serializable() = default;
};
class Invoice : public Printable, public Serializable {   // "implements" two interfaces
public:
    void print() const override { /* ... */ }
    string serialize() const override { return "{...}"; }
};
```

Inheriting from several **data-less** interfaces is the safe form of multiple inheritance: with no data in the bases, there's nothing to duplicate in a diamond (M3 §3.8).

### 2. Abstract class vs interface (the standard question)

| | Abstract class | Interface |
|---|---|---|
| Purpose | **Partial implementation**: shared code + a contract | **Pure contract**: what, never how |
| Data members | Allowed | None (by convention in C++; in Java, only constants) |
| Concrete methods | Allowed | None in C++ by convention (Java 8+ allows `default` methods) |
| Constructors | Allowed | None needed |
| Multiple inheritance | C++: allowed but risky (diamond); Java: a class extends **one** | A class can implement **many** (both languages) |
| Relationship | is-a (strong, shared identity) | can-do (capability: `Printable`, `Comparable`) |
| Keyword | C++: `= 0`; Java: `abstract class` | C++: convention; Java: `interface` |
| Use when | Related classes share state or code | Unrelated classes share a capability |

**The model answer:** *"An abstract class can hold state and some implementation, and is used when related classes share code. An interface is a pure contract with no state, used to give unrelated classes a common capability. A class can extend only one abstract class in Java but implement many interfaces. C++ has no interface keyword; an interface is an abstract class with only pure virtual functions and a virtual destructor."*

### 3. Must remember

1. A C++ interface = all pure virtual functions + a virtual destructor + no data.
2. Abstract class = shared state and code; interface = capability only.
3. Multiple interfaces avoid the diamond's data problem.

---

## 4.12 Overloading vs overriding vs hiding

The most-asked comparison in this module. Add hiding to your answer; most candidates don't know it, and it shows depth.

| | Overloading | Overriding | Hiding |
|---|---|---|---|
| Where | **Same scope** (same class or namespace) | Base and derived class | Base and derived class |
| Signature | **Different** parameters | **Same** signature | Same **name**, any signature |
| `virtual` needed | No | **Yes** (in the base) | No (or the signature differs) |
| Resolved | Compile time | **Runtime** | Compile time (static type) |
| Polymorphism kind | Compile-time | Runtime | None |
| Return type | Can differ (but can't be the only difference) | Same, or covariant | Anything |
| Purpose | Same operation, different inputs | Specialise behaviour in a subclass | Usually an accident |
| Keyword help | — | `override` | `using Base::f;` to un-hide |

```cpp
struct B {
    virtual void f(int);
    void g(int);
};
struct D : B {
    void f(int) override;     // OVERRIDING: same signature, virtual in the base
    void g(int);              // HIDING:     same name, not virtual
    void f(double);           // HIDING again: also hides any other B::f overloads
    void h(int); void h(char);// OVERLOADING: same scope, different parameters
};
```

**The model answer:** *"Overloading is same name, different parameters, in the same scope, resolved at compile time. Overriding is a derived class redefining a base class virtual function with the same signature, resolved at runtime through the vtable. There's a third case, hiding: a derived function with the same name but not virtual, or with a different signature, which hides the base versions and is resolved by static type."*

---

## 4.13 Early vs late binding

| | Early (static) binding | Late (dynamic) binding |
|---|---|---|
| Decided | Compile time | Runtime |
| Applies to | Non-virtual functions, overloads, templates, calls on objects | Virtual functions via pointer/reference |
| Mechanism | Direct call to a fixed address | Indirect call through vptr → vtable |
| Speed | Faster, inlinable | Slightly slower, usually not inlined |
| Flexibility | Fixed | Extensible with new derived types |

"Binding" means connecting a function call to the function body that will run.

---

## 4.14 Trick questions

### 1. Default arguments on virtual functions

**Default arguments are bound statically (from the static type); the function body is bound dynamically.** Mixing them gives surprising output:

```cpp
struct B { virtual void show(int x = 1) { cout << "B" << x; } virtual ~B() = default; };
struct D : B {      void show(int x = 2) override { cout << "D" << x; } };

D d; B* p = &d;
p->show();     // D1   <- D's body (dynamic), B's default (static type B*)
d.show();      // D2
```

**Rule:** never give an override a different default argument from the base.

### 2. Private override

```cpp
struct B { public:  virtual void f() { cout << "B"; } virtual ~B() = default; };
struct D : B { private: void f() override { cout << "D"; } };

D d; B* p = &d;
p->f();        // prints "D". Access is checked on the STATIC type (B::f is public)
// d.f();      // ERROR: D::f is private
```

Access control is a compile-time check on the static type; dispatch is a runtime mechanism that ignores access. (This underlies the **Non-Virtual Interface** idiom: public non-virtual functions in the base call private virtual ones that derived classes override.)

### 3. Can static functions be virtual?

**No.** There's no object, so no vptr to dispatch on (M0 §0.6).

### 4. Can a virtual function be inline?

Yes, it can be *declared* inline (or defined in the class body). It's actually inlined only when the call is resolved statically: on an object, with qualification (`B::f()`), or when the compiler can prove the dynamic type (`final`). Calls through a pointer generally aren't inlined.

### 5. Can a template member function be virtual?

**No.** A vtable needs a fixed number of slots at compile time, but a member function template has an unbounded number of instantiations. (A class template can have virtual functions; a *member function template* can't be virtual.)

### 6. Covariant return types

An override may return a **pointer or reference to a more derived type** than the base version returns:

```cpp
struct Shape  { virtual Shape*  clone() const { return new Shape(*this); }  virtual ~Shape() = default; };
struct Circle : Shape { Circle* clone() const override { return new Circle(*this); } };
```

This is the standard **virtual copy constructor** idiom. Since constructors can't be virtual, `clone()` gives you "copy this object, whatever its real type is". With `unique_ptr` return types, covariance doesn't apply (`unique_ptr<Circle>` isn't covariant with `unique_ptr<Shape>`), so modern code returns `unique_ptr<Shape>` from every override.

### 7. Calling a virtual function non-virtually

`p->Base::f()` calls `Base::f` directly, with no dispatch. Overrides use this to extend rather than replace the base behaviour.

### 8. Does a derived class need the `virtual` keyword on its override?

No. A function that overrides a virtual function is automatically virtual. Write `override` instead, which is both clearer and checked.

### Must remember (tricks)

1. Default arguments come from the static type; the body from the dynamic type.
2. Access is checked on the static type, so a private override is still dispatched to.
3. No virtual static functions and no virtual member templates.
4. Covariant returns enable `clone()`, the "virtual constructor" substitute.

---

## 4.15 Consolidation

### Must remember (module)

1. Polymorphism = one interface, many behaviours. Compile-time (overloading, operators, templates) vs runtime (virtual functions).
2. Overloads differ by parameters, never by return type alone; tie → ambiguous; implemented by name mangling.
3. Can't overload `::  .  .*  ?:  sizeof  typeid`; `=  []  ()  ->` must be members; stream `<<` must be a non-member.
4. Dynamic dispatch needs **virtual + pointer/reference**.
5. Always write `override`; `final` stops overriding or derivation.
6. **vtable per class** (static array of function pointers), **vptr per object** (set by the constructor); call = load vptr → fixed slot → indirect call.
7. Cost: one pointer per object, an indirect call, usually no inlining.
8. In constructors and destructors, virtual calls resolve to the current class; a pure virtual call there is UB.
9. Polymorphic base ⇒ virtual destructor; otherwise `delete` through the base is UB.
10. A pure virtual destructor needs a body.
11. Abstract class: at least one pure virtual function; can't be instantiated; can have constructors, data and concrete methods.
12. C++ interface = only pure virtuals + a virtual destructor + no data.
13. Overloading (same scope) vs overriding (virtual, same signature, runtime) vs hiding (same name, static).
14. Default arguments are static; access is checked statically; no virtual statics or virtual member templates.
15. `clone()` with covariant returns = the virtual copy constructor.

### Common wrong answers (module)

- "Overloading can differ by return type."
- "Virtual functions work on objects too." Only through pointers or references.
- "There is one vtable per object." One per **class**; one **vptr** per object.
- "Each virtual function adds a pointer to the object." Only one vptr in total.
- "In the base constructor, the derived override is called."
- "Without a virtual destructor, just the derived part leaks." It's **undefined behaviour**; the leak is only the typical symptom.
- "An abstract class can't have a constructor."
- "A pure virtual function can't have a body."
- "Constructors can be virtual."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is polymorphism? | One interface, many behaviours; compile-time and runtime | Real-world example |
| Compile-time vs runtime polymorphism? | Overloading/templates resolved by the compiler vs virtual functions resolved by the object's actual type at runtime | How is runtime implemented? |
| Overloading vs overriding? | Same scope, different parameters, compile time vs base/derived, same signature, virtual, runtime | And hiding? |
| How do virtual functions work? | vtable per class, vptr per object, indexed indirect call | How many vtables/vptrs? Where stored? |
| Overhead of virtual? | One pointer per object, an indirect call, no inlining | When is it inlined? |
| Why a virtual destructor? | Deleting through a base pointer otherwise skips the derived destructor (UB) | Pure virtual destructor? |
| Virtual call in a constructor? | Calls the current class's version; the derived part isn't built yet | Pure virtual case? (UB) |
| Can a constructor be virtual? | No: no vptr yet, and the exact type must be known | Alternative? (`clone()`, factory) |
| Abstract class? | Has at least one pure virtual function; can't be instantiated | Can it have a constructor? (Yes) |
| Abstract class vs interface? | Shared state and code vs pure contract; one base vs many | How in C++? |
| Which operators can't be overloaded? | `::  .  .*  ?:  sizeof  typeid` | Why not `.`? |
| Prefix vs postfix `++` overload? | Postfix takes a dummy `int` and returns the old value by copy | Which is faster? |
| What does `override` do? | Compile error if the function doesn't actually override | What is `final`? |

### Practice: predict the output or the error

**P1.**
```cpp
struct B{ virtual void f(){cout<<"B::f ";} void g(){cout<<"B::g ";} virtual ~B()=default; };
struct D:B{ void f() override{cout<<"D::f ";} void g(){cout<<"D::g ";} };
int main(){ D d; B* p=&d; B& r=d; B b=d; p->f(); p->g(); r.f(); b.f(); d.g(); p->B::f(); }
```
<details><summary>Answer</summary>

`D::f B::g D::f B::f D::g B::f`
</details>

**P2.**
```cpp
struct B{ B(){ cout<<"Bctor:"; hello(); } virtual void hello(){cout<<"B ";} virtual ~B(){ cout<<"Bdtor:"; hello(); } };
struct D:B{ D(){cout<<"Dctor:"; hello();} void hello() override{cout<<"D ";} ~D(){cout<<"Ddtor:"; hello();} };
int main(){ D d; }
```
<details><summary>Answer</summary>

`Bctor:B Dctor:D Ddtor:D Bdtor:B`
</details>

**P3.**
```cpp
struct B{ virtual void show(int x=1){cout<<"B"<<x<<" ";} virtual ~B()=default; };
struct D:B{ void show(int x=2) override{cout<<"D"<<x<<" ";} };
int main(){ D d; B* p=&d; p->show(); d.show(); }
```
<details><summary>Answer</summary>

`D1 D2`. The body is dynamic; the default argument comes from the static type.
</details>

**P4.**
```cpp
void k(int){cout<<"int";} void k(long){cout<<"long";}
int main(){ k('a'); k(3.5); }
```
<details><summary>Answer</summary>

**Compile error** on `k(3.5)`: ambiguous (double→int and double→long are both conversions). If you remove that call, `k('a')` prints `int` (promotion).
</details>

**P5.** Does it compile? If yes, what's printed?
```cpp
struct B{ virtual void f() const {cout<<"B";} virtual ~B()=default; };
struct D:B{ void f() {cout<<"D";} };
int main(){ D d; const B& r = d; r.f(); }
```
<details><summary>Answer</summary>

It compiles and prints **`B`**. `D::f()` is missing `const`, so it doesn't override `B::f() const`; it's a new function that hides it. Adding `override` would have turned this silent bug into a compile error.
</details>

**P6.**
```cpp
struct S{ virtual double area() const = 0; };
struct T : S {};
int main(){ T t; }
```
<details><summary>Answer</summary>

**Compile error**: `T` is abstract, because it didn't override `area()`.
</details>

**P7.**
```cpp
struct C{ int v; C(int v):v(v){} C& operator++(){++v; return *this;} C operator++(int){C t=*this; ++v; return t;} };
int main(){ C x(5); C y = x++; C z = ++x; cout<<x.v<<" "<<y.v<<" "<<z.v; }
```
<details><summary>Answer</summary>

`7 5 7`
</details>

**P8.**
```cpp
struct B{ public: virtual void f(){cout<<"B";} virtual ~B()=default; };
struct D:B{ private: void f() override{cout<<"D";} };
int main(){ D d; B* p=&d; p->f(); }
```
<details><summary>Answer</summary>

`D`. Access is checked against the static type `B`, where `f` is public; dispatch still reaches `D::f`.
</details>

**P9.** On a 64-bit compiler, what are the typical sizes?
```cpp
struct E{}; struct S{ virtual void f(){} };
struct I{ int x; virtual void a(){} virtual void b(){} virtual void c(){} };
```
<details><summary>Answer</summary>

`1 8 16`. One vptr no matter how many virtual functions; `I` = 8 (vptr) + 4 + 4 padding.
</details>

**P10.** What's wrong, and what is the typical symptom?
```cpp
struct Base { ~Base() {} };
struct Derived : Base { std::vector<int> big = std::vector<int>(1'000'000); };
int main() { Base* p = new Derived; delete p; }
```
<details><summary>Answer</summary>

`Base` has no virtual destructor, so `delete p` through a `Base*` is **undefined behaviour**. Typically `~Derived` never runs and the vector's million ints leak. Fix: `virtual ~Base() = default;`.
</details>

**P11.** Draw the vtables and the object layout for:
```cpp
struct A { virtual void x(); virtual void y(); int a; virtual ~A(); };
struct B : A { void y() override; virtual void z(); int b; };
```
<details><summary>Answer</summary>

```
A's vtable: [&A::x, &A::y, &A::~A]
B's vtable: [&A::x, &B::y, &B::~B, &B::z]    <- inherited x, overridden y and destructor, new slot z appended
A object:   [vptr->A's vtable | a]
B object:   [vptr->B's vtable | a | b]
```

The exact slot order is compiler-specific; what matters is that inherited slots keep their positions and new virtuals are appended.
</details>

---

## Exit checklist

```
[ ] I can explain compile-time vs runtime polymorphism with a table and an example
[ ] I know what can and cannot distinguish overloads, and the resolution ranking
[ ] I can list the non-overloadable operators and the must-be-member ones
[ ] I can write prefix and postfix ++ correctly
[ ] I know the two conditions for dynamic dispatch
[ ] I always write override, and know what final does
[ ] I can draw vtables and vptrs for a two-class hierarchy and explain a virtual call step by step
[ ] I can state the memory and time cost of virtual functions
[ ] I can explain why virtual calls in constructors don't reach derived overrides
[ ] I can explain the virtual destructor bug and fix, and the pure virtual destructor rule
[ ] I can define an abstract class and an interface, and compare them
[ ] I can compare overloading vs overriding vs hiding in one table
[ ] I know the default-argument, private-override, static, template and covariant tricks
[ ] P1–P11 done
```

---

## Next

**Part 7: M5 — Object Relationships and UML.** It covers association vs aggregation vs composition (with lifetime as the deciding test), dependency, multiplicity, "favour composition over inheritance" with a worked refactor, and reading and drawing UML class diagrams, which you'll need for every LLD round.
