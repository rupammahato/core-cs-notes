# S1: Rate limiter

Run `python verify.py` with Python 3.12 or later. Recorded versions: Python 3.12.10, SQLite 3.49.1. No third-party packages, Docker, Redis, cloud credentials or existing database service are required.

- `algorithms.py`: deterministic fixed-window, exact sliding-log and weighted sliding-counter comparisons, including an approximation counterexample. These classes assume trusted positive configuration and nondecreasing integer time; they are not concurrent request handlers.
- `limiter.py`: validated integer token bucket, trusted tuple scope, atomic SQLite read/refill/check/debit/write, per-bucket clock high-water mark, active policy conflict, bounded active state and conservative idle cleanup.
- `http_api.py`: real owned loopback lesson API with authenticated stable subject scope, 429/Retry-After/no-store, charged failed work and explicit read fail-open / write fail-closed behavior. Published lesson credentials are not production authentication.
- `estimates.py`: hypothetical traffic/state/replica/local-budget calculations, not memory or throughput benchmarks.
- `verify.py`: 95 named checks: eight algorithms, 16 validation, 14 bucket, 13 scope/lifecycle, seven concurrency, 26 HTTP, seven estimates and four cleanup. Includes four competing worker calls on separate thread-owned connections, a deliberately broken race, the atomic result and actual SQLite writer-lock timeouts.
- `start.py`: optional ephemeral loopback manual server with a temporary database. Ctrl+C closes the listener and removes session data. Automated work does not leave this running or use port 3000.
- `author.py`: chapter generator embedding four exact sources and six recorded outputs.
- `integrate.py`: adds S1 to the existing Worked Systems group, refreshes authored progress and advances the next section to S2.
- `validate_site.py` and `site-smoke.mjs`: source/output/link fidelity, production build, existing/new routes, search/navigation and owned preview cleanup.

The token store is a local SQLite teaching authority, not Redis emulation or several deployed machines. SQLite serializes writers for the entire file. The 200 ms busy timeout bounds this dependency wait, not total HTTP latency. Callers use consistent server-side time/policy; clock rollback is clamped, while forward jumps, cross-authority clock skew, state loss and distributed failover remain outside the guarantee. Active policy mismatch is rejected; live migration is not implemented, and policy identity disappears when an idle bucket is pruned.

Denials persist refill/time state but do not debit tokens. Successful admissions debit before work and stay charged on work failure. Retry-After is rounded up and reserves no future credit. Custom X-Lesson-Quota headers are teaching fields. Fail-open deliberately relaxes the shared quota; production authentication/TLS, hierarchical budgets, a global clock, leases, emergency local protection and throughput benchmarking are not implemented.

Idle cleanup waits a conservative full-refill period after the last effective decision. Deleting live buckets or starting with an empty authority would grant fresh credit. At the live-key cap, new scopes fail while existing scopes retain their state. Cleanup/counting on each transaction is deliberately simple and not a scale claim.

After behavior changes:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

The harness joins its worker/server threads, closes owned connections/listeners and removes its exact temporary directory. Port 3000 and Docker remain stopped. Site checks use the existing cached font fixture when available. Use this latest chapter's summary for the expanded site; older verification summaries remain historical snapshots.
