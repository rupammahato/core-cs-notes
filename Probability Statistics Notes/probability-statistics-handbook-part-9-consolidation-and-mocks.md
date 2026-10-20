# Probability and Statistics Handbook — Part 9: Consolidation and Mocks

**State the model, work the example and defend the interpretation.**

## 1. Twenty confusable pairs

| Pair | Distinction to preserve |
| --- | --- |
| Outcome / event | One elementary result versus a set of outcomes |
| Independent / exclusive | Joint factorization versus impossible co-occurrence |
| Combination / permutation | Unordered membership versus ordered positions |
| With / without replacement | Restarted selection pool versus changed remaining pool |
| Forward / reverse conditional | Same intersection, different conditioning denominator |
| Sensitivity / precision | Condition on actual positives versus alerted positives |
| Pairwise / mutual independence | Every pair versus factorization for every subset |
| PMF / PDF | Point mass versus density integrated over an interval |
| Rate / expected count | Per-exposure parameter versus parameter times exposure |
| SD / SE | Observation variation versus estimator variation |
| Parameter / statistic | Population/model quantity versus a sample function |
| Bias / variance | Sampling expectation error versus repeated-sampling spread |
| LLN / CLT | Average convergence versus standardized limiting distribution |
| Sampling / assignment | Selecting a population sample versus allocating an intervention |
| Confidence / credible interval | Repeated-sampling coverage versus posterior probability |
| Nominal / actual coverage | Procedure label versus coverage at a specified model setting |
| Paired / independent analysis | Preserve matched differences versus independent groups |
| Significant / practically useful | Statistical evidence versus decision value |
| Correlation / causation | Observed association versus an intervention claim |
| Training / future error | Fit on observed training outcomes versus verified generalization |

## 2. Ten diagnosis cards

| ID | Symptom | First discriminating check |
| --- | --- | --- |
| D01 | A probability exceeds one | Check overlapping events and double counting |
| D02 | A rare-event detector seems almost infallible | Reconstruct the conditioning population and base rate |
| D03 | Two copies make evidence much stronger | Inspect shared event identity and dependence |
| D04 | Arrival predictions fail during bursts | Check exposure, rate stability and count variation |
| D05 | Two dashboards disagree on p95 | Compare quantile conventions, units and populations |
| D06 | An enormous sample gives a suspiciously precise answer | Inspect selection, missingness and independent units |
| D07 | Zero failures yields a zero-width interval | Identify the interval method and boundary behavior |
| D08 | A result appears only after many slices or looks | Inspect multiplicity, stopping and exploratory selection |
| D09 | Pooled and segment trends reverse | Reconcile raw counts, mixture weights and variable timing |
| D10 | A strong training fit fails in production | Check residuals, leakage, time split and extrapolation |

These are investigation hypotheses, not confirmed incident causes. Evidence should distinguish competing explanations before a diagnosis is accepted.

## 3. Thirty oral checks

| ID | Question | Answer checkpoint |
| --- | --- | --- |
| O01 | When does favorable/total counting work? | Equally likely elementary outcomes |
| O02 | Why use a complement? | “None” can be simpler than an overlapping union |
| O03 | What distinguishes named roles from a committee? | Order changes outcome identity |
| O04 | Does linearity of expectation need independence? | No, when the expectations exist |
| O05 | What changes in a reverse conditional? | The conditioning denominator |
| O06 | Why can precision fall despite high sensitivity? | Low prevalence and false positives |
| O07 | Can pairwise independence miss a dependency? | Yes; inspect the XOR triple |
| O08 | When can two evidence likelihoods be multiplied? | Under the relevant conditional-independence model |
| O09 | Can a continuous density exceed one? | Yes; probability is interval area |
| O10 | What geometric convention is used? | Trials including the first success |
| O11 | How do you convert an arrival rate to a count mean? | Multiply by consistent exposure |
| O12 | What makes a wait memoryless? | Conditional survival equals fresh additional survival |
| O13 | What does sample variance's correction establish? | Unbiasedness under its model, not removal of selection bias |
| O14 | Why document a quantile algorithm? | Short-sample quantiles depend on the convention |
| O15 | What does SE quantify? | Sampling variability of an estimator |
| O16 | Does CLT make raw observations Normal? | No; it concerns a standardized average under conditions |
| O17 | Can larger n repair missing-not-at-random observations? | No automatic bias repair |
| O18 | Why is a Wilson upper endpoint positive after no events? | Finite data do not establish a known zero probability |
| O19 | What is exact in the bootstrap example? | Enumeration of the empirical resampling distribution |
| O20 | What does coverage vary over? | Repeated samples while the true parameter is fixed |
| O21 | Is a p-value P(null true given data)? | No; it is calculated under a null model |
| O22 | What does failure to reject establish? | Insufficient evidence under that procedure, not equality |
| O23 | Why use paired differences? | Retain the matching and relevant covariance |
| O24 | What makes randomization enumeration valid? | It follows the design's permitted assignments and null |
| O25 | Does Bonferroni require independence? | No for its union-bound family-wise guarantee |
| O26 | Is the independent-test family error a peeking calculation? | No; accumulating looks are correlated |
| O27 | Does zero Pearson correlation imply independence? | Not generally; a curved relationship can remain |
| O28 | What does R-squared fail to establish? | Model validity, generalization and causality |
| O29 | Why not automatically control for every variable? | Causal roles and post-treatment selection matter |
| O30 | What does E34 establish about CUPED? | Descriptive sample algebra, not a real experimental power gain |

