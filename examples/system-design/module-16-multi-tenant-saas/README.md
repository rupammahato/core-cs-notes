# S11: Multi-tenant SaaS with authentication and permissions

From repository root run `python examples/system-design/module-16-multi-tenant-saas/verify.py`. Standard-library Python; owned temporary SQLite/HTTP resources are closed and removed. Port 3000 stays unused.

`saas.py` implements hashed opaque sessions, current tenant/membership/role checks, owned/shared title documents, verified switch rotation, invitation lifecycle, atomic quota/audit and scoped metadata exports with worker/delivery rechecks. `verify.py` records 95 checks including four competing calls, rollback/reopen and actual bearer API HTTP. No tokens are stored in observation outputs.

Session issuance assumes trusted upstream identity verification. No password/OIDC/BFF/browser-cookie/CSRF integration, email delivery, object storage, production RLS or performance claim is implemented. Invitations use random opaque capabilities and server state, not signed JWTs.

`lesson.md` is the teaching source. `../worked-systems-s10-s11/author.py` embeds exact code and observed results into Part 18. See the batch README for integration and validation.
