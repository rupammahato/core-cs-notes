# Product and Analytics Casebook — Part 6: Pricing and Business Models

**C10–C12: name the value unit, cost basis, denominator and assumptions.**

## Before the cases

A pricing case combines a customer value hypothesis, a cost model, a packaging choice and a way to learn demand. Cost arithmetic alone cannot supply willingness to pay, incremental demand or future retention.

Usage-based subscriptions can represent several patterns, including fixed fees with overages and credit-based consumption. The operational contract still needs to say what is metered and when entitlements change. No current provider fee or product price is assumed in these fictional cases. [Stripe pricing models](https://docs.stripe.com/products-prices/pricing-models), [Stripe's credits introduction](https://stripe.com/blog/introducing-credits-for-usage-based-billing).

Every monetary input below is invented USD cents. “Contribution” refers to the selected costs explicitly named in that case, rather than a universal accounting classification. Review [unit economics](/docs/product-analytics/pricing-unit-economics) for the foundations.

<!-- BEGIN WORKED CASES -->

## C10. Price AI credits with failed work included

A fixed-price plan includes up to 100 useful AI jobs. Eighty succeed and twenty extra attempts fail. Calculate the selected contribution model and discuss whether the plan is economically credible.

### Clarify the question

- What customer action consumes a credit, and which failures are charged?
- Which provider, storage, payment and support costs are included or missing?
- What usage distribution and refund policy apply over the plan period?

### Frame the user and objective

Offer a customer-understandable value unit while keeping usage economics observable. Credits are an entitlement/accounting mechanism; they do not directly equal provider calls or recognized revenue.

### Evidence status and complete fixture inputs

All amounts are invented integer cents. Each useful job requires one successful attempt in this fixture, plus twenty failed attempts. Selected variable costs are treated as complete for this scenario; staffing, taxes, acquisition and other overhead are excluded. Refunds are a supplied amount, not a forecasted rate.

```json
{
  "price_cents": 2000,
  "refund_cents": 200,
  "useful_jobs": 80,
  "failed_attempts": 20,
  "cost_per_attempt_cents": 12,
  "payment_cost_cents": 90,
  "storage_cost_cents": 100,
  "target_contribution_margin": 0.5
}
```

### Metric and decision contract

Net collected = supplied price minus supplied refund. Selected contribution = net collected minus attempt, payment and storage costs. Cost per useful job includes failed attempts. The target collection floor assumes the same selected cost, rather than predicting demand or changing fees.

### Work the evidence

Charge all 100 attempts to cost even though only 80 useful jobs occurred. Keep payment/storage costs and the refund denominator explicit. The margin and net collection floor answer a conditional unit-economics question. Examine heavy users, retries, unused entitlements and refund behavior before setting a price.

Run `python examples/product-casebook/compute.py C10` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "net_collected_cents": 1800,
  "known_variable_cost_cents": 1390,
  "scenario_contribution_cents": 410,
  "scenario_contribution_margin_pct": 22.777778,
  "cost_per_useful_job_cents": 17.375,
  "net_collection_floor_at_unchanged_cost_cents": 2780.0
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Charge per useful job with a clear allowance: aligns with an understandable outcome, but the business absorbs some failed-work cost.
- Charge raw usage: can align cost closely but may make value and budgeting difficult for customers.
- Use a fixed fee plus metered overage: balances predictability and tail usage, but needs precise terms and reliable metering.

### Worked recommendation

Use a transparent useful-job unit with documented failure/credit behavior if research supports it. Instrument the cost and entitlement ledgers separately, model usage distributions and test willingness to pay. Do not quote the computed cost floor as the market price.

**What would change this recommendation:** Different heavy-user costs, refunds, support burden or willingness to pay can change the packaging. A missing material cost should qualify the contribution claim rather than be silently zeroed.

### Engineering and architecture implications

Keep an idempotent entitlement ledger, reserve/finalize/refund semantics and a separate actual-cost ledger. A retry must not accidentally debit a customer twice, even when it creates another provider cost.

Review the [related technical chapter](/docs/system-design/checkout-payments-credit-ledger) for implementation depth.

### Interviewer follow-ups

**F1. Why include failed attempts?**

They consume resources under the supplied cost contract even if they do not produce a customer-charged useful job.

**F2. Is contribution the same as gross margin?**

Not here. The case explicitly defines its selected variable-cost contribution model; accounting measures can classify costs differently.

**F3. Does the floor establish willingness to pay?**

No. It is a conditional cost arithmetic result, not customer research or a demand curve.

**F4. How do unused credits affect the answer?**

They alter realized usage and entitlement obligations, but they cannot be converted into an accounting conclusion without the actual contract and policy.

### Practice task

Remove failed attempts and quantify the cost sensitivity while explaining why real retry costs cannot simply be omitted.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C11. A discount grows sales but reduces contribution

Sales proposes a 20% discount and expects volume to rise from 100 to 180 units. Decide what evidence is needed before approving it.

### Clarify the question

- Is the discount applied to the same product and customer mix?
- Does unit cost stay fixed over the relevant capacity range?
- What cannibalization, renewal and support effects might appear?

### Frame the user and objective

Evaluate a pricing intervention against contribution and customer strategy, rather than treating higher order volume as sufficient success.

### Evidence status and complete fixture inputs

Prices, costs and volume are invented scenario inputs. Demand response is assumed, not estimated from an experiment. Variable cost is fixed per unit and fixed operating costs are outside the comparison.

```json
{
  "price_cents": 10000,
  "variable_cost_cents": 6000,
  "discount_share": 0.2,
  "baseline_units": 100,
  "scenario_units": 180
}
```

### Metric and decision contract

Compare price minus selected variable cost per unit, then multiply by scenario units. The break-even multiplier here preserves baseline total contribution, not company-wide profit or a full fixed-cost break-even target.

### Work the evidence

The discount halves unit contribution in this fixture. The proposed volume increase does not reach the multiplier required to preserve total contribution. Investigate incremental buyers versus buyers who would have purchased anyway, capacity, renewal anchoring and channel eligibility before recommending a scoped evaluation.

Run `python examples/product-casebook/compute.py C11` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "baseline_unit_contribution_cents": 4000,
  "discounted_unit_contribution_cents": 2000.0,
  "baseline_total_contribution_cents": 400000,
  "scenario_total_contribution_cents": 360000.0,
  "required_volume_multiplier": 2.0
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Offer a broad permanent discount: simple messaging, but can subsidize existing demand and change price expectations.
- Test a limited eligible offer: can estimate response with defined exposure and guardrails, while risking leakage between customers.
- Change packaging or a nonprice barrier: may solve affordability or value communication without lowering every unit's contribution.

### Worked recommendation

Do not justify the proposal with volume alone. Explain the contribution scenario and test a clearly scoped pricing hypothesis if the strategic objective remains credible. Preserve a no-discount comparison where a suitable design permits it.

**What would change this recommendation:** A credible larger incremental volume response, lower cost, strategic retention benefit or targeted accessibility goal could justify another decision. Each belongs explicitly in the model.

### Engineering and architecture implications

Version offers and eligibility, show unambiguous checkout terms, record the actual applied price and make billing changes auditable. Separate promotional exposure from realized transaction value.

Review the [related technical chapter](/docs/resume-skills/webhooks-payments-reliable-integrations) for implementation depth.

### Interviewer follow-ups

**F1. What if discounted contribution reaches zero?**

No finite positive volume preserves a positive baseline contribution under this unchanged-cost model.

**F2. Is revenue growth always bad here?**

No. Revenue can serve a strategic objective, but its relationship to contribution and costs must be explicit.

**F3. How would you examine cannibalization?**

Define eligible cohorts and compare incremental purchase behavior, mix, timing and renewal outcomes under an appropriate design.

**F4. Can you claim demand elasticity from two scenario prices?**

No. The proposed response is an assumption, not an identified demand relationship.

### Practice task

Set the discount to the point where selected unit contribution is zero and explain the missing finite remedy.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

## C12. CAC changes when the acquired unit changes

Marketing platforms claim 150 acquisitions, the first-party report has 120 new customers, and 80 activate. Compare acquisition cost definitions and discuss payback.

### Clarify the question

- What is an acquired customer versus an activated customer?
- Are spend, attribution window and identity rules aligned?
- What future retention and contribution evidence exists?

### Frame the user and objective

Assess an acquisition program's ability to bring valuable new customers, using one declared cost and customer definition rather than a favorable platform denominator.

### Evidence status and complete fixture inputs

The fixture declares deduplicated first-party identities and supplied activation labels, but provides no source rows to verify them. Monthly contribution for the static payback illustration is an assumption. No churn, survival curve or future contribution horizon is supplied.

```json
{
  "spend_cents": 60000,
  "platform_claimed_acquisitions": 150,
  "deduplicated_new_customers": 120,
  "activated_new_customers": 80,
  "assumed_monthly_contribution_cents": 500
}
```

### Metric and decision contract

Spend divided by platform claims, deduplicated new customers or activated new customers produces three named ratios. Static payback divides activated-customer CAC by assumed constant monthly contribution. LTV remains unknown.

### Work the evidence

Reconcile duplicate claims, repeat customers, attribution overlap and incomplete activation windows. Do not compare a platform's broad denominator against a business-qualified CAC target. The static payback number omits retention, timing and uncertainty, so it cannot establish the campaign's lifetime return.

Run `python examples/product-casebook/compute.py C12` from the repository root.

**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):

