# Probability and Statistics Handbook — Part 7: Hypothesis Tests and Experiments

**F6: connect evidence to a declared question, design and decision rule.**

## 1. The components of a test

State a null hypothesis, alternative, statistic, null reference distribution and rejection rule before calculating a p-value. A two-sided p-value sums null outcomes at least as incompatible with the null as the observation, according to the specified statistic and ordering. Discrete two-sided definitions need explicit conventions.

A p-value conditions on a null model and its assumptions. It is not the probability that the null is true, the probability that an effect is useful or a replication guarantee. Report effect size, uncertainty and context alongside it. The ASA's statement explicitly cautions against making decisions solely from whether a threshold was crossed. [ASA statement](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf).

Failing to reject does not establish equality. Equivalence and noninferiority require planned margins and suitable tests. Choosing a one-sided direction after seeing the data changes the procedure; a one-sided plan needs advance justification.

## 2. Errors, power and practical effect

| Quantity | Conditional question |
| --- | --- |
| Type I error | How often does the procedure reject when the relevant null is true? |
| Type II error beta | At a specified alternative, how often does it fail to reject? |
| Power 1-beta | At that alternative, how often does it reject? |
| Minimum worthwhile effect | Which effect size matters for the decision? |

Alpha is a property of a procedure under a null, not the posterior error probability of one decision. Power is evaluated at specified alternatives. Observed post-hoc “power” based on the same estimated effect is not a substitute for reporting its uncertainty.

## 3. Choose the analysis from the design

| Question/data | Candidate method | Important condition |
| --- | --- | --- |
| One binary rate versus a null rate | Exact binomial or justified approximation | Binomial trial model |
| Two independent means | Welch t method | Independent units; appropriate mean/variance behavior |
| Matched before/after mean change | One-sample analysis of paired differences | Valid matching; independent differences |
| Two independent proportions | Two-proportion method or suitable exact method | Outcome, denominators and sampling model |
| Categorical contingency | Chi-square approximation or suitable exact procedure | Expected counts, design and independence |
| More than two means | ANOVA or an appropriate alternative | A global test does not identify every differing pair |
| A randomized assignment contrast | Design-based randomization test | Correct assignment set and relevant null |

Welch uses SE=sqrt(sA^2/nA+sB^2/nB) and approximate Welch-Satterthwaite degrees of freedom. A paired design instead analyzes within-unit differences. Equal sample sizes do not create pairing, and unequal variances do not automatically invalidate Welch. [NIST: two-sample t methods](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm).

