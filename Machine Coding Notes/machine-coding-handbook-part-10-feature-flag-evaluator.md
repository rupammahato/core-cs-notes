# Machine Coding Practice — Part 10: Feature Flag Evaluator

**M8: stable cohorts require a stable hash input and an explicit configuration version policy.**

## 1. The problem and its purpose

Build an in-memory, tenant-scoped percentage rollout evaluator. Feature flags separate deploying a capability from enabling it for a cohort. A percentage rollout should give the same identity a stable decision under the same policy, rather than drawing a fresh random number on every request.

Clarify default behavior, tenant scope, identity, hashing, percentage endpoints, configuration retries and stale updates. Here undefined flags return false. Configurations are keyed by (tenant, flag), have a positive increasing version and an integer percentage in 0..100. Evaluation requires nonempty tenant, flag and user identifiers.

## 2. Version and cohort contract

| Update | Result |
| --- | --- |
| No prior config or higher version | Apply and return true |
| Same version and same percentage | Idempotent no-op, return false |
| Same version and different percentage | Reject version conflict |
| Lower version | Reject stale version |
| Invalid version/percentage | Reject before changing current config |

Construct the hash input by concatenating each component's decimal byte length, a colon and its exact bytes: tenant, flag, user in that order. Length prefixes prevent structural ambiguity such as concatenating ab+c versus a+bc. They do not prevent ordinary hash collisions.

Use 32-bit FNV-1a with unsigned wraparound, then bucket = hash % 10,000. Enable when bucket < percent × 100. Zero enables nobody; 100 enables every valid identity. Increasing percentage for the same tenant/flag/hash contract retains every previously enabled identity. Changing an identity, flag key or hash contract can reshuffle membership.

