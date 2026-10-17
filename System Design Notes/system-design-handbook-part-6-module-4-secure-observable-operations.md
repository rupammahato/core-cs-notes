# Architecture and System Design Placement Handbook — Part 6
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

```json
{
  "owned_note": 200,
  "other_owner": 404,
  "spoofed_headers": 404,
  "read_only_upload": 403,
  "revoked_membership": 403,
  "same_id_other_tenant_title": "PRIVATE_BETA_NOTE"
}
```

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

```json
{
  "limit_per_tenant_per_10_seconds": 2,
  "before_boundary_statuses": [
    200,
    200,
    429
  ],
  "after_boundary_statuses": [
    200,
    200
  ],
  "accepted_near_boundary": 4,
  "retry_after_seconds": 1
}
```

Two requests just before a boundary and two just after it can be accepted in a short interval. That is the fixed-window algorithm's boundary burst, not an implementation bug. A sliding window or token bucket provides a different contract; S1 will build those mechanisms.

Observed final-slot race:

```json
{
  "independent_connections": 2,
  "statuses": [
    200,
    429
  ],
  "stored_used": 1
}
```

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

```json
{
  "accepted_state": "pending",
  "before_approval": 409,
  "after_approval": 200,
  "other_tenant": 404,
  "invalid_text_state": "rejected",
  "tampered_bytes_state": "rejected",
  "over_byte_budget": 429,
  "retained_bytes": 1055,
  "antivirus_executed": false
}
```

The bytes and SQLite metadata are two storage systems. The normal exception path removes a file when its metadata transaction rolls back, but a process/storage failure between writing bytes and committing metadata can leave an orphan. No process-kill cleanup/reconciliation protocol is implemented. A deployed upload service needs durable staging/completion, orphan detection, retention and safe deletion; S3 develops that separate system.

Retained rejected/pending objects still consume this fixture's storage quota. The code has no cleanup/deletion API, multipart upload, presigned object URL, executable preview, archive decompression or malware sandbox. Those require their own limits and lifecycle rather than extending the `.txt` checker by assumption.

---

## 7. Runnable policy, quota and quarantine source

Files live under `examples/system-design/module-4-secure-observable-operations/`. Three exact runnable source files are embedded. `policy.py` owns current membership, scoped reads, transactional quotas and upload metadata/private files.

