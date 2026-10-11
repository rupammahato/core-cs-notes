# Computer Networks Placement Handbook — Part 1: Master Roadmap

**Your roadmap for the Computer Networks portion of technical interviews: what to learn, in what order, how deep, which numericals and protocols to practise, and which interview questions each module answers. Later parts teach each module in full.**

---

## 0. How this handbook is built

Fifth subject, same system as DSA, OOP, OS and DBMS. Nothing new to learn about *how* to read these notes.

| | |
|---|---|
| **Files** | 13 — this roadmap, eleven modules (M0–M10), one consolidation file |
| **Folder** | `CN Notes/`, one file per module, named `cn-handbook-part-N-module-X-topic.md` |
| **Length** | 500–900 lines per module |
| **Total time** | About 28–32 hours of first-pass study |
| **Prerequisites** | None strictly, but M0's delay arithmetic assumes you can multiply, and M4 assumes DSA Part 14 (graphs) |

### Note format

Every module file has the same shape, so you always know where to look:

```
Header line        Module 3 · 5 hours · Tier 1 · Requires: M0, M2
Why this module    what it buys you in an interview, and the weighting
                   one ORGANISING PRINCIPLE in a blockquote -- the sentence
                   the whole module hangs off
Numbered sections  3.1, 3.2, ... with ASCII diagrams and traced tables
Comparison tables  one for every confusable pair
Must remember      the compressed block to re-read before an interview
Common wrong       a two-column table: the wrong answer, then the right one
answers
Interview Q&A      20-30 questions with answers at interview length
Practice           problems, with answers to the ones people get wrong
Exit checklist     tick every line or the module is not done
Next               what the following part covers
```

### Tier marking

Every section is marked **Tier 1** (must master), **Tier 2** (high priority at product companies), **Tier 3** (good to know, one page) or **Tier 4** (skip). You can read Tier 1 only and still pass most interviews — §3 lists exactly what that means.

### How things are verified

This is the strictest rule in the handbook, carried over from the OS numericals and the DBMS SQL: **nothing computable is asserted from memory.** Specifically, on this machine:

| Verified with | What it proves |
|---|---|
| Python 3.12.10 `ipaddress` | Every subnetting, VLSM, CIDR and supernetting result (M3) |
| Python `socket` on loopback | TCP and UDP behaviour, socket options, connection states (M5) |
| Pure Python, self-tested against known answers | CRC, Internet checksum, Hamming, sliding-window utilization, Dijkstra, distance vector, `cwnd` traces (M1, M4, M6) |
| `dnspython` against the real root servers | Iterative resolution, every record type, TTLs (M7) |
| `httpx` + `h2` against real servers | **Real HTTP/2**, headers, caching, redirects (M8) |
| Python `ssl` against real servers | The negotiated TLS version, cipher suite and certificate chain (M9) |
| `ipconfig`, `arp -a`, `netstat -an`, `route print`, `tracert`, `nslookup` | This machine's real addresses, ARP table, TCP states and routing table |

Confirmed before writing a line: `example.com` resolves, port 80 returns `HTTP/1.1 200 OK`, and TLS negotiates **TLSv1.3 with TLS_AES_256_GCM_SHA384**. So the application-layer modules are taught from real traffic.

### The two honest limits

Stated here once, and re-stated wherever they apply:

1. **No packet captures.** Raw sockets are blocked on this machine (`PermissionError 10013`) and `scapy` is not installed, so I cannot capture or craft packets. Headers are instead **built and decoded byte-by-byte with `struct`** and checked field-by-field against the RFC layout — which verifies the format exactly but is not a capture. Where a capture is the only honest evidence, the notes say "run Wireshark yourself" and give you the display filter.
2. **ICMP echo is filtered on this network.** `ping 1.1.1.1` gives 100% loss while `tracert 1.1.1.1` returns hops and TCP/443 works perfectly. That is a real firewall doing a real thing, so it is presented as evidence rather than worked around.

### The live material this handbook is built on

Four commands on this machine, whose outputs cross-check each other:

