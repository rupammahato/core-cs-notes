# OOP Placement Handbook (C++) — Part 4
# Module 2: Encapsulation and Abstraction

**Module 2 · 1.5–2 hours · Tier 1 · Requires: M0, M1**

---

## Why this module is short but critical

"What is the difference between abstraction and encapsulation?" is the most frequently asked "difference between" question in OOP interviews, and the one most often answered badly. The usual bad answer defines both as "hiding things", which tells the interviewer you've memorised two words but not two ideas.

The two concepts are related. They usually appear together, and one class often demonstrates both. But they answer different questions:

> **Encapsulation answers "who is allowed to touch this data?" Abstraction answers "what does the user need to know to use this?" Encapsulation protects an object's insides; abstraction simplifies its outside.**

Hold on to that sentence and the rest of the module follows from it.

---

## 2.1 Encapsulation

### 1. What is it?

**Bundling data together with the functions that operate on it into one unit (a class), and restricting direct access to that data so that it can only be changed through those functions.**

There are two halves: **bundling** (data and methods live together) and **access restriction** (data is `private`, and the methods are the only door).

### 2. Why does it exist?

To protect **invariants**: rules that must always be true about an object's state.

```cpp
// No encapsulation: any code anywhere can break the rules
struct Account {
    double balance;             // anyone can write  acc.balance = -5000;
};

// Encapsulated: the invariant "balance >= 0" can never be violated
class Account {
    double balance = 0;         // private: only Account's own methods can touch it
public:
    void deposit(double amt) {
        if (amt <= 0) throw invalid_argument("deposit must be positive");
        balance += amt;
    }
    bool withdraw(double amt) {
        if (amt <= 0 || amt > balance) return false;   // the guard lives in ONE place
        balance -= amt;
        return true;
    }
    double getBalance() const { return balance; }
};
```

In the first version, the "balance can't go negative" rule must be enforced by every piece of code that touches `balance`. One forgetful caller breaks it. In the second, the rule is enforced in exactly one place, and the compiler guarantees there is no other way in.

### 3. The benefits (say three of these)

| Benefit | What it means |
|---|---|
| **Invariants are protected** | The object can never be put into an invalid state from outside |
| **Implementation can change freely** | Change `double balance` to `long long paise` and no caller notices, because they only use the methods |
| **Validation and logging in one place** | Every change goes through a method, so you can check, log or audit it |
| **Bugs are localised** | If `balance` is wrong, only `Account`'s methods can be the culprit |
| **Thread safety becomes possible** | A mutex inside the class can guard every access, which is impossible if fields are public |

### 4. Real-world analogies

- **A capsule (medicine):** the ingredients are sealed inside; you take the capsule as a whole.
- **An ATM:** you can't reach into the cash vault; you can only use the buttons, and each button enforces rules (PIN, balance, daily limit).

### 5. How C++ achieves it

1. A `class` bundles data and methods.
2. `private` (and `protected`) restrict access.
3. Public member functions form the only interface.
4. `const` member functions guarantee that read-only access really is read-only.

### 6. Must remember

1. Encapsulation = **bundling + access restriction**, for the purpose of **protecting invariants**.
2. It is achieved with classes and access specifiers.
3. The key benefit to mention: **you can change the internals without breaking any caller**.

---

## 2.2 Getters and setters are not automatically encapsulation

This is the point that separates a strong answer from a textbook one.

```cpp
class Account {
    double balance;
public:
    double getBalance() const { return balance; }
    void   setBalance(double b) { balance = b; }      // anyone can set -5000
};
```

This class has a private field, so it *looks* encapsulated. But `setBalance` lets any caller set any value, so the invariant is just as unprotected as with a public field. It is **a public field with extra steps**.

**Real encapsulation exposes operations that mean something in the domain** (`deposit`, `withdraw`, `transfer`), not raw access to fields. This principle is called **"Tell, don't ask"**: tell the object what to do, rather than asking for its data, changing it outside, and pushing it back.

```cpp
// Ask (weak): logic outside the object
if (acc.getBalance() >= amt) acc.setBalance(acc.getBalance() - amt);

// Tell (strong): logic inside the object
acc.withdraw(amt);
```

### When setters are fine

When a field genuinely has **no invariant** (a display name, a colour), or when the setter **validates**:

