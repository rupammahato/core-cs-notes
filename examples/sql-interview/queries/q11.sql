WITH RECURSIVE paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), days(day) AS (
 SELECT :calendar_start UNION ALL
 SELECT date(day,'+1 day') FROM days WHERE date(day,'+1 day')<:report_end_day
), daily AS (
 SELECT d.day,COALESCE(SUM(p.billed_cents),0) known_contribution,
 COUNT(p.order_id)-COUNT(p.billed_cents) missing_bills
 FROM days d LEFT JOIN paid p ON date(p.ordered_ts,'unixepoch')=d.day
 GROUP BY d.day
), running AS (
 SELECT day,known_contribution,
 SUM(known_contribution) OVER(ORDER BY day ROWS UNBOUNDED PRECEDING) running_known,
 SUM(missing_bills) OVER(ORDER BY day ROWS UNBOUNDED PRECEDING) running_missing
 FROM daily WHERE day>=:report_start_day
)
SELECT *,CASE WHEN running_missing=0 THEN running_known END complete_running
FROM running ORDER BY day;
