# A2: Data, caching and scaling

Run `python verify.py` with Python 3.12 or later. The recorded run uses Python 3.12.10 and SQLite 3.49.1. No third-party Python packages, database server, Docker, Redis, credentials or network listener are required.

- `data.py`: real temporary SQLite schema seeded with 12,000 notes, scoped listing, composite index, keyset pagination, query-plan/VM-instruction profiling and conditional replacement. Supplied tenant/owner context is trusted fixture input, not authentication.
- `cache.py`: process-local TTL/LRU cache, immutable values, single-flight, cancelled-waiter shielding and a scalar local invalidation epoch. Entry count is bounded; bytes and unique in-flight loads are not. The owning service must supply deadlines/admission limits.
- `scaling.py`: hypothetical source-demand/connection arithmetic and stable-hash modulo placement under a weighted hot-tenant workload. No capacity, live routing or shard migration test.
- `verify.py`: 91 named assertions: 12 query, 16 pagination, 23 basic cache, ten single-flight, eleven invalidation, four independent-cache, two cleanup and thirteen scaling-model checks.
- `author.py`: generates the teaching chapter with three exact source files and nine exact observation blocks from `verification-results.json`.
- `integrate.py`: updates actual chapter availability, sidebar, predecessor continuation, root progress and footprint. Learner checklists remain unchecked.
- `validate_site.py` and `site-smoke.mjs`: source/output fidelity, internal links, production build, routes/navigation/search and owned-preview cleanup.

The query experiment compares equivalent pages and SQLite VM instruction counts; it does not measure production latency, disk reads or PostgreSQL behavior. The real between-page insert illustrates offset duplication and keyset continuation under immutable ordering, not a stable snapshot or an opaque HTTP cursor implementation.

Async tests use event barriers and an injected TTL clock rather than timing sleeps. A naive cache reproduces stale refill after a canonical write and cache deletion. The local epoch prevents that cooperating single-cache interleaving, but independent caches over two SQLite connections remain stale until expiry without broadcast. Both caches run in one verification process. The epoch is process-local, conservatively affects unrelated in-flight loads and is not thread-safe or a distributed fencing mechanism.

No loader failures or missing results are cached. A cancelled waiter leaves shared work available for others; cleanup cancels pending work and clears entries. The cache does not implement Redis operations, distributed locks, permission revocation, replica routing or globally current reads. The separate A1 HTTP backend keeps its original API unchanged.

Reproduction order after changing behavior:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

Verification closes both SQLite connections and cache tasks before removing its owned temporary database directory. Site validation uses an ephemeral loopback preview and closes it afterward; port 3000 remains stopped. The build uses the existing cached font-response fixture when available. Use this chapter's validation summary for the current expanded site; older chapter summaries are historical snapshots.
