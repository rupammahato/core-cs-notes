# Module 5: Express.js and Backend Application Structure

A layered public quote API, sixteen isolated runtime examples, 39 API checks and five TypeScript boundary checks.

Verified versions: Express 5.3.0, body-parser 2.3.0, @types/express 5.0.6, TypeScript 7.0.2 and Node.js v22.14.0. Express and its declaration dependencies are isolated here and pinned by package.json/package-lock.json. The notes website dependencies are unchanged.

From the repository root:

```powershell
node examples/resume-skills/module-5-express/verify.mjs
node examples/resume-skills/module-5-express/verify.mjs 09-async-five
node examples/resume-skills/module-5-express/verify-api.mjs
node examples/resume-skills/module-5-express/start.mjs
```

The manual API listens on 127.0.0.1:3105, separate from the notes website at port 3000. Stop it with Ctrl+C; change the launcher port if occupied.

For a fresh checkout, install this isolated package lockfile:

```powershell
npm --prefix examples/resume-skills/module-5-express ci --ignore-scripts --no-audit --no-fund
```

The full verifier uses the compiler at study-guide/node_modules/typescript/bin/tsc. Those workspace development dependencies must be installed for typed checks, or set PLACEMENT_TSC_PATH to a compatible compiler script. Runtime-only verification is available through verify-runtime.mjs.

Routes:

- GET /health: basic availability response.
- GET /api/products/:productId: selected public product fields; implicit HEAD is supported.
- POST /api/quotes: application/json only, one-kilobyte parser limit, compression disabled; validate productId and quantity, use stored price, check availability, return a quote.

Quotes do not reserve stock, create orders or charge payments. The repository uses seeded process memory and a simulated async interface, not a database. The method policy on known API paths explicitly returns 405/Allow and intercepts OPTIONS.

Application source: app.mjs, validation.mjs, controllers.mjs, service.mjs, repository.mjs, errors.mjs and start.mjs. createApp constructs without listening and accepts repository/observation dependencies for meaningful failure and concurrency checks.

Evidence:

- cases.json, verify-runtime.mjs and results.json: sixteen ES-module cases with source/captured output; each has a ten-second process timeout.
- http-cases.json, verify-api.mjs, http-results.json and http-verification-output.txt: 39 API groups, including downstream-call boundaries and controlled concurrent requests.
- typed/, tsconfig files, verify-types.mjs, type-results.json and type-verification-output.txt: accepted typed boundary, expected TS18046 rejection, and valid/invalid/missing-middleware runtime outcomes. Compiler calls have ten-second timeouts.
- verify.mjs and verification-output.txt: full suite entry point/log.
- validation-summary.json and site-build-output.txt: chapter/site verification.

HTTP helpers bind ephemeral IPv4 loopback listeners with two-second request deadlines and close them. Request traces remain in the verification observer rather than the public API response. node_modules, installation cache and emitted dist are gitignored.

Coverage includes middleware order/termination, next versus async completion, error dispatch, route skipping, mounted URL views, repeated queries, nested parameters, parser order/schema limits, raw bytes, returned async errors, callback forwarding, HEAD/404 and Express 5 path syntax.

The typed companion starts ReqBody as unknown and checks optional validated locals. Its runtime missing-middleware case demonstrates that handler types do not prove registration order. The Express 4 comparison in the chapter is documentation-based; only Express 5 was executed.

This is an unauthenticated loopback learning API. Authentication/authorization, real transactions, durable jobs, deployment, client-abort/partial-response behavior and OS signal delivery are outside the verified scope. Startup/shutdown launcher syntax is checked; functional tests are not performance benchmarks.
