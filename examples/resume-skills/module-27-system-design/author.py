"""Assemble the canonical chapter with exact executable sources and observed output."""
from pathlib import Path
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE / 'verification-results.json').read_text(encoding='utf-8'))
source_names = ['capacity.mjs', 'ring.mjs', 'pool.mjs', 'proxy.mjs', 'cache-model.mjs']

def code(name):
    return '```js\n' + (BASE / name).read_text(encoding='utf-8') + '```'

def output(name):
    return '```json\n' + json.dumps(proof['observations'][name], ensure_ascii=False, indent=2) + '\n```'

chapter = r'''# Resume Skills Placement Handbook — Part 29
# Module 27: System-Design Bridge Through Your Load Balancer

**Estimated time: 5–6 hours | Tier: 2 | Requires: DSA hashing/searching, CN HTTP/TCP, M4/M6 and M13–M19**

---

## Why this module exists

“I built a load balancer” invites questions about what is being balanced, how a destination is chosen, what happens during failure, and how the measurements support the resume bullet. A good answer connects a small implementation to the wider system: clients, authentication, application state, databases, deployment, capacity and observability.

This chapter starts from your consistent-hashing project and builds a separate runnable learning fixture. It then extends the reasoning to stateless application servers and cache placement. The questions are selected interview fundamentals and useful follow-ups; no company-frequency ranking was measured.

**Organizing principle: state the invariant, trace one request, and distinguish placement, capacity and correctness.**

---

## 1. What system design means in this project

System design explains how components cooperate to satisfy a workload and its correctness requirements. An architecture diagram is a useful starting point, but it must explain the behavior at each boundary. “Add a cache and load balancer” leaves unanswered which data is cached, who owns it, when it becomes stale, and whether another server can safely handle the next request.

For this exercise, the functional requirement is: receive an authenticated request, derive a routing key, select an eligible configured backend, forward a bounded body, and return its result. When the preferred server becomes unavailable, select another eligible server. While draining a server, stop assigning new work while allowing admitted work to finish.

The invariants are more precise:

- A client cannot choose an arbitrary upstream URL or impersonate another tenant using a header.
- Identical tenant/key/configuration inputs produce the same primary owner.
- An unhealthy or draining member receives no newly selected application work.
- An ambiguous write is not automatically repeated by this proxy.
- Admission slots and backend counters are released after completion or cancellation.
- Ring membership changes and health eligibility changes remain distinguishable.

These statements can be tested. “Highly scalable” cannot be tested until the workload, resource budget, acceptable latency and error rate are defined.

Before discussing implementation, ask whether requests are reads or writes, whether sessions require local state, how much response data moves, and what failure clients may observe. The fixture forwards synthetic requests; it does not implement business authorization, a payment ledger or durable distributed state.

---

## 2. What was executed and what the resumes report

The example uses **Node.js {{NODE}}**, ES modules and the Node standard library on **{{OS}}**. It has no third-party runtime dependencies. Run it from the repository root:

```powershell
Set-Location examples/resume-skills/module-27-system-design
npm run verify
```

**95 actual local checks passed:** 21 ring-placement checks, 17 pool-policy checks, eight capacity-arithmetic checks, 11 in-process cache-model checks and 38 real HTTP checks. The HTTP fixture starts three backend servers and two proxy servers on owned ephemeral loopback ports. It exercises actual forwarding, readiness responses, transport failure, draining, admission, cancellation and deadline expiry, then closes every listener and destroys its agents.

The ring/capacity/cache checks have different evidence boundaries. Ring experiments compute deterministic ownership over 10,000 distinct keys. Capacity is arithmetic over stated assumptions. Cache behavior is a controlled in-memory model. Neither arithmetic nor a simulated shard establishes production throughput, durability or distributed consistency.

The two resume PDFs were rechecked for the project claims:

| Resume statement | What this chapter can establish |
| --- | --- |
| 19.66% remapping on failure | The resume reports this value; this fixture separately measures 19.83% of a different fixed key corpus |
| About 80% movement with naive routing | This fixture's explicit modulo comparator moves 79.65%; that does not reproduce the original experiment |
| 2,046 requests/s | Reported project result; no throughput benchmark is reproduced here |
| Three failed health checks before rerouting | This fixture independently exercises that chosen threshold with real readiness responses |
| Proxy latency 2,459 → 1.6 ms, errors 3.7% → 0 | Reported in the product resume; the original benchmark, latency definition and bottleneck fix were not independently reviewed here |

The original project repository and raw benchmark logs were not reviewed in this chapter. Treat those resume metrics as reported claims until their workload, commands and raw evidence are available. Do not substitute this learning fixture's results for the original project's results.

---

## 3. Requirements, SLOs and the first architecture

An interview design can begin with a tenant-scoped placement-notes API. Users read notes and submit edits. Ordinary reads should remain fast; edits must preserve ownership and revision checks. Background indexing can lag, provided the API accepts only current permitted evidence as discussed in M23–M26.

State a proposed objective explicitly: for example, “For admitted ordinary reads, target p95 below 200 ms over a stated measurement window, with a defined availability target.” This is an illustrative requirement, not a result of the fixture. Define the window, eligible routes, client location, and treatment of overload responses before evaluating it.

```text
Client
  -> TLS edge / reverse proxy
  -> admission + routing
  -> application server A, B or C
       -> canonical database
       -> optional shared cache
       -> durable jobs -> indexing workers -> derived search stores
```

Start with one application codebase and a canonical database. Multiple processes may run the same code. You do not need separate microservices for authentication, notes and revision checks merely because there are separate boxes in a diagram. Split services when independent ownership, scaling, deployment or fault isolation justifies the added network and consistency work.

Separate functional requirements from operational targets. “An edit cannot overwrite a newer revision” is a correctness rule. “The request normally completes within 200 ms” is a latency target. A cache can help the second while breaking the first if freshness validation is omitted.

---

## 4. Capacity: translate assumptions into units

Assume 100,000 daily active users, 20 requests per user per day, a peak multiplier of ten, a mean service time of 120 ms, and a 20 KiB response. Assume an independently measured backend capacity would be 80 requests/s, then plan to operate at 70% of that assumed value. The example deliberately labels 80 requests/s as an assumption.

```text
daily requests       = users × requests/user/day
average requests/s   = daily requests / 86,400
peak requests/s      = average × peak multiplier
mean requests active ≈ arrival rate × mean time in system
target per backend   = assumed backend capacity × utilization target
healthy backends     = ceil(peak / target per backend)
```

The in-flight relation uses steady average flow with a consistent system boundary. It does not mean peak QPS multiplied by p99 latency predicts a p99 queue length. Include queueing if the measured time includes queueing; keep arrival and completion definitions consistent when requests are rejected or abandoned.

{{CAPACITY_SOURCE}}

{{CAPACITY_OUTPUT}}

The scenario gives about 231.48 peak requests/s, 27.78 average requests in the system at that flow/time assumption, five healthy backends, and six total if one may fail while leaving five. That last statement assumes similar capacity, adequate surviving resources, useful distribution and no shared bottleneck. A single hot key can invalidate the effective distribution assumption.

The calculated response bandwidth is about 4.74 MB/s of payload at the assumed peak, before protocol overhead, retries, uploads or replication. State MB versus MiB. Storage planning separately needs object count, bytes per object, retention, indexes, replicas and growth. Backends also have CPU, memory, file-descriptor, connection-pool and dependency limits. Six API processes sharing an exhausted database pool do not create six times the useful capacity.

---

## 5. Stateless servers, affinity and session state

A stateless application server can handle a request using its input and authoritative external state without requiring a previous request to have reached that particular process. It can still use temporary local caches, connection pools and request-local variables. Those are optimizations or execution resources, not the only durable home for a user's session or note.

If a login session exists only in server A's memory, routing the next request to B can lose it. Sticky sessions can mask the problem during normal operation, but A's failure still loses that local state. Store authoritative sessions externally or use appropriately verified tokens with the revocation/expiry trade-offs from M7. Keep authorization at the application boundary as well.

Affinity can be useful for local cache reuse or connection-oriented workloads. It is a routing preference, not a durability mechanism. “Same user, same server” requires a stable key and a stable placement configuration. Health fallback, membership changes, key changes and configuration skew can move the request.

In this example, a public demonstration credential maps to a tenant. A validated `x-route-key` chooses affinity within that namespace. This is not real identity verification, and the key is not permission to read an object. In a real notes API, the application must check the authenticated user's access to the requested note even when the proxy selected the expected server.

---

## 6. Reverse proxy, load balancer, API gateway and BFF

| Component | Main responsibility | Example decision |
| --- | --- | --- |
| Reverse proxy | Accept a client connection and forward to an upstream | TLS termination or fixed upstream routing |
| Load balancer | Distribute work among eligible destinations | Round robin, least active requests, key affinity |
| API gateway | Apply common API boundary policies | Authentication integration, quotas, API routing |
| Backend for frontend | Adapt responses/workflows for a particular client | Aggregate a mobile dashboard |

A single product can perform several roles. Explain the responsibility instead of assuming the label guarantees a feature.

At layer 4, routing commonly operates on transport connections and addresses/ports. At layer 7, an HTTP-aware component can inspect the request method, path and headers. TLS termination determines where plaintext becomes visible and which hop needs encryption. HTTP/2 multiplexing and long-lived connections complicate the assumption that one connection equals one request or equal work.

The fixture is a small HTTP/1.x layer-7 proxy. It does not demonstrate TLS, HTTP/2, WebSockets, streaming, public exposure or a complete gateway. M17 contains separate Nginx/TLS material. Nginx's official guide documents several routing methods; product/edition capabilities must be checked rather than inferred from the generic phrase “load balancer.” [NGINX HTTP load balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/).

---

## 7. Choose a routing policy from the workload

| Policy | Mechanism | Useful when | Main limitation |
| --- | --- | --- | --- |
| Round robin | Rotate through eligible servers | Requests and servers are roughly similar | Ignores actual request cost and affinity |
| Weighted routing | Give larger servers more selections | Capacities differ predictably | Weights can become stale |
| Least connections | Prefer fewer open upstream connections | Connection occupancy approximates work | Keep-alive/multiplexing can mislead |
| Least in-flight requests | Prefer fewer active requests | Active request count approximates work | Count does not measure CPU or remaining duration |
| Key hashing | Derive destination from a stable key | Affinity or shard ownership matters | Hot keys and topology changes need treatment |

The pool below verifies round robin, least in-flight and consistent-hash selection. Only the hash strategy is exercised through the real proxy in this fixture. The other two have deterministic policy tests; no performance comparison between policies is claimed.

An application server pool and a cache shard pool have different correctness requirements. A stateless API server can ask the database for the same object regardless of which server received the request. A cache shard contains only its local entries; selecting a different shard may miss. A database shard may be the only authoritative owner, so “try another healthy server” is unsafe unless that server has a suitable replica and ownership authority.

Routing by client IP can collapse many users behind a NAT into one key. Routing by path can collapse every `/search` call into one destination. Routing by object ID can help cache locality while creating hot objects. Choose the key for the intended ownership/affinity goal and observe its distribution.

---

## 8. Consistent hashing: trace the actual algorithm

Modulo routing is easy: choose `hash(key) % memberCount`, then index a stable member list. Changing the divisor changes many destinations. A consistent-hash ring instead places keys and server tokens in the same ordered space. The owner is the first token clockwise at or beyond the key hash, wrapping to the beginning if necessary.

```text
hash(key) -> first token >= hash(key) -> physical backend ID
                   no token remains? -> first token in ring
```

The implementation hashes canonical strings with SHA-256 and takes the first unsigned 64 bits. Each physical member receives 128 virtual tokens derived from its stable ID and token number. Token ordering has explicit tie-breakers. The backend ID is independent of the ephemeral listening port.

{{RING_SOURCE}}

With R total tokens, building the sorted ring costs O(R log R) time and O(R) space. A primary lookup uses O(log R) binary search. `candidates()` then walks tokens until it finds each distinct physical member, so its worst-case work includes O(R) scanning. The pool also performs small linear member searches. Do not describe the complete fallback implementation as O(log R).

On removal, keys formerly owned by the removed member move to the next surviving token. Other keys retain their primary. On addition, the new member takes ownership of the intervals preceding its new tokens. This chapter's invariant checks prove those properties for its fixed corpus and implementation. The original consistent-hashing paper provides the underlying placement idea; exact results depend on the chosen ring and workload. [Karger et al., consistent hashing](https://people.csail.mit.edu/karger/Papers/web.pdf).

---

## 9. Virtual nodes, replicas, weights and versions

A virtual node is another token assigned to the same physical server. It spreads that server's ownership across several intervals. It is not another machine, process, database copy or durable replica. Giving a server more tokens can approximate a larger ownership weight, but the ratio is statistical and should be checked against actual keys and traffic.

One token per server can create uneven intervals. More tokens reduce variation for many ordinary key distributions, at the cost of a larger ring and more configuration work. They cannot split a single key's requests across servers while preserving single-owner affinity. The hot-key experiment below demonstrates that limitation directly.

Every proxy replica must agree on member identities, hash function, key encoding, token count, weights and tie-breaking. `JSON.stringify([tenant, key])` avoids ambiguity such as joining unescaped fields with `:`. A changed encoding is a placement change even if the physical machines remain the same.

The ring version hashes placement configuration. It helps debug whether replicas have the same placement view. It does not include origin URLs, health observations, draining state or a full deployment revision. Changing an origin while retaining an ID can preserve placement but still require a separately versioned and validated destination configuration.

Hash collisions remain possible in a finite space. The fixture deterministically orders equal token positions; it does not claim cryptographic collision impossibility or that every other ring implementation uses the same convention.

---

## 10. Read the remapping result and its denominator

{{RING_OUTPUT}}

The removal experiment starts with five members and 10,000 distinct, equally weighted keys, then removes `c`. Of all original keys, 1,983 change primary: **19.83%**. Those are exactly the keys originally owned by `c`. Among keys originally owned by `c`, the movement fraction is 100%. State which denominator is being used.

The comparator uses `hash(key) % 5` against `[a,b,c,d,e]`, then `hash(key) % 4` against `[a,b,d,e]`. It moves 7,965 keys: **79.65%**. This result belongs to that defined comparator; arbitrary “naive routing” implementations need not have the same behavior. Adding `f` to the ring moves 17.34% of this corpus, all to `f`.

The five-member, 128-token ring has counts from 1,923 to 2,193. One token gives a much less even distribution on these inputs. The coefficient of variation is standard deviation divided by mean across member counts; it describes this population of counts, not a universal balance guarantee.

Now give `hot-document` 9,000 of 10,000 requests and distribute only the remaining 1,000 requests across ordinary keys. Its owner `c` receives 9,195 requests. Key ownership can be reasonably even while request load is severely uneven. If `c` fails, traffic-weighted movement in that hot workload is very different from 19.83%.

For resume evidence, record the exact keys, hash, token count, initial/final memberships, comparator and weights. A failure experiment also needs to distinguish temporary health fallback from permanent membership removal. The proxy keeps its configured ring during failure and selects the next eligible candidate; the separate placement experiment constructs a new ring after removal.

---

## 11. Health checks and the eligible pool

Active checks deliberately probe readiness. Passive checks observe application request outcomes. A process can be alive while unable to serve useful work; readiness should reflect the dependencies needed for the operation without creating a check so expensive that it becomes another failure source. Nginx distinguishes passive checks from active-check features, with edition-specific capabilities. [NGINX health checks](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-health-check/).

{{POOL_SOURCE}}

This fixture begins with members eligible, marks a member unavailable after three consecutive negative observations, and restores it after two positive observations. A success resets the failure streak; a failure resets the recovery streak. The proxy and manually invoked readiness probes share this small observation model. A production design may separate passive circuit state from readiness-probe state so successful unrelated traffic does not mask a failing readiness check.

The verifier calls `probeOnce()` explicitly, using actual HTTP `/ready` responses. No background probe scheduler, jittered interval, cross-replica consensus or production failure detector is tested. A production scheduler also needs bounded probe concurrency and cleanup at shutdown.

Three failures do not mean “failure detected in three seconds.” The delay depends on probe interval, timeout, phase, scheduling and which observations count. Hysteresis reduces rapid down/up oscillation but trades faster reaction against false positives. Failures can be network problems or overload, not necessarily a dead process.

If every member is unavailable, this fixture returns 503. That is an explicit fail-closed routing policy. AWS documents that an Application Load Balancer can route to all unhealthy targets when all targets are unhealthy; this provider-specific behavior must not be generalized to this code. [AWS ALB target health behavior](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html).

---

## 12. Trace the real proxy implementation

The flow is: validate the demonstration identity and fixed route; validate affinity; reserve an admission slot; buffer a bounded body; choose an eligible backend; increment its active count; issue one upstream request; collect a bounded response; release resources once.

{{PROXY_SOURCE}}

The explicit header allowlist forwards only selected content metadata and an internally derived tenant. It drops the public demonstration credential, client-supplied identity and arbitrary connection-nominated fields. Recomputed content length matches the buffered payload. In a real proxy, define the complete protocol/header policy deliberately and handle response headers needed by the application. This limited fixture does not preserve cookies, redirects, caching headers or the full behavior of a general-purpose reverse proxy.

Destinations come from trusted fixed configuration restricted to loopback in this exercise. The incoming URL cannot nominate another host. Debug response headers expose backend, primary and placement version for local verification; they are not a public administration API.

Node's HTTP API exposes request/server lifecycle and agent controls. This implementation owns a keep-alive agent and explicitly destroys it at cleanup. Its timer covers body buffering, upstream socket acquisition and response buffering after the request handler begins; header receipt before that handler has separate server limits. The socket timeout APIs do not themselves substitute for this deadline-and-abort policy. [Node.js v22.14.0 HTTP API](https://nodejs.org/download/release/v22.14.0/docs/api/http.html).

Bodies are buffered, not streamed: at most 1 KiB is retained for the incoming body and 4 KiB for the response. Oversized incoming bodies are discarded until their end and then rejected. A production edge must also bound connections, header sizes, upload time and work spent draining rejected bodies. This fixture's admission counter is not a complete slow-client defense.

---

## 13. Deadlines, overload and ambiguous writes

{{HTTP_OUTPUT}}

Four held requests occupy the fixture's four admission slots. A fifth is rejected with 503; no application queue is created. This proves the configured local bound, not fairness between tenants or a whole-deployment limit. Three proxy replicas with independent limits can admit three times as much work unless another shared limit is used.

The timeout test configures a 50 ms deadline against a synthetic 400 ms backend delay and observes 504. It does not claim timers fire at exactly 50 ms under every event-loop load. The proxy destroys the upstream request after sending the deadline response. Client cancellation also releases admission and aborts upstream transport, but neither action proves the upstream business operation rolled back.

The write test increments the backend mutation counter, then destroys the socket before acknowledging success. The proxy returns 502 after one upstream attempt. The counter is one: the operation happened even though the client received no successful reply. Retrying that write without a durable idempotency design could apply it twice.

For safe retries, define eligible operations, an overall deadline, an attempt limit and a single retry owner. Use backoff/jitter when appropriate and avoid multiplying retries across layers. An idempotency key needs a durable, correctly scoped record of the business result, not just a transient proxy map. These choices follow the failure modes discussed by AWS and HTTP's semantics; the fixture intentionally has no automatic retries. [AWS timeouts/retries/backoff](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter), [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html).

Status alone does not decide retry safety. A GET can still trigger a poorly designed server side effect, and an idempotent method can carry application constraints. A 502 after a dropped acknowledgement is not evidence that the original write did nothing.

---

## 14. Draining, membership changes and multiple proxies

Draining changes eligibility for new work. It does not erase a member from the ring or terminate an admitted request. The test holds a request on `a`, drains `a`, sends the same affinity key to `c`, releases the held request, and verifies the original finishes on `a` with its active count returning to zero.

A production rollout can mark an instance unready/draining, allow existing work a bounded grace period, stop accepting new connections/work as appropriate, then terminate. Define what happens to requests exceeding the grace period. Long-lived connections and protocol upgrades need separate treatment; the fixture does not implement them.

Permanent membership change is another operation. Publish a validated configuration with an epoch, stable IDs and origins; make replacement atomic within a process; monitor which proxies adopted it. During skew, two proxies can route the same key differently. An ownership-sensitive data store may require coordinated migration, forwarding or a read/write transition protocol. A stateless API pool usually tolerates the skew better because both servers consult authoritative shared state.

Keep control-plane mutations authenticated and auditable. Do not accept an upstream list, health override or ring rewrite from arbitrary application headers. The fixture modifies drain/health state directly in its test process; there is no exposed administrative endpoint.

Multiple load balancers remove one process as the sole routing point only if clients can reach healthy replicas through a suitable front door. DNS caching, edge routing, independent failure domains and configuration distribution then become part of the design. The real fixture uses one proxy per test scenario; high availability of the load-balancer tier is conceptual here.

---

## 15. Consistent hashing for a cache: ownership is not replication

Cache placement asks where to look for a value. Replication asks where additional valid copies live. Consistency asks which value may be returned after writes or failures. The ring solves only the placement part unless additional mechanisms are implemented.

{{CACHE_SOURCE}}

{{CACHE_OUTPUT}}

This model checks canonical in-memory revision/deletion state on every access. It demonstrates a cold load, warm hit, TTL expiry exactly at the boundary, revision rejection, tenant namespaces and deletion acceptance. When a new member owns `key-3`, that shard starts cold; the old shard's copy still exists. Changing a ring does not migrate bytes, delete old entries or coordinate distributed ownership.

Consulting the source on every hit can defeat the latency/load-saving purpose of a remote cache. A real system must choose and justify its coherence mechanism: versioned keys with a reliable current-version source, durable invalidation events plus reconciliation, write-through, or explicitly bounded staleness. TTL alone allows a stale window and does not establish immediate deletion or permission revocation.

For disposable cache data, a miss can reload from the database. For authoritative data, a new owner cannot simply start empty. You need replication, recovery, migration and failure authority. Clockwise fallback is a candidate order, not proof that a candidate holds a durable replica or may accept writes.

Mitigate a cache stampede with bounded single-flight work, expiry jitter, prewarming and admission controls suited to the data policy. A hot key may use read replicas, local caching or application-specific decomposition, but each changes freshness or ownership assumptions. Those are architectural extensions, not verified features of this model.

---

## 16. Grow the system by identifying the bottleneck

If CPU-heavy parsing blocks one Node event loop, adding keep-alive does not remove the CPU work. If the database is slow, adding API replicas can exhaust its connection budget faster. If a shared proxy is saturated, more backends may remain idle behind it. Measure the constrained resource before choosing the next component.

```text
Stage 1: one app + database; correct queries and authorization
Stage 2: several stateless app replicas + redundant routing tier
Stage 3: bounded shared caching and durable background work
Stage 4: read replicas / partitioning only for a demonstrated data bottleneck
```

These are possible development stages, not a rule that every project must reach stage four. Read replicas bring lag. Partitioning brings cross-partition queries and rebalancing. Queues bring retries, duplicate delivery and backlogs. Service splitting brings network failures and coordinated changes.

For a payment-like write, preserve its transaction/idempotency invariant rather than failing over to an arbitrary empty process-local ledger. For a read-only cached note, a database fallback may be acceptable if bounded and authorized. Requirements decide which failure response is correct.

CAP reasoning applies when a network partition prevents replicas from communicating and a replicated operation must choose between strong consistency and serving every request under that partition. It is not a slogan that an application always “chooses two,” nor does adding a hash ring establish either consistency or partition tolerance. State the replicated data, requested guarantee and failure scenario.

Tail latency deserves separate attention when one request fans out to many dependencies. The slowest required branch can dominate completion. Limit fan-out and propagate useful deadline budgets; measure the distribution rather than assuming a fast average proves a fast tail. [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/).

---

## 17. Observe the system and defend the benchmark

Useful signals include admitted/completed/rejected requests, status/error counts, active work, upstream attempts, timeout/cancellation counts, health transitions, placement/configuration version and per-backend latency. Break down traffic by route class and backend without using unbounded user/document IDs as metric labels. Logs/traces can carry suitably protected request IDs for detailed debugging.

Distinguish arrival rate, achieved completion rate, successful goodput and retries. If a load generator stops sending while waiting for slow replies, it can underrepresent the offered workload and tail impact. Choose an explicit arrival model, record generator capacity and include error/time-out results. A high requests/s value with unacceptable failure rate is not the same capacity claim as successful traffic meeting a latency objective.

For the resume's 2,046 requests/s, recover these details before confidently defending the number:

- Hardware, OS/runtime versions, process counts and whether client/proxy/backends share a host.
- Exact command, concurrency/arrival rate, warm-up, duration and repeated-run results.
- Route, payload/response size, key distribution, connection reuse and backend work.
- Successful completions, errors, timeouts, p50/p95/p99 latency and generator limitations.
- Direct and proxied runs under equivalent conditions, plus CPU/event-loop/connection observations.

For 2,459 → 1.6 ms, first establish whether each number is mean, percentile, one sample, or a mixed load phase. Keep units and measurement boundaries consistent. Check connection setup/reuse, proxy buffering, logging, event-loop stalls, upstream response completion and resource saturation as hypotheses. Do not assert which fix caused the resume result without the original code/logs.

“Zero observed errors” means zero in the recorded sample; it is not a universal zero-error guarantee. Likewise, 19.66% key movement is not an automatic 19.66% latency improvement or traffic redistribution. The current chapter's 95 checks verify selected mechanisms; they do not constitute a sustained load benchmark.

---

## 18. Connect this bridge to the architecture companion

The root files `Architecture-System-Design-Notes-Plan.md` and `Architecture-System-Design-Question-Bank.md` describe the broader track. M27 develops one bridge; it does not mark all planned architecture chapters complete.

| Companion area | Connection from this chapter |
| --- | --- |
| A0: design method and estimates | Workload, units, SLOs, capacity assumptions and request trace |
| A1: application boundaries | Stateless processes, modular baseline, control/data plane |
| A2: data/cache/scaling | Placement, hot keys, cache coherence, replica versus shard |
| A3: reliability/concurrency | Admission, deadlines, ambiguous writes, draining and health |
| A4: secure operation | Trusted identity, fixed destinations, observability and rollout |
| S10: load balancing/distributed cache | Extend this fixture into a full worked design with explicit data semantics |

Use question-bank Q02/Q03 for capacity, Q08/Q09 for proxy roles/statelessness, Q35 for placement, Q49 for failed/rejoining cache servers and Q53 for your resume project. Other worked designs—booking, payments, chat, notifications, RAG and SaaS—need their own correctness rules and implementations. M28 next connects the relevant modules to project/experience explanations and available evidence.

---

## 19. Interview questions and answers

{{QUESTIONS}}

---

## 20. Practice tasks

1. Write functional requirements, one latency objective and five correctness invariants for a notes API. Trace one authorized read and one versioned edit through every component.
2. Change the capacity assumptions to 250,000 users, 12 requests/day and a 15× peak. Show units, surviving capacity after one failure, and why p99 cannot replace mean time in the average in-flight calculation.
3. Implement a documented weighted policy and compare it with round robin and least in-flight on controlled uneven work. Separate policy correctness from throughput evidence.
4. Change the ring to seven members and several virtual-node counts. Save the exact key corpus/configurations, removal/addition numerators and per-member distribution instead of targeting a preferred percentage.
5. Give one tenant or document 90% of requests. Compare distinct-key movement with traffic-weighted movement and design a hot-key mitigation with explicit freshness trade-offs.
6. Add a bounded probe scheduler with jitter, separate passive/readiness counters and graceful shutdown. Test probe timeout, flapping, false positives and recovery without leaking listeners/timers.
7. Extend the HTTP fixture with an oversized upstream response and a slow client body. Verify which limits reject each case and whether sockets/resources are eventually reclaimed.
8. Implement a durable idempotent write in a database-backed upstream. Drop the acknowledgement after commit, retry with the same key, and verify one business effect plus a repeatable stored result.
9. Simulate two proxies on different membership epochs and a cache-node rejoin. Explain cold misses, stale copies, migration and canonical read acceptance without claiming the ring replicates data.
10. Recover the original project benchmark commands/logs and produce equivalent direct/proxied runs with throughput, successful goodput, latency percentiles, errors and resource observations. Keep reported resume metrics separate until reproduced.

---

## 21. Revision checklist

- [ ] I can start a design with workload, invariants and a concrete request trace.
- [ ] I can calculate QPS, bandwidth and average in-flight work with explicit units.
- [ ] I can explain stateless servers, session storage and the limits of affinity.
- [ ] I can distinguish reverse proxy, load balancer, API gateway and BFF responsibilities.
- [ ] I can choose round robin, least in-flight or hashing from a workload.
- [ ] I can trace ring lookup, wrapping, virtual tokens and fallback complexity.
- [ ] I can distinguish virtual nodes, physical replicas, key balance and hot traffic.
- [ ] I can report remapping with its exact numerator, denominator and comparator.
- [ ] I can explain active/passive checks, hysteresis and all-unhealthy policy.
- [ ] I can reason about admission, deadlines, cancellation and ambiguous writes.
- [ ] I can design draining, versioned configuration and multi-proxy rollout behavior.
- [ ] I can defend cache freshness and resume metrics with evidence boundaries.

---

## 22. Primary sources and verification artifacts

Version-sensitive sources were checked on **16 October 2026**. The executable runtime is Node.js {{NODE}}; current product documentation is not a claim that this fixture implements every documented feature.

| Topic | Primary reference |
| --- | --- |
| Original placement idea | [Consistent hashing and random trees, Karger et al.](https://people.csail.mit.edu/karger/Papers/web.pdf) |
| HTTP load balancing | [NGINX routing methods](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) |
| Health policy | [NGINX health checks](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-health-check/), [AWS ALB target health](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html) |
| HTTP lifecycle | [Node.js v22.14.0 HTTP](https://nodejs.org/download/release/v22.14.0/docs/api/http.html) |
| Retry semantics | [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), [AWS timeouts, retries and jitter](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter) |
| Latency distribution | [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/) |

Artifacts are under `examples/resume-skills/module-27-system-design/`: five exact teaching sources embedded above, the real HTTP backend/client fixture, `verify.mjs`, `verification-results.json`, `cleanup-results.json`, `resume-claims.json`, dependency scope, content validation and build/route/search evidence. Every check is named in the verification report. These artifacts establish the learning fixture's behavior, not independent reproduction of the original project.

**Next: [M28: Resume project and experience deep-dives](/docs/resume-skills/resume-project-experience-deep-dives).** Connect the stack and architecture mechanisms to your own contribution, data/request flows, choices, failure cases and defensible metrics.
'''

