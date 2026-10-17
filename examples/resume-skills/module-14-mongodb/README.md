# M14: MongoDB in a Backend

Real MongoDB examples accompanying Part 16. Recorded environment: MongoDB Community 7.0.28/WiredTiger, CPython 3.12.10 (64-bit Windows), PyMongo 4.10.1 and dnspython 2.8.0.

## Run

From the repository root, using the prepared environment:

```powershell
./examples/resume-skills/module-14-mongodb/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-14-mongodb/verify.py
```

To recreate the environment, select Python 3.12, create .venv here, install requirements.lock.txt and run pip check. The recorded installation used cached wheels with --no-index. The lock pins versions without hashes; .venv and .wheelhouse are ignored. PyMongo includes bson; the unrelated standalone bson distribution is not a dependency.

Install MongoDB binaries separately. M14_MONGOD defaults to C:/Program Files/MongoDB/Server/7.0/bin/mongod.exe. The runner creates a new temporary dbPath and loopback process, verifies its dbPath/port, initializes a single-member replica set and creates a fresh database per group. It never targets the existing Windows service or its data. Authentication/TLS are disabled only for this isolated local fixture; no credentials are involved. This is not a remote deployment configuration.

After child processes finish, the runner shuts down its owned process, checks the listener is closed and removes the validated temporary directory. The successful run recorded graceful shutdown and both cleanup flags true. Individual group files expect the aggregate runner's explicit M14 environment. Use verify.py for a fresh complete run. Port 3000 is not used.

## Results

| Group | Named checks |
| --- | --- |
| Core | 17 |
| Queries / aggregation | 12 |
| Indexes | 10 |
| Atomic updates | 6 |
| Transactions / purchase | 15 |
| Pool / cursor | 5 |
| **Total** | **65** |

The 30,000-document query fixture naturally moves from a collection scan/sort to a compound index without changing selected documents. A covered projection returns 20 rows with zero document fetches; a broad query still naturally scans. Counts/plans are actual evidence, not a benchmark.

The suite produces a real transient write conflict and verifies with_transaction reruns the callback with fresh reads. Barrier-started purchase calls test last-unit contention and same-key replay; they assert final state without claiming to observe an internal lock schedule. Other checks demonstrate array-element matching, an unscoped foreign lookup, aggregation double-counting, partial ordered batches and pool checkout pressure.

## Implementation and artifacts

- cluster.py: owned temporary mongod/replica-set lifecycle, target verification and cleanup.
- db.py: explicit loopback URI, aware UTC decoding, connection/pool budgets.
- catalog.py: server product validator, tenant/SKU and tenant/request-key uniqueness, seed data and safe scalar query builder.
- purchase.py: one-item purchase with conditional stock update, item/price snapshot, replay and atomic outbox intent.
- queries.py / pagination.py: tenant-scoped dashboard/lookup and typed keyset continuation.
- checks.py / verify.py / verify_*.py: assertions, aggregate lifecycle and six fresh-database groups.
- *-results.json / verification-output.txt / mongodb-server-output.txt: real execution evidence; raw BSON plan metadata uses Extended JSON.
- content-validation.json / site-validation.json / validation-summary.json: source/results fidelity and website checks.
- site-smoke.mjs: ephemeral loopback website checks, then stops its owned server.

The chapter embeds catalog.py, purchase.py, db.py, queries.py, pagination.py, verify_atomic.py and verify_indexes.py exactly.

## Boundaries

No HTTP/authentication, database role enforcement, remote TLS, Atlas, multi-member failover, sharding, crash/power-loss/backup recovery, provider payment, TTL-deletion experiment or outbox delivery worker is exercised. Orders/outbox have no full document validator in this fixture; the service and indexes enforce the illustrated write path, and alternate writers require their own control. A reference field is not a foreign key.

with_transaction may rerun the callback. The executed driver documents a 120-second retry window; max_commit_time_ms=3000 bounds a commit command, not the whole purchase. A production API needs a compatible end-to-end deadline/retry policy. External side effects do not belong inside this callback. Proposed ingestion/dispatch/cancellation extensions remain design work.
