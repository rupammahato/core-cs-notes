# Analytics Engineering and Warehousing — Part 8: Semantic Metrics and Consumption

**A7: make a metric definition a reusable contract rather than a chart-specific formula.**

## 1. What a semantic layer is for

A semantic layer describes entities, measures, dimensions, relationships and metric definitions for consistent consumption. It can reduce duplicated business logic across dashboards and queries, but still depends on correct source/model contracts and appropriate access enforcement.

A table called revenue or active_users is not a definition. Consumers need to know the grain, amount/time units, eligibility, period, distinct-identity policy, missingness, revisions, owner and source coverage.

## 2. The lesson's paid-billing contract

| Field | Meaning |
| --- | --- |
| Eligible order | Latest admitted nondeleted order whose status is paid |
| Amount | Supplied integer USD billed cents, not settlement or recognized revenue |
| Segment | Current knowledge of business-effective customer plan at order day |
| Known subtotal | Sum of nonmissing admitted bills, zero when no known contribution exists in a retained group |
| Missing bills | Number of admitted paid orders with unknown amount |
| Complete billing | Known subtotal only when that admitted group has no missing bills |
| Publication | Immutable run ID with source upper bound and metric definition paid-billing-v1 |

Unknown dimension classification, missing amounts and quarantined source entities are separate issues. A complete billed amount for admitted facts does not imply complete source capture or a complete accounting ledger.

## 3. Aggregate measures at the correct unit

```text
overall average bill = sum(complete eligible billing) / count(eligible paid orders)
```

Preserve numerator and denominator. An equal average of daily averages weights days, while the overall order average weights orders. Both can be defined questions, but swapping them silently changes the estimand.

Rates and averages are usually nonadditive. Distinct users cannot generally be summed across overlapping days or segments. Balances may be additive across accounts but not time. A semantic definition should state the valid reaggregation behavior rather than promise that every measure can be summed.

Zero-value paid orders count in the denominator. Missing bills do not become zero merely to allow division. An alternative known-subtotal ratio can be published under a distinct transparent name, with coverage limitations.

## 4. Historical reports and revisions

Late facts, amount corrections, deletes and dimension restatements can legitimately revise older dates. Readers must distinguish a source revision from a definition change. Pin run ID and definition when comparing results.

The lab stores each published mart's plan labels and measures, so run1 remains readable after later dimension corrections. Current fact/dimension tables are not immutable historical generations. Reconstructing an earlier fact-level knowledge state requires bounded source replay or a fuller versioned design, not simply joining today's dimension to yesterday's query.

## 5. Consumer interfaces and ownership

Expose stable names, units and approved relationships. Document which dimensions can filter a metric and how late data affects it. A metric owner should review breaking changes and provide migration guidance to known consumers.

Dashboards should show relevant publication freshness, known missingness and revision status. Exported spreadsheets, notebooks and downstream services can become hidden consumers; include them in dependency and deprecation discussions where possible.

For cohort, experiment and causal interpretation, use the [product analytics](/docs/product-analytics/product-analytics-experiments) and [statistics](/docs/probability-statistics) bridges. A warehouse can consistently compute the wrong denominator if the business contract is wrong.

## 6. Avoid ambiguous joins at consumption time

Facts at different grains should not be casually joined and then summed. Conform shared dimensions, aggregate each relevant fact independently or use a validated bridge/allocation rule. A semantic tool's relationship metadata still needs to match actual cardinality and temporal behavior.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L25. Reconcile tenant totals across publications

Explain accepted paid-order counts and known billing at all three stages.

**Worked explanation:** Corrections, deletes and late facts change totals according to the declared latest-state contract. The independent reference recalculates the complete admitted mart after every stage. The untouched t2 order remains separate despite sharing a business order ID with t1.

Run `python examples/analytics-engineering/lab.py L25`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "run_id": "run1",
    "tenant_id": "t1",
    "known_bill_cents": 4300,
    "paid_orders": 5
  },
  {
    "run_id": "run1",
    "tenant_id": "t2",
    "known_bill_cents": 9000,
    "paid_orders": 1
  },
  {
    "run_id": "run2",
    "tenant_id": "t1",
    "known_bill_cents": 3200,
    "paid_orders": 6
  },
  {
    "run_id": "run2",
    "tenant_id": "t2",
    "known_bill_cents": 9000,
    "paid_orders": 1
  },
  {
    "run_id": "run3",
    "tenant_id": "t1",
    "known_bill_cents": 3250,
    "paid_orders": 6
  },
  {
    "run_id": "run3",
    "tenant_id": "t2",
    "known_bill_cents": 9000,
    "paid_orders": 1
  }
]
```

**Common trap:** Historical restatement can be correct; freeze a source prefix and publication ID before comparing results.

**Interview follow-up:** When would a consumer instead need an append-only accounting-event measure?

### L26. Compute a complete average only when its inputs are complete

Inspect final tenant totals and average billing per paid order.

**Worked explanation:** The missing bill has become a known zero by the third stage. Sum amounts and paid-order denominators before dividing; zero-value paid orders still count. Before repair, a complete average should be withheld even though a known-subtotal ratio could be calculated under another name.

Run `python examples/analytics-engineering/lab.py L26`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "paid_orders": 6,
    "known_cents": 3250,
    "missing_bills": 0,
    "complete_cents": 3250,
    "complete_average_cents": 541.666667
  },
  {
    "tenant_id": "t2",
    "paid_orders": 1,
    "known_cents": 9000,
    "missing_bills": 0,
    "complete_cents": 9000,
    "complete_average_cents": 9000.0
  }
]
```

