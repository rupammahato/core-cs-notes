# Computer Networks Placement Handbook — Part 2
# Module 0: Fundamentals and Layering

**Module 0 · 3 hours · Tier 1 · Requires: nothing**

---

## Why this module matters

Two things come out of this module, and they are the two things everything else is built on.

The first is **"explain the OSI model"** — the most predictable question in the subject, asked almost verbatim and asked *first*. Reciting seven names fails it. The question means "what happens at each layer", and the answer is about **what each layer addresses** and **what it calls its unit of data**. Get that and the related questions — which layer is a switch, which is a router, where does encapsulation happen — all answer themselves.

The second is **the delay model**: transmission versus propagation delay, and the bandwidth-delay product. That sounds like dry arithmetic, and it is the single highest-leverage thing in this handbook, because:

- M1's sliding-window utilization formula is **nothing but a ratio of those two delays**
- M2's minimum Ethernet frame size is **a propagation-delay constraint**
- M6's "throughput ≈ window / RTT" is **the bandwidth-delay product restated**
- M10's "why does the first page load feel slow" is **an RTT budget**

So this module is cheap and it unlocks four others. Do not skim the arithmetic.

The organising principle:

> **A network is a stack of layers, each of which solves exactly one problem and hands an opaque payload to the one below. Every layer has its own addressing scheme and its own name for a chunk of data, and a device "works at layer N" precisely when layer N's address is the one it reads. Everything above the physical layer is a convention; the only physical facts are how fast you can push bits out (bandwidth) and how long they take to arrive (propagation delay).**

**Everything computable in this module was computed.** The delay tables, the encapsulation overhead and the bandwidth-delay products are program output, and §0.9 includes real measurements from this machine.

---

## 0.1 Why layering exists

Imagine writing a chat application with no layers. Your code would have to: encode text, compress it, encrypt it, break it into chunks, number the chunks, retransmit lost ones, find a route to the other machine, translate the destination name into an address, decide which cable to use, and modulate bits onto a voltage. Change the Wi-Fi card and you rewrite the chat app.

Layering is the fix, and it is the same idea as an interface in **OOP M3**: each layer offers a service, hides how it provides it, and depends only on the service below.

```
   application  "send this message to bob@example.com"
        |                            each layer:
   transport    "deliver these         - solves ONE problem
                 bytes reliably"       - adds its own header
        |                              - treats the layer above's
   network      "get this packet         output as an opaque PAYLOAD
                 to 93.184.216.34"     - can be replaced without
        |                                touching the others
   data link    "get this frame to
                 the next hop"
        |
   physical     "put these bits on
                 the wire"
```

The payoff is **substitutability**: TCP works identically over Ethernet, Wi-Fi and 5G, because TCP never learns which one it is using. The cost is **overhead** — every layer adds a header, and §0.5 measures exactly how much.

What layering buys, in the four words an interviewer wants: **modularity, abstraction, interoperability, independent evolution**.

---

## 0.2 The OSI model

Seven layers. Learn them as **(what it addresses, what it calls its data unit, what problem it solves)** — not as names.

```
 #  layer         addresses by        PDU         solves
 -- ------------- ------------------- ----------- ------------------------------------
 7  Application   nothing (names)     data/msg    what the bytes MEAN (HTTP, DNS, SMTP)
 6  Presentation  --                  data        encoding, serialization, compression,
                                                  encryption boundary
 5  Session       --                  data        dialogue: establish, sync, tear down
 4  Transport     PORT number         segment     process-to-process delivery, reliability
                                      (datagram)  flow control, congestion control
 3  Network       IP address          packet      host-to-host across MULTIPLE networks:
                                                  logical addressing, routing, fragmentation
 2  Data link     MAC address         frame       node-to-node across ONE link:
                                                  framing, error detection, MAC, flow ctrl
 1  Physical      no addresses        bit         voltages, timing, connectors, modulation
```

**The one-sentence version of each, at interview length:**

| Layer | What to say |
|---|---|
| **7 Application** | Where the protocols users care about live — HTTP, DNS, SMTP, FTP, SSH. It defines what the bytes *mean*. |
| **6 Presentation** | Translation: character encoding, serialization, compression, and where encryption conceptually sits. In TCP/IP it does not exist separately; TLS is the closest real thing. |
| **5 Session** | Managing a conversation: setting one up, checkpointing it, tearing it down. Mostly absorbed into the application layer in practice. |
| **4 Transport** | Gets data to the right **process** on the right host, using **port numbers**, and optionally makes the delivery reliable, ordered and rate-controlled. TCP and UDP. |
| **3 Network** | Gets a packet from **any host to any other host across multiple networks**, using **IP addresses** and routing. IP, ICMP, routing protocols. |
| **2 Data link** | Gets a frame **across one physical link to the next device**, using **MAC addresses**, and detects corruption. Ethernet, Wi-Fi, PPP. |
| **1 Physical** | Puts actual bits on actual media — voltages, light, radio, timing, pin layouts. |

### Layers 2 versus 3 — the distinction everything else rests on

This is worth its own table, because confusing them causes most wrong answers in the whole subject.

| | Data link (2) | Network (3) |
|---|---|---|
| Address | MAC, 48-bit, burned into the NIC | IP, 32-bit (v4), assigned by configuration |
| Scope | **One link**, hop to hop | **End to end**, across any number of links |
| Changes en route | **Yes — every single hop** | **No — stays the same the whole way** |
| Knows about | Only its own physical segment | The whole internetwork topology |
| Flat or hierarchical | **Flat** — no structure to aggregate on | **Hierarchical** — prefixes aggregate, which is what makes routing scale |
| Device | Switch, bridge | Router |

