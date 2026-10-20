# Analytics engineering and warehouse lab

Three source batches drive a small owned in-memory warehouse. Thirty-two recorded traces accompany the ten-file Analytics Engineering Notes subject. The source includes repeats, conflicts, source-version corrections, deletes, stale upserts, late facts/dimensions, moved partitions and missing bills.

## Run from the repository root

```powershell
python examples/analytics-engineering/verify.py
python examples/analytics-engineering/lab.py L12
python examples/analytics-engineering/lab.py L22
python examples/analytics-engineering/build_book.py
python examples/analytics-engineering/validate_content.py
```

Python 3.13.15 / SQLite 3.50.4, standard library only. The selected-trace command executes and verifies the whole isolated lesson, closes all databases and prints one observation. It does not execute only that trace's query. No persistent database, account or external service is needed.

The 74 runtime checks include nine independent full-state reference comparisons across the three stages, 24 candidate quality assertions and selected recovery, replay, ordering, conflict, input, constraint, query-plan and preservation cases. verification-results.json records the exact breakdown. All four owned in-memory connections close. reference.py uses independent Python maps and effective dates, executes no SQL and reads no saved expected outputs.

warehouse.py lands raw batches separately, freezes a local receipt prefix, canonicalizes versions and builds complete candidate dimensions/facts/aggregates. It identifies changed enriched facts and old/new tenant/day partitions, selects a mart result, and compares it with full aggregation. Publication writes current models, immutable mart rows, active pointer and cursor atomically. This deliberately recomputes full candidates; it tests partition-selection correctness rather than production incremental efficiency. The three SELECT files in models/ are actually executed SQL. Published mart versions remain immutable, while fact/dimension tables hold current state only.

The conflict policy holds the entire entity out if any known bounded version has conflicting payloads. It has no authoritative resolution API and is not bitemporal history. A late conflict is tested as a retraction. Source versions are authored per-entity integers, not a real CDC LSN. The local ingestion sequence is not a distributed source watermark. Dates are day-grain UTC labels; money is integer USD cents; refunds, multiple currencies and accounting revenue recognition are outside the metric.

The injected failure is a Python exception inside a SQLite transaction. Power-loss, process-kill, concurrent readers, multi-host recovery, true connector snapshot/log handoff and cloud performance are not tested. Semantic negative billing is intentionally permitted in raw and blocked at publication; an unsupported schema rejects its whole ingestion batch. A later valid higher version repairs the semantic candidate. A separate wrong-lookback warehouse produces a real incorrect subtotal. A local index probe inspects actual access paths without claiming timing or cloud pruning results.

dbt, Airflow, Debezium, Iceberg and cloud warehouses are documentation references and are not installed/run by this lab. dbt SQL/YAML in the handbook is explicitly illustrative and not parsed or compiled. The dependency-order exercise uses Python graphlib over an authored graph, not tool-derived dbt lineage. Tool/adapter versions and target syntax must be pinned and verified in a real project.

build_book.py inserts exact recorded traces, executed model SQL and all 25 supplied envelopes into marked handbook blocks. Theory, Q&A and practice remain authored in root Markdown. validate_content.py checks fidelity, coverage, links and the byte-preservation snapshot of all 153 earlier handbooks. Content audits are recorded separately from runtime checks.

After syncing and building study-guide, run `node examples/analytics-engineering/site-smoke.mjs` to check routes, rendered content and subject-filtered search. Its owned temporary loopback preview closes afterward; port 3000 remains stopped unless separately requested. The recorded local build uses the existing local font-response fixture for this machine's network restrictions, with normal site font configuration unchanged.

Primary sources and scope are in research.json and inline chapter links. The lesson is synthetic educational preparation, not measured company question frequency, a production data audit or a certification of business completeness. Learner practice and mock feedback remain manual work.
