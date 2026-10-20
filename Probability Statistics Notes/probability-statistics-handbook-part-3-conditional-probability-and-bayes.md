# Probability and Statistics Handbook — Part 3: Conditional Probability and Bayes

**F2: keep the conditioning population visible.**

## 1. A conditional is a restricted population

For P(B)>0, P(A given B)=P(A and B)/P(B). Read this as the share of B's probability mass also belonging to A. Reversing the condition changes the denominator. The card example below makes that change concrete. With continuous variables, conditioning on an exact value uses conditional distributions rather than dividing by a zero point probability.

```text
All observations
  -> restrict to those satisfying B
      -> ask what fraction also satisfy A
```

The multiplication rule reverses the identity: P(A and B)=P(A given B)*P(B). Longer event sequences use repeated conditioning; they do not automatically become products of marginal probabilities.

## 2. Total probability and Bayes' rule

If H1,...,Hm form a disjoint exhaustive partition:

```text
P(E) = sum_i P(E given Hi) * P(Hi)
P(Hj given E) = P(E given Hj) * P(Hj) / P(E)
```

The prior weights possible sources before observing E. The likelihood says how compatible E is with a source. The evidence normalizes across every modeled source, producing the posterior. All source categories must be accounted for, and the evidence must have positive probability. [Penn State STAT 414: Bayes' theorem](https://online.stat.psu.edu/stat414/Lesson06).

Natural frequencies are often easier than symbolic substitution. Choose a hypothetical population size, count how much mass travels along each branch, then condition on the observed branch total. Expected fractional counts are acceptable when the population size is just a scaling device.

## 3. Base rates and classifier vocabulary

| Quantity | Condition being held fixed |
| --- | --- |
| Sensitivity / true-positive rate | Actual positives |
| Specificity / true-negative rate | Actual negatives |
| False-positive rate | Actual negatives |
| Precision / positive predictive value | Predicted or alerted positives |

Specificity is one minus false-positive rate. Precision depends on prevalence as well as sensitivity and specificity. A detector evaluated on an artificially balanced dataset may have a different precision in a low-prevalence deployment. Check labels, population shift, thresholds and observation completeness before transferring a measured number.

The hypothetical fraud example is arithmetic practice. It does not establish a real detector's calibration, economic utility or acceptable threshold. A decision also depends on false-alert review costs and the losses from missed fraud.

## 4. Independence at the right level

Events A and B are independent if P(A and B)=P(A)P(B). Conditional independence given H means P(A and B given H)=P(A given H)P(B given H), for the relevant conditional distributions. These are different statements.

Two detector outputs can be conditionally independent within each fraud class but marginally dependent because both respond to the same underlying status. Conversely, marginal independence does not ensure conditional independence after selecting a subgroup. Do not multiply evidence likelihoods merely because they came from separate services.

Pairwise independence checks each pair. Mutual independence requires factorization for every subset. The XOR case below is a small counterexample: all pairs pass while the triple fails.

## 5. Updating is a model operation

Bayesian updating does not mean “change confidence however seems reasonable.” The prior, likelihood and observation process specify the update. Duplicate reports of the same event provide one piece of evidence, while two suitably modeled observations can provide more.

An observation with zero probability under every modeled hypothesis cannot be normalized. Revisit the model rather than divide by zero or invent a posterior. New categories, missing labels and measurement errors can be reasons the observation model was incomplete.

<!-- BEGIN WORKED EXAMPLES -->

## 6. Worked examples

### E06. Reverse conditionals on cards

Draw one uniform card from a standard 52-card deck. Compare P(king given red) with P(red given king).

**Hint:** Conditioning changes the denominator.

**Worked reasoning:** The red-card condition restricts the sample space to 26 cards containing two kings. The king condition restricts it to four cards containing two red cards. The overlap is the same, but the conditioning populations differ. The verifier constructs all cards and filters each conditioning set.

Run `python examples/probability-statistics/compute.py E06` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "red_cards": 26,
  "red_kings": 2,
  "king_given_red": 0.076923,
  "red_given_king": 0.5
}
```

**Common trap:** Reversing the conditional preserves the intersection but usually changes the probability.

**Interview follow-up:** What extra information would let you derive a reverse conditional from the forward one?

### E07. Fraud alerts and the base rate

Fraud prevalence is 1%. An alert catches 90% of fraud and flags 5% of legitimate transactions. What fraction of alerts indicate fraud?

**Hint:** Use natural frequencies in 10,000 transactions.

**Worked reasoning:** There are 100 fraud transactions, of which 90 alert. Of 9,900 legitimate transactions, 495 alert. Condition on the 585 alerted transactions, giving 90/585. These are a hypothetical model's expected frequencies, not actual monitoring data or a measured classifier guarantee.

Run `python examples/probability-statistics/compute.py E07` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "true_alerts_per_10000": 90,
  "false_alerts_per_10000": 495,
  "fraud_given_alert": 0.153846
}
```