> **The sentence to deliver:** *"The IP addresses in a packet stay the same from source to destination; the MAC addresses are rewritten at every hop. That is the whole difference between end-to-end and hop-to-hop addressing."*

That single fact answers "why do we need both MAC and IP addresses", which is asked constantly. MAC alone cannot scale because it is flat — there is no way to aggregate 48-bit addresses into routes, so every router would need an entry per device on Earth. IP alone cannot work because the final delivery on a shared medium has to name a physical adapter.

### Mnemonics

```
bottom-up:  Please Do Not Throw Sausage Pizza Away
top-down:   All People Seem To Need Data Processing
```

Use the bottom-up one; questions are usually asked bottom-up, since that is the order a packet is built.

---

## 0.3 The TCP/IP model, and the honest mapping

OSI is a **reference model** designed by committee and never fully implemented. TCP/IP is what the internet actually runs. You should be able to say that out loud.

```
   OSI (7)                     TCP/IP (4, the RFC version)    TCP/IP (5, as taught)
   ------------------------    --------------------------     ---------------------
 7 Application            \
 6 Presentation            >   Application                    Application
 5 Session                /
 4 Transport                   Transport                      Transport
 3 Network                     Internet                       Network / Internet
 2 Data link              \
 1 Physical                >   Network Access / Link          Data link
                          /                                   Physical
```

| | OSI | TCP/IP |
|---|---|---|
| Layers | 7 | 4 (RFC 1122) or 5 as commonly taught |
| Origin | ISO, designed before the protocols | Protocols first, model described afterwards |
| Session and presentation | Separate layers | **Folded into the application** |
| Physical and data link | Separate layers | Combined as "link" in the 4-layer version |
| Service/interface/protocol | Clearly separated | Not cleanly separated |
| Transport reliability | Guaranteed at layer 4 | **Both options**: TCP reliable, UDP not |
| Use today | Teaching, troubleshooting vocabulary | **Everything real** |

**The question behind the question:** if TCP/IP is what we use, why teach OSI? Because it is the shared *vocabulary*. When an engineer says "layer 7 load balancer" or "it's a layer 2 problem", those numbers are OSI's. Say that and you have answered the comparison properly.

**The honest caveats worth one line each**, because they are what a sharp interviewer probes:

- The 5-layer model is a teaching compromise that exists purely so physical and data link stay distinct.
- **TLS does not fit.** It sits between TCP and the application, which OSI has no slot for. "Layer 6-ish" or "between 4 and 7" is the honest answer; claiming it is cleanly layer 6 is not.
- ARP does not fit either: it maps a layer-3 address to a layer-2 one, so it belongs to neither. Conventionally it is called layer 2.5, or "layer 2 with layer 3 knowledge".
- ICMP is carried *inside* IP but is a layer-3 protocol, which looks like a layering violation and is one.

---

## 0.4 Encapsulation

Each layer wraps the layer above's output in its own header. Drawn once, this diagram answers a dozen questions:

```
 APPLICATION   [        HTTP request: GET / HTTP/1.1 ...        ]   "data"
                                   |
 TRANSPORT     [ TCP hdr ][        HTTP request                 ]   "segment"
               20 bytes     src port, dst port, seq, ack, flags, window
                                   |
 NETWORK       [ IP hdr ][ TCP hdr ][     HTTP request          ]   "packet"
               20 bytes    src IP, dst IP, TTL, protocol, checksum
                                   |
 DATA LINK     [ Eth hdr ][ IP hdr ][ TCP hdr ][ HTTP ][ FCS ]      "frame"
               14 bytes    dst MAC, src MAC, EtherType      4 bytes
                                   |
 PHYSICAL      101000110101110100011010111010110101...              "bits"
```

Four facts to extract:

1. **Each layer's header goes in front, and the whole thing below is its payload.** The data-link layer has no idea the bytes it carries contain an IP header.
2. **Decapsulation is the exact reverse.** The receiver strips the Ethernet header, sees `EtherType = 0x0800`, hands the rest to IP; IP sees `protocol = 6`, hands the rest to TCP; TCP sees `dst port = 443`, hands the rest to the process listening there. Every header carries a "what's inside me" field precisely so this works — `EtherType`, IP's `protocol`, TCP's `port`. That chain of demultiplexing fields *is* layering, implemented.
3. **Only the headers are read by intermediate devices.** A router reads the IP header and rewrites the Ethernet one. It never looks at the TCP header (unless it is a NAT box or a firewall, which is exactly why those are called layering violations).
4. **The FCS is a trailer, not a header** — the only one, because the CRC has to cover everything before it.

### Verified: what layering costs

Computed exactly, for an Ethernet + IPv4 + TCP stack with no options:

```
   Ethernet header+FCS           18 bytes
   IPv4 header (no options)      20 bytes
   TCP header (no options)       20 bytes
   total overhead per segment    58 bytes

     payload    frame  efficiency
           1       59        1.7%
           6       64        9.4%
         100      158       63.3%
         536      594       90.2%
        1460     1518       96.2%
       14600    15180       96.2%   (10 segments)
```

Read the first row. **One useful byte in fifty-nine — 1.7% efficiency.** That is one keystroke sent over SSH, and it is the entire reason **Nagle's algorithm** exists (M6): batching small writes is the difference between 1.7% and something sane.

Read the last two rows: efficiency tops out at **96.2%** and stays there, because 1460 is the largest payload that fits. The 3.8% is the irreducible cost of layering on Ethernet.

Two numbers from that table to memorise:

