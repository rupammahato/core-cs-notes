# Analytics Engineering and Warehousing — Part 10: Consolidation and Mocks

**Defend the grain, history, source cursor, publication and consumer contract together.**

## 1. Twenty confusable pairs

| Pair | Distinction |
| --- | --- |
| OLTP / OLAP | Transactional state access versus analytical workloads |
| File format / table format | Physical file representation versus table metadata/operations |
| ETL / ELT | Transformation before versus after loading into the intended target |
| Layer name / data contract | Organizational convention versus actual grain and guarantees |
| Delivery / source version | Transport occurrence versus a business version identity |
| Source version / receipt sequence | Truth ordering versus what has arrived locally |
| Current state / event ledger | Latest entity projection versus immutable event-grain facts |
| Type 1 / Type 2 | Attribute overwrite versus effective version retention |
| Effective / knowledge time | When a state applies versus when its evidence became known |
| Unknown member / missing fact | Unavailable classification versus absent business observation |
| Source date / extraction cursor | Business placement versus newly received source knowledge |
| New partition / affected partition | Where a row is now versus every old/new location needing repair |
| Snapshot / supplied effective history | Observed source changes versus an explicitly dated source timeline |
| Unique-key declaration / uniqueness test | Matching configuration versus an assertion about actual data |
| Model contract / business correctness | Output shape/enforcement versus valid semantics and coverage |
| Quality / completeness | Tested fitness of admitted data versus required source coverage |
| Freshness / sequence gap | Relevant time age versus local progress distance |
| Known subtotal / complete amount | Observed contribution versus all admitted required amounts resolved |
| Rate value / ratio state | A computed number versus numerator/denominator needed to reaggregate |
| Local plan / production performance | Executed access-path evidence versus measured scale, latency and cost |

## 2. Twelve diagnosis cards

| ID | Symptom | First discriminating check |
| --- | --- | --- |
| D01 | More delivered rows than business facts | Inspect version identity, duplicates, deletes and grain |
| D02 | Historical plan totals change unexpectedly | Inspect effective dates, correction policy and publication version |
| D03 | One fact matches several dimension rows | Check temporal overlap and scoped join keys |
| D04 | Late customers reduce totals | Check whether unmatched facts were dropped instead of exposed as unknown |
| D05 | A deleted record returns | Inspect source version fences and tombstone retention |
| D06 | Incremental and full totals disagree | Trace old/new affected keys, partitions and dimension changes |
| D07 | An empty date retains yesterday's amount | Check whether replacement clears partitions with no new groups |
| D08 | Job succeeds but dashboard is wrong | Inspect definitions, semantic tests and publication boundaries |
| D09 | Checkpoint advances while readers have old data | Inspect atomic effects/pointer/cursor commit |
| D10 | Data is fresh but incomplete | Inspect source control totals, rejected input and quarantine |
| D11 | Averages disagree between dashboards | Compare unit, numerator/denominator and aggregation weights |
| D12 | A faster query is called cheaper without evidence | Inspect real engine plan, scanned data and pricing |

These are investigation hypotheses. A useful diagnosis needs source/definition/run evidence, not only the most familiar failure story.

## 3. Thirty oral checks

| ID | Interview question | Answer checkpoint |
| --- | --- | --- |
| O01 | What is the first modeling decision? | State the business process and exact fact grain |
| O02 | Why are raw and fact counts different? | Deliveries, versions and admitted entities have different grains |
| O03 | Does gold mean complete? | No; names do not establish tests or coverage |
| O04 | Why preserve tenant in keys? | Business identities can repeat across tenants |
| O05 | Why use a dimension surrogate key? | Distinguish warehouse rows/versions under a stable policy |
| O06 | How do you join Type 2 history? | Scoped identity and a nonoverlapping half-open validity interval |
| O07 | What does an unknown member preserve? | A known fact whose classification is unavailable |
| O08 | Is current known effective history bitemporal? | Not without a separate knowledge-time design |
| O09 | What does a repeated delivery mean? | Transport retry does not necessarily mean another business version |
| O10 | Why not sort entity truth by arrival? | Stale versions can arrive after newer versions |
| O11 | What prevents deleted-state resurrection? | Retained source ordering/delete evidence and valid replay policy |
| O12 | How are conflicts handled here? | Hold the entire ambiguous entity out of admitted state |
| O13 | What does ref contribute in dbt? | Relation resolution and modeled dependency information |
| O14 | Does unique_key prove uniqueness? | No; actual input/target assertions are needed |
| O15 | Contract versus data test? | Output expectations/enforcement versus assertions over data; both have scope limits |
| O16 | Can a snapshot recover unobserved intermediate states? | Not without another source of that history |
| O17 | Why can an event-date lookback miss facts? | New knowledge can describe older business dates |
| O18 | Which partitions change after a move? | Both old and new locations, including empty replacements |
| O19 | Why can a dimension correction change old marts? | Historical classification under current knowledge can be restated |
| O20 | Does the lesson optimize incremental compute? | No; full candidates validate partition-selected publication |
| O21 | What commits with the publication cursor? | Tested model effects, versioned mart and active pointer in one local transaction |
| O22 | What remains after publication failure? | Accepted raw input and the prior successful consumer state |
| O23 | What does zero cursor gap fail to prove? | Source completeness, wall-clock freshness and semantic fitness |
| O24 | Why expose missing bills separately? | Unknown amounts cannot be silently converted to observed zero |
| O25 | How should rates be reaggregated? | Preserve the intended numerator/denominator and weighting |
| O26 | What does an old mart run preserve? | Its published labels/measures, not every current fact/dimension generation |
| O27 | Does a tenant predicate authenticate a user? | No; trusted identity and permission enforcement are separate |
| O28 | What does the index experiment measure? | A local SQLite access path and result preservation, not timing |
| O29 | What does the pruning estimate establish? | Arithmetic under logical assumptions, not actual scanned bytes or a bill |
| O30 | What should a backfill publish with? | Source/definition scope, validation evidence, version and consumer communication |

