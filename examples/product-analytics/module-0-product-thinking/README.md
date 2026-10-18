# P0: product-thinking worksheet

Run from the repository root with Python 3.13 (verified on 3.13.15; standard library only):

```powershell
python -X utf8 examples/product-analytics/module-0-product-thinking/workshop.py
python -X utf8 examples/product-analytics/module-0-product-thinking/verify.py
```

`workshop.py` computes RICE scores, separates mandatory protections from discretionary ranking, validates declared requirement/check links, summarizes supplied check states and lists declared change dependencies. It starts no server and accesses no account.

`case.json` is entirely synthetic, including the five `passed` and three `pending` acceptance-criterion states. No candidate-portal tests produced those states. Changing all supplied states to passed changes worksheet readiness, not real-world release approval.

`verify.py` executes **53 checks** against the worksheet, covering arithmetic, estimate boundaries, stable ties, mandatory-work handling, missing/duplicate links, pending/failed states, change impact and evidence preservation. It writes `verification-results.json` and `worksheet-output.json`; runtime and scope appear in the evidence. Decimal arithmetic avoids binary floating-point representation artifacts; RICE remains a rough decision aid.

The helper assumes already structured input. It is not a general JSON-schema validator, prioritization optimizer, dependency crawler, research tool, compliance assessment or product implementation. Reach periods and effort units must be consistent; the program cannot establish their truth. Its deliberately simple traceability policy requires all declared criteria to pass and rejects unreferenced checks. Real delivery policies may be more complex.

Figma prototyping, Notion organization, usability sessions and keyboard exercises remain manual. No user interviews or causal impact measurements were performed.

`validate_content.py` audits source/output fidelity, planned-section links and preserved existing handbooks. `site-smoke.mjs` starts a temporary production preview on an automatically selected loopback port, checks navigation and scoped search, and closes its own process. Port 3000 is not used.

Production integration passed on 18 October 2026: TypeScript, 128 static pages, 124 successful page routes and scoped searches for the new and existing subjects. See `validation-summary.json`. The first npm/PowerShell invocation dropped the intended webpack flag and stalled in Turbopack; its diagnostic log is preserved. Direct `node node_modules/next/dist/bin/next build --webpack`, after the sync step, passed with the existing cached-font fixture. No website source workaround was needed.
