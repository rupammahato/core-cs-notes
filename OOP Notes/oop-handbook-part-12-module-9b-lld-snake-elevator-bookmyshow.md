# OOP Placement Handbook (C++) — Part 12
# Module 9b: Low-Level Design — Snake & Ladder, Elevator, BookMyShow

**Module 9b · 3–4 hours · Tier 2/3 · Requires: M9a (the method), M8 (Strategy, State, Observer)**

---

## What these three add

M9a taught the method on three classic designs. These three are the favourites of **machine-coding rounds**, and each one tests a different skill:

| Design | The skill it tests |
|---|---|
| **Snake & Ladder** | Clean modelling of a simple domain, **validation**, and **testability** (deterministic dice). The easiest, which is exactly why a sloppy version fails |
| **Elevator** | **State and scheduling**: a stateful object driven by time ticks, plus a **dispatch strategy** across several cars |
| **BookMyShow** | **Concurrency**: two users must never book the same seat. The hardest of the six, and the most frequently asked follow-up in design rounds |

Use the 6-step method from M9a for each: **clarify → entities → relationships → diagram → code → extend**.

All code below compiles under C++17 (`-pthread` for the threads demo) with no warnings, and the outputs shown are from real runs. The BookMyShow concurrency test was run repeatedly, and exactly one thread won the seat every time.

The organising principle:

> **In machine coding, a design is only as good as the questions it can answer: "is this board valid?", "which elevator should come?", "can these two users get the same seat?". Put each such question in exactly one place (a validator, a strategy, a critical section), and the design stays correct when the requirements move.**

---

# Design 4: Snake & Ladder

## 9b.1 Snake & Ladder

### Step 1: Requirements

1. A board of N cells (commonly 100) with **snakes** (head → tail, going down) and **ladders** (bottom → top, going up).
2. 2+ players take turns rolling a die and moving forward by the roll.
3. Landing on a snake head or a ladder bottom moves the player to its other end.
4. **Exact landing:** if a roll would overshoot the last cell, the player stays put.
5. The first player to reach the last cell wins.
6. Configurable: board size, snakes and ladders, number of dice, players.
7. The game must be **testable** with a predictable sequence of rolls.

**Out of scope:** UI, networking, persistence. **Clarify:** do several players share a cell? (Yes, no capture.) Does rolling a 6 give an extra turn? (Treated as an extension.)

### Step 2: Entities

| Noun | Becomes | Note |
|---|---|---|
| Board | `class Board` | Owns the jumps; **validates the configuration** in its constructor |
| Snake, Ladder | **Not classes**: one `unordered_map<int,int> jumps` (start → end) | Both are "land on X, go to Y". Separate classes would add code without behaviour |
| Dice | `interface Dice` → `RandomDice`, `ScriptedDice` | **Strategy + testability**: inject scripted dice in tests |
| Player | `struct Player` (name, position) | |
| Game | `class Game` (turn queue, rules, winner) | The orchestrator |

**Say this out loud:** *"Snakes and ladders behave identically (land on start, move to end), so I model both as jumps in one map, and validate direction separately. Making them two classes with one identical method would be inheritance with no behaviour difference."* Interviewers specifically look for this judgement.

### Step 3–4: Diagram

```
 +-----------------+  1        +---------------------+
 |      Game       |<#>------->|       Board         |
 +-----------------+           +---------------------+
 | - turns : deque |           | - size              |
 | + play() : name |           | - jumps : map<int,int>
 +-----------------+           | + resolve(cell)     |
    <#> 1   <#> 2..*           +---------------------+
     |         |
     v         v
 <<interface>> Dice          Player
 + roll() : int              - name, position
   ^          ^
 RandomDice  ScriptedDice
```

### Step 5: Code

