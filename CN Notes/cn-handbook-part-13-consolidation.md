# Computer Networks Placement Handbook — Part 13
# Consolidation: Revision Sheets, Rapid-Fire and Worked Numericals

**Part 13 · 2 hours per pass · Requires: everything**

---

## How to use this file

This is what you read the night before, and the only file you read on the morning of an interview.

| Section | Use it for | Time |
|---|---|---|
| §13.1 **Layer map** | The one picture that holds the subject together | 10 min |
| §13.2 **Ports and protocols** | A one-mark question you should never lose | 5 min |
| §13.3 **Confusable pairs** | Every "X vs Y" in the subject | 30 min |
| §13.4 **Numericals procedures** | The ten computational question types, as steps | 20 min |
| §13.5 **70 rapid-fire** | Self-test. Cover the right column | 35 min |
| §13.6 **18 worked numericals** | All computed. Do them, then check | 45 min |
| §13.7 **The three big answers** | Said out loud | 15 min |
| §13.8 **Final exit checklist** | Am I done? | 10 min |

**The honest triage.** With one day: §13.4, §13.6 and the Tier 1 rows of §13.3 if a **written test** is coming; §13.5, §13.7 and §13.3 if an **interview** is coming. They are genuinely different files for different purposes.

**On the morning of an interview, read §13.7 only.** It touches every module, so it reloads the whole subject in fifteen minutes.

Every number in §13.6 is **program output**, and the scripts self-tested against known answers before producing it.

---

## 13.1 The layer map

```
 LAYER        ADDRESS   PDU      DEVICES          PROTOCOLS            MODULE
 ───────────────────────────────────────────────────────────────────────────────
 7 Application  names   message  proxy, LB(L7)    HTTP DNS SMTP SSH    M7 M8
 6 Presentation   --    data     --               (TLS sits ~here)     M9
 5 Session        --    data     --               --                    --
 4 Transport    PORT    segment  LB(L4), firewall TCP UDP QUIC         M5 M6
 3 Network      IP      packet   ROUTER           IP ICMP ARP* OSPF BGP M3 M4
 2 Data link    MAC     frame    SWITCH, bridge   Ethernet Wi-Fi PPP   M1 M2
 1 Physical      --     bit      hub, repeater    cables, radio        M1
                                 modem, NIC(1-2)
 ───────────────────────────────────────────────────────────────────────────────
 * ARP maps L3 to L2 and belongs to neither -- conventionally "layer 2.5"

 ENCAPSULATION, and the demultiplexing field at each step:
   [Eth hdr | IP hdr | TCP hdr | HTTP data | FCS]
      |          |         |
   EtherType  protocol   port      <- each says "what is inside me"
   0x0800     6=TCP      443
   0x0806=ARP 17=UDP
   0x86DD=v6  1=ICMP

 THE ONE FACT: IP addresses stay the same end to end.
               MAC addresses are REWRITTEN AT EVERY HOP.
   MAC is flat (cannot aggregate) -> cannot scale routing
   IP is hierarchical (prefixes aggregate) -> routing scales
   That is why both exist.

 SIZES:  MTU 1500 = the largest IP PACKET | MSS 1460 = 1500 - 20 - 20
         frame on the wire 1518 = 1460 + 20 + 20 + 18
         Ethernet's 18 bytes are NOT part of the MTU
         overhead per segment 58 bytes -> 96.2% efficient at full size,
         1.7% for a one-byte payload (which is why Nagle exists)
```

---

## 13.2 Ports and protocols

```
    20/21  FTP data/control  TCP   plaintext; carries IPs in PORT (breaks NAT)
       22  SSH / SFTP        TCP   SFTP IS SSH, not FTP
       23  Telnet            TCP   plaintext, obsolete
       25  SMTP              TCP   server-to-server mail
       53  DNS               UDP + TCP   TCP for truncation, AXFR, DoT/DoH
    67/68  DHCP server/client UDP  must be UDP: no address yet
       80  HTTP              TCP
      110  POP3              TCP   downloads AND DELETES
      123  NTP               UDP   a wrong clock breaks certs and tokens
      143  IMAP              TCP   leaves mail on the server, multi-device
      161  SNMP              UDP   amplification vector
      389  LDAP              TCP
      443  HTTPS / QUIC      TCP + UDP (HTTP/3)
      587  SMTP submission   TCP
      853  DNS over TLS      TCP
      993  IMAPS             TCP
      995  POP3S             TCP
     3306  MySQL             TCP
     3389  RDP               TCP
     5432  PostgreSQL        TCP
     6379  Redis             TCP
    27017  MongoDB           TCP

  RANGES: 0-1023 well known (privileged) | 1024-49151 registered
          49152-65535 dynamic/ephemeral

  ICMP TYPES: 0 echo reply | 8 echo request          -> ping
              3/0 net unreach | 3/1 host | 3/3 port
              3/4 FRAGMENTATION NEEDED, DF SET       -> path MTU discovery
              5 redirect | 11/0 TIME EXCEEDED        -> traceroute
```

---

## 13.3 Confusable pairs — the master table

Cover the right column and work down.