```python
"""Scoped SQLite policies and private text-upload quarantine; trusted lesson principals."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from threading import RLock
from uuid import uuid4
import math
import re
import sqlite3


class Denied(Exception):
    def __init__(self, status, code, retry_after=None):
        self.status, self.code, self.retry_after = status, code, retry_after
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    tenant: str
    user: str


# Published lesson credentials, NOT production authentication.
TOKENS = {'lesson-alice': Principal('alpha', 'alice'), 'lesson-bob': Principal('alpha', 'bob'),
          'lesson-viewer': Principal('alpha', 'eve'), 'lesson-beta': Principal('beta', 'alice')}


class Store:
    def __init__(self, database, vault):
        self.db = sqlite3.connect(database, timeout=5, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = RLock()  # Prevent interleaved use of this connection by HTTP threads.
        self.vault = Path(vault).resolve()
        self.vault.mkdir(exist_ok=True)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS members(tenant TEXT,user TEXT,role TEXT,active INTEGER,
            PRIMARY KEY(tenant,user));
          CREATE TABLE IF NOT EXISTS notes(tenant TEXT,owner TEXT,id TEXT,title TEXT,
            PRIMARY KEY(tenant,id));
          CREATE TABLE IF NOT EXISTS quota(tenant TEXT,action TEXT,window INTEGER,used INTEGER CHECK(used>=0),
            PRIMARY KEY(tenant,action,window));
          CREATE TABLE IF NOT EXISTS uploads(tenant TEXT,owner TEXT,id TEXT,name TEXT,size INTEGER,
            digest TEXT,state TEXT CHECK(state IN ('pending','ready','rejected')),PRIMARY KEY(tenant,id));
        ''')

    def seed(self):
        with self.lock:
            self.db.executemany('INSERT INTO members VALUES(?,?,?,1)',
                [('alpha','alice','editor'), ('alpha','bob','editor'), ('alpha','eve','viewer'), ('beta','alice','editor')])
            self.db.executemany('INSERT INTO notes VALUES(?,?,?,?)',
                [('alpha','alice','shared_id','PRIVATE_ALPHA_NOTE'), ('alpha','bob','bob_note','PRIVATE_BOB_NOTE'),
                 ('beta','alice','shared_id','PRIVATE_BETA_NOTE')])

    def authorize(self, principal, action):
        with self.lock:
            row = self.db.execute('SELECT role,active FROM members WHERE tenant=? AND user=?',
                                  (principal.tenant, principal.user)).fetchone()
            allowed = {'viewer': {'read'}, 'editor': {'read', 'upload'}}
            if row is None or row['active'] != 1 or action not in allowed.get(row['role'], set()):
                raise Denied(403, 'forbidden')

    def note(self, principal, identity):
        with self.lock:
            self.authorize(principal, 'read')
            row = self.db.execute('SELECT id,title FROM notes WHERE tenant=? AND owner=? AND id=?',
                                 (principal.tenant, principal.user, identity)).fetchone()
            if row is None:
                raise Denied(404, 'not_found')
            return dict(row)

    def listing(self, principal):
        with self.lock:
            self.authorize(principal, 'read')
            return [dict(row) for row in self.db.execute('SELECT id,title FROM notes WHERE tenant=? AND owner=? ORDER BY id LIMIT 20',
                (principal.tenant, principal.user))]

    def take_quota(self, principal, action, now, limit=1000, seconds=10):
        if not math.isfinite(now) or now<0 or type(limit) is not int or limit<1 or type(seconds) is not int or seconds<1:
            raise ValueError('invalid quota configuration')
        window = math.floor(now/seconds)
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                self.db.execute('DELETE FROM quota WHERE window<?', (window-1,))
                self.db.execute('INSERT OR IGNORE INTO quota VALUES(?,?,?,0)', (principal.tenant, action, window))
                changed = self.db.execute('UPDATE quota SET used=used+1 WHERE tenant=? AND action=? AND window=? AND used<?',
                    (principal.tenant, action, window, limit)).rowcount
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise
        if not changed:
            raise Denied(429, 'quota_exceeded', max(1, math.ceil((window+1)*seconds-now)))

    def stage(self, principal, name, mime, body, byte_budget=2048):
        self.authorize(principal, 'upload')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_. -]{0,63}\.txt', name) or '..' in name:
            raise Denied(400, 'invalid_filename')
        if mime != 'text/plain':
            raise Denied(415, 'text_required')
        if not 1 <= len(body) <= 1024:
            raise Denied(413, 'invalid_upload_size')
        identity = uuid4().hex
        path = self.vault/identity  # No user path or original filename is used for storage.
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                self.authorize(principal, 'upload')
                retained = self.db.execute('SELECT coalesce(sum(size),0) FROM uploads WHERE tenant=?', (principal.tenant,)).fetchone()[0]
                if retained+len(body)>byte_budget:
                    raise Denied(429, 'storage_quota_exceeded')
                with path.open('xb') as file:
                    file.write(body)
                self.db.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?,?)',
                    (principal.tenant, principal.user, identity, name, len(body), sha256(body).hexdigest(), 'pending'))
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                path.unlink(missing_ok=True)
                raise
        return {'id': identity, 'state': 'pending'}

    def approve(self, tenant, identity):
        # Internal validator; no public approval route. NOT an antivirus scanner.
        with self.lock:
            row = self.db.execute('SELECT * FROM uploads WHERE tenant=? AND id=?', (tenant, identity)).fetchone()
            if row is None:
                raise Denied(404, 'not_found')
            if row['state'] != 'pending':
                return row['state']
            body = (self.vault/row['id']).read_bytes()
            valid = len(body) == row['size'] and sha256(body).hexdigest() == row['digest']
            try:
                text = body.decode('utf-8', errors='strict')
                valid = valid and '\0' not in text
            except UnicodeDecodeError:
                valid = False
            state = 'ready' if valid else 'rejected'
            self.db.execute('UPDATE uploads SET state=? WHERE tenant=? AND id=?', (state, tenant, identity))
            return state

    def download(self, principal, identity):
        with self.lock:
            self.authorize(principal, 'read')
            row = self.db.execute('SELECT * FROM uploads WHERE tenant=? AND owner=? AND id=?',
                (principal.tenant, principal.user, identity)).fetchone()
            if row is None:
                raise Denied(404, 'not_found')
            if row['state'] != 'ready':
                raise Denied(409, 'upload_not_ready')
            return row['name'], (self.vault/row['id']).read_bytes()

    def close(self):
        self.db.close()
```

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

