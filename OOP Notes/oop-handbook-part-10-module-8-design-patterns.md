# OOP Placement Handbook (C++) — Part 10
# Module 8: Design Patterns

**Module 8 · 3–4 hours · Tier 2 (Singleton, Factory, Strategy, Observer) / Tier 3 (Builder, Decorator, Adapter, State) · Requires: M4, M5, M7**

---

## How to study patterns for interviews

The Gang of Four book catalogues 23 patterns. Freshers and SDE-1 candidates are asked about **four**, plus the vocabulary of a few more:

| Tier | Patterns | How they're asked |
|---|---|---|
| **2 (learn to code)** | **Singleton, Factory, Strategy, Observer** | "Implement a thread-safe Singleton." "When would you use Strategy?" "Explain Observer with an example." |
| **3 (learn to explain)** | Builder, Decorator, Adapter, State | "Which pattern would you use here?" in LLD rounds |
| Skip | The remaining ~15 | Rarely asked of freshers |

For each pattern you need four things: **the problem it solves, its structure, a short C++ implementation, and when *not* to use it.** The last one separates people who understand patterns from people who've memorised them.

The organising principle:

> **A design pattern is a named, reusable solution to a recurring design problem. Nearly every pattern is SOLID applied to a specific situation: isolate what varies behind an interface, and compose objects instead of hard-coding behaviour. Learn the problem first; the structure follows.**

### The three categories

| Category | Concerned with | Patterns in this module |
|---|---|---|
| **Creational** | *How objects are created* | Singleton, Factory (Simple, Method, Abstract), Builder |
| **Structural** | *How objects are composed* | Adapter, Decorator |
| **Behavioural** | *How objects interact and divide responsibility* | Strategy, Observer, State (+ Template Method recap) |

All code in this module compiles under C++17 and was run to confirm the outputs shown.

---

# PART A — Tier 2 patterns

## 8.1 Singleton

### 1. What is it?

Ensure a class has **exactly one instance**, and provide a **global access point** to it.

### 2. Why does it exist?

Some resources should exist once per process: a logger, a configuration registry, a connection pool, a hardware device driver. Two loggers writing to the same file would interleave output; two config objects could disagree.

### 3. The three ingredients

1. **Private constructor**: nobody outside can create instances.
2. **Deleted copy constructor and copy assignment**: nobody can duplicate the instance.
3. **A static access function** that returns the single instance.

### 4. The right implementation in modern C++: the Meyers Singleton

```cpp
class Logger {
public:
    static Logger& instance() {
        static Logger inst;               // created on first call; thread-safe since C++11
        return inst;
    }
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    void log(const string& m) {
        lock_guard<mutex> g(mtx);         // the INSTANCE's methods still need their own locking
        cout << "[log] " << m << "\n";
    }
private:
    Logger() { cout << "Logger created\n"; }
    mutex mtx;
};

int main() {
    cout << "start\n";
    Logger::instance().log("a");          // "Logger created" prints here: lazy
    Logger::instance().log("b");
    cout << (&Logger::instance() == &Logger::instance());   // 1: same object
}
```

**Output:** `start` / `Logger created` / `[log] a` / `[log] b` / `1`

**Why it's thread-safe:** C++11 guarantees that a function-local `static` is initialised **exactly once**, even if several threads call `instance()` at the same moment. Other threads block until initialisation finishes (M0 §0.6). It is also **lazy** (created on first use) and **destroyed automatically** at program exit.

### 5. Why the naive version is broken

```cpp
class Bad {
    static Bad* inst;
    Bad() {}
public:
    static Bad* get() {
        if (inst == nullptr)          // two threads can both see nullptr here...
            inst = new Bad();         // ...and both create an instance: a race
        return inst;                  // also: never deleted
    }
};
```

Older fixes: lock a mutex on every call (correct but slow), or **double-checked locking** (check, lock, check again). In C++, double-checked locking is correct only with `std::atomic` or `std::call_once`, and the plain-pointer version is a data race. The Meyers Singleton makes all of this unnecessary. Mention double-checked locking by name if asked about the history, then say "in C++11 and later I'd use a function-local static".

### 6. Two subtleties

