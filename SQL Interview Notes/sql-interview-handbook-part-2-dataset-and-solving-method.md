# SQL Interview Problem Book — Part 2: Dataset and Solving Method

**Before choosing an operator, define what one result row means.**

## 1. The problem-solving contract

For every query, say: “One output row represents ___; eligible records are ___; amounts are ___; the interval is ___; missing data means ___; ties are handled by ___.” That sentence often reveals a mistake before SQL is written.

The fixture is invented commerce and product-event data. Its timestamps use aware UTC epoch seconds, and money uses integer USD cents. The report interval is 1 October inclusive to 1 November exclusive. Event behavior is observed before 12 October at midnight UTC; knowledge has an initial cutoff on 12 October and a later cutoff on 14 October. These are synthetic exercise settings, not complete real monthly reports.

Customer signup timestamps are UTC-midnight cohort anchors in this dataset. The retention formulas use elapsed 86,400-second days from those anchors. For a different signup/calendar definition, normalize the cohort anchor deliberately. Do not substitute this arithmetic for a local civil day across daylight-saving transitions.

## 2. Source grains and deliberate traps

| Table | One row means | Main issue to notice |
| --- | --- | --- |
| customers | One globally unique customer identity with tenant and signup anchor | Scope eligible users before counting |
| carts | One cart creation | Cart-level outcomes differ from customer-level outcomes |
| orders | One order | Paid/cancelled and missing/zero billing differ |
| items | One order line | Joining lines repeats order-level amounts |
| payments | One payment record | Only succeeded payments count as confirmed here |
| refunds | One order-linked refund amount | Several refunds can multiply several payment rows |
| plan_history | One effective plan change per customer/time | Current state is not historical state |
| exclusions | One supplied exclusion-list value | A NULL exposes NOT IN semantics |
| raw_events | One delivery of an event report | Delivery identity differs from business-event identity |

The full schema and all source rows are in `examples/sql-interview/schema.sql` and `fixture.json`. The fixture includes a second tenant, customers without paid orders, tied order timestamps, equal order amounts, an unknown bill, missing item evidence, a line/bill mismatch, a repeated event, a conflicting event identity, late data and two invalid ownership reports.

The amounts and identities are teaching data. They are unrelated to original resume transactions, customer exports or interview-company datasets.

## 3. Load and inspect the fixture

From the repository root:

```powershell
python examples/sql-interview/lab.py Q01
python examples/sql-interview/lab.py Q19
python examples/sql-interview/verify.py
```

The runner creates an in-memory SQLite database, enables foreign keys, loads tables in dependency order, executes a query with bound named parameters and closes the connection. No database file or listener is left running.

Each `queries/qNN.sql` file is standalone after loading `schema.sql` and `fixture.json`. `parameters.json` supplies its named values. Unused dictionary entries are harmless; values are bound through the driver rather than interpolated into SQL text. The loader's table-name construction uses only the authored fixture inventory, not user-controlled identifiers.

**Executed environment:** Python 3.13.15 and SQLite 3.50.4. No PostgreSQL engine was run for this book. Current documentation can describe a newer SQLite build; recorded outputs are tied to this environment.

## 4. A repeatable query strategy

```text
Question -> output grain -> eligible base set
  -> reduce each child fact/dimension to the required grain
  -> join or test existence
  -> aggregate or calculate windows
  -> apply output filter and deterministic ordering
  -> reconcile counts, amounts and boundary rows
```

