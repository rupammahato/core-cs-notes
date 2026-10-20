WITH months(month) AS (VALUES('2026-08-01'),('2026-09-01'),('2026-10-01')),
counts AS (
 SELECT m.month,COUNT(o.order_id) paid_orders FROM months m
 LEFT JOIN (SELECT o.* FROM orders o JOIN customers c USING(customer_id)
            WHERE c.tenant_id=:tenant AND o.status='paid') o
 ON date(o.ordered_ts,'unixepoch','start of month')=m.month GROUP BY m.month
), prior AS (SELECT *,LAG(paid_orders) OVER(ORDER BY month) previous_count FROM counts)
SELECT *,ROUND(100.0*(paid_orders-previous_count)/NULLIF(previous_count,0),6) change_pct
FROM prior ORDER BY month;
