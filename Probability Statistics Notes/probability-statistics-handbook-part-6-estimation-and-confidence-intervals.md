# Probability and Statistics Handbook — Part 6: Estimation and Confidence Intervals

**F5: report the estimate, its uncertainty and the assumptions behind both.**

## 1. An estimator is a rule

An estimator maps a possible sample to a value. Its observed value is the estimate. Bias compares its sampling expectation to the target parameter. Variance describes its repeated-sampling spread. Mean squared error decomposes into variance plus squared bias when those quantities exist.

Consistency means the estimator approaches its target in an appropriate probabilistic sense as information grows. It is not a claim that every individual larger sample is closer. Unbiasedness and low variance are separate properties; a small biased estimator can sometimes have smaller MSE.

Maximum likelihood chooses parameters that maximize the observed-data likelihood under a stated model. For iid Bernoulli observations, the MLE is the observed success proportion. That is not automatically the best estimator for every loss function or sparse-data problem.

## 2. What a confidence level describes

A frequentist interval procedure has a coverage probability under its repeated-sampling model. Once data are observed and the interval is computed, the fixed parameter is either contained or not. A 95% label does not assign a 95% posterior probability to this particular interval. It also does not mean 95% of individuals lie inside an interval for a mean. [NIST: confidence limits for a mean](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm).

```text
Known-sigma iid Normal mean interval:
  xbar +/- z_(1-alpha/2) * sigma/sqrt(n)

Unknown-sigma iid Normal mean interval:
  xbar +/- t_(1-alpha/2,n-1) * s/sqrt(n)
```

The t interval is exact under its iid Normal model. Large-sample use outside that model is an approximation whose adequacy depends on the outcome distribution and design. Small n plus heavy tails or dependence is not fixed by changing a critical value.

A wider confidence level usually produces a wider interval from the same data and method. More independent information generally improves precision under an appropriate design. No interval calculation verifies that an export is complete or its sample represents the intended population.

## 3. Proportions and boundaries

