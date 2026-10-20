# SQL Interview Problem Book — Part 1: Master Roadmap

**Thirty business questions, runnable SQL, verified answers and interview follow-ups.**

## 0. What this book adds

The existing DBMS chapters explain SQL syntax and mechanisms. This companion starts with a question, asks you to define its grain and population, then makes you write and defend a query against awkward data.

**Authoring status: complete.** Seven files cover the dataset/method, thirty problems and final revision. The example data is invented. The selection is editorial preparation, not a measured ranking of questions asked by companies.

**Verification, 20 October 2026:** 86 local checks passed on Python 3.13.15 and SQLite 3.50.4. Thirty query outputs match independent Python reference answers; the other checks cover insertion order, changed inputs, wrong-query counterexamples, constraints, plans and source preservation. All 16 database connections closed. No PostgreSQL execution or production performance result is claimed.

## 1. Reading and practice map

| Chapter | Coverage | Practice |
| --- | --- | --- |
| [Dataset and solving method](/docs/sql-interview/dataset-and-solving-method) | Source contracts, schema, bound parameters, grain, timestamps and execution | Load the fixture and predict an output shape |
| [Joins, grain and NULL](/docs/sql-interview/joins-grain-and-null-semantics) | Preserved rows, missing totals, fan-out, category membership and exclusion lists | Q01–Q08 |
| [Windows and time series](/docs/sql-interview/windows-and-time-series) | Ties, deterministic latest rows, dense dates, rolling windows, islands, sessions and historical dimensions | Q09–Q16 |
| [Funnels, cohorts and retention](/docs/sql-interview/funnels-cohorts-and-retention) | Ordered stages, maturity, exact returns, late knowledge, active users, repeat purchase and abandonment | Q17–Q24 |
| [Reconciliation and query plans](/docs/sql-interview/reconciliation-and-query-plans) | Duplicate/conflicting events, ownership diagnostics, payments/refunds, exceptions and composite indexes | Q25–Q30 |
| [Consolidation and mocks](/docs/sql-interview/consolidation-and-mocks) | Counterexamples, oral checks, failure diagnosis and two timed mocks | Explain, modify and re-solve |

Amazon's BIE preparation guide explicitly includes SQL and analytical problem solving. This is one primary role-specific reason for combining query mechanics with a business definition; it does not establish a universal interview format. [Amazon BIE preparation](https://www.amazon.jobs/content/en/how-we-hire/bie-interview-prep).

## 2. Prerequisites and bridges

- [DBMS SQL querying](/docs/dbms/sql-querying): logical phases, predicates, aggregates and NULL.
- [DBMS joins and windows](/docs/dbms/sql-joins-subqueries-windows): operators, ranking and frames.
- [PostgreSQL backend practice](/docs/resume-skills/postgresql-backend): real-engine transaction/index work from the earlier track.
- [Product analytics and experiments](/docs/product-analytics/product-analytics-experiments): metric definitions and causal limits.
- [Python and Excel analysis](/docs/product-analytics/python-excel-analysis): reconciliation and grain in another tool.
- [Analytics event pipeline design](/docs/system-design/analytics-event-pipeline): ingestion, revisions and reliable publication.

If a concept blocks a problem, use that bridge for a short review and return to the query. The thirty tasks are intended to turn definitions into observable behavior.

## 3. How to attempt each problem

1. State the output row grain and list the required columns.
2. Clarify the eligible population, amount unit, time interval and missingness policy.
3. Identify source grains and which relationships can multiply rows.
4. Predict at least one normal row and one boundary row.
5. Write the query, then inspect the hint or solution only when useful.
6. Compare the actual output and explain a counterexample to a tempting wrong query.
7. Change a tie, missing value, date or eligibility assumption and adapt the solution.

The SQL solution is one correct implementation under the fixture's contract. An alternative query is acceptable when it preserves the same defined result, including identities, missingness, ties and ordering.

## 4. Verification scope

| Check group | Count | Meaning |
| --- | --- | --- |
| Baseline query outputs | 30 | Actual SQL compared with independent Python answers |
| Reversed insertion order | 30 | Same ordered answer when input insertion order changes |
| Changed-input scenarios | 12 | Boundary, scope, missingness and repair cases |
| Incorrect-query counterexamples | 6 | Real outputs exposing plausible wrong answers |
| Constraint checks | 4 | Foreign-key setting and rejected invalid writes |
| Query-plan checks | 3 | Actual access paths and preserved results |
| Source preservation | 1 | Inputs and solution/reference sources unchanged by the run |

The independent reference also embodies the same written business definitions. Agreement does not prove those definitions match an external company or production dataset. The book preserves assumptions so they can be challenged.

## 5. Suggested routes

**First SQL interview:** solving method → Q01–Q10 → Q17–Q19 → Q25/Q27 → Mock A.

**Product/data analyst:** solving method → joins → windows → cohorts → reconciliation → both mocks.

**Backend engineer:** joins/grain → deterministic selection → historical dimensions → reconciliation → query plans, with transaction/security depth in the earlier tracks.

Use the consolidation page to choose targeted revision. Suggested continuation after this book: probability and statistics foundations, then a broader product/analytics casebook.

## 6. Authoring completion and learner practice

- [x] Dataset, shared parameters and solving method authored.
- [x] Q01–Q30 SQL and worked outputs executed.
- [x] Counterexamples, boundary mutations and plan evidence preserved.
- [x] Final revision and two 45-minute mocks authored.
- [ ] I have solved the questions without reading their answers first.
- [ ] I can explain each query's grain, boundary and failure case.
- [ ] I have attempted both mocks and reviewed my mistakes.

Begin with [Dataset and Solving Method](/docs/sql-interview/dataset-and-solving-method).
