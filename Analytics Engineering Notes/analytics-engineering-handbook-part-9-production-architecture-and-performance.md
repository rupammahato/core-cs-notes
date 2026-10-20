# Analytics Engineering and Warehousing — Part 9: Production Architecture and Performance

**A8: connect correctness contracts to storage, execution, access and operational ownership.**

## 1. A production-shaped reference architecture

```text
Operational sources / business events
  -> connector or extract with consistent handoff and retained replay bounds
  -> protected raw landing + source manifests
  -> staging and canonicalization
  -> dimensions / facts / semantic marts
  -> candidate tests and reconciliation
  -> controlled publication
  -> dashboards / notebooks / APIs with trusted access policy

Cross-cutting: orchestration, lineage, source contracts, access, retention,
              cost controls, incident ownership and consumer communication
```

Choose batch or lower-latency processing from the freshness requirement, source change rate, cost and recovery constraints. Streaming does not eliminate replay, backfills, semantic definitions or versioned publication. A near-real-time dashboard can still be wrong or incomplete.

## 2. Columnar files, tables and engines

Columnar layouts can avoid reading unneeded columns and improve analytical compression. Actual read behavior depends on file/block layout, query engine and filters. Partitioning divides data by a defined key; clustering/order can improve pruning within broader ranges. Neither is automatically effective for every query.

BigQuery guidance recommends controlling projection and filtering partition columns appropriately. Validate the engine's actual bytes, plan, latency and pricing behavior rather than inferring a cost reduction from SQL appearance. [Projection and query computation](https://docs.cloud.google.com/bigquery/docs/best-practices-performance-compute), [partitioned tables](https://docs.cloud.google.com/bigquery/docs/partitioned-tables).

SQLite's composite-index experiment below demonstrates a local B-tree access path. It does not test a columnar cloud warehouse's partitioning, clustering or billing model.

## 3. Lakehouse metadata and maintenance

A table format can manage schemas, snapshots and files beyond what a standalone columnar file provides. Apache Iceberg specifies metadata, evolution and snapshot-related table behavior. Exact write/catalog/concurrency guarantees depend on the selected engines and deployment. [Iceberg table specification](https://iceberg.apache.org/spec/).

Schema evolution does not itself populate a new field correctly for old rows. Partition evolution does not remove the need to validate query plans and reader compatibility. Small files, compaction, metadata growth, snapshot expiration and recovery retention remain operational concerns.

Wide denormalized tables can simplify a bounded consumer pattern, while star models support reusable descriptive dimensions and measure policies. Evaluate update costs, duplication, historical semantics and query patterns instead of treating one modeling style as universally best.

## 4. Orchestration and CI

An orchestrator coordinates dependencies, bounds, retries, concurrency and operational state. Transformations still need idempotent behavior and a trustworthy source cursor. A green schedule cannot repair a wrong join or a missing producer record.

For development, isolate schemas and credentials, pin code/tool/adapter versions, review source and metric contract changes, and execute appropriate unit/data/reconciliation checks. A changed dimension can affect old facts; selection based only on directly edited model files can miss downstream consequences if lineage is incomplete.

A production publication design must match the actual engine's transactional, table-swap or snapshot capabilities. Do not assume the local multi-table SQLite transaction ports unchanged to every platform.

## 5. Security and data lifecycle

Carry trusted tenant/entity scope through ingestion, keys, joins and consumer policy. Restrict raw and sensitive fields according to real roles and purpose. Engine grants, row/column policies, service identity and export controls are separate from a WHERE tenant_id clause in an application query.

The lab tests scoped joins and composite foreign keys under trusted local SQL. It does not authenticate a user or prevent arbitrary SQL access. Unknown members are tenant-scoped to avoid accidental cross-tenant fallback.

Raw retention enables replay but also retains data that may require restricted access or removal. Define retention, erasure/correction propagation, downstream exports, backups and audit requirements for the actual application. The fixture contains no real personal data and implements no general privacy-compliance workflow.

## 6. Performance and capacity reasoning

Measure source rates, backlog growth, model runtime, warehouse concurrency, scanned data, storage growth and consumer latency. Identify whether the bottleneck is source extraction, transformation, publication or consumption.

Push selective filters/projections where semantics permit, reduce fan-out, materialize expensive shared logic when justified and inspect actual plans. Model caching and incremental choices need invalidation and restatement policies; making an incorrect dataset faster does not make it trustworthy.

L32 is logical sizing arithmetic from assumptions. Compression, row groups, partition selectivity, metadata and pricing can make measured results differ. No throughput, cloud bill or production speedup is asserted.

## 7. Incident and change ownership

For a failed refresh, identify source bounds, failed gate, last-good publication, affected consumers and repair owner. Preserve evidence, decide how consumers should see stale/unavailable data, and run a scoped repair with reconciliation.

A rollback of transformation code does not undo every data mutation or definition change. Maintain tested forward-repair/rebuild paths and enough compatible source history to use them. Separate recovery objectives from the existence of backups or a version-control commit.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L29. Keep tenant keys scoped through the model

Inspect the two distinct o1 facts and their historical plans.

**Worked explanation:** Every business key, dimension join and fact reference includes tenant identity. The local query shows correct scope under trusted SQL. It does not implement production authentication, row-level security or prevention of arbitrary SQL access.

Run `python examples/analytics-engineering/lab.py L29`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "order_id": "o1",
    "plan": "free",
    "billed_cents": 1200
  },
  {
    "tenant_id": "t2",
    "order_id": "o1",
    "plan": "enterprise",
    "billed_cents": 9000
  }
]
```

**Common trap:** Adding a tenant predicate in one query is not a complete access-control system.

**Interview follow-up:** Where must trusted tenant identity, warehouse grants and consumer policy be enforced?

### L30. Inspect an actual access path

Compare the local probe query plan before and after a matching composite index.

**Worked explanation:** The separate probe table contains 10,003 rows, mostly older data. The unindexed query scans and sorts; the composite tenant/day/order index supports a covering search with the same ordered result. No timing or cloud columnar pruning result is measured.

Run `python examples/analytics-engineering/lab.py L30`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "before": [
    {
      "id": 3,
      "parent": 0,
      "notused": 216,
      "detail": "SCAN probe_orders"
    },
    {
      "id": 16,
      "parent": 0,
      "notused": 0,
      "detail": "USE TEMP B-TREE FOR ORDER BY"
    }
  ],
  "after": [
    {
      "id": 3,
      "parent": 0,
      "notused": 47,
      "detail": "SEARCH probe_orders USING COVERING INDEX probe_tenant_day (tenant_id=? AND order_day>? AND order_day<?)"
    }
  ],
  "result": [
    {
      "order_id": "a"
    },
    {
      "order_id": "b"
    }
  ],
  "timing_benchmark": false
}
```