```
ipconfig   ->  IPv4 10.145.68.45   mask 255.255.128.0   gateway 10.145.0.2
           ->  169.254.15.67 on a disconnected adapter

arp -a     ->  10.145.0.2        00-00-5e-00-01-01   dynamic
               10.145.127.255    ff-ff-ff-ff-ff-ff   static
               224.0.0.251       01-00-5e-00-00-fb   static

netstat    ->  76 ESTABLISHED   48 TIME_WAIT   44 LISTENING   3 CLOSE_WAIT

tracert    ->  1  10.145.0.3    2  10.120.0.25    3  10.250.1.9
```

Everything interesting in M2 and M3 comes out of those twelve lines:

- `10.145.68.45 / 255.255.128.0` is **`10.145.0.0/17`**, and its broadcast address is `10.145.127.255` — **exactly** the entry in the ARP table. The mask and the ARP table confirm each other.
- `169.254.15.67` is a real **APIPA** address: DHCP failed on that adapter.
- `00-00-5e-00-01-01` is not a vendor MAC; it is a **VRRP virtual MAC**, so the default gateway is a redundant pair of routers.
- `01-00-5e-00-00-fb` is the IPv4 multicast MAC for `224.0.0.251` (low 23 bits of the group address) — mDNS.
- 48 `TIME_WAIT` entries against 76 `ESTABLISHED` is why M5 explains `TIME_WAIT` properly instead of in one line.
- Private addresses at hops 1–3 of the traceroute say this machine is several NAT layers from the internet.

---

## 1. The master syllabus

| Part | Module | Hours | Tier | The questions it answers |
|---|---|---|---|---|
| 1 | Master roadmap | — | — | What to study and in what order |
| 2 | **M0** Fundamentals and layering | 3 | 1 | OSI vs TCP/IP. Which layer does a switch work at? What is encapsulation? |
| 3 | **M1** Framing and errors | 4 | 1 | CRC, Hamming, stop-and-wait vs sliding window, utilization numericals |
| 4 | **M2** Medium access and the LAN | 3 | 1 | Hub vs switch vs router. CSMA/CD vs CSMA/CA. What is ARP? |
| 5 | **M3** IP addressing and subnetting | 5 | 1 | Subnetting arithmetic. NAT, DHCP, ICMP, IPv6 |
| 6 | **M4** Routing | 4 | 1/2 | Distance vector vs link state. RIP/OSPF/BGP. Longest prefix match |
| 7 | **M5** UDP and TCP connections | 4 | 1 | TCP vs UDP. The three-way handshake. Why does `TIME_WAIT` exist? |
| 8 | **M6** TCP reliability and congestion | 5 | 1 | Flow vs congestion control. Slow start, AIMD, fast recovery |
| 9 | **M7** DNS | 3 | 1 | How resolution works. Recursive vs iterative. Record types. Why UDP? |
| 10 | **M8** HTTP and the web | 4 | 1 | Methods, status codes, caching, cookies, HTTP/1.1 vs 2 vs 3, CORS |
| 11 | **M9** Network security | 4 | 1/2 | The TLS handshake. Certificates. Hashing vs encryption. Common attacks |
| 12 | **M10** What happens when you type a URL | 3 | 1 | The whole subject as one answer, at three depths |
| 13 | **Consolidation** | 2 | — | Revision sheets, 70 rapid-fire, 25 worked numericals |

**Total: about 28–32 hours.** Tier 1 alone (M0, M1, M2, M3, M5, M6, M7, M8, M10) is about 22–25 hours.

---

## 2. Dependency map

```
                        [M0] Fundamentals & layering
                         (OSI/TCP-IP, encapsulation,
                          devices, delays, BDP)
                                   |
                 +-----------------+-----------------+
                 |                                   |
        [M1] Framing & errors                [M5] UDP & TCP connections
        (CRC, Hamming, ARQ,                  (ports, headers, handshake,
         utilization)                          state machine, TIME_WAIT)
                 |                                   |
        [M2] Medium access & LAN             [M6] TCP reliability &
        (CSMA, Ethernet, switches,                congestion control
         ARP, VLAN)                           (windows, slow start, AIMD)
                 |                                   |
        [M3] IP & subnetting  <----------------------+
        (header, CIDR, VLSM,                         |
         NAT, DHCP, ICMP, IPv6)          +-----------+-----------+
                 |                       |           |           |
        [M4] Routing                 [M7] DNS   [M8] HTTP   [M9] Security
        (DV, LS, RIP/OSPF/BGP,                                (TLS, PKI,
         longest prefix)                                       attacks)
                 |                       |           |           |
                 +-----------+-----------+-----------+-----------+
                                         |
                      [M10] What happens when you type a URL
                           (the integration module)
                                         |
                              [Part 13] Consolidation
```

