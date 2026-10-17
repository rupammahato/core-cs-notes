"""Generate the architecture roadmap from a structured syllabus and the existing bank."""
from pathlib import Path
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
foundation_labels = [f'A{i}' for i in range(5)]
definitions = [
('A0','How to approach a design question','design-method-estimation',3,4,[],[0,6],'Scope, actors, requirements, invariants, workload/units, APIs/data, baseline and trade-offs.'),
('A1','Application architecture and service boundaries','application-architecture-service-boundaries',3,4,['A0'],[5,11,12],'Controllers/services/data access, modular baseline, state ownership, synchronous calls/events, proxy/gateway/BFF.'),
('A2','Data, caching and scaling','data-caching-scaling',4,5,['A0'],[13,14,15],'Access patterns, indexes, replicas/shards, cache coherence, hot keys and explicit consistency requirements.'),
('A3','Reliable workflows and concurrency','reliable-workflows-concurrency',4,5,['A0','A2'],[9,13,15],'Deadlines/retries, operation identity, constraints/versions/locks, outbox, recovery and compensation.'),
('A4','Operating a secure and observable system','secure-observable-operations',3,4,['A1','A2','A3'],[8,16,17,18,19],'Tenant scope, least privilege, quotas, safe uploads, readiness/drain, telemetry, SLOs and capacity evidence.'),
('S0','URL shortener','url-shortener',3,4,foundation_labels,[6,13],'Create/redirect contracts, unique codes, collision handling, expiry, cache and bounded analytics.'),
('S1','Rate limiter','rate-limiter',4,5,foundation_labels,[7,8,15],'Window/token-bucket algorithms, local/shared atomic decisions, quota keys, clocks and degraded behavior.'),
('S2','Notification and webhook delivery service','notifications-webhooks',4,5,foundation_labels+['S1'],[9,15],'Preferences/subscriptions, durable delivery attempts, signatures, retries, duplicate effects and provider limits.'),
('S3','File upload, storage and processing service','file-upload-processing',4,5,foundation_labels,[8,15,18,23],'Metadata/object boundaries, authorization, upload completion, validation/quarantine, jobs and cleanup.'),
('S4','Ticket booking and limited-inventory reservation','booking-reservations',5,6,foundation_labels,[9,13,15],'Scarce inventory, holds, authoritative expiry, atomic reservation, concurrent callers and late payment.'),
('S5','Chat and real-time messaging','chat-messaging',4,6,foundation_labels,[6,7,15],'Connections, durable messages, message IDs, ordering/ack scope, offline fetch and reconnect.'),
('S6','Social feed and photo sharing','social-feed-photo-sharing',4,6,foundation_labels+['S3'],[14,15,20],'Post/media ownership, feed access patterns, fan-out choice, pagination, hot users and freshness.'),
('S7','Background job scheduler and worker platform','job-scheduler-workers',4,5,foundation_labels,[15,17],'Job identity/state, schedules, claims/leases, retries, worker crashes, fairness and backlog.'),
('S8','Checkout, payments and credit ledger','checkout-payments-credit-ledger',5,7,foundation_labels+['S4','S7'],[9,13,22,28],'Order/payment states, atomic ledger effects, idempotency, provider ambiguity and reconciliation.'),
('S9','Search and autocomplete','search-autocomplete',4,6,foundation_labels+['S3','S7'],[13,23,24],'Prefix/full-text/semantic access, source/index lag, ranking, permission, updates and latency.'),
('S10','Load balancer and distributed cache','load-balancer-distributed-cache',4,6,foundation_labels,[15,19,27],'Placement versus load, membership/health, hot keys, replicas, invalidation and node rejoin.'),
('S11','Multi-tenant SaaS with authentication and permissions','multi-tenant-saas',4,6,foundation_labels+['S1'],[7,8,21,28],'Tenant identity, roles/ownership/sharing, sessions/BFF, invitations, quotas and negative tests.'),
('S12','Multi-tenant RAG knowledge-base platform','multi-tenant-rag',5,7,foundation_labels+['S3','S7','S9','S11'],[22,23,24,25,26],'Versioned ingestion, scoped retrieval, accepted citations, model/tool budgets, evaluation and deletion.'),
('S13','Analytics event pipeline and dashboard','analytics-event-pipeline',4,6,foundation_labels+['S2','S7'],[15,19,28],'Event contracts/identity, ingestion, event time, duplicate/late data, aggregates and metric definitions.'),
]
entries=[]
for module,(label,title,slug,low,high,prereqs,resume,focus) in enumerate(definitions):
    part=module+2
    filename=f'system-design-handbook-part-{part}-module-{module}-{slug}.md'
    entries.append({'label':label,'module':module,'part':part,'title':title,'slug':slug,'hours':[low,high],'prerequisites':prereqs,'resume_modules':resume,'focus':focus,'file':filename,'status':'Available' if (ROOT/'System Design Notes'/filename).is_file() else 'Planned'})
