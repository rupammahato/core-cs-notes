# Computer Networks Placement Handbook — Part 7
# Module 5: UDP and TCP Connection Management

**Module 5 · 4 hours · Tier 1 · Requires: M0 (layering, BDP), M3 (IP). Links to OS M3 (threads) and OS M10 (I/O)**

---

## Why this module matters

**This module answers more interview questions than any other in the handbook.** Not routing, not subnetting — this one. The list is short and it is asked relentlessly:

- **TCP vs UDP**, and which would you choose for a video call, a payment, a game, DNS
- **Explain the three-way handshake.** Why three and not two?
- **Explain the four-way close.** What is a half-close?
- **Why does `TIME_WAIT` exist, and why do I have thousands of them?**
- **What does a lot of `CLOSE_WAIT` tell you?**
- What is a socket? What is the five-tuple?
- What is a SYN flood, and what is a SYN cookie?

Several of these are also *operational* questions — a backend engineer who has debugged a production incident has met `CLOSE_WAIT` and knows why it matters. Answering them from mechanism rather than memory is what separates candidates here.

The organising principle:

> **IP delivers to a host. The transport layer's entire job is to deliver to a *process* — which is what a port number is for — and then to decide how much more to promise. UDP promises nothing beyond that and costs 8 bytes. TCP promises a reliable, ordered, flow-controlled byte stream, and pays for it with state at both ends, a round trip before any data moves, and a 20-byte header. Every question in this module is about the price of those promises.**

**How this module was verified.** The TCP and UDP headers were built and parsed field by field; the handshake, the half-close, and connection setup cost were measured on real sockets; the TCP state distribution is read live from this machine; and `TIME_WAIT` accumulation was **created on demand and counted** — 300 client-initiated closes produced a delta of exactly 300. One demonstration **did not** reproduce the behaviour I expected, and §5.8 says so and explains why.

---

## 5.1 What the transport layer adds

IP gets a packet to a host and stops. Three things are missing:

1. **Which process?** A machine runs a web server, a database and an SSH daemon. IP cannot tell them apart — hence **ports**.
2. **Did it arrive?** IP is best-effort: packets may be lost, duplicated, reordered or corrupted, and IP will not tell you.
3. **How fast may I send?** IP has no idea what the receiver or the network can absorb.

UDP solves only (1). TCP solves all three.

### Ports and the five-tuple

```
  a CONNECTION is identified by FIVE things, not two:

     (protocol, source IP, source port, destination IP, destination port)
```

That is the **five-tuple**, and it is the answer to several questions at once. A **socket** is the operating system's handle on one endpoint of this — and in **OS M10**'s terms it is a file descriptor, which is why `read`, `write`, `select` and `epoll` work on it.

```
  port ranges:
    0 - 1023      well known, privileged (binding needs root/admin)
    1024 - 49151  registered
    49152 - 65535 dynamic / ephemeral  (what a client's source port comes from)
```

Ports worth memorising, because they get asked directly:

```
     20  FTP data            80  HTTP              443  HTTPS
     21  FTP control        110  POP3              587  SMTP submission
     22  SSH                123  NTP               993  IMAPS
     23  Telnet             143  IMAP             3306  MySQL
     25  SMTP               161  SNMP             5432  PostgreSQL
     53  DNS (UDP and TCP)  67/68  DHCP svr/client 6379  Redis
                                                 27017  MongoDB
```

### "Can a server only handle 65,535 connections?"

A common and wrong claim, and the five-tuple is the refutation:

```
  ONE client to ONE server:port is limited by the client's ephemeral ports:
     16,384 (the IANA 49152-65535 range) -- the other four elements are fixed

  but a SERVER on ONE port accepts as many connections as there are distinct
  (client IP, client port) pairs -- effectively unbounded.
```

The server's port is a *constant* in the tuple, not a limit. The real limits are file descriptors, memory per connection and CPU — which is the C10K/C10M discussion, not an addressing one. A client talking to **one** destination does hit the ephemeral-port ceiling, which is why load generators need multiple source IPs.

---

## 5.2 UDP: the whole protocol

```
  raw: c82200350025abcd   (8 bytes, fixed)

  source port        51234    16 bits
  destination port   53       16 bits   (53 = DNS)
  length             37       16 bits   <- header + data
  checksum           0xabcd   16 bits   <- OPTIONAL in IPv4, mandatory in IPv6
```

Four fields. That is the entire protocol.

**8 bytes versus TCP's 20–60, and that size difference *is* the argument.** No sequence numbers, no acknowledgements, no window, no flags, no connection state — nothing to set up and nothing to tear down.

What UDP gives you: process-to-process delivery, a length, and an optional integrity check. What it does **not** give you: reliability, ordering, duplicate suppression, flow control or congestion control. A UDP datagram is a *message* — it arrives whole or not at all, with its boundaries intact, which is itself a feature TCP lacks.

### When UDP is the right answer

| Use | Why UDP wins |
|---|---|
| **DNS** | A query and an answer, both tiny. A TCP handshake would **triple** the number of round trips for a 100-byte reply |
| **DHCP** | The client has no IP address yet, so a TCP connection is impossible |
| **Voice and video calls** | A late packet is **worthless** — you cannot play audio from 300 ms ago. Better to drop it and continue than to stall the stream retransmitting it |
| **Games** | Same reasoning: position updates supersede each other, so the newest matters and old ones are noise |
| **Streaming (live)** | Latency budget over completeness |
| **SNMP, NTP, syslog** | Small, frequent, individually unimportant messages |
| **QUIC / HTTP/3** | UDP as a **substrate**, with reliability rebuilt in user space so it can be improved without kernel changes (M8) |

