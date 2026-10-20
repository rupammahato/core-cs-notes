# Probability and Statistics Handbook — Part 4: Random Variables and Distributions

**F3: choose a model by its mechanism, support and assumptions.**

## 1. Random variables, mass, density and cumulative probability

A random variable maps experimental outcomes to values. A discrete probability mass function assigns probability to each supported value. A continuous density contributes probability through area over intervals; its height is not a point probability. The cumulative distribution function F(x)=P(X<=x) works for both kinds. The survival function is P(X>x)=1-F(x).

State the support. A count cannot be negative, a geometric trial count here starts at one, and a wait is nonnegative. Distribution names alone do not specify parameter conventions. [NIST: distribution gallery](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366.htm).

## 2. Moments and their limitations

```text
E(X) = sum x*p(x), or the corresponding density integral
Var(X) = E[(X-E(X))^2] = E(X^2) - E(X)^2
SD(X) = sqrt(Var(X))
E(aX+b) = aE(X)+b
Var(aX+b) = a^2 Var(X)
Var(X+Y) = Var(X)+Var(Y)+2Cov(X,Y)
```

Use these identities when the required moments exist. The mean and SD retain different units: variance has squared outcome units. Linearity of expectation does not allow you to discard covariance in a variance calculation.

## 3. Discrete model selection

| Model | Mechanism | Mean | Variance |
| --- | --- | --- | --- |
| Bernoulli(p) | One binary trial | p | p(1-p) |
| Binomial(n,p) | Fixed n independent equal-p trials | np | np(1-p) |
| Geometric(p), trials including success | Independent equal-p trials until first success | 1/p | (1-p)/p^2 |
| Poisson(lambda) | Count in a declared exposure under the Poisson model | lambda | lambda |
| Hypergeometric(N,K,n) | n draws without replacement; K successes in population N | nK/N | Binomial-style variance times finite-population correction |

For the binomial PMF, P(X=k)=C(n,k)p^k(1-p)^(n-k). The fixed trial count, binary result, common probability and independence all matter. [OpenStax: binomial distribution](https://openstax.org/books/introductory-statistics-2e/pages/4-3-binomial-distribution).

The Poisson parameter is an expected count for a specific exposure. Convert rate and interval units first. Independence of disjoint increments and constant rate characterize a homogeneous Poisson process; a Poisson marginal count assumption alone does not establish an entire temporal process.

## 4. Continuous models and rate conventions

| Model | Useful interpretation | Assumption or caution |
| --- | --- | --- |
| Uniform(a,b) | Equal density over a bounded interval | Equal density, not positive point mass |
| Exponential(rate) | Time to next homogeneous Poisson arrival | Mean=1/rate; constant hazard |
| Normal(mu,sigma^2) | A symmetric location/scale model | sigma is SD; squared parameter denotes variance |
| Student t(df) | Standardized mean uncertainty under a Normal sample model | Heavier tails; df convention matters |

An exponential survival function is exp(-rate*t) and is memoryless. A measured service time need not be exponential just because it is positive. Mixtures, aging and queueing often change the hazard. [NIST: exponential distribution](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3667.htm).

The t reference has heavier tails than Normal at small df, approaching Normal as df grows. Standardizing a small sample mean by its estimated SD introduces this reference under the iid Normal model. Welch uses an approximate t reference with estimated, potentially fractional df. [NIST: Student t distribution](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3664.htm).

## 5. Do not infer a distribution from a familiar word

“Arrivals” does not prove Poisson, “retry” does not prove geometric and “average” does not prove Normal. Check stable rate/probability, dependence, observation limits and fit to the relevant mechanism. Similar means do not imply similar tails or risk.

For Bernoulli sums, a Poisson approximation can be useful when trials are numerous and success probabilities are small under suitable conditions. A Normal approximation to binomial counts needs enough spread away from the boundaries and does not become an exact identity. Prefer a direct finite calculation when it is easy.

<!-- BEGIN WORKED EXAMPLES -->

## 6. Worked examples

### E11. Binomial successes

For ten independent trials with constant success probability 0.2, find P(X=3), E(X) and Var(X).

**Hint:** Choose the success positions, then weight every such sequence.

**Worked reasoning:** Use C(10,3)*0.2^3*0.8^7. The mean and variance are np and np(1-p). The verifier enumerates all binary sequences with rational probability weights, independently of the combination formula. A binary outcome alone does not establish independent trials or constant probability.

Run `python examples/probability-statistics/compute.py E11` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "P_X_equals_3": 0.201327,
  "mean": 2.0,
  "variance": 1.6
}
```

**Common trap:** Multiplying 0.2 by three does not calculate the probability of exactly three successes.

**Interview follow-up:** Why is a binomial model questionable for many sessions from the same user?

### E12. Geometric retries

Independent attempts succeed with probability 0.25. Count attempts including the first success. Find the expected count and P(T>3).

**Hint:** T>3 means the first three attempts all fail.

**Worked reasoning:** The geometric waiting count starts at one. Its expectation is 1/p, and its survival probability after three attempts is (1-p)^3. This model retries indefinitely with an unchanged independent success probability. A cap, backoff-related environment change or persistent failure changes the model.

Run `python examples/probability-statistics/compute.py E12` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "expected_trials_including_success": 4.0,
  "P_T_greater_3": 0.421875
}
```

