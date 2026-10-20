WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), choices AS (
 SELECT p.order_id,h.plan,ROW_NUMBER() OVER(PARTITION BY p.order_id ORDER BY h.effective_ts DESC) rn
 FROM paid p LEFT JOIN plan_history h ON h.customer_id=p.customer_id AND h.effective_ts<=p.ordered_ts
)
SELECT order_id,COALESCE(plan,'Unmapped') plan FROM choices WHERE rn=1 ORDER BY order_id;
