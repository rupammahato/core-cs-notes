# Plan: Computer Networks Placement Handbook

*Read this and approve it, or change it. No module gets written until you say so.*

---

## 0. What carries over from the DSA / OOP / OS / DBMS handbooks

Everything. Same system, no new conventions to learn:

| Existing trait | How it applies here |
|---|---|
| Part 1 is a roadmap with no teaching | Same |
| One module per file, `cn-handbook-part-N-module-X-topic.md` | Same |
| Header line: `Module 3 · 4 hours · Tier 1 · Requires: M0, M1` | Same |
| Opening "why this module matters" + one organising principle in a blockquote | Same |
| Numbered sub-sections, ASCII diagrams, trace tables | Same. Diagrams for headers, handshakes, sliding windows, routing tables |
| Comparison table for every confusable pair | Essential here — CN is even more "difference between X and Y" than DBMS |
| Must remember / common wrong answers / interview Q&A bank / practice / exit checklist / Next | Same |
| Everything executable is executed before it goes in the notes | See §3 — this subject verifies *better* than DBMS did |
| Tier marking, Tier 3 = skippable | Same |
| Source notes never modified by the site sync | Same; `CN Notes/` is copied, never edited |

---

## 1. What the research says interviewers actually ask

The lists agree closely, and they are much shorter than the GATE syllabus.

**Sources consulted:** InterviewBit *"70+ Top Networking Interview Questions (2026)"* (subnetting and CIDR appear as question 8 — it is front-loaded, not advanced); Unstop *"Top 100 Networking Interview Questions & Answers (2026)"* (OSI/TCP-IP models, IP addressing, subnetting, routing, switching, security, HTTP/DNS/FTP); HireStepX *"Computer Networks Interview India 2026"* (explicitly: "explain the OSI model and what happens at each layer", then HTTP and DNS); Intellipaat *"25+ Computer Networks Interview Questions (2026)"* (hub vs switch vs router, OSI, VPN); GATE Overflow's Computer Networks subject page (**CN carries 8–12 marks in GATE CS**); the GO Classes GATE marathon topic breakdown (stop-and-wait and sliding window → Hamming and CRC → subnetting, supernetting, distance vector, link state → TCP congestion control and UDP); and the *"what happens when you type a URL"* corpus — AWS's own blog, Medium, dev.to and a LinkedIn post whose author calls it the question they are "shocked at how often" they see.

What that adds up to:

**Near-certain, asked almost verbatim**
- Explain the OSI model, layer by layer — and OSI vs TCP/IP
- **TCP vs UDP**, and when you would choose each
- The **three-way handshake**, and the four-way close
- **Subnetting**: given an address and a mask, find the network, broadcast, host range and usable count
- **What happens when you type a URL and press Enter** — the end-to-end integration question
- **DNS**: how resolution works, recursive vs iterative, record types
- **HTTP**: methods, status codes, HTTP/1.1 vs 2 vs 3, and HTTPS/TLS
- Hub vs switch vs router; **ARP**; **DHCP**; **NAT**
- Flow control vs congestion control

**Common follow-ups that separate candidates**
- Why does `TIME_WAIT` exist, and why are there so many of them
- Why is HTTP/2 multiplexed and what did HTTP/3 change (QUIC, connection migration)
- Stateless vs stateful; idempotent vs safe HTTP methods
- What a load balancer, reverse proxy and CDN each actually do
- Why TCP needs congestion control at all when it already has flow control

**Written-test / GATE numericals** (8–12 marks, and the highest-density marks in the subject)
- Stop-and-wait, Go-Back-N and Selective Repeat **utilization and window-size** problems
- **CRC** division and **Hamming code** placement/syndrome
- **Subnetting / VLSM / supernetting** arithmetic
- Distance-vector convergence tables and **link-state (Dijkstra)** runs
- Bandwidth-delay product, transmission vs propagation delay, throughput

**Deliberately thin** — named, defined, one line each, Tier 3: session and presentation layer specifics, token ring, ATM, SONET, analogue modulation, the full IPv6 feature list, SNMP, X.25.

---

## 2. Scope

**In:** the five layers as actually used (physical/data-link, network, transport, application), every numerical above, the real protocols a backend engineer meets (IP, ARP, DHCP, NAT, ICMP, TCP, UDP, DNS, HTTP, TLS, SMTP/FTP/SSH in brief), security fundamentals through TLS and PKI, and the end-to-end URL walkthrough as an integration module.

