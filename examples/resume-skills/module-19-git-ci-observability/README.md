# M19: Git, CI/CD, Testing, Observability and Performance

Part 21 examples. Recorded 14 October 2026: Windows, CPython 3.12.10, Node v22.14.0, Git 2.55.0.windows.5, PyYAML 6.0.2, OpenTelemetry API 1.9.1 and core/trace SDK packages 2.12.0.

## Run

From the repository root in PowerShell:

```powershell
Set-Location examples/resume-skills/module-19-git-ci-observability
npm ci --ignore-scripts
python -m venv .venv
& '.venv/Scripts/python.exe' -m pip install -r requirements.txt
& '.venv/Scripts/python.exe' -X utf8 verify.py
```

Use Python 3.12 and Node/Git on PATH. Package installation needs registry access. The full run uses local fixtures and the saved official action pins, without a cloud account, hosted runner, main-repository commit or remote deployment. requirements.txt pins PyYAML without hashes; package-lock.json records the JavaScript tree. The recorded npm audit reported zero vulnerabilities at that time; it is not a security guarantee.

All Git mutations target disposable repositories and a local bare remote inside a validated owned scratch directory. Global Git configuration/hooks are isolated and the main repository's HEAD is checked before/after. The scratch repositories/releases and candidate HTTP processes are removed. Retained artifacts are public teaching source/results. Port 3000 is unused; test HTTP binds only to ephemeral loopback ports. Docker is not started.

## Results

| Group | Checks |
| --- | --- |
| Git histories and source snapshot | 15 |
| Real HTTP contract tests | 3 |
| Additional HTTP | 4 |
| Official SDK traces | 7 |
| Structured logs | 2 |
| Custom metrics | 4 |
| Statistics | 8 |
| Load mechanics | 5 |
| Local release gates | 9 |
| Workflow static checks | 5 |
| **Total** | **62** |

Tests cover index/worktree/HEAD, merge/conflict/abort/rebase/revert, local remote fetch/integration, real source snapshot identity, HTTP contracts/failures, W3C context and parent links, concurrent context isolation, log canary exclusion, bounded metrics and histogram checks, known percentile/budget cases, errors/deadlines in load reports, failed test/digest/health promotion gates and retained-good metadata rollback.

The load generator, gateway and dependency share one Node process. The normal measurement is 60 requests at closed concurrency four after six warm-up attempts, with fresh HTTP connections and no TLS/database. It is a short mechanism demonstration, not production capacity or a benchmark of any resume project. Raw samples are retained. OpenTelemetry traces use an actual SDK/in-memory exporter; metrics/logs are custom JSON structures, without a collector/Prometheus/backend.

## Files and boundaries

- app.mjs / serve.mjs: local gateway/dependency and owned candidate-process lifecycle.
- telemetry.mjs: official OpenTelemetry provider, W3C propagator and in-memory export.
- statistics.mjs / load.mjs: declared quantile/rate/error-budget arithmetic and bounded closed-model HTTP harness.
- contract.test.mjs: three actual HTTP interface tests with Node's built-in runner.
- git_lab.py: actual fixture Git operations and committed release-source snapshot.
- release.py / pipeline.py: source ZIP, manifest/digest verification, real candidate HTTP gates and local atomic selection/rollback.
- build_artifact.py: teaching source-bundle packaging command used by the example workflow.
- ci.example.yml / action-pins.json: inactive teaching workflow and commits resolved from official v7 action tags. YAML/policy/order checks are local; no hosted Actions execution occurred.
- package.json / package-lock.json / requirements.txt: execution dependencies.
- verification-results.json / verification-output.txt / cleanup-results.json: complete evidence and cleanup.
- git-results.json / node-results.json / pipeline-results.json: detailed subsystem checks and actual commands/events.
- contract-test-output.txt / node-verification-output.txt: actual test output.
- trace-output.json / application-log-output.json / load-results.json: actual trace/log/raw measurement evidence.
- release-artifact.zip / release-manifest.json / release-artifact.sha256: retained public source bundle and identity evidence.
- dependency-audit.json / content-validation.json / site-validation.json / validation-summary.json: audit and chapter/site checks.

The source bundle's revision identifies an actual disposable Git commit containing the packaged files. Candidate extraction beneath the module resolves the installed parent node_modules; the ZIP is not a self-contained production runtime image. current.json is local metadata, not a running traffic router. Rollback reselects retained metadata, without a database restore or traffic cutover. The failed-health injection changes candidate runtime health configuration while using the same v2 bundle.

The chapter includes 30 interview Q&As, ten exercises, 12 unchecked learning items, official sources and a release/diagnosis architecture walkthrough. It embeds tested teaching sources and exact recorded observations. Hosted Actions, cloud OIDC/provenance, production deployment/draining, schema/restore compatibility, distributed telemetry storage and production capacity/availability remain documented extensions.
