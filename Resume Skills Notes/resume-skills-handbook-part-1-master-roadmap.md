# Resume Skills Placement Handbook — Part 1: Master Roadmap

**Your roadmap from resume keywords to interview explanations, working examples and architectural reasoning. Backend/SDE first; product and analytics later.**

---

## 0. How this handbook is built

The existing five handbooks establish DSA, OOP, OS, DBMS and CN. This companion explains the practical stack on top: languages, runtimes, frameworks, APIs, security, deployment and AI applications.

**The goal is to explain a skill, trace its mechanism, use it in a small working example and defend a choice from your resume.**

This is the roadmap, not the teaching chapter. It tells you what exists, what will be written, and how the pieces connect.

| Item | Status |
| --- | --- |
| Authored handbook | 31 files: roadmap, M0-M28, consolidation M29 |
| Available now | This roadmap, [M0: How a Backend Works](/docs/resume-skills/how-backend-works), [M1: JavaScript Fundamentals](/docs/resume-skills/javascript-fundamentals), [M2: Asynchronous JavaScript](/docs/resume-skills/asynchronous-javascript), [M3: TypeScript Fundamentals](/docs/resume-skills/typescript-fundamentals), [M4: Node.js](/docs/resume-skills/nodejs), [M5: Express.js](/docs/resume-skills/express-backend-structure), [M6: REST APIs and HTTP](/docs/resume-skills/rest-apis-http), [M7: Authentication](/docs/resume-skills/authentication-sessions-jwt-oauth), [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy), [M9: Webhooks and Payments](/docs/resume-skills/webhooks-payments-reliable-integrations), [M10: Python Fundamentals](/docs/resume-skills/python-fundamentals), [M11: Flask/FastAPI](/docs/resume-skills/flask-fastapi-python-request-handling), [M12: Django/DRF](/docs/resume-skills/django-django-rest-framework), [M13: PostgreSQL](/docs/resume-skills/postgresql-backend), [M14: MongoDB](/docs/resume-skills/mongodb-backend), [M15: Caching, Jobs and Ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion), [M16: Docker](/docs/resume-skills/docker-fundamentals), [M17: Linux Deployment](/docs/resume-skills/linux-deployment-nginx-pm2), [M18: AWS/GCP](/docs/resume-skills/aws-gcp-fundamentals), [M19: Git/CI/Observability](/docs/resume-skills/git-ci-cd-testing-observability-performance), [M20: React](/docs/resume-skills/react-fundamentals), [M21: Next.js/Tailwind](/docs/resume-skills/nextjs-api-routes-tailwind), [M22: LLM/AI APIs](/docs/resume-skills/llm-ai-api-fundamentals) [M23: RAG/Ingestion](/docs/resume-skills/rag-document-ingestion) [M24: Embeddings/Vector Stores](/docs/resume-skills/embeddings-pinecone-pgvector) [M25: AI Frameworks](/docs/resume-skills/langchain-langgraph-llamaindex) [M26: Neo4j](/docs/resume-skills/neo4j-graph-backed-applications) [M27: System-Design Bridge](/docs/resume-skills/system-design-load-balancer) [M28: Resume Deep-Dives](/docs/resume-skills/resume-project-experience-deep-dives) and [M29: Consolidation](/docs/resume-skills/consolidation-interview-drills) |
| Executable examples | examples/resume-skills/module-0-backend/ through module-29-consolidation/ |
| Main sequence | M0-M29 authored; learning mastery is assessed separately |
| Architecture companion | [Master roadmap](/docs/system-design), [A0](/docs/system-design/design-method-estimation), [A1](/docs/system-design/application-architecture-service-boundaries), [A2](/docs/system-design/data-caching-scaling), [A3](/docs/system-design/reliable-workflows-concurrency), [A4](/docs/system-design/secure-observable-operations), [S0](/docs/system-design/url-shortener), [S1](/docs/system-design/rate-limiter), [S2](/docs/system-design/notifications-webhooks), [S3](/docs/system-design/file-upload-processing), [S4](/docs/system-design/booking-reservations), [S5](/docs/system-design/chat-messaging), [S6](/docs/system-design/social-feed-photo-sharing), [S7](/docs/system-design/job-scheduler-workers), [S8](/docs/system-design/checkout-payments-credit-ledger), [S9](/docs/system-design/search-autocomplete), [S10](/docs/system-design/load-balancer-distributed-cache), [S11](/docs/system-design/multi-tenant-saas), [S12](/docs/system-design/multi-tenant-rag), [S13](/docs/system-design/analytics-event-pipeline) and [architecture consolidation](/docs/system-design/consolidation) available; all 21 architecture files authored |
| Architecture question bank | Sixty compiled prompts/checkpoints at the repository root |
| Product/analytics | Separate later track |

