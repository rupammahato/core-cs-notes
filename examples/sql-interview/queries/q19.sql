WITH cutoffs(label,asof) AS (VALUES('initial',:knowledge_cutoff),('revised',:later_knowledge)),
mature AS (SELECT * FROM customers WHERE tenant_id=:tenant AND signup_ts+8*86400<=:event_cutoff),
flags AS (
 SELECT k.label,c.customer_id,EXISTS(SELECT 1 FROM canonical_events e
 WHERE e.tenant_id=:tenant AND e.customer_id=c.customer_id AND e.event_name='activity'
 AND e.event_ts>=c.signup_ts+7*86400 AND e.event_ts<c.signup_ts+8*86400
 AND e.event_ts<:event_cutoff AND e.ingested_ts<k.asof) returned
 FROM cutoffs k CROSS JOIN mature c
)
SELECT label,COUNT(*) eligible_users,SUM(returned) returned_users,
 ROUND(100.0*SUM(returned)/COUNT(*),6) retention_pct FROM flags GROUP BY label ORDER BY label;
