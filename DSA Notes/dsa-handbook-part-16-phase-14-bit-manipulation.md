# DSA Placement Handbook (C++) — Part 16
# Phase 14: Bit Manipulation

**Module 14 · 4–5 hours · Tier 2 · Requires: Module 0**

---

## Why this is a side module

Bit manipulation is small, self-contained, and depends on almost nothing. The roadmap flagged it as a parallel module you can slot in any time after complexity analysis, and if you are reading it now it is because Module 13's bitmask DP needed it.

It earns Tier 2 status on cost-effectiveness rather than depth: **four hours buys you a whole category of OA questions** plus the machinery behind subset generation and bitmask DP. The questions themselves are usually easy-to-medium and formulaic, which is exactly why they appear in timed rounds.

What it is **not**: a source of hard interview questions. Outside of Single Number II and the XOR-trie problem, bit manipulation rarely carries a full interview. Learn the toolkit, learn the XOR properties, keep the cheat sheet, move on.

---

## 14.1 Binary and two's complement

### Representation

```
  13 in binary:   0000 0000 0000 0000 0000 0000 0000 1101
                                                    ^^^^
  bit position:                                     3210
  value:                                    8 + 4 + 0 + 1 = 13
```

Bit `i` has place value `2^i`. Bit 0 is the least significant (rightmost).

### Negative numbers: two's complement

C++ stores negatives as two's complement: **`-x` is `~x + 1`**.

```
   5  =  0000 ... 0101
  ~5  =  1111 ... 1010
  +1  =  1111 ... 1011  =  -5
```

Consequences worth knowing:

| Fact | Why it matters |
|---|---|
| `-1` is all ones | `~0 == -1` |
| The top bit is the sign bit | `x < 0` ⟺ bit 31 set (for `int`) |
| `INT_MIN` has no positive counterpart | `-INT_MIN` overflows |
| `x & -x` isolates the lowest set bit | Works *because* of two's complement |

### The widths

| Type | Bits | Range |
|---|---|---|
| `int` | 32 | −2³¹ to 2³¹−1 |
| `unsigned int` | 32 | 0 to 2³²−1 |
| `long long` | 64 | −2⁶³ to 2⁶³−1 |

---

## 14.2 The operators

| Op | Name | Rule | Example (5 = 101, 3 = 011) |
|---|---|---|---|
| `&` | AND | 1 if **both** are 1 | `5 & 3 = 001 = 1` |
| `\|` | OR | 1 if **either** is 1 | `5 \| 3 = 111 = 7` |
| `^` | XOR | 1 if they **differ** | `5 ^ 3 = 110 = 6` |
| `~` | NOT | flips every bit | `~5 = -6` |
| `<<` | Left shift | `x << k` = `x · 2^k` | `5 << 1 = 10` |
| `>>` | Right shift | `x >> k` = `x / 2^k` | `5 >> 1 = 2` |

### What each is *for*

| Operator | Use it to |
|---|---|
| `&` | **Test** or **mask** bits: is this bit set? keep only these bits |
| `\|` | **Set** bits: turn this on, combine two masks |
| `^` | **Toggle** bits, and **cancel** pairs (Section 14.4) |
| `~` | Build an inverted mask, usually combined with `&` |
| `<<` | Build a single-bit mask (`1 << i`), multiply by a power of two |
| `>>` | Read bit `i` (`x >> i`), divide by a power of two |

---

## 14.3 The bit toolkit

**Memorise these five lines.** They are the entire working vocabulary.

```cpp
(x >> i) & 1          // CHECK  bit i  (gives 0 or 1)
x |  (1 << i)         // SET    bit i
x & ~(1 << i)         // CLEAR  bit i
x ^  (1 << i)         // TOGGLE bit i
x & (x - 1)           // clear the LOWEST set bit
```

Reading them:

**`(x >> i) & 1`** — shift bit `i` down to position 0, then mask off everything else. An equivalent form is `x & (1 << i)`, but that returns `2^i` rather than `1`, which is fine for a truth test and wrong if you want the literal bit value.

**`x | (1 << i)`** — OR with a mask that has only bit `i` set. Every other bit is OR'd with 0 and unchanged.