```
 MTU (Ethernet)   = 1500 bytes   -- the largest IP PACKET the link will carry
 MSS (TCP/IPv4)   = 1500 - 20 - 20 = 1460 bytes   -- the largest TCP PAYLOAD
 frame on the wire = 1460 + 20 + 20 + 18 = 1518 bytes
```

**And the trap:** Ethernet's own 18 bytes are **not** part of the MTU. The MTU is the size of the payload the link layer will carry — i.e. the IP packet — so the frame is always MTU + 18. People get this wrong in both directions.

---

## 0.5 Protocol, service, and interface

A small distinction that gets asked as a definition question.

| Term | Meaning | Example |
|---|---|---|
| **Service** | *What* a layer offers the layer above, as a set of operations | "reliable, ordered byte stream" |
| **Interface** | *How* the layer above asks for it | the socket API: `connect`, `send`, `recv` |
| **Protocol** | The rules two **peer** entities at the same layer follow to talk to each other | TCP's handshake, sequence numbers, ACKs |

The relationship in one line: **a service is vertical, a protocol is horizontal.** Your application talks *down* to TCP through an interface and receives a service; your TCP talks *across* to the far TCP using a protocol. OSI separates these three cleanly and TCP/IP does not, which is the one real criticism of the TCP/IP model.

**Connection-oriented vs connectionless** service, since it follows directly:

| | Connection-oriented | Connectionless |
|---|---|---|
| Setup before data | Yes (handshake) | No — just send |
| State at the endpoints | Yes | None |
| Ordering | Guaranteed | Not guaranteed |
| Example at layer 4 | TCP | UDP |
| Analogy | A phone call | Posting a letter |

Note that **connection-oriented is not the same as reliable.** A connection can be set up and still lose data; reliability is a separate guarantee that TCP happens to add on top. ATM's connections, for instance, were ordered but not reliable.

---

## 0.6 Devices, and which layer each works at

The most frequently asked practical question in the module. The rule that generates the whole table: **a device works at layer N when layer N's address is the one it reads to make its decision.**

| Device | Layer | Decides using | What it does |
|---|---|---|---|
| **Repeater** | 1 | nothing | Regenerates the signal to extend distance. Copies bits, understands nothing |
| **Hub** | 1 | nothing | A multiport repeater: every bit in goes out of **every** other port |
| **Bridge** | 2 | MAC | Connects two segments and filters by MAC. The 2-port ancestor of a switch |
| **Switch** | 2 | MAC | Learns which MAC is on which port and forwards only there |
| **Router** | 3 | IP | Chooses the next hop from a routing table, decrements TTL, rewrites the MAC addresses |
| **Layer-3 switch** | 2+3 | MAC and IP | A switch that also routes between VLANs, in hardware |
| **NIC** | 1+2 | MAC | The host's own interface: frames out, frames in, filters by MAC |
| **Modem** | 1 | nothing | Modulates digital to analogue and back |
| **Access point** | 1+2 | MAC | A wireless "switch" — but shared medium, so really closer to a hub |
| **Firewall** | 3–7 | IP, ports, payload | Filters by rules; stateful ones track connections (M9) |
| **Load balancer** | 4 or 7 | ports, or HTTP content | L4 balances connections, L7 reads URLs and headers (M10) |
| **Gateway** | up to 7 | anything | A general translator between dissimilar systems. "Default gateway" is a router |
| **Proxy** | 7 | application data | Terminates the request and makes its own on your behalf |

### The four questions this table gets asked as

**"Why doesn't a switch have an IP address?"** Because it forwards on MAC addresses and never looks at the IP header — a pure layer-2 device has no reason to have a layer-3 identity. (Managed switches *do* have a management IP, which is for administering the switch, not for forwarding. Saying that distinction out loud is a good answer.)

**"Hub vs switch vs router?"** The table everyone wants:

| | Hub | Switch | Router |
|---|---|---|---|
| Layer | 1 | 2 | 3 |
| Address used | none | MAC | IP |
| Forwarding | floods every port | learned port only | next hop from routing table |
| Collision domains | **1** (extends it) | **one per port** | one per port |
| Broadcast domains | 1 | **1** | **one per interface** |
| Duplex | half only | full | full |
| Bandwidth | **shared** | **dedicated per port** | per interface |
| Connects | devices on one segment | devices on one network | **different networks** |

**"Does a router change the IP address?"** No — not in forwarding. It decrements TTL, recomputes the header checksum, and replaces both MAC addresses. The IP addresses only change if the router is doing **NAT** (M3), which is an extra function bolted on, not routing.

**"What's the difference between a switch and a bridge?"** Historically: a bridge had two ports and worked in software; a switch has many and works in hardware. Functionally they are the same thing, and "switch" is the modern word.

---

## 0.7 Collision domains and broadcast domains

Needed here because §0.6's table references them; M2 does the full treatment.

- A **collision domain** is the set of devices whose transmissions can collide with each other — one shared medium.
- A **broadcast domain** is the set of devices that will receive a broadcast frame — one logical network.

Two rules generate every answer:

```
 every SWITCH PORT (and every full-duplex link) is its own COLLISION domain
 every ROUTER INTERFACE (and every VLAN) bounds a BROADCAST domain

 a HUB    extends both
 a SWITCH splits collision domains, NOT broadcast domains
 a ROUTER splits both
```

Verified by counting:

```
  1 hub, 8 PCs                                         collision=1  broadcast=1
  1 switch (8 ports), 8 PCs                            collision=8  broadcast=1
  1 switch, 3 hubs of 4 PCs on 3 ports, 5 PCs direct   collision=8  broadcast=1
  1 router, 2 switches (one per port)                  broadcast=2
  1 switch with 3 VLANs                                broadcast=3
```

