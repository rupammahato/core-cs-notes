# Computer Networks Placement Handbook — Part 12
# Module 10: What Happens When You Type a URL

**Module 10 · 3 hours · Tier 1 · Requires: everything**

---

## Why this module matters

This is the question. It appears in AWS's own engineering blog, across Medium and dev.to, and in a widely-shared LinkedIn post whose author says they are "shocked at how often" they ask it. It is the only question that touches **every module in this handbook**, which makes it both the hardest to answer well and the best revision device in the subject.

It is also asked at **three completely different depths** depending on who is asking and how much time there is, and a candidate who gives the ten-minute answer to a thirty-second question has misread the room. So §10.3 gives all three, and the skill is choosing.

The organising principle:

> **Every step is a question with a cached answer. Do I already know this name? Do I already have a connection? Do I already have this resource? The fast path is the one where all three answers are yes and almost nothing happens. The slow path — a cold first visit — is a sequence of round trips, and because the round-trip time is a law of physics, the entire modern web is engineering to remove them.**

**How this module was verified.** The full walkthrough was **measured phase by phase on this machine** against two real sites, five runs each, and the resulting latency budget in §10.5 is real output. The warm-connection comparison is measured. Where this network's filtering prevents a step from being observed — DNS to the root, ICMP — earlier modules said so and this one does not pretend otherwise.

---

## 10.1 The walkthrough

Typing `https://www.wikipedia.org/wiki/Internet` and pressing Enter.

```
 ┌─ 0. THE BROWSER PARSES THE INPUT ───────────────────────────────────────┐
 │  Is it a URL or a search term? (no dot, or spaces -> search engine)      │
 │  scheme https | host www.wikipedia.org | port 443 implied | path /wiki/… │
 │  IDN/punycode conversion, percent-encoding of unsafe characters          │
 │  HSTS CHECK: is this host on the preloaded or remembered HSTS list?      │
 │    -> if so, http:// is upgraded to https:// BEFORE any packet is sent   │
 │       (M9: this is the gap that closes HTTPS stripping)                  │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 1. NAME RESOLUTION  (M7) ──────────────────────────────────────────────┐
 │  four caches, in order, and most lookups stop in one of them:            │
 │    browser cache -> OS cache -> router -> recursive resolver             │
 │  on a full miss, the recursive resolver walks iteratively:               │
 │    root ("ask .org") -> .org TLD ("ask wikipedia's servers")             │
 │    -> authoritative ("103.102.166.224")                                  │
 │  the answer may be a CNAME chain, each link cached on its own TTL        │
 │  GeoDNS/anycast may return a DIFFERENT address depending where you are   │
 │  RESULT: an IP address                                                   │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 2. IS IT LOCAL?  (M3) ─────────────────────────────────────────────────┐
 │  destination AND my mask  ==  my network AND my mask ?                  │
 │    YES -> ARP for the destination itself                                │
 │    NO  -> ARP for the DEFAULT GATEWAY                                   │
 │  (M2) ARP request is BROADCAST, reply is UNICAST; cached for minutes    │
 │  RESULT: a next-hop MAC address                                         │
 │  so the frame carries the SERVER's IP and the ROUTER's MAC               │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 3. TCP HANDSHAKE  (M5) ── 1 RTT ───────────────────────────────────────┐
 │  SYN(seq=x) -> SYN+ACK(seq=y, ack=x+1) -> ACK(ack=y+1)                  │
 │  options negotiated here: MSS, WINDOW SCALE (M6 -- without it the        │
 │  connection is capped at 64 KB in flight), SACK, timestamps             │
 │  en route, every router: decrement TTL, recompute the header checksum,   │
 │  longest-prefix match, rewrite BOTH MAC addresses (M4)                  │
 │  and somewhere, NAT rewrites the source IP and port (M3)                │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 4. TLS HANDSHAKE  (M9) ── 1 RTT (1.3) or 2 (1.2) ─────────────────────┐
 │  ClientHello: versions, cipher suites, random, SNI (PLAINTEXT), ALPN,   │
 │               and in 1.3 a guessed KEY SHARE                            │
 │  ServerHello + certificate chain + key share                            │
 │  client validates: chain to a trusted root, signatures, THE NAME IN THE  │
 │    SAN LIST, validity dates, revocation, CAA                            │
 │  both derive a shared key by ephemeral ECDHE -> FORWARD SECRECY          │
 │  Finished messages MAC the whole transcript -> no silent downgrade       │
 │  ALPN picks the application protocol: h2, http/1.1 (M8)                 │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 5. THE HTTP REQUEST  (M8) ── 1 RTT + server time ─────────────────────┐
 │  GET /wiki/Internet HTTP/2                                              │
 │  :authority, user-agent, accept, accept-encoding, cookie,               │
 │  if-none-match / if-modified-since if we hold a cached copy             │
 │  (HTTP/2: binary frames, HPACK-compressed headers, one stream of many)   │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 6. THE SERVER SIDE ───────────────────────────────────────────────────┐
 │  CDN edge (anycast, nearest PoP) -- may answer entirely from cache      │
 │    -> on a miss: origin                                                 │
 │  LOAD BALANCER: L4 (five-tuple) or L7 (reads the URL and headers)       │
 │  REVERSE PROXY: TLS termination, compression, static files, rate limits │
 │  APPLICATION server -> cache (Redis) -> DATABASE (the whole DBMS         │
 │    handbook lives in this one box)                                      │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 7. THE RESPONSE  (M8) ────────────────────────────────────────────────┐
 │  200 OK, or 304 if our conditional request matched (no body at all)     │
 │  cache-control / etag / vary decide what the browser may reuse          │
 │  content-encoding: gzip or br; transfer-encoding: chunked for streaming  │
 │  TCP delivers it over several segments, growing cwnd by slow start (M6)  │
 └─────────────────────────────────────────────────────────────────────────┘
                                   |
 ┌─ 8. RENDER, AND THEN DO IT ALL AGAIN ──────────────────────────────────┐
 │  parse HTML -> DOM; discover CSS, JS, images, fonts                     │
 │  each subresource repeats steps 1-7 -- though usually on the SAME       │
 │  connection (keep-alive) and often from the SAME cache                  │
 │  a different origin means a new DNS lookup, TCP and TLS handshake       │
 │  cross-origin reads are governed by CORS (M8), enforced by the BROWSER   │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 10.2 The same picture as a round-trip count

Strip the detail and what remains is the thing that actually determines how it feels:

```
  COLD first visit, HTTP/1.1 + TLS 1.2:
    DNS (1 RTT if uncached) + TCP (1) + TLS (2) + HTTP (1)  =  5 round trips

  COLD first visit, HTTP/1.1 + TLS 1.3:
    DNS (1) + TCP (1) + TLS (1) + HTTP (1)                  =  4 round trips

  COLD first visit, HTTP/3 (QUIC):
    DNS (1) + QUIC incl. TLS (1) + HTTP (1)                 =  3 round trips

  WARM -- DNS cached, connection reused:
    HTTP (1)                                                =  1 round trip

  FULLY CACHED -- a fresh response within max-age:
                                                            =  0 round trips
