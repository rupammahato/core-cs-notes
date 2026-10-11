# Computer Networks Placement Handbook — Part 11
# Module 9: Network Security

**Module 9 · 4 hours · Tier 1/2 · Requires: M3 (IP, NAT), M5 (TCP, SYN), M7 (DNS), M8 (HTTP). Links to DBMS M6 (SQL injection)**

---

## Why this module matters

Security questions for an SDE candidate stop at TLS. Nobody asks you about cipher-suite internals; they ask **what a certificate proves**, **what the handshake accomplishes**, and — most often of all — **the difference between hashing and encryption**. That last one is asked constantly and answered badly constantly.

The list:

- **Symmetric vs asymmetric encryption**, and why both are used together
- **Hashing vs encryption vs encoding** — the single most common confusion in this area
- **Walk me through the TLS handshake**
- **What does a certificate actually prove?**
- **What does HTTPS *not* hide?**
- Name some attacks and their defences — MITM, DDoS, SYN flood, ARP/DNS spoofing

The organising principle:

> **Encryption gives you confidentiality and nothing else. On its own it means you have a private conversation with whoever answered the phone — which is useless if that is the attacker. Authentication is the separate, harder problem, and the certificate system exists solely to solve it. Every real protocol therefore layers three distinct properties: confidentiality (nobody can read it), integrity (nobody can change it undetected), and authenticity (it is really who it claims to be).**

**How this module was verified.** Three real TLS handshakes with their negotiated versions, cipher suites, issuers and certificate details; **certificate validation broken three different ways** against `badssl.com`, each rejected with its specific reason; and the decisive demonstration — **connecting to an expired certificate with validation disabled, which encrypts perfectly well and proves nothing**. Password-hashing rates were measured on this CPU. And this network's own filtering, found in M3 and M7, serves as the live firewall example.

---

## 9.1 The threat model

Before mechanisms, be clear what you are defending against. An attacker on the path can do four things:

```
  EAVESDROP   read your traffic                      -> defeated by CONFIDENTIALITY
  TAMPER      modify it in flight                    -> defeated by INTEGRITY
  IMPERSONATE pretend to be the other end            -> defeated by AUTHENTICITY
  REPLAY      re-send a valid message later          -> defeated by FRESHNESS
              (nonces, sequence numbers, timestamps)
```

And a fifth that cryptography cannot touch:

```
  DENY SERVICE  exhaust a resource so nobody can use it  -> capacity, filtering, rate limits
```

**Those five map to five defences, and conflating them is where bad answers come from.** "We use HTTPS so we're secure" addresses the first three and does nothing for the last two.

The classic distinction worth naming: a **passive** attacker only listens, so you may never know they were there, which is why confidentiality must be the default rather than something you enable when you suspect trouble. An **active** attacker modifies or injects and is therefore detectable — if you are checking integrity.

---

## 9.2 Hashing vs encryption vs encoding

The three that get confused, demonstrated on the same input.

```
  plaintext: transfer 1000 to account 42

  ENCODING   base64: dHJhbnNmZXIgMTAwMCB0byBhY2NvdW50IDQy
             decode: transfer 1000 to account 42
             -> REVERSIBLE BY ANYONE. No key. NOT security at all.

  HASHING    md5     c9ce191d645949ee5b8666e552261ed2                  (128 bits)
             sha1    f8ac214f972f898f0872b4970738f14ec091b026          (160 bits)
             sha256  5176e1344d4216b629d8d6df85fc2eb0ec5b9b9b1a39e...  (256 bits)
             sha512  870b313a923c2f70402b5178a0022409b0661ebb3b5b6...  (512 bits)
             -> ONE WAY. Fixed size. No key. Cannot be reversed.

  MAC        HMAC-SHA256 with a secret key: 2ff14f7413b3913de736d4a84c514117...
             -> one way AND keyed: proves INTEGRITY + AUTHENTICITY
```

| | Encoding | Hashing | Encryption |
|---|---|---|---|
| Purpose | **Representation** | **Integrity / fingerprint** | **Confidentiality** |
| Key | None | None (or a key for a MAC) | **Yes** |
| Reversible | **Yes, by anyone** | **No** | Yes, **with the key** |
| Output size | Proportional to input | **Fixed** | Roughly input size |
| Example | base64, URL-encoding, UTF-8 | SHA-256, MD5 | AES, RSA |
| Security value | **None** | Detects change | Hides content |

> **The one-line test:** *base64 is not encryption because there is no key — anyone can reverse it. A hash is not encryption because it cannot be reversed at all, by anyone, including you.*

**The three questions they answer**, which is the cleanest way to hold the distinction:

```
  encoding:   "can both sides read the same bytes?"      (a transport format)
  hashing:    "is this the same data?"                   (integrity)
  encryption: "can only the key-holder read it?"         (confidentiality)
```

### The avalanche effect

```
   sha256('account 42') = fd992c1fb101405aa3aa4c58dd11c371...
   sha256('account 43') = bca97c36c7191bae98dbf699842f815d...
   bits differing: 113 of 256 (44%) -- a one-character change
```

One character changed, and **44% of the output bits flipped** — close to the ideal 50%. That is what makes a hash a usable fingerprint: similar inputs do not produce similar outputs, so you cannot work backwards by getting "close".

### Hash properties, and which ones are broken

| Property | Meaning | Status |
|---|---|---|
| **Preimage resistance** | Given `h`, you cannot find `m` with `hash(m) = h` | Holds for SHA-2/3 |
| **Second preimage** | Given `m`, you cannot find `m′ ≠ m` with the same hash | Holds |
| **Collision resistance** | You cannot find *any* two inputs with the same hash | **Broken for MD5 and SHA-1** |

**MD5 and SHA-1 are not "weak", they are broken for collisions** — practical collisions exist and have been used to forge certificates. They remain acceptable for non-adversarial checksums (detecting accidental corruption) and must never be used for signatures. SHA-256 is the default; SHA-3 is a structurally different alternative.

---

## 9.3 Password hashing is a different problem

A general hash is **the wrong tool for passwords**, and the reason is measurable.

```
  measured sha256 rate on this CPU, single-threaded: 2,106,611 hashes/sec
   -> an 8-char lowercase password space is 26^8 = 208,827,064,576,
      which at 2,106,611/s takes 27.5 hours on ONE CPU CORE.
```

**Two million hashes a second on one core of an ordinary laptop**, and a GPU does millions to billions. Fast is a *virtue* for a checksum and a *catastrophe* for a password, because speed helps the attacker exactly as much as it helps you — and the attacker is the one doing billions of attempts.

So password hashes are **deliberately slow**:

```
  PBKDF2-SHA256,   1,000 rounds:    0.95 ms per hash ->        1,053 attempts/sec
  PBKDF2-SHA256,  10,000 rounds:    3.91 ms per hash ->          256 attempts/sec
  PBKDF2-SHA256, 100,000 rounds:   33.08 ms per hash ->           30 attempts/sec
```