**Common trap:** SQLite index behavior is not evidence of BigQuery partition/clustering performance or a production cost saving.

**Interview follow-up:** How would you validate the target warehouse's real query plan, bytes, latency and cost?

### L31. Caught up is not complete

Explain a zero local cursor gap alongside one quarantined entity.

**Worked explanation:** All admitted deliveries through the local raw upper bound have been considered, yet ambiguity still excludes an entity. Receipt progress, source completeness, semantic quality and consumer publication age are separate observability dimensions. This example measures a sequence gap, not wall-clock freshness.

Run `python examples/analytics-engineering/lab.py L31`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "local_raw_upper": 25,
  "committed_upper": 25,
  "quarantined_entities": 1,
  "all_source_entities_complete": false
}
```

**Common trap:** A current checkpoint cannot certify that the source producer sent every required record.

**Interview follow-up:** Which source control totals and reconciliation jobs would help detect silent missing data?

### L32. Separate logical sizing from measured scan cost

Calculate a hypothetical projected/pruned logical data size from the supplied row and selectivity assumptions.

**Worked explanation:** Multiply the assumed row count and logical bytes per row, then the assumed partition and column shares. The result is a teaching estimate only. Actual compressed blocks, pruning, caching, metadata and billing rules need target-engine measurements.

Run `python examples/analytics-engineering/lab.py L32`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "assumed_rows": 1000000,
  "assumed_logical_bytes_per_row": 1000,
  "unpruned_logical_bytes": 1000000000,
  "assumed_partition_share": 0.1,
  "assumed_column_share": 0.2,
  "illustrative_remaining_bytes": 20000000,
  "measured_scan_or_cost": false
}
```

**Common trap:** A logical arithmetic reduction is not a measured query speedup or cloud bill.

**Interview follow-up:** What experiment would compare a full scan, projected query and partition-filtered query on the target engine?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. What determines batch versus streaming?
Required freshness, change rate, source/consumer constraints, cost and recovery needs. Tool fashion is not a substitute for that contract.

### Q2. What is partitioning versus clustering?
They organize data at different layout levels in relevant engines. Actual pruning depends on query filters, layout and implementation.

### Q3. Does SELECT fewer columns prove a smaller cloud bill?
No. It is a useful optimization hypothesis, but engine storage, execution and pricing must be measured.

### Q4. Is Parquet a complete transactional table system?
No. A file format and a table/catalog format supply different responsibilities; engine integration determines usable guarantees.

### Q5. Does a caught-up cursor prove completeness?
No. It can mean every received item was considered while the producer omitted required records or some entities remain quarantined.

### Q6. Are tenant-scoped keys a complete authorization system?
No. They help model integrity. Trusted identity, permissions, grants and consumer/export controls are still required.

### Q7. Does the local plan establish warehouse scalability?
No. It verifies a specific SQLite access path and result preservation, not a cloud or distributed performance claim.

### Q8. What should accompany a warehouse change?
Versioned contracts/code, dependency assessment, appropriate validation, controlled publication, recovery behavior and consumer communication.

## Practice tasks

1. Draw a production architecture that preserves the local source and publication contracts.
2. Explain which measured evidence would be needed before claiming a real columnar pruning saving.
3. Add an access and export policy without assuming a tenant predicate authenticates a reader.
4. Write a failed-refresh incident note naming source bounds, last-good status, affected consumers and repair verification.

**Answer checkpoints:** preserve capture/replay and publication boundaries; measure the actual target engine; model integrity differs from authentication; expose stale/unavailable results and validate the repair.

- [ ] I can connect warehouse correctness to deployment and operations.
- [ ] I can distinguish measured access paths from logical estimates.

Continue with [Consolidation and Mocks](/docs/analytics-engineering/consolidation-and-mocks).