The third line is the one exam questions use: the three hubs each collapse their four PCs into **one** collision domain, so `3 + 5 = 8`, not 17.

And the consequence, computed:

```
  10 PCs on a 10 Mbps hub    -> ONE collision domain, 10 Mbps SHARED
   each PC's fair share       = 1.0 Mbps, and collisions waste more on top
  10 PCs on a 10 Mbps switch -> 10 collision domains, full duplex
   each PC gets               = 10 Mbps each way
   non-blocking backplane needs 200 Mbps
```

---

## 0.8 The four delays

Everything numerical in this subject is built from these. There are exactly four, and only two can be computed from first principles.

```
 total delay per hop = T_transmission + T_propagation + T_queuing + T_processing

 T_t = L / B        L = packet length in BITS, B = link rate in bits/sec
                    "how long to push the bits out of the interface"
 T_p = d / v        d = distance in metres, v = signal speed
                    "how long for one bit to travel the wire"
                    v ~ 2 x 10^8 m/s in fibre or copper (about 2/3 of c)
 T_q                time waiting in the router's output buffer -- VARIABLE,
                    depends on load, and is the only one congestion affects
 T_proc             header inspection, checksum, lookup -- small and fixly
```

**The two that get confused.** `T_t` depends on the **packet size and the link rate**, and *not at all* on distance. `T_p` depends on the **distance**, and *not at all* on the packet size or the link rate. Doubling the bandwidth halves `T_t` and does nothing to `T_p`. That is the whole distinction and it is a guaranteed follow-up.

### Verified

```
  case                                          T_t          T_p    a=Tp/Tt  dominates
  1 KB over 1 Mbps,    LAN 100 m           8.000 ms     0.001 ms       0.00  transmission
  1 KB over 100 Mbps,  LAN 100 m           0.080 ms     0.001 ms       0.01  transmission
  1 KB over 1 Gbps,    LAN 100 m           0.008 ms     0.001 ms       0.06  transmission
  1 KB over 1 Mbps,    WAN 2000 km         8.000 ms    10.000 ms       1.25  propagation
  1 KB over 1 Gbps,    WAN 2000 km         0.008 ms    10.000 ms    1250.00  propagation
  1 MB over 1 Gbps,    WAN 2000 km         8.000 ms    10.000 ms       1.25  propagation
  1 KB over 1 Gbps,    satellite 36000 km  0.008 ms   180.000 ms   22500.00  propagation
```

### The single most useful derived quantity

```
   a = T_p / T_t
```

Remember this symbol. It is the only parameter in M1's formulas, and it tells you which delay you are fighting:

- **a ≪ 1** — transmission dominates. The link is "short and slow". Stop-and-wait is fine; the pipe is never empty.
- **a ≫ 1** — propagation dominates. The link is "long and fast". You *must* pipeline, because a single packet in flight leaves the link almost entirely idle.

Notice rows 4 and 6 of the table: a 1 KB packet at 1 Mbps and a 1 MB packet at 1 Gbps both give `a = 1.25`. **`a` is a ratio, so what matters is the combination, not either number alone.** That is why one parameter can replace four.

---

## 0.9 Bandwidth, throughput and latency

Three words people use interchangeably and interviewers do not.

| Term | Means | Unit | Analogy (a pipe) |
|---|---|---|---|
| **Bandwidth** | The link's *capacity* — the maximum rate | bits/sec | the pipe's diameter |
| **Throughput** | The rate you actually *achieve* | bits/sec | water actually flowing |
| **Goodput** | Throughput minus headers and retransmissions | bits/sec | water that reaches the bucket |
| **Latency** | Time for one bit to get there | seconds | the pipe's length |
| **RTT** | Round-trip time: there and back | seconds | there and back |
| **Jitter** | Variation in latency | seconds | unsteady flow |

Two consequences worth saying:

**Bandwidth and latency are independent.** A satellite link can have enormous bandwidth and dreadful latency; a short slow serial cable the reverse. "Fast internet" conflates them, and for interactive work latency usually matters more.

**Throughput is the minimum over the path** — the bottleneck link and nothing else. Verified:

```
   your Wi-Fi            300 Mbps
   home uplink            40 Mbps
   ISP backbone        10000 Mbps
   server NIC           1000 Mbps
   end-to-end throughput = min = 40 Mbps  (home uplink)
   upgrading ANY other link changes nothing.
```

### Measured on this machine: delay is not only distance

Loopback never touches a wire, so `T_p ≈ 0` and whatever is left is pure software:

```
       1-byte round trip on loopback: median    25.3 us  (min   23.6)
      64-byte round trip on loopback: median    25.4 us  (min   20.2)
    1460-byte round trip on loopback: median    27.7 us  (min   20.6)
   32 MB echoed in 0.021 s -> 12098 Mbps each way (24196 Mbps of traffic)
```

Two readings. The round trip is **25 µs with zero distance** — that is kernel transitions, buffer copies and scheduling, and it is the floor beneath which no local network call can go. And the payload size barely changes it (25.3 → 27.7 µs for 1460× more data), which says the cost is **per operation**, not per byte — the same reason N+1 queries are slow in **DBMS M10** and the same reason batching always wins.

### And the floor that is a law of physics

Real traceroute from this machine, then the theoretical minimum for some real distances:

```
  1     3 ms     2 ms     3 ms  10.145.0.3
  2     4 ms     3 ms     9 ms  10.120.0.25
  3     4 ms     2 ms     1 ms  10.250.1.9
  4     *        *        *     Request timed out.

  theoretical one-way propagation (v = 2e8 m/s):
   same city (10 km)              one-way    0.05 ms   RTT floor    0.10 ms
   Delhi-Mumbai (1150 km)         one-way    5.75 ms   RTT floor   11.50 ms
   Mumbai-Singapore (3900 km)     one-way   19.50 ms   RTT floor   39.00 ms
   Mumbai-London (7200 km)        one-way   36.00 ms   RTT floor   72.00 ms
   Mumbai-California (13000 km)   one-way   65.00 ms   RTT floor  130.00 ms
```