Two independent spines come out of M0: the **lower layers** (M1 → M2 → M3 → M4) and the **transport-and-up** path (M5 → M6 → M7/M8/M9). They can be done in either order or interleaved — but M10 needs both, which is why it is last.

**If an interview is close**, pull the second spine forward: M5, M6, M8 and M7 answer more interview questions per hour than M1 and M4 do. **If a written test is close**, do the first spine: M1, M3 and M4 are where the marks are.

### The dependencies that actually bite

| You cannot understand | Until you have | Because |
|---|---|---|
| Why a switch has no IP address | M0 layering | Layer 2 forwards on MAC; layer 3 is a different addressing scheme entirely |
| Why fragmentation exists | M0 (MTU) + M2 (Ethernet frame) | The 1500-byte Ethernet payload is *why* IP must fragment |
| Minimum Ethernet frame size | M0 delays + M2 CSMA/CD | It is a propagation-delay constraint, not an arbitrary number |
| Sliding-window utilization | M0 transmission vs propagation delay | Utilization is a ratio of those two, nothing more |
| Why sequence numbers need `2^k ≥ N+1` bits | M1 ARQ timelines | The bound comes from the ambiguity a lost ACK creates |
| Subnetting at all | M0 layering + M3 CIDR | A mask is meaningless until "network portion" means something |
| Longest-prefix match | M3 prefixes | A routing table is a set of prefixes; matching is a trie walk |
| Count-to-infinity | M4 distance vector + DSA Bellman-Ford | It is Bellman-Ford converging slowly with stale neighbour information |
| Why three-way and not two-way handshake | M5 ISNs | Two-way cannot confirm that *both* initial sequence numbers were received |
| Why `TIME_WAIT` lasts 2×MSL | M5 state machine + M0 propagation delay | It is a duration derived from how long a stray packet can survive |
| Flow control vs congestion control | M6 — but it fails without M0 | One protects the *receiver*, the other the *network*; the distinction needs the delay model |
| Why throughput ≈ window / RTT | M0 BDP | It is the bandwidth-delay product restated from the sender's view |
| Why DNS uses UDP | M5 UDP + M0 delays | One round trip beats three for a 100-byte answer |
| Why HTTP/2 multiplexes | M6 + M8 | HTTP/1.1 head-of-line blocking is an *application*-layer queue above a TCP-layer one |
| Why HTTP/3 left TCP | M6 loss recovery + M8 multiplexing | One lost segment stalls every multiplexed stream, because TCP delivers in order |
| What TLS actually protects | M9 + M3 + M7 | The payload is encrypted; the IP header, SNI and DNS query are not |
| The URL walkthrough | Everything | It is the whole subject in sequence, which is why it is the best revision tool |

---

## 3. Priority tiers

### Tier 1 — must master

Asked directly, in almost every interview that touches networks.

