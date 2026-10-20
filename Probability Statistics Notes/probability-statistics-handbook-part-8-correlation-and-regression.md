# Probability and Statistics Handbook — Part 8: Correlation and Regression

**F7: distinguish a useful description, a prediction and a causal claim.**

## 1. Covariance, correlation and ranks

Covariance summarizes joint centered variation and has product units. Pearson correlation divides by both SDs to produce a unitless linear-association measure between minus one and one, when both variances are positive. Constant variables make this correlation undefined; returning zero would invent information.

Correlation is symmetric but a predictive slope is directional and has units. Zero Pearson correlation means no linear covariance, rather than independence. A deterministic curved relationship can have zero correlation. Spearman correlation instead calculates Pearson correlation on ranks, with an explicit tie convention, and describes monotone association. This lab executes Pearson calculations, rather than a Spearman significance test.

## 2. Ordinary least squares with an intercept

For paired observations, OLS chooses coefficients minimizing the sum of squared vertical residuals:

```text
Sxx = sum((xi-xbar)^2)
Sxy = sum((xi-xbar)*(yi-ybar))
slope b1 = Sxy/Sxx
intercept b0 = ybar - b1*xbar
prediction yi_hat = b0 + b1*xi
residual ei = yi - yi_hat
```

The fitted line passes through (xbar,ybar). With an intercept, residuals sum to zero and have zero sample cross-product with x, up to numerical precision. Those fitting identities do not demonstrate that the model is correct. [OpenStax: regression equation](https://openstax.org/books/introductory-statistics-2e/pages/12-3-the-regression-equation).

## 3. Fit and uncertainty answer different questions

```text
SSE = sum(residual_i^2)
SST = sum((yi-ybar)^2)
R_squared = 1 - SSE/SST, when SST > 0
training MSE = SSE/n
usual simple-model residual variance estimate = SSE/(n-2)
```

For this simple OLS model with an intercept on the same observations, R-squared equals Pearson r squared. Do not generalize that identity indiscriminately to models without an intercept, different samples or arbitrary prediction scores.

Computing OLS does not require Normal outcomes. Usual small-sample t inference additionally relies on an appropriate linear error model, including conditional mean structure, independence and variance assumptions; Normal errors give the familiar exact small-sample reference. Unequal conditional variances call for appropriate uncertainty methods, rather than silently reusing the standard formula.

## 4. Inspect residuals and prediction conditions

Plot residuals against fitted values, predictors and time. Curvature can indicate a missing nonlinear structure; a fan shape can indicate changing variance; runs over time can indicate dependence. Check leverage and influential observations, label/data quality, train/test separation and extrapolation. A high R-squared alone is insufficient model validation. [NIST: evaluating model fit](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd44.htm).

Outlier is a descriptive label, not permission to remove a row. A valid extreme value can be central to the target. Correct demonstrable measurement errors and use a declared robust/modeling policy when appropriate.

Training error describes the data used to fit the line. Future prediction performance needs suitable evaluation, with time-respecting splits when deployment predicts future periods. Leakage from future information can make an otherwise careful evaluation misleading. A prediction outside the observed range is an extrapolation whose credibility requires substantive reasoning.

## 5. Confounding, stratification and Simpson reversal

A pooled comparison mixes within-segment outcomes with segment weights. Different mixes can reverse an association seen in each segment. E33 shows the arithmetic and then standardizes both arms to a common mixture.

Standardization defines a weighted comparison; it does not by itself identify a causal effect. The role and timing of the segment variable matter. Pre-treatment confounders, mediators and selection variables have different causal roles. Conditioning on an intervention-affected variable can introduce bias. Specify the causal question and design before deciding what to control for.

## 6. Covariate adjustment and the CUPED bridge

If a pre-treatment covariate predicts an outcome, an appropriate adjusted estimator can reduce treatment-effect uncertainty under its design assumptions. Production CUPED/related regression adjustment is about the variance of an estimator, rather than merely editing a raw-data variance number. [Microsoft Research: variance reduction](https://www.microsoft.com/en-us/research/articles/deep-dive-into-variance-reduction/).

E34 shows centered in-sample linear residualization. It preserves the pooled mean and removes sample linear variation. It is not a randomized treatment/control analysis and proves no real gain in experimental power. A production method needs valid pre-treatment features, a declared estimator and variance calculation, assignment assumptions and evaluation of its actual behavior.

## 7. How to defend a model in an interview

Explain the target response and intended use, why the predictors are available at prediction time, the fitted relationship and what a coefficient means in its units. Describe residual and evaluation checks. Separate descriptive, predictive and causal interpretations; a coefficient does not become causal because its p-value is small.

<!-- BEGIN WORKED EXAMPLES -->

## 8. Worked examples

### E31. Fit a simple line

For x=[1,2,3,4,5] and y=[2,4,5,4,5], compute Pearson correlation and an ordinary least-squares line with an intercept.

**Hint:** Use centered cross-products; keep correlation separate from a slope with units.

**Worked reasoning:** The slope is Sxy/Sxx and the intercept makes the fitted line pass through the pair of sample means. Pearson r scales the cross-product by both centered sums of squares. The verifier compares with Python's independent standard-library regression and correlation functions. R-squared equals r-squared for this simple least-squares fit with an intercept on the same rows.

Run `python examples/probability-statistics/compute.py E31` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "x": [
    1,
    2,
    3,
    4,
    5
  ],
  "y": [
    2,
    4,
    5,
    4,
    5
  ],
  "slope": 0.6,
  "intercept": 2.2,
  "r": 0.774597,
  "r_squared": 0.6,
  "sse": 2.4,
  "residuals": [
    -0.8,
    0.6,
    1.0,
    -0.6,
    -0.2
  ]
}
```

**Common trap:** A positive association does not establish that changing x would cause the fitted change in y.

**Interview follow-up:** Which assumptions are needed for standard regression uncertainty, beyond simply computing this line?

### E32. Zero correlation with perfect dependence

For x=[-2,-1,0,1,2] and y=x^2, calculate Pearson correlation and the best straight-line fit.

**Hint:** Symmetry cancels the linear cross-product.

**Worked reasoning:** The correlation and fitted slope are zero, but y is fully determined by x. The intercept is the sample mean of y, and the straight-line R-squared is zero. A curved model or a scatterplot would reveal the deterministic relationship. Independence is much stronger than absence of linear association.

Run `python examples/probability-statistics/compute.py E32` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "x": [
    -2,
    -1,
    0,
    1,
    2
  ],
  "y": [
    4,
    1,
    0,
    1,
    4
  ],
  "slope": 0.0,
  "intercept": 2.0,
  "r": 0.0,
  "r_squared": 0.0,
  "sse": 14.0,
  "residuals": [
    2.0,
    -1.0,
    -2.0,
    -1.0,
    2.0
  ]
}
```

**Common trap:** Zero correlation does not generally imply independence; special model families need additional assumptions for that conclusion.

**Interview follow-up:** Would a larger sample fix the straight-line model's inability to represent this shape?

### E33. Simpson reversal and standardization

Easy segment: A converts 81/90 and B 19/20. Hard segment: A 1/10 and B 16/80. Compare segment rates, pooled rates and rates standardized to an equal easy/hard mixture.

**Hint:** The two variants receive very different segment mixtures.

**Worked reasoning:** B's observed rate exceeds A's within each segment, while A's pooled rate is larger because A has far more easy-segment observations. Equal-mixture standardization gives a third, explicitly weighted comparison. These are arithmetic descriptions. Whether to adjust for a variable causally depends on its timing, the design and the estimand.

Run `python examples/probability-statistics/compute.py E33` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "A_easy": 0.9,
  "B_easy": 0.95,
  "A_hard": 0.1,
  "B_hard": 0.2,
  "A_overall": 0.82,
  "B_overall": 0.35,
  "A_equal_mix": 0.5,
  "B_equal_mix": 0.575
}
```

**Common trap:** Automatically controlling for every available segment can introduce bias, especially when the variable is affected by treatment.

**Interview follow-up:** What would you inspect before interpreting a segment imbalance as a data-quality problem?

### E34. A centered covariate adjustment

Reuse E31's x and y. Compute theta=Cov(x,y)/Var(x), then adjusted y=y-theta*(x-mean(x)). Compare sample means and variances.

**Hint:** Centering preserves the overall mean; subtracting the fitted component removes linear variation in this sample.

**Worked reasoning:** The descriptive coefficient is 0.6. Centering makes adjusted and raw means equal, while sample variance falls from 1.5 to 0.6. The 60% reduction equals this fit's R-squared. This is in-sample algebra illustrating covariate adjustment, not an executed randomized CUPED experiment or evidence about the variance of a real treatment-effect estimator.

Run `python examples/probability-statistics/compute.py E34` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "theta": 0.6,
  "raw_mean": 4,
  "adjusted_mean": 4.0,
  "raw_sample_variance": 1.5,
  "adjusted_sample_variance": 0.6,
  "descriptive_variance_reduction": 0.6
}
```

