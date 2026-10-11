# Computer Networks Placement Handbook — Part 9
# Module 7: DNS

**Module 7 · 3 hours · Tier 1 · Requires: M3 (addresses), M5 (UDP vs TCP)**

---

## Why this module matters

Every connection in the world starts here. Before a browser can open a TCP connection it needs an IP address, and getting one is the first and most failure-prone step of M10's URL walkthrough.

It is also a reliably asked module, and the questions are specific:

- **How does DNS resolution work, end to end?**
- **Recursive vs iterative** — the distinction almost everyone blurs
- **Name the record types** and what each is for
- **Why does DNS use UDP, and when does it use TCP?**
- What is a TTL, and what does "DNS propagation" actually mean?

It is also the module where a candidate with operational experience shows it, because **DNS caching causes a distinctive class of bug** — the change that works for you and not for your colleague — and knowing why is a strong signal.

The organising principle:

> **DNS is a distributed, hierarchical, aggressively cached database, and almost everything surprising about it follows from the caching rather than the lookup. The hierarchy means no single server knows everything and no single server has to. The caching means an answer you receive may be seconds or hours old, and that a change you make is not *propagated* anywhere — it simply becomes visible as other people's caches expire.**

**How this module was verified.** Every record type below is a **live query made from this machine** using `dnspython`, with real values and real TTLs. The TTL countdown was observed over several seconds. UDP and TCP query sizes were measured. **One thing could not be verified** — iterative resolution from the root servers — because this network blocks it, and §7.4 reports exactly what the probe found rather than presenting a textbook trace as an observation.

---

## 7.1 Why names exist, and the shape of the solution

Addresses are for routers; names are for people. But a name service for the whole internet cannot be a single server or a single file, which is what the original `HOSTS.TXT` was until it collapsed under its own weight in the early 1980s.

Three design decisions solve it, and they are the module in miniature:

1. **Hierarchy** — delegate authority downward, so no server needs to know everything.
2. **Caching** — answers are reused, so the authoritative servers are not asked billions of times.
3. **Replication** — every level is served by several machines, usually by anycast.

```
                              . (root)
                                |
        +---------------+-------+-------+---------------+
        |               |               |               |
       com             org             net              in        <- TLDs
        |               |                               |
   +----+----+     +----+----+                     +----+----+
 google    amazon  wikipedia  ...                 ac        co    <- second level
   |                  |
  www, mail       www, en, ...                                    <- hosts/subdomains

  read a name RIGHT TO LEFT:  www.wikipedia.org.
                               |        |      |  |
                               host     zone  TLD root (the trailing dot)
```

The **trailing dot** is the root, and it is genuinely there — `wikipedia.org.` is the fully qualified name. Your resolver adds it for you.

Three terms to keep separate:

| Term | What it is |
|---|---|
| **Zone** | A portion of the tree that one administrator controls |
| **Authoritative server** | Holds the real data for a zone and answers from it |
| **Resolver** | Asks questions on a client's behalf. A **stub** resolver (your OS) asks someone else; a **recursive** resolver does the full lookup |

---

## 7.2 Record types, with live lookups

Every one of these is a real query made while writing this module:

```
  example.com  A   TTL 21s   (IPv4 address)
     172.66.147.243
     104.20.23.154

  example.com  AAAA   TTL 209s   (IPv6 address)
     2606:4700:10::6814:179a
     2606:4700:10::ac42:93f3

  www.github.com  CNAME   TTL 791s   (alias -> canonical name)
     github.com.

  google.com  MX   TTL 300s   (mail exchangers, with preference)
     10 smtp.google.com.

  google.com  NS   TTL 5826s   (authoritative name servers)
     ns1.google.com.   ns2.google.com.   ns3.google.com.   ns4.google.com.

  google.com  SOA   TTL 60s   (start of authority)
     ns1.google.com. dns-admin.google.com. 997031930 900 900 1800 60

  google.com  TXT   TTL 299s   (arbitrary text)
     "v=spf1 include:_spf.google.com ~all"
     "apple-domain-verification=30afIBcvSuDV2PLX"
     "MS=E4A68B9AB2BB9670BCE15412F62916164C0B20BB"

  google.com  CAA   TTL 43200s   (which CAs may issue certs for this name)
     0 issue "pki.goog"
```

| Record | Maps | Notes |
|---|---|---|
| **A** | name → IPv4 | The common case |
| **AAAA** | name → IPv6 | "Quad A", four times the 32 bits |
| **CNAME** | name → **another name** | Cannot coexist with other records at the same name, and **cannot be at the zone apex** |
| **MX** | domain → mail server, with a **preference** | Lower preference is tried first |
| **NS** | zone → authoritative servers | This is what delegation *is* |
| **SOA** | zone → its master record | Serial, refresh, retry, expire, minimum TTL |
| **TXT** | name → free text | SPF, DKIM, domain-ownership proofs |
| **PTR** | address → name | Reverse lookup, in `in-addr.arpa` |
| **SRV** | service → host **and port** | `_service._proto.name`. Used by SIP, XMPP, Kerberos |
| **CAA** | domain → permitted certificate authorities | Verified above: only `pki.goog` may issue for google.com |

