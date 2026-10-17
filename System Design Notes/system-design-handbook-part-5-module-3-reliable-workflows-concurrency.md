# Architecture and System Design Placement Handbook — Part 5
# A3: Reliable Workflows and Concurrency

**Estimated time: 4–5 hours | Architecture numeric module: 3 | Requires: A0/A2, transactions; Resume M9/M13/M15 refreshers**

---

## Why this module exists

A request can time out after its effect commits. A worker can finish its work and stop before acknowledging it. Two callers can both observe the last available unit. A reservation can succeed while a later payment step becomes uncertain. These problems need an operation identity, an authoritative state transition and a recovery owner; adding a retry loop alone can make them worse.

This chapter uses real local SQLite transactions for operation replay, a transactional outbox, a separate consumer inbox/effect, worker claims and compensating stock release. Two independent SQLite connections compete in controlled races. Retry budgets and lease time use injected clocks, and controlled exceptions or omitted steps mark failure boundaries.

**Organizing principle: name the effect, make the local invariant atomic, and define what recovery does after each uncertain boundary.**

This is a separate Python learning fixture. It does not change [A1's Express API](/docs/system-design/application-architecture-service-boundaries) or [A2's cache example](/docs/system-design/data-caching-scaling). There is no deployed broker, provider call, network timeout, process-kill test, payment integration or complete saga coordinator. Supplied tenant/owner/worker context is trusted test input, not authentication.

The 30 Q&As are editorial interview practice, not a measured employer-frequency ranking. A3 develops the architecture bank's Q16–Q22 and reliability reasoning used later in S2/S4/S7/S8. Refresh [M9: webhooks/payments](/docs/resume-skills/webhooks-payments-reliable-integrations), [M13: PostgreSQL](/docs/resume-skills/postgresql-backend) and [M15: jobs/ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion) for stack-specific mechanisms.

---

## 1. Start with the effect and the failure timeline

| Action | Authoritative effect | Uncertain boundary | Recovery question |
| --- | --- | --- | --- |
| Create note | Note + original operation outcome + event intent | Response lost after commit | Does retry find the same operation/result? |
| Deliver note event | Consumer inbox + local projection | Consumer commits but relay acknowledgement is lost | Can redelivery repeat delivery without repeating the effect? |
| Claim work | Current owner/generation/lease recorded | Worker pauses beyond expiry | Can a replacement progress and can the stale owner finish improperly? |
| Reserve stock | Conditional decrement + reservation + outcome | Competing callers or interruption between writes | Can the invariant oversell or partially commit? |
| Compensate reservation | Active reservation becomes released; stock restored | Release response lost or release invoked twice | Can recovery restore stock more than once? |

A timeout tells the caller it lacks a confirmed result. It does not establish whether the remote operation never started, failed before commit, committed without a response, or is still running. The recovery protocol must distinguish what can be checked and what remains unknown.

Write the timeline before selecting a tool:

```text
request accepted -> local transaction -> commit -> response
                                   ^          ^
                               rollback?   result may be lost

claim -> perform consumer effect -> acknowledge source work
                                ^
                    effect may exist while work remains unacknowledged
```

Local transaction rollback addresses changes before commit. Idempotency addresses repeated intent. Acknowledgement addresses delivery progress. Compensation addresses a later business action after an earlier commit. These mechanisms solve different boundaries.

---

## 2. Deadlines, timeouts and cancellation

An end-to-end deadline bounds how long the caller is willing to wait for the complete operation. A per-attempt timeout bounds one dependency attempt. Connection establishment, DNS/TLS, pool wait, request transmission, response reading and any retries must fit the actual deadline contract.

At each attempt, compute remaining time from a suitable monotonic clock and pass a bounded timeout to the transport. A policy function that checks time only between calls cannot interrupt a blocking transport that ignores its timeout. Cancellation also does not undo an already committed remote effect.

AWS recommends choosing timeouts from dependency latency and request context, and warns that retries can amplify overload or repeat side effects. Backoff and jitter spread repeated demand; their usefulness depends on bounded attempts and retry safety. [AWS timeouts, retries and jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/).

For a note create, keep the same scoped operation key across a timeout retry. For an external payment, retain provider operation identity and an explicit unknown/pending state until status lookup or a verified callback resolves it. A caller's expired deadline and the business operation's eventual outcome are different state machines.

The fixture's injected transport honors the budgets in controlled scenarios. Its retry code is not a network client, cancellation runtime or a substitute for a real library's connect/read/overall timeout semantics.

---

## 3. Retry classification, backoff and retry budgets

| Outcome | Default reasoning | Required qualification |
| --- | --- | --- |
| Validation/authentication failure | Fix input/credentials instead of repeating unchanged work | Exact API contract may define a later resolution path |
| Version conflict | Reload/reconcile or retry a complete transaction | Do not overwrite newer state blindly |
| Transient transport/dependency failure | Retry only when the operation is safe | Effect may have committed; preserve operation identity |
| Rate limit / overload | Respect server delay and local budget or shed work | More retries can delay recovery |
| Unknown payment/provider result | Reconcile using stable identity | Do not create a fresh charge operation for every timeout |
| Poison event/schema | Quarantine/investigate or bounded explicit failure | Infinite immediate retries will not repair incompatible data |

The example uses explicit `Transient` and `Permanent` outcomes rather than pretending every HTTP 5xx or Python exception is retryable. `retry_safe=True` is a caller assertion about the operation contract; it does not make an unsafe action idempotent by setting a Boolean.

Its illustrative full-jitter delay is selected within `0..min(cap, base × 2^(attempt−1))`. The injected fraction makes the test deterministic. It does not measure a real distribution of retry traffic. Production also needs a total retry budget, admission control and a policy for server-provided delay such as `Retry-After`.

Only the layer that owns recovery should normally retry the same action under one coordinated budget. Five nested layers allowing three attempts each can generate 243 leaf attempts in the worst case. That is multiplicative arithmetic, not a measured incident in this repository.

---

## 4. Runnable retry policy and observed budgets

`retry.py` accepts transport/time/jitter functions so its decisions can be verified without sleeps or network calls. The transport must enforce the budget it receives.

