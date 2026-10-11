# Computer Networks Placement Handbook — Part 5
# Module 3: IP Addressing and Subnetting

**Module 3 · 5 hours · Tier 1 · Requires: M0 (layering, MTU), M2 (ARP, frames)**

---

## Why this module matters

This is the **second numericals centrepiece** and the only piece of arithmetic in the whole subject you may be asked to do **on a whiteboard, out loud, under pressure**. InterviewBit's 2026 list puts subnetting at question 8 — it is front-loaded, not advanced.

The questions are completely predictable:

- Given an address and a mask, give the **network, broadcast, host range and usable count**
- Design a **VLSM** plan for subnets of unequal size
- How many **subnets and hosts** if I borrow `n` bits?
- What are the **private ranges**? What is `169.254.x.x`?
- What is **NAT** and what does it break? What is **DHCP's DORA**?
- What does **`ping`** actually send? What does **`tracert`** actually send?

So this module is drilled rather than discussed: a mechanical procedure, run until it is automatic.

The organising principle:

> **An IP address is not an identifier, it is a location — and a mask is the instruction for how much of that address names the location and how much names the host within it. Every subnetting question is the same three bit operations: AND with the mask for the network, OR with the wildcard for the broadcast, and count the host bits for the size. Everything else in this module — CIDR, VLSM, supernetting, NAT — is a consequence of treating the prefix length as a variable instead of a constant.**

**How this module was verified.** The subnetting toolkit computes every answer twice — once from raw bit arithmetic I wrote, once via Python's `ipaddress` module, which is an independent implementation of the same RFCs. They agreed on **50,000 random (address, prefix) pairs with 0 mismatches**, plus seven textbook cases, a prefix↔mask round trip over all 33 prefixes, rejection of all four malformed masks, and a minimality check on `hosts_to_prefix` over 4,999 sizes. The IPv4 header was built and parsed field by field with a verified checksum; fragmentation, the private ranges, IPv6 notation and the classful arithmetic are all program output; and **NAT is demonstrated live**.

One happy accident: **this machine's address changed while I was writing this module**, from a `/17` on one subnet to a `/24` on another. That is DHCP doing its job, and §3.9 uses it as the demonstration.

---

## 3.1 The IPv4 header

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-------+-------+---------------+-------------------------------+
 |Version|  IHL  |      ToS      |         Total Length          |
 +-------+-------+---------------+-----+-------------------------+
 |        Identification         |Flags|     Fragment Offset     |
 +---------------+---------------+-----+-------------------------+
 |      TTL      |   Protocol    |        Header Checksum        |
 +---------------+---------------+-------------------------------+
 |                       Source IP Address                       |
 +---------------------------------------------------------------+
 |                     Destination IP Address                    |
 +---------------------------------------------------------------+
 |                    Options (0-40 bytes, rare)                 |
 +---------------------------------------------------------------+
```

Built and parsed for real:

```
  raw: 450005dc1c4640004006943d0a91442d5db8d822

  version            4                    4 bits
  IHL                5  (20 bytes)        4 bits   <- in 32-bit WORDS
  type of service    0x00                 8 bits   (DSCP + ECN)
  total length       1500                16 bits   <- header + DATA
  identification     0x1c46              16 bits   <- groups fragments
  flags              010                  3 bits   (reserved=0, DF=1, MF=0)
  fragment offset    0                   13 bits   <- in 8-BYTE units
  TTL                64                   8 bits   <- decremented per hop
  protocol           6  (TCP)             8 bits
  header checksum    0x943d              16 bits   <- HEADER ONLY, redone per hop
  source IP          10.145.68.45        32 bits
  destination IP     93.184.216.34       32 bits

  checksum verifies at the receiver: 0x0000 (must be 0x0000)
```

### The fields that actually get asked

| Field | What to know |
|---|---|
| **IHL** | Header length in **32-bit words**, not bytes. So 5 means 20 bytes. Min 5, max 15 → header is 20–60 bytes |
| **Total length** | Header **plus** data, in bytes. 16 bits → a theoretical maximum packet of 65,535 bytes |
| **Identification** | Same value in every fragment of one original packet — this is what groups them at reassembly |
| **Flags** | 3 bits: reserved (0), **DF** (don't fragment), **MF** (more fragments) |
| **Fragment offset** | Where this fragment's data starts, **in units of 8 bytes** — which is why every fragment but the last must carry a multiple of 8 |
| **TTL** | Decremented by every router; at 0 the packet is dropped and an ICMP Time Exceeded is returned. Loop protection, and what `traceroute` exploits |
| **Protocol** | The demultiplexing field: 1 = ICMP, 6 = TCP, 17 = UDP |
| **Header checksum** | Covers the **header only**, not the data — and **must be recomputed at every hop** because TTL changed |

Three things to notice together, because they explain each other:

1. **The checksum covers only the header.** Data integrity is left to the layer below (Ethernet's CRC-32) and the layer above (TCP's checksum). IP checks only what IP is responsible for.
2. **It must be recomputed per hop**, which is why it is a cheap one's-complement sum rather than a CRC — the cost argument from M1 §1.2, made concrete.
3. **IPv6 dropped the header checksum entirely**, on the reasoning that layer 2 and layer 4 both already check, so a third check is pure per-hop cost.

### TTL and traceroute, verified

```
  a router decrements TTL; at zero it DISCARDS the packet and sends back
  ICMP Time Exceeded (type 11). traceroute sends TTL=1, then 2, then 3...
  and reads the source address of each ICMP error. That is the whole trick.

   Tracing route to one.one.one.one [1.1.1.1]
     1    <1 ms    <1 ms    <1 ms  10.105.73.2
     2    <1 ms    <1 ms    <1 ms  10.120.1.5
     3    <1 ms    <1 ms    <1 ms  10.250.1.2
     4     *        *        *     Request timed out.
```

Hop 1 answered the TTL=1 probe, hop 2 the TTL=2 probe, and so on. The timeouts from hop 4 are routers whose ICMP replies this network filters — so traceroute degrades gracefully into asterisks rather than failing, which is worth knowing when you are debugging with it.

---

## 3.2 Addresses, masks and CIDR

An IPv4 address is 32 bits, written as four decimal octets. A **mask** splits it:

```
   10.145.68.45    with mask 255.255.128.0

   address  00001010 10010001 01000100 00101101
   mask     11111111 11111111 10000000 00000000
            |<------ network ----->|<- host -->|
                  17 bits             15 bits

   written in CIDR notation:  10.145.68.45/17
```

**The mask is a run of ones followed by a run of zeros, and nothing else.** That is a hard rule, and it is why `255.255.0.255` is not a valid mask. Verified — all four malformed masks were rejected:

```
  non-contiguous masks rejected: 4/4
      255.255.0.255   255.0.255.0   0.255.255.255   255.255.255.1