**Common trap:** Choosing post-treatment covariates or reporting in-sample residual variance as proven experimental power can mislead.

**Interview follow-up:** Which pre-treatment, assignment-independent covariates and validation would a real variance-reduction method require?

### E35. Training fit is not future performance

Using E31's fitted line, compare training MSE, the usual residual-variance estimate and the prediction at x=6. Is future prediction error known?

**Hint:** The same residual sum of squares has different denominators for different purposes.

**Worked reasoning:** Training MSE divides SSE by five. Estimating residual variance under the standard simple linear model divides by n-2 because slope and intercept were estimated. The prediction at six extends beyond the observed x range. No held-out outcomes were supplied, so out-of-sample MSE is explicitly unknown rather than copied from training fit.

Run `python examples/probability-statistics/compute.py E35` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "training_n": 5,
  "training_mse": 0.48,
  "residual_variance_estimate": 0.8,
  "prediction_at_x_6": 5.8,
  "out_of_sample_mse": null
}
```

**Common trap:** A numerical prediction and a good training score do not verify generalization, extrapolation or causal usefulness.

**Interview follow-up:** How would you construct a time-respecting evaluation and distinguish a mean-response interval from an individual prediction interval?

<!-- END WORKED EXAMPLES -->

## 9. Interview Q&A

### Q1. Is covariance unitless?
No. Covariance has product units. Pearson correlation normalizes by both SDs and is unitless when defined.

### Q2. Does zero correlation mean independence?
Not generally. The quadratic example has zero linear correlation and a deterministic dependency.

### Q3. What does OLS minimize?
The sum of squared vertical residuals for the declared model and observations. That objective is separate from a causal or generalization claim.

### Q4. Must y itself be Normally distributed to fit a line?
No. Calculating OLS is algebraic. Standard inference needs assumptions about the conditional errors and design, rather than merely a Normal marginal histogram.

### Q5. Does a large R-squared establish a good model?
No. Inspect residuals, leakage, target relevance and out-of-sample performance. A high value does not establish causality.

### Q6. What creates Simpson reversal?
Different segment mixtures can overwhelm consistent within-segment associations. Check weights and the causal role of any adjustment variable.

### Q7. Is centered residualization a verified CUPED experiment?
No. It illustrates fitting algebra. Experimental estimator validity and variance reduction require a design, estimator and appropriate uncertainty analysis.

### Q8. Why is prediction outside the observed range risky?
The fitted relationship has not been observed there. Mechanisms, support and uncertainty can change beyond the training range.

## 10. Practice tasks

1. Verify E31's residual sum and residual/x cross-product, then explain why these fitting identities do not validate a model.
2. Sketch E32's five points and explain what Pearson correlation misses.
3. Reconstruct E33's raw counts and compare observed-mixture with equal-mixture estimands.
4. Explain why E35 leaves future MSE unknown rather than reporting training MSE as a proxy.

**Answer checkpoints:** fitted residual identities follow OLS with an intercept; a curve can defeat linear association; the mixture weights change the descriptive question; no held-out outcomes were supplied to verify future error.

- [ ] I can interpret correlation, slope, residuals and R-squared separately.
- [ ] I can distinguish descriptive adjustment, prediction and causal inference.

Continue with [Consolidation and Mocks](/docs/probability-statistics/consolidation-and-mocks).
