# Product and Analytics Casebook — Part 8: Experiments, AI and Launch Decisions

**C16–C18: favorable averages do not replace trustworthy evidence and critical requirements.**

## Before the cases

Sample-ratio mismatch is a diagnostic comparing observed allocation with the configured experiment ratio. It can expose problems in assignment, eligibility, instrumentation or analysis, but does not identify a unique cause. C16's threshold and arithmetic are local teaching inputs. [Microsoft Research: diagnosing SRM](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/).

AI evaluation should cover the intended task, representative and challenging contexts, and relevant failures. NIST's generative-AI profile gives a risk-management and evaluation context; C17's particular label rubric and permission gate are authored fixture policies, not a claim to implement that framework or certify a model. [NIST Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence).

Canaries limit release exposure and require meaningful evaluation and recovery behavior. Error-budget policies make reliability trade-offs explicit. C18 uses a simplified request-based ratio and a supplied canary gate, rather than reproducing Google's exact example policy or implementing a multiwindow alert. [Google SRE: canarying](https://sre.google/workbook/canarying-releases/), [example error-budget policy](https://sre.google/workbook/error-budget-policy/).

<!-- BEGIN WORKED CASES -->

## C16. An attractive conversion lift fails the assignment check

A nominal 50/50 experiment has 1,100 control assignments and 900 treatment assignments. Treatment conversion appears higher. Decide whether to use the lift.

### Clarify the question

- What allocation was actually configured for this experiment version?
- Are these assignment counts or post-treatment exposed users?
- Were any eligibility, bot or logging filters applied differently?

### Frame the user and objective

Make an experiment decision from trustworthy assignment and outcomes. A strong-looking metric cannot compensate for a broken or unexplained analysis population.

### Evidence status and complete fixture inputs

The fixture gives synthetic aggregate assignments and conversions, but verifies no actual randomization, deduplication or stopping plan. The two-category chi-square SRM calculation is asymptotic. The supplied diagnostic threshold is 0.001, not a universal standard.

```json
{
  "control_assigned": 1100,
  "control_converted": 220,
  "treatment_assigned": 900,
  "treatment_converted": 225,
  "planned_treatment_share": 0.5,
  "srm_threshold": 0.001
}
```

### Metric and decision contract

SRM compares observed assignment counts with configured allocation. Conversion is converted assigned users / eligible assigned users under the declared analysis. Passing an SRM check does not prove every other experimental assumption.

### Work the evidence

Calculate the raw observed conversion difference and SRM diagnostic separately. The allocation discrepancy fails the supplied gate, so investigate assignment versioning, eligibility, logging and post-treatment filtering before interpreting the effect. If the actual configured treatment share were 45%, these counts would match that allocation; do not substitute an allocation just because it fits.

Run `python examples/product-casebook/compute.py C16` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "observed_conversion_difference_pp": 5.0,
  "srm_chi_square": 20.0,
  "srm_asymptotic_p": 8e-06,
  "supplied_srm_gate_passed": false,
  "assignment_verified": false
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Ship because conversion is higher: ignores a failed trustworthiness diagnostic.
- Repair the population or instrumentation and rerun the planned analysis: preserves validity, with time and opportunity costs.
- Manually delete users to equalize groups: produces an attractive count balance without repairing the underlying design.

### Worked recommendation

Hold causal interpretation and expansion until the discrepancy is explained with source evidence. Preserve the original assignment record and configuration. After repair, apply the appropriate planned analysis and uncertainty rather than reusing an unqualified lift.

**What would change this recommendation:** A verified non-50/50 configured allocation or a reconciled logging defect can change the SRM assessment. It does not, by itself, verify outcomes, independence, stopping or guardrails.

### Engineering and architecture implications

Store immutable assignment/version identity, deterministic eligibility rules and a separate exposure stream. Join outcomes to the declared assignment population and monitor instrumentation changes.

Review the [related technical chapter](/docs/probability-statistics/hypothesis-tests-and-experiments) for implementation depth.

### Interviewer follow-ups

**F1. Does balanced assignment prove a valid experiment?**

