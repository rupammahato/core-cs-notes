# Computer Networks Placement Handbook — Part 4
# Module 2: Medium Access and the LAN

**Module 2 · 3 hours · Tier 1 · Requires: M0 (delays, devices, domains), M1 (framing, CRC)**

---

## Why this module matters

M1 solved one link with one sender. This module solves one link with **many** senders — which is the actual situation on every Ethernet segment and every Wi-Fi network that has ever existed.

The interview questions here are concrete and frequently asked:

- **Hub vs switch vs router** — the table, which M0 previewed and this module earns
- **CSMA/CD vs CSMA/CA**, and why Wi-Fi uses the second
- **Why does Ethernet have a minimum frame size?** — a genuinely good question, because the answer is a propagation-delay argument rather than a convention
- **What is ARP?** and what is ARP spoofing
- **How does a switch know where to send a frame?**

And one written-test numerical: **ALOHA and slotted ALOHA efficiency**, `1/2e` and `1/e`.

The organising principle:

> **When one medium is shared, the only real problem is deciding who talks. Every protocol in this module is an answer to that one question, and they differ along a single axis: how much do you listen before you speak, and what do you do when two of you speak anyway. Then switching makes the problem disappear by giving everyone their own medium — which is why CSMA/CD, the centrepiece of every textbook, is effectively dead in practice.**

**How this module was verified.** The ALOHA efficiencies were checked against event-driven simulations; the Ethernet minimum-frame-size arithmetic was computed and its gap from the standard explained; the Ethernet frame was built and parsed field by field with a real CRC-32; the switch-learning trace is program output; and **ARP is decoded against this machine's actual ARP table**, where three separate facts turned out to cross-check each other arithmetically.

---

## 2.1 The multiple-access problem

```
                          one shared medium
   A ----+----+----+----+----+----+----+----+---- 
         |         |              |         |
        [A]       [B]            [C]       [D]

   If B and C transmit at overlapping times, their signals superimpose and
   both frames are destroyed. That is a COLLISION -- not a lost frame, a
   mutually-destroyed pair.
```

Three families of answer, and knowing the taxonomy is worth a mark on its own:

| Family | Idea | Protocols |
|---|---|---|
| **Random access** (contention) | Just transmit; detect and recover from collisions | ALOHA, slotted ALOHA, CSMA, CSMA/CD, CSMA/CA |
| **Controlled access** | Take turns by an explicit rule | Polling, token passing, reservation |
| **Channelization** | Divide the medium itself | FDMA, TDMA, CDMA, OFDMA |

Random access wins at low load (no coordination overhead) and collapses at high load (all collisions). Controlled access is the reverse — predictable and fair, with overhead you pay even when idle. Channelization is perfect when the number of stations is fixed and known, and wasteful when they are bursty, because an idle station's slot or frequency goes unused.

**Which is why Ethernet is random access and cellular is channelization**: a LAN has unpredictable bursty hosts, a cell tower has a managed set of subscribers.

---

## 2.2 ALOHA and slotted ALOHA

The simplest possible protocol: transmit whenever you have something to send; if no acknowledgement comes, wait a random time and retry.

```
 PURE ALOHA -- frames may start at any instant
   A:      [====A====]
   B:            [====B====]        overlap -> BOTH destroyed
   vulnerable period = 2 frame times
   (a frame is destroyed by anything starting in the frame time before it
    as well as anything starting during it)

 SLOTTED ALOHA -- time is divided into frame-sized slots, transmission may
 only begin at a slot boundary
   slot:  |....1....|....2....|....3....|
   A:     [====A====]
   B:                [====B====]          no partial overlap possible
   vulnerable period = 1 frame time
```

Halving the vulnerable period exactly doubles the throughput:

```
   pure ALOHA     S = G e^(-2G)    maximum 1/(2e) = 18.4% at G = 0.5
   slotted ALOHA  S = G e^(-G)     maximum 1/e    = 36.8% at G = 1.0
```

where `G` is the offered load in frames per frame-time and `S` the throughput.

### Verified: formula against simulation

```
      G  slotted formula   slotted sim   pure formula   pure sim
    0.1          0.09048       0.09125        0.08187    0.08160
    0.3          0.22225       0.22373        0.16464    0.16428
    0.5          0.30327       0.30178        0.18394    0.18445
    0.8          0.35946       0.35717        0.16152    0.16227
    1.0          0.36788       0.36715        0.13534    0.13723
    1.5          0.33470       0.33430        0.07468    0.07438
    2.0          0.27067       0.27367        0.03663    0.03715

  the maxima, located by scanning:
   slotted: max S = 0.36788 at G = 1.000   (1/e  = 0.36788)
   pure   : max S = 0.18394 at G = 0.500   (1/2e = 0.18394)
```

The simulation is an independent Poisson-arrival model that never uses the formula, and it reproduces both curves and both maxima. Two things to take from the table:

1. **The maxima are where theory says**, to five decimal places: `1/e` at `G = 1` and `1/2e` at `G = 0.5`.
2. **Throughput *falls* past the maximum.** At `G = 2.0` pure ALOHA delivers 3.7% — worse than at `G = 0.1`. Offering more load makes things worse, because almost everything collides. That is **congestion collapse** in its simplest possible form, and it is the same phenomenon M6 handles properly in TCP.

**Interview-ready:** *"Pure ALOHA peaks at 18.4% because a frame is vulnerable for two frame times — anything starting in the frame before it also destroys it. Slotting forces transmissions to start on boundaries, which halves the vulnerable period to one frame time and exactly doubles the maximum to 36.8%, or `1/e`."*

---

## 2.3 CSMA: listen before you talk

ALOHA transmits blind. **Carrier Sense Multiple Access** listens first — the obvious improvement, and the basis of everything real.

| Variant | Rule when the channel is busy | Behaviour |
|---|---|---|
| **1-persistent** | Keep sensing; transmit **immediately** when it goes idle | Greedy. Maximum collisions, because every waiting station jumps at the same instant |
| **Non-persistent** | Wait a **random** time, then sense again | Fewer collisions, but the channel can sit idle while everyone waits |
| **p-persistent** | When idle, transmit with probability `p`; else wait a slot and repeat | The tunable compromise, used in slotted systems |

