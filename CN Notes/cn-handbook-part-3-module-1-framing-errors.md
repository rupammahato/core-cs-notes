# Computer Networks Placement Handbook — Part 3
# Module 1: Framing and Errors

**Module 1 · 4 hours · Tier 1 · Requires: M0 (the four delays, and `a = Tp/Tt`). Links to DSA Part 4 (bit manipulation)**

---

## Why this module matters

This is the **first numericals centrepiece** and the densest marks in the subject. In a GATE-style paper, the data-link layer alone accounts for a large share of the 8–12 marks Computer Networks carries, and it arrives as four question types that never change:

- Compute the **utilization** of stop-and-wait or a sliding window
- Compute the **minimum window size** for 100% utilization
- Compute the **number of sequence-number bits** for Go-Back-N or Selective Repeat
- Do a **CRC division** or a **Hamming syndrome** by hand

In an interview, by contrast, this module gets maybe two questions — "what's the difference between Go-Back-N and Selective Repeat" and "how does CRC detect errors". So **be deliberate**: if a written test is coming, this is the highest-value module in the handbook. If only an interview is coming, learn the comparison tables and the one-line formulas and move on.

The good news is that all four question types are mechanical. There is nothing to understand creatively; there is a procedure, and this module gives you each one plus verified worked examples.

The organising principle:

> **The data link layer takes an unreliable stream of bits and turns it into a reliable sequence of frames across one hop. It needs exactly three mechanisms to do that: a way to tell where a frame starts and ends (framing), a way to tell whether it arrived intact (error detection), and a way to get a fresh copy when it did not (ARQ). Every formula in this module falls out of one number — `a = Tp/Tt`, the ratio of propagation to transmission delay — because that ratio is how much of the link sits idle while you wait.**

**How this module was verified.** Everything here is program output from a toolkit that was **self-tested against independently-known answers before being trusted**:

- my bit-level **CRC-32** reproduces `zlib.crc32` on **2,000 random messages, 0 mismatches**
- my **Internet checksum** reproduces **RFC 1071's own documented worked example** exactly (sum `0xddf2`, checksum `0x220d`), and agrees with a second independent implementation on 5,000 random buffers
- **Hamming** encode/decode was tested by injecting **27,024 single-bit errors** across every data word for `m = 4..11`: every syndrome pointed at the right bit and every correction was right
- the **ARQ formulas** were checked against an event-driven simulation that never uses them
- **bit stuffing and byte stuffing** round-tripped 20,000 random payloads each

Two of my own expected values turned out to be wrong, not the code, and §1.4 tells you which — because the one that was wrong is exactly the off-by-one the formula exists to catch.

---

## 1.1 Framing

The physical layer hands up a stream of bits with no punctuation. The data link layer has to decide where each frame begins and ends. Four approaches:

| Method | How | Problem |
|---|---|---|
| **Character count** | First field says how many bytes follow | If that one field is corrupted, every subsequent frame boundary is lost. Unusable alone |
| **Byte/character stuffing** | Delimit with a FLAG byte; escape any FLAG inside the payload | Byte-oriented only |
| **Bit stuffing** | Delimit with the bit pattern `01111110`; insert a `0` after five consecutive `1`s | The standard (HDLC, PPP) |
| **Physical-layer coding violations** | Use a signal pattern that cannot occur in data | Needs help from the medium |

### Bit stuffing — the rule and why it works

```
  FLAG = 01111110         (six 1s between two 0s)

  SENDER:   after every FIVE consecutive 1s in the PAYLOAD, insert a 0
  RECEIVER: after every FIVE consecutive 1s, delete the next bit (it must be the 0)
```

The flag contains six consecutive `1`s. Stuffing guarantees the payload can never contain six, so the flag pattern becomes **unambiguous** — it can only be a delimiter.

**Verified round trips:**

```
   01111110                   -> 011111010                      unstuffed OK  flag-free: True
   0111111001111110           -> 011111010011111010             unstuffed OK  flag-free: True
   1111111111                 -> 111110111110                   unstuffed OK  flag-free: True
   011011111111111111110010   -> 011011111011111011111010010    unstuffed OK  flag-free: True
   00000000                   -> 00000000                       unstuffed OK  flag-free: True
   11111                      -> 111110                         unstuffed OK  flag-free: True
   111110                     -> 1111100                        unstuffed OK  flag-free: True

   20,000 random payloads round-tripped, flag never appears: 0 failures
```

Three things in that output worth noticing. Row 1: the payload *was* the flag pattern and came out as `011111010` — one stuffed bit, and no longer confusable with a delimiter. Row 5: a payload with no runs of `1`s is **unchanged**, so stuffing costs nothing when the data does not need it. Rows 6 and 7: a `0` is stuffed after five `1`s **even when the next bit is already a `0`** (`11111` → `111110`, `111110` → `1111100`) — the rule is unconditional, because the receiver's rule has to be unconditional too.

**Worst-case overhead** is one bit per five, or **20%** — a payload of all `1`s. That is the figure an exam asks for.

### Byte stuffing

```
  FLAG = 0x7E   ESC = 0x7D
  SENDER:   replace FLAG with ESC, (FLAG xor 0x20); replace ESC with ESC, (ESC xor 0x20)
  RECEIVER: on ESC, drop it and xor the next byte with 0x20
```

Verified, including the example that shows both substitutions:

```
   20,000 random byte payloads: 0 failures (flag 0x7e never appears)
   example: b'A~}B' -> b'A}^}]B'
```

`A ~ } B` became `A }^ }] B`: the `~` (0x7E) became `7D 5E` and the `}` (0x7D) became `7D 5D`. **The escape character itself must be escaped** — that is the part people forget, and without it the receiver cannot tell a literal `0x7D` from an escape.

---

## 1.2 Error detection

Three schemes, in increasing strength. The question is always *what can this catch*, not *how is it computed* — though you need both.

### Parity

```
 even parity: append a bit so the total number of 1s is even
 1011001 -> 1011001|0   (four 1s, already even)
 1011011 -> 1011011|1   (five 1s, add one)
```

| | Catches | Misses |
|---|---|---|
| **Single parity bit** | **any odd** number of bit errors | **any even** number — including the common case of 2 |
| **2-D parity** (parity per row and per column) | all 1-, 2- and 3-bit errors; **corrects** single-bit errors | some 4-bit patterns (a rectangle of four flips) |

