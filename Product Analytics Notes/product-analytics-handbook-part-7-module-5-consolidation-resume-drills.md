# Product and Analytics Placement Handbook — Part 7: P5: Product and Analytics Resume Drills and Revision

**Turn the six sections into explanations you can defend under follow-up questions.**

**Verification, 18 October 2026:** 27 local checks passed with Python 3.13.15 and SQLite 3.50.4: 12 isolated output drills and 15 source/coverage audits. The audits cover six chapter mappings, seven projects in the existing resume-evidence catalogue and the fingerprints of the two local source resumes. They verify provenance and coverage, not the truth of original business-impact claims. All drill workers exited; the SQL drill closed its in-memory database. No service, message or advertising-budget action was started.

---

## 5.0 How to use the final section

The earlier chapters explain concepts and mechanisms. This chapter asks you to choose among them, predict outputs, diagnose misleading numbers and explain your own contribution. It completes the planned Product and Analytics track; an authored handbook is not evidence that the learner has mastered it.

Start with one real resume story and one output drill. Answer aloud before reading the checkpoint. When an answer breaks down, return to the relevant chapter rather than memorizing a sentence without understanding its assumptions.

The question bank and practice schedules are editorial preparation tools. They are not a measured ranking of company interview frequency, a hiring guarantee or an automated assessment of interview readiness.

## 5.1 The six-section map

| Section | Central question | What you should produce |
| --- | --- | --- |
| [P0: Product thinking and requirements](/docs/product-analytics/product-thinking-requirements-design) | Which user problem should we solve, and what behavior is required? | Problem statement, coherent scope, criteria and evidence plan |
| [P1: Pricing and unit economics](/docs/product-analytics/pricing-unit-economics) | Does the value and cost model support the proposed offer? | Metering assumptions, complete cost, margin and pricing trade-offs |
| [P2: Analytics and experiments](/docs/product-analytics/product-analytics-experiments) | What happened, and what would establish an effect? | Tracking contract, eligible denominator, cohorts and experiment interpretation |
| [P3: Python and Excel analysis](/docs/product-analytics/python-excel-analysis) | Can we reproduce and reconcile the result? | Grain-aware transformation, missingness policy and traceable worksheet |
| [P4: Marketing and visualization](/docs/product-analytics/marketing-measurement-data-visualization) | What can acquisition numbers and charts legitimately tell us? | Comparable reports, attribution limits and a useful visual comparison |
| P5: Resume drills and revision | Can I defend the decision, mechanism and contribution? | Evidence-backed story, output prediction, diagnosis and next action |

```text
User need -> requirement -> implementation behavior -> measured observation
    -> correct interpretation -> decision -> follow-up evidence
                       |
          Explain your own contribution at each boundary
```

Use the [master roadmap](/docs/product-analytics) to choose a study route. Use [M28 resume deep-dives](/docs/resume-skills/resume-project-experience-deep-dives) for the technical request traces and source catalogue behind the story cards below.

## 5.2 A reusable answer structure

For a product or analysis answer, use: **user and problem → decision → your action → mechanism/check → observed result → limitation or next step**. The order can change when the interviewer asks about a failure or a specific calculation.

