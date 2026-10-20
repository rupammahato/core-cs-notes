# Analytics Engineering and Warehousing — Part 3: Dimensional Modeling and History

**A2: declare the business process and fact grain, then attach dimensions deliberately.**

## 1. A dimensional model starts with grain

Choose the process, declare the fact row and identify dimensions and measures. A star model puts a fact at the center of descriptive dimensions. Dimensions support filtering/grouping; facts capture events or observations at a declared grain. The roles are about the model, not whether a column happens to be numeric. [Microsoft: star schema](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).

| Fact pattern | One row might mean | Important distinction |
| --- | --- | --- |
| Transaction fact | One order line or payment event | Events and source versions are different grains |
| Periodic snapshot | One account/day balance | Balances are generally not additive across time |
| Accumulating snapshot | One workflow with milestone state | Updates require a clear lifecycle/revision policy |
| Factless fact | One qualifying association or occurrence | Counts depend on that association's grain |

The lesson's order fact is a latest-state order projection. Calling it an immutable transaction-event ledger would misrepresent its updates and deletes. Its line table is a separate, limited grain illustration.

## 2. Keys, dimensions and measure behavior

A natural/business key identifies a source entity within its domain. A surrogate key identifies a warehouse dimension row. Composite scope can be essential: order o1 and customer c1 exist independently in t1 and t2.

The lab uses a deterministic dimension-row identifier derived from customer identity and effective start, with tenant stored separately. Its length prefix avoids confusing embedded separators. Source metadata and transformation policy still determine whether that key is stable across corrections.

Measures can be additive over specified dimensions, semi-additive or nonadditive. Billing sums can aggregate over admitted same-currency orders. A balance does not sum meaningfully over consecutive dates. An average or rate needs its numerator and denominator, and distinct counts require appropriate set-aware handling.

Role-playing dimensions use one concept in several roles, such as order day and delivery day. A degenerate dimension retains an identifier such as order number in a fact without a separate descriptive table. Many-to-many bridges need allocation or distinct-entity policies to avoid multiplying measures.

## 3. Slowly changing dimensions

| Policy | Behavior | Question it can answer |
| --- | --- | --- |
| Type 1 | Overwrite selected attributes | Describe history using the current corrected attribute |
| Type 2 | Retain effective versions with validity bounds | Classify a fact using an applicable historical version |

SCD terminology does not determine the source of effective timestamps, correction policy or deletion behavior. Design those explicitly. [Microsoft: dimension history](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables).

This lab uses customer changes with source-supplied effective dates. Different effective starts form half-open periods. A higher source version at the same effective start corrects that currently known period, rather than preserving both plans in the active dimension. Raw deliveries retain the earlier evidence.

```text
valid_from <= fact_day
and (valid_to is null or fact_day < valid_to)
```

An order on the transition day belongs to the new period. Overlap can produce multiple matches; a gap can leave no match. Neither should be hidden by arbitrarily selecting one row after a fan-out join.

## 4. Late dimensions and restatement

An early-arriving fact can be known before its descriptive member. A scoped Unknown member preserves the fact and exposes missing classification. Depending on consumer requirements, unknown counts can warn, block or trigger a repair workflow.

When cLate history arrives, the lab reclassifies its earlier fact. A plan correction at the same start changes the enriched signature even though the dimension key stays stable. That causes affected daily segments to refresh.

This is current knowledge of business-effective history. It is not a bitemporal model that simultaneously supports effective time and historical knowledge time. Moving an effective date or retracting dimension changes requires a fuller correction contract than the supplied payload supports.

## 5. Grain protects the measure

Joining one order to several lines repeats order attributes and amounts. Aggregate each fact at the needed grain before combining independent facts, or use a relationship-aware semantic layer with a proved measure policy. Equal amounts do not mean equal business identities.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L05. Build effective-dated customer history

Inspect the initial SCD2-style customer periods and explain their endpoints.

