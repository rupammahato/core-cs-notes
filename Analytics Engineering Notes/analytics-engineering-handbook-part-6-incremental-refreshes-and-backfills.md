# Analytics Engineering and Warehousing — Part 6: Incremental Refreshes and Backfills

**A5: define which changes are new to the pipeline and which business partitions they can revise.**

## 1. Two different selection questions

Extraction asks which source changes have not been considered. Recalculation asks which analytical entities or partitions those changes can affect. A business date is not automatically a safe cursor for the first question.

An old order can receive a new amount, deletion or classification. A newly received fact can have an old business date. A dimension correction can reclassify many facts without changing their order timestamps. Include those paths in the refresh design.

## 2. The lesson's algorithm and scope

```text
read last successful cursor and freeze current raw upper bound
rebuild full candidate canonical state, dimensions, facts and daily aggregates
compare old/new enriched fact signatures
collect both old and new paid-order tenant/day partitions
copy unaffected published rows and replace affected partitions
compare the selected result with the full candidate
commit current models, versioned mart, pointer and cursor together
```

Enriched signatures include plan attributes, not only dimension keys. A same-effective-start correction can change a plan while keeping its row key stable. The affected set also includes the old day of a deletion or moved order.

This miniature implementation computes the full candidate on every run and stores complete mart versions. It establishes partition-selection correctness and reconciliation, rather than reduced compute/write cost. A production incremental implementation would maintain affected keys/history and choose target-engine operations that satisfy the same contracts.

## 3. Refresh strategies and empty results

| Strategy | What must be true |
| --- | --- |
| Append | New rows really are new immutable logical facts |
| Keyed update/merge | Incoming and target identity, ordering and delete behavior are valid |
| Delete and insert affected keys | The replacement set is complete for every deleted key |
| Replace affected partitions | The new partition content is complete, including an intentionally empty partition |
| Full rebuild | Retained source and definitions can reconstruct the desired result |

A partition whose last eligible order is deleted must become empty. Inserting only nonempty newly computed groups leaves stale rows. An old partition also needs clearing when a row moves to another date.

The lab derives semantic changes by comparing candidate facts; its cursor is publication provenance, not a claim that only rows after that cursor are scanned. Do not infer a performance optimization from the word incremental.

## 4. Lookbacks and late data

A lookback can intentionally rescan a recent interval, reducing risk from bounded lateness. It does not establish completeness for arbitrary older corrections. Pair a justified source cursor with retention guarantees, source control totals, periodic reconciliation and an explicit older-data repair path.

L20 runs a deliberately wrong business-date filter. It skips both an amount correction and a late fact, creating a real wrong warehouse subtotal. Correctness requires the changed source records and their affected dates, not just the newest dates in the report.

## 5. Backfills are controlled reprocessing

Define source bounds, transformation/metric version, business interval, tenant scope, dependencies and expected control totals. Run into an isolated candidate, compare with the intended reference and publish under an auditable version. Protect current freshness and production capacity during large reprocessing.

A backfill can revise earlier history or apply a new definition. State which purpose applies. Do not label a definition change as mere late-data repair. The retained source must contain enough evidence to reconstruct the desired state; a full refresh cannot recover records that never landed or were deleted from all retained sources.

## 6. Orchestration intervals and retries

A scheduled run's data interval describes the intended period, which differs from the wall-clock time at which it runs. Airflow documents interval, catchup and backfill behavior; exact scheduling and APIs depend on the installed release and configuration. [Airflow Dag runs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html).

Pass explicit bounds to transformations, use stable logical run identity, keep retries idempotent and distinguish an existing successful run from a new raw prefix. The local lesson rejects reuse of a successful run identity for a different upper prefix.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L17. Compare initial and corrected publications

Explain the changed dates, plan segments and amounts after batch two.

**Worked explanation:** The publication combines an amount correction, a delete, an old-business-day fact, a late customer history and a plan correction. Full candidate facts and dimensions are rebuilt in this small lesson. Partition-selected mart publication is checked against complete candidate aggregation.