The uncorrected Wald interval is phat +/- z*sqrt(phat*(1-phat)/n). It can behave poorly near zero/one and with small samples. A score interval such as Wilson avoids its degenerate zero-observed-success behavior. Wilson comes from solving a score-test inequality for the candidate proportion. [NIST: proportion intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

```text
denominator = 1 + z^2/n
center = (phat + z^2/(2n))/denominator
half_width = z*sqrt(phat*(1-phat)/n + z^2/(4n^2))/denominator
Wilson interval = center +/- half_width
```

This remains a method with finite-sample coverage properties to inspect. E25 calculates those properties at one known model rate. Exact binomial inversion methods are another option and can be conservative; “exact” should name the calculation being performed.

## 4. Bootstrap: resample at the independent unit

A nonparametric bootstrap treats the empirical sample distribution as a plug-in model and resamples with replacement. Compute the statistic on each resample. A percentile interval uses quantiles of that resampling distribution. E24 enumerates the entire small empirical resampling space, so it has no Monte Carlo seed or Monte Carlo error.

That enumeration does not establish real-population coverage. Small samples, extreme quantiles, heavy tails and nonsmooth statistics can be difficult. Resampling individual events can understate uncertainty if the independent units are users or clusters. Paired, clustered and time-dependent data need methods that preserve the relevant structure. [SciPy: bootstrap concepts and methods](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).

The example uses percentile quantiles with the explicitly declared linear algorithm. It does not claim to execute SciPy's default BCa bootstrap, which is a different procedure. SciPy is a documentation reference and is not installed or called by this lab.

## 5. Bayesian and predictive intervals

A Bayesian posterior combines a prior with a likelihood. A credible interval has posterior probability conditional on that model and observed data. It is not the same construction or interpretation as a frequentist confidence interval.

For a Bernoulli model and Beta(a,b) prior, k successes in n trials update the prior to Beta(a+k,b+n-k). The posterior mean is (a+k)/(a+b+n). Prior choice matters, particularly with little data. This symbolic bridge is not an implemented general posterior sampler or credible-interval calculator.

A mean-response interval estimates an average response at a setting. An individual prediction interval additionally allows for an individual outcome's variability. Do not use a narrow mean interval as a guarantee for one future user's latency.

## 6. A reporting template

State the target, point estimate and units; then name the interval method, confidence level, independent unit and main assumptions. Include missingness, selection and multiplicity/stopping limits when they affect the interpretation. Report the actual endpoints rather than only a significant/not-significant label.

<!-- BEGIN WORKED EXAMPLES -->

## 7. Worked examples

### E21. Known-sigma mean interval

An iid Normal model has known population SD 10. With n=100 and sample mean 50, calculate a two-sided 95% mean interval.

**Hint:** Known sigma gives SE=sigma/sqrt(n), with a Normal critical value.

**Worked reasoning:** The standard error is one, so add and subtract z0.975 from the observed mean. The interval estimates the population mean, rather than a range containing 95% of individual observations. Exact Normal-model coverage relies on the stated sampling assumptions; a large n alone does not establish those assumptions.

Run `python examples/probability-statistics/compute.py E21` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "known_sigma": 10,
  "n": 100,
  "sample_mean": 50,
  "se": 1.0,
  "z_critical": 1.959964,
  "ci_low": 48.040036,
  "ci_high": 51.959964
}
```

**Common trap:** Using SD itself as the uncertainty of the sample mean makes the interval unnecessarily wide and answers another question.

**Interview follow-up:** What changes when the population SD is estimated from the same small sample?

### E22. Unknown-sigma Student interval

Treat [8,9,10,11,12] as five iid Normal-model observations. Calculate a two-sided 95% interval for the population mean.

**Hint:** Use sample SD, n-1 degrees of freedom and a Student t critical value.

**Worked reasoning:** The sample mean is ten and sample variance is 2.5. Divide the sample SD by sqrt(5), then multiply by the df=4 t critical value. The local integrator calculates the t CDF and inverts it; independent closed-form df=4 calculations and published rounded tables check the result. These invented values do not demonstrate that real-world observations follow a Normal model.

Run `python examples/probability-statistics/compute.py E22` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "values": [
    8,
    9,
    10,
    11,
    12
  ],
  "mean": 10,
  "sample_sd": 1.581139,
  "se": 0.707107,
  "df": 4,
  "critical": 2.776445,
  "low": 8.036757,
  "high": 11.963243
}
```

**Common trap:** Substituting 1.96 for the small-sample t critical value understates model-based uncertainty.

**Interview follow-up:** Would this formula remain trustworthy for five highly skewed, dependent observations?

### E23. Zero observed successes is not known zero

Among twenty iid Bernoulli trials, observe zero successes. Compare a 95% Wilson interval with the uncorrected Wald interval.

**Hint:** The Wald plug-in standard error collapses when the observed proportion is zero.

**Worked reasoning:** The Wald interval degenerates at zero. Inverting the score inequality yields the Wilson interval, whose upper endpoint is z^2/(n+z^2) in this case. The data support uncertainty about a small unknown rate even though no event was observed. The displayed lower endpoint is zero after rounding floating-point arithmetic.

Run `python examples/probability-statistics/compute.py E23` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "successes": 0,
  "n": 20,
  "wilson_low": 0.0,
  "wilson_high": 0.161125,
  "wald_low": 0.0,
  "wald_high": 0.0
}
```

**Common trap:** No observed event does not establish that the true event probability is zero, and Wilson is not an exact guaranteed-coverage method.

**Interview follow-up:** Which source and observation assumptions are needed before interpreting this as a failure-rate interval?

### E24. An exact empirical bootstrap

For the observed sample [0,0,6], enumerate all 27 ordered index resamples of size three with replacement. Calculate a percentile interval for the mean.

**Hint:** The two observed zeros have distinct indices and retain their combined probability weight.

**Worked reasoning:** The bootstrap means zero, two, four and six occur 8,12,6,1 times. Use the declared (m-1)q linear quantile rule on all 27 means, not just their distinct values. This is exact enumeration of the empirical resampling distribution; it is not an exact confidence-coverage guarantee for the unknown population. The tiny skewed sample intentionally exposes that distinction.

Run `python examples/probability-statistics/compute.py E24` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "original_values": [
    0,
    0,
    6
  ],
  "ordered_index_resamples": 27,
  "mean_frequencies": {
    "0": 8,
    "2": 12,
    "4": 6,
    "6": 1
  },
  "percentile_95_low": 0.0,
  "percentile_95_high": 4.7,
  "exact_empirical_bootstrap_se": 1.632993
}
```

