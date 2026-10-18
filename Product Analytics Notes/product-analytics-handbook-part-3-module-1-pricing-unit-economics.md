# Product and Analytics Placement Handbook — Part 3
# P1: Pricing and Unit Economics

**P1 · 3–4 hours plus practice · Tier 1 for AI-product and product interviews · Requires: P0; basic ratios**

---

## Why this module matters

“The generation costs five cents” sounds precise, but the interviewer can immediately ask: one API call or a completed post? Does it include images? Retries? Failed attempts? Infrastructure? Is five cents your cost or the customer price? Was the provider bill paid with promotional credits?

A useful answer defines the unit, records the costs that belong to it, explains what the customer buys, and states what remains after serving that customer.

> **Trace three connected quantities separately: what the customer receives, what you charge, and what it costs to deliver.**

This chapter teaches pricing models, usage normalization, credits, margins, failure economics and a defensible Zyke explanation. It does not choose a real commercial price for your project.

**Verification:** **88 local checks passed** on Python 3.13.15. The executable example uses invented USD rates and a five-job cohort. It checks normalization, duplicate evidence, missing usage, margins, price floors, break-even arithmetic and simple credit-pack allocation. No AI provider, payment gateway, durable ledger or accounting system was called.

## 1.1 Price, cost, value and willingness to pay

| Term | Meaning | Teaching example |
| --- | --- | --- |
| Customer value | Benefit from accomplishing the task | A usable branded post without assembling text and images manually |
| Willingness to pay | What a customer would exchange for that benefit under available alternatives | Something to investigate with the target segment |
| Price | What the seller asks under a specified contract | USD 0.20 for a completed teaching action |
| Provider cost | Amount attributable to upstream provider work | Text and image calls, including chargeable failed attempts |
| Cost to serve | Relevant delivery and support costs under a stated boundary | Provider charges, hosting and other included costs |
| Unit economics | Revenue and cost reasoning around a defined unit | Contribution per completed customer action |

Cost matters because a product must fund delivery. Cost alone does not establish what customers value or will pay. A technically cheap output can be worthless; a useful workflow may create value beyond the token bill.

### Three approaches to setting an initial price

| Approach | Starting point | What it can miss |
| --- | --- | --- |
| Cost-informed | Estimate cost and a required buffer | Demand, alternatives and perceived value |
| Competitor-informed | Compare substitutes and their terms | Differences in segment, quality, limits and cost structure |
| Value-informed | Investigate the outcome and customer benefit | Weak evidence or optimistic estimates of willingness to pay |

A practical product decision combines these perspectives, then tests the offer with an appropriate audience. The arithmetic below supplies constraints and scenarios; it does not prove demand.

## 1.2 Define the unit before calculating

An AI application can contain several units at once:

```text
one customer action: "Create a complete post"
  |
  +-- text generation attempt
  |     +-- retry or fallback attempt
  |
  +-- image generation attempt
  |
  +-- validation/rendering/storage
  |
  +-- usable final result, or a failed customer action
```

An attempt is not a completed action. A successful text call can belong to an action that fails during image generation. A retried attempt can incur a new provider charge even when the product charges the customer once.

### State the denominator and boundary

| Claim | Questions that make it meaningful |
| --- | --- |
| Cost per API attempt | Which provider, model, configuration and usage categories? |
| Cost per successful generation | What constitutes success? Which unsuccessful work is included? |
| Cost per customer | Which period, active customers, support and infrastructure? |
| Gross margin | Which revenue and cost-of-sales classifications? |
| Contribution per action | Which variable costs are deducted? |
| Lifetime value | Which contribution stream, retention and acquisition cohort? |

For this chapter, the primary unit is **one completed text-and-image customer action**. The fixed cohort contains five final jobs, three successful and two failed. It is invented teaching data, not a Zyke usage sample.

We calculate total provider cost for the cohort divided by its successful actions. This definition deliberately includes the cost of failed jobs from the same cohort.

## 1.3 Pricing models and their trade-offs

| Model | Customer pays for | Useful property | Main risk |
| --- | --- | --- | --- |
| Flat subscription | Access or an entitlement for a period | Predictable customer bill | Heavy usage can outrun revenue |
| Per seat | A user seat or named role | Aligns with team access | Seats may poorly reflect expensive usage |
| Pay as you go | Measured units or actions | Usage and charges move together | Surprise bills and uncertain spend |
| Prepaid credits | A balance later consumed under a rate policy | Budget visibility and earlier cash collection | Opaque conversion, expiry and refund disputes |
| Subscription plus allowance/overage | Base entitlement plus excess usage | Combines access and usage | More rules and a harder-to-explain bill |
| Tiered offer | A bundle of capabilities or quantities | Segment-specific packaging | Thresholds and feature gates can confuse buyers |

