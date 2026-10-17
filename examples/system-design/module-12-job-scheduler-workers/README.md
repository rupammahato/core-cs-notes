# S7: Job scheduler and worker platform

Run `python examples/system-design/module-12-job-scheduler-workers/verify.py` from the repository root. Standard-library Python; no dependency install or persistent server. The fixture owns temporary SQLite files and an ephemeral HTTP listener, then closes/removes them. Port 3000 stays unused.

`scheduler.py` implements one-off jobs, coalesced interval occurrences, tenant admission, fenced leases, bounded renewal/retries and a transactional local counter receipt. `verify.py` records 65 checks in `verification-results.json`, including two competing claims, effect-before-ack reopen recovery and rollback. It deliberately omits ACK and reopens; it does not kill a process. No broker, cron daemon or remote effect is executed.

`lesson.md` is the authored teaching source. The batch `../worked-systems-s7-s9/author.py` embeds exact local/runtime source and recorded output into Part 14. See the batch README for integration and site validation.
