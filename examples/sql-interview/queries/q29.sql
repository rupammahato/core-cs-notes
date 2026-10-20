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
