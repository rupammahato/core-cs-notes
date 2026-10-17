"""Generate S1 from authored explanations, exact code and recorded observations."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
sources = ['estimates.py', 'algorithms.py', 'limiter.py', 'http_api.py']
outputs = ['estimates', 'algorithms', 'bucket', 'scope_lifecycle', 'concurrency', 'http_contract']


def code(name):
    return '```python\n'+(BASE/name).read_text(encoding='utf-8')+'```'


def output(name):
    return '```json\n'+json.dumps(proof['observations'][name], ensure_ascii=False, indent=2)+'\n```'


chapter = r'''# Architecture and System Design Placement Handbook — Part 8
# S1: Rate Limiter

**Estimated time: 4–5 hours | Architecture numeric module: 6 | Requires: A0–A4; Resume M7/M8/M15 refreshers**

---

## Why this module exists

“Allow 100 requests per minute” leaves several questions unanswered: per whom, across how many servers, with what burst allowance, measured by whose clock, and what happens when the quota authority is unavailable? A counter alone cannot answer them.

This worked design starts with the behavior promised to an API caller, compares window algorithms and implements an atomic shared token-bucket decision. A real local SQLite race exposes the broken read/check/write approach. A loopback HTTP API then demonstrates authenticated scope, 429, rounded Retry-After, charged failed work and explicit degraded behavior.

**Organizing principle: define the admission contract, then put the complete check-and-charge decision at the state authority.**

Python/SQLite makes the mechanism reproducible without starting Docker, Redis or an existing database service. Separate thread-owned connections share a local file; they are not multiple deployed API machines. SQLite serializes writers for the file. A Redis or PostgreSQL implementation needs its own engine, failover, clock, transaction and performance checks.

The 30 Q&As are curated interview practice, not a measured ranking of employer frequency. This chapter answers architecture bank Q26 and Q40: two API servers both admit what they believe is the final request in a shared quota. The fix must cover identity, atomicity, time and failure semantics together.

---

## 1. Prompt and clarification questions

**Prompt:** design rate limiting for an authenticated API used by placement learners. Protect expensive operations, allow a small legitimate burst and maintain one quota per tenant, authenticated subject and route class across API instances.

| Clarification | Architectural consequence |
| --- | --- |
| Abuse protection, paid quota or downstream capacity protection? | Different strictness, retention, reconciliation and outage choices |
| Per IP, API key, account, tenant, endpoint or several at once? | Key ownership, fairness and multi-key atomicity |
| Exact rolling count or average rate plus burst? | Sliding log versus token bucket and permitted traffic shape |
| Do rejected attempts or failed admitted operations count? | Check/update logic, refunds and retry behavior |
| Equal request cost or server-estimated weights? | Token units, validation and expensive-route budgets |
| One region or a hard worldwide quota? | Routing authority, coordination latency and partition policy |
| Reject immediately or queue/delay? | 429 contract versus bounded scheduler and deadline management |
| Can reads continue during dependency failure? | Explicit fail-open scope and emergency protection |
| What traffic, active identities and hot-key skew? | Memory, decision throughput and partition bottlenecks |
| What configuration changes and clock assumptions are acceptable? | Migration, refill behavior and consistency during rollout |

A product quota such as “1000 successful exports per month” is not automatically the same service as a protective request limiter. Billing needs a durable usage definition, deduplication and reconciliation; the short-lived token state below is insufficient.

---

## 2. Scope, invariants and deliberate limits

| Area | Baseline choice |
| --- | --- |
| Identity | Trusted credential mapping to stable tenant and subject; request headers cannot choose those values |
| Key | Canonical tuple `(tenant, subject, route_class)` |
| Algorithm | Token bucket; capacity 3 tokens, refill 1 token/second for the HTTP lesson |
| Accounting | One token per HTTP admission; denials do not charge; admitted failed work remains charged |
| Shared decision | Read/refill/check/debit/write in one SQLite `BEGIN IMMEDIATE` transaction |
| Time | Nonnegative integer epoch milliseconds supplied by server context; rollback clamped per bucket |
| Rejection | 429 with integer Retry-After and no-store |
| Dependency failure | Read route chosen fail-open; write route chosen fail-closed with 503 |
| State growth | 128 live scopes by default; conservative idle expiry; reject new scopes when full |
| Policy change | Active bucket rejects a different capacity/rate; no live migration implemented |
| Exclusions | Redis execution, global clock service, distributed failover, production auth/TLS, hierarchical quotas, scheduler, billing and throughput benchmark |

The invariants are testable:

- One shared bucket cannot spend the same available credit twice under competing transactions.
- Credit stays between zero and capacity; a rejected request does not subtract its cost.
- Refill uses elapsed time since the stored high-water time; clock rollback does not mint credit.
- Another credential for the same subject does not create another budget.
- A different tenant, subject or route class has a deliberately separate budget.
- An unavailable authority is distinguishable from a known exhausted bucket.
- State cannot be reset early merely to make room for a new identity.

The strict shared-quota promise applies while decisions use the same authority and consistent policy/time assumptions. Chosen fail-open requests bypass that promise. A fast clock, state loss or independent authority can grant extra traffic; naming those boundaries is part of the design.

---

## 3. Estimate traffic and state before selecting infrastructure

Assume 8,640,000 requests/day, a selected 10× peak factor and one million active scope keys. At 128 assumed logical bytes per bucket, a single logical copy is 128 MB. These are planning inputs, not an observed Redis allocation or SQLite file size.

{{ESTIMATES_CODE}}

Calculated output:

{{ESTIMATES_OUTPUT}}

100 average requests/second becomes a hypothetical 1000 peak decisions/second. One atomic script can be one network round trip but still consumes several internal operations and server time. Count decision calls, bytes, connection budgets, hot keys and business work separately.

A sliding log holding 60 events for each of 100,000 active keys has six million timestamps. The example's 16 bytes/event gives 96 MB of event payload before data-structure, identity, allocator, index and replica overhead. A constant-size bucket may use much less state, but you must measure the actual implementation.

Four independent local buckets of capacity 30 permit 120 initial requests for one intended global identity. More API instances can silently increase a local quota. Dividing a global budget among servers avoids that particular multiplication only by introducing allocation, rebalancing and unused-capacity problems.

Use [A0's estimation method](/docs/system-design/design-method-estimation): state units, distinguish active keys from registered users, describe skew, and separate logical estimates from measured capacity.

---

## 4. Choose the algorithm from its traffic promise

| Algorithm | State per key | Admission behavior | Main caveat |
| --- | --- | --- | --- |
| Fixed aligned window | Window ID and counter | At most L admissions in each aligned W interval | Can admit almost 2L around a boundary |
| Exact sliding log | Recent accepted timestamps | At most L in the chosen rolling interval | State and pruning proportional to retained admissions |
| Weighted sliding counter | Previous/current counters and window ID | Approximates a rolling count using previous-window weight | Cannot reconstruct the actual timestamp distribution |
| Token bucket | Credit and last refill time | Burst up to B with sustained refill r | Does not promise an exact L-in-every-W rolling limit |
| Leaky-bucket shaping | Queue/debt/scheduled departure state | Smooths release at a chosen pace | Delay queue needs bounds, deadlines and overload behavior |

For fixed windows, events at 999 ms and 1000 ms belong to different aligned one-second windows. The exact log below uses `(now − W, now]`, so an event at the left cutoff is removed. State this equality rule explicitly.

The weighted counter estimates `current + previous × (1 − elapsed/window)`. It assumes something about distribution inside the previous window. Three requests at 999 ms are all still recent at 1500 ms, but their weighted estimate is only 1.5. The implementation can admit a fourth request while the exact log denies it. Approximation error can also be conservative for another distribution.

Nginx documents leaky-bucket request limiting with configurable burst and delay behavior. The product configuration determines when excess requests wait or reject; do not treat every named bucket implementation as identical. [Nginx request-limiting module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html).

---

## 5. Run the window comparison and its counterexample

These comparison classes intentionally take trusted positive constructor constants and nondecreasing integer milliseconds. They are deterministic single-process teaching models, not a thread-safe or attacker-facing API. The shared token store later performs its own input checks.

{{ALGORITHMS_CODE}}

Observed timeline and counterexample:

{{ALGORITHMS_OUTPUT}}

At 1999 ms the exact log removes admissions at 999 ms because of its chosen open-left interval. The fixed window's current counter is still full. Neither trace is inherently “wrong”; they implement different promises. The error would be advertising a fixed-window policy as an exact rolling limit.

The exact log stores only admissions and is bounded by its limit per key. An algorithm that stores every rejected request can let an attacker grow its memory footprint. Total memory still grows with the number of identities unless the system controls scope creation and retention.

---

## 6. Derive token-bucket arithmetic with units

Let B be capacity in tokens, r be refill in tokens/second, c be request cost and Δ be elapsed milliseconds. The implementation stores milli-tokens:

```text
full_credit = B × 1000
refilled_credit = min(full_credit, old_credit + Δ_ms × r_tokens_per_second)
allow if refilled_credit >= c × 1000
if allowed: new_credit = refilled_credit - c × 1000
if denied:  new_credit = refilled_credit
wait_ms = ceil((c × 1000 - refilled_credit) / r), for a denial
```

One millisecond at one token/second adds one milli-token. Integer arithmetic retains fractional refill without floating-point rounding drift. This fixture accepts whole positive token rates and costs; arbitrary decimal rates need a deliberate fixed-point/rational representation.

For capacity 3 and rate 1, three simultaneous requests consume the initial burst. At 999 ms the balance is 999 milli-tokens: deny and report one more millisecond. At 1000 ms exactly one token is available. For cost 3 against two available tokens at rate 2, wait is 500 ms.

A cost above capacity cannot ever succeed under that policy. Reject the configuration/request before state mutation rather than returning a misleading finite retry. Here cost is selected by server code, not an untrusted caller.

The usual traffic envelope is a burst plus refill, approximately `B + r × elapsed_seconds` for unit-cost admissions over an interval, subject to interval endpoints and initial state. It is not “B requests every second” and does not limit simultaneous in-flight work by itself.

---

## 7. API contract and identity ownership

| Request | Meaning | Chosen responses |
| --- | --- | --- |
| `GET /api/read` with lesson bearer | Admit a cheap read using route class `read` | 200, 429, or marked fail-open 200 on authority outage |
| Empty `POST /api/write` with lesson bearer | Admit a write using route class `write` | 200, 429, or 503 on authority outage |
| Missing/unknown bearer on known route | Authentication failure before quota decision | 401 |
| Unrecognized method/path/query variant | No configured route | 404 in this narrow lesson router |
| Body or transfer encoding on known route | Unsupported input, checked before quota | 400 |
| Admitted work deliberately fails | Quota charge remains | 500 with enforced remaining count |

Two published lesson credentials map to the same stable Alice identity. Credential rotation does not reset Alice's budget. Bob and another tenant have distinct scopes. These credentials are public fixtures, not a security implementation.

The route class comes from a fixed server route table. Do not key on raw URLs containing arbitrary IDs or query strings: `/items/1` and `/items/2` might need one shared `item-read` budget. Do not accept a tenant header as authenticated identity. Trust forwarded client IP only across an explicitly configured proxy boundary; NAT also makes IP a poor sole identity for many authenticated products.

RFC 6585 defines 429 and allows Retry-After, while leaving identification and counting policies to the server. It also forbids caching 429 responses. This fixture sends no-store and rounds positive waits up to whole seconds. [RFC 6585 §4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4).

Retry-After can be an HTTP date or delay in seconds; this API chooses the latter. It is a scheduling hint, not a reserved future token: another client may spend the newly refilled credit first. `X-Lesson-Quota*` are custom teaching headers, not a claim to implement standardized quota fields. [RFC 9110: Retry-After](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after).

---

## 8. Schema, indexes and the atomic authority

| Column | Purpose |
| --- | --- |
| `scope TEXT PRIMARY KEY` | Canonical JSON encoding of trusted tenant/subject/route tuple |
| `capacity`, `rate` | Detect conflicting policy for a live bucket |
| `credit` | Nonnegative integer milli-token balance |
| `last_ms` | Effective timestamp high-water mark |
| `expires_ms` | Conservative time after which idle reset is safe under chosen time assumptions |

The primary key locates one budget. The expiry index supports pruning. All callers use the same file and policy in the local shared-authority demonstration. The transaction first acquires write ownership, prunes safe idle rows, reads current credit, refills, checks cost, updates and commits.

`BEGIN IMMEDIATE` obtains a write transaction up front; it can fail with busy contention. It does not create a row lock per scope. SQLite permits only one concurrent write transaction, so unrelated buckets can contend. This is useful for demonstrating serialization and an important scaling limit. [SQLite transactions](https://sqlite.org/lang_transaction.html).

{{LIMITER_CODE}}

The try/rollback boundary includes pruning, admission and update. A live-policy mismatch or state-cap failure rolls back the transaction. A BEGIN failure occurs before any mutation. A connection is created and used by its owning thread and closed afterwards.

This schema is an executable mechanism demonstration, not a durable policy registry. Policy identity is stored only while a bucket exists. After safe idle deletion, a bucket is created under the current configuration. All callers must agree on that configuration; an explicit migration/registry protocol is needed for a real rollout.

---

## 9. Smallest architecture and end-to-end traces

```mermaid
flowchart LR
    Client[Authenticated API caller] --> API[Route and identity validation]
    API --> Decision[Atomic quota decision]
    Decision --> State[(Shared bucket authority)]
    Decision -->|allowed| Work[Business operation]
    Decision -->|exhausted| Rejection[429 plus Retry-After]
    Decision -->|unavailable| Policy[Configured failure policy]
    Policy -->|read: chosen open| Work
    Policy -->|write: chosen closed| Unavailable[503]
```

The diagram's shared-authority boundary is the important part. The executable API uses per-handler connections to one local SQLite file, not a remote cluster. No message broker or separate policy microservice is required to demonstrate admission.

**Allowed trace:** authenticate → map route class and cost → obtain authority transaction → load/refill/check/debit/commit → return decision → perform work. The business result is outside the quota transaction. Do not hold the quota write lock while making a downstream network call.

**Denied trace:** authenticate → transaction computes insufficient credit → persist refill/high-water state without spending tokens → commit → send 429/no-store/rounded Retry-After → do not run work.

**Authority unavailable trace:** dependency times out or cannot admit a new state key → select the route's explicit failure policy. Read returns a marked degraded-open result; write returns 503 before work. A policy mismatch stays closed even on the read route because silently bypassing a configuration error is not the chosen outage policy.

**Lost response trace:** admission may commit and work may complete even if the client sees a timeout. A fresh retry is another admission. Exactly-once business effects require their own stable operation key and atomic operation outcome as in [A3](/docs/system-design/reliable-workflows-concurrency); rate limiting cannot supply that guarantee.

---

## 10. Observe refill, weighted cost, rollback and restart

The verification suite uses deterministic server-side clocks, including equality boundaries and a deliberate rollback:

{{BUCKET_OUTPUT}}

At 500 ms after a stored 1000 ms high-water mark, the implementation does not refill backwards. An empty bucket needs 500 ms to catch up and another 1000 ms for a token, so the returned wait is 1500 ms. Reporting only the refill deficit would understate the chosen clock behavior.

Clamping a backward clock can make the limiter temporarily stricter. A forward jump can refill early relative to real elapsed time; the credit cap bounds the instantaneous bucket balance but does not repair the clock. The caller supplying a fast timestamp could also prune old rows. Consequently this API never accepts client timestamps, and a deployed shared implementation needs one controlled time source plus an explicit clock/failover policy.

Python's monotonic clock is suitable for process-local durations, but its reference point is unspecified. Do not persist it as an epoch timestamp or casually compare independently scoped clocks. Redis TIME supplies server time, not a promise that wall time never moves backwards. [Python time.monotonic](https://docs.python.org/3.12/library/time.html#time.monotonic), [Redis TIME](https://redis.io/docs/latest/commands/time/).

Restart preserves a bucket when the same SQLite database file survives. That is different from restarting with an empty file, losing Redis state or routing to an independent authority. The fixture demonstrates close/reopen; it does not simulate a machine crash, replica promotion or disaster recovery.

---

## 11. Bound scope growth without resetting live quotas

Observed lifecycle evidence:

{{SCOPE_LIFECYCLE_OUTPUT}}

The fixture expires a bucket only after its last effective decision time plus the time required to refill a completely empty bucket. This is conservative: it can retain state longer than necessary, but recreating a full bucket after that idle period does not grant credit sooner than natural refill under the same policy/time assumptions.

A TTL shorter than full refill can reset a depleted bucket early. A memory cache that evicts live buckets under pressure can have the same effect. Capacity policies must describe whether state loss is allowed to relax enforcement; “it is only a cache” is not a correctness argument for a quota authority.

Here a new active scope fails when the cap is full, while an existing scope keeps its budget. The HTTP layer treats that resource failure as dependency unavailability according to route policy. This creates a potential availability attack if many authenticated identities can monopolize the cap. Limit account/key creation, use a coarser protective budget, monitor cardinality and provision based on active populations.

Pruning all due rows and counting keys inside every write transaction is deliberately simple and can become expensive. A production design needs bounded cleanup batches or engine-native expiry, measured storage/index costs, and an overload policy. The fixture's 128-key cap is a lesson resource bound, not a claim of production capacity.

---

## 12. Reproduce the final-slot race

The harness first runs a deliberately broken implementation. Two independent connections both read `count = 0` before a barrier, both decide the one-slot policy permits them, and both write `1`. The state claims one admission although two callers were admitted.

It then runs two thread-owned connections through `Store.decide` with the same key, timestamp and capacity-one policy. The transaction boundary covers the complete read/refill/check/debit/write decision.

{{CONCURRENCY_OUTPUT}}

The winner is intentionally unspecified. One succeeds and one denies; a third caller still sees the charge. Another check holds an actual SQLite write transaction, observes the second connection's bounded busy failure, releases the lock and confirms recovery. HTTP tests exercise that real contention path too.

Atomic increment alone does not necessarily implement a check-and-admit contract. You must decide whether over-limit increments count rejected attempts, how expiry is attached, and whether there is a read/check race. Redis's own INCR patterns describe the increment/expiry failure gap and a script approach. [Redis INCR rate-limiter patterns](https://redis.io/docs/latest/commands/incr/).

---

## 13. Real HTTP boundary and observed responses

{{HTTP_API_CODE}}

Observed local HTTP contract:

{{HTTP_CONTRACT_OUTPUT}}

The controlled outage flag exists only in the harness/server context, never as an HTTP parameter. The suite also holds a real database write lock to verify fallback. Invalid credentials and unsupported input are rejected before admission. Forwarded identity, client cost and arbitrary query strings cannot create new budgets in this route table.

The small server handles lesson requests on loopback only. It does not implement production TLS, timeouts for hostile clients, connection quotas, authentication verification, proxy trust configuration or an administrative policy endpoint. A deployed gateway/Node application still needs these boundaries.

Every admitted operation is charged before work. The injected 500 demonstrates that work failure does not refund automatically. Refunding requires a stable admission identifier, one-time refund semantics and a decision about retries; a careless refund endpoint is an abuse primitive.

---

## 14. Dependency failures, retries and backpressure

| Situation | Chosen baseline behavior | Remaining risk or alternative |
| --- | --- | --- |
| Known exhausted bucket | 429, no work, Retry-After | Concurrent users can consume the next credit first |
| Authority unavailable on read | Marked fail-open and execute | Shared quota can be exceeded; use separate emergency protection if required |
| Authority unavailable on write | 503, no work | Availability depends on authority recovery |
| Active policy mismatch | 503, no bypass | Requires rollout/migration correction |
| Admission commits but response lost | Retry is a new attempt | May charge again; business idempotency remains separate |
| Work fails after admission | Token stays spent | Product may instead define a controlled refund protocol |
| State lost/recreated early | Not repaired by this fixture | Persist/recover, rebuild conservatively or accept a documented burst |

There is no universal fail-open answer. A public catalog read may prioritize availability; password reset, payment authorization or a costly model endpoint may require stronger abuse/cost controls. Choose using the harm being limited. The read/write split here illustrates a policy, not a universal classification.

Fail-open must be visible in metrics and responses. It does not mean unlimited capacity is safe. An emergency process-local bucket, concurrency semaphore or upstream coarse limit can bound some damage, but each adds a separate budget and recovery contract; those mechanisms are discussed, not implemented here.

Do not immediately retry the quota authority many times inside every request. Bound dependency time and attempts. Clients should respect Retry-After, add scheduling jitter when appropriate and stop at a retry/deadline budget. Otherwise the limiter can become the target of a synchronized retry storm.

A rate limit bounds admissions over time. A concurrency limit bounds in-flight work. Even a modest arrival rate can accumulate many slow requests. An unbounded queue merely moves the overload into memory and latency. Bounded queues need maximum wait time, cancellation and a rejection policy; they are separate from this immediate-rejection API.

---

## 15. Redis, partitions and justified growth stages

| Stage / trigger | Change to consider | Contract to preserve and evidence needed |
| --- | --- | --- |
| One small API process | Local bucket may suffice | Explicitly process-local scope; restart and replica multiplication understood |
| Several API instances need one quota | Shared atomic authority | Same key, policy, time and atomic check/update; race/timeout tests |
| SQLite writer contention matters | Redis script/function or PostgreSQL transactional implementation | Port exact units, expiry, failure and clock behavior; measure actual latency/skew |
| Many independent keys | Partition by canonical subject/tenant scope | Stable routing, hot-key handling and failover/state-loss policy |
| One hot tenant/key | Revisit quota scope or leased sub-budgets | One key remains a serialization point; lease overshoot/stranded capacity accounted |
| Worldwide hard quota | One logical authority or coordinated allocations | Cross-region latency versus availability during partition |
| Several budget dimensions | Atomic multi-budget decision or defined staged charges | All-or-none, refund/compensation or accepted partial charge semantics |

A Redis implementation would execute refill/check/debit/write/expiry in a short atomic script or function using server-owned policy and time. Scripts block other activity while executing, so do not scan a large history or do unbounded work. Atomic isolation is not a promise of automatic rollback for arbitrary script errors; validate inputs and structure writes carefully. No Redis script is executed by this fixture. [Redis scripting introduction](https://redis.io/docs/latest/develop/programmability/eval-intro/).

With Redis Cluster, multi-key operations require compatible hash-slot placement. A per-user plus per-tenant plus global quota is not automatically one atomic script across arbitrary slots. Co-locating keys can create a hot partition; staged checks can spend one budget before another rejects. State the chosen compromise rather than drawing three independent boxes and calling the result atomic. [Redis Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/).

Replication and failover can lose recent decisions depending on configuration and failure mode. Global active-active counters can disagree under partitions. If regions each get a local burst B and refill r, the aggregate can approach the sum of those budgets. Leasing pieces of a global budget can reduce coordination but needs bounded allocation, lease expiry/fencing and recovery rules.

Adding an API instance does not increase the capacity of one hot shared bucket. Adding a cache in front of allowed decisions can also let many requests reuse one allowance. Cache denials only with an explicit freshness rule; never reuse an allow as if it were a reusable token.

---

## 16. Security, fairness and useful telemetry

| Concern | Design response / observation |
| --- | --- |
| Forged scope or cost | Trusted auth and route policy; never raw tenant/cost headers |
| Credential churn | Stable subject scope; rotation shares quota |
| NAT/shared IP unfairness | Authenticated subject plus a separate coarse IP boundary if needed |
| Expensive operations | Server-selected cost or dedicated route/provider budget |
| Key-cardinality attack | Enrollment controls, bounded state, cardinality/rejection monitoring |
| Unequal traffic within one tenant | Per-subject policy plus explicit tenant-wide budget if required |
| Information leakage | Avoid exposing another tenant's usage; custom remaining is advisory |
| Unbounded metrics labels | Aggregate by route/policy/reason; do not label every subject or token |

Measure decision latency separately from business latency, allowed/denied/degraded counts, reason, dependency timeouts, busy errors, active keys, prune backlog, memory, hot-key skew and configuration mismatch. Alert on sustained fail-open, because apparent successful API traffic may hide enforcement loss.

For fairness, distinguish isolation from scheduling. Separate user buckets prevent one user spending another's per-user budget, but they do not guarantee equal service under a shared saturated database or worker pool. A shared tenant budget and a fair queue solve different problems.

Record policy versions and bounded error categories; never log bearer tokens. Sample traces should connect authentication, quota decision and work outcome without turning every decision into a costly synchronous analytics write. Billing-grade usage belongs in a separate durable event/ledger design.

---

## 17. Reproduce and interpret the verification

From the repository root:

```powershell
cd examples/system-design/module-6-rate-limiter
python verify.py
python author.py
python integrate.py
python validate_site.py
```

The recorded run used **Python {{PYTHON}}**, **SQLite {{SQLITE}}**, **{{OS}}**, on **{{DATE}}**. **{{TOTAL}} local checks passed**: {{COUNTS}}. The harness includes four competing worker calls, actual file-level writer contention and real loopback HTTP; it never assumes which concurrent caller wins.

`verification-results.json` records each named assertion and the exact observations embedded here. `content-validation.json` checks source/output fidelity and learning structure. `validation-summary.json` records the production site build, routes/search and cleanup. These prove the stated local behavior, not throughput, Redis semantics, a crash-recovery theorem or production readiness.

For optional manual inspection:

```powershell
python start.py
# Use the printed ephemeral loopback origin in another terminal:
curl.exe -i -H "Authorization: Bearer lesson-alice" http://127.0.0.1:PRINTED_PORT/api/read
curl.exe -i -X POST -H "Authorization: Bearer lesson-alice" http://127.0.0.1:PRINTED_PORT/api/write
# Ctrl+C in the server terminal closes the listener and removes its temporary DB.
```

The automated run closes its listener and SQLite connections, joins the workers/server thread and removes its owned temporary directory. Port 3000 and Docker remain stopped. The optional manual runner has real wall-clock refill; unlike deterministic checks, typing slowly can naturally refill credit between requests.

---

## 18. Interview question bank with answer direction

### Q1. What is a rate limiter and where does it run?

It decides whether an operation may be admitted under a budget over time. It can run at an edge, gateway, application or provider boundary; placement changes available identity, cost knowledge and failure isolation. More than one layer can protect different resources.

### Q2. Why is an in-memory map insufficient after adding API replicas?

Each process can grant its own full budget. Requests routed across replicas multiply burst and refill unless the contract is intentionally per-instance or budgets are allocated. A strict shared identity needs one logical authority or bounded coordinated allocations.

### Q3. What happens at a fixed-window boundary?

L requests just before a boundary and L just after can both be admitted. That satisfies each aligned window but permits a short burst near 2L. Ask whether that behavior fits the product promise.

### Q4. How does an exact sliding log differ?

It removes accepted timestamps outside the selected rolling interval and checks the retained count. It preserves timing distribution at a state/pruning cost. Define equality at the cutoff and avoid recording unlimited denials.

### Q5. Is a weighted sliding counter exact?

No. Two counters cannot recover all event timestamps. The 999/1500 ms example demonstrates underestimation and excess admission relative to the exact log. Choose it only when the approximation is acceptable.

### Q6. Explain token capacity and refill rate separately.

Capacity bounds stored burst credit; refill rate determines sustained replenishment. Capacity 30 and refill 5/second permit an initial 30-token burst followed by replenishment at five/second. That is not a strict rolling 30-per-second policy.

### Q7. Why use integer milli-tokens?

They preserve fractional refill with explicit units and avoid repeated binary floating-point drift. The scale and bounds must fit the engine's numeric representation. This fixture deliberately restricts rates and costs to whole positive tokens.

### Q8. How do you compute Retry-After?

Compute the missing credit divided by refill rate, round up, include any clock catch-up interval under the chosen model, then round up to HTTP seconds. The hint does not reserve capacity against other callers.

### Q9. Two API servers both admit the last request. What failed?

They likely separated read/check from update or used independent authorities. Put refill, comparison and charge inside one authority-side atomic operation, using the same identity and policy. Verify the race with two real independent connections and a synchronized start.

### Q10. Does atomic INCR alone solve the entire limiter?

It solves an increment race, not every policy. You still need the count convention, expiry attachment, conditional admission, time, scope and failure contract. A check followed by INCR can over-admit; an increment-first scheme may intentionally count denials.

### Q11. Which identity should a quota key contain?

Use the product's budget owner, such as stable tenant/subject/route class, derived from trusted auth and routing. Raw API key rotation, client-selected tenant fields or raw URLs can bypass or fragment the intended quota.

### Q12. Why not rely only on client IP?

Many users share NAT addresses, while one actor can use many addresses. Forwarded headers also require a trusted proxy boundary. IP can be useful for coarse unauthenticated protection alongside authenticated budgets.

### Q13. Should failed requests consume quota?

Define “failed.” This fixture rejects authentication/input before quota and charges every successful admission, even if work later returns 500. Another product may count attempts or completed effects, but refunds and retries need stable accounting rules.

### Q14. What if cost is greater than bucket capacity?

It can never be admitted under that policy. Reject the invalid cost/configuration or choose a different policy/route. Returning a finite retry interval would falsely imply waiting can fix it.

### Q15. What happens when the clock moves backwards?

Clamp to the stored high-water time so elapsed refill is nonnegative. This can delay legitimate refill until time catches up. Include that catch-up in a retry hint and do not claim the clamp fixes forward jumps or cross-machine clock skew.

### Q16. Can monotonic time simply be persisted in a shared database?

Not as an arbitrary epoch timestamp: its reference point is unspecified. Use it for local durations where appropriate; a shared persisted limiter needs a defined time authority and restart/failover semantics.

### Q17. Why not delete a bucket whenever memory is full?

Recreating a depleted bucket as full can grant extra requests. Expire only after reset is safe under the policy/time model, reject new keys, or explicitly accept approximate enforcement. Cardinality is an availability and abuse concern.

### Q18. How long should token-bucket state live?

A safe idle horizon covers the time to naturally refill the stored deficit. The fixture conservatively uses full-capacity refill time after the last decision. Engine expiry, policy changes, clock skew and eviction still need independent consideration.

### Q19. What should happen if Redis or the quota authority is down?

Choose by route and harm. Fail-open preserves availability while relaxing enforcement; fail-closed rejects before work. Distinguish 503 dependency unavailability from 429 known exhaustion, and monitor degraded mode explicitly.

### Q20. Can you cache an allow decision?

Reusing it admits several requests for one charge unless it represents an explicit token lease. A lease needs a finite allocation, ownership, expiry and recovery accounting. Ordinary cache reuse is unsafe for a strict per-request budget.

### Q21. How do per-user and per-tenant limits combine?

Specify whether all budgets must charge atomically. Independent checks can spend one budget and then fail another. Co-location, staged reservation/compensation or accepted partial charging are possible choices with different scale and failure properties.

### Q22. Why is one hot key difficult to shard?

All admissions for that strict budget need coordinated credit. More unrelated shards do not split that serialization point. Leased sub-budgets, a different scope or relaxed exactness may help, but each changes the contract.

### Q23. Can regions enforce a hard global quota while partitioned?

Not by each granting the full budget independently. One authority increases cross-region dependency; allocated regional budgets bound local grants but can strand capacity. State what happens when allocations cannot renew.

### Q24. Does a rate limiter prevent overload from slow operations?

Not alone. In-flight concurrency depends on arrival rate and operation duration. Use concurrency budgets, deadlines and bounded queues where needed, and test saturation rather than relying only on request rate.

### Q25. Token bucket versus leaky bucket: what should I say?

Explain the traffic behavior rather than relying on names. A token bucket permits stored burst credit. A shaping queue smooths departure, adding delay and queue-management requirements. Real products may offer configurable reject/delay modes.

### Q26. Is admission the same as an exactly-once business effect?

No. The quota decision can commit before the response or business outcome is known. Retries can spend another token. Business idempotency and durable outcome replay need their own atomic protocol.

### Q27. How do policy updates avoid accidental free bursts?

Do not blindly switch to a fresh versioned key and refill every user to full. Define a migration for balance, capacity, rate and rollout consistency. The fixture rejects active mismatches and leaves live migration unimplemented.

### Q28. What metrics distinguish a healthy limiter from hidden failure?

Track allowed, denied, unavailable and degraded-open separately, plus decision latency, contention/timeouts, active keys and policy mismatch. Aggregate labels; a metric per subject creates its own cardinality problem.

### Q29. What do the local tests prove, and what remains unproven?

They prove the recorded deterministic math, live SQLite serialization/rollback/reopen behavior and loopback HTTP contract for tested cases. They do not prove Redis cluster behavior, production auth, clock synchronization, failover durability or capacity at the hypothetical peak.

### Q30. Give a compact design answer and one justified growth step.

Start with trusted subject/tenant/route scope, a stated token-bucket contract and one atomic authority-side decision. Return explicit 429 hints and choose outage behavior per risk. If file-level writer contention becomes material, port the mechanism to a measured shared engine while preserving keys, units, expiry, policy and failure semantics.

---

## 19. A 45-minute mock and answer skeleton

**Mock prompt:** “Design a limiter for a multi-instance authenticated API. It must permit small bursts, protect expensive writes and behave deliberately when the shared quota store is unavailable. Two servers currently both admit the final request.”

| Segment | Minutes |
| --- | --- |
| Clarify owner, time window, burst and counting semantics | 5 |
| State invariants and estimate traffic/state/skew | 7 |
| Choose algorithm, API, key and schema | 8 |
| Trace atomic admission, rejection and retry | 10 |
| Inject race, clock jump, state loss and authority failure | 10 |
| Justify growth and state evidence limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I would scope a budget by trusted tenant, stable authenticated subject and server route class. A token bucket provides the agreed burst and refill behavior; it does not claim an exact rolling-window count. One authority atomically loads, refills, checks and charges credit with a controlled clock. Known exhaustion returns 429/no-store and rounded Retry-After, which reserves no future credit. Admitted failures remain charged under this contract. Authority failure is a separately monitored 503 or explicit fail-open choice by route. I would bound state, expire only after safe idle refill and test two contenders for one remaining token. Shared-engine or regional growth must preserve or explicitly relax that contract.

Use bank Q26/Q40 to probe the design. Explain why more API instances, a longer TTL, atomic increment alone or retries cannot automatically fix the original race.

---

## 20. Practice tasks

1. Clarify five ambiguous phrases in “100 requests/minute,” including owner, burst, window, failures and deployment scope. Write the resulting exact contract.
2. Recompute the daily-to-peak and state estimates for another workload. Include active-key skew and metadata/replica overhead without calling logical bytes measured memory.
3. Run the aligned-window timeline and the 1500 ms weighted-counter counterexample. Explain equality at the sliding cutoff and approximation error.
4. Trace milli-token arithmetic for capacity five, rate two and cost three. Calculate partial-refill denial and HTTP retry rounding without floating-point shortcuts.
5. Run the broken and atomic two-connection races. Identify the exact transaction boundary and explain why the persisted broken count hides over-admission.
6. Test backward time, a large forward jump and close/reopen. Describe the mechanism's protection and the distributed clock/state-loss cases it cannot fix.
7. Fill the one-key state cap and advance to just before/at safe cleanup. Explain why live eviction, arbitrary TTL and fresh policy keys can grant extra budget.
8. Inspect actual 429, failed admitted work, rotated credentials and untrusted forwarded headers. Explain which values own identity, route and cost.
9. Exercise injected and real-lock dependency failures. Defend the chosen read/write policies and propose a bounded emergency alternative with its changed guarantee.
10. Complete the 45-minute mock. Add per-tenant plus per-user budgets or two regions, specify atomicity/allocation and failure behavior, and mark all unimplemented extensions.

---

## 21. Completion checklist

- [ ] I can clarify owner, counting rule, burst and deployment scope.
- [ ] I can estimate decisions, active state and hot-key skew with units.
- [ ] I can distinguish fixed, exact sliding and approximate windows.
- [ ] I can derive token refill, weighted cost and rounded retry math.
- [ ] I can reproduce the broken final-slot race and atomic result.
- [ ] I can derive stable trusted scope without client-selected identity.
- [ ] I can explain clock rollback, forward jumps and time authority.
- [ ] I can explain safe idle expiry, state caps and restart limits.
- [ ] I can distinguish known exhaustion from authority unavailability.
- [ ] I can explain charged failures, retries and separate idempotency.
- [ ] I can justify multi-budget/region tradeoffs and useful telemetry.
- [ ] I can finish the mock while stating the local evidence limits.

---

## 22. Research references and continuation

Primary sources reviewed on {{DATE}}. All workload inputs, code, outputs, counterexamples and Q&As are authored teaching material. This chapter makes no measured claim about employer frequency and does not copy a third-party worked design.

| Primary source | Mechanism to verify |
| --- | --- |
| [RFC 6585 §4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4) | 429 semantics, optional retry hint and cache prohibition |
| [RFC 9110 Retry-After](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after) | HTTP date versus delay-seconds |
| [Redis INCR](https://redis.io/docs/latest/commands/incr/) | Counter patterns and increment/expiry failure gap |
| [Redis scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/) | Atomic execution, blocking and script lifecycle |
| [Redis TIME](https://redis.io/docs/latest/commands/time/) | Authority-side server time |
| [Redis Cluster](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) | Hash-slot constraints and distributed deployment boundaries |
| [SQLite transactions](https://sqlite.org/lang_transaction.html) | Immediate write acquisition and writer contention |
| [Python monotonic clock](https://docs.python.org/3.12/library/time.html#time.monotonic) | Local elapsed time and unspecified reference point |
| [Nginx limit_req](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html) | Concrete leaky-bucket burst/delay behavior |

Return to the [architecture roadmap](/docs/system-design), [A2: data/cache](/docs/system-design/data-caching-scaling), [A3: reliable workflows](/docs/system-design/reliable-workflows-concurrency), [A4: operations](/docs/system-design/secure-observable-operations) or [S0: URL shortener](/docs/system-design/url-shortener). Resume [M7: authentication](/docs/resume-skills/authentication-sessions-jwt-oauth), [M8: authorization/security](/docs/resume-skills/api-security-authorization-multi-tenancy) and [M15: caching/background work](/docs/resume-skills/caching-background-jobs-data-ingestion) supply stack refreshers.

**Next: [S2 — Notification and webhook delivery service](/docs/system-design/notifications-webhooks)**, architecture part 9 / numeric module 7. It develops durable delivery attempts, preferences, provider limits, signatures, retries and duplicate-effect handling, with its own local SQLite/signed-HTTP verification scope. S0-S2 are authored; remaining worked systems and architecture consolidation continue one section at a time.
'''

for name, tag in [('estimates.py', 'ESTIMATES'), ('algorithms.py', 'ALGORITHMS'),
                  ('limiter.py', 'LIMITER'), ('http_api.py', 'HTTP_API')]:
    chapter = chapter.replace('{{'+tag+'_CODE}}', code(name))
for name in outputs:
    chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}', output(name))
for tag, value in [('DATE', proof['verified_date']), ('PYTHON', proof['python']),
                   ('SQLITE', proof['sqlite']), ('OS', proof['os']), ('TOTAL', str(proof['total'])),
                   ('COUNTS', ', '.join(f"{n} {name.replace('_', ' ')}" for name, n in proof['counts'].items()))]:
    chapter = chapter.replace('{{'+tag+'}}', value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-8-module-6-rate-limiter.md'
(ROOT/'System Design Notes'/filename).write_text(chapter, encoding='utf-8')
metadata = {'label': 'S1', 'chapter': filename, 'words': len(chapter.split()),
    'lines': chapter.count('\n'), 'questions': 30, 'practice_tasks': 10,
    'unchecked_learning_items': 12, 'source_fidelity': sources, 'output_fidelity': outputs,
    'mock_minutes': 45, 'verified_checks': proof['total'],
    'next': 'S2: Notification and webhook delivery service'}
(BASE/'content-validation.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
print(json.dumps(metadata, indent=2))