> **The sentence that gets this right:** *"Use UDP when a late packet is worse than a missing one, when the exchange is a single small request and response, or when you want to implement your own transport semantics."*

That third clause is the modern one. QUIC does not use UDP because it wants unreliability — it uses UDP because TCP is implemented in kernels that take a decade to upgrade, while a user-space transport over UDP can ship with the browser.

---

## 5.3 The TCP header

```
  raw: c82201bb5a4b3c2d112233445012faf000000000

  source port        51234        16 bits
  destination port   443          16 bits   (443 = HTTPS)
  sequence number    1514880045   32 bits   <- byte offset, NOT segment number
  acknowledgement    287454020    32 bits   <- NEXT byte expected
  data offset        5            4 bits    (20 bytes) -- in 32-bit WORDS
  flags              000010010    9 bits    SYN+ACK
  window             64240        16 bits   <- FLOW CONTROL (max 65535 w/o scaling)
  checksum           0x0000       16 bits   <- covers header + DATA + pseudo-header
  urgent pointer     0            16 bits   (essentially unused)
```

```
  0                   1                   2                   3
 +-------------------------------+-------------------------------+
 |          source port          |       destination port        |
 +---------------------------------------------------------------+
 |                        sequence number                        |
 +---------------------------------------------------------------+
 |                     acknowledgement number                    |
 +-------+-------+---------------+-------------------------------+
 | dataof| rsvd  |C E U A P R S F|            window             |
 +-------+-------+---------------+-------------------------------+
 |           checksum            |        urgent pointer         |
 +-------------------------------+-------------------------------+
 |                    options (0-40 bytes)                       |
 +---------------------------------------------------------------+
```

### The fields that matter

| Field | What to know |
|---|---|
| **Sequence number** | The byte offset of the **first byte** of this segment's data, not a segment counter. TCP numbers **bytes** |
| **Acknowledgement number** | The **next** byte expected — i.e. everything below it has arrived. Cumulative |
| **Data offset** | Header length in 32-bit words. 5 = 20 bytes, max 15 = 60, so options get 40 bytes |
| **Window** | How many **more** bytes the receiver can accept. 16 bits → 65,535 without scaling (M0 §0.10) |
| **Checksum** | Covers the header, the **data**, and a pseudo-header containing the IP addresses — which is why a NAT box must recompute it |
| **Flags** | The six classic ones below, plus ECE/CWR for ECN and NS |

```
  SYN  synchronise -- open a connection and carry an initial sequence number
  ACK  this segment's acknowledgement field is meaningful (set on nearly everything)
  FIN  I have no more data to send
  RST  abort immediately, abnormally -- no graceful exchange
  PSH  deliver to the application now, do not wait to fill a buffer
  URG  the urgent pointer is meaningful (obsolete in practice)
```

**The one to understand properly is `RST`.** A FIN means "I am finished"; an RST means "this connection is invalid, throw it away". You get an RST when you connect to a port with nothing listening, when you send to a connection the peer has forgotten, or when an application aborts rather than closing. "Connection reset by peer" is this flag.

