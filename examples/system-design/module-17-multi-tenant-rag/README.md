# S12: Multi-tenant RAG knowledge-base platform

From repository root, run `python examples/system-design/module-17-multi-tenant-rag/verify.py` with Python 3.12 and the existing S11/shared helper folders intact. No dependency installation, external API, Docker or persistent server is needed. The owned ephemeral listener, connections and temporary database directory are closed/removed; port 3000 stays unused.

`rag.py` extends the unchanged `../module-16-multi-tenant-saas/saas.py` authority and reuses `../worked-systems-s4-s6/runtime.py`. It implements versioned plaintext/ingest publication, deterministic feature-hash vectors, authorized exact-scan retrieval, request evidence/citation checks, character-budget reservation and uncertainty, source deletion and local row/request cleanup.

`verify.py` records 125 checks, including six competing calls, selected judged retrieval cases, invalid citations/quotes/tool requests, permission changes during generation, retained unknown/review reservations, purge during prepared/running requests, rollback/reopen and actual HTTP. The model is extractive local code. No learned semantic model, real LLM/vector service, provider token/money meter, tool execution, streaming or external deletion is verified.

`lesson.md` is the authored prose. `../worked-system-s12/author.py` embeds exact runtime/local code and observed outputs into Part 19 and records the S11 dependency checksum. The companion batch README describes integration/build/smoke validation. The chapter contains 30 Q&As, ten tasks, twelve unchecked learning items and a 45-minute mock.
