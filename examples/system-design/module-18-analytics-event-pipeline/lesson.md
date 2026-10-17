# Architecture and System Design Placement Handbook — Part 20
# S13: Analytics Event Pipeline and Dashboard

**Estimated time: 4–6 hours | Architecture numeric module: 18 | Requires: A0–A4, S2 and S7; Resume M15/M19/M28 refreshers**

---

## Why this module exists

A producer retries after losing its acknowledgement. A consumer changes an aggregate but loses its checkpoint. An activation arrives before its signup, or after the dashboard called a window final. A chart looks plausible while counting different populations in its numerator and denominator.

**Organizing principle: preserve event identity and time semantics, commit projection effects with progress, and publish the metric definition with its freshness.**

This local SQLite pipeline implements durable bounded event batches, scoped replay, five-minute event-time windows, an explicit lateness policy, distinct-subject cohorts, atomic projection/checkpoint recovery, generation rebuild and subject removal. Actual HTTP serves intake and a JSON dashboard read model.

No Kafka/Beam cluster, browser chart, automatic watermark estimator, external spreadsheet connector or throughput test runs. Fixed lesson credentials represent trusted local publishers/readers, not production user/producer authentication. The 30 Q&As are curated practice, not measured interview frequency. This chapter develops Q38/Q52 and connects to the ingestion concerns in Q56.

---

## 1. Prompt and clarification questions

**Prompt:** collect page views, signups and activations for tenant dashboards. Duplicate and out-of-order events must not corrupt metrics, dashboard lag must be visible, and late data and deletion must follow a stated policy.

| Clarification | Architectural consequence |
| --- | --- |
| Operational monitoring or product behavior? | Different actors, retention, dimensions and correctness needs |
| Who is allowed to publish each event? | Authentication, event provenance and spoofing risk |
| What uniquely identifies an occurrence? | Producer-scoped deduplication and replay horizon |
| Event time or receipt time? | Window membership, timezone and clock-skew handling |
| How late may data arrive? | Mutable windows, exclusion, correction or backfill |
| What does activation rate mean? | Cohort identity, ordering, denominator and attribution |
| What freshness is promised? | Queue/projection lag and dashboard status |
| Which dimensions and cardinalities? | Aggregate growth and privacy risk |
| What can be deleted/replayed? | Source retention, erasure markers and rebuild policy |

The baseline has three event kinds and three allowlisted channels. Every event includes an explicit-offset ISO timestamp with whole seconds. It measures same-window, same-channel signup/activation, not seven-day retention, ordered funnel completion, attribution, revenue or causal product impact.

---

## 2. Contract and invariants

| Area | Executed policy |
| --- | --- |
| Event identity | Tenant/credential producer/client event ID, immutable normalized fingerprint |
| Batch | 1–16 events; validation/conflict failure rolls back the whole batch |
| Durability | 202 only after SQLite source commit |
| Source order | Increasing database sequence; event time remains independent |
| Window | Floor UTC event timestamp to 300-second start |
| Lateness | Window becomes final under policy when end + 120 seconds ≤ watermark |
| Watermark | Trusted explicit control; monotonic, not beyond now, only after local backlog drains |
| Projection | Effect receipt, counters, cohort participants, event decision and frontier atomic |
| Metric | Distinct activated signup subjects divided by distinct signup subjects in the same cell |
| Rebuild | New local generation preserves original included/late decisions |
| Privacy | Trusted removal recomputes active aggregates and retains a replay-blocking subject marker |

Equivalent timestamp offsets produce the same event fingerprint. A new ID for the same behavior is a new event, so event deduplication and distinct-user metric semantics remain separate. A real source must define stable occurrence IDs rather than generating a new one on every retry.

The late-data decision is explicit. Too-late events are durably retained as `late_excluded` and do not silently change finalized counts. This preserves an audit/reconciliation input, not automatic correction. Changing that policy requires a separately versioned recomputation decision.

---

## 3. Volume, storage and recovery estimates

{{ESTIMATES_OUTPUT}}

8.64 million events/day average 100/second; an assumed fivefold peak gives 500/second. At 400 assumed bytes/event, raw logical input is 3.456 decimal GB/day before indexes, retained decisions, replicas, backups and aggregate state.

A ten-minute outage at the average rate builds 60,000 events. Processing 150/second while 100/second keep arriving drains at fifty/second, requiring twenty minutes. Neither adding partitions nor changing the chart fixes insufficient net service capacity.

