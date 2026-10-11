# OOP Placement Handbook (C++) — Part 13
# Consolidation: Cheat Sheets, Drill Bank, Rapid-Fire Q&A

**For the final 7–10 days before interviews · Requires: the modules you've done**

---

## How to use this part

This part contains no new teaching. It compresses Parts 2–12 into the forms you'll use when time is short:

| Section | Use it for | When |
|---|---|---|
| 13.1 Cheat sheets | Re-reading each module in 3 minutes | Daily in the final week |
| 13.2 Confusable pairs | The "difference between X and Y" questions (most OOP questions) | Every other day |
| 13.3 Output-prediction drill bank | Written tests, OAs, "what does this print?" rounds | Do it on paper, timed: 30 snippets in 45 minutes |
| 13.4 Rapid-fire Q&A | Spoken answers under 60 seconds | Have someone quiz you, or record yourself |
| 13.5 Patterns and LLD on one page | The night before an LLD round | Once |

**Every drill answer in §13.3 was produced by compiling and running the snippet with g++ 12 (`-std=c++17`).** Where behaviour is implementation-defined (`sizeof`), the answer says "typical".

---

## 13.1 Cheat sheets

### M0 — Classes and objects

- Four pillars: **Encapsulation** (protect data), **Abstraction** (hide complexity), **Inheritance** (is-a reuse), **Polymorphism** (one interface, many behaviours). Each needs an example.
- C++ is **multi-paradigm**, not pure OO.
- `struct` vs `class`: **only** the default member access and default inheritance mode differ (public vs private).
- Access is **per class, not per object**, and is checked at compile time.
- `this`: a hidden argument; `X*` (or `const X*` in const functions); there's none in static functions.
- Static data: one copy per class; needs an out-of-class definition unless `inline`/`constexpr`/const integral; **not in `sizeof`**.
- Static functions: no `this`, so they can't be `const` or `virtual`.
- Const objects call only const member functions; `mutable` is the exception.
- `sizeof(empty) == 1` (unique addresses); a vptr adds one pointer; padding depends on member order.
- `new` = allocate + construct; `malloc` = bytes only. Never mix the families. `T x();` declares a function.

### M1 — Constructors, destructors, copying

- Constructor: no return type; overloadable; can be private; **not virtual**. Any user-declared constructor removes the implicit default one.
- Initialiser list **mandatory** for: const members, references, members without a default constructor, bases without one.
- Members initialise in **declaration order**.
- Order: bases → members → body; destruction is the exact reverse. Static locals: once, lazily; destroyed after `main`.
- `X b = a;` → **copy constructor**. `b = a;` → **assignment**.
- Copy constructor parameter: `const X&` (by value = infinite recursion, so ill-formed).
- Default copy = memberwise = **shallow** for raw pointers → double free.
- Assignment: self-check, allocate before free, return `*this`; or **copy-and-swap**.
- Rule of 3 / 5 / **0**. A user-declared destructor or copy operation disables the implicit moves.
- `std::move` is a cast. Moved-from = valid but unspecified. Mark moves `noexcept`.
- `explicit` on one-argument constructors. Destructors are `noexcept`. A throwing constructor: no destructor call, but built members are destroyed.
- C++17: elision of prvalues guaranteed; NRVO optional; **parameters are never elided**.
- **RAII**: constructor acquires, destructor releases; stack unwinding guarantees it.

### M2 — Encapsulation and abstraction

- Encapsulation = bundling + access restriction → **protects invariants** (inside view; access specifiers).
- Abstraction = show what, hide how → **manages complexity** (outside view; abstract classes and interfaces).
- Blind getters and setters ≠ encapsulation: "tell, don't ask".
- Friend: not a member; **not inherited, not transitive, not mutual**; granted by the class. Canonical use: `operator<<`.

### M3 — Inheritance