No. Contamination, outcome mismeasurement, dependence or improper stopping can remain.

**F2. Why not analyze only exposed users?**

Exposure may be affected by treatment, so conditioning on it can change comparability. A triggered analysis needs its own valid definition.

**F3. Does SRM identify the root cause?**

No. It flags a discrepancy that can arise at assignment, eligibility, logging or analysis stages.

**F4. What if 45% treatment was truly configured?**

The supplied counts then match allocation, and this diagnostic passes. Verify configuration independently rather than choosing it retrospectively.

### Practice task

Change only the planned allocation to the verified hypothetical 45% and explain why assignment_verified still stays false in the offline fixture.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C17. An AI assistant answers more questions but leaks permissioned content

An AI candidate answers more benchmark questions and has more grounded-correct answers overall. It also has one supplied permission failure. Decide how to evaluate and release it.

### Clarify the question

- What questions, permission contexts and user tasks does the benchmark represent?
- Who labeled grounded correctness, and how were disagreements handled?
- Are refusals, unsupported answers and unauthorized disclosures tracked separately?

### Frame the user and objective

Deliver useful permitted answers with acceptable cost and reliability. More answered questions is not sufficient if access boundaries fail.

### Evidence status and complete fixture inputs

The benchmark has 100 invented questions with supplied answered and grounded-correct counts for each version. Labels and permission failures are fixtures, not an executed model evaluation. The candidate's total cost is supplied; no provider call, real document or sensitive content is used.

```json
{
  "questions": 100,
  "old_answered": 90,
  "old_grounded_correct": 72,
  "new_answered": 95,
  "new_grounded_correct": 76,
  "old_permission_failures": 0,
  "new_permission_failures": 1,
  "new_total_cost_cents": 1800
}
```

### Metric and decision contract

Report grounded-correct / all questions alongside grounded-correct / answered. Keep permission failures as a separate critical gate under this case's policy. Cost per grounded-correct outcome uses all supplied candidate cost, including unsuccessful answers.

### Work the evidence

Conditional correctness stays the same while answer coverage and whole-benchmark grounded correctness rise. The permission failure still blocks the candidate under the supplied gate. Inspect retrieval authorization, caching, document identity and output handling before further rollout. Average quality cannot cancel a specific access-control failure.

Run `python examples/product-casebook/compute.py C17` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "old_conditional_grounded_correct_pct": 80.0,
  "new_conditional_grounded_correct_pct": 80.0,
  "old_all_question_grounded_correct_pct": 72.0,
  "new_all_question_grounded_correct_pct": 76.0,
  "new_cost_per_grounded_correct_cents": 23.684211,
  "supplied_permission_gate_passed": false
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Launch on overall quality alone: exploits broader answers but violates the supplied permission gate.
- Repair and retest the access boundary: addresses the critical issue while preserving a candidate for future evaluation.
- Restrict to a verified lower-risk scope: can reduce exposure only if the restriction is real and its permission behavior is demonstrated.

### Worked recommendation

Hold the candidate, isolate the failing permission path and expand the evaluation to relevant adversarial and normal contexts. Reevaluate task usefulness, coverage, cost and uncertainty after repair. Do not claim actual safety from the offline arithmetic.

**What would change this recommendation:** Verified corrected permissions and representative evaluation can support another release review. A relabeled quality score cannot substitute for proving the access boundary works.

### Engineering and architecture implications

Apply authorization before retrieval, partition caches and indexes by the actual access model, propagate document versions and recheck permissions at answer delivery where needed. Log references and policy decisions without retaining sensitive content indiscriminately.

Review the [related technical chapter](/docs/system-design/multi-tenant-rag) for implementation depth.

### Interviewer follow-ups

**F1. Why show both denominators?**

Answered-only quality can hide refusals or selective answering. All-question usefulness retains the full intended task population.

**F2. Does grounding guarantee permission?**

No. An answer can be well supported by a document the requester is not allowed to access.

**F3. Can one failure matter despite better average quality?**

Yes under this critical-gate policy. User harm and access requirements are not interchangeable with a mean quality score.

**F4. What is verified by the example?**

