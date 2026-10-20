# SQL Interview Problem Book — Part 7: Consolidation and Mocks

**Explain the grain, predict the result, expose the wrong answer, then adapt the query.**

## 1. What a strong SQL answer contains

A strong explanation has an output contract, a query, a small expected example, a counterexample and a relevant implementation trade-off. A correct-looking aggregate can still answer the wrong question if it uses the wrong population or grain.

The thirty solutions are in the four case chapters: [joins](/docs/sql-interview/joins-grain-and-null-semantics), [windows](/docs/sql-interview/windows-and-time-series), [analytics](/docs/sql-interview/funnels-cohorts-and-retention) and [reconciliation](/docs/sql-interview/reconciliation-and-query-plans). Use the [solving method](/docs/sql-interview/dataset-and-solving-method) when an assumption is unclear.

## 2. Eighteen confusable pairs

| Pair | Distinction |
| --- | --- |
| Output grain / physical row count | What a row represents versus how many current rows exist |
| Join retention / join cardinality | Keeping a left record versus how many matches it produces |
| ON filter / WHERE filter | Match qualification versus filtering the joined result |
| COUNT(*) / COUNT(identity) | Result rows versus non-NULL observations |
| Distinct entities / distinct amounts | Deduplicating business identity versus losing legitimate equal values |
| Known subtotal / complete bill | Observed contribution versus all required inputs resolved |
| NULL / zero | Unknown versus an observed numeric value |
| NOT EXISTS / NULL-bearing NOT IN | Absence of a matching record versus three-valued membership comparison |
| ROW_NUMBER / DENSE_RANK | One ordered position versus tied distinct value tiers |
| Window order / final order | Calculation sequence versus returned row sequence |
| Seven rows / seven days | Equal only after a one-row-per-day spine exists |
| Current plan / historical plan | Latest state now versus state effective at the business instant |
| Exact-day / any-week retention | A specified bucket versus any return in a bounded interval |
| Event time / receipt time | When behavior occurred versus when it became known |
| User conversion / cart conversion | A user can create several carts with different outcomes |
| Bill / confirmed payment | Requested amount versus succeeded payment evidence |
| Payment record / refund record | Independent child facts that can multiply each other |
| Index existence / useful access path | A data structure exists versus the actual plan using it effectively |

## 3. Six executed wrong-answer counterexamples

| Wrong approach | Observed wrong result | Correct contract/result |
| --- | --- | --- |
| Paid-order condition in WHERE after a left join | Six customers remain | Q01 retains all eight t1 customers |
| COUNT(*) for an unmatched customer's paid orders | One row counted | c6 has zero paid orders |
| SUM(DISTINCT bill) to repair duplicated billing | c1 has 3,000 cents | Legitimate equal orders make its total 4,000 |
| NOT IN over the NULL-bearing exclusion list | No customers returned | Q08 retains seven eligible customers |
| Raw payment rows joined to raw refund rows for o01 | 2,000 confirmed and 200 refunded cents | Independent facts contain 1,000 and 100 cents |
| Seven sparse sales rows treated as seven days on Oct 11 | 11,100 known cents | The seven calendar-day known contribution is 1,900 |

These are actual outputs preserved in counterexamples.json. The last counterexample extends the report end by one day so 11 October is included; it is not Q12's default output slice. The figures are invented teaching values, not real invoices.

## 4. Twelve diagnosis cards

| ID | Symptom | First discriminating check |
| --- | --- | --- |
| D01 | Zero-order customers disappear | Inspect optional-side WHERE conditions |
| D02 | Bills increase after enrichment | Compare row multiplicity per order before summing |
| D03 | Equal legitimate bills disappear | Check whether DISTINCT was applied to a value instead of identity |
| D04 | An exclusion query returns nothing | Inspect NULL values inside the NOT IN source |
| D05 | Latest-row output changes between runs | Add a stable tie-breaker to the window order |
| D06 | Rolling metric skips quiet days | Inspect the date spine and pre-window history |
| D07 | Session counts change after a late event | Recompute event-time neighbors and apply the revision policy |
| D08 | Recent cohorts look artificially weak | Check the full observation horizon before eligibility |
| D09 | Historical retention improves overnight | Compare receipt cutoffs and late/identity changes |
| D10 | A plan segment loses unknown users | Inspect inner joins and historical dimension gaps |
| D11 | Both payments and refunds grow after a join | Aggregate child facts independently before joining |
| D12 | An index exists but the query scans | Inspect predicates, selectivity, leading columns and actual plan |

