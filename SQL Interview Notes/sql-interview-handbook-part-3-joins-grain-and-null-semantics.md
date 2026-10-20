# SQL Interview Problem Book — Part 3: Joins, Grain and NULL

**Q01-Q08: preserve the intended population and add each measure once.**

Verified on Python 3.13.15 / SQLite 3.50.4, 20 October 2026. The full lab passes 86 checks. Inputs are invented; the SQL shown is the exact executed solution.

The first eight tasks make row retention and measure grain explicit. State the difference between no order, cancelled work, an unknown bill and an observed zero. The supplied payment ledger is treated as complete; a real incomplete extract requires another completeness policy.

Read the [dataset and solving contract](/docs/sql-interview/dataset-and-solving-method) before attempting these problems. Use the shared bound parameters from parameters.json.

## Q01. Keep customers with no paid orders

Count October paid orders for every t1 customer, including customers with none.

**Hint:** Put order filters in ON and count the nullable-side identity.

### Worked query

```sql
SELECT c.customer_id,COUNT(o.order_id) paid_orders
FROM customers c LEFT JOIN orders o ON o.customer_id=c.customer_id
 AND o.status='paid' AND o.ordered_ts>=:start AND o.ordered_ts<:end
WHERE c.tenant_id=:tenant GROUP BY c.customer_id ORDER BY c.customer_id;
```

### Verified output

| customer_id | paid_orders |
| --- | --- |
| c1 | 3 |
| c2 | 2 |
| c3 | 1 |
| c4 | 1 |
| c5 | 1 |
| c6 | 0 |
| c7 | 0 |
| c8 | 1 |

### Why it works

The left input fixes the population at all tenant customers. Conditions on the optional orders remain in the match, so an unmatched customer is retained. Counting the non-null order identity then yields zero for that customer.

**Common wrong answer:** COUNT(*) counts the preserved customer row; WHERE o.status changes retention.

**Interview follow-up:** What if a customer has only cancelled orders?

## Q02. Find customers without a paid order

Return t1 customers with no paid order in the report interval.

**Hint:** Use NOT EXISTS with the same status and time contract.

### Worked query

```sql
SELECT c.customer_id FROM customers c WHERE c.tenant_id=:tenant
AND NOT EXISTS(SELECT 1 FROM orders o WHERE o.customer_id=c.customer_id
 AND o.status='paid' AND o.ordered_ts>=:start AND o.ordered_ts<:end)
ORDER BY c.customer_id;
```

### Verified output

| customer_id |
| --- |
| c6 |
| c7 |

### Why it works

The correlated subquery asks whether any eligible order exists for this customer. Its truth value is independent of how many items or payments the order has. A cancelled-only customer remains a no-paid-order customer.

**Common wrong answer:** No orders and only cancelled orders both qualify.

**Interview follow-up:** Would a customer with a zero-value paid order qualify?

## Q03. Known billing versus complete billing

For customers with October paid orders, return known billed sum, missing bills and complete total.

**Hint:** SUM ignores NULL; count missing observations separately.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
)
SELECT customer_id,SUM(billed_cents) known_bill_cents,
 COUNT(*)-COUNT(billed_cents) missing_bills,
 CASE WHEN COUNT(*)=COUNT(billed_cents) THEN SUM(billed_cents) END complete_bill_cents
FROM paid GROUP BY customer_id ORDER BY customer_id;
```

### Verified output

| customer_id | known_bill_cents | missing_bills | complete_bill_cents |
| --- | --- | --- | --- |
| c1 | 4000 | 0 | 4000 |
| c2 | 3000 | 0 | 3000 |
| c3 | 3000 | 0 | 3000 |
| c4 | 0 | 0 | 0 |
| c5 | NULL | 1 | NULL |
| c8 | 400 | 0 | 400 |

### Why it works

The group contains actual paid orders, not preserved customer placeholder rows. Compare total order count with nonmissing bill count before publishing a complete sum. A known zero stays part of the observed data.

**Common wrong answer:** A known subtotal is not a complete total; all-missing SUM is NULL.

**Interview follow-up:** What changes if the missing bill becomes an observed zero?

## Q04. Enrich orders without multiplying billing

Return customer billing and item count while preserving job-level billing grain.

**Hint:** Aggregate items to order grain before joining.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), item_counts AS (
 SELECT order_id,COUNT(*) item_count FROM items GROUP BY order_id
)
SELECT p.customer_id,SUM(p.billed_cents) known_bill_cents,
 SUM(COALESCE(i.item_count,0)) item_count
FROM paid p LEFT JOIN item_counts i USING(order_id)
GROUP BY p.customer_id ORDER BY p.customer_id;
```

### Verified output

| customer_id | known_bill_cents | item_count |
| --- | --- | --- |
| c1 | 4000 | 5 |
| c2 | 3000 | 2 |
| c3 | 3000 | 1 |
| c4 | 0 | 1 |
| c5 | NULL | 1 |
| c8 | 400 | 0 |

### Why it works

