# OOP Placement Handbook (C++) — Part 11
# Module 9a: Low-Level Design — The Method, Parking Lot, LRU Cache, Splitwise

**Module 9a · 4–5 hours · Tier 2 · Requires: M4, M5, M6 (smart pointers), M7, M8**

---

## What an LLD round is

An LLD (low-level design) round asks you to design the **classes, relationships and core code** of a small system: a parking lot, a cache, an expense splitter. It is where everything in M0–M8 is graded at once, under time pressure, on a problem you haven't seen before.

| | LLD / object-oriented design | HLD / system design |
|---|---|---|
| Unit of design | Classes, interfaces, methods | Services, databases, queues, caches |
| Question | "Design the classes for a parking lot" | "Design a parking system for 10,000 lots nationwide" |
| Output | Class diagram + working code | Architecture diagram + scaling plan |
| Asked of | Freshers/SDE-1 onwards (where an LLD round exists) | Mostly SDE-2 and above |

### Two formats

| Format | Duration | What you produce | Reported at (varies by team and year) |
|---|---|---|---|
| **Design discussion** | 45–60 min | Requirements, class diagram, key classes and methods in code, extension discussion | Amazon, Microsoft, Atlassian, many product companies |
| **Machine coding** | 90–150 min | A **running** program with clean structure, often with demo input, sometimes tests | Flipkart, Swiggy, Razorpay, PhonePe, Uber, Zomato, CRED and similar Indian product companies |

The method below works for both. In machine coding, steps 5–6 just take longer, and the code must actually run.

The organising principle:

> **LLD is graded on how cheaply your design absorbs the next requirement. Get the entities and relationships right, put interfaces exactly where variation is likely, keep each class to one responsibility, and the interviewer's "now add X" becomes "that's one new class", which is the moment the round is won.**

---

## 9a.1 What interviewers grade

| Criterion | What they look for | How to show it |
|---|---|---|
| **Requirements clarity** | You scoped the problem before designing | Ask 4–6 sharp questions; write down the agreed requirements |
| **Object modelling** | The right entities with the right responsibilities | Nouns → classes; no god class; behaviour lives with its data (M2) |
| **Relationships** | Correct is-a / has-a, ownership, multiplicity | Clean class diagram (M5) |
| **Extensibility** | New variants need new classes, not edits | Interfaces at variation points (Strategy, Factory: M7, M8) |
| **Code quality** | Readable, encapsulated, correct C++ | Private data, `const`, smart pointers, enums, validation |
| **Correctness and edge cases** | Full lot, invalid ticket, rounding, duplicates | Explicit checks and error handling |
| **Concurrency awareness** | Shared mutable state is identified | Name where races happen; add locks there |
| **Communication** | Thinking out loud, trade-offs stated | "I chose X over Y because..." |

**What loses the round:** jumping into code without requirements, one giant class, inheritance used for reuse (`Car extends ParkingSpot`), `switch` on type strings everywhere, no extension story, silence.

---

## 9a.2 The 6-step method

Time budget for a 60-minute round (machine coding: stretch steps 5–6):

| Step | What | Time |
|---|---|---|
| 1 | **Clarify requirements**: functional, scope out, constraints | 5–8 min |
| 2 | **Identify entities**: nouns → classes, enums | 5 min |
| 3 | **Define relationships and responsibilities**: who owns whom, who does what | 5 min |
| 4 | **Draw the class diagram** and the key interfaces | 5–8 min |
| 5 | **Code the core**: models, then the main service and its main flows | 20–25 min |
| 6 | **Extend and discuss**: new requirements, concurrency, edge cases, testing | 5–10 min |

### Step 1: Clarify requirements

Ask questions that **change the design**, not trivia. Template:

- **Actors:** who uses it? (customer, admin, system)
- **Core use cases:** what are the 3–5 must-have operations?
- **Variants:** what types exist, and will more be added? (Vehicle types, split types, payment modes. These become your interfaces.)
- **Rules:** pricing, limits, validation, ordering.
- **Scale and concurrency:** one instance or many? Concurrent users? (Decides where the locks go.)
- **Out of scope:** payments, auth, UI and persistence are usually out. **Say so explicitly.**

Then **write the agreed requirement list down**. It's your contract for the rest of the round.

### Step 2: Identify entities

Underline the **nouns** in the requirements. These are candidate classes. Then:
- Merge synonyms; drop nouns that are just attributes (a "plate number" is a field, not a class).
- Turn fixed small sets into **enums** (`VehicleType`, `SpotSize`, `OrderStatus`).
- Turn **varying behaviour** into **interfaces** (`FeeStrategy`, `SplitStrategy`).
- **Verbs** become methods. Attach each to the class that **owns the data it needs** (a spot knows whether it can fit a vehicle).

