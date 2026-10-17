# M13: PostgreSQL in a Backend

Real PostgreSQL examples accompanying the Part 15 handbook. Verified on PostgreSQL 18.4 and CPython 3.12.10 (64-bit Windows), with Psycopg/psycopg-binary 3.3.4, psycopg-pool 3.3.1 and client libpq 18.3.

## Run

From the repository root:

```powershell
./examples/resume-skills/module-13-postgresql/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-13-postgresql/verify.py
```

To recreate dependencies, select Python 3.12, create .venv in this folder, install requirements.lock.txt and run pip check. The recorded installation used cached wheels with --no-index; .venv and .wheelhouse are ignored. The lock pins versions without hashes. requirements.txt records the direct dependencies.

PostgreSQL binaries must be installed separately. M13_PG_BIN defaults to C:/Program Files/PostgreSQL/18/bin and must contain initdb, postgres and pg_ctl. The runner initializes a brand-new temporary cluster, launches native postgres hidden on an ephemeral loopback port, verifies its data_directory, and creates a fresh database per group. It uses public local fixture passwords and SCRAM host authentication; TLS is explicitly disabled for this local fixture. It never targets an existing service/database.

Application queries use a NOSUPERUSER/NOCREATEDB/NOCREATEROLE role; fixture setup uses its separate owner. Children finish and connections close before the owned cluster is stopped and its validated temporary directory removed. The successful run recorded both cleanup flags true. Do not direct individual group scripts at an existing database: their explicit M13 environment is supplied by the aggregate runner. Port 3000 is not used.

## Verified results

| Group | Named checks |
| --- | --- |
| Core | 19 |
| Concurrency | 14 |
| Pool | 8 |
| Plans | 7 |
| Reservation service | 12 |
| **Total** | **60** |

Separate sessions reproduce snapshot differences, a real row-lock wait, lost update, Repeatable Read write skew, a Serializable failure followed by a full-transaction retry and an actual deadlock. Reservation races observe the intended blocked SQL before releasing a competitor: last-unit contention yields one reservation, while same-key contention yields one new result and one replay.

The 50,000-row plan fixture naturally changes from scan/sort to the composite index, preserves result rows and still scans for a broad query. Raw timings are preserved for traceability, not presented as a benchmark.

## Files

- cluster.py: isolated server lifecycle and validated cleanup.
- db.py / schema.sql: explicit connection setup, pool and real DDL/fixtures/grants.
- reservation.py: trusted-price, tenant/key-scoped reservation with conditional stock update and atomic outbox intent.
- retry.py: bounded whole-transaction retry for serialization/deadlock errors; production jitter/deadline scheduling is not included.
- checks.py / coordination.py: named assertions, observed blocking and bounded owned-thread cleanup.
- verify.py / verify_*.py: aggregate runner and five independent groups.
- *-results.json / verification-output.txt / postgres-server-output.txt: actual engine results and expected server-error evidence.
- content-validation.json / site-validation.json / validation-summary.json: chapter/source fidelity and site checks.
- site-smoke.mjs: temporary loopback website verification; closes its owned listener.

The chapter embeds schema.sql, db.py, reservation.py, retry.py and verify_plans.py exactly. Other code snippets are labeled usage examples.

## Scope

This verifies local engine/driver behavior. It does not provide an HTTP endpoint, authentication, remote TLS, PgBouncer, a payment integration, an outbox delivery worker, replication, crash/power-loss recovery, backup restoration or a load benchmark. Table grants do not implement tenant row filtering; RLS is not enabled. The helper requires trusted tenant context and an idle autocommit connection and owns its complete transaction.

The documentation proposes cancellation, dispatcher and migration extensions separately. The temporary-cluster mechanism is a test harness, not a production deployment recipe.
