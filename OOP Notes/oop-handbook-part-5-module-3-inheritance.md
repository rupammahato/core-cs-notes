# OOP Placement Handbook (C++) — Part 5
# Module 3: Inheritance

**Module 3 · 3 hours · Tier 1 · Requires: M0, M1, M2**

---

## What this module is really testing

Interview questions on inheritance fall into three groups:

1. **Tables you must know cold:** the types of inheritance, and the access-mode table (what `public`/`protected`/`private` inheritance does to each member). These are easy marks.
2. **Mechanics that drive output questions:** constructor and destructor order across a hierarchy, the diamond problem, object slicing and name hiding.
3. **Judgement:** when to use inheritance at all. Product companies care most about this one, and M5 and M7 build on it.

The organising principle:

> **Public inheritance means "is-a": a Derived object *is* a Base object, plus more. Every rule in this module (which constructor runs first, why slicing happens, why the diamond duplicates the base) follows from the fact that a derived object physically contains a complete base object inside it.**

---

## 3.1 What inheritance is

### 1. What is it?

A mechanism by which a new class (**derived**, child, subclass) acquires the members of an existing class (**base**, parent, superclass) and can add or change behaviour.

```cpp
class Vehicle {
protected:
    string regNo;
    int wheels;
public:
    Vehicle(string r, int w) : regNo(r), wheels(w) {}
    void showReg() const { cout << regNo << "\n"; }
};

class Car : public Vehicle {             // Car IS-A Vehicle
    int seats;
public:
    Car(string r, int s) : Vehicle(r, 4), seats(s) {}   // build the base part first
    void showSeats() const { cout << seats << "\n"; }
};

Car c("KA01", 5);
c.showReg();          // inherited
c.showSeats();        // own
```

### 2. Why does it exist?

| Purpose | Meaning |
|---|---|
| **Reuse** | Write common code once, in the base |
| **Extension** | Add new behaviour without touching the base |
| **Polymorphism** | The real reason. A `Vehicle*` can point at a `Car` or a `Truck`, and code written against `Vehicle` works for all of them (M4) |

Reuse alone is **not** a good reason to inherit; composition (M5) reuses code without the coupling. The defensible reasons are a genuine **is-a** relationship and a need for **substitutability** (polymorphism).

### 3. The memory picture (the key to the whole module)

```
   Car object in memory
   +-----------------------------+
   |  Vehicle sub-object         |  <- a complete Vehicle lives INSIDE every Car
   |    regNo                    |
   |    wheels                   |
   +-----------------------------+
   |  Car's own members          |
   |    seats                    |
   +-----------------------------+
```

From this picture:
- **Construction order:** the inner Vehicle part must be built before the Car part.
- **Slicing:** copying a Car into a Vehicle keeps only the top box.
- **Diamond problem:** two paths to the same base mean two boxes.
- **Upcasting** is free: a `Car*` already points at a `Vehicle`.

### 4. Must remember

1. Public inheritance models **is-a**.
2. A derived object **contains** a complete base sub-object.
3. Polymorphism is the main reason to inherit; reuse alone points to composition.

---

## 3.2 Types of inheritance

```
 Single          Multiple            Multilevel       Hierarchical          Hybrid
                                                                         (often a diamond)
   A             A       B              A                 A                    A
   |              \     /               |               / | \                 / \
   B                 C                  B              B  C  D               B   C
                                        |                                     \ /
                                        C                                      D
```

| Type | Definition | Example |
|---|---|---|
| **Single** | One derived class, one base | `Car : Vehicle` |
| **Multiple** | One derived class, **two or more bases** | `SmartPhone : Phone, Camera` |
| **Multilevel** | A chain: C derives from B, which derives from A | `ElectricCar : Car : Vehicle` |
| **Hierarchical** | Many derived classes from **one base** | `Car`, `Bike`, `Truck` : `Vehicle` |
| **Hybrid** | A combination of two or more of the above | Multiple + hierarchical → the **diamond** |