```json
{
  "platform_denominator_cac_cents": 400.0,
  "deduplicated_new_customer_cac_cents": 500.0,
  "activated_customer_cac_cents": 750.0,
  "static_payback_months": 1.5,
  "lifetime_value_cents": null
}
```

The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.

### Compare options

- Optimize the platform ratio: easy to operate but vulnerable to overlap and definition drift.
- Use a first-party qualified acquisition outcome: closer to the intended customer, but requires maturation and identity quality.
- Run an incrementality study: addresses whether spend caused new demand, with design and cost trade-offs.

### Worked recommendation

Publish the definitions side by side, resolve identity and window discrepancies, then assess a qualified cohort with future contribution and retention evidence. Do not fabricate LTV from the supplied month alone.

**What would change this recommendation:** A corrected customer identity contract, a different target acquisition stage or evidence of incremental retained contribution can alter the assessment.

### Engineering and architecture implications

Join campaign exposure and first-party customer identity with explicit consent and attribution rules. Preserve cost sources, cohort maturity and model versions; avoid summing overlapping platform claims as unique customers.

Review the [related technical chapter](/docs/product-analytics/marketing-measurement-data-visualization) for implementation depth.

### Interviewer follow-ups

**F1. Why does qualified CAC exceed blended new-customer CAC?**

The same spend is divided by fewer activated new customers. The two metrics answer different stage-specific questions.

**F2. Is attributed acquisition incremental acquisition?**

No. Attribution allocates credit under a rule; incrementality asks what would have happened without the spend.

**F3. Why is LTV null?**

The fixture does not supply the retention, future contribution and horizon assumptions needed for a defensible estimate.

**F4. Does static payback promise recovery in that time?**

No. It assumes constant contribution, continued activity and compatible timing, which are not verified here.

### Practice task

Explain why changing the acquisition denominator changes CAC without changing a cent of spend.

- [ ] I attempted the prompt before reading the worked recommendation.
- [ ] I can explain a changed assumption and defend a different valid decision.

<!-- END WORKED CASES -->

## Synthesis

A cost floor, a discounted-volume scenario and static payback answer different conditional questions. Keep unavailable LTV unknown. Explain omitted costs, future assumptions and what a customer or market evaluation would need to establish before a real pricing decision.

Continue with [Marketplaces and Operations](/docs/product-casebook/marketplaces-and-operations).
