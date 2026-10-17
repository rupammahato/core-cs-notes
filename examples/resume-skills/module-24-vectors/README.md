# M24: Embeddings, Pinecone and pgvector

Real native PostgreSQL 16.15 / pgvector 0.8.6 checks using authored vectors. Pinecone examples construct JSON request bodies only; no SDK, hosted calls, embedding model, keys or charges.

Run from the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-24-vectors/.venv
examples/resume-skills/module-24-vectors/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-24-vectors/requirements-lock.txt
examples/resume-skills/module-24-vectors/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-24-vectors/prepare_runtime.py
examples/resume-skills/module-24-vectors/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-24-vectors/verify.py
```

`prepare_runtime.py` downloads pinned conda-forge native packages, verifies SHA-256 hashes in `runtime-packages.json` and extracts a workspace-only prefix. It runs no installer or package activation scripts. Package caches and portable binaries are ignored. Package metadata/licenses remain in the archives; `runtime-provenance.json` records engine versions and package count. No installed PostgreSQL files or services change. The optional resolver is used only when creating a new lock; delivered reproduction uses the recorded lock.

`cluster_runtime.py` creates a new temporary cluster, verifies its data directory, uses public test credentials on an ephemeral loopback port and closes/removes it in `finally`. The wrapper prepends native DLL lookup paths for this Python process only and restores them afterward. `M24_PG_BIN` can select another already prepared, compatible PostgreSQL/extension installation.

The first experimental MinGW build against installed PostgreSQL 18 failed at load time. Its two test clusters were stopped and removed, and those build files were discarded. The delivered portable runtime avoids that compiler/ABI mismatch; `setup-recovery.json` records the recovery. This failure is not included in the passing checks.

The recorded 92 checks cover math (12), space validation (11), local Pinecone body contracts (12), engine behavior (11), lifecycle (12), retrieval (8), authorization (8), ANN/query plans (15), and cleanup (3). `verification-results.json` names each assertion and records observations. `cleanup-results.json` records shutdown evidence.

Application search uses exact three-dimensional vectors. ANN uses 1,000 seeded eight-dimensional vectors, five queries and k=5. The test verifies real HNSW/IVFFlat plans, compares with exact IDs and exercises filtered HNSW underfill/iterative scanning. Graph/group construction may vary between runs. These data do not establish semantic relevance, production latency or capacity. Disabling sequential scans is a diagnostic fixture setting, never an application recommendation.

`vectors.py`, `schema.sql`, `store.py`, and `pinecone_contract.py` are embedded verbatim in the chapter. `verify.py` orchestrates the database checks. The application role and tenant-setting design assume a trusted backend; credentials must not be exposed to untrusted SQL clients. Deployed systems should separate read/publish roles and extend canonical generation guards.

`validate_site.py` checks chapter/source/output fidelity, syncs notes, builds the handbook and runs an owned ephemeral website process through `site-smoke.mjs`. Both database and site processes stop; port 3000 and Docker stay stopped. The site build can use the previously recorded local Google-font response fixture when present.

Next module: M25, LangChain, LangGraph and LlamaIndex.
