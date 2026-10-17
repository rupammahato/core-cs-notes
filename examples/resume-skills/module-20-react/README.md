# M20: React Fundamentals

Part 22 practice fixture. Recorded 15 October 2026: Windows, Node v22.14.0, React/React DOM 19.3.1, esbuild 0.28.2, playwright-core 1.64.1 and installed Chrome 155.0.8059.40. The handbook site's React/Next dependency tree is separate and was not upgraded.

## Run

From the repository root in PowerShell:

```powershell
Set-Location examples/resume-skills/module-20-react
npm ci
npm run build
npm run verify
```

playwright-core uses an installed compatible Chromium browser, without downloading a browser. The verifier searches the recorded Chrome/Edge paths. Set M20_BROWSER to another executable path when needed. Package installation needs registry access; verification uses actual browser pages and an owned same-origin loopback HTTP server.

For manual practice, run npm run demo and open its printed ephemeral URL. Ctrl+C stops it. Add ?strict=1 for root development Strict Mode, ?strict=1&production=1 for the production bundle comparison, or ?ignoreAbort=1 for the deliberately uncancellable transport race experiment. The Release held API reply and Recover fixture API buttons control local teaching failures; they are not production features.

The verifier closes its owned browser and HTTP server, with ephemeral host-loopback ports. Port 3000 is unused and Docker is not started. dist/ and node_modules/ are ignored generated files. The recorded dependency audit reported zero vulnerabilities; this is not a security guarantee.

## Verified results

| Group | Checks |
| --- | --- |
| State | 8 |
| Identity/keys | 6 |
| Effects | 6 |
| Strict Mode | 3 |
| Forms | 6 |
| Sharing/context/memo | 4 |
| Real HTTP/API states | 11 |
| Selected accessibility/layout | 5 |
| Uncaught browser exceptions | 1 |
| **Total** | **50** |

The suite exercises actual clicks/typing/keyboard/focus, replacement/updater snapshots, stored closure/ref behavior, nested copies, stable-key DOM reuse and an index-key counterexample, key reset/remount, dependency cleanup, root development/production effect behavior, controlled forms/derived results, context and observed memo commits, loading/empty/error/retry/schema/escaping, browser abort and an old real HTTP response deliberately completed after a newer one.

The race server holds a reply until explicitly released, so stale-result ordering does not depend on a narrow timed sleep. The normal loader passes AbortSignal; the special loader ignores it to verify that inactive-result suppression still protects the screen.

## Files

- main.jsx: panel composition and root Strict Mode selection.
- StateLab.jsx / IdentityLab.jsx / EffectsLab.jsx / FormsLab.jsx / ContextLab.jsx: teaching mechanisms.
- useTopics.js / TopicsPanel.jsx: validated read-only HTTP lifecycle and presentation.
- diagnostics.js: test-only observations recorded in event handlers/effects, not render.
- styles.css: semantic-control styling, visible focus and a responsive grid.
- build.mjs: separate development/production esbuild bundles; React Compiler disabled.
- server.mjs / serve.mjs: owned API/assets and optional manual entrypoint.
- verify.mjs: actual headless-browser interaction assertions and cleanup.
- package.json / package-lock.json: pinned source and dependency snapshot.
- verification-results.json / verification-output.txt / cleanup-results.json: actual check results and resource closure.
- browser-desktop.png / browser-mobile.png: actual captured layouts inspected during authoring.
- browser-build-output.txt / dependency-audit.json: build and audit results.
- content-validation.json / site-validation.json / validation-summary.json: chapter/source and handbook-site checks.
- validate_site.py / site-smoke.mjs: reproduce source fidelity, handbook build/routes/search and listener cleanup checks. Run python -X utf8 examples/resume-skills/module-20-react/validate_site.py from the repository root after installing the study-guide dependencies. A cached Google Fonts response fixture is used when available; otherwise the Next.js build needs font network access.

The chapter embeds the seven teaching component/hook files exactly and includes recorded snapshot/identity/lifecycle/race JSON, 30 interview Q&As, ten exercises and 12 unchecked learning items. The index-key and ignore-abort paths are explicitly labelled counterexamples.

No comprehensive screen-reader/WCAG or cross-browser audit, framework SSR/hydration, React Compiler, real authentication/database, production security/compliance or performance benchmark was performed. Fifty browser checks demonstrate these selected mechanisms, not all production guarantees.