**Out:** wireless PHY in depth, telecom-era technologies, network administration (Cisco IOS configuration, VLAN trunking syntax), and anything that only appears in a networking-specialist role rather than an SDE interview. Where something is out, the notes say so rather than silently omitting it.

---

## 3. How things get verified — and the honest limits

This is where CN differs from DBMS, and mostly for the better. **Verified available on this machine:**

| Capability | What it verifies | Status |
|---|---|---|
| Python 3.12.10 `ipaddress` | Every subnetting, VLSM, CIDR and supernetting numerical | ✅ Confirmed working |
| Python `socket` on loopback | TCP and UDP behaviour, socket options, connection states, blocking vs non-blocking | ✅ TCP and UDP loopback confirmed |
| `ipconfig`, `arp`, `netstat`, `route`, `getmac`, `tracert`, `nslookup`, `pathping`, `curl` | Real machine and network state | ✅ All present |
| Real internet | DNS resolution, HTTP over port 80, TLS handshake | ✅ Confirmed: `example.com` resolved, `HTTP/1.1 200 OK` received, **TLS 1.3 / TLS_AES_256_GCM_SHA384** negotiated and the certificate read |
| `dnspython` | A/AAAA/MX/NS/CNAME/TXT lookups, TTLs, iterative resolution from the root | ✅ Installed |
| `httpx` + `h2` | **Real HTTP/2** requests, not just documented ones | ✅ Installed |
| `requests`, `urllib3`, `ssl`, `http.server` | Headers, redirects, cookies, caching, keep-alive; and a local server to show both sides | ✅ Available |
| Pure Python | CRC, Internet checksum, Hamming, Dijkstra, Bellman-Ford/distance-vector, sliding-window simulation | ✅ Self-testable against known answers |

**And the limits, which will be labelled in the notes rather than hidden:**

1. **Raw sockets are blocked** (`PermissionError 10013`) and `scapy` is not installed, so **I cannot capture or craft packets.** Headers will instead be built and parsed byte-by-byte with `struct` and checked field-by-field against the RFC layout — which verifies the *format* exactly, but is not a packet capture. Where a real capture is the only honest evidence, the notes will say "run Wireshark yourself" and give the filter to use.
2. **ICMP echo to public hosts is filtered here** — `ping 1.1.1.1` gives 100% loss while `tracert 1.1.1.1` returns hops and TCP/443 works fine. That is itself good teaching material about firewalls, and it will be presented as the real finding it is, not worked around.
3. This machine is behind NAT on a private `/17`, so NAT translation can be *inferred* but not observed from both sides.

**Two pieces of live material already captured, as a sample of what this buys:**

```
ipconfig  ->  IPv4 10.145.68.45 / 255.255.128.0, gateway 10.145.0.2        (a real /17)
          ->  169.254.15.67 on a disconnected adapter                      (real APIPA)

arp -a    ->  10.145.0.2       00-00-5e-00-01-01   dynamic   (a VRRP virtual MAC)
              10.145.127.255   ff-ff-ff-ff-ff-ff   static    (the subnet broadcast)
              224.0.0.251      01-00-5e-00-00-fb   static    (IPv4 multicast -> MAC)

netstat   ->  76 ESTABLISHED, 48 TIME_WAIT, 44 LISTENING, 3 CLOSE_WAIT
```

Those four lines cross-check each other, and I verified it: `10.145.68.45/255.255.128.0` is `10.145.0.0/17`, whose broadcast address is **exactly** the `10.145.127.255` that appears in the ARP table, and `224.0.0.251` maps to **exactly** the `01-00-5e-00-00-fb` that appears there too (low 23 bits of the group address). The subnetting module can therefore be taught from this machine's own numbers rather than from invented ones, and the 48 `TIME_WAIT` entries give the TCP-states module a real reason to explain `TIME_WAIT` properly.

---

## 4. Module plan

**Folder:** `CN Notes/` · **About 28–32 hours** · 13 files

