# Product and Analytics Casebook — Part 7: Marketplaces and Operations

**C13–C15: local compatibility, capacity and quality determine useful throughput.**

## Before the cases

An operation can look healthy in a global total while failing in the time, geography, skill or risk category users actually need. Follow the flow from demand through compatible service and useful completion. Keep the work unit and resource assumptions explicit.

Capacity models distinguish input rate, processing capacity and accumulating work. The support example is a constant-rate fluid calculation; it does not implement a stochastic queue or infer a real waiting-time distribution. MIT's service-operations materials provide the broader capacity/flow context. [MIT service operations lecture notes](https://ocw.mit.edu/courses/15-768-management-of-services-concepts-design-and-delivery-fall-2010/eadc63624af3de30d642f9463a1ed612_MIT15_768F10_lec09-10.pdf).

For classifier-related decisions, [conditional probability](/docs/probability-statistics/conditional-probability-and-bayes) explains why a better precision denominator need not mean fewer missed positives. Real policy decisions also need label, harm, capacity and intervention evidence.

<!-- BEGIN WORKED CASES -->

## C13. Marketplace matching is more than total supply

A local services marketplace completes only 40 of 100 requests. The team wants twenty more seller slots. Decide where to investigate and how to assess liquidity.

### Clarify the question

- Which location, time and skill constraints define a compatible match?
- Are slots genuinely available and exclusive within the same request window?
- What happens between a match and a completed service?

### Frame the user and objective

Help buyers receive a suitable completed service while giving sellers worthwhile, reliable work. Total registrations are weaker than compatible availability in the relevant market cell.

### Evidence status and complete fixture inputs

The fixture supplies three disjoint zones, one-use slots, compatible match counts and total completed matches. It does not include the compatibility graph or actual seller response histories. Added slots are a capacity scenario, not guaranteed matches.

```json
{
  "zones": [
    {
      "id": "A",
      "requests": 50,
      "slots": 40,
      "matches": 35
    },
    {
      "id": "B",
      "requests": 30,
      "slots": 15,
      "matches": 8
    },
    {
      "id": "C",
      "requests": 20,
      "slots": 5,
      "matches": 2
    }
  ],
  "completed": 40,
  "assumed_added_slots": 20
}
```

### Metric and decision contract

Match rate = matched requests / eligible requests; fulfillment = completed requests / eligible requests; post-match completion = completed / matched. Segment by geography, time and job type. Track cancellation, wait time, quality and seller economics.

### Work the evidence

Inspect the unmatched requests by zone, available capacity and the post-match losses. Aggregate supply can mask local shortages and incompatible availability. The extra-slot ceiling assumes compatible allocation and successful completion; it is only a capacity upper bound. Investigate why existing slots do not match before buying undifferentiated supply.

Run `python examples/product-casebook/compute.py C13` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "requests": 100,
  "available_slots": 60,
  "matches": 45,
  "completed": 40,
  "match_rate_pct": 45.0,
  "fulfillment_rate_pct": 40.0,
  "completion_given_match_pct": 88.888889,
  "unmatched_by_zone": {
    "A": 15,
    "B": 22,
    "C": 18
  },
  "capacity_only_ceiling_after_added_slots": 80
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Recruit sellers everywhere: increases a headline total but may miss the constrained cells.
- Focus compatible supply in a bounded market cell: can improve local usefulness, but narrows reach initially.
- Improve response and post-match reliability: can use existing supply better, but may not solve genuine capacity gaps.

### Worked recommendation

Choose a specific constrained cell using demand, compatibility and seller evidence, then evaluate reliable completed service there. Address cancellations separately. Make the added-capacity ceiling conditional rather than a forecast.

**What would change this recommendation:** Evidence that available slots are unusable, prices suppress acceptance or post-match failures dominate would change the intervention and target cell.

### Engineering and architecture implications

Model availability and booking separately, reserve a slot atomically and expire abandoned holds. Publish request, match, acceptance and completion identities without counting retries as new demand.

Review the [related technical chapter](/docs/system-design/booking-reservations) for implementation depth.

### Interviewer follow-ups

**F1. What is marketplace liquidity here?**