- **The singleton's *creation* is thread-safe; its *methods* are not** automatically. `log()` still needs its own mutex.
- **Destruction order:** if one singleton's destructor uses another singleton that was already destroyed (statics die in reverse construction order), you get undefined behaviour. This is rare, but it's the reason some codebases deliberately leak singletons.

### 7. When NOT to use it (the criticism interviewers want)

| Problem | Why |
|---|---|
| **It's global state** | Any code can reach it and change it; hidden dependencies |
| **Hard to unit-test** | You can't substitute a fake; state leaks between tests |
| **Violates SRP** | The class manages its own lifetime *and* does its job |
| **Hides dependencies** | A function's signature doesn't reveal that it uses the logger |
| **Concurrency bottleneck** | One shared instance means contention |

**Better alternative:** create one instance at startup and **inject** it (DIP, M7 §7.5). "One instance" is a decision for the application, not a property the class has to enforce. Use a true Singleton for things that really are process-wide (logging, hardware access) and prefer injection everywhere else.

### 8. Interview questions

- *"Implement a thread-safe Singleton in C++."* The Meyers Singleton above: private constructor, deleted copies, function-local static. *Follow-up: "Why is it thread-safe?"* C++11 guarantees one-time initialisation of local statics. *Follow-up: "Problems with Singletons?"* Global state, testability, hidden dependencies; prefer dependency injection.
- *"Singleton vs a class with all static members?"* A singleton is an **object**: it can implement interfaces, be passed by reference, be lazily initialised, and in principle be replaced. A static-only class can do none of these.

---

## 8.2 Factory (Simple Factory, Factory Method, Abstract Factory)

### 1. What is it?

**Encapsulate object creation.** Client code asks for an object by *what it needs*, and the factory decides *which concrete class* to instantiate.

### 2. Why does it exist?

OCP (M7 §7.2) moves type switches out of business logic, but *something* still has to say `new UpiPayment` or `new CardPayment`. The factory is that one place. Without it, `new ConcreteType` calls scattered through the code couple everything to the concrete classes.

### 3. Simple Factory (the one you'll write most)

A single function or class that creates the right subclass from a parameter.

```cpp
struct Notification { virtual void send(const string& msg) = 0; virtual ~Notification() = default; };
struct EmailNotification : Notification { void send(const string& m) override { cout << "Email: " << m << "\n"; } };
struct SmsNotification   : Notification { void send(const string& m) override { cout << "SMS: " << m << "\n"; } };
struct PushNotification  : Notification { void send(const string& m) override { cout << "Push: " << m << "\n"; } };

class NotificationFactory {
public:
    static unique_ptr<Notification> create(const string& channel) {
        if (channel == "email") return make_unique<EmailNotification>();
        if (channel == "sms")   return make_unique<SmsNotification>();
        if (channel == "push")  return make_unique<PushNotification>();
        throw invalid_argument("unknown channel: " + channel);
    }
};

NotificationFactory::create("sms")->send("OTP 1234");     // SMS: OTP 1234
```

