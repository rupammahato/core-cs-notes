# Machine Coding Practice — Part 5: Event Bus and Callback Lifecycle

**M3: callback ownership and mutation during dispatch are design decisions.**

## 1. The problem and its purpose

Build a synchronous, topic-based event bus. A producer publishes a payload without knowing every consumer. Consumers register callbacks by subscription ID and topic. This reduces direct coupling but creates lifecycle questions: who owns a handler, when can it disappear, and what happens when it fails?

Clarify order, duplicate subscriptions, unsubscribe timing, exceptions, recursive publishing and threads before coding. Here IDs are globally unique among active subscriptions; matching callbacks execute in subscription order. A publish copies the entire subscription list. Add/remove operations affect future dispatches, while the current snapshot still runs. Recursive synchronous publish is rejected.

## 2. API and invariants

| Command | Meaning |
| --- | --- |
| SUB id topic behavior target | Register a test callback; behavior is record, throw, off, add or recursive |
| OFF id | Remove active subscription, returning whether it existed |
| PUB topic payload | Run a snapshot and return per-callback outcomes plus captured test events |
| STATE | Active IDs in subscription order |

The behavior/target arguments belong to the test adapter, not to the model's real callback API. `subscribe` accepts `std::function<void(const std::string&)>`. A record callback appends an observation. A throw callback appends then throws. off removes target; add registers a record callback at target; recursive attempts another publish. The target must be nonempty even when unused.

Keep active IDs unique, preserve registration order and ensure the publishing guard clears on every exit. Callback exceptions are isolated per handler. A handler's effects before it throws are not undone: this bus offers failure isolation, not transactional callback execution.

## 3. How dispatch works

Copy callbacks first. Then set an RAII guard that resets the publishing flag in its destructor. Iterate the copy and invoke handlers matching the topic. Catch failures individually, append an error result and continue.

The snapshot owns copies of callable objects, so erasing an active subscription cannot invalidate the current loop. It does not automatically extend the lifetime of objects captured by reference. A callback closing over a destroyed object still has a lifetime bug. Prefer explicit ownership, weak references where appropriate, and a subscription handle that unregisters on destruction in a larger library.