**`x & ~(1 << i)`** — `~(1 << i)` is all ones except bit `i`. ANDing keeps everything and zeroes that one position.

**`x ^ (1 << i)`** — XOR with 1 flips; XOR with 0 preserves. So only bit `i` changes.

**`x & (x - 1)`** — subtracting 1 flips the lowest set bit to 0 and turns every bit below it into 1. ANDing then clears exactly that bit. This one line is behind Brian Kernighan's bit count and the power-of-two test.

### Worked: why `x & (x-1)` clears the lowest set bit

```
x     = 1011 0100
x - 1 = 1011 0011        (lowest 1 became 0; everything below became 1)
x&(x-1)=1011 0000        (that bit cleared, rest untouched)
```

### The other essential

```cpp
x & (-x)              // ISOLATE the lowest set bit
```

```
x    = 1011 0100
-x   = 0100 1100        (two's complement: ~x + 1)
x&-x = 0000 0100        (only the lowest set bit survives)
```

This is used in Fenwick trees and in splitting a set into two groups by a distinguishing bit (Section 14.5).

### Must remember

1. The five-line toolkit. Write it from memory.
2. `x & (x-1)` clears the lowest set bit; `x & -x` isolates it.
3. `(x >> i) & 1` gives 0 or 1; `x & (1 << i)` gives 0 or `2^i`.
4. Shifting is multiplication and division by powers of two, with no rounding issues for non-negative values.

---

## 14.4 XOR and its properties

**The most useful operator in this module**, because its algebraic properties produce genuinely non-obvious solutions.

### The properties

| Property | Statement |
|---|---|
| Identity | `x ^ 0 = x` |
| Self-inverse | `x ^ x = 0` |
| Commutative | `a ^ b = b ^ a` |
| Associative | `(a ^ b) ^ c = a ^ (b ^ c)` |
| Cancellation | `a ^ b ^ b = a` |

**The consequence that matters:** in a XOR of many values, **pairs cancel out and order does not matter.** Anything appearing an even number of times vanishes; anything appearing an odd number of times survives.

### Single Number (LC 136)

*Every element appears twice except one. Find it.*

```cpp
int singleNumber(const vector<int>& a) {
    int res = 0;
    for (int x : a) res ^= x;
    return res;
}
```

Every duplicated value XORs with itself to 0, leaving only the unique one. O(n) time, **O(1) space** — which is the point; a hash map solves it in O(n) space and the interviewer will ask you to do better.

### Missing Number (LC 268)

*An array contains `n` distinct numbers from `0..n`. One is missing.*

```cpp
int missingNumber(const vector<int>& a) {
    int res = a.size();                        // start with n
    for (int i = 0; i < (int)a.size(); i++)
        res ^= i ^ a[i];
    return res;
}
```

XOR together every index `0..n` and every array value. Each present number appears twice (once as an index, once as a value) and cancels; the missing one appears only as an index and survives.

**The arithmetic alternative** — `n(n+1)/2 − sum` — is equally valid and shorter, but can overflow `int` for large `n`. XOR never overflows. Mention both.

### Single Number III (LC 260): two unique numbers

*Every element appears twice except **two**. Find both.*

XOR of everything gives `p ^ q`, which is non-zero but does not separate them. The trick: **any set bit in `p ^ q` is a position where `p` and `q` differ.** Pick one, and partition the array by it.

```cpp
vector<int> singleNumber(const vector<int>& a) {
    long long xorAll = 0;
    for (int x : a) xorAll ^= x;

    long long diffBit = xorAll & (-xorAll);    // lowest bit where p and q differ

    int p = 0, q = 0;
    for (int x : a) {
        if (x & diffBit) p ^= x;               // group with the bit set
        else             q ^= x;               // group without
    }
    return {p, q};
}
```

Every duplicate pair lands in the same group (identical values have identical bits), so each group reduces to a Single Number problem. Using `long long` for the isolation avoids the `INT_MIN` edge case where `-x` overflows.

### Single Number II (LC 137): every element appears three times

XOR does not help — three copies leave one behind. Count each bit position modulo 3 instead:

```cpp
int singleNumber(const vector<int>& a) {
    int res = 0;
    for (int i = 0; i < 32; i++) {
        int count = 0;
        for (int x : a) count += (x >> i) & 1;
        if (count % 3) res |= (1 << i);
    }
    return res;
}
```

If every number appears three times, each bit position's count is a multiple of 3; the leftover is the unique number's bit. O(32n) = O(n) time, O(1) space.

This works correctly for negative numbers too: setting bit 31 produces the right two's-complement value.

### Must remember

1. `x ^ x = 0` and `x ^ 0 = x`. Everything follows from these two.
2. XOR is commutative and associative, so order never matters.
3. Pairs cancel. Anything appearing an even number of times disappears.
4. Two unique numbers: XOR everything, isolate a differing bit, partition.
5. Three copies: count bits modulo 3.
6. XOR-based solutions are O(1) space, which is why they are the expected answer.
7. XOR never overflows, unlike the sum-formula alternatives.

---

## 14.5 The classic tricks

### Power of two

```cpp
bool isPowerOfTwo(int x) {
    return x > 0 && (x & (x - 1)) == 0;
}
```

A power of two has exactly one set bit, so clearing the lowest set bit leaves 0. **The `x > 0` guard is mandatory** — without it, 0 and negative values give false positives.

### Counting set bits

```cpp
// 1. Built-in (fastest, GCC/Clang)
__builtin_popcount(x);        // int
__builtin_popcountll(x);      // long long

// 2. Brian Kernighan: O(number of set bits)
int count = 0;
while (x) { x &= (x - 1); count++; }

// 3. Naive: O(32)
int count = 0;
for (int i = 0; i < 32; i++) count += (x >> i) & 1;
```

Kernighan's method loops once per **set bit**, not once per bit position, which is a real win on sparse values. If asked to implement it yourself, that is the expected answer.

### Counting Bits for 0..n (LC 338): bits meet DP

```cpp
vector<int> countBits(int n) {
    vector<int> dp(n + 1, 0);
    for (int i = 1; i <= n; i++)
        dp[i] = dp[i >> 1] + (i & 1);         // bits of i/2, plus the last bit
    return dp;
}
```

`i >> 1` drops the last bit, and `i & 1` adds it back. O(n) total instead of O(n log n).

An equally neat alternative: `dp[i] = dp[i & (i-1)] + 1` — one fewer set bit, plus one.

### The rest of the toolkit

```cpp
x & 1                          // is x odd?
x >> 1                         // x / 2   (for non-negative x)
x << 1                         // x * 2
(x ^ y) < 0                    // do x and y have opposite signs?
x & (~0 << i)                  // clear all bits BELOW position i
x | (x + 1)                    // set the lowest zero bit
a ^ b ^ a == b                 // XOR cancellation, used in many puzzles
```

### Reverse bits (LC 190)

```cpp
uint32_t reverseBits(uint32_t n) {
    uint32_t res = 0;
    for (int i = 0; i < 32; i++) {
        res = (res << 1) | (n & 1);           // push n's lowest bit into res
        n >>= 1;
    }
    return res;
}
```

**Use `uint32_t`.** Shifting into the sign bit of a signed `int` is undefined behaviour.

### The XOR swap (know it, do not use it)

```cpp
a ^= b; b ^= a; a ^= b;        // swaps without a temp
```

It works, and it **fails catastrophically when `a` and `b` are the same variable** (both become 0). It is also slower than `std::swap` on modern compilers. Know it as trivia; never write it.

---

## 14.6 Subsets with bitmasks

The bridge from bit manipulation to Modules 8 and 13.

### The idea

A subset of `n` elements is an `n`-bit number: bit `i` set means element `i` is included. Iterating `0` to `2ⁿ − 1` enumerates every subset exactly once.

```cpp
void allSubsets(const vector<int>& a) {
    int n = a.size();
    for (int mask = 0; mask < (1 << n); mask++) {
        vector<int> subset;
        for (int i = 0; i < n; i++)
            if (mask & (1 << i)) subset.push_back(a[i]);
        // process subset
    }
}
```

O(2ⁿ · n) time — the same as the backtracking version from Module 8.3, with no recursion.

**Which to use:** backtracking is easier to prune and extends to permutations and constrained problems. The bitmask version is shorter, iterative, and is the right choice when you need the **mask itself** as a DP state.