Ethernet uses **1-persistent** — and compensates for its greediness with collision detection plus exponential backoff, which is the next section.

**Why CSMA still collides at all** is the question worth having an answer to: because of **propagation delay**. Station A begins transmitting; for `Tp` seconds, station B at the far end still senses an idle channel, because A's signal has not reached it yet. B transmits, and they collide. Sensing can never be instantaneous, so collisions can never be eliminated by sensing alone.

---

## 2.4 CSMA/CD, and why Ethernet has a 64-byte minimum

**Collision Detection**: keep listening *while* transmitting, and the moment you detect a collision, stop, send a 32-bit **jam signal** so everyone else notices too, and back off.

```
 1. sense the channel; if busy, wait (1-persistent)
 2. transmit, AND KEEP LISTENING
 3. collision detected?
       -> abort immediately
       -> send a 32-bit jam sequence
       -> wait a backoff time, go to 1
 4. transmitted the whole frame with no collision -> success
```

**Binary exponential backoff:** after the `n`th collision, wait `k × slot_time` where `k` is drawn uniformly from `0 … 2ⁿ−1`, capped at `n = 10` (so `0..1023`), and give up after 16 attempts. The point of doubling the range is that the backoff window adapts to the load without any station knowing what the load is.

### The minimum frame size — and the honest version of the derivation

A sender must **still be transmitting** when the worst-case collision signal gets back to it. Otherwise it finishes, considers the frame sent, and never learns it was destroyed.

```
   T_t >= 2 * T_p     ->     L/B >= 2d/v     ->     L >= 2dB/v
```

Computed for classic Ethernet — 10 Mbps over a 2500 m maximum span:

```
  pure propagation over 2500 m:      Tp = 12.50 us, 2Tp = 25.00 us
  bits sendable in 2Tp at 10 Mbps: 250 bits = 31 bytes
  but the standard's SLOT TIME is   51.2 us = 512 bits = 64 bytes
  the ratio is 2.05x.
```

**The formula gives 250 bits and Ethernet specifies 512.** That gap is real and worth explaining rather than glossing over, because the extra budget is **not propagation**:

- up to **4 repeaters** in the maximum configuration, each adding store-and-forward and jitter delay
- the **32-bit jam signal** the colliding station must transmit
- transceiver and PHY latency at both ends
- engineering margin

So the honest statement is: **`L ≥ 2dB/v` is the floor; 512 bits is the standardised slot time that includes all the other delays.** Exams ask for the floor and expect the formula; Ethernet ships 64 bytes. Being able to say both is strictly better than knowing either.

### And why 64 bytes survived three orders of magnitude

```
  standard            rate  max span       2Tp  2Tp*B (bits)
  10BASE5            10Mbps    2500m   25.00us           250
  100BASE-TX        100Mbps     250m    2.50us           250
  1000BASE-T       1000Mbps      25m    0.25us           250
```

Each generation raised the rate tenfold and **cut the maximum span to a tenth**, which holds `2Tp × B` constant — so the same 64-byte minimum keeps working. That is a deliberate design decision, not a coincidence, and it is a satisfying thing to be able to point out.

Gigabit also defines **carrier extension**, padding half-duplex frames to 512 *bytes*. Nobody uses it, because:

> **CSMA/CD is effectively dead.** It only runs in half-duplex mode on a shared medium. Every modern Ethernet port is switched and full-duplex, which means a dedicated collision domain per port and separate wires for each direction — so there is nothing to collide with. Gigabit and faster are full-duplex only. The protocol is still examined in detail and has not run on a real office network in twenty years. Say that and you have answered "is CSMA/CD still used".

Two more numbers from the same arithmetic: a frame **shorter** than 64 bytes that appears on the wire is a **runt** and is discarded as a collision fragment; this is also why Ethernet has a **minimum payload of 46 bytes** (64 − 18 of header and FCS) and pads anything smaller.

---

## 2.5 CSMA/CA: why Wi-Fi is different

Wireless **cannot detect collisions**, for three independent reasons, and this is the question that separates a memorised answer from an understood one:

1. **A radio cannot listen while transmitting.** Its own signal is overwhelmingly stronger than anything else at its antenna, so there is nothing to hear a collision *against*. (Full-duplex radio is a research topic, not a product.)
2. **The hidden-terminal problem.** A and C can both reach B but cannot hear each other, so each senses an idle channel and both transmit to B. The collision happens at B and neither sender can detect it.
3. **The exposed-terminal problem.** The mirror image: B is transmitting to A, and C defers because it hears B — even though C's transmission to D would not have interfered with anything. Sensing costs throughput here.

```
 HIDDEN TERMINAL                        EXPOSED TERMINAL
   A ) ) ) [B] ( ( ( C                    A ( ( ( [B]  [C] ) ) ) D
   A and C cannot hear each other         C hears B and defers
   -> both transmit, collision at B       -> but C->D would NOT have collided
   -> cost: a real collision nobody        -> cost: wasted idle time
      can detect
```

So Wi-Fi does **Collision Avoidance** instead: try not to collide in the first place, and confirm success explicitly.

```
 1. sense the channel; if idle, wait DIFS, then still idle -> send
 2. if busy, pick a random backoff from the contention window and count it
    down ONLY WHILE THE CHANNEL IS IDLE (freeze the counter when busy)
 3. send the frame
 4. WAIT FOR AN EXPLICIT ACK. No ACK = assume collision, double the
    contention window, retry.
 5. optionally RTS/CTS first, to solve hidden terminals
```

**RTS/CTS** is the hidden-terminal fix: the sender asks permission with a short Request To Send, the access point replies Clear To Send, and **every station that hears the CTS stays silent** for the stated duration — including stations that cannot hear the original sender. It costs two extra frames per transmission, so it is normally enabled only above a size threshold.

