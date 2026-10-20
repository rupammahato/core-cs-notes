# Product and Analytics Casebook — Part 3: Product Sense and Prioritization

**C01–C03: make a constrained product choice and explain how it can be assessed.**

## Before the cases

Begin with a blocked task and a target user. Segment only when the segment changes the need or decision. Generate alternatives, compare them and define a small useful scope with explicit failure behavior.

Intercom's RICE framework combines reach, impact, confidence and effort. It makes estimated inputs inspectable, but the score is not a substitute for evidence, dependency analysis or strategic judgment. C02 deliberately changes one estimate to expose that sensitivity. [Original RICE explanation](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/).

Usable forms need meaningful control labels and instructions, including for people using assistive technologies. C03 applies that design concern as a case requirement; its local criterion counts are not a standards audit or conformance claim. [W3C WAI: labeling controls](https://www.w3.org/WAI/tutorials/forms/labels/).

<!-- BEGIN WORKED CASES -->

## C01. Recover an interrupted application

A hiring portal wants more completed applications. The team proposes autosave. Decide what to investigate, what to build first and how to measure it.

### Clarify the question

- Which candidates, devices and application deadlines are in scope?
- Does interruption mean lost work, an intentional pause or a blocker elsewhere?
- What must remain true about application quality and candidate privacy?

### Frame the user and objective

Focus on invited candidates completing a usable application. The employer buys the service, but the candidate experiences the interruption. Improve successful completion without lowering quality or exposing another candidate's draft.

### Evidence status and complete fixture inputs

The supplied counts are invented, complete aggregates for one eligible cohort. Interruption is a supplied label, not a verified causal explanation. Recovering half of interrupted noncompletions is a scenario assumption, not an observed effect.

```json
{
  "eligible": 1000,
  "interrupted": 400,
  "interrupted_completed": 240,
  "uninterrupted_completed": 540,
  "assumed_recovery_share": 0.5
}
```

### Metric and decision contract

Primary: eligible candidates who submit a usable application by the agreed deadline / eligible invited candidates. Segment by device and interruption history. Guardrails: unusable submissions, lost acknowledged work, duplicate submissions and unauthorized access.

### Work the evidence

Compare interrupted and uninterrupted journeys, then observe the failure state and ask candidates what stopped them. Investigate form complexity, eligibility rejection, upload failure and intentional withdrawal alongside lost progress. The scenario calculation bounds a possible opportunity under a declared recovery assumption; it does not identify which intervention delivers it.

Run `python examples/product-casebook/compute.py C01` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "baseline_completed": 780,
  "interrupted_not_completed": 160,
  "scenario_additional_completed": 80.0,
  "scenario_total_completed": 860.0,
  "scenario_lift_pp": 8.0
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Shorten the form: may remove broad friction, but can omit information recruiters need.
- Save and resume a constrained draft: targets interruption, but adds identity, version and restoration behavior.
- Send reminders: inexpensive to trial, but cannot repair lost work and can create unwanted messaging.

### Worked recommendation

Validate the interrupted flow, then prototype a small save/resume journey if lost work is material. Keep clear saving, saved and failed states. Test restoration and authorization before a limited outcome evaluation. Do not promise the scenario lift as a delivery commitment.

**What would change this recommendation:** If interrupted candidates mostly fail eligibility or intentionally withdraw, prioritize that underlying problem. If server-acknowledged drafts are already restored correctly, investigate discoverability or another bottleneck.

### Engineering and architecture implications

Persist drafts under candidate/application ownership, acknowledge durable writes, use version checks for concurrent tabs and make final submission idempotent. Instrument acknowledged saves and restoration failures without logging application contents.

Review the [related technical chapter](/docs/resume-skills/api-security-authorization-multi-tenancy) for implementation depth.

### Interviewer follow-ups

**F1. Why not start by choosing a database?**

First specify what successful save and restore mean. Storage choice follows identity, durability, conflict and retention requirements.

**F2. What does the forecast assume?**

That half the interrupted noncompleters become completers and nothing else changes. The fixture does not establish that response.

**F3. What would be an MVP?**

A recoverable constrained draft with clear status, authorized restoration and a reliable submission boundary, plus measurement of the relevant outcome.

**F4. How would you validate quality?**

Define usable-submission criteria with recruiters before the evaluation; inspect both completion and downstream acceptance or rework.

### Practice task

Replace the recovery assumption with zero and explain why the original cohort description still does not prove a lost-work cause.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C02. Prioritize onboarding, notifications or admin work

Three teams want roadmap capacity. Use the supplied RICE estimates, then handle a stakeholder who says the score settles the decision.

### Clarify the question

- Are reach and effort measured over the same period and unit?
- Which work is mandatory, dependency-enabling or tied to an existing commitment?
- What evidence supports impact and confidence?

### Frame the user and objective

Choose the next discretionary investment for a product trying to create useful activation. Keep mandatory security or contractual work visible outside a single discretionary ranking.

### Evidence status and complete fixture inputs

Reach, impact, confidence and effort are invented planning estimates. Scores are arithmetic summaries of these estimates, not predicted realized value or calibrated success probabilities.

```json
{
  "candidates": [
    {
      "id": "onboarding",
      "reach": 800,
      "impact": 2,
      "confidence": 0.75,
      "effort": 3
    },
    {
      "id": "notifications",
      "reach": 2000,
      "impact": 0.5,
      "confidence": 0.5,
      "effort": 2
    },
    {
      "id": "admin",
      "reach": 100,
      "impact": 3,
      "confidence": 0.9,
      "effort": 1
    }
  ],
  "lower_onboarding_confidence": 0.3
}
```

### Metric and decision contract

Evaluate the chosen project's user outcome and guardrails after delivery. The prioritization score is a planning aid, not a North Star metric. Record estimate owners, period, effort unit and confidence rationale.

### Work the evidence

Calculate reach*impact*confidence/effort using common conventions. Onboarding leads in the baseline, but its lower-confidence scenario falls behind the alternatives. Explore why confidence changed and whether a small discovery activity can resolve the most decision-relevant uncertainty.

Run `python examples/product-casebook/compute.py C02` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "baseline_ranking": [
    {
      "id": "onboarding",
      "score": 400.0
    },
    {
      "id": "admin",
      "score": 270.0
    },
    {
      "id": "notifications",
      "score": 250.0
    }
  ],
  "lower_confidence_ranking": [
    {
      "id": "admin",
      "score": 270.0
    },
    {
      "id": "notifications",
      "score": 250.0
    },
    {
      "id": "onboarding",
      "score": 160.0
    }
  ]
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Choose baseline-leading onboarding: plausible if the estimates are credible, but sensitive to confidence.
- Run a narrow evidence-gathering activity: can improve the decision, but consumes time and needs a stopping question.
- Fund a lower-scoring dependency or mandatory task: justified by constraints the discretionary score does not model.

### Worked recommendation

Use the ranking to structure discussion, inspect estimate sensitivity and explicitly handle constraints. If onboarding uncertainty can be reduced cheaply, do that before committing a larger team. Publish the trade-off and what was deferred.

**What would change this recommendation:** A credible mandatory deadline, invalid reach estimate or costly dependency can alter the order. So can evidence that a lower-scoring project solves a more strategic problem.

### Engineering and architecture implications

Identify shared platform dependencies and separate enabling work from user-facing scope. Agree thin acceptance criteria so effort includes integration, telemetry, rollout and ongoing ownership.

Review the [related technical chapter](/docs/system-design/application-architecture-service-boundaries) for implementation depth.

### Interviewer follow-ups

**F1. Is confidence a probability of project success?**

Not here. It is an editorial evidence-strength adjustment on the declared scale.

**F2. Can a low score still win?**

Yes, when mandatory obligations, strategic sequencing or dependencies change the feasible choice. Make that reasoning explicit.

**F3. How do you avoid false precision?**

Show ranges or scenarios, name uncertain inputs and examine whether plausible changes reverse the ranking.

**F4. How do you answer an executive's urgent request?**

Clarify its objective and deadline, compare opportunity costs, and agree an explicit trade-off rather than silently displacing work.

### Practice task

Lower onboarding confidence to zero and explain the new ranking without calling the other projects guaranteed winners.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C03. Make document submission usable

Mobile application completion trails desktop. A redesign has four supplied passing criteria and one critical failure. Decide whether its projected lift justifies launch.

### Clarify the question

- What is the mobile task, device mix and assistive-technology context?
- Are the criteria executable behaviors with evidence, rather than labels?
- What exactly failed and who would be blocked?

### Frame the user and objective

Help eligible candidates complete document submission reliably, including users who navigate by keyboard or use assistive technology. Treat accessibility and privacy as design requirements rather than optional polish.

### Evidence status and complete fixture inputs

The counts and criterion states are supplied synthetic data. Four passes, one critical failure and one unknown do not constitute a real accessibility audit. A ten-percentage-point mobile improvement is an assumption, capped at the remaining mobile noncompleters.

```json
{
  "mobile_users": 700,
  "mobile_completed": 420,
  "desktop_users": 300,
  "desktop_completed": 240,
  "assumed_mobile_lift": 0.1,
  "criteria": 6,
  "verified_passes": 4,
  "critical_failures": 1
}
```

### Metric and decision contract

Primary: usable submissions / eligible candidates in the same complete outcome window. Track mobile/desktop results and task failures. Acceptance states need linked evidence; a critical failure blocks the proposed release under this case's policy.

### Work the evidence

The weighted baseline is lower than an unweighted average of device rates would suggest. Calculate the mobile-improvement scenario separately from observed performance. Investigate upload errors, unclear labels, keyboard focus, error recovery and file constraints. Do not infer the cause from the device split alone.

Run `python examples/product-casebook/compute.py C03` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "baseline_completion_pct": 66.0,
  "scenario_extra_completions": 70.0,
  "scenario_completion_pct": 73.0,
  "verified_pass_coverage_pct": 66.666667,
  "unknown_criteria": 1,
  "supplied_critical_gate_passed": false
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Ship the visually improved form now: faster delivery, but knowingly retains a supplied critical failure.
- Repair the blocking behavior and verify unknown criteria: slower, but provides a coherent release boundary.
- Offer an accessible assisted route temporarily: can unblock users while the primary flow is fixed, with clear ownership and privacy controls.

### Worked recommendation

Hold the proposed launch until the critical failure is repaired and the relevant criteria are verified. Test the actual task with affected users and supported interaction methods. Use any interim route as a deliberate supported service, then evaluate the improved flow's outcome.

**What would change this recommendation:** New evidence can change which interaction is blocking or whether an interim path is usable. It cannot turn a forecast into verification that the current critical failure is harmless.

### Engineering and architecture implications

Keep accessible labels tied to controls, expose upload/error status meaningfully, preserve progress after recoverable errors and enforce file/ownership checks on the server. A frontend success state must follow server acknowledgement.

Review the [related technical chapter](/docs/system-design/file-upload-processing) for implementation depth.

### Interviewer follow-ups

**F1. Does four of six mean 67% accessible?**

No. It is supplied pass coverage over six local criteria, not a standards-conformance score or a weighted user-impact measure.

**F2. Why not infer causality from mobile completion?**

Device users can differ in intent, network, form context and eligibility. Observe the failure and compare appropriately.

**F3. What does one unknown criterion mean?**

No supplied pass or fail result exists for it; absence of evidence is not a pass.

**F4. How do you communicate the delay?**

Name the blocked task, affected users, required evidence, owner and interim route; keep the projected commercial benefit separate.

### Practice task

Change the supplied critical failure to a verified pass, then explain why passing that gate alone still does not establish a real outcome lift.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

<!-- END WORKED CASES -->

## Synthesis

A forecast describes a possibility under assumptions, a prioritization score organizes estimates, and an acceptance check verifies supplied behavior evidence. They are different inputs to a product decision. Explain the user outcome and which uncertainty matters before optimizing any of them.

Continue with [Metrics and Root-Cause Analysis](/docs/product-casebook/metrics-and-root-cause-analysis).