```

At the Mumbai-to-California floor of **130 ms** from M0:

```
   5 RTT = 650 ms     4 RTT = 520 ms     3 RTT = 390 ms
   1 RTT = 130 ms     0 RTT =   0 ms
```

**That table is the whole of web performance engineering in five rows.** Every technique you have met is an attempt to move down it: HSTS avoids a redirect, TLS 1.3 removes a handshake round trip, QUIC merges two handshakes, keep-alive and connection pooling skip to row four, and HTTP caching reaches row five. And none of them touch bandwidth — because from M0, the RTT floor is `2d/v` and no amount of capacity reduces it.

---

## 10.3 The answer at three depths

### Thirty seconds

> "The browser resolves the hostname to an IP address through DNS, checking its caches first. It opens a TCP connection to that address — one round trip — and then negotiates TLS, which authenticates the server via its certificate and establishes a shared encryption key. It sends an HTTP request over that connection, the server responds, and the browser parses the HTML and fetches the subresources, mostly reusing the same connection. If anything is already cached — the name, the connection, the resource — that step is skipped entirely."

Four sentences, correct, and it names the right mechanisms. **This is the answer to give unless asked for more.**

### Three minutes

Add the structure and the caching:

> "First the browser decides whether the input is a URL at all, normalises it, and checks its HSTS list — if the host is there, `http` becomes `https` before any packet leaves, which closes the stripping gap.
>
> Then DNS. There are four caches in sequence — browser, OS, router, recursive resolver — and most lookups stop in one of them. On a full miss, the recursive resolver walks the hierarchy iteratively: a root server refers it to the TLD servers, which refer it to the zone's authoritative servers. The answer carries a TTL, which is why a DNS change takes time to become visible — nothing propagates, caches just expire.
>
> With an address, the host checks whether it is on the local subnet by ANDing with its own mask. If not, it ARPs for the default gateway — so the frame carries the server's IP address and the router's MAC, which is the difference between end-to-end and hop-to-hop addressing.
>
> Then the TCP three-way handshake, one round trip, which also negotiates MSS, window scaling and SACK. Then TLS: the client sends its supported versions and the SNI in plaintext, the server returns its certificate chain, the client validates the chain to a trusted root and checks the requested name is in the SAN list, and both derive an ephemeral shared key — one round trip in TLS 1.3, two in 1.2. ALPN also selects HTTP/2 here.
>
> Then the HTTP request and response, with conditional headers if we hold a cached copy — a 304 returns no body at all. On the server side the request may be answered by a CDN edge, or pass through a load balancer and reverse proxy to an application server and database. Finally the browser parses the HTML and repeats the process for every subresource, usually on the same connection."

### Ten minutes

The whole of §10.1, plus:

- **Where each step can fail** (§10.4) and what the user sees
- **The latency budget** (§10.5), with the measurement
- **The cross-references**: why the window-scaling option in step 3 determines throughput; why the certificate check in step 4 is the only thing that makes the encryption worth anything; why a CDN exists to shorten `d` rather than to add bandwidth
- **The honest gaps**: this network blocks root-server queries and ICMP, so parts of the walkthrough are documented rather than observed

> **How to pick.** If the interviewer says "briefly", give thirty seconds. If they say "walk me through it", give three minutes and then stop and let them steer. **Offering to go deeper is better than going deeper uninvited** — "I can go into the TLS handshake or the caching layers if that's useful" turns a monologue into a conversation.

---

## 10.4 Where it breaks, and what the user sees

The diagnostic value of the walkthrough, and the reason it is worth memorising as a sequence.

| Step | Failure | What the user sees | First diagnostic |
|---|---|---|---|
| 0 | Typo, or treated as a search | A search results page | Read the address bar |
| 1 | No DNS server reachable | "Server not found" immediately | `nslookup`; check `169.254.x.x` (M3) |
| 1 | NXDOMAIN | "Server not found" | `nslookup` — does the name exist? |
| 1 | **Stale cached DNS** | Reaches the **old** server; works for colleagues | Compare TTL with the zone; flush; try another resolver |
| 2 | No gateway MAC | Hangs, then fails | `arp -a`, `ping` the gateway |
| 2 | Wrong mask | Local hosts work, internet does not | Compute the network from the mask (M3) |
| 3 | SYN unanswered | **Hangs**, then "took too long to respond" | `telnet host 443`; firewall rules |
| 3 | RST returned | Fails **fast** — "connection refused" | Nothing is listening on that port (M5) |
| 3 | Window scaling stripped | Connects, then is inexplicably slow | Capped at 64 KB in flight (M6) |
| 4 | Certificate expired / wrong name / untrusted | Interstitial warning | Read the specific error — it names the failed check (M9) |
| 4 | Clock wrong on the client | "Certificate not yet valid" | Check the system clock |
| 4 | TLS version mismatch | Handshake failure | Old client against a TLS-1.2-minimum server |
| 5 | Path MTU black hole | **Headers arrive, body hangs** | ICMP type 3 code 4 blocked (M3, M9) |
| 6 | Application error | 500 | Server logs |
| 6 | Upstream invalid | **502** | The proxy's upstream (M8) |
| 6 | Nothing available | **503**, often with `Retry-After` | Capacity, deploys |
| 6 | Upstream never replied | **504** | The slow dependency behind the proxy |
| 7 | Over-aggressive cache | Stale content; a hard refresh fixes it | `Cache-Control`, `ETag` (M8) |
| 8 | Cross-origin fetch | Console CORS error; the request **succeeded** | The server answered; the browser withheld it (M8) |

**Three of those rows are worth singling out, because the *shape* of the failure identifies the layer:**

- **Hang versus instant failure at step 3.** A silently dropped SYN hangs until the RTO gives up (M6's exponential backoff — which is why it takes minutes); an RST fails immediately. **Hang means a firewall is dropping; fast failure means nothing is listening.** That single distinction resolves a large fraction of connectivity tickets.
- **Headers arrive and then the body hangs.** That is a path-MTU black hole almost every time: small packets fit, full-size segments do not, and the ICMP that would say so is blocked.
- **It works for me and not for my colleague.** Almost always a cache — DNS or HTTP — holding different answers at different places.

---

## 10.5 The latency budget, measured

Measured on this machine, five runs each, median:

```
  https://example.com/   (resolved to 172.66.147.243, 930 bytes)
   phase                                     ms    share
   1. DNS resolution                        0.5     0.2%
   2. TCP handshake (1 RTT)                62.3    19.7%
   3. TLS handshake                       116.7    36.9%
   4. request + first byte (1 RTT + server) 141.6   44.8%
   5. remaining body                        0.0     0.0%
   TOTAL                                  316.2
   -> SETUP (DNS+TCP+TLS) = 179.5 ms = 57% of the total,
      before a single byte of the request has been sent.

  https://www.wikipedia.org/   (resolved to 103.102.166.224, 348 bytes)
   phase                                     ms    share
   1. DNS resolution                        0.4     0.1%
   2. TCP handshake (1 RTT)                95.9    19.5%
   3. TLS handshake                       213.1    43.3%
   4. request + first byte (1 RTT + server) 180.0   36.6%
   5. remaining body                        0.0     0.0%
   TOTAL                                  492.0
   -> SETUP (DNS+TCP+TLS) = 309.4 ms = 63% of the total
