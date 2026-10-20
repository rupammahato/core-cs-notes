WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
)
SELECT i.category,SUM(i.line_cents) line_cents FROM paid p
JOIN items i USING(order_id) GROUP BY i.category ORDER BY i.category;
