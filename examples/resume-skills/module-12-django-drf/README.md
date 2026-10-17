# M12: Django and Django REST Framework

A tenant-scoped task API with real migrations, ORM query measurements and transactions.

## Reproduce

Select Python 3.12, then from the repository root:

    python -m venv examples/resume-skills/module-12-django-drf/.venv
    ./examples/resume-skills/module-12-django-drf/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-12-django-drf/requirements.lock.txt
    ./examples/resume-skills/module-12-django-drf/.venv/Scripts/python.exe -m pip check
    ./examples/resume-skills/module-12-django-drf/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-12-django-drf/verify.py

The prepared environment used the separate Python312 installation, CPython 3.12.10
on Windows AMD64, Django 5.1.3, DRF 3.15.2 and SQLite 3.49.1. Django 5.1 is now
unsupported; this is a historical teaching snapshot, not a production deployment
recommendation. Version-matched docs explain the observed behavior.

This machine installed from cached wheels with --no-index. The environment and
wheelhouse are ignored; global packages were not changed. Online reproduction needs
package access. The lock pins versions, not hashes or every platform condition.

## Application

- config/: settings, URLs and WSGI/ASGI entry points. Only WSGI serving was verified.
- work/models.py and migrations/: real persisted schema and generated initial migration.
- work/authentication.py: public opaque credential fixtures checked against active users/memberships.
- work/permissions.py: workspace role and owner-write policy.
- work/serializers.py: explicit public fields, rejected unknown/server-managed input,
  tenant-scoped related project selection.
- work/views.py: scoped ModelViewSet, filtered tag prefetch, pagination and completion action.
- work/services.py: conditional SQL transition plus audit in one transaction.
- work/middleware.py: in-memory correlation trace for the bounded test workload.

Settings require M12_DATABASE explicitly. Use verify.py: it supplies a fresh database
for each group, migrates/seeds it and removes the owned directory after child exit.
Calling groups directly against an already-seeded database is not the supported run.

## Verification

76 named checks: 15 ORM, 14 transactions, 9 framework, 38 real HTTP. Some named
checks include multiple related assertions/fixtures. Three extra management checks
validate system configuration, model/migration drift and pending migrations.

- fixtures.py / bootstrap.py / checks.py: deterministic fixtures and named assertions.
- verify_orm.py: lazy queries/cache, joins/prefetch, serializer budget, projections,
  bound parameters, deferred fields, model validation and SQLite lock capability.
- verify_transactions.py: rollback/savepoints, DB constraints, conditional completion,
  sequential retry, stale model attributes and post-commit callback failure.
- verify_framework.py: migration graph, routing/middleware, real fixture auth,
  session/CSRF with force_login, serializer defaults and cross-tenant relation guards.
- verify_http.py: actual loopback WSGI requests, allowed/rejected mutations and cleanup.
- verify.py: aggregate runner, fresh file-backed databases and verified-owned temp cleanup.
- *-results.json / verification-output.txt: captured results and observations.
- dependency install/check output, content/site validation and validation-summary.json:
  reproduction and integration evidence.

No real password/login/JWT verification, PostgreSQL instance, production server,
external API, durable queue or notification delivery is implemented. A force_login
session fixture does not verify passwords. The audit table is not an immutable ledger
or complete outbox. Ingress streaming/export and production concurrency are not tested.

Query counts belong to this six-task SQLite fixture, not a benchmark. select_for_update
on this backend does not prove PostgreSQL row locks. Ordinary PATCH has no expected-
revision contract; that extension is discussed as an exercise. The task-system/outbox
architecture beyond the runnable slice remains a design proposal.

The temporary HTTP listener is probed closed. All child processes exit before database
cleanup. Website smoke checks also stop their own temporary listener, and port 3000
remains stopped.