```cpp
void setAge(int a) {
    if (a < 0 || a > 150) throw invalid_argument("bad age");
    age = a;
}
```

A validating setter is encapsulation. A blind setter is not.

### Must remember

1. A private field with a blind getter and setter is barely better than a public field.
2. Expose **behaviour** (`withdraw`), not **data** (`setBalance`).
3. Setters are acceptable when they validate, or when the field has no invariant.

---

## 2.3 Data hiding vs encapsulation

A sub-question that comes up occasionally.

| | Data hiding | Encapsulation |
|---|---|---|
| What it is | Making data inaccessible from outside (`private`) | Bundling data with methods, **and** controlling access |
| Scope | One part of encapsulation | The whole idea |
| Focus | Restriction | Organisation + restriction |

**One line:** data hiding is the *mechanism*, the access restriction. Encapsulation is the *design principle* that uses data hiding together with bundling. You can bundle without hiding (a `struct` with methods and public fields), which is encapsulation's bundling half without the data hiding.

---

## 2.4 Abstraction

### 1. What is it?

**Exposing only what an object does, and hiding how it does it.** The user works with a simplified model and doesn't need to understand, or depend on, the details behind it.

### 2. Why does it exist?

To **manage complexity**. Nobody can hold a whole large system in their head. Abstraction lets each piece be understood through a small interface:

- You call `std::sort(v.begin(), v.end())` without knowing it's introsort.
- You call `car.start()` without knowing about fuel injection timing.
- You call `payment->pay(500)` without knowing whether it's UPI, a card or a wallet.

Abstraction also **decouples**. Code written against an abstraction keeps working when the implementation behind it changes or a new one is added.

### 3. Real-world analogies

- **A TV remote:** buttons for power, volume and channel; the infrared protocol is hidden.
- **Driving a car:** steering, accelerator, brake. You can drive any car without knowing its engine type.
- **An ATM** again: "withdraw ₹500" is the abstraction; the bank's ledger, network calls and cash-dispensing mechanics are hidden.

### 4. The levels of abstraction in C++

| Level | Mechanism | Example |
|---|---|---|
| **Function** | A function hides its steps behind a name | `sqrt(x)` |
| **Class interface** | Public methods hide the private implementation | `vector::push_back` hides reallocation |
| **Abstract class / interface** | Pure virtual functions define *what* without *how*; several classes provide the *how* | `PaymentMethod::pay()` (M4) |
| **Module / header** | The `.h` file declares, the `.cpp` file implements | Library APIs |

The third level is what interviewers usually mean by "abstraction in OOP":

```cpp
class PaymentMethod {                         // the abstraction: WHAT a payment can do
public:
    virtual bool pay(double amount) = 0;      // pure virtual: no HOW here
    virtual ~PaymentMethod() = default;
};

class UpiPayment : public PaymentMethod {     // one HOW
public:
    bool pay(double amount) override { /* call UPI gateway */ return true; }
};

class CardPayment : public PaymentMethod {    // another HOW
public:
    bool pay(double amount) override { /* tokenise card, call processor */ return true; }
};

void checkout(PaymentMethod& pm, double total) {   // depends only on the abstraction
    if (pm.pay(total)) cout << "Order placed\n";
}
```

`checkout` doesn't know or care which payment method it got. Adding `WalletPayment` tomorrow requires **no change** to `checkout`. That is the practical payoff of abstraction, and the bridge to polymorphism (M4) and the Open/Closed principle (M7).

### 5. Must remember

1. Abstraction = **show what, hide how**, for the purpose of **managing complexity**.
2. In C++ it is achieved mainly with **abstract classes** (pure virtual functions) and well-designed public interfaces.
3. The key benefit to mention: **callers depend on the interface, so implementations can be swapped or added without changing them**.

---

## 2.5 Abstraction vs encapsulation (the comparison)

### 1. The table

| | Abstraction | Encapsulation |
|---|---|---|
| **Core question** | What does the user need to know? | Who is allowed to touch the data? |
| **Hides** | **Complexity** (implementation details) | **Data** (internal state) |
| **Purpose** | Simplify the view; decouple users from implementations | Protect invariants; prevent invalid state |
| **Level** | Design level: what interface to expose | Implementation level: how to protect what's inside |
| **Viewpoint** | Outside view (the user's perspective) | Inside view (the object's integrity) |
| **Achieved in C++ with** | Abstract classes, pure virtual functions, interfaces, header/implementation split | Classes, `private`/`protected`, member functions |
| **Example** | `PaymentMethod::pay()`: callers don't know whether it's UPI or card | `Account::balance` is private, and only `withdraw()` can change it, with checks |
| **Without it** | Callers depend on details and break when the details change | Any code can corrupt the object's state |

