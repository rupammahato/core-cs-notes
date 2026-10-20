SELECT o.order_id FROM orders o JOIN customers c USING(customer_id)
WHERE c.tenant_id=:tenant AND o.customer_id=:customer
AND o.ordered_ts>=:start AND o.ordered_ts<:end ORDER BY o.ordered_ts,o.order_id;
