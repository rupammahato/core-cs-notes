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