### Step 3: Relationships and responsibilities

For each pair: is-a or has-a? Who **owns** whom (composition) and who merely **refers** (association)? What are the multiplicities? Watch for:
- Inheritance only for genuine, substitutable is-a (M7 LSP). **Data-only differences don't need subclasses**; an enum field is often enough.
- One **service / orchestrator** class per use case cluster (`ParkingLot`, `ExpenseManager`). It coordinates, while the entities hold the rules.

### Step 4: Class diagram

Boxes for the 6–10 key classes; the UML arrows from M5; interfaces marked. Talk through one flow on the diagram ("a car arrives: the gate asks the lot, the lot asks the allocation strategy...") **before** you write code.

### Step 5: Code the core

Order: **enums and models → interfaces → concrete strategies → the service → a tiny `main` demo**. Rules:
- Private data, public behaviour, `const` getters.
- `unique_ptr` for owned polymorphic parts; raw pointers or references for non-owning links (M6).
- Validate inputs and throw or return `optional` on failure.
- Skip boilerplate (trivial getters for everything); say "plus the obvious getters".

### Step 6: Extend and discuss

Expect "now add X". Answer by pointing at the interface X plugs into. Then volunteer: **concurrency** (what's shared, where the lock goes), **edge cases**, and **how you'd test it** (inject fake strategies).

### Common mistakes

1. Coding before requirements are agreed.
2. A god class (`ParkingLotManager` with 40 methods).
3. Inheritance for differences that are just data (`RedCar : Car`).
4. Type-string `switch`es everywhere instead of polymorphism.
5. Money in `double` (use integer paise/cents).
6. Ignoring concurrency entirely, or locking everything without saying why.
7. Over-engineering: interfaces for things that will never vary (YAGNI).
8. Long silences. Narrate decisions.

---

# Design 1: Parking Lot

## 9a.3 Parking Lot

The single most-asked LLD question.

### Step 1: Requirements (as agreed with the interviewer)

**In scope**
1. The lot has multiple **floors**; each floor has **spots** of sizes Small, Medium and Large.
2. Vehicles: **Bike, Car, Truck**. A vehicle fits a spot of its size **or larger** (bike → small+, car → medium+, truck → large).
3. **Park:** on entry, assign a spot and issue a **ticket**; if nothing fits, reject.
4. **Unpark:** on exit, given the ticket, compute the **fee** and free the spot.
5. **Fee:** hourly, by vehicle type, rounded up, minimum 1 hour.
6. Several **entry/exit gates** operate concurrently.
7. **Extensible:** the spot allocation rule and the pricing rule must be changeable.

**Out of scope:** payment processing, display boards, reservations, persistence (mention them as extensions).

### Step 2: Entities

| Noun | Becomes |
|---|---|
| Vehicle type, spot size | `enum class VehicleType`, `enum class SpotSize` |
| Vehicle | `struct Vehicle` (plate + type). **No subclasses**: bike, car and truck differ only by data here |
| Spot | `class ParkingSpot` (knows its size and occupant; decides `canFit`) |
| Floor | `struct Floor` (number + spots) |
| Ticket | `struct Ticket` (id, vehicle, spot, entry time) |
| "Which spot?" (varies) | `interface SpotAllocationStrategy` → `NearestFirst` |
| "How much?" (varies) | `interface FeeStrategy` → `HourlyFee` |
| The lot | `class ParkingLot` (orchestrator: park/unpark, owns floors, active tickets, the lock) |

**Design decision to say out loud:** *"I'm not subclassing Vehicle into Car/Bike/Truck because they have no different behaviour, only a different size requirement. An enum is simpler. If, say, electric vehicles later need charging behaviour, I'd add that as a capability."*

### Step 3–4: Relationships and class diagram

```
                                   <<interface>>                       <<interface>>
                               SpotAllocationStrategy                   FeeStrategy
                               + findSpot(floors, v)                + fee(ticket, exit)
                                        ^                                   ^
                                        |                                   |
                                   NearestFirst                         HourlyFee
                                        ^                                   ^
                                        | 1 (owns, unique_ptr)              | 1
 +------------------+                   |                                   |
 |    ParkingLot    |<#>----------------+-----------------------------------+
 +------------------+
 | - floors         |<#>--- 1..* ---> Floor <#>--- 1..* ---> ParkingSpot
 | - active tickets |                                        - id, size
 | - mutex          |<#>--- 0..* ---> Ticket ---- 1 ------->  - optional<Vehicle>
 | + park(v, t)     |                 - id, entryMinute       + canFit(v)
 | + unpark(id, t)  |                 - vehicle : Vehicle     + park(v), vacate()
 +------------------+
```

The lot **owns** floors, floors **own** spots (composition). A ticket **refers** to its spot (non-owning association). The lot **owns** its two strategies (composition with injected implementations: DIP).

### Step 5: Code

```cpp
#include <bits/stdc++.h>
using namespace std;

enum class VehicleType { Bike, Car, Truck };
enum class SpotSize    { Small, Medium, Large };      // ordered: bigger spots fit smaller vehicles

SpotSize requiredSize(VehicleType t) {
    switch (t) {
        case VehicleType::Bike:  return SpotSize::Small;
        case VehicleType::Car:   return SpotSize::Medium;
        case VehicleType::Truck: return SpotSize::Large;
    }
    throw logic_error("unknown vehicle type");
}

struct Vehicle {
    string plate;
    VehicleType type;
};

class ParkingSpot {
    string id;
    SpotSize size;
    optional<Vehicle> parked;                         // empty = free
public:
    ParkingSpot(string id, SpotSize s) : id(std::move(id)), size(s) {}
    bool isFree() const { return !parked.has_value(); }
    bool canFit(const Vehicle& v) const { return isFree() && size >= requiredSize(v.type); }
    void park(const Vehicle& v) { if (!canFit(v)) throw logic_error("spot unavailable"); parked = v; }
    void vacate() { parked.reset(); }
    const string& getId() const { return id; }
};

struct Floor {
    int number;
    vector<ParkingSpot> spots;
};

struct Ticket {
    string id;
    Vehicle vehicle;
    ParkingSpot* spot;                                // non-owning: the Floor owns spots
    long long entryMinute;
};

// ---- extension point 1: which spot? ----
struct SpotAllocationStrategy {
    virtual ParkingSpot* findSpot(vector<Floor>& floors, const Vehicle& v) = 0;
    virtual ~SpotAllocationStrategy() = default;
};
struct NearestFirst : SpotAllocationStrategy {
    ParkingSpot* findSpot(vector<Floor>& floors, const Vehicle& v) override {
        for (auto& f : floors)
            for (auto& s : f.spots)
                if (s.canFit(v)) return &s;
        return nullptr;
    }
};

// ---- extension point 2: how much? ----
struct FeeStrategy {
    virtual long long fee(const Ticket& t, long long exitMinute) const = 0;   // rupees
    virtual ~FeeStrategy() = default;
};
class HourlyFee : public FeeStrategy {
    map<VehicleType, long long> ratePerHour;
public:
    explicit HourlyFee(map<VehicleType, long long> r) : ratePerHour(std::move(r)) {}
    long long fee(const Ticket& t, long long exitMinute) const override {
        long long mins  = max(0LL, exitMinute - t.entryMinute);
        long long hours = max(1LL, (mins + 59) / 60);          // round up, minimum 1 hour
        return hours * ratePerHour.at(t.vehicle.type);
    }
};

class ParkingLot {
    vector<Floor> floors;
    unique_ptr<SpotAllocationStrategy> allocator;
    unique_ptr<FeeStrategy> pricing;
    unordered_map<string, Ticket> active;              // ticketId -> ticket
    long long nextTicket = 1;
    mutex mtx;                                         // gates run concurrently
public:
    ParkingLot(vector<Floor> f, unique_ptr<SpotAllocationStrategy> a, unique_ptr<FeeStrategy> p)
        : floors(std::move(f)), allocator(std::move(a)), pricing(std::move(p)) {}

    optional<Ticket> park(const Vehicle& v, long long nowMinute) {
        lock_guard<mutex> g(mtx);                      // find + occupy must be ATOMIC
        ParkingSpot* spot = allocator->findSpot(floors, v);
        if (!spot) return nullopt;                     // full for this vehicle type
        spot->park(v);
        Ticket t{"T" + to_string(nextTicket++), v, spot, nowMinute};
        active.emplace(t.id, t);
        return t;
    }

    long long unpark(const string& ticketId, long long nowMinute) {
        lock_guard<mutex> g(mtx);
        auto it = active.find(ticketId);
        if (it == active.end()) throw invalid_argument("invalid ticket");
        long long amount = pricing->fee(it->second, nowMinute);
        it->second.spot->vacate();
        active.erase(it);
        return amount;
    }
};

int main() {
    vector<Floor> floors = {
        {0, {ParkingSpot("F0-S1", SpotSize::Small), ParkingSpot("F0-M1", SpotSize::Medium)}},
        {1, {ParkingSpot("F1-L1", SpotSize::Large)}}
    };
    ParkingLot lot(std::move(floors), make_unique<NearestFirst>(),
                   make_unique<HourlyFee>(map<VehicleType, long long>{
                       {VehicleType::Bike, 10}, {VehicleType::Car, 30}, {VehicleType::Truck, 60}}));

    auto t1 = lot.park({"KA01", VehicleType::Car}, 0);     // F0-M1
    auto t2 = lot.park({"KA02", VehicleType::Car}, 5);     // medium taken -> F1-L1 (larger fits)
    auto t3 = lot.park({"KA03", VehicleType::Car}, 6);     // nothing fits -> nullopt
    cout << t1->spot->getId() << " " << t2->spot->getId() << " " << (t3 ? "yes" : "full") << "\n";
    cout << lot.unpark(t1->id, 130) << "\n";               // 130 min -> 3 h x 30 = 90
    auto t4 = lot.park({"KA04", VehicleType::Bike}, 140);
    cout << t4->spot->getId() << "\n";                      // F0-S1
    try { lot.unpark("T99", 200); } catch (const exception& e) { cout << e.what() << "\n"; }
}
```

**Output:**
```
F0-M1 F1-L1 full
90
F0-S1
invalid ticket
```

### Design notes to say out loud

- **Why `findSpot` + `park` are under one lock:** two gates could both find the same free spot and both park in it, a classic check-then-act race (OS handbook, synchronization). The lock makes the pair atomic. **Scaling it:** one global lock serialises all gates. Better: a lock **per floor**, or an atomic compare-and-set on each spot's state, so gates contend only when they pick the same spot.
- **Pointer stability:** `Ticket::spot` points into a `vector<ParkingSpot>`. That's safe because the spot vectors never change size after construction. If floors could be added at runtime, use stable storage (`vector<unique_ptr<ParkingSpot>>`, or IDs instead of pointers).
- **Time as a parameter** (`nowMinute`) instead of reading the clock inside: it makes the code deterministic and testable (DIP applied to time). Mention a `Clock` interface for production.
- **Money as integers** (whole rupees here; use paise if fractional prices are possible).

### Step 6: Extensions the interviewer will ask for

| "Now add..." | Answer |
|---|---|
| Different pricing: weekend rates, first hour free, flat daily cap | A new `FeeStrategy` class. **Nothing else changes** (OCP) |
| Allocate the spot nearest to the exit / best-fit size instead of first-fit | A new `SpotAllocationStrategy` (e.g. `BestFit`, which prefers the smallest fitting size) |
| EV charging spots | `SpotSize` stays; add a `features` set (or a `ChargingSpot` with charging behaviour) and an allocation strategy that honours a vehicle's `needsCharging` |
| Display boards showing free spots per floor | **Observer**: the lot notifies `DisplayBoard` observers on park and unpark |
| Payment modes (cash, card, UPI) | `PaymentMethod` interface + Factory, called in `unpark` |
| Multiple lots in a city | A `ParkingLot` per site; a registry service on top (this becomes HLD) |
| Make `ParkingLot` a Singleton? | Possible (one lot per process), but injection is better for testability (M8 §8.1). Say both |
| Lost ticket | Look up by plate: add an `unordered_map<string plate, ticketId>` index, plus a penalty in the fee strategy |

---

# Design 2: LRU Cache (the LLD version)

## 9a.4 LRU Cache

**DSA Part 8 §6.10** already covers the LeetCode version (LC 146): a hand-written doubly linked list + hash map with `int` keys. In an **LLD round**, the same question is graded differently. The interviewer wants a **generic**, **extensible** and **thread-safe** design: *"Design a cache with a configurable eviction policy."*

### Step 1: Requirements

1. `get(key)` → value or "miss"; `put(key, value)`; fixed **capacity**.
2. When full, **evict** according to a policy: **LRU** now, **LFU / FIFO** later.
3. Generic key and value types.
4. **Thread-safe**: used by many request threads.
5. O(1) average `get` and `put`.

### Step 2–4: Entities and diagram

```
 +---------------------+          1   <<interface>> EvictionPolicy<K>
 |   Cache<K, V>       |<#>-------->  + keyAccessed(k)
 +---------------------+               + keyAdded(k)
 | - capacity          |               + evict() : K
 | - store : map K->V  |                    ^           ^
 | - mutex             |                    |           |
 | + get(k) : opt<V>   |              LruPolicy<K>   LfuPolicy<K> (extension)
 | + put(k, v)         |              list<K> + map<K, iterator>
 +---------------------+
```

**The key decision:** separate **storage** (the cache's map) from **eviction bookkeeping** (the policy). The cache never knows *why* a key was chosen for eviction. That's SRP + Strategy, and it's what turns a LeetCode answer into an LLD answer.

### Step 5: Code

```cpp
template <class K>
struct EvictionPolicy {
    virtual void keyAccessed(const K& k) = 0;      // on get, or on put to an existing key
    virtual void keyAdded(const K& k) = 0;
    virtual K evict() = 0;                         // choose a victim and forget it
    virtual ~EvictionPolicy() = default;
};

template <class K>
class LruPolicy : public EvictionPolicy<K> {
    list<K> order;                                             // front = most recently used
    unordered_map<K, typename list<K>::iterator> pos;          // key -> its node, for O(1) moves
public:
    void keyAccessed(const K& k) override { order.splice(order.begin(), order, pos.at(k)); }  // O(1)
    void keyAdded(const K& k) override    { order.push_front(k); pos[k] = order.begin(); }
    K evict() override {
        K victim = order.back();
        order.pop_back();
        pos.erase(victim);
        return victim;
    }
};

template <class K, class V>
class Cache {
    size_t capacity;
    unordered_map<K, V> store;
    unique_ptr<EvictionPolicy<K>> policy;
    mutable mutex mtx;
public:
    Cache(size_t cap, unique_ptr<EvictionPolicy<K>> p) : capacity(cap), policy(std::move(p)) {
        if (cap == 0) throw invalid_argument("capacity must be positive");
    }
    optional<V> get(const K& k) {
        lock_guard<mutex> g(mtx);
        auto it = store.find(k);
        if (it == store.end()) return nullopt;
        policy->keyAccessed(k);                    // a read changes recency: it's a WRITE to the policy
        return it->second;
    }
    void put(const K& k, const V& v) {
        lock_guard<mutex> g(mtx);
        auto it = store.find(k);
        if (it != store.end()) { it->second = v; policy->keyAccessed(k); return; }
        if (store.size() == capacity) store.erase(policy->evict());
        store.emplace(k, v);
        policy->keyAdded(k);
    }
};

int main() {
    Cache<int, string> cache(2, make_unique<LruPolicy<int>>());
    cache.put(1, "one"); cache.put(2, "two");
    cache.get(1);                                   // 1 becomes most recent
    cache.put(3, "three");                          // evicts 2 (least recent)
    cout << (cache.get(2) ? "hit" : "miss") << " " << *cache.get(1) << " " << *cache.get(3) << "\n";
    cache.put(1, "uno");                            // update refreshes 1
    cache.put(4, "four");                           // evicts 3
    cout << (cache.get(3) ? "hit" : "miss") << " " << *cache.get(1) << "\n";
}
```

**Output:**
```
miss one three
miss uno
```

### Design notes to say out loud

- **`std::list::splice`** moves a node to the front in O(1) without reallocating. It's the standard-library equivalent of the hand-written DLL from DSA Part 8 (which you should still be able to write if asked).
- **Why `get` takes an exclusive lock, not a shared (reader) lock:** in LRU, every read **reorders** the recency list, so reads mutate state. A `shared_mutex` would be wrong here. This is the subtle concurrency point interviewers probe.
- **Scaling the lock:** one mutex serialises everything. For high throughput, use **sharding**: N independent caches, each with its own lock, with the shard chosen by `hash(key) % N`. Approximate LRU per shard is usually acceptable.
- **`get` returns `optional<V>` by value**, not a reference into the map. A reference could dangle once another thread evicts that entry.

### Step 6: Extensions

| "Now add..." | Answer |
|---|---|
| LFU eviction | `LfuPolicy`: `key → freq`, `freq → list<K>` (LRU within each frequency), and `minFreq`, all O(1) (LC 460). The `Cache` class is unchanged |
| TTL / expiry | Store `{value, expiresAt}`; treat expired entries as misses on `get` (lazy expiry); optionally a background sweeper thread |
| Eviction listener (e.g. write-back to a DB) | Observer: callbacks invoked with the evicted key and value |
| Size by bytes instead of count | A `weigher` function; evict until the total weight fits |
| Distributed cache | Consistent hashing across nodes: HLD territory |

---

# Design 3: Splitwise

## 9a.5 Splitwise (expense sharing)

### Step 1: Requirements

1. **Users** can be added.
2. **Add an expense:** a payer, an amount, participants, and a **split type**:
   - **EQUAL**: divided equally (leftover paise distributed fairly)
   - **EXACT**: given amounts, which must sum to the total
   - **PERCENT**: given percentages, which must sum to 100
3. **Show balances:** how much each user owes or is owed overall.
4. **Settle up:** suggest a small set of transactions that clears all debts.
5. More split types (shares/ratio) will be added later.

**Out of scope:** groups (mention as an extension), currencies, persistence, notifications.

### Step 2–4: Entities and diagram

| Noun | Becomes |
|---|---|
| Money | `using Paise = long long;` **integers, never `double`** |
| User | A string ID here (a `User` class with name, email and phone in a fuller version) |
| Split type (varies, will grow) | `interface SplitStrategy` → `EqualSplit`, `ExactSplit`, `PercentSplit` |
| Expense | `struct Expense` (id, description, payer, amount, computed shares) |
| Balances, settle-up | `class ExpenseManager` (orchestrator) |

```
 +-------------------------+                 <<interface>> SplitStrategy
 |     ExpenseManager      |  uses (dep.)    + split(total, users, params) : map<user, Paise>
 +-------------------------+ - - - - - - ->          ^          ^           ^
 | - users : set           |                         |          |           |
 | - expenses : vector     |<#>-- 0..* --> Expense  EqualSplit ExactSplit PercentSplit
 | - net : map<user,Paise> |
 | + addUser(u)            |
 | + addExpense(...)       |
 | + balanceOf(u)          |
 | + settleUp() : txns     |
 +-------------------------+
```

**The key modelling decision: store each user's net balance, not pairwise debts.** A user's net = (total they paid) − (total of their shares). Positive means they're owed; negative means they owe. The nets always sum to zero. Pairwise "who owes whom" is derived at settle-up time. This keeps `addExpense` O(participants) and makes debt simplification natural.

### Step 5: Code

```cpp
using Paise = long long;                        // money as integers: no floating-point drift

struct SplitStrategy {
    // how much each participant owes; must sum EXACTLY to total
    virtual map<string, Paise> split(Paise total, const vector<string>& users,
                                     const vector<double>& params) const = 0;
    virtual ~SplitStrategy() = default;
};

struct EqualSplit : SplitStrategy {
    map<string, Paise> split(Paise total, const vector<string>& users, const vector<double>&) const override {
        map<string, Paise> res;
        Paise share = total / (Paise)users.size(), rem = total % (Paise)users.size();
        for (size_t i = 0; i < users.size(); i++)
            res[users[i]] += share + ((Paise)i < rem ? 1 : 0);    // spread leftover paise
        return res;
    }
};

struct ExactSplit : SplitStrategy {
    map<string, Paise> split(Paise total, const vector<string>& users, const vector<double>& amts) const override {
        if (amts.size() != users.size()) throw invalid_argument("need one amount per user");
        map<string, Paise> res; Paise sum = 0;
        for (size_t i = 0; i < users.size(); i++) { res[users[i]] += (Paise)llround(amts[i]); sum += (Paise)llround(amts[i]); }
        if (sum != total) throw invalid_argument("exact amounts must add up to total");
        return res;
    }
};

struct PercentSplit : SplitStrategy {
    map<string, Paise> split(Paise total, const vector<string>& users, const vector<double>& pct) const override {
        if (pct.size() != users.size()) throw invalid_argument("need one percent per user");
        if (llround(accumulate(pct.begin(), pct.end(), 0.0) * 100) != 10000) throw invalid_argument("percents must sum to 100");
        map<string, Paise> res; Paise given = 0;
        for (size_t i = 0; i < users.size(); i++) {
            Paise p = (i + 1 == users.size()) ? total - given : (Paise)llround(total * pct[i] / 100.0);
            res[users[i]] += p; given += p;                      // last user absorbs rounding
        }
        return res;
    }
};

struct Expense {
    string id, description, paidBy;
    Paise amount;
    map<string, Paise> shares;
};

class ExpenseManager {
    set<string> users;
    vector<Expense> expenses;
    map<string, Paise> net;                             // + : should receive, - : owes
public:
    void addUser(const string& u) { users.insert(u); net[u]; }

    const Expense& addExpense(const string& desc, const string& paidBy, Paise amount,
                              const vector<string>& participants,
                              const SplitStrategy& strategy, const vector<double>& params = {}) {
        if (!users.count(paidBy)) throw invalid_argument("unknown payer");
        for (auto& u : participants) if (!users.count(u)) throw invalid_argument("unknown user " + u);
        auto shares = strategy.split(amount, participants, params);   // validates BEFORE any state changes
        net[paidBy] += amount;
        for (auto& [u, s] : shares) net[u] -= s;
        expenses.push_back({"E" + to_string(expenses.size() + 1), desc, paidBy, amount, shares});
        return expenses.back();
    }

    Paise balanceOf(const string& u) const { return net.at(u); }

    // Greedy simplification: settle the largest debtor against the largest creditor, repeatedly.
    vector<tuple<string, string, Paise>> settleUp() const {
        priority_queue<pair<Paise, string>> creditors, debtors;          // max-heaps (DSA Part 12)
        for (auto& [u, b] : net) {
            if (b > 0) creditors.push({b, u});
            else if (b < 0) debtors.push({-b, u});
        }
        vector<tuple<string, string, Paise>> tx;
        while (!creditors.empty() && !debtors.empty()) {
            auto [c, cu] = creditors.top(); creditors.pop();
            auto [d, du] = debtors.top();   debtors.pop();
            Paise x = min(c, d);
            tx.emplace_back(du, cu, x);                                  // du pays cu
            if (c > x) creditors.push({c - x, cu});
            if (d > x) debtors.push({d - x, du});
        }
        return tx;
    }
};

int main() {
    ExpenseManager em;
    for (auto u : {"A", "B", "C", "D"}) em.addUser(u);
    EqualSplit eq; ExactSplit ex; PercentSplit pc;

    em.addExpense("Dinner", "A", 100000, {"A", "B", "C", "D"}, eq);        // Rs 1000.00 equally
    em.addExpense("Cab",    "B",  30000, {"B", "C"}, ex, {10000, 20000});  // Rs 300.00, exact
    em.addExpense("Hotel",  "C", 100001, {"A", "C"}, pc, {50, 50});        // Rs 1000.01, odd paisa

    for (auto u : {"A", "B", "C", "D"}) cout << u << ":" << em.balanceOf(u) << " ";
    cout << "\n";
    for (auto& [from, to, amt] : em.settleUp()) cout << from << "->" << to << " " << amt << "\n";

    try { em.addExpense("Bad", "A", 1000, {"A", "B"}, ex, {100, 100}); }
    catch (const exception& e) { cout << e.what() << "\n"; }
}
```

**Output:**
```
A:24999 B:-5000 C:5001 D:-25000
D->A 24999
B->C 5000
D->C 1
exact amounts must add up to total
```

**Checking the numbers** (always verify with the interviewer):
- Dinner: A paid 100000; each owes 25000 → A +75000; B, C, D −25000 each.
- Cab: B paid 30000; B owes 10000, C owes 20000 → B −5000, C −45000.
- Hotel: C paid 100001; A's 50% = `llround(50000.5)` = 50001 and C absorbs the rest (50000) → A +24999, C +5001.
- Nets: 24999 − 5000 + 5001 − 25000 = **0**. ✓ (The nets summing to zero is a great invariant to assert in tests.)

### Design notes to say out loud

- **Integers for money.** `0.1 + 0.2 != 0.3` in floating point. ₹1000 ÷ 3 must give 33333 + 33333 + 33334 paise, with no paisa lost. That's handled explicitly by distributing the remainder.
- **Validate before mutating.** `split()` throws before `net` changes, so a bad expense leaves the state untouched (the strong exception guarantee, M6 §6.8).
- **Strategy for split types.** `ShareSplit` (by ratio, e.g. 2:1:1) is one new class. The manager doesn't change.
- **Settle-up complexity.** Each greedy step zeroes at least one person, so there are at most n−1 transactions, in O(n log n) with heaps. Finding the true *minimum* number of transactions is NP-hard in general (it reduces to partitioning people into zero-sum subgroups). The greedy is the standard practical answer. Say this; it shows depth.

### Step 6: Extensions

| "Now add..." | Answer |
|---|---|
| Groups (trip, flat) | `Group { id, members, its own net map }`; expenses belong to a group; per-group and overall balances |
| Pairwise view ("how much does B owe A?") | Additionally maintain `map<pair<user,user>, Paise>` updated per expense, or derive from settle-up |
| Share/ratio split | `ShareSplit : SplitStrategy` |
| Record a settlement payment | An expense of a special kind: the payer pays the receiver 100% (`ExactSplit` with one participant) |
| Undo or edit an expense | Reverse its shares from `net` (store shares in `Expense`, which we do) |
| Notifications when you're added to an expense | Observer |
| Concurrency (many users adding expenses) | Lock per group; `net` updates for one expense must be atomic |
| Simplify debts as a per-group option | Keep raw pairwise debts, and run `settleUp` only when "simplify" is enabled |

---

## 9a.6 Consolidation

### Must remember (module)

1. LLD grades: requirements, modelling, relationships, **extensibility**, code quality, edge cases, concurrency, communication.
2. The 6 steps: **clarify → entities → relationships → diagram → code the core → extend**.
3. Nouns → classes, verbs → methods, fixed sets → enums, **varying behaviour → interfaces (Strategy)**.
4. Don't subclass for data-only differences (Vehicle types).
5. Orchestrator classes coordinate; entities own their rules (`ParkingSpot::canFit`).
6. **Money in integers.** Time as a parameter (or a `Clock` interface) for testability.
7. Name the race (check-then-act) and lock exactly that; mention finer-grained locking for scale.
8. Parking lot: allocation and fee strategies; find+park atomic.
9. LRU (LLD): storage separated from eviction policy; `list::splice`; reads mutate, so no reader lock; sharding.
10. Splitwise: net balances, split strategies, remainder distribution, greedy settle-up (≤ n−1 transactions; the true minimum is NP-hard).

### LLD round checklist (use it in the room)

```
[ ] Asked about actors, core use cases, variants, rules, concurrency, out-of-scope
[ ] Wrote the agreed requirements down
[ ] Listed entities; used enums for fixed sets
[ ] Put interfaces where variation was stated or likely
[ ] Drew the diagram with ownership and multiplicities
[ ] Walked one flow through the diagram before coding
[ ] Coded models -> interfaces -> strategies -> service -> demo
[ ] Validated inputs; handled the full / missing / invalid cases
[ ] Identified shared state and where to lock
[ ] Answered "now add X" by pointing at an interface
```

### Interview Q&A bank

| Question | Crisp answer |
|---|---|
| How do you approach an LLD problem? | Clarify requirements, identify entities, define relationships, draw a class diagram, code the core flows, then discuss extensions, concurrency and edge cases |
| Why not subclass Car/Bike/Truck? | They differ only in data (size requirement); an enum is simpler. Subclass when behaviour differs |
| Where are the concurrency issues in a parking lot? | Two gates assigning the same spot: find+park must be atomic; per-floor locks or CAS for scale |
| Why can't an LRU `get` use a shared lock? | `get` reorders the recency list, so it's a write |
| Why integers for money? | Floating-point rounding errors; exact paise arithmetic with explicit remainder handling |
| How does Splitwise simplify debts? | Net balances, then greedily match the largest debtor with the largest creditor; at most n−1 payments |

### Practice prompts (do at least two under a 45-minute timer)

1. **Library management system:** members, books with multiple copies, borrow/return, a due-date fine, max 5 books per member, reservation queue when all copies are out. *(Hints: `Book` vs `BookCopy` (composition), `FinePolicy` strategy, Observer for "reserved book available".)*
2. **Rate limiter (class-level):** `allow(userId)`, configurable algorithm (fixed window, sliding window, token bucket). *(Hints: `RateLimitStrategy` interface, a per-user state map, a lock per user, time injected for tests.)*
3. **Vending machine:** select item, insert coins/notes, dispense, return change, sold-out handling. *(Hints: the **State** pattern from M8 §8.8, an inventory map, a change-making strategy.)*
4. **Logger library:** levels (DEBUG..ERROR), multiple sinks (console, file), a configurable format, a single global access point. *(Hints: Singleton, Strategy for the format, Observer or a list of sinks, chain of responsibility for levels.)*

---

## Exit checklist

```
[ ] I know what LLD rounds grade, and the two formats (discussion vs machine coding)
[ ] I can run the 6-step method with a time budget
[ ] I can design the Parking Lot from memory: requirements, diagram, core code, 5 extensions
[ ] I can explain the parking-lot race and how to lock it, and how to scale the locking
[ ] I can design the LLD-style LRU cache with a pluggable eviction policy, and explain the locking subtlety
[ ] I can design Splitwise with net balances, three split strategies, integer money and greedy settle-up
[ ] I can explain why minimum-transaction settlement is NP-hard and greedy is used
[ ] I completed two practice prompts under a timer
```

---

## Next

**Part 12: M9b — Low-Level Design: Snake & Ladder, Elevator, BookMyShow.** These are three machine-coding favourites: a turn-based game with a configurable board, an elevator system with a scheduling strategy and a state machine, and a movie-ticket booking system where **concurrent seat booking** is the core challenge (locking, seat holds with expiry, and the double-booking race).
