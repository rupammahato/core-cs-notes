# M8: API Security, Authorization and Multi-Tenancy

Recorded versions: Node.js v22.14.0, jose 6.2.12, SQLite 3.47.2.

From the repository root:

```powershell
npm --prefix examples/resume-skills/module-8-api-security ci --ignore-scripts --no-audit --no-fund
node examples/resume-skills/module-8-api-security/verify.mjs
```

Individual groups: verify-policy.mjs, verify-http.mjs and verify-sql.mjs.

74 named cases pass: 22 policy/input, 46 real HTTP and six SQLite cases. Cases can contain multiple assertions/requests; this is not a request count or throughput result. The SQL group uses experimental node:sqlite on the recorded runtime and preserves its expected warning separately.

The API uses in-memory documents and membership. The SQL group uses a separate in-memory database to demonstrate parameter binding, independent tenant predicates and composite foreign keys. It is not PostgreSQL/RLS verification.

Optional manual service:

```powershell
node examples/resume-skills/module-8-api-security/start.mjs
```

It binds 127.0.0.1:3108 and prints generated Alice/Dana fixture bearer credentials valid for 300 seconds. Copy a credential into Authorization: Bearer for manual requests. Stop it with Ctrl+C. This is a local trusted issuer fixture, not an external login/provider integration.

Memberships: Alice=alpha editor; Bob=alpha viewer; Carol=beta admin; Dana=alpha viewer and beta admin. Resource IDs repeat across tenants. Token scopes cap operations but do not override membership/role/ownership.

Routes under /tenants/:tenant/documents: GET list, POST create, GET /:id, PATCH /:id with exact If-Match, POST /bulk-delete, GET /:id/download, POST /import. Lists accept after, limit=1..5 and q. Bulk deletion is locally all-or-nothing.

Imports accept <=1024-byte UTF-8 text/plain without NUL and narrow .txt display names. Ownership is server-assigned and visibility private. storageKey is recorded metadata only: no file/object-store artifact is created. Downloads reauthorize and return text/plain attachments with nosniff.

CORS is exact-origin/header/method preflight policy for a bearer-only API. It does not establish identity or tenant permission. No session cookies, browser enforcement or CSRF flow is implemented here; M7 demonstrates its own cookie/CSRF mechanism.

Gate-controlled tests revoke membership while edits/bulk deletes await and overlap requests in different tenants. Cache hits recheck current membership/object policy. Denied effects are checked against actual document state.

Maps/counters/cache and audit are not durable/distributed. No production eviction, PostgreSQL/RLS, browser tests, malware scanning, complex-file parsers, object storage, SSRF network fetching, distributed revocation ordering or throughput is established. Audit tests confirm generated credentials/content are not retained; the optional launcher deliberately prints public learning credentials for manual use.

See the [M8 chapter](../../../Resume%20Skills%20Notes/resume-skills-handbook-part-10-module-8-api-security-authorization-multi-tenancy.md) for explanations, complete source and interview practice.