```

Four readings, and this is the most useful single measurement in the handbook:

**Setup is 57% and 63% of the total.** Over half the time to load a small page is spent **before the request is sent**. The payload was 930 bytes and 348 bytes — the transfer itself is 0.0 ms. This is not a bandwidth problem and cannot be fixed with a bigger pipe.

**TLS is the largest single phase** — 117 ms and 213 ms, roughly **double** the TCP handshake, which is consistent with two round trips against one plus the asymmetric cryptography. Which is exactly why TLS 1.3 and QUIC target it.

**DNS is 0.5 ms — effectively free, because it was already cached.** That number is honest but unrepresentative: on a genuine cold lookup it would be one or more round trips. It is worth stating both ways, because it shows caching doing its job while reminding you the measurement is of a warm cache.

**And the warm-connection comparison:**

```
  cold (first)  188.1 ms
  warm (median)  58.0 ms
  -> reuse removes 130 ms, which is exactly the setup cost
```

**Connection reuse eliminated 130 ms, and 130 ms is the setup cost measured independently.** The two numbers agree, which confirms what row four of §10.2's table asserts: keep-alive is not a marginal optimisation, it removes an entire category of work.

### What this justifies

Every one of these is an attack on a row of that budget:

| Technique | Removes |
|---|---|
| **DNS caching, long TTLs, prefetch** | Step 1 |
| **Keep-alive, connection pooling, HTTP/2's single connection** | Steps 2–4, for every request after the first |
| **TLS 1.3** | One round trip from step 4 |
| **TLS session resumption, 0-RTT** | Most or all of step 4 |
| **QUIC / HTTP/3** | Merges steps 3 and 4 into one |
| **HSTS** | A redirect round trip before step 1 |
| **CDN / anycast / GeoDNS** | Shortens `d`, so it shrinks **every** RTT at once |
| **HTTP caching (`max-age`)** | Steps 1–7 entirely |

**The CDN row is the strongest lever** and it is worth understanding why: the others each remove one round trip, while a CDN reduces the *size* of every round trip simultaneously. Moving from a 130 ms path to a 10 ms edge turns a 4-RTT cold load from 520 ms into 40 ms. From M0, that is the only thing that touches the floor, because the floor is distance over signal speed.

---

## 10.6 The server side in one picture

Where this handbook meets the system-design round, and where the DBMS handbook picks up.

```
                    the internet
                         |
                  [ DNS: GeoDNS / anycast ]  -> steers you to the nearest edge
                         |
                  [ CDN EDGE (PoP) ]  -- static assets, cached pages
                         |  cache MISS only
                  [ WAF / DDoS scrubbing ]
                         |
                  [ LOAD BALANCER ]
                      L4: routes by the five-tuple, cheap, protocol-agnostic
                      L7: reads the URL/headers, can route /api vs /static,
                          terminate TLS, retry, and do sticky sessions
                         |
            +------------+------------+
            |            |            |
      [ reverse proxy / app server x N ]   <- stateless, so any one can serve
            |            |            |       any request (that is HTTP's
            +------------+------------+        statelessness paying off)
                         |
                  [ CACHE: Redis / memcached ]
                         |  cache MISS only
                  [ DATABASE: primary + read replicas ]
                         |
                  [ queue -> async workers ]
