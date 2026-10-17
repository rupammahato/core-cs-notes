# S6: Social feed and photo sharing

Run `python verify.py` here with Python 3.12+. Recorded runtime: Python 3.12.10 / SQLite 3.49.1. `feed.py` implements a bounded chronological hybrid feed and JSON HTTP contract with shared helpers from `../worked-systems-s4-s6/`.

67 named checks cover owned ready-media/version binding, stable post replay, atomic publication/job, partial fanout rollback/cursor progress, overlapping backfill, pull merge, viewer/tenant-scoped signed keyset cursors, current follow/block/delete/media filtering, four competing calls and actual HTTP.

Media state is trusted fixture metadata, not real image bytes, S3 projection integration or private CDN access. The public cursor secret and bearer map are lesson values. No ranking/recommendation engine, production auth/TLS, distributed queue/cache, global revocation or capacity claim is included. Already delivered pages/media cannot be retracted.

Limits are 256 retained posts/tenant, 16 follows/viewer, page and batch sizes at most 50. The implementation deliberately scans its bounded candidate set; it is not a production query plan. `lesson.md` contains authored prose; follow the [batch instructions](../worked-systems-s4-s6/README.md) for generation/integration and one full site check. All owned resources/temporary files close or are removed; port 3000 and Docker remain stopped.