Treat the card as a hypothesis, not a confirmed production incident. A real investigation needs the original source, query, snapshot and authority to inspect them.

## 5. Twenty-four oral checks

| ID | Interview question | Answer checkpoint |
| --- | --- | --- |
| O01 | What does one output row represent? | State the entity/group/time grain before choosing joins |
| O02 | How do you retain no-order customers? | Drive from customers and keep optional-side restrictions in ON |
| O03 | Why can a left join multiply rows? | A left record may match several right records |
| O04 | Why is SUM(DISTINCT amount) unsafe? | Several real entities can share one amount |
| O05 | What does SUM of all missing amounts return here? | NULL; completeness still needs a separate missing count |
| O06 | When is COALESCE to zero justified? | When the source contract establishes absence as no contribution, not unknown |
| O07 | Why does the exclusion list favor NOT EXISTS? | A supplied NULL cannot poison the membership result |
| O08 | How do you keep the top two value tiers? | Rank complete group totals with DENSE_RANK and preserve ties |
| O09 | How do you choose one latest tied row? | A total ordering including a deterministic tie-breaker |
| O10 | Why filter a window result in an outer query? | Its calculated value is not a pre-window WHERE input |
| O11 | What makes ROWS a calendar window? | A complete one-row-per-day spine and adequate history |
| O12 | Why filter presentation after a rolling window? | Earlier rows may be needed for the first displayed result |
| O13 | What starts a new session in Q15? | A first activity or a strictly greater-than-1,800-second gap |
| O14 | What can a late bridging event change? | Previously separate session neighbors and session labels |
| O15 | Why select a plan as of signup or order time? | Current state can introduce future classification |
| O16 | What is an ordered funnel completion? | A qualifying completion after the specified valid start and before the horizon |
| O17 | Why require a full return day? | Users need the same opportunity to produce the defined outcome |
| O18 | Can DAU be summed to obtain seven-day distinct users? | No; the same person can appear on several days |
| O19 | Why does D7 change when knowledge changes? | A qualifying earlier event can arrive later |
| O20 | Is first in the supplied data a verified first-ever purchase? | No; complete historical evidence would be needed |
| O21 | Does no recorded confirmed payment make the bill zero? | No; source-completeness and amount meaning differ |
| O22 | What is wrong with a payment-refund raw join? | It creates a cross-product among each order's child facts |
| O23 | What does the local index experiment establish? | A changed access path with the same ordered result on the tested fixture |
| O24 | Does the SQLite result prove PostgreSQL parity? | No; adapt and execute the target dialect and driver explicitly |

## 6. Mock A: query construction, 45 minutes

Use the shared fixture without reading the worked answers. The time allocation is an editorial practice format, not a statement about a company's process.

| Minutes | Task | What to explain |
| --- | --- | --- |
| 0–5 | Clarify Q01 | Scope, grain, status, interval and expected zero row |
| 5–15 | Write and test Q01/Q04 | Retention, COUNT and order/item cardinality |
| 15–25 | Solve Q09/Q10 | Ties versus one deterministic selection |
| 25–35 | Solve Q15 | Deduplication, event order and the exact gap boundary |
| 35–42 | Accept a changed input | New customer, equal bill, tie or bridging event |
| 42–45 | Explain a wrong alternative | State the smallest counterexample and repair |

## 7. Mock B: analytical investigation, 45 minutes

**Scenario:** a hypothetical dashboard reports better retention and more confirmed revenue, but its data was refreshed late and several refunds arrived for one order.

