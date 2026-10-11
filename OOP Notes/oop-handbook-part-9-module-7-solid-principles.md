# OOP Placement Handbook (C++) — Part 9
# Module 7: SOLID and Design Principles

**Module 7 · 2 hours · Tier 2 · Requires: M0–M5 (M6 helpful)**

---

## Why SOLID is asked, and how it's graded

"Explain SOLID" is a standard product-company question, and it is graded harshly on one point: **can you give an example of a violation and its fix for each letter?** Reciting the five names earns little. Reciting definitions earns a bit more. Showing a broken class and how to repair it earns the marks.

SOLID is also the **vocabulary of LLD rounds**. When an interviewer says "now add a new payment method", they want to see the Open/Closed Principle in action, and naming it shows you know what you're doing.

The organising principle:

> **All five principles are about one thing: making change cheap. Each one names a specific way that code becomes expensive to change (too many responsibilities, editing to extend, broken substitutability, fat interfaces, depending on details) and the structural fix for it.**

Every section uses the same format: **definition → why → broken code → fixed code → how to spot it → one-line interview answer.**

---

## 7.1 S — Single Responsibility Principle

### 1. Definition

> **A class should have only one reason to change.** (Robert C. Martin)

A more precise modern phrasing: *a class should be responsible to one **actor***, meaning one group of people (or one part of the system) who would ask for changes.

### 2. Why

When one class serves several masters, a change requested by one can break another's feature. Classes that do one thing are smaller, easier to test, and change for only one reason.

### 3. Broken

```cpp
class Invoice {
    vector<Item> items;
public:
    double total() const;                         // business rules  (finance team)
    string toHtml() const;                        // presentation     (UI team)
    void saveToDatabase(Database& db) const;      // persistence      (DB/infra team)
    void emailTo(const string& addr) const;       // delivery         (notifications team)
};
```

Four reasons to change: a tax-rule change, a redesign of the invoice layout, a schema migration, and an email-provider switch all edit the same class. A bug introduced while changing the HTML can break total calculation, and testing `total()` requires a database.

### 4. Fixed

```cpp
class Invoice {                          // only the business data and rules
    vector<Item> items;
public:
    double total() const;
    const vector<Item>& getItems() const;
};
class InvoiceRenderer   { public: string toHtml(const Invoice&) const; };
class InvoiceRepository { public: void save(const Invoice&); };
class InvoiceMailer     { public: void send(const Invoice&, const string& addr); };
```

Each class now has one reason to change, and each can be tested in isolation.

### 5. How to spot a violation

- The class name needs "and" to describe it ("InvoiceCalculatorAndPrinter"), or ends in `Manager`/`Util` and keeps growing.
- Methods fall into clusters that use different subsets of the fields.
- It imports database, UI and network headers all at once.

### 6. Common wrong answer

**"A class should do only one thing / have one method."** No. A class can have many methods that serve one responsibility. The test is *reasons to change*, not the number of methods.

### 7. Interview line

*"A class should have only one reason to change. For example, an `Invoice` that calculates totals, renders HTML and saves to a database changes whenever finance, UI or the DB schema changes, so I'd split rendering and persistence into separate classes."*

---

## 7.2 O — Open/Closed Principle

### 1. Definition

> **Software entities should be open for extension but closed for modification.** (Bertrand Meyer)

You should be able to add new behaviour by **adding new code**, not by **editing existing, tested code**.

### 2. Why

Every edit to working code risks breaking it, and forces it to be retested and redeployed. A `switch` on a type that's copied across many functions has to be edited in every copy for every new type.

### 3. Broken

```cpp
enum class PaymentType { Card, Upi };

class PaymentProcessor {
public:
    void process(PaymentType type, double amount) {
        if (type == PaymentType::Card)      { /* card logic */ }
        else if (type == PaymentType::Upi)  { /* UPI logic */ }
        // Adding Wallet: edit the enum, edit this function, and every other
        // switch on PaymentType elsewhere (refund(), fee(), validate()...)
    }
};
```

