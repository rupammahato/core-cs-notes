# S13: Analytics event pipeline and dashboard

From repository root, run `python examples/system-design/module-18-analytics-event-pipeline/verify.py`. Standard-library Python 3.12 and SQLite; owned temporary database/HTTP resources are closed/removed. Port 3000 stays unused.

`pipeline.py` implements scoped immutable occurrence identity, durable atomic intake, explicit UTC event time, bounded aggregate processing with effect/frontier transactions, exact signup cohorts, a trusted watermark/late policy, local generation rebuild and subject removal/replay markers. The dashboard is an actual JSON read model with metric/freshness metadata, not an executed browser chart.

`verify.py` records 78 local checks and four competing calls, including conflict rollback, checkpoint/generation rollback, normalized-time replay, late data, tenant scope, privacy, reopen and real HTTP. Shared support is reused unchanged from `../worked-systems-s4-s6/`. No Kafka/Beam cluster, connector, automatic watermark estimator, secure erase or production capacity test runs.

`lesson.md` is the authored prose. `../finish-track/author.py` embeds exact code/output into Part 20. See `../finish-track/README.md` for the complete author/integrate/audit/build workflow.