| Part | Module | Contents | Hours | Tier |
|---|---|---|---|---|
| 1 | Master roadmap | Syllabus, dependency map, tiers, research, the 50-question map, numericals list, schedules, progress checklist | — | — |
| 2 | **M0 Fundamentals and layering** | What a network is for; **OSI seven layers and what genuinely happens at each**; **TCP/IP four/five-layer model and the honest mapping between them**; encapsulation and headers as one picture; PDU names per layer; protocol vs service vs interface; devices — hub, switch, router, bridge, gateway, repeater, NIC, modem, access point — and **which layer each works at**; collision vs broadcast domains; LAN/MAN/WAN, client-server vs P2P; topologies (Tier 3); **the four delays** (transmission, propagation, queuing, processing), bandwidth vs throughput vs latency, **bandwidth-delay product** with worked numbers | 3 | 1 |
| 3 | **M1 Physical and data link: framing and errors (numericals centrepiece 1)** | Line coding named only; framing — character/bit stuffing with a worked trace; **error detection: parity, 2-D parity, Internet checksum, CRC** (polynomial long division worked and verified, plus what CRC can and cannot catch); **Hamming code** — redundant-bit count, placement, syndrome decoding, `d = 2t+1`; **error control / ARQ: stop-and-wait, Go-Back-N, Selective Repeat** with timeline diagrams; **utilization, efficiency and window-size numericals** (the highest-yield numerical family in the subject); sequence-number bit requirements; piggybacking | 4 | 1 |
| 4 | **M2 Medium access and the LAN** | The multiple-access problem; ALOHA and slotted ALOHA efficiency; **CSMA, CSMA/CD** (and why minimum frame size exists, worked), **CSMA/CA** and why Wi-Fi cannot do collision *detection*; **Ethernet frame format field by field**, MAC addresses, unicast/multicast/broadcast; **hub vs switch vs router as the one table everyone is asked**; switch learning and forwarding with a worked MAC-table trace; **ARP** — request/reply, the cache, gratuitous ARP, ARP spoofing (verified against this machine's real ARP table); VLANs and trunking in brief; spanning tree in one page (Tier 3) | 3 | 1 |
| 5 | **M3 Network layer: IP and subnetting (numericals centrepiece 2)** | The IPv4 header field by field (and which fields matter in an interview); fragmentation, MTU, DF, and a worked fragmentation numerical; classful addressing and why it died; **CIDR, masks, prefix arithmetic**; **subnetting — the mechanical procedure, done on this machine's own `/17`**; **VLSM** worked end to end for a real address plan; supernetting and route aggregation; special addresses (loopback, APIPA, private ranges, broadcast); **NAT and PAT** — why they exist, what they break; **DHCP's DORA**; **ICMP** and what `ping`/`tracert` actually send; **IPv6** — why, the header, address notation, and transition mechanisms, kept to one Tier-2/3 section | 5 | 1 |
| 6 | **M4 Routing** | Forwarding vs routing; the routing table read from this machine (`route print`) and **longest-prefix match** worked; static vs dynamic; **distance vector** with a full convergence table, **count-to-infinity** and the split-horizon/poison-reverse fixes; **link state and Dijkstra** run step by step (straight reuse of DSA Part 14); DV vs LS as a table; RIP, OSPF (areas, LSAs in brief), **BGP and why the internet needs a path-vector protocol**; interior vs exterior gateway; hierarchical routing; multicast/broadcast named | 4 | 1/2 |
| 7 | **M5 Transport layer: UDP, and TCP connection management** | What the transport layer adds over IP; ports, sockets, the five-tuple; **UDP header and when UDP is the right answer** (DNS, DHCP, VoIP, games, QUIC); **TCP header field by field**; **the three-way handshake** — why three and not two, ISNs, SYN flooding and SYN cookies; **the four-way close**, half-close; **the full TCP state machine** with the real `netstat` distribution from this machine; **why `TIME_WAIT` exists and why there are 48 of them here**; `CLOSE_WAIT` as a bug signal; **TCP vs UDP — the table**; verified socket demonstrations on loopback | 4 | 1 |
| 8 | **M6 TCP reliability, flow and congestion control (centrepiece 3)** | Sequence and acknowledgement numbers traced on real bytes; cumulative ACKs, SACK; retransmission — RTO, RTT estimation, Karn's algorithm, exponential backoff; **flow control: the receive window**, zero-window and window probes, **silly window syndrome** and both halves of the fix (Nagle and Clark); **congestion control: why it is a separate problem from flow control**, slow start, congestion avoidance, **AIMD**, fast retransmit, fast recovery, **Tahoe vs Reno vs NewReno vs CUBIC vs BBR**; a worked **cwnd-versus-RTT table** through loss events; bufferbloat and ECN in brief; **throughput ≈ window / RTT** and why long fat networks need window scaling | 5 | 1 |
| 9 | **M7 DNS** | Why names exist; the hierarchy — root, TLD, authoritative; **recursive vs iterative resolution traced for real, from the root servers down**; resolver and the four caches (browser, OS, router, ISP); **record types** — A, AAAA, CNAME, MX, NS, TXT, SOA, PTR, SRV, CAA — each with a real lookup; TTL and propagation; why DNS uses UDP and when it falls back to TCP; reverse DNS; round-robin DNS and GeoDNS as crude load balancing; DNS caching bugs in practice; DoH/DoT and DNSSEC in brief; `nslookup`/`dig` output read line by line | 3 | 1 |
| 10 | **M8 HTTP and the web** | HTTP as a stateless request/response protocol; **methods, and the safe/idempotent table** (the one people get wrong); **status-code families with the ones that actually get asked** (301 vs 302 vs 307, 401 vs 403, 404 vs 410, 500 vs 502 vs 503 vs 504); request and response structure with **real captured headers**; **cookies, sessions, and token-based auth** — stateless vs stateful, and where JWT fits; **caching**: `Cache-Control`, `ETag`, conditional requests, and a real 304; content negotiation and compression; **CORS and the preflight**, with the browser-only-restriction point made clearly; **HTTP/1.0 → 1.1 → 2 → 3**: keep-alive, pipelining and why it failed, **head-of-line blocking at both layers**, multiplexing, HPACK, server push and why it was abandoned, **QUIC and connection migration**; **a real HTTP/2 request executed**; WebSockets and SSE vs polling; REST principles briefly | 4 | 1 |
| 11 | **M9 Network security** | Threat model: what an attacker on the path can do; symmetric vs asymmetric crypto and why both are used; hashing vs encryption vs encoding (**the single most common confusion in this area**); digital signatures; **certificates, CAs and the chain of trust**; **the TLS 1.2 handshake and the shorter TLS 1.3 handshake, step by step**, with the **real negotiated version and cipher from this machine** and the certificate chain printed; forward secrecy; HTTPS end to end, HSTS, mixed content; **what HTTPS does and does not hide** (SNI, DNS, traffic size); firewalls — stateless vs stateful, and this network's blocked ICMP as the live example; NAT as accidental security; VPN and tunnelling; **the attacks worth naming**: MITM, replay, DoS/DDoS, SYN flood, ARP/DNS spoofing, session hijacking, with the defence for each | 4 | 1/2 |
| 12 | **M10 Putting it together: what happens when you type a URL** | The integration module, written as one continuous end-to-end trace with every step verified where possible: URL parsing → HSTS check → the four DNS caches → recursive resolution → ARP for the gateway → TCP handshake → TLS handshake → the HTTP request → server, reverse proxy, load balancer and CDN → the response → render and subresources → keep-alive and connection reuse. Then the **layered answer at three depths** (30 seconds, 3 minutes, 10 minutes) because the question is asked at all three; where each step can fail and what the user sees; **latency budget arithmetic** showing why DNS and TLS dominate a first request; the remaining application protocols in one table (SMTP/IMAP/POP3, FTP vs SFTP, SSH, Telnet, SNMP, NTP) | 3 | 1 |
| 13 | **Consolidation** | Layer-by-layer one-page map; port-number and protocol sheet; **confusable-pairs master table (~100 rows)**; **numericals procedure sheet** (subnetting, VLSM, CRC, Hamming, sliding-window utilization, fragmentation, BDP, Dijkstra, distance vector, cwnd trace); **70 rapid-fire Q&A**; **25 worked numericals with full solutions, all computed**; the three "tell me everything" answers (URL walkthrough, TCP vs UDP, OSI); final exit checklist | 2 | — |

**Dependency chain:** M0 → M1 → M2 → M3 → M4, and M0 → M5 → M6. M7/M8/M9 need M5. M10 needs everything. Consolidation last.

**If you only have a week:** M0, M3, M5, M6, M8 plus the DNS section of M7 and the TLS section of M9 — then read M10 twice. That is the 80%, and it is weighted towards the interview rather than the written test.

**If the written test is the priority instead:** M1, M3, M4, M6 — the four numerical modules.

---

## 5. Links back to your existing handbooks

| CN topic | Builds on |
|---|---|
| Dijkstra for link-state routing | DSA Part 14 (graphs) — the same algorithm, run on a router's topology database |
| Bellman-Ford for distance-vector routing | DSA Part 14 — and count-to-infinity is what a negative-cycle-free but slow-converging Bellman-Ford looks like in the wild |
| Longest-prefix match | DSA Part 17 (tries) — a routing table is a trie over address bits |
| Sliding window buffers, sequence-number wraparound | DSA Part 3 (arrays), circular buffers |
| CRC and checksums | DSA Part 4 (bit manipulation) — XOR arithmetic and polynomial division |
| Hamming distance | DSA Part 4 (bit manipulation) |
| Sockets, blocking vs non-blocking, `select`/`epoll` | OS M3 (threads), OS M10 (I/O) — a socket is a file descriptor |
| TCP state machine | OS M2 (process states) — same style of diagram, same reasoning |
| Congestion control as feedback | OS M4 (synchronization) for the shared-resource framing |
| Buffer bloat, queuing delay | OS M7 (queuing and scheduling) |
| Load balancers, CDNs, caching, read replicas | **DBMS M10** (§10.3–§10.4) — CN M10 is the other half of that conversation |
| TLS, PKI, hashing | DBMS M6 (SQL injection) was the application-layer half of security; this is the transport half |
| CAP, latency vs consistency | DBMS M10 — PACELC's "L" is the latency this subject explains |

As before, these go *into* the notes as cross-references, not just into this plan. With four handbooks already written, CN should read like revision of the other three about a third of the time.

---

## 6. Site integration

One entry in `SUBJECTS` in `study-guide/scripts/sync-notes.mjs` plus a `CN` tag in `components/search-dialog.tsx`, exactly as DBMS was wired. Proposed sidebar groups:

| Group | Chapters |
|---|---|
| **Foundations** | M0 fundamentals/layering, M1 framing and errors |
| **Link & Network** | M2 medium access and LAN, M3 IP and subnetting, M4 routing |
| **Transport** | M5 UDP and TCP connections, M6 TCP reliability and congestion |
| **Application** | M7 DNS, M8 HTTP |
| **Security** | M9 network security |
| **End to End & Revision** | M10 URL walkthrough, consolidation |

The sync script throws if any chapter is in no group, so I'll wire this **after all 13 files exist**, as with DBMS, and run `npm run build` to confirm.

---

## 7. How we'll work

1. You approve or edit this plan.
2. I write **Part 1 (master roadmap)**.
3. Then you say "start M0" or "do the next 3", and modules get written in order — roughly 500–900 lines each, same depth and voice as the DBMS handbook, everything computable computed before it lands.

---

## 8. Open decisions — tell me if you disagree

1. **Live output comes from this Windows machine** (`ipconfig`, `arp`, `netstat`, `route print`, `tracert`, `nslookup`), with the Linux/macOS equivalent named in a table beside each. Defaulting to this, since it is what can actually be verified; say the word if you'd rather see Linux commands as primary with Windows as the aside.
2. **No packet captures.** Raw sockets are blocked and `scapy` is absent, so headers get built and decoded with `struct` against the RFC field layout, and the notes will tell you the Wireshark filter to run yourself rather than pretending. Flagging this because a packet capture would genuinely be better, and I can't produce one here.
3. **"What happens when you type a URL" is its own module (M10)**, not spread thinly across the others, because it is asked as one question and is the best revision device in the subject.
4. **IPv6 stays one Tier-2/3 section inside M3** rather than becoming its own module. It is asked as "why IPv6 and how is the address written", not in depth.
5. **Wireless, telecom-era tech and router configuration are out of scope** (§2) — named and dismissed in a line each, not taught.
6. **Batch size: 3 modules per batch**, as with OOP, OS and DBMS.

---

**Next after CN:** the thin **HLD / system-design handbook**, which DBMS M10 and CN M8/M10 have now both pre-loaded — that would be the fifth and final piece for product-company SDE rounds.
