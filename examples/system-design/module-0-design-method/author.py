"""Assemble A0 with exact source and recorded planning/repository evidence."""
from pathlib import Path
import json
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
def code(name):
    return '```python\n'+(BASE/name).read_text(encoding='utf-8')+'```'
def output(name):
    return '```json\n'+json.dumps(proof['observations'][name],ensure_ascii=False,indent=2)+'\n```'
mock=[('Clarify actors and operations',5),('Scope and invariants',5),('Workload and estimates',5),('API and data contract',8),('Baseline and request traces',8),('Failure/concurrency deep dive',9),('Trade-offs and recap',5)]
assert sum(minutes for _,minutes in mock)==45
mock_table='| Segment | Minutes |\n| --- | --- |\n'+'\n'.join(f'| {name} | {minutes} |' for name,minutes in mock)+'\n| **Total** | **45** |'
chapter=r'''# Architecture and System Design Placement Handbook — Part 2
# A0: How to Approach a Design Question

**Estimated time: 3–4 hours | Architecture numeric module: 0 | Requires: Resume M0/M6 and basic DBMS/CN**

---

## Why this module exists

A design question usually starts with too little information: “Design a notes app,” “Build a notification service” or “How would you scale this?” The first task is to discover which operations, correctness rules and workloads matter. A diagram chosen before those decisions can look impressive while failing the actual problem.

This chapter teaches a repeatable method using a private study-note service. It includes calculated workload estimates, an offline SLI exercise and a small persistent SQLite repository probe. The service's HTTP contract and deployment diagram are design artifacts; this chapter does not implement an authenticated HTTP server. [A1](/docs/system-design/application-architecture-service-boundaries) develops application responsibilities and a framework baseline.

**Organizing principle: clarify the operation, name the invariant, and trace the state change before adding scale.**

The questions and mock timing are editorial practice material, not a measured employer-frequency ranking or a prescribed interview format. A0 addresses the root bank's Q01–Q03 and contributes estimation/evidence reasoning to Q24/Q60; it does not complete the other foundations or worked designs.

---

## 1. What a design answer must establish

A useful answer makes these relationships visible:

```text
User need -> operation and contract -> invariant and state owner
          -> workload/limits -> small architecture -> request/failure trace
          -> evidence and justified growth
```

Requirements constrain the design; estimates help identify likely pressure; a concrete API/data model turns a box into something buildable. Then a failure timeline exposes whether the chosen boundary actually protects the invariant.

An architecture is more than a deployment drawing. Two services can share an unsafe read-modify-write sequence. One process with a database constraint can enforce the same scarce-resource rule correctly. Start by explaining authority, execution and recovery rather than counting components.

At the end, the interviewer should understand what the system does, which assumptions were made, why the baseline is enough to begin, what can go wrong and which requirement would justify the next change. Be explicit about implementation evidence versus a proposal.

---

## 2. Clarification: ask questions that change the design

Begin with actors and core actions, then explore the consequences of failure or scale. Do not spend every minute collecting trivia or ask for a database brand before understanding the query.

| Question | Why the answer matters |
| --- | --- |
| Who creates, reads and edits a note? | Identity, permission and ownership boundaries |
| Is a note private, shared or public? | Query/cache scope and revocation behavior |
| Is content a small text value or a large file? | Payload, storage and processing boundaries |
| Can two devices edit simultaneously? | Conflict policy, expected revisions or merge semantics |
| What happens when the client retries a create? | Business operation identity and stored outcome |
| Is full-text search, collaboration or offline editing required? | Indexing, consistency and synchronization scope |
| What does “fast” mean for which user/operation? | Measurement boundary, latency distribution and objective |
| What workload and growth should the baseline handle? | Units, peaks, storage and dependency capacity |

If an answer is unavailable, make a reasonable explicit assumption and continue: “I will start with private text notes, one owner, create/read/replace operations and no collaboration. If sharing is required, I will add grant/revocation behavior and revisit all derived data paths.” That is a proposal awaiting clarification, not an observed fact.

In an interview, keep an assumption ledger. Separate confirmed requirements from your choices. A later change then has a visible impact instead of forcing you to defend an accidental assumption.

---

## 3. Scope the running example

**Prompt:** design a service for learners to store and edit short private study notes.

| Area | Chosen teaching scope |
| --- | --- |
| Actor | An authenticated learner within a tenant |
| Create | Title and small UTF-8 content; stable create operation identity |
| Read | Fetch an identified note only for its current owner/tenant |
| Edit | Replace title/content only when the expected revision is current |
| Exclusions | Sharing, public notes, attachments, listing/search, collaborative/offline merge and a delete API |
| Persistence | Canonical note and create-operation outcome stored transactionally |
| Growth inputs | Explicit hypothetical traffic, payload, retention and copy assumptions |

The probe accepts already supplied tenant/owner values; it does not authenticate them. In the proposed application, an authentication boundary must derive those values from a verified credential rather than trusting a request body. Resource checks remain necessary after authentication.

The one-year storage horizon is a planning assumption, not an implemented deletion/archive job. The operation-record table also needs an explicit retention policy in a deployed design. Do not confuse an estimate with a shipped lifecycle feature.

Keep three core flows for the first answer. If the prompt requires another operation, state it and revise the data/API/failure analysis. Leaving out a confirmed requirement is different from making an explicit initial non-goal.

---

## 4. Functional requirements, invariants and objectives

| Kind | Example | How to assess it |
| --- | --- | --- |
| Functional requirement | An owner can create/read/edit a note | Contract and authorized positive-path checks |
| Correctness invariant | Another tenant/owner must not obtain it | Scoped queries and negative tests |
| Concurrency invariant | A stale edit must not overwrite a newer revision | Conditional write and two-caller scenario |
| Replay invariant | The same scoped create identity/input must not create another note | Durable result plus duplicate/concurrent checks |
| Atomicity invariant | A note and its create outcome agree after failure | Crash-point/rollback test |
| Operational objective | A declared fraction of eligible requests gets a correct result within a limit | Defined good-event measurement over a window |

A correctness invariant is not an allowed error-budget percentage. “Only one percent of requests leaked another tenant's note” is still a broken permission design. Availability/latency objectives describe tolerated operational failure under an agreed policy; they do not authorize forbidden business effects.

Some requirements are absolute within a specified scope, while implementation claims still need evidence. Saying “never overwrite” identifies the desired rule. Showing a constraint or conditional write and its race test explains how the baseline protects it; that still does not establish every possible deployment behavior.

Use measurable language. Replace “highly scalable” with an assumed peak, response-size distribution, latency/error objective and resource context. Replace “strong consistency everywhere” with the particular read/write guarantee and the operation that needs it.

---

## 5. SLI, SLO and the measurement boundary

An SLI is a defined indicator; an SLO is its target. An SLA adds an agreement and consequences rather than being just another label for a latency number. Choose indicators that describe the user-relevant operation and specify the measurement window and population. [Google SRE service-level objectives](https://sre.google/sre-book/service-level-objectives/).

For this teaching exercise, a good eligible event is a correct, nonviolating result completed within 200 ms. The illustrative target is at least 99% good events in a chosen window. These values are assumptions, not measured service results. A real monitor must define and collect the relevant events; the function below receives a hand-authored list already selected for a window.

{{OBJECTIVES_SOURCE}}

{{OBJECTIVES_OUTPUT}}

The first sample has 99 good events and one slow event. The second has 99 good events and one deliberately labeled invariant violation. Both reach the illustrative aggregate target, but only the first passes the separate design gate. Even an event outside the eligible latency population can trigger the invariant check.

The classifier relies on its input labels. It cannot discover a leaked note or validate a response by itself. In practice, specify what makes a result correct, how server failures/timeouts count, which client requests are in scope and how exclusions are audited. Excluding overload or timeouts merely to improve the number can defeat the objective's purpose. [Google SRE SLO implementation](https://sre.google/workbook/implementing-slos/).

Do not turn this 100-event fixture into a claim about production uptime or p95. It verifies denominator/boundary/gate mechanics over synthetic samples; it does not collect traffic, implement rolling windows or estimate long-term reliability.

---

## 6. Estimate workload with units and a stated purpose

Ask which estimate can change a decision. Request rate can motivate admission or replication of stateless work. Record growth can reveal an unrealistic retention assumption. Large payload bandwidth can motivate object/CDN boundaries. Estimates are tools for prioritization, not decorations.

```text
reads/day       = active users × reads/user/day
writes/day      = active users × writes/user/day
average QPS     = total requests/day ÷ seconds/day
assumed peak    = average QPS × peak factor
new records/day = writes/day × creation fraction
retained bytes  = new records/day × retained days × bytes/record
planned copies  = logical bytes × physical copies × overhead factor
```

For this case, assume 100,000 active users, 30 reads and three writes per user per day, an eightfold peak, 150 ms mean request time and a 40% creation share among writes. Updates are not all new records. The assumed mean record is 2 KiB; read/write response sizes are separate inputs.

The copy/overhead factors are planning inputs, not an implemented replicated database. The assumed per-instance capacity is 100 requests/s with a 65% operating target. No benchmark establishes that capacity. The numerical fixture validates explicit positive/zero/count bounds and allows a read-only workload.

{{ESTIMATES_SOURCE}}

{{ESTIMATES_OUTPUT}}

The scenario gives about 38.19 average and 305.56 assumed peak requests/s. It predicts 43.8 million retained created records under the stated annual horizon. The planned physical storage is 403.6608 decimal GB, or about 375.94 GiB. Those values are computed from assumptions; they do not describe the tiny probe's actual dataset or storage footprint.

Bandwidth is response payload only: 1,152,000 bytes/s at the assumed peak. Upload bodies, headers, TLS, replication, backups and retries are excluded. Make exclusions visible so another person can revise the estimate.

---

## 7. Latency, throughput and average in-flight work

Little's law relates average number in a stable system to average flow rate and average time in that same system. Keep the boundary and averaging population consistent. It does not say peak traffic multiplied by p99 predicts a p99 queue length. [Little's original queuing formula paper](https://pubsonline.informs.org/doi/10.1287/opre.9.3.383).

Here the arithmetic asks: if the assumed peak becomes a sustained stable flow and mean time in the chosen system remains 150 ms, what average in-flight work would that imply? The answer is about 45.83 requests. This is a conditional planning calculation, not an observed instantaneous concurrency or latency guarantee.

If queueing is included in time, it is included in the corresponding system population. If admission drops work, distinguish offered traffic from admitted/completed traffic. Requests per second, open connections, browser users and in-flight requests are different quantities.

The server-count arithmetic rounds the assumed peak divided by 65 target requests/s up to five healthy instances, then adds one reserve instance. That only works if surviving resources, workload distribution, dependency capacity and the per-instance assumption hold. Five API instances sharing an exhausted database do not create five independent database capacities.

The 65% target is an exercise assumption, not a universal best utilization. Tail latency, burstiness, hot keys, uneven request cost and resource ceilings can change the operating point. Measure a representative workload before turning this estimate into a capacity claim.

---

## 8. Sensitivity: change one assumption at a time

{{SENSITIVITY_OUTPUT}}

Doubling users doubles requests, the implied average in-flight population and planned storage. Doubling mean time doubles implied in-flight work while the assumed arrival rate stays the same. Doubling record size changes planned storage without changing request count.

The instance count in the double-time row stays unchanged because this simple calculator holds the assumed per-instance QPS input fixed. That is not proof that a slower implementation needs no more instances. If extra service time reduces actual capacity, the capacity input must change or be measured again. The model exposes what it calculates and what it does not model.

Use a range for uncertain peak/size assumptions and show which one dominates the decision. A single precise-looking answer can hide a weak premise. Do not spend the entire interview doing arithmetic that would not change the baseline or the next investigation.

---

## 9. Turn operations into an API contract

The following is a **proposed HTTP contract**, not executed HTTP evidence. The repository below verifies selected state behavior directly. An adapter still needs parsing, verified identity, limits, exception/status mapping and response headers.

| Operation | Proposed contract | Important rule |
| --- | --- | --- |
| Create | `POST /notes`, title/content and an application-defined Idempotency-Key; 201 result | Scope operation identity by tenant/owner and bind it to validated input |
| Read | `GET /notes/{id}`; 200 current representation | Return a uniform invisible/absent outcome under the chosen permission policy |
| Replace | `PUT /notes/{id}` with expected revision carried by an If-Match validator | Only replace the version the caller actually read |
| Malformed input | 400-class validation response | Bound types, size and representation before persistence |
| Same create key/different input | 409 under this application contract | Do not silently replay a different command |
| Failed edit precondition | 412 under the proposed If-Match contract | Do not overwrite a newer revision |

HTTP defines conditional-request and method semantics; the application must choose a concrete validator format and business contract. A proposed adapter could expose a strong ETag such as a revision-derived value for the representation, then check If-Match. The current probe accepts an integer revision directly and does not parse HTTP headers or implement ETag behavior. [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html).

The stored create outcome is replayed, including its original revision; a later GET retrieves current state. A deployed adapter should specify whether a replay returns the original status/representation and any replay indicator. The probe's `replayed` field is verification metadata, not an already published API standard.

An update's expected revision prevents stale overwrites but does not provide full replayed-result semantics after a lost acknowledgement. A repeated conditional PUT may return 412 after the first successful write without applying another update. HTTP idempotent-effect semantics do not require identical responses; returning a stored operation outcome is a separate contract. A client may need to read/reconcile current state or use an additional operation protocol.

---

## 10. Data model: identity, constraints and access patterns

| Record | Key and fields | Authority |
| --- | --- | --- |
| Note | `(tenant, id)`, owner, title, content, positive revision | Canonical note state |
| Create operation | `(tenant, owner, operation_id)`, input fingerprint, note ID, stored result | Replay identity and original create outcome |

The read path looks up one tenant/note and checks owner. The edit path adds the expected revision. The primary key supports this baseline access pattern; no listing index is added because listing is outside scope. A later owner-list API would need its ordering/pagination/query/index analysis.

Keep stable identity separate from mutable title/content. Validate untrusted values at the boundary and enforce relevant rules in storage. In the probe, title/content limits, positive revisions, unique keys and the operation-to-note relation are database constraints as well as application checks where appropriate.

The operation fingerprint compares the exact validated title/content values under a canonical serialization. It does not perform Unicode normalization or infer that two semantically similar texts are the same command. Request-equivalence and dedupe-retention policies are application decisions. A stable client operation identity supports safe replay; a new identity on each retry defeats that purpose. [AWS idempotent API design](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

SQLite is used for a small reproducible invariant probe. Its writer/concurrency behavior is not a substitute for testing the chosen deployment database. Future foundation/worked chapters can use the default Node/Express and appropriate engine stack without changing this chapter's method.

---

## 11. Smallest useful architecture and responsibilities

```text
Client
  -> HTTP/TLS adapter: parse, verify identity, validate and map contract
  -> note application operation: scope command and preserve invariant
  -> canonical repository/database: conditional writes + durable outcome
  -> adapter serializes permitted representation
```

This can begin as modules in one application with one appropriate canonical database. The boxes show responsibilities, not four independently deployed services. The database transaction boundary matters more than the number of arrows.

For the running case, no cache, queue, object store, search engine or agent is required to demonstrate create/read/edit correctness. Add one only for an identified need. For example, attachments would create a bytes/metadata lifecycle; asynchronous indexing would create job/generation state; shared notes would create grant/revocation behavior.

The repository probe supplies the lowest state boundary. Authentication and HTTP remain proposed responsibilities above it. It must not be presented as a secure deployed service merely because cross-owner database queries reject the supplied identities.

---

## 12. Exact runnable repository probe

{{BASELINE_SOURCE}}

The create transaction starts with `BEGIN IMMEDIATE` to serialize the read-dedupe/create sequence in this SQLite exercise. The note and stored outcome commit together. A deliberately injected exception after the note insert rolls back the transaction. The fault switch is an internal test hook, not an exposed application parameter.

The update's condition includes tenant, owner, note ID and expected revision. If the condition does not match, a scoped read distinguishes an invisible/absent resource from a visible stale version without revealing another owner's record. The read and version logic depend on trusted caller context supplied above this boundary.

The default ID factory uses UUIDs; fixture IDs are injected for readable deterministic observations. A database identity collision still needs an application policy in a full service; the probe does not claim a universal collision-retry protocol.

Python's connection context manages transaction commit/rollback; it is not itself a connection-close guarantee. The verifier owns and explicitly closes connections before removing the temporary database directory. [Python SQLite transaction and lifecycle API](https://docs.python.org/3.12/library/sqlite3.html).

---

## 13. Trace success, replay, conflict and rollback

{{BASELINE_OUTPUT}}

**Create:** validate caller-supplied identity/input → open transaction → look for the scoped operation → insert note revision 1 → persist outcome → commit. An identical retry returns the stored result and creates no second row.

**Read:** use trusted tenant/owner plus note ID → scoped database query → permitted representation or the uniform invisible/absent exception. Another owner and another tenant are both rejected by the probe.

**Edit:** use the revision the caller read → conditional UPDATE → increment revision once → return the updated representation. A stale edit is rejected and current content survives.

**Rollback:** inject failure after the note insert but before the operation record → transaction rollback removes both effects → the same operation can later succeed. The retry may receive a different generated ID because an allocated-but-rolled-back ID is not a committed business result.

**Replay after a later edit:** the create operation returns its original revision-1 outcome while a current read returns revision 2. Those are different contracts; returning an old create outcome does not mean a current read became stale.

---

## 14. Two callers: make concurrency concrete

The verifier opens two independent SQLite connections behind a barrier for each concurrent pair. For duplicate creates, one receives a new result and the other a replay; only one note and operation are stored. For two edits of revision 1, one is accepted and one rejects stale state; the final revision is 2.

The winning edit title is intentionally not asserted. Scheduling may choose either caller. The invariant is one accepted state transition, not a preferred thread winning. Four worker calls complete and close their connections.

This is real concurrent database execution in a tiny local fixture. It is not a load benchmark, distributed transaction, PostgreSQL isolation proof or evidence that an HTTP adapter maps errors correctly. Explain the exact tested boundary before extending the claim.

When analyzing another design, draw two callers on separate timelines. Locate the read, decision, commit, external effect and acknowledgement. Ask which rule survives both reading the same old state and what happens if either caller retries.

---

## 15. Select a deep dive and justify growth

Choose a deep dive from a requirement or failure: stale edits, duplicate creates, tenant visibility, overloaded database, large content or indexing lag. Make the current baseline and the proposed change easy to compare.

| Trigger | Investigation before adding a component | Possible justified change |
| --- | --- | --- |
| Slow reads | Query/pool/CPU trace, payload and access pattern | Better query/index or appropriately scoped caching |
| CPU-heavy processing | Measure synchronous work and queue/resource limits | Bounded worker/background work |
| Larger binary content | Size, upload recovery and authorization | Object storage plus durable metadata/lifecycle |
| One process saturated | Resource profile, dependency capacity and state placement | Stateless application replicas with bounded admission |
| Write contention | Invariant, conditional updates, lock waits and retry budget | Targeted transaction/schema/workflow change |
| Sharing/revocation | Permission source and every derived/cache path | Explicit grants and current acceptance/invalidation |

These are design alternatives, not implemented features of the probe. Adding a queue creates durable job/acknowledgement semantics to explain; adding a cache creates freshness and permission questions. Name the new failure boundary as well as the intended benefit.

Do not use the large annual storage calculation to assert that the prototype must immediately be sharded. Revisit retention, actual creation rate, payload distribution and engine measurements first. A good next step can be a better measurement rather than another service.

---

## 16. Communicate the answer and the trade-off

Use connected statements: “The note is private, so the query uses server-derived tenant/owner. Concurrent edits must not overwrite, so the write includes the expected revision. A create may be retried, so its operation identity and outcome commit with the note.” Each component follows a requirement.

| Choice | Alternative | What decides |
| --- | --- | --- |
| Reject stale replace | Automatic merge | Collaboration requirements, conflict semantics and complexity |
| Stored create result | Client reconcile by reading | Contract needs, retention and ambiguous-outcome handling |
| One modular application | Independent services | Team/deployment/fault boundary, not diagram size |
| Direct canonical read | Cache | Measured pressure plus allowed freshness/permission policy |
| Synchronous note write | Background acceptance | Whether the user needs the committed result immediately |

If challenged, state the assumption that would make you choose differently. “I chose this because the service is initially private small text with immediate create/read/edit results” is more useful than “this database is scalable.”

For your resume, connect method to available evidence: use M27's placement/workload distinctions and M28's metric/source worksheet. A calculated scenario or this new repository fixture cannot substantiate an original production benchmark.

---

## 17. A 45-minute practice outline and short explanations

{{MOCK_TABLE}}

This is a proposed practice allocation. Change it when an interviewer requests a particular deep dive; do not mechanically rush through estimates while leaving a critical invariant unexplained.

**Short explanation:** “I would first clarify private versus shared notes and the core operations. For a private create/read/edit baseline, I need trusted owner scope, a safe create retry identity and expected revisions for edits. I would estimate the workload, define the API/data contract, start with one application and canonical database, then test duplicate creates, concurrent edits and failures before adding scale.”

**Two-minute expansion:** identify the actor/non-goals, give the assumptions and one important estimate, draw the baseline, trace a create and edit, then explain the replay/transaction and permission boundary. End with the first bottleneck you would measure. This is an outline, not a word-count guarantee.

**Five-minute expansion:** add the data keys/constraints, one two-caller timeline, an ambiguous response, a viable alternative and the evidence that would settle it. Keep stated assumptions visible so a changed requirement has an explicit impact.

---

## 18. Verification scope and connection to later chapters

**62 local checks passed:** 23 estimate-arithmetic/input checks, 12 offline-objective checks, 23 repository checks and four concurrency-invariant checks. The runtime was **Python {{PYTHON}}**, SQLite **{{SQLITE}}**, on **{{OS}}**. Temporary databases and owned connections are cleaned; no persistent service listener is started by the examples.

```powershell
Set-Location examples/system-design/module-0-design-method
python verify.py
```

Three exact sources are embedded above. The numerical and SLI inputs are authored; the repository transactions, persistence, constraints and concurrent pairs are real local SQLite behavior. API/ETag/status/authentication/TLS/monitoring/deployment behavior remains proposed. [A1](/docs/system-design/application-architecture-service-boundaries) supplies application responsibilities and a framework baseline; A2–A4 and S0–S13 remain separate work.

Use the [architecture roadmap](/docs/system-design) and its question bank: Q01 for clarification/invariants, Q02/Q03 for estimates, Q24 for operational evidence and Q60 for defending resume metrics. Resume [M0](/docs/resume-skills/how-backend-works), [M6](/docs/resume-skills/rest-apis-http), [M13](/docs/resume-skills/postgresql-backend), [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance) and [M28](/docs/resume-skills/resume-project-experience-deep-dives) provide supporting mechanisms.

---

## 19. Interview questions and answers

{{QUESTIONS}}

---

## 20. Practice tasks

1. Clarify “design a notes app” with five questions that change the architecture. Record confirmed requirements and your assumptions separately.
2. Write three core flows, three non-goals, four invariants and a proposed good-event objective. Identify the state owner for each invariant.
3. Change users, daily actions and peak assumptions, then run the estimator. Explain which estimate changes a design decision and which capacity input still needs measurement.
4. Separate creation from updates and estimate retention, response bandwidth and physical storage. State missing costs such as backups, dedupe records and upload/replication traffic.
5. Compare average flow/time/in-flight work with p95/p99 latency. Give a changed queue/admission boundary and explain why the same numbers cannot be substituted blindly.
6. Add an HTTP adapter around the repository with owned demonstration authentication, parsing, body limits, expected-revision validators and explicit status mapping. Test the real contract before claiming HTTP behavior.
7. Change the concurrent edit test to many callers or a different real database. Preserve one-transition semantics and report the actual engine/isolation behavior, errors and cleanup.
8. Add a defined operation-retention and note deletion policy. Test replays after deletion/expiry, permission revocation and cleanup rather than simply removing rows.
9. Introduce sharing, attachments or search as a changed requirement. Update the API/data/permission/failure model and justify each new component before implementing it.
10. Record a 45-minute mock using the outline. Review one unsupported assumption, one missing failure boundary and one unmeasured metric, then retest with a changed requirement.

---

## 21. Revision checklist

- [ ] I can clarify actors, operations and non-goals without choosing infrastructure first.
- [ ] I can separate confirmed requirements from explicit assumptions.
- [ ] I can state an invariant and name its authoritative state/transaction boundary.
- [ ] I can distinguish functional behavior, correctness and operational objectives.
- [ ] I can define eligible/good events and a measurement window without hiding failures.
- [ ] I can estimate QPS, storage and bandwidth with units and stated exclusions.
- [ ] I can use average flow/time/in-flight reasoning without substituting percentiles.
- [ ] I can change an uncertain input and explain what the model does not capture.
- [ ] I can design API/data identity and expected-revision/replay contracts.
- [ ] I can trace a successful write, a retry, a stale caller and rollback.
- [ ] I can justify a deep dive or growth change from a requirement/bottleneck.
- [ ] I can communicate trade-offs and distinguish proposed behavior from execution evidence.

---

## 22. Primary references and verification artifacts

Sources were checked on **16 October 2026**. The primary references support the method's technical definitions; the examples and assumptions are independently authored teaching fixtures.

| Topic | Primary source |
| --- | --- |
| Service-level definitions | [Google SRE objectives](https://sre.google/sre-book/service-level-objectives/), [SLO implementation](https://sre.google/workbook/implementing-slos/) |
| Average queuing relation | [Little, 1961](https://pubsonline.informs.org/doi/10.1287/opre.9.3.383) |
| HTTP semantics/preconditions | [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) |
| Safe replay identity | [AWS idempotent API design](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) |
| Local transaction/lifecycle | [Python 3.12 SQLite](https://docs.python.org/3.12/library/sqlite3.html) |

Artifacts under `examples/system-design/module-0-design-method/` include the three exact sources, `verify.py`, named assertions/observations, cleanup evidence, content fidelity and site build/route/search reports. They establish arithmetic, offline classification and the local repository boundary, not a deployed service or production capacity.

**Next: [A1 — Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries).** Develop the controller/service/repository responsibilities, modular application baseline, synchronous/event boundaries and a concrete request trace.
'''
questions=[
('What is the first step in a design question?','Clarify the actors, core operations and requirements that change architecture. Record assumptions if answers are unavailable. Do not start by selecting a database or drawing a distributed deployment before understanding the invariant.'),
('Which clarification questions are useful?','Ask about permission, data size, concurrent changes, retries, workload, latency/availability needs and required features. A useful answer changes the API/data/failure model or the next measurement; a trivia question does not.'),
('What are non-goals?','Explicit exclusions from the current design scope, such as sharing or attachments in this baseline. They keep the first solution reviewable. They do not excuse omitting a confirmed requirement.'),
('Functional requirement versus invariant?','A functional requirement describes an operation; an invariant describes a rule that must survive allowed operations/failures. An owner editing a note is functionality; a stale edit never overwriting a newer revision is the associated correctness rule.'),
('How do invariants influence architecture?','They identify authoritative state and the necessary atomic/version/permission boundary. Start with that rule, then choose a mechanism that protects it. More services or replicas do not automatically strengthen the invariant.'),
('SLI, SLO and SLA?','An indicator measures a defined behavior; an objective sets its target; an agreement includes the relevant commitment/consequences. Define population, measurement boundary and window. The teaching classifier is not a production monitor.'),
('Can an error budget permit tenant leaks?','No. Operational targets do not authorize violating a business/security invariant. The synthetic sample meets the aggregate goal while failing the separate invariant gate; a fast leaked response is not a correct result.'),
('How do you estimate average and peak QPS?','Multiply users by actions per user per day, divide by the stated seconds/day, then apply a justified peak assumption. Separate read/write operations and label the multiplier. Average daily activity alone does not establish burst capacity.'),
('Why separate creations from updates?','Counting every write as a new retained record can greatly overestimate logical growth. Define the creation fraction, record size and retention. Updates, histories, dedupe records and logs may have their own storage costs.'),
('GB versus GiB?','Decimal GB uses powers of ten; GiB uses powers of two. State bytes and the unit convention, and distinguish logical records from physical copies, indexes/overhead, backups and lifecycle costs.'),
('What does response bandwidth omit here?','Request/upload bytes, protocol/TLS overhead, replication, backups and retries. This estimate uses declared read/write response sizes only. Record exclusions so they can be revised instead of presenting the value as total network demand.'),
('How should Little’s law be used?','Use averages over a consistent, suitably stable system boundary. The exercise asks what sustained assumed flow and mean time would imply. It does not predict a percentile queue length from peak QPS times p99 latency.'),
('Does average in-flight work equal concurrent users?','No. Browser users, connections, offered requests and requests currently inside the measured system differ. Define the arrival/completion/admission boundary and avoid silently substituting populations.'),
('Does the estimate prove six instances are enough?','No. That count uses an assumed per-instance capacity/utilization and one-failure reserve. Distribution, shared dependency limits, workload cost and actual latency/errors still need representative measurement.'),
('Why run sensitivity analysis?','It shows which uncertain input affects rate, storage, concurrency or an architectural choice. Change one assumption at a time and explain fixed inputs. The double-time example does not update capacity automatically.'),
('What belongs in the API contract?','Methods/resources, validated payloads, identity/permission, errors, representation/version, retry identity and pagination if needed. Define the exact client-visible behavior. The chapter’s HTTP table is proposed and has not been exercised over a network.'),
('What does an expected revision protect?','It makes an edit conditional on the state the caller read, preventing a stale overwrite under the tested boundary. It does not by itself return a prior successful edit result after an ambiguous acknowledgement.'),
('Why use a precondition failure for a stale edit?','Under the proposed If-Match contract, an unsatisfied conditional request maps to HTTP precondition semantics. The repository raises StaleVersion directly; an actual adapter must implement validator parsing and status behavior.'),
('How is a create retry made safe in the probe?','Tenant/owner/operation identity and exact input fingerprint select a stored outcome. The note and outcome commit together. Duplicate concurrent calls are serialized under the chosen SQLite transaction and create one note.'),
('What if the same operation key has different input?','The probe raises Conflict under its declared request-equivalence policy. A deployed API must document this behavior and key retention. Do not silently return an unrelated earlier result.'),
('Why can create replay return an old revision?','It returns the original operation outcome, not a current resource read. A later GET retrieves current state. Define that distinction so a client does not mistake a replay response for a freshness guarantee.'),
('Why keep the first architecture small?','It makes state ownership, traces and failure boundaries easier to assess and build. Complexity should follow a requirement or bottleneck. A modular application can enforce the baseline without premature queues, caches or independent services.'),
('What does the SQLite concurrency test prove?','Two independent connections yield one create plus one replay, and one accepted edit plus one stale edit in the controlled fixture. It does not prove production throughput, another engine’s isolation behavior or HTTP/auth correctness.'),
('How do you test a crash boundary?','Place a controlled interruption between meaningful effects and inspect persisted state/retry behavior. The create test fails after note insertion and verifies rollback of note/outcome together, then retries successfully.'),
('Is passing tenant/owner into a scoped query authentication?','No. Those values must come from a verified caller boundary. The repository checks resource scope using supplied identities; it does not verify credentials, sessions, TLS or service delegation.'),
('When should you add a cache or queue?','After naming the need and its evidence. A cache adds freshness/permission policy; a queue adds persisted work, replay, acknowledgement and backlog behavior. Explain the new failure boundary as well as the expected benefit.'),
('How do you choose a deep dive?','Select the highest-impact requirement or uncertainty: concurrency, replay, tenant scope, dependency saturation or large content. Trace one operation/failure in detail and compare a concrete alternative.'),
('How should you handle an unknown scale requirement?','State a reasonable range/assumption, calculate the consequences and identify what measurement would refine it. Do not invent production metrics or claim an assumed capacity was observed.'),
('How do you defend a technology choice?','Tie it to access patterns, invariants, execution/operational needs and team constraints. Name an alternative and the deciding requirement. A brand label or a large diagram is not the justification.'),
('What should the final recap contain?','Core scope/assumptions, invariant/state owner, API/data baseline, a success/failure trace, the important estimate and its evidence limit, then the justified next change. Keep proposed improvements separate from implemented or resume-reported behavior.'),
]
assert len(questions)==30
chapter=chapter.replace('{{QUESTIONS}}','\n\n'.join(f'### Q{i}. {q}\n\n{a}' for i,(q,a) in enumerate(questions,1)))
for tag,name in [('ESTIMATES','estimates.py'),('OBJECTIVES','objectives.py'),('BASELINE','baseline.py')]:
    chapter=chapter.replace('{{'+tag+'_SOURCE}}',code(name))
for tag,name in [('ESTIMATES','estimates'),('SENSITIVITY','sensitivity'),('OBJECTIVES','objectives'),('BASELINE','baseline')]:
    chapter=chapter.replace('{{'+tag+'_OUTPUT}}',output(name))
for tag,value in [('MOCK_TABLE',mock_table),('PYTHON',proof['python']),('SQLITE',proof['sqlite']),('OS',proof['os'])]:
    chapter=chapter.replace('{{'+tag+'}}',value)
assert not re.search(r'\{\{[A-Z_]+\}\}',chapter)
filename='system-design-handbook-part-2-module-0-design-method-estimation.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
metadata={'label':'A0','module':0,'chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),'interview_questions':30,'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':['estimates.py','objectives.py','baseline.py'],'mock_minutes':sum(minutes for _,minutes in mock)}
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
