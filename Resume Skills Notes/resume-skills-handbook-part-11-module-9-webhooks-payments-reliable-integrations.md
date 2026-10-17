# Resume Skills Placement Handbook — Part 11
# Module 9: Webhooks, Payments and Reliable Integrations

**Module 9 · 4–5 hours · Tier 1 · Requires: M6-M8; DBMS transactions**

---

## Why this module matters

A payment integration is not complete when a browser displays success. Requests can time out after an effect commits, providers can deliver an event twice, callbacks can arrive out of order, and your process can stop between writes.

An interviewer can ask “How did you verify Razorpay?”, then follow with “What did you sign?”, “What if the same payment arrives under another event ID?” or “What prevents credits from being added twice after a restart?”

> **Treat integration messages as authenticated observations across a failure boundary. Bind them to trusted local state, make business effects transactional/idempotent, and preserve a recovery path.**

This module builds a small signed-webhook receiver with a durable inbox, transactional credit ledger and outbox. It uses local Razorpay-shaped fixtures rather than a real account.

**Verification:** **57 checks passed on Node.js v22.14.0 / SQLite 3.47.2**: 21 core checks, 26 real HTTP checks, six reconciliation-fixture checks and four file/process-recovery checks.

SQLite is accessed through the experimental node:sqlite API on this runtime. Its expected warnings are preserved separately. There are no extra npm dependencies or payment credentials.

### Run the examples

From the repository root:

```powershell
node examples/resume-skills/module-9-webhooks-payments/verify.mjs
node examples/resume-skills/module-9-webhooks-payments/verify-core.mjs
node examples/resume-skills/module-9-webhooks-payments/verify-http.mjs
node examples/resume-skills/module-9-webhooks-payments/verify-reconciliation.mjs
node examples/resume-skills/module-9-webhooks-payments/verify-recovery.mjs
```

Optional manual demo, using two terminals:

```powershell
# Terminal 1: creates/reuses the example's demo.sqlite and starts a local worker.
node examples/resume-skills/module-9-webhooks-payments/start.mjs

# Terminal 2: sends a fixed signed local fixture; repeat to observe deduplication.
node examples/resume-skills/module-9-webhooks-payments/send-fixture.mjs
node examples/resume-skills/module-9-webhooks-payments/inspect.mjs
```

The receiver binds **127.0.0.1:3109**. Ctrl+C stops it. The sender always targets that loopback address; it does not contact Razorpay or any other external account.

The manual database persists between runs so replay remains visible. The verifier uses isolated in-memory databases and newly created temporary file-backed fixtures, then closes/removes its own temporary resources.

Public fixture secrets, account IDs and payment IDs are teaching values. No real payment, refund, customer notification or provider-account action occurs.

---

## 9.1 What is a webhook?

A webhook is an HTTP request one system sends to another to notify it about an event. Your server becomes the receiver of a provider-initiated request.

| Interaction | Who initiates? | Typical purpose |
| --- | --- | --- |
| Ordinary API request | Your application/client | Create or fetch a resource |
| Polling | Your application repeatedly | Ask for current remote status |
| Webhook | Provider/event sender | Notify your server that something happened |
| Browser checkout callback | Browser/frontend SDK | Update local UI or initiate server verification |
| Reconciliation job | Your backend | Repair uncertain/missing/inconsistent observations |

A webhook is not a WebSocket. It is usually an independent HTTP request with its own authentication and retry policy.

### Webhook versus polling

Webhooks can reduce repeated reads and improve responsiveness, but delivery may be delayed, duplicated or exhausted after retries. Polling can help establish current state, but consumes requests and needs rate/deadline policy.

Use them together when the business requires recovery from missing notifications. A webhook can trigger work while a scheduled reconciliation process finds unresolved operations.