```

**CIDR** (classless inter-domain routing) is just the decision to carry the prefix length explicitly, rather than inferring it from the first octet. That one change is what made subnetting, VLSM and route aggregation possible.

---

## 3.3 The procedure

Eight steps, and they never change. Worked here on a real address from this machine:

```
  given: 10.145.68.45 with mask 255.255.128.0

  step 1  mask -> prefix: count the 1 bits = /17
  step 2  host bits = 32 - 17 = 15
  step 3  network  = address AND mask        = 10.145.0.0
  step 4  wildcard = NOT mask                = 0.0.127.255
  step 5  broadcast= network OR wildcard     = 10.145.127.255
  step 6  first host = network + 1           = 10.145.0.1
  step 7  last host  = broadcast - 1         = 10.145.127.254
  step 8  total = 2^15 = 32,768   usable = total - 2 = 32,766
```

And in binary, which is where the AND actually happens:

```
   address  00001010100100010100010000101101   10.145.68.45
   mask     11111111111111111000000000000000   255.255.128.0
   AND      00001010100100010000000000000000   10.145.0.0      <- network
   wildcard 00000000000000000111111111111111   0.0.127.255
   OR       00001010100100010111111111111111   10.145.127.255  <- broadcast
```

**Why `−2`:** the all-zeros host part is the network identifier and the all-ones host part is the directed broadcast, so neither can be assigned to a machine. Two exceptions worth knowing: a **`/31`** has 2 addresses and 0 usable by that rule, but RFC 3021 permits both on a point-to-point link; and a **`/32`** is a single host route.

### The table to memorise

```
   prefix mask               block  subnets of /24  usable hosts
      /24 255.255.255.0        256               1           254
      /25 255.255.255.128      128               2           126
      /26 255.255.255.192       64               4            62
      /27 255.255.255.224       32               8            30
      /28 255.255.255.240       16              16            14
      /29 255.255.255.248        8              32             6
      /30 255.255.255.252        4              64             2
```

**The "block size" is the shortcut that makes this fast by hand.** Block size = `256 − last octet of the mask` = `2^(host bits)`. Subnets start at **multiples of the block size**:

```
   /25: block 128 -> .0 .128
   /26: block  64 -> .0 .64 .128 .192
   /27: block  32 -> .0 .32 .64 .96 .128 .160 .192 .224
   /28: block  16 -> .0 .16 .32 .48 .64 .80 .96 .112 .128 ...
```

So for `192.168.1.130/25`: block is 128, multiples are 0 and 128, and 130 falls in the **128** block. Network `192.168.1.128`, broadcast `192.168.1.255`, range `.129–.254`. **That is a five-second answer once the block sizes are memorised**, and it is how you do this on a whiteboard.

### Verified worked problems

```
  192.168.10.0/26   mask 255.255.255.192 net 192.168.10.0   bcast 192.168.10.63   range 192.168.10.1 - 192.168.10.62    (62 usable)
  192.168.1.130/25  mask 255.255.255.128 net 192.168.1.128  bcast 192.168.1.255   range 192.168.1.129 - 192.168.1.254   (126 usable)
  172.16.35.123/20  mask 255.255.240.0   net 172.16.32.0    bcast 172.16.47.255   range 172.16.32.1 - 172.16.47.254     (4,094 usable)
  204.55.77.89/28   mask 255.255.255.240 net 204.55.77.80   bcast 204.55.77.95    range 204.55.77.81 - 204.55.77.94     (14 usable)
  200.1.2.3/30      mask 255.255.255.252 net 200.1.2.0      bcast 200.1.2.3       range 200.1.2.1 - 200.1.2.2           (2 usable)
  192.168.5.77/29   mask 255.255.255.248 net 192.168.5.72   bcast 192.168.5.79    range 192.168.5.73 - 192.168.5.78     (6 usable)
```

Note `172.16.35.123/20`: the mask's third octet is 240, so the block size is 16 **in the third octet**, and the multiples are 0, 16, 32, 48 — so 35 falls in the **32** block, giving `172.16.32.0`. The same block-size trick works in any octet; you just have to notice which octet the prefix lands in.

### Counting subnets and hosts

```
   borrowed  prefix   subnets  host bits  usable hosts
          0     /24         1          8           254
          1     /25         2          7           126
          2     /26         4          6            62
          3     /27         8          5            30
          4     /28        16          4            14
```

Borrow `s` bits from the host part: you get **`2^s` subnets** of **`2^(host bits) − 2` hosts** each. Note that the two halves multiply to *less* than the original — each new subnet loses its own network and broadcast address, so splitting a `/24` into four `/26`s costs you 6 usable addresses.

---

## 3.4 VLSM — variable length subnet masking

Fixed-size subnetting wastes space whenever the subnets are different sizes. **VLSM** uses a different prefix per subnet.

**The procedure, and the order matters:**

```
  1. sort the requirements LARGEST FIRST
  2. for each, pick the smallest prefix whose usable count is big enough
     (2^h - 2 >= needed  ->  h bits  ->  prefix 32 - h)
  3. allocate from the lowest free address, but ALIGNED: every block must
     start at a multiple of its own size
  4. move the cursor past the block and repeat
```

### Verified end to end

```
  requirement: 192.168.1.0/24 split for
    Sales             100 hosts
    Engineering        50 hosts
    HR                 25 hosts
    Ops                10 hosts
    link to branch      2 hosts

  name              need  prefix network           range                            usable
  Sales              100     /25 192.168.1.0/25    192.168.1.1 - 192.168.1.126         126
  Engineering         50     /26 192.168.1.128/26  192.168.1.129 - 192.168.1.190        62
  HR                  25     /27 192.168.1.192/27  192.168.1.193 - 192.168.1.222        30
  Ops                 10     /28 192.168.1.224/28  192.168.1.225 - 192.168.1.238        14
  link to branch       2     /30 192.168.1.240/30  192.168.1.241 - 192.168.1.242         2

  addresses still free in the /24: 12
```

Check the sizing decisions, because this is where marks are lost: 100 hosts needs **`/25`** (126 usable) because a `/26` gives only 62. 50 needs `/26` (62), not `/27` (30). A point-to-point link needs exactly 2, which is what a **`/30`** gives — and `/30` for router-to-router links is the real-world convention.

### Largest-first versus smallest-first

Running the same plan in the wrong order:

```
  the same plan allocated SMALLEST-first:
   link to branch   /30 at 192.168.1.0
   Ops              /28 at 192.168.1.16     <- 12 addresses skipped for alignment
   HR               /27 at 192.168.1.32
   Engineering      /26 at 192.168.1.64
   Sales            /25 at 192.168.1.128
   alignment padding wasted: 12 addresses
