# SQL Interview Problem Book — Part 4: Windows and Time Series

**Q09-Q16: rank ties, select stable rows and reason about calendar time.**

Verified on Python 3.13.15 / SQLite 3.50.4, 20 October 2026. The full lab passes 86 checks. Inputs are invented; the SQL shown is the exact executed solution.

Different tasks need different ordering contracts. Keep all tied value tiers with DENSE_RANK, but choose one latest row with a deterministic ROW_NUMBER tie-breaker. Dense date spines make calendar windows meaningful; historical dimension selection avoids using future state.

Read the [dataset and solving contract](/docs/sql-interview/dataset-and-solving-method) before attempting these problems. Use the shared bound parameters from parameters.json.

## Q09. Top two complete revenue tiers with ties

Return customers in the two highest distinct complete billed-value tiers; retain ties.

**Hint:** Aggregate and exclude incomplete totals, then DENSE_RANK.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), totals AS (
 SELECT customer_id,SUM(billed_cents) bill_cents FROM paid GROUP BY customer_id
 HAVING COUNT(*)=COUNT(billed_cents)
), ranked AS (
 SELECT *,DENSE_RANK() OVER(ORDER BY bill_cents DESC) revenue_rank FROM totals
)
SELECT customer_id,bill_cents,revenue_rank FROM ranked WHERE revenue_rank<=2
ORDER BY revenue_rank,customer_id;
```

### Verified output

| customer_id | bill_cents | revenue_rank |
| --- | --- | --- |
| c1 | 4000 | 1 |
| c2 | 3000 | 2 |
| c3 | 3000 | 2 |

### Why it works

The grouped source first establishes complete known billing for each ranked customer. DENSE_RANK assigns the same tier to equal totals without leaving gaps. Filtering tiers outside the window-producing CTE preserves all boundary ties.

**Common wrong answer:** ROW_NUMBER caps rows rather than distinct value tiers; ranking partial bills can mislead.

**Interview follow-up:** What would exactly two customers require?

## Q10. One deterministic latest order

Choose one latest October paid order per customer; equal timestamps choose the larger order ID.

**Hint:** ROW_NUMBER needs a total ordering.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY ordered_ts DESC,order_id DESC) rn FROM paid
)
SELECT customer_id,order_id,billed_cents FROM ranked WHERE rn=1 ORDER BY customer_id;
```

### Verified output

| customer_id | order_id | billed_cents |
| --- | --- | --- |
| c1 | o03 | 1000 |
| c2 | o05 | 1500 |
| c3 | o06 | 3000 |
| c4 | o07 | 0 |
| c5 | o08 | NULL |
| c8 | o09 | 400 |

### Why it works

The first sort key finds recency and the second chooses one row among equal timestamps. The row number is calculated within each customer. The outer filter selects one record without throwing away that record original bill value.

**Common wrong answer:** MAX(timestamp) joined back can return several tied orders.

**Interview follow-up:** How would the answer change if all latest ties were required?

## Q11. Running known billing with completeness

For Oct 1-10, return known daily contribution, cumulative known contribution, cumulative missing bills and complete running bill when possible.

**Hint:** Build a date spine and use explicit ROWS frames.

### Worked query

```sql
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
```

### Verified output

| day | known_contribution | running_known | running_missing | complete_running |
| --- | --- | --- | --- | --- |
| 2026-10-01 | 2500 | 2500 | 0 | 2500 |
| 2026-10-02 | 3000 | 5500 | 0 | 5500 |
| 2026-10-03 | 3000 | 8500 | 0 | 8500 |
| 2026-10-04 | 0 | 8500 | 0 | 8500 |
| 2026-10-05 | 1500 | 10000 | 0 | 10000 |
| 2026-10-06 | 0 | 10000 | 1 | NULL |
| 2026-10-07 | 0 | 10000 | 1 | NULL |
| 2026-10-08 | 0 | 10000 | 1 | NULL |
| 2026-10-09 | 0 | 10000 | 1 | NULL |
| 2026-10-10 | 0 | 10000 | 1 | NULL |