entries.append({'label':'Revision','module':None,'part':21,'title':'Consolidation and design mocks','slug':'consolidation','hours':[2,3],'prerequisites':[e['label'] for e in entries],'resume_modules':[29],'focus':'Design-pattern map, changed-requirement/failure drills, timed mocks and final self-test.','file':'system-design-handbook-part-21-consolidation.md','status':'Available' if (ROOT/'System Design Notes/system-design-handbook-part-21-consolidation.md').is_file() else 'Planned'})
source=ROOT/'Architecture-System-Design-Question-Bank.md'
bank_text=source.read_text(encoding='utf-8')
embedded=bank_text.split('## Architecture concepts and decisions',1)[1].split('## Research and interpretation',1)[0].strip()
embedded='### Architecture concepts and decisions\n\n'+embedded
for heading in ('System-building prompts','Failure and concurrency follow-ups','Resume-specific architecture questions'):
    embedded=embedded.replace('## '+heading,'### '+heading)
questions=[]
for line in bank_text.splitlines():
    if re.match(r'^\| Q\d{2} \|',line):
        identity,question,checkpoints,mapping=[cell.strip() for cell in line.strip('|').split('|')]
        questions.append({'id':identity,'question':question,'checkpoints':checkpoints,'mapping':mapping,'source_row':line})
resume_catalogue=json.loads((ROOT/'examples/resume-skills/module-29-consolidation/module-catalogue.json').read_text(encoding='utf-8'))
resume_routes={e['module']:e['route'] for e in resume_catalogue}
resume_routes[29]='/docs/resume-skills/consolidation-interview-drills'
def resume_links(modules):
    return ', '.join(f'[M{m}]({resume_routes[m]})' for m in modules)
table='| Label | Numeric module / part | Section | Hours | Requires in this track | Resume refresher | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n'
def section_title(entry):
    return f"[{entry['title']}](/docs/system-design/{entry['slug']})" if entry['status']=='Available' else f"**{entry['title']}**"