The algorithm and constants are documented in [RFC 9923, FNV Basics and Constants](https://www.rfc-editor.org/rfc/rfc9923.html#section-2). It is an Informational independent-stream RFC, not an Internet Standard. FNV is non-cryptographic; this evaluator is not an authorization or security boundary. Modulo reduction also does not promise an exactly sized cohort or an exactly unbiased sample.

## 3. Implementation reasoning

Keep configuration mutation separate from pure cohort computation. Validate an entire update before replacing its stored value. Evaluation reads only the configuration matching both tenant and flag; another tenant's policy is irrelevant even when the flag name matches.

The configuration invariants are positive versions, percentages within 0..100, and one value per accepted tenant/flag/version. Accepted replacement versions increase; identical retries preserve state. Evaluation is read-only and cannot create a configuration.

Do not use an implementation-dependent `std::hash` contract for cross-language stable cohorts. A specified byte encoding, fixed algorithm and width let clients reproduce the decision. The CLI's printable-ASCII scope makes byte length unambiguous; a multilingual version would need a fixed text encoding contract.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
class FeatureFlags {
    struct Config { Number version, percent; };
    std::map<std::pair<std::string, std::string>, Config> configs_;
public:
    static Number bucket(const std::string& tenant, const std::string& flag, const std::string& user) {
        // Length-prefix every component so (ab,c) cannot collide merely by concatenation with (a,bc).
        std::string input;
        for (const auto& value : {tenant, flag, user}) input += std::to_string(value.size()) + ':' + value;
        std::uint32_t hash = 2166136261u;
        for (unsigned char c : input) { hash ^= c; hash *= 16777619u; }
        return static_cast<Number>(hash % 10000u);
    }
    bool update(const std::string& tenant, const std::string& flag, Number version, Number percent) {
        identifier(tenant); identifier(flag); require(version > 0, "invalid version");
        require(percent >= 0 && percent <= 100, "invalid percentage");
        auto key = std::make_pair(tenant, flag); auto it = configs_.find(key);
        if (it != configs_.end()) {
            require(version >= it->second.version, "stale version");
            if (version == it->second.version) {
                require(percent == it->second.percent, "version conflict"); return false;
            }
        }
        configs_[key] = {version, percent}; return true;
    }
    bool enabled(const std::string& tenant, const std::string& flag, const std::string& user) const {
        identifier(tenant); identifier(flag); identifier(user);
        auto it = configs_.find({tenant, flag});
        return it != configs_.end() && bucket(tenant, flag, user) < it->second.percent * 100;
    }
};
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T29. Undefined flags fail closed; percentage endpoints are exact

**Worked explanation:** No config means disabled. A zero-percent policy enables nobody and a hundred-percent policy enables every valid identity.

Run `python examples/machine-coding/verify.py --trace T29` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
EVAL t new user
{"ok":true,"result":false}
UPDATE t new 1 0
{"ok":true,"result":true}
EVAL t new user
{"ok":true,"result":false}
UPDATE t new 2 100
{"ok":true,"result":true}
EVAL t new user
{"ok":true,"result":true}
```

**Common trap:** A <= threshold comparison accidentally enables one bucket at zero percent.

**Interview follow-up:** When might a non-security feature need a configurable default?

### T30. Retries and conflicting versions differ

**Worked explanation:** An identical version and value is an idempotent no-op. The same version with a different percentage is a conflict; lower versions are stale.

Run `python examples/machine-coding/verify.py --trace T30` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
UPDATE t f 4 100
{"ok":true,"result":true}
UPDATE t f 4 100
{"ok":true,"result":false}
UPDATE t f 4 0
{"ok":false,"error":"version conflict"}
UPDATE t f 3 0
{"ok":false,"error":"stale version"}
EVAL t f u
{"ok":true,"result":true}
```

**Common trap:** Accepting stale updates can undo an emergency disable.

**Interview follow-up:** Can timestamps replace an authoritative version under clock skew?

### T31. Tenant configurations stay separate

**Worked explanation:** The configuration key includes tenant and flag. Disabling a flag in one tenant cannot overwrite the policy for another tenant.

Run `python examples/machine-coding/verify.py --trace T31` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
UPDATE alpha f 1 100
{"ok":true,"result":true}
UPDATE beta f 1 0
{"ok":true,"result":true}
EVAL alpha f u
{"ok":true,"result":true}
EVAL beta f u
{"ok":true,"result":false}
EVAL gamma f u
{"ok":true,"result":false}
```

**Common trap:** Keying only by flag name breaks tenant isolation.

**Interview follow-up:** Who is allowed to write tenant configuration?

### T32. Invalid policy changes preserve the last valid policy

**Worked explanation:** Percentage and version validation happen before replacement. A failed update leaves evaluation on the last valid zero-percent policy.

Run `python examples/machine-coding/verify.py --trace T32` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
UPDATE t f 1 0
{"ok":true,"result":true}
UPDATE t f 2 101
{"ok":false,"error":"invalid percentage"}
UPDATE t f 0 50
{"ok":false,"error":"invalid version"}
EVAL t f u
{"ok":true,"result":false}
UPDATE t f 2 100
{"ok":true,"result":true}
EVAL t f u
{"ok":true,"result":true}
```

**Common trap:** Clamping an invalid percentage hides bad configuration input.

**Interview follow-up:** What should a remote client do when a configuration stream disconnects?

<!-- END TRACES -->

## 6. Complexity and verification

For F configured tenant/flag pairs and an encoded identity of length L, evaluation uses O(log F) map comparisons plus O(L) hashing and O(L) temporary input storage, ignoring string comparison details. Updates use O(log F) comparisons plus copied key storage. Configurations are retained until object destruction; there is no eviction or delete operation.

The reference tests compare deterministic bucket calculations, version histories, tenant separation, percentage endpoints and 200 identities across five increasing percentages. The latter is a finite monotonicity test, not a statistical claim that each rollout enables precisely its nominal percentage.

## 7. Architecture follow-up

A remote configuration system needs authenticated writers, an authoritative version source, distribution, caching, last-known-good policy and observability. An emergency disable has a propagation delay; “local evaluation is fast” does not mean every client sees the latest update.

Distinguish rollout from experimentation. Stable assignment alone does not establish randomization quality, exposure logging, metric validity or a causal estimate. Also distinguish enabling a feature from authorizing access to protected data. Bridge to [secure observable operations](/docs/system-design/secure-observable-operations) and [experiments](/docs/probability-statistics/hypothesis-tests-and-experiments).

## 8. Interview questions with answers

### Q1. Why hash rather than generate a random number per call?

Hashing a stable identity gives repeatable membership under a fixed policy. Fresh randomness could make a user alternate between old and new behavior on consecutive requests.

### Q2. Why include tenant and flag in the input?

They scope the cohort as well as the configuration. The same user can receive different stable buckets for different flags or tenants; independence of those buckets is not formally proved here.

### Q3. Why length-prefix fields?

Unseparated concatenation can encode different tuples as identical byte strings. Length prefixes make tuple boundaries recoverable, though the finite hash still has ordinary collisions.

### Q4. Why is duplicate version with a different value rejected?

An authoritative version should identify one policy. Silently accepting two values under that identity makes replicas' meaning depend on arrival order and obscures configuration conflicts.

### Q5. Can percentage increases remove existing users?

With the same key, identity encoding and hash, raising only the threshold cannot remove a bucket that was already below the old threshold. Changing the hash inputs or algorithm can.

### Q6. Does a 10% rollout enable exactly 10% of a small user set?

No. It selects buckets below a threshold. The realized fraction depends on the user identities, finite sample and hash distribution; it is not a quota allocator.

### Q7. Can this replace authorization?

No. A flag controls product behavior. Authentication and permission checks must still protect resources, and a non-cryptographic hash must not be treated as an access token.

### Q8. What should happen during a configuration outage?

Choose last-known-good or a specified default according to the capability's risk and availability needs. Record staleness and provide an override path; no one default is correct for every flag.

## 9. Practice tasks

- [ ] Add an explicit salt/version to the hash contract. Show which changes preserve cohorts and which intentionally reshuffle them.
- [ ] Return an evaluation explanation containing config version, bucket and reason. Decide which fields are safe to expose to end users.
- [ ] Add a remote-config adapter with last-known-good data. Test stale delivery, reconnect and an emergency disable without using wall-clock sleeps in the model.
- [ ] Design an experiment exposure event. Specify assignment unit, first exposure, deduplication and metric joins; explain why rollout alone is insufficient.

Next: [Consolidation and Mocks](/docs/machine-coding/consolidation-and-mocks).
