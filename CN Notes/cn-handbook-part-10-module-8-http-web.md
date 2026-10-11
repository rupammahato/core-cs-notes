# Computer Networks Placement Handbook — Part 10
# Module 8: HTTP and the Web

**Module 8 · 4 hours · Tier 1 · Requires: M5 (TCP), M6 (head-of-line blocking), M7 (DNS)**

---

## Why this module matters

HTTP is now weighted like a core subject rather than an application-layer footnote, and for a backend engineer it is the protocol you actually live in. In interviews it comes up **more often than routing protocols do**.

The questions are specific and practical:

- **GET vs POST vs PUT vs PATCH** — which are safe, which idempotent
- **301 vs 302 vs 307; 401 vs 403; 500 vs 502 vs 503 vs 504**
- **How does HTTP caching work? What is an `ETag`?**
- **Cookies vs sessions vs tokens** — and "is HTTP stateless?"
- **HTTP/1.1 vs 2 vs 3** — what problem did each solve
- **What is CORS and why does my request fail only in the browser?**

That last one is the single most common source of genuine confusion in web development, and §8.7 settles it with a measurement.

The organising principle:

> **HTTP is a stateless request/response protocol over a reliable byte stream, and everything it has acquired since 1991 is an answer to one of two pressures: statelessness is inconvenient, so we bolted state on with cookies and tokens; and one request per connection is slow, so we spent thirty years removing round trips — keep-alive, then pipelining, then multiplexing, then abandoning TCP altogether.**

**How this module was verified.** Everything here is live traffic from this machine. A raw request and response captured byte for byte over a socket; status codes from real servers; **HTTP/2 negotiated for real over ALPN**; a genuine **304 Not Modified** and the bytes it saved; redirect chains followed; a **real CORS preflight**; and keep-alive timed. One measurement did not behave as intended and §8.9 says so.

---

## 8.1 A request and response, byte for byte

Sent over a plain socket so nothing is hidden:

```
  REQUEST (note the BLANK LINE terminating the headers):
   GET / HTTP/1.1
   Host: example.com
   User-Agent: cn-handbook/1.0
   Accept: */*
   Connection: close
   ''
```

```
  RESPONSE: 932 bytes total, 339 of headers, 589 of body
   HTTP/1.1 200 OK
   Date: Sun, 11 Oct 2026 04:02:00 GMT
   Content-Type: text/html; charset=utf-8
   Transfer-Encoding: chunked
   Connection: close
   Server: cloudflare
   Last-Modified: Fri, 09 Oct 2026 20:18:28 GMT
   Allow: GET, HEAD
   Accept-Ranges: bytes
   Age: 13778
   cf-cache-status: HIT
   CF-RAY: a48af77e6d6e9a95-NAG
   alt-svc: h3=":443"; ma=86400

  first 100 bytes of body:
   b'241\r\n<!doctype html><html lang=en><head><meta charset=utf-8>...'
```

### The structure

```
  REQUEST                          RESPONSE
  METHOD path HTTP/version         HTTP/version STATUS reason
  Header: value                    Header: value
  Header: value                    Header: value
  <blank line>                     <blank line>
  [body]                           [body]
```

**The blank line is load-bearing.** It is the only thing telling the parser the headers have ended, which is also why **header injection** — smuggling a CR/LF into a header value — is a whole vulnerability class: an attacker who can insert `\r\n\r\n` can terminate the headers early and control what the parser treats as the body.

### Five things in that real response worth reading

**`Transfer-Encoding: chunked`** — there is no `Content-Length`. The body arrives in length-prefixed chunks, which is why the raw bytes begin `241\r\n` — hex `0x241` = 577 bytes for the first chunk. Chunking exists so a server can start sending before it knows the total size, and it is the mechanism behind streaming responses.

**`Age: 13778`** and **`cf-cache-status: HIT`** — this response came from a Cloudflare cache and is **nearly four hours old**. No origin server was contacted. Caching is not theoretical; it is what served this request.

**`alt-svc: h3=":443"; ma=86400`** — the server is advertising that it also speaks **HTTP/3** on port 443 and that the client may remember this for a day. That header is how HTTP/3 gets discovered at all, since you cannot negotiate QUIC over a TCP connection you are already using.

**`Allow: GET, HEAD`** — the server is telling us what it accepts. Sending a `POST` here would get a `405 Method Not Allowed`.

**`Host: example.com` in the request** is mandatory in HTTP/1.1 and the reason **virtual hosting** works: one IP address can serve thousands of sites because the request names which one it wants. HTTP/1.0 had no `Host` header, so one address meant one site. (It is also why TLS needed **SNI** — the certificate must be chosen before the encrypted `Host` header can be read.)

---

## 8.2 Methods, safe and idempotent

```
  method    safe   idempotent  meaning
  GET       yes    yes         retrieve
  HEAD      yes    yes         headers only
  OPTIONS   yes    yes         what is allowed
  TRACE     yes    yes         echo (usually disabled)
  PUT       no     YES         replace the whole resource
  DELETE    no     YES         remove it
  POST      no     no          create / process -- NOT idempotent
  PATCH     no     no          partial update -- usually not idempotent
```

Two definitions that get conflated and shouldn't:

- **Safe** — does not change server state. A crawler or a prefetcher may call it freely.
- **Idempotent** — calling it *N* times has the same effect as calling it once.

**The pair that makes the distinction clear is `PUT`:** it is **idempotent but not safe.** `PUT /user/1 {name: "Asha"}` changes things — so not safe — but doing it five times leaves exactly the same state as doing it once, so it is idempotent. `DELETE` is the same: the first call removes the resource, the rest are no-ops on an already-absent resource.

**And `POST` is neither**, which is why your browser warns before re-submitting a form: replaying it might create a second order. This is also why **idempotency matters operationally** — a client that times out cannot safely retry a `POST`, which is why payment APIs make you supply an *idempotency key*.

`PATCH` is usually not idempotent: "append to this list" applied twice appends twice. A `PATCH` written as a declarative diff can be idempotent, which is why the spec leaves it unspecified rather than forbidding it.

Verified against a real server:

```
  a real OPTIONS response: 200, Allow: GET, HEAD, OPTIONS
  HEAD vs GET on the same URL: HEAD body 0 bytes, GET body 577 bytes
```

`HEAD` returns the headers a `GET` would, with **no body** — useful for checking existence, size or freshness without transferring anything.

---

## 8.3 Status codes

