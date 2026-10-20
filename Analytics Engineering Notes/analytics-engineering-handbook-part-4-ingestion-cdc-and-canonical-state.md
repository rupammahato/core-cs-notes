# Analytics Engineering and Warehousing — Part 4: Ingestion, CDC and Canonical State

**A3: delivery progress and source truth need different identities and ordering rules.**

## 1. Capture choices and their contracts

| Pattern | Useful property | Main correctness questions |
| --- | --- | --- |
| Full extract | Rebuild from an authoritative snapshot | Snapshot consistency, deletes, cost and source impact |
| Timestamp polling | Bound source changes with an update field | Ties, precision, clock semantics, corrections and delete capture |
| Log-based CDC | Observe database changes through a connector | Snapshot/log boundary, ordering, offsets, retention and schema changes |
| Application events/outbox | Capture explicit business events | Transactional intent, identity, replay and consumer effects |

A real CDC connector has source-specific metadata and recovery behavior. Debezium's PostgreSQL connector documents row-change events, source log position and delete/tombstone behavior. The lab's integer source_version and D payload are a simplified teaching contract, not a Debezium envelope or WAL reader. [Debezium PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html).

## 2. Three identities in this lesson

```text
Delivery identity: delivery_id
Version identity: stream + tenant + entity + source_version
Current business identity: stream + tenant + entity
```

Replaying the same delivery with the same content inserts nothing. Reusing its delivery identity with changed content rejects the ingestion batch. A new delivery of the same business version collapses if the payload matches. A contradictory payload under that version quarantines the entity.

Canonical JSON serialization makes key order irrelevant to the lesson's payload comparison. Added or changed payload content under the same version is still a conflict. Producers must assign a new source version for a legitimate changed record under this contract.

## 3. Latest state is not an additive event ledger

An upsert at a higher source version replaces current order state. A delete at a higher source version removes the order from current facts. Retaining source versions/tombstones prevents an older upsert delivered later from winning.

The latest admitted version is selected by source_version, not receipt sequence or business date. A delete payload retains fields in this fixture, but a real connector can represent deletes differently. Never assume a missing record in a partial extract proves deletion.

## 4. Conflicts need a resolution policy

The lesson withholds an entire entity if any version identity within the known bounded raw prefix has multiple payloads. It intentionally does not choose an arbitrary first writer or silently revert to an older state. A late conflict can retract a previously admitted entity in a new publication.

This policy is conservative and can exclude useful data indefinitely. A real design needs authority to resolve the contradiction, explicit resolution records and downstream restatement. Simply appending a higher version does not remove the older conflict under the implemented rule.

Full-snapshot conflict evaluation describes what this run knows. It is not a claim to reconstruct historical observer knowledge about conflicts, implement aliases or manage every correction/retraction workflow.

## 5. Structural admission versus semantic quality

Raw ingestion enforces the supplied envelope and supported schema version, and commits its batch atomically. Some structurally valid source data can still be unsuitable for the mart. The lesson deliberately lands a negative bill so a later semantic gate can reject publication and preserve the source evidence.

Whether to reject, quarantine or stop a feed depends on the data contract and consequences. Do not automatically treat negative amounts as invalid in every domain: refunds or signed ledger entries can be legitimate in a differently defined fact.

## 6. Snapshot and replay boundaries

A consistent initial snapshot and subsequent change log need a connector-specific handoff that avoids gaps and duplication. A cursor must mean more than “latest date I saw.” Source retention, recovery offsets, source epochs and reconciliation determine whether a missed range can be replayed.

The lab has one owned append log and a frozen local upper sequence. It tests arrival-order independence under the supplied per-entity versions. It does not implement distributed source-partition offsets or concurrent ingestion during publication.

<!-- BEGIN WAREHOUSE LAB -->

## Worked warehouse traces

### L09. Distinguish retries from conflicting versions

Inspect repeated source-version identities and their distinct payload counts.

**Worked explanation:** A retry can use another delivery identity while reporting the same business version and payload. That collapses to one source version. Two different payloads under one version create an unresolved contradiction. The grouping is scoped by stream, tenant, entity and source version.

Run `python examples/analytics-engineering/lab.py L09`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "stream": "orders",
    "tenant_id": "t1",
    "entity_id": "bad",
    "source_version": 1,
    "deliveries": 2,
    "payloads": 2
  },
  {
    "stream": "orders",
    "tenant_id": "t1",
    "entity_id": "o1",
    "source_version": 1,
    "deliveries": 2,
    "payloads": 1
  }
]
```

**Common trap:** Deduplicating only by delivery ID misses logical repeats, while deduplicating only by entity erases legitimate versions.

**Interview follow-up:** What source identity and ordering guarantees must a real connector expose?

### L10. Quarantine an ambiguous entity

Inspect the entity withheld because one version has conflicting payloads.

**Worked explanation:** This teaching policy holds the entire entity out of the admitted state when any version identity conflicts. It avoids silently falling back to a convenient older version. A separate test adds a late conflict and verifies that a previously published entity is retracted in a new publication.

Run `python examples/analytics-engineering/lab.py L10`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
[
  {
    "stream": "orders",
    "tenant_id": "t1",
    "entity_id": "bad"
  }
]
```

