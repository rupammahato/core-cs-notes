"""Assemble M28 from reviewed resume claims and exact teaching-model evidence."""
from pathlib import Path
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE / 'verification-results.json').read_text(encoding='utf-8'))
catalogue = json.loads((BASE / 'resume-evidence.json').read_text(encoding='utf-8'))
sources = ['sla.py', 'hierarchy.py', 'sheet_sync.py', 'costs.py']

def code(name):
    return '```python\n' + (BASE / name).read_text(encoding='utf-8') + '```'

def output(name):
    return '```json\n' + json.dumps(proof['observations'][name], ensure_ascii=False, indent=2) + '\n```'

chapter = r'''# Resume Skills Placement Handbook — Part 30
# Module 28: Resume Project and Experience Deep-Dives

**Estimated time: 5–6 hours | Tier: 1 | Requires: relevant M0–M27 modules; practice with your actual project evidence**

---

## Why this module exists

Your resume gives an interviewer several concrete entry points: a payroll SLA engine, hierarchy-based authorization, asynchronous RAG ingestion, cross-service sessions, AI billing, a hash-ring load balancer, a festival website and an NGO chatbot. The next question is usually a request to explain a mechanism, trace a request, justify a choice or diagnose a failure.

This chapter turns those entry points into project explanations and technical follow-ups. It uses both supplied resumes, the completed learning modules and a limited read-only review of the public links in the PDFs. It does not assume that an architectural improvement discussed here existed in the original product.

**Organizing principle: explain your own contribution, trace the state change, and attach evidence to each claim.**

---

## 1. The evidence available and how to use it

The user-provided sources are `Rupam_Resume_Updated.pdf` and `Rupam_Resume_Product.pdf`. Their relevant project/experience sections were extracted with pypdf {{PYPDF}} into a catalogue containing source filename, page, anchor, text and SHA-256 checksum. Contact details and education are omitted from that catalogue. Each PDF contributes seven project/experience entries.

| Evidence class | Meaning in these notes | Safe use in an answer |
| --- | --- | --- |
| Resume-reported | A statement present in your supplied document | Explain it as your recorded account and recover supporting detail |
| Public self-report | A statement on your public profile | An additional account to reconcile, not independent verification |
| Locally verified teaching model | An executed example from this handbook | Demonstrate the mechanism and describe its limited scope |
| Proposed design | A recommended way to address a failure | Say what you would build or change |
| Unresolved detail | Original source/configuration/measurement not reviewed | Identify the missing evidence rather than inventing an answer |

The original employer repositories, deployment configuration, production logs and analytics exports were not reviewed for this chapter. No original business metric, internship contribution, revenue result or historical benchmark has been independently reproduced. The learning examples are original small fixtures, not recovered employer code.

The public GitHub profile adds details about the load balancer and Zyke; those remain self-reported. A current read of `megalith.co.in` identifies a 2026 site, which does not establish the architecture or analytics of the 2025 project. The linked load-balancer deployment could not be read through the research tool. No authentication, forms, payments or other live application actions were attempted. [Public GitHub profile](https://github.com/rupammahato), [current Megalith site](https://megalith.co.in/).

### Resolve these details before a final interview script

| Topic | Documents say | What needs clarification |
| --- | --- | --- |
| Datsol role title | Developer in technical PDF; Intern in product PDF | Use the accurate formal title and explain scope separately |
| 10X authentication coverage | 93 routes in technical PDF; 95 endpoints in product PDF | Commit/date, counting rule, exclusions and distinction from 42 BFF handlers |
| Load-balancer remapping | Keys in technical PDF; traffic in product PDF | Denominator and whether traffic was equally weighted by key |
| Load-balancer internals | Public profile describes a different hash space from M27's fixture | Verify original code; the teaching SHA-256 ring is a separate implementation |
| Zyke payments | Payments-live MVP; public profile describes a credits-funded project without cash collection | Separate payment integration readiness, test/live mode and actual customer revenue |
| Megalith metrics | Growth, concurrency, page-load/uptime claims | Year, tool, time window, population, percentile and measurement boundary |

These are reconciliation tasks. A difference in wording or snapshot date does not by itself prove a false claim. Keep the original values visible until the evidence explains them.

---

## 2. Build a 30-second, 2-minute and 5-minute explanation

Use a consistent structure: user/problem → your owned work → request/data flow → difficult decision → failure/test → result and measurement boundary. A list of framework names is not an architecture explanation.

The short drafts below use first person because they are rehearsal material grounded in your resume statements. Verify that the wording matches your actual contribution before using it. The longer versions are expansion outlines, not a promise that a fixed word count fits your speaking speed.

| Length | Content to prioritize | Stop before |
| --- | --- | --- |
| About 30 seconds | Problem, personal contribution, one hard mechanism | Listing every endpoint/library |
| About 2 minutes | One complete flow, choice, failure and outcome | A second unrelated project |
| About 5 minutes | Draw the design, trace success/failure, justify alternatives and evidence | Speculating about unreviewed production internals |

For a five-minute practice answer, allocate roughly 30 seconds to scope/ownership, 60 to the diagram, 60 to one state change, 60 to failure handling, 60 to choices/testing, and 30 to results/limits. An interviewer may interrupt at any stage; make each stage useful on its own.

Distinguish “I owned this module” from “the team built the product.” A commit ratio can support a narrow repository-history statement, but it is not a percentage of intellectual contribution or business impact. Explain your requirements decisions, implementation, review, rollout and debugging work using concrete artifacts.

---

## 3. Project map and the best follow-ups to prepare

| Experience/project | Main interview spine | Earlier modules |
| --- | --- | --- |
| Neosophical Labs | SLA lifecycle, working-day deadlines, ingestion and auditability | M10–M15, M19, M22/M25 |
| Datsol / Posterity | Candidate invitations, BFS authorization, reliable sheet sync | M7/M8, M14/M15, DSA graphs |
| 10X Analysts | Tenant-scoped RAG, async work, JWE sessions and BFF trust | M7/M8, M11, M18, M21, M23–M26 |
| Zyke | Usage metering, payment events and atomic credit effects | M9, M13/M14, M22 |
| Consistent-hashing load balancer | Placement, health/failure, proxy capacity and metrics | M4/M6, M17/M19, M27 |
| Megalith | Registration/auth, payment operations, dashboards and traffic evidence | M7–M9, M14, M19–M21 |
| Membition | Tenant provisioning, PDF ingestion, vector isolation and answer scope | M8, M11, M23/M24 |

For each row, prepare an API/data-flow explanation, a concrete invariant, a failure scenario, a trade-off and a source of evidence. Architecture-question-bank Q53–Q60 map directly to these themes; the wider worked-system chapters remain a separate planned track.

---

## 4. Neosophical Labs: workflows, SLA tracking and payroll-data quality

**Resume-reported scope:** a Telegram digest orchestrating agents over marketing data; a bureau SLA engine with task states, working-day-aware scans, escalation and audit history; an audit against a 30-section BRD/HMRC rules fixing four payroll defects; and Excel/XML/PDF normalization into a relational schema.

### Short draft

“At Neosophical Labs I worked on a UK payroll bureau platform. I built the SLA workflow around task states, working-day deadlines, tiered alerts and audit history, and worked on normalizing incoming client files. I also audited payroll calculations against the requirements and recorded rules, fixing four defects. The main engineering challenge was translating business rules into repeatable state changes and traceable checks.”

### Two-minute expansion outline

Explain the bureau user and one task that must be completed by a deadline. Identify what you personally built in the lifecycle and scan, then draw how a task is created, receives a deadline, changes state and becomes eligible for an alert. Separate deadline calculation from scheduled detection and external notification delivery. Describe one rule boundary you checked, how the expected result was established and how the regression was prevented. Explain the ingestion path from a client file to a validated normalized record, including rejected rows and provenance. End with the reported scope of four payroll defects and the artifacts needed to substantiate them, without inventing the exact formulas or customer impact.

### Five-minute walkthrough

1. Identify the actors: bureau user, responsible staff, scanner/worker and alert recipient.
2. Draw task state, due date, calendar reference, assignee, version and audit/alert records as a proposed model.
3. Trace an ordinary transition and its audit entry; explain how stale edits should fail.
4. Walk through a holiday/weekend, a missed scan and a duplicate alert attempt.
5. Explain one reviewed requirement/test case and how raw input provenance helps diagnose an ingestion defect.
6. State what shipped according to the resume and which original rule/tests/logs you would show.

### Architectural understanding and follow-ups

A proposed reliable flow is: validate the business event → calculate deadline from an explicit calendar policy → persist task/version → scan eligible tasks → persist alert intent → send notification → record delivery/retry. The database transaction should protect the local invariant; an external send needs its own retry/deduplication policy.

Clarify whether the starting day counts, which holiday calendar applies, what “nightly” means in the bureau timezone, whether escalation intervals are calendar or working days, and whether reassignment/rescheduling starts another alert lifecycle. Store the rule/calendar version if reproducing historical decisions matters. A working-day calculation and a scan scheduler are separate mechanisms.

For payroll, prepare a requirements-to-test matrix: BRD section, effective tax/rule period, expected behavior approved by the appropriate domain owner, input, observed result, fix and regression test. The resume's pro-rata, rounding and back-pay labels do not establish the precise four cases. Avoid presenting an invented arithmetic example as an HMRC-approved calculation. Current HMRC guidance is a reference entry point, not evidence of the product's historical compliance. [HMRC payroll overview](https://www.gov.uk/running-payroll).

For the marketing digest, distinguish fetching platform reports, calculating cohort metrics, summarizing and recommending an action. Check metric windows/timezones, missing data and duplicate scheduled runs. Agent output should retain source numbers and require suitable approval before any action that changes advertising spend. The resume says the digest helps steer spend; it does not establish a measured causal ROI improvement.

For Excel/XML/PDF ingestion, schemas and validation rules create the contract. An LLM/framework can assist parsing, but it must not silently decide payroll numbers. Preserve source file/row/page provenance, reject ambiguous values, guard duplicate imports and review low-confidence extractions. M15/M23 cover the underlying publication and provenance mechanisms.

---

## 5. Verified SLA model: dates, transitions, audit and alert intent

This is a new teaching model. It accepts a **calendar-local date supplied by the caller**; it does not derive that date from a timezone or run a nightly scheduler. It excludes weekends and a hand-authored holiday set when adding working days. It counts escalation tiers in elapsed calendar days after the due date, emits only the current tier if scans were missed, and never reschedules tasks. Those policies are explicit fixture choices, not recovered bureau rules.

{{SLA_SOURCE}}

{{SLA_OUTPUT}}

The example persists tier rows once per tenant/task/tier, reopens the SQLite file and verifies another scan does not duplicate them. It also verifies a stale expected version is rejected. A deliberately conflicting audit insert fails after the task UPDATE; the transaction rolls the task back. These are actual local database results, not proof of production notification delivery or parallel-load behavior.

The `pending` alert is intent, not a delivered message. A sender can crash after a successful external send but before recording delivery; handle that ambiguous outcome with the channel's appropriate idempotency/reconciliation strategy. Exactly one row in an outbox does not prove exactly one email or Telegram message.

Rescheduling would require a task lifecycle/rule revision in the alert identity, otherwise a legitimately new tier alert could collide with an old one. Cancellation, reopened tasks, assignment changes, holidays added later and a missed entire tier need business decisions before more code. Do not copy the toy uniqueness key unchanged without those decisions.

---

## 6. Datsol / Posterity: invitations, manager views and spreadsheet sync

**Resume-reported scope:** ownership of the hiring module and candidate portal; signed, expiring, revocable links with three scoped rate limiters; a BFS resolver for indirect reports; and sheet-ingestion fixes for blank timestamps, timezone shifts and dropped nested records. The product resume additionally describes MindMap analytics, 13 routes across four modules, and a ten-minute OneDrive sync.

### Short draft

“At Datsol/Posterity I owned the hiring assessment module and worked on manager access and external sheet synchronization. The candidate flow used signed, expiring and revocable links with scoped abuse limits. For manager views I built a BFS resolver that includes indirect reports. I also fixed ingestion failures involving blank timestamps, timezone interpretation and nested records, so the important questions are authorization boundaries and reliable identity matching.”

### Two-minute expansion outline

Start with HR creating an assessment and a candidate opening a constrained invitation. Explain which operation the link grants, how expiry/revocation are checked and why a signature alone cannot provide revocation. Trace a manager request from verified identity to the hierarchy-derived allowed set and the final scoped data query. Describe the blank-timestamp failure from the resume, the matching strategy and the regression boundary without guessing the unreviewed index definition. Finish with the OneDrive/analytics work if relevant to the role, distinguishing formula translation, scheduled synchronization and visualization. Give the accurate title after reconciling the two PDFs.

### Five-minute walkthrough

1. Draw HR, candidate, authenticated manager, portal/API and canonical data.
2. Trace invitation issuance, opening, authorization, expiry and revocation.
3. Show direct and indirect reports, a shared descendant and a cycle; explain traversal bounds.
4. Trace one external row through identity matching, timestamp interpretation and a nested update.
5. Describe the failing batch, patch and regression/reconciliation approach using original evidence where available.
6. Explain personal ownership and the scope of the reported routes/modules or analytics work.

### Invitation and rate-limit follow-ups

A proposed invitation record can hold tenant, candidate/assessment scope, token ID/hash, expiry, revocation and any redemption policy. The issued token must be unguessable or appropriately signed, and the server must verify its intended audience/purpose and current record state. Do not use the browser's claimed tenant or assessment as authority.

The resume names three scoped limiters but does not identify their exact keys/windows. Recover those configurations before naming them as implemented. Candidate IP, invitation identity and tenant-wide issuance are plausible **design alternatives**, not established historical scopes. A counter stored in one process does not enforce a deployment-wide quota across replicas. Verification and redemption must also avoid races when usage is limited.

### Hierarchy follow-ups

A hierarchy resolver provides a set of permitted subjects; the API must still scope the requested resource and action. Clarify what each polymorphic escalation relationship means and whether it grants visibility. Cycles and diamonds require a visited set. Tenant checks must cover intermediate nodes/edges, not just the start and final report. Invalidate cached access after org changes or role revocation. [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

---

## 7. Verified hierarchy model: a BFS result is only one policy input

The next function permits two illustrative edge types, `line` and `escalation`. Their names do not claim to reproduce the original project schema or permission semantics. It rejects invalid tenant edges and traversal overflow rather than returning a partial authorization set.

{{HIERARCHY_SOURCE}}

{{HIERARCHY_OUTPUT}}

The hand-authored graph contains a cycle and a diamond. The output is `a, b, c`, with the root excluded and the shared descendant included once. Cross-tenant or missing referenced people are rejected. For a graph already loaded into memory, construction/traversal is linear in the visited graph size, with additional per-adjacency sorting in this deterministic fixture; database query count and latency are separate concerns.

In production, derive the manager identity from verified authentication and load only relations relevant to the tenant/policy. Do not load every tenant into an unscoped client-visible graph. Decide whether a malformed relation rejects the entire request or is quarantined for repair; never accidentally let a bad intermediate relation grant access. The fixture fails closed on a reached invalid tenant relation and rejects unknown relation types anywhere in its provided link set.

The original claim is about polymorphic escalation chains, not necessarily a strict tree. Explain edge direction, allowed relation semantics and data constraints. A BFS label without these details does not establish correct manager authorization. The example returns IDs; it does not implement authenticated HTTP, row-level security, a cache invalidation service or original route coverage.

---

## 8. Verified spreadsheet model: identity, time and nested updates

The resume mentions dual-key matching, but the exact original schema/index and conflict policy are unresolved. This new model uses a stable `(tenant, source, external_id)` identity. Its toy source additionally declares nonblank timestamps unique within a tenant/source. A blank timestamp can update by stable ID; conflicting ID/timestamp evidence is rejected. This is an illustrative contract, not a claim that timestamps are generally safe unique identifiers.

{{SHEET_SOURCE}}

{{SHEET_OUTPUT}}

The batch test first updates a record with no timestamp, preserving omitted nested scores and children. It isolates equal external IDs across tenants and sources. A later invalid row causes the earlier update in that same batch to roll back. This is real SQLite behavior; MongoDB document/index semantics and OneDrive synchronization were not executed here.

The partial-update policy is explicit: nested objects merge, arrays replace, omitted fields survive, and null remains a stored value. This is a custom patch contract, not an implementation of JSON Merge Patch. If an incoming file is a full authoritative snapshot, this policy may retain fields that should be removed. Choose snapshot versus patch semantics and test deletions separately.

The offset example converts `10:00+05:30` to `04:30 UTC`. A naive `10:00` is refused unless the caller supplies an explicit source offset. The resume says naive timestamps were anchored to UTC; that is correct only when the source contract says those values represent UTC. A fixed offset does not implement historical timezone/DST conversion. Python distinguishes aware timestamps from naive ones; this teaching policy chooses how to accept or reject them. [Python datetime](https://docs.python.org/3.12/library/datetime.html).

For a real sync, prepare checkpoint/cursor rules, replay semantics, source deletions, formula-version changes, raw-file retention and reconciliation counts. Do not catch every error and report a successful batch after silently dropping records. Also decide whether one invalid row rejects the whole batch or is quarantined with a durable error report. The example chooses whole-batch rollback; another policy needs its own invariant and evidence.

---

## 9. 10X Analysts: tenant-scoped RAG and cross-service sessions

**Resume-reported scope:** knowledge-base APIs backed by a pgvector RAG corpus; Cloud Tasks embedding work; owner/public/shared access that also gates graph reads; NextAuth JWE/HKDF session interoperability; and 42 BFF route handlers in front of FastAPI. Authentication coverage is reported as 93 routes in one PDF and 95 endpoints in the other.

### Short draft

“At 10X Analysts I owned knowledge-base APIs for a multi-tenant equity-research application. Uploads were processed asynchronously for RAG, and access followed an owner/public/shared model across retrieval and graph reads. I also worked on shared sign-in between Next.js and FastAPI and the BFF proxy layer. The key challenge was carrying verified identity and permission decisions across each boundary without exposing service credentials in browser code.”

### Two-minute expansion outline

Draw browser → Next.js/BFF → FastAPI → canonical metadata, task worker, vector corpus and graph. Trace upload acceptance separately from completed indexing. Explain who authenticates the user, which credential is forwarded or exchanged and where authorization is enforced. Describe the session-format interoperability challenge from the resume, including why decrypting a JWE is different from merely decoding a JWT-shaped string. Walk through a private document later shared or revoked, including worker jobs, vector/graph reads and cached results. Close with the scope of your APIs/proxy handlers and the route-count discrepancy that must be reconciled from original route inventories.

### Five-minute walkthrough

1. Define user, tenant, owner, public and shared-grant semantics; “public” needs a precise audience.
2. Draw the logical components without claiming an unreviewed deployment topology.
3. Trace cookie/session verification, BFF forwarding and FastAPI resource authorization.
4. Trace upload, durable job identity, processing generation and accepted retrieval evidence.
5. Handle duplicate tasks, stale workers, revoked sharing and unauthorized graph expansion.
6. Show the original route/configuration inventory and relevant positive/negative tests when available.

### Session interoperability: the follow-ups that matter

NextAuth v4 documents encrypted JWT sessions and helper-based decryption/verification; it can also use database sessions. Recover the actual session strategy, package version, custom encode/decode behavior and cookie options from the project. The resume's Next.js version does not establish its NextAuth version. [NextAuth v4 session options](https://next-auth.js.org/configuration/options).

A JWE provides an encrypted token representation; reading a base64 payload is not authenticated decryption. HKDF derives key material from secret input with context parameters. Interoperability requires the matching hash, salt, info, output length and token algorithm for the exact library/configuration. Do not paste a current Auth.js derivation recipe into a historical NextAuth project and assume compatibility. Prefer a supported verification/exchange boundary where possible, and test tampering, expiry, wrong key/context and rotation. [JWE, RFC 7516](https://www.rfc-editor.org/rfc/rfc7516.html), [HKDF, RFC 5869](https://www.rfc-editor.org/rfc/rfc5869.html).

Cookie origin/domain/SameSite/Secure policy, CSRF protections and CORS are separate from resource permission. A same-origin BFF can keep service credentials server-side; it still needs a fixed upstream, route/method policy, controlled forwarded headers and independent backend verification appropriate to the trust model. “Bearer tokens off the client bundle” does not by itself prove tokens never reach responses, logs or browser storage.

### RAG and graph boundaries

Queue delivery may duplicate or arrive in an unexpected order; a worker needs idempotent effects and source-generation checks. Acknowledging upload does not mean the document is searchable. Define states such as accepted, processing, ready and failed as a proposed contract and show where they are persisted. [Cloud Tasks limitations](https://docs.cloud.google.com/tasks/docs/common-pitfalls).

Authorization must cover document bytes, metadata, chunk/vector candidates, graph intermediate nodes/edges, citations and cached answers. A per-user graph view can still traverse unauthorized intermediate entities if the query is scoped only at the endpoints. M23–M26 provide actual learning fixtures for revision/tombstone acceptance and path scope; those fixtures do not prove the internship implemented every mechanism.

---

## 10. Zyke: AI usage, unit economics and payment correctness

**Resume-reported scope:** sole-engineer MVP in 26 days; 45 of 49 commits; a 26-endpoint Flask API and Next.js 14 client; metering across seven AI/image providers; Razorpay orders, HMAC webhooks, replay-safe handling and atomic credit debits. The product PDF additionally reports $0.05 per generation, a four-minute content cycle and URL-based brand onboarding.

### Short draft

“For Zyke I built an AI social-content MVP, including the Flask API, Next.js client and the payment and credit path. I normalized usage across seven AI/image providers and connected generation to a USD balance. The hard part was separating provider usage, user credit effects and payment confirmation so retries or repeated events could not charge twice. I would explain the shipped integration separately from actual customer revenue.”

### Two-minute expansion outline

Start with a user generating a post and the resulting text/image work. Identify the provider-specific usage units and pricing version, then distinguish estimating cost, authorizing/reserving credit and settling actual usage. Trace a payment order through a verified server-side event and a durable balance/ledger effect. Explain the duplicate event and concurrent-generation cases. Discuss the MVP constraints and which steps were simplified, using actual code if available. Finish with the reported 26-day/commit scope and any measured cost/time result only after defining its denominator and sample. The public profile's credits-funded account means payment readiness must not be casually described as collected revenue.

### Five-minute walkthrough

1. Draw generation intent, provider calls, usage capture and the user's credit state.
2. Explain token/image/other units and the pricing configuration effective for each request.
3. Trace the payment event and deduplicated credit effect with its business identity.
4. Walk through provider success with a lost response, failed images and duplicate webhook delivery.
5. Defend transaction/idempotency boundaries and a simpler MVP choice versus a future improvement.
6. Show repository history, payment mode and usage/cost records supporting the reported outcomes.

### Billing and payment follow-ups

Razorpay documents HMAC verification using the raw body, duplicate-event identification and the possibility of out-of-order events. Verification establishes the message came from a holder of the appropriate secret; it does not by itself apply the right business effect exactly once. Persist event/business identity and validate order, amount, currency and allowed state progression inside a suitable transaction. [Razorpay webhook validation](https://razorpay.com/docs/webhooks/validate-test/).

For generation, distinguish an estimate from the actual bill. Usage may be missing after a timeout even if the provider did work. Keep pricing version, model/provider, units, request identity and reconciliation state. With several calls, a partial success can incur cost even when the final product action fails. Define refunds or releases as business rules rather than assuming “error means zero cost.”

A proposed reserve → call → settle/release model protects against simultaneous requests spending the same balance, but it is an architectural recommendation unless original code confirms it. The resume claims atomic credit debits; it does not specify reservations or the original transaction implementation. M9/M22 explain the underlying ledger, idempotency and provider-boundary mechanisms.

---

## 11. Verified unit-normalization model and its limits

This model uses invented teaching rates for input tokens, output tokens and images. It does not encode seven live providers, call a model, debit a balance or reproduce the $0.05 resume result. Decimal-string inputs avoid introducing binary-float rounding before arithmetic; the chosen settlement precision and rounding rule are explicit fixture policies. Decimal operations still have a finite arithmetic context, which a real pricing system must size and test for its allowed ranges. [Python Decimal](https://docs.python.org/3.12/library/decimal.html).

{{COSTS_SOURCE}}

{{COSTS_OUTPUT}}

The three synthetic lines total $0.0848. That is a teaching result, not a correction to the resume. Input and output token rates are separate; per-image units use another denominator. Rounding each tiny line before summing can differ from rounding the final total. Choose and persist the policy, and reconcile against provider billing semantics.

To substantiate “$0.05 a generation,” define generation: one idea, post, image, full campaign or successfully completed customer action. Include retries, unsuccessful attempts, discounts/promotional credits, free-tier usage, fixed infrastructure and payment fees when relevant to the particular cost or margin claim. A cost estimate and a customer price are different quantities; neither establishes profitability without the other costs and realized revenue.

---

## 12. Consistent-hashing load balancer: defend the original project

**Resume-reported scope:** Express/Node/http-proxy, virtual nodes, deterministic routing, automatic failover, binary-search lookup, configurable IP/path/header keys and debug APIs. Reported metrics are 19.66% remapping and 2,046 requests/s; the product PDF also reports a three-failed-probe threshold and a latency/error improvement.

### Short draft

“I built a Node/Express load balancer using a consistent-hash ring with virtual nodes. It chose a stable primary from an IP, path or custom key and used health information to route around unavailable backends. My reported tests measured remapping and throughput, and I also investigated proxy overhead. To defend those results I need to show the exact workload, denominator, benchmark configuration and original fix.”

### Two-minute expansion outline

Draw a client, proxy, ring and backend pool. Trace key extraction, hash lookup, candidate selection, forwarding and response completion. Distinguish permanent membership changes from temporary health fallback. Explain why virtual nodes help ordinary key distribution while a hot key can still overload one owner. State the original reported remapping/throughput results with their unresolved measurement definitions. If discussing the public profile's keep-alive explanation, label it as self-reported until code and direct/proxied logs demonstrate the fix under equivalent load.

### Five-minute walkthrough

1. Define affinity versus stateless distribution and why the chosen key serves that goal.
2. Trace ring construction, binary search, wraparound and fallback complexity.
3. Simulate removal/addition and define moved keys versus moved traffic.
4. Explain health hysteresis, all-unhealthy policy, draining and ambiguous writes.
5. Compare direct/proxied benchmark boundaries and identify the demonstrated bottleneck.
6. Separate the original project claims from M27's independently executed learning fixture.

Your public profile describes a 32-bit MD5 ring and attributes the proxy improvement to keep-alive configuration. M27 deliberately uses a separate SHA-256-derived 64-bit teaching ring and measures 19.83% equal-key movement on its own corpus. The public account provides a hypothesis to verify in original code/logs, not independent reproduction. [Public project account](https://github.com/rupammahato).

Do not average 19.66% and 19.83%, or present 2,046 requests/s as a universal server capacity. Recover backend count, virtual-node settings, key corpus, traffic weights, direct/proxied commands, concurrency/arrival model, payload sizes, duration, p50/p95/p99, errors and machine limits. Identify whether the latency figures are means, percentiles or individual samples. M27 contains the full mechanism and benchmark-method discussion.

---

## 13. Megalith: registrations, operations and performance evidence

**Resume-reported scope:** official Next.js/TypeScript/MongoDB fest site; JWT/bcrypt roles and refresh-token rotation; jose in Edge Middleware; an aggregation-backed Recharts admin dashboard; Razorpay, generated certificates and mail. Reported results include 42.7% YoY user growth and 5K+ concurrent users; the technical PDF reports sub-two-second page loads and the product PDF reports 99.2% uptime.

### Short draft

“For Megalith I built the official festival website and operational flows around registrations, authentication, payments, certificates and organizer reporting. The stack was Next.js, TypeScript and MongoDB, with role-based access and a dashboard over aggregations. The resume reports strong traffic growth and peak usage. I would defend those numbers using their analytics windows and definitions, while explaining the registration and payment paths separately from static page delivery.”

### Two-minute expansion outline

Trace a participant opening a page, signing in, registering and paying. Separate static/CDN delivery from dynamic API work and organizer-only endpoints. Explain which JWT checks run at middleware and which authorization checks the API repeats; show refresh rotation and reuse handling from original code if available. Trace trusted payment confirmation before issuing certificates or emails, including duplicates and worker failures. Explain the dashboard's source collections and grouping rules. Close with the reported traffic, page-load and availability numbers only after naming the relevant tools, windows, populations and measurement boundaries.

### Five-minute walkthrough

1. Draw participant, organizer, web/API runtime, database, payment provider and output workers.
2. Trace one registration/payment state change and the durable record that authorizes fulfillment.
3. Explain roles, refresh/session lifetime and server-side resource checks.
4. Walk through duplicate payment notification, email failure and repeated certificate requests.
5. Describe a representative aggregation/index and protect operational/reporting queries from peak registration work.
6. Distinguish historical evidence from the currently visible 2026 website and discuss measured capacity limits.

Next.js 14 distinguishes Node and Edge runtime capabilities. A Node-only crypto dependency cannot be assumed to work in Edge; compatible library imports must be checked for that runtime. Password hashing belongs in an appropriate server execution path, not merely wherever a token is checked. The resume reports jose use, but the exact package/version and route runtime require original configuration evidence. [Next.js 14 runtimes](https://nextjs.org/docs/14/app/building-your-application/rendering/edge-and-nodejs-runtimes).

“5K concurrent users” may mean an analytics active-user window, open browser sessions, connections, virtual users in a test or simultaneous in-flight requests. Those are different measurements. “Sub-two-second page load” needs device/network, cache state, route, metric and percentile. “99.2% uptime” needs monitored endpoint, region, interval, success criterion and reporting window. Avoid claiming a thousand-user API stress test from a page-analytics widget.

Refresh-token rotation requires more than issuing another token: define previous-token invalidation, concurrent refresh races, replay response and session-family revocation. A valid role claim can become stale after a role change; sensitive API actions need current authority as appropriate. For certificate/email workflows, verified payment and a unique entitlement identity should guard duplicate effects; the original implementation must be checked before claiming these proposed safeguards existed.

---

## 14. Membition: tenant onboarding, ingestion and scoped answers

**Resume-reported scope:** a three-service multi-tenant RAG platform; a dedicated Pinecone index for each nonprofit; PDF chunking, OpenAI embeddings, 3072-dimensional upserts, Pydantic validation and path checks; and 13 answer-scope rules. The product PDF describes a seven-step intake plus one PDF becoming a live chatbot in one request.

### Short draft

“Membition was a multi-tenant chatbot platform for NGOs. I built onboarding and PDF ingestion into a retrieval-backed assistant, using separate Pinecone indexes for nonprofit knowledge bases, input validation and file-path checks. The system prompt constrained answer scope with 13 rules. The important distinction is that tenant isolation must be enforced by server-side data access, while prompt rules shape answers and need their own evaluation.”

### Two-minute expansion outline

Draw intake, application API, document storage/processing, embedding/index operations and chat retrieval as logical components. The resume says three services, but recover their actual boundaries rather than naming three guessed deployments. Trace tenant creation and an uploaded PDF through validation, chunk metadata, embeddings and index readiness. Explain where the authenticated tenant is mapped to its index and why a client-supplied index name is not authority. Discuss partial onboarding failure, duplicate requests and cleanup. Close with the difference between successful provisioning, an accepted asynchronous operation and the first useful chat answer.

### Five-minute walkthrough

1. Identify NGO admin, end user, tenant/index mapping and chat ownership.
2. Trace validation, storage path/object identity and ingestion provenance.
3. Explain chunking/embedding dimension and index schema compatibility.
4. Trace authorized retrieval, context construction, scope rules and source-supported output.
5. Handle duplicate provisioning, stale index mappings, deleted files and guardrail-evaluation failures.
6. Show the actual three-service diagram and provisioning/evaluation evidence when available.

An index per tenant provides a useful separation boundary only if the backend's trusted mapping selects it. Provisioning credentials, job payloads, queries, logs and deletion paths still need scope. Index count, cost and operations can motivate namespace/shared-index alternatives later, but changing isolation strategy requires a new permission/data-lifecycle analysis. Pinecone index creation has schema requirements that must match the vectors used. [Pinecone index creation](https://docs.pinecone.io/guides/index-data/create-an-index).

3072 dimensions alone does not prove the embedding model/version, metric or quality. Recover those settings and any configured dimension reduction; a migrated index can need re-embedding. The 13 prompt rules are application instructions, not a security boundary against arbitrary user input. Build labeled tests for answerable, unrelated, unsafe, prompt-injection, wrong-tenant and insufficient-evidence queries. No model inference or guardrail effectiveness from the original chatbot was tested here.

“One request” describes an interface boundary, not automatically atomic provisioning across storage, database, embedding provider and Pinecone. A proposed robust design returns an operation identity, persists progress and reconciles orphaned resources. If the original flow was synchronous, explain its timeout and partial-failure behavior honestly rather than retroactively claiming a durable workflow.

---

## 15. Shared architecture: make boundaries and state changes explicit

These projects share mechanisms, but their business invariants differ. A routing preference is not a payment ledger; a prompt boundary is not a tenant permission; a scheduled scan is not delivered notification evidence.

```text
Verified principal
   -> resource/action policy
   -> validated command + stable operation identity
   -> canonical transaction / versioned state change
   -> durable external-work intent
   -> retryable worker / provider boundary
   -> accepted current result + audit/provenance
```

This is a proposed reasoning template. It is not the documented architecture of every project above. Locate the original state owner and transaction boundary before applying it.

| Project flow | Invariant to explain | Failure to trace |
| --- | --- | --- |
| SLA transition | Task and audit history agree | Audit write fails after task update |
| Candidate invite | Only the intended current scope is granted | Revoked/expired or concurrently redeemed token |
| Manager view | Only authorized tenant/report resources are returned | Cycle or cross-tenant intermediate relation |
| Sheet sync | Stable identity and documented update policy preserve data | Invalid row after earlier batch updates |
| RAG ingestion | Only current permitted evidence is accepted | Late worker publishes an old source revision |
| AI billing | One authorized business action has the intended credit effect | Provider succeeded but response/acknowledgement was lost |
| Fest registration | Fulfillment follows the correct payment/registration state | Duplicate notification or partial certificate/mail work |
| NGO provisioning | A tenant reaches a known recoverable state | Index creation succeeds before metadata commit fails |

When asked for an alternative, compare one concrete trade-off: synchronous versus background ingestion; one index per tenant versus shared namespace; server-side session versus token interoperability; BFS on request versus precomputed closure; whole-batch rollback versus row quarantine. State which requirements change and what evidence would decide the choice. Do not claim every scalable-looking component was necessary at MVP scale.

---

## 16. Turn a resume bug into a technical incident explanation

Use: symptom → impact/scope → smallest reproduction → violated invariant → actual cause → fix → regression → rollout/reconciliation. If an exact cause is absent from available evidence, say which original artifact would establish it. You can still explain the class of failure and a verified teaching analogue.

| Resume incident | Supported starting point | Detail to recover |
| --- | --- | --- |
| Blank-timestamp async crash | A batch hit a unique-index failure; matching changed | Index key/options, original row, async error path and dual-key conflict policy |
| Dropped nested records | A spread/update lost subdocuments | Before/after payload and exact overwrite/merge semantics |
| Shifted timestamps | Naive timestamps needed explicit UTC anchoring | Source timezone contract and historical affected-row set |
| Payroll defects | Four pro-rata/rounding/back-pay defects reported | Each requirement, test input, approved expected result and patch |
| Proxy bottleneck | Reported direct/proxied latency/error regression | Original command, profile, agent setting and equivalent before/after runs |

Do not add an invented outage duration, number of affected customers or revenue saved. For the sync incident, the new fixture proves rollback and patch semantics on its own data; it does not prove the original repair reconciled all historical records. A strong answer distinguishes preventing another bad write from repairing data already lost or shifted.

Prepare one example of a choice you would change now. Tie it to a real constraint or measured failure: a missing persistent operation state, unclear timestamp contract, brittle session-coupling boundary or insufficient metric definition. Present the original decision's context fairly and explain the proposed improvement's cost.

---

## 17. Metrics: denominator, window, provenance and attribution

{{METRICS_OUTPUT}}

The growth example uses invented counts, 10,000 and 14,270, to demonstrate 42.7% arithmetic. They are not historical Megalith counts and cannot be inferred uniquely from the percentage. A percent-growth claim needs the original baseline, current count, matched population and comparable time windows.

The commit-ratio arithmetic gives approximately 91.84% for the reported 45/49 count. It does not establish 91.84% of effort, architecture ownership or product value. Recover repository/branch/time boundaries and explain concrete work rather than letting commit count stand in for contribution.

| Reported outcome | Evidence worksheet |
| --- | --- |
| 26-day MVP | Start/end criteria, release date, implemented scope and payment mode |
| Seven provider integrations | Provider/model list, unit adapters, usage records, pricing versions and failure policy |
| $0.05 generation | Definition, sample distribution, credits/discounts, retries and included cost categories |
| Four-minute content cycle | Start/end event, human edits, successful sample set and exclusions |
| 42.7% growth | Raw counts, analytics definition, comparable cohorts/windows and attribution limits |
| 5K+ concurrency | User/connection/request definition, observed window or test command and errors |
| Sub-two-second load | Specific performance metric, percentile, device/network/cache and route |
| 99.2% uptime | Endpoint, probes, observation window, exclusions and failed-check treatment |
| 19.66% remapping | Corpus, members/tokens, removed node and key/traffic/byte denominator |
| 2,046 requests/s | Successful goodput, latency/error budget, duration, generator and resource limits |

A before/after observation can support a result without proving that one feature caused every change. Seasonality, promotion, event attendance and measurement changes can affect traffic. Describe the engineering contribution and measured association; causal attribution needs suitable comparison evidence. Product/analytics modeling is a later track, but backend interviews still require honest definitions.

---

## 18. Assemble an interview evidence pack

Prepare a compact private pack from materials you are entitled to use: a sanitized diagram, relevant code/PR references, API/schema contracts, one regression test, a release or incident note, and metric definitions/raw exports where appropriate. Do not publish employer code, customer records, credentials or production tokens into these study notes.

| Project | Highest-value next artifact |
| --- | --- |
| Neosophical | Calendar/state specification, requirements-to-regression matrix and sanitized ingestion cases |
| Datsol | Invitation verification/revocation tests, hierarchy policy/schema and before/after sync rows |
| 10X | Package/session configuration, route inventory, trust diagram and permission-negative tests |
| Zyke | Pricing adapters, transaction/idempotency boundary, payment mode and usage/release evidence |
| Load balancer | Original ring/proxy code, benchmark commands and before/after raw results |
| Megalith | Historical 2025 revision, registration/payment flow and analytics/uptime definitions |
| Membition | Actual service diagram, tenant/index lifecycle and labeled answer-scope evaluation |

For each artifact, label version/date and which claim it supports. A screenshot can illustrate behavior but may not establish history, correctness under retries or the metric denominator. A public README is still self-report; an executed regression test supports only its tested case. Keep unanswered questions visible so rehearsal does not turn assumptions into autobiographical facts.

### What ran in this chapter

**81 actual local checks passed:** 12 hierarchy, 21 SLA, 18 spreadsheet, 12 cost, five metric-arithmetic and 13 evidence-catalogue checks. The first 68 exercise teaching models/arithmetic; the last 13 check PDF checksums, source classification and seven-project coverage. No cloud APIs, payment/provider calls, model inference, original employer services or production benchmark ran.

The executable model runtime was **Python {{PYTHON}}**, SQLite **{{SQLITE}}**, on **{{OS}}**. The model verifier uses the standard library. PDF extraction separately uses pypdf {{PYPDF}} from the already installed M23 environment. Temporary SQLite files are deleted after their connections close; no persistent model listener starts.

```powershell
Set-Location examples/resume-skills/module-28-resume-deep-dives
python verify.py
```

The site is separately built and checked using a temporary loopback server, then stopped. Port 3000 remains stopped.

---

## 19. Interview questions and answers

{{QUESTIONS}}

---

## 20. Practice tasks

1. Record a 30-second explanation for all seven project/experience rows. Remove unsupported adjectives and make personal ownership explicit; compare with the source PDF.
2. Draw a five-minute walkthrough for one internship and one project. Trace a successful state change and a failure across every trust/persistence boundary.
3. Reconcile Datsol's role title and the 93/95/42 route numbers from dated original records. Document what each count includes instead of choosing the largest number.
4. Extend the SLA fixture with a reschedule/lifecycle identity and explicit missed-tier behavior. Specify the business-calendar/timezone policy before implementing a scheduler.
5. Translate the original hierarchy relationship types into a permission policy. Test cycles, diamonds, role revocation, cross-tenant intermediates and traversal bounds.
6. Recover one sanitized original sync defect and test the intended snapshot/patch semantics, timestamp contract, identity conflict and batch-recovery policy. Reconcile historical affected records separately.
7. Build a version-pinned test at the actual 10X session boundary using owned demonstration credentials. Test wrong key/context, expiry, tampering, rotation, CSRF/CORS and unauthorized resources without copying production secrets.
8. Trace two concurrent Zyke generation attempts and duplicate payment events through the actual ledger/transaction design. Compare estimated, reserved, settled and provider-reconciled cost using synthetic data first.
9. Produce a metric worksheet for Megalith and the load balancer with commands/exports, windows, denominators, latency/errors and resource context. Keep unavailable evidence explicitly unresolved.
10. Build a labeled Membition evaluation set with in-scope answers, unrelated questions, prompt injection, cross-tenant requests, stale sources and partial provisioning. Separate retrieval permission from answer-scope quality.

---

## 21. Revision checklist

- [ ] I can explain each project's problem and my own contribution without a tool-name list.
- [ ] I can give a short pitch, two-minute expansion and five-minute request/state walkthrough.
- [ ] I can label resume-reported, locally verified, proposed and unresolved details accurately.
- [ ] I can reconcile title, route-count, timeline and metric wording across resume versions.
- [ ] I can explain working-day policy, SLA transitions, audit and notification deduplication.
- [ ] I can explain candidate-link revocation, scoped limits and hierarchy authorization.
- [ ] I can defend source identity, timestamp meaning and nested sheet-update semantics.
- [ ] I can trace sessions, BFF trust, async RAG work and access revocation across stores.
- [ ] I can distinguish provider usage, price, estimate, credit effect and actual revenue.
- [ ] I can defend ring routing and proxy benchmarks with workload/denominator evidence.
- [ ] I can explain fest operations and NGO provisioning failures without inventing topology.
- [ ] I can present metric definitions, one incident regression and a sanitized evidence pack.

---

## 22. Primary sources and verification artifacts

Sources were checked on **16 October 2026**. Current product documentation supports technical preparation; historical project behavior requires its own versioned code/configuration and evidence.

| Topic | Primary reference |
| --- | --- |
| Project claims | Both user PDFs in the repository root; [public self-report](https://github.com/rupammahato); [current fest site](https://megalith.co.in/) |
| Authorization | [OWASP authorization cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) |
| Payroll reference entry point | [HMRC running payroll](https://www.gov.uk/running-payroll) |
| Time and arithmetic | [Python datetime](https://docs.python.org/3.12/library/datetime.html), [Decimal](https://docs.python.org/3.12/library/decimal.html) |
| Session interoperability | [NextAuth v4 options](https://next-auth.js.org/configuration/options), [JWE RFC 7516](https://www.rfc-editor.org/rfc/rfc7516.html), [HKDF RFC 5869](https://www.rfc-editor.org/rfc/rfc5869.html) |
| Runtime boundary | [Next.js 14 Edge/Node runtimes](https://nextjs.org/docs/14/app/building-your-application/rendering/edge-and-nodejs-runtimes) |
| Async/provider boundary | [Cloud Tasks pitfalls](https://docs.cloud.google.com/tasks/docs/common-pitfalls), [Razorpay verification/idempotency](https://razorpay.com/docs/webhooks/validate-test/) |
| Vector provisioning | [Pinecone index creation](https://docs.pinecone.io/guides/index-data/create-an-index) |

Artifacts are under `examples/resume-skills/module-28-resume-deep-dives/`: four exact teaching sources embedded above, `extract_evidence.py`, project-only `resume-evidence.json`, `research-scope.json`, `verify.py`, named assertions/observations, cleanup evidence, dependency scope and content/site validation reports. The report distinguishes model execution, arithmetic and document provenance checks.

**Next: [M29: Consolidation and interview drills](/docs/resume-skills/consolidation-interview-drills).** Bring the backend/stack/project explanations together with revision routes, timed practice and cross-module debugging questions. The broader worked architecture track and product/analytics chapters remain separate planned work.
'''