Single parity is 1 bit of overhead for 50% of error patterns missed. It survives in serial links and memory, not in networks.

### Internet checksum (RFC 1071)

Used by IP, TCP, UDP and ICMP. One's-complement sum of 16-bit words:

```
 1. treat the data as a sequence of 16-bit words (pad with a zero byte if odd)
 2. add them, and whenever the sum overflows 16 bits, ADD THE CARRY BACK IN
    (the "end-around carry" -- this is what makes it one's-complement arithmetic)
 3. the checksum is the ONE'S COMPLEMENT (bitwise NOT) of that sum
 4. the RECEIVER sums everything INCLUDING the checksum field;
    the result must be 0x0000
```

**Verified against RFC 1071's own example:**

```
  Internet checksum, RFC 1071 example 0001f203f4f5f6f7: 0x220d (RFC says 0x220d)
  two independent checksum implementations, 5000 random buffers: 0 mismatches
  a 20-byte IP header with its checksum inserted re-sums to 0x0000
                                      (the receiver's invariant is 0x0000)
```

That last line is the property to remember: **the receiver does not recompute and compare — it sums the whole thing including the checksum and expects zero.** It is cheaper and it is why the one's complement is taken.

| | Strength |
|---|---|
| Catches | all single-bit errors; most burst errors |
| **Misses** | **any error that preserves the sum** — swap two words, or flip bits in two places that cancel |
| Why it is used anyway | **Extremely cheap in software**: just adds. IP needs to recompute it at *every hop* because TTL changes, so cost matters more than strength |

That trade-off is the interview answer: **IP uses a weak checksum on purpose, because the strong check (CRC) is done by Ethernet at every hop anyway, and IP's own header checksum has to be recomputed by every router.** (IPv6 dropped the header checksum entirely for exactly this reason.)

### CRC — cyclic redundancy check

The real one. Treat the bit string as a polynomial over GF(2) and take the remainder modulo a fixed **generator polynomial**.

```
 SENDER
  1. let r = degree of the generator (number of generator bits - 1)
  2. append r zeros to the data
  3. divide by the generator using mod-2 arithmetic (XOR, no carries)
  4. the r-bit remainder is the CRC; transmit data + CRC

 RECEIVER
  1. divide the WHOLE received frame (data + CRC) by the same generator
  2. remainder zero -> accept.  Non-zero -> error.
```

### Worked by hand

Data `1101011011`, generator `10011` (`x⁴+x+1`, so `r = 4`):

```
                      1100001010
            ----------------------
  10011 ) 11010110110000
          10011
          -----
           10011
           10011
           -----
            00001 1011 0000      bring down
                10011
                -----
                 1110 0000
                 10011
                 -----
                  11010 00
                  10011
                  -----
                   10010 0
                   10011
                   -----
                    00010 -> remainder 1110

  transmitted frame = 1101011011 | 1110
```

The receiver divides `11010110111110` by `10011` and gets zero. Note mod-2 division is just **XOR where the leading bit is 1** — no borrows, no carries, which is why it is a handful of gates in hardware.

### Verified: my implementation matches the real thing

```
  CRC-32 bit-by-bit vs zlib.crc32, 2000 random messages: 0 mismatches
  textbook CRC: transmitted frame verifies, 2000 random (gen,data): 0 failures
```

The first line matters: a from-scratch bit-by-bit CRC-32 (init `0xFFFFFFFF`, reflected, final XOR) reproduces `zlib`'s — which is Ethernet's CRC-32 — on 2,000 random messages. So the implementation behind every number below is the real algorithm, not an approximation of it.

### Verified: exactly what CRC guarantees

This is the part worth real attention, because the guarantees are usually recited and rarely justified.

**1. All single-bit errors are caught** — every generator with at least two terms:

```
  CRC-4 (x^4+x+1)            single-bit errors missed: 0/18
  CRC-8 (x^8+x^2+x+1)        single-bit errors missed: 0/22
  CRC-12                     single-bit errors missed: 0/26
  CRC-16 (x^16+x^15+x^2+1)   single-bit errors missed: 0/30
```

**2. All burst errors of length ≤ r are caught, and longer ones slip through at exactly 2⁻ʳ.** Tested exhaustively with CRC-8 (`r = 8`) over every burst position and every bit pattern within the burst:

```
  CRC-8, bursts of length  2:      0/58     missed (ALL caught)
  CRC-8, bursts of length  3:      0/112    missed (ALL caught)
  CRC-8, bursts of length  4:      0/216    missed (ALL caught)
  CRC-8, bursts of length  5:      0/416    missed (ALL caught)
  CRC-8, bursts of length  6:      0/800    missed (ALL caught)
  CRC-8, bursts of length  7:      0/1536   missed (ALL caught)
  CRC-8, bursts of length  8:      0/2944   missed (ALL caught)
  CRC-8, bursts of length  9:     22/5632   missed (0.391% slip through)  <- burst > r
  CRC-8, bursts of length 10:     42/10752  missed (0.391% slip through)  <- burst > r
  CRC-8, bursts of length 11:     80/20480  missed (0.391% slip through)  <- burst > r
```

Look at the cliff. **Perfect up to length 8, and then exactly 0.391% missed from length 9 onward** — and `2⁻⁸ = 1/256 = 0.390625%`. The theoretical slip rate is reproduced to three decimal places by exhaustive enumeration, and it does not get worse as the burst gets longer. For Ethernet's CRC-32 the same bound gives `2⁻³² ≈ 1 in 4.3 billion`.

**3. All odd numbers of bit errors are caught if and only if the generator is divisible by `(x+1)`.** And the test for that is pleasingly simple: a polynomial is divisible by `(x+1)` exactly when it has an **even number of terms** (substitute `x = 1` and it must vanish).

```
  x^8+x^2+x+1      (4 terms)   div_by_(x+1)=True   odd-weight errors missed: 0/16664
  x^9+x^8+x^3^+x^2+1 (5 terms) div_by_(x+1)=False  odd-weight errors missed: 51/21700
```

