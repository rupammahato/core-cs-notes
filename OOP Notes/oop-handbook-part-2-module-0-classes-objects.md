# OOP Placement Handbook (C++) — Part 2
# Module 0: Classes and Objects

**Module 0 · 2–3 hours · Tier 1 · Requires: C++ basics (DSA Part 2)**

---

## Why this module exists

Almost every OOP round opens with the same few questions: what is OOP, what are its pillars, how a class differs from an object, how a struct differs from a class, and what `this` is. These are warm-ups, and that makes them dangerous. A vague answer here tells the interviewer that the deeper questions will go badly too.

This module also covers the mechanics every later module relies on: static members, const member functions, and what an object actually looks like in memory. You need the memory picture before M4, because the vtable makes sense only once you know where an object's bytes come from.

The organising principle:

> **A class is a blueprint that costs no memory. An object is a block of memory laid out according to that blueprint. Member functions are not stored in the object; they are ordinary functions that receive the object's address as a hidden argument called `this`.**

Most of this module unpacks that one sentence.

---

## 0.1 OOP and the four pillars at a glance

### 1. What is it?

Object-oriented programming organises a program around **objects**, meaning bundles of data together with the functions that operate on that data. Procedural programming organises it around **functions** that pass data between each other.

### 2. Why does it exist?

In a large procedural program, data is passed around freely and any function can modify it. When something goes wrong, every function that touches the data is a suspect. OOP puts data behind an interface, so only the object's own methods can change it. That localises bugs, makes it possible to change internals without breaking callers, and lets you model the problem domain (an `Order`, a `Customer`, a `ParkingSpot`) directly in code.

### 3. Procedural vs object-oriented

| | Procedural (C) | Object-oriented (C++, Java) |
|---|---|---|
| Unit of organisation | Function | Class / object |
| Data and behaviour | Separate | Bundled together |
| Data access | Usually open to any function | Controlled by access specifiers |
| Reuse | Call functions; copy code | Inheritance, composition |
| Extending behaviour | Edit existing functions (add `if`/`switch` cases) | Add a new class (polymorphism) |
| Modelling | Steps of an algorithm | Entities in the problem domain |
| Good for | Small programs, scripts, performance-critical kernels | Large systems with many interacting entities |

OOP is not automatically better. A 50-line algorithm gains nothing from classes, which is why your DSA solutions are mostly free functions.

### 4. The four pillars

You will be asked to name them in the first five minutes. Give each one with a one-line definition and a concrete example.

| Pillar | One line | Example | Taught in |
|---|---|---|---|
| **Encapsulation** | Bundle data with the methods that use it, and restrict direct access to the data | `BankAccount` keeps `balance` private; only `deposit()`/`withdraw()` can change it, so it can never go negative | M2 |
| **Abstraction** | Expose *what* an object does and hide *how* | You call `car.start()` without knowing about fuel injection; a `Shape` interface exposes `area()` without saying how it is computed | M2 |
| **Inheritance** | Create a new class from an existing one, reusing and extending it (an "is-a" relationship) | `SavingsAccount` is a `BankAccount` with an added `addInterest()` | M3 |
| **Polymorphism** | One interface, many implementations; the call is resolved to the right version automatically | `shape->area()` runs the circle formula for a `Circle` and the rectangle formula for a `Rectangle` | M4 |

**A model 60-second answer:**
*"OOP organises code around objects that bundle data with behaviour. It has four pillars. Encapsulation hides an object's data behind its methods: a bank account's balance is private, so only deposit and withdraw can change it. Abstraction exposes what an object does and hides how; I call `start()` on a car without knowing the engine internals. Inheritance lets a class reuse another, like a savings account that is a bank account plus interest. Polymorphism lets one call behave differently depending on the actual object, so `area()` on a shape pointer does the right thing for a circle or a square."*

### 5. Is C++ a pure object-oriented language?

**No.** In a pure OO language everything is an object and all code lives inside classes. C++ allows free functions, global variables and primitive types (`int`, `char`) that are not objects, and `main` sits outside any class. C++ is **multi-paradigm**: procedural, object-oriented and generic.

