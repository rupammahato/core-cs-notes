# Resume Skills Placement Handbook — Part 8
# Module 6: REST APIs and HTTP in Application Design

**Module 6 · 3–4 hours · Tier 1 · Requires: M0-M5**

---

## Why this module matters

M5 showed how a request reaches application code. This module decides what that request promises: which resource it addresses, how clients interpret success/failure, and what happens when requests overlap or repeat.

“Build a CRUD API” is only the starting point. An interviewer can ask why your client created two orders after a timeout, why pagination skipped a row, or why one user's edit silently replaced another's.

> **An API is a contract across a failure boundary. Design the resource, the observable response and the state invariant together.**

The example is a task API. Its small data model makes HTTP behavior visible without a database or framework hiding it. The same contracts apply when Express, Django or FastAPI handles the transport.

**Verification:** **68 HTTP checks passed on Node.js v22.14.0**. They exercise real loopback HTTP, state changes, overlapping requests and a deliberately incomplete request body. Clock-dependent cases inject a clock; they do not wait a minute or claim to measure network performance.

### Run the example

From the repository root:

```powershell
node examples/resume-skills/module-6-rest-http/verify.mjs
node examples/resume-skills/module-6-rest-http/start.mjs
```

The manual API listens on **127.0.0.1:3106**, separate from the notes website on port 3000. Stop it with Ctrl+C. There are no extra dependencies, external services or credentials.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3106/v1/tasks -ContentType application/json -Headers @{'Idempotency-Key'='learn-http-1'} -Body '{"title":"Learn HTTP","completed":false}'
```

This is a learning service with an in-memory store and a single shared demo scope. It has no authentication and loses state on restart. Its conditional-request handling covers the documented routes below, rather than implementing every HTTP feature or precondition combination.

---

## 6.1 API, HTTP and REST: distinguish the layers

An **API** is an interface another program can use. A library function can be an API without involving a network.

**HTTP** gives communicating programs a request/response protocol with methods, status codes, headers and representation semantics. HTTP/1.1, HTTP/2 and HTTP/3 have different transport/framing arrangements; application concepts such as GET and 404 remain useful across them.

**REST** is an architectural style. It is not another name for JSON, Express or every HTTP endpoint.

| Layer | Question it answers | Example |
| --- | --- | --- |
| Business capability | What may a user accomplish? | Record a task |
| Resource model | What is addressed? | A task collection and one task |
| HTTP contract | How is the interaction expressed? | POST collection; 201 with Location |
| Representation | What crosses the boundary? | JSON containing id/title/completed |
| Implementation | How does code perform it? | Router, validator, service and store |
| Deployment | Where does it run? | One process initially; more instances later |

A resource is the thing being identified; a representation is a particular description of it. The same resource could have different representations or change over time without changing its URI.

### REST constraints in plain language

Fielding's REST description combines client/server separation, stateless interaction, cache constraints, a uniform interface and a layered system; code on demand is optional. The uniform interface includes resource identification, representation-based manipulation, self-descriptive messages and hypermedia-driven interaction.

Stateless interaction means a request carries the context needed to understand it. It does not prohibit stored tasks, database rows or account records. Hidden conversational context such as “use whichever document this server remembers you opened last” makes requests dependent on server-side conversation state.

Hypermedia means representations provide links/actions that guide the client through available transitions. A JSON CRUD API with hardcoded client routes does not automatically demonstrate the full REST style.

Reference: [Fielding's original REST chapter](https://roy.gbiv.com/pubs/dissertation/rest_arch_style.htm).

**Interview line:** “Our service exposed an HTTP resource API using JSON. I would describe its actual methods, representations, cache behavior and links before claiming full REST conformance.”

---

## 6.2 Start with resources and invariants

For a task service, decide these before writing handlers:

- A task has a server-assigned immutable ID.
- A title is a non-empty string within a documented bound.
- completed is a boolean.
- Clients may write title and completed, while the server owns id.
- A successful edit must not silently overwrite a newer version.
- A retained creation key represents one creation intent.
- A page must have a bounded size and deterministic ordering.

These are application choices, not facts supplied by the word REST.

| Intent | Contract in this example |
| --- | --- |
| List tasks | GET /v1/tasks |
| Create a task | POST /v1/tasks |
| Read one task | GET /v1/tasks/7 |
| Replace writable state | PUT /v1/tasks/7 |
| Modify selected fields | PATCH /v1/tasks/7 |
| Remove a task | DELETE /v1/tasks/7 |
| Discover supported methods | OPTIONS on a known route |

Plural collection nouns are a useful convention, not an HTTP requirement. A consistent contract matters more than arguing whether a path must always use a plural word.

### Relationships and actions

A resource path can express ownership or a useful relationship:

```text
GET  /projects/42/tasks
GET  /tasks/7
POST /orders/12/cancellations
POST /report-jobs
GET  /report-jobs/94
```

Avoid forcing every operation into arbitrary database CRUD. A cancellation can be a domain action with eligibility checks, an audit record and a refund workflow. A cancellation resource makes those outcomes inspectable.

Deep nesting is rarely useful when the child already has a globally unique ID. More importantly, a parent ID in the path does not prove ownership. Data access must verify the relationship and the caller's permission in M7/M8.

### Path, query, body and headers

Use the path to identify the target, query parameters to refine a collection request, the body for a supported input representation, and headers for transport/representation conditions and credentials.

Do not put passwords or bearer tokens in query strings. URLs commonly travel through logs and histories. HTTPS protects transport; it does not erase application logs.

A GET body has no generally defined semantics. For ordinary list/search APIs, use documented query parameters. Complex search may need a separately documented operation with its own cache/retry contract.

---

## 6.3 Method semantics: safe, idempotent and cacheable

**Safe** means the client is requesting a read-only operation. Internal logging or metering can still happen. A GET that purchases a ticket violates that expectation even if your UI only calls it after a button click.

**Idempotent** means repeating the same intended operation has the same intended effect as performing it once. It does not promise byte-identical responses.

**Cacheable** concerns whether a response may be stored and reused under the relevant rules. It is a separate property.

| Method | Typical purpose | Safe? | Idempotent by method semantics? |
| --- | --- | --- | --- |
| GET | Retrieve a representation | Yes | Yes |
| HEAD | GET metadata without response content | Yes | Yes |
| OPTIONS | Communication options | Yes | Yes |
| POST | Process submitted input; often create under a collection | No | No general guarantee |
| PUT | Create/replace the target state | No | Yes |
| PATCH | Apply a specified partial modification | No | No general guarantee |
| DELETE | Remove the target association | No | Yes |

Reference: [HTTP method definitions](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods).

### PUT versus PATCH

In this API:

```json
{"title":"Revised","completed":false}
```

is a complete writable task representation for PUT. Omitting completed is rejected.

PATCH accepts a custom application/json object containing one or both writable fields. An omitted field stays unchanged; null is rejected. This is explicitly **not JSON Merge Patch**.

PATCH's meaning depends on its patch format. “Set completed to true” can be idempotent; “append this event” or “increment count” can repeat an effect. The whole patch must succeed atomically or leave the resource unchanged. See [PATCH semantics](https://www.rfc-editor.org/rfc/rfc5789.html).

**JSON Merge Patch** is a distinct format with media type application/merge-patch+json. Its null member values remove members; arrays are replaced as units. Do not label a custom “ignore missing keys” handler as compliant without implementing those rules. See [RFC 7396](https://www.rfc-editor.org/rfc/rfc7396.html).

### Why DELETE can return different statuses

The verified example returns 204 for the first removal and 404 for another attempt. The resource is absent afterward in both cases. That is compatible with idempotency.

A side effect such as “send a refund on every DELETE request” can break the intended guarantee. Repeating an HTTP request must not repeatedly trigger a logically one-time financial action.

Likewise, an idempotent method does not automatically make an implementation correct. A PUT handler that increments a balance on every call has misused the method.

---

## 6.4 Choose statuses by what happened

The status is useful to generic clients, gateways and monitoring. The body supplies application detail. Returning 200 with success:false for every failure discards that distinction.

| Code | Meaning useful in API design |
| --- | --- |
| 200 | Successful response with a representation |
| 201 | Resource created; identify it with Location when appropriate |
| 202 | Accepted for processing; completion is still pending |
| 204 | Successful response with no content |
| 304 | Conditional retrieval can reuse a stored representation; no content |
| 400 | Request cannot be processed because of a client request problem |
| 401 | Valid authentication is missing; requires an appropriate WWW-Authenticate challenge |
| 403 | Request understood but refused |
| 404 | Resource/route not found, or existence intentionally concealed |
| 405 | Target does not support this method; include Allow |
| 409 | Conflict with current application state |
| 412 | A supplied precondition evaluated false |
| 413 | Request content exceeds the accepted size |
| 415 | Request media type/content encoding unsupported |
| 422 | Syntax understood, but instructions/input cannot be processed |
| 428 | Server requires a conditional request |
| 429 | Request rate exceeds the applicable policy |
| 500 | Unexpected server failure |
| 502 | Gateway received an invalid upstream response |
| 503 | Service temporarily unavailable |
| 504 | Gateway timed out waiting for an upstream |

References: [HTTP status reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status), [428 and 429](https://www.rfc-editor.org/rfc/rfc6585.html).

### A status decision for this service

```text
POST task
  wrong body media type       -> 415
  malformed JSON              -> 400
  valid JSON, invalid task     -> 422
  valid task, missing key      -> 400 (our documented creation policy)
  retained key, new input      -> 409
  newly committed task         -> 201