```
M0   OSI seven layers and what happens at each; OSI vs TCP/IP
     encapsulation and headers; which layer each device works at
     collision vs broadcast domain
     transmission vs propagation delay; bandwidth-delay product
M1   CRC (worked), Hamming (worked), checksum
     stop-and-wait vs Go-Back-N vs Selective Repeat
     utilization and window-size numericals
M2   hub vs switch vs router (the table)
     CSMA/CD and CSMA/CA; why Wi-Fi cannot detect collisions
     Ethernet frame; MAC addresses; switch learning
     ARP: request, reply, cache
M3   IPv4 header; fragmentation and MTU
     CIDR, masks, subnetting, VLSM (the arithmetic, cold)
     private ranges, APIPA, loopback, broadcast
     NAT and PAT; DHCP DORA; ICMP and what ping/tracert send
M4   distance vector vs link state; count-to-infinity
     longest prefix match
     RIP vs OSPF vs BGP in one line each
M5   TCP vs UDP (the table), and when to choose each
     TCP header; three-way handshake; four-way close
     TCP states; TIME_WAIT and CLOSE_WAIT
     ports, sockets, the five-tuple
M6   sequence/ACK numbers; retransmission and RTO
     flow control: the receive window
     congestion control: slow start, AIMD, fast retransmit/recovery
     why flow control and congestion control are different problems
     throughput = window / RTT
M7   the DNS hierarchy; recursive vs iterative
     A, AAAA, CNAME, MX, NS, TXT; TTL and caching
     why UDP, and when DNS uses TCP
M8   methods and the safe/idempotent table
     status codes that get asked (301/302/307, 401/403, 500/502/503/504)
     cookies and sessions; stateless vs stateful
     caching: Cache-Control, ETag, 304
     HTTP/1.1 vs 2 vs 3; head-of-line blocking; QUIC
     CORS and the preflight
M9   symmetric vs asymmetric; hashing vs encryption vs encoding
     certificates and the chain of trust
     the TLS handshake (1.2 and 1.3)
     what HTTPS does NOT hide
M10  the URL walkthrough at three depths
```

### Tier 2 — high priority at product companies

```
M3   IPv6: why, the address notation, dual stack
M4   OSPF areas; BGP path vector and why the internet needs it
     hierarchical routing
M6   Tahoe vs Reno vs CUBIC vs BBR; SACK; Nagle; silly window syndrome
     window scaling and long fat networks
M7   DoH/DoT; DNSSEC in brief; round-robin and GeoDNS
M8   WebSockets vs SSE vs polling; REST principles; HPACK
M9   firewalls stateless vs stateful; VPN and tunnelling
     MITM, DoS/DDoS, SYN flood, ARP/DNS spoofing, session hijacking
M10  load balancer, reverse proxy, CDN; latency budget arithmetic
```

### Tier 3 — good to know, one page each

```
M0   network topologies; MAN/WAN specifics; client-server vs P2P
M1   line coding; piggybacking; 2-D parity
M2   VLANs and trunking; spanning tree
M3   IPv6 transition mechanisms; ICMPv6 and NDP
M4   multicast and broadcast routing
M6   bufferbloat and ECN
M8   content negotiation and compression; server push and why it died
M9   HSTS, mixed content, forward secrecy details
M10  SMTP/IMAP/POP3, FTP vs SFTP, SSH, Telnet, SNMP, NTP
```

### Tier 4 — skip for placements

```
Session and presentation layer specifics (name them, move on)
Token ring, ATM, SONET, X.25, Frame Relay
Analogue modulation, signal theory, Shannon/Nyquist beyond the formula
Wireless PHY: OFDM, MIMO, 802.11 amendment letters
Router and switch configuration (Cisco IOS syntax)
SNMP MIBs, network management
```

---

## 4. Interview orientation (what the research says)

Seven observations that shaped the module weighting:

1. **"Explain the OSI model" is the single most predictable question in the subject.** It is asked almost verbatim, and it is asked *first*. A candidate who recites seven names and stops has failed it; the question is really "what happens at each layer", which is a one-minute answer about addressing and units.

2. **"What happens when you type a URL and press Enter" is the question that actually discriminates.** It appears in AWS's own engineering blog, across Medium and dev.to, and in a widely-shared LinkedIn post whose author says they are "shocked at how often" they ask it. It is the only question that touches every module, which is why M10 exists as its own file and teaches the answer at **three depths** — 30 seconds, 3 minutes, 10 minutes — because it gets asked at all three.

3. **Subnetting is front-loaded, not advanced.** InterviewBit's 2026 list has it at question 8. It is the one piece of arithmetic you may be asked to do on a whiteboard, so M3 drills the mechanical procedure rather than explaining the theory of masks.

4. **TCP vs UDP is never just a table.** The table is the setup; the real question is "you're designing a video call / a payment / a game leaderboard — which one and why", so M5 ends with decisions rather than properties.

5. **The written test and the interview want different modules.** GATE-style tests put **8–12 marks** on CN, almost all of it in M1 (sliding-window utilization, CRC, Hamming), M3 (subnetting) and M6 (congestion windows). Interviews put almost nothing there and almost everything in M5, M7, M8 and M10. This handbook covers both and tells you which is which, so you can skip accordingly.

