# Probability and Statistics Handbook — Part 5: Descriptive Statistics and Sampling

**F4: distinguish variation in observations from uncertainty in an estimate.**

## 1. Start with the population and unit

A population is the set or generating process you want to describe. A sample supplies observations about it. A parameter describes the population/model; a statistic is a function of the sample. The observed value of a statistic is an estimate when used to estimate a parameter.

For product data, a row might represent an event, session, user, order or workspace. Those units are not interchangeable. A user with many events can dominate an event-weighted average without representing many independent users. Define the target period, eligibility, missing observations and aggregation before interpreting any summary.

| Data form | Examples | Useful caution |
| --- | --- | --- |
| Nominal category | Region, platform | Numeric codes do not create a meaningful average |
| Ordered category | Satisfaction levels | Order does not establish equal spacing |
| Numeric count | Orders, retries | Zero, missing and censored differ |
| Numeric measurement | Latency, revenue | Units, tails and observation window matter |

## 2. Location, spread and robustness

The arithmetic mean relates to totals and gives large observations substantial influence. The median describes a central order position and is less sensitive to a few extreme values. A mode describes frequently occurring values or categories. None is a universal definition of “typical.”

For n observations, sample variance is the sum of squared deviations from the sample mean divided by n-1. Under iid finite-variance sampling, it is unbiased for population variance. If the list is the complete finite population you want to describe, dividing by n describes that list's population variance. [OpenStax: spread](https://openstax.org/books/introductory-statistics-2e/pages/2-7-measures-of-the-spread-of-the-data).

```text
sample mean = sum(xi)/n
sample variance s^2 = sum((xi-xbar)^2)/(n-1)
sample SD s = sqrt(s^2)
estimated SE of an iid sample mean = s/sqrt(n)
```

SD describes outcome spread. SE describes variability of an estimator over samples under a design/model. Increasing n reduces SE under the stated iid setup; it does not force individual outcomes to become less variable.

Quantiles need a convention. This book uses linear interpolation at zero-based position (n-1)q when labelled linear, and sorted position ceil(nq) when labelled nearest rank. An IQR is Q3-Q1. Tool defaults can differ, especially on short samples; report the method and empty/missing-data policy.

## 3. Weights define the question

A pooled conversion is total successes divided by total eligible units. An equal average of segment rates is a different weighted estimand. Weights should describe the intended target population rather than whichever result looks preferable.

Likewise, a mean user spend differs from a mean order spend. Ratio metrics, such as total revenue/total users, have uncertainty influenced by their joint numerator/denominator structure. This book does not implement a general ratio-metric variance estimator.

## 4. Sampling designs and bias

| Design or process | What to inspect |
| --- | --- |
| Simple random sampling | Frame coverage and actual selection mechanism |
| Stratified sampling | Within-stratum selection and target population weights |
| Cluster sampling | Dependence within clusters and number of independent clusters |
| Convenience/volunteer sample | Who is excluded or more likely to respond |
| Longitudinal sample | Repeated measurements, attrition and temporal dependence |

Random sampling supports generalization to its covered population under the design. Random assignment supports a treatment comparison under its experimental assumptions. One does not substitute for the other.

More data can narrow an interval around a biased answer. Nonresponse, selection, survivorship, mismeasurement and missing-not-at-random observations need substantive investigation; n-1 is not a bias repair kit. A missing value must not silently become an observed zero.

## 5. Sampling distributions, LLN and CLT

Imagine repeatedly sampling under the same rules and computing the same statistic. The distribution of that statistic is its sampling distribution. Enumerating all small samples below makes the distinction visible.

For iid observations with mean mu and finite variance sigma squared:

```text
E(sample mean) = mu
Var(sample mean) = sigma^2/n
SE(sample mean) = sigma/sqrt(n)
```

The law of large numbers concerns convergence of an average to its expectation under suitable conditions. The classical central limit theorem concerns the limiting Normal distribution of a centered, scaled average. It does not make raw observations Normal or guarantee that n=30 is enough for every population. Severe skew, dependence and infinite-variance cases require care. [OpenStax: CLT](https://openstax.org/books/introductory-statistics-2e/pages/7-1-the-central-limit-theorem-for-sample-means-averages).

Without replacement from a finite population, the independent-draw variance formula needs its sampling-design correction. When the sampling fraction is substantial, ignoring that correction can matter. Clustering can instead increase uncertainty relative to a naive independent-row model.

<!-- BEGIN WORKED EXAMPLES -->

## 6. Worked examples

### E16. An outlier changes the mean

Summarize the invented values [2,3,3,4,100] using mean, median and both population and sample variance.

**Hint:** Use n for the listed population's variance and n-1 when estimating variance from an iid sample.

**Worked reasoning:** The outlier pulls the mean far above the median. Both variance calculations use the same squared deviations but different denominators. The correct denominator depends on what is being estimated. Do not delete the large value merely because the result becomes inconvenient; first investigate its meaning and data quality.

Run `python examples/probability-statistics/compute.py E16` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "values": [
    2,
    3,
    3,
    4,
    100
  ],
  "mean": 22.4,
  "median": 3,
  "population_variance": 1505.84,
  "sample_variance": 1882.3
}
```

**Common trap:** A small median does not show that every observation is small, and Bessel's correction does not repair sampling bias.

**Interview follow-up:** Which summary answers typical-user experience, and which relates to total resource usage?

### E17. Quantiles need a convention

For values 1 through 8, calculate Q1/Q3 by linear interpolation at position (n-1)q, and p95 by nearest rank.

**Hint:** Different declared quantile algorithms can return different answers on the same short sample.

**Worked reasoning:** The linear positions for the quartiles are 1.75 and 5.25 in zero-based indexing, so interpolate between neighboring values. For nearest-rank p95, choose sorted position ceil(0.95*n), using one-based indexing. This example intentionally compares conventions rather than pretending all tools implement the same percentile definition.

Run `python examples/probability-statistics/compute.py E17` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "values": [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8
  ],
  "Q1_linear": 2.75,
  "Q3_linear": 6.25,
  "IQR": 3.5,
  "p95_nearest_rank": 8
}
```