```
  1xx informational   -- rare; 100 Continue, 101 Switching Protocols (WebSockets)
  2xx success         -- 200 OK, 201 Created, 204 No Content, 206 Partial Content
  3xx redirection     -- 301, 302, 304, 307, 308
  4xx CLIENT error    -- you sent something wrong
  5xx SERVER error    -- the server failed
```

Real responses, captured:

```
  200 OK                     a normal page
  404 Not Found              missing path
  301 MOVED PERMANENTLY      redirect
  401 UNAUTHORIZED           unauthenticated
  403 FORBIDDEN              forbidden
  418 I'M A TEAPOT           a joke code that really exists
  500 INTERNAL SERVER ERROR  server error
  503 SERVICE UNAVAILABLE    unavailable
```

### The confusable pairs that actually get asked

| Pair | Distinction |
|---|---|
| **401 vs 403** | 401 = **not authenticated** — "I don't know who you are, log in". 403 = **authenticated but not permitted** — "I know who you are and the answer is no". Re-sending credentials helps with 401 and never with 403 |
| **404 vs 410** | 404 = not found, might come back. 410 = **Gone**, deliberately and permanently removed. Search engines treat 410 as final |
| **301 vs 308** | Both permanent. **301 may change the method** (historically POST→GET); 308 **must preserve** it |
| **302 vs 307** | Both temporary, same distinction: 307 **must preserve** the method and body |
| **500 vs 502 vs 503 vs 504** | 500 = the app threw. **502 Bad Gateway** = a proxy got an invalid response from upstream. **503 Service Unavailable** = temporarily down or overloaded, often with `Retry-After`. **504 Gateway Timeout** = a proxy waited for upstream and gave up |
| **200 vs 201 vs 204** | 200 = here is the result. 201 = **created**, usually with a `Location` header. 204 = success, **deliberately no body** |

**The 502/503/504 distinction is the operationally useful one**, and it is worth being crisp about: all three come from the *proxy or load balancer*, not the application, and they say different things about where the failure is. 502 means upstream answered with garbage; 503 means nothing was available to ask; 504 means upstream was asked and never replied. Debugging starts in a different place for each.

### Redirects, followed for real

```
  follow_redirects=False -> 302, Location: /relative-redirect/2
  follow_redirects=True  -> 200 after 3 hops:
     302 https://httpbin.org/redirect/3        -> /relative-redirect/2
     302 https://httpbin.org/relative-redirect/2 -> /relative-redirect/1
     302 https://httpbin.org/relative-redirect/1 -> /get
     200 https://httpbin.org/get
```

Each hop is a **full round trip**, which is why redirect chains are a real performance problem — three hops on a 100 ms path cost 300 ms before the real response starts. And note the `Location` values are **relative**, which is permitted; the client resolves them against the current URL.

**One practical warning:** 301 and 308 are **cached by browsers, aggressively and sometimes indefinitely**. A mistaken permanent redirect is extremely hard to undo because you cannot reach into every user's browser cache. Test with 302 first and promote to 301 only when you are sure.

---

## 8.4 Caching

The most valuable part of HTTP for performance, and the one with the most moving parts.

```
  FRESHNESS -- can the cache serve this without asking at all?
    Cache-Control: max-age=3600        seconds from now
    Cache-Control: no-cache            must REVALIDATE (not "do not store")
    Cache-Control: no-store            genuinely do not store
    Cache-Control: private             only the browser, not a shared CDN
    Cache-Control: public              shared caches may store it
    Cache-Control: immutable           never revalidate (for hashed asset names)
    Expires: <date>                    the HTTP/1.0 ancestor; max-age wins

  VALIDATION -- stale copy: is it still good?
    ETag: "abc123"       <-> If-None-Match: "abc123"     (an opaque version)
    Last-Modified: date  <-> If-Modified-Since: date      (one-second resolution)
    -> unchanged: 304 NOT MODIFIED, no body
```

### Verified: a real 304

```
  first request : 200, 317 bytes
     etag: abc123

  conditional request with If-None-Match: abc123
   -> 304 NOT MODIFIED, 0 bytes of body
   saved 317 bytes (100% of the payload)
```

**The entire payload, saved by a conditional request.** The 304 carries headers only — no body at all — so the client reuses what it already has. On a real page of images and scripts that is the difference between a 2 MB reload and a few hundred bytes of headers.

And explicit freshness, which avoids even the conditional request:

```
  cache-control: public, max-age=120
  date: Sun, 11 Oct 2026 04:02:08 GMT
```

Within those 120 seconds the cache serves the copy **without contacting the server at all** — zero round trips. That is the difference worth holding onto:

> **Freshness avoids the request entirely. Validation still costs a round trip but avoids the body.** The first is dramatically better, which is why `max-age` plus content-hashed filenames — `app.a4f91c.js` with `immutable` — is the modern pattern: the URL changes when the content does, so the cache can be told to never revalidate.

### `ETag` vs `Last-Modified`

| | `ETag` | `Last-Modified` |
|---|---|---|
| Value | An opaque server-chosen token | A timestamp |
| Resolution | Exact | **One second** — two changes in the same second are indistinguishable |
| Detects | Any change | Only changes that move the clock |
| Strong vs weak | `"abc"` strong (byte-identical) vs `W/"abc"` weak (semantically equivalent) | n/a |
| Cost | Server must compute or store it | Free if the filesystem has mtime |

### Two naming traps

**`no-cache` does not mean "do not cache".** It means "cache it, but **revalidate** before every use" — so you still get 304s and save the body. The directive that means do not store is **`no-store`**. Getting these backwards is one of the most common header mistakes.

**`Vary` is what keeps shared caches correct.** `Vary: Accept-Encoding` tells a cache that the response depends on that request header, so it must not serve a gzipped body to a client that cannot decode it. Forgetting `Vary` on a content-negotiated response is how a CDN starts serving the wrong language or the wrong format to everyone.

---

## 8.5 Statelessness, cookies, sessions and tokens

**HTTP is stateless**: each request is independent and the server is not required to remember anything between them. That is what makes HTTP scalable — any server can handle any request — and it is inconvenient for anything resembling a login.

```
  server -> client:  Set-Cookie: session=abc123; HttpOnly; Secure; SameSite=Lax; Max-Age=3600
  client -> server:  Cookie: session=abc123        (on every subsequent request)
```

Cookie attributes, and each exists to stop something specific:

| Attribute | Effect | Prevents |
|---|---|---|
| **`HttpOnly`** | JavaScript cannot read it | Cookie theft via **XSS** |
| **`Secure`** | Sent only over HTTPS | Interception on a plaintext connection |
| **`SameSite=Strict/Lax/None`** | Controls sending on cross-site requests | **CSRF** |
| **`Domain` / `Path`** | Scope | Over-broad sharing |
| **`Max-Age` / `Expires`** | Lifetime | Indefinite validity |

### Session vs token — the architectural choice

| | Server-side session | Token (e.g. JWT) |
|---|---|---|
| The cookie holds | An opaque **session ID** | The **claims themselves**, signed |
| Server stores | Session data, per user | **Nothing** |
| Validating a request | A lookup in a store | **Verify a signature** |
| Revocation | **Immediate** — delete the session | **Hard** — valid until it expires |
| Scaling | Needs shared storage or sticky sessions | **Stateless**, any server can verify |
| Size on the wire | Tiny | Larger, on every request |
| Right when | Revocation matters; sessions are long | Many services; short-lived tokens |

**The honest answer, which is what a good interviewer wants:** *"Sessions are stateful but revocable; tokens are stateless but hard to revoke. The usual compromise is short-lived access tokens plus a refresh token you can revoke, which gets you most of both."*

**And the correction worth making:** "stateless authentication" does not make the *application* stateless — the state moved onto the client and into every request. A JWT large enough to carry real claims is sent with every single call, which is a bandwidth and latency cost people forget to count.

---

## 8.6 HTTP/1.0 → 1.1 → 2 → 3

Thirty years of removing round trips, each version fixing the previous one's bottleneck.

### The progression

| | HTTP/1.0 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|---|
| Year | 1996 | 1997 | 2015 | 2022 |
| Transport | TCP, **one request per connection** | TCP, **keep-alive** | TCP, **one** connection | **QUIC over UDP** |
| Framing | Text | Text | **Binary** | Binary |
| Concurrency | None | Pipelining (failed) | **Multiplexed streams** | Multiplexed, **independent** |
| Header compression | None | None | **HPACK** | **QPACK** |
| Head-of-line blocking | Yes | Yes, at the application | Removed at HTTP, **remains in TCP** | **Removed entirely** |
| `Host` header | Optional | **Required** | Via `:authority` | Via `:authority` |
| Server push | — | — | Yes (**abandoned**) | Deprecated |
| Setup round trips (with TLS) | 2–3 | 2–3 | 2–3 | **1, or 0 on resume** |

### Verified: the version is chosen by ALPN, not by the URL

```
  https://example.com/             http2=True  -> negotiated HTTP/2   status 200
  https://example.com/             http2=False -> negotiated HTTP/1.1 status 200
  https://www.google.com/          http2=True  -> negotiated HTTP/2   status 200
  https://www.google.com/          http2=False -> negotiated HTTP/1.1 status 200
  https://www.cloudflare.com/      http2=True  -> negotiated HTTP/2   status 200
  https://www.cloudflare.com/      http2=False -> negotiated HTTP/1.1 status 200
```

**The same URL, two protocol versions, decided during the TLS handshake.** HTTP/2 is negotiated by **ALPN** — an extension in the TLS `ClientHello` listing the protocols the client speaks. So `https://` tells you nothing about the wire protocol, and there is no such thing as an "HTTP/2 URL". HTTP/3 is different again: it is **advertised** by the `alt-svc` header seen in §8.1 and used on the *next* connection, because you cannot upgrade a TCP connection to QUIC.

### Head-of-line blocking — the concept that ties M6 to M8

This is the most important idea in the section, and it exists at **two layers**:

```
 HTTP/1.1, APPLICATION-layer HOL blocking:
   one connection carries one request at a time. A slow response blocks every
   request queued behind it. PIPELINING let you send several requests at once
   but responses still had to come back IN ORDER -- so the blocking remained,
   and buggy proxies made it worse. It was effectively never deployed.
   Browsers worked around it by opening 6 connections per origin.

 HTTP/2 fixes that: many STREAMS multiplexed over ONE TCP connection,
   interleaved at the frame level, responses in any order.

 BUT -- TCP-layer HOL blocking remains:
   TCP delivers bytes IN ORDER. One lost segment stalls the receive buffer,
   so EVERY multiplexed stream waits for that one retransmission -- even
   streams whose data already arrived. HTTP/2 made this WORSE than HTTP/1.1
   in some lossy conditions, because 6 connections meant a loss stalled 1/6
   of the work, whereas 1 connection means it stalls everything.

 HTTP/3 fixes THAT: QUIC gives each stream its OWN sequence space, so a loss
   stalls only the stream that lost something. Reliability is implemented per
   stream in user space, which TCP cannot do because it is one byte stream.
```

**That is the real answer to "why did HTTP/3 abandon TCP?"** Not for speed in the abstract — because TCP's in-order delivery is a *single* byte stream, and no amount of multiplexing above it can undo that. The fix had to be below HTTP and outside TCP, which meant UDP.

Two more things QUIC brings: the TLS and transport handshakes are **combined**, so a new connection is 1 RTT (or 0 on resumption) rather than 2–3; and a connection is identified by a **connection ID** rather than the five-tuple, so it **survives a change of IP address** — your phone moving from Wi-Fi to cellular keeps the connection alive, which TCP cannot do by construction (M5: the five-tuple *is* the identity).

### HPACK, and server push's failure

**HPACK** compresses headers with a shared dynamic table, which matters more than it sounds: a typical request carries several hundred bytes of largely identical headers, repeated for every one of a page's hundred-odd resources. HTTP/1.1 sent all of it in full every time.

**Server push** let a server send resources the client had not asked for, anticipating need. It has been **abandoned** — Chrome removed it — because servers could not tell what the client already had cached, so push frequently wasted bandwidth re-sending files the browser already held. `103 Early Hints`, which merely *tells* the client what to fetch, replaced it. A good thing to know, because it is a rare example of a protocol feature being tried at scale and withdrawn.

---

## 8.7 CORS — and why it fails only in the browser

The most commonly misunderstood topic in web development, and a measurement settles it.

**The same-origin policy** is a *browser* rule: script on one origin may not read responses from another. An origin is the triple **scheme + host + port**, so `https://a.com` and `https://a.com:8443` are different origins, as are `http://` and `https://` versions of the same host.

**CORS** is the mechanism for a server to opt in to being read cross-origin.

### Verified: the server answers regardless