**That RTT floor is a law, not a target.** No amount of bandwidth reduces it, and fibre cannot be made faster than light in glass. A Mumbai user talking to a California server pays **at least 130 ms per round trip**, so a page needing four sequential round trips (DNS, TCP, TLS, HTTP) cannot load in under about half a second however fast the server is. **That is why CDNs exist** — not to add bandwidth, but to shorten `d`. M10 does this arithmetic properly.

(Note hop 4 onwards times out. ICMP echo is filtered on this network — real firewalls really do this, and M9 explains it. The three hops that *did* answer are private addresses, so this machine is several NAT layers from the internet.)

---

## 0.10 Bandwidth-delay product

The capacity of the link *as a container*: how many bits are "in flight" at once.

```
   BDP = bandwidth x RTT        (bits)
```

Think of the pipe again: bandwidth is its cross-section, RTT its length, so the product is its **volume**. And the volume is exactly how much unacknowledged data a sender must be allowed to have outstanding to keep the link busy. That makes BDP the right **window size**, which is why it reappears in M1 and M6.

Verified:

```
  link                                    RTT     BDP (bits)    BDP (bytes)  window needed
  LAN 1 Gbps, RTT 0.5 ms                0.5ms        500,000         62,500  fits in 16-bit window
  city 100 Mbps, RTT 10 ms             10.0ms      1,000,000        125,000  > 64 KB: NEEDS scaling
  country 100 Mbps, RTT 40 ms          40.0ms      4,000,000        500,000  > 64 KB: NEEDS scaling
  intercontinental 1 Gbps, 200 ms     200.0ms    200,000,000     25,000,000  > 64 KB: NEEDS scaling
  satellite 10 Mbps, RTT 500 ms       500.0ms      5,000,000        625,000  > 64 KB: NEEDS scaling
```

And the consequence that makes this more than an exercise:

```
  TCP's window field is 16 bits -> 65,535 bytes maximum without scaling.
  at 1 Gbps that is exhausted by an RTT of only 0.52 ms
```

**TCP's receive-window field, as designed in 1981, is too small for almost any modern link.** One gigabit and half a millisecond is enough to fill it — which is to say, a gigabit LAN. That is why **RFC 1323 window scaling** exists, and why M6 treats it as mandatory rather than optional. A "long fat network" (high bandwidth, high delay) is precisely one with a large BDP, and without scaling TCP simply cannot fill it.

**The interview-ready statement:** *"The bandwidth-delay product is how many bits fit in the pipe, and therefore how large your window has to be to keep the link busy. TCP's 16-bit window field caps that at 64 KB, which a gigabit link exhausts in half a millisecond, so window scaling is required on anything fast or distant."*

---

## 0.11 Network types and topologies (Tier 3)

One page, as promised.

| Type | Span | Example |
|---|---|---|
| **PAN** | a few metres | Bluetooth, your earbuds |
| **LAN** | a building | office Ethernet, home Wi-Fi |
| **CAN/MAN** | a campus or city | university network, metro fibre |
| **WAN** | countries, the globe | the internet, a corporate MPLS network |

| Topology | Shape | Pros | Cons |
|---|---|---|---|
| **Bus** | one shared cable | cheap, simple | one break kills it; collisions; no longer used |
| **Star** | all to a central hub/switch | easy to manage, isolates faults | central device is a single point of failure |
| **Ring** | each to the next, in a loop | predictable latency | one break splits it (dual rings fix this) |
| **Mesh** | many-to-many | redundant, resilient | `n(n−1)/2` links — expensive |
| **Tree/hierarchical** | star of stars | scales, matches buildings | depends on the upper tiers |
| **Hybrid** | a mix | practical | complex |

**Star is what you actually have** — every modern Ethernet LAN is a star (or a tree of stars) centred on switches. A full mesh needs `n(n−1)/2` links, so 10 nodes need 45 and 100 nodes need 4,950, which is why mesh is used between *routers in a core*, never between hosts.

