# A3: Reliable workflows and concurrency

Run `python verify.py` with Python 3.12 or later. The recorded run uses Python 3.12.10 and SQLite 3.49.1. No third-party Python packages, broker, Redis, Docker, external credentials/provider or listener are required.

- `retry.py`: deadline and attempt budget, explicit transient/permanent outcomes, caller-asserted retry safety and injected full-jitter decisions. The transport must enforce its supplied timeout; this function does not interrupt blocking calls itself.
- `workflow.py`: real SQLite effect/outcome/outbox transactions, action/input-bound operation keys, stable event IDs, due/lease/generation/attempt states, conditional scarce-stock reservation and guarded release compensation.
- `consumer.py`: a separate SQLite inbox plus note-created projection committed atomically. Version-1 create events only; this is not an ordered general-purpose note-update projection or an external provider adapter.
- `verify.py`: 90 named assertions: 19 retry policy, 14 atomic operation, ten lease, twelve consumer atomicity, eleven delivery-bound, ten concurrency, twelve compensation and two cleanup checks. Six competing calls use thread-owned independent SQLite connections.
- `author.py`: generates the chapter with three exact source files and eight exact recorded observation blocks.
- `integrate.py`: updates actual availability, sidebar, predecessor continuation, root progress/footprint and next A4. Learning mastery remains unchecked.
- `validate_site.py` and `site-smoke.mjs`: exact source/result fidelity, authored links, production build, all available routes, navigation/search and owned-preview cleanup.

The local source transaction stores the note, original successful operation result and outbox intent together. The direct relay steps are exercised by the harness: claim, call the separate consumer, then acknowledge. The recovery case deliberately omits acknowledgement and reopens both files; a later claim redelivers the same event and the consumer applies its local effect once. Controlled faults after source/consumer inserts verify rollback boundaries.

These are controlled exceptions/omitted steps and persistent close/reopen, not actual process-kill, power-loss, network packet or broker failure tests. The effect guarantee is limited to the consumer's local inbox/projection and its retained identity history. The source lease generation rejects stale acknowledgement/reschedule; it does not stop stale worker CPU or fence an external provider. Lease time and retry transport/time are injected by the harness.

Automatic delivery claims stop after three attempts; dead work needs explicit recovery. A dead item may already have affected its consumer. The implementation does not provide lease renewal, quarantine replay tooling, a broker fan-out protocol, complete saga coordinator, payment/refund or production authentication. Operation keys retain successful outcomes only; failures roll back without retaining terminal error results. Dedupe/outbox retention is unbounded in this teaching fixture.

The stock release is an actual local compensation with an active-to-released guard. Repeated release using either the same or a new operation key cannot restore stock twice. It is not a full reservation/payment workflow with holds and expiry; S4/S8 remain future worked systems.

Reproduction order after behavior changes:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

Verification closes all SQLite connections and joins the six competing calls before removing its exact temporary directory. Site validation uses an ephemeral loopback preview and closes it afterward. Port 3000 and Docker remain stopped. The site build uses the existing cached font-response fixture when available. Use this chapter's validation summary for the expanded site; previous summaries are historical snapshots.