The fixture retains at most 512 source events and four generations. These are deterministic lesson limits, not production capacities. Distinct-subject sets can dominate memory for high-cardinality dimensions; estimate users × windows × dimensions and required retention rather than only counting event bytes.

---

## 4. Schema, authority and access patterns

| Table | Responsibility |
| --- | --- |
| `events` | Canonical accepted occurrence, event/receipt time, fingerprint and inclusion decision |
| `active` | Serving projection generation per tenant |
| `checkpoints` | Last source sequence, update time and watermark per generation |
| `effects` | Unique generation/event processing receipt, including exclusions |
| `counts` | Per-window/channel/kind event totals |
| `participants` | Exact distinct-subject sets for defined cohorts |
| `erased` | Tenant/subject marker blocking ingestion replay after removal |

The tenant/sequence index supports bounded catchup; aggregate keys match the read cells. Sequence gaps can result from other tenants or removed rows. They do not imply missing data when the consumer queries its scoped ordered source correctly.

The fixture uses exact sets rather than approximate distinct sketches. Approximate counts can save space but introduce estimation error and complicate cohort intersection, subtraction and erasure. Choose them only with an acceptable metric/error contract.

---

## 5. API and producer trust

| Actual endpoint | Contract |
| --- | --- |
| `POST /events` | Exact events envelope; credential determines tenant/producer; 202 receipts |
| `GET /dashboard?start=&buckets=` | Aligned UTC start, 1–12 five-minute windows, three fixed channels |

Dashboard responses include metric-definition version, active generation, source/projection positions, pending count, update time and watermark. Values are aggregate data; raw subject lists are not returned. Authenticated lesson readers can see their tenant aggregates under this explicit policy.

Processing, watermark advancement, rebuild and subject removal are trusted internal/admin methods without public routes. A deployed collector needs scoped producer credentials, limits, provenance validation and separate reader/admin roles. An authenticated producer report is not proof that a real customer action occurred; these analytics events do not authorize payments or permissions.

---

## 6. Smallest architecture and traces

```mermaid
flowchart LR
    Producer[Authenticated producer] --> Validate[Schema identity time and dimensions]
    Validate --> Source[(Durable scoped events)]
    Source --> Batch[Bounded ordered catchup]
    Policy[Trusted watermark and lateness] --> Batch
    Batch --> Atomic[Commit effects decisions aggregates and frontier]
    Atomic --> ReadModel[(Counts and cohort participants)]
    Reader[Tenant dashboard reader] --> Dashboard[Current generation and freshness]
    ReadModel --> Dashboard
    Source --> Rebuild[Bounded generation rebuild]
    Rebuild --> ReadModel
```

**Write:** validate the entire request → normalize event times → match scoped IDs/fingerprints → insert new source rows → commit → acknowledge. **Process:** read a bounded ordered slice after the tenant frontier → include or record exclusion → update receipts/counts/sets → move frontier in the same transaction.

**Read:** select active generation and return bounded cells plus freshness metadata in one transaction. **Recovery:** an injected projection failure leaves accepted source rows available and rolls back the whole projection batch. A later call retries from the original frontier.