Stripe documents several pricing models, including usage-based approaches. The exact billing mechanism should follow a clear customer contract. [Stripe pricing models](https://docs.stripe.com/products-prices/pricing-models).

### Graduated versus volume pricing

Under graduated pricing, different portions of usage can have different rates. Under volume pricing, reaching a tier can apply that tier's rate to the relevant entire quantity. Always specify which rule applies before doing arithmetic.

A product may call both “tiered.” Ask what happens at the threshold, whether a base fee exists, and what the customer sees before consumption. Do not infer the rule from a plan name.

### An AI-product offer needs limits

If “unlimited” includes variable-cost model calls, define the actual fair-use or capacity policy. Provider rate limits do not by themselves protect the product's budget. Consider per-action limits, bounded output, explicit premium options and spend alerts.

Rejecting or queuing expensive work changes the user experience. Make the trade-off visible rather than silently switching every request to a lower-quality model.

## 1.4 Credits: a product unit, not free money

Credits translate product consumption into a balance the customer can understand. They may be denominated in money-like amounts or abstract units, but the conversion policy must be explicit.

### A simple single-pack example

The fixture assumes a pack with 1,000 credits. One completed action consumes 20 credits.

| Pack | Cash associated with this teaching pack | Service value allocated to 20 credits |
| --- | ---: | ---: |
| Standard | USD 10 | USD 0.200000 |
| Discounted | USD 8 | USD 0.160000 |
| Promotional | USD 0 | USD 0.000000 |

The program computes `credits consumed × pack price / pack credits`. It is a simple single-pack allocation, not a general revenue-recognition calculation. Mixed grants, refunds, taxes, breakage and allocation across several obligations need additional policy and records.

**The same 20-credit list charge can imply different paid value.** A dashboard that values every promotional credit at the standard pack rate can overstate commercial performance.

Stripe's billing-credit documentation distinguishes paid and promotional grants and their application to eligible billing items. An internal application wallet is a separate design: Stripe's invoice credits do not automatically implement request-time authorization and atomic product debits. [Stripe billing credits](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits).

### Questions a credit policy must answer

- What does one credit buy, and can different models consume different amounts?
- Is the charge known before starting, or estimated and later settled?
- Which grant is consumed first when paid and promotional balances coexist?
- What happens on partial success, cancellation or an uncertain provider outcome?
- Can grants expire, and how are those terms communicated?
- How are payment reversals and product refunds reflected without rewriting history?

These are product rules with engineering consequences. Do not invent a historical Zyke policy just because the proposed policy seems sensible.

## 1.5 Provider metering: normalize units without losing detail

A normalized report should preserve each provider's original usage while making totals comparable in a chosen reporting currency.

```text
provider/model + pricing version + usage category + quantity
                         |
                         v
matching unit rate and denominator
                         |
                         v
line cost -> attempt cost -> customer-action cost -> cohort report
```

Input tokens, output tokens, cache writes/reads, images, audio time, tool calls and storage can have different units and tariffs. Some categories may already include another quantity; do not add overlapping counters blindly.

Current Claude pricing documentation separates categories such as input, output and caching. Gemini pricing also distinguishes models, modalities and usage categories. Those pages explain why a single universal “cost per token” is inadequate. **No live provider price from either page is embedded in the fixture.** [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing).

### Minimum useful cost record

| Field | Why keep it? |
| --- | --- |
| Customer-action/job ID | Join all work belonging to the product outcome |
| Provider-attempt ID | Distinguish a retry from repeated reporting |
| Provider and exact model | Select the applicable product/configuration |
| Pricing version/effective rule | Reproduce historical estimates |
| Unit and quantity | Apply the correct denominator |
| Currency | Avoid silently summing unlike amounts |
| Usage completeness | Preserve missing evidence |
| Product and attempt outcomes | Keep partial and failed work visible |
| Provider request/invoice reference | Support later reconciliation |

The teaching model uses USD only and rejects another currency. A real implementation needs an explicit FX policy, rate/time reference, conversion fees and a consistent reporting boundary.

### Invented teaching rates

| Provider/model | Category | Price | Per |
| --- | --- | ---: | ---: |
| text-demo / text-small | Input tokens | USD 2 | 1,000,000 tokens |
| text-demo / text-small | Output tokens | USD 8 | 1,000,000 tokens |
| image-demo / image-basic | Images | USD 0.04 | 1 image |

All three rows use pricing version `teaching-v1`. They are invented rates, not quotes for any real service and not the seven historical Zyke integrations.

For a text attempt with 1,000 input tokens and 500 output tokens:

```text
input  = 1000 × 2 / 1000000 = USD 0.002
output =  500 × 8 / 1000000 = USD 0.004
total  = USD 0.006
```

One image adds USD 0.04, giving USD 0.046 for the simplest completed teaching action.

## 1.6 Retries, failed work and uncertain outcomes

### Three different situations

| Situation | Provider-cost question | Customer-charge question |
| --- | --- | --- |
| Known rejected request with explicit zero usage | Is there reliable evidence of no chargeable work? | What does the product contract promise? |
| Failed/partial attempt with reported usage | Include the known cost even if the final action failed | Refund/charge under the chosen policy |
| Timeout without complete usage | Cost is unresolved; reconcile it | Preserve uncertainty and avoid uncontrolled repeated effects |

“The UI displayed an error” does not establish that the provider did no work. A retry may fix the customer experience while adding cost.

### An idealized retry formula

If every attempt costs the same amount `c`, attempts are independent with success probability `s`, and retrying continues until success without a cap:

```text
expected attempts per success = 1 / s
expected cost per success     = c / s
```

The verified example uses `c = USD 0.04`. At success probability 0.8, expected cost is **USD 0.050000**; at 0.5 it is **USD 0.080000**.

Those are mathematical scenario results. Real retries are capped, failures can be correlated, fallback models can have different prices, and partial work can change the next attempt's cost. Use observed attempt records for the actual cohort calculation.

### Duplicate report versus a real second attempt

Repeated reporting of the same attempt should not increase cost. A new provider attempt can add cost even if it serves the same customer action.

The fixture ignores an identical repeated record for a04, but rejects a conflicting record with the same attempt ID. Reconciliation is supplied as an explicit replacement of a10's unknown usage before reaggregation; the helper does not implement an append-only revision log.

## 1.7 The executable five-job cohort

Run from the repository root with Python 3.13:

```powershell
python -X utf8 examples/product-analytics/module-1-pricing-unit-economics/economics.py
python -X utf8 examples/product-analytics/module-1-pricing-unit-economics/verify.py
```

The example contains ten distinct provider attempts plus one duplicate report.

| Job | Product outcome | Work | Provider cost after synthetic reconciliation |
| --- | --- | --- | ---: |
| g1 | Success | Text + one image | USD 0.046000 |
| g2 | Success | Failed text attempt + text retry + one image | USD 0.047800 |
| g3 | Failed | Text succeeded; image attempt failed but incurred cost | USD 0.046000 |
| g4 | Success | Larger text + two images | USD 0.092000 |
| g5 | Failed | Timeout with initially missing usage | USD 0.002000 |

### Before reconciliation

The known subtotal is **USD 0.231800**. Usage for a10 is unknown, so the program returns `null` for total cost and cost per success.

```json
{
  "jobs": 5,
  "successful_jobs": 3,
  "unique_attempts": 10,
  "duplicate_reports_ignored": 1,
  "known_cost_usd": "0.231800",
  "total_cost_usd": null,
  "cost_per_success_usd": null,
  "unknown_attempts": ["a10"]
}
```

This is an exact projection of the preserved output. A known subtotal can be described as a lower bound on this fixture's nonnegative list-price usage cost. It is not necessarily a lower bound on a real invoice with credits, adjustments or discounts.

### After synthetic reconciliation

The fixture supplies a10 with 1,000 input tokens and no output tokens, adding USD 0.002. It does not contact a provider or retrieve an actual invoice.

```json
{
  "jobs": 5,
  "successful_jobs": 3,
  "unique_attempts": 10,
  "duplicate_reports_ignored": 1,
  "known_cost_usd": "0.233800",
  "total_cost_usd": "0.233800",
  "cost_per_success_usd": "0.077933",
  "unknown_attempts": []
}
```

The total divides by **three successful customer actions**, not ten attempts or five jobs. Failed jobs g3 and g5 remain in the numerator.

### Why not average only the successful rows?

That would omit the cost of g3 and g5. It answers a different question: provider cost attached directly to successful jobs. It can be a useful diagnostic if labelled, but it understates this cohort's cost per delivered successful action.

The provider totals are **image-demo USD 0.200000** and **text-demo USD 0.033800**. Keeping both the provider and customer-action views helps reconcile the same underlying work from different directions.

## 1.8 Gross profit, gross margin and markup

```text
gross profit = net revenue - COGS
gross margin = gross profit / net revenue
markup       = (price - cost) / cost
```

COGS means cost of goods sold, also referred to here as cost of sales. Gross margin uses revenue as its denominator; markup uses cost.

If cost is USD 0.10 and price is USD 0.20, the markup is 100%, while gross margin is **50%**. Doubling cost is not the same as achieving a 100% margin.

An income statement deducts cost of sales before gross profit and then other operating expenses before operating profit. Gross profit therefore does not establish net profit. Classify costs consistently with the reporting policy rather than treating every expense as interchangeable. [SEC: financial-statement basics](https://www.sec.gov/about/reports-publications/beginners-guide-financial-statements).

### The cohort's explicit accounting simplification

For teaching only, assume each successful action contributes USD 0.20 of net service revenue. There are no sales taxes, refunds, subscription allocations or recognition timing differences in this scenario.

Add USD 0.015 of variable infrastructure to provider cost and classify both as COGS. Treat USD 0.05 of allocated payment fees as another variable expense outside COGS. **That fee classification is the fixture's explicit convention, not a universal accounting rule.**

```json
{
  "revenue_usd": "0.600000",
  "cogs_usd": "0.248800",
  "gross_profit_usd": "0.351200",
  "gross_margin_pct": "58.533333",
  "other_variable_usd": "0.050000",
  "contribution_usd": "0.301200",
  "contribution_margin_pct": "50.200000",
  "scenario_after_fixed_usd": "0.301200"
}
```

These are actual calculator results under invented inputs. No fixed costs are deducted in this small cohort output, so its final scenario amount equals contribution. It is not the product's operating or net profit.

### Use the ratio of totals

To aggregate gross margin, add revenue and COGS and calculate the ratio from those totals. Do not take an unweighted average of percentages from differently sized customers.

The verifier checks a separate example with total revenue USD 10.10 and total COGS USD 2.08; its gross margin is **79.405941%**. A small low-margin customer and a large high-margin customer should not receive equal weight in the aggregate ratio.

Zero revenue produces an undefined margin percentage, represented as `null`. Negative gross profit remains negative; the program does not hide a loss by clamping it to zero.

## 1.9 Contribution margin and fixed costs

Contribution is what remains after the specified variable costs and can contribute toward fixed costs. COGS classification and variable/fixed behavior are separate dimensions.

In the cohort fixture, all COGS is assumed variable, and payment fees are an additional variable expense. Thus:

```text
contribution = revenue - variable delivery COGS - other variable expense
```

If some COGS were fixed, simply subtracting all COGS would not produce the same conventional variable-cost contribution measure. State the cost boundary before comparing reports.

| Cost example | Possible behavior | Question to ask |
| --- | --- | --- |
| Provider tokens/images | Usually driven by usage | Are retries, discounts and minimum commitments included? |
| Hosting | Fixed, variable or stepwise | Which capacity band and allocation method? |
| Payment fee | Often a transaction component and/or percentage | Is it charged per top-up or per action? |
| Support | Fixed staffing plus workload effects | Which service level and customer segment? |
| Engineering | A period expense or another approved classification | Which reporting definition are we using? |

Contribution is not automatically profit, and gross margin is not automatically contribution margin. A comparison is useful only when the definitions are compatible.

## 1.10 Price floors and break-even

### A margin constraint is not a demand forecast

For a chosen gross-margin target `m` and unit COGS `c`:

```text
(price - c) / price = m
price = c / (1 - m)
```

The separate price-floor example uses `c = USD 0.06` and `m = 0.60`:

```json
{
  "unrounded_usd": "0.15",
  "cent_price_usd": "0.15"
}
```

If cost is USD 0.061 with the same target, the required cent-denominated floor rounds upward to **USD 0.16**. Rounding a floor downward could violate the target. The model rejects a target of one or above.

This target concerns the specified COGS only. Payment fees, acquisition cost, operating expenses and commercial willingness to pay are separate considerations. A mathematically sufficient margin price can still be an unsuccessful offer.

### A separate linear break-even scenario

Assume price USD 0.20, variable cost USD 0.07, and fixed costs USD 1,000 for a defined period. Contribution per action is USD 0.13.

```text
break-even actions = ceil(fixed costs / contribution per action)
                   = 7,693
```

At 7,692 actions, contribution totals USD 999.96; at 7,693 it totals USD 1,000.09. Both boundary values are checked.

This is a different, explicitly stated scenario from the five-job cohort. It assumes stable price, variable cost and capacity. A step increase in infrastructure or support can change the answer. With zero or negative unit contribution, the helper returns `null` rather than claiming a finite volume can cover positive fixed costs. [Stripe: break-even reasoning](https://stripe.com/resources/more/how-to-calculate-the-break-even-point).

## 1.11 Credits, cash and revenue are different records

```text
customer payment ----------> cash/processor record
       |
       +-------------------> paid entitlement / credit grant
                                  |
                                  v
                              consumption
                                  |
                                  v
                         service/revenue allocation

provider usage ------------> provider-cost record and reconciliation
```

A payment arriving and a credit being consumed can occur in different periods. A promotional grant may create product access without customer cash. A provider's promotional grant can reduce immediate cash paid while the product still consumes a resource that will eventually need funding.

Keep at least these views distinct:

| View | Useful question |
| --- | --- |
| List-price resource usage | What would this workload cost under the stated tariff? |
| Provider invoice/cash cost | What adjustments, discounts and credits actually applied? |
| Customer consumption | Which product units and grants were used? |
| Customer payments/refunds | What money moved and when? |
| Service revenue allocation | What revenue belongs to the period or delivered service under the adopted policy? |

Prepayment improves the timing of cash collection; it does not by itself prove demand retention or profitable service delivery. The fixture allocates one pack arithmetically and does not implement formal revenue accounting, tax, expiration or refund rules.

## 1.12 From a product rule to a credit-control architecture

The economic model is offline. A real product must enforce its charging policy under concurrency, retries and failures.

```text
request intent + operation ID
        |
        v
authorize product access and available entitlement
        |
        v
reserve an allowed amount under a chosen contract
        |
        v
bounded provider attempts -> record usage and uncertain outcomes
        |
        v
settle customer charge / release unused entitlement / reconcile
```

This is a proposed design, not a statement that Zyke implemented reservation states. The historical resume reports atomic debits; it does not establish their exact transaction mechanism.

### Important contracts

- A retry with the same product operation identity must not create an unintended second customer charge.
- A real new provider attempt can still create an additional upstream cost.
- Two requests must not independently spend the same available entitlement.
- Unknown usage must stay visible until reconciled or handled under an explicit approved rule.
- Refunds and adjustments need traceable effects and cannot erase the fact that provider work occurred.
- Reservations need bounded lifetime and recovery, but expiry cannot simply assume the provider did nothing.

Do not perform the external network call inside a long database lock just to make a diagram look atomic. Durable operation states and reconciliation bridge the database/provider boundary.

The earlier [M9 payment/webhook chapter](/docs/resume-skills/webhooks-payments-reliable-integrations) and [S8 checkout and credit-ledger design](/docs/system-design/checkout-payments-credit-ledger) provide implementation depth. This chapter explains why those choices affect the product's economics.

### Payment confirmation is its own boundary

Razorpay documents raw-body signature validation and duplicate-event handling. A valid signature is not, by itself, a deduplicated credit effect. Verify the appropriate payment/order state and apply the business effect using durable identity and a suitable transaction. [Razorpay webhook validation](https://razorpay.com/docs/webhooks/validate-test/).

This chapter calls no gateway. It does not claim to reverify the historical integration or infer customer revenue from configured endpoints.

## 1.13 Reconciliation and the pricing dashboard

A useful internal dashboard should answer more than “how many credits remain?”

| Question | Useful breakdown |
| --- | --- |
| Where is cost concentrated? | Provider, model, usage category and pricing version |
| Which actions are expensive? | Action type, successful/failed outcome and attempt count |
| Which cost is unresolved? | Missing usage, provider reference and age |
| What did customers pay? | Paid versus promotional consumption, discounts and refunds |
| Is the offer sustainable? | Defined revenue, cost boundary, contribution and tail behavior |
| What changed? | Tariff, model mix, product rule and measurement revisions |

### A practical reconciliation sequence

1. Select a closed reporting population and observation window.
2. Preserve original provider usage and stable request identities.
3. Apply the tariff effective for that work, keeping estimates distinct from finalized charges.
4. Deduplicate reporting without deleting genuine new attempts.
5. List missing or conflicting evidence rather than substituting zero.
6. Compare provider totals with the relevant billing records and document adjustments.
7. Join product outcomes and customer charging/refund rules.
8. Publish the definition, completeness state and revision/version with the result.

In the fixture, step 6 is simulated by a supplied usage replacement. No invoice import, automated accounting close or provider settlement took place.

### Means can hide an expensive tail

The average does not bound the cost of a long prompt, many images or repeated failures. Investigate cost distributions and expensive action paths, then choose output limits, routing and spend controls that preserve acceptable quality.

A lower-cost provider is not automatically a better product decision. Compare quality-adjusted completion, latency, failures, support burden and switching effort. Preserve enough evidence to evaluate a routing change instead of assuming the lowest listed rate wins.

## 1.14 Explain Zyke without inventing business results

The earlier [M28 resume deep-dive](/docs/resume-skills/resume-project-experience-deep-dives) records these as **resume-reported**: an AI social-content MVP, usage normalization across seven providers, a USD balance/credit path and Razorpay integration. The product resume additionally reports USD 0.05 per generation and a four-minute content cycle.

Those statements establish what was reported, not the missing measurement details. The same earlier review notes a public profile describing a credits-funded project without cash collection. Reconcile the project snapshot and payment mode before presenting a business result.

### Evidence needed for “USD 0.05 per generation”

| Dimension | Clarification to prepare |
| --- | --- |
| Unit | Text attempt, completed post, image or full workflow? |
| Population | Which real jobs, sample size, dates and product version? |
| Provider configuration | Which models, image settings and routing? |
| Failure policy | Were failed jobs, retries and partial outcomes included? |
| Cost basis | List-price estimate, invoiced amount or cash after promotional credits? |
| Other costs | Were infrastructure, fees and support included or excluded? |
| Distribution | Mean, median, range or another summary? |
| Customer economics | Was this cost, price, revenue allocation or margin? |

The teaching result **USD 0.077933** is not a correction to the resume's USD 0.05 figure. It comes from a separate invented cohort with a different defined numerator and denominator.

### Thirty-second answer skeleton

“The product creates [defined output] for [user]. I normalized [actual usage categories] using [recorded tariff/version rules]. The reported cost figure referred to [unit and sample] and included [costs] while excluding [costs]. Customer credits followed [actual policy]. We verified [actual correctness evidence]. Payment integration readiness and actual cash/revenue are separate, so I would substantiate each from its own records.”

If those records are unavailable, say which definitions need confirmation. Do not replace missing facts with this chapter's synthetic prices or proposed reservation architecture.

## 1.15 Common wrong answers

| Wrong answer | Better reasoning |
| --- | --- |
| “Low token prices make the product profitable.” | Include all work, relevant delivery costs, pricing and actual demand |
| “A generation is one API call.” | Define the customer action and distinguish its attempts |
| “A failed job costs zero.” | Failed or partial work can have known chargeable usage |
| “Missing usage means zero usage.” | Preserve an unresolved state and reconcile |
| “Retries are duplicates.” | A repeated report differs from a genuine new provider attempt |
| “Every token has the same rate.” | Match model, pricing version, category and denominator |
| “A 100% markup means 100% margin.” | Markup divides by cost; margin divides by revenue |
| “Gross margin is the remaining cash.” | Cash timing and other expenses are separate |
| “All credits are worth the list price.” | Paid, discounted and promotional grants can differ |
| “Payment success means revenue and credits are correct.” | Verify each financial, entitlement and business effect |
| “Average provider cost is our complete cost to serve.” | State inclusions and examine other costs and tails |
| “The formula gives the right market price.” | It supplies a scenario constraint, not willingness to pay |

## 1.16 Must remember

- Define the unit and reporting cohort before dividing costs.
- Record provider, model, unit, quantity, currency and tariff version.
- Customer success and provider-attempt success are different states.
- Preserve unknown costs; do not hide them with a zero default.
- Keep provider cost, entitlement consumption, cash and revenue separate.
- Gross margin and markup use different denominators.
- Contribution depends on a declared variable-cost boundary.
- Price floors and break-even results are conditional on their assumptions.
- Paid and promotional credits require clear treatment.
- A resume result needs original evidence, not a plausible teaching calculation.

## 1.17 Interview questions and answers

### Q1. What are unit economics?

Revenue and cost reasoning around a defined unit, such as a completed customer action or an active customer over a period. State the unit and included costs before giving a margin.

**Follow-up:** Why define the unit first? One action can require several attempts and still fail.

### Q2. How would you price an AI product?

Understand the customer outcome and alternatives, estimate cost distributions, compare simple offers and investigate willingness to pay. Use cost constraints without assuming cost determines value.

**Follow-up:** What would you launch first? A clear constrained offer that tests the key value assumption.

### Q3. Subscription versus usage-based pricing?

Subscription gives a predictable entitlement or bill; usage pricing ties charges to measured consumption. Their attractiveness depends on customer budgeting and how variable delivery cost behaves.

**Follow-up:** Can they be combined? Yes, with a clear allowance and overage contract.

### Q4. Why use credits?

They can make a multi-unit product easier to budget and package. The conversion, model-specific consumption, grant order and failure policy must remain understandable.

**Follow-up:** What is the risk? Credits can obscure real price or create confusing expiration/refund expectations.

### Q5. Are paid and promotional credits equivalent?

They may grant product access under similar consumption rules, but they do not imply the same customer cash or paid service value. The fixture allocates zero paid-pack value to promotional credits.

**Follow-up:** Does promotional usage cost nothing? Provider and delivery resources can still be consumed.

### Q6. How do you normalize several provider schemes?

Preserve the original usage, match each category to its versioned tariff and denominator, then aggregate in a consistent currency. Keep provider-attempt and customer-action identities.

**Follow-up:** What if currency differs? Apply an explicit documented FX process; this fixture rejects it.

### Q7. Why version pricing?

A historical job must remain reproducible when current rates or model names change. Preserve the effective rule rather than recalculating all past costs with today's tariff.

**Follow-up:** What about corrected invoices? Keep a traceable revision or adjustment rather than silently erasing the earlier estimate.

### Q8. How do input and output tokens differ economically?

They can have separate rates, and additional categories such as cache activity can have their own semantics. Use documented non-overlapping usage categories for the selected provider/model.

**Follow-up:** Can you count characters instead? That is not authoritative provider token usage.

### Q9. What is cost per successful generation?

Under this chapter's definition, all attributable provider cost in the closed cohort divided by completed customer actions. The reconciled fixture gives USD 0.077933.

**Follow-up:** Why include failed jobs? Their cost was incurred while trying to deliver those cohort outcomes.

### Q10. Does an error mean no cost?

No. Partial output, failed downstream work or a lost response can coexist with provider usage. Record what is known and keep unknown usage unresolved.

**Follow-up:** How does the fixture show it? Failed g3 has USD 0.046000 provider cost.

### Q11. How should missing usage appear in a report?

As missing evidence with affected attempts identified. Before a10 is reconciled, this fixture shows a known subtotal but no final total or cost-per-success figure.

**Follow-up:** Can you estimate it? Yes, if estimates are explicitly separate from finalized usage.

### Q12. How do retries change economics?

They may improve completion while increasing attempts and cost. Under the idealized equal-cost independent model, cost per success is attempt cost divided by success probability.

**Follow-up:** Why not use that formula everywhere? Real failures, caps and fallback prices violate its assumptions.

### Q13. How do you avoid double-counting provider costs?

Deduplicate repeated reports using provider-attempt identity, without dropping genuinely new attempts. Conflicting records need explicit reconciliation.

**Follow-up:** Does one customer operation ID suffice? It groups the action but cannot identify every distinct upstream attempt.

### Q14. Gross margin versus markup?

Margin divides profit by revenue; markup divides the price-cost difference by cost. USD 0.10 cost and USD 0.20 price imply 50% gross margin and 100% markup.

**Follow-up:** Which denominator is used in a target-margin floor? Price/revenue.

### Q15. Gross margin versus contribution margin?

Gross margin follows the chosen cost-of-sales classification; contribution concerns the specified variable costs. They can differ because classification and cost behavior are different questions.

**Follow-up:** Where do payment fees belong? State the actual reporting convention; the fixture places them outside COGS but inside variable costs.

### Q16. Does positive contribution prove profitability?

No. Fixed costs and other period expenses can still exceed total contribution. Inspect the complete defined reporting boundary.

**Follow-up:** Can growth help? Only under the relevant price, cost, demand and capacity assumptions.

### Q17. How do you compute a target-margin price?

For unit cost c and margin fraction m, price is c divided by one minus m. The USD 0.06/60% example gives USD 0.15 before other cost considerations.

**Follow-up:** Does that prove customers will pay? No; it is a conditional floor calculation.

### Q18. How do you calculate break-even volume?

Divide fixed costs by positive unit contribution, then round up to a whole unit under the linear scenario. The checked example requires 7,693 successful actions.

**Follow-up:** What if contribution is negative? More of the same unit does not cover positive fixed costs.

### Q19. How should you aggregate margins across customers?

Use total revenue and total relevant costs, then calculate the ratio. An unweighted mean of percentages overweights small customers.

**Follow-up:** What if revenue is zero? Margin percentage is undefined, not automatically zero.

### Q20. Why use Decimal arithmetic?

It expresses decimal inputs and rounding policy explicitly, avoiding binary-float representation artifacts. Precision, allowed ranges and when to round still need definition.

**Follow-up:** Why not round every token line to cents? Small costs can disappear or compound incorrectly before aggregation.

### Q21. Is collecting a credit top-up the same as earning revenue?

Cash collection, entitlement and service/revenue allocation can occur at different times. Keep them separate under the adopted reporting policy.

**Follow-up:** Does the single-pack helper implement that policy? No; it is only an arithmetic allocation example.

### Q22. How should a failed action affect customer credits?

Follow a clear contract about failure, partial delivery and uncertainty. Customer refunds do not erase incurred provider cost.

**Follow-up:** Can automatic refunds be abused? The implementation and product policy must consider retries, repeated effects and access controls.

### Q23. What is a reserve-settle-release flow?

It temporarily encumbers entitlement before work, later applies the allowed charge and releases unused capacity. Its recovery and timeout rules must respect uncertain provider outcomes.

**Follow-up:** Was that proven to be Zyke's design? No; the resume reports atomic debits, not the precise reservation mechanism.

### Q24. Does a valid payment webhook guarantee correct credits?

It supplies evidence about an authenticated event, but the handler still needs correct state validation, durable deduplication and a suitable atomic business effect.

**Follow-up:** What should be checked? The relevant identity, payment/order state, amount, currency and permitted transition.

### Q25. What would you show on a cost dashboard?

Provider/model/category totals, attempts per outcome, failed-job cost, missing usage, paid/promotional consumption and clearly defined margin measures.

**Follow-up:** Why show unresolved usage age? Old missing evidence can make recent margins look falsely healthy.

### Q26. Is the cheapest provider the best choice?

Compare usable completion, latency, quality, reliability and support cost alongside unit rates. A cheaper attempt can require more retries or produce less useful output.

**Follow-up:** How would you evaluate a switch? Use a relevant workload and quality criteria with cost and failure evidence.

### Q27. Why examine tail costs?

An average can hide a minority of very expensive jobs or customers. Limits and routing should address the actual cost/quality distribution.

**Follow-up:** Does a provider rate limit protect margin? It limits some throughput, not necessarily cost per action or customer spend.

### Q28. How would you substantiate Zyke's USD 0.05 claim?

Identify the original unit, sample, provider configuration, included failures and cost basis, then reconcile the records. Keep cost distinct from customer price and profit.

**Follow-up:** Does this chapter reproduce it? No; USD 0.077933 is from a separate invented cohort.

### Q29. Does a payment-ready MVP prove business traction?

No. Distinguish integrated capability, test/live mode, actual transactions, paying customers and retention. Confirm the historical project snapshot using original evidence.

**Follow-up:** What can you claim without revenue? Your real shipped contribution and its verified behavior.

### Q30. What did the local checks establish?

Eighty-eight checks verified the stated offline arithmetic and evidence-handling cases. They did not run real providers, charge customers, reconcile invoices or verify historical business results.

**Follow-up:** What would make the model production-ready? Real usage adapters, durable state, authoritative billing reconciliation and approved policies, plus tests for those boundaries.

## 1.18 A 30-minute mock

**Prompt:** “An AI content tool sells credits. Customers complain about failed generations, and the team claims every post costs five cents. Propose a pricing and measurement review.”

| Minutes | Task | Useful result |
| --- | --- | --- |
| 0–4 | Define user, output, price contract and current claim | One action, its success condition and disputed cost boundary |
| 4–9 | Draw usage and money flows | Attempts, credits, provider cost, cash and service allocation separated |
| 9–15 | Inspect a small cohort | Retries, partial failures, missing usage and duplicate reports visible |
| 15–21 | Compare offers and constraints | Simple credit/usage policy, budget protections and alternatives |
| 21–26 | Compute economics | Explicit revenue/COGS/variable costs and scenario assumptions |
| 26–30 | Define verification and next decision | Reconciliation owner, customer failure policy and evidence needed |

### Answer skeleton

“I would define a completed post and trace all provider attempts belonging to it. I would separate known costs from missing usage and avoid counting a timeout as zero. Next I would join the customer charging and refund policy, paid versus promotional consumption, and the actual cost boundary. I would compare simple offers using contribution and demand evidence, with spend controls and understandable failure behavior. The five-cent claim needs its original sample and definition before we use it to set a commercial price.”

The mock is manual. The calculator verifies arithmetic, not your interview performance or willingness-to-pay research.

## 1.19 Practice tasks and answer checkpoints

1. **Define the unit.** Rewrite “generation costs USD 0.05” as a complete measurement statement with unknown fields explicitly marked.
2. **Predict the text cost.** Compute 1,000 input and 500 output tokens using the invented tariffs before running the program.
3. **Trace a partial failure.** Explain why g3 has cost despite no completed customer output.
4. **Find the missing denominator.** Compare attempts, jobs and successful customer actions as possible divisors; explain the question each answers.
5. **Repair uncertainty.** Inspect a10 before and after the supplied reconciliation. Explain why replacing unknown with zero is misleading.
6. **Detect duplicate evidence.** Change the repeated a04 record's quantity in a copy of case.json and explain why aggregation rejects it.
7. **Compare margin and markup.** Use USD 0.10 cost and USD 0.20 price and identify both denominators.
8. **Review a credit promotion.** Compare the standard and discounted 1,000-credit packs for a 20-credit action. State what remains unmodelled.
9. **Check a price floor.** Use USD 0.061 unit COGS and a 60% gross-margin target; explain upward cent rounding.
10. **Defend break-even.** Explain the 7,692/7,693 boundary and identify two assumptions that can invalidate the linear scenario.
11. **Design a failure policy.** Specify product treatment of known zero usage, partial delivery and unresolved provider outcomes. Trace its entitlement and cost effects.
12. **Prepare a real Zyke story.** Bring original usage or code evidence where available, separate contribution from commercial results, and list unresolved definitions.

### Answer checkpoints

- **1:** specify unit, cohort, dates, provider configuration, cost basis, inclusions and summary statistic.
- **2:** USD 0.006 before image work.
- **3/4:** failed product outcomes do not delete provider costs; cost per successful action uses all relevant cohort cost over three successes.
- **5:** the known subtotal is USD 0.231800, but total and unit cost remain unresolved until the fixture supplies the missing usage.
- **6:** a repeated identity with different content is a reconciliation conflict, not another safe deduplication.
- **7:** markup 100%; gross margin 50%.
- **8:** USD 0.20 versus USD 0.16 in this single-pack allocation; mixed grants and recognition policy remain outside it.
- **9:** USD 0.16 at cent precision for the stated floor.
- **10:** USD 999.96 versus USD 1,000.09 contribution; check capacity, cost and demand assumptions.
- **11/12:** preserve real uncertainty and original evidence rather than substituting a convenient invented policy.

## 1.20 Exit checklist

- [ ] I can distinguish customer value, price, provider cost and cost to serve.
- [ ] I can define the unit, population, time window and cost boundary.
- [ ] I can compare subscription, usage and credit pricing.
- [ ] I can explain paid, discounted and promotional credits.
- [ ] I can normalize versioned provider units without mixing currencies.
- [ ] I can distinguish attempts, reports and completed customer actions.
- [ ] I can preserve unknown costs and explain partial-failure economics.
- [ ] I can compute gross margin, markup and contribution with the correct denominators.
- [ ] I can state a cost-classification convention and avoid double deductions.
- [ ] I can explain price-floor and break-even assumptions.
- [ ] I can distinguish cash, entitlement consumption and service/revenue allocation.
- [ ] I can connect the charging policy to concurrency, idempotency and reconciliation.
- [ ] I can explain what the 88 local checks establish and what remains unverified.
- [ ] I can defend a genuine resume claim without adopting the synthetic rates as project facts.

## 1.21 Sources, reproducibility and next

Primary sources checked on **18 October 2026** appear beside the relevant concepts. Provider rates and product billing features can change; revisit the documentation when implementing actual adapters. Python's [Decimal documentation](https://docs.python.org/3.13/library/decimal.html) supports the explicit decimal and rounding mechanisms used here.

Preserved source and evidence: economics.py, case.json, verify.py, economics-output.json, verification-results.json, research.json and README.md under examples/product-analytics/module-1-pricing-unit-economics/. The model accepts bounded integer usage and decimal-string amounts, uses explicit arithmetic precision and six-decimal display rounding, and has no external-service dependency.

Return to the [Product and Analytics roadmap](/docs/product-analytics) or review [P0: Product Thinking](/docs/product-analytics/product-thinking-requirements-design). Continue with [P2: Product Analytics and Experiments](/docs/product-analytics/product-analytics-experiments)—tracking plans, funnels, cohorts, retention, activation and causal limits.