**Worked explanation:** The dimension selects the highest source version for each supplied effective date, then LEAD closes the previous interval. An order on a boundary belongs to the interval starting there. The raw source supplies business-effective dates; these rows are not observations from a dbt polling snapshot.

Run `python examples/analytics-engineering/lab.py L05`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Exact model SELECT executed by the pipeline:**

```sql
WITH candidates AS (
 SELECT tenant_id,entity_id customer_id,source_version,
 json_extract(payload_json,'$.effective_from') valid_from,
 json_extract(payload_json,'$.plan') plan
 FROM valid_changes WHERE stream='customers'
), ranked AS (
 SELECT *,ROW_NUMBER() OVER(
 PARTITION BY tenant_id,customer_id,valid_from ORDER BY source_version DESC) rn
 FROM candidates
), periods AS (
 SELECT tenant_id,customer_id,valid_from,plan,
 LEAD(valid_from) OVER(PARTITION BY tenant_id,customer_id ORDER BY valid_from) valid_to
 FROM ranked WHERE rn=1
)
SELECT tenant_id,length(customer_id)||':'||customer_id||':'||valid_from customer_sk,
 customer_id,valid_from,valid_to,plan,0 is_unknown FROM periods
UNION ALL
SELECT DISTINCT tenant_id,'unknown','__unknown__','0001-01-01',NULL,'Unknown',1
FROM bounded_changes;
```

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "customer_id": "c1",
    "valid_from": "2026-10-01",
    "valid_to": "2026-10-03",
    "plan": "free"
  },
  {
    "tenant_id": "t1",
    "customer_id": "c1",
    "valid_from": "2026-10-03",
    "valid_to": null,
    "plan": "pro"
  },
  {
    "tenant_id": "t1",
    "customer_id": "c2",
    "valid_from": "2026-10-01",
    "valid_to": null,
    "plan": "free"
  },
  {
    "tenant_id": "t2",
    "customer_id": "c1",
    "valid_from": "2026-10-01",
    "valid_to": null,
    "plan": "enterprise"
  }
]
```

**Common trap:** System receipt time and business-effective time are different history axes.

**Interview follow-up:** How would you represent what was known at an earlier receipt cutoff as well as what was effective?

### L06. Join a fact to the historical dimension

Inspect plan assignments for initial orders, including c1's plan change.

**Worked explanation:** The join includes tenant, customer identity and a half-open validity interval containing order_day. It attaches exactly one qualifying version or the tenant-scoped Unknown member. Joining every order to today's plan would answer a different, restated-current-segment question.

Run `python examples/analytics-engineering/lab.py L06`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Exact model SELECT executed by the pipeline:**

```sql
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY tenant_id,entity_id ORDER BY source_version DESC) rn
 FROM valid_changes WHERE stream='orders'
), current_orders AS (
 SELECT tenant_id,entity_id order_id,source_version,
 json_extract(payload_json,'$.customer_id') customer_id,
 json_extract(payload_json,'$.order_day') order_day,
 json_extract(payload_json,'$.billed_cents') billed_cents,
 json_extract(payload_json,'$.status') status
 FROM ranked WHERE rn=1 AND json_extract(payload_json,'$.op')='U'
)
SELECT o.tenant_id,o.order_id,o.customer_id,COALESCE(d.customer_sk,'unknown') customer_sk,
 o.order_day,o.billed_cents,o.status,o.source_version
FROM current_orders o LEFT JOIN next_dim d
 ON d.tenant_id=o.tenant_id AND d.customer_id=o.customer_id AND d.is_unknown=0
 AND d.valid_from<=o.order_day AND (d.valid_to IS NULL OR o.order_day<d.valid_to);
