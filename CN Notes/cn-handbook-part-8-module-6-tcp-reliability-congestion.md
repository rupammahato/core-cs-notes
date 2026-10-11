# Computer Networks Placement Handbook — Part 8
# Module 6: TCP Reliability, Flow and Congestion Control

**Module 6 · 5 hours · Tier 1 · Requires: M0 (BDP, delays), M1 (ARQ, sliding windows), M5 (TCP header, states)**

---

## Why this module matters

This is the **third centrepiece** and the heaviest Tier 1 module in the handbook. It is simultaneously the most-examined part of the transport layer and the part most often half-understood.

The questions:

- **Flow control vs congestion control** — asked constantly, and the distinction is the single most common thing candidates get wrong
- **Explain slow start, congestion avoidance and AIMD**
- **Fast retransmit vs fast recovery; Tahoe vs Reno**
- **How does TCP choose its retransmission timeout?**
- **Why is throughput ≈ window / RTT?** — and why window scaling exists
- Written tests add a **`cwnd`-versus-RTT trace through loss events**, which is the single most reliable numerical in the transport layer

The organising principle:

> **TCP has two independent brakes and they exist for two different reasons. The receive window protects the *receiver* from a sender that is too fast; the congestion window protects the *network* from everybody. The sender may send no more than the minimum of the two. Everything else — slow start, AIMD, fast recovery, CUBIC — is the algorithm for guessing the second number, because unlike the first it is never told to you.**

**How this module was verified.** The `cwnd` simulator was **self-tested against canonical hand-computed traces before being trusted**: Tahoe and Reno on the same loss event, the invariant that slow start doubles exactly and congestion avoidance adds exactly one, Reno-on-timeout being identical to Tahoe, and CUBIC's two defining boundary conditions. All passed. AIMD's fairness, the throughput ceiling, the Mathis loss relationship and the Jacobson/Karels RTO are all computed output.

---

## 6.1 Reliability: sequence numbers and acknowledgements

From M5: the sequence number is a **byte offset** and the acknowledgement number is the **next byte expected**. That is the whole basis of reliability.

```
  sender sends 3 segments, 1000 bytes each, starting at seq 5000

   seq=5000 len=1000   ->   receiver has 5000-5999, replies ack=6000
   seq=6000 len=1000   ->   receiver has 6000-6999, replies ack=7000
   seq=7000 len=1000   ->   receiver has 7000-7999, replies ack=8000

  now segment 2 is LOST:

   seq=5000 len=1000   ->   ack=6000
   seq=6000 len=1000   ->   X  lost
   seq=7000 len=1000   ->   arrives, but 6000-6999 is MISSING
                            so the receiver can only repeat ack=6000
   seq=8000 len=1000   ->   ack=6000 again
   seq=9000 len=1000   ->   ack=6000 again       <- 3 DUPLICATE ACKs
```

**Acknowledgements are cumulative**, which has one great virtue and one real weakness:

- **Virtue:** a lost ACK is harmless. If `ack=7000` is lost but `ack=8000` arrives, the sender learns everything it needed — `8000` implies `7000`. So ACKs need no reliability of their own.
- **Weakness:** the receiver cannot say "I got 7000–7999 but not 6000–6999". It can only repeat the lowest gap. The sender is told *where* the hole starts and nothing about what arrived after it.

### SACK — selective acknowledgement

The TCP option that fixes the weakness: the receiver reports the **blocks it actually received** alongside the cumulative ACK.

```
  without SACK:  ack=6000                      "I'm stuck at 6000"
  with SACK:     ack=6000, SACK=[7000-10000]   "I'm stuck at 6000, but I
                                                already have 7000 to 9999"
```

The sender then retransmits exactly the 1000-byte hole instead of guessing. Without SACK a sender facing multiple losses in one window learns about one hole per round trip; with SACK it learns about all of them at once. It is negotiated in the SYN and is universal in practice.

### Retransmission: the two triggers

```
  1. TIMEOUT        -- the retransmission timer expired. Interpreted as
                       "the network is badly congested or broken".
  2. 3 DUPLICATE ACKs -- later segments ARE arriving, so the path is alive
                       and a single segment was dropped. Interpreted as
                       "mild, isolated loss". Triggers FAST RETRANSMIT.
```

**Why three duplicates and not one?** Because reordering is normal. One or two duplicate ACKs most likely mean segments arrived out of order and the gap will fill itself in a moment. Three is the heuristic threshold at which loss becomes more likely than reordering — a tuned constant, not a derived one, which is worth saying because it sounds like it should be derived.

**Fast retransmit** is the resulting optimisation: resend the missing segment **immediately** on the third duplicate ACK, without waiting for the timer. Since the RTO is deliberately conservative (§6.5), that can save hundreds of milliseconds per loss.

---

## 6.2 Flow control: the receive window

The receiver advertises, in every segment, how much more it can buffer:

```
  sender                                        receiver
    |                                             |  buffer: 4000 bytes free
    |<-------------------------- ack=X, win=4000 -|
    |-- 4000 bytes ----------------------------->  |  buffer full,
    |                                             |  application hasn't read yet
    |<-------------------------- ack=Y, win=0 ----|  ZERO WINDOW
    |   (sender must STOP)                        |
    |                                             |  application reads 2000
    |<------------------------- WINDOW UPDATE -----|  win=2000
    |-- 2000 bytes ----------------------------->  |
```

The sender's rule: **unacknowledged data ≤ advertised window.** That is it.

**The zero-window deadlock, and its fix.** If the receiver advertises `win=0` and the later window update is lost, the sender waits forever while the receiver waits for data. TCP breaks it with a **persist timer**: the sender periodically sends a one-byte **window probe**, forcing the receiver to re-advertise. The probe is deliberately tiny and the timer deliberately slow.

### Silly window syndrome

Both ends can independently degrade a connection into tiny segments:

```
  RECEIVER-SIDE: the application reads 1 byte at a time, so the receiver
  advertises win=1 repeatedly. The sender dutifully sends 1-byte segments:
  41 bytes of header for 1 byte of data -- 2.4% efficiency.

  SENDER-SIDE: the application writes 1 byte at a time (a terminal, SSH),
  so the sender emits 1-byte segments for the same reason.
```

