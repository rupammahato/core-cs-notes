# Module 2: Asynchronous JavaScript

Twenty-eight dependency-free examples for the Resume Skills teaching chapter.

From the repository root:

```powershell
node examples/resume-skills/module-2-async-javascript/verify.mjs
node examples/resume-skills/module-2-async-javascript/verify.mjs 25-bounded
```

The verifier executes each case in its own Node.js process, checks exit status, empty stderr and exact stdout, and enforces a five-second timeout. A full run refreshes results.json; an individual run also prints its output.

Verified on Node.js v22.14.0. Every case uses ES-module mode except 19-cjs-tick, which intentionally uses CommonJS to compare top-level scheduling with 18-esm-tick. These outputs are context-labeled observations, not universal timing guarantees.

Coverage: callbacks; executor and resolution; chaining and completion ownership; error recovery and cleanup; await; sequential/concurrent composition; all/allSettled/any/race; microtasks; CPU blocking; timeout versus cancellation; fetch status/body boundaries; bounded worker pools; logical races; callback adaptation and required/optional dependency contracts.

The fetch example creates an ephemeral 127.0.0.1 HTTP server and closes it. No external services, credentials or packages are needed. Deadlines use local timers. Gate-controlled cases demonstrate ordering without relying on close wall-clock races.

Artifacts:

- cases.json: source, expected output, case IDs and module mode.
- verify.mjs: isolated runner and assertions.
- results.json: captured source/output and Node version.
- verification-output.txt: preserved full verification log.
- validation-summary.json and site-build-output.txt: chapter/site verification evidence.

The bounded pool accepts a finite dense array, collects every outcome, preserves input order and limits active work. It has no distributed coordination, rate window, retries, cancellation or persistence. The lost-update example demonstrates why asynchronous workflows still need atomic state changes.