**Common trap:** A percentile disagreement across tools can come from the algorithm instead of corrupted data.

**Interview follow-up:** Which definition and empty-sample behavior should a production latency dashboard document?

### E18. Average rates at the intended unit

One segment converts 2 of 10 users and another 90 of 100. Compare overall user conversion with the equal-weight average of segment rates.

**Hint:** Pooling numerator and denominator answers a user-weighted question.

**Worked reasoning:** Overall conversion divides total converted users by total users. Equal weighting instead describes a hypothetical population that gives each segment half the weight. Either estimand can be meaningful when declared, but they answer different questions. Never silently switch weights during a comparison.

Run `python examples/probability-statistics/compute.py E18` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "small_segment_rate": 0.2,
  "large_segment_rate": 0.9,
  "pooled_rate": 0.836364,
  "unweighted_segment_average": 0.55
}
```

**Common trap:** The average of two percentages is not automatically the percentage over the combined population.

**Interview follow-up:** When would a fixed, standardized segment mixture be more useful than the current observed mixture?

### E19. Enumerate a sampling distribution

Draw two independent observations with replacement from the equally likely population entries [0,0,6]. Enumerate all sample means.

**Hint:** There are nine equally likely ordered index samples, including repeated values.

**Worked reasoning:** The population mean is two and variance is eight. Averaging two iid draws preserves the mean and divides variance by two. Enumerating all index samples produces the exact sampling distribution for this tiny experiment; it is discrete and visibly not exactly Normal. Repetition of samples, rather than a histogram of raw values, defines this distribution.

Run `python examples/probability-statistics/compute.py E19` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "ordered_samples": 9,
  "mean_of_sample_means": 2,
  "variance_of_sample_means": 4,
  "population_variance": 8
}
```

**Common trap:** The central limit theorem concerns a standardized average under conditions; it does not make a two-observation raw dataset Normal.

**Interview follow-up:** What changes as sample size grows, and what assumptions would invalidate the variance/n calculation?

### E20. Finite-population correction

Select two distinct entries by simple random sampling without replacement from the finite population [0,2,4,6]. Find the sampling variance of their mean.

**Hint:** Use population variance/n multiplied by (N-n)/(N-1).

**Worked reasoning:** The six unordered samples are equally likely. Their means average to three and have variance 5/3. Independent sampling with replacement would have variance 5/2. With population variance defined using N, the correction is (N-n)/(N-1). The equivalent survey formula uses the finite-population variance defined with N-1 and correction (1-n/N).

Run `python examples/probability-statistics/compute.py E20` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "unordered_samples": 6,
  "mean_of_sample_means": 3,
  "variance_without_replacement": 1.666667,
  "variance_with_replacement": 2.5,
  "variance_correction": 0.666667
}
```

**Common trap:** Mixing the N-denominator variance with the alternative correction formula introduces a denominator error.

**Interview follow-up:** Why does sampling the whole finite population leave zero sampling uncertainty about its mean?

<!-- END WORKED EXAMPLES -->

## 7. Interview Q&A

### Q1. Is a parameter the same as a statistic?
No. A parameter describes the target population or model; a statistic is computed from a sample and varies across samples.

### Q2. When would mean and median answer different business questions?
The mean connects to totals per unit, while the median describes a central observation. Heavy tails can separate these substantially.

### Q3. Why use n-1 in sample variance?
Estimating the mean consumes a degree of freedom; the correction gives an unbiased variance estimator under the iid finite-variance model.

### Q4. What is SD versus SE?
SD measures observation spread; SE measures the sampling variability of an estimator under its model/design.

### Q5. Does the CLT guarantee a Normal histogram of user revenue?
No. Its classical statement concerns a standardized sample average, with conditions. The raw outcome distribution can remain highly skewed.

### Q6. Does a huge sample remove bias?
No. Selection and measurement errors can persist while sampling uncertainty shrinks.

### Q7. What is random assignment versus random sampling?
Assignment allocates interventions; sampling selects units from a population. They address different inferential questions.

### Q8. Can repeated rows count as independent evidence?
Only when the observation/design model supports it. Shared users, workspaces and time effects often introduce dependence.

## 8. Practice tasks

1. Recompute E16 after removing the outlier, then explain why a deletion policy requires a reason beyond the changed average.
2. State both estimands in E18 before comparing their values.
3. List the nine ordered index samples in E19 and explain why equal observed values retain separate sampling weight.
4. Explain E20's whole-population limit without mixing the two finite-population variance conventions.

**Answer checkpoints:** a different summary is not evidence that the original observation was erroneous; pooled and standardized rates have different weights; E19 samples indices; observing the entire fixed population eliminates sampling uncertainty about its mean.

- [ ] I can distinguish a population, observation, statistic and sampling distribution.
- [ ] I can explain weights, dependence and the limits of larger n.

Continue with [Estimation and Confidence Intervals](/docs/probability-statistics/estimation-and-confidence-intervals).
