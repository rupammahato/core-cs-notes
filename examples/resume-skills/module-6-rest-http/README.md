# M6: REST APIs and HTTP

A dependency-free learning API with a single in-memory task collection. Recorded runtime: Node.js v22.14.0.

From the repository root:

```powershell
node examples/resume-skills/module-6-rest-http/verify.mjs
node examples/resume-skills/module-6-rest-http/start.mjs
```

The manual service binds 127.0.0.1:3106. Stop it with Ctrl+C. The verifier chooses temporary loopback ports and closes every listener.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3106/v1/tasks -ContentType application/json -Headers @{'Idempotency-Key'='learn-http-1'} -Body '{"title":"Learn HTTP","completed":false}'
```

Task fields: server-owned id, title (trimmed 1–80 UTF-16 code units), completed (boolean). POST requires a documented key; PUT/PATCH/DELETE require If-Match. PATCH is a custom application/json partial object, not JSON Merge Patch.

GET /v1/tasks supports limit=1..5, completed=true|false, order=asc|desc and cursor. Follow the returned next URL unchanged. Item GET supports If-None-Match. GET /v1/limited demonstrates a separate global fixed-window budget.

verify.mjs passes 68 real HTTP checks: input/error/method/validator contracts, list traversal under deletion/insertion, atomic edits including a split request body, pending creation deduplication, expiry, a pre-write injected failure, and rate-limit policy. results.json and verification-output.txt are generated evidence.

Clock tests inject time. Creation/replay hooks synchronize overlap. No sleeps establish concurrency, and no throughput is measured.

Limitations: one public demo scope; no authentication, persistence, distributed coordination, TLS/CORS, full negotiation/precondition engine, browser cache testing, external effects or process-crash tests. Retained keys last 60 seconds after completion; failed pre-write operations release their record; pending records are not expired. The body reader bounds allocation while draining an oversized request, not upload bandwidth.

See the [M6 chapter](../../../Resume%20Skills%20Notes/resume-skills-handbook-part-8-module-6-rest-apis-http.md) for the exact contract and production evolution.