Two independent fixes, and the question usually wants both:

| Side | Fix | Rule |
|---|---|---|
| **Receiver** | **Clark's solution** | Do not advertise a window until it is at least one MSS, or half the buffer. Advertise zero rather than something useless |
| **Sender** | **Nagle's algorithm** | Do not send a small segment while an earlier small segment is still unacknowledged. Buffer small writes and send them as one |

Nagle's rule in full: *send immediately if you have a full MSS to send, or if there is no unacknowledged data outstanding; otherwise wait.* The effect is that the first small write goes out at once and subsequent ones are coalesced until its ACK returns — so it self-tunes to the RTT with no configuration.

**This is M0's 1.7%-efficiency figure in operational form:** a one-byte payload costs 59 bytes on the wire, and Nagle is why your SSH session does not send one packet per keystroke.

**And `TCP_NODELAY` disables it**, which matters because **Nagle interacts badly with delayed ACKs**. The receiver waits up to 200 ms before acknowledging (hoping to piggyback), while Nagle waits for that ACK before sending — so a request/response protocol that writes a header and then a body in two calls can stall for 200 ms per message. That interaction is the reason every latency-sensitive application sets `TCP_NODELAY`, and it is a genuinely good interview answer because it shows two reasonable optimisations combining into a bug.

---

## 6.3 Congestion control: a different problem entirely

**This distinction is the most important thing in the module.**

| | Flow control | Congestion control |
|---|---|---|
| Protects | The **receiver's** buffer | The **network's** capacity |
| Problem | A fast sender, a slow receiver | Too many senders for the links between them |
| Signal | **Explicit** — the receiver advertises a window | **Implicit** — inferred from loss or delay |
| Mechanism | `rwnd`, carried in the TCP header | `cwnd`, kept **only** in the sender's memory |
| Who knows the right value | The receiver knows exactly | **Nobody.** It must be guessed, continuously |
| Scope | One connection | All connections sharing the bottleneck |

```
   the sender may have in flight:    min(rwnd, cwnd)
                                          ^      ^
                            receiver's limit   network's limit (a guess)
```

> **The sentence to deliver:** *"Flow control stops me overwhelming the receiver, and the receiver tells me the number. Congestion control stops me overwhelming the network, and nobody tells me the number — so I have to discover it by increasing until something breaks, then backing off. That is why there is an algorithm for one and a header field for the other."*

**Why congestion control had to be invented.** In October 1986 the NSFNET backbone's throughput collapsed from 32 kbps to **40 bps** — a factor of 1,000. The cause: every sender retransmitted on timeout, retransmissions added load, load caused more loss, more loss caused more retransmissions. That is **congestion collapse**, and it is the same runaway feedback as ALOHA past its optimum (M2 §2.2). Van Jacobson's response — slow start and AIMD — is what this module describes, and it is why TCP has congestion control at all.

---

## 6.4 Slow start, congestion avoidance and AIMD

```
  cwnd starts at 1 MSS (modern: 10). ssthresh starts high.

  if cwnd < ssthresh:  SLOW START          -- cwnd DOUBLES each RTT
  if cwnd >= ssthresh: CONGESTION AVOIDANCE -- cwnd += 1 MSS each RTT
  on loss:             ssthresh = cwnd/2, and cwnd depends on the variant
```

### Verified

```
  ssthresh = 16, no loss
   RTT | cwnd | ssthresh | phase
     0 |    1 |       16 | slow start
     1 |    2 |       16 | slow start
     2 |    4 |       16 | slow start
     3 |    8 |       16 | slow start
     4 |   16 |       16 | congestion avoidance
     5 |   17 |       16 | congestion avoidance
     6 |   18 |       16 | congestion avoidance
     7 |   19 |       16 | congestion avoidance
```

Checked as invariants rather than eyeballed:

```
  slow-start ratios (must all be 2.0): {2.0}
  congestion-avoidance increments (must all be 1): {1}
```

**"Slow start" is exponential, which is the module's worst-named concept.** It is slow only relative to *original* TCP, which began by sending an entire window immediately. Starting at one segment and doubling is slow by comparison — and a candidate who says "slow start increases slowly" has misread it.

Why exponential at all: the sender has **no idea** what the path can carry, and the range of possibilities spans six orders of magnitude. Doubling finds the right order of magnitude in logarithmic time. Once it is in the right neighbourhood — which is what `ssthresh` records — caution becomes worthwhile, and growth switches to linear.

### AIMD, and why the asymmetry

**Additive Increase, Multiplicative Decrease.** Probe up by one, back off by half. The asymmetry is deliberate: overshooting causes loss that hurts everyone, so increase cautiously; congestion compounds, so decrease decisively.

But the deeper reason is **fairness**, and it can be demonstrated. Two flows sharing a 30-unit link, starting badly unequal at 20 and 4:

```
    round  flow A  flow B   total  ratio A:B
        0      20       4      24       5.00
        1      21       5      26       4.20
        2      22       6      28       3.67
        3      23       7      30       3.29
        4      11       3      14       3.67   <- loss: both halved
        5      12       4      16       3.00
        6      13       5      18       2.60
        7      14       6      20       2.33
        8      15       7      22       2.14
        9      16       8      24       2.00
```

**The ratio falls from 5.00 to 2.00 and keeps converging toward 1.** Additive increase adds the *same* amount to both, which narrows the gap proportionally; multiplicative decrease takes *more* from the bigger flow in absolute terms. Together they drive any starting point toward equality.

And the control: the same two flows under **AIAD** (add one, subtract one):

```
   after 10 rounds: A=22 B=6 ratio 3.67 -- the gap is preserved
```

**AIAD never converges.** Subtracting a constant from both preserves the difference forever, so whoever started ahead stays ahead. That is the proof that the asymmetry is load-bearing and not just conservative instinct — and it is a much better answer to "why halve?" than "to be safe".

---

## 6.5 Tahoe, Reno, and the loss distinction

### Verified: the same loss, two variants

