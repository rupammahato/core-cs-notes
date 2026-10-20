WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
), eligible AS (
 SELECT * FROM customers WHERE tenant_id=:tenant
 AND signup_ts+7*86400<=:event_cutoff
), first_starts AS (
 SELECT c.customer_id,MIN(e.event_ts) start_ts FROM eligible c
 LEFT JOIN known_events e ON e.customer_id=c.customer_id
 AND e.event_name='onboard_start' AND e.event_ts>=c.signup_ts
 AND e.event_ts<c.signup_ts+7*86400 GROUP BY c.customer_id
), funnel AS (
 SELECT c.customer_id,c.signup_ts,s.start_ts,
 MIN(e.event_ts) completion_ts FROM eligible c JOIN first_starts s USING(customer_id)
 LEFT JOIN known_events e ON e.customer_id=c.customer_id AND e.event_name='activate'
 AND e.event_ts>=s.start_ts AND e.event_ts<c.signup_ts+7*86400
 GROUP BY c.customer_id,c.signup_ts,s.start_ts
), choices AS (
 SELECT f.*,h.plan,ROW_NUMBER() OVER(PARTITION BY f.customer_id ORDER BY h.effective_ts DESC) rn
 FROM funnel f LEFT JOIN plan_history h ON h.customer_id=f.customer_id AND h.effective_ts<=f.signup_ts
)
SELECT COALESCE(plan,'Unmapped') plan,COUNT(*) eligible_users,COUNT(completion_ts) completed_users,
 ROUND(100.0*COUNT(completion_ts)/COUNT(*),6) completion_pct FROM choices WHERE rn=1
GROUP BY COALESCE(plan,'Unmapped') ORDER BY plan;