### Three details in that output worth reading

**The TXT record shows what TXT is actually used for in practice** — an SPF policy, an Apple verification string and a Microsoft one. TXT became the internet's general-purpose "prove you control this domain" mechanism, which is why real domains accumulate several.

**The SOA's last field is the negative-caching TTL** — here `60`. That is how long a resolver may cache the *absence* of a record, and it is why a newly created record can appear missing for a while even though nothing is wrong.

**Look at the spread of TTLs: 21 s for an A record, 43,200 s for CAA, 5,826 s for NS.** TTL is a deliberate choice, and short TTLs mark names expected to **move**. An A record at 21 seconds belongs to something behind a load balancer or CDN; NS records change rarely and are cached for hours. **Reading TTLs tells you about the architecture behind a name**, which is a nice observation to be able to make.

### `CNAME` and its two restrictions

```
  www.github.com  CNAME  github.com.
```

A `CNAME` says "this name is an alias — go look up that one instead", so the resolver restarts with the new name. Two rules that get asked:

- **A `CNAME` cannot coexist with other record types at the same name.** If `www` is a `CNAME`, it cannot also have an `MX`. The alias replaces the name wholesale.
- **A `CNAME` cannot be at the zone apex** (`example.com` itself), because the apex *must* carry `SOA` and `NS` records, and rule one forbids coexistence. Which is why providers invented `ALIAS`/`ANAME`/flattened CNAMEs — non-standard records that resolve server-side to give apex-level aliasing.

A real chain, captured from a query with recursion disabled:

```
    www.wikipedia.org.  9410 IN CNAME  dyna.wikimedia.org.
    dyna.wikimedia.org.   69 IN A      103.102.166.224
```

Two records, **two very different TTLs** — 9,410 s for the alias and 69 s for the address. The alias is stable; the address behind it moves. The resolver follows the chain and caches each link on its own clock, so your answer can be a mix of a fresh address and a stale alias.

---

## 7.3 Reverse DNS

Address to name, and the mechanism is a neat trick:

```
  8.8.8.8          -> query name 8.8.8.8.in-addr.arpa.
     PTR dns.google.
  1.1.1.1          -> query name 1.1.1.1.in-addr.arpa.
     PTR one.one.one.one.
  140.82.121.4     -> query name 4.121.82.140.in-addr.arpa.
     PTR lb-140-82-121-4-fra.github.com.
```

**Why the octets are reversed:** DNS delegates from the right — `org` first, then `wikipedia`, then `www` — so the *least* specific part is rightmost. IP addresses are the opposite, with the most significant octet first. Reversing them makes the hierarchy line up, so `8.8.8.8` becomes `8.8.8.8.in-addr.arpa` and the `8.in-addr.arpa` zone can be delegated to whoever owns `8.0.0.0/8`. (IPv6 uses `ip6.arpa` with each **nibble** reversed, producing those famously long query names.)

Note the third result: `lb-140-82-121-4-fra.github.com` — a GitHub load balancer in Frankfurt, named in its own PTR record. **Reverse DNS often leaks infrastructure detail**, which is why it is useful for diagnosis and why some operators keep it deliberately bland.

Reverse DNS is not guaranteed to exist or to match. **Forward and reverse are separate zones with separate owners**, so a PTR that claims a name proves nothing unless you re-resolve that name forward and get the same address back — the **forward-confirmed reverse DNS** check that mail servers use.

---

## 7.4 Recursive and iterative resolution

This is the distinction that interviews probe, and it is about **who does the work**.

```
 ITERATIVE: the server REFERS you onward. You do the walking.

   resolver -> root       : "where is www.wikipedia.org?"
   root     -> resolver   : "don't know; ask the .org servers, here they are"
   resolver -> .org       : "where is www.wikipedia.org?"
   .org     -> resolver   : "don't know; ask wikipedia.org's servers, here they are"
   resolver -> wikipedia  : "where is www.wikipedia.org?"
   wikipedia-> resolver   : "it is 103.102.166.224"

 RECURSIVE: you ask ONE server and it returns the final answer.

   stub resolver -> recursive resolver : "where is www.wikipedia.org?"
   (the recursive resolver then does the ENTIRE iterative walk above)
   recursive resolver -> stub          : "it is 103.102.166.224"
```

| | Recursive | Iterative |
|---|---|---|
| The client asks | Once | Once per level |
| Work done by | The **server** | The **client** |
| Returns | The final answer | A **referral** |
| Caches | Yes, heavily | The client may |
| Who does this | Your OS → your ISP's resolver, or 8.8.8.8 | A recursive resolver → root, TLD, authoritative |
| Root servers do | — | **Only this.** They never recurse |