```
  preflight OPTIONS with Origin + Access-Control-Request-*: 200
     access-control-allow-origin: https://evil.example
     access-control-allow-credentials: true
     access-control-allow-methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
     access-control-max-age: 3600
     access-control-allow-headers: X-Custom

  simple GET with an Origin header: 200
     access-control-allow-origin: https://evil.example
     access-control-allow-credentials: true
```

**Both requests succeeded and returned data.** Python sent an `Origin` header claiming to be `https://evil.example`, and the server replied normally.

> **CORS is enforced entirely by the browser.** The request is sent, the server processes it, the response comes back — and then the browser **withholds it from the page's JavaScript** if the headers do not permit that origin. So "CORS blocked my request" almost always means *"the browser refused to show me a response it had already received."*

Three consequences that follow, and they are what the question is really testing:

1. **`curl`, Python and a server-side proxy are unaffected.** There is no browser to enforce anything. Which is why a request that fails in the browser works from your terminal, and why routing it through your own backend "fixes" it.
2. **CORS is not a security mechanism for your server.** It does not stop anyone sending requests. Authentication and authorisation are still entirely your job — and note the side effect in the output above: the request **was processed**, so a state-changing `GET` would have changed state before any CORS check mattered.
3. **The preflight is a separate round trip.** A "non-simple" request — a method beyond `GET`/`HEAD`/`POST`, or a custom header — triggers an `OPTIONS` preflight *first*, and only then the real request. `Access-Control-Max-Age: 3600` above is the server telling the browser to cache that permission for an hour, which is how you avoid paying the extra round trip on every call.

**And the credentials trap worth knowing:** with `Access-Control-Allow-Credentials: true`, the spec forbids `Access-Control-Allow-Origin: *`. You must name the exact origin — which is precisely what the server did above, echoing `https://evil.example` back. A server that reflects any `Origin` *and* allows credentials has effectively disabled the same-origin policy for itself, and that is a real vulnerability rather than a configuration style.

---

## 8.8 Keep-alive, measured

```
  SAME client (keep-alive):  178.5    60.0    59.9    60.4    59.8    61.2  ms
   first 178.5 ms vs median of the rest 60.0 ms

  NEW client each time (no reuse):  202.9   189.8   167.0   161.5  ms
```

**The first request costs 178 ms; every subsequent one on the same connection costs 60.** Nearly a **3× difference**, and the 118 ms gap is DNS plus the TCP handshake plus the TLS handshake — exactly the round trips M0's latency budget predicts. The second row is the control: open a fresh connection each time and you pay it **every** time, never dropping below 160 ms.

That single measurement is the justification for a great deal of engineering: `Connection: keep-alive` (the HTTP/1.1 default), connection pooling in every HTTP client library, and HTTP/2's decision to use **one** connection per origin. It is also why the N+1 problem in **DBMS M10** has the same shape — the per-operation cost dominates, so batching and reuse beat almost any other optimisation.

---

## 8.9 Compression, and a measurement that misbehaved

```
  Accept-Encoding sent by default: gzip, deflate, br
  response content-encoding: gzip
  decoded body: 297 bytes

  with Accept-Encoding: identity -> content-encoding gzip, 288 bytes
```

The first part works as expected: the client advertises what it can decode, the server picks one, and `Content-Encoding` says what it chose.

**The second part did not do what I intended.** I asked for `identity` — no compression — and the server **gzipped anyway**. That is not a protocol subtlety; the endpoint I used (`httpbin.org/gzip`) always gzips regardless of what the client requests, so the test was badly chosen rather than revealing. A correct demonstration needs a server that honours the header. Reported as a failed measurement rather than reinterpreted into a finding.

What remains true and worth knowing: `Content-Encoding` is **end-to-end** compression of the body chosen by content negotiation, while `Transfer-Encoding: chunked` (seen in §8.1) is a **hop-by-hop** framing decision. They are different mechanisms that both affect the bytes on the wire, and `Vary: Accept-Encoding` is what stops a shared cache serving a compressed body to a client that cannot handle it.

---

## 8.10 WebSockets, SSE and polling

HTTP is request/response, so the server cannot initiate. Four ways around that:

| | Polling | Long polling | **SSE** | **WebSocket** |
|---|---|---|---|---|
| Mechanism | Ask every *n* seconds | Request held open until there is news | One long-lived HTTP response, streamed | **Full-duplex** after an upgrade |
| Direction | Client pulls | Client pulls | **Server → client only** | **Both ways** |
| Protocol | HTTP | HTTP | HTTP | `ws://` / `wss://` after `101 Switching Protocols` |
| Overhead | High — headers every poll | Moderate | Low | **Lowest** per message |
| Latency | Up to the poll interval | Low | Low | **Lowest** |
| Works through proxies | Always | Usually | Usually | Sometimes awkward |
| Auto-reconnect | n/a | manual | **Built in** | manual |
| Right for | Simple, infrequent updates | A legacy fallback | Notifications, live feeds, token streaming | Chat, games, collaborative editing |

**WebSockets start as HTTP** — a `GET` with `Upgrade: websocket` — and the server's `101 Switching Protocols` hands the same TCP connection over to a different protocol. That is the only common use of a `1xx` status code, and it is why WebSockets work on port 443 through most firewalls.

**SSE is underrated** and worth naming: if you only need server→client, it is plain HTTP, survives proxies, and reconnects automatically. Choosing a WebSocket when you only push one way is a common over-engineering, and saying so is a good answer.

---

## Must remember

