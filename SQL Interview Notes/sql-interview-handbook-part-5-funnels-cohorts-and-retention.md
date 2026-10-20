# SQL Interview Problem Book — Part 5: Funnels, Cohorts and Retention

**Q17-Q24: define behavior, observation maturity and receipt-time knowledge.**

Verified on Python 3.13.15 / SQLite 3.50.4, 20 October 2026. The full lab passes 86 checks. Inputs are invented; the SQL shown is the exact executed solution.

The customer signup anchors are UTC midnight in this fixture. State whether a task measures an ordered first-start funnel, an exact-day return, an any-week return or a cart outcome. Hold the behavioral period fixed when studying late knowledge. These synthetic rates do not establish causal product effects.

Read the [dataset and solving contract](/docs/sql-interview/dataset-and-solving-method) before attempting these problems. Use the shared bound parameters from parameters.json.

## Q17. Ordered onboarding funnel

For signups with seven elapsed days observed, count eligible users, first starts within seven days and completions at or after that first start but before signup+7 days.

**Hint:** First reduce starts, then search for a completion no earlier than that start.

### Worked query

```sql
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
)
SELECT COUNT(*) eligible_users,COUNT(start_ts) started_users,COUNT(completion_ts) completed_users,
 ROUND(100.0*COUNT(completion_ts)/NULLIF(COUNT(*),0),6) completion_pct FROM funnel;
```

### Verified output

| eligible_users | started_users | completed_users | completion_pct |
| --- | --- | --- | --- |
| 6 | 5 | 2 | 33.333333 |

### Why it works

Eligibility is fixed before event matching. A first qualifying start is chosen per user, then only completions at or after that start and before the exclusive horizon count. This specified first-start model is not every possible multi-attempt funnel definition.

**Common wrong answer:** A completion before the first start is not an ordered funnel success; the upper bound is exclusive.

**Interview follow-up:** Would a different valid-attempt funnel need a different query?

## Q18. Exact day-one retention by cohort

Return signup-cohort D1 retention using a full UTC day window and only mature users.

**Hint:** Use EXISTS so several return events do not multiply users.

### Worked query

```sql
WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
), mature AS (
 SELECT * FROM customers WHERE tenant_id=:tenant
 AND signup_ts+(1+1)*86400<=:event_cutoff
), retained AS (
 SELECT c.*,EXISTS(SELECT 1 FROM known_events e WHERE e.customer_id=c.customer_id
 AND e.event_name='activity' AND e.event_ts>=c.signup_ts+1*86400
 AND e.event_ts<c.signup_ts+(1+1)*86400) returned FROM mature c
)
SELECT date(signup_ts,'unixepoch') cohort,COUNT(*) eligible_users,SUM(returned) returned_users,
 ROUND(100.0*SUM(returned)/COUNT(*),6) retention_pct FROM retained GROUP BY cohort ORDER BY cohort;
```

### Verified output

| cohort | eligible_users | returned_users | retention_pct |
| --- | --- | --- | --- |
| 2026-10-01 | 2 | 1 | 50.0 |
| 2026-10-02 | 2 | 2 | 100.0 |
| 2026-10-03 | 1 | 1 | 100.0 |
| 2026-10-04 | 1 | 1 | 100.0 |
| 2026-10-10 | 1 | 1 | 100.0 |

### Why it works

EXISTS reduces any number of qualifying return events to one retained flag. The maturity condition observes the full day-one interval, including its exclusive upper endpoint. The final group compares users within the same signup cohort.

**Common wrong answer:** A cohort needs its entire qualifying day observed, not merely the start of that day.

**Interview follow-up:** What is the policy for a signup timestamp outside midnight?

## Q19. A late D7 event revises retention

Compute D7 retention at initial and later knowledge cutoffs while holding the event cutoff fixed.

**Hint:** Cross two as-of settings with mature users; use a correlated EXISTS.

### Worked query

```sql
WITH cutoffs(label,asof) AS (VALUES('initial',:knowledge_cutoff),('revised',:later_knowledge)),
mature AS (SELECT * FROM customers WHERE tenant_id=:tenant AND signup_ts+8*86400<=:event_cutoff),
flags AS (
 SELECT k.label,c.customer_id,EXISTS(SELECT 1 FROM canonical_events e
 WHERE e.tenant_id=:tenant AND e.customer_id=c.customer_id AND e.event_name='activity'
 AND e.event_ts>=c.signup_ts+7*86400 AND e.event_ts<c.signup_ts+8*86400
 AND e.event_ts<:event_cutoff AND e.ingested_ts<k.asof) returned
 FROM cutoffs k CROSS JOIN mature c
)
SELECT label,COUNT(*) eligible_users,SUM(returned) returned_users,
 ROUND(100.0*SUM(returned)/COUNT(*),6) retention_pct FROM flags GROUP BY label ORDER BY label;
```

### Verified output

| label | eligible_users | returned_users | retention_pct |
| --- | --- | --- | --- |
| initial | 6 | 2 | 33.333333 |
| revised | 6 | 3 | 50.0 |

### Why it works

The set of mature users and behavioral cutoff remain fixed. Each receipt cutoff changes only the event knowledge visible for the return test. The late consistent event therefore changes historical retention without implying later behavior in the old window.

**Common wrong answer:** A revised historical result does not imply new behavior at the time of the report.

**Interview follow-up:** What conflict/retraction policy would a production event system require?

## Q20. Any return during days one through seven

For users with eight elapsed days observed, count any activity in [signup+1 day,signup+8 days).

**Hint:** State the bounded return window instead of calling it exact D7.

### Worked query