An available chapter is not a claim that you have mastered it. Learning checklists remain unchecked until you can demonstrate the skill.

### Three questions every chapter prepares you for

1. **Explain:** what is it, and why does it exist?
2. **Trace:** what happens when the application uses it?
3. **Defend/debug:** why choose it, what can fail, and what would you change?

A good answer identifies a mechanism and an example. “It is scalable” without saying how or under which conditions is incomplete.

---

## 1. Master syllabus

Hours are first-pass estimates including a small exercise. Architecture case studies, revision and full mock interviews are additional.

| Module | Section | Hours | Tier | Status |
| --- | --- | --- | --- | --- |
| M0 | **How a backend works** | 2 | 1 | Available |
| M1 | **JavaScript fundamentals for interviews** | 4 | 1 | Available |
| M2 | **Asynchronous JavaScript** | 3 | 1 | Available |
| M3 | **TypeScript fundamentals** | 3 | 1 | Available |
| M4 | **Node.js: what it is and how it works** | 4 | 1 | Available |
| M5 | **Express.js and backend application structure** | 3 | 1 | Available |
| M6 | **REST APIs and HTTP in application design** | 3 | 1 | Available |
| M7 | **Authentication, sessions, JWT and OAuth** | 4 | 1 | Available |
| M8 | **API security, authorization and multi-tenancy** | 4 | 1 | Available |
| M9 | **Webhooks, payments and reliable integrations** | 3 | 1 | Available |
| M10 | **Python fundamentals for backend interviews** | 4 | 1 for Python roles | Available |
| M11 | **Flask, FastAPI and Python request handling** | 4 | 2 | Available |
| M12 | **Django and Django REST Framework** | 4 | 2 | Available |
| M13 | **PostgreSQL in a backend** | 5–6 | 1 | Available |
| M14 | **MongoDB in a backend** | 5–6 | 1 | Available |
| M15 | **Caching, background jobs and data ingestion** | 5–6 | 1 concepts | Available |
| M16 | **Docker fundamentals** | 4–5 | 2 | Available |
| M17 | **Linux deployment, Nginx and PM2** | 4–5 | 2 | Available |
| M18 | **AWS and GCP fundamentals for this resume** | 4–5 | 2 | Available |
| M19 | **Git, CI/CD, testing, observability and performance** | 5–6 | 1 concepts | Available |
| M20 | **React fundamentals** | 5–6 | 2 | Available |
| M21 | **Next.js, API routes and Tailwind** | 5–6 | 2 | Available |
| M22 | **LLM and AI API fundamentals** | 5–6 | 2, high relevance here | Available |
| M23 | **RAG and document ingestion** | 5–6 | 2, high relevance here | Available |
| M24 | **Embeddings, Pinecone and pgvector** | 4–5 | 2 | Available |
| M25 | **LangChain, LangGraph and LlamaIndex** | 5–6 | 2 | Available |
| M26 | **Neo4j and graph-backed applications** | 4–5 | 2 | Available |
| M27 | **System-design bridge** | 5–6 | 2 | Available |
| M28 | **Resume project and experience deep-dives** | 5–6 | 1 | Available |
| M29 | **Consolidation and interview drills** | 2 per pass | Revision | Available |

**Estimated first pass: 103–105 hours**, including the planned consolidation pass. Existing familiarity changes the time; these estimates are not a promise of mastery.

### Priority tiers

- **Tier 1:** explain and apply confidently for the chosen backend track.
- **Tier 2:** resume-linked depth and secondary-stack knowledge.
- **Tier 3 inside chapters:** compressed optional follow-ups.

Tier 2 is not permission to ignore a prominent resume claim. A project's technology choice can become the main topic of that interview.

Priorities reflect this resume and transferable mechanisms. They are not measured company-question frequencies.

---

## 2. Dependency map

