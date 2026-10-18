# Product and Analytics Placement Handbook — Part 1: Master Roadmap

**From a user problem to a product decision, a measurable outcome and an interview explanation.**

---

## 0. What this track adds

The backend and architecture handbooks explain how systems behave. This track explains how to decide what a system should help people accomplish, how to specify that behavior, and how to assess the result.

It covers the product and analysis skills in the second resume. The six-section syllabus was already agreed in Resume-Skills-Notes-Plan.md at the repository root; this roadmap makes that sequence usable as its own subject.

**Authoring status: complete; roadmap and all six sections P0–P5 available.** An authored chapter does not establish learning mastery. Checklists stay unchecked until you can demonstrate the skill.

### The questions every section should help you answer

1. What problem does this concept or tool solve?
2. What are its inputs, definitions and assumptions?
3. How does a small example work, step by step?
4. What decision would you make from the result?
5. What alternative explanation or failure would change that decision?
6. Which parts can you support with evidence from your own experience?

**Organizing principle:** make the connection from problem to decision to evidence explicit.

## 1. Sections and current availability

| ID | Section | Coverage | Status |
| --- | --- | --- | --- |
| P0 | [Product thinking, requirements and design communication](/docs/product-analytics/product-thinking-requirements-design) | User problems, stakeholders, discovery, prioritization, BRD/PRD, acceptance criteria, traceability, flows, Figma and Notion | Available |
| P1 | [Pricing and unit economics](/docs/product-analytics/pricing-unit-economics) | Usage-based pricing, credits, provider costs, retries, cost per successful generation, gross margin and the Zyke case | Available |
| P2 | [Product analytics and experiments](/docs/product-analytics/product-analytics-experiments) | Tracking plans, events, funnels, cohorts, retention, activation, experiments and causal limits; PostHog, GA4 and Clarity | Available |
| P3 | [Python and Excel for analysis](/docs/product-analytics/python-excel-analysis) | NumPy, pandas, joins, aggregation, missing values, dates, formulas, lookups, pivots and reconciliation | Available |
| P4 | [Marketing measurement and data visualization](/docs/product-analytics/marketing-measurement-data-visualization) | Ads vocabulary, attribution windows, metric denominators, D3, chart selection, treemaps and the marketing-digest case | Available |
| P5 | [Product/analytics resume drills and revision](/docs/product-analytics/consolidation-resume-drills) | Decision stories, contribution, quantified outcomes, stakeholder situations, confusable pairs and interview mocks | Available |

There are **seven authored handbook files**: this roadmap, five teaching chapters P0–P4 and consolidation P5. All six sections have live chapter links. Figma, Notion, analytics platforms and advertising consoles are subsections, rather than separate vendor courses.

## 2. Suggested learning order

```text
P0  user need -> scope -> requirement -> flow -> check -> outcome
 |\
 | +-> P1  value, pricing and economic constraints
 |
 +---> P2  measurement, interpretation and experiments
          |
          +-> P3  reproduce and reconcile the calculations
          |
          +-> P4  acquisition measurement and honest visualization
                         |
P0 + P1 + P2 + P3 + P4 --+-> P5  explain and defend your contribution
```

P3 can be studied before P2 if Python or spreadsheets are immediate interview priorities. P4 relies on the denominator and causality habits introduced in P2. Start preparing resume examples in P0, then improve them as the later sections add economic and analytical detail.

### Useful bridges to the earlier handbooks

| Product question | Existing technical bridge |
| --- | --- |
| Can this user perform this action? | [API security and multi-tenancy](/docs/resume-skills/api-security-authorization-multi-tenancy) |
| Can a payment callback change credits twice? | [Webhooks and payments](/docs/resume-skills/webhooks-payments-reliable-integrations) |
| What produces a trustworthy dashboard? | [S13: analytics event pipeline](/docs/system-design/analytics-event-pipeline) |
| What is a reliable metric collection path? | [Testing and observability](/docs/resume-skills/git-ci-cd-testing-observability-performance) |
| What did I personally build or decide? | [Resume project deep-dives](/docs/resume-skills/resume-project-experience-deep-dives) |
| How do I turn a product requirement into a system? | [A0: design method](/docs/system-design/design-method-estimation) |