### 4. Fixed: polymorphism

```cpp
class PaymentMethod {
public:
    virtual void pay(double amount) = 0;
    virtual ~PaymentMethod() = default;
};
class CardPayment : public PaymentMethod { public: void pay(double a) override { /* ... */ } };
class UpiPayment  : public PaymentMethod { public: void pay(double a) override { /* ... */ } };

class PaymentProcessor {                      // CLOSED: never changes again
public:
    void process(PaymentMethod& m, double amount) { m.pay(amount); }
};

class WalletPayment : public PaymentMethod {  // OPEN: extension = a new class
public: void pay(double a) override { /* ... */ }
};
```

### 5. How to spot a violation

- `if/else` or `switch` chains on a **type code** or `dynamic_cast` (M6 §6.6).
- The same type-switch appears in several functions.
- Adding a variant means touching many files.

### 6. Nuances (they show depth)

- OCP doesn't mean "never edit code". Bug fixes are edits. It means **adding a variant shouldn't require modifying working code**.
- You can't be closed against *every* change. Choose the axes where change is **likely** (payment methods, notification channels, pricing rules) and put an abstraction there. Abstracting everything is over-engineering (YAGNI, §7.7).
- Somewhere, something still has to choose which concrete class to create. That's usually a **Factory** (M8), which is the one place that knows all the types.

### 7. Interview line

*"Open for extension, closed for modification. Instead of a `switch` on payment type that I'd edit for every new method, I define a `PaymentMethod` interface; adding a wallet means adding a class, and the processor code never changes."*

---

## 7.3 L — Liskov Substitution Principle

### 1. Definition

> **Objects of a derived class must be usable wherever objects of the base class are expected, without breaking the program's correctness.** (Barbara Liskov, 1987)

If code works with a `Base&`, it must keep working when handed any `Derived`, with no surprises.

### 2. Why

Polymorphism relies on it. The whole point of `process(PaymentMethod&)` is that the caller doesn't check what it got. A subclass that behaves differently in ways the base didn't allow forces callers back to type checks, which then violates OCP.

### 3. Broken (1): Rectangle and Square

```cpp
class Rectangle {
protected:
    int w = 0, h = 0;
public:
    virtual void setWidth(int x)  { w = x; }
    virtual void setHeight(int y) { h = y; }
    int area() const { return w * h; }
    virtual ~Rectangle() = default;
};
class Square : public Rectangle {              // "a square IS a rectangle"... mathematically
public:
    void setWidth(int x)  override { w = h = x; }
    void setHeight(int y) override { w = h = y; }
};

void resize(Rectangle& r) {
    r.setWidth(5);
    r.setHeight(4);
    assert(r.area() == 20);                    // FAILS for a Square: area is 16
}
```

`Rectangle` promises that width and height are **independent**. `Square` breaks that promise, so code that's correct for every `Rectangle` is wrong for a `Square`.

**Fix:** don't make `Square` a subtype of a *mutable* `Rectangle`. Options: make both siblings under a `Shape` interface with `area()`, or make shapes immutable (a `Square` constructed with a side never violates rectangle behaviour, because there's no `setWidth`).

### 4. Broken (2): Bird and Penguin

```cpp
class Bird    { public: virtual void fly() { /* ... */ } virtual ~Bird() = default; };
class Penguin : public Bird { public: void fly() override { throw logic_error("can't fly"); } };

void migrate(vector<Bird*>& flock) { for (Bird* b : flock) b->fly(); }   // crashes on a penguin
```

**Fixed: model the real capabilities.**

```cpp
class Bird       { public: virtual void eat(); virtual ~Bird() = default; };
class FlyingBird : public Bird { public: virtual void fly() = 0; };
class Sparrow    : public FlyingBird { public: void fly() override; };
class Penguin    : public Bird { public: void swim(); };

void migrate(vector<FlyingBird*>& flock);      // penguins can't even be passed in
```

### 5. The formal rules (for a strong answer)

A subclass must not:

| Rule | Meaning | Violation example |
|---|---|---|
| **Strengthen preconditions** | Can't demand more from callers than the base did | Base accepts any amount; the override rejects amounts over ₹10,000 |
| **Weaken postconditions** | Can't deliver less than the base promised | Base `sort()` guarantees sorted output; the override sorts only the first half |
| **Break invariants** | Must keep everything the base keeps true | Square ties width to height |
| **Throw new kinds of exceptions** | Callers aren't prepared for them | `Penguin::fly()` throws |

### 6. How to spot a violation

- Overrides that **throw "not supported"** or do **nothing**.
- Callers doing `if (dynamic_cast<Penguin*>(b))` before calling a method.
- A subclass's documentation says "unlike the base, this one...".

### 7. Interview line

*"Subtypes must be substitutable for their base types without breaking correctness. Square extending a mutable Rectangle is the classic violation: setting width and height independently is a rectangle guarantee that a square can't keep. A sign of violation is an override that throws 'not supported'; the fix is usually to restructure the hierarchy around real capabilities."*

---

## 7.4 I — Interface Segregation Principle

### 1. Definition

> **Clients should not be forced to depend on methods they do not use.**

Prefer several small, focused interfaces over one large, general one.

### 2. Why

A fat interface forces implementers to write dummy methods (often LSP violations: empty bodies or throws), and it couples every client to every method. A change to a method one client never calls still forces that client to recompile and retest.

### 3. Broken

```cpp
class Machine {                                   // fat interface
public:
    virtual void print(const Doc&) = 0;
    virtual void scan(Doc&) = 0;
    virtual void fax(const Doc&) = 0;
    virtual ~Machine() = default;
};
class BasicPrinter : public Machine {
public:
    void print(const Doc&) override { /* real */ }
    void scan(Doc&) override       { throw logic_error("not supported"); }   // forced
    void fax(const Doc&) override  { throw logic_error("not supported"); }   // forced
};
```

### 4. Fixed

```cpp
class Printer { public: virtual void print(const Doc&) = 0; virtual ~Printer() = default; };
class Scanner { public: virtual void scan(Doc&) = 0;        virtual ~Scanner() = default; };
class Fax     { public: virtual void fax(const Doc&) = 0;   virtual ~Fax() = default; };

class BasicPrinter : public Printer { public: void print(const Doc&) override; };
class OfficeAllInOne : public Printer, public Scanner, public Fax {   // multiple INTERFACE inheritance: safe (M4 §4.11)
public:
    void print(const Doc&) override; void scan(Doc&) override; void fax(const Doc&) override;
};

void printReport(Printer& p);                  // depends ONLY on what it uses
```

### 5. How to spot a violation

- Implementations with empty or throwing methods.
- Interfaces named `IEverything` or `XxxManager` with 15 methods.
- Clients that call only 2 of an interface's 12 methods.

### 6. ISP vs SRP

| | SRP | ISP |
|---|---|---|
| About | Classes (implementations) | Interfaces (contracts) |
| Viewpoint | The class's reasons to change | The **client's** needs |
| Fix | Split the class | Split the interface |

### 7. Interview line

*"No client should be forced to depend on methods it doesn't use. A `Machine` interface with print, scan and fax forces a basic printer to stub out scan and fax; splitting it into `Printer`, `Scanner` and `Fax` lets each class implement only what it supports."*

---

## 7.5 D — Dependency Inversion Principle

### 1. Definition

> **High-level modules should not depend on low-level modules; both should depend on abstractions. Abstractions should not depend on details; details should depend on abstractions.**

- **High-level module:** business logic, the *policy* (`OrderService`).
- **Low-level module:** the *mechanism* (`MySqlDatabase`, `SmtpEmailSender`).

### 2. Why

If business logic directly creates and calls a concrete database or email class, you can't swap providers, can't unit-test without a real database, and changes to infrastructure ripple into business code.

### 3. Broken