```json
{
  "initial_ready": 200,
  "dependency_unready": 503,
  "liveness_during_dependency_failure": 200,
  "over_capacity": 503,
  "new_work_during_drain": 503,
  "already_accepted_work": 200,
  "active_after_drain": 0,
  "operating_system_signal_sent": false
}
```

No operating-system termination signal is sent. The test calls the application drain method and then closes its owned servers/threads. It demonstrates the application policy; signal wiring, load-balancer propagation, keep-alive behavior, HTTP/2 streams, WebSockets and forced termination are separate deployment work.

For background work, draining also means stop new claims and decide whether accepted jobs finish, release safely or recover after lease expiry. Never assume a shutdown hook makes every external effect unambiguous; A3's operation identity and recovery still matter.

Use compatible schema evolution for rolling deployments: expand supported fields/schema, deploy readers/writers that tolerate the transition, migrate/backfill, verify, then contract obsolete behavior when safe. A code rollback cannot always reverse an irreversible data migration. The fixture does not perform a rolling release or migration benchmark.

---

## 10. Admission control and the overload experiment

An active-work gate accepts only a bounded number of application requests. It makes overload explicit instead of allowing an unbounded work queue to accumulate until memory, sockets or database connections are exhausted.

The controlled saturation experiment admits two requests and holds them at a test barrier, offers six more, then releases the first two:

```json
{
  "offered_requests": 8,
  "accepted_completed": 2,
  "overload_responses": 6,
  "peak_active_application_work": 2,
  "test_shape": "two accepted requests held; six excess requests offered; then release",
  "throughput_capacity_measured": false
}
```

This demonstrates two accepted completions, six explicit overload responses and a peak active-work count of two. It does not establish a sustainable QPS, p99 latency at a realistic workload or the maximum connections the machine can handle. The artificial barrier intentionally creates saturation.

The standard-library threaded server can create handler threads before this gate runs, so the gate bounds application work, not all accepted sockets/threads. A production edge/server still needs connection, header/body, worker/thread and queue bounds. The three-second socket timeout in the lesson is not an end-to-end request deadline.

Load shedding should preserve a useful service contract. Distinguish business quota, shared overload, unavailable dependencies and deliberate drain. Do not quietly report rejected eligible requests as successful service availability; the SLI policy must account for them.

---

## 11. Runnable HTTP lifecycle and diagnostic source

`server.py` binds only to loopback on an ephemeral port. It generates its own correlation ID, maps credentials, checks current policy, consumes scoped quota, performs bounded application work and writes selected diagnostics. Health routes expose minimal state and bypass business admission.