```

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "order_id": "o1",
    "order_day": "2026-10-02",
    "plan": "free"
  },
  {
    "tenant_id": "t1",
    "order_id": "o2",
    "order_day": "2026-10-04",
    "plan": "pro"
  },
  {
    "tenant_id": "t1",
    "order_id": "o3",
    "order_day": "2026-10-02",
    "plan": "Unknown"
  },
  {
    "tenant_id": "t1",
    "order_id": "o4",
    "order_day": "2026-10-03",
    "plan": "free"
  },
  {
    "tenant_id": "t1",
    "order_id": "o5",
    "order_day": "2026-10-04",
    "plan": "free"
  },
  {
    "tenant_id": "t1",
    "order_id": "o8",
    "order_day": "2026-10-03",
    "plan": "pro"
  },
  {
    "tenant_id": "t2",
    "order_id": "o1",
    "order_day": "2026-10-02",
    "plan": "enterprise"
  }
]
```

**Common trap:** A join that omits the validity interval can multiply facts or misclassify history.

**Interview follow-up:** Which tests would detect overlapping dimensions and join fan-out?

### L07. Keep a late dimension visible as Unknown

Why is an initial order retained even though its customer history has not arrived?

**Worked explanation:** The cLate order is a known accepted business fact, but no supplied dimension interval applies yet. The tenant-scoped Unknown member preserves its amount and exposes the missing classification. Batch two later supplies the effective history and restates the affected mart segment.

Run `python examples/analytics-engineering/lab.py L07`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "order_id": "o3",
    "customer_id": "cLate",
    "customer_sk": "unknown"
  }
]
```

**Common trap:** Dropping unmatched facts makes a classification problem look like lower business activity.

**Interview follow-up:** When should unknown-dimension prevalence warn, block publication or trigger a targeted repair?

### L08. Execute an order-to-lines fan-out mistake

Compare a repeated order bill after a line join with its correct order-grain value.

**Worked explanation:** Two illustrative lines match the same initial order. Summing its order bill after the raw join repeats that bill. The separate line sum happens to equal the order bill in this supplied initial example, but the ledgers have different grains and no ongoing reconciliation contract in the lab.

Run `python examples/analytics-engineering/lab.py L08`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "wrong_join_bill_cents": 2000,
  "correct_bill_cents": 1000,
  "supplied_line_cents": 1000
}
```

**Common trap:** SUM(DISTINCT amount) is not a general repair because separate legitimate orders can share an amount.

**Interview follow-up:** How would you aggregate each measure before combining order, line, payment and refund facts?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. Why declare grain first?
Grain determines valid keys, joins and aggregations. Choosing dimensions without it can create a mixed-grain table that is hard to query correctly.

### Q2. Is an integer always a fact measure?
No. A numeric code can be a descriptive category or identifier. Meaning and aggregation behavior determine its role.

### Q3. Why use surrogate dimension keys?
They distinguish warehouse versions and can decouple source identifiers from analytical references. Their stability and scope still need a contract.

### Q4. Type 1 versus Type 2?
Type 1 overwrites selected attributes; Type 2 retains effective versions. Neither automatically supplies bitemporal knowledge history.

### Q5. How do you join a historical dimension?
Use scoped entity identity and the fact's relevant instant or day within a nonoverlapping validity interval.

### Q6. What is an unknown member for?
It preserves a known fact whose descriptive mapping is unavailable, while making that classification problem observable.

### Q7. Why is SUM(DISTINCT bill) unsafe?
Separate real orders can share the same bill. Deduplicating values can discard legitimate contribution.

### Q8. What is semi-additivity?
A measure can aggregate over some dimensions but not others, such as account balances across accounts but not simply across consecutive dates.

## Practice tasks

1. Explain which dimension period contains a fact exactly on a boundary.
2. Trace cLate from an initial Unknown member to its supplied historical plan.
3. Explain why a correction can change a plan while keeping the same dimension-row key.
4. Repair L08 conceptually without using DISTINCT on the amount.

**Answer checkpoints:** intervals are half-open; late history restates the admitted classification; same-effective-start corrections change known attributes; preaggregate at a business identity/grain before joining measures.

- [ ] I can defend a fact grain and dimension-history policy.
- [ ] I can explain fan-out, unknowns and historical restatement.

Continue with [Ingestion, CDC and Canonical State](/docs/analytics-engineering/ingestion-cdc-and-canonical-state).