### Why it works

The date spine contributes rows for days with no orders. The running frame begins at the report start because this problem intentionally excludes earlier billing. Missing counts accumulate with known contribution, so a later row cannot imply complete billing after a missing input.

**Common wrong answer:** Zero known contribution on a missing-bill day is not a known zero total; the completeness flag must remain visible.

**Interview follow-up:** What does an unbounded frame start at after filtering?

## Q12. Seven calendar-day rolling bill

Show Oct 1-10 rolling known contribution and missing bills using six prior calendar days, including pre-report history.

**Hint:** Densify days, calculate the window, then slice the output.

### Worked query

```sql
WITH RECURSIVE paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=unixepoch(:calendar_start) AND o.ordered_ts<:end
), days(day) AS (
 SELECT :calendar_start UNION ALL
 SELECT date(day,'+1 day') FROM days WHERE date(day,'+1 day')<:report_end_day
), daily AS (
 SELECT d.day,COALESCE(SUM(p.billed_cents),0) known_contribution,
 COUNT(p.order_id)-COUNT(p.billed_cents) missing_bills
 FROM days d LEFT JOIN paid p ON date(p.ordered_ts,'unixepoch')=d.day
 GROUP BY d.day
), rolling AS (
 SELECT day,SUM(known_contribution) OVER(ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) rolling_known,
 SUM(missing_bills) OVER(ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) rolling_missing
 FROM daily
)
SELECT * FROM rolling WHERE day>=:report_start_day ORDER BY day;
```

### Verified output

| day | rolling_known | rolling_missing |
| --- | --- | --- |
| 2026-10-01 | 3200 | 0 |
| 2026-10-02 | 6200 | 0 |
| 2026-10-03 | 9200 | 0 |
| 2026-10-04 | 9200 | 0 |
| 2026-10-05 | 10700 | 0 |
| 2026-10-06 | 10700 | 1 |
| 2026-10-07 | 10000 | 1 |
| 2026-10-08 | 7500 | 1 |
| 2026-10-09 | 4500 | 1 |
| 2026-10-10 | 1500 | 1 |

### Why it works

The source includes the history needed for the first requested day. The window sees one row per calendar day, then the outer SELECT limits presentation. Do not compare this result with a window built over sparse sale dates.

**Common wrong answer:** Seven sparse sales rows are not seven calendar days; filtering early also loses lookback history.

**Interview follow-up:** How would a seven-complete-day metric treat today?

## Q13. Month-over-month counts and a zero baseline

Return supplied paid-order counts for Aug, Sep and Oct, previous count and relative change; zero prior count is undefined.

**Hint:** Use an explicit month spine and LAG.

### Worked query

```sql
WITH months(month) AS (VALUES('2026-08-01'),('2026-09-01'),('2026-10-01')),
counts AS (
 SELECT m.month,COUNT(o.order_id) paid_orders FROM months m
 LEFT JOIN (SELECT o.* FROM orders o JOIN customers c USING(customer_id)
            WHERE c.tenant_id=:tenant AND o.status='paid') o
 ON date(o.ordered_ts,'unixepoch','start of month')=m.month GROUP BY m.month
), prior AS (SELECT *,LAG(paid_orders) OVER(ORDER BY month) previous_count FROM counts)
SELECT *,ROUND(100.0*(paid_orders-previous_count)/NULLIF(previous_count,0),6) change_pct
FROM prior ORDER BY month;
```

### Verified output

| month | paid_orders | previous_count | change_pct |
| --- | --- | --- | --- |
| 2026-08-01 | 0 | NULL | NULL |
| 2026-09-01 | 1 | 0 | NULL |
| 2026-10-01 | 9 | 1 | 800.0 |

### Why it works