```python
"""Owned loopback HTTP lesson; Python http.server is not a production web server."""
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Condition
from time import perf_counter, time
from urllib.parse import urlsplit
from uuid import uuid4
import json

from policy import Denied, TOKENS


class Runtime:
    def __init__(self, capacity=2):
        self.condition = Condition()
        self.started = self.database_available = True
        self.draining = False
        self.active, self.peak, self.capacity = 0, 0, capacity
        self.logs, self.traces = deque(maxlen=128), deque(maxlen=128)
        self.counts = Counter()
        self.hold = None  # Owned test barrier, never exposed as a request parameter.

    def ready(self):
        with self.condition:
            return self.started and self.database_available and not self.draining

    def enter(self):
        with self.condition:
            if not self.ready():
                raise Denied(503, 'not_ready')
            if self.active >= self.capacity:
                raise Denied(503, 'overloaded', 1)
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.condition.notify_all()

    def leave(self):
        with self.condition:
            self.active -= 1
            self.condition.notify_all()

    def drain(self):
        with self.condition:
            self.draining = True
            self.condition.notify_all()

    def record(self, trace_id, method, route, status, elapsed, events):
        with self.condition:
            self.counts[(method, route, str(status//100)+'xx')] += 1
            self.logs.append({'trace_id': trace_id, 'method': method, 'route': route,
                              'status': status, 'duration_ms': round(elapsed*1000, 3)})
            self.traces.append({'trace_id': trace_id, 'events': events})


def make_server(store, runtime, clock=time, quota_limit=1000):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Suppress standard raw-URL/header logging; structured records below.

        def handle_request(self):
            start, trace_id, events = perf_counter(), uuid4().hex, ['http.received']
            path = urlsplit(self.path).path
            route = '/unmatched'
            if path in ('/livez', '/readyz', '/notes', '/uploads'):
                route = path
            elif path.startswith('/notes/'):
                route = '/notes/:id'
            elif path.startswith('/uploads/'):
                route = '/uploads/:id'
            status, headers, body, entered = 500, {}, {'error': 'internal_error'}, False
            try:
                if path == '/livez' and self.command == 'GET':
                    status, body = 200, {'alive': True}
                elif path == '/readyz' and self.command == 'GET':
                    status = 200 if runtime.ready() else 503
                    body = {'ready': status == 200}
                else:
                    runtime.enter()
                    entered = True
                    raw = self.headers.get('Authorization', '')
                    principal = TOKENS.get(raw[7:]) if raw.startswith('Bearer ') else None
                    if principal is None:
                        headers['WWW-Authenticate'] = 'Bearer'
                        raise Denied(401, 'unauthorized')
                    events.append('identity.lesson_allowlist')
                    action = 'upload' if path == '/uploads' and self.command == 'POST' else 'read'
                    store.authorize(principal, action)
                    events.append('authorization.current_membership')
                    store.take_quota(principal, action, clock(), quota_limit)
                    events.append('quota.accepted')
                    if runtime.hold is not None and self.command == 'GET' and route == '/notes/:id':
                        if not runtime.hold.wait(timeout=5):
                            raise Denied(503, 'fixture_wait_expired')
                    if self.command == 'GET' and path == '/notes':
                        body, status = {'notes': store.listing(principal)}, 200
                    elif self.command == 'GET' and route == '/notes/:id':
                        body, status = store.note(principal, path[len('/notes/'):]), 200
                    elif self.command == 'POST' and path == '/uploads':
                        if self.headers.get('Transfer-Encoding') is not None:
                            raise Denied(400, 'fixed_length_required')
                        sizes = self.headers.get_all('Content-Length', [])
                        if len(sizes) != 1 or not sizes[0].isascii() or not sizes[0].isdigit():
                            raise Denied(411, 'length_required')
                        size = int(sizes[0])
                        if not 1<=size<=1024:
                            raise Denied(413, 'invalid_upload_size')
                        payload = self.rfile.read(size)
                        if len(payload) != size:
                            raise Denied(400, 'incomplete_body')
                        body = store.stage(principal, self.headers.get('X-Filename', ''), self.headers.get('Content-Type', ''), payload)
                        status = 202
                    elif self.command == 'GET' and route == '/uploads/:id':
                        name, body = store.download(principal, path[len('/uploads/'):])
                        headers.update({'Content-Type': 'application/octet-stream',
                                        'Content-Disposition': 'attachment; filename="'+name+'"'})
                        status = 200
                    else:
                        raise Denied(404, 'not_found')
                    events.append('store.completed')
            except Denied as error:
                status, body = error.status, {'error': error.code}
                if error.retry_after is not None:
                    headers['Retry-After'] = str(error.retry_after)
                events.append('request.rejected')
            except Exception:
                events.append('request.internal_error')
            encoded = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
            try:
                self.send_response(status)
                self.send_header('Content-Type', headers.pop('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(encoded)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('X-Request-Id', trace_id)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(encoded)
                events.append('http.response_written')
            finally:
                if entered:
                    runtime.leave()
                runtime.record(trace_id, self.command, route, status, perf_counter()-start, events)

        def setup(self):
            super().setup()
            self.connection.settimeout(3)  # Socket timeout, not a complete production deadline.

        do_GET = do_POST = handle_request

    class Server(ThreadingHTTPServer):
        daemon_threads = False
        block_on_close = True

    return Server(('127.0.0.1', 0), Handler)
```

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