### The mask operations for DP

```cpp
mask & (1 << i)          // is element i in the set?
mask | (1 << i)          // add element i
mask & ~(1 << i)         // remove element i
mask == (1 << n) - 1     // is every element included?
__builtin_popcount(mask) // how many elements are in the set?
```

`(1 << n) - 1` is the "all bits set" mask, which is the usual termination condition in bitmask DP.

### Iterating submasks (advanced)

```cpp
for (int sub = mask; sub; sub = (sub - 1) & mask) {
    // sub ranges over every non-empty submask of mask
}
// handle sub == 0 separately if needed
```

Summed over all masks this is O(3ⁿ), not O(4ⁿ). Used in set-partition DP. **Tier 4** — know it exists.

### Bitmask DP recap

Module 13.13 covered this. The short version: when `n ≤ 20`, a state of the form `dp[mask][i]` is viable, where `mask` records which items have been used. Complexity is typically O(2ⁿ · n) or O(2ⁿ · n²).

**`n ≤ 20` in the constraints is the signal.** Nothing else produces that specific bound.

### Must remember

1. A subset is an integer; iterate `0` to `(1 << n) - 1`.
2. `(1 << n) - 1` is the full mask.
3. `__builtin_popcount(mask)` gives the subset size.
4. O(2ⁿ · n) to enumerate all subsets with their contents.
5. `n ≤ 20` is the bitmask signal.
6. Use `1LL << n` when `n` can reach 31 or beyond.

---

## 14.7 C++ pitfalls

These cause real bugs and at least two of them are genuinely surprising.

### 1. Operator precedence — the big one

**Bitwise operators have LOWER precedence than comparison operators.**

```cpp
if (x & 1 == 0)          // parses as  x & (1 == 0)  ->  x & 0  ->  always 0!
if ((x & 1) == 0)        // CORRECT
```

The first line compiles without warning on many setups and is always false. **Always parenthesise bitwise expressions inside comparisons.** This is a historical wart in C's precedence table and it catches people constantly.

Same problem with `|`, `^`, `<<`, and `>>`.

### 2. Shifting into or past the sign bit

```cpp
1 << 31          // UNDEFINED BEHAVIOUR for a 32-bit signed int
1u << 31         // fine (unsigned)
1LL << 31        // fine (64-bit)
1 << 32          // UNDEFINED: shift >= the type's width
```

**Rule: use `1LL << i` whenever `i` can reach 31, and never shift by the type's width or more.**

### 3. Right-shifting negative numbers

`-8 >> 1` is implementation-defined in older standards (arithmetic shift in practice on every mainstream compiler, giving −4). Avoid relying on it; shift unsigned values when the sign could matter.

### 4. `~` on small types

`~x` operates after integer promotion, so `~(char)5` is an `int`. Rarely matters, occasionally surprising.

### 5. `-x` on `INT_MIN`

`INT_MIN` has no positive counterpart, so `-INT_MIN` overflows. The `x & -x` trick is technically unsafe there; cast to `long long` or `unsigned` when the input range includes `INT_MIN`.

### 6. Signed overflow in bit arithmetic

Signed overflow is undefined behaviour in C++. For algorithms like addition-without-`+` (LC 371), use `unsigned` for the intermediate carry:

```cpp
int getSum(int a, int b) {
    while (b != 0) {
        unsigned carry = (unsigned)(a & b) << 1;
        a = a ^ b;                    // sum without carry
        b = carry;                    // carry to propagate
    }
    return a;
}
```

### Must remember

1. **Parenthesise bitwise expressions inside comparisons.** `(x & 1) == 0`.
2. `1 << 31` is UB for `int`. Use `1LL << 31`.
3. Never shift by the type's width or more.
4. `-INT_MIN` overflows; be careful with `x & -x` at the boundary.
5. Use `unsigned` for shifts that could touch the sign bit.
6. Signed overflow is UB; cast for carry arithmetic.

---

## 14.8 Bit manipulation cheat sheet

You asked for a compact one. This is it.

### Core operations

