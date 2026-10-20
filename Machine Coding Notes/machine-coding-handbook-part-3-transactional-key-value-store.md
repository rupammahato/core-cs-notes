# Machine Coding Practice — Part 3: Transactional Key-Value Store

**M1: preserve state correctly before optimizing transaction storage.**

## 1. The problem and its purpose

Build an in-memory string key-value store with SET, GET, ERASE and nested BEGIN, COMMIT and ROLLBACK. This exercise tests whether you can turn ambiguous transaction language into precise state transitions. It is a useful bridge from a map implementation to database reasoning.

Ask what an inner commit means, whether reads see uncommitted writes, how missing keys differ from empty values, and what happens without an active transaction. Here every call belongs to one serial session. Reads see current writes. An inner commit remains inside its parent; an outer rollback can undo it. There is no persistence, isolation between clients, or database connection.

## 2. Contract and invariants

| Operation | Agreed result |
| --- | --- |
| SET key value | Insert or replace; empty values allowed, empty keys rejected |
| GET key | Optional string: missing is null, present empty is an empty string |
| ERASE key | True if a mapping existed; false otherwise |
| BEGIN | Push a complete snapshot of the current map |
| COMMIT | Discard the most recent snapshot; current data stays |
| ROLLBACK | Restore and remove the most recent snapshot |
| STATE | Diagnostic data and transaction depth; not a production transaction API |

The map is the current visible state. Each stack frame is the state immediately before its corresponding BEGIN. Only the top frame closes on COMMIT or ROLLBACK. A rejected COMMIT/ROLLBACK leaves both map and stack unchanged.

## 3. Build it in this order

First implement a map with optional reads. Then add BEGIN as a copy into a stack. COMMIT removes a snapshot; it does not copy the current map back into the parent snapshot. ROLLBACK swaps the current map with the top snapshot and removes that frame.

The subtle point is the meaning of the parent frame. It describes the beginning of the outer transaction, not the latest committed child. Overwriting it on an inner commit makes outer rollback incorrect.

Consider describing the stack aloud before writing the code: “My undo point belongs to the transaction being opened.” This gives a simple correctness argument for any nesting depth, rather than relying on one successful example.

## 4. Complete model implementation

The listing is copied exactly from the compiled `TransactionalKV` class. Shared includes and validation helpers appear in [the harness chapter](/docs/machine-coding/solving-method-and-test-harness). The command adapter is `examples/machine-coding/main.cpp`.

<!-- BEGIN MODEL -->

```cpp
class TransactionalKV {
    std::map<std::string, std::string> data_;
    std::vector<std::map<std::string, std::string>> snapshots_;
public:
    void set(const std::string& key, const std::string& value) { identifier(key); data_[key] = value; }
    std::optional<std::string> get(const std::string& key) const {
        identifier(key); auto it = data_.find(key);
        return it == data_.end() ? std::nullopt : std::optional<std::string>(it->second);
    }
    bool erase(const std::string& key) { identifier(key); return data_.erase(key) != 0; }
    void begin() { snapshots_.push_back(data_); }
    void commit() { require(!snapshots_.empty(), "no transaction"); snapshots_.pop_back(); }
    void rollback() {
        require(!snapshots_.empty(), "no transaction");
        data_.swap(snapshots_.back()); snapshots_.pop_back();
    }
    const auto& data() const { return data_; }
    Number depth() const { return static_cast<Number>(snapshots_.size()); }
};
```

<!-- END MODEL -->

## 5. Worked command traces

Each trace starts a fresh process. The JSON response immediately after a command is the recorded response from the C++ executable.

<!-- BEGIN TRACES -->

### T01. A nested commit is still inside its parent

**Worked explanation:** BEGIN saves the current map. Committing the inner frame discards only its snapshot; the outer snapshot still contains the original value.

Run `python examples/machine-coding/verify.py --trace T01` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SET name original
{"ok":true,"result":null}
BEGIN
{"ok":true,"result":null}
SET name outer
{"ok":true,"result":null}
BEGIN
{"ok":true,"result":null}
SET name inner
{"ok":true,"result":null}
COMMIT
{"ok":true,"result":null}
GET name
{"ok":true,"result":"inner"}
ROLLBACK
{"ok":true,"result":null}
STATE
{"ok":true,"result":{"data":{"name":"original"},"depth":0}}
```

**Common trap:** Discarding every snapshot on inner COMMIT silently changes the contract.

**Interview follow-up:** How would an undo log reduce the cost of BEGIN?

### T02. Empty value and missing key differ

**Worked explanation:** An optional value distinguishes a present empty string from no mapping. Erasing a missing key is a successful no-op returning false.

Run `python examples/machine-coding/verify.py --trace T02` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SET k ""
{"ok":true,"result":null}
GET k
{"ok":true,"result":""}
GET absent
{"ok":true,"result":null}
ERASE k
{"ok":true,"result":true}
ERASE k
{"ok":true,"result":false}
```

