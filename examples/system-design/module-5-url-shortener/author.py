"""Generate S0's worked design with exact runnable sources and observed local evidence."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
sources = ['estimates.py','shortener.py','service.py','http_api.py']
outputs = ['estimates','allocation','concurrency','expiry_and_disable','analytics','http_contract']


def code(name):
    return '```python\n'+(BASE/name).read_text(encoding='utf-8')+'```'


def output(name):
    return '```json\n'+json.dumps(proof['observations'][name],ensure_ascii=False,indent=2)+'\n```'


chapter = r'''# Architecture and System Design Placement Handbook — Part 7
# S0: URL Shortener

**Estimated time: 3–4 hours | Architecture numeric module: 5 | Requires: A0–A4; Resume M6/M13 refreshers**

---

## Why this module exists

“Build a URL shortener” looks like a map from short code to long URL. A useful design must also explain who can create/manage links, which code namespace is unique, what happens when allocation collides or a response is lost, how expiry interacts with caches, and whether analytics can delay redirects.

This first worked system combines the [architecture foundations](/docs/system-design) into a real local SQLite authority and loopback HTTP API. It implements create/replay, public GET/HEAD redirects, owner-scoped management/disable/statistics, a bounded process-local cache and explicitly best-effort analytics. It exercises forced collisions and concurrent operations rather than relying on random luck to demonstrate correctness.

**Organizing principle: make the code mapping authoritative, make create retries stable, and protect redirect correctness before optimizing its data path.**

This fixture uses Python/SQLite for reproducible local mechanism tests, following [A1's framework boundaries](/docs/system-design/application-architecture-service-boundaries). A deployed Node/Express/PostgreSQL version would preserve the contracts but require its own driver/transaction/transport tests. No Redis, CDN, cloud deployment, production authentication/TLS or throughput benchmark is included.

The 30 Q&As are editorial practice. URL shortening appears in the repository's previously researched design catalogs; this chapter does not claim a measured employer-frequency rank. It answers bank Q25 and collision/retry follow-up Q39. S1 onward remain separate worked designs.

---

## 1. Prompt and clarification questions

**Prompt:** learners create short links to approved study resources. Anyone possessing a code can follow it; only its creator can inspect management data, disable it or view its recorded redirect statistics.

| Clarification | What changes if the answer differs? |
| --- | --- |
| Are redirects public or authenticated/private? | Read-path permission checks, caching and code-secrecy assumptions |
| One short domain or tenant/custom domains? | Global versus domain-scoped uniqueness and routing |
| May owners edit destinations or only disable links? | Cache invalidation, versioning and replay semantics |
| Required expiry, retention and code reuse? | Absolute deadline checks, tombstones and old-link safety |
| Random code or custom alias? | Allocation conflict contract, namespace abuse and reserved names |
| Open destinations or curated allowlist? | Abuse policy, parser validation and moderation workflow |
| Approximate popularity or billing-grade analytics? | Loss tolerance, durable events, dedupe and critical-path cost |
| What read/write volume, skew and latency objective? | Cache benefit, hot keys, capacity testing and growth stages |

State assumptions before adding components. A public redirect is different from a private document link: the code is a publicly usable identifier in this design, not proof that a visitor is authorized to a separate destination resource.

---

## 2. Scope, promises and invariants

| Area | Chosen contract |
| --- | --- |
| Create | Published lesson credential, stable owner/tenant operation key, URL and optional integer lifetime |
| Namespace | One global case-sensitive eight-character Base62 code namespace |
| Destination | Immutable exact accepted HTTPS URL; curated host allowlist in this fixture |
| Lifetime | Default 3600 seconds; accepted range 1–86400 seconds; fixed at successful creation |
| Redirect | Public GET/HEAD `/r/:code`; active unexpired link returns 302 and Location |
| Management | Creator/tenant-scoped get, disable and recorded-statistics routes |
| Disable | Idempotent local transition; local cache invalidated; independent caches can lag |
| Analytics | Bounded local admission, lossy on overflow/write failure/restart, recent minute aggregates |
| Exclusions | Custom domains/aliases, destination editing, URL preview fetching, authenticated redirects, deletion/code reuse, durable analytics, global deployment |

The invariants are concrete:

- A committed code must never silently switch from one link to another because of a collision.
- Equivalent retries of one successful scoped create return its original code, URL and expiry.
- A warmed local cache must not redirect at or after the link's absolute expiry under the fixture's clock.
- A caller cannot manage or inspect another owner's link by guessing the global code.
- Analytics work is bounded and its chosen loss policy is visible; a count is not silently labelled unique human visits.

The system does not promise immediate global disable across independent caches. The test deliberately demonstrates that gap. A stricter abuse-takedown or private-access requirement would change the read path; do not hide that change behind the word “invalidation.”

---

## 3. Workload, storage and code-space estimates

The hypothetical inputs are 10,000 creates/day, 1,000,000 redirect requests/day, a selected 10× peak multiplier and 365 days of new links. They are planning assumptions, not production traffic or measured capacity. Logical record size is assumed to be 512 bytes, excluding several forms of overhead.

`estimates.py` computes the units and namespace arithmetic:

{{ESTIMATES_CODE}}

Observed calculated output:

{{ESTIMATES_OUTPUT}}

Average redirect rate is about 11.57/s and the assumed peak about 115.74/s. These numbers do not mean an instance can handle that rate. One year produces 3.65 million links and 1,868,800,000 logical bytes under the selected record-size assumption; operation outcomes, indexes, replicas, backups and analytics are excluded.

Eight Base62 characters provide `62^8` possibilities and about 47.63 bits under uniform independent selection. For `n` allocated identities in a space `N`, expected colliding pairs are approximately `n(n−1)/(2N)` and the birthday approximation gives probability of any collision `1−exp(−pairs)`. The next draw's collision probability is instead about `n/N`.

At this assumed population, the chance of at least one collision somewhere is roughly 3%, while one next draw colliding is much smaller. That is why a large namespace can make retries cheap without making the uniqueness constraint optional. The code does not preallocate millions of links to test this probability; it computes the model and separately forces collisions in the actual database.

The 365-day volume is not an implemented retention/deletion policy. Expired/disabled codes remain stored and are never automatically reused. An unguessable private capability needs a separate entropy/access design; this public short code is not presented as a secret credential.

---

## 4. API contract and redirect semantics

| Route | Caller/input | Success | Selected failure |
| --- | --- | --- | --- |
| `POST /api/links` | Lesson bearer token, Idempotency-Key, JSON URL and optional ttl_seconds | 201, original representation, management Location and replay flag | 400 invalid, 409 changed intent, 503 allocation exhausted |
| `GET /api/links/:code` | Creator/tenant credential | 200, canonical management state | 401 credential absent/unknown, 404 invisible/absent |
| `DELETE /api/links/:code` | Creator/tenant credential | 204; sets disabled, repeated disable has same effect | 404 invisible/absent |
| `GET /api/links/:code/stats` | Creator/tenant credential | 200, recent recorded redirect decisions | 404 invisible/absent |
| `GET /r/:code` | Public visitor | 302, exact accepted target in Location, empty body | 404 unknown/malformed code, 410 expired/disabled |
| `HEAD /r/:code` | Public visitor | Same redirect headers, no body, excluded from analytics | Same lookup errors without response body |

Creation JSON accepts exactly `url` and optionally `ttl_seconds`. The caller cannot choose code, owner, tenant, current time or absolute expiry. `short_url` uses a trusted configured base, not the untrusted Host header. In the lesson response, `https://short.example` is an illustrative deployment origin; the actual local server prints its own loopback origin.

The fixture supports redirects only for GET/HEAD. A POST to `/r/:code` returns 405. A 302 indicates a temporary redirect with a Location target; 307 preserves method when redirecting methods where that matters. Permanent 301/308 behavior can be appropriate for a genuinely permanent promise, but conflicts with a product that expects later expiry/disable to be observed through the short route. [RFC 9110 redirect semantics](https://www.rfc-editor.org/rfc/rfc9110.html#name-302-found).

All fixture responses use `Cache-Control: no-store`. This deliberately prevents a compliant downstream cache from retaining the redirect response; it is separate from the application's own internal mapping cache. `no-cache` means revalidation policy rather than “store nothing.” Explicit HTTP cache directives matter independently of the selected redirect status. [RFC 9111 HTTP caching](https://www.rfc-editor.org/rfc/rfc9111.html).

Known expired/disabled identifiers return 410, while missing codes return 404. Both are explicit choices that reveal different public states; a product wanting uniform concealment could choose another contract. Neither error should leak owner metadata.

---

## 5. Data model, ownership and access paths

| Table | Key and role | Critical access |
| --- | --- | --- |
| links | Global code primary key; target, creator, timestamps, disabled state | Public lookup by code; management lookup by tenant+owner+code |
| operations | Primary key tenant+owner+key; input fingerprint and original result | Detect completed retry before allocating another code |
| counts | Primary key code+minute bucket; recent recorded aggregate | Owner checks canonical link, then sums selected recent buckets |

One global short-domain namespace requires global code uniqueness, not merely uniqueness within a tenant. Tenant ownership still protects management. With custom domains, a deliberate `(domain,code)` namespace could change the key; routing must then resolve the trusted domain identity consistently.

Targets and absolute expiry are immutable in this prototype. Disable is stored on the canonical row; expired/disabled rows are retained. This avoids an old distributed bookmark later redirecting to somebody else's new link after automatic code reuse.

The operation fingerprint binds the exact validated URL and requested duration. The stored original expiry is calculated once. Retrying ten seconds later does not grant another ten seconds of lifetime. Successful outcomes remain replayable after expiry or disable, while current management/public reads reflect canonical state.

The code primary key supports direct lookup; the operation primary key supports scoped retry. The small statistics fixture has a code/bucket key. Production listing, expiry cleanup and aggregate lifecycle queries would need measured access-pattern/index decisions rather than automatically adding every field to a composite index.

---

## 6. Smallest architecture and end-to-end traces

```text
Implemented local baseline:
management client -> HTTP adapter -> scoped create/management -> SQLite authority
visitor           -> HTTP adapter -> redirect service
                                       | local bounded mapping cache
                                       | miss -> SQLite code lookup
                                       + bounded volatile analytics queue
                                                -> explicit batch / optional local thread
                                                -> SQLite recent aggregates

Proposed deployment growth, not run here:
client -> TLS edge -> application replicas -> shared authoritative PostgreSQL
                                  | suitable shared/local cache policy
                                  + separately bounded analytics path if required
```

**Create trace:** credential maps to creator/tenant; allowed JSON/URL/duration/key are validated; a transaction finds an old outcome or tries a code insert; a collision retries within a bound; the link and original outcome commit together; then HTTP 201 is sent.

**Redirect trace:** validate code shape; check local cache; on miss read canonical mapping; enforce disabled/absolute-expiry state; try nonblocking analytics admission for GET; return 302/Location. The shortener does not request the destination. A browser may subsequently do so, but the verification client intentionally does not follow it.

**Disable trace:** authenticate creator; update only its owned canonical row; invalidate that service's local cached mapping; return 204. Another independently warmed cache has no broadcast invalidation and can still expose the old active state until refresh.

Analytics batch writes are outside the individual redirect's queue-admission step. The teaching service still shares locks/database resources during batch flushing; a deployed worker needs deliberate isolation and bounded dependencies to prevent analytics contention from harming redirect latency. “Asynchronous” alone is not proof of isolation.

---

## 7. Code allocation choices and collision policy

| Choice | Benefit | Trade-off / deciding requirement |
| --- | --- | --- |
| Random Base62 + unique insert | No central sequential generator; bounded collisions handled by authority | Occupancy/retry budget, randomness, retained namespace |
| Database sequence encoded Base62 | Straightforward uniqueness under the sequence authority | Predictable codes, generator/partition coordination |
| Truncated URL hash | Deterministic candidate for the same chosen normalization | Collisions, privacy/leakage, same URL may represent separate intents |
| Allocated code blocks | Reduce per-ID coordination for distributed creators | Block ownership, exhaustion, crash/unused ranges and migration |
| Custom aliases | Human-readable codes | Explicit 409 conflict, reserved names and abuse ownership |

The baseline selects eight random Base62 characters with `secrets.choice`, whose purpose is cryptographically strong random selection rather than simulation randomness. The tests inject deterministic candidates to make collisions reproducible; they do not measure random entropy or guess resistance. [Python secrets documentation](https://docs.python.org/3.12/library/secrets.html).

Do not “check whether the code exists” outside the insert and assume that prevents a race. Another writer can choose it after the check. The authority attempts an insert protected by the unique code key and retries only the code conflict. It never overwrites a different mapping.

The SQLite statement uses `ON CONFLICT(code) DO NOTHING`. It intentionally avoids a replacement strategy that could delete/replace the existing mapping. Different constraint/error categories should not all be mistaken for a random collision. [SQLite conflict handling](https://sqlite.org/lang_conflict.html).

The prototype permits at most five candidate attempts in one create transaction. Exhaustion returns 503 and rolls back without a false operation result. The same caller key can be retried later under a bounded request policy; monitoring frequent exhaustion would signal a broken generator, unusually full space or attack rather than a reason to loop forever.

---

## 8. Runnable authority and input policy

Files are under `examples/system-design/module-5-url-shortener/`. Four exact runnable sources are embedded. `shortener.py` defines the public code namespace, restricted destination policy, real SQLite allocation and scoped operation/management behavior.

{{SHORTENER_CODE}}

The host allowlist is intentionally narrow: example hosts and Python documentation. Only ASCII HTTPS URLs with an allowed host, no credentials, default/443 port and no whitespace/backslash/control-character ambiguity are accepted. Exact accepted path/query/fragment is preserved. This is a declared curated-resource policy, not a universal validator for every internationalized/public URL.

URL parsing is not complete validation; libraries can split strings that an application should still reject. Do not silently normalize query order or signatures when defining request equivalence or URL deduplication. [Python urllib.parse security notes](https://docs.python.org/3.12/library/urllib.parse.html).

The database uses `BEGIN IMMEDIATE` to serialize local writer transactions. It does not demonstrate PostgreSQL row-level locks or a multi-region allocator. A PostgreSQL port can use its own unique constraint and conflict handling, but must re-test concurrent insert/replay and transaction semantics in that engine. [PostgreSQL INSERT](https://www.postgresql.org/docs/18/sql-insert.html).

---

## 9. Two creators and lost-response recovery

The deterministic allocation test first creates `AAAAAAAA`, forces that candidate again, then allocates `BBBBBBBB` without changing the first target. Another case returns the same original create after closing/reopening SQLite. A controlled fault after link insertion rolls back both link and outcome.

{{ALLOCATION_OUTPUT}}

Two thread-owned independent SQLite connections then start together at a barrier. With different intents and the same first candidate, one inserts it and the other retries. With the same scoped operation key, one creates and the other replays the committed result.

{{CONCURRENCY_OUTPUT}}

Which different-intent caller wins the first candidate is deliberately not asserted. The assertions concern two distinct committed mappings, one collision and one successful effect for the duplicate-intent case.

If creation commits but its response is lost, repeating the same key/input returns the original representation. If the first transaction rolls back, the retry can allocate normally. Changing the key is a new intent. Operation history is persistent but has no retention/deletion job in this fixture; a deployed replay window needs an explicit storage/privacy policy.

---

## 10. Cache expiry and disable visibility

The local cache stores immutable mapping data under the global code and caps retained entries with LRU eviction. Its eligibility deadline is the earlier of local cache TTL and absolute link expiry. Every resolution also checks the absolute expiry before returning a destination.

```text
cache deadline = min(read start + cache TTL, link expires_at)
redirect allowed only while current time < link expires_at and link is not disabled
```

Observed expiry/disable behavior:

{{EXPIRY_AND_DISABLE_OUTPUT}}

A long local cache TTL cannot extend an absolute ten-second lifetime. At exactly expiry, the response is 410. Retrying create after expiry still returns the original expiry rather than renewing it.

Local resolve/fill/disable share a lock, so this service's disable invalidates its warmed mapping without a competing local stale fill. Two independent services/connections have independent caches: the other one can still serve an active mapping until refresh. This is the implemented visibility contract, not immediate global revocation or a hard worldwide staleness bound under arbitrary stalled loads/clocks.

For strict takedown, options include an authoritative state check, a reliably propagated version/deny decision with a defined recovery path, or removing unsuitable caches. Each adds dependency/capacity/availability cost. A short TTL reduces ordinary lag under assumptions; it is not a complete invalidation proof.

Redis key expiry can remove cached entries after a selected lifetime, but application-level link validity must remain in the mapping protocol and clock/freshness policy. This fixture uses local memory, not Redis expiration events or a shared-cache deployment. [Redis EXPIRE](https://redis.io/docs/latest/commands/expire/).

---

## 11. Runnable redirect/cache and analytics service

`service.py` owns local cache policy, code resolution and bounded analytics admission. GET decisions enqueue `(code,minute_bucket)` without blocking on a full queue; HEAD is excluded. A batch transaction updates recent aggregate rows and prunes old buckets when flushing.

{{SERVICE_CODE}}

No target URLs, IP addresses, user agents or referer values enter the analytics queue. This deliberately limits both data volume and privacy scope. The statistics endpoint checks canonical ownership before returning recorded counts for the code.

The queue is volatile. Overflow, process exit, controlled batch-write failure and stale queued events can lose analytics. Recent bucket cleanup runs when flushing, while reads filter their current window even before physical pruning. This is bounded-age recorded data, not a complete continuous cleanup service.

Stored counts accumulate recorded redirect decisions, not unique people, actual destination visits or billing-grade clicks. Bots, retries, previews and response-write failures can affect the relationship between a server decision and a user's navigation. If business requirements need durable/auditable analytics, use a different acceptance/completion/deduplication contract rather than relabelling this lossy count.

---

## 12. Runnable HTTP adapter and observed contract

The adapter maps management credentials, translates requests/results and exposes public redirect routes. All server instances bind to ephemeral loopback ports, and the verification client uses `http.client` without automatic redirect following.

{{HTTP_API_CODE}}

Observed HTTP behavior:

{{HTTP_CONTRACT_OUTPUT}}

The API verifies HTTP status, exact Location, trusted short-URL origin, empty redirect body, HEAD behavior, operation replay, scoped management/statistics, invalid inputs, expiry and repeated disable. No external destination request is made.

The published lesson-token map is not production authentication, current membership/revocation or TLS. Reuse the authority and operational boundaries from [A4](/docs/system-design/secure-observable-operations) when building a deployed version. Python's standard-library server is for this owned learning fixture, not public production service. [Python http.server](https://docs.python.org/3.12/library/http.server.html).

---

## 13. Analytics loss, backlog and failure policy

The analytics test makes five successful redirect decisions with queue capacity two. Only two fit; three are explicitly dropped. It records the accepted pair, injects a later database-write failure, verifies rollback of that batch and confirms redirects remain usable afterward.

{{ANALYTICS_OUTPUT}}

The design chooses redirect availability over exact popularity counts. That trade-off is acceptable only when the product promises best-effort statistics. Silent data loss would be wrong if these events represented paid clicks, usage credits or audit evidence.

The optional manual runner flushes periodically with a bounded batch thread. Verification invokes flushing explicitly to control failure/retention scenarios. Neither uses a durable message broker or the outbox/inbox protocol from A3. A durable event pipeline would need stable event identity, acceptance durability, consumer idempotency, retention and reconciliation.

Analytics writes still share the local authority's database and can contend with cold reads/creates. Separate workers/connections, aggregate batching, a distinct store and overload policies are growth choices to assess with measurements. A memory queue does not automatically isolate database I/O or guarantee eventual delivery.

---

## 14. Growth stages: add a component for a named bottleneck

| Stage / evidence | Proposed change | New obligation |
| --- | --- | --- |
| Baseline fits workload | One app + suitable authoritative DB; optional bounded local cache | Correct contracts, unique inserts, operation history, measurements |
| Repeated hot reads dominate source work | Suitable local/shared cache | Expiry, disable visibility, cold-cache load, stampedes and hot keys |
| Application CPU/connection saturation | More stateless app instances | Shared authority, pool budget, independent-cache policy and draining |
| Eligible reads can tolerate replica lag | Read replica routing | Create-read freshness, expiry/disable state and promotion policy |
| Dataset/write ownership exceeds one DB | Shard mappings by a chosen code/domain rule | Global allocation/routing ownership, migration and management lookups |
| Global latency dominates | Regional serving/CDN where compatible with redirect policy | Takedown/expiry consistency, routing, cache directives and operational control |
| Analytics competes with redirect work | Separate bounded/durable analytics path if required | Delivery/effect semantics, privacy, backpressure and aggregate freshness |

Do not add every row's component at the beginning. A code hash can place mappings, but an extremely hot code still creates a hot key even if codes distribute evenly. A shortener's tenant-owned management queries may cross shards if placement is by code; decide whether listing requires a secondary projection.

Read replicas can lag immediately after creation or disable. A visitor receiving a newly created link must have a defined read-after-create path, such as authority routing, an eligible replica/version policy or a cache filled from the committed result. A replica miss is not always proof that a code never existed.

A CDN introduces browser/edge state outside the application's local cache. The baseline sends no-store and does not configure a CDN. If edge caching is added, define max-age relative to expiry, purge/revalidation behavior, regional failure and abuse-takedown promises. A permanent cached redirect can reduce origin analytics and make later control harder.

No architecture drawing here proves internet-scale throughput, worldwide availability or global write consistency. Capacity requires the workload, arrival model, key skew, dependency limits, tail/error/freshness measurements and fault tests introduced in A4.

---

## 15. Security, observability and trade-offs

A URL shortener intentionally redirects to creator-chosen destinations, which creates phishing/abuse risk. The curated host policy is a fixture choice; an open service would need a documented moderation/reporting/takedown approach, creator abuse controls and an appropriate destination policy. Validation alone cannot make every third-party destination trustworthy. [OWASP redirects/forwards](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html).

The server never fetches destinations. Adding a preview crawler, safety scanner or metadata fetcher introduces SSRF and resource-processing risks; protect its network access, redirects, DNS/IP checks and budgets under a separate service contract. Do not assume the browser-facing redirect validator is a complete server-side fetch policy. [OWASP SSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

Routine logs suppress raw URLs, credentials and query strings. Proposed production metrics include create/replay/conflict/allocation-retry counts, redirect 302/404/410/5xx and latency, cache hit/miss/eviction/fill delay, expiry/disable propagation, source saturation and analytics drop/lag. Avoid one metric time series per code or destination URL; use bounded route/status/outcome dimensions and restricted investigation records where needed.

| Decision | Baseline choice | Alternative and deciding requirement |
| --- | --- | --- |
| Destination identity | New key means new link, even for same URL | Semantic URL dedupe needs normalization/ownership/lifecycle rules |
| Code creation | Random + authority uniqueness | Sequence/block generator if allocation requirements justify coordination |
| Redirect response | 302 + no-store, GET/HEAD only | 301/308 for a true permanent contract; cache directives still explicit |
| Invalid code state | 404 unknown, 410 known gone | Uniform concealment if public state disclosure is undesirable |
| Disable visibility | Immediate local invalidation, independent-cache lag | Stronger authority/propagation path for strict takedown |
| Analytics | Bounded lossy recorded decisions | Durable/audited events for billing/compliance/business needs |
| Storage | Real local SQLite learning probe | PostgreSQL/shared persistence and separate deployment testing |

Quota/rate limiting is not added again in this fixture. Use A4's controls and the upcoming S1 design for creator quotas, code-enumeration abuse and downstream capacity protection. Correct collision handling is not protection against an attacker exhausting resources.

---

## 16. How to build and run it

Verified on **{{DATE}}** using **Python {{PYTHON}}**, **SQLite {{SQLITE}}**, and **{{OS}}**. No third-party Python packages, Docker, Redis, PostgreSQL server or external credentials are needed.

From the repository root in PowerShell:

```powershell
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 'examples/system-design/module-5-url-shortener/verify.py'
```

Or run `python verify.py` from the fixture directory with Python 3.12 or later. To explore manually, run `python start.py`. It prints a loopback origin, starts a periodic best-effort analytics batch thread and keeps data only in that manual session. Ctrl+C closes the server/worker and removes the temporary database.

Use the printed local origin rather than following the illustrative short.example URL:

```powershell
$shortenerOrigin = 'http://127.0.0.1:PORT'
$shortenerHeaders = @{ Authorization = 'Bearer lesson-alice'; 'Idempotency-Key' = 'manual-create' }
$shortenerBody = @{ url = 'https://example.com/guide'; ttl_seconds = 60 } | ConvertTo-Json
$shortenerCreated = Invoke-RestMethod -Uri "$shortenerOrigin/api/links" -Method Post -Headers $shortenerHeaders -ContentType 'application/json' -Body $shortenerBody
$shortenerCreated
# Inspect 302/Location without following the destination:
curl.exe -s -D - -o NUL "$shortenerOrigin/r/$($shortenerCreated.code)"
# Owner management and recent best-effort statistics:
Invoke-RestMethod -Uri "$shortenerOrigin/api/links/$($shortenerCreated.code)" -Headers $shortenerHeaders
Invoke-RestMethod -Uri "$shortenerOrigin/api/links/$($shortenerCreated.code)/stats" -Headers $shortenerHeaders
```

`curl` without `-L` inspects the redirect rather than following it. Manual use can create different random codes; the recorded automated tests inject deterministic candidates and never visit any destination.

The build order is authority/schema first, then allocation/replay/rollback tests, then redirect/expiry, cache/disable policy, bounded analytics and HTTP translation. Add deployment/authentication/abuse controls only with explicit contracts and verification. A test of an exact local invariant is more useful than a diagram with unimplemented infrastructure boxes.

---

## 17. Failure drills and verification limits

**{{TOTAL}} local checks passed:** {{COUNTS}}. Four exact source files and six exact observation blocks are embedded. `verification-results.json` names every assertion and records the boundary of the evidence.

| Scenario | Implemented outcome | Further requirement if scope changes |
| --- | --- | --- |
| Same code candidate in two creates | Authority uniqueness, loser retries, no overwrite | Multi-region ownership/consensus if writes distributed |
| Same create key concurrently | One mapping and one replayed original result | Durable operation lifecycle/retention policy |
| Fault after link insert | Local transaction rollback, no false outcome | Storage/process-kill durability and recovery configuration |
| Retry after expiry/disable | Original create result; current redirect stays gone | A distinct renewal/update operation if needed |
| Cache warm at expiry | Absolute deadline still enforced | Distributed clock/freshness assumptions |
| Disable on another instance | Warmed independent cache can lag | Strong takedown protocol if required |
| Analytics queue/write failure | Explicit loss, redirect remains usable | Durable delivery if counts become business-critical |
| Unknown owner/tenant | Management/statistics/disable rejected | Real identity/membership and permission model |

Verification closes its owned HTTP server, joins all handler/serving threads and four competing calls, closes SQLite connections and removes its exact temporary database directory. Port 3000 is not used. The optional manual runner is separate from the deterministic verification protocol.

No destination network traffic, cloud service, Redis/CDN, multi-host cache coherence, production authentication/TLS, exact human analytics or sustainable throughput capacity is verified. Distinguish a direct database race from a worldwide guarantee and a calculated namespace probability from observed random failures.

---

## 18. Common interview questions with answer checkpoints

### Q1. What would you clarify first for a URL shortener?

Public/private redirects, domain namespace, target editing/disable/expiry, custom aliases, destination policy, analytics accuracy and workload/freshness. These choices determine permissions, keys, cache semantics and recovery rather than just code length.

### Q2. What is the core correctness invariant?

A code must identify one committed mapping in its declared namespace without collision overwriting. Creation retries must refer to the same successful intent/result. Expiry and management scope add separate read/lifecycle invariants.

### Q3. Is code uniqueness global or per tenant?

For one short-domain namespace it is global, because a public request only supplies the code. Tenant/owner still protect management. Custom domains can support a domain-plus-code key if routing and domain authority are designed consistently.

### Q4. Why choose random Base62 codes?

They provide a large compact space without a central sequential allocator, while the database handles actual uniqueness. Randomness does not eliminate collisions. A sequence or allocated blocks can be valid alternatives under different coordination/guessability requirements.

### Q5. Is Base62 encoding encryption?

No. It represents values with sixty-two symbols. A sequential ID encoded in Base62 remains predictable. This public short code is not claimed to be a private capability or a credential.

### Q6. How long should the code be?

Choose from namespace population, growth, collision/retry budget, guessing risk and URL usability. The eight-character example computes its space and collision model, then relies on unique inserts. It does not claim a universal best length.

### Q7. Why distinguish birthday collision probability from next-draw risk?

The former asks whether any pair collides across a population; the latter asks whether the next candidate is already occupied. A modest chance of at least one collision can coexist with a tiny per-create retry probability. Both use explicit uniform-selection assumptions.

### Q8. How do you handle a collision safely?

Attempt the unique insert and retry only the code conflict within a bound. Do not replace the existing mapping or rely on a separate exists check. The fixture forces one collision and verifies the original destination remains unchanged.

### Q9. What if two servers choose the same code simultaneously?

The authoritative uniqueness boundary accepts one and the other tries another candidate. Two independent SQLite connections exercise this locally. A multi-region architecture needs a defined authority/ownership protocol; local results are not proof of it.

### Q10. How do retries avoid creating two links?

Keep a tenant/owner-scoped operation key, bind exact input/duration and atomically store the mapping plus original result. Concurrent equivalent requests return one code, with one replay. A fresh key represents a fresh intent.

### Q11. Should the same long URL always get the same short code?

Not in this contract: different keys can create independent lifetimes/owners/analytics. Semantic deduplication needs normalization, ownership and lifecycle decisions. Hashing the URL does not remove collisions or settle those product questions.

### Q12. Why return 302 instead of a permanent redirect?

This product expects expiry/disable to be observed through the short route. It uses a temporary GET/HEAD redirect with explicit no-store. Permanent redirects and method-preserving variants serve different promises; status alone is not the whole caching policy.

### Q13. Does a redirect require the server to fetch the long URL?

No. It returns Location and the client may navigate afterward. The test client never follows destinations. Adding previews or safety fetches introduces SSRF, DNS/redirect and resource-budget requirements absent from this baseline.

### Q14. What destination validation is implemented?

Curated ASCII HTTPS URLs for allowed hosts, default/443 ports, no userinfo/whitespace/backslash/control ambiguity, exact accepted string preserved. This is not general internationalized-URL validation or a guarantee that third-party content is harmless.

### Q15. How is expiry enforced with a cache?

The mapping includes absolute expiry; cache eligibility is capped by it and resolution checks current time before returning. At equality the link is gone. Cache key expiry alone is insufficient to define business validity across stale sources/clocks.

### Q16. Can create retry extend a lifetime?

No. It returns the original stored expiry. If renewal is needed, design a separate operation/version contract. The fixture verifies that retrying an already expired create neither renews nor reallocates it.

### Q17. Should expired codes be reused?

Only under an explicit policy that accounts for old bookmarks, cached redirects and operation replay. This baseline retains expired/disabled codes and never reassigns them. Deletion/retention is not implemented by the annual storage estimate.

### Q18. Does disabling locally revoke every cached redirect?

No. The local cache is invalidated, but an independent warmed cache has no broadcast and can lag. Strict takedown requires stronger authority/propagation or removing an unsuitable cache. The test exposes the gap instead of claiming global coherence.

### Q19. Why not cache all redirects in a CDN immediately?

It changes expiry, takedown, origin-observed analytics and failure behavior. The baseline sends no-store. Add edge caching only with an explicit freshness/purge/control contract and measurements showing its benefit.

### Q20. How do read replicas affect new links and disable?

Replication lag can make a new code appear absent or a disabled link appear active. Route freshness-sensitive reads to authority or a source meeting the required state/version contract. A replica miss is not always authoritative absence.

### Q21. How would you shard mappings?

Choose code/domain placement with a stable routing/ownership rule, then handle allocation, migration and cross-shard management queries. Hashing keys does not split one very hot code's traffic. S10 deepens placement and cache infrastructure.

### Q22. What happens if analytics is slow or unavailable?

The selected queue is bounded and lossy; overflow/write failure can drop recorded decisions without suppressing future redirects. Shared database/locks can still create contention. Durable or isolated analytics needs additional design rather than an “async” label.

### Q23. Are these counts unique human visits?

No. They are recorded GET redirect decisions, excluding HEAD under this fixture contract. Bots, retries, previews, failed response delivery and destination behavior differ from a person visiting a page. No IP/device identity or unique-visitor algorithm is implemented.

### Q24. How would billing-grade analytics change the design?

Define a durable acceptance/effect boundary, stable event identity, deduplication, retention, fraud/bot policy and reconciliation. A volatile drop-on-full queue would not satisfy that promise. A3/S13 supply the relevant workflow/pipeline foundations.

### Q25. How do creators manage public codes safely?

Public resolution is intentional, while get/disable/stats require the trusted creator/tenant principal and scoped canonical query. A guessed code must not reveal management metadata or grant mutation. Production needs actual credential/membership policy.

### Q26. Why use a trusted short-URL base?

Reflecting an arbitrary Host header can produce attacker-chosen advertised links. The fixture builds responses from configuration and tests that boundary. Real custom domains require verified domain ownership and routing policy.

### Q27. What should you monitor?

Create/replay/conflict/collision rates, redirect outcome/latency, expiry/disable lag, cache/source saturation and analytics loss/lag. Use bounded dimensions and restricted diagnostics. A count per destination URL as a metric label can create privacy and cardinality problems.

### Q28. What do the capacity estimates establish?

Hypothetical volume/rate/storage and code-space consequences under stated assumptions. They exclude substantial overhead and do not measure instance throughput. The prototype verifies mechanisms, not a cloud deployment or global availability.

### Q29. When would you add services, caches or queues?

After naming the bottleneck and correctness/freshness requirement. Independent analytics work, regional latency or a measured data boundary may justify change. More components also add failure, consistency and operational obligations.

### Q30. What does the worked example prove?

Local code uniqueness/replay/rollback, two-connection races, real HTTP redirects without target fetches, cache expiry/local disable, scoped management and bounded lossy analytics. It does not prove production identity/TLS, distributed cache coherence, durable analytics, PostgreSQL isolation or global capacity.

---

## 19. Revision sheet and a 45-minute mock

| Prompt | Recall |
| --- | --- |
| Namespace | One global code key for one short domain |
| Allocation | Random candidate + unique insert + bounded retry; never overwrite |
| Retry | Scoped key + exact input/duration + original result in same transaction |
| Redirect | GET/HEAD, 302/Location, explicit no-store, no server destination fetch |
| Expiry | Absolute link deadline checked independently of cache |
| Disable | Owned canonical transition + local invalidation; other caches can lag |
| Analytics | Recorded decisions, bounded/lossy admission and recent buckets |
| Security | Destination policy, owner management, trusted advertised base and abuse controls |
| Growth | Measured bottleneck; source/cache/replica/CDN consistency obligations |
| Evidence | Real local HTTP/SQLite; computed assumptions remain assumptions |

**Mock prompt:** “Design a URL shortener with expiring links, owner disable and basic popularity statistics. Two creators can choose the same code and clients retry after a timeout.”

| Segment | Minutes |
| --- | --- |
| Clarify public/private scope and lifecycle | 5 |
| State invariants and calculate workload/code space | 7 |
| Specify APIs and canonical schema | 8 |
| Trace allocation/retry and redirect/cache | 10 |
| Inject collision, expiry, disable lag and analytics failure | 10 |
| Justify growth, monitoring and evidence limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I will use one global code namespace with an authoritative unique key. Authenticated creators retain an owner/tenant operation key, and creation atomically stores the link plus its original outcome. Random candidates can collide, so insertion—not a separate precheck—decides acceptance and retries are bounded. Public GET/HEAD returns a temporary redirect without fetching the destination. Cache entries carry absolute expiry; disable is immediate locally but other caches need an explicit freshness/takedown protocol. Popularity is best-effort recorded decisions in this baseline, with visible drop metrics. I would add shared caching, replicas or durable analytics only for a measured need and a clear consistency contract.

Check that you distinguished per-draw collision risk, original operation result versus current state, downstream HTTP caching versus internal mapping caching, and recorded redirect decisions versus actual human visits.

---

## 20. Practice tasks

1. Clarify private redirects, custom domains, target editing, custom aliases and analytics accuracy. For each change, identify the affected key, permission or consistency promise.
2. Recompute code-space, birthday and next-draw probabilities for another length/population. Explain why a low next-draw probability does not remove the unique constraint.
3. Run the forced collision and two-connection race. Trace the candidate insert, losing conflict, retry and committed mapping without assuming which caller wins.
4. Reproduce concurrent same-operation create and close/reopen replay. Explain what changes if the caller chooses a new key or changes the requested duration.
5. Inspect GET/HEAD 302 responses without following them. Explain Location, body, no-store, method semantics and the trusted configured short origin.
6. Warm a cache just before expiry and check equality behavior. Then disable through one instance and explain the independent-cache visibility result and a strict-takedown alternative.
7. Fill the analytics queue, inject a failed batch and advance beyond bucket retention. Identify what is lost, what persists and why these counts are not human visits.
8. Design an unrestricted destination/preview extension with abuse controls and a separate SSRF-aware fetch boundary. Mark every feature not implemented by the curated fixture.
9. Propose a growth stage for hot-code traffic, replica lag or cross-region latency. Include cold-cache demand, disable/expiry correctness, pool budgets and needed measurements.
10. Complete the 45-minute mock and answer bank Q25/Q39. Defend one baseline choice against an alternative and state the evidence limit.

---

## 21. Completion checklist

- [ ] I can clarify namespace, public/private access and lifecycle.
- [ ] I can calculate workload/storage/code-space assumptions with units.
- [ ] I can explain birthday versus next-draw collision risk.
- [ ] I can trace unique insert and bounded allocation retry.
- [ ] I can explain stable scoped create replay under concurrency/restart.
- [ ] I can explain GET/HEAD redirect and explicit HTTP cache policy.
- [ ] I can enforce absolute expiry despite a warmed cache.
- [ ] I can distinguish local disable from cross-instance coherence.
- [ ] I can explain creator-only management/statistics on public codes.
- [ ] I can state the analytics loss/window/counting contract.
- [ ] I can justify a growth stage, security controls and useful measurements.
- [ ] I can complete a timed design mock and state the prototype's limits.

---

## 22. Research references and continuation

Primary references reviewed on {{DATE}}. Code, estimates and scenarios are authored examples. The repository's original plan/question bank supplies the learning route; this chapter does not invent a universal frequency ranking or copy a third-party worked solution.

| Primary source | Relevant mechanism |
| --- | --- |
| [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-302-found) | Redirect/Location and method semantics |
| [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) | Explicit HTTP caching policy |
| [Python secrets](https://docs.python.org/3.12/library/secrets.html) | Strong random selection API |
| [Python URL parsing](https://docs.python.org/3.12/library/urllib.parse.html) | Parser behavior and application validation responsibility |
| [SQLite conflicts](https://sqlite.org/lang_conflict.html) | Unique-insert conflict handling versus replacement |
| [PostgreSQL INSERT](https://www.postgresql.org/docs/18/sql-insert.html) | Port-specific conflict handling, not an executed engine here |
| [Redis expiry](https://redis.io/docs/latest/commands/expire/) | Cache lifetime as distinct from business validity |
| [OWASP redirects](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html) | Destination control and redirect abuse |
| [OWASP SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) | Separate risks when adding a server-side fetcher |
| [Python HTTP server](https://docs.python.org/3.12/library/http.server.html) | Local lesson server and production limitations |

Return to the [architecture roadmap](/docs/system-design), [A0: design method](/docs/system-design/design-method-estimation), [A2: data/cache](/docs/system-design/data-caching-scaling), [A3: workflows](/docs/system-design/reliable-workflows-concurrency) or [A4: operations](/docs/system-design/secure-observable-operations). Resume [M6: HTTP APIs](/docs/resume-skills/rest-apis-http) and [M13: PostgreSQL](/docs/resume-skills/postgresql-backend) provide stack refreshers.

**Next: [S1 — Rate limiter](/docs/system-design/rate-limiter)**, architecture part 8 / numeric module 6. It develops fixed/sliding windows and token buckets, atomic shared decisions, quota keys/clocks and degraded behavior, with its own local SQLite/HTTP verification scope. S0 and S1 are authored; remaining worked systems and consolidation continue one section at a time.
'''

for name,tag in [('estimates.py','ESTIMATES'),('shortener.py','SHORTENER'),('service.py','SERVICE'),('http_api.py','HTTP_API')]:
    chapter=chapter.replace('{{'+tag+'_CODE}}',code(name))
for name in outputs:
    chapter=chapter.replace('{{'+name.upper()+'_OUTPUT}}',output(name))
for tag,value in [('DATE',proof['verified_date']),('PYTHON',proof['python']),('SQLITE',proof['sqlite']),
                  ('OS',proof['os']),('TOTAL',str(proof['total'])),
                  ('COUNTS',', '.join(f"{count} {name.replace('_',' ')}" for name,count in proof['counts'].items()))]:
    chapter=chapter.replace('{{'+tag+'}}',value)
assert '{{' not in chapter
filename='system-design-handbook-part-7-module-5-url-shortener.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
metadata={'label':'S0','chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),
    'questions':30,'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':sources,
    'output_fidelity':outputs,'mock_minutes':45,'verified_checks':proof['total'],'next':'S1: Rate limiter'}
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