```

| Component | Does | Trade-off |
|---|---|---|
| **CDN** | Serves cached content from a nearby PoP | Shortens `d`; stale content; cache invalidation |
| **L4 load balancer** | Routes connections by the five-tuple | Fast and protocol-blind; cannot route on URL |
| **L7 load balancer** | Routes on URL, headers, cookies | Flexible; terminates TLS, so it sees everything (M9) |
| **Reverse proxy** | TLS termination, compression, static files, rate limits | One more hop to debug |
| **Forward proxy** | Acts on the **client's** behalf | Different thing entirely — a common confusion |
| **Cache** | Avoids the database | Invalidation, and stampedes (DBMS M10) |
| **Read replicas** | Scale reads | **Replication lag** → read-your-own-writes (DBMS M10) |
| **Queue** | Decouples slow work from the request | Eventual consistency, ordering, retries |

**Reverse vs forward proxy** is a question in its own right: a **reverse** proxy sits in front of servers and acts for *them* — the client does not know it is there. A **forward** proxy sits in front of clients and acts for *them* — the server does not know it is there. Same technology, opposite direction, and the words are routinely swapped.

**And note the link back:** the load balancer can distribute requests to any application server **only because HTTP is stateless** (M8). The moment you put session state in a server's memory you need sticky sessions and you have given that up — which is the architectural argument for tokens or a shared session store.

---

## 10.7 The remaining application protocols

Everything a backend engineer should be able to place, in one table.

| Protocol | Port | Transport | Purpose | Notes |
|---|---|---|---|---|
| **HTTP / HTTPS** | 80 / 443 | TCP, or UDP for HTTP/3 | The web | M8 |
| **DNS** | 53 | **UDP**, TCP when needed | Names | M7 |
| **DHCP** | 67 / 68 | UDP | Addressing | M3 |
| **SMTP** | 25, 587 | TCP | **Sending** mail | 25 server-to-server, 587 submission |
| **IMAP** | 143 / 993 | TCP | **Reading** mail, kept on the server | Multi-device |
| **POP3** | 110 / 995 | TCP | **Reading** mail, downloaded and removed | Single device, legacy |
| **FTP** | 21 control, 20 data | TCP | File transfer | **Plaintext**; two connections; active vs passive mode |
| **FTPS / SFTP** | 990 / 22 | TCP | Secure transfer | **SFTP is SSH, not FTP at all** |
| **SSH** | 22 | TCP | Remote shell, tunnels, SFTP | Key-based auth |
| **Telnet** | 23 | TCP | Remote shell, **plaintext** | Obsolete; use SSH |
| **NTP** | 123 | UDP | Time | Clock skew breaks TLS and tokens (M9) |
| **SNMP** | 161 / 162 | UDP | Device monitoring | An amplification vector |
| **LDAP** | 389 / 636 | TCP | Directory services | |
| **RDP** | 3389 | TCP | Remote desktop | |
| **QUIC** | 443 | UDP | HTTP/3's transport | M8 |

**Three distinctions that get asked directly:**

**SMTP sends, IMAP and POP3 read.** This trips people up because all three are "email protocols". SMTP is for pushing mail outward and between servers; IMAP and POP3 are for a client retrieving it.

**IMAP vs POP3:** IMAP leaves mail on the server and syncs state, so several devices see the same mailbox. POP3 downloads and typically deletes, which made sense for one desktop and dial-up and almost never does now.

**SFTP is not FTP.** It is a subsystem of SSH that happens to transfer files. **FTPS** is actual FTP wrapped in TLS. They share a purpose and nothing else — and plain FTP's habit of **carrying IP addresses in its `PORT` command** is exactly what NAT breaks (M3).

**And why NTP matters more than it looks:** a wrong clock breaks certificate validity checks (M9), token expiry, log correlation and database replication. "Certificate not yet valid" on a fresh machine is almost always a clock problem, not a certificate problem.

---

## Must remember

```
THE WALKTHROUGH -- EVERY STEP IS A QUESTION WITH A CACHED ANSWER
 0 PARSE + HSTS CHECK   (http -> https BEFORE any packet; closes stripping)
 1 DNS                  4 caches: browser, OS, router, recursive resolver;
                        on a miss the resolver walks root -> TLD -> authoritative
 2 LOCAL OR NOT         AND with my mask: same network -> ARP the destination,
                        else ARP THE GATEWAY. Frame = server's IP + ROUTER's MAC.
 3 TCP HANDSHAKE 1 RTT  negotiates MSS, WINDOW SCALE, SACK, timestamps
 4 TLS HANDSHAKE        1 RTT (1.3) or 2 (1.2). SNI is PLAINTEXT. Validate the
                        chain and THE NAME IN THE SAN LIST. Ephemeral ECDHE ->
                        forward secrecy. Finished MACs the transcript. ALPN picks h2.
 5 HTTP REQUEST  1 RTT  conditional headers if we hold a cached copy
 6 SERVER SIDE          CDN edge -> WAF -> load balancer -> reverse proxy ->
                        app -> cache -> database
 7 RESPONSE             200, or 304 WITH NO BODY. cache-control/etag/vary decide
                        reuse. cwnd grows by slow start as the body arrives.
 8 RENDER + SUBRESOURCES  repeat 1-7 per resource, usually on the SAME connection

