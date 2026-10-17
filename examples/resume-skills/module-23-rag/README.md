# M23: RAG and Document Ingestion

Part 25 practice fixture, recorded 15 October 2026 on Windows/Python 3.12.10, SQLite 3.49.1 with FTS5, pypdf 6.20.1 and tiktoken 0.14.0. The handbook site's separate dependencies were not upgraded.

## Reproduce

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-23-rag/.venv
& examples/resume-skills/module-23-rag/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-23-rag/requirements-lock.txt
& examples/resume-skills/module-23-rag/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-23-rag/verify.py
```

Installation and the first cl100k_base vocabulary download need network access. Later tests use a cached vocabulary and owned local HTTP/database fixtures. requirements.txt pins direct dependencies; requirements-lock.txt records the resolved environment. dependency-check.txt reports pip check, not a vulnerability audit.

To verify handbook integration after installing study-guide dependencies:

```powershell
python -X utf8 examples/resume-skills/module-23-rag/validate_site.py
```

The site validator uses a cached Google Fonts response fixture when available; otherwise the handbook build needs font network access. Its temporary preview is closed. Port 3000 remains stopped; Docker and paid provider APIs are unused.

## Verified results

| Group | Checks |
| --- | --- |
| Actual text/PDF extraction and rejection/review paths | 14 |
| Page-aware word chunking/provenance/identity | 9 |
| SQLite publication/conflict/rollback/reopen | 12 |
| FTS5/BM25 query behavior | 7 |
| Trusted user/tenant/source scope | 4 |
| Scoped result-cache behavior | 5 |
| Current context/token budget/data boundary | 8 |
| Exact quote/citation/current-version checks | 4 |
| Actual local HTTP search/answer/source paths | 17 |
| Tombstones/delete/index consistency | 6 |
| RRF and heuristic reranking mechanics | 5 |
| Tiny document-level retrieval evaluation | 6 |
| Listener/database cleanup | 2 |
| **Total** | **99** |

The verifier generates tiny in-memory text PDF fixtures, parses real pages with pypdf, checks normalized page offsets and overlapping word windows, publishes into real SQLite FTS5/BM25, and exercises real transaction rollback and a scoped read-only HTTP API. No user resume/private PDF is opened.

The executed retriever is lexical. RRF lists are handwritten, the reranker is an explicit phrase/coverage heuristic, and the answer copies a source excerpt. No learned semantic embedding, LLM generation, OCR, hosted vector store or real model-quality test is hidden behind these examples. The tiny evaluation reports the lexical paraphrase miss, with recall/MRR 0.666667 over three labeled answerable queries and a separate unanswerable query. This is not a broad benchmark or a promise that another retriever would fix every miss.

## Data and lifecycle rules

- Fixed synthetic HTTP tokens map to trusted tenant/user Principal values; this is a routing/scope fixture, not real authentication.
- Search applies owner/tenant/current-version filtering before LIMIT. Direct source lookup, context packing and quote validation recheck current permitted sources.
- Same version/hash/configuration is duplicate publication; a conflicting same version is rejected and a lower revision is stale.
- Chunk/FTS/document/epoch changes publish in one SQLite transaction. A controlled mid-publication failure preserves the old generation.
- Replacement invalidates old chunk IDs and cache epochs. Delete tombstones the logical document and removes current chunk/FTS rows. Late jobs cannot resurrect it.
- Cache keys include user, tenant, epoch, query and limit. Cached results are copied and the local cache is bounded.
- The chunker counts whitespace words, not model tokens. The context gate tokenizes the local serialized evidence JSON with cl100k_base, which is not a complete provider request count.
- Quote membership/ID/current-source checks are a narrow extractive contract, not general semantic entailment or protection from misleading selective quotations.

## Files

- ingestion.py: UTF-8/PDF extraction, normalization, review/rejection paths and page-aware chunk identity.
- store.py: explicitly closed SQLite connections, publication/rollback/conflict, scoped FTS retrieval/source lookup and tombstones.
- ranking.py: RRF arithmetic and a clearly labeled lexical reranker.
- context.py: current-source reauthorization, serialized budget, extractive reply and quote/citation validation.
- service.py: bounded process-local scoped/epoch cache and excerpt-answer orchestration.
- evaluation.py: document-level recall/reciprocal-rank mechanics with duplicate handling.
- fixtures.py: tiny in-memory parser inputs; uses pypdf writer internals only to construct test content streams, not for the production parsing path.
- http_fixture.py: read-only local search/answer/source boundary with synthetic principals.
- verify.py: actual parser/index/transaction/HTTP/tokenizer and controlled policy/metric checks.
- requirements.txt / requirements-lock.txt / dependency-check.txt: dependency snapshot and consistency output.
- verification-results.json / verification-output.txt / cleanup-results.json: actual named checks, observations and closure.
- content-validation.json / site-validation.json / validation-summary.json: source/output fidelity, handbook build/routes/search and cleanup.
- validate_site.py / site-smoke.mjs: repeatable handbook integration checks.

The chapter embeds six core source files exactly, six recorded observation objects, 30 interview Q&As, ten exercises and twelve unchecked learning items. Temporary SQLite directories are removed; generated environments/vocabulary/bytecode are ignored.

## Limits

The file byte/page limits are not a parser sandbox or a bound on decompressed memory/CPU. The textless fixture is a blank page, not an OCR accuracy test. Global FTS statistics can influence ranking across the shared corpus even though returned rows are scoped. Local source rechecks do not establish every concurrent revocation or statistical/timing isolation guarantee.

Deletion tests establish current local searchability and source unavailability, not complete erasure across original objects, conversations, logs, backups or external services. SQL publication does not prove a distributed transaction with hosted storage/indexes. No durable queue, trained embeddings, LLM, OCR, real login, hosted retrieval, production deployment, comprehensive security audit or capacity benchmark was executed.
