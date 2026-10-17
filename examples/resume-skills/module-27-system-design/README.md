# M27: System-design bridge through your load balancer

Run `npm run verify` in this directory with Node.js 22 or later. The recorded run uses Node.js v22.14.0 on Windows. All runtime imports are Node built-ins or local modules; no install, Docker, account or API key is required.

`verify.mjs` executes deterministic placement/policy/capacity/cache-model checks plus real HTTP forwarding and failure cases over owned ephemeral loopback ports. It writes named assertions and observations to `verification-results.json` and closes servers, agents and fixture timers in `finally`. No throughput/latency benchmark from the original resume project is reproduced.

- `ring.mjs`: SHA-256-derived 64-bit ring, virtual tokens, binary-search primary and clockwise physical-member candidates.
- `pool.mjs`: hash/round-robin/least-inflight policies, consecutive observation thresholds and drain eligibility.
- `capacity.mjs`: arithmetic over stated planning assumptions, not measured backend capacity.
- `cache-model.mjs`: in-process canonical revision/TTL/deletion model, not a network cache.
- `proxy.mjs` and `http-fixture.mjs`: limited buffered HTTP proxy and synthetic upstream/client helpers. Public demo credentials are not real authentication. Read the chapter's production boundaries before adapting it.
- `resume-claims.json`: source filenames/checksums and reported metrics, explicitly unverified as original-project results.

`author.py` regenerates the canonical teaching chapter from these exact sources and recorded observations. `validate_site.py` checks source/output fidelity and builds/smoke-tests the handbook using a temporary loopback server, then closes it. It requires the repository's existing installed site dependencies and Python; it does not start port 3000.

The implementation is a teaching fixture: no TLS/HTTP2/upgrades/streaming, production authentication, public control plane, distributed cache, cross-proxy consensus or production benchmark is claimed. Learning exercises document further work separately.
