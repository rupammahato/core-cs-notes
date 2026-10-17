# Module 1: JavaScript Fundamentals

Thirty dependency-free snippets used in the Resume Skills teaching chapter.

From the repository root:

```powershell
node examples/resume-skills/module-1-javascript/verify.mjs
node examples/resume-skills/module-1-javascript/verify.mjs 16-loop
```

The first command runs every snippet in a separate Node.js process using `--input-type=module`. The second runs one case and prints its output. Each case has a five-second timeout; the verifier checks exit status, empty stderr and exact stdout.

Verified on Node.js v22.14.0. ES modules use strict mode, and top-level `this` is `undefined`. Browser classic scripts and CommonJS have different top-level context; do not transfer these context-dependent predictions blindly.

- `cases.json`: case IDs, titles, source and expected output.
- `verify.mjs`: isolated execution and assertions.
- `results.json`: actual captured output and source for every case, refreshed by a full run.
- `verification-output.txt`: preserved verification log.
- `validation-summary.json`: chapter and website verification summary.

Coverage: types, aliases and argument passing; shallow/path/structured copies; numbers, equality and coercion; defaults; scope and TDZ; closures; receivers and arrows; prototypes/classes; destructuring; arrays/maps/sets; JSON; optional chaining; input validation and trusted-field ordering.

The loop example uses saved closures without timers. Async scheduling is covered separately in M2. These examples demonstrate language behavior and selected backend mistakes; they do not establish a complete authorization or production validation system.
