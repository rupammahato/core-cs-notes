# Product and Analytics Casebook — Part 4: Metrics and Root-Cause Analysis

**C04–C06: distinguish a changed number from a demonstrated explanation.**

## Before the cases

A dashboard movement can arise from definitions, logging, late data, identity duplication, observation windows, population mixture or behavior. Start by making the comparison reproducible, then inspect the most discriminating breakdown.

The cases give complete synthetic aggregates with declared set relationships. Their arithmetic cannot inspect real event identities, labels or instrumentation. In a real investigation, source rows and provenance are part of the evidence.

Use the [SQL reconciliation chapter](/docs/sql-interview/reconciliation-and-query-plans) for executable grain/duplicate examples and [correlation and standardization](/docs/probability-statistics/correlation-and-regression) for the limits of descriptive adjustment.

<!-- BEGIN WORKED CASES -->

## C04. Checkout falls while every device rate is stable

Overall checkout completion falls. The release team wants to roll back immediately. Use the device evidence before diagnosing the release.

### Clarify the question

- Is the metric contract and checkout eligibility unchanged?
- Are the periods comparable and outcomes fully observed?
- Did traffic sources, devices or customer intent change?

### Frame the user and objective

Determine whether users are experiencing a regression, whether the aggregate changed through composition, and what additional evidence should guide an operational response.

### Evidence status and complete fixture inputs

Both periods contain invented complete device counts. Device-specific rates are unchanged, while the mobile share grows. This exactly explains the aggregate arithmetic in the supplied two-segment fixture; it does not prove why the mix changed or exclude all real regressions.

```json
{
  "before_mobile_users": 400,
  "before_mobile_completed": 240,
  "before_desktop_users": 600,
  "before_desktop_completed": 540,
  "after_mobile_users": 800,
  "after_mobile_completed": 480,
  "after_desktop_users": 200,
  "after_desktop_completed": 180
}
```

### Metric and decision contract

Completed eligible checkouts / eligible checkout starts in each fixed period. Show within-device rates, device weights and a standardized comparison using the earlier mixture. Keep errors, payment authorization and customer complaints as independent checks.

### Work the evidence

Decompose aggregate completion into segment weight times segment rate. Standardize the later rates to the earlier device mix. The apparent drop disappears under those fixed weights. Next inspect acquisition campaigns, device classification, population coverage and error trends rather than immediately calling the release defective.

Run `python examples/product-casebook/compute.py C04` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "before_overall_pct": 78.0,
  "after_overall_pct": 66.0,
  "after_standardized_to_before_mix_pct": 78.0,
  "observed_change_pp": -12.0
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Roll back on the aggregate alone: may remove a genuine issue quickly, but the fixture does not identify the release as the cause.
- Investigate the mix with segmented quality checks: targets the observed explanation while preserving a safety response to corroborated incidents.
- Optimize mobile checkout strategically: may be valuable because mobile has lower completion, but is a separate intervention hypothesis.

### Worked recommendation

Explain the composition result and investigate its source. Do not claim a device-level deterioration from these counts. Continue checking severe errors or user reports that could justify immediate action independently of the aggregate.

**What would change this recommendation:** A within-device error spike, changed event definition, missing transactions or a newly affected critical segment would require another explanation and potentially urgent mitigation.

### Engineering and architecture implications

Preserve device classification and metric-definition versions alongside events. Reconcile start/completion identities and use a reproducible aggregate query with explicit eligibility and time bounds.

Review the [related technical chapter](/docs/sql-interview/funnels-cohorts-and-retention) for implementation depth.

### Interviewer follow-ups

**F1. Does standardization prove no user was harmed?**

No. It explains the supplied aggregate using declared segments; smaller segments and unmeasured outcomes can still deteriorate.

**F2. Which weighting is correct?**

Current weights describe current users; fixed weights answer a comparable-mixture question. State the estimand rather than choosing whichever looks better.

**F3. Why not compare raw completion counts?**

Counts combine traffic volume and completion probability. Retain both numerator and denominator.

**F4. Can a release change traffic mix?**

Yes. The mix can itself be part of an intervention's effect, so descriptive standardization is not automatically a causal adjustment.

### Practice task

Restore the earlier device mixture and verify the aggregate change becomes zero.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C05. Reconcile purchase reports before explaining revenue

A dashboard disagrees with the order ledger, and raw server event value appears larger than order value. Investigate the data before telling a growth story.

### Clarify the question

- Which source is authoritative for the requested business quantity?
- Do event and ingestion cutoffs, identities, currencies and paid statuses match?
- Are the late client set and already received client set disjoint?

### Frame the user and objective

Produce a trustworthy purchase measure and a revision policy. Separate client-observed behavior, server order state and financial accounting rather than assuming they are interchangeable.

### Evidence status and complete fixture inputs

The fixture supplies aggregate set cardinalities, not individual event identities. It declares 200 late unique client receipts disjoint from 700 already received identities, and a server stream with 300 duplicate deliveries beyond 1,000 canonical orders. The calculation does not independently verify those identity declarations.

```json
{
  "server_paid_orders": 1000,
  "client_unique_received": 700,
  "late_unique": 200,
  "raw_server_events": 1300,
  "order_price_cents": 5000
}
```

### Metric and decision contract

For this exercise, canonical paid-order value equals one supplied fixed amount per distinct paid order. Client observation coverage is a separate reconciliation metric. Neither quantity is claimed to be recognized revenue or a complete settlement ledger.

### Work the evidence

Apply the late receipts, retain the unresolved gap and compare raw event multiplication with canonical order value. Inspect event IDs, delivery IDs, order state, receipt timestamps and producer versions on real source rows. A single missing browser event cannot by itself invalidate a paid server order.