```cpp
class SmtpEmailSender { public: void send(const string& to, const string& body); };

class OrderService {
    SmtpEmailSender mailer;               // depends on a CONCRETE low-level class
public:
    void placeOrder(const Order& o) {
        // ... business logic ...
        mailer.send(o.email, "Order placed");
    }
};
// Switch to SMS? Edit OrderService. Unit-test placeOrder? Sends real emails.
```

```
   OrderService  ------------->  SmtpEmailSender        high-level depends on low-level
```

### 4. Fixed

```cpp
class MessageSender {                                     // abstraction (owned by the high level)
public:
    virtual void send(const string& to, const string& body) = 0;
    virtual ~MessageSender() = default;
};

class OrderService {
    MessageSender& sender;                                // depends on the abstraction
public:
    explicit OrderService(MessageSender& s) : sender(s) {}   // INJECTED
    void placeOrder(const Order& o) { /* ... */ sender.send(o.email, "Order placed"); }
};

class SmtpEmailSender : public MessageSender { public: void send(const string&, const string&) override; };
class SmsSender       : public MessageSender { public: void send(const string&, const string&) override; };
class FakeSender      : public MessageSender {            // for unit tests
public:
    vector<string> sent;
    void send(const string& to, const string&) override { sent.push_back(to); }
};
```

```
   OrderService  ------->  <<interface>> MessageSender  <------- SmtpEmailSender
                                                         <------- SmsSender
              both now point at the abstraction: the dependency arrow is "inverted"
```

The arrow from the low-level class used to point *away* from the abstraction; now it points *toward* it. That's the "inversion".

### 5. DIP vs Dependency Injection vs IoC (a frequent follow-up)

| Term | What it is |
|---|---|
| **Dependency Inversion Principle** | The design **principle**: depend on abstractions, not concretions |
| **Dependency Injection** | A **technique** for achieving it: pass dependencies in (constructor, setter or parameter) instead of creating them inside |
| **Inversion of Control** | The broader idea that a framework or container, not your class, controls object creation and wiring. DI containers (Spring in Java) are one form |

**"DI is how you usually achieve DIP."** Constructor injection, as above, is the preferred form, because the dependency is mandatory and visible.

### 6. How to spot a violation

- `new ConcreteThing()` or concrete-type members inside business logic.
- Business-logic headers that include database, HTTP or SDK headers.
- A unit test that needs a network or database.

### 7. Interview line

*"High-level business logic and low-level details should both depend on abstractions. Instead of `OrderService` creating an `SmtpEmailSender`, it takes a `MessageSender` interface through its constructor, so I can swap in SMS or a fake for tests without touching the service. Dependency injection is the technique; inversion is the principle."*

---

## 7.6 SOLID at a glance

| Letter | Principle | Problem it prevents | Typical fix | Related pattern |
|---|---|---|---|---|
| **S** | Single Responsibility | God classes; unrelated changes collide | Split by reason to change | — |
| **O** | Open/Closed | Editing tested code for each new variant | Abstraction + polymorphism | Strategy, Factory, Decorator |
| **L** | Liskov Substitution | Subclasses that break callers | Model real capabilities; don't inherit for reuse | — |
| **I** | Interface Segregation | Fat interfaces, stub methods | Split interfaces per client need | Adapter |
| **D** | Dependency Inversion | Business logic tied to infrastructure | Depend on interfaces; inject them | Strategy, Factory, DI |

**How they connect:** OCP is the *goal* (extend without editing). LSP makes polymorphism *safe* enough to rely on. DIP and ISP shape the *interfaces* that make OCP possible. SRP keeps each piece small enough to change on its own.

### The 60-second SOLID answer

*"SOLID is five principles for code that's cheap to change. Single responsibility: one reason to change; I'd split an Invoice that calculates, renders and saves. Open/closed: extend without modifying; add a payment method as a new class instead of editing a switch. Liskov: subtypes must be substitutable; Square extending a mutable Rectangle breaks it. Interface segregation: don't force clients to depend on methods they don't use; split a Machine interface into Printer and Scanner. Dependency inversion: business logic depends on abstractions, injected through the constructor, so a MessageSender interface instead of a concrete SMTP class."*

