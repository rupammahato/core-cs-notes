# Analytics Engineering and Warehousing — Part 7: Quality, Observability and Publication

**A6: a successful computation is not automatically a publishable dataset.**

## 1. Place checks at meaningful boundaries

| Boundary | Example assertion | Failure response to define |
| --- | --- | --- |
| Envelope/source | Supported schema, immutable delivery identity | Reject batch or route to an explicit error workflow |
| Staging | Required fields, valid types and known source codes | Quarantine or stop affected consumers |
| Dimensions/facts | Scoped unique keys, valid references, nonoverlapping intervals | Block candidate publication |
| Metrics | Count/amount reconciliation and eligibility | Withhold incorrect results |
| Consumer | Definition, freshness and allowed access | Display status, preserve last-good or fail clearly |

A count can be a warning or a critical gate depending on the consumer contract. Unknown members and conflicting source entities remain visible warnings in this lesson. That policy is not universally suitable for financial, safety-sensitive or completeness-dependent reporting.

## 2. The eight executed candidate checks

The lab checks duplicate fact keys, negative bills, missing dimension references, invalid dimension intervals, overlapping intervals, duplicate dimension keys, paid-count reconciliation and known-amount reconciliation.

Uniqueness and not-null checks address different failures. Relationship checks must preserve the composite tenant scope. Reconciliation must use matching eligibility, currency and source coverage. Equal totals can still hide offsetting errors, so row/key-level references and targeted counterexamples are valuable.

The independent Python oracle compares complete admitted facts, dimension periods and mart rows at each main stage, rather than accepting a green local check as its own reference answer.

## 3. Publication is a state transition

```text
raw batch accepted and committed
  -> candidate built for a frozen prefix
  -> critical checks pass
  -> write immutable mart version and current model state
  -> commit active pointer and cursor in the same transaction
```

If publication fails, raw evidence remains while the successful checkpoint does not move. Retrying can recompute the same intended input. A failed candidate must not replace a last-good reader result merely because an intermediate SQL statement succeeded.

L22 injects an exception after model replacement inside the transaction. It verifies rollback of the pointer, cursor, facts and candidate manifest. These are local SQLite exception/transaction observations. They do not prove behavior under process kill, storage failure, concurrent clients or distributed orchestration.

## 4. Semantic failure and repair

A negative billed amount is structurally supported by the raw payload but violates this order-billing fact's semantic rule. Publication is rejected. A later valid source version repairs the candidate while the raw record remains inspectable.

An unsupported schema version instead rejects the entire ingestion batch. Structural and semantic admission deliberately differ. A production design should record failed-run metadata, alerts, ownership and repair state durably; this lesson retains proof outputs but does not implement an operational incident-management service.

## 5. Observability has several axes

- Source capture: expected files/partitions, extraction coverage and connector lag.
- Receipt progress: local offsets, oldest pending input and input rejection.
- Semantic quality: unknown dimensions, conflicts, violating rows and reconciliation.
- Publication freshness: age and source bounds of the last successful consumer version.
- Consumption: definition versions, access failures and unexpected metric changes.

Sequence distance is not wall-clock lag. A caught-up cursor cannot detect a producer that silently stopped sending records. A fresh dataset can still be incomplete or wrong. Use source control totals and domain reconciliation alongside technical freshness.

## 6. Handle failure without erasing evidence

Keep the last-good publication with a visible freshness/status limitation where the consumer contract permits it. For consumers that cannot tolerate stale data, fail explicitly. Avoid silently displaying old values as current.

Record which assertion failed, candidate/source bounds, affected consumers, owner and safe replay procedure. Decide whether a warning needs escalation or a threshold change; do not relax a failed critical check simply to make the run green.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L21. Distinguish quality gates from warnings

Inspect a successful run's test counts and separate quarantine warning.

**Worked explanation:** The eight configured critical candidate checks pass. One ambiguous entity is still quarantined and is explicitly outside admitted metrics. Whether that warning is acceptable is a product/data-owner policy; this lesson allows it while exposing the coverage limitation.

