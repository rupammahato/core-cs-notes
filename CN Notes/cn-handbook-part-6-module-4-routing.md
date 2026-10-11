# Computer Networks Placement Handbook — Part 6
# Module 4: Routing

**Module 4 · 4 hours · Tier 1/2 · Requires: M3 (prefixes, masks). Direct reuse of DSA Part 14 (graphs) and Part 17 (tries)**

---

## Why this module matters

M3 gave a packet an address. This module gets it to the other side of the world.

The interview questions are a short, stable list:

- **Distance vector vs link state**
- **What is count-to-infinity and how is it fixed?**
- **RIP vs OSPF vs BGP**
- **What is longest-prefix match?**
- **Forwarding vs routing**

And the written test adds **distance-vector convergence tables** and **Dijkstra runs**, both of which you have already done in DSA — this module is largely that material wearing a different hat, which is why it is cheaper than its four hours suggest.

The honest weighting: **routing is more heavily examined than it is interviewed.** A backend SDE is rarely asked about OSPF areas. But "how does a packet find its way" is a fair question at any level, and BGP comes up whenever an interviewer wants to talk about internet-scale systems.

The organising principle:

> **A router makes one decision, over and over: given a destination address, which neighbour do I hand this to? Everything in this module is either how that lookup is performed (longest-prefix match) or how the table it consults gets filled (routing protocols). And the protocols split on one question: do I tell my neighbours what I know about everyone, or do I tell everyone what I know about my neighbours?**

**How this module was verified.** The two routing algorithms are implemented independently and **cross-checked against each other**: Dijkstra (link state) and converged Bellman-Ford (distance vector) must agree on every shortest-path cost, and they did across **3,000 random graphs with 0 mismatches**. Longest-prefix match was checked against a brute-force reference on **20,000 random destinations, 0 mismatches**. The routing table is read live from this machine, and count-to-infinity is simulated until it actually reaches infinity.

---

## 4.1 Forwarding versus routing

Two words used loosely and distinguished sharply in interviews.

| | **Forwarding** | **Routing** |
|---|---|---|
| Question | "This packet is here — which port now?" | "What does the table *say*?" |
| Scope | One packet, one router, one lookup | The whole network, over time |
| Timescale | **Nanoseconds** — per packet | **Seconds to minutes** — per topology change |
| Implemented in | Hardware (the data plane) | Software (the control plane) |
| Data structure | The **forwarding table** (FIB) | The **routing table** (RIB), from which the FIB is derived |

> **The sentence:** *"Routing is the process of building the table; forwarding is the act of consulting it. One is a distributed algorithm running continuously; the other is a lookup that must happen at line rate."*

That split is also why **SDN** exists — it moves the control plane off the box entirely and leaves the switch doing nothing but forwarding.

---

## 4.2 The routing table, and longest-prefix match

### This machine's real table

```
  Network Destination        Netmask          Gateway       Interface  Metric
  0.0.0.0          0.0.0.0      10.105.73.2     10.105.73.61     25
  10.105.73.0    255.255.255.0         On-link      10.105.73.61    281
  10.105.73.61  255.255.255.255         On-link      10.105.73.61    281
  10.105.73.255  255.255.255.255         On-link      10.105.73.61    281
  127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
  127.0.0.1  255.255.255.255         On-link         127.0.0.1    331
  127.255.255.255  255.255.255.255         On-link         127.0.0.1    331
  224.0.0.0        240.0.0.0         On-link         127.0.0.1    331
  224.0.0.0        240.0.0.0         On-link      10.105.73.61    281
  255.255.255.255  255.255.255.255         On-link      10.105.73.61    281
```

Every row is `(destination prefix, next hop, outgoing interface, metric)`. Read a few:

- `0.0.0.0/0` → the **default route**, via the gateway `10.105.73.2`. Matches everything.
- `10.105.73.0/24` → "On-link": my own subnet, reachable directly with no router.
- `10.105.73.61/32` → a host route for **my own address**, so traffic to myself never leaves.
- `10.105.73.255/32` and `255.255.255.255/32` → the two broadcast forms from M3.
- `127.0.0.0/8` → loopback.

### The lookup rule

```
   among every row whose prefix CONTAINS the destination,
   choose the one with the LONGEST prefix.
   If several tie on length, break the tie by METRIC.
```

Verified on that real table:

```
  127.0.0.1          -> matches 127.0.0.1/32       (/32)  On-link      iface 127.0.0.1
  10.105.73.9        -> matches 10.105.73.0/24     (/24)  On-link      iface 10.105.73.61
  10.105.73.255      -> matches 10.105.73.255/32   (/32)  On-link      iface 10.105.73.61
  8.8.8.8            -> matches 0.0.0.0/0          (/0)   gateway 10.105.73.2
  224.0.0.251        -> matches 224.0.0.0/4        (/4)
  169.254.1.1        -> matches 0.0.0.0/0          (/0)   gateway 10.105.73.2
```

