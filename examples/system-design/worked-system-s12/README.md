# S12 authoring and site verification

This chapter uses the unchanged shared runtime/verification harness and S11 authority. From repository root:

```powershell
python examples/system-design/module-17-multi-tenant-rag/verify.py
python examples/system-design/worked-system-s12/author.py
python examples/system-design/worked-system-s12/integrate.py
python examples/system-design/worked-system-s12/validate_site.py
```

The last command validates all 22 sections, questions/tasks/checklists/mock, exact source/output and dependency fidelity, sync/navigation and footprint preservation. It builds once, checks published handbook/companion routes plus scoped search on an owned ephemeral preview, then closes the preview. Port 3000 remains stopped and Docker is not started. `--reuse-build` requires all relevant inputs to predate the recorded successful build.

The chapter fixture records 125 checks and six completed competing calls. Per-chapter JSON contains local results, selected micro-corpus observations, content metadata and cleanup. This folder's validation summary, site evidence and build/smoke logs record publication checks. Automated assertions do not mark learner mastery complete.

Scope is deterministic local orchestration: plaintext, feature-hash vectors, exact scan, extractive model, current permissions/citations, character-budget uncertainty and local deletion/redaction. No real model/embedding/vector API, external tools, stream, object storage, provider metering or production quality/performance is implied.