```cpp
class A {};
class B : public A {};                       // single
class C : public B {};                       // multilevel (A -> B -> C)
class D : public A {};                       // hierarchical (B and D from A)
class E { };
class F : public B, public E {};             // multiple
class G : public B, public D {};             // hybrid: diamond through A
```

### Java note (asked often)

Java supports single, multilevel and hierarchical inheritance of **classes**, but **not multiple inheritance of classes**, precisely to avoid the diamond problem. A Java class can implement **multiple interfaces**. Since Java 8, interfaces can have default methods; if two interfaces supply the same default method, the class must override it explicitly, which resolves the ambiguity by force. C++ allows multiple inheritance and solves the diamond with **virtual inheritance** (§3.8).

---

## 3.3 Access control in inheritance

Two separate things decide access:
1. The **member's** access specifier in the base (`public`, `protected`, `private`).
2. The **inheritance mode** (`class D : public B`, `: protected B`, `: private B`).

### 1. The table (memorise it)

| Member in Base ↓ / Inheritance mode → | `public` | `protected` | `private` |
|---|---|---|---|
| `public` | public in Derived | protected in Derived | private in Derived |
| `protected` | protected in Derived | protected in Derived | private in Derived |
| `private` | **not accessible** | **not accessible** | **not accessible** |

**How to remember it:** the inheritance mode is a **ceiling**. Each inherited member gets the *more restrictive* of its own access and the mode. Base-private members are never accessible to the derived class, whatever the mode.

### 2. What each mode means

| Mode | Relationship it models | Outside code can treat `Derived` as `Base`? | Typical use |
|---|---|---|---|
| `public` | **is-a** | Yes (`Base* p = &derived;` works) | 99% of inheritance |
| `protected` | is-a, visible only to further derived classes | Only inside Derived and its descendants | Very rare |
| `private` | **"implemented-in-terms-of"** | **No**: the base is an inaccessible base | Reusing an implementation without exposing it; usually composition is better |

```cpp
class Base {};
class D : private Base {};
D d;
Base* b = &d;          // ERROR: 'Base' is an inaccessible base of 'D'
```

### 3. Defaults

- `class D : B` → **private** inheritance.
- `struct D : B` → **public** inheritance.

`class Car : Vehicle` (forgetting `public`) is a classic bug: it compiles, then `Vehicle* p = &car;` fails with "inaccessible base".

### 4. Private members *are* inherited

Every base member, including private ones, physically exists inside the derived object and takes up space. Private members are **inherited but not accessible**. The derived class reaches them only through the base's public or protected functions.

```cpp
class Base { int secret = 7; public: int get() const { return secret; } };
class D : public Base { public: void f() { /* secret = 1;  ERROR */ cout << get(); } };
// sizeof(D) includes secret.
```

"Private members are not inherited" is a **wrong answer**. Say "inherited but inaccessible".

### 5. The protected subtlety (advanced trick question)

A derived class can access a protected base member **only through objects of its own type** (or types derived from it), not through an arbitrary `Base` object:

```cpp
class Base { protected: int x; };
class D : public Base {
public:
    void f(D& other, Base& b) {
        x = 1;          // OK: own inherited member
        other.x = 2;    // OK: accessed through a D
        b.x = 3;        // ERROR: 'int Base::x' is protected within this context
    }
};
```

**Why:** `b` might really be a *different* derived class, say `OtherDerived`. Allowing `D` to modify `OtherDerived`'s protected state would let any class bypass another sibling's encapsulation just by inheriting from the same base.

### 6. Must remember

1. Inheritance mode = ceiling on access. Base-private is never accessible.
2. Default: `class` → private inheritance, `struct` → public.
3. Private members are inherited (they take space) but inaccessible.
4. Only **public** inheritance gives an is-a relationship that outside code can use.
5. Protected access works only through the derived class's own type.

---

## 3.4 What is and isn't inherited

