# P2: product analytics and experiments

Run from the repository root with Python 3.13.15 (standard library; SQLite 3.50.4 recorded):

```powershell
python -X utf8 examples/product-analytics/module-2-analytics-experiments/analytics.py
python -X utf8 examples/product-analytics/module-2-analytics-experiments/verify.py
```

The 95 executed checks cover event/schema/property validation, explicit alias mapping, delivery duplicates, receipt time, timezone and boundary behavior, ordered same-operation funnels, mature cohorts, exact-period retention, late-data revisions, activity units and aggregate experiment calculations. metrics.sql contains the actual SQLite query. The database is in memory and explicitly closed on normal and rejected-input paths. No persistent listener or external service is used.

All events, users and experiment counts are invented. The event observation cutoff stays fixed while initial and revised knowledge cutoffs differ. Generation success at exactly 24 hours is excluded; equal whole-second start/success timestamps use nondecreasing order. Incomplete follow-up excludes both recent converters and non-converters. D7 means the elapsed interval [signup+7 days, signup+8 days); cohort labels are UTC signup dates. Receipt before occurrence is rejected by this fixture policy, not asserted impossible in production. The alias registry is explicit and static; no automatic identity resolution or vendor person processing is implemented.

The experiment helper computes a normal interval with unpooled variance, a pooled two-sided equality test and a two-category chi-square SRM approximation. It withholds the normal calculation if either group has fewer than ten observed successes or failures, and withholds SRM p-values for expected counts below five. Those guards do not establish independent units, proper randomization, mature outcomes or valid stopping. The SRM flag uses an illustrative threshold of 0.001. No exact, clustered, sequential or power-analysis method is implemented. assignment_verified is always false for these aggregate synthetic inputs.

The fixture assumes structured records and does not implement an arbitrary schema validator, real tracking SDK, user authentication, production ingestion, analytics-platform parity, consent tooling or a genuine randomized experiment. See research.json for sources and boundaries. The chapter's vendor exercises remain manual.

validate_content.py audits exact output projections, chapter structure, internal routes and source preservation. site-smoke.mjs checks a temporary local production preview and closes its own process. Port 3000 is not used.

Integration verified on 18 October 2026: webpack production build, TypeScript, 130 static pages and 126 successful page routes. P1/P2 navigation and five scoped searches passed; planned P3 returns 404. The temporary preview closed, port 3000 is stopped and the in-memory database is closed. The existing cached font fixture was used. Historical runtime suites were not rerun; see validation-summary.json.
