# Product and Analytics Casebook — Part 9: Consolidation and Mocks

**Explain a conditional recommendation and the evidence that could overturn it.**

## 1. Twenty confusable pairs

| Pair | Distinction |
| --- | --- |
| User / buyer | Person experiencing the task versus who funds or chooses the service |
| Need / feature request | Desired task outcome versus one proposed implementation |
| Output / outcome | Delivered work versus a change for users or the business |
| Supplied fact / verified real evidence | An interview premise versus an inspected source claim |
| Hypothesis / diagnosis | A possible explanation versus one supported by discriminating evidence |
| Observed difference / causal effect | Description versus a counterfactual intervention claim |
| Forecast / scenario | A future estimate requiring validation versus an explicit conditional calculation |
| Primary outcome / diagnostic | The target result versus a measure that helps explain it |
| Guardrail / universal rule | A declared decision constraint versus an assumed policy for every product |
| RICE score / validated value | Arithmetic over estimates versus established user/business benefit |
| Passing criteria / user benefit | Behavioral evidence versus an achieved product outcome |
| Mix change / within-segment change | Different population weights versus different segment rates |
| Event receipt / business event | A delivered report versus the underlying event identity |
| Mature nonreturner / immature user | Full opportunity with no observed return versus an unfinished window |
| Credit / provider call | Customer entitlement unit versus a potentially separate cost-generating attempt |
| Revenue / selected contribution | Named inflow measure versus inflow after explicitly selected costs |
| Attribution / incrementality | Credit under a rule versus what would happen without the intervention |
| Total supply / compatible capacity | Headline availability versus usable service in the required cell |
| Precision / recall | Correct alerts among alerts versus caught positives among actual positives |
| Grounding / authorization | Support from a source versus permission to use that source for this requester |

## 2. Twelve diagnosis cards

| ID | Situation | First useful check |
| --- | --- | --- |
| D01 | A stakeholder starts with a preferred feature | Reconstruct the user, blocked task and evidence |
| D02 | A score is treated as the roadmap decision | Inspect assumptions, sensitivity and mandatory constraints |
| D03 | A forecast is called a promised outcome | Identify its response and invariance assumptions |
| D04 | Overall conversion falls | Verify definition/maturity, then separate mix and segment rates |
| D05 | Event totals exceed business totals | Reconcile identities, source grain and receipt duplication |
| D06 | More clicks produce fewer useful outcomes | Check the task definition and both denominators |
| D07 | New-cohort retention looks weak | Inspect full qualifying windows and knowledge cutoffs |
| D08 | A discount is justified by volume | Compare unit contribution and required incremental volume |
| D09 | CAC looks excellent only in one dashboard | Reconcile spend, identity, attribution and acquisition stage |
| D10 | Supply grows but fulfillment does not | Inspect compatibility and post-match failure in each cell |
| D11 | A strong experiment result has unequal arms | Compare assignment counts with verified configured allocation |
| D12 | A launch wins averages but violates a critical requirement | Inspect the actual failure and predeclared gate separately |

These cards start an investigation. None establishes a real root cause or authorizes changing a production system.

## 3. Thirty oral checks

| ID | Interview question | Answer checkpoint |
| --- | --- | --- |
| O01 | How do you start an ambiguous product case? | Define a user, task, objective, constraints and critical uncertainty |
| O02 | When should you stop clarifying? | When a reasonable working assumption lets you make useful progress |
| O03 | What makes discovery useful? | It changes a decision by resolving a material uncertainty |
| O04 | Can no build be a good answer? | Yes, when evidence and opportunity cost support it |
| O05 | What does a RICE score verify? | The declared estimate arithmetic, not realized value |
| O06 | Why show confidence sensitivity? | Plausible inputs can reverse the ranking |
| O07 | Does criterion pass coverage establish accessibility? | No; it is a local evidence count, not conformance or user-outcome proof |
| O08 | What is a useful metric contract? | Population, unit, numerator, denominator, window, identity and source policy |
| O09 | What can a mix decomposition explain? | The supplied aggregate movement under its declared segments and weights |
| O10 | Does standardization identify a causal effect? | Not by itself; variable timing and design matter |
| O11 | Why separate event and delivery identity? | Retries can report the same business event more than once |
| O12 | What does an unresolved source gap mean? | A remaining reconciliation question, not invented zero or invented revenue |
| O13 | Why can CTR be misleading? | Extra clicks may reflect friction rather than useful task completion |
| O14 | Does the biggest funnel loss set priority? | No; need, addressability, value, effort and downstream effects matter |
| O15 | Why use mature cohorts? | Included users need comparable defined opportunities to generate outcomes |
| O16 | What can later receipts change? | Knowledge of behavior within an unchanged historical period |
| O17 | Why can positive short-run contribution still fail a decision? | Critical guardrails or unmodeled longer-term harms can matter |
| O18 | Why do failed AI attempts belong in cost? | They can consume resources without consuming a useful-job credit |
| O19 | Is a cost floor a market price? | No; willingness to pay and demand remain unverified |
| O20 | What does the discount multiplier preserve? | Baseline selected contribution under its stated unchanged-cost scenario |
| O21 | Why is LTV unavailable in C12? | Future contribution, retention and horizon evidence are missing |
| O22 | Is attributed acquisition necessarily incremental? | No; allocation of credit differs from a causal counterfactual |
| O23 | Why segment marketplace availability? | Matching requires compatible time, geography, skill and terms |
| O24 | What is missing from a fluid capacity model? | Stochastic variation, routing, reopens and other real flow complexities |
| O25 | Why can precision improve while policy value falls? | Lower recall and harm/cost changes can outweigh saved reviews |
| O26 | Does SRM identify the logging defect? | No; it flags an allocation discrepancy with several possible causes |
| O27 | Does an SRM pass certify an experiment? | No; outcomes, dependence, stopping and other validity conditions remain |
| O28 | Why use all-question AI usefulness as well as answered-only quality? | Selective answering changes the conditional denominator |
| O29 | Can grounding compensate for unauthorized retrieval? | No; support and requester permission are separate requirements |
| O30 | Why can a pooled SLO hide a failing canary? | A large healthier batch can dilute version-specific harm |