The technical analytics pipeline and product analytics answer different questions. A pipeline can process events correctly while a product team chooses a weak metric or draws an unsupported causal conclusion.

## 3. How each chapter is framed

- Start with a plain definition and the interview question it answers.
- Use a concrete, explicitly labelled teaching case.
- Explain inputs, assumptions, units and alternatives before giving a formula or framework.
- Include a flow, worked decision, comparison table and common wrong answers.
- Execute numerical or code examples locally and preserve their actual output.
- Separate computed results, supplied scenario inputs, manual exercises and genuine project evidence.
- Finish with interview Q&A, a mock, practice tasks, answer checkpoints and an unchecked exit checklist.

The question choices are editorial preparation priorities for this resume. They are not measured company interview frequencies or guarantees of what a recruiter will ask.

## 4. Evidence rules

### Four labels to keep separate

| Label | Meaning | Example |
| --- | --- | --- |
| Resume-reported | The resume describes it; implementation or impact may still need corroboration | A hiring-module ownership claim |
| Synthetic teaching case | Invented to explain a mechanism | A backlog with 120 candidates per month |
| Executed local result | A preserved program produced the stated result | The RICE worksheet returns 96.0 |
| Manual exercise | The reader must perform and assess it | A keyboard walkthrough or moderated prototype session |

An invented research observation must never become a quote from an actual customer. A synthetic dashboard must never become a project growth claim. A calculated percentage must identify its numerator, denominator, population and time window.

### What P0 currently verifies

The Python worksheet has **53 local checks** covering RICE arithmetic, malformed estimates, ranking constraints, traceability and change impact. Its eight acceptance-criterion states are **synthetic inputs**: five supplied passes and three pending states. The helper does not execute the corresponding product checks.

No real candidate portal, customer interview, Figma file or Notion workspace was tested. Research came from public primary documentation; no account access or paid service is required.

### What P1 adds

[P1: Pricing and Unit Economics](/docs/product-analytics/pricing-unit-economics) has **88 local checks** for invented provider rates, failed/retried work, missing usage, margins, price floors, break-even and simple credit-pack allocation. It does not reproduce historical Zyke costs or verify real revenue. Each section preserves its own research manifest and execution boundary.

### What P2 adds

[P2: Product Analytics and Experiments](/docs/product-analytics/product-analytics-experiments) has **95 local checks** on an actual SQLite worksheet with invented events, including aliases, duplicates, mature funnels, exact retention and late data. A separate synthetic comparison illustrates lift, approximate uncertainty and SRM. No vendor account or real randomized deployment was used.

### What P3 adds

[P3: Python and Excel for Analysis](/docs/product-analytics/python-excel-analysis) has **72 Python checks**, **38 native Excel checks** and six authoring-engine mutation scenarios on synthetic job and attempt data. It demonstrates join inflation, missing-versus-zero amounts, UTC boundaries and a formula-based workbook. Creating and refreshing the PivotTable remains manual practice.

### What P4 adds

[P4: Marketing Measurement and Data Visualization](/docs/product-analytics/marketing-measurement-data-visualization) has **79 Python/SQLite checks** for metric denominators, fractional credits, attribution windows, cross-platform overlap and a local digest-publication model, plus **36 real Chrome/D3 checks** on keyed joins, charts and responsive states. The supplied data is invented; no ad account, causal lift study or notification delivery was tested.

### What P5 adds

[P5: Product and Analytics Resume Drills and Revision](/docs/product-analytics/consolidation-resume-drills) has **27 local checks**: 12 fresh isolated output drills and 15 source/coverage audits. It consolidates seven resume stories, 30 confusable pairs, 16 diagnosis cards, 60 Q&As, two 45-minute mocks, 12 practice tasks and a 24-question self-test. Source provenance is checked; original business impact and personal learning readiness are not inferred from those checks.