**Common trap:** Sensitivity is P(alert given fraud), rather than P(fraud given alert). Ignoring legitimate transactions discards most of the denominator.

**Interview follow-up:** How does the posterior change if prevalence rises while sensitivity and false-positive rate stay fixed?

### E08. Which server produced the error?

Server A handles 70% of requests with a 1% error rate. B handles 30% with a 4% error rate. Find the overall error probability and P(B given error).

**Hint:** Weight the two branches by traffic share before reversing the condition.

**Worked reasoning:** For 10,000 model requests, A contributes 70 errors and B contributes 120. Overall error probability is 190/10,000 and B's share among errors is 120/190. Traffic allocation forms an exhaustive, disjoint partition. The question is attribution under this model, not proof of an operational root cause.

Run `python examples/probability-statistics/compute.py E08` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "error_probability": 0.019,
  "server_B_given_error": 0.631579
}
```

**Common trap:** Averaging the two error percentages equally ignores traffic share.

**Interview follow-up:** What must be measured before applying this calculation to a load-balanced fleet?

### E09. Pairwise independence is weaker

Let A mean the first fair bit is one, B the second is one, and C that the two independent bits differ. Are these three events mutually independent?

**Hint:** Check both pairwise intersections and the triple intersection.

**Worked reasoning:** The four bit pairs are equally likely. Every event has probability one half and every pairwise intersection has probability one quarter. But A and B together force both bits to one, which makes C false. Thus the triple intersection is zero rather than the product of all three marginals.

Run `python examples/probability-statistics/compute.py E09` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "P_A": 0.5,
  "P_B": 0.5,
  "P_C": 0.5,
  "P_A_and_B": 0.25,
  "P_A_and_C": 0.25,
  "P_B_and_C": 0.25,
  "P_all_three": 0.0,
  "product_of_marginals": 0.125
}
```

**Common trap:** Checking every pair does not establish the factorization required for every larger subset.

**Interview follow-up:** When can a dependence hidden in a joint system matter even though pairwise summaries look harmless?

### E10. Two alerts versus one alert copied twice

Reuse the fraud model. Compare two alerts that are conditionally independent given fraud status with a duplicate copy of the same alert.

**Hint:** Multiply likelihoods only under the stated conditional-independence model.

**Worked reasoning:** For two conditionally independent alerts, the joint sensitivity is 0.9^2 and the joint false-positive rate is 0.05^2; apply Bayes to those likelihoods. A duplicate carries no additional information, so its posterior stays at the single-alert result. The alerts can remain marginally dependent because they share the hidden fraud status.

Run `python examples/probability-statistics/compute.py E10` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "two_conditionally_independent_alerts": 0.765957,
  "duplicate_of_same_alert": 0.153846
}
```

**Common trap:** Treating repeated logging or two correlated detectors as independent evidence creates unjustified certainty.

**Interview follow-up:** What joint conditional rates would replace the products if the two detectors are correlated?

<!-- END WORKED EXAMPLES -->

## 7. Interview Q&A

### Q1. Why is P(A given B) different from P(B given A)?
Their intersections agree but their conditioning populations generally differ. Use counts or Bayes' rule to make the denominators explicit.

### Q2. What does the evidence denominator do?
It sums the observation probability across the modeled hypothesis partition, ensuring that posterior probabilities normalize.

### Q3. Can a highly sensitive detector have poor precision?
Yes. When positives are rare, a modest false-positive rate can produce many more false than true alerts.

### Q4. Is independence the same as conditional independence?
No. Conditioning changes the distribution. State which variables are held fixed and whether likelihood factorization is justified there.

### Q5. Why does a duplicate alert not multiply evidence?
It is determined by the original alert. Treating it as an independent observation counts the same information again.

### Q6. Is pairwise independence enough for three variables?
No. The XOR example has independent pairs but fails the triple factorization required for mutual independence.

### Q7. What does a zero evidence denominator mean?
The observed event is impossible under the stated model. A normalized conditional probability is undefined under that model.

### Q8. Does Bayes' rule establish a causal explanation?
No. It transforms probabilities within an assumed model. Causal claims require a justified causal structure or design.

## 8. Practice tasks

1. Rebuild E07's frequency tree without formulas, retaining every alerted transaction.
2. Raise E07 prevalence to 10%, keeping the conditional alert rates fixed.
3. Enumerate E09's four bit pairs and verify every pairwise intersection.
4. Explain which joint likelihoods you would need for correlated alerts instead of squaring two rates.

**Answer checkpoints:** at 10% prevalence the posterior is 2/3, as checked by the verifier. Pairwise intersections in E09 are 1/4 while the triple is zero. Correlated alerts need their joint class-conditional probabilities rather than a product assumption.

- [ ] I can interpret a reverse conditional with a frequency table.
- [ ] I can distinguish duplicate, independent and conditionally independent evidence.

Continue with [Random Variables and Distributions](/docs/probability-statistics/random-variables-and-distributions).