| Pair | The distinction in one line |
|---|---|
| **OSI vs TCP/IP** | 7 layers designed before the protocols vs 4 described after them. OSI is the shared vocabulary; TCP/IP is what runs |
| **Layer 2 vs layer 3 address** | MAC is rewritten at **every hop** and is flat; IP stays the same end to end and is hierarchical, so it aggregates |
| **Service vs protocol** | Service is **vertical** (what a layer offers above); protocol is **horizontal** (rules between peers) |
| **Connection-oriented vs reliable** | A connection can be ordered and still lose data. Reliability is a separate guarantee |
| **MTU vs MSS** | MTU 1500 is the largest **IP packet**; MSS 1460 is the largest **TCP payload** |
| **Transmission vs propagation delay** | `L/B` — size and rate, not distance. `d/v` — distance, not size or rate |
| **Bandwidth vs throughput vs goodput** | Capacity vs achieved rate vs useful bytes delivered |
| **Latency vs bandwidth** | Independent. A satellite has plenty of one and terrible other |
| **Hub vs switch vs router** | Floods everything, 1 collision domain / learns MACs, 1 per port / routes on IP, bounds broadcast domains |
| **Switch vs bridge** | Same function; bridge is the 2-port software ancestor |
| **Collision vs broadcast domain** | What can collide (one medium, split by a switch) vs what receives a broadcast (one network, split by a router or VLAN) |
| **Bit stuffing vs byte stuffing** | Insert a 0 after five 1s vs escape the flag byte — and the escape byte itself |
| **Parity vs checksum vs CRC** | Odd errors only / cheap sum, misses sum-preserving changes / polynomial division, bursts up to `r` guaranteed |
| **Detection vs correction** | "Is it wrong?" plus a retransmission, vs "which bit?" paid for on every frame |
| **`d_min ≥ s+1` vs `≥ 2t+1`** | Detect `s` errors vs **correct** `t` |
| **Stop-and-wait vs sliding window** | One frame in flight vs `N`. `U = 1/(1+2a)` vs `min(1, N/(1+2a))` |
| **Go-Back-N vs Selective Repeat** | Receiver window 1, discards out-of-order, cumulative ACKs, resends everything / window `N`, buffers, individual ACKs, resends one |
| **`2^k ≥ N+1` vs `2^k ≥ 2N`** | GBN's receiver accepts **one** number; SR's accepts a **window**, so two disjoint windows need `2N` |
| **CSMA/CD vs CSMA/CA** | Detects collisions during transmission vs avoids them and confirms by ACK, because a radio cannot hear while sending |
| **Hidden vs exposed terminal** | Two senders that cannot hear each other collide at the receiver vs a sender defers unnecessarily and wastes capacity |
| **ALOHA vs slotted ALOHA** | Vulnerable period 2 frame times vs 1, so `1/2e` vs `1/e` — exactly double |
| **ARP vs DHCP** | IP → MAC on this link vs "give me an IP at all" |
| **ARP request vs reply** | Request is **broadcast**, reply is **unicast** |
| **Classful vs CIDR** | Fixed /8, /16, /24 boundaries vs an explicit prefix length — which is what enabled subnetting, VLSM and aggregation |
| **Subnetting vs supernetting** | Split one block into smaller ones vs merge contiguous aligned blocks into one route |
| **VLSM vs fixed-length subnetting** | A different prefix per subnet, sized to need, vs one size for all |
| **Network vs broadcast address** | All-zero host bits vs all-one host bits. Neither is assignable |
| **Limited vs directed broadcast** | `255.255.255.255`, never forwarded, vs a subnet's own, now blocked by default |
| **Private vs public address** | RFC 1918 ranges, not routable on the internet, vs globally unique |
| **APIPA (`169.254.x.x`) vs private** | Self-assigned because **DHCP failed** — a diagnostic — vs a deliberate plan |
| **NAT vs PAT** | Rewrites the IP vs the IP **and the port**, so one address serves tens of thousands of flows |
| **NAT vs firewall** | Blocking unsolicited inbound is a **side effect** of having no translation entry, not a policy |
| **MF vs DF flag** | "More fragments follow" vs "do not fragment this" |
| **Fragmentation in IPv4 vs IPv6** | Routers may fragment vs routers **may not** — they return Packet Too Big |
| **Routing vs forwarding** | Building the table (software, seconds) vs consulting it (hardware, nanoseconds) |
| **RIB vs FIB** | The routing table vs the forwarding table derived from it |
| **Distance vector vs link state** | Tell your **neighbours** about **everyone** vs tell **everyone** about your **neighbours** |
| **Bellman-Ford vs Dijkstra** | Distributed, iterative, suffers count-to-infinity vs local, on a full topology, does not |
| **Split horizon vs poison reverse** | Stay silent vs advertise **infinity** — explicit beats ambiguous. Neither fixes 3-node loops |
| **IGP vs EGP** | Within an AS, shortest path, all routers yours vs between ASes, **policy**, zero trust |
| **RIP vs OSPF vs BGP** | Hop count, 15 max / bandwidth cost, areas / **path vector**, policy, TCP 179 |
| **Longest-prefix match vs metric** | Prefix length decides first; **metric breaks ties** |
| **Default route vs no route** | `0.0.0.0/0` matches everything with length 0, so it always loses to anything else |
| **TCP vs UDP** | Connection, reliable, ordered, flow+congestion control, 20–60 B, **byte stream** vs none of that, 8 B, **datagram** |
| **Byte stream vs datagram** | Two sends may arrive as one receive — you must frame your own messages — vs boundaries preserved |
| **Sequence vs acknowledgement number** | This segment's first **byte offset** vs the **next byte expected** |
| **FIN vs RST** | "I am finished" gracefully vs "this connection is invalid, discard it" |
| **Three-way vs four-way** | Opening needs 3 because each side must learn its own ISN arrived; closing needs 4 because the two directions are independent |
| **`TIME_WAIT` vs `CLOSE_WAIT`** | The kernel doing its job on the **active** closer, self-healing, vs **your application** failing to call `close()` |
| **Active vs passive close** | Sent the first FIN → `TIME_WAIT` vs received it → `CLOSE_WAIT` |
| **`shutdown()` vs `close()`** | Closes one direction and keeps receiving vs closes both |
| **Flow vs congestion control** | Protects the **receiver**, and the receiver **tells you the number** vs protects the **network**, and **nobody knows the number** |
| **`rwnd` vs `cwnd`** | A header field set by the receiver vs a value only in the sender's memory |
| **Slow start vs congestion avoidance** | **Exponential** (×2/RTT) to `ssthresh` vs **linear** (+1/RTT) after it |
| **AIMD vs AIAD** | Converges to fairness (verified 5.00→2.00) vs preserves the gap forever |
| **Fast retransmit vs fast recovery** | Resend on the 3rd duplicate ACK vs do not collapse `cwnd` to 1 afterwards. Reno added the second |
| **Tahoe vs Reno** | Any loss → `cwnd=1` vs distinguishes signals; **identical on a timeout** |
| **Reno vs CUBIC** | +1 per **RTT** (RTT-unfair) vs cubic in real **time** (RTT-fair), β=0.7 |
| **Loss-based vs delay-based** | Must fill a buffer to learn the limit — which is bufferbloat — vs models bandwidth and min RTT (BBR) |
| **Nagle vs delayed ACK** | Sender coalesces small writes vs receiver waits to piggyback. **Together they stall 200 ms** |
| **Silly window: Clark vs Nagle** | The receiver-side fix vs the sender-side fix |
| **Recursive vs iterative DNS** | You ask once and get the answer vs the server **refers** you onward. **Both happen in every lookup** |
| **Authoritative vs recursive server** | Holds the zone data vs does the walking and caches |
| **`NXDOMAIN` vs empty answer** | The name does not exist vs exists **without that record type** |
| **A vs CNAME** | Name → address vs name → **another name**, which cannot sit at the apex |
| **DNS TTL vs "propagation"** | Nothing propagates; caches **expire**, bounded by the TTL they last saw |
| **DNSSEC vs DoH/DoT** | **Signs** records (authenticity) vs **encrypts** the channel (confidentiality). Neither replaces the other |
| **Round-robin DNS vs a load balancer** | No health checking, bounded by TTL vs active checks and weighting |
| **GeoDNS vs anycast** | A different answer per location vs one address announced from many places, BGP picks |
| **Safe vs idempotent** | Changes nothing vs N calls equal 1 call. **`PUT` is idempotent and not safe** |
| **`POST` vs `PUT`** | Submit to a processor, not idempotent vs replace at a known URL, idempotent |
| **401 vs 403** | Not authenticated — credentials may help vs authenticated and forbidden — they never will |
| **404 vs 410** | Not found, may return vs **Gone**, deliberately permanent |
| **301 vs 302 vs 307 vs 308** | Permanent/temporary × may-change-method/must-preserve. 301 and 308 are **cached hard** |
| **500 vs 502 vs 503 vs 504** | The app threw vs the proxy got garbage upstream vs nothing available vs upstream never replied |
| **Freshness vs validation** | `max-age` avoids the **request** vs `ETag` avoids the **body** but costs a round trip |
| **`no-cache` vs `no-store`** | **Revalidate before use** vs genuinely do not store |
| **`ETag` vs `Last-Modified`** | Exact and opaque vs one-second resolution, so it misses two changes in a second |
| **Session vs token** | Opaque ID + server state, revocable, needs shared storage vs signed claims, stateless, hard to revoke |
| **`HttpOnly` vs `SameSite`** | Stops **XSS** reading the cookie vs addresses **CSRF** |
| **HTTP/1.1 vs 2 vs 3** | Keep-alive + `Host` vs multiplexed binary + HPACK vs QUIC with per-stream reliability |
| **Application vs TCP head-of-line blocking** | HTTP/2 fixed the first; only HTTP/3 fixes the second, by leaving TCP |
| **Pipelining vs multiplexing** | Several requests but **in-order responses** (so it failed) vs interleaved frames in any order |
| **Server push vs Early Hints** | Send unrequested resources (**abandoned** — the server cannot know the cache) vs just tell the client what to fetch |
| **CORS vs same-origin policy** | The opt-in mechanism vs the browser rule it relaxes. **Both are browser-side** |
| **Simple vs preflighted request** | Goes straight out vs an `OPTIONS` round trip first |
| **WebSocket vs SSE vs polling** | Full duplex after a `101` vs server→client over plain HTTP with auto-reconnect vs ask repeatedly |
| **Encoding vs hashing vs encryption** | No key, anyone reverses / no key, nothing reverses / key, reversible with it |
| **Hash vs MAC** | Integrity vs integrity **and** authenticity, because it is keyed |
| **Symmetric vs asymmetric** | One shared key, fast, key distribution is the problem vs a key pair, slow, solves distribution |
| **Encrypting vs signing** | Public key encrypts (confidentiality) vs **private** key signs (authenticity) |
| **Forward secrecy vs encryption** | A future key theft cannot decrypt **past** recorded traffic |
| **TLS 1.2 vs 1.3** | 2 RTT vs **1 RTT**, because the client guesses the key-exchange group |
| **Certificate vs trust** | Proves key control and domain validation; proves **nothing** about honesty — a lookalike domain can hold a valid one |
| **Stateless vs stateful firewall** | Headers in isolation, so inbound replies must all be allowed vs a connection table, so only established flows pass |
| **SYN flood vs DDoS** | **State** exhaustion, cheap for the attacker, fixed by SYN cookies vs **capacity** exhaustion, not a crypto problem |
| **Reverse vs forward proxy** | Acts for the **servers** (client unaware) vs for the **clients** (server unaware) |
| **L4 vs L7 load balancer** | Routes by the five-tuple, protocol-blind vs reads URLs and headers, terminates TLS |
| **SMTP vs IMAP vs POP3** | Sends vs reads leaving mail on the server, multi-device vs reads and deletes |
| **SFTP vs FTPS** | **SSH** on port 22 vs real FTP wrapped in TLS. Unrelated protocols |

