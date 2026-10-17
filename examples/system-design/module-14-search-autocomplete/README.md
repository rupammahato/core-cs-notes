# S9: Search and autocomplete

Run `python examples/system-design/module-14-search-autocomplete/verify.py` from the repository root with Python/SQLite supporting FTS5. Owned temporary SQLite files and an ephemeral HTTP listener are closed/removed; port 3000 stays unused.

`search.py` implements actual FTS5 full-text/title-token-prefix retrieval, source/outbox transactions, version/tombstone projection fences and current tenant/ACL/version checks before top-k. `verify.py` records 77 checks including two competing projectors, selected relevance judgments, rollback, local rebuild and HTTP. No external cluster, semantic model, online reindex or benchmark is executed.

`lesson.md` is the teaching source. The batch `../worked-systems-s7-s9/author.py` embeds exact source and observed output into Part 16. See the batch README for integration and site validation.
