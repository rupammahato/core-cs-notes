# Plan: Resume Skills Placement Handbook

**Backend/SDE first; product and analytics later. Research and section plan prepared on 13 October 2026.**

---

## 0. Purpose and agreed direction

Extend the existing DSA, OOP, OS, DBMS and CN handbooks with the practical technologies listed on the resumes.

The user asked for fundamentals that can be discussed in interviews: what a tool is, how it works, why it is used, what happens inside it, and how it is used in a backend. Node.js is the reference example for this depth.

**Confirmed preference:** prioritize backend/SDE preparation; cover product and analytics afterwards.

This document is the section list and authoring plan. Teaching chapters will be written one at a time after this list, in dependency order unless the user requests a particular section.

### What the notes should make possible

For every listed skill, the reader should be able to:

1. Explain it in 30 seconds without relying on a brand-name definition.
2. Draw where it sits in a working application.
3. Trace a small request or operation through it.
4. Explain why it was chosen and name a reasonable alternative.
5. Answer the first two or three follow-ups.
6. Spot a common correctness, performance or security mistake.
7. Connect the concept to a resume example without inventing project details.

**Organizing principle:** a skill on a resume is a promise that you can explain the mechanism, justify the choice, and reason about failure.

---

## 1. Research method and scope

The section choices combine the exact resume skills, the claims made in the experience/project bullets, and primary documentation about how the technologies work.

The priority assignments below are editorial judgments for this resume and the chosen backend/SDE track. They are **not measured interview-frequency rankings** or predictions of particular companies' questions.

Official documentation is the technical baseline. Individual chapters will refresh version-sensitive details before authoring; this plan is not a permanent guarantee of API behavior.

### Priority tiers

| Tier | Meaning here |
| --- | --- |
| 1 | Explain and apply confidently: backend foundations, main language/runtime, API design, authentication, correctness, data access |
| 2 | Resume-linked depth: secondary frameworks, deployment, AI systems, project architecture |
| 3 | Compressed awareness or an optional deep follow-up; teach only enough to support the main concept |

Tier 2 does not mean unimportant. A tool used prominently in a project can become the centre of that interview.

### Three interview question shapes

| Shape | Example |
| --- | --- |
| Explain | What is Node.js? How is it different from JavaScript or Express? |
| Trace | What happens from an HTTP request arriving until the response leaves? |
| Diagnose / defend | Why did every request slow down? Why use a queue here? What if the webhook arrives twice? |

### Scope boundaries

- Build on existing CS material with precise cross-references; add a short refresher when needed.
- Teach practical fundamentals and the first useful layer of internals.
- Use JavaScript/TypeScript for the Node/Express examples and Python for Python/AI examples. C++ remains in the existing handbooks.
- Small tools get focused subsections rather than a full course.
- Supporting topics such as Redis, IAM, object storage and OpenID Connect will be labelled as bridges where they are not explicitly listed skills.
- No Kubernetes course, advanced compiler theory, model-training course or cloud certification syllabus.
- No invented account-specific cloud observations, paid API runs, deployment metrics or resume anecdotes.

---

## 2. Main section list and writing order

**Proposed folder:** Resume Skills Notes/

**Structure:** one master roadmap, 29 teaching sections (M0-M28), and a consolidation section (M29): 31 files in total. Each row below is one planned section/file. Smaller tools are subsections within these files.

### A. Backend foundations and the JavaScript stack