Note `127.0.0.1` matches **both** `127.0.0.0/8` and `127.0.0.1/32`, and the `/32` wins. And `8.8.8.8` matches only the default route, which is what "default" means: **`0.0.0.0/0` has prefix length 0, so it matches everything and always loses to anything else.** It is the last resort by construction, not by a special rule.

### The tie that longest-prefix match cannot break

The real table above has **two rows for `224.0.0.0/4`** — one via loopback with metric 331, one via the real interface with metric 281. Identical prefix length, so the lookup rule is silent:

```
    224.0.0.0  240.0.0.0  On-link  127.0.0.1     metric 331
    224.0.0.0  240.0.0.0  On-link  10.105.73.61  metric 281
  -> the tie-break is the METRIC: 281 < 331, so multicast goes out the
     real interface, not loopback. Longest prefix FIRST, then metric.
```

Worth knowing, because the textbook rule is usually stated as if ties cannot happen, and this machine has one sitting in its table.

### A synthetic table, to make the rule unmistakable

```
  destination        next hop     iface
  0.0.0.0/0          10.0.0.1     eth0
  10.0.0.0/8         direct       eth0
  10.1.0.0/16        10.0.0.2     eth1
  10.1.2.0/24        10.0.0.3     eth2
  10.1.2.128/25      10.0.0.4     eth3
  10.1.2.200/32      10.0.0.9     eth5

  10.1.2.200     -> 10.1.2.200/32      via 10.0.0.9     (eth5)
  10.1.2.150     -> 10.1.2.128/25      via 10.0.0.4     (eth3)
  10.1.2.5       -> 10.1.2.0/24        via 10.0.0.3     (eth2)
  10.1.9.9       -> 10.1.0.0/16        via 10.0.0.2     (eth1)
  10.9.9.9       -> 10.0.0.0/8         via direct       (eth0)
  172.16.0.1     -> 0.0.0.0/0          via 10.0.0.1     (eth0)
```

Six destinations, six different rows, each chosen purely by prefix length. `10.1.2.150` matches four rows — `/0`, `/8`, `/16`, `/24` and `/25` — and the `/25` wins.

**Why longest-prefix match exists:** it is what makes **aggregation** work (M3 §3.5). A provider can advertise one `/16` while a customer inside it advertises its own `/24`; both routes coexist, and the more specific one automatically wins for that customer's traffic. Without longest-prefix match, aggregation and exceptions could not both exist.

**And the DSA connection:** a forwarding table is a **trie over address bits** (DSA Part 17). You walk the destination's bits down the trie and remember the deepest node that held a route — which is literally longest-prefix match. Real hardware does it with a compressed trie or a TCAM that matches all prefixes in parallel in one clock cycle.

### What a router actually does per packet

```
 1. receive the frame, check the FCS, strip the Ethernet header
 2. verify the IP header checksum
 3. decrement TTL. If it hits 0: DROP and send ICMP Time Exceeded
 4. RECOMPUTE the header checksum (TTL changed)
 5. longest-prefix match on the destination -> next hop + interface
 6. ARP for the next hop's MAC (or use the cache)
 7. build a NEW Ethernet header: src = my MAC on that interface,
    dst = the next hop's MAC
 8. transmit
```

Step 7 is M0's central fact in operational form: **the IP addresses are untouched; both MAC addresses are replaced.**

---

## 4.3 Static versus dynamic routing

| | Static | Dynamic |
|---|---|---|
| Table built by | A human, by hand | A protocol, continuously |
| Adapts to a failure | **No** | **Yes** |
| CPU and bandwidth | None | Ongoing |
| Predictability | Total | Depends on convergence |
| Scales to | A handful of routes | Thousands |
| Right for | Stub networks, default routes, a host's own table | Anything with redundancy |

Almost every host uses static routing — your machine's table above is entirely static, with one default route. Dynamic routing is for routers with choices to make.

### Metrics

A protocol needs a notion of "better". What it counts shapes everything:

| Metric | Used by | Problem |
|---|---|---|
| **Hop count** | RIP | A 3-hop path over satellite beats a 4-hop fibre path. Bandwidth-blind |
| **Bandwidth** | OSPF (cost = reference ÷ bandwidth) | Ignores current load |
| **Delay, load, reliability, MTU** | IGRP/EIGRP (composite) | Complex, vendor-specific |
| **Policy** (AS path, preferences) | **BGP** | Not shortest-path at all — deliberately |

BGP is the odd one out and the reason is worth remembering: **between organisations, the cheapest path is a business question, not a graph question.** A network may prefer a longer path because it is a peer rather than a paid transit provider.

---

## 4.4 Distance vector

Each router knows only the cost to its **direct neighbours**, and periodically tells each neighbour its whole **distance vector** — its current best cost to every destination. This is **distributed Bellman-Ford**.

```
   D(x, y) = min over all neighbours v of  [ cost(x,v) + D(v, y) ]
```

### Verified convergence, round by round

Topology: `A–B 1, A–C 4, B–C 2, B–D 6, C–D 3`