```text
M0 Backend picture
 |
 +-- M1 JavaScript -- M2 Async -- M4 Node -- M5 Express -- M6 APIs
 |        |                                                |
 |        +-- M3 TypeScript                                 +-- M7 Auth -- M8 Security
 |                                                         |                   |
 +-- M10 Python -- M11 Flask/FastAPI; M12 Django/DRF ---------+--------- M9 Integrations
 |
 +-- existing DBMS -- M13 PostgreSQL / M14 MongoDB -- M15 Cache/jobs/ingestion

M16 Docker -- M17 Deployment -- M18 Cloud -- M19 CI/CD/observability

M1/M3 -- M20 React -- M21 Next.js/Tailwind

M6/M10 -- M22 AI APIs -- M23 RAG -- M24 Vector stores -- M25 Frameworks
                              |
                              +-- M26 Neo4j (also uses DBMS/DSA graphs)

M27 Design bridge -- M28 Resume deep-dives -- M29 Consolidation
```

This is a conceptual map, not a requirement to finish every branch before practising a project answer.

| To understand | First establish | Why |
| --- | --- | --- |
| Node concurrency | JavaScript execution and async | Single-threaded is not one request at a time |
| Middleware | Node request/response and control flow | Ordering/error propagation is execution behavior |
| TypeScript boundaries | JavaScript values/runtime behavior | A type is not JSON validation |
| Authentication | HTTP/cookies and trust boundaries | A token needs a transport/verification path |
| Tenant security | Auth plus data access | Filtering one route is not whole-system isolation |
| Webhook effects | Transactions and idempotency | Retries can duplicate side effects |
| Python async frameworks | Coroutines and request execution | async syntax alone does not remove blocking |
| Practical indexes | DBMS SQL/indexing | Query shape and actual plans matter |
| Durable jobs | Data model and failure states | Enqueue, execute and acknowledge can fail independently |
| RAG | API calls, ingestion and authorization | Retrieval is a pipeline with state and permissions |
| Agent frameworks | Plain model/retrieval/tool flow | Understand the mechanism before its abstraction |

---

## 3. Architecture is part of the learning path

The separate architecture companion teaches how to assemble the stack.

| Label | Foundation |
| --- | --- |
| A0 | Requirements, invariants, estimates and design method |
| A1 | Responsibilities, module boundaries and architecture styles |
| A2 | Data access, caching, consistency and scale |
| A3 | Queues, retries, idempotency, concurrency and recovery |
| A4 | Secure operation, observability and failure verification |

| Stage | Worked designs |
| --- | --- |
| First | URL shortener; rate limiter; notifications/webhooks; file processing; booking |
| Next | Chat; feed/photo sharing; job scheduling |
| Resume depth | Payments/credits; search; load balancing/cache; multi-tenant SaaS; RAG; analytics |

The companion plan and question bank are Architecture-System-Design-Notes-Plan.md and Architecture-System-Design-Question-Bank.md at the repository root. Worked chapters remain planned.

### Interleave as prerequisites become available

- After API/data basics: A0/A1 and URL shortening.
- After auth/integrations: rate limiting, SaaS permissions and notifications.
- After transactions/jobs: reservation, payment and worker failures.
- After deployment: operational/performance discussions.
- After AI/RAG: the multi-tenant knowledge-base design.

**Every design starts with a correct small system**, then changes in response to a requirement or bottleneck.

Existing OOP LLD establishes object responsibilities. The system-design track adds communicating processes, durable state, failure boundaries and scale.

---

## 4. Interview question map

These are learning targets, not predictions of exact company questions.