### 2. How they relate

They aren't opposites; they **cooperate**. Encapsulation is often *how* abstraction is delivered: by hiding a class's data and internals behind methods (encapsulation), you present a simple interface (abstraction).

> One class can show both: `Account` *encapsulates* `balance` (private, guarded) and *abstracts* the transfer process (`transfer()` hides logging, fraud checks and ledger entries).

### 3. The model answer (aim for about 40 seconds)

*"Abstraction is about hiding complexity: exposing what an object does and not how. For example, a `PaymentMethod` interface with `pay()` lets checkout code work with UPI or cards without knowing how either works. It's a design-level idea, achieved in C++ with abstract classes. Encapsulation is about protecting data: bundling it with its methods and making it private, so that it can only change through controlled operations. For example, a bank account's balance is private, and `withdraw()` checks it never goes negative. It's achieved with access specifiers. Put simply, abstraction simplifies the outside view and encapsulation protects the inside. They work together, since encapsulating the internals is what makes a clean abstraction possible."*

### 4. Common wrong answers

- "Both are about hiding data." Only encapsulation hides *data*; abstraction hides *complexity*.
- "Abstraction is achieved using private members." Private members are encapsulation. Abstraction comes from interfaces and abstract classes (and public interfaces in general).
- "Encapsulation is getters and setters." See §2.2.
- "Abstraction means abstract classes." Abstract classes are one mechanism. Abstraction is the broader idea; a plain function is an abstraction too.

---

## 2.6 Friend functions and friend classes

### 1. What is it?

A `friend` declaration inside a class grants a specific non-member function, or another class, **full access to that class's private and protected members**.

### 2. Why does it exist?

Some operations are naturally about a class but can't, or shouldn't, be member functions. The canonical case is the stream output operator:

```cpp
class Point {
    int x, y;
public:
    Point(int x, int y) : x(x), y(y) {}
    friend ostream& operator<<(ostream& os, const Point& p);   // grant access
};

ostream& operator<<(ostream& os, const Point& p) {   // NOT a member
    return os << "(" << p.x << ", " << p.y << ")";    // but can read private x, y
}

cout << Point(1, 2);   // (1, 2)
```

**Why can't `operator<<` be a member of `Point`?** For a member operator, the *left* operand must be the class object. In `cout << p`, the left operand is `cout`, an `ostream`, and you can't add members to `ostream`. So it must be a free function, and since it needs `x` and `y`, it must be a friend (or use public getters).

Other legitimate uses:
- **Symmetric binary operators**, so that `2 * v` and `v * 2` both work. A member `operator*` only handles `v * 2`.
- **Tightly coupled class pairs**, such as a container and its iterator, or a `LinkedList` and its `Node`.
- **Unit tests** that need to inspect internals (debatable).

### 3. Friend class

```cpp
class Engine {
    int rpm = 0;
    friend class Car;          // every member function of Car can access Engine's privates
};
class Car {
    Engine e;
public:
    void rev() { e.rpm += 1000; }   // allowed
};
```

### 4. Properties (asked as a list)

| Property | Answer |
|---|---|
| Is a friend function a member? | **No.** It has no `this` and is called like a normal function |
| Where is the declaration placed? | Anywhere in the class; `public`/`private` sections make **no difference** to a friend declaration |
| Is friendship **inherited**? | **No.** A friend of `Base` has no special access to `Derived`'s new members, and a class derived from a friend is not a friend |
| Is friendship **transitive**? | **No.** A friend of my friend is not my friend |
| Is friendship **mutual**? | **No.** If `A` declares `B` a friend, `B` can access `A`, but `A` cannot access `B` |
| Who grants it? | Only the class itself. Nobody can make themselves a friend from outside |

**"Friendship is granted, not taken; and it is not inherited, transitive, or mutual."** That sentence covers the whole table.

### 5. Does `friend` break encapsulation?

This is the standard follow-up, and the strong answer is **"No, when used properly"**:

1. **The class grants it explicitly.** Nobody outside can make themselves a friend. The class still controls exactly who has access, so this is an access-control decision, not a breach.
2. **A friend is part of the class's interface**, just declared outside the class body. `operator<<` for `Point` is as much a part of `Point` as any member is.
3. The alternative is often **worse**: adding public getters for everything so that the free function can work exposes the data to *everyone*, not just to one function.

**But** heavy use of friends is a design smell. If many outside classes need private access, the class boundaries are probably in the wrong place.

### 6. Must remember

1. Friends are not members and have no `this`.
2. Not inherited, not transitive, not mutual.
3. The `public`/`private` placement of a friend declaration is irrelevant.
4. Canonical use: `operator<<` and symmetric operators.
5. A friend doesn't break encapsulation when used sparingly; it's controlled, explicit access granted by the class.

### 7. Java note

Java has no `friend`. The closest equivalent is package-private access (no modifier), which grants access to every class in the same package.

---

## 2.7 Stronger encapsulation: the Pimpl idiom (Tier 3, optional)

Private members are hidden from **code**, but not from **compilers**: they still appear in the header file. Changing a private member forces every file that includes the header to recompile, and the header reveals implementation details.

**Pimpl** ("pointer to implementation") moves all private data into a separate struct, defined only in the `.cpp` file:

```cpp
// widget.h
class Widget {
public:
    Widget();
    ~Widget();
    void draw();
private:
    struct Impl;                    // declared, never defined in the header
    std::unique_ptr<Impl> pImpl;    // the only private member
};

// widget.cpp
struct Widget::Impl { int width, height; std::string label; /* ... */ };
Widget::Widget() : pImpl(std::make_unique<Impl>()) {}
Widget::~Widget() = default;        // must be defined here, where Impl is complete
```

Benefits: true implementation hiding, faster builds, and a stable binary interface for libraries. Cost: one heap allocation and one indirection. Mention it only if the interviewer goes deep. It's an excellent "do you know more" answer to *"how would you make encapsulation stronger in C++?"*.

---

## 2.8 Consolidation

### Must remember (module)

1. **Encapsulation** = bundle data with its methods + restrict access, to protect invariants. Achieved with classes and `private`.
2. **Abstraction** = expose what, hide how, to manage complexity and decouple. Achieved with abstract classes and interfaces.
3. Encapsulation hides **data**; abstraction hides **complexity**. Inside view vs outside view. Implementation level vs design level.
4. They cooperate: encapsulation is often the means of delivering an abstraction.
5. Blind getters and setters are not real encapsulation. Expose behaviour, not data ("tell, don't ask").
6. Data hiding is the access-restriction mechanism; encapsulation is the whole principle.
7. Friend: not a member, no `this`; not inherited, transitive or mutual; granted only by the class.
8. A friend doesn't break encapsulation when used sparingly; `operator<<` is the canonical use.

### Common wrong answers (module)

- Defining abstraction and encapsulation with the same word ("hiding").
- "Abstraction is achieved with private members."
- "Getters and setters give encapsulation."
- "Friend functions are member functions."
- "Friendship is inherited."
- "Friend functions break encapsulation, so never use them."

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What is encapsulation? | Bundling data and methods in a class, with the data private, so it can only change through controlled methods. E.g. `Account::withdraw` guarding `balance` | Are getters/setters encapsulation? |
| What is abstraction? | Showing what an object does and hiding how. E.g. a `PaymentMethod::pay()` interface with UPI and card implementations | How do you achieve it in C++? (Abstract classes) |
| Abstraction vs encapsulation? | Hides complexity vs hides data; design vs implementation; outside view vs inside view; abstract classes vs access specifiers | Can one class show both? (Yes, with an example) |
| Data hiding vs encapsulation? | Data hiding is the access restriction; encapsulation is bundling plus data hiding | |
| What is a friend function? | A non-member function granted access to a class's private members by that class | Why is `operator<<` a friend? |
| Does friend break encapsulation? | No, when sparing: access is explicitly granted by the class and is part of its interface | Is friendship inherited? (No; not transitive or mutual either) |
| Benefits of encapsulation? | Invariants protected, internals changeable, validation in one place, bugs localised | |

### Practice

