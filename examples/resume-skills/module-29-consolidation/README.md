# M29: Consolidation and interview drills

Run `python verify.py` here with Python 3.12+ and Node.js 22+ on PATH. No package installation, Docker, cloud account or API key is needed.

The recorded run uses Python 3.12.10, Node.js v22.14.0 and SQLite 3.49.1. Fourteen isolated processes execute seven ES-module, four Python and three in-memory SQLite drills. Each JSON result is compared with its declared expected value, stderr must be empty, and all processes must exit. SQL connections are explicitly closed inside their drills.

The other 29 checks audit source paths, titles, slugs and SHA-256 hashes for M0–M28. The combined report contains 43 checks; it does not mean 43 production scenarios were executed. Earlier engine, HTTP, browser, hosted-service and model-quality claims are not rerun/revalidated by this chapter.

- `drills/` and `drills.json`: exact output-prediction sources and contracts.
- `module-catalogue.json`: canonical teaching-module references and revision prompts.
- `bank.py` / `revision-bank.json`: 36 confusable pairs, 60 rapid-fire Q&As, 16 debug cards, 24 self-test prompts and timing plans. These are editorial study material, not measured question frequencies or an automated user assessment.
- `verify.py`: isolated runtime and reference verifier; outputs/process cleanup are recorded in JSON.
- `author.py`: canonical chapter generator with exact source/output blocks and linked answer checkpoints.
- `validate_site.py`: content/count/link/timing fidelity plus production build and route/search checks using an owned temporary loopback server, closed afterward.

To regenerate after changing a teaching chapter or a predecessor link, run in order:

```powershell
python prepare.py
python verify.py
python author.py
```

`prepare.py` updates expected contracts/catalogue from explicit authored definitions. Review changed expected results before treating a new verification as evidence. It does not infer correctness from actual stdout.

No persistent model listener starts and port 3000 remains stopped. The main handbook's authored sequence is complete; the architecture companion roadmap/foundations/worked systems and product/analytics track remain separate planned work.