| Question | Module |
| --- | --- |
| What happens after a user clicks a button? | M0 |
| JavaScript vs Node.js vs Express? | M0/M4/M5 |
| What does this closure capture? | M1 |
| What does async/await change? | M2/M4 |
| Why does a TypeScript type not validate JSON? | M3 |
| Why does middleware order matter? | M5 |
| How would you design a paginated API? | M6 |
| Sessions vs JWT, and how does logout work? | M7 |
| How do you prevent cross-tenant access? | M8; S11 |
| What if a webhook or job happens twice? | M9/M15; A3 |
| Threads vs processes vs async in Python? | M10/M11 |
| Why can ORM code still produce slow queries? | M12 |
| When would an index not help? | M13; DBMS |
| Embed or reference in MongoDB? | M14 |
| Cache or queue: which problem is being solved? | M15; A2/A3 |
| Image vs container vs VM? | M16 |
| What does the reverse proxy do? | M17 |
| What happens when a target becomes unhealthy? | M18/M27 |
| How was the claimed throughput measured? | M19/M28 |
| Why did a React effect run again? | M20 |
| Server vs Client Component, and where is the secret? | M21 |
| Tool calling vs generated JSON? | M22 |
| Why did RAG retrieve irrelevant text? | M23/M24 |
| Pinecone vs pgvector: what decides the choice? | M24 |
| When is an agent framework useful? | M25 |
| Why use a graph DB? | M26 |
| What happens to the hash ring when nodes change? | M27; S10 |
| What did you personally build, and how do you know it worked? | M28 |
| Can you handle a changed requirement without memorized diagrams? | M29; mocks |

---

## 5. Links to existing handbooks

| Existing subject | Contribution |
| --- | --- |
| DSA | Maps, queues, trees, search, graphs and complexity |
| OOP | Responsibilities, interfaces, invariants, patterns and LLD |
| OS | Processes, threads, memory, I/O and synchronization |
| DBMS | Schemas, constraints, SQL, indexes, transactions and recovery |
| CN | Addresses/ports, TCP, DNS, HTTP, TLS and request paths |

C/C++ remain primarily in DSA/OOP. Python/JavaScript get their own execution models because they are part of the applied stack.

Cross-references supplement short refreshers; they do not assume that an unexplained term is already understood.

---

## 6. How each module is framed

1. Header: module, hours, tier and prerequisites.
2. Why it matters and one organizing principle.
3. Plain definition and the problem it solves.
4. Diagram locating it in an application.
5. Step-by-step mechanism and worked trace.
6. Executable example where useful.
7. Trade-offs and comparison tables.
8. Resume connection and likely follow-ups.
9. Must remember: non-obvious facts.
10. Common wrong answers and corrections.
11. Short interview Q&A and follow-ups.
12. Distinct practice tasks and answer checkpoints.
13. Exit checklist and Next.

Small familiar topics get compressed treatment. Length follows teaching need.

### How to read a module

First follow the example. Then recreate the diagram/trace with the page closed. Change an input or requirement and predict the effect. Answer questions aloud. Tick an exit item only when you can demonstrate it.

Definitions alone are not the exit condition.

---

## 7. Verification rules

**Do not turn expected behavior into a claimed observation.**

- Record runtime/package versions and actual outputs.
- Preserve source, verification scripts and fixtures under examples/.
- Distinguish live runs, simulations, mocked providers and documented behavior.
- Use the actual engine for database-specific guarantees.
- Verify rejected inputs/permissions as well as success.
- Show concurrency/crash timing when correctness depends on it.
- State workload, errors, runtime and hardware for benchmarks.
- Explain what checks establish and what they do not.
- Keep secrets and privileged credentials out of examples.
- Recheck official docs for version-sensitive chapters.

Next.js 14 on the resume and the study website's installed version are separate contexts.

A passing local example does not establish production readiness.

---

## 8. Study routes and revision

| Route | Order |
| --- | --- |
| Backend foundation | M0 -> M1 -> M2 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9 |
| TypeScript addition | M3 before TypeScript-heavy implementation |
| Python backend | M0/M6 -> M10 -> M11/M12 -> M13/M14 -> M15, with M7/M8 |
| AI backend | API/auth/data -> M22 -> M23 -> M24 -> M25, plus M26 |
| Production/architecture | M16-M19, A0-A4 and selected worked cases |
| Project defence | M27/M28 and the relevant design/failure prompts |

### Revision passes

| Pass | Activity |
| --- | --- |
| 1 | Understand the mechanism and run the example |
| 2 | Recreate the trace/core code without notes |
| 3 | Change a requirement and explain the consequence |
| 4 | Mixed Q&A, debugging and a timed design |
| 5 | Mistake log, comparison tables and resume explanations |

Leave time for your existing CS and DSA preparation. Choose the relevant branch for a particular role; a long tool list is not a reason to skim the core mechanisms.

### Product and analytics later

P0 requirements/flows/Figma/Notion; P1 pricing/unit economics; P2 events/funnels/retention/PostHog/GA4/Clarity; P3 NumPy/pandas/Excel; P4 ads measurement/D3; P5 resume drills and revision.