For behavioral questions, STAR organizes situation, task, action and result. Keep context short, make your own actions concrete and adapt the story to the question. A result can include a verified delivery, corrected behavior or a useful lesson when a causal business metric is unavailable. [MIT's STAR guidance](https://capd.mit.edu/resources/the-star-method-for-behavioral-interviews/).

Amazon's BIE preparation guidance is one role-specific primary example of preparing concrete experiences, data where applicable, and lessons from success or failure. It does not establish that every employer uses the same format or questions. [Amazon BIE preparation](https://www.amazon.jobs/content/en/how-we-hire/bie-interview-prep).

| Answer length | Focus | Useful stopping point |
| --- | --- | --- |
| About 30 seconds | User problem, owned contribution, one concrete mechanism | Invite a follow-up on the difficult part |
| About two minutes | One complete decision or failure story | Explain the outcome and its evidence boundary |
| About five minutes | Diagram, success path, failure, alternative and measurement | State what you would improve and why |

Practice outlines, not a fabricated transcript. Do not invent a stakeholder quote, rejected alternative, user study or result merely because the structure has a slot for it.

## 5.3 Build a small evidence pack

| Claim | Evidence that would support it | What does not establish it |
| --- | --- | --- |
| I owned a module | Requirements, implementation/review history and concrete decisions | A framework list or commit percentage alone |
| I corrected a calculation | Approved rule, failing input, expected result, patch and regression | A new teaching example with different inputs |
| I improved conversion | Defined before/after populations and measurement method | A screenshot without its denominator or a release date alone |
| The product caused improvement | An appropriate causal design and its assumptions | Attribution credit or an uncontrolled before/after comparison |
| I reduced onboarding effort | Defined start/end states, comparable task observations | Fewer fields with no task-success evidence |
| The system handles a load | Workload, environment, duration, concurrency, failures and latency definition | A raw request count or an unrelated local fixture |

For each major resume bullet, keep a claim, source, ownership boundary, date/window, definition, known limitation and follow-up artifact. You can explain confidential structures and decisions without exposing customer data or inventing substitute impact numbers.

The two supplied PDFs remain local. This chapter uses the existing M28 catalogue, which omits contact details and preserves page/anchor provenance. Checking a PDF fingerprint proves the file matches the catalogue's source; it does not independently corroborate the resume's claims.

## 5.4 Seven resume story cards

The following rehearsal openings are grounded in resume-reported scope. Confirm that the wording matches your actual contribution before using it. The trade-offs and follow-up prompts are preparation questions, not assertions that those conversations or improvements occurred.

### S01. Neosophical Labs: requirements, workflows and the marketing digest

**Rehearsal opening:** “At Neosophical Labs, I worked on turning payroll-bureau requirements into repeatable workflows and data checks. My recorded scope includes an SLA lifecycle with working-day deadlines and audit history, payroll-rule defect fixes, normalized incoming files, and a marketing digest over analytics and advertising reports.”

**Two-minute outline:** choose one of those flows. For the SLA story, identify the staff member's task, the deadline policy, state changes, escalation and audit evidence. For the digest story, trace source reports to defined metrics, reviewable facts and delivery. Explain the particular piece you owned and one failure that the original evidence can establish.

**Decision to prepare:** when to publish a partial report, withhold a recommendation, retry a notification or escalate an overdue task. Separate the cost of delay from the cost of presenting incorrect information.

**Evidence to recover:** one requirements-to-test mapping, one actual before/after defect case or a redacted digest with source definitions and as-of time. The reported four payroll defects do not authorize inventing their exact inputs or claiming that this handbook certified compliance.

**Follow-ups:** What happened when a report page failed? What did “working day” mean? Was an alert created or delivered? What evidence supports “steering ad spend,” and what causal ROI claim remains unestablished?

### S02. Datsol Solutions / Posterity: candidate journey and MindMap analytics

**Rehearsal opening:** “At Datsol/Posterity, I owned the hiring assessment flow and worked on manager access and analytics. The product resume describes secure candidate invitations, indirect-report access and translating nested Excel scoring into a synchronized MindMap treemap. I also worked on sheet-sync failures involving identity, timestamps and nested records.”

**Two-minute outline:** select the candidate journey or the analytics journey. For candidates, identify HR's action, the invitation's allowed scope, expiry/revocation, recovery and successful submission. For analytics, trace a source row through formula translation, a normalized score, update timing and the visual comparison a manager needs.

**Decision to prepare:** a simpler reliable scoring view versus a richer interactive view, or immediate synchronization versus a documented freshness interval. Describe an alternative only if it was genuinely considered; otherwise frame it as what you would evaluate now.

**Evidence to recover:** source formula, worked scoring example, sync lineage, treemap value definition and actual acceptance criteria. The product resume's ten-minute sync interval is a reported configuration, not proof that every update arrived within that time.

**Follow-ups:** Does area represent an additive quantity or a ratio? How do missing scores appear? Which source timezone was intended? Recover the correct formal role title because the two resumes use different wording.

### S03. 10X Analysts: research access, background ingestion and shared sign-in

**Rehearsal opening:** “At 10X Analysts, I owned knowledge-base APIs for a multi-tenant research product. Users could upload documents for background processing, with owner, public and shared access. I also worked on sign-in interoperability and a proxy boundary that kept service credentials out of browser code.”

**Two-minute outline:** begin with a researcher needing useful private evidence. Trace upload acceptance, processing, readiness and authorized retrieval. Explain a product-visible state for delayed or failed ingestion. Then connect permission changes to what the user can discover or retrieve.

**Decision to prepare:** returning an operation state promptly versus waiting synchronously; convenience of sharing versus permission freshness; one consistent sign-in experience versus cross-service coupling.

**Evidence to recover:** an original state diagram, permission matrix and test showing an unauthorized resource is excluded. Reconcile the technical resume's 93 routes and product resume's 95 endpoints against a specific inventory and date; do not choose a number arbitrarily.

**Follow-ups:** Is upload acceptance the same as search readiness? What happens after revocation? What was your owned work versus the team's? Which observed user outcome is available beyond endpoint counts?

### S04. Zyke: pricing, credits and onboarding

**Rehearsal opening:** “At Zyke, my resume describes taking an AI content product to an MVP while owning onboarding, provider-pricing normalization and credit-based generation. The analytical challenge is connecting a simple customer unit to variable provider usage, retries and failed work.”

**Two-minute outline:** identify the user task and the generation unit. Trace usage measurement, provider cost, credit consumption and payment/entitlement state. Explain the proposed or actual policy for a failed generation using original evidence, then connect onboarding simplification to a measurable completed task.

**Decision to prepare:** predictable per-post credits versus variable provider cost; low-friction onboarding versus output quality; generation retries versus margin and latency. A simple price is useful only if the operational policy supports it.

**Evidence to recover:** dated provider/rate assumptions, actual usage, retry mix, payment mode and cost per successful outcome. P1's invented tariffs and reconciliation are learning evidence, not historical Zyke costs.

**Follow-ups:** Does “payments-live” describe integration readiness, transaction mode or collected customer cash? What supports the reported generation cost? How was a posting-cycle duration measured? Commit share is not a percentage of product impact.

### S05. Consistent Hashing Load Balancer: translate engineering metrics into consequences

**Rehearsal opening:** “My load-balancer project explored placement, failure handling and proxy capacity. For a product explanation, I would connect those mechanisms to stable routing, predictable failures and a defensible capacity measurement.”

**Two-minute outline:** define the request and placement key, trace routing and failure handling, then explain the workload used for any reported comparison. Distinguish a deterministic key-remapping result from a weighted traffic-remapping result.

**Decision to prepare:** operational complexity versus the actual routing requirement, and placement stability versus uneven load. A small fraction of moved keys can still carry most requests if the keys are heavily skewed.

**Evidence to recover:** original ring implementation, key/traffic distributions, benchmark command, environment and equivalent direct/proxied runs. The earlier technical fixture uses a separate teaching ring and does not reproduce the original project benchmark.

**Follow-ups:** What was counted as a moved item? Were keys weighted equally? What failure behavior could users observe? How would you explain p95 latency and errors alongside throughput?

### S06. Megalith: registrations, organizer decisions and quantified outcomes

**Rehearsal opening:** “For Megalith, the resume describes the festival website's registration, authentication, payment and organizer-dashboard workflows. I would explain one complete participant journey and the organizer decision the dashboard supported before discussing reported growth or load figures.”

**Two-minute outline:** trace entry, registration, payment confirmation and the next visible outcome. Identify your contribution, a failure state and one dashboard measure's denominator. Separate successful payment from certificate or notification completion.

**Decision to prepare:** a reliable end-to-end registration path versus extra dashboard or presentation features; event-time reporting versus corrected payment records; fast static pages versus dynamic API capacity.

**Evidence to recover:** comparable year-specific user counts for the reported 42.7% growth, workload evidence for concurrency, and the time window/tool behind uptime or page-load claims. A current site or a screenshot does not establish historical measurements.

**Follow-ups:** Users, accounts, registrations or paid registrations? Same event dates and eligibility? Was page-load time a median, percentile or single observation? What would separate the site's contribution from other growth drivers?

### S07. Membition: NGO onboarding and useful first answers

**Rehearsal opening:** “Membition was a multi-tenant chatbot platform for NGOs. My recorded work includes intake and PDF ingestion into a retrieval-backed assistant, tenant-specific indexing, input validation and answer-scope rules. The product question is when an NGO has actually reached a useful, recoverable ready state.”

**Two-minute outline:** trace NGO intake, tenant provisioning, document processing and the first supported answer. Explain visible progress and recovery after partial failure. Separate the interface's “one request” description from the state changes across several services.

**Decision to prepare:** reducing onboarding steps versus collecting necessary configuration; dedicated tenant resources versus operational overhead; permissive answer behavior versus evidence and scope requirements.

**Evidence to recover:** original service boundaries, readiness criteria, a task-based onboarding observation and labelled answer-evaluation cases. Prompt rules guide behavior but do not establish server-side tenant isolation or measured answer quality.

**Follow-ups:** Was the operation accepted or completed? What happened to orphaned resources? How were unrelated or unsupported questions handled? What source demonstrates a useful first answer rather than merely a provisioned index?

## 5.5 Handling a quantified claim under pressure

For each number, answer: **what was counted, for whom, over which period, compared with what, measured how, and with which exclusions?** Then separate your contribution from the team's result and the result from a causal claim.

| Claim wording | First follow-up | If the supporting artifact is unavailable |
| --- | --- | --- |
| “Growth increased by X%” | Baseline, final count, population and time window? | State the recorded claim and the evidence needed to reproduce it |
| “Cost per generation was Y” | Attempt or successful job, retries, usage and rate version? | Explain the cost model without substituting P1's synthetic values |
| “Onboarding took one request” | Accepted operation or completed ready state? | Trace the interface and identify the unresolved completion semantics |
| “All endpoints were covered” | Which inventory, date and definition of coverage? | Keep the route-count discrepancy visible |
| “A digest improved ROI” | Measured profit, attributed revenue or causal effect? | Describe the delivered decision support and avoid an unestablished impact claim |

An honest boundary can be concise: “That number is in my recorded project summary; to reproduce it I would need the original cohort export and counting rule. I can explain the mechanism and the validation I personally performed.” Do not use this sentence to evade details you actually know; recover them before the interview when possible.

## 5.6 Thirty confusable pairs

| ID | Pair | Distinction to say aloud |
| --- | --- | --- |
| C01 | User need / feature | A desired outcome or obstacle versus one proposed solution |
| C02 | User / buyer | The person doing a task versus the person deciding to pay |
| C03 | Output / outcome | Delivered artifact versus changed user/business behavior |
| C04 | Assumption / observation | A belief to test versus something actually observed |
| C05 | BRD / PRD | Business context and requirements versus defined product behavior and scope |
| C06 | Acceptance criterion / test execution | Required observable behavior versus evidence from performing a check |
| C07 | Traceability / readiness | Linked requirements/evidence versus sufficient verified release conditions |
| C08 | RICE score / decision | A ranking input versus a choice that also considers constraints and uncertainty |
| C09 | Wireframe / prototype | Structural representation versus a model of interaction |
| C10 | Prototype task success / product adoption | A controlled observed task versus sustained real-world use |
| C11 | Provider attempt / successful job | One cost-bearing execution versus the successful user outcome |
| C12 | Known subtotal / complete total | Observed contribution versus a total with its required inputs resolved |
| C13 | Gross margin / contribution margin | Revenue less COGS versus revenue less defined variable costs |
| C14 | Credit consumption / cash collection | A service entitlement effect versus a payment/cash event |
| C15 | Break-even / healthy cash flow | Cost/revenue balance under assumptions versus timing and available funds |
| C16 | Event time / ingestion time | When an action occurred versus when the system learned about it |
| C17 | Activation / retention | Reaching an initial value milestone versus returning under a defined rule |
| C18 | Exact-day / rolling retention | Return in one specified period versus return from a point onward |
| C19 | Percentage points / relative percent | Difference between rates versus difference divided by a baseline rate |
| C20 | Correlation / causation | Association versus a supported counterfactual effect |
| C21 | Grain / row count | Meaning of one row versus the number of rows currently stored |
| C22 | Exact duplicate / legitimate retry | Repeated delivery of one identity versus a new attempt identity |
| C23 | Label alignment / position | Matching by index identity versus matching by array order |
| C24 | Lookup / aggregation | Retrieve a corresponding attribute versus summarize multiple records |
| C25 | Count / sum | Number of qualifying observations versus added measure values |
| C26 | Cell recalculation / data refresh | Re-evaluating formulas versus obtaining/updating source or cached report data |
| C27 | CPA / CAC | Cost per defined action versus acquisition of a new customer under a cost scope |
| C28 | ROAS / profit | Attributed value per ad spend versus revenue less the relevant costs |
| C29 | Attribution / incrementality | Assigning outcome credit versus estimating outcomes caused by intervention |
| C30 | Treemap identity / position | A stable data key versus a layout location that can change with values |

Use the pair that matches the interviewer's uncertainty. Reciting all of them in one answer makes the explanation harder to follow.

## 5.7 Twelve executed output drills

Each drill has a separate Python source under `examples/product-analytics/module-5-consolidation-resume-drills/drills/`. Predict the output and explain its consequence before running it. The actual output below is checked against independently specified answers in `expected-output.json`.

D01–D03 call the earlier P0/P1 helpers. D10–D11 call P4's actual local functions. Other drills are deliberately small standard-library analogues; D07 uses real SQLite. None replays an original employer system or re-runs every historical chapter test.

### D01. RICE sensitivity

Reach is 120 in one period, impact 2, confidence 0.8 and effort 2 person-time units. Halve confidence while leaving other inputs fixed.

```json
{"baseline": "96.0", "lower_confidence": "48.0"}
```

The arithmetic changes the score, not the evidence behind the estimate. Mandatory security work cannot be removed merely because another discretionary feature scores higher.

### D02. Linked criteria versus supplied pass states

Run P0's traceability helper on its authored synthetic case. It summarizes supplied statuses; it does not execute a product check.

```json
{"criteria": 8, "supplied_passes": 5, "passed_fraction": "0.625", "worksheet_ready": false}
```

Structural linkage, supplied passes and genuine product readiness are different claims. A manually pending criterion must not silently become a pass.

### D03. Margin and price floor

Use synthetic revenue of 100 USD, COGS of 40 and another 10 of variable cost. Ask for the price that supports a 60% gross margin on cost 40.

```json
{"gross_margin_pct": "60.000000", "contribution_margin_pct": "50.000000", "price_for_60pct_margin_usd": "100.00"}
```

A 60% margin is not a 60% markup. The calculation also does not establish demand at the resulting price.

### D04. Failed work belongs in cost per success

Three successful jobs each cost 60 cents; a failed job costs 120 cents. Compare the complete selected cohort cost with an incorrectly successful-only numerator.

```json
{"all_cost_cents": 300, "successes": 3, "cost_per_success_cents": 100.0, "wrong_success_only_cents": 60.0}
```

The denominator is successful outcomes, while the numerator includes the cohort's failed work. Define any other exclusions explicitly.

### D05. Percentage points and relative lift

Control has 20 outcomes from 100 eligible observations; treatment has 24 from 100. This is arithmetic, not a randomized deployment or a significance conclusion.

```json
{"control_pct": "20.0", "treatment_pct": "24.00", "absolute_lift_pp": "4.00", "relative_lift_pct": "20.0"}
```

Use the units in the answer: four percentage points, or twenty percent relative lift. Baseline and uncertainty still matter.

### D06. Mature denominator

Three synthetic users enter on 1, 2 and 8 October. The report cutoff is 10 October at midnight UTC. The drill admits users whose seven-day milestone is strictly before cutoff and supplies one returned mature user.

```json
{"mature_users": 2, "returned_mature_users": 1, "rate_pct": "50.000000", "wrong_all_users_pct": "33.333333"}
```

This is a small maturity-denominator illustration, not P2's complete exact-day retention query. Define whether a full observation period has elapsed in the actual metric contract.

### D07. The join that creates money

Five synthetic jobs have six attempts. Execute a direct join and a corrected join that aggregates attempt costs to job grain first.

```json
{"job_rows": 5, "joined_rows": 6, "known_bill_cents": 290, "wrong_bill_cents": 490, "cost_cents": 110, "missing_bills": 2}
```

The direct join repeats a job's billed value for its additional attempt. Billing is still incomplete because two bills are unknown. The SQLite drill closes its in-memory connection.

### D08. Zero and missing

Analyze `[0, null, 200]` under an explicit Python policy: sum known values, count missing values and withhold a complete total. Then inspect an all-missing input.

```json
{"known_cents": 200, "missing": 1, "complete": null, "all_missing_known": null}
```

This is an explicit teaching helper, not a claim that Python's built-in sum or every library automatically follows that policy. P3 shows the nullable pandas implementation.

### D09. Aware dates and exclusive end

Use October UTC as `[start, end)`. One source timestamp is 1 October at 00:30 with a +05:30 offset; another is in the middle; the last is exactly the upper boundary.

```json
{"included": ["middle"], "offset_utc": "2026-09-30T19:00:00+00:00", "end_excluded": true}
```

Textual calendar dates alone do not determine membership in a timezone-aware report. Naive source dates need a source policy, not a guessed offset.

### D10. Weighted rates

Run P4's campaign report on its supplied same-currency snapshot. Contrast the combined click/impression ratio with a mean of campaign CTRs.

```json
{"ctr_pct": 1.333333, "wrong_mean_pct": 1.5, "reported_roas": 2.666667}
```

The CTR denominator is impressions; the ROAS denominator is media spend. Neither ratio supports a causal budget decision by itself.

### D11. Credit, overlap and the ledger

Run P4's two hand-defined attribution rules and its independent claim reconciliation. Amounts are net ledger cents.

```json
{
  "click_only": {"A": 5000, "B": 10000, "Unattributed": 27000},
  "view_fallback": {"A": 20000, "B": 10000, "Unattributed": 12000},
  "summed_claim_cents": 40000,
  "unique_claimed_cents": 30000,
  "ledger_net_cents": 42000
}
```

Allocation changes while ledger net revenue stays the same. Summed independent claims, distinct claimed orders and the broader ledger are different populations.

### D12. Keys versus weighted traffic

Ten invented keys carry 1,000 requests. One moved key carries 900 requests; the other nine carry the rest.

```json
{"keys": 10, "moved_keys": 1, "requests": 1000, "moved_requests": 900, "moved_key_pct": 10.0, "moved_traffic_pct": 90.0}
```

A remapping percentage must identify its denominator. These inputs demonstrate a distinction in the resume reconciliation task; they do not reproduce the project's original routing distribution.

## 5.8 Sixteen diagnosis cards

These are hypothetical situations. State the first discriminating check and what result would change your diagnosis; do not call a plausible hypothesis the established cause.

| ID | Symptom | First check | Decision or repair |
| --- | --- | --- | --- |
| B01 | “Users want an AI summary” | Which task or obstacle was actually observed? | Test the need before committing to that feature |
| B02 | Highest RICE item would break access safety | Mandatory constraints and estimate assumptions | Preserve the required boundary and rank the remaining options |
| B03 | PRD says “fast and intuitive” | Observable task and acceptance behavior | Replace vague criteria with measurable behavior and failure cases |
| B04 | Traceability is complete but release is called unready | Pending/failed evidence and owner decisions | Keep linkage separate from verified readiness |
| B05 | Provider invoice exceeds successful-job costs | Attempts, retries, failed work, usage and tariffs | Reconcile the full cost-bearing population |
| B06 | Attractive gross margin but poor cash position | Other costs, payment timing and cash obligations | Explain the narrower margin calculation and cash constraint |
| B07 | Activation jumps after changing the event name | Tracking/schema/version and eligibility changes | Compare consistent definitions or label the discontinuity |
| B08 | Recent cohorts have much lower retention | Observation maturity and return-window definition | Exclude immature periods under the contract |
| B09 | Historical retention changed without a release | Late events, alias resolution and as-of policy | Publish a traceable revision instead of inventing a product effect |
| B10 | Billing grows after a “safe” left join | Right-key multiplicity and repeated left measures | Aggregate to the required grain before enrichment |
| B11 | Excel and pandas disagree on a month | Cell types, timezone, interval and missingness | Isolate boundary records and align the contract |
| B12 | A lookup returns a reasonable but wrong plan | Exact mode, duplicate keys and matched blanks | Diagnose ambiguity rather than taking an arbitrary first result |
| B13 | Two channels both claim most revenue | Models, windows and overlapping order identities | Do not add attributed totals as distinct revenue |
| B14 | Digest recommends scaling after one missing page | Extraction completion and report freshness | Withhold or label the incomplete recommendation |
| B15 | Treemap total is larger than the ledger | Parent contributions, duplicate leaves and measure additivity | Contribute leaf amounts once and reconcile the source |
| B16 | Chart labels vanish on a phone | Available width, layout, label size and data alternative | Recompute layout and preserve a readable exact-value table |

## 5.9 Stakeholder and trade-off practice

| Situation | Useful response pattern | Evidence or artifact |
| --- | --- | --- |
| A stakeholder insists on their preferred feature | Restate the underlying need, explain options and agree a discriminating check | Problem statement and a small test |
| Deadline threatens a reliable end-to-end journey | Protect the minimum complete task and name deferred scope | Scope/exclusion list and acceptance criteria |
| Finance and marketing report different revenue | Align units, population, refunds, windows and attribution | Reconciliation table with unresolved rows |
| Engineering says an event is too expensive to collect | Explain the decision it supports and consider a narrower reliable event | Tracking contract, volume and alternative |
| A metric improved but user complaints increased | Inspect segments, guardrails and what the metric omits | Cohort breakdown and actual qualitative evidence |
| Stakeholders disagree on the denominator | Write competing definitions and show how each changes the decision | Numerator/denominator examples |
| Asked for immediate certainty on incomplete data | State what is known, what is unresolved and the smallest next check | Known subtotal, completeness and next action |
| Your first solution did not work | Explain the original constraint, observed failure, correction and lesson | Actual before/after behavior, not an invented success ending |

When practicing a real disagreement, distinguish your recommendation, the decision owner's authority and the final team choice. A strong contribution story can include a decision you did not win and what you learned from the result.

## 5.10 Sixty rapid-fire questions and answers

### Q1. How do you begin an ambiguous product problem?

Identify the user, task, obstacle, desired outcome and evidence. State uncertain assumptions before proposing a solution.

### Q2. What makes a problem statement useful?

It identifies who struggles with what and why it matters without embedding a required feature as the answer.

### Q3. How do you distinguish a user from a buyer?

Ask who performs the task and who authorizes or pays for the purchase. Their incentives and evidence needs can differ.

### Q4. What is the difference between shipping and success?

Shipping is delivery. Success needs the intended behavior or outcome, appropriate measurement and guardrails.

### Q5. How do you avoid leading user research?

Ask about actual recent tasks, obstacles and workarounds before asking for opinions about your proposed solution.

### Q6. What does RICE leave out?

It does not settle mandatory constraints, dependencies, strategic fit or the truth of uncertain estimates. Use it as a decision input.

### Q7. What is an MVP?

A coherent minimum way to deliver and learn about the intended value. Removing random features can leave an unusable journey.

### Q8. BRD versus PRD?

Business needs and context versus defined product behavior, scope and success conditions. Explain the actual document conventions your team used.

### Q9. What makes a good acceptance criterion?

Observable behavior under specified conditions, including relevant rejection or failure cases. It should be possible to decide whether the check passed.

### Q10. What is a prototype for?

Exploring and testing a flow or interaction before committing to full implementation. A prototype task result is not production adoption evidence.

### Q11. How would you use Figma and Notion here?

Figma can represent flows and interactive prototypes; Notion can organize linked requirements, decisions and evidence. Naming the tool does not establish that a usability test occurred.

### Q12. Why maintain traceability?

To connect requirements, criteria, checks, designs and metrics and identify likely change impact. Link coverage alone does not prove the product works.

### Q13. What is the unit of a price?

State what the customer buys or consumes, such as a credit, job or subscription period. Then connect that unit to variable cost and value.

### Q14. Why can a failed generation still cost money?

Provider execution may consume billable resources before a user-visible success. Meter attempts and define the failure/refund policy.

### Q15. Which costs belong in cost per success?

The defined cohort's relevant cost-bearing work, including failed attempts and retries, divided by successful outcomes. State any excluded costs.

### Q16. Why is known cost different from complete cost?

An observed subtotal can omit unresolved usage or rates. Track missing inputs and withhold a final total when required evidence is incomplete.

### Q17. Margin versus markup?

Margin divides profit by revenue; markup divides the increase by cost. Their percentages have different denominators.

### Q18. Gross margin versus contribution margin?

Gross margin subtracts defined COGS. Contribution subtracts the defined variable-cost scope, which may include additional costs.

### Q19. Why do credits not directly equal cash revenue?

Credits represent an entitlement or consumption unit. Cash collection, discounts, promotions, refunds and accounting treatment need separate definitions.

### Q20. What does break-even assume?

A specified price, variable cost, fixed cost and sales/output model. It is a scenario result, not a demand forecast or cash-flow guarantee.

### Q21. What belongs in a tracking plan?

Event meaning, trigger, actor/entity identity, required properties, schema/version, timestamps, deduplication and a decision it supports.

### Q22. Why distinguish event time from ingestion time?

One determines when behavior occurred; the other describes when it became known. Late data can revise a report without new behavior in that period.

### Q23. What is activation?

A defined initial value milestone for an eligible population and window. A button click is useful only if it meaningfully represents that value.

### Q24. What is retention?

Return under a specified cohort, qualifying activity and period rule. Exact-day, rolling and other definitions are not interchangeable.

### Q25. Why exclude immature cohorts?

They have not had the required opportunity to produce the measured outcome. Including them can bias the denominator.

### Q26. Can two events from one person mean two active users?

No. Define identity resolution and count distinct eligible users rather than raw events when the metric is users.

### Q27. Four percentage points versus twenty percent lift?

A rate change from 20% to 24% is four points and twenty percent relative to the 20% baseline. Say which one you mean.

### Q28. Does a before/after increase prove a feature worked?

No. Timing, population, seasonality, tracking changes and other interventions can explain it. Causal interpretation needs an appropriate design.

### Q29. Why inspect sample-ratio mismatch?

Unexpected assignment proportions can signal problems with assignment or measurement. A favorable outcome estimate does not repair an invalid experiment population.

### Q30. Does statistical significance settle a rollout?

No. Consider experiment validity, effect size, uncertainty, guardrails, costs and the decision's practical consequences.

### Q31. What is data grain?

The meaning of one row. A join can change row multiplicity without changing the underlying business transactions.

### Q32. Why does a left join inflate sums?

Repeated right keys can repeat a left record and its measure. Retention of left records is not a uniqueness guarantee.

### Q33. How do you distinguish a duplicate from a retry?

Use the source identity and version contract. Repeated delivery of one attempt differs from a new attempt with its own identity.

### Q34. Why preserve an ID as text?

It is a label, so leading zeros and exact representation can matter. Numeric inference can change it before a join.

### Q35. Is unknown zero?

Only if the domain establishes that meaning. Otherwise preserve missingness, expose its count and distinguish subtotal from complete total.

### Q36. loc versus iloc?

Label/mask selection versus positional selection. Integer-looking labels still have label semantics with loc.

### Q37. How can Series and array addition differ?

Series align labels while arrays operate by position. Converting to an array removes the label-alignment contract.

### Q38. How should you update pandas rows?

Use one explicit assignment to the intended object, such as loc. P3's pandas 3 example explains Copy-on-Write and why chained assignment does not update the original.

### Q39. Why normalize aware timestamps?

Different text can denote the same instant, and a local date can lie in another reporting month. Apply an explicit business interval after normalization.

### Q40. Why use a half-open interval?

An inclusive start and exclusive end make adjacent periods meet without overlap and avoid guessing the last representable instant of a date.

### Q41. Lookup versus aggregation?

A lookup retrieves an attribute for a match; aggregation summarizes records. One matching attempt is not a job's total retry cost.

### Q42. Why can an Excel report remain stale after recalculation?

Formula evaluation does not automatically establish fresh source extraction, complete ranges or refreshed cached reports. Inspect each dependency.

### Q43. Why not average campaign CTRs?

They can have different impression denominators. Combine compatible clicks and impressions before division.

### Q44. CPA versus CAC?

Cost per defined action versus cost of acquiring a new customer under an explicit cost scope. Repeat purchases and new customers are different populations.

### Q45. ROAS versus profit?

Attributed value per media spend omits other costs. A high ratio can coexist with weak contribution or a misleading attribution allocation.

### Q46. What does an attribution window change?

Eligibility for outcome credit. It can change channel allocation while leaving the order ledger unchanged.

### Q47. Can independent channel totals double count revenue?

Yes. Multiple sources may claim the same order. Exact deduplication requires adequate identities; aggregate totals alone may not reveal overlap.

### Q48. Does unattributed mean organic?

No. Tracking gaps, missing touch history and window rules can also leave an order unassigned.

### Q49. Attribution versus incrementality?

Credit assignment versus estimating the effect of an intervention relative to a counterfactual. A good attribution model is not itself a randomized study.

### Q50. What makes a digest trustworthy?

Complete comparable snapshots, deterministic metrics, visible freshness/missingness, provenance and a reviewable recommendation. Delivery status remains a separate boundary.

### Q51. When do you choose a bar chart?

When readers need direct comparison of magnitudes on a common baseline, especially close values.

### Q52. When is a treemap useful?

For broad composition within a hierarchy using an additive nonnegative quantity. Exact values and small differences need a table or another view.

### Q53. Why can a hierarchy sum double count?

An accessor can contribute a supplied parent total as well as its children. In the P4 example, only leaves contribute spend.

### Q54. Why use stable D3 keys?

They preserve which data identity an element represents across updates. They do not guarantee a fixed layout position or repair duplicate source keys.

### Q55. What should a chart do with missing data?

Explain its absence and preserve an appropriate data alternative. Do not silently draw an unknown value as a known zero.

### Q56. How do you explain ownership in a team project?

Describe your concrete decisions and work, the team's surrounding responsibilities and the evidence for the boundary. Avoid converting commit share into impact share.

### Q57. What if two resume versions disagree?

Keep the values visible, recover the original definition/date/source and explain the resolved distinction. Do not average conflicting route counts or silently choose the larger one.

### Q58. How do you discuss a result you cannot reproduce now?

Identify it as your recorded project claim, explain the mechanism you know and name the missing artifact. Do not substitute a new fixture's result as original evidence.

### Q59. How do you answer a stakeholder-disagreement question?

Use an actual incident: competing goals, your reasoning, the decision process, outcome and lesson. A hypothetical framework is not a past event.

### Q60. What proves this track is complete?

All planned files, links and verification records are authored and integrated. It does not prove original resume impact, completion of manual exercises or personal interview mastery.

## 5.11 Mock A: product and ownership, 45 minutes

**Scenario:** a hypothetical hiring team sees abandoned candidate assessments and wants an AI summary immediately. You must choose the next coherent improvement under limited delivery capacity. No user study or baseline is supplied; ask for or state the evidence needed.

| Minutes | Interview task | Strong answer evidence |
| --- | --- | --- |
| 0–5 | Clarify users, obstacle and goal | Distinguish candidate, HR, buyer and assumptions |
| 5–15 | Plan discovery and scope a minimum journey | Non-leading question, coherent recovery path and exclusions |
| 15–25 | Prioritize and address economics | Constraints, estimates, dependencies and cost-bearing work |
| 25–35 | Define success and an evaluation | Eligible denominator, window, guardrails and causal limits |
| 35–42 | Connect one genuine resume story | Personal action, mechanism, test and evidence boundary |
| 42–45 | Reconsider after contradictory evidence | A specific next check and a reasoned change of decision |

**Follow-up injects:** the highest score assumes unobserved reach; a security fix is mandatory; all criteria are linked but one check is pending; after launch the event schema changes. Explain which decision each inject affects.

## 5.12 Mock B: analyst and reporting system, 45 minutes

**Scenario:** a hypothetical daily digest reports rising revenue and recommends moving budget. A finance export disagrees, one campaign page is missing and the chart uses treemap area for ROAS. Use the executed drills where relevant, without treating their inputs as real business data.

| Minutes | Interview task | Strong answer evidence |
| --- | --- | --- |
| 0–5 | Define the report contract | Grain, units, dates, attribution and as-of time |
| 5–15 | Predict D07 and D09 | Join multiplicity, known subtotal and UTC boundary |
| 15–25 | Reconcile missing money and outcomes | Explicit unresolved rows and compatible populations |
| 25–35 | Interpret D10/D11 and redesign the chart | Weighted denominators, overlap, attribution limits and additive area |
| 35–42 | Design reliable calculation and publication | Complete snapshot, revision, retry and delivery state |
| 42–45 | Recommend the immediate next action | Withhold unsupported scaling, identify the smallest decisive check |

**Follow-up injects:** someone fills blanks with zero; an older worker publishes after a correction; the digest is retried after an ambiguous send; the mobile chart hides labels. Separate diagnosis, proposed repair and evidence needed to confirm it.

### Manual feedback rubric for both mocks

| Dimension | Weak answer | Strong answer |
| --- | --- | --- |
| Definition | Names a metric or framework | States population, unit, contract and assumptions |
| Mechanics | Gives a vague tool list | Traces a concrete calculation or state change |
| Evidence | Treats a claim as proof | Distinguishes recorded facts, computation and missing corroboration |
| Decision | Recommends a feature or spend change immediately | Connects a choice to evidence, constraints and a next check |
| Ownership | Says “we did everything” | Explains personal work and team boundaries |

Ask a peer to interrupt, change an assumption and request a counterexample. These are editorial feedback criteria, not a validated hiring score or automated grade.

## 5.13 Practice tasks and answer checkpoints

1. Create an evidence pack for two genuine resume bullets without adding unsupported outcomes.
2. Give one story at about 30 seconds, two minutes and five minutes; keep the same facts and ownership boundary.
3. Resolve or explicitly catalogue the Datsol title, 10X endpoint and Zyke payment ambiguities.
4. Predict D01–D04, run them, and explain the decision each output can and cannot support.
5. Predict D05–D08 and identify the denominator, grain or missingness trap in each.
6. Predict D09–D12 and distinguish reporting membership, weighted rates, attribution and weighted traffic.
7. Use a real project to write a need, requirement, acceptance criterion and evidence check.
8. Choose four diagnosis cards and state the first discriminating check before proposing a repair.
9. Rehearse a real stakeholder disagreement with your contribution, decision owner and actual outcome.
10. Complete Mock A with a peer and record which assumption changed your answer.
11. Complete Mock B, including the partial-report and duplicate-delivery follow-ups.
12. Use the self-test and exit checklist to choose a targeted revision session rather than rereading everything.

### Answer checkpoints

| Task | Checkpoint |
| --- | --- |
| 1 | Each claim has a source, definition, ownership boundary and unresolved artifact where necessary |
| 2 | Longer answers add mechanisms and trade-offs, not new invented facts |
| 3 | Preserve contradictions until the original title, inventory/date or payment evidence resolves them |
| 4 | RICE is sensitive to estimates; supplied passes are not tests; margin is not markup; failed work has cost |
| 5 | Points differ from percent; maturity changes eligibility; a join can repeat billing; unknown is not zero |
| 6 | UTC affects membership; combine ratio components; attribution changes credit; weighted traffic differs from keys |
| 7 | Each artifact has a distinct role, and the evidence check actually observes the criterion |
| 8 | A hypothesis is tested against an alternative, with a decision that changes if the check disagrees |
| 9 | The story is a real event and separates personal action from the team's final choice |
| 10 | Explain the candidate journey, mandatory constraints, measurement and contradictory evidence |
| 11 | Explain grain, incomplete reporting, attribution, chart semantics and publication/delivery boundaries |
| 12 | Revise the failed concept and demonstrate it again with a changed example |

These tasks are learner work. Authoring and executing the companion does not tick them off for you.

## 5.14 Twenty-four-question self-test

Cover the answer-checkpoint column, answer each question, then compare your explanation with the checkpoint.

| ID | Question | Answer checkpoint |
| --- | --- | --- |
| T01 | Can a need statement name the required chatbot? | That embeds a solution; establish the underlying task and obstacle |
| T02 | Can the top RICE feature override required access safety? | No; model mandatory constraints separately |
| T03 | Does every linked criterion prove readiness? | No; check actual evidence and unresolved decisions |
| T04 | Is a Figma prototype equivalent to a production task? | No; distinguish the observed environment and outcome |
| T05 | Can failed attempts be omitted from cost per success? | Not if they are relevant costs in the selected cohort |
| T06 | Does a positive gross margin establish positive contribution? | Additional variable costs can change contribution |
| T07 | Do consumed promotional credits prove cash received? | No; entitlement and cash events differ |
| T08 | Does a price floor prove customers will pay it? | No; demand needs its own evidence |
| T09 | Why might historical retention rise without new behavior? | Late data, identity resolution or a definition/as-of revision |
| T10 | Is an immature cohort a fair denominator for a later outcome? | It has not had the required observation opportunity |
| T11 | Does a rate rise of four points always mean four percent relative lift? | Relative lift depends on the baseline |
| T12 | Can a favorable metric repair invalid experiment assignment? | No; inspect validity and sample integrity first |
| T13 | Does a left join preserve the number of rows? | Not when matching multiplicity repeats left records |
| T14 | Does a repeated job ID identify a duplicate attempt? | Attempts need their own identity contract |
| T15 | Is an all-missing sum a known zero? | Preserve unknown under an explicitly chosen policy |
| T16 | Does a date-looking Excel string guarantee a numeric date? | No; inspect cell types and normalization |
| T17 | Can two platform ROAS values be averaged directly? | Recompute compatible value/spend components; consider overlap |
| T18 | Does an unattributed purchase establish an organic source? | No; history and rule coverage may be incomplete |
| T19 | Does attribution establish incremental revenue? | No; credit and counterfactual effect answer different questions |
| T20 | Can a missing response page become a recommendation? | Withhold or explicitly qualify the incomplete snapshot |
| T21 | Should a treemap sum campaign ROAS? | No; use an additive nonnegative measure for area |
| T22 | Does a stable D3 key freeze a tile's position? | No; data identity and layout position are separate |
| T23 | Does a local teaching check verify historical resume impact? | No; state its independent source and scope |
| T24 | Does completing this handbook complete the manual mocks? | No; learning readiness requires your own demonstrated practice |

## 5.15 A seven-day revision route

| Day | Focus | Produce before moving on |
| --- | --- | --- |
| 1 | P0 and one ownership story | Problem, minimum scope, criteria and a real contribution outline |
| 2 | P1 and Zyke/economic reasoning | Cost-bearing population, margin explanation and D03/D04 |
| 3 | P2 and measurement | Tracking contract, mature denominator and an experiment limitation |
| 4 | P3 and reconciliation | D07–D09, row-grain explanation and a missing-versus-zero worksheet check |
| 5 | P4 and reporting/visualization | D10/D11, report contract, attribution limit and chart choice |
| 6 | Resume follow-ups and Mock A | Two evidence packs, contradiction list and peer feedback |
| 7 | Mock B and targeted repair | Reproduce failed drills and explain changed assumptions aloud |

The schedule is a suggested sequence, not a measured time-to-mastery promise. If a prerequisite is weak, repeat the relevant worked case before adding more mock questions.

### If only the final day remains

Review the six-section map, your two strongest genuine stories, the thirty confusable pairs and the outputs you previously missed. Practice one product answer and one reconciliation answer under interruption. Check the original definitions behind any number you plan to say. Avoid spending the whole session learning a new framework while leaving your existing claims unexplained.

### Keep a small error log

Record the prompt, your initial answer, the missed assumption, a corrected explanation and a different example you can now solve. “Reread P3” is less useful than “I repeated job-level billing after a one-to-many join; next time I will state the grain and compare unique IDs before summing.”

## 5.16 Research, execution and what remains manual

MIT and Amazon's official preparation material support the use of specific experiences, personal action and structured reflection. The story cards, pair table, diagnosis cards, schedules and mocks are this handbook's editorial exercises; neither source validates their hiring effectiveness or question frequency.

Technical explanations consolidate P0–P4 and their primary-source manifests. The 12 small drills were freshly executed in separate Python processes. The 15 additional checks audit source/coverage relationships and local PDF fingerprints. They do not evaluate spoken answers, original project implementation, actual customer outcomes or a real experiment.

The earlier NumPy/pandas, native Excel and Chrome/D3 checks remain recorded evidence with their original runtime versions and scopes. P5 does not silently relabel them as newly executed or as current production-platform parity.

From the repository root, run:

```powershell
python examples/product-analytics/module-5-consolidation-resume-drills/verify.py
```

The companion README explains the output files and audits. The final website verification covers the entire published handbook and subject-scoped search, and closes its temporary preview. Source resumes remain ignored and local; port 3000 remains stopped.

## 5.17 Exit checklist

- [ ] I can navigate P0–P5 and choose the section that resolves a specific weakness.
- [ ] I can state a user problem before suggesting a feature.
- [ ] I can connect requirements, observable criteria and actual evidence.
- [ ] I can explain prioritization without treating estimates as facts.
- [ ] I can calculate cost per success and distinguish margin from markup.
- [ ] I can separate credits, cash, known cost and complete cost.
- [ ] I can define a metric's population, denominator, time and as-of policy.
- [ ] I can distinguish activation, mature retention and experiment validity.
- [ ] I can predict and explain the twelve executed drills.
- [ ] I can diagnose join multiplicity, missing values and timezone boundaries.
- [ ] I can explain Excel lookups, aggregation, refresh and the manual PivotTable exercise.
- [ ] I can reconcile platform credit with canonical order values and causal limits.
- [ ] I can explain D3 scales, stable keys, chart choice and additive treemap area.
- [ ] I can give an accurate short and expanded account of two genuine resume experiences.
- [ ] I can identify the source and unresolved details behind each quantified claim I use.
- [ ] I can describe a real disagreement or failure without inventing a success ending.
- [ ] I have attempted both mocks and corrected the assumptions I missed.
- [ ] I can separate authored completion from my own demonstrated learning readiness.

**The planned Product and Analytics handbook is fully authored:** the roadmap, P0–P4 teaching chapters and P5 consolidation. Continue with manual practice, evidence recovery and targeted revision using the [master roadmap](/docs/product-analytics).
