# M17: Linux Deployment, Nginx and PM2

Real Linux deployment laboratory accompanying Part 19. Recorded on 14 October 2026: Debian 12.15, Node v22.23.3, PM2 7.0.4, Nginx 1.22.1, OpenSSL 3.0.22, Docker client/engine 29.8.2 and WSL2 Linux kernel 5.15.153.1.

## Run

Start Docker Desktop's Linux engine, then from the repository root:

```powershell
docker pull node:22-bookworm-slim
& 'C:/Users/Win11/AppData/Local/Programs/Python/Python312/python.exe' -X utf8 examples/resume-skills/module-17-linux-nginx-pm2/verify.py
```

Select another Python interpreter path on other machines. The host verifier uses standard-library modules. The Docker build installs Linux tools from Debian repositories and PM2 using the committed package-lock.json. Initial registry/repository access is needed. The selected local Node base tag is resolved to a RepoDigest for the verification build; the recorded digest is in verification-results.json. apt packages are not frozen by that base-image digest.

One owned container models a single Linux network namespace: Nginx forwards to loopback Node workers managed by PM2. Its sleep entrypoint and multiple tools are a test-harness arrangement, not a production container pattern. Only Nginx HTTP/TLS ports are published, with ephemeral host ports restricted to 127.0.0.1. The app port is unpublished and loopback-bound inside Linux. Port 3000 is unused.

The verifier uses unique ownership labels, checks them before removal, and cleans only its container/image and validated host scratch directory. The generated TLS key is removed with the container; only a public certificate is briefly copied to host scratch. Public base images and build cache are retained. There is no global prune or host PM2/systemd/firewall change.

The reusable verifier leaves the engine running. For the recorded authoring session, the engine was initially stopped and was restored to stopped after all fixture cleanup and confirming no active containers remained.

## Verified results

| Group | Checks |
| --- | --- |
| Linux | 6 |
| Nginx | 14 |
| TLS | 4 |
| PM2 | 8 |
| Lifecycle | 5 |
| Host publication | 3 |
| **Total** | **40** |

The tests perform real file/permission denials, environment inheritance, URI routing, spoofed-header replacement, 413/404/502/504 responses, self-signed TLS trust/rejection, two-worker requests and separate counters, worker crash/replacement, environment restart/update, active-request drain and sampled traffic during reload, invalid-candidate validation, live Nginx reload, PM2 save/resurrect and actual requests through Docker's published proxy ports.

## Sources and evidence

- app.cjs: bounded demonstration API and signal-driven shutdown.
- ecosystem.config.cjs: two PM2 cluster workers, readiness, timeouts and log paths.
- nginx.conf: HTTP/TLS routing, headers, limits and request/timing log format.
- Dockerfile / package.json / package-lock.json: Linux test environment and dependency snapshot.
- verify_linux.py / verify.py: Linux checks and host ownership-scoped lifecycle.
- verification-results.json / linux-results.json / verification-output.txt: actual results.
- linux-command-output.json / docker-command-output.json / image-build-output.txt: actual commands/build.
- application-output.txt / application-error-output.txt / nginx-access-output.txt / nginx-error-output.txt: actual logs.
- cleanup-results.json / engine-session-results.json: cleanup and authoring engine restoration.
- dependency-audit.json: actual npm audit report.
- content-validation.json / site-validation.json / validation-summary.json: chapter and site checks.

The locked dependency audit reported eight high-severity package entries, including affected ancestors, arising from basic-ftp, braces and js-yaml advisories. The fixture does not exercise FTP/PAC/untrusted YAML or watching; that bounds its demonstrated paths, without proving the package tree safe for production. No forced package downgrade or unverified override was applied. Re-audit and assess fixes/exposure before deployment.

The chapter embeds app.cjs, ecosystem.config.cjs, nginx.conf and Dockerfile exactly. It includes 30 interview Q&As and ten exercises. It separates actual results from proposed single-VM production architecture.

No public DNS/CA/renewal, host/systemd boot, cloud deployment, authentication/database integration, blue/green cutover, schema migration, backup restore, adversarial/slow-client ingress, WebSocket/SSE draining, forced-deadline exhaustion or production load benchmark was tested. The successful sampled reload is not a universal zero-downtime guarantee. PM2 save/resurrect was tested within an available daemon environment, not across a host reboot.