```
STRUCTURE (both directions): START LINE / HEADERS / BLANK LINE / BODY
 the BLANK LINE is the only header terminator -> HEADER INJECTION (CR/LF in a
 value) is a vulnerability class.
 Host: is MANDATORY in HTTP/1.1 and is what makes VIRTUAL HOSTING work --
 one IP, thousands of sites. It is also why TLS needed SNI (pick the cert before
 the encrypted Host can be read).
 Transfer-Encoding: chunked = length-prefixed chunks, no Content-Length; lets a
 server start sending before it knows the size. (verified: body began "241\r\n")
 Age + cf-cache-status: HIT = served from a CDN cache (verified: 13,778 s old)
 alt-svc: h3=":443" = how HTTP/3 is ADVERTISED, because you cannot upgrade a TCP
 connection to QUIC.

METHODS
 SAFE       = does not change server state (a crawler may call it freely)
 IDEMPOTENT = N calls have the same effect as 1
 GET HEAD OPTIONS TRACE  safe + idempotent
 PUT DELETE              IDEMPOTENT BUT NOT SAFE  <- the pair that clarifies both
 POST PATCH              neither
 PUT is the clarifying example: it changes state (not safe) but 5 calls leave the
 same state (idempotent). POST is neither -> hence the browser's resubmit warning,
 and why payment APIs require an IDEMPOTENCY KEY.
 HEAD returns a GET's headers with NO body (verified: 0 vs 577 bytes).

STATUS CODES  1xx info | 2xx success | 3xx redirect | 4xx CLIENT | 5xx SERVER
 401 NOT AUTHENTICATED ("log in") vs 403 AUTHENTICATED BUT FORBIDDEN
   -> resending credentials helps 401, NEVER 403
 404 might return vs 410 GONE, deliberately permanent
 200 ok | 201 created (+ Location) | 204 success, NO BODY ON PURPOSE
 301/308 PERMANENT, 302/307 TEMPORARY;  307/308 MUST PRESERVE method+body,
   301/302 MAY change POST->GET
 301/308 ARE CACHED BY BROWSERS, often indefinitely -> TEST WITH 302 FIRST
 500 the app threw | 502 BAD GATEWAY: upstream returned garbage
 503 UNAVAILABLE: nothing to ask (often + Retry-After) | 504 upstream never replied
   -> 502/503/504 all come from the PROXY, not the app, and point at different places
 EVERY REDIRECT HOP IS A FULL ROUND TRIP.

CACHING -- two different mechanisms
 FRESHNESS avoids the request ENTIRELY (zero round trips):
   Cache-Control: max-age / public / private / immutable, Expires (max-age wins)
 VALIDATION still costs a round trip but avoids the BODY:
   ETag <-> If-None-Match | Last-Modified <-> If-Modified-Since -> 304, NO BODY
   VERIFIED: a real 304 returned 0 bytes, saving 100% of a 317-byte payload
 no-cache MEANS "REVALIDATE BEFORE USE", NOT "do not cache". no-store means do not store.
 ETag is exact and opaque; Last-Modified has ONE-SECOND resolution so it misses
 two changes in the same second. W/"x" is a WEAK etag (semantically equivalent).
 Vary names the request headers the response depends on -- forget it and a shared
 cache serves a gzip body to a client that cannot decode it.
 modern pattern: content-hashed filenames + max-age + immutable = never revalidate.

STATELESSNESS: each request is independent, which is WHY HTTP SCALES.
 Set-Cookie attributes and what each prevents:
   HttpOnly (XSS stealing it) | Secure (plaintext interception)
   SameSite (CSRF) | Domain/Path (over-broad scope) | Max-Age (indefinite validity)
 SESSION = opaque id + server state: REVOCABLE, needs shared storage
 TOKEN/JWT = signed claims: STATELESS, hard to revoke, bigger on every request
 the compromise: SHORT-LIVED access token + REVOCABLE refresh token.
 "stateless auth" does not make the app stateless -- the state moved to the client
 and is re-sent on every single call.

HTTP VERSIONS
 1.0 one request per connection | 1.1 keep-alive + required Host + pipelining(failed)
 2   BINARY framing, MULTIPLEXED streams on ONE TCP connection, HPACK headers
 3   QUIC over UDP, per-stream reliability, QPACK, 1-RTT (0 on resume)
 THE VERSION IS CHOSEN BY TLS ALPN, NOT BY THE URL (verified: the same URL
 negotiated both HTTP/2 and HTTP/1.1). There is no such thing as an HTTP/2 URL.
 HEAD-OF-LINE BLOCKING EXISTS AT TWO LAYERS -- this is the key idea:
   HTTP/1.1: one request at a time per connection; pipelining still required
     IN-ORDER RESPONSES, so the blocking remained. Browsers opened 6 connections.
   HTTP/2: fixes the APPLICATION layer (multiplexed streams, any order)
     BUT TCP STILL DELIVERS IN ORDER, so ONE LOST SEGMENT STALLS EVERY STREAM --
     sometimes WORSE than HTTP/1.1, because 6 connections meant losing 1/6 of the
     work while 1 connection means losing all of it.
   HTTP/3: QUIC gives each stream its OWN sequence space -> a loss stalls only
     that stream. THAT is why HTTP/3 had to leave TCP: in-order delivery of a
     SINGLE byte stream cannot be fixed from above.
 QUIC also: combines the TLS and transport handshakes (1 RTT), and identifies a
 connection by CONNECTION ID not the five-tuple -> SURVIVES AN IP CHANGE
 (Wi-Fi to cellular), which TCP cannot do because the five-tuple IS the identity.
 SERVER PUSH WAS ABANDONED (Chrome removed it): the server could not know what the
 client already had cached, so it wasted bandwidth. 103 Early Hints replaced it.

CORS / SAME-ORIGIN
 an ORIGIN is SCHEME + HOST + PORT (so https vs http, and :443 vs :8443, differ)
 CORS IS ENFORCED BY THE BROWSER, NOT THE SERVER. VERIFIED: a request with
 Origin: https://evil.example was PROCESSED and ANSWERED normally; the browser is
 what would withhold the response from the page's JavaScript.
 -> curl/Python/a server-side proxy are UNAFFECTED, which is why it "works in
    Postman" and why proxying through your own backend "fixes" it
 -> CORS IS NOT SERVER-SIDE SECURITY: the request still ran. Auth is still your job.
 -> a PREFLIGHT OPTIONS is an EXTRA ROUND TRIP for non-simple requests (a method
    beyond GET/HEAD/POST, or a custom header). Access-Control-Max-Age caches it.
 -> with Allow-Credentials: true you MAY NOT use Allow-Origin: *. Reflecting any
    Origin AND allowing credentials disables the same-origin policy for your site.

KEEP-ALIVE, MEASURED: first request 178.5 ms, subsequent 60.0 ms on the same
 connection -- a 3x difference, and the 118 ms gap is DNS + TCP + TLS. A new
 connection every time never dropped below 160 ms. That is why keep-alive is the
 HTTP/1.1 default, why every client pools connections, and why HTTP/2 uses ONE.

Content-Encoding (gzip/br) is END-TO-END body compression chosen by negotiation.
Transfer-Encoding (chunked) is HOP-BY-HOP framing. Different mechanisms.

SERVER PUSH ALTERNATIVES  polling | long polling | SSE | WebSocket
 SSE: server -> client ONLY, plain HTTP, survives proxies, AUTO-RECONNECTS
 WebSocket: FULL DUPLEX, starts as an HTTP GET with Upgrade and a
   101 SWITCHING PROTOCOLS -- the only common 1xx code
 choosing a WebSocket when you only push ONE WAY is over-engineering; SSE is the
 right default for notifications and live feeds.
```