*Java is not pure either*, because of its primitive types. Smalltalk and Ruby are the usual examples of pure OO languages.

### 6. Must remember

1. Four pillars: **Encapsulation, Abstraction, Inheritance, Polymorphism**. Some sources list three, folding abstraction into encapsulation. Name four.
2. Every pillar answer needs a concrete example. Definitions alone score half.
3. C++ is multi-paradigm, not pure OO.

### 7. Common wrong answers

- "OOP is faster than procedural code." It isn't. Virtual calls and indirection cost a little; OOP's gains are in maintainability.
- Defining encapsulation and abstraction with the same words ("hiding data"). The difference is the most common follow-up and gets a full section in M2.
- "C++ is fully object-oriented because it has classes."

---

## 0.2 Class and object

### 1. What is it?

A **class** is a user-defined type: a description of what data an object holds (data members) and what it can do (member functions). An **object** is an instance of a class, meaning an actual region of memory holding values for those data members.

### 2. Core idea

```
          class Car                         objects (instances)
   +---------------------------+
   | data:                     |       c1                  c2
   |   string brand            |   +-----------+       +-----------+
   |   int speed               |   | "Tata"    |       | "BMW"     |
   | behaviour:                |   | 60        |       | 120       |
   |   void accelerate(int)    |   +-----------+       +-----------+
   |   int getSpeed()          |    own copy of         own copy of
   +---------------------------+    the data            the data
      a blueprint: no memory           both share ONE copy of the code
      for data is allocated            for accelerate() and getSpeed()
```

**The class is the blueprint and the object is the house.** You can build many houses from one blueprint. Each house has its own rooms (data), but they all follow the same plan (code).

### 3. How it works

```cpp
#include <iostream>
#include <string>
using namespace std;

class Car {
private:                                // data hidden from outside
    string brand;
    int speed;

public:                                 // interface visible to outside
    Car(string b, int s) : brand(b), speed(s) {}   // constructor (M1)

    void accelerate(int delta) { speed += delta; }
    int getSpeed() const { return speed; }          // const: see 0.7
};

int main() {
    Car c1("Tata", 60);                 // object on the stack
    Car* c2 = new Car("BMW", 120);      // object on the heap

    c1.accelerate(10);                  // dot for objects
    c2->accelerate(5);                  // arrow for pointers

    cout << c1.getSpeed() << " " << c2->getSpeed() << "\n";   // 70 125
    delete c2;                          // heap objects need delete
}
```

### 4. Class vs object

| | Class | Object |
|---|---|---|
| What it is | A type, a blueprint | An instance of that type |
| Memory | None for data members (code exists once) | Allocated for its data members |
| How many | Declared once | Any number |
| When it exists | Compile time | Runtime (created and destroyed) |
| Analogy | Blueprint, cookie cutter | House, cookie |
| Example | `class Car {...};` | `Car c1("Tata", 60);` |

### 5. Ways to create an object (and a trap)

```cpp
Car a("Tata", 60);       // direct initialisation, stack
Car b = Car("BMW", 90);  // copy-initialisation; no copy actually happens (C++17, see M1)
Car c{"Audi", 80};       // brace (uniform) initialisation
Car* d = new Car("Kia", 50);   // heap: you own it; must delete

class Point { public: int x = 0, y = 0; };
Point p1;       // OK: default-constructed object
Point p2();     // TRAP: declares a FUNCTION named p2 returning Point
Point p3{};     // OK: value-initialised object
```

`Point p2();` is the **most vexing parse**. C++ reads anything that *can* be a function declaration as one. The fix is `Point p2;` or `Point p2{};`. It makes a good output-prediction trick: `p2.x` fails to compile, because `p2` is a function.

### 6. Must remember

1. A class takes no memory for its data until you create an object.
2. Every object has its own copy of the non-static data members. There is only **one** copy of each member function's code, shared by all objects.
3. `.` for objects and references, `->` for pointers.
4. `T x();` declares a function, not an object.
5. Heap objects created with `new` must be `delete`d, or better, owned by a smart pointer (M6).