```json
{
  "trace_events": [
    "http.received",
    "identity.lesson_allowlist",
    "authorization.current_membership",
    "quota.accepted",
    "store.completed",
    "http.response_written"
  ],
  "log_fields": [
    "duration_ms",
    "method",
    "route",
    "status",
    "trace_id"
  ],
  "metric_labels": [
    "method",
    "route_template",
    "status_class"
  ],
  "diagnostic_buffer_limit": 128,
  "private_content_logged": false,
  "otel_exporter_or_prometheus_server_started": false
}
```

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

```python
"""Offline authored SLI samples and hypothetical capacity/cost arithmetic."""
from fractions import Fraction
import math


def percentile(values, quantile):
    if not 0<quantile<=1 or any(not math.isfinite(value) or value<0 for value in values):
        raise ValueError('invalid percentile inputs')
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(quantile*len(ordered))-1]  # Explicit nearest-rank convention.


def analyze(samples, target='0.99', threshold_ms=200):
    target = Fraction(target)
    if not 0<target<1 or not math.isfinite(threshold_ms) or threshold_ms<0:
        raise ValueError('invalid objective')
    for sample in samples:
        if type(sample['eligible']) is not bool or type(sample['leak']) is not bool:
            raise ValueError('explicit eligibility and invariant flags required')
        if type(sample['status']) is not int or not 100<=sample['status']<=599:
            raise ValueError('invalid status')
        if not math.isfinite(sample['latency_ms']) or sample['latency_ms']<0:
            raise ValueError('invalid latency')
    eligible = [sample for sample in samples if sample['eligible']]
    good = sum(sample['status'] == 200 and sample['latency_ms']<=threshold_ms for sample in eligible)
    bad, total = len(eligible)-good, len(eligible)
    budget = (1-target)*total
    invariant = not any(sample['leak'] for sample in samples)
    return {'eligible': total, 'excluded': len(samples)-total, 'good': good, 'bad': bad,
            'good_fraction': good/total if total else None,
            'allowed_bad': float(budget), 'remaining_budget': float(budget-bad),
            'burn_rate': float(Fraction(bad,total)/(1-target)) if total else None,
            'p95_ms': percentile([sample['latency_ms'] for sample in eligible], 0.95),
            'p99_ms': percentile([sample['latency_ms'] for sample in eligible], 0.99),
            'invariant_passed': invariant,
            'objective_passed': bool(total) and bad<=budget and invariant}


def sample_workload():
    groups = [(970, True, 200, 50), (20, True, 200, 350),
              (5, True, 503, 20), (5, True, 429, 5), (3, False, 401, 5)]
    return [{'eligible': eligible, 'status': status, 'latency_ms': latency, 'leak': False}
            for count, eligible, status, latency in groups for _ in range(count)]


def capacity_plan(qps=200, mean_service_ms=50, instances=4, pool=20,
                  db_budget=60, hours=720, assumed_hourly_cost='0.10'):
    if type(qps) is not int or qps<0 or not math.isfinite(mean_service_ms) or mean_service_ms<0:
        raise ValueError('invalid workload')
    if any(type(value) is not int or value<1 for value in (instances, pool, db_budget, hours)):
        raise ValueError('positive counts required')
    rate = Fraction(assumed_hourly_cost)
    if rate<0:
        raise ValueError('negative assumed price')
    return {'assumed_qps': qps, 'assumed_mean_service_ms': mean_service_ms,
            'estimated_mean_in_flight': qps*mean_service_ms/1000,
            'application_connection_ceiling': instances*pool, 'selected_db_budget': db_budget,
            'pool_ceiling_fits_budget': instances*pool<=db_budget,
            'assumed_instance_hours': instances*hours,
            'hypothetical_instance_cost': float(rate*instances*hours),
            'cost_excludes': ['database', 'storage', 'network', 'logs', 'backups', 'provider calls']}
```