| | CSMA/CD | CSMA/CA |
|---|---|---|
| Medium | Wired | Wireless |
| Collisions are | **Detected** during transmission | **Avoided**, never detected |
| Can listen while sending | **Yes** | **No** |
| On collision | Abort immediately + jam signal | Nothing happens — detected later by **missing ACK** |
| Acknowledgements | None at layer 2 | **Every frame is ACKed** |
| Backoff | After a detected collision | **Before** transmitting, and the counter freezes while busy |
| Extra mechanism | — | Optional **RTS/CTS**, interframe spaces (DIFS/SIFS) |
| Efficiency | Higher | Lower — ACKs, backoff and interframe spaces are pure overhead |
| Used by | 802.3 Ethernet (half duplex only) | 802.11 Wi-Fi |

**The one-liner:** *"CD detects collisions and recovers; CA tries to prevent them and confirms with an ACK, because a radio cannot hear a collision while it is transmitting."*

---

## 2.6 The Ethernet frame

Built and parsed field by field, with a real CRC-32:

```
  destination MAC  70-61-7b-4c-7a-9f   6 bytes
  source MAC       f8-fe-5e-81-40-7a   6 bytes
  EtherType        0x0800              2 bytes  (IPv4)
  payload          46 bytes (46-1500 allowed)
  FCS (CRC-32)     f453eded            4 bytes
  total on the wire 64 bytes + 8 preamble/SFD + 12 interframe gap
  header+trailer overhead = 6+6+2+4 = 18 bytes  (matches M0's figure)
```

```
 +----------+-----+----------+----------+-----------+-----------+-----+
 | preamble | SFD | dst MAC  | src MAC  | EtherType |  payload  | FCS |
 |  7 bytes |  1  |    6     |    6     |     2     | 46 - 1500 |  4  |
 +----------+-----+----------+----------+-----------+-----------+-----+
  |<-- not counted -->|<------------- 64 to 1518 bytes ------------->|
  and then a 12-byte interframe gap before the next frame
```

| Field | Purpose |
|---|---|
| **Preamble** (7 B) | `10101010` repeated — lets the receiver's clock synchronise |
| **SFD** (1 B) | `10101011` — the two trailing `1`s mark "the frame starts now" |
| **Destination MAC** (6 B) | Who it is for. **First**, so hardware can decide to ignore the rest early |
| **Source MAC** (6 B) | Who sent it — this is what a switch learns from |
| **EtherType** (2 B) | What is inside: `0x0800` IPv4, `0x0806` ARP, `0x86DD` IPv6, `0x8100` VLAN tag |
| **Payload** (46–1500 B) | The IP packet. Padded to 46 if shorter |
| **FCS** (4 B) | CRC-32 over everything from dst MAC onward. The only **trailer** |

Note two details that get asked: the preamble and SFD are **not counted** in the frame length (they are a physical-layer artifact), and the EtherType field doubles as a **length** field in the old 802.3 format — values ≤ 1500 are a length, values ≥ 1536 are a type. That ambiguity is why the boundary is where it is.

### MAC addresses

48 bits, written as six hex bytes. The structure:

```
  70-61-7b : 4c-7a-9f
  |_______|  |_______|
     OUI       NIC-specific
  (vendor,     (assigned by
   assigned     the vendor)
   by IEEE)

  the TWO LOW BITS OF THE FIRST BYTE are flags:
    bit 0 (I/G): 0 = unicast,  1 = multicast or broadcast
    bit 1 (U/L): 0 = globally unique (OUI-based), 1 = locally administered
```

Verified against real addresses:

```
   unicast  70-61-7b-...              first byte 0x70  I/G=0 (unicast)   U/L=0 (global/OUI)
   broadcast ff-ff-ff-...             first byte 0xff  I/G=1 (multicast) U/L=1 (local)
   IPv4 multicast 01-00-5e-...        first byte 0x01  I/G=1 (multicast) U/L=0 (global/OUI)
   VRRP virtual 00-00-5e-00-01-01     first byte 0x00  I/G=0 (unicast)   U/L=0 (global/OUI)
```

**The I/G bit is how a NIC decides in hardware whether a frame might be for it**, which is why it is in the very first byte received. `ff-ff-ff-ff-ff-ff` is the broadcast address — every station accepts it.

Note that the VRRP virtual MAC reads as **unicast and globally assigned**, which is correct: it is a real unicast address from a block IANA reserved for the protocol, not a locally-made-up one.

---

## 2.7 Switching: how a switch learns

A switch starts knowing nothing and learns from the **source** address of every frame it sees.

```
 for each frame arriving on port P with source S and destination D:
   1. LEARN:    table[S] = P       (always, every frame)
   2. FORWARD:  if D is broadcast/multicast      -> FLOOD all ports except P
                else if D is in the table        -> send only to table[D]
                     (and if table[D] == P       -> FILTER, drop it)
                else                             -> FLOOD all ports except P
```

### Verified trace

```
   in  src  dst  learn      action
    1    A    B  learned A  FLOOD (unknown) -> ports [2, 3, 4]
    2    B    A  learned B  FORWARD -> port 1
    3    C   FF  learned C  FLOOD (broadcast) -> ports [1, 2, 4]
    4    D    A  learned D  FORWARD -> port 1
    1    A    D             FORWARD -> port 4
    2    B    C             FORWARD -> port 3

  final MAC table: {'A': 1, 'B': 2, 'C': 3, 'D': 4}
```

