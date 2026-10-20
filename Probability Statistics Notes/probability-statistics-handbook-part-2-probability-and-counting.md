# Probability and Statistics Handbook — Part 2: Probability and Counting

**F1: define the experiment before counting its outcomes.**

## 1. What probability describes

A sample space contains the possible outcomes of an experiment. An event is a set of those outcomes. A probability model assigns nonnegative weights with total one. The probability of an event is the total weight of its outcomes. A favorable-count/total-count calculation needs equally likely elementary outcomes. A fair coin flipped twice has four equally likely ordered sequences; the three possible head counts are not equally likely. [OpenStax: terminology](https://openstax.org/books/introductory-statistics-2e/pages/3-1-terminology).

```text
Experiment: two independent fair bits
Elementary outcomes: 00, 01, 10, 11
Event "exactly one 1": {01, 10}
Event "at least one 1": {01, 10, 11}
```

In interviews, translate words carefully. “At least one” includes every positive count; “exactly one” excludes two or more; “at most one” includes zero. First choose the experiment, then form the event. A request arriving and a request succeeding are different random quantities.

## 2. Complements, unions and intersections

```text
P(not A) = 1 - P(A)
P(A or B) = P(A) + P(B) - P(A and B)
P(A and B) = P(A) * P(B given A), when P(A) > 0
If A and B are independent: P(A and B) = P(A) * P(B)
```

“Or” includes overlap unless the question explicitly says otherwise. The subtraction in the union rule removes double counting. For many possible occurrences, the complement of “none” can be simpler than separately adding every way an event might happen.

Mutually exclusive events cannot happen together. Independent events factor their joint probability. Two exclusive events with positive probabilities cannot be independent. Sampling without replacement generally creates dependence between draws. [OpenStax: independent and exclusive events](https://openstax.org/books/introductory-statistics-2e/pages/3-2-independent-and-mutually-exclusive-events).

## 3. Counting: what makes outcomes distinct?

| Question | Count for selecting k distinct items from n |
| --- | --- |
| Ordered positions, no replacement | n!/(n-k)! |
| Unordered subset, no replacement | n!/[k!(n-k)!] |
| Ordered positions, independent choices with replacement | n^k |

The combination formula divides the ordered count by k! because all reorderings of a selected subset represent the same subset. That division is valid only if those reorderings really describe the same outcome. Named roles and sequential passwords preserve order; committee membership does not.

The multiplication principle counts stages of a construction. It does not, by itself, establish probabilistic independence. For example, the number of second-stage choices can depend on the first-stage selection.

## 4. Expectation starts with weighted outcomes

For a finite random variable, E(X)=sum of x*P(X=x). For an indicator I_A, E(I_A)=P(A). Linearity gives E(X+Y)=E(X)+E(Y) whenever the expectations exist, including dependent variables. Independence is needed for additional identities such as factoring an expectation of a product in the usual independent case.

Split a waiting time or count into interpretable components. The coupon example below separates collecting a new category into stages. You do not need to predict one likely run to calculate an average over possible runs.

## 5. Model assumptions to say aloud

Fair dice and uniform birthdays are invented models. An actual source can be biased, dependent or affected by previous draws. Collision calculations often give useful intuition for hash buckets, but a real hash function, key distribution and adversarial input require their own analysis.

An expected count can be fractional. A rare catastrophic outcome can make an expectation large while the median stays small. Before recommending a retry policy or capacity limit, inspect the distribution and operational constraints as well as the mean.

<!-- BEGIN WORKED EXAMPLES -->

## 6. Worked examples

### E01. At least one six on two dice

Roll two independent fair six-sided dice. Find the probability of at least one six, exactly one six and two sixes.

**Hint:** Use the complement for at least one, or inclusion-exclusion with the double-six overlap.

**Worked reasoning:** There are 36 equally likely ordered pairs. The complement has five non-six choices on each die, so P(at least one six) = 1 - (5/6)^2. Inclusion-exclusion gives 1/6 + 1/6 - 1/36. Exactly one six has two choices of position and five choices for the other face. The enumerator independently lists all 36 pairs.

Run `python examples/probability-statistics/compute.py E01` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "outcomes": 36,
  "at_least_one_six": 0.305556,
  "both_six": 0.027778,
  "exactly_one_six": 0.277778
}
```

**Common trap:** Adding the two one-die probabilities counts the double-six outcome twice.

**Interview follow-up:** What changes if the dice are dependent or have unequal face probabilities?

### E02. Committee versus assigned roles

From five distinct candidates, select three for a committee, then compare assigning three distinct roles.

**Hint:** Ask whether exchanging two selected people produces a different outcome.

**Worked reasoning:** For the unordered committee use C(5,3). For named roles use 5*4*3. Every unordered committee corresponds to 3! role assignments. Both counts assume one person cannot occupy two selected positions and every candidate is eligible.

Run `python examples/probability-statistics/compute.py E02` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "unordered_committees": 10,
  "ordered_roles": 60
}
```

**Common trap:** A combination count silently removes the ordering that named roles require.

**Interview follow-up:** How would replacement or a restricted role change the sample space?

### E03. Sampling without replacement

A bag has three red and two blue balls. Find the probability that two draws are both red, with and without replacement.

**Hint:** After the first red without replacement, both the numerator and denominator change.

**Worked reasoning:** Without replacement use (3/5)*(2/4), or choose two of the three red balls out of all two-ball subsets. With replacement and independent draws use (3/5)^2. Distinct physical balls remain different sampling units even when their colors match.

Run `python examples/probability-statistics/compute.py E03` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "two_red_without_replacement": 0.3,
  "two_red_with_replacement": 0.36
}
```

**Common trap:** Keeping the second red probability at 3/5 in the without-replacement experiment assumes independence that the design does not provide.

**Interview follow-up:** Which standard distribution describes the red count without replacement?

### E04. Shared birthdays

Under independent uniform birthdays on 365 days, find the probability of a shared birthday among 23 people. Ignore leap days.

**Hint:** It is easier to count everyone having a distinct birthday.

**Worked reasoning:** The no-collision probability is the product of (365-i)/365 for i from zero through 22. Subtract it from one. This is a collision between any pair, rather than a match to one preselected person's birthday. Uniformity and independence are model assumptions; actual birthday data need not satisfy them.

Run `python examples/probability-statistics/compute.py E04` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "people": 23,
  "shared_birthday_probability": 0.507297
}
```

