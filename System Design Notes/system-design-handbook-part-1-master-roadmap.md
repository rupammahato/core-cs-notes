# Architecture and System Design Placement Handbook — Part 1: Master Roadmap

**From a buildable backend to defensible architecture: requirements, state, failures, scale and evidence. Backend/SDE first.**

---

## 0. What is available now

This companion extends the completed [Resume Skills handbook](/docs/resume-skills). That handbook explains the stack and connects it to your projects. This track shows how to assemble a system, implement its defining mechanism and defend its behavior under a changed requirement or failure.

**Organizing principle: start with a correct small system; add architectural complexity only when a requirement, bottleneck or failure justifies it.**

| Item | Current status |
| --- | --- |
| Authored sources | This master roadmap, [A0: How to approach a design question](/docs/system-design/design-method-estimation), [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries), [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling), [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency), [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations), [S0: URL shortener](/docs/system-design/url-shortener), [S1: Rate limiter](/docs/system-design/rate-limiter), [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks), [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing), [S4: Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations), [S5: Chat and real-time messaging](/docs/system-design/chat-messaging), [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing), [S7: Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers), [S8: Checkout, payments and credit ledger](/docs/system-design/checkout-payments-credit-ledger), [S9: Search and autocomplete](/docs/system-design/search-autocomplete), [S10: Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache), [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas), [S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag), [S13: Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline) and [Consolidation and design mocks](/docs/system-design/consolidation) |
| Completed handbook | 21 authored files: roadmap, five foundations, fourteen worked designs and consolidation |
| Foundations A0–A4 | A0–A4 available; all five foundations authored |
| Worked systems S0–S13 | S0–S13 available; all fourteen worked designs authored |
| Interview bank | 60 previously compiled prompts and answer checkpoints, reproduced in §8 |
| Existing bridges | Resume M27 load-balancer mechanisms, M28 project explanations and M29 revision |
| Product/analytics | Separate later track; S13 supplies a technical event-pipeline foundation |

This roadmap links the complete authored track: A0–A4, S0–S13 and final consolidation. All 21 planned files are available on the site. Each teaching chapter has its own implementation, verification scope and unchecked learning checklist; authoring completion does not establish learner mastery or production guarantees.

The repository-root plan and question-bank files remain the planning sources: `Architecture-System-Design-Notes-Plan.md` and `Architecture-System-Design-Question-Bank.md`. Their question checkpoints are included below so you can use them directly on the study site.

---

## 1. What architecture preparation should let you do

After a worked chapter, you should be able to:

1. Clarify the users, core operations, scope and important workload assumptions.
2. State correctness invariants before selecting infrastructure.
3. Propose APIs and a data model with explicit identity, constraints and access patterns.
4. Draw a small baseline and trace at least one read and one write.
5. Explain a concurrent request or crash timeline and its recovery.
6. Identify a demonstrated bottleneck before adding caches, replicas, shards or services.
7. Compare a reasonable alternative using the actual requirement.
8. Build and verify the defining mechanism under a stated environment and evidence boundary.

An architecture diagram is useful when its arrows explain who calls whom, what is persisted and what can be retried. “Database,” “queue” and “cache” labels alone do not establish a transaction boundary, durable completion or fresh permission checks.

Existing OOP material teaches single-process object responsibilities. This track adds communicating processes, durable state, independent failures and workload limits. It builds on DBMS/CN/OS concepts rather than replacing them with tool names.

---

## 2. How the sections were chosen

The ordering combines the earlier research plan, reusable design patterns, entry-level buildability and your resume's specific follow-ups. It is not a measured ranking of company question frequency.

Employer guidance is useful context: Amazon's SDE II page emphasizes practical, accurate, efficient, reliable and scalable design. Its role level is above a campus-entry baseline, so the companion starts smaller and separates deeper extensions. [Amazon SDE II preparation](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep).

