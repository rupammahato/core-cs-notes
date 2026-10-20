# Machine Coding Practice — Part 8: Meeting Room Booking

**M6: preserve the old booking until a replacement is known to be valid.**

## 1. The problem and its purpose

Allocate rooms to meetings, cancel bookings and reschedule existing bookings. This is an interval-allocation problem with a domain invariant: no two active bookings may overlap in the same room. It tests validation, deterministic policy and failure-safe updates.

Clarify time representation, endpoints, capacity, room choice, duplicate IDs and move semantics. Here times are integers from 0 to 10^12 in one shared unit. There are no time zones or recurring meetings. Intervals are half-open [start, end), so adjacent meetings are allowed. Choose the smallest-capacity fitting room, breaking ties lexicographically by room ID.

## 2. Fixture, API and invariants

Rooms are A with capacity 2, B with capacity 4 and C with capacity 4. Every booking has an immutable external ID, assigned room, start, end and attendee count. A move can change time, attendees and assigned room.

| Command | Behavior |
| --- | --- |
| BOOK id start end people | Reject duplicate ID; allocate best available room |
| MOVE id start end people | Require existing ID; choose before replacing old booking |
| CANCEL id | Remove if present and return whether it existed |
| STATE | Full active booking records for inspection |

Require start < end and positive attendees <=1,000,000. Two intervals overlap exactly when start1 < end2 and start2 < end1. Capacity must cover attendees. Booking IDs are unique and nonempty. Rejected operations leave the booking map unchanged.

## 3. The important update sequence

For each room, inspect overlapping bookings except the booking being moved. Gather candidates and choose minimum (capacity, room ID). Only after finding one, replace the old booking.

Deleting first is a common mistake: if no replacement exists, the caller loses a valid reservation. Ignoring the current booking while checking a move is equally important; otherwise a move within its own old interval can conflict with itself.

The service serializes calls simply by being single-threaded. “Check then write” is safe only within that scope. Independent concurrent callers need a shared enforcement mechanism.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
class RoomBooking {
    struct Booking { std::string room; Number start, end, people; };
    const std::map<std::string, Number> rooms_{{"A", 2}, {"B", 4}, {"C", 4}};
    std::map<std::string, Booking> bookings_;
    std::string choose(Number start, Number end, Number people, const std::string& ignore) const {
        timeValue(start); timeValue(end); require(start < end, "invalid interval");
        require(people > 0 && people <= 1000000, "invalid attendees");
        std::vector<std::pair<Number, std::string>> choices;
        for (const auto& [room, capacity] : rooms_) {
            bool free = capacity >= people;
            for (const auto& [id, b] : bookings_)
                if (id != ignore && b.room == room && start < b.end && b.start < end) free = false;
            if (free) choices.push_back({capacity, room});
        }
        require(!choices.empty(), "no room"); return std::min_element(choices.begin(), choices.end())->second;
    }
public:
    std::string book(const std::string& id, Number start, Number end, Number people) {
        identifier(id); require(bookings_.count(id) == 0, "duplicate booking");
        auto room = choose(start, end, people, ""); bookings_[id] = {room, start, end, people}; return room;
    }
    std::string move(const std::string& id, Number start, Number end, Number people) {
        identifier(id); require(bookings_.count(id) != 0, "unknown booking");
        auto room = choose(start, end, people, id); bookings_[id] = {room, start, end, people}; return room;
    }
    bool cancel(const std::string& id) { identifier(id); return bookings_.erase(id) != 0; }
    std::string state() const {
        std::string out = "{";
        for (const auto& [id, b] : bookings_) {
            if (out.size() > 1) out += ',';
            out += json(id) + ":[" + json(b.room) + ',' + json(b.start) + ',' + json(b.end) + ',' + json(b.people) + ']';
        }
        return out + '}';
    }
};
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T21. Adjacent meetings share a room

**Worked explanation:** Intervals are half-open. A meeting ending at 20 does not overlap one starting at 20, and best fit chooses room A for both.

Run `python examples/machine-coding/verify.py --trace T21` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
BOOK first 10 20 2
{"ok":true,"result":"A"}
BOOK next 20 30 2
{"ok":true,"result":"A"}
BOOK overlap 19 21 2
{"ok":true,"result":"B"}
STATE
{"ok":true,"result":{"first":["A",10,20,2],"next":["A",20,30,2],"overlap":["B",19,21,2]}}
```

**Common trap:** Using <= for both overlap comparisons rejects adjacency.

**Interview follow-up:** Where would a cleanup buffer enter the interval model?

### T22. Best fit has a deterministic tie break

**Worked explanation:** Rooms B and C both fit four attendees. Lexicographic room ID breaks equal capacities; the third overlapping request has no room.

Run `python examples/machine-coding/verify.py --trace T22` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
BOOK x 0 10 4
{"ok":true,"result":"B"}
BOOK y 0 10 4
{"ok":true,"result":"C"}
BOOK z 0 10 4
{"ok":false,"error":"no room"}
CANCEL x
{"ok":true,"result":true}
BOOK z 0 10 4
{"ok":true,"result":"B"}
```

**Common trap:** Iterating an unordered container makes allocation order unstable.