**Client-server vs peer-to-peer:** in client-server, dedicated servers hold the resources and clients request them — simple to secure and administer, and the server is a bottleneck and a single point of failure. In peer-to-peer, every node is both, so capacity grows as nodes join (which is BitTorrent's whole trick) at the cost of harder security, discovery and consistency.

---

## Must remember

```
LAYERING buys modularity, abstraction, interoperability, independent evolution.
Cost = header overhead (measured: 58 bytes per TCP/IP/Ethernet segment).

OSI 7: Physical Data-link Network Transport Session Presentation Application
       ("Please Do Not Throw Sausage Pizza Away", bottom-up)
 learn each as (ADDRESS, PDU, problem):
 1 Physical    no address    bit       voltages, timing, media
 2 Data link   MAC           frame     node-to-node on ONE link, framing, error detect
 3 Network     IP            packet    host-to-host across MANY networks, routing
 4 Transport   PORT          segment   process-to-process, reliability, flow, congestion
 5 Session     --            data      dialogue setup/sync/teardown
 6 Presentation--            data      encoding, compression, encryption boundary
 7 Application names         data/msg  what the bytes MEAN

THE KEY FACT: IP addresses stay the same end to end; MAC addresses are
REWRITTEN AT EVERY HOP. MAC is flat (cannot aggregate); IP is hierarchical
(prefixes aggregate, which is what makes routing scale). That is why both exist.

TCP/IP = 4 layers (RFC 1122) or 5 as taught. Session+presentation folded into
application. OSI is the shared VOCABULARY ("layer 7 LB"); TCP/IP is what runs.
Things that do not fit the model: TLS (between 4 and 7), ARP (layer 2.5),
ICMP (inside IP but is layer 3).

ENCAPSULATION: each layer prepends its header; the layer below's payload is opaque.
Demultiplexing on the way up uses EtherType -> IP protocol -> TCP port.
FCS is the only TRAILER (the CRC must cover everything before it).
MTU 1500 = the largest IP PACKET. MSS 1460 = 1500 - 20 - 20.
Frame on the wire = 1518 = MSS + 20 + 20 + 18.  Ethernet's 18 bytes are NOT in the MTU.
Efficiency (verified): 1-byte payload = 1.7%; 1460-byte payload = 96.2%.
  -> the 1.7% figure is why Nagle's algorithm exists.

SERVICE is vertical (what a layer offers above, via an INTERFACE);
PROTOCOL is horizontal (rules between PEERS at the same layer).
Connection-oriented != reliable. TCP adds reliability on top of its connection.

DEVICE BY LAYER -- a device works at layer N if layer N's address is what it reads:
 1 repeater, hub, modem      2 bridge, switch, NIC, AP     3 router
 3-7 firewall    4 or 7 load balancer    7 proxy    up to 7 gateway
A switch has no forwarding IP because it never reads the IP header.
A router does NOT change the IP addresses (only TTL, checksum, MACs) -- unless NAT.

HUB vs SWITCH vs ROUTER
 layer           1              2                 3
 address         none           MAC               IP
 forwarding      floods all     learned port      next hop from table
 collision dom.  1 (extends)    one per port      one per port
 broadcast dom.  1              1                 one per interface
 bandwidth       SHARED         dedicated/port    per interface

every SWITCH PORT = its own collision domain
every ROUTER INTERFACE or VLAN = a broadcast domain boundary
hub extends both; switch splits collision only; router splits both

THE FOUR DELAYS
 T_t = L/B   transmission -- size and rate, NOT distance
 T_p = d/v   propagation  -- distance, NOT size or rate.  v ~ 2e8 m/s
 T_q         queuing      -- variable, the only one congestion touches
 T_proc      processing   -- small
 a = T_p / T_t  is THE parameter.  a<<1 transmission-bound (stop-and-wait is fine)
                                   a>>1 propagation-bound (MUST pipeline)

bandwidth = capacity;  throughput = achieved;  goodput = useful bytes delivered
throughput = MIN over the path (the bottleneck). Upgrading any other link does nothing.
bandwidth and latency are INDEPENDENT.
measured on loopback: 25 us RTT with zero distance, and nearly size-independent
  -> delay is per-OPERATION, not only per-byte or per-metre

BDP = bandwidth x RTT = bits in flight = the window size you need
 TCP's window field is 16 bits -> 64 KB, exhausted by 1 Gbps at 0.52 ms RTT
 -> RFC 1323 window scaling is mandatory on any long fat network
RTT floor is a LAW: Mumbai-California >= 130 ms whatever you spend. Hence CDNs.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "OSI has 7 layers: physical, data link, network, transport, session, presentation, application" — and stopping | That is the *names*. The question means what each layer **addresses** and what its **data unit** is. Names alone read as memorisation |
| "We use the OSI model" | We use TCP/IP. OSI is the shared vocabulary for talking about layers |
| "TCP/IP has 5 layers" | RFC 1122 defines **4**; the 5-layer version is a teaching convention that keeps physical and data link apart. Say which you mean |
| "TLS is layer 6" | It does not fit OSI. It sits between transport and application — "layer 6-ish" is the honest answer |
| "ARP is a layer 3 protocol" | It maps layer 3 to layer 2 and belongs to neither; conventionally layer 2.5 |
| "MAC addresses change at the destination" | They change at **every hop**. The IP addresses are what stay constant |
| "We have IP because MAC addresses ran out" | We have IP because MAC is **flat** — it cannot be aggregated into routes, so routing could not scale. Address space is not the issue |
| "A router changes the IP address" | It changes TTL, the checksum and both MACs. The IP addresses change only under NAT, which is a separate function |
| "A switch needs an IP address" | Only for management. Forwarding never reads the IP header |
| "A switch splits broadcast domains" | It splits **collision** domains. Broadcast domains are split by routers and VLANs |
| "A hub and a switch are the same with different speeds" | A hub floods every port and shares one collision domain; a switch learns and gives each port its own. Verified: 1 Mbps each on a hub vs 10 Mbps each on a switch |
| "The MTU is 1518 bytes on Ethernet" | 1500 — the largest **IP packet**. The 18 bytes of Ethernet header and FCS sit outside it, making the frame 1518 |
| "MSS is 1500" | 1460 on Ethernet with IPv4: 1500 − 20 (IP) − 20 (TCP) |
| "Doubling bandwidth halves latency" | It halves **transmission** delay only. Propagation delay does not move |
| "Bandwidth and throughput are the same" | Capacity vs what you actually get. Throughput is capped by the **bottleneck** link, not the average |
| "Latency is caused by congestion" | Congestion raises the **queuing** component. Propagation delay is distance over signal speed and is irreducible |
| "A faster link makes a distant server feel closer" | No — the RTT floor is physics. A Mumbai-to-California round trip is ≥ 130 ms at any bandwidth. That is what CDNs address |
| "The BDP is just trivia" | It is the required window size, and it is why TCP needs window scaling at all |
| "Connection-oriented means reliable" | A connection can be ordered and unreliable. Reliability is a separate guarantee TCP adds |
| "Mesh topology is best" | It needs `n(n−1)/2` links — 4,950 for 100 nodes. Real LANs are stars |

---

## Interview Q&A bank

**Q1. Explain the OSI model.**
Seven layers, each solving one problem and handing an opaque payload downward. Physical moves bits as signals. Data link moves frames across a single link using MAC addresses and detects corruption. Network moves packets host to host across multiple networks using IP addresses and routing. Transport moves segments process to process using port numbers, and optionally adds reliability and flow control. Session manages a conversation, presentation handles encoding and encryption, and application defines what the bytes mean. The useful way to hold it is: each layer has its own address type and its own name for a chunk of data.

**Q2. Why do we need layers at all?**
So each concern is solved once and can be replaced independently. TCP works unchanged over Ethernet, Wi-Fi and 5G because it never learns which one is underneath. The cost is header overhead — 58 bytes per segment on a TCP/IP/Ethernet stack.

**Q3. OSI vs TCP/IP?**
OSI has seven layers and was designed before the protocols; TCP/IP has four and was described after them. TCP/IP folds session and presentation into the application layer and combines physical and data link. OSI is the vocabulary engineers speak in — "layer 7 load balancer" is an OSI number — while TCP/IP is what actually runs.

**Q4. Which layer does a switch work at, and why?**
Layer 2, because the address it reads to make a forwarding decision is the MAC address. A device works at layer N when layer N's address is what it acts on.

**Q5. Why do we need both MAC and IP addresses?**
MAC addresses are flat, so they cannot be aggregated into routes — a router would need an entry for every device on Earth. IP addresses are hierarchical, so prefixes aggregate and routing scales. But the final hop over a shared medium still has to name a specific physical adapter, which is what the MAC does.

**Q6. What changes as a packet crosses a router?**
The MAC addresses are both rewritten for the next hop, the TTL is decremented and the header checksum recomputed. The IP addresses do not change — unless the router is also doing NAT.

**Q7. What is encapsulation?**
Each layer wraps the layer above's output in its own header, treating it as an opaque payload. On the way back up, each header's demultiplexing field says what is inside — EtherType says IPv4, IP's protocol field says TCP, TCP's port says which process.

**Q8. What is the MTU, and what is the MSS?**
The MTU is the largest IP packet a link will carry — 1500 bytes on Ethernet. The MSS is the largest TCP payload, which is the MTU minus the IP and TCP headers: 1460. Ethernet's own 18 bytes of header and FCS are outside the MTU, so the frame on the wire is 1518.

**Q9. How much overhead does the stack add?**
58 bytes per segment — 20 IP, 20 TCP, 18 Ethernet. That is 3.8% on a full-size segment, and verified at 98.3% on a one-byte payload, which is why Nagle's algorithm batches small writes.

**Q10. Transmission delay vs propagation delay?**
Transmission delay is `L/B` — how long to push the bits out of the interface, which depends on packet size and link rate but not distance. Propagation delay is `d/v` — how long a bit takes to travel, which depends on distance but not on size or rate. Doubling the bandwidth halves the first and does nothing to the second.

**Q11. Name the four delays.**
Transmission, propagation, queuing and processing. Only the first two can be computed from first principles; queuing is load-dependent and is the only one congestion affects.

**Q12. What is `a`, and why does it matter?**
The ratio of propagation to transmission delay. If `a` is much less than 1 the link is short and slow, so one packet in flight keeps it busy and stop-and-wait is fine. If `a` is much greater than 1 the link is long and fast, so you must pipeline. Every sliding-window formula in M1 is written in terms of `a` alone.

**Q13. Bandwidth vs throughput vs latency?**
Bandwidth is the link's capacity, throughput is the rate actually achieved, and latency is the time for one bit to arrive. Bandwidth and latency are independent — a satellite link has plenty of the first and terrible second. Throughput end to end is the minimum over the path, so upgrading anything but the bottleneck changes nothing.

**Q14. What is the bandwidth-delay product?**
Bandwidth times RTT — the number of bits in flight, and therefore the window size a sender needs to keep the link busy. It is why TCP needs window scaling: the 16-bit window field caps out at 64 KB, which one gigabit exhausts in half a millisecond of RTT.

**Q15. Can you make a distant server respond faster by buying more bandwidth?**
No. The round-trip floor is distance over signal speed — about 130 ms between Mumbai and California — and no bandwidth reduces it. The only fix is to shorten the distance, which is what a CDN does.

**Q16. Service vs protocol vs interface?**
A service is what a layer offers the layer above; the interface is how you ask for it; the protocol is the rules two peers at the same layer follow. A service is vertical, a protocol horizontal.

**Q17. Connection-oriented vs connectionless — and is connection-oriented the same as reliable?**
Connection-oriented sets up state before sending and tears it down afterwards; connectionless just sends. They are not the same as reliable: a connection can be ordered and still lose data. TCP happens to add reliability on top of its connection.

**Q18. Collision domain vs broadcast domain?**
A collision domain is the set of devices whose transmissions can collide — one shared medium. A broadcast domain is the set that receives a broadcast frame — one logical network. Every switch port is its own collision domain; every router interface or VLAN bounds a broadcast domain.

**Q19. Hub vs switch vs router?**
A hub is layer 1 and floods every port, so all devices share one collision domain and the bandwidth. A switch is layer 2, learns which MAC is on which port, and gives each port its own collision domain and full duplex. A router is layer 3, forwards between different networks using a routing table, and bounds broadcast domains.

**Q20. Why is loopback latency not zero?**
Because propagation delay is only one of four. Measured at about 25 µs with zero distance, and almost unchanged from 1 byte to 1460 — so the cost is per operation: system calls, buffer copies, scheduling. It is the floor under any local network call.

---

## Practice

1. A 1500-byte packet crosses a 100 Mbps link of 300 m. Compute `T_t`, `T_p` and `a`, and say which dominates.
2. The same packet crosses a 10 Gbps link of 3000 km. Repeat, and comment on what changed.
3. A file of 10 MB is sent over a 100 Mbps link with a 50 ms RTT. How long does the transfer take if the sender may have only one packet outstanding at a time, with 1500-byte packets? Compare with the ideal time.
4. Compute the BDP of a 500 Mbps link with a 30 ms RTT. Will TCP fill it without window scaling? Show why.
5. A 20-byte payload is sent over TCP/IPv4/Ethernet. What fraction of the bits on the wire are useful? What is the fraction for a 1460-byte payload?
6. Name the layer and the addressing used by each: repeater, bridge, layer-3 switch, L7 load balancer, modem, NAT box.
7. A network has one router with three interfaces. Each interface connects to a switch with 12 ports, and on one of those switches three ports each have a 4-port hub. Count the collision and broadcast domains.
8. Explain, in two sentences each, what changes and what does not change in a packet's headers as it crosses (a) a switch, (b) a router, (c) a NAT router.
9. A page needs DNS, then TCP, then TLS, then the HTTP request before any byte of HTML arrives, over a path with a 90 ms RTT. Estimate the minimum time to first byte, stating your assumptions. Then say which single change helps most.
10. Your colleague says "our API is slow, let's upgrade to a 10 Gbps uplink". The API returns 2 KB JSON responses to users in another continent. Give the two-sentence rebuttal and the diagnostic you would run.

**Answers to 3, 7 and 9:**

> **3.** `T_t = 12000/100e6 = 0.12 ms`, and one packet per RTT means one packet per `T_t + RTT = 50.12 ms`. 10 MB is 6,991 packets (ceil of 10,485,760/1500), so about `6991 × 50.12 ms ≈ 350 s` — nearly six minutes. The ideal time is `10 MB / 100 Mbps ≈ 0.84 s`. The ratio is the utilization: `0.12/50.12 ≈ 0.24%`, which is `1/(1+2a)` with `a ≈ 208`. **This is the M1 formula arriving before M1.**
>
> **7.** Broadcast domains: **3**, one per router interface. Collision domains: the two untouched switches contribute 12 each = 24; the third has 9 plain ports plus 3 ports each feeding a hub, and each hub collapses its 4 PCs into **one** collision domain, so that switch contributes `9 + 3 = 12`. Total **36**. The trap is counting the hub's 4 ports separately.
>
> **9.** Four sequential round trips before the first byte: DNS (1 RTT, assuming an uncached query to a nearby resolver — call it 1 RTT), TCP handshake (1 RTT), TLS 1.3 (1 RTT), HTTP request and response (1 RTT). That is `4 × 90 ms = 360 ms` minimum, before any server processing. The single biggest change is **shortening the RTT** — a CDN edge at 10 ms turns 360 ms into 40 ms — and after that, removing round trips: TLS 1.3 over TLS 1.2 saves one, connection reuse saves two, and DNS caching saves one.

---

## Exit checklist

```
[ ] I can name all 7 OSI layers bottom-up without hesitating
[ ] For each layer I can give the ADDRESS type and the PDU name
[ ] I can say what problem each layer solves in one sentence
[ ] I can state the layer-2 vs layer-3 distinction in terms of what changes per hop
[ ] I can explain why both MAC and IP addresses exist (flat vs hierarchical)
[ ] I can compare OSI and TCP/IP and say why we still teach OSI
[ ] I know TLS, ARP and ICMP do not fit the model cleanly, and roughly where they go
[ ] I can draw the encapsulation diagram with all four headers and the FCS
[ ] I can name the demultiplexing field at each layer (EtherType, protocol, port)
[ ] I know MTU = 1500 = the IP packet, MSS = 1460, frame = 1518
[ ] I know Ethernet's 18 bytes are NOT part of the MTU
[ ] I can state the overhead efficiency for a 1-byte and a 1460-byte payload
[ ] I can distinguish service, interface and protocol (vertical vs horizontal)
[ ] I know connection-oriented does not mean reliable
[ ] I can give the layer and address used by every device in the table
[ ] I can say why a switch needs no forwarding IP address
[ ] I can say exactly what a router changes in a packet, and what it does not
[ ] I can reproduce the hub/switch/router table from memory
[ ] I can count collision and broadcast domains for any described topology
[ ] I can compute T_t and T_p and say which depends on what
[ ] I can compute a = Tp/Tt and interpret both extremes
[ ] I can distinguish bandwidth, throughput, goodput, latency, RTT and jitter
[ ] I know throughput is the minimum over the path
[ ] I can compute a BDP and say what window size it implies
[ ] I can explain why TCP needs window scaling, with the 0.52 ms figure
[ ] I can explain the RTT floor and why it justifies CDNs
[ ] I know why loopback latency is 25 us and not 0
```

---

## Next

**Part 3: M1 — Framing and Errors.** The first numericals centrepiece, and the densest marks in the subject. Framing with **bit stuffing and byte stuffing** round-tripped; error **detection** — parity, the Internet checksum, and **CRC** with the polynomial division worked out and its guarantees tested exhaustively; error **correction** with **Hamming codes** — how many redundant bits, where they go, and how the syndrome locates the flipped bit; then **ARQ: stop-and-wait, Go-Back-N and Selective Repeat**, with the **utilization and window-size formulas checked against a simulation** and the sequence-number bound demonstrated by making it fail.
