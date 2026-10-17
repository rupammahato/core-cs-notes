# S3: File upload, storage and processing service

Run `python verify.py` with Python 3.12 or later. Recorded runtime: Python 3.12.10 / SQLite 3.49.1. Only the standard library is needed. The owned local filesystem must support create-only hard links; the recorded Windows run does. No cloud credentials, external uploads, Docker or existing database service is used.

- `objects.py`: opaque validated storage keys, complete staging/install, immutable same-byte retry, bounded reads and exact owned-parent checks before cleanup. User display names never become disk paths.
- `uploads.py`: owner/tenant-scoped create replay, fixed custom upload capability, object verification, atomic completion/job, quarantine, bounded leased claims, guarded result publication, private download, tombstones and inventory reconciliation.
- `http_api.py`: actual owned loopback create/status/complete/delete/download API and capability-only PUT. Public lesson bearer tokens and secret are demo values, not production auth/TLS or S3 signatures.
- `estimates.py`: hypothetical transfer/storage/CPU/egress/unfinished-part calculations, not a load or cost benchmark.
- `verify.py`: 121 named assertions: 17 validation, 23 intake, 19 processing, 19 lifecycle, 27 HTTP, four concurrency, eight estimates and four cleanup. Six competing calls cover actual PUT/completion pairs and two independent thread-owned processing claims.
- `author.py`: chapter generator with four exact source files, six outputs, 30 Q&As, ten exercises and a 45-minute mock.
- `integrate.py`: publishes S3 in Worked Systems, refreshes progress and advances only the next section to S4.
- `validate_site.py` and `site-smoke.mjs`: content/source/output/link fidelity, production build, bounded route sweep, navigation/search and owned preview cleanup.

The fixture accepts immutable 1–1024-byte `.txt` objects with declared text/plain, exact size/SHA-256 and a ten-second transfer window. It decodes UTF-8 and rejects NUL/a lesson marker; this is not antivirus, a general parser or a file-safety guarantee. Rejected/failed files remain private. Only ready originals can be downloaded by their authenticated owner; attachment/no-store/nosniff are verified.

Create replay retains the original ID/deadline and never renews expired intent. Completion verifies actual bytes and creates one durable job. Every claim counts toward three attempts, including crashes. Stale/expired/deleted workers cannot publish. A failed metadata commit can leave a real derived artifact; inventory cleanup and publication retry demonstrate recovery.

All legitimate local object writes, publication and cleanup hold the same SQLite write authority. That intentionally serializes file I/O and metadata and is not a scalable cloud direct-upload protocol. The collector only unlinks exact files inside resolved private object areas. It is a full-inventory teaching implementation, not a batched lifecycle service. Its safety assumes a trusted owned filesystem root and no hostile local process manipulating paths.

Direct S3 grants, multipart sessions, browser CORS, PDF/image/video parsers, safe sandboxing, proactive tenant byte reservations, distributed coordination, lease renewal/backoff, automatic reprocess and production streaming/deadlines are discussed rather than implemented. An application tombstone does not automatically revoke an independent cloud PUT grant. The local PUT handler explicitly rechecks metadata; do not transfer that property to S3 by analogy.

The 128-row cap includes tombstones/replay records and is not a production retention or tenant-quota policy. Cleanup expires unfinished uploads and removes unreferenced/deleted/expired bytes; it does not implement retention for rejected/failed/ready files or metadata deletion. Missing/corrupt ready source is an explicit 503. Already delivered/in-flight download bytes cannot be retracted.

After changes:

```powershell
python verify.py
python author.py
python integrate.py
python validate_site.py
```

The harness checks its resolved temporary root before removing it, closes owned connections/listeners, joins all serving/handler/worker threads and removes session files. Port 3000 and Docker remain stopped; no persistent service starts. Site checks use six concurrent routes and the cached font fixture when available. Use this chapter's summary for the expanded site; previous summaries are historical snapshots.