- Types: single, multiple, multilevel, hierarchical, hybrid. Java: no multiple *class* inheritance.
- Access table: the mode is a **ceiling**; base-private is never accessible. `class` → private inheritance by default.
- Private members **are inherited** (they take space) but are inaccessible.
- Not inherited: constructors (unless `using Base::Base`), destructor, copy assignment, friends.
- Base constructor arguments only through the initialiser list.
- Name hiding: a derived name hides **all** base overloads → `using Base::f;`.
- Diamond: two base copies → **virtual inheritance** on the intermediate classes; the **most-derived class constructs the virtual base**, first.
- Slicing: copying a derived object into a base by value → use references/pointers, `vector<unique_ptr<Base>>`.
- is-a (with substitutability) → inherit; has-a → compose.

### M4 — Polymorphism

- Compile-time: overloading (parameters differ, **never return type alone**), operators, templates. Runtime: **virtual + pointer/reference**.
- Overload resolution: exact > promotion > conversion > user-defined; a tie is ambiguous.
- Can't overload: `:: . .* ?: sizeof typeid`. Must be members: `= [] () ->`.
- **vtable per class** (static array of function pointers); **vptr per object** (set by the constructor). Call = load vptr → fixed slot → indirect call.
- In constructors and destructors, virtual calls resolve to the **current class**.
- Polymorphic base ⇒ **virtual destructor** (otherwise deleting through the base is UB).
- Abstract class: at least one pure virtual; can't be instantiated; **can** have constructors, data and bodies (even for the pure virtual functions).
- C++ interface = only pure virtuals + a virtual destructor + no data.
- Overloading (same scope) / overriding (virtual, same signature) / **hiding** (same name).
- Default arguments come from the **static** type; access is checked on the static type; no virtual statics or virtual member templates; covariant `clone()`.
- Always write `override`.

### M5 — Relationships and UML

- Dependency < association < aggregation < composition < inheritance.
- **Test: destroy the whole; do the parts die?** Yes → composition (House–Room). No → aggregation (Team–Player).
- C++: composition → value member / `unique_ptr`; aggregation / association → non-owning pointer / reference (or `shared_ptr` when ownership is shared).
- Composition over inheritance: N + M classes instead of N × M; changeable at runtime (Strategy).
- UML: `+ - #`; diamond at the **whole** (hollow = aggregation, filled = composition); triangle at the **parent** (solid = inheritance, dashed = realization); dashed arrow = dependency; write multiplicities.

### M6 — Modern C++ object model

- `unique_ptr` (default, move-only, zero overhead) · `shared_ptr` (counted, control block, atomic counts) · `weak_ptr` (observer, breaks cycles, `lock()`).
- `make_unique` / `make_shared`; never two `shared_ptr`s from one raw pointer.
- The `shared_ptr` count is thread-safe; the object isn't. Cycles leak.
- Pass `T&` unless transferring (`unique_ptr` by value) or sharing (`shared_ptr` by value) ownership.
- Casts: static (compile-time), **dynamic** (checked; needs a virtual function; nullptr for pointers / `bad_cast` for references), const, reinterpret. Avoid C-style casts.
- `typeid` gives the dynamic type only for polymorphic types.
- **Catch by `const&`** (avoids slicing), most-derived first.
- Guarantees: no-throw > strong (copy-and-swap) > basic.
- CRTP = compile-time polymorphism: fast, but no mixed containers.

### M7 — SOLID

- **S**: one reason to change. **O**: extend by adding classes. **L**: subtypes substitutable (Square/Rectangle). **I**: no client depends on unused methods. **D**: depend on abstractions; inject them.
- Smells: god class (S), type switch (O), "not supported" override (L/I), `new Concrete` in business logic (D).
- DIP = principle, DI = technique, IoC = broader idea. DRY = knowledge, not text. YAGNI balances OCP. Law of Demeter: no `a.b().c().d()`.

### M8 — Design patterns

- Creational: Singleton, Factory, Builder. Structural: Adapter, Decorator. Behavioural: Strategy, Observer, State, Template Method.
- **Singleton**: private constructor, deleted copies, `static T& get() { static T t; return t; }` (thread-safe since C++11). Criticism: global state, testability.
- **Factory**: returns `unique_ptr<Base>`; the one place that knows the concrete types.
- **Strategy**: swappable algorithm behind an interface. **State**: states drive their own transitions.
- **Observer**: subscribe/notify; watch for dangling observers and mutation during notification.
- **Builder**: many optional parameters, chained setters, validate in `build()`. **Decorator**: same interface + wraps. **Adapter**: translates an incompatible interface.