| ID | Section | What it will cover | Tier / requires |
| --- | --- | --- | --- |
| M0 | **How a backend works** | Frontend vs backend; client, server, process, port and API; request/response lifecycle; web server vs application server; runtime vs framework vs library; routes, business logic, storage and external services; one complete request diagram | 1 / none |
| M1 | **JavaScript fundamentals for interviews** | Types, coercion and equality; scope, hoisting and temporal dead zone; closures; this and arrow functions; objects/prototypes; references, mutation and shallow copies; destructuring; short output-prediction drills | 1 / M0 |
| M2 | **Asynchronous JavaScript** | Call stack and host runtime; callbacks, promises, async/await; microtasks vs tasks; errors; sequential vs concurrent requests; Promise combinators; cancellation, timeouts and bounded concurrency; browser vs Node scheduling distinctions | 1 / M1 |
| M3 | **TypeScript fundamentals** | What TypeScript checks and what remains at runtime; types vs interfaces; unions, narrowing, generics, utility types, unknown vs any; structural typing; nullability; runtime validation at API boundaries | 1 / M1 |
| M4 | **Node.js: what it is and how it works** | Runtime, V8, native bindings, libuv, OS I/O and worker pool; request handling; event-loop blocking; modules and npm; buffers, streams and backpressure; process vs worker thread; strengths, limits and use cases | 1 / M0, M1, M2 |
| M5 | **Express.js and backend application structure** | Why Express exists on top of Node; routing; request/response objects; middleware and order; body parsing and validation; routers, controllers, services and data access; error middleware; Express 4/5 differences where relevant | 1 / M4 |
| M6 | **REST APIs and HTTP in application design** | Resources and endpoint design; HTTP method semantics; status codes; headers and JSON; validation and error contracts; pagination, filtering and sorting; API versioning; retries, idempotency and rate limiting; API tests | 1 / M0, M5; CN HTTP refresher |
| M7 | **Authentication, sessions, JWT and OAuth** | Authentication vs authorization; password verification; cookies and sessions; JWT structure and verification; access/refresh tokens and rotation; expiry and revocation; OAuth 2.0 roles and authorization-code flow with PKCE; OAuth vs OIDC; JWT vs JWE; BFF pattern | 1 / M6 |
| M8 | **API security, authorization and multi-tenancy** | Server-side ownership checks; RBAC and scoped permissions; tenant filtering on every data path; object-level authorization; injection, XSS, CSRF and CORS; safe file ingestion; secrets; layered rate limits; negative authorization tests | 1 / M6, M7 |
| M9 | **Webhooks, payments and reliable integrations** | Webhook vs polling; sender/receiver trace; raw-body signature verification; replay and duplicate events; event IDs and idempotency; out-of-order events; payment/order states; atomic credits; timeout ambiguity; reconciliation and testing using local fixtures | 1 / M6-M8; DBMS transactions |

### B. Python frameworks and practical databases

| ID | Section | What it will cover | Tier / requires |
| --- | --- | --- | --- |
| M10 | **Python fundamentals for backend interviews** | Mutable/immutable values; references and copying; collections; iterables/generators; decorators; context managers; exceptions; modules and environments; typing; asyncio; threads vs processes; GIL with implementation/version caveats | 1 for Python roles / M0 |
| M11 | **Flask, FastAPI and Python request handling** | Framework vs WSGI/ASGI server; Flask routing, request context and blueprints; FastAPI routing, Pydantic validation, dependency injection and OpenAPI; def vs async def; background tasks vs durable jobs; framework choice | 2 / M6, M10 |
| M12 | **Django and Django REST Framework** | Project/app and MVT structure; URL-to-view lifecycle; middleware; models, migrations and ORM; lazy QuerySets and N+1; serializers, views/viewsets and routers; permissions, pagination and tests; transactions | 2 / M6-M8, M10; DBMS |
| M13 | **PostgreSQL in a backend** | Connecting safely; schema/migrations; transactions, isolation and row locking in an application; connection pools; parameterized queries; EXPLAIN and EXPLAIN ANALYZE; indexes and query shape; upserts and constraints; PostgreSQL vs generic SQL | 1 / M6; DBMS keys, SQL, indexing, transactions |
| M14 | **MongoDB in a backend** | Documents, collections, BSON and ObjectId; flexible schema vs validation; embedding vs references; CRUD, updates and atomicity boundaries; indexes; aggregation pipeline; pagination; transactions when needed; SQL vs document-model trade-offs | 1 / M6; DBMS |
| M15 | **Caching, background jobs and data ingestion** | Cache-aside, TTL and invalidation; a short Redis bridge; queue vs cron vs in-process task; GCP Cloud Tasks as the resume example; retries, backoff and duplicate execution; idempotent workers; failed-job handling; CSV/Excel/XML/PDF validation, batching, timestamps and upserts | 1 concepts / M9-M14 |

### C. Shipping and operating the application

| ID | Section | What it will cover | Tier / requires |
| --- | --- | --- | --- |
| M16 | **Docker fundamentals** | Image vs container vs VM; layers and Dockerfile; build context/cache; ports and networks; bind mounts vs volumes; environment/secrets; Compose; multi-stage builds; non-root execution; why a container exits; local API-plus-database example | 2 / M0, one framework |
| M17 | **Linux deployment, Nginx and PM2** | Processes, permissions, environment and logs; reverse proxy vs app server; Nginx routing, TLS termination, headers and timeouts; PM2 process management and clustering; graceful shutdown; connection draining; deployment failure walkthrough | 2 / M4, M6, M16; OS/CN |
| M18 | **AWS and GCP fundamentals for this resume** | Cloud vs local hosting; regions/AZs; EC2, network reachability and security groups; IAM bridge; ELB/ALB, target groups and health checks; CDN cache/origin path; scaling and availability; GCP Cloud Tasks auth/retries; end-to-end deployment diagram | 2 / M15-M17 |
| M19 | **Git, CI/CD, testing, observability and performance** | Git commit/branch/merge/rebase basics; GitHub Actions events/jobs/steps/runners; CI vs delivery vs deployment; lint/test/build/release/rollback; unit vs integration vs contract tests; logs/metrics/traces; latency percentiles vs throughput; reproducible load tests | 1 concepts / M6, M16-M18 |