questions = [
('What does a load balancer actually do?', 'It chooses an eligible destination for a connection or request and forwards work according to a policy. Explain its layer, health rules, admission limits and failure behavior. It does not by itself make application state durable or transactions correct.'),
('Why add a load balancer instead of just a larger server?', 'It can distribute work and route around unavailable instances, allowing horizontal application capacity and rolling maintenance. It adds another component to operate. A larger server may be sufficient for a small workload; either choice still needs dependency and correctness analysis.'),
('How do you estimate the number of application servers?', 'Estimate peak useful traffic, measure representative per-instance capacity at the target latency/error budget, reserve headroom, and round up. Include failure reserve and verify that the database, network and hot-key distribution support the resulting fleet. This chapter assumes capacity; it does not measure it.'),
('What is a stateless backend?', 'A process that can serve a request without depending on that user having reached the same process earlier. Authoritative state lives in suitable external stores or validated request credentials. Local caches and connection pools can still exist, provided losing them does not lose required business state.'),
('Do sticky sessions solve session availability?', 'They can keep normal requests on the same server, but the local session can still disappear when that server fails or is replaced. Use external session state or an appropriate token design, and explain revocation, expiry and security trade-offs.'),
('Round robin or least connections?', 'Round robin fits roughly similar work and capacity. Least connections uses occupancy as a heuristic, which may help with uneven connection durations but can be misleading with idle keep-alive or multiplexed traffic. Least in-flight is another heuristic; none directly measures remaining CPU work.'),
('Why does modulo hashing move so many keys?', 'Changing the member count changes the divisor for every key. In the explicit five-to-four comparator here, 79.65% of the fixed corpus changes destination. That value depends on the algorithm, member ordering and inputs; it is not a theorem about every naive routing scheme.'),
('How does consistent hashing choose an owner?', 'Hash the key into the token space, binary-search the first token at or beyond it, and wrap if needed. Map that token to its physical member. Stable key encoding, member IDs, hash and token configuration are part of the contract.'),
('What is the lookup complexity?', 'The primary lookup in this sorted ring is O(log R) for R tokens. Constructing the ring costs O(R log R). Finding distinct fallback candidates scans tokens and can cost O(R), with additional small member searches in this pool. State which operation is being analyzed.'),
('What are virtual nodes?', 'Several token positions assigned to one physical member. They spread ownership across intervals and can improve aggregate key distribution or approximate weights. They do not create extra machines or replicated data copies.'),
('Does consistent hashing guarantee equal load?', 'No. It seeks stable placement and can improve ordinary key distribution with suitable tokens. Unequal key popularity, object size, request cost or server capacity can create severe imbalance. One hot key still has one primary owner in this design.'),
('Why does removing a member move about one fifth here?', 'Five members with reasonably even ownership give the removed member roughly one fifth of equally weighted keys. The measured share here is 1,983/10,000. All those removed-owner keys move, while keys owned by surviving members retain their primary.'),
('How would you explain the resume’s 19.66%?', 'First state what moved and the denominator: distinct keys, requests or bytes. Then provide the original corpus, ring settings, removed member, comparator and measurement commands. The resume reports 19.66%; the separate fixture here measures 19.83% and must not replace the original evidence.'),
('How is traffic-weighted movement different?', 'Weight each moved key by its observed request volume and divide by total request volume. Equal-key movement counts each key once. A failed owner holding one very popular key can move most traffic even when it owns a modest fraction of distinct keys.'),
('What happens when the primary backend fails?', 'This proxy retains the configured ring but skips ineligible members in clockwise candidate order. It sends new work to an eligible fallback or returns 503 if none exists. That fallback can serve stateless API work; it is not automatically a valid authoritative data replica.'),
('Active versus passive health checks?', 'Active checks send dedicated probes; passive checks observe real request failures. Both have false-positive and detection-delay trade-offs. Explain which endpoint/status counts, thresholds, timeouts and recovery rules apply; the fixture manually invokes active probes and also records selected request outcomes.'),
('Why require multiple failures and successes?', 'Consecutive-observation thresholds add hysteresis, reducing rapid flapping. Larger thresholds can delay failure detection or recovery. The chosen three-failure/two-success policy is a fixture choice; its elapsed time depends on probe timing and observation rules.'),
('What if all servers are unhealthy?', 'Choose and document a policy. This proxy fails closed with 503. Some managed products have fail-open behavior in particular all-unhealthy cases. Do not assume the same behavior across implementations, and consider the correctness/security consequences of serving degraded work.'),
('What is graceful draining?', 'Exclude a member from new selections while allowing admitted requests a bounded opportunity to finish. Then terminate after completion or a documented grace deadline. It differs from permanent membership removal and needs special handling for long-lived streams/connections.'),
('What if two proxies have different rings?', 'The same key can reach different owners. Track configuration epochs/versions, publish validated configurations and monitor adoption. Stateless API requests may tolerate this; cache/database ownership can need migration, forwarding or coordinated write authority during the transition.'),
('Is a ring version enough to identify deployment state?', 'No. This version covers placement inputs. Origins, health/draining observations, application version and broader destination configuration are separate. Include the relevant revisions in diagnostics without pretending one short placement digest describes the entire system.'),
('Why use admission control?', 'It limits work accepted into constrained resources and avoids an unbounded queue turning overload into extreme latency. The fixture admits four requests per proxy and rejects overflow. A real design also needs fairness, dependency budgets, connection limits and a clear client response policy.'),
('Is a socket timeout an end-to-end deadline?', 'No. Define the stages and total budget explicitly, including any queues, uploads, connection acquisition and response work. The fixture starts an absolute timer inside the request handler and uses separate header/request server limits. Cancellation must propagate where possible.'),
('Can a proxy retry a failed POST?', 'A dropped acknowledgement can occur after the operation committed. Retry only with appropriate semantics and a durable idempotency design, bounded attempts and a deadline. The fixture returns 502 after one attempt and proves the synthetic mutation already occurred.'),
('Does aborting an upstream request undo its write?', 'No. Closing transport can stop waiting or some ongoing work but is not a business rollback guarantee. Use transactional state and reconciliation/idempotency for ambiguous outcomes. The client must not infer that timeout or cancellation means no effect.'),
('Does consistent hashing replicate cache data?', 'No. It chooses where a key should be placed or looked up. Replication, migration, repair and freshness require separate mechanisms. The in-memory model leaves an old shard copy and loads the new owner cold after membership changes.'),
('Is TTL enough for authorization or deletion correctness?', 'TTL permits an interval before expiry and does not automatically revoke access or remove every derived copy. Define freshness/permission acceptance at the authoritative boundary and coordinate invalidation or versioning. This controlled model checks canonical memory on every read, which is not a remote-cache coherence solution.'),
('How would you handle a hot key?', 'Measure its traffic/cost, then consider suitable local caching, read replicas, request coalescing, dedicated capacity or a domain-specific split. Each option changes freshness, failure or affinity behavior. More virtual tokens alone cannot split one key’s requests in a single-owner ring.'),
('How do you defend 2,046 requests/s and the latency improvement?', 'Show the original workload, environment, generator command, connection settings, errors and latency percentiles, then compare direct/proxied traffic under equivalent conditions. Explain the observed bottleneck with logs/profiles and the actual change. This chapter does not reproduce either resume benchmark or establish its cause.'),
('How would you present the complete design in an interview?', 'Start with workload, SLOs and invariants. Draw the minimal request/data flow, choose state placement and routing, calculate capacity, then walk through failure, ambiguous write, overload, draining and growth. Separate implemented evidence from proposed extensions and use the resume project to ground concrete decisions.'),
]
chapter = chapter.replace('{{QUESTIONS}}', '\n\n'.join(f'### Q{i}. {q}\n\n{a}' for i, (q, a) in enumerate(questions, 1)))
for token, name in [('CAPACITY', 'capacity'), ('RING', 'ring'), ('POOL', 'pool'), ('PROXY', 'proxy'), ('CACHE', 'cache-model')]:
    chapter = chapter.replace('{{' + token + '_SOURCE}}', code(name + '.mjs'))
for token, name in [('CAPACITY', 'capacity'), ('RING', 'ring'), ('HTTP', 'http'), ('CACHE', 'cache')]:
    chapter = chapter.replace('{{' + token + '_OUTPUT}}', output(name))
chapter = chapter.replace('{{NODE}}', proof['node']).replace('{{OS}}', proof['os'])
assert not re.search(r'\{\{[A-Z_]+\}\}', chapter)
filename = 'resume-skills-handbook-part-29-module-27-system-design-load-balancer.md'
(ROOT / 'Resume Skills Notes' / filename).write_text(chapter, encoding='utf-8')
content = {'chapter': filename, 'words': len(chapter.split()), 'lines': chapter.count('\n'), 'interview_questions': 30, 'practice_tasks': 10, 'unchecked_learning_items': 12, 'source_fidelity': source_names}
(BASE / 'content-validation.json').write_text(json.dumps(content, indent=2) + '\n', encoding='utf-8')
print(json.dumps(content, indent=2))
