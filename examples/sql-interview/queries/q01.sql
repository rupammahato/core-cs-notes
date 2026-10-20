SELECT c.customer_id,COUNT(o.order_id) paid_orders
FROM customers c LEFT JOIN orders o ON o.customer_id=c.customer_id
 AND o.status='paid' AND o.ordered_ts>=:start AND o.ordered_ts<:end
WHERE c.tenant_id=:tenant GROUP BY c.customer_id ORDER BY c.customer_id;
