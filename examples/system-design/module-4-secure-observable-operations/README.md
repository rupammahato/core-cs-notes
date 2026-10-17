# A4: Operating a secure and observable system

Run `python verify.py` with Python 3.12 or later. The recorded run uses Python 3.12.10 and SQLite 3.49.1. No third-party packages, Docker, cloud identity, object store, antivirus or external telemetry backend are required.

- `policy.py`: current membership/role checks, tenant/owner-scoped note/list/download access, transactional fixed-window request quota and private generated-key upload quarantine with retained-byte limits. Published lesson tokens map trusted fixture principals; they are not production authentication.
- `server.py`: an owned ephemeral loopback HTTP API, minimal liveness/readiness, bounded application admission, drain state and selected privacy-aware in-memory logs/counters/request events. Python's standard-library server is not for public production use.
- `indicators.py`: offline authored SLI samples, explicit nearest-rank percentiles, exact target/error-budget arithmetic, a confidentiality gate and hypothetical capacity/cost assumptions.
- `verify.py`: 93 named assertions: 17 HTTP policy, 24 upload, seven quota, eleven lifecycle, five saturation, nine telemetry, two cleanup, thirteen indicator and five planning checks. Four owned HTTP servers close after verification; two quota competitors use independent SQLite connections.
- `author.py`: generates the chapter with three exact sources and nine exact recorded observation blocks.
- `integrate.py`: publishes A4, records all five foundations authored and advances only the next planned section to S0. Worked designs and learner mastery remain incomplete.
- `validate_site.py` and `site-smoke.mjs`: source/result fidelity, authored links, production site build, routes/navigation/scoped search and owned-preview cleanup.

The upload lesson accepts 1–1024 bytes and a bounded `.txt` filename/MIME claim. It stores bytes privately under an application-generated key, starts pending and approves only matching size/digest and valid NUL-free UTF-8. Pending/rejected objects cannot be downloaded; approved content uses attachment/octet-stream/nosniff/no-store. This is not malware scanning, archive processing or arbitrary-document safety. Database metadata and filesystem bytes are separate stores; exception cleanup does not prove orphan-free process-failure recovery. Retained rejected/pending files still count against the 2048-byte tenant budget.

The runtime's admission gate bounds application work, not all sockets/handler threads. Probe dependency state is injected, and draining is invoked directly rather than through an operating-system signal or Kubernetes rollout. A held-work burst yields two accepted completions and six overload responses; it is deliberately not a sustainable throughput benchmark. Socket timeout is not an end-to-end deadline.

Logs omit tokens, private content, filenames, raw resource/query values and exception details; metrics use bounded method/route-template/status-class dimensions. Diagnostic buffers retain only 128 records and are not a complete audit trail. The trace is an ordered local event list, not an OTel span/export deployment. Server write timing is distinct from client-observed completion; a failed write can still retain an attempted status.

SLI samples and cost/workload inputs are authored offline data, not the HTTP timing sample or a cloud price. Eligible 429/503 outcomes and slow successes remain bad events; a separate confidentiality violation fails acceptance even if quantitative success is perfect. No production SLO, multi-window alert or disaster-recovery timing is measured.

Reproduction order after changing behavior:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

Verification joins serving/handler threads, closes SQLite connections and removes its exact temporary database/private-vault directory. Site validation closes its own ephemeral preview; port 3000 and Docker remain stopped. The site build uses the existing cached font-response fixture when available. Use this chapter's validation summary for the current expanded site; prior chapter summaries remain historical snapshots.