```
   after round 0:                        (each node knows only its own links)
     node |       A       B       C       D
        A |       0     1/B     4/C     INF
        B |     1/A       0     2/C     6/D
        C |     4/A     2/B       0     3/D
        D |     INF     6/B     3/C       0

   after round 1:                        (one exchange with neighbours)
        A |       0     1/B     3/B     7/B     <- A learned C is closer via B
        B |     1/A       0     2/C     5/C     <- B learned D is closer via C
        C |     3/B     2/B       0     3/D
        D |     7/B     5/C     3/C       0

   after round 2:                        (converged)
        A |       0     1/B     3/B     6/B
        B |     1/A       0     2/C     5/C
        C |     3/B     2/B       0     3/D
        D |     6/C     5/C     3/C       0

  cross-check against Dijkstra from A: {'A': 0, 'B': 1, 'C': 3, 'D': 6}
```

Follow A's row. At round 0 it believes C costs 4 (its direct link) and D is unreachable. At round 1, B tells A that B reaches C for 2, so A revises to `1 + 2 = 3` **via B** — the direct 4-cost link to C is now unused. By round 2 it has D at 6. Three rounds to settle a four-node network, and the final costs match Dijkstra exactly.

Each cell is `cost/next hop`, and **the next hop is all that gets installed in the forwarding table.** A distance-vector router never knows the path, only the first step and the total — which is exactly the information that makes count-to-infinity possible.

### Count-to-infinity

`A — B — C`, both links cost 1. The `A–B` link fails. Verified, run until it terminates:

```
   step                | B -> A         | C -> A
   before failure      | 1 via A        | 2 via B
   A-B link fails      | INF            | 2 via B
   round 1             | 3 via C        | 4 via B
   round 2             | 5 via C        | 6 via B
   round 3             | 7 via C        | 8 via B
   round 4             | 9 via C        | 10 via B
   round 5             | 11 via C       | 12 via B
   round 6             | 13 via C       | 14 via B
   round 7             | 15 via C       | 16 via B
   round 8             | 16 via C       | 16 via B

   -> both finally reach INFINITY (16) after 8 rounds.
```

**The lie, stated plainly:** B asks C "how far to A?" and C answers **2** — without mentioning that **C's route to A goes through B.** So B believes 3, advertises 3, C believes 4, advertises 4, and the count climbs two per round until it hits infinity.

Two things make it inevitable:

1. **A router advertises a cost without saying which way it goes.** The whole problem is the missing path information.
2. **A router must follow its own next hop even when the news is worse.** C's route to A is via B, so when B's cost rises, C has no choice but to adopt it. That is correct behaviour, and it is what propagates the bad news slowly instead of discarding it.

**Why RIP's infinity is 16:** purely to bound this. With a maximum useful hop count of 15, the count can only climb 16 steps before everyone agrees a destination is gone. It is not a topology limit chosen for elegance; it is a timeout expressed in hops.

### The fixes, and their limits

```
  with SPLIT HORIZON (C never advertises its A route back to B):
   round 1 | B -> A = INF | C -> A = INF
   -> converged immediately. The loop never forms.
```

| Fix | Rule | Catches |
|---|---|---|
| **Split horizon** | Never advertise a route back to the neighbour you learned it from | Two-node loops |
| **Poison reverse** | Advertise it back **as infinity** — an explicit "do not use me for this" | Two-node loops, more robustly |
| **Triggered updates** | Send immediately on a change rather than waiting for the timer | Speeds convergence |
| **Hold-down timers** | Ignore new information about a route that just went down, briefly | Stops flapping |

Poison reverse is stronger than silence because silence is ambiguous — a missing route might just be a lost packet — whereas an explicit infinity is a positive statement.

**And the honest limitation:** none of these fixes loops of three or more routers. A→B→C→A can still form a transient loop during convergence, because each pair individually obeys split horizon. **That irreducible weakness is the real reason link state exists**, and saying so is a much better answer than listing the fixes.

---

## 4.5 Link state

Each router discovers its own links, floods that information to **everyone**, and then every router independently builds the **same complete map** and runs **Dijkstra** on it.

```
 1. discover neighbours and the cost to each (HELLO packets)
 2. build a LINK-STATE ADVERTISEMENT: "I am C, my links are B(2), A(5), D(1), E(6)"
 3. FLOOD it to every router in the area (not just neighbours)
 4. every router now holds an identical LINK-STATE DATABASE
 5. each runs DIJKSTRA on it, rooted at itself
 6. install the FIRST HOP of each shortest path
```

### Verified: Dijkstra step by step

```
  topology (every router learns ALL of this via flooded LSAs):
   A: B(2), C(5)
   B: A(2), C(2), D(3)
   C: A(5), B(2), D(1), E(6)
   D: B(3), C(1), E(2)
   E: C(6), D(2)

  Dijkstra from A -- the order nodes are finalised, with their cost:
   finalise A at cost 0
   finalise B at cost 2
   finalise C at cost 4
   finalise D at cost 5
   finalise E at cost 7

  resulting FORWARDING TABLE at A:
   destination   cost  full path         FIRST HOP
   B                2  A-B                       B
   C                4  A-B-C                     B
   D                5  A-B-D                     B
   E                7  A-B-D-E                   B
```

