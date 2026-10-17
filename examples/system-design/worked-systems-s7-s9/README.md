# S7–S9 worked systems

Three independently authored chapters with actual local SQLite/HTTP examples. The shared `runtime.py` and `verification.py` are reused unchanged from `../worked-systems-s4-s6/`.

| Chapter | Source | Checks | Concurrency |
| --- | --- | --- | --- |
| S7 scheduler/workers | `../module-12-job-scheduler-workers/` | 65 | Two competing claim calls |
| S8 checkout/credit ledger | `../module-13-checkout-payments-credit-ledger/` | 62 | Two spends and two payment observations |
| S9 search/autocomplete | `../module-14-search-autocomplete/` | 77 | Two competing projector calls |

Use Python 3.12 with SQLite FTS5 and the existing installed site dependencies. From the repository root:

```powershell
python examples/system-design/module-12-job-scheduler-workers/verify.py
python examples/system-design/module-13-checkout-payments-credit-ledger/verify.py
python examples/system-design/module-14-search-autocomplete/verify.py
python examples/system-design/worked-systems-s7-s9/author.py
python examples/system-design/worked-systems-s7-s9/integrate.py
python examples/system-design/worked-systems-s7-s9/validate_site.py
```

The final command syncs content, verifies code/output fidelity, builds once, checks all handbook landing/companion routes and scoped search on an owned ephemeral loopback preview, then closes the preview. Port 3000 stays unused. `--reuse-build` is accepted only when relevant inputs are no newer than the successful build.

`verification-results.json` in each chapter records local checks and resource cleanup. `content-validation.json` records chapter structure and fidelity. This folder's `validation-summary.json`, `site-validation.json` and build/smoke logs record the final batch verification. Each chapter includes 30 Q&As, ten tasks, twelve unchecked learning items and a 45-minute mock. Learning checklists remain unchecked regardless of automated verification.

Scope: explicit-time scheduling and local counter effects; separate local provider/merchant stores and CREDIT journals; actual FTS5 plus authoritative local joins. No production broker, cron daemon, real charge/refund, cash ledger, external search cluster, semantic model, online reindex or capacity benchmark is executed. No persistent server or Docker process is started.
