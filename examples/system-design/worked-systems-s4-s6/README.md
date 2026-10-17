# S4–S6 worked systems

This batch completes assigned-seat booking, chat and a hybrid photo-feed metadata service. Each has its own authored lesson, runnable source, verifier and named evidence. The shared runtime uses Python's standard library, SQLite and an owned ephemeral loopback HTTP server. Public lesson credentials are not production authentication.

From the repository root:

```powershell
python examples/system-design/module-9-booking-reservations/verify.py
python examples/system-design/module-10-chat-messaging/verify.py
python examples/system-design/module-11-social-feed-photo-sharing/verify.py
python examples/system-design/worked-systems-s4-s6/author.py
python examples/system-design/worked-systems-s4-s6/integrate.py
python examples/system-design/worked-systems-s4-s6/validate_site.py
```

- S4: 57 checks; atomic assigned-seat/group ownership, fixed expiry, late-payment/refund intent, exact custom signed callback and rollback. No real money/provider/refund execution.
- S5: 59 checks; durable room sequence/replay, bounded catchup, lossy hint recovery, current membership, reported-read merge and restart. Actual transport is HTTP polling; no WebSocket protocol, human-read proof or distributed gateway is implemented.
- S6: 67 checks; owned ready media/version references, batched fanout/cursor rollback, pull merge, graph backfill, scoped pagination and current local privacy filters. Media is a trusted lifecycle metadata fixture; no image bytes, S3 integration, ranking engine or CDN is implemented.

Each chapter contains 30 Q&As, ten practice tasks, twelve learner checklist items and a 45-minute mock. Its generated Markdown embeds the exact shared runtime, domain code and recorded observations. These are local mechanism checks, not production capacity, provider interoperability, distributed coordination or power-loss tests.

`verification.py` closes owned HTTP/SQLite resources, joins threads and verifies the absolute temporary root before cleanup. Port 3000 and Docker remain stopped. `validate_site.py` checks all three chapter structures and sources, builds once, sweeps old/new routes in bounded batches, checks scoped search/navigation and closes its preview. Use this batch summary for the expanded site; previous summaries are historical snapshots.
