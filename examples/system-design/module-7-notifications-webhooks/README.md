# S2: Notification and webhook delivery service

Run `python verify.py` with Python 3.12 or later. Recorded runtime: Python 3.12.10 / SQLite 3.49.1. No third-party packages, Docker, Redis, vendor account, external messages or existing database service are required.

- `delivery.py`: atomic event/fan-out acceptance, scoped stable replay, immutable configured targets, enabled preferences, bounded claims, leases/fencing, attempt history, retries, cooldowns and tenant-scoped inspection.
- `protocol.py`: custom raw-body HMAC/timestamp protocol, actual owned loopback receiver, scoped receipt/effect transaction, injected receiver failures and real socket close after commit. Public lesson secrets are not production credentials or a Stripe/GitHub implementation.
- `worker.py`: bounded loopback HTTP adapter, stable delivery ID, per-attempt signing, no redirect following, unknown outcome, retry scheduling and injected/drawn full jitter. Only trusted `(tenant,endpoint)` registry entries can select a target. The fixture supports decimal Retry-After seconds up to one day; HTTP-date is not parsed.
- `estimates.py`: hypothetical fan-out, attempt amplification, mean concurrency, storage and backlog drain calculations; no throughput claim.
- `verify.py`: 109 named checks: 11 validation, 17 intake, four concurrency, 16 leases, 13 retry, 22 HTTP, 14 network, eight estimates and four cleanup. Includes four queue worker calls on independent thread-owned connections and two concurrent receiver requests.
- `author.py`: chapter generator with four exact source files and seven recorded outputs, 30 Q&As, ten exercises and a 45-minute mock.
- `integrate.py`: publishes S2 in Worked Systems, refreshes authored progress and advances only the next section to S3.
- `validate_site.py` and `site-smoke.mjs`: content/source/output/link consistency, production build, bounded route sweep, scoped search, navigation and owned preview cleanup.

All notifications are optional reminders. Disabled subscriptions are excluded at acceptance and rechecked before claim; already claimed external work can race opt-out. Re-enable does not revive skipped intent. Original event replay does not fan out to subscribers added later. Fan-out is capped at eight subscriptions/tenant; retained events at 256 globally. Existing replay works at capacity. Trusted subscription configuration and receiver receipt retention are not globally bounded by those caps; no retention service is implemented.

The executed sender is a local SQLite authority. Its writer lock serializes the file, not individual rows. Clock values are controlled server milliseconds, not client input. `run_once` defaults completion time to the supplied fixture start time; a real supervised runner must supply current completion time and implement polling, total deadline and lease management. The 250 ms HTTP socket timeout is not a hard total deadline under arbitrary slow traffic.

Every durable claim counts toward the three-attempt limit, including crashes before I/O. Expired/stale completion is fenced in sender state, not at a remote effect. Unknown transport may mean the receiver already committed; retry uses the same delivery ID and receipt/effect dedupe suppresses repetition. The demonstrated effect is a local record, not an external payment/email action. Success means endpoint acceptance, not inbox delivery or human read.

429 cooldowns reactively block later claims for a tenant/endpoint; they do not control already in-flight work or implement proactive provider-wide rate limits. Full jitter can draw zero. Failed rows remain for inspection; no broker DLQ, automated redrive, strict ordering, live secret rotation, public admin/ingestion API, production auth/TLS or machine-crash/load benchmark is implemented. Email/SMS/push adapters are discussed architecture, not executed integrations.

After changes:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

The harness closes all owned listeners/connections, joins serving/handler/worker threads and removes its exact temporary directory. Port 3000 and Docker remain stopped. No persistent service starts. Use this chapter's latest validation summary for the expanded site; previous summaries are historical snapshots. Site previews use six concurrent route requests and the cached font-response fixture when available.