```cpp
struct Dice {
    virtual int roll() = 0;
    virtual ~Dice() = default;
};
class RandomDice : public Dice {
    mt19937 rng;
    uniform_int_distribution<int> dist;
public:
    explicit RandomDice(int faces = 6, unsigned seed = random_device{}()) : rng(seed), dist(1, faces) {}
    int roll() override { return dist(rng); }
};
class ScriptedDice : public Dice {                 // deterministic: for tests and demos
    vector<int> seq; size_t i = 0;
public:
    explicit ScriptedDice(vector<int> s) : seq(std::move(s)) {}
    int roll() override { return seq.at(i++ % seq.size()); }
};

class Board {
    int size;
    unordered_map<int, int> jumps;                 // start -> end (snake: end < start, ladder: end > start)
public:
    Board(int size, const vector<pair<int,int>>& snakes, const vector<pair<int,int>>& ladders) : size(size) {
        auto add = [&](int from, int to) {
            if (from <= 1 || from >= size || to < 1 || to > size) throw invalid_argument("jump out of range");
            if (jumps.count(from)) throw invalid_argument("two jumps start at one cell");
            jumps[from] = to;
        };
        for (auto [head, tail] : snakes)   { if (tail >= head) throw invalid_argument("snake must go down"); add(head, tail); }
        for (auto [bottom, top] : ladders) { if (top <= bottom) throw invalid_argument("ladder must go up"); add(bottom, top); }
        for (auto& [from, to] : jumps)
            if (jumps.count(to)) throw invalid_argument("jump ends on another jump start");   // no chains/cycles
    }
    int getSize() const { return size; }
    int resolve(int cell) const { auto it = jumps.find(cell); return it == jumps.end() ? cell : it->second; }
};

struct Player {
    string name;
    int position = 0;                              // 0 = not yet on the board
};

class Game {
    Board board;
    unique_ptr<Dice> dice;
    deque<Player> turns;
public:
    Game(Board b, unique_ptr<Dice> d, const vector<string>& names) : board(std::move(b)), dice(std::move(d)) {
        if (names.size() < 2) throw invalid_argument("need at least 2 players");
        for (auto& n : names) turns.push_back({n});
    }
    string play(int maxTurns = 10000) {
        for (int t = 0; t < maxTurns; t++) {
            Player p = turns.front(); turns.pop_front();
            int r = dice->roll();
            int target = p.position + r;
            if (target <= board.getSize()) {                       // exact-landing rule: overshoot = stay
                int landed = board.resolve(target);
                cout << p.name << " rolls " << r << ": " << p.position << " -> " << target;
                if (landed != target) cout << (landed > target ? " ladder -> " : " snake -> ") << landed;
                cout << "\n";
                p.position = landed;
            } else {
                cout << p.name << " rolls " << r << ": stays at " << p.position << "\n";
            }
            if (p.position == board.getSize()) return p.name;
            turns.push_back(p);
        }
        throw runtime_error("no winner within turn limit");
    }
};

int main() {
    Board board(20, {{17, 4}, {14, 8}}, {{3, 11}, {6, 15}});
    Game game(board, make_unique<ScriptedDice>(vector<int>{3, 6, 5, 2, 4, 6, 2, 4, 1}), {"Asha", "Ravi"});
    string winner = game.play();
    cout << "Winner: " << winner << "\n";
    try { Board bad(20, {{5, 9}}, {}); } catch (const exception& e) { cout << e.what() << "\n"; }
}
```

**Output:**
```
Asha rolls 3: 0 -> 3 ladder -> 11
Ravi rolls 6: 0 -> 6 ladder -> 15
Asha rolls 5: 11 -> 16
Ravi rolls 2: 15 -> 17 snake -> 4
Asha rolls 4: 16 -> 20
Winner: Asha
snake must go down
```

### Design notes to say out loud