**Common trap:** Using an empty string as the missing-value sentinel loses information.

**Interview follow-up:** What should a DELETE API return for an absent key?

### T03. Rollback restores deletion and insertion

**Worked explanation:** The snapshot restores the complete key set, so an erased old key returns and a newly inserted key disappears.

Run `python examples/machine-coding/verify.py --trace T03` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SET a one
{"ok":true,"result":null}
BEGIN
{"ok":true,"result":null}
ERASE a
{"ok":true,"result":true}
SET b two
{"ok":true,"result":null}
ROLLBACK
{"ok":true,"result":null}
STATE
{"ok":true,"result":{"data":{"a":"one"},"depth":0}}
```

**Common trap:** Restoring updated values alone misses inserted and deleted keys.

**Interview follow-up:** How do tombstones help an undo-log implementation?

### T04. Invalid commands preserve the map

**Worked explanation:** Both transaction preconditions and the full command arity are checked before mutation.

Run `python examples/machine-coding/verify.py --trace T04` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SET a safe
{"ok":true,"result":null}
COMMIT
{"ok":false,"error":"no transaction"}
ROLLBACK
{"ok":false,"error":"no transaction"}
SET a bad extra
{"ok":false,"error":"wrong arity"}
STATE
{"ok":true,"result":{"data":{"a":"safe"},"depth":0}}
```

**Common trap:** Ignoring trailing arguments can accept a malformed write.

**Interview follow-up:** What is the difference between domain rejection and allocation failure?

<!-- END TRACES -->

## 6. Complexity and alternatives

With n current keys and d snapshots, map reads/writes are O(log n) comparisons, ignoring string length. BEGIN copies O(n) entries. Snapshot storage is the sum of all saved map sizes, roughly O(dn) when their sizes are comparable.

COMMIT logically pops one frame, but destroying its map takes O(size of that snapshot); it is not constant-time work overall. ROLLBACK swaps maps in constant time, then destroys the replaced current map. This distinction matters when a short-looking statement owns a large container.

An undo log can make BEGIN cheap: record the first prior value of each key changed in a frame, including a missing-key marker. Rolling back replays those changes. Committing a child must merge its earliest prior values into the parent without overwriting older parent history. That optimization needs new tests; it is not implemented here.

## 7. Architecture follow-up

One mutex around an operation would serialize access but would not assign transaction ownership to clients. A production API needs session identity, isolation semantics, limits, timeouts and a persistence strategy. Writing a snapshot file is not automatically a crash-safe transaction protocol.

Bridge to [transactions and concurrency](/docs/dbms/transactions-concurrency) and [recovery](/docs/dbms/recovery-relational-algebra). Explain which property each mechanism supplies; this exercise only implements serial in-memory state restoration.

## 8. Interview questions with answers

### Q1. Is COMMIT the same as persisting data?

No. Here it only removes an undo boundary. The entire map disappears when the process exits. Durability needs a separately specified storage and recovery protocol.

### Q2. Why use optional rather than returning an empty string?

An empty string is a legitimate stored value. Optional encodes presence independently of content, so the caller can distinguish absent from present-but-empty.

### Q3. Why can outer rollback undo an inner commit?

The outer snapshot predates both sets of changes. Inner commit removes only its own undo point and keeps the current map. The outer undo point remains valid.

### Q4. What would make this a multi-client transaction system?

Separate client contexts, a defined isolation level, conflict handling and a coordinated commit protocol. Sharing this snapshot stack among unrelated requests would mix transaction ownership.

### Q5. What does the random oracle test?

It generates writes, deletions, reads and nested transaction operations, compares responses with a Python snapshot model, and checks full state and depth after operations. It does not test concurrent interleavings.

### Q6. Is the strongest exception guarantee proved?

No. Exercised domain validation happens before mutation, and owned containers clean up normally. Allocation failure is not injected, so the handbook does not claim a verified all-exceptions transaction guarantee.

### Q7. Why can an undo log need tombstones?

It must record that a key did not exist before insertion. Restoring an empty string would leave an unwanted key instead of removing the insertion.

### Q8. What should you optimize first in an interview?

Complete the agreed API and prove nested rollback behavior. Then discuss snapshot memory and show which workload would justify an undo log or persistent data structure.

## 9. Practice tasks

- [ ] Add a maximum nesting depth. Reject a new BEGIN without changing state; test the boundary and a subsequent rollback.
- [ ] Replace snapshots with undo logs. Use the same command histories and add a child commit where the parent already changed the same key.
- [ ] Add a COUNT command. Verify insertion, replacement and erase affect size correctly; decide whether it counts keys or values.
- [ ] Design client-owned transactions on paper. Name the isolation contract, conflict policy and lifetime; do not claim that adding a mutex alone solves ownership.

Next: [Sliding Window Rate Limiter](/docs/machine-coding/sliding-window-rate-limiter).
