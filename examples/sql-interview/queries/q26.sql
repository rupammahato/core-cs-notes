SELECT r.delivery_id,CASE WHEN c.customer_id IS NULL THEN 'unknown-customer' ELSE 'tenant-mismatch' END issue
FROM raw_events r LEFT JOIN customers c ON c.customer_id=r.customer_id
WHERE (r.tenant_id=:tenant OR c.tenant_id=:tenant)
AND (c.customer_id IS NULL OR c.tenant_id<>r.tenant_id) ORDER BY r.delivery_id;
