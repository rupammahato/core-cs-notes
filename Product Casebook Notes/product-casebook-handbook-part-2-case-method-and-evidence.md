# Product and Analytics Casebook — Part 2: Case Method and Evidence

**A framework is useful when it exposes the next decision, assumption or discriminating check.**

## 1. Classify the question without forcing a template

| Prompt shape | First useful move | Frequent failure |
| --- | --- | --- |
| Design or improve a product | Define a user, context and blocked outcome | Starting with a feature list |
| A metric changed | Verify definition and decompose the change | Naming one cause before checking evidence |
| Grow activation or retention | Define value, cohort and observation window | Optimizing an immature or proxy denominator |
| Price or monetize | Define value unit, cost basis and scenario | Calling a cost floor a market price |
| Improve a marketplace or operation | Inspect compatibility and flow constraints | Optimizing a global count that hides a local shortage |
| Evaluate or launch | Validate evidence and predeclared decision rules | Treating a favorable headline as sufficient |

Clarification should reduce uncertainty about the answer. If no answer is available, state a reasonable working assumption and continue. Do not spend the whole interview collecting questions without making progress.

## 2. State the target and constraints

Use a compact opening: “I will focus on [user] trying to [task] in [context]. I will optimize [outcome] while preserving [constraints]. I will first check [critical uncertainty].”

Separate the user, buyer and operating stakeholder. A recruiter purchasing a portal and a candidate completing it can have related but different goals. A marketplace needs both a useful buyer outcome and viable seller participation.

User-needs research should establish what people are trying to accomplish rather than encode a preferred feature as the need. Discovery can establish that a proposed build is not worthwhile or that another problem deserves attention. [GOV.UK user needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs), [discovery](https://www.gov.uk/service-manual/agile-delivery/how-the-discovery-phase-works).

## 3. Build an evidence ledger

| Evidence class | What to write | What it cannot establish alone |
| --- | --- | --- |
| Supplied case fact | Definition, period, source and coverage | That a real source was actually verified |
| Descriptive measurement | Numerator, denominator and uncertainty about coverage | An intervention's causal effect |
| User observation | Context, behavior and sampling limitation | Population prevalence without a suitable design |
| Hypothesis | A mechanism that could explain observations | That the mechanism is already the cause |
| Scenario assumption | Explicit parameter and what stays fixed | A forecast validated against future outcomes |
| Decision policy | Threshold, owner and when it was agreed | A universal rule for every product |

In these notes, fixture data are a supplied case fact. A forecast is visibly labelled scenario. A recommendation combines those inputs with judgment; it is not a runtime test result.

## 4. Turn a goal into a metric contract

Specify population, independent unit, eligibility, numerator, denominator, observation window, source identity, exclusions, missingness and revision policy. Then name one primary outcome, diagnostic measures and guardrails.

```text
User goal -> observable signal -> metric definition
  -> trusted source -> valid comparison -> decision use
```

Google's HEART work connects user-centered goals, signals and metrics, rather than selecting an available event count as the objective. A metric needs to represent the intended user outcome and context. [HEART and goals-signals-metrics](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/).

A North Star is not permission to ignore other outcomes. A user-value metric can improve while reliability, privacy, quality or supplier economics deteriorate. Define critical gates and softer trade-offs explicitly.

## 5. Investigate with a falsifiable tree

For a reported metric change, begin with definition, instrumentation, source completeness and observation maturity. Then decompose by eligible volume, segment mix and within-segment behavior. Inspect release, seasonality and external changes only with the relevant evidence.

```text
Reported change
  -> same definition, source, identity and cutoff?
  -> same opportunity to observe the outcome?
  -> changed population volume or mixture?
  -> changed behavior within comparable segments?
  -> plausible mechanisms and discriminating checks
```

Ask for a check that can distinguish competing explanations. If every possible result would leave your story unchanged, it is probably too vague to function as an investigation hypothesis.

Use [SQL population and grain practice](/docs/sql-interview/joins-grain-and-null-semantics) and [sampling/uncertainty foundations](/docs/probability-statistics/descriptive-statistics-and-sampling) when reasoning about the evidence.

## 6. Compare feasible options

Include the current behavior or no-build option, a constrained intervention and a materially different alternative. Compare user value, evidence strength, cost, time, risk, reversibility and dependencies. Explain which uncertainty is worth reducing before committing more effort.

Prioritization scores can make assumptions explicit, but mandatory work, strategic constraints and dependency order may not fit a single score. A score ranks supplied estimates; it does not validate them.

## 7. Connect the decision to architecture

Describe only the technical properties needed to make the product behavior and measurement credible: ownership, state transitions, reliable acknowledgement, duplicate handling, permission checks, event identity and rollback boundaries.

For a saved application, “the latest acknowledged draft can be restored by its owner” is a meaningful requirement. “Use database X” is an implementation preference until the behavior and constraints explain it. For analytics, a receipt-time revision policy can matter as much as the visualization library.

## 8. A small decision and delivery memo

| Field | What a reviewer needs |
| --- | --- |
| Problem and user | Task, context, obstacle and evidence status |
| Target and scope | Outcome, population, explicit exclusions and constraints |
| Options | Feasible alternatives with opportunity costs |
| Recommendation | Choice, main assumption and what would reverse it |
| Requirements | Observable behavior, failure handling and acceptance evidence |
| Measurement | Metric contract, design, observation maturity and guardrails |
| Delivery | Owner, dependencies, rollout boundary and recovery plan |
| Review | Decision date/trigger, evidence to collect and unresolved questions |

Do not copy fixture numbers into a real business memo as measured results. For an actual project, trace every material claim to evidence you can show.

## 9. Communicate under challenge

If a stakeholder prefers another option, identify the objective or constraint behind that preference. Explain the opportunity cost and evidence rather than treating disagreement as a failure to understand a framework. Agree what new information or risk ownership could change the choice.

If the interviewer changes an assumption, update the affected denominator, scenario or constraint and explain the consequence. Keeping the original recommendation regardless of changed evidence is weaker than a clear revision.

Finish an answer with a conditional decision and a concrete next step: what to investigate, prototype, measure, hold or test, and why that step resolves the most important remaining uncertainty.

## 10. Practice checkpoint

- [ ] I can separate supplied evidence, assumptions and judgment.
- [ ] I can choose a discriminating check rather than list every possible metric.
- [ ] I can connect a user requirement to a necessary engineering property.

Continue with [Product Sense and Prioritization](/docs/product-casebook/product-sense-and-prioritization).
