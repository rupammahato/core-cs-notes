WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), settled AS (
 SELECT order_id,SUM(amount_cents) confirmed_cents,COUNT(*) confirmed_payments
 FROM payments WHERE status='succeeded' GROUP BY order_id
), refunded AS (
 SELECT order_id,SUM(amount_cents) refund_cents FROM refunds GROUP BY order_id
)
SELECT COUNT(*) paid_orders,SUM(COALESCE(s.confirmed_cents,0)) confirmed_cents,
 SUM(COALESCE(r.refund_cents,0)) refund_cents,
 SUM(COALESCE(s.confirmed_cents,0)-COALESCE(r.refund_cents,0)) confirmed_net_cents,
 COUNT(*)-COUNT(p.billed_cents) missing_bills
FROM paid p LEFT JOIN settled s USING(order_id) LEFT JOIN refunded r USING(order_id);
