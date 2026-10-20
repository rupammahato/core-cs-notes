# Product and Analytics Casebook — Part 5: Growth, Activation and Retention

**C07–C09: improve useful behavior without changing the question through the denominator.**

## Before the cases

Activation is a product-specific first-value hypothesis that needs an observable definition. Retention needs a behavior, cohort anchor and qualifying return window. Messaging must account for user attention and preferences alongside near-term conversion.

The largest funnel loss is a place to investigate, not an automatic feature priority. Newly acquired users may not resemble the users who progressed earlier. Reusing observed downstream conversion in a forecast is an explicit assumption about that change in population.

Connect these cases with [product analytics](/docs/product-analytics/product-analytics-experiments), [SQL cohorts](/docs/sql-interview/funnels-cohorts-and-retention) and [hypothesis-testing foundations](/docs/probability-statistics/hypothesis-tests-and-experiments). The book does not verify real randomization or campaign incrementality from aggregate counts.

<!-- BEGIN WORKED CASES -->

## C07. Find an activation bottleneck for an AI assistant

An AI document assistant has many signups but few useful first answers. Decide where to investigate and estimate a conditional opportunity.

### Clarify the question

- What observable outcome counts as useful first value?
- Are all users eligible and given a full activation window?
- Are the funnel stages nested and ordered under one identity rule?

### Frame the user and objective

Help a new eligible user reach a grounded, usable first answer from an allowed document. Uploading or generating an answer is intermediate behavior, not proof of value.

### Evidence status and complete fixture inputs

The invented funnel has 1,000 mature eligible users, followed by 700 starters, 400 uploaders, 300 answer recipients and 180 useful-answer users. The forecast assumes 100 extra uploaders and unchanged downstream conversion; neither intervention response nor downstream invariance is verified.

```json
{
  "eligible_mature": 1000,
  "started": 700,
  "uploaded": 400,
  "answered": 300,
  "useful": 180,
  "assumed_extra_uploads": 100
}
```

### Metric and decision contract

Primary: mature eligible users receiving a rubric-qualified first useful answer / mature eligible new users. Segment by document compatibility and user job. Guardrails: authorization, ingestion failures, unsupported answers, cost and task time.

### Work the evidence

Compute each conditional stage rate and the whole-cohort activation rate. The start-to-upload transition has the lowest conditional rate, but investigate its causes and user value before calling it the best investment. Some starters may intentionally use sample content or lack a suitable document. The forecast reuses the observed useful-per-uploader rate, making its invariance assumption visible.

Run `python examples/product-casebook/compute.py C07` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "stage_conversion_pct": [
    70.0,
    57.142857,
    75.0,
    60.0
  ],
  "useful_activation_pct": 18.0,
  "scenario_extra_useful": 45.0,
  "scenario_lift_pp": 4.5
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Improve document upload and error recovery: targets a visible transition, but may not address lack of a useful task.
- Offer a permitted sample task: can teach the experience, but may increase activity without real user value.
- Improve answer grounding: helps later-stage quality, but reaches fewer users if ingestion remains blocked.

### Worked recommendation

Observe and segment the upload transition, then test a narrow recovery or task-guidance intervention if it addresses a real blocker. Keep useful first value as the primary outcome and treat the computed opportunity as a scenario.

**What would change this recommendation:** If nonuploaders lack a real task or the main failure is unsupported answers, prioritize discovery or grounding rather than optimizing a stage count mechanically.

### Engineering and architecture implications

Model upload acceptance, ingestion completion and answer readiness as separate states. Use owned jobs, retry-safe ingestion and versioned document permissions; publish failure states the UI can explain.

Review the [related technical chapter](/docs/system-design/multi-tenant-rag) for implementation depth.

### Interviewer follow-ups

**F1. Does the largest drop define the best feature?**

No. Opportunity also depends on user need, addressability, effort, downstream quality and how much of the drop is intentional.

**F2. Why use a mature cohort?**

