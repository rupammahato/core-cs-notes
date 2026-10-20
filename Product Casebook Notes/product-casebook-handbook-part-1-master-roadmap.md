# Product and Analytics Casebook — Part 1: Master Roadmap

**Practice a complete decision: clarify the task, inspect the evidence, compare options and defend what comes next.**

## 0. What this book adds

The [product foundations](/docs/product-analytics) explain concepts. The [SQL lab](/docs/sql-interview) practices reliable measurement, and the [statistics handbook](/docs/probability-statistics) explains uncertainty. This casebook combines those skills in extended interview scenarios with user goals, data problems, trade-offs and engineering consequences.

**Authoring status: complete.** Nine chapters contain a solving method, 18 worked cases, 72 interviewer follow-ups with answer checkpoints, 18 case practice tasks, 30 final oral checks and two 45-minute mocks. These are original hypothetical cases, not a collection of claimed company question leaks or a measured frequency ranking.

Atlassian's public product interview handbook emphasizes customer understanding, outcomes, prioritization, communication and leadership. That is one role-specific reason to practice both analytical reasoning and a clear decision explanation. It does not establish every company's interview format. [Atlassian product interview handbook](https://www.atlassian.com/company/careers/resources/career-growth/product-managers).

## 1. Chapter map

| Chapter | Cases | Main skill |
| --- | --- | --- |
| [Case method and evidence](/docs/product-casebook/case-method-and-evidence) | Reusable approach | Clarify, scope, distinguish facts from assumptions and communicate a decision |
| [Product sense and prioritization](/docs/product-casebook/product-sense-and-prioritization) | C01–C03 | Design for a blocked user task, prioritize and verify a usable flow |
| [Metrics and root-cause analysis](/docs/product-casebook/metrics-and-root-cause-analysis) | C04–C06 | Decompose changes, reconcile sources and avoid proxy optimization |
| [Growth, activation and retention](/docs/product-casebook/growth-activation-and-retention) | C07–C09 | Find useful first value, compare mature cohorts and handle attention guardrails |
| [Pricing and business models](/docs/product-casebook/pricing-and-business-models) | C10–C12 | Define contribution, discount scenarios, CAC and payback limits |
| [Marketplaces and operations](/docs/product-casebook/marketplaces-and-operations) | C13–C15 | Reason about compatibility, capacity, quality and threshold trade-offs |
| [Experiments, AI and launch decisions](/docs/product-casebook/experiments-ai-and-launch-decisions) | C16–C18 | Validate assignment, evaluate permitted useful answers and gate a rollout |
| [Consolidation and mocks](/docs/product-casebook/consolidation-and-mocks) | Final practice | Diagnose failures, adapt assumptions and explain a conditional recommendation |

## 2. How each case is framed

Every case supplies a prompt, clarification questions, target user/objective, evidence status, complete numerical fixture, metric contract, analysis, actual calculation output, competing options, worked recommendation, evidence that would change it, engineering implications and four follow-ups.

The recommendation is a defensible teaching answer under the stated assumptions. Another answer can be better when it identifies a different supported target, constraint or decision criterion. The executable lab verifies selected arithmetic and named fixture gates; it does not grade product judgment automatically.

## 3. Verified scope

**Verification, 21 October 2026:** 41 checks passed on Python 3.13.15: 18 independent arithmetic reference projections, 13 changed scenarios, eight rejected contradictions and two preservation checks. The earlier 144 handbook files remain byte-identical to the captured snapshot.

All users, companies, labels, costs, traffic and experiments in the cases are invented. Aggregate declarations such as canonical identities, mature users or grounded-correct labels are supplied assumptions, not independently inspected real source records. No actual user research, provider call, experiment or deployment is performed.

Some outputs describe a scenario. A recovery assumption, unchanged downstream conversion, constant monthly contribution or uniform prevented loss is not an observed causal effect. Some gates reflect an illustrative predeclared policy. Passing a gate is not proof that a launch is safe or commercially optimal.

## 4. Run a case

From the repository root:

```powershell
python examples/product-casebook/compute.py C04
python examples/product-casebook/compute.py C18
python examples/product-casebook/verify.py
```

The lab uses only Python's standard library and fixture.json. Results are recorded at full floating-point precision; displayed outputs round to six decimal places, retaining significant digits for tiny probabilities. Money is invented USD cents unless the case says otherwise. Ratios and percentage-point changes retain explicit denominator names.

## 5. Study routes

**Product role:** method → C01–C03 → C07/C09 → C10/C11 → C13 → C16–C18 → both mocks.

**Analyst role:** method → C04–C08 → C12 → C15/C16 → C17/C18, with the SQL and statistics bridges.

**Engineer explaining product ownership:** method → C01/C03 → C05/C07 → C10/C14 → C17/C18, explaining how architecture supports the user and measurement contracts.

Use the [resume drills](/docs/product-analytics/consolidation-resume-drills) for actual experience storytelling. Do not recast a casebook's invented improvement as a personal resume achievement.

## 6. Authoring and learner status

- [x] Method, six case families and final revision authored.
- [x] All 18 arithmetic scenarios executed with selected independent references.
- [x] Follow-ups, architectural bridges and two mocks authored.
- [ ] I have attempted the cases before reading the worked recommendations.
- [ ] I can name the assumption most likely to change each recommendation.
- [ ] I have attempted both mocks and recorded evidence gaps in my answers.

Begin with [Case Method and Evidence](/docs/product-casebook/case-method-and-evidence).