### M9a / M9b — LLD

- Method: **clarify → entities → relationships → diagram → code core → extend**.
- Nouns → classes, fixed sets → enums, varying behaviour → interfaces. Don't subclass for data-only differences.
- Money in integers; time as a parameter; validate before mutating.
- Concurrency: find the **check-then-act**, lock it as one critical section, use the smallest sensible lock scope (per floor, per show), and keep a fixed lock order when taking several locks.
- Parking lot (allocation + fee strategies) · LRU (storage vs eviction policy; a read mutates) · Splitwise (net balances, split strategies, greedy settle-up) · Snake & Ladder (jumps map, validation, injectable dice) · Elevator (LOOK + dispatch strategy) · BookMyShow (per-show seat state, hold/confirm/expire, atomic all-or-nothing hold).

---

## 13.2 Confusable pairs: master table

| Pair | One-line distinction | Module |
|---|---|---|
| Class vs object | Type/blueprint vs instance with memory | M0 |
| struct vs class | Default public vs default private (members and inheritance) | M0 |
| `new` vs `malloc` | Constructs + typed + throws vs raw bytes + `void*` + NULL | M0 |
| Static vs non-static member | Per class (no `this`) vs per object | M0 |
| Const vs non-const member function | `this` is `const X*`; callable on const objects | M0 |
| Copy constructor vs copy assignment | Creates a new object vs overwrites an existing one | M1 |
| Shallow vs deep copy | Copies pointers vs copies the pointees | M1 |
| Copy vs move | Duplicate the resource vs steal it from an rvalue | M1 |
| Rule of three vs five vs zero | 3 special members vs + 2 moves vs none (self-managing members) | M1 |
| Initialisation vs assignment | Initialiser list (once) vs body (default-construct, then overwrite) | M1 |
| Abstraction vs encapsulation | Hide complexity (what/how) vs hide data (protect invariants) | M2 |
| Data hiding vs encapsulation | Access restriction vs bundling + restriction | M2 |
| Friend function vs member function | No `this`, not inherited vs called on an object | M2 |
| public vs protected vs private inheritance | The mode caps member access; only public is a usable is-a | M3 |
| Virtual vs non-virtual inheritance | One shared base vs one copy per path | M3 |
| Upcasting vs downcasting | Implicit, safe vs explicit, checked only with `dynamic_cast` | M3 |
| Overloading vs overriding vs hiding | Same scope, different parameters vs virtual, same signature vs same name, static | M4 |
| Compile-time vs runtime polymorphism | Overloads/templates vs virtual dispatch | M4 |
| Early vs late binding | Fixed call address vs vptr lookup | M4 |
| Virtual vs pure virtual function | Has a default implementation vs must be overridden (abstract) | M4 |
| Abstract class vs interface | State + partial code vs pure contract | M4 |
| vtable vs vptr | Per class, static vs per object, hidden member | M4 |
| Association vs aggregation vs composition | Knows vs has (independent) vs owns (lifetime) | M5 |
| Inheritance vs composition | is-a, static, tight vs has-a, dynamic, loose | M5 |
| `unique_ptr` vs `shared_ptr` vs `weak_ptr` | Exclusive vs counted vs observing | M6 |
| `static_cast` vs `dynamic_cast` | Unchecked, compile-time vs checked, runtime, polymorphic | M6 |
| Static vs dynamic polymorphism | Templates/CRTP vs virtual | M6 |
| SRP vs ISP | Split classes by reason to change vs split interfaces by client need | M7 |
| DIP vs DI vs IoC | Principle vs technique vs framework-controlled wiring | M7 |
| Singleton vs static class | An object (interfaces, laziness) vs a bag of functions | M8 |
| Factory vs Builder | Which class to create vs assembling one complex object | M8 |
| Strategy vs State | Client swaps the algorithm vs states drive transitions | M8 |
| Decorator vs Adapter | Same interface + behaviour vs different interface, translated | M8 |
| Strategy vs Template Method | Composition, runtime vs inheritance, compile time | M8 |
| Optimistic vs pessimistic locking | Verify version at write, retry vs lock before reading | M9b |
| LLD vs HLD | Classes and code vs services and infrastructure | M9a |