## 4. Mock A: design, prioritization and economics, 45 minutes

**Prompt:** a hypothetical hiring product wants to improve completion and launch an AI assistance package before a deadline. Capacity is limited and the team disagrees about what to prioritize.

| Minutes | Task | Evidence of a strong answer |
| --- | --- | --- |
| 0–5 | Clarify user, task and scope | Distinguishes candidate, recruiter and buyer |
| 5–13 | Work C01 or C03 | Separates a blocked task from the proposed feature |
| 13–21 | Handle C02 priorities | Shows estimate sensitivity and explicit trade-offs |
| 21–31 | Work C10 or C11 | Names the selected cost model and conditional demand assumptions |
| 31–39 | Explain requirements and engineering | Ownership, acknowledgement, failure behavior and evidence |
| 39–45 | Accept a changed assumption | Updates the recommendation and names the next check |

**Answer checkpoints:** forecast recovery is not verified impact; a RICE lead does not remove constraints; a critical failure does not become a pass because a forecast is attractive; a cost floor does not establish willingness to pay. Use the corresponding case outputs for arithmetic and defend judgment separately.

## 5. Mock B: investigate and make a launch decision, 45 minutes

**Prompt:** an AI-enabled marketplace reports falling conversion but improving clicks. A new model and canary appear promising, while the reports use different denominators and cutoffs.

| Minutes | Task | Evidence of a strong answer |
| --- | --- | --- |
| 0–6 | Define the reported measures | Population, identity, window and source contract |
| 6–16 | Work C04/C05 or C08 | Demonstrates mix, reconciliation or maturity rather than guessing a cause |
| 16–24 | Evaluate task usefulness | Explains C06/C07 and competing user-value hypotheses |
| 24–32 | Handle assignment and quality | Uses C16/C17 without treating fixture labels as real verification |
| 32–39 | Evaluate the canary | Uses overlap and version-specific evidence from C18 |
| 39–45 | Communicate the decision | Conditional action, owner, evidence gap and review trigger |

**Answer checkpoints:** descriptive adjustment does not identify causality; assignment configuration must be verified independently; average quality cannot cancel an access failure; earlier healthy traffic cannot justify a canary that fails the supplied gate.

The mocks are editorial practice formats, not observed company processes. Alternate recommendations are welcome when they use the evidence and constraints coherently.

## 6. Review rubric without a fake automatic score

Assess whether the answer defines a coherent target, asks decision-relevant questions, names assumptions, calculates correctly, compares feasible options, addresses customer costs and explains what evidence would change the recommendation. Look for requirements and architecture that serve the behavior rather than gratuitous tool names.

Record one concrete strength, one unsupported claim and one better next check. Do not grade only whether the learner picked the same feature as the worked recommendation. The runtime checks cannot assess empathy, stakeholder communication or the wisdom of a real trade-off.

## 7. Seven-day practice route

| Day | Work | Produce |
| --- | --- | --- |
| 1 | Method and C01–C03 | A one-page decision memo and revised scope |
| 2 | C04–C06 | A reproducible metric contract and hypothesis tree |
| 3 | C07–C09 | A mature-cohort explanation and a guardrail decision |
| 4 | C10–C12 | Explicit cost, acquisition and future-value assumptions |
| 5 | C13–C15 | A compatible-capacity model and policy trade-off |
| 6 | C16–C18 and Mock A | A trustworthiness review and feedback |
| 7 | Mock B and targeted repair | One changed-assumption answer for a missed concept |

The schedule suggests an order, not a measured learning-time promise. Keep the original prompt, your answer, the assumption you missed and a different example that demonstrates the correction.

## 8. Exit checklist

- [ ] I define a user, task and outcome before proposing features.
- [ ] I distinguish evidence, hypothesis, scenario and decision policy.
- [ ] I can write a metric contract with complete observation opportunities.
- [ ] I compare feasible alternatives and their opportunity costs.
- [ ] I can explain a mix change without inventing a release cause.
- [ ] I reconcile identity, grain, late data and unresolved source gaps.
- [ ] I state the assumptions behind pricing, cost and payback calculations.
- [ ] I reason about compatible capacity and useful completion.
- [ ] I separate prediction quality from actual harm and intervention value.
- [ ] I check assignment and critical gates before defending a launch.
- [ ] I connect requirements to necessary engineering properties.
- [ ] I have attempted both mocks and revised an answer after new evidence.

The casebook is fully authored. Continue manual practice from the [roadmap](/docs/product-casebook), [SQL lab](/docs/sql-interview), [statistics handbook](/docs/probability-statistics) or [actual resume story drills](/docs/product-analytics/consolidation-resume-drills).
