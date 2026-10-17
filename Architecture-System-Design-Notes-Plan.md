# Plan: Architecture and System Design Placement Handbook

**Extension to the resume-skills syllabus. Backend/SDE first. Researched on 13 October 2026.**

---

## 0. What this adds

The resume-skills handbook explains the tools. This companion explains how to combine them into a working system and defend the design.

The user explicitly requested architectural understanding, how to build systems, and a compiled set of important recurring interview questions.

Deliverables in the completed architecture track:

- This architecture syllabus and writing order.
- [A compiled 60-question bank](Architecture-System-Design-Question-Bank.md), with answer checkpoints and chapter mappings.
- Cross-references in [the resume-skills plan](Resume-Skills-Notes-Plan.md).

All five foundations, fourteen worked systems and final consolidation are now authored in System Design Notes/, alongside the master roadmap: 21 files. This plan and the original question bank remain the syllabus/checkpoint sources; the teaching chapters and final drills supply the worked explanations.

**Organizing principle:** start with a correct system you can build, then change the architecture only when a requirement, bottleneck or failure justifies it.

---

## 1. What the research supports

Three kinds of evidence informed the selection:

1. **Employer expectations.** [Amazon's SDE II preparation page](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep) emphasizes practical, reliable, efficient and scalable design. It is evidence about that role, not a claim that a campus fresher faces the same bar.
2. **Recurring practice prompts.** [Hello Interview's question catalog](https://www.hellointerview.com/learn/system-design/in-a-hurry/problem-breakdowns) and the [System Design Primer](https://github.com/donnemartin/system-design-primer) repeatedly cover link shortening, messaging/feeds, storage and infrastructure designs. [IGotAnOffer's question collection](https://igotanoffer.com/blogs/tech/system-design-interviews) also groups candidate-reported prompts across product and infrastructure systems.
3. **Technical mechanisms.** Official AWS, Microsoft, PostgreSQL, Redis and other documentation supplies the basis for correctness, failure handling and implementation details.

### How to read "common" and "best"

The sources are employer guidance, curated teaching catalogs and candidate reports. They do not establish a complete, unbiased frequency ranking across employers.

Here, "best to study first" means good coverage of reusable patterns, manageable entry-level depth and relevance to this resume. The ordering is a learning recommendation, not a numbered claim about how often a question is asked.

Every case will distinguish:

- **Baseline:** explainable, buildable design for a small deployment.
- **Growth:** address an identified throughput, latency, storage or availability requirement.
- **Deep follow-up:** optional distributed-system complexity.

The main audience is placement/backend/SDE preparation. Senior-level consensus proofs, global active-active payments and building an entire database engine are optional.

---

## 2. Architecture foundations: five teaching sections

**Source folder:** System Design Notes/ (all 21 files authored: roadmap, A0-A4, S0-S13 and consolidation)

| ID | Section | Topics and outcomes | Prerequisites |
| --- | --- | --- | --- |
| A0 | **How to approach a design question** | Clarify actors/use cases; functional vs non-functional requirements; scope; invariants; QPS, peak traffic, storage, bandwidth and concurrency estimates; APIs and data model; baseline architecture; deep-dive selection; trade-offs and interview narration | Resume M0/M6; basic DBMS/CN |
| A1 | **Application architecture and service boundaries** | Layered application; controller/service/repository responsibilities; modular monolith; bounded contexts at introductory depth; monolith vs microservices; synchronous calls vs events; API gateway/BFF; deployment unit vs logical module; a small backend skeleton | A0; one backend framework |
| A2 | **Data, caching and scaling** | Access patterns before database choice; indexes; replicas vs shards; partition keys; hot keys; consistency requirements; cache-aside, TTL, invalidation and stampedes; load balancing and stateless instances; CAP with its actual partition boundary | A0; DBMS; Resume M13-M15 refresher |
| A3 | **Reliable workflows and concurrency** | Timeouts, bounded retries, backoff/jitter; delivery vs effects; idempotency keys and atomic state changes; queue acknowledgements; deduplication; locks/versions/constraints; outbox; saga/compensation; ordering and recovery; schema/event evolution | A0/A2; Resume M9/M15; DBMS transactions |
| A4 | **Operating a secure and observable system** | Tenant boundaries; least privilege; quotas; safe uploads; TLS/secrets; health vs readiness; deployment/draining; logs, metrics and traces; p95/p99; saturation and backpressure; SLOs; failure injection; cost and capacity validation | A1-A3; Resume M8/M16-M19 refresher |

A1 must show actual component responsibilities and a request trace. Naming architectural styles without explaining who owns state and how data moves is insufficient.

For A3, [AWS's retry guidance](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) and [idempotent-API discussion](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) motivate bounded retry and duplicate-handling exercises. [Microsoft's architecture-style guide](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/) supports teaching styles as constraints and trade-offs.

---

## 3. Worked systems: recommended practice order

Evidence labels:

- **C:** recurring design family in the checked interview-preparation catalogs. This is not a verified company-specific question.
- **R:** selected because of this resume.
- **E:** a related extension chosen for pattern coverage.

Start with S0-S4, then S5-S7. S8-S13 deepen the resume connections and fill remaining patterns. If a specific interview focuses on AI, move S11/S12 earlier after their prerequisites.

| ID | System to design | Central reasoning problem | Evidence / priority |
| --- | --- | --- | --- |
| S0 | **URL shortener** | Unique codes, collisions, redirects, expiry, read-heavy caching, basic analytics | C / start here |
| S1 | **Rate limiter** | Fixed/sliding windows and token bucket; local vs shared state; atomic check/update; quotas, clock assumptions and degraded behavior | C+R / early |
| S2 | **Notification and webhook delivery service** | Durable event-to-delivery flow; email/SMS/push adapters; preferences; retries, deduplication, ordering, signatures and provider limits | C+R / early |
| S3 | **File upload, storage and processing service** | Metadata vs object bytes; authorization; direct uploads; multipart/resumability; validation/quarantine; asynchronous processing; deletion and cleanup | C+R / early |
| S4 | **Ticket booking / limited-inventory reservation** | Browse vs reserve paths; temporary holds; atomic inventory changes; expiry; payment races; avoiding overselling and handling late payment | C+R / early |
| S5 | **Chat and real-time messaging** | WebSocket/SSE/polling choices; connection routing; persistence; message IDs, ordering, acknowledgements, offline delivery and reconnect | C / next |
| S6 | **Social feed / photo-sharing service** | Media storage; feed data model; fan-out on write vs read; pagination; celebrity/hot-user handling; freshness and cache trade-offs | C / next |
| S7 | **Background job scheduler and worker platform** | Immediate vs scheduled work; queueing; leases/visibility; retries; worker crashes; idempotency; poison jobs; fairness and backlog | C+R / next |
| S8 | **Checkout, payments and credit ledger** | Order/payment state machines; duplicate callbacks; balance invariants; integer money; append-only records; reconciliation and compensating actions | C+R / resume depth |
| S9 | **Search and autocomplete** | Prefix lookup vs full-text vs semantic retrieval; indexes; ranking; updates; query latency; permission filters and source-of-truth lag | C+E / pattern coverage |
| S10 | **Load balancer and distributed cache** | Routing policies; consistent-hash ring and virtual nodes; placement vs balancing; health checks; hot keys; node churn; cache replication and invalidation | C+R / resume depth |
| S11 | **Multi-tenant SaaS with authentication and permissions** | Tenant identity; roles plus ownership; shared vs isolated storage; BFF/session flow; signed invites; quotas; cross-tenant negative tests | R / high resume relevance |
| S12 | **Multi-tenant RAG knowledge-base platform** | Upload-to-index state machine; async embeddings; tenant-filtered retrieval; versioned/deleted documents; citations; provider limits; evaluation, cost and failure recovery | R / high resume relevance |
| S13 | **Analytics event pipeline and dashboard** | Event contracts/IDs; ingestion; deduplication; event time vs processing time; late data; aggregates; freshness; metric definitions and privacy | C+R / resume depth |

### Optional later designs

These are extension prompts, not prerequisites for the core track:

- Video streaming: uploads, transcoding, manifests, CDN and adaptive delivery.
- Ride-hailing/location service: changing locations, proximity lookup, matching and assignment.
- Web crawler: frontier, deduplication, politeness, retries and scheduling.
- Collaborative editing: operation ordering, conflicts, presence; OT/CRDT overview only.

### Boundaries between related cases

- S2 delivers messages/events to people or external endpoints; S7 executes internal jobs. They share queue mechanics but have different product and completion semantics.
- S4 focuses on scarce-resource reservation; S8 focuses on financial/order state and reconciliation.
- S3 builds the upload/processing foundation; S12 adds retrieval, model calls and AI evaluation.
- S10 extends the load-balancer experience in Resume M27 rather than repeating its definitions.
- Existing OOP BookMyShow is the single-process LLD starting point; S4 explains what changes across several application instances.

---

## 4. What every worked design must contain

Each design follows the same sequence so the reader learns a method, not a memorized diagram.

1. **Prompt and clarification questions:** what changes the architecture?
2. **Requirements and explicit exclusions:** actors, core flows, scale, latency and availability assumptions.
3. **Correctness invariants:** what must never happen?
4. **Capacity estimates:** formulas, units and stated assumptions.
5. **API contract:** request/response shape, errors, pagination, authentication and idempotency where relevant.
6. **Data model:** entities, keys, constraints, indexes and ownership.
7. **Smallest working architecture:** a buildable baseline, often one application and database with a worker when needed.
8. **End-to-end traces:** at least one write path and one read path.
9. **Core implementation:** short code/pseudocode for the defining mechanism, with stated execution guarantees.
10. **Concurrency/failure timeline:** two simultaneous callers or a crash at a meaningful point.
11. **Growth stages:** show the bottleneck before adding caches, replicas, queues or shards.
12. **Security and observability:** trust boundaries, permissions, logs, metrics and useful alerts.
13. **Trade-off table:** the chosen option, a viable alternative and what requirement decides.
14. **How to build it:** ordered tasks, local setup, seed data, endpoints and verification commands.
15. **Interview follow-ups:** short answer checkpoints, deeper extensions and common wrong answers.
16. **Exit checklist and next design.**

Diagrams should show request/data/event direction and distinguish synchronous calls from asynchronous delivery. A box labelled "database" must be accompanied by the relevant tables/collections and access patterns.

A local prototype proves the mechanism it exercises. It does not prove internet-scale throughput or availability.

---

## 5. Implementation and verification expectations

### Default learning stack

- Node.js/TypeScript + Express for the first concrete backend.
- PostgreSQL when relationships, constraints and transactions are central.
- Redis, object storage or a queue only when the design needs that capability.
- Python/FastAPI for AI/ingestion extensions where it fits the resume.
- Docker Compose where it makes the example easier to reproduce.

These are teaching choices. Alternatives are discussed using requirements, not brand preference.

### Required evidence

- Compute capacity estimates with a small script and preserve the assumptions.
- Test duplicate requests, stale state, invalid ownership and concurrency.
- Use real engine behavior for database transactions/locking.
- Use deterministic clocks/fake providers for retry, expiry and payment examples where appropriate.
- Keep verification scripts and fixtures with the examples.
- Record package/runtime versions; do not present a simulated provider response as live evidence.
- Load tests state hardware, payload, concurrency, duration, warmup and error rate.
- Never label a local test as proof of a global guarantee.
- Separate message-delivery semantics from business-effect deduplication; define the scope of any exactly-once claim.
- Distinguish a lease from a permanent lock; expiry alone cannot guarantee a stalled worker stops modifying state.
- For outbox designs, examine publisher crash/retry and consumer duplicates as well as the database commit.
- Start with a database transaction/constraint for reservation correctness; do not present an expiring cache key as a complete booking protocol.

Technical starting points include [PostgreSQL locking](https://www.postgresql.org/docs/17/explicit-locking.html), [Redis counter/rate-limiter examples](https://redis.io/docs/latest/commands/incr/), [S3 multipart uploads](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html), [cache-aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside), [transactional outbox](https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos) and [saga](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga). Provider-specific examples are not universal implementations.

---

## 6. Compiled interview-question bank

The companion bank contains **60 original compiled prompts**, grouped as:

| Questions | Category | Count |
| --- | --- | --- |
| Q01-Q24 | Architecture concepts and decision questions | 24 |
| Q25-Q38 | System-building prompts aligned with S0-S13 | 14 |
| Q39-Q52 | Failure and concurrency follow-ups aligned with S0-S13 | 14 |
| Q53-Q60 | Resume-specific architecture questions | 8 |

Each question includes what a strong answer needs to address and where it will be taught. The bank is a study checklist, not a verbatim interview transcript or a completed solution set.

Suggested practice:

- Explain conceptual questions in 30-90 seconds.
- Sketch a system in 10-15 minutes before reading its chapter.
- Give a complete mock design in 35-45 minutes.
- Introduce one changed requirement or failure midway.
- Afterward, record the missing invariant, weak assumption or unjustified component.

---

## 7. Connection to the original syllabus

Architecture will be interleaved as soon as its prerequisites are ready:

| After studying | Practice |
| --- | --- |
| Resume M0/M5/M6 and basic DBMS | A0/A1, then S0 URL shortener |
| Resume M7-M9 | S1 rate limiting, S2 notifications/webhooks, S11 SaaS permission design |
| Resume M13-M15 and DBMS transactions | A2/A3, S3 file processing, S4 reservations, S7 jobs, S8 payments |
| Resume M16-M19 | A4 and failure/deployment discussions for completed designs |
| CN HTTP/transport and the API stack | S5 chat, S6 feeds, S9 search |
| Resume M22-M26 | S12 RAG |
| Resume M27 | S10 load balancing/cache; validate the documented project assumptions |
| Resume M28 | Q53-Q60 and relevant designs; S13 analytics connects to the later product track |

Product/analytics remains the later track. Its dashboards and metrics can reuse S13 without delaying the backend fundamentals.

### File and website conventions

Planned source files: one roadmap + five foundations + fourteen worked designs + one consolidation = **21 files**.

Use numeric module filenames compatible with the existing sync:
- Part 1: master-roadmap.
- Parts 2-6 / Modules 0-4: A0-A4.
- Parts 7-20 / Modules 5-18: S0-S13.
- Part 21: consolidation.

A0/S0 are syllabus labels; numeric module identifiers remain the file convention. The roadmap must include that mapping.

The master roadmap is now registered as the System Design subject and search tag at `/docs/system-design`. All authored chapters are registered under Foundations, Worked Systems and Revision. Reuse the source-Markdown -> generated-content pipeline; planned chapters have no published routes.

---

## 8. Progress

- [x] Architecture extension requested by the user.
- [x] Employer guidance and recurring question catalogs reviewed.
- [x] Technical primary sources identified and reviewed for the initial plan.
- [x] Five foundation sections and fourteen worked cases selected.
- [x] Sixty questions compiled with answer checkpoints.
- [x] Cross-links added to the resume-skills plan.
- [x] Architecture master roadmap written; existing 60-question bank reproduced with exact checkpoints and mappings.
- [x] A0 authored with 30 interview Q&As, ten exercises and 62 checks: 23 estimate/input, 12 offline-objective, 23 real SQLite repository and four concurrent-invariant checks. Proposed HTTP/auth/deployment boundaries are explicit; temporary data/connections cleaned.
- [x] A1 authored with 30 interview Q&As, ten exercises and 67 checks: four runtime-import boundary, 17 direct service/repository, four transaction and 42 real HTTP assertions. Includes a TypeScript/Express backend, observed request trace, ownership and deployment decisions, fixed public lesson-token scope and temporary-data/listener cleanup.
- [x] A2 authored with 30 interview Q&As, ten exercises and 91 checks: 12 query/index, 16 pagination, 23 basic cache, ten single-flight, eleven invalidation, four independent-cache, two cleanup and thirteen hypothetical scaling-model checks. Includes real SQLite plans/VM work, offset drift, scoped TTL/LRU, stale-refill reproduction and local fencing; distributed replicas/shards/Redis and capacity remain explanatory.
- [x] A3 authored with 30 interview Q&As, ten exercises and 90 checks: 19 retry-policy, 14 atomic-operation, ten lease, twelve consumer-atomicity, eleven delivery-bound, ten concurrency, twelve compensation and two cleanup assertions. Includes real SQLite outbox/inbox recovery, six competing worker calls, bounded claim generations and guarded local compensation; network/provider/broker/full-saga behavior remains outside scope.
- [x] A4 authored with 30 interview Q&As, ten exercises and 93 checks: 17 HTTP policy, 24 upload, seven quota, eleven lifecycle, five saturation, nine telemetry, two cleanup, thirteen offline-indicator and five hypothetical-planning assertions. Includes four owned loopback servers, current membership/scoped queries, private text quarantine, two-connection quota admission and drain/overload behavior; production identity/TLS, antivirus, orchestration and capacity remain outside scope.
- [x] All five foundation teaching chapters A0-A4 authored.
- [x] S0 URL shortener authored with 30 interview Q&As, ten exercises and 118 checks: 16 validation, 24 authority, 16 cache/expiry, twelve analytics, six concurrency, 34 HTTP, two cleanup and eight hypothetical-estimate assertions. Includes unique random-code insert/retry, persistent scoped create replay, four competing worker calls, public GET/HEAD redirects without destination requests, absolute expiry, local disable and bounded lossy analytics.
- [x] S1 rate limiter authored with 30 interview Q&As, ten exercises and 95 checks: eight algorithms, 16 validation, 14 bucket, 13 scope/lifecycle, seven concurrency, 26 HTTP, seven estimates and four cleanup. Includes window approximation counterexamples, atomic shared token decisions, four competing worker calls, clock/refill/cost boundaries, bounded state/reopen, real writer contention and explicit HTTP outage policies.
- [x] S2 notification/webhook delivery authored with 30 interview Q&As, ten exercises and 109 checks: 11 validation, 17 intake, four concurrency, 16 leases, 13 retry, 22 HTTP, 14 network, eight estimates and four cleanup. Includes atomic event/fan-out, original-intent replay, preferences, competing claims, lease fencing/crash budgets, shared 429 cooldowns, raw-byte HMAC, receiver receipt/effect rollback and actual connection loss after commit followed by duplicate-safe retry. Six concurrent worker/request calls use owned local fixtures.
- [x] S3 file upload/storage/processing authored with 30 interview Q&As, ten exercises and 121 checks: 17 validation, 23 intake, 19 processing, 19 lifecycle, 27 HTTP, four concurrency, eight estimates and four cleanup. Includes scoped create replay/capabilities, immutable real files, atomic completion/job, quarantine, guarded worker publication, delete/expiry, orphan reconciliation and private download. Six competing PUT/completion/claim calls and actual artifact-after-metadata-rollback recovery are verified locally; cloud multipart and antivirus remain explicitly unimplemented.
- [x] S4 ticket booking/reservations authored with 30 interview Q&As, ten exercises and 57 local checks: atomic group holds, expiry/replay, two last-seat contenders, signed callback binding, payment/event dedupe, late-charge compensation intent and rollback. No real payment/refund is executed.
- [x] S5 chat/messaging authored with 30 interview Q&As, ten exercises and 59 local checks: durable send/ack replay, room sequence, high-water catchup, bounded lossy hints, membership revocation, monotonic reported reads, restart and four competing calls. Actual transport is HTTP polling; WebSocket is discussed, not implemented.
- [x] S6 social feed/photo sharing authored with 30 interview Q&As, ten exercises and 67 local checks: ready-media/version ownership, durable batched push rollback/frontier, pull merge, follow backfill, current graph/block/delete filtering, scoped keyset cursors and four competing calls. Media is a metadata fixture, not an image/S3 integration.
- [x] S7 job scheduler/workers authored with 30 interview Q&As, ten exercises and 65 local checks: durable occurrence/frontier, original-intent replay, two concurrent claims, tenant admission, fenced leases, bounded renewal/retries, local effect-before-ack recovery, rollback and real HTTP. Explicit fixture time; no broker, cron daemon or remote effect.
- [x] S8 checkout/payments/credit ledger authored with 30 interview Q&As, ten exercises and 62 local checks: separate provider commit and reply-loss injection, catalog snapshot, event/payment/grant dedupe, signed fixture callback, four competing calls, balanced CREDIT journals, nonnegative spends, reversal, rollback and HTTP. No real charge, cash ledger or external refund.
- [x] S9 search/autocomplete authored with 30 interview Q&As, ten exercises and 77 local checks: actual SQLite FTS5, title-token prefixes, source/outbox atomicity, stale/tombstone fences, current tenant/ACL/version before top-k, two competing projectors, local rebuild, rollback and HTTP. No external cluster, semantic model, online reindex or throughput claim.
- [x] S10 load balancer/distributed cache authored with 30 interview Q&As, ten exercises and 69 local checks: 2,000-key ring/remapping sample, distinct copies, live admission/drain labels, TTL/LRU, canonical version probes, stale-fill/version/epoch/incarnation fences, controlled failure/rejoin, four competing calls, rollback/reopen and real edge HTTP. In-process nodes; no upstream network proxy, Redis replication, automatic detector or throughput claim.
- [x] S11 multi-tenant SaaS authored with 30 interview Q&As, ten exercises and 95 local checks: hashed opaque sessions, current role/membership and document/share scope, tenant-switch rotation, removal/logout, last-owner protection, recipient/audience/expiry/revocation-bound invitations, atomic quotas/audit, worker/result rechecks, four competing calls, rollback/reopen and real HTTP. Trusted fixture login; no browser BFF/cookie/CSRF, email, object storage or production RLS integration.
- [x] S12 multi-tenant RAG authored with 30 interview Q&As, ten exercises and 125 local checks: unchanged S11 authority, versioned source/ingest publication, deterministic chunk/vector profiles, current permission/version before top-k, exact request-evidence/citation checks, character-budget reservation/uncertainty, six competing calls, selected judged corpus, deletion/redaction/tombstone, rollback/reopen and real HTTP. Feature-hash vectors and extractive model fixture; no real model/embedding/vector API, tools, stream, object store, provider token/money metering or production quality claim.
- [x] S13 analytics event pipeline/dashboard authored with 30 interview Q&As, ten tasks and 78 local checks: scoped immutable events, timezone normalization, atomic effects/frontier, exact cohorts, explicit lateness, generation rebuild, subject removal/replay marker, four competing calls, rollback/reopen and real aggregate HTTP. No live Kafka/Beam, connector, browser chart or production load claim.
- [x] All fourteen worked systems S0-S13 authored.
- [x] Runnable core mechanisms and verification artifacts created for all 19 teaching chapters; final catalogue preserves 1,600 recorded local assertions with their original runtime/date/scope.
- [x] Final consolidation authored: expanded drills for all 60 bank prompts, fourteen failure cards, 24 confusable pairs, 24 self-tests, six 45-minute mocks, revision routes and a manual-score helper. Learner mastery remains ungraded.
- [x] System Design subject and search tag integrated into the website; all 21 files are published: roadmap, A0-A4, S0-S13 and consolidation.

Authored completion: **all 21 Architecture and System Design files are available**. Continue with consolidation and manual practice; the separate product/analytics track P0-P5 remains later work.
