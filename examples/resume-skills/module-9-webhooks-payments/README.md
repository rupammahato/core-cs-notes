# M9: Webhooks, Payments and Reliable Integrations

Recorded versions: Node.js v22.14.0 and SQLite 3.47.2. No extra npm packages are required. node:sqlite is experimental on this runtime; its expected warnings are preserved separately.

From the repository root:

```powershell
node examples/resume-skills/module-9-webhooks-payments/verify.mjs
```

57 named cases: 21 core, 26 real HTTP, six reconciliation-fixture and four file/process-recovery cases. Individual runners are verify-core.mjs, verify-http.mjs, verify-reconciliation.mjs and verify-recovery.mjs.

The receiver verifies raw-body HMAC under a configured endpoint/account, then commits a minimal normalized inbox receipt before returning 202. A worker atomically applies payment state, one purchase credit grant, paid order, processed receipt and outbox intent.

Scoped event deduplication and business-effect uniqueness are separate. Replaying a valid body under another unsigned delivery header does not grant twice. Amount/currency/order/payment conflicts go to review. A failed attempt does not prevent another attempt from funding the order.

Store opening requires an explicit file path or explicit :memory:. File-backed tests query/assert DELETE journal mode, FULL synchronization and foreign keys. Isolated in-memory tests use a memory journal. Recovery tests create unique temporary databases, exit workers before/after commit, reopen/inspect/retry, run two ready independent workers and safely remove their own resolved temporary directory.

Reconciliation uses a local account-bound provider fixture and the same effect guard. Outbox delivery uses a local idempotent recipient fixture. No external provider or customer message is sent.

Manual demo:

```powershell
# Terminal 1; creates/reuses this example's demo.sqlite.
node examples/resume-skills/module-9-webhooks-payments/start.mjs

# Terminal 2; fixed loopback destination and public fixture secrets.
node examples/resume-skills/module-9-webhooks-payments/send-fixture.mjs
node examples/resume-skills/module-9-webhooks-payments/inspect.mjs
```

Receiver: 127.0.0.1:3109. Ctrl+C stops it. Repeating the sender shows replay handling; the manual database persists. The timer worker is a demo convenience. Outbox rows remain for inspection; no notification daemon is started.

Limits: narrow Razorpay-shaped subset, public fixture credentials/IDs, no real checkout/provider API/refund/dispute/settlement integration, no operator review/requeue API, no queue retry/dead-letter system, no multi-dispatcher lease, no multi-host/production database benchmark. Process exits do not simulate power loss. The local idempotent recipient is not proof of an external recipient's behavior.

See the [M9 chapter](../../../Resume%20Skills%20Notes/resume-skills-handbook-part-11-module-9-webhooks-payments-reliable-integrations.md) for complete source, evidence and interview practice.
