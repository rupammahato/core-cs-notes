WITH payloads AS (
 SELECT DISTINCT tenant_id,event_id,customer_id,event_ts,event_name FROM raw_events WHERE tenant_id=:tenant
), counts AS (SELECT tenant_id,event_id,COUNT(*) payloads FROM payloads GROUP BY tenant_id,event_id)
SELECT r.event_id,COUNT(*) deliveries,c.payloads,
 CASE WHEN c.payloads=1 THEN 'exact-repeat' ELSE 'conflict' END kind
FROM raw_events r JOIN counts c USING(tenant_id,event_id) WHERE r.tenant_id=:tenant
GROUP BY r.tenant_id,r.event_id,c.payloads HAVING COUNT(*)>1 ORDER BY r.event_id;