The month spine keeps the zero-order month in sequence. LAG reads the preceding count, not the preceding nonzero month. NULLIF makes a zero baseline undefined; partial real months would need a separate maturity policy.

**Common wrong answer:** These supplied fixture counts do not establish complete real monthly reporting or a fair growth claim.

**Interview follow-up:** Which maturity and as-of rules would you add to compare actual months?

## Q14. Consecutive active-day islands

Return activity streaks of at least two consecutive UTC dates per customer. Count each date once.

**Hint:** Deduplicate dates, subtract row number from date ordinal.

### Worked query

```sql
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
```

### Verified output

| customer_id | start_day | end_day | days |
| --- | --- | --- | --- |
| c1 | 2026-10-01 | 2026-10-02 | 2 |
| c2 | 2026-10-03 | 2026-10-04 | 2 |

### Why it works

First remove repeated dates for each customer. Consecutive dates and their sequential row numbers increase together, leaving a constant island key. Grouping that key recovers a run without counting repeated actions as additional days.

**Common wrong answer:** Several events on one day must not extend a streak.

**Interview follow-up:** What changes for local dates across daylight-saving boundaries?

## Q15. Thirty-minute inactivity sessions

Sessionize c1 activity events. A gap strictly greater than 1,800 seconds starts a new session; exact 1,800 remains in the same session.

**Hint:** LAG, boundary flag, cumulative SUM, then group.

### Worked query

```sql
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
```

### Verified output

| session_id | start_utc | events |
| --- | --- | --- |
| 1 | 2026-10-01 10:00:00 | 2 |
| 2 | 2026-10-01 11:00:01 | 1 |
| 3 | 2026-10-02 10:00:00 | 1 |
| 4 | 2026-10-08 10:00:00 | 1 |

### Why it works

LAG measures the gap to the immediately previous activity in event-time order. The first event and gaps above the stated threshold start sessions. A cumulative flag sum labels sessions before the final group counts their events.

**Common wrong answer:** Use event time and a deterministic tie-breaker; duplicate delivery is not another user action.

**Interview follow-up:** What if a late event bridges two existing sessions?

## Q16. Plan as of the order

Return the last plan effective at or before each paid order, with Unmapped when absent.

**Hint:** Join eligible history, then ROW_NUMBER per order.

### Worked query

```sql
WITH paid AS (
 SELECT o.* FROM orders o JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND o.status='paid'
 AND o.ordered_ts>=:start AND o.ordered_ts<:end
), choices AS (
 SELECT p.order_id,h.plan,ROW_NUMBER() OVER(PARTITION BY p.order_id ORDER BY h.effective_ts DESC) rn
 FROM paid p LEFT JOIN plan_history h ON h.customer_id=p.customer_id AND h.effective_ts<=p.ordered_ts
)
SELECT order_id,COALESCE(plan,'Unmapped') plan FROM choices WHERE rn=1 ORDER BY order_id;
```

### Verified output

| order_id | plan |
| --- | --- |
| o01 | free |
| o02 | paid |
| o03 | paid |
| o04 | free |
| o05 | free |
| o06 | paid |
| o07 | free |
| o08 | Unmapped |
| o09 | Unmapped |

### Why it works

Only historical changes effective by the order time are candidates. Descending effective time selects the last qualifying plan. The left join leaves one unmatched candidate when no history exists, preserving an Unmapped order.

**Common wrong answer:** Joining the current plan leaks future classification into past orders.

**Interview follow-up:** What if history permits overlapping or equal-effective versions?

## Practice checkpoint

- [ ] I can write these queries before reading the solutions.
- [ ] I can state the output grain and a counterexample to the tempting wrong answer.
- [ ] I can adapt one boundary or missingness rule and explain the changed result.

Return to the [roadmap](/docs/sql-interview) or continue with [consolidation and mocks](/docs/sql-interview/consolidation-and-mocks).
