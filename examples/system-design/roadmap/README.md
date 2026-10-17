# Architecture companion roadmap

The master roadmap and A0 are authored. A1-A4, fourteen worked designs and consolidation remain planned. The roadmap generator derives each teaching entry's availability from its source file.

`author.py` generates the roadmap, structured syllabus and an exact copy of the 60 compiled question rows from the existing root question bank. `verify.py` checks numeric mappings, filenames, dependency order/cycles, existing resume links, estimate arithmetic, question mappings/source fidelity and available-versus-planned status. These are document audits, not executed architecture prototypes.

```powershell
python author.py
python verify.py
```

Python verification uses the standard library. This folder's site evidence records the original roadmap-only publication snapshot; use the latest teaching chapter's site validator for the current page tree. Site validation uses the existing Node/Next/Fumadocs dependencies and an owned temporary preview, closed afterward. Port 3000 remains stopped. No package installation, Docker startup, cloud/payment/model call or external application write is required for the roadmap.

See `source-provenance.json`, `verification-results.json`, `content-validation.json` and site evidence for the exact scope. Expected first-pass hours are editorial estimates; the script verifies only their arithmetic. Checklists are not assertions of learner mastery.