table+='\n'.join(f"| {e['label']} | {'—' if e['module'] is None else e['module']} / {e['part']} | {section_title(e)} | {e['hours'][0]}–{e['hours'][1]} | {', '.join(e['prerequisites']) if e['label']!='Revision' else 'All foundations and worked designs'} | {resume_links(e['resume_modules'])} | {e['status']} |" for e in entries)
focus_table='| Label | Defining mechanism to build and explain |\n| --- | --- |\n'+'\n'.join(f"| {e['label']} | {e['focus']} |" for e in entries[:-1])
hours=[sum(e['hours'][i] for e in entries) for i in (0,1)]
checklist='\n'.join(f"- [ ] {e['label']}: {e['title']}" for e in entries)
chapter=r'''# Architecture and System Design Placement Handbook — Part 1: Master Roadmap

**From a buildable backend to defensible architecture: requirements, state, failures, scale and evidence. Backend/SDE first.**

---

## 0. What is available now

This companion extends the completed [Resume Skills handbook](/docs/resume-skills). That handbook explains the stack and connects it to your projects. This track shows how to assemble a system, implement its defining mechanism and defend its behavior under a changed requirement or failure.

**Organizing principle: start with a correct small system; add architectural complexity only when a requirement, bottleneck or failure justifies it.**

| Item | Current status |
| --- | --- |
| Authored sources | This master roadmap, [A0: How to approach a design question](/docs/system-design/design-method-estimation), [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries), [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling), [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency), [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations), [S0: URL shortener](/docs/system-design/url-shortener), [S1: Rate limiter](/docs/system-design/rate-limiter), [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks), [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing), [S4: Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations), [S5: Chat and real-time messaging](/docs/system-design/chat-messaging), [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing), [S7: Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers), [S8: Checkout, payments and credit ledger](/docs/system-design/checkout-payments-credit-ledger), [S9: Search and autocomplete](/docs/system-design/search-autocomplete), [S10: Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache), [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas), [S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag), [S13: Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline) and [Consolidation and design mocks](/docs/system-design/consolidation) |
| Completed handbook | 21 authored files: roadmap, five foundations, fourteen worked designs and consolidation |
| Foundations A0–A4 | A0–A4 available; all five foundations authored |
| Worked systems S0–S13 | S0–S13 available; all fourteen worked designs authored |
| Interview bank | 60 previously compiled prompts and answer checkpoints, reproduced in §8 |
| Existing bridges | Resume M27 load-balancer mechanisms, M28 project explanations and M29 revision |
| Product/analytics | Separate later track; S13 supplies a technical event-pipeline foundation |

This roadmap links the complete authored track: A0–A4, S0–S13 and final consolidation. All 21 planned files are available on the site. Each teaching chapter has its own implementation, verification scope and unchecked learning checklist; authoring completion does not establish learner mastery or production guarantees.

The repository-root plan and question-bank files remain the planning sources: `Architecture-System-Design-Notes-Plan.md` and `Architecture-System-Design-Question-Bank.md`. Their question checkpoints are included below so you can use them directly on the study site.

---

## 1. What architecture preparation should let you do

After a worked chapter, you should be able to:

1. Clarify the users, core operations, scope and important workload assumptions.
2. State correctness invariants before selecting infrastructure.
3. Propose APIs and a data model with explicit identity, constraints and access patterns.
4. Draw a small baseline and trace at least one read and one write.
5. Explain a concurrent request or crash timeline and its recovery.
6. Identify a demonstrated bottleneck before adding caches, replicas, shards or services.
7. Compare a reasonable alternative using the actual requirement.
8. Build and verify the defining mechanism under a stated environment and evidence boundary.

An architecture diagram is useful when its arrows explain who calls whom, what is persisted and what can be retried. “Database,” “queue” and “cache” labels alone do not establish a transaction boundary, durable completion or fresh permission checks.

Existing OOP material teaches single-process object responsibilities. This track adds communicating processes, durable state, independent failures and workload limits. It builds on DBMS/CN/OS concepts rather than replacing them with tool names.

---

## 2. How the sections were chosen

The ordering combines the earlier research plan, reusable design patterns, entry-level buildability and your resume's specific follow-ups. It is not a measured ranking of company question frequency.

Employer guidance is useful context: Amazon's SDE II page emphasizes practical, accurate, efficient, reliable and scalable design. Its role level is above a campus-entry baseline, so the companion starts smaller and separates deeper extensions. [Amazon SDE II preparation](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep).

The original question-bank research used curated practice catalogs to identify recurring system families. A catalog is evidence about its own selection, not an unbiased record of all employer interviews. The refreshed [Hello Interview catalog](https://www.hellointerview.com/learn/system-design/in-a-hurry/problem-breakdowns) is one such practice source; technical behavior will be checked against primary documentation and executed examples in the relevant chapter.

Every design has three depths:

| Depth | What it means |
| --- | --- |
| Baseline | Small, correct and explainable application with real data ownership and APIs |
| Growth | Change a measured constraint: traffic, latency, storage, availability or operations |
| Deep follow-up | Optional distributed complexity with explicit failure/consistency assumptions |

The default audience is backend/SDE placement preparation. Building a database engine, global active-active payments or consensus proofs is not required before you can explain a reservation transaction or upload state machine.

---

## 3. Complete syllabus and numeric mapping

The labels A0–A4 and S0–S13 identify learning sections. Numeric modules and part numbers identify files; they are not the Resume Skills module numbers. For example, architecture numeric module 5 is S0, not Resume M5.

{{TABLE}}

The planned source conventions are:

- Part 1: `system-design-handbook-part-1-master-roadmap.md`.
- A0–A4: parts 2–6, numeric modules 0–4.
- S0–S13: parts 7–20, numeric modules 5–18.
- Part 21: `system-design-handbook-part-21-consolidation.md`.

The first-pass teaching/build estimates total **{{LOW}}–{{HIGH}} active hours**, including the planned consolidation and excluding this roadmap, breaks, deep extensions and repeated mocks. They are planning estimates, not measured time or a promise of mastery. Use earlier familiarity to shorten a refresher; do not skip the defining failure case merely to meet the estimate.

---

## 4. Foundations: what comes before the worked designs

**A0 — method and estimation:** learn to turn an ambiguous request into actors, operations, non-goals, workload units, APIs/data and invariants. Estimates guide a choice; assumed per-instance capacity must not be presented as a measured result.

**A1 — responsibilities and boundaries:** trace the controller/service/data layers in a buildable application. Separate a logical module from a deployment unit and a network boundary. Compare monolith/modular monolith/services without assuming more boxes make the design better. Architecture styles carry constraints and trade-offs, not a mandatory technology list. [Microsoft architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/).

**A2 — data, cache and scale:** choose storage/indexes from operations and invariants. Distinguish source of truth, replicas, shards and derived caches. Define the stale behavior you permit before proposing TTL or invalidation.

**A3 — reliable workflows:** walk through concurrent callers, retries and crash/ack gaps. Explain which condition/effect shares a transaction, what is outside it and how replay/reconciliation works. Bounded retries need operation safety and a total budget; idempotency needs a precise business identity. [AWS retry guidance](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter), [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

**A4 — secure operation:** carry verified identity and resource permission across all data paths; define quotas, readiness, draining, telemetry and capacity evidence. An available process is not automatically a useful or authorized service.

The writing route is foundations first, then S0–S13. If you already understand equivalent mechanisms, the prerequisite column lets you revisit them selectively. Early cases use A3 and the resume job/payment chapters for basic workflow reasoning; they do not require later S7/S8 implementations to exist.

---

## 5. Worked systems: the mechanism behind each name

{{FOCUS}}

Study S0–S4 first: identity/collisions, shared quotas, delivery, uploads and scarce resources give reusable patterns. S5–S7 add connection/feed/worker lifecycles. S8–S13 deepen payments, search, infrastructure, multi-tenancy, RAG and event analytics.

### Keep related cases distinct

- S2 delivers notifications/webhooks; S7 executes internal jobs. They share retry mechanics but have different recipients, status and completion semantics.
- S4 owns inventory/hold correctness; S8 owns payment/order/ledger correctness. A late payment needs an explicit decision across that boundary.
- S3 establishes upload/storage/processing; S12 adds retrieval, model work, current evidence and evaluation.
- S9 covers prefix/full-text/semantic search choices; S12 is a complete permission-aware RAG application.
- S10 extends [Resume M27](/docs/resume-skills/system-design-load-balancer) into cache ownership, replicas, invalidation and rejoin behavior rather than repeating the same ring definition.
- S13 is a technical event-processing design. It does not mark the later product/analytics curriculum complete.

Existing OOP booking examples are a useful single-process starting point for S4. The architecture case must explain what changes when independent application instances share authoritative inventory.

---

## 6. What every worked chapter will contain

| Step | Reviewable artifact |
| --- | --- |
| Clarify | Actors, core flows, changed requirements and explicit exclusions |
| Define correctness | Named invariant and the authority that enforces it |
| Estimate | Inputs, units, formulas and preserved assumptions |
| Specify | API contracts, resource identity, errors and pagination/idempotency where needed |
| Model data | Entities, keys, constraints, indexes and state ownership |
| Build a baseline | Small architecture with useful read/write traces |
| Implement | Defining mechanism with stated execution/transaction guarantees |
| Break it | Two callers or a crash at a meaningful boundary |
| Recover | Durable state, safe replay/reconciliation and cleanup |
| Grow | Named bottleneck and justified next component |
| Operate | Identity/permissions, limits, readiness, logs/metrics/traces and failure visibility |
| Compare | Chosen option, viable alternative and deciding requirement |
| Reproduce | Setup, seed inputs, commands, versions and actual outputs |
| Rehearse | Follow-ups, wrong answers, practice tasks and unchecked exit items |

An answer should identify whether each arrow is a synchronous request, an asynchronous delivery or a data-replication/update path. Distinguish accepted work from completed work, and execution state from external effects.

---

## 7. Implementation and verification rules

The planned default is Node.js/TypeScript with Express for early concrete backends, PostgreSQL when constraints/transactions are central, and Python/FastAPI for suitable AI/ingestion work. Redis, object storage, queues and Docker are introduced when useful to the case. These are teaching choices; the chapter must justify the capability, not assume the brand is the requirement.

Each implementation will record what actually ran. Real database claims need real engine behavior; a fake provider or clock must be labeled. A local test proves selected fixture behavior, not internet-scale availability, hosted-provider semantics or real model quality.

| Mechanism | Required verification direction |
| --- | --- |
| Unique identity | Collision/duplicate input, storage-enforced rule and safe retry |
| Quota/reservation | Concurrent callers at the final available unit |
| External work | Commit/ack gap, duplicate delivery and ambiguous response |
| Expiry/lease | Boundary time, stale owner and late work; expiry alone is not proof a worker stopped |
| Source/index lifecycle | Late revision, delete/revoke, partial publication and current acceptance |
| Permission | Wrong tenant/resource/action through reads, lists, jobs and derived stores |
| Overload | Bounded admission/queues/pools, deadlines and cleanup |
| Performance | Workload/resources, successful goodput, latency/errors and duration |

Preserve raw fixture inputs and named assertions. Keep production metrics separate from estimates and local observations. Provider-specific patterns need their own boundary: a transaction protects the local records inside it, while an external request may need a separate effect identity and recovery path.

This roadmap validates syllabus/question/link consistency and site integration only. No architecture service, database experiment, cloud resource, payment call or model inference is executed here.

---

## 8. Compiled 60-question bank

The following rows reproduce the existing root bank's questions, checkpoints and mappings. They are prompts for preparation, not completed worked answers or verbatim interview transcripts. A0/S0 labels refer to this companion; Resume M labels refer to the completed stack handbook.

| Range | Category | Count |
| --- | --- | --- |
| Q01–Q24 | Architecture concepts and decisions | 24 |
| Q25–Q38 | System-building prompts for S0–S13 | 14 |
| Q39–Q52 | Failure/concurrency follow-ups for S0–S13 | 14 |
| Q53–Q60 | Resume-specific architecture questions | 8 |

{{BANK}}

---

## 9. How to practice the bank

Begin with **Q01, Q02, Q06, Q10, Q14, Q19, Q25 and Q39**. This set moves a small URL service from scope and data ownership to cache, operation identity and collision handling. It is a practice route through authored worked explanations, followed by the final consolidation drills.

Then add Q26/Q40 for quota races, Q27/Q41 for delivery ambiguity, Q28/Q42 for upload recovery and Q29/Q43 for reservations/late payment. Later pair each system prompt Q25–Q38 with its failure prompt Q39–Q52 before spending time on a more elaborate scale diagram.

For each answer, record:

1. The requirement or assumption that changes the design.
2. The invariant and its state owner.
3. One request/state transition and one failure timeline.
4. A viable alternative and its cost.
5. What evidence would establish the behavior.

Practice conceptual answers in roughly 30–90 seconds, a first sketch in 10–15 minutes and a full design in 35–45 minutes. These are editorial exercise targets, not observed company formats. Introduce a changed requirement midway and record what you missed.

Use the root bank's diagnostic scale: 0 for unable to explain, 1 for vocabulary only, 2 for a coherent mechanism, 3 for mechanism plus trade-off/failure/evidence. The roadmap does not grade you automatically or imply that a score predicts an interview outcome.

---

## 10. Prerequisites and study routes

### Foundations-first route

```text
Resume API/data/security basics + core CS
 -> A0 -> A1/A2 -> A3 -> A4
 -> S0–S4 -> S5–S7 -> S8–S13 -> consolidation
```

The arrows summarize learning order, not runtime service calls. The syllabus table gives the explicit prerequisites; later designs may depend on earlier worked mechanisms.

### Resume-focused revisits

| Goal | Relevant path |
| --- | --- |
| Candidate invitations and org permissions | A0–A4, S1/S11; Resume M7/M8/M28 |
| Payroll SLA and external file sync | A3/A4, S2/S3/S7/S13; Resume M15/M28 |
| Zyke payment and usage effects | A2/A3/A4, S8; Resume M9/M22/M28 |
| Load-balancer project | A0/A2/A4, S10; Resume M19/M27/M28 |
| 10X or Membition RAG | A0–A4, S3/S7/S9/S11/S12; Resume M22–M26/M28 |
| Fest traffic and operations | A0/A4, S3/S4/S8/S13; Resume M19–M21/M28 |

These are revision routes through authored chapters. Use the existing [M28 project explanations](/docs/resume-skills/resume-project-experience-deep-dives) and [M29 revision tools](/docs/resume-skills/consolidation-interview-drills) alongside the completed architecture companion. Unresolved original project details and benchmarks remain unresolved unless their own evidence becomes available.

---

## 11. Technical reading map

The references below are the initial reading map for the authored chapters. Current documentation is not a claim that a local prototype has implemented every feature or that an older project used the same version.

| Area | Primary starting point |
| --- | --- |
| Architecture styles | [Microsoft architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/) |
| Retry budget and safety | [AWS timeouts/retries](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter), [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) |
| Concurrent state | [PostgreSQL 18 locking](https://www.postgresql.org/docs/18/explicit-locking.html) |
| Cache coherence | [Microsoft cache-aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) |
| Upload lifecycle | [S3 multipart uploads](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html) |

Other mechanisms retain the fuller reference map in the root architecture plan and prior Resume Skills chapters. Individual chapters record their own reviewed references and runtime evidence. This initial reading map was checked on **16 October 2026**; the authored track was completed on **18 October 2026**.

---

## 12. Authored progress and learning checklist

| Authoring milestone | Status |
| --- | --- |
| Root architecture syllabus and 60-question bank | Compiled |
| Master roadmap and embedded bank | Available |
| Foundation teaching chapters | A0–A4 available; all five foundations authored |
| Worked implementations and their failure evidence | S0–S13 available; all fourteen worked designs authored |
| Architecture consolidation | [Available: pattern map, all 60 bank drills, six mocks and final self-test](/docs/system-design/consolidation) |

Learning items remain unchecked until you can explain/build the corresponding mechanism:

{{CHECKLIST}}

---

## 13. Continue with revision

Start with [A0: How to approach a design question](/docs/system-design/design-method-estimation), then [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries). Continue with [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling). Continue with [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency). Finish the foundations with [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations). Continue with [S0: URL shortener](/docs/system-design/url-shortener), the first worked design. Continue with [S1: Rate limiter](/docs/system-design/rate-limiter) for window/token-bucket algorithms, atomic quota decisions and failure/degraded behavior. Continue with [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks) for durable delivery attempts, signatures, retries, duplicate effects and provider limits. Continue with [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing) for metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup. Continue with [S4: Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations), [S5: Chat and real-time messaging](/docs/system-design/chat-messaging) and [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing). They develop inventory/payment boundaries, durable reconnectable messaging and privacy-aware hybrid feeds. Continue with [S7: Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers), [S8: Checkout, payments and credit ledger](/docs/system-design/checkout-payments-credit-ledger) and [S9: Search and autocomplete](/docs/system-design/search-autocomplete). They develop recoverable job effects, uncertain payment commits, balanced credit posting and current-authorized search over asynchronous projections. Continue with [S10: Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache) and [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas). They develop placement versus live load, current cache version/rejoin fences, tenant/session/resource authority, invitations, quotas and scoped delayed work. Continue with [S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag) for versioned ingest, current authorized retrieval, request evidence and citation acceptance, bounded uncertain generation and deletion. Its runnable vectors/model are deterministic local fixtures. Finish with [S13: Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline), architecture part 20 / numeric module 18, for event identity, atomic progress, cohorts, late data, rebuild and privacy. Then use [Consolidation and design mocks](/docs/system-design/consolidation), Part 21, for cross-system revision and manual self-assessment.

The Architecture and System Design track is fully authored: roadmap, all foundations A0–A4, all worked systems S0–S13 and consolidation, 21 files. No planned architecture teaching chapter remains unfinished. Learning checklists remain unchecked for manual self-assessment. The separate product/analytics track P0–P5 remains later work.
'''
for key,value in [('TABLE',table),('FOCUS',focus_table),('BANK',embedded),('CHECKLIST',checklist),('LOW',str(hours[0])),('HIGH',str(hours[1]))]:
    chapter=chapter.replace('{{'+key+'}}',value)
assert not re.search(r'\{\{[A-Z_]+\}\}',chapter)
filename='system-design-handbook-part-1-master-roadmap.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
metadata={'chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),'planned_files':21,'foundations':5,'worked_systems':14,'consolidations':1,'available_files':len(list((ROOT/'System Design Notes').glob('*.md'))),'compiled_questions':60,'unchecked_learning_items':20,'estimated_active_hours':hours}
(BASE/'syllabus.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
(BASE/'source-provenance.json').write_text(json.dumps({'checked_date':'2026-10-16','question_bank':{'file':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},'scope':'Roadmap/compiled checkpoint fidelity and syllabus consistency; no worked-system runtime or learner-mastery claim.'},indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