The original question-bank research used curated practice catalogs to identify recurring system families. A catalog is evidence about its own selection, not an unbiased record of all employer interviews. The refreshed [Hello Interview catalog](https://www.hellointerview.com/learn/system-design/in-a-hurry/problem-breakdowns) is one such practice source; technical behavior will be checked against primary documentation and executed examples in the relevant chapter.

Every design has three depths:

| Depth | What it means |
| --- | --- |
| Baseline | Small, correct and explainable application with real data ownership and APIs |
| Growth | Change a measured constraint: traffic, latency, storage, availability or operations |
| Deep follow-up | Optional distributed complexity with explicit failure/consistency assumptions |

The default audience is backend/SDE placement preparation. Building a database engine, global active-active payments or consensus proofs is not required before you can explain a reservation transaction or upload state machine.

---

## 3. Complete syllabus and numeric mapping

The labels A0–A4 and S0–S13 identify learning sections. Numeric modules and part numbers identify files; they are not the Resume Skills module numbers. For example, architecture numeric module 5 is S0, not Resume M5.

| Label | Numeric module / part | Section | Hours | Requires in this track | Resume refresher | Status |
| --- | --- | --- | --- | --- | --- | --- |
| A0 | 0 / 2 | [How to approach a design question](/docs/system-design/design-method-estimation) | 3–4 |  | [M0](/docs/resume-skills/how-backend-works), [M6](/docs/resume-skills/rest-apis-http) | Available |
| A1 | 1 / 3 | [Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries) | 3–4 | A0 | [M5](/docs/resume-skills/express-backend-structure), [M11](/docs/resume-skills/flask-fastapi-python-request-handling), [M12](/docs/resume-skills/django-django-rest-framework) | Available |
| A2 | 2 / 4 | [Data, caching and scaling](/docs/system-design/data-caching-scaling) | 4–5 | A0 | [M13](/docs/resume-skills/postgresql-backend), [M14](/docs/resume-skills/mongodb-backend), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) | Available |
| A3 | 3 / 5 | [Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency) | 4–5 | A0, A2 | [M9](/docs/resume-skills/webhooks-payments-reliable-integrations), [M13](/docs/resume-skills/postgresql-backend), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) | Available |
| A4 | 4 / 6 | [Operating a secure and observable system](/docs/system-design/secure-observable-operations) | 3–4 | A1, A2, A3 | [M8](/docs/resume-skills/api-security-authorization-multi-tenancy), [M16](/docs/resume-skills/docker-fundamentals), [M17](/docs/resume-skills/linux-deployment-nginx-pm2), [M18](/docs/resume-skills/aws-gcp-fundamentals), [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance) | Available |
| S0 | 5 / 7 | [URL shortener](/docs/system-design/url-shortener) | 3–4 | A0, A1, A2, A3, A4 | [M6](/docs/resume-skills/rest-apis-http), [M13](/docs/resume-skills/postgresql-backend) | Available |
| S1 | 6 / 8 | [Rate limiter](/docs/system-design/rate-limiter) | 4–5 | A0, A1, A2, A3, A4 | [M7](/docs/resume-skills/authentication-sessions-jwt-oauth), [M8](/docs/resume-skills/api-security-authorization-multi-tenancy), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) | Available |
| S2 | 7 / 9 | [Notification and webhook delivery service](/docs/system-design/notifications-webhooks) | 4–5 | A0, A1, A2, A3, A4, S1 | [M9](/docs/resume-skills/webhooks-payments-reliable-integrations), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) | Available |
| S3 | 8 / 10 | [File upload, storage and processing service](/docs/system-design/file-upload-processing) | 4–5 | A0, A1, A2, A3, A4 | [M8](/docs/resume-skills/api-security-authorization-multi-tenancy), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion), [M18](/docs/resume-skills/aws-gcp-fundamentals), [M23](/docs/resume-skills/rag-document-ingestion) | Available |
| S4 | 9 / 11 | [Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations) | 5–6 | A0, A1, A2, A3, A4 | [M9](/docs/resume-skills/webhooks-payments-reliable-integrations), [M13](/docs/resume-skills/postgresql-backend), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) | Available |
| S5 | 10 / 12 | [Chat and real-time messaging](/docs/system-design/chat-messaging) | 4–6 | A0, A1, A2, A3, A4 | [M6](/docs/resume-skills/rest-apis-http), [M7](/docs/resume-skills/authentication-sessions-jwt-oauth), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) | Available |
| S6 | 11 / 13 | [Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing) | 4–6 | A0, A1, A2, A3, A4, S3 | [M14](/docs/resume-skills/mongodb-backend), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion), [M20](/docs/resume-skills/react-fundamentals) | Available |
| S7 | 12 / 14 | [Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers) | 4–5 | A0, A1, A2, A3, A4 | [M15](/docs/resume-skills/caching-background-jobs-data-ingestion), [M17](/docs/resume-skills/linux-deployment-nginx-pm2) | Available |
| S8 | 13 / 15 | [Checkout, payments and credit ledger](/docs/system-design/checkout-payments-credit-ledger) | 5–7 | A0, A1, A2, A3, A4, S4, S7 | [M9](/docs/resume-skills/webhooks-payments-reliable-integrations), [M13](/docs/resume-skills/postgresql-backend), [M22](/docs/resume-skills/llm-ai-api-fundamentals), [M28](/docs/resume-skills/resume-project-experience-deep-dives) | Available |
| S9 | 14 / 16 | [Search and autocomplete](/docs/system-design/search-autocomplete) | 4–6 | A0, A1, A2, A3, A4, S3, S7 | [M13](/docs/resume-skills/postgresql-backend), [M23](/docs/resume-skills/rag-document-ingestion), [M24](/docs/resume-skills/embeddings-pinecone-pgvector) | Available |
| S10 | 15 / 17 | [Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache) | 4–6 | A0, A1, A2, A3, A4 | [M15](/docs/resume-skills/caching-background-jobs-data-ingestion), [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance), [M27](/docs/resume-skills/system-design-load-balancer) | Available |
| S11 | 16 / 18 | [Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas) | 4–6 | A0, A1, A2, A3, A4, S1 | [M7](/docs/resume-skills/authentication-sessions-jwt-oauth), [M8](/docs/resume-skills/api-security-authorization-multi-tenancy), [M21](/docs/resume-skills/nextjs-api-routes-tailwind), [M28](/docs/resume-skills/resume-project-experience-deep-dives) | Available |
| S12 | 17 / 19 | [Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag) | 5–7 | A0, A1, A2, A3, A4, S3, S7, S9, S11 | [M22](/docs/resume-skills/llm-ai-api-fundamentals), [M23](/docs/resume-skills/rag-document-ingestion), [M24](/docs/resume-skills/embeddings-pinecone-pgvector), [M25](/docs/resume-skills/langchain-langgraph-llamaindex), [M26](/docs/resume-skills/neo4j-graph-backed-applications) | Available |
| S13 | 18 / 20 | [Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline) | 4–6 | A0, A1, A2, A3, A4, S2, S7 | [M15](/docs/resume-skills/caching-background-jobs-data-ingestion), [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance), [M28](/docs/resume-skills/resume-project-experience-deep-dives) | Available |
| Revision | — / 21 | [Consolidation and design mocks](/docs/system-design/consolidation) | 2–3 | All foundations and worked designs | [M29](/docs/resume-skills/consolidation-interview-drills) | Available |