**From two million per second to thirty.** That is a factor of 70,000, bought by a 33 ms delay the legitimate user never notices on a login. The work factor is tunable, which is the point — as hardware improves you raise the round count.

**And salting**, which solves a different problem:

```
   same password, salt_a -> dcf7e66ac60e1d2dfa9fc454
   same password, salt_b -> 8b8832e5be6d476a9d684b97   (unrelated)
```

A **salt** is a per-user random value stored alongside the hash. It is not secret; its job is to make identical passwords hash differently, so that (a) one precomputed **rainbow table** cannot cover every user, and (b) a breach does not reveal which users share a password. Without a salt, cracking one user's password cracks it for everyone who chose the same one.

**What to actually use:** `bcrypt`, `scrypt` or `argon2` rather than PBKDF2, because they are additionally **memory-hard** — they require a large working set, which is specifically what defeats GPUs and ASICs, whose advantage is parallel arithmetic rather than memory bandwidth. Argon2 is the current recommendation.

---

## 9.4 Symmetric and asymmetric encryption

| | Symmetric | Asymmetric (public key) |
|---|---|---|
| Keys | **One shared secret** | **A key pair** — public and private |
| Encrypt / decrypt | Same key does both | Public encrypts, private decrypts |
| Speed | **Fast** — hardware-accelerated | **Slow** — 100–1000× slower |
| Key distribution | **The hard problem** — how do you share it? | **Solved** — publish the public key |
| Scaling | `n(n−1)/2` keys for `n` parties | `n` key pairs |
| Examples | AES, ChaCha20, 3DES | RSA, ECDSA, Diffie-Hellman, Ed25519 |
| Used for | **Bulk data** | **Key exchange and signatures** |

**Why both, which is the actual question:** symmetric encryption is fast but requires a shared key, and you cannot share a key over a channel you have not yet secured — a circular problem. Asymmetric cryptography solves exactly that circularity and is far too slow for bulk data. So every real protocol uses asymmetric cryptography **once**, to agree a symmetric key, then symmetric encryption for everything after.

```
   expensive, once:   asymmetric -> agree a shared secret
   cheap, forever:    symmetric  -> encrypt the actual traffic
```

That hybrid is TLS, SSH, PGP and Signal. It is not a compromise, it is the design.

### Diffie-Hellman, and why ephemeral matters

**Diffie-Hellman** lets two parties derive a shared secret over a public channel without ever transmitting it — each combines its own private value with the other's public value and arrives at the same result, which an eavesdropper cannot compute.

**Ephemeral** DH (`DHE`, `ECDHE`) generates a **fresh** key pair for every session and discards it afterwards. That buys **forward secrecy**:

> **If the server's long-term private key is stolen tomorrow, past sessions remain unreadable** — because they were encrypted with ephemeral keys that no longer exist anywhere. Under old RSA key transport, the session key was *encrypted with the server's public key*, so a recorded session plus a later-stolen private key decrypts everything retroactively.

That property is why TLS 1.3 **removed** RSA key transport entirely and made ephemeral key exchange mandatory. It is a good thing to be able to explain, because it shows you understand that "it was encrypted at the time" is not sufficient.

### Digital signatures

Signatures use the key pair **the other way round**:

```
  ENCRYPTION  encrypt with the PUBLIC key  -> only the private key can read it
                                              (confidentiality)
  SIGNATURE   sign with the PRIVATE key    -> anyone with the public key can
                                              verify it   (authenticity + integrity)
```

In practice you sign the **hash** of the message, not the message — because signing is slow and the hash is fixed-size. A signature therefore proves three things at once: the holder of the private key produced it, the content has not changed, and (with a nonce or timestamp) that it is current.

**And this is why collision-resistant hashing matters for signatures**: if an attacker can find two documents with the same hash, a signature on one is a valid signature on the other. That is precisely how forged MD5 certificates were produced.

---

## 9.5 Certificates and the chain of trust

Asymmetric cryptography solves key distribution only if you know the public key is genuinely the server's. Otherwise an attacker simply supplies their own — a perfect man-in-the-middle. **The certificate system exists to solve this one problem.**

```
  a CERTIFICATE is a signed statement:
     "the public key below belongs to example.com"
     ... signed by a Certificate Authority

  the CHAIN OF TRUST:

    ROOT CA certificate          <- SELF-SIGNED, pre-installed in your
      (in the OS/browser store)     OS and browser. This is the ANCHOR.
            | signs
    INTERMEDIATE CA certificate  <- so the root's key can stay offline
            | signs
    SERVER (leaf) certificate    <- "this key belongs to example.com"
```

The verification a client performs, in order:

```
  1. does the chain lead to a root I ALREADY TRUST?
  2. is every signature in the chain valid?
  3. is the name I asked for in the certificate's SAN list?
  4. is it within its validity dates?
  5. has it been revoked? (CRL, OCSP, OCSP stapling)
  6. does the CAA record permit this CA? (M7)
```

### Verified: three real certificates

```
  example.com
   protocol      TLSv1.3
   cipher suite  TLS_AES_256_GCM_SHA384  (256 bit)
   handshake     71.6 ms
   subject CN    example.com
   issuer        SSL Corporation / Cloudflare TLS Issuing ECC CA 3
   valid         Sep 26 22:49:11 2026 GMT  ->  Dec 25 22:56:35 2026 GMT
   SANs (2)      example.com, *.example.com

  www.google.com
   protocol      TLSv1.3
   cipher suite  TLS_AES_256_GCM_SHA384  (256 bit)
   handshake     48.0 ms
   issuer        Google Trust Services / WE2
   valid         Sep 18 20:02:33 2026 GMT  ->  Dec 11 20:02:32 2026 GMT
   SANs (1)      www.google.com
   serial        EE1B4C7369FE9ECB129010DA0C5C87DF

  github.com
   protocol      TLSv1.3
   cipher suite  TLS_AES_128_GCM_SHA256  (128 bit)
   handshake     45.8 ms
   issuer        Sectigo Limited / Sectigo Public Server Authentication CA DV E36
   valid         Sep  1 00:00:00 2026 GMT  ->  Nov 29 23:59:59 2026 GMT
   SANs (2)      github.com, www.github.com
```

