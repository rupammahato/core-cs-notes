# P1: pricing and unit economics

Run from the repository root (Python 3.13.15; standard library only):

```powershell
python -X utf8 examples/product-analytics/module-1-pricing-unit-economics/economics.py
python -X utf8 examples/product-analytics/module-1-pricing-unit-economics/verify.py
```

The model has 88 checks covering normalization, duplicate/conflicting evidence, unknown usage, final outcome cohorts, margin denominators, price-floor rounding, break-even boundaries, idealized retry cost and single-pack credit allocation. Actual output and runtime are in economics-output.json and verification-results.json.

All rates and jobs are invented. Missing usage remains unknown; an explicit supplied replacement simulates reconciliation. Failed attempts and jobs retain their known cost. Repeated identical attempt reports are ignored; conflicting identities are rejected. Output rounds to six decimal places for display, while the price-floor calculation retains the higher-precision value for upward cent rounding. Input amounts are decimal strings, bounded nonnegative values with at most twelve decimal places; usage is bounded integer quantities. The model assumes structured input and rejects unsupported tariffs/currencies. It is not a general schema validator or arbitrary-precision accounting engine.

The model does not implement durable storage, concurrent reservations, a payment or credit ledger, real usage adapters, FX, invoice adjustments, taxes, mixed credit-grant allocation, refund accounting or revenue recognition. Its cohort margin assumes fixed revenue per successful action and explicitly classified synthetic costs. The independent break-even scenario assumes stable unit contribution and capacity. Retry cost c/s assumes unlimited independent equal-cost attempts until success.

No provider, gateway or account was accessed. Public primary sources and evidence limits are recorded in research.json. Historical Zyke claims are referenced from earlier M28 and are not proven by these fixtures.

validate_content.py checks note/output fidelity, routes, chapter structure and preservation of the original 121 handbook files. site-smoke.mjs checks a temporary production preview and closes its own process. Port 3000 remains unused.

Integration verified on 18 October 2026: webpack production build and TypeScript passed, 129 static pages, 125 successful page routes, P0/P1 navigation and four scoped searches. Planned P2 returns 404. The temporary preview closed and port 3000 is stopped. See validation-summary.json; the existing cached font fixture was used for the build. Historical runtime suites were not rerun.