Every included user should have the defined chance to achieve the outcome before being counted as a nonconverter.

**F3. What does unchanged downstream conversion assume?**

That extra uploaders behave like current uploaders and the intervention does not change later stages. Selection can invalidate that forecast.

**F4. What would a useful activation event contain?**

A stable user/document/task identity, outcome timestamp and rubric/version reference, while keeping sensitive answer text out of routine telemetry.

### Practice task

Set the entire eligible funnel to empty and explain why its conversion rate is unknown rather than zero.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C08. Retention falls because the observation window is unfinished

New-cohort D7 retention appears much worse than the previous cohort. Investigate maturity and a later receipt update before proposing reactivation campaigns.

### Clarify the question

- Does D7 mean an exact day or any return by day seven?
- Which users have a fully observed qualifying interval?
- Which event-time and receipt-time cutoffs define each report?

### Frame the user and objective

Compare a stable return behavior over comparable opportunities to return. Distinguish behavior from the reporting system's current knowledge of it.

### Evidence status and complete fixture inputs

The fixture declares exact-day D7 and completed UTC cohort-day intervals. Only 600 of 1,000 new signups are mature. The 180 known returns belong to that mature subset. Thirty later receipts are additional unique qualifying returns from the same mature users, with event times inside the original D7 windows.

```json
{
  "previous_signups": 1000,
  "previous_mature": 1000,
  "previous_returns": 300,
  "new_signups": 1000,
  "new_mature": 600,
  "new_returns": 180,
  "late_valid_returns": 30
}
```

### Metric and decision contract

Known qualifying unique returners / fully mature eligible users, under a named event period and knowledge cutoff. Report immature users separately and version revised historical results.

### Work the evidence

Compare the naive all-signup denominator with the mature denominator. The mature comparison initially matches the earlier cohort. Later knowledge revises the new mature rate upward without introducing behavior outside the original return period. Investigate late-delivery mechanisms and cohort definitions before explaining the report as changed loyalty.

Run `python examples/product-casebook/compute.py C08` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "previous_mature_retention_pct": 30.0,
  "new_naive_all_signup_pct": 18.0,
  "new_mature_retention_pct": 30.0,
  "new_revised_mature_retention_pct": 35.0,
  "immature_signups": 400
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Launch a campaign based on the naive decline: may spend money on a reporting artifact.
- Fix comparability and publication labels: improves interpretation while preserving visibility of current incomplete cohorts.
- Run targeted retention research after the corrected comparison: useful if a genuine behavioral problem remains.

### Worked recommendation

Correct the denominator, label maturity and cutoffs, then examine comparable segments. Publish the late-data revision transparently. The fixture does not justify a causal loyalty narrative in either direction.

**What would change this recommendation:** A fully mature comparable cohort with a persistent within-segment decline, corroborating task failures or a changed return definition would support a different investigation.

### Engineering and architecture implications

Retain event and ingestion time, canonical user/event identity and cohort anchors. Version historical aggregates and define the policy for late events, conflicts and retractions.

Review the [related technical chapter](/docs/sql-interview/funnels-cohorts-and-retention) for implementation depth.

### Interviewer follow-ups

**F1. Why not count immature users as not retained?**

They have not had the same defined opportunity to generate the outcome.

**F2. Did the later report create new historical behavior?**

No. The exercise adds knowledge of behavior already inside the fixed qualifying windows.

**F3. Can D7 rates across tools differ?**

Yes, if exact-day, rolling, calendar, timezone, identity or eligibility definitions differ.

**F4. What should the dashboard display?**

Definition, eligible mature count, immature count, event period, knowledge cutoff and whether a historical value was revised.

### Practice task

Make the new cohort fully mature with the same return rate, then explain which apparent discrepancy disappears.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C09. Reminder conversions improve but the message guardrail fails

A reminder test appears to increase conversions. Unsubscribes also rise. Decide what to recommend under the supplied experiment contract.

