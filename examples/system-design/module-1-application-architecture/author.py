"""Assemble A1 from teaching prose, exact runnable sources and recorded results."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
sources = ['src/notes.ts', 'src/sqlite.ts', 'src/http.ts', 'src/composition.ts']

def code(name):
    return '```typescript\n'+(BASE/name).read_text(encoding='utf-8')+'```'

def output(name):
    return '```json\n'+json.dumps(proof['observations'][name], ensure_ascii=False, indent=2)+'\n```'

chapter = r'''# Architecture and System Design Placement Handbook — Part 3
# A1: Application Architecture and Service Boundaries

**Estimated time: 3–4 hours | Architecture numeric module: 1 | Requires: A0 and one backend framework**

---

## Why this module exists

You can know Express routing, SQL and authentication separately and still struggle to explain how a backend should be organized. Interviewers can ask “Where does this rule live?”, “Why are these two features separate services?” or “What happens between receiving this request and committing the data?” A useful answer connects code responsibilities, data authority and deployment choices.

This chapter turns [A0's private-note baseline](/docs/system-design/design-method-estimation) into a real Node.js/TypeScript + Express HTTP application. It uses a persistent SQLite adapter to keep the example reproducible without another server. The same service is called directly and through HTTP, and a recorded request trace follows a create through every responsibility.

**Organizing principle: group rules that must agree, expose a small contract, and make each network boundary earn its cost.**

The local backend is implemented and verified. Microservices extraction, gateways, BFFs and event delivery are explained as design choices; this fixture does not deploy those components. Its published lesson-token allowlist demonstrates identity-to-principal mapping only. It does not implement OAuth, sessions, password storage, TLS or production credential management.

The 30 Q&As are editorial interview practice, not a measured ranking of employer question frequency. This chapter addresses the architecture bank's Q05–Q08 and introduces the state-placement reasoning in Q09; A2/A3/A4 deepen scaling, workflows and operations. Refresh [Resume M5: Express](/docs/resume-skills/express-backend-structure), [M11: Flask/FastAPI](/docs/resume-skills/flask-fastapi-python-request-handling) or [M12: Django/DRF](/docs/resume-skills/django-django-rest-framework) when framework syntax is unfamiliar.

---

## 1. Architecture is a set of decisions, not a box count

Application architecture defines responsibilities and dependencies: which code interprets an HTTP request, which code applies a use case, which component writes authoritative state and what contract connects them. Deployment architecture defines where programs run and communicate. The two views must agree, but they describe different things.

| Term | Concrete meaning in the notes example | Common confusion |
| --- | --- | --- |
| Function/class | `NotesService.create()` implements one application action | Every class needs a network API |
| Logical module | Notes capability and its public operations | A folder automatically enforces encapsulation |
| Layer | HTTP adapter, application service, persistence adapter | Every layer must run on a different machine |
| Process | One Node runtime and its memory/event loop | Two processes automatically own independent data |
| Deployment unit | A version of the notes application released together | Several containers necessarily mean microservices |
| Replica | Another running instance of that same deployment | A replica is a new business service |
| Network boundary | A call can time out independently of the caller | Remote calls behave like local function calls |
| Data owner | Component authorized to change a particular canonical state | Any component knowing the table name may write it |

A controller and a repository can be separate source files in one process. They do not need separate containers. Conversely, several containers can remain tightly coupled if every release requires synchronized changes or every service writes everyone else's tables.

In a design answer, identify the deployment unit separately from the capability boundary. “Notes, account management and notifications are logical modules in one deployable application” communicates more than calling a diagram “three-tier microservices.”

---

## 2. Start with operations and invariants

The example keeps A0's narrow scope: private text notes, one owner within a tenant, create/read/replace, and no sharing, listing, public links, attachments or deletion API. This lets you reason about boundaries without inventing unrelated infrastructure.

| Operation | Required invariant | Authority in this implementation |
| --- | --- | --- |
| Create | Same tenant + owner + operation key + same input gives one note and the original outcome | SQLite transaction over note and operation rows |
| Retry create with different input | An operation key cannot silently represent a different command | Fingerprint checked within that transaction |
| Read | Another owner/tenant cannot retrieve a note by guessing its ID | Scoped repository query using verified principal |
| Replace | An old revision cannot overwrite newer state | Conditional SQL update within a transaction |
| Validate input | Title/content limits apply even outside HTTP | Application service validation plus database constraints |

The body contains only `title` and `content`. `tenant`, `owner`, `id` and `revision` are not mass-assigned from user JSON. The controller obtains identity from the adapter's verified context; the service passes that explicit scope to persistence.

These rules reveal the first boundary: canonical notes and create-operation outcomes belong together because they must commit atomically. Splitting “idempotency service” from “notes writer” would turn a local invariant into a distributed workflow. A future architecture may justify that complexity, but this baseline does not.

---

## 3. Controller, service and repository: who does what?

| Responsibility | What it owns here | What to avoid placing there |
| --- | --- | --- |
| Middleware | Request ID, credential mapping, JSON parsing, transport body bound | Notes SQL or a decision about whether a revision is current |
| Controller / HTTP adapter | Route parameters, application headers, HTTP status/ETag/Location, error translation | SQL, business-state ownership, reading an owner from the body |
| Application service | Use-case inputs, domain limits, principal scope, repository port | Express `req`/`res`, SQL dialect, HTTP status codes |
| Repository port | Required persistence operations and typed outcomes | Arbitrary table access exposed to every caller |
| SQLite adapter | Scoped SQL, constraint enforcement, atomic operations, commit/rollback | Rendering responses or trusting client identity fields |
| Composition root | Construct concrete adapters and inject them | Turning dependency wiring into hidden business rules |

The service is deliberately small: this domain has few rules. Do not create ten pass-through classes to make the code look “enterprise.” A simple use case can remain simple while preserving a boundary that helps with testing or a later adapter change.

Validation has several layers with distinct purposes. The parser limits bytes accepted into the application. The service validates the meaning of an input regardless of caller. The database protects stored invariants. A correct static TypeScript type does not validate arbitrary JSON at runtime.

Where should a transaction live? The use case defines which effects must be atomic. Here each repository operation fully expresses that atomic unit. If a future use case updates two repositories, do not silently let each commit separately; introduce an explicit unit-of-work boundary or a workflow with defined intermediate states.

---

## 4. Dependency direction and the composition root

Execution follows a call from HTTP to service to persistence. Source dependency direction can differ because the service depends on a port, while the concrete persistence adapter implements that port.

```text
Runtime calls:
client -> Express adapter -> NotesService -> SqliteNotes -> database

Source dependencies:
http.ts ---------> notes.ts <--------- sqlite.ts
                       ^
                       |
composition.ts wires all three concrete pieces
```

`NotesRepository` is a TypeScript interface defined beside the service's needs. `NotesService` accepts that interface, and `SqliteNotes` implements it. Nothing in `notes.ts` imports Express or SQLite. This is dependency inversion in a small, practical form: the use case defines the persistence capability it requires.

Dependency injection is how a concrete object is supplied. It does not require a container or decorators: `new NotesService(repository)` is sufficient here. Avoid a service locator that lets arbitrary code pull a global database; it hides dependencies and makes isolation harder.

The verification harness parses emitted JavaScript imports with Acorn to check runtime dependency directions. Type checking separately verifies the interface implementation. This is a narrow import audit of these four files, not a universal proof that every future module is independent or every dynamic import is safe.

---

## 5. One small deployment, clear internal boundaries

```text
Implemented locally:
HTTP client
    |
    v
one Node process
    Express adapter -> NotesService -> SqliteNotes
                                           |
                                           v
                                 one temporary SQLite file

Possible deployed baseline, not run here:
browser -> TLS reverse proxy -> application instance -> PostgreSQL
```

The fixture is a layered notes capability, not a complete multi-module product. A modular monolith would apply similar boundaries to several capabilities while releasing the application as one unit. For example:

```text
application/
  notes/          public use cases; owns canonical note writes
  accounts/       public identity/profile operations; owns account state
  notifications/  delivery requests and delivery state, if later required
  composition/    wiring; does not become a shared business-data bucket
```

Inside each module, controller/service/repository layers may be useful. Across modules, prefer explicit public operations to reaching into another module's internal repository. A shared database server can host multiple owned schemas; ownership means controlling writes and evolution, not necessarily buying a separate database machine immediately.

This example uses synchronous repository operations to keep the transaction visible. `DatabaseSync` blocks the Node event loop; the SQLite module in the verified Node version is experimental. Treat this as a local learning adapter, not evidence that synchronous database access is appropriate for a high-traffic API. [Node v22.14.0 SQLite documentation](https://nodejs.org/download/release/v22.14.0/docs/api/sqlite.html).

Switching to an asynchronous PostgreSQL adapter would require asynchronous port methods, awaited service/controller calls, connection/transaction handling and new integration tests. Dependency inversion makes the change localized; it does not make database semantics interchangeable. Do not share this local file across independently scaled API hosts and call that a production database architecture.

---

## 6. Monolith, modular monolith and microservices

| Choice | Deployment and state consequences | Reasonable starting signal | Main cost |
| --- | --- | --- | --- |
| Monolith | One application released together; internal structure varies | Small product/team and evolving requirements | Internal coupling can grow without deliberate boundaries |
| Modular monolith | One release unit with explicit capability APIs and controlled data ownership | Need maintainability while retaining local calls/transactions | Boundaries require discipline and enforcement |
| Microservices | Multiple independently deployable capabilities communicating remotely | Independent ownership/releases/scaling justify distribution | Timeouts, compatibility, observability, data workflows and operations |

For this private-note application, start with one deployment and explicit internal boundaries. That is a scope-based recommendation for this teaching example, not a claim that every company should use a monolith. Microsoft describes microservices' independent deployment/data ownership and the added distributed-system complexity. [Microservices architecture style](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices).

Consider extracting indexing only after search becomes a requirement and indexing has an independent workload or release lifecycle. Canonical notes can remain in the notes owner; indexing maintains a derived representation. The extraction creates a freshness contract, a permission/deletion propagation problem and recovery work.

Do not split into “controller service,” “business service” and “database service” merely because those were layers. Every ordinary note request would traverse a remote chain, and business transactions would still cross it. Capability boundaries usually provide a stronger starting hypothesis than horizontal technical layers.

Physical tiers and logical layers are separate choices. A presentation layer and an application layer can share a deployment; physical isolation adds an actual network/operational boundary. [N-tier architecture guidance](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier).

---

## 7. Bounded contexts, cohesion and coupling

A bounded context is a boundary within which a domain model and its terms have a consistent meaning. It is not a synonym for a table, a REST endpoint or a required microservice. Domain analysis helps identify capabilities before choosing physical service boundaries. [Microsoft domain analysis](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis).

In a learning platform, “note” in the private-notes capability means owner-controlled text with a revision. In search, a “document” could mean a versioned projection with searchable fields. In notifications, a “message” means a delivery attempt with a recipient/channel/status. Reusing one giant `Document` object across all three can couple unrelated lifecycles.

Use this boundary worksheet before extraction:

| Question | Notes example |
| --- | --- |
| Which business action belongs together? | Create/read/replace a private note |
| Which invariant requires atomic agreement? | Note creation and saved operation outcome |
| Which model/terms are authoritative? | Note identity, owner, content and revision |
| Who can write that state? | Notes persistence adapter through the notes use cases |
| What can others request or observe? | A scoped read or a versioned published event, if later designed |
| Which changes should not force coordinated releases? | Search ranking changes should not require changing canonical-note writes |
| What failure can callers tolerate? | Search delay may be acceptable; silent loss of canonical writes is not |

High cohesion means related rules change together within a boundary. Low coupling means other boundaries need limited knowledge of those internals. These goals can conflict: moving tightly coupled operations apart may increase network coupling rather than reduce it.

A useful smell is a service that cannot answer any normal request without many fine-grained calls to another service's tables. Reconsider the boundary, offer a coarser operation, or build an explicitly stale projection. Do not hide the problem behind the label “microservice.”

---

## 8. Data ownership and the real transaction boundary

The notes owner controls the `notes` table and `operations` table. A transaction starts before the operation lookup, checks for a previous result, inserts a new note when needed, stores its response, and commits before HTTP success is sent.

```text
BEGIN IMMEDIATE
  lookup operation by (tenant, owner, operation)
  if same fingerprint: return saved original representation
  if different fingerprint: reject and roll back
  otherwise insert note + save original outcome
COMMIT
send HTTP response
```

The key's scope matters. Alice in tenant alpha and Alice in tenant beta can use the same operation string for independent commands. Bob in alpha can do so too. Omitting owner/tenant from operation storage could leak outcomes or incorrectly suppress a legitimate command.

Create retries use the stored original representation, even if the note was later edited. A GET retrieves current state. A replay returning revision 1 after a revision-2 edit does not mean the edit was reverted; it answers the original create operation. The observed persistence section demonstrates this distinction.

A replace uses `WHERE tenant=? AND owner=? AND id=? AND revision=?`, then increments the revision. A zero-row update is classified with a scoped read: invisible/absent returns the same missing outcome; an owned existing note with another revision is stale. This avoids treating every zero-row update as permission disclosure.

SQLite `BEGIN IMMEDIATE` is the local adapter's writer-transaction mechanism. These results do not establish PostgreSQL isolation behavior or a distributed lock. The SQL condition is the state-transition guard; the service does not read a revision, compare it in JavaScript, then perform an unconditional write.

---

## 9. HTTP contract and identity boundary

| Request | Required application inputs | Success | Selected failures |
| --- | --- | --- | --- |
| `POST /notes` | Allowlisted bearer token, JSON title/content, `Idempotency-Key` | 201, Location, revision ETag, saved note | 400 invalid/key missing, 409 key reused with changed input |
| `GET /notes/:id` | Allowlisted bearer token | 200, current note and ETag | 404 invisible or absent |
| `PUT /notes/:id` | Allowlisted bearer token, JSON replacement, one numeric strong `If-Match` | 200, revision increment and new ETag | 428 condition missing, 400 unsupported condition, 412 stale, 404 invisible/absent |

All represented responses carry `Cache-Control: no-store` and a generated request ID. Parser failures use safe JSON errors; unexpected exceptions become `500 {"error":"internal_error"}`. Authentication runs before parsing on notes paths. Unknown routes return 404. Authorization and error behavior are tested through actual loopback requests.

`If-Match` uses strong comparison to guard an operation against a changed representation. This API intentionally accepts one strong numeric tag such as `"2"`; it rejects weak tags, wildcard and lists rather than implementing the complete HTTP grammar. That is a documented application subset, not the general grammar of the standard. [RFC 9110: If-Match](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match).

The transport and domain size bounds have different purposes: JSON transport limit is 8 KiB; note content is at most 4096 UTF-8 bytes; title is nonblank, NUL-free and at most 120 Unicode code points. The parser's allowance does not expand the domain limit. Unknown body fields are rejected, which also prevents accidentally accepting `owner` or `tenant`.

The `Idempotency-Key` name and response replay header are this fixture's application contract. A required key is an alphanumeric/underscore/hyphen identifier of at most 64 characters, not an arbitrary string. It is an operation identity within the authenticated owner/tenant scope, not an authentication credential.

The three published tokens map to alpha/Alice, alpha/Bob and beta/Alice. An unknown token returns 401 with a bearer challenge. `X-Tenant` and `X-Owner` never override this mapping. In a deployed application, replace this allowlist with verified credentials and server-derived membership; consider issuer/audience/expiry/revocation and permission changes. Direct service callers must supply a trusted principal; validating its syntax does not authenticate a person.

---

## 10. Runnable backend: application service and port

Files are under `examples/system-design/module-1-application-architecture/`. The following four code blocks are embedded verbatim from the compiled fixture's TypeScript sources.

`src/notes.ts` defines input validation, typed outcomes and use cases. The repository interface expresses the operations this service requires; it does not expose a generic database connection.

{{NOTES_CODE}}

The interface is synchronous because this learning adapter is synchronous. Do not add `async` to a route and assume a blocking database call becomes non-blocking. If a repository becomes async, its return types and every caller must reflect that change.

---

## 11. Runnable backend: SQLite adapter

`src/sqlite.ts` implements the port with real file-backed persistence. Bound values are passed through prepared statements; SQL text does not interpolate user content. The injected ID factory gives verification deterministic IDs; normal composition uses random UUIDs. The `afterInsert` hook exists solely to inject an owned test fault and is never exposed as an HTTP option.

{{SQLITE_CODE}}

Both create and replace commit before their successful result returns to the controller. If the injected fault occurs after the note insert, rollback removes it. The retry can then create normally because no completed operation was stored. The observer callback used for traces is a local harness hook; a production telemetry pipeline needs its own bounded, failure-safe behavior.

The operation table has no expiry in this fixture. A production retention policy must relate replay guarantees to key/outcome retention and note lifecycle. Deleting an old outcome can permit an old key to be treated as new; retain or reject based on an explicit contract. A0's planning retention arithmetic is not an implemented deletion job.

---

## 12. Runnable backend: Express adapter and composition

Express processes middleware in registration order. Here that order is request context, identity mapping, transport checks/parsing, controller, unknown-route handling and error translation. Error middleware has four arguments. Express 5 propagates rejected promises from async handlers to error handling, which the fault-injection HTTP case exercises. [Express middleware](https://expressjs.com/en/guide/using-middleware/), [Express error handling](https://expressjs.com/en/guide/error-handling/).

`src/http.ts`:

{{HTTP_CODE}}

`src/composition.ts`:

{{COMPOSITION_CODE}}

The composition root is intentionally boring: build a repository, inject it into the service, build the HTTP adapter, and expose cleanup. A change from Express to another transport would replace the adapter; the input policy and state-transition behavior still belong to the use case and persistence boundary.

The example centralizes HTTP error translation so the service can return meaningful rule outcomes without knowing `res.status()`. A larger application may use typed result values instead of exceptions. The architectural requirement is a deliberate contract, not a mandatory exception style.

---

## 13. Run it and inspect real evidence

Verified on **{{DATE}}**, using **Node {{NODE}}**, **Express {{EXPRESS}}**, **TypeScript {{TYPESCRIPT}}**, Node's bundled **SQLite {{SQLITE}}**, and **{{OS}}**. The compile uses strict checking with `skipLibCheck` for dependency declarations. Installed Node type definitions are newer than this runtime; the example restricts SQLite calls to APIs present in Node v22.14.0 and verifies them at runtime.

The registry metadata in the offline npm cache could not resolve the existing Express version. The successful run uses directory links to already installed M5 dependencies and the study-guide compiler/parser. `prepare-local.mjs` creates links inside this example's ignored `node_modules`; it does not modify either source installation or fetch packages. This is a workspace reproduction path, not a verified fresh npm install on another machine.

From the example directory, in PowerShell:

```powershell
npm.cmd run prepare:local
npm.cmd run verify
# Optional interactive lesson; prints an ephemeral loopback URL:
npm.cmd start
# Stop with Ctrl+C; its temporary database is then removed.
```

The start script chooses a loopback port automatically and keeps data only for that manual session. Verification also chooses temporary ports, closes listeners/connections and removes its exact temporary database directory. It does not use port 3000, start Docker or touch an existing database server.

For manual requests, replace the URL with the printed address:

```powershell
$lessonOrigin = 'http://127.0.0.1:PORT'
$lessonHeaders = @{ Authorization = 'Bearer lesson-alice'; 'Idempotency-Key' = 'manual_create' }
$lessonBody = @{ title = 'Architecture'; content = 'Trace the owner of each state change' } | ConvertTo-Json
$lessonCreated = Invoke-WebRequest -Uri "$lessonOrigin/notes" -Method Post -Headers $lessonHeaders -ContentType 'application/json' -Body $lessonBody
$lessonCreated.StatusCode
$lessonCreated.Headers
$lessonCreated.Content
# Repeating the same POST/key/body returns the saved outcome.
```

**{{TOTAL}} local checks passed:** {{COUNTS}}. The count describes this fixture's assertions, not coverage of every production failure mode.

Observed create response (date and request ID are from this run; connection headers are runtime details):

{{CREATE_OUTPUT}}

Observed ordered trace, captured out of band by the verification observer rather than exposed in the response body:

{{TRACE_OUTPUT}}

Read that trace as a causal story: the adapter mapped a token to a principal, the controller translated transport input, the service validated the use case, the repository atomically stored canonical state and the saved outcome, and only then did the controller produce success. A trace marker alone does not prove a commit; real persistence and rollback checks support that claim.

Observed direct-call persistence after closing/reopening the database:

{{PERSISTENCE_OUTPUT}}

Observed failure after insert and retry:

{{ROLLBACK_OUTPUT}}

Observed HTTP contracts:

{{CONTRACTS_OUTPUT}}

The two concurrent client requests are handled in one Node process with synchronous SQLite calls. One succeeds at revision 2 and the other is rejected as stale; final revision is 3. This checks the visible same-revision guard under that execution model. It is not multi-host contention evidence, a throughput benchmark or a PostgreSQL isolation test. A0 separately exercised two SQLite connections in its own Python probe.

The harness also checks credential rejection, owner/tenant scoping, spoofed identity headers, unknown body fields, transport/domain size limits, unsupported conditions, replay after an edit, safe unexpected-error mapping, dependency direction and cleanup. See `verify.mjs` and `verification-results.json` for assertion names and complete observations.

---

## 14. Synchronous calls, commands, queues and events

Do not conflate blocking I/O with synchronous business interaction. An awaited HTTP request can use non-blocking I/O while the caller still requires the remote answer before completing its operation. An event loop does not remove that business dependency.

| Interaction | What the caller needs | Notes example if the feature is added | New obligation |
| --- | --- | --- | --- |
| Local function call | Immediate result in the same process | Controller calls create use case | Exceptions/typed results and clear ownership |
| Synchronous remote request | Immediate answer from another deployment | Validate an external account entitlement before an action | Deadline, authentication, overload/failure policy, response compatibility |
| Queued command | Another component should perform work later | `IndexNoteVersion` job | Durable acceptance, backlog, retries, dedupe and completion status |
| Published event | A fact already happened; interested consumers react | `NoteCreated` after canonical commit | Event identity/schema, publication recovery, consumer idempotency and lag |

An event is a semantic contract; a queue/topic is a delivery mechanism. A command normally targets an owner expected to perform an action. An event describes a fact without pretending that every subscriber completed its work. One mechanism can carry either kind of message.

For private notes, create should wait for canonical persistence because the success response claims that the note exists. Search indexing can be delayed if the product accepts that new notes may take time to appear in search. Returning 202 for accepted work requires a durable acceptance boundary and a way to discover completion/failure; spawning an untracked promise is not enough.

Beware the dual-write gap:

```text
commit note -> process crashes -> publish never happens
publish event -> note transaction fails -> consumer sees a nonexistent note
```

A transactional outbox stores canonical changes and publication intent in one database transaction; a relay delivers that intent later. Relay retries can still duplicate delivery, so consumers need suitable deduplication/effect rules. [AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).

This A1 fixture does not implement an outbox or broker. A local `EventEmitter`, an observer trace callback or an async function is not durable message delivery. A3 will develop recovery and concurrency mechanisms rather than treating “event driven” as a guarantee.

---

## 15. Reverse proxy, load balancer, API gateway and BFF

| Role | Main question it answers | Typical responsibilities | What it does not establish by itself |
| --- | --- | --- | --- |
| Reverse proxy | How does a client reach an origin through an intermediary? | Forwarding, TLS termination, request bounds, routing | Business authorization or independent service ownership |
| Load balancer | Which healthy target receives this request/connection? | Selection, health, connection handling | Uniform work per target or correctness of database writes |
| API gateway | How are public APIs exposed and governed? | API routing, shared policy, quotas, credential checks, version entry points | Every resource-level permission decision |
| BFF | What API does this particular frontend experience need? | Client-specific aggregation, response shape, server-side credential handling | A replacement for backend invariants |

These roles can overlap in one product or deployment. A reverse proxy may also load balance and enforce request bounds. An API gateway can use reverse-proxy behavior. Draw only components whose responsibility matters to the request you are explaining.

A BFF separates frontend-specific API needs from general backend capability contracts. Different clients can need different aggregation or payloads, and the extra layer brings maintenance/latency costs. [Backends for Frontends pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends).

Example proposed trace, not a deployment run by this fixture:

```text
browser sends session cookie
  -> TLS reverse proxy routes request
  -> web BFF verifies session and shapes a use-case request
  -> notes API verifies accepted downstream identity and enforces owner/tenant scope
  -> notes transaction commits
  -> result returns through the BFF
```

If a gateway verifies a credential, the downstream service must still establish which asserted identity it trusts and which resources that identity may access. Client-supplied identity headers are not automatically trustworthy. Either verify credentials downstream or secure the intermediary path and authenticated assertion contract; do not leave an alternate direct path that bypasses the assumed trust boundary.

For your Next.js/FastAPI project explanation, distinguish a Next.js page, a route acting as a BFF and the FastAPI capability API. Explain the actual documented credential flow and resource checks. This chapter's allowlist is not evidence of that project's session/JWE implementation; use [Resume M28](/docs/resume-skills/resume-project-experience-deep-dives) and the source project when answering those specifics.

---

## 16. Stateless instances, scaling and extraction

An application instance is stateless for routing when correctness does not depend on a later request reaching that same instance's private durable state. It still has memory, connections and temporary work. The important question is which state can be lost when an instance exits and which state all eligible instances can access correctly.

| State | A1 fixture placement | Multi-instance consideration |
| --- | --- | --- |
| Canonical note and operation outcome | Local SQLite file | Move to a suitable shared authoritative datastore; define transactions and failover |
| Credential registry | Fixed per-process lesson map | Use real verification/session authority and membership rules |
| Request trace list | Verification process memory only | Export bounded telemetry; do not depend on trace retention for correctness |
| Active HTTP connection | Process owning the socket | Drain/reconnect; connection ownership is transient |
| Derived search index | Not implemented | Define version/freshness/authorization and rebuild behavior |

Putting state “in a database” is not sufficient if every application replica has a different private database. Copying this SQLite file into each container would create divergent notes and retry records. The fixture is a single-host persistence lesson, not a stateless deployment.

Sticky sessions keep a client directed to a target and can help with certain connection/session designs. They do not replicate state, make retries safe after target failure or eliminate hotspots. A WebSocket connection naturally stays with one process while connected; reconnect must still have a defined recovery/authentication path.

Before extracting a module, record evidence and answer these questions:

1. Which independent capability, owner or release need is blocked today?
2. Which measured workload would benefit from independent scaling?
3. What contract replaces local calls, including version and error behavior?
4. Which tables/invariants stay authoritative on each side?
5. Which cross-boundary workflow and partial failures now exist?
6. How will the first rollout, compatibility window and rollback work?

For a proposed search extraction: build a projection contract, backfill with version identity, capture ongoing changes durably, compare results, route reads gradually and preserve a rollback path. These are design steps, not implemented A1 migration tooling. Do not promise zero lag or atomic updates across both stores without a mechanism that supports those claims.

---

## 17. Changed requirements and failure walkthroughs

### The client loses the create response

The database may have committed even though the caller saw a timeout. The client retains the same operation key and input, then retries. The repository returns the stored outcome if it exists; it creates normally if the first attempt rolled back. A network timeout alone does not tell the client which happened.

For replace, the expected revision prevents a stale retry from writing again. If the first edit committed but its response was lost, retrying the old revision can return 412. The client then reads current state and resolves the result. This prevents another overwrite; it is not a stored-result replay protocol for edits.

### A second device edits while the first is idle

Both devices read revision 1. One writes with `If-Match: "1"` and receives revision 2. The other receives 412 with its old condition. Product policy can offer reload/compare/manual merge; the backend should not silently discard newer work. Real-time collaborative editing would require a different model than replacing a whole text value.

### The team adds search

Keep canonical notes as the authority. Decide whether search may lag, whether users need read-after-write discoverability, how projections carry note revisions, and how access revocation/deletion removes or filters results. A worker cannot trust a stale event to establish current access indefinitely. A2/S9/S12 deepen these mechanisms.

### Notifications become required

A create response must say whether it promises only note persistence or also delivery. Sending email inside the SQL transaction extends lock time and still does not make the external provider part of that transaction. Persist delivery intent and track attempts if reliable delivery is required; then define retries and duplicate effects. A3/S2 develop this rather than adding a fire-and-forget call here.

### Another team wants direct database access

Read-only reporting access can be an explicit contract with constraints, but granting write access bypasses the module's invariants. Prefer an owner-provided command/API for mutations. If a shared schema is unavoidable, coordinate compatibility and permissions explicitly; do not claim independent evolution while allowing arbitrary cross-service writes.

### An unexpected database error occurs

The adapter rolls back its transaction and the HTTP adapter returns a safe 500. The fixture injects a failure after insertion to verify this path. It does not simulate every disk-full/commit-ambiguity scenario. A production caller still needs an operation identity, bounded retry policy and an operational investigation path; raw SQL details should not become a public error response.

---

## 18. Common interview questions with answer checkpoints

### Q1. What is application architecture?

It is the arrangement of responsibilities, dependencies and contracts that implements use cases. For notes, the HTTP adapter translates transport, the service validates the action, and persistence atomically changes scoped state. Explain those relationships before naming an architecture style.

### Q2. How is application architecture different from deployment architecture?

Application architecture describes logical responsibilities; deployment architecture describes running processes, hosts and communication. Three source layers can live in one deployment. Multiple replicas can run the same capability without becoming different business services.

### Q3. What belongs in a controller?

Route/header extraction, trusted principal access, use-case invocation and response/error translation. In this fixture it maps a current note revision to an ETag. SQL and canonical-state rules belong below the transport adapter.

### Q4. What belongs in a service layer?

Application use-case policy and coordination: valid input, caller scope and required persistence operation. It should remain callable without Express. Avoid a large service that becomes the owner of every unrelated capability or a layer of wrappers with no useful boundary.

### Q5. Why use a repository interface?

It describes persistence operations in terms the application needs and keeps SQL/framework details out of the use case. Here it makes direct service invocation and a concrete SQLite adapter possible. It does not guarantee that swapping databases preserves transactions or performance.

### Q6. Where should a transaction start and end?

Around the state changes required to preserve one invariant. Creating a note and saving its operation outcome must commit together. The successful response follows the commit. Independent commits in two repositories do not become atomic just because one service called them.

### Q7. Is validation a controller or service responsibility?

Transport checks belong at the transport boundary; use-case rules must apply regardless of caller; storage invariants deserve database enforcement. The 8-KiB parser bound and 4096-byte content limit are different checks. TypeScript types alone do not validate JSON.

### Q8. What is dependency inversion?

The high-level use case defines the persistence capability it needs, and a concrete adapter implements it. `NotesService` imports no Express/SQLite code. Runtime execution still reaches the concrete adapter supplied by composition.

### Q9. What is dependency injection?

Supplying dependencies rather than constructing or globally locating them inside the consumer. Passing a repository into the service constructor is injection. A framework container is optional and should not obscure the application's actual dependencies.

### Q10. Would you start this product with microservices?

For the stated private-notes scope, one deployment with clear internal boundaries is a reasonable baseline. Independent team ownership, releases or a measured specialized workload could justify extraction. Name the benefit and the remote-call/data-workflow cost rather than assuming services are required for scale.

### Q11. What makes a monolith modular?

Explicit capability APIs, controlled internal dependencies and clear data-write ownership within one release unit. Folders help organization but do not enforce those rules. The A1 fixture demonstrates a layered capability; a full modular monolith would apply such boundaries across multiple capabilities.

### Q12. How do you choose a service boundary?

Start with business capability, cohesive rules and state that must agree. Check ownership, change rate and cross-boundary calls/transactions. Notes plus saved create outcome belong together in this baseline because splitting them creates a distributed atomicity problem.

### Q13. What is a bounded context?

A boundary within which terms and a domain model have consistent meaning. A canonical note and a search projection need not share one giant model. A bounded context can inform a logical module or service; it does not automatically require a new deployment.

### Q14. Should every microservice have a separate database server?

Independent ownership means controlling the state/schema and preventing unauthorized cross-service writes. Physical placement can vary, including separate owned schemas on shared infrastructure. Sharing one physical server also creates resource/failure coupling that the design must acknowledge.

### Q15. Can several services write the same table?

They can technically do so, but then ownership and invariants become coupled. Ask who controls schema evolution and every mutation path. Prefer an explicit owner for canonical writes; direct shared writes need deliberate coordination rather than a claim of independent service autonomy.

### Q16. When should a call be synchronous?

When the caller needs that result to decide or complete the current action. Canonical note persistence precedes successful creation. A remote synchronous dependency adds a deadline and failure/overload policy; using non-blocking I/O does not remove that dependency.

### Q17. What is the difference between a command and an event?

A command asks an owner to perform an action; an event describes a fact that occurred. `IndexNoteVersion` is a command, while `NoteCreated` is an event. Neither name says whether delivery is durable or exactly once.

### Q18. Is a queue always better than a direct request?

No. It changes completion semantics, adds backlog and requires recovery/deduplication. It helps when work can complete later or producers need temporal decoupling. If the user requires the final result immediately, explain what the acceptance response means and how completion is discovered.

### Q19. Why is publishing after commit not reliably atomic?

A process can crash between commit and publication. Publishing first reverses the inconsistency risk. An outbox records publication intent with the state change, while relay/consumer logic handles subsequent delivery. A1 explains that design but does not implement the relay.

### Q20. Does an in-process event emitter solve reliable messaging?

No. Its memory and handlers share process lifetime and failure. It may be useful for local notifications, but it does not establish durable delivery, redelivery or atomicity with a database. The A1 observer is instrumentation for a test trace, not a queue.

### Q21. How do reverse proxies and load balancers differ?

A reverse proxy forwards on behalf of origins; load balancing chooses a target among eligible targets. One component can perform both roles. Explain health, routing and connection behavior for the actual request instead of drawing duplicate boxes by habit.

### Q22. What does an API gateway add?

An API-facing policy/routing boundary that may centralize quotas, credential checks or API version exposure. It does not automatically enforce every note's owner/tenant permissions. Downstream services must trust the identity path deliberately and retain resource-level policy.

### Q23. What is a BFF and when would you add one?

A backend shaped for a particular frontend's needs, often aggregating operations or managing server-side credentials. Add it when those needs justify an extra maintained boundary. It should call capability contracts without taking ownership of all backend business rules.

### Q24. What makes an API instance stateless?

Correctness does not require a later request to land on the same instance's private durable state. Shared authoritative persistence and real credential/session handling need explicit designs. This local SQLite fixture does not demonstrate multi-instance stateless deployment.

### Q25. Do sticky sessions make state safe?

They provide affinity, not replication or recovery. An instance can still fail and take private memory with it. Describe reconnect/failover semantics and any authoritative shared state rather than using affinity as a correctness guarantee.

### Q26. How do authentication and authorization appear in this trace?

The adapter maps an allowlisted lesson credential to a principal; scoped repository predicates restrict notes to that principal's owner/tenant. Identity syntax validation alone is not authentication. The test credential mechanism is intentionally limited and must be replaced for a real deployment.

### Q27. Why can a create retry return an old revision?

It returns the saved outcome of that original operation. Current state is fetched with GET. The fixture edits to revision 2, then replays create revision 1 without reverting the note. A stable operation ID answers a different question from a current resource read.

### Q28. What if a replace response is lost?

Retrying with the old expected revision can produce 412 if the first edit committed. Read current state and resolve the result. Optimistic concurrency prevents another stale overwrite; it does not automatically provide an original-result replay record for edits.

### Q29. How would you extract search from this application?

Keep canonical notes authoritative; define a versioned projection, acceptable lag, current permission checks and deletion propagation. Plan backfill, ongoing change capture, compatibility and rollback. Extraction changes consistency and failure handling even if the API shape appears unchanged.

### Q30. What does the runnable example actually prove?

The strict TypeScript build and named checks demonstrate local service/persistence/HTTP contracts, scope rejection, rollback/reopen, import direction and cleanup. They do not prove production authentication, a multi-service deployment, distributed concurrency, durable events or throughput capacity. Tie each claim to the evidence that supports it.

---

## 19. Revision sheet and a 45-minute mock

| Prompt | Recall |
| --- | --- |
| First boundary | Capability + invariant + state owner |
| Controller | Transport to use case; result to HTTP |
| Service | Input/use-case policy; explicit scoped persistence operation |
| Repository adapter | SQL, transactions, stored-state invariants |
| Source dependency | Adapter depends on use-case port; composition wires concrete pieces |
| Module vs service | Logical boundary vs independently deployed remote boundary |
| Microservice trigger | Concrete ownership/release/scaling benefit with costs acknowledged |
| Retry create | Stable scoped key + input fingerprint + saved outcome in one transaction |
| Replace | Expected revision checked by conditional write |
| Async work | Durable acceptance, completion semantics and recovery |
| Proxy/gateway/BFF | Forward/select/policy/client-specific API roles can overlap |
| Evidence | Real local HTTP/SQLite behavior; no production deployment claim |

**Mock prompt:** “Build a private study-note backend. Explain your code structure and whether search or notifications should be separate services.”

| Segment | Minutes |
| --- | --- |
| Clarify operations and scope | 5 |
| State invariants and data ownership | 7 |
| Draw logical modules and deployment separately | 7 |
| Trace create/read/replace through code | 10 |
| Inject lost response, stale edit and future indexing | 10 |
| Explain alternatives and evidence limits | 6 |
| **Total** | **45** |

A defensible short answer:

> I will begin with one notes deployment and explicit HTTP, use-case and persistence responsibilities. The verified principal supplies tenant and owner; the client supplies only allowed note fields. A create commits the note and original operation outcome together, so a retry uses the same scoped key. A replace checks the expected revision in the write. Search may become a separate derived projection if its workload or ownership justifies it, but then I must define lag, permission propagation and recovery. The local fixture verifies the HTTP and database contracts; a deployed system still needs real credentials, suitable shared persistence and operational checks.

After the mock, inspect whether you traced a commit before success, distinguished current state from operation outcome, and justified every remote boundary. “Use Kafka/Kubernetes/microservices” is not a substitute for those decisions.

---

## 20. Practice tasks

1. Draw the runtime call chain and source import graph separately. Explain why the arrows can differ and where composition belongs.
2. Run the fixture. Trace one create from credential mapping to committed note/outcome and match every observed event to source code.
3. Create, edit and replay create. Explain why revision 1 can be returned by replay while GET returns revision 2; confirm the edit remains stored.
4. Remove the conditional revision predicate in a scratch copy and show which stale-edit check fails. Restore it and explain the lost-update risk.
5. Send alpha/Bob's credential for alpha/Alice's note, then spoof `X-Tenant`/`X-Owner`. Confirm the scoped rejection and identify its authority.
6. Propose an asynchronous PostgreSQL port/adapter conversion. List changes to types, await points, transaction scope, connection cleanup and integration tests; do not claim it is a drop-in dialect swap.
7. Add a separate logical capability on paper, such as delivery tracking. Define its public commands, data-write owner and which canonical-note internals it must not access directly.
8. Design a search extraction plan with versioned projection, backfill, update capture, permission/deletion behavior, lag objective and rollback. Mark every unimplemented mechanism.
9. Compare synchronous delivery with durable queued delivery for notifications. Write response promises and a crash timeline for each; explain the dual-write gap.
10. Complete the 45-minute mock, then answer Q05–Q09 from the architecture bank without relying on architecture labels alone.

---

## 21. Completion checklist

- [ ] I can distinguish a layer, module, process, replica and deployment unit.
- [ ] I can assign each request responsibility to a concrete component.
- [ ] I can explain dependency inversion and simple constructor injection.
- [ ] I can locate canonical note and operation-outcome ownership.
- [ ] I can reproduce the recorded create trace and local HTTP contracts.
- [ ] I can explain replayed original outcome versus current note state.
- [ ] I can explain conditional replacement and its lost-response limitation.
- [ ] I can distinguish verified principal scope from user-controlled identity fields.
- [ ] I can justify a modular baseline or a specific service extraction.
- [ ] I can distinguish commands/events and identify durable-delivery obligations.
- [ ] I can compare reverse proxy, load balancer, gateway and BFF roles.
- [ ] I can state the fixture's evidence limits and complete a timed design mock.

---

## 22. Research references and continuation

Primary references were reviewed on {{DATE}}. Framework/version claims use the exact runtime's documentation where available; architectural choices in the notes example are worked reasoning, not a vendor-prescribed design or an employer-frequency survey.

| Primary reference | What it supports here |
| --- | --- |
| [Node v22.14.0 SQLite](https://nodejs.org/download/release/v22.14.0/docs/api/sqlite.html) | Available synchronous database APIs and experimental status |
| [Express middleware](https://expressjs.com/en/guide/using-middleware/) | Ordered request pipeline and error middleware shape |
| [Express errors](https://expressjs.com/en/guide/error-handling/) | Async handler rejection propagation and safe error handling |
| [Microsoft microservices style](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices) | Independent deployment/data ownership and distributed-system trade-offs |
| [Microsoft N-tier style](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier) | Logical layers versus physical tiers |
| [Microsoft domain analysis](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis) | Domain boundaries and bounded contexts |
| [Microsoft BFF pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends) | Frontend-specific API responsibility and costs |
| [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | Dual-write recovery through transactional publication intent |
| [RFC 9110, If-Match](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match) | Strong validator precondition semantics |

Return to the [architecture roadmap](/docs/system-design) or [A0: Design method](/docs/system-design/design-method-estimation). For framework mechanics, revisit [Resume M5](/docs/resume-skills/express-backend-structure); for authorization, [M8](/docs/resume-skills/api-security-authorization-multi-tenancy); for data access, [M13](/docs/resume-skills/postgresql-backend); and for jobs, [M15](/docs/resume-skills/caching-background-jobs-data-ingestion).

**Next: [A2 — Data, caching and scaling](/docs/system-design/data-caching-scaling)**, architecture part 4 / numeric module 2. It connects access patterns and consistency requirements to indexes, replicas/shards, caches, hot keys and scaling choices. A2 is now available with its own local data/cache verification scope. A3 then develops reliable workflows; A4 covers secure, observable operation. All worked systems and consolidation remain later sections.
'''

replacements = {
    '{{NOTES_CODE}}': code(sources[0]), '{{SQLITE_CODE}}': code(sources[1]),
    '{{HTTP_CODE}}': code(sources[2]), '{{COMPOSITION_CODE}}': code(sources[3]),
    '{{CREATE_OUTPUT}}': output('create'), '{{TRACE_OUTPUT}}': output('createTrace'),
    '{{PERSISTENCE_OUTPUT}}': output('persistence'), '{{ROLLBACK_OUTPUT}}': output('rollback'),
    '{{CONTRACTS_OUTPUT}}': output('contracts'), '{{DATE}}': proof['verified_date'],
    '{{NODE}}': proof['node'], '{{EXPRESS}}': proof['express'], '{{TYPESCRIPT}}': proof['typescript'],
    '{{SQLITE}}': proof['sqlite'], '{{OS}}': proof['os'], '{{TOTAL}}': str(proof['total']),
    '{{COUNTS}}': ', '.join(f"{value} {key.replace('_', '/')}" for key, value in proof['counts'].items()),
}
for marker, value in replacements.items():
    assert marker in chapter, marker
    chapter = chapter.replace(marker, value)
filename = 'system-design-handbook-part-3-module-1-application-architecture-service-boundaries.md'
(ROOT/'System Design Notes'/filename).write_text(chapter, encoding='utf-8')
metadata = {'label': 'A1', 'chapter': filename, 'words': len(chapter.split()), 'lines': chapter.count('\n'),
    'questions': 30, 'practice_tasks': 10, 'unchecked_learning_items': 12,
    'source_fidelity': sources, 'output_fidelity': ['create', 'createTrace', 'persistence', 'rollback', 'contracts'],
    'mock_minutes': 45, 'verified_checks': proof['total'], 'next': 'A2: Data, caching and scaling'}
(BASE/'content-validation.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
print(json.dumps(metadata, indent=2))