PATCH task
  otherwise valid edit, no If-Match -> 428
  supplied tag no longer matches    -> 412
  valid conditional edit           -> 200 + updated task
```

Other APIs can consistently choose 400 for many validation failures. Explain your contract rather than claiming that every business rule has one universally mandatory code.

### 202 requires an asynchronous design

For a large report, a useful proposed contract is POST /report-jobs followed by GET /report-jobs/id. States might include queued, running, succeeded and failed.

Returning 202 does not make an in-process setTimeout durable. A reliable design must persist the job, arrange worker delivery and expose a recovery path. This task API does not implement jobs; M15 and the architecture track will.

### Client behavior matters

A client must not blindly call response.json() after every successful request. This example's 204 and 304 responses have empty bodies. A 304 is a cache-validation response, not a fresh task document.

For fetch, an HTTP failure generally produces a Response; it is not the same as a rejected network request. Check status/ok and parse according to the contract.

---

## 6.5 Headers are part of the contract

| Header | Role | Example use |
| --- | --- | --- |
| Content-Type | Format of the message content being sent | application/json |
| Accept | Response formats the client prefers/accepts | application/json |
| Location | URI associated with a created resource or redirect | /v1/tasks/1 after creation |
| Allow | Methods supported by the target | GET, HEAD, POST, OPTIONS |
| ETag | Validator for a selected representation | A quoted opaque value |
| If-None-Match | Conditional retrieval/other precondition semantics | Avoid downloading unchanged item |
| If-Match | Require a matching current representation | Protect a write |
| Cache-Control | Cache storage/reuse policy | private, no-cache |
| Retry-After | Delay/date associated with a later attempt | 2 seconds in the limiter case |
| Authorization | Credentials for the selected scheme | Bearer token in M7 |
| X-Request-Id | This example's correlation convention | Server-generated UUID |
| Idempotency-Key | This API's documented creation convention | learn-http-1 |

HTTP header names are case-insensitive. Node exposes incoming names in lowercase; do not make clients depend on display casing.

An ETag is opaque. Clients should preserve its quotes rather than parse a revision number out of it. The example hashes the exact JSON task representation and uses strong tags.

Idempotency-Replayed is a custom response header in this example. It is not required by HTTP or a guarantee supplied by Node.

### Content negotiation versus body validation

Content-Type says what you sent. Accept expresses what you can receive. A server supporting several response formats selects one; it can return 406 when it cannot satisfy the accepted formats.

Our service always responds with its documented JSON/problem JSON formats and does not implement Accept negotiation. It rejects unsupported request formats with 415. That narrower behavior is explicit.

Do not manually concatenate untrusted strings into header values. Use your framework/runtime's header API and validate any application value that contributes to a URI or redirect.

### OPTIONS is not automatically CORS permission

The example advertises methods using Allow and patch format using Accept-Patch. It does not add Access-Control-Allow-Origin or implement a browser CORS policy.

A browser cross-origin preflight is an OPTIONS request with specific CORS headers. Answering a plain OPTIONS successfully does not prove that a browser can read the subsequent response. CORS also does not authenticate the caller.

---

## 6.6 Parsing, validation and normalization

The boundary establishes facts in stages:

```text
bytes
  -> permitted encoding/media type
  -> bounded body
  -> valid UTF-8 and JSON syntax
  -> allowed object shape
  -> field types and bounds
  -> normalized writable input
  -> identity/permissions in M7/M8
  -> business/state conditions
  -> state change and public response
```

The example deliberately rejects arrays, null, unknown fields and string booleans. The string "false" is truthy in JavaScript; Boolean(input.completed) is not a suitable validator.

It trims titles before creating the fingerprint and task. Thus two supported inputs differing only in surrounding title whitespace represent the same normalized creation intent. Property order in incoming JSON also does not change that intent.

Normalization must be part of the documented domain rule. Trimming a task title is different from rewriting an opaque signed payload or changing a password.

### Bound the work as well as the value

The body allocation is capped at 2048 bytes. The reader continues consuming/discarding extra bytes before returning 413; it is not a bandwidth cap. A production edge needs total size enforcement, upload deadlines and a policy for stopping excessive bodies.

Titles have an 80-character limit measured here using JavaScript string length, which counts UTF-16 code units. This is not a Unicode grapheme-counting promise.

List limit is an integer from 1 to 5. Unknown or repeated query keys are rejected, so ?limit=1&limit=2 never silently depends on parser defaults.

A TypeScript interface does not perform these checks. See M3/M5 for the distinction between declared types and established runtime facts.

---

## 6.7 Give clients a stable error contract

This service uses application/problem+json with the Problem Details model. It uses about:blank for generic HTTP problem types and adds code/requestId extensions.

A problem has a status-consistent title and a safe detail message. instance identifies this occurrence, while type identifies the kind of problem. The custom code is the stable application label a client can use.

Reference: [Problem Details for HTTP APIs, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html).

A structural illustration, with placeholders rather than a captured UUID:

```json
{
  "type": "about:blank",
  "title": "Precondition Failed",
  "status": 412,
  "detail": "Task changed; fetch it and reconcile before retrying.",
  "instance": "urn:uuid:<server-generated-uuid>",
  "code": "stale_version",
  "requestId": "<same-server-generated-uuid>"
}
```

The verified suite checks that the actual response header, requestId and instance correlate. It also injects an internal failure and confirms that a private database message does not appear in the response.

Do not return a stack trace, SQL text or a provider secret to make debugging easier. Log appropriate internal context under the correlation ID. This example demonstrates safe public mapping; it does not implement a production log pipeline.

Clients should branch on status/code, not exact English wording. An error message may improve without changing the error's meaning.

---

## 6.8 Pagination, filtering and sorting

Returning every record has no natural upper bound. It can overload the database, serialization, network and client.

### Offset pagination

A common contract is ?limit=20&offset=40. It is simple and supports numbered pages, but changing rows can shift positions between requests. Large offsets can require substantial work before the database returns the requested slice.

Always define ordering. PostgreSQL explicitly warns that LIMIT/OFFSET without a predictable ordering can produce inconsistent subsets. See [PostgreSQL LIMIT/OFFSET](https://www.postgresql.org/docs/current/queries-limit.html).

Conceptual list, not a measured database query:

```text
Before: [1, 2, 3, 4, 5]
Page 1 offset 0 limit 2 -> [1, 2]
Delete task 1
Now:    [2, 3, 4, 5]
Page 2 offset 2 limit 2 -> [4, 5]   // task 3 skipped
```

### Keyset/cursor pagination

Our API orders by immutable id and continues strictly after the previous page's last ID. A deletion before the cursor does not change that comparison.

The cursor encodes after, completed and order. The server validates it against the current request. It does not store conversational page state.

The next URL preserves the filter/order, and the response supplies it both in JSON and a Link header. The server fetches the conceptual equivalent of limit+1 to know whether another page exists. In this in-memory example, it still scans/sorts the entire collection; it has no database index or performance guarantee.

Verified continuation:

```text
first page                 -> [1, 2]
delete an earlier item
follow next                -> [3, 4]
insert task 6
follow the next page        -> [5, 6]
```

The walk can see later insertions. **A cursor does not create a snapshot.**

### Stable ordering needs a tie-breaker

For a future database version sorted by created_at, use a unique tie-breaker such as id. Conceptually:

```sql
-- Proposed PostgreSQL shape; not executed in this module.
SELECT id, title, completed, created_at
FROM tasks
WHERE tenant_id = $1
  AND (created_at, id) > ($2, $3)