The planned source conventions are:

- Part 1: `system-design-handbook-part-1-master-roadmap.md`.
- A0–A4: parts 2–6, numeric modules 0–4.
- S0–S13: parts 7–20, numeric modules 5–18.
- Part 21: `system-design-handbook-part-21-consolidation.md`.

The first-pass teaching/build estimates total **77–105 active hours**, including the planned consolidation and excluding this roadmap, breaks, deep extensions and repeated mocks. They are planning estimates, not measured time or a promise of mastery. Use earlier familiarity to shorten a refresher; do not skip the defining failure case merely to meet the estimate.

---

## 4. Foundations: what comes before the worked designs

**A0 — method and estimation:** learn to turn an ambiguous request into actors, operations, non-goals, workload units, APIs/data and invariants. Estimates guide a choice; assumed per-instance capacity must not be presented as a measured result.

**A1 — responsibilities and boundaries:** trace the controller/service/data layers in a buildable application. Separate a logical module from a deployment unit and a network boundary. Compare monolith/modular monolith/services without assuming more boxes make the design better. Architecture styles carry constraints and trade-offs, not a mandatory technology list. [Microsoft architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/).

**A2 — data, cache and scale:** choose storage/indexes from operations and invariants. Distinguish source of truth, replicas, shards and derived caches. Define the stale behavior you permit before proposing TTL or invalidation.