These remain a separate later track as agreed.

---

## 9. Progress checklist

### Material available

- [x] Master roadmap authored.
- [x] M0 teaching chapter authored.
- [x] M0 executable example and verifier preserved.
- [x] M1 teaching chapter and 30 executable snippets authored.
- [x] M2 teaching chapter and 28 executable examples authored.
- [x] M3 teaching chapter and 26 compiler/runtime examples authored.
- [x] M4 teaching chapter, 20 runtime cases and 16 HTTP checks authored.
- [x] M5 teaching chapter, 16 runtime examples, 39 API checks and five typed boundary checks authored.
- [x] M6 teaching chapter and 68 real HTTP checks authored, including retry, pagination and concurrent-edit cases.
- [x] M7 teaching chapter, 38 credential/session/token/crypto checks, 32 HTTP checks and 16 OAuth-model checks authored.
- [x] M8 teaching chapter, 22 policy/input checks, 46 HTTP checks and six SQLite checks authored.
- [x] M9 teaching chapter and 57 integration checks authored, including 26 HTTP and four file/process-recovery cases.
- [x] M10 teaching chapter, 24 language examples, six concurrency examples and 14 application-boundary checks authored.
- [x] M11 teaching chapter and 80 framework checks authored, including 52 real HTTP and 16 runtime checks.
- [x] M12 teaching chapter and 76 checks authored: 15 ORM, 14 transaction, nine framework and 38 real HTTP; three additional management checks passed.
- [x] M13 teaching chapter and 60 real PostgreSQL checks authored: 19 core, 14 concurrency, eight pool, seven query-plan and 12 reservation-service checks.
- [x] M14 teaching chapter and 65 real MongoDB checks authored: 17 core, 12 query/aggregation, ten index, six atomic-update, 15 transaction/service and five pool/cursor checks.
- [x] M15 teaching chapter and 58 checks authored: ten local cache, 13 SQLite job, 23 real format/parser and 12 restartable ingestion checks. Redis and Cloud Tasks are documented bridges, not executed services.
- [x] M16 teaching chapter and 40 real Docker checks authored: five build, six HTTP, five lifecycle, five network, three readiness, ten runtime and six storage. Owned fixture resources removed; Docker restored to stopped.
- [x] M17 teaching chapter and 40 real Linux deployment checks authored: six Linux, 14 Nginx, four TLS, eight PM2, five lifecycle and three host-publication checks. Owned resources removed; Docker restored to stopped.
- [x] M18 teaching chapter and 53 local checks authored: nine SDK, 14 token/authentication, 16 HTTP/SQLite worker and 14 HTTP-cache checks. Cloud service behavior researched; no account/API/resources used. Listeners and scratch database removed.
- [x] M19 teaching chapter and 62 local checks authored: 15 Git, three contracts, four HTTP, seven tracing, two logs, four metrics, eight statistics, five load mechanics, nine release gates and five workflow-static checks. Fixture histories/ports/releases cleaned; main repository HEAD unchanged.
- [x] M20 teaching chapter and 50 actual browser checks authored: eight state, six identity, six effects, three Strict Mode, six forms, four sharing, 11 HTTP/API, five selected accessibility/layout and one uncaught-exception check. Desktop/mobile layouts inspected; browser/server closed.
- [x] M21 teaching chapter and 54 actual production-framework/HTTP/browser checks authored; Next.js 14/Tailwind 3 context separated from newer versions. Thirty Q&As, ten exercises; dependency audit and scope limits recorded. Screenshots inspected; browser/listeners closed.
- [x] M22 teaching chapter and 79 local checks authored: actual SDK/HTTP/SSE/errors and tokenizer, tool/authorization, bounded retries, Decimal cost/admission/concurrency and deterministic grader mechanics. Thirty Q&As and ten exercises. Handwritten peer only; no model inference/provider calls/keys/charges. SDK/listener closed.
- [x] M23 teaching chapter and 99 local checks authored: real PDF extraction, page/word chunk provenance, SQLite FTS5/BM25/publication rollback, scoped HTTP/source/context, citations, stale revisions/tombstones/cache and tiny lexical evaluation. Thirty Q&As and ten exercises. RRF lists handcrafted, reranker heuristic, answer extractive; no embeddings/LLM/OCR/hosted calls. Temporary databases/listener removed.
- [x] M24 teaching chapter and 92 local checks authored: real PostgreSQL 16.15/pgvector 0.8.6 operators, exact scoped retrieval/RLS, atomic publication rollback, revision/tombstone guards, HNSW/IVFFlat plans and sampled recall. Thirty Q&As and ten exercises. Authored vectors; Pinecone JSON body contracts only, no learned model/hosted calls. Portable runtime hash-verified; owned database cluster removed.
- [x] M25 teaching chapter and 89 actual framework checks authored: LangChain composition/parsing/async/stream and scripted agent tools, LangGraph reducers and file-checkpoint resume across fresh processes, strict owned review/freshness and local idempotent replay recovery, LlamaIndex ingestion/metadata-filtered retrieval/synthesis/persist/reload/delete. Thirty Q&As and ten exercises. Fake/scripted models, extractive graph draft and handwritten feature encoder; no learned inference/provider/hosted tracing. All 21 workers exited and temporary data removed.
- [x] M26 teaching chapter and 76 real-engine checks authored: Neo4j Community 2026.09.0 over loopback Bolt, Cypher 5 patterns/nulls/constraints/MERGE, bounded tenant-scoped paths, rollback/concurrent correctness, actual index plans/deletion and source-revision/tombstone acceptance. Thirty Q&As and ten exercises. Hand-authored graph; application authorization only, no Enterprise RBAC/APOC/GDS/model/Aura/performance claim. Portable vendor archives hash-verified; owned Java process, listener and temporary data cleaned.
- [x] M27 teaching chapter and 95 local checks authored: 21 deterministic ring, 17 pool-policy, eight capacity-arithmetic, 11 in-process cache-model and 38 real HTTP checks. Thirty Q&As and ten exercises. Actual forwarding/readiness/failure/drain/admission/cancellation/deadline over owned loopback sockets; no original-project throughput/latency reproduction, distributed cache or production authentication claim. All fixture listeners/agents/timers cleaned.
- [x] M28 teaching chapter authored for all seven resume experiences/projects: seven short pitches, seven two-minute outlines, seven five-minute walkthroughs, 30 Q&As and ten exercises. Eighty-one checks passed: 68 teaching-model/arithmetic and 13 PDF-provenance checks. Actual SQLite audit rollback, reopen alert dedupe and batch rollback; original project code/metrics/revenue/compliance remain explicitly unverified. Temporary databases removed; no persistent model listener.
- [x] M29 consolidation authored: 29-module map, 36 confusable pairs, 14 executed output drills, 16 debug cards, 60 rapid-fire Q&As, two 45-minute mocks, revision schedules and 24-question self-test. Forty-three checks passed: 14 isolated Node/Python/SQLite outputs and 29 canonical chapter-reference audits. All 14 workers exited; SQLite in-memory connections closed. Editorial drills are not production/user-assessment evidence; architecture/product extensions remain planned.
- [ ] Architecture worked chapters authored.
- [ ] Product/analytics track authored.