| Goal | Expression |
|---|---|
| Check bit `i` | `(x >> i) & 1` |
| Set bit `i` | `x \| (1 << i)` |
| Clear bit `i` | `x & ~(1 << i)` |
| Toggle bit `i` | `x ^ (1 << i)` |
| Clear lowest set bit | `x & (x - 1)` |
| Isolate lowest set bit | `x & (-x)` |
| Set lowest zero bit | `x \| (x + 1)` |
| Clear all bits below `i` | `x & (~0 << i)` |
| Full mask of `n` bits | `(1 << n) - 1` |

### Tests

| Question | Expression |
|---|---|
| Is `x` odd? | `x & 1` |
| Is `x` a power of two? | `x > 0 && (x & (x-1)) == 0` |
| Do `x`, `y` have opposite signs? | `(x ^ y) < 0` |
| Is bit `i` of `mask` set? | `mask & (1 << i)` |
| Is `mask` complete (n bits)? | `mask == (1 << n) - 1` |

### Arithmetic

| Goal | Expression |
|---|---|
| `x · 2^k` | `x << k` |
| `x / 2^k` (non-negative) | `x >> k` |
| `x mod 2^k` | `x & ((1 << k) - 1)` |
| Count set bits | `__builtin_popcount(x)` |
| Count set bits (64-bit) | `__builtin_popcountll(x)` |
| Trailing zeros | `__builtin_ctz(x)` |
| Leading zeros | `__builtin_clz(x)` |
| Highest set bit position | `31 - __builtin_clz(x)` |

### XOR identities

| Identity | |
|---|---|
| `x ^ 0` | `= x` |
| `x ^ x` | `= 0` |
| `a ^ b ^ b` | `= a` |
| XOR of all, pairs cancel | odd-count survivors remain |

### Set / subset operations

| Goal | Expression |
|---|---|
| Add element `i` | `mask \| (1 << i)` |
| Remove element `i` | `mask & ~(1 << i)` |
| Union of two sets | `a \| b` |
| Intersection | `a & b` |
| Difference (a minus b) | `a & ~b` |
| Symmetric difference | `a ^ b` |
| Subset size | `__builtin_popcount(mask)` |
| Iterate all subsets of `n` | `for (int m = 0; m < (1<<n); m++)` |
| Iterate submasks of `mask` | `for (int s = mask; s; s = (s-1) & mask)` |

### Constants

| | Value |
|---|---|
| `~0` | `-1`, all bits set |
| `INT_MAX` | `0x7FFFFFFF` |
| `INT_MIN` | `0x80000000` |
| `log₂(10⁶)` | ≈ 20 bits |
| `log₂(10⁹)` | ≈ 30 bits |

---

## 14.9 Consolidation

### Recognition guide

| The statement says | Technique |
|---|---|
| "every element appears twice except one" | XOR everything |
| "except two" | XOR, isolate a differing bit, partition |
| "every element appears three times except one" | Count bits mod 3 |
| "missing number from 0..n" | XOR indices and values, or the sum formula |
| "without using +, −, ×, ÷" | Bit arithmetic with carry |
| "count set bits", "Hamming weight" | `__builtin_popcount` or Kernighan |
| "is it a power of two/four" | `x & (x-1)` |
| "generate all subsets" | Bitmask enumeration, or backtracking |
| "n ≤ 20" with subset structure | **Bitmask DP** |
| "swap / reverse / rotate bits" | Shift and mask loop |
| "maximum XOR pair" | **Trie** (Module 15) |
| "O(1) space required" on a counting problem | Suspect XOR |

**"O(1) extra space" on a problem that obviously wants a hash map is the strongest XOR signal there is.**

### Must remember (consolidated)

1. The five-line toolkit: check, set, clear, toggle, clear-lowest.
2. `x & (x-1)` clears the lowest set bit; `x & -x` isolates it.
3. `x ^ x = 0`, `x ^ 0 = x`. Pairs cancel; order does not matter.
4. Power of two: `x > 0 && (x & (x-1)) == 0`. The guard is mandatory.
5. Brian Kernighan counts bits in O(set bits).
6. Two unique numbers: partition by any differing bit.
7. Three copies: count each bit position mod 3.
8. A subset is an integer; `(1 << n) - 1` is the full mask.
9. **Parenthesise bitwise ops inside comparisons.**
10. `1 << 31` is UB for `int`; use `1LL << 31`.
11. Never shift by the type's width or more.
12. `n ≤ 20` signals bitmask DP.
13. XOR solutions are O(1) space, which is usually the point.
14. `__builtin_popcount`, `__builtin_ctz`, `__builtin_clz` are all O(1).