---

## Common wrong answers

| Wrong | Right |
|---|---|
| "GET is idempotent and POST isn't, that's the difference" | There are **two** properties. `PUT` and `DELETE` are idempotent but **not safe** — that pair is what distinguishes the concepts |
| "PUT and POST are both for creating things" | `PUT` replaces a resource at a known URL and is idempotent; `POST` submits to a processor and is not. Replaying a `POST` may create a duplicate |
| "PATCH is idempotent" | Usually not — "append to this list" applied twice appends twice. A declarative diff can be, which is why the spec leaves it open |
| "401 means you don't have permission" | 401 is **not authenticated**; 403 is authenticated and **not permitted**. Resending credentials helps only with 401 |
| "502 and 503 both mean the server is down" | Both come from the **proxy**. 502 means upstream returned something invalid; 503 means nothing was available to ask; 504 means upstream never replied |
| "301 and 302 are the same except for duration" | 301 and 308 are permanent and **cached by browsers, often indefinitely** — a mistaken 301 is very hard to undo. And 307/308 preserve the method where 301/302 may not |
| "`no-cache` means don't cache it" | It means **revalidate before use**. `no-store` is the one that means do not store |
| "A 304 saves bandwidth" — with no detail | It returns **headers only, zero body**. Verified: 100% of a 317-byte payload saved. But it still costs a **round trip** — `max-age` costs none at all |
| "`Last-Modified` and `ETag` are interchangeable" | `Last-Modified` has one-second resolution, so two changes in the same second are indistinguishable. `ETag` is exact |
| "`Vary` is optional metadata" | Omit it on a content-negotiated response and a shared cache will serve the wrong variant to everyone |
| "HTTP is stateless, so you can't have logins" | State is layered on with cookies carrying a session ID or a signed token. The *protocol* stays stateless, which is what makes it scalable |
| "JWTs are better because they're stateless" | They are also **hard to revoke** and are re-sent on every request. Sessions are revocable but need shared storage. The usual answer is short-lived tokens plus a revocable refresh token |
| "`HttpOnly` stops CSRF" | `HttpOnly` stops **XSS** reading the cookie. `SameSite` is the one that addresses CSRF |
| "`https://` means HTTP/2" | The version is negotiated by **TLS ALPN**. Verified: the same URL served both HTTP/2 and HTTP/1.1 depending only on what the client offered |
| "HTTP/2 removed head-of-line blocking" | At the **application** layer only. TCP still delivers in order, so one lost segment stalls every multiplexed stream — sometimes making HTTP/2 **worse** than HTTP/1.1 on lossy links |
| "HTTP/3 uses UDP because UDP is faster" | Because TCP's in-order delivery of a single byte stream cannot be fixed from above. QUIC gives each stream its own sequence space |
| "HTTP/3 is just HTTP/2 over UDP" | It also merges the TLS and transport handshakes into one RTT and identifies connections by **connection ID**, so they survive an IP change |
| "Server push makes pages load faster" | It was **abandoned** — the server could not know what the client had cached, so it wasted bandwidth. `103 Early Hints` replaced it |
| "Pipelining is how HTTP/1.1 does concurrency" | Pipelining required **in-order responses**, so the blocking remained; it was effectively never deployed. Browsers opened six connections per origin instead |
| "CORS protects my API" | It is enforced by the **browser** and does not stop anyone sending requests. Verified: the server processed and answered a request from `https://evil.example` |
| "CORS blocked my request" | The browser blocked your **access to the response**. The request was sent and processed — which is also why a state-changing `GET` is dangerous regardless of CORS |
| "I'll set `Access-Control-Allow-Origin: *` and allow credentials" | The spec forbids that combination. Reflecting an arbitrary `Origin` while allowing credentials effectively disables the same-origin policy for your site |
| "A preflight is free" | It is a **separate round trip** before the real request. `Access-Control-Max-Age` is what amortises it |
| "Keep-alive is a minor optimisation" | Measured: 178 ms first request against 60 ms for reused connections — nearly 3×, and the gap is DNS plus TCP plus TLS |
| "Use WebSockets for live updates" | If the data flows one way, **SSE** is plain HTTP, survives proxies and reconnects automatically. WebSockets are for genuinely bidirectional traffic |

---

## Interview Q&A bank

**Q1. Describe the structure of an HTTP request and response.**
Both are a start line, then headers, then a blank line, then an optional body. The request's start line is the method, path and version; the response's is the version, status code and reason phrase. The blank line is the only thing marking the end of the headers, which is why injecting CR/LF into a header value is a vulnerability.

**Q2. Why is the `Host` header mandatory in HTTP/1.1?**
Because it enables virtual hosting — one IP address serving thousands of sites, since the request says which one it wants. HTTP/1.0 had no such header, so one address meant one site. It is also why TLS needed SNI: the certificate must be chosen before the encrypted `Host` header can be read.

**Q3. What is `Transfer-Encoding: chunked` for?**
It lets a server start sending a body before it knows the total length, by sending length-prefixed chunks instead of a `Content-Length`. It is the mechanism behind streaming responses.

**Q4. What do safe and idempotent mean, and which methods are which?**
Safe means no change to server state; idempotent means *N* calls have the same effect as one. `GET`, `HEAD`, `OPTIONS` and `TRACE` are both. `PUT` and `DELETE` are idempotent but **not** safe — which is the pair that makes the distinction clear. `POST` and `PATCH` are neither.

**Q5. Why does idempotency matter in practice?**
Because a client that times out does not know whether the request was processed. An idempotent request can simply be retried; a `POST` cannot, which is why payment APIs require an idempotency key and browsers warn before re-submitting a form.

**Q6. 401 vs 403?**
401 means not authenticated — the server does not know who you are, so supplying credentials may help. 403 means authenticated but not permitted, so credentials will never help.

**Q7. 502 vs 503 vs 504?**
All three come from a proxy or load balancer rather than the application. 502 means upstream returned an invalid response; 503 means nothing was available to serve, usually overload, often with `Retry-After`; 504 means upstream was asked and never replied. They point at different places in the stack.

**Q8. 301 vs 302 vs 307 vs 308?**
301 and 308 are permanent; 302 and 307 are temporary. 307 and 308 must preserve the method and body, whereas 301 and 302 historically allowed a `POST` to become a `GET`. And 301/308 are cached by browsers, sometimes indefinitely, so a mistake is very hard to undo — test with 302 first.

