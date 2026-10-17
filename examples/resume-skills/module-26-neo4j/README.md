# M26: Neo4j and graph-backed applications

Actual Neo4j Community 2026.09.0, explicitly selected Cypher 5, Python driver 6.4.1 and portable Zulu Java 21.0.12.1 on Windows. Synthetic concept/source graph; no hosted service, model, APOC or GDS.

Run from the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-26-neo4j/.venv
& examples/resume-skills/module-26-neo4j/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-26-neo4j/requirements-lock.txt
& examples/resume-skills/module-26-neo4j/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-26-neo4j/prepare_runtime.py
& examples/resume-skills/module-26-neo4j/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-26-neo4j/verify.py
```

The prepare helper downloads official vendor ZIPs and verifies SHA-256 hashes pinned in `runtime-packages.json`. Archives and extracted distributions/licenses stay in ignored `.packages/` and `.runtime/`; no installer, service registration or machine Java configuration is used. `runtime-provenance.json` records exact URLs/hash sources and verification.

`LocalGraphServer.java` starts an actual embedded engine with an ephemeral loopback Bolt connector. `runtime.py` compiles it using the portable JDK, launches one hidden native Java process, verifies readiness through the official driver and signals shutdown via stdin. The Java helper calls `dbms.shutdown()`; the verifier closes the driver, waits for exit, probes the port, validates the owned temporary path and removes database files. Maximum heap is 256 MiB and page cache 64 MiB for this tiny fixture, not production sizing.

Authentication and TLS are disabled only for the isolated local fixture. Tenant/read/write checks are trusted application contracts; database-level auth/RBAC/isolation is not verified. Do not expose the database credential or accept client-created Principal objects in deployment. No existing database service changes; Docker and port 3000 remain stopped.

The 76 checks cover engine/version (2), graph model (5), Cypher/null/parameter behavior (11), constraints (3), CREATE/MERGE (6), traversal (7), application authorization (8), input bounds (7), transaction rollback (5), concurrent correctness (4), query plans (3), deletion (4), current source retrieval (7) and cleanup (4).

The graph includes a cycle, a shared neighbor and intentionally invalid cross-tenant links. The service bounds depth/count, scopes every path node/relationship, rejects stale/deleted source evidence and parameterizes data. A small allowlisted integer controls traversal syntax. The verifier demonstrates that endpoint-only predicates can follow an invalid private intermediate route.

Concurrency uses separate sessions in four worker threads. Eight upsert calls leave one constrained identity; twenty database-dependent counter updates leave twenty. The suite does not measure retry occurrence, throughput, production latency or forced timeout behavior. EXPLAIN/PROFILE verify actual index lookup, not a performance benchmark.

The four exact sources embedded in the chapter are `schema.cypher`, `fixtures.py`, `service.py` and `LocalGraphServer.java`. `verify.py` records every assertion and observation in `verification-results.json`; `cleanup-results.json` records process/port/data cleanup. Dependency locks/checks and content/site reports make the result reproducible. `pip check` verifies dependency consistency, not vulnerabilities.

`validate_site.py` checks chapter/source/output fidelity, syncs/builds the handbook and uses `site-smoke.mjs` for an owned temporary preview. The preview closes. Next: M27, system-design bridge through the load balancer.