### Common mistakes (consolidated)

**Wrong answer**
- `x & 1 == 0` instead of `(x & 1) == 0`.
- Missing the `x > 0` guard in the power-of-two test.
- Using XOR for the "appears three times" variant.
- `(x >> i) & 1` versus `x & (1 << i)` confusion when you need the literal bit value.
- Assuming `>>` on negatives behaves a particular way.

**Undefined behaviour**
- `1 << 31` on a signed `int`.
- Shifting by 32 or more.
- `-INT_MIN`.
- Signed overflow in carry arithmetic.
- XOR swap where both operands are the same variable.

**Missed optimisations**
- Looping 32 times to count bits instead of using Kernighan or the builtin.
- Using a hash map where XOR gives O(1) space.
- Recursion for subset generation where a bitmask loop is three lines.

---

## 14.10 Problem set

Nine problems. They are mostly easy by design; the module is about fluency, not difficulty.

### Level 1 — Concept (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Single Number (LC 136) | Easy | XOR cancellation | The core property, in one line |
| Number of 1 Bits (LC 191) | Easy | Bit counting | Kernighan's method |
| Power of Two (LC 231) | Easy | `x & (x-1)` | Why the `x > 0` guard matters |

### Level 2 — Pattern (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Counting Bits (LC 338) | Easy | Bits + DP | `dp[i >> 1] + (i & 1)` |
| Missing Number (LC 268) | Easy | XOR indices and values | Two valid approaches, one overflows |
| Reverse Bits (LC 190) | Easy | Shift and mask | Why `uint32_t` |

### Level 3 — Interview (3)

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| **Single Number II (LC 137)** | Medium | Bit counts mod 3 | When XOR does not work |
| **Single Number III (LC 260)** | Medium | Partition by a differing bit | The cleverest trick in the module |
| Subsets (LC 78), bitmask version | Medium | Mask enumeration | The bridge to bitmask DP |

### Optional

| Problem | Difficulty | Pattern | What it teaches |
|---|---|---|---|
| Sum of Two Integers (LC 371) | Medium | Carry arithmetic | Addition from first principles; `unsigned` for UB |
| Maximum XOR of Two Numbers (LC 421) | Medium | XOR **trie** | Do this **after** Module 15 |

**LC 260 is the one worth understanding properly.** The move — XOR everything to get `p ^ q`, then use any set bit of that result to split the array into two independent Single Number problems — is the kind of reasoning that transfers, and it is a satisfying result to be able to derive rather than recall.

---

## Exit checklist

```
[ ] I can write the five-line toolkit from memory
[ ] I know x & (x-1) clears the lowest set bit
[ ] I know x & -x isolates it
[ ] I can state the XOR properties and what follows from them
[ ] I can solve Single Number in one line and explain why
[ ] I can derive the two-unique-numbers partition trick
[ ] I know why XOR fails for the three-copies variant
[ ] I can write the power-of-two test including the guard
[ ] I know Brian Kernighan's bit count
[ ] I can enumerate subsets with a bitmask loop
[ ] I know (1 << n) - 1 is the full mask
[ ] I ALWAYS parenthesise bitwise ops inside comparisons
[ ] I use 1LL << i when i can reach 31
[ ] I know "O(1) space" on a counting problem hints at XOR
[ ] I have the cheat sheet saved somewhere I'll actually look
[ ] Level 1-3 problems solved
```

---

## Next

Say **"Start Phase 15"** for Trie (5–6 hours, Tier 3). It is the last teaching module, and a short one now that trees are done — a trie is a tree with 26 children, and the interesting content is knowing when it beats a hash map, plus the XOR trie which uses exactly the bit operations from this module.

After that, what remains is the roadmap's advanced-topics survey (segment trees, Fenwick trees, KMP, Z-algorithm, and the rest, each classified by placement priority so you can decide what to skip) and the ten final cheat sheets.
