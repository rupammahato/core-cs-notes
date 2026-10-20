WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
), mature AS (
 SELECT * FROM customers WHERE tenant_id=:tenant
 AND signup_ts+(1+1)*86400<=:event_cutoff
), retained AS (
 SELECT c.*,EXISTS(SELECT 1 FROM known_events e WHERE e.customer_id=c.customer_id
 AND e.event_name='activity' AND e.event_ts>=c.signup_ts+1*86400
 AND e.event_ts<c.signup_ts+(1+1)*86400) returned FROM mature c
)
SELECT date(signup_ts,'unixepoch') cohort,COUNT(*) eligible_users,SUM(returned) returned_users,
 ROUND(100.0*SUM(returned)/COUNT(*),6) retention_pct FROM retained GROUP BY cohort ORDER BY cohort;