questions = [
('Which project should you lead with?', 'Choose the one most relevant to the role and best supported by your own work and evidence. For backend roles, a clear authorization, transactional, asynchronous-processing or routing story often gives a stronger technical discussion than a broad list of product features. Be ready to switch when the interviewer chooses another resume bullet.'),
('How do you explain personal ownership without overstating it?', 'Name the module, decisions, implementation and debugging work you actually owned, then identify the surrounding team/product context. Distinguish the reported sole-engineer MVP from internship modules inside a larger platform. Repository counts support only a defined history claim, not an automatic share of effort.'),
('How would you explain the SLA engine?', 'Start with the task lifecycle, business-calendar deadline and escalation policy. Trace state persistence, audit and notification intent separately from external delivery. Explain missed scans, duplicate attempts, rescheduling and rule versions. The new model verifies a small policy; original bureau requirements remain the authority for the real implementation.'),
('What makes working-day deadlines tricky?', 'Starting-day conventions, weekends, regional holidays, timezone/DST, cutoff times and later calendar changes can affect the result. Separate a business date from a UTC instant. The fixture accepts a precomputed local date and a hand-authored holiday set; it does not implement the original scheduler or a legal calendar.'),
('Does one outbox row mean one delivered alert?', 'No. The sender can complete an external send and crash before recording delivery. Durable intent prevents losing local work but requires channel-specific idempotency or reconciliation for ambiguous outcomes. The SQLite model proves persisted tier deduplication, not exactly-once Telegram/email delivery.'),
('How would you defend the payroll bug fixes?', 'Show each reviewed requirement and its effective period, sanitized inputs, domain-approved expected result, failing case, patch and regression test. The resume supports four reported defects in named categories, not a complete reconstruction of formulas or proof of current HMRC compliance.'),
('How do signed, expiring invitations become revocable?', 'Verification must consult current authoritative invitation state or another revocation mechanism, not just the token signature and expiry. Scope the token to tenant, candidate, assessment and operation, validate audience/purpose, and handle redemption races. Recover the actual implementation before presenting a proposed token schema as historical fact.'),
('What were the three rate-limit scopes?', 'The resume states there were three scoped limiters but does not identify their keys/windows in the available text. Retrieve configuration/tests and explain why each scope fits its threat/workload. Per-IP, per-invite and tenant-wide controls are possible designs, not established details of this project.'),
('Why BFS for manager views?', 'It explores direct then indirect relationships and can collect a reachable report set. A visited set handles cycles/diamonds, while tenant and edge semantics determine which paths are permitted. The API still needs action/resource authorization; reachability alone does not grant every manager action.'),
('Can checking only the first and last tenant be enough?', 'No. A path can pass through a foreign or unauthorized intermediate entity or relationship. Scope traversal and canonical data, reject or quarantine invalid links deliberately, and keep cached permission sets current. M26 and this chapter demonstrate different controlled forms of that boundary.'),
('What went wrong with blank timestamps?', 'The technical resume reports an async batch failure involving blank-timestamp rows and a unique index, addressed by dual-key matching. Explain the original index definition, matching rules and error path from code. The new fixture uses explicit external IDs and a toy partial timestamp constraint; it does not recover the original schema.'),
('How do you prevent nested-record loss during sync?', 'Declare snapshot versus patch semantics. Preserve omitted fields only when the source contract calls for a patch, handle arrays/deletions explicitly and validate the resulting record. Test before/after nested payloads and reconcile any historical data loss; shallow spreading is not a universal deep-merge policy.'),
('How should naive timestamps be handled?', 'Establish their source meaning before assigning a timezone. If the source contract is UTC, anchoring to UTC preserves that meaning; otherwise use the correct timezone/offset policy or reject ambiguity. The example refuses naive values without a supplied policy and does not implement historical DST rules.'),
('Trace a 10X document upload into RAG.', 'Authenticate and authorize the upload, persist its canonical identity/revision and processing state, dispatch bounded background work, then publish only current permitted derived content. The exact original steps need code evidence; the resume reports Cloud Tasks and pgvector. Duplicate or stale workers must not silently override newer accepted data.'),
('How should owner/public/shared permissions propagate?', 'Define the audience and current grants, derive trusted identity, and enforce access across bytes, metadata, retrieval candidates, graph reads, citations and caches. Sharing/revocation updates need freshness handling at acceptance. Do not treat a filtered UI or a prompt instruction as the authorization boundary.'),
('Why was JWE/HKDF interoperability needed?', 'The resume reports a session-format boundary between NextAuth and the AI service. Encrypted token verification requires matching the actual library/configuration and derivation parameters. Explain the trust boundary and version-pinned tests; the available documents do not establish the exact algorithm or key-derivation recipe.'),
('Why put a BFF before FastAPI?', 'It can adapt client requests and keep service credentials in server code while presenting an appropriate browser-facing boundary. It also needs controlled upstreams/headers, session and CSRF policy, deadlines and resource authorization. The reported 42 handlers are not automatically the same inventory as 93 routes or 95 endpoints.'),
('How do you reconcile 93 routes and 95 endpoints?', 'Recover the relevant commit/date and counting rule, including methods, aliases, health/public routes and exclusions. Keep 42 BFF route handlers as a separate inventory unless the code establishes a mapping. Do not silently select the larger number or assert a growth explanation without evidence.'),
('How did Zyke normalize provider usage?', 'The resume says seven provider schemes were modeled. Explain each actual unit, pricing/model version, measured usage and failed/retried-call policy from the adapters. The teaching calculation shows token/image denominators and Decimal arithmetic with invented prices, not the original seven integrations.'),
('How do atomic debits avoid overspending?', 'The balance condition and credit effect must be enforced within the appropriate atomic/transactional boundary and deduplicated by business identity. Two read-then-write sequences can both observe enough credit. A reserve/settle design is one proposed approach; the original implementation must establish what actually shipped.'),
('Is a verified webhook enough to credit a user?', 'No. Validate the intended order, account, amount/currency and allowed state, then apply a deduplicated durable effect. A signature authenticates the payload under its secret, while replay/out-of-order handling and business authorization are separate. A client success redirect is not authoritative payment confirmation.'),
('What does the USD 0.05 generation claim mean?', 'It needs a precise action denominator, sample, provider/model configuration, retries and included cost categories, with promotional credits distinguished from list-price usage and realized cost. It is a reported figure, not a live provider price or the result of the new USD 0.0848 teaching example.'),
('Does payments-live mean collected revenue?', 'No. Distinguish a deployed payment integration, test versus live mode, successful real transactions and actual customer revenue. Reconcile the resume wording with the public credits-funded account using original payment records. Do not infer business traction from configured payment endpoints.'),
('How do you distinguish the original ring from M27?', 'The original resume/project account and M27 are separate evidence sets. M27 uses its own hash configuration, key corpus and real HTTP fixture and measures 19.83% equal-key removal movement. The original reported 19.66%, throughput and proxy improvement need original code/benchmark evidence.'),
('What would substantiate the proxy improvement?', 'An equivalent direct/proxied before/after workload, original agent/configuration change, raw latency/error results and resource observations. The public profile attributes it to keep-alive, which is still self-report. Do not compare unrelated runs or infer whether the latency numbers are means or percentiles.'),
('What does 5K concurrent users establish?', 'Only the measurement actually collected. Analytics users in a window, open sessions, connections, load-test virtual users and simultaneous requests differ. Retrieve the tool/window/workload and errors before describing API capacity, and separate static-page delivery from dynamic registration/payment behavior.'),
('How would you defend Megalith auth and fulfillment?', 'Trace middleware and API checks, current role authority, refresh rotation/reuse behavior, verified payment state and unique certificate/email entitlement. Cite original code/tests for implemented safeguards. Next.js 14 runtime constraints explain compatible crypto choices but do not prove every endpoint enforced authorization.'),
('Why a dedicated Pinecone index per NGO?', 'It can simplify tenant separation, provided trusted server mapping controls every operation. It also adds provisioning, cost and lifecycle overhead. Compare alternatives using requirements, and explain failed provisioning/deletion. The resume supports the chosen separation, not unreviewed current provider limits or the exact three-service topology.'),
('Do thirteen prompt rules make the chatbot safe and isolated?', 'They express answer-scope intent and need evaluation; they are not data-access controls or proof of universal refusal behavior. Enforce tenant selection outside the model and test in-scope, off-topic, injection, stale/unsupported and wrong-tenant cases. The original model/guardrail effectiveness was not run here.'),
('What should you do when asked for an unavailable detail?', 'State the supported part, identify the missing artifact and explain the mechanism or proposed design without inventing history. Follow with the concrete test or evidence that would settle it. A candid boundary is stronger than a precise-sounding algorithm, metric or incident timeline unsupported by your records.'),
]
chapter = chapter.replace('{{QUESTIONS}}', '\n\n'.join(f'### Q{i}. {q}\n\n{a}' for i, (q, a) in enumerate(questions, 1)))
for tag, name in [('SLA', 'sla.py'), ('HIERARCHY', 'hierarchy.py'), ('SHEET', 'sheet_sync.py'), ('COSTS', 'costs.py')]:
    chapter = chapter.replace('{{' + tag + '_SOURCE}}', code(name))
for tag, name in [('SLA', 'sla'), ('HIERARCHY', 'hierarchy'), ('SHEET', 'sheet'), ('COSTS', 'costs'), ('METRICS', 'metrics')]:
    chapter = chapter.replace('{{' + tag + '_OUTPUT}}', output(name))
for tag, value in [('PYTHON', proof['python']), ('SQLITE', proof['sqlite']), ('OS', proof['os']), ('PYPDF', catalogue['pypdf'])]:
    chapter = chapter.replace('{{' + tag + '}}', value)
assert len(questions) == 30 and not re.search(r'\{\{[A-Z_]+\}\}', chapter)
filename = 'resume-skills-handbook-part-30-module-28-resume-project-experience-deep-dives.md'
(ROOT / 'Resume Skills Notes' / filename).write_text(chapter, encoding='utf-8')
content = {'chapter': filename, 'words': len(chapter.split()), 'lines': chapter.count('\n'), 'interview_questions': 30, 'practice_tasks': 10, 'unchecked_learning_items': 12, 'projects': 7, 'source_fidelity': sources}
(BASE / 'content-validation.json').write_text(json.dumps(content, indent=2) + '\n', encoding='utf-8')
print(json.dumps(content, indent=2))