**Common trap:** A known subtotal divided by all orders must not be mislabeled as a complete average.

**Interview follow-up:** How would unknown currency conversion or refunds change this metric's contract?

### L27. Read the semantic daily mart

Inspect the final tenant/day/plan metric rows and explain their grain.

**Worked explanation:** The mart includes only admitted paid orders, aggregates each amount once and shows missing counts alongside known and complete billing. Plans represent supplied business-effective history as currently known. The metric version is a named definition, not an automatic external accounting standard.

Run `python examples/analytics-engineering/lab.py L27`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Exact model SELECT executed by the pipeline:**

```sql
SELECT f.tenant_id,f.order_day,d.plan,COUNT(*) paid_orders,
 COALESCE(SUM(f.billed_cents),0) known_bill_cents,
 COUNT(*)-COUNT(f.billed_cents) missing_bills,
 CASE WHEN COUNT(*)=COUNT(f.billed_cents) THEN SUM(f.billed_cents) END complete_bill_cents
FROM next_fact f JOIN next_dim d
 ON d.tenant_id=f.tenant_id AND d.customer_sk=f.customer_sk
WHERE f.status='paid'
GROUP BY f.tenant_id,f.order_day,d.plan;
```

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
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
```

**Common trap:** A mart needs stable meaning, ownership and revision policy, not just a useful table name.

**Interview follow-up:** How would you version a breaking eligibility or plan-classification change?

### L28. Execute an average-of-averages error

Compare an unweighted average of daily order averages with the full order-weighted average.

**Worked explanation:** Different paid days contain different numbers of orders. Equal day weights answer a different question from equal order weights. The SQL executes both definitions against the same final t1 accepted data.

Run `python examples/analytics-engineering/lab.py L28`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "unweighted_daily_average": 472.222222,
    "correct_order_weighted_average": 541.666667
  }
]
```

**Common trap:** Ratios are generally not additive; preserve their numerator and denominator for valid reaggregation.

**Interview follow-up:** Which metrics are additive, semi-additive or nonadditive across your desired dimensions?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. What belongs in a metric definition?
Population, grain, numerator/denominator, units, time window, identity, missingness, revision policy, source and ownership.

### Q2. Is billing the same as revenue?
Not automatically. The lesson's billed amount is a selected source measure; accounting recognition and settlement need their own contracts.

### Q3. Why keep a missing-bill count?
It lets consumers distinguish an observed zero from an unresolved amount and assess whether a complete measure can be published.

### Q4. Why is averaging daily averages different?
Days have different order counts. Equal day weights are not the same as equal order weights.

### Q5. Can daily distinct users be added to get weekly distinct users?
Generally no. Users can appear on several days; use an appropriate distinct-set or supported approximate-state method with declared error semantics.

### Q6. Does a semantic layer remove the need for model tests?
No. It depends on valid grains, keys, relationships, histories and source data.

### Q7. How should a breaking metric change be handled?
Version the definition, document the changed meaning, assess downstream impact and coordinate a consumer migration rather than silently rewriting history.

### Q8. Why retain old mart versions?
They preserve the actual published result for reproducibility and comparison, within retention and access policy.

## Practice tasks

1. Explain why the initial t1 complete billing is withheld but final complete billing is available.
2. Rebuild L28 from numerator and denominator rather than averaging rate values.
3. Define a migration from billed amount to a different financial measure without reusing its name ambiguously.
4. Explain what an old mart version preserves and what it does not preserve about current fact tables.

**Answer checkpoints:** an unknown amount becomes observed zero; sum numerator and denominator at the intended unit; a financial definition change needs new contracts; immutable mart rows do not make all underlying current tables historically versioned.

- [ ] I can define a metric and its valid aggregation behavior.
- [ ] I can explain historical restatement and consumer versioning.

Continue with [Production Architecture and Performance](/docs/analytics-engineering/production-architecture-and-performance).