Run `python examples/analytics-engineering/lab.py L17`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "initial": [
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02",
      "plan": "Unknown",
      "paid_orders": 1,
      "known_bill_cents": 500,
      "missing_bills": 0,
      "complete_bill_cents": 500
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 1000,
      "missing_bills": 0,
      "complete_bill_cents": 1000
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 0,
      "missing_bills": 1,
      "complete_bill_cents": null
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03",
      "plan": "pro",
      "paid_orders": 1,
      "known_bill_cents": 800,
      "missing_bills": 0,
      "complete_bill_cents": 800
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-04",
      "plan": "pro",
      "paid_orders": 1,
      "known_bill_cents": 2000,
      "missing_bills": 0,
      "complete_bill_cents": 2000
    },
    {
      "tenant_id": "t2",
      "order_day": "2026-10-02",
      "plan": "enterprise",
      "paid_orders": 1,
      "known_bill_cents": 9000,
      "missing_bills": 0,
      "complete_bill_cents": 9000
    }
  ],
  "corrected": [
    {
      "tenant_id": "t1",
      "order_day": "2026-10-01",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 300,
      "missing_bills": 0,
      "complete_bill_cents": 300
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 1200,
      "missing_bills": 0,
      "complete_bill_cents": 1200
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02",
      "plan": "partner",
      "paid_orders": 1,
      "known_bill_cents": 500,
      "missing_bills": 0,
      "complete_bill_cents": 500
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03",
      "plan": "business",
      "paid_orders": 1,
      "known_bill_cents": 800,
      "missing_bills": 0,
      "complete_bill_cents": 800
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 0,
      "missing_bills": 1,
      "complete_bill_cents": null
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-05",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 400,
      "missing_bills": 0,
      "complete_bill_cents": 400
    },
    {
      "tenant_id": "t2",
      "order_day": "2026-10-02",
      "plan": "enterprise",
      "paid_orders": 1,
      "known_bill_cents": 9000,
      "missing_bills": 0,
      "complete_bill_cents": 9000
    }
  ]
}
```

**Common trap:** The demo establishes correctness of selected refresh behavior, not incremental compute savings at warehouse scale.

**Interview follow-up:** How would you identify and recompute only affected keys and partitions in a larger implementation?

### L18. Refresh every affected partition

Inspect batch two's old/new partition set and source bounds.

**Worked explanation:** Affected days come from both prior and new enriched fact signatures, including plan changes. The set includes the old date whose last paid order was deleted and the old business day of a newly received fact. Other-tenant rows are copied unchanged into the new immutable mart version.

Run `python examples/analytics-engineering/lab.py L18`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "run_id": "run2",
  "lower_seq": 14,
  "upper_seq": 20,
  "affected_partitions": [
    {
      "tenant_id": "t1",
      "order_day": "2026-10-01"
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02"
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03"
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-04"
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-05"
    }
  ],
  "changed_order_keys": 6,
  "quality_failures": {
    "duplicate_fact_keys": 0,
    "negative_bills": 0,
    "missing_dimension_references": 0,
    "invalid_dimension_intervals": 0,
    "overlapping_dimension_intervals": 0,
    "duplicate_dimension_keys": 0,
    "paid_count_reconciliation": 0,
    "known_amount_reconciliation": 0
  },
  "unknown_fact_rows": 0,
  "quarantined_entities": 1,
  "incremental_equals_full": true
}
```

**Common trap:** Filtering only the new state misses deletions and moves from old partitions.

**Interview follow-up:** How do dimension corrections expand the set of affected facts?

### L19. Clear a partition after an order moves

Inspect the third publication after o7 moves from Oct 5 to Oct 2 and its amount changes.

**Worked explanation:** The old and new business dates both belong to the refresh set. The old day's last paid row disappears, so the new publication must not carry its previous aggregate forward. A missing bill also becomes an observed zero; it changes missingness, not the known subtotal.