**The options are not optional in practice.** MSS negotiation, **window scaling** (without which M0's bandwidth-delay arithmetic makes TCP unusable on fast links), SACK and timestamps all live there, which is why a real SYN is 40–60 bytes rather than 20.

---

## 5.4 The three-way handshake

```
   client                                        server
     |                                             |  LISTEN
     |-- SYN, seq=x --------------------------->   |  SYN_RCVD
     |   SYN_SENT                                  |
     |<------------- SYN+ACK, seq=y, ack=x+1 ---   |
     |-- ACK, ack=y+1 -------------------------->  |  ESTABLISHED
     |   ESTABLISHED                               |
```

Measured on a real connection:

```
  server listening on 127.0.0.1:57311
  server socket state before any client: LISTEN
  client connected from 127.0.0.1:57312  (handshake took 320 us on loopback)
  the five-tuple now identifying this connection:
   (TCP, 127.0.0.1, 57312, 127.0.0.1, 57311)
```

### Why three and not two

The question behind the question, and the answer is not "to be safe":

> **Each side must learn that *its own* initial sequence number was received.** The SYN carries `x` and the SYN+ACK acknowledges it — that confirms the client→server direction. The SYN+ACK carries `y`, and **only the third message confirms it**. Two messages can establish agreement in one direction only; the third is what makes it mutual.

A useful framing is the **two-army problem**: two parties over a lossy channel can never be *certain* they agree, but three messages are the minimum that synchronises both sequence spaces. TCP accepts that residual uncertainty — which is why the final ACK can be lost and the connection still works, since data arriving implies the ACK.

**Why the ISN is random** rather than zero: two reasons. It prevents a delayed segment from an *old* connection on the same five-tuple from being accepted as valid in a new one; and a predictable ISN lets an off-path attacker forge segments into someone else's connection, which was a real exploit before randomisation.

### SYN flood and SYN cookies

A worthwhile attack to understand, because it exposes something about the handshake:

```
  the server allocates state on the SECOND message, not the third.
  so an attacker sends thousands of SYNs with spoofed source addresses:
    - the server replies SYN+ACK to addresses that never asked
    - it holds a half-open connection in SYN_RCVD, waiting
    - the backlog queue fills, and LEGITIMATE SYNs are dropped
  the attacker spends almost nothing; the server spends memory and a queue slot.
```

**SYN cookies** are the fix, and the idea is elegant: instead of storing state, the server **encodes** the state into the initial sequence number it sends — a hash of the five-tuple, a coarse timestamp and a secret. It then forgets the connection entirely. When the final ACK arrives it carries `y+1`, from which the server recovers and validates the original parameters. **No state is held until the handshake actually completes**, so there is nothing to exhaust. The cost is that some TCP options cannot be carried through, so cookies are usually enabled only when the backlog is under pressure.

---

## 5.5 The four-way close

```
   client                                        server
     |-- FIN, seq=u --------------------------->   |  CLOSE_WAIT
     |   FIN_WAIT_1                                |
     |<--------------------------- ACK, ack=u+1 -- |
     |   FIN_WAIT_2                                |  (server may still SEND)
     |<------------------------------ FIN, seq=v --|  LAST_ACK
     |-- ACK, ack=v+1 -------------------------->  |  CLOSED
     |   TIME_WAIT  (2 x MSL)                      |
     |   ... then CLOSED                           |
```

**Why four and not three:** a TCP connection is **two independent byte streams**, one in each direction, and each is closed separately. "I have no more data to send" does not mean "I will accept no more data". So each direction needs its own FIN and its own ACK.

(In practice the server's ACK and FIN are often combined into one segment when it has nothing left to send, which makes it look like three. The specification is four.)

### The half-close is a real feature — verified

```
   client sent data then shutdown(SHUT_WR)
   server reads: b'request done'
   server reads again (sees EOF): b''  <- empty = the FIN
   server can STILL send, and client receives: b"response AFTER the client's FIN"
```

The client declared itself done sending and **still received a reply afterwards**. That is `shutdown(SHUT_WR)` versus `close()`, and it matters: the empty read is how the server learns "the request is complete, no more is coming" — which is exactly how HTTP/1.0 with `Connection: close` signals the end of a request body.

Note also what the empty read *means*: **`recv()` returning zero bytes is not an error and not an empty message — it is the FIN.** Treating it as a retryable condition produces an infinite loop, and it is one of the most common socket-programming bugs.

---

## 5.6 The TCP state machine

```
                         CLOSED
                           |
            passive open   |   active open: send SYN
         +-----------------+-----------------+
         |                                   |
      LISTEN                             SYN_SENT
         |  recv SYN, send SYN+ACK           |  recv SYN+ACK, send ACK
      SYN_RCVD ----------------------------> ESTABLISHED
                 recv ACK                     |
                                              |
            +---------------------------------+---------------------------+
            | we close first (ACTIVE close)        peer closes first      |
            |                                       (PASSIVE close)       |
        send FIN                                 recv FIN, send ACK
            |                                             |
       FIN_WAIT_1                                    CLOSE_WAIT
            | recv ACK                                    | app calls close(),
       FIN_WAIT_2                                          | send FIN
            | recv FIN, send ACK                      LAST_ACK
        TIME_WAIT                                          | recv ACK
            | 2 x MSL elapses                           CLOSED
         CLOSED
```

The division worth holding onto: **the side that sends the first FIN does the *active* close and ends in `TIME_WAIT`; the side that receives it does the *passive* close and passes through `CLOSE_WAIT`.** Those two states are the ones you meet in production, and they mean completely different things.

### This machine's real distribution

```
  ESTABLISHED         71
  TIME_WAIT           55
  LISTENING           36

  (later, during this module's own measurements:)
  TIME_WAIT is 260 of 367 sockets (71%)
```

---

## 5.7 `TIME_WAIT`: why it exists and why there are so many

### Verified: created on demand

```
  before: TIME_WAIT=465  ESTABLISHED=67
  after 300 client-initiated closes: TIME_WAIT=765  (delta 300)
  -> the side that closes FIRST is the side that pays TIME_WAIT.
```

**Exactly 300 new `TIME_WAIT` sockets for 300 closes.** One per connection, on the closing side, with no exceptions — which also explains the 71% figure above: those were this module's own test connections.

And the netstat rows show precisely *which* port holds the state:

```
  client closed first, port 63725:
    TCP    127.0.0.1:63726   127.0.0.1:63725   TIME_WAIT     <- the CLIENT's port
  server closed first, port 63727:
    TCP    127.0.0.1:63727   127.0.0.1:63728   TIME_WAIT     <- the SERVER's port
```

### The two reasons, and you need both

**1. The final ACK may be lost.** If it is, the peer's `LAST_ACK` timer fires and it **retransmits its FIN**. Only a socket still in `TIME_WAIT` can answer that retransmission with another ACK. A socket that had gone straight to `CLOSED` would reply with an **RST**, and the peer would report an error on a connection that had in fact finished cleanly.

**2. A delayed duplicate must not contaminate a new connection.** If a segment from this connection is wandering the network and a *new* connection reuses the same five-tuple, that old segment could be accepted as valid data. `2 × MSL` is chosen as the time after which no segment from the old connection can still exist — one MSL for the segment to die, one for its response.

**MSL** (maximum segment lifetime) is 2 minutes by convention, so `TIME_WAIT` is nominally 4 minutes. In practice Linux uses 60 s and Windows 2 minutes.

### Why a server with many `TIME_WAIT` sockets is usually fine

The interview-grade answer: **`TIME_WAIT` holds almost no resources** — a small kernel entry and a reservation on that five-tuple. It is not a leak and it expires by itself. The pattern that produces thousands of them is a client making many short-lived connections, and the correct fixes are **connection reuse** (HTTP keep-alive, a connection pool) rather than fighting the kernel.

The anti-patterns, which an interviewer may be probing for: `SO_LINGER` with a zero timeout skips `TIME_WAIT` by sending an RST, which abandons the guarantees above; `tcp_tw_recycle` was removed from Linux because it broke connections from behind NAT; lowering MSL globally weakens both protections. The legitimate tools are `SO_REUSEADDR` for servers, `tcp_tw_reuse` for outbound connections, and above all **not opening so many connections**.

### `CLOSE_WAIT` is a different animal entirely

```
  CLOSE_WAIT on this machine: 0
```

`CLOSE_WAIT` means: **the peer sent FIN, the kernel acknowledged it, and the local application has not called `close()`.** The kernel is waiting for the application, and it will wait forever.

> **It is the one TCP state that is almost always an application bug.** A leaked socket, a missing `close()` in an error path, a connection pool that never reaps. Many `CLOSE_WAIT` sockets are a file-descriptor leak that will eventually make the process fail to accept anything at all.

**The contrast is the thing to say:** *"Many `TIME_WAIT` is normal and self-healing — it is the kernel doing its job. Many `CLOSE_WAIT` is a defect in my code, because the kernel cannot leave that state until my application calls `close()`."* That answer demonstrates operational experience, and it is why this question gets asked.

---

## 5.8 A demonstration that did not work, and why

I expected to show that rebinding a server port fails without `SO_REUSEADDR` while a `TIME_WAIT` socket holds it. On this machine, it did not:

```
  client closed first, port 63725:  rebind WITHOUT SO_REUSEADDR: OK
  server closed first, port 63727:  rebind WITHOUT SO_REUSEADDR: OK
```

Both succeeded. The reason is a genuine platform difference rather than a flaw in the rationale: **Windows permits a wildcard or specific bind even when a `TIME_WAIT` entry exists for that port**, rejecting only an exact five-tuple conflict. On **Linux**, a `bind()` to a port with a `TIME_WAIT` connection fails with `EADDRINUSE` unless `SO_REUSEADDR` is set — which is why every server sets it and why "Address already in use" on restart is such a familiar message.

So the mechanism stands, the platform does not demonstrate it, and this section says so instead of presenting the Linux behaviour as something I observed. **The netstat rows in §5.7 are the part that did verify** — and they established the more important fact, that `TIME_WAIT` lands on whichever side sent the first FIN.

---

## 5.9 TCP vs UDP

### The table

| | TCP | UDP |
|---|---|---|
| Connection | **Connection-oriented** — 3-way handshake | **Connectionless** — just send |
| Reliability | Guaranteed delivery via ACKs and retransmission | **None** |
| Ordering | **Guaranteed** | None — datagrams may arrive in any order |
| Duplicate suppression | Yes | No |
| Flow control | Yes — the receive window | No |
| Congestion control | **Yes** | **No** (and this is the dangerous omission) |
| Header size | **20–60 bytes** | **8 bytes** |
| Data model | **Byte stream** — no message boundaries | **Datagram** — boundaries preserved |
| State at endpoints | Yes, substantial | None |
| Setup latency | **One RTT before any data** | Zero |
| Broadcast / multicast | **No** | **Yes** |
| Speed | Slower, with variable latency | Faster, predictable |
| Used by | HTTP(S), SSH, SMTP, FTP, databases | DNS, DHCP, VoIP, games, QUIC, NTP, SNMP |

### Measured on the same loopback

```
  one-way 64-byte send+receive, averaged over 2,000:
   UDP     5.29 us/message
   TCP     7.01 us/message

  connection setup cost:
   TCP connect+accept on loopback: median 165 us
   UDP: 0 us -- there is nothing to set up
```

Two honest readings of those numbers. **Per message, TCP costs about 32% more here** — real, and smaller than people expect, because loopback has no loss and no congestion for TCP to manage. And **setup is the dominant difference**: 165 µs on loopback, but on a real network the handshake is **one full RTT before a single byte of data moves** — 130 ms on the Mumbai-to-California path from M0. *That* is the number that matters, and it is why DNS uses UDP and why QUIC folds its handshake into the first flight.

### Two things people get wrong

**"TCP's byte stream is the same as UDP's datagrams."** It is not, and this causes real bugs. TCP preserves **bytes**, not **messages** — two `send()` calls may arrive as one `recv()`, or one `send()` may arrive as three. Any protocol over TCP must frame its own messages (a length prefix, or a delimiter like HTTP's `\r\n\r\n`). UDP preserves boundaries exactly: one `sendto()` is one `recvfrom()`.

**"UDP is just TCP without the reliability."** The more important omission is **congestion control**. A UDP application that sends as fast as it can will keep sending during congestion, while TCP flows back off — so it crowds them out and can contribute to collapse. Which is why responsible UDP protocols implement their own congestion control: QUIC does, and WebRTC does.

### The decision, which is how the question is really asked

| Scenario | Choice | Reason |
|---|---|---|
| Fetching a web page | **TCP** | Every byte matters and must be in order |
| A bank transfer | **TCP** | Loss is unacceptable, and latency is irrelevant at human scale |
| A video call | **UDP** | A 300 ms-old audio frame is worthless; dropping it beats stalling for it |
| A multiplayer game's position updates | **UDP** | Newer updates supersede older ones, so retransmitting stale ones is harmful |
| A game's chat and inventory | **TCP** | Same application, different requirements — mixing both is normal |
| DNS lookup | **UDP**, falling back to TCP | One small exchange; TCP's handshake would triple the round trips |
| DNS zone transfer | **TCP** | Large and must be complete |
| Live sports stream | **UDP** | Latency budget beats completeness |
| Netflix-style video on demand | **TCP** (HTTP) | Buffered, so there is time to retransmit, and completeness matters |
| File upload | **TCP** | Obviously |
| HTTP/3 | **UDP** | Reliability rebuilt in user space so it can evolve without kernel upgrades |

**The pattern to notice and say out loud:** *"Live and on-demand video make opposite choices, and so do a game's position updates and its chat. The question is never 'which protocol is better' — it is whether a late packet is useful, and whether you can afford a round trip before you start."*

---

## Must remember

```
THE TRANSPORT LAYER adds: WHICH PROCESS (ports), DID IT ARRIVE (acks), HOW FAST
 (window). UDP does only the first. TCP does all three.

FIVE-TUPLE = (protocol, src IP, src port, dst IP, dst port). A socket is the OS's
 handle on one endpoint -- a FILE DESCRIPTOR (OS M10), hence read/write/select/epoll.
 ports: 0-1023 well known (privileged) | 1024-49151 registered | 49152-65535 ephemeral
 "a server can only handle 65535 connections" IS WRONG: the server's port is a
 CONSTANT in the tuple. One CLIENT to one server:port is capped by ephemeral ports
 (~16k); a server is capped by file descriptors, memory and CPU.
 PORTS: 20/21 FTP, 22 SSH, 23 Telnet, 25 SMTP, 53 DNS, 67/68 DHCP, 80 HTTP,
 110 POP3, 123 NTP, 143 IMAP, 161 SNMP, 443 HTTPS, 3306 MySQL, 5432 Postgres,
 6379 Redis, 27017 MongoDB

UDP HEADER = 8 bytes FIXED: src port | dst port | length | checksum. That is all.
 checksum OPTIONAL in IPv4, MANDATORY in IPv6.
 preserves MESSAGE BOUNDARIES (one sendto = one recvfrom)
 supports BROADCAST and MULTICAST; TCP cannot
 use UDP when a LATE PACKET IS WORSE THAN A MISSING ONE, when the exchange is one
 small request/response, or when you want to implement your own transport (QUIC)

TCP HEADER 20-60 bytes
 seq = BYTE OFFSET of the first data byte (TCP numbers BYTES, not segments)
 ack = the NEXT byte expected (so everything below it arrived) -- CUMULATIVE
 data offset in 32-bit WORDS (5 = 20 bytes, 15 = 60, so options get 40)
 window = flow control, 16 bits -> 65535 without scaling
 checksum covers HEADER + DATA + a PSEUDO-HEADER with the IP addresses
   -> which is why a NAT box must recompute it
 FLAGS: SYN open | ACK ack field valid | FIN done sending | RST ABORT, invalid
        PSH deliver now | URG obsolete
 FIN = "I am finished"; RST = "this connection is invalid, discard it".
   "Connection reset by peer" is an RST.
 options are NOT optional in practice: MSS, WINDOW SCALE, SACK, timestamps

THREE-WAY HANDSHAKE   SYN(x) -> SYN+ACK(y, ack x+1) -> ACK(ack y+1)
 states: LISTEN -> SYN_RCVD -> ESTABLISHED  /  SYN_SENT -> ESTABLISHED
 WHY THREE: each side must learn ITS OWN ISN was received. Two messages confirm
 ONE direction; the third makes it MUTUAL. (The two-army problem.)
 ISN IS RANDOM to reject stale segments from an old connection on the same
 five-tuple, and to stop off-path attackers forging segments.
 SYN FLOOD: the server allocates state on the SECOND message, so spoofed SYNs
 fill the backlog cheaply. SYN COOKIES encode the state INTO the ISN (hash of the
 five-tuple + coarse time + secret) and hold NO state until the final ACK returns.

FOUR-WAY CLOSE  FIN -> ACK -> FIN -> ACK
 FOUR because a connection is TWO INDEPENDENT BYTE STREAMS, closed separately.
 HALF-CLOSE: shutdown(SHUT_WR) says "no more from me" and STILL RECEIVES (verified).
 recv() RETURNING 0 IS THE FIN -- not an error, not an empty message.
   Treating it as retryable is an infinite loop and a classic bug.

ACTIVE close (sent the first FIN) -> FIN_WAIT_1 -> FIN_WAIT_2 -> TIME_WAIT -> CLOSED
PASSIVE close (received it)       -> CLOSE_WAIT -> LAST_ACK -> CLOSED

TIME_WAIT exists for TWO reasons, and you need both:
 1. the final ACK may be LOST; the peer retransmits its FIN and only a socket
    still in TIME_WAIT can ACK it. A CLOSED socket would send RST and the peer
    would report an error on a cleanly-finished connection.
 2. a delayed duplicate must not be accepted by a NEW connection on the same
    five-tuple. 2 x MSL is how long a segment can still exist.
 MSL = 2 min by convention -> TIME_WAIT nominally 4 min (Linux 60 s, Windows 2 min)
 VERIFIED: 300 client-initiated closes produced EXACTLY 300 new TIME_WAIT sockets,
 and netstat shows the state sits on WHICHEVER SIDE SENT THE FIRST FIN.
 Many TIME_WAIT is NORMAL and self-healing. Fix it with CONNECTION REUSE
 (keep-alive, pooling), not with SO_LINGER 0 (sends RST, abandons the guarantees)
 or tcp_tw_recycle (removed from Linux -- broke NAT).

CLOSE_WAIT means THE PEER SENT FIN AND MY APPLICATION HAS NOT CALLED close().
 It is almost always an APPLICATION BUG -- a leaked socket, a missing close() in an
 error path, a pool that never reaps. The kernel cannot escape it alone.
 MANY TIME_WAIT = normal.  MANY CLOSE_WAIT = a file-descriptor leak.

TCP vs UDP: connection-oriented/connectionless; reliable/not; ordered/not;
 flow+congestion control/neither; 20-60/8 byte header; BYTE STREAM/DATAGRAM;
 state/none; one RTT setup/zero; no broadcast/broadcast+multicast
MEASURED: 7.01 vs 5.29 us per 64-byte message on loopback (~32% more for TCP),
 and 165 us for connect+accept -- but on a real path setup is ONE FULL RTT, which
 is the number that actually matters.
TWO COMMON ERRORS:
 - TCP is a BYTE stream: two sends may arrive as one recv. You MUST frame your own
   messages (length prefix, or a delimiter like HTTP's blank line).
 - UDP's worse omission is NOT reliability but CONGESTION CONTROL: a greedy UDP
   flow crowds out TCP flows. QUIC and WebRTC implement their own.
DECISIONS: live video UDP / on-demand video TCP; game positions UDP / game chat TCP;
 DNS query UDP / zone transfer TCP. Same app, opposite answers -- ask whether a
 LATE packet is useful and whether you can afford a round trip first.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "A connection is identified by source and destination port" | The **five-tuple**: protocol, both addresses and both ports |
| "A server can only handle 65,535 connections" | The server's port is a constant in the tuple, so it is bounded by file descriptors, memory and CPU — not by port numbers. A *client* to one destination is capped by its ephemeral range |
| "TCP's sequence number counts segments" | It counts **bytes** — it is the offset of this segment's first data byte |
| "The ACK number is the last byte received" | It is the **next byte expected**. Off by one, and it matters in every trace |
| "The TCP checksum covers the segment" | Header, data **and** a pseudo-header containing the IP addresses — which is why NAT must recompute it |
| "The window field is congestion control" | **Flow control** — what the *receiver* can absorb. Congestion control is the sender's own `cwnd` and is not in the header at all (M6) |
| "A FIN and an RST are both ways to close" | A FIN closes gracefully; an **RST aborts** and declares the connection invalid. "Connection reset by peer" is an RST |
| "TCP options are rarely used" | MSS, window scaling, SACK and timestamps are all options, and without window scaling TCP cannot fill a fast link |
| "The handshake is three-way for reliability" | Each side must learn **its own** ISN was received. Two messages confirm one direction; the third makes it mutual |
| "The ISN is random for performance" | For correctness and security: it rejects stale segments from an earlier connection on the same five-tuple and stops off-path forgery |
| "A SYN flood works by sending a lot of traffic" | It works because the server allocates state on the **second** message, so a trickle of spoofed SYNs fills the backlog cheaply. It is a state-exhaustion attack, not a volumetric one |
| "SYN cookies store the connection somewhere cheaper" | They store **nothing**. The state is encoded into the ISN and recovered from the client's final ACK |
| "Closing takes three messages, like the handshake" | **Four**, because the two directions are independent streams closed separately. They are sometimes coalesced into three in practice |
| "`recv()` returning 0 means no data right now" | It means the peer sent **FIN**. Treating it as retryable gives an infinite loop — a classic socket bug |
| "`shutdown()` and `close()` are the same" | `shutdown(SHUT_WR)` closes one direction and **keeps receiving** — verified: the client got a reply after its own FIN |
| "`TIME_WAIT` is a bug or a leak" | It is required for correctness, holds almost no resources, and expires by itself. Verified: exactly one per closed connection |
| "`TIME_WAIT` exists so the kernel can clean up" | Two specific reasons: to ACK a retransmitted FIN if the final ACK was lost, and to let any delayed duplicate expire before the five-tuple is reused |
| "`TIME_WAIT` appears on the server" | On whichever side sent the **first FIN** — verified in `netstat`, where the port holding the state changed with the close order |
| "Fix many `TIME_WAIT` with `SO_LINGER 0`" | That sends an RST and abandons both guarantees. Fix it with **connection reuse** — keep-alive and pooling |
| "`CLOSE_WAIT` and `TIME_WAIT` are similar states" | Opposite meanings. `TIME_WAIT` is the kernel doing its job; `CLOSE_WAIT` is your application failing to call `close()` |
| "TCP guarantees my messages arrive whole" | TCP is a **byte stream**. Two sends may arrive as one receive. You must frame your own messages |
| "UDP is TCP minus reliability" | It is also minus **congestion control**, which is the more consequential omission — a greedy UDP flow crowds out TCP ones |
| "UDP is always faster" | Measured 5.29 vs 7.01 µs per message on loopback — about 32%, less than people expect. The real difference is the **one-RTT setup** |
| "HTTP/3 uses UDP because it doesn't need reliability" | It rebuilds reliability in **user space**, so the transport can evolve without waiting for kernel upgrades |
| "Video always uses UDP" | Live video does; on-demand video uses TCP over HTTP, because buffering leaves time to retransmit |

---

## Interview Q&A bank

**Q1. What does the transport layer add over IP?**
Delivery to a **process** rather than a host, via port numbers; optionally reliability through acknowledgements and retransmission; and rate control, both for the receiver and for the network.

**Q2. What is a socket, and what is the five-tuple?**
A socket is the operating system's handle on one endpoint of a connection — in practice a file descriptor, which is why the normal I/O calls work on it. The five-tuple is what uniquely identifies a connection: protocol, source address, source port, destination address and destination port.

**Q3. Can a server handle more than 65,535 connections on one port?**
Yes. Its port is a constant in the five-tuple, so connections are distinguished by the client's address and port. The real limits are file descriptors, memory per connection and CPU. A *client* talking to one destination is capped by its ephemeral port range, which is why load generators use multiple source addresses.

**Q4. Describe the UDP header.**
Four 16-bit fields in 8 fixed bytes: source port, destination port, length, and a checksum that is optional in IPv4 and mandatory in IPv6. That is the whole protocol.

**Q5. When would you choose UDP?**
When a late packet is worse than a missing one — voice, video, game state. When the exchange is one small request and response, like DNS, where a handshake would triple the round trips. When the client has no address yet, as in DHCP. Or when you want to implement your own transport semantics, which is what QUIC does.

**Q6. Walk me through the TCP header.**
Source and destination ports; a sequence number that is the byte offset of this segment's first data byte; an acknowledgement number giving the next byte expected; a data offset in 32-bit words; nine flag bits; a receive window for flow control; a checksum covering the header, data and a pseudo-header with the IP addresses; and an urgent pointer that is effectively unused. Then up to 40 bytes of options — MSS, window scaling, SACK, timestamps.

**Q7. What does the sequence number count?**
Bytes, not segments. It is the offset of the first data byte in the segment, which is what lets TCP acknowledge, retransmit and reassemble at byte granularity.

**Q8. What is the difference between FIN and RST?**
A FIN closes one direction gracefully and expects an acknowledgement. An RST aborts immediately and declares the connection invalid — you get it when connecting to a closed port or sending to a connection the peer has forgotten. "Connection reset by peer" is an RST.

**Q9. Explain the three-way handshake.**
The client sends a SYN carrying its initial sequence number. The server replies with a SYN+ACK carrying its own and acknowledging the client's. The client sends a final ACK. Both sides are then established with synchronised sequence spaces.

**Q10. Why three messages and not two?**
Because each side must learn that **its own** initial sequence number was received. The SYN is acknowledged by the SYN+ACK, which confirms one direction; only the third message confirms the other. Two messages cannot establish mutual agreement.

**Q11. Why is the initial sequence number random?**
To stop a delayed segment from an earlier connection on the same five-tuple being accepted as valid, and to prevent an off-path attacker from guessing sequence numbers and injecting data into someone else's connection.

**Q12. What is a SYN flood, and what is a SYN cookie?**
The server allocates connection state when it sends the SYN+ACK, so an attacker sends many SYNs with spoofed sources, filling the backlog with half-open connections at almost no cost. SYN cookies encode the needed state into the initial sequence number — a hash of the five-tuple, a coarse timestamp and a secret — and keep no state until the client's final ACK returns it, so there is nothing to exhaust.

**Q13. Why does closing take four messages?**
Because a connection is two independent byte streams. Each direction has to be closed and acknowledged separately. In practice the passive side often combines its ACK and FIN, which makes it look like three.

**Q14. What is a half-close?**
Closing only your sending direction with `shutdown(SHUT_WR)` while continuing to receive. Verified: a client that shut down its write side still received a reply afterwards. The peer sees a zero-length read, which is how it learns the request is complete.

**Q15. What does `recv()` returning 0 mean?**
The peer sent FIN. It is not an error and not an empty message — it is end of stream. Treating it as retryable produces a busy loop, and it is one of the most common socket bugs.

**Q16. Why does `TIME_WAIT` exist?**
Two reasons. If the final ACK is lost, the peer retransmits its FIN, and only a socket still in `TIME_WAIT` can acknowledge it — a closed socket would reply with RST and the peer would see a failure on a clean close. And any delayed duplicate from this connection must expire before the same five-tuple is reused, which is what `2 × MSL` guarantees.

**Q17. Which side gets `TIME_WAIT`?**
Whichever sent the first FIN — the active closer. Verified in `netstat`: when the client closed first the state sat on the client's ephemeral port, and when the server closed first it sat on the server's port.

**Q18. I have 50,000 sockets in `TIME_WAIT`. Is that a problem?**
Usually not. Each holds a small kernel entry and a five-tuple reservation, and they expire on their own — verified at exactly one per closed connection. It indicates a pattern of many short-lived connections, and the right fix is connection reuse through keep-alive or a pool, not `SO_LINGER 0`, which sends an RST and abandons the guarantees.

**Q19. I have 50,000 sockets in `CLOSE_WAIT`. Is that a problem?**
Yes — that is a bug in the application. `CLOSE_WAIT` means the peer sent FIN, the kernel acknowledged it, and the local code has not called `close()`. It is a file-descriptor leak and the process will eventually stop accepting connections. The kernel cannot resolve it.

**Q20. So contrast those two states.**
Many `TIME_WAIT` is the kernel doing its job and resolves itself. Many `CLOSE_WAIT` is my code failing to close sockets and never resolves itself.

**Q21. TCP vs UDP?**
TCP is connection-oriented, reliable, ordered, with flow and congestion control, a 20–60 byte header, a byte-stream model, state at both ends and one round trip before data. UDP is connectionless, unreliable, unordered, has no flow or congestion control, an 8-byte header, preserves message boundaries, holds no state, and starts instantly. UDP also supports broadcast and multicast; TCP cannot.

**Q22. How much slower is TCP really?**
Measured on loopback, about 32% more per 64-byte message — 7.0 µs against 5.3 µs — which is less than most people expect, because loopback gives TCP nothing to recover from. The dominant cost is setup: one full round trip before any data, which on an intercontinental path is over 100 ms.

**Q23. What's the most important thing UDP lacks?**
Arguably congestion control rather than reliability. An application that sends as fast as it can will not back off during congestion, so it crowds out TCP flows. Responsible UDP protocols implement their own — QUIC and WebRTC both do.

**Q24. TCP delivers my messages intact, right?**
No. TCP preserves the **byte stream**, not message boundaries — two sends may arrive in one receive, or one send in three. Any protocol over TCP must frame its own messages, with a length prefix or a delimiter. UDP does preserve boundaries.

**Q25. Which protocol for a video call, and which for a file upload?**
UDP for the call, because a 300 ms-old audio frame is worthless and stalling to retransmit it makes the call worse. TCP for the upload, because every byte matters and latency does not.

**Q26. Why does live video use UDP but Netflix use TCP?**
Because the latency budgets differ. Live video must stay close to real time, so a late packet is useless. On-demand video is buffered seconds ahead, so there is ample time to retransmit, and completeness matters more than latency.

**Q27. Why does HTTP/3 run over UDP?**
Not because it wants unreliability — it rebuilds reliability and congestion control in user space. That lets the transport evolve with the browser instead of waiting for operating-system kernels to be upgraded, and it removes TCP's head-of-line blocking across multiplexed streams (M8).

---

## Practice

1. List the five elements of the five-tuple, then explain why two browser tabs can both connect to the same web server on port 443.
2. A client has the IANA ephemeral range and talks to one server on one port. What is its maximum concurrent connection count, and how would you raise it?
3. A TCP segment has sequence number 10,000 and carries 500 bytes. What acknowledgement number will the receiver send, and what does it assert?
4. Draw the three-way handshake with real numbers, choosing `x = 1000` and `y = 5000`. Label every field.
5. Explain why a two-way handshake is insufficient. Then explain why four would be unnecessary.
6. A server is under a SYN flood. Describe the resource being exhausted, and explain exactly how SYN cookies remove it.
7. Draw the four-way close, labelling every state on both sides. Mark where `TIME_WAIT` and `CLOSE_WAIT` appear.
8. Your code does `while True: data = sock.recv(1024); process(data)`. What happens when the peer closes, and what is the fix?
9. A monitoring dashboard shows 80,000 `TIME_WAIT` and 12 `CLOSE_WAIT` on a web server. Which do you investigate, and what do you do about each?
10. The same server later shows 40 `TIME_WAIT` and 60,000 `CLOSE_WAIT`. Now what?
11. For each, choose TCP or UDP and give the one-line reason: a stock-price ticker; a stock trade order; DNS; a DNS zone transfer; a video doorbell's live feed; its recorded clips; multiplayer position updates; multiplayer chat.
12. You are designing a protocol over TCP that sends JSON objects. What must you add, and why? What would change if you used UDP?

**Answers to 3, 9 and 10:**

> **3.** `10,500`. The acknowledgement number is the **next byte expected**, not the last received — so it asserts "I have every byte up to and including 10,499, send me 10,500 next". It is cumulative, so it also implicitly acknowledges everything before 10,000.
>
> **9.** Investigate the **`CLOSE_WAIT`**, even though it is a far smaller number. 80,000 `TIME_WAIT` on a web server is the expected consequence of many short-lived client connections — it is self-healing and the improvement is HTTP keep-alive or a connection pool, not a kernel setting. 12 `CLOSE_WAIT` is small but it is **the wrong shape**: it means sockets are being leaked somewhere, and 12 today is 60,000 next month. Find the code path that receives a FIN and never calls `close()`.
>
> **10.** That is now an emergency. 60,000 `CLOSE_WAIT` is an active file-descriptor leak, and the process will soon fail to accept any connection at all — typically surfacing as "too many open files" while the service appears healthy by CPU and memory. Restarting clears it and does not fix it. Look for a missing `close()` in an error path, an exception that skips cleanup, or a pool that never reaps idle connections; the dropped `TIME_WAIT` count is a *symptom* of the same thing, because connections are no longer completing their close at all.

---

## Exit checklist

```
[ ] I can say what the transport layer adds over IP, in three parts
[ ] I can give the five-tuple and explain why it has five elements
[ ] I can refute "a server is limited to 65535 connections" properly
[ ] I know a socket is a file descriptor, and why that matters (OS M10)
[ ] I know the port ranges and about 15 well-known port numbers
[ ] I can draw the UDP header -- all four fields, 8 bytes
[ ] I know UDP's checksum is optional in IPv4 and mandatory in IPv6
[ ] I can give four distinct reasons to choose UDP
[ ] I can draw the TCP header with every field and its width
[ ] I know seq counts BYTES and ack is the NEXT byte expected
[ ] I know the checksum includes a pseudo-header, and why NAT must recompute it
[ ] I know the window is FLOW control, not congestion control
[ ] I can name all six classic flags and explain FIN vs RST
[ ] I know the four options that matter and why they are not optional
[ ] I can draw the three-way handshake with field values and states
[ ] I can explain WHY three, from the mutual-ISN argument
[ ] I can give both reasons the ISN is random
[ ] I can explain a SYN flood as STATE exhaustion, not volume
[ ] I can explain how SYN cookies hold no state at all
[ ] I can draw the four-way close with all states on both sides
[ ] I know why it is four, and when it looks like three
[ ] I can explain the half-close and what shutdown(SHUT_WR) does
[ ] I know recv() == 0 IS the FIN, and the bug that follows from forgetting it
[ ] I can draw the TCP state machine, active and passive paths
[ ] I know the active closer gets TIME_WAIT and the passive one passes CLOSE_WAIT
[ ] I can give BOTH reasons TIME_WAIT exists
[ ] I know it lands on whoever sent the FIRST FIN
[ ] I know many TIME_WAIT is normal, and the right fix is connection reuse
[ ] I know why SO_LINGER 0 and tcp_tw_recycle are the wrong fixes
[ ] I can explain CLOSE_WAIT as an application bug, and what it leads to
[ ] I can state the TIME_WAIT vs CLOSE_WAIT contrast in one sentence
[ ] I can fill in the TCP vs UDP table from memory, all 13 rows
[ ] I know the measured per-message and setup costs, and which dominates on a real path
[ ] I know TCP is a BYTE STREAM and that I must frame my own messages
[ ] I know UDP's worse omission is congestion control, not reliability
[ ] I can make the TCP/UDP choice for ten scenarios and justify each in one line
[ ] I can explain why live and on-demand video choose differently
```

---

## Next

**Part 8: M6 — TCP Reliability, Flow and Congestion Control.** The third centrepiece. Sequence and acknowledgement numbers traced on real bytes; cumulative ACKs and SACK; retransmission — RTO, RTT estimation, Karn's algorithm, exponential backoff; **flow control** and the receive window, zero windows and **silly window syndrome** with both halves of the fix; then **congestion control** — why it is a separate problem from flow control, slow start, congestion avoidance, **AIMD**, fast retransmit and fast recovery, and **Tahoe vs Reno vs CUBIC vs BBR** — with a **worked `cwnd`-versus-RTT table traced through loss events**, plus why long fat networks need window scaling.
