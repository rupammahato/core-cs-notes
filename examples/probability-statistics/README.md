# Probability and statistics examples

Thirty-five synthetic worked examples accompany the nine-file Probability Statistics Notes subject. The earlier 135 handbooks, including the SQL book, remain byte-identical to the captured snapshot.

## Run from the repository root

```powershell
python examples/probability-statistics/compute.py E07
python examples/probability-statistics/compute.py E25
python examples/probability-statistics/verify.py
python examples/probability-statistics/build_book.py
python examples/probability-statistics/validate_content.py
```

Python 3.13.15, standard library only. No SciPy, NumPy, account, persistent database, random simulation or external data is required. `compute.py` without an example ID records all raw outputs in results.json. With an ID it prints the six-decimal presentation used in the handbook. Input definitions are explicit in compute.py; cases.json stores the associated questions, reasoning, traps and follow-ups.

The 71 runtime checks comprise 35 independent worked-example reference projections, nine closed-form Student-CDF checks, three published rounded critical-value comparisons, twelve boundary/property checks, ten rejected invalid inputs and two preservation checks. Independent references use weighted finite enumeration, rational arithmetic, algebraic CDFs, Python's separate correlation/regression/quantile routines, and fixed-grid quadrature. They do not read saved answer values as their oracle. Reference projections check selected mathematically meaningful output fields, rather than claiming a proof of every input or every metadata field.

The teaching Student-CDF implementation integrates the density with adaptive Simpson integration and numerically inverts it. It is checked in the exercised range, including fractional Welch degrees of freedom. It is not a certified general-purpose tail-probability library; extreme tails and arbitrary inputs are outside the verification claim. Default comparisons use 1e-8 relative/absolute tolerance; published three-decimal t references use 5e-4 relative/absolute tolerance. Floating-point raw results and rounded note outputs are both retained.

E24 enumerates the empirical bootstrap distribution exactly with respect to observed-index resampling and a declared linear quantile rule. That is not exact confidence coverage for an unknown population. E25 computes actual binomial interval coverage at one specified n and true p. E29 follows a complete balanced assignment design under a sharp no-effect null and absolute-difference ordering. E30 uses an approximate fixed-horizon Normal power plan; it neither computes exact achieved power nor a sequential or cluster-adjusted design. Its independent twenty-test family error is not a calculation for repeated correlated peeking. E34 is descriptive in-sample residualization, not an executed CUPED experiment.

`build_book.py` replaces only the marked worked-example sections of the seven teaching modules. The root handbook Markdown remains the authored source for theory, interview Q&A and practice. `validate_content.py` checks source/output fidelity and the earlier-note snapshot after the website sync. `site-smoke.mjs` checks the built site's routes and filtered search using a temporary loopback preview that it closes. Port 3000 stays stopped unless separately requested.

The website workflow is to sync the notes, run the production build, then run `node examples/probability-statistics/site-smoke.mjs` from the root. The recorded local build uses this machine's local font-response fixture in its restricted network environment; normal site font configuration is unchanged.

Primary references and their scope are in research.json. Tests verify calculations under the stated synthetic models. They do not establish sampling validity, actual assignment, causality, real-world model fit or learner completion. Manual solving and mocks remain learner work.

The numerical calibration references include the [NIST Student t critical-value table](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm). Standard-library API behavior is documented in the [Python statistics reference](https://docs.python.org/3.13/library/statistics.html). content-validation.json records documentation audits separately from runtime checks; site-validation.json records HTTP route/content checks and subject-filtered search. validation-summary.json combines their scope and outcomes without treating them as one homogeneous test count.
