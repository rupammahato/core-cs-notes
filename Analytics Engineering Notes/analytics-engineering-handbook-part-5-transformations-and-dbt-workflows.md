# Analytics Engineering and Warehousing — Part 5: Transformations and dbt Workflows

**A4: make dependencies, meaning and validation visible in code.**

## 1. What dbt contributes

dbt organizes analytical transformations as models and related resources, with dependency references, configuration, tests, documentation and build artifacts. It relies on the selected data platform/adapter for execution behavior. It does not automatically capture source changes, determine business truth or certify every join.

The local lesson has analogous source/canonical/dimension/fact/mart steps implemented in Python and SQLite. No dbt engine or adapter runs. The examples below explain a possible dbt organization rather than provide a validated deployable project.

```text
models/staging/       explicit source projections and structural contracts
models/intermediate/ canonical entity/history logic and reusable joins
models/marts/        consumer facts, dimensions and aggregate models
tests/               business-specific violating-row queries
snapshots/           configured observed-change history where appropriate
```

## 2. source, ref and dependency discovery

Use source references to declared external tables and ref references to modeled dependencies. ref resolves a model relation and contributes dependency information; it is not simply a string replacement for a hard-coded production table. [dbt ref reference](https://docs.getdbt.com/reference/dbt-jinja-functions/ref).

**Illustrative dbt SQL, not executed here:**

```sql
{{ config(materialized='view') }}

select
    tenant_id,
    order_id,
    billed_cents
from {{ ref('stg_orders') }}
where status = 'paid'
```

This assumes a separately defined stg_orders model and a configured target. Actual adapters differ in SQL types, JSON extraction, merge strategy and constraints. A successful parse is not proof of valid warehouse data or consumer semantics.

## 3. Materializations and state

| Choice | Useful motivation | Cost/correctness trade-off |
| --- | --- | --- |
| View | Reuse logic without persisting its output | Runtime dependencies and repeated computation remain |
| Table | Persist a complete modeled relation | Rebuild/write cost and refresh timing matter |
| Incremental | Update an existing target from selected changes | Key uniqueness, source selection, deletes and restatement need explicit policies |
| Ephemeral/intermediate expansion | Reuse logic within downstream queries | Query expansion and debugging can become complex |

An incremental unique_key identifies merge/update correspondence; declaring it does not prove uniqueness in input or target. Duplicate keys and adapter strategy can cause failure or incorrect effects. The incremental and full-refresh branches must each be valid for their intended state. [dbt incremental models](https://docs.getdbt.com/docs/build/incremental-models).

Do not copy an event-date lookback into an incremental model without understanding which corrections it can miss. The next chapter executes that failure mode.

## 4. Tests, unit fixtures and contracts

Generic data tests can cover uniqueness, not-null, relationships and accepted values. A singular query can return domain-specific violations, such as overlapping effective intervals or mismatched totals. Unit fixtures can target transformation behavior with small controlled input; they do not replace tests on actual transformed datasets. [dbt data tests](https://docs.getdbt.com/docs/build/data-tests).

**Illustrative model properties, not parsed by dbt in this lab:**

```yaml
version: 2
models:
  - name: fct_orders
    columns:
      - name: tenant_id
        data_tests: [not_null]
      - name: order_id
        data_tests: [not_null]
      - name: status
        data_tests:
          - accepted_values:
              arguments:
                values: [paid, cancelled]
```

A separate composite-key test must include tenant_id and order_id; applying unique to order_id alone would reject legitimate cross-tenant identities. Tool version syntax must be checked against the project's pinned release.

Model contracts describe an expected output shape, including supported names/types and applicable constraints. Actual constraint support/enforcement depends on the resource and warehouse. Contracts do not replace business reconciliation or prove every upstream record was captured. [dbt model contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts).

## 5. Snapshots versus source-effective history

dbt snapshots capture changes observed across runs under configured keys and strategies. They can preserve history from a mutable source, subject to sampling frequency and delete/change configuration. They cannot recover an intermediate source state that was never observed unless another source provides it. [dbt snapshots](https://docs.getdbt.com/docs/build/snapshots).

The lab's dimension instead consumes explicit effective-dated change records. Its valid_from is a supplied business date, not automatically a snapshot observation timestamp. Keep that difference visible when choosing or combining the two patterns.

## 6. Documentation and development workflow

Document model purpose, owner, grain, keys, source assumptions, freshness, business definitions, excluded records and downstream consumers. A dependency graph helps trace possible impact; it does not know every downstream spreadsheet or exported report unless those dependencies are captured.

Review SQL and definition changes in version control. Use isolated development schemas, controlled source samples, targeted unit/data checks and consumer review for breaking changes. Promote only with a clear publication and rollback contract. No external CI or dbt deployment is performed by these notes.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L13. Project an explicit staging contract

Inspect the selected identity, schema version and business day from admitted raw payloads.

**Worked explanation:** Staging gives semi-structured source fields stable names and types while retaining raw payloads for inspection. This selection is executed with SQLite JSON functions. dbt would organize related transformations and dependencies, but its adapter syntax and execution are outside this run.

Run `python examples/analytics-engineering/lab.py L13`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "tenant_id": "t1",
    "order_id": "o1",
    "schema_version": 1,
    "order_day": "2026-10-02"
  },
  {
    "tenant_id": "t2",
    "order_id": "o1",
    "schema_version": 1,
    "order_day": "2026-10-02"
  }
]
```

**Common trap:** SELECT star through every layer hides source changes and expands a public contract accidentally.

**Interview follow-up:** Which additions are backward-compatible, and which require a versioned migration?

### L14. Validate declared dependency order

Read the local topological order for raw, canonical state, dimensions, facts, mart, quality and publication.

**Worked explanation:** Python's graphlib actually orders the declared dependencies and rejects an injected cycle. That demonstrates a graph property only. It does not parse dbt ref calls, schedule Airflow tasks or verify an external orchestrator's retry behavior.

Run `python examples/analytics-engineering/lab.py L14`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "declared_dependency_order": [
    "raw",
    "canonical",
    "dimensions",
    "facts",
    "mart",
    "quality",
    "publication"
  ],
  "dbt_or_airflow_executed": false
}
```

**Common trap:** A valid DAG is necessary for this dependency plan but does not prove its SQL or business definitions are correct.

**Interview follow-up:** Which tasks can run independently, and where must quality gate publication?

### L15. Read model-test failure counts

Interpret the eight executed candidate checks at a successful initial build.

**Worked explanation:** The checks return violating-row counts or reconciliation differences, all zero here. They cover key uniqueness, amount validity, dimension references and intervals, and paid-count/known-amount reconciliation. They do not certify source completeness, business meaning or every allowed input.

Run `python examples/analytics-engineering/lab.py L15`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "duplicate_fact_keys": 0,
  "negative_bills": 0,
  "missing_dimension_references": 0,
  "invalid_dimension_intervals": 0,
  "overlapping_dimension_intervals": 0,
  "duplicate_dimension_keys": 0,
  "paid_count_reconciliation": 0,
  "known_amount_reconciliation": 0
}
```

**Common trap:** A green test run reflects the tested assertions; it cannot establish an unstated contract.

**Interview follow-up:** Which tests belong at sources, staging, facts, metrics and consumer boundaries?

### L16. Retain an additive raw field without changing the metric

Inspect the campaign field added to a higher source version and the corresponding modeled order.

**Worked explanation:** Raw retains the additive campaign field. The explicitly projected fact does not automatically expose it as a new column or metric dimension. The higher version remains part of source lineage, while the declared billing value stays unchanged for that order.

Run `python examples/analytics-engineering/lab.py L16`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "retained_raw_campaign": "autumn",
  "modeled_order": [
    {
      "tenant_id": "t1",
      "order_id": "o1",
      "customer_id": "c1",
      "customer_sk": "2:c1:2026-10-01",
      "order_day": "2026-10-02",
      "billed_cents": 1200,
      "status": "paid",
      "source_version": 3,
      "plan": "free"
    }
  ]
}
```

**Common trap:** Landing an extra field is not the same as migrating downstream models or validating a new meaning.

**Interview follow-up:** What would a consumer-safe rollout for a newly required dimension include?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. Does dbt replace ingestion infrastructure?
Not generally. Its transformation workflow consumes accessible sources; capture and delivery remain separate concerns unless supplied by another component.

### Q2. Why use ref instead of a production schema name?
It expresses modeled dependencies and lets the configured environment resolve the relation rather than baking one deployment location into every query.

### Q3. Does unique_key enforce unique input?
No. Test source/target keys and understand the incremental strategy and adapter behavior.

### Q4. What distinguishes a unit test from a data test?
A unit fixture checks controlled transformation behavior; a data test checks assertions over an actual dataset at the relevant stage.

### Q5. Does a model contract prove business correctness?
No. Output shape and supported constraints do not establish source coverage, correct eligibility or valid metric meaning.

### Q6. Is a snapshot always business-effective history?
No. Snapshot observation/change timestamps need not equal when a business change took effect.

### Q7. How would you test a composite order key?
Group by both tenant and order identity and return duplicates; independently check required key fields for nulls.

### Q8. What is demonstrated by the local DAG?
A topological order and cycle rejection for a declared graph. It is not an executed dbt project or Airflow schedule.

## Practice tasks

1. Sketch source, staging, intermediate and mart responsibilities for the supplied orders.
2. Explain how a broken ref/dependency and a wrong business join are different failures.
3. Write the shape of a composite-key violation query using both tenant and order.
4. Explain why retaining a new raw campaign field does not automatically migrate a public model.

**Answer checkpoints:** physical dependencies and semantic validity are separate; composite scope matters; a consumer-facing addition needs definition, compatibility and validation rather than an automatic SELECT star.

- [ ] I can explain materializations, dependencies, tests and contracts.
- [ ] I can distinguish illustrative dbt workflow from the executed local lab.

Continue with [Incremental Refreshes and Backfills](/docs/analytics-engineering/incremental-refreshes-and-backfills).
