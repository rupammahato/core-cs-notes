# SQL Interview Problem Book — Part 6: Reconciliation and Query Plans

**Q25-Q30: expose source exceptions and explain the actual access path.**

Verified on Python 3.13.15 / SQLite 3.50.4, 20 October 2026. The full lab passes 86 checks. Inputs are invented; the SQL shown is the exact executed solution.

Diagnostics are useful only under a stated authority and source contract. Q26 is an authorized ingestion audit, not a tenant-facing endpoint. Billing, line amounts, confirmed payments and refunds are separate facts; reconcile them before recommending a business action.

Read the [dataset and solving contract](/docs/sql-interview/dataset-and-solving-method) before attempting these problems. Use the shared bound parameters from parameters.json.

## Q25. Exact repeats versus conflicting event identities

Audit event identities with more than one delivery; show deliveries, distinct payloads and conflict class.

**Hint:** Count distinct full payload rows before grouping identity.

### Worked query

```sql
WITH payloads AS (
 SELECT DISTINCT tenant_id,event_id,customer_id,event_ts,event_name FROM raw_events WHERE tenant_id=:tenant
), counts AS (SELECT tenant_id,event_id,COUNT(*) payloads FROM payloads GROUP BY tenant_id,event_id)
SELECT r.event_id,COUNT(*) deliveries,c.payloads,
 CASE WHEN c.payloads=1 THEN 'exact-repeat' ELSE 'conflict' END kind
FROM raw_events r JOIN counts c USING(tenant_id,event_id) WHERE r.tenant_id=:tenant
GROUP BY r.tenant_id,r.event_id,c.payloads HAVING COUNT(*)>1 ORDER BY r.event_id;
```

### Verified output

| event_id | deliveries | payloads | kind |
| --- | --- | --- | --- |
| a1 | 2 | 1 | exact-repeat |
| conflict | 2 | 2 | conflict |

### Why it works

Delivery count and distinct payload count answer different questions. Consistent repeated reports can collapse to one business event; conflicting identities require a correction or quarantine policy. Receipt identity alone does not resolve authoritative event truth.

**Common wrong answer:** A conflicting identity is quarantined by the helper view; latest delivery is not automatically authoritative.

**Interview follow-up:** Which changes would require a versioned correction model?

## Q26. Unknown and mismatched event ownership

For an authorized ingestion audit, identify unknown customers or a tenant/customer mismatch involving t1.

**Hint:** LEFT JOIN on identity first so ownership mismatch remains visible.

### Worked query

```sql
SELECT r.delivery_id,CASE WHEN c.customer_id IS NULL THEN 'unknown-customer' ELSE 'tenant-mismatch' END issue
FROM raw_events r LEFT JOIN customers c ON c.customer_id=r.customer_id
WHERE (r.tenant_id=:tenant OR c.tenant_id=:tenant)
AND (c.customer_id IS NULL OR c.tenant_id<>r.tenant_id) ORDER BY r.delivery_id;
```

### Verified output

| delivery_id | issue |
| --- | --- |
| bad-tenant | tenant-mismatch |
| unknown-user | unknown-customer |

### Why it works

The initial identity-only left join makes both missing owners and wrong-tenant owners observable. The query is explicitly an ingestion administrator diagnostic over this fixture. A public application must derive and enforce its own trusted authorization scope.

**Common wrong answer:** This is a trusted administrative fixture audit, not a tenant-facing authorization query.

**Interview follow-up:** Where must trusted tenant context be enforced in an application?

## Q27. Reconcile payments and refunds per order

Show confirmed payments, refunds, confirmed net and bill gap for each October paid order.

**Hint:** Aggregate each child fact independently.

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
SELECT p.order_id,COALESCE(s.confirmed_cents,0) confirmed_cents,
 COALESCE(r.refund_cents,0) refund_cents,
 COALESCE(s.confirmed_cents,0)-COALESCE(r.refund_cents,0) confirmed_net_cents,
 p.billed_cents-COALESCE(s.confirmed_cents,0) bill_gap_cents
FROM paid p LEFT JOIN settled s USING(order_id) LEFT JOIN refunded r USING(order_id)
ORDER BY p.order_id;
```

### Verified output

| order_id | confirmed_cents | refund_cents | confirmed_net_cents | bill_gap_cents |
| --- | --- | --- | --- | --- |
| o01 | 1000 | 100 | 900 | 0 |
| o02 | 1000 | 0 | 1000 | 1000 |
| o03 | 1000 | 200 | 800 | 0 |
| o04 | 1500 | 0 | 1500 | 0 |
| o05 | 1500 | 1500 | 0 | 0 |
| o06 | 3000 | 0 | 3000 | 0 |
| o07 | 0 | 0 | 0 | 0 |
| o08 | 0 | 0 | 0 | NULL |
| o09 | 400 | 0 | 400 | 0 |

### Why it works

Payment and refund sums are computed independently at order grain. Their later joins cannot create cross-products between transactions. Missing billing is still unknown even when the supplied confirmed-payment sum is zero.

**Common wrong answer:** Pending payments and unknown billing have different meanings. Refunds here are supplied order-linked amounts, not a real recognition policy.

**Interview follow-up:** What evidence would establish payment-extract completeness and refund timing?

## Q28. Reconcile grand totals without multi-fact fan-out

Return order count, confirmed payments, refunds, net and missing bills for the selected orders.

**Hint:** Reduce payments and refunds separately before joining.

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
SELECT COUNT(*) paid_orders,SUM(COALESCE(s.confirmed_cents,0)) confirmed_cents,
 SUM(COALESCE(r.refund_cents,0)) refund_cents,
 SUM(COALESCE(s.confirmed_cents,0)-COALESCE(r.refund_cents,0)) confirmed_net_cents,
 COUNT(*)-COUNT(p.billed_cents) missing_bills
FROM paid p LEFT JOIN settled s USING(order_id) LEFT JOIN refunded r USING(order_id);
```

