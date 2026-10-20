# Analytics Engineering and Warehousing — Part 2: Warehouse Foundations and Dataset

**A1: identify what one row means before choosing a layer or tool.**

## 1. What analytics engineering does

Analytics engineering turns source data into reusable, tested datasets with documented meaning. It connects data-platform ingestion to business analysis: model the entities and events, make transformations reproducible, test quality, define metrics and support consumers when sources change.

A data engineer may own capture, storage and execution infrastructure; an analyst may own interpretation and business questions. Team boundaries vary. The important ownership questions concern source contracts, transformation behavior, publication decisions and consumer support, rather than job-title definitions.

## 2. OLTP, OLAP and storage choices

| System concern | Typical emphasis | Consequence |
| --- | --- | --- |
| OLTP | Small transactional reads/writes and integrity | Normalize operational state and protect business transactions |
| OLAP | Scans, joins and aggregates over history | Organize analytical access patterns and reproducible definitions |
| Data lake | Files/objects retained for many uses | File layout, schema, catalog and quality remain design responsibilities |
| Warehouse | Managed analytical tables and query execution | Engine capabilities, loading and access policy still matter |
| Lakehouse | Table-management/query capabilities over lake-style storage | Specify the actual table format, catalog and engine guarantees |

These categories can overlap in products. Separate storage format from table format and query engine. Parquet describes a columnar file format; a managed table format adds metadata and operations over files. A lake does not become trustworthy merely by retaining raw objects.

## 3. ETL, ELT and logical layers

ETL transforms before loading into the intended target; ELT loads and then transforms there. Real systems can mix the two, including pre-load redaction or validation. Neither acronym guarantees correctness, lower cost or a particular tool.

| Layer in this lesson | Grain and responsibility |
| --- | --- |
| raw_changes | One accepted delivery envelope with a local append sequence |
| valid_changes | One unambiguous source version per stream/tenant/entity/version |
| dim_customer | One currently known effective period per customer, plus scoped Unknown members |
| fact_orders | One latest admitted nondeleted order per tenant/order |
| mart_daily | One published run/tenant/day/plan paid-billing aggregate |
| runs / pipeline_state | Source bounds, definition version and active publication |

Names such as bronze/silver/gold or raw/staging/mart are organizational conventions. Write the actual contract instead of assuming a layer name defines its grain or quality.

## 4. The source and time contract

The fixture contains 25 deliveries in three batches of 14, six and five. The order and customer streams use separate tenant-scoped entity identities. Each entity's source_version must increase when source truth changes. Delivery identity is separately immutable.

Order payloads contain a day, customer, amount, status and U/D operation. Customer payloads provide effective day and plan. All amounts are integer USD cents; all business dates are day-grain UTC labels. Within-day plan changes, currencies, taxes, refunds and settlement are outside this lesson.

Source business dates, local arrival sequence, source version and publication version have different jobs. A later arrival can describe an older business date or stale source version. A successful run considers a frozen raw prefix, rather than claiming to capture every real source change.

The known conflicting entity is excluded. The published billing sum describes admitted paid orders and is not recognized accounting revenue. A complete amount within that set is distinct from source coverage.

## 5. A reproducible publication boundary

Raw ingestion commits separately. Publication builds candidates against the admitted prefix, checks them, writes a versioned mart and atomically advances current model state, active pointer and cursor in one local transaction.

A consumer can pin a published mart run. Current dimensions and facts are not retained as immutable versions in this implementation. Joining an old published fact interpretation to today's dimension without a proper history contract would not reconstruct an earlier reader's knowledge.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L01. Trace the layers at the first publication

Explain why fourteen landed deliveries produce different counts of valid versions, current facts and mart rows.

**Worked explanation:** The initial raw prefix includes repeated delivery of one version, two conflicting payloads for a quarantined entity, historical customer changes and a cancelled order. Each layer has a different grain. A daily plan aggregate groups several facts, while canonical source versions still include customer history.

