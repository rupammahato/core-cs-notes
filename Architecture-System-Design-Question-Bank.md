# Architecture and System Design Interview Question Bank

**60 compiled prompts for backend/SDE placement preparation. Researched and assembled on 13 October 2026.**

This bank extends the [architecture syllabus](Architecture-System-Design-Notes-Plan.md) and [resume-skills syllabus](Resume-Skills-Notes-Plan.md).

Questions are written as a study synthesis, not copied interview transcripts. System families recur in the checked preparation catalogs; failure drills and resume questions are tailored exercises. There is no universal frequency ranking here.

**Status:** prompts and answer checkpoints are compiled. Full worked explanations, diagrams and implementations will be authored in the mapped chapters.

## How to practice

- Conceptual answer: 30-90 seconds, with one example and a trade-off.
- Full design: clarify -> invariants -> API/data -> baseline -> trace -> failure -> scale.
- Cover the checkpoints before answering. They are a review aid, not a script.
- A0-A4 and S0-S13 refer to the architecture plan. Resume M IDs refer to the skills plan.
- Score each answer: 0 = cannot explain; 1 = vocabulary only; 2 = coherent mechanism; 3 = mechanism plus trade-off, failure case and evidence.
- Revisit every answer scored below 2; record the missing assumption or invariant.

## Architecture concepts and decisions

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

## System-building prompts

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

## Failure and concurrency follow-ups

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

## Resume-specific architecture questions

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

## Research and interpretation

Recurring system families were cross-checked against [Hello Interview's catalog](https://www.hellointerview.com/learn/system-design/in-a-hurry/problem-breakdowns), the [System Design Primer](https://github.com/donnemartin/system-design-primer) and [IGotAnOffer's reported-question collection](https://igotanoffer.com/blogs/tech/system-design-interviews). These support practice selection, not a claim that every listed prompt is asked equally often.

[Amazon's SDE II guidance](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep) supplies employer context about design quality. Its role level is above campus-entry expectations; the notes will begin with small buildable systems.

Mechanism verification starts from [AWS retry guidance](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/), [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), [PostgreSQL locking](https://www.postgresql.org/docs/17/explicit-locking.html), [Redis rate-limiter examples](https://redis.io/docs/latest/commands/incr/), [Microsoft cache-aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside), [transactional outbox](https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos) and [saga guidance](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga).

The checkpoints are answer targets for future chapters. A satisfactory solution still needs assumptions, execution guarantees, diagrams and tested examples appropriate to the question.

## First practice set

Begin with **Q01, Q02, Q06, Q10, Q14, Q19, Q25 and Q39**. Together they take a small URL service from requirements to data model, caching, duplicate handling and collision recovery.

Then add **Q26/Q40**, **Q27/Q41**, **Q28/Q42** and **Q29/Q43** as rate limiting, notifications, file processing and reservations are taught.