---

## 13.3 Output-prediction drill bank (30)

Rules: assume `#include <bits/stdc++.h>` and `using namespace std;`. Write your answer down **before** opening the solution. For "error" items, state which line fails and why. Target: 30 in 45 minutes, 27+ correct.

**D1.**
```cpp
struct C { static int n; C(){n++;} ~C(){n--;} };
int C::n = 0;
int main(){ C a; { C b = a; } cout << C::n; }
```
<details><summary>Answer</summary>

`0`. `C b = a` uses the **implicit copy constructor**, which doesn't increment `n`, but `b`'s destructor still decrements it: 1 − 1 = 0. This is why the copy constructor must be written whenever the constructor has side effects (rule of three).
</details>

**D2.**
```cpp
struct A{A(){cout<<"A";}~A(){cout<<"a";}};
struct B{B(){cout<<"B";}~B(){cout<<"b";}};
struct C:A{B b; C(){cout<<"C";}~C(){cout<<"c";}};
int main(){ C c; }
```
<details><summary>Answer</summary>

`ABCcba`. Base, then member, then body; destruction mirrors it.
</details>

**D3.**
```cpp
struct B{ virtual string f(){return "B";} virtual ~B()=default; };
struct D:B{ string f() override {return "D";} };
int main(){ D d; B& r=d; B* p=&d; B o=d; cout<<r.f()<<p->f()<<o.f()<<d.B::f(); }
```
<details><summary>Answer</summary>

`DDBB`. Reference and pointer dispatch dynamically; `o` is a sliced `B`; `d.B::f()` is a qualified call, so no dispatch.
</details>

**D4.**
```cpp
struct A{ A(){} A(const A&){cout<<"C";} A& operator=(const A&){cout<<"=";return *this;} };
A pass(A x){ return x; }
int main(){ A a; A b(a); A c = b; c = a; A d; d = pass(a); }
```
<details><summary>Answer</summary>

`CC=CC=`. `b(a)` → C; `c = b` (declaration) → C; `c = a` → =; `pass(a)`: the parameter copy → C, then `return x` → C (a **function parameter is never elided**, and `A` has no move constructor because its user-declared copy constructor suppresses the implicit move), then `d = ...` → =.
</details>

**D5.**
```cpp
struct T{ T(){} T(const T&){cout<<"C";} T(T&&) noexcept {cout<<"M";} };
int main(){ vector<T> v; v.reserve(3); T t; v.push_back(t); v.push_back(T()); v.push_back(std::move(t)); }
```
<details><summary>Answer</summary>

`CMM`. An lvalue is copied; a temporary is moved; `std::move` makes an rvalue, so it's moved. (`reserve` prevents reallocation, which would add extra moves.)
</details>

**D6.**
```cpp
struct Shape{ virtual string name() const {return "shape";} virtual ~Shape()=default; };
struct Circle:Shape{ string name() const override {return "circle";} };
int main(){ vector<Shape> v; v.push_back(Circle());
  vector<unique_ptr<Shape>> w; w.push_back(make_unique<Circle>());
  cout<<v[0].name()<<" "<<w[0]->name(); }
```
<details><summary>Answer</summary>

`shape circle`. `vector<Shape>` slices.
</details>

**D7.**
```cpp
struct B{ virtual void f(int x=10){cout<<"B"<<x;} virtual ~B()=default; };
struct D:B{ void f(int x=20) override {cout<<"D"<<x;} };
int main(){ B* p=new D; p->f(); delete p; }
```
<details><summary>Answer</summary>

`D10`. The body is dynamic; the default argument is static (from `B*`).
</details>

**D8.**
```cpp
struct B{ void f(int){cout<<"Bi";} void f(double){cout<<"Bd";} };
struct D:B{ using B::f; void f(char){cout<<"Dc";} };
int main(){ D d; d.f(1); d.f(2.0); d.f('x'); }
```
<details><summary>Answer</summary>

`BiBdDc`. `using B::f` brings the base overloads into D's scope, so all three overloads compete. Without it, every call would go to `f(char)`.
</details>

