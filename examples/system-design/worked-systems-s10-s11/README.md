# S10–S11 worked systems

Two independently authored chapters using the unchanged `runtime.py` and `verification.py` from `../worked-systems-s4-s6/`.

| Chapter | Fixture | Checks | Competing calls |
| --- | --- | --- | --- |
| S10 load balancer/cache | `../module-15-load-balancer-distributed-cache/` | 69 | Two cold reads and two source CAS writes |
| S11 tenant SaaS | `../module-16-multi-tenant-saas/` | 95 | Two invitation accepts and two quota creates |

From repository root with standard-library Python 3.12 and the existing site dependencies:

```powershell
python examples/system-design/module-15-load-balancer-distributed-cache/verify.py
python examples/system-design/module-16-multi-tenant-saas/verify.py
python examples/system-design/worked-systems-s10-s11/author.py
python examples/system-design/worked-systems-s10-s11/integrate.py
python examples/system-design/worked-systems-s10-s11/validate_site.py
```

The last command verifies chapter structure and exact code/output fidelity, syncs content, builds the site once and checks navigation/search on an owned ephemeral loopback preview. It closes the preview. Port 3000 remains stopped, and Docker is never started. `--reuse-build` requires all relevant inputs to predate the recorded successful build.

Per-chapter JSON records local assertions, content fidelity and resource cleanup. This folder's `validation-summary.json`, `site-validation.json` and build/smoke logs hold batch evidence. Each chapter includes 30 Q&As, ten tasks, twelve unchecked learning items and a 45-minute mock. Automated checks do not mark learner mastery complete.

S10 uses in-process cache nodes and backend labels, canonical version probes on every read, controlled health changes and a deterministic placement sample. It is not a network proxy, Redis cluster, membership protocol or throughput benchmark. S11 uses trusted fixture identity issuance and actual opaque bearer HTTP; no browser/OIDC/BFF/cookie/CSRF flow, email, object store or RLS deployment is executed. Read each chapter's scope before extending it.
