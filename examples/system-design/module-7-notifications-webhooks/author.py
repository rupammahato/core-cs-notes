"""Author S2 with exact runnable mechanisms and recorded local observations."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
sources = ['estimates.py', 'delivery.py', 'protocol.py', 'worker.py']
outputs = ['estimates', 'intake', 'concurrency', 'leases', 'retry', 'http_contract', 'lost_ack_and_ordering']


def code(name):
    return '```python\n'+(BASE/name).read_text(encoding='utf-8')+'```'


def output(name):
    return '```json\n'+json.dumps(proof['observations'][name], ensure_ascii=False, indent=2)+'\n```'


chapter = r'''# Architecture and System Design Placement Handbook — Part 9
# S2: Notification and Webhook Delivery Service

**Estimated time: 4–5 hours | Architecture numeric module: 7 | Requires: A0–A4 and S1; Resume M9/M15 refreshers**

---

## Why this module exists

“Send a notification” becomes a system-design question when one event has several destinations, recipients change preferences, providers throttle, and workers stop after a remote receiver has already committed its work. A successful HTTP response is also different from an email reaching an inbox or a person reading a message.

This chapter designs the event-to-delivery workflow and implements its defining failure boundary: a durable SQLite fan-out/lease queue sends signed HTTP to an owned loopback receiver. That receiver commits a local effect, then deliberately closes the socket without acknowledging. The sender retries with the same delivery identity; the receiver acknowledges again without repeating its effect.

**Organizing principle: persist notification intent, track each destination separately, retry ambiguous attempts, and deduplicate effects where they commit.**

The architecture covers email, SMS, push and customer webhooks. The executable adapter is a custom lesson webhook protocol, not SMTP, a vendor SDK or a real customer notification. It uses public fixture secrets and controlled clocks. No external messages, accounts, Docker, Redis or existing database services are involved.

The 30 Q&As are curated interview practice, not a measured employer-frequency ranking. This chapter addresses architecture bank Q27 and Q41, extending [A3's workflow foundations](/docs/system-design/reliable-workflows-concurrency) and [S1's quota reasoning](/docs/system-design/rate-limiter). S7 will later generalize scheduling/worker infrastructure.

---

## 1. Prompt and clarification questions

**Prompt:** an application generates placement-practice reminders. Deliver optional reminders through subscribed channels and support customer webhook endpoints. Persist acceptance, expose destination status, tolerate transient provider failures and prevent a repeated webhook attempt from repeating the receiver's local effect.

| Clarification | Consequence for the design |
| --- | --- |
| Transactional/security or optional marketing/reminder traffic? | Consent, unsubscribe rules, priority and legal/product policy |
| Which channels and what does “delivered” mean? | Adapter contract, provider callbacks and user-read semantics |
| Fan-out to a few subscriptions or millions of recipients? | Inline materialization versus resumable batch fan-out |
| Best effort or a bounded retry/delivery objective? | Attempt limits, expiration, retention and escalation |
| Do preferences apply at acceptance or dispatch? | Snapshot versus latest-consent behavior and in-flight races |
| Does event ordering matter per account/resource? | Sequence numbers, partitions, blocking and reconciliation |
| Can a customer configure arbitrary webhook URLs? | Ownership verification, SSRF-aware outbound boundary and secret management |
| Which provider limits and outage isolation are required? | Shared quotas, cooldowns, concurrency and channel/provider queues |
| What is the duplicate business-effect identity? | Event/delivery IDs versus domain-specific operation dedupe |
| What can tenants inspect, replay or change? | Scoped status APIs, audited administration and immutable attempts |

Do not silently make every notification mandatory to bypass opt-out. This fixture treats all `practice.reminder` events as optional and uses an enabled subscription as its preference. Mandatory/security traffic would require a separate stated policy.

---

## 2. Scope, promises and invariants

| Area | Executed baseline |
| --- | --- |
| Acceptance | Validated event plus all currently enabled subscription deliveries in one transaction |
| Replay | Stable `(tenant,event_id)` and exact canonical event bytes; changed content conflicts |
| Fan-out | At most eight configured subscriptions per tenant; retry does not add new subscribers |
| Destination | Immutable configured endpoint identifier, resolved by trusted `(tenant,endpoint)` registry |
| Preferences | Disabled at acceptance excluded; disabled before claim becomes skipped |
| Attempts | Durable claim recorded before HTTP; maximum three claims, including expired/crashed claims |
| Ownership | Lease plus fresh fencing token; expired/stale completion cannot update sender state |
| Retry | Unknown transport, 408, 429 and 5xx; bounded exponential full jitter; selected Retry-After format |
| Terminal state | `succeeded` means endpoint accepted; `failed` and `skipped` retained for inspection |
| Receiver | Raw-body HMAC/time validation, scoped delivery receipt and local effect in one transaction |
| Exclusions | External channel delivery, public ingestion/admin API, arbitrary URL registration, live secret rotation, broker, automated redrive, strict ordering, production TLS/auth and load benchmark |

The invariants:

- An accepted new event cannot leave only part of its chosen fan-out committed.
- Equivalent event retries cannot create another logical delivery for the same subscription.
- Only one unexpired claim owns a delivery's sender-state transition.
- A stale worker cannot overwrite a newer worker's result; its external request may still have happened.
- Repeated authenticated deliveries with the same scoped identity cannot repeat the receiver's demonstrated transactional effect.
- A known provider rejection, an unknown transport result and endpoint acceptance remain distinguishable.
- Tenant scope applies to event replay, status lookup, routing configuration and cooldowns.

Bounded attempts mean eventual delivery is not guaranteed. “At least once” describes why retries can repeat requests, not a promise that every accepted event must reach a receiver despite permanent failure or exhausted retries.

---

## 3. Estimate fan-out, retries, backlog and storage

Assume 100,000 events/day, four destinations/event, and extra attempts equal to 10% of initial deliveries. The last input is an amplification assumption, not a claim that exactly 10% of recipients fail once. Outages can correlate failures and greatly increase amplification.

{{ESTIMATES_CODE}}

Calculated output:

{{ESTIMATES_OUTPUT}}

400,000 deliveries become 440,000 expected attempts under the selected assumption. Average throughput is about 5.093 attempts/second; the chosen 20× peak gives about 101.852. Multiplying by assumed mean attempt duration 0.2 seconds yields about 20.37 mean in-flight attempts at that peak model. This is a planning calculation, not a safe worker-pool setting: tails, provider concurrency limits, connection pools, retries and headroom matter.

An hour of outage at 100 new deliveries/second creates 360,000 pending deliveries. Recovering at 150/second while 100/second continue leaves only 50/second for the backlog, so drain takes two hours. Provisioning only enough capacity for ordinary arrivals does not clear an outage backlog.

Seven days of 1024-byte event payloads is about 0.7168 GB, excluding delivery rows, attempt history, indexes, envelopes, replicas and backups. Event bodies can be stored once and referenced by deliveries; avoid copying large payloads for every target unless the access/reliability tradeoff justifies it.

Separate incoming events, logical deliveries, actual attempts, provider acceptances and user outcomes in both estimates and metrics. They are not interchangeable units.

---

## 4. Event, notification, delivery and attempt are different records

| Concept | Identity and meaning |
| --- | --- |
| Domain event | Something occurred, such as a reminder becoming due; stable tenant/event identity |
| Notification intent | A policy decision to inform recipients, with category and content/template version |
| Logical delivery | One selected channel/destination for that intent; stable ID across transport retries |
| Attempt | One claimed execution/network attempt; separate number/token/time/outcome |
| Provider receipt | Provider-specific acceptance/message ID, if supported |
| User outcome | Inbox placement, device display or human read, with channel-specific evidence |

The fixture combines notification intent with one immutable event envelope and materializes webhook deliveries. The envelope includes version, tenant, event ID, event type and message. It deliberately omits unrelated personal information. A richer production envelope might reference a resource, template version, locale and audience while keeping secrets and large private documents out of the event.

The delivery ID remains stable across retries. The claim token changes on every claim and fences sender-state updates. The signature timestamp changes at send time; it is not the original event creation time. These identities serve different purposes and should not be collapsed into one random UUID.

Two distinct event IDs can still describe the same real business operation. Receipt dedupe alone cannot decide whether those events should share a business effect. Use domain constraints or an operation key when the product requires that guarantee, as discussed in [Resume M9](/docs/resume-skills/webhooks-payments-reliable-integrations).

---

## 5. API contracts and authority boundaries

These are proposed product HTTP APIs. The fixture executes the corresponding trusted Python queue methods and a real HTTP webhook receiver; it does not implement an ingestion, authentication, preference or administrative web server.

| Proposed API | Contract |
| --- | --- |
| `POST /v1/events` | Authenticate producer/tenant; validate bounded versioned envelope; 202 after durable acceptance; stable replay; 409 for changed event intent |
| `PUT /v1/me/preferences/:category/:channel` | Authenticate recipient/tenant; update consent under explicit policy |
| `GET /v1/deliveries/:id` | Tenant/ownership-scoped status and redacted attempt summary |
| `POST /v1/webhook-endpoints` | Authorize tenant admin; verify endpoint ownership and egress policy; generate secret securely |
| `POST /v1/deliveries/:id/redrive` | Authorized/audited reviewed replay with an explicit identity and retry-generation contract |
| Customer `POST /hooks/...` | Verify protocol-specific signature over exact bytes; durably accept/dedupe before acknowledgement |

202 at ingress means the service owns a durable intent, not that a provider or person received it. If the database commit fails, return an error so the producer can retry its stable event ID. If acceptance commits but the response is lost, replay returns the existing outcome without refanning out newly added subscriptions.

The tenant comes from authenticated producer context, not a body field that overrides credentials. The fixture's direct methods receive already trusted tenant/configuration arguments and validate shapes; they are not an authorization layer. Its receiver separately rejects a signed envelope whose tenant does not match the endpoint configuration.

---

## 6. Schema, indexes and smallest architecture

| Table | Authority and important access |
| --- | --- |
| `subscriptions` | Tenant/subscription primary key; immutable endpoint identifier and enabled preference |
| `events` | Tenant/event primary key; canonical immutable bytes for replay/fan-out |
| `deliveries` | Stable ID; unique tenant/event/subscription; status, due time, attempts and lease token |
| `attempts` | Delivery/number primary key; claim token, start and observed outcome |
| `cooldowns` | Tenant/endpoint primary key; shared “not before” time after 429 |
| Receiver `receipts` | Endpoint/delivery primary key plus payload digest |
| Receiver `effects` | Demonstrated local application effect; same transaction as its receipt |

```mermaid
flowchart LR
    Producer[Authenticated event producer] --> Intake[Validate and choose subscriptions]
    Intake --> DB[(Events and delivery queue)]
    DB --> Worker[Claim with lease and token]
    Worker --> Adapter[Bounded channel adapter]
    Adapter --> Receiver[Customer webhook receiver]
    Receiver --> Inbox[(Receipt and local effect)]
    Worker -->|accept, retry or fail| DB
    Pref[Preference changes] --> DB
```

Start with one database-backed queue when it meets requirements. The due-state index supports selection, but the simple OR predicate, cleanup updates and file-wide SQLite writer lock need measurement; they do not prove scalable scheduling. HTTP is outside the queue transaction, so a slow receiver does not hold its write transaction during network work.

No broker is required for this baseline. If a separate application database generates events, its business update and publication still have a dual-write gap. Write an outbox row in that application's transaction and relay with stable IDs. The fixture atomically persists accepted event plus fan-out within its own database; it does not execute a cross-database domain outbox bridge.

---

## 7. Durable acceptance, fan-out and preference implementation

The queue implementation includes the complete acceptance, claim and completion boundaries:

{{DELIVERY_CODE}}

The eight-subscription cap bounds fixture fan-out. A 256-event retention cap rejects new events instead of deleting replay identity prematurely; existing replay still works at capacity. This is an intentionally finite lesson store, not a retention service or production capacity setting. Trusted subscription configuration is not globally cardinality-bounded by these event limits.

Observed intake evidence:

{{INTAKE_OUTPUT}}

The suite injects a database trigger failure during fan-out and verifies that both the event and any inserted delivery roll back. It also closes/reopens the database, retries equivalent input, changes content under the same event ID and queries status under another tenant.

For million-recipient broadcasts, do not hold one giant transaction to insert every target. Persist the event plus a resumable fan-out job, page the audience under a stated snapshot/latest policy, store a cursor and keep a unique delivery key. Recovery must not skip a page or duplicate logical deliveries. That is a justified extension, not an implemented feature of this small fan-out.

---

## 8. Claim leases, stale workers and crash windows

The sender state machine is:

```text
pending --due and enabled--> inflight(token, lease, attempt recorded)
inflight --2xx before lease expiry--> succeeded
inflight --retryable and attempts remain--> pending(new due time)
inflight --permanent or exhausted--> failed
pending / expired inflight --disabled preference--> skipped
expired inflight --attempts remain--> inflight(new token, next attempt)
```

`BEGIN IMMEDIATE` serializes competing claim transactions. A claim increments the attempt count and records an attempt before HTTP. At lease equality, the old owner is expired; completion requires the current token and an unexpired lease. Expired claims consume the attempt budget, including a crash before the network call actually started. [SQLite transaction semantics](https://sqlite.org/lang_transaction.html).

Observed competing producers/workers:

{{CONCURRENCY_OUTPUT}}

Two thread-owned connections race on equivalent event creation: one creates and one replays. Two more race to claim the one delivery: only one gets a live claim. These are local independent connections, not deployed hosts or a distributed lock service.

Observed lease and preference boundaries:

{{LEASES_OUTPUT}}

Lease fencing protects sender database state. It cannot stop a worker whose HTTP request is already in flight or undo an effect at the receiver. A recovered worker may send the same delivery again. The receiver's stable identity and atomic effect boundary are what handle that repetition.

Choose a lease with network deadline, expected execution and scheduling margin in mind; long work may require safe renewal. The fixture uses controlled milliseconds, a 2000 ms default lease and a 250 ms local connection/socket timeout. It does not implement renewal, a distributed time authority or a hard total network deadline under arbitrary trickling traffic.

---

## 9. Retries, provider cooldowns and terminal inspection

| Observed outcome | Selected policy |
| --- | --- |
| 2xx | Endpoint accepted; sender marks succeeded |
| No HTTP status / network exception | Unknown outcome; retry if budget remains |
| 408, 429, 5xx | Retry if budget remains |
| Redirect or other 4xx | Permanent failure under this lesson contract |
| Third retryable failure or expired third claim | Failed; retain history for operator inspection |
| 429 | Also update shared tenant/endpoint cooldown using the selected delay |

This status classification is an authored webhook contract, not a universal provider policy. A provider may require different treatment for 409, authentication errors, disabled endpoints or idempotency conflicts. Use its documented semantics rather than copying one list everywhere.

Backoff cap is `min(8000, 500 × 2^(attempt_number−1))` milliseconds. A production-style draw is uniform from zero through that cap; deterministic tests supply selected values. Zero is a valid full-jitter draw, so backoff is not a minimum-spacing guarantee. Due time is completion time plus the maximum of the chosen jitter and accepted Retry-After.

The adapter supports decimal Retry-After delay-seconds up to one day; invalid/unsupported hints fall back to backoff. It does not parse HTTP-date. A general HTTP adapter must deliberately support required formats and scheduling horizon. Retry-After's standard syntax is broader than this selected fixture subset. [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after).

Observed retry/cooldown evidence:

{{RETRY_OUTPUT}}

A 429 cooldown applies to all later claims for that tenant/endpoint, not just the delivery that received it. Another endpoint or tenant can continue. Already claimed requests can still be in flight. This reactive cooldown is not a proactive shared rate limiter; provider-wide quota admission can use [S1's atomic budget](/docs/system-design/rate-limiter).

Retries can amplify an outage. Bound attempts and work age, use jitter, avoid retrying at every layer and reserve recovery capacity. AWS's retry guidance motivates these mechanisms; the exact numbers here are teaching choices. [AWS timeouts, retries and jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/).

The fixture's retained `failed` rows serve as a dead-letter state; no separate broker DLQ or automatic redrive exists. A real redrive operation needs authorization, audit, reason, retry generation, original identity semantics and rate controls. Resetting an attempt counter without preserving history obscures what happened.

---

## 10. Channel adapters and what success means

| Channel | Adapter-specific work | Acceptance is different from |
| --- | --- | --- |
| Email | Versioned template/locale, validated destination, provider API/SMTP, bounce/complaint callbacks | Inbox placement or human read |
| SMS | Verified number, consent/category, cost budget, provider receipt and delivery reports | A person seeing the message |
| Push | Device tokens, invalid-token retirement, platform payload/TTL, per-device fan-out | Device display or application read |
| Customer webhook | Endpoint ownership, signed bytes, bounded HTTP, retry identity, receiver dedupe | Customer's entire downstream workflow completing |

Keep channel workers separate when their failure rates, latency, provider limits or priorities differ. A slow webhook should not exhaust every thread needed for security email. Start with a modular adapter boundary; separate queues/pools or services only when the operational need justifies them.

Store the chosen template and rendering/version policy for audit and retries. Re-rendering an old notification with a changed template or mutable profile can change its meaning. Snapshotting everything also retains private data, so choose minimal immutable inputs, access controls and deletion/retention policy deliberately.

Provider message IDs and callbacks can refine delivery state, but callbacks themselves need authentication, dedupe and monotonic state rules. A late “queued” callback should not overwrite a later accepted failure/success observation blindly. Exactly which states are comparable depends on the channel/provider contract.

Only the webhook adapter below executes. No email, SMS, push, bounce callback, template engine, mandatory-message policy or real provider account is simulated as if it were integrated.

---

## 11. Raw-body HMAC and transactional receiver implementation

The custom lesson signature authenticates:

```text
decimal_timestamp_seconds + "." + stable_delivery_id + "." + exact_raw_body_bytes
HMAC-SHA256 with the endpoint's configured secret
```

Headers are `X-Lesson-Timestamp`, `X-Lesson-Delivery` and `X-Lesson-Signature`. The timestamp tolerance is ±30 seconds, including equality. It limits the replay time window but does not deduplicate repeats within that window. Persistent receipt identity handles those repeats.

GitHub documents HMAC validation and timing-safe comparison; Stripe documents raw-byte validation, duplicate events and lack of ordering. Their protocols and delivery policies differ. Use the provider's SDK/contract for a real integration; these custom headers are compatible with neither vendor. [GitHub signature validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries), [Stripe webhooks](https://docs.stripe.com/webhooks).

{{PROTOCOL_CODE}}

The receiver verifies raw bytes before JSON schema/effect processing, checks the configured tenant and then atomically writes receipt plus local effect. It stores a digest to reject the same delivery ID with changed content. For simplicity, this fixture also requires its own canonical envelope encoding; that is an application schema choice, not a general rule that signed JSON must be canonicalized before verification.

An injected effect-insert failure proves that its receipt rolls back too. Marking the receipt processed in a separate transaction before the effect would suppress a legitimate retry after failure. Writing the effect first and the receipt later would leave a duplicate-effect gap.

The demonstrated effect is a local SQLite record. For a remote payment, email or other external effect, the receiver needs that system's idempotency/transaction protocol or another durable intent/reconciliation boundary. A local receipt cannot atomically wrap arbitrary external actions.

---

## 12. Bounded HTTP sender implementation

{{WORKER_CODE}}

The trusted registry is indexed by tenant and endpoint. It resolves only to an owned `127.0.0.1` listener and configured `/hooks/` path; it is not an arbitrary URL fetcher. `http.client` does not automatically follow redirects, and the selected response policy treats them as permanent failures. The receiver sends an empty response body; the sender does not buffer an arbitrary response body.

Production-style jitter uses `secrets.randbelow`; tests inject values to make due times reproducible. `run_once` receives a controlled start time and optional completion-time callback; its default completion time equals the supplied fixture time. A real runner must supply current authoritative completion time, poll/schedule continuously, supervise workers and manage lease/deadline budgets. None of those services is silently running after verification.

Unknown transport is intentionally not reported as “not delivered.” The remote effect may already have committed. The sender records ambiguity and retries the same stable logical delivery identity with a newly signed timestamp.

---

## 13. End-to-end lost-acknowledgement trace

1. The producer commits an event and one pending delivery.
2. The worker commits claim/attempt one, then signs and sends the delivery.
3. The receiver validates the signature and commits receipt plus effect.
4. The receiver closes the real socket before sending an HTTP status.
5. The sender observes an unknown transport outcome and schedules a retry.
6. At the due time, attempt two sends the same delivery ID and unchanged bytes.
7. The receiver finds the matching receipt, applies no new effect and returns 200.
8. The sender commits succeeded with both attempt outcomes retained.

Observed evidence:

{{LOST_ACK_AND_ORDERING_OUTPUT}}

This is an actual loopback connection close after receiver commit, not a fabricated successful return value. It demonstrates why transport acknowledgement and effect commit are separate events. It does not prove universal exactly-once delivery or machine-crash durability.

The same observation also shows independent event reordering: an earlier event gets 503 and waits; a later event succeeds first. The system does not advertise strict event order. Retrying until success while allowing later events to proceed naturally changes arrival order.

---

## 14. Preferences, ordering, retention and replay boundaries

Preference checks at acceptance avoid creating work for already disabled subscriptions. Checks before claim suppress queued optional reminders after opt-out. An opt-out that races after claim may be too late for an in-flight request. Stronger revocation would require another boundary and still cannot retract a message already accepted externally.

Skipped deliveries stay skipped after re-enable. An old event retry does not refan out to a newly created subscription. These choices make original intent replay stable. If the product wants “send the current reminder to all current subscribers,” that should be a new explicit command rather than an accidental side effect of transport retries.

For ordered state updates, choose an aggregate/resource key and monotonic version or sequence. A consumer can ignore stale versions, wait for gaps or reconcile against authoritative state. Strict per-key ordering can block later messages behind a poison event. Global ordering usually adds unnecessary coordination. The fixture's independent reminder records need no ordered state transition.

Keep receipt/dedupe identity at least as long as allowed retries/redrives and the relevant business replay risk. Deleting a receipt while old messages can return can repeat the effect. Keeping it forever has privacy/storage costs; retaining a minimal identity/digest may serve a different policy from retaining full message text.

This lesson retains rows within a small event cap and has no deletion, automated retention, data-subject workflow or redrive API. Close/reopen proves file-backed application replay, not disk-loss, power-failure or backup-restore guarantees. Lease and signature behavior also depend on the chosen server clocks; distributed clock skew is not implemented.

---

## 15. Security, endpoint registration and tenant isolation

| Risk | Design response |
| --- | --- |
| Forged producer/tenant or status lookup | Authenticate producer/recipient; derive tenant; scope every query and registry lookup |
| Arbitrary webhook URL reaches internal services | Ownership verification plus SSRF-aware egress boundary; no arbitrary URLs in this fixture |
| Signed bytes changed by JSON middleware | Capture and verify exact bytes before parsing |
| Replayed valid request | Timestamp policy plus durable scoped receipt/effect dedupe |
| Secret leakage or rotation | Secret manager, per-endpoint keys, key IDs/overlap policy, redacted logs; live rotation is not implemented |
| Large/slow receiver traffic | Input/response bounds, connection and total deadlines, concurrency and egress limits |
| Abusive tenant or replay storm | Event/fan-out quotas, provider budget, bounded retries and audited redrive |
| Private notification data retained everywhere | Minimal payload, scoped access and deliberate retention/deletion |

A public endpoint-registration API must validate more than the URL string. Consider protocol/port policy, DNS resolution and rebinding, private/link-local/metadata address ranges, redirects, network egress controls and revalidation at connection time. A production outbound proxy can enforce a common policy. The local registry sidesteps this boundary rather than claiming to solve general URL safety. [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

Subscription configuration is trusted administration in the fixture. Its method validates identity and target immutability but does not authenticate an admin or verify endpoint ownership. The public demo secrets are intentionally unsuitable for real messages. Production HTTPS remains necessary even with HMAC: signing authenticates selected content, not confidentiality.

Observed HTTP validation/transaction evidence:

{{HTTP_CONTRACT_OUTPUT}}

The 4096-byte declared-length limit is enforced before reading an oversized body. The tiny standard-library server is not hardened against hostile slow clients. Invalid framing/oversized uploads may terminate a connection; the tests check the bounded declared-length rejection without sending an unread oversized stream.

---

## 16. Growth stages, operations and meaningful metrics

| Trigger | Change to justify | Contract or measurement to preserve |
| --- | --- | --- |
| Small bounded fan-out | One transactional database queue | Acceptance/replay and complete fan-out are durable together |
| Huge audience | Resumable batched fan-out | Stable audience policy, cursor recovery and unique delivery key |
| More workers/lock contention | Engine-specific row claims or broker-backed dispatch | Claim/ack/lease behavior, dedupe and due scheduling tested on that engine |
| Provider outage harms other channels | Separate queue/pool/provider budgets | Fairness, concurrency, backlog and failure isolation |
| High retry traffic | Shared quota, circuit breaker and recovery budget | Avoid retry amplification; do not discard durable intent silently |
| Multi-region | Explicit delivery owner/routing/failover | Prevent independent active owners from creating uncontrolled duplicates |
| Slow history queries | Separate reporting/read model | Authoritative delivery transitions remain correct and access scoped |

Moving to a broker introduces publication, acknowledgement and redelivery boundaries. Use a transactional outbox/relay where necessary and treat broker ack as its own event. A broker does not remove the post-effect/pre-ack crash window. PostgreSQL row locking or Redis/SQS leases also need their own tested semantics; the SQLite example is not a substitute for those tests.

Measure acceptance rate, fan-out amplification, pending depth and oldest due age, attempts/delivery, time-to-first-attempt, time-to-endpoint-acceptance, permanent failures, unknown outcomes, expired leases, stale completions, skipped preferences, receiver duplicates, provider 429/latency and cooldown time. Separate accepted, succeeded, delivered and read in dashboards.

Use bounded labels such as channel, provider, route and outcome class. Do not create one metric label for every recipient, URL or delivery ID. Put sensitive correlation IDs in access-controlled logs/traces with retention rather than logging payloads and secrets indiscriminately.

Define an SLO at a boundary you can observe, for example “eligible accepted webhook deliveries receive endpoint acceptance within five minutes under the selected availability assumptions.” Specify exclusions and failures honestly. No such production SLO is measured by this fixture.

---

## 17. Reproduce and interpret the verification

From the repository root:

```powershell
cd examples/system-design/module-7-notifications-webhooks
python verify.py
python author.py
python integrate.py
python validate_site.py
```

Recorded runtime: **Python {{PYTHON}}**, **SQLite {{SQLITE}}**, **{{OS}}**, on **{{DATE}}**. **{{TOTAL}} local checks passed**: {{COUNTS}}. Four queue worker calls use separate thread-owned connections; two additional concurrent HTTP requests verify receiver effect dedupe.

The suite covers event/fan-out rollback, original-intent replay, tenant lookup, real competing claims, lease equality, stale completion, crashed attempt exhaustion, opt-out, retry classification, shared cooldown, signed raw Unicode bytes, timestamp bounds, receiver transaction rollback, actual socket loss after commit, duplicate effects and event reordering.

`verification-results.json` records each named assertion. This chapter embeds four exact sources and seven exact calculated/observed outputs. `content-validation.json` checks learning structure and source fidelity; `validation-summary.json` records site build, routes/search and cleanup.

All local SQLite connections/listeners are closed, serving/handler/worker threads joined and the owned temporary directory removed. Port 3000 and Docker remain stopped. There is no persistent sender/receiver service, external provider call or message sent to another person. The prototype does not claim machine-crash recovery, production throughput, vendor interoperability or universal exactly-once delivery.

---

## 18. Interview question bank with answer direction

### Q1. What is a notification service responsible for?

It turns accepted domain intent into eligible per-channel deliveries, schedules attempts, handles provider outcomes and exposes meaningful status. Product policy includes category, consent, content and priority; transport code alone is not the full service.

### Q2. How is a webhook different from email or push?

A webhook calls a customer-controlled HTTP endpoint and requires endpoint ownership, signing, bounded outbound requests and receiver dedupe. Email/push have different destination identities, provider receipts and user-outcome evidence. They can share workflow infrastructure while retaining separate adapter contracts.

### Q3. Why distinguish event, delivery and attempt IDs?

An event may fan out to many targets, and one target may require several attempts. Stable event identity deduplicates intake; stable delivery identity groups retries; attempt number/token identifies one execution and fences state updates.

### Q4. When should the ingestion API return 202?

After the service durably owns the accepted intent and its required fan-out/job boundary. It does not mean delivery completed. A lost acceptance response must be recoverable through the producer's stable event identity.

### Q5. How do you prevent partial fan-out?

For small fan-out, commit event plus all chosen delivery rows in one transaction. For huge audiences, commit event plus a resumable fan-out job and use cursor recovery with unique delivery identity. Do not attempt an unbounded transaction without considering load and recovery.

### Q6. What if the producer retries after a timeout?

Compare the same scoped event ID with its immutable accepted content. Equivalent retry replays the original intent; changed content conflicts. Newly added subscriptions do not silently alter an old acceptance in this fixture.

### Q7. Should preference changes affect already queued messages?

Choose and document the policy. Here disabled subscriptions are excluded at acceptance and rechecked before claim; pending work becomes skipped. A change after claim may race with external acceptance, and re-enable does not revive skipped work.

### Q8. Where does the transactional outbox fit?

It connects a domain database update to eventual publication without a dual-write gap: write business state and outbox locally, then relay with stable identity. It does not atomically include an arbitrary remote provider effect.

### Q9. How do workers avoid claiming the same delivery?

Use an authority-side atomic claim with state/lease update and attempt record. The local fixture serializes the whole write transaction. Other engines need their own row-lock, visibility/lease or broker-ack tests.

### Q10. What does a fencing token protect?

It prevents an old owner from changing the sender's state after ownership changed. It cannot stop an already sent network request or undo receiver work. External effect dedupe remains necessary.

### Q11. A worker dies before sending. Should it count as an attempt?

The fixture counts every durable claim, including a crash before I/O. This bounds recovery loops but can exhaust attempts without three actual sends. Another policy needs a defensible definition of start/attempt and crash accounting.

### Q12. A receiver commits, but the sender times out. What happens?

The sender has an unknown outcome and retries the same logical delivery. The receiver checks its persistent scoped receipt and repeats acknowledgement without repeating the transactional effect. The fixture reproduces this with a real connection close before any status.

### Q13. Where must dedupe and the business effect commit?

At the effect authority in one transaction when both are local. Separating “processed” from the effect creates a loss or duplicate window. An external effect requires that external system's idempotency protocol or another durable intent/reconciliation design.

### Q14. Is HMAC enough to prevent duplicate processing?

No. A valid signed request can repeat within its allowed time window. HMAC authenticates bytes; timestamp policy limits age; durable identity/effect constraints suppress repeated effects. None alone replaces the others.

### Q15. Why verify the raw body before parsing JSON?

Serialization changes whitespace, key order or Unicode representation and therefore changes signed bytes. Capture the raw body, verify using the actual provider protocol, then parse/validate. This fixture's later canonical-envelope check is an additional lesson schema rule.

### Q16. Which statuses should be retried?

Use the adapter/provider contract. This lesson retries unknown transport, 408, 429 and 5xx, while redirects/other 4xx are permanent. A provider-specific conflict or authentication response may need different operational handling.

### Q17. Why exponential backoff with jitter?

Backoff spreads repeated pressure; jitter avoids synchronized clients retrying together. Bound attempts, deadlines and scheduling horizon too. Full jitter can draw zero, so it is not a strict minimum-spacing or provider-quota guarantee.

### Q18. How does Retry-After affect scheduling?

Use the accepted provider hint as a not-before floor relative to completion time, combined with your backoff policy. State supported formats and maximum horizon. The fixture handles decimal delay-seconds, not all valid HTTP-date forms.

### Q19. Should 429 delay only the failed delivery?

Often the limit applies to a shared endpoint/account/provider budget. This fixture updates a tenant/endpoint cooldown that blocks later claims for that scope. Already in-flight requests may proceed; proactive quota admission is a separate mechanism.

### Q20. What is a dead-letter queue for?

It retains terminal/problematic work with enough reason/history for diagnosis and controlled recovery. It should not be an invisible deletion bucket or an automatic infinite retry loop. The fixture uses retained failed rows, not a separate broker service.

### Q21. How should manual redrive work?

Authorize and audit it, preserve original history and define whether identity remains the same or represents new intent. Respect current preferences, payload/secret policy, rate limits and retry budget. Do not blindly reset counters or erase dedupe records.

### Q22. Does the service guarantee event order?

This baseline does not; retries let later independent events arrive first. If resource transitions require order, use an aggregate key plus version/sequence and explicit stale/gap handling. Strict ordering may block on poison events.

### Q23. What does a 200 or 202 from an email/webhook provider prove?

Only the documented acceptance boundary. It may not prove inbox placement, device display, a human read or completion of a customer's later jobs. Name those outcomes separately in status and metrics.

### Q24. How do you isolate a failing channel/provider?

Separate concurrency, quotas and scheduling pools when the failure/priority needs justify it. Monitor backlog age by class and retain durable work. A single unlimited pool lets slow webhooks consume capacity needed by other channels.

### Q25. What makes public webhook endpoint registration risky?

It creates an outbound request capability that can reach internal/metadata services or follow unsafe redirects. Verify ownership and enforce DNS/address/port/protocol/egress policy at the connection boundary. String URL validation alone is insufficient.

### Q26. How do secret rotation and retries interact?

Old queued attempts must have a clear signing policy; receivers may need a bounded key-overlap window and key IDs. Re-sign each attempt with a fresh send timestamp without changing its delivery identity. The fixture deliberately leaves live rotation unimplemented.

### Q27. When may dedupe receipts be deleted?

Only under a retention policy consistent with retry/redrive and business replay risk. Old messages can repeat effects if receipts disappear too early. Minimize retained data while preserving the identity/constraints needed for the chosen guarantee.

### Q28. How do you calculate outage recovery capacity?

Backlog grows at arrivals minus successful service. During recovery, only capacity above continuing arrivals drains it. The example's 360,000 backlog at net 50/second takes 7200 seconds; ordinary steady-state capacity alone cannot clear it.

### Q29. What measurements matter most?

Oldest due age, time to endpoint acceptance, attempts/delivery, terminal failures, unknown outcomes, lease expiry/stale completion, provider latency/429 and preference skips. Separate tenant debugging from bounded aggregate metric labels and avoid logging secrets/payloads.

### Q30. What do the runnable checks prove and what remains unproven?

They prove the recorded local transaction, race, lease, retry, signature and loopback failure behavior. They do not prove external channel delivery, vendor interoperability, machine-crash/failover durability, global timing, production authentication or capacity at the hypothetical peak.

---

## 19. A 45-minute mock and answer skeleton

**Mock prompt:** “Design notifications and customer webhooks for a multi-tenant application. Recipients can opt out, providers throttle and a worker may stop after the customer has already processed a request.”

| Segment | Minutes |
| --- | --- |
| Clarify categories, channels, outcomes and consent | 5 |
| Estimate fan-out, attempt amplification and backlog | 7 |
| Specify identities, APIs, schema and acceptance boundary | 8 |
| Trace claim, signed delivery, acknowledgement and retry | 10 |
| Inject duplicate effect, worker crash, opt-out and 429 | 10 |
| Justify growth, metrics and evidence limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I would durably accept a stable tenant-scoped event and create per-destination delivery intents, with preferences and content versioning defined explicitly. Workers atomically claim due work with a lease and fencing token, then perform bounded channel I/O outside the database transaction. Unknown outcomes retry the same delivery identity with bounded jitter and provider-aware scheduling. A customer receiver verifies exact signed bytes and atomically stores receipt plus local effect, because the remote effect can commit before its acknowledgement reaches us. Success means the documented acceptance boundary, not a human read. I would add separate pools, batched fan-out or a broker only when measured needs justify the added failure boundaries.

Use bank Q27/Q41 to test the post-effect/pre-ack gap. Explain why a broker, HMAC, worker lock or HTTP 200 alone cannot establish a universal exactly-once business outcome.

---

## 20. Practice tasks

1. Clarify optional versus transactional traffic and define accepted, provider-accepted, delivered and read for each channel. Identify the preference owner and in-flight race.
2. Recompute deliveries, retry amplification, mean in-flight work and backlog drain for another workload. Explain why a mean calculation is not a safe concurrency setting.
3. Inject fan-out failure and inspect the rollback. Retry the same event before/after a new subscription, change its payload and explain original-intent replay.
4. Run the competing producer and claim races. Trace the unique keys and transaction that prevent duplicate intent and simultaneous live ownership.
5. Advance to just before/at lease expiry, reclaim, and attempt a stale completion. Explain what is fenced locally and why external effects still need dedupe.
6. Exercise opt-out, skipped state, re-enable and the race after claim. Propose a different product contract and the affected consistency boundary.
7. Observe actual socket loss after receiver commit, then retry. Inspect both attempt outcomes and the single receipt/effect transaction; repeat with an injected effect-insert failure.
8. Tamper with raw bytes, delivery identity, tenant and timestamp. Explain signature validation, replay tolerance, durable dedupe and the custom protocol's vendor incompatibility.
9. Exercise 429 cooldown, independent endpoint progress, transient failure exhaustion and event reordering. Propose scoped provider quotas, ordered-resource handling and audited redrive without claiming they are implemented.
10. Complete the 45-minute mock. Extend to huge fan-out or email/SMS/push adapters, marking new API, provider, consent, security, retention and verification requirements.

---

## 21. Completion checklist

- [ ] I can clarify channel, category, consent and success boundary.
- [ ] I can estimate fan-out, retries, in-flight work and backlog drain.
- [ ] I can distinguish event, delivery, attempt and effect identity.
- [ ] I can explain durable acceptance and original-intent replay.
- [ ] I can reproduce fan-out rollback and competing claim results.
- [ ] I can explain lease expiry, fencing and crash attempt budgets.
- [ ] I can explain preference checks and in-flight opt-out limits.
- [ ] I can trace unknown outcomes and receiver transactional dedupe.
- [ ] I can verify raw-body signatures and explain replay tolerance.
- [ ] I can explain provider cooldowns, terminal states and ordering tradeoffs.
- [ ] I can justify endpoint security, retention and channel isolation.
- [ ] I can finish the mock and state the local evidence limits.

---

## 22. Research references and continuation

Primary sources reviewed on {{DATE}}. Code, workload assumptions, outputs and Q&As are authored examples. Provider policies differ; this lesson does not claim its protocol, retry count or status list is a vendor implementation or a measured interview-frequency ranking.

| Primary source | Relevant mechanism |
| --- | --- |
| [Stripe webhooks](https://docs.stripe.com/webhooks) | Raw-body verification, duplicate events, asynchronous handling and ordering limits |
| [GitHub signature validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries) | HMAC and timing-safe comparison |
| [GitHub webhook practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks) | Prompt acknowledgement, queues and delivery identifiers |
| [AWS retries and jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Timeout budgets and retry amplification |
| [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after) | HTTP acknowledgement and Retry-After semantics |
| [SQLite transactions](https://sqlite.org/lang_transaction.html) | Local transaction/write-ownership boundaries |
| [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) | Outbound endpoint/DNS/address/redirect boundary |

Return to the [architecture roadmap](/docs/system-design), [A3: reliable workflows](/docs/system-design/reliable-workflows-concurrency), [A4: operations](/docs/system-design/secure-observable-operations) or [S1: rate limiter](/docs/system-design/rate-limiter). Resume [M9: webhooks/payments](/docs/resume-skills/webhooks-payments-reliable-integrations) and [M15: caching/background work](/docs/resume-skills/caching-background-jobs-data-ingestion) provide stack refreshers.

**Next: [S3 — File upload, storage and processing service](/docs/system-design/file-upload-processing)**, architecture part 10 / numeric module 8. It develops metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup, with its own immutable local-file/SQLite/HTTP verification scope. S0-S3 are authored; remaining worked systems and architecture consolidation continue one section at a time.
'''

for name, tag in [('estimates.py','ESTIMATES'), ('delivery.py','DELIVERY'),
                  ('protocol.py','PROTOCOL'), ('worker.py','WORKER')]:
    chapter = chapter.replace('{{'+tag+'_CODE}}', code(name))
for name in outputs:
    chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}', output(name))
for tag, value in [('DATE',proof['verified_date']), ('PYTHON',proof['python']),
    ('SQLITE',proof['sqlite']), ('OS',proof['os']), ('TOTAL',str(proof['total'])),
    ('COUNTS',', '.join(f"{n} {name.replace('_',' ')}" for name,n in proof['counts'].items()))]:
    chapter = chapter.replace('{{'+tag+'}}',value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-9-module-7-notifications-webhooks.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
metadata = {'label':'S2','chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),
    'questions':30,'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':sources,
    'output_fidelity':outputs,'mock_minutes':45,'verified_checks':proof['total'],
    'next':'S3: File upload, storage and processing service'}
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