**D9.**
```cpp
struct V{V(){cout<<"V";}};
struct N{N(){cout<<"N";}};
struct X: N, virtual V { X(){cout<<"X";} };
int main(){ X x; }
```
<details><summary>Answer</summary>

`VNX`. **Virtual bases are constructed before all non-virtual bases**, regardless of declaration order.
</details>

**D10.**
```cpp
struct Base{ virtual ~Base()=default; };
struct Der:Base{};
int main(){ try{ throw Der(); } catch(const Base&){ cout<<"Base"; } catch(const Der&){ cout<<"Der"; } }
```
<details><summary>Answer</summary>

`Base`. The first matching handler wins, and `Der` matches `const Base&`. Order catch blocks from most derived to most general.
</details>

**D11.**
```cpp
void f(int){cout<<"i";} void f(double){cout<<"d";} void f(long){cout<<"l";}
int main(){ f('c'); f(1.0f); f(1L); f(true); }
```
<details><summary>Answer</summary>

`idli`. char→int is a promotion; float→double is a promotion; `1L` is an exact match for long; bool→int is a promotion.
</details>

**D12.**
```cpp
struct S{ void f(){cout<<"nc ";} void f() const {cout<<"c ";} };
int main(){ S s; const S cs; s.f(); cs.f(); const S& r=s; r.f(); }
```
<details><summary>Answer</summary>

`nc c c`. Overloading on const: the const version is chosen for const objects and const references.
</details>

**D13.** Typical 64-bit sizes?
```cpp
struct A{ char c; int i; };
struct B{ int i; virtual void f(){} };
struct E{};
struct F{ E e; char c; };
```
<details><summary>Answer</summary>

`8 16 1 2` (typical). A: 1 + 3 padding + 4. B: vptr 8 + 4 + 4 padding. E: 1. F: an empty *member* still takes 1 byte, + 1.
</details>

**D14.**
```cpp
int main(){ int i=5; int a = i++ + 10; int b = ++i + 10; cout<<a<<" "<<b<<" "<<i; }
```
<details><summary>Answer</summary>

`15 17 7`. Postfix uses the old value (5) then increments to 6; prefix increments to 7, then uses 7.
</details>

**D15.**
```cpp
struct A{ A(){cout<<"+";} ~A(){cout<<"-";} };
int main(){ A(); cout<<"|"; A a; cout<<"|"; }
```
<details><summary>Answer</summary>

`+-|+|-`. The unnamed temporary `A()` dies at the end of its full expression (`;`); `a` lives until `}`.
</details>

**D16.**
```cpp
struct A{ A(){cout<<"+";} ~A(){cout<<"-";} };
int main(){ const A& r = A(); cout<<"|"; }
```
<details><summary>Answer</summary>

`+|-`. Binding a temporary to a `const&` **extends its lifetime** to the reference's scope.
</details>

**D17.**
```cpp
struct B{ virtual void who(){cout<<"B";} virtual ~B(){ who(); } };
struct D:B{ void who() override {cout<<"D";} ~D(){ who(); } };
int main(){ B* p = new D; delete p; }
```
<details><summary>Answer</summary>