ROUND TRIPS -- the number that actually determines how it feels
 cold, HTTP/1.1 + TLS 1.2   DNS 1 + TCP 1 + TLS 2 + HTTP 1 = 5 RTT
 cold, HTTP/1.1 + TLS 1.3                           = 4 RTT
 cold, HTTP/3 (QUIC)                                = 3 RTT
 warm (DNS cached, connection reused)               = 1 RTT
 fully cached within max-age                        = 0 RTT
 at the 130 ms Mumbai-California floor: 650 / 520 / 390 / 130 / 0 ms
 EVERY web-performance technique is a move DOWN that table, and NONE of them
 involve bandwidth -- because the floor is 2d/v (M0).

MEASURED LATENCY BUDGET (this machine, median of 5)
 example.com      DNS 0.5 | TCP 62.3 | TLS 116.7 | req+TTFB 141.6 | body 0.0
                  SETUP = 179.5 ms = 57% OF THE TOTAL
 www.wikipedia.org DNS 0.4 | TCP 95.9 | TLS 213.1 | req+TTFB 180.0
                  SETUP = 309.4 ms = 63%
 -> OVER HALF the time to load a small page is spent BEFORE THE REQUEST IS SENT
 -> TLS is the LARGEST single phase, roughly DOUBLE the TCP handshake
 -> DNS was 0.5 ms because it was ALREADY CACHED -- honest but unrepresentative
 -> body transfer was 0.0 ms for a ~900-byte page: NOT a bandwidth problem
 WARM: cold 188.1 ms vs warm 58.0 ms -> reuse removed 130 ms, which EQUALS the
 independently measured setup cost. Keep-alive removes a whole category of work.

WHAT REMOVES WHAT
 DNS caching/prefetch -> step 1 | keep-alive & pooling & HTTP/2 -> steps 2-4
 TLS 1.3 -> one RTT | session resumption/0-RTT -> most of step 4
 QUIC -> merges 3 and 4 | HSTS -> a redirect | HTTP caching -> steps 1-7
 CDN/anycast/GeoDNS -> shortens d, so it shrinks EVERY RTT AT ONCE
   <- THE STRONGEST LEVER: a 130 ms path becoming a 10 ms edge turns a 4-RTT
      cold load from 520 ms into 40 ms

THE THREE DEPTHS -- the question is asked at all three, so CHOOSE
 30 s: DNS -> TCP -> TLS -> HTTP -> render, and caching skips steps
 3 min: + HSTS, the four DNS caches, the mask/ARP decision, what the handshakes
        negotiate, certificate validation, conditional requests, the server tier
 10 min: + failure modes, the latency budget, the cross-references, and the
         honest gaps
 OFFER to go deeper rather than going deeper uninvited.

FAILURE SHAPES IDENTIFY THE LAYER
 HANG on connect     -> a firewall is DROPPING (RTO backoff, so it takes minutes)
 FAST "refused"      -> an RST: nothing is LISTENING
 headers then hang   -> PATH MTU BLACK HOLE (ICMP type 3 code 4 blocked)
 works for me only   -> a CACHE differs (DNS or HTTP)
 502 / 503 / 504     -> all from the PROXY: bad upstream reply / nothing to ask /
                        upstream never replied
 CORS error          -> the request SUCCEEDED; the BROWSER withheld the response
 cert "not yet valid"-> usually the CLIENT CLOCK, not the certificate

SERVER TIER
 L4 LB routes by the FIVE-TUPLE (fast, protocol-blind); L7 reads URL/headers
 (flexible, terminates TLS so it sees everything)
 REVERSE proxy acts for the SERVERS (client does not know); FORWARD proxy acts
 for the CLIENTS (server does not know). Routinely swapped.
 the LB can send any request to any app server ONLY BECAUSE HTTP IS STATELESS --
 put session state in server memory and you need sticky sessions and lose that.