Run `python examples/analytics-engineering/lab.py L21`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "failed_row_counts": {
    "duplicate_fact_keys": 0,
    "negative_bills": 0,
    "missing_dimension_references": 0,
    "invalid_dimension_intervals": 0,
    "overlapping_dimension_intervals": 0,
    "duplicate_dimension_keys": 0,
    "paid_count_reconciliation": 0,
    "known_amount_reconciliation": 0
  },
  "all_eight_gates_passed": true,
  "quarantine_is_separate_warning": 1
}
```

**Common trap:** A green critical gate does not mean every source entity is included or all business questions are resolved.

**Interview follow-up:** Which warning thresholds should block your actual consumer's publication?

### L22. Fail after replacement but before commit

Inspect state before and after an injected publication exception.

**Worked explanation:** The second batch is already accepted in raw. Candidate fact/dimension replacement, versioned mart insertion, checkpoint and active pointer are in one SQLite transaction. An injected Python exception rolls that publication transaction back; retry can use the retained raw input.

Run `python examples/analytics-engineering/lab.py L22`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "injected_error": "Injected failure after candidate replacement, before pointer/checkpoint commit",
  "before": {
    "singleton": 1,
    "committed_seq": 14,
    "active_run": "run1"
  },
  "after": {
    "singleton": 1,
    "committed_seq": 14,
    "active_run": "run1"
  },
  "raw_upper_seq": 20,
  "last_good_rows_unchanged": true
}
```

**Common trap:** This is a tested exception/rollback boundary, not a process-kill, power-loss or concurrent-reader experiment.

**Interview follow-up:** How would a cloud engine's transaction and table-swap boundaries alter the publication design?

### L23. Block a semantic error while preserving raw evidence

Inspect the negative-amount candidate and the unchanged active publication.

**Worked explanation:** A structurally accepted higher version lands in raw, but its negative bill fails the semantic gate. The old publication remains active. A subsequent higher, valid source version is tested as a repair, without pretending the bad source payload never existed.

Run `python examples/analytics-engineering/lab.py L23`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "failure_counts": {
    "duplicate_dimension_keys": 0,
    "duplicate_fact_keys": 0,
    "invalid_dimension_intervals": 0,
    "known_amount_reconciliation": 0,
    "missing_dimension_references": 0,
    "negative_bills": 1,
    "overlapping_dimension_intervals": 0,
    "paid_count_reconciliation": 0
  },
  "active_publication_unchanged": true,
  "raw_contains_rejected_candidate": true
}
```

**Common trap:** Structural ingestion success and semantic fitness for a business mart are different contracts.

**Interview follow-up:** When should invalid data be rejected at intake, quarantined, corrected upstream or block the entire publish?

### L24. Reject an unsupported schema atomically

Inspect a batch with one otherwise valid delivery followed by schema version two.

**Worked explanation:** The envelope contract accepts only the lesson's schema version one. The whole ingestion batch rolls back when version two is encountered, so the earlier row in that batch does not land partially. This is separate from the semantic-error handling illustrated by negative billing.

Run `python examples/analytics-engineering/lab.py L24`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "unsupported_schema_version": 2,
  "raw_upper_before": 27,
  "raw_upper_after": 27,
  "partial_valid_delivery_present": 0
}
```

**Common trap:** Tolerating additive fields in a supported schema does not imply accepting every new schema version.

**Interview follow-up:** What producer/consumer compatibility plan would permit the new version deliberately?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. Is a passing data test proof of correct business meaning?
No. It proves the tested assertion on that dataset under its implementation. Definitions and source completeness require additional evidence.

### Q2. Why not advance the cursor after raw ingestion?
Raw acceptance and successful analytical publication differ. The publication checkpoint must reflect the input whose consumer effects are successfully committed.

### Q3. What remains after the injected failure?
The accepted second raw batch, the previous active mart and its successful cursor. Failed candidate changes are rolled back.

### Q4. Is a warning always safe to ignore?
No. Its acceptable threshold depends on impact and consumer requirements. The lesson's quarantine policy is explicitly scoped.

### Q5. Why compare full rows with an independent oracle?
Local reconciliation can miss shared implementation errors or offsetting mistakes. A separately implemented reference strengthens the scoped verification.

### Q6. What is freshness versus completeness?
Freshness concerns relevant time/progress; completeness concerns required coverage. One can hold while the other fails.

### Q7. Does a retry repair the source data?
Not by itself. It re-executes under the source and transformation contract; a persistent semantic error can fail repeatedly until resolved.

### Q8. What is not covered by the rollback test?
Power-loss durability, process recovery, concurrent-reader behavior and distributed transaction boundaries are outside the executed claim.

## Practice tasks

1. Categorize the eight executed checks by identity, relationship, temporal and metric concerns.
2. Explain the raw versus published cursor state after L22.
3. Write a consumer-facing stale-result policy for a failed daily refresh.
4. Name an upstream completeness problem that a zero local cursor gap would miss.

**Answer checkpoints:** raw reaches the next batch while publication stays at last-good; expose age/bounds; a producer can omit required records even when every received delivery has been processed.

- [ ] I can separate critical gates, warnings and source completeness.
- [ ] I can explain the tested publication transaction and its limits.

Continue with [Semantic Metrics and Consumption](/docs/analytics-engineering/semantic-metrics-and-consumption).