```python
"""Deterministic deadline/retry exercise; injected transport must honor each budget."""
import math


class Transient(Exception):
    pass


class Permanent(Exception):
    pass


class Deadline(Exception):
    pass


def retry(call, clock, sleep, random_fraction, *, total=1.0, per_attempt=0.4,
          attempts=3, base=0.1, cap=0.5, retry_safe=False):
    values = (total, per_attempt, base, cap)
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError('positive finite durations required')
    if type(attempts) is not int or not 1 <= attempts <= 10:
        raise ValueError('attempt count must be 1..10')
    deadline, trace = clock()+total, []
    for number in range(1, attempts+1):
        remaining = deadline-clock()
        if remaining <= 0:
            raise Deadline('end-to-end deadline exhausted')
        budget = min(per_attempt, remaining)
        trace.append({'attempt': number, 'budget': round(budget, 6)})
        try:
            result = call(budget)
        except Transient:
            if not retry_safe or number == attempts:
                raise
            fraction = random_fraction()
            if not 0 <= fraction <= 1:
                raise ValueError('jitter fraction must be 0..1')
            delay = min(cap, base*2**(number-1))*fraction
            remaining = deadline-clock()
            if remaining <= 0 or delay >= remaining:
                raise Deadline('retry delay would consume remaining deadline')
            trace[-1]['backoff'] = round(delay, 6)
            sleep(delay)
        else:
            if clock() >= deadline:
                raise Deadline('response arrived outside caller deadline')
            return {'result': result, 'trace': trace}
    raise AssertionError('unreachable')
```

Observed safe transient-failure recovery:

```json
{
  "outcome": {
    "result": "accepted",
    "trace": [
      {
        "attempt": 1,
        "budget": 0.4,
        "backoff": 0.05
      },
      {
        "attempt": 2,
        "budget": 0.4,
        "backoff": 0.1
      },
      {
        "attempt": 3,
        "budget": 0.4
      }
    ]
  },
  "fake_elapsed_seconds": 0.45,
  "network_calls_made": false
}
```

Observed deadline decision and amplification arithmetic:

```json
{
  "caller_deadline_seconds": 0.25,
  "first_call_seconds": 0.2,
  "proposed_delay_seconds": 0.1,
  "next_attempt_started": false,
  "retry_layers": 5,
  "attempts_per_layer": 3,
  "maximum_leaf_attempts": 243
}
```

The caller with a 0.25-second deadline has spent 0.2 seconds in its first simulated call. A proposed 0.1-second backoff cannot fit, so a second attempt does not start. The harness also checks permanent failures, unsafe operations, attempt exhaustion, invalid configuration and a result arriving at the deadline.

This small policy omits server-specified retry delays, cancellation tokens and global token-bucket budgets. Those are explicit production follow-ups. It gives a reproducible example of bounded decision logic without claiming to have tested real sockets, TLS or provider behavior.

---

## 5. Idempotency: one intent, one stored outcome

An idempotent operation preserves its defined effect under repeated execution of the same intent. A robust create API normally needs a client-retained operation key, a scope, a request-equivalence policy, an atomic effect/outcome boundary and a retention policy.

AWS's idempotent-API discussion emphasizes caller-provided request identity and detecting different intent under the same identity. Those choices matter because two identical payloads can represent two separate legitimate actions. [AWS safe retries and idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

The fixture scopes keys by `(tenant, owner, key)` and binds them to action kind, contract version and canonical validated input. A create-note fingerprint is based on `['create_note', 1, {'title': title}]`. A repeated key with another title or another action kind conflicts; an equivalent completed request returns its saved original result.

| Decision | Fixture policy | Why it matters |
| --- | --- | --- |
| Key origin | Caller-supplied identifier | Retry must retain it; a fresh key means a fresh operation |
| Scope | Tenant + owner | Other owners/tenants may use the same key independently |
| Equivalence | Kind + version + canonical request | Same key cannot silently change meaning |
| Atomicity | Effect, outbox intent and successful outcome share one transaction | No saved success without its effect |
| Concurrent duplicate | Writers serialize; second sees first outcome | No duplicate reservation/effect |
| Saved failure | Uncommitted failures are not retained | A later retry can succeed after rollback or changed availability |
| Retention | No expiry/deletion in this fixture | A deployed replay window needs an explicit lifecycle |

This is not payload-only deduplication. Alice may create two notes with the same title using two different keys. It is also not authentication: knowing a key does not authorize another tenant's operation.

The fixture stores successful outcomes only. An unavailable reservation raises and rolls back without permanently binding the key. If the product must replay terminal failures or reserve operation identity before long processing, add a durable pending/completed/failed state contract. Do not infer that behavior from this implementation.

---

## 6. Conditional writes, constraints, locks and isolation

| Mechanism | Useful invariant | Limitation or cost |
| --- | --- | --- |
| Conditional update | Decrement only if stock is sufficient; replace only at expected revision | Must check affected rows and handle conflicts |
| Unique constraint | One operation key, one event inbox record or one canonical identity | Does not by itself make separate effects atomic |
| CHECK constraint | Stored stock cannot be negative | A valid individual row may still violate a multi-row business rule |
| Row/pessimistic lock | Protect a read-decide-write sequence inside a transaction | Contention/deadlocks; keep transactions short |
| Optimistic version | Detect a stale writer without holding a long user-edit lock | Contended callers need bounded conflict resolution |
| Serializable transaction | Stronger protection for certain concurrent transaction anomalies | Engine-specific serialization failures can require whole-transaction retry |
| Distributed lease | Temporary coordination across workers | Expiry is not proof the old worker stopped; target must enforce effect safety |