### Verified output

| paid_orders | confirmed_cents | refund_cents | confirmed_net_cents | missing_bills |
| --- | --- | --- | --- | --- |
| 9 | 9400 | 1800 | 7600 | 1 |

### Why it works

The order population is fixed once and each reduced child contributes at most once. The resulting sum reconciles to the per-order result, including the unknown-bill count. A successful payment amount is a different measure from the original bill.

**Common wrong answer:** Joining raw payments and raw refunds multiplies both fact tables when either has several rows.

**Interview follow-up:** Why can the per-order and overall totals both look plausible after a bad join?

## Q29. Explain line-to-bill exceptions

Flag missing bills, missing item evidence or line totals differing from known bills. This fixture contract has no separate tax/shipping/discount adjustments.

**Hint:** Keep missing evidence separate from numeric mismatch.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), lines AS (
 SELECT order_id,SUM(line_cents) line_total FROM items GROUP BY order_id
)
SELECT p.order_id,CASE WHEN p.billed_cents IS NULL THEN 'missing-bill'
 WHEN l.line_total IS NULL THEN 'missing-items' ELSE 'line-bill-mismatch' END issue
FROM paid p LEFT JOIN lines l USING(order_id)
WHERE p.billed_cents IS NULL OR l.line_total IS NULL OR p.billed_cents<>l.line_total
ORDER BY p.order_id;
```

### Verified output

| order_id | issue |
| --- | --- |
| o05 | line-bill-mismatch |
| o08 | missing-bill |
| o09 | missing-items |

### Why it works

The exception priority distinguishes unknown billing from absent line evidence before checking numeric equality. Under this fixture contract, known bills should equal the supplied item sum. A real tax, shipping or discount policy would change the reconciliation rule.

**Common wrong answer:** COALESCE can hide missing line evidence. Real invoices need their actual adjustment and rounding policies.

**Interview follow-up:** Would a legitimate discount make this same rule a valid exception?

## Q30. Inspect a selective ordered lookup plan

Return c1 October orders ordered by time and ID. Compare its actual SQLite plan before and after a matching composite index.

**Hint:** Keep the indexed timestamp bare in the predicate.

### Worked query

```sql
SELECT o.order_id FROM orders o JOIN customers c USING(customer_id)
WHERE c.tenant_id=:tenant AND o.customer_id=:customer
AND o.ordered_ts>=:start AND o.ordered_ts<:end ORDER BY o.ordered_ts,o.order_id;
```

### Verified output

| order_id |
| --- |
| o01 |
| o02 |
| o03 |

### Why it works

Tenant and customer equality constrain the population while the bare timestamp range stays usable by an appropriate index. The experiment adds historical rows on a separate in-memory connection and compares actual plans. A preserved result and a covering search are evidence of this access path, not a measured production speedup.

**Common wrong answer:** An index name or a tiny timing difference does not prove production performance; preserve result equivalence and explain plan evidence.

**Interview follow-up:** How could SELECT date(ordered_ts,...) in WHERE affect the usable access path?

## Actual plan evidence for Q30

A separate in-memory connection adds 10,000 older rows outside the report interval. Before the matching composite index, the engine scans the existing order primary-key index and uses a temporary B-tree for sorting. After the new index it performs a covering search. Both return o01, o02 and o03.

### Before the composite index

| id | parent | notused | detail |
| --- | --- | --- | --- |
| 6 | 0 | 47 | SEARCH c USING INDEX sqlite_autoindex_customers_1 (customer_id=?) |
| 14 | 0 | 215 | SCAN o USING INDEX sqlite_autoindex_orders_1 |
| 28 | 0 | 0 | USE TEMP B-TREE FOR ORDER BY |

### After the composite index

| id | parent | notused | detail |
| --- | --- | --- | --- |
| 5 | 0 | 47 | SEARCH c USING INDEX sqlite_autoindex_customers_1 (customer_id=?) |
| 13 | 0 | 46 | SEARCH o USING COVERING INDEX orders_customer_time (customer_id=? AND ordered_ts>? AND ordered_ts<?) |

The verified index definition is:

```sql
CREATE INDEX orders_customer_time ON orders(customer_id, ordered_ts, order_id);
```

EXPLAIN QUERY PLAN text is engine/version-specific and can change. This is local access-path evidence, not a timing benchmark. [SQLite plan output](https://www.sqlite.org/eqp.html), [query planner](https://www.sqlite.org/queryplanner.html).

## Practice checkpoint

- [ ] I can write these queries before reading the solutions.
- [ ] I can state the output grain and a counterexample to the tempting wrong answer.
- [ ] I can adapt one boundary or missingness rule and explain the changed result.

Return to the [roadmap](/docs/sql-interview) or continue with [consolidation and mocks](/docs/sql-interview/consolidation-and-mocks).