| Inherited | Not inherited |
|---|---|
| All data members (including private ones, which are present but inaccessible) | **Constructors** (unless `using Base::Base;`, C++11) |
| Ordinary member functions | **Destructor** (each class has its own, but the base's still runs as part of destruction) |
| Virtual functions (and the vptr mechanism) | **Copy assignment operator** (the derived class's implicitly generated one hides the base's; it calls the base's internally) |
| Static members (the **same** single copy is shared with the base) | **Friends** (friendship isn't inherited, M2) |
| Nested types and typedefs | |
| Operator overloads (except assignment, which is hidden) | |

```cpp
class Base { public: Base(int x) {} };
class D : public Base {
public:
    using Base::Base;      // C++11 inheriting constructors: D(int) now exists
};
D d(5);                    // works only because of the using-declaration
```

**Static members are shared, not copied:**

```cpp
class Base { public: static int count; };
int Base::count = 0;
class D : public Base {};
D::count = 5;
cout << Base::count;       // 5: one variable, two names
```

---

## 3.5 Constructor and destructor order across a hierarchy

### 1. The rules

**Construction:** base first, then members, then own body. This applies recursively up the chain, so the most basic class is built first.

**Destruction:** exactly the reverse: own body, then members (in reverse), then the base.

**Why:** the derived part is built on top of the base part. The derived constructor might use base members, so the base must already exist. The derived destructor might use base members, so the base must still exist.

### 2. Trace: multilevel with a member

```cpp
struct A { A() { cout << "A"; } ~A() { cout << "~A"; } };
struct M { M() { cout << "M"; } ~M() { cout << "~M"; } };
struct B : A { M m; B() { cout << "B"; } ~B() { cout << "~B"; } };
struct C : B { C() { cout << "C"; } ~C() { cout << "~C"; } };

int main() { C c; cout << "|"; }
```

**Output:** `AMBC|~C~B~M~A`

| Step | Why |
|---|---|
| A | C's base is B; B's base is A, the deepest, so it is built first |
| M | Then B's members |
| B | Then B's body |
| C | Then C's body |
| ~C ~B ~M ~A | Exact mirror |

### 3. Passing arguments to the base constructor

The **only** place to pass arguments to a base constructor is the derived constructor's **initialiser list**:

```cpp
class Vehicle { public: Vehicle(string reg, int wheels); };      // no default constructor
class Car : public Vehicle {
public:
    Car(string reg) : Vehicle(reg, 4) {}     // REQUIRED
    // Car(string reg) { }                   // ERROR: no default Vehicle() to call
};
```

If the initialiser list doesn't mention the base, the base's **default constructor** is called. If the base has none, it's a compile error. This is the fourth "mandatory initialiser list" case from M1.

### 4. Multiple inheritance order

Bases are constructed in the order they are **listed in the class declaration**, not the order in the initialiser list:

```cpp
struct X { X() { cout << "X"; } };
struct Y { Y() { cout << "Y"; } };
struct Z : Y, X {                        // declaration order: Y, then X
    Z() : X(), Y() { cout << "Z"; }      // list order doesn't matter
};
Z z;   // YXZ
```

Same rule as members in M1: **declaration order always wins**.

### 5. Must remember

1. Construction: base → members → body, recursively. Destruction: the exact reverse.
2. Base constructor arguments go only in the initialiser list.
3. If the base has no default constructor, the derived constructor **must** call one explicitly.
4. Multiple bases are constructed in **declaration order**.
5. Virtual bases are constructed first of all (§3.8).

---

## 3.6 Name hiding and calling the base version

### 1. Overriding a non-virtual function (redefinition)

A derived class can declare a function with the same name and signature as a base function. Without `virtual` this is **redefinition/hiding**, not overriding. The version called depends on the **static type** of the pointer or reference, not the object (M4 covers the virtual version).

### 2. Calling the base version explicitly

```cpp
class Logger { public: void log(const string& m) { cout << "[LOG] " << m << "\n"; } };
class TimedLogger : public Logger {
public:
    void log(const string& m) {
        cout << timestamp() << " ";
        Logger::log(m);              // scope resolution calls the base version
    }
};
```

### 3. The name-hiding trap

**A derived-class function hides *all* base functions with the same name, whatever their parameters.**

```cpp
struct B {
    void f(int)    { cout << "B::f(int)"; }
    void f(double) { cout << "B::f(double)"; }
};
struct D : B {
    void f(string) { cout << "D::f(string)"; }    // hides BOTH B::f overloads
};

D d;
d.f(1);      // ERROR: cannot convert 'int' to 'std::string'
             // name lookup finds f in D and stops; B::f is never considered
```

**Why:** C++ name lookup searches scopes from the inside out and **stops at the first scope that contains the name**. It finds `f` in `D` and never looks into `B`. Overload resolution then happens among the `f`s found, which is only `D::f(string)`.

**The fix:** bring the base overloads into scope.

```cpp
struct D : B {
    using B::f;                     // B::f(int) and B::f(double) are visible again
    void f(string) { ... }
};
d.f(1);                             // B::f(int)
d.f(string("x"));                   // D::f(string)
```

### 4. Must remember

1. Same name in Derived hides **every** base overload of that name.
2. Fix with `using Base::name;`.
3. Call the base version explicitly with `Base::name(...)`.
4. Hiding is about **names**, not signatures; overload resolution only happens after lookup.

---

## 3.7 Multiple inheritance and ambiguity

When two bases have members with the same name, using that name in the derived class is ambiguous:

```cpp
struct Camera { void powerOn() { cout << "camera on"; } };
struct Phone  { void powerOn() { cout << "phone on"; } };
struct SmartPhone : Camera, Phone {};

SmartPhone s;
s.powerOn();          // ERROR: request for member 'powerOn' is ambiguous
s.Camera::powerOn();  // OK: qualify it
```

The better fix is usually to **override in the derived class** and decide explicitly:

```cpp
struct SmartPhone : Camera, Phone {
    void powerOn() { Phone::powerOn(); Camera::powerOn(); }
};
```

Ambiguity is an error only when the name is **used**. Merely inheriting two same-named members is fine.

---

## 3.8 The diamond problem (the centrepiece)

### 1. The problem

```cpp
struct Device {
    int id = 0;
    void powerOn() { cout << "Device on\n"; }
};
struct Printer : Device {};
struct Scanner : Device {};
struct Copier  : Printer, Scanner {};   // the diamond

Copier c;
c.id = 1;            // ERROR: request for member 'id' is ambiguous
Device* d = &c;      // ERROR: 'Device' is an ambiguous base of 'Copier'
```

```
        Device                      Copier object WITHOUT virtual inheritance
        /    \                      +--------------------------+
   Printer  Scanner                 | Printer sub-object       |
        \    /                      |   Device sub-object #1   |  <- id, powerOn
        Copier                      +--------------------------+
                                    | Scanner sub-object       |
                                    |   Device sub-object #2   |  <- id AGAIN
                                    +--------------------------+
                                    | Copier members           |
                                    +--------------------------+
```

There are **two `Device` sub-objects**. Three problems follow:
1. **Ambiguity:** `c.id`: which one?
2. **Wasted memory** and **inconsistent state:** setting `c.Printer::id = 5` leaves `c.Scanner::id` at 0. Is the copier's ID 5 or 0?
3. **The base constructor runs twice:** `Device()` is called once for each path.

### 2. The fix: virtual inheritance

```cpp
struct Printer : virtual Device {};
struct Scanner : virtual Device {};
struct Copier  : Printer, Scanner {};

Copier c;
c.id = 1;            // OK: only one Device
Device* d = &c;      // OK
```

```
   Copier object WITH virtual inheritance
   +-------------------------------+
   | Printer part  (+ hidden ptr) -+---+
   +-------------------------------+   |
   | Scanner part  (+ hidden ptr) -+---+   both locate the ONE shared base
   +-------------------------------+   |
   | Copier members                |   |
   +-------------------------------+   |
   | Device sub-object (shared)  <-+---+   id, powerOn: exactly one copy
   +-------------------------------+
```

`virtual` goes on the **intermediate** classes (Printer, Scanner), not on the final class. It means: "if several classes in a hierarchy inherit this base virtually, share one copy."

### 3. Who constructs the shared base?

The rule that drives output questions: **the most-derived class constructs the virtual base directly**, and it does so **before any non-virtual base**. The intermediate classes' calls to the virtual base's constructor are **ignored** when they are part of a larger object.

```cpp
struct A { A(int x) { cout << "A" << x; } };
struct B : virtual A { B() : A(1) { cout << "B"; } };
struct C : virtual A { C() : A(2) { cout << "C"; } };
struct D : B, C      { D() : A(3) { cout << "D"; } };

D d;   // A3BCD   <- A built once, by D, with 3; B's A(1) and C's A(2) are ignored
```

Why: there's only one `A`, but `B` and `C` disagree about how to build it. The language gives the decision to the one class that knows the whole picture, the most-derived one.

If `D` didn't call `A(3)`, the compiler would try `A()`, and since `A` has no default constructor this is a **compile error**, even though `B` and `C` both call `A(int)`.

**Without virtual inheritance**, for comparison:

```cpp
struct A { A() { cout << "A"; } };
struct B : A { B() { cout << "B"; } };
struct C : A { C() { cout << "C"; } };
struct D : B, C { D() { cout << "D"; } };
D d;   // ABACD   <- A built twice
```

With `virtual` on B and C: `ABCD`.

### 4. The cost of virtual inheritance

- **Memory:** each class that inherits virtually carries a hidden pointer (or offset) used to locate the shared base, so objects get bigger. Typically, with GCC on 64-bit, `struct A { int x; }` is 4 bytes, a plain `struct C : A {}` is also 4, and `struct B : virtual A {}` is 16.
- **Speed:** accessing virtual-base members goes through an extra indirection.
- **Complexity:** the "most-derived constructs it" rule surprises people.

This is why many style guides allow multiple inheritance only from **interfaces**, meaning abstract classes with no data (M4). With no data in the base, there's nothing to duplicate.

### 5. Must remember

1. Diamond = two paths to one base, so **two copies** of the base, so ambiguity, inconsistent state and a double construction.
2. Fix: `virtual` inheritance on the **intermediate** classes.
3. The **most-derived class constructs the virtual base**, first of all; intermediate calls are ignored.
4. If the most-derived class doesn't call it, the virtual base's default constructor is used (an error if there isn't one).
5. Cost: extra hidden pointers, an indirection, and a bigger `sizeof`.
6. Java avoids the issue by not allowing multiple class inheritance.

### 6. Interview questions

- *"What is the diamond problem?"* When a class inherits from two classes that share a common base, it gets two copies of that base. Accessing base members becomes ambiguous, state can diverge, and the base constructor runs twice. *Follow-up: "How does C++ solve it?"* With virtual inheritance: the intermediate classes inherit `virtual`ly, so only one shared base sub-object exists, and the most-derived class constructs it. *Follow-up: "And Java?"* Java forbids multiple inheritance of classes. With interfaces' default methods, a conflict must be resolved by overriding.

---

## 3.9 Object slicing

### 1. What is it?

When a derived object is **copied into a base object by value**, only the base part is copied. The derived members are "sliced off", and the copy behaves as a pure base object, **including its virtual functions**.

### 2. Where it happens

```cpp
struct Animal {
    virtual string speak() const { return "..."; }
    virtual ~Animal() = default;
};
struct Dog : Animal {
    string breed = "lab";
    string speak() const override { return "woof"; }
};

void byVal(Animal a)        { cout << a.speak(); }   // SLICES
void byRef(const Animal& a) { cout << a.speak(); }   // doesn't

Dog d;
byVal(d);          // "..."   <- sliced: a is a real Animal
byRef(d);          // "woof"  <- a refers to the Dog
Animal a = d;      // sliced
a.speak();         // "..."
vector<Animal> v;
v.push_back(d);    // sliced: the vector stores Animals
```

### 3. Why it happens

`Animal a = d;` calls **`Animal`'s copy constructor**, which knows only about `Animal`'s members. It builds a genuine `Animal` object, sized for an `Animal`, with its vptr pointing at `Animal`'s vtable (M4). There is no room for `breed` and no record that it was ever a Dog.

```
   Dog d                         Animal a = d;
   +------------------+          +------------------+
   | Animal part      |  copy -> | Animal part      |   vptr -> Animal's vtable
   |  (vptr -> Dog)   |          +------------------+
   +------------------+
   | breed = "lab"    |  <- sliced off
   +------------------+
```

### 4. The fix

**Use references or pointers for polymorphic objects; never pass or store them by value.**

```cpp
void process(const Animal& a);                      // reference
vector<unique_ptr<Animal>> zoo;                     // owning pointers
zoo.push_back(make_unique<Dog>());
for (auto& a : zoo) cout << a->speak();             // "woof"
```

A defensive extra: make polymorphic base classes **non-copyable** (`= delete` the copy operations), so that accidental slicing becomes a compile error.

### 5. Must remember

1. Slicing = base-class copy of a derived object, so the derived part and the derived behaviour are lost.
2. Causes: pass by value, assign by value, `vector<Base>`.
3. Fix: references, pointers, `vector<unique_ptr<Base>>`.
4. Even virtual functions can't save a sliced object, because it really *is* a base object now.

---

## 3.10 Upcasting and downcasting

| | Upcasting | Downcasting |
|---|---|---|
| Direction | Derived → Base | Base → Derived |
| Syntax | Implicit: `Base* p = &derived;` | Explicit: `static_cast<Derived*>(p)` or `dynamic_cast<Derived*>(p)` |
| Safety | Always safe (public inheritance) | Safe only if the object really *is* a Derived |
| Use | Polymorphism | Recovering derived-only functionality (often a design smell) |

```cpp
Animal* a = new Dog();                       // upcast, implicit
Dog* d1 = static_cast<Dog*>(a);              // compiles; UB if *a weren't actually a Dog
Dog* d2 = dynamic_cast<Dog*>(a);             // checked at runtime: nullptr if not a Dog
```

`dynamic_cast` requires the base class to have at least one virtual function (it uses RTTI). Full details are in M6. **Frequent downcasting** usually means a virtual function is missing from the base.

---

## 3.11 When to use inheritance: is-a vs has-a

### 1. The test

| Relationship | Test sentence | Implement with | Example |
|---|---|---|---|
| **is-a** | "A Car *is a* Vehicle" sounds right in every context | Public inheritance | `Car : Vehicle` |
| **has-a** | "A Car *has an* Engine" | Composition: a member object (M5) | `class Car { Engine e; }` |

"A Car is an Engine" is obviously wrong, so `Car : Engine` would be a design error even though it would let `Car` reuse `Engine::start()`.

### 2. The deeper test: substitutability

"Is-a" in English isn't quite enough. The real requirement is that **a Derived object can be used anywhere a Base is expected without breaking anything**. This is the Liskov Substitution Principle (M7). The famous counter-example: mathematically a square *is a* rectangle, but if `Rectangle` has `setWidth()` and `setHeight()` that work independently, a `Square` that forces them equal breaks code that expects a rectangle. So `Square : Rectangle` is a bad design despite passing the English test.

### 3. Advantages and disadvantages (asked as a list)

| Advantages | Disadvantages |
|---|---|
| Code reuse | **Tight coupling**: Derived depends on Base's internals (the "fragile base class" problem: a change in Base can break every Derived) |
| Enables polymorphism and extensibility | The hierarchy is fixed at compile time; you can't change an object's base at runtime |
| Models natural hierarchies | Deep hierarchies are hard to understand ("which `log` runs?") |
| Avoids duplicate code | Multiple inheritance brings the diamond and ambiguity |
| | Inherits *everything*, including members the derived class doesn't want |

These disadvantages are why the guideline is **"favour composition over inheritance"** (M5).

### 4. Must remember

1. Inherit for **is-a with substitutability**; compose for **has-a**.
2. Square/Rectangle is the classic "is-a in English, not in code" example.
3. The main disadvantage is tight coupling (fragile base class).

---

## 3.12 Consolidation

### Must remember (module)

1. Public inheritance = is-a. A derived object contains a full base sub-object.
2. Five types: single, multiple, multilevel, hierarchical, hybrid. Java has no multiple class inheritance.
3. Access table: the mode is a ceiling; base-private is never accessible.
4. `class` defaults to private inheritance, `struct` to public.
5. Private members are inherited but inaccessible.
6. Protected access works only through the derived class's own type.
7. Not inherited: constructors (unless `using Base::Base`), destructor, copy assignment, friends.
8. Order: base → members → body; destruction reversed. Multiple bases in **declaration order**.
9. Base constructor arguments only via the initialiser list; required if there's no default constructor.
10. A derived name hides **all** base overloads; fix with `using Base::f;`.
11. Diamond: two base copies; fix with virtual inheritance on the intermediate classes; the **most-derived class constructs the virtual base**, first.
12. Slicing: copying a derived object by value into a base loses the derived part; use references or pointers.
13. Upcast implicit and safe; downcast explicit, and checked only with `dynamic_cast`.
14. Inheritance's main cost is tight coupling, hence "composition over inheritance".

### Common wrong answers (module)

- "Private members are not inherited."
- "Java supports multiple inheritance through classes."
- "Constructors are inherited."
- "In the diamond, `virtual` goes on the bottom class."
- "With virtual inheritance, the intermediate classes construct the base."
- "Virtual functions prevent slicing."
- "A derived `f(string)` overloads the base `f(int)`." It **hides** it.
- "Use inheritance to reuse code." Use it for is-a and polymorphism; reuse alone calls for composition.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is inheritance? | Deriving a class from another to reuse and extend it; models is-a | Why use it? (Polymorphism, more than reuse) |
| Types of inheritance? | Single, multiple, multilevel, hierarchical, hybrid | Which does Java not support? |
| Public vs protected vs private inheritance? | The mode caps member access (table); only public gives an is-a usable from outside | What does private inheritance model? (Implemented-in-terms-of) |
| Are private members inherited? | Yes, they take space, but they're inaccessible to the derived class | How does Derived reach them? (Base's public/protected functions) |
| Constructor order in inheritance? | Base first, then members, then the derived body; destructors in reverse | Why that order? |
| How to call a parameterised base constructor? | In the derived constructor's initialiser list | What if the base has no default constructor? |
| Diamond problem? | Two copies of the common base, so ambiguity | How does virtual inheritance fix it? Who constructs the base? |
| Object slicing? | Copying a derived object into a base by value loses the derived part and behaviour | How to avoid it? |
| Name hiding? | A derived member hides all base members with that name | Fix? (`using Base::f;`) |
| is-a vs has-a? | Inheritance vs composition | Square/Rectangle |
| Disadvantages of inheritance? | Tight coupling, fragile base class, rigid hierarchy | Alternative? (Composition, M5) |

### Practice: predict the output or the error

**P1.**
```cpp
struct A { A(){cout<<"A";} ~A(){cout<<"~A";} };
struct M { M(){cout<<"M";} ~M(){cout<<"~M";} };
struct B : A { M m; B(){cout<<"B";} ~B(){cout<<"~B";} };
struct C : B { C(){cout<<"C";} ~C(){cout<<"~C";} };
int main(){ C c; cout<<"|"; }
```
<details><summary>Answer</summary>

`AMBC|~C~B~M~A`
</details>

**P2.**
```cpp
struct A{A(){cout<<"A";}};
struct B:virtual A{B(){cout<<"B";}};
struct C:virtual A{C(){cout<<"C";}};
struct D:B,C{D(){cout<<"D";}};
int main(){ D d; }
```
What changes if both `virtual` keywords are removed?
<details><summary>Answer</summary>

`ABCD`. Without `virtual`: `ABACD`, because A is constructed twice, once per path.
</details>

**P3.**
```cpp
struct A{A(int x){cout<<"A"<<x;}};
struct B:virtual A{B():A(1){cout<<"B";}};
struct C:virtual A{C():A(2){cout<<"C";}};
struct D:B,C{D():A(3){cout<<"D";}};
int main(){ D d; }
```
<details><summary>Answer</summary>

`A3BCD`. The most-derived class (D) constructs the virtual base; B's `A(1)` and C's `A(2)` are ignored. If `D()` omitted `A(3)`, this would be a **compile error** (no `A()` exists).
</details>

**P4.**
```cpp
struct X{X(){cout<<"X";}};
struct Y{Y(){cout<<"Y";}};
struct Z:Y,X{ Z():X(),Y(){cout<<"Z";} };
int main(){ Z z; }
```
<details><summary>Answer</summary>

`YXZ`. Bases are built in declaration order (`Y, X`), not initialiser-list order.
</details>

**P5.**
```cpp
struct Animal{ virtual string speak() const {return "...";} virtual ~Animal()=default; };
struct Dog:Animal{ string speak() const override {return "woof";} };
void byVal(Animal a){cout<<a.speak()<<" ";}
void byRef(const Animal& a){cout<<a.speak()<<" ";}
int main(){ Dog d; byVal(d); byRef(d); Animal a=d; cout<<a.speak(); }
```
<details><summary>Answer</summary>

`... woof ...`. Pass-by-value and `Animal a = d` both slice.
</details>

**P6.** Does it compile?
```cpp
struct B { void f(int){} };
struct D : B { void f(std::string){} };
int main(){ D d; d.f(1); }
```
<details><summary>Answer</summary>

**No.** `D::f` hides `B::f`; `int` can't convert to `string`. Fix: `using B::f;` in D.
</details>

**P7.** Does it compile?
```cpp
class Base {};
class D : Base {};
int main(){ D d; Base* b = &d; }
```
<details><summary>Answer</summary>

**No.** `class` defaults to **private** inheritance, so `Base` is an inaccessible base. Fix: `class D : public Base`.
</details>

**P8.** Which line fails?
```cpp
class Base { protected: int x; };
class D : public Base {
public:
    void f(D& other, Base& b) { x = 1; other.x = 2; b.x = 3; }
};
```
<details><summary>Answer</summary>

`b.x = 3;`. Protected members are accessible only through objects of the derived class's own type.
</details>

**P9.** Design question: `class Stack : public std::vector<int>`, so Stack reuses push_back/pop_back. What's wrong with this, and what should it be?

<details><summary>Answer</summary>

A Stack is **not** a vector: through public inheritance, callers get `insert`, `erase`, `operator[]` and so on, which break stack discipline (LIFO only). That violates is-a and substitutability. Also, `vector` has no virtual destructor, so deleting a `Stack` through a `vector<int>*` is undefined behaviour. Use **composition**: `class Stack { vector<int> data; public: void push(int); int pop(); ... };`. That's exactly what `std::stack` does with its underlying container.
</details>

---

## Exit checklist

```
[ ] I can draw the five inheritance types and give an example of each
[ ] I can reproduce the access-mode table and explain the "ceiling" rule
[ ] I know class/struct default inheritance modes
[ ] I can explain "private members are inherited but inaccessible"
[ ] I can explain the protected-access-through-own-type rule
[ ] I can list what is not inherited
[ ] I can predict construction/destruction order in multilevel and multiple inheritance
[ ] I can explain name hiding and fix it with a using-declaration
[ ] I can draw the diamond with and without virtual inheritance
[ ] I can explain who constructs a virtual base and predict A3BCD-style outputs
[ ] I can explain object slicing, where it happens, and how to avoid it
[ ] I can apply is-a vs has-a, and explain Square/Rectangle
[ ] P1–P9 done
```

---

## Next

**Part 6: M4 — Polymorphism.** This is the centrepiece of the handbook and the module product-company interviewers probe hardest. It covers compile-time vs runtime polymorphism, function and operator overloading, `virtual`/`override`/`final`, **the vtable and vptr drawn out in memory**, why destructors must be virtual, pure virtual functions and abstract classes, interfaces in C++, overloading vs overriding vs hiding, and the trick questions (virtual calls in constructors, default arguments on virtual functions, private virtuals).