**P1.** Does this compile?
```cpp
class A { int secret = 42; friend void peek(A&); };
class B : public A { int mine = 7; };
void peek(A& a) { cout << a.secret; }
void peekB(B& b) { cout << b.mine; }
```
<details><summary>Answer</summary>

`peek` compiles: it's a friend of `A`. `peekB` **doesn't**: `B::mine` is private (class default) and `peekB` isn't a friend of anything. Even `peek` could not access `B::mine`, because friendship isn't inherited downward.
</details>

**P2.** Does this compile?
```cpp
class X { int a = 1; friend class Y; };
class Y { int b = 2; public: int readX(X& x) { return x.a; } };
class Z { public: int readY(Y& y) { return y.b; } };
```
<details><summary>Answer</summary>

`Y::readX` compiles, because `X` made `Y` a friend. `Z::readY` **doesn't**: `Y::b` is private and `Z` isn't `Y`'s friend. And `X` could not read `Y::b` either, because friendship isn't mutual.
</details>

**P3.** This class has private fields but weak encapsulation. Identify the problem and redesign it.
```cpp
class Order {
    vector<Item> items;
    double total;
    string status;      // "NEW", "PAID", "SHIPPED"
public:
    vector<Item>& getItems() { return items; }
    void setTotal(double t) { total = t; }
    void setStatus(string s) { status = s; }
};
```
<details><summary>Answer</summary>

Three leaks:
1. `getItems()` returns a **non-const reference**, so callers can modify the vector directly and `total` goes out of sync.
2. `setTotal` lets anyone set any total, so it can disagree with the items.
3. `setStatus` allows any string and any transition (for example "SHIPPED" before "PAID").

Redesign: expose behaviour, keep invariants inside.

```cpp
class Order {
    vector<Item> items;
    double total = 0;
    enum class Status { New, Paid, Shipped } status = Status::New;
public:
    void addItem(const Item& it) {
        if (status != Status::New) throw logic_error("order locked");
        items.push_back(it);
        total += it.price;                       // total can never drift
    }
    void markPaid()    { if (status != Status::New)  throw logic_error("bad transition"); status = Status::Paid; }
    void markShipped() { if (status != Status::Paid) throw logic_error("bad transition"); status = Status::Shipped; }
    const vector<Item>& getItems() const { return items; }   // read-only view
    double getTotal() const { return total; }
};
```
</details>

**P4.** In one sentence each, explain how a **coffee vending machine** shows abstraction and how it shows encapsulation.

<details><summary>Answer</summary>

**Abstraction:** you press "Cappuccino" and get coffee without knowing the brewing temperature, the grind or the milk-frothing steps. The interface exposes *what*, not *how*. **Encapsulation:** the coin box and the ingredient containers are locked inside, and you can only affect them through the buttons and the coin slot, which enforce the rules (enough money paid, stock available).
</details>

**P5.** Why is this `operator<<` a compile error, and what are two ways to fix it?
```cpp
class Temp { double c; public: Temp(double c):c(c){} };
ostream& operator<<(ostream& os, const Temp& t) { return os << t.c; }
```
<details><summary>Answer</summary>

`c` is private and `operator<<` is neither a member nor a friend. Fix 1: declare `friend ostream& operator<<(ostream&, const Temp&);` inside `Temp`. Fix 2: add a public `double celsius() const` getter and use it. Fix 2 is fine when the getter makes sense publicly anyway.
</details>

---

## Exit checklist

```
[ ] I can define encapsulation with the invariant idea and a BankAccount example
[ ] I can explain why blind getters/setters are weak encapsulation ("tell, don't ask")
[ ] I can define abstraction with a PaymentMethod-style interface example
[ ] I can deliver the abstraction vs encapsulation answer in ~40 s, with the table in my head
[ ] I can explain data hiding vs encapsulation in one line
[ ] I can explain why operator<< must be a non-member, and hence often a friend
[ ] I can state: friendship is granted, not inherited, not transitive, not mutual
[ ] I can argue why friend doesn't break encapsulation when used sparingly
[ ] P1–P5 done
```

---

## Next

**Part 5: M3 — Inheritance.** It covers the five types of inheritance, the public/protected/private inheritance access table, constructor chaining and destruction order across a hierarchy, what is and isn't inherited, the diamond problem and virtual inheritance (with the memory picture), object slicing, name hiding, and when to use inheritance at all (is-a vs has-a).