Run `python examples/analytics-engineering/lab.py L01`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "raw_deliveries": 14,
  "distinct_unblocked_source_versions": 11,
  "fact_orders": 7,
  "mart_rows": 6
}
```

**Common trap:** Equal counts across layers are not a universal quality requirement. Explain every intended inclusion and reduction.

**Interview follow-up:** What count reconciliation would be appropriate at each specific layer?

### L02. Define current orders versus paid orders

Compare current fact counts and paid-order counts by tenant after batch one.

**Worked explanation:** The fact stores current nondeleted orders, including cancelled orders. The paid-billing mart deliberately filters status. A fact-table row and a metric-eligible transaction therefore need different count contracts. Tenant identity is part of both contracts.

Run `python examples/analytics-engineering/lab.py L02`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "all_current_orders": 6,
    "paid_orders": 5
  },
  {
    "tenant_id": "t2",
    "all_current_orders": 1,
    "paid_orders": 1
  }
]
```

**Common trap:** Treating every warehouse fact as eligible revenue silently includes cancelled work.

**Interview follow-up:** How would you model a cancellation rate without discarding cancelled facts?

### L03. Read the publication manifest

Inspect the first run's source bounds, mode and metric version.

**Worked explanation:** The committed prefix ends at local ingestion sequence fourteen, and the metric definition is named paid-billing-v1. The mode names the publication path, not a claim that the lesson avoids full candidate recomputation. A manifest connects a result to its admitted source prefix and definition.

Run `python examples/analytics-engineering/lab.py L03`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "run_id": "run1",
    "lower_seq": 0,
    "upper_seq": 14,
    "mode": "partition_refresh",
    "metric_version": "paid-billing-v1"
  }
]
```

**Common trap:** A recent run ID or successful job status alone does not describe the business data covered.

**Interview follow-up:** Which code, source-extract and metric-definition identifiers would you persist in production?

### L04. Separate known subtotal from complete billing

Interpret paid orders, known cents and missing bills in the initial tenant totals.

**Worked explanation:** The accepted t1 paid set has one missing bill. The known subtotal remains useful with its missing count, but the complete sum is withheld. The t2 accepted set has no missing bill. Completeness here refers to amounts within the admitted set, not proof that every real source entity was captured.

Run `python examples/analytics-engineering/lab.py L04`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "paid_orders": 5,
    "known_cents": 4300,
    "missing_bills": 1,
    "complete_cents": null
  },
  {
    "tenant_id": "t2",
    "paid_orders": 1,
    "known_cents": 9000,
    "missing_bills": 0,
    "complete_cents": 9000
  }
]
```

**Common trap:** A missing bill is not an observed zero, and quarantined source entities remain a separate coverage issue.

**Interview follow-up:** What would a dashboard need to show before a consumer can assess this total?

<!-- END WAREHOUSE LAB -->

<!-- BEGIN COMPLETE RAW FIXTURE -->