**Q9. How does HTTP caching work?**
Two mechanisms. Freshness — `Cache-Control: max-age` — lets a cache serve a copy with **no request at all**. Validation — `ETag` with `If-None-Match`, or `Last-Modified` with `If-Modified-Since` — costs a round trip but returns a **304 with no body** if nothing changed. Verified: a real 304 saved 100% of the payload.

**Q10. Which is better, freshness or validation?**
Freshness, decisively, because it avoids the request entirely rather than just the body. The modern pattern is content-hashed filenames with a long `max-age` and `immutable`, so the URL changes when the content does and the cache never needs to revalidate.

**Q11. What does `no-cache` mean?**
Revalidate before using the cached copy — not "do not cache". The directive meaning do not store at all is `no-store`.

**Q12. `ETag` vs `Last-Modified`?**
`ETag` is an opaque token that changes whenever the content does. `Last-Modified` is a timestamp with one-second resolution, so two changes within the same second are indistinguishable. `ETag` is exact; `Last-Modified` is free if the filesystem already tracks mtime.

**Q13. What is `Vary` for?**
It tells caches which request headers the response depends on. Without `Vary: Accept-Encoding`, a shared cache can serve a gzipped body to a client that cannot decode it, or the wrong language variant to everyone.

**Q14. Is HTTP stateless, and how do logins work then?**
The protocol is stateless — each request is independent, which is what lets any server handle any request. State is layered on top with a cookie carrying either an opaque session ID, with the data held server-side, or a signed token carrying the claims themselves.

**Q15. Sessions vs JWTs?**
Sessions store data server-side and the cookie is just an ID: revocation is immediate but you need shared storage or sticky routing. Tokens carry signed claims so any server can verify them without state, but they cannot easily be revoked and are re-sent on every request. The common compromise is short-lived access tokens plus a revocable refresh token.

**Q16. What do the cookie attributes do?**
`HttpOnly` stops JavaScript reading it, which mitigates XSS theft. `Secure` restricts it to HTTPS. `SameSite` controls whether it is sent on cross-site requests, which addresses CSRF. `Domain` and `Path` scope it, and `Max-Age` bounds its life.

**Q17. What problem did each HTTP version solve?**
1.1 added keep-alive and a mandatory `Host`, so connections could be reused and virtual hosting worked. 2 added binary framing, multiplexed streams over one connection and header compression, removing application-layer head-of-line blocking. 3 moved to QUIC over UDP, removing TCP's head-of-line blocking, merging the handshakes into one round trip, and surviving IP changes.

**Q18. How is the HTTP version chosen?**
By TLS ALPN during the handshake — the client lists the protocols it speaks. Verified: the same URL negotiated HTTP/2 or HTTP/1.1 depending only on what the client offered. HTTP/3 is different: it is advertised by `alt-svc` and used on a subsequent connection, because a TCP connection cannot be upgraded to QUIC.

**Q19. Explain head-of-line blocking.**
It exists at two layers. In HTTP/1.1 a connection carries one request at a time, so a slow response blocks everything behind it. HTTP/2 fixes that with multiplexed streams — but TCP still delivers bytes in order, so one lost segment stalls every stream on the connection, even streams whose data already arrived. HTTP/3 fixes that by giving each stream its own sequence space in QUIC.

**Q20. Was HTTP/2 ever worse than HTTP/1.1?**
On lossy links, yes. HTTP/1.1 browsers opened six connections, so a loss stalled a sixth of the work; HTTP/2 uses one, so a single loss stalls all of it. That is the specific motivation for HTTP/3.

**Q21. Why did HTTP/3 have to leave TCP?**
Because TCP presents a single in-order byte stream, and no amount of multiplexing above it can make one stream's loss stop blocking the others. The fix had to live below HTTP and outside TCP, which meant building on UDP.

**Q22. What else does QUIC give you?**
The TLS and transport handshakes are combined, so a new connection costs one round trip and a resumed one can cost zero. And a connection is identified by a connection ID rather than the five-tuple, so it survives a change of IP address — a phone moving from Wi-Fi to cellular keeps the connection, which TCP cannot do because the five-tuple *is* the identity.

**Q23. What happened to HTTP/2 server push?**
It was abandoned and removed from Chrome. The server could not know what the client already had in cache, so pushes frequently re-sent resources the browser already held. `103 Early Hints`, which only tells the client what to fetch, replaced it.

**Q24. What is CORS?**
A mechanism for a server to tell the browser that another origin may read its responses. The same-origin policy is a browser rule preventing script on one origin from reading responses from another, where an origin is scheme, host and port.

**Q25. Why does a request fail in the browser but work from `curl`?**
Because CORS is enforced by the **browser**, not the server. Verified: a request carrying `Origin: https://evil.example` was processed and answered normally — the browser is simply what withholds the response from the page's JavaScript. There is no browser in `curl`, so nothing enforces it.

**Q26. Does CORS protect my API?**
No. The request is still sent and still processed, so authentication and authorisation remain entirely your responsibility. It is a browser-side restriction on reading responses, not a server-side access control.

**Q27. What is a CORS preflight and when does it happen?**
An `OPTIONS` request the browser sends before a "non-simple" request — one using a method beyond `GET`, `HEAD` or `POST`, or carrying a custom header — to ask whether it is allowed. It is an extra round trip, which `Access-Control-Max-Age` lets the browser cache.

**Q28. Can you use `Access-Control-Allow-Origin: *` with credentials?**
No, the spec forbids it — you must name the exact origin. And a server that reflects whatever `Origin` it is given while also allowing credentials has effectively disabled the same-origin policy for itself, which is a vulnerability rather than a configuration style.

**Q29. How much does keep-alive actually save?**
Measured: 178 ms for the first request against 60 ms for each subsequent request on the same connection — nearly a threefold difference. The 118 ms gap is DNS plus the TCP handshake plus the TLS handshake, and a fresh connection every time never dropped below 160 ms.

**Q30. WebSockets vs SSE vs polling?**
Polling asks repeatedly and wastes headers; long polling holds a request open. SSE is a single long-lived HTTP response streamed server-to-client, which survives proxies and reconnects automatically. WebSockets upgrade the connection to a full-duplex protocol after a `101 Switching Protocols`. If the data flows one way, SSE is the right default; WebSockets are for genuinely bidirectional traffic.

---

## Practice

