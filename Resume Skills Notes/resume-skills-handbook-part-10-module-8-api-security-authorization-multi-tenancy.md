# Resume Skills Placement Handbook — Part 10
# Module 8: API Security, Authorization and Multi-Tenancy

**Module 8 · 4–5 hours · Tier 1 · Requires: M6-M7; DBMS fundamentals help**

---

## Why this module matters

M7 established who a credential represents. That identity is not permission to read every document, change any field or act in every organization.

A multi-tenant application can authenticate perfectly and still leak data through one unscoped query, cache key, download link or bulk operation. Security therefore belongs in the application/data boundaries, not only a login screen.

> **Every effect and every disclosure needs a decision about subject, action, resource and tenant, using trusted context at the point where it matters.**

This chapter builds a two-tenant document API and tests both permitted behavior and rejected attempts. It also explains injection, browser security, ingestion and operational controls with their distinct mechanisms.

**Verification:** **74 checks passed on Node.js v22.14.0 and jose 6.2.12**: 22 policy/input checks, 46 real HTTP checks and six SQL checks using **SQLite 3.47.2**.

The SQL group uses Node's experimental node:sqlite API on the recorded runtime. The expected warning is preserved in sql-verification-stderr.txt. The API itself uses an in-memory repository; SQL demonstrations are a separate isolated database.

### Run the examples

From the repository root:

```powershell
npm --prefix examples/resume-skills/module-8-api-security ci --ignore-scripts --no-audit --no-fund
node examples/resume-skills/module-8-api-security/verify.mjs
node examples/resume-skills/module-8-api-security/verify-policy.mjs
node examples/resume-skills/module-8-api-security/verify-http.mjs
node examples/resume-skills/module-8-api-security/verify-sql.mjs
```

Optional manual service:

```powershell
node examples/resume-skills/module-8-api-security/start.mjs
```

It binds **127.0.0.1:3108** and prints generated Alice/Dana fixture bearer credentials, valid for 300 seconds. Copy one into an Authorization header for manual requests, then stop the service with Ctrl+C.

```powershell
# Replace the placeholder with the generated local Alice fixture credential.
Invoke-RestMethod -Uri http://127.0.0.1:3108/tenants/alpha/documents -Headers @{Authorization='Bearer <paste-Alice-fixture-token>'}
```

Those tokens are public learning fixtures generated locally, not credentials for any external account. The verifier does not save generated tokens or private keys in result files.

The fixture issuer exercises real JWT verification under M7's trust model. It is not a provider login or a production identity server. Signing keys, memberships, documents and counters live in one process.

---

## 8.1 Security starts with assets and trust boundaries

Start a small design by naming what must be protected and who can influence each input.

| Asset/invariant | Example threat |
| --- | --- |
| Private document contents | Another authenticated member guesses the ID |
| Tenant isolation | A caller changes tenant path/header |
| Ownership and privileges | A caller submits ownerId or role |
| Integrity of state changes | Permission is revoked while an edit awaits |
| Server resources | Many expensive imports or oversized bodies |
| Credentials/internal data | Logs or responses expose secrets |
| Browser origin | Stored user content becomes executable script |

The interesting attacker is often a valid user with a valid token. Authentication failure tests alone do not address that case.

### Boundary map

```text
untrusted HTTP request
  -> supported route and bounded transport
  -> verified principal
  -> selected tenant + current membership
  -> token scope ceiling
  -> object/action/property policy
  -> scoped read or guarded effect
  -> selected public representation

separate boundaries:
  browser rendering
  database query construction
  file/parser/worker execution
  cache/object-storage access
  secrets and audit infrastructure
```

Each boundary changes what a value may safely mean. Parsing JSON establishes a JavaScript value. It does not turn that value into SQL syntax, a trusted identity, a safe file path or safe HTML.

**Interview line:** “I treat input as data, establish a trusted principal, and check tenant/object/action permissions before disclosure or mutation. I test denied operations for both response and state effects.”

---

## 8.2 Subject, action, resource and context

A useful policy decision has four parts:

```text
Can subject Alice
perform action update
on document alpha/1
under current membership, scope and document state?
```

The resource ID alone does not answer that question.

| Input | Trust treatment in this example |
| --- | --- |
| Authorization bearer credential | Verify signature, issuer, audience, type and lifetime |
| JWT subject/scope | Promote only after accepted verification |
| Tenant path segment | Candidate target; verify current membership |
| X-Tenant-Id, X-Role, X-User-Id | Do not use as authority |
| JWT role/tenant extras | Deliberately ignored by this application's policy |
| Document owner/visibility | Read from server-controlled state |
| Request title/visibility | Validate writable fields and property permission |

A signed claim is authentic under the key policy; that does not imply that every claim is authoritative for your application forever. This design deliberately loads current membership instead of trusting a possibly stale role claim.

Other architectures can use signed membership claims with an explicitly bounded freshness/revocation model. State that model rather than mixing current and stale sources accidentally.

### Deny by default

An unknown role, action, resource or missing membership must not fall into an allow branch. Default denial is especially important when new endpoints or roles are added.