ORDER BY created_at, id
LIMIT $4;
```

The matching index, null policy, ordering direction and filter shape need actual database verification in M13. Sorting by mutable values can still move rows across a cursor, so explain the allowed consistency.

### Cursors are input, not permission

Base64url is an encoding. Our cursor is readable and unsigned. A caller can construct another valid cursor; it only changes the position in this public demo list.

In a tenant API, authorization filtering must apply independently on every page. Signing a cursor can protect integrity, but does not grant access or replace validation. If clients switch sort/filter, require a new cursor or explicitly define how that switch works.

---

## 6.9 Caching and conditional GET

HTTP caching stores representations of responses. It is different from putting arbitrary database objects in Redis.

| Directive | Practical interpretation |
| --- | --- |
| no-store | Do not store this response under the cache rules |
| no-cache | Storage is possible, but reuse requires successful validation |
| private | Shared caches must not store it |
| max-age=N | Freshness lifetime in seconds |
| public | Explicitly permits shared caching under the applicable rules |

Reference: [HTTP caching, RFC 9111](https://datatracker.ietf.org/doc/html/rfc9111).

The example uses private, no-cache for item retrieval and no-store by default for other responses. That makes the item validator flow visible without treating task data as public CDN content.

```text
client GET task
  <- 200 + JSON + ETag

client retains representation
client GET task with If-None-Match: <saved tag>
  <- 304 + ETag, empty body if still matching

client reuses its retained representation
```

The verifier explicitly sends headers and checks responses. Node fetch is not acting as a persistent browser cache in this test.

Vary tells a cache which request-header dimensions influence representation selection. If language or encoding changes the representation, validators and cache keys must reflect that. Adding authentication also requires a deliberate user/shared-cache policy.

Do not use a cached GET from a replica to decide whether a payment or inventory write is safe. Conditional writes must check authoritative state, not just a potentially stale representation at the edge.

---

## 6.10 ETags and lost updates

Two editors can read the same task and independently prepare changes:

```text
A reads title="Before", tag=E1
B reads title="Before", tag=E1
A submits title="A" with If-Match E1 -> succeeds, current tag E2
B submits title="B" with If-Match E1 -> 412
```

The client now fetches the current representation and asks the user to reconcile, or applies an explicitly safe merge. Blindly fetching E2 and retrying B's old replacement just hides the overwrite.

If-Match uses strong comparison. A weak tag does not establish the equality required for this edit guard. If-None-Match uses weak comparison for the demonstrated GET validator flow. See [conditional requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests).

### The compare and write must be atomic

This implementation parses/validates the entire body first. It then reads current state, compares the supplied condition and performs the Map update with no await in between.

```text
await body parsing/validation
read authoritative current task
check precondition
write updated task
```

Checking a tag before awaiting database/network work leaves a gap. “Node is single-threaded” does not close gaps across await.

The suite goes beyond two immediate edits. It starts one PATCH body, leaves it incomplete, completes another PATCH, and then finishes the earlier body. The slow request receives 412 and the fast editor's state survives.

### PUT normalization affects response validators

This API trims input and builds a stored representation with a server-owned ID. PUT therefore returns the updated JSON without an ETag. RFC 9110 prohibits sending a validator in a successful PUT response when the submitted representation was transformed. Read the resource with GET to obtain its current tag before another guarded edit. PATCH responses can supply the updated tag here. The suite checks this distinction and confirms repeated replacement leaves the same content-derived GET validator.

Reference: [RFC 9110, PUT](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.4).

### Database translation

A proposed database implementation might conditionally update where id, tenant_id and revision match, incrementing revision in the same statement/transaction. Inspect affected rows and distinguish missing/forbidden/stale according to the public contract.

That is a design sketch, not a PostgreSQL guarantee measured in this module. A JavaScript Map check is not shared across server processes.

If-Match: * checks existence rather than the exact version. Our service accepts it, so clients wanting protection against intervening edits must send the exact saved strong tag.

This content-hash ETag can repeat if the resource returns to the exact same representation. If a workflow must detect every intervening event, including change-and-revert, use an appropriate monotonic revision model in addition to representation equality.

---

## 6.11 Idempotency keys and duplicate creation

Consider a creation that committed, followed by a lost response:

```text
client -> POST task
server -> commits task
response -> not observed by client
client -> retries
```

The client cannot infer “nothing happened” from a timeout. A new uncoordinated POST can create another task.

Our contract requires a client-generated Idempotency-Key for POST /v1/tasks. One user intent keeps the same key across retries; a new intent gets a new key.

The in-memory record contains:

```text
scope + operation + key
  -> normalized-input fingerprint
  -> pending operation promise
  -> completed creation result
  -> expiry
