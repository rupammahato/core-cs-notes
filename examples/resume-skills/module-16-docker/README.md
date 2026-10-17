# M16: Docker Fundamentals

Real Linux-container examples accompanying Part 18. Recorded: Docker client/engine 29.8.2, Compose 5.5.1, Buildx 0.37.2, WSL2 Linux kernel 5.15.153.1, host CPython 3.12.10, image Python 3.12.15 and PostgreSQL 18.6.

## Run

Start Docker Desktop's Linux engine, then from the repository root:

```powershell
docker pull python:3.12-slim
docker pull postgres:18-alpine
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 examples/resume-skills/module-16-docker/verify.py
```

Select another Python 3.12 interpreter path on other machines. The host verifier uses standard-library modules. Application packages install inside the image from requirements.lock.txt; initial registry/package access is required. Base tags are resolved to local RepoDigests for each verifier run. The recorded digests are in verification-results.json; default manual builds still use moving tags unless overridden. Package pins have no hashes.

The verifier creates a unique Compose project, application image, helper containers, network and named PostgreSQL volume. It checks ownership labels before removing only its resources. Generated bind fixtures live in a validated-owned temporary subdirectory. No global prune is performed. API ports are ephemeral and host-loopback-only; PostgreSQL has no published host port. Port 3000 is unused.

The reusable verifier assumes the engine is running and does not stop it. In the recorded authoring session, Docker was initially stopped and had no existing containers; it was started for this exercise and restored to stopped after cleanup. Public Python/PostgreSQL images and BuildKit cache remain available. Existing native database services/user documents are untouched.

## Results

| Group | Named checks |
| --- | --- |
| Build | 5 |
| HTTP | 6 |
| Lifecycle | 5 |
| Networking | 5 |
| Readiness | 3 |
| Runtime | 10 |
| Storage | 6 |
| **Total** | **40** |

Real builds verify stage selection/context guards and cache reuse. Actual requests through Docker's published port create/replay/read PostgreSQL records. Tests distinguish container localhost, service DNS and publishing; one-shot/background exits; writable-layer restart versus recreation; bind changes/denial/masking; database-volume persistence; liveness/readiness/health and dependency recovery. Resource settings and selected kernel denials are recorded, without a load/OOM or adversarial-isolation claim.

## Files and boundaries

- Dockerfile / .dockerignore / requirements.lock.txt: scoped context and multi-stage image.
- compose.yaml / bootstrap.sql: runtime services, non-superuser application role, health/storage/network configuration.
- app.py / healthcheck.py: demonstration HTTP API and readiness request.
- secrets/db_password.txt: deliberately public local fixture password, not a real credential.
- verify.py: unique resource lifecycle, assertions and ownership-scoped cleanup.
- verification-results.json / verification-output.txt: recorded checks/runtime/digests.
- image-build-output.txt / image-rebuild-output.txt / docker-command-output.json / compose-container-output.txt: actual command/build/application evidence.
- cleanup-results.json / engine-session-results.json: fixture removal and recorded engine restoration.
- content-validation.json / site-validation.json / validation-summary.json: chapter/source and website checks.

The chapter embeds the Dockerfile, ignore file, package snapshot, Compose file, initialization SQL and application/probe source exactly. The standard-library HTTP server/public password are teaching fixtures, without authentication/TLS or full ingress/draining hardening. No registry push, cloud deployment, host crash, backup restore, major database upgrade, OOM/load benchmark or container-escape audit is exercised.