---

## 13.4 Numericals procedure sheet

Ten computational types. Each is a procedure, not an insight.

### A. Delays and `a`

```
 T_t = L / B      L in BITS, B in bits/sec        (size and rate, not distance)
 T_p = d / v      v = 2x10^8 m/s in fibre/copper  (distance only)
 a   = T_p / T_t  <- THE parameter
 a << 1 transmission-bound (stop-and-wait is fine); a >> 1 MUST pipeline
```

### B. Bandwidth-delay product and window scaling

```
 BDP = bandwidth x RTT   (bits) -- the bits in flight, = the window you need
 bytes = BDP/8. Need scaling if > 65,535.
 scale factor = ceil(log2(bytes / 65535))
```

### C. ARQ utilization and sequence bits

```
 stop-and-wait  U = 1/(1+2a)
 window N       U = min(1, N/(1+2a))
 full use       N >= 1 + 2a        (ceil)
 throughput     U x bandwidth
 sequence bits  GBN: 2^k >= N+1    SR: 2^k >= 2N
 with ack time / processing: U = Tt/(Tt + 2Tp + Tack + 2Tproc)
 NOTE the formula is the STEADY-STATE limit; it ignores 2Tp of pipeline fill
```

### D. CRC

```
 1. r = (generator bits) - 1
 2. append r zeros to the data
 3. divide by the generator, mod 2 (XOR wherever the leading bit is 1)
 4. the r-bit remainder is the CRC; frame = data + CRC
 5. receiver divides the WHOLE frame; remainder 0 = accept
 guarantees: all single-bit; all bursts <= r; all ODD-weight errors IFF the
 generator has an EVEN number of terms (i.e. is divisible by x+1);
 longer bursts slip at 2^-r
```

### E. Hamming