Arithmetic over supplied labels and the declared gate, not actual model behavior, label validity or authorization enforcement.

### Practice task

Describe a test plan that could challenge the supplied permission result without simply reclassifying it as a quality issue.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C18. A canary harms users while the combined SLO still looks acceptable

A canary produces more bad requests, but the pooled window is at the allowed error budget. Decide whether to expand the release.

### Clarify the question

- What counts as bad, and can errors and slow requests overlap?
- Are the previous and canary request batches disjoint with comparable definitions?
- What canary-specific stop rule and rollback owner were declared?

### Frame the user and objective

Assess the new version's reliability for its exposed users, while retaining a correct overall service measure. A large healthy denominator must not hide a failing canary.

### Evidence status and complete fixture inputs

The fixture declares disjoint earlier and canary request batches. In the canary, five requests belong to both error and slow sets. The SLO is 99% good requests, and the illustrative canary stop rule triggers above two times its request-based budget. No service or deployment is actually run.

```json
{
  "previous_requests": 10000,
  "previous_bad": 80,
  "canary_requests": 1000,
  "canary_error": 20,
  "canary_slow": 15,
  "canary_both": 5,
  "slo_good_share": 0.99,
  "canary_burn_stop_above": 2
}
```

### Metric and decision contract

Bad is the union of error and slow requests. Budget burn here is observed bad requests / allowed bad requests for each batch, not a time-normalized alerting burn-rate implementation. Compare canary and pooled values separately.

### Work the evidence

Subtract overlap before counting bad requests. The canary consumes three times its local allowance, while pooling it with the healthier earlier batch gives a combined ratio of one. Under the supplied stop rule, the canary fails even though the combined result does not exceed its allowance. Investigate version-specific failures and segment exposure.

Run `python examples/product-casebook/compute.py C18` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "canary_bad_unique_requests": 30,
  "canary_good_pct": 97.0,
  "previous_budget_burn_ratio": 0.8,
  "canary_budget_burn_ratio": 3.0,
  "combined_budget_burn_ratio": 1.0,
  "supplied_canary_gate_passed": false
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Expand on the pooled metric: hides the canary's local harm behind earlier traffic.
- Pause and roll back the canary under the declared rule: contains exposure while evidence is inspected.
- Continue only a narrowly justified diagnostic slice: may help investigation but requires explicit risk ownership and a separate permitted policy.

### Worked recommendation

Do not expand. Apply the declared canary response, preserve diagnostic evidence and verify rollback behavior. Resume review only after a cause and fix are tested under the relevant metrics; this case does not authorize any real deployment action.

**What would change this recommendation:** A proven metric-definition error or corrected request identity can change the calculation. A more favorable pooled denominator does not explain away the canary's supplied failures.

### Engineering and architecture implications

Use version-tagged metrics, bounded traffic allocation, compatibility-aware rollback and explicit ownership. Check side effects, in-flight jobs and schema compatibility before assuming that turning off a flag reverses every change.

Review the [related technical chapter](/docs/resume-skills/git-ci-cd-testing-observability-performance) for implementation depth.

### Interviewer follow-ups

**F1. Why subtract overlap?**

The SLI counts unique bad requests, and one request can be both slow and an error.

**F2. Is this the same as a production multiwindow burn alert?**

No. The example uses a request-budget ratio on declared batches and does not implement time-window alerting policy.

**F3. Why inspect the canary separately?**

Its users receive the changed version. Pooling with unrelated healthier requests can conceal version-specific harm.

**F4. Does rollback guarantee full recovery?**

No. Data mutations, external effects, incompatible schemas and queued work can persist. Verify the actual recovery contract.

### Practice task

Remove the error/slow overlap and predict the changed canary bad count and gate result.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

<!-- END WORKED CASES -->

## Synthesis

Clarify what the evidence actually verifies. An assignment diagnostic can fail before an effect is interpretable. Grounding and authorization are separate properties. A pooled healthy denominator can conceal local release harm. Recommend a concrete investigation or recovery step within the real decision owner's authority.

Continue with [Consolidation and Mocks](/docs/product-casebook/consolidation-and-mocks).