```sql
WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
), mature AS (
 SELECT * FROM customers WHERE tenant_id=:tenant AND signup_ts+8*86400<=:event_cutoff
), flags AS (
 SELECT c.customer_id,EXISTS(SELECT 1 FROM known_events e WHERE e.customer_id=c.customer_id
 AND e.event_name='activity' AND e.event_ts>=c.signup_ts+86400 AND e.event_ts<c.signup_ts+8*86400) returned FROM mature c
)
SELECT COUNT(*) eligible_users,SUM(returned) returned_users,
 ROUND(100.0*SUM(returned)/NULLIF(COUNT(*),0),6) retention_pct FROM flags;
```

### Verified output

| eligible_users | returned_users | retention_pct |
| --- | --- | --- |
| 6 | 6 | 100.0 |

### Why it works

This return set spans seven daily buckets beginning one day after signup. A user returning on day two qualifies even without a day-seven event. Keep that bounded definition separate from exact-day and unbounded rolling retention.

**Common wrong answer:** Any-week return and an exact-day return use different sets.

**Interview follow-up:** How would rolling retention from day seven onward differ?

## Q21. DAU and seven-day active users

For Oct 11, count distinct activity users that day and across Oct 5-11.

**Hint:** Count distinct customers over each interval, not sums of daily users.

### Worked query

```sql
WITH known_events AS (
 SELECT * FROM canonical_events WHERE tenant_id=:tenant
 AND event_ts<:event_cutoff AND ingested_ts<:knowledge_cutoff
)
SELECT COUNT(DISTINCT CASE WHEN event_ts>=unixepoch(:activity_day) AND event_ts<unixepoch(:activity_day,'+1 day') THEN customer_id END) dau,
 COUNT(DISTINCT CASE WHEN event_ts>=unixepoch(:activity_day,'-6 days') AND event_ts<unixepoch(:activity_day,'+1 day') THEN customer_id END) active_7d
FROM known_events WHERE event_name='activity';
```

### Verified output

| dau | active_7d |
| --- | --- |
| 2 | 6 |

### Why it works

Both measures count customer identities, not deliveries or events. A customer active on several days still contributes once to the seven-day set. Do not sum daily distinct counts to obtain that larger interval count.

**Common wrong answer:** Users can appear on several days; add events only when the metric is events.

**Interview follow-up:** How would an identity alias merge change the historical result?

## Q22. Repeat purchase among mature first purchasers

Find each customer first paid order across supplied history. Among first purchasers with seven days observed, count another paid order within that first seven-day interval.

**Hint:** Find first purchase before applying any October reporting restriction.

### Worked query

```sql
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
```

### Verified output

| mature_first_purchasers | repeat_purchasers | repeat_pct |
| --- | --- | --- |
| 4 | 2 | 50.0 |

### Why it works

The first purchase is determined over all supplied paid history before the event cutoff, not only October orders. The maturity filter gives every selected first purchaser the opportunity to repeat. Another order at the identical first timestamp is excluded by the stated strict inequality.

**Common wrong answer:** First in an extract is not necessarily first in history. Here first means first in supplied history; equal-time second orders are explicitly excluded.

**Interview follow-up:** How would you count another order at exactly the first order timestamp?

## Q23. Cart-level abandonment with a mature horizon

For carts with a full hour observed, count carts with a linked paid order in [created,created+1 hour), and abandoned carts.

**Hint:** Use EXISTS over the explicit cart link.

### Worked query

```sql
WITH flags AS (
 SELECT r.cart_id,EXISTS(SELECT 1 FROM orders o WHERE o.cart_id=r.cart_id
 AND o.customer_id=r.customer_id AND o.status='paid' AND o.ordered_ts>=r.created_ts AND o.ordered_ts<r.created_ts+3600) converted
 FROM carts r JOIN customers c USING(customer_id)
 WHERE c.tenant_id=:tenant AND r.created_ts+3600<=:event_cutoff
)
SELECT COUNT(*) mature_carts,SUM(converted) converted_carts,SUM(1-converted) abandoned_carts,
 ROUND(100.0*SUM(1-converted)/NULLIF(COUNT(*),0),6) abandonment_pct FROM flags;
```

### Verified output

| mature_carts | converted_carts | abandoned_carts | abandonment_pct |
| --- | --- | --- | --- |
| 4 | 2 | 2 | 50.0 |

### Why it works

The denominator is carts, so one customer can contribute more than one eligible cart. A paid order must reference the same cart and customer and fall inside its one-hour interval. The unfinished late cart is not labelled abandoned yet.

**Common wrong answer:** A later purchase does not satisfy a one-hour cart conversion; immature carts are excluded.

**Interview follow-up:** What if one order can legitimately satisfy multiple carts?

## Q24. Segment activation by signup-time plan

Report the Q17 funnel by plan effective at signup, preserving an Unmapped segment.

**Hint:** Reuse the same eligibility and ordered completion, then select historical dimension state.

### Worked query

```sql
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
```

### Verified output

| plan | eligible_users | completed_users | completion_pct |
| --- | --- | --- | --- |
| Unmapped | 2 | 1 | 50.0 |
| free | 3 | 1 | 33.333333 |
| paid | 1 | 0 | 0.0 |

### Why it works

The funnel eligibility and completion rule stay unchanged when adding segmentation. Plan selection is anchored to signup rather than the current plan or eventual order. Missing history becomes its own visible segment instead of dropping users.

**Common wrong answer:** An inner history join drops users; current-plan segmentation changes the original cohort definition.

**Interview follow-up:** Would weighting segment rates equally recover the overall rate?

## Practice checkpoint

- [ ] I can write these queries before reading the solutions.
- [ ] I can state the output grain and a counterexample to the tempting wrong answer.
- [ ] I can adapt one boundary or missingness rule and explain the changed result.

Return to the [roadmap](/docs/sql-interview) or continue with [consolidation and mocks](/docs/sql-interview/consolidation-and-mocks).