`ssthresh` starts at 8; loss happens at RTT 6 when `cwnd = 11`.

```
  TAHOE (any loss -> ssthresh = cwnd/2, cwnd = 1, restart slow start)
   cwnd: 1, 2, 4, 8, 9, 10, 11, [LOSS], 1, 2, 4, 5, 6, ...

  RENO on 3 duplicate ACKs (FAST RECOVERY -> cwnd = ssthresh, stay linear)
   cwnd: 1, 2, 4, 8, 9, 10, 11, [LOSS], 5, 6, 7, 8, 9, ...
```

Both set `ssthresh = 11/2 = 5`. Tahoe then drops `cwnd` to **1** and climbs all the way back through slow start; Reno drops to **5** and continues adding one per RTT. On this trace Tahoe needs four RTTs to get back to 5 while Reno is already there — and on a large window the gap is far bigger.

Also verified, and worth stating because it is often missed:

```
  Reno on a TIMEOUT == Tahoe on a timeout:  MATCH
```

**Reno is not "better than Tahoe"; Reno distinguishes two kinds of loss.**

| Signal | What it means | Tahoe | Reno |
|---|---|---|---|
| **3 duplicate ACKs** | Later segments **are arriving** — the path works, one segment was dropped | `cwnd = 1` | **Fast recovery**: `cwnd = ssthresh`, stay in congestion avoidance |
| **Timeout** | **Nothing** is getting through | `cwnd = 1` | `cwnd = 1` — identical to Tahoe |

That is the real insight: duplicate ACKs are *evidence of delivery*. Receiving them proves segments are still flowing, so halving is a proportionate response. A timeout is evidence of nothing, so a full restart is appropriate.

### Fast retransmit vs fast recovery

Two different things with similar names, and the distinction gets asked:

- **Fast retransmit** — *resend the missing segment* on the third duplicate ACK rather than waiting for the timeout. Tahoe has this.
- **Fast recovery** — *do not collapse `cwnd` to 1* afterwards; set it to `ssthresh` and continue linearly. **This is what Reno added.**

### The variants in order

```
  variant         | on loss                      | adds                                   | note
  Tahoe (1988)    | any loss -> cwnd=1           | fast retransmit                        | simple; wastes a full restart
  Reno (1990)     | 3 dup ACK -> cwnd=ssthresh   | + fast recovery                        | one loss per RTT only
  NewReno         | as Reno                      | + partial ACK handling                 | multiple losses per window
  SACK            | selective acks               | receiver reports WHICH blocks arrived  | sender retransmits exactly the gaps
  CUBIC (default) | beta*W_max                   | cubic growth in real TIME              | RTT-fair, fills long fat pipes
  BBR (Google)    | ignores loss                 | models BOTTLENECK BW and RTprop        | avoids bufferbloat; fairness debated
```

---

## 6.6 CUBIC: what Linux actually runs

Reno's `+1 MSS per RTT` is hopeless on a modern long fat pipe. From M0: a 1 Gbps path with a 200 ms RTT has a BDP of 25 MB, which is about 17,000 segments — and recovering 8,500 of them at one per RTT takes **8,500 round trips**, or 28 minutes. That is not a tuning problem, it is a different regime.

**CUBIC** grows as a cubic function of the **time** since the last loss:

```
   W(t) = C(t - K)^3 + W_max        K = cbrt( W_max * (1 - beta) / C )
   C = 0.4,  beta = 0.7  (so cwnd drops to 70%, not 50%)
```

Verified, with both boundary conditions checked as invariants:

```
  CUBIC: W(K) == W_max and W(0) == beta*W_max for 4 sizes: 0 violations

  after a loss at W_max = 100: cwnd drops to 70, and K = 4.217 s

     t (s)     cwnd  shape
     0.000    70.00  #######################
     1.000    86.68  ############################
     2.000    95.64  ###############################
     3.000    99.28  #################################
     4.217   100.00  #################################  <- K: back at W_max
     5.000   100.19  #################################
     6.000   102.27  ##################################
     7.000   108.62  ####################################
     8.000   121.65  ########################################
```

**Read the shape, because the shape is the design.** Steep recovery toward the previous `W_max` (70 → 95 in two seconds), then it **flattens** right around it — cautious probing near the capacity that was known to work — then steepens again to look for more. A cubic is the simplest function with exactly that profile.

Two properties that matter:

1. **It is a function of real time, not of RTTs.** So a flow with a 200 ms RTT grows just as fast per second as one with 20 ms. **Reno is RTT-unfair** — a short-RTT flow gets `+1` ten times as often and crowds out the long one. CUBIC fixes that, and RTT fairness is the less famous but arguably more important of its two improvements.
2. `beta = 0.7` rather than 0.5, so it gives up less on each loss. Reasonable when loss is often *not* congestion (wireless bit errors, for instance).

### BBR: the conceptual break

Every variant above BBR treats **loss** as the congestion signal. That assumption has a flaw: routers have large buffers, so by the time loss occurs the buffers are already **full**, which means the queue is long and the latency is already bad. That is **bufferbloat** — a connection with excellent throughput and terrible latency.

**BBR** instead estimates the **bottleneck bandwidth** and the **minimum round-trip propagation time**, then paces at exactly bandwidth × RTprop. It does not need to fill a buffer to discover the limit, so it keeps queues short.

The honest caveats, which are what an interviewer probing this wants: BBR's fairness against loss-based flows is contested — early versions could take more than their share — and it needs accurate measurement that NICs and virtualisation can confound. It is deployed widely (Google, YouTube) and is not a settled replacement.

---

## 6.7 Throughput arithmetic

```
   throughput ≈ W / RTT
```

This is **M0's bandwidth-delay product read from the sender's side**: you can have `W` bytes outstanding and you learn the result one RTT later, so your rate is `W/RTT` regardless of how fast the link itself is.

Verified:

```
      window      RTT     throughput  note
      65,535      1ms       524.3 Mbps  max 16-bit window
      65,535     10ms        52.4 Mbps  max 16-bit window
      65,535    100ms         5.2 Mbps  max 16-bit window
      65,535    200ms         2.6 Mbps  max 16-bit window
   1,000,000    100ms        80.0 Mbps
  25,000,000    200ms      1000.0 Mbps
```