Run `python examples/analytics-engineering/lab.py L19`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "publication": {
    "run_id": "run3",
    "lower_seq": 20,
    "upper_seq": 25,
    "affected_partitions": [
      {
        "tenant_id": "t1",
        "order_day": "2026-10-02"
      },
      {
        "tenant_id": "t1",
        "order_day": "2026-10-03"
      },
      {
        "tenant_id": "t1",
        "order_day": "2026-10-05"
      }
    ],
    "changed_order_keys": 3,
    "quality_failures": {
      "duplicate_fact_keys": 0,
      "negative_bills": 0,
      "missing_dimension_references": 0,
      "invalid_dimension_intervals": 0,
      "overlapping_dimension_intervals": 0,
      "duplicate_dimension_keys": 0,
      "paid_count_reconciliation": 0,
      "known_amount_reconciliation": 0
    },
    "unknown_fact_rows": 0,
    "quarantined_entities": 1,
    "incremental_equals_full": true
  },
  "final_mart": [
    {
      "tenant_id": "t1",
      "order_day": "2026-10-01",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 300,
      "missing_bills": 0,
      "complete_bill_cents": 300
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02",
      "plan": "free",
      "paid_orders": 2,
      "known_bill_cents": 1650,
      "missing_bills": 0,
      "complete_bill_cents": 1650
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-02",
      "plan": "partner",
      "paid_orders": 1,
      "known_bill_cents": 500,
      "missing_bills": 0,
      "complete_bill_cents": 500
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03",
      "plan": "business",
      "paid_orders": 1,
      "known_bill_cents": 800,
      "missing_bills": 0,
      "complete_bill_cents": 800
    },
    {
      "tenant_id": "t1",
      "order_day": "2026-10-03",
      "plan": "free",
      "paid_orders": 1,
      "known_bill_cents": 0,
      "missing_bills": 0,
      "complete_bill_cents": 0
    },
    {
      "tenant_id": "t2",
      "order_day": "2026-10-02",
      "plan": "enterprise",
      "paid_orders": 1,
      "known_bill_cents": 9000,
      "missing_bills": 0,
      "complete_bill_cents": 9000
    }
  ]
}
```

**Common trap:** Overwriting only nonempty new groups leaves stale rows in now-empty partitions.

**Interview follow-up:** How would insert-overwrite or delete-and-insert semantics handle empty replacement partitions on your target engine?

### L20. Run the wrong event-date lookback

Compare a pipeline that drops old-order-day changes from batch two with the correct publication.

**Worked explanation:** The deliberately wrong pipeline skips the older-day correction and late order. It really runs a separate in-memory warehouse and produces the wrong known subtotal. The correct lesson follows a bounded local receipt prefix and derives impacted business partitions, rather than treating order day as a complete extraction cursor.

Run `python examples/analytics-engineering/lab.py L20`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "wrong_event_date_cutoff": "2026-10-03",
  "skipped_delivery_ids": [
    "o1-v2",
    "o6-late"
  ],
  "wrong_t1_known_cents": 2700,
  "correct_t1_known_cents": 3200,
  "all_three_publications_match_full_candidates": true
}
```

**Common trap:** A finite business-time lookback can mitigate lateness but is not proof that arbitrary corrections are captured.

**Interview follow-up:** What source cursor, periodic reconciliation and explicit backfill policy would close this gap?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. Is an order-date filter a CDC cursor?
Not generally. It can miss new knowledge about older business dates and source deletes/corrections.

### Q2. Why include old partitions?
Deletes and moved records remove contributions from their previous locations. Looking only at new rows leaves stale aggregates.

### Q3. Why compare dimension attributes as well as keys?
A corrected attribute can change a metric segment while retaining the same effective-start key.

### Q4. Does a lookback guarantee correctness?
Only under a justified bound and complete change contract. Arbitrary older changes need another capture/reconciliation/backfill path.

### Q5. When is append-only safe?
When the target grain and source policy truly represent immutable new logical records, with replay deduplication and later correction behavior defined.

### Q6. What should a backfill record?
Source and business bounds, code/definition version, scope, dependencies, validation evidence and the publication it creates or replaces.

### Q7. Does full refresh always fix a model?
No. Missing source evidence, a wrong definition or flawed joins can reproduce the same error at larger cost.

### Q8. Does this lesson measure incremental efficiency?
No. Full candidates are recomputed; the executed claim concerns affected-partition correctness and full-result agreement.

## Practice tasks

1. Trace the old and new dates needed when o7 moves.
2. Explain why a deleted last order requires an empty replacement partition.
3. Identify the two batch-two changes missed by L20's date cutoff.
4. Draft a backfill contract that changes the metric definition without hiding the revision.

**Answer checkpoints:** both dates and dimension effects matter; replace rather than only append groups; o1's correction and o6's late fact are skipped; distinguish definition version from source receipt revision.

- [ ] I can defend extraction and recomputation bounds separately.
- [ ] I can explain how a partition becomes intentionally empty.

Continue with [Quality, Observability and Publication](/docs/analytics-engineering/quality-observability-and-publication).