**Common trap:** Deduplicating sample values changes the empirical distribution. Calling exhaustive enumeration exact does not make its percentile interval universally valid.

**Interview follow-up:** Why should a cluster-randomized experiment resample independent clusters rather than individual rows?

### E25. Calculate actual interval coverage

For n=10 iid Bernoulli trials at true p=0.1, calculate the actual coverage of nominal 95% Wilson and Wald procedures over every possible success count.

**Hint:** Sum the binomial mass of each count whose interval contains 0.1.

**Worked reasoning:** Wilson covers the specified true value for counts zero, one and two; Wald covers it for counts one through four. Summing the respective binomial masses gives actual fixed-n coverage. The verifier independently enumerates weighted binary sequences. This is a repeated-sampling property at one specified p, not a posterior probability for any particular observed interval.

Run `python examples/probability-statistics/compute.py E25` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "wilson": {
    "true_p": 0.1,
    "n": 10,
    "coverage": 0.929809,
    "covering_counts": [
      0,
      1,
      2
    ]
  },
  "wald": {
    "true_p": 0.1,
    "n": 10,
    "coverage": 0.649687,
    "covering_counts": [
      1,
      2,
      3,
      4
    ]
  }
}
```

**Common trap:** A nominal label does not promise exactly that coverage for every finite sample size and parameter value.

**Interview follow-up:** What additional calculations would be needed to assess coverage across a grid of true rates?

<!-- END WORKED EXAMPLES -->

## 8. Interview Q&A

### Q1. Is an unbiased estimate always more accurate?
No. Accuracy under squared loss depends on variance plus squared bias. Unbiasedness alone does not minimize MSE.

### Q2. Does 95% confidence mean 95% posterior probability?
No. Frequentist coverage describes an interval procedure across repeated samples; posterior probability requires a Bayesian model.

### Q3. When should I use z instead of t for a mean?
Under the stated Normal model with known population SD, use z. Estimating SD from a small Normal sample introduces a t reference.

### Q4. Why can zero successes still leave a positive upper bound?
An unknown small success probability can produce no successes in a finite sample. The uncertainty is not resolved by a zero observed count.

### Q5. Does exact bootstrap enumeration imply exact confidence coverage?
No. It removes Monte Carlo error for the specified empirical resampling distribution, rather than proving its population approximation.

### Q6. What should a cluster bootstrap resample?
Independent clusters with their relevant internal structure, under a method appropriate to the design. Arbitrary individual rows can destroy dependence.

### Q7. Can a confidence interval be compared with a hypothesis test?
When the interval and test are corresponding inversions using matching models, tails and procedures. Different methods can disagree near a threshold.

### Q8. What separates a prediction interval from a mean interval?
A prediction interval accounts for the variability of an individual outcome as well as uncertainty about its conditional mean.

## 9. Practice tasks

1. Explain every assumption behind E21 and E22 before comparing their critical values.
2. Derive E23's Wilson upper endpoint for zero observed successes.
3. Reproduce E24's resampling frequencies without deduplicating the observed zeros.
4. Explain why E25's coverage calculation cannot be read as the posterior probability of its true parameter.

**Answer checkpoints:** known versus estimated sigma changes the reference; the zero-success Wilson upper endpoint is z^2/(n+z^2); bootstrap index multiplicities are 8,12,6,1; E25 varies the possible sample while holding the true rate fixed.

- [ ] I can state the sampling interpretation of an interval.
- [ ] I can distinguish exact enumeration, approximation and model validation.

Continue with [Hypothesis Tests and Experiments](/docs/probability-statistics/hypothesis-tests-and-experiments).
