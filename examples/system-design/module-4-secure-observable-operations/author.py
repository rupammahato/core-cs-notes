"""Generate A4 with exact local policy/runtime/indicator sources and measured evidence."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
sources = ['policy.py', 'server.py', 'indicators.py']
outputs = ['authorization', 'uploads', 'quota_window', 'quota_race', 'drain',
           'saturation', 'telemetry', 'objectives', 'planning']


def code(name):
    return '```python\n'+(BASE/name).read_text(encoding='utf-8')+'```'


def output(name):
    return '```json\n'+json.dumps(proof['observations'][name], ensure_ascii=False, indent=2)+'\n```'


chapter = r'''# Architecture and System Design Placement Handbook — Part 6
# A4: Operating a Secure and Observable System

**Estimated time: 3–4 hours | Architecture numeric module: 4 | Requires: A1–A3; Resume M8/M16–M19 refreshers**

---

## Why this module exists

A backend can return correct results in a happy-path demo and still leak another tenant's files, exhaust its database under a burst, accept unsafe uploads, interrupt requests during deployment or hide an outage behind a healthy-looking average. Operating the system means defining who may do what, how much work it accepts, how it behaves during failure and how evidence reveals the result.

This chapter uses a temporary loopback HTTP API with current SQLite membership checks, scoped note/list/download queries, shared quota decisions, a private text-upload quarantine, readiness/drain controls and bounded diagnostic records. An offline exercise separately calculates SLI/error-budget/percentile results from authored samples, plus hypothetical capacity and cost arithmetic.

**Organizing principle: carry authority through every data path, bound accepted work, and measure the user's actual outcome.**

This is a separate Python learning fixture. It does not modify [A1's Express backend](/docs/system-design/application-architecture-service-boundaries), [A2's cache](/docs/system-design/data-caching-scaling) or [A3's workflow](/docs/system-design/reliable-workflows-concurrency). Published lesson tokens map to server-controlled principals; they are not production credentials, OAuth, sessions or TLS. The standard-library HTTP server is for owned loopback tests, not public deployment. [Python http.server documentation](https://docs.python.org/3.12/library/http.server.html).

The 30 Q&As are editorial placement practice, not a measured employer-frequency ranking. A4 addresses architecture-bank Q23/Q24 and operations follow-ups in Q04/Q11/Q15. The five foundations are now available; worked systems S0–S13 remain a separate sequence. Refresh [M8: API security](/docs/resume-skills/api-security-authorization-multi-tenancy), [M16: Docker](/docs/resume-skills/docker-fundamentals), [M17: deployment](/docs/resume-skills/linux-deployment-nginx-pm2), [M18: cloud](/docs/resume-skills/aws-gcp-fundamentals) and [M19: testing/observability](/docs/resume-skills/git-ci-cd-testing-observability-performance) for stack details.

---

## 1. Operational requirements are part of the design

| Requirement | Private-note example | Failure to make concrete |
| --- | --- | --- |
| Confidentiality | A principal sees only its tenant/owner's content | A correct 200 response leaks another user's data |
| Integrity | Only allowed roles can upload or mutate state | A viewer changes ownership or uploads arbitrary data |
| Bounded resource use | Request, stored bytes and active work have explicit bounds | One tenant or burst exhausts everyone else's capacity |
| Safe lifecycle | New work stops during drain while accepted work finishes | Deployments lose acknowledged work or sever active requests |
| Useful availability | Eligible note reads succeed within the stated latency boundary | A live process cannot satisfy its actual operation |
| Diagnosis | Correlated, privacy-aware records connect symptoms to work | Raw payload logs leak data while aggregate averages hide failure |
| Recovery | Dependency, storage and deployment failures have owners/actions | A dashboard reports trouble but nobody knows how to restore service |

Security and reliability are connected. A quota can protect capacity, but refusing valid work is still a user-visible outcome. A cache can improve latency, but a stale permission decision can violate confidentiality. An error budget is not permission to leak a small fraction of private notes.

Write the invariants and degradation policy beside the operation. “Fast and secure” is not testable until the actor, resource, load, expected result and measurement boundary are specified.

---

## 2. Identity, membership and resource authorization

Authentication establishes an identity under a credential contract. Authorization decides whether that identity may perform this action on this resource now. A valid token is not automatic permission to read every row, file or tenant.

OWASP recommends least privilege, deny-by-default behavior and permission checks at the relevant request/resource boundaries. Tests should include attempts outside the allowed combinations rather than only successful owner requests. [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

The fixture maps an exact lesson bearer token to `(tenant,user)`, then reads the current membership role/active state from SQLite. Viewer can read; editor can read/upload; unknown roles and inactive/missing memberships deny. Note/list/download queries still filter by owner and tenant after the role decision.

| Decision | Authority here | Untrusted input that cannot override it |
| --- | --- | --- |
| Tenant and user | Server-owned lesson-token map | `X-Tenant`, `X-Owner`, body fields or URL guesses |
| Current role/membership | SQLite membership row | Client claims that it is an editor |
| Note ownership | Scoped query predicates | A known or guessed note ID |
| Upload download permission | Current membership + scoped metadata row + ready state | Storage key or original filename alone |

The same `shared_id` exists in two tenants with different synthetic private content. Correct scoping returns each tenant's own row. Another owner in alpha receives the same 404 representation as an absent note. This is an explicit application contract; not every API must choose 404 over 403 for resource concealment.

Observed authorization behavior:

{{AUTHORIZATION_OUTPUT}}

Revoking membership blocks the next request. The store rechecks authorization when retrieving content or accepting an upload, including after the handler's first decision. This does not revoke bytes already returned or promise to interrupt an already authorized in-flight response at the exact revocation instant. Define that boundary if a product needs stronger revocation behavior.

---

## 3. Tenant scope must survive every data path

| Path | Required scope/authority | Common bypass |
| --- | --- | --- |
| Direct get/replace | Verified principal + resource ownership/permission | Filter only by resource ID |
| List/search | Scope before returning any result/metadata | Protect detail route but leak titles through listing |
| Cache | Tenant/representation scope and current permission policy | Note-ID-only key or stale sharing grant |
| File/object download | Scoped metadata plus accepted object state | Direct public storage URL bypasses application policy |
| Background job | Trusted originating context or service authority, current policy where needed | Trust arbitrary tenant IDs embedded in an unverified message |
| Vector/graph retrieval | Tenant-bound retrieval plus permission-aware result handling | Cross-tenant chunks escape through a derived index |
| Logs/traces | Minimal permitted data with restricted operational access | Raw headers, tokens, content or private URLs in telemetry |

The HTTP fixture executes get/list/download checks. Cache, queue, vector and graph paths are architectural follow-ups connected to A2/A3 and the resume chapters; they are not implemented as extra backends here.

For a multi-tenant AI knowledge base, filtering retrieval by tenant is necessary but may not be sufficient for per-document grants and revocation. Keep authoritative permission/version policy clear across the source, chunks, cache and generated response. Use later S11/S12 for worked designs rather than assuming this note-owner policy covers shared documents.

Least privilege also applies to services and infrastructure. Separate application read/write needs from schema migration, backup, operational inspection and upload-validation duties. SQLite in this fixture does not demonstrate database roles, row-level security, cloud IAM or OS-level per-service isolation.

---

## 4. TLS, secrets and trusted intermediaries

Transport security protects data on the chosen network hop and authenticates endpoints under a certificate/trust policy. It does not decide which note the caller owns. If TLS ends at a reverse proxy, explicitly decide the protection and identity trust on the next hop. [OWASP TLS guidance](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html).

Do not copy credentials into source files, client bundles, container images, URLs or routine logs. Use a suitable secret authority, narrowly scoped access, rotation/revocation and audited retrieval. An environment variable is a delivery mechanism, not a complete secret-management lifecycle. [OWASP secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).

The fixture's `lesson-*` tokens are intentionally public teaching strings and are useful only inside its loopback test boundary. It verifies mapping/rejection/resource policy, not password storage, token signing, issuer/audience checks, session expiry or real credential theft resistance.

A gateway/BFF may verify credentials, but the backend must establish which identity assertion it trusts and retain resource-level policy. Client-supplied forwarding headers are not automatically trustworthy. Keep request/trace correlation separate from authentication: a trace ID helps connect observations; it does not authorize a tenant or operation.

---

## 5. Quotas, rate limits and concurrency bounds

| Bound | What it limits | Fixture example |
| --- | --- | --- |
| Transport body bound | Bytes accepted for one upload | 1–1024 bytes with a fixed Content-Length |
| Request-rate quota | Requests accepted for a scope/time rule | Tenant + action + ten-second fixed window |
| Retained-byte quota | Accepted stored bytes across operations | 2048 bytes per tenant, including retained pending/rejected objects |
| Active-work bound | Application work currently admitted | Capacity 1 or 2 under controlled tests |
| Queue/backlog bound | Deferred demand and memory/storage growth | Discussed; no general background queue added in A4 |

A rate quota does not bound concurrent slow work by itself. A concurrency gate does not enforce long-term fairness or storage limits. Use the bounds required by the actual resource and distinguish per-tenant fairness from protecting the shared service.

The fixed-window counter increments conditionally inside SQLite `BEGIN IMMEDIATE`. Independent connections cannot both take the final slot. A client-side counter or one process's dictionary would not coordinate other instances. The example's request budget uses the verified tenant, so switching between two users does not evade that tenant's quota.

Observed window behavior:

{{QUOTA_WINDOW_OUTPUT}}

Two requests just before a boundary and two just after it can be accepted in a short interval. That is the fixed-window algorithm's boundary burst, not an implementation bug. A sliding window or token bucket provides a different contract; S1 will build those mechanisms.

Observed final-slot race:

{{QUOTA_RACE_OUTPUT}}

Request quota rejection is 429 with a retry delay; the admission gate uses 503 for shared overload/not-ready. The retained-byte quota has no automatic time reset, so its 429 does not invent a meaningful `Retry-After`. Production APIs should explain whether recovery requires time, deletion, a plan change or operator action.

The quota clock is injected in verification. A distributed implementation needs a consistent window/time authority and a clock-skew/restart policy. The SQLite shared-file test is local, not a multi-region limiter or a Redis atomic-script benchmark. Old quota windows are pruned, but tenant cardinality and storage still require a capacity plan.

---

## 6. Safe upload state and storage ownership

Uploads combine untrusted bytes, metadata, storage cost and later processing. Choose allowed types, size bounds, generated storage keys, quarantine and download policy before accepting broad file formats. A filename extension or client MIME header alone does not validate the content. [OWASP file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

The fixture deliberately supports only small `.txt` uploads. It accepts a bounded ASCII filename for metadata, requires `text/plain`, stores bytes under a generated hex key in an owned private directory and records `pending` metadata. The original filename never becomes a disk path.

```text
authorized upload -> fixed-length/body/type/name checks
                  -> private generated-key bytes + pending metadata
                  -> internal byte digest/UTF-8/NUL validation
                  -> ready or rejected

authorized download -> tenant/owner metadata -> ready check -> attachment bytes
```

Pending and rejected objects cannot be downloaded. The internal validator compares stored size/digest and strict UTF-8 decoding, then rejects NUL-containing text. It is not an antivirus scanner, content-disarm service or proof that arbitrary text is harmless in every downstream parser.

Approved downloads use `application/octet-stream`, attachment disposition, `nosniff` and `no-store`. These response choices reduce unintended browser interpretation in the teaching contract; they do not replace permission checks or make public serving of arbitrary uploaded content safe.

Observed upload behavior:

{{UPLOADS_OUTPUT}}

The bytes and SQLite metadata are two storage systems. The normal exception path removes a file when its metadata transaction rolls back, but a process/storage failure between writing bytes and committing metadata can leave an orphan. No process-kill cleanup/reconciliation protocol is implemented. A deployed upload service needs durable staging/completion, orphan detection, retention and safe deletion; S3 develops that separate system.

Retained rejected/pending objects still consume this fixture's storage quota. The code has no cleanup/deletion API, multipart upload, presigned object URL, executable preview, archive decompression or malware sandbox. Those require their own limits and lifecycle rather than extending the `.txt` checker by assumption.

---

## 7. Runnable policy, quota and quarantine source

Files live under `examples/system-design/module-4-secure-observable-operations/`. Three exact runnable source files are embedded. `policy.py` owns current membership, scoped reads, transactional quotas and upload metadata/private files.

{{POLICY_CODE}}

The connection is protected by an `RLock` because this HTTP lesson uses several handler threads with one SQLite connection. The cross-connection quota test separately verifies the database transaction boundary. The connection lock alone would not protect another process or database connection.

The upload directory is an application-owned temporary root with no untrusted local writer in the test. Generated keys and scoped metadata prevent a request ID from becoming an arbitrary path. A hostile co-tenant process, filesystem permission mistake, symlink attack or object-store policy error is a different trust boundary and is not simulated here.

---

## 8. Liveness, readiness and startup are different questions

| Signal | Question | Wrong coupling to avoid |
| --- | --- | --- |
| Startup | Has initialization progressed enough for normal health handling? | Restart a legitimately slow initialization repeatedly |
| Liveness | Is this process making the progress that requires restart if absent? | Restart every replica because a shared database is down |
| Readiness | Should this instance receive new application traffic now? | Declare ready because its TCP socket exists |
| Dependency health | Can this operation use its required dependency? | Treat every optional dependency as fatal to all routes |

Kubernetes provides startup, liveness and readiness probes with distinct effects. Failed readiness affects traffic eligibility; liveness/startup failure can trigger restart under configured thresholds. Choose checks that reflect the workload and avoid synchronized restart storms for shared dependency failure. [Kubernetes probe concepts](https://kubernetes.io/docs/concepts/workloads/pods/probes/).

The fixture's `/livez` returns a minimal 200 when the handler runs. `/readyz` checks initialized/database-available/draining flags. A controlled dependency-unavailable flag removes readiness and rejects new application work while liveness stays 200. This is application state-machine evidence, not an actual database connectivity probe or Kubernetes deployment.

Production readiness may need cached bounded checks of required dependencies, migration/schema compatibility and capacity state. Probe credentials and response bodies should reveal only necessary operational information. A probe must have its own bounded runtime; probing an overloaded backend in an expensive way can worsen the incident.

---

## 9. Graceful draining and deployment

When a replica is stopping, it should stop admitting new application work, become ineligible for new routed traffic, let accepted work finish within a grace deadline and close resources deliberately. Routing changes and termination signals do not necessarily arrive in a neat global order.

Kubernetes termination involves endpoint state, termination grace and process signals/hooks. Actual rollout behavior needs integration testing with the configured router, server and orchestrator. [Kubernetes pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination-flow).

The local runtime uses a condition-protected drain flag and active-work count. Verification holds an already admitted read with an internal barrier, starts draining, checks that new reads fail, then releases the accepted read and observes completion.

{{DRAIN_OUTPUT}}

No operating-system termination signal is sent. The test calls the application drain method and then closes its owned servers/threads. It demonstrates the application policy; signal wiring, load-balancer propagation, keep-alive behavior, HTTP/2 streams, WebSockets and forced termination are separate deployment work.

For background work, draining also means stop new claims and decide whether accepted jobs finish, release safely or recover after lease expiry. Never assume a shutdown hook makes every external effect unambiguous; A3's operation identity and recovery still matter.

Use compatible schema evolution for rolling deployments: expand supported fields/schema, deploy readers/writers that tolerate the transition, migrate/backfill, verify, then contract obsolete behavior when safe. A code rollback cannot always reverse an irreversible data migration. The fixture does not perform a rolling release or migration benchmark.

---

## 10. Admission control and the overload experiment

An active-work gate accepts only a bounded number of application requests. It makes overload explicit instead of allowing an unbounded work queue to accumulate until memory, sockets or database connections are exhausted.

The controlled saturation experiment admits two requests and holds them at a test barrier, offers six more, then releases the first two:

{{SATURATION_OUTPUT}}

This demonstrates two accepted completions, six explicit overload responses and a peak active-work count of two. It does not establish a sustainable QPS, p99 latency at a realistic workload or the maximum connections the machine can handle. The artificial barrier intentionally creates saturation.

The standard-library threaded server can create handler threads before this gate runs, so the gate bounds application work, not all accepted sockets/threads. A production edge/server still needs connection, header/body, worker/thread and queue bounds. The three-second socket timeout in the lesson is not an end-to-end request deadline.

Load shedding should preserve a useful service contract. Distinguish business quota, shared overload, unavailable dependencies and deliberate drain. Do not quietly report rejected eligible requests as successful service availability; the SLI policy must account for them.

---

## 11. Runnable HTTP lifecycle and diagnostic source

`server.py` binds only to loopback on an ephemeral port. It generates its own correlation ID, maps credentials, checks current policy, consumes scoped quota, performs bounded application work and writes selected diagnostics. Health routes expose minimal state and bypass business admission.

{{SERVER_CODE}}

The active count remains held through response writing and is released in cleanup. Its timing measures local handler work through the write attempt; it does not include every client/network/proxy phase or establish that the user received the bytes. A failed write can still have an attempted response status, which is why external/client-side outcome measurements matter.

Only GET/POST lesson routes are implemented. This is not a hardened public HTTP stack or an OpenTelemetry instrumentation library. The structured records are captured in memory by the harness; no collector, metrics backend, dashboard or alerting service is started.

---

## 12. Logs, metrics and traces answer different questions

| Signal | Useful question | Notes example |
| --- | --- | --- |
| Log/event record | What happened for this particular operation? | Safe request metadata with a correlation ID |
| Metric | How much/often/slow across a defined population? | Request counts by method, route template and status class |
| Trace | Where did one operation spend work and cross boundaries? | Receive → identity → policy → quota → store → response |
| Audit record | Who performed a security-relevant action under which policy? | Separate protected actor/action/decision evidence when required |

OpenTelemetry defines signals used to describe system behavior; effective correlation and propagation need an actual instrumentation/export path. The local event list demonstrates request flow, not a distributed span graph or an OTel exporter. [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/).

For online services, measure requests, errors and latency, plus saturation/in-progress work and important dependency stages. Use counters for accumulating events and gauges for quantities that rise and fall. Avoid turning user IDs, note IDs, raw URLs or trace IDs into unbounded metric dimensions. [Prometheus instrumentation guidance](https://prometheus.io/docs/practices/instrumentation/).

Observed diagnostic contract:

{{TELEMETRY_OUTPUT}}

The fixture's bounded deques retain only the newest 128 logs/traces; its counters accumulate during that runtime. The log schema allows only request ID, method, route template, status and duration. It excludes bearer tokens, private note/file content, filenames, raw query values and exception detail. The client cannot replace the internal correlation ID with arbitrary text.

This is not a complete security audit trail. For investigations, a separate restricted audit stream may need actor/policy/action identity and safe error categories, with retention, integrity and access controls. Do not remove all accountability in the name of redaction, or dump every request body in the name of debugging. [OWASP logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

---

## 13. Latency distributions and measurement boundaries

The mean does not reveal whether a small fraction of users experience long waits. p95 and p99 describe selected quantiles under a defined population, interval and calculation convention. A p99 from five requests is not a precise population guarantee, and averaging per-instance percentiles is generally not a fleet percentile.

Use a histogram or suitable distribution mechanism when aggregating across instances/time. Choose bucket boundaries around meaningful objectives and consider quantile approximation. The offline exercise uses an explicit nearest-rank calculation over a complete authored list; that is different from a live histogram estimator.

Separate server handling, queue wait, pool wait, dependency execution, network/proxy time and client-observed completion. Sampling can miss important errors or tails, so a sampled trace list should not silently become the denominator of a complete request SLI.

Google SRE describes user-facing monitoring through latency, traffic, errors and saturation. Connect these symptoms to the operation and dependency rather than collecting numbers without a decision they support. [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/).

For A3 workflows, also measure accepted-to-completed age, oldest pending work, retries and dead items. A fast 202 response does not mean the user's indexing or delivery completed promptly. Use completion/freshness SLIs for asynchronous promises.

---

## 14. SLI, SLO, error budget and invariant gates

An SLI measures a chosen service outcome. An SLO sets a target for that measurement over a specified window. An error budget is the allowed bad outcome fraction/count under that target. An SLA is a separate service/business agreement; do not treat every internal target as a contractual commitment.

Google's SLO guidance emphasizes useful indicators, explicit good/valid events and an objective that guides reliability work. Decide the population, observation point and time window before calculating a percentage. [Google SRE implementing SLOs](https://sre.google/workbook/implementing-slos/).

The offline example defines an eligible event as an intended read of an owned existing note under its chosen lesson policy. A good event returns 200 within 200 ms. It authors 970 fast successes, twenty slow successes, five 503s, five 429s and three excluded 401 attempts.

| Input/policy | Consequence |
| --- | --- |
| Eligible reads | Denominator 1000 |
| Good reads | Numerator 970 |
| Target | Illustrative 99% good reads |
| Allowed bad | 10 events for this sample count |
| Observed bad | 30 events: slow success and eligible rejections both count |
| Remaining budget | −20 events |
| Burn rate | 3× the allowed bad fraction in this evaluated sample |
| Security invariant | Any observed confidentiality leak fails a separate gate |

Eligibility flags are authored fixture classification, not supplied by real HTTP clients or automatically inferred by this server. The example is not a measured production SLO. In a deployed system, define expected denials, missing resources, client cancellation, rate limiting and internal retries so the denominator cannot be manipulated to hide user harm.

A single fast 200 containing another tenant's content could pass an availability/latency indicator while violating confidentiality. The separate leak flag intentionally fails the acceptance gate even when its quantitative good fraction is one. Statistical success cannot excuse an invariant violation.

---

## 15. Runnable indicator and capacity-planning source

`indicators.py` validates explicit sample fields, calculates nearest-rank percentiles and uses exact rational arithmetic for the selected target/budget. It handles an empty denominator without claiming healthy service.

{{INDICATORS_CODE}}

Observed authored-sample results:

{{OBJECTIVES_OUTPUT}}

p95 is 50 ms while p99 is 350 ms for these samples. Slow successes and eligible 429/503s make the objective fail. The one-event leak case fails its invariant gate despite zero quantitative bad events. None of these values comes from the loopback API's timing samples.

Burn-rate alerts should account for the objective window, sustained impact, traffic volume and actionability. Multi-window policies can combine a longer confirmation window with a shorter signal to catch current fast burn without paging on every isolated error. The code calculates one sample's ratio; it does not implement a rolling multi-window alert evaluator. [Google SRE SLO alerting](https://sre.google/workbook/alerting-on-slos/).

Do not page on every debug symptom. A page should indicate urgent user impact or imminent risk and have an owner/runbook. Dashboards and tickets can carry slower capacity trends, known nonurgent failures and improvement work.

---

## 16. Capacity, cost and realistic validation

The planning helper uses explicitly hypothetical inputs: 200 requests/s, 50-ms mean service time, four instances, twenty possible connections each, a selected database budget of sixty, 720 hours and a fictional 0.10 currency units per instance-hour. It does not quote a cloud price.

{{PLANNING_OUTPUT}}

At a stable boundary where the assumptions apply, throughput × mean time gives an estimated mean in-flight count of ten. That is not a peak concurrency guarantee or a pool-sizing prescription. Four pools of twenty can request eighty connections against a sixty-connection selected budget. The computed 288 cost units excludes the database, storage, network, logs, backups and provider calls.

Before claiming capacity, define and record:

1. Hardware/runtime/deployment and dependency limits, schema/data size and key skew.
2. Operation mix, payload/page sizes, permissions and cache warm/cold state.
3. Offered arrival rate, completed/failed/rejected rate, active/queued work and client behavior.
4. Client and server p50/p95/p99, errors, freshness and correctness under load.
5. CPU/memory/GC, database pool/locks/I/O, network and provider bottlenecks.
6. Ramp, steady soak, bursts, dependency failure, restart/drain and recovery behavior.

A closed-loop client that waits for each response can reduce offered load as the service slows; report that test shape. An open-loop arrival schedule introduces different queuing/overload behavior and needs suitable client capacity. Neither model should hide rejected work or silently discard timeouts from the latency population.

The A4 burst is deliberately held work that verifies the admission bound. It is not a throughput benchmark. A0/A2's arithmetic, A1's HTTP contracts and A3's failure recovery establish different evidence; combine them carefully instead of presenting their counts as one production performance result.

Recovery needs evidence too. A replica is not a substitute for a backup/restore policy: an unwanted deletion can propagate to replicas. Define acceptable data loss and recovery time, protect backup access, and test restoring a coherent combination of canonical metadata and file/object bytes. Derived caches/projections may be rebuildable, but their rebuild time and permission behavior still matter. No backup restore or disaster-recovery timing is measured by this fixture.

---

## 17. Run, failure drills and scope

Verified on **{{DATE}}** with **Python {{PYTHON}}**, **SQLite {{SQLITE}}**, and **{{OS}}**. No third-party Python packages, Docker, cloud credentials or external observability services are required.

From the repository root in PowerShell:

```powershell
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 'examples/system-design/module-4-secure-observable-operations/verify.py'
```

Or run `python verify.py` from the fixture directory with Python 3.12 or later. The harness starts four owned HTTP servers on ephemeral loopback ports, closes each server and joins its serving/handler threads, closes SQLite connections and removes its exact temporary database/vault directory. Port 3000 is not used.

**{{TOTAL}} local checks passed:** {{COUNTS}}. Three exact source files and nine exact observation blocks are embedded; `verification-results.json` records the named assertions and scope.

| Drill | Actual evidence | Limit |
| --- | --- | --- |
| Resource/membership negatives | Real HTTP owner/tenant/role/revocation/identity-spoof rejection | Published allowlist credentials, no production identity provider |
| Upload lifecycle | Actual private bytes/metadata, quarantine/approval/download/digest/size tests | Text-only validation, no antivirus/object store/process-kill orphan cleanup |
| Quota race | Two independent SQLite connections, one accepted final slot | Local database/time model, no distributed Redis limiter |
| Dependency/drain | Real HTTP responses under controlled flags and held work | No actual dependency outage, OS signal or Kubernetes rollout |
| Saturation | Eight offered requests, two completions, six overloads, bounded active work | Artificial barrier; no sustainable QPS claim |
| Diagnostics | Actual request metadata/counters/ordered events with privacy checks | In-memory buffers, no collector or complete audit trail |
| SLO/planning | Authored sample classification and hypothetical arithmetic | No production SLO, billing price or measured capacity |

Use failure drills to verify invariants and recovery owners: dependency timeout must not cause a credential bypass; saturation must not expand quotas unexpectedly; draining must not erase accepted durable work; telemetry failure must not leak tokens or block the service indefinitely. The fixture covers selected local cases, not every failure combination.

For an incident runbook, connect symptoms to actions: rising overload responses call for inspecting offered demand and dependency/active-work saturation; widespread unready replicas call for checking the shared dependency without restarting every live process; a tenant-isolation violation calls for containing the affected data path and preserving restricted evidence; upload leftovers need metadata/byte reconciliation. Name the owner, safe mitigation, validation signal and rollback/recovery step. An alert without that response path is incomplete.

---

## 18. Common interview questions with answer checkpoints

### Q1. What does operating a backend add to a working API?

Authority, resource bounds, failure/lifecycle behavior, measurement and recovery ownership. A correct owner read is insufficient if another tenant can retrieve it, a burst exhausts dependencies or a deployment interrupts accepted work.

### Q2. Authentication versus authorization?

Authentication establishes identity; authorization decides permitted action/resource/context. The lesson token maps a principal, current membership supplies role/active state and scoped queries restrict content. Valid identity alone does not grant access to every note.

### Q3. How do you enforce tenant isolation?

Derive tenant context from a trusted boundary and carry it through queries, cache keys, files, jobs, indexes and diagnostics. Test negative combinations. A4 executes get/list/download scoping; queue/vector/graph isolation needs its own implementation and tests.

### Q4. Is a role check enough for a private note?

No. An editor role permits an action class, but the specific note still belongs to an owner/tenant or a defined sharing policy. A global editor role must not turn an ID guess into another user's content.

### Q5. What does least privilege mean beyond user roles?

Give services/operators/database accounts only the permissions their duties require. Separate migrations, backups, runtime queries and file validation where appropriate. This SQLite fixture does not demonstrate cloud IAM or database role enforcement.

### Q6. How does revocation affect cached or in-flight content?

The next request must use the intended current-authority policy; stale grants can leak data through caches or indexes. Already returned bytes cannot be recalled, and in-flight cutoff semantics need an explicit contract. A4 verifies the next-request membership check, not instantaneous global revocation.

### Q7. Does TLS solve API authorization?

No. It protects/authenticates the chosen transport hop under its trust policy. Resource permission remains an application decision. If TLS terminates at an intermediary, define the next hop's protection and the identity assertion the backend trusts.

### Q8. How should secrets reach an application?

Through a controlled secret lifecycle with narrow access, rotation/revocation and audit. Keep them out of source, images, URLs and routine telemetry. An environment variable alone is not a complete management solution; the fixture tokens are public teaching data.

### Q9. Rate limit versus concurrency limit?

A rate policy bounds accepted demand over time; a concurrency gate bounds currently admitted work. Slow requests can exhaust resources despite a rate bound. Use both when needed, plus payload/storage/queue limits tied to the resource.

### Q10. What key should a tenant quota use?

Use verified tenant/action identity according to the fairness contract. The fixture shares one tenant budget across Alice and Bob, so switching users does not reset it. User, IP and global limits can serve additional goals but have different bypass/fairness trade-offs.

### Q11. Why can a fixed-window limiter allow a burst?

It resets at a boundary, allowing up to a window's limit just before and again just after. The test accepts four requests around a two-per-ten-second boundary. That is the stated algorithm, not a sliding-window guarantee.

### Q12. Why must shared quota admission be atomic?

Two callers can both observe one remaining slot before either increments. A conditional counter update inside the authoritative transaction accepts only one. The two-connection race verifies this locally; a per-process dictionary would not coordinate other instances.

### Q13. What makes an upload safe to publish?

A defined type/size contract, private generated-key storage, quarantine/validation and current authorized download. Extension/MIME alone are insufficient. A4 validates small UTF-8 text/digest, not malware, archives or arbitrary document processing.

### Q14. Why not use the original filename as a storage path?

It mixes untrusted metadata with filesystem authority and can create traversal/collision problems. Use an application-generated key, scoped metadata and a controlled root. The filename can remain validated display metadata under a separate response contract.

### Q15. Are database metadata and object bytes one transaction?

Usually they are separate stores and need a completion/reconciliation protocol. The normal exception cleanup here removes a file after metadata rollback, but a process failure can leave an orphan. Do not claim atomic cross-store durability from this helper.

### Q16. Liveness, readiness and startup probes?

Startup handles initialization, liveness detects progress problems that warrant restart and readiness controls traffic eligibility. A shared dependency outage should not automatically restart every replica. The fixture exercises flags and responses, not a real orchestrator.

### Q17. What does graceful draining do?

Stop new application admission, withdraw traffic eligibility, let accepted work finish within a bound and close resources. Account for routing propagation and forced termination. A4 tests an application drain method; OS signal and load-balancer integration remain separate.

### Q18. Why can a deployment rollback still fail?

New code may have made data/schema changes that old code cannot read or reverse. Use compatible expand/migrate/contract steps and a recovery plan. The fixture does not perform rolling migrations or prove data rollback safety.

### Q19. What does the saturation test establish?

Under a deliberate held-work barrier, two requests complete and six excess requests receive 503, with peak active application work two. It proves that selected admission behavior, not sustainable QPS, realistic tail latency or socket/thread capacity.

### Q20. Logs, metrics and traces?

Logs describe particular events, metrics summarize a defined population and traces connect one operation's work across boundaries. A4 records in-memory metadata/counters/events. It does not run an OTel collector, Prometheus backend or distributed tracing deployment.

### Q21. Why use route templates in metrics?

Raw note/user/trace IDs create high-cardinality series and can expose private data. Bounded method/route-template/status-class labels support aggregation. Put permitted per-operation correlation in appropriately restricted diagnostic records instead.

### Q22. What should not appear in routine request logs?

Credentials, raw sensitive payloads, private URLs/query values and unrestricted exception details. Use an allowed schema and safe correlation. A separate protected audit stream may still need actor/action/policy evidence; the fixture is not a complete audit trail.

### Q23. Why p95 and p99 instead of only average latency?

Tail percentiles reveal slow subsets hidden by a mean or lower percentile. State population, interval, sample size and calculation/aggregation method. The authored sample has p95 50 ms and p99 350 ms; neither is a production measurement.

### Q24. SLI, SLO and SLA?

An SLI measures service behavior, an SLO targets it over a window and an SLA is a separate service/business agreement. Define eligible/good events and the observation point. Internal targets do not automatically become contractual promises.

### Q25. What is an error budget and burn rate?

Allowed bad events come from the target and denominator; burn compares observed bad fraction with allowed fraction for a defined interval. The offline 99% example allows ten bad events but observes thirty, or 3× burn. It is not a rolling production alert result.

### Q26. Should 429/503 responses be excluded from availability?

Not automatically. If the request is eligible under the service promise, rejection harms its outcome. Expected unauthorized requests may be outside that population. Publish the classification so quotas or shedding cannot make the reported SLO look artificially healthy.

### Q27. Can a good SLO excuse a confidentiality leak?

No. A fast 200 can contain the wrong tenant's data. The separate invariant gate fails that case even if availability/latency is perfect. Security correctness must not be hidden in an allowed statistical failure fraction.

### Q28. What makes an alert useful?

A clear user-impact/risk signal, suitable window/traffic context, owner and actionable runbook. Use pages for urgent response and dashboards/tickets for other trends. A single sampled trace or every isolated debug error is not an alert policy.

### Q29. How do you validate capacity?

Specify deployment, data/key skew, operation mix, arrival model, cache state and dependencies; measure offered/completed/rejected work, tails and saturation; test bursts, soak, failures and recovery. Connection and cost arithmetic are assumptions until supported by real workload evidence.

### Q30. What does A4 verify and what comes next?

Local HTTP policies/uploads/quotas/drain/admission/diagnostics, two-connection quota admission and offline SLI/planning calculations. It does not verify production identity/TLS, antivirus/object storage, Kubernetes rollout, observability backends or production capacity. The foundations now lead into S0's URL-shortener worked design.

---

## 19. Revision sheet and a 45-minute mock

| Prompt | Recall |
| --- | --- |
| Identity | Trusted credential context; do not take tenant authority from user headers |
| Permission | Current role + resource scope + every relevant derived path |
| Least privilege | User/service/database/storage/operator duties have bounded access |
| Quota | Verified scope + algorithm/time contract + atomic acceptance |
| Upload | Bounded bytes + generated private key + quarantine + authorized ready download |
| Readiness | Eligibility for new traffic; distinct from process progress |
| Drain | Stop admission, withdraw readiness, finish accepted work, close within a bound |
| Telemetry | Safe event metadata, bounded metric dimensions and causal correlation |
| SLO | Eligible/good events + window + observation point |
| Budget | Bad fraction versus target; independent correctness gates |
| Capacity | Workload/arrival model + completed/rejected work + tails + saturation |
| Evidence | Loopback mechanisms and authored samples; no production deployment claim |

**Mock prompt:** “Operate a multi-tenant notes API with private text attachments. It must survive bursts and deployments without leaking content. Define policies, lifecycle and evidence.”

| Segment | Minutes |
| --- | --- |
| Clarify actors, invariants and user promises | 6 |
| Trace identity/permissions through data and files | 8 |
| Define quotas, upload states and overload behavior | 8 |
| Walk readiness, drain and failure recovery | 8 |
| Define telemetry, SLI/SLO and load evidence | 10 |
| Recap limits, recovery owner and next change | 5 |
| **Total** | **45** |

A defensible short answer:

> I will derive tenant/user from a trusted credential boundary and apply current membership plus resource scope to get, list and file download. Uploads have bounded bytes, generated private storage keys and quarantine before an authorized ready-state download. Quota admission is atomic for its verified scope; active work is separately bounded. Draining withdraws readiness and stops new work while accepted requests finish within a grace policy. I will record safe route-level metrics and correlated diagnostic events, define eligible/good user outcomes and keep confidentiality as a separate invariant. Capacity claims require realistic offered/completed/rejected load and tail/failure measurements, beyond this local fixture.

Check whether you named the revocation boundary, the upload cross-store gap, routing/drain uncertainty, SLO denominator and the exact limitation of the saturation result.

---

## 20. Practice tasks

1. Build an actor/action/resource matrix for owner, other owner, other tenant, viewer, revoked member and internal validator. Trace every decision to an authority.
2. Run the HTTP negatives and explain why role checks do not replace owner/tenant predicates. Include list/download rather than only a detail route.
3. Extend the design on paper to shared-note revocation through a cache, job and vector index. State what permission/version must remain current.
4. Reproduce fixed-window boundary admission and the two-connection final-slot race. Compare the promises of a token bucket or sliding window without claiming they are implemented here.
5. Walk an upload from pending to ready/rejected, then describe the process-failure gap between bytes and metadata and a safe orphan-reconciliation policy.
6. Reproduce dependency-unready, live-but-unready and drain behavior. Define the additional Linux/orchestrator/router integration tests needed for deployment.
7. Reproduce the held-work burst and explain why it verifies admission rather than QPS capacity. Identify the unbounded socket/thread layer in this lesson server.
8. Inspect allowed log fields, route-template counters and request events. Propose protected audit fields and an actual export/retention strategy without logging tokens or content.
9. Recalculate the authored SLI and hypothetical pool/cost plan with changed inputs. Keep eligibility, percentile convention, budget window, price assumptions and exclusions explicit.
10. Complete the 45-minute mock and answer architecture-bank Q23/Q24. Name which additional evidence is required before making a production reliability or capacity claim.

---

## 21. Completion checklist

- [ ] I can separate identity, current membership, role and resource permission.
- [ ] I can trace tenant scope through direct, derived, file and diagnostic paths.
- [ ] I can explain least privilege, TLS hops and secret lifecycle.
- [ ] I can distinguish request, byte, active-work and backlog bounds.
- [ ] I can reproduce fixed-window behavior and atomic quota admission.
- [ ] I can explain quarantine, validation, download policy and orphan risk.
- [ ] I can distinguish startup, liveness and readiness.
- [ ] I can trace drain behavior and its deployment-integration limits.
- [ ] I can explain safe logs, metric cardinality and trace correlation.
- [ ] I can define SLI/SLO eligibility, error budget and independent invariants.
- [ ] I can separate arithmetic/saturation evidence from production capacity.
- [ ] I can complete a timed operations mock and proceed to worked designs.

---

## 22. Research references and continuation

Primary references reviewed on {{DATE}}. The code and scenarios are authored teaching examples, with explicit limits; the sources support named mechanisms rather than a claim that this is a complete vendor-prescribed deployment or a measured interview-frequency ranking.

| Primary source | Relevant boundary |
| --- | --- |
| [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | Least privilege, default denial and resource checks |
| [OWASP uploads](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Validation, private names/storage and publication control |
| [OWASP TLS](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html) | Transport-hop protection and trust |
| [OWASP secrets](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) | Access, delivery, rotation and lifecycle |
| [OWASP logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | Sensitive-data limits and security accountability |
| [Kubernetes probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/) | Startup/liveness/readiness distinctions |
| [Kubernetes termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination-flow) | Grace, signals and endpoint lifecycle |
| [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) | Logs/metrics/traces and instrumentation concepts |
| [Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/) | Metric types, service/dependency measurements and label costs |
| [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/) | User-facing latency/traffic/errors/saturation |
| [Google SRE SLOs](https://sre.google/workbook/implementing-slos/) | Good/valid events and useful service objectives |
| [Google SRE alerting](https://sre.google/workbook/alerting-on-slos/) | Error-budget burn and actionable windows |
| [Python http.server](https://docs.python.org/3.12/library/http.server.html) | Lesson server API and public-production limitation |

Return to the [architecture roadmap](/docs/system-design), [A1](/docs/system-design/application-architecture-service-boundaries), [A2](/docs/system-design/data-caching-scaling) or [A3](/docs/system-design/reliable-workflows-concurrency). Resume [M8](/docs/resume-skills/api-security-authorization-multi-tenancy) and [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance) supply security/measurement refreshers; deployment modules M16–M18 are linked individually in this chapter's introduction.

**Next: [S0 — URL shortener](/docs/system-design/url-shortener)**, architecture part 7 / numeric module 5. The first worked system combines create/redirect contracts, code uniqueness/collisions, expiry, caching and bounded analytics, with its own local HTTP/SQLite verification scope. All five foundations and S0 are authored; remaining worked systems and consolidation continue one section at a time.
'''

for name, tag in [('policy.py', 'POLICY'), ('server.py', 'SERVER'), ('indicators.py', 'INDICATORS')]:
    chapter = chapter.replace('{{'+tag+'_CODE}}', code(name))
for name in outputs:
    chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}', output(name))
for tag, value in [('DATE', proof['verified_date']), ('PYTHON', proof['python']), ('SQLITE', proof['sqlite']),
                   ('OS', proof['os']), ('TOTAL', str(proof['total'])),
                   ('COUNTS', ', '.join(f"{count} {name.replace('_', ' ')}" for name,count in proof['counts'].items()))]:
    chapter = chapter.replace('{{'+tag+'}}', value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-6-module-4-secure-observable-operations.md'
(ROOT/'System Design Notes'/filename).write_text(chapter, encoding='utf-8')
metadata = {'label':'A4','chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),
    'questions':30,'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':sources,
    'output_fidelity':outputs,'mock_minutes':45,'verified_checks':proof['total'],
    'next':'S0: URL shortener'}
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