**Common trap:** Using 22/365 answers a different and still approximate question about one fixed birthday.

**Interview follow-up:** Why can a hashing collision become plausible before the number of keys reaches the number of buckets?

### E05. Collect all three categories

Each independent draw returns one of three equally likely categories. What is the expected number of draws until all three have appeared?

**Hint:** Split the waiting time into collecting the first, second and third new category.

**Worked reasoning:** The waiting stages have success probabilities 1, 2/3 and 1/3, so their means are 1, 3/2 and 3. Add them by linearity of expectation. The total waiting time is random, and its mean need not be an integer. The verifier also uses an inclusion-exclusion identity rather than the stage implementation.

Run `python examples/probability-statistics/compute.py E05` from the repository root.

**Verified output** (six-decimal presentation; full precision in results.json):

```json
{
  "categories": 3,
  "expected_draws_to_collect_all": 5.5
}
```

**Common trap:** Three categories do not imply three expected draws; repeats can delay completion.

**Interview follow-up:** How does a rare category change the waiting time, and which independence assumptions are needed?

<!-- END WORKED EXAMPLES -->

## 7. Interview Q&A

### Q1. When can I divide favorable outcomes by total outcomes?
When the elementary outcomes being counted have equal probability. If they do not, sum their actual probability weights.

### Q2. Why is the complement useful?
The event “none” often has a simple product representation under independence, while “one or more” combines many overlapping possibilities.

### Q3. Is the union rule an independence assumption?
No. Inclusion-exclusion works generally. Independence is a separate condition that may simplify the intersection term.

### Q4. Can exclusive events be independent?
If both have positive probability, no: their joint probability is zero while the product is positive. Zero-probability boundary events need separate care.

### Q5. Why does replacement matter?
Without replacement, the remaining composition changes. With uniform independent replacement, each draw restarts from the same distribution.

### Q6. Does an expected value have to be a possible outcome?
No. It is a probability-weighted average. Fractional expected waiting times are compatible with integer-valued realized counts.

### Q7. Does linearity of expectation require independence?
No, when the expectations exist. Do not transfer that fact to variance or product calculations without checking their conditions.

### Q8. What should I clarify in a counting interview question?
Whether identities and order matter, whether replacement is allowed, which restrictions apply, and whether all counted elementary outcomes are equally likely.

## 8. Practice tasks

1. Solve E01 using both a complement and inclusion-exclusion.
2. Modify E02 so the same person can occupy several roles. State the new experiment before counting.
3. List every unordered two-ball physical sample for E03 and label its color outcome.
4. Explain why a fractional expected collection time does not describe a fractional realized draw.

**Answer checkpoints:** the two E01 methods must agree; replacement changes the role count to independent per-position choices; physical balls retain distinct identities; expectation averages across runs. Use the exact displayed cases for their original numeric answers.

- [ ] I can distinguish outcome counts from probability weights.
- [ ] I can state the order, replacement and overlap rules.

Continue with [Conditional Probability and Bayes](/docs/probability-statistics/conditional-probability-and-bayes).