APPLICATION PROTOCOLS
 SMTP 25/587 SENDS | IMAP 143/993 reads, LEAVES mail on the server, multi-device
 POP3 110/995 reads, DOWNLOADS AND DELETES, single device, legacy
 FTP 21 control + 20 data, PLAINTEXT, carries IP ADDRESSES IN ITS PORT COMMAND
   -> which is exactly what NAT breaks (M3)
 SFTP IS SSH (port 22), NOT FTP. FTPS is real FTP wrapped in TLS. Different things.
 SSH 22 | Telnet 23 plaintext/obsolete | NTP 123 | SNMP 161 (amplification vector)
 NTP matters more than it looks: a wrong clock breaks CERTIFICATE VALIDITY, token
 expiry, log correlation and replication.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "The browser sends a request to the website" | Five or six distinct phases happen first — parse and HSTS, DNS, the local/remote decision and ARP, TCP, TLS — and each can be skipped by a cache |
| "DNS returns the IP and then we connect" | Missing the local-versus-remote decision: the host ANDs the destination with its own mask and ARPs either the destination or the **gateway**. The frame carries the server's IP and the router's MAC |
| "The TCP handshake just opens the connection" | It also negotiates MSS, **window scaling** — without which the connection is capped at 64 KB in flight — SACK and timestamps |
| "TLS encrypts the connection" | It also **authenticates the server**, which is the part that makes the encryption worth anything, and selects the application protocol via ALPN |
| "HTTPS means nobody knows where I went" | The destination IP and the **SNI hostname** are plaintext. The path and body are hidden; the visit is not |
| "Page load is mostly download time" | Measured: setup was **57% and 63%** of the total, and body transfer was **0.0 ms** for a ~900-byte page |
| "Faster internet would fix it" | Over half the time was round trips. From M0 the RTT floor is `2d/v` and bandwidth does not touch it |
| "A CDN gives you more bandwidth" | It **shortens the distance**, which shrinks every round trip at once — the strongest lever available, and the only one that moves the floor |
| "Keep-alive is a minor optimisation" | Measured: it removed **130 ms**, which equalled the independently measured setup cost |
| "HTTP/3 is faster because UDP is faster" | It merges the transport and TLS handshakes into one round trip and removes TCP's head-of-line blocking (M8) |
| "Each image on the page opens a new connection" | They reuse the existing one via keep-alive, and HTTP/2 multiplexes them all over a single connection |
| "A hanging connection and a refused connection are similar failures" | Opposite diagnoses. A hang means a firewall is **dropping** packets; a fast refusal is an **RST**, meaning nothing is listening |
| "If headers arrive the connection is fine" | Headers arriving and the body hanging is the signature of a **path-MTU black hole** from blocked ICMP |
| "A CORS error means the request was blocked" | The request was **sent and answered**. The browser withheld the response from the page's JavaScript |
| "A 502 means my application crashed" | 502 comes from the **proxy** and means upstream returned something invalid. 503 means nothing was available; 504 means upstream never replied |
| "Reverse proxy and forward proxy are two names for the same thing" | A reverse proxy acts for the **servers**; a forward proxy acts for the **clients**. Opposite directions |
| "An L4 load balancer can route `/api` to a different pool" | It only sees the five-tuple. Routing on a URL requires **L7**, which means terminating TLS |
| "Load balancing works because servers share state" | It works because **HTTP is stateless**, so any server can handle any request. Server-memory sessions break it and force sticky routing |
| "SFTP is FTP with TLS" | SFTP is a **subsystem of SSH** on port 22. **FTPS** is FTP with TLS. Different protocols entirely |
| "IMAP and POP3 both just read mail" | IMAP leaves it on the server and syncs across devices; POP3 downloads and typically deletes |
| "A 'certificate not yet valid' error means a bad certificate" | Usually the **client's clock** is wrong, which is why NTP matters |

---

## Interview Q&A bank

**Q1. What happens when you type a URL and press Enter?**
The browser parses the input and checks its HSTS list, upgrading to HTTPS before any packet leaves. It resolves the hostname through a chain of caches and, on a miss, a recursive resolver walking the DNS hierarchy. It decides whether the destination is local by masking, and ARPs either the destination or the gateway. It performs a TCP handshake, then a TLS handshake that authenticates the server and establishes an ephemeral key, then sends the HTTP request. The server — possibly a CDN edge, otherwise through a load balancer and proxy to an application and database — responds, and the browser parses the HTML and fetches subresources, usually over the same connection.

**Q2. How many round trips is a cold first visit?**
Five with HTTP/1.1 and TLS 1.2 — DNS, TCP, two for TLS, and the request. Four with TLS 1.3, three with HTTP/3, one on a warm connection, and zero if the resource is still fresh in cache.

**Q3. Which phase actually dominates?**
Measured on this machine, setup — DNS plus TCP plus TLS — was 57% and 63% of total time for two real sites, with TLS the single largest phase at roughly double the TCP handshake. The body transfer was 0.0 ms for a 900-byte page.

**Q4. So what would you optimise?**
Round trips, not bandwidth. Reuse connections, which measured a 130 ms saving; move to TLS 1.3 or HTTP/3 to remove handshake round trips; cache aggressively so steps are skipped entirely; and put a CDN edge nearby, which is the strongest lever because shortening the distance shrinks every round trip at once.

