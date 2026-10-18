# Product and Analytics Placement Handbook — Part 5: P3: Python and Excel for Analysis

**Turn source rows into a calculation you can explain, reproduce and reconcile.**

**Verification, 18 October 2026:** 72 Python checks passed with Python 3.12.14, NumPy 2.3.5 and pandas 3.0.1. The companion workbook passed 38 native Excel checks in Excel 16.0, build 20430, plus six Artifact Tool mutation scenarios. The numerical results below come from the preserved synthetic inputs. The PivotTable exercise is manual; the workbook's plan summary uses SUMIFS.

---

## 3.0 Why this section belongs in a product interview

A product analyst is asked why the spreadsheet says one amount while the backend export says another. Knowing a function name is insufficient: the analyst must identify what each row represents, which rows belong in the report, and whether missing data makes the proposed conclusion incomplete.

This chapter connects the metric definitions in [P2](/docs/product-analytics/product-analytics-experiments) and the cents, retries and cost distinctions in [P1](/docs/product-analytics/pricing-unit-economics) to practical analysis. Python language fundamentals remain in [M10](/docs/resume-skills/python-fundamentals); ingestion architecture is covered in the earlier resume-skills track.

The questions are editorial interview priorities for this resume, rather than a measured ranking of company interview frequency. The resume's Python, analysis and spreadsheet context motivates practice; this teaching dataset does not establish original project outcomes.

### What you should be able to explain

- Why NumPy arrays, pandas tables and Excel are useful for different parts of an analysis.
- How shape, dtype, labels, missing values and dates affect a result.
- Why a join can increase money without introducing new transactions.
- How formulas, lookups and PivotTables differ.
- How to investigate a mismatch before presenting a business recommendation.

## 3.1 Start with the row contract

**Grain** means what one row represents. Write it before joining or aggregating.

| Source | Grain after validation | Identity | Meaning of amount |
| --- | --- | --- | --- |
| Jobs | One final job record | job_id | Job-level billed cents; blank means unknown |
| Attempts | One provider attempt | attempt_id | Attempt cost in cents; retries are separate attempts |
| Workspaces | One workspace | workspace_id | Dimension attributes, with one plan per key |

One job may have several attempts. Repeating a job's billing once for each attempt changes the grain and inflates a sum. Repeated delivery of the *same* attempt is different from a legitimate retry with a new attempt ID.

The report uses job occurrence time in the UTC interval from 1 October 2026 inclusive to 1 November exclusive. That is a chosen teaching contract, not a claim that all businesses should report in UTC. An invoice report might use posting time and a different population.

```text
Original CSVs, unchanged
  -> validate identities, types and conflicts
  -> remove exact repeated identities
  -> normalize aware dates; retain date issues
  -> aggregate attempts to job grain
  -> join jobs to costs and workspace dimension
  -> apply reporting interval
  -> publish known subtotals + completeness indicators
  -> reconcile orphan costs and excluded records separately
```

**Interview opening:** “I would first align the entity, grain, currency unit, date field and reporting interval. Then I would inspect duplicate keys and missing data before comparing totals.”

## 3.2 NumPy, pandas and Excel: what each does

| Tool | Main model | Useful for | Watch for |
| --- | --- | --- | --- |
| NumPy | Typed multidimensional arrays | Numerical operations over many values | Shape, overflow, positional assumptions and shared memory |
| pandas | Labelled Series and DataFrames | Imports, joins, groups, dates and audit tables | Label alignment, missingness and join cardinality |
| Excel | Cells, formulas, tables and summaries | Reviewable models, ad hoc exploration and stakeholder handoff | Cell types, copied references, hidden filters and refresh state |

A NumPy array usually has one dtype. A DataFrame can have different dtypes across columns. Excel cells can mix numbers, strings, dates and formulas, which is convenient but makes accidental type changes easy.

Use pandas to prepare a repeatable reconciliation and Excel to inspect the line items and vary assumptions. Repeating a calculation in two tools helps only when the two implementations also agree on the population and units.

## 3.3 Arrays, shape, dtype and axes

An array's **shape** records the length of each dimension. A two-dimensional shape of `(2, 3)` means two rows and three columns. **dtype** determines the element representation; `int64` stores fixed-width integers.

The executed example treats rows as two workspaces and columns as three usage categories:

```python
usage = np.array([[10, 20, 30], [1, 2, 3]], dtype=np.int64)
rates = np.array([2, 3, 4], dtype=np.int64)
weighted_rows = (usage * rates).sum(axis=1)
matrix_vector = usage @ rates
```

`axis=0` reduces the row dimension, leaving one result per column. `axis=1` reduces the column dimension, leaving one result per row. Describe the remaining result rather than memorizing “vertical” or “horizontal.” The arrays here are synthetic teaching units, not actual provider prices.

This is the exact NumPy observation from `analysis-output.json`:

```json
{
  "shape": [2, 3],
  "dtype": "int64",
  "broadcast_product": [[20, 60, 120], [2, 6, 12]],
  "column_sums": [11, 22, 33],
  "row_sums": [60, 6],
  "weighted_rows": [200, 20],
  "matrix_vector": [200, 20],
  "original_after_slice_edit": [1, 99, 3, 4],
  "fancy_copy_after_edit": [-1, 3]
}
```

Integer cents avoid decimal representation issues for these inputs. Fixed-width integer arithmetic can still overflow; validate ranges and the largest possible aggregate. Divisions introduce ratios and require explicit handling of zero denominators.

Reference: [NumPy beginner guide](https://numpy.org/doc/stable/user/absolute_beginners).

## 3.4 Broadcasting and vectorization

Broadcasting compares dimensions from the right. Corresponding dimensions must be equal or one must be 1. Missing leading dimensions behave as size 1. Here `(2, 3)` and `(3,)` are compatible, so each row is multiplied by the same three rates. NumPy need not materialize a second full rates matrix. [NumPy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html).

Vectorization expresses operations over arrays rather than writing a Python loop for each element. This can reduce interpreter overhead, but does not guarantee that every expression is faster or memory efficient. Large temporary arrays may dominate memory usage. `np.vectorize` is primarily a convenience wrapper around repeated function calls, rather than an automatic conversion to a fast native numerical kernel.

`*` is elementwise multiplication; `@` is matrix multiplication. In this example a matrix multiplied by a vector produces the same weighted row totals as an elementwise product followed by a row sum. They are different operations with different shape contracts.

For boolean masks use `&`, `|` and `~`, and parenthesize comparisons. Python's `and` asks for the truth value of an entire array and cannot express an elementwise combination.

## 3.5 Views, copies and mutation

The executed example creates a basic slice `original[1:3]` and changes its first element. The original changes because the slice shares the underlying data. Selecting `original[[0, 2]]` uses advanced indexing and produces a copy, so changing that result leaves the original unchanged. [NumPy copies and views](https://numpy.org/doc/stable/user/basics.copies.html).

Do not assume every reshape copies or every selection shares memory. Check ownership when mutation matters; use an explicit copy where an independent working buffer is required. Reshape may return a view when the layout permits it and otherwise may copy.

**Interview follow-up:** “If a cleaning step unexpectedly changes my raw array, I would inspect whether I assigned a view. I would reproduce the mutation on a small input and make the independence requirement explicit.”

NumPy memory behavior and pandas Copy-on-Write are separate concepts; do not transfer one tool's mutation rules to the other.

## 3.6 Series, DataFrames and index alignment

A Series is a one-dimensional labelled object. A DataFrame is a two-dimensional labelled table. Their indexes identify labels used for selection and alignment; an index is not automatically a unique database key.

`.loc` selects by labels and masks. `.iloc` selects by integer position. A label that happens to be an integer still has label semantics with `.loc`. Check index uniqueness if the analysis expects one record per label.

The runnable case adds two Series with the same labels in different orders. Adding Series aligns labels; adding the extracted NumPy arrays uses position:

```json
{
  "label_sum": {"a": 11, "b": 22},
  "positional_sum": [21, 12]
}
```

Converting to `.to_numpy()` discards the alignment contract. Do it only when order is independently established. A positional result that has the expected length can still pair the wrong users or products.

For assignments, prefer one explicit operation such as `df.loc[mask, "status"] = "review"`. pandas 3 uses Copy-on-Write: a derived object behaves independently when modified, while internal storage may be shared until a write. Chained assignment does not reliably express an update of the original table; with Copy-on-Write it cannot update the original through the chained target. The example was checked on pandas 3.0.1. [pandas Copy-on-Write](https://pandas.pydata.org/docs/user_guide/copy_on_write.html).

## 3.7 Import identifiers and amounts intentionally

The CSV loader uses explicit string columns and disables default missing-token inference:

```python
pd.read_csv(path, dtype="string", keep_default_na=False)
```

This keeps an ID such as `0001` intact and lets the contract decide which tokens mean missing. It is not permission to leave every measure as text: the pipeline converts amount columns to nullable `Int64` after validating whole-cent strings or explicit blanks.

The fixture rejects negative, fractional, malformed and out-of-range amount strings. This is a teaching schema; a refunds ledger would need a signed amount policy and a clear event model. Do not silently remove a minus sign to make a validation pass.

Useful first checks are column names, row counts, dtypes, identity uniqueness, null counts, allowed categories and small samples around boundaries. `.head()` alone cannot establish that a full import is valid.

## 3.8 Missing, zero, empty and invalid are different states

| State | Meaning in this case | Correct treatment |
| --- | --- | --- |
| Billed amount 0 | Known zero billing | Include as an observed amount |
| Blank billing | Unknown amount | Preserve missingness and count it |
| Malformed amount | Violates schema | Reject rather than quietly reinterpret |
| No matching workspace | Dimension coverage gap | Retain job as Unmapped |
| No cost attempt for a job | No cost evidence | Mark cost incomplete, rather than infer free work |

Use `.isna()` to detect missing values; equality with a missing sentinel is not a general missingness test. `pd.NA` also cannot be used as an ordinary boolean. Nullable arithmetic and comparisons can propagate unknown results. Decide what an unknown mask means before filtering; the policy must follow the business question. [pandas missing-data guide](https://pandas.pydata.org/docs/user_guide/missing_data.html).

The default sum of an all-missing Series can yield zero. `sum(min_count=1)` requires at least one known value. Even that only returns a **known subtotal** when some values remain missing. The pipeline separately counts missing jobs and withholds the complete total.

Do not use blanket `fillna(0)` to make a dashboard look finished. Replace missing values only where the domain guarantees that absence means zero.

## 3.9 Duplicate handling is a business rule

There are ten raw job rows but nine distinct job identities, and ten attempt rows but nine distinct attempts. The repeated job `0002` and attempt `a02` are exact repeats. Removing those repeats is valid under the fixture's identity contract.

If two rows with one identity disagree, the pipeline raises a conflict. “Keep the last row” is valid only if the source supplies a trustworthy version or ordering rule. Physical file order is not inherently a revision sequence.

Two attempts for job `0002` are legitimate: `a01` and `a02` have different identities. Deduplicating on job ID would delete real provider cost. Two users having the same name is also not evidence that they are the same user.

**Three questions before deduplication:** What is the identity? Which fields must agree? If they disagree, what source establishes the authoritative version?

## 3.10 Joins and cardinality

| Join | Population retained | Typical analysis use |
| --- | --- | --- |
| Left | Every left record, plus matching right records | Enrich jobs without discarding unknown dimensions |
| Inner | Matching records only | Explicit matched-only population, with exclusions reported |
| Outer | Keys from either side | Reconciliation and source coverage |
| Anti-match | Left keys absent on right | Orphan costs or missing dimension keys |

A left join can increase the number of rows when the right side has repeated keys. “Left” describes retention, not uniqueness.

The pipeline aggregates attempts to job ID first. That table has at most one row per job, so its merge uses `validate="one_to_one"`. Joining jobs to workspaces uses `validate="many_to_one"` and an indicator to expose unmatched dimensions. pandas also matches null join keys to other null keys, which differs from ordinary SQL null equality; this fixture rejects blank relationship keys before joining. [pandas merge API](https://pandas.pydata.org/docs/reference/api/pandas.merge.html).

For a direct jobs-to-attempts join, many attempts per job are expected. A cardinality check cannot make summing repeated job billing valid. You must use the correct grain for each measure.

## 3.11 The join that invents billing

The selected job set has five jobs. A deliberately incorrect direct attempt join produces six rows because job `0002` has two attempts. Its known billed subtotal rises from **290 cents to 490 cents**. No new billed job was created.

The corrected sequence is:

```python
costs = attempts.groupby("job_id", dropna=False).agg(
    known_cost_cents=("cost_cents", lambda s: s.sum(min_count=1)),
    missing_cost_lines=("cost_cents", lambda s: int(s.isna().sum())),
)
facts = jobs.merge(costs, on="job_id", how="left", validate="one_to_one")
facts = facts.merge(workspaces, on="workspace_id", how="left",
                    validate="many_to_one", indicator="dimension_match")
```

Compare the sum of job-level money before and after enrichment, audit unique job counts, and inspect unmatched keys. A grand total that happens to agree is weaker evidence than row-level reconciliation. [pandas merge guide](https://pandas.pydata.org/docs/user_guide/merging.html).

## 3.12 groupby, agg, transform and counts

`groupby` partitions rows by keys. `agg` reduces each group to summaries. `transform` produces results aligned to the original rows, useful for adding a group total beside each job. Joining a reduced group result back is another option if its key uniqueness is checked.

`size` counts rows; `count` counts nonmissing values in a selected column. They answer different questions when billing is missing. A revenue count is not automatically a job count.

The fixture's grouped analysis specifies `dropna=False`, `observed=True` and `sort=True` explicitly. This makes missing-key policy, categorical behavior and presentation order visible rather than relying on changing defaults. It fills unmatched plans with an explicit Unmapped label before grouping.

Do not average subgroup percentages unless equal weighting is part of the definition. For an overall completion share, combine completed-job counts and eligible-job counts. If group sizes differ, each group's percentage needs its denominator as a weight.

## 3.13 pivot, pivot_table and crosstab

`pivot` reshapes a table when each row/column key pair identifies at most one value. Duplicate pairs require resolution. `pivot_table` combines reshaping with aggregation, so specify the aggregation rather than accepting a mean by accident. `crosstab` is convenient for frequency tables.

The runnable case counts plan by final status. It explicitly reindexes the status columns so a missing category does not change the expected schema:

```json
{
  "Unmapped": {"completed": 1, "failed": 0},
  "free": {"completed": 1, "failed": 1},
  "paid": {"completed": 2, "failed": 0}
}
```

These zeros mean no selected jobs in those combinations. They do not mean an unknown monetary amount is zero. Displaying the same shape as a spreadsheet PivotTable does not establish that a native Excel PivotTable was created.

## 3.14 Dates, UTC and half-open intervals

The source parser accepts timestamps with an explicit offset or `Z`. It converts aware dates to UTC using `pd.to_datetime(..., format="ISO8601", errors="coerce", utc=True)`. Missing, invalid and naive source dates become audited date issues. It does not guess that a naive local timestamp means UTC. [pandas datetime conversion](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html).

Job `0001` says `2026-10-01T00:30:00+05:30`. In UTC that is 30 September at 19:00, so it is outside this report. Job `0006` is exactly `2026-11-01T00:00:00Z`, so the exclusive endpoint excludes it. Jobs `0007` and `0008` have date issues and remain visible in an audit list.

```python
in_period = facts["occurred_utc"].ge(start) & facts["occurred_utc"].lt(end)
selected = facts.loc[in_period].copy()
```

The interval `[start, end)` avoids overlapping adjacent reporting periods and does not depend on guessing the last representable moment of a day. For a local business month, construct timezone-aware local boundaries, resolve daylight-saving ambiguity if relevant, then compare equivalent instants. The boundary policy must be consistent across Python, SQL and Excel.

`errors="coerce"` is a conversion policy, not an excuse to discard failures. Publish the rejected or unresolved count and a path to correction.

## 3.15 The executed reconciliation

Selected jobs are `0002`, `0003`, `0004`, `0005` and `0009`. This exact projection is taken from the preserved report:

```json
{
  "selected_jobs": 5,
  "completed_jobs": 4,
  "completion_share": 0.8,
  "known_billed_cents": 290,
  "missing_billed_jobs": 2,
  "complete_billed_cents": null,
  "known_provider_cents": 110,
  "missing_cost_jobs": 0,
  "complete_provider_cents": 110,
  "orphan_attempts": ["a09"],
  "orphan_cost_cents": 7,
  "orphan_missing_cost_lines": 0,
  "wrong_direct_join_rows": 6,
  "wrong_direct_join_billed_cents": 490
}
```

Billing is incomplete because two jobs have unknown amounts. The provider total is complete **for the selected job population and supplied attempt evidence**, not for an independently audited provider invoice. Attempt `a09` has seven cents of known cost but no matching job. It is kept separate; without a matching timestamped job, assigning it to this report month would invent evidence.

Job `0009` lacks a workspace match but remains selected as Unmapped. An inner join would hide it. Its 90 cents is part of the known billed subtotal even though the plan classification is unresolved.

**Decision:** do not report a final billing or margin number. Resolve missing billing, investigate date issues and the unmatched cost, and confirm the reporting contract. A completed share of 80% describes these five final job records; it does not establish user retention or causal product improvement.

## 3.16 A repeatable analysis pipeline

Keep source data immutable and store derived outputs separately. The companion contains the three CSVs, `analysis.py`, `verify.py`, version pins, actual JSON outputs, workbook builder and native Excel verifier.

From the repository root, after installing the pinned analysis dependencies in an isolated environment:

```powershell
python -m pip install -r examples/product-analytics/module-3-python-excel-analysis/requirements.txt
python examples/product-analytics/module-3-python-excel-analysis/analysis.py
python examples/product-analytics/module-3-python-excel-analysis/verify.py
```

The documented results were executed with Python 3.12.14. A different machine must install dependencies into the interpreter it actually runs; the system Python used for other chapters does not automatically contain pandas. The workbook's build instructions are in the example README.

The checks use independently specified expected outputs, boundary cases and changed inputs. They cover duplicate conflicts, join inflation, date normalization, missing-versus-zero behavior, masks, label alignment, copies and source preservation. They do not prove that arbitrary external exports satisfy this schema.

For a real workflow, record the source snapshot, extraction interval, schema version, code revision and runtime versions. Stable ordering makes output diffs understandable. A notebook run out of order can hide stale state; a clean script run is a useful reproducibility check.

## 3.17 Excel foundations: cells, tables and references

An Excel date is represented numerically with a date format; a date-looking string is different. An identifier should remain text when leading zeros matter. A display format alone cannot recover digits lost during import. [Microsoft: keeping leading zeros](https://support.microsoft.com/en-us/excel/keeping-leading-zeros-and-large-numbers).

| Reference | Copy behavior | Example use |
| --- | --- | --- |
| A2 | Row and column move | Current row input |
| $A$2 | Row and column fixed | Report boundary |
| $A2 | Column fixed, row moves | A row label across periods |
| A$2 | Row fixed, column moves | A period header down categories |

An Excel Table provides named columns, filter controls and a defined data region. Structured references make formulas easier to read and often extend with table rows. Formulas using fixed cell ranges still need their own range-extension policy.

The companion uses named source tables but fixed teaching ranges for formulas. Existing input edits and reporting dates recalculate; adding source rows requires rebuilding or deliberately updating all dependent ranges. Do not promise automatic CSV refresh.

Filters can hide rows without removing them from ordinary SUMIFS calculations. If the intended calculation is “visible rows only,” use a suitable visible-row method and document that different population. Also check hidden rows and active filters while reconciling an export.

## 3.18 SUMIFS, COUNTIFS and explicit units

SUMIFS aggregates a measure across rows meeting all supplied conditions; COUNTIFS counts qualifying rows. Keep criteria and sum ranges aligned. A report for aware UTC instants has already been normalized before the workbook receives numeric dates. [Microsoft SUMIFS guidance](https://support.microsoft.com/en-us/excel/sum-values-based-on-multiple-conditions).

In the exported workbook, `Analysis!B5` is the start and `E5` the exclusive end. Each row of the job build uses:

```text
=IF(ISNUMBER(B20),IF(AND(B20>=$B$5,B20<$E$5),1,0),0)
```

Here B20 is a job's normalized timestamp and G20 receives the period flag. Jobs with unresolved dates get a zero period flag **and** remain counted in the separate date-issue audit.

The plan summary aggregates the job build, not the attempt source:

```text
=SUMIFS($I$20:$I$28,$C$20:$C$28,E8)
```

Column I holds known billed cents for selected jobs; column C holds plan. A neighboring summary counts missing billing, so a displayed known subtotal does not masquerade as a complete amount.

The workbook uses numeric counts and cents, percentage formatting for the completed share, and the text `n.a.` for withheld totals. It does not mix currency symbols into numeric inputs.

## 3.19 Lookups answer a different question from sums

An exact lookup answers “which attribute belongs to this key?” An aggregation answers “what is the total across these matching records?” Looking up one cost attempt cannot calculate a job's total retry cost.

XLOOKUP returns the corresponding first match by default and uses exact matching by default. A duplicate key can therefore produce a plausible result without exposing ambiguity. Always establish key cardinality first. [Microsoft XLOOKUP documentation](https://support.microsoft.com/en-us/excel/functions/xlookup-function).

The companion uses exact INDEX/MATCH inside explicit COUNTIFS guards, making these cases distinct:

- No workspace key match: Unmapped.
- More than one matching key: Duplicate key.
- One key match with a blank plan: Missing plan.
- One key match with a present plan: that plan.

The native Excel checks change a key to create ambiguity and clear a plan value to verify both paths. A broad `IFERROR(...,0)` would conceal the difference between no match, a broken reference and an actual zero amount.

The workbook's guard diagnoses dimension problems but is not a general data-entry validator. Its prepared inputs follow the Python schema; edits outside that schema require revalidation before treating the report as reliable.

## 3.20 PivotTables: a manual practice workflow

A PivotTable groups a source table and computes summaries that can be rearranged interactively. It is useful for exploring categories and checking grouped counts without writing a new formula for every view. [Microsoft PivotTable creation](https://support.microsoft.com/en-us/excel/get-started/create-a-pivottable-to-analyze-worksheet-data).

**Manual exercise — no native PivotTable is included in the generated file:**

1. Open a practice copy and choose `Analysis!A19:L28`, including its header row.
2. Insert a PivotTable into a new worksheet.
3. Put Plan in Rows and Status in Columns.
4. Put Job ID in Values, explicitly selecting Count.
5. Add In period as a filter and select 1.
6. Compare the resulting matrix with the executed crosstab in section 3.13.
7. Add Period billed as a Sum and Missing bill as a Sum. Keep the latter visible.
8. Change an input and inspect the result after the necessary source refresh/recalculation steps.

This source is one row per prepared job. Using the attempt-level source would count attempts. Excel's default choice of Count or Sum can depend on source types, so inspect Value Field Settings. Count of Job ID avoids treating a numeric-looking identifier as an additive quantity.

PivotTable source changes and refresh behavior depend on the Excel version, source and settings. Use a deliberate refresh step and inspect its result; do not assume that pressing a cell-recalculation key refreshes every data connection and PivotTable. [Microsoft refresh guidance](https://support.microsoft.com/en-us/excel/refresh-pivottable-data).

## 3.21 Using the companion workbook

The final artifact is `examples/product-analytics/module-3-python-excel-analysis/outputs/p3-analysis/analysis-practice.xlsx`.

| Location | What to inspect or change |
| --- | --- |
| Analysis B5 and E5 | UTC report boundaries; end is exclusive |
| Analysis B8:B16 | Jobs, completed jobs, known/complete amounts and completed share |
| Analysis E7:I10 | SUMIFS plan summary with missing-billing counts |
| Analysis G13:G16 | Unassigned cost, unassigned attempts, date issues and unmapped jobs |
| Analysis A19:L28 | Traceable calculations at job grain |
| Sources A5:F14 | Nine prepared jobs, source timestamp text and normalized date |
| Sources H5:L14 | Nine attempts, known costs and audit flags |
| Sources N5:O8 | Workspace-to-plan dimension |

The Sources sheet is a deduplicated prepared snapshot. Original timestamp cells carry a visible `raw: ` prefix to preserve their literal offsets during workbook authoring; the normalized UTC column contains actual dates. Original CSVs retain the unprefixed source strings. Job IDs remain text, with a zero-padded display for readability.

Change the known billed input at Sources F7 from 200 to 250 and observe the subtotal update. Restore it, then clear the known zero at F8: missing billing increases from two to three. This is why a blank cannot be treated as an ordinary zero.

Clear attempt cost J7: known provider cost becomes 100, one selected job has incomplete cost, and the complete provider total becomes `n.a.`. Restore the input. Move the exclusive endpoint to 20 October at midnight: three jobs remain, billing is complete at 290, and provider cost is 70. These changes were checked in both the authoring engine and native Excel.

The native verifier opens a disposable copy, checks recalculation and restores its mutations, scans formula errors and closes its own Excel instance. It does not modify the final workbook or interact with an account. Native checks establish the tested formulas' behavior, rather than validating the synthetic data as real invoices.

## 3.22 Reconciliation and debugging order

| Symptom | First investigation | Evidence to retain |
| --- | --- | --- |
| Billing grows after enrichment | Join multiplicity and right-key duplicates | Unique IDs and before/after totals |
| A month differs across tools | Date field, timezone and endpoint policy | Boundary records and normalized instants |
| One segment disappears | Inner join, missing groups or categorical settings | Unmatched-key and missing-key counts |
| Excel sum is too small | Numbers stored as text, range or filters | Types, covered rows and formula references |
| A lookup seems plausible but wrong | Repeated keys or approximate matching | Match count and explicit exact-match mode |
| One report claims zero cost | Missing values replaced by zero | Known subtotal and completeness indicator |
| A percentage differs | Population and weighting | Numerator and denominator per group |

First align definitions. Then compare input snapshots and row counts. Check types and identities, isolate boundary rows, and inspect row-level differences. Change one rule at a time. Finish by documenting the cause and adding a regression check that would catch it again.

For large datasets, select necessary columns, choose useful dtypes, filter early where valid, and measure memory. Chunked aggregation works for additive measures but needs care for distinct counts, deduplication and cross-chunk joins. Move work to a database when its indexed storage and query engine better fit the volume; loading everything into pandas is not mandatory.

## 3.23 Resume explanation and common wrong answers

A defensible explanation connects the task, input, method, checks and decision: “I reconciled job billing against attempt costs, preserved missing values, aggregated retries before joining, and withheld a complete billing total until unresolved amounts were explained.” This sentence describes this teaching case. Use it as project evidence only if you actually performed the corresponding work in your project.

For your own resume, bring one original sample schema, the row grain, one transformation, one validation rule, one surprising mismatch and the decision it changed. If the source is confidential, explain its structure without inventing new outcomes. Earlier [M28 resume deep-dives](/docs/resume-skills/resume-project-experience-deep-dives) distinguishes resume-reported claims from independently reproduced behavior.

| Weak answer | Better explanation |
| --- | --- |
| “pandas cleans data automatically” | Its operations follow explicit schemas and policies that I must choose |
| “A left join cannot change totals” | Matching multiplicity can repeat left-side measures |
| “Missing means zero” | I need domain evidence for that replacement |
| “XLOOKUP sums all matches” | It retrieves a corresponding match; SUMIFS aggregates |
| “The PivotTable proves the source is correct” | It summarizes the supplied source and can repeat its defects |
| “Both reports agree, so the metric is valid” | They may share a wrong grain, population or definition |
| “80% means the product improved retention” | It is completed jobs divided by selected final jobs in this case |

## 3.24 Interview questions and answers

### Q1. What is NumPy, and why use it?

NumPy provides typed multidimensional arrays and numerical operations. It helps express repeated calculations compactly and can avoid per-element Python interpreter work. I still inspect memory, shapes and numerical ranges.

### Q2. What are shape and dtype?

Shape records dimension lengths; dtype records element representation. Matching business meanings is also necessary: two arrays can share a shape while their rows refer to different customers.

### Q3. Explain broadcasting with this case.

The usage matrix has three columns and the rates vector has three elements. Trailing dimensions match, so NumPy applies the rates across both rows without requiring a manually repeated matrix.

### Q4. What does axis mean in a sum?

It identifies the dimension being reduced. For this two-dimensional usage matrix, reducing axis 1 leaves one total per row; reducing axis 0 leaves one total per column.

### Q5. How do elementwise multiplication and matrix multiplication differ?

Elementwise multiplication pairs compatible elements with broadcasting. Matrix multiplication combines dimensions according to its contraction rules. The example's matrix-vector product equals its weighted row sums, but the operations are not generally interchangeable.

### Q6. When does a selection change the original array?

A basic NumPy slice is usually a view, so writes can affect the original. Advanced indexing returns a copy. I make independence explicit before mutating a working selection.

### Q7. How is a DataFrame different from a NumPy array?

A DataFrame has labelled axes and potentially different column dtypes. A NumPy array is primarily positional and has a single dtype. Converting between them can change the alignment and type assumptions.

### Q8. What is the difference between loc and iloc?

loc uses labels or aligned masks; iloc uses positions. An integer index label is still a label under loc, and duplicate labels can return more than one record.

### Q9. Why can adding Series differ from adding arrays?

Series addition aligns index labels. Arrays add by position. Converting to arrays removes label protection and requires a separately verified ordering contract.

### Q10. How would you update selected rows safely?

Use one explicit loc assignment on the intended DataFrame. With pandas 3 Copy-on-Write, assigning through a chained derived selection does not update the original object.

### Q11. Why read an ID as text?

The ID is a label rather than a quantity. Numeric inference can remove leading zeros or alter large identifiers. An explicit import type preserves its representation before later joins.

### Q12. Is filling every missing value with zero acceptable?

Only where the domain establishes zero as the correct meaning. An unknown billed amount is different from observed zero billing. I preserve missingness and expose incomplete totals.

### Q13. What does min_count=1 solve?

It prevents a sum with no known observations from looking like a known zero. It does not make a partially observed sum complete; I also track missing counts.

### Q14. How would you deduplicate events or exports?

Identify the true identity, compare repeated records and remove only repeats allowed by the contract. Conflicting versions require an authoritative version rule or quarantine. Retries with different attempt IDs remain separate.

### Q15. Why did a left join increase billing?

A job with two matching attempts appeared twice. Summing its repeated job-level billed amount inflated the total. I aggregate costs to job grain before joining and keep billing at job grain.

### Q16. What do validate and indicator provide in a pandas merge?

validate checks the expected key cardinality. indicator identifies source participation in matched and unmatched rows. Neither determines the correct business grain for an additive measure.

### Q17. How does pandas handle null merge keys?

pandas can match null keys to one another, unlike ordinary SQL null equality. The case rejects missing relationship keys, rather than allowing unrelated missing IDs to form a match.

### Q18. Explain agg versus transform.

agg returns a reduced summary per group. transform returns values aligned to original rows, useful when each record needs its group's statistic. The required result grain determines the choice.

### Q19. Why can count and size disagree?

size counts rows, while count excludes missing values in the selected column. Counting billed amounts can undercount jobs with unknown billing.

### Q20. When do you use pivot_table instead of pivot?

pivot requires unique row/column combinations for the reshaped values. pivot_table supports aggregation over repeated combinations. I specify the aggregation and preserve missingness appropriate to the measure.

### Q21. How do you calculate an overall rate from segment rates?

Combine segment numerators and denominators, or weight rates by their valid denominators. An unweighted mean changes the question unless equal segment weighting is intended.

### Q22. Why normalize timestamps?

Different textual dates can represent the same instant, and one local date can fall in a different UTC month. I normalize aware instants and apply explicitly chosen business boundaries.

### Q23. Why use an exclusive end date?

Adjacent intervals then meet without overlap. It also avoids relying on a guessed “last instant” of a date. The same policy must be applied in every tool.

### Q24. What is wrong with coercing invalid dates and continuing?

Coercion is useful only if conversion failures remain visible. Silently discarding NaT records can bias the report. I retain IDs and counts for correction and avoid guessing missing timezones.

### Q25. What is the difference between a lookup and SUMIFS?

A lookup retrieves a value associated with a match. SUMIFS adds all qualifying measures. For retry costs I need an aggregation; for a workspace plan I need a unique attribute match.

### Q26. How would you make a lookup reliable?

Check key cardinality, choose exact matching, distinguish no match from a matched blank, and expose duplicate keys. Returning the first plausible plan can conceal conflicting dimension data.

### Q27. What can make an Excel report stale?

An outdated source snapshot, fixed ranges, manual calculation settings, unrefreshed connections or PivotTables, and copied formulas pointing at old rows. I check source lineage and refresh behavior separately.

### Q28. How would you compare a PivotTable with pandas?

Use the same source grain, interval, missing-value rules and aggregation. Compare counts and group subtotals, including unmatched categories, before a grand total. Matching tools can still share a bad definition.

### Q29. What should the stakeholder hear about the case's billing?

The known subtotal is 290 cents, but two selected jobs lack billing, so a complete total is withheld. Five jobs and 110 known provider cents are in scope; an unmatched seven-cent attempt remains separate.

### Q30. How do you make an analysis reproducible?

Preserve inputs and schema, pin runtime dependencies, run a deterministic pipeline, record definitions and outputs, and test boundaries and changed inputs. Include a reconciliation trail, rather than only a final chart.

## 3.25 A 30-minute mock

| Time | Interview prompt | Strong evidence |
| --- | --- | --- |
| 0–4 min | Choose NumPy, pandas or Excel for a recurring job-cost report | Data model, audience, scale and repeatability |
| 4–10 min | Explain why the joined billing is 490 | Grain trace and legitimate attempt multiplicity |
| 10–16 min | Resolve missing amounts and the UTC month boundary | Explicit unknowns, offset conversion and half-open interval |
| 16–22 min | Build an Excel plan summary | Correct sum ranges, exact lookup guards and completeness flag |
| 22–27 min | Describe the PivotTable exercise and validation | Job-level source, Count vs Sum, filters and refresh |
| 27–30 min | Present a recommendation and resume boundary | Known subtotal, unresolved evidence and next action |

Score each answer for definition, concrete mechanics, an edge case and a decision. Naming a function without explaining the population should not receive full credit.

## 3.26 Practice tasks and answer checkpoints

1. Annotate each CSV with its row grain, identity and permitted missing fields.
2. Run the NumPy case and explain every dimension and axis without reading the output labels.
3. Reproduce the slice mutation and the advanced-indexing copy, then explain the difference from pandas Copy-on-Write.
4. Add the two labelled Series by label and by position; explain which mapping each result assumes.
5. Create a conflicting duplicate job and identify the rule that should reject it.
6. Perform the deliberately wrong direct join, then restore the correct job-grain enrichment.
7. Change an observed zero bill to blank and distinguish the subtotal from a complete total.
8. Trace jobs 0001, 0006, 0007 and 0008 through date parsing and interval selection.
9. Remove one selected attempt cost and investigate known cost, missing-cost count and the withheld total.
10. Change a workbook input and report boundary, then restore them and compare the baseline.
11. Create the manual PivotTable, explicitly set its aggregations and compare it with the pandas crosstab.
12. Give a two-minute reconciliation explanation, then list which parts you could support from an actual resume project.

### Answer checkpoints

| Task | Checkpoint |
| --- | --- |
| 1 | Jobs and attempts have different identities; blank monetary values represent unknowns |
| 2 | Rates broadcast along columns; row totals survive axis-1 reduction |
| 3 | Basic NumPy slice shares memory; advanced indexing copies; pandas 3 follows its own CoW rules |
| 4 | Label sums are a:11 and b:22; positional sums are 21 and 12 |
| 5 | A repeated identity with conflicting fields fails, rather than keeping an arbitrary version |
| 6 | Wrong result has six joined rows and 490 known billed cents; correct selected set has five jobs and 290 |
| 7 | Clearing job 0003's zero increases missing billing to three; known billed subtotal stays 290 |
| 8 | 0001 belongs to September UTC; 0006 is at the excluded upper bound; 0007/0008 are date issues |
| 9 | Clearing a02 cost leaves known provider subtotal 100 and one incomplete selected job |
| 10 | Original baseline has five jobs; a 20 October exclusive end leaves three and 70 provider cents |
| 11 | Counts match section 3.13; a SUMIFS summary alone does not complete the PivotTable exercise |
| 12 | Explain grain, known/unknown amounts, date policy, orphan investigation and your personal contribution |

Tasks 1–10 have runnable components in the companion. Creating the PivotTable and presenting the explanation remain reader practice; authoring checks do not establish that you have completed them.

## 3.27 Primary research and version boundary

Primary documentation was checked on 18 October 2026. The citations beside each concept support API and tool behavior; the CSVs supply the invented amounts. Current documentation can describe a newer release than the executed environment. The preserved results are anchored to NumPy 2.3.5 and pandas 3.0.1, not to an unspecified “latest” installation.

The research manifest records NumPy fundamentals, broadcasting and copies; pandas missing values, merge behavior, dates and Copy-on-Write; and Microsoft guidance on identifiers, SUMIFS, lookups, PivotTable creation and refresh. No external account, vendor dataset or real project invoice was used. The local workbook was authored with Artifact Tool 2.8.99 and checked independently with native Excel on a disposable copy.

## 3.28 Exit checklist

- [ ] I can describe the grain and identity of each source.
- [ ] I can explain array shapes, axes and dtype choices.
- [ ] I can apply broadcasting and distinguish elementwise from matrix multiplication.
- [ ] I can explain views, copies and pandas 3 Copy-on-Write.
- [ ] I can predict label-aligned and positional results.
- [ ] I can import identifiers without losing their representation.
- [ ] I can preserve missing amounts and distinguish them from observed zero.
- [ ] I can reject conflicting duplicates without deleting legitimate retries.
- [ ] I can validate join cardinality and diagnose inflated sums.
- [ ] I can normalize dates and apply a chosen half-open reporting interval.
- [ ] I can explain groupby, counts, pivots and weighted rates.
- [ ] I can use Excel references, SUMIFS and guarded exact lookups.
- [ ] I can create and refresh the manual PivotTable and reconcile it with pandas.
- [ ] I can present a reproducible analysis without turning a teaching result into a resume claim.

Return to the [master roadmap](/docs/product-analytics) or revisit [P2: Product Analytics and Experiments](/docs/product-analytics/product-analytics-experiments).

Continue with [P4: Marketing Measurement and Data Visualization](/docs/product-analytics/marketing-measurement-data-visualization)—campaign vocabulary, attribution, denominators, chart selection, D3 and treemaps.