### Your learning progress

- [ ] M0: How a backend works
- [ ] M1: JavaScript fundamentals for interviews
- [ ] M2: Asynchronous JavaScript
- [ ] M3: TypeScript fundamentals
- [ ] M4: Node.js: what it is and how it works
- [ ] M5: Express.js and backend application structure
- [ ] M6: REST APIs and HTTP in application design
- [ ] M7: Authentication, sessions, JWT and OAuth
- [ ] M8: API security, authorization and multi-tenancy
- [ ] M9: Webhooks, payments and reliable integrations
- [ ] M10: Python fundamentals for backend interviews
- [ ] M11: Flask, FastAPI and Python request handling
- [ ] M12: Django and Django REST Framework
- [ ] M13: PostgreSQL in a backend
- [ ] M14: MongoDB in a backend
- [ ] M15: Caching, background jobs and data ingestion
- [ ] M16: Docker fundamentals
- [ ] M17: Linux deployment, Nginx and PM2
- [ ] M18: AWS and GCP fundamentals for this resume
- [ ] M19: Git, CI/CD, testing, observability and performance
- [ ] M20: React fundamentals
- [ ] M21: Next.js, API routes and Tailwind
- [ ] M22: LLM and AI API fundamentals
- [ ] M23: RAG and document ingestion
- [ ] M24: Embeddings, Pinecone and pgvector
- [ ] M25: LangChain, LangGraph and LlamaIndex
- [ ] M26: Neo4j and graph-backed applications
- [ ] M27: System-design fundamentals through your load balancer
- [ ] M28: Resume project and experience deep-dives
- [ ] M29: Consolidation and interview drills