item_counts has at most one row per order, so enrichment cannot multiply an order bill. Missing line evidence contributes zero item count, while the bill sum keeps its own missingness semantics. The result remains one row per customer.

**Common wrong answer:** A direct items join repeats the full billed amount once per line.

**Interview follow-up:** Why is SUM(DISTINCT billed_cents) not a valid repair?

## Q05. Compare billing with confirmed payments

At order grain, show successful-payment count, confirmed amount and billing gap. Pending payments do not count.

**Hint:** Reduce payments before enriching orders.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), settled AS (
 SELECT order_id,SUM(amount_cents) confirmed_cents,COUNT(*) confirmed_payments
 FROM payments WHERE status='succeeded' GROUP BY order_id
), refunded AS (
 SELECT order_id,SUM(amount_cents) refund_cents FROM refunds GROUP BY order_id
)
SELECT p.order_id,COALESCE(s.confirmed_payments,0) confirmed_payments,
 COALESCE(s.confirmed_cents,0) confirmed_cents,
 p.billed_cents-COALESCE(s.confirmed_cents,0) bill_gap_cents
FROM paid p LEFT JOIN settled s USING(order_id) ORDER BY p.order_id;
```

### Verified output

| order_id | confirmed_payments | confirmed_cents | bill_gap_cents |
| --- | --- | --- | --- |
| o01 | 2 | 1000 | 0 |
| o02 | 1 | 1000 | 1000 |
| o03 | 1 | 1000 | 0 |
| o04 | 1 | 1500 | 0 |
| o05 | 1 | 1500 | 0 |
| o06 | 1 | 3000 | 0 |
| o07 | 1 | 0 | 0 |
| o08 | 0 | 0 | NULL |
| o09 | 1 | 400 | 0 |

### Why it works

Only succeeded payment rows are reduced into settled. Joining that reduced table preserves each selected order once. The subtraction propagates an unknown bill instead of declaring an amount discrepancy of zero.

**Common wrong answer:** An absent succeeded payment means no confirmed payment in this supplied complete ledger, not an unknown bill of zero.

**Interview follow-up:** What new completeness evidence is needed for a partial payment extract?

## Q06. Category line totals

Sum line amounts by category for October paid orders, including item lines whose order bill is unresolved.

**Hint:** Filter orders before aggregating line-level measures.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
)
SELECT i.category,SUM(i.line_cents) line_cents FROM paid p
JOIN items i USING(order_id) GROUP BY i.category ORDER BY i.category;
```

### Verified output

| category | line_cents |
| --- | --- |
| books | 4900 |
| software | 5800 |

### Why it works

The measure belongs to item grain, so its sum is taken over item rows matched to eligible orders. This is deliberately different from summing repeated order bills. A category line may be known even when the order bill is not.

**Common wrong answer:** Line totals are a separate source measure; they need not reconcile to incomplete or inconsistent order bills.

**Interview follow-up:** Where would you investigate a difference between line and order totals?

## Q07. Customers who bought both categories

Find customers whose paid order items include books and software in the interval.

**Hint:** Conditional aggregation avoids a multiplying double join.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
)
SELECT p.customer_id FROM paid p JOIN items i USING(order_id)
GROUP BY p.customer_id HAVING MAX(i.category='books')=1 AND MAX(i.category='software')=1
ORDER BY p.customer_id;
```

### Verified output

| customer_id |
| --- |
| c1 |
| c2 |

### Why it works

Each customer group is tested for membership of both requested categories. Several repeated books lines only keep the books flag true. No particular pair of item rows needs to be joined.

**Common wrong answer:** Repeated lines should not change category membership.

**Interview follow-up:** How would you require all categories from a variable requested set?

## Q08. A NULL-safe exclusion list

Return t1 customers absent from exclusions, which deliberately contains a NULL.

**Hint:** Use correlated NOT EXISTS.

### Worked query

```sql
SELECT c.customer_id FROM customers c WHERE c.tenant_id=:tenant
AND NOT EXISTS(SELECT 1 FROM exclusions x WHERE x.customer_id=c.customer_id)
ORDER BY c.customer_id;
```

### Verified output

| customer_id |
| --- |
| c1 |
| c3 |
| c4 |
| c5 |
| c6 |
| c7 |
| c8 |

### Why it works

The subquery checks an actual identity match, so a NULL exclusion is not equal to a valid customer ID. This avoids relying on NOT IN over an unknown comparison. Canonical customer identities cannot be NULL under the schema.

**Common wrong answer:** NOT IN with a NULL-bearing subquery can discard all otherwise eligible rows.

**Interview follow-up:** How should an actual NULL customer identity be handled?

## Practice checkpoint

- [ ] I can write these queries before reading the solutions.
- [ ] I can state the output grain and a counterexample to the tempting wrong answer.
- [ ] I can adapt one boundary or missingness rule and explain the changed result.

Return to the [roadmap](/docs/sql-interview) or continue with [consolidation and mocks](/docs/sql-interview/consolidation-and-mocks).