**A3 — reliable workflows:** walk through concurrent callers, retries and crash/ack gaps. Explain which condition/effect shares a transaction, what is outside it and how replay/reconciliation works. Bounded retries need operation safety and a total budget; idempotency needs a precise business identity. [AWS retry guidance](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter), [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

**A4 — secure operation:** carry verified identity and resource permission across all data paths; define quotas, readiness, draining, telemetry and capacity evidence. An available process is not automatically a useful or authorized service.

The writing route is foundations first, then S0–S13. If you already understand equivalent mechanisms, the prerequisite column lets you revisit them selectively. Early cases use A3 and the resume job/payment chapters for basic workflow reasoning; they do not require later S7/S8 implementations to exist.

---

## 5. Worked systems: the mechanism behind each name

| Label | Defining mechanism to build and explain |
| --- | --- |
| A0 | Scope, actors, requirements, invariants, workload/units, APIs/data, baseline and trade-offs. |
| A1 | Controllers/services/data access, modular baseline, state ownership, synchronous calls/events, proxy/gateway/BFF. |
| A2 | Access patterns, indexes, replicas/shards, cache coherence, hot keys and explicit consistency requirements. |
| A3 | Deadlines/retries, operation identity, constraints/versions/locks, outbox, recovery and compensation. |
| A4 | Tenant scope, least privilege, quotas, safe uploads, readiness/drain, telemetry, SLOs and capacity evidence. |
| S0 | Create/redirect contracts, unique codes, collision handling, expiry, cache and bounded analytics. |
| S1 | Window/token-bucket algorithms, local/shared atomic decisions, quota keys, clocks and degraded behavior. |
| S2 | Preferences/subscriptions, durable delivery attempts, signatures, retries, duplicate effects and provider limits. |
| S3 | Metadata/object boundaries, authorization, upload completion, validation/quarantine, jobs and cleanup. |
| S4 | Scarce inventory, holds, authoritative expiry, atomic reservation, concurrent callers and late payment. |
| S5 | Connections, durable messages, message IDs, ordering/ack scope, offline fetch and reconnect. |
| S6 | Post/media ownership, feed access patterns, fan-out choice, pagination, hot users and freshness. |
| S7 | Job identity/state, schedules, claims/leases, retries, worker crashes, fairness and backlog. |
| S8 | Order/payment states, atomic ledger effects, idempotency, provider ambiguity and reconciliation. |
| S9 | Prefix/full-text/semantic access, source/index lag, ranking, permission, updates and latency. |
| S10 | Placement versus load, membership/health, hot keys, replicas, invalidation and node rejoin. |
| S11 | Tenant identity, roles/ownership/sharing, sessions/BFF, invitations, quotas and negative tests. |
| S12 | Versioned ingestion, scoped retrieval, accepted citations, model/tool budgets, evaluation and deletion. |
| S13 | Event contracts/identity, ingestion, event time, duplicate/late data, aggregates and metric definitions. |

Study S0–S4 first: identity/collisions, shared quotas, delivery, uploads and scarce resources give reusable patterns. S5–S7 add connection/feed/worker lifecycles. S8–S13 deepen payments, search, infrastructure, multi-tenancy, RAG and event analytics.

### Keep related cases distinct

- S2 delivers notifications/webhooks; S7 executes internal jobs. They share retry mechanics but have different recipients, status and completion semantics.
- S4 owns inventory/hold correctness; S8 owns payment/order/ledger correctness. A late payment needs an explicit decision across that boundary.
- S3 establishes upload/storage/processing; S12 adds retrieval, model work, current evidence and evaluation.
- S9 covers prefix/full-text/semantic search choices; S12 is a complete permission-aware RAG application.
- S10 extends [Resume M27](/docs/resume-skills/system-design-load-balancer) into cache ownership, replicas, invalidation and rejoin behavior rather than repeating the same ring definition.
- S13 is a technical event-processing design. It does not mark the later product/analytics curriculum complete.

Existing OOP booking examples are a useful single-process starting point for S4. The architecture case must explain what changes when independent application instances share authoritative inventory.

---

## 6. What every worked chapter will contain

| Step | Reviewable artifact |
| --- | --- |
| Clarify | Actors, core flows, changed requirements and explicit exclusions |
| Define correctness | Named invariant and the authority that enforces it |
| Estimate | Inputs, units, formulas and preserved assumptions |
| Specify | API contracts, resource identity, errors and pagination/idempotency where needed |
| Model data | Entities, keys, constraints, indexes and state ownership |
| Build a baseline | Small architecture with useful read/write traces |
| Implement | Defining mechanism with stated execution/transaction guarantees |
| Break it | Two callers or a crash at a meaningful boundary |
| Recover | Durable state, safe replay/reconciliation and cleanup |
| Grow | Named bottleneck and justified next component |
| Operate | Identity/permissions, limits, readiness, logs/metrics/traces and failure visibility |
| Compare | Chosen option, viable alternative and deciding requirement |
| Reproduce | Setup, seed inputs, commands, versions and actual outputs |
| Rehearse | Follow-ups, wrong answers, practice tasks and unchecked exit items |

An answer should identify whether each arrow is a synchronous request, an asynchronous delivery or a data-replication/update path. Distinguish accepted work from completed work, and execution state from external effects.

---

## 7. Implementation and verification rules

The planned default is Node.js/TypeScript with Express for early concrete backends, PostgreSQL when constraints/transactions are central, and Python/FastAPI for suitable AI/ingestion work. Redis, object storage, queues and Docker are introduced when useful to the case. These are teaching choices; the chapter must justify the capability, not assume the brand is the requirement.

Each implementation will record what actually ran. Real database claims need real engine behavior; a fake provider or clock must be labeled. A local test proves selected fixture behavior, not internet-scale availability, hosted-provider semantics or real model quality.

| Mechanism | Required verification direction |
| --- | --- |
| Unique identity | Collision/duplicate input, storage-enforced rule and safe retry |
| Quota/reservation | Concurrent callers at the final available unit |
| External work | Commit/ack gap, duplicate delivery and ambiguous response |
| Expiry/lease | Boundary time, stale owner and late work; expiry alone is not proof a worker stopped |
| Source/index lifecycle | Late revision, delete/revoke, partial publication and current acceptance |
| Permission | Wrong tenant/resource/action through reads, lists, jobs and derived stores |
| Overload | Bounded admission/queues/pools, deadlines and cleanup |
| Performance | Workload/resources, successful goodput, latency/errors and duration |

Preserve raw fixture inputs and named assertions. Keep production metrics separate from estimates and local observations. Provider-specific patterns need their own boundary: a transaction protects the local records inside it, while an external request may need a separate effect identity and recovery path.

This roadmap validates syllabus/question/link consistency and site integration only. No architecture service, database experiment, cloud resource, payment call or model inference is executed here.

---

## 8. Compiled 60-question bank

The following rows reproduce the existing root bank's questions, checkpoints and mappings. They are prompts for preparation, not completed worked answers or verbatim interview transcripts. A0/S0 labels refer to this companion; Resume M labels refer to the completed stack handbook.

| Range | Category | Count |
| --- | --- | --- |
| Q01–Q24 | Architecture concepts and decisions | 24 |
| Q25–Q38 | System-building prompts for S0–S13 | 14 |
| Q39–Q52 | Failure/concurrency follow-ups for S0–S13 | 14 |
| Q53–Q60 | Resume-specific architecture questions | 8 |

### Architecture concepts and decisions

| ID | Question | Answer checkpoints | Chapter |
| --- | --- | --- | --- |
| Q01 | How do you turn an ambiguous product request into a design scope? | Actors, three core flows, explicit exclusions, functional/non-functional requirements and a correctness invariant. | A0 |
| Q02 | How would you estimate average/peak request rate and in-flight work? | Users and actions -> requests/day -> requests/second; state peak assumptions; distinguish latency, throughput and concurrency. | A0 |
| Q03 | How do you estimate storage and bandwidth without false precision? | Record/payload size, retention, read/write volume, indexes/replication overhead, units and a sensitivity check. | A0 |
| Q04 | When would you scale up versus scale out? | Identify the saturated resource, state/correctness constraints, resource ceiling, operational cost and measurement. | A2/A4 |
| Q05 | Would you start this product as a monolith, modular monolith or microservices? | Team/deployment boundaries, ownership, change rate, failure isolation and the cost of remote calls. | A1 |
| Q06 | How do you decide module/service boundaries and who owns the data? | Business capability, invariants, ownership, APIs, coupling and cross-boundary transactions. | A1 |
| Q07 | When should a request use a synchronous call, a queue or an event? | Latency, immediate response needs, decoupling, completion semantics, backlog and recovery. | A1/A3 |
| Q08 | How do a reverse proxy, load balancer, API gateway and BFF differ? | The responsibility and placement of each; overlapping implementations; one request trace without redundant boxes. | A1 |
| Q09 | What makes an application instance stateless, and when are sticky sessions useful? | Where sessions/state live, reconnection/failover, shared stores, affinity limits and scale-out implications. | A1/A2 |
| Q10 | How do access patterns determine the database and schema? | Reads/writes, relationships, query shapes, constraints, consistency and a concrete index choice. | A2 |
| Q11 | How would you diagnose a slow query before changing the architecture? | Query plan, selectivity, indexes, N+1, returned rows, locks and reproducible before/after measurement. | A2/A4 |
| Q12 | How do replication, partitioning and sharding solve different problems? | Read scale vs data placement/write scale; lag, shard keys, hot partitions, joins and operational trade-offs. | A2 |
| Q13 | Where does this design require strong consistency, and where is eventual consistency acceptable? | Name the operation/invariant; user-visible stale behavior; read-after-write and partition trade-offs. | A2 |
| Q14 | Where would you add a cache, and how would you invalidate it? | Source of truth, key, TTL, update path, stale-read tolerance and failure behavior. | A2 |
| Q15 | How do you handle a hot key, cache stampede or mass expiry? | Identify the traffic shape; coalescing, jitter, bounded stale reads, spreading load and origin protection. | A2/A4 |
| Q16 | When do you need a work queue versus publish/subscribe? | One logical job vs multiple interested consumers; acknowledgements, retention, ordering and independent progress. | A3 |
| Q17 | What do at-most-once, at-least-once and exactly-once mean here? | Define delivery/effect scope; crash/ack timeline; duplication/loss risks; avoid an unscoped exactly-once claim. | A3 |
| Q18 | How should timeouts and retries be chosen? | End-to-end deadline, retryable errors, bounded attempts, backoff/jitter, retry amplification and operation safety. | A3 |
| Q19 | How would you make a create/payment operation idempotent? | Client key scope, request equivalence, atomic effect plus dedupe record, saved response, concurrent retries and retention. | A3/S8 |
| Q20 | Would you use a database lock, version check, unique constraint or distributed lease? | State/invariant ownership; contention; transactional boundary; crash/expiry behavior; retries and fencing where needed. | A3 |
| Q21 | What problem does the transactional outbox solve? | Database commit plus event publication dual-write gap; atomic local outbox write; publisher retries and consumer dedupe. | A3 |
| Q22 | When would you use a saga, and what can compensation fail to undo? | Sequence of local commits; business compensation, external side effects, recovery ownership and reconciliation. | A3 |
| Q23 | How would you enforce tenant isolation across an entire request path? | Trusted tenant identity, authorization, query filters, cache/queue keys, files/vector search, logs and negative tests. | A4/S11 |
| Q24 | How do you know whether the design is reliable and fast enough? | SLOs, p95/p99 and error rate, saturation, traces, realistic load/failure tests, capacity headroom and cost. | A4 |

### System-building prompts

| ID | Question | Answer checkpoints | Chapter |
| --- | --- | --- | --- |
| Q25 | Design a URL-shortening service. | Create/redirect APIs, unique code generation, collision handling, schema, expiry, cache and analytics trade-offs. | S0 |
| Q26 | Design a rate limiter for an API served by several application instances. | Limiter algorithm, key/quota scope, atomic updates, shared state, bursts, expiry and degraded behavior. | S1 |
| Q27 | Design a notification service that also supports customer webhooks. | Event storage, subscriptions/preferences, channel workers, retry schedule, signatures, deduplication and delivery status. | S2 |
| Q28 | Design a secure file-upload and asynchronous processing service. | Metadata/object separation, direct upload authorization, multipart completion, validation, job state, download permissions and cleanup. | S3 |
| Q29 | Design ticket booking or a limited-stock reservation system. | Browse vs reserve, per-resource inventory state, holds/expiry, transaction/constraint, payment integration and release/refund. | S4 |
| Q30 | Design a chat service with online and offline messaging. | Connection routing, persistent messages, identifiers, ordering scope, acknowledgements, offline fetch, reconnect and permissions. | S5 |
| Q31 | Design a social feed or photo-sharing service. | Post/media storage, follow graph, feed generation, read/write fan-out, pagination, hot users and freshness. | S6 |
| Q32 | Design a background-job scheduler and worker platform. | Job contract/state, schedules, durable queue, claim/lease, concurrency limits, retry/backoff, poison jobs and monitoring. | S7 |
| Q33 | Design checkout, payments and a usage-credit ledger. | Order/payment states, integer money, atomic ledger effects, idempotency, external outcomes, reconciliation and auditability. | S8 |
| Q34 | Design search and autocomplete for a product catalog or documents. | Query semantics, source data, prefix/full-text/semantic indexes, ranking, updates, authorization and latency. | S9 |
| Q35 | Design request routing and a distributed cache across changing nodes. | Hash placement, virtual nodes, membership/health, remapping, hot keys, replica choice, TTL and failure routing. | S10 |
| Q36 | Design a multi-tenant SaaS with roles, document sharing and expiring invitations. | Tenant and ownership model, auth/BFF, role checks, invite lifecycle, quotas, storage isolation and tests. | S11 |
| Q37 | Design a multi-tenant RAG knowledge-base service. | Upload/ingestion state, chunk/version metadata, embeddings, retrieval permissions, generation/streaming, evaluation, deletion and cost. | S12 |
| Q38 | Design an analytics event-ingestion pipeline and dashboard. | Event IDs/schema, ingestion/queueing, dedupe, event time, aggregates, late data, dashboard freshness and privacy. | S13 |

### Failure and concurrency follow-ups

| ID | Question | Answer checkpoints | Chapter |
| --- | --- | --- | --- |
| Q39 | Two URL creators generate the same short code. What happens? | Uniqueness enforced at storage, collision detection/retry, custom aliases, idempotency and deterministic tests. | S0 |
| Q40 | Two API servers both admit the final request in a quota. How do you prevent it? | Atomic shared decision/update, algorithm boundary behavior, consistent keying, time assumptions and failure policy. | S1 |
| Q41 | A webhook receiver accepts an event but the acknowledgement is lost. What happens next? | Sender retries; receiver deduplicates effects; saved delivery attempts/status; bounded retries and replay. | S2 |
| Q42 | A user uploads a file, but the completion callback or processing worker crashes. How do you recover? | Durable state, idempotent completion/job, reconciliation, orphan/partial cleanup and safe retry. | S3 |
| Q43 | Two users reserve the last seat while one payment arrives after hold expiry. What should happen? | Atomic reservation, authoritative expiry/version recheck, late-payment handling and explicit refund/reconciliation. | S4 |
| Q44 | A chat client disconnects after sending and resends on reconnect. How do you avoid confusing duplicates? | Client message ID, persistence/ack boundary, dedupe, reconnect cursor and defined ordering scope. | S5 |
| Q45 | A celebrity publishes a post and fan-out overloads the system. What changes? | Hybrid read/write fan-out, asynchronous/batched work, hot-user handling, feed latency and backpressure. | S6 |
| Q46 | A worker finishes its effect but crashes before acknowledging the job. What happens on retry? | Redelivery, durable idempotency with the business effect, lease/ack scope and crash-point testing. | S7 |
| Q47 | A payment provider succeeds, but your request times out and the client retries. What do you return? | Stable operation ID, unknown/pending state, provider verification/webhook, atomic ledger effect and reconciliation. | S8 |
| Q48 | A document is deleted or access is revoked while the search index is stale. How do you avoid leaking it? | Authoritative permission enforcement, deletion/version propagation, result filtering and cache/index lag handling. | S9 |
| Q49 | A cache/backend node fails, then rejoins. What happens to placement, load and stale values? | Membership and health state, bounded remapping, ownership/replication, hot spots, invalidation and measured behavior. | S10 |
| Q50 | A valid user changes the document or tenant ID in a request. How is access rejected? | Server-derived tenant context, resource-level checks, all data paths including lists/jobs, and negative tests. | S11 |
| Q51 | A document is updated while embedding retries run, or one tenant's chunks reach another tenant's query. How do you prevent that? | Document/version IDs, idempotent indexing, stale-job checks, tenant-scoped keys/filters and retrieval-time authorization. | S12 |
| Q52 | An event is duplicated or arrives late, after the dashboard aggregate was computed. How do you correct the metric? | Event identity, bounded dedupe/retention assumptions, event-time windows, correction/recomputation and denominator consistency. | S13 |

### Resume-specific architecture questions

| ID | Question | Answer checkpoints | Chapter |
| --- | --- | --- | --- |
| Q53 | Explain your consistent-hashing load balancer: why that policy, and what did your benchmark actually establish? | Ring lookup/virtual nodes, failure detection, placement vs load balance, remapping denominator, workload and reproducible metrics. | Resume M27-M28; S10 |
| Q54 | Trace authentication from Next.js through the BFF to FastAPI in your AI research platform. | Trust boundaries, credentials, server-side verification, session/JWE handling where documented, authorization and token exposure. | Resume M7-M8/M28; S11 |
| Q55 | How would you design signed, expiring and revocable candidate invitations with scoped rate limits? | Token creation/verification, expiry/revocation source of truth, audience/scope, replay/abuse handling and ownership checks. | Resume M7-M8/M28; S1/S11 |
| Q56 | How would you make external spreadsheet ingestion recover from partial batches, timezone ambiguity and nested-record loss? | Input contracts, UTC semantics, stable matching/upserts, transaction/batch policy, validation, checkpoints and reconciliation. | Resume M15/M28; S7/S13 |
| Q57 | How would you build an SLA engine with working-day deadlines and tiered escalation? | Calendar/timezone model, task state machine, scheduled scan vs events, idempotent alerts, audit log and restart behavior. | Resume M15/M28; S2/S7 |
| Q58 | How would you meter several AI providers and debit credits without charging twice? | Provider usage normalization, pricing versions, integer/decimal accounting, reservations/settlement, idempotent ledger and failed-call policy. | Resume M9/M22/M28; S8 |
| Q59 | How would you isolate each tenant's uploaded research, vector retrieval and graph reads? | Tenant identity across storage/jobs/retrieval/graphs, access model, index strategy, revocation and cross-tenant tests. | Resume M8/M23-M26/M28; S11/S12 |
| Q60 | How would you defend the traffic, performance and availability claims for the fest website? | Define users vs sessions vs concurrent requests, measurement window, workload, p95/error rate, monitoring and source evidence. | Resume M19/M28; A0/A4 |

---

## 9. How to practice the bank

Begin with **Q01, Q02, Q06, Q10, Q14, Q19, Q25 and Q39**. This set moves a small URL service from scope and data ownership to cache, operation identity and collision handling. It is a practice route through authored worked explanations, followed by the final consolidation drills.

Then add Q26/Q40 for quota races, Q27/Q41 for delivery ambiguity, Q28/Q42 for upload recovery and Q29/Q43 for reservations/late payment. Later pair each system prompt Q25–Q38 with its failure prompt Q39–Q52 before spending time on a more elaborate scale diagram.

For each answer, record:

1. The requirement or assumption that changes the design.
2. The invariant and its state owner.
3. One request/state transition and one failure timeline.
4. A viable alternative and its cost.
5. What evidence would establish the behavior.

Practice conceptual answers in roughly 30–90 seconds, a first sketch in 10–15 minutes and a full design in 35–45 minutes. These are editorial exercise targets, not observed company formats. Introduce a changed requirement midway and record what you missed.

Use the root bank's diagnostic scale: 0 for unable to explain, 1 for vocabulary only, 2 for a coherent mechanism, 3 for mechanism plus trade-off/failure/evidence. The roadmap does not grade you automatically or imply that a score predicts an interview outcome.

---

## 10. Prerequisites and study routes

### Foundations-first route

```text
Resume API/data/security basics + core CS
 -> A0 -> A1/A2 -> A3 -> A4
 -> S0–S4 -> S5–S7 -> S8–S13 -> consolidation
```

The arrows summarize learning order, not runtime service calls. The syllabus table gives the explicit prerequisites; later designs may depend on earlier worked mechanisms.

### Resume-focused revisits

| Goal | Relevant path |
| --- | --- |
| Candidate invitations and org permissions | A0–A4, S1/S11; Resume M7/M8/M28 |
| Payroll SLA and external file sync | A3/A4, S2/S3/S7/S13; Resume M15/M28 |
| Zyke payment and usage effects | A2/A3/A4, S8; Resume M9/M22/M28 |
| Load-balancer project | A0/A2/A4, S10; Resume M19/M27/M28 |
| 10X or Membition RAG | A0–A4, S3/S7/S9/S11/S12; Resume M22–M26/M28 |
| Fest traffic and operations | A0/A4, S3/S4/S8/S13; Resume M19–M21/M28 |

These are revision routes through authored chapters. Use the existing [M28 project explanations](/docs/resume-skills/resume-project-experience-deep-dives) and [M29 revision tools](/docs/resume-skills/consolidation-interview-drills) alongside the completed architecture companion. Unresolved original project details and benchmarks remain unresolved unless their own evidence becomes available.

---

## 11. Technical reading map

The references below are the initial reading map for the authored chapters. Current documentation is not a claim that a local prototype has implemented every feature or that an older project used the same version.

| Area | Primary starting point |
| --- | --- |
| Architecture styles | [Microsoft architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/) |
| Retry budget and safety | [AWS timeouts/retries](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter), [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) |
| Concurrent state | [PostgreSQL 18 locking](https://www.postgresql.org/docs/18/explicit-locking.html) |
| Cache coherence | [Microsoft cache-aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) |
| Upload lifecycle | [S3 multipart uploads](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html) |

Other mechanisms retain the fuller reference map in the root architecture plan and prior Resume Skills chapters. Individual chapters record their own reviewed references and runtime evidence. This initial reading map was checked on **16 October 2026**; the authored track was completed on **18 October 2026**.

---

## 12. Authored progress and learning checklist

| Authoring milestone | Status |
| --- | --- |
| Root architecture syllabus and 60-question bank | Compiled |
| Master roadmap and embedded bank | Available |
| Foundation teaching chapters | A0–A4 available; all five foundations authored |
| Worked implementations and their failure evidence | S0–S13 available; all fourteen worked designs authored |
| Architecture consolidation | [Available: pattern map, all 60 bank drills, six mocks and final self-test](/docs/system-design/consolidation) |

Learning items remain unchecked until you can explain/build the corresponding mechanism:

- [ ] A0: How to approach a design question
- [ ] A1: Application architecture and service boundaries
- [ ] A2: Data, caching and scaling
- [ ] A3: Reliable workflows and concurrency
- [ ] A4: Operating a secure and observable system
- [ ] S0: URL shortener
- [ ] S1: Rate limiter
- [ ] S2: Notification and webhook delivery service
- [ ] S3: File upload, storage and processing service
- [ ] S4: Ticket booking and limited-inventory reservation
- [ ] S5: Chat and real-time messaging
- [ ] S6: Social feed and photo sharing
- [ ] S7: Background job scheduler and worker platform
- [ ] S8: Checkout, payments and credit ledger
- [ ] S9: Search and autocomplete
- [ ] S10: Load balancer and distributed cache
- [ ] S11: Multi-tenant SaaS with authentication and permissions
- [ ] S12: Multi-tenant RAG knowledge-base platform
- [ ] S13: Analytics event pipeline and dashboard
- [ ] Revision: Consolidation and design mocks

---

## 13. Continue with revision

Start with [A0: How to approach a design question](/docs/system-design/design-method-estimation), then [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries). Continue with [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling). Continue with [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency). Finish the foundations with [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations). Continue with [S0: URL shortener](/docs/system-design/url-shortener), the first worked design. Continue with [S1: Rate limiter](/docs/system-design/rate-limiter) for window/token-bucket algorithms, atomic quota decisions and failure/degraded behavior. Continue with [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks) for durable delivery attempts, signatures, retries, duplicate effects and provider limits. Continue with [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing) for metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup. Continue with [S4: Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations), [S5: Chat and real-time messaging](/docs/system-design/chat-messaging) and [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing). They develop inventory/payment boundaries, durable reconnectable messaging and privacy-aware hybrid feeds. Continue with [S7: Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers), [S8: Checkout, payments and credit ledger](/docs/system-design/checkout-payments-credit-ledger) and [S9: Search and autocomplete](/docs/system-design/search-autocomplete). They develop recoverable job effects, uncertain payment commits, balanced credit posting and current-authorized search over asynchronous projections. Continue with [S10: Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache) and [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas). They develop placement versus live load, current cache version/rejoin fences, tenant/session/resource authority, invitations, quotas and scoped delayed work. Continue with [S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag) for versioned ingest, current authorized retrieval, request evidence and citation acceptance, bounded uncertain generation and deletion. Its runnable vectors/model are deterministic local fixtures. Finish with [S13: Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline), architecture part 20 / numeric module 18, for event identity, atomic progress, cohorts, late data, rebuild and privacy. Then use [Consolidation and design mocks](/docs/system-design/consolidation), Part 21, for cross-system revision and manual self-assessment.

The Architecture and System Design track is fully authored: roadmap, all foundations A0–A4, all worked systems S0–S13 and consolidation, 21 files. No planned architecture teaching chapter remains unfinished. Learning checklists remain unchecked for manual self-assessment. The separate product/analytics track P0–P5 remains later work.
