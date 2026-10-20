WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
)
SELECT COUNT(DISTINCT CASE WHEN event_ts>=unixepoch(:activity_day) AND event_ts<unixepoch(:activity_day,'+1 day') THEN customer_id END) dau,
 COUNT(DISTINCT CASE WHEN event_ts>=unixepoch(:activity_day,'-6 days') AND event_ts<unixepoch(:activity_day,'+1 day') THEN customer_id END) active_7d
FROM known_events WHERE event_name='activity';