```

The owner reserves the record before asynchronous creation work can yield. An overlapping retry with the same normalized input joins that promise. Different input under that key conflicts with 409, including while the owner is pending.

The suite holds creation behind a gate, proves the retry entered the replay path, then releases it. Both responses identify one task and the creation hook runs once.

### Replay is historical, not a fresh GET

A replay returns the original creation representation even if a later PATCH changed the task. The verifier checks this distinction. To obtain current state, follow Location with GET.

### The guarantee has a retention boundary

Completed records live for 60 seconds in this learning service. The injected-clock test demonstrates deduplication at 59,999 ms and a new task at 60,000 ms. The exact times are our chosen policy.

Pending records are not expired by this cleanup rule. A hung operation therefore needs cancellation/recovery bounds in a real service. Cleanup is lazy on creation requests, so this Map is not a general memory-management solution.

The example removes a failed record before retry because its injected failure occurs before the task write. That policy would be unsafe for an external payment whose outcome was uncertain.

Provider policies differ. Stripe's documentation describes its own key/result retention, parameter checks and failure behavior; those are not universal rules automatically inherited by every API. See [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests).

### Persist the effect and the record together

For a database-backed service, consider a unique constraint on verified tenant/user scope, operation and key; store the input fingerprint and result reference; coordinate the resource write with the idempotency record in a transaction.

For an external effect, a local transaction alone cannot atomically commit the provider's state. Use provider-side idempotency where supported, stable operation IDs, reconciliation and durable workflow records. M9 develops that problem.

The current Map implementation guarantees the demonstrated single-process behavior. It does not survive a restart, coordinate replicas or deliver universal “exactly once” execution.

---

## 6.12 Retry design: decide before looping

Retry only when both the failure is plausibly temporary and repetition is safe under the operation's contract.

| Situation | Useful next step |
| --- | --- |
| Invalid body/credentials/permission | Correct the request or identity; repeating unchanged input is unhelpful |
| 412 stale edit | Fetch and reconcile; do not blindly replay old replacement |
| 409 key/input conflict | Fix the intent/key association |
| 429 rate limit | Respect applicable delay and retry budget |
| Selected temporary 503/network failures | Consider bounded retry for a safe/idempotent operation |
| POST outcome unknown | Reuse the retained operation key or reconcile |
| Deadline already exhausted | Stop; report a useful outcome to the caller |

A retry policy needs a total deadline, maximum attempts, per-attempt timeouts and bounded backoff with jitter. Without jitter, many clients can retry together and overload a recovering dependency.

Retry-After can be a number of delay seconds or an HTTP date. Our limiter emits integer seconds rounded up. A real client must handle the form used by its provider, clock differences for dates and the remaining total budget.

Avoid independent retries at every layer without a shared budget. Browser, gateway, application and SDK retries can multiply downstream work.

An abort stops waiting/request activity at that boundary; it does not prove that the remote operation rolled back. Cancellation semantics must be explicit.

This chapter verifies server retry contracts. It does not ship or benchmark a generalized retry client. M2's cancellation examples and M9's integration workflows provide the next steps.

---

## 6.13 Rate limiting, quotas and concurrency

Rate limiting constrains activity over time. A quota constrains total consumption over a longer policy horizon. A concurrency limit bounds simultaneous work. They address related but different pressure.

The demonstration route GET /v1/limited has a global budget of two accepted requests per ten-second fixed window.

```text
window = floor(clock_ms / 10_000)
if window changed: reset count
if count already 2: return 429 + Retry-After
otherwise increment and accept
```

This uses one process-global bucket, deliberately separate from task routes. It is not a per-user production policy.

| Algorithm | Useful property | Trade-off |
| --- | --- | --- |
| Fixed window | Small counter state | Allows bursts around adjacent boundaries |
| Sliding log | Tracks a precise recent interval | Stores timestamps for many requests |
| Sliding-window counter | Approximates a moving interval | Boundary approximation |
| Token bucket | Allows configured bursts while refilling | Must coordinate token updates |
| Leaky-bucket/queue approaches | Smooth release rate | Queue delay and overflow policy |

The suite injects 8500 ms into the fixed-window clock, consumes the budget, and observes Retry-After: 2. At 10,000 ms the next window accepts a request. These are functional checks, not wall-clock measurements.

### Production placement

A gateway can protect all application instances, while application limits can enforce tenant budgets or expensive feature usage. Key policies by verified identity where appropriate.

Do not trust arbitrary X-Forwarded-For as a verified client IP. Proxy trust configuration must reflect the actual deployment. IP policies also have shared-NAT and IPv6 considerations.

Independent in-memory counters on several instances do not provide one global limit. A shared atomic counter/script, partitioned ownership or a dedicated limiter changes the architecture.

Decide what happens if the limiter store fails. Fail-open preserves availability but can overload dependencies; fail-closed protects resources but rejects legitimate users. The right choice depends on the operation and other safeguards.

A rate limit alone does not stop a few extremely slow or expensive requests. Add work bounds, concurrency control and deadlines where those risks arise.

---

## 6.14 Versioning and contract documentation

A path such as /v1/tasks makes this example's major contract visible. Header/media-type versioning is another option; URI versioning is not a requirement of REST.

Version when the externally visible contract needs an incompatible change. Renaming title to name, changing money units, narrowing a field's accepted values or removing a response property can break clients.

Adding an optional field is often compatible for tolerant clients, but strict deserializers and exhaustive enum handling can still break. Compatibility depends on the real consumer behavior.

Plan a migration: new contract, overlapping support, consumer communication, usage measurement and an explicit retirement policy. Do not put every code deployment under a new major API path.

### What an API specification should contain

For POST /v1/tasks, record:

- Required JSON format, fields, limits and normalization.
- Required key format, scope, replay/conflict behavior and retention.
- Success representation, 201, Location and validator.
- Error status/body contracts.
- Authentication/authorization once introduced.
- Examples and compatibility expectations.

OpenAPI describes HTTP API operations, parameters, request bodies, responses and security schemes. Documentation or generated client types do not make the server enforce those rules by themselves. Contract checks still need to exercise the actual boundary. See the [OpenAPI specification](https://spec.openapis.org/oas/latest.html).

We preserve executable checks and the contract table below rather than claiming an unvalidated OpenAPI document.

---

## 6.15 Build the small system before adding infrastructure

### Requirement and boundaries

Build a task collection with creation, reading, edits and removal. Support bounded list traversal, conditional editing and retained-key creation retries.

```text
HTTP client
  -> Node HTTP listener
      -> route/method selection
      -> query/body/condition validation
      -> task Map and idempotency Map
      -> JSON or Problem Details response

separate demonstration route
  -> fixed-window rate counter
```

All state is in one process. The file combines the responsibilities to keep the full mechanism visible. In an Express application, keep M5's controller/service/repository boundaries while preserving these invariants.

### Endpoint contract

| Route | Input | Success | Important failure |
| --- | --- | --- | --- |
| GET /v1/tasks | limit, completed, order, cursor | 200 items/next; optional Link | 400 invalid query/cursor |
| POST /v1/tasks | full task + Idempotency-Key | 201 task, Location, ETag | 409 changed input under key |
| GET /v1/tasks/id | optional If-None-Match | 200 task or 304 empty | 404 absent task |
| HEAD /v1/tasks/id | retrieval headers | GET metadata, empty body | 404 absent task, empty body |
| PUT /v1/tasks/id | full writable task + If-Match | 200 task; obtain validator via GET | 428 missing / 412 false condition |
| PATCH /v1/tasks/id | custom partial object + If-Match | 200 task, ETag | 422 invalid patch; 412 stale |
| DELETE /v1/tasks/id | If-Match | 204 empty | 404 already absent; 412 stale |
| OPTIONS known route | no body required | 204, Allow; item Accept-Patch | Unknown route 404 |
| GET /v1/limited | none | 200 remaining count | 429 and Retry-After |

Unknown routes return 404. Unsupported methods on recognized valid routes return 405 with Allow. Malformed IDs have a documented 400 path. Ordinary item routes do not accept query parameters.

### Request traces worth explaining aloud

Creation: parse -> normalize -> validate key -> find/reserve key record -> create once -> retain result -> respond.

Conditional edit: parse complete input -> read current task -> compare strong condition -> update without yielding -> return updated representation.

List: validate query/cursor -> apply filter -> continue after cursor -> deterministic sort -> bounded slice -> construct next URL.

Failure: classify known application error -> choose status/code -> return safe Problem Details with a new request correlation ID.

A request ID identifies one attempt. An idempotency key identifies one logical intent across attempts. They should not be treated as interchangeable.

---

## 6.16 Complete learning implementation

The authoritative runnable file is examples/resume-skills/module-6-rest-http/server.mjs. The following is that file, including the test seams used to control time and creation.

beforeCreate lets the verifier hold/fail a creation before any task write. onReplay lets it prove an overlapping retry entered the pending-record path. Production business code would use a real repository/workflow rather than those hooks.

```javascript
import { createServer } from 'node:http';
import { createHash, randomUUID } from 'node:crypto';

class ApiError extends Error {
  constructor(status, code, detail, headers = {}) {
    super(detail);
    Object.assign(this, { status, code, headers });
  }
}
const fail = (status, code, detail, headers) => {
  throw new ApiError(status, code, detail, headers);
};
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const etag = task => '"' + createHash('sha256').update(JSON.stringify(task)).digest('hex') + '"';

function tags(header) {
  if (header === '*') return ['*'];
  const result = [];
  let rest = header.trim();
  while (rest) {
    const match = /^(W\/)?"[\x21\x23-\x7e\x80-\xff]*"/.exec(rest);
    if (!match) fail(400, 'invalid_condition', 'Use an entity-tag list or *.');
    result.push(match[0]);
    rest = rest.slice(match[0].length).trimStart();
    if (!rest) return result;
    if (!rest.startsWith(',')) fail(400, 'invalid_condition', 'Invalid entity-tag list.');
    rest = rest.slice(1).trimStart();
    if (!rest) fail(400, 'invalid_condition', 'Trailing comma is not allowed.');
  }
  if (!result.length) fail(400, 'invalid_condition', 'Condition cannot be empty.');
  return result;
}