**A 100 ms path with the maximum unscaled window caps at 5.2 Mbps, no matter how fast the link is.** Put a gigabit intercontinental circuit under a stock 1981 TCP and you get 2.6 Mbps. That single row is the entire argument for **window scaling** (RFC 1323), which multiplies the 16-bit field by up to 2¹⁴ and lifts the ceiling to 1 GB. It is negotiated once, in the SYN — so if the SYN's options are stripped by a middlebox, the connection silently runs at 1981 speeds.

### Why a tiny loss rate ruins a long path

The **Mathis formula**, `throughput ≈ (MSS/RTT) × (C/√p)`:

```
      loss p  relative throughput
       1e-02                 10.0
       1e-03                 31.6
       1e-04                100.0
       1e-05                316.2
       1e-06               1000.0
```

**Throughput falls as `1/√p`.** A 1% loss rate costs a factor of ten against 0.01% — which is why a long fat path with a trace of loss performs catastrophically rather than slightly worse, and why "the link is only dropping 1% of packets" is not the reassurance it sounds like. (Tier 3 as a formula; the `1/√p` shape is worth remembering.)

---

## 6.8 Retransmission timeout: Jacobson/Karels

The RTO must be longer than the RTT — but by how much? Too short and you retransmit needlessly, adding load during congestion. Too long and you stall after every loss.

```
   SRTT   = (1 - α)·SRTT   + α·sample            α = 1/8
   RTTVAR = (1 - β)·RTTVAR + β·|SRTT − sample|   β = 1/4
   RTO    = SRTT + 4·RTTVAR                      (floor 1 s, RFC 6298)
```

Verified, with a deliberate 350 ms spike injected into a stable 100 ms path:

```
    sample     SRTT   RTTVAR      RTO  note
       100   100.00    50.00   300.00
       102   100.25    38.00   252.25
        98    99.97    29.06   216.22
       101   100.10    22.05   188.32
        99    99.96    16.82   167.22
       100    99.97    12.62   150.45
       350   131.22    71.97   419.12  <- a 350 ms spike
       105   127.94    60.54   370.09
       100   124.45    52.39   334.00
        98   121.14    45.90   304.76
       102   118.75    39.21   275.60
       100   116.41    34.10   252.80
```

**Watch exactly what the spike does.** `SRTT` barely moves — 100 to 131, because α = 1/8 smooths heavily. But `RTTVAR` **jumps from 12.6 to 72**, and since the RTO carries `4 × RTTVAR`, the timeout widens from 150 ms to 419 ms.

**That is the whole design.** The original TCP used only a smoothed mean, and on a variable path it retransmitted constantly — adding load precisely when the network was struggling. Jacobson's insight was that the timeout must be tolerant of **variance**, not just of the mean, because a path that *sometimes* takes 350 ms needs a timeout above 350 ms even though its average is 100. Notice also how slowly the RTO comes back down: 12 samples later it is still 252 ms, not 150. The estimator is deliberately quick to widen and slow to narrow.

### Karn's algorithm

> **Never take an RTT sample from a retransmitted segment.**

The reason is ambiguity: when you retransmit and an ACK arrives, you cannot tell whether it acknowledges the original (making the true RTT large) or the retransmission (making it small). Either assumption corrupts `SRTT` in a systematic direction, so the sample must be discarded.

But then a connection whose RTT has genuinely risen could never update its estimate. Karn's second half handles that: **on a timeout, double the RTO** and keep the doubled value until a clean, un-retransmitted sample arrives.

```
   timeout 1: RTO =    1.0 s
   timeout 2: RTO =    2.0 s
   timeout 3: RTO =    4.0 s
   timeout 4: RTO =    8.0 s
   timeout 5: RTO =   16.0 s
   timeout 6: RTO =   32.0 s
   timeout 7: RTO =   64.0 s  (typically capped ~64 s)
```

Exponential backoff, for the same reason as Ethernet's (M2 §2.4): if the network is overloaded, probing harder makes it worse. This is also why a connection to a dead host takes minutes to fail — the timeouts are doubling.

---

## 6.9 Bufferbloat and ECN (Tier 3)

**Bufferbloat:** router buffers got cheap, so they got large. A loss-based congestion control fills whatever buffer it finds before it sees loss, so a large buffer means a long standing queue — hundreds of milliseconds of latency for traffic that is achieving full throughput. One bulk download can make an interactive session unusable on the same link, which every home user has experienced without having the name for it.

Fixes come from both ends: **AQM** at the router (CoDel, FQ-CoDel, which drop early rather than when full) and **delay-based congestion control** at the sender (BBR, Vegas, which treat rising RTT as the signal).

**ECN** (explicit congestion notification) is the cleaner answer: a router near saturation **marks** a bit in the IP header instead of dropping the packet; the receiver echoes the mark back in the TCP header's `ECE` flag; the sender halves `cwnd` as if it had seen loss. **Congestion signalled without losing any data.** It needs support at both endpoints and in the routers between, which is why uptake has been slow — a coordination problem, like IPv6.

---

## Must remember

