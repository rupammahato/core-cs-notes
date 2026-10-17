# M28: Resume project and experience deep-dives

Run `python verify.py` here with Python 3.12 or later. The model verifier uses only the standard library and the included project-only `resume-evidence.json`; the original PDFs must remain at the repository root for checksum verification. The recorded runtime is Python 3.12.10 with SQLite 3.49.1.

The 81 checks comprise 68 teaching-model/arithmetic checks and 13 document-provenance checks. They do not reproduce original employer/project code, production metrics, revenue or compliance.

- `hierarchy.py`: bounded tenant-scoped BFS on hand-authored relations; no authenticated HTTP or original org schema.
- `sla.py`: illustrative business-date calendar, versioned state transitions, transactional audit and deduplicated pending alert rows. No timezone scheduler, external sends or real bureau policy.
- `sheet_sync.py`: scoped external-ID SQLite upserts, explicit timestamp policy and custom nested patches; no OneDrive/MongoDB execution. The toy timestamp uniqueness contract is deliberately declared, not a general identity recommendation.
- `costs.py`: synthetic Decimal usage/rate normalization and metric arithmetic, not actual provider prices or a ledger.
- `verify.py`: named assertion evidence and observations. Temporary SQLite connections close before their directory is removed, including failure paths.
- `resume-evidence.json`: relevant excerpts from both user PDFs, pages and SHA-256 hashes; contact and education data omitted.

`extract_evidence.py` regenerates the catalogue using pypdf. The recorded extraction uses pypdf 6.20.1 already installed in `../module-23-rag/.venv`; no package installation was needed. From this directory:

```powershell
& ../module-23-rag/.venv/Scripts/python.exe -X utf8 extract_evidence.py
python verify.py
python author.py
```

`author.py` embeds four exact model sources and five observation blocks into the canonical chapter. `validate_site.py` checks fidelity, builds the existing handbook, verifies navigation/search/routes on an owned temporary loopback server and closes it. It uses the site's existing dependencies and does not start port 3000.

See `research-scope.json` for public self-report versus official-reference boundaries. The chapter includes seven short project pitches, seven two-minute expansion outlines, seven five-minute walkthroughs, 30 Q&As, ten practice tasks and twelve unchecked learning items. Unreviewed historical details remain labeled for reconciliation.
