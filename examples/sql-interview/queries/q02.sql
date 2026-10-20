SELECT c.customer_id FROM customers c WHERE c.tenant_id=:tenant
AND NOT EXISTS(SELECT 1 FROM orders o WHERE o.customer_id=c.customer_id
 AND o.status='paid' AND o.ordered_ts>=:start AND o.ordered_ts<:end)
ORDER BY c.customer_id;