## 4. Mock A: probability and estimation, 45 minutes

| Minutes | Work | What to explain |
| --- | --- | --- |
| 0–5 | State E01's experiment | Fairness, independence and event definitions |
| 5–12 | Solve E01/E03 | Overlap and changed probabilities without replacement |
| 12–20 | Solve E07/E10 | Base rate and duplicated versus independent evidence |
| 20–28 | Choose E11–E15 models | Support, rate/time units and assumptions |
| 28–38 | Explain E22/E23 | t reference, coverage and zero-observation uncertainty |
| 38–45 | Accept a changed assumption | Say which equation no longer applies and why |

**Feedback checkpoints:** retain the alerted denominator; do not square a duplicate alert; name the geometric convention; distinguish an interval for a mean from a distribution of observations. Use the corresponding case outputs as numerical answer checkpoints.

## 5. Mock B: analytical investigation, 45 minutes

**Hypothetical scenario:** a product report shows higher conversion, a tiny p-value and a strong regression fit. It combines repeated user events, unequal segment mixtures and several exploratory metrics.

| Minutes | Work | What to explain |
| --- | --- | --- |
| 0–7 | Clarify the estimand and unit | Eligible user/workspace, window, denominator and missingness |
| 7–15 | Reconcile rates using E18/E33 | Pooling versus standardized weights |
| 15–25 | Choose an inference design | Assignment, dependence, pairing and post-treatment filtering |
| 25–33 | Discuss E26–E30 | Null evidence, practical effect, power and multiple testing |
| 33–40 | Inspect E31/E32/E35 | Curvature, residuals, leakage and unknown future error |
| 40–45 | Recommend the next check | A check whose outcome could change the conclusion |

**Feedback checkpoints:** do not treat events as automatically independent; the independent twenty-test calculation is not a sequential correction; common-mixture arithmetic alone is not causal identification; training fit supplies no held-out performance result.

Both mocks are authored practice formats. They are not observed company processes or automatically graded learner accomplishments.

## 6. Seven-day revision route

| Day | Study | Produce |
| --- | --- | --- |
| 1 | F1, E01–E05 | Sample spaces and two counting explanations |
| 2 | F2, E06–E10 | A frequency tree and independence counterexample |
| 3 | F3, E11–E15 | A distribution-selection card with assumptions |
| 4 | F4, E16–E20 | Unit/weight definitions and a sampling distribution |
| 5 | F5, E21–E25 | Interval interpretation and actual-coverage explanation |
| 6 | F6, E26–E30 | A test contract and Mock A feedback |
| 7 | F7, E31–E35 and Mock B | A regression critique and targeted correction |

The schedule is a suggested order, not a measured learning-time claim. Keep an error log containing the mistaken assumption, a minimal counterexample and an improved explanation.

## 7. Exit checklist

- [ ] I define events, units and denominators before choosing a formula.
- [ ] I distinguish independent, exclusive and conditionally independent events.
- [ ] I can derive a posterior from a natural-frequency table.
- [ ] I choose distributions by mechanism and support.
- [ ] I distinguish SD, SE and a sampling distribution.
- [ ] I explain LLN/CLT assumptions and sampling bias.
- [ ] I interpret frequentist and Bayesian intervals correctly.
- [ ] I distinguish exact enumeration from exact population coverage.
- [ ] I connect a test to its null, design and tail convention.
- [ ] I discuss practical effect, multiplicity and stopping.
- [ ] I can criticize a regression without treating a fit score as causality.
- [ ] I have attempted both mocks without copying the worked solutions.

Return to the [roadmap](/docs/probability-statistics) or combine this revision with the [SQL interview lab](/docs/sql-interview) and [product experiments](/docs/product-analytics/product-analytics-experiments). The handbook is fully authored; manual practice remains learner work.