### 7. Interview questions

- *"What's the difference between a class and an object?"* A class is a user-defined type that describes data and behaviour, and it has no storage for data. An object is an instance with its own memory for the data members. One class, many objects. *Follow-up: "Does each object get its own copy of the member functions?"* No. Functions exist once in the code segment. Each object passes its own address to them as `this` (0.5).
- *"Can you create an object without a class?"* Not in C++. Every object has a type. (Primitive variables like `int x` are objects in the C++ standard's sense, but not class instances.)

---

## 0.3 struct vs class

### 1. The entire difference

In C++, `struct` and `class` are **the same thing** apart from two defaults:

| | `struct` | `class` |
|---|---|---|
| Default member access | `public` | `private` |
| Default inheritance mode | `public` | `private` |

That is the whole list. A `struct` can have constructors, destructors, member functions, virtual functions, private members, inheritance and templates, exactly like a `class`.

```cpp
struct S { int x; };              // x is public
class  C { int x; };              // x is private

struct D1 : S {};                 // public inheritance by default
class  D2 : C {};                 // private inheritance by default
```

### 2. Convention (what to say about usage)

- Use `struct` for **passive data aggregates** with no invariants: `Point`, `Edge`, a DSA `TreeNode`.
- Use `class` when there are **invariants to protect**, meaning private data guarded by methods.

### 3. The C vs C++ comparison (the other version of this question)

Sometimes the question is "struct in C vs struct in C++":

| | C `struct` | C++ `struct` |
|---|---|---|
| Member functions | No | Yes |
| Access specifiers | No | Yes |
| Constructors / destructors | No | Yes |
| Inheritance | No | Yes |
| Static members | No | Yes |
| Need `struct` keyword to declare a variable | Yes (`struct S s;`) unless `typedef`'d | No (`S s;`) |
| Empty struct size | Not allowed in standard C (a GCC extension gives size 0) | 1 byte |

### 4. Common wrong answers

- "Structs can't have functions." True in C, false in C++.
- "Structs are stored on the stack and classes on the heap." That is C#'s distinction, not C++'s. In C++ both can live anywhere.
- "Structs can't have private members." They can; members are just public by default.

### 5. Interview question

- *"Difference between struct and class in C++?"* Only the defaults: struct members and inheritance are public by default, class members and inheritance are private by default. Everything else is identical. By convention, struct is for plain data and class is for types with invariants. *Follow-up: "Then why have both?"* Backward compatibility with C, which had `struct`. `class` was added to signal the encapsulated, OO intent.

---

## 0.4 Access specifiers (the basics)

### 1. What is it?

Keywords that control **who can name a member**.

| Specifier | Accessible from member functions of the same class | From derived classes | From outside (e.g. `main`) |
|---|---|---|---|
| `public` | Yes | Yes | Yes |
| `protected` | Yes | Yes | No |
| `private` | Yes | No | No |

`friend` functions and classes (M2) get the same access as members. Protected access has a subtlety covered in M3 (§3.3).

### 2. Access control is per class, not per object

This is a classic trick question:

```cpp
class Account {
    int balance = 0;
public:
    bool richerThan(const Account& other) const {
        return balance > other.balance;   // LEGAL: other.balance is private,
    }                                     // but we are inside Account's code
};
```

A member function of `Account` can read the private members of **any** `Account` object, not just `this`. Access is checked at compile time against the *code's* class, not the object. That is why a copy constructor can read the private fields of the object it copies.

### 3. Must remember

1. Default is `private` for `class` and `public` for `struct`.
2. Access is per class, not per object.
3. Access control is a **compile-time** check. It is not a security mechanism: with pointer arithmetic you can read private memory. It protects against mistakes, not malice.
4. Private members are still **inherited**. They exist inside the derived object and take up space; the derived class just can't name them (M3).

### 4. Java note

Java has a fourth level, package-private (no keyword), and its `protected` also grants access to the same package. C++ has no packages and only three levels.

---

## 0.5 The `this` pointer

### 1. What is it?

Inside every non-static member function, `this` is a pointer to the object the function was called on.

### 2. Why does it exist?

Member functions exist once in memory, but they need to know *which* object's data to touch. The compiler solves this by passing the object's address as a hidden first argument.

### 3. Core idea: what the compiler actually does

```cpp
// What you write
class Car {
    int speed;
public:
    void accelerate(int d) { speed += d; }
};
c1.accelerate(10);

// Roughly what the compiler generates
void Car_accelerate(Car* const this, int d) { this->speed += d; }
Car_accelerate(&c1, 10);
```

Every unqualified member access such as `speed` inside a member function is really `this->speed`.

### 4. The three uses you need to know

```cpp
class Box {
    int width;
public:
    // Use 1: disambiguate a parameter that shadows a member
    Box(int width) { this->width = width; }       // left is member, right is parameter

    // Use 2: return the object itself to allow chaining
    Box& setWidth(int w) { width = w; return *this; }
    Box& grow(int d)     { width += d; return *this; }

    // Use 3: pass the current object to another function
    void registerWith(class Registry& r);          // e.g. r.add(this)
};

Box b(1);
b.setWidth(10).grow(5);                            // chaining: width == 15
```

For chaining, return `*this` **by reference**. If you return by value (`Box setWidth(...)`), the second call modifies a temporary copy and the original object changes only once.

### 5. The type of `this`

| Member function | Type of `this` |
|---|---|
| Non-const member of class `X` | `X*` (a prvalue, so you cannot assign to it) |
| `const` member of class `X` | `const X*`, which is why you cannot modify members |
| Static member function | **There is no `this`** |

### 6. Must remember

1. `this` is a hidden parameter, not a member. It takes **no space** in the object.
2. `this` cannot be reassigned (`this = nullptr;` does not compile).
3. Static member functions have no `this`, which is why they can't touch non-static members.
4. Return `*this` by reference for chaining.
5. **`delete this`** is legal *only* if the object was allocated with `new` and nothing touches it afterwards, including members and the caller. It is an advanced, rarely justified idiom. Know that it exists and say it is risky.

### 7. Interview questions

- *"What is the `this` pointer?"* A pointer to the object a member function was called on, passed by the compiler as a hidden argument. It lets one shared copy of the function's code work on any object's data. *Follow-up: "Is `this` available in static functions?"* No. Static functions are not called on an object, so there is nothing to point to.
- *"What is the size cost of `this`?"* Zero inside the object. It is a function argument (usually passed in a register), not a stored member.

---

## 0.6 Static members

### 1. What is it?

A **static data member** belongs to the class rather than to any object: there is exactly one copy, shared by all objects. A **static member function** belongs to the class and is called without an object.

### 2. Why does it exist?

For data that is about the class as a whole: an instance counter, a shared configuration, an ID generator, a cache shared by all instances. A global variable could hold such data too, but then nothing ties it to the class or protects it with access control.

### 3. Core idea

```
   class Student                     memory
   static int count  ----------->  [ count = 3 ]   one copy, static storage
                                                   exists even with 0 objects
   s1: [ name | roll ]
   s2: [ name | roll ]   <- objects contain ONLY non-static members
   s3: [ name | roll ]
```

### 4. How it works

```cpp
class Student {
    string name;
    static int count;                        // DECLARATION only
public:
    Student(string n) : name(n) { count++; }
    ~Student() { count--; }
    static int getCount() { return count; }  // no 'this'; touches only statics
};

int Student::count = 0;                      // DEFINITION: exactly one, in one .cpp

int main() {
    cout << Student::getCount() << "\n";     // 0  — callable with no objects
    Student a("Asha"), b("Ravi");
    {
        Student c("Meera");
        cout << Student::getCount() << "\n"; // 3
    }                                        // c destroyed here
    cout << a.getCount() << "\n";            // 2  — also callable via an object
}
```

**The out-of-class definition.** `static int count;` inside the class is only a declaration. Without `int Student::count = 0;` you get a **linker error** ("undefined reference to Student::count"). Two modern alternatives:

```cpp
class A {
    static const int MAX = 100;      // OK: const integral can be initialised in-class
    inline static int count = 0;     // C++17: inline static, no outside definition needed
    static constexpr double PI = 3.14159;   // constexpr static, also fine in-class
};
```

### 5. Static member functions: the rules

| Can a static member function... | Answer | Why |
|---|---|---|
| Access static data members | Yes | They don't need an object |
| Access non-static members directly | **No** | There is no `this` |
| Be `const` | **No** | `const` qualifies `this`, which doesn't exist |
| Be `virtual` | **No** | Virtual dispatch needs an object (and its vptr) |
| Be called via `ClassName::f()` | Yes | The normal way |
| Be called via `obj.f()` | Yes | Legal; the object is ignored |

A static function *can* access non-static members of an object passed to it as a parameter (`void f(Student& s) { s.name; }`), because access is per class (0.4).

### 6. The three meanings of `static` in C++

A favourite follow-up, because one keyword does three different jobs:

| Where | Meaning |
|---|---|
| Static **member** (data or function) | Belongs to the class, not the object |
| Static **local variable** in a function | Initialised once, keeps its value across calls (lives for the whole program) |
| Static **global** variable or free function | Internal linkage: visible only inside this `.cpp` file |

```cpp
int nextId() {
    static int id = 0;        // initialised once, on the first call
    return ++id;              // 1, 2, 3, ... across calls
}
```

### 7. Must remember

1. One copy per class, shared by all objects; it exists before any object is created.
2. Static data members **do not count toward `sizeof(object)`**.
3. A non-inline static data member needs exactly one out-of-class definition, or you get a linker error.
4. Static member functions have no `this`, so they can't be `const` or `virtual` and can't touch non-static members directly.
5. A static local variable is initialised on first use, and since C++11 that initialisation is **thread-safe**. This fact powers the Meyers Singleton (M8).

### 8. Common wrong answers

- "A static function can access any member." Only static ones, unless it is given an object.
- "Static members are stored inside each object." They are stored once, in static storage.
- Forgetting the out-of-class definition and calling the linker error a compiler error.

### 9. Interview questions

- *"How would you count the number of objects of a class currently alive?"* A static counter, incremented in every constructor (including the copy constructor) and decremented in the destructor. *Follow-up: "What if the counter is wrong after copying?"* The implicit copy constructor doesn't increment it. You must write the copy constructor too, which is a preview of the rule of three (M1).
- *"Why can't static member functions be virtual?"* Virtual dispatch looks up the function through the object's vptr. A static function is called without an object, so there is nothing to look up.

---

## 0.7 Const member functions

### 1. What is it?

A member function marked `const` after its parameter list promises not to modify the object.

```cpp
class Circle {
    double r;
public:
    double area() const { return 3.14159 * r * r; }   // read-only
    void setR(double x) { r = x; }                    // modifies
};
```

### 2. Why does it exist?

Because `const` objects and `const&` parameters are everywhere: `void print(const Circle& c)`. On a const object, the compiler allows **only** const member functions. If `area()` weren't marked const, `c.area()` inside `print` would not compile.

### 3. The rules

| Rule | Detail |
|---|---|
| Inside a const function, `this` is `const X*` | So `r = 5;` is a compile error |
| A const function can only call other const member functions | Calling a non-const one would allow modification |
| Const objects can only call const member functions | `const Circle c(1); c.setR(2);` is an error |
| Non-const objects can call both | |
| `const` is part of the signature | You can overload `f()` and `f() const`; the const one is chosen for const objects |
| `mutable` members can be changed even in const functions | For caches, counters and mutexes, which are logically not part of the object's state |

```cpp
class Text {
    string data;
    mutable int readCount = 0;          // bookkeeping, not "real" state
public:
    char  at(int i) const { readCount++; return data[i]; }  // OK: mutable
    char& at(int i)       { return data[i]; }               // non-const overload
};
// const Text t; t.at(0) -> calls const version, returns a copy
// Text u;       u.at(0) = 'x' -> calls non-const version, returns a reference
```

### 4. Must remember

1. **Mark every function that doesn't modify the object as `const`.** Forgetting this is the most common reason a function "mysteriously" fails to compile when called through a `const&`.
2. Const objects can call only const member functions.
3. You can overload on constness; `operator[]` in `vector` does exactly this.
4. `mutable` is for state that is logically invisible to callers (caches, mutexes).
5. Constructors and destructors cannot be const. (They can still run for a const object, because the object isn't const until construction finishes.)

### 5. Interview question

- *"What is a const member function, and why use it?"* It promises not to modify the object; inside it `this` is a pointer-to-const. It's needed so the function can be called on const objects and through const references, which is how most objects are passed. *Follow-up: "Can a const function ever modify a member?"* Yes, if the member is declared `mutable`. That is used for caches or locks.

---

## 0.8 Object memory layout and `sizeof`

### 1. What goes into an object

| Inside the object (counts toward `sizeof`) | NOT inside the object |
|---|---|
| Non-static data members | Member functions (code segment, once) |
| Padding for alignment | Static data members (static storage, once) |
| A hidden **vptr** if the class has any virtual function (M4) | The `this` pointer (a function argument) |
| Base class sub-objects (M3) | Type information |

### 2. The empty class

```cpp
class Empty {};
cout << sizeof(Empty);     // 1
```

**Why not 0?** Every object must have a **unique address**. If `sizeof(Empty)` were 0, then in `Empty arr[10];` every element would sit at the same address, `&arr[0] == &arr[1]` would be true, and pointer arithmetic would break. The compiler adds one byte to keep objects distinct.

**Empty base optimisation (EBO).** When an empty class is used as a *base*, the compiler may give it zero size inside the derived object:

```cpp
class D : Empty { int x; };
cout << sizeof(D);         // 4 on typical compilers, not 5 or 8
```

### 3. Padding and alignment

Types have alignment requirements: an `int` usually wants an address divisible by 4, and a `double` one divisible by 8. The compiler inserts padding between members, and at the end of the object, so that an *array* of the struct keeps every element aligned.

```
struct A { char c; int i; char d; };     // typical sizeof = 12

offset: 0    1  2  3   4  5  6  7    8    9 10 11
        [c] [pad pad pad][   i    ]  [d] [pad pad pad]
                                          ^ trailing padding so A[1].i is aligned

struct B { int i; char c; char d; };     // typical sizeof = 8

offset: 0  1  2  3    4    5    6  7
        [   i    ]   [c]  [d]  [pad pad]
```

**Same members, different order, 12 bytes vs 8.** Ordering members from largest to smallest alignment minimises padding.

### 4. The `sizeof` table to know (typical 64-bit Linux/GCC)

| Class | `sizeof` | Why |
|---|---|---|
| `class E {};` | 1 | Unique-address rule |
| `class A { int x; void f(); };` | 4 | Functions take no space |
| `class B { int x; static int s; };` | 4 | Statics take no space |
| `class C { char c; int i; char d; };` | 12 | Padding |
| `class D { int i; char c; char d; };` | 8 | Better ordering |
| `class F { char c; double d; };` | 16 | 1 + 7 padding + 8 |
| `class V { virtual void f(); };` | 8 | Hidden vptr (M4) |
| `class W { int x; virtual void f(); };` | 16 | 8 (vptr) + 4 + 4 padding |
| `class G : E { int x; };` | 4 | Empty base optimisation |
| `class H { E e; int x; };` | 8 | Empty *member* still takes 1 byte, + 3 padding |

These values are **implementation-defined**. Say "typically, on a 64-bit compiler" in an interview, because that's the precise answer.

### 5. Must remember

1. Empty class: size 1, so that distinct objects have distinct addresses.
2. Functions, static members and `this` add nothing to `sizeof`.
3. One virtual function adds one pointer (the vptr), however many virtual functions the class has.
4. Padding depends on member order; sorting members by decreasing size minimises it.
5. Exact numbers are implementation-defined.

### 6. Interview questions

- *"What is the size of an empty class? Why?"* 1 byte, typically. Two distinct objects must have distinct addresses, which zero size would break, for example in an array. *Follow-up: "What if it is used as a base class?"* The empty base optimisation lets it take 0 bytes inside the derived object.
- *"Does adding member functions increase an object's size?"* No. Adding *one* virtual function does, by one pointer, and adding more virtual functions after that adds nothing more.

---

## 0.9 Where objects live: stack vs heap, `new` vs `malloc`

### 1. Stack vs heap objects

| | Stack (`Car c;`) | Heap (`Car* p = new Car;`) |
|---|---|---|
| Lifetime | Ends automatically at the closing `}` | Until you `delete` it |
| Destructor | Called automatically | Called by `delete` |
| Speed | Very fast (move the stack pointer) | Slower (allocator call) |
| Size limit | Small (typically 1–8 MB per thread) | Large |
| Risk | Dangling references if you return its address | Leaks (forgot `delete`), double delete, dangling pointers |
| Use when | The default | The object must outlive the scope, is large, or its size or type is known only at runtime (polymorphism) |

### 2. `new` vs `malloc` (a very common question)

| | `new` | `malloc` |
|---|---|---|
| What it is | Operator (overloadable per class) | Library function |
| Calls the constructor | **Yes** | **No** (raw bytes) |
| Return type | Correctly typed pointer | `void*` (needs a cast in C++) |
| Size | Computed by the compiler | You pass it in bytes |
| On failure | Throws `std::bad_alloc` | Returns `NULL` |
| Release with | `delete` (calls the destructor) | `free` (no destructor) |
| Arrays | `new T[n]` / `delete[]` | `malloc(n * sizeof(T))` / `free` |

**Never mix them.** `delete` on `malloc`'d memory, `free` on `new`'d memory, or `delete` on `new[]`'d memory is **undefined behaviour**.

### 3. Must remember

1. Prefer stack objects; use the heap only when you need it.
2. `new` = allocate + construct; `delete` = destruct + deallocate. `malloc` and `free` do only the memory half.
3. `new[]` must pair with `delete[]`.
4. In modern C++, raw `new`/`delete` in application code is a code smell. Use `std::make_unique` (M6).

---

## 0.10 Consolidation

### Must remember (module)

1. Class = blueprint (no data memory); object = instance (own copy of the data).
2. Four pillars, each with an example.
3. struct vs class: only default member access and default inheritance mode differ.
4. Access control is per class, not per object, and is checked at compile time.
5. `this` is a hidden argument, `X*` in normal functions and `const X*` in const functions; there is none in static functions.
6. Static data: one copy per class, needs an out-of-class definition unless `inline`/`const` integral/`constexpr`, and isn't counted in `sizeof`.
7. Static functions: no `this`, so they can't be `const` or `virtual`.
8. Const objects can only call const member functions; mark every non-mutating method `const`.
9. Empty class is 1 byte; a vptr adds 8 bytes on 64-bit; padding depends on member order.
10. `new` constructs; `malloc` doesn't. Never mix allocation families.
11. `T x();` declares a function.

### Common wrong answers (module)

- "struct members are public and can't have functions."
- "Each object stores its own copy of the member functions."
- "The size of an empty class is 0."
- "Static functions can be virtual."
- "`malloc` and `new` are the same except syntax."
- Defining encapsulation and abstraction identically.

### Interview Q&A bank (rapid fire)

| Question | Crisp answer |
|---|---|
| What is OOP? | Organising a program around objects that bundle data with behaviour, built on encapsulation, abstraction, inheritance and polymorphism |
| Is C++ pure OO? | No; it allows free functions, globals and primitives. It's multi-paradigm |
| Class vs object? | Type vs instance; a class has no data storage, an object does |
| struct vs class? | Default access and default inheritance are public vs private; nothing else |
| What is `this`? | Hidden pointer to the calling object, passed to every non-static member function |
| Static data member? | One shared copy per class, existing independently of objects |
| Why can't a static function access non-static members? | It has no `this` |
| Const member function? | Promises not to modify the object; required for calls on const objects |
| `mutable`? | Lets a member change inside const functions; used for caches and locks |
| Empty class size? | 1, so that objects have unique addresses |
| Do member functions take space in the object? | No; one virtual function adds a vptr |
| `new` vs `malloc`? | `new` calls the constructor, is typed, and throws on failure; `malloc` gives raw bytes and returns NULL |

### Practice: predict the output or the error

Do these on paper before compiling.

**P1.**
```cpp
class A { static int n; public: A() { n++; } static int get() { return n; } };
int A::n = 0;
int main() { A a, b; A c[3]; A* p = new A; cout << A::get(); delete p; }
```
<details><summary>Answer</summary>

`6`. Two named objects, three array elements and one heap object each run the constructor once. `delete` doesn't decrement anything, because there is no destructor logic.
</details>

**P2.**
```cpp
class B { int x = 5; public: int get() { return x; } };
int main() { const B b; cout << b.get(); }
```
<details><summary>Answer</summary>

**Compile error.** `get()` is not `const`, so it cannot be called on a const object. Fix: `int get() const`.
</details>

**P3.**
```cpp
struct P { char a; double b; char c; };
struct Q { double b; char a; char c; };
int main() { cout << sizeof(P) << " " << sizeof(Q); }
```
<details><summary>Answer</summary>

Typically `24 16`. P = 1 + 7 pad + 8 + 1 + 7 trailing pad. Q = 8 + 1 + 1 + 6 trailing pad.
</details>

**P4.**
```cpp
class C { public: int v = 1; C& inc() { v++; return *this; } };
class D { public: int v = 1; D  inc() { v++; return *this; } };
int main() { C c; c.inc().inc(); D d; d.inc().inc(); cout << c.v << " " << d.v; }
```
<details><summary>Answer</summary>

`3 2`. `D::inc` returns a copy, so the second `inc()` modifies a temporary.
</details>

**P5.**
```cpp
class E { public: static void f() { cout << this; } };
```
<details><summary>Answer</summary>

**Compile error.** There is no `this` in a static member function.
</details>

**P6.**
```cpp
class F { public: int x = 7; };
int main() { F f(); cout << f.x; }
```
<details><summary>Answer</summary>

**Compile error.** `F f();` declares a function (the most vexing parse), so `f.x` is meaningless.
</details>

**P7.** Write a class `IdGen` whose objects each get a unique, increasing `id` on construction (1, 2, 3, ...), with a static function returning how many have been created in total. Make it compile without an out-of-class definition (C++17).

<details><summary>Answer</summary>

```cpp
class IdGen {
    inline static int created = 0;
    const int id;
public:
    IdGen() : id(++created) {}
    int getId() const { return id; }
    static int total() { return created; }
};
```

`id` is `const`, so it must be set in the initialiser list (M1).
</details>

---

## Exit checklist

```
[ ] I can name the four pillars with a one-line definition and an example each, in 60 s
[ ] I can explain why C++ is not a pure OO language
[ ] I can state the complete struct vs class difference (two defaults)
[ ] I know access control is per class, not per object
[ ] I can explain what `this` is, its type in const functions, and why statics lack it
[ ] I can write a static object counter, including the out-of-class definition
[ ] I can list the three meanings of `static`
[ ] I know why const objects can only call const functions, and what `mutable` is for
[ ] I can explain sizeof(empty class) == 1 and predict padding for a simple struct
[ ] I can give the new vs malloc table
[ ] I recognise the most vexing parse
[ ] P1–P7 done
```

---

## Next

**Part 3: M1 — Constructors, Destructors, and Copying.** This is the most C++-specific module and the source of most output-prediction questions. It covers every constructor type, initialiser lists (and the order trap), destructor rules, the order of construction and destruction, **shallow vs deep copy** with the double-free bug drawn out, copy constructor vs assignment operator, the rule of three/five/zero, move semantics essentials, `explicit`, and RAII.
