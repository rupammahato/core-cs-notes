# P3 Python and Excel analysis companion

Synthetic source reconciliation; original CSVs remain separate from derived outputs. No real billing, provider invoice or customer outcome is established.

Jobs have job grain, attempts have attempt grain and workspaces form a unique dimension. The report uses aware UTC job timestamps in `[2026-10-01, 2026-11-01)`. Exact repeated identities are removed; conflicting repeats fail. Missing money remains unknown. Orphan costs stay separate.

## Run the analysis

From the repository root, in an isolated Python environment:

```powershell
python -m pip install -r examples/product-analytics/module-3-python-excel-analysis/requirements.txt
python examples/product-analytics/module-3-python-excel-analysis/analysis.py
python examples/product-analytics/module-3-python-excel-analysis/verify.py
```

Executed with Python 3.12.14, NumPy 2.3.5 and pandas 3.0.1: **72 checks passed**. analysis-output.json and prepared-inputs.json are actual outputs. verification-results.json records assertions and versions. A different interpreter needs its own dependencies.

The selected population contains five jobs, four completed, 290 known billed cents and two unknown bills. Complete billing is withheld. Provider cost is 110 cents; an unmatched seven-cent attempt remains separate. A deliberately wrong join inflates billing to 490 cents.

## Workbook

Open outputs/p3-analysis/analysis-practice.xlsx. Analysis contains controls, results and job-grain formulas. Sources contains prepared job, attempt and workspace tables. Source timestamps carry a visible `raw: ` prefix to preserve literal offsets during authoring; the normalized column contains numeric UTC dates. Original CSV text remains unchanged.

Existing inputs and report controls recalculate. This is a prepared snapshot, not an automatically refreshing CSV connection. New rows require rebuilding or updating every dependent range. Formulas assume the prepared schema; arbitrary malformed edits require revalidation.

The plan summary uses SUMIFS. **No native PivotTable is included.** Follow the manual chapter exercise on Analysis A19:L28, filter In period to 1, group Plan by Status and count Job ID.

build-workbook.mjs uses @oai/artifact-tool 2.8.99 without adding repository dependencies. Here its ignored node_modules junction resolves the bundled runtime. Rebuild with:

```powershell
& 'C:/Users/Win11/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' examples/product-analytics/module-3-python-excel-analysis/build-workbook.mjs
```

Elsewhere, provide the same package in the builder's module resolution environment. The builder verifies baseline formulas, runs six input-mutation scenarios, restores baseline, scans errors, exports and renders both sheets. The authoring operation marker was issued once during initial creation, not during ordinary rebuilds.

verify-excel.ps1 requires desktop Excel on Windows. It starts a hidden instance, opens a disposable copy under ignored outputs/qa, checks baseline and mutations, scans errors and closes its own instance without saving. It never edits the final workbook. **38 checks passed in Excel 16.0 build 20430**, separately from the six authoring-engine scenarios.

validate_content.py audits output fidelity, research, structure, routes and preservation. site-smoke.mjs checks the built site on a temporary loopback port and closes its own process. Port 3000 remains stopped.

All data is invented. The checks establish stated local program/formula behavior, not completion of reader exercises or parity with production invoices. Research and runtime boundaries are in research.json.
