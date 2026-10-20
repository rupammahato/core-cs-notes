WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
), dates AS (
 SELECT DISTINCT customer_id,date(event_ts,'unixepoch') day FROM known_events WHERE event_name='activity'
), islands AS (
 SELECT *,CAST(julianday(day) AS INTEGER)-ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY day) island FROM dates
)
SELECT customer_id,MIN(day) start_day,MAX(day) end_day,COUNT(*) days
FROM islands GROUP BY customer_id,island HAVING COUNT(*)>=2 ORDER BY customer_id,start_day;