The tiny local guard is a concrete use of resource cleanup tied to scope. The [C++ Core Guidelines' error-handling section](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-errors) recommends reasoning around invariants and resource ownership. The contract here is deliberately narrower than a general message broker.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
class EventBus {
public:
    using Callback = std::function<void(const std::string&)>;
    struct Subscription { std::string id, topic; Callback callback; };
private:
    std::vector<Subscription> subscriptions_;
    bool publishing_ = false;
public:
    void subscribe(const std::string& id, const std::string& topic, Callback callback) {
        identifier(id); identifier(topic); require(static_cast<bool>(callback), "empty callback");
        require(std::none_of(subscriptions_.begin(), subscriptions_.end(),
            [&](const auto& s) { return s.id == id; }), "duplicate subscription");
        subscriptions_.push_back({id, topic, std::move(callback)});
    }
    bool unsubscribe(const std::string& id) {
        identifier(id);
        auto it = std::find_if(subscriptions_.begin(), subscriptions_.end(),
            [&](const auto& s) { return s.id == id; });
        if (it == subscriptions_.end()) return false;
        subscriptions_.erase(it); return true;
    }
    std::vector<std::string> publish(const std::string& topic, const std::string& payload) {
        identifier(topic); require(!publishing_, "recursive publish");
        // Snapshot before setting the guard: a failed copy cannot leave the guard set.
        const auto snapshot = subscriptions_;
        struct Guard { bool& flag; explicit Guard(bool& f) : flag(f) { flag = true; } ~Guard() { flag = false; } } guard(publishing_);
        std::vector<std::string> results;
        for (const auto& s : snapshot) if (s.topic == topic) {
            try { s.callback(payload); results.push_back(s.id + ":ok"); }
            catch (const std::exception&) { results.push_back(s.id + ":error"); }
            catch (...) { results.push_back(s.id + ":error"); }
        }
        return results;
    }
    std::vector<std::string> ids() const {
        std::vector<std::string> result;
        for (const auto& s : subscriptions_) result.push_back(s.id);
        return result;
    }
};
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T09. One callback failure does not stop delivery

**Worked explanation:** Each matching callback runs in subscription order and is isolated by its own exception handler. Other topics are ignored.

Run `python examples/machine-coding/verify.py --trace T09` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SUB a orders record x
{"ok":true,"result":null}
SUB b orders throw x
{"ok":true,"result":null}
SUB c other record x
{"ok":true,"result":null}
SUB d orders record x
{"ok":true,"result":null}
PUB orders paid
{"ok":true,"result":{"callbacks":["a:ok","b:error","d:ok"],"events":["a:paid","b:paid","d:paid"]}}
```

**Common trap:** A catch around the entire loop skips later callbacks after the first throw.

**Interview follow-up:** Should a caller receive aggregate failures, or should they go to telemetry?

### T10. Unsubscribe changes the next dispatch

**Worked explanation:** The copied callback list owns this dispatch. Removing b while a runs does not remove b from the current snapshot.

Run `python examples/machine-coding/verify.py --trace T10` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SUB a t off b
{"ok":true,"result":null}
SUB b t record x
{"ok":true,"result":null}
PUB t one
{"ok":true,"result":{"callbacks":["a:ok","b:ok"],"events":["a:one","b:one"]}}
PUB t two
{"ok":true,"result":{"callbacks":["a:ok"],"events":["a:two"]}}
STATE
{"ok":true,"result":["a"]}
```

**Common trap:** Iterating the live vector while erasing subscriptions can invalidate iterators.

**Interview follow-up:** How would immediate cancellation differ from snapshot semantics?

### T11. New subscriptions wait until the next publish

**Worked explanation:** The first dispatch copies only a. The next dispatch includes c; a then tries to add c again, fails, and delivery still reaches c.

Run `python examples/machine-coding/verify.py --trace T11` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SUB a t add c
{"ok":true,"result":null}
PUB t one
{"ok":true,"result":{"callbacks":["a:ok"],"events":["a:one"]}}
PUB t two
{"ok":true,"result":{"callbacks":["a:error","c:ok"],"events":["a:two","c:two"]}}
STATE
{"ok":true,"result":["a","c"]}
```

**Common trap:** Growing the live callback list during iteration can make one publish unbounded.

**Interview follow-up:** Should repeated registration replace a handler or report a conflict?

### T12. Recursive publish is isolated and the guard resets

**Worked explanation:** A callback attempting synchronous recursion receives a rejection. The outer dispatch records its failure, runs b, and remains usable afterwards.

Run `python examples/machine-coding/verify.py --trace T12` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
SUB a t recursive x
{"ok":true,"result":null}
SUB b t record x
{"ok":true,"result":null}
PUB t one
{"ok":true,"result":{"callbacks":["a:error","b:ok"],"events":["a:one","b:one"]}}
PUB t two
{"ok":true,"result":{"callbacks":["a:error","b:ok"],"events":["a:two","b:two"]}}
```

**Common trap:** A manually reset boolean can remain set after an unexpected exception.

**Interview follow-up:** How would a queued event loop support recursive emission safely?

<!-- END TRACES -->

## 6. Complexity and trade-offs

For S active subscriptions, duplicate detection and unsubscribe are O(S); vector erase can move later entries. Publish copies O(S) callable wrappers and scans O(S), plus callback execution and result-building costs. A callable copy may itself allocate or copy expensive captured state. Snapshot memory is O(S) wrappers plus captured copies and output.

A topic index could avoid scanning unrelated subscriptions, while stable handler tokens could make removal cheaper. Optimizing containers before deciding mutation semantics is dangerous: a fast live iterator still cannot safely erase itself without a defined strategy.

## 7. Architecture follow-up

For a threaded bus, protect subscription mutation, copy the relevant handlers under a lock, then normally invoke user code after releasing the lock. Otherwise arbitrary callback work can cause contention or reentrant deadlock. Even that design needs clear concurrent removal semantics and thread-safe callback targets.

An asynchronous bus adds queues, backpressure, shutdown, ordering, retries and duplicate delivery. The current in-process synchronous call provides none of those guarantees. Bridge to [notifications and webhooks](/docs/system-design/notifications-webhooks) and [reliable workflows](/docs/system-design/reliable-workflows-concurrency).

## 8. Interview questions with answers

### Q1. Why copy the subscribers?

A stable dispatch snapshot prevents active-list mutation from invalidating iteration and defines which handlers belong to this publish. The copy's cost is an explicit trade-off for simple semantics.

### Q2. Does unsubscribe stop a callback already in the snapshot?

No. It removes future participation. Immediate cancellation would require a shared active token or other check, plus a contract for callbacks that have already started.

### Q3. Why can a newly added callback wait until the next publish?

The producer's event has a fixed recipient snapshot. This avoids unbounded growth of the current dispatch and produces deterministic behavior when handlers register more handlers.

### Q4. What happens if one callback throws?

Its outcome becomes error, its earlier side effects remain, and later handlers continue. The direct API tests also throw a non-standard exception to exercise the catch-all path.

### Q5. Why reject recursive publish?

It bounds synchronous nesting and keeps the teaching contract simple. A queue can support nested emission by deferring events, but then ordering, queue limits and failure semantics must be specified.

### Q6. Is std::function itself a lifetime guarantee?

It owns its stored callable, including value captures. Reference captures and raw pointers can still refer to objects that die first. Ownership must be designed at the callback boundary.

### Q7. Can the same ID be registered after unsubscribe?

Yes, once it is no longer active. A current snapshot may still hold the old callable under that ID, so a new registration does not retroactively change that snapshot.

### Q8. How would you avoid a global lock during callbacks?

Acquire a lock to obtain an owned snapshot, release it, then invoke user code. Specify what concurrent unsubscribe means and keep handler-owned state safe independently of the subscription container.

## 9. Practice tasks

- [ ] Add a move-only subscription handle that unregisters in its destructor. Test moved-from handles and ensure the bus outlives the handle or use shared lifetime state.
- [ ] Implement a topic index while preserving dispatch order and the current four traces.
- [ ] Add bounded queued publication. Specify overflow behavior and test nested emission without recursive stack growth.
- [ ] Add a handler that unsubscribes itself and verify it runs once across two publishes. Then explain why this differs from stopping its current invocation.

Next: [Virtual Time Task Scheduler](/docs/machine-coding/virtual-time-task-scheduler).