Two generators, exhaustive testing over all 1-, 3- and 5-bit error patterns. The one with an even number of terms missed **nothing**; the one with an odd number missed 51. **That is why real generators are chosen to have `(x+1)` as a factor** — it buys all odd-weight errors for free. (CRC-32's standard polynomial does.)

### The summary table to memorise

| Error class | Caught? |
|---|---|
| Single-bit | **Always** (any generator with ≥ 2 terms) |
| Any odd number of bits | **Always, if the generator is divisible by `(x+1)`** — i.e. has an even number of terms |
| Burst of length ≤ r | **Always** |
| Burst of length r+1 | All but a fraction `2^-(r-1)` |
| Burst longer than r+1 | All but a fraction `2^-r` — verified at exactly 0.391% for `r = 8` |

**Common generators:** CRC-8, CRC-10, CRC-12, CRC-16 (`x¹⁶+x¹⁵+x²+1`), CRC-CCITT (`x¹⁶+x¹²+x⁵+1`), CRC-32 (Ethernet). The degree `r` is the number of CRC bits.

### Checksum vs CRC

| | Checksum | CRC |
|---|---|---|
| Arithmetic | One's-complement addition | Polynomial division mod 2 (XOR) |
| Cost in software | **Very cheap** | Moderate |
| Cost in hardware | Cheap | **Very cheap** (a shift register) |
| Burst detection | Weak | **Guaranteed up to `r` bits** |
| Misses | Any sum-preserving change (swapped words) | Only multiples of the generator |
| Used by | IP, TCP, UDP, ICMP | Ethernet, Wi-Fi, PPP, HDLC, disk, ZIP |
| Layer | Mostly 3 and 4 | Layer 2 |

---

## 1.3 Error correction: Hamming codes

Detection asks "is it wrong?"; correction asks "which bit is wrong?". Correction is called **FEC** — forward error correction — and it is used when retransmission is impossible or too expensive (satellite, storage, wireless).

### The distance rule

```
 Hamming distance d(a,b) = the number of positions in which a and b differ
 d_min = the minimum distance between any two valid codewords

 to DETECT up to s errors:   d_min >= s + 1
 to CORRECT up to t errors:  d_min >= 2t + 1
```

The intuition: to *detect* `s` errors, no `s` flips may turn one valid codeword into another. To *correct* them, the corrupted word must still be strictly closer to the original than to any other codeword — hence the factor of two.

### How many redundant bits?

```
 m data bits, r parity bits, n = m + r total.
 The syndrome must be able to name every single-bit error position (n of them)
 PLUS the "no error" case -> it needs n+1 distinct values -> 2^r >= m + r + 1
```

**Verified against the standard table:**

```
  Hamming r(m) vs the standard table: MATCH
   m:  4  7  8 11 12 16 26 27 32 57 64
   r:  3  4  4  4  5  5  5  6  6  6  7
```

Look at `m = 26` and `m = 27`. Both need checking:

```
  m=26 r=5: 2^r= 32 >= m+r+1= 32 ?  True       <- exactly fits
  m=27 r=5: 2^r= 32 >= m+r+1= 33 ?  False      <- one short
  m=27 r=6: 2^r= 64 >= m+r+1= 34 ?  True
```

**`m = 26` is the largest data size that fits in 5 parity bits, and 27 needs 6.** I had 5 written down for `m = 27` and the formula corrected me — which is exactly the off-by-one the inequality exists to prevent, and the reason to compute it rather than estimate it. (The famous `(7,4)` code is `m = 4, r = 3`; `(15,11)` is `m = 11, r = 4`; `(31,26)` is `m = 26, r = 5` — note that last one is the boundary case.)

### Placement and the syndrome

```
 parity bits go at positions 1, 2, 4, 8, 16, ...  (the POWERS OF TWO, 1-indexed)
 data bits fill every other position

 parity bit at position p checks every position whose index has bit p set:
   P1 (pos 1)  checks 1, 3, 5, 7, 9, 11, 13, 15, ...   (bit 0 set)
   P2 (pos 2)  checks 2, 3, 6, 7, 10, 11, 14, 15, ...  (bit 1 set)
   P4 (pos 4)  checks 4,5,6,7, 12,13,14,15, ...        (bit 2 set)
   P8 (pos 8)  checks 8..15, 24..31, ...               (bit 3 set)
```

**Why powers of two, and why this works** — the fact that makes Hamming codes feel inevitable rather than arbitrary:

> Every position index is a unique sum of powers of two. So position 11 = 8+2+1 is checked by exactly P8, P2 and P1. If bit 11 flips, exactly those three parity checks fail, and `8+2+1 = 11` — **the failing checks add up to the position of the error.** The syndrome is not a lookup; it is the binary representation of the answer.

A syndrome of **0** means no error (all checks pass).

### Worked example: `m = 4`, data `1011`

```
 r = 3 (2^3 = 8 >= 4+3+1 = 8), n = 7

 position:   1   2   3   4   5   6   7
 content:   P1  P2  d1  P4  d2  d3  d4
 data:                1       0   1   1

 P1 checks 1,3,5,7 -> P1 ^ 1 ^ 0 ^ 1 = 0 -> P1 = 0
 P2 checks 2,3,6,7 -> P2 ^ 1 ^ 1 ^ 1 = 0 -> P2 = 1
 P4 checks 4,5,6,7 -> P4 ^ 0 ^ 1 ^ 1 = 0 -> P4 = 0

 codeword = 0 1 1 0 0 1 1

 Now flip bit 5:  0 1 1 0 1 1 1
 P1 over 1,3,5,7 = 0^1^1^1 = 1  -> FAIL, contributes 1
 P2 over 2,3,6,7 = 1^1^1^1 = 0  -> pass
 P4 over 4,5,6,7 = 0^1^1^1 = 1  -> FAIL, contributes 4
 syndrome = 1 + 4 = 5  ->  bit 5 is wrong. Flip it back.
```

### Verified exhaustively

```
  Hamming: 27,024 single-bit errors injected (m=4..11) -> 0 wrong syndromes
                                                          or bad corrections
```

Every data word for `m = 4` through `m = 11`, every bit position in each codeword, one flip at a time: the syndrome pointed at the right position every single time, and the recovered data always equalled the original. Also checked: a clean codeword always has syndrome 0.

### The limits, stated honestly

Plain Hamming corrects **one** bit and that is all. Two flipped bits produce a syndrome that points confidently at a **third, innocent** position — so it does not just fail, it *makes things worse*. **SECDED** (single error correct, double error detect) adds one overall parity bit, so the combination "syndrome non-zero but overall parity even" means "two errors, do not try to correct". That is what ECC memory uses.

| | Error detection (CRC) | Error correction (Hamming) |
|---|---|---|
| Question answered | Is it wrong? | Which bit is wrong? |
| Overhead | Low (r bits, r small) | **Higher** (`2^r ≥ m+r+1`) |
| On failure | Ask for a retransmission | Fix it locally |
| Right when | Retransmission is cheap — **networks** | Retransmission is impossible or dear — satellite, storage, RAM, wireless |
| Strength per bit | **Much better** | Worse |

**The interview answer to "why don't networks use FEC everywhere?"** Because a retransmission is cheap on a terrestrial link and correction codes cost bandwidth on every single frame, including the overwhelming majority that arrive intact. You pay for correction always; you pay for retransmission only on loss. Links where that calculation flips — satellite, deep space, Wi-Fi, LTE — do use FEC.

---

## 1.4 ARQ: stop-and-wait, Go-Back-N, Selective Repeat

Detection tells you a frame is bad. **ARQ** (automatic repeat request) is how you get a good one: acknowledgements, timeouts and retransmission.

### Stop-and-wait

```
 sender                                    receiver
   |-- frame 0 --------------------------->|   Tt to put it on the wire
   |                                       |   Tp for it to arrive
   |<------------------------- ACK 0 ------|   Tp for the ack to come back
   |-- frame 1 --------------------------->|
   |                                       |

 one frame in flight, one ack per frame. Simple, and usually catastrophic.
```

```
   cycle time = Tt + 2*Tp   (plus Tack and 2*Tproc if the question gives them)
   utilization U = Tt / (Tt + 2*Tp) = 1 / (1 + 2a)        where a = Tp / Tt
```

### Sliding window: the fix

Let the sender have `N` frames outstanding instead of 1. Within one cycle time it sends `N` frames instead of 1, so:

```
   U = min( 1,  N * Tt / (Tt + 2*Tp) )  =  min( 1,  N / (1 + 2a) )

   for 100% utilization:   N >= 1 + 2a
```

Note what `N ≥ 1 + 2a` is really saying: the window must be large enough to keep sending for a whole round trip. **It is the bandwidth-delay product from M0, measured in frames.**

### Verified: the formula against a simulation

The formula was checked against an event-driven simulation that plays out send times and ack arrivals and **never uses the formula**:

```
   Tt(ms)  Tp(ms)        a    N   formula  simulated     diff
     1.00    0.50     0.50    1    0.5000     0.5000  0.00000
     1.00    5.00     5.00    1    0.0909     0.0909  0.00000
     1.00    5.00     5.00    4    0.3636     0.3635  0.00010
     1.00    5.00     5.00    8    0.7273     0.7263  0.00092
     1.00   20.00    20.00    1    0.0244     0.0244  0.00000
     1.00   20.00    20.00   16    0.3902     0.3897  0.00057
     0.10   10.00   100.00   16    0.0796     0.0796  0.00002
     8.00   10.00     1.25    2    0.5714     0.5713  0.00008
     1.00    0.05     0.05    1    0.9091     0.9091  0.00000
```

Agreement to four or five decimals wherever utilization is below 1. But the cases that *saturate* showed a small, consistent shortfall — the simulation reported 0.9975 where the formula said 1.0000. That is not an error in either, and the reason is worth more than the agreement:

```
  if the gap is the start-up transient, it must fall as 1/n and equal 2Tp/(n*Tt):
   n_frames  simulated       gap   predicted 2Tp/(n*Tt)
      1,000   0.990099  0.009901               0.010000
      4,000   0.997506  0.002494               0.002500
     16,000   0.999375  0.000625               0.000625
     64,000   0.999844  0.000156               0.000156
    256,000   0.999961  0.000039               0.000039
```

The gap matches `2Tp/(n·Tt)` to five decimal places and falls as `1/n`. **It is the pipeline-fill time** — the first round trip, during which no acknowledgements have arrived yet — amortised over `n` frames. So:

> **The textbook utilization formula is the steady-state limit.** It silently ignores the cost of filling the pipe, which is invisible for a long transfer and is exactly `2Tp` of dead time for a short one. For a 10-frame transfer on a long link the formula is simply wrong, and that is why a small HTTP response over a slow-start TCP connection behaves nothing like the formula predicts (M6).

### The worked numericals

```
  1 Kbit frame, 1 Mbps, 20 ms one-way
    Tt = 1000/1e+06 = 1.0000 ms      Tp = 20.000 ms      a = 20.000
    stop-and-wait   U = 1/(1+2a) = 2.439%
    window for 100% N >= 1+2a = 41.000 -> N = 41
    N = 4     U = 9.756%
    N = 7     U = 17.073%
    N = 8     U = 19.512%
    N = 41    U = 100.000%
    sequence bits: Go-Back-N needs 2^k >= N+1 = 42 -> k = 6
                   Selective Repeat 2^k >= 2N = 82 -> k = 7

  1 KB frame, 1 Mbps, 1 ms one-way
    Tt = 8.0000 ms      Tp = 1.000 ms      a = 0.125
    stop-and-wait   U = 80.000%
    window for 100% N >= 1.250 -> N = 2
    sequence bits: GBN 2^k >= 3 -> k = 2    SR 2^k >= 4 -> k = 2

  1 KB frame, 10 Mbps, 10 ms one-way
    Tt = 0.8000 ms      Tp = 10.000 ms      a = 12.500
    stop-and-wait   U = 3.846%
    window for 100% N >= 26.000 -> N = 26
    sequence bits: GBN 2^k >= 27 -> k = 5   SR 2^k >= 52 -> k = 6

  1500 B frame, 1 Gbps, 15 ms one-way
    Tt = 0.0120 ms      Tp = 15.000 ms      a = 1250.000
    stop-and-wait   U = 0.040%
    window for 100% N >= 2501.000 -> N = 2501
    sequence bits: GBN 2^k >= 2502 -> k = 12   SR 2^k >= 5002 -> k = 13
```

And in throughput terms, which is what the question sometimes asks for:

```
  1 Kbit frame, 1 Mbps, 20 ms one-way      S&W throughput =   0.0244 Mbps of 1 Mbps
  1 KB frame, 1 Mbps, 1 ms one-way         S&W throughput =   0.8000 Mbps of 1 Mbps
  1 KB frame, 10 Mbps, 10 ms one-way       S&W throughput =   0.3846 Mbps of 10 Mbps
  1500 B frame, 1 Gbps, 15 ms one-way      S&W throughput =   0.3998 Mbps of 1000 Mbps
```

**That last row is the one to remember.** A gigabit link, and stop-and-wait delivers **0.4 Mbps — 0.04% of capacity.** The link is not slow; the protocol is. A 1 Gbps intercontinental link run with stop-and-wait performs worse than a dial-up modem, and `a = 1250` is why.

### Go-Back-N and Selective Repeat

Both are sliding windows; they differ only in **what happens on loss**.

```
 GO-BACK-N: the receiver is simple. It accepts ONLY the next in-order frame
 and discards everything else. On a timeout the sender retransmits the lost
 frame AND EVERY FRAME AFTER IT.

   send:  0  1  2  3  4  5          frame 2 is lost
   recv:  0  1  X  (3,4,5 discarded -- out of order)
   ack:  A0 A1    (duplicate ACK1s)
   timeout on 2 -> resend 2 3 4 5

 SELECTIVE REPEAT: the receiver buffers out-of-order frames and acknowledges
 them individually. The sender retransmits ONLY the missing frame.

   send:  0  1  2  3  4  5          frame 2 is lost
   recv:  0  1  X  3  4  5          (3,4,5 BUFFERED)
   ack:  A0 A1    A3 A4 A5
   timeout on 2 -> resend 2 only, then deliver 2,3,4,5 in order
```

| | Stop-and-wait | Go-Back-N | Selective Repeat |
|---|---|---|---|
| Sender window | 1 | N | N |
| **Receiver window** | **1** | **1** | **N** |
| Out-of-order frames | n/a | **discarded** | **buffered** |
| ACK style | individual | **cumulative** | **individual (selective)** |
| On loss, retransmits | the frame | the frame **and all after it** | **only the lost frame** |
| Receiver buffering | none | **none** | **N frames** |
| Receiver complexity | trivial | **simple** | **complex** |
| Sorting at receiver | no | no | **yes** |
| Bandwidth on loss | — | **wasteful** | **efficient** |
| Sequence numbers | 1 bit | `2^k ≥ N+1` | `2^k ≥ 2N` |
| Timers | 1 | **1 (for the oldest)** | **one per frame** |
| Used by | simple links | — | TCP, approximately (with SACK) |

**The one-line distinction to give:** *"Go-Back-N keeps the receiver dumb and pays for it in bandwidth; Selective Repeat keeps the bandwidth and pays for it in receiver complexity — a buffer, per-frame timers, and twice the sequence-number space."*

### Why the sequence-number bounds are what they are

This is asked as a formula and understood by almost nobody. Both bounds come from the same scenario: **the sender's window is full, every ACK is lost, and the sender retransmits.** The receiver must be able to tell the retransmission from new data.

**Go-Back-N: `2^k ≥ N+1`.** Demonstrated by making it fail:

```
  window N = 4, sequence numbers mod 4  (BAD: modulus == N)
   sender transmits frames with seq [0, 1, 2, 3]
   every ACK is lost; sender times out and retransmits [0, 1, 2, 3]
   receiver accepted [0, 1, 2, 3], now expects seq 0
   RETRANSMITTED frame has seq 0 == expected 0
   -> receiver ACCEPTS A DUPLICATE AS NEW DATA. Silent corruption.

  window N = 4, sequence numbers mod 5  (OK: 2^k >= N+1)
   receiver accepted [0, 1, 2, 3], now expects seq 4
   retransmitted frame has seq 0 != expected 4
   -> receiver recognises it as a duplicate and discards it. Correct.

  window N = 7, sequence numbers mod 8  (OK)   -> correctly discarded
  window N = 8, sequence numbers mod 8  (BAD)  -> ACCEPTS A DUPLICATE
```

Read the first block carefully: no frame was lost, no frame was corrupted, and the receiver still ended up with **duplicate data accepted as new**. The failure is silent — nothing detects it — which is why the bound is not a suggestion. With `k` bits the modulus is `2^k`, so `N` can be at most `2^k − 1`, which is the familiar "with 3 bits, the window can be 7".

**Selective Repeat: `2^k ≥ 2N`.** The bound is twice as large, and `N+1` is **not** enough:

```
  window N = 4, mod 5  (BAD: 2^k < 2N)
   sender sends [0, 1, 2, 3]; all ACKs lost; sender retransmits [0, 1, 2, 3]
   receiver accepted all N, its window has moved to [4, 0, 1, 2]
   OVERLAP [0, 1, 2]: a retransmitted old frame falls inside the new
   receive window -> accepted as new data. Silent corruption.

  window N = 4, mod 8  (OK: 2^k >= 2N)
   receiver's window has moved to [4, 5, 6, 7]
   no overlap -> every retransmission is correctly seen as a duplicate.
```

**The reason for the factor of two:** in Go-Back-N the receiver accepts exactly one sequence number, so it only needs the retransmission to differ from that one. In Selective Repeat the receiver accepts a *window* of `N` numbers, so the old window and the new window must not overlap at all — and two non-overlapping windows of size `N` need `2N` distinct numbers. That is the entire derivation, and it is worth saying rather than quoting.

### Piggybacking (Tier 3)

On a bidirectional link, carry the acknowledgement inside the next data frame going the other way instead of sending a separate ACK frame. It saves a frame's worth of overhead; the cost is a delay while the receiver waits for data to send, so implementations use a short timer and give up. TCP does this, which is why a `tcpdump` of an interactive session shows almost no pure ACKs.

---

## Must remember

```
FRAMING
 bit stuffing: FLAG 01111110; sender inserts a 0 after five 1s, receiver deletes it
   unconditional -- 11111 -> 111110 even though a 0 follows anyway
   worst case overhead 20% (one bit in five)
 byte stuffing: FLAG 0x7E, ESC 0x7D; escape both, xor the escaped byte with 0x20
   THE ESCAPE CHARACTER MUST ITSELF BE ESCAPED

ERROR DETECTION
 parity:        catches any ODD number of errors, misses ALL EVEN ones
 2-D parity:    catches 1,2,3-bit errors; CORRECTS single-bit; misses some 4-bit
 Internet checksum (IP/TCP/UDP/ICMP): one's-complement sum of 16-bit words with
   END-AROUND CARRY, then complement. RECEIVER SUMS EVERYTHING AND EXPECTS 0x0000.
   weak (misses any sum-preserving change) but very cheap -- and IP must recompute
   it at EVERY hop because TTL changes. IPv6 dropped it entirely.
 CRC: append r zeros, divide mod 2 (XOR) by the generator, remainder = CRC.
   receiver divides the whole frame; zero remainder = accept.
   GUARANTEES (all verified exhaustively):
     single-bit             ALWAYS caught
     any ODD number of bits ALWAYS caught IFF generator divisible by (x+1)
                            <=> the generator has an EVEN NUMBER OF TERMS
     burst <= r             ALWAYS caught
     burst > r              missed with probability 2^-r  (measured 0.391% for r=8)
   CRC-32 (Ethernet) -> 2^-32 ~ 1 in 4.3 billion

ERROR CORRECTION
 d_min >= s+1    to DETECT s errors
 d_min >= 2t+1   to CORRECT t errors
 Hamming: 2^r >= m + r + 1          (m=26 -> r=5 EXACTLY fits; m=27 -> r=6)
 parity bits at positions 1,2,4,8,... (powers of two, 1-indexed)
 parity at position p checks every position whose index has bit p set
 THE SYNDROME IS THE POSITION: the failing checks SUM to the index of the bad bit
 syndrome 0 = no error. Corrects ONE bit; two errors make it corrupt a third bit.
 SECDED adds an overall parity bit to detect (not correct) double errors.
 networks prefer DETECTION + retransmission because correction costs bandwidth on
 every frame including the good ones; satellite/storage/wireless prefer FEC.

ARQ  -- everything is in terms of  a = Tp / Tt
 stop-and-wait  U = Tt/(Tt+2Tp) = 1/(1+2a)
 sliding window U = min(1, N/(1+2a))
 full use needs N >= 1 + 2a        (= the bandwidth-delay product, in frames)
 throughput = U x bandwidth
 with ack time and processing: U = Tt/(Tt + 2Tp + Tack + 2Tproc)
 THE FORMULA IS THE STEADY-STATE LIMIT: it ignores the 2Tp pipeline fill, which
 is 2Tp/(n*Tt) of the total -- verified, and it matters for SHORT transfers.

                stop-and-wait   Go-Back-N        Selective Repeat
 sender window        1             N                  N
 RECEIVER window      1             1                  N
 out of order         --        DISCARDED            BUFFERED
 ACKs            individual    CUMULATIVE          INDIVIDUAL
 on loss resend    the frame   frame + ALL AFTER   ONLY the lost one
 timers               1         1 (oldest)         ONE PER FRAME
 seq numbers       1 bit       2^k >= N+1          2^k >= 2N

 the N+1 bound: with all ACKs lost, the retransmitted frame must differ from the
   ONE number the receiver now expects
 the 2N bound: the receiver accepts a WHOLE WINDOW, so old and new windows must
   not overlap -- two disjoint windows of size N need 2N numbers
 both failures are SILENT: a duplicate is accepted as new data (verified)
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "Bit stuffing inserts a 0 after six 1s" | After **five**. The flag has six, so five-plus-stuffed-zero guarantees the payload can never produce six |
| "You only stuff when the next bit is a 1" | Unconditional. Verified: `11111` → `111110` and `111110` → `1111100`, because the receiver's rule is unconditional too |
| "Byte stuffing just escapes the flag" | It must escape **the escape character as well**, or the receiver cannot tell a literal `0x7D` from an escape |
| "A parity bit catches any error" | Only an **odd** number of flips. It misses every even number, including the common two-bit case |
| "The receiver recomputes the checksum and compares" | It sums the data **including the checksum field** and expects `0x0000`. That is cheaper and is why the one's complement is taken |
| "IP uses a weak checksum because it's old" | Because it must be **recomputed at every hop** (TTL changes), and Ethernet's CRC-32 already covers each link. IPv6 dropped it for the same reason |
| "CRC can correct errors" | CRC **detects**. Correction is Hamming/FEC |
| "CRC catches all errors" | It misses any error pattern that is a multiple of the generator. Verified: bursts longer than `r` slip through at exactly `2^-r` |
| "CRC catches all bursts" | All bursts of length **≤ r**. Verified perfect to length 8 for `r = 8`, then 0.391% missed |
| "Any generator catches all odd-weight errors" | Only one divisible by `(x+1)` — equivalently, with an **even number of terms**. Verified: 0 missed vs 51 missed for two generators tested exhaustively |
| "Hamming distance is the number of 1s" | It is the number of **positions where two codewords differ**. The number of 1s is the *weight* |
| "`d_min ≥ t+1` corrects t errors" | That **detects** t. Correcting needs `d_min ≥ 2t+1` |
| "For `m = 27`, 5 parity bits are enough" | `2^5 = 32 < 27+5+1 = 33`, so you need **6**. `m = 26` is the last one that fits in 5 — verified |
| "Parity bits go at the end" | At positions **1, 2, 4, 8, …** That placement is what makes the failing checks sum to the error position |
| "Hamming can correct any number of errors" | **One**. With two errors it points at a third, innocent bit and corrupts it. SECDED detects the double instead |
| "Networks should use FEC, it avoids retransmission" | FEC costs bandwidth on **every** frame including the good ones. Retransmission costs only on loss, which is why terrestrial links detect and resend |
| "Stop-and-wait is just a bit slower" | Verified: **0.04% of a 1 Gbps link** at `a = 1250`. It is not slower, it is unusable |
| "Utilization depends on bandwidth" | It depends on `a = Tp/Tt` alone. Two completely different links with the same `a` have identical utilization — verified |
| "The utilization formula is exact" | It is the **steady-state limit** and ignores the `2Tp` pipeline fill, which is `2Tp/(n·Tt)` of the total — verified to five decimals |
| "Go-Back-N buffers out-of-order frames" | It **discards** them. Buffering is what makes Selective Repeat complex |
| "Selective Repeat needs `N+1` sequence numbers" | It needs **`2N`**. Verified: with `N = 4` and modulus 5, the old and new receive windows overlap on `[0,1,2]` and duplicates are accepted as new data |
| "With 3 sequence bits the window can be 8" | **7** for Go-Back-N (`2^k ≥ N+1`) and **4** for Selective Repeat (`2^k ≥ 2N`) |
| "If sequence numbers wrap wrongly you get an error" | You get **silent corruption** — a duplicate accepted as new data, with nothing to detect it |

---

## Interview Q&A bank

**Q1. What problems does the data link layer solve?**
Three: framing (where does a frame start and end), error detection (did it arrive intact), and error control via ARQ (get a fresh copy if not). Plus medium access on a shared link, which is M2.

**Q2. What is bit stuffing and why five ones?**
The frame delimiter is `01111110`, which contains six consecutive ones. The sender inserts a zero after every five consecutive ones in the payload, so the payload can never contain six, making the flag unambiguous. The receiver deletes the bit after any five ones.

**Q3. What is the worst-case overhead of bit stuffing?**
One bit per five, so 20%, on a payload of all ones.

**Q4. How does the Internet checksum work, and how does the receiver verify it?**
One's-complement sum of the 16-bit words with the carry added back in, then complemented. The receiver sums everything *including* the checksum field and expects zero — it does not recompute and compare.

**Q5. Why does IP use such a weak checksum?**
Because every router has to recompute it, since the TTL changes at each hop, so cost dominates. The strong check — Ethernet's CRC-32 — is already done on each link. IPv6 removed the header checksum altogether for the same reason.

**Q6. How does CRC work?**
Append `r` zeros to the data, divide by the generator polynomial using mod-2 arithmetic, and transmit the data plus the `r`-bit remainder. The receiver divides the whole received frame by the same generator and accepts only if the remainder is zero.

**Q7. What errors does CRC guarantee to catch?**
All single-bit errors; all bursts of length up to `r`; and all odd numbers of bit errors provided the generator is divisible by `(x+1)`. Longer bursts slip through with probability `2^-r` — verified at exactly 0.391% for an 8-bit CRC, and about one in 4.3 billion for Ethernet's CRC-32.

**Q8. How do you know whether a generator catches all odd-weight errors?**
It must be divisible by `(x+1)`, which is true exactly when the generator has an even number of terms. Verified: a 4-term generator missed none of 16,664 odd-weight error patterns, while a 5-term one missed 51.

**Q9. Checksum vs CRC?**
A checksum is a one's-complement addition — very cheap in software, weak, and blind to anything that preserves the sum. A CRC is polynomial division — very cheap in hardware, with guaranteed burst detection up to its degree. Layers 3 and 4 use checksums, layer 2 uses CRC.

**Q10. Detection vs correction — when would you use each?**
Detect and retransmit when a retransmission is cheap, which is every terrestrial network: correction codes cost bandwidth on every frame including the good ones. Correct locally when retransmission is impossible or expensive — satellite, deep space, storage, RAM, wireless.

**Q11. How many redundant bits does a Hamming code need?**
The smallest `r` with `2^r ≥ m + r + 1`, because the syndrome must name every single-bit position plus the no-error case. For 26 data bits that is exactly 5; for 27 it is 6.

**Q12. Where do the parity bits go, and why there?**
At positions 1, 2, 4, 8 and so on. Parity bit at position `p` checks every position whose index has bit `p` set, so if a bit flips, the failing checks sum to that bit's position — the syndrome *is* the answer in binary.

**Q13. What does a syndrome of zero mean, and what happens with two errors?**
Zero means no error. With two errors the syndrome is non-zero but points at a third, innocent bit, so plain Hamming actively corrupts the data. SECDED adds an overall parity bit so a double error is detected rather than mis-corrected.

**Q14. State the distance rules.**
To detect `s` errors you need a minimum distance of `s+1`; to correct `t` you need `2t+1`, because the corrupted word must still be strictly nearer the original than any other codeword.

**Q15. Give the stop-and-wait utilization formula and explain it.**
`U = Tt/(Tt + 2Tp) = 1/(1+2a)` where `a = Tp/Tt`. The sender is useful only while transmitting and idle for a whole round trip after each frame, so the useful fraction is transmission time over cycle time.

**Q16. A 1 Gbps link, 15 ms one-way, 1500-byte frames. What does stop-and-wait achieve?**
`Tt = 12 µs`, `Tp = 15 ms`, so `a = 1250` and `U = 1/2501 ≈ 0.04%` — about 0.4 Mbps out of 1000. The link is fine; the protocol is unusable.

**Q17. What window size gives full utilization, and what is that quantity really?**
`N ≥ 1 + 2a`. It is the bandwidth-delay product expressed in frames: enough frames to keep transmitting for one whole round trip.

**Q18. Is the utilization formula exact?**
It is the steady-state limit. It ignores the pipeline-fill time of one round trip, which is `2Tp/(n·Tt)` of the total — negligible for a long transfer and significant for a short one. Verified against a simulation, where the gap matched that expression to five decimals.

**Q19. Go-Back-N vs Selective Repeat?**
Both slide a window of `N`. Go-Back-N has a receive window of 1, discards out-of-order frames, uses cumulative ACKs and one timer, and on loss retransmits the lost frame and everything after it. Selective Repeat buffers out-of-order frames, acknowledges individually, needs a timer per frame, and retransmits only what was lost. Go-Back-N trades bandwidth for a simple receiver.

**Q20. Why does Go-Back-N need `N+1` sequence numbers?**
If the window is full and every ACK is lost, the sender retransmits the whole window. The receiver has advanced to expecting the frame after the window, so the retransmitted frames must all differ from that number — which fails exactly when the modulus equals `N`. Verified: with `N = 4` mod 4, the receiver accepts a duplicate as new data, silently.

**Q21. Why does Selective Repeat need `2N`?**
Because its receiver accepts a whole window of `N` numbers rather than one. After accepting `N` frames the receive window has moved on by `N`, and the old and new windows must not overlap — two disjoint windows of size `N` need `2N` distinct numbers. Verified: `N = 4` with modulus 5 overlaps on `[0,1,2]` and accepts duplicates.

**Q22. What happens if you get the sequence-number space wrong?**
Silent data corruption: a retransmitted duplicate is accepted as new data and nothing detects it. It is not a performance bug, it is a correctness bug.

**Q23. What is piggybacking?**
Carrying an acknowledgement inside the next data frame travelling the other way instead of sending a separate ACK frame. It saves overhead on bidirectional traffic, at the cost of a short wait, so implementations bound that wait with a timer.

---

## Practice

1. Bit-stuff `0111111011111110` and then unstuff your answer to check it.
2. Byte-stuff `41 7E 7D 7E 42` with `FLAG = 0x7E`, `ESC = 0x7D`.
3. Data `110101`, generator `1011`. Compute the CRC and the transmitted frame, then verify it at the receiver.
4. For the same generator, what burst length is guaranteed to be caught? What fraction of longer bursts slips through?
5. A generator has terms `x⁵ + x² + 1`. Does it catch all odd-weight errors? Justify your answer without dividing anything.
6. How many parity bits for `m = 12`? For `m = 26`? For `m = 27`? Show the inequality each time.
7. Encode the data `1101` as a (7,4) Hamming codeword. Then flip bit 6 and show the syndrome locating it.
8. A received (7,4) codeword is `1001101`. Is it valid? If not, which bit is wrong and what was the data?
9. A link is 2 Mbps with 10 ms one-way delay and 2000-bit frames. Compute `a`, the stop-and-wait utilization, the window for 100% use, and the sequence bits for both GBN and SR.
10. Same link. If the sender uses a window of 8, what utilization and what throughput does it achieve?
11. A satellite link is 1 Mbps with 270 ms one-way delay and 1000-bit frames. Repeat question 9 and comment on the window size you get.
12. With 4 sequence-number bits, what is the largest usable window for Go-Back-N? For Selective Repeat?
13. Explain why a 10-frame transfer on the link in question 11 will not achieve the utilization your formula predicts.

**Answers to 5, 9 and 13:**

> **5.** `x⁵ + x² + 1` has **three** terms — an odd number — so substituting `x = 1` gives `1+1+1 = 1 ≠ 0`, meaning it is **not** divisible by `(x+1)`. So it does **not** catch all odd-weight errors. The whole test is counting terms, which is why no division is needed.
>
> **9.** `Tt = 2000/2e6 = 1 ms`, `Tp = 10 ms`, so **`a = 10`**. Stop-and-wait: `U = 1/(1+20) = 1/21 ≈ **4.76%**`. Window for full use: `N ≥ 1+2a = 21`, so **`N = 21`**. Sequence bits: GBN needs `2^k ≥ 22` → **`k = 5`**; SR needs `2^k ≥ 42` → **`k = 6`**.
>
> **13.** Because the formula is the steady-state limit and ignores the pipeline fill. On that link `2Tp = 540 ms` while 10 frames take only `10 × 1 ms = 10 ms` of transmission, so the fill time dominates completely: the transfer takes about `540 + 10 = 550 ms`, giving roughly `10/550 ≈ 1.8%` utilization rather than the `min(1, N/(1+2a))` the formula would give for a large `N`. Verified in general: the gap is exactly `2Tp/(n·Tt)`.

---

## Exit checklist

```
[ ] I can bit-stuff and unstuff, and I know the rule is unconditional
[ ] I know the worst-case bit-stuffing overhead is 20%
[ ] I can byte-stuff, including escaping the escape character
[ ] I know parity catches odd errors and misses ALL even ones
[ ] I can compute an Internet checksum with the end-around carry
[ ] I know the receiver sums INCLUDING the checksum and expects 0x0000
[ ] I can say why IP's checksum is deliberately weak, and why IPv6 dropped it
[ ] I can do a CRC division by hand and verify it at the receiver
[ ] I can state all four CRC guarantees, including the 2^-r slip rate
[ ] I can decide whether a generator catches odd-weight errors BY COUNTING TERMS
[ ] I can compare checksum and CRC on cost, strength and layer
[ ] I know d_min >= s+1 to detect and d_min >= 2t+1 to correct
[ ] I can compute Hamming r from 2^r >= m+r+1, and I know m=26 is the boundary for r=5
[ ] I know parity bits sit at powers of two, and WHY that makes the syndrome the position
[ ] I can encode a (7,4) codeword and locate an injected error by syndrome
[ ] I know plain Hamming corrupts a third bit when two errors occur, and what SECDED adds
[ ] I can argue why networks detect-and-retransmit instead of using FEC
[ ] I can derive U = 1/(1+2a) rather than recite it
[ ] I can compute U, N and throughput for any (frame size, rate, delay)
[ ] I know N >= 1+2a is the bandwidth-delay product in frames
[ ] I know the formula is a steady-state limit that ignores 2Tp of pipeline fill
[ ] I can fill in the stop-and-wait / GBN / SR comparison table from memory
[ ] I know GBN discards out-of-order frames and SR buffers them
[ ] I can DERIVE 2^k >= N+1 and 2^k >= 2N, not just quote them
[ ] I know getting the sequence space wrong causes SILENT corruption
[ ] I can say what piggybacking is and what it costs
```

---

## Next

**Part 4: M2 — Medium Access and the LAN.** What happens when many stations share one medium: **ALOHA and slotted ALOHA**, with their `1/2e` and `1/e` efficiencies verified against a simulation; **CSMA, CSMA/CD** and the computation of **why Ethernet has a 64-byte minimum frame** — including the honest gap between the textbook `2dB/v` formula and the standard's actual 512-bit figure; **CSMA/CA** and why Wi-Fi cannot detect collisions at all; the **Ethernet frame field by field**, built and parsed; MAC address structure and the unicast/multicast bit; **switch learning traced frame by frame**; and **ARP**, decoded against this machine's real ARP table — where the gateway turns out to be a VRRP virtual MAC and the multicast mappings can be checked arithmetically.
