# Product and Analytics Placement Handbook — Part 4
# P2: Product Analytics and Experiments

**P2 · 4–5 hours plus practice · Tier 1 for product/analytics interviews · Requires: P0; basic percentages; P1 for cost guardrails**

---

## Why this module matters

“Conversion improved by 20%” raises several questions. Which conversion? Twenty percent relative change or twenty percentage points? Did the denominator change? Were recent users given enough time? Was tracking changed? What establishes that the feature caused the result?

Product analytics measures behavior so a team can investigate a problem and assess a decision. An experiment adds an intervention and an assignment design intended to support a causal comparison. A dashboard does not supply that design by itself.

> **A metric is a contract about events, identity, population, time and calculation—not just a number with a name.**

This chapter builds that contract, runs a local event worksheet, and explains the limits of the resulting comparisons. It also places PostHog, GA4 and Microsoft Clarity in a practical investigation workflow.

**Verification:** **95 local checks passed** on Python 3.13.15 with SQLite 3.50.4. Actual local SQL processes invented events, duplicates, aliases, ordered steps, mature cohorts and late arrivals. Separate synthetic counts exercise normal-approximation and sample-ratio arithmetic. No vendor account, real customer telemetry or randomized deployment was used.

## 2.1 What questions does product analytics answer?

| Question | Useful analysis | What it does not establish alone |
| --- | --- | --- |
| Where do users stop? | A defined funnel | Why they stop |
| Do new users reach value? | Activation and time-to-value | Long-term retention |
| Do they return? | Cohort retention | Whether a feature caused the return |
| Which segments differ? | Breakdowns under consistent definitions | A causal explanation for the difference |
| What happens in the interface? | Paths, recordings and heatmaps | Population prevalence from a few selected recordings |
| Did the intervention help? | A trustworthy experiment or another justified evaluation design | Universal impact outside the studied population |

Begin with a decision. “Which part of onboarding should we investigate?” is more useful than “build a dashboard with every available chart.”

### Outcome, input, diagnostic and guardrail metrics

| Role | Teaching example | Use |
| --- | --- | --- |
| Outcome | Teams repeatedly producing usable content | Approximate the desired product value |
| Input/leading indicator | Eligible users completing onboarding | Identify an earlier behavior that may support the outcome |
| Diagnostic | Generation-start-to-success conversion | Locate a possible failure mechanism |
| Guardrail | Cost per successful output, harmful errors or support burden | Detect an unacceptable trade-off |

A “north star” is a chosen summary of value, not a special formula that every product must share. Count meaningful use rather than selecting a large activity number because it looks good.

## 2.2 Events, properties, users and sessions

An event records that something happened under a declared meaning. Properties describe relevant context. A user identifier groups activity belonging to the chosen person/account entity. A session groups interactions under a sessionization rule.

| Concept | Example | Common confusion |
| --- | --- | --- |
| Event | generation_succeeded | A click does not prove the output was produced |
| Event property | device=mobile | A property is context, not automatically another event |
| User/person | Canonical user u1 | Anonymous and authenticated identifiers may refer to one person |
| Operation | Generation job op1 | One user can start many operations |
| Session | A vendor-defined visit grouping | One session is not one customer or one completed action |
| Account/workspace | A team using the product | Person-level and account-level retention answer different questions |

One person can trigger many events, sessions and jobs. A chart of event counts cannot be relabelled as unique users without changing the calculation.

### Client intention versus authoritative outcome

```text
click "Generate" -> request accepted -> provider work -> usable output persisted
       |                  |                                 |
       v                  v                                 v
 UI intent event    operation-start event             success event
```

Client events help explain interface behavior. Backend/worker events can establish a committed product outcome when emitted at the right point. Neither is automatically complete: browser collection can be blocked, and a backend can commit without publishing its analytical event.

The [S13 analytics pipeline](/docs/system-design/analytics-event-pipeline) explains reliable ingestion and replay. Here we focus on what the events should mean and how the reports use them.

## 2.3 Build a tracking plan before collecting everything

A tracking plan connects a product question to a small vocabulary of events and properties. It should include ownership, emission point, identity, schema version and verification cases.

### Teaching plan

| Event | Emit after | Required identity | Why collect it? |
| --- | --- | --- | --- |
| signup_completed | Backend signup commit | Canonical user or an explicitly linked alias | Cohort anchor |
| generation_started | Backend accepts an operation | User and operation ID | Attempted product action |
| generation_succeeded | Worker persists usable output | User and operation ID | Successful action and return behavior |

The fixture accepts version 1 and allowlisted device/plan values. It rejects unknown event names, schema versions, identity links and property values. It is a teaching contract for structured input, not a complete general-purpose event-schema platform.

One exact input record is:

```json
{
  "id": "s1",
  "subject": "anon-1",
  "name": "signup_completed",
  "occurred_at": "2026-10-01T00:00:00Z",
  "received_at": "2026-10-01T00:00:00Z",
  "operation": null,
  "version": 1,
  "properties": {"device": "mobile", "plan": "free"}
}
```

The declared alias map links anon-1 to u1. This is not an instruction to guess identity from an IP address, device name or similar-looking email.

### An event checklist

