WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), totals AS (
 SELECT customer_id,SUM(billed_cents) bill_cents FROM paid GROUP BY customer_id
 HAVING COUNT(*)=COUNT(billed_cents)
), ranked AS (
 SELECT *,DENSE_RANK() OVER(ORDER BY bill_cents DESC) revenue_rank FROM totals
)
SELECT customer_id,bill_cents,revenue_rank FROM ranked WHERE revenue_rank<=2
ORDER BY revenue_rank,customer_id;