### D. Frontend knowledge needed to explain the full stack

| ID | Section | What it will cover | Tier / requires |
| --- | --- | --- | --- |
| M20 | **React fundamentals** | Components, props and state; render/commit; state snapshots; hooks and effect cleanup; dependency arrays; keys and reconciliation; controlled forms; API state/loading/errors; context and memoization basics; HTML/CSS and accessibility refresher | 2 / M1-M3 |
| M21 | **Next.js, API routes and Tailwind** | Why Next.js wraps React; routing/layouts; CSR/SSR/SSG/ISR; Server vs Client Components and hydration; Route Handlers vs Pages API routes; BFF/proxy use; data fetching/caching; Node vs Edge runtimes; Tailwind utility/responsive basics | 2 / M6, M7, M20 |

### E. AI systems and specialized data stores

| ID | Section | What it will cover | Tier / requires |
| --- | --- | --- | --- |
| M22 | **LLM and AI API fundamentals** | LLMs, tokens and context windows at conceptual depth; prompts, inference and sampling; hallucination; streaming; structured output vs tool calling; OpenAI and OpenRouter roles; retries, rate limits, model/provider choice and cost accounting; evaluation basics | 2, high relevance here / M6, M10 |
| M23 | **RAG and document ingestion** | Why retrieval exists; RAG vs prompting vs fine-tuning; loading/parsing, chunking, embeddings, indexing, retrieval, prompt assembly and generation; citations; hybrid search and reranking; updates/deletion; retrieval vs answer evaluation; prompt injection and tenant isolation | 2, high relevance here / M8, M15, M22 |
| M24 | **Embeddings, Pinecone and pgvector** | What a vector represents; dimensions and model compatibility; cosine/dot/Euclidean concepts; exact vs approximate nearest neighbors; HNSW/IVFFlat overview; top-k vs threshold; metadata filters; Pinecone index/namespace vs pgvector tables/indexes; tenancy, deletion and cost trade-offs | 2 / M13, M23 |
| M25 | **LangChain, LangGraph and LlamaIndex** | Library vs model; chain vs workflow vs agent; retrieval/model/tool abstractions; LangGraph state, nodes, edges and checkpoints; LlamaIndex ingestion/retrieval abstractions; state persistence; loops, budgets, tool authorization, retries, evaluation and when plain code is simpler | 2 / M22-M24 |
| M26 | **Neo4j and graph-backed applications** | Nodes, relationships, labels and properties; graph DB vs relational joins vs vector store; Cypher MATCH/WHERE/RETURN, CREATE/MERGE; constraints and indexes; traversal and relationship patterns; graph-backed retrieval basics; ownership/tenant checks and query limits | 2 / DBMS; DSA graphs |

### F. Connecting the skills to the resume

| ID | Section | What it will cover | Tier / requires |
| --- | --- | --- | --- |
| M27 | **System-design bridge through your load balancer** | Scale requirements, stateless services, routing, consistent hashing, virtual nodes and health checks; connect to A0-A4 and S10 in the architecture companion; use its wider worked-system track and question bank | 2 / M13-M19; DSA hashing/searching; CN |
| M28 | **Resume project and experience deep-dives** | Architecture, personal contribution, request/data flow, technology choices, alternatives, failure cases, tests and metrics for the internships, Zyke, load balancer, Megalith and Membition; 30-second/2-minute/5-minute explanations; follow-up banks grounded in available evidence | 1 / relevant modules above |
| M29 | **Consolidation and interview drills** | Technology map, confusable-pairs tables, request-flow diagrams, output prediction, debugging prompts, short Q&A, project-question index, revision schedules and final self-test | Revision / completed modules |

---

## 3. The Node.js section: example of the intended depth

The Node.js chapter must answer the user's example directly before introducing internals.

### Planned subsections

1. What Node.js is; JavaScript vs V8 vs Node.js vs Express.
2. What it means to execute JavaScript outside the browser.
3. Why backend applications use it, and what workload characteristics matter.
4. The architecture: JavaScript/V8, native bindings, libuv, OS and worker pool.
5. A tiny HTTP server, followed by a request trace.
6. How multiple requests make progress; concurrency vs parallelism.
7. Blocking vs non-blocking operations; why adding async does not move CPU work elsewhere.
8. Event loop, timers, promises and nextTick; label version/context-dependent ordering.
9. Modules: CommonJS/ES modules; packages, npm, package.json and lockfiles.
10. Buffers, streams and backpressure, taught through a file-transfer example.
11. Processes, worker threads and clustering; internal worker pool vs JavaScript worker threads.
12. Errors, resource cleanup, configuration and graceful shutdown.
13. When Node.js is a good fit; when another execution approach is better.
14. Resume connection: Express load balancer, proxy overhead and bounded downstream work.
15. Must remember, common wrong answers, Q&A, practice and exit checklist.