## 4. Mock A: model and transform a warehouse, 45 minutes

**Prompt:** a multi-tenant commerce source provides mutable orders and effective-dated customer changes. Build a trustworthy daily paid-billing dataset and explain how it changes over time.

| Minutes | Work | What to defend |
| --- | --- | --- |
| 0–5 | Clarify sources and consumers | Grain, keys, dates, amount meaning and freshness |
| 5–15 | Model facts and dimensions | Current state versus event grain, unknowns and historical joins |
| 15–24 | Define ingestion and CDC | Identity, version ordering, deletes and conflict policy |
| 24–33 | Organize transformation workflow | Dependencies, materializations, tests and documentation |
| 33–40 | Define metric consumption | Eligibility, missingness, additive behavior and revision |
| 40–45 | Accept a changed requirement | Explain which contracts and consumers need migration |

**Answer checkpoints:** tenant is part of identity; a current-state order is not every CDC version; effective and receipt time differ; snapshots cannot recover arbitrary unseen states; the billing measure is explicitly scoped rather than called recognized revenue.

## 5. Mock B: repair an incorrect incremental refresh, 45 minutes

**Prompt:** a daily report misses a late order, a deleted order reappears and the checkpoint advanced during a failed refresh. Explain an investigation and a safe repair.

| Minutes | Work | What to defend |
| --- | --- | --- |
| 0–7 | Reproduce the report | Source bounds, definition, run identity and last-good state |
| 7–17 | Diagnose capture and ordering | Event-date filters, source versions and tombstones |
| 17–27 | Plan affected recomputation | Old/new partitions, late dimensions and empty replacements |
| 27–35 | Design validation/publication | Independent reconciliation and atomic effects/progress |
| 35–41 | Plan backfill and operation | Isolation, ownership, consumer status and recovery |
| 41–45 | State verification limits | What was tested and which production guarantees remain unproved |

**Answer checkpoints:** inspect source evidence before choosing a cause; do not advance consumer progress beyond committed effects; old partitions can need clearing; replay requires retained evidence; the local exception rollback is not a distributed durability test.

Both mocks are authored practice formats. Different valid architectures are welcome when their source, history, metric and recovery contracts are explicit.

## 6. Review rubric

Look for a consistent row grain, scoped identities, appropriate historical mapping, valid change capture, explicit admission policy, complete affected-set reasoning, meaningful tests and a coherent publication boundary. Require an explanation of what remains unknown about sources and production behavior.

Do not grade an answer by the number of vendor names. A simpler design with clear replay and consumer semantics is easier to assess than an unexplained list of tools. Keep one error example, the incorrect assumption and the evidence that repairs it.

## 7. Seven-day revision route

| Day | Work | Produce |
| --- | --- | --- |
| 1 | A1 and L01–L04 | Layer, source and publication contracts |
| 2 | A2 and L05–L08 | Fact/dimension model with historical join and fan-out explanation |
| 3 | A3/A4 and L09–L16 | CDC identity map and transformation dependency plan |
| 4 | A5 and L17–L20 | Old/new partition trace and lookback counterexample |
| 5 | A6 and L21–L24 | Failed-publication repair and consumer-status note |
| 6 | A7/A8 and L25–L32 | Metric contract and production-shaped architecture |
| 7 | Both mocks and targeted correction | Revised answers for missed assumptions |

The schedule is an editorial sequence, not a measured learning-time claim. Manual solving, diagramming and mock feedback remain learner work.

## 8. Exit checklist

- [ ] I can state every layer's grain and admission policy.
- [ ] I can distinguish delivery, source version and business identity.
- [ ] I can model historical dimensions and expose unknown members.
- [ ] I can explain corrections, deletes, conflicts and replay.
- [ ] I can describe dbt dependencies, materializations, tests and contracts.
- [ ] I can trace late facts and old/new affected partitions.
- [ ] I can explain an empty replacement partition and a backfill scope.
- [ ] I can connect quality gates to a last-good publication boundary.
- [ ] I can distinguish freshness, completeness and semantic validity.
- [ ] I can define a metric's valid aggregation and revision behavior.
- [ ] I can discuss security, performance and production limits honestly.
- [ ] I have attempted both mocks and revised a design after new evidence.

The handbook is fully authored. Return to the [roadmap](/docs/analytics-engineering), [SQL practice](/docs/sql-interview), [pipeline architecture](/docs/system-design/analytics-event-pipeline) or [product casebook](/docs/product-casebook) for targeted practice.