Reference: [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

The example rejects an unexpected superuser role. The string sounds privileged, but no configured rule grants it access.

---

## 8.3 RBAC, attributes, relationships and scopes

**RBAC** groups permissions by roles such as viewer, editor and admin.

**Attribute-based policy** considers facts such as resource visibility, tenant, classification or workflow state.

**Relationship-based policy** considers relationships such as owner, project member or manager.

These ideas can be combined. A useful rule is often “an editor may update documents they own in a tenant where they are currently a member.”

A token **scope** is a capability ceiling for that credential. docs:write does not automatically turn a viewer into an administrator or identify which objects the user owns.

### Example policy

| Action | Viewer | Editor | Tenant admin |
| --- | --- | --- | --- |
| Read tenant-shared document | Yes | Yes | Yes |
| Read own private document | Yes | Yes | Yes |
| Read another member's private document | No | No | Yes |
| Create a document | No | Yes | Yes |
| Update/delete own document | No | Yes | Yes |
| Update/delete another member's document | No | No | Yes |
| Change visibility after creation | No | No | Yes |

Reads also require docs:read. Write operations require docs:write. For this selected API, a write operation's authorized response is part of that operation; it does not require a separate read scope.

Editors may choose initial visibility when creating a document; later visibility changes require tenant admin. That is a deliberate teaching policy for property permissions, not a universal product rule.

### Roles are tenant-scoped

| User | alpha membership | beta membership |
| --- | --- | --- |
| Alice | editor | None |
| Bob | viewer | None |
| Carol | None | admin |
| Dana | viewer | admin |

Dana being an admin in beta does not make Dana an admin in alpha. A global isAdmin flag loses that distinction.

Ownership is not enough by itself either: Bob owns alpha/2 but remains a viewer, so cannot edit it. Conversely, a tenant admin can manage other owners' documents within that tenant.

---

## 8.4 Object, function and property authorization

### Broken object-level authorization

An API accepts an object identifier but fails to verify the caller's permission on that specific object. Changing the identifier can expose or mutate someone else's resource.

UUIDs can make guessing harder, but known or leaked IDs still need authorization. The failure is the missing access decision, not merely predictable numbering.

Reference: [OWASP API1: Broken Object Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/).

The example deliberately reuses local IDs across tenants:

```text
alpha/1 -> Alice's private document
beta/1  -> Carol's tenant-shared document
```

A query/cache keyed only by id=1 can confuse those resources.

### Broken function-level authorization

A caller reaches an operation they are not allowed to use, such as a privileged export, moderation or management endpoint. Hiding the button or choosing an obscure URL is insufficient.

A route-level capability check may reject a viewer from creating documents, but that check does not replace object-level checks for later edits.

Reference: [OWASP API5: Broken Function Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa5-broken-function-level-authorization/).

### Broken property-level authorization

Even an allowed object operation can accept or expose forbidden properties.

Input risks include copying ownerId, tenantId, role, internalNote or price directly from a request. Output risks include serializing every database field.

The example allowlists title/visibility, assigns owner/tenant server-side and projects only id, title, ownerId, visibility and version. It also separately restricts visibility changes.

Reference: [OWASP API3: Broken Object Property Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/).

### 403 versus 404

This service conceals missing membership and unreadable/missing objects with 404. A visible object with an unauthorized action can produce 403. Missing authentication produces 401.

That is a selected disclosure policy. It is not proof that timing, counts, constraint errors or other endpoints reveal nothing about existence.

---

## 8.5 Multi-tenancy: select, verify and carry context

A tenant is an organizational/data boundary, such as a company using the same SaaS application. One person can belong to several tenants with different permissions.

### Tenant selection is not tenant authority

A path, subdomain, header or body field can select a candidate tenant. The server must establish that the verified subject is allowed to operate in it.

In the example:

```text
request /tenants/alpha/documents/1
  -> verify bearer subject
  -> look up membership(alpha, subject)
  -> resolve action scope
  -> load document under alpha + id
  -> check policy
```

Changing X-Tenant-Id to beta does not move the lookup. Changing the actual path to beta makes membership fail for Alice.

A request-wide context should remain local to that request. A mutable module-level currentTenant variable can be overwritten while another request awaits.

The verifier pauses Dana's alpha read, completes Dana's beta read and then resumes the alpha request. Each retains its own tenant and role.

### Where isolation must continue

| Data path | Required consideration |
| --- | --- |
| Single-object read/write | Scoped identity and object policy |
| Lists/search/counts | Filter visible rows before pagination/aggregation |
| Bulk operations | Authorize every selected object |
| Downloads/object storage | Recheck access before disclosure |
| Cache | Tenant-aware key and permission/freshness policy |
| Jobs/exports | Verified context, current policy and result authorization |
| Webhooks/integrations | Bind external account/event to the correct tenant |
| Vector/graph retrieval | Filter tenant/resource access before exposing retrieved content |
| Logs/backups/admin tools | Separate access and operational privileges |

The runnable API covers reads, lists/search, create/update, bulk deletion, download, cache and text import. Jobs, webhooks, object storage and AI retrieval are design extensions, not implemented services.

Reference: [OWASP multi-tenant security guidance](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html).

---

## 8.6 Data model and database defense

### Shared rows, schemas or databases?

| Strategy | Advantage | Cost/remaining responsibility |
| --- | --- | --- |
| Shared tables with tenant_id | Efficient shared operation | Every relevant path needs correct isolation |
| Separate schema per tenant | Namespace separation | Migrations/pooling/privilege management |
| Separate database per tenant | Stronger operational separation | Provisioning, migrations, cost and cross-tenant operations |
| Hybrid | Match isolation to tenant needs | More routing and operational complexity |

Physical separation does not replace user/resource permissions within one tenant. Shared rows can be appropriate when their constraints, policy and operation are designed carefully.

The in-memory example uses composite tenant/id keys and tenant-scoped membership maps. A future schema should preserve that identity deliberately.

### Composite relationships

If document IDs or project IDs are tenant-local, foreign keys must include the tenant dimension when enforcing tenant-local relationships.

The SQL fixture has projects(tenant_id,id) and documents(tenant_id,id,project_id). It rejects a document in alpha referring to beta's project ID, while retaining all four original rows.

That specific constraint was executed against SQLite. It is not evidence of a live PostgreSQL schema or RLS configuration.

### Scoped SQL shape

```sql
-- Proposed PostgreSQL read shape, not executed in this module.
SELECT id, title, owner_id, visibility, version
FROM documents
WHERE tenant_id = $1
  AND id = $2;
```

This is one necessary data-access bound. The application still needs current membership and object policy; selecting a tenant correctly does not automatically authorize every member to read a private object.

Likewise, parameterizing id without a tenant predicate can safely execute the wrong data-access policy. The SQLite test returns two rows for id=1 across tenants despite using a bound parameter.

### PostgreSQL row-level security

RLS can add database-side row policies as defense in depth. It needs careful runtime roles, policy coverage and connection context. Superusers/BYPASSRLS roles bypass it; table owners normally bypass it unless the appropriate FORCE behavior applies.

A privileged application connection can therefore defeat the isolation you expected. Test using the actual runtime role, not only the migration/admin account.

Reference: [PostgreSQL row-security documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).

If policies depend on transaction-local tenant context, set it from trusted application context and verify pooling/cleanup. A leftover connection-wide tenant setting can affect another request.

No PostgreSQL instance or RLS policy was exercised here. M13 will verify engine-specific behavior. Do not claim RLS makes application permissions unnecessary.

---

## 8.7 Lists, bulk effects, downloads and cache hits

### Filter before pagination

Bob cannot read alpha/1. For limit=1, his first page should contain alpha/2, not an empty page with continuation/count hints based on the hidden private row.

The service filters by tenant and read policy, then search/continuation, then ordering and slicing. It returns only visible continuation information.

The small implementation scans/sorts an in-memory collection. It is not an indexed-query performance result or a snapshot-consistent export.

### Bulk means many decisions

Checking the first object or the tenant once is not enough. A batch can combine one allowed ID with one forbidden or missing ID.

This example defines bulk deletion as all-or-nothing. It validates IDs, checks all objects, waits at the test seam, rechecks all objects and then removes them with no await between checks and effects.

A denied batch leaves all document rows unchanged. A durable implementation needs appropriate transaction/locking behavior; a process-local loop is not a distributed transaction.

### Downloads are data access

A separate download endpoint must apply the same object policy. Knowing a storage key or download URL is not automatically permission.

Signed object-storage URLs can intentionally delegate short-lived access, but a copied valid URL may remain usable until its expiry or another supported control. Define that lifetime and permission model.

The demo downloads text directly through the authorized API. It does not create object-storage signed URLs.

### Cache policy remains an authorization decision

The cache key includes tenant, local ID and resource version. Before every hit, the service reads current membership/object policy from the authoritative in-memory repository.

That permits a shared projection cache because the cached fields are identical for every authorized reader. A user-specific/redacted representation would also need the relevant subject/policy dimensions.

This cache does not avoid the authoritative lookup and is not a database-cache performance optimization. It illustrates isolation and freshness decisions.

Tests warm a private document under an authorized user and reject another viewer; they also downgrade/remove membership after warm-up and reject the later hit. Same local ID in another tenant returns the other tenant's correct document.

---

## 8.8 Permission changes and time-of-check/time-of-use

A permission check can become stale while a request waits:

```text
request verifies Alice's membership
request awaits external/database work
administrator removes Alice's membership
request resumes
```

If it blindly uses the old decision, the effect may occur after the removal.

The service rechecks current membership, object policy and edit precondition after its asynchronous test seam. It then commits synchronously in this one-process store.

The verifier pauses an update and a bulk deletion, removes membership, then releases them. Both receive 404 and leave documents unchanged.

### This is a local serialization guarantee

A JavaScript run-to-completion region prevents another callback from changing these Maps midway through the final synchronous checks/write. It does not coordinate other server processes or database transactions.

A database design must specify what concurrent revocation means. A single statement can check a consistent snapshot, but that alone does not prove immediate revocation ordering across concurrent commits.

Use an appropriate locking/transaction/version protocol, define the freshness/serialization contract and verify it against the real engine. Consider cache invalidation and retries too.

### Separate authorization and resource-version conditions

If-Match prevents a stale edit from overwriting a newer representation. It does not prove permission. A valid editor still needs ownership; an owner with an obsolete version still gets 412.

The demo requires the exact current quoted vN condition on PATCH. It implements this route-specific contract rather than a general HTTP entity-tag list/precondition engine.

---

## 8.9 Input validation, mass assignment and safe output

Validation should establish exact facts:

- The body is an allowed object.
- Only writable fields are present.
- Field types and bounds are correct.
- Server-owned identity/ownership fields come from trusted context.
- Property-specific policy permits the requested change.
- The output contains only approved public fields.

A generic ORM update(req.body) can bypass those boundaries even when the route itself requires authentication.

In the example, ownerId and tenantId never come from client input. The unknown-field check also rejects a __proto__ property parsed from JSON rather than copying it into arbitrary objects.

Do not infer that rejecting one prototype property solves every prototype-pollution mechanism. Avoid unsafe merges and validate schemas throughout the relevant data flow.

### Parsing and canonicalization

The JSON body is limited to 2048 bytes. Titles are trimmed and bounded to 80 JavaScript UTF-16 code units. Query keys are allowlisted and repeated values rejected.

Canonicalization belongs to the supported field's contract. Do not trim a password, rewrite a signed webhook body or decode a path repeatedly without understanding what the next boundary expects.

For responses, a deliberate projection is safer than serializing the whole repository row. The verifier confirms that content, storage metadata and internal operator notes do not appear in ordinary document JSON.

---

## 8.10 Injection: keep data separate from instructions

### SQL injection

A query built by concatenating user input can interpret that input as SQL structure. Bound values let the driver/database treat it as data.

The SQL fixture compares an intentionally unsafe query with a parameterized query in an isolated in-memory database. The unsafe query returns all four rows, including beta; the bound-value version returns no match.

```javascript
// Excerpt from the executed SQLite verifier; db is its in-memory DatabaseSync.
const payload = "' OR 1=1 --";
const rows = db.prepare(
  'SELECT tenant_id, id FROM documents WHERE tenant_id = ? AND title = ?'
).all('alpha', payload);
```

Parameterization does not add authorization or tenant predicates automatically. It also does not generally bind SQL identifiers such as a column name. For allowed dynamic sorts, map a supported API value to a fixed SQL fragment.

Reference: [OWASP SQL injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).

### NoSQL operator injection

If an API expects a scalar username but accepts an arbitrary object and passes it into a query, an operator-bearing object can change the query's meaning.

Validate exact shapes/types, construct queries from known fields and keep operators server-controlled. An ORM/ODM does not make unsafe dynamic query construction impossible.

No MongoDB engine is used here. M14 will verify Mongo-specific behavior.

### Command and option injection

Avoid concatenating user values into shell commands. A process API that passes an argument array without a shell prevents shell metacharacters from becoming shell syntax, but the invoked program can still interpret options, filenames or expressions dangerously.

Validate the operation, arguments and allowed paths; use end-of-options markers only where that program supports them. A safe argument boundary is not a permission decision.

Reference: [Node child-process API](https://nodejs.org/download/release/v22.14.0/docs/api/child_process.html).

This document API invokes no external process for uploaded content. The verification runner's child processes use fixed local test filenames.

---

## 8.11 XSS, CSRF and CORS address different boundaries

| Issue/control | Main boundary |
| --- | --- |
| XSS | Untrusted content becomes executable in an origin |
| CSRF | Browser automatically supplies credentials to an unwanted action |
| CORS | Browser permits/blocks cross-origin response access |
| API authorization | Server decides whether this subject may act on this resource |

### XSS: encode for the actual output context

Use framework escaping or a safe text API for ordinary text. Rich HTML needs an appropriate sanitizer and a deliberately supported HTML policy.

HTML text encoding is not a general JavaScript/CSS/URL sanitizer. A javascript: URL needs a scheme policy; escaping angle brackets does not make every destination safe.

Our utility demonstrates escaping HTML text metacharacters and the test checks the resulting string. The API itself returns JSON or authorized text attachments; it has no HTML preview UI.

```text
Input:
<script>alert("x")</script>&

Checked HTML-text result:
&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;&amp;
```

Those are data strings from the verified utility, not a browser execution test.

Reference: [OWASP XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

HttpOnly does not prevent injected same-origin script from performing permitted authenticated actions. CSP can add a restriction layer, but does not replace correct rendering/sanitization.

### CSRF: follow ambient credentials

M7 demonstrated a session-bound synchronizer token and exact Origin checks for cookie-authenticated mutations. SameSite and safe HTTP method design support that boundary.

For a signed double-submit design, bind the token appropriately to session context and validate it; simply accepting equal attacker-controlled cookie/body strings is not a complete anti-injection strategy.

XSS can often read/use a CSRF token or make legitimate-origin requests. CSRF controls are not XSS prevention.

Reference: [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

This M8 API accepts only explicit bearer headers and does not accept session cookies. It does not add a second cookie/CSRF implementation or claim to test browser CSRF behavior.

### CORS: a browser response-access policy

The adapter supports an exact configured origin allowlist. It does not reflect arbitrary origins, allow null or accept a hostname merely because it starts with the trusted hostname.

Preflight validates the requested route method and supported headers, and returns the appropriate origin/method/header policy. It requires no bearer credential because it returns policy metadata, not protected document data.

Actual requests still need authentication and tenant/object permissions. A valid allowed Origin without a token receives 401; an allowed Origin with Alice's token still cannot read beta.

No Access-Control-Allow-Credentials is emitted because this example is not a credentialed-cookie cross-origin API. The browser's rules for explicit authorization headers and credentialed requests still require a deliberate client/server configuration.

Reference: [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS).

### No-Origin callers still exist

The service permits a non-browser request without Origin, subject to bearer verification and full authorization. A non-browser caller can also forge an Origin header.

For a supplied disallowed Origin, this adapter additionally rejects the actual request before its effect. That is a server policy choice beyond merely omitting CORS response headers.

The tests inspect actual HTTP headers/status/state. They do not emulate a browser's enforcement of CORS, cookie or script policy.

---

## 8.12 Safe ingestion: bytes, names, storage and rendering

An upload feature crosses several boundaries:

```text
authenticated/authorized request
  -> size, format and encoding bounds
  -> narrow accepted content model
  -> server-controlled ownership/storage identity
  -> quarantine/parser/scan workflow when needed
  -> authorized retrieval
  -> safe rendering/download policy
```

A client filename and Content-Type are assertions, not proof that bytes are safe.

### This example accepts only small UTF-8 text

It requires text/plain with supported UTF-8 metadata, at most 1024 bytes, valid UTF-8 and no NUL byte. Its display-name allowlist accepts a narrow .txt form and rejects path separators, hidden-style names and other extensions.

The original filename is never used as a filesystem path. The repository records a random storageKey as internal metadata; no actual filesystem/object-storage file is written.

Imports assign the verified subject as owner and default to private. Viewer/nonmember requests fail before payload processing. Current permission is rechecked before the row is created.

### Text can contain markup without becoming HTML

A file named markup.txt may contain script-looking text. The demo preserves those bytes as text, serves them only after authorization, and uses text/plain, attachment disposition and nosniff.

This is a narrow text-serving contract, not malware detection or an HTML sanitizer. A later preview UI must still render as text or use an appropriate safe policy.

### Extending to PDFs, images or archives

Use format-aware validation and parsers, byte/expansion/page/time limits, isolated execution and safe storage. Extension and MIME checks alone are insufficient.

Compressed archives introduce decompressed-size limits and entry-path handling; PDFs/images introduce complex parser behavior. Consider quarantine/scanning and ownership transitions before making output accessible.

Reference: [OWASP file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

No archive/PDF parser, scanner or sandbox is deployed by this example.

### URL ingestion and SSRF

Fetching a user-supplied URL can make your server contact internal services or metadata endpoints. Use a narrow target/protocol policy, network egress controls, redirect policy and safe DNS/address handling.

A one-time hostname string check can be bypassed by redirects or changes in resolution. Do not present a simple prefix or private-IP regex as a complete SSRF defense.

Reference: [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

This API performs no user-directed network fetching. URL ingestion is a design extension for later document/RAG workflows.

---

## 8.13 Secrets, audit and resource limits

### Secrets have a lifecycle

Keep production credentials out of source, client bundles, public responses and logs. Use a supported secret-management mechanism, least-privilege identities, rotation and a revocation/recovery plan.

An environment variable is a delivery mechanism, not automatic protection from a compromised process or careless logging. Publicly exposed frontend configuration is not a place for signing keys/provider secrets.

Reference: [OWASP secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).

The fixture generates ephemeral signing keys. It does not load production secrets. Its optional launcher deliberately prints only generated public learning credentials for manual use.

### Audit decisions without copying credentials

The HTTP adapter records request ID, verified subject when available, selected tenant, action and result status. It does not log raw bearer headers, titles, file contents or internal notes.

The verifier checks correlation and confirms those sensitive values are absent from the recorded events.

The audit hook is best-effort and in-memory. Production audit delivery needs durability, access controls, retention and an explicit failure policy. A successful response here is not proof that an external audit sink durably accepted an event.

### Layer resource limits

The import route demonstrates a fixed-window attempt budget keyed by verified tenant and subject. It allows three attempts per ten-second window by default. The dedicated verifier selects a budget of two.

The budget is consumed after authorization but before payload validation, so malformed authorized import attempts can consume it. That protects work; it is different from charging a business quota only for successful imports.

Other useful layers include edge request-size/rate bounds, login abuse controls, per-tenant cost quotas, concurrent-work limits, parser deadlines and downstream timeouts.

Independent counters in different processes do not enforce one global policy. Shared counter coordination and store-failure behavior belong in a deployed limiter design.

This example has request/header timeouts and bounded payload allocation, but draining excessive bodies is not a bandwidth cap. It has no deployed edge limiter, parser worker pool or distributed counter.

---

## 8.14 Build the protected document service

### Request flow

```text
Bearer credential
  -> configured JOSE verification
  -> principal(subject, scopes)
  -> current tenant membership
  -> role + object/property rules
  -> scoped repository access
  -> selected public result

PATCH:
  validated input + initial permission check
  -> await test seam
  -> current permission + version check
  -> synchronous local update

Bulk delete:
  validate IDs + authorize all
  -> await test seam
  -> authorize all again
  -> remove all without yielding
```

The CORS adapter does not establish identity, and the repository's tenant predicate does not establish every resource permission. Each stage has a separate responsibility.

### Endpoint contract

| Endpoint | Required decision | Success |
| --- | --- | --- |
| GET /tenants/t/documents | Membership, read scope, per-row visibility | 200 bounded visible list |
| GET /tenants/t/documents/id | Membership, read scope, object policy | 200 public document + ETag |
| POST /tenants/t/documents | Membership, write scope, create role | 201 server-owned document |
| PATCH /tenants/t/documents/id | Write scope, object/action/property policy, exact If-Match | 200 updated document |
| POST /tenants/t/documents/bulk-delete | Write scope, every object's delete permission | 204 all removed |
| GET /tenants/t/documents/id/download | Read scope and object policy | 200 text attachment |
| POST /tenants/t/documents/import | Create permission, attempt budget, text contract | 201 private document |
| OPTIONS recognized route | Configured preflight policy | 204 metadata; no protected data |

List inputs are after, limit and q; limit is 1–5. This simple tenant-local continuation is not the general opaque cursor contract from M6. Every request is reauthorized.

Errors use compact JSON code/requestId in this example, with status-specific headers. That is its local error contract, not a replacement requirement for M6's Problem Details model.

### Complete source

The following five files are the authoritative teaching implementation. The verifier supplies controlled hooks to pause reads/commits; those hooks are not external HTTP capabilities.

#### security.mjs

```javascript
export class ApiError extends Error {
  constructor(status, code, headers = {}) {
    super(code); Object.assign(this, { status, code, headers });
  }
}
export const fail = (status, code, headers) => { throw new ApiError(status, code, headers); };
export const roles = new Set(['viewer', 'editor', 'admin']);
export function allowed(role, subject, action, row) {
  if (!roles.has(role)) return false;
  if (action === 'create') return role === 'editor' || role === 'admin';
  if (!row) return false;
  if (action === 'read') return role === 'admin' || row.visibility === 'tenant' || row.ownerId === subject;
  if (action === 'update' || action === 'delete')
    return role === 'admin' || (role === 'editor' && row.ownerId === subject);
  return false;
}
export function writable(input, partial = false) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail(400, 'invalid_document');
  const keys = Object.keys(input);
  if (keys.some(key => !['title', 'visibility'].includes(key))) fail(400, 'unknown_field');
  if (partial && !keys.length) fail(400, 'empty_patch');
  const result = {};
  if (!partial || Object.hasOwn(input, 'title')) {
    if (typeof input.title !== 'string' || !input.title.trim() || input.title.trim().length > 80)
      fail(400, 'invalid_title');
    result.title = input.title.trim();
  }
  if (Object.hasOwn(input, 'visibility')) {
    if (!['private', 'tenant'].includes(input.visibility)) fail(400, 'invalid_visibility');
    result.visibility = input.visibility;
  } else if (!partial) result.visibility = 'private';
  return result;
}
export function safeFilename(name) {
  if (typeof name !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,59}\.txt$/.test(name))
    fail(400, 'invalid_filename');
  return name;
}
export function textContent(bytes) {
  if (!(bytes instanceof Uint8Array)) fail(400, 'invalid_text');
  if (bytes.byteLength > 1024) fail(413, 'body_too_large');
  let text;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { fail(400, 'invalid_utf8'); }
  if (text.includes('\0')) fail(400, 'invalid_text');
  return text;
}
export function escapeHtmlText(value) {
  return value.replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}
export function createBudget({ now = Date.now, limit = 3, windowMs = 10_000 } = {}) {
  const buckets = new Map();
  return (tenant, subject) => {
    const time = now(), window = Math.floor(time / windowMs);
    const key = JSON.stringify([tenant, subject, 'import']);
    let bucket = buckets.get(key);
    if (!bucket || bucket.window !== window) buckets.set(key, bucket = { window, used: 0 });
    if (bucket.used >= limit) fail(429, 'import_rate_limited', {
      'Retry-After': String(Math.max(1, Math.ceil(((window + 1) * windowMs - time) / 1000))),
    });
    bucket.used++;
  };
}
```

#### fixture-auth.mjs

```javascript
import { generateKeyPair, SignJWT, jwtVerify } from 'jose';
import { fail } from './security.mjs';

// A local trusted issuer fixture. No external account/provider or login flow.
export async function createFixtureAuth({ now = Date.now } = {}) {
  const { privateKey, publicKey } = await generateKeyPair('RS256');
  const issuer = 'https://identity.example.test', audience = 'placement-secure-api';
  async function issue(subject, scope = 'docs:read docs:write', extra = {}) {
    const seconds = Math.floor(now() / 1000);
    return new SignJWT({ scope, ...extra }).setProtectedHeader({ alg: 'RS256', typ: 'at+jwt' })
      .setSubject(subject).setIssuer(issuer).setAudience(audience)
      .setIssuedAt(seconds).setExpirationTime(seconds + 300).sign(privateKey);
  }
  async function authenticate(header) {
    try {
      const match = /^Bearer ([^\s,]+)$/i.exec(header ?? '');
      if (!match) throw Error();
      const { payload } = await jwtVerify(match[1], publicKey, {
        algorithms: ['RS256'], typ: 'at+jwt', issuer, audience,
        requiredClaims: ['sub', 'exp', 'iat', 'scope'],
        currentDate: new Date(now()), clockTolerance: 0,
      });
      if (typeof payload.sub !== 'string' || !payload.sub ||
          typeof payload.scope !== 'string' || !Number.isSafeInteger(payload.iat) ||
          payload.iat > Math.floor(now() / 1000)) throw Error();
      // Tenant and role claims are deliberately not promoted into authority.
      return { subject: payload.sub, scopes: new Set(payload.scope.split(' ').filter(Boolean)) };
    } catch { fail(401, 'unauthenticated', { 'WWW-Authenticate': 'Bearer realm="placement-security"' }); }
  }
  const tokens = {};
  for (const subject of ['alice', 'bob', 'carol', 'dana']) tokens[subject] = await issue(subject);
  tokens.aliceReadOnly = await issue('alice', 'docs:read');
  return { authenticate, issue, tokens };
}
```

#### repository.mjs

```javascript
const key = (tenant, id) => JSON.stringify([tenant, id]);
const clone = row => row && { ...row };

export function createRepository() {
  const rows = new Map();
  const members = new Map([
    ['alpha', new Map([['alice', 'editor'], ['bob', 'viewer'], ['dana', 'viewer']])],
    ['beta', new Map([['carol', 'admin'], ['dana', 'admin']])],
  ]);
  const initial = [
    { tenantId: 'alpha', id: 1, ownerId: 'alice', title: 'Alpha private', visibility: 'private' },
    { tenantId: 'alpha', id: 2, ownerId: 'bob', title: 'Alpha shared', visibility: 'tenant' },
    { tenantId: 'beta', id: 1, ownerId: 'carol', title: 'Beta shared', visibility: 'tenant' },
    { tenantId: 'beta', id: 2, ownerId: 'carol', title: 'Beta private', visibility: 'private' },
  ];
  for (const row of initial) rows.set(key(row.tenantId, row.id), {
    ...row, version: 1, content: row.title, internalNote: 'PRIVATE-OPERATOR-NOTE',
  });
  const next = new Map([['alpha', 3], ['beta', 3]]);
  return {
    role: (tenant, subject) => members.get(tenant)?.get(subject),
    get: (tenant, id) => clone(rows.get(key(tenant, id))),
    list: tenant => [...rows.values()].filter(row => row.tenantId === tenant).map(clone),
    put: row => { rows.set(key(row.tenantId, row.id), clone(row)); },
    remove: (tenant, id) => rows.delete(key(tenant, id)),
    create: (tenant, subject, input) => {
      const row = {
        tenantId: tenant, id: next.get(tenant), ownerId: subject,
        ...input, version: 1, internalNote: 'PRIVATE-OPERATOR-NOTE',
      };
      next.set(tenant, row.id + 1);
      rows.set(key(tenant, row.id), clone(row));
      return clone(row);
    },
    // Test-only administrative seam, never exposed as an HTTP endpoint.
    setRole: (tenant, subject, role) => {
      if (role === null) members.get(tenant)?.delete(subject);
      else members.get(tenant)?.set(subject, role);
    },
  };
}
```

#### service.mjs

```javascript
import { randomUUID } from 'node:crypto';
import { allowed, roles, writable, safeFilename, textContent, fail } from './security.mjs';

const view = row => ({
  id: row.id, title: row.title, ownerId: row.ownerId, visibility: row.visibility, version: row.version,
});
export function createDocumentService({ repository, beforeRead = async () => {}, beforeCommit = async () => {} }) {
  const cache = new Map();
  function context(principal, tenant, write = false) {
    const role = repository.role(tenant, principal.subject);
    if (!roles.has(role)) fail(404, 'not_found');
    if (!principal.scopes.has(write ? 'docs:write' : 'docs:read')) fail(403, 'scope_required');
    return role;
  }
  function visible(principal, tenant, id, write = false) {
    const role = context(principal, tenant, write);
    const row = repository.get(tenant, id);
    if (!row || !allowed(role, principal.subject, 'read', row)) fail(404, 'not_found');
    return { role, row };
  }
  function edit(principal, tenant, id, action, input) {
    const result = visible(principal, tenant, id, true);
    if (!allowed(result.role, principal.subject, action, result.row)) fail(403, 'forbidden');
    if (input && Object.hasOwn(input, 'visibility') && result.role !== 'admin')
      fail(403, 'visibility_change_forbidden');
    return result;
  }
  function mayCreate(principal, tenant) {
    const role = context(principal, tenant, true);
    if (!allowed(role, principal.subject, 'create')) fail(403, 'forbidden');
  }
  async function list(principal, tenant, { after = 0, limit = 2, query = '' } = {}) {
    if (!Number.isSafeInteger(after) || after < 0 || !Number.isSafeInteger(limit) || limit < 1 || limit > 5 ||
        typeof query !== 'string' || query.length > 80) fail(400, 'invalid_query');
    context(principal, tenant);
    await beforeRead({ tenant, subject: principal.subject, action: 'list' });
    const role = context(principal, tenant);
    const rows = repository.list(tenant)
      .filter(row => allowed(role, principal.subject, 'read', row))
      .filter(row => row.id > after && row.title.includes(query))
      .sort((a, b) => a.id - b.id);
    const items = rows.slice(0, limit).map(view);
    return { items, nextAfter: rows.length > limit ? items.at(-1).id : null };
  }
  async function get(principal, tenant, id, download = false) {
    context(principal, tenant);
    await beforeRead({ tenant, subject: principal.subject, action: 'get', id });
    const { row } = visible(principal, tenant, id);
    if (download) return { content: row.content, filename: 'document-' + row.id + '.txt' };
    const key = JSON.stringify([tenant, id, row.version]);
    // Always establish current membership/object permission before serving a cache hit.
    if (!cache.has(key)) cache.set(key, view(row));
    return { ...cache.get(key) };
  }
  async function create(principal, tenant, value) {
    mayCreate(principal, tenant);
    const input = writable(value);
    await beforeCommit({ tenant, subject: principal.subject, action: 'create' });
    mayCreate(principal, tenant);
    return view(repository.create(tenant, principal.subject, { ...input, content: input.title }));
  }
  async function update(principal, tenant, id, value, condition) {
    const input = writable(value, true);
    edit(principal, tenant, id, 'update', input);
    if (condition === undefined) fail(428, 'condition_required');
    await beforeCommit({ tenant, subject: principal.subject, action: 'update', id });
    const { row } = edit(principal, tenant, id, 'update', input);
    if (condition !== '"v' + row.version + '"') fail(412, 'stale_version');
    const updated = { ...row, ...input, version: row.version + 1 };
    repository.put(updated);
    return view(updated);
  }
  async function bulkDelete(principal, tenant, ids) {
    if (!Array.isArray(ids) || !ids.length || ids.length > 5 ||
        ids.some(id => !Number.isSafeInteger(id) || id < 1) || new Set(ids).size !== ids.length)
      fail(400, 'invalid_ids');
    const checkAll = () => ids.map(id => edit(principal, tenant, id, 'delete'));
    checkAll();
    await beforeCommit({ tenant, subject: principal.subject, action: 'bulk-delete' });
    checkAll();
    // All checks precede all effects; no await inside this local commit region.
    for (const id of ids) repository.remove(tenant, id);
  }
  async function importText(principal, tenant, filename, bytes) {
    mayCreate(principal, tenant);
    const title = safeFilename(filename), content = textContent(bytes);
    await beforeCommit({ tenant, subject: principal.subject, action: 'import' });
    mayCreate(principal, tenant);
    return view(repository.create(tenant, principal.subject, {
      title, content, visibility: 'private', storageKey: randomUUID(),
    }));
  }
  return { list, get, create, update, bulkDelete, importText, mayCreate };
}
```

#### server.mjs

```javascript
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { ApiError, createBudget, fail } from './security.mjs';

async function bytes(req, mediaType, maximum) {
  const parts = (req.headers['content-type'] ?? '').split(';').map(s => s.trim().toLowerCase());
  if (parts[0] !== mediaType || parts.slice(1).some(s => !/^charset="?utf-8"?$/.test(s)) ||
      (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity'))
    fail(415, 'unsupported_body_format');
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size <= maximum) chunks.push(chunk);
  }
  if (size > maximum) fail(413, 'body_too_large');
  return Buffer.concat(chunks);
}
async function json(req) {
  const data = await bytes(req, 'application/json', 2048);
  try { return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(data)); }
  catch { fail(400, 'invalid_json'); }
}
export function createSecurityServer({
  authenticate, service, now = Date.now, importLimit = 3,
  allowedOrigins = ['https://app.example.test'], onAudit = () => {},
}) {
  const origins = new Set(allowedOrigins);
  const importBudget = createBudget({ now, limit: importLimit });
  const server = createServer(async (req, res) => {
    const requestId = randomUUID();
    let principal, tenant, action = 'route';
    res.setHeader('X-Request-Id', requestId);
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Vary', 'Origin');
    const send = (status, data, headers = {}) => {
      res.writeHead(status, {
        ...(data === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }),
        ...headers,
      });
      res.end(data === undefined ? undefined : JSON.stringify(data));
    };
    try {
      const origin = req.headers.origin;
      if (origin !== undefined) {
        if (!origins.has(origin)) fail(403, 'origin_rejected');
        res.setHeader('Access-Control-Allow-Origin', origin);
        res.setHeader('Access-Control-Expose-Headers', 'ETag, X-Request-Id');
      }
      const url = new URL(req.url, 'http://localhost');
      const match = /^\/tenants\/([a-z][a-z0-9-]{0,15})\/documents(?:\/(bulk-delete|import|[1-9]\d*)(\/download)?)?$/.exec(url.pathname);
      if (!match || (match[3] && !/^[1-9]\d*$/.test(match[2]))) fail(404, 'not_found');
      tenant = match[1];
      const suffix = match[2];
      const item = suffix && /^[1-9]\d*$/.test(suffix);
      const id = item ? Number(suffix) : undefined;
      if (item && !Number.isSafeInteger(id)) fail(400, 'invalid_id');
      action = !suffix ? (req.method === 'POST' ? 'create' : 'list')
        : suffix === 'import' ? 'import' : suffix === 'bulk-delete' ? 'bulk-delete'
          : match[3] ? 'download' : req.method === 'PATCH' ? 'update' : 'get';
      const methods = !suffix ? ['GET', 'POST']
        : item ? (match[3] ? ['GET'] : ['GET', 'PATCH']) : ['POST'];
      if (req.method === 'OPTIONS') {
        const requestedMethod = req.headers['access-control-request-method'];
        const requested = (req.headers['access-control-request-headers'] ?? '')
          .split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
        if (!origin || !requestedMethod) fail(400, 'invalid_preflight');
        if (!methods.includes(requestedMethod) ||
            requested.some(name => !['authorization', 'content-type', 'if-match', 'x-file-name'].includes(name)))
          fail(403, 'preflight_rejected');
        return send(204, undefined, {
          'Access-Control-Allow-Methods': methods.join(', '),
          'Access-Control-Allow-Headers': requested.join(', '),
          'Access-Control-Max-Age': '60',
          Vary: 'Origin, Access-Control-Request-Method, Access-Control-Request-Headers',
        });
      }
      if (!methods.includes(req.method)) fail(405, 'method_not_allowed', { Allow: methods.join(', ') + ', OPTIONS' });
      principal = await authenticate(req.headers.authorization);
      if (action !== 'list' && url.search) fail(400, 'unexpected_query');

      if (action === 'list') {
        for (const name of url.searchParams.keys())
          if (!['after', 'limit', 'q'].includes(name) || url.searchParams.getAll(name).length !== 1)
            fail(400, 'invalid_query');
        const after = url.searchParams.get('after') ?? '0', limit = url.searchParams.get('limit') ?? '2';
        if (!/^(0|[1-9]\d*)$/.test(after) || !/^[1-5]$/.test(limit)) fail(400, 'invalid_query');
        return send(200, await service.list(principal, tenant, {
          after: Number(after), limit: Number(limit), query: url.searchParams.get('q') ?? '',
        }));
      }
      if (action === 'get' || action === 'download') {
        const result = await service.get(principal, tenant, id, action === 'download');
        if (action === 'download') {
          res.writeHead(200, {
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': 'attachment; filename="' + result.filename + '"',
          });
          return res.end(result.content);
        }
        return send(200, result, { ETag: '"v' + result.version + '"' });
      }
      if (action === 'create') {
        service.mayCreate(principal, tenant);
        const result = await service.create(principal, tenant, await json(req));
        return send(201, result, { Location: '/tenants/' + tenant + '/documents/' + result.id });
      }
      if (action === 'update') {
        const result = await service.update(principal, tenant, id, await json(req), req.headers['if-match']);
        return send(200, result, { ETag: '"v' + result.version + '"' });
      }
      if (action === 'bulk-delete') {
        const input = await json(req);
        if (!input || typeof input !== 'object' || Array.isArray(input) ||
            Object.keys(input).join(',') !== 'ids') fail(400, 'invalid_ids');
        await service.bulkDelete(principal, tenant, input.ids);
        return send(204);
      }
      service.mayCreate(principal, tenant);
      importBudget(tenant, principal.subject);
      const data = await bytes(req, 'text/plain', 1024);
      const result = await service.importText(principal, tenant, req.headers['x-file-name'], data);
      return send(201, result, { Location: '/tenants/' + tenant + '/documents/' + result.id });
    } catch (error) {
      if (res.headersSent) { res.destroy(); return; }
      const known = error instanceof ApiError;
      send(known ? error.status : 500, {
        code: known ? error.code : 'internal_error', requestId,
      }, known ? error.headers : {});
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
      // Best-effort audit example. Do not retain credentials, titles or request bodies.
      try { onAudit({ requestId, subject: principal?.subject ?? null, tenant: tenant ?? null, action, status: res.statusCode }); }
      catch { /* A production audit sink needs its own durability/failure policy. */ }
    }
  });
  server.requestTimeout = 10_000;
  server.headersTimeout = 5000;
  return server;
}
```

The repository's setRole hook is test-only. No HTTP route exposes it. Likewise, beforeRead and beforeCommit are supplied by the verifier, not by a request parameter.

### Implementation limits

All authorization state, projection cache and counters are local Maps. The repository returns flat copies so handlers cannot accidentally mutate stored objects through a returned reference.

The cache and bucket Maps do not implement production eviction. The SQL fixture is separate from the service. No real object-storage file is created by storageKey metadata.

CORS support is intentionally narrow. The OPTIONS handler implements the demonstrated preflight contract, not every possible plain-OPTIONS/HTTP negotiation behavior.

---

## 8.15 Verification: check denial and its consequences

A negative test should establish more than “the response was 403.”

| Area | Useful invariant checked here |
| --- | --- |
| Identity | Missing/forged/expired credential cannot reach protected data |
| Tenant boundary | Other tenant/unknown tenant is concealed under the selected policy |
| Role/object policy | Viewer, owner, editor and tenant admin have distinct permissions |
| Scope ceiling | Read-only credential cannot write even for an editor |
| Input authority | Body/header/signed extras do not replace server-owned membership/fields |
| Lists | Filter visible rows before search/continuation/slicing |
| Bulk mutation | One forbidden/missing ID prevents every deletion |
| Download/import | Apply object/create policy independently of ordinary JSON reads |
| Cache | Same ID in different tenants stays distinct; current policy gates hits |
| Permission race | Revocation while awaiting blocks update/bulk commit |
| Browser policy | Exact origin/header/method preflight checks; actual request still authorizes |
| File boundary | Rejected text inputs leave documents unchanged |
| Audit | Correlation/decision captured without credentials or content |
| SQL | Parameter binding and tenant scoping are independent requirements |

### Actual selected output

```text
PASS write scope does not upgrade viewer role: {"create":403,"editOwn":403,"stateUnchanged":true}
PASS mass assignment attempts cannot alter server-owned fields: {"rejectedInputs":4,"stateUnchanged":true}
PASS list filters permissions before pagination: {"bobIds":[2],"bobNext":null,"aliceIds":[1,2]}
PASS bulk failure has no partial deletion: {"forbidden":403,"missing":404,"duplicate":400,"stateUnchanged":true}
PASS cache cannot mix same local ID across tenants or viewers: {"alpha1":"Alpha private","beta1":"Beta shared","otherViewer":404}
PASS current membership and object policy checked before cache hit: {"downgradedPrivate":404,"removedMembership":404}
PASS membership revoked while update awaits prevents commit: {"status":404,"documentsUnchanged":true}
PASS membership revoked while bulk-delete awaits prevents commit: {"status":404,"documentsUnchanged":true}
PASS overlapping tenant requests keep local context and role: {"alpha":"Alpha shared","beta":"Beta private"}
PASS unsafe concatenation leaks rows in isolated training database: {"rows":4,"includesOtherTenant":true}
PASS bound value remains data rather than injected SQL: {"rows":0}
PASS parameterization alone does not add tenant authorization: {"rows":2,"distinctTenants":["alpha","beta"]}
PASS composite foreign key rejects cross-tenant parent: {"rejected":true,"rowsRemain":4}
Verified 74 checks across policy, real HTTP and SQLite groups.
```

The full run records **22 policy checks, 46 HTTP checks and six SQLite checks**. Individual checks can contain several assertions/requests; 74 is the count of named cases, not a request-count or benchmark result.

Concurrency cases use explicit entered/release gates and scenario deadlines. They do not infer overlap from arbitrary sleeps. Temporary HTTP listeners and the in-memory SQL connection are closed.

### What these checks do not establish

There is no real PostgreSQL/RLS deployment, browser automation, HTML preview, object-storage service, PDF/archive parser, malware scanner, external network ingestion, distributed counter, multi-instance store, durable audit pipeline or load benchmark.

The string-escaping check is not a browser XSS assessment. CORS tests inspect header/status/state contracts, not browser enforcement. The SQL examples do not turn the HTTP repository into a database-backed service.

A local synchronous recheck does not prove distributed revocation ordering. Production behavior requires verification at those real boundaries.

---

## 8.16 Extend the architecture by requirement

### Requirement: move documents to PostgreSQL

Preserve tenant identity in keys/queries and relevant foreign keys. Implement current membership/object policy under a defined transaction/freshness contract.

Add engine-specific checks for application runtime roles, constraints, optional RLS and concurrent permission changes. Test tenant context across reused pool connections.

### Requirement: add background exports

Persist trusted tenant/requester context and the requested capability, then define whether current permission must be rechecked at execution and download. A requester removed after enqueue should not accidentally receive a private export.

Export results need their own retention/access policy. Do not publish an entire tenant dataset merely because the worker itself has a privileged database connection.

### Requirement: add a document search/RAG index

Store tenant/resource identity with indexed chunks, filter authorized retrieval and apply permissions before content reaches the model or client.

Deleting/changing access needs index/cache invalidation or another freshness mechanism. A correct database API does not automatically secure a separate vector index.

Prompt instructions inside a document are untrusted content. Retrieval authorization and prompt-injection defense address different failures; M23 develops the pipeline.

### Requirement: support tenant administrators and support staff

Separate tenant-local administration from platform-wide operational privileges. Use explicit administrative workflows, narrow capabilities and auditable access.

Do not infer platform authority from a client-provided role name or a tenant-admin role in one organization.

### Requirement: revoke access quickly

Define the permitted propagation delay across sessions, policy caches, API instances, download credentials and jobs. Coordinate invalidation or authoritative checks at the necessary boundaries.

An architecture answer should state its consistency/failure policy, not simply add the word secure to a diagram.

---

## 8.17 Resume connection

For a multi-tenant or permission-related resume claim, prepare a concrete explanation:

> “I verified the caller first, selected a tenant only after membership checks, scoped data access and checked resource/action permissions. I allowlisted writable fields and selected public output. I tested another tenant, a same-tenant non-owner, a lower role and a revoked member, including denied effects and cache paths.”

Only describe mechanisms your project actually implemented. This learning API gives you practice evidence, not proof of an earlier project's security.

| Resume topic | Follow-up to prepare |
| --- | --- |
| Multi-tenant SaaS | Which queries, caches, downloads, jobs and admin paths carry tenant scope? |
| Organization hierarchy | How does a reporting relationship grant/revoke access, and how is it bounded by tenant? |
| Signed/revocable invites | How are purpose, target, expiry, use and revocation checked at acceptance? |
| Document/AI ingestion | Who may upload, parse, retrieve and download each artifact/chunk? |
| Payment/credits | Which caller/event may act on this order or ledger, and who supplies authoritative amounts? |
| Deployment/performance | What do privileged service identities and shared resource limits allow? |

A good three-minute answer gives the policy, its enforcement location, a rejected example and the evidence. “We hide unauthorized buttons” is only a user-interface statement.

---

## 8.18 Must remember

- Authentication is a prerequisite, not a universal permission grant.
- A tenant selector is untrusted until resolved against verified identity/current policy.
- Tenant admin and platform admin are different capabilities.
- Role, object relationship, attributes and scope can all constrain one operation.
- Unknown roles/actions fail closed.
- UUIDs do not replace object-level authorization.
- Request body/header fields must not silently become ownership or role authority.
- Input allowlists and response projections protect different directions.
- Lists/counts/search/continuation can leak data if filtered at the wrong stage.
- Bulk operations require every-object policy and a defined failure contract.
- Downloads, caches, workers and indexes are additional data paths.
- Cache keys need the relevant tenant/resource/policy dimensions.
- Current permission must be established before serving a protected cache hit.
- If-Match prevents stale overwrites; it does not establish permission.
- A check before await can become stale before the effect.
- Parameterized SQL separates values from syntax; it does not add tenant policy.
- SQL identifiers need a controlled mapping rather than ordinary value binding.
- RLS must be verified with actual runtime roles and connection behavior.
- HTML text encoding is not a universal sanitizer for every output context.
- CSRF, CORS, XSS and authorization address distinct boundaries.
- A preflight 204 does not grant access to protected data.
- File names/MIME are untrusted claims; rendering/parsing/storage need independent controls.
- A small UTF-8 text contract is not a general malware/complex-file validation system.
- Rate, concurrency, cost quota, size and time bounds solve different pressure.
- Audit metadata is useful; raw credentials/content in logs create exposure.

---

## 8.19 Common wrong answers

| Wrong answer | Correction |
| --- | --- |
| “The JWT is valid, so access is allowed.” | Apply tenant/resource/action policy after authentication. |
| “The request says tenantId=alpha.” | Resolve the candidate against trusted membership. |
| “An admin somewhere is an admin everywhere.” | Scope roles to the relevant tenant/capability. |
| “The owner may always edit.” | Role, scope and workflow rules can still constrain ownership. |
| “UUIDs solve IDOR.” | Known identifiers still require authorization. |
| “We check the first ID in a batch.” | Check every object and define partial/all-or-nothing behavior. |
| “Pagination first, authorization afterward.” | Hidden rows can distort continuation/counts and leak information. |
| “A cached result was authorized once.” | Permission and representation freshness still matter. |
| “The version matches, so permission is proven.” | Version and authorization establish different facts. |
| “Parameterized SQL is tenant isolation.” | A bound unscoped query can still select another tenant's data. |
| “RLS protects the application using its admin connection.” | Runtime roles may bypass the policy. |
| “ORM update(req.body) is safe because types exist.” | Runtime writable-field/property policy still applies. |
| “CORS blocks all unauthorized callers.” | It is a browser response-access mechanism; server authorization remains. |
| “SameSite/HttpOnly solves every CSRF/XSS issue.” | Follow actual credential sending and script capabilities. |
| “A .txt or .pdf extension proves safe contents.” | Content, parser, resource and rendering boundaries remain. |
| “A random storage key makes every download private.” | Retrieval must apply an explicit access/delegation policy. |
| “A local counter is a global rate limit.” | Replicas need coordination or a clearly per-instance policy. |
| “A denied status proves no side effect occurred.” | Assert actual state and downstream effects too. |

---

## 8.20 Interview questions and follow-ups

These are preparation targets covering common security mechanisms and design failures. They are not a measured ranking of company questions.

**Q1. What is authorization?**

It decides whether a verified subject may perform an action on a resource under the application's policy.

**Follow-up:** where do tenant membership and document visibility enter the decision?

**Q2. Authentication versus authorization in middleware?**

Authentication establishes the principal. Authorization uses that principal and current resource/context to permit or deny the operation.

**Follow-up:** why is a route-level logged-in check insufficient?

**Q3. What is BOLA/IDOR?**

A caller manipulates a resource identifier and accesses an object without a correct object-level decision. Identifier unpredictability alone does not fix it.

**Follow-up:** test a known UUID belonging to another member or tenant.

**Q4. Object-level versus function-level authorization?**

Object policy governs a specific target. Function policy governs use of an operation/capability such as tenant administration.

**Follow-up:** can a route-level editor role still edit someone else's private document?

**Q5. What is property-level authorization?**

It controls which fields a caller can read or change, even when access to the surrounding object/operation is allowed.

**Follow-up:** why reject ownerId and separately guard visibility changes?

**Q6. RBAC versus attribute/relationship policy?**

Roles group capabilities; attributes/relationships add conditions such as visibility, ownership or project membership. Real policies often combine them.

**Follow-up:** explain Bob owning a document but lacking edit permission.

**Q7. What does an OAuth/token scope mean here?**

It limits the credential's capability. docs:write does not independently grant tenant membership or administrator privileges.

**Follow-up:** why is AliceReadOnly denied despite Alice's editor membership?

**Q8. How do you establish tenant context?**

Treat path/header/subdomain selection as a candidate, verify membership using the trusted subject and carry context locally through scoped operations.

**Follow-up:** why can a module-global currentTenant fail across await?

**Q9. Can signed role claims become stale?**

Yes. A signature protects authenticity/integrity, not current membership freshness. Decide whether to resolve current policy or accept a bounded staleness model.

**Follow-up:** how quickly must removal take effect in your project?

**Q10. Why include tenant_id in keys and relationships?**

Tenant-local IDs can repeat. Composite identity and foreign keys prevent accidental cross-tenant references under the defined schema.

**Follow-up:** what did the SQLite cross-tenant parent test reject?

**Q11. Shared tables versus separate databases?**

Compare isolation requirements, cost, migrations, provisioning and operations. Physical separation still leaves intra-tenant user permissions.

**Follow-up:** what new routing/admin paths does a hybrid model introduce?

**Q12. What can PostgreSQL RLS add?**

Database-side row policies can reinforce isolation, provided runtime roles/context/policies are correct. Privileged roles can bypass it.

**Follow-up:** how would you test pooled connection context with the actual application role?

**Q13. Where should a list be permission-filtered?**

Before returning counts/continuation and slicing the visible result according to the defined contract. Avoid allowing hidden rows to shape disclosure accidentally.

**Follow-up:** why does Bob's limit=1 page contain document 2 immediately?

**Q14. How do you secure a bulk operation?**

Validate the requested set, authorize each object and apply a defined all-or-nothing or partial-result contract at the appropriate commit boundary.

**Follow-up:** what remains when one requested ID is forbidden or missing?

**Q15. How do caches cause tenant leaks?**

Keys may omit tenant or policy dimensions, or hits may bypass current permission/freshness checks.

**Follow-up:** when would a subject-specific representation require more than tenant/id/version?

**Q16. How do you prevent a revoked member's pending write?**

Define the required ordering/freshness, recheck at the effect boundary and coordinate that decision with the write using the real state system.

**Follow-up:** why is the local Map guarantee not proof of database/distributed revocation ordering?

**Q17. Does If-Match authorize an edit?**

No. It checks a representation/version condition. Role, ownership, tenant and property rules still apply.

**Follow-up:** what different failures produce 403 and 412 here?

**Q18. What is mass assignment?**

Unrestricted binding/copying of input into internal objects can let callers change server-owned or privileged fields.

**Follow-up:** why does a response need a separate output projection?

**Q19. How do parameterized queries prevent injection?**

Bound values remain data rather than changing the query structure. Dynamic identifiers need an allowed mapping.

**Follow-up:** why did a safely parameterized id-only query still return both tenants?

**Q20. Can an ORM still have injection or authorization bugs?**

Yes. Raw/dynamic query construction and missing policy predicates can bypass its conveniences. Validate types and query structure deliberately.

**Follow-up:** what happens if an expected scalar becomes an operator-bearing object?

**Q21. XSS versus CSRF?**

XSS executes attacker-controlled script in an origin. CSRF induces an unwanted request carrying ambient credentials. Their defenses are different.

**Follow-up:** why can XSS undermine a CSRF-token strategy?

**Q22. What is CORS?**

A browser mechanism governing cross-origin response access. It does not establish the caller's identity or resource permissions.

**Follow-up:** why does an allowed preflight not prove the actual request will succeed?

**Q23. Why avoid blindly reflecting Origin?**

It can authorize browser access from an unintended origin. Use a deliberate exact policy, including credentials and preflight behavior.

**Follow-up:** explain null Origin, suffix tricks and no-Origin callers in the example.

**Q24. How do you render user input safely?**

Use the framework's safe text rendering/context-appropriate encoding. Rich HTML needs a supported sanitizer; URL/script/style contexts require their own policy.

**Follow-up:** what does the string-escaping test fail to prove about a real browser?

**Q25. How do you design safe file ingestion?**

Authorize, bound bytes/work, validate the supported content model, use server-controlled storage identity and secure parsing/retrieval/rendering.

**Follow-up:** which new risks appear for archives or PDF parsers?

**Q26. Why not use the uploaded filename as a path?**

It is untrusted and can encode traversal or collisions. Keep a validated display name separate from server-controlled storage location.

**Follow-up:** why is a random key still insufficient for download authorization?

**Q27. What is SSRF in URL ingestion?**

A server follows attacker-influenced targets and reaches unintended resources. Target, protocol, resolution, redirect and egress policies must work together.

**Follow-up:** why is checking the initial hostname alone insufficient?

**Q28. Which limits protect an expensive API?**

Use appropriate request-size, rate, concurrent-work, cost/quota and time bounds at relevant layers. A request count does not bound every request's cost.

**Follow-up:** how do replicas and limiter-store failures change the policy?

**Q29. What belongs in a security audit event?**

Useful identifiers/context, action, outcome and correlation under a privacy/retention policy. Avoid raw credentials and unnecessary private content.

**Follow-up:** what does this example's best-effort hook not guarantee?

**Q30. How would you test tenant isolation?**

Use several subjects/roles/tenants and exercise reads, lists, writes, bulk, downloads, caches and revoked membership. Check both responses and state/disclosure effects.

**Follow-up:** which additional database, browser, worker and storage tests would deployment require?

---

## 8.21 Practice tasks

### Task 1: Write the permission matrix

Recreate viewer/editor/admin rules and apply them to Alice, Bob, Carol and Dana without reading the implementation.

**Checkpoint:** ownership alone is insufficient, and Dana's role changes with tenant.

### Task 2: Review an endpoint

Given GET /documents/id, identify the principal, tenant identity, current policy source and response projection it would need.

**Checkpoint:** a logged-in flag and a guessed/unguessable ID do not establish object access.

### Task 3: Add an export contract

Specify requester/tenant context, execution-time permission, result access, expiration and what happens if membership changes while queued.

**Checkpoint:** the worker's own database privilege is not the requester's permission.

### Task 4: Design a list query

Translate the visibility policy into a proposed database query and decide which counts/continuation are public. Then identify the index/plan checks required later.

**Checkpoint:** do not apply a visible-row filter only after slicing an arbitrary unfiltered page.

### Task 5: Analyze a cache

Compare caching identical public projections with subject-specific redacted projections. Identify key dimensions and permission-invalidation policy.

**Checkpoint:** a tenant-aware key is necessary in many designs but does not independently ensure current access.

### Task 6: Break a local permission race in a scratch copy

Remove the final policy recheck after beforeCommit, predict the effect, then run the revocation cases.

**Checkpoint:** restore the authoritative source. The failure should concern actual document state, not merely a different status.

### Task 7: Compare SQL safety and policy

Run the SQL verifier and explain why both parameter binding and tenant/object predicates matter.

**Checkpoint:** the bound id-only query is injection-safe yet insufficiently scoped.

### Task 8: Extend text import to PDF

List the new byte/parser/expansion/time/storage/rendering boundaries and choose an isolation/ownership workflow.

**Checkpoint:** an extension allowlist alone is not a parser sandbox or malware scan.

### Task 9: Specify cookie-based mutations

Adapt the bearer-only example conceptually to M7 sessions. Identify cookie policy, CSRF mechanism, allowed browser origins and server-side authorization.

**Checkpoint:** CORS and SameSite are not universal replacements for the intended CSRF strategy.

### Task 10: Defend your resume implementation

Explain one real permission rule, its enforcement location, an abuse case and actual verification. Then name one unverified boundary honestly.

**Checkpoint:** distinguish implemented evidence, a local example and a future architectural proposal.

---

## Exit checklist

- [ ] I can separate identity, tenant selection, scopes and resource permissions.
- [ ] I can write a subject/action/resource/context policy.
- [ ] I can compare role, attribute and relationship rules.
- [ ] I can explain object/function/property authorization failures.
- [ ] I can reject client-controlled ownership/role authority.
- [ ] I can scope identity/queries/relationships for tenant-local IDs.
- [ ] I can compare shared-table/schema/database isolation strategies.
- [ ] I can explain RLS runtime-role and pooled-context limitations.
- [ ] I can secure list/search/continuation/count disclosure.
- [ ] I can define and test an every-object bulk contract.
- [ ] I can apply access policy to downloads and cache hits.
- [ ] I can identify stale checks across await and locate the commit boundary.
- [ ] I can distinguish authorization from version/precondition checks.
- [ ] I can explain parameter binding versus policy predicates.
- [ ] I can distinguish values from SQL identifiers/operators/shell arguments.
- [ ] I can explain context-specific XSS prevention.
- [ ] I can distinguish CSRF, CORS and API authorization.
- [ ] I can explain the example's exact preflight/Origin policy.
- [ ] I can define a narrow file-content/storage/retrieval contract.
- [ ] I can identify parser/archive/URL-ingestion risks not implemented here.
- [ ] I can describe secret/audit lifecycle without exposing credentials.
- [ ] I can distinguish rate, concurrency, quota, size and time limits.
- [ ] I can run all 74 checks and explain the evidence boundaries.

---

## Next

[**M9: Webhooks, Payments and Reliable Integrations**](/docs/resume-skills/webhooks-payments-reliable-integrations). Verify exact signed payloads, bind events to the correct account/tenant, handle replay/duplicates and out-of-order delivery, and coordinate payment/credit state under uncertain outcomes.

The architecture companion will reuse these permission and state boundaries in multi-tenant SaaS, file-processing, payment and RAG designs.

### Sources and reproducible evidence

Research checked on **14 October 2026**. Execution used Node.js v22.14.0, jose 6.2.12 and SQLite 3.47.2.

- OWASP API Security 2023: [object-level authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/), [property-level authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) and [function-level authorization](https://api-security.owasp.org/editions/2023/en/0xa5-broken-function-level-authorization/).
- OWASP: [authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) and [multi-tenant security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html).
- [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html); no PostgreSQL/RLS runtime guarantee is claimed here.
- OWASP: [SQL injection](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [XSS](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [file upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) and [secrets](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).
- [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS).
- Node v22.14.0: [SQLite API](https://nodejs.org/download/release/v22.14.0/docs/api/sqlite.html) and [child processes](https://nodejs.org/download/release/v22.14.0/docs/api/child_process.html).
- [jose project](https://github.com/panva/jose); the isolated package.json/package-lock.json pin 6.2.12.
- Preserved source: examples/resume-skills/module-8-api-security/security.mjs, fixture-auth.mjs, repository.mjs, service.mjs, server.mjs and start.mjs.
- Preserved verification: verify.mjs, verify-policy.mjs, verify-http.mjs, verify-sql.mjs, aggregate/group results and output files, sql-verification-stderr.txt and validation-summary.json.
