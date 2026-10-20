# Machine Coding Practice — Part 4: Sliding Window Rate Limiter

**M2: make time boundaries and quota consumption part of the API.**

## 1. The problem and its purpose

Implement ALLOW(key, now) for at most L accepted requests per key in a window of width W. A rate limiter decides whether an action may proceed under a policy. It may protect an expensive backend, enforce a plan allowance, or reduce a burst of work. Those goals can require different algorithms.

Ask whether the quota counts attempts or accepted requests, whether different users share capacity, how boundary timestamps behave, and who supplies time. Here only accepted requests count, quotas are per key, and callers supply nonnegative integer time in one arbitrary unit. An instance requires globally nondecreasing timestamps, including calls for different keys.

## 2. Contract and invariant

The active window is **(now − W, now]**. A timestamp equal to now − W has expired. Each key owns a deque of accepted timestamps in nondecreasing order. Prune expired entries before deciding. Admit only when the remaining count is below L, and append only on admission.

INIT L W is allowed once after a valid constructor completes. L is in 1..1,000,000 and W in 1..10^12. Time is in 0..10^12. A rejected time or empty key does not advance the clock. A quota denial is a valid call, so it does advance the instance clock.

| Choice | Consequence |
| --- | --- |
| Sliding log | Exact accepted-request count within the declared interval |
| Fixed window | Simpler counters but a different boundary-burst behavior |
| Token bucket | Defines replenishment and burst capacity rather than this exact history rule |
| Injected time | Fast deterministic boundary tests without sleeping |

These algorithms answer different policy questions. Do not replace one with another while preserving the old explanation of its guarantee.

## 3. Implementation reasoning

Validate key and time first. Look up the key's deque, pop its expired prefix, then test size. A denied request never adds a timestamp. The deque remains sorted because the instance rejects time regression before touching it.

Requests with equal timestamps are distinct requests and consume separate slots if admitted. There is no request-ID deduplication. If retries should count once, introduce a separate identity and retention contract.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
class SlidingLimiter {
    Number limit_, window_, clock_ = 0;
    std::map<std::string, std::deque<Number>> accepted_;
public:
    SlidingLimiter(Number limit, Number window) : limit_(limit), window_(window) {
        require(limit > 0 && limit <= 1000000, "invalid limit");
        require(window > 0 && window <= 1000000000000LL, "invalid window");
    }
    bool allow(const std::string& key, Number now) {
        identifier(key); timeValue(now); require(now >= clock_, "time regressed");
        clock_ = now; auto& times = accepted_[key];
        while (!times.empty() && times.front() <= now - window_) times.pop_front();
        if (static_cast<Number>(times.size()) >= limit_) return false;
        times.push_back(now); return true;
    }
};
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T05. The oldest accepted request expires exactly at the boundary

**Worked explanation:** The active interval is (now-window, now]. At time 10 the request at 0 is outside a width-10 window, while the request at 9 remains.

Run `python examples/machine-coding/verify.py --trace T05` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
INIT 2 10
{"ok":true,"result":null}
ALLOW user 0
{"ok":true,"result":true}
ALLOW user 9
{"ok":true,"result":true}
ALLOW user 9
{"ok":true,"result":false}
ALLOW user 10
{"ok":true,"result":true}
ALLOW user 10
{"ok":true,"result":false}
```

**Common trap:** Using < instead of <= when pruning counts an expired request.

**Interview follow-up:** Would a closed interval change your test expectation?

### T06. Users have separate quotas

**Worked explanation:** The accepted histories are keyed by user. A denied attempt does not add another timestamp.

Run `python examples/machine-coding/verify.py --trace T06` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
INIT 1 5
{"ok":true,"result":null}
ALLOW a 0
{"ok":true,"result":true}
ALLOW a 1
{"ok":true,"result":false}
ALLOW b 1
{"ok":true,"result":true}
ALLOW a 5
{"ok":true,"result":true}
```

**Common trap:** A single global deque accidentally makes unrelated users share a quota.

**Interview follow-up:** How would you add a second global quota without partial consumption?

### T07. A regressing clock is rejected

**Worked explanation:** Time is globally nondecreasing for this limiter instance. An invalid timestamp is rejected before pruning or inserting.