Two observations that are the point of the exercise:

1. **Every destination's first hop is B.** A's direct 5-cost link to C is never used, because `A→B→C` costs 4. The table is four rows all saying "send it to B", which is what a shortest-path tree rooted at A looks like.
2. **A router stores only the first hop, not the path.** The rest is recomputed by the next router from *its* database. Which means **consistency matters absolutely**: if two routers hold different databases, they can compute first hops that point at each other, and the packet loops. That is why flooding reliability and LSA sequence numbers are such a large part of OSPF.

### Verified: the two algorithms agree

```
  3,000 random graphs: Dijkstra vs converged distance-vector
                       shortest paths -> 0 mismatches
```

Two completely different algorithms — centralised Dijkstra on a full topology, and distributed Bellman-Ford exchanging vectors — computing the same shortest-path costs on 3,000 randomly generated graphs. That is the self-test, and it is stronger than checking either one against a textbook example, because each is an independent implementation of a different idea.

### Distance vector versus link state

```
                           | distance vector                       | link state
  what each router knows   | only its neighbours' distance vectors | the WHOLE topology
  algorithm                | Bellman-Ford, distributed             | Dijkstra, run locally
  what is exchanged        | a vector of distances                 | link-state advertisements
  exchanged with           | neighbours only                       | FLOODED to everyone in the area
  convergence              | slow, iterative                       | fast, once flooding completes
  count-to-infinity        | YES -- the central weakness           | no
  loops during convergence | likely                                | possible but brief
  memory                   | O(neighbours x destinations)          | O(whole topology)
  CPU                      | low                                   | higher (Dijkstra per change)
  message size             | small, sent often                     | larger, sent on change
  scales by                | hop count limit                       | AREAS / hierarchy
  example                  | RIP, IGRP                             | OSPF, IS-IS
```

**The one-line summary worth memorising:** *"Distance vector tells its neighbours what it knows about everyone; link state tells everyone what it knows about its neighbours."* That single inversion generates every row of the table.

---

## 4.6 The real protocols

### RIP — Routing Information Protocol

Distance vector, hop count, infinity = 16, full table broadcast every **30 seconds**, routes expire after 180 s. RIPv1 was classful; RIPv2 carries masks and supports CIDR.

Simple, and obsolete for good reasons: a 15-hop diameter limit, slow convergence, and bandwidth-blind metrics. Still worth knowing because it is the canonical distance-vector example and every count-to-infinity question is really a RIP question.

### OSPF — Open Shortest Path First

Link state, the standard interior protocol. Cost is derived from bandwidth (`reference / bandwidth`, so faster links cost less). Features worth naming:

- **Areas** — the network is split, with **area 0** (the backbone) joining them. Routers inside an area hold its full topology and only summaries of other areas, so Dijkstra's input stays bounded and flooding does not cross the whole network. **This is how link state scales**, and it is the answer to "doesn't every router needing the whole map prevent scaling?"
- **Router types**: internal, area border router (ABR), autonomous system boundary router (ASBR).
- **DR/BDR** on a broadcast segment, so `n` routers do not form `n(n−1)/2` adjacencies.
- **LSA types**, Hello/Dead intervals, and an adjacency state machine. Tier 3 — name them and move on.
- Runs directly over IP, protocol 89. Supports equal-cost multipath.

### BGP — Border Gateway Protocol

**The protocol that makes the internet one network**, and the one most worth understanding conceptually.

BGP is a **path-vector** protocol: it advertises not just a destination and a cost, but **the full list of autonomous systems the route passes through**. Three consequences:

1. **Loop detection is trivial and exact.** An AS that sees its own number in the path discards the route. No count-to-infinity, no hop limit, no timers — the path *is* the proof.
2. **Policy is expressible.** Because you can see the whole AS path, you can prefer or reject routes on business grounds, which is the entire point.
3. **It is not shortest-path.** BGP picks by local preference, then AS-path length, then a chain of further tie-breaks. A longer path through a settlement-free peer beats a shorter path through a paid transit provider, and that is *correct*.

| | IGP (RIP, OSPF, IS-IS) | EGP (BGP) |
|---|---|---|
| Scope | **Within** one autonomous system | **Between** autonomous systems |
| Goal | Find the shortest path | Enforce **policy** and reachability |
| Metric | Hops, bandwidth, delay | AS path, local preference, MED, communities |
| Trust | All routers are yours | **None** — the peer is a different company |
| Scale | Thousands of routes | **~1 million** routes in the global table |
| Transport | IP or UDP | **TCP port 179** — it needs reliability and incremental updates |