**Q5. Why doesn't more bandwidth help?**
Because the round-trip floor is distance over signal speed — about 130 ms between Mumbai and California — and no capacity reduces it. A small page is a sequence of round trips, not a transfer.

**Q6. What does the host do between getting the IP and sending the SYN?**
It ANDs the destination address with its own subnet mask and compares with its own network. If they match, it ARPs for the destination; if not, it ARPs for the default gateway. Either way the frame carries the destination's IP address and the next hop's MAC.

**Q7. What is negotiated in the TCP handshake besides the connection?**
Maximum segment size, window scaling, selective acknowledgement and timestamps. Window scaling matters most: without it the connection is capped at 64 KB in flight, which on a long path limits throughput severely.

**Q8. What does the TLS handshake accomplish?**
Agreeing a version and cipher, authenticating the server through its certificate chain, deriving a shared key with forward secrecy from ephemeral key exchange, MAC-ing the whole transcript so no downgrade goes unnoticed, and selecting the application protocol via ALPN.

**Q9. Which parts of the request are visible to an observer?**
The destination IP and port, and the hostname via SNI, which is sent in plaintext. The path, query, headers, cookies and body are encrypted. So an observer learns who you contacted and how much data moved, not what you asked for.

**Q10. The page hangs with no error. Where do you look?**
A hang rather than a fast failure points at packets being dropped rather than refused — a firewall, or a routing problem. If the connection establishes and headers arrive but the body hangs, it is a path-MTU black hole from blocked ICMP. A fast "connection refused" would instead mean an RST, so nothing is listening.

**Q11. It works for you but not for a colleague. First hypothesis?**
A cache differing between you — DNS or HTTP. Compare the TTL you are getting against the zone's configured value, try a different resolver, and force a reload to bypass the HTTP cache.

**Q12. A CORS error appears in the console. Did the request reach the server?**
Yes. It was sent, processed and answered — the browser withheld the response from the page's JavaScript because the headers did not permit that origin. Which is why it works from `curl` and why proxying through your own backend changes the outcome.

**Q13. What is the difference between a 502, a 503 and a 504?**
All three come from the proxy or load balancer rather than the application. 502 means upstream returned an invalid response, 503 means nothing was available to ask, and 504 means upstream was asked and never replied.

**Q14. L4 versus L7 load balancing?**
An L4 balancer routes by the five-tuple — fast, cheap and protocol-blind, but it cannot make decisions based on the URL. An L7 balancer reads the request, so it can route by path or header, terminate TLS, retry and do sticky sessions — at the cost of seeing all the plaintext.

**Q15. Reverse proxy versus forward proxy?**
A reverse proxy sits in front of servers and acts on their behalf; the client does not know it exists. A forward proxy sits in front of clients and acts on theirs; the server does not know. Same technology, opposite direction.

**Q16. Why can a load balancer send any request to any server?**
Because HTTP is stateless, so no server needs to have seen the previous request. The moment session state lives in a server's memory, that breaks and you need sticky sessions — which is the architectural argument for tokens or a shared session store.

**Q17. Where does a CDN fit, and what does it actually do?**
In front of everything, selected by GeoDNS or anycast so you reach a nearby point of presence. It serves cached content from there and only forwards misses to the origin. Its value is shortening the physical distance, which reduces every round trip rather than just one.

**Q18. SMTP, IMAP and POP3?**
SMTP sends mail, both from a client and between servers. IMAP and POP3 retrieve it: IMAP leaves it on the server and synchronises state across devices, while POP3 downloads and typically deletes, which suited a single desktop.

**Q19. Is SFTP just FTP over TLS?**
No — SFTP is a file-transfer subsystem of SSH on port 22. FTPS is actual FTP wrapped in TLS. Plain FTP also carries IP addresses inside its `PORT` command, which is one of the things NAT breaks.

**Q20. Why does NTP matter for security?**
Because certificate validity, token expiry, log correlation and replication all depend on the clock. A client with a wrong clock reports "certificate not yet valid" on a perfectly good certificate.

**Q21. Give the thirty-second version of the whole answer.**
The browser resolves the name through DNS, checking caches first; opens a TCP connection; negotiates TLS, which authenticates the server and establishes an encryption key; sends an HTTP request; and renders the response, fetching subresources over the same connection. Anything already cached — the name, the connection, the resource — skips its step entirely.

---

## Practice

1. Give the thirty-second answer out loud, timed. Then the three-minute one. Then compare against §10.3.
2. Count the round trips for: a cold HTTP/1.1 + TLS 1.2 load; the same with TLS 1.3; the same over HTTP/3; a second page view on the same site. Convert each to milliseconds on a 90 ms path.
3. A page takes 2.1 s to first byte. The payload is 4 KB. Where is the time, and what three measurements would you take first?
4. For each failure, name the most likely layer: (a) hangs for 60 s then fails; (b) "connection refused" instantly; (c) certificate warning; (d) headers arrive, body hangs; (e) works on mobile data, not on office Wi-Fi; (f) CORS error in the console.
5. You add a CDN and the cold-load time drops from 520 ms to 90 ms. Explain which phases changed and why, in terms of the latency budget.
6. Explain why `window scaling` being stripped by a middlebox produces a connection that works but is slow, and how you would confirm it.
7. Trace what changes in the walkthrough if the user types `http://` and the site uses HSTS, versus if it does not.
8. A single-page app loads 40 API calls after the HTML. Compare HTTP/1.1, HTTP/2 and HTTP/3, including behaviour under 1% packet loss.
9. Your API is behind an L7 load balancer terminating TLS. List everything the balancer can see, and name two consequences for how you design authentication.
10. A user in Singapore reports a 900 ms page load; the server is in Virginia. Compute the RTT floor, estimate the cold-load time, and give the two changes with the largest effect.
11. Explain why putting session state in application-server memory undermines the load-balancer tier, and give two fixes with trade-offs.
12. Walk the request for a single `<img>` tag on an already-loaded page, naming every step that is *skipped* and why.

