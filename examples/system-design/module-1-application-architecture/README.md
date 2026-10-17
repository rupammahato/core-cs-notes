# A1: Application architecture and service boundaries

Real loopback HTTP with a strict TypeScript/Express backend and temporary file-backed SQLite. The service is callable without HTTP; persistence implements the port the service requires.

From this directory in PowerShell:

```powershell
npm.cmd run prepare:local
npm.cmd run verify
```

The recorded run uses Node v22.14.0, Express 5.3.0 and TypeScript 7.0.2. `node:sqlite` is experimental in this Node release and its synchronous operations block the event loop. Installed Node type definitions are newer than the runtime; only SQLite APIs supported by the verified runtime are used. This is a local lesson adapter, not a scalable production persistence recommendation.

The offline npm cache could not resolve the installed Express version. The verified setup uses `prepare-local.mjs`, which creates ignored directory links to the existing M5 Express/types installation and study-guide TypeScript/Acorn installation. It checks existing link destinations, fetches nothing and does not modify source installations. `package.json` records the dependency versions; a fresh registry installation was not verified. The TypeScript 7 package's CLI builds the fixture; Acorn parses emitted JavaScript imports for the runtime dependency audit.

- `src/notes.ts`: use-case validation, principal scope, repository port and typed rule failures.
- `src/sqlite.ts`: real SQLite scoped queries, conditional replacement, create-operation replay and transaction ownership.
- `src/http.ts`: ordered middleware, public lesson-token mapping, transport/controller/error contracts and out-of-band trace observer.
- `src/composition.ts`: concrete wiring and connection cleanup.
- `verify.mjs`: 67 named assertions: four runtime-import boundaries, 17 service/repository, four transaction and 42 real HTTP checks. Uses isolated temporary files/listeners and closes/removes them even on failures.
- `start.mjs`: optional manual server on an ephemeral loopback port; Ctrl+C closes the connection/listener and removes that session's temporary database.
- `author.py`: generates the chapter with four exact source blocks and five exact recorded observation blocks.
- `integrate.py`: updates actual availability, successor links, sidebar and root progress/footprint. It does not mark learner mastery complete.
- `validate_site.py` and `site-smoke.mjs`: content fidelity, build, navigation, route/search checks and owned-process cleanup. Use this chapter's current validation summary for the expanded site; previous chapter summaries are historical snapshots.

The published `lesson-alice`, `lesson-bob` and `lesson-other-tenant` credentials are loopback teaching data. They demonstrate mapping to a server-controlled principal, not OAuth, password handling, production sessions or TLS. Never expose this fixture publicly. Identity headers and body fields cannot override principal scope.

Create requires an owner/tenant-scoped `Idempotency-Key`; replay returns the saved original representation. Replace requires one numeric strong `If-Match` revision. Lists, weak tags and wildcard conditions are outside this API's documented subset. A lost replace response can yield a stale-precondition response on retry; no edit-outcome replay ledger is implemented.

Parallel HTTP edit checks run in one Node process with synchronous SQLite; they do not establish multi-process/distributed contention or production throughput. Proxy/gateway/BFF deployment, asynchronous PostgreSQL conversion, service extraction, outbox and durable events are explanatory proposals, not executed mechanisms here. No Docker, cloud/provider call, existing database mutation or persistent port-3000 server is required.

After changing behavior, run verification before regenerating evidence and content:

```powershell
npm.cmd run verify
python author.py
python integrate.py
python validate_site.py
```

Use Python 3.12 or later. The recorded site run uses the existing cached font-response fixture for the production build, then stops its owned preview process.