For independent proportions under an equality null, a large-sample test pools successes and sample sizes to estimate the null rate. An unpooled difference interval uses another variance estimate and need not invert that exact test. Sparse cases can need another method. [NIST: two proportions](https://www.itl.nist.gov/div898/handbook/prc/section3/prc33.htm).

## 4. Exact tests still need assumptions

The exact coin example sums a finite null distribution. The randomization example enumerates all assignments permitted by its complete balanced design under a sharp no-effect null. A generic permutation test instead needs its relevant exchangeability/null conditions; changing grouping labels is not universally justified.

The exact E29 calculation uses absolute mean difference, includes the observed assignment and enumerates every permitted assignment. Other software can define two-sided tails differently. A Monte Carlo approximation would need its own sampling and p-value conventions. [SciPy: permutation-test definitions](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).

## 5. Sample-size planning

For equal independent binary-outcome arms, E30 uses this declared approximation:

```text
pbar = (p0+p1)/2
n_per_arm approximately equals
 [ z_(1-alpha/2)*sqrt(2*pbar*(1-pbar))
   + z_power*sqrt(p0*(1-p0)+p1*(1-p1)) ]^2 / (p1-p0)^2
```

Round upward. This plans an approximate two-sided Normal comparison for specified rates; it is not exact achieved power, a sequential design or a cluster adjustment. A planning tool also needs the allocation ratio and test choice. [MedCalc: comparison-of-proportions planning inputs](https://www.medcalc.org/en/manual/sample-size-comparison-of-proportions.php).

Small worthwhile effects require more information. Outcome variance, unequal allocation, clustering, attrition, observation maturity and missingness can change the plan. Calendar duration also needs traffic, eligibility and full outcome-window assumptions. “One week” is not a complete statistical design.

## 6. Multiplicity and stopping

For m independent tests that each have exact null rejection probability alpha, the probability of at least one rejection is 1-(1-alpha)^m. E30 computes that illustrative independent-test family. Ordinary repeated looks at accumulating data are correlated, so that number is not their calculated error rate.

Bonferroni uses alpha/m to control family-wise error by a union bound when each individual test is valid, without requiring independence. False discovery rate is a different target: the expected false-discovery proportion under the procedure's conventions and assumptions. Predeclare confirmatory metrics; label exploratory slices and validate promising findings separately.

Repeatedly stopping when an ordinary fixed-horizon p-value first crosses a threshold changes the test's behavior. Use a planned fixed horizon or a valid sequential procedure. The lab does not implement alpha spending, confidence sequences or sequential power.

## 7. Product experiment checklist in context

Define population, assignment unit, stable assignment, outcome window and analysis population. Check assignment counts and logging before treating a metric difference as evidence. Analyze dependence at the randomization unit and account for contamination/interference where relevant.

An intent-to-treat comparison follows assignment. Filtering on post-treatment exposure or activity can break comparability. Practical decisions also need effect size, guardrails, costs and transportability. Return to the [product experiment chapter](/docs/product-analytics/product-analytics-experiments) for the operational discussion; the aggregate fixtures here verify no real assignment process.

<!-- BEGIN WORKED EXAMPLES -->

## 8. Worked examples

### E26. Exact binomial evidence

Observe eight heads in ten iid coin flips. Under H0:p=0.5, calculate a two-sided binomial p-value using probability ordering.

**Hint:** Include null outcomes with probability no greater than that of the observed count.

**Worked reasoning:** The included counts are 0,1,2,8,9,10. Their total null probability is 0.109375. The rule is stated explicitly because discrete two-sided definitions can differ. At a predeclared 0.05 threshold this outcome does not reject the fair-coin null; it does not establish that the coin is fair.

Run `python examples/probability-statistics/compute.py E26` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "heads": 8,
  "n": 10,
  "included_counts": [
    0,
    1,
    2,
    8,
    9,
    10
  ],
  "two_sided_probability_ordered_p": 0.109375
}
```

**Common trap:** The p-value is neither P(H0 true given data) nor the probability that this one observed sequence occurred.

**Interview follow-up:** What would change for a one-sided alternative chosen before the data were observed?

### E27. Welch comparison of independent means

Compare A=[10,12,9,11,13] and B=[13,15,14,16,12,18] using a two-sided Welch test and 95% interval for mean(B)-mean(A). Assume independent Normal-model observations.

**Hint:** Combine sA^2/nA and sB^2/nB, then use Welch-Satterthwaite degrees of freedom.

**Worked reasoning:** Compute the mean difference, its estimated SE, the Welch t statistic and approximate degrees of freedom. The confidence interval uses that same t reference and df. The verifier uses independent raw-moment algebra and fixed-grid integration, rather than saved outputs. This model-based inference needs independence and appropriate distributional behavior; it does not verify a real treatment assignment or causal effect.

Run `python examples/probability-statistics/compute.py E27` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "A": [
    10,
    12,
    9,
    11,
    13
  ],
  "B": [
    13,
    15,
    14,
    16,
    12,
    18
  ],
  "difference_B_minus_A": 3.666667,
  "se": 1.130388,
  "t": 3.243723,
  "df": 8.898234,
  "two_sided_p": 0.01025,
  "ci_low": 1.105086,
  "ci_high": 6.228248
}
```

**Common trap:** Welch relaxes equal variances, not independence, measurement quality or the need for an appropriate outcome model.

**Interview follow-up:** Would repeated measurements from the same units call for this independent-sample analysis?

### E28. Paired measurements

For five matched units, before=[10,20,30,40,50] and after=[12,21,33,42,54]. Test a zero mean change and give its 95% interval. Assume iid Normal-model differences.

**Hint:** Analyze within-unit differences, retaining the pairing.

**Worked reasoning:** The differences are 2,1,3,2,4. Calculate the one-sample mean-change t statistic and df=4 interval on those differences. The relevant variance is variation in changes, not the large spread between baseline levels of different units. A before/after change alone still cannot identify causality without an appropriate design.

Run `python examples/probability-statistics/compute.py E28` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "before": [
    10,
    20,
    30,
    40,
    50
  ],
  "after": [
    12,
    21,
    33,
    42,
    54
  ],
  "paired_differences": [
    2,
    1,
    3,
    2,
    4
  ],
  "mean": 2.4,
  "sample_sd": 1.140175,
  "se": 0.509902,
  "df": 4,
  "critical": 2.776445,
  "low": 0.984285,
  "high": 3.815715,
  "t": 4.706787,
  "two_sided_p": 0.009262
}
```

**Common trap:** Discarding the matched identity loses the covariance structure and changes the analysis.

**Interview follow-up:** What should you do if some units lack an after measurement or the pairing is unreliable?

### E29. All balanced random assignments

Six units have fixed outcomes [1,2,3,4,5,6]. A receives the first three and B the last three. Under a sharp no-effect null and uniform complete assignment of three units per arm, calculate a two-sided randomization p-value based on absolute mean difference.

**Hint:** Enumerate the twenty equally likely choices of A, rather than all ordered label permutations.

**Worked reasoning:** The observed difference is three. Exactly two balanced assignments have an absolute difference at least that large, giving 2/20. Every assignment in the declared design is included, so no Monte Carlo correction or random seed is needed. With another assignment design or a weaker null, a different reference calculation may be needed.

Run `python examples/probability-statistics/compute.py E29` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "observed_B_minus_A": 3.0,
  "balanced_assignments": 20,
  "absolute_difference_at_least_observed": 2,
  "exact_two_sided_p": 0.1
}
```