| Minutes | Task | What to explain |
| --- | --- | --- |
| 0–5 | Define the analytical contract | Event/receipt cutoffs, completeness and money units |
| 5–15 | Solve Q17 | Mature denominator and ordered completion |
| 15–25 | Solve Q19/Q21 | Late knowledge and distinct active users |
| 25–35 | Solve Q27/Q28 | Independent child facts, confirmed net and unknown bills |
| 35–42 | Inspect Q30 plans | Matching index, ordered result and performance limits |
| 42–45 | Recommend the next check | Resolve the actual source difference before claiming a business effect |

### Feedback checklist for both mocks

Look for a stated contract, correctly scoped query, deterministic output, normal and boundary examples, and a clear explanation of what the result cannot establish. Do not grade only query length or memorized syntax. A different valid solution is welcome when it preserves the intended result.

## 8. Twelve practice tasks

1. Load the fixture and explain all nine source grains.
2. Predict the zero-order customers before executing Q01/Q02.
3. Explain why c1 has two legitimate equal bills and how that affects Q04.
4. Reproduce the NULL exclusion and wrong DISTINCT counterexamples.
5. Modify a revenue tie and compare ROW_NUMBER with the required value tiers.
6. Extend the rolling report to Oct 11 and explain the sparse-row counterexample.
7. Move a session gap from 1,801 to 1,800 seconds and predict the new sessions.
8. Move a completion to one second before its exclusive funnel endpoint.
9. Explain initial and revised D7 without describing a causal product improvement.
10. Repair o05's line total and explain which reconciliation exception remains.
11. Explain the two Q30 plans without inventing a speedup number.
12. Attempt both mocks, record one missed assumption and solve a changed case again.

### Answer checkpoints

The executable verifier covers the actual outputs and selected changed-input cases. The roadmap lists its 86 checks. c6 and c7 have no paid orders in the interval; c1's known report bill is 4,000 cents; exact-threshold session gaps stay in the same session; a completion at the exclusive endpoint is excluded; revised D7 changes as data becomes known. Q29 retains missing-bill and missing-item evidence after the line mismatch is repaired. Consult each problem's exact result for the remaining row-level details.

## 9. Seven-day revision route

| Day | Work | Produce |
| --- | --- | --- |
| 1 | Method and Q01–Q04 | Output contracts and correct zero/missing behavior |
| 2 | Q05–Q10 | Reconciled facts and deterministic ties |
| 3 | Q11–Q16 | Calendar, sessions and historical dimension explanations |
| 4 | Q17–Q20 | Mature funnels and retention definitions |
| 5 | Q21–Q26 | Distinct populations, late data and source diagnostics |
| 6 | Q27–Q30 and Mock A | Reconciliation, actual plan explanation and feedback |
| 7 | Mock B and targeted repair | A changed example for every concept you missed |

The schedule is a suggested sequence, not a measured learning-time promise. Keep an error log with the mistaken assumption and a different example that demonstrates the correction.

## 10. Exit checklist

- [ ] I can define source and output grain before joining.
- [ ] I can preserve customers with no qualifying child rows.
- [ ] I can distinguish NULL, zero, counts and complete amounts.
- [ ] I can diagnose both one-child and multi-fact fan-out.
- [ ] I can rank tied values and select one stable latest record.
- [ ] I can calculate calendar windows with the required history.
- [ ] I can explain islands, inactivity sessions and historical dimensions.
- [ ] I can define a mature ordered funnel and exact return window.
- [ ] I can distinguish behavior time from receipt-time knowledge.
- [ ] I can reconcile lines, bills, payments and refunds under a stated contract.
- [ ] I can read the actual query-plan evidence and state its limits.
- [ ] I have attempted the questions and both mocks without copying the solutions first.

The SQL interview book is fully authored. Continue targeted practice from the [roadmap](/docs/sql-interview), or revisit [DBMS foundations](/docs/dbms) when a concept remains unclear.
