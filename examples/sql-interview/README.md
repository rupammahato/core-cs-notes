# SQL interview lab

Thirty problem-led SQL exercises over invented commerce and event data. Queries, hints, worked outputs and follow-ups accompany the seven-file SQL Interview Notes subject. Existing DBMS and product notes remain unchanged.

## Run

From the repository root:

```powershell
python examples/sql-interview/lab.py Q19
python examples/sql-interview/verify.py
python examples/sql-interview/build_book.py
python examples/sql-interview/validate_content.py
```

Python standard library only. Verified on Python 3.13.15 and SQLite 3.50.4. The runner uses owned in-memory databases with foreign keys enabled and bound named parameters; it creates no persistent database or listener. All 16 connections close after verification. No PostgreSQL server or external account is used.

The **86 checks** comprise 30 baseline outputs, 30 reversed-insertion checks, 12 changed-input scenarios, six deliberately incorrect-query counterexamples, four constraint checks, three actual query-plan checks and one source-preservation check. Outputs are compared with independent Python loops/maps/date arithmetic in reference.py, not with saved outputs produced by the same SQL. That reference is still a teaching implementation, not proof of every possible input or a real metric contract.

Each queries/qNN.sql file is standalone against schema.sql and uses the shared parameters.json dictionary. lab.py loads fixture.json in foreign-key-safe order and executes the selected query. Money is integer cents; timestamps are UTC epoch seconds. Customer signup timestamps are fixture cohort anchors at UTC midnight. Other timezone/cohort definitions require deliberate changes.

## Evidence and boundaries

query-output.json contains the actual SQLite rows, counterexamples.json contains executed wrong-query results, and query-plans.json preserves actual EXPLAIN QUERY PLAN rows. The plan experiment adds 10,000 historical orders to a separate in-memory connection, compares the same result before/after a composite index and records the access paths. No timing benchmark or production speedup is asserted.

canonical_events is a teaching view: it rejects conflicting event identities across the supplied snapshot, checks tenant/customer agreement and picks the earliest consistent delivery. Its full-snapshot quarantine is not a historical correction/retraction engine. The late-event exercises use conflicts already present at both cutoffs and change which consistent events are known.

Missing bills remain unknown. Known contribution can be zero with a visible missing count; it is not a complete invoice amount. No succeeded payment in the supplied complete payment ledger means zero confirmed payment, rather than zero billing. Real extracts need completeness, refund-time and adjustment policies. Q26 is an authorized administrative audit, not a tenant-facing data-access recipe.

problems.json stores prompts/hints/traps/follow-ups; build_book.py writes the four worked-query chapters from the exact SQL and verified results. The roadmap, solving method and consolidation are authored separately. validate_content.py checks query/output fidelity, links, coverage and the byte-preservation snapshot of all 128 earlier handbook files. site-smoke.mjs checks the built site and search using its own temporary preview and closes it. Port 3000 remains stopped.

Primary documentation and dialect boundaries are recorded in research.json. The book's problem selection, mocks and suggested schedules are editorial practice material, not measured company interview frequencies. Manual solving, explaining and mock assessment remain learner work.

After syncing and building study-guide, run `node examples/sql-interview/site-smoke.mjs` from the repository root to check every page route, the new chapter content and subject-filtered search. The script creates and closes its own temporary loopback preview. `content-validation.json` records content/source audits separately from the 86 runtime checks; `site-validation.json` records the website checks. The recorded build used local font responses for this machine's network-restricted environment; the site's normal font configuration is unchanged.
