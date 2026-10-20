SELECT c.customer_id FROM customers c WHERE c.tenant_id=:tenant
AND NOT EXISTS(SELECT 1 FROM exclusions x WHERE x.customer_id=c.customer_id)
ORDER BY c.customer_id;
