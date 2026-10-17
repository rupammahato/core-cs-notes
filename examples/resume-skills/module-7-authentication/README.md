# M7: Authentication, Sessions, JWT and OAuth

Recorded runtime: Node.js v22.14.0; isolated dependency: jose 6.2.12.

From the repository root:

```powershell
npm --prefix examples/resume-skills/module-7-authentication ci --ignore-scripts --no-audit --no-fund
node examples/resume-skills/module-7-authentication/verify.mjs
```

Individual groups: verify-crypto.mjs, verify-http.mjs and verify-oauth.mjs. The aggregate verifier records 86 checks: 38 credential/session/token/crypto checks, 32 real HTTP checks and 16 OAuth protocol-model checks. All HTTP listeners are temporary and closed.

The package has no site dependency. The website's dependencies are unchanged.

Optional manual service:

```powershell
node examples/resume-skills/module-7-authentication/start.mjs
```

It binds 127.0.0.1:3107. Stop it with Ctrl+C. Public fixture: learner@example.test / placement-demo-password.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3107/tokens/login -ContentType application/json -Headers @{Origin='http://127.0.0.1:3107'} -Body '{"email":"learner@example.test","password":"placement-demo-password"}'
```

Session routes: POST /session/login, GET /session/me, POST /session/logout. Logout needs the cookie and X-CSRF-Token. Token routes: POST /tokens/login, /tokens/refresh and /tokens/logout; GET /api/me accepts the access credential in Authorization: Bearer.

These are first-party fixture endpoints, not OAuth password-grant endpoints. Every POST requires the configured trusted Origin. The local HTTP launcher uses sid without Secure; the verifier checks __Host-sid/Secure headers while manually passing cookies. It does not emulate browser cookie handling or TLS.

The OAuth file is a synchronous protocol model: PKCE S256, browser-bound state, redirect/client matching, code/state consumption and expiry. Provider authentication/consent are assumed; discovery, HTTP provider endpoints, client authentication and OIDC validation are not implemented.

Signing keys, sessions and refresh families live only in memory. Access lifetime: 60 seconds. Session idle/absolute limits: 30/120 seconds. Refresh-family absolute limit: 300 seconds. Rotation consumes old credentials; reuse revokes the family, including the winner's successor after a legitimate race. Existing issued access tokens remain valid until expiry.

Password derivation uses async Node scrypt with N=131072, r=8, p=1 and a 256 MiB maxmem ceiling. No throughput, timing indistinguishability or actual peak-memory measurement is claimed.

Results/logs contain safe observations rather than generated bearer credentials or private keys. No production store cleanup, distributed coordination, crash recovery, MFA/recovery, abuse-control deployment, browser tests, real provider login or JWKS/key rotation is established.

See the [M7 chapter](../../../Resume%20Skills%20Notes/resume-skills-handbook-part-9-module-7-authentication-sessions-jwt-oauth.md) for the complete explanation and interview drills.
