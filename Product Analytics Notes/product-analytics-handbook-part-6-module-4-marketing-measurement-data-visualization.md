# Product and Analytics Placement Handbook — Part 6: P4: Marketing Measurement and Data Visualization

**Explain acquisition numbers, reconcile attribution and choose a chart that answers a decision.**

**Verification, 18 October 2026:** 79 Python checks passed with Python 3.13.15 and SQLite 3.50.4. Separately, 36 browser checks passed with D3 7.9.0, Playwright 1.62.1 and Chrome 155.0.8059.84. The examples use invented data, hand-defined attribution rules and a local browser. No ad account, live reporting API, Telegram delivery or causal advertising effect was tested.

---

## 4.0 What an interviewer is really testing

“Our social campaign has the highest ROAS. Should we increase its budget?” tests more than a formula. You need to establish which conversion value was credited, which spend it is divided by, whether reporting is complete, and whether the result predicts the effect of spending more.

The resume-reported marketing digest is a useful connection: fetching reports, computing metrics, summarizing them and recommending an action are separate responsibilities. A recommendation can be well written while its underlying denominator is wrong.

This chapter builds on [P1 pricing and economics](/docs/product-analytics/pricing-unit-economics), [P2 analytics and experiments](/docs/product-analytics/product-analytics-experiments) and [P3 Python/Excel analysis](/docs/product-analytics/python-excel-analysis). [M28 resume deep-dives](/docs/resume-skills/resume-project-experience-deep-dives) identifies the original digest claim as resume-reported; none of the synthetic outputs below establishes its historical impact.

The question choices are editorial preparation priorities. They are not measured interview frequencies, universal performance benchmarks or a claim that a particular platform will ask them.

## 4.1 Acquisition vocabulary and system boundaries

| Term | Plain meaning | Useful follow-up |
| --- | --- | --- |
| Organic acquisition | Visits obtained without paying for that ad placement | Content and staff still have costs |
| Paid search | Ads associated with search intent | Which queries, geography and conversion action? |
| Paid social | Ads delivered in a social platform's inventory | Prospecting or retargeting, and what audience? |
| Campaign | A grouping for advertising objectives and configuration | What settings live at this level on this platform? |
| Ad group / ad set | Intermediate grouping for ads, targeting or delivery settings | Similar names do not guarantee identical platform semantics |
| Creative | The ad's content, such as image, video or copy | Is it compared on the same audience and placement? |
| Landing page | Destination reached after an interaction | Does its promise match the ad and intended action? |
| Conversion action | A defined valuable action | Purchase, lead, qualified lead or another event? |
| Attribution | Assignment of credit for an outcome | Which eligible touches, model and window? |
| Incrementality | Outcome caused by the advertising intervention | What would have happened without it? |

SEO concerns improving organic discoverability. Paid search buys eligible ad exposure. People sometimes use SEM for paid search and sometimes for a broader category; define your usage in the interview rather than arguing over an unstated convention.

Do not compare a lead-generation campaign with a purchase campaign solely by the number called “conversions.” The event and quality threshold must match the business question. Automated bidding optimizes toward its configured objective; choosing that objective is part of the product and measurement design.

## 4.2 From exposure to outcome

```text
Eligible audience -> ad delivery -> impression -> interaction
  -> landing experience -> desired action -> qualified/paid outcome
  -> refund, repeat purchase and longer-term value
```

This is a conceptual journey, not a guarantee that every counted platform event has a directly observed event at every step. A view-through credit can occur without an ad click. Cross-device behavior, tagging gaps and modelled reporting can also affect observed paths.

| Measure | What it counts | Common mistake |
| --- | --- | --- |
| Impressions | Recorded ad displays under the source's definition | Treating displays as unique people |
| Reach | Distinct audience estimate within a defined source/window | Adding overlapping daily or channel reach |
| Frequency | Exposure per reached audience under that definition | Comparing ratios with different populations |
| Clicks | A specified interaction count | Mixing all clicks, link clicks and sessions |
| Sessions | Analytics visits under session rules | Assuming one session per ad click |
| Conversions | Credit for configured actions | Assuming every credit is a distinct order or new customer |

