WITH flags AS (
 SELECT r.cart_id,EXISTS(SELECT 1 FROM orders o WHERE o.cart_id=r.cart_id
 AND o.customer_id=r.customer_id AND o.status='paid' AND o.ordered_ts>=r.created_ts AND o.ordered_ts<r.created_ts+3600) converted
 FROM carts r JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND r.created_ts+3600<=:event_cutoff
)
SELECT COUNT(*) mature_carts,SUM(converted) converted_carts,SUM(1-converted) abandoned_carts,
 ROUND(100.0*SUM(1-converted)/NULLIF(COUNT(*),0),6) abandonment_pct FROM flags;