## 5. Interview practice map

| Question family | Start in | Useful follow-up |
| --- | --- | --- |
| Improve an application or onboarding journey | P0 | What evidence would change your feature choice? |
| Translate a vague stakeholder request | P0 | Write one acceptance criterion and one rejection case |
| Prioritize a backlog | P0 | What is mandatory even if its score is low? |
| Choose a price or credit policy | P1 | What happens to economics when a generation fails? |
| Explain a conversion drop | P2 | Is the denominator stable and the event stream complete? |
| Evaluate a feature launch | P2 | What would establish causality? |
| Reconcile two reports | P3 | Which join, time boundary or missing-value rule differs? |
| Evaluate campaign performance | P4 | Does attributed revenue equal incremental revenue? |
| Explain a chart choice | P4 | What comparison does the chart make easy or difficult? |
| Defend a resume outcome | P5 | Which part was your contribution and how was impact measured? |

## 6. Study routes

**Starting now:** follow the route that matches your interview, attempt the section exercises and mocks, then use P5 for final revision, evidence recovery and two 45-minute mocks. All planned chapters are authored; learner exercises remain your own practice.

**Product interview route:** P0 → P1 → P2 → P4 → P5, with P3 exercises alongside P2.

**Analyst interview route:** P0 definitions → P2 → P3 → P4 → P1 → P5.

**Engineer explaining product ownership:** P0 → P1/P2 fundamentals → P5, using the earlier resume and architecture chapters for implementation depth.

Do not memorize a framework without practicing its failure case. A useful answer includes the relevant evidence, the choice, the trade-off and what would cause you to revisit it.

## 7. Research map

Primary sources checked for P0 on **18 October 2026**:

- [GOV.UK: user needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs), [research planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service) and [discovery](https://www.gov.uk/service-manual/agile-delivery/how-the-discovery-phase-works).
- [Atlassian: PRDs](https://www.atlassian.com/agile/product-management/requirements/) and [business requirements](https://www.atlassian.com/software/confluence/resources/guides/how-to/business-requirements).
- [Intercom: the original RICE framework](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers).
- [Figma: prototype flows](https://help.figma.com/hc/en-us/articles/360039823894-Create-and-manage-prototype-flows).
- [Notion: relations and rollups](https://www.notion.com/help/relations-and-rollups).
- [W3C WAI: form notifications](https://www.w3.org/WAI/tutorials/forms/notifications/).
- [The Scrum Guide](https://scrumguides.org/scrum-guide.html): Definition of Done terminology.

The source list supports the concepts and tool vocabulary. It does not establish the teaching case's estimates, historical project facts or interview frequency. P1-P5 preserve their own primary references and version boundaries in the companion research manifests.

## 8. Progress and continued practice

- [x] Six-section scope carried forward from the resume-skills plan.
- [x] Dedicated roadmap, research references and first teaching chapter authored.
- [x] P0 worksheet executed and local evidence preserved.
- [x] P1: pricing and unit economics; 88 local arithmetic/evidence checks and a clearly labelled synthetic cohort.
- [x] P2: product analytics and experiments; 95 local SQLite, event-quality, cohort and experiment-arithmetic checks.
- [x] P3: Python and Excel for analysis; 72 Python checks, 38 native Excel checks and six authoring-engine mutation scenarios.
- [x] P4: marketing measurement and data visualization; 79 Python/SQLite checks and 36 real Chrome/D3 browser checks.
- [x] P5: final revision; 12 isolated output drills and 15 source/coverage audits, seven story cards, 60 Q&As and two 45-minute mocks.

Start with [P0: Product Thinking, Requirements and Design Communication](/docs/product-analytics/product-thinking-requirements-design). Finish with [P5: Product and Analytics Resume Drills and Revision](/docs/product-analytics/consolidation-resume-drills). No planned authoring sections remain; continue with evidence recovery, manual exercises and targeted revision.