Run `python examples/product-casebook/compute.py C05` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "client_after_late_receipts": 900,
  "still_unreconciled": 100,
  "duplicate_server_deliveries": 300,
  "naive_event_value_cents": 6500000,
  "canonical_order_value_cents": 5000000
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Use raw event value: easy but double-counts the declared duplicate server deliveries.
- Publish canonical order value with a client-coverage caveat: appropriate to the declared order measure, with remaining reconciliation work visible.
- Suppress every financial report until all client events arrive: avoids apparent disagreement but can discard authoritative business facts for an unrelated telemetry gap.

### Worked recommendation

Publish the clearly named order measure only after its source contract is validated, retain the client reconciliation discrepancy and investigate the remaining identities. Record when late data revises earlier reports. Do not fill the unresolved gap with invented purchases.

**What would change this recommendation:** If the canonical order extract is incomplete, paid status is wrong or amounts include unresolved currency/refund issues, withhold or qualify that total until the actual contract is repaired.

### Engineering and architecture implications

Keep business-event identity separate from delivery identity, make ingestion idempotent, retain receipt time and publish versioned materializations. Do not use a dashboard de-duplication trick as a replacement for a source policy.

Review the [related technical chapter](/docs/system-design/analytics-event-pipeline) for implementation depth.

### Interviewer follow-ups

**F1. Do these aggregates prove duplicate identities?**

No. They encode a supplied synthetic identity reconciliation. A real investigation needs source rows and a documented canonicalization policy.

**F2. Does every gap represent lost revenue?**

No. Client logging, order state and settlement describe different stages and sources.

**F3. Should missing client purchases become zero orders?**

No. Unknown observation coverage cannot erase known authoritative orders.

**F4. How do you explain a revised report?**

Hold the event period fixed, identify the new receipt cutoff and source version, and quantify what changed and remains unresolved.

### Practice task

Allow all remaining valid client receipts to arrive, then explain which duplicate-server-event problem remains unchanged.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C06. Search clicks rise while useful outcomes fall

A search redesign increases click-through. The team calls it successful, but fewer sessions reach a useful result. Choose an outcome and a next investigation.

### Clarify the question

- What user task defines a useful result?
- Are sessions and their observation windows comparable?
- Can one session create multiple clicks, and how is the supplied clicked-session count defined?

### Frame the user and objective

Help users complete their search task. Clicks can be a signal, but extra navigation caused by confusing results can increase clicks without increasing value.

### Evidence status and complete fixture inputs

The fixture has disjoint periods with 1,000 eligible sessions each. Clicks here mean sessions with at least one result click, and useful sessions are a subset of those clicked sessions. No randomized assignment or causal release effect is verified.

```json
{
  "sessions_per_period": 1000,
  "before_clicks": 300,
  "before_useful": 200,
  "after_clicks": 450,
  "after_useful": 180
}
```

### Metric and decision contract

Primary: useful-result sessions / eligible sessions. Diagnostic: clicked sessions / eligible sessions and useful sessions / clicked sessions. Guardrails include time to useful result, complaints, unsafe results and permission failures.

### Work the evidence

Read both whole-session and conditional metrics. The redesign has more clicked sessions but a lower useful-result rate and lower usefulness among clickers. Inspect query mix, empty results, ranking, result labeling and what happens after a click. A clicked-only comparison selects a population whose membership can change.

Run `python examples/product-casebook/compute.py C06` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "before_ctr_pct": 30.0,
  "after_ctr_pct": 45.0,
  "before_useful_per_session_pct": 20.0,
  "after_useful_per_session_pct": 18.0,
  "before_useful_per_click_pct": 66.666667,
  "after_useful_per_click_pct": 40.0
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Optimize CTR alone: gives a simple target but can reward confusing or sensational results.
- Evaluate useful task completion: closer to the user outcome, but needs defensible labels and a complete window.
- Run targeted query/task research first: can expose failure modes before a larger ranking experiment.

### Worked recommendation

Do not call the redesign successful from CTR. Verify the useful-result definition and investigate the changed journey. If that decline is credible, pause expansion and choose a focused intervention with a predeclared primary outcome.

**What would change this recommendation:** A corrected outcome label, a changed intended task or a previously missing population may alter the interpretation. A credible user-value signal is needed before promoting CTR to the objective.

### Engineering and architecture implications

Join query, impression, click and downstream outcome IDs; retain ranking/version context. Enforce document permissions before retrieval and display, and avoid logging sensitive query contents unnecessarily.

Review the [related technical chapter](/docs/system-design/search-autocomplete) for implementation depth.

### Interviewer follow-ups

**F1. Can fewer clicks be better?**

Yes. Users may find an answer directly or finish with less navigation. Judge the task, not a universal click target.

**F2. Is useful-per-click the primary metric?**

Not automatically. Its denominator changes with the treatment; the whole eligible-session outcome keeps the broader target visible.

**F3. How would you inspect quality?**

Sample representative tasks with a declared rubric, inspect failures and validate labels rather than accepting a click as proof.

**F4. Does the case establish causality?**

No. It is a descriptive contrast that motivates investigation and a suitable evaluation design.

### Practice task

Explain why a higher clicked-session rate can coexist with a lower useful-session rate without any arithmetic contradiction.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

<!-- END WORKED CASES -->

## Synthesis

Give the metric movement, the demonstrated decomposition and the remaining uncertainty as separate statements. A mix explanation can be arithmetically complete for supplied cells without establishing a real release's causal effect. A trusted order measure can coexist with incomplete client observation.

Continue with [Growth, Activation and Retention](/docs/product-casebook/growth-activation-and-retention).