Observed authored-sample results:

```json
{
  "authored_sample_result": {
    "eligible": 1000,
    "excluded": 3,
    "good": 970,
    "bad": 30,
    "good_fraction": 0.97,
    "allowed_bad": 10.0,
    "remaining_budget": -20.0,
    "burn_rate": 3.0,
    "p95_ms": 50,
    "p99_ms": 350,
    "invariant_passed": true,
    "objective_passed": false
  },
  "one_success_with_leak": {
    "eligible": 1,
    "excluded": 0,
    "good": 1,
    "bad": 0,
    "good_fraction": 1.0,
    "allowed_bad": 0.01,
    "remaining_budget": 0.01,
    "burn_rate": 0.0,
    "p95_ms": 1,
    "p99_ms": 1,
    "invariant_passed": false,
    "objective_passed": false
  },
  "production_slo_measured": false
}
```

p95 is 50 ms while p99 is 350 ms for these samples. Slow successes and eligible 429/503s make the objective fail. The one-event leak case fails its invariant gate despite zero quantitative bad events. None of these values comes from the loopback API's timing samples.

Burn-rate alerts should account for the objective window, sustained impact, traffic volume and actionability. Multi-window policies can combine a longer confirmation window with a shorter signal to catch current fast burn without paging on every isolated error. The code calculates one sample's ratio; it does not implement a rolling multi-window alert evaluator. [Google SRE SLO alerting](https://sre.google/workbook/alerting-on-slos/).

Do not page on every debug symptom. A page should indicate urgent user impact or imminent risk and have an owner/runbook. Dashboards and tickets can carry slower capacity trends, known nonurgent failures and improvement work.

---

## 16. Capacity, cost and realistic validation

The planning helper uses explicitly hypothetical inputs: 200 requests/s, 50-ms mean service time, four instances, twenty possible connections each, a selected database budget of sixty, 720 hours and a fictional 0.10 currency units per instance-hour. It does not quote a cloud price.

```json
{
  "assumed_qps": 200,
  "assumed_mean_service_ms": 50,
  "estimated_mean_in_flight": 10.0,
  "application_connection_ceiling": 80,
  "selected_db_budget": 60,
  "pool_ceiling_fits_budget": false,
  "assumed_instance_hours": 2880,
  "hypothetical_instance_cost": 288.0,
  "cost_excludes": [
    "database",
    "storage",
    "network",
    "logs",
    "backups",
    "provider calls"
  ]
}
```

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

Verified on **2026-10-16** with **Python 3.12.10**, **SQLite 3.49.1**, and **Windows 11**. No third-party Python packages, Docker, cloud credentials or external observability services are required.

From the repository root in PowerShell:

```powershell
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 'examples/system-design/module-4-secure-observable-operations/verify.py'
```

Or run `python verify.py` from the fixture directory with Python 3.12 or later. The harness starts four owned HTTP servers on ephemeral loopback ports, closes each server and joins its serving/handler threads, closes SQLite connections and removes its exact temporary database/vault directory. Port 3000 is not used.

**93 local checks passed:** 17 http policy, 24 uploads, 7 quotas, 11 lifecycle, 5 saturation, 9 telemetry, 2 cleanup, 13 indicators, 5 planning. Three exact source files and nine exact observation blocks are embedded; `verification-results.json` records the named assertions and scope.

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

Primary references reviewed on 2026-10-16. The code and scenarios are authored teaching examples, with explicit limits; the sources support named mechanisms rather than a claim that this is a complete vendor-prescribed deployment or a measured interview-frequency ranking.

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