function validateTask(input, partial = false) {
  if (!object(input)) fail(422, 'invalid_task', 'Task input must be an object.');
  const keys = Object.keys(input);
  if (keys.some(key => !['title', 'completed'].includes(key)))
    fail(422, 'unknown_field', 'Only title and completed are writable.');
  if (partial && !keys.length) fail(422, 'empty_patch', 'Supply at least one writable field.');
  const result = {};
  if (!partial || Object.hasOwn(input, 'title')) {
    if (typeof input.title !== 'string' || !input.title.trim() || input.title.trim().length > 80)
      fail(422, 'invalid_title', 'title must contain 1 to 80 characters after trimming.');
    result.title = input.title.trim();
  }
  if (!partial || Object.hasOwn(input, 'completed')) {
    if (typeof input.completed !== 'boolean')
      fail(422, 'invalid_completed', 'completed must be a boolean.');
    result.completed = input.completed;
  }
  return result;
}

async function jsonBody(req) {
  if (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity')
    fail(415, 'unsupported_encoding', 'Compressed request bodies are not supported.');
  const media = (req.headers['content-type'] ?? '').split(';').map(s => s.trim().toLowerCase());
  if (media[0] !== 'application/json' ||
      media.slice(1).some(s => !/^charset="?utf-8"?$/.test(s)))
    fail(415, 'unsupported_media_type', 'Send application/json encoded as UTF-8.');
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size <= 2048) chunks.push(chunk);
  }
  if (size > 2048) fail(413, 'body_too_large', 'JSON body exceeds 2048 bytes.');
  try {
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
  } catch {
    fail(400, 'invalid_json', 'Body must contain valid UTF-8 JSON.');
  }
}

function listTasks(tasks, params) {
  for (const key of params.keys()) {
    if (!['limit', 'completed', 'order', 'cursor'].includes(key) || params.getAll(key).length !== 1)
      fail(400, 'invalid_query', 'Unknown or repeated query parameter.');
  }
  const limitText = params.get('limit') ?? '2';
  if (!/^[1-5]$/.test(limitText)) fail(400, 'invalid_limit', 'limit must be 1 to 5.');
  const limit = Number(limitText);
  const completed = params.get('completed');
  if (completed !== null && !['true', 'false'].includes(completed))
    fail(400, 'invalid_filter', 'completed must be true or false.');
  const order = params.get('order') ?? 'asc';
  if (!['asc', 'desc'].includes(order)) fail(400, 'invalid_order', 'order must be asc or desc.');
  let after = null;
  const cursor = params.get('cursor');
  if (cursor !== null) {
    try {
      const bytes = Buffer.from(cursor, 'base64url');
      if (!cursor || cursor.length > 512 || bytes.toString('base64url') !== cursor) throw Error();
      const parsed = JSON.parse(bytes.toString('utf8'));
      if (!object(parsed) || Object.keys(parsed).sort().join(',') !== 'after,completed,order' ||
          !Number.isSafeInteger(parsed.after) || parsed.after < 1 ||
          parsed.completed !== completed || parsed.order !== order) throw Error();
      after = parsed.after;
    } catch {
      fail(400, 'invalid_cursor', 'Cursor must match this filter and ordering.');
    }
  }
  const rows = [...tasks.values()]
    .filter(task => completed === null || task.completed === (completed === 'true'))
    .filter(task => after === null || (order === 'asc' ? task.id > after : task.id < after))
    .sort((a, b) => order === 'asc' ? a.id - b.id : b.id - a.id);
  const items = rows.slice(0, limit);
  let next = null;
  if (rows.length > limit) {
    const token = Buffer.from(JSON.stringify({
      after: items.at(-1).id, completed, order,
    })).toString('base64url');
    const query = new URLSearchParams({ limit: String(limit), order });
    if (completed !== null) query.set('completed', completed);
    query.set('cursor', token);
    next = '/v1/tasks?' + query;
  }
  return { items, next };
}

export function createTaskServer({
  now = Date.now,
  beforeCreate = async () => {},
  onReplay = () => {},
  idempotencyTtlMs = 60_000,
} = {}) {
  const tasks = new Map();
  const requests = new Map();
  let nextId = 1;
  let windowId = null;
  let used = 0;

  const server = createServer(async (req, res) => {
    const requestId = randomUUID();
    res.setHeader('X-Request-Id', requestId);
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, body, headers = {}) => {
      res.writeHead(status, {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }),
        ...headers,
      });
      res.end(req.method === 'HEAD' || body === undefined ? undefined : JSON.stringify(body));
    };
    try {
      const url = new URL(req.url, 'http://localhost');
      let pathname;
      try { pathname = decodeURIComponent(url.pathname); }
      catch { fail(400, 'invalid_path', 'Path encoding is invalid.'); }
      const collection = pathname === '/v1/tasks';
      const limited = pathname === '/v1/limited';
      const match = /^\/v1\/tasks\/([^/]+)$/.exec(pathname);
      if (!collection && !limited && !match) fail(404, 'not_found', 'Route does not exist.');
      let id;
      if (match) {
        if (!/^[1-9]\d*$/.test(match[1]) || !Number.isSafeInteger(Number(match[1])))
          fail(400, 'invalid_id', 'Task ID must be a positive safe integer.');
        id = Number(match[1]);
      }
      const allow = collection ? 'GET, HEAD, POST, OPTIONS'
        : limited ? 'GET, HEAD, OPTIONS' : 'GET, HEAD, PUT, PATCH, DELETE, OPTIONS';
      if (req.method === 'OPTIONS') return send(204, undefined, {
        Allow: allow, ...(match ? { 'Accept-Patch': 'application/json' } : {}),
      });
      if (!allow.split(', ').includes(req.method))
        fail(405, 'method_not_allowed', 'Method is not supported on this route.', { Allow: allow });
      if (!collection && url.search)
        fail(400, 'invalid_query', 'This route has no query parameters.');
      if (collection && !['GET', 'HEAD'].includes(req.method) && url.search)
        fail(400, 'invalid_query', 'Creation has no query parameters.');

      if (limited) {
        const current = Math.floor(now() / 10_000);
        if (current !== windowId) { windowId = current; used = 0; }
        if (used >= 2) fail(429, 'rate_limited', 'Demo global budget exhausted.', {
          'Retry-After': String(Math.max(1, Math.ceil(((current + 1) * 10_000 - now()) / 1000))),
        });
        used++;
        return send(200, { remaining: 2 - used });
      }

      if (collection && ['GET', 'HEAD'].includes(req.method)) {
        const page = listTasks(tasks, url.searchParams);
        return send(200, page, page.next ? { Link: '<' + page.next + '>; rel="next"' } : {});
      }
      if (collection) {
        const input = validateTask(await jsonBody(req));
        const key = req.headers['idempotency-key'];
        if (typeof key !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(key))
          fail(400, 'invalid_key', 'Supply an Idempotency-Key with 1 to 64 letters, digits, _ or -.');
        // A single loopback demo scope. Production scope must use verified identity.
        const scopedKey = 'demo:POST:/v1/tasks:' + key;
        const fingerprint = JSON.stringify(input);
        for (const [storedKey, record] of requests)
          if (record.done && record.expiresAt <= now()) requests.delete(storedKey);
        const prior = requests.get(scopedKey);
        if (prior) {
          if (prior.fingerprint !== fingerprint)
            fail(409, 'key_conflict', 'This key was used with different task input.');
          onReplay();
          const saved = await prior.promise;
          return send(201, saved.task, {
            Location: saved.location, ETag: etag(saved.task), 'Idempotency-Replayed': 'true',
          });
        }
        const record = { fingerprint, done: false };
        // Defer the operation so the record is reserved before beforeCreate can yield.
        record.promise = Promise.resolve().then(async () => {
          await beforeCreate();
          const task = { id: nextId++, ...input };
          tasks.set(task.id, task);
          record.done = true;
          record.expiresAt = now() + idempotencyTtlMs;
          return { task, location: '/v1/tasks/' + task.id };
        });
        requests.set(scopedKey, record);
        try {
          const saved = await record.promise;
          return send(201, saved.task, { Location: saved.location, ETag: etag(saved.task) });
        } catch (error) {
          requests.delete(scopedKey);
          throw error;
        }
      }

      const input = ['GET', 'HEAD', 'DELETE'].includes(req.method) ? null
        : validateTask(await jsonBody(req), req.method === 'PATCH');
      const task = tasks.get(id);
      if (!task) fail(404, 'not_found', 'Task does not exist.');
      const currentTag = etag(task);
      if (['GET', 'HEAD'].includes(req.method)) {
        const condition = req.headers['if-none-match'];
        const headers = { ETag: currentTag, 'Cache-Control': 'private, no-cache' };
        if (condition !== undefined && tags(condition).some(tag => tag === '*' || tag.replace(/^W\//, '') === currentTag))
          return send(304, undefined, headers);
        return send(200, task, headers);
      }
      const condition = req.headers['if-match'];
      if (condition === undefined) fail(428, 'condition_required', 'Send the ETag in If-Match.');
      // Comparison and write have no await between them in this one-process store.
      if (!tags(condition).some(tag => tag === '*' || tag === currentTag))
        fail(412, 'stale_version', 'Task changed; fetch it and reconcile before retrying.');
      if (req.method === 'DELETE') {
        tasks.delete(id);
        return send(204);
      }
      const updated = { id, ...(req.method === 'PATCH' ? task : {}), ...input };
      tasks.set(id, updated);
      // PUT normalizes/builds the stored representation, so omit response validators.
      return send(200, updated, req.method === 'PATCH' ? { ETag: etag(updated) } : {});
    } catch (error) {
      if (res.headersSent) { res.destroy(); return; }
      const known = error instanceof ApiError;
      const status = known ? error.status : 500;
      send(status, {
        type: 'about:blank',
        title: {
          400: 'Bad Request', 404: 'Not Found', 405: 'Method Not Allowed',
          409: 'Conflict', 412: 'Precondition Failed', 413: 'Content Too Large',
          415: 'Unsupported Media Type', 422: 'Unprocessable Content',
          428: 'Precondition Required', 429: 'Too Many Requests', 500: 'Internal Server Error',
        }[status],
        status,
        detail: known ? error.message : 'Unexpected server failure.',
        instance: 'urn:uuid:' + requestId,
        code: known ? error.code : 'internal_error',
        requestId,
      }, { 'Content-Type': 'application/problem+json', ...(known ? error.headers : {}) });
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
    }
  });
  server.requestTimeout = 10_000;
  server.headersTimeout = 5_000;
  return server;
}