**The key fact that makes it click:** both happen in every lookup, at different places. Your machine makes a **recursive** request to its configured resolver; that resolver then performs an **iterative** walk down the tree. The root and TLD servers only ever answer iteratively — if they recursed for everyone, they would be doing the whole internet's work.

### Glue records

A referral names servers **by name** — "ask `ns1.wikimedia.org`". But resolving *that* name needs DNS, which needs a referral, which names another server… an infinite regress.

**Glue records** break it: the referral's additional section carries the **addresses** of the servers it names. The root servers' own addresses are the base case, shipped with every resolver as a **root hints** file — thirteen named servers, `a` through `m.root-servers.net`, each actually an anycast cluster of hundreds of machines.

### What I could not verify, and what the probe found

I intended to trace an iterative resolution from a real root server. On this network it is impossible, and the probe is worth showing because the result is itself instructive:

```
  UDP/53 -> a.root-servers.net   198.41.0.4       Timeout
  UDP/53 -> Google DNS           8.8.8.8          Timeout
  UDP/53 -> Cloudflare DNS       1.1.1.1          Timeout
  UDP/53 -> Quad9                9.9.9.9          Timeout
  UDP/53 -> local resolver       10.131.202.39    OK  34 ms, 1 answer section(s)
```

**All outbound DNS is blocked except to the network's own resolvers.** And asking the local resolver with the recursion-desired bit cleared does not produce a referral either — it just serves from its cache:

```
  RD=0 to the local resolver: 2 answer, 0 authority, 0 additional
    ANSWER: www.wikipedia.org. 9410 IN CNAME dyna.wikimedia.org.
    ANSWER: dyna.wikimedia.org. 69 IN A 103.102.166.224
```

So the iterative trace in this section is **documented, not observed**, and this module says so rather than dressing up a diagram as a capture. If you want to see it for yourself, the command is `dig +trace www.wikipedia.org` on an unrestricted network — and it is worth doing once, because watching the referrals arrive makes the hierarchy concrete in a way reading cannot.

**And the blocking itself is the lesson.** Forcing all DNS through the network's own resolvers is exactly how an operator implements content filtering, logging and visibility — and it is why **DNS over HTTPS** is contentious: it routes name resolution around precisely this control point. That is a real policy argument sitting in a timeout.

---

## 7.5 Caching, TTL and what "propagation" really means

### Verified: the TTL counting down

```
  first query  : 2012.66 ms   TTL reported 68s
  second query : 2013.51 ms   TTL reported 66s

  watching the TTL at the recursive resolver:
   t+1.2s  TTL now 62s
   t+2.4s  TTL now 59s
   t+3.6s  TTL now 56s
   t+4.8s  TTL now 53s
```

**The TTL decreases in real time**, because the cache decrements it. So the number you receive is not the record's configured TTL — it is **the seconds remaining before this cached copy expires**. Seeing 53 where the zone says 300 tells you your answer is 247 seconds old.

(The ~2 s for both queries is this network's resolver chain timing out on its first configured server before falling through to one that answers — not resolution time. Honest reading of one's own measurement matters: the *interesting* number here is the TTL, not the latency.)

### The four caches

A lookup may be answered at any of these, and the one that bites is usually not the one you are thinking of:

```
 1. BROWSER cache        (Chrome keeps its own, minutes; chrome://net-internals/#dns)
 2. OPERATING SYSTEM     (ipconfig /flushdns, systemd-resolved, nscd)
 3. ROUTER / local       (your home router often caches, badly and without honouring TTL)
 4. RECURSIVE RESOLVER   (your ISP or 8.8.8.8 -- the big one)
    then: AUTHORITATIVE SERVER
```

### "DNS propagation" is a misnomer, and saying so is a good answer

> **Nothing propagates.** When you change a record, the authoritative server changes **immediately**. What takes time is every cache holding the *old* answer expiring. So the delay is bounded by the TTL that was in force **when those caches last looked** — not by the new TTL, which they have not seen.

That has a practical consequence worth knowing: **lower the TTL *before* you migrate.** Drop it to 60 seconds a day ahead, so caches pick up the short TTL, then make the change and the world follows within a minute. Raise it again afterwards. Changing the TTL at the same time as the record achieves nothing, because the caches are still running the old long one.

And negative caching is the mirror image: **the SOA's minimum field bounds how long a resolver may cache an NXDOMAIN**, so a record you just created can be invisible for that long.

### `NXDOMAIN` versus "no answer"

Verified:

```
  definitely-not-a-real-name-9z8y7x.com    -> NXDOMAIN (correct)
  zzz.invalid                              -> NXDOMAIN (correct)
  no-such-host-zzz.example.com             -> NoAnswer
```

Two genuinely different outcomes:

- **`NXDOMAIN`** — the name does not exist at all.
- **`NOERROR` with an empty answer** — the name exists but has no record **of that type**. Asking for `AAAA` on an IPv4-only host gives this.