- What exact behavior causes emission, and can it fire more than once?
- Which entity is being measured: person, invitation, workspace or operation?
- Which ID survives a delivery retry?
- Which timestamp describes the action, and which describes arrival?
- Which properties are necessary for a defined question?
- Which internal/test traffic is excluded, and how is that verified?
- Who owns the definition and its version changes?

Keep sensitive content out of event payloads when it is unnecessary. A useful generation event does not need a private prompt, document body, password or payment credential to establish a count.

## 2.4 Identity and deduplication

### Two distinct identity problems

| Problem | Example | Required reasoning |
| --- | --- | --- |
| Delivery duplication | The same success event is retried | Use stable event identity; do not count it twice |
| Person fragmentation | Anonymous signup and authenticated use have different IDs | Apply an explicit, justified identity link |

The fixture stores 28 unique events from 29 input reports. One repeated c1 report is ignored analytically. If a repeated event ID contains conflicting business content, ingestion rejects it rather than silently choosing a version.

Receipt time may differ across identical deliveries; the earliest known receipt is retained. Event content is compared after timestamp normalization and explicit alias resolution.

### Avoid merging different people

Sharing a device, browser or network does not prove two accounts are the same person. Conversely, a person can use several devices. Identity policy affects both numerator and denominator, so document it alongside the metric.

PostHog describes linking anonymous and identified activity through a stable distinct identifier. The fixture uses a small declared map instead of implementing that vendor's person-processing system. [PostHog: identifying users](https://posthog.com/docs/getting-started/identify-users).

Reset/logout behavior and shared-device use need particular attention in an actual implementation. A successful SDK installation does not prove identity stitching is correct.

## 2.5 Time: occurrence, arrival and observation maturity

Three clocks answer different questions:

| Time concept | Meaning | Teaching policy |
| --- | --- | --- |
| Occurrence time | When the action happened | Aware whole-second timestamp, normalized to UTC |
| Receipt time | When collection learned of the event | Earliest known receipt of a matching event |
| Observation cutoff | How far product behavior has been observed | Events before 11 October 2026 at 00:00 UTC |

The worksheet also uses a **knowledge cutoff**: which received records may be used in that report revision. This lets us reproduce an initial report and a later backfill while holding the product observation window fixed.

```text
behavior window ends:    11 Oct 00:00 UTC
initial knowledge:      records received by 11 Oct 00:00 UTC
revised knowledge:      records received by 13 Oct 00:00 UTC

one return occurred:     9 Oct 10:00 UTC
that return arrived:    12 Oct 00:00 UTC
```

The event belongs to the behavior window but was unknown to the first report. Its later inclusion changes the report without implying new user behavior in that already closed period.

### Half-open windows

The fixture's activation window is `[signup, signup + 24 hours)`. An event exactly at the upper bound does not count. Exact D7 return is `[signup + 7 days, signup + 8 days)`.

These are elapsed UTC windows, not a claim about any vendor's default calendar-day convention. Match the intended definition and timezone before comparing a dashboard with a query.

### Do not call unfinished follow-up a failure

A user who signed up twelve hours before the cutoff has not had a full 24-hour conversion window. Excluding only unfinished non-converters while keeping recent converters would bias the report.

For the final activation rate here, **all users without complete follow-up are excluded**, including one who already converted. A separate preliminary view can be useful, but it must be labelled differently.

## 2.6 Funnels: define order, window and unit

A funnel counts entities progressing through specified steps. State whether the funnel is open or closed, the aggregation unit, step order and conversion window.

This chapter uses a **closed user funnel** anchored on the earliest visible signup in the fixture:

```text
signup_completed -> generation_started -> generation_succeeded
    user u              operation op              same op
```

Other events may occur between the steps. Completion must follow a start for the same operation, within 24 hours of signup. Equal whole-second start/success timestamps are treated as nondecreasing order.

