# Module 4: Node.js

Twenty isolated runtime cases plus a small HTTP/streaming server for the Resume Skills handbook.

From the repository root:

```powershell
node examples/resume-skills/module-4-nodejs/verify.mjs
node examples/resume-skills/module-4-nodejs/verify.mjs 11-backpressure
node examples/resume-skills/module-4-nodejs/verify-server.mjs
node examples/resume-skills/module-4-nodejs/start.mjs
```

The manual launcher listens on 127.0.0.1:3104; stop with Ctrl+C. It is separate from the notes website on port 3000. Change the launcher port if 3104 is occupied.

Verified on Node.js v22.14.0. Nineteen cases use ES modules; 03-commonjs uses CommonJS. Each case runs in its own process, with the example directory as its working directory and a ten-second timeout. The verifier checks exit status, empty stderr and exact stdout. A full run refreshes results.json.

No packages, database, credentials or external network service are required. The cases use local fixtures, an ephemeral loopback HTTP server, two short-lived Worker threads and one child Node process. Those resources finish or close during verification. The pending-promise/unref case intentionally exits without waiting for its unreferenced timer.

HTTP routes (GET only):

- /health: small readiness-style response, not a complete dependency/liveness policy.
- /api/info: await file/dependency work and return UTF-8 byte count.
- /download: stream a fixed 79,872-byte fixture with backpressure via pipeline.

The sixteen HTTP checks cover normal routes/headers, fixed file selection, 404/405, overlapping waits with health progress, draining admission while accepted work completes, listener closure, missing files and async failure mapping. They are functional checks, not throughput benchmarks.

Artifacts:

- cases.json, verify.mjs, results.json and verification-output.txt: runtime examples and captured output.
- server.mjs: exported HTTP application factory.
- start.mjs: manual launcher and bounded shutdown attempt.
- verify-server.mjs and http-verification-output.txt: sixteen HTTP verification groups.
- fixtures/: immutable download text, CJS/ESM counters and CPU Worker module.
- validation-summary.json and site-build-output.txt: chapter/site checks.

Runtime cases cover host APIs, EventEmitter behavior, module caching/live bindings, asynchronous files, I/O callback scheduling, host yielding, Buffers/UTF-8 decoding, pipelines, pressure, stream failure, compression, Workers/errors, child processes, configuration, process liveness and native asynchronous crypto work.

The server is a public loopback learning application. It does not implement authentication, a database, request-body parsing, range requests, global limits or durable jobs. Download behavior assumes a stable regular fixture. OS signal delivery/forced shutdown and client-abort behavior are not covered by the HTTP checks; the launcher is syntax-checked. Runtime/version/context labels matter for scheduling examples.