The ability to reach a suitable transaction in a defined cell and time window, measured through matching and reliable completion rather than total signups.

**F2. Does more supply guarantee more fulfillment?**

No. Skills, time, location, price, response and post-match reliability can prevent additional slots from helping.

**F3. Why track both sides?**

Buyer convenience can impose low utilization or poor economics on sellers, making the apparent gain unsustainable.

**F4. What data would improve the diagnosis?**

Compatible candidate sets, offer/response times, rejection reasons, prices, hold expirations and final outcome evidence.

### Practice task

Explain what must be true for the added-slot capacity ceiling to become realized completed service.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C14. A support backlog grows faster than the team can clear it

Three agents each process fifteen tickets per hour while sixty arrive per hour. Propose a response without promising an unjustified queue wait time.

### Clarify the question

- Are arrival and service rates stable averages or deterministic assumptions?
- Do ticket types, reopens and priority classes change the work?
- What happens to arrivals after the busy period?

### Frame the user and objective

Restore timely, useful support while protecting answer quality and urgent cases. A lower ticket count can hide deflection failures or unresolved work.

### Evidence status and complete fixture inputs

This is a deterministic fluid-capacity scenario over four busy hours, starting with zero backlog. It has constant processing rate, no abandonment, no reopens and no routing loss. It is not a stochastic queue simulation or a measured response-time forecast.

```json
{
  "agents": 3,
  "service_per_agent_per_hour": 15,
  "arrivals_per_hour": 60,
  "busy_hours": 4,
  "target_utilization": 0.8,
  "later_arrivals_per_hour": 30
}
```

### Metric and decision contract

Track incoming workload, completed useful resolutions, backlog age by priority and quality/reopen guardrails. The load/capacity ratio can exceed one during overload; it is not a probability. Staffing targets use the supplied 80% utilization policy.

### Work the evidence

Calculate total capacity, net work accumulation and staffing needed for the declared target. The later clearance estimate assumes arrivals fall to the supplied lower rate while capacity stays unchanged. At no spare capacity, a finite clearance time is not available. Arrival/service variability would need another model for waiting-time predictions.

Run `python examples/product-casebook/compute.py C14` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "capacity_per_hour": 45,
  "load_to_capacity": 1.333333,
  "fluid_backlog_after_busy_period": 60,
  "agents_for_target_utilization": 5,
  "fluid_clearance_hours_at_later_arrival_rate": 4.0
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Add or temporarily reassign trained capacity: can address the deficit quickly, with staffing and quality constraints.
- Remove a recurring product defect: reduces demand sustainably if the cause is real, but takes investigation and delivery.
- Automate a constrained support task: may help throughput, but needs escalation, correctness and reopen measurement.

### Worked recommendation

Protect urgent cases, stabilize capacity and investigate top recurring causes. Use the fluid calculation to explain the capacity deficit, then validate actual rates and variability before committing staffing or response-time promises.

**What would change this recommendation:** Higher complexity, reopens, interrupted service or continuing peak arrivals would invalidate the simple clearance estimate. A genuine product fix can change demand more effectively than staffing alone.

### Engineering and architecture implications

Use a durable owned queue with priorities, retry-safe assignment and clear resolution states. Track enqueue, first response and final resolution separately; do not discard work to improve backlog metrics.

Review the [related technical chapter](/docs/system-design/job-scheduler-workers) for implementation depth.

### Interviewer follow-ups

**F1. Can load/capacity exceed 100%?**

Yes as a load ratio; it signals demand exceeds nominal capacity. It cannot describe a stable server's busy-time probability above one.

**F2. Can Little's law predict this overloaded transient wait?**

Not by substituting unstable backlog counts into a steady-state interpretation. State the flow boundary and stability conditions before using it.

**F3. Why target spare capacity?**

Real arrivals and service work vary, so operating at nominal full load can create poor waits. The supplied target is a policy assumption, not a universal optimum.

**F4. Is ticket deflection always success?**

No. Users may abandon the service or return with unresolved work; check useful resolution and escalation outcomes.

### Practice task

Set later arrivals equal to capacity and explain why the existing backlog does not clear in finite time in this model.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C15. Fraud precision improves while more fraud is missed

