"""Author S3 with exact executable sources and observed local failure evidence."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
sources = ['estimates.py','objects.py','uploads.py','http_api.py']
outputs = ['estimates','intake','processing','lifecycle','concurrency','http_contract']


def code(name):
    return '```python\n'+(BASE/name).read_text(encoding='utf-8')+'```'


def output(name):
    return '```json\n'+json.dumps(proof['observations'][name],ensure_ascii=False,indent=2)+'\n```'


chapter = r'''# Architecture and System Design Placement Handbook — Part 10
# S3: File Upload, Storage and Processing Service

**Estimated time: 4–5 hours | Architecture numeric module: 8 | Requires: A0–A4; Resume M8/M15/M18/M23 refreshers**

---

## Why this module exists

“Upload a file” includes at least three different facts: the application authorized an upload, some bytes reached storage, and the exact accepted bytes passed the processing policy. A fourth fact—whether the current caller may download them—must remain separate. A file key or successful client callback does not establish all four.

This chapter implements a local metadata/control API, immutable private objects, an upload capability, idempotent completion, quarantine, leased processing, guarded publication, owner-only download and inventory cleanup. Actual loopback HTTP and local files exercise retries, lost publication state, stale workers and deletion before a late result.

**Organizing principle: bind authorization to a specific upload, pin the bytes you validate, and publish only through current authoritative state.**

The runnable fixture accepts at most 1024 bytes of UTF-8 plain text. Its deterministic rejection policy is not antivirus, a general document parser or a claim that a file is harmless. S3 presigned URLs, multipart transfer, PDF/image/video processing and cloud cleanup are architectural extensions discussed explicitly; none is executed or emulated here.

The 30 Q&As are curated interview practice rather than a measured employer-frequency ranking. This chapter answers architecture bank Q28 and Q42: bytes upload successfully, but completion or a processing worker crashes. It builds on [A3's recovery boundaries](/docs/system-design/reliable-workflows-concurrency) and connects to later S6 media and S12 document/RAG systems.

---

## 1. Prompt and clarification questions

**Prompt:** authenticated learners upload private notes. The service should accept an authorized bounded object, process it asynchronously, expose clear status and let only its owner download an approved file. Failed uploads and processing must not leave permanent untracked storage or publish a deleted file.

| Clarification | Architectural effect |
| --- | --- |
| Private documents, public photos or executable/active content? | Authorization, serving origin, content handling and abuse policy |
| Accepted formats and maximum size? | Transfer strategy, validation, parser isolation and resource limits |
| Direct browser-to-object-store or API-proxied bytes? | Bandwidth path, capability policy, CORS and completion authority |
| Resumable/multipart uploads needed? | Upload-session/part identities, manifest, abort and unfinished-part cleanup |
| Immutable uploads or replacements under one file ID? | Version/generation identity and stale processing protection |
| What counts as complete and who may assert it? | Storage verification, pinned object version and job creation |
| Which processing outputs and deadline? | Queue ownership, compute isolation, retries and derived artifact keys |
| How quickly must delete/revoke take effect? | Tombstones, cached/signed downloads and in-flight access |
| Retention, legal hold, quota and privacy requirements? | Metadata/object lifecycle, accounting and deletion policy |
| Traffic, average size, download ratio and CPU cost? | Storage, egress, queue depth, concurrency and cost model |

Do not select a bucket, CDN and queue before answering what the product promises about identity, bytes, readiness and deletion.

---

## 2. Scope, invariants and evidence limits

| Area | Executed choice |
| --- | --- |
| Upload owner | Trusted lesson credential maps to tenant and subject |
| Create replay | Stable tenant/owner/operation key; exact name/size/SHA-256 intent |
| Accepted input | Restricted `.txt` display name, declared text/plain, 1–1024 bytes |
| Upload capability | Custom HMAC bearer bound to PUT, file, owner/tenant, size, digest and fixed 10-second window |
| Stored bytes | Opaque generated key; complete immutable local object installation |
| Completion | Verify stored size/digest, atomically enter quarantine and create one job |
| Processing | Bounded text checks/summary; lease/token, maximum three claims |
| Publish | Current unexpired claim plus processing state; private derived artifact reference |
| Download | Owner/tenant authorization, ready state, checked original bytes, attachment/no-store/nosniff |
| Delete/cleanup | Tombstone first; fence work; collect private unreferenced/dead objects under shared local authority |
| Exclusions | Cloud SDK, multipart protocol, browser CORS, production auth/TLS, real malware detection, arbitrary parsers, distributed storage/locking and benchmark |

The invariants are concrete:

- A retry cannot silently change an accepted create intent or renew its upload deadline.
- A capability for one upload cannot write another object or authorize a download.
- The bytes accepted for completion cannot be replaced by a legitimate late PUT.
- Quarantine and its durable job commit together; repeated completion creates no second job.
- A stale worker cannot publish after reclaim, lease expiry or deletion.
- Unprocessed, rejected, expired and deleted files are unavailable for new downloads.
- Cleanup cannot delete another filesystem area or race a legitimate local publish into a dangling reference.

The last guarantee depends on every legitimate local writer and collector using the same SQLite write authority. A direct cloud PUT does not acquire that lock. The chapter explains the different cloud protocol instead of extending the local guarantee by analogy.

---

## 3. Estimate bytes, jobs, egress and abandoned work

Assume 10,000 uploads/day, mean size 2 MiB and 30 days of retained originals. This hypothetical product workload is deliberately larger than the fixture's 1 KiB input limit. The prototype is a mechanism test, not a load simulator.

{{ESTIMATES_CODE}}

Calculated output:

{{ESTIMATES_OUTPUT}}

The inputs yield about 585.938 GiB of original objects and 146.484 GiB of derived data at the assumed 25% output ratio. They exclude version history, replication, indexes, backups, quarantined/rejected retention and temporary processing files. Define whether a vendor's quoted storage/egress units are decimal GB or binary GiB before comparing costs.

Average incoming bandwidth is about 0.231 MiB/second; a selected 10× peak is about 1.157 uploads/second. Mean size hides a tail of large objects and bursty concurrent transfers. At two assumed CPU-seconds/job, mean processing demand is about 0.231 fully utilized cores, before peak, headroom and parser resource limits.

Five full downloads per upload imply about 97.656 GiB/day of payload egress. A design optimized only for ingest can still be dominated by download cost and authorization/cache behavior.

1,000 abandoned sessions with four 8 MiB parts each retain 31.25 GiB for one day's unfinished uploads. This is a planning example, not an S3 minimum/maximum part-size statement. Unfinished parts, staging objects and failed derived artifacts belong in the storage budget.

---

## 4. Control plane, data plane and multipart decisions

| Path | What happens | Main tradeoff |
| --- | --- | --- |
| API-proxied upload | Application authorizes and streams bytes to storage | Central control; application bandwidth/concurrency/backpressure cost |
| Direct upload | Application creates scoped permission; client sends bytes to storage | Removes large transfer from API; separate completion/version/abuse boundary |
| Multipart/resumable | Client uploads identified parts and completes a manifest | Retry only failed pieces; session/part/abort/expiry complexity |

The local HTTP fixture separates metadata endpoints from a capability-authorized object PUT, but both are served by one local process and bytes pass through it. It demonstrates the logical boundary, not bandwidth offload to a separate storage service.

S3 presigned URLs are time-limited bearer permissions based on the signing principal. They can be reused until expiry, and an upload to an existing key can replace that key's current data. Therefore “presigned” must not be treated as automatically single-use or immutable. [AWS presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

For a cloud immutable design, use unique server-generated keys and an appropriate conditional-write/version protocol, then pin the actual accepted object identity for processing. AWS documents conditional writes using preconditions; test their interaction with the exact upload and signing API you deploy. [AWS conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html).

Multipart design has three conceptual stages: initiate an owned session, upload/retry identified parts, then complete with the required part manifest. Persist enough information to resume safely and abort abandoned sessions. The assembled object's ETag is not necessarily the whole-file MD5. Do not use an ETag as a universal SHA-256 or malware verdict. [AWS multipart overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html).

Client-side “100% uploaded” is not the same as application completion. Reconcile a lost completion response against authoritative storage/session state rather than blindly creating another logical file.

---

## 5. HTTP API and ownership contract

| Executed endpoint | Credential/meaning | Selected responses |
| --- | --- | --- |
| `POST /api/files` | Lesson bearer plus Idempotency-Key and name/size/sha256/mime | 201 new/replay; changed intent 409; invalid input 400 |
| `PUT /objects/:id` | X-Lesson-Upload capability, exact body, text/plain; no owner bearer required | 201 first write, 200 same-byte retry; 403 bad grant, 422 size/digest mismatch |
| `POST /api/files/:id/complete` | Authenticated owner; verify stored object and schedule | 202 with current accepted state; 409 missing/terminal; 410 expired/deleted |
| `GET /api/files/:id` | Owner status/reason | 200; unknown/other owner or tenant 404 |
| `GET /api/files/:id/download` | Owner and ready state | 200 bytes; 409 not ready; 410 gone; 503 missing/corrupt ready object |
| `DELETE /api/files/:id` | Owner tombstone and cancel job ownership | 200, including repeated delete |

The create response carries ID, fixed expiry, upload path and capability. It is no-store. Equivalent replay returns the original grant/deadline even after expiration; it does not reactivate a dead upload. A new upload needs new explicit intent.

The path ID is an identifier, not proof of authority. Owner APIs scope by tenant plus subject. The upload grant intentionally acts as a bearer: possession can authorize its one bounded upload while valid. It cannot authorize metadata inspection, completion, deletion or download.

These public lesson tokens are a deterministic identity fixture. Production authentication, authorization verification, rate limiting, tenant byte reservations and safe credential distribution remain separate required engineering work; they are not implemented by the token dictionary.

---

## 6. Metadata model and smallest architecture

| Metadata | Purpose |
| --- | --- |
| File ID, tenant, owner | Identity and access scope |
| Operation key and unique scoped constraint | Original-intent replay under retries |
| Display name, expected size/SHA-256, expiry | Accepted upload contract |
| State, reason and result key | Authoritative visibility and selected processing output |
| Job state, attempts, token, lease deadline | Durable execution ownership and bounded recovery |

```mermaid
flowchart LR
    Client[Authenticated learner] --> Control[Create complete status delete]
    Control --> Metadata[(Metadata and jobs)]
    Client -->|scoped PUT capability| Transfer[Upload boundary]
    Transfer --> Raw[(Private immutable originals)]
    Metadata --> Worker[Claim and inspect pinned bytes]
    Raw --> Worker
    Worker --> Derived[(Private derived artifacts)]
    Worker -->|guarded publication| Metadata
    Client --> Download[Authorized ready-only download]
    Metadata --> Download
    Raw --> Download
    Metadata --> Collector[Reconciliation and cleanup]
```

The primary metadata key finds a file; a unique tenant/owner/operation key decides create replay. The expiry index supports unfinished-upload cleanup. One job per file is enforced by its primary key. This lesson's files are immutable: replacing content creates a new file ID. A mutable product needs a version/generation key carried through storage, job, output and publication.

A job row in the same transaction as quarantine avoids an “accepted completion but no processing work” gap. No broker or cache is required to demonstrate this baseline. A later broker needs an outbox/relay or a DB-backed recovery scanner and idempotent worker handling.

---

## 7. Immutable local objects and safe storage keys

`objects.py` creates a complete staging file, flushes it and installs it by a create-only hard link. It does not overwrite an existing object. The local filesystem must support that primitive; the recorded Windows run did. This is not a cloud consistency or power-loss guarantee.

{{OBJECTS_CODE}}

User display names never become disk paths. Raw keys are generated 32-character hex IDs; derived keys include file ID and claim token. Storage is private and outside the web application content tree. Cleanup resolves each candidate and checks its exact owned parent before unlinking it; a sentinel outside those areas remains untouched in verification.

The staging name is private and not a readable object key. Readers see a fully installed target rather than partially written final bytes. Same-byte retries are harmless; a conflicting immutable insert raises instead of replacing validated content. This fixture assumes no hostile local process/reparse-point manipulation of its owned temporary root.

Local fsync plus a database commit is not a distributed transaction across bytes and metadata. A later metadata failure can leave an object behind. The recovery path intentionally collects such unreferenced objects rather than pretending the two stores commit atomically.

---

## 8. Capability, completion and publication implementation

The complete metadata authority is below. All legitimate local object installation, publication and inventory cleanup acquire its SQLite write transaction.

{{UPLOADS_CODE}}

The custom grant is an HMAC of the fixed upload contract with an explicit PUT context. Verification compares it with the grant derived from authoritative metadata. The API does not parse a client-selected disk key, accept a renewed deadline or trust a client completion statement instead of checking the object.

`BEGIN IMMEDIATE` serializes local writers for the whole database file. That makes the cleanup/publication boundary clear and limits throughput; it is not row-level locking or a protocol implemented by direct S3 uploads. A production remote-store version must avoid treating long network I/O under a database write lock as a scalable design.

The 128-row metadata cap includes tombstones/replay identity. It rejects new work instead of silently forgetting old intent; original replay still works. This is a finite teaching resource bound, not production retention or a per-tenant storage quota.

---

## 9. Completion trace and idempotent recovery

**Trace:** authenticate owner → find accepted upload → verify deadline/state → read the immutable original → compare actual size/SHA-256 → atomically set quarantine and insert the unique job → acknowledge scheduling. A repeated completion sees the existing accepted state and creates no extra job.

Observed intake evidence:

{{INTAKE_OUTPUT}}

The suite calls complete before bytes exist, forces wrong-body and wrong-target uploads, retries accepted bytes, closes/reopens metadata and retries completion. It injects job insertion failure to verify the quarantine transition rolls back while already uploaded bytes remain available for a legitimate completion retry.

A client-provided digest helps bind the intended bytes and detect transfer/replacement mismatches; it is not a trust verdict on content. An attacker can declare the digest of malicious bytes correctly. Production checksum verification also needs the right storage checksum algorithm/type and exact object version. [AWS object integrity](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html).

If a completion callback is missing, a reconciler can inspect expired/pending session state and the authoritative object/session rather than relying only on the browser. It must still use the same idempotent completion/job boundary. Object notifications can be duplicated or arrive out of order; use them as recoverable signals, not unchecked commands to make any matching key ready. [AWS event notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html).

---

## 10. Quarantine, leased processing and guarded publication

```text
uploading --verified completion + job--> quarantined
quarantined --claim--> processing
processing --current accepted result--> ready
processing --current content rejection--> rejected
processing --third expired claim--> failed
uploading --expired sweep--> expired
any owned state --delete--> deleted
```

`ready` means this fixture's text policy completed and its artifact was published. `rejected` means a deterministic content-policy result; `failed` means the attempt budget exhausted. A job can complete successfully with a rejected file: worker execution success and file approval are distinct.

The worker reads bounded original bytes, verifies size/hash again, decodes strict UTF-8 and rejects NUL or a lesson marker. It derives a small character/line summary. No PDF parsing, OCR, image decode, antivirus engine or sandbox has been executed. Never label this result “virus free.”

Before publication, the authority requires the file still be processing, the token still current and its lease unexpired. A reclaimed worker has a new token. Derived objects include that token in their key so independent attempts cannot overwrite another result.

Observed processing and rollback evidence:

{{PROCESSING_OUTPUT}}

The injected ready-state update failure occurs after the artifact file was installed. Metadata rolls back, leaving processing plus an orphan artifact. Cleanup removes that artifact while keeping the active original. The same still-valid claim can recreate its artifact and publish. The suite therefore exercises the bytes/metadata gap directly.

A three-claim budget includes crashes before work finishes. Polling after the third expired claim marks failed; there is no automatic infinite loop, lease renewal, timed retry backoff, manual reprocess API or worker supervisor. Those mechanisms need an explicit product/operations policy if added.

---

## 11. Real HTTP boundary and private downloads

{{HTTP_API_CODE}}

Observed local HTTP contract:

{{HTTP_CONTRACT_OUTPUT}}

The HTTP tests actually upload bytes, race PUT/completion, run a processing claim and fetch the original. They verify authentication/tenant scope, upload-grant scope, framing/declared size, checksum, quarantine, attachment/no-store/nosniff and deletion. No external object or provider is contacted.

The download handler rechecks authority and the original bytes. A ready row with a missing/corrupt source returns 503 rather than a fabricated empty success. That mismatch needs telemetry and repair policy. An already authorized response can still be in flight when deletion commits; no protocol can retract bytes already delivered to a client.

The fixed attachment filename avoids putting untrusted display text directly into Content-Disposition. The lesson serves UTF-8 text with no-store and nosniff. Broader formats require deliberate content type, filename encoding, active-content/origin policy and authorization for originals as well as previews/derived artifacts.

This small loopback server is not hardened against hostile slow clients. Its bounded declared-length reader does not implement streaming multipart, resumable upload or a hard total request deadline. Browser CORS and production TLS/auth are also absent.

---

## 12. Delete, expiry and orphan cleanup

**Delete trace:** authenticate owner → commit tombstone and cancel claim token → deny new download/complete/PUT → sweep bytes later. Physical deletion is idempotent and can retry. Tombstones/replay state prevent old capabilities or worker results from becoming new active files.

**Unfinished-upload expiry:** at the fixed deadline, a new PUT/first completion is too late. The sweeper marks uploading rows expired and removes their bytes. A completed file can continue processing beyond that upload deadline: transfer permission expiry is different from file-retention expiry.

Observed lifecycle evidence:

{{LIFECYCLE_OUTPUT}}

The collector computes a live reference set while holding the same write authority used for local object installation and metadata publication. Raw objects referenced by non-dead metadata stay; only ready-selected derived objects stay. Unreferenced staging/results, metadata-free objects and deleted/expired objects are removable inside the checked private areas.

This full inventory under a global write lock is deliberately simple and expensive. A production inventory/lifecycle job needs bounded batches, grace periods, generation/version checks, ownership and retry progress. A recent unreferenced object may still belong to an in-flight remote upload or result, so “not referenced right now” is not by itself permission to delete it.

Direct cloud PUTs may arrive after an application tombstone because their storage permission remains valid. Do not publish them, and reconcile their exact versions later with a grace/expiry policy. The local PUT handler rechecks metadata on every request; that stronger local behavior is not automatic revocation of an already issued S3 grant.

Multipart sessions need their own abort/reconciliation path. A lifecycle rule for incomplete multipart uploads addresses unfinished parts, which are different from completed orphan objects or old object versions. [AWS incomplete-upload lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpu-abort-incomplete-mpu-lifecycle-config.html).

---

## 13. Concurrent calls and the overwrite/delete races

Observed concurrency:

{{CONCURRENCY_OUTPUT}}

Two actual HTTP PUT calls install once and replay once. Two completion calls both acknowledge the same accepted file while only one job exists. Two independent thread-owned connections then compete for that job; only one gets a live claim. No winner order is assumed.

The overwrite race is prevented by both immutable storage and state checks: an accepted target is never replaced, and completed state rejects further legitimate PUTs. A mutable object key without version binding would let processing validate one set of bytes and a later download serve another.

The stale-worker/delete race is prevented at publication: a worker computes outside the transaction, then must prove current ownership and processing state before creating a selected artifact/reference. Deletion clears that ownership. A stale result is discarded rather than changing deleted metadata back to ready.

For S3 versioning, distinguish key from version ID. Versioning can preserve distinct versions; it does not itself select which version your application validated, authorize access or define deletion of retained history. Store and use the chosen immutable identity consistently. [AWS versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html).

---

## 14. Failure matrix and cloud/multipart recovery

| Failure window | Local outcome | Recovery / cloud question |
| --- | --- | --- |
| Create commits; response lost | Same scoped operation replays ID/deadline | Do not create untracked sessions on every retry |
| Bytes arrive; complete never called | Uploading row/object remains until expiry sweep | Reconcile actual object/session; decide whether to complete or abort |
| Complete job insert fails | State rolls back; original remains | Retry one atomic state/job boundary |
| Worker expires/crashes | Current token invalid; bounded reclaim | Lease/attempt policy and duplicate processing |
| Artifact installed; metadata commit fails | Unreferenced artifact remains | Inventory/grace/version reconciliation |
| Delete commits; old worker finishes | Publication fenced | Tombstone/generation applies to every output |
| Ready original disappears externally | Download 503 | Alert, repair/reprocess/restore or mark unavailable |
| Old cloud grant writes after delete | Not executed here | Keep invisible, collect late version safely; do not assume DB revocation |
| Multipart completion response lost | Not executed here | Check owned upload/session and final exact object; repeat supported operation safely |

For a real multipart service, bind session ownership, object key, allowed size/checksum policy and expiry at initiation. Persist upload ID and the intended part/manifest contract; do not accept another user's upload ID because the client can name it. Validate final assembled object/version, then schedule work once. Resume/abort and retries need the actual provider API's documented behavior.

Events or callbacks are delivery mechanisms, not source-of-truth ownership. A duplicate “object created” notification should find the same accepted generation/job. A stale notification for a replaced/deleted generation must not resurrect it. Reconciliation should be safe to rerun and visible in metrics.

No transaction spans an arbitrary remote object store, SQL database and parser process. Prefer recoverable states and idempotent transitions; enumerate the orphan/missing-reference windows instead of drawing one fictional all-or-nothing box.

---

## 15. Security, quotas and processing isolation

| Boundary | Design question |
| --- | --- |
| Create authority | Who owns the file, may choose its namespace and reserve byte quota? |
| Transfer permission | Which method/key/size/checksum/window is granted, and who may possess the bearer? |
| Content handling | Which formats are allowed and which parsers/scanners run under resource limits? |
| Storage permissions | Are originals/quarantine/derived data private and inaccessible through guessed URLs? |
| Download | Does the current caller have access to this exact ready version? |
| Deletion | Are metadata, versions, previews, indexes, backups and cached grants covered by the stated policy? |

OWASP recommends a layered upload boundary: authorized users, constrained names/types/size, generated storage names, private storage and appropriate scanning/sandboxing. A claimed MIME type or extension can be spoofed; neither alone establishes safe content. [OWASP upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

For arbitrary PDFs, images, office files or archives, treat parser execution as untrusted work. Define time, memory, CPU, page/pixel/member/decompressed-size and output limits, restrict network/filesystem privileges, patch dependencies and isolate failures. A compressed transfer size does not bound expanded work. This paragraph is an architectural requirement, not a feature implemented by the text processor.

Use per-tenant reserved/committed byte accounting when granting uploads, with expiration/reconciliation to release abandoned reservations. Add admission/concurrency budgets for upload bytes, processing CPU and downloads. A global row cap does not make a fair tenant storage quota.

Do not log upload grants, private file contents or signed download URLs. Browser CORS permits selected origins/methods/headers; it is not a substitute for storage authorization. Public content requires abuse reporting/moderation and a deliberate serving policy beyond this private-note lesson.

---

## 16. Growth stages and useful operations evidence

| Trigger | Change to justify | Contract/measurement to retain |
| --- | --- | --- |
| Small private text service | API + metadata + private object boundary | Exact accepted bytes, readiness and owner access |
| Large transfer volume | Direct object-store upload | Scoped grant, fixed identity, completion and orphan policy |
| Unreliable large uploads | Multipart/resumable protocol | Session ownership, part integrity, idempotent completion and abort |
| Slow/risky processing | Isolated worker pools by format/cost | Resource bounds, versions, fenced publication and backlog recovery |
| Many processing stages | Versioned DAG/jobs and durable transitions | Stage inputs/outputs, retry identity and deleted-generation handling |
| High download volume | Authorized CDN/signed access where appropriate | Permission freshness, short expiry, revocation/cache limits and egress cost |
| Large inventories | Batched lifecycle/reconciliation | Never delete active generations; measure orphan lag and failed cleanup |

Measure create/byte-transfer/completion success separately, upload age, checksum mismatch, quarantine age, processing queue age, attempts, lease expiry/stale publish, rejected/failed reasons, ready-but-missing objects, orphan count/bytes, cleanup delay and tenant reserved-versus-actual usage. Storage byte-hours and download egress are different cost signals.

Keep metric labels bounded by format/stage/outcome, not file ID or full filename. Put scoped correlation IDs in controlled logs/traces. Reconciliation metrics should distinguish a missing object from a duplicate event or a deleted generation.

Define an observable readiness objective, such as time from verified completion to ready/rejected under stated load and format assumptions. Do not describe a hypothetical peak calculation as achieved throughput. The 121 local assertions demonstrate mechanisms, not a production SLO.

---

## 17. Reproduce and interpret the verification

From the repository root:

```powershell
cd examples/system-design/module-8-file-upload-processing
python verify.py
python author.py
python integrate.py
python validate_site.py
```

Recorded runtime: **Python {{PYTHON}}**, **SQLite {{SQLITE}}**, **{{OS}}**, on **{{DATE}}**. **{{TOTAL}} local checks passed**: {{COUNTS}}. Six competing calls cover two PUTs, two completions and two processing claims. File contents, SQLite constraints and real loopback HTTP are exercised directly.

`verification-results.json` records each named assertion. This chapter embeds four exact source files and six exact calculated/observed outputs. `content-validation.json` checks structure and fidelity; `validation-summary.json` records the full site build, routes/search and cleanup.

The harness verifies its absolute temporary root before removal, refuses deletion outside private object areas, closes all owned connections/listeners, joins server/handler/worker threads and removes session data. Port 3000 and Docker remain stopped. No persistent service, cloud upload, malware-scanning claim, power-loss test or capacity benchmark is included.

---

## 18. Interview question bank with answer direction

### Q1. Why separate file metadata from object bytes?

Metadata owns permissions, identity and lifecycle; object storage owns potentially large immutable byte versions. They have different access/cost characteristics and do not share one arbitrary distributed transaction. Design recovery for mismatches explicitly.

### Q2. When should bytes pass through the API?

When centralized transfer control is useful and bandwidth/concurrency cost fits. Direct upload offloads the large transfer but adds a scoped storage permission and completion boundary. Neither path removes content validation or download authorization.

### Q3. Does a presigned upload URL mean one-time upload?

No. Its documented permission lifetime and storage write semantics matter. Design unique/versioned targets, appropriate preconditions and completion verification rather than treating a signature as automatic immutability.

### Q4. What should an upload grant bind?

The intended method, server-chosen target, lifetime and relevant integrity/size policy, with a trusted owner/tenant association in application state. The exact enforceable fields depend on the provider API. Keep the grant out of logs and unrelated access paths.

### Q5. What happens if the create response is lost?

Retry with the same scoped operation key and equivalent intent. Return the original ID/deadline instead of creating another abandoned object/session. Changed intent conflicts; old replay should not renew an expired permission silently.

### Q6. Why not use the user's filename as the storage key?

It can collide, carry path/header ambiguity and expose private information. Use opaque server identity and keep a bounded display name separately. Safe output encoding and download headers remain necessary even for metadata names.

### Q7. Is Content-Type sufficient to validate a file?

No. It is a caller claim. Match allowed formats and actual content behavior using appropriate bounded validation/processing. The text fixture checks UTF-8 and a limited policy; it does not establish general malware safety.

### Q8. Does a matching SHA-256 prove the file is safe?

It establishes byte identity/integrity under the chosen protocol, not benign meaning. A malicious producer can supply the correct digest of malicious content. Safety policy and parser isolation are separate.

### Q9. Why is multipart upload useful?

It can retry individual failed pieces, resume and parallelize large transfers. It also creates session, part-manifest, completion and abort state. Choose it for requirements that justify that complexity and test the actual provider protocol.

### Q10. Can you assume an ETag is the whole-file checksum?

No. Its meaning depends on the storage/upload implementation; multipart ETags are not necessarily whole-file MD5. Use the documented checksum algorithm/type and exact object identity required by your integrity contract.

### Q11. What does the completion endpoint verify?

Owner/session scope, state/deadline and the actual final object's size/integrity/version. It then atomically records accepted completion and durable processing intent. A browser's success message is not enough.

### Q12. What if completion is called twice concurrently?

The authority checks current state and a unique job identity inside a transaction. One transition schedules the job; the other returns the existing accepted state. The real HTTP race verifies one job without assuming which caller wins.

### Q13. What if job creation fails after setting quarantine?

Keep the state transition and job insertion in one local transaction so both roll back. Uploaded bytes can remain for retry. If a separate broker is involved, use an outbox/relay or reconciliation rather than an unchecked dual write.

### Q14. Why quarantine instead of immediately making uploads public?

Transfer success does not mean validation/processing succeeded. Private quarantine keeps unapproved content unavailable while work completes. Define ready/rejected/failed separately and enforce access at every original/preview/download path.

### Q15. What if the object changes while a worker processes it?

Pin an immutable version or use a conditional/version protocol consistently. Otherwise validation can apply to one byte sequence while downloads expose another. The fixture's create-only object and post-completion write denial demonstrate one local solution.

### Q16. How do worker leases and tokens prevent stale publication?

Each claim gets current ownership and a deadline. Publication compares file state, token and expiry before selecting an output. Reclaim or delete invalidates the old owner; the old worker may compute, but it cannot make that result visible.

### Q17. What happens when a worker crashes repeatedly?

Expired claims can be reclaimed with a new token until the chosen attempt budget ends. The fixture counts three durable claims, then marks failed on a recovery poll. A production system needs reason history, alerts and controlled reprocess policy.

### Q18. Is writing an artifact and updating SQL atomic?

Not as one filesystem/database transaction. A failed metadata commit can leave an unreferenced artifact. Use immutable output identities, guarded references and safe reconciliation; the fixture injects this exact failure and recovers.

### Q19. How does delete avoid a worker resurrecting a file?

Commit a tombstone and invalidate execution ownership before collecting bytes. Publication must check that authoritative generation/state. A late result must not transition deleted metadata back to ready.

### Q20. Can deleting metadata revoke an issued cloud PUT immediately?

Do not assume so. Storage permission and application state are separate. Keep late objects invisible and reconcile them under the grant/version/lifecycle policy. The local handler rechecks metadata on each PUT, which is a stronger explicit local boundary.

### Q21. Which data should an orphan collector delete?

Only objects/versions proven outside live, in-flight and retained references under a safe protocol. Use ownership, grace and generation checks as needed. A present-time missing reference is not sufficient if publication can race the collector.

### Q22. What is the difference between unfinished parts and an orphan object?

Unfinished multipart parts belong to an uncompleted storage session; a completed orphan object has no selected application reference. They need different inventory/abort/delete operations, and version history can add another retention category.

### Q23. Does upload-token expiry mean ready files expire too?

No. Transfer permission lifetime, unfinished-session expiry and file retention are different policies. A completed file can still process after its transfer window. State which deadline applies at each operation.

### Q24. What should a download endpoint check?

Current caller/tenant access, exact selected file/version and readiness, then a deliberate serving policy. The fixture returns attachment/no-store/nosniff and verifies the original bytes; other content/CDN paths must enforce equivalent permissions.

### Q25. What if SQL says ready but storage has no object?

Treat it as an availability/integrity mismatch, alert and reconcile under a stated repair/restore policy. Do not return an empty successful file. The fixture returns 503 and leaves the inconsistency observable.

### Q26. How do you process hostile archives or documents safely?

Define accepted formats and bounded compute/decompression/output, isolate parser privileges/network, maintain dependencies and use suitable scanning/sandboxing. A small extension/MIME check or this lesson's marker rejection cannot substitute for those controls.

### Q27. How do tenant quotas work with abandoned uploads?

Reserve allowed bytes/slots when granting permission, then reconcile committed usage and release abandoned reservations safely. Bound processing and download work separately. A global metadata row cap is neither fair allocation nor full storage accounting.

### Q28. What does a CDN change for private downloads?

It can reduce origin/egress pressure, but authorization/cache-key design, signed access lifetime, revocation and retained copies must match the product promise. An already delivered/cached response cannot be recalled simply by deleting a database row.

### Q29. How do duplicate or stale object notifications affect processing?

Treat them as signals to reconcile the accepted exact generation. A unique job and state/version checks suppress duplicate intent and reject stale/deleted generations. Do not trust the order of callback arrival as business authority.

### Q30. What do the runnable examples prove and what remains unproven?

They verify local immutable files, SQLite transactions/replay/leases, bounded text handling, HTTP permissions and cleanup races for the tested cases. They do not prove S3/multipart semantics, malware safety, cloud failover, browser integration, power-loss durability or production capacity.

---

## 19. A 45-minute mock and answer skeleton

**Mock prompt:** “Design private document upload and asynchronous processing. Users retry completion, a worker crashes after writing output, and delete can race a late worker or upload.”

| Segment | Minutes |
| --- | --- |
| Clarify formats, privacy, size and lifecycle | 5 |
| Estimate transfer, storage, processing and abandoned work | 7 |
| Specify identity, APIs, state and exact object version | 8 |
| Trace grant, upload, completion, quarantine and publish | 10 |
| Inject lost callback, stale worker, deletion and orphan cleanup | 10 |
| Justify growth, security and evidence limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I would create an owner-scoped upload intent with a stable retry key, fixed transfer window and server-generated immutable object identity. Transfer success alone does not make the file available: completion checks the actual accepted object and atomically schedules processing. Workers inspect pinned bytes privately, then publish only while their claim and file generation are current. Download checks owner and readiness. Delete tombstones first so late work cannot resurrect it; immutable orphan outputs and abandoned sessions are collected through a recoverable, race-aware protocol. Direct cloud uploads, multipart sessions and arbitrary document parsers each add their own authorization and failure boundaries, which I would test on the actual implementation.

Use bank Q28/Q42 to probe completion/job atomicity, pinned byte identity and safe cleanup. Explain why a signed URL, successful upload callback, ETag or antivirus label alone cannot establish the whole lifecycle contract.

---

## 20. Practice tasks

1. Clarify a private resume-PDF service versus public photo sharing. Identify changed formats, permissions, scanning/serving policy, retention and abuse handling without claiming the text fixture implements them.
2. Recompute raw/derived storage, download egress, processing demand and unfinished-part storage for another workload. Separate average/peak assumptions and logical estimates from measured capacity.
3. Inspect the create replay and upload grant. Attempt changed intent, another target, wrong size/digest and an expired replay; explain which authority rejects each.
4. Run actual upload/completion races and inspect the one durable job. Inject job insertion failure and trace why bytes remain while quarantine rolls back.
5. Follow a file through quarantine, processing, ready and rejected. Explain the deterministic text policy and which malware/parser safety claims it cannot establish.
6. Reclaim at lease equality and attempt stale publication. Delete after processing computes a result and prove the old worker cannot publish or recreate the source.
7. Inject a ready-state metadata failure after artifact installation. Inspect the orphan, collect it and safely retry publication without a dangling ready reference.
8. Inspect owner-only HTTP download headers and error states. Remove a ready source deliberately, explain 503/reconciliation, and distinguish new-request revocation from bytes already in flight.
9. Design a real direct/multipart extension: session ownership, manifest/checksum/version, completion recovery, late writes, abort and separate part/orphan cleanup. Mark every unexecuted cloud mechanism.
10. Complete the 45-minute mock. Add tenant reservations, a risky parser pool or private CDN, justify its consistency/security boundaries and state required implementation tests.

---

## 21. Completion checklist

- [ ] I can clarify formats, privacy, size and lifecycle requirements.
- [ ] I can estimate bytes, jobs, egress and abandoned storage with units.
- [ ] I can distinguish control/data paths and multipart complexity.
- [ ] I can explain owner scope and bounded upload capability.
- [ ] I can trace create replay without extending the deadline.
- [ ] I can explain immutable bytes, checksums and pinned versions.
- [ ] I can reproduce idempotent completion and atomic job creation.
- [ ] I can explain quarantine and the limits of content validation.
- [ ] I can fence stale/expired/deleted worker publication.
- [ ] I can reconcile orphan artifacts and abandoned uploads safely.
- [ ] I can enforce ready-only private download and explicit delete semantics.
- [ ] I can finish the mock and state the local evidence limits.

---

## 22. Research references and continuation

Primary sources reviewed on {{DATE}}. Code, workloads, counterexamples and Q&As are authored material. Cloud API behavior is source-specific; the local capability/object protocol does not emulate S3. No measured interview-frequency ranking is asserted.

| Primary source | Mechanism to verify |
| --- | --- |
| [AWS presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html) | Bearer access, lifetime and repeat-write behavior |
| [AWS conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html) | Storage-side overwrite preconditions |
| [AWS multipart overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html) | Parts, final manifest and ETag caveat |
| [AWS object integrity](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html) | Explicit checksum/integrity mechanism |
| [AWS notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html) | Duplicate/order boundaries for storage events |
| [AWS versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html) | Key versus object version |
| [AWS incomplete multipart lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpu-abort-incomplete-mpu-lifecycle-config.html) | Unfinished-part cleanup distinct from completed-object deletion |
| [OWASP upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Layered upload/content/storage boundary |

Return to the [architecture roadmap](/docs/system-design), [A3: workflows](/docs/system-design/reliable-workflows-concurrency), [A4: operations](/docs/system-design/secure-observable-operations) or [S2: notification delivery](/docs/system-design/notifications-webhooks). Resume [M8: API security](/docs/resume-skills/api-security-authorization-multi-tenancy), [M15: background work](/docs/resume-skills/caching-background-jobs-data-ingestion), [M18: cloud fundamentals](/docs/resume-skills/aws-gcp-fundamentals) and [M23: document ingestion](/docs/resume-skills/rag-document-ingestion) provide stack refreshers.

**Next: [S4 — Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations)**, architecture part 11 / numeric module 9. It develops authoritative inventory, atomic holds, expiry, concurrent booking attempts and late-payment decisions with its own local SQLite/signed-HTTP scope. S4-S6 are also authored; remaining systems and architecture consolidation remain planned.
'''

for name,tag in [('estimates.py','ESTIMATES'),('objects.py','OBJECTS'),('uploads.py','UPLOADS'),('http_api.py','HTTP_API')]:
    chapter = chapter.replace('{{'+tag+'_CODE}}',code(name))
for name in outputs:
    chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}',output(name))
for tag,value in [('DATE',proof['verified_date']),('PYTHON',proof['python']),('SQLITE',proof['sqlite']),
    ('OS',proof['os']),('TOTAL',str(proof['total'])),
    ('COUNTS',', '.join(f"{n} {name.replace('_',' ')}" for name,n in proof['counts'].items()))]:
    chapter = chapter.replace('{{'+tag+'}}',value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-10-module-8-file-upload-processing.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
metadata = {'label':'S3','chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),
    'questions':30,'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':sources,
    'output_fidelity':outputs,'mock_minutes':45,'verified_checks':proof['total'],
    'next':'S4: Ticket booking and limited-inventory reservation'}
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