**Common trap:** Shuffling rows is valid only when it matches the design or a justified exchangeability assumption. Exact enumeration does not repair a bad design.

**Interview follow-up:** How would blocked or clustered randomization change the allowable assignments?

### E30. Power planning and multiple looks

Plan equal independent binary-outcome arms for baseline 0.20 versus alternative 0.23, two-sided alpha=0.05 and target power 0.80. Also calculate family error for twenty independent null tests at 0.05 and a Bonferroni threshold.

**Hint:** Use the stated Normal sample-size approximation; distinguish per-test error from family error.

**Worked reasoning:** The example solves the conventional equal-allocation Normal approximation using pooled variance in the null critical boundary and alternative variance for power. It rounds the per-arm sample size upward. It does not compute exact achieved binomial power, adjust for clusters, exclusions or repeated monitoring. For twenty independent level-0.05 null tests the family error is 1-0.95^20. Bonferroni uses alpha/20 and does not require independence for its error bound.

Run `python examples/probability-statistics/compute.py E30` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "baseline": 0.2,
  "alternative": 0.23,
  "alpha_two_sided": 0.05,
  "target_power": 0.8,
  "approx_n_per_arm_unrounded": 2942.586737,
  "approx_n_per_arm_ceiling": 2943,
  "independent_20_null_tests_family_error": 0.641514,
  "bonferroni_20_test_threshold": 0.0025
}
```

**Common trap:** Independent tests and repeated correlated interim looks are different designs. The family-error figure here is not a computed peeking error rate.

**Interview follow-up:** How would the sample plan change with a smaller worthwhile effect, unequal allocation or workspace randomization?

<!-- END WORKED EXAMPLES -->

## 9. Interview Q&A

### Q1. What does a p-value condition on?
The specified null model and its assumptions, plus the declared extremeness rule. It does not assign posterior probability to the null.

### Q2. Does nonsignificance prove no effect?
No. The estimate may be imprecise. Equivalence requires planned margins and an appropriate procedure.

### Q3. Why distinguish paired and independent tests?
Pairing changes the variance structure. Matched differences retain within-unit covariance that an independent analysis discards.

### Q4. Does Welch fix every small-sample issue?
No. It addresses unequal variance estimation, while independence, extreme tails, measurement quality and model suitability still matter.

### Q5. What makes the E29 randomization test exact?
It enumerates every assignment allowed by the declared small design under its sharp null, with no Monte Carlo sampling.

### Q6. Is statistical significance enough to ship?
No. Compare effect size and uncertainty with practical goals, costs, guardrails and the validity of measurement and assignment.

### Q7. Why plan a sample size before testing?
Power and error properties depend on the effect, outcome variability, allocation and decision rule. Opportunistic stopping can change those properties.

### Q8. Does Bonferroni require independent tests?
Its family-wise error bound uses a union bound and valid individual tests; independence is not required for that bound.

## 10. Practice tasks

1. Explain E26 without using the phrase “probability the null is true.”
2. Recalculate E27 after swapping arm names and predict which quantities change sign.
3. Describe how E29's allowed assignment set changes under blocking or clustering.
4. Explain which parts of E30 would change for a smaller practical effect or repeated interim testing.

**Answer checkpoints:** the coin tail is conditional on a fair-coin model; swapped arms reverse difference and t while preserving the two-sided p-value; a randomization reference must follow the assignment design; the normal fixed-horizon plan does not supply sequential error control.

- [ ] I can connect a test to a null, design, statistic and tail rule.
- [ ] I can report practical effect and uncertainty without overclaiming.

Continue with [Correlation and Regression](/docs/probability-statistics/correlation-and-regression).