A CTE can name an intermediate stage and make the grain easier to inspect. It is not automatically a performance optimization or a guarantee that an intermediate result is materialized. Recursive CTEs build the small date spine here. [SQLite WITH](https://www.sqlite.org/lang_with.html).

Do not add DISTINCT merely because the output has too many rows. Diagnose the relationship that created them. Two legitimate orders can have the same amount; deduplicating their amounts loses real contribution.

## 5. Count, sum and missingness

COUNT(*) counts result rows; COUNT(column) counts non-NULL observations in that column. SUM ignores NULL inputs and returns NULL when no known input exists. These behaviors do not decide whether an incomplete business total is publishable. [SQLite aggregates](https://www.sqlite.org/lang_aggfunc.html).

Q03 preserves an all-missing customer bill as NULL and separately counts missing bills. Q11/Q12 use an additive **known contribution**, with absent observations contributing nothing to that subtotal while missing-bill counts remain visible. Complete running billing is withheld after an unresolved bill enters the selected period. The zero contribution is not a claim that unknown billing is zero.

In the supplied complete payment ledger, no succeeded payment means zero confirmed payments. That does not mean a missing bill is zero. A partial external payment extract would require additional completeness evidence before using this convention.

For exclusion membership, correlated NOT EXISTS avoids the fixture's NULL-bearing NOT IN trap. The exact SQL three-valued semantics still matter when the left identity itself is missing. Canonical customer identities are non-NULL here. [SQLite expressions](https://www.sqlite.org/lang_expr.html).

## 6. Dates, frames and ordered rows

The queries use SQLite's `date`, `datetime`, `unixepoch` and `julianday` functions with explicit epoch interpretation. An integer is not automatically interpreted as the timestamp unit you intended. [SQLite date/time functions](https://www.sqlite.org/lang_datefunc.html).

Half-open intervals use `>= start AND < end`. They avoid overlap between adjacent reports. A seven-row frame represents seven calendar days only after the dataset contains one row per calendar day. Q12 creates that spine and calculates its window before slicing the requested report days.

Window ordering and final output ordering have different jobs. A deterministic latest-row choice needs a tie-breaker; ranking distinct value tiers should preserve ties. Aggregate windows use explicit ROWS frames here instead of relying on peer-sensitive defaults. [SQLite window functions](https://www.sqlite.org/windowfunctions.html).

## 7. The canonical event view

The view groups event identity by `(tenant_id, event_id)`. It compares payload identity, customer, event time and event name across the supplied snapshot. A conflicting payload quarantines the identity; consistent repeated deliveries collapse to the earliest receipt with a delivery-ID tie-breaker. Only events whose customer and tenant agree are admitted.

The analytical queries then apply event-time and receipt-time cutoffs. The late-event exercise changes which consistent records are known while keeping the behavioral period fixed.

This view evaluates conflict quarantine across the full supplied snapshot. It does not reconstruct what an observer knew about a conflict before the conflicting delivery arrived, and it does not implement authoritative corrections, retractions or aliases. Both conflicting fixture deliveries are already known at the exercise cutoffs. A real historical-event system needs a versioned policy; Q19's later knowledge result is a narrower illustration.

Q26 deliberately reads invalid raw ownership records as an authorized administrative diagnostic. It is not an example of application authorization for an arbitrary tenant user. Q30's lookup also includes tenant scope rather than treating a client-supplied customer ID as authority.

## 8. Billing, lines, payments and refunds

The fixture's bill/line reconciliation contract has no separate taxes, shipping or discounts. Q29 therefore treats a known bill differing from the supplied sum of lines as an exception. A real invoice would need its actual adjustment and rounding policy.

Confirmed payment minus supplied refunds is a fixture reconciliation measure. It is not a statement about revenue recognition, cash-settlement timing or an independently audited invoice. The book's payment extract is treated as complete for its stated source snapshot; external extracts must prove that boundary.

## 9. Dialect and portability boundary

| Construct in this lab | What to revisit when moving engines |
| --- | --- |
| Epoch seconds and SQLite date functions | Timestamp type, conversion and timezone rules |
| Numeric comparisons used inside MAX/SUM | Boolean aggregate or explicit CASE support |
| Recursive date spine | Recursive CTE syntax or a native series/calendar source |
| Named `:parameter` binding | The selected driver's binding convention |
| NULL ordering and ties | Explicit ordering policy for the target engine |
| Query-plan detail strings | Engine/version-specific plan format and cost model |

PostgreSQL also supports window functions, but the executable syntax here is SQLite-first. Review the [PostgreSQL window tutorial](https://www.postgresql.org/docs/current/tutorial-window.html) and [date/time documentation](https://www.postgresql.org/docs/current/functions-datetime.html) when adapting it. No cross-engine result parity is asserted by these local checks.

## 10. What to explain after a passing query

State why its grain is correct, how it treats a zero-order customer, a tie, a NULL amount and a boundary timestamp, and which source-completeness assumption it needs. A passing fixture is stronger when you can also explain a changed input that would break a tempting alternative.

Continue with [Q01–Q08: Joins, Grain and NULL](/docs/sql-interview/joins-grain-and-null-semantics).

<!-- BEGIN SQL FIXTURE TABLES -->

## 11. Inspect the actual source rows

The tables below are the complete fixture, not abbreviated samples. Timestamp columns are displayed as UTC text for reading; fixture.json and the database store the corresponding integer epoch seconds. NULL remains an unknown value.

### customers

| customer_id | tenant_id | signup_ts (UTC) |
| --- | --- | --- |
| c1 | t1 | 2026-10-01 00:00:00 |
| c2 | t1 | 2026-10-01 00:00:00 |
| c3 | t1 | 2026-10-02 00:00:00 |
| c4 | t1 | 2026-10-02 00:00:00 |
| c5 | t1 | 2026-10-03 00:00:00 |
| c6 | t1 | 2026-10-04 00:00:00 |
| c7 | t1 | 2026-10-10 00:00:00 |
| c8 | t1 | 2026-10-11 00:00:00 |
| c9 | t2 | 2026-10-01 00:00:00 |

### carts

| cart_id | customer_id | created_ts (UTC) |
| --- | --- | --- |
| r1 | c1 | 2026-10-01 08:00:00 |
| r2 | c2 | 2026-10-01 09:00:00 |
| r3 | c3 | 2026-10-02 11:00:00 |
| r4 | c7 | 2026-10-11 23:30:00 |
| r5 | c2 | 2026-10-05 08:00:00 |

### orders

| order_id | customer_id | ordered_ts (UTC) | status | billed_cents | cart_id |
| --- | --- | --- | --- | --- | --- |
| o00 | c1 | 2026-09-30 12:00:00 | paid | 700 | NULL |
| o01 | c1 | 2026-10-01 08:20:00 | paid | 1000 | r1 |
| o02 | c1 | 2026-10-03 12:00:00 | paid | 2000 | NULL |
| o03 | c1 | 2026-10-03 12:00:00 | paid | 1000 | NULL |
| o04 | c2 | 2026-10-01 10:30:00 | paid | 1500 | r2 |
| o05 | c2 | 2026-10-05 08:20:00 | paid | 1500 | r5 |
| o06 | c3 | 2026-10-02 12:00:00 | paid | 3000 | NULL |
| o07 | c4 | 2026-10-03 09:00:00 | paid | 0 | NULL |
| o08 | c5 | 2026-10-06 14:00:00 | paid | NULL | NULL |
| o09 | c8 | 2026-10-11 10:00:00 | paid | 400 | NULL |
| o10 | c6 | 2026-10-04 10:00:00 | cancelled | 500 | NULL |
| o11 | c9 | 2026-10-02 10:00:00 | paid | 9000 | NULL |

### items

| item_id | order_id | category | line_cents |
| --- | --- | --- | --- |
| i01 | o01 | books | 600 |
| i02 | o01 | software | 400 |
| i03 | o02 | software | 1000 |
| i04 | o02 | books | 1000 |
| i05 | o03 | books | 1000 |
| i06 | o04 | books | 1500 |
| i07 | o05 | software | 1400 |
| i08 | o06 | software | 3000 |
| i09 | o07 | books | 0 |
| i10 | o08 | books | 800 |
| i11 | o11 | books | 9000 |

### payments

| payment_id | order_id | amount_cents | status |
| --- | --- | --- | --- |
| p01 | o01 | 600 | succeeded |
| p02 | o01 | 400 | succeeded |
| p03 | o02 | 1000 | succeeded |
| p04 | o02 | 1000 | pending |
| p05 | o03 | 1000 | succeeded |
| p06 | o04 | 1500 | succeeded |
| p07 | o05 | 1500 | succeeded |
| p08 | o06 | 3000 | succeeded |
| p09 | o07 | 0 | succeeded |
| p10 | o09 | 400 | succeeded |
| p11 | o00 | 700 | succeeded |
| p12 | o11 | 9000 | succeeded |

### refunds

| refund_id | order_id | amount_cents |
| --- | --- | --- |
| f01 | o01 | 50 |
| f02 | o01 | 50 |
| f03 | o03 | 200 |
| f04 | o05 | 1500 |

### plan_history

| customer_id | effective_ts (UTC) | plan |
| --- | --- | --- |
| c1 | 2026-09-01 00:00:00 | free |
| c1 | 2026-10-02 00:00:00 | paid |
| c2 | 2026-09-01 00:00:00 | free |
| c3 | 2026-09-01 00:00:00 | paid |
| c4 | 2026-09-01 00:00:00 | free |

### exclusions

| customer_id |
| --- |
| c2 |
| NULL |

### raw_events

| delivery_id | event_id | tenant_id | customer_id | event_ts (UTC) | ingested_ts (UTC) | event_name |
| --- | --- | --- | --- | --- | --- | --- |
| a1 | a1 | t1 | c1 | 2026-10-01 10:00:00 | 2026-10-01 10:00:00 | activity |
| a2 | a2 | t1 | c1 | 2026-10-01 10:30:00 | 2026-10-01 10:30:00 | activity |
| a3 | a3 | t1 | c1 | 2026-10-01 11:00:01 | 2026-10-01 11:00:01 | activity |
| a4 | a4 | t1 | c1 | 2026-10-02 10:00:00 | 2026-10-02 10:00:00 | activity |
| a5 | a5 | t1 | c1 | 2026-10-08 10:00:00 | 2026-10-08 10:00:00 | activity |
| a6 | a6 | t1 | c2 | 2026-10-01 10:00:00 | 2026-10-01 10:00:00 | activity |
| a7 | a7 | t1 | c2 | 2026-10-03 10:00:00 | 2026-10-03 10:00:00 | activity |
| a8 | a8 | t1 | c2 | 2026-10-04 10:00:00 | 2026-10-04 10:00:00 | activity |
| a9 | a9 | t1 | c3 | 2026-10-03 10:00:00 | 2026-10-03 10:00:00 | activity |
| a10 | a10 | t1 | c3 | 2026-10-10 10:00:00 | 2026-10-10 10:00:00 | activity |
| a11 | a11 | t1 | c4 | 2026-10-03 10:00:00 | 2026-10-03 10:00:00 | activity |
| a12 | a12 | t1 | c4 | 2026-10-09 10:00:00 | 2026-10-09 10:00:00 | activity |
| a13 | a13 | t1 | c5 | 2026-10-04 10:00:00 | 2026-10-04 10:00:00 | activity |
| a14 | a14 | t1 | c6 | 2026-10-05 10:00:00 | 2026-10-05 10:00:00 | activity |
| a15 | a15 | t1 | c7 | 2026-10-11 10:00:00 | 2026-10-11 10:00:00 | activity |
| a16 | a16 | t1 | c8 | 2026-10-11 10:00:00 | 2026-10-11 10:00:00 | activity |
| repeat-a1 | a1 | t1 | c1 | 2026-10-01 10:00:00 | 2026-10-01 10:01:00 | activity |
| late | late | t1 | c2 | 2026-10-08 10:00:00 | 2026-10-13 10:00:00 | activity |
| s1 | s1 | t1 | c1 | 2026-10-01 09:00:00 | 2026-10-01 09:00:00 | onboard_start |
| v1 | v1 | t1 | c1 | 2026-10-02 09:00:00 | 2026-10-02 09:00:00 | activate |
| s2 | s2 | t1 | c2 | 2026-10-01 09:00:00 | 2026-10-01 09:00:00 | onboard_start |
| v2 | v2 | t1 | c2 | 2026-10-10 09:00:00 | 2026-10-10 09:00:00 | activate |
| v3 | v3 | t1 | c3 | 2026-10-02 09:00:00 | 2026-10-02 09:00:00 | activate |
| s3 | s3 | t1 | c3 | 2026-10-03 09:00:00 | 2026-10-03 09:00:00 | onboard_start |
| s5 | s5 | t1 | c5 | 2026-10-03 09:00:00 | 2026-10-03 09:00:00 | onboard_start |
| v5 | v5 | t1 | c5 | 2026-10-04 09:00:00 | 2026-10-04 09:00:00 | activate |
| s6 | s6 | t1 | c6 | 2026-10-04 09:00:00 | 2026-10-04 09:00:00 | onboard_start |
| v6 | v6 | t1 | c6 | 2026-10-11 00:00:00 | 2026-10-11 00:00:00 | activate |
| conflict-a | conflict | t1 | c1 | 2026-10-02 14:00:00 | 2026-10-02 14:00:00 | activity |
| conflict-b | conflict | t1 | c1 | 2026-10-02 14:00:00 | 2026-10-02 14:00:00 | other |
| bad-tenant | wrong-tenant | t2 | c1 | 2026-10-02 15:00:00 | 2026-10-02 15:00:00 | activity |
| unknown-user | unknown | t1 | ghost | 2026-10-02 15:00:00 | 2026-10-02 15:00:00 | activity |

<!-- END SQL FIXTURE TABLES -->