Confusing them hides bugs. An application that treats "no answer" as "host down" will fail on a perfectly healthy IPv4-only name when it happens to ask for `AAAA` first.

---

## 7.6 Why UDP, and when TCP

### Verified sizes

```
  a DNS query for google.com A is 28 bytes on the wire
  a query WITH EDNS0 advertising 4096: 39 bytes (the OPT pseudo-record adds 11)
```

**Why UDP is correct here** is pure arithmetic from M5: the whole exchange is a 28-byte question and a small answer. A TCP handshake would cost **one extra round trip before the question is even asked**, and a close afterwards — tripling the latency of something that a single datagram handles. DNS has no ordering requirement, no flow to control, and its own retry logic (ask the next server in the list), so TCP's guarantees buy nothing.

### When DNS does use TCP

| Case | Why |
|---|---|
| **A truncated response** | Original DNS caps a UDP reply at **512 bytes**. A larger answer sets the **`TC` flag** and the client **retries over TCP** |
| **Zone transfer (`AXFR`/`IXFR`)** | A whole zone, potentially megabytes, and it must be complete |
| **DNS over TLS / over HTTPS** | TLS requires TCP (DoQ over QUIC is the exception) |
| **Large DNSSEC answers** | Signatures are big, which is a large part of why EDNS0 was needed |

**EDNS0** is the modern fix for the 512-byte cap: the client advertises a larger UDP buffer — commonly 1232 or 4096 bytes — in an `OPT` pseudo-record, so big answers fit in UDP after all. Verified above: the `OPT` record costs 11 bytes.

(The 1232 figure is not arbitrary: it is chosen to stay under the smallest plausible path MTU after IPv6 headers, so the reply never needs **IP fragmentation** — which from M3 is unreliable and, for DNS specifically, a cache-poisoning vector.)

---

## 7.7 DNS as load balancing

### Verified

```
  google.com           TTL   275s  1 address: 142.250.206.14
  www.wikipedia.org    TTL   134s  1 address: 103.102.166.224
  amazon.com           TTL    34s  3 addresses: 98.82.161.185, 98.87.170.71, 98.87.170.74
```

**Round-robin DNS**: several A records for one name, handed out in rotation. The crudest possible load balancing, and its limits are the interview point:

- **No health checking.** A dead server stays in the answer until someone edits the zone. The TTL bounds how fast you can remove it, and clients that have already cached it will keep trying.
- **No weighting**, so a small server gets the same share as a large one.
- **Clients may not cooperate** — some pick the first address every time, some reorder, caches may not rotate.

Notice the **TTL of 34 s on `amazon.com`** against 275 s for `google.com`. A short TTL is the price of agility: you can withdraw an address quickly, at the cost of far more DNS traffic.

**GeoDNS and anycast** are the real mechanisms. GeoDNS returns a *different* answer depending on where the query came from, so a user in Mumbai gets a Mumbai edge. Anycast goes further: the same address is announced from many locations and **BGP** (M4) routes you to the nearest. Those two together are how a CDN puts a server near you — and from M0, shortening `d` is the only thing that reduces the RTT floor. M10 does the arithmetic.

---

## 7.8 DoH, DoT and DNSSEC (Tier 2/3)

Classic DNS is **plaintext and unauthenticated**, which creates two separate problems that get conflated:

| Problem | Fix | What it does |
|---|---|---|
| **Anyone on the path can read your queries** | **DoT** (port 853) or **DoH** (port 443) | **Encrypts** the query in transit |
| **Anyone on the path can forge a reply** | **DNSSEC** | **Signs** the records so a forgery is detectable |

**They solve different things and neither replaces the other.** DoH/DoT encrypt the channel between you and your resolver, and say nothing about whether the resolver told you the truth. DNSSEC authenticates the data all the way from the zone owner, and leaves it in plaintext. In principle you want both.

- **DoT** — DNS over TLS on port 853. Visibly DNS, so it can be blocked.
- **DoH** — DNS over HTTPS on port 443, indistinguishable from other web traffic. Hence the controversy: it routes around network-level filtering, which is a feature to a user on a hostile network and a problem to an administrator who needs visibility. The timeouts in §7.4 are exactly the control DoH bypasses.
- **DNSSEC** — a chain of signatures from the root down, using `RRSIG`, `DNSKEY` and `DS` records. Adoption is partial, the answers are large (hence EDNS0), and misconfiguration takes a domain **completely offline** rather than degrading, which has kept deployment cautious.