## Complete supplied raw-change fixture
Every row below is one delivered envelope. Payload keys are preserved; no abbreviated source sample is used.
| Batch | Delivery | Stream | Tenant | Entity | Version | Payload |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | c1-free | customers | t1 | c1 | 1 | `{"effective_from":"2026-10-01","plan":"free","schema_version":1}` |
| 1 | c1-pro | customers | t1 | c1 | 2 | `{"effective_from":"2026-10-03","plan":"pro","schema_version":1}` |
| 1 | c2-free | customers | t1 | c2 | 1 | `{"effective_from":"2026-10-01","plan":"free","schema_version":1}` |
| 1 | t2-c1 | customers | t2 | c1 | 1 | `{"effective_from":"2026-10-01","plan":"enterprise","schema_version":1}` |
| 1 | o1-v1 | orders | t1 | o1 | 1 | `{"billed_cents":1000,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 1 | o2-v1 | orders | t1 | o2 | 1 | `{"billed_cents":2000,"customer_id":"c1","op":"U","order_day":"2026-10-04","schema_version":1,"status":"paid"}` |
| 1 | o3-v1 | orders | t1 | o3 | 1 | `{"billed_cents":500,"customer_id":"cLate","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 1 | o4-v1 | orders | t1 | o4 | 1 | `{"billed_cents":null,"customer_id":"c2","op":"U","order_day":"2026-10-03","schema_version":1,"status":"paid"}` |
| 1 | o5-v1 | orders | t1 | o5 | 1 | `{"billed_cents":700,"customer_id":"c2","op":"U","order_day":"2026-10-04","schema_version":1,"status":"cancelled"}` |
| 1 | o8-v1 | orders | t1 | o8 | 1 | `{"billed_cents":800,"customer_id":"c1","op":"U","order_day":"2026-10-03","schema_version":1,"status":"paid"}` |
| 1 | t2-o1 | orders | t2 | o1 | 1 | `{"billed_cents":9000,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 1 | o1-repeat | orders | t1 | o1 | 1 | `{"billed_cents":1000,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 1 | bad-a | orders | t1 | bad | 1 | `{"billed_cents":100,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 1 | bad-b | orders | t1 | bad | 1 | `{"billed_cents":200,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 2 | o1-v2 | orders | t1 | o1 | 2 | `{"billed_cents":1200,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 2 | o2-delete | orders | t1 | o2 | 2 | `{"billed_cents":2000,"customer_id":"c1","op":"D","order_day":"2026-10-04","schema_version":1,"status":"paid"}` |
| 2 | o6-late | orders | t1 | o6 | 1 | `{"billed_cents":300,"customer_id":"c2","op":"U","order_day":"2026-10-01","schema_version":1,"status":"paid"}` |
| 2 | late-dimension | customers | t1 | cLate | 1 | `{"effective_from":"2026-10-01","plan":"partner","schema_version":1}` |
| 2 | o7-v1 | orders | t1 | o7 | 1 | `{"billed_cents":400,"customer_id":"c2","op":"U","order_day":"2026-10-05","schema_version":1,"status":"paid"}` |
| 2 | c1-business | customers | t1 | c1 | 3 | `{"effective_from":"2026-10-03","plan":"business","schema_version":1}` |
| 3 | o1-old-again | orders | t1 | o1 | 1 | `{"billed_cents":1000,"customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 3 | o2-old-again | orders | t1 | o2 | 1 | `{"billed_cents":2000,"customer_id":"c1","op":"U","order_day":"2026-10-04","schema_version":1,"status":"paid"}` |
| 3 | o7-move | orders | t1 | o7 | 2 | `{"billed_cents":450,"customer_id":"c2","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |
| 3 | o4-zero | orders | t1 | o4 | 2 | `{"billed_cents":0,"customer_id":"c2","op":"U","order_day":"2026-10-03","schema_version":1,"status":"paid"}` |
| 3 | o1-extra-field | orders | t1 | o1 | 3 | `{"billed_cents":1200,"campaign":"autumn","customer_id":"c1","op":"U","order_day":"2026-10-02","schema_version":1,"status":"paid"}` |

The separate illustrative order-lines list is used only for L08; it is not a maintained CDC line-item mart.
```json
[
  [
    "t1",
    "o1",
    "l1",
    600
  ],
  [
    "t1",
    "o1",
    "l2",
    400
  ],
  [
    "t1",
    "o2",
    "l3",
    2000
  ],
  [
    "t2",
    "o1",
    "l4",
    9000
  ]
]
```

<!-- END COMPLETE RAW FIXTURE -->

## Interview Q&A

### Q1. Is a warehouse a copy of production tables?
A raw copy can be an input. Analytical datasets additionally need grains, historical policies, trusted transformations and consumer definitions.

### Q2. How do ETL and ELT differ?
They place transformation before or after loading into the intended target. Actual architectures can combine both patterns.

### Q3. What should a staging model do?
Give source fields explicit names, types and structural contracts while preserving traceability. Avoid silently introducing unrelated business aggregates there.

### Q4. Does a gold table imply complete data?
No. Quality and completeness follow explicit checks and source policies, not a layer label.

### Q5. Why store raw evidence?
It supports replay, reconciliation, lineage and changed transformation logic, subject to actual security and retention requirements.

### Q6. Is source version the same as receipt order?
No. The lesson uses source version for entity truth and local sequence for the bounded set of received deliveries.

### Q7. Why version a publication?
Consumers need to reproduce a specific result and understand its source bounds, definition and later revisions.

### Q8. What does this lab actually execute?
Python and SQLite, including SQL models and transactions. Tool-specific warehouse/orchestration discussions are conceptual references.

## Practice tasks

1. State the exact row grain for every table in the layer map.
2. Explain L01's count differences without calling every difference a defect.
3. Name the information required to compare two published totals reproducibly.
4. Distinguish complete accepted billing from complete source capture in L04.

**Answer checkpoints:** layers contain deliveries, versions, current entities, effective periods or aggregate groups; preserve source prefix, metric definition and run identity; an unresolved quarantine remains visible even when admitted amounts are complete.

- [ ] I can explain the layer and source contracts.
- [ ] I can separate business, arrival and publication time.

Continue with [Dimensional Modeling and History](/docs/analytics-engineering/dimensional-modeling-and-history).