```

Both orders consume 12 addresses beyond the requirements, so **smallest-first is not more wasteful in total** — I had expected it to be, and the arithmetic says otherwise. The real difference is **where the slack ends up**: largest-first leaves 12 contiguous addresses **at the end**, available for a future subnet, while smallest-first scatters them as unusable padding *between* allocations. Largest-first is still the right rule, but for the right reason — **contiguity of the remaining free space**, not total waste.

### Why alignment is non-negotiable

A block must start at a multiple of its own size because the network address has to be the result of ANDing with the mask. `192.168.1.100/26` is not a valid network: `100 AND /26` gives `64`, so the block containing `.100` is `192.168.1.64/26`. There is no choice in the matter — **the mask decides where blocks can start**, and that is why alignment padding exists at all.

---

## 3.5 Supernetting and route aggregation

The reverse operation: merge several contiguous blocks into one shorter prefix so a router advertises **one** route instead of many. This is what keeps the global routing table from exploding.

Verified:

```
  172.16.0.0/24, 172.16.1.0/24, 172.16.2.0/24, 172.16.3.0/24
    -> 172.16.0.0/22   (aggregated into one route)
  200.1.0.0/24, 200.1.1.0/24
    -> 200.1.0.0/23   (aggregated into one route)
  10.1.0.0/16, 10.2.0.0/16, 10.3.0.0/16
    -> 10.1.0.0/16, 10.2.0.0/15   (NOT fully aggregable: two routes)
  192.168.0.0/24, 192.168.2.0/24
    -> 192.168.0.0/24, 192.168.2.0/24   (NOT contiguous: stays two routes)
```

Two conditions, both required: the blocks must be **contiguous**, and the combined block must be **aligned** to its own size. Four `/24`s starting at `172.16.0.0` satisfy both and collapse to a `/22`. But look at the third case — `10.1`, `10.2`, `10.3` are contiguous yet **cannot all merge**, because a `/14` starting at `10.0.0.0` would also cover `10.0.0.0/16` which was not in the set. The best possible is a `/16` plus a `/15`, and the tool found exactly that. **Partial aggregation is the normal outcome**, which is a more honest picture than the textbook example where everything collapses neatly.

The procedure by hand: write the blocks in binary, find the **longest common prefix**, and check that the resulting block contains nothing else you did not intend.

---

## 3.6 Classful addressing, and the arithmetic that killed it

```
  class  leading bits  first octet  default prefix    networks   hosts each
  A      0             1-126        /8                     128   16,777,214
  B      10            128-191      /16                 16,384       65,534
  C      110           192-223      /24              2,097,152          254
  D      1110          224-239      multicast
  E      1111          240-255      reserved
```

A correction worth making, because exam answers differ: the bit patterns give **128** class A networks, but `0.0.0.0/8` is reserved and `127.0.0.0/8` is loopback, so there are **126 usable** class A networks. Class B's 16,384 and class C's 2,097,152 are all usable.

**Why it died**, computed:

```
  a company needing 300 hosts could not use a class C (254 hosts),
  so it got a class B -- 65,534 addresses, of which it wasted 65,234.
  CIDR gives the same company a /23 (510 hosts), wasting 210 instead.
  waste ratio: 311x better.
```

**That factor of 311 is the whole argument.** Fixed boundaries at /8, /16 and /24 meant the only sizes available were 16 million, 65 thousand and 254, so almost every organisation was forced to over-allocate by orders of magnitude. CIDR made the prefix a free variable, and subnetting, VLSM and aggregation all follow from that.

Classful addressing is dead but its vocabulary survives: people still say "a class C network" meaning a `/24`, and the private ranges are still described by class.

---

## 3.7 Special addresses

Verified against the `ipaddress` module:

```
  address             private  loopback  link-local  multicast  what it is
  0.0.0.0                True     False       False      False  this host / any ("bind all", DHCP source)
  127.0.0.1              True      True       False      False  loopback (all of 127.0.0.0/8)
  169.254.15.67          True     False        True      False  APIPA / link-local -- DHCP FAILED
  10.145.68.45           True     False       False      False  private, 10.0.0.0/8
  172.16.35.123          True     False       False      False  private, 172.16.0.0/12
  192.168.1.1            True     False       False      False  private, 192.168.0.0/16
  100.64.1.1            False     False       False      False  carrier-grade NAT, 100.64.0.0/10
  224.0.0.251           False     False       False       True  multicast -- mDNS
  255.255.255.255        True     False       False      False  limited broadcast -- NEVER forwarded
  10.145.127.255         True     False       False      False  directed subnet broadcast
  8.8.8.8               False     False       False      False  ordinary public address
```

```
  the private ranges (RFC 1918), and how many addresses each holds:
   10.0.0.0/8           16,777,216 addresses   (10.0.0.0 - 10.255.255.255)
   172.16.0.0/12         1,048,576 addresses   (172.16.0.0 - 172.31.255.255)
   192.168.0.0/16           65,536 addresses   (192.168.0.0 - 192.168.255.255)
```

**Memorise the three private ranges** — it is a one-mark question and it comes up constantly. Note the middle one is `172.16.0.0/12`, so it runs to `172.31.255.255`, **not** `172.16.255.255`. That off-by-16 is the usual mistake.

### The two broadcast forms

| | `255.255.255.255` | `10.145.127.255` |
|---|---|---|
| Name | **Limited** broadcast | **Directed** / subnet broadcast |
| Scope | The local link only | A specific subnet |
| Forwarded by a router | **Never** | Historically yes; now blocked by default (it was a DDoS amplifier — the "smurf attack") |
| Used by | DHCP discovery, before you have an address | Legacy applications |

### `169.254.x.x` — the address that means something is broken

This is worth knowing because it is a **diagnostic**. If a host has a `169.254.x.x` address, **DHCP failed** and the OS self-assigned a link-local address (APIPA). It can talk to other hosts on the same wire that did the same thing, and nothing else — no gateway, no DNS. Seeing it in `ipconfig` tells you to look at the DHCP server or the cable, not at the host's configuration. This machine has one on a disconnected adapter, which is exactly the expected behaviour.

---

## 3.8 NAT and PAT

A private address cannot appear on the internet, so something must translate it. **NAT** rewrites the source address on the way out and reverses the translation on the way back.

### Verified live

```
  the address this host uses as a source: 10.105.73.61  (private: True)
  the address a public server actually sees: 203.110.x.x (private: False)
  -> the source address was REWRITTEN in flight. That is NAT.
```

Two addresses, two different values, one packet. The host believes it is `10.105.73.61`; a public server reports seeing a completely different, public address. Nothing on the host did that — a router in the path rewrote the IP header.

### NAT vs PAT

Plain NAT maps one private address to one public address, which does not help with scarcity. **PAT** (also called NAPT, or "NAT overload") rewrites the **port** as well, so many hosts share one public address:

```
  translation table, keyed on ports:

  private                      public                     destination
  10.0.0.5:51000      <->      203.0.113.7:61001    ->    93.184.216.34:443
  10.0.0.6:51000      <->      203.0.113.7:61002    ->    93.184.216.34:443
  10.0.0.5:51001      <->      203.0.113.7:61003    ->    142.250.library:443
                                            ^
                      the port is what disambiguates the return traffic
```

And the capacity, computed:

```
   IANA dynamic range     16,384 concurrent translations per public IP
   Linux default          28,232 concurrent translations per public IP
   theoretical maximum    64,512 concurrent translations per public IP