**Cache poisoning** is the attack DNSSEC addresses: an attacker races a forged reply to a resolver, and if it arrives first with a matching query ID, the resolver caches the lie and serves it to everyone until the TTL expires. The pre-DNSSEC mitigations were **query-ID randomisation** and **source-port randomisation** (the response to Kaminsky's 2008 attack), which make the race much harder to win but not impossible.

---

## Must remember

```
DNS = a distributed, hierarchical, HEAVILY CACHED database. Three design choices:
 HIERARCHY (no server knows everything), CACHING (authoritative servers are not
 asked billions of times), REPLICATION (anycast at every level).
 read a name RIGHT TO LEFT. The trailing dot IS the root and is really there.
 ZONE = an administrative portion | AUTHORITATIVE = holds the data
 STUB resolver (your OS) asks someone else | RECURSIVE resolver does the full walk

RECORD TYPES
 A     name -> IPv4            AAAA  name -> IPv6
 CNAME name -> ANOTHER NAME    MX    domain -> mail server + PREFERENCE (lower first)
 NS    zone -> authoritative servers (delegation IS the NS record)
 SOA   zone master record; its LAST field is the NEGATIVE-caching TTL
 TXT   free text: SPF, DKIM, domain-ownership proofs
 PTR   address -> name, in in-addr.arpa     SRV  service -> host AND PORT
 CAA   which CAs may issue certs (verified: only pki.goog for google.com)
CNAME's two rules: it CANNOT coexist with other types at the same name, and
 therefore CANNOT sit at the ZONE APEX (which must have SOA and NS).
 -> hence the non-standard ALIAS/ANAME records providers invented.
A CNAME CHAIN caches each link on its OWN clock (verified: 9410s alias, 69s address)
TTL SPREAD TELLS YOU THE ARCHITECTURE: a 21-34 s A record is behind a load balancer
 or CDN; NS and CAA records sit at hours because they do not move.

REVERSE DNS: octets REVERSED because DNS delegates right-to-left while IP is most
 significant first. 8.8.8.8 -> 8.8.8.8.in-addr.arpa. IPv6 uses ip6.arpa by NIBBLE.
 forward and reverse are SEPARATE zones with separate owners, so a PTR proves
 nothing alone -> FORWARD-CONFIRMED reverse DNS is the real check (mail servers).
 PTR records often LEAK infrastructure (verified: a GitHub load balancer in Frankfurt).

RECURSIVE vs ITERATIVE -- it is about WHO DOES THE WORK
 iterative: the server REFERS you onward; you walk root -> TLD -> authoritative
 recursive: you ask ONE server and it returns the FINAL answer
 BOTH HAPPEN IN EVERY LOOKUP: your OS makes a RECURSIVE request to its resolver,
 which then performs an ITERATIVE walk. Root and TLD servers answer ONLY
 iteratively -- recursing for everyone would mean doing the whole internet's work.
GLUE RECORDS break the regress: a referral names servers BY NAME, so the additional
 section carries their ADDRESSES. The base case is the ROOT HINTS file -- 13 named
 servers a-m.root-servers.net, each an anycast cluster.

CACHING
 FOUR caches: browser -> OS -> router -> recursive resolver -> authoritative
 the TTL YOU RECEIVE IS SECONDS REMAINING, not the configured value, because the
 cache DECREMENTS it (verified counting down 68 -> 66 -> 62 -> 59 -> 56 -> 53).
 "DNS PROPAGATION" IS A MISNOMER: nothing propagates. The authoritative server
 changes INSTANTLY; what takes time is other caches EXPIRING, bounded by the TTL
 THEY LAST SAW -- not the new one.
 -> SO LOWER THE TTL A DAY BEFORE A MIGRATION, not at the same time.
 NEGATIVE caching is bounded by the SOA minimum field, which is why a NEWLY
 CREATED record can appear missing for a while.
 NXDOMAIN (the name does not exist) != NOERROR with no answer (the name exists but
 has no record OF THAT TYPE -- e.g. asking AAAA of an IPv4-only host).

UDP vs TCP
 query is 28 BYTES (verified). A TCP handshake would add a full RTT before the
 question is even asked, tripling the latency of a single-datagram exchange.
 DNS needs no ordering, no flow control, and has its own retry (try the next server).
 TCP IS USED FOR: a TRUNCATED response (TC flag -> retry over TCP; the original UDP
 cap is 512 bytes), ZONE TRANSFERS (AXFR/IXFR), DoT/DoH, large DNSSEC answers.
 EDNS0 advertises a bigger UDP buffer in an OPT pseudo-record (+11 bytes, verified).
 1232 is the common value: it stays under the smallest plausible path MTU so the
 reply never needs IP FRAGMENTATION (unreliable, and a poisoning vector).

DNS AS LOAD BALANCING
 ROUND-ROBIN = several A records (verified: amazon.com returned 3 with a 34 s TTL).
 limits: NO HEALTH CHECKING (a dead server stays until the zone is edited and
 caches expire), no weighting, and clients may not rotate fairly.
 GEODNS returns a DIFFERENT answer per location; ANYCAST announces ONE address
 from many places and lets BGP route you to the nearest. Together they are how a
 CDN shortens d -- the only thing that lowers M0's RTT floor.

SECURITY -- two DIFFERENT problems, two different fixes, neither replaces the other
 reading your queries    -> DoT (853) / DoH (443): ENCRYPTS the channel
 forging a reply         -> DNSSEC: SIGNS the records (RRSIG, DNSKEY, DS)
 DoH is contentious because it bypasses network-level filtering and visibility --
 which is exactly the control that blocked this module's root-server probe.
 DNSSEC misconfiguration takes a domain OFFLINE rather than degrading it.
 CACHE POISONING: race a forged reply with a matching query ID. Pre-DNSSEC
 mitigations are query-ID and SOURCE-PORT randomisation (post-Kaminsky 2008).
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "DNS is a server that maps names to addresses" | A **distributed, hierarchical, heavily cached** database. No single server holds it, and most answers come from a cache rather than an authority |
| "Recursive and iterative are two alternative designs" | **Both happen in every lookup.** Your OS asks its resolver recursively; that resolver walks the tree iteratively |
| "Root servers resolve names for you" | They answer **iteratively only** — a referral to the TLD. Recursing for everyone would mean doing the whole internet's work |
| "There are 13 root servers" | 13 **named** servers, each an **anycast cluster** of hundreds of machines worldwide |
| "A referral is enough to continue" | It names servers **by name**, which would need resolving too. **Glue records** in the additional section carry their addresses |
| "The TTL I see is the record's TTL" | It is the **seconds remaining** on that cached copy. Verified counting down 68 → 53 |
| "DNS changes propagate across the internet" | **Nothing propagates.** The authority changes instantly; other caches expire, bounded by the TTL they last saw |
| "To speed up a migration, set a low TTL when you change the record" | Too late — caches are still running the **old** long TTL. Lower it a day **before** |
| "If a lookup returns nothing, the host doesn't exist" | `NXDOMAIN` means the name does not exist; an empty `NOERROR` means it exists without **that record type**, which is what an IPv4-only host returns for `AAAA` |
| "A CNAME can point anywhere, including the apex" | Not at the zone apex, because the apex must carry `SOA` and `NS`, and a `CNAME` cannot coexist with other types. Providers invented `ALIAS`/`ANAME` for this |
| "A CNAME chain shares one TTL" | Each link is cached on its **own** clock. Verified: a 9,410 s alias pointing at a 69 s address |
| "MX preference is a priority where higher wins" | **Lower is tried first** |
| "A PTR record proves who an address belongs to" | Forward and reverse are separate zones with separate owners. The real check is **forward-confirmed reverse DNS** |
| "DNS uses UDP because UDP is faster" | Because the exchange is **one 28-byte question and a small answer**. A handshake would add a round trip before the question was even asked, and DNS needs none of TCP's guarantees |
| "DNS never uses TCP" | Truncated responses, zone transfers, DoT/DoH and large DNSSEC answers all use it |
| "The 512-byte limit still applies" | **EDNS0** lets a client advertise a larger UDP buffer — typically 1232, chosen to avoid IP fragmentation |
| "Round-robin DNS is load balancing" | It is **distribution without health checking**: a dead server stays in the answer until the zone changes and every cache expires |
| "A CDN works by having more bandwidth" | By being **nearer**, via GeoDNS and anycast. Only shortening the distance lowers the RTT floor |
| "DNSSEC encrypts DNS" | It **signs** — the data stays plaintext. Encryption is DoT/DoH, and they solve a different problem |
| "DoH is strictly better than plain DNS" | It encrypts your queries from the network **and** removes the operator's ability to filter and see them. Which of those matters depends on whose network it is |

---

## Interview Q&A bank

**Q1. What is DNS?**
A distributed, hierarchical, heavily cached database mapping names to records. The hierarchy means no server needs to know everything; the caching means most answers come from a cache rather than an authority.

**Q2. Walk me through a DNS lookup end to end.**
The application asks the OS stub resolver, which checks the browser and OS caches and then makes a **recursive** request to the configured resolver. That resolver checks its own cache; on a miss it walks the tree **iteratively** — asking a root server, which refers it to the TLD servers, which refer it to the zone's authoritative servers, which give the answer. The resolver caches it for the TTL and returns it.

**Q3. Recursive vs iterative?**
Iterative means the server refers you onward and you do the walking; recursive means you ask once and get the final answer. Both occur in every lookup: your machine's request is recursive, and the resolver's walk is iterative. Root and TLD servers answer only iteratively.

**Q4. Why don't root servers answer recursively?**
Because they would be performing the entire internet's resolution. Referring onward keeps their work to one small response per query, which is what lets thirteen anycast clusters serve the whole world.

**Q5. What is a glue record and why is it needed?**
A referral names the next servers by name, and resolving those names would itself need DNS — an infinite regress. Glue records are the addresses of those servers, carried in the referral's additional section. The base case is the root hints file shipped with every resolver.

**Q6. Name the main record types.**
A and AAAA for IPv4 and IPv6 addresses; CNAME for an alias to another name; MX for mail servers with a preference; NS for delegation; SOA for the zone's master record; TXT for free text such as SPF and ownership proofs; PTR for reverse lookups; SRV for a service's host and port; and CAA for which certificate authorities may issue for the domain.

**Q7. What are the restrictions on CNAME?**
It cannot coexist with other record types at the same name, and therefore cannot sit at the zone apex, which must carry SOA and NS records. Providers offer non-standard ALIAS or ANAME records to give apex-level aliasing.

**Q8. What is a TTL, and is the value I see the configured one?**
It is how long an answer may be cached. The value you receive is the **remaining** time, because caches decrement it — verified counting down from 68 to 53 seconds over five seconds of observation. So a low number tells you your answer is old.

**Q9. What does "DNS propagation" mean?**
It is a misnomer — nothing propagates. The authoritative server changes immediately; what takes time is every cache holding the old answer expiring, bounded by the TTL those caches last saw.

**Q10. So how do you migrate a domain with minimal downtime?**
Lower the TTL well in advance — a day before, say to 60 seconds — so caches pick up the short TTL. Then make the change, which becomes visible within a minute, and raise the TTL again afterwards. Changing the TTL at the same time as the record does nothing.

**Q11. What is negative caching?**
Resolvers cache the *absence* of a record too, bounded by the SOA's minimum field. It is why a record you have just created can appear missing for a while even though the zone is correct.

**Q12. `NXDOMAIN` vs an empty answer?**
`NXDOMAIN` says the name does not exist at all. `NOERROR` with no answer says the name exists but has no record of the type you asked for — which is exactly what an IPv4-only host returns for an AAAA query, so conflating them causes real bugs.

**Q13. Why does DNS use UDP?**
Because the whole exchange is a 28-byte question and a small answer. A TCP handshake would cost a full round trip before the question was even asked, and DNS needs no ordering or flow control and has its own retry logic.

**Q14. When does DNS use TCP?**
When a response is truncated — the `TC` flag is set and the client retries over TCP; for zone transfers, which are large and must be complete; for DNS over TLS or HTTPS; and for large DNSSEC answers.

**Q15. What is the 512-byte limit and what replaced it?**
The original cap on a UDP DNS reply. EDNS0 lets a client advertise a larger buffer in an OPT pseudo-record — commonly 1232 bytes, chosen so the reply stays under the smallest plausible path MTU and never needs IP fragmentation.

**Q16. Why does reverse DNS reverse the octets?**
Because DNS delegates from the right while IP addresses are most-significant-first. Reversing them aligns the hierarchies, so the `8.in-addr.arpa` zone can be delegated to whoever holds `8.0.0.0/8`.

**Q17. Can I trust a PTR record?**
Not on its own — forward and reverse zones have separate owners. The real check is forward-confirmed reverse DNS: resolve the name the PTR claims and confirm it maps back to the same address. Mail servers do exactly this.

**Q18. How can DNS be used for load balancing, and what are the limits?**
Round-robin: several A records handed out in rotation. Verified on a real domain returning three addresses with a 34-second TTL. The limits are no health checking — a dead server stays in the answer until the zone is edited and every cache expires — no weighting, and clients that may not rotate fairly.

**Q19. How does a CDN actually get you to a nearby server?**
GeoDNS returns a different answer depending on where the query came from, and anycast announces one address from many locations so BGP routes you to the nearest. Both shorten the physical distance, which is the only thing that reduces the round-trip floor.

**Q20. What is DNS cache poisoning?**
An attacker races a forged reply to a resolver; if it arrives first with a matching query ID, the resolver caches and serves the lie until the TTL expires. Query-ID and source-port randomisation make the race much harder; DNSSEC makes the forgery detectable.

**Q21. DNSSEC vs DoH — don't they do the same thing?**
No, and this is the common confusion. DNSSEC **signs** records so forgery is detectable, leaving them in plaintext. DoH and DoT **encrypt** the channel between you and your resolver, saying nothing about whether the resolver was truthful. They address different threats and neither substitutes for the other.

**Q22. Why is DoH controversial?**
Because it hides DNS inside ordinary HTTPS traffic on port 443, which routes around network-level filtering and logging. That is protection to a user on a hostile network and a loss of visibility to an administrator — and it is exactly the control that blocked this module's attempt to query a root server directly.

**Q23. A colleague sees the new site and you still see the old one. What is happening?**
Your caches differ. One of the four layers — browser, OS, router or recursive resolver — still holds the old answer within its TTL. Flush locally, check with a different resolver, and compare the TTL you are getting against the zone's configured value to see how stale your copy is.

---

## Practice

1. For `www.shop.example.co.in.`, name each label's role and say which part is the zone, the TLD and the root.
2. A name returns `CNAME` → `lb.provider.net` with TTL 3600, and that returns `A` with TTL 30. You query twice, ten minutes apart. What is cached, what is re-fetched, and why?
3. Why can't `example.com` itself be a `CNAME`? What do providers offer instead, and why is it non-standard?
4. You change an A record whose TTL has been 86400 for a year. Estimate the worst case before every user sees the change, and give the correct migration procedure.
5. A newly created record returns `NXDOMAIN` for ten minutes. Explain the mechanism and name the field that controls it.
6. An application fails with "host not found" but only on IPv6-capable machines. Give the most likely cause.
7. A DNS answer is 900 bytes. Trace what happens with and without EDNS0.
8. Why is 1232 a common EDNS0 buffer size rather than 4096?
9. You get three A records for a service and one of the three servers is down. Describe the user experience, and explain why DNS cannot fix it.
10. Explain to a developer why their `dig` output disagrees with their browser.
11. A mail server rejects your mail citing reverse DNS. What exactly is it checking, and what do you have to configure?
12. Your network blocks UDP/53 to everything except its own resolvers. List three things that enables for the operator, and name the technology that defeats it.

**Answers to 2, 4 and 7:**

> **2.** The first query caches both links independently: the `CNAME` for 3600 s and the `A` for 30 s. Ten minutes later, the `CNAME` is **still valid** (600 < 3600) but the `A` has **long expired** (600 ≫ 30), so the resolver re-fetches only the address. That is the point of per-record TTLs — verified in §7.2, where a real chain had a 9,410 s alias in front of a 69 s address. The stable indirection is cached for hours while the thing it points at is refreshed constantly.
>
> **4.** Worst case is **a full 86,400 seconds — 24 hours** — because a cache that fetched the record one second before your change holds it for the whole TTL, and you cannot reach into it. The correct procedure: lower the TTL to 60 s and **wait a full 86,400 seconds** so that every cache has re-fetched and now holds the 60-second value; then make the change, which becomes visible everywhere within a minute; then raise the TTL again. The waiting step is the one people skip, and skipping it makes the whole exercise pointless.
>
> **7.** **Without EDNS0:** the server cannot fit 900 bytes in a 512-byte UDP reply, so it returns a truncated response with the `TC` flag set. The client discards it and **re-asks over TCP** — a handshake plus the query, so roughly three round trips instead of one. **With EDNS0:** the client advertised a 1232- or 4096-byte buffer in its `OPT` record, the 900-byte answer fits in a single UDP datagram, and the whole exchange is one round trip. That is why EDNS0 matters so much for DNSSEC, whose signatures routinely push answers past 512 bytes.

---

## Exit checklist

```
[ ] I can state the three design choices (hierarchy, caching, replication)
[ ] I can read a domain name right to left and name every part
[ ] I know the trailing dot is the root and is genuinely part of the name
[ ] I can distinguish zone, authoritative server, stub resolver, recursive resolver
[ ] I can name 10 record types and what each maps
[ ] I know MX preference is lowest-first
[ ] I know the SOA's last field is the negative-caching TTL
[ ] I know both CNAME restrictions and why the apex one follows from the other
[ ] I know each link of a CNAME chain is cached on its own clock
[ ] I can read a TTL spread and infer the architecture behind a name
[ ] I can explain why reverse DNS reverses the octets
[ ] I know forward-confirmed reverse DNS and why a PTR alone proves nothing
[ ] I can explain recursive vs iterative in terms of WHO DOES THE WORK
[ ] I know BOTH occur in every lookup, and where each one happens
[ ] I can say why root servers never recurse
[ ] I can explain glue records and the regress they break
[ ] I know the root hints file and that the 13 names are anycast clusters
[ ] I can name the four caches a lookup may be answered from
[ ] I know the TTL I receive is SECONDS REMAINING
[ ] I can explain why "DNS propagation" is a misnomer
[ ] I can give the correct TTL-lowering migration procedure, INCLUDING the wait
[ ] I can explain negative caching and the field that bounds it
[ ] I can distinguish NXDOMAIN from NOERROR-with-no-answer, with an example
[ ] I can justify UDP from the 28-byte query size and the handshake cost
[ ] I can list four cases where DNS uses TCP
[ ] I know the 512-byte cap, the TC flag, and what EDNS0 changed
[ ] I know why 1232 is the common EDNS0 size
[ ] I can explain round-robin DNS and its three limitations
[ ] I can explain GeoDNS and anycast, and connect them to the RTT floor
[ ] I can explain cache poisoning and the two pre-DNSSEC mitigations
[ ] I can state the DNSSEC-vs-DoH distinction: SIGNS vs ENCRYPTS
[ ] I can give both sides of the DoH controversy
```

---

## Next

**Part 10: M8 — HTTP and the Web.** The application protocol a backend engineer lives in, and now weighted like a core subject rather than a footnote. A **raw request and response captured byte for byte**; methods and the **safe/idempotent table**; the status codes that actually get asked, with real responses; **caching with a real 304** and the bytes it saves; cookies, sessions and tokens; **CORS with a real preflight** — and the demonstration that the server answered anyway; **HTTP/1.1 vs 2 vs 3** with the version negotiated live over ALPN, head-of-line blocking at both layers, and what QUIC changed; **keep-alive measured**; and WebSockets versus polling.