1. Write a raw HTTP/1.1 `GET` for `https://api.example.com/users?page=2` with an `Authorization` header, and say which single header is mandatory and why.
2. Classify each as safe, idempotent, both or neither: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`. Then give a `PATCH` body that *is* idempotent and one that is not.
3. A client times out on a request. For each method, say whether it is safe to retry automatically, and why.
4. Choose the status code: (a) the resource moved for good; (b) the user is not logged in; (c) the user is logged in but lacks the role; (d) the upstream service timed out; (e) a resource was created; (f) the update succeeded with nothing to return.
5. Your CSS is cached for 24 hours and you need to ship a fix now. Give two approaches and say which is better and why.
6. Explain the difference between a response with `Cache-Control: max-age=600` and one with `ETag` only, in terms of round trips over ten minutes of repeated requests.
7. `no-cache`, `no-store`, `private`, `must-revalidate`, `immutable` — give one sentence each.
8. Your API works in Postman and fails in the browser with a CORS error. Explain exactly what is happening, and give three ways to fix it with their trade-offs.
9. A page loads 80 small images. Compare HTTP/1.1, HTTP/2 and HTTP/3, including what happens if 1% of packets are lost.
10. Why can't you upgrade an existing TCP connection to HTTP/3? How does a client discover HTTP/3 support?
11. You are designing a live dashboard pushing updates every two seconds to 10,000 clients. Compare polling, SSE and WebSockets, and pick one.
12. Explain why the measurement `178 ms then 60 ms` in §8.8 is an argument for connection pooling, and connect it to the N+1 problem in DBMS M10.

**Answers to 3, 6 and 9:**

> **3.** `GET`, `HEAD`, `OPTIONS`, `PUT` and `DELETE` are **idempotent**, so an automatic retry is safe — the worst case is repeating work with the same final state. `POST` and most `PATCH` requests are **not**, so a blind retry risks creating a duplicate order or double-applying a change. The standard resolution is an **idempotency key**: the client generates a unique id, the server records it, and a repeated request with the same key returns the original result instead of acting again. That is precisely why payment APIs require one.
>
> **6.** With `max-age=600`, the first request is a round trip and **every request for the next ten minutes costs nothing at all** — the cache serves locally. With `ETag` only and no freshness information, the cache must revalidate **every time**: each request is a full round trip that returns a 304 with no body. So over ten minutes of, say, 50 requests, `max-age` costs **1** round trip and `ETag` costs **50** — all of them small, but all of them paying the RTT. The bodies are saved either way; only freshness saves the request.
>
> **9.** **HTTP/1.1:** six connections per origin, so 80 images take roughly 14 sequential rounds of 6; each connection pays its own handshake unless keep-alive is working. **HTTP/2:** one connection, all 80 multiplexed, headers compressed by HPACK — dramatically fewer round trips and far less header overhead. **With 1% loss, though,** HTTP/2 can be *worse*: every lost segment stalls the single TCP connection and therefore all 80 streams, whereas HTTP/1.1's six connections confine a loss to a sixth of the work. **HTTP/3** is the best of both: still one connection and fully multiplexed, but a loss stalls only the stream that lost data, because QUIC gives each stream its own sequence space.

---

## Exit checklist

```
[ ] I can write a raw HTTP request and response and name every part
[ ] I know the blank line is the header terminator and why that matters for security
[ ] I know why Host is mandatory, and that it is why TLS needed SNI
[ ] I know what chunked transfer encoding is for
[ ] I can read Age and a cache-status header and say where a response came from
[ ] I know alt-svc is how HTTP/3 is advertised, and why it has to be
[ ] I can define safe and idempotent separately
[ ] I know PUT/DELETE are idempotent but NOT safe, and why that pair clarifies both
[ ] I can explain why idempotency matters for retries and idempotency keys
[ ] I know HEAD returns no body and what it is for
[ ] I can give the five status-code classes
[ ] I can distinguish 401/403, 404/410, 200/201/204
[ ] I can distinguish 301/302/307/308 on BOTH axes
[ ] I know 301/308 are cached hard, so test with 302 first
[ ] I can distinguish 500/502/503/504 and say which come from the proxy
[ ] I know every redirect hop is a full round trip
[ ] I can explain freshness vs validation and which saves more
[ ] I know a 304 has NO body, and that it still costs a round trip
[ ] I know no-cache means REVALIDATE, and no-store means do not store
[ ] I can compare ETag and Last-Modified, including the one-second resolution
[ ] I know what Vary is for and what breaks without it
[ ] I know the content-hash + max-age + immutable pattern
[ ] I can explain why statelessness is what makes HTTP scale
[ ] I can name five cookie attributes and what each one prevents
[ ] I know HttpOnly addresses XSS and SameSite addresses CSRF
[ ] I can compare sessions and tokens on revocation, scaling and size
[ ] I can give the short-lived-token-plus-refresh-token compromise
[ ] I can say what each HTTP version fixed
[ ] I know the version is chosen by TLS ALPN, not by the URL
[ ] I can explain head-of-line blocking AT BOTH LAYERS
[ ] I can explain why HTTP/2 can be worse than HTTP/1.1 under loss
[ ] I can explain why HTTP/3 had to leave TCP
[ ] I know QUIC merges the handshakes and survives an IP change, and why
[ ] I know server push was abandoned and what replaced it
[ ] I know why pipelining failed
[ ] I can define an origin as scheme + host + port
[ ] I can explain that CORS is enforced by the BROWSER, with the evidence
[ ] I can explain why it works in curl and not in the browser
[ ] I know CORS is not server-side security
[ ] I know what triggers a preflight and what Access-Control-Max-Age does
[ ] I know the wildcard-plus-credentials prohibition and why reflecting Origin is bad
[ ] I can quote the keep-alive measurement and say what the gap consists of
[ ] I can distinguish Content-Encoding from Transfer-Encoding
[ ] I can compare polling, long polling, SSE and WebSockets on six axes
[ ] I know SSE is the right default for one-way updates
```

---

## Next

**Part 11: M9 — Network Security.** What an attacker on the path can do, and the layer that stops them. Symmetric versus asymmetric cryptography and why both are needed; **hashing versus encryption versus encoding** — the single most common confusion in this area; digital signatures; **certificates, CAs and the chain of trust**; **the TLS 1.2 and TLS 1.3 handshakes step by step**, with the **real negotiated version, cipher suite and certificate chain** captured from this machine; forward secrecy; **what HTTPS does and does not hide**; firewalls, with this network's own ICMP and DNS filtering as the live example; NAT as accidental security; VPNs and tunnelling; and the attacks worth naming — MITM, replay, DoS/DDoS, SYN flood, ARP and DNS spoofing, session hijacking — each with its defence.
