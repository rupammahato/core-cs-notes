# P4 marketing measurement and visualization

Invented campaign, order, touch and claim data. This companion does not establish original project results, actual platform attribution, causal lift or a delivered marketing digest.

## Run

From the repository root:

```powershell
python examples/product-analytics/module-4-marketing-measurement-data-visualization/measurement.py
python examples/product-analytics/module-4-marketing-measurement-data-visualization/verify.py
```

Python standard library only. Verified on Python 3.13.15 and SQLite 3.50.4: **79 checks passed**. case.json is the unchanged input; measurement-output.json contains executed results and verification-results.json preserves assertions and versions.

Campaign grain is one row per campaign within one supplied USD/UTC report snapshot. Exact repeats are removed and conflicts rejected. Extend the identity key before adding dates, accounts or breakdowns. The local order illustrations use supplied timestamps and hand-defined attribution policies; they are not a reproduction of the aggregate report's attribution model.

Amounts are cents. Ratios are rounded to six decimal places after calculation. Missing values remain distinct from zero; complete ratios are withheld when a required component is missing. Conversion credits may be fractional. The ledger's new-customer flags are supplied facts, not inferred from complete customer history.

## Browser companion

Enter this folder and run:

```powershell
npm ci --ignore-scripts --no-audit --no-fund
npm run verify
```

The isolated lockfile pins D3 7.9.0 and Playwright 1.62.1. The verifier uses an installed Google Chrome via Playwright's chrome channel. Chrome 155.0.8059.84 passed **36 browser checks** for real keyed joins, scales, hierarchy sums, filtering, zero/missing/empty states, exact tables, responsive geometry and script/network errors. It opens no external account and blocks nonlocal page requests. It always closes its browser and temporary loopback server.

For a manual preview from this folder:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765 and stop that command with Ctrl+C when finished. This is an optional reader command; automated verification leaves no server running and does not start port 3000.

The bar's measure and channel filter are interactive; the treemap always sizes known nonnegative spend and colors channel. Its exact values remain in the table. Domains and layout recompute after filtering and resize. This is a standalone companion, not an embedded React chart. Desktop and mobile screenshots under ignored outputs/qa were reviewed; a full accessibility audit remains manual.

## Other evidence

The SQLite DigestStore is an in-memory publication model. It verifies exact retries, same-revision conflicts and replacement by a later revision. It is not a scheduler, durable outbox, distributed concurrency or notification delivery implementation. No Telegram message or advertising-budget action is sent.

research.json lists primary documentation and the unavailable Meta documentation-page fallback to official SDK source. validate_content.py audits chapter output blocks, sources, structure, generated routes and prior-note hashes. site-smoke.mjs checks production-site pages and scoped search through its own temporary server. validation-summary.json records the completed verification scope.