```
 smallest r with 2^r >= m + r + 1     (m=26 -> 5 EXACTLY; m=27 -> 6)
 parity bits at positions 1,2,4,8,... (powers of two, 1-indexed)
 parity at p checks every position whose index has bit p set
 THE SYNDROME IS THE POSITION: failing checks SUM to the bad bit's index
 syndrome 0 = no error. Corrects ONE bit only.
```

### F. Minimum Ethernet frame

```
 T_t >= 2 T_p  ->  L >= 2 d B / v
 that is the FLOOR. Ethernet standardises 512 bits (64 B) because the 51.2 us
 slot time also budgets 4 repeaters, the 32-bit jam signal and PHY latency.
```

### G. ALOHA

```
 pure    S = G e^(-2G)   max 1/(2e) = 18.4% at G = 0.5
 slotted S = G e^(-G)    max 1/e    = 36.8% at G = 1.0
```

### H. Subnetting / VLSM / aggregation

```
 prefix   = count the 1 bits in the mask
 network  = address AND mask        wildcard = NOT mask
 broadcast= network OR wildcard     first = network+1   last = broadcast-1
 total = 2^(32-prefix)              usable = total - 2
 BLOCK SIZE = 2^(host bits) -- subnets start at MULTIPLES of it
   /25 128 | /26 64 | /27 32 | /28 16 | /29 8 | /30 4
 usable: /24 254 | /25 126 | /26 62 | /27 30 | /28 14 | /29 6 | /30 2
 borrow s bits -> 2^s subnets, each 2^(32-newprefix) - 2 hosts
 VLSM: sort LARGEST FIRST, smallest prefix that fits, blocks ALIGNED to their size
 aggregation: needs CONTIGUOUS blocks AND an ALIGNED combined block
```

### I. Fragmentation

```
 data per fragment = ((MTU - 20) // 8) * 8     <- rounded DOWN to a multiple of 8
 fragments = ceil(payload / that)
 offset field = byte offset / 8                <- 8-byte units
 MF = 1 on all but the last
 offsets stay ABSOLUTE when a fragment is fragmented again
```

### J. `cwnd` trace and throughput

```
 cwnd < ssthresh -> x2 per RTT (clamp to ssthresh)   else +1 per RTT
 on loss: ssthresh = cwnd/2
   Tahoe: cwnd = 1 (any loss)
   Reno:  timeout -> cwnd = 1; 3 dup ACKs -> cwnd = ssthresh
 throughput ~= W / RTT         and falls as 1/sqrt(loss rate)
 RTO: SRTT = 7/8 SRTT + 1/8 sample; RTTVAR = 3/4 RTTVAR + 1/4 |SRTT - sample|
      RTO = SRTT + 4 RTTVAR, floor 1 s; double on each timeout (Karn)
```

---

## 13.5 Seventy rapid-fire questions

Cover the right column.

| # | Question | Answer |
|---|---|---|
| 1 | Seven OSI layers, bottom up? | Physical, data link, network, transport, session, presentation, application |
| 2 | Address and PDU at layers 2, 3, 4? | MAC/frame, IP/packet, port/segment |
| 3 | What changes at every hop? | Both MAC addresses, TTL, the header checksum. **Not** the IP addresses |
| 4 | Why both MAC and IP? | MAC is flat and cannot aggregate into routes; IP is hierarchical so routing scales |
| 5 | Which layer is a switch? A router? | 2 (MAC), 3 (IP) |
| 6 | MTU vs MSS on Ethernet? | 1500 (IP packet) vs 1460 (TCP payload) |
| 7 | Frame size for a full segment? | 1518 = 1460 + 20 + 20 + 18 |
| 8 | Transmission vs propagation delay? | `L/B`, size and rate. `d/v`, distance only |
| 9 | What is `a`? | `Tp/Tt`. Much less than 1 → transmission-bound; much more → must pipeline |
| 10 | What is the BDP? | Bandwidth × RTT — bits in flight, and the window you need |
| 11 | Why does TCP need window scaling? | 16-bit field caps at 64 KB, exhausted by 1 Gbps at 0.52 ms RTT |
| 12 | Throughput over a path? | The **minimum** — the bottleneck link |
| 13 | Collision vs broadcast domain? | What can collide (split by a switch) vs what gets broadcasts (split by a router/VLAN) |
| 14 | Bit stuffing rule? | Insert a 0 after five consecutive 1s, unconditionally. 20% worst case |
| 15 | Byte stuffing trap? | The escape character must itself be escaped |
| 16 | What does parity miss? | Any **even** number of errors |
| 17 | How does the receiver check an Internet checksum? | Sums everything **including** the checksum and expects `0x0000` |
| 18 | Why is IP's checksum weak? | It is recomputed at every hop. IPv6 removed it entirely |
| 19 | CRC burst guarantee? | All bursts ≤ `r`; longer ones slip at `2^-r` |
| 20 | When does CRC catch all odd-weight errors? | When the generator is divisible by `(x+1)` — an **even** number of terms |
| 21 | Detect `s` vs correct `t` errors? | `d_min ≥ s+1` vs `d_min ≥ 2t+1` |
| 22 | Hamming redundant bits? | Smallest `r` with `2^r ≥ m+r+1` |
| 23 | Where do parity bits go, and why? | Powers of two, so the failing checks **sum to** the error position |
| 24 | What does Hamming do with two errors? | Points at a third, innocent bit. SECDED detects instead |
| 25 | Stop-and-wait utilization? | `1/(1+2a)` |
| 26 | Window for full utilization? | `N ≥ 1+2a` — the BDP in frames |
| 27 | GBN vs SR on loss? | Resends the frame **and everything after** vs only the lost one |
| 28 | Sequence bits for each? | `2^k ≥ N+1` vs `2^k ≥ 2N` |
| 29 | Why `2N` for SR? | Its receiver accepts a whole window, so old and new windows must not overlap |
| 30 | Slotted vs pure ALOHA max? | `1/e` = 36.8% vs `1/2e` = 18.4% — the vulnerable period halves |
| 31 | Why a minimum Ethernet frame? | A sender must still be transmitting when the collision returns: `L ≥ 2dB/v` |
| 32 | Why can't Wi-Fi detect collisions? | A radio cannot listen while transmitting; and hidden terminals collide at the receiver |
| 33 | How does CSMA/CA know it failed? | A **missing ACK** |
| 34 | What does a switch learn from? | The **source** MAC of every frame |
| 35 | ARP request vs reply? | Broadcast vs unicast |
| 36 | What decides whether you ARP the host or the gateway? | The subnet mask |
| 37 | Why is ARP spoofing easy? | ARP has **no authentication** and hosts accept unsolicited replies |
| 38 | Why does STP exist? | An Ethernet frame has **no TTL**, so a loop becomes a broadcast storm |
| 39 | Give the network and broadcast for `192.168.1.130/25` | `192.168.1.128` and `192.168.1.255`, 126 usable |
| 40 | Block size for `/27`? | 32 |
| 41 | Why `2^h − 2`? | All-zero host bits are the network, all-ones the broadcast |
| 42 | Three private ranges? | `10/8`, `172.16/12` (to `172.31.255.255`), `192.168/16` |
| 43 | What does `169.254.x.x` mean? | APIPA — **DHCP failed** |
| 44 | NAT vs PAT? | Rewrites the IP vs the IP and port, so one address serves tens of thousands of flows |
| 45 | Is NAT security? | Incidentally — no translation entry for unsolicited inbound. Not a policy |
| 46 | DHCP's four messages? | Discover, Offer, Request, Acknowledge — over UDP 67/68 |
| 47 | Why is DHCP Request broadcast? | So declined servers release their reservations |
| 48 | Data per fragment? | `((MTU − 20) // 8) × 8` |
| 49 | Where does reassembly happen? | Only at the **final destination** |
| 50 | What does `ping` send? | ICMP Echo Request (type 8) |
| 51 | What makes traceroute work? | Increasing TTL and the ICMP Time Exceeded each router returns |
| 52 | What breaks if you block all ICMP? | Path-MTU discovery (type 3 code 4) → black-hole connections |
| 53 | Routing vs forwarding? | Building the table vs consulting it |
| 54 | Longest-prefix match, and ties? | Longest prefix wins; **metric** breaks ties |
| 55 | DV vs LS in one line? | Tell neighbours about everyone vs tell everyone about neighbours |
| 56 | What is count-to-infinity? | A router learns a route whose path goes back through itself; the cost climbs slowly |
| 57 | Why is RIP's infinity 16? | To **bound** count-to-infinity |
| 58 | Does split horizon fix it? | Two-node loops only. Three or more survive it |
| 59 | What makes BGP a path vector? | It advertises the full **AS path**, so loop detection is exact and policy is expressible |
| 60 | Why does BGP use TCP? | ~1 million routes must arrive reliably, in order, and **incrementally** |
| 61 | Five-tuple? | Protocol, both addresses, both ports |
| 62 | Why three-way and not two? | Each side must learn **its own** ISN was received |
| 63 | What is a SYN flood, really? | **State** exhaustion. SYN cookies hold no state until the final ACK |
| 64 | Why four-way close? | Two independent byte streams, each closed separately |
| 65 | What does `recv()` returning 0 mean? | The peer sent FIN. Not an error, not an empty message |
| 66 | Why does `TIME_WAIT` exist? | To ACK a retransmitted FIN, and to let delayed duplicates expire before the tuple is reused |
| 67 | What does lots of `CLOSE_WAIT` mean? | **Your application** is not calling `close()` — a descriptor leak |
| 68 | Flow vs congestion control? | Protects the receiver, who tells you the number, vs the network, where nobody does |
| 69 | Is slow start slow? | No — it **doubles** every RTT. The name is relative to original TCP |
| 70 | Why halve on loss? | **Fairness** — AIMD converges, AIAD preserves the gap forever |

