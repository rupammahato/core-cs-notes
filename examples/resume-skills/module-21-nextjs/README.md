# M21: Next.js, API Routes and Tailwind

Part 23 practice fixture, recorded 15 October 2026 on Windows with Node v22.14.0. It deliberately uses Next.js 14.2.35, React/React DOM 18.3.1 and Tailwind 3.4.19 to match the resume's historical context. TypeScript 5.9.3 and playwright-core 1.64.1 support compilation and actual browser verification. The handbook site's separate Next.js 16/React 19/Tailwind 4 dependencies were not upgraded.

## Run

From the repository root in PowerShell:

```powershell
Set-Location examples/resume-skills/module-21-nextjs
npm ci
npm run verify
```

The verifier starts a controlled origin, builds the actual Next application, starts its production server on an ephemeral 127.0.0.1 port, opens an installed headless Chrome/Edge browser, executes checks and closes its resources. It searches the recorded browser installation paths; set M21_BROWSER to another compatible executable when needed. It does not download a browser. Installation needs registry access; runtime HTTP uses local fixtures. There is no persistent demo command, and port 3000 is unused. Docker is not started.

To reproduce handbook integration checks, install the study-guide dependencies, then run this from the repository root:

```powershell
python -X utf8 examples/resume-skills/module-21-nextjs/validate_site.py
```

The site validator uses a cached Google Fonts response fixture when available; otherwise the handbook build needs font network access. It starts and stops its own temporary production preview.

## Verified results

| Group | Checks |
| --- | --- |
| Production build/types/manifest | 4 |
| Rendering | 5 |
| Routing/layout lifetime | 4 |
| Server/client boundaries | 3 |
| App Route Handlers | 11 |
| Pages API | 5 |
| Data Cache/memoization/tag/ISR | 7 |
| Hydration/no-JS comparison | 3 |
| Browser API interaction | 2 |
| Middleware matcher | 2 |
| Streaming | 2 |
| Error boundary/recovery | 2 |
| Compiled Tailwind layout | 3 |
| Uncaught browser exceptions | 1 |
| **Total** | **54** |

The origin counts duplicate and subsequent reads, changes versions, holds a streaming dependency until explicitly released, and simulates a repairable 503. A request-time cache page demonstrates both within-render deduplication and cross-request persistent reuse. Tag invalidation uses a synthetic fixed test-control key. ISR verification waits for eventually refreshed output rather than assuming a fixed response ordering. Error recovery requests a fresh server payload and resets the boundary in a transition.

The public topic data is in memory. The dashboard cookie is untrusted display data, not authentication. The POST echo does not persist anything. Its parsed string limit is distinct from an ingress body-size limit; the Pages API separately tests a configured 1kb parser limit. Middleware adds a diagnostic header only for dashboard paths. The private environment marker is synthetic, not a credential.

## Files

- app/: actual App Router pages/layouts/handlers, including cache, ISR, streaming and error experiments.
- components/: client counter/hydration and submit-only API lookup islands.
- lib/: server-only public topic service and shared runtime message contract.
- pages/api/legacy-echo.ts: separately routed Pages API with its own parsing/method interface.
- middleware.ts: Next.js 14 matcher/header example.
- next.config.mjs / tsconfig.json / next-env.d.ts: framework and type configuration.
- tailwind.config.cjs / postcss.config.cjs / app/globals.css: Tailwind 3 compilation.
- origin.mjs / verify.mjs: counted/versioned/held origin and owned production verification lifecycle.
- package.json / package-lock.json: pinned dependency snapshot.
- fixture-build-output.txt / fixture-server-output.txt: actual framework build and server output; the server log includes the deliberate error experiment.
- verification-results.json / verification-output.txt / cleanup-results.json: named checks, observations and resource closure.
- browser-desktop.png / browser-mobile.png: actual layouts captured and inspected.
- dependency-audit.json: full historical dependency audit.
- content-validation.json / site-validation.json / validation-summary.json: source/output fidelity and handbook build/routes/search/cleanup checks.
- validate_site.py / site-smoke.mjs: reproduce handbook integration verification.

The chapter embeds 19 relevant source files exactly, four recorded observation objects, 30 interview Q&As, ten exercises and twelve unchecked learning items. .next/, node_modules/ and compiler caches are ignored generated artifacts.

## Historical dependency and scope limits

Next.js 14 is currently unsupported. The recorded full npm audit reports nine affected packages: two moderate, six high and one critical. These are package-level findings, not a demonstration of nine exploits. The report recommends major-version changes for some findings; no automatic force-upgrade was applied because that would replace the historical behavior under study. This local fixture is not a new production starter or a deployment recommendation.

No real login/database, durable mutation, Server Action execution, hosted Edge/CDN behavior, deployment, comprehensive screen-reader/WCAG suite or performance benchmark was performed. The local middleware run demonstrates request matching, not global Edge placement. Captured layouts and selected interaction checks establish the specific results only.
