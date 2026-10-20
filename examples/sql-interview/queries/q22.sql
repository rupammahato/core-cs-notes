WITH paid_history AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid' AND o.ordered_ts<:event_cutoff
), firsts AS (SELECT customer_id,MIN(ordered_ts) first_ts FROM paid_history GROUP BY customer_id),
flags AS (
 SELECT f.customer_id,EXISTS(SELECT 1 FROM paid_history o WHERE o.customer_id=f.customer_id
 AND o.ordered_ts>f.first_ts AND o.ordered_ts<f.first_ts+7*86400) repeated
 FROM firsts f WHERE f.first_ts+7*86400<=:event_cutoff
)
SELECT COUNT(*) mature_first_purchasers,SUM(repeated) repeat_purchasers,
 ROUND(100.0*SUM(repeated)/NULLIF(COUNT(*),0),6) repeat_pct FROM flags;