And ten more on the application and security layers:

| # | Question | Answer |
|---|---|---|
| 71 | Recursive vs iterative DNS? | You ask once and get the answer vs the server refers you onward. **Both** in every lookup |
| 72 | What is the TTL you receive? | **Seconds remaining** — the cache decrements it |
| 73 | What is "DNS propagation"? | A misnomer. Caches **expire**, bounded by the TTL they last saw |
| 74 | Why does DNS use UDP? | A 28-byte question and a small answer; a handshake would add a round trip first |
| 75 | DNSSEC vs DoH? | **Signs** vs **encrypts**. Different threats, neither replaces the other |
| 76 | Safe vs idempotent, with the clarifying example? | `PUT` is idempotent but **not safe** |
| 77 | 401 vs 403? | Not authenticated vs authenticated and forbidden |
| 78 | `no-cache` vs `no-store`? | Revalidate before use vs do not store |
| 79 | Where is head-of-line blocking after HTTP/2? | In **TCP** — one lost segment stalls every stream. Only HTTP/3 fixes it |
| 80 | Who enforces CORS? | The **browser**. The server answered the request |

---

## 13.6 Eighteen worked numericals

**Every number below is program output.** Cover the answers, work them, then check.

**N1 — delay and `a`**
```
   L=12000b B=1e+08 d=300m       -> Tt=0.1200ms Tp=0.0015ms a=0.0125
   L=12000b B=1e+10 d=3000000m   -> Tt=0.0012ms Tp=15.0000ms a=12500.0000
```
A 1500-byte frame on a 100 Mbps LAN is transmission-bound (`a` ≈ 0.01); the same frame on a 10 Gbps intercontinental link has `a = 12,500`. Same frame, four orders of magnitude apart.

**N2 — BDP and the window-scale factor**
```
   500Mbps x 30ms  = 15,000,000 bits  = 1,875,000 B;  scale factor 5
   1000Mbps x 200ms = 200,000,000 bits = 25,000,000 B; scale factor 9
```

**N3 — stop-and-wait, minimum window, sequence bits**
```
   Tt=1.000ms Tp=10.0ms  a=10.00  U_sw=4.762%  Nmin=21  GBN k=5  SR k=6
   Tt=1.000ms Tp=270.0ms a=270.00 U_sw=0.185%  Nmin=541 GBN k=10 SR k=11
```
The second is a satellite link: stop-and-wait delivers **0.185%** of capacity, and full use needs a window of 541 frames.

**N4 — utilization and throughput at a given `N`** (2 Mbps, `a = 10`)
```
   N=8:  U=38.095%  throughput=0.7619 Mbps of 2 Mbps
   N=21: U=100.000% throughput=2.0000 Mbps of 2 Mbps
```

**N5 — CRC**
```
   data 110101     gen 1011  -> CRC 111,  frame 110101111
   data 1101011011 gen 10011 -> CRC 1110, frame 11010110111110
```