```
RELIABILITY
 seq = BYTE offset of the first data byte. ack = NEXT byte expected. CUMULATIVE.
 cumulative ACKs mean a LOST ACK IS HARMLESS (a later one implies it)
 but the receiver can only report the LOWEST GAP -> hence SACK, which lists the
 blocks that DID arrive so the sender retransmits exactly the holes
 two retransmission triggers:
   TIMEOUT          = nothing getting through    -> treat as severe
   3 DUPLICATE ACKs = later segments ARE arriving -> isolated loss
   three, not one, because REORDERING IS NORMAL. It is a tuned heuristic.
 FAST RETRANSMIT = resend on the 3rd dup ACK without waiting for the timer

FLOW CONTROL (rwnd) vs CONGESTION CONTROL (cwnd) -- THE KEY DISTINCTION
 flow:       protects the RECEIVER's buffer. EXPLICIT -- advertised in the header.
             The receiver KNOWS the right number.
 congestion: protects the NETWORK. IMPLICIT -- inferred from loss or delay.
             NOBODY knows the right number, so it must be guessed continuously.
 the sender may have in flight:  min(rwnd, cwnd)
 ZERO WINDOW deadlock -> PERSIST TIMER sends a 1-byte WINDOW PROBE
 SILLY WINDOW SYNDROME, two independent halves:
   receiver side -> CLARK: do not advertise a window below 1 MSS / half the buffer
   sender side   -> NAGLE: do not send a small segment while a small one is unacked
     (send if you have a full MSS, OR if nothing is outstanding; else buffer)
   Nagle self-tunes to the RTT with no configuration.
 NAGLE + DELAYED ACK = a 200 ms stall per message for write-header-then-body
   protocols. THAT is why latency-sensitive apps set TCP_NODELAY.

CONGESTION COLLAPSE: NSFNET 1986, 32 kbps -> 40 bps. Retransmissions added load,
 load added loss, loss added retransmissions. Same runaway feedback as ALOHA past
 its optimum. Jacobson's slow start + AIMD is the response.

 cwnd < ssthresh  -> SLOW START: cwnd DOUBLES per RTT (exponential!)
 cwnd >= ssthresh -> CONGESTION AVOIDANCE: cwnd += 1 MSS per RTT (additive)
 on loss          -> ssthresh = cwnd/2, cwnd per variant
 "slow start" is EXPONENTIAL -- slow only vs original TCP, which sent a whole
 window at once. Exponential because the right value spans orders of magnitude.

AIMD: additive increase, multiplicative decrease. The ASYMMETRY IS LOAD-BEARING.
 VERIFIED: two flows at 20 and 4 converge from ratio 5.00 to 2.00 in 10 rounds.
 Under AIAD the ratio STAYS 3.67 forever -- subtracting a constant preserves the gap.
 So AIMD converges to fairness and AIAD provably cannot. That is why you halve.

TAHOE vs RENO on the SAME loss (ssthresh 8, loss at cwnd 11, verified):
 Tahoe: 1,2,4,8,9,10,11 -> 1,2,4,5,6    (any loss -> cwnd=1, restart slow start)
 Reno:  1,2,4,8,9,10,11 -> 5,6,7,8,9    (3 dup ACKs -> cwnd=ssthresh, stay linear)
 RENO ON A TIMEOUT IS IDENTICAL TO TAHOE (verified). Reno does not "do less on
 loss" -- it DISTINGUISHES TWO KINDS of loss, because duplicate ACKs are
 EVIDENCE OF DELIVERY.
 FAST RETRANSMIT = resend early.  FAST RECOVERY = do not collapse to 1. Reno added
 the second.
 Tahoe -> Reno -> NewReno (multiple losses per window) -> SACK -> CUBIC -> BBR

CUBIC (the Linux default)
 W(t) = C(t-K)^3 + W_max,  K = cbrt(W_max(1-beta)/C),  C=0.4, beta=0.7
 verified: W(K) == W_max and W(0) == beta*W_max exactly
 shape: steep recovery -> FLAT near the old W_max (cautious probing) -> steep again
 t is REAL TIME, not RTTs -> RTT-FAIR. Reno is RTT-UNFAIR: a short-RTT flow gets
 its +1 ten times as often and crowds out a long-RTT one.
 why Reno fails on long fat pipes: 1 Gbps x 200 ms = 25 MB = ~17,000 segments;
 recovering 8,500 of them at +1/RTT takes 8,500 RTTs = 28 minutes.
BBR: ignores loss; estimates BOTTLENECK BANDWIDTH and MIN RTT and paces to their
 product. Loss-based control must FILL a buffer to see loss, which IS bufferbloat.
 Honest caveat: fairness vs loss-based flows is contested.

THROUGHPUT ~= W / RTT   -- the BDP from the sender's side
 65,535-byte window at 100 ms RTT = 5.2 Mbps, WHATEVER the link speed
 -> that single number is the whole case for WINDOW SCALING (RFC 1323, up to 1 GB),
    negotiated once in the SYN. A middlebox stripping SYN options = 1981 speeds.
 MATHIS: throughput ~ (MSS/RTT)(C/sqrt(p)) -> falls as 1/sqrt(p)
 1% loss costs 10x versus 0.01%. "Only 1% loss" is not reassuring.

RTO (Jacobson/Karels)
 SRTT   = 7/8 SRTT + 1/8 sample
 RTTVAR = 3/4 RTTVAR + 1/4 |SRTT - sample|
 RTO    = SRTT + 4 RTTVAR, floor 1 s
 VERIFIED with a 350 ms spike on a 100 ms path: SRTT moved 100 -> 131 but RTTVAR
 jumped 12.6 -> 72, widening the RTO 150 -> 419 ms. The 4*RTTVAR term makes the
 timeout tolerant of VARIANCE, not just the mean -- the original mean-only
 formula retransmitted constantly on variable paths. Quick to widen, SLOW to narrow.
 KARN: never sample RTT from a RETRANSMITTED segment (you cannot tell which copy
 the ACK is for, so the sample is systematically wrong). Instead DOUBLE the RTO
 on each timeout and hold it until a clean sample. 1,2,4,8,16,32,64 s.
 Same reasoning as Ethernet backoff: probing harder during overload makes it worse.

BUFFERBLOAT: loss-based control fills whatever buffer it finds, so big cheap
 buffers = hundreds of ms of standing queue at full throughput. Fixes: AQM at the
 router (CoDel/FQ-CoDel, drop early) and delay-based control at the sender (BBR).
ECN: the router MARKS a bit instead of dropping; the receiver echoes it in ECE;
 the sender halves cwnd. Congestion signalled WITHOUT LOSING DATA. Needs both
 endpoints and the routers -- a coordination problem, like IPv6.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "Flow control and congestion control both stop the sender sending too fast" | They protect **different things** for different reasons. Flow control protects the receiver and the receiver *tells you the number*; congestion control protects the network and **nobody knows the number** |
| "The congestion window is in the TCP header" | Only `rwnd` is in the header. `cwnd` exists **solely in the sender's memory** — which is why it has to be guessed |
| "The sender sends `min(rwnd, cwnd)`" — with no idea why | Correct, but the point is *why there are two*: one is told to you, one is inferred |
| "Slow start increases slowly" | It **doubles every RTT** — exponential. It is slow only compared with original TCP, which sent a whole window at once |
| "Slow start is linear and congestion avoidance exponential" | The exact reverse |
| "TCP halves `cwnd` on loss to be safe" | For **fairness**. Verified: AIMD converges two unequal flows from a 5.00 ratio to 2.00, while AIAD leaves the gap unchanged forever |
| "Reno backs off less than Tahoe" | Reno **distinguishes two kinds of loss**. On a timeout it is *identical* to Tahoe — verified. The difference applies only to triple duplicate ACKs |
| "Fast retransmit and fast recovery are the same" | Fast retransmit resends early; fast recovery avoids collapsing `cwnd` to 1. Tahoe has the first, Reno added the second |
| "Three duplicate ACKs is derived from the protocol" | It is a **tuned heuristic**: reordering routinely produces one or two, so three is where loss becomes likelier than reordering |
| "Duplicate ACKs mean the network is broken" | They mean the opposite — **segments are still arriving**, so the path works and one was dropped. That is why a proportionate response is appropriate |
| "A lost ACK causes a retransmission" | Cumulative ACKs mean a later ACK implies the earlier ones, so a single lost ACK is harmless |
| "SACK makes TCP faster in general" | It specifically helps when **several** segments are lost in one window — without it the sender learns about one hole per RTT |
| "CUBIC grows cubically with RTTs" | With **real time**, which is what makes it RTT-fair. Reno's per-RTT growth is why Reno is RTT-*unfair* |
| "CUBIC halves `cwnd` on loss" | `beta = 0.7`, so it drops to 70%, not 50% |
| "BBR is just a better loss-based algorithm" | It **ignores loss as a signal** and models bottleneck bandwidth and minimum RTT instead. That is a different idea, not a refinement |
| "Bufferbloat is caused by slow links" | By **large buffers plus loss-based congestion control**: the sender fills whatever buffer it finds before it sees loss, so throughput is fine and latency is terrible |
| "Throughput is limited by bandwidth" | Also by `W/RTT`. Verified: a 65,535-byte window at 100 ms RTT caps at **5.2 Mbps** on a link of any speed |
| "Window scaling is an optimisation" | Without it TCP cannot fill any long fat path. It is negotiated once in the SYN, and a middlebox stripping SYN options silently caps you at 1981 speeds |
| "1% packet loss means roughly 1% less throughput" | Throughput falls as `1/√p`, so 1% costs about **ten times** against 0.01% |
| "The RTO is the average RTT plus a margin" | `SRTT + 4·RTTVAR` — it is built on **variance**, not just the mean. Verified: a single 350 ms spike moved SRTT by 31% and the RTO by 180% |
| "RTT samples come from every ACK" | **Not from retransmitted segments** — Karn's algorithm — because you cannot tell which copy the ACK is for |
| "On a timeout, TCP retries at the same interval" | It **doubles** the RTO each time, capped around 64 s. That is why a connection to a dead host takes minutes to fail |
| "Nagle's algorithm is obsolete" | It is why SSH does not send a packet per keystroke. What *is* a problem is its interaction with delayed ACKs, which is why latency-sensitive code sets `TCP_NODELAY` |
| "Silly window syndrome is a receiver problem" | Both ends cause it independently, and there are two separate fixes: Clark's on the receiver, Nagle's on the sender |

---

## Interview Q&A bank

**Q1. Flow control vs congestion control?**
Flow control protects the receiver's buffer from a sender that is too fast, and the receiver advertises the exact permitted amount in every segment. Congestion control protects the network from all senders collectively, and no one can advertise the right value — it has to be inferred from loss or delay and adjusted continuously. The sender's limit is the minimum of the two windows.

**Q2. Where does each window live?**
`rwnd` is a field in the TCP header, set by the receiver. `cwnd` exists only in the sender's memory and is never transmitted — because it is the sender's own estimate of something nobody knows.

**Q3. What is a zero window, and how does TCP avoid deadlocking on it?**
The receiver advertises zero when its buffer is full, and the sender must stop. If the later window update is lost, both sides would wait forever — so the sender runs a persist timer and sends a one-byte window probe to force a fresh advertisement.

**Q4. What is silly window syndrome?**
A connection degrading into tiny segments, with far more header than data. The receiver causes it by advertising a one-byte window as its application dribbles data out; the sender causes it by writing one byte at a time. Clark's solution fixes the receiver by refusing to advertise less than an MSS or half the buffer; Nagle's algorithm fixes the sender by not sending a small segment while an earlier small one is unacknowledged.

**Q5. State Nagle's algorithm precisely.**
Send immediately if you have a full MSS to send, or if there is no unacknowledged data outstanding. Otherwise buffer the small write. That makes the first small write go out at once and subsequent ones coalesce until the ACK returns, so it self-tunes to the RTT.

**Q6. Why would you disable Nagle?**
Because it interacts badly with delayed ACKs. The receiver waits up to 200 ms hoping to piggyback its ACK, while Nagle waits for that ACK before sending the next small segment — so a protocol that writes a header then a body in two calls can stall 200 ms per message. `TCP_NODELAY` is the standard fix for latency-sensitive traffic.

**Q7. Why does TCP have congestion control at all?**
Because of congestion collapse. In 1986 the NSFNET backbone fell from 32 kbps to 40 bps: timeouts caused retransmissions, which added load, which caused more loss, which caused more retransmissions. Slow start and AIMD were introduced to break that feedback loop.

**Q8. Explain slow start.**
`cwnd` begins at one segment and **doubles every round trip** until it reaches `ssthresh`. It is exponential, and the name is relative to the original TCP, which sent an entire window immediately. Doubling is right because the correct window spans orders of magnitude and doubling finds the right one logarithmically.

**Q9. What happens at `ssthresh`?**
Growth switches to congestion avoidance: `+1 MSS per RTT`, which is linear. The idea is that `ssthresh` records roughly where trouble began last time, so beyond it caution is worth the slower growth.

**Q10. What is AIMD and why is it asymmetric?**
Additive increase, multiplicative decrease — probe up by one, back off by half. The asymmetry is what produces fairness: additive increase gives the same amount to every flow, narrowing relative gaps, while multiplicative decrease takes more in absolute terms from the larger flow. Verified: two flows starting at 20 and 4 converged from a 5.00 ratio to 2.00 in ten rounds, whereas under additive decrease the ratio never changed at all.

**Q11. Tahoe vs Reno?**
Tahoe treats any loss as severe: `ssthresh = cwnd/2`, `cwnd = 1`, and slow start again. Reno distinguishes the signals — on three duplicate ACKs it fast-retransmits and then enters fast recovery, setting `cwnd = ssthresh` and continuing linearly. On a timeout, Reno behaves exactly like Tahoe.

**Q12. Why is Reno's distinction justified?**
Because duplicate ACKs are **evidence of delivery**: later segments are arriving, so the path is working and a single segment was dropped. A timeout is evidence of nothing arriving at all, and merits a full restart.

**Q13. Fast retransmit vs fast recovery?**
Fast retransmit resends the missing segment on the third duplicate ACK instead of waiting for the timer. Fast recovery is what happens afterwards — halving `cwnd` and continuing in congestion avoidance rather than dropping to one. Tahoe has the first; Reno added the second.

**Q14. Trace `cwnd` for Reno: `ssthresh` 8, triple-dup loss when `cwnd` is 11.**
`1, 2, 4, 8` in slow start, then `9, 10, 11` in congestion avoidance. On the loss, `ssthresh` becomes 5 and `cwnd` becomes 5, then `6, 7, 8, 9` linearly. Tahoe on the same event would go to 1 and need four round trips just to get back to 5.

**Q15. Why did CUBIC replace Reno as the default?**
Reno's `+1 per RTT` cannot fill a long fat pipe — a 1 Gbps, 200 ms path needs about 17,000 segments, so recovering half of them one per RTT would take thousands of round trips. CUBIC grows as a cubic function of real time, which is both much faster and RTT-fair.

**Q16. What does CUBIC's curve shape achieve?**
Steep growth back toward the window that worked before, flattening as it approaches it so it probes cautiously around the known-good point, then steepening again to look for new capacity. Verified: starting from 70 after a loss at 100, it reaches 95 in two seconds, touches 100 exactly at `K`, and only then accelerates past it.

**Q17. Why is Reno RTT-unfair, and how does CUBIC fix it?**
Reno grows per round trip, so a flow with a 20 ms RTT increments ten times as often as one with 200 ms and takes a disproportionate share. CUBIC grows as a function of elapsed time, so both gain at the same rate per second.

**Q18. What is different about BBR?**
It does not use loss as the congestion signal. It estimates the bottleneck bandwidth and the minimum round-trip propagation delay and paces to their product, so it never needs to fill a buffer to discover the limit. That avoids bufferbloat, though its fairness against loss-based flows is debated.

**Q19. What is bufferbloat?**
Large, cheap router buffers combined with loss-based congestion control. The sender keeps increasing until it sees loss, which only happens once the buffer is full — so you get full throughput with hundreds of milliseconds of standing queue, and one bulk transfer makes interactive traffic on the same link unusable.

**Q20. What is ECN?**
A router approaching saturation marks a bit in the IP header instead of dropping the packet; the receiver echoes it in the TCP `ECE` flag; the sender reduces `cwnd` as if it had seen loss. Congestion is signalled without losing any data. It needs support at both endpoints and in the routers, which is why deployment has lagged.

**Q21. Why is throughput `window / RTT`?**
You can have one window of data outstanding and you learn its fate one round trip later, so your rate is limited to a window per RTT whatever the link speed. It is the bandwidth-delay product viewed from the sender.

**Q22. Why is window scaling necessary?**
Because the window field is 16 bits, capping at 65,535 bytes. Verified: on a 100 ms path that is 5.2 Mbps regardless of link capacity. Scaling shifts the field by up to 14 bits, allowing windows up to a gigabyte, and is negotiated once in the SYN.

**Q23. How does packet loss affect throughput?**
Roughly as `1/√p` by the Mathis formula, so a 1% loss rate costs about ten times the throughput of 0.01%. That is why a trace of loss on a long fat path is catastrophic rather than marginal.

**Q24. How does TCP choose its retransmission timeout?**
It maintains a smoothed RTT and a smoothed deviation, and sets the timeout to `SRTT + 4·RTTVAR`. Including variance is the crucial part: verified with one 350 ms spike on a 100 ms path, `SRTT` moved only to 131 while `RTTVAR` jumped from 13 to 72, widening the timeout from 150 ms to 419 ms.

**Q25. Why include variance rather than just the mean?**
Because a path that occasionally takes 350 ms needs a timeout above 350 ms even though its average is 100. The original mean-only estimator retransmitted constantly on variable paths, adding load exactly when the network was already struggling.

**Q26. What is Karn's algorithm?**
Never take an RTT sample from a retransmitted segment, because you cannot tell whether the ACK corresponds to the original or the retransmission, so the sample is systematically wrong either way. Instead, on each timeout double the RTO and keep that value until a clean sample arrives.

**Q27. Why does a connection to a dead host take minutes to fail?**
Exponential backoff: the RTO doubles after every timeout — 1, 2, 4, 8, 16, 32, 64 seconds — so a handful of retries consumes minutes. The reasoning is the same as Ethernet's backoff: probing harder during overload makes things worse.

---

## Practice

1. `ssthresh` is 16 and `cwnd` is 1. Give `cwnd` for the first 12 RTTs with no loss, and mark where the phase changes.
2. Same start, but a **timeout** occurs at RTT 7. Give the Tahoe trace through RTT 15.
3. Same start and timing, but **three duplicate ACKs** instead. Give the Reno trace and the new `ssthresh`.
4. At what RTT do the two traces from questions 2 and 3 first hold the same `cwnd` again?
5. Two flows share a 40-unit bottleneck, starting at 30 and 2. Run AIMD for eight rounds and report the ratio. Then do the same with additive decrease and compare.
6. A path is 500 Mbps with a 60 ms RTT. What window is needed to fill it? Can an unscaled TCP do it? What scale factor is needed?
7. Same path with 0.1% loss. Estimate the relative throughput penalty versus a lossless path.
8. RTT samples arrive as 60, 62, 58, 61, 200, 60, 59 ms. Compute `SRTT`, `RTTVAR` and the RTO after each, starting from `SRTT = 60`, `RTTVAR = 30`.
9. A segment is retransmitted and the ACK arrives 40 ms later. Why can this not be used as an RTT sample, and what does TCP do instead?
10. An application sends a 4-byte header then a 200-byte body as two `write()` calls, and the peer uses delayed ACKs. Explain the stall, and give two fixes.
11. A 10 Gbps data-centre link shows excellent throughput and 300 ms of latency under load. Name the phenomenon, explain the mechanism, and give two fixes from different layers.
12. Explain why "we'll just use UDP to avoid TCP's slow start" is usually wrong.

**Answers to 4, 8 and 12:**

> **4.** The Tahoe trace after the loss at `cwnd = 11` is `1, 2, 4, 5, 6, 7, 8, …` (new `ssthresh` = 5, so slow start doubles 1→2→4 and then clamps to 5 and goes linear). Reno's is `5, 6, 7, 8, 9, …`. Tahoe is at 5 on its **third** RTT after the loss, whereas Reno was at 5 immediately — so Tahoe is **three RTTs behind**, and the traces align in value only once Tahoe reaches 5 while Reno has already moved on to 8. On a window of 11 that is a modest cost; on a window of 10,000 the equivalent gap is enormous, which is the whole argument for fast recovery.
>
> **8.** With α = 1/8 and β = 1/4: after 60 → SRTT 60.0, RTTVAR 30.0, RTO 180. After 62 → SRTT 60.25, RTTVAR 23.0, RTO 152.25. After 58 → SRTT 59.97, RTTVAR 17.81, RTO 131.2. After 61 → SRTT 60.10, RTTVAR 13.62, RTO 114.6. After **200** → SRTT 77.59, RTTVAR 45.19, RTO 258.3. After 60 → SRTT 75.39, RTTVAR 38.29, RTO 228.6. After 59 → SRTT 73.34, RTTVAR 32.81, RTO 204.6. The pattern to notice is the one verified in §6.8: the spike barely shifts SRTT but **triples** RTTVAR, and the RTO stays elevated long afterwards.
>
> **12.** Because slow start is not overhead to be avoided — it is what stops congestion collapse, and a UDP application that skips it has to reinvent it or become the problem. The real costs are the handshake round trip and head-of-line blocking, and those have proper answers: TLS 1.3 and TCP Fast Open cut the setup, and QUIC over UDP removes head-of-line blocking **while still implementing congestion control**. The legitimate reasons to choose UDP are that a late packet is useless, or that you want to evolve the transport yourself — not that congestion control is inconvenient.

---

## Exit checklist

```
[ ] I know seq is a byte offset and ack is the NEXT byte expected
[ ] I can explain why cumulative ACKs make a lost ACK harmless
[ ] I can explain the weakness cumulative ACKs have, and what SACK adds
[ ] I know both retransmission triggers and what each one IMPLIES
[ ] I know why the threshold is THREE duplicate ACKs
[ ] I can distinguish fast retransmit from fast recovery
[ ] I can state the flow/congestion distinction in one sentence
[ ] I know rwnd is in the header and cwnd is only in the sender's memory
[ ] I know the sender is limited by min(rwnd, cwnd) and WHY there are two
[ ] I can explain the zero-window deadlock and the persist timer
[ ] I can explain silly window syndrome from BOTH sides
[ ] I can state Nagle's algorithm precisely
[ ] I can explain the Nagle + delayed-ACK interaction and TCP_NODELAY
[ ] I can tell the congestion-collapse story with the 1986 numbers
[ ] I know slow start is EXPONENTIAL and why it is called slow
[ ] I know congestion avoidance is +1 MSS per RTT
[ ] I can trace cwnd through any ssthresh and loss pattern
[ ] I can explain AIMD's asymmetry as a FAIRNESS argument
[ ] I can say why AIAD provably fails to converge
[ ] I can give the Tahoe and Reno traces for the same loss
[ ] I know Reno on a TIMEOUT is identical to Tahoe
[ ] I can explain why duplicate ACKs are evidence of DELIVERY
[ ] I can list the variants in order and say what each added
[ ] I can write CUBIC's equation and explain its curve shape
[ ] I know beta is 0.7, not 0.5
[ ] I can explain RTT fairness and why Reno lacks it
[ ] I can do the long-fat-pipe arithmetic that dooms Reno
[ ] I can explain what BBR measures instead of loss, and its honest caveat
[ ] I can explain bufferbloat as a consequence of loss-based control
[ ] I can explain ECN and why it is not widely deployed
[ ] I can derive throughput = W/RTT and connect it to the BDP
[ ] I know the 65,535-byte / 100 ms / 5.2 Mbps figure and what it proves
[ ] I know window scaling is negotiated in the SYN and what breaks it
[ ] I know throughput falls as 1/sqrt(p)
[ ] I can compute SRTT, RTTVAR and RTO from a sample sequence
[ ] I can explain why variance, not just the mean, is in the formula
[ ] I can state Karn's algorithm and BOTH of its halves
[ ] I can explain why a dead host takes minutes to fail
```

---

## Next

**Part 9: M7 — DNS.** The name system, traced for real against the root servers. Why names exist; the hierarchy of root, TLD and authoritative servers; **recursive versus iterative resolution, traced from the root down**; the resolver and the four caches; **every record type with a live lookup** — A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV, CAA; TTL and propagation; **why DNS uses UDP and when it falls back to TCP**; reverse lookups; round-robin and GeoDNS as crude load balancing; the caching bugs that bite in practice; and DoH, DoT and DNSSEC in brief.