```

**One public address supports tens of thousands of simultaneous connections** — which is the real reason IPv4 exhaustion was survivable for two decades rather than catastrophic.

### What NAT breaks

This is the interesting half of the question, and the half candidates usually miss:

| Broken | Why |
|---|---|
| **Inbound connections** | There is no translation entry until the inside host sends something first. You cannot run a server behind NAT without explicit port forwarding |
| **Peer-to-peer** | Both peers are behind NAT, and neither can initiate. Hence STUN, TURN, ICE and hole punching — an entire industry of workarounds |
| **End-to-end addressing** | The internet's original model was that an address identifies a host globally. NAT ends that, and it is why NAT is called a layering violation |
| **Protocols carrying addresses in the payload** | FTP's `PORT` command, SIP and some VoIP protocols embed IP addresses in the data, which NAT does not rewrite — so they need application-layer gateways |
| **IPsec AH** | Authenticates the IP header, which NAT modifies, so the check fails. NAT traversal exists precisely to work around this |
| **Logging and attribution** | Thousands of users behind one address, so a server's logs cannot identify an individual host |

**Does NAT provide security?** The honest answer, which is a good one to give: *"Incidentally and partially. Unsolicited inbound traffic has nowhere to go, which blocks naive scanning — but that is a side effect of address translation, not a security policy. It does nothing about outbound connections, malware already inside, or anything at the application layer. Treat it as a firewall's accidental cousin, not a firewall."*

---

## 3.9 DHCP

A host booting up knows its MAC address and nothing else. DHCP gives it an address, a mask, a gateway and DNS servers.

### DORA

```
  client (0.0.0.0)                                 server
      |                                               |
      |---- DISCOVER -------------------------------->|   broadcast to 255.255.255.255
      |     "anyone there? my MAC is ..."             |   src 0.0.0.0 -- it has no address yet
      |                                               |
      |<--------------------------------- OFFER ------|   "you can have 10.0.0.57,
      |                                               |    mask /24, gw 10.0.0.1, DNS ..."
      |                                               |   (may come from several servers)
      |---- REQUEST --------------------------------->|   broadcast: "I accept THAT offer"
      |     (broadcast, so other servers              |
      |      know their offer was declined)           |
      |                                               |
      |<----------------------------------- ACK ------|   "confirmed, lease 86400 s"
      |                                               |
```

**Why Discover and Request are both broadcast** is the detail worth knowing: Discover has to be, because the client has no address and does not know the server's. Request is broadcast so that **every** server that made an offer learns whether it was accepted — otherwise the others would hold reservations for a client that went elsewhere.

DHCP runs over **UDP**, ports **67** (server) and **68** (client). It must be UDP, because TCP needs addresses on both ends to set up a connection, and the client does not have one yet.

Other messages worth naming: `NAK` (that address is no longer available — start again), `RELEASE` (I am done with this lease), `DECLINE` (I probed and something else is already using this address), and `INFORM` (I have a static address, just give me the options).

Across a router, DHCP needs a **relay agent**, because the Discover broadcast would not be forwarded. The relay unicasts it to a central server and sets the `giaddr` field so the server knows which subnet to allocate from.

### Verified: a lease change, mid-module

This machine's address changed between two runs of this handbook:

```
  earlier today  10.145.68.45/255.255.128.0  -> 10.145.0.0/17   bcast 10.145.127.255   usable 32,766
  now            10.105.73.61/255.255.255.0  -> 10.105.73.0/24  bcast 10.105.73.255     usable 254
```

**The host moved to a different subnet with a different prefix length, and nothing on it was reconfigured.** That is DHCP's entire value proposition demonstrated by accident: addressing is a property of where you are plugged in, not of the machine.

And the M2 cross-check reproduces on the new network, which is the stronger result:

```
  computed broadcast for 10.105.73.0/24 = 10.105.73.255
  broadcast entries in arp -a           = ['10.105.73.255', '255.255.255.255']
  -> MATCH