`DB`. Virtual destructor → `~D` runs (calls D's `who`), then `~B`, inside which the object is a `B` again, so B's `who` runs.
</details>

**D18.**
```cpp
struct B{ virtual ~B(){cout<<"~B";} };
struct M{ ~M(){cout<<"~M";} };
struct D:B{ M m; ~D(){cout<<"~D";} };
int main(){ B* p = new D; delete p; }
```
<details><summary>Answer</summary>

`~D~M~B`. Destructor body → members → base.
</details>

**D19.**
```cpp
struct M{ int v; M(int v):v(v){} };
M operator+(M a, M b){ return M(a.v+b.v); }
int main(){ cout << (1 + M(2)).v << (M(3) + 4).v; }
```
<details><summary>Answer</summary>

`37`. A **non-member** `operator+` allows the implicit int→M conversion on **either** side. A member `operator+` would reject `1 + M(2)`.
</details>

**D20.**
```cpp
void f(shared_ptr<int> p){ cout<<p.use_count(); }
int main(){ auto p=make_shared<int>(1); f(p); cout<<p.use_count(); f(std::move(p)); cout<<(p==nullptr); }
```
<details><summary>Answer</summary>

`2111`. Copying into the parameter gives count 2; after return, 1; moving transfers ownership (count stays 1), and `p` becomes null.
</details>

**D21.**
```cpp
struct L{ L(int x){cout<<x;} };
struct Q{ L a; L b; Q(): b(2), a(1) {} };
int main(){ Q q; }
```
<details><summary>Answer</summary>

`12`. Declaration order (`a`, then `b`), not initialiser-list order.
</details>

**D22.**
```cpp
struct B{ void f(){cout<<"B";} };
struct D:B{ void f(){cout<<"D";} };
int main(){ D d; B* p=&d; p->f(); d.f(); static_cast<B&>(d).f(); }
```
<details><summary>Answer</summary>

`BDB`. Not virtual, so the static type decides.
</details>

**D23.**
```cpp
struct A{ A(){cout<<"A";} A(const A&){cout<<"c";} };
void byVal(A){} void byRef(const A&){}
int main(){ A a; byVal(a); byRef(a); byVal(A()); }
```
<details><summary>Answer</summary>

`AcA`. Copy for the lvalue argument; nothing for the reference; the temporary initialises the parameter directly (guaranteed elision in C++17), so only its constructor runs.
</details>

**D24.**
```cpp
struct B{ B(){ cout<<"B"<<id(); } virtual int id(){ return 1; } virtual ~B()=default; };
struct D:B{ D(){ cout<<"D"<<id(); } int id() override { return 2; } };
int main(){ D d; }
```
<details><summary>Answer</summary>

`B1D2`. During B's constructor, the object is a B.
</details>

**D25.** Does it compile?
```cpp
struct M{ explicit M(int){} };
int main(){ M m = 5; }
```
<details><summary>Answer</summary>

**Error**: copy-initialisation can't use an `explicit` constructor ("conversion from 'int' to non-scalar type 'M' requested"). `M m(5);` or `M m{5};` work.
</details>

**D26.** Does it compile?
```cpp
int main(){ auto p = make_unique<int>(1); auto q = p; }
```
<details><summary>Answer</summary>

**Error**: `unique_ptr`'s copy constructor is deleted. Use `auto q = std::move(p);`.
</details>

**D27.** Does it compile?
```cpp
struct S{ virtual void f()=0; };
int main(){ S s; }
```
<details><summary>Answer</summary>

**Error**: you can't create an object of an abstract type. `S* p` or `S& r` would be fine.
</details>

**D28.** Does it compile?
```cpp
struct B{}; class D : B{};
int main(){ D d; B& r = d; }
```
<details><summary>Answer</summary>

**Error**: `class` defaults to **private** inheritance, so `B` is an inaccessible base of `D`.
</details>

**D29.** Does it compile?
```cpp
struct A{int x=0;}; struct B:A{}; struct C:A{}; struct D:B,C{};
int main(){ D d; d.x = 1; }
```
<details><summary>Answer</summary>

**Error**: `x` is ambiguous (the diamond without virtual inheritance gives two copies of `A`). Fix: `virtual` on B's and C's inheritance, or `d.B::x`.
</details>

**D30.** Does it compile?
```cpp
struct A{ A(int){} };
struct B : A { B(){} };
int main(){ B b; }
```
<details><summary>Answer</summary>

**Error**: `B()` implicitly calls `A()`, which doesn't exist. Fix: `B() : A(0) {}`.
</details>

*Bonus (no snippet needed):* why does `struct S { int v = 0; static int get() { return v; } };` fail? A static function has no `this`, so it can't use the non-static `v`.

---

## 13.4 Rapid-fire Q&A

Answer each out loud in under 30 seconds, then check.

### Basics (M0–M2)

| # | Question | Answer |
|---|---|---|
| 1 | Four pillars? | Encapsulation, abstraction, inheritance, polymorphism |
| 2 | Is C++ purely OO? | No: free functions, globals, primitives; multi-paradigm |
| 3 | struct vs class? | Default access and inheritance: public vs private |
| 4 | Size of an empty class? | 1, so that objects have unique addresses |
| 5 | What is `this`? | Hidden pointer to the calling object; absent in static functions |
| 6 | Why can't static functions be virtual or const? | No object/`this` to dispatch on or qualify |
| 7 | What does `mutable` do? | Allows modification inside const functions |
| 8 | `new` vs `malloc`? | `new` calls constructors, is typed, throws; `malloc` gives raw bytes, returns NULL |
| 9 | Abstraction vs encapsulation? | Hide complexity vs hide data; design vs implementation |
| 10 | Does `friend` break encapsulation? | No: granted explicitly by the class, part of its interface; avoid overuse |
| 11 | Is friendship inherited? | No; not transitive or mutual either |

### Constructors and copying (M1)

| # | Question | Answer |
|---|---|---|
| 12 | Can constructors be virtual? | No: no vptr yet; the type must be known to construct |
| 13 | Can constructors be private? | Yes (Singleton, factories) |
| 14 | When is the default constructor generated? | Only if no constructor is declared |
| 15 | When is an initialiser list mandatory? | const, reference, no-default-constructor member, base without a default constructor |
| 16 | Initialisation order of members? | Declaration order |
| 17 | When is the copy constructor called? | New object from an lvalue; pass/return by value (unless elided) |
| 18 | Why `const&` in the copy constructor? | By value would recurse; const allows copying const objects and temporaries |
| 19 | Shallow vs deep copy? | Pointer copied vs pointee copied; shallow causes double free |
| 20 | Rule of three / five / zero? | Destructor + copy constructor + copy assign / + moves / none needed |
| 21 | What does `std::move` do? | Casts to an rvalue; moves nothing itself |
| 22 | Why should move constructors be `noexcept`? | `vector` copies instead of moving otherwise |
| 23 | Can destructors throw? | Shouldn't; `noexcept` by default, so `terminate` |
| 24 | A constructor throws: is the destructor called? | No; built members are destroyed |
| 25 | RAII? | Resource lifetime = object lifetime |

### Inheritance and polymorphism (M3–M4)

| # | Question | Answer |
|---|---|---|
| 26 | Types of inheritance? | Single, multiple, multilevel, hierarchical, hybrid |
| 27 | Private members inherited? | Yes, but inaccessible |
| 28 | Diamond problem fix? | Virtual inheritance; the most-derived class constructs the base |
| 29 | Object slicing? | Derived copied into a base by value loses the derived part |
| 30 | Name hiding? | A derived name hides all base overloads; `using Base::f` |
| 31 | Overloading vs overriding? | Same scope, different parameters, compile time vs virtual, same signature, runtime |
| 32 | Can overloads differ by return type only? | No |
| 33 | How do virtual functions work? | vtable per class, vptr per object, indirect call |
| 34 | Cost of virtual? | A pointer per object, an indirect call, no inlining |
| 35 | Virtual destructor, why? | Deleting through a base pointer would skip the derived destructor (UB) |
| 36 | Virtual call in a constructor? | Resolves to the current class |
| 37 | Abstract class? | Has a pure virtual function; can't be instantiated |
| 38 | Can an abstract class have a constructor? | Yes |
| 39 | Can a pure virtual function have a body? | Yes |
| 40 | Abstract class vs interface? | State + code vs pure contract |
| 41 | Operators you can't overload? | `:: . .* ?: sizeof typeid` |
| 42 | Prefix vs postfix overload? | Postfix takes a dummy `int` and returns the old value |
| 43 | Early vs late binding? | Compile-time address vs vtable lookup |

### Design (M5–M8)

| # | Question | Answer |
|---|---|---|
| 44 | Aggregation vs composition? | Part outlives the whole vs part dies with it |
| 45 | Composition over inheritance? | Looser coupling, runtime flexibility, no class explosion |
| 46 | `unique_ptr` vs `shared_ptr`? | Exclusive, zero cost vs shared, counted |
| 47 | How does `shared_ptr` leak? | Cycles; fix with `weak_ptr` |
| 48 | `dynamic_cast` failure? | nullptr (pointer) / `bad_cast` (reference) |
| 49 | Why catch by reference? | Avoid slicing and copies |
| 50 | SOLID? | SRP, OCP, LSP, ISP, DIP, with one example each |
| 51 | LSP violation example? | Square extends a mutable Rectangle |
| 52 | DIP vs DI? | Principle vs technique |
| 53 | Thread-safe Singleton? | Function-local static (C++11) |
| 54 | Singleton drawbacks? | Global state, hard to test, hidden dependencies |
| 55 | Strategy vs State? | Client swaps vs states transition themselves |
| 56 | Decorator vs Adapter? | Same interface, adds behaviour vs converts an interface |
| 57 | When Builder? | Many optional parameters, validation, immutability |
| 58 | Observer pitfalls? | Dangling observers, mutation during notify, threading |

### LLD (M9a–M9b)

| # | Question | Answer |
|---|---|---|
| 59 | Your LLD approach? | Clarify, entities, relationships, diagram, code core, extend |
| 60 | Prevent double booking? | Atomic check-and-hold (one critical section / DB row lock / optimistic version check) |
| 61 | Why integers for money? | Floating-point rounding |
| 62 | Why can't an LRU `get` use a read lock? | It reorders the recency list, so it's a write |
| 63 | Elevator scheduling? | LOOK: continue while requests lie ahead, then reverse |

---

## 13.5 Patterns and LLD on one page

```
REQUIREMENT PHRASE                        -> PATTERN
"exactly one", "global config/logger"     -> Singleton (or one instance + DI)
"create X based on type/input"            -> Factory
"families that must match"                -> Abstract Factory
"many optional params", "immutable"       -> Builder
"multiple ways to do X", "pluggable rule" -> Strategy
"notify/subscribe/alert when"             -> Observer
"behaviour depends on status/lifecycle"   -> State
"add features in combinations", "wrap"    -> Decorator
"third-party/legacy interface"            -> Adapter
"same skeleton, different steps"          -> Template Method

LLD IN THE ROOM
1. Clarify: actors, use cases, variants (-> interfaces), rules, concurrency, out of scope
2. Entities: nouns -> classes, fixed sets -> enums, varying behaviour -> interfaces
3. Relationships: own (value/unique_ptr) vs refer (pointer/ref); multiplicities
4. Diagram: 6-10 boxes, correct arrows; walk one flow
5. Code: models -> interfaces -> strategies -> service -> demo; validate; integers for money
6. Extend: "that's a new class implementing X"; name the race; lock exactly it

THE SIX DESIGNS IN ONE LINE EACH
Parking Lot  : floors own spots; AllocationStrategy + FeeStrategy; find+park under one lock
LRU Cache    : map storage + EvictionPolicy (list::splice); exclusive lock (reads mutate); shard to scale
Splitwise    : net balance per user; Equal/Exact/Percent strategies in paise; heap-greedy settle-up
Snake&Ladder : one jumps map, validated board; injectable Dice; exact landing
Elevator     : set<int> stops + LOOK per car; DispatchStrategy cost function; State pattern only if states diverge
BookMyShow   : seat state per (show, seat); hold(TTL)->confirm->booked; atomic all-or-nothing under per-show lock
```

---

## Final checklist: OOP handbook complete

```
[ ] All module exit checklists ticked (M0-M9b)
[ ] Drill bank: 27+/30 correct on paper in 45 minutes
[ ] Rapid-fire: 60+/63 answered correctly out loud
[ ] Can deliver without notes: four pillars (60 s), abstraction vs encapsulation (40 s),
    vtable explanation (60 s), virtual destructor (30 s), SOLID (60 s)
[ ] Designed at least 3 of the 6 LLD problems from scratch under a timer
[ ] Re-read 13.1 and 13.2 the day before the interview
```

---

## Next

The OOP handbook is complete. The next handbook is **Operating Systems**, in the same format: Part 1 (master roadmap), then the modules from the approved plan (processes, threads, CPU scheduling with numericals, synchronization with C++ concurrency code, deadlocks and Banker's algorithm, memory management and paging, virtual memory and page replacement, storage, IPC, integrative questions), ending with a numericals formula sheet and rapid-fire Q&A.