6. **HTTP is now weighted like a core subject, not an application-layer footnote.** Status-code semantics, caching headers, CORS and the HTTP/2-vs-3 story come up constantly in backend interviews — more often than routing protocols do. M8 is sized accordingly, at four hours.

7. **Security questions stop at TLS.** Nobody asks an SDE candidate about cipher-suite internals; they ask what a certificate proves, what the handshake accomplishes, and the difference between hashing and encryption. M9 is pitched exactly there and marked Tier 1/2 rather than Tier 1.

---

## 5. Question map

Fifty questions the research says get asked, each pointing at the module that answers it. Use this backwards: pick a question, see if you can answer it, and if not go to that module.

| # | Question | Module |
|---|---|---|
| 1 | Explain the OSI model and what happens at each layer | M0 |
| 2 | OSI vs TCP/IP model — differences, and why we use one but teach the other | M0 |
| 3 | What is encapsulation? What is the PDU at each layer? | M0 |
| 4 | Which layer does a hub / switch / router / gateway work at? | M0, M2 |
| 5 | Collision domain vs broadcast domain | M0, M2 |
| 6 | Transmission delay vs propagation delay; what is the bandwidth-delay product? | M0 |
| 7 | Bandwidth vs throughput vs latency | M0 |
| 8 | How does CRC detect errors? Work this one out | M1 |
| 9 | Hamming code: how many redundant bits, and where do they go? | M1 |
| 10 | Error detection vs error correction; what is Hamming distance? | M1 |
| 11 | Stop-and-wait vs Go-Back-N vs Selective Repeat | M1 |
| 12 | Compute the utilization of a sliding-window protocol | M1 |
| 13 | How many bits does the sequence number need? | M1 |
| 14 | CSMA/CD vs CSMA/CA, and why Wi-Fi uses the second | M2 |
| 15 | Why does Ethernet have a minimum frame size? | M2 |
| 16 | Hub vs switch vs router | M2 |
| 17 | How does a switch learn where to forward? | M2 |
| 18 | What is ARP? What is ARP spoofing? | M2 |
| 19 | What is a MAC address, and how does it differ from an IP address? | M2 |
| 20 | Walk me through the IPv4 header | M3 |
| 21 | What is fragmentation and when does it happen? | M3 |
| 22 | Given 192.168.10.0/26, give the network, broadcast, range and host count | M3 |
| 23 | Design an address plan for 4 subnets of unequal size (VLSM) | M3 |
| 24 | What are the private IP ranges? What is 169.254.x.x? | M3 |
| 25 | What is NAT and what does it break? | M3 |
| 26 | Explain DHCP's DORA | M3 |
| 27 | What does `ping` send? What does `tracert` send? | M3 |
| 28 | Why IPv6, and how is an IPv6 address written? | M3 |
| 29 | Distance vector vs link state routing | M4 |
| 30 | What is count-to-infinity and how is it fixed? | M4 |
| 31 | RIP vs OSPF vs BGP | M4 |
| 32 | What is longest-prefix match? | M4 |
| 33 | Forwarding vs routing | M4 |
| 34 | TCP vs UDP — and which for video calls, payments, DNS, gaming? | M5 |
| 35 | Explain the three-way handshake. Why three and not two? | M5 |
| 36 | Explain the four-way close. What is a half-close? | M5 |
| 37 | Why does `TIME_WAIT` exist, and why do I have so many? | M5 |
| 38 | What does a lot of `CLOSE_WAIT` tell you? | M5 |
| 39 | What is a socket? What is the five-tuple? | M5 |
| 40 | What is a SYN flood and what is a SYN cookie? | M5, M9 |
| 41 | Flow control vs congestion control | M6 |
| 42 | Explain slow start, congestion avoidance and AIMD | M6 |
| 43 | Fast retransmit vs fast recovery; Tahoe vs Reno | M6 |
| 44 | How does TCP decide its retransmission timeout? | M6 |
| 45 | How does DNS resolution work, end to end? | M7 |
| 46 | Recursive vs iterative resolution | M7 |
| 47 | Name the DNS record types and what each is for | M7 |
| 48 | Why does DNS use UDP, and when does it use TCP? | M7 |
| 49 | GET vs POST vs PUT vs PATCH; which are safe and which idempotent? | M8 |
| 50 | 301 vs 302 vs 307; 401 vs 403; 502 vs 503 vs 504 | M8 |