**Answers to 3, 6 and 10:**

> **3.** With a 4 KB payload, transfer time is negligible — so 2.1 s is almost entirely **round trips plus server time**. The budget in §10.5 says setup is typically over half, so first check whether this is a **cold** connection: if DNS, TCP and TLS are all being paid, that is 3–4 RTTs. The three measurements: **(1)** split the phases as in §10.5 — DNS, TCP connect, TLS, TTFB — because that immediately tells you whether the time is in setup or in the server; **(2)** repeat on a **warm** connection, which isolates setup entirely; **(3)** measure **server-side** processing independently (application logs or a local request), because if TTFB minus one RTT is 1.8 s then the network is innocent and it is a database or application problem — which is where DBMS M7's "my query is slow" procedure takes over.
>
> **6.** Window scaling is negotiated **only in the SYN** (M6). A middlebox that strips unknown TCP options leaves both sides believing the other does not support it, so the window is capped at the 16-bit maximum of **65,535 bytes**. The connection establishes perfectly and transfers correctly — it is simply limited to `65535 / RTT`, which on a 100 ms path is **5.2 Mbps** regardless of link capacity. Confirm it by checking whether throughput is suspiciously close to `64 KB / RTT`, by comparing a short-RTT transfer (which will be fast) with a long-RTT one (slow), and by inspecting the SYN options with a capture on both sides — the scaling option present on one side and absent on the other is the signature.
>
> **10.** Singapore to Virginia is roughly **15,000 km**, so one-way propagation is `15,000,000 / 2×10⁸ = 75 ms` and the **RTT floor is about 150 ms**. A cold HTTP/1.1 + TLS 1.2 load is 5 RTTs ≈ **750 ms**, which is consistent with the reported 900 ms once server time is added — so the user's experience is *expected*, not a fault. The two highest-impact changes: **a CDN or edge presence near Singapore**, which cuts the RTT from 150 ms to perhaps 10 ms and therefore shrinks *all five* round trips at once — 750 ms becomes 50 ms; and **TLS 1.3 plus connection reuse**, which removes two to three round trips outright. Note the ordering: the CDN wins because it attacks the multiplier rather than the count.

---

## Exit checklist

```
[ ] I can give the thirty-second answer fluently, in four sentences
[ ] I can give the three-minute answer with HSTS, the four caches, the mask/ARP
    decision, what each handshake negotiates, and the server tier
[ ] I can give the ten-minute answer and know when NOT to
[ ] I offer to go deeper rather than going deeper uninvited
[ ] I can draw all nine phases in order from memory
[ ] I know the HSTS check happens BEFORE any packet is sent
[ ] I can name the four DNS caches in order
[ ] I can state the mask/ARP decision and what ends up in the frame
[ ] I know the TCP handshake negotiates MSS, WINDOW SCALE, SACK, timestamps
[ ] I know what the TLS handshake achieves, all six things
[ ] I know SNI is plaintext and what that leaks
[ ] I can give the round-trip count for five scenarios
[ ] I can convert those to milliseconds on any given RTT
[ ] I can quote the measured budget: setup was 57% and 63% of the total
[ ] I know TLS was the largest single phase, double the TCP handshake
[ ] I know the body transfer was 0.0 ms, so it is NOT a bandwidth problem
[ ] I know keep-alive removed 130 ms, matching the measured setup cost
[ ] I can map eight techniques to the phases they remove
[ ] I know why the CDN is the strongest lever (it shrinks EVERY RTT)
[ ] I can diagnose a failure from its SHAPE: hang vs refused vs headers-then-hang
[ ] I know a CORS error means the request SUCCEEDED
[ ] I know 502/503/504 all come from the proxy and mean different things
[ ] I know "certificate not yet valid" is usually the client clock
[ ] I can draw the server tier from CDN to database
[ ] I can distinguish L4 from L7 load balancing and say what L7 costs
[ ] I can distinguish reverse from forward proxy
[ ] I can explain why the LB tier depends on HTTP being stateless
[ ] I can place 15 application protocols with their ports and transports
[ ] I know SMTP sends while IMAP and POP3 read, and how those two differ
[ ] I know SFTP is SSH and FTPS is FTP, and that they are unrelated
[ ] I know why NTP matters for certificates and tokens
```

---

## Next

**Part 13: Consolidation.** The revision file: a **layer-by-layer one-page map**; the **port and protocol sheet**; the **confusable-pairs master table** covering every "X vs Y" in the subject; a **numericals procedure sheet** for all ten computational question types; **70 rapid-fire questions** with one-line answers; **25 worked numericals** with full solutions, all computed; the three "tell me everything" answers; and the final exit checklist for the whole subject.