```

The mask-derived broadcast address appears verbatim in the ARP table on **both** subnets — two unrelated sources of truth agreeing twice, on two different prefix lengths.

One honest difference between the captures: the old gateway's MAC was a **VRRP virtual address** (`00-00-5e-00-01-01`), while the new one, `08-f3-fb-a8-35-a8`, is an ordinary vendor MAC. So the first network had a redundant router pair and this one does not — visible in one line of `arp -a`, and a reminder that these observations are of a real network rather than a diagram.

---

## 3.10 Fragmentation

A router that must forward a packet larger than the outgoing link's MTU either **fragments** it or drops it and complains.

```
  max data per fragment = ((MTU - 20) // 8) * 8
                           ^^^^^^^^^^     ^^^
                           room for data  rounded DOWN to a multiple of 8,
                                          because the offset field counts
                                          in 8-byte units
```

### Verified

```
  3980-byte payload (4000-byte packet) over MTU 1500
   max data per fragment = ((1500-20)//8)*8 = 1480
   -> 3 fragments
    #   data  total len  offset(bytes)  offset field  MF
    1   1480       1500              0             0   1
    2   1480       1500           1480           185   1
    3   1020       1040           2960           370   0
   total bytes on the wire = 4040 (vs 4000: 40 bytes of extra headers)

  2000-byte payload (2020-byte packet) over MTU 620
   max data per fragment = ((620-20)//8)*8 = 600
   -> 4 fragments
    #   data  total len  offset(bytes)  offset field  MF
    1    600        620              0             0   1
    2    600        620            600            75   1
    3    600        620           1200           150   1
    4    200        220           1800           225   0
   total bytes on the wire = 2080 (vs 2020: 60 bytes of extra headers)
```

The three fields doing the work:

- **Identification** — identical in every fragment, so the destination knows which ones belong together
- **Fragment offset** — where this piece starts, in 8-byte units (so offset field 185 means byte 1480)
- **MF** — set on every fragment except the last, so the receiver knows when it has them all

Four facts that get asked:

1. **Reassembly happens only at the final destination**, never at an intermediate router — because different fragments may take different routes and no router can be sure it will see them all.
2. **Losing one fragment destroys the whole packet.** There is no partial delivery and no per-fragment retransmission, so a 1% fragment loss rate on a 4-fragment packet gives nearly 4% packet loss.
3. **Every fragment carries a full 20-byte header**, so fragmentation adds overhead — 40 bytes for the example above.
4. **The last fragment is the only one allowed a non-multiple-of-8 size.**

Which is why fragmentation is avoided in practice: TCP discovers the path MTU and sizes its segments to fit (**MSS negotiation plus path-MTU discovery**), and **IPv6 forbids router fragmentation entirely** — a router that cannot forward a packet drops it and returns an ICMPv6 Packet Too Big, making the source responsible. That shifts work to the endpoints, which is the general IPv6 design philosophy.

**And the trap:** path-MTU discovery depends on receiving **ICMP type 3 code 4** ("fragmentation needed, DF set"). Firewalls that block all ICMP break it, producing the classic failure where small requests work and large ones hang forever — a **black-hole connection**. This network's filtering of ICMP, visible in §3.1's traceroute, is exactly that configuration.

---

## 3.11 ICMP

The control and error-reporting protocol for IP. Carried **inside** IP packets (protocol number 1) but logically part of layer 3 — the layering violation M0 mentioned.

```
  type 0   code     Echo Reply                         ping response
  type 3   code 0   Destination Unreachable (net)      no route
  type 3   code 1   Destination Unreachable (host)     ARP failed on the last hop
  type 3   code 3   Destination Unreachable (port)     UDP with nothing listening
  type 3   code 4   Fragmentation Needed, DF set       PATH MTU DISCOVERY depends on this
  type 5   code     Redirect                           better route available
  type 8   code     Echo Request                       ping
  type 11  code 0   Time Exceeded (TTL)                TRACEROUTE depends on this
  type 11  code 1   Time Exceeded (reassembly)         a fragment never arrived
```

**What `ping` sends:** ICMP Echo Request (type 8); the target replies with Echo Reply (type 0). That is all. `ping` is not TCP, has no ports, and a host that does not answer may simply be configured not to.

**What `traceroute` sends:** probes with increasing TTL, reading the **ICMP Time Exceeded** (type 11) each router returns. Unix `traceroute` traditionally sends UDP datagrams to high ports and uses Destination Unreachable (type 3 code 3) to detect the final hop; Windows `tracert` sends ICMP Echo Requests throughout. Same trick, different probe.

**ICMP is also a diagnostic trap**, and the sentence to say is: *"Blocking all ICMP is a classic over-correction. It hides you from ping but it also breaks path-MTU discovery and traceroute, so you trade a little obscurity for intermittent, extremely hard-to-diagnose failures on large packets."* This machine's network does precisely that — `ping 1.1.1.1` returns 100% loss while TCP to port 443 works perfectly.

---

## 3.12 IPv6 (Tier 2)

The reason is arithmetic:

```
  IPv4: 2^32  = 4,294,967,296
  IPv6: 2^128 = 340,282,366,920,938,463,463,374,607,431,768,211,456
  ratio = 79,228,162,514,264,337,593,543,950,336x more
  a single IPv6 /64 subnet holds 18,446,744,073,709,551,616 addresses
    -- 4,294,967,296x the entire IPv4 internet
```

A **single /64 subnet** holds four billion times the whole IPv4 address space. That is the scale of the change.

### Notation, verified

```
  2001:0db8:0000:0000:0000:ff00:0042:8329  -> 2001:db8::ff00:42:8329
  0000:0000:0000:0000:0000:0000:0000:0001  -> ::1                      loopback
  fe80:0000:0000:0000:0204:61ff:fe9d:f156  -> fe80::204:61ff:fe9d:f156 link-local
  2001:db8:0:0:1:0:0:1                     -> 2001:db8::1:0:0:1
```

Two rules: drop leading zeros within each group, and replace **one** run of all-zero groups with `::`. Only one `::` is permitted — two would make the length ambiguous. The last line shows the tie-break: with two equal-length zero runs, the **leftmost** is compressed.

### IPv4 vs IPv6

| | IPv4 | IPv6 |
|---|---|---|
| Address size | 32 bits | 128 bits |
| Notation | Dotted decimal | Colon-separated hex, with `::` compression |
| Header | **20–60 bytes, variable** | **40 bytes, fixed** |
| Header checksum | Yes | **None** — layer 2 and layer 4 already check |
| Fragmentation | By routers **and** hosts | **Hosts only**; routers return Packet Too Big |
| Address configuration | DHCP or static | **SLAAC** (stateless autoconfiguration) or DHCPv6 |
| Broadcast | Yes | **None** — replaced by multicast |
| ARP | Yes | Replaced by **NDP** (Neighbor Discovery, over ICMPv6) |
| NAT | Ubiquitous | **Unnecessary** — restores end-to-end addressing |
| IPsec | Optional | Designed in (though in practice still optional) |
| Private addresses | RFC 1918 | **ULA**, `fc00::/7` |
| Loopback | `127.0.0.1` | `::1` |

Key address types: **`::1`** loopback; **`fe80::/10`** link-local (every interface has one, automatically); **`fc00::/7`** unique local; **`2000::/3`** global unicast; **`ff00::/8`** multicast. Note there is **no broadcast at all** — "all nodes on this link" is the multicast group `ff02::1`.

**Transition mechanisms** (Tier 3, one line each): **dual stack** — run both, which is what almost everyone does; **tunnelling** — carry IPv6 inside IPv4 packets (6to4, Teredo); **translation** — NAT64/DNS64 for IPv6-only clients reaching IPv4 servers.

**Why adoption is slow**, which is the follow-up question: NAT removed the urgency, every device and every piece of middleware has to support it, dual stack means running and debugging two networks, and there is no benefit visible to a user. It is a textbook coordination problem, not a technical one.

---

## Must remember

```
IPv4 HEADER (20-60 bytes)
 version | IHL (in 32-bit WORDS, so 5 = 20 bytes) | ToS | total length (hdr+data)
 identification | flags (res, DF, MF) | fragment offset (in 8-BYTE units)
 TTL | protocol (1 ICMP, 6 TCP, 17 UDP) | header checksum (HEADER ONLY, redone per hop)
 source IP | destination IP | options (rare)
 the checksum covers only the header because L2 (CRC) and L4 (checksum) cover data
 TTL: decremented per hop, 0 -> drop + ICMP Time Exceeded. THAT IS HOW TRACEROUTE WORKS.

MASK = a run of 1s then a run of 0s. Nothing else is a valid mask.
CIDR = carry the prefix length explicitly instead of inferring it from the first octet.

THE PROCEDURE (8 steps)
 1 prefix = count the 1 bits in the mask
 2 host bits = 32 - prefix
 3 network   = address AND mask
 4 wildcard  = NOT mask
 5 broadcast = network OR wildcard
 6 first host = network + 1      7 last host = broadcast - 1
 8 total = 2^hostbits, usable = total - 2
   (-2 because all-zeros = the network and all-ones = the broadcast)
   /31 = 2 addresses, RFC 3021 allows both on a point-to-point link.  /32 = one host route.

BLOCK SIZE is the whiteboard shortcut: block = 256 - (last nonzero mask octet) = 2^hostbits
 subnets start at MULTIPLES OF THE BLOCK SIZE
 /25 block 128 | /26 block 64 | /27 block 32 | /28 block 16 | /29 block 8 | /30 block 4
 usable: /24 254 | /25 126 | /26 62 | /27 30 | /28 14 | /29 6 | /30 2
 borrow s bits -> 2^s subnets, each 2^(32-prefix) - 2 hosts

VLSM: sort LARGEST FIRST, pick the smallest prefix that fits, allocate ALIGNED.
 alignment is forced: a network address must equal (address AND mask), so a block
 can only start at a multiple of its own size.
 largest-first does not waste FEWER addresses than smallest-first (verified: both 12)
 -- it leaves the slack CONTIGUOUS at the end, which is the real reason to do it.
 a router-to-router link gets a /30 (exactly 2 usable).

SUPERNETTING needs CONTIGUOUS blocks AND an ALIGNED combined block.
 4 x /24 from 172.16.0.0 -> /22.  But 10.1/16 + 10.2/16 + 10.3/16 -> /16 + /15,
 because a /14 would also cover 10.0/16. PARTIAL aggregation is normal.

CLASSFUL (dead, vocabulary survives)
 A 0xxx    1-126    /8   126 USABLE (0.0.0.0/8 and 127/8 are reserved)  16,777,214 hosts
 B 10xx  128-191   /16   16,384                                            65,534 hosts
 C 110x  192-223   /24   2,097,152                                            254 hosts
 D 1110 224-239 multicast     E 1111 240-255 reserved
 why it died: 300 hosts forced a class B, wasting 65,234 addresses; CIDR gives a /23
 and wastes 210 -- 311x better (computed)

SPECIAL ADDRESSES
 0.0.0.0          this host / bind-all / DHCP source before you have an address
 127.0.0.0/8      loopback
 169.254.0.0/16   APIPA link-local -> DHCP FAILED. It is a DIAGNOSTIC.
 10.0.0.0/8       private, 16,777,216 addresses
 172.16.0.0/12    private, runs to 172.31.255.255 (NOT 172.16.255.255)
 192.168.0.0/16   private, 65,536 addresses
 100.64.0.0/10    carrier-grade NAT
 224.0.0.0/4      multicast
 255.255.255.255  LIMITED broadcast -- never forwarded
 x.x.x.255        DIRECTED subnet broadcast -- now blocked by default (smurf attack)

NAT rewrites the source IP; PAT also rewrites the PORT, so one public address serves
 ~16k-64k concurrent translations (computed) -- which is why IPv4 exhaustion was survivable
 verified live: host 10.105.73.61 (private) appeared to a public server as a public address
 NAT BREAKS: inbound connections, peer-to-peer (hence STUN/TURN/ICE), end-to-end
 addressing, protocols carrying addresses in the payload (FTP PORT, SIP), IPsec AH, logging
 NAT is NOT a firewall -- blocking unsolicited inbound is a side effect, not a policy

DHCP DORA over UDP 67 (server) / 68 (client), because TCP needs an address first
 DISCOVER (broadcast, src 0.0.0.0) -> OFFER -> REQUEST (BROADCAST, so declined servers
 release their reservations) -> ACK. Also NAK, RELEASE, DECLINE, INFORM.
 across a router you need a RELAY AGENT (the broadcast would not be forwarded)

FRAGMENTATION  data per fragment = ((MTU - 20) // 8) * 8
 identification groups them; offset is in 8-BYTE units; MF set on all but the last
 REASSEMBLY ONLY AT THE FINAL DESTINATION (fragments may take different routes)
 ONE LOST FRAGMENT DESTROYS THE WHOLE PACKET
 every fragment carries a full 20-byte header
 IPv6 forbids router fragmentation: routers return ICMPv6 Packet Too Big
 PATH MTU DISCOVERY NEEDS ICMP TYPE 3 CODE 4 -- blocking ICMP creates black holes

ICMP (protocol 1, inside IP)
 0 echo reply | 8 echo request          -> ping
 3/0 net unreachable | 3/1 host unreachable | 3/3 port unreachable
 3/4 fragmentation needed, DF set       -> path MTU discovery
 11/0 time exceeded (TTL)               -> traceroute
 ping sends ICMP echo. tracert sends increasing TTL and reads type 11.
 unix traceroute uses UDP probes + type 3/3 for the last hop; windows uses ICMP throughout

IPv6: 2^128, a single /64 holds 4.3 billion times the whole IPv4 space
 FIXED 40-byte header, NO header checksum, NO broadcast (multicast only), NO router
 fragmentation, NDP instead of ARP, SLAAC instead of DHCP, NAT unnecessary
 ::1 loopback | fe80::/10 link-local | fc00::/7 ULA | 2000::/3 global | ff00::/8 multicast
 notation: drop leading zeros per group; ONE run of zero groups -> '::'; on a tie the
 LEFTMOST run is compressed
 slow adoption because NAT removed the urgency and dual stack means two networks to debug
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "IHL of 20 means a 20-byte header" | IHL counts **32-bit words**, so 20 bytes is IHL = 5. The field's maximum of 15 gives a 60-byte header |
| "The fragment offset is in bytes" | In **8-byte units**. Offset field 185 means byte 1480, which is why all but the last fragment must be a multiple of 8 |
| "The IP checksum protects the data" | **Header only.** The data is covered by Ethernet's CRC below and TCP's checksum above |
| "The IP checksum is computed once" | **Recomputed at every hop**, because the TTL changed. That is why it is a cheap sum, and why IPv6 removed it |
| "255.255.0.255 is a valid mask" | A mask is a contiguous run of ones. Verified: all four malformed masks were rejected |
| "A `/26` gives 64 usable hosts" | **62.** The all-zeros and all-ones host patterns are the network and broadcast addresses |
| "`192.168.1.100/26` is a network address" | `100 AND /26 = 64`, so the network is `192.168.1.64/26`. A block can only start at a multiple of its own size |
| "Splitting a /24 into four /26s keeps 254 usable addresses" | **248.** Each new subnet loses its own network and broadcast address |
| "The private range is `172.16.0.0` to `172.16.255.255`" | It is `172.16.0.0/12`, so it runs to **`172.31.255.255`** |
| "VLSM largest-first wastes fewer addresses" | Verified: both orders consumed 12 extra. The gain is that the slack is left **contiguous** at the end, usable later |
| "Any contiguous blocks can be aggregated" | They must also be **aligned**. Verified: `10.1/16 + 10.2/16 + 10.3/16` cannot become one route, because the enclosing `/14` would also cover `10.0/16` |
| "There are 128 class A networks" | 128 bit patterns, but `0.0.0.0/8` and `127.0.0.0/8` are reserved, so **126 usable** |
| "Classful addressing died because of the routing table size" | Primarily because of **waste**: the only sizes were 16M, 65K and 254, so a 300-host site had to take a class B and throw away 65,234 addresses — 311× worse than a `/23` |
| "`169.254.x.x` is a private address like 192.168" | It is **link-local**, self-assigned because **DHCP failed**. It is a fault diagnostic, not a usable plan |
| "`255.255.255.255` reaches the whole internet" | It is the **limited** broadcast and is never forwarded by any router |
| "NAT gives you security" | It incidentally blocks unsolicited inbound traffic as a side effect of having no translation entry. It does nothing about outbound connections, internal threats or the application layer |
| "NAT just changes the IP address" | **PAT** changes the port too, which is what lets one public address serve tens of thousands of connections |
| "NAT is transparent to applications" | It breaks inbound connections, peer-to-peer, IPsec AH, and any protocol that carries an address in its payload — FTP's `PORT`, SIP |
| "DHCP uses TCP" | **UDP** 67/68. TCP would need an address on both ends to set up a connection, and the client has none yet |
| "DHCP REQUEST is unicast to the chosen server" | **Broadcast**, so the servers whose offers were declined can release their reservations |
| "Fragments are reassembled at each router" | **Only at the final destination**, because different fragments may take different routes |
| "Losing a fragment loses that fragment" | It destroys the **whole packet** — there is no partial delivery and no per-fragment retransmission |
| "`ping` uses TCP" | ICMP Echo Request/Reply. No ports, no connection |
| "A host that doesn't reply to ping is down" | It may simply filter ICMP. Verified on this network: `ping 1.1.1.1` is 100% loss while TCP to port 443 works perfectly |
| "Blocking all ICMP is good security hygiene" | It breaks **path-MTU discovery** (type 3 code 4) and traceroute, producing black-hole connections where small packets work and large ones hang |
| "IPv6 is just a bigger address" | Also: a fixed 40-byte header, no checksum, no broadcast, no router fragmentation, NDP instead of ARP, SLAAC instead of DHCP, and no need for NAT |
| "You can use `::` twice to shorten an address further" | Only once. Two would make the number of elided groups ambiguous |

---

## Interview Q&A bank

**Q1. Walk me through the IPv4 header.**
Version and IHL, where IHL counts 32-bit words so the minimum 5 means 20 bytes. Type of service, then total length covering header plus data. Identification, flags and fragment offset handle fragmentation. TTL is decremented per hop for loop protection, protocol demultiplexes upward — 6 for TCP, 17 for UDP, 1 for ICMP — and the checksum covers only the header. Then the source and destination addresses.

**Q2. Why does the IP checksum cover only the header?**
Because the data is already protected below by the link layer's CRC and above by TCP's or UDP's checksum. IP checks only what it is responsible for, and the header checksum has to be recomputed at every hop since the TTL changes — so it is deliberately cheap. IPv6 removed it entirely on that reasoning.

**Q3. What is a subnet mask?**
A 32-bit value, a contiguous run of ones followed by zeros, that marks which bits of an address identify the network and which identify the host. The count of ones is the prefix length.

**Q4. Given `192.168.1.130/25`, find the network, broadcast, range and usable count.**
A `/25` has block size 128, so the networks are `.0` and `.128`, and `130` falls in the `.128` block. Network `192.168.1.128`, broadcast `192.168.1.255`, range `.129` to `.254`, and 126 usable addresses.

**Q5. Why is it `2^h − 2` and not `2^h`?**
The all-zeros host pattern is the network identifier and the all-ones pattern is the directed broadcast, so neither is assignable. The exceptions are a `/31`, where RFC 3021 lets both addresses be used on a point-to-point link, and a `/32`, which is a single host route.

**Q6. What is the block-size shortcut?**
Block size is `2^(host bits)`, equivalently `256` minus the interesting octet of the mask. Subnets start at multiples of it, so you find which multiple your address falls between and you have the network and broadcast immediately — which is how to do this by hand under pressure.

**Q7. What is VLSM, and what is the procedure?**
Using a different prefix length per subnet so each is sized for its requirement. Sort requirements largest-first, choose the smallest prefix whose usable count suffices, and allocate aligned blocks from the lowest free address.

**Q8. Why largest-first?**
Alignment forces every block to start at a multiple of its own size, so a small block placed early leaves padding that a large block cannot use. Interestingly the total consumption is the same either way — verified — but largest-first leaves the leftover space contiguous at the end, where a future subnet can use it.

**Q9. Design a plan for 100, 50, 25, 10 and 2 hosts out of `192.168.1.0/24`.**
`/25` for 100 at `.0`, `/26` for 50 at `.128`, `/27` for 25 at `.192`, `/28` for 10 at `.224`, and `/30` for the two-host link at `.240`, leaving 12 addresses free at the top.

**Q10. What is supernetting, and when does it fail?**
Merging contiguous blocks into one shorter prefix so a router advertises one route instead of many. It requires the blocks to be contiguous **and** the combined block to be aligned — verified, `10.1/16 + 10.2/16 + 10.3/16` only partially aggregates, because the enclosing `/14` would also cover `10.0/16`.

**Q11. Why did classful addressing fail?**
Because the only sizes available were `/8`, `/16` and `/24`: 16 million, 65 thousand, or 254 hosts. A site needing 300 hosts had to take a class B and waste 65,234 addresses, where CIDR gives it a `/23` and wastes 210 — about 311 times better.

**Q12. Name the private ranges.**
`10.0.0.0/8`, `172.16.0.0/12` — note that runs to `172.31.255.255` — and `192.168.0.0/16`.

**Q13. What does `169.254.x.x` mean?**
APIPA, a link-local address the OS self-assigns when **DHCP failed**. The host can reach others on the same wire that did the same thing, and nothing else. It is a diagnostic: look at the DHCP server or the cable.

**Q14. Limited vs directed broadcast?**
`255.255.255.255` is limited and is never forwarded by a router — it is what DHCP Discover uses before the client has an address. A directed broadcast like `10.0.1.255` targets a specific subnet and is now blocked by default, because it was a DDoS amplifier.

**Q15. What is NAT, and what is PAT?**
NAT rewrites the source address as a packet leaves a private network and reverses it on return. PAT also rewrites the source port, so many private hosts share one public address — which supports tens of thousands of concurrent connections per address and is why IPv4 exhaustion was survivable.

**Q16. What does NAT break?**
Inbound connections, since there is no translation entry until the inside host initiates; peer-to-peer, hence STUN, TURN and ICE; end-to-end addressing as a model; protocols embedding addresses in their payload like FTP's `PORT` and SIP; IPsec AH, which authenticates the header NAT modifies; and attribution in logs.

**Q17. Is NAT a security feature?**
Incidentally and partially. Unsolicited inbound traffic has nowhere to go, which stops naive scanning, but that is a side effect of translation rather than a policy. It does nothing about outbound connections, internal compromise, or anything at the application layer.

**Q18. Explain DHCP DORA.**
Discover, broadcast from `0.0.0.0` because the client has no address; Offer from one or more servers with an address, mask, gateway and DNS; Request, broadcast so that declined servers release their reservations; and Acknowledge confirming the lease. It runs over UDP 67 and 68, because TCP would need addresses on both ends first.

**Q19. How does DHCP work across a router?**
Through a relay agent, because the Discover broadcast is not forwarded. The relay unicasts it to a central server and records which subnet it came from, so the server allocates from the right pool.

**Q20. Explain fragmentation.**
A router forwarding a packet larger than the outgoing MTU splits it. Data per fragment is `((MTU − 20) / 8) × 8` because the offset field counts in 8-byte units. Identification groups the fragments, the offset says where each starts, and MF is set on all but the last. Reassembly happens only at the final destination.

**Q21. What's wrong with fragmentation?**
Losing one fragment destroys the entire packet, every fragment carries a full header, and reassembly costs state at the destination. So TCP sizes its segments to the path MTU instead, and IPv6 forbids router fragmentation altogether — routers return an ICMPv6 Packet Too Big and make the source handle it.

**Q22. What does `ping` send, and what does `traceroute` send?**
`ping` sends an ICMP Echo Request and expects an Echo Reply — no ports, no connection. `traceroute` sends probes with increasing TTL and reads the ICMP Time Exceeded that each router returns when the TTL hits zero. Windows uses ICMP probes; Unix traditionally uses UDP to high ports plus a Port Unreachable to detect the last hop.

**Q23. A host doesn't respond to ping. Is it down?**
Not necessarily — it may filter ICMP. Verified on this network: `ping 1.1.1.1` reports 100% loss while a TCP connection to port 443 succeeds immediately.

**Q24. Why is blocking all ICMP a bad idea?**
Because path-MTU discovery depends on ICMP type 3 code 4. Block it and large packets vanish silently while small ones work, which is a black-hole connection and one of the hardest failures to diagnose.

**Q25. Why IPv6, and what else changed besides the address size?**
Address exhaustion — a single `/64` holds four billion times the entire IPv4 space. Also a fixed 40-byte header, no header checksum, no broadcast at all, no router fragmentation, NDP replacing ARP, stateless autoconfiguration replacing DHCP, and no need for NAT, restoring end-to-end addressing.

**Q26. How do you write an IPv6 address?**
Eight groups of four hex digits, dropping leading zeros in each group, with one run of all-zero groups replaced by `::`. Only one `::` is allowed, because two would make the number of elided groups ambiguous; and on a tie between equal-length runs, the leftmost is compressed.

**Q27. Why is IPv6 adoption slow?**
NAT removed the urgency, every device and middlebox in the path has to support it, dual stack means operating two networks, and there is no user-visible benefit. It is a coordination problem rather than a technical one.

---

## Practice

1. `10.20.30.40` with mask `255.255.255.192`. Give the prefix, network, broadcast, range and usable count.
2. `172.20.100.200/22`. Same five answers. Which octet does the block size land in?
3. How many `/27` subnets fit in a `/22`? How many usable hosts in each? How many usable addresses in total, and how many were lost to subnetting?
4. You are given `10.50.0.0/16` and need subnets for 4000, 2000, 500, 60 and 2 hosts. Produce the VLSM plan with networks, masks and ranges.
5. Can `192.168.8.0/24`, `192.168.9.0/24`, `192.168.10.0/24` and `192.168.11.0/24` be aggregated? Show the binary reasoning.
6. Can `192.168.4.0/24` through `192.168.7.0/24` be aggregated? What about `192.168.5.0/24` through `192.168.8.0/24`?
7. A 5000-byte IP packet must cross a link with MTU 1500, then one with MTU 576. Give the fragments after each stage, with offsets and MF flags.
8. A host has IP `192.168.1.50/24` and gateway `192.168.1.1`. It sends to `192.168.1.200` and then to `172.217.16.1`. For each, state the destination IP and destination MAC in the frame, and whether ARP is needed and for what.
9. Your machine shows `169.254.10.5`. List three things you would check, in order.
10. Explain why a host behind PAT can browse the web but cannot host a game server, and give two ways to fix it.
11. A customer reports that small HTTP requests work but large file uploads hang forever. Give the most likely cause and the diagnostic that confirms it.
12. Compress `2001:0db8:0000:0000:af00:0000:0000:0001` and explain each decision you make.

**Answers to 3, 7 and 11:**

> **3.** A `/22` has 10 host bits; a `/27` has 5. So borrowing 5 bits gives **`2⁵ = 32` subnets** of `2⁵ − 2 = **30** usable hosts each, totalling **960** usable. The original `/22` had `2¹⁰ − 2 = 1022` usable, so subnetting **lost 62 addresses** — two per new subnet, times 31 extra subnets. That loss is the price of segmentation and is exactly what the question is testing.
>
> **7.** Payload is `5000 − 20 = 4980` bytes. Over MTU 1500: `((1500−20)//8)×8 = 1480` per fragment, giving fragments of 1480, 1480, 1480 and 540 bytes at offsets 0, 185, 370 and 555, with MF = 1,1,1,0. Then over MTU 576: `((576−20)//8)×8 = 552`. Each 1480-byte fragment splits into 552 + 552 + 376, and offsets are **absolute within the original packet**, so the first becomes offsets 0, 69, 138; the second 185, 254, 323; and so on. **MF stays 1 on every piece except the very last** — a fragment of a fragment that is not final must set MF even though it was the last piece of its parent. That is the detail the question exists to catch.
>
> **11.** Almost certainly **path-MTU discovery broken by an ICMP-blocking firewall**. Small requests fit in one segment and work; large uploads produce full-size segments that need fragmentation somewhere, the router returns ICMP type 3 code 4 "fragmentation needed", the firewall drops it, and the sender never learns to use smaller segments — so it retransmits forever. Confirm it by retrying with a reduced MSS or MTU: if `ping -f -l <size>` (Windows) or `ping -M do -s <size>` (Linux) succeeds below a threshold and fails above it while large TCP transfers hang, that is the signature.

---

## Exit checklist

```
[ ] I can draw the IPv4 header and name every field's purpose
[ ] I know IHL is in 32-bit WORDS and the fragment offset in 8-BYTE units
[ ] I know the checksum is header-only and recomputed every hop, and why
[ ] I can explain how TTL makes traceroute possible
[ ] I know a mask must be a contiguous run of ones
[ ] I can run the 8-step procedure on any address and mask in under 30 seconds
[ ] I know the block-size shortcut and the /24 table by heart
[ ] I can do the procedure when the prefix lands in the 2nd or 3rd octet
[ ] I can explain why usable = 2^h - 2, and the /31 and /32 exceptions
[ ] I can count subnets and hosts from borrowed bits, and the addresses lost
[ ] I can build a VLSM plan largest-first with correct alignment
[ ] I know WHY alignment is forced (network = address AND mask)
[ ] I know largest-first buys CONTIGUITY, not fewer wasted addresses
[ ] I can aggregate routes and say when aggregation is impossible
[ ] I know partial aggregation is the normal outcome
[ ] I can give the classful table, including 126 usable class A networks
[ ] I can state the waste argument that killed classful addressing, with numbers
[ ] I know all three private ranges, including that 172.16.0.0/12 reaches 172.31.x.x
[ ] I recognise 169.254.x.x as a DHCP FAILURE diagnostic
[ ] I can distinguish limited and directed broadcast and say why directed is blocked
[ ] I can explain NAT and PAT and why one address serves tens of thousands of flows
[ ] I can list six things NAT breaks
[ ] I can give the honest answer on whether NAT is security
[ ] I can walk through DORA and say why Discover and Request are both broadcast
[ ] I know DHCP is UDP 67/68 and why it cannot be TCP
[ ] I know what a DHCP relay agent is for
[ ] I can compute fragments for any payload and MTU, with offsets and MF
[ ] I know reassembly is destination-only and one lost fragment kills the packet
[ ] I know fragments of fragments keep MF set, and offsets stay absolute
[ ] I can name the ICMP types for ping, traceroute and path-MTU discovery
[ ] I can explain the black-hole failure caused by blocking ICMP
[ ] I can state the IPv6 address-space arithmetic and the /64 comparison
[ ] I can compress an IPv6 address and justify every step
[ ] I can give six differences between IPv4 and IPv6 beyond address length
[ ] I can explain why IPv6 adoption is slow
```

---

## Next

**Part 6: M4 — Routing.** How a packet actually gets across the internet. Forwarding versus routing; the routing table read from this machine with **longest-prefix match worked out**; static versus dynamic; **distance vector with a full convergence table**, **count-to-infinity** and the split-horizon and poison-reverse fixes; **link state and Dijkstra run step by step** — a direct reuse of DSA Part 14; the DV-versus-LS comparison; RIP, OSPF and **BGP, and why the internet needs a path-vector protocol**; interior versus exterior gateway protocols; and hierarchical routing.