**Common trap:** Some APIs count failures before success, whose expectation is (1-p)/p. State the convention before using a formula.

**Interview follow-up:** How would a maximum number of attempts change expected cost and success probability?

### E13. Poisson arrivals and units

A homogeneous Poisson model has rate two arrivals per hour. Find the probability of at least two arrivals during 30 minutes.

**Hint:** Convert the interval to hours before calculating its mean count.

**Worked reasoning:** The half-hour count has Poisson mean one. Subtract P(0)+P(1) from one, using exp(-lambda)*lambda^k/k!. The reference sums the remaining tail instead. Homogeneous Poisson arrivals assume independent increments and constant rate; bursts or shared external shocks can violate the model.

Run `python examples/probability-statistics/compute.py E13` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "expected_arrivals_in_half_hour": 1.0,
  "P_at_least_2": 0.264241
}
```

**Common trap:** Using the hourly rate as the half-hour mean doubles the modeled exposure.

**Interview follow-up:** What evidence would suggest overdispersion rather than a constant-rate Poisson count?

### E14. Exponential waiting and memorylessness

An exponential wait has rate 0.5 per minute. Find its mean, P(T>4), and P(T>6 given T>2).

**Hint:** Divide two survival probabilities for the conditional event.

**Worked reasoning:** The mean is 1/rate and survival at t is exp(-rate*t). The conditional ratio exp(-0.5*6)/exp(-0.5*2) equals survival over a fresh four-minute interval. Memorylessness belongs to this model, not every real process. An aging component or queue with changing load needs another distribution.

Run `python examples/probability-statistics/compute.py E14` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "mean_wait_minutes": 2.0,
  "P_wait_greater_4": 0.135335,
  "P_wait_greater_6_given_greater_2": 0.135335
}
```

**Common trap:** Rate and mean have reciprocal units; a rate of 0.5 per minute does not mean a half-minute expected wait.

**Interview follow-up:** How does the exponential waiting model connect to homogeneous Poisson arrivals?

### E15. Normal tail versus point density

Under a continuous Normal model with mean 100 and standard deviation 15, find P(X>130) and P(X=130).

**Hint:** Standardize the threshold and distinguish a tail area from a density height.

**Worked reasoning:** The standardized threshold is two. The survival area is computed using erfc to avoid unnecessary subtraction in the tail. The probability of any one exact point is zero for this continuous model. Real rounded observations can give nonzero probability to a reported value because a rounded value represents an interval.

Run `python examples/probability-statistics/compute.py E15` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "mean": 100,
  "sd": 15,
  "threshold": 130,
  "z_score": 2.0,
  "P_X_greater_130": 0.02275,
  "P_X_equals_130": 0.0
}
```

**Common trap:** A probability density evaluated at the threshold is not its point probability or its tail probability.

**Interview follow-up:** What interval corresponds to a rounded integer observation, and what changes if the model is discrete?

<!-- END WORKED EXAMPLES -->

## 7. Interview Q&A

### Q1. What distinguishes a PMF from a PDF?
A PMF assigns point probabilities. A PDF is integrated over intervals to obtain probabilities and can exceed one in height.

### Q2. What does a CDF describe?
The probability that the variable is at most a threshold. Its jumps correspond to point masses in a discrete distribution.

### Q3. When is a count binomial?
When the stated model has a fixed number of independent binary trials with a common success probability, rather than merely binary recorded outcomes.

### Q4. What geometric convention is used here?
Attempts including the first success, with support 1,2,... . Counting failures before success shifts the variable and its mean.

### Q5. How do Poisson rate and mean differ?
Rate is per unit exposure; the count mean is rate multiplied by exposure, under the homogeneous model.

### Q6. What does memoryless mean?
Conditional survival after an elapsed wait equals survival over a fresh additional interval, under the geometric/exponential model's relevant convention.

### Q7. What happens to variance after scaling?
Multiplication by a scales variance by a squared; adding a constant leaves variance unchanged.

### Q8. Does the mean determine the distribution?
No. Different distributions can have the same mean and very different spread, tails, support and dependence behavior.

## 8. Practice tasks

1. List a realistic violation of every assumption in E11's binomial model.
2. Reinterpret E12 using failures before success and explain the shift symbolically.
3. Derive E13 with minutes rather than hours and confirm the same half-hour mean.
4. Explain how recording continuous E15 outcomes rounded to integers changes the interpretation of an exact reported value.

**Answer checkpoints:** users can generate dependent trials or different probabilities; failures equal attempts minus one; consistent units leave the Poisson mean unchanged; a rounded value represents an interval of the continuous variable.

- [ ] I can choose a distribution from a mechanism and state its support.
- [ ] I can distinguish a rate, a density and a probability.

Continue with [Descriptive Statistics and Sampling](/docs/probability-statistics/descriptive-statistics-and-sampling).