PostHog supports funnel order and conversion-window controls; its strict-order mode differs from allowing unrelated events between steps. Align the chosen settings with the question. [PostHog funnels](https://posthog.com/docs/product-analytics/funnels).

### The seven-user fixture

| User | Relevant behavior | Activation treatment |
| --- | --- | --- |
| u1 | Valid start and success after signup | Counts |
| u2 | Success at 25 hours | Outside the activation window |
| u3 | Starts without a success | Does not complete |
| u4 | Success exactly at 24 hours | Excluded by the upper boundary |
| u5 | An orphan early success, then a valid started operation | Only the valid ordered operation counts |
| u6 | Recent signup and an early success | Excluded from the final rate: follow-up incomplete |
| u7 | Recent signup without a start | Excluded from the final rate: follow-up incomplete |

Internal staff activity is stored but excluded. A later future-dated event in the stored fixture is outside the observation cutoff and cannot affect the snapshot.

### Actual funnel output

```json
{
  "eligible": 5,
  "immature_excluded": 2,
  "started": 5,
  "completed": 2,
  "rate_pct": "40.000000",
  "start_to_complete_pct": "40.000000"
}
```

```text
five mature signups -> five users start -> two users complete
                                   overall conversion: 2 / 5
```

Step conversion and overall conversion use different denominators in general. They happen to match for the final step here because every eligible user started. Do not assume that equality in another funnel.

### Why independent event counts fail

Counting distinct users who ever signed up, ever started and ever succeeded can include unrelated or reversed actions. The local SQL checks time and operation linkage, not just the presence of three event names.

Run from the repository root:

```powershell
python -X utf8 examples/product-analytics/module-2-analytics-experiments/analytics.py
python -X utf8 examples/product-analytics/module-2-analytics-experiments/verify.py
```

## 2.7 Activation: an observable first-value hypothesis

Activation is a defined early behavior intended to represent a user reaching useful value. It is not universally the same as signup, a page view or paying.

For the teaching product, the activation proxy is a correctly ordered first successful output within 24 hours. That is an explicit design choice. It is not proof that the user liked the output or will retain.

### Choosing an activation event

1. Explain the user value the behavior represents.
2. Define the entity and observation window.
3. Make the event observable and its instrumentation reliable.
4. Inspect whether it is associated with later useful behavior.
5. Investigate mechanisms and interventions rather than treating association as causation.

“Users who activate retain better” can reflect motivation, prior experience or selection. It does not prove that forcing a click on the activation event will improve retention.

Time-to-value can help locate friction, but the median among completed users excludes people who never completed. Describe censoring and non-completion alongside timing summaries.

## 2.8 Cohorts and retention

A cohort groups entities by a shared start condition or characteristic. Retention asks whether members return under a specified definition and follow-up period.

### Define all of these

| Choice | Teaching definition |
| --- | --- |
| Entity | Canonical non-internal user |
| Anchor | Earliest visible signup in the fixture |
| Return event | generation_succeeded |
| Interval | Elapsed day 7: from 7 through less than 8 days after signup |
| Denominator | Users with that full interval observed |
| Repeat actions | At least one qualifying return per user |
| Cohort display | Signup calendar date in UTC |
| Report revision | Fixed behavior cutoff, explicit receipt/knowledge cutoff |

The fixture's history is finite. In production, “first ever signup” requires an authoritative historical rule; the first row visible after filtering is not automatically the first event in a person's lifetime.

### Actual revised D7 report

```json
{
  "day": 7,
  "eligible": 5,
  "returned": 3,
  "rate_pct": "60.000000",
  "cohorts": {
    "2026-10-01": {"eligible": 3, "returned": 1, "rate_pct": "33.333333"},
    "2026-10-02": {"eligible": 2, "returned": 2, "rate_pct": "100.000000"}
  }
}
```

Combine cohort counts when calculating the overall user-level rate: three returned out of five eligible. A simple unweighted mean of the displayed percentages answers a different question and ignores the different cohort sizes.

### Exact-period versus on-or-after retention

Exact D7 requires a return in the specified day-7 interval. On-or-after D7 includes a later return under the report's follow-up boundary. A user returning on day 9 can count in the latter but not exact D7.

PostHog distinguishes exact-period and on-or-after retention, along with cohort and reference settings. Do not compare two “D7” numbers without matching those definitions. [PostHog retention](https://posthog.com/docs/product-analytics/retention).

The executable worksheet implements exact-period retention only. It does not silently substitute an observed-so-far rolling measure for a completed follow-up period.

### Retention among which users?

Signup-cohort retention and activated-user retention have different denominators. Comparing them can be informative, but selecting users based on a behavior can also select a more motivated group.

For a B2B tool, workspace retention may be more relevant than person retention if team members rotate. Choose the unit that fits the product question and billing/value model.

## 2.9 Late data and dashboard revisions

The same fixed D7 population yields:

| Report | Eligible users | Known returned users | D7 retention |
| --- | ---: | ---: | ---: |
| Initial knowledge cutoff | 5 | 2 | 40.000000% |
| Revised knowledge cutoff | 5 | 3 | 60.000000% |

The late u5 return occurred before the behavior cutoff but arrived after the first report. The product did not improve between these two calculations; the report learned about an existing action.

### Useful metadata on a metric card

- Definition/version and aggregation unit.
- Observation period and timezone.
- Cohort maturity rule.
- Included population and exclusions.
- Data freshness/completeness and backfill status.
- Filter, identity and attribution settings where relevant.

In this worksheet, empty denominators produce `null`, not an automatic zero. “No eligible cohort” and “an eligible cohort with no returns” are different observations.

## 2.10 Active users, event counts and stickiness

An active user is someone who performed a defined qualifying action in a period. Define that action; merely loading a page may not represent product value.

On 8 October in the fixture, two successful-generation events belong to one user. The actual activity output is **events=2, active_users=1**. Event count and active-user count measure different things.

DAU, WAU and MAU require explicit daily/weekly/monthly windows. A DAU/MAU ratio can describe frequency under compatible definitions; it is not automatically retention or proof of product-market fit.

Retention asks whether a cohort returned. A frequency/stickiness view asks how often qualifying activity occurs. Use the analysis that matches the decision.

## 2.11 PostHog, GA4 and Microsoft Clarity

These tools overlap. The table describes useful emphases rather than claiming exclusive capabilities.

| Tool | Useful emphasis | How to use it in this investigation |
| --- | --- | --- |
| PostHog | Product events, funnels, cohorts and retention | Model signup-to-value progression with explicit identity and windows |
| GA4 | Event-based web/app measurement and acquisition context | Investigate traffic sources, events and important outcomes under GA4 definitions |
| Microsoft Clarity | Recordings and heatmaps | Inspect interface behavior around a suspected failure point |

### PostHog: define the insight rather than trust a chart title

For the teaching funnel, select the three events, a user aggregation, appropriate order, a 24-hour window and the relevant population. Check the treatment of incomplete periods.

For retention, align the start event, return event, exact/on-or-after mode, cohort reference and time boundaries. The fixture is an independent SQL implementation of its stated rules, not a PostHog SDK or a claim of output parity under default settings.

### GA4: event versus key event

GA4 records events and parameters. Marking an event as a key event identifies an outcome important to the business; it does not make the event a verified payment or a causal result. GA4's key-event terminology and Google Ads conversion terminology are related but distinct. [GA4 events](https://support.google.com/analytics/answer/9356037?hl=en), [key events and conversions](https://support.google.com/analytics/answer/13965727?hl=en).

When reconciling reports, inspect user/session scope, event/key-event counting settings, identity, timezones and filters. “Key events divided by sessions” is not necessarily the same as “sessions containing a key event divided by sessions.”

Do not equate a vendor's engaged-session definition with your product's activation definition. A session can satisfy a platform engagement rule without producing a usable customer result.

### Clarity: investigate how the interaction unfolded

A recording can reveal hesitation, repeated clicks or a confusing error state. A heatmap aggregates selected interactions over pages and devices. Neither makes a few selected sessions representative of all users. [Clarity recordings](https://learn.microsoft.com/en-us/clarity/session-recordings/recordings-overview), [Clarity heatmaps](https://learn.microsoft.com/en-us/clarity/heatmaps/heatmaps-overview).

Start with a defined segment and question, inspect relevant sessions, form a hypothesis and validate it with suitable evidence. A repeated click can indicate friction, but it does not uniquely identify its cause.

### Privacy and collection coverage

Define necessary properties, minimize sensitive data, and apply the organization's consent, masking and access policies before collecting real sessions. Clarity documents masking and consent controls; selecting a default is not evidence that your particular page or organization is correctly configured. [Clarity masking](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-masking), [Clarity consent mode](https://learn.microsoft.com/en-us/clarity/setup-and-installation/consent-mode).

Blocked collection and consent choices can change the observed population. A difference between tools may reflect coverage as well as behavior. No tracking SDK was installed in the study website while writing this chapter.

## 2.12 Correlation, before/after comparisons and causality

Suppose users who save a draft finish more applications. They may be more motivated, have more complex applications or use a different device. The association does not isolate the effect of saving.

Suppose conversion rises after a release. Traffic mix, seasonality, a concurrent campaign, eligibility changes, instrumentation and observation maturity could also explain the rise.

### A causal question is a comparison against an alternative

“What would the same eligible population have done without the intervention?” cannot be answered by observing both outcomes for the same person at the same moment. A valid randomized design makes treatment and control comparable in expectation under its assumptions.

Randomization does not make every realized sample identical, eliminate all bugs or guarantee external validity. The assignment process, measurement and analysis still need scrutiny.

## 2.13 Plan an experiment before looking for a winner

Write a short experiment contract:

| Item | Teaching example or question |
| --- | --- |
| Hypothesis | A clearer start-to-result flow improves mature activation |
| Population | Eligible new non-internal users under a stated rule |
| Randomization unit | User, or workspace if users influence each other |
| Assignment | Stable allocation with recorded experiment/version |
| Primary outcome | Defined conversion over a complete window |
| Guardrails | Cost, errors, quality and support burden |
| Decision threshold | Practical effect worth shipping and statistical method |
| Duration/sample plan | Based on baseline, detectable effect, uncertainty and traffic |
| Analysis | Declared population, exclusions, variance unit and stopping rule |

### Assignment is not exposure

An assigned user may never see the changed screen. An intent-to-treat comparison follows assignment and measures the effect of offering the treatment under that design.

Filtering to exposed users can answer another question, but exposure may itself be affected by treatment. Post-treatment filtering can destroy comparability. Define triggered analyses carefully instead of dropping inconvenient users after inspecting outcomes.

### Match the randomization and analysis unit

If a whole workspace receives the same version, its members are not independent user-level randomized units. Shared state and collaboration can create interference. Design and uncertainty calculations should account for the chosen unit and dependence.

A deterministic hash can make assignment stable, but stability alone does not prove correct randomization, eligibility or absence of contamination.

## 2.14 Observed lift: percentage points versus percent

The separate synthetic experiment has:

| Variant | Assigned units | Converted units | Observed rate |
| --- | ---: | ---: | ---: |
| Control | 1,000 | 200 | 20.000000% |
| Treatment | 1,000 | 240 | 24.000000% |

```text
absolute difference = 24% - 20% = 4 percentage points
relative lift       = (24% - 20%) / 20% = 20%
```

These are observed differences in invented aggregate counts. They do not establish that an actual product intervention worked.

### Approximate uncertainty calculation

For two independent binary-outcome groups, the worksheet computes a normal-approximation interval for the difference using the unpooled standard error:

```text
SE = sqrt(pT*(1-pT)/nT + pC*(1-pC)/nC)
approximate 95% interval = (pT-pC) +/- z0.975*SE
```

Its two-sided equality test uses the pooled proportion under the null, following the large-sample two-proportion approach described by NIST. The interval and test use different variance estimates and need not agree exactly near a decision boundary. [NIST: difference of proportions](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/diffprop.htm).

An exact projection of the actual output is:

```json
{
  "control_rate_pct": "20.000000",
  "treatment_rate_pct": "24.000000",
  "absolute_lift_pp": "4.000000",
  "relative_lift_pct": "20.000000",
  "normal_approximation_adequate_for_fixture": true,
  "approx_95_ci_pp": ["0.373272", "7.626728"],
  "two_sided_p_value": 0.030837167828904336,
  "assignment_verified": false
}
```

The interval is expressed in **percentage points**, not raw fractions or relative lift. The program labels assignment unverified because aggregate counts cannot demonstrate a real assignment process.

### Approximation limits

This worksheet withholds the normal interval/test unless each group's observed successes and failures are at least ten. That is an explicit teaching guard for the approximation, not a guarantee of independence, correct assignment or valid inference.

For sparse outcomes, dependence, heavy-tailed metrics or complex assignment, use a method suited to that setting. The fixture does not implement exact tests, cluster-robust inference, bootstrap design or sequential testing.

## 2.15 Interpreting p-values, intervals and practical effect

A p-value is calculated under a null model and its assumptions. It is not the probability that the feature is bad, that the null is true, or that a result will replicate.

A frequentist 95% interval describes the long-run coverage of its procedure under assumptions. It is not a posterior probability that this fixed unknown effect lies inside this particular interval.

### Statistical evidence is not the whole shipping decision

- Compare the estimated effect and uncertainty with the minimum worthwhile practical effect.
- Inspect guardrails and the cost of maintaining the intervention.
- Check measurement, assignment, exposure and observation maturity.
- Respect the declared analysis and stopping plan.
- Explain what population and duration the evidence covers.

The synthetic interval excludes zero, but the chapter supplies no real deployment or causal verification. Even a valid positive experiment can be commercially unattractive if it increases expensive low-quality usage.

### Power, detectable effect and sample size

Power concerns the probability of detecting an effect of a specified size under a stated design and decision rule. Minimum detectable effect, baseline rate, variance, allocation and sample size are related.

“Run for a week” is not a universal sample-size plan. A small experiment can be inconclusive; lack of significance does not prove equivalence. An equivalence/non-inferiority question requires its own planned margins and method.

## 2.16 Peeking, multiple comparisons and sample-ratio mismatch

### Repeatedly checking for significance

Running an ordinary fixed-horizon test every hour and stopping the first time it looks significant changes its error properties. Define the stopping rule or use a valid sequential method.

Monitoring safety and data quality can still be necessary. Distinguish operational stopping rules from an unplanned search for a favorable outcome. The worksheet performs one descriptive fixed-count calculation and does not implement a monitoring policy.

### Looking at many metrics or segments

If many comparisons are explored, some can look favorable by chance. Predeclare primary metrics, handle multiplicity appropriately, and label exploratory findings as hypotheses needing confirmation.

Post-hoc segment selection can also create misleading stories. A segment effect needs a suitable interaction/comparison analysis, not merely significance in one subgroup and non-significance in another.

### Sample-ratio mismatch, SRM

SRM compares the observed assignment counts with the planned allocation. A large discrepancy can reveal assignment, eligibility, logging or filtering problems. It is a data-quality diagnostic; it does not identify the cause by itself. [Microsoft Research: diagnosing SRM](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/).

For a planned 50/50 split, the fixture's separate imbalanced example has 1,000 control and 600 treatment assignments. Its two-category chi-square statistic is **100.0**, with approximate p-value **1.5239706048320992e-23**.

The declared teaching flag uses p less than 0.001 and fires for that example. If the planned treatment share were instead 0.375, those counts would match the allocation and the statistic would be zero. Always use the actual planned ratio.

A balanced sample does not prove randomization was correct. An SRM flag requires investigation before trusting an effect estimate; the program does not automatically repair the data.

## 2.17 Diagnose a conversion drop in a useful order

```text
reported drop
   |
   +-> definition/window/population changed?
   |
   +-> events missing, duplicated or late?
   |
   +-> identity, consent or internal-filter coverage changed?
   |
   +-> traffic mix or eligibility changed?
   |
   +-> stage/segment where valid behavior changed?
   |
   +-> evidence for a mechanism; intervention and evaluation
```

Reproduce one metric from its underlying records. Compare identical cohorts/windows and inspect the affected step. Use recordings or interviews to investigate a plausible mechanism, then evaluate a proposed change with appropriate evidence.

For this fixture, an analyst who compared initial and revised retention without receipt metadata could wrongly announce a large improvement. An analyst who counted recent users as failures could wrongly diagnose worse onboarding.

## 2.18 Resume connection and honest evidence

If your resume claims a funnel, dashboard or product improvement, prepare the metric contract and one reproducible path from records to result. Explain your personal contribution: event design, instrumentation, query, dashboard, investigation or experiment.

The earlier [resume project deep-dives](/docs/resume-skills/resume-project-experience-deep-dives) distinguish reported analytics/project scope from independently confirmed behavior. Do the same here.

### Evidence to prepare

| Claim | Useful supporting material |
| --- | --- |
| “Built analytics” | Event definitions, relevant code, identity policy and query/dashboard version |
| “Improved activation” | Unit, baseline/cohort, full observation windows and instrumentation checks |
| “Increased retention” | Start/return definitions, exact/rolling mode, maturity and observation period |
| “A/B test showed lift” | Assignment unit/logs, planned metric, sample and stopping rules, uncertainty and guardrails |
| “Recordings revealed friction” | Selection criteria, actual observations and a separate validation of prevalence/effect |

### Thirty-second answer skeleton

“The decision was [question]. I defined [event/unit/window/population] and implemented [your contribution]. We checked [identity, data quality and boundaries] and observed [defined result]. The evidence supports [descriptive finding or justified causal effect] under [conditions]. It does not establish [remaining uncertainty]. We used that to decide [action and revisit condition].”

Do not present this chapter's 40%/60% retention or 20% relative lift as your project result. They are teaching calculations from invented inputs.

## 2.19 Common wrong answers

| Wrong answer | Better reasoning |
| --- | --- |
| “Events, sessions and users are interchangeable.” | They count different entities under different rules |
| “A click means generation succeeded.” | Intention and committed product outcome have different emission points |
| “Different IDs always mean different people.” | Apply a justified identity policy; do not guess merges |
| “Drop duplicate rows by every field.” | Delivery retries can have different receipt times but the same business event |
| “Every recent signup is a failed conversion.” | The full observation window may not have elapsed |
| “D7 is a universal formula.” | State exact/rolling mode, anchor, timezone and mature denominator |
| “A higher report means the product improved.” | Backfills, definitions and collection coverage can change a number |
| “20% to 24% is 4% relative lift.” | It is 4 percentage points and 20% relative lift |
| “p=0.03 means 97% chance the feature works.” | A p-value is conditional on a null model and assumptions |
| “No significance means the variants are equal.” | The study may lack precision; equivalence is a separate planned question |
| “Balanced counts prove randomization.” | SRM is one diagnostic, not proof of the assignment process |
| “The heatmap proves what caused the conversion drop.” | It can suggest a mechanism requiring further evidence |

## 2.20 Must remember

- Write the metric's entity, event definitions, population and windows.
- Separate intended actions from authoritative outcomes.
- Match funnel step order and operation/user identity to the question.
- Exclude incomplete follow-up consistently from final mature-cohort rates.
- Keep occurrence and receipt time so report revisions are explainable.
- Distinguish cohort retention, active-user counts and activity frequency.
- Tool reports can disagree because their definitions and coverage differ.
- Separate descriptive lift from a causal claim.
- Randomization, exposure, stopping rules and guardrails matter alongside a p-value.
- Prepare original evidence for resume impact claims.

## 2.21 Interview questions and answers

### Q1. What is product analytics?

Measurement and analysis of product behavior to inform decisions. Define the question and metric contract before building a chart.

**Follow-up:** How does it differ from an experiment? An experiment adds an intervention and assignment design intended to support causal comparison.

### Q2. Event versus property?

An event records a defined action; a property describes its context. generation_succeeded is an event, while device=mobile is context.

**Follow-up:** Should all available properties be sent? Collect only the data justified by the measurement need and policy.

### Q3. Client versus backend tracking?

Client tracking observes interface actions; backend/worker tracking can record committed outcomes. Use both deliberately and check publication completeness.

**Follow-up:** Does a backend event prove analytics is exactly once? No; delivery and deduplication still need design.

### Q4. What belongs in a tracking plan?

Question, event meaning, emission point, identity, required properties, version, owner and verification cases. The plan should explain why each event is needed.

**Follow-up:** What breaks after renaming an event? Funnels, saved queries and historical comparability may need migration.

### Q5. How do you join anonymous and identified activity?

Use a justified explicit identity link under the tool/application's rules. The fixture maps anon-1 directly to u1; it does not infer identity from a shared network.

**Follow-up:** What is the risk of a wrong merge? Different people's activity can become one apparent journey.

### Q6. How do you handle duplicates?

Use stable event identity and compare the business content. The worksheet keeps one matching event with its earliest receipt and rejects conflicting content.

**Follow-up:** Why not deduplicate every event from one user? A user can legitimately perform an action several times.

### Q7. What defines a funnel?

Entities, steps, order, conversion window and entry/population rules. This fixture uses mature signup users and matches start/success to the same operation.

**Follow-up:** Can unrelated events occur between steps? Yes in this fixture; strict adjacency is another definition.

### Q8. Step conversion versus overall conversion?

Step conversion uses the preceding eligible step; overall conversion uses the funnel entry population. They coincide here only because all five eligible users start.

**Follow-up:** Why not compare independent event totals? They do not establish ordered progression for the same entity.

### Q9. What is activation?

A defined early behavior used as a proxy for reaching value. Here it is ordered successful output within 24 hours, not merely signup.

**Follow-up:** Does activation predict causally better retention? Association alone does not establish that effect.

### Q10. Why exclude immature users?

They have not had the full follow-up window. Keeping early successes but removing recent non-converters would bias the rate.

**Follow-up:** What happens to u6? It converted early but is still excluded from the final mature rate.

### Q11. What is a cohort?

A group sharing a declared start condition or characteristic. The worksheet displays signup-date cohorts while retaining per-user elapsed windows.

**Follow-up:** Is the first visible event always first ever? No; limited history or filters can hide earlier events.

### Q12. What does D7 retention mean?

Only what its definition specifies. Here it means at least one successful-generation return during elapsed day 7, among users with that full interval observed.

**Follow-up:** Can a day-9 return count? Not for this exact D7 definition.

### Q13. Exact-period versus rolling retention?

Exact-period requires return within that interval; on-or-after includes qualifying later returns under its follow-up boundary. They answer different questions.

**Follow-up:** Can you compare their percentages directly? Only after aligning the definition and period.

### Q14. Retention versus stickiness?

Retention asks whether a cohort returns; stickiness/frequency concerns how often qualifying use occurs. Two events from one user are not two retained users.

**Follow-up:** Is DAU/MAU the same as retention? No; define its action and windows separately.

### Q15. Why preserve receipt time?

It lets a report distinguish events known initially from later arrivals. The fixture's D7 revision from 40% to 60% comes from a late event, not new behavior in the fixed window.

**Follow-up:** Which timestamp drives the behavior interval? Occurrence time under this contract.

### Q16. Why can two analytics tools disagree?

Identity, population, session/event scope, timezone, conversion windows, counting modes, collection coverage and backfills may differ. Reconcile definitions and records before blaming a tool.

**Follow-up:** Does a key event prove revenue? No; it is a configured important outcome.

### Q17. What is Clarity useful for?

Recordings and heatmaps can help investigate interface behavior and form hypotheses. They do not make selected sessions representative or establish causal effect.

**Follow-up:** What should precede real collection? Appropriate data minimization, masking, consent and access configuration.

### Q18. Is a before/after improvement causal?

Not by itself. Traffic mix, seasonality, instrumentation, observation maturity or other changes may explain the difference.

**Follow-up:** What strengthens the claim? A suitable controlled design with trustworthy assignment and measurement.

### Q19. What should be planned before an A/B test?

Hypothesis, population, randomization unit, allocation, primary outcome, guardrails, sample/duration, analysis and stopping rules.

**Follow-up:** Why not choose the best-looking metric afterward? That changes the inferential question and can inflate false discoveries.

### Q20. Assignment versus exposure?

Assignment records the allocated variant; exposure records encountering the intervention. Exposure may depend on treatment, so exposed-only filtering can introduce selection bias.

**Follow-up:** What does intent-to-treat analyze? Outcomes by assigned group under the stated eligible population.

### Q21. Why does the randomization unit matter?

It determines which observations are independently assigned. Workspace-level assignment cannot automatically be analyzed as independent user randomization.

**Follow-up:** What is interference? One unit's treatment can affect another unit's outcome.

### Q22. Percent versus percentage points?

Control 20% and treatment 24% differ by four percentage points and 20% relative lift. Name the denominator when communicating the result.

**Follow-up:** What if baseline is zero? Relative lift is undefined; the fixture returns null.

### Q23. What is a p-value?

A tail probability calculated under a null model and its assumptions. It is not the probability that the null is true or the feature is commercially good.

**Follow-up:** Does p below a chosen threshold prove causality? No; the design and measurement must support that interpretation.

### Q24. How should you read a confidence interval?

Use it to describe the uncertainty of the specified procedure under assumptions. The fixture's approximate interval is in percentage points, not relative percent.

**Follow-up:** Why withhold it for sparse counts? The chosen normal approximation may be unsuitable.

### Q25. What do power and minimum detectable effect mean?

They connect the chance of detecting a specified effect with the design, sample and variance. A calendar duration alone is not a complete precision plan.

**Follow-up:** Does non-significance prove no difference? No; uncertainty may still include important effects.

### Q26. What is the problem with peeking?

Unplanned repeated fixed-horizon significance checks with favorable stopping change error properties. Use a declared stopping plan or valid sequential procedure.

**Follow-up:** Must safety monitoring stop? No; define operational and statistical monitoring deliberately.

### Q27. What is sample-ratio mismatch?

A diagnostic discrepancy between observed assignment counts and the planned allocation. The fixture checks a two-category chi-square approximation with an explicit threshold.

**Follow-up:** Does it identify the bug? No; investigate assignment, filtering, exposure/logging and other causes.

### Q28. Why not ship every statistically positive result?

Practical effect, uncertainty, guardrails, reliability, implementation cost and the studied population still matter. The synthetic calculation has no real assignment evidence at all.

**Follow-up:** How does P1 connect? Higher activation can be unattractive if expensive low-quality work increases.

### Q29. How would you explain a conversion drop?

Reproduce the metric, check definition and collection changes, align mature populations, locate the affected step/segment and investigate mechanisms before proposing a fix.

**Follow-up:** How would you support a resume claim? Bring original definitions, code/queries and the appropriate descriptive or experimental evidence.

### Q30. What did the 95 checks verify?

Local SQL and calculation behavior on synthetic events/counts, including time/identity edges, late data, mature denominators and approximate experiment arithmetic. No vendor parity, real assignment or historical impact was established.

**Follow-up:** What remains manual? Real instrumentation QA, consent configuration, account setup and an actual evaluation design.

## 2.22 A 30-minute mock

**Prompt:** “An AI-content product reports weak activation and claims a new onboarding screen increased conversion by 20%. Audit the claim and propose the next decision.”

| Minutes | Task | Useful result |
| --- | --- | --- |
| 0–4 | Clarify the user, outcome and claimed lift | Entity, denominator, time window and absolute/relative distinction |
| 4–9 | Inspect tracking and identity | Emission points, duplicates, aliases and coverage |
| 9–14 | Reproduce the mature funnel/cohort | Ordered steps, observation maturity and late-data treatment |
| 14–20 | Review the experiment design | Assignment unit, eligibility, exposure, stopping and SRM |
| 20–25 | Read effect and uncertainty | Practical threshold, interval and guardrails |
| 25–30 | State the decision and remaining evidence | What is descriptive, what is causal, and what to investigate next |

### Answer skeleton

“I would define activation and establish whether 20% means relative lift or percentage points. Then I would reproduce the result for identical mature populations, checking event identity, ordering, coverage and late data. If there was an experiment, I would review assignment, exposure, allocation and the analysis plan before interpreting uncertainty. I would compare a trustworthy effect estimate with the practical objective and cost/quality guardrails. If those conditions are missing, I would report the descriptive finding and specify the evidence needed for a causal decision.”

The mock is manual. A passing calculator does not establish that your interview reasoning or a real experiment is valid.

## 2.23 Practice tasks and answer checkpoints

1. **Define the metric.** Write a contract for “weekly active workspace,” including action, identity, period, exclusions and data freshness.
2. **Choose emission points.** Distinguish a Generate click, accepted operation and persisted usable output.
3. **Trace identity.** Follow anon-1 and u1 through signup and generation without counting an extra person.
4. **Read the funnel.** Explain all seven users and why only five enter the final activation denominator.
5. **Change a boundary.** Move u4's completion from exactly 24 hours to one second earlier in a copy of the fixture and predict the changed count.
6. **Audit order.** Remove u5's valid completion and explain why the orphan success cannot complete the same-operation funnel.
7. **Explain retention revisions.** Reproduce initial and revised D7 results while keeping the observation cutoff fixed.
8. **Distinguish activity.** Explain why two successful events on 8 October produce one active user.
9. **Read an experiment.** Explain four percentage points versus 20% relative lift and identify what the aggregate counts cannot prove.
10. **Inspect SRM.** Compare the 1,000/600 counts under planned treatment shares 0.5 and 0.375.
11. **Write an experiment plan.** State assignment unit, outcome, guardrails, observation window and stopping rules for a real candidate-portal or content-tool change.
12. **Prepare your own story.** Describe one actual metric or analytics contribution, with original evidence and explicit limits on causal claims.

### Answer checkpoints

- **1/2:** define meaningful product use and collect the event at the point its meaning becomes true.
- **3:** a declared alias maps to the existing canonical user; no guessed merge is needed.
- **4:** u6 and u7 lack full follow-up, even though u6 already converted.
- **5:** completed mature users increase from two to three under this fixture's half-open window.
- **6:** wrong-operation or pre-start success is insufficient.
- **7:** the late return changes known D7 returns from two to three, not the eligible population.
- **8:** event count and distinct-user count have different units.
- **9:** observed rates are 20% and 24%; randomization, measurement and causal effect remain unverified.
- **10:** the 50/50 expectation yields statistic 100; the 0.375 treatment share matches these counts.
- **11/12:** use a plan and evidence suited to the actual unit and question; do not transplant synthetic results into a resume.

## 2.24 Exit checklist

- [ ] I can define an event, property, user, session and operation.
- [ ] I can write a tracking plan with precise emission points.
- [ ] I can explain identity linking without guessing merges.
- [ ] I can distinguish delivery duplication from repeated real actions.
- [ ] I can define ordered funnels and their conversion windows.
- [ ] I can exclude immature follow-up consistently.
- [ ] I can explain exact/rolling retention and cohort denominators.
- [ ] I can distinguish active users, events and frequency.
- [ ] I can explain a late-data report revision without claiming product improvement.
- [ ] I can place PostHog, GA4 and Clarity in an investigation workflow.
- [ ] I can distinguish assignment, exposure and analysis units.
- [ ] I can interpret lift, uncertainty, p-values and SRM with their assumptions.
- [ ] I can explain what the 95 local checks establish and what remains manual.
- [ ] I can support an actual analytics resume claim with an appropriate evidence boundary.

## 2.25 Sources, reproducibility and next

Primary sources were checked on **18 October 2026** and are linked beside the relevant concepts. Vendor interfaces and analysis settings can change; align current settings explicitly when reproducing a metric in an account.

Preserved artifacts under examples/product-analytics/module-2-analytics-experiments/: analytics.py, metrics.sql, tracking-plan.json, case.json, verify.py, analytics-output.json, verification-results.json, research.json and README.md. The fixture uses an in-memory SQLite database that is explicitly closed, no external service and no persistent listener.

Return to the [Product and Analytics roadmap](/docs/product-analytics) or review [P1: Pricing and Unit Economics](/docs/product-analytics/pricing-unit-economics). Continue with [P3: Python and Excel for Analysis](/docs/product-analytics/python-excel-analysis)—dataframes, joins, missing values, dates, formulas, lookups, pivots and reconciliation.