Follow the first two rows, because together they are the whole idea: **frame 1 floods** (A is learned from the source, but B's location is unknown) and **frame 2 forwards precisely** (A was learned a moment ago). A switch is a *learning* bridge — it is no better than a hub until it has seen traffic from a station, and it learns a station's location from traffic that station **sends**, never from traffic sent to it.

Three consequences worth knowing:

- **Entries age out** (typically 300 s), so a machine that moves to another port is relocated rather than permanently wrong.
- **A full MAC table** falls back to flooding, which is the basis of a **MAC flooding attack**: fill the table with bogus addresses and the switch degrades into a hub, letting the attacker see everyone's traffic.
- **Store-and-forward vs cut-through**: store-and-forward buffers the whole frame and verifies the FCS before sending it on (safe, adds latency); cut-through starts forwarding as soon as it has read the destination MAC (fast, forwards corrupt frames too). Most switches do store-and-forward.

**Switch vs bridge vs router, in one line each:** a bridge is a two-port software switch (a historical artifact); a switch is a many-port hardware bridge; a router does the same job one layer up, on IP addresses, between networks rather than within one.

---

## 2.8 ARP: from IP address to MAC address

A host knows the destination's **IP** address and must put a **MAC** address in the Ethernet header. ARP is the bridge between layer 3 and layer 2, which is why it belongs to neither (M0 called it "layer 2.5").

```
 Host A (10.145.68.45) wants to send to 10.145.67.41

 1. A checks: is the target in MY subnet?   (uses the mask -- M3)
      YES -> I need the TARGET's MAC
      NO  -> I need the DEFAULT GATEWAY's MAC instead
 2. A looks in its ARP cache. Hit -> done.
 3. Miss -> ARP REQUEST, BROADCAST to ff-ff-ff-ff-ff-ff:
      "who has 10.145.67.41? tell 10.145.68.45"
      (every host on the segment receives and inspects it)
 4. Only the owner replies -- ARP REPLY, UNICAST back to A:
      "10.145.67.41 is at f8-fe-5e-81-40-7a"
 5. A caches it (typically a few minutes) and sends the frame.
```

**Request is broadcast, reply is unicast.** That asymmetry is the most commonly asked detail. Note also that every host that sees the request learns the *sender's* mapping for free, which is why ARP caches fill up without anyone asking.

### Step 1 is the part people miss

Whether ARP targets the destination or the gateway is decided **by the subnet mask**, and it explains a pattern that otherwise looks strange:

> **A packet leaving your subnet has the final destination's IP address and the router's MAC address.** Layer 3 is end-to-end, layer 2 is hop-to-hop (M0). If you understand this one sentence, you understand why there are two address systems.

### Verified: this machine's real ARP table

```
  IP                 MAC                 type      what it is
  10.145.0.2         00-00-5e-00-01-01   dynamic   VRRP virtual MAC, group 1
  10.145.0.3         70-61-7b-4c-7a-9f   dynamic   real NIC, OUI 70-61-7b
  10.145.55.211      da-56-55-1e-82-ce   dynamic   real NIC, OUI da-56-55
  10.145.67.41       f8-fe-5e-81-40-7a   dynamic   real NIC, OUI f8-fe-5e
  10.145.85.58       76-72-9e-c7-a7-83   dynamic   real NIC, OUI 76-72-9e
  10.145.127.255     ff-ff-ff-ff-ff-ff   static    subnet broadcast
  224.0.0.22         01-00-5e-00-00-16   static    IPv4 multicast -> expect 01-00-5e-00-00-16 MATCH
  224.0.0.251        01-00-5e-00-00-fb   static    IPv4 multicast -> expect 01-00-5e-00-00-fb MATCH
  224.0.0.252        01-00-5e-00-00-fc   static    IPv4 multicast -> expect 01-00-5e-00-00-fc MATCH
  239.255.255.250    01-00-5e-7f-ff-fa   static    IPv4 multicast -> expect 01-00-5e-7f-ff-fa MATCH
  255.255.255.255    ff-ff-ff-ff-ff-ff   static    subnet broadcast
```

Four separate things in that table are worth reading carefully, and they confirm each other:

**1. The gateway is a virtual router.** `10.145.0.2` has MAC `00-00-5e-00-01-01`, which is not a vendor address at all — IANA reserved `00-00-5E-00-01-XX` for **VRRP**, with the last byte as the group number. So the default gateway is a redundant *pair* of routers sharing one virtual IP and MAC; if the active one dies, the standby takes over the same addresses and hosts never notice. A real-world detail, visible in one line of `arp -a`.

**2. The multicast MAC mappings are arithmetically checkable, and all four match.** An IPv4 multicast address maps to a MAC by taking the **low 23 bits** of the group address and prefixing `01-00-5e`:

```
  224.0.0.251        -> 01-00-5e-00-00-fb
  239.255.255.250    -> 01-00-5e-7f-ff-fa
  224.255.255.250    -> 01-00-5e-7f-ff-fa      <-- the SAME MAC
  225.0.0.251        -> 01-00-5e-00-00-fb      <-- the SAME MAC
```

Only 23 of the 28 group-address bits fit, so **32 different multicast groups share one MAC address**. The NIC therefore accepts frames the host must discard in software. That is a genuine design compromise, and it is sitting in the real table above.

**3. The broadcast entry confirms the subnet mask.** The machine's address and mask, independently computed:

```
   10.145.68.45 / 255.255.128.0  ->  10.145.0.0/17
   broadcast address              ->  10.145.127.255
   broadcast entry in arp -a      ->  10.145.127.255   MATCH
```

The `/17` is derived purely from the mask, and the resulting broadcast address appears **verbatim** in the ARP table. Two unrelated sources of truth agreeing — which is the strongest sort of verification available without a packet capture.

**4. Both broadcast forms are present.** `255.255.255.255` is the *limited* broadcast (never forwarded by a router) and `10.145.127.255` is the *directed* subnet broadcast. Both map to `ff-ff-ff-ff-ff-ff`.

### ARP variants and the attack

| Variant | What it does |
|---|---|
| **ARP request/reply** | The normal case above |
| **Gratuitous ARP** | An unsolicited reply announcing "this IP is at my MAC" — used on boot, after a failover (VRRP sends one), and to detect address conflicts |
| **Proxy ARP** | A router answers on behalf of a host on another segment, so hosts with a wrong mask still work. A legacy crutch |
| **RARP / BOOTP / DHCP** | The reverse problem — "I know my MAC, what is my IP?" DHCP is the modern answer (M3) |

**ARP spoofing** is the attack, and it is trivially easy because **ARP has no authentication whatsoever**: there is no way to verify a reply, and hosts accept unsolicited ones. An attacker sends a forged reply claiming the gateway's IP is at the attacker's MAC; every host on the segment then sends its outbound traffic to the attacker, who forwards it on and reads or modifies it in between. That is a **man-in-the-middle** on a switched LAN, and it needs no privileged access.

Mitigations, all of which are bolted on: **dynamic ARP inspection** on managed switches (validate replies against DHCP leases), **static ARP entries** for critical hosts, **port security**, and — the honest answer — **encryption at a higher layer**, because TLS makes a successful MITM much less useful (M9).

---

## 2.9 VLANs and spanning tree (Tier 3)

### VLANs

A VLAN splits one physical switch into several logical broadcast domains. Ports in VLAN 10 cannot reach ports in VLAN 20 without a router, even though they are in the same box.

- **Access port**: belongs to exactly one VLAN, carries untagged frames, faces a host.
- **Trunk port**: carries many VLANs between switches, and tags each frame with its VLAN ID using **802.1Q** — a 4-byte tag inserted after the source MAC, which is why the EtherType `0x8100` exists and why a tagged frame can be 1522 bytes.
- **Inter-VLAN routing** needs a router or a layer-3 switch; the common pattern is a trunk to a router with a sub-interface per VLAN ("router on a stick").

Why they exist: segmentation without extra hardware, broadcast-domain control, and security separation that follows the person rather than the cable.

### Spanning tree

Redundant links between switches create **loops**, and a layer-2 loop is catastrophic rather than merely wasteful: a broadcast frame circulates forever, is duplicated at every switch, and saturates the network in seconds — a **broadcast storm**. Unlike IP, an Ethernet frame has **no TTL**, so nothing stops it.

**STP** (802.1D) builds a loop-free tree: elect a root bridge (lowest bridge ID), compute each switch's lowest-cost path to it, and **block** every port not on that tree. If a link fails, blocked ports are re-enabled. Classic STP takes 30–50 seconds to converge, which is why **RSTP** (802.1w) exists and is what you actually meet.

Port states to recognise: blocking, listening, learning, forwarding, disabled.

---

## Must remember

```
THE PROBLEM: one shared medium, many senders. Collisions destroy BOTH frames.
 random access (ALOHA, CSMA*) -- great at low load, collapses at high
 controlled access (polling, token) -- predictable, overhead even when idle
 channelization (FDMA/TDMA/CDMA) -- perfect for fixed known stations, wasteful for bursty

ALOHA      S = G e^(-2G)   max 1/(2e) = 18.4% at G=0.5   vulnerable period 2 frame times
SLOTTED    S = G e^(-G)    max 1/e    = 36.8% at G=1.0   vulnerable period 1 frame time
 slotting halves the vulnerable period and exactly DOUBLES throughput (verified)
 past the maximum, throughput FALLS -- congestion collapse in its simplest form

CSMA variants: 1-persistent (jump the instant it is idle -- Ethernet),
 non-persistent (random wait, channel can idle), p-persistent (compromise)
CSMA still collides BECAUSE OF PROPAGATION DELAY: the far station senses idle
 for Tp seconds after you start.

CSMA/CD: sense, transmit WHILE LISTENING, on collision abort + 32-bit JAM,
 then BINARY EXPONENTIAL BACKOFF: k uniform from 0..2^n-1, capped at n=10,
 give up after 16 attempts.
MINIMUM FRAME SIZE: Tt >= 2Tp  ->  L >= 2dB/v
 10 Mbps over 2500 m: the FLOOR is 250 bits = 31 bytes
 the STANDARD is 512 bits = 64 bytes (slot time 51.2 us), because the budget also
 covers 4 repeaters, the 32-bit jam signal, PHY latency and margin. Know both.
 every generation x10 the rate and /10 the span -> 2Tp*B stays 250 -> 64 bytes survives
 min payload 46 bytes (64 - 18); shorter frames on the wire are RUNTS
 CSMA/CD IS EFFECTIVELY DEAD: switched full-duplex ports have nothing to collide with

WIRELESS CANNOT DETECT COLLISIONS, for three reasons:
 1. a radio cannot listen while transmitting (its own signal swamps the antenna)
 2. HIDDEN TERMINAL: A and C cannot hear each other, both transmit to B
 3. EXPOSED TERMINAL: C defers to B unnecessarily, wasting capacity
CSMA/CA: sense + DIFS, random backoff COUNTED DOWN ONLY WHILE IDLE (freezes when
 busy), send, WAIT FOR AN EXPLICIT ACK, no ACK = assume collision and double the
 contention window. Optional RTS/CTS fixes hidden terminals (everyone hearing the
 CTS stays quiet), at the cost of two extra frames.

ETHERNET FRAME  preamble 7 | SFD 1 | dst 6 | src 6 | EtherType 2 | payload 46-1500 | FCS 4
 preamble+SFD are NOT counted; frame is 64-1518; interframe gap 12 bytes
 overhead 18 bytes (matches MTU 1500 -> frame 1518)
 EtherType: 0800 IPv4, 0806 ARP, 86DD IPv6, 8100 VLAN tag
 dst comes FIRST so hardware can discard early
 FCS is the only TRAILER (CRC-32 must cover everything before it)

MAC = 48 bits = OUI (3 bytes, IEEE-assigned vendor) + 3 bytes vendor-assigned
 first byte, bit 0 = I/G (1 = multicast/broadcast), bit 1 = U/L (1 = locally administered)
 ff-ff-ff-ff-ff-ff = broadcast
 01-00-5e-xx-xx-xx = IPv4 multicast, carrying the LOW 23 BITS of the group address
   -> only 23 of 28 bits fit, so 32 GROUPS SHARE ONE MAC (verified on real entries)
 00-00-5e-00-01-xx = VRRP virtual MAC, last byte = group number

SWITCH LEARNING: learn table[src] = in_port on EVERY frame; forward to table[dst]
 if known, else FLOOD. Broadcast always floods. Same-port -> filter.
 a switch learns a station from traffic it SENDS, never from traffic sent TO it
 entries age out (~300 s). A FULL table falls back to flooding -> MAC FLOODING ATTACK
 store-and-forward (checks FCS, adds latency) vs cut-through (faster, forwards corruption)

ARP maps IP -> MAC. REQUEST IS BROADCAST, REPLY IS UNICAST.
 the SUBNET MASK decides whether you ARP for the destination or for the GATEWAY
 -> a packet leaving your subnet carries the DESTINATION's IP and the ROUTER's MAC
 gratuitous ARP = unsolicited announcement (boot, failover, conflict detection)
 proxy ARP = a router answers for a host elsewhere (legacy crutch)
 ARP HAS NO AUTHENTICATION -> ARP SPOOFING is a trivial LAN man-in-the-middle
 mitigations: dynamic ARP inspection, static entries, port security, and TLS above

VLAN = one switch, several broadcast domains. access port = 1 untagged VLAN;
 trunk port = many VLANs, 802.1Q 4-byte tag (EtherType 8100, frame up to 1522).
 inter-VLAN needs a router / L3 switch.
STP exists because an ETHERNET FRAME HAS NO TTL, so a layer-2 loop is a broadcast
 storm, not just waste. Elect a root bridge, block non-tree ports. RSTP converges fast.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "Slotted ALOHA is twice as fast because slots are more efficient" | Because slotting halves the **vulnerable period** from two frame times to one. The factor of two in the exponent is the factor of two in throughput |
| "More offered load means more throughput" | Past the maximum, throughput **falls**. Verified: pure ALOHA delivers 3.7% at `G = 2` versus 18.4% at `G = 0.5` |
| "CSMA eliminates collisions" | It reduces them. Collisions remain **because of propagation delay** — the far station senses idle for `Tp` after you begin |
| "Ethernet uses non-persistent CSMA" | **1-persistent** — it transmits the instant the channel goes idle, and relies on collision detection plus exponential backoff to cope |
| "Exponential backoff waits twice as long each time" | It doubles the **range** it draws from — uniform in `0..2ⁿ−1` — capped at `n = 10`, giving up after 16 tries |
| "The minimum frame size is 64 bytes because `2dB/v` says so" | `2dB/v` gives **250 bits / 31 bytes** for classic Ethernet. 512 bits is the standardised slot time, which also covers 4 repeaters, the jam signal, PHY latency and margin |
| "The minimum frame size got bigger with faster Ethernet" | It stayed 64 bytes because each generation cut the maximum span by the same factor it raised the rate — verified, `2Tp × B` stays at 250 bits |
| "CSMA/CD is how modern Ethernet works" | It only applies to half-duplex shared media. Every switched full-duplex port has its own collision domain, so it never runs. Gigabit and above are full-duplex only |
| "Wi-Fi uses CSMA/CA because it is wireless" | Because a radio **cannot listen while transmitting**, and because of hidden terminals — collisions at the receiver that no sender can observe |
| "In CSMA/CA, collisions are detected and the frame is resent" | Nothing detects them. The sender infers a collision from a **missing ACK** |
| "RTS/CTS prevents all collisions" | It addresses **hidden terminals** by silencing everyone who hears the CTS. It costs two extra frames, so it is usually only used above a size threshold |
| "The exposed-terminal problem causes collisions" | It causes **wasted idle time** — a station defers when it did not need to. Hidden terminals cause collisions |
| "Ethernet frames are 1500 bytes maximum" | The **payload** is 1500. The frame is 1518, and 1522 with a VLAN tag |
| "The preamble is part of the frame" | It is a physical-layer artifact and is not counted in the frame length |
| "The source MAC comes first" | **Destination** first, so hardware can discard a frame that is not for it without reading the rest |
| "A multicast IP maps uniquely to a MAC" | Only 23 of 28 group bits fit, so **32 groups share one MAC**. Verified: `239.255.255.250` and `224.255.255.250` both map to `01-00-5e-7f-ff-fa` |
| "A switch learns from the destination address" | From the **source** address. It learns where a station is from traffic that station sends |
| "A switch always forwards to the right port" | Not until it has learned the destination. Verified: frame 1 floods, frame 2 forwards |
| "Filling a switch's MAC table just slows it down" | It makes the switch **flood**, turning it into a hub — which is the point of a MAC flooding attack |
| "ARP replies are broadcast" | The **request** is broadcast; the **reply** is unicast back to the asker |
| "ARP finds the MAC of the destination" | Only if the destination is in your subnet. Otherwise it finds the **gateway's** MAC — the mask decides, and the packet then carries the destination's IP with the router's MAC |
| "ARP spoofing needs admin access or a compromised switch" | It needs nothing. ARP has **no authentication**, and hosts accept unsolicited replies |
| "A VLAN is a security boundary you can rely on" | It is a broadcast-domain boundary. VLAN hopping and trunk misconfiguration are real; do not treat it as a substitute for encryption |
| "Spanning tree exists to improve performance" | It exists because an Ethernet frame has **no TTL**, so a loop becomes a broadcast storm. STP blocks links to prevent that |

---

## Interview Q&A bank

**Q1. What is the multiple-access problem?**
When several stations share one medium, overlapping transmissions superimpose and destroy each other. The protocols that solve it fall into random access, controlled access and channelization.

**Q2. Why is slotted ALOHA twice as efficient as pure ALOHA?**
Because requiring transmissions to begin on slot boundaries removes partial overlap, halving the vulnerable period from two frame times to one. That turns `G·e^(−2G)` into `G·e^(−G)`, so the maximum rises from `1/2e` ≈ 18.4% to `1/e` ≈ 36.8%.

**Q3. What happens to ALOHA throughput as load grows past the optimum?**
It falls. Verified: pure ALOHA delivers 18.4% at `G = 0.5` and only 3.7% at `G = 2.0`, because nearly everything collides. It is the simplest example of congestion collapse.

**Q4. Why does CSMA still have collisions if everyone listens first?**
Propagation delay. For `Tp` seconds after a station starts, stations further away still sense an idle channel and may transmit. Sensing is never instantaneous, so sensing alone cannot eliminate collisions.

**Q5. Which CSMA variant does Ethernet use?**
1-persistent: transmit as soon as the channel goes idle. That is deliberately greedy, and it is paired with collision detection and binary exponential backoff to cope with the resulting collisions.

**Q6. Explain binary exponential backoff.**
After the `n`th collision, wait a random multiple of the slot time drawn uniformly from `0` to `2ⁿ−1`, capped at `n = 10`, and abandon the frame after 16 attempts. Doubling the range lets the backoff adapt to the load without any station needing to know what the load is.

**Q7. Why does Ethernet have a minimum frame size?**
So a sender is still transmitting when the worst-case collision signal returns; otherwise it would finish, assume success, and never learn the frame was destroyed. The constraint is `Tt ≥ 2Tp`, i.e. `L ≥ 2dB/v`.

**Q8. Work out that minimum for 10 Mbps over 2500 m.**
`Tp = 12.5 µs`, so `2Tp = 25 µs`, which at 10 Mbps is 250 bits or about 31 bytes. Ethernet specifies 512 bits — 64 bytes — because the standardised slot time of 51.2 µs also budgets for four repeaters, the 32-bit jam signal, transceiver latency and margin. The formula gives the floor; 64 bytes is the standard.

**Q9. Why is the minimum still 64 bytes on gigabit Ethernet?**
Because each generation raised the rate tenfold and cut the maximum span to a tenth, keeping `2Tp × B` constant at 250 bits. Gigabit also defines carrier extension to 512 bytes for half duplex, which is unused because gigabit is switched full-duplex.

**Q10. Is CSMA/CD still used?**
Effectively no. It only operates in half-duplex mode on a shared medium, and every modern switched port is full-duplex with its own collision domain, so there is nothing to collide with. It is still examined thoroughly and has not run on an office LAN in two decades.

**Q11. Why can't Wi-Fi detect collisions?**
Three reasons: a radio cannot meaningfully listen while transmitting because its own signal swamps its receiver; hidden terminals mean two senders that cannot hear each other collide at the receiver, which neither can observe; and in any case the collision happens at the receiver, not at the sender.

**Q12. What is the hidden-terminal problem, and the exposed-terminal problem?**
Hidden: A and C can both reach B but not each other, so both transmit and collide at B undetectably. Exposed: C hears B transmitting and defers, even though C's transmission to D would not have interfered — so it wastes capacity rather than causing a collision.

**Q13. How does CSMA/CA work?**
Sense the channel, wait an interframe space, and if still idle transmit. If busy, pick a random backoff and count it down only while the channel is idle. Then wait for an explicit acknowledgement — a missing ACK is the only evidence of a collision — and on failure double the contention window. RTS/CTS optionally reserves the medium to handle hidden terminals.

**Q14. CSMA/CD vs CSMA/CA in one sentence?**
CD detects collisions during transmission and aborts; CA tries to avoid them and confirms success with an explicit ACK, because a radio cannot hear a collision while sending.

**Q15. Walk me through the Ethernet frame.**
Preamble and start-of-frame delimiter for clock synchronisation and are not counted; destination MAC first so hardware can discard early; source MAC, which is what switches learn from; EtherType saying what is inside; a 46-to-1500-byte payload; and a CRC-32 frame check sequence as the only trailer. The frame is 64 to 1518 bytes, with 18 bytes of overhead.

**Q16. How is a MAC address structured?**
48 bits: a three-byte IEEE-assigned OUI identifying the vendor, plus three vendor-assigned bytes. In the first byte, the low bit is the individual/group flag — set for multicast and broadcast — and the next bit marks a locally administered address.

**Q17. How does an IPv4 multicast address map to a MAC address?**
The low 23 bits of the group address are prefixed with `01-00-5e`. Only 23 of the 28 group bits fit, so 32 different groups share one MAC — verified on real entries, where `239.255.255.250` and `224.255.255.250` both map to `01-00-5e-7f-ff-fa`. The host must filter the overlap in software.

**Q18. How does a switch know where to send a frame?**
It learns `source MAC → incoming port` from every frame, and forwards to the port recorded for the destination. If the destination is unknown or is a broadcast, it floods every other port. Entries age out after a few minutes.

**Q19. What happens if a switch's MAC table is full?**
It floods, behaving like a hub. That is exactly the goal of a MAC flooding attack: fill the table with bogus source addresses and the switch starts broadcasting everyone's traffic.

**Q20. What is ARP, and which message is broadcast?**
ARP resolves an IP address to a MAC address on the local segment. The request is **broadcast** — "who has this IP?" — and the reply is **unicast** back to the asker.

**Q21. Does ARP always resolve the destination's address?**
No. The subnet mask decides: if the destination is off-subnet, the host ARPs for the **default gateway** instead. So a packet leaving your subnet carries the final destination's IP address and the router's MAC address — which is the layer-3-versus-layer-2 distinction made concrete.

**Q22. What is gratuitous ARP for?**
An unsolicited ARP reply announcing a mapping. Used at boot, to detect duplicate addresses, and after a failover — a VRRP pair sends one when the standby takes over, so switches relearn the port immediately.

**Q23. What is ARP spoofing and how do you defend against it?**
ARP has no authentication and hosts accept unsolicited replies, so an attacker can claim the gateway's IP is at their MAC and become a man-in-the-middle on a switched LAN. Defences are dynamic ARP inspection on managed switches, static entries for critical hosts, port security — and encryption above, since TLS makes a successful MITM much less useful.

**Q24. Why do VLANs exist?**
To split one physical switch into several broadcast domains, giving segmentation and separation without extra hardware. Access ports carry one untagged VLAN; trunks carry many, tagged with 802.1Q; crossing between VLANs needs a router or layer-3 switch.

**Q25. Why is spanning tree necessary?**
Because an Ethernet frame has no TTL, so a layer-2 loop makes a broadcast circulate and multiply forever — a broadcast storm that saturates the network in seconds. STP elects a root bridge and blocks non-tree ports to keep the topology loop-free while retaining the physical redundancy.

---

## Practice

1. Compute the maximum throughput of pure and slotted ALOHA, and the offered load at which each occurs. Then say what physical fact explains the factor of two.
2. A slotted ALOHA network carries 200 stations, each sending one frame per 100 slots on average. What is `G`, and what throughput should you expect?
3. A 10 Mbps Ethernet has a 1 km span. Compute the minimum frame size from first principles. Then explain why Ethernet specifies 64 bytes rather than your answer.
4. A 100 Mbps Ethernet keeps the 64-byte minimum. What is the greatest span this permits by the `2dB/v` argument alone?
5. Two stations collide. Station A draws backoff `k = 0` and station B draws `k = 1`. What happens next, and what are the odds of another collision on the retry if both have collided once?
6. Explain why a collision at a Wi-Fi access point cannot be detected by either sender, and give the two mechanisms 802.11 uses instead.
7. A frame arrives on port 3 with source `AA` and destination `BB`. The table holds `{BB: 3, CC: 1}`. What does the switch do, and what does the table hold afterwards?
8. Same switch, next frame: port 1, source `CC`, destination `AA`. What happens?
9. Host `10.0.1.5/24` sends to `10.0.1.9` and then to `8.8.8.8`. For each, say whose MAC address ends up in the Ethernet header and why.
10. An IPv4 multicast group `232.1.2.3` is in use. Give its MAC address, and name another group that shares it.
11. You see 60,000 MAC addresses in a switch's table on a network with 40 hosts. What is happening, what is the attacker's goal, and what single feature stops it?
12. A network has two switches connected by two cables for redundancy. Describe exactly what happens without STP, in order, within the first second.

**Answers to 3, 9 and 12:**

> **3.** `Tp = 1000/2×10⁸ = 5 µs`, so `2Tp = 10 µs`, and at 10 Mbps that is **100 bits = 12.5 bytes**. Ethernet still specifies 64 bytes because the 51.2 µs slot time is sized for the *maximum* 2500 m configuration with four repeaters, plus the 32-bit jam signal and PHY latency — and one fixed minimum has to work for every legal topology, so it is set by the worst case, not yours.
>
> **9.** To `10.0.1.9`: the mask `/24` puts it in the same subnet, so the host ARPs for `10.0.1.9` and the frame carries **that host's MAC**. To `8.8.8.8`: off-subnet, so the host ARPs for its **default gateway** and the frame carries the **router's MAC** while the IP header still says `8.8.8.8`. Destination IP is end-to-end; destination MAC is only ever the next hop.
>
> **12.** A host sends one broadcast — an ARP request, say. Switch 1 floods it out both cables to switch 2. Switch 2 floods each copy out its other ports, including the second cable back to switch 1. Switch 1 floods those again. The frame count doubles on every pass, each switch's MAC table thrashes because the same source address keeps arriving on alternating ports, and because **an Ethernet frame has no TTL**, nothing ever discards it. Within a second the links are saturated and the network is unusable — a broadcast storm, from a single ARP request.

---

## Exit checklist

```
[ ] I can name the three families of medium-access protocol and when each suits
[ ] I know both ALOHA formulas and both maxima, and WHY the factor is two
[ ] I know throughput FALLS past the optimum, and what that phenomenon is called
[ ] I can name the three CSMA persistence variants and say which Ethernet uses
[ ] I can explain why sensing cannot eliminate collisions
[ ] I can state the CSMA/CD algorithm including the jam signal
[ ] I can explain binary exponential backoff precisely (range, cap, give-up)
[ ] I can derive the minimum frame size from Tt >= 2Tp
[ ] I know the derived floor (250 bits) differs from the standard (512) and WHY
[ ] I can explain why 64 bytes survived from 10 Mbps to 1 Gbps
[ ] I can say whether CSMA/CD still runs, and justify it
[ ] I can give all three reasons wireless cannot detect collisions
[ ] I can describe hidden and exposed terminals and the different costs of each
[ ] I can state the CSMA/CA algorithm, including the frozen backoff counter
[ ] I know a missing ACK is the only collision evidence Wi-Fi gets
[ ] I know what RTS/CTS fixes and what it costs
[ ] I can fill in the CSMA/CD vs CSMA/CA table from memory
[ ] I can draw the Ethernet frame with every field and its size
[ ] I know the preamble is not counted, and the frame is 64-1518 (1522 tagged)
[ ] I know why the destination MAC comes first
[ ] I can decode a MAC address: OUI, I/G bit, U/L bit
[ ] I can map an IPv4 multicast address to its MAC and explain the 32:1 ambiguity
[ ] I can recognise a VRRP virtual MAC and say what it implies
[ ] I can trace switch learning frame by frame and say when it floods
[ ] I know a switch learns from the SOURCE address only
[ ] I can explain MAC flooding and how a full table degrades the switch
[ ] I know store-and-forward vs cut-through
[ ] I can describe ARP, and I know request = broadcast, reply = unicast
[ ] I know the MASK decides whether I ARP for the host or the gateway
[ ] I can state the destination-IP / next-hop-MAC rule in one sentence
[ ] I can explain gratuitous ARP and proxy ARP
[ ] I can explain ARP spoofing, why it is trivial, and four mitigations
[ ] I can explain VLAN access vs trunk ports and 802.1Q tagging
[ ] I can explain why STP exists, starting from "an Ethernet frame has no TTL"
```

---

## Next

**Part 5: M3 — IP Addressing and Subnetting.** The second numericals centrepiece, and the arithmetic you may be asked to do on a whiteboard. The **IPv4 header field by field**; **fragmentation, MTU and a worked fragmentation numerical**; classful addressing and why it died; **CIDR, masks and prefix arithmetic**; **subnetting as a mechanical procedure, drilled on this machine's own `/17`**; **VLSM** worked end to end for a real address plan; supernetting and route aggregation; the special addresses — loopback, APIPA, private ranges, broadcast; **NAT and PAT** and what they break; **DHCP's DORA**; **ICMP** and what `ping` and `tracert` actually send; and **IPv6** in one Tier-2 section.