### Example interview ladder

- What is Node.js?
- Is it a language, framework, server or runtime?
- Why use it in a backend?
- How can it handle many clients?
- What does single-threaded mean in this context?
- Does every asynchronous operation run on the worker pool?
- Does async/await make CPU-heavy JavaScript non-blocking?
- Why might a large JSON operation delay unrelated requests?
- When would you use a worker thread, another process or a durable queue?
- How would you explain the choice of Node.js in your load-balancer project?

The architecture and blocking topics are grounded in the [Node.js introduction](https://nodejs.org/learn/getting-started/introduction-to-nodejs), [event-loop guide](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) and [event-loop/worker-pool guide](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop). These are selected fundamentals, not evidence of a numerical interview frequency.

---

## 4. Resume coverage map

| Resume skill or supporting claim | Where it belongs |
| --- | --- |
| C++, C | Existing DSA/OOP; add a compressed C vs C++ memory/lifetime refresher to the new roadmap if useful, without repeating those books |
| JavaScript | M1-M2 |
| TypeScript | M3; applied in M5/M21 |
| Python | M10; applied in M11/M12/M22-M25 |
| SQL | Existing DBMS; applied PostgreSQL in M13 |
| Node.js, Express | M4-M5 |
| REST design | M6 |
| JWT, OAuth 2.0; signed/revocable invites; NextAuth/JWE/HKDF experience | M7-M8; specialized JWE/HKDF details as a resume-specific follow-up, supported by actual project code when available |
| Webhooks; Razorpay payment and credit logic | M9 |
| Flask, FastAPI, Pydantic | M11 |
| Django, DRF | M12 |
| PostgreSQL | M13 |
| MongoDB; nested records and aggregation dashboards | M14-M15 |
| GCP Cloud Tasks; async embedding workers | M15/M18/M23 |
| Docker | M16 |
| Nginx, PM2 | M17 |
| AWS EC2, ELB, CDN | M18; CloudFront can be a named example, not an assumption about the resume's actual CDN |
| GitHub Actions, CI/CD | M19 |
| React.js | M20 |
| Next.js 14, Next.js API routes, Edge Middleware | M21 |
| Tailwind | Compressed CSS/responsive subsection in M21 |
| OpenAI APIs, OpenRouter APIs | M22 |
| RAG | M23 |
| Pinecone, pgvector | M24 |
| LangChain, LangGraph, LlamaIndex | M25, applied in M23 |
| Neo4j | M26 |
| Consistent hashing, health checks, throughput/remapping claims | M27-M28 |
| Org hierarchy/BFS, SLA state machine, payroll rules, ingestion defects | M28, cross-referencing DSA/OOP/DBMS and M8/M15 |
| Product, analytics and business tools | Completed P0-P5 track below |

A resume bullet is evidence of what the resume says, not proof of a specific implementation or benchmark. Project deep-dives must distinguish documented claims, confirmed code behavior and hypothetical improvements.

---

## 5. Product and analytics track: fully authored

This track follows the completed main backend/SDE and architecture sequences as requested. It covers the second resume's remaining skills.

**Started 18 October 2026:** the dedicated [Product and Analytics roadmap](/docs/product-analytics) and [P0: Product Thinking, Requirements and Design Communication](/docs/product-analytics/product-thinking-requirements-design) are authored in Product Analytics Notes/. P0 includes 53 executed local worksheet checks; manual design/research exercises remain manual. P1 is now authored with 88 executed local pricing/evidence checks. P2 is now authored with 95 executed SQLite/analytics/experiment-arithmetic checks. P3 is now authored with 72 Python checks, 38 native Excel checks and six workbook mutation scenarios. P4 is now authored with 79 Python/SQLite and 36 real Chrome/D3 checks. P5 is now authored with 12 isolated output drills and 15 source/coverage audits, seven resume story cards, 60 Q&As, revision schedules and two final 45-minute mocks. All seven Product and Analytics handbook files are authored; manual practice and original claim corroboration remain separate.

| ID | Section | Coverage |
| --- | --- | --- |
| P0 | **Product thinking, requirements and design communication** | User problem, stakeholders, discovery, prioritization, success criteria; BRDs, acceptance criteria and requirements traceability; user flows and wireframes; Figma prototyping and Notion documentation basics |
| P1 | **Pricing and unit economics** | Usage-based pricing, credits, cost per generation, gross margin, provider-cost aggregation, failed/retried generations and pricing trade-offs; Zyke as the documented case |
| P2 | **Product analytics and experiments** | Events/properties, tracking plans, funnels, cohorts, retention and activation; metric definitions; experiment/causality basics; PostHog, GA4 and Microsoft Clarity roles |
| P3 | **Python and Excel for analysis** | NumPy arrays, shape/vectorization/broadcasting; pandas filtering, joins, groupby, missing values and dates; Excel formulas/lookups/pivots; reconciliation and reproducible analysis |
| P4 | **Marketing measurement and data visualization** | Google/Meta Ads basics, attribution and conversion denominators; CTR/CPC/CPA/ROAS vocabulary; D3 scales/selections/data binding; treemap/chart choices and misleading graphs; marketing-digest case |
| P5 | **Product/analytics resume drills and revision** | Product decisions, quantified outcomes, trade-offs, stakeholder examples and concise answers; distinguish measured impact from attribution assumptions |

Account-console details, provider prices and ad-platform behavior will be researched when these chapters are written.

---

## 6. Note format and voice

Keep the existing handbook system, adapted to tools:

1. **Header:** module, realistic study time, tier, prerequisites.
2. **Why this module matters:** which questions it prepares you to answer.
3. **One organizing principle:** the mechanism that holds the chapter together.
4. **What it is and why it exists:** plain definitions before terminology.
5. **Where it fits:** an application diagram.
6. **How it works:** numbered steps, short code and a request/data trace.
7. **When to use it and when to choose an alternative.**
8. **Comparisons:** every likely confusion gets a table.
9. **Resume connection:** documented example plus likely follow-ups.
10. **Must remember:** non-obvious points only.
11. **Common wrong answers:** incorrect claim and corrected reasoning.
12. **Interview Q&A:** crisp answer, then a likely follow-up.
13. **Practice:** a few distinct output/trace/debug/design exercises.
14. **Exit checklist and Next.**

Important mechanisms receive full treatment; syntax and small tools use compressed blocks. Target roughly 400-800 lines for a substantial chapter, with shorter files where the subject warrants it. Length is a planning guide, not a quota.

The writing should remain direct, explanatory and practical. Begin with the simple answer, then earn each additional layer of depth. Avoid assuming that familiarity with a package name means the reader understands the underlying mechanism.

---

## 7. Verification and version rules

- Execute runnable examples and include the actual output, with runtime/package versions recorded.
- Preserve useful verification scripts/fixtures in a small examples directory so evidence is reproducible.
- Verify event-loop examples in the stated Node version and module mode; distinguish guarantees from one observed ordering.
- Use the actual database engine for engine-specific claims. SQLite cannot stand in for PostgreSQL or MongoDB concurrency behavior.
- Simulate payment webhooks and AI-provider errors locally where possible. Label mocks, simulations and documented behavior honestly.
- Paid services are not required for learning the fundamentals. A mocked provider must never be presented as a live result.
- Benchmarks must record workload, concurrency, payload, hardware/runtime and measurement method.
- For security examples, verify both the allowed path and rejected cross-user/cross-tenant paths.
- Check currently maintained official documentation before framework-specific chapters.
- Anchor Next.js explanations to the resume's **Next.js 14**, with explicit notes for later versions. The study website's own installed version is a separate context.
- Distinguish Express 4 from Express 5 async error propagation.
- Label Python interpreter/build details where the GIL or concurrency behavior depends on them.
- Explain concepts first; provider APIs and exact limits can change.

Research examples that influence the syllabus:

- Node separates event-loop callbacks from worker-pool work: hence M2/M4 focus on blocking and concurrency.
- [Express error handling](https://expressjs.com/en/5x/guide/error-handling/) documents Promise-aware handling in Express 5: hence the version note.
- [Flask async documentation](https://flask.palletsprojects.com/en/stable/async-await/) explains WSGI request handling: hence Flask vs FastAPI requires an execution-model comparison.
- [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/) distinguishes permission checks and their limits: hence ownership/list filtering deserves explicit exercises.
- [Cloud Tasks limitations](https://docs.cloud.google.com/tasks/docs/common-pitfalls) includes duplicate execution: hence idempotent workers are essential.
- [Razorpay webhook validation](https://razorpay.com/docs/webhooks/validate-test/) includes signature checking, idempotency and event ordering: hence M9 goes beyond a webhook definition.
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling) describes an application/model interaction loop: hence tool execution is taught separately from generated text.

---

## 8. Dependencies and incremental delivery

### Reading order

- Start **M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6**.
- Continue with **M7 -> M8 -> M9** for authentication and reliable integrations.
- Python branch: **M10 -> M11/M12**, using the shared API fundamentals from M6-M8.
- Data branch: **M13/M14 -> M15**.
- Deployment branch: **M16 -> M17 -> M18 -> M19**.
- Frontend branch: **M20 -> M21**.
- AI branch: **M22 -> M23 -> M24 -> M25**; M26 draws on existing graphs/DBMS.
- Finish with **M27 -> M28 -> M29**. Project explanations can be practiced earlier as their dependencies become available.

Dependencies are conceptual, not a demand to reread every older chapter. Short refreshers should make each section usable.

### File convention

- Roadmap: resume-skills-handbook-part-1-master-roadmap.md
- Teaching: resume-skills-handbook-part-N-module-X-topic.md
- M0 starts at Part 2; M28 is Part 30; M29 consolidation is Part 31.
- Product/analytics has its own Product Analytics Notes/ folder and roadmap; P0-P5 and the roadmap are fully authored.

### Site integration

When teaching chapters begin, add one Resume Skills subject using the existing sync pipeline.

- Register the subject and sidebar groups in study-guide/scripts/sync-notes.mjs.
- Add the search tag in study-guide/components/search-dialog.tsx.
- Register only chapters that actually exist; expand group lists as chapters are delivered.
- Keep edits in source Markdown; generated content/docs copies are not the authoring location.
- The home page already derives subject cards from the page tree.
- Validate sync coverage and run the appropriate site build after integration.

### Next concrete section

Authored: the master roadmap and **M0-M29**, including consolidation and interview drills: **31 files**. The [architecture companion roadmap](/docs/system-design) is available. The architecture companion is fully authored: all 21 files, including A0-A4, S0-S13 and consolidation. The separate product/analytics track now has its roadmap and all P0-P5 authored: **seven files, no planned authoring sections remaining**. Learning mastery is assessed separately.

---

## 9. Primary-source reading map

Sources checked for the initial plan; chapter authors must revisit version-sensitive pages.

| Area | Primary references |
| --- | --- |
| JavaScript and TypeScript | [MDN closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures), [MDN promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises), [TypeScript narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing) |
| Node.js | [Introduction](https://nodejs.org/learn/getting-started/introduction-to-nodejs), [event loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick), [blocking and worker pool](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop) |
| Express | [Error handling](https://expressjs.com/en/5x/guide/error-handling/), [Express 5 migration](https://expressjs.com/en/guide/migrating-5/) |
| Python backends | [Python exceptions](https://docs.python.org/3/tutorial/errors.html), [Flask async](https://flask.palletsprojects.com/en/stable/async-await/), [FastAPI async](https://fastapi.tiangolo.com/async/), [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/), [Django async](https://docs.djangoproject.com/en/6.0/topics/async/), [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/) |
| API security | [OWASP object-level authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/), [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) |
| Data stores | [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), [MongoDB embedding](https://www.mongodb.com/docs/manual/data-modeling/embedding/), [pgvector](https://github.com/pgvector/pgvector), [Neo4j Cypher](https://neo4j.com/docs/getting-started/cypher/) |
| Containers/cloud/payments | [Docker image building](https://docs.docker.com/get-started/docker-concepts/building-images/), [AWS ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html), [Cloud Tasks limitations](https://docs.cloud.google.com/tasks/docs/common-pitfalls), [Razorpay webhooks](https://razorpay.com/docs/webhooks/validate-test/) |
| React and Next.js | [React render and commit](https://react.dev/learn/render-and-commit), [Next.js 14 Server Components](https://nextjs.org/docs/14/app/building-your-application/rendering/server-components), [Next.js 14 caching](https://nextjs.org/docs/14/app/building-your-application/caching) |
| AI applications | [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling), [OpenAI embeddings](https://developers.openai.com/api/reference/resources/embeddings/methods/create), [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), [LlamaIndex RAG](https://developers.llamaindex.ai/python/framework/understanding/rag/), [Pinecone overview](https://docs.pinecone.io/guides/get-started/overview), [OpenRouter prompt caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching) |
| Analytics references | [PostHog funnels](https://posthog.com/docs/product-analytics/funnels), [PostHog retention](https://posthog.com/docs/product-analytics/retention), [GA4 key events](https://support.google.com/analytics/answer/9267568?hl=en), [pandas tutorials](https://pandas.pydata.org/docs/getting_started/intro_tutorials/) |

---

## 10. Progress

- [x] Existing handbook structure reviewed.
- [x] Resume skills mapped to planned sections.
- [x] Backend/SDE-first preference confirmed.
- [x] Primary-source research completed for the initial syllabus.
- [x] Dependencies, note format and verification rules defined.
- [x] Master roadmap written.
- [x] M0: How a Backend Works written; 13 HTTP verification cases passed.
- [x] M1: JavaScript Fundamentals written; 30 isolated ES-module snippets verified, with 24 interview Q&As.
- [x] M2: Asynchronous JavaScript written; 28 isolated examples verified (27 ES modules and one CommonJS), with 26 interview Q&As.
- [x] M3: TypeScript Fundamentals written; 16 compiled/runtime examples and 10 expected compiler rejections verified, with 28 interview Q&As.
- [x] M4: Node.js written; 20 isolated runtime cases verified, including 16 HTTP checks, with 30 interview Q&As.
- [x] M5: Express.js written; 16 runtime examples, 39 API checks and five typed boundary checks verified, with 28 interview Q&As.
- [x] M6: REST APIs and HTTP written; 68 HTTP checks verified, with 28 interview Q&As and ten practice tasks.
- [x] M7: Authentication written; 86 checks (38 credential/session/token/crypto, 32 HTTP, 16 OAuth-model), with 30 interview Q&As and ten practice tasks.
- [x] M8: API Security written; 74 checks (22 policy/input, 46 HTTP, six SQLite), with 30 interview Q&As and ten practice tasks.
- [x] M9: Webhooks and payments written; 57 checks (21 core, 26 HTTP, six reconciliation fixtures, four file/process recovery), with 30 interview Q&As and ten practice tasks.
- [x] M10: Python Fundamentals written; 44 checks (24 language, six concurrency, 14 application-boundary), with 30 interview Q&As and ten practice tasks.
- [x] M11: Flask/FastAPI written; 80 checks (two protocol, ten Pydantic, 52 real HTTP, 16 framework-runtime), with 30 interview Q&As and ten practice tasks.
- [x] M12: Django/DRF written; 76 checks (15 ORM, 14 transaction, nine framework, 38 real HTTP), three additional management checks, 30 interview Q&As and ten practice tasks.
- [x] M13: PostgreSQL written; 60 real-engine checks (19 core, 14 concurrency, eight pool, seven query-plan, 12 reservation-service), 30 interview Q&As and ten practice tasks. Isolated cluster stopped and removed; existing PostgreSQL service untouched.
- [x] M14: MongoDB written; 65 real-engine checks (17 core, 12 query/aggregation, ten index, six atomic-update, 15 transaction/service, five pool/cursor), 30 interview Q&As and ten practice tasks. Isolated replica set stopped and removed; existing MongoDB service untouched.
- [x] M15: caching/jobs/ingestion written; 58 checks (ten local cache, 13 SQLite job, 23 parser/format, 12 ingestion), 30 interview Q&As and ten practice tasks. Redis/Cloud Tasks are documented bridges; temporary databases removed and no persistent listener started.
- [x] M16: Docker written; 40 actual Linux-container checks (five build, six HTTP, five lifecycle, five network, three readiness, ten runtime, six storage), 30 interview Q&As and ten practice tasks. Owned resources cleaned; Docker restored to stopped; public base images/build cache retained.
- [x] M17: Linux deployment written; 40 checks (six Linux, 14 Nginx, four TLS, eight PM2, five lifecycle, three host), 30 interview Q&As and ten exercises. Actual worker crash/reload/drain and local TLS; host boot/public CA remain documented extensions. Dependency audit retained; owned resources removed and Docker restored to stopped.
- [x] M18: AWS/GCP written; 53 local checks (nine SDK, 14 authentication, 16 HTTP/SQLite worker, 14 HTTP cache), 30 interview Q&As and ten exercises. Provider behavior researched; offline SDK/generated-key trust and actual local HTTP/transactions clearly separated. No account/API/cloud resources or Docker startup; temporary listeners/database cleaned.
- [x] M19: Git/CI/testing/observability/performance written; 62 checks (15 Git, three contracts, four HTTP, seven traces, two logs, four metrics, eight statistics, five load, nine release gates, five static workflow), 30 interview Q&As and ten exercises. Actual local release gates and official SDK traces; hosted Actions/production capacity are explicitly unverified. Fixture cleanup complete; main Git history unchanged.
- [x] M20: React written; 50 actual Chrome checks (eight state, six identity, six effects, three Strict Mode, six forms, four sharing, 11 API, five selected accessibility/layout, one browser-health), 30 interview Q&As and ten exercises. Real development/production bundles and HTTP race/abort; screenshots inspected. No SSR/React Compiler/full accessibility claim; browser/server closed.
- [x] M21 teaching chapter and 54 actual production-framework/HTTP/browser checks authored; Next.js 14/Tailwind 3 context separated from newer versions. Thirty Q&As, ten exercises; dependency audit and scope limits recorded. Screenshots inspected; browser/listeners closed.
- [x] M22 teaching chapter and 79 local checks authored: actual SDK/HTTP/SSE/errors and tokenizer, tool/authorization, bounded retries, Decimal cost/admission/concurrency and deterministic grader mechanics. Thirty Q&As and ten exercises. Handwritten peer only; no model inference/provider calls/keys/charges. SDK/listener closed.
- [x] M23 teaching chapter and 99 local checks authored: real PDF extraction, page/word chunk provenance, SQLite FTS5/BM25/publication rollback, scoped HTTP/source/context, citations, stale revisions/tombstones/cache and tiny lexical evaluation. Thirty Q&As and ten exercises. RRF lists handcrafted, reranker heuristic, answer extractive; no embeddings/LLM/OCR/hosted calls. Temporary databases/listener removed.
- [x] M24 teaching chapter and 92 local checks authored: real PostgreSQL 16.15/pgvector 0.8.6 operators, exact scoped retrieval/RLS, atomic publication rollback, revision/tombstone guards, HNSW/IVFFlat plans and sampled recall. Thirty Q&As and ten exercises. Authored vectors; Pinecone JSON body contracts only, no learned model/hosted calls. Portable runtime hash-verified; owned database cluster removed.
- [x] M25 teaching chapter and 89 actual framework checks authored: LangChain composition/parsing/async/stream and scripted agent tools, LangGraph reducers and file-checkpoint resume across fresh processes, strict owned review/freshness and local idempotent replay recovery, LlamaIndex ingestion/metadata-filtered retrieval/synthesis/persist/reload/delete. Thirty Q&As and ten exercises. Fake/scripted models, extractive graph draft and handwritten feature encoder; no learned inference/provider/hosted tracing. All 21 workers exited and temporary data removed.
- [x] M26 teaching chapter and 76 real-engine checks authored: Neo4j Community 2026.09.0 over loopback Bolt, Cypher 5 patterns/nulls/constraints/MERGE, bounded tenant-scoped paths, rollback/concurrent correctness, actual index plans/deletion and source-revision/tombstone acceptance. Thirty Q&As and ten exercises. Hand-authored graph; application authorization only, no Enterprise RBAC/APOC/GDS/model/Aura/performance claim. Portable vendor archives hash-verified; owned Java process, listener and temporary data cleaned.
- [x] M27 teaching chapter and 95 local checks authored: 21 deterministic ring, 17 pool-policy, eight capacity-arithmetic, 11 in-process cache-model and 38 real HTTP checks. Thirty Q&As and ten exercises. Actual forwarding/readiness/failure/drain/admission/cancellation/deadline over owned loopback sockets; no original-project throughput/latency reproduction, distributed cache or production authentication claim. All fixture listeners/agents/timers cleaned.
- [x] M28 teaching chapter authored for all seven resume experiences/projects: seven short pitches, seven two-minute outlines, seven five-minute walkthroughs, 30 Q&As and ten exercises. Eighty-one checks passed: 68 teaching-model/arithmetic and 13 PDF-provenance checks. Actual SQLite audit rollback, reopen alert dedupe and batch rollback; original project code/metrics/revenue/compliance remain explicitly unverified. Temporary databases removed; no persistent model listener.
- [x] M29 consolidation authored: 29-module map, 36 confusable pairs, 14 executed output drills, 16 debug cards, 60 rapid-fire Q&As, two 45-minute mocks, revision schedules and 24-question self-test. Forty-three checks passed: 14 isolated Node/Python/SQLite outputs and 29 canonical chapter-reference audits. All 14 workers exited; SQLite in-memory connections closed. Editorial drills are not production/user-assessment evidence; the architecture/product extensions were subsequently authored in their separate companion tracks.
- [x] Resume Skills subject registered in website navigation and search.
- [x] Product/analytics track fully authored: roadmap, P0-P4 and P5 consolidation; source examples, verification records, navigation and search integrated.

---

## 11. Architecture and system-design extension

**Added at the user's request on 13 October 2026.**

The curriculum now includes [a separate architecture/system-design plan](Architecture-System-Design-Notes-Plan.md) and [a compiled 60-question bank](Architecture-System-Design-Question-Bank.md).

The architecture track has five foundation sections (design method/estimation; application boundaries; data/cache/scale; reliable workflows; secure operation) and fourteen worked designs. Its planned handbook is 21 files including a roadmap and consolidation.

Worked systems: URL shortener; rate limiter; notifications/webhooks; file upload/processing; ticket/inventory booking; chat; feeds/photo sharing; job scheduler; checkout/payments/credits; search/autocomplete; load balancing/distributed cache; multi-tenant SaaS; RAG knowledge base; analytics pipeline.

Each case starts with a small buildable system, APIs, data model and request traces, then addresses concurrency, failures and growth. It includes an implementation path, verification exercises and interview follow-ups.

Resume M27 is the bridge to that track, not the entirety of architecture coverage. Resume M28 uses the relevant worked designs and the bank's eight resume-specific prompts. The existing OOP LLD examples remain useful foundations, especially BookMyShow before distributed reservation design.

Interleave architecture after its prerequisites: A0/A1 and URL shortening after API/data basics; rate limiting and SaaS permissions after auth; queues/booking/payments after transactions and jobs; AI architecture after RAG. Product/analytics follows those completed sequences and is now fully authored; continue with manual exercises, evidence recovery and interview practice.

- [x] Architecture research and syllabus compiled.
- [x] Sixty architecture/design/failure/resume questions compiled.
- [x] Worked architecture chapters, implementations and final consolidation written; all 21 companion files authored.
