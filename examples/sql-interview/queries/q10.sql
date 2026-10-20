WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY ordered_ts DESC,order_id DESC) rn FROM paid
)
SELECT customer_id,order_id,billed_cents FROM ranked WHERE rn=1 ORDER BY customer_id;
