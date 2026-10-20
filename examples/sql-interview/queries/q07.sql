WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
)
SELECT p.customer_id FROM paid p JOIN items i USING(order_id)
GROUP BY p.customer_id HAVING MAX(i.category='books')=1 AND MAX(i.category='software')=1
ORDER BY p.customer_id;