Three things to notice. **The validity windows are about 90 days** — short-lived certificates are now the norm, because automated issuance (ACME, Let's Encrypt) made renewal cheap and short lifetimes limit the damage from a key compromise. **Matching is done on the SAN list**, not the common name: `CN` is legacy and browsers have ignored it for years, which is why a certificate for `example.com` also lists `*.example.com`. And all three negotiated **TLS 1.3 with an AEAD cipher**, which §9.6 explains is now essentially the only shape available.

### Verified: validation broken three ways

```
     expired.badssl.com         REJECTED: certificate has expired
     wrong.host.badssl.com      REJECTED: Hostname mismatch, certificate is not valid for ...
     self-signed.badssl.com     REJECTED: self-signed certificate
```

Three different failures, three specific reasons — the validity window, the name check and the chain to a trusted root. Each corresponds to one of the numbered steps above.

### The demonstration that matters most

```
  the same expired site with verification DISABLED:
     connected. protocol TLSv1.2, cipher ECDHE-RSA-AES128-GCM-SHA256
     -> ENCRYPTION STILL WORKS. What is lost is AUTHENTICATION.
```

**The connection is fully encrypted with a perfectly good cipher, and it is worthless.** The traffic is confidential *to whoever answered* — which, if an attacker is in the path, is the attacker. This is the whole reason certificates exist, and it is the argument against every `verify=False`, `-k` and "accept all certificates" workaround you will be tempted by:

> **Disabling certificate verification does not weaken encryption. It removes authentication entirely, which converts strong encryption into strong encryption with an unknown party.**

(One honest wrinkle from the same experiment: connecting to `example.com` while claiming to expect a different hostname produced a **connection reset** rather than a certificate error. The server rejected the unrecognised **SNI** before the certificate stage, so the failure happened earlier than the validation step I was testing. That is itself informative — SNI is sent in the clear and the server acts on it first.)

### What a certificate does and does not prove

| Proves | Does **not** prove |
|---|---|
| The holder controls this private key | That the site is honest or safe |
| A CA verified control of the domain | That the company is reputable |
| The name matches what you asked for | That the content is accurate |
| It has not expired or been revoked | That it is the site you *meant* to visit |

**The last row is the one that matters in practice.** A DV certificate for `paypa1.com` is perfectly valid — it just belongs to a different domain than you thought. HTTPS proves you are talking to the name in the address bar; it does not check whether that name is the one you wanted. Phishing sites have valid certificates, and "it has a padlock so it's safe" is a genuinely harmful misunderstanding.

**DV, OV and EV** differ only in how much the CA checked: domain control, organisation identity, or extended legal verification. Browsers have removed the EV visual indicators because studies showed users ignored them, so in practice all three look identical.

---

## 9.6 The TLS handshake

### TLS 1.2 — two round trips

```
  client                                                server
    |---- ClientHello ----------------------------------->|
    |     TLS versions, cipher suites, random, SNI        |
    |                                                     |
    |<------------------------------- ServerHello --------|
    |     chosen version + cipher, server random          |
    |<------------------------------- Certificate --------|
    |<------------------------- ServerKeyExchange --------|  (ECDHE params, signed)
    |<------------------------- ServerHelloDone ----------|
    |                                                     |
    |---- ClientKeyExchange ----------------------------->|  (its ECDHE public value)
    |---- ChangeCipherSpec ----------------------------->|
    |---- Finished (encrypted) ------------------------->|
    |<------------------------- ChangeCipherSpec ---------|
    |<------------------------- Finished (encrypted) -----|
    |                                                     |
    |========== application data ========================|
                        2 RTT before any data
```

### TLS 1.3 — one round trip

```
  client                                                server
    |---- ClientHello + KEY SHARE ---------------------->|
    |     the client GUESSES the group and sends its     |
    |     ephemeral public value immediately             |
    |                                                     |
    |<-------- ServerHello + key share, {Certificate},  --|
    |          {CertificateVerify}, {Finished}            |
    |          (everything in braces is ENCRYPTED)        |
    |---- Finished ------------------------------------->|
    |========== application data ========================|
                        1 RTT before any data
                   (0 RTT on resumption, with caveats)
```

**The trick that saves the round trip:** in 1.2 the client had to wait to be told which key-exchange group the server wanted. In 1.3 it **guesses** — sends a key share for the most likely group in the very first message — so the server can derive the shared secret and reply with its certificate already encrypted. If the guess is wrong there is a `HelloRetryRequest` and you are back to two round trips, but the guess is almost always right.

Two more consequences: the **certificate is encrypted** in 1.3, so a passive observer cannot see which certificate was served (though SNI still leaks the hostname), and **0-RTT resumption** can send application data in the first flight — at the cost of replay protection, which is why it is restricted to idempotent requests.

### What the handshake achieves, in one list

```
  1. agree a TLS version and cipher suite
  2. AUTHENTICATE the server (its certificate chain)
  3. optionally authenticate the client (mutual TLS)
  4. derive a shared symmetric key, with FORWARD SECRECY
  5. verify that nobody tampered with the negotiation
     (the Finished messages are a MAC over the whole transcript)
  6. agree the application protocol via ALPN  (M8: this is where HTTP/2 is chosen)
```

**Step 5 is the one people omit and it matters:** the `Finished` messages authenticate the entire handshake transcript, so a man-in-the-middle cannot have quietly downgraded the version or the cipher suite — any edit changes the MAC. That is what defeats **downgrade attacks**.

### The round trips, costed

```
   HTTP/1.1 + TLS 1.2     1 RTT TCP + 2 RTT TLS = 3 RTT before the request
   HTTP/1.1 + TLS 1.3     1 RTT TCP + 1 RTT TLS = 2 RTT before the request
   HTTP/3 (QUIC)          0 RTT TCP + 1 RTT     = 1 RTT before the request

   at the Mumbai-California RTT floor of 130 ms (M0):
   HTTP/1.1 + TLS 1.2      390 ms before the first request byte is sent
   HTTP/1.1 + TLS 1.3      260 ms
   HTTP/3                  130 ms
```

**That is the whole modern performance story in three rows** — and from M0, no bandwidth upgrade changes any of it.

### What TLS 1.3 removed

| Removed | Why |
|---|---|
| RSA key transport | **No forward secrecy** — a stolen key decrypts recorded past traffic |
| Static Diffie-Hellman | Same problem |
| CBC-mode ciphers | Padding-oracle attacks — BEAST, Lucky13 |
| RC4 | Broken keystream biases |
| MD5/SHA-1 signatures | Practical collisions |
| **Compression** | The **CRIME** attack recovered secrets from compressed length |
| Renegotiation | A protocol-level attack surface |

**TLS 1.3 deliberately leaves essentially one shape**: ephemeral (EC)DHE key exchange plus an AEAD cipher. Fewer options means fewer downgrade paths and fewer misconfigurations — a design lesson worth stating, because the long tail of TLS 1.2 vulnerabilities came mostly from the flexibility rather than from the primitives.

---

## 9.7 What HTTPS does and does not hide

Verified, with the reasons:

```
  what                               status    why
  the request URL path and query     HIDDEN    inside the encrypted body
  the request and response headers   HIDDEN    same
  cookies and credentials            HIDDEN    same
  the destination IP ADDRESS         VISIBLE   it is the IP header -- routers need it
  the destination PORT               VISIBLE   TCP header
  the HOSTNAME via SNI               VISIBLE   sent in the CLEAR in the ClientHello,
                                               so the server can pick a certificate
  the DNS query that preceded it     VISIBLE   plaintext UDP/53 unless DoH/DoT
  the SIZE and TIMING of traffic     VISIBLE   enables traffic analysis
  the certificate the server sent    VISIBLE   TLS 1.2; encrypted in TLS 1.3
```

> **An observer learns who you talked to and how much, but not what you said.**

Three points that follow and get asked:

**The URL is hidden but the hostname is not.** `https://example.com/secret-page?token=abc` hides the path and the query, but the *hostname* is in the SNI in plaintext. So HTTPS protects the contents of your request to a site, not the fact that you visited it. **ECH** (encrypted client hello) is the in-progress fix.

**Putting secrets in a URL is still wrong even over HTTPS**, because the URL is not encrypted end-to-end in the places that matter: it lands in browser history, server access logs, the `Referer` header sent to third parties, and any proxy that terminates TLS.

**Traffic analysis works without decryption.** Packet sizes and timing can identify which page of a site you loaded, or which video you are streaming, purely from the pattern. Encryption does not hide shape.

---

## 9.8 Firewalls, NAT and VPNs

### Firewalls

| Type | Inspects | Can decide |
|---|---|---|
| **Packet filter** (stateless) | Each packet's headers in isolation | By address, port, protocol |
| **Stateful** | Packets **plus connection state** | "Is this part of a connection I allowed?" |
| **Application / proxy** (layer 7) | The payload | By URL, HTTP method, content |
| **WAF** | HTTP semantics | Injection patterns, rate limits |

**Why stateful matters:** a stateless filter that allows outbound traffic must also allow all the inbound replies, which means permitting inbound traffic to high ports from anywhere. A stateful firewall tracks the connection table and admits **only** packets belonging to connections initiated from inside. That is the single biggest improvement in firewall design and the reason "allow established and related" is the first rule in every ruleset.

### This network as the live example

The filtering found in earlier modules is a real firewall policy, observed:

```
  ping 1.1.1.1              -> 100% loss          (ICMP echo blocked, M3)
  tracert 1.1.1.1           -> 3 hops then *      (TTL-exceeded partly blocked)
  UDP/53 -> 8.8.8.8         -> Timeout            (all external DNS blocked, M7)
  UDP/53 -> local resolver  -> OK                 (only the operator's resolvers)
  TCP/443 -> example.com    -> works              (ordinary web traffic allowed)
  TCP/443 -> 1.1.1.1        -> Timeout            (public DNS providers blocked outright)
```

**Read as a policy, that is coherent:** permit normal web browsing, force all name resolution through resolvers the operator controls, and deny the diagnostic protocols. The DNS rule is the interesting one — it gives the operator filtering, logging and visibility over every name every host looks up, which is exactly the control that **DoH** is designed to bypass. The timeouts in M7 are a policy decision, not a fault.

**And the cost of over-blocking ICMP**, from M3: path-MTU discovery depends on ICMP type 3 code 4, so blocking all ICMP produces **black-hole connections** where small packets work and large ones hang forever. It is a textbook over-correction.

### NAT is not a firewall

From M3, worth restating because it is a common claim: NAT incidentally blocks unsolicited inbound traffic, because there is no translation entry for it. That is a **side effect of address translation**, not a security policy — it does nothing about outbound connections, nothing about malware already inside, and nothing at the application layer. Treat it as a firewall's accidental cousin.

### VPNs and tunnelling

A **VPN** encrypts traffic between you and a VPN server and makes it appear to originate there.

```
  [your packet] --> encrypted and wrapped in a NEW packet --> [VPN server]
                    --> unwrapped, sent on to the real destination
```

What a VPN actually gives you, stated honestly because it is widely oversold:

| Gives you | Does **not** give you |
|---|---|
| Confidentiality from your **local network and ISP** | Protection from the **VPN provider**, who now sees everything |
| Apparent location change | Anonymity — the destination still sees a single identifiable exit |
| Access to a private network remotely | Security for an already-compromised device |
| Protection on hostile Wi-Fi | Anything HTTPS does not already provide for web traffic |

**The honest summary:** a VPN **moves** your trust from your local network to the VPN provider. For reaching a corporate network, that is exactly right. For "privacy" when the sites you visit are already HTTPS, the benefit is much smaller than the marketing suggests — you are hiding the *hostnames* from your ISP and revealing them to someone else.

**IPsec** is the protocol suite: **AH** provides authentication and integrity, **ESP** provides those plus encryption, in **transport mode** (payload only) or **tunnel mode** (the whole original packet wrapped). Recall from M3 that **AH breaks through NAT**, because it authenticates the IP header that NAT rewrites — which is why NAT traversal exists.

---

## 9.9 The attacks worth naming

Each with the layer it attacks and its defence. This is a table to be able to recite.

| Attack | How it works | Defence |
|---|---|---|
| **Eavesdropping** | Read traffic on a shared medium or compromised path | Encryption (TLS) |
| **Man-in-the-middle** | Sit between two parties, impersonating each to the other | **Certificate validation** — this is what it is for |
| **ARP spoofing** (M2) | Forge an ARP reply claiming the gateway's IP; ARP has no authentication | Dynamic ARP inspection, static entries, port security, and TLS above |
| **DNS spoofing / cache poisoning** (M7) | Race a forged reply to a resolver | Query-ID and source-port randomisation; DNSSEC |
| **SYN flood** (M5) | Spoofed SYNs fill the backlog — **state exhaustion**, not volume | **SYN cookies**, backlog tuning, rate limits |
| **DoS / DDoS** | Exhaust bandwidth, connections or CPU from many sources | Over-provisioning, scrubbing services, anycast, rate limiting |
| **Amplification / reflection** | Send a small spoofed query to a service that replies hugely (DNS, NTP, memcached) to a victim | Disable open resolvers, **BCP 38 source-address filtering**, rate limits |
| **Session hijacking** | Steal or guess a session token and reuse it | `HttpOnly`, `Secure`, `SameSite`; rotate on privilege change; bind to context |
| **Replay** | Re-send a captured valid message | Nonces, sequence numbers, timestamps |
| **TCP RST injection** | Forge an RST to kill a connection | Encryption does not prevent it; sequence-number randomisation makes it harder |
| **Downgrade / stripping** | Force a weaker version, or HTTPS → HTTP | **HSTS**, TLS 1.3's transcript MAC, dropping old versions |
| **Phishing** | A valid certificate for a *lookalike* domain | User education, CAA records, certificate transparency monitoring |
| **XSS / CSRF / SQL injection** | Application-layer flaws | Output encoding; `SameSite` + CSRF tokens; **parameterized queries (DBMS M6)** |

### Three that deserve a sentence more

**DDoS cannot be solved by cryptography.** It is a capacity problem. The defences are economic and architectural — have more capacity than the attacker can buy, absorb it at the edge with anycast (M7), and filter upstream. This is why "we use HTTPS" is irrelevant to it.

**Amplification is why source-address spoofing matters so much.** An attacker sends a 60-byte DNS query with the victim's address as the source and the server sends a 4,000-byte reply to the victim — a 60× amplification, from a source that cost the attacker nothing. **BCP 38** — ISPs refusing to forward packets with source addresses not belonging to their customers — would largely end this, and remains incompletely deployed. It is a textbook collective-action problem.

**HSTS closes the stripping gap.** A user typing `example.com` makes a plaintext HTTP request first, which an attacker can intercept and keep on HTTP. `Strict-Transport-Security` tells the browser to use HTTPS for this domain for the next *n* seconds, so after one successful visit the plaintext request never happens again. The **HSTS preload list**, shipped with browsers, closes even the very first visit.

---

## Must remember

```
THREAT MODEL -- five attacks, five DIFFERENT defences. Conflating them is the
 source of bad answers:
 EAVESDROP   -> CONFIDENTIALITY (encryption)
 TAMPER      -> INTEGRITY (MAC/signature)
 IMPERSONATE -> AUTHENTICITY (certificates)
 REPLAY      -> FRESHNESS (nonce, sequence number, timestamp)
 DENY SERVICE-> capacity, filtering, rate limits -- CRYPTOGRAPHY CANNOT HELP
 passive attacker = undetectable, so confidentiality must be the DEFAULT

ENCODING vs HASHING vs ENCRYPTION
 encoding   base64/URL/UTF-8   NO KEY, reversible BY ANYONE, zero security value
 hashing    SHA-256            NO KEY, ONE WAY, FIXED size -> integrity
 MAC        HMAC-SHA256        keyed + one way -> integrity AND authenticity
 encryption AES/RSA            KEY, reversible WITH IT -> confidentiality
 the test: base64 is not encryption (no key); a hash is not encryption (no reverse)
 AVALANCHE: one character changed flipped 113 of 256 bits (44%, verified)
 hash properties: preimage, second preimage, COLLISION resistance
  -> MD5 and SHA-1 are BROKEN FOR COLLISIONS (practical, used to forge certs).
     Fine for accidental-corruption checksums, NEVER for signatures.
 collision resistance matters for signatures because you sign the HASH: two
 documents with one hash means one signature covers both.

PASSWORD HASHING IS A DIFFERENT PROBLEM
 MEASURED on this CPU: sha256 at 2,106,611 hashes/sec single-threaded
  -> 26^8 (8 lowercase chars) = 208 billion = 27.5 hours on ONE CORE
 PBKDF2-SHA256 measured: 1k rounds = 1,053/s | 10k = 256/s | 100k = 30/s
  -> from 2 MILLION/s to 30/s. A 70,000x reduction for 33 ms the user never notices.
 SALT = per-user random, NOT SECRET. Makes identical passwords hash differently,
  so one rainbow table cannot cover everyone and a breach does not reveal
  shared passwords. (verified: same password, two salts -> unrelated hashes)
 USE bcrypt/scrypt/ARGON2, not PBKDF2, because they are MEMORY-HARD, which is
  specifically what defeats GPUs (parallel arithmetic, limited memory bandwidth).

SYMMETRIC vs ASYMMETRIC
 symmetric  one shared key, FAST, n(n-1)/2 keys, KEY DISTRIBUTION IS THE PROBLEM
 asymmetric key PAIR, 100-1000x SLOWER, n pairs, SOLVES key distribution
 WHY BOTH: you cannot share a symmetric key over a channel you have not secured
  -- circular. So: asymmetric ONCE to agree a key, symmetric FOREVER after.
  That hybrid is TLS, SSH, PGP, Signal. It is the design, not a compromise.
 DIFFIE-HELLMAN derives a shared secret over a public channel without sending it.
 EPHEMERAL (DHE/ECDHE) = fresh keys per session, discarded -> FORWARD SECRECY:
  a stolen server key tomorrow CANNOT decrypt recorded past traffic.
  Old RSA key transport encrypted the session key WITH the server key, so a
  recording + a later key theft decrypts everything retroactively. Hence TLS 1.3
  REMOVED it and made ephemeral MANDATORY.
 SIGNATURES use the pair BACKWARDS: sign with the PRIVATE key, anyone verifies
  with the public one. You sign the HASH (signing is slow, hashes are fixed-size).

CERTIFICATES exist to solve ONE problem: is this public key really the server's?
 CHAIN: self-signed ROOT (pre-installed, the anchor) -> INTERMEDIATE (so the root
  key stays offline) -> LEAF. Validation checks: chain to a trusted root, every
  signature, THE NAME IS IN THE SAN LIST (CN is legacy and ignored), validity
  dates, revocation (CRL/OCSP/stapling), and the CAA record (M7).
 VERIFIED: 3 real certs, all TLS 1.3 + AEAD, ~90-DAY validity (short lifetimes are
  now the norm because ACME made renewal free and it limits compromise damage).
 VERIFIED BROKEN 3 WAYS: expired / hostname mismatch / self-signed, each rejected
  with its specific reason -- one per validation step.
 THE KEY DEMO: the SAME expired site with verification DISABLED connected fine,
  TLS 1.2, a good AEAD cipher. ENCRYPTION STILL WORKS; AUTHENTICATION IS WHAT IS
  LOST. Encryption without identity is encryption TO WHOEVER ANSWERED.
  -> that is the argument against every verify=False and curl -k.
 A CERT PROVES: control of the key, that a CA verified domain control, the name
  matches, it is in date. IT DOES NOT PROVE the site is honest or the one you MEANT.
  paypa1.com can hold a perfectly valid certificate. "Padlock = safe" is harmful.
 DV/OV/EV differ only in how much the CA checked; browsers removed EV indicators.

TLS HANDSHAKE
 1.2 = 2 RTT: ClientHello -> ServerHello+Certificate+ServerKeyExchange
              -> ClientKeyExchange+Finished -> Finished
 1.3 = 1 RTT: the client GUESSES the key-exchange group and sends its KEY SHARE in
   the ClientHello, so the server can reply with an ENCRYPTED certificate and
   Finished. Wrong guess -> HelloRetryRequest and you are back to 2 RTT.
   0-RTT resumption exists, with REPLAY caveats (idempotent requests only).
 WHAT IT ACHIEVES: agree version+cipher | AUTHENTICATE the server | optional
  mutual TLS | derive a shared key WITH FORWARD SECRECY | MAC THE WHOLE
  TRANSCRIPT (the Finished messages -- this is what defeats DOWNGRADE attacks)
  | choose the application protocol via ALPN (M8: where HTTP/2 is selected)
 COSTED at the 130 ms Mumbai-California floor (M0):
  HTTP/1.1+TLS1.2 = 3 RTT = 390 ms | +TLS1.3 = 2 RTT = 260 ms | HTTP/3 = 1 RTT = 130 ms
 TLS 1.3 REMOVED: RSA key transport and static DH (no forward secrecy), CBC
  (padding oracles: BEAST/Lucky13), RC4, MD5/SHA-1 signatures, COMPRESSION (CRIME),
  renegotiation. It leaves essentially ONE shape: ephemeral (EC)DHE + AEAD.
  Fewer options = fewer downgrades and misconfigurations.

WHAT HTTPS DOES NOT HIDE
 HIDDEN: the URL path and query, all headers, cookies, credentials, the body
 VISIBLE: the destination IP (routers need it), the port, THE HOSTNAME VIA SNI
  (plaintext in the ClientHello so the server can choose a certificate), the
  preceding DNS query, and TRAFFIC SIZE AND TIMING.
 -> an observer learns WHO and HOW MUCH, not WHAT. ECH is the fix for SNI.
 secrets in a URL are still wrong over HTTPS: browser history, access logs, the
  Referer header, and any TLS-terminating proxy all see it.
 TRAFFIC ANALYSIS identifies pages and videos from size/timing alone.

FIREWALLS
 stateless packet filter (headers only) | STATEFUL (+ connection table) |
 application/proxy (payload) | WAF (HTTP semantics)
 STATEFUL IS THE BIG WIN: a stateless filter allowing outbound must allow all
 inbound replies to high ports. Stateful admits only packets belonging to
 connections STARTED FROM INSIDE -- hence "allow established and related".
 THIS NETWORK, OBSERVED: ICMP echo blocked, external UDP/53 blocked, only the
 operator's resolvers answer, TCP/443 to public DNS providers blocked, ordinary
 web traffic allowed. A coherent policy: permit browsing, FORCE DNS through
 resolvers the operator controls (filtering + logging + visibility -- exactly
 what DoH bypasses), deny diagnostics.
 OVER-BLOCKING ICMP breaks PATH-MTU DISCOVERY (type 3 code 4) -> BLACK HOLES
 where small packets work and large ones hang.
 NAT IS NOT A FIREWALL: blocking unsolicited inbound is a SIDE EFFECT of having
 no translation entry. Nothing about outbound, internal threats or layer 7.

VPN MOVES YOUR TRUST from the local network to the VPN PROVIDER, who now sees
 everything. Right for reaching a private network; much weaker than advertised as
 "privacy" when the sites are already HTTPS -- you hide hostnames from the ISP and
 reveal them to someone else. No anonymity, no help on a compromised device.
IPsec: AH = authentication + integrity; ESP = + encryption.
 transport mode (payload) vs tunnel mode (the whole packet wrapped).
 AH BREAKS THROUGH NAT because it authenticates the header NAT rewrites (M3).

ATTACKS
 MITM            -> CERTIFICATE VALIDATION (this is what it is for)
 ARP spoofing    -> DAI, static entries, port security + TLS above (M2)
 DNS poisoning   -> query-ID + source-port randomisation, DNSSEC (M7)
 SYN flood       -> SYN COOKIES. It is STATE exhaustion, not volume (M5)
 DDoS            -> capacity, anycast, scrubbing, rate limits. CRYPTO CANNOT HELP.
 AMPLIFICATION   -> a 60-byte spoofed query provokes a 4,000-byte reply to the
                    victim: 60x. Fix = no open resolvers + BCP 38 source-address
                    filtering by ISPs -- a collective-action problem, still partial.
 session hijack  -> HttpOnly, Secure, SameSite, rotate on privilege change
 replay          -> nonces, sequence numbers, timestamps
 downgrade/strip -> HSTS (+ the PRELOAD LIST for the very first visit), and TLS
                    1.3's transcript MAC
 phishing        -> a VALID cert for a LOOKALIKE domain. CAA, CT monitoring, users.
 XSS/CSRF/SQLi   -> output encoding; SameSite + tokens; PARAMETERIZED QUERIES (DBMS M6)
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "base64 is a form of encryption" | There is **no key** — anyone can reverse it. It is a representation format with zero security value |
| "Hashing is two-way encryption with a fixed key" | A hash has **no key and no inverse**. Nobody can reverse it, including you |
| "We encrypt passwords in the database" | You **hash** them, with a salt and a deliberately slow function. Encrypting means someone holds a key that can recover them |
| "SHA-256 is fine for passwords" | Measured at **2.1 million hashes/sec** on one CPU core. You need a *slow*, memory-hard function — bcrypt, scrypt or argon2 |
| "A salt has to be secret" | It does not. It is stored next to the hash. Its job is to make identical passwords hash differently and defeat precomputed tables |
| "MD5 is weak" | It is **broken for collisions** — practical collisions exist and have forged certificates. Acceptable only for accidental-corruption checksums |
| "Asymmetric encryption is just better" | It is **100–1000× slower**. It is used once to agree a symmetric key, and symmetric encryption does the actual work |
| "You encrypt with the private key" | You **sign** with the private key and **encrypt** with the public one. Signing and encrypting use the pair in opposite directions |
| "Forward secrecy means the connection is encrypted" | It means a **future** theft of the server's long-term key cannot decrypt **past recorded** sessions, because the session keys were ephemeral and are gone |
| "A certificate proves the site is safe" | It proves control of the key and the domain. `paypa1.com` can hold a perfectly valid certificate — HTTPS checks the name in the bar, not whether it is the name you meant |
| "The certificate's common name is what's checked" | The **SAN** list. `CN` is legacy and browsers have ignored it for years |
| "Disabling certificate verification makes it less encrypted" | Verified: the connection still negotiated TLS 1.2 with a strong AEAD cipher. You lose **authentication**, which turns strong encryption into strong encryption with an unknown party |
| "TLS 1.3 is faster because the crypto is faster" | Because it is **one round trip instead of two** — the client guesses the key-exchange group and sends its key share in the first message |
| "HTTPS hides which sites I visit" | The destination IP and the **SNI hostname** are both visible; SNI is plaintext in the ClientHello. The path and query are hidden; the fact of the visit is not |
| "It's fine to put a token in the URL over HTTPS" | The URL lands in browser history, server logs, the `Referer` header and any TLS-terminating proxy |
| "Encrypted traffic reveals nothing" | **Size and timing** identify pages and videos without any decryption |
| "A stateless firewall is enough" | It must allow all inbound replies to high ports. A stateful one admits only packets belonging to connections started from inside |
| "Blocking all ICMP is good hygiene" | It breaks **path-MTU discovery**, giving black-hole connections where small packets work and large ones hang |
| "NAT is a firewall" | It blocks unsolicited inbound traffic as a **side effect** of having no translation entry. No policy, nothing outbound, nothing at layer 7 |
| "A VPN makes me anonymous" | It **moves** your trust to the VPN provider, who sees everything. The destination still sees one identifiable exit point |
| "A SYN flood is a bandwidth attack" | It is **state exhaustion** — spoofed SYNs fill the backlog at almost no cost to the attacker. SYN cookies remove the state entirely |
| "HTTPS protects against DDoS" | Cryptography is irrelevant to it. DDoS is a capacity and filtering problem |
| "Amplification needs a powerful attacker" | A 60-byte spoofed query provoking a 4,000-byte reply is 60× leverage. The fix is BCP 38 source-address filtering, which is a collective-action problem |
| "HSTS encrypts the first request" | It ensures there is **no** plaintext first request after the first successful visit. The **preload list** covers even that first visit |

---

## Interview Q&A bank

**Q1. Hashing vs encryption vs encoding?**
Encoding is a representation change with no key, reversible by anyone — base64 — and has no security value. Hashing is a one-way, fixed-size fingerprint with no key, used for integrity. Encryption uses a key and is reversible with it, providing confidentiality. The test: base64 is not encryption because there is no key, and a hash is not encryption because nothing can reverse it.

**Q2. What are the three properties of a cryptographic hash?**
Preimage resistance — you cannot find an input for a given hash. Second preimage resistance — given one input you cannot find another with the same hash. Collision resistance — you cannot find any two inputs that collide. MD5 and SHA-1 are broken for the third.

**Q3. Why does collision resistance matter for signatures?**
Because you sign the hash, not the document. If an attacker can produce two documents with the same hash, a signature on one is a valid signature on the other — which is exactly how forged MD5 certificates were produced.

**Q4. How should passwords be stored?**
Hashed with a per-user salt using a deliberately slow, memory-hard function — argon2, bcrypt or scrypt. Measured here: plain SHA-256 runs at 2.1 million hashes per second on a single core, while PBKDF2 at 100,000 rounds drops that to 30 — a 70,000-fold reduction for 33 milliseconds the user never notices.

**Q5. What does a salt do, and does it need to be secret?**
It makes identical passwords hash to different values, so one precomputed table cannot cover every user and a breach does not reveal which users share a password. It is stored alongside the hash and does not need to be secret.

**Q6. Symmetric vs asymmetric, and why use both?**
Symmetric uses one shared key and is fast; asymmetric uses a key pair and is hundreds of times slower but solves key distribution. You cannot share a symmetric key over a channel you have not yet secured, which is circular — so asymmetric cryptography is used once to agree a symmetric key, and symmetric encryption carries the traffic.

**Q7. What is Diffie-Hellman?**
A way for two parties to derive a shared secret over a public channel without ever transmitting it: each combines its own private value with the other's public value and reaches the same result, which an eavesdropper cannot compute.

**Q8. What is forward secrecy and why does it matter?**
Using ephemeral keys per session, discarded afterwards, so that stealing the server's long-term private key later cannot decrypt recorded past traffic. Under old RSA key transport the session key was encrypted with the server's key, so a recording plus a later theft decrypted everything retroactively. TLS 1.3 removed that option and made ephemeral exchange mandatory.

**Q9. How does a digital signature work?**
You hash the message and encrypt the hash with your private key. Anyone with your public key can verify it, which proves the holder of the private key produced it and that the content has not changed.

**Q10. What problem do certificates solve?**
Asymmetric cryptography only helps if you know the public key really belongs to the server — otherwise an attacker supplies their own and you have a perfectly encrypted channel to the attacker. A certificate is a CA's signed statement binding a key to a name.

**Q11. Describe the chain of trust.**
A self-signed root certificate pre-installed in your OS or browser is the anchor. It signs intermediates — which exist so the root's key can stay offline — and an intermediate signs the server's leaf certificate. The client verifies every signature up to a root it already trusts.

**Q12. What does a client check during validation?**
That the chain reaches a trusted root, that every signature is valid, that the requested name appears in the SAN list, that the certificate is within its validity dates, that it has not been revoked, and that the domain's CAA record permits that CA.

**Q13. What happens if you disable certificate verification?**
Encryption continues to work perfectly. Verified: connecting to a site with an expired certificate and verification off negotiated TLS 1.2 with a strong AEAD cipher. What is lost is authentication — so you have a confidential conversation with whoever answered, which is the attacker's goal.

**Q14. What does a certificate *not* prove?**
That the site is honest, reputable, or the one you intended to visit. A lookalike domain can hold a perfectly valid certificate, which is why phishing sites show padlocks. HTTPS verifies the name in the address bar, not your intent.

**Q15. Walk me through the TLS handshake.**
The client sends a ClientHello with its supported versions, cipher suites, a random value and the SNI. The server replies with its choices, its certificate chain and its key-exchange parameters. Both derive a shared secret, exchange Finished messages that MAC the whole transcript, and switch to symmetric encryption. In TLS 1.3 the client guesses the key-exchange group and includes its key share up front, which collapses this to one round trip.

**Q16. How does TLS 1.3 save a round trip?**
In 1.2 the client had to wait to learn which key-exchange group the server wanted. In 1.3 it guesses and sends a key share immediately, so the server can derive the secret and reply with an already-encrypted certificate and Finished. A wrong guess triggers a HelloRetryRequest and costs the extra round trip.

**Q17. What do the Finished messages accomplish?**
They are a MAC over the entire handshake transcript, so any tampering with the negotiated version or cipher suite is detected. That is what defeats downgrade attacks.

**Q18. What did TLS 1.3 remove, and why?**
RSA key transport and static Diffie-Hellman, because they have no forward secrecy; CBC ciphers, because of padding-oracle attacks; RC4; MD5 and SHA-1 signatures; compression, because of CRIME; and renegotiation. It deliberately leaves essentially one shape — ephemeral key exchange plus an AEAD cipher — because fewer options means fewer downgrade paths and misconfigurations.

**Q19. What does HTTPS not hide?**
The destination IP address and port, because routers need them; the hostname, because SNI is sent in plaintext so the server can choose a certificate; the DNS query that preceded it unless you use DoH or DoT; and the size and timing of your traffic. An observer learns who you talked to and how much, but not what you said.

**Q20. Is it safe to put a token in a URL over HTTPS?**
No. Although the URL is encrypted on the wire, it ends up in browser history, server access logs, the `Referer` header sent to third parties, and anything that terminates TLS in the middle.

**Q21. Stateless vs stateful firewall?**
A stateless filter judges each packet by its headers alone, so permitting outbound traffic forces it to permit all inbound replies to high ports. A stateful firewall tracks a connection table and admits only packets belonging to connections initiated from inside — which is why "allow established and related" is the first rule everywhere.

**Q22. Is NAT a security feature?**
Incidentally and partially. Unsolicited inbound traffic has no translation entry so it is dropped, but that is a side effect of address translation rather than a policy. It does nothing about outbound connections, internal compromise or the application layer.

**Q23. What does a VPN actually give you?**
Confidentiality from your local network and ISP, and an apparent change of location. It moves your trust to the VPN provider, who now sees everything you do. It gives no anonymity, and for web traffic already protected by HTTPS the extra benefit is mainly hiding hostnames from your ISP — and revealing them to someone else.

**Q24. Name some attacks and their defences.**
Man-in-the-middle, defeated by certificate validation. ARP spoofing, mitigated by dynamic ARP inspection and by TLS above it. DNS cache poisoning, mitigated by randomisation and DNSSEC. SYN flood, defeated by SYN cookies. DDoS, which needs capacity and filtering rather than cryptography. Session hijacking, mitigated by cookie attributes and rotation. And HTTPS stripping, closed by HSTS.

**Q25. Why is amplification such an effective attack?**
Because the attacker spoofs the victim's address and asks a service for something small that produces a large reply — a 60-byte DNS query can provoke a 4,000-byte response, so 60× the traffic arrives at the victim at no cost to the attacker. BCP 38, where ISPs refuse to forward packets with source addresses they do not own, would largely end it, and remains incompletely deployed.

**Q26. What is HSTS and what gap does it close?**
A user typing a bare domain makes a plaintext HTTP request first, which an attacker can intercept and keep on HTTP. `Strict-Transport-Security` tells the browser to use HTTPS for that domain for a set period, so after one successful visit the plaintext request never happens. The preload list shipped with browsers closes even the first visit.

**Q27. Can cryptography solve DDoS?**
No. It is a capacity and filtering problem — absorb it at the edge with anycast, over-provision, use scrubbing services, and rate limit. Encryption is orthogonal and adds CPU cost that can make you marginally easier to exhaust.

---

## Practice

1. For each of base64, SHA-256, HMAC-SHA256 and AES, say whether it has a key, whether it is reversible, and which security property it provides.
2. A colleague stores passwords as `sha256(password)`. Give three separate problems and the fix for each.
3. Why is a fast hash function a liability for passwords but a virtue for file integrity?
4. Explain why TLS uses both asymmetric and symmetric cryptography, in three sentences, without using the word "secure".
5. An attacker records your encrypted session today and steals the server's private key in a year. What can they read under RSA key transport, and under ECDHE? Name the property.
6. Which is signed with which key: a certificate, a TLS Finished message, a JWT? For each, say what the verifier proves.
7. A client connects to `https://example.com` and gets a certificate valid for `*.example.net`. At which validation step does this fail, and what should the client do?
8. You set `verify=False` to fix a certificate error in production. Describe precisely what you have given up and what an attacker can now do.
9. List everything a passive observer on the path learns about `GET https://bank.example/accounts/123?token=xyz`, and everything they do not.
10. A firewall blocks all ICMP. A user reports that SSH works but `scp` of large files hangs. Explain the chain of causation.
11. Your API is behind a load balancer that terminates TLS. What can the load balancer see, and what does that mean for secrets in URLs and for `HttpOnly` cookies?
12. Classify each as confidentiality, integrity, authenticity, freshness or availability: HSTS, a nonce, a certificate, AES-GCM's tag, anycast, `SameSite`, SYN cookies.

**Answers to 5, 7 and 10:**

> **5.** Under **RSA key transport**, the client encrypted the session key with the server's public key and sent it. So the recording contains the session key, encrypted under a key the attacker now holds — they decrypt the session key and then the entire session, **retroactively**. Under **ECDHE**, the session key was derived from ephemeral key pairs that both sides discarded immediately; the server's long-term key was used only to *sign* the exchange, not to protect it. The stolen key lets an attacker impersonate the server **in future** connections but reveals nothing about past ones. The property is **forward secrecy**, and it is why TLS 1.3 removed RSA key transport entirely.
>
> **7.** Step **3** — the name check. The client asked for `example.com`, and the certificate's SAN list covers `*.example.net`, which does not match on any reading (and note a wildcard matches only one label, so it would not even cover `a.b.example.net`). The client must **abort the connection and show an error**, not prompt or proceed, because this is indistinguishable from a man-in-the-middle presenting a certificate it legitimately holds for a different domain. Verified in §9.5: `wrong.host.badssl.com` was rejected with exactly "Hostname mismatch".
>
> **10.** Blocking all ICMP breaks **path-MTU discovery**, which depends on **ICMP type 3 code 4**, "fragmentation needed, DF set". An interactive SSH session sends small packets that fit any MTU, so it works. `scp` sends full-size segments; somewhere on the path a link has a smaller MTU, the router drops the packet and sends the type 3 code 4 that would tell the sender to use smaller segments — and the firewall discards it. The sender never learns, so it retransmits the same oversized segment forever. The transfer hangs rather than failing, which is the signature of a **black-hole connection** (M3 §3.10).

---

## Exit checklist

```
[ ] I can name five attacks and the five DIFFERENT defences they need
[ ] I know cryptography cannot address denial of service
[ ] I can distinguish encoding, hashing, MACs and encryption on key/reversibility
[ ] I can give the one-line test for why base64 is not encryption
[ ] I can explain the avalanche effect and quote the measured figure
[ ] I know the three hash properties and that MD5/SHA-1 are broken for collisions
[ ] I can explain why collision resistance matters specifically for signatures
[ ] I know why a fast hash is wrong for passwords, with the measured rate
[ ] I know what a salt does and that it need not be secret
[ ] I know to use argon2/bcrypt/scrypt and why MEMORY hardness matters
[ ] I can compare symmetric and asymmetric on five axes
[ ] I can explain why both are used, from the circularity of key distribution
[ ] I can explain Diffie-Hellman in one sentence
[ ] I can explain forward secrecy and the RSA-key-transport failure it fixes
[ ] I know signing uses the PRIVATE key and that you sign the HASH
[ ] I can state the single problem certificates solve
[ ] I can draw the chain of trust and say why intermediates exist
[ ] I can list all six validation steps
[ ] I know the SAN list is checked, not the CN
[ ] I can describe the three ways validation was broken, and the reason each gave
[ ] I can explain what disabling verification costs, and what it does NOT cost
[ ] I can say what a certificate does and does not prove, including the lookalike case
[ ] I can draw both the TLS 1.2 and TLS 1.3 handshakes
[ ] I can explain exactly how TLS 1.3 saves a round trip
[ ] I know what the Finished messages protect against
[ ] I can list the six things a handshake achieves, including ALPN
[ ] I can cost the handshakes in RTTs and in milliseconds on a real path
[ ] I can list what TLS 1.3 removed and why, for at least four items
[ ] I can list what HTTPS hides and what it leaves visible, with reasons
[ ] I know SNI is plaintext and that ECH is the fix
[ ] I know why secrets in URLs are wrong even over HTTPS
[ ] I know traffic analysis works without decryption
[ ] I can explain why stateful firewalls are the big improvement
[ ] I can read this network's filtering as a coherent policy
[ ] I know over-blocking ICMP causes black holes
[ ] I can argue that NAT is not a firewall
[ ] I can say what a VPN moves rather than what it adds
[ ] I know AH breaks through NAT and why
[ ] I can recite the attack/defence table for at least ten rows
[ ] I can explain amplification, the leverage figure, and BCP 38
[ ] I can explain HSTS and the gap the preload list closes
```

---

## Next

**Part 12: M10 — What Happens When You Type a URL.** The integration module, and the best revision device in the subject: one continuous end-to-end trace, with **every phase measured on this machine**. URL parsing, the HSTS check, the four DNS caches, resolution, ARP for the gateway, the TCP handshake, the TLS handshake, the HTTP request, the server with its reverse proxy, load balancer and CDN, the response, rendering and subresources, and connection reuse. Then the **same answer at three depths** — 30 seconds, 3 minutes, 10 minutes — because the question is asked at all three; where each step fails and what the user sees; a **measured latency budget** showing that setup is 57% of a first request; and the remaining application protocols in one table.