A new alert threshold increases precision and cuts review volume, but catches fewer fraudulent transactions. Compare the trade-offs before selecting a policy.

### Clarify the question

- How complete and timely are fraud labels?
- Can the review team handle both proposed workloads, and what happens after a true alert?
- Which false-positive friction and missed-loss costs are not modeled?

### Frame the user and objective

Reduce harmful transactions while preserving legitimate users' access and a workable review process. A threshold optimizes a chosen loss/constraint problem, rather than precision alone.

### Evidence status and complete fixture inputs

The invented labeled population contains 200 fraud cases. All old and new alerts are assumed reviewed in the scenario. Each caught fraud is assumed to avert the same supplied loss; review cost is fixed. The figures do not verify real prevention or include false-positive user friction.

```json
{
  "actual_fraud": 200,
  "old_alerts": 1000,
  "old_true_alerts": 100,
  "new_alerts": 500,
  "new_true_alerts": 90,
  "review_cost_cents": 20,
  "assumed_prevented_loss_per_caught_cents": 10000
}
```

### Metric and decision contract

Report precision, recall, missed fraud, review workload and the explicitly simplified prevented-loss-minus-review model. Evaluate on a relevant mature label window and retain appeal and legitimate-user impact measures.

### Work the evidence

The new policy produces more precise alerts but lower recall. Under the stated loss assumptions, saved review expense does not offset the extra missed-loss opportunity. That result is a sensitivity example, not a deployment recommendation: real fraud amounts, delayed labels, interventions and customer harm can change the objective.

Run `python examples/product-casebook/compute.py C15` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "old": {
    "precision_pct": 10.0,
    "recall_pct": 50.0,
    "missed_fraud": 100,
    "modeled_prevention_minus_review_cents": 980000
  },
  "new": {
    "precision_pct": 18.0,
    "recall_pct": 45.0,
    "missed_fraud": 110,
    "modeled_prevention_minus_review_cents": 890000
  }
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Choose the new threshold for precision: reduces workload but misses more supplied fraud cases.
- Keep the old threshold under the scenario model: preserves more catches, but may impose unmodeled legitimate-user costs.
- Use risk tiers and constrained review: can match treatment to capacity and harm, with additional calibration and operational complexity.

### Worked recommendation

State the trade-off and request the missing harm, loss distribution, intervention and capacity evidence. Test candidate policies with a declared objective and review safeguards. Do not select a real threshold from this synthetic uniform-loss model.

**What would change this recommendation:** Different loss amounts, false-positive costs, review capacity or incomplete labels can reverse the modeled ordering. A true alert that does not actually prevent loss also breaks the scenario assumption.

### Engineering and architecture implications

Version scores and threshold policies, keep review decisions auditable and restrict access to sensitive evidence. Separate prediction, intervention and eventual label so delayed outcomes do not masquerade as immediate ground truth.

Review the [related technical chapter](/docs/resume-skills/api-security-authorization-multi-tenancy) for implementation depth.

### Interviewer follow-ups

**F1. Why is precision insufficient?**

It conditions on alerts and ignores missed positives. Recall, workload and harm determine whether the operating point is useful.

**F2. Does a true alert equal prevented fraud?**

No. The scenario assumes a fully effective intervention; a real causal prevention claim needs evidence about what action changed the outcome.

**F3. What changes under review capacity limits?**

The assumption that all alerts are reviewed may fail; ranking, prioritization and treatment effects must enter the model.

**F4. How would you handle delayed labels?**

Use mature outcome windows, track label versions and account for unlabeled observations rather than treating all unknowns as legitimate.

### Practice task

Explain which unmodeled legitimate-user cost could make the policy ranking different from the supplied uniform-loss arithmetic.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

<!-- END WORKED CASES -->

## Synthesis

Compatibility and reliable completion matter more than total listings; spare capacity matters more than a staffing count; precision, recall and harm matter more than one classifier score. The calculations expose a trade-off while leaving its real policy choice conditional on the missing evidence.

Continue with [Experiments, AI and Launch Decisions](/docs/product-casebook/experiments-ai-and-launch-decisions).
