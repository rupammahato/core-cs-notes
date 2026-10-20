# Analytics Engineering and Warehousing — Part 1: Master Roadmap

**Turn changing source records into explainable, tested and reproducible analytical datasets.**

## 0. What this handbook adds

The [SQL lab](/docs/sql-interview) explains query correctness. The [event-pipeline design](/docs/system-design/analytics-event-pipeline) explains ingestion and event-time projection. This companion focuses on warehouse modeling, historical dimensions, CDC state, transformation workflows, refresh correctness, quality gates and trustworthy consumption.

**Authoring status: complete.** Ten chapters contain eight teaching modules, 32 executed warehouse traces, 64 interview Q&As, 32 practice tasks, 30 final oral checks and two 45-minute mocks. Questions and priorities are editorial placement practice, not measured company interview frequencies.

## 1. Reading map

| Module | Chapter | Main outcome |
| --- | --- | --- |
| A1 | [Warehouse foundations and dataset](/docs/analytics-engineering/warehouse-foundations-and-dataset) | Define layers, grain, source contracts and publication boundaries |
| A2 | [Dimensional modeling and history](/docs/analytics-engineering/dimensional-modeling-and-history) | Model facts, SCD2-style history, unknown members and temporal joins |
| A3 | [Ingestion, CDC and canonical state](/docs/analytics-engineering/ingestion-cdc-and-canonical-state) | Handle retries, corrections, deletes, ordering and ambiguity |
| A4 | [Transformations and dbt workflows](/docs/analytics-engineering/transformations-and-dbt-workflows) | Organize source/staging/mart models, dependencies, tests and contracts |
| A5 | [Incremental refreshes and backfills](/docs/analytics-engineering/incremental-refreshes-and-backfills) | Recompute old/new affected partitions and reconcile with full results |
| A6 | [Quality, observability and publication](/docs/analytics-engineering/quality-observability-and-publication) | Block bad candidates and preserve last-good results through failure |
| A7 | [Semantic metrics and consumption](/docs/analytics-engineering/semantic-metrics-and-consumption) | Publish stable definitions, correct denominators and reproducible versions |
| A8 | [Production architecture and performance](/docs/analytics-engineering/production-architecture-and-performance) | Explain storage, orchestration, security, performance and operations |
| Revision | [Consolidation and mocks](/docs/analytics-engineering/consolidation-and-mocks) | Diagnose failures and defend an end-to-end design |

## 2. The local warehouse lesson

Three batches change a small invented commerce warehouse. They include duplicate deliveries, conflicting payloads, a late dimension, an older-business-day fact, amount and plan corrections, a delete, stale upserts, a moved order and a missing bill resolved as zero.

```text
accepted raw prefix -> canonical source versions
  -> effective-dated customer dimension -> current order fact
  -> daily tenant/plan billing candidate -> quality checks
  -> versioned published mart + active pointer + committed cursor
```

The run deliberately fails after replacing candidate facts but before commit. The tested rollback keeps the previous publication active while raw input remains available for retry.

## 3. Verification and its boundaries

**Verification, 21 October 2026:** 74 checks passed on Python 3.13.15 and SQLite 3.50.4. They include independent Python reference comparisons at all three data stages, 24 candidate quality assertions, replay/order/conflict cases, injected rollback, source-contract rejection, constraints and actual local query plans. All four owned in-memory connections closed. The earlier 153 handbook files remain byte-identical to the captured snapshot.

The runtime executes SQLite and Python. **dbt, Airflow, Debezium, Iceberg and cloud warehouses are discussed through primary documentation and are not executed.** dbt snippets are illustrative and require a real project, pinned tool/adapter versions and target-engine verification.

The lesson rebuilds full candidate dimensions, facts and aggregates. It then selects affected mart partitions, preserves unaffected rows and checks the result against full recomputation. It demonstrates refresh correctness, not production incremental compute savings. Published mart versions remain immutable; fact/dimension tables hold current state rather than immutable historical generations.

The conflict policy evaluates a bounded known raw snapshot and withholds the entire ambiguous entity. It is not a general correction-resolution or bitemporal system. A source-version integer is an authored per-entity ordering contract, not a real database LSN. The publication cursor is a local append sequence, not a distributed watermark.

No persistent database, external service, real customer extract, process-kill, power-loss, concurrent-reader experiment or performance benchmark is claimed.

## 4. Run and inspect

From the repository root:

```powershell
python examples/analytics-engineering/verify.py
python examples/analytics-engineering/lab.py L12
python examples/analytics-engineering/lab.py L22
```

Each selected trace runs the complete isolated lesson and prints one observation after closing its databases. The source schema, three executed SQL model files, complete fixture, independent oracle and recorded outputs are in examples/analytics-engineering/. The fixture uses day-grain UTC business dates and integer USD cents.

## 5. Suggested learning routes

**First analytics engineering interview:** A1 → A2 → A3 → A4 → A5 → A6 → revision.

**Backend/data-platform engineer:** A1/A3 → A5/A6 → A8, then inspect the dimensional and semantic contracts that consumers depend on.

**Product/data analyst:** A1/A2 → A7 → A5/A6, using the [statistics](/docs/probability-statistics) and [casebook](/docs/product-casebook) bridges for interpretation and decisions.

The architecture chapter connects warehouse mechanics to an operational design. It does not imply that this miniature full-rebuild lesson is the right deployment implementation for a large source.

## 6. Authoring and learner status

- [x] Eight modules, executed SQL models and 32 traces authored.
- [x] Independent references and selected failure/recovery boundaries executed.
- [x] Consolidation, oral checks and two mocks authored.
- [ ] I can define every layer's grain and admission policy.
- [ ] I can explain a correction, delete, late dimension and failed publication.
- [ ] I have attempted both mocks and revised an answer after a changed assumption.

Begin with [Warehouse Foundations and Dataset](/docs/analytics-engineering/warehouse-foundations-and-dataset).
