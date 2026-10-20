WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
), previous AS (
 SELECT *,LAG(event_ts) OVER(ORDER BY event_ts,event_id) previous_ts FROM known_events
 WHERE customer_id=:customer AND event_name='activity'
), numbered AS (
 SELECT *,SUM(CASE WHEN previous_ts IS NULL OR event_ts-previous_ts>1800 THEN 1 ELSE 0 END)
 OVER(ORDER BY event_ts,event_id ROWS UNBOUNDED PRECEDING) session_id FROM previous
)
SELECT session_id,datetime(MIN(event_ts),'unixepoch') start_utc,COUNT(*) events
FROM numbered GROUP BY session_id ORDER BY session_id;