The client depends only on `Notification`. Adding WhatsApp means one new class plus **one line in the factory**: the change is confined to the single place whose job is to know every type. (Strictly, the Simple Factory is an idiom, not one of the GoF 23, but it's what interviewers usually mean by "factory pattern".)

The return type is **`unique_ptr<Base>`**: the factory hands ownership to the caller (M6 §6.5).

### 4. Factory Method (GoF)

A base class defines an algorithm that needs an object, and **leaves the choice of object to a virtual method that subclasses override**.

```cpp
struct Transport { virtual string deliver() const = 0; virtual ~Transport() = default; };
struct Truck : Transport { string deliver() const override { return "by road"; } };
struct Ship  : Transport { string deliver() const override { return "by sea"; } };

class Logistics {
public:
    void planDelivery() const {
        auto t = createTransport();                       // which one? the subclass decides
        cout << "Delivering " << t->deliver() << "\n";
    }
    virtual ~Logistics() = default;
protected:
    virtual unique_ptr<Transport> createTransport() const = 0;   // THE factory method
};
struct RoadLogistics : Logistics { unique_ptr<Transport> createTransport() const override { return make_unique<Truck>(); } };
struct SeaLogistics  : Logistics { unique_ptr<Transport> createTransport() const override { return make_unique<Ship>(); } };

RoadLogistics().planDelivery();    // Delivering by road
SeaLogistics().planDelivery();     // Delivering by sea
```

### 5. Abstract Factory (explain only)

A factory interface that creates **families of related objects** that must be used together.

```
   <<interface>> UIFactory                 WindowsFactory          MacFactory
   + createButton()   : Button     ->      WinButton               MacButton
   + createCheckbox() : Checkbox   ->      WinCheckbox             MacCheckbox
```

The client gets one factory and is guaranteed a consistent family: no Mac button next to a Windows checkbox.

### 6. Comparison

| | Simple Factory | Factory Method | Abstract Factory |
|---|---|---|---|
| Mechanism | One function with a conditional | A virtual method overridden in subclasses | An interface with several creation methods |
| Creates | One product, chosen by a parameter | One product, chosen by the subclass | A **family** of related products |
| Extension | Edit the factory (one place) | Add a subclass | Add a whole new factory class |
| Typical use | Most LLD code | Frameworks with extension points | Themes, cross-platform UI, database drivers |

### 7. When NOT to use it

When there's only one concrete type and no realistic prospect of more. `make_unique<Thing>()` is fine (YAGNI).

### 8. Interview line

*"A factory encapsulates object creation so clients depend on an interface, not concrete classes. A Simple Factory picks the subclass from a parameter, in one place. Factory Method lets subclasses decide by overriding a creation method. Abstract Factory creates families of related objects."*

---

## 8.3 Strategy

### 1. What is it?

Define a **family of interchangeable algorithms**, put each behind a common interface, and let the client **choose or swap one at runtime**.

### 2. Why does it exist?

When one operation has several variants (pricing rules, sorting orders, route calculation, payment flows, compression formats), the alternatives are a growing `if/else` (an OCP violation) or a subclass per variant of the *whole* class (class explosion, M5 §5.7). Strategy extracts just the varying algorithm.

### 3. Structure

```
   Checkout  <#>------->  <<interface>> PricingStrategy
   (context)              + price(base) : double
                                 ^           ^            ^
                                 |           |            |
                         RegularPricing  SalePricing  SurgePricing
```

### 4. Code

```cpp
struct PricingStrategy { virtual double price(double base) const = 0; virtual ~PricingStrategy() = default; };

struct RegularPricing : PricingStrategy { double price(double b) const override { return b; } };
struct SalePricing : PricingStrategy {
    double pct; explicit SalePricing(double p) : pct(p) {}
    double price(double b) const override { return b * (1 - pct / 100); }
};
struct SurgePricing : PricingStrategy {
    double mult; explicit SurgePricing(double m) : mult(m) {}
    double price(double b) const override { return b * mult; }
};

class Checkout {                                          // the context
    unique_ptr<PricingStrategy> strategy;
public:
    explicit Checkout(unique_ptr<PricingStrategy> s) : strategy(std::move(s)) {}
    void setStrategy(unique_ptr<PricingStrategy> s) { strategy = std::move(s); }   // swap at runtime
    double total(double base) const { return strategy->price(base); }
};

Checkout c(make_unique<RegularPricing>());
c.total(1000);                                   // 1000
c.setStrategy(make_unique<SalePricing>(20));     c.total(1000);   // 800
c.setStrategy(make_unique<SurgePricing>(1.5));   c.total(1000);   // 1500
```

### 5. Real-world uses

`std::sort`'s comparator (a strategy passed as a function object), payment methods, route planners (fastest / shortest / avoid tolls), parking-spot allocation (M9a), cache eviction policies (LRU / LFU, M9a), compression algorithms.

**Lightweight variant in C++:** when a strategy is a single function, `std::function<double(double)>` or a lambda is often simpler than an interface plus classes. Mention it; it shows judgement.

### 6. When NOT to use it

When there are only two variants that will never grow. A simple `if` is clearer (KISS).

### 7. Interview line

*"Strategy encapsulates interchangeable algorithms behind an interface so the client can pick or swap them at runtime without conditionals. For example, a checkout with regular, sale and surge pricing strategies. It's open/closed in practice, and it's composition over inheritance."*

---

## 8.4 Observer

### 1. What is it?

A **one-to-many** dependency: when one object (the **subject**) changes state, all its registered dependents (the **observers**) are notified automatically. Also called **publish–subscribe**, or listeners/callbacks.

### 2. Why does it exist?

Without it, the subject must know and call every interested party directly (`app.update(); alert.check(); logger.record();`), so it's coupled to all of them and has to be edited for each new one. With Observer, the subject knows only an `Observer` interface, and parties subscribe and unsubscribe themselves.

### 3. Structure

```
   StockTicker (subject)              <<interface>> Observer
   - observers : list<Observer*> ---> + update(stock, price)
   + subscribe(o)                          ^            ^
   + unsubscribe(o)                        |            |
   + setPrice(s, p) -> notify all     MobileApp     PriceAlert
```

### 4. Code

```cpp
struct Observer { virtual void update(const string& stock, double price) = 0; virtual ~Observer() = default; };

class StockTicker {
    vector<Observer*> observers;                 // non-owning (association, M5)
public:
    void subscribe(Observer* o)   { observers.push_back(o); }
    void unsubscribe(Observer* o) { observers.erase(remove(observers.begin(), observers.end(), o), observers.end()); }
    void setPrice(const string& s, double p) { for (Observer* o : observers) o->update(s, p); }
};

struct MobileApp : Observer {
    void update(const string& s, double p) override { cout << "App: " << s << " = " << p << "\n"; }
};
struct PriceAlert : Observer {
    double threshold; explicit PriceAlert(double t) : threshold(t) {}
    void update(const string& s, double p) override {
        if (p > threshold) cout << "ALERT: " << s << " above " << threshold << "\n";
    }
};

StockTicker t; MobileApp app; PriceAlert alert(500);
t.subscribe(&app); t.subscribe(&alert);
t.setPrice("INFY", 480);      // App: INFY = 480
t.setPrice("INFY", 520);      // App: INFY = 520   /   ALERT: INFY above 500
t.unsubscribe(&app);
t.setPrice("INFY", 530);      // ALERT: INFY above 500
```

### 5. Pitfalls (what makes an answer strong)

| Pitfall | Fix |
|---|---|
| **Dangling observers**: an observer is destroyed without unsubscribing, and the subject calls through a dead pointer | Unsubscribe in the observer's destructor (RAII), or store `weak_ptr<Observer>` and skip expired ones (M6 §6.4) |
| **Modifying the list during notification**: an observer unsubscribes inside `update()`, invalidating the loop's iterators | Iterate over a copy, or defer removals until after the loop |
| **Thread safety**: subscribe and notify from different threads | Guard the list with a mutex, and don't hold it while calling observers (deadlock risk), so copy the list under the lock first |
| **Push vs pull**: send the data in `update()` (push) or just "something changed" and let observers query (pull) | Push is simpler; pull suits large or varied state |
| **Cascades and ordering**: observers triggering other notifications | Keep `update()` cheap; don't depend on notification order |

### 6. Real-world uses

GUI event listeners (button clicks), stock or score feeds, notification systems, the MVC model → view update, event buses, reactive programming (RxJS), and a "notify me when back in stock" feature (a common LLD extension).

### 7. Interview line

*"Observer defines a one-to-many relationship: subjects keep a list of observers behind an interface and notify them on change, so the subject never depends on concrete listeners. The classic pitfalls are dangling observers, which you fix by unsubscribing in the destructor or using weak_ptr, and modifying the list during notification."*

---

# PART B — Tier 3 patterns (explain and sketch)

## 8.5 Builder

### Problem

Constructing an object with **many optional parameters** leads to "telescoping constructors" (`Request(url)`, `Request(url, method)`, `Request(url, method, headers, body, timeout, retries...)`) or call sites full of unreadable positional arguments: `Request("u", "POST", {}, "", 2000, 3, true)`.

### Solution

A separate builder object with **named, chainable setters**, and a final `build()` that validates and returns the finished object.

```cpp
class HttpRequest {
public:
    class Builder;
    void print() const { cout << method << " " << url << " headers=" << headers.size() << " timeout=" << timeoutMs << "\n"; }
private:
    string method = "GET", url, body;
    map<string, string> headers;
    int timeoutMs = 5000;
};

class HttpRequest::Builder {                   // nested class: may access HttpRequest's privates
    HttpRequest req;
public:
    explicit Builder(string url) { req.url = std::move(url); }          // required parameter
    Builder& method(string m)           { req.method = std::move(m); return *this; }
    Builder& header(string k, string v) { req.headers[std::move(k)] = std::move(v); return *this; }
    Builder& body(string b)             { req.body = std::move(b); return *this; }
    Builder& timeout(int ms)            { req.timeoutMs = ms; return *this; }
    HttpRequest build() {
        if (req.method == "GET" && !req.body.empty()) throw logic_error("GET with body");   // validate once
        return req;
    }
};

HttpRequest r = HttpRequest::Builder("https://api.x.com/users")
                    .method("POST").header("Auth", "t").body("{}").timeout(2000)
                    .build();
r.print();      // POST https://api.x.com/users headers=1 timeout=2000
```

Chaining works by returning `*this` by reference (M0 §0.5). Benefits: readable call sites, optional parameters in any order, validation in one place, and the product can be **immutable** after `build()`.

**Use when:** 4+ parameters, many of them optional, or a multi-step construction. **Not when:** 2–3 parameters (a constructor, or designated initialisers / a config struct, is simpler).

---

## 8.6 Decorator

### Problem

Add responsibilities to objects **dynamically**, in **combinations**. A coffee with milk, caramel or extra shots: subclassing gives `EspressoWithMilk`, `EspressoWithMilkAndCaramel`, ..., which is a class explosion again.

### Solution

A decorator **implements the same interface** as the object it wraps, **holds** a wrapped object, and adds behaviour before or after delegating to it. Decorators can wrap decorators.

```cpp
struct Coffee { virtual double cost() const = 0; virtual string desc() const = 0; virtual ~Coffee() = default; };
struct Espresso : Coffee { double cost() const override { return 100; } string desc() const override { return "Espresso"; } };

class CoffeeDecorator : public Coffee {        // IS-A Coffee (same interface)...
protected:
    unique_ptr<Coffee> inner;                  // ...and HAS-A Coffee (the wrapped one)
public:
    explicit CoffeeDecorator(unique_ptr<Coffee> c) : inner(std::move(c)) {}
};
struct Milk : CoffeeDecorator {
    using CoffeeDecorator::CoffeeDecorator;    // inherit the constructor (M3 §3.4)
    double cost() const override { return inner->cost() + 20; }
    string desc() const override { return inner->desc() + " + Milk"; }
};
struct Caramel : CoffeeDecorator {
    using CoffeeDecorator::CoffeeDecorator;
    double cost() const override { return inner->cost() + 30; }
    string desc() const override { return inner->desc() + " + Caramel"; }
};

unique_ptr<Coffee> cup = make_unique<Caramel>(make_unique<Milk>(make_unique<Espresso>()));
cout << cup->desc() << " = " << cup->cost();     // Espresso + Milk + Caramel = 150
```

```
   Caramel  --wraps-->  Milk  --wraps-->  Espresso
   cost() = 30 + (20 + (100))
```

**Real uses:** I/O stream layers (buffering, compression and encryption wrapping a raw stream; Java's `BufferedReader(new FileReader(...))`), middleware (logging/auth/retry around an HTTP handler), adding caching or metrics around a repository.

**Decorator vs inheritance:** inheritance adds behaviour **statically, per class**. Decorator adds it **dynamically, per object**, and in any combination.

---

## 8.7 Adapter

### Problem

You have a class with the interface you need *conceptually* but the **wrong shape**, typically a third-party or legacy API you can't modify.

### Solution

A wrapper that **implements the interface your code expects** and **translates** each call to the existing class's interface.

```cpp
struct PaymentGateway {                                  // what OUR code expects
    virtual bool pay(double rupees) = 0;
    virtual ~PaymentGateway() = default;
};

class LegacyBankApi {                                    // third-party: can't change it
public:
    int makeTransfer(long paise, const char* currency) { /* ... */ return 0; }   // 0 = success
};

class LegacyBankAdapter : public PaymentGateway {
    LegacyBankApi api;                                   // composition (object adapter)
public:
    bool pay(double rupees) override {
        return api.makeTransfer(lround(rupees * 100), "INR") == 0;   // translate units, args, result
    }
};

unique_ptr<PaymentGateway> pg = make_unique<LegacyBankAdapter>();
pg->pay(499.99);     // Legacy transfer 49999 INR  -> returns true
```

**Real uses:** wrapping third-party SDKs (payment, SMS, maps) behind your own interface, so that switching vendors means writing a new adapter (DIP + OCP). Also legacy-system integration, and `std::stack`/`std::queue`, which are *container adapters* exposing a stack interface over a `deque`.

**Adapter vs Decorator:**

| | Adapter | Decorator |
|---|---|---|
| Interface | **Changes** it (A's shape → B's shape) | **Keeps** it (same interface in and out) |
| Purpose | Make incompatible things work together | Add behaviour |
| Stacking | Usually one layer | Often many layers |

---

## 8.8 State

### Problem

An object's behaviour depends on its **state**, and every method is a `switch` on the current state:

```cpp
void insertCoin() { switch (state) { case IDLE: ...; case HAS_COIN: ...; case SOLD_OUT: ...; } }
void selectItem() { switch (state) { case IDLE: ...; case HAS_COIN: ...; case SOLD_OUT: ...; } }
// every new state edits every method
```

### Solution

Make each state a **class** implementing a common interface. The context holds the current state object and delegates to it, and **states trigger transitions** by replacing it.

```cpp
class VendingMachine;
struct VmState {
    virtual void insertCoin(VendingMachine&) = 0;
    virtual void selectItem(VendingMachine&) = 0;
    virtual string name() const = 0;
    virtual ~VmState() = default;
};

class VendingMachine {
    unique_ptr<VmState> state;
public:
    VendingMachine();
    void setState(unique_ptr<VmState> s) { state = std::move(s); }
    void insertCoin() { state->insertCoin(*this); }        // delegate to the current state
    void selectItem() { state->selectItem(*this); }
    string stateName() const { return state->name(); }
};

struct IdleState : VmState {
    void insertCoin(VendingMachine& vm) override;
    void selectItem(VendingMachine&) override { cout << "Insert coin first\n"; }
    string name() const override { return "Idle"; }
};
struct HasCoinState : VmState {
    void insertCoin(VendingMachine&) override { cout << "Coin already inserted\n"; }
    void selectItem(VendingMachine& vm) override {
        cout << "Dispensing\n";
        vm.setState(make_unique<IdleState>());             // transition
    }
    string name() const override { return "HasCoin"; }
};
void IdleState::insertCoin(VendingMachine& vm) {
    cout << "Coin accepted\n";
    vm.setState(make_unique<HasCoinState>());              // transition
}
VendingMachine::VendingMachine() : state(make_unique<IdleState>()) {}

VendingMachine vm;
vm.selectItem();   // Insert coin first
vm.insertCoin();   // Coin accepted        -> HasCoin
vm.insertCoin();   // Coin already inserted
vm.selectItem();   // Dispensing           -> Idle
```

**Careful with `setState` inside a state method:** replacing `state` destroys the current state object while its member function is still running. That's safe here only because nothing touches `this` after `setState`. In real code, make `setState` the last statement, or defer the swap.

**Real uses:** vending machines, ATMs, elevators (M9b), order lifecycles (Placed → Paid → Shipped → Delivered), TCP connections, document workflows, game characters.

### Strategy vs State (asked often, because the UML is identical)

| | Strategy | State |
|---|---|---|
| What varies | **How** a task is done (algorithm) | **What** the object does, depending on its condition |
| Who changes it | The **client** chooses or swaps it | The **states themselves** trigger transitions |
| Do implementations know each other? | No, they're independent | Yes, each state knows its successor states |
| Example | Sale vs surge pricing | Idle → HasCoin → Dispensing |

---

## 8.9 Template Method (recap)

Covered in M4 §4.10 with `Shape::describe()`. A base class defines the **skeleton of an algorithm** in a non-virtual method and calls virtual "hook" steps that subclasses override.

```cpp
class DataExporter {
public:
    void exportData() { auto d = fetch(); auto f = format(d); write(f); }   // fixed skeleton
    virtual ~DataExporter() = default;
protected:
    virtual vector<Row> fetch() = 0;          // steps vary
    virtual string format(const vector<Row>&) = 0;
    virtual void write(const string&) = 0;
};
```

**Template Method vs Strategy:** Template Method varies *steps* through **inheritance** (compile time). Strategy varies the *whole algorithm* through **composition** (runtime). Prefer Strategy when you want runtime swapping.

---

# PART C — Consolidation

## 8.10 Pattern recognition guide

As with DSA patterns, recognise the requirement phrase and name the pattern within seconds:

| Requirement phrase | Pattern |
|---|---|
| "Only one instance", "global config / logger", "shared connection pool" | **Singleton** (or a single instance + DI) |
| "Create different types based on input", "hide which class gets instantiated" | **Factory** |
| "Families of related objects that must match" (themes, platforms) | **Abstract Factory** |
| "Many optional parameters", "step-by-step construction", "immutable once built" | **Builder** |
| "Multiple ways to do X", "choose the algorithm at runtime", "pluggable policy / rule" | **Strategy** |
| "Notify when something changes", "subscribe", "event", "alert me when" | **Observer** |
| "Behaviour depends on current status", "lifecycle", "transitions" | **State** |
| "Add features dynamically in combinations", "wrap with logging/caching" | **Decorator** |
| "Integrate a third-party / legacy API", "incompatible interface" | **Adapter** |
| "Same algorithm skeleton, steps differ per subclass" | **Template Method** |

## 8.11 Comparison tables

| Pair | Key difference |
|---|---|
| Strategy vs State | Client swaps the algorithm vs states drive their own transitions |
| Factory vs Builder | Picks *which* class to create vs assembles *one complex* object step by step |
| Decorator vs Adapter | Same interface, adds behaviour vs different interface, translates |
| Decorator vs inheritance | Dynamic, per object, combinable vs static, per class |
| Strategy vs Template Method | Composition, runtime vs inheritance, compile time |
| Singleton vs static class | An object (interfaces, laziness, passable) vs a bag of functions |

## 8.12 Must remember (module)

1. Categories: creational (Singleton, Factory, Builder), structural (Adapter, Decorator), behavioural (Strategy, Observer, State, Template Method).
2. **Singleton** = private constructor + deleted copies + function-local static (thread-safe since C++11). Creation is thread-safe; methods aren't. Criticisms: global state and testability; prefer DI.
3. **Factory** returns `unique_ptr<Base>`; Simple vs Factory Method vs Abstract Factory.
4. **Strategy** = interchangeable algorithms behind an interface, swappable at runtime. Lambdas/`std::function` for one-function strategies.
5. **Observer** = subject notifies subscribed observers. Pitfalls: dangling observers, mutation during notification, threading.
6. **Builder** for many optional parameters; chain by returning `*this&`; validate in `build()`.
7. **Decorator** = same interface + wraps an inner object; stackable.
8. **Adapter** = translate an incompatible interface; wrap third-party SDKs.
9. **State** = a class per state; states trigger transitions. Strategy vs State is about who drives the change.
10. Always know **when not to use** each one.

## 8.13 Common wrong answers (module)

- A Singleton with a `static T* inst` and an unsynchronised `if (!inst) inst = new T;` presented as thread-safe.
- "Singleton is a good way to share data." It's global state; mention the drawbacks.
- Confusing Strategy and State, or Decorator and Adapter.
- "Factory is any function that returns an object."
- Using a pattern without being able to name the problem it solves.

## 8.14 Interview Q&A bank

| Question | Crisp answer | Likely follow-up |
|---|---|---|
| What are design patterns? | Named, reusable solutions to recurring design problems; creational, structural, behavioural | Which have you used? |
| Thread-safe Singleton in C++? | Meyers: function-local static, private constructor, deleted copies | Disadvantages? |
| Factory vs Abstract Factory? | One product by parameter vs a family of related products | Factory Method? |
| What is Strategy? Example? | Swappable algorithms behind an interface: pricing, routing, payment | Strategy vs State |
| Explain Observer | Subject notifies registered observers via an interface | How do you avoid dangling observers? |
| When Builder? | Many optional parameters, validation, immutability | Builder vs Factory |
| Decorator example? | Coffee add-ons, stream wrappers, middleware | Decorator vs inheritance |
| Adapter example? | Wrapping a legacy or third-party API | Adapter vs Decorator |
| Which patterns in a parking lot? | Strategy (allocation, pricing), Factory (vehicles/spots), Singleton (lot, debatable), Observer (display boards) | Justify each |

## 8.15 Practice

**P1.** Name the pattern for each requirement:
1. A ride app computes fares differently for normal, pool and premium rides, and ops can change the rule live.
2. Send order updates to email, SMS and push, and new channels will be added.
3. Users get a "back in stock" alert when a product is restocked.
4. An `Order` moves through Created → Paid → Shipped → Delivered, and allowed actions depend on the stage.
5. Your code uses a `Maps` interface; the company switches from Google Maps' SDK to Mapbox's SDK, which has different method names.
6. A `Pizza` can have any combination of toppings, each adding cost.
7. A `QueryOptions` object has 9 optional fields.
8. The entire app must share one configuration object loaded at startup.

<details><summary>Answer</summary>

1 Strategy · 2 Factory (+ Strategy for the channels) · 3 Observer · 4 State · 5 Adapter · 6 Decorator · 7 Builder · 8 Singleton (or one instance + dependency injection, which is better for testing)
</details>

**P2.** What's wrong with this Singleton, and how do you fix it?
```cpp
class Config {
public:
    static Config* get() { if (!inst) inst = new Config(); return inst; }
    Config() {}
private:
    static Config* inst;
};
```
<details><summary>Answer</summary>

(1) The **public constructor** lets anyone create more instances. (2) The copy constructor and assignment aren't deleted. (3) `get()` is a **data race**: two threads can create two instances. (4) It's never destroyed. Fix: the Meyers Singleton (private constructor, deleted copy operations, `static Config& get() { static Config c; return c; }`).
</details>

**P3.** Refactor using the right pattern:
```cpp
double discount(const string& type, double amt) {
    if (type == "student") return amt * 0.10;
    if (type == "senior")  return amt * 0.15;
    if (type == "festive") return min(amt * 0.20, 500.0);
    return 0;
}
```
<details><summary>Answer</summary>

**Strategy** + **Simple Factory**: a `DiscountStrategy` interface with `StudentDiscount`, `SeniorDiscount`, `FestiveDiscount` and `NoDiscount`, and a `DiscountFactory::create(type)` that holds the one remaining conditional (or a `unordered_map<string, function<unique_ptr<DiscountStrategy>()>>` registry, so adding a type doesn't even edit the factory's logic).
</details>

**P4.** In the Observer implementation above, what happens if a `MobileApp` object is destroyed while still subscribed and `setPrice` is called? Give two fixes.

<details><summary>Answer</summary>

Undefined behaviour: the subject calls `update()` through a dangling pointer. Fixes: (1) RAII: the observer stores a reference to the subject and calls `unsubscribe(this)` in its destructor; (2) the subject stores `weak_ptr<Observer>` and skips or removes expired entries during notification (observers are then owned by `shared_ptr`s).
</details>

**P5.** Design the classes (no full code) for a **text editor's formatting**: plain text can be made bold, italic and underlined in any combination, and new formats will be added. Which pattern, and what is the interface?

<details><summary>Answer</summary>

**Decorator.** `struct Text { virtual string render() const = 0; }`, `PlainText : Text`, `TextDecorator : Text` holding `unique_ptr<Text>`, and `Bold`, `Italic`, `Underline : TextDecorator` wrapping the inner `render()` in tags. `Bold(Italic(PlainText("hi")))` renders `<b><i>hi</i></b>`. A new format is a new decorator class (OCP).
</details>

---

## Exit checklist

```
[ ] I can name the three categories and place each pattern in one
[ ] I can write the Meyers Singleton and explain why it's thread-safe, and critique Singletons
[ ] I can write a Simple Factory returning unique_ptr, and explain Factory Method and Abstract Factory
[ ] I can write Strategy with runtime swapping, and mention the lambda alternative
[ ] I can write Observer and list its pitfalls (dangling, mutation during notify, threading)
[ ] I can sketch Builder, Decorator, Adapter and State, with one real use each
[ ] I can distinguish Strategy/State, Decorator/Adapter, Factory/Builder, Strategy/Template Method
[ ] I can map requirement phrases to patterns (§8.10) in seconds
[ ] P1–P5 done
```

---

## Next

**Part 11: M9a — Low-Level Design: the method, Parking Lot, LRU Cache, Splitwise.** It covers what LLD rounds grade and how to spend 45–60 minutes, the 6-step method, and three complete designs with requirements, class diagrams, compilable C++, and the "now extend it" follow-ups interviewers ask.