**Common trap:** The policy evaluates the known bounded snapshot; it is not a universal CDC correction, identity-resolution or bitemporal engine.

**Interview follow-up:** Who would resolve a conflict and how would the resolution become auditable source policy?

### L11. Apply a source-version correction

Compare order o1 before and after its higher-version amount correction.

**Worked explanation:** The second batch changes the latest admitted source version of t1/o1. The current fact and its historical daily partition are rebuilt. A correction is replacement of current business state under this contract, not another additive paid order.

Run `python examples/analytics-engineering/lab.py L11`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "initial_order_o1": [
    {
      "tenant_id": "t1",
      "order_id": "o1",
      "customer_id": "c1",
      "customer_sk": "2:c1:2026-10-01",
      "order_day": "2026-10-02",
      "billed_cents": 1000,
      "status": "paid",
      "source_version": 1,
      "plan": "free"
    }
  ],
  "corrected_order_o1": [
    {
      "tenant_id": "t1",
      "order_id": "o1",
      "customer_id": "c1",
      "customer_sk": "2:c1:2026-10-01",
      "order_day": "2026-10-02",
      "billed_cents": 1200,
      "status": "paid",
      "source_version": 2,
      "plan": "free"
    }
  ]
}
```

**Common trap:** Appending every CDC update to a transaction metric counts versions as transactions.

**Interview follow-up:** When should the warehouse preserve transaction events as a separate event-grain fact?

### L12. Do not resurrect a tombstoned order

After batch three, inspect stale upserts and the deleted order's current fact count.

**Worked explanation:** Source version two for o2 is a delete. An older version-one upsert delivered later cannot win merely because its local ingest sequence is larger. The retained tombstone version in raw supplies the ordering fence, even though deleted orders are absent from the current fact table.

Run `python examples/analytics-engineering/lab.py L12`. The runner executes and closes the full isolated lesson, then prints this selected trace.

**Verified output** (six-decimal display; raw values are in observations.json):

```json
{
  "stale_deliveries": [
    {
      "delivery_id": "o1-old-again",
      "entity_id": "o1",
      "source_version": 1
    },
    {
      "delivery_id": "o2-old-again",
      "entity_id": "o2",
      "source_version": 1
    }
  ],
  "o2_current_fact_count": 0
}
```

**Common trap:** Ordering business truth solely by receipt time can resurrect deleted state.

**Interview follow-up:** What retention boundary must be defined before old deletes or source versions can be discarded?

<!-- END WAREHOUSE LAB -->

## Interview Q&A

### Q1. Is CDC automatically exactly once?
No. Source capture, delivery, sink effects and checkpoint publication have distinct boundaries. Specify the identities and atomic effects you actually guarantee.

### Q2. Why separate delivery and version IDs?
One logical source version can be delivered repeatedly, while one business entity legitimately has many source versions.

### Q3. Why not choose the latest receipt?
Receipt order can contain stale versions. The source's valid ordering contract decides which business state wins.

### Q4. Why retain tombstones or version fences?
Without retained delete/order evidence, a late older upsert can resurrect deleted state.

### Q5. Can an update timestamp miss changes?
Yes. Ties, precision, delete absence, source semantics and backdated corrections can defeat a naive strict timestamp filter.

### Q6. What happens to conflicts here?
The entire scoped entity is withheld under a visible conservative policy. A real system needs an authoritative resolution mechanism.

### Q7. Does raw mean unchecked?
No. Raw admission still needs structural, ownership, safety and retention contracts. Semantic suitability can be checked in later layers.

### Q8. What makes replay safe?
Stable source identity/version semantics, retained evidence and effects/checkpoints that cannot diverge under the tested recovery model.

## Practice tasks

1. Trace all three identities for the repeated o1 payload.
2. Explain why the stale o2 upsert does not recreate a fact.
3. Describe the restatement caused by a late conflicting version identity.
4. Specify what a real initial-snapshot/CDC handoff must prove.

**Answer checkpoints:** delivery, version and entity scopes differ; source version fences stale arrivals; conflict resolution is outside the implemented policy; the source handoff needs an auditable gap/duplication recovery boundary.

- [ ] I can explain source identity, ordering, deletes and replay.
- [ ] I can distinguish the local contract from real connector guarantees.

Continue with [Transformations and dbt Workflows](/docs/analytics-engineering/transformations-and-dbt-workflows).
