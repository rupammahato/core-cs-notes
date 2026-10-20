WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
)
SELECT customer_id,SUM(billed_cents) known_bill_cents,
 COUNT(*)-COUNT(billed_cents) missing_bills,
 CASE WHEN COUNT(*)=COUNT(billed_cents) THEN SUM(billed_cents) END complete_bill_cents
FROM paid GROUP BY customer_id ORDER BY customer_id;
