# M11: Flask, FastAPI and Python Request Handling

Comparable quote/product adapters plus protocol, validation and lifecycle checks.

## Reproduce

Select Python 3.12, then from the repository root:

    python -m venv examples/resume-skills/module-11-python-frameworks/.venv
    ./examples/resume-skills/module-11-python-frameworks/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-11-python-frameworks/requirements.lock.txt
    ./examples/resume-skills/module-11-python-frameworks/.venv/Scripts/python.exe -m pip check
    ./examples/resume-skills/module-11-python-frameworks/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-11-python-frameworks/verify.py

Here the environment was created from the separate Python312 installation;
the machine's default python command is 3.13.15. The executed interpreter was
CPython 3.12.10 (Windows AMD64), with Flask 3.0.3, FastAPI 0.142.2,
Pydantic 2.13.5, Starlette 1.7.0, Uvicorn 0.54.0 and HTTPX 0.28.1.

This is a reproducible teaching snapshot. It is not a current production-dependency
recommendation. Online installation requires package access; this run used local
cached wheels with --no-index. .venv and .wheelhouse are ignored; global packages
were not modified. requirements.lock.txt pins exact installed versions, not hashes.

## Files and evidence

- protocols.py: tiny WSGI and HTTP-only ASGI applications.
- domain.py: schemas, public fixture tokens, tenant catalog and instrumented leases.
- flask_app.py / fastapi_app.py: complete framework adapters/factories.
- servers.py: owned ephemeral loopback WSGI/ASGI test listeners with cleanup.
- verify_protocols.py: 2 in-process protocol checks.
- verify_validation.py: 10 real Pydantic checks.
- verify_http.py: 52 real HTTP checks (25 Flask, 27 FastAPI), including failure-path
  lease cleanup and a guard that invalid body values do not reach the business marker.
- verify_runtime.py: 16 in-process framework checks, including thread dispatch,
  dependency caching/scope, response filtering bypass and background failure.
- verify.py / checks.py: runner, named assertions and captured evidence.
- verification-results.json / verification-output.txt: actual 80-check results.
- expected-warning-output.txt: known pinned Starlette HTTPX-adapter deprecation.
- dependency-install-output.txt / dependency-check-output.txt: offline install and pip check.
- content-validation.json / site artifacts / validation-summary.json: chapter integration evidence.

The aggregate runner enforces selected version pins, uses fresh subprocesses and
fails on unexpected errors/stderr. One known TestClient warning is recognized and
saved separately; the existing HTTPX adapter remains functional on the pinned stack.

## Scope

Opaque credentials, catalog entries, audit logs and resource leases are local
fixtures. No real JWT/login, database, payment, provider or durable job is implemented.
Prices and tenant scope come from trusted fixture state; clients cannot choose them.
The service expects the declared validated request and trusted principal.

Werkzeug is a development/test WSGI server here, not a production deployment.
The HTTP harness binds only loopback and closes its own temporary listeners;
Uvicorn lifespan startup/shutdown and catalog cleanup are checked. Runtime clients
use no sockets. There is no persistent server and port 3000 stays stopped.

No throughput benchmark, streaming DB response, free-threaded comparison, browser
Swagger interaction or ingestion deployment is claimed. The architecture is a design
exercise. Dependency cleanup/send order belongs to the recorded framework stack.