Run `python examples/machine-coding/verify.py --trace T07` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
INIT 1 10
{"ok":true,"result":null}
ALLOW a 10
{"ok":true,"result":true}
ALLOW b 9
{"ok":false,"error":"time regressed"}
ALLOW b 10
{"ok":true,"result":true}
ALLOW a 19
{"ok":true,"result":false}
ALLOW a 20
{"ok":true,"result":true}
```

**Common trap:** Sorting timestamps after accepting them hides a broken clock contract.

**Interview follow-up:** Which clock would you inject in a real single-process service?

### T08. Failed initialization can be retried

**Worked explanation:** The optional service becomes engaged only after a valid constructor completes. Initialization is then immutable.

Run `python examples/machine-coding/verify.py --trace T08` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
ALLOW a 0
{"ok":false,"error":"initialize first"}
INIT 0 10
{"ok":false,"error":"invalid limit"}
INIT 1 10
{"ok":true,"result":null}
INIT 2 10
{"ok":false,"error":"already initialized"}
ALLOW a 0
{"ok":true,"result":true}
```

**Common trap:** Setting an initialized flag before validation can brick the service.

**Interview follow-up:** How would you safely change a running limiter policy?

<!-- END TRACES -->

## 6. Complexity, memory and limitations

A lookup in the ordered key map costs O(log U), where U is the number of seen keys. One call can prune up to L entries; across accepted requests each timestamp is appended and removed at most once. Deque maintenance is therefore amortized O(1) per accepted timestamp, plus map and string costs.

Each key retains at most L accepted timestamps, including expired timestamps until that key is visited again. The map never evicts inactive keys. Memory can grow with distinct keys even when traffic stops. A production cleanup strategy needs limits and ownership; adding expiration must preserve the last required history.

This is single-threaded. A check followed by an append must be one protected operation under concurrency. Two threads observing the same available slot could otherwise both admit. Independent instances each enforcing L do not enforce a global L across a fleet.

## 7. Architecture follow-up

For one process, inject a monotonic clock and serialize check/prune/append for a key. For a shared limiter, choose an authoritative state owner and an atomic operation supported by its storage. Explain what happens when that owner is unavailable: the policy may fail open or fail closed depending on the feature.

A per-user limit plus a global limit requires a combined reservation decision. Consuming one quota before discovering the other is exhausted can waste capacity unless rollback or an atomic joint decision is defined. No distributed store, real clock or throughput benchmark runs in this lab.

Bridge to [the architecture rate limiter](/docs/system-design/rate-limiter) for fleet-level trade-offs.

## 8. Interview questions with answers

### Q1. Why does pruning use <=?

The left endpoint is open. At time now, a request at now − W is outside the window. Changing the comparison changes the policy and the expected boundary tests.

### Q2. Do denied requests consume quota?

Not under this contract. They can still advance the accepted notion of current time and prune history, but they do not append to a key's accepted deque.

### Q3. Why not call the system clock inside ALLOW?

Injecting time makes edge cases deterministic and avoids slow sleeps. A real adapter can supply a monotonic clock while the policy remains independently testable.

### Q4. Why is time global rather than per key?

It is an explicit simplification: one caller supplies an ordered stream to one instance. Per-key monotonic time is another valid design, but the implementation and tests would need to change together.

### Q5. Does an unordered map make the whole call constant time?

It changes lookup expectations, not the cost of pruning many expired timestamps. Hashing strings, collisions, allocation and cleanup still matter; state the amortized and worst-case parts separately.

### Q6. How would you test that denials are not stored?

Fill the quota, issue several denied calls, then advance exactly to the first expiration boundary. Admission should depend only on the originally accepted timestamps.

### Q7. What is missing for multiple application servers?

A coordinated key owner or shared atomic state, routing/failure semantics and a consistent time contract. Copying this limiter onto every server multiplies the possible accepted fleet total.

### Q8. Is a rate limiter an authentication mechanism?

No. It controls resource consumption according to supplied keys. Identity and authorization must be established separately, and keys must resist trivial evasion if the policy depends on users.

## 9. Practice tasks

- [ ] Add an idle-key cleanup operation. Prove it cannot erase history that would still count at the next valid time.
- [ ] Return remaining capacity and earliest retry time. Test a full deque, an empty deque and equal timestamps.
- [ ] Implement an attempts-counting variant. Write a counterexample showing its behavior differs from this accepted-only policy.
- [ ] Specify a shared limiter outage policy for login and image previews. Explain the different costs of admitting or rejecting during an outage.

Next: [Event Bus and Callback Lifecycle](/docs/machine-coding/event-bus-and-callback-lifecycle).