**Interview follow-up:** How might fairness change the allocator policy?

### T23. A failed move preserves the original reservation

**Worked explanation:** The candidate is chosen before the existing booking is replaced. Moving x into a fully occupied four-person interval fails without freeing its old slot.

Run `python examples/machine-coding/verify.py --trace T23` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
BOOK x 0 10 4
{"ok":true,"result":"B"}
BOOK y 10 20 4
{"ok":true,"result":"B"}
BOOK z 10 20 4
{"ok":true,"result":"C"}
MOVE x 10 20 4
{"ok":false,"error":"no room"}
STATE
{"ok":true,"result":{"x":["B",0,10,4],"y":["B",10,20,4],"z":["C",10,20,4]}}
```

**Common trap:** Delete-then-book loses the original reservation on failure.

**Interview follow-up:** Which database constraint can protect concurrent interval allocation?

### T24. A move ignores its own old interval

**Worked explanation:** Rescheduling x over its current interval is valid because its own occupancy is excluded. Bad intervals and duplicate IDs are rejected.

Run `python examples/machine-coding/verify.py --trace T24` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
BOOK x 0 10 2
{"ok":true,"result":"A"}
MOVE x 2 8 2
{"ok":true,"result":"A"}
BOOK x 30 40 2
{"ok":false,"error":"duplicate booking"}
MOVE x 8 8 2
{"ok":false,"error":"invalid interval"}
STATE
{"ok":true,"result":{"x":["A",2,8,2]}}
```

**Common trap:** Treating the booking being moved as a conflict rejects harmless updates.

**Interview follow-up:** Would an idempotent booking endpoint accept an identical duplicate?

<!-- END TRACES -->

## 6. Complexity and alternative indexes

With R rooms and B bookings, candidate discovery scans all bookings for each room: O(RB). Choosing the minimum candidate is O(R); ordered-map insertion or replacement adds O(log B). Cancellation is O(log B). The state uses O(R+B) storage, plus at most O(R) temporary candidates.

For many bookings, index intervals per room. An ordered start-time map can inspect relevant neighbors when the nonoverlap invariant is already maintained, while more general interval queries may need an interval index. Explain which query the index accelerates before naming a data structure.

The random oracle uses small integer intervals and compares occupied time slots, giving an independent way to catch overlap mistakes. That oracle does not justify iterating every real timestamp in a production implementation.

## 7. Architecture follow-up

A database-backed implementation should enforce availability under concurrent writes, not merely check it in application code. Options depend on the chosen database: transactions with appropriate locking, serializable operations with retries, or interval exclusion constraints where supported. All competing writers must participate in the same rule.

Idempotent creation also needs a request identity: the same booking ID with an identical payload could be accepted as a retry, while a conflicting payload should not silently overwrite it. This exercise instead rejects every duplicate BOOK; explain that choice accurately.

Bridge to [booking and reservations](/docs/system-design/booking-reservations). Room allocation is a different model from the existing [BookMyShow seat example](/docs/oop/lld-snake-elevator-bookmyshow), so reuse reasoning rather than copying seat-count assumptions.

## 8. Interview questions with answers

### Q1. Why are intervals half-open?

They represent occupancy through the start of end time, allowing a meeting ending at 20 and another starting at 20 to share a room. A cleanup buffer would extend the reserved interval explicitly.

### Q2. Why choose best fit?

It is the agreed deterministic policy and tends to preserve larger rooms for larger groups. It is not a proof of globally optimal future allocation; other fairness or utilization goals can choose differently.

### Q3. What happens when a move fails?

The original booking remains exactly intact. The method computes a valid candidate before assigning a replacement, so no rollback reconstruction is needed for a no-room rejection.

### Q4. Why ignore the current booking during a move?

It is being replaced, not added alongside itself. Counting its old interval as another booking would incorrectly reject overlapping changes to the same meeting.

### Q5. Is checking capacity enough?

No. A fitting room may already be occupied. Both capacity and interval availability must hold, and concurrency can invalidate a check unless the subsequent write is protected.

### Q6. Can a mutex solve booking conflicts?

One mutex can serialize calls in one process if every relevant access uses it. It does not coordinate other processes or database writers. State the ownership boundary before making a safety claim.

### Q7. What changes for recurring meetings?

Define recurrence, time zone, daylight-saving behavior, exceptions and whether allocation is all-or-nothing across occurrences. Expanding a finite horizon is one implementation choice, not a complete recurrence contract.

### Q8. Why use a tie break in the allocator?

It makes responses reproducible, tests stable and behavior explainable. Dependence on incidental hash iteration order can change a user's assigned room across runs.

## 9. Practice tasks

- [ ] Add a cleanup buffer and test adjacency with and without it. Store the business meeting interval separately if display requirements need it.
- [ ] Make identical BOOK retries idempotent. Reject a conflicting payload for the same ID and test both outcomes.
- [ ] Add a per-room ordered interval index. Compare with the existing slot oracle before claiming equivalent behavior.
- [ ] Specify an all-or-nothing recurring booking API. Explain which conflicts abort the series and what is retained on failure.

Next: [In-Memory Document Search](/docs/machine-coding/in-memory-document-search).