And ten more that are asked just as often but do not fit the "one question one module" shape:

| # | Question | Module |
|---|---|---|
| 51 | How does HTTP caching work? What is an `ETag`? | M8 |
| 52 | Cookies vs sessions vs tokens; is HTTP stateless? | M8 |
| 53 | HTTP/1.1 vs HTTP/2 vs HTTP/3 — what problem did each solve? | M8 |
| 54 | What is head-of-line blocking, and where does it happen? | M6, M8 |
| 55 | What is CORS and why does my request fail only in the browser? | M8 |
| 56 | Symmetric vs asymmetric encryption; why use both? | M9 |
| 57 | Hashing vs encryption vs encoding | M9 |
| 58 | Walk me through the TLS handshake | M9 |
| 59 | What does a certificate actually prove? | M9 |
| 60 | What does HTTPS *not* hide? | M9 |

Plus the three "tell me everything" questions, which get their own treatment: **"what happens when you type a URL"** (M10), **"TCP vs UDP, fully"** (M5), and **"explain the OSI model"** (M0).

---

## 6. Numericals and protocol traces you must be able to do

### Numericals

| Numerical | Module | The procedure in one line |
|---|---|---|
| Transmission vs propagation delay | M0 | `T_t = L/B`, `T_p = d/v`. Everything else is built from these two |
| Bandwidth-delay product | M0 | `BDP = bandwidth × RTT` — the bits "in flight", and the window you need |
| Stop-and-wait utilization | M1 | `η = T_t / (T_t + 2T_p) = 1/(1+2a)` where `a = T_p/T_t` |
| Sliding-window utilization | M1 | `η = min(1, N/(1+2a))`, `N` = window size |
| Minimum window for full use | M1 | `N ≥ 1 + 2a`, rounded up |
| Sequence-number bits | M1 | Go-Back-N: `2^k ≥ N+1`. Selective Repeat: `2^k ≥ 2N` |
| CRC | M1 | Append `r` zeros, divide by the generator mod 2 (XOR), the remainder is the CRC |
| Hamming redundant bits | M1 | Smallest `r` with `2^r ≥ m + r + 1`; parity bits at positions `2^i` |
| Minimum Ethernet frame size | M2 | `L ≥ 2 × T_p × B` — the frame must still be sending when a collision returns |
| Subnet network/broadcast/range | M3 | AND with the mask; broadcast = network OR the wildcard; usable = `2^h − 2` |
| Number of subnets and hosts | M3 | Borrow `s` bits → `2^s` subnets, `2^(32−p) − 2` hosts each |
| VLSM address plan | M3 | Sort requirements descending, allocate the largest first, keep blocks aligned |
| Supernetting / aggregation | M3 | Find the longest common prefix of the blocks being merged |
| Fragmentation | M3 | Payload per fragment = `(MTU − 20)` rounded down to a multiple of 8; offsets are in 8-byte units |
| Dijkstra shortest paths | M4 | The DSA Part 14 algorithm, on the router's topology database |
| Distance-vector convergence | M4 | Iterate `D(x,y) = min over v of [c(x,v) + D(v,y)]` until stable; tabulate each round |
| Congestion-window trace | M6 | Slow start doubles per RTT to `ssthresh`, then +1 per RTT; on loss apply the Tahoe or Reno rule |
| Throughput from window and RTT | M6 | `throughput ≈ W / RTT`, capped by the link rate |
| Effective throughput with loss | M6 | Tier 3, but know that it falls roughly as `1/√p` |

Every one of these appears in Part 13 as a worked, computed example — and every number in the module files is produced by running code, not recalled.

### Protocol traces you must be able to draw from memory