Razorpay documents asynchronous delivery, retries and duplicate events; its documented retry policy is provider-specific. Reference: [Razorpay webhook best practices](https://razorpay.com/docs/webhooks/best-practices/).

### Browser feedback is a separate boundary

A browser can close, lose connectivity or submit attacker-controlled values. Do not grant credits merely because the client reports success, sends an amount or names a payment ID.

The backend needs a trusted verification path and local mapping. The frontend can ask the backend for the application's confirmed order state under normal user/tenant authorization.

The runnable example focuses on the server-to-server receiver/worker. It does not implement a checkout UI or a user-facing order-status API.

---

## 9.2 Trace a payment integration before choosing SDK calls

A typical proposed checkout flow is:

```text
authenticated user chooses a product/credit pack
  -> backend reads authoritative price/currency/entitlement
  -> backend records a local payment intent/order snapshot
  -> backend creates/binds the provider order under configured credentials
  -> frontend opens provider checkout using allowed public data
  -> provider processes payment attempts

observations arrive independently:
  browser callback
  signed webhook
  backend provider-status lookup

backend applies trusted state + business invariants
  -> confirmed entitlement/credit state
```

The local order should snapshot the intended amount/currency and credit entitlement. A later catalog price change should not silently rewrite an existing order's contract.

Provider-order creation is itself an external operation with timeout ambiguity. Record an operation identity and determine the provider's actual retry/idempotency/reconciliation support. Do not assume every Razorpay endpoint inherits Stripe's Idempotency-Key behavior.

References: [Razorpay integration steps](https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/) and [Stripe's provider-specific idempotency contract](https://docs.stripe.com/api/idempotent_requests).

### Different identifiers mean different things

| Identifier | Scope/purpose |
| --- | --- |
| Local order ID | Your application's purchase intent |
| Provider order ID | Provider-side order associated with that intent |
| Payment ID | A particular payment attempt/resource |
| Provider event ID | One provider event observation |
| Delivery/attempt correlation | A particular HTTP delivery or retry |
| Inbox key | Your receiver's deduplication identity |
| Ledger business key | The effect that must not be granted twice |
| Outbox notification ID | Stable identity for a downstream message |

Several payment attempts can relate to one order. Several events can describe one payment. Several HTTP deliveries can carry one event.

This is why “we stored the event ID” is only part of an idempotency answer.

---

## 9.3 Verify the exact bytes

Razorpay documents a webhook signature using HMAC-SHA256 with the webhook secret and raw request body, supplied in X-Razorpay-Signature.

The body must remain unchanged for verification. Parsing JSON and serializing it again can change whitespace/property ordering and produce different bytes even when the values look equivalent.

Reference: [Razorpay webhook validation](https://razorpay.com/docs/webhooks/validate-test/).

```text
HTTP body bytes
  -> bounded raw buffer
  -> expected HMAC using configured webhook secret
  -> safe signature comparison
  -> parse supported JSON
  -> validate account/event/payment shape
  -> durable inbox
```

The verifier tests an independently published HMAC-SHA256 vector and an exact-body versus reserialized-body mismatch.

### HMAC is not encryption

Anyone possessing the webhook secret can produce a valid MAC. Keep production secrets out of frontend code/logs and separate test/live/provider-account contexts.

HMAC does not hide the body. TLS protects transport; storage/logging policies still matter.

The sample uses Node's crypto implementation, validates a 64-hex-character signature and compares equal-length byte buffers with timingSafeEqual. That comparison does not prove endpoint-wide timing indistinguishability.

### Provider schemes differ

Stripe's webhook signature scheme includes its own signed timestamp/header format and SDK verification behavior. Do not reuse a bare Razorpay HMAC recipe as a Stripe verifier.

Use the provider's maintained SDK or a carefully scoped implementation matching the exact documented scheme and version. Reference: [Stripe webhook handling](https://docs.stripe.com/webhooks).

### Express parser placement

For an Express adaptation, put the raw-body route before middleware that consumes/transforms the body. M5 already verified the distinction between raw bytes and parsed JSON.

```javascript
// Adaptation sketch, not the native-HTTP implementation verified in this module.
app.post('/webhooks/razorpay',
  express.raw({ type: 'application/json', limit: '16kb', inflate: false }),
  handlerThatVerifiesReqBodyBuffer);

app.use(express.json());
```

A JSON.stringify example is safe only if it actually reproduces the originally signed bytes, which a parsed object generally does not guarantee. Preserve the original supported byte/string input instead of guessing.

---

## 9.4 Signatures, replay, account binding and rotation

A valid signature authenticates message content under a configured secret. It does not by itself establish that a new business effect should occur.

### Replay is still possible

A previously valid signed body remains valid under the same secret. This Razorpay-style body-MAC example does not invent a signed delivery timestamp or reject older events based on a generic timestamp tolerance.

An event's creation time is not necessarily its latest delivery time. Legitimate retries/replays can be old. If a provider defines signed freshness checks, implement that provider's actual contract.

Durable event deduplication and business-effect keys remain necessary.

### The event-ID header has a separate trust property

The published body-HMAC construction signs the body, not arbitrary HTTP headers. Changing only X-Razorpay-Event-Id leaves that body signature valid.

The sample therefore has both a scoped inbox key and ledger/payment/order constraints. A captured body replayed under a new delivery ID can create another receipt, but cannot grant the same order credits twice.

The test explicitly changes that header and confirms one ledger grant. Do not claim that header deduplication alone prevents all replay.

### Bind the endpoint to the provider account

The configured endpoint determines its expected account and allowed webhook secrets. The signed account_id must match. The provider order is resolved under that same endpoint before deriving the local tenant/order.

X-Tenant-Id, payload notes and client-supplied credit counts do not select the beneficiary or entitlement.

Even an authenticated provider event can be inconsistent with your local order. Check amount, currency and immutable payment/order identity before granting.

### Secret rotation

The fixture permits an explicitly configured previous alpha secret to verify delayed deliveries. Removing it causes an old-signature request to fail.

Razorpay's validation guidance calls out older retries after secret changes. Define overlap/removal using the provider's real delivery history and your security requirements; there is no universal permanent “accept every old secret” policy.

If an old secret is compromised, retaining it preserves forgery capability. Rotation and incident recovery require an explicit operational decision.

---

## 9.5 Durable acceptance versus business completion

The receiver and worker have different responsibilities:

```text
receiver:
  authenticate/validate message
  commit durable receipt
  return 2xx acceptance

worker:
  load pending receipt
  validate trusted local mapping/invariants
  transactionally apply effect or record review outcome
```

The example returns **202 after inbox commit**. It has not promised that credits are already available.

Razorpay treats successful 2xx delivery as consumed for its retry protocol. After acknowledging, the application owns internal processing/recovery.

### Why not acknowledge before persistence?

If the process exits after sending success but before recording work, the provider may stop retrying while your application has forgotten the event.

A temporary Map or an unawaited Promise does not make acceptance durable.

### What if persistence fails?

The sample returns 503 and retains no receipt. A retry can later succeed.

If the inbox commits but the handler fails before the successful acknowledgment, the provider can retry. The sample returns 503 in that injected case, then recognizes the retained receipt on retry and applies one grant.

The same ambiguity occurs when a response is lost after commit. The tests inject a post-commit handler failure; they do not physically drop a packet.

### Permanent problems need a deliberate policy

Malformed signatures/unsupported transport are rejected. A recognized, structurally valid event can be accepted but later placed in review for an unknown order, amount mismatch or conflicting payment identity.

Unsupported signed event types are durably marked ignored in this demo. Configure subscriptions to the events the application handles, and monitor ignored/schema-error rates. This is not permission to silently ignore a newly required funding/refund event.

Production systems may use durable quarantine for schema evolution instead of endlessly rejecting a legitimate changed payload. The sample has a narrow supported subset.

---

## 9.6 Inbox identity and business idempotency

The inbox key is (configured endpoint, event ID). It stores a raw-body hash, a minimal normalized event and processing state.

```text
same scoped event ID + same raw-body hash
  -> existing receipt/duplicate acceptance

same scoped event ID + changed bytes
  -> 409 conflict under this demo's policy

different event ID + same captured payment/order
  -> new receipt, existing business grant
```

The byte-conflict policy is deliberately strict. It is not a universal claim that every provider always serializes replayed data identically. In a real adapter, investigate conflicts under the provider's event/version contract.

The inbox does not retain full customer/card/email payloads. It keeps only fields needed by the selected worker, plus the original raw hash. A production audit/replay retention policy may require additional protected storage.

### The ledger key identifies the effect

The selected rule is one purchase credit grant per local order. The ledger primary key includes tenant, local order and kind. Another uniqueness constraint prevents the same provider payment from funding multiple purchase effects.

The worker additionally checks payment identity and existing grants, recording meaningful review reasons rather than relying only on a database exception.

A second captured payment for an already funded order is not automatically “the same event.” It can represent an actual additional charge requiring investigation/refund policy. The demo records review and preserves one entitlement grant.

### Retention changes the guarantee

If deduplication records disappear, old deliveries can look new. Long-lived business ledger/order keys can still prevent an entitlement from being granted again.

Define retention and archival alongside accounting/privacy/operational requirements. Do not claim unlimited replay safety from a short-lived in-memory cache.

The verifier's file-backed recovery demonstrates retained database state across process exit/reopen. It is not an archival/backup policy.

---

## 9.7 Order intent, payment attempts and out-of-order observations

A local order and a payment attempt are different state machines.

| Entity | Selected example states |
| --- | --- |
| Local order | pending, paid |
| Payment attempt | authorized, failed, captured |
| Inbox receipt | pending, processed, ignored, review |
| Outbox message | pending, sent |

A failed attempt does not permanently fail the order. Another payment attempt can later capture and fulfill it.

### Do not assume delivery order

An authorized snapshot can arrive after a captured snapshot. Downgrading paid/captured state because the last HTTP delivery said authorized would regress the business result.

The sample treats captured as absorbing for its narrow purchase-grant model. Earlier authorized/failed observations cannot remove an established capture or a paid order.

Reference: [Razorpay payment event snapshots](https://razorpay.com/docs/webhooks/payments/).

This is not a universal numeric ranking for every provider state. Refunds, reversals, disputes, cancellation and partial capture require separate supported transitions and effects.

### What exactly causes the grant?

Only a supported captured observation can create the purchase grant, after validating the local expected order/account/amount/currency/payment identity.

Authorization alone reserves/approves an attempt under the provider's model; it is not the same as the confirmed captured observation this application requires.

The example supports full expected amounts in INR fixtures. Partial captures, multi-currency conversion, settlement/net fees and reconciliation of refunds are not implemented.

### Why event timestamps are insufficient

Events can describe different attempts/resources, and timestamps can have equal precision or arrive long after creation. Sorting incoming notifications by timestamp does not establish all causal/business relationships.

Use stable resource identities, a defined transition policy and authoritative lookup/reconciliation when observations are incomplete or contradictory.

---

## 9.8 Atomic credits: one local transaction

For a new accepted capture, the worker commits:

```text
payment observation/state
purchase ledger entry
local order paid state
outbox notification intent
inbox processed state
```

as one database transaction.

If a failure occurs after the ledger insert but before commit, the transaction rolls back. The receipt stays pending and no partial grant/payment/outbox mutation survives.

The test injects that failure and then retries successfully. Another test exits a separate process at the same stage and reopens the file-backed database.

Reference: [SQLite transactions](https://www.sqlite.org/lang_transaction.html).

### No network wait inside the transaction

The example's transaction operation is synchronous and uses BEGIN IMMEDIATE. It does not call a payment API or send email while holding the transaction.

SQLite serializes writers for this selected database/transaction model. busy_timeout is a bounded lock-wait configuration, not an application-wide retry policy.

File-backed fixtures select rollback-journal DELETE mode and synchronous=FULL; explicitly in-memory fixtures use a memory journal. Both configurations and foreign-key enforcement are queried/asserted by the verifier. Process-recovery observations apply to the recorded local runtime/filesystem; they do not simulate machine power loss or prove all storage durability configurations.

### The ledger is the source of the demonstrated balance

Balances are sums of purchase-credit entries in the sample. Credit amounts come from the server-owned local order snapshot, not payload notes or request fields.

The code inserts purchase entries and does not expose ledger update/delete operations. That does not make the database tamper-proof against a privileged operator.

Spending, refunds, negative adjustments and concurrent debit limits are separate workflows. A production balance/ledger model must specify those invariants too.

### Transactional does not mean globally atomic

The provider's payment and your local database are separate systems. A transaction here cannot roll back a captured remote payment.

Coordinate uncertain remote outcomes through stable identities, provider-supported idempotency, durable workflow state and reconciliation. Use compensating actions only under a defined business policy.

---

## 9.9 Outbox: record downstream intent with the grant

If you grant credits and then crash before queuing a notification, the user may never receive the notification. If you send first and crash before recording it, retry can send twice.

The transactional outbox records notification intent in the same transaction as the business effect. A separate dispatcher sends it later.

```text
transaction:
  ledger + order + processed receipt + outbox row
commit

dispatcher:
  send stable message ID
  record local delivery completion
```

Reference: [AWS transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).

### The outbox does not guarantee one external delivery

The sender can succeed remotely and fail before marking the local row sent. Retry can repeat delivery.

The test's local recipient fixture deduplicates on the stable notification ID. Two delivery attempts produce one fixture effect.

If a recipient has no idempotency capability, the product must tolerate duplicates or use another reconciliation/design policy. Do not describe outbox alone as universal exactly-once messaging.

The dispatcher in this sample is deliberately single-dispatcher code with no leasing/backoff/dead-letter system. Multiple dispatchers need claiming/leases or equivalent coordination, and still need a duplicate-delivery policy.

No real email/customer webhook/provider notification is sent.

---

## 9.10 Timeout ambiguity, retries and reconciliation

A timeout establishes that a response was not observed within the caller's waiting budget. It does not establish that the remote operation failed or rolled back.

| Situation | Useful action |
| --- | --- |
| Invalid signature | Reject, investigate configuration/forgery; no business effect |
| Temporary inbox/storage failure | Non-2xx; provider retry may repair delivery |
| Accepted inbox, worker failure | Internal retry/recovery of retained pending work |
| Captured amount/account mismatch | Review/reconcile; do not guess entitlement |
| Provider call times out | Retain unknown outcome and stable operation identity |
| Notification accepted but local completion lost | Retry under recipient idempotency/duplicate policy |
| Missing capture webhook | Account-bound provider lookup can supply an observation |

### Retry policy belongs to each boundary

Provider delivery retry, application worker retry, provider SDK retry and notification retry are different loops. Give each a deadline, attempt/backoff policy and observability.

Retry only appropriately temporary failures and only when repetition is safe under that operation's contract. Avoid nested retry loops multiplying work.

The sample does not ship a generalized provider SDK retry client or a failed-job scheduler. Pending work remains recoverable; production scheduling/dead-letter behavior belongs in M15 and the architecture reliability track.

### Reconciliation is an active recovery path

A proposed reconciliation job finds unresolved local operations, fetches account-bound provider state and applies the same business invariants as webhooks.

The runnable adapter accepts a local fixture client returning an account context plus payment entity. That account context represents the configured client's credentials, not an invented account_id field in Razorpay's payment-fetch response.

Reference: [Razorpay fetch-payment API](https://razorpay.com/docs/api/payments/fetch-with-id/).

It validates returned account/payment identity, normalizes a supported observation and feeds the same inbox/worker. Repeating a captured observation or receiving a delayed real webhook cannot grant again.

A lookup timeout leaves local state unchanged and unresolved. An unsupported provider state such as created is also unresolved, not a guessed capture.

The tests use fixture provider functions only. No actual authenticated provider request, settlement report or live reconciliation job is run.

---

## 9.11 Define the small system and failure boundaries

### Seeded order snapshots

| Tenant/local order | Configured endpoint/provider order | Amount/currency | Credits |
| --- | --- | --- | --- |
| alpha / a-1 | alpha / order_alpha_1 | 25000 / INR | 100 |
| alpha / a-2 | alpha / order_alpha_2 | 50000 / INR | 200 |
| beta / b-1 | beta / order_beta_1 | 25000 / INR | 100 |

Amounts use the provider's currency-subunit convention for these INR fixtures. Avoid floating-point multiplication of untrusted money input; validate exact expected integer amounts/currency at the boundary.

The example seeds already bound provider orders. It does not implement real order creation, checkout callback verification or catalog APIs.

### Architecture

```text
local fixture sender
  -> raw signed HTTP POST /webhooks/alpha or /beta
      -> configured endpoint/secret/account checks
      -> minimal normalized durable inbox
      <- 202 after commit

worker (same process or independent local process)
  -> pending receipt
  -> authoritative local provider-order mapping
  -> transaction: payment + ledger + order + outbox + receipt

dispatcher
  -> local recipient fixture using stable message ID

reconciliation adapter
  -> local account-bound provider fixture
  -> same normalized observation/worker invariant
```

Only the webhook receiver is an HTTP capability here. Worker, snapshot inspection and reconciliation are trusted local test/launcher APIs. A deployed operator interface would require M7/M8 authentication/authorization.

### Complete teaching source

Opening a store requires an explicit filename; use :memory: only for isolated tests, and a real file path when persistence is required. The following files form the verified implementation. Phase hooks are synchronous test seams for failure/exit injection; they are not request-controlled.

#### fixtures.mjs

```javascript
export const endpoints = {
  alpha: { accountId: 'acc_alpha', secrets: ['alpha-demo-secret', 'alpha-old-demo-secret'] },
  beta: { accountId: 'acc_beta', secrets: ['beta-demo-secret'] },
};
export const orders = [
  { tenant: 'alpha', localId: 'a-1', endpoint: 'alpha', providerId: 'order_alpha_1', amount: 25000, currency: 'INR', credits: 100 },
  { tenant: 'alpha', localId: 'a-2', endpoint: 'alpha', providerId: 'order_alpha_2', amount: 50000, currency: 'INR', credits: 200 },
  { tenant: 'beta', localId: 'b-1', endpoint: 'beta', providerId: 'order_beta_1', amount: 25000, currency: 'INR', credits: 100 },
];
export function fixtureEvent({
  endpoint = 'alpha', type = 'payment.captured', paymentId = 'pay_alpha_1',
  providerOrderId = endpoint === 'alpha' ? 'order_alpha_1' : 'order_beta_1',
  amount = 25000, currency = 'INR', extra = {},
} = {}) {
  return {
    entity: 'event', account_id: 'acc_' + endpoint, event: type,
    payload: { payment: { entity: {
      entity: 'payment', id: paymentId, order_id: providerOrderId, amount, currency,
      status: type.split('.')[1],
    } } }, ...extra,
  };
}
```

#### webhook.mjs

```javascript
import { createHash, createHmac, timingSafeEqual } from 'node:crypto';
export class IntegrationError extends Error {
  constructor(status, code) { super(code); Object.assign(this, { status, code }); }
}
export const fail = (status, code) => { throw new IntegrationError(status, code); };
export const sign = (raw, secret) => createHmac('sha256', secret).update(raw).digest('hex');
export function verifySignature(raw, signature, secrets) {
  if (typeof signature !== 'string' || !/^[a-fA-F0-9]{64}$/.test(signature)) fail(401, 'invalid_signature');
  const received = Buffer.from(signature, 'hex');
  const matches = secrets.map(secret => timingSafeEqual(Buffer.from(sign(raw, secret), 'hex'), received));
  if (!matches.some(Boolean)) fail(401, 'invalid_signature');
}
const id = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,80}$/.test(value);
export function parseEvent(raw, endpoint) {
  let value;
  try { value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw)); }
  catch { fail(400, 'invalid_json'); }
  if (!value || value.entity !== 'event' || typeof value.event !== 'string' || value.event.length > 80)
    fail(400, 'invalid_event');
  if (value.account_id !== endpoint.accountId) fail(403, 'account_mismatch');
  const expected = new Map([
    ['payment.authorized', 'authorized'], ['payment.captured', 'captured'], ['payment.failed', 'failed'],
  ]).get(value.event);
  if (!expected) return { type: value.event, ignored: true };
  const payment = value.payload?.payment?.entity;
  if (!payment || payment.entity !== 'payment' || !id(payment.id) || !id(payment.order_id) ||
      !Number.isSafeInteger(payment.amount) || payment.amount <= 0 ||
      typeof payment.currency !== 'string' || !/^[A-Z]{3}$/.test(payment.currency) ||
      payment.status !== expected) fail(400, 'invalid_payment');
  return {
    type: value.event, paymentId: payment.id, providerOrderId: payment.order_id,
    amount: payment.amount, currency: payment.currency, status: expected,
  };
}
export function receive({ endpointId, endpoints, store, raw, signature, eventId }) {
  const endpoint = Object.hasOwn(endpoints, endpointId) ? endpoints[endpointId] : undefined;
  if (!endpoint) fail(404, 'not_found');
  if (!id(eventId)) fail(400, 'invalid_event_id');
  verifySignature(raw, signature, endpoint.secrets);
  const event = parseEvent(raw, endpoint);
  const rawHash = createHash('sha256').update(raw).digest('hex');
  return store.accept(endpointId, eventId, rawHash, event);
}
```

#### store.mjs

```javascript
import { DatabaseSync } from 'node:sqlite';
import { fail } from './webhook.mjs';

export function openStore(filename, { onPhase = () => {} } = {}) {
  if (typeof filename !== 'string' || !filename)
    throw new TypeError('Supply a database path or explicit :memory: for tests.');
  const db = new DatabaseSync(filename);
  db.exec(`
    PRAGMA foreign_keys = ON;
    PRAGMA journal_mode = DELETE;
    PRAGMA synchronous = FULL;
    PRAGMA busy_timeout = 5000;
    CREATE TABLE IF NOT EXISTS orders (
      tenant TEXT NOT NULL, local_id TEXT NOT NULL, endpoint TEXT NOT NULL,
      provider_id TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount > 0),
      currency TEXT NOT NULL, credits INTEGER NOT NULL CHECK(credits > 0),
      state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','paid')),
      PRIMARY KEY(tenant, local_id), UNIQUE(endpoint, provider_id)
    );
    CREATE TABLE IF NOT EXISTS inbox (
      endpoint TEXT NOT NULL, event_id TEXT NOT NULL, raw_hash TEXT NOT NULL,
      payload TEXT NOT NULL, state TEXT NOT NULL, reason TEXT,
      PRIMARY KEY(endpoint, event_id)
    );
    CREATE TABLE IF NOT EXISTS payments (
      endpoint TEXT NOT NULL, payment_id TEXT NOT NULL,
      provider_order_id TEXT NOT NULL, amount INTEGER NOT NULL,
      currency TEXT NOT NULL, state TEXT NOT NULL,
      PRIMARY KEY(endpoint, payment_id)
    );
    CREATE TABLE IF NOT EXISTS ledger (
      tenant TEXT NOT NULL, local_order_id TEXT NOT NULL,
      endpoint TEXT NOT NULL, payment_id TEXT NOT NULL,
      credits INTEGER NOT NULL CHECK(credits > 0), kind TEXT NOT NULL,
      PRIMARY KEY(tenant, local_order_id, kind),
      UNIQUE(endpoint, payment_id, kind),
      FOREIGN KEY(tenant, local_order_id) REFERENCES orders(tenant, local_id)
    );
    CREATE TABLE IF NOT EXISTS outbox (
      id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
      attempts INTEGER NOT NULL DEFAULT 0
    );
  `);
  const one = (sql, ...args) => db.prepare(sql).get(...args);
  const all = (sql, ...args) => db.prepare(sql).all(...args);
  const run = (sql, ...args) => db.prepare(sql).run(...args);
  function transaction(operation) {
    db.exec('BEGIN IMMEDIATE');
    try {
      const result = operation();
      db.exec('COMMIT');
      return result;
    } catch (error) {
      try { db.exec('ROLLBACK'); } catch { /* preserve the original failure */ }
      throw error;
    }
  }
  function seed(items) {
    for (const item of items) run(`
      INSERT OR IGNORE INTO orders(tenant,local_id,endpoint,provider_id,amount,currency,credits)
      VALUES(?,?,?,?,?,?,?)
    `, item.tenant, item.localId, item.endpoint, item.providerId, item.amount, item.currency, item.credits);
  }
  function accept(endpoint, eventId, rawHash, event) {
    const accepted = transaction(() => {
      const prior = one('SELECT raw_hash,state FROM inbox WHERE endpoint=? AND event_id=?', endpoint, eventId);
      if (prior) {
        if (prior.raw_hash !== rawHash) fail(409, 'event_id_conflict');
        return { accepted: true, duplicate: true, state: prior.state };
      }
      onPhase('before-inbox-insert');
      run('INSERT INTO inbox(endpoint,event_id,raw_hash,payload,state) VALUES(?,?,?,?,?)',
        endpoint, eventId, rawHash, JSON.stringify(event), event.ignored ? 'ignored' : 'pending');
      return { accepted: true, duplicate: false, state: event.ignored ? 'ignored' : 'pending' };
    });
    onPhase('after-inbox-commit');
    return accepted;
  }
  function processOne(endpoint, eventId) {
    const result = transaction(() => {
      const receipt = one('SELECT * FROM inbox WHERE endpoint=? AND event_id=?', endpoint, eventId);
      if (!receipt || receipt.state !== 'pending') return { outcome: receipt?.state ?? 'missing' };
      const event = JSON.parse(receipt.payload);
      const finish = (state, reason) => {
        run('UPDATE inbox SET state=?,reason=? WHERE endpoint=? AND event_id=?', state, reason, endpoint, eventId);
        return { outcome: state, reason };
      };
      const order = one('SELECT * FROM orders WHERE endpoint=? AND provider_id=?', endpoint, event.providerOrderId);
      if (!order) return finish('review', 'unknown_order');
      if (order.amount !== event.amount || order.currency !== event.currency)
        return finish('review', 'amount_or_currency_mismatch');
      const prior = one('SELECT * FROM payments WHERE endpoint=? AND payment_id=?', endpoint, event.paymentId);
      if (prior && (prior.provider_order_id !== event.providerOrderId ||
          prior.amount !== event.amount || prior.currency !== event.currency))
        return finish('review', 'payment_identity_conflict');
      // Captured is absorbing only for this deliberately narrow payment model.
      const state = prior?.state === 'captured' || event.status === 'captured' ? 'captured'
        : prior?.state === 'failed' || event.status === 'failed' ? 'failed' : 'authorized';
      run(`INSERT INTO payments(endpoint,payment_id,provider_order_id,amount,currency,state)
        VALUES(?,?,?,?,?,?) ON CONFLICT(endpoint,payment_id) DO UPDATE SET state=excluded.state`,
      endpoint, event.paymentId, event.providerOrderId, event.amount, event.currency, state);
      if (event.status !== 'captured') return finish('processed', 'no_capture_grant');
      const granted = one("SELECT * FROM ledger WHERE tenant=? AND local_order_id=? AND kind='purchase'",
        order.tenant, order.local_id);
      if (granted) {
        if (granted.payment_id !== event.paymentId) return finish('review', 'order_already_funded');
        return finish('processed', 'already_granted');
      }
      run("INSERT INTO ledger(tenant,local_order_id,endpoint,payment_id,credits,kind) VALUES(?,?,?,?,?,'purchase')",
        order.tenant, order.local_id, endpoint, event.paymentId, order.credits);
      onPhase('after-ledger-write');
      run("UPDATE orders SET state='paid' WHERE tenant=? AND local_id=?", order.tenant, order.local_id);
      const notificationId = JSON.stringify(['credit-granted', order.tenant, order.local_id]);
      run('INSERT INTO outbox(id,payload) VALUES(?,?)', notificationId, JSON.stringify({
        tenant: order.tenant, orderId: order.local_id, credits: order.credits,
      }));
      const completed = finish('processed', 'granted');
      onPhase('before-effect-commit');
      return completed;
    });
    onPhase('after-effect-commit');
    return result;
  }
  function processNext() {
    const row = one("SELECT endpoint,event_id FROM inbox WHERE state='pending' ORDER BY rowid LIMIT 1");
    return row ? processOne(row.endpoint, row.event_id) : { outcome: 'idle' };
  }
  async function dispatchOne(send, { afterSend = () => {} } = {}) {
    const row = one("SELECT * FROM outbox WHERE state='pending' ORDER BY rowid LIMIT 1");
    if (!row) return { outcome: 'idle' };
    run('UPDATE outbox SET attempts=attempts+1 WHERE id=?', row.id);
    await send({ id: row.id, payload: JSON.parse(row.payload) });
    await afterSend();
    run("UPDATE outbox SET state='sent' WHERE id=?", row.id);
    return { outcome: 'sent', id: row.id };
  }
  function snapshot() {
    return {
      orders: all('SELECT * FROM orders ORDER BY tenant,local_id'),
      inbox: all('SELECT endpoint,event_id,state,reason FROM inbox ORDER BY endpoint,event_id'),
      payments: all('SELECT * FROM payments ORDER BY endpoint,payment_id'),
      ledger: all('SELECT * FROM ledger ORDER BY tenant,local_order_id'),
      outbox: all('SELECT * FROM outbox ORDER BY id'),
      balances: all('SELECT tenant,SUM(credits) AS credits FROM ledger GROUP BY tenant ORDER BY tenant'),
    };
  }
  return {
    seed, accept, processOne, processNext, dispatchOne, snapshot,
    sqlite: () => one('SELECT sqlite_version() AS version').version,
    configuration: () => ({ journal: one('PRAGMA journal_mode').journal_mode,
      synchronous: one('PRAGMA synchronous').synchronous, foreignKeys: one('PRAGMA foreign_keys').foreign_keys }),
    close: () => db.close(),
  };
}

```

#### server.mjs

```javascript
import { createServer } from 'node:http';
import { receive, IntegrationError, fail } from './webhook.mjs';

export function createWebhookServer({ endpoints, store }) {
  const server = createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, value, headers = {}) => {
      res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', ...headers });
      res.end(JSON.stringify(value));
    };
    try {
      const match = /^\/webhooks\/(alpha|beta)$/.exec(req.url);
      if (!match || !endpoints[match[1]]) fail(404, 'not_found');
      if (req.method !== 'POST') return send(405, { code: 'method_not_allowed' }, { Allow: 'POST' });
      const media = (req.headers['content-type'] ?? '').split(';').map(s => s.trim().toLowerCase());
      if (media[0] !== 'application/json' || media.slice(1).some(s => !/^charset="?utf-8"?$/.test(s)) ||
          (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity'))
        fail(415, 'unsupported_body_format');
      let size = 0;
      const chunks = [];
      for await (const chunk of req) {
        size += chunk.length;
        if (size <= 16384) chunks.push(chunk);
      }
      if (size > 16384) fail(413, 'body_too_large');
      const result = receive({
        endpointId: match[1], endpoints, store, raw: Buffer.concat(chunks),
        signature: req.headers['x-razorpay-signature'], eventId: req.headers['x-razorpay-event-id'],
      });
      // Commit of the local inbox happened before acknowledgment; business work is separate.
      return send(202, result);
    } catch (error) {
      const known = error instanceof IntegrationError;
      const status = known ? error.status : 503;
      send(status, { code: known ? error.code : 'temporarily_unavailable' },
        status === 401 ? { 'WWW-Authenticate': 'Webhook-HMAC realm="local-fixture"' } : {});
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
    }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 5000;
  return server;
}
```

#### reconcile.mjs

```javascript
import { createHash } from 'node:crypto';
import { parseEvent, fail } from './webhook.mjs';

// Trusted worker API, not an unauthenticated HTTP route.
// fetchPayment is an account-bound provider client; the tests supply a local fixture.
export async function reconcilePayment({ endpointId, endpoints, store, paymentId, fetchPayment }) {
  const endpoint = Object.hasOwn(endpoints, endpointId) ? endpoints[endpointId] : undefined;
  if (!endpoint) fail(404, 'not_found');
  const snapshot = await fetchPayment({ endpointId, paymentId });
  if (snapshot.accountId !== endpoint.accountId) fail(502, 'provider_account_mismatch');
  if (snapshot.payment?.id !== paymentId) fail(502, 'provider_payment_mismatch');
  if (!['authorized', 'captured', 'failed'].includes(snapshot.payment.status))
    return { outcome: 'unresolved' };
  const raw = Buffer.from(JSON.stringify({
    entity: 'event', account_id: snapshot.accountId,
    event: 'payment.' + snapshot.payment.status,
    payload: { payment: { entity: snapshot.payment } },
  }));
  const normalized = parseEvent(raw, endpoint);
  const hash = createHash('sha256').update(raw).digest('hex');
  // ':' is forbidden in external delivery IDs, separating internal observations.
  const eventId = 'reconcile:' + hash;
  store.accept(endpointId, eventId, hash, normalized);
  return store.processOne(endpointId, eventId);
}
```

The demo's phase hooks can throw or exit synchronously at selected boundaries. They are used only by the verifier. Network calls do not run inside the database transaction.

The optional launcher polls pending receipts every 250 ms in the same process. That timer is a convenience for inspection, not a durable scheduler or throughput recommendation.

---

## 9.12 Checkout verification, refunds and boundaries not implemented

### Checkout signatures are a different message

Razorpay's checkout verification uses the server-associated provider order ID and returned payment ID, joined by a separator, with the API key secret. Its webhook verifier uses the raw body and webhook secret.

Documented checkout construction, not a live checkout execution here:

```text
HMAC_SHA256(server_saved_order_id + "|" + returned_payment_id, api_key_secret)
```

Do not replace the server's order association with whatever order ID a browser supplies. First enforce the authenticated user's local order/tenant access and then verify the supported provider feedback.

Reference: [Razorpay server integration and signature verification](https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/).

Valid checkout feedback still needs the application's capture/fulfillment policy. The current code intentionally grants only through its supported captured observations and trusted local mapping.

### Refunds and disputes are new effects

A refund is not simply a late failed event that moves the paid order back to pending. It has its own provider identity, amount, lifecycle and accounting/entitlement consequences.

If credits have already been spent, subtracting the original grant without a business rule can create an invalid balance. Decide on refund eligibility, partial amounts, debt/entitlement policy, audit and reconciliation before automating reversal.

Use separate idempotent ledger adjustment/effect keys and account for provider-call timeout ambiguity. A local database rollback cannot cancel an already accepted remote refund.

This chapter does not issue refunds or implement refund/dispute/settlement states. The narrow captured-absorbing rule must not be copied as a full financial state machine.

---

## 9.13 What the verification establishes

| Group | Count | Main evidence |
| --- | --- | --- |
| Core | 21 | HMAC vector/raw bytes, secret rotation, business deduplication, account/order/amount mapping, state ordering, rollback and outbox fixture |
| Real HTTP | 26 | Rejected input/signatures, durable acceptance boundary, duplicate/relabelled deliveries, old secret, account/tenant checks and acknowledgment failures |
| Reconciliation fixtures | 6 | Timeout remains unknown, missing-webhook repair, identity validation and shared grant invariant |
| File/process recovery | 4 | Reopen pending inbox, exit before/after commit and two independent workers |
| Total | 57 | Named cases; each may contain several assertions/requests |

### Actual selected output

```text
PASS verification preserves raw whitespace and rejects reserialization: {"exactBytesAccepted":true,"reserializedRejected":true}
PASS worker commits credit, paid order, receipt and outbox together: {"credits":100,"ledgerRows":1,"order":"paid","receipt":"processed","outboxRows":1}
PASS new delivery ID for same signed payment cannot grant twice: {"receiptRows":2,"ledgerRows":1,"credits":100}
PASS failed attempt does not close order to a later successful attempt: {"failedAttemptCredits":0,"finalOrder":"paid","credits":100}
PASS injected failure after ledger insert rolls back every business effect: {"credits":0,"ledgerRows":0,"outboxRows":0,"receipt":"pending"}
PASS outbox retry after accepted send can repeat delivery but not idempotent sink effect: {"deliveryAttempts":2,"sinkEffects":1,"outbox":"sent"}
PASS acknowledgment follows inbox commit but precedes worker effect: {"ack":202,"inboxAtAck":1,"ledgerAtAck":0,"ledgerAfterWorker":1}
PASS post-commit acknowledgment failure leaves retryable durable acceptance: {"first":503,"retry":202,"duplicate":true,"ledgerRows":1}
PASS provider lookup timeout leaves outcome unresolved and local balance unchanged: {"knownPaymentFailure":false,"ledgerRows":0}
PASS process exit before effect commit recovers pending receipt with zero partial credit: {"workerExit":77,"beforeRetryLedgerRows":0,"receipt":"pending","afterRetryCredits":100}
PASS process exit after commit preserves one grant and one outbox row: {"workerExit":77,"receipt":"processed","ledgerRows":1,"outboxRows":1,"afterRetryCredits":100}
PASS two ready independent worker processes commit a single grant: {"workerProcesses":2,"grants":1,"ledgerRows":1,"outboxRows":1,"credits":100}
Verified 57 checks across core, real HTTP, reconciliation fixtures and file/process recovery.
```

### How recovery was exercised

The verifier creates a fresh temporary directory and file-backed SQLite databases. A child worker calls process.exit(77) immediately after the ledger write or after effect commit, without executing normal close/finally cleanup.

The parent reopens the database, inspects actual retained state and retries. Before commit, the pending receipt survives with no partial payment/ledger/outbox state. After commit, one processed receipt/grant/outbox row survives.

Two other child workers both open the same prepared database, report readiness and are released by the parent to process the same receipt. The database transaction/constraints yield one grant. This is not a lock-wait timing measurement or a claim about which OS process runs first.

The verifier closes handles and checks the resolved identity/location of its newly created temporary directory before removing that directory.

### What remains unverified

No real Razorpay/Stripe account, public endpoint, external notification, authenticated provider API, browser checkout, refund, dispute, settlement report or PostgreSQL service participates.

Process exits are not power-loss/storage-failure experiments. The tests do not establish network-filesystem behavior, distributed multi-host operation, multi-dispatcher leases, queue scheduling, backoff/dead-letter policy, backup restoration or performance.

The local receiver's account/schema subset is not a full provider SDK or compatibility certification. The outbox recipient's idempotency and reconciliation provider are fixtures.

These limits describe the evidence, not reasons to skip the invariants when extending the system.

---

## 9.14 Evolve the architecture from explicit requirements

### Requirement: use a production database and several workers

Preserve unique receipt/effect identities and transactionally coordinate receipt state, payment/order state, ledger and outbox. Verify the target database's constraints, isolation and worker-claim behavior.

Do not use a check-then-insert without a shared uniqueness/locking protocol. Separate application processes do not share a JavaScript Map.

SQLite's verified local single-file behavior does not establish a multi-host database deployment. M13 will examine PostgreSQL-specific transaction/query behavior.

### Requirement: process larger workloads

Keep the receiver's durable acceptance path small. Use a durable worker scheduler/queue or polling strategy with bounded batches, retries, claim expiry and monitoring.

Observe pending-receipt age, worker failure/review counts and outbox backlog. Returning 202 quickly while never draining the inbox is not a successful payment integration.

### Requirement: emit customer webhooks

Commit a stable event/outbox record with your own business change. Sign each receiver's supported message using that receiver's secret, retry according to your delivery contract and expose appropriate event/delivery status.

Keep event identity distinct from delivery attempts. Define timestamp/signature freshness and secret rotation rather than copying another provider's headers as an accidental standard.

### Requirement: support additional event types

Add explicit normalized adapters, transition rules, review reasons and regression fixtures. Subscribe only to the required supported provider events.

A refund, chargeback or order.paid observation can overlap existing effects. Its own event ID does not justify reapplying a purchase grant.

### Requirement: recover missing or uncertain operations

Persist unresolved work, perform account-bound provider lookup/report comparison and apply the same effect guard. Track unknown/review outcomes so operators can repair mappings or retry safely.

The sample records review but does not expose an operator requeue/approval API. Such an API needs authentication, tenant/capability checks and an audit trail from M7/M8.

### Requirement: immediate UI feedback

Let the browser query authorized local order state and display pending/confirmed/review appropriately. A browser success callback can initiate verification or improve UX, but it cannot choose paid amount or grant credits.

Do not expose the entire ledger, provider account secrets or other tenants' order existence to make status checking convenient.

---

## 9.15 Connect this to your resume

For a Razorpay/payment/credit claim, prepare an answer tied to the actual system you built:

> “The backend owned the expected order amount and credit entitlement. I verified the provider's supported signature over the exact required message, mapped the observation to our local order/account, and applied the grant under a durable unique business key. Duplicate or delayed events could not grant twice. Unknown outcomes had a reconciliation/review path.”

Only include mechanisms your project actually implemented. This learning service is practice evidence, not proof that an older project had a durable inbox/outbox.

| Resume claim | Follow-up |
| --- | --- |
| Razorpay integration | Checkout signature versus webhook signature; which secret/message? |
| Payment/credit logic | What is the unique business effect, and what commits atomically? |
| Webhooks | How do replay, changed delivery IDs and out-of-order snapshots behave? |
| Multi-tenant integration | Which trusted mapping selects account, tenant and beneficiary? |
| Reliability | What survives a process exit, and who retries after 2xx? |
| Notifications | Can delivery repeat after the recipient already accepted it? |
| Performance | Which workload/latency/error/backlog measurements support the claim? |

A strong design explanation traces one successful capture, one repeated observation, one failure before commit and one uncertain remote outcome.

---

## 9.16 Must remember

- Webhook, polling and browser callback are different observations.
- Local order, provider order, payment attempt, event and delivery are different identities.
- Preserve the exact signed message; JSON equivalence is not byte equality.
- HMAC authenticates under a secret; it does not encrypt or prevent replay by itself.
- Signature formats and freshness policies are provider-specific.
- A body signature does not automatically authenticate every HTTP header.
- Bind provider account/endpoint and order mapping before deriving tenant/credits.
- Expected amount, currency and entitlement come from trusted local state.
- Durable acceptance and completed business work are separate states.
- After a 2xx acknowledgment, internal processing/recovery belongs to the receiver.
- Inbox event deduplication and business-effect idempotency solve different duplication.
- A failed payment attempt does not necessarily fail the whole order intent.
- Arrival order is not causal/provider-state order.
- Captured-absorbing purchase logic is not a complete refund/dispute model.
- Commit ledger, order, receipt and downstream intent together where the invariant requires it.
- Avoid remote network calls while holding the local business transaction.
- An outbox can deliver more than once; the receiver/operation needs a duplicate policy.
- A timeout does not prove a remote failure or rollback.
- Reconciliation applies trusted observations through the same effect guard.
- A local transaction cannot atomically commit a provider's remote state.
- Process-recovery evidence is narrower than power-loss/distributed durability.
- Unknown/review/ignored/pending states require operational ownership and monitoring.

---

## 9.17 Common wrong answers

| Wrong answer | Correction |
| --- | --- |
| “The browser says paid, so add credits.” | Verify through a trusted server/provider path and authoritative local mapping. |
| “We verify JSON.stringify(req.body).” | Verify the exact bytes/message required by the provider scheme. |
| “HMAC encrypts the payment payload.” | It authenticates content under a secret; the payload is not hidden. |
| “A valid signature means this event is new.” | Replay and business identity still need controls. |
| “Every signed HTTP header is covered by the body signature.” | Only the scheme's actual signed input is covered. |
| “Event-ID deduplication makes credits exactly once.” | Different events/delivery IDs can describe the same business effect. |
| “Failed payment means the order can never succeed.” | Another attempt may later capture for the same intent. |
| “The latest delivery status always wins.” | Older snapshots can arrive after newer state. |
| “Return 200 and start an unawaited task.” | Acknowledgment before durable acceptance can lose work. |
| “A 202 means credits are already available.” | It means accepted; completion follows the application contract. |
| “Mark processed, then update balance separately.” | A crash can split those writes; coordinate the invariant transactionally. |
| “Send email while the ledger transaction is open.” | Record outbox intent and send outside the transaction. |
| “Outbox means one external send.” | Acceptance/completion ambiguity can repeat delivery. |
| “Provider timeout means payment failed.” | The outcome can be unknown; reconcile by stable identity. |
| “Every endpoint supports the same idempotency header.” | Provider/endpoint contracts differ. |
| “A database rollback undoes a captured payment.” | Local and provider state are separate systems. |
| “Refund is a late failed event.” | Model its separate identity, amounts and compensating effects. |
| “A local fixture proves live provider compatibility.” | Real credentials, transport, schemas and operational behavior still need testing. |

---

## 9.18 Interview questions and follow-ups

These questions target integration mechanisms and failure cases. They are not measured company-question frequencies.

**Q1. What is a webhook?**

A sender initiates an HTTP request to notify a receiver about an event. It has its own authentication, acknowledgment and retry behavior.

**Follow-up:** how is it different from a browser callback, WebSocket or polling loop?

**Q2. Webhook versus polling: which would you choose?**

Webhooks improve event-driven responsiveness, while polling/reconciliation can repair missing or uncertain observations. Consider latency, rate limits and delivery guarantees.

**Follow-up:** how do you find an unresolved order whose webhook never arrived?

**Q3. Why not trust checkout success from the frontend?**

The browser is an untrusted and unreliable boundary. Verify supported provider feedback and bind it to the server's local order and fulfillment policy.

**Follow-up:** who supplies the expected amount and credit entitlement?

**Q4. How does Razorpay webhook verification work?**

Under the documented scheme, compute HMAC-SHA256 over the raw body using the configured webhook secret and compare with the supplied signature safely.

**Follow-up:** why does parsing then serializing JSON break verification?

**Q5. Checkout signature versus webhook signature?**

They cover different messages and use distinct configured secrets. Checkout verification uses the server-associated order/payment construction; webhooks use raw-body verification.

**Follow-up:** why must the expected order come from server association?

**Q6. Does HMAC prevent replay?**

No. A previously valid message can remain valid. Apply the provider's supported freshness rules plus durable event/effect identities.

**Follow-up:** why is event creation time not always a valid generic delivery-expiry clock?

**Q7. Is X-Razorpay-Event-Id covered by the raw-body HMAC?**

That construction authenticates body bytes, not arbitrary headers. The example therefore verifies business payment/order identity independently of delivery ID.

**Follow-up:** what happens when a signed captured body is sent with another event ID?

**Q8. What belongs in a durable inbox?**

Scoped receipt identity, enough verified normalized data to process, processing state and appropriate audit/conflict information under a retention/privacy policy.

**Follow-up:** what must commit before acknowledging?

**Q9. Why return 202 instead of doing all work in the request?**

It expresses accepted pending processing. Durable acceptance can be short while workers handle business effects/recovery separately.

**Follow-up:** who retries when the provider has already received 2xx?

**Q10. What if persistence fails before acknowledgment?**

Return an appropriate failure and let the provider/application retry under its contract. Do not claim accepted work that was never durably recorded.

**Follow-up:** what if commit succeeded but the acknowledgment failed?

**Q11. Event idempotency versus business idempotency?**

Event identity deduplicates an observation; business identity guards an effect such as one purchase credit grant for an order. Different events can describe the same effect.

**Follow-up:** which database keys enforce both in this sample?

**Q12. Why scope provider IDs by account/endpoint?**

Different account/environment contexts can have separate namespaces and trust. Resolve the event under configured credentials/mapping before deriving tenant identity.

**Follow-up:** why ignore an X-Tenant-Id or payload credit count?

**Q13. How do you handle out-of-order payment events?**

Use resource identity and explicit transition/effect rules. An older authorized snapshot must not downgrade an established captured/purchase result.

**Follow-up:** why is a universal numeric status rank unsafe for refunds and disputes?

**Q14. Order versus payment attempt?**

The order represents purchase intent; payment IDs represent attempts/resources. One failed attempt can be followed by another successful attempt.

**Follow-up:** why does this example keep the order pending after a failed attempt?

**Q15. What causes a credit grant?**

A supported trusted captured observation matching the expected account/order/amount/currency and unique purchase effect, applied under the local transaction.

**Follow-up:** why is authorization alone insufficient under this application's policy?

**Q16. How do you make credits atomic?**

Coordinate the ledger entry, local order state, receipt completion and downstream intent in a database transaction with shared uniqueness constraints.

**Follow-up:** what should survive a failure after the ledger insert but before commit?

**Q17. How do two workers avoid duplicate effects?**

Use shared database transaction/constraint/claim behavior, not process-local checks. Verify against the actual engine and workload.

**Follow-up:** what did the two independent worker processes establish, and what did they not measure?

**Q18. What is an outbox?**

A durable message intent committed with the business effect, delivered later by a dispatcher outside the business transaction.

**Follow-up:** why can the same notification still be delivered twice?

**Q19. How would you make notification effects idempotent?**

Use a stable message/effect ID and recipient-side deduplication/operation semantics, or explicitly tolerate/reconcile duplicates.

**Follow-up:** what if the recipient accepts but your sent marker is never committed?

**Q20. Does timeout mean failure?**

No. The remote operation may have committed before the response was lost or delayed. Retain stable operation identity and reconcile.

**Follow-up:** why is immediately creating a new payment/order intent dangerous?

**Q21. What is reconciliation?**

It compares/repairs unresolved local state using trusted provider observations, ideally through the same invariant guard used by events.

**Follow-up:** what happens if the lookup itself times out or returns the wrong account/payment?

**Q22. Should every error be retried?**

No. Distinguish temporary transport/storage failures from invalid input, identity conflicts and permanent business review. Bound attempt/deadline/backoff behavior.

**Follow-up:** how can several retrying layers multiply downstream work?

**Q23. How do you rotate webhook secrets?**

Use a deliberate provider-compatible overlap/retirement policy for valid delayed deliveries, and treat compromise differently from routine rotation.

**Follow-up:** why not accept every historical secret forever?

**Q24. What if amount or currency does not match?**

Do not derive entitlement from an unexpected value. Record/reconcile the inconsistency according to a review policy and preserve evidence.

**Follow-up:** what if a valid payment ID is rebound to another local order?

**Q25. What if another payment captures for an already funded order?**

It may be an actual additional payment rather than a duplicate notification. Preserve one entitlement grant and investigate the extra charge under a separate workflow.

**Follow-up:** why must automatic refund policy be explicit?

**Q26. How do refunds affect credits?**

Use a separate idempotent adjustment/state model accounting for partial amounts and spent entitlements. Do not simply erase the original purchase record.

**Follow-up:** how do you handle an uncertain remote refund result?

**Q27. Does a local transaction make provider and application state atomic?**

No. They are separate commit domains. Use durable workflows, supported idempotency and reconciliation/compensation.

**Follow-up:** which boundary can the database actually roll back?

**Q28. What operational metrics matter?**

Pending-receipt age, processing/review/error rates, duplicate/conflict counts, outbox backlog and unresolved operation age, with safe correlation and no raw secrets.

**Follow-up:** why is quick 202 with a growing backlog still unhealthy?

**Q29. How would you test this integration?**

Verify known signature input, byte preservation, invalid accounts/amounts, duplicate identities, reordered events, transaction failures, acknowledgment ambiguity, recovery and reconciliation.

**Follow-up:** what requires a real provider sandbox or deployment environment?

**Q30. How would you explain your resume payment work?**

Trace authoritative order creation/mapping, verification, state transition, atomic effect, duplicate handling and uncertain-outcome recovery using actual evidence.

**Follow-up:** distinguish implemented guarantees from the improvements proposed in this chapter.

---

## 9.19 Practice tasks

### Task 1: Draw the complete request paths

Trace checkout initiation, provider webhook, worker and reconciliation. Label which interactions are implemented here and which are proposed.

**Checkpoint:** a browser callback and server-to-server notification are not the same trust path.

### Task 2: Explain signature input

Show why equivalent parsed JSON can have different raw bytes. Identify what the Razorpay-style HMAC covers and which metadata it does not cover.

**Checkpoint:** do not assume the event-ID header is authenticated by the body MAC.

### Task 3: Recreate the identity table

Map local order, provider order, payment, event, inbox, ledger and outbox IDs to their purposes.

**Checkpoint:** one order can have several attempts and observations but one selected purchase entitlement.

### Task 4: Analyze reordered observations

Predict captured then authorized, failed attempt then a different captured attempt, and a second captured payment for an already funded order.

**Checkpoint:** preserve established capture, allow another attempt, and review a possible extra charge without duplicate entitlement.

### Task 5: Break the transaction in a scratch design

Propose what could happen if ledger, order and processed receipt were separate commits. Compare with the injected failure and process-recovery outputs.

**Checkpoint:** restore authoritative code; reasoning must account for actual retained state before retry.

### Task 6: Design a worker retry policy

Specify transient retries, attempt/deadline bounds, backoff, pending/review ownership and alerts for old work.

**Checkpoint:** provider retry after non-2xx is separate from internal retry after accepted work.

### Task 7: Explain the outbox gap

Draw remote acceptance followed by failure before local sent marking. State the recipient behavior required to avoid repeated effects.

**Checkpoint:** two sends can still correspond to one idempotent recipient effect; outbox alone does not prove it.

### Task 8: Add a reconciliation source

Sketch a real account-bound client and safe result adapter. Decide how to handle wrong identity, an unsupported state, unknown order and timeout.

**Checkpoint:** do not invent payment failure or credit value from missing/ambiguous responses.

### Task 9: Propose refund support

Define independent refund identity, allowed amount, state transitions, ledger adjustment, spent-credit policy and uncertain-outcome recovery.

**Checkpoint:** no remote action is implemented by this task; the design needs its own verified provider contract.

### Task 10: Give a resume answer

Explain your actual payment integration in three minutes with a success trace, duplicate, process failure and unknown outcome.

**Checkpoint:** clearly separate local fixture results, real sandbox evidence and proposed production behavior.

---

## Exit checklist

- [ ] I can distinguish webhook, polling, browser callback and reconciliation.
- [ ] I can trace authoritative local order/entitlement mapping.
- [ ] I can distinguish order, attempt, event, delivery and effect identity.
- [ ] I can explain exact-byte signature verification and parser placement.
- [ ] I can distinguish checkout and webhook signature inputs/secrets.
- [ ] I can explain provider-specific freshness and secret rotation.
- [ ] I can identify unsigned metadata and still guard the business effect.
- [ ] I can bind account/endpoint, tenant, amount/currency and payment identity.
- [ ] I can explain durable acceptance versus completed credits.
- [ ] I can state who owns retries after acknowledgment.
- [ ] I can compare receipt deduplication and business-effect uniqueness.
- [ ] I can handle different attempts and out-of-order snapshots.
- [ ] I can locate the atomic ledger/order/receipt/outbox transaction.
- [ ] I can explain rollback and recovery before/after commit.
- [ ] I can describe the independent-worker test without claiming a timing benchmark.
- [ ] I can explain outbox duplicate delivery and recipient idempotency.
- [ ] I can preserve unknown outcomes after timeouts.
- [ ] I can apply reconciled observations through the same grant invariant.
- [ ] I can identify refund/dispute/settlement workflows outside the selected model.
- [ ] I can propose retry/backlog/review observability without leaking secrets.
- [ ] I can run all 57 checks and state the limits of fixture/process evidence.

---

## Next

[M10: Python Fundamentals for Backend Interviews](/docs/resume-skills/python-fundamentals). Build the language/runtime foundation for the resume's Python frameworks: values, functions, collections, exceptions, modules, typing and execution/concurrency distinctions.

M11/M12 then compare Flask/FastAPI and Django/DRF using the same HTTP, authentication, authorization and integration boundaries established in M6-M9.

### Sources and reproducible evidence

Research checked on **14 October 2026**. Execution used Node.js v22.14.0 and SQLite 3.47.2.

- Razorpay: [webhook validation](https://razorpay.com/docs/webhooks/validate-test/), [best practices](https://razorpay.com/docs/webhooks/best-practices/), [payment events](https://razorpay.com/docs/webhooks/payments/), [server integration](https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/) and [fetch payment](https://razorpay.com/docs/api/payments/fetch-with-id/).
- Stripe: [webhooks and signature behavior](https://docs.stripe.com/webhooks) and [idempotent request contract](https://docs.stripe.com/api/idempotent_requests). These policies are not assumed to apply to other providers.
- [HMAC-SHA256 test vectors, RFC 4231](https://www.rfc-editor.org/rfc/rfc4231.html).
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html) and [Node v22.14.0 SQLite API](https://nodejs.org/download/release/v22.14.0/docs/api/sqlite.html).
- [AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).
- Preserved implementation: examples/resume-skills/module-9-webhooks-payments/fixtures.mjs, webhook.mjs, store.mjs, server.mjs and reconcile.mjs.
- Manual-only local demo: start.mjs, send-fixture.mjs and inspect.mjs.
- Preserved verification: verify.mjs, four verify-group files, recovery-worker.mjs, aggregate/group result/log files and SQLite warning logs. validation-summary.json records scope and site checks.
- File-backed tests use isolated temporary databases and confirm cleanup. No real provider credentials, payments or customer messages are used.