---

## 7.7 Other design principles (short answers)

| Principle | Meaning | Interview line |
|---|---|---|
| **DRY** (Don't Repeat Yourself) | Every piece of *knowledge* has one authoritative place | "If the GST rate is hard-coded in five places, changing it means five edits and one forgotten bug." Note: DRY is about knowledge, not textual similarity; two identical-looking functions that change for different reasons should stay separate |
| **KISS** (Keep It Simple) | Prefer the simplest design that works | "Don't add a plugin system for two payment methods" |
| **YAGNI** (You Aren't Gonna Need It) | Don't build for hypothetical future requirements | "Add the abstraction when the second variant arrives, not the first." This balances OCP |
| **Law of Demeter** ("talk only to friends") | A method should call methods only on itself, its parameters, its members and objects it creates, not on objects returned by those | `order.getCustomer().getAddress().getCity()` couples you to three classes' structure; prefer `order.shippingCity()` |
| **Composition over inheritance** | Has-a for flexibility, is-a only for true substitutability | M5 §5.7 |
| **High cohesion, low coupling** | Things inside a class belong together; classes depend on each other minimally | The goal SOLID serves |
| **Separation of concerns** | Distinct concerns (UI, logic, storage) live in distinct modules | SRP at the architecture level |
| **Program to an interface, not an implementation** | Declare variables and parameters with abstract types | `PaymentMethod&`, not `UpiPayment&` |

**Tension worth mentioning:** OCP pushes toward abstraction, and YAGNI and KISS push against premature abstraction. A good answer: *"I introduce an interface where change is likely or already happening, not everywhere."*

---

## 7.8 SOLID in LLD rounds

How to use it out loud, without lecturing:

| When the interviewer says... | Say/do |
|---|---|
| "Add a new vehicle type / payment method / notification channel" | "Since `X` is an interface, that's a new class and no existing code changes. That's open/closed." |
| "How would you test this?" | "The service takes its dependencies through the constructor, so I'd inject fakes. That's dependency inversion." |
| "This class is getting big" | "Let me pull pricing out into a `PricingStrategy`. It changes for different reasons than spot allocation." |
| "Why not make `ElectricCar` override `refuel()` to throw?" | "That would break Liskov; callers of `refuel()` don't expect it to throw. I'd separate `Refuelable` and `Chargeable` interfaces." |

**Don't** recite all five unprompted in the middle of a design. Apply them, and name them in one phrase when you do.

---

## 7.9 Consolidation

### Must remember (module)

1. **S**: one reason to change (one actor). Not "one method".
2. **O**: extend by adding code; switch on type → polymorphism. Abstract only where change is likely.
3. **L**: subtypes must be substitutable. Square/Rectangle, Penguin/Bird. Don't strengthen preconditions, weaken postconditions or throw new exceptions.
4. **I**: no client depends on methods it doesn't use; split fat interfaces.
5. **D**: depend on abstractions; inject dependencies. DIP = principle, DI = technique, IoC = broader idea.
6. Signs: god classes (S), type switches (O), "not supported" overrides (L, I), `new Concrete` in business logic (D).
7. DRY is about knowledge, not identical text. YAGNI balances OCP. Law of Demeter: no long call chains.

### Common wrong answers (module)

- "SRP means a class has one method."
- "OCP means you can never modify a class."
- "LSP means the derived class has the same methods as the base." Same *behaviour contract*, not just the same signatures.
- "ISP and SRP are the same thing."
- "DIP and dependency injection are the same thing."
- Listing the five names without a single example.

### Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| Explain SOLID | The five principles, with one violation + fix each (§7.6) | Which do you find most useful? |
| SRP example? | Invoice split into calculator / renderer / repository | How do you decide what a "responsibility" is? (Reason to change / actor) |
| OCP example? | Payment type switch → `PaymentMethod` interface | Doesn't something still need a switch? (Yes, a factory, in one place) |
| LSP violation? | Square–Rectangle or Penguin–Bird | How to fix it? |
| ISP example? | Machine → Printer / Scanner / Fax | ISP vs SRP? |
| DIP vs DI? | Principle vs technique | Types of injection? (Constructor, setter, parameter) |
| DRY vs WET? | One source of truth for each piece of knowledge | When is duplication OK? |
| Law of Demeter? | Don't chain through objects returned by other calls | Example |

### Practice: identify the violated principle and fix it

**P1.**
```cpp
class Report {
public:
    string generate(const Data& d);
    void saveAsPdf(const string& path);
    void uploadToS3(const string& bucket);
};
```
<details><summary>Answer</summary>

**SRP**: content generation, PDF formatting and cloud storage are three reasons to change. Split into `ReportGenerator`, `PdfExporter` and `ReportStorage` (and make storage an interface for **DIP**).
</details>

**P2.**
```cpp
double shippingCost(const Order& o) {
    if (o.carrier == "BlueDart") return o.weight * 50;
    if (o.carrier == "Delhivery") return 40 + o.weight * 30;
    if (o.carrier == "IndiaPost") return o.weight * 20;
    return 0;
}
```
<details><summary>Answer</summary>

**OCP**: each new carrier edits this function. Use a `ShippingCarrier` interface with `cost(const Order&)`, one class per carrier, and a factory or registry to look up the carrier by name.
</details>

**P3.**
```cpp
class ReadOnlyFile : public File {
public:
    void write(const string&) override { throw runtime_error("read-only"); }
};
```
<details><summary>Answer</summary>

**LSP** (and **ISP**): code expecting a `File` can write to it; this subclass breaks that. Split into `ReadableFile` and `WritableFile` interfaces, with a read-only file implementing only `ReadableFile`.
</details>

**P4.**
```cpp
class UserService {
    MySqlUserRepository repo;          // concrete
    BcryptHasher hasher;               // concrete
public:
    void registerUser(const string& email, const string& pwd);
};
```
<details><summary>Answer</summary>

**DIP**: business logic depends on concrete infrastructure, so you can't test it without MySQL or swap the hashing algorithm. Introduce `UserRepository` and `PasswordHasher` interfaces and inject them through the constructor.
</details>

**P5.**
```cpp
class Worker { public: virtual void work() = 0; virtual void eat() = 0; virtual void sleep() = 0; };
class RobotWorker : public Worker { void eat() override {} void sleep() override {} void work() override; };
```
<details><summary>Answer</summary>

**ISP**: robots are forced to implement `eat`/`sleep` as empty stubs (also an LSP smell). Split into `Workable` and `LivingBeing` (or `Eater` and `Sleeper`). `HumanWorker` implements both; `RobotWorker` implements only `Workable`.
</details>

**P6.** `cout << order.getCustomer().getWallet().getBalance();`: which principle does this break, and what's the fix?

<details><summary>Answer</summary>

**Law of Demeter**: the caller depends on the structure of `Order`, `Customer` and `Wallet`. Add `order.customerBalance()`, or better, ask for what you actually want (`order.canBePaidFromWallet()`).
</details>

---

## Exit checklist

```
[ ] For each SOLID letter I can give: definition, a broken example, the fix, the warning signs
[ ] I can deliver the 60-second SOLID answer
[ ] I avoid "SRP = one method" and "OCP = never modify"
[ ] I can explain Square/Rectangle and Penguin/Bird and the formal LSP rules
[ ] I can distinguish ISP from SRP and DIP from DI from IoC
[ ] I can explain DRY, KISS, YAGNI and the Law of Demeter in one line each
[ ] I know how to name SOLID principles briefly during an LLD round
[ ] P1–P6 done
```

---

## Next

**Part 10: M8 — Design Patterns.** Tier 2: Singleton (with thread safety), Factory and Factory Method, Strategy, Observer. Tier 3: Builder, Decorator, Adapter, State. Each comes with the problem, a UML sketch, compilable C++, real-world uses and when *not* to use it, plus a recognition table that maps requirement phrases to patterns.