PostgreSQL row locks persist for the transaction and can block conflicting operations. Isolation and lock behavior must be understood in that engine; deadlocks and serialization failures require deliberate retry handling, usually of the complete transaction. [PostgreSQL explicit locking](https://www.postgresql.org/docs/18/explicit-locking.html), [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html).

The SQLite fixture uses `BEGIN IMMEDIATE` to acquire the writer transaction before its read/modify sequence. SQLite allows only one writer at a time; this is not a demonstration of independent PostgreSQL row-level locks. Separate connections compete under SQLite's actual transaction rules. [SQLite transactions](https://sqlite.org/lang_transaction.html).

For scarce stock, the transition is:

```sql
UPDATE stock SET remaining = remaining - ?
WHERE tenant = ? AND item = ? AND remaining >= ?;
```

The conditional write, reservation record and operation outcome commit together. An application-level read of `remaining=1` followed by an unconditional decrement can race. A thread mutex in one API process would not protect another process's database connection.

---

## 7. Two callers: last-unit and duplicate-intent races

The harness starts two worker threads at a barrier. Each constructs and closes its own SQLite connection; connections are not shared between threads. The first scenario gives them different operation keys for one remaining unit.

```json
{
  "accepted": 1,
  "unavailable": 1,
  "remaining": 0,
  "reservations": 1,
  "independent_sqlite_connections": 2
}
```

One reservation commits and one request reports unavailable. Stock stays at zero and one reservation exists. The `CHECK(remaining>=0)` constraint supports the stored invariant, while the conditional update determines acceptance. Which owner wins is intentionally not asserted.

The second scenario gives both callers the same scoped key and intent against two available units:

```json
{
  "same_result": true,
  "replay_flags": [
    false,
    true
  ],
  "remaining": 1,
  "reservations": 1,
  "independent_sqlite_connections": 2
}
```

Both receive the same reservation outcome, exactly one is a replay, and stock is decremented once. An in-memory “seen keys” set would be lost at restart and would not coordinate independent application instances.

The third concurrent pair competes to claim one outbox item and produces one current owner/generation. All six worker calls finish before cleanup. These are real local two-connection races, not a multi-host load test or proof of another database's isolation semantics.

---

## 8. Durable work, queues and publish/subscribe

A work queue assigns a logical task to an eligible worker, with acknowledgement and retry/recovery semantics. Publish/subscribe lets multiple interested consumers make independent progress on an event. A single shared queue with competing consumers does not deliver every event to every business subscriber.

```text
Work queue:
task -> queue -> one of several eligible workers -> completed effect -> acknowledgement

Independent event subscribers:
NoteCreated -> indexing subscription -> indexing workers
            -> notifications subscription -> delivery workers
```

If both indexing and notifications must receive each event, design independent subscription/delivery state. The A3 outbox has one logical consumer path; adding a second competing worker does not create a second subscriber. Fan-out and per-subscriber retention are later design work.

Durable acceptance means the system has persisted enough intent to recover after process exit under its storage assumptions. An HTTP 202 or an async function alone does not establish that. Accepted work also needs a status/query contract, bounded backlog, ownership, expiry and an operational recovery path.

RabbitMQ distinguishes publisher confirms from consumer acknowledgements: confirmation of publication is not proof the consumer's business effect completed. A consumer should acknowledge according to its effect contract and configured durability guarantees. [RabbitMQ acknowledgements and confirms](https://www.rabbitmq.com/docs/confirms).

The fixture contains no broker. Its outbox row is a local durable delivery work item, and the harness directly calls a separate SQLite consumer before acknowledging that item. Real brokers add their own persistence, acknowledgement, redelivery, routing and operational semantics that require separate integration tests.

---

## 9. At-most-once, at-least-once and effect scope

| Claim | What must be specified | Typical failure consequence |
| --- | --- | --- |
| At-most-once delivery attempt | Which transport/stage suppresses redelivery | Work can be lost if failure happens after removal but before effect |
| At-least-once delivery | Retry/redelivery assumptions and retention/recovery owner | Duplicates are expected; consumers need effect safety |
| One local effect per event identity | Durable dedupe and effect share one atomic boundary | Limited to that store/effect and retention contract |
| End-to-end exactly once | Every source, transport, consumer and external effect boundary | Usually cannot be inferred from one queue setting or inbox table |

Do not acknowledge and then perform an unprotected effect if loss is unacceptable. Do not perform an effect and assume acknowledgement cannot be lost. The latter is why redelivery-safe consumers matter.

This fixture's automatic delivery attempts are bounded. An item can end in `dead` and require intervention; successful eventual delivery is not guaranteed without recovery and dependency assumptions. “We retry” is not a liveness proof.

The verified guarantee is narrow: for one valid event identity/payload, the consumer's inbox and local projection commit together, and repeated accepted delivery does not insert another projection. This says nothing about an email, external payment or model call made outside that transaction.

---

## 10. The transactional outbox and its remaining gap

Without an outbox, the application faces a dual-write gap:

```text
commit note -> stop before publishing -> note exists but event is absent
publish event -> note transaction fails -> downstream sees a note that never committed
```

An outbox stores canonical changes and publication/delivery intent in the same local transaction. A relay later sends the recorded intent and marks progress. Retrying that relay can duplicate delivery, so consumers still need an appropriate effect protocol. [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).

The fixture's create transaction writes:

```text
BEGIN IMMEDIATE
  find existing operation outcome or reject changed intent
  insert note
  insert NoteCreated outbox payload with stable event ID
  store original successful response
COMMIT
```

A fault after the note insert rolls everything back. A successful commit followed by close/reopen preserves the note, operation result and delivery intent. Retrying the create returns the original result without another event.

```json
{
  "replayed_after_reopen": true,
  "original_result": {
    "id": "id_3",
    "title": "Atomic note",
    "revision": 1
  },
  "notes": 1,
  "operation_outcomes": 1,
  "outbox_events": 1,
  "event_type": "NoteCreated"
}
```

Outbox creation closes the local commit/intent gap. It does not make a later network send and the source's `done` update atomic. Marking sent before durable acceptance risks loss; marking after acceptance leaves a possible duplicate on lost acknowledgement. The consumer inbox handles that specific second boundary for the local projection.

---

## 11. Worker claims, visibility, expiry and fencing

The outbox item has this durable state machine:

```text
ready --claim--> leased --acknowledge--> done
                   |
                   +--failed, attempts remain--> ready at a later due time
                   +--failed, limit reached----> dead
                   +--lease expires------------> reclaim with a higher generation,
                                                  or dead after final attempt
```

Each claim increments a stored generation and attempt count. Acknowledgement/reschedule requires the current worker, generation, leased state and an unexpired lease. A stale claim cannot change the source row after a replacement claims it.

Amazon SQS visibility timeouts similarly make received work temporarily unavailable and allow redelivery when it is not completed/deleted in time; visibility is not a guarantee against every duplicate. Engine-specific APIs and semantics differ from this local lease table. [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html).

Expiry does not stop the old worker's CPU or cancel a remote side effect. The generation here fences source acknowledgement/reschedule only. The consumer uses stable event identity for its local effect; it does not enforce arbitrary external fencing tokens. A general fencing design requires the resource accepting writes to reject older generations under a defined authority.

The fixture takes lease time from the harness. A deployed multi-worker design needs a consistent time authority and clock/expiry assumptions. It also needs renewal policy, deadlines, fairness, claim indexes and contention testing. No renewal API or claim-performance benchmark is implemented here.

Redis' distributed-lock guidance discusses ownership-safe release and validity assumptions. Those concerns reinforce why a random lock token, a lease duration and a monotonic fencing generation have different roles. This chapter does not implement or benchmark a Redis lock algorithm. [Redis distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/).

---

## 12. Runnable operation, outbox, lease and reservation source

Files are under `examples/system-design/module-3-reliable-workflows-concurrency/`. Three exact runnable source files are embedded. `workflow.py` uses explicit transactions with `isolation_level=None`; transaction ownership is visible instead of relying on implicit driver behavior. [Python sqlite3 transaction control](https://docs.python.org/3.12/library/sqlite3.html).

```python
"""Local durable operations/outbox/leases and scarce-stock transitions using SQLite."""
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4
import json
import math
import re
import sqlite3


class Conflict(Exception):
    pass


class Missing(Exception):
    pass


class Unavailable(Exception):
    pass


def identifiers(*values):
    if not all(type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) for value in values):
        raise ValueError('invalid identifier')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def fingerprint(value):
    return sha256(canonical(value).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Claim:
    tenant: str
    event_id: str
    worker: str
    generation: int
    payload: str
    lease_until: float
    attempt: int


class Workflow:
    def __init__(self, path, id_factory=lambda: str(uuid4())):
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.id_factory = id_factory
        self.db.executescript('''PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS notes (
            tenant TEXT NOT NULL, owner TEXT NOT NULL, id TEXT NOT NULL,
            title TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
            PRIMARY KEY(tenant,id)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS operations (
            tenant TEXT NOT NULL, owner TEXT NOT NULL, key TEXT NOT NULL,
            kind TEXT NOT NULL, fingerprint TEXT NOT NULL, response TEXT NOT NULL,
            PRIMARY KEY(tenant,owner,key)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS outbox (
            tenant TEXT NOT NULL, event_id TEXT NOT NULL, note_id TEXT NOT NULL,
            payload TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('ready','leased','done','dead')),
            due REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3, generation INTEGER NOT NULL DEFAULT 0,
            worker TEXT, lease_until REAL, PRIMARY KEY(tenant,event_id),
            FOREIGN KEY(tenant,note_id) REFERENCES notes(tenant,id)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS stock (
            tenant TEXT NOT NULL, item TEXT NOT NULL, remaining INTEGER NOT NULL CHECK(remaining>=0),
            PRIMARY KEY(tenant,item)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS reservations (
            tenant TEXT NOT NULL, id TEXT NOT NULL, owner TEXT NOT NULL, item TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity>0), state TEXT NOT NULL CHECK(state IN ('active','released')),
            PRIMARY KEY(tenant,id), FOREIGN KEY(tenant,item) REFERENCES stock(tenant,item)
          ) STRICT;''')

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def operation(self, tenant, owner, key, kind, request, action):
        identifiers(tenant, owner, key)
        digest = fingerprint([kind, 1, request])
        with self.transaction():
            old = self.db.execute('SELECT * FROM operations WHERE tenant=? AND owner=? AND key=?',
                                  (tenant, owner, key)).fetchone()
            if old:
                if old['kind'] != kind or old['fingerprint'] != digest:
                    raise Conflict('operation key reused with different intent')
                return json.loads(old['response']), True
            result = action()
            self.db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?)',
                            (tenant, owner, key, kind, digest, canonical(result)))
        return result, False

    def create_note(self, tenant, owner, key, title, fail_after_note=False):
        if type(title) is not str or not title.strip() or '\0' in title or len(title)>120:
            raise ValueError('invalid title')

        def action():
            note_id, event_id = self.id_factory(), self.id_factory()
            identifiers(note_id, event_id)
            self.db.execute('INSERT INTO notes VALUES(?,?,?,?,1)', (tenant, owner, note_id, title))
            if fail_after_note:
                raise RuntimeError('owned fault after note insertion')
            event = {'type': 'NoteCreated', 'schema': 1, 'tenant': tenant, 'owner': owner,
                     'event_id': event_id, 'note_id': note_id, 'title': title, 'revision': 1}
            self.db.execute('''INSERT INTO outbox(tenant,event_id,note_id,payload,state,due)
                               VALUES(?,?,?,?,'ready',0)''', (tenant, event_id, note_id, canonical(event)))
            return {'id': note_id, 'title': title, 'revision': 1}

        return self.operation(tenant, owner, key, 'create_note', {'title': title}, action)

    def claim(self, worker, now, lease=5):
        identifiers(worker)
        if not math.isfinite(now) or not math.isfinite(lease) or lease<=0:
            raise ValueError('finite clock and positive lease required')
        with self.transaction():
            self.db.execute('''UPDATE outbox SET state='dead',worker=NULL,lease_until=NULL
                WHERE state='leased' AND lease_until<=? AND attempts>=max_attempts''', (now,))
            row = self.db.execute('''SELECT * FROM outbox WHERE attempts<max_attempts AND
                ((state='ready' AND due<=?) OR (state='leased' AND lease_until<=?))
                ORDER BY due,tenant,event_id LIMIT 1''', (now, now)).fetchone()
            if row is None:
                return None
            generation, attempt = row['generation']+1, row['attempts']+1
            self.db.execute('''UPDATE outbox SET state='leased',worker=?,lease_until=?,
                generation=?,attempts=? WHERE tenant=? AND event_id=?''',
                (worker, now+lease, generation, attempt, row['tenant'], row['event_id']))
            return Claim(row['tenant'], row['event_id'], worker, generation, row['payload'], now+lease, attempt)

    def acknowledge(self, claim, now):
        if not math.isfinite(now):
            raise ValueError('finite clock required')
        with self.transaction():
            return self.db.execute('''UPDATE outbox SET state='done',worker=NULL,lease_until=NULL
                WHERE tenant=? AND event_id=? AND state='leased' AND worker=?
                AND generation=? AND lease_until>?''',
                (claim.tenant, claim.event_id, claim.worker, claim.generation, now)).rowcount == 1

    def fail(self, claim, now, delay=1):
        if not math.isfinite(now) or not math.isfinite(delay) or delay<0:
            raise ValueError('finite time and nonnegative retry delay required')
        with self.transaction():
            return self.db.execute('''UPDATE outbox SET state=CASE WHEN attempts>=max_attempts
                THEN 'dead' ELSE 'ready' END,due=?,worker=NULL,lease_until=NULL
                WHERE tenant=? AND event_id=? AND state='leased' AND worker=?
                AND generation=? AND lease_until>?''',
                (now+delay, claim.tenant, claim.event_id, claim.worker, claim.generation, now)).rowcount == 1

    def reserve(self, tenant, owner, key, item, quantity=1, fail_after_decrement=False):
        identifiers(item)
        if type(quantity) is not int or not 1 <= quantity <= 100:
            raise ValueError('quantity must be 1..100')

        def action():
            changed = self.db.execute('''UPDATE stock SET remaining=remaining-?
                WHERE tenant=? AND item=? AND remaining>=?''', (quantity, tenant, item, quantity)).rowcount
            if not changed:
                raise Unavailable('stock unavailable')
            if fail_after_decrement:
                raise RuntimeError('owned fault after stock decrement')
            identity = self.id_factory()
            identifiers(identity)
            self.db.execute("INSERT INTO reservations VALUES(?,?,?,?,?,'active')", (tenant, identity, owner, item, quantity))
            return {'reservation_id': identity, 'item': item, 'quantity': quantity}

        return self.operation(tenant, owner, key, 'reserve', {'item': item, 'quantity': quantity}, action)

    def release(self, tenant, owner, key, reservation_id):
        identifiers(reservation_id)

        def action():
            row = self.db.execute('SELECT * FROM reservations WHERE tenant=? AND owner=? AND id=?',
                                  (tenant, owner, reservation_id)).fetchone()
            if row is None:
                raise Missing('reservation not found')
            if row['state'] == 'active':
                self.db.execute("UPDATE reservations SET state='released' WHERE tenant=? AND id=?", (tenant, reservation_id))
                self.db.execute('UPDATE stock SET remaining=remaining+? WHERE tenant=? AND item=?',
                                (row['quantity'], tenant, row['item']))
            return {'reservation_id': reservation_id, 'state': 'released'}

        return self.operation(tenant, owner, key, 'release', {'reservation_id': reservation_id}, action)

    def close(self):
        self.db.close()
```

The internal `operation()` helper runs only local database changes in its action callback. Placing a provider call inside that callback would hold database locks and still not make the provider participate in the local transaction. The injected failure flags are private harness controls, not HTTP request options.

The relay claims in a short transaction, performs consumer delivery after the claim transaction has committed, then acknowledges using the current claim. The harness exercises those steps directly; there is no background daemon, polling scheduler or network transport in this fixture.

Operation rows and inbox rows have no retention/cleanup job. A deployed design must relate key retention to maximum retry/redelivery age, business lifecycle and storage/privacy rules. Deleting dedupe history can permit an old message to be interpreted as new. Deleting payloads also needs a deliberate delivery/recovery policy rather than an arbitrary TTL.

---

## 13. Runnable consumer inbox and effect

`consumer.py` owns a separate SQLite file with an inbox and a note-created projection. It checks event type/schema/fields, validates supplied identifiers, binds event identity to payload fingerprint and commits inbox/effect together.

```python
"""Separate durable inbox and local projection effect; no external provider involved."""
import json
import sqlite3
from workflow import Conflict, canonical, fingerprint, identifiers


class Consumer:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS inbox (
            tenant TEXT NOT NULL,event_id TEXT NOT NULL,fingerprint TEXT NOT NULL,
            PRIMARY KEY(tenant,event_id)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS projection (
            tenant TEXT NOT NULL,note_id TEXT NOT NULL,owner TEXT NOT NULL,
            title TEXT NOT NULL,revision INTEGER NOT NULL CHECK(revision>0),
            PRIMARY KEY(tenant,note_id)
          ) STRICT;
        ''')

    def accept(self, raw, fail_after_effect=False):
        event = json.loads(raw)
        fields = {'type', 'schema', 'tenant', 'owner', 'event_id', 'note_id', 'title', 'revision'}
        if type(event) is not dict or set(event) != fields or event['type'] != 'NoteCreated':
            raise ValueError('unsupported event contract')
        if type(event['schema']) is not int or event['schema'] != 1 or type(event['revision']) is not int or event['revision'] != 1:
            raise ValueError('unsupported schema or revision')
        identifiers(event['tenant'], event['owner'], event['event_id'], event['note_id'])
        if type(event['title']) is not str or not event['title'].strip() or '\0' in event['title'] or len(event['title'])>120:
            raise ValueError('invalid title')
        digest = fingerprint(event)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old = self.db.execute('SELECT fingerprint FROM inbox WHERE tenant=? AND event_id=?',
                                  (event['tenant'], event['event_id'])).fetchone()
            if old:
                if old['fingerprint'] != digest:
                    raise Conflict('event identity reused with different payload')
                replayed = True
            else:
                self.db.execute('INSERT INTO inbox VALUES(?,?,?)', (event['tenant'], event['event_id'], digest))
                self.db.execute('INSERT INTO projection VALUES(?,?,?,?,?)',
                    (event['tenant'], event['note_id'], event['owner'], event['title'], event['revision']))
                if fail_after_effect:
                    raise RuntimeError('owned fault after consumer effect')
                replayed = False
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
        return {'event_id': event['event_id'], 'replayed': replayed}

    def close(self):
        self.db.close()
```

The event schema accepts only version-1 `NoteCreated` at revision 1. It is not a general note-update handler, search indexer or ordered event log. A different event ID trying to create an already existing note projection can fail its unique key rather than silently replacing newer data.

In a larger projection, carry aggregate identity/version and define duplicate, stale, gap and reorder behavior. For delta events such as “add 10 credits,” deduplication alone does not establish business ordering or conflict policy. For replacement snapshots, rejecting older aggregate versions can be useful, but that protocol is not implemented by this create-only consumer.

The trusted local relay supplies the tenant/owner-bearing event. Schema validation does not authenticate the publisher or authorize arbitrary callers to mutate projections. A networked consumer needs source/service authentication, tenant routing and appropriate permissions before accepting that context.

---

## 14. Recovery after effect commit and lost acknowledgement

The central failure drill is:

```text
source claims event at generation 1
consumer commits inbox + projection
relay omits acknowledgement (controlled interruption boundary)
both database connections close/reopen
lease expires -> another worker claims same event at generation 2
consumer recognizes same event/payload -> returns replay result
old generation cannot acknowledge or reschedule source
new generation acknowledges -> source state done
```

Observed result:

```json
{
  "first_generation": 1,
  "recovered_generation": 2,
  "same_event_id": true,
  "consumer_replayed": true,
  "inbox_records": 1,
  "projection_effects": 1,
  "source_state": "done",
  "crash_boundary": "consumer committed; source acknowledgement omitted"
}
```

The harness also injects a failure after the consumer projection insert but before commit. Both inbox and projection roll back, so a later delivery can perform the effect normally. A “seen event” marker committed separately from its effect would leave a loss window instead.

This drill uses deliberate exceptions/omitted steps and real persistent reopen, not an actual process kill, power loss or network packet fault. It supports the stated application transaction/replay behavior. Durability under machine/storage failure requires engine configuration, deployment assumptions and separate fault testing.

The old worker is rejected at the source, but the code cannot physically stop its external work. Stable event identity protects the particular consumer projection. For a real charge or webhook delivery, the provider/receiver must participate through its own idempotency/status protocol or the workflow must keep an unknown outcome and reconcile.

---

## 15. Attempt limits, poison work and dead-letter recovery

An attempt count, due time and terminal state bound automatic retry. They do not repair the underlying failure. The fixture reschedules a failed claim, waits until its recorded due time, rejects acknowledgement at lease expiry and eventually records `dead` after three claims.

```json
{
  "attempts": 3,
  "retry_due": 4,
  "ack_at_expiry_accepted": false,
  "terminal_state": "dead",
  "automatic_retry_after_dead": false
}
```

`dead` means automatic processing stopped. It does not prove the downstream effect never happened: the final worker might have committed the consumer effect before losing its acknowledgement. Inspect receiver state by stable identity before deciding to replay, compensate or mark success.

A useful recovery record includes safe error category, attempt history, relevant IDs, first/last failure time and required action. Avoid storing credentials or unrestricted private payloads in diagnostics. A4 develops telemetry/permissions; this fixture retains basic state and counters rather than a complete operational audit trail.

Replay from quarantine should preserve event/operation identity when repeating the same intent. Changing a poison payload under an existing event ID conflicts with this consumer's fingerprint contract. A corrected event may need a new identity and a deliberate business repair protocol; blindly resetting attempts is not enough.

Bound worker concurrency and downstream calls. A retry delay can spread work while backlog still grows if arrival exceeds effective completion rate. Track oldest pending age, ready/leased/dead counts, attempts, lease expiry and consumer completion separately from merely counting HTTP 200 responses.

---

## 16. Sagas, compensation and unknown outcomes

A saga coordinates a sequence of local commits across independently owned steps. If later steps fail, it may run business compensations rather than a database rollback spanning every participant. Orchestration uses an explicit coordinator; choreography uses reacting participants and events. Both require durable progress, idempotent steps and a recovery owner. [AWS saga orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html).

Compensation is a new business action. It may not restore the exact past: an email cannot be unsent, a shipment may already have left, a refund can fail or take time, and another customer may take released inventory. Compensation itself must be retryable and observable. [Microsoft compensating transactions](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction).

The fixture demonstrates one local compensating action. Reserve creates an active reservation and reduces stock. Release changes it to `released` and restores stock in one transaction. Repeating the same release key returns the saved outcome; even a different release key cannot restore stock a second time because the reservation is already released.

```json
{
  "original_stock": 2,
  "after_reserve": 1,
  "after_repeated_release": 2,
  "reservation_state": "released",
  "same_key_replayed_after_reopen": true,
  "external_payment_refund_executed": false
}
```

This is not a complete booking/payment saga. It has no holds/expiry, provider request, refund, coordinator table or reconciliation worker. Those belong in later worked systems. The implemented action shows why business state guards matter in addition to deduplicating one request key.

Example proposed coordinator states, not executed here:

```text
new -> reserved -> payment_pending -> completed
                          |
                          +--payment_unknown -> reconcile status
                          +--definitive failure -> release_pending -> released
```

If payment is unknown, do not immediately assume failure and release while a charge may complete. The coordinator must resolve or explicitly manage that ambiguity. Compensation and reconciliation have distinct roles: one requests a corrective action; the other compares authoritative outcomes and repairs unresolved state.

---

## 17. Verification, ordering and production boundaries

Verified on **2026-10-16** using **Python 3.12.10**, **SQLite 3.49.1**, and **Windows 11**. No third-party packages, broker, Redis, Docker, external provider, credentials or listener are required.

From the repository root in PowerShell:

```powershell
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 'examples/system-design/module-3-reliable-workflows-concurrency/verify.py'
```

Or run `python verify.py` from the example directory with Python 3.12 or later. Each run uses an owned temporary directory, source/consumer SQLite files and six completed concurrent worker calls; connections close before the directory is removed. Port 3000 is not used.

**90 local checks passed:** 19 retry policy, 14 atomic operations, 10 leases, 12 consumer atomicity, 11 delivery bounds, 10 concurrency, 12 compensation, 2 cleanup. Three exact sources and eight exact observation blocks are embedded; `verification-results.json` contains every named assertion.

| Evidence | What it establishes | What remains outside scope |
| --- | --- | --- |
| Injected-clock retry transport | Classification, attempts, delay/deadline decisions | Real network timeout/cancellation or provider latency |
| Note/outcome/outbox transaction | Local commit and replay consistency, rollback on controlled fault | Broker publication/replication or machine-failure durability |
| Separate inbox/effect database | Redelivery-safe local projection and reopen recovery | External email/payment effects or global exactly-once processing |
| Lease generations | Source ownership checks and expiry/reclaim/attempt states | Stopping stale worker CPU or fencing an arbitrary external resource |
| Two-connection races | SQLite acceptance/dedupe/claim invariants | PostgreSQL row-lock behavior, multi-host contention or capacity |
| Released reservation state | Local compensation cannot restore stock twice | Complete distributed saga, refunds or booking expiry |

The outbox's due-time ordering is a claim preference, not a global business-event order. Workers can take different amounts of time, events can retry and independent tenants can interleave. If per-aggregate ordering is required, define aggregate sequence, partition/subscription ownership and gap handling; broker FIFO or a timestamp alone is not a complete application protocol.

Before deploying an analogous system, add actual transport contracts, authentication/tenant routing, deadline propagation, backpressure, due/claim indexes, retention/recovery tooling, observability and realistic fault tests. These are concrete next requirements, not features verified by the small local example.

---

## 18. Common interview questions with answer checkpoints

### Q1. Does a timeout mean the operation failed?

No. The effect may have committed and its response may be lost, or work may still be running. Retain the same operation identity and use the API's replay/status protocol. A new key can create a second legitimate operation rather than recover the first.

### Q2. Deadline versus per-attempt timeout?

A deadline bounds the whole caller operation; a timeout bounds an individual attempt or phase. Compute remaining time before retry/backoff and pass it to a transport that enforces it. Checking time between calls cannot interrupt an unbounded blocking call.

### Q3. Which failures should be retried?

Those classified as transient under a retry-safe operation contract and a bounded budget. Validation/authentication, version conflict, overload and unknown provider outcomes need different policies. Do not retry every exception or assume all 5xx responses have harmless effects.

### Q4. Why backoff and jitter?

Backoff reduces immediate repeated demand; jitter spreads correlated retries. Neither repairs invalid input, guarantees eventual success or prevents overload alone. The local example uses injected deterministic fractions and an attempt/deadline bound rather than measuring real retry traffic.

### Q5. How can retries amplify an outage?

Multiple independently retrying layers multiply downstream attempts, and failed work consumes more resources. Five layers allowing three attempts can reach 243 leaf calls. Coordinate recovery at a deliberate boundary and cap total retry/admission demand.

### Q6. What makes a create operation idempotent?

A stable scoped intent identity, defined input equivalence and an atomic effect plus durable saved outcome. The note, original response and outbox intent commit together here. Repeating that key/input after reopen returns the same original result.

### Q7. Why not deduplicate by payload hash alone?

Two identical payloads can represent two intended actions. A caller-provided operation key distinguishes them, while a fingerprint detects changed intent under one key. Scope the key to its tenant/owner and action contract.

### Q8. What if a key is reused with different input?

Reject it under a documented equivalence policy. Returning an unrelated old success would hide a bug or mix intents. The fixture also rejects switching from reserve to release under the same scoped key.

### Q9. How do concurrent retries avoid duplicate effects?

They coordinate through the authoritative transactional/unique-key boundary. One caller commits; the next sees its outcome. The two-connection reservation retry returns one new result and one replay, with a single stock decrement.

### Q10. How long should idempotency records live?

Long enough for the advertised retry/redelivery/business lifecycle, with explicit storage/privacy policy. Expiring a record can allow an old key to act as new. This fixture has no expiry and saves successful outcomes only; it does not guarantee replay of terminal failures.

### Q11. How do you prevent two callers buying the last unit?

Keep acceptance authoritative and atomic, such as a conditional decrement checking sufficient stock, plus the reservation/outcome in the same transaction. A separate stale read or process-local lock is insufficient across database clients.

### Q12. Optimistic version check or pessimistic lock?

Choose from contention, transaction duration and the invariant. Expected revisions suit stale-edit detection; row locks can protect a short read-decide-write sequence. Both need conflict/deadlock handling and neither should be held across arbitrary user/provider wait time.

### Q13. Does a unique constraint replace a transaction?

No. It protects a uniqueness invariant, but separate balance/stock/effect writes can still partially commit. Couple the relevant state changes and outcome record inside the correct transaction, then handle constraint conflicts deliberately.

### Q14. What should you retry after a serialization failure?

The complete transaction according to the engine's documented semantics, with fresh reads and a bounded policy. Retrying only the final statement can reuse invalid decisions. The SQLite fixture does not demonstrate PostgreSQL serialization behavior.

### Q15. Work queue or publish/subscribe?

Use competing workers for one logical task; use independent subscriptions when multiple capabilities must each process an event. A shared queue with two worker types does not broadcast every event to both. A3 implements one direct consumer path only.

### Q16. Publisher confirm versus consumer acknowledgement?

They refer to different delivery stages. Publication confirmation does not establish that a consumer's business effect committed. Define which durable boundary each acknowledgement represents and what a lost response implies.

### Q17. At-most-once versus at-least-once?

At-most-once can lose work if completion is assumed too early; at-least-once retries can duplicate delivery. Specify the transport/effect scope and recovery assumptions. Bounded attempts ending in dead state do not guarantee eventual business completion.

### Q18. Does an inbox table give end-to-end exactly once?

Only the atomic inbox/local-effect boundary is protected here. A separate provider call can still happen twice or remain unknown. Name the actual effect and storage/retention scope instead of claiming a global exactly-once guarantee.

### Q19. Why use a transactional outbox?

It records canonical change and delivery/publication intent in one local transaction, closing the commit/intent dual-write gap. A relay retries later. The send/acknowledgement gap still exists and requires downstream effect safety.

### Q20. What if the relay stops after delivery but before acknowledgement?

The lease expires, the same event is reclaimed and delivery repeats. The consumer's durable inbox recognizes the same event/payload and avoids repeating its local projection. The harness closes/reopens both databases to verify this path.

### Q21. Why commit inbox and effect together?

Committing a seen marker first can suppress unfinished work after a failure. Committing only the effect first can repeat it after redelivery. The fixture's controlled fault after effect insertion rolls both back before a later successful delivery.

### Q22. Is lease expiry proof the old worker stopped?

No. It permits a replacement claim but the old process may continue or resume. The source checks generation/owner/expiry before accepting its acknowledgement. External resources still need idempotency or a target-enforced fencing protocol.

### Q23. What is a fencing token?

A generation/order value whose authority is enforced by the resource accepting effects, rejecting stale owners. Merely attaching a number to a request is insufficient. A3's generation fences source state transitions; its consumer effect uses event deduplication instead.

### Q24. Why not hold a SQL transaction during delivery?

It prolongs locks and connection occupancy while the remote system still remains outside the transaction. Claim locally, commit, perform delivery, then record progress with ownership checks. Handle ambiguous downstream outcomes explicitly.

### Q25. What should happen to poison work?

Classify the problem, bound automatic attempts, quarantine with safe diagnostics and provide an operator/recovery path. Infinite requeueing can starve healthy work. A dead state may coexist with an already applied downstream effect, so inspect by stable identity.

### Q26. Does queue ordering mean effects finish in order?

Not necessarily. Parallel workers, retry delays and independent partitions can reorder completion. Define per-aggregate sequence/version and gap handling if the business requires order. The create-only fixture does not implement a general ordered projection protocol.

### Q27. What is a saga?

A coordinated sequence of local commits with business recovery/compensation when needed. It requires durable progress and an owner for unresolved steps. An outbox can support messages between participants but does not by itself implement a saga coordinator.

### Q28. Is compensation the same as rollback?

No. Compensation is a new business action after an earlier commit and may not restore the exact past. The fixture's release restores stock once under an active-to-released guard; it does not undo an email, external charge or shipment.

### Q29. How do you handle an unknown payment outcome?

Keep stable provider identity and an explicit pending/unknown state, then reconcile through authoritative lookup/callbacks. Do not assume timeout means failure, create a fresh charge blindly or release inventory as if payment definitively failed. No payment is executed by this fixture.

### Q30. What does A3 actually verify?

Local SQLite atomic/replay/claim/inbox/compensation behavior, reopen recovery, two-connection races and injected-clock retry decisions. It does not prove broker/provider semantics, process-kill/storage-failure durability, PostgreSQL isolation, multi-host fencing, a full saga or production capacity.

---

## 19. Revision sheet and a 45-minute mock

| Prompt | Recall |
| --- | --- |
| Timeout | Result unknown; effect may have committed |
| Retry | Classify + safe identity + deadline/attempt budget + backoff/jitter |
| Idempotency | Scoped key + equivalence + atomic effect/outcome + retention |
| Concurrency | Put the guard in the authoritative state transition |
| Constraint | Protects its invariant; not a substitute for multi-effect atomicity |
| Outbox | Canonical change + delivery intent commit together |
| Inbox | Dedupe + local effect commit together |
| Lease | Temporary ownership; stale work can continue |
| Fencing | Target enforces ownership generation, with a defined authority |
| Dead work | Automatic attempts stopped; effect may still need reconciliation |
| Compensation | New business action, retryable and state guarded |
| Evidence | Real local SQLite and controlled failure boundaries; no deployed provider/broker |

**Mock prompt:** “A private-note create must eventually update a derived view. Clients retry after timeouts and workers can stop anywhere. Explain correctness, delivery and recovery. Then add a limited-stock reservation followed by an uncertain payment step.”

| Segment | Minutes |
| --- | --- |
| Define effects, invariants and completion promises | 6 |
| Design scoped operation identity and transaction | 8 |
| Trace outbox, consumer and lost acknowledgement | 10 |
| Explain competing writes, leases and stale workers | 8 |
| Discuss deadline budgets and compensation/unknown state | 8 |
| Recap evidence and recovery owner | 5 |
| **Total** | **45** |

A defensible short answer:

> The create request retains a tenant/owner-scoped operation key across retries. One local transaction stores the note, original result and outbox intent. A relay claims work briefly, delivers outside the source transaction and acknowledges only its current lease generation. The consumer commits its inbox and local projection together, so delivery after a lost acknowledgement is safe for that effect. Attempts and deadlines are bounded; dead work has a recovery owner. Stock acceptance uses a conditional authoritative write. A later payment timeout remains unknown until reconciled; compensation is a guarded business action rather than an assumption that the earlier commit never happened.

Check whether your answer addressed the gap after each commit, distinguished source acknowledgement from downstream effect, bounded retries and avoided claiming that a lease physically stops an old worker.

---

## 20. Practice tasks

1. Draw a create timeline with failure before transaction, after note insert, after commit and after response transmission. State the persisted data and retry result at each point.
2. Run the retry tests. Change total/per-attempt budgets and jitter fractions; explain why time spent in calls and sleeps must share the caller's deadline.
3. Reproduce create replay after reopen and a changed-input conflict. Explain the action/version fingerprint, scope and successful-outcome-only policy.
4. Trace the two last-unit requests and concurrent duplicate reservation requests. Identify the conditional write, unique key and transaction boundary for each invariant.
5. Reproduce the consumer fault after effect insertion. Explain what would go wrong if inbox and effect committed separately.
6. Walk through commit-without-ack recovery. Confirm the stable event ID, higher claim generation, consumer replay and single projection effect.
7. Test an expired/old/wrong-worker acknowledgement and explain why rejecting it does not stop an old external side effect.
8. Design dead-work recovery with safe diagnostics, a replay/status check, identity preservation and escalation. Include a final-attempt effect that succeeded before acknowledgement was lost.
9. Outline a durable reservation/payment coordinator with unknown state and idempotent compensation. Mark the unimplemented provider, hold expiry, refund and reconciliation mechanisms.
10. Complete the 45-minute mock and answer architecture-bank Q16–Q22. Name each verified local guarantee and the production evidence still required.

---

## 21. Completion checklist

- [ ] I can explain why a timeout leaves the effect uncertain.
- [ ] I can budget attempts/backoff under an end-to-end deadline.
- [ ] I can classify retry-safe and terminal outcomes.
- [ ] I can explain scoped keys, equivalence and retention.
- [ ] I can trace an atomic effect/outcome/outbox transaction.
- [ ] I can explain the real last-unit and duplicate-intent races.
- [ ] I can distinguish work queues, subscriptions and acknowledgement stages.
- [ ] I can trace inbox/effect atomicity and lost-acknowledgement recovery.
- [ ] I can explain expiry, claim generations and their fencing limits.
- [ ] I can bound automatic attempts and define dead-work recovery.
- [ ] I can distinguish compensation, rollback and reconciliation.
- [ ] I can state evidence limits and complete a timed workflow mock.

---

## 22. Research references and continuation

Primary references reviewed on 2026-10-16. The code, scenarios and interview questions are authored teaching material. The references support named mechanisms and limits; they do not prescribe this complete fixture or establish company question frequency.

| Primary source | Relevant boundary |
| --- | --- |
| [AWS timeouts/retries/jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Bounded dependency calls, retry load and timing |
| [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | Caller identity and detecting changed intent |
| [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | Atomic local intent plus later delivery and duplicates |
| [PostgreSQL locking](https://www.postgresql.org/docs/18/explicit-locking.html) | Transaction-scoped locks and deadlocks |
| [PostgreSQL isolation](https://www.postgresql.org/docs/18/transaction-iso.html) | Concurrent transaction semantics and retryable conflicts |
| [PostgreSQL SELECT](https://www.postgresql.org/docs/18/sql-select.html) | Locking clauses and queue-oriented `SKIP LOCKED` trade-offs |
| [SQLite transactions](https://sqlite.org/lang_transaction.html) | Actual local writer/transaction behavior |
| [Python sqlite3](https://docs.python.org/3.12/library/sqlite3.html) | Explicit transaction control and connection ownership |
| [RabbitMQ acknowledgements/confirms](https://www.rabbitmq.com/docs/confirms) | Publication and consumption acknowledgement stages |
| [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) | Temporary invisibility and redelivery |
| [Redis distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/) | Lock ownership and validity assumptions |
| [AWS saga orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html) | Coordinated local steps and recovery |
| [Microsoft compensation](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) | Business undo limits and retryable correction |

For a PostgreSQL worker, `FOR UPDATE SKIP LOCKED` can avoid waiting on rows another worker locked, but its inconsistent view is suited to queue-style access rather than arbitrary business reads. It still needs an atomic claim/ownership update and crash recovery. This fixture does not execute that PostgreSQL pattern. [PostgreSQL locking clauses](https://www.postgresql.org/docs/18/sql-select.html).

Return to the [architecture roadmap](/docs/system-design), [A1: Application architecture](/docs/system-design/application-architecture-service-boundaries) or [A2: Data/caching](/docs/system-design/data-caching-scaling). Resume [M9](/docs/resume-skills/webhooks-payments-reliable-integrations), [M13](/docs/resume-skills/postgresql-backend), [M15](/docs/resume-skills/caching-background-jobs-data-ingestion) and [M19](/docs/resume-skills/git-ci-cd-testing-observability-performance) provide stack/integration refreshers.

**Next: [A4 — Operating a secure and observable system](/docs/system-design/secure-observable-operations)**, architecture part 6 / numeric module 4. It connects tenant scope, least privilege, quotas, safe uploads, readiness/draining, telemetry, SLOs and capacity evidence. A4 is now available with its own local HTTP and offline-indicator verification scope. The worked systems start with S0 after the foundations.