This is a database-backed local pipeline. If source log and aggregate sink become separate services, their progress/effect boundary needs a cooperative protocol. Kafka transactions do not automatically make arbitrary external database writes atomic. [Kafka delivery semantics](https://kafka.apache.org/41/design/design/).

---

## 7. Shared executable runtime

{{RUNTIME_CODE}}

The helper is reused unchanged from S4–S6. It provides bounded JSON, no-store HTTP and fixed local credentials. The new proof records its actual verification date separately; historical chapter artifacts retain their original dates. No persistent server or Docker process is needed.

---

## 8. Executable event pipeline and dashboard read model

{{CORE_CODE}}

`BEGIN IMMEDIATE` serializes local writers, including dashboard snapshot transactions. This favors understandable transaction boundaries and can create contention; it is not a scalable warehouse query strategy. Exact local event effects and progress share SQLite authority.

Timestamp parsing requires an explicit offset and rejects fractional seconds/unsupported dates under this lesson contract. It normalizes to integer UTC seconds. It does not infer a timezone for ambiguous spreadsheet dates or implement a business calendar. [Python datetime](https://docs.python.org/3.12/library/datetime.html).

---

## 9. Metric definitions and late data

{{TIME_METRICS_OUTPUT}}

For one tenant/window/channel cell, the denominator is distinct subjects with a signup. The numerator is that set intersected with distinct activation subjects. Repeated signup/activation IDs or orphan activations cannot inflate the ratio beyond one. An empty denominator returns null, not a fabricated zero-percent conversion.

This is not an ordered funnel: an activation timestamp can precede its signup within the same cell and still be in the intersection. It also does not attribute a paid-channel activation to an organic-channel signup. A seven-day post-signup cohort needs an explicit signup anchor, time ordering, identity rules and maturation window.

Before the final boundary, late events can correct existing counts. At the exact end-plus-lateness boundary, future arrivals for that window are excluded under policy. A watermark expresses a progress/completeness assumption, not proof that no historical event will ever arrive. Beam provides window/watermark/trigger concepts, but its runtime is not executed here. [Beam guide](https://beam.apache.org/documentation/programming-guide/#watermarks-and-late-data).

---

## 10. Replay, partial batches and checkpoints

{{RECOVERY_OUTPUT}}

Duplicate intake reuses the original sequence. A changed payload under the same identity conflicts, and an earlier new record in that batch rolls back too. Two processing calls on separate connections drain each source row once under the local transaction boundary.

Moving the checkpoint before applying counts can lose data; applying counts and moving progress independently can double-count after retry. Here effects, canonical decisions, aggregates and frontier commit together. The local proof does not imply exactly-once business effects in unrelated services.

External file/spreadsheet ingestion adds source-specific cursor/row identity, schema and snapshot semantics. Reject unsupported nested records rather than silently dropping properties. Preserve and document timezone conversion; stable matching/upsert IDs and checkpointed batches must survive connector retries. This API rejects unknown nested fields and implements no spreadsheet parser or connector.

---

## 11. Rebuild, finality and subject removal

{{REBUILD_OUTPUT}}

Rebuild creates a new generation and switches the serving pointer atomically. It uses retained source inclusion decisions, so advancing today's watermark does not retrospectively discard events previously included. A failed pointer flip rolls back the new generation and leaves current dashboard values intact.

This is a bounded blocking local rebuild, not online stream catchup/warehouse migration. A large deployment needs a stable replay position, policy/schema version, catchup, comparison and serving switch. If intentionally correcting old exclusions, version the revised metric policy and label the restatement.

{{PRIVACY_OUTPUT}}

Subject removal deletes local source rows, clears all local projection/participant generations and reconstructs the current generation from remaining decided events. Old generation values become unavailable; they are not immutable historical snapshots. A retained subject marker rejects old/new replay for that subject in the tenant. Other tenants remain separate.

The marker itself is retained identity metadata. This is an executable local lifecycle policy, not a claim of legal compliance or secure disk/backup erasure. Raw archives, replicas, exports, caches and external analytics providers require their own deletion and retention treatment.

---

## 12. Actual HTTP evidence

{{HTTP_CONTRACT_OUTPUT}}

The owned loopback endpoint accepts durable events before materialization, then serves the updated aggregate after trusted processing. Tests exercise retries, anonymous access, tenant override, bounded query parameters and absent worker/privacy management routes.

The “dashboard” implemented here is its JSON read model and metric/freshness contract. No browser chart or hosted analytics console is executed. A frontend can render time/channel series from these bounded rows; it should display null denominators, provisional/final policy and pending updates accurately. All owned listeners/connections and temporary databases are closed/removed; port 3000 stays unused.

---

## 13. Architecture alternatives

| Option | Benefit | Cost or boundary |
| --- | --- | --- |
| Transactional database projection | Source/effect/frontier can share a transaction | Write contention and retention growth |
| Log plus consumers | Replay, independent consumers and partition progress | Sink coordination, skew and consumer ownership |
| Stream processor | Window/trigger/state abstractions | Watermark/state/checkpoint semantics and operations |
| Warehouse batch | Broad historical recomputation | Freshness delay and model/version management |
| Approximate distinct state | Smaller large-cardinality state | Error, intersection and deletion semantics |

Choose based on required freshness, query shape and replay/retention needs. Event ingestion and arbitrary analytical joins are different workloads. A single event stream does not guarantee correct business metric definitions or causal conclusions.

---

## 14. Growth and changed requirements

Partition by an ordering/key boundary that spreads actual traffic. Per-user ordering may suit behavioral sessions; tenant partitions can isolate work but one huge tenant can become hot. Merge partial aggregates only when the operation is valid: summing distinct-user counts from overlapping partitions overcounts.

Separate raw accepted data, validated canonical events and derived metric generations when requirements justify it. Schema evolution needs versioned producers/consumers and replay compatibility. Event corrections can use replacement/retraction identities with a defined accounting rule; this fixture instead rejects changed identity content.

Add bounded backlog admission, retries, poison-event quarantine and connector reconciliation. The global 512-row cap and four-generation cap stop this fixture; they do not implement archival or per-tenant resource fairness. Production retention must coordinate dedupe history, rebuild horizon and erasure.

---

## 15. Security, privacy and data quality

Derive tenant/producer scope from authenticated context and restrict who may publish trusted business events. Limit dimensions and payload size; avoid secrets, raw emails and arbitrary URLs in event properties. A browser event can be blocked, spoofed or repeated, so operational billing/inventory must use its own authority.

Aggregate views can still disclose small groups. Thresholds, access rules, query restrictions and export retention may be needed beyond hiding raw rows. Fixed credentials and same-tenant aggregate visibility are explicit lesson choices, not a deployed governance system.

Validate provenance and metric lineage as well as input syntax. A consistent timestamp with the wrong timezone assumption remains wrong. A clean count with the wrong cohort definition remains misleading. Keep business definitions reviewable and versioned.

---

## 16. Observability and incident questions

Track accepted/replayed/conflicted events, validation failures, pending age/count, projection checkpoint, included/late decisions, watermark lag and aggregate freshness. Monitor dimensions/cardinality, source-to-dashboard latency and rebuild/deletion backlog. Do not expose private subjects as metric labels.

When a graph changes, ask whether raw behavior changed, the source retried, the collector lost data, late data arrived, a metric definition changed, an identity join changed or deletion restated the cohort. Report numerator, denominator, time range and query/model version with the chart.

---

## 17. Run and evidence limits

From repository root:

```powershell
python examples/system-design/module-18-analytics-event-pipeline/verify.py
```

Verified {{DATE}} on Python {{PYTHON}}, SQLite {{SQLITE}}, {{OS}}. **{{TOTAL}} local checks passed**: {{COUNTS}}. Four synchronized calls cover paired intake and projection workers. Results are recorded beside the source, including rollback/reopen and actual HTTP cleanup.

No automatic watermark estimation, live broker/processor, external connector, chart renderer, process kill, secure erase or production throughput is tested. The worked system establishes local contracts and failure boundaries; the final consolidation maps those lessons across the full track.

---

## 18. Interview questions and answers

### Q1. What is an analytics event?

A record of an occurrence under a named schema, identity and time/provenance contract. It is distinct from a current-state row. Define who may report it and what it means before choosing a transport or drawing a chart.

### Q2. Why keep event time and receipt time?

Event time describes the reported occurrence; receipt time describes ingestion. They differ with offline clients, retries and clock skew. Event-time windows answer different questions from processing-time monitoring.

### Q3. What identifies a duplicate?

The same tenant/producer/event ID with equivalent canonical content. Reusing it with changed content conflicts. A new ID for the same behavior is a new event, so producers must preserve occurrence identity across retries.

### Q4. Is deduplication the same as counting distinct users?

No. Deduplication prevents repeating one occurrence; distinct-user metrics deliberately group many different occurrences by subject. Both contracts are needed to avoid either duplicate effects or misleading population counts.

### Q5. When should intake acknowledge success?

After its required durable acceptance boundary. Here 202 follows the source transaction commit. It does not mean the dashboard already includes the event, so freshness/projection state must remain visible.

### Q6. Why reject naïve timestamps?

Their UTC meaning is ambiguous without a timezone contract. The fixture requires an explicit offset and normalizes whole seconds. External spreadsheets may need a configured source timezone and explicit DST ambiguity policy rather than guessing.

### Q7. Why bound future timestamps?

A broken or malicious clock can misplace windows and distort progress estimates. The fixture rejects event time more than sixty seconds beyond supplied server time. It does not derive its watermark from the newest client event.

### Q8. What is a watermark?

A progress assumption used to reason about event-time completeness. It is not proof that no older event can arrive. This fixture advances it explicitly after backlog drains; a real processor needs partition, idle-source and estimator policies.

### Q9. What happens to allowed late events?

Before the chosen final boundary they can update an already materialized window. The example adds a delayed activation to the same signup cohort. Out-of-order arrival does not require arrival-order funnel semantics.

### Q10. What happens after finality?

Under this policy the event is retained as late_excluded without silently changing the dashboard. Another system may reopen/restatements/backfill instead. State which policy applies and how consumers learn about corrections.

### Q11. Why drain before watermark advancement?

Accepted local backlog could otherwise be classified too late merely because its worker was delayed. This guard protects the local model. It is not a substitute for distributed source watermark/partition coordination.

### Q12. What commits with the checkpoint?

The processing receipt, canonical inclusion decision, counter/set effects and new frontier. If any fail, all roll back. Independent progress and sink commits create loss or duplicate windows after a crash.

### Q13. Does Kafka make any sink exactly once?

No. Its documented transactions cover defined cooperative boundaries. An external aggregate database must coordinate effect identity and progress or implement a compatible sink protocol. This local example uses one SQLite transaction and no Kafka cluster.

### Q14. Why use effect receipts as well as a frontier?

They identify per-generation event application and make replay/rebuild decisions explicit. A unique receipt prevents repeating its local aggregate effect. It does not protect an unrelated external side effect.

### Q15. How is activation rate defined here?

Distinct subjects with both signup and activation in the same tenant/window/channel divided by distinct signup subjects in that cell. Orphan activations are excluded. The definition does not require event-time ordering or multi-day attribution.

### Q16. Why return null for an empty cohort?

Zero divided by zero is undefined; presenting zero percent invents a result. A dashboard should show no eligible denominator and retain context, rather than making empty data look like observed nonconversion.

### Q17. Can distinct counts be summed across partitions?

Only when their subject sets are disjoint under the metric definition. Overlap causes overcount. Merge sets/sketches using their documented algebra or deduplicate at an appropriate authority.

### Q18. How does rebuild avoid changing history accidentally?

It reuses retained inclusion/exclusion decisions and the metric policy. Applying today's watermark to every historical event would incorrectly exclude previously valid data. An intentional restatement needs a versioned policy and labeled output.

### Q19. Is this an online reindex/rebuild?

No. It performs a bounded local transaction and atomically changes the serving generation. Large deployments need snapshot/replay positions, catchup, comparison, switch and rollback procedures across services.

### Q20. What should a dashboard report besides values?

Metric definition/version, time range/timezone, numerator/denominator, source/projection freshness and provisional/final policy. A successful response with stale or differently defined data can still mislead users.

### Q21. How do you handle schema evolution?

Version producers and consumers, define compatibility/defaults and replay behavior, and avoid silently dropping unfamiliar properties. The fixture accepts only version one with exact fields and rejects unsupported nested input.

### Q22. How would a spreadsheet connector recover?

Preserve stable source record identity, explicit timestamps/timezone and the complete supported nested structure. Validate batches, checkpoint durable progress and reconcile source changes. This event API demonstrates those principles but implements no spreadsheet connector.

### Q23. How should privacy deletion affect aggregates?

Define whether identifiable state and derived cohorts are recomputed, anonymized or retained under an explicit policy. The local fixture removes source/participant data and rebuilds current aggregates, retaining a replay-blocking marker.

### Q24. Why keep an erasure marker?

Otherwise a delayed original event can recreate removed subject state. The marker is itself retained metadata with its own policy. It does not prove secure disk erase or compliance across backups and external providers.

### Q25. How do you choose a partition key?

From required ordering, workload skew and mergeable state. Tenant-only partitioning may isolate small customers while making one large tenant hot. More partitions do not automatically split one subject's ordering requirement or sink bottleneck.

### Q26. How do you recover an outage backlog?

Ensure service capacity exceeds continuing arrivals, then estimate backlog divided by net drainage. Respect sink limits and query load. Age and source-to-dashboard freshness reveal more than worker count alone.

### Q27. Can product events authorize revenue reports?

Only under a defined trusted provenance/reconciliation model. Browser-reported actions may be spoofed or missing. Authoritative payment/accounting state remains separate; this fixture models behavior counts, not a financial ledger.

### Q28. What is the difference between a metric and causality?

A metric summarizes observed data under a definition. A change in that metric does not establish that a product change caused it. Experiments, confounding, population selection and attribution need separate analysis.

### Q29. What did the tests establish?

Selected local intake, time, replay, transaction, cohort, late-policy, rebuild, removal and HTTP behavior. They do not establish broker failover, automatic watermark correctness, dashboard rendering or production capacity.

### Q30. Give a compact design answer.

Persist versioned scoped event identities and explicit event/receipt times, process bounded batches with effects and checkpoints atomically, and define cohort/window/late policies. Serve a versioned fresh read model, rebuild from retained canonical decisions and handle subject removal/replay deliberately.

---

## 19. A 45-minute mock and answer skeleton

**Mock prompt:** “Design a tenant analytics dashboard. Events duplicate, activations arrive late, a worker loses progress and a subject requests removal.”

| Segment | Minutes |
| --- | --- |
| Clarify provenance, metric and event-time policy | 5 |
| Estimate volume, state and backlog drainage | 7 |
| Define event, checkpoint and aggregate keys | 8 |
| Trace durable intake and atomic projection | 10 |
| Inject duplicate, late, rebuild and removal cases | 10 |
| Defend freshness, growth and evidence limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I would persist scoped immutable occurrence IDs with explicit event and receipt times. A bounded worker commits inclusion decisions, effect receipts, aggregate changes and source progress together. The dashboard exposes its cohort definition and freshness. Watermarks and lateness govern whether late data updates a window or becomes an explicit exclusion/restatement input. Rebuild preserves the selected policy instead of applying today's cutoff retroactively. Privacy removal covers retained source/participant/projection data and prevents old replay. Broker, connector and large-scale migration guarantees need their own evidence.

---

## 20. Practice tasks

1. Define the producer, occurrence identity, supported schema and provenance for views, signups and trusted business events.
2. Recompute event storage, peak rate, distinct-state size and outage drainage with explicit units and continuing arrivals.
3. Replay equivalent timestamps in different offsets, change an event under the same ID and inject a mid-batch conflict.
4. Stop after a partial projection batch and inspect pending/freshness metadata. Inject a checkpoint failure and retry accepted source.
5. Race intake and processing calls. Explain source identity, distinct-user state and per-generation effect deduplication separately.
6. Send out-of-order activations, orphan activations and repeated signups; state what the resulting ratio does and does not measure.
7. Advance to one second before and exactly at finality, then send late records. Compare exclusion, reopening and versioned restatement policies.
8. Rebuild after watermark advancement and fail the generation flip. Design the separate online distributed migration.
9. Remove a subject, inspect old/current projection state and retry the original event. Enumerate archive/export/provider retention obligations.
10. Complete the mock and Q38/Q52/Q56, including connector cursor/timezone/nested-data contracts and honest metric/evidence claims.

---

## 21. Completion checklist

- [ ] I can define scoped occurrence identity and immutable schema.
- [ ] I can distinguish event, receipt and processing time.
- [ ] I can normalize explicit timezones without guessing ambiguous dates.
- [ ] I can commit source before acknowledging acceptance.
- [ ] I can keep processing effects and progress atomic.
- [ ] I can explain exact cohort numerators and denominators.
- [ ] I can define watermark, lateness and finality policy.
- [ ] I can retain/explain too-late data and restatements.
- [ ] I can rebuild without accidental policy drift.
- [ ] I can scope dashboard access and expose freshness.
- [ ] I can handle subject removal and replay protection.
- [ ] I can finish the mock and state broker/connector/scale limits.

---

## 22. Research references and continuation

Reviewed {{DATE}}. Primary references: [Beam event-time/window concepts](https://beam.apache.org/documentation/programming-guide/#watermarks-and-late-data), [Kafka delivery/transaction boundaries](https://kafka.apache.org/41/design/design/), [PostgreSQL conflict handling](https://www.postgresql.org/docs/18/sql-insert.html), and [Python datetime](https://docs.python.org/3.12/library/datetime.html). The executed engine is SQLite; these references do not imply that their runtimes or complete guarantees were exercised. The metric, late policy and examples are authored teaching choices.

Return to the [architecture roadmap](/docs/system-design), [A3 reliable workflows](/docs/system-design/reliable-workflows-concurrency), [S7 workers](/docs/system-design/job-scheduler-workers), [Resume M15 ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion) or [M28 project explanations](/docs/resume-skills/resume-project-experience-deep-dives).

**Finish with [Consolidation and design mocks](/docs/system-design/consolidation)**, Part 21. All foundations A0–A4 and worked systems S0–S13 are authored. Revision and learner self-assessment continue separately from authoring completion.