### Clarify the question

- Was assignment valid, and are the users and outcome windows comparable?
- Was the unsubscribe guardrail chosen before the result?
- Which costs and longer-term effects are outside the short-window model?

### Frame the user and objective

Help eligible users complete a task while respecting attention and communication preferences. Conversions and short-term contribution do not capture every user cost.

### Evidence status and complete fixture inputs

Counts are synthetic aggregates from a hypothetical assigned comparison; the lab does not verify assignment or inference assumptions. The case supplies a maximum one-percentage-point unsubscribe increase. Incremental contribution assumes a fixed value per additional conversion and excludes longer-term effects.

```json
{
  "control_users": 1000,
  "control_converted": 200,
  "control_unsubscribed": 20,
  "treatment_users": 1000,
  "treatment_converted": 240,
  "treatment_unsubscribed": 50,
  "delivery_cost_cents": 5000,
  "contribution_per_conversion_cents": 500,
  "allowed_unsubscribe_increase_pp": 1
}
```

### Metric and decision contract

Primary: conversion among assigned eligible users in a complete window. Guardrail: treatment-minus-control unsubscribe percentage points. Cost: supplied delivery spending divided by standardized extra conversions when positive; avoid calling it an acquisition CAC.

### Work the evidence

Compare rates rather than raw counts, standardize the incremental count to treatment population size and retain the unsubscribe difference. The favorable contribution scenario and conversion contrast coexist with a failed predeclared guardrail. Inspect message frequency, relevance and consent state before choosing another experiment.

Run `python examples/product-casebook/compute.py C09` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "conversion_difference_pp": 4.0,
  "standardized_incremental_conversions": 40.0,
  "scenario_incremental_contribution_cents": 15000.0,
  "cost_per_incremental_conversion_cents": 125.0,
  "unsubscribe_increase_pp": 3.0,
  "supplied_guardrail_passed": false
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Expand immediately: exploits the apparent short-run upside but violates the supplied attention guardrail.
- Reduce frequency or target a legitimate task context: may preserve value with less burden, requiring a new valid evaluation.
- Stop reminders entirely: avoids this harm but could discard a useful intervention for a better-defined population.

### Worked recommendation

Hold broad expansion under the supplied rule. Investigate and redesign the message policy, then evaluate a predeclared variant with suitable uncertainty and longer-term checks. A passed arithmetic gate would still not certify actual experiment validity.

**What would change this recommendation:** Corrected unsubscribe classification or an explicitly reconsidered business policy can change the decision, but retroactively moving a threshold because a result looks attractive weakens the original claim.

### Engineering and architecture implications

Record stable assignment, eligibility and send identity, enforce preference/frequency limits and make sends idempotent. Join delivery, conversion and unsubscribe outcomes without leaking message content.

Review the [related technical chapter](/docs/system-design/notifications-webhooks) for implementation depth.

### Interviewer follow-ups

**F1. Does positive contribution settle the decision?**

No. The selected cost model omits attention, trust and longer-term effects, and the declared guardrail fails.

**F2. Why standardize extra conversions?**

Arm sizes can differ. Apply the control rate to the treatment population before subtracting observed treatment conversions.

**F3. Is a failed guardrail proof of causal harm?**

Not from these aggregates alone. It triggers the supplied decision policy while assignment, uncertainty and measurement still need validation.

**F4. What changes at the exact allowed boundary?**

The supplied rule accepts an increase at or below one percentage point, as the changed-scenario check demonstrates.

### Practice task

Move treatment unsubscribes to the exact declared boundary and explain which validity questions remain.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

<!-- END WORKED CASES -->

## Synthesis

Show the useful outcome, complete observation opportunity and customer costs. A revised historical rate can reflect later knowledge; a conversion gain can fail an attention guardrail. Keep these interpretations visible when explaining what to do next.

Continue with [Pricing and Business Models](/docs/product-casebook/pricing-and-business-models).