```

The manual launcher imports createTaskServer and listens on 127.0.0.1:3106. The verifier instead chooses available ephemeral ports and closes every listener in a finally block.

The server assigns request IDs itself rather than trusting an arbitrary incoming ID. For a deployed service, validate any accepted upstream correlation context and keep it separate from authorization.

### What the reader intentionally does not implement

The body reader consumes the request before deciding 413, storing only the bounded prefix. It is chosen for a small learning API, not for production streaming uploads. Node handles HTTP framing; the application handles its documented JSON contract.

The service does not implement PUT creation, generalized content negotiation, range requests, a full HTTP precondition precedence engine, CORS, authentication, TLS termination or persistence. Those omissions define its scope and should be stated when explaining the implementation.

---

## 6.17 What was verified

Run verify.mjs for all **68 checks**. The result file records the Node version and each named observation; verification-output.txt preserves the console output.

| Area | What the checks establish |
| --- | --- |
| Input boundary | Format/encoding, malformed JSON, 2048-byte bound, shape, writable fields, title/boolean rules and key format |
| Creation | 201, Location, strong tag, normalized retry, conflicting key input and one stored task |
| Retrieval | Item projection, cache policy, HEAD, matching/nonmatching validators and empty 304 |
| Conditional writes | Missing condition, weak tag rejection, PUT/PATCH rules, changed tag and stale edit protection |
| Removal/methods | Empty 204, repeated DELETE 404, OPTIONS metadata, 405 Allow and invalid paths |
| Pagination | Bounds, query rejection, next Link, deletion/insertion behavior, filters, descending order and cursor binding |
| Concurrency | One winner for competing edits; slow-body stale edit rejected; overlapping creation retries share one pending operation |
| Failure/retention | Safe 500 before write, retry after that failure, deduplication before expiry and new creation after expiry |
| Rate limit | Two accepted requests, 429, rounded-up delay, task-route independence and window reset |

The concurrent creation check uses explicit gates. It waits for the owner to enter beforeCreate and for the retry to enter onReplay before releasing the operation. It does not infer overlap from a sleep.

Selected lines from the actual run:

```text
PASS normalized same-key retry replays original creation: {"id":1,"replayed":true,"total":1}
PASS stale editor cannot overwrite newer state: {"status":412,"completed":true}
PASS keyset continuation survives deletion before cursor: {"ids":[3,4]}
PASS keyset walk sees later insertion without duplicating earlier IDs: {"ids":[5,6],"snapshot":false}
PASS two concurrent editors produce one winner and one 412: {"statuses":[200,412],"storedMatchesWinner":true}
PASS write checks current state after a slow request body finishes: {"fast":200,"slow":412,"title":"Fast editor"}
PASS overlapping same-key requests share one operation: {"statuses":[201,201],"creations":1,"total":1}
PASS retained key deduplicates before expiry: {"id":1,"atMs":59999}
PASS expired key can create again: {"id":2,"atMs":60000,"total":2}
PASS unexpected failure returns private problem and permits retry: {"first":500,"retry":201,"attempts":2,"total":1}
PASS exhausted budget returns 429 and rounded-up Retry-After: {"status":429,"retryAfterSeconds":2}
Verified 68 HTTP checks; all temporary listeners closed.
```

### What a pass does not establish

No database, cache cluster, load balancer or third-party provider participates. The suite does not kill a process between commits, test multi-instance coordination, emulate browser caching/CORS, exercise launcher signals or benchmark throughput.

The unknown-outcome explanation describes a real distributed-systems risk. The tests verify retained-key behavior and overlapping requests; they do not physically drop a committed response on the network.

The test clock proves selected time-bound policies. It is not evidence of real timer precision or behavior under clock adjustments.

---

## 6.18 Evolve the architecture in response to a requirement

### Requirement: survive restarts

Replace the task Map with durable data. Store creation keys/results durably too. Moving only tasks to a database leaves a duplicate-creation window when the process loses its key Map.

Establish uniqueness and commit boundaries, then add crash/recovery checks. Persisted data introduces migrations, backups and operational ownership.

### Requirement: run several application instances

A request may reach a different instance on retry. Shared tasks with private idempotency Maps are insufficient. Coordinate the key reservation and effect through durable shared state.

The conditional write must be atomic in the shared store. A local mutex or JavaScript run-to-completion region protects only that process.

The fixed-window counter needs shared coordination or an explicitly per-instance policy. A load balancer does not merge memory.

### Requirement: add users and projects

Authenticate the caller, verify project/task access and scope every relevant query. Scope retained keys and rate policies by verified identity/tenant as appropriate.

Never accept a body ownerId as proof of identity. The current validator rejects that field rather than copying arbitrary input into storage.

Revisit private data in caches, logs, error details and list links. Add cross-user negative checks, not only “valid user gets 200.”

### Requirement: send a notification after creation

A successful task commit and an external notification are two effects. If the process crashes after one, how does the other recover?

A transactional outbox plus an idempotent worker is one candidate design. It needs real transaction and delivery behavior; a Promise.all between database save and email send does not make them atomic.

### Requirement: export all tasks consistently

The cursor walk is not a snapshot. Define whether the export means “whatever appears while traversing” or a stable point-in-time dataset.

A snapshot/export job can have different lifetime, storage and permissions from the interactive list API. Avoid silently promising snapshot consistency because a cursor looks sophisticated.

### Requirement: support expensive searches

List-size bounds do not bound the cost of an arbitrary filter. Use allowed query shapes, suitable indexes, query deadlines, workload observation and possibly asynchronous jobs.

Do not add Redis, queues or microservices merely because the endpoint exists. Name the bottleneck or invariant each component addresses.

---

## 6.19 Connect this to resume projects

For a backend/API claim, prepare a concrete explanation:

> “I defined resources and response contracts, validated input at the boundary and selected public output fields. For retry-sensitive creation, I associated a stable operation key with normalized input and a retained result. For edits, I required a version condition and made comparison/write atomic at the state boundary. I checked success, rejected inputs and overlapping requests.”

Only use the parts your project actually implements. This learning service is practice evidence, not proof that an earlier resume project had all those guarantees.

| Resume area | Interview follow-up |
| --- | --- |
| Node/Express API | What is the resource, and what can happen twice? |
| Payment/credit workflow | How is an uncertain provider outcome reconciled? |
| Multi-tenant SaaS | Where is tenant filtering enforced on every page/write? |
| AI endpoint | How are long calls, cancellation, costs and repeated tool effects handled? |
| High-throughput claim | Which workload, latency/error metrics and bottlenecks were measured? |
| Deployment | What state is lost when one instance restarts? |

A useful five-minute design answer starts with a requirement and an invariant, gives an API/data model, traces one request, and then examines a duplicate, a stale edit and a crash.

---

## 6.20 Must remember

- API, HTTP and REST refer to different levels.
- A resource is distinct from its representation.
- Safety, idempotency and cacheability are different properties.
- PUT replaces the supported target state; PATCH has a documented patch format.
- Idempotency concerns the intended effect, not identical response statuses.
- A 202 needs a completion/recovery story; it does not guarantee eventual success.
- 204, HEAD and 304 responses do not contain a response body.
- Parsing JSON does not establish field validity, ownership or permissions.
- Unknown/repeated query keys need an explicit policy.
- A cursor needs stable ordering and does not automatically supply a snapshot.
- no-cache allows storage with revalidation; no-store forbids storage under the cache rules.
- ETag is opaque; retain quotes and use appropriate comparison rules.
- A precondition check and its write must share an atomic boundary.
- A timeout leaves the remote outcome potentially unknown.
- A key must be associated with intent, input, scope and retention.
- Request IDs, resource IDs and idempotency keys have different purposes.
- An in-memory correctness demonstration does not become distributed merely by adding instances.
- Rate, total quota and simultaneous work need separate policy decisions.

---

## 6.21 Common wrong answers

| Wrong answer | Correction |
| --- | --- |
| “REST means JSON over HTTP.” | REST has architectural constraints; describe the actual API behavior. |
| “Stateless means there is no database.” | Resource data can persist; requests should carry required interaction context. |
| “GET is safe if our frontend uses it carefully.” | Safe semantics apply beyond one frontend's calling pattern. |
| “Idempotent means the same status every time.” | Repeated DELETE can return 204 then 404 while preserving absence. |
| “PATCH is always idempotent.” | Repetition depends on the patch operation/format. |
| “Missing PUT fields always mean unchanged.” | Define complete replacement input; partial semantics belong in an explicit contract. |
| “A cursor prevents every duplicate or missing row.” | Mutable ordering/filter membership and concurrent data changes still matter. |
| “Base64 protects the cursor.” | Encoding provides neither integrity nor authorization. |
| “no-cache disables caching.” | It requires revalidation before reuse. |
| “Check ETag, await work, then save.” | The comparison/write gap can permit a lost update. |
| “A timeout proves creation failed.” | The effect may have committed before the response was lost. |
| “Generate a new key for each retry.” | That represents a new intent and bypasses deduplication. |
| “A Map key guarantees exactly once.” | Scope, retention, crashes and replicas limit the guarantee. |
| “CORS is API authorization.” | A browser response-access policy does not establish user permissions. |
| “A rate limit bounds all expensive work.” | Slow/expensive requests also need cost, concurrency and time bounds. |
| “OpenAPI validation happens automatically.” | A document/client type does not enforce server runtime behavior by itself. |

---

## 6.22 Interview questions and follow-ups

These questions target common API-design mechanisms and failure cases. They are not a measured ranking of company question frequency.

**Q1. What is an API?**

An interface a program exposes for other programs to use. An HTTP API uses network requests and responses; a library API may be ordinary function calls.

**Follow-up:** identify the contract, implementation and consumer separately in your project.

**Q2. What makes an API RESTful?**

REST is an architectural style with constraints including stateless interaction, a uniform interface, caching and layering. JSON endpoints alone do not demonstrate all of it.

**Follow-up:** explain which constraints your service actually follows and how clients discover transitions.

**Q3. Does statelessness prohibit sessions or stored data?**

Stored resource data is compatible with stateless interaction. Hidden server-side conversation context can make requests dependent on prior interaction state. Explain the actual session design rather than using stateless as a vague scaling claim.

**Follow-up:** what context must each authenticated request carry or resolve?

**Q4. Why use resource nouns in URLs?**

They give clients stable targets while HTTP methods express supported interactions. It is a convention that improves consistency, not a universal grammatical rule.

**Follow-up:** model cancellation or report generation as an inspectable resource/workflow.

**Q5. PUT versus POST?**

PUT targets the URI being created/replaced and has idempotent method semantics. POST asks the target to process submitted content; collection creation is one common use and has no general deduplication guarantee.

**Follow-up:** who chooses the new resource URI, and how can the client retry safely?

**Q6. PUT versus PATCH?**

PUT supplies replacement state under the documented representation contract. PATCH supplies modifications in a specified format.

**Follow-up:** what do missing fields, null and arrays mean in your format?

**Q7. Can PATCH be idempotent?**

A patch setting a field to a constant value can be. A repeated increment/append can repeat its effect. PATCH itself provides no general idempotency guarantee.

**Follow-up:** how do preconditions and operation IDs affect the retry policy?

**Q8. Why is GET called safe if it writes access logs?**

Safety concerns the operation requested by the client. Incidental logging does not make the client request a business-state change.

**Follow-up:** why is deleting via a GET link dangerous around prefetchers and crawlers?

**Q9. Why can DELETE return 404 on retry and remain idempotent?**

Its intended final effect is absence. Repeating it does not need to reproduce the original response.

**Follow-up:** how would you prevent repeated refunds attached to a removal workflow?

**Q10. When would you use 201, 202 and 204?**

201 for creation, 202 for acceptance before processing completes, and 204 for success with no response content.

**Follow-up:** how does the client learn a 202 operation's final outcome?

**Q11. 401 versus 403?**

401 means valid authentication is missing and includes an appropriate challenge. 403 means the request is understood but refused; retrying the same credentials is not generally a remedy.

**Follow-up:** when would concealing a resource with 404 be appropriate?

**Q12. 409 versus 412 versus 428?**

409 signals an application-state conflict. 412 says a supplied precondition failed. 428 says the server requires a conditional request.

**Follow-up:** apply each to a different request in the task API.

**Q13. Content-Type versus Accept?**

Content-Type describes the content being sent. Accept describes response formats the client can accept.

**Follow-up:** explain 415 versus 406 and this example's narrower negotiation scope.

**Q14. Why not expose database rows directly?**

Rows can contain private fields and storage-specific shapes. Select a public representation and accept only writable fields.

**Follow-up:** what happens if a future migration adds internalCost or ownerId?

**Q15. Why distinguish malformed JSON from invalid fields?**

Syntax parsing establishes a value; validation establishes domain facts. Their error contracts can help clients correct different problems.

**Follow-up:** does a TypeScript type or successful JSON.parse prove completed is boolean?

**Q16. How would you design pagination?**

Bound size, define a deterministic total order, choose offset/cursor based on navigation and consistency needs, and return continuation information.

**Follow-up:** what happens when a row is deleted before the next page or the sort key changes?

**Q17. Why add a unique tie-breaker to a timestamp sort?**

Several rows can share a timestamp. A unique secondary key makes continuation unambiguous for the defined order.

**Follow-up:** which query/index would support your actual filter and ordering?

**Q18. Is a cursor a security boundary?**

No. Validate it and independently enforce access on every request. Encoding is not integrity protection.

**Follow-up:** what would signing protect, and what would it still not authorize?

**Q19. no-cache versus no-store?**

no-cache permits storage but requires validation before reuse; no-store forbids storing the response under the cache rules.

**Follow-up:** what changes when a shared CDN is placed in front of user-specific data?

**Q20. What is an ETag?**

An opaque validator associated with a selected representation. It can support conditional retrieval or precondition-based writes.

**Follow-up:** distinguish strong If-Match comparison from the weak comparison used by If-None-Match.

**Q21. How do you prevent lost updates?**

Require a version/precondition and compare it atomically with the state change at the authoritative store. Let the client reconcile a rejected stale edit.

**Follow-up:** why did the slow-body case matter, and why does a local check fail across replicas?

**Q22. What should a client do after a creation timeout?**

Treat the outcome as potentially unknown. Retry with the same supported operation key or reconcile through a stable operation reference.

**Follow-up:** why is a fresh key dangerous for a payment?

**Q23. What belongs in an idempotency record?**

Verified scope, operation/key, input fingerprint, execution state, retained result/reference and expiry/recovery policy.

**Follow-up:** how do two concurrent owners get prevented, and what happens after a crash?

**Q24. Should every failure be cached under a key?**

That depends on when the operation failed and whether its effect is known. This example removes a pre-write failure; a provider timeout after a possible charge requires reconciliation.

**Follow-up:** explain the policy of the actual provider you used.

**Q25. What is a good retry policy?**

Retry appropriate temporary failures only when repetition is safe, with a deadline, attempt cap and bounded backoff/jitter. Respect relevant server delay guidance.

**Follow-up:** how can retries at multiple layers amplify load?

**Q26. Rate limit versus concurrency limit?**

One constrains work over time; the other bounds simultaneous in-flight work. A service may need both.

**Follow-up:** what changes when counters are spread over several instances?

**Q27. How would you version an API?**

Identify incompatible external changes, select a versioning convention, support migration and observe old-client use before retirement.

**Follow-up:** can adding a response enum value break a client?

**Q28. How would you test an API beyond happy-path CRUD?**

Assert statuses/headers/representations and state invariants under invalid input, duplicate intent, stale edits, pagination changes and injected failures. Control concurrency with gates instead of relying on sleeps.

**Follow-up:** what crash, database, browser and performance claims remain untested here?

---

## 6.23 Practice tasks

Try each task before reading the checkpoints. Keep the chapter closed when explaining the mechanism.

### Task 1: Trace one request

Draw the POST flow from bytes through normalization, key reservation and response. Label resource ID, request ID and idempotency key.

**Checkpoint:** each ID has a different lifetime/purpose; the key record is reserved before creation yields.

### Task 2: Specify PATCH

Write the behavior for omitted title, null title, an empty object, an unknown field and repeated application of completed:true.

**Checkpoint:** our custom format keeps omitted fields, rejects null/empty/unknown input, and constant assignment does not repeatedly add an effect. Do not import Merge Patch's null rule into this contract.

### Task 3: Classify failures

Explain the statuses for malformed JSON, an invalid boolean, a changed input under the same key, a missing edit condition, and a stale condition.

**Checkpoint:** this contract uses 400, 422, 409, 428 and 412 respectively. Explain the mechanism behind each, not just the number.

### Task 4: Break a conditional update

Move the current-task read above await jsonBody in a scratch copy. Predict which concurrency invariant is threatened before running the checks.

**Checkpoint:** the slow-body case must reject the stale edit. Restore the authoritative source before using the service.

### Task 5: Explain pagination under change

Compare offset and immutable-ID continuation after deleting an earlier row. Then change a filter membership between pages.

**Checkpoint:** cursor position can resist position shifts; it does not freeze membership or provide a snapshot.

### Task 6: Add a field deliberately

Propose priority as an optional field. Specify defaults, validation, writable/output shape, fingerprint changes, PUT/PATCH semantics and compatibility implications.

**Checkpoint:** changing just the response serializer leaves multiple contract decisions unresolved.

### Task 7: Design a durable key table

Sketch a table/constraint for tenant-scoped creation keys and task creation. Mark where the transaction begins/ends and what a second request observes while the first is pending.

**Checkpoint:** uniqueness and commit/recovery behavior must survive replicas and restarts. Do not use a process-local Map as the shared constraint.

### Task 8: Design an export job

Define POST/GET contracts, states, permissions, result expiration and failure recovery for a consistent task export.

**Checkpoint:** 202 acceptance is separate from durable queuing, snapshot selection and result authorization.

### Task 9: Defend a limiter

Choose a policy for expensive AI requests: per-user budget, concurrency bound, total deadline and behavior during limiter-store failure.

**Checkpoint:** explain both dependency protection and legitimate-user impact. An arbitrary IP header is not verified identity.

### Task 10: Give a resume answer

Explain one API you built in three minutes. Include the resource, one invariant, a request trace, a duplicate/stale failure and actual evidence.

**Checkpoint:** distinguish implemented behavior, a proposed improvement and an unmeasured performance claim.

---

## Exit checklist

- [ ] I can distinguish API, HTTP, REST, resource and representation.
- [ ] I can describe REST constraints without equating them to JSON CRUD.
- [ ] I can choose resource paths and model a long-running operation.
- [ ] I can distinguish safe, idempotent and cacheable behavior.
- [ ] I can explain POST, PUT, PATCH and DELETE with retry examples.
- [ ] I can document missing/null/unknown fields in a patch format.
- [ ] I can select success/error statuses and required related headers.
- [ ] I can handle HEAD, 204 and 304 without parsing a nonexistent body.
- [ ] I can distinguish body format, syntax, runtime validation and permission checks.
- [ ] I can define a stable public Problem Details contract.
- [ ] I can compare offset/keyset pagination and explain its consistency limits.
- [ ] I can explain why cursor encoding does not establish access.
- [ ] I can distinguish no-cache, no-store and private.
- [ ] I can trace ETag conditional retrieval and a guarded edit.
- [ ] I can locate the atomic compare/write boundary after body parsing.
- [ ] I can explain timeout ambiguity and retained-key creation.
- [ ] I can distinguish operation intent from request correlation.
- [ ] I can explain pending owners, changed input, expiry and crash limits.
- [ ] I can propose bounded retries and identify amplification risks.
- [ ] I can compare rate, quota and concurrency policies.
- [ ] I can describe how persistence, replicas and users change this architecture.
- [ ] I can run all 68 checks and state what they do not establish.

---

## Next

[**M7: Authentication, Sessions, JWT and OAuth**](/docs/resume-skills/authentication-sessions-jwt-oauth). Establish who the caller is, how credentials travel and expire, how session/token validation works, and what logout means.

Then M8 adds authorization and tenant isolation; M9 applies retry/idempotency reasoning to webhooks and payments. The architecture companion builds larger systems after the API/data prerequisites.

### Sources and reproducible evidence

Research checked on **13 October 2026**. Standards establish protocol semantics; the example's selected policies and recorded outputs establish its local behavior.

- [Fielding: REST architectural style](https://roy.gbiv.com/pubs/dissertation/rest_arch_style.htm).
- [HTTP semantics, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), with [method reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods) and [status reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).
- [HTTP caching, RFC 9111](https://datatracker.ietf.org/doc/html/rfc9111) and [conditional requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests).
- [PATCH, RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html) and [JSON Merge Patch, RFC 7396](https://www.rfc-editor.org/rfc/rfc7396.html).
- [Problem Details, RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) and [additional statuses, RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html).
- [PostgreSQL LIMIT/OFFSET](https://www.postgresql.org/docs/current/queries-limit.html); proposed SQL here was not executed against PostgreSQL.
- [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests), a provider-specific policy reference rather than the contract of this demo.
- [Microsoft API design guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design) and [OpenAPI specification](https://spec.openapis.org/oas/latest.html).
- Preserved source/evidence: examples/resume-skills/module-6-rest-http/server.mjs, start.mjs, verify.mjs, results.json, verification-output.txt and validation-summary.json.