### Cross-cutting exit checks

- [ ] I can distinguish language, runtime, framework, application and database.
- [ ] I can draw a request/data flow for every major project.
- [ ] I can name the authority and invariant for each state change.
- [ ] I can justify a choice and name a viable alternative.
- [ ] I can explain a real failure without inventing implementation details.
- [ ] I can defend a resume metric using its measurement method.
- [ ] I can reason about duplicate work, concurrency and uncertain outcomes.
- [ ] I distinguish observed evidence from a hypothesis.

---

## Next

Start with [M0: How a Backend Works](/docs/resume-skills/how-backend-works), then [M1: JavaScript Fundamentals](/docs/resume-skills/javascript-fundamentals). Continue with [M2: Asynchronous JavaScript](/docs/resume-skills/asynchronous-javascript). Continue with [M3: TypeScript Fundamentals](/docs/resume-skills/typescript-fundamentals). Continue with [M4: Node.js](/docs/resume-skills/nodejs). Continue with [M5: Express.js](/docs/resume-skills/express-backend-structure). Continue with [M6: REST APIs and HTTP](/docs/resume-skills/rest-apis-http). Continue with [M7: Authentication](/docs/resume-skills/authentication-sessions-jwt-oauth). Continue with [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy). Continue with [M9: Webhooks and Payments](/docs/resume-skills/webhooks-payments-reliable-integrations). Continue with [M10: Python Fundamentals](/docs/resume-skills/python-fundamentals). Continue with [M11: Flask/FastAPI](/docs/resume-skills/flask-fastapi-python-request-handling). Continue with [M12: Django/DRF](/docs/resume-skills/django-django-rest-framework). Continue with [M13: PostgreSQL in a Backend](/docs/resume-skills/postgresql-backend). Continue with [M14: MongoDB in a Backend](/docs/resume-skills/mongodb-backend). Continue with [M15: Caching, Background Jobs and Data Ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion). Continue with [M16: Docker Fundamentals](/docs/resume-skills/docker-fundamentals). Continue with [M17: Linux Deployment, Nginx and PM2](/docs/resume-skills/linux-deployment-nginx-pm2). Continue with [M18: AWS and GCP Fundamentals](/docs/resume-skills/aws-gcp-fundamentals). Continue with [M19: Git, CI/CD, Testing, Observability and Performance](/docs/resume-skills/git-ci-cd-testing-observability-performance). Continue with [M20: React Fundamentals](/docs/resume-skills/react-fundamentals). Continue with [M21: Next.js, API Routes and Tailwind](/docs/resume-skills/nextjs-api-routes-tailwind). Continue with [M22: LLM and AI API Fundamentals](/docs/resume-skills/llm-ai-api-fundamentals). Continue with [M23: RAG and Document Ingestion](/docs/resume-skills/rag-document-ingestion). Continue with [M24: Embeddings, Pinecone and pgvector](/docs/resume-skills/embeddings-pinecone-pgvector). Continue with [M25: LangChain, LangGraph and LlamaIndex](/docs/resume-skills/langchain-langgraph-llamaindex). Continue with [M26: Neo4j and graph-backed applications](/docs/resume-skills/neo4j-graph-backed-applications). Continue with [M27: System-design bridge through your load balancer](/docs/resume-skills/system-design-load-balancer). Continue with [M28: Resume project and experience deep-dives](/docs/resume-skills/resume-project-experience-deep-dives). Finish with [M29: Consolidation and interview drills](/docs/resume-skills/consolidation-interview-drills). The main sequence is authored. The architecture roadmap, all foundations A0-A4, all worked systems S0-S13 and consolidation are available: **21 authored architecture files**; product/analytics remains a separate later track.

Teaching proceeds one section at a time; the sidebar grows only when source chapters exist. The detailed authoring scope/source maps remain in Resume-Skills-Notes-Plan.md and Architecture-System-Design-Notes-Plan.md at the repository root.