| Trace | Module |
|---|---|
| Encapsulation: application bytes down to a frame on the wire, with every header | M0 |
| Stop-and-wait with a lost frame and a lost ACK | M1 |
| Go-Back-N and Selective Repeat on the same loss, side by side | M1 |
| A switch learning two MAC addresses and forwarding the third frame | M2 |
| ARP request (broadcast) and reply (unicast) | M2 |
| DHCP DORA, four messages | M3 |
| A packet fragmented into three, with offsets | M3 |
| Distance-vector tables over three rounds, including one link failure | M4 |
| The three-way handshake with real ISNs and flags | M5 |
| The four-way close, and where `TIME_WAIT` sits | M5 |
| `cwnd` over 12 RTTs through two loss events | M6 |
| DNS iterative resolution: root → TLD → authoritative | M7 |
| An HTTP request and response, header by header | M8 |
| The TLS 1.3 handshake, one round trip | M9 |
| The full URL walkthrough, all of the above in order | M10 |

---

## 7. Schedules

Pick the one that matches the time you have. All three assume you have already done DSA, OOP, OS and DBMS, since this handbook leans on them.

### 2 weeks (~1 h/day, ~14 h) — interview-focused

| Day | Work |
|---|---|
| 1 | M0 Tier 1: OSI, TCP/IP, encapsulation, devices, delays |
| 2 | M5: TCP vs UDP, handshake, close, states, `TIME_WAIT` |
| 3 | M6 part 1: sequence numbers, retransmission, flow control |
| 4 | M6 part 2: congestion control, slow start, AIMD, fast recovery |
| 5 | M3 part 1: IPv4 header, CIDR, subnetting arithmetic — drill it |
| 6 | M3 part 2: VLSM, NAT, DHCP, ICMP |
| 7 | M7 DNS, all of it |
| 8 | M8 part 1: methods, status codes, headers, caching, cookies |
| 9 | M8 part 2: HTTP/1.1 vs 2 vs 3, CORS, WebSockets |
| 10 | M2 Tier 1: hub/switch/router, Ethernet, ARP, CSMA |
| 11 | M9 Tier 1: crypto basics, certificates, the TLS handshake |
| 12 | **M10: the URL walkthrough.** Then say it out loud three times |
| 13 | Part 13: confusable pairs + 70 rapid-fire |
| 14 | M1 and M4 Tier 1 only — the concepts, skip the numericals |

### 1 month (~1 h/day, ~28 h) — complete

| Days | Work |
|---|---|
| 1–3 | M0 in full |
| 4–7 | M1 in full, numericals included |
| 8–10 | M2 in full |
| 11–15 | M3 in full, subnetting drilled daily |
| 16–19 | M4 in full |
| 20–23 | M5 in full |
| 24–28 | M6 in full |
| 29–31 | M7 and M8 |
| 32–35 | M9 and M10 |
| 36–37 | Part 13, twice |

*(That runs to 37 days at an hour a day; compress by doubling up on the lighter modules, or stretch it — the order is what matters.)*

### 2–3 months (~1 h on alternate days, alongside DSA) — recommended

One module per 3–4 days, in order, with Part 13 read at the end of every second week. This is the version that sticks, and it is what I would actually do.

### Revision passes

Six passes, each cheaper than the last:

| Pass | What you read | Time |
|---|---|---|
| 1 | The module, in full, doing the practice problems | the hours above |
| 2 | "Must remember" + "common wrong answers" of every module | 2 h |
| 3 | Part 13's confusable-pairs table, covering the right column | 45 min |
| 4 | Part 13's numericals sheet — work three of each from scratch | 1.5 h |
| 5 | Part 13's 70 rapid-fire, out loud | 40 min |
| 6 | **M10's URL walkthrough, said out loud at all three depths** | 15 min |

Pass 6 is the one to do on the morning of the interview. It touches every module, so it reloads the whole subject in a quarter of an hour.

---

## 8. Rules I will follow in every module

