# S10: Load balancer and distributed cache

From repository root run `python examples/system-design/module-15-load-balancer-distributed-cache/verify.py`. Standard-library Python; owned temporary SQLite/HTTP resources are closed and removed. Port 3000 stays unused.

`cache.py` implements deterministic ring placement, backend admission/drain labels, bounded copied LRU caches, TTL, source-head validation, guarded late fills, controlled failure/rejoin and membership epochs. `verify.py` records 69 checks including a 2,000-key placement sample, four competing calls, source rollback/reopen and actual edge HTTP.

Nodes/backends are in process. There is no actual upstream proxy, network replication, failure detector, consensus or throughput benchmark. Every cache read still probes the canonical source version/deletion state. The logical miss counter is not a count of every SQL request.

`lesson.md` is the teaching source. `../worked-systems-s10-s11/author.py` embeds exact code and observed outputs into Part 17; the batch README documents integration and site validation.