- **Validation in the Board constructor** means an invalid board can never exist: snakes must go down, ladders up, nothing starts on cell 1 or the last cell, no two jumps share a start, and **no jump ends on another jump's start** (that prevents chains and infinite loops such as a ladder 5→9 plus a snake 9→5). This is encapsulation of invariants (M2) applied.
- **`ScriptedDice`** makes the game deterministic. Tests can force "land on a snake" or "overshoot" and assert the result. Injecting randomness through an interface is DIP (M7). `RandomDice` uses `<random>`, not `rand()`.
- **`maxTurns`**: a guard against a configuration where no one can ever win (it can't happen with valid boards and a fair die, but a defensive cap costs nothing).
- **`deque<Player>` as the turn queue**: pop the front, push to the back. Removing a player who finishes (for "play until the last two") is natural.
- A good C++ trap to mention: `cout << "Winner: " << game.play()` would print "Winner:" **after** the whole game log, because `play()` (which prints) is evaluated before the stream output it's part of. Store the result in a variable first.

### Step 6: Extensions

| "Now add..." | Answer |
|---|---|
| Two dice / a different die | `RandomDice(12)` or a `MultiDice` that sums several (the Dice strategy) |
| A 6 gives an extra turn; three 6s in a row cancel the turn | A `TurnRule` strategy, or the logic inside `play()` with a counter; don't push the player to the back on a 6 |
| Play until only one player remains | On win, record the rank and don't re-queue; loop while more than one player remains |
| Special cells (skip a turn, teleport) | Generalise jumps into a `CellEffect` interface: `Jump`, `SkipTurn`, ... (Strategy per cell) |
| Snakes that are "biting" only at night, power-ups | Same `CellEffect` mechanism |
| Undo / replay | Record a `vector<Move>` (Command-style); replay from the log |

---

# Design 5: Elevator system

## 9b.2 Elevator

### Step 1: Requirements

1. A building with **F floors** and **N elevator cars**.
2. **Hall calls:** a person on a floor presses Up or Down, and the system assigns a car.
3. **Car calls:** inside a car, a person presses a destination floor.
4. Each car serves its stops efficiently: continue in the current direction while there are stops ahead, then reverse (the **LOOK** algorithm, the same one used for disk scheduling in OS).
5. The car-assignment rule must be **pluggable** (nearest car, least loaded, energy-saving...).
6. Simulated time: the system advances in **ticks**; a car moves one floor per tick.

**Out of scope:** doors, weight limits, emergency mode, maintenance (all extensions). **Clarify:** do hall calls give a direction? (Yes.) Can a car be busy when assigned? (Yes; choose sensibly.)

### Step 2: Entities

| Noun | Becomes |
|---|---|
| Direction | `enum class Direction { Up, Down, Idle }` |
| Car | `class Elevator`: floor, direction, set of pending stops; `addStop()`, `step()` |
| Assignment rule (varies) | `interface DispatchStrategy` → `NearestSuitable` |
| The system | `class ElevatorController`: owns the cars and the strategy, handles hall and car calls, advances time |

**State pattern or an enum?** An elevator has states (idle, moving up, moving down), so the **State pattern** (M8 §8.8) is a candidate. Here, the behaviour in each state differs by a single sign (+1 or −1 floor) plus the reversal rule, so an **enum is simpler** and just as clear. Say that out loud. Reach for the State pattern when states have genuinely different behaviour, such as adding *DoorsOpen*, *Maintenance* and *Emergency*, where each one accepts or rejects requests differently.

### Step 3–4: Diagram

```
 +---------------------------+  1      <<interface>> DispatchStrategy
 |    ElevatorController     |<#>----> + choose(cars, floor, dir) : Elevator&
 +---------------------------+                ^
 | - floors : int            |                |
 | - mutex                   |          NearestSuitable
 | + pickup(floor, dir) : id |
 | + destination(car, floor) |
 | + tick()                  |
 +---------------------------+
          <#> 1..*
           |
           v
 +---------------------------+
 |        Elevator           |
 +---------------------------+
 | - id, floor               |
 | - dir : Direction         |
 | - stops : set<int>        |
 | + addStop(f)              |
 | + step()     (LOOK)       |
 +---------------------------+
```

### Step 5: Code

```cpp
enum class Direction { Up, Down, Idle };

class Elevator {
    int id, floor = 0;
    Direction dir = Direction::Idle;
    set<int> stops;                                // sorted: next stop above/below in O(log n)
public:
    explicit Elevator(int id) : id(id) {}
    int getId() const { return id; }
    int getFloor() const { return floor; }
    Direction getDir() const { return dir; }

    void addStop(int f) {
        if (f == floor && dir == Direction::Idle) { cout << "E" << id << " opens at " << f << "\n"; return; }
        stops.insert(f);
        if (dir == Direction::Idle) dir = (f > floor) ? Direction::Up : Direction::Down;
    }

    void step() {                                  // one tick = one floor; LOOK scheduling
        if (dir == Direction::Idle) return;
        floor += (dir == Direction::Up) ? 1 : -1;
        if (stops.erase(floor)) cout << "E" << id << " stops at " << floor << "\n";
        bool above = stops.upper_bound(floor) != stops.end();
        bool below = !stops.empty() && *stops.begin() < floor;
        if (dir == Direction::Up && !above)        dir = below ? Direction::Down : Direction::Idle;
        else if (dir == Direction::Down && !below) dir = above ? Direction::Up   : Direction::Idle;
    }
};

struct DispatchStrategy {
    virtual Elevator& choose(vector<Elevator>& cars, int floor, Direction want) = 0;
    virtual ~DispatchStrategy() = default;
};
struct NearestSuitable : DispatchStrategy {
    Elevator& choose(vector<Elevator>& cars, int floor, Direction want) override {
        auto cost = [&](const Elevator& e) {
            int d = abs(e.getFloor() - floor);
            if (e.getDir() == Direction::Idle) return d;
            bool onTheWay = (e.getDir() == Direction::Up   && want == Direction::Up   && e.getFloor() <= floor) ||
                            (e.getDir() == Direction::Down && want == Direction::Down && e.getFloor() >= floor);
            return onTheWay ? d : d + 1000;        // penalise cars that must turn around first
        };
        return *min_element(cars.begin(), cars.end(),
                            [&](const Elevator& a, const Elevator& b) { return cost(a) < cost(b); });
    }
};

class ElevatorController {
    vector<Elevator> cars;
    unique_ptr<DispatchStrategy> strategy;
    int floors;
    mutex mtx;
public:
    ElevatorController(int numCars, int floors, unique_ptr<DispatchStrategy> s) : strategy(std::move(s)), floors(floors) {
        for (int i = 0; i < numCars; i++) cars.emplace_back(i);
    }
    int pickup(int floor, Direction want) {        // hall button
        lock_guard<mutex> g(mtx);
        if (floor < 0 || floor >= floors) throw invalid_argument("bad floor");
        Elevator& e = strategy->choose(cars, floor, want);
        e.addStop(floor);
        return e.getId();
    }
    void destination(int carId, int floor) {       // button inside the car
        lock_guard<mutex> g(mtx);
        if (floor < 0 || floor >= floors) throw invalid_argument("bad floor");
        cars.at(carId).addStop(floor);
    }
    void tick() { lock_guard<mutex> g(mtx); for (auto& e : cars) e.step(); }
};

int main() {
    ElevatorController ctl(2, 10, make_unique<NearestSuitable>());
    cout << "pickup(5,Down) -> E" << ctl.pickup(5, Direction::Down) << "\n";
    for (int i = 0; i < 2; i++) ctl.tick();
    cout << "pickup(1,Up) -> E" << ctl.pickup(1, Direction::Up) << "\n";
    for (int i = 0; i < 3; i++) ctl.tick();
    ctl.destination(0, 2);
    ctl.destination(1, 8);
    for (int i = 0; i < 8; i++) ctl.tick();
}
```

**Output and trace:**
```
pickup(5,Down) -> E0        both idle at floor 0 (tie) -> E0; heads up to 5
pickup(1,Up) -> E1          E0 is at 2 going Up: floor 1 is behind it (+1000). E1 is idle at 0, distance 1 -> E1
E1 stops at 1               tick 3
E0 stops at 5               tick 5; no stops remain -> E0 idle
E0 stops at 2               the rider in E0 pressed 2: E0 goes down 5 -> 2
E1 stops at 8               the rider in E1 pressed 8: E1 goes up 1 -> 8
```

### Design notes to say out loud

- **`set<int>` of stops + LOOK:** a sorted set answers "any stop above me?" with `upper_bound` and "any below?" with `begin()`, both in O(log n). The car keeps its direction while stops remain ahead, then reverses. It's the same algorithm as LOOK disk scheduling in OS. **Why not FIFO order?** Serving requests in arrival order makes the car zig-zag, which wastes travel and starves passengers mid-route.
- **Dispatch as a Strategy:** "nearest suitable" is one policy. Others: least-loaded car, zoning (cars 0–1 serve floors 0–20), and energy-saving (prefer cars already moving). Each is a new class (OCP).
- **The cost function** treats an idle car as its distance, a car already moving toward the caller in the right direction as its distance, and anything else as heavily penalised. It's simple, explainable, and easy to swap.
- **Concurrency:** hall buttons, car buttons and the ticking clock run on different threads in a real system. One controller mutex is the simple correct answer; per-car locks are the refinement (dispatch then needs a consistent snapshot of all cars).
- **Simplification to admit:** this model doesn't record the *direction* of a hall call at the stop, so a car going up will also stop for someone at that floor who wants to go down. Production systems keep separate up-calls and down-calls per floor, and a car serves only the calls matching its direction. Mention it as the first refinement.

### Step 6: Extensions

| "Now add..." | Answer |
|---|---|
| Separate up/down hall calls | `set<int> upCalls, downCalls` plus car destinations; a car stops for a hall call only in that call's direction |
| Capacity / weight limit | `Elevator::load`; dispatch skips full cars; a door state that refuses boarding |
| Doors, maintenance, emergency mode | Now the **State pattern** earns its place: `Idle`, `Moving`, `DoorsOpen`, `Maintenance`, each handling `addStop`/`step` differently |
| Display panels per floor | Observer: cars notify displays of floor and direction changes |
| VIP / express elevators | A dispatch strategy that reserves cars, or zoning |
| Minimise average waiting time | Smarter dispatch (estimated time of arrival including queued stops); a pure strategy swap |

---

# Design 6: BookMyShow (movie ticket booking)

## 9b.3 BookMyShow

The most important design in this module. It is really a **concurrency question disguised as an LLD question**: everything else (movies, cinemas, search) is routine modelling.

### Step 1: Requirements

1. **Catalogue:** cities → cinemas → screens; movies; **shows** (a movie on a screen at a time).
2. Each screen has a **seat layout** with seat types (Regular, Premium); price depends on seat type (and possibly the show).
3. **Booking flow:** a user picks seats for a show → the seats are **held** for a few minutes while the user pays → on payment success the hold is **confirmed** into a booking; on failure or timeout, the seats are **released**.
4. **No double booking:** two users must never both get the same seat, even when clicking at the same moment.
5. **All-or-nothing:** if a user asks for 3 seats and any one is taken, they get none (no partial holds).
6. Concurrency: thousands of users on popular shows.

**Out of scope:** search UI, real payment integration, refunds, notifications (extensions). **Clarify:** hold duration? (5 minutes.) Can a user hold seats in two shows at once? (Allowed here.)

### Step 2: Entities

| Noun | Becomes | Note |
|---|---|---|
| City, Cinema, Screen, Movie | Plain data classes | Routine; skip in code, show in the diagram |
| Seat | `struct Seat { id, type }` | Physical seat in the layout |
| Seat status **per show** | `struct SeatState { status, holdId, holdExpiry }` | Seat A1 can be booked for the 6 pm show and free for the 9 pm one, so status belongs to the **show**, not the seat |
| Show | `class Show`: layout + seat states + **its own mutex** | The unit of locking |
| Price (varies) | `interface PricingStrategy` → `FlatByType` | Weekend, surge and dynamic pricing later |
| Hold, Booking | `struct Hold`, `struct Booking` | Hold = temporary claim; Booking = confirmed |
| Orchestrator | `class BookingService`: hold, confirm, release | |

**The modelling insight to state explicitly:** *"Seat availability is a property of (show, seat), not of the seat."* Getting this wrong (a `bool isBooked` on `Seat`) is the most common modelling error in this question.

### Step 3–4: Diagram

```
 City 1 <#>-- 1..* Cinema 1 <#>-- 1..* Screen 1 <#>-- 1..* Seat
                                         ^ 1
                                         |
 Movie 1 <------------------- 0..* +-----------+
                                   |   Show    |  - seat states : map<seatId, SeatState>
                                   +-----------+  - mutex  (one per show)
                                   | tryHold() |  + confirm(), release()
                                   +-----------+
                                         ^ 1..*
                                         |
 +-------------------------+             |      <<interface>> PricingStrategy
 |     BookingService      |-------------+      + price(seat) : Paise
 +-------------------------+ <#> 1 ---------->          ^
 | - holds : map<id, Hold> |                       FlatByType
 | + hold(user, show, seats, now) : optional<Hold>
 | + confirm(holdId, paid, now) : optional<Booking>
 +-------------------------+

 Seat state machine (per show):

      tryHold (all seats free)           confirm (hold valid & paid)
   FREE ----------------------> HELD -----------------------------> BOOKED
     ^                            |
     +----------------------------+
      release (payment failed)  OR  hold expired (lazy check on next access)
```

### Step 5: Code

```cpp
using Paise = long long;
enum class SeatType { Regular, Premium };
enum class SeatStatus { Free, Held, Booked };

struct Seat { string id; SeatType type; };

struct SeatState {
    SeatStatus status = SeatStatus::Free;
    string holdId;
    long long holdExpiry = 0;                      // seconds
};

struct PricingStrategy {
    virtual Paise price(const Seat& s) const = 0;
    virtual ~PricingStrategy() = default;
};
struct FlatByType : PricingStrategy {
    Paise price(const Seat& s) const override { return s.type == SeatType::Premium ? 35000 : 20000; }
};

class Show {
public:
    const string id, movie;
    Show(string id, string movie, vector<Seat> seats) : id(std::move(id)), movie(std::move(movie)) {
        for (auto& s : seats) { layout[s.id] = s; state[s.id]; }
    }
    // all-or-nothing hold of several seats; the whole check+mark is one critical section
    bool tryHold(const vector<string>& seatIds, const string& holdId, long long now, long long ttl) {
        lock_guard<mutex> g(mtx);
        for (auto& sid : seatIds) {
            auto it = state.find(sid);
            if (it == state.end()) throw invalid_argument("no seat " + sid);
            expireIfStale(it->second, now);
            if (it->second.status != SeatStatus::Free) return false;       // nothing modified yet
        }
        for (auto& sid : seatIds) state[sid] = {SeatStatus::Held, holdId, now + ttl};
        return true;
    }
    bool confirm(const vector<string>& seatIds, const string& holdId, long long now) {
        lock_guard<mutex> g(mtx);
        for (auto& sid : seatIds) {
            auto& st = state.at(sid);
            expireIfStale(st, now);
            if (st.status != SeatStatus::Held || st.holdId != holdId) return false;   // hold lost
        }
        for (auto& sid : seatIds) state[sid] = {SeatStatus::Booked, holdId, 0};
        return true;
    }
    void release(const vector<string>& seatIds, const string& holdId) {
        lock_guard<mutex> g(mtx);
        for (auto& sid : seatIds) {
            auto& st = state.at(sid);
            if (st.status == SeatStatus::Held && st.holdId == holdId) st = SeatState{};
        }
    }
    const Seat& seat(const string& sid) const { return layout.at(sid); }
    int countFree(long long now) {
        lock_guard<mutex> g(mtx);
        int c = 0;
        for (auto& [sid, st] : state) { expireIfStale(st, now); c += st.status == SeatStatus::Free; }
        return c;
    }
private:
    unordered_map<string, Seat> layout;
    unordered_map<string, SeatState> state;
    mutex mtx;                                     // one lock PER SHOW: different shows never contend
    static void expireIfStale(SeatState& st, long long now) {
        if (st.status == SeatStatus::Held && now >= st.holdExpiry) st = SeatState{};   // lazy expiry
    }
};

struct Hold    { string id, user, showId; vector<string> seats; Paise amount; };
struct Booking { string id, user, showId; vector<string> seats; Paise amount; };

class BookingService {
    unordered_map<string, unique_ptr<Show>> shows;
    unique_ptr<PricingStrategy> pricing;
    unordered_map<string, Hold> holds;
    mutex holdsMtx;                                // protects holds and the id counter
    long long nextId = 1;
    static constexpr long long HOLD_TTL = 300;     // 5 minutes to pay
public:
    explicit BookingService(unique_ptr<PricingStrategy> p) : pricing(std::move(p)) {}
    void addShow(unique_ptr<Show> s) { string id = s->id; shows[id] = std::move(s); }

    optional<Hold> hold(const string& user, const string& showId, const vector<string>& seats, long long now) {
        if (seats.empty()) throw invalid_argument("no seats");
        Show& show = *shows.at(showId);
        string hid;
        { lock_guard<mutex> g(holdsMtx); hid = "H" + to_string(nextId++); }
        if (!show.tryHold(seats, hid, now, HOLD_TTL)) return nullopt;
        Paise amt = 0;
        for (auto& s : seats) amt += pricing->price(show.seat(s));
        Hold h{hid, user, showId, seats, amt};
        lock_guard<mutex> g(holdsMtx);
        holds[hid] = h;
        return h;
    }
    optional<Booking> confirm(const string& holdId, bool paymentOk, long long now) {
        Hold h;
        { lock_guard<mutex> g(holdsMtx);
          auto it = holds.find(holdId);
          if (it == holds.end()) return nullopt;
          h = it->second; holds.erase(it); }
        Show& show = *shows.at(h.showId);
        if (!paymentOk) { show.release(h.seats, h.id); return nullopt; }
        if (!show.confirm(h.seats, h.id, now)) return nullopt;   // hold expired: refund in real life
        return Booking{"B" + h.id.substr(1), h.user, h.showId, h.seats, h.amount};
    }
    Show& getShow(const string& id) { return *shows.at(id); }
};
```

**Demo:**

```cpp
int main() {
    BookingService svc(make_unique<FlatByType>());
    svc.addShow(make_unique<Show>("S1", "Dune", vector<Seat>{
        {"A1", SeatType::Regular}, {"A2", SeatType::Regular}, {"P1", SeatType::Premium}}));

    auto h1 = svc.hold("asha", "S1", {"A1", "P1"}, 0);
    auto h2 = svc.hold("ravi", "S1", {"P1", "A2"}, 10);    // P1 is held -> fails; A2 NOT held (all-or-nothing)
    cout << (h1 ? "asha held " + to_string(h1->amount) : "asha failed") << " | "
         << (h2 ? "ravi held" : "ravi failed") << "\n";
    cout << "free now: " << svc.getShow("S1").countFree(10) << "\n";

    auto late = svc.hold("ravi", "S1", {"P1"}, 400);       // asha's hold expired at t=300
    cout << (late ? "ravi got P1 after expiry" : "ravi failed") << "\n";
    auto b1 = svc.confirm(h1->id, true, 401);              // asha pays too late
    cout << (b1 ? "asha booked" : "asha's hold lost") << "\n";
    auto b2 = svc.confirm(late->id, true, 402);
    cout << (b2 ? "ravi booked " + b2->id + " for " + to_string(b2->amount) : "ravi failed") << "\n";

    // concurrency proof: 16 threads race for the same seat; exactly one may win
    svc.addShow(make_unique<Show>("S2", "Dune", vector<Seat>{{"X1", SeatType::Regular}}));
    atomic<int> wins{0};
    vector<thread> ts;
    for (int i = 0; i < 16; i++)
        ts.emplace_back([&, i] { if (svc.hold("u" + to_string(i), "S2", {"X1"}, 0)) wins++; });
    for (auto& t : ts) t.join();
    cout << "concurrent winners: " << wins << "\n";
}
```

**Output** (the last line was identical over repeated runs):
```
asha held 55000 | ravi failed
free now: 1
ravi got P1 after expiry
asha's hold lost
ravi booked B3 for 35000
concurrent winners: 1
```

(`B3` is the booking for hold `H3`: hold IDs are allocated even for failed attempts, so ravi's failed attempt used `H2`.)

### 9b.4 The concurrency discussion (where this round is won)

**1. The race, stated precisely.** Booking is **check-then-act**: "is seat P1 free? → yes → mark it held". If two threads both run the check before either acts, both see "free" and both mark it, and you have a **double booking**. The check and the act must be **one atomic step**.

```
   Thread A (asha)                 Thread B (ravi)
   reads P1: Free
                                   reads P1: Free         <- both pass the check
   writes P1: Held by A
                                   writes P1: Held by B   <- overwrites A: DOUBLE BOOKING
```

**2. The fix in this design.** `Show::tryHold` checks **all** requested seats and marks them **under one `lock_guard`**. No other thread can observe or change that show's seats in between. The 16-thread test shows exactly one winner.

**3. Why a lock per show, not one global lock.** Bookings for *different* shows never conflict, so they shouldn't wait for each other. Per-show locking gives full parallelism across shows and serialises only the contention that's real. (Finer still: per-seat locks, but then a multi-seat hold must take several locks, and it must take them **in a fixed order** (for example sorted seat IDs) to avoid deadlock. That's the classic lock-ordering rule from OS deadlock prevention.)

**4. All-or-nothing.** The first loop only **checks**; the second loop **writes**. If any seat fails the check, the function returns before modifying anything, so there's no partial hold to roll back.

**5. Holds with expiry (TTL).** A user who abandons the payment page mustn't block seats forever. Each hold records `holdExpiry`, and `expireIfStale()` frees stale holds **lazily**, whenever the seat is next touched. A background sweeper thread is the alternative (it frees seats promptly for the availability display). `confirm` **re-checks the hold under the lock**, so a payment that arrives after expiry, when someone else may already hold the seat, can't steal it back (asha's case above). In real life, that payment is then refunded.

**6. In a real system (say this, briefly).** The in-memory mutex works only within one process. With several app servers, the atomic check-and-set moves to shared storage:
- **Database:** a transaction with row locks (`SELECT ... FOR UPDATE` on the show's seat rows), or **optimistic locking**: `UPDATE show_seat SET status='HELD', hold_id=?, version=version+1 WHERE show_id=? AND seat_id=? AND status='FREE' AND version=?`, then check that the affected-row count matches.
- A **unique constraint** on (show_id, seat_id) in the bookings table as the last line of defence: a second insert simply fails.
- **Redis** `SET key value NX EX 300` per seat as a distributed lock with a built-in TTL. That maps directly onto the hold-with-expiry design above.

Mentioning **optimistic vs pessimistic locking** with one sentence each is usually enough at SDE-1 level:

| | Pessimistic | Optimistic |
|---|---|---|
| Idea | Lock first, then read and modify | Read freely; at write time, verify nothing changed (version check); retry on conflict |
| Best when | Contention is high (a blockbuster's opening night) | Contention is low (most shows) |
| Cost | Waiting and lock overhead | Retries under contention |

### Step 6: Extensions

| "Now add..." | Answer |
|---|---|
| Dynamic / weekend / surge pricing | New `PricingStrategy` classes (could also take the show, time and occupancy) |
| Payment methods | `PaymentGateway` interface + Adapter for each provider (M8 §8.7) |
| Notify waitlisted users when seats free up | Observer on seat release/expiry |
| Search by city/movie/date | Indexes: `map<city, vector<Show*>>`, `map<movie, ...>`; HLD would add a search service |
| Booking cancellation + refund | `Booking::status` state machine (Confirmed → Cancelled); release the seats back to Free under the show lock |
| Offers / coupons | Decorator around the pricing strategy, or a separate `DiscountStrategy` |
| Prevent one user from hoarding seats | Limit active holds per user (count in `holds` per user) and maximum seats per hold |

---

## 9b.5 Consolidation

### Must remember (module)

1. **Snake & Ladder:** snakes and ladders are one `jumps` map (same behaviour, so no classes). Validate the board in its constructor (direction, range, no shared starts, no chained jumps). Inject `Dice` for deterministic tests. The exact-landing rule.
2. **Elevator:** a car holds a sorted `set<int>` of stops and runs LOOK (keep direction while stops lie ahead). Dispatch is a Strategy with a cost function. An enum is enough until states behave differently, then the State pattern.
3. **BookMyShow:** availability belongs to (show, seat). The hold → confirm → release state machine. Holds have a TTL with lazy expiry. **Check and mark under one lock** (no check-then-act race). Lock per show. All-or-nothing by checking everything before writing anything. `confirm` re-validates the hold.
4. Multi-seat locking at seat granularity requires a **fixed lock order** to avoid deadlock.
5. Across servers: DB row locks, optimistic version checks, unique constraints, or Redis `SET NX EX`.
6. A general C++ point: `cout << x << f()` where `f()` prints can interleave unexpectedly. Evaluate first, then print.

### Common mistakes (module)

- `Snake` and `Ladder` classes with identical behaviour; no board validation.
- Using `rand()` and no way to test deterministically.
- An elevator serving requests in FIFO order; no dispatch abstraction.
- `bool isBooked` on `Seat` (availability is per show).
- Checking availability and then booking in two separate locked sections (still a race).
- Partial holds (some seats held when others failed).
- Holds that never expire.
- One global lock for every show without acknowledging the bottleneck.

### Interview Q&A bank

| Question | Crisp answer |
|---|---|
| Why not separate Snake and Ladder classes? | Identical behaviour (land on start → move to end); one jumps map plus direction validation |
| How do you test a dice game? | Inject a `Dice` interface; use scripted dice in tests |
| What scheduling does an elevator use? | LOOK/SCAN: continue in the current direction while requests lie ahead, then reverse; it avoids zig-zagging and starvation |
| How do you pick which elevator answers? | A dispatch strategy with a cost function (distance, direction, load); swappable |
| How do you prevent double booking? | Make check-and-hold atomic: one critical section per show (in memory), or row locks / optimistic version checks / unique constraints in the DB |
| What if the user never pays? | Holds carry an expiry; expired holds are freed lazily or by a sweeper; confirm re-checks the hold |
| Optimistic vs pessimistic locking? | Verify-at-write with a version + retry vs lock-before-read; optimistic for low contention, pessimistic for hot shows |
| How do you avoid deadlock when locking several seats? | Acquire the locks in a global fixed order (sorted seat IDs) |

### Practice prompts (timed, 45–90 minutes each)

1. **Tic-tac-toe / N×N board game:** players, board, a win check in O(1) per move (row/column/diagonal counters), extensible to N-in-a-row.
2. **Food-delivery order lifecycle:** Placed → Accepted → Preparing → PickedUp → Delivered/Cancelled with allowed transitions (State pattern), and a delivery-partner assignment strategy.
3. **Meeting room booking:** rooms with capacity, book [start, end) intervals, no overlaps (interval checks from DSA Part 13, using `map::lower_bound`), concurrent requests (lock per room).
4. **Cab booking (Uber-lite):** riders, drivers with locations and states, a matching strategy (nearest available), and fare strategies (base + per-km + surge). It reuses ideas from the Elevator design (dispatch) and BookMyShow (one driver can't accept two rides: an atomic state change).

---

## Exit checklist

```
[ ] I can design Snake & Ladder with board validation and injectable dice
[ ] I can explain why snakes and ladders don't need separate classes
[ ] I can design the elevator with LOOK scheduling and a dispatch strategy
[ ] I can explain when an enum is enough and when the State pattern earns its place
[ ] I can model BookMyShow with per-show seat state and the hold/confirm/release lifecycle
[ ] I can explain the double-booking race and fix it with one critical section per show
[ ] I can explain hold expiry and why confirm re-validates
[ ] I can describe DB-level solutions: row locks, optimistic locking, unique constraints, Redis NX EX
[ ] I completed at least two practice prompts under a timer
```

---

## Next

**Part 13: Consolidation.** The final part of the OOP handbook: one-page cheat sheets, the confusable-pairs master table, a drill bank of 30 output-prediction snippets (all verified by compiling), and rapid-fire Q&A covering the whole handbook for the final days before interviews.