**N6 — Hamming redundant bits**
```
   m=4->r=3  m=8->r=4  m=12->r=5  m=16->r=5  m=26->r=5  m=27->r=6  m=32->r=6  m=64->r=7
```
`m = 26` is the boundary: `2⁵ = 32 ≥ 26+5+1 = 32` exactly, and 27 needs six.

**N7 — minimum Ethernet frame**
```
   10Mbps 1000m: 2Tp=10.00us -> floor 100 bits = 12.5 B  (standard 64 B)
   100Mbps 250m: 2Tp=2.50us  -> floor 250 bits = 31.3 B  (standard 64 B)
```
The formula gives the **floor**; 64 bytes is the standardised value, because the slot time also budgets repeaters, the jam signal and PHY latency.

**N8 — ALOHA**
```
   pure max 0.18394 at G=0.5 | slotted max 0.36788 at G=1.0
   G=0.2: pure 0.13406  slotted 0.16375
   G=0.5: pure 0.18394  slotted 0.30327
   G=1.0: pure 0.13534  slotted 0.36788
```
Note pure ALOHA at `G = 1.0` delivers **less** than at `G = 0.5` — past the optimum, more load means less throughput.

**N9 — subnetting**
```
   10.20.30.40/26     mask 255.255.255.192 net 10.20.30.0    bcast 10.20.30.63    range .1-.62        usable 62
   172.20.100.200/22  mask 255.255.252.0   net 172.20.100.0  bcast 172.20.103.255 range .100.1-.103.254 usable 1,022
   192.168.5.77/29    mask 255.255.255.248 net 192.168.5.72  bcast 192.168.5.79   range .73-.78       usable 6
```
The `/22` lands in the **third** octet: block size 4, multiples 0, 4, 8 … 100, so `100` is itself a network boundary.

**N10 — subnets and hosts from borrowed bits**
```
   /24 -> /27: 8 subnets of 30 usable;    was 254,    now 240,    lost 14
   /22 -> /27: 32 subnets of 30 usable;   was 1,022,  now 960,    lost 62
   /16 -> /20: 16 subnets of 4094 usable; was 65,534, now 65,504, lost 30
```
Subnetting always **loses** addresses — two per new subnet. That loss is the question's real target.

**N11 — VLSM on `10.50.0.0/16`**
```
   A: need 4000 -> /20 at 10.50.0.0    10.50.0.1-10.50.15.254  usable 4,094
   B: need 2000 -> /21 at 10.50.16.0   10.50.16.1-10.50.23.254 usable 2,046
   C: need  500 -> /23 at 10.50.24.0   10.50.24.1-10.50.25.254 usable 510
   D: need   60 -> /26 at 10.50.26.0   10.50.26.1-10.50.26.62  usable 62
   E: need    2 -> /30 at 10.50.26.64  10.50.26.65-10.50.26.66 usable 2
   free: 58,812
```

**N12 — aggregation**
```
   192.168.8.0/24 .. 192.168.11.0/24 -> ['192.168.8.0/22']
   192.168.5.0/24 .. 192.168.8.0/24  -> ['192.168.5.0/24', '192.168.6.0/23', '192.168.8.0/24']
```
The first four are contiguous **and** aligned, so they collapse. The second four are contiguous and **misaligned**, so the best possible is three routes — partial aggregation is the normal outcome.

**N13 — fragmentation**
```
   payload 4980 over MTU 1500: 1480 B/frag -> 4 fragments
     #1 offset     0 (field    0) data  1480 MF 1
     #2 offset  1480 (field  185) data  1480 MF 1
     #3 offset  2960 (field  370) data  1480 MF 1
     #4 offset  4440 (field  555) data   540 MF 0

   payload 4980 over MTU 576:  552 B/frag -> 10 fragments
     #1 offset 0 (field 0) ... #10 offset 4968 (field 621) data 12 MF 0
```
Note the last fragment carries only **12 bytes** — the remainder after nine full ones. Offsets stay absolute within the original packet.

**N14 — `cwnd` traces** (`ssthresh = 16`, event at RTT 7)
```
   Tahoe, timeout:   [1, 2, 4, 8, 16, 17, 18, 19, 1, 2, 4, 8, 9, 10]
   Reno,  3-dup ACK: [1, 2, 4, 8, 16, 17, 18, 19, 9, 10, 11, 12, 13, 14]
```
Both set `ssthresh = 19/2 = 9`. Tahoe restarts at 1 and takes four RTTs to get back to 9; Reno is there immediately.

**N15 — throughput from window and RTT**
```
   W=65,535B  RTT=60ms -> 8.74 Mbps
   W=500,000B RTT=60ms -> 66.67 Mbps
```

**N16 — RTO after a spike**
```
    sample  60 SRTT   60.00 RTTVAR  30.00 RTO  180.00
    sample  62 SRTT   60.25 RTTVAR  23.00 RTO  152.25
    sample  58 SRTT   59.97 RTTVAR  17.81 RTO  131.22
    sample  61 SRTT   60.10 RTTVAR  13.62 RTO  114.57
    sample 200 SRTT   77.59 RTTVAR  45.19 RTO  258.34
    sample  60 SRTT   75.39 RTTVAR  38.29 RTO  228.54
    sample  59 SRTT   73.34 RTTVAR  32.81 RTO  204.59
```
One 200 ms sample moved `SRTT` by 29% and **`RTTVAR` by 232%**, more than doubling the RTO — and it is still elevated three samples later. The estimator is quick to widen and slow to narrow.

**N17 — RTT floor and cold-load time**
```
   Singapore-Virginia 15000km: one-way 75.0ms, RTT floor 150.0ms
     HTTP/1.1+TLS1.2  5 RTT = 750 ms
     +TLS1.3          4 RTT = 600 ms
     HTTP/3           3 RTT = 450 ms
     warm             1 RTT = 150 ms

   Mumbai-London 7200km: one-way 36.0ms, RTT floor 72.0ms
     HTTP/1.1+TLS1.2  5 RTT = 360 ms   +TLS1.3 288 ms   HTTP/3 216 ms   warm 72 ms
```

**N18 — encapsulation efficiency**
```
   payload    1 -> frame   59, efficiency 1.7%
   payload  100 -> frame  158, efficiency 63.3%
   payload  536 -> frame  594, efficiency 90.2%
   payload 1460 -> frame 1518, efficiency 96.2%
```

