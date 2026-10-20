# Probability and Statistics Handbook — Part 1: Master Roadmap

**Understand uncertainty, calculate carefully and explain what the result supports.**

## 0. What this companion adds

The product track explains decisions and experiments; the SQL lab practices obtaining trustworthy counts. This book explains the mathematical uncertainty behind those counts. Begin with outcomes and denominators, then build toward estimators, intervals, tests and models.

**Authoring status: complete.** Nine chapters contain seven teaching modules, 35 computed examples, 56 module interview Q&As, 28 practice tasks, 30 final oral checks and two 45-minute mocks. Topic selection and mock formats are editorial placement preparation, rather than a measured ranking of company interview questions.

**Local verification, 21 October 2026:** 71 checks passed on Python 3.13.15. They cover all 35 worked-example reference projections, nine closed-form distribution checks, three published t-table comparisons, twelve boundary/property checks, ten rejected invalid inputs and two source-preservation checks. The examples use the Python standard library, invented inputs and no external service. Numerical references verify selected calculations under their stated models; they cannot verify the suitability of a model for a real dataset.

## 1. Reading map

| Module | Chapter | What you should be able to explain |
| --- | --- | --- |
| F1 | [Probability and counting](/docs/probability-statistics/probability-and-counting) | Sample spaces, complements, overlap, order and replacement |
| F2 | [Conditional probability and Bayes](/docs/probability-statistics/conditional-probability-and-bayes) | Conditioning populations, base rates and independence |
| F3 | [Random variables and distributions](/docs/probability-statistics/random-variables-and-distributions) | Choose a model, state its assumptions and calculate its moments |
| F4 | [Descriptive statistics and sampling](/docs/probability-statistics/descriptive-statistics-and-sampling) | Summaries, units, weights, sampling distributions and CLT limits |
| F5 | [Estimation and confidence intervals](/docs/probability-statistics/estimation-and-confidence-intervals) | Estimates, uncertainty, coverage, Wilson and bootstrap |
| F6 | [Hypothesis tests and experiments](/docs/probability-statistics/hypothesis-tests-and-experiments) | Null models, errors, pairing, exact tests and power planning |
| F7 | [Correlation and regression](/docs/probability-statistics/correlation-and-regression) | Association, linear fits, confounding and prediction limits |
| Revision | [Consolidation and mocks](/docs/probability-statistics/consolidation-and-mocks) | Distinguish close concepts, diagnose failures and defend an analysis |

Probability asks what observations a specified model produces. Statistical inference works from observations toward statements about unknown parameters or populations, using a sampling/design model. Neither direction makes an assumption true merely because the arithmetic works.

## 2. Prerequisites and bridges

- Basic fractions, algebra, sums, squares and square roots are enough to begin. Calculus appears as an interpretation of continuous probability, rather than an entrance requirement.
- [Product analytics](/docs/product-analytics/product-analytics-experiments) supplies metric contracts, experimental assignment and decision context.
- [Python and Excel analysis](/docs/product-analytics/python-excel-analysis) supplies practical data-cleaning and reconciliation context.
- [SQL interview lab](/docs/sql-interview) supplies population, grain, missingness and event-window practice.
- [Analytics pipelines](/docs/system-design/analytics-event-pipeline) supplies late-data and publication context.

An inference can be precisely calculated over the wrong SQL population. Check the data contract and the statistical contract together.

## 3. A repeatable interview method

1. Define the random experiment, population or estimand in plain language.
2. Name the observational unit, outcome, amount/time units and denominator.
3. State replacement, independence, sampling or assignment assumptions.
4. Choose an identity, distribution, estimator or test that matches that contract.
5. Calculate a small example and inspect a boundary case.
6. Interpret the answer in the original units and distinguish uncertainty from effect size.
7. Say which new observation or design failure would change your answer.

Each worked case includes a prompt, hint, derivation, actual output, trap and follow-up. Try the prompt first. The displayed output is rounded to six decimal places; results.json preserves the full recorded floating-point values.

## 4. Run the worked examples

From the repository root:

```powershell
python examples/probability-statistics/compute.py E07
python examples/probability-statistics/compute.py E25
python examples/probability-statistics/verify.py
```

Read `examples/probability-statistics/README.md` for the complete workflow. Exact enumeration here means all outcomes of a specified small model are included. It does not mean a bootstrap interval has exact population coverage, a model describes real users, or an observed association is causal. No random simulation, SciPy execution, production experiment or deployment is asserted.

## 5. Suggested routes

**First placement interview:** F1 → F2 → F3 → F4 → F5 → F6 → final oral checks.

**Product/data analyst:** cover all modules, then combine the two mocks with SQL cohort and experiment questions.

**Backend engineer:** prioritize retries, arrivals, latency summaries, dependence, uncertainty and regression limits. Use actual system measurements before selecting a probabilistic model.

The book introduces advanced bridges such as beta-binomial updating, cluster dependence, CUPED and sequential analysis. It does not implement a general Bayesian inference library, cluster-robust standard errors or a sequential testing engine.

## 6. Authoring and learning status

- [x] Seven foundation modules and their worked examples authored.
- [x] Calculations and selected independent references executed.
- [x] Consolidation, oral checks and two timed mocks authored.
- [ ] I can explain a denominator and assumption before choosing a formula.
- [ ] I can reproduce the examples and predict a changed input.
- [ ] I have attempted both mocks and recorded my mistakes.

Begin with [Probability and Counting](/docs/probability-statistics/probability-and-counting).