**Why BGP runs over TCP** is a good question to be ready for: the global table is about a million routes, so an advertisement must be reliable, ordered and **incremental** — send only the changes and keep the session alive with keepalives. Rebuilding a million routes from a periodic broadcast, RIP-style, is unthinkable.

**And why BGP is fragile**, which is the follow-up: it is built on trust. If an AS advertises a prefix it does not own, neighbours may believe it and traffic for that prefix is diverted — **BGP hijacking**. Mitigations (RPKI, route filtering, IRR) are bolted on, voluntary and incompletely deployed.

### Hierarchical routing

The underlying reason any of this scales. Without hierarchy every router would need an entry per network on Earth. With it:

- **Aggregation** (M3) lets one route stand for thousands of subnets.
- **Areas** bound link-state flooding and Dijkstra's input.
- **Autonomous systems** mean the internet's core routes to ~75,000 ASes, not to billions of hosts.
- **Default routes** let a stub network hold one entry instead of a million.

That is the same divide-and-conquer argument as a B+ tree's fan-out in **DBMS M7**: you do not make the lookup cleverer, you make the number of things to look through smaller.

---

## Must remember

```
ROUTING builds the table (control plane, software, seconds). FORWARDING consults it
 (data plane, hardware, nanoseconds). RIB -> FIB. SDN separates them onto different boxes.

ROUTING TABLE ROW = (destination prefix, next hop, interface, metric)
LONGEST-PREFIX MATCH: among all rows containing the destination, take the LONGEST
 prefix. Ties on length are broken by METRIC (verified: this machine has two
 224.0.0.0/4 rows, and the metric 281 route wins over the metric 331 one).
 0.0.0.0/0 is the DEFAULT ROUTE: length 0, matches everything, always loses to
 anything else -- it is last resort by construction, not by special rule.
 /32 host route > /25 > /24 > /16 > /8 > /0
 longest-prefix match IS what makes aggregation + exceptions coexist.
 a FIB is a TRIE over address bits (DSA Part 17); hardware uses a TCAM.

PER-PACKET AT A ROUTER
 check FCS, strip Ethernet | verify IP checksum | DECREMENT TTL (0 -> drop + ICMP 11)
 RECOMPUTE the IP checksum (TTL changed) | longest-prefix match | ARP the next hop
 | build a NEW Ethernet header | transmit
 -> IP addresses UNTOUCHED, BOTH MACs REPLACED

METRICS: hop count (RIP -- bandwidth-blind), bandwidth (OSPF, cost = ref/bw),
 composite (EIGRP), POLICY (BGP -- deliberately not shortest path, because
 between companies the best path is a business question)

DISTANCE VECTOR = distributed Bellman-Ford
 D(x,y) = min over neighbours v of [ cost(x,v) + D(v,y) ]
 tell your NEIGHBOURS what you know about EVERYONE
 each cell is cost/next-hop, and ONLY THE NEXT HOP is installed
 verified: 4-node network converged in 2 rounds, matching Dijkstra exactly

COUNT-TO-INFINITY (verified, 8 rounds to infinity on A--B--C)
 B asks C "how far to A?"; C says 2 WITHOUT SAYING ITS ROUTE GOES THROUGH B.
 B believes 3, C believes 4, ... climbing 2 per round until infinity.
 two causes: (1) a cost is advertised with no path information
             (2) a router MUST follow its own next hop even when the news is worse
 RIP's infinity = 16 exists ONLY to bound how long this takes.
 FIXES: split horizon (never advertise a route back the way you learned it),
        poison reverse (advertise it back AS INFINITY -- stronger than silence,
        because silence is ambiguous), triggered updates, hold-down timers.
 NONE of them fixes a loop of 3+ routers. THAT is why link state exists.

LINK STATE = flood LSAs, every router builds the SAME database, each runs DIJKSTRA
 tell EVERYONE what you know about your NEIGHBOURS
 install only the FIRST HOP; the rest is recomputed by the next router
 -> CONSISTENCY IS CRITICAL: different databases produce first hops pointing at
    each other, and the packet loops
 verified: Dijkstra and converged distance vector agree on 3,000 random graphs

 DV vs LS: knows neighbours' vectors / whole topology; Bellman-Ford / Dijkstra;
 exchanges distance vectors with neighbours / floods LSAs to the area;
 slow / fast convergence; count-to-infinity YES / no; low / higher CPU;
 scales by hop limit / AREAS; RIP, IGRP / OSPF, IS-IS

RIP: DV, hop count, infinity 16 (max 15 hops), full table every 30 s, expire 180 s.
 v1 classful, v2 carries masks. Obsolete: hop limit, slow, bandwidth-blind.
OSPF: link state, cost = reference/bandwidth, AREAS with AREA 0 as the backbone.
 Areas are HOW LINK STATE SCALES -- they bound flooding and Dijkstra's input.
 DR/BDR avoid n(n-1)/2 adjacencies. Runs on IP protocol 89. ECMP supported.
BGP: PATH VECTOR -- advertises the full AS PATH, not just a cost.
 loop detection is EXACT (see your own AS number -> discard). No hop limit needed.
 NOT shortest path: local preference, then AS-path length, then further tie-breaks.
 runs over TCP 179 because ~1M routes must be reliable, ordered and INCREMENTAL.
 fragile because it is built on TRUST -> BGP HIJACKING; RPKI/filtering are bolted on.
IGP = within an AS, shortest path, all routers yours. EGP = between ASes, policy, no trust.

HIERARCHY is why any of it scales: aggregation (one route for thousands of subnets),
 areas (bounded flooding), autonomous systems (~75k ASes, not billions of hosts),
 default routes (one entry instead of a million).
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "Routing and forwarding are the same thing" | Routing builds the table over seconds in software; forwarding consults it per packet in hardware. SDN exists precisely to separate them |
| "The router picks the first matching route" | It picks the **longest** matching prefix, regardless of order in the table |
| "The default route is checked first" | `0.0.0.0/0` has length 0, so it loses to every other match. It is consulted last by construction |
| "Longest-prefix match always gives one answer" | Two rows can tie on prefix length, and then the **metric** decides. Verified: this machine has two `224.0.0.0/4` rows |
| "A router stores the whole path to each destination" | Only the **next hop**. The rest is recomputed by the next router, which is why consistent databases matter |
| "A router changes the IP addresses" | TTL, header checksum and **both MAC addresses**. The IP addresses are untouched unless it is doing NAT |
| "A router doesn't need to recompute the IP checksum" | It must — the TTL changed, and the checksum covers the header |
| "RIP's limit of 15 hops is about network size" | It is about **bounding count-to-infinity**. Infinity is 16, so the count can only climb 16 steps before everyone agrees |
| "Count-to-infinity happens because routers are slow" | Because a distance vector advertises a **cost with no path**, so a router cannot tell that the route it is being offered goes back through itself |
| "Split horizon fixes count-to-infinity" | It fixes **two-node** loops. Loops of three or more routers survive it, which is the irreducible weakness of distance vector |
| "Poison reverse and split horizon are the same" | Split horizon stays silent; poison reverse advertises **infinity**, which is an explicit statement rather than an ambiguous absence |
| "Link state floods its routing table" | It floods **link-state advertisements** — a description of its own links. Each router then computes its own table |
| "In link state, routers exchange routes with neighbours" | That is distance vector. Link state floods topology to **everyone in the area** and each router runs Dijkstra alone |
| "Link state can't scale because every router needs the whole map" | **Areas** bound both the flooding and Dijkstra's input. That is what area 0 is for |
| "OSPF uses hop count" | Cost derived from **bandwidth** — a reference value divided by the link rate, so faster links cost less |
| "BGP finds the shortest path between networks" | It is **policy-based**. Local preference outranks AS-path length, so a longer path through a peer can beat a shorter path through paid transit — correctly |
| "BGP is a distance-vector protocol" | **Path vector**: it carries the full AS path, which makes loop detection exact and policy expressible |
| "BGP uses UDP for speed" | **TCP port 179**, because a million routes must arrive reliably, in order, and incrementally |
| "BGP is secure because it's used by ISPs" | It is built on trust and has no native origin validation, which is why **prefix hijacking** works. RPKI and filtering are voluntary add-ons |
| "Static routing is always worse" | Your own machine's table is entirely static. It is right for stub networks and default routes; dynamic routing is for routers with choices |

---

## Interview Q&A bank

**Q1. Forwarding vs routing?**
Routing is the ongoing, distributed process of building the table — control plane, software, timescale of seconds. Forwarding is the per-packet lookup in that table — data plane, hardware, timescale of nanoseconds.

**Q2. What is in a routing table row?**
A destination prefix, a next hop, an outgoing interface and a metric.

**Q3. What is longest-prefix match?**
Of all the rows whose prefix contains the destination address, the router uses the one with the longest prefix. Ties on length are broken by metric.

**Q4. Why does longest-prefix match exist?**
So aggregation and exceptions can coexist: a provider advertises one `/16` while a customer inside it advertises its own `/24`, and the more specific route automatically wins for that customer without anyone coordinating table order.

**Q5. Why is `0.0.0.0/0` the default route?**
Because its prefix length is zero, it matches every address but loses to any other match. It is the last resort by construction rather than by a special rule.

**Q6. How is longest-prefix match implemented at line rate?**
As a trie over the address bits — you walk the destination's bits and keep the deepest route you passed. Hardware uses a compressed trie or a TCAM, which matches every prefix in parallel in one cycle.

**Q7. What does a router do to a packet?**
Verifies the IP header checksum, decrements the TTL and drops with an ICMP Time Exceeded if it reaches zero, recomputes the header checksum because the TTL changed, performs longest-prefix match to get a next hop, resolves that next hop's MAC by ARP, and builds a completely new Ethernet header. The IP addresses are untouched.

**Q8. Distance vector vs link state?**
Distance vector tells its neighbours what it knows about everyone — each router exchanges a vector of costs and runs distributed Bellman-Ford. Link state tells everyone what it knows about its neighbours — each router floods a description of its own links, assembles an identical topology database, and runs Dijkstra locally.

**Q9. Which converges faster, and which uses more resources?**
Link state converges faster, because once flooding completes every router computes the answer immediately. It costs more memory, since each holds the full topology, and more CPU, since a change triggers a fresh Dijkstra. Distance vector is cheap per router and slow to settle.

**Q10. What is count-to-infinity?**
When a destination becomes unreachable, a router may learn a route to it from a neighbour whose own route went back through the first router. Neither can see the path, so each believes the other, and the advertised cost climbs slowly toward infinity. Verified on a three-router line: it took eight rounds to reach RIP's infinity of 16.

**Q11. Why does it happen at all?**
Two reasons together: a distance vector advertises a cost without saying which way the route goes, and a router must follow its own next hop even when that neighbour's cost rises. So bad news propagates one hop per round instead of being discarded.

**Q12. Why is RIP's infinity 16?**
Purely to bound count-to-infinity. With 15 as the maximum useful hop count, the climb can only run 16 steps before every router agrees the destination is gone. It is a timeout expressed in hops, not a topology limit.

**Q13. How is count-to-infinity fixed?**
Split horizon — never advertise a route back to the neighbour you learned it from. Poison reverse — advertise it back as infinity instead, which is stronger because silence is ambiguous. Plus triggered updates and hold-down timers to speed convergence and damp flapping.

**Q14. Do those fixes solve it completely?**
No. They eliminate two-node loops, but a loop of three or more routers can still form transiently, since each pair individually obeys split horizon. That irreducible weakness is the main reason link state exists.

**Q15. In link state, what exactly gets flooded?**
Link-state advertisements: each router's description of its own links and their costs. Not routes — topology. Every router then independently computes its own forwarding table from the identical database.

**Q16. Why does consistency matter so much in link state?**
Because each router installs only the first hop and trusts the next one to continue. If two routers hold different databases they can compute first hops pointing at each other, and the packet loops — which is why LSA sequence numbers and reliable flooding are such a large part of OSPF.

**Q17. Doesn't link state fail to scale if every router needs the whole topology?**
That is what areas are for. The network is divided, with area 0 as the backbone; routers hold full detail for their own area and summaries for others, so both the flooding and Dijkstra's input stay bounded.

**Q18. RIP vs OSPF vs BGP?**
RIP is distance vector with hop-count metrics and a 15-hop limit — simple and obsolete. OSPF is link state with bandwidth-derived costs and areas — the standard interior protocol. BGP is path vector, runs between autonomous systems over TCP, and selects routes by policy rather than shortest path.

**Q19. What makes BGP a path-vector protocol, and why does that matter?**
It advertises the full list of autonomous systems a route traverses. That makes loop detection exact — an AS seeing its own number discards the route — and it makes policy expressible, because you can accept or reject a route based on who it goes through.

**Q20. Why does BGP not pick the shortest path?**
Because between organisations the best path is a commercial question. BGP consults local preference before AS-path length, so a longer route through a settlement-free peer can correctly beat a shorter one through paid transit.

**Q21. Why does BGP run over TCP?**
The global table is roughly a million routes, so updates must be reliable, ordered and incremental, with keepalives holding the session open. A periodic full broadcast, as RIP does, would be unworkable at that size.

**Q22. What is BGP hijacking?**
An autonomous system advertising a prefix it does not own. Neighbours have no native way to verify ownership, so they may accept it and divert that traffic. RPKI, route filtering and IRR databases mitigate it, but they are voluntary and incompletely deployed.

**Q23. IGP vs EGP?**
An interior gateway protocol runs within one autonomous system, optimises for shortest path, and trusts every router. An exterior gateway protocol runs between autonomous systems, optimises for policy, and trusts nothing.

**Q24. Why does internet routing scale at all?**
Hierarchy at four levels: prefix aggregation means one route stands for thousands of subnets, areas bound link-state flooding, autonomous systems mean the core routes to about 75,000 ASes rather than billions of hosts, and default routes let a stub network keep a single entry.

**Q25. When is static routing the right choice?**
On stub networks with only one way out, for default routes, and on hosts — your own machine's table is entirely static with a single default route. Dynamic routing earns its cost only where there are genuine alternatives to choose between.

---

## Practice

1. Given this table, where does each destination go?
   ```
   0.0.0.0/0        -> R1
   172.16.0.0/12    -> R2
   172.16.8.0/21    -> R3
   172.16.9.0/24    -> R4
   172.16.9.128/26  -> R5
   ```
   Destinations: `172.16.9.200`, `172.16.9.50`, `172.16.10.1`, `172.16.40.1`, `10.0.0.1`.
2. Two rows have the same prefix length and different metrics. Which wins, and why is that rule needed?
3. A router receives a packet with TTL = 1. List everything it does, in order.
4. Topology `A–B 1, B–C 1, C–D 1, A–D 5`. Run Dijkstra from A and give A's forwarding table with first hops.
5. Same topology. Build the distance-vector tables round by round until they converge, and confirm they match question 4.
6. Now the `B–C` link fails. Trace what A believes about D over the next three rounds, under plain distance vector and then with split horizon.
7. `A–B–C–D` in a line, all costs 1, and the `A–B` link fails. Does split horizon prevent a loop here? Justify your answer.
8. Why can a link-state network form a transient loop at all, if every router has the same map?
9. A `/16` is advertised by a provider and a `/24` inside it by its customer. Explain what happens to a packet for an address in that `/24`, and what would happen without longest-prefix match.
10. Your AS can reach a destination via a paid transit provider in 2 AS hops or a settlement-free peer in 4. Which does BGP choose by default, and which attribute decides?
11. Explain in three sentences why BGP needs TCP but OSPF does not.
12. Count the entries a router would need without aggregation, areas, ASes or default routes. Then say which of the four does the most work.

**Answers to 1, 7 and 9:**

> **1.** `172.16.9.200` → **R5** (matches `/26`, the longest). `172.16.9.50` → **R4** (`/24`; the `/26` covers `.128–.191` only). `172.16.10.1` → **R3** (`/21` covers `172.16.8.0–172.16.15.255`). `172.16.40.1` → **R2** (`/12`; outside the `/21`). `10.0.0.1` → **R1** (only the default matches).
>
> **7.** **No.** Split horizon only stops a router advertising a route back to the neighbour it learned it from — a two-node loop. Here, when `A–B` fails, C still advertises its route to A to **D**, and D advertises back to C; C learned it from B, not D, so split horizon permits the exchange. The three-router loop B→C→D forms and the count climbs. **This is exactly the case that split horizon cannot fix**, and it is why the honest answer to "how is count-to-infinity solved" is "two-node cases are, larger ones are not — which is why link state exists".
>
> **9.** The router's table contains both rows. Longest-prefix match selects the `/24`, so the packet goes to the customer directly, while every *other* address in the `/16` follows the provider's route. Without longest-prefix match the two routes would be ambiguous and would have to be resolved by table order or by never aggregating at all — so aggregation and customer-specific exceptions could not coexist, and the global table would have to carry every subnet separately.

---

## Exit checklist

```
[ ] I can distinguish routing from forwarding on five axes
[ ] I know what RIB and FIB mean and which is hardware
[ ] I can read a real routing table row by row
[ ] I can apply longest-prefix match to any table and destination
[ ] I know ties on prefix length are broken by METRIC
[ ] I can explain why 0.0.0.0/0 is the default route, from its prefix length
[ ] I can explain why longest-prefix match is what makes aggregation possible
[ ] I know a FIB is a trie over address bits, and what a TCAM does
[ ] I can list the eight things a router does per packet, in order
[ ] I know the IP addresses are untouched and both MACs are replaced
[ ] I know why the IP checksum must be recomputed at each hop
[ ] I can compare static and dynamic routing and say where each belongs
[ ] I can name four metric families and which protocol uses each
[ ] I can write the Bellman-Ford update equation
[ ] I can build distance-vector tables round by round until convergence
[ ] I know only the NEXT HOP is installed, not the path
[ ] I can trace count-to-infinity to its conclusion
[ ] I can state BOTH causes of count-to-infinity
[ ] I know why RIP's infinity is 16
[ ] I can explain split horizon and poison reverse, and why poison is stronger
[ ] I know neither fixes loops of 3+ routers, and that this is why link state exists
[ ] I can list the six steps of link state, in order
[ ] I can run Dijkstra and produce a forwarding table with first hops
[ ] I can explain why database consistency is critical in link state
[ ] I can fill in the DV vs LS table from memory
[ ] I can give the "tells neighbours about everyone / tells everyone about neighbours" line
[ ] I can describe RIP, OSPF and BGP in one sentence each
[ ] I know OSPF's cost comes from bandwidth, and what areas are for
[ ] I can explain path vector and the two things it buys
[ ] I can explain why BGP is not shortest-path, and name the deciding attribute
[ ] I can explain why BGP needs TCP
[ ] I can explain BGP hijacking and why it is possible
[ ] I can distinguish IGP from EGP on scope, goal, metric and trust
[ ] I can give the four levels of hierarchy that make internet routing scale
```

---

## Next

**Part 7: M5 — UDP and TCP Connection Management.** The transport layer, and the module that answers more interview questions than any other: what the transport layer adds over IP; ports, sockets and the five-tuple; the **UDP header and when UDP is the right answer**; the **TCP header field by field**; **the three-way handshake** — why three and not two, initial sequence numbers, SYN flooding and SYN cookies; the **four-way close** and the half-close; the **full TCP state machine** with the real `netstat` distribution from this machine; **why `TIME_WAIT` exists and why there are so many of them**; `CLOSE_WAIT` as a bug signal; and **TCP vs UDP as a decision, not a table**.