---

## 13.7 The three big answers

Read these aloud. **This is the section to read on the morning of an interview** — it touches every module.

### 1. "Explain the OSI model"

> "Seven layers, each solving one problem and handing an opaque payload downward. The useful way to hold it is that **each layer has its own address type and its own name for a chunk of data**.
>
> Physical moves bits as signals. Data link moves **frames** across a single link using **MAC addresses** and detects corruption with a CRC. Network moves **packets** host to host across many networks using **IP addresses** and routing. Transport moves **segments** process to process using **port numbers**, and optionally adds reliability, flow control and congestion control. Session manages a conversation, presentation handles encoding and encryption, and application defines what the bytes mean.
>
> The fact that ties it together: **the IP addresses stay the same from source to destination, and the MAC addresses are rewritten at every hop.** That is end-to-end versus hop-by-hop addressing, and it is why both exist — MAC is flat so it cannot be aggregated into routes, while IP is hierarchical so routing scales.
>
> In practice we run TCP/IP, which has four layers and folds session and presentation into the application. OSI survives as the shared vocabulary — when someone says 'layer 7 load balancer', that number is OSI's."

### 2. "TCP vs UDP"

> "TCP is connection-oriented, reliable, ordered, and has both flow and congestion control, with a 20-to-60-byte header and a **byte-stream** model. UDP is connectionless with an 8-byte header, no reliability, ordering or congestion control, and preserves **message boundaries**. TCP also costs a round trip before any data moves; UDP costs nothing.
>
> Two things people get wrong. First, TCP is a byte stream, not a message stream — two sends may arrive as one receive, so any protocol over TCP has to frame its own messages. Second, UDP's more consequential omission is not reliability but **congestion control**: a greedy UDP flow does not back off and crowds out TCP flows, which is why QUIC and WebRTC implement their own.
>
> The choice is never abstract. Use UDP when **a late packet is worse than a missing one** — voice, video, game state — or when the exchange is one small request and response, like DNS, where a handshake would triple the round trips. Use TCP when every byte matters and latency does not. And the same application often uses both: a game sends position updates over UDP and chat over TCP, and live video uses UDP while on-demand video uses TCP, because buffering leaves time to retransmit."

### 3. "What happens when you type a URL?"

> "The browser parses the input and checks its **HSTS** list, upgrading to HTTPS before any packet leaves.
>
> Then **DNS**: four caches in sequence — browser, OS, router, recursive resolver — and most lookups stop in one. On a miss the resolver walks the hierarchy iteratively, root to TLD to authoritative, and the answer carries a TTL.
>
> With an address, the host **ANDs it with its own subnet mask**. Same network, it ARPs for the destination; different network, it ARPs for the gateway. Either way the frame carries the server's IP and the router's MAC.
>
> Then the **TCP handshake** — one round trip, which also negotiates MSS, window scaling and SACK. Then **TLS**: the client sends its versions and the SNI in plaintext, the server returns its certificate chain, the client checks the chain to a trusted root and that the name is in the SAN list, and both derive an ephemeral key — one round trip in TLS 1.3, two in 1.2. ALPN picks HTTP/2 here too.
>
> Then the **HTTP request**, with conditional headers if we have a cached copy — a 304 returns no body at all. The response may come from a CDN edge, or pass through a load balancer and reverse proxy to an application and database. Finally the browser parses the HTML and repeats this for every subresource, usually on the same connection.
>
> And the thing worth adding: **the cost is round trips, not bytes.** A cold load is four or five of them; warm it is one; fully cached it is zero. I measured a small page recently and **setup — DNS, TCP and TLS — was 57% of the total**, with the body transfer at effectively zero. That is why every optimisation here removes a round trip rather than adding bandwidth, and why a CDN is the strongest lever: it shortens the distance, so it shrinks *every* round trip at once."

---

## 13.8 Final exit checklist for the subject

