# M15 research — caching, jobs and ingestion

Primary-source research refreshed on 14 October 2026. The teaching chapter and local execution evidence are recorded separately.

Primary sources:

- Redis cache-aside: https://redis.io/docs/latest/develop/use-cases/cache-aside/
- Redis eviction: https://redis.io/docs/latest/develop/reference/eviction/
- Cloud Tasks delivery/order limitations: https://docs.cloud.google.com/tasks/docs/common-pitfalls
- Cloud Tasks queue rates and retries: https://docs.cloud.google.com/tasks/docs/configuring-queues
- HTTP target task creation and authentication: https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks
- Task creation deduplication: https://docs.cloud.google.com/tasks/docs/create-tasks
- Python CSV: https://docs.python.org/3.12/library/csv.html
- Python XML processing: https://docs.python.org/3.12/library/xml.html

The examples distinguish local cache algorithms and a local durable job store from Redis and managed Cloud Tasks. Neither service has been exercised. Redis is not available on PATH; the Docker engine is unavailable in this session.

The local examples passed 58 checks. See verification-results.json for the executed boundaries and validation-summary.json for content/site checks. No managed service execution is claimed.
