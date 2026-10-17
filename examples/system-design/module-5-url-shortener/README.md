# S0: URL shortener

Run `python verify.py` with Python 3.12 or later. The recorded run uses Python 3.12.10 and SQLite 3.49.1. It needs no third-party packages, Docker, Redis, cloud credentials or existing database service. Redirect tests use `http.client` and never follow or fetch destinations.

- `shortener.py`: global case-sensitive eight-character Base62 namespace, curated destination validation, real SQLite unique allocation with five-attempt bound, scoped atomic operation replay, owned management and disable.
- `service.py`: bounded local cache capped by absolute link expiry, local disable invalidation and explicitly lossy bounded analytics admission/recent SQLite aggregates. Independent caches can lag disable; no distributed invalidation exists.
- `http_api.py`: real owned loopback create/management/stats/disable API and public GET/HEAD 302/Location redirects. Uses trusted configured short origin and no-store. Published lesson tokens are not production authentication/TLS.
- `estimates.py`: hypothetical traffic/storage/namespace and birthday/next-draw collision arithmetic; no load or entropy benchmark.
- `verify.py`: 118 named assertions: 16 validation, 24 authority, 16 cache/expiry, twelve analytics, six concurrency, 34 HTTP, two cleanup and eight estimate checks. Four competing calls use independent thread-owned SQLite connections.
- `start.py`: optional manual server with a periodic best-effort analytics batch thread, ephemeral loopback port and temporary database. Ctrl+C closes resources/removes the session data. Use the printed local origin for redirects; short.example is illustrative.
- `author.py`: generates the worked chapter with four exact source files and six exact recorded observations.
- `integrate.py`: publishes S0 under a new Worked Systems sidebar group, fixes authored/planned progress and advances only the next section to S1.
- `validate_site.py` and `site-smoke.mjs`: source/result/link fidelity, production build, routes/navigation/search and owned-preview cleanup.

The curated URL policy accepts only ASCII HTTPS for example.com, www.example.com and docs.python.org, with no userinfo, whitespace/control/backslash ambiguity or non-default port. Exact accepted path/query/fragment is preserved. This is not a general validator, safety crawler or a claim that third-party destinations are trustworthy. The service never requests a target; adding previews introduces a separate SSRF/abuse boundary.

Public resolution is intentional. Management/statistics/disable remain scoped by creator and tenant; the code is not an authentication credential. Targets/lifetimes are immutable and codes are never automatically reused. Original create replay does not renew or reactivate an expired/disabled code. Retention/deletion of links and operation outcomes is not implemented.

The local cache and disable share one service lock. Two independent caches/connections demonstrate another instance serving old active state until refresh. This is not global immediate revocation or a hard distributed staleness guarantee under arbitrary clock/load failure. Absolute expiry is checked before returning a destination even on a warmed cache.

Analytics records selected GET redirect decisions, not unique human visits or confirmed destination navigations. Queue overflow, batch failure, process exit and stale events may lose records. Aggregates cover the current minute plus the prior two minute buckets; physical pruning occurs on flush. The verification harness invokes batches explicitly; the optional manual runner schedules them. Shared locks/SQLite still permit analytics contention, so no isolation/throughput claim is made.

After behavior changes:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

Verification closes its owned listener, joins serving/handler threads and four competing calls, closes SQLite connections and removes its exact temporary directory. Port 3000 and Docker remain stopped. The site build uses the existing cached font-response fixture when available. Use this chapter's validation summary for the expanded site; older summaries are historical snapshots.