```
FOUNDATIONS
[ ] Seven OSI layers with the ADDRESS and PDU of each
[ ] What changes per hop and what does not, and why both address types exist
[ ] OSI vs TCP/IP, and why OSI is still taught
[ ] Encapsulation with the demultiplexing field at each layer
[ ] MTU 1500 / MSS 1460 / frame 1518, and the 58-byte overhead
[ ] Device-to-layer for every device in the table
[ ] Collision vs broadcast domains, and counting them
[ ] The four delays; T_t vs T_p; a = Tp/Tt and both extremes
[ ] Bandwidth vs throughput vs goodput vs latency; throughput = the minimum
[ ] BDP, and why TCP needs window scaling

DATA LINK
[ ] Bit stuffing (unconditional, 20% worst case) and byte stuffing (escape the escape)
[ ] Parity misses all even errors; the checksum invariant is 0x0000
[ ] CRC by hand, and all four guarantees including the 2^-r slip rate
[ ] Odd-weight detection iff the generator has an even number of terms
[ ] d_min >= s+1 vs 2t+1; Hamming r from 2^r >= m+r+1 (26 is the boundary)
[ ] Parity bits at powers of two, and why the syndrome IS the position
[ ] U = 1/(1+2a); N >= 1+2a; throughput = U x bandwidth
[ ] GBN vs SR on every axis; the N+1 and 2N bounds DERIVED, not quoted
[ ] ALOHA 1/2e and 1/e, and why slotting exactly doubles it
[ ] CSMA/CD, the min-frame derivation, and the floor-vs-standard gap
[ ] Why wireless cannot detect collisions, all three reasons
[ ] CSMA/CA with the frozen backoff and the ACK as the only signal
[ ] Ethernet frame field by field; MAC structure and the I/G bit
[ ] Switch learning from SOURCE addresses; flooding; MAC flooding attacks
[ ] ARP: request broadcast, reply unicast, and the mask decides the target

NETWORK
[ ] IPv4 header; IHL in words; offset in 8-byte units; checksum header-only
[ ] The 8-step subnetting procedure in under 30 seconds
[ ] Block sizes and the /24 usable table from memory
[ ] VLSM largest-first, with alignment, and why alignment is forced
[ ] Aggregation, and that partial aggregation is normal
[ ] The three private ranges; 169.254 as a DHCP-failure diagnostic
[ ] NAT vs PAT; six things NAT breaks; NAT is not a firewall
[ ] DORA, why it is UDP, and why Request is broadcast
[ ] Fragmentation arithmetic; destination-only reassembly; one lost fragment
[ ] ICMP types for ping, traceroute and path-MTU discovery
[ ] IPv6: the arithmetic, the fixed header, no broadcast, SLAAC, NDP

ROUTING
[ ] Routing vs forwarding; longest-prefix match; metric breaks ties
[ ] The 8 per-packet steps at a router
[ ] DV vs LS on all twelve axes, and the one-line summary
[ ] Count-to-infinity: both causes, the trace, and why split horizon is partial
[ ] Dijkstra producing a forwarding table of FIRST HOPS
[ ] RIP / OSPF / BGP; path vector; why BGP uses TCP; BGP hijacking
[ ] The four levels of hierarchy that make internet routing scale

TRANSPORT
[ ] Five-tuple; why 65,535 is not a server limit
[ ] UDP's 8 bytes; four reasons to choose it
[ ] TCP header; seq counts BYTES; ack is the NEXT byte; FIN vs RST
[ ] Three-way handshake and WHY three; random ISNs; SYN flood and cookies
[ ] Four-way close; half-close; recv() == 0 IS the FIN
[ ] The state machine; active vs passive close
[ ] TIME_WAIT's two reasons; it lands on the first FIN sender; reuse is the fix
[ ] CLOSE_WAIT is an application bug, and the contrast with TIME_WAIT
[ ] TCP vs UDP table, and the decision for ten scenarios

CONGESTION
[ ] Flow vs congestion control, stated so the difference is obvious
[ ] Zero window and the persist timer; silly window from BOTH sides
[ ] Nagle precisely, and the delayed-ACK interaction
[ ] Slow start is EXPONENTIAL; congestion avoidance is +1/RTT
[ ] AIMD as a FAIRNESS argument, and why AIAD fails
[ ] Tahoe vs Reno traces; Reno on a timeout IS Tahoe
[ ] Fast retransmit vs fast recovery
[ ] CUBIC's equation, curve shape, and RTT fairness
[ ] BBR measures bandwidth and min RTT; bufferbloat; ECN
[ ] throughput = W/RTT; the 5.2 Mbps figure; 1/sqrt(p)
[ ] SRTT/RTTVAR/RTO, why variance is in it, and Karn's both halves

APPLICATION
[ ] DNS hierarchy; recursive AND iterative in every lookup; glue records
[ ] 10 record types; CNAME's two restrictions; per-link TTLs
[ ] TTL is seconds remaining; "propagation" is cache expiry
[ ] The TTL-lowering migration procedure, including the wait
[ ] NXDOMAIN vs empty answer; negative caching
[ ] Why DNS is UDP and the four cases for TCP; EDNS0 and 1232
[ ] Round-robin's three limits; GeoDNS and anycast vs the RTT floor
[ ] HTTP structure; why Host is mandatory; chunked encoding
[ ] Safe vs idempotent, with PUT as the clarifying case
[ ] 401/403, 404/410, 301/302/307/308, 500/502/503/504
[ ] Freshness vs validation; no-cache vs no-store; ETag vs Last-Modified; Vary
[ ] Statelessness; cookie attributes and what each prevents; session vs token
[ ] HTTP/1.1 vs 2 vs 3; ALPN chooses it; head-of-line blocking AT BOTH LAYERS
[ ] Why HTTP/3 left TCP; what QUIC adds; why server push was abandoned
[ ] CORS is BROWSER-enforced; the preflight; not server-side security

SECURITY
[ ] Five attack classes and five different defences
[ ] Encoding vs hashing vs MAC vs encryption, by key and reversibility
[ ] Why a fast hash is wrong for passwords; salts; memory hardness
[ ] Symmetric vs asymmetric and why both; Diffie-Hellman; forward secrecy
[ ] Signing uses the PRIVATE key, on the HASH
[ ] The chain of trust and all six validation checks
[ ] Disabling verification keeps encryption and destroys authentication
[ ] What a certificate does and does not prove
[ ] TLS 1.2 and 1.3 handshakes; how 1.3 saves an RTT; what the Finished MAC stops
[ ] What TLS 1.3 removed and why, for four items
[ ] What HTTPS hides and what it leaves visible, including SNI
[ ] Stateless vs stateful firewalls; why over-blocking ICMP causes black holes
[ ] A VPN MOVES trust rather than adding it
[ ] Ten attacks with their defences; amplification and BCP 38; HSTS

END TO END
[ ] The nine-phase walkthrough from memory
[ ] The round-trip count for five scenarios, converted to ms
[ ] Setup was 57-63% of a small page load; the body was 0.0 ms
[ ] Eight techniques mapped to the phases they remove
[ ] Why the CDN is the strongest lever
[ ] Diagnosing by failure SHAPE: hang vs refused vs headers-then-hang
[ ] The server tier; L4 vs L7; reverse vs forward proxy
[ ] 15 application protocols with ports; SMTP vs IMAP vs POP3; SFTP is SSH
[ ] All three big answers, out loud, at the right depth
```

---

## Where this handbook sits

Five subjects are now complete in this format, and they interlock deliberately:

| Handbook | What it gives this one |
|---|---|
| **DSA** | Dijkstra and Bellman-Ford for routing (Part 14); tries for longest-prefix match (Part 17); XOR and polynomial arithmetic for CRC (Part 4); heaps for top-N |
| **OOP** | Nothing directly — the one subject this leans on least |
| **OS** | Sockets as file descriptors and `select`/`epoll` (M3, M10); process states as the model for the TCP state machine (M2); queuing and buffering (M7) |
| **DBMS** | M10's load balancers, CDNs, caching and read replicas are the other half of CN M10's server tier; SQL injection (M6) is the application-layer half of CN M9 |
| **CN** | The transport, naming, HTTP and TLS reasoning that the system-design round is built on |

**What remains**, and it is now the last piece: a **thin HLD / system-design handbook**. DBMS M10 and CN M8/M10 have both pre-loaded it — between them you already have CAP, sharding, replication, consistent hashing, caching patterns, load balancers, CDNs, proxies, the latency budget and the N+1 problem. The handbook would mostly be assembling those into the standard design questions rather than teaching new material.

**And the standing advice for this subject:** of everything here, **§13.7 is what you will actually be asked**. Re-read it, say it out loud, and time yourself. If you can give the URL walkthrough at three depths and pick the right one, the round is yours.
