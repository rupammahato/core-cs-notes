SELECT f.tenant_id,f.order_day,d.plan,COUNT(*) paid_orders,
 COALESCE(SUM(f.billed_cents),0) known_bill_cents,
 COUNT(*)-COUNT(f.billed_cents) missing_bills,
 CASE WHEN COUNT(*)=COUNT(f.billed_cents) THEN SUM(f.billed_cents) END complete_bill_cents
FROM next_fact f JOIN next_dim d
 ON d.tenant_id=f.tenant_id AND d.customer_sk=f.customer_sk
WHERE f.status='paid'
GROUP BY f.tenant_id,f.order_day,d.plan;