The Google Ads CTR definition uses clicks divided by impressions. The relevant click field still has to be chosen consistently across a report. [Google Ads CTR](https://support.google.com/google-ads/answer/2615875).

## 4.3 Metric formulas with units

| Metric | Definition for this chapter | Unit |
| --- | --- | --- |
| CTR | Clicks / impressions × 100 | Percent |
| CPM | Media spend / impressions × 1,000 | Currency per thousand impressions |
| Average CPC | Media spend / clicks | Currency per click |
| Purchase-credit rate | Supplied purchase credits / clicks × 100 | Percent; explicitly click-denominated |
| Cost per purchase credit | Media spend / supplied purchase credits | Currency per credited action |
| Reported ROAS | Supplied attributed value / media spend | Multiple, such as 2× |
| Media spend per new customer | Media spend / supplied distinct new customers | Currency per new customer |
| Blended net revenue / media spend | Net ledger revenue / media spend | Multiple, with this explicit scope |

Average CPC is cost divided by clicks. [Google Ads average CPC](https://support.google.com/google-ads/answer/14074/average-cost-per-click-avg-cpc-definition?hl=en-GB).

Our purchase-credit rate is deliberately named with its denominator. A platform's reported conversion rate may use eligible ad interactions rather than just clicks, so it is not automatically the same field. Several actions or fractional attribution can also make credited conversions differ from distinct converted people. [Google Ads conversion rate](https://support.google.com/google-ads/answer/2684489).

Store the numerator and denominator alongside the displayed ratio. Use cents for input amounts in this fixture, then format dollars at presentation. A zero denominator makes the ratio undefined; missing input makes it unknown. Both appear as unavailable rather than infinity or a fabricated zero.

## 4.4 CPA, CAC, ROAS and profit are different questions

CPA means cost per defined action. CAC refers to the cost of acquiring a customer, with the cost scope and new-customer definition specified. An order from a returning customer can contribute to purchases without adding a new customer.

Media-only spend per new customer excludes other acquisition costs such as staff, agency fees or creative production. It should not be labelled fully loaded CAC. Likewise, a gross transaction value, a net-of-refund value and a contribution profit are different numerators.

ROAS measures a revenue/value-to-ad-spend relationship. It does not subtract provider costs, cost of goods, fulfilment or other expenses. A high attributed ROAS does not prove positive contribution margin. Marketing ROI should state its profit/cost convention rather than borrowing a revenue ratio and relabelling it.

For a budget decision, connect acquisition cost to contribution and customer behavior. A longer payback period creates cash requirements even if a long-term value estimate looks attractive. The economic reasoning is in [P1](/docs/product-analytics/pricing-unit-economics); this chapter does not invent a universal “good ROAS” threshold.

## 4.5 A source contract before a dashboard

Record the account, currency, report dates, timezone, extraction time, grain, metric fields, conversion definition, attribution settings and report-time basis. Also record whether the amount includes taxes, refunds or cancellations.

| Contract item | Why it changes the comparison |
| --- | --- |
| Account and campaign identity | A campaign name can repeat or change |
| Currency and amount unit | Dollars, cents and micros are different representations |
| Timezone and boundary | A local calendar day differs from a UTC day |
| Action and value field | Leads and purchases are not interchangeable |
| Model and eligible channels | Different rules distribute different credit |
| Click/view eligibility window | The same outcome may qualify under one rule but not another |
| Interaction vs outcome date | A late purchase can be placed on different report dates |
| Extraction as-of time | Later backfills and refunds can revise history |

This example is one **supplied report snapshot**, in USD and UTC. Its daily campaign figures and order ledger are hand-authored inputs, not an automatic date-filtered API extraction. The order-level illustrations use explicit timestamps; they are not expected to reproduce the synthetic aggregate report's attribution model.

In production, normalize compatible data before aggregation. Keep incompatible windows and currencies in separate comparisons until a documented transformation is available. Relabelling an account-local daily bucket “UTC” does not reconstruct its underlying event timestamps.

## 4.6 The executed campaign example

The input includes two campaigns and one exact repeated campaign row. The identity contract removes that repeat. A conflicting row with the same identity fails; a legitimate second reporting date would require that date in a composite key.

| Campaign | Channel | Spend cents | Impressions | Clicks | Supplied purchase credits | Attributed value cents |
| --- | --- | --- | --- | --- | --- | --- |
| A: Intent search | Search | 10,000 | 10,000 | 100 | 2 | 15,000 |
| B: Prospecting social | Social | 5,000 | 5,000 | 100 | 2 | 25,000 |

The exact blended metrics from the executable report are:

```json
{
  "ctr_pct": 1.333333,
  "cpm_cents": 1000.0,
  "cpc_cents": 75.0,
  "purchase_credit_rate_pct": 2.0,
  "cost_per_purchase_credit_cents": 3750.0,
  "reported_roas": 2.666667
}
```

Campaign A's CTR is 1% and B's is 2%. Their unweighted mean is 1.5%, but the overall CTR is 200 clicks divided by 15,000 impressions, or 1.333333%. Recompute ratios from additive components; do not average percentages without their intended weights.

Campaign B's reported ROAS is 5× and A's is 1.5×. That supports a description of the supplied report, not a causal conclusion about reallocating budget. Attribution overlap, margins, customer quality and marginal performance still need investigation.

## 4.7 What can be added, and what cannot

Spend and impressions can be additive across disjoint compatible rows. They double count if the same campaign total appears beside its component ad rows, or if the same response page is imported twice.

Reach and distinct customers generally cannot be summed across overlapping segments. Ratio metrics need their components. Conversion credits can be fractional under some attribution models; coercing them to integers discards information. [GA4 attribution settings and fractional credit](https://support.google.com/analytics/answer/10597962).

The fixture preserves decimal purchase credits and verifies a fractional-credit mutation. It also reports known subtotals, missing-row counts and complete totals separately. Clearing a campaign's spend withholds blended ROAS even if the other campaign still has a known amount.

**Interview check:** “Before summing a breakdown, I would ask whether the rows partition the population, whether they mix hierarchy levels, and whether this measure is additive.”

## 4.8 Attribution models and windows

Attribution assigns credit among eligible touches. A model might prefer a last eligible touch or distribute credit across multiple touches. A lookback window decides how far before the outcome a touch can remain eligible. Model choice, channel eligibility and lookback are related settings but different rules.

The teaching function has two explicitly invented policies:

1. **Last eligible click, seven days:** choose the latest same-customer click no more than seven elapsed days before the order.
2. **Seven-day click, otherwise one-day view:** use the same click rule; only when no eligible click exists, choose the latest same-customer view within one elapsed day.

The lower age bound is zero, the maximum age is inclusive, and future touches are excluded. Equal-time candidates use touch ID as a deterministic tie-breaker. These are fixture policies, not a claim about any platform's exact implementation or default settings.

In GA4, attribution configuration also interacts with dimension scope: changing a reporting attribution model affects compatible event-scoped reports, while user- and session-scoped dimensions have their own semantics. Read the current property settings and report definition rather than assuming every acquisition report uses one model. The same [GA4 settings documentation](https://support.google.com/analytics/answer/10597962) explains these distinctions.

## 4.9 The order ledger remains a separate source

There are four canonical orders. One is a repeat purchase and one has a refund. New-customer flags are supplied scenario facts; the example does not infer first purchase from complete historical customer records.

```json
{
  "orders": 4,
  "new_customers_supplied": 3,
  "gross_cents": 47000,
  "refund_cents": 5000,
  "net_cents": 42000,
  "blended_net_revenue_per_media_spend": 2.8,
  "media_spend_per_supplied_new_customer_cents": 5000.0
}
```

The ratio of net ledger revenue to media spend is 2.8×. It includes unattributed orders and is therefore a blended business indicator under this definition. It is not channel-attributed ROAS and does not establish that media caused all ledger revenue.

The media-only acquisition ratio is 5,000 cents per supplied new customer. Its cost scope is intentionally narrower than fully loaded CAC. The dataset has no cost-of-goods or incremental profit evidence.

For an actual report, validate order IDs, customer identity, refund timing and whether new-customer status is available from an authoritative history. A customer merely appearing for the first time in this small extract need not be a genuinely new customer.

## 4.10 Changing a window changes credit, not the ledger

The exact seven-day click-only allocation is:

```json
{
  "A": 5000,
  "B": 10000,
  "Unattributed": 27000
}
```

The exact click-then-view fallback allocation is:

```json
{
  "A": 20000,
  "B": 10000,
  "Unattributed": 12000
}
```

Both conserve the same 42,000 net ledger cents. Order o2 has no eligible pre-order click but has an eligible view for A, so the fallback policy moves its 15,000 net cents from Unattributed to A. A later click after that order is excluded.

For o3, A's eligible click takes priority over B's later view under the chosen fallback policy. Tests also isolate exactly seven days, one second outside, exactly one day and future touches. Matching an intended boundary is more persuasive than saying that a date filter “looks right.”

Unattributed means not assigned under this supplied touch history and policy. It is not proof that advertising had no influence. Nor should every unattributed order automatically be called organic.

## 4.11 Cross-platform overlap

Independent illustrative claims credit o1 to both A and B. Summing both claim lists counts that order twice. The executable reconciliation returns:

```json
{
  "claim_rows": 4,
  "unique_claimed_orders": 3,
  "summed_claim_value_cents": 40000,
  "unique_claimed_net_cents": 30000,
  "overlap_cents": 10000
}
```

The summed platform claim value is 40,000 cents, while the distinct claimed orders contain 30,000 net cents. The broader ledger is 42,000 net cents because it also includes an unclaimed order. These are different populations.

The source report's four purchase credits happen to equal the ledger's four order records. Agreement of grand totals does not establish agreement of identities: the claim set contains only three unique orders and one overlap.

In real platform reporting, order-level claim identities may not be available or joinable, particularly for modelled outcomes. Then an exact overlap calculation cannot be recovered from aggregate totals alone. State that limitation rather than inventing a precise deduplicated channel split.

## 4.12 Attribution is not incrementality

Attribution asks where to allocate credit among observed or modelled touches. Incrementality asks what additional outcome the intervention caused relative to a counterfactual. Retargeting people already close to buying can look efficient in an attribution report without proving a large incremental effect.

A randomized holdout can compare eligible groups offered different advertising exposure, subject to suitable design, measurement and contamination controls. Geography-based studies have additional assumptions. Existing product experiment habits from P2 still apply: predefine the unit, outcome, observation period and exclusions, and inspect uncertainty and sample integrity.

Google's user-based Conversion Lift describes measuring incremental outcomes and has account-eligibility constraints; the presence of this product is not evidence that this fixture ran a lift study. [Google Conversion Lift](https://support.google.com/google-ads/answer/12005564?hl=en).

**Manual design exercise:** propose a holdout for a retargeting campaign and explain the outcome, assignment unit, cross-device contamination risk and budget decision it could inform. No lift estimate is supplied here.

## 4.13 Diagnosing a campaign change

| Observation | Plausible hypotheses | Next evidence |
| --- | --- | --- |
| CTR falls | Different audience, placement, creative fatigue or delivery mix | Segment impressions/clicks by compatible dimensions |
| CPC rises | Auction conditions, changed mix, bids or lower engagement | Comparable query/audience and delivery reports |
| Clicks rise but purchases fall | Landing failure, low-quality traffic or tracking gap | Site errors, qualified outcomes and tracking checks |
| ROAS jumps overnight | Delayed conversions, a large order, model/window change or real improvement | As-of revisions, order distribution and settings history |
| CPA improves but customers worsen | Easier action or lower-quality conversion mix | Qualified leads, new customers, refunds and contribution |

Avoid presenting any hypothesis as a diagnosis before checking it. Compare like periods, maturity and populations. A dashboard change can come from a reporting revision even when customer behavior did not change.

Before increasing spend, ask whether current efficiency will hold at the margin. The historical average ratio does not describe the next unit of spend. A controlled budget change and an appropriate causal design provide stronger evidence than a ranking alone.

## 4.14 Campaign tags and source identity

UTM parameters attach campaign metadata to URLs. Define a stable naming convention for source, medium, campaign and, where useful, content. A campaign ID is usually a better join key than a mutable display name.

Tags help classify traffic; they do not establish a person's identity or prove incrementality. Redirects, missing tags, inconsistent spelling and internal links tagged as acquisition can create misleading classifications. Validate the landing URL and the resulting recorded metadata. [Google campaign URL guidance](https://support.google.com/analytics/answer/10917952).

Keep the originally observed values and a versioned mapping for normalization. Lowercasing or aliasing a value should follow a policy rather than an unexplained manual edit in the final chart. Use a test order to verify measurement where appropriate; distinguish that from a real customer purchase.

## 4.15 How to build a reliable marketing digest

This is a proposed architecture, not a reconstruction of the employer's exact implementation:

```text
Scheduler -> bounded report request per account/contract
  -> fetch all pages or finish the report job
  -> immutable raw snapshot + query/settings/as-of metadata
  -> schema, completeness and reconciliation checks
  -> normalized metrics with numerator/denominator provenance
  -> deterministic digest facts and evidence links
  -> optional language-model explanation of those facts
  -> reviewable draft -> publication intent -> notification adapter
```

Fetch raw data before summarization. Keep incomplete requests separate from completed snapshots. A failed second response page must not silently become a “spend fell” recommendation. Report staleness and missing fields alongside known values.

A useful logical key includes account, reporting interval, currency, timezone and definition/settings version. Revisions distinguish later corrections or backfills. Retry-safe publication prevents two worker attempts from creating two logical reports. External notification still needs its own delivery and deduplication strategy.

An LLM may explain a verified metric table, but it should not invent missing rows, perform unreviewed spend changes or state unsupported causal conclusions. Any proposed advertising-budget action needs an explicit authorized workflow. The runnable case never sends a message or changes an account.

## 4.16 Reporting APIs: what to understand

Google Ads reporting uses GAQL to select resource attributes, metrics and segments. Search pages results; SearchStream streams them. Adding segments changes result grain and may have compatibility constraints. [Google reporting overview](https://developers.google.com/google-ads/api/docs/reporting/overview), [segmentation guide](https://developers.google.com/google-ads/api/docs/reporting/segmentation).

Meta's maintained business SDK exposes Insights parameters for reporting level, breakdowns, time ranges, attribution windows and action report time. Those settings belong in the report contract. Their existence does not establish the correct settings for a specific account or API version. The documentation page was unavailable during this research, so this parameter claim is grounded in the [official Meta SDK source](https://raw.githubusercontent.com/facebook/facebook-python-business-sdk/main/facebook_business/adobjects/adaccount.py).

For either integration, prepare to explain authentication scope, version pinning, rate-limit handling, retries, pagination/report-job completion, currency conversion policy, backfill and schema changes. A successful HTTP response proves neither a complete multi-page extraction nor a correct metric definition.

No live API request, token, SDK service call or account configuration was exercised. The examples accept authored local JSON so the numerical and chart behavior remains reproducible.

## 4.17 What the publication example actually verifies

`measurement.py` contains a small SQLite publication model. It has one row per logical digest key and stores its revision and body atomically. Publishing the same revision/body again returns duplicate. A conflicting body at the same revision fails. A higher revision replaces the snapshot; a lower revision is rejected.

The checks confirm that a rejected conflicting revision leaves the published body intact and that retries do not add rows. This is an in-memory database model and is closed after the run. It does not simulate concurrent distributed workers, durable production storage, an outbox or a successful Telegram delivery.

**Architecture follow-up:** to make this production-ready, add trusted account scoping, durable raw snapshots, bounded retries, query-version lineage and a transactional publication intent. Decide whether a corrected report edits a prior message or sends a clearly labelled revision. Keep delivery state distinct from calculation state.

The important separation is: raw data fetched, snapshot validated, facts computed, draft approved, publication committed and delivery acknowledged. One undifferentiated “done” flag cannot explain failures across these boundaries.

## 4.18 Choose the chart from the question

| Question | Useful chart | Why |
| --- | --- | --- |
| Which campaign spent more? | Sorted horizontal bars | Lengths share a baseline |
| How did spend evolve? | Time-series line | Ordered time reveals trend and gaps |
| Where does spend sit in a hierarchy? | Treemap plus exact-value table | Area shows composition across levels |
| Does higher spend associate with higher value? | Scatter plot | Shows paired values, with causal limits |
| How variable is order value? | Histogram or box plot | Shows distribution rather than only an average |
| Which funnel stage loses eligible users? | Stage counts and rates | Makes stage population and denominator explicit |
| How did channel share change? | Stacked bars or small multiples | Shows composition without hiding the overall total |

For close comparisons, aligned position or length is easier to compare precisely than rectangle area. Use a bar chart when the decision requires ranking near-equal values. A treemap is useful for broad composition and hierarchy, not an all-purpose replacement for bars.

Line charts should not connect unrelated categories as though they were ordered time. Pie slices and treemap rectangles make small differences harder to judge. A second axis can manufacture apparent agreement between unrelated series; use labelled small multiples when that is clearer.

## 4.19 Honest encodings and labels

Bar length encodes magnitude, so use a zero baseline for ordinary magnitude comparisons. A line chart can use a narrower range when its purpose is to inspect variation, but the axis and context must make that choice clear. Log scales require a suitable interpretation and cannot represent zero in the usual logarithmic mapping.

Show units, date range, as-of time, population and metric definition. Display uncertainty or missingness where it affects the decision. A missing day is not necessarily zero activity and should not be drawn as a confirmed zero.

Use color consistently. A channel color should keep its meaning when filters reorder rows. Do not encode “good” with green for one chart and “high spend” with the same green elsewhere without a clear legend. A categorical palette identifies categories; a sequential scale represents ordered magnitude; a diverging scale needs a meaningful midpoint.

Avoid making a large area and a strong color both imply “best” when the two encodings mean different things. In the companion treemap, **area means known spend, color means channel, and neither means causal performance**.

## 4.20 What D3 is and how it works

D3 is a JavaScript toolkit for data-driven visualization. It supplies utilities for selection, scales, layouts and other operations; it does not automatically choose an honest metric or chart. SVG elements provide a inspectable representation for the small example.

The local pipeline is:

```text
Prepared JSON -> validate fields and stable campaign keys
  -> choose channel and bar measure
  -> compute scale domains and layout coordinates
  -> join data to SVG elements
  -> set geometry, text and colors
  -> update exact-value table and empty/missing explanations
```

A scale maps a data domain to a visual range. The example maps a nonnegative measure from zero to the largest known selected value into a pixel width. It uses a safe fallback domain for zero/empty data instead of dividing by a zero maximum. [D3 linear scales](https://d3js.org/d3-scale/linear).

The chosen domain is recomputed after filtering; this makes within-selection comparison convenient but changes visual context across selections. Exact labels stay visible. If the task is comparing views across filters or dates, consider a fixed shared domain and make that choice explicit.

## 4.21 Data joins, keys and updates

The bar renderer uses a keyed join:

```javascript
svg.selectAll('g.plot').data([null]).join('g').attr('class', 'plot')
  .selectAll('rect.campaign-bar')
  .data(valid, row => row.campaign_id).join('rect');
```

Enter creates elements for new data, update changes existing elements, and exit removes elements no longer represented. A stable key preserves which campaign an element belongs to when the order changes. Index-based matching can associate an old element with a different campaign after sorting. [D3 data joins](https://d3js.org/d3-selection/joining).

The browser test holds a reference to A's actual DOM node, reverses the data and verifies that A keeps that node while the displayed order changes. Filtering removes departed bars, tiles and table rows. Repeated rendering does not append duplicate charts.

Keys need to be unique in the joined selection. The example rejects duplicate campaign keys before rendering. A display name alone can collide; use a stable identity at the intended grain.

In a React application, decide which system owns which nodes. React can own the component and D3 can own a dedicated SVG subtree, or React can render geometry computed by D3. Competing ownership of the same nodes makes updates harder to reason about. This companion is standalone JavaScript, not a React integration test.

## 4.22 Treemap construction and its traps

A treemap subdivides a rectangular region according to values in a hierarchy. The teaching hierarchy is root → channel → campaign. Each campaign contributes its nonnegative known spend. Parent totals are calculated from children.

```javascript
const root = d3.hierarchy(hierarchy)
  .sum(node => node.children ? 0 : node.spend_cents);
d3.treemap().size([canvasWidth - 20, 240]).paddingInner(3)(root);
```

The accessor returns zero for internal nodes so a supplied parent total is not added a second time. D3's hierarchy sum visits internal nodes as well as leaves. [D3 hierarchy sums](https://d3js.org/d3-hierarchy/hierarchy).

The layout assigns rectangle edges x0, y0, x1 and y1. Width is x1−x0 and height is y1−y0. The browser tests verify that an unpadded test layout conserves the containing area; the displayed layout uses padding, so visible filled area excludes the gaps. [D3 treemap layout](https://d3js.org/d3-hierarchy/treemap).

Spend is additive and nonnegative, making it suitable for this area encoding. ROAS is a ratio, so summing campaign ROAS into parent area has no valid business meaning. Negative profit also cannot be represented faithfully by an ordinary positive-area treemap; choose a different encoding.

Stable data keys preserve element identity but do not guarantee stable treemap positions. Changing values or the sort order can rearrange tiles. Evaluate layout stability when readers compare successive digests. Tiny tiles need a table or detail view rather than unreadable labels.

## 4.23 Responsive behavior and accessible alternatives

The example measures the available SVG width and recomputes layout on resize. This keeps chart text at a readable size instead of shrinking an entire wide desktop graphic onto a phone. Narrow treemap tiles use a short campaign ID; the full campaign name and exact values remain in the adjacent table.

Controls have labels and native keyboard behavior. Each SVG has a title and description. Channel colors are accompanied by text, and the table provides exact values without requiring color perception or hovering. Filter status is exposed as a live text update.

For complex charts, provide a short explanation and an appropriate longer description or data equivalent. [W3C guidance on complex images](https://www.w3.org/WAI/tutorials/images/complex/).

The browser checks verify names, table values, focusability, script errors, responsive geometry and absence of document overflow. Desktop and mobile screenshots were visually reviewed. They are not a complete screen-reader, contrast, keyboard-navigation or WCAG conformance audit; those remain manual review tasks before a real product release.

Avoid adding animation unless it helps readers track change. Respect reduced-motion preferences when introducing it. The current companion uses direct updates and makes no animation or performance-benchmark claim.

## 4.24 Running and extending the examples

The companion is in `examples/product-analytics/module-4-marketing-measurement-data-visualization/`. It preserves the synthetic source, Python logic, actual output, assertions, D3 renderer, pinned npm dependencies and browser checks.

From the repository root:

```powershell
python examples/product-analytics/module-4-marketing-measurement-data-visualization/measurement.py
python examples/product-analytics/module-4-marketing-measurement-data-visualization/verify.py
```

For the browser checks, enter the example folder, install its lockfile dependencies with `npm ci --ignore-scripts`, then run `npm run verify`. The verifier uses installed Chrome through Playwright's chrome channel, starts a temporary loopback server, exercises the real D3 code, captures ignored QA previews and closes the browser and listener.

The README gives a separate manual preview command. No server remains running after the automated checks, and port 3000 stays stopped. The chapter's website integration presents the notes; the interactive teaching app is a separate local companion.

When extending the snapshot to multiple dates or accounts, expand the identity key and contract before concatenating rows. Preserve raw snapshots, compute ratios after aggregation, and decide how late conversions/refunds revise prior reports. Do not silently overwrite provenance to make totals agree.

## 4.25 Interview questions and answers

### Q1. What is the difference between impressions and reach?

Impressions count recorded ad displays. Reach estimates a distinct audience within a specified source and window. The same person can create multiple impressions, and overlapping reach cannot simply be summed across days or platforms.

### Q2. How do you calculate CTR?

Divide the chosen click count by impressions and express it as a percentage. I retain both components and specify whether clicks means all clicks, link clicks or another field.

### Q3. Why can averaging campaign CTRs be wrong?

The campaigns can have different impression denominators. I sum compatible clicks and impressions, then divide. The case's unweighted 1.5% differs from its blended 1.333333%.

### Q4. Explain CPC, CPM and CPA.

CPC is cost per click, CPM is cost per thousand impressions, and CPA is cost per defined action. The action, cost scope and observation period must be stated before comparing campaigns.

### Q5. Is a conversion always a new customer?

No. It may be a lead, a repeat purchase, another configured action or fractional attribution credit. New-customer acquisition requires a customer definition and sufficient history.

### Q6. How does CAC differ from CPA?

CAC concerns acquiring a new customer and needs an explicit acquisition-cost scope. CPA concerns a defined action. Media-only spend per customer excludes costs that may belong in a fully loaded CAC.

### Q7. Is ROAS the same as ROI?

ROAS relates attributed revenue or value to advertising spend. ROI needs a clearly defined profit and cost basis. Revenue ratios alone omit costs and do not establish profitability.

### Q8. What is a good ROAS?

There is no universal threshold. The acceptable value depends on contribution, refunds, customer retention, payback, cash constraints and how attribution was computed. I would connect the target to the business model.

### Q9. How do a campaign, ad set and creative relate?

They describe levels of organization and delivery/content configuration. The exact settings differ by platform, so I check which level controls the objective, audience and budget rather than assuming names are interchangeable.

### Q10. What does an attribution window do?

It limits which earlier touches are eligible to receive outcome credit. The model then assigns credit among eligible touches. Window changes can move credited revenue without changing actual orders.

### Q11. What is view-through attribution?

It assigns credit under a rule to an eligible earlier ad view even when there was no required click. I specify its window and priority rules, and avoid treating the credit as proof of incremental impact.

### Q12. Why can two platforms claim the same purchase?

Each can apply its own eligible-touch history and attribution rules to one order. Summing independent claims can therefore double count value. The case has 10,000 cents of overlap.

### Q13. Why do the ad dashboard, GA4 and order database disagree?

They can differ in identity, conversion definitions, models, windows, timezones, report-time basis, refunds, missing data and extraction freshness. I align those contracts before investigating row-level differences.

### Q14. Does unattributed mean organic?

No. It means the available history and policy did not assign credit. Missing tracking or an expired window can also produce that result. I do not infer an acquisition source from absence alone.

### Q15. Does high attributed ROAS prove the campaign caused sales?

No. Attribution assigns credit; causal impact needs a counterfactual. A suitable holdout can help estimate incremental outcomes, subject to its design and uncertainty.

### Q16. How would you decide whether to increase a budget?

Check data completeness, contribution, customer quality and attribution limitations, then evaluate marginal performance through an appropriately controlled change. The current average ROAS does not predict the next unit of spend by itself.

### Q17. What would you investigate if CTR fell?

Compare compatible audience, placement, device, time and creative segments, then consider delivery mix, fatigue and tracking. I treat these as hypotheses until the supporting data distinguishes them.

### Q18. What are UTMs useful for?

They attach campaign metadata to traffic URLs. Stable naming and IDs help classify and join traffic. Tags do not establish identity, guarantee capture or prove advertising caused a conversion.

### Q19. How would you build a daily marketing digest?

Fetch complete source snapshots with settings and as-of metadata, validate them, calculate deterministic facts, then produce a reviewable summary. Publication revisions and notification delivery need separate state and retry rules.

### Q20. Where should an LLM fit in that system?

It can explain verified facts and propose questions. It should retain provenance and uncertainty, while arithmetic and completeness checks remain deterministic. Changing spend requires a separately authorized action workflow.

### Q21. What reporting API failures would you plan for?

Partial pagination, report-job failure, throttling, stale snapshots, schema/version changes and mismatched query settings. A successful first page does not prove that a report is complete.

### Q22. How do you prevent duplicate digests?

Use a logical report identity and explicit revision/body rules for retry-safe publication. Track external delivery separately. The SQLite case verifies local publication semantics, not distributed exactly-once messaging.

### Q23. How do you choose between a bar chart and a treemap?

Use bars for precise comparisons on a common baseline. Use a treemap for broad composition within a hierarchy, with exact values available elsewhere. The decision and task determine the choice.

### Q24. What is D3?

D3 is a JavaScript toolkit for data-driven visualization, including DOM selections, scales and layouts. It gives control over how data maps to marks, but I still choose meaningful measures and validate the source.

### Q25. What are domain and range in a scale?

The domain is the data interval and the range is the visual interval. In the bar example, a known nonnegative value maps to a width. I handle empty or zero data and state whether domains change after filtering.

### Q26. Why use stable keys in a D3 join?

Keys associate data identities with existing DOM elements across updates. Sorting then preserves which element represents which campaign. Duplicate keys still require validation; a key does not repair an ambiguous source.

### Q27. How do you construct a treemap without double counting?

Build a hierarchy, contribute additive leaf values once, calculate parent totals and run the layout. If an accessor adds supplied parent totals as well as child values, the root can be inflated.

### Q28. Can you size treemap areas by ROAS or negative profit?

Ordinary part-to-whole area needs an additive nonnegative measure. ROAS is not additive, and negative profit cannot occupy negative area. Use another chart or a clearly separated encoding appropriate to the question.

### Q29. How would you make a chart usable on a phone and without color?

Recompute layout for available width, preserve readable labels, and provide exact values in a table. Use labelled controls, textual explanations and accessible names; do not make hovering or color the only way to obtain information.

### Q30. How would you defend the marketing-digest claim on your resume?

Explain the user's decision, source/report contract, deterministic metrics, your contribution and one failure you handled. Identify the evidence for any impact claim. This teaching case cannot establish the original project's ROI or adoption.

## 4.26 A 30-minute mock

| Time | Prompt | Evidence to include |
| --- | --- | --- |
| 0–5 min | Define the acquisition report and its audience | Action, population, window, units and as-of time |
| 5–11 min | Explain CTR, CPA, CAC and ROAS | Numerators, denominators and cost scope |
| 11–17 min | Reconcile the platform claims with orders | Overlap, refunds, identity and unattributed outcomes |
| 17–23 min | Design a reliable marketing digest | Complete snapshots, publication revisions and delivery boundary |
| 23–27 min | Choose and implement a chart | Bar vs treemap, keys, scale and missing-state behavior |
| 27–30 min | Recommend a next action and defend your contribution | Uncertainty, causal limits and actual project evidence |

For each answer, look for a concrete mechanism, a failure case and a decision. A polished recommendation without a source contract should not receive full credit.

## 4.27 Practice tasks and answer checkpoints

1. Write a report contract for one acquisition decision, including the action, grain, currency and as-of time.
2. Run the blended metrics and explain why the campaign CTR mean differs from the overall CTR.
3. Replace one campaign's spend with null and trace which totals and ratios must be withheld.
4. Change purchase credit to a fraction and explain why it need not equal a distinct customer count.
5. Trace o2 under both attribution rules, including its refund and post-order click.
6. Move a click to exactly seven days before an order, then one second earlier, and predict eligibility.
7. Reconcile the independent claims, distinct claimed orders and broader net order ledger.
8. Propose a manual holdout study for retargeting and state what attribution cannot establish.
9. Retry a digest publication, introduce a conflicting same-revision body, and explain the stored result.
10. Reorder/filter the D3 dataset and inspect DOM identity, removed marks and table values.
11. Explain the treemap sum accessor, change spend to zero/missing, and compare its suitability with a bar chart.
12. Review the mobile view and keyboard/screen-reader experience, then deliver a two-minute resume explanation with evidence limits.

### Answer checkpoints

| Task | Checkpoint |
| --- | --- |
| 1 | The contract explains which values are comparable and which source can establish the desired outcome |
| 2 | Blended CTR is 1.333333%; unweighted mean is 1.5%; ratios come from compatible components |
| 3 | Known spend remains visible, but incomplete spend withholds complete ROAS and acquisition-cost ratios |
| 4 | Fractional attribution credit is preserved; customer acquisition needs a separate identity/history definition |
| 5 | o2 has 15,000 net cents; it is Unattributed under click-only and A under click-then-view fallback |
| 6 | The teaching policy includes the exact seven-day age and excludes one second beyond it |
| 7 | Summed claims are 40,000; distinct claimed value is 30,000; broader ledger net is 42,000 cents |
| 8 | Define assignment, outcome, follow-up and contamination risks; no causal lift is claimed from these reports |
| 9 | Exact retry is a duplicate; conflict fails without changing the old body; newer revision can replace it |
| 10 | A keeps its keyed DOM identity after reorder; departed data leaves bars, tiles and table |
| 11 | Internal nodes contribute zero; area uses known nonnegative spend, not a summed ROAS |
| 12 | Automated browser checks support the reviewed cases; a full accessibility audit and personal interview practice remain manual |

The holdout proposal, complete accessibility review and personal delivery are reader exercises. Passing the example checks does not establish that you have completed them.

## 4.28 Research and evidence boundary

Primary documentation was checked on 18 October 2026. Google sources support CTR/CPC/conversion vocabulary, attribution settings, campaign tags, reporting and lift-study concepts. Meta's official SDK source supports the named request parameters; no current default attribution window or live account behavior is asserted.

D3's current documentation supports scales, joins and hierarchy layouts. The executed dependency is pinned to D3 7.9.0. The browser checks exercise actual SVG/DOM updates and mobile behavior on the recorded Chrome version. They do not reproduce a vendor chart or establish a performance benchmark.

`research.json`, the lockfile, source snapshot hashes, Python observations and browser evidence are preserved beside the example. No real advertising cost, customer revenue, production digest, original employer architecture or incremental return was reproduced.

## 4.29 Exit checklist

- [ ] I can distinguish impressions, reach, clicks, sessions and conversion actions.
- [ ] I can calculate CTR, CPC, CPM and cost per defined action with units.
- [ ] I can separate CPA, media-only acquisition cost, CAC, ROAS and profit.
- [ ] I can aggregate compatible components without averaging ratios blindly.
- [ ] I can preserve fractional credits, unknown values and zero denominators.
- [ ] I can define a report's model, window, timezone, grain and as-of time.
- [ ] I can trace click/view eligibility and explain the fixture's boundaries.
- [ ] I can explain cross-platform overlap and reconcile canonical order values.
- [ ] I can distinguish attribution from incremental causal impact.
- [ ] I can describe a complete, retry-safe marketing-digest architecture.
- [ ] I can choose a chart based on the comparison the reader needs.
- [ ] I can explain D3 scales, stable keys and enter/update/exit behavior.
- [ ] I can build a treemap without double counting and provide accessible alternatives.
- [ ] I can defend my actual resume contribution without inventing measured impact.

Return to the [master roadmap](/docs/product-analytics) or revisit [P3: Python and Excel for Analysis](/docs/product-analytics/python-excel-analysis).

Continue with [P5: Product and Analytics Resume Drills and Revision](/docs/product-analytics/consolidation-resume-drills)—decision stories, evidence, confusable pairs, stakeholder situations and final mocks.
