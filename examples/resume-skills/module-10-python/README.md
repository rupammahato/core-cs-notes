# M10: Python Fundamentals

Standard-library-only examples for the Python interview chapter.

Run from the repository root:

    python -X utf8 examples/resume-skills/module-10-python/verify.py

Verified on CPython 3.13.15, 64-bit Windows, conventional build with GIL enabled
(Py_GIL_DISABLED=0). Python 3.13 documentation was researched independently.

The runner uses the same interpreter executable for each fresh subprocess, enables
UTF-8, disables bytecode-cache writes, checks exact stdout/exit/stderr and imposes
per-process deadlines. Run without -O: examples use assertions and the runner
refuses optimized mode. quote_service.py uses explicit runtime validation errors.

## Included

- snippets/: 24 executable language cases plus the imported module fixture.
- concurrency/: six executable cases for coroutine scheduling/blocking/thread
  offload, bounded async workers, TaskGroup cleanup, timeout cleanup, coordinated
  thread races/locks and spawned process workers.
- cases.json: source paths and expected output contracts.
- quote_service.py: pure parsing/application/public-serialization boundary.
- verify_domain.py: 14 named application checks, including accepted boundaries
  and rejected input/tenant fixtures.
- verify.py: complete runner; records verification-results.json and
  verification-output.txt from actual execution.
- content-validation.json: embedded source/output fidelity and chapter counts.
- site validation artifacts: generated during handbook integration checks.

44 checks pass: 24 language, 6 concurrency, 14 domain. Some domain checks contain
several related rejected fixtures; totals count named checks, not every assertion.

## Scope

No external packages, environment creation, paid APIs, framework server or database
are required. The catalog/principal are local fixtures. The caller must authenticate
the principal and pass externally supplied data through parse_body; annotations and
dataclass construction are not a trust boundary. Production HTTP reading limits,
authentication, persistence and transactions belong to later modules.

The bounded sample retains only eight results for comparison; a real unbounded
stream needs a bounded/persisted sink. Async provider behavior is locally modeled.
The process example checks transferred values and separate execution, not speed.
The cycle example explicitly invokes collection and does not assert RSS changes.
No free-threaded interpreter, static type checker, production deployment or real
provider call is claimed. The document-processing architecture is a design exercise.

All child executors/loops are scoped and closed. These examples open no network
listeners. Website smoke checks use a temporary loopback port and stop it afterward;
port 3000 remains stopped.