1. **Nothing computable is asserted.** Every numerical is produced by code that is self-tested against answers known in advance, and the real output is what goes in the notes.
2. **Where a result surprised me, it stays in** with the explanation, rather than being quietly replaced by the textbook answer. Three such findings already exist in the DBMS handbook and they are the most useful paragraphs in it.
3. **Live output is labelled as live**, and what cannot be verified here is labelled as *not executed* with the reason — never dressed up.
4. **Every confusable pair gets a table.** This subject is mostly such pairs.
5. **Every protocol gets a field-by-field header diagram**, and the notes say which fields an interviewer actually cares about.
6. **Cross-references to DSA, OOP, OS and DBMS go in the text**, so the fifth subject is partly revision of the first four.
7. **Tier 3 sections are one page and say so.** Tier 4 topics are named in a line and dismissed.
8. **Interview answers are written at interview length** — two to four sentences, not a paragraph.
9. **Windows commands are primary** (this is what can be verified here), with the Linux/macOS equivalent named beside each.
10. **The source notes are never edited by the site sync.** It only copies.
11. **No module is written ahead of its dependencies**, so the reading order in §1 is always safe.

---

## 9. Progress checklist

```
[ ] Part 1   Master roadmap (this file)
[ ] M0       Fundamentals and layering
[ ] M1       Framing and errors
[ ] M2       Medium access and the LAN
[ ] M3       IP addressing and subnetting
[ ] M4       Routing
[ ] M5       UDP and TCP connections
[ ] M6       TCP reliability and congestion control
[ ] M7       DNS
[ ] M8       HTTP and the web
[ ] M9       Network security
[ ] M10      What happens when you type a URL
[ ] Part 13  Consolidation
```

And the readiness test, which is stricter than the checklist:

```
[ ] I can explain all seven OSI layers in terms of what each one ADDRESSES
    and what its unit of data is -- not just name them
[ ] Given any address and mask, I can produce the network, broadcast, host
    range and usable count in under 30 seconds, without a calculator
[ ] I can design a VLSM plan for four subnets of unequal size
[ ] I can compute sliding-window utilization and the minimum window size
[ ] I can do a CRC division and a Hamming syndrome by hand
[ ] I can draw the three-way handshake and the four-way close with flags
[ ] I can explain TIME_WAIT from first principles, including the 2xMSL
[ ] I can distinguish flow control from congestion control in one sentence
    and say what each one protects
[ ] I can trace cwnd through two loss events under both Tahoe and Reno
[ ] I can describe DNS resolution from the root servers down
[ ] I can give the safe/idempotent classification of all the HTTP methods
[ ] I can explain what each of HTTP/2 and HTTP/3 fixed, and what it did not
[ ] I can walk through the TLS handshake and say what the certificate proves
[ ] I can say what HTTPS does NOT protect
[ ] I can answer "what happens when you type a URL" for 30 seconds,
    for 3 minutes, and for 10 minutes -- the same answer at three depths
```

---

## Next

**Part 2: M0 — Fundamentals and Layering.** Why layering exists at all; the **OSI seven layers** with what each one genuinely addresses and what its unit of data is; the **TCP/IP model** and the honest mapping between the two; **encapsulation** drawn as one picture from application bytes to a frame on the wire; protocol vs service vs interface; every network device and **which layer it works at**, including why a switch has no IP address; collision versus broadcast domains; and the **four delays** — transmission, propagation, queuing, processing — with bandwidth versus throughput versus latency and the **bandwidth-delay product**, all worked with real numbers, because every numerical in M1 and M6 is built out of them.

---

### Sources used for the interview-orientation and question-map sections

- InterviewBit — *70+ Top Networking Interview Questions (2026)*
- Unstop — *Top 100 Networking Interview Questions & Answers (2026)*
- HireStepX — *Computer Networks Interview India 2026: OSI Model, TCP/IP, HTTP and DNS*
- Intellipaat — *25+ Computer Networks Interview Questions (2026)*
- GATE Overflow — *Computer Networks subject page* (weightage: 8–12 marks in GATE CS)
- GO Classes for GATE CS — *Computer Networks marathon series* topic breakdown (data link flow control → Hamming/CRC/IP addressing → subnetting/supernetting/DV/LS → transport layer and TCP congestion control)
- AWS Mobile Blog — *What happens when you type a URL into your browser?*
- Assorted *"what happens when you type a URL"* write-ups on Medium and dev.to, and the LinkedIn discussion on how often the question is asked

Everything technical in the module files is verified on this machine per §0 — these sources were used only to decide **what to cover and how heavily**, never as the authority for a fact.
