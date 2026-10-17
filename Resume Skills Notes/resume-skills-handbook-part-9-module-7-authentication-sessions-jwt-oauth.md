# Resume Skills Placement Handbook — Part 9
# Module 7: Authentication, Sessions, JWT and OAuth

**Module 7 · 4–5 hours · Tier 1 · Requires: M0-M6**

---

## Why this module matters

An API must establish who is calling before applying permissions. “We used JWT” does not explain how passwords were verified, which claims were trusted, how logout worked or what happened when a refresh token was stolen.

Authentication questions quickly become architecture questions: where is session state stored, which service owns keys, what can a browser read, and how quickly can a compromised credential stop working?

> **Authentication establishes a trusted identity through a credential lifecycle: issue, transport, verify, expire, renew and revoke. Follow that lifecycle across every boundary.**

This module compares two first-party login designs and then traces delegated access with OAuth/OIDC. It includes runnable password/session/JWT examples and a deliberately limited OAuth protocol model.

**Verification:** **86 checks passed on Node.js v22.14.0 and jose 6.2.12**: 38 password/session/token/crypto checks, 32 real HTTP checks, and 16 OAuth-model checks. The latter are a local state-machine model, not a real provider login.

### Run the examples

From the repository root:

```powershell
node examples/resume-skills/module-7-authentication/verify.mjs
node examples/resume-skills/module-7-authentication/verify-crypto.mjs
node examples/resume-skills/module-7-authentication/verify-http.mjs
node examples/resume-skills/module-7-authentication/verify-oauth.mjs
```

The isolated example package pins jose, a maintained JOSE implementation. For a fresh checkout:

```powershell
npm --prefix examples/resume-skills/module-7-authentication ci --ignore-scripts --no-audit --no-fund
```

For manual inspection:

```powershell
node examples/resume-skills/module-7-authentication/start.mjs
```

The optional launcher binds **127.0.0.1:3107**, and Ctrl+C stops it. Its public fixture account is learner@example.test with password placement-demo-password. These are teaching values, not credentials for any external service.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3107/tokens/login -ContentType application/json -Headers @{Origin='http://127.0.0.1:3107'} -Body '{"email":"learner@example.test","password":"placement-demo-password"}'
```

The HTTP launcher uses an explicitly local cookie configuration because it does not serve TLS. Tests inspect the secure-cookie configuration over raw loopback HTTP while manually passing cookie headers. They do not prove browser cookie acceptance or HTTPS behavior.

---

## 7.1 Authentication versus authorization

**Authentication (AuthN)** establishes the identity represented by the caller's credentials. **Authorization (AuthZ)** decides whether that identity may perform a particular action on a particular resource.

| Question | Concern | Example |
| --- | --- | --- |
| Who is this caller? | Authentication | This session resolves to user-1 |
| May this caller read project 42? | Authorization | Membership and project policy |
| May this caller edit this invoice? | Authorization plus domain state | Owner, role and invoice status |
| Is the caller really the named legal person? | Identity proofing | Separate verification process |

A valid token does not grant universal access. A user can authenticate correctly and still be forbidden from reading another tenant's data.

The trusted identity must come from the verification path. A request body containing userId:"admin" is a claim supplied by the caller, not an authenticated subject.

Reference: [OWASP authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

### Locate the trust boundary

```text
untrusted request
  -> extract supported credential
  -> verify credential and lifecycle state
  -> establish trusted subject
  -> authorize subject against resource/action
  -> apply business invariant
  -> perform effect
```

M7 establishes identity. M8 follows through ownership, roles, scopes and tenant filtering. Keep both stages visible even if one framework middleware invokes them together.

**Interview line:** “Authentication tells my application which subject the credential represents. Authorization checks what that subject may do to this specific resource.”

---

## 7.2 Credentials, authenticators and threats

A password demonstrates knowledge of a secret. A session ID or bearer token demonstrates possession of a credential. A passkey uses public-key credentials and an authenticator; it is not simply a password encoded differently.

Multi-factor authentication combines independent factor categories. Two passwords do not become two factors merely because the user typed twice.

| Threat | What goes wrong | Relevant response |
| --- | --- | --- |
| Credential stuffing | Stolen passwords reused across services | MFA/passkeys, throttling, detection |
| Offline guessing | Attacker obtains password verifiers | Salted adaptive password hashing |
| Session theft | Attacker obtains a valid session credential | Transport/storage controls, expiry, revocation |
| Session fixation | Application keeps an attacker-known ID after login | Regenerate authenticated session credential |
| CSRF | Browser sends ambient credentials on an unwanted action | CSRF controls and safe method design |
| XSS | Attacker runs script in the application's origin | Prevent injection; limit token exposure |
| Token substitution | Credential for another purpose accepted here | Explicit issuer/audience/type/algorithm policy |
| Refresh replay | An old credential is used again | Rotation, reuse detection and family policy |

These defenses solve different problems. A strong password hash does not prevent a stolen session cookie from being used, and JWT signatures do not make a browser immune to XSS.

### A complete login service needs surrounding controls

Credential verification should sit behind bounded input, TLS, abuse controls and safe logging. Sensitive operations may require reauthentication even with an otherwise valid session.

This learning service has one public fixture account and no registration, recovery, MFA, abuse-throttling deployment or account-lockout system. Its examples isolate mechanisms; they are not a ready-made identity product.

---

## 7.3 Password storage and verification

Store a password verifier, not the plaintext password. When the user logs in, derive a candidate verifier using the stored salt and configured work factor, then compare it safely.

```text
registration/setup:
  password + random salt + configured cost -> password verifier
  persist algorithm/version, salt and verifier

login:
  submitted password + stored salt + configured cost -> candidate
  compare candidate with stored verifier
```

A hash is not “decrypted” during login. An attacker with the stored verifier can guess candidate passwords and check them; the cost of each guess matters.

A salt gives accounts independent derivations, preventing one precomputed result from directly matching all users with the same password. It is stored alongside the verifier and does not need to be secret.

A pepper is additional secret material kept separately from the verifier database. It introduces secret management and rotation/recovery considerations. It does not replace a salt or a suitable password-hashing algorithm.

OWASP prefers Argon2id and documents scrypt as an alternative when Argon2id is unavailable. Fast SHA-256 alone is unsuitable for human-password storage. See [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

### Why this example uses scrypt

The recorded Node runtime supplies scrypt as a built-in async API. The example uses N=131072, r=8, p=1, a 16-byte random salt and a 64-byte derived value, with a 256 MiB maxmem setting.

These are a selected configuration consistent with the cited scrypt fallback. maxmem is an API memory ceiling, not a measurement of actual process memory. We do not benchmark or recommend an unmeasured requests-per-second capacity.

The async call uses worker-pool resources. It avoids executing the expensive derivation synchronously on the event-loop thread, but many concurrent login attempts can still exhaust CPU, memory and pool capacity. M4's worker-pool discussion applies.

### Input and comparison policy

The demonstration accepts non-empty passwords up to 256 UTF-8 bytes at its verification boundary. That bound protects the example's input/work path; it is not a recommended password-enrollment policy.

It does not trim or normalize passwords. Surrounding whitespace changes the password. Enrollment policy should support long passwords and managers, consider compromised-password checks and follow the identity system's requirements.

The final derived buffers have equal length and are compared with timingSafeEqual. That does not prove that the whole login endpoint has identical timing for every account or failure.

Unknown account names still perform a derivation against the fixture/dummy verifier and get the same public invalid_credentials response as a wrong password. The tests verify public responses, not timing indistinguishability.

### Complete password example

File: examples/resume-skills/module-7-authentication/password.mjs.

```javascript
import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';

const scrypt = promisify(scryptCallback);
const cost = { N: 131072, r: 8, p: 1, maxmem: 256 * 1024 * 1024 };

function passwordBytes(password) {
  if (typeof password !== 'string' || Buffer.byteLength(password, 'utf8') < 1 ||
      Buffer.byteLength(password, 'utf8') > 256) throw new TypeError('Unsupported password input.');
  return password;
}
export async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const derived = await scrypt(passwordBytes(password), salt, 64, cost);
  return { scheme: 'scrypt-demo-v1', salt, derived: derived.toString('hex') };
}
export async function verifyPassword(password, record) {
  if (record?.scheme !== 'scrypt-demo-v1' || !/^[a-f0-9]{32}$/.test(record.salt) ||
      !/^[a-f0-9]{128}$/.test(record.derived)) throw new TypeError('Invalid stored credential.');
  const derived = await scrypt(passwordBytes(password), record.salt, 64, cost);
  return timingSafeEqual(derived, Buffer.from(record.derived, 'hex'));
}
```

The record's scheme fixes the cost/version used by this small example. A production verifier typically encodes algorithm parameters and supports deliberate rehash-on-login migration. Do not accept arbitrary expensive hashing parameters from a client.

---

## 7.4 Server-side sessions: what happens after login?

A server-side session associates a hard-to-guess credential with trusted server state.

```text
POST login + credentials
  -> verify password
  -> generate fresh random session credential
  -> store session record under credential hash
  <- Set-Cookie with opaque credential

GET profile + Cookie
  -> extract exactly one supported cookie
  -> hash credential and look up session
  -> check idle/absolute expiry
  -> establish subject
  <- public profile
```

The browser carries the opaque credential. It does not carry a trusted userId merely because a cookie contains that text.

Our example generates 32 random bytes and encodes them as 43 base64url characters. It stores SHA-256 of the credential as the Map key.

Fast hashing is reasonable here because the input is a high-entropy random bearer credential, not a human-chosen password. Hashing protects stored token values from direct reuse if the token-record table alone leaks; it does not protect an attacker who already captured the raw cookie or controls the application.

### Session fixation

On successful re-login, the service issues a fresh credential and invalidates the presented previous one. It never promotes an arbitrary client-selected session ID into an authenticated session.

The verifier confirms that the old credential stops working and the new one resolves the user.

This is not “log out all devices.” Other independently established sessions are not automatically removed. Device-wide/session-wide revocation needs an explicit index and policy.

### Idle versus absolute timeout

The selected policy is:

- **Idle timeout:** 30 seconds without accepted session activity.
- **Absolute timeout:** 120 seconds after creation, regardless of activity.
- **Cookie Max-Age:** 120 seconds; the server remains authoritative for session validity.

Authenticated session lookups update lastSeen. They cannot move createdAt, so continued activity does not remove the absolute bound.

Tests inject clock values to check the exact boundaries. These short lifetimes make the mechanism visible; they are not universal production recommendations.

### Logout has two parts

Delete/invalidate the server record and expire the browser cookie. Expiring only the browser cookie leaves a copied credential usable elsewhere.

The clearing cookie uses the same name and Path, with Max-Age=0. Our cookie has no Domain attribute; changing identity attributes while clearing can leave another cookie intact.

Reference: [OWASP session lifecycle guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

---

## 7.5 Cookies describe transport and browser policy

A cookie is a browser storage/transport mechanism. It can contain an opaque session credential, a JWT or another application value. “Cookies versus JWT” mixes storage/transport with credential format.

| Attribute | What it contributes |
| --- | --- |
| Secure | Restricts sending to secure transport under browser rules |
| HttpOnly | Prevents ordinary script access through document.cookie |
| SameSite | Restricts cross-site cookie sending according to its policy |
| Path | Selects request paths; it is not an authorization boundary |
| Domain omitted | Makes the cookie host-only |
| Max-Age | Controls cookie persistence; does not override server revocation |
| __Host- prefix | Requires Secure, Path=/ and no Domain in supporting browsers |

Reference: [Set-Cookie documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).

### HttpOnly limits one XSS consequence

HttpOnly makes direct cookie reading harder for injected scripts. A script running in your origin can still issue authenticated requests and read permitted responses. Prevent XSS rather than treating HttpOnly as complete containment.

Similarly, Secure does not make JavaScript-readable storage safe from XSS, and it does not replace TLS for the rest of the application.

### Same-site is not same-origin

An origin includes scheme, host and port. Site-based rules use a different grouping, including scheme and registrable domain. Two subdomains can be different origins yet belong to the same site.

SameSite=Lax permits some cross-site top-level safe navigations. Do not put state changes behind GET and assume SameSite blocks them all.

OAuth redirects also interact with cookie policy. A blanket “always use Strict for every cookie” can break an intended cross-site login flow. Use the library's supported correlation-cookie policy for the actual response mode and deployment.

### Browser fetch behavior

A same-origin browser request normally carries same-origin cookies. Cross-origin credentialed requests need an appropriate credentials mode and a compatible server CORS policy.

Setting credentials:"include" does not manufacture an Authorization: Bearer header. Likewise, a browser does not expose Set-Cookie to frontend JavaScript as a normal readable response header.

Our Node HTTP verifier manually reads Set-Cookie and supplies Cookie. It checks header contracts without pretending to be a browser cookie jar.

---

## 7.6 CSRF and login boundaries

With cookie authentication, the browser can attach credentials automatically. A malicious page can try to induce a state-changing request without knowing the credential value.

The session demonstration uses:

1. POST for login/logout.
2. An exact configured trusted Origin for every POST.
3. A random synchronizer CSRF token tied to the session for logout.
4. SameSite=Lax and a host-only HttpOnly cookie as additional browser controls.

The token is returned to a same-origin client and sent back in X-CSRF-Token. Server-side comparison checks that it belongs to the session.

The suite confirms that a cookie without a CSRF token cannot log out, and that a correct CSRF token with an untrusted Origin is also rejected.

### Origin is not identity

An arbitrary non-browser client can forge an Origin header. The Origin check is a browser-request defense, not a substitute for password/session/token verification.

This example rejects missing and null Origin values on POST because it has a deliberately narrow first-party contract. A native client/provider callback may need a different documented policy.

### Login CSRF also matters

An unwanted login can attach a victim's browser to the attacker's account. Protect login initiation/correlation as well as authenticated mutations. Our first-party JSON login requires the configured Origin before checking credentials.

A deployed design should use a framework's supported CSRF strategy and verify proxy/origin configuration. M8 examines synchronizer/double-submit strategies, CORS, XSS and tenant boundaries more deeply.

Bearer credentials manually placed in Authorization are not ordinarily ambient browser credentials. However, moving a bearer token into an automatically sent cookie brings cookie/CSRF considerations back. The risk follows transport and application behavior, not the JWT label.

---

## 7.7 Sessions and JWTs: compare complete designs

| Design concern | Opaque server-side session | Self-contained signed JWT access token |
| --- | --- | --- |
| Credential content | Random identifier | Claims plus integrity protection |
| Ordinary verification | Session-store lookup and expiry | Signature and expected-claim validation |
| Central state | Session records | Keys/policy; revocation may add state |
| Immediate logout | Invalidate authoritative record | Requires additional state/checks or wait for expiry |
| Permission freshness | Can resolve current policy on access | Embedded claims can become stale |
| Multiple instances | Need shared/coordinated session state | Need consistent trusted keys/policy |
| Credential disclosure | Bearer session can be reused | Bearer JWT can be reused |
| Browser storage | Often HttpOnly cookie | May be cookie, memory or another deliberate arrangement |

JWT is a format, not an architectural command to remove all state. A JWT application often still has users, refresh sessions, revocation records and permission checks.

For a first-party browser application, an opaque session with a shared store can be straightforward. For multiple APIs that must validate access independently, short-lived signed access tokens may be useful. Choose based on trust boundaries and revocation needs.

Do not claim that sessions “cannot scale.” Shared stores, expiry and failure policies can support many instances. Conversely, JWT verification has cryptographic cost and key-distribution requirements; it is not free unlimited scale.

A modular monolith may need neither a separate identity microservice nor a custom token framework. Understand the maintained framework's session behavior first.

---

## 7.8 JWT structure: readable does not mean trusted

A commonly used signed JWT in JWS compact serialization has three parts:

```text
base64url(protected header).base64url(claims).signature
```

The first two parts are encoded, not encrypted. Anyone holding the token can decode them. Do not put a password, API secret or confidential personal data in a signed-only payload.

| Claim/header | Typical purpose |
| --- | --- |
| iss | Expected issuer |
| sub | Subject identifier within issuer context |
| aud | Intended recipient(s) |
| exp | Expiry time |
| nbf | Not valid before |
| iat | Issuance time |
| jti | Token identifier; revocation/deduplication policy may use it |
| alg | Cryptographic algorithm identifier |
| kid | Key-selection identifier within trusted key policy |
| typ | Token-type/purpose convention |

JWT time claims use NumericDate seconds. The service converts its millisecond clock before issuing claims. Confusing milliseconds and seconds can create a dramatically wrong lifetime.

These claims are not all universally mandatory for every JWT. Our access-token profile explicitly requires sub, iat, exp and jti and validates issuer/audience/type. An application must define its profile.

Reference: [JWT specification, RFC 7519](https://www.rfc-editor.org/rfc/rfc7519.html).

### Decode versus verify

Decoding only parses untrusted data. The verifier test changes sub to attacker, confirms that decoding reads it, and then confirms that access verification rejects the modified token.

Never populate a trusted req.user from decodeJwt alone.

In the example, jose performs JOSE verification; the application supplies its allowlist, trust anchor and claim policy. It does not implement custom signature parsing.

### Symmetric versus asymmetric signing

With HMAC, the shared secret can both create and verify the MAC. Every verifier holding that secret is also capable of minting tokens.

With an asymmetric signature such as the example's RS256, the issuer holds the private key while verifiers use the public key. Distributing a public verification key does not distribute signing authority.

Neither choice encrypts a signed JWT payload. Algorithm choice, minimum key properties and deployment support must follow a maintained library and current policy.

---

## 7.9 JWT verification is a policy, not one cryptographic call

The access service accepts a credential only if it satisfies the selected contract:

```text
supported compact credential
  -> RS256 allowlist
  -> fixed trusted public key
  -> valid signature
  -> expected issuer
  -> audience contains placement-api
  -> expected at+jwt type
  -> required claims and expiry/not-before checks
  -> known subject, bounded lifetime and issued-at policy
  -> expected demo key ID
  -> established identity
```

The algorithm in the incoming header is untrusted input. It must not choose an unrestricted verification path. The tests reject alg:none and an HS256 credential at the RS256 boundary.

A valid signature from the right key is insufficient if the token was issued for another API or another purpose. The suite rejects wrong issuer, audience, type, key ID, missing claims and future/not-yet-valid values.

The exact 60-second lifetime cap and zero clock tolerance are selected demo policies. Real services need deliberate bounded skew tolerance and synchronized operational clocks.

Reference: [JWT best practices, RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html) and [jose jwtVerify](https://github.com/panva/jose/blob/main/docs/jwt/verify/functions/jwtVerify.md).

### Trusted key discovery

A production verifier may use a JWKS endpoint from configured issuer metadata. The key ID selects among those trusted keys; it does not make arbitrary token-supplied keys or URLs trustworthy.

Do not fetch an attacker-selected jku URL or trust an arbitrary embedded public key merely because it appeared in a token header. Configure discovery/trust and bound cache/unknown-key behavior.

Our service uses a fixed generated key pair, with a deliberately fixed expected kid. It does not implement remote discovery or rotation. In tests, unexpected kid is an application-policy rejection even when the same trusted key signed the token.

### Rotation and revocation are different

Key rotation changes signing/verification material. Normal rotation can retain old public keys until relevant tokens expire. Removing a compromised key can invalidate many users' tokens at once.

Revoking one user's session is a different operation. It may use a session/version lookup, a jti denylist or token introspection. Those choices add state and consistency requirements.

Access checks in this demo do not consult refresh-family revocation. That limit is visible in the logout tests rather than hidden behind the word stateless.

---

## 7.10 Access tokens, refresh tokens and rotation

An access token is presented to an API for an operation. A refresh token is presented to the authorization/session service to obtain new access credentials.

In our example:

- Access tokens are signed JWTs valid for 60 seconds.
- Refresh tokens are opaque 32-byte random credentials.
- The server stores refresh credential hashes and family state.
- A family has a fixed 300-second absolute lifetime.
- Successful refresh consumes the current credential and returns a new one.
- Reusing a consumed credential revokes the entire family.

These lifetimes and policies are teaching choices. Real provider behavior must be read and tested for that provider.

### Why rotate?

```text
R0 issued
  -> refresh with R0
     mark R0 used
     issue R1

later request using R0
  -> recognize consumed credential
  -> revoke family including R1
```

Retaining consumed-token records lets the server distinguish a recognized old credential from a random unknown one. Deleting all history immediately loses that signal.

A random unknown credential does not revoke an unrelated family. Otherwise an attacker could invalidate users simply by sending guesses.

### The consume-and-successor step must be atomic

Our Map update has no await between checking/consuming the old credential and creating the successor. That works only inside this one process.

A durable implementation needs a shared atomic update/transaction and a uniqueness/state model that prevents two active successors. A JavaScript check in one instance cannot coordinate several instances.

### Concurrent refresh is a user-experience problem too

Two browser tabs can legitimately send R0 concurrently. The strict policy yields one successful rotation and then a reuse rejection that revokes the family. The verifier proves the winner's successor is no longer usable.

Coordinate refresh attempts in the client/BFF and carefully design any server-side retry/grace policy. Blind grace periods can give stolen credentials a replay window.

If a response containing R1 is lost, retrying R0 has an uncertain outcome. M6's retry reasoning applies: a rotation protocol needs a defined recovery/relogin policy, not an unconditional retry loop.

### Revoking refresh does not erase issued access

The server can refuse future refresh while an already issued JWT remains valid until expiry. The HTTP suite confirms that behavior, then advances the clock and confirms access rejection at expiry.

For immediate access invalidation, add an authoritative revocation/introspection/session-version check. A refresh-family flag alone does not supply it.

Current OAuth security guidance covers refresh replay protection and authorization-code security; see [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

---

## 7.11 Complete identity service

File: examples/resume-skills/module-7-authentication/identity.mjs.

This service deliberately separates session lookup from bearer-token verification. Session login and token login are two independent demonstration modes; logging out of one does not silently revoke all credentials from the other.

The generated signing key is ephemeral. Restarting this example loses session/refresh state and replaces the default key. Production keys and session records need managed persistence and rotation.

```javascript
import { createHash, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { SignJWT, jwtVerify, generateKeyPair } from 'jose';
import { verifyPassword } from './password.mjs';

export class AuthError extends Error {
  constructor(status, code) { super(code); Object.assign(this, { status, code }); }
}
const deny = (code = 'unauthenticated') => { throw new AuthError(401, code); };
const opaque = () => randomBytes(32).toString('base64url');
const validOpaque = token => typeof token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(token);
const digest = token => createHash('sha256').update(token).digest('hex');
const equal = (a, b) => typeof a === 'string' && typeof b === 'string' &&
  Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b));

export async function createIdentity({
  passwordRecord, now = Date.now, keyPair,
  issuer = 'https://identity.example.test', audience = 'placement-api',
} = {}) {
  if (!passwordRecord) throw new TypeError('Supply a fixture credential record.');
  const keys = keyPair ?? await generateKeyPair('RS256');
  const user = { id: 'user-1', email: 'learner@example.test', name: 'Placement Learner' };
  const sessions = new Map();
  const families = new Map();
  const refreshRecords = new Map();

  async function login(email, password) {
    // The single fixture record doubles as the dummy record for unknown accounts.
    const correct = await verifyPassword(password, passwordRecord);
    if (email !== user.email || !correct) deny('invalid_credentials');
    return user.id;
  }
  function makeSession(subject, oldToken) {
    if (subject !== user.id) deny();
    if (validOpaque(oldToken)) sessions.delete(digest(oldToken));
    const token = opaque();
    const createdAt = now();
    const record = { subject, csrf: opaque(), createdAt, lastSeen: createdAt };
    sessions.set(digest(token), record);
    return { token, csrf: record.csrf };
  }
  function getSession(token) {
    if (!validOpaque(token)) deny();
    const key = digest(token);
    const record = sessions.get(key);
    const current = now();
    if (!record) deny();
    if (current - record.lastSeen >= 30_000 || current - record.createdAt >= 120_000) {
      sessions.delete(key);
      deny('session_expired');
    }
    record.lastSeen = current;
    return record;
  }
  function sessionView(token) {
    const record = getSession(token);
    return { user: { ...user }, csrfToken: record.csrf };
  }
  function logoutSession(token, csrf) {
    const record = getSession(token);
    if (!equal(csrf, record.csrf)) throw new AuthError(403, 'csrf_rejected');
    sessions.delete(digest(token));
  }
  async function issueAccess(subject) {
    if (subject !== user.id) deny();
    const seconds = Math.floor(now() / 1000);
    return new SignJWT({})
      .setProtectedHeader({ alg: 'RS256', typ: 'at+jwt', kid: 'demo-rsa-1' })
      .setIssuer(issuer).setAudience(audience).setSubject(subject)
      .setIssuedAt(seconds).setExpirationTime(seconds + 60).setJti(randomUUID())
      .sign(keys.privateKey);
  }
  async function accessView(token) {
    try {
      const { payload, protectedHeader } = await jwtVerify(token, keys.publicKey, {
        algorithms: ['RS256'], typ: 'at+jwt', issuer, audience,
        requiredClaims: ['sub', 'iat', 'exp', 'jti'],
        currentDate: new Date(now()), clockTolerance: 0,
      });
      const seconds = Math.floor(now() / 1000);
      if (payload.sub !== user.id || typeof payload.jti !== 'string' || !payload.jti ||
          !Number.isSafeInteger(payload.iat) || payload.iat > seconds ||
          !Number.isSafeInteger(payload.exp) || payload.exp <= payload.iat ||
          payload.exp - payload.iat > 60 || protectedHeader.kid !== 'demo-rsa-1') deny();
      return { user: { ...user } };
    } catch { deny('invalid_access_token'); }
  }
  function makeRefresh(subject) {
    if (subject !== user.id) deny();
    const familyId = randomUUID();
    const token = opaque();
    families.set(familyId, { subject, absoluteAt: now() + 300_000, revoked: false });
    refreshRecords.set(digest(token), { familyId, used: false });
    return token;
  }
  function rotateRefresh(token) {
    if (!validOpaque(token)) deny('invalid_refresh_token');
    const record = refreshRecords.get(digest(token));
    const family = record && families.get(record.familyId);
    if (!family || family.revoked || now() >= family.absoluteAt) deny('invalid_refresh_token');
    if (record.used) {
      family.revoked = true;
      deny('refresh_reuse');
    }
    // No await separates consumption from successor creation in this demo store.
    record.used = true;
    const next = opaque();
    refreshRecords.set(digest(next), { familyId: record.familyId, used: false });
    return { subject: family.subject, refreshToken: next };
  }
  function revokeRefresh(token) {
    if (!validOpaque(token)) return;
    const record = refreshRecords.get(digest(token));
    if (record) families.get(record.familyId).revoked = true;
  }
  return {
    login, makeSession, sessionView, logoutSession,
    issueAccess, accessView, makeRefresh, rotateRefresh, revokeRefresh,
  };
}
```

### Architectural limits visible in this code

Maps are private to one process. Used refresh records are retained to recognize replay, and expiry is checked on use; there is no periodic cleanup or bounded production session-store design.

The refresh endpoint rotates first and then signs the response's access token. A signing/response failure can therefore leave the client without the successor credential. Our tests do not inject that failure, and the strict policy requires an explicit recovery/relogin strategy.

A production credential lifecycle must coordinate durable state, failure handling, storage cleanup and service limits. These are next design steps, not guarantees provided by the learning implementation.

---

## 7.12 HTTP adapter and endpoint contract

| Endpoint | Credential/input | Observable behavior |
| --- | --- | --- |
| POST /session/login | JSON email/password; trusted Origin | Fresh cookie and CSRF token |
| GET /session/me | Session cookie | Public user and session CSRF token |
| POST /session/logout | Cookie, CSRF token, trusted Origin | Server revocation, clearing cookie, 204 |
| POST /tokens/login | JSON email/password; trusted Origin | Access/refresh pair |
| POST /tokens/refresh | JSON refreshToken; trusted Origin | Rotated pair or 401 |
| POST /tokens/logout | JSON refreshToken; trusted Origin | Revoke family; 204 |
| GET /api/me | Authorization: Bearer access token | Verified public user or 401 |

These are first-party fixture login endpoints. **/tokens/login is not an OAuth resource-owner-password grant implementation.** The OAuth protocol model appears separately below.

All responses use Cache-Control:no-store. Login input has a 2048-byte body bound and rejects unknown fields. Query-string credential transport is rejected. Body allocation is bounded while excess bytes are drained; it is not an upload bandwidth limit.

401 responses include a challenge. Bearer is the access endpoint's scheme. Session is this example's custom challenge label, not a standardized browser session-login protocol.

The adapter requires exactly one supported named cookie, rejecting duplicate values rather than letting parsing order decide the identity. Session cookies do not automatically authenticate the bearer route, and a bearer header does not authenticate the session route.

File: examples/resume-skills/module-7-authentication/server.mjs.

```javascript
import { createServer } from 'node:http';
import { AuthError } from './identity.mjs';

async function body(req) {
  if ((req.headers['content-type'] ?? '').split(';')[0].trim().toLowerCase() !== 'application/json' ||
      (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity'))
    throw new AuthError(415, 'unsupported_body_format');
  const chunks = [];
  let bytes = 0;
  for await (const chunk of req) {
    bytes += chunk.length;
    if (bytes <= 2048) chunks.push(chunk);
  }
  if (bytes > 2048) throw new AuthError(413, 'body_too_large');
  try {
    const value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error();
    return value;
  } catch { throw new AuthError(400, 'invalid_json_object'); }
}
function fields(value, allowed) {
  if (Object.keys(value).some(key => !allowed.includes(key)) ||
      allowed.some(key => typeof value[key] !== 'string' || !value[key]))
    throw new AuthError(400, 'invalid_input');
  if (value.password && Buffer.byteLength(value.password, 'utf8') > 256)
    throw new AuthError(400, 'invalid_input');
  return value;
}
function cookieToken(header, name) {
  const matches = (header ?? '').split(';').map(s => s.trim()).filter(s => s.startsWith(name + '='));
  if (matches.length > 1) throw new AuthError(400, 'ambiguous_cookie');
  return matches[0]?.slice(name.length + 1);
}
export function createAuthServer({
  identity, trustedOrigin = 'https://app.example.test', secureCookies = true,
} = {}) {
  if (!identity) throw new TypeError('Supply the identity service.');
  const cookieName = secureCookies ? '__Host-sid' : 'sid';
  const cookie = (token, clear = false) =>
    cookieName + '=' + token + '; Path=/; HttpOnly; SameSite=Lax; Max-Age=' +
    (clear ? '0' : '120') + (secureCookies ? '; Secure' : '');
  const server = createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, value, headers = {}) => {
      res.writeHead(status, {
        ...(value === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }),
        ...headers,
      });
      res.end(value === undefined ? undefined : JSON.stringify(value));
    };
    try {
      const url = new URL(req.url, 'http://localhost');
      const routes = {
        '/session/login': 'POST', '/session/me': 'GET', '/session/logout': 'POST',
        '/tokens/login': 'POST', '/tokens/refresh': 'POST', '/tokens/logout': 'POST',
        '/api/me': 'GET',
      };
      const method = routes[url.pathname];
      if (!method) throw new AuthError(404, 'not_found');
      if (req.method !== method) return send(405, { code: 'method_not_allowed' }, { Allow: method });
      if (url.search) throw new AuthError(400, 'unexpected_query');
      if (method === 'POST' && req.headers.origin !== trustedOrigin)
        throw new AuthError(403, 'origin_rejected');

      if (url.pathname === '/session/login' || url.pathname === '/tokens/login') {
        const input = fields(await body(req), ['email', 'password']);
        const subject = await identity.login(input.email, input.password);
        if (url.pathname === '/session/login') {
          const prior = cookieToken(req.headers.cookie, cookieName);
          const session = identity.makeSession(subject, prior);
          return send(200, { authenticated: true, csrfToken: session.csrf }, {
            'Set-Cookie': cookie(session.token),
          });
        }
        return send(200, {
          accessToken: await identity.issueAccess(subject),
          refreshToken: identity.makeRefresh(subject),
          tokenType: 'Bearer', expiresIn: 60,
        });
      }
      if (url.pathname === '/session/me')
        return send(200, identity.sessionView(cookieToken(req.headers.cookie, cookieName)));
      if (url.pathname === '/session/logout') {
        identity.logoutSession(cookieToken(req.headers.cookie, cookieName), req.headers['x-csrf-token']);
        return send(204, undefined, { 'Set-Cookie': cookie('', true) });
      }
      if (url.pathname === '/tokens/refresh') {
        const { refreshToken } = fields(await body(req), ['refreshToken']);
        const rotated = identity.rotateRefresh(refreshToken);
        return send(200, {
          accessToken: await identity.issueAccess(rotated.subject),
          refreshToken: rotated.refreshToken, tokenType: 'Bearer', expiresIn: 60,
        });
      }
      if (url.pathname === '/tokens/logout') {
        const { refreshToken } = fields(await body(req), ['refreshToken']);
        identity.revokeRefresh(refreshToken);
        return send(204);
      }
      const authorization = req.headers.authorization ?? '';
      const match = /^Bearer ([^\s,]+)$/i.exec(authorization);
      if (!match) throw new AuthError(401, 'invalid_access_token');
      return send(200, await identity.accessView(match[1]));
    } catch (error) {
      const known = error instanceof AuthError;
      const status = known ? error.status : 500;
      send(status, { code: known ? error.code : 'internal_error' }, status === 401 ? {
        'WWW-Authenticate': req.url === '/api/me' ? 'Bearer realm="placement-demo"' : 'Session realm="placement-demo"',
      } : {});
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
    }
  });
  server.requestTimeout = 10_000;
  server.headersTimeout = 5000;
  return server;
}
```

The launcher selects trustedOrigin=http://127.0.0.1:3107 and secureCookies=false. That produces a sid cookie for the explicit loopback HTTP demo. The secure test configuration uses __Host-sid and Secure. Do not apply the launcher configuration to a deployed public login service.

---

## 7.13 OAuth 2.0: delegated access

OAuth lets a client obtain limited access to a resource on behalf of a resource owner without collecting that owner's password for the other service.

| Role | Responsibility | Example |
| --- | --- | --- |
| Resource owner | Grants/controls access | The user |
| Client | Requests and uses delegated access | Your placement application |
| Authorization server | Authenticates/authorizes and issues credentials | A configured identity/provider service |
| Resource server | Accepts access credentials for protected resources | A provider API |

The authorization server and resource server can belong to the same organization, but their roles remain distinct.

The client ID identifies the application registration; it is not a password. A confidential backend can protect client credentials. Browser code and mobile binaries cannot reliably keep a distributed client secret confidential.

### Authorization code with PKCE

```text
1. Application creates state + PKCE verifier/challenge
2. Browser redirects to configured authorization endpoint
3. Provider authenticates user and obtains applicable consent
4. Browser returns to registered callback with code + state
5. Application validates callback correlation/binding
6. Client exchanges code + verifier at token endpoint
   (and authenticates as a confidential client when required)
7. Client receives tokens and calls intended resource server
```

The authorization code is a short-lived, one-use intermediate credential. It is not the access token used for ordinary API requests.

The registered redirect must follow the provider's exact matching rules. Avoid wildcard/prefix checks or an arbitrary return URL from request input. After login, any application return-path handling needs its own safe policy.

Current security guidance favors authorization-code designs with PKCE and rejects the resource-owner-password credentials grant. The old implicit token-in-redirect pattern is not the default to copy from tutorials. Reference: [OAuth security BCP, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

### PKCE: prove continuity of the initiating client

Generate a high-entropy verifier and send its S256 challenge in the authorization request:

```text
challenge = BASE64URL(SHA256(ASCII(verifier)))
```

At the token endpoint, submit the verifier. The server checks that it matches the challenge associated with the authorization code. An intercepted code alone is insufficient.

S256 uses SHA-256 and base64url without padding. The verifier's allowed length/character rules are part of the protocol. The test checks the independently published RFC example rather than only comparing two functions written together.

Reference: [PKCE, RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html).

PKCE does not replace a confidential client's authentication, token validation, state/transaction binding or redirect restrictions.

### state: correlate the browser transaction

A random state value ties the returned callback to a pending login/delegation request. Keep it bound to the initiating browser/session, expire it and consume it appropriately.

Checking that state merely exists somewhere in a global Map is insufficient if another browser can use it. The local model checks both the state and browser-session binding.

Store the verifier securely with that transaction. Do not put it in the authorization URL. The model exposes it to the test caller for inspection; a BFF would keep it on the backend.

### The local model's exact scope

The following state machine verifies challenge/code binding, redirect/client matching, browser-bound state, one-use state/code and selected expiry rules.

It assumes provider user authentication and consent already happened. It does not implement discovery, HTTP authorization/token endpoints, client authentication, TLS, scopes negotiation, provider account login, access-token issuance or OIDC ID-token validation.

The returned delegatedSubject/scope object is a modeled result, not a real OAuth token response.

File: examples/resume-skills/module-7-authentication/oauth-model.mjs.

```javascript
import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';

const random = () => randomBytes(32).toString('base64url');
const hash = value => createHash('sha256').update(value, 'ascii').digest('base64url');
const same = (a, b) => typeof a === 'string' && typeof b === 'string' &&
  Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b));

export const pkceS256 = verifier => {
  if (typeof verifier !== 'string' || !/^[A-Za-z0-9._~-]{43,128}$/.test(verifier))
    throw new Error('invalid_verifier');
  return hash(verifier);
};

// Protocol model only: no browser, discovery, TLS, provider login or OIDC validation.
export function createOAuthModel({ now = Date.now } = {}) {
  const clientId = 'placement-bff';
  const redirectUri = 'https://app.example.test/oauth/callback';
  const transactions = new Map();
  const codes = new Map();
  function start(browserSession) {
    if (typeof browserSession !== 'string' || !browserSession) throw new Error('missing_browser_binding');
    const state = random(), verifier = random();
    transactions.set(state, { browserSession, verifier, expiresAt: now() + 60_000 });
    return {
      state, verifier,
      request: { clientId, redirectUri, state, codeChallenge: pkceS256(verifier), codeChallengeMethod: 'S256' },
    };
  }
  function authorize(request) {
    if (request.clientId !== clientId || request.redirectUri !== redirectUri ||
        request.codeChallengeMethod !== 'S256' || !/^[A-Za-z0-9_-]{43}$/.test(request.codeChallenge))
      throw new Error('invalid_authorization_request');
    // The model assumes provider authentication/consent already happened.
    const code = random();
    codes.set(code, { challenge: request.codeChallenge, redirectUri, clientId, expiresAt: now() + 30_000 });
    return { code, state: request.state };
  }
  function callback({ state, code }, browserSession) {
    const transaction = transactions.get(state);
    if (!transaction || transaction.browserSession !== browserSession || now() >= transaction.expiresAt)
      throw new Error('invalid_state');
    transactions.delete(state); // one-use correlation even if later exchange fails
    return { code, verifier: transaction.verifier, clientId, redirectUri };
  }
  function exchange({ code, verifier, clientId: suppliedClient, redirectUri: suppliedRedirect }) {
    const record = codes.get(code);
    if (!record || now() >= record.expiresAt) throw new Error('invalid_grant');
    if (record.clientId !== suppliedClient || record.redirectUri !== suppliedRedirect ||
        !same(record.challenge, pkceS256(verifier))) throw new Error('invalid_grant');
    codes.delete(code); // consume only after checks in this selected model policy
    return { delegatedSubject: 'provider-user-1', scope: 'tasks:read' };
  }
  return { start, authorize, callback, exchange };
}
```

The model intentionally does not consume a code on a failed verifier check, but consumes it after a valid exchange. It consumes callback state before exchange. These are explicit model choices, not a complete implementation of every provider's error/recovery behavior.

---

## 7.14 OAuth versus OpenID Connect

OAuth concerns delegated access. OpenID Connect (OIDC) adds an authentication layer, including an ID token describing the authentication event and subject.

| Credential | Intended consumer/use | Typical audience |
| --- | --- | --- |
| Access token | Resource API authorizes delegated access | Intended API/resource |
| Refresh token | Token service renews access | Authorization/session service |
| ID token | Client validates authentication information | Registered client |
| Local session cookie | Your application resolves its session | Your application |

An access token can be opaque or a JWT. An ID token is not a replacement access token for whichever API you want to call.

In a usual OIDC code flow, the client requests openid and validates the returned ID token under the provider/profile rules. It checks trusted issuer, signature/allowed algorithms, audience/client binding, expiry and applicable nonce/other claims. If nonce was sent, validate the returned nonce against the stored transaction.

state correlates a browser authorization transaction; nonce binds an OIDC ID token to the request; PKCE binds code redemption to the verifier. They are related defenses with different roles.

Reference: [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html).

### Mapping external identity to your user

Use a trusted issuer plus subject identifier as the external identity key. An email can change, be absent or have provider-specific verification semantics.

Do not automatically merge accounts merely because an untrusted/unchecked email string matches. Account linking is an explicit authenticated workflow with its own takeover risks.

After a successful provider login, your application may create its own session. Provider access/refresh credentials, an ID token and your application cookie then have separate lifetimes and logout behavior.

The local OAuth model does not validate ID tokens or demonstrate account linking. Use a maintained OIDC client and the actual provider's discovery/validation contract when implementing that flow.

---

## 7.15 JWS, JWE and HKDF: resume-specific depth

### Signing and encryption solve different problems

A signed JWT in JWS form protects integrity/authenticity under the configured key policy. Its payload remains readable.

JWE adds authenticated encryption of content. Compact JWE has five components:

```text
protected-header.encrypted-key.iv.ciphertext.authentication-tag
```

With direct key management (alg=dir), the encrypted-key component is empty. It still occupies its position, so compact serialization has five parts.

Our jose tests use dir with A256GCM and a fresh 32-byte symmetric key. They decrypt the demonstration claim, reject a wrong key and enforce expiry.

Reference: [JWE specification, RFC 7516](https://www.rfc-editor.org/rfc/rfc7516.html).

Encryption does not supply application permissions or remove replay risk. Whoever possesses a still-valid encrypted bearer credential can present it without understanding the contents.

Depending on the profile, a JWE may contain a signed JWT that needs separate inner verification. Do not assume “decryption succeeded” proves every expected issuer/audience/purpose check was done.

### What HKDF does

HKDF derives key material from input key material, a salt and context information. Changing context can separate keys for different purposes. It is not a slow password-hashing substitute.

The suite derives 32-byte keys from random input material. The same inputs/context reproduce the same key, while a different context produces a different result in the checked example. It does not print those key values.

Do not replace password hashing with HKDF merely because both involve derivation. Their intended inputs and resistance goals differ.

### Auth.js/NextAuth is version-specific

The current Auth.js JWT documentation describes encrypted JWTs using A256CBC-HS512 by default and secret-derived encryption keys. The inspected implementation derives keys with HKDF-SHA256, including salt/context and algorithm-dependent output length.

References: [Auth.js JWT documentation](https://authjs.dev/reference/core/jwt) and [current implementation](https://raw.githubusercontent.com/nextauthjs/next-auth/main/packages/core/src/jwt.ts).

That does not establish which version/configuration an earlier NextAuth project used. Next.js 14 on the resume does not identify the Auth.js/NextAuth version.

Our A256GCM example is a JOSE demonstration, not an Auth.js-compatible session decoder. If your project tried to decode an encrypted framework cookie as a three-part signed access token, explain the format/key-derivation mismatch before changing secrets at random.

Useful debugging sequence: identify the exact package version and session strategy; inspect the configured algorithm/format; follow its supported secret/salt derivation; use the framework's server-side session API; verify the intended token audience and purpose.

Do not copy a moving main-branch implementation into a production custom decoder without pinning and compatibility verification.

---

## 7.16 Browser architecture and the BFF pattern

A Backend for Frontend (BFF) gives the browser an application-specific backend boundary. For authentication, it can perform provider exchanges and keep provider credentials on the backend while exposing a local browser session.

```text
browser
  -- HttpOnly application session cookie -->
BFF
  -- provider/API access credential -->
resource API

login callback
  -> BFF validates transaction and provider response
  -> BFF retains provider credentials according to its storage policy
  -> BFF establishes local session
```

The browser's ordinary application code need not hold raw provider access/refresh tokens. That reduces direct token exposure to JavaScript. A compromised same-origin script can still act through the BFF, so XSS prevention and authorization remain essential.

| Arrangement | Benefit | Main remaining concern |
| --- | --- | --- |
| Opaque session cookie + BFF | Backend controls provider token lifecycle | CSRF/session store and backend availability |
| Access token in browser memory | Limits persistence compared with durable JS storage | XSS can still use/read accessible credentials |
| Token in localStorage | Survives reloads and is easy for scripts to retrieve | Same-origin XSS can read durable credentials |
| Refresh credential in HttpOnly cookie | Restricts direct script reading | Automatic sending needs CSRF and cookie policy |

There is no token location that makes the application immune to compromised-origin script execution.

### BFF boundaries must remain narrow

Forward only approved operations/targets and enforce user/resource permissions. A generic proxy that forwards arbitrary URLs and credentials creates new security problems.

Coordinate refresh centrally so several browser requests do not all rotate the same credential. The BFF still needs a defined retry/unknown-outcome policy.

If there are multiple BFF instances, share/coordinately manage session and refresh records. Sticky routing can be an optimization, but it does not make process memory durable.

---

## 7.17 Authentication architecture: how to build it incrementally

### Start with an explicit small boundary

Use one maintained authentication/session implementation and a durable user/session store as requirements demand. Keep credential verification separate from user-profile output and resource authorization.

```text
credential boundary
  -> verified principal
  -> authorization boundary
  -> application service
  -> repository

supporting state:
  password verifiers
  sessions/refresh families
  signing/encryption key policy
  abuse controls and security events
```

The example has no session-listing/revoke-all endpoint. Adding those requires a subject/session index and a policy for currently issued access tokens.

### Requirement: permission changes take effect immediately

A long-lived embedded role claim can remain stale. Consider current policy lookup, a bounded policy cache, subject/session versions, shorter access lifetime or introspection.

Name the tolerated delay and what happens if the policy store is unavailable. “JWT has the role” is not an immediate-revocation design.

### Requirement: password reset or suspected compromise

Define which sessions/families are revoked, whether existing access tokens remain usable, and whether sensitive operations require fresh authentication. Account recovery must not become an easier bypass than login.

Recovery links/OTPs need independent expiry, one-use behavior and safe transport/logging. The fixture does not implement them.

### Requirement: operate multiple instances

Persist key material through a managed mechanism, share authoritative lifecycle state, coordinate refresh consumption, define cache invalidation and test stale/replayed credentials on different instances.

Restarting a server should have a deliberate effect on users, not an accidental one caused by random keys regenerated at every boot.

### Requirement: observe failures safely

Measure login failures, throttling, refresh reuse, verification reasons and latency without logging raw passwords, cookies, access/refresh credentials or signing keys.

A correlation ID belongs to a request; a session/family ID represents a lifecycle; a token ID identifies a credential. Apply privacy and access policy to the logs too.

The current examples record safe outcomes and identifiers for a public fixture. They do not provide a deployed security-event pipeline.

---

## 7.18 What was verified

| Group | Count | Evidence |
| --- | --- | --- |
| Password/session/token/crypto | 38 | Salt independence, password verification, JWT trust policy/time boundaries, sessions, refresh families, JWE and HKDF |
| Real HTTP | 32 | Login/error/cookie/CSRF contracts, distinct credential modes, refresh race, logout and access expiry |
| OAuth model | 16 | RFC PKCE vector, callback/browser binding, client/redirect matching, expiry and one-use code/state |
| Total | 86 | The top-level verifier runs all three groups |

Actual selected output:

```text
PASS same password receives independent random salts: {"saltsDiffer":true,"derivedValuesDiffer":true}
PASS signed JWT has three parts and readable untrusted claims: {"parts":3,"decodedSubject":"user-1","containsPassword":false}
PASS payload tampering is rejected even though decoding succeeds: {"rejected":"invalid_access_token"}
PASS wrong audience rejected: {"rejected":"invalid_access_token"}
PASS absolute timeout survives continued activity: {"rejected":"session_expired"}
PASS reuse of consumed refresh revokes family: {"reuseRejected":true,"successorRejected":true}
PASS concurrent refresh has one winner then conservative family revocation: {"statuses":[200,401],"winnerSuccessorRevoked":true}
PASS token logout revokes refresh family without immediate access revocation: {"logout":204,"refresh":401,"issuedAccess":200}
PASS JWE has five parts and decrypts with expected algorithms: {"parts":5,"decryptedNote":"private-demo-value"}
PASS HKDF context separates derived keys: {"sameContextSameKey":true,"changedContextDifferentKey":true,"bytes":32}
PASS PKCE S256 matches RFC 7636 Appendix B vector: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
Verified 86 checks across password/session/JWT/JWE, HTTP and OAuth model groups.
```

### Scope of the evidence

The HTTP group binds a temporary loopback listener and closes it. Clocks are injected for expiry tests. The refresh race uses actual overlapping HTTP requests, with synchronous consumption at the service's one-process state boundary.

The tests do not establish production browser-cookie behavior, real TLS/provider login, full OIDC validation, distributed transactions, crash recovery, signing failure after refresh consumption, adversarial timing indistinguishability, key rotation/JWKS operation or throughput.

They do not prove the session/token service is ready to deploy. They verify the selected local mechanisms and expose important limits.

Evidence files are retained under examples/resume-skills/module-7-authentication/: source, package lock, group results/logs, aggregate results and validation summary. Generated bearer credentials and private keys are not saved in those result files.

---

## 7.19 Connect this to your resume

For a session/JWT/OAuth claim, be prepared to identify the exact implementation rather than naming all three technologies interchangeably.

> “The browser used an application session credential. The backend verified the session and applied resource permissions. Provider login used an authorization-code flow with PKCE and transaction correlation. Provider tokens and the local session had separate lifecycles. For an API token, verification constrained the trusted issuer, intended audience, algorithm and expiry.”

Use that answer only for the parts your project actually implemented. The learning example is not evidence that an earlier project had every mechanism.

| Resume claim | Questions to prepare |
| --- | --- |
| JWT-based authentication | Who signs? Who verifies? Which issuer/audience/algorithms? |
| OAuth login | Where are state/verifier stored and bound? Who handles callback/exchange? |
| NextAuth/Auth.js | Exact version, session strategy, cookie format and supported server API? |
| JWE/HKDF integration | Why encrypted format? Which key derivation, salt/context and algorithms? |
| Revocable invites | What is signed, what expires, and which server state permits revocation? |
| Multi-tenant SaaS | How does the verified principal become a tenant-scoped resource check? |

For signed invites, a signature proves integrity under the trusted key, not that an invite remains unused or unrevoked. A durable invite record with purpose, target, expiry and consumption state is a separate workflow. M8/M9 develop those boundaries.

---

## 7.20 Must remember

- Authentication and authorization establish different facts.
- Credential verification must produce a trusted subject before resource checks.
- Human passwords need suitable adaptive hashing; random tokens have different entropy assumptions.
- A salt is not a secret pepper, and HKDF is not password hashing.
- timingSafeEqual does not make the whole network endpoint constant-time.
- Regenerate the authenticated session credential rather than trusting a client-selected ID.
- Idle timeout and absolute lifetime solve different lifecycle problems.
- A cookie is transport/storage; a JWT is a format.
- HttpOnly limits direct reading but does not stop same-origin malicious actions.
- SameSite and same-origin refer to different boundaries.
- CSRF defenses follow automatic credential sending, not the token's marketing name.
- Decoding a JWT does not verify it.
- Signature, issuer, audience, algorithm, time and purpose checks work together.
- Access, refresh, ID and local session credentials have different consumers.
- Refresh rotation must coordinate consumption and successor state atomically.
- Strict refresh reuse detection can revoke a family after a legitimate race.
- Refresh logout does not automatically invalidate already issued self-contained access tokens.
- OAuth is delegated access; OIDC adds authentication information.
- PKCE, state and nonce have different binding roles.
- A client ID is not a client secret.
- JWS protects integrity; JWE provides encrypted content under its configured profile.
- Framework session formats and key derivation are version-specific.
- An in-memory store and ephemeral keys do not establish durable multi-instance identity.

---

## 7.21 Common wrong answers

| Wrong answer | Correction |
| --- | --- |
| “A valid login lets the user access every route.” | Resource/action authorization still applies. |
| “We encrypt passwords and decrypt at login.” | Store suitable password verifiers and derive/compare candidates. |
| “SHA-256 is strong, so it is enough for passwords.” | Fast guessing is the problem for human-chosen secrets. |
| “The salt must stay secret.” | Salt is stored with the verifier; a pepper is separate secret material. |
| “HttpOnly prevents XSS.” | It restricts direct cookie reading; malicious same-origin actions remain possible. |
| “Cookies and JWT are competing authentication protocols.” | They describe different dimensions: transport/storage and format. |
| “JWT payloads are encrypted.” | Signed compact JWT claims are readable; JWE is a separate encrypted form. |
| “decodeJwt tells me the authenticated user.” | It parses untrusted claims without establishing authenticity. |
| “A valid signature is enough.” | Verify intended issuer, recipient, lifetime, type and application rules. |
| “kid tells us which arbitrary URL to trust.” | Select only within a configured trusted key policy. |
| “Deleting localStorage/cookie logs out a copied token.” | Server validity/revocation and access expiry still matter. |
| “Refresh rotation means both concurrent requests succeed safely.” | The selected strict policy revokes the family on reuse. |
| “OAuth means my app collects the provider password.” | Authorization-code delegation avoids that arrangement. |
| “PKCE replaces every other OAuth check.” | State/browser binding, redirect rules and applicable client authentication remain. |
| “An ID token works as any API access token.” | Consumer/audience/purpose differ. |
| “JWE avoids replay because nobody can read it.” | A valid encrypted bearer credential can still be presented. |
| “Next.js version determines the Auth.js session format.” | Authentication package version and configuration determine it. |
| “A successful local auth test proves production security.” | Browser, provider, state-store and failure boundaries still need verification. |

---

## 7.22 Interview questions and follow-ups

These are preparation targets drawn from core mechanisms and failure cases, not measured company-question frequencies.

**Q1. Authentication versus authorization?**

Authentication establishes a subject from verified credentials. Authorization decides whether that subject may perform the requested action on the target resource.

**Follow-up:** where is ownership/tenant checking performed after req.user is populated?

**Q2. What happens when a user logs in with a password?**

The service validates input, derives a candidate verifier using the stored salt/cost, compares safely and establishes a fresh credential/session on success.

**Follow-up:** what do unknown-account responses and abuse controls reveal?

**Q3. Why not store plaintext or plain SHA-256 passwords?**

Plaintext exposes usable secrets directly. Fast hashing lets an offline attacker check guesses cheaply; suitable adaptive hashing raises per-guess cost.

**Follow-up:** why can SHA-256 be appropriate for the example's random session-token lookup?

**Q4. Salt versus pepper?**

A salt is independent per-password derivation input stored with the verifier. A pepper is additional separately managed secret material.

**Follow-up:** how would you migrate a work factor or rotate a pepper?

**Q5. Does timingSafeEqual make login constant-time?**

It addresses comparison of supported equal-length byte buffers. Database lookups, validation, derivation paths and response behavior can still differ.

**Follow-up:** what exactly did the example verify about unknown accounts?

**Q6. What is a server-side session?**

A credential identifies trusted server state with subject and lifecycle rules. The browser usually carries an opaque ID while the server stores the record.

**Follow-up:** what happens when a different application instance receives the next request?

**Q7. What is session fixation?**

Keeping an attacker-known session credential when authentication succeeds can let the attacker reuse it. Generate a fresh authenticated credential and invalidate the appropriate previous state.

**Follow-up:** is that the same as signing out all devices?

**Q8. Idle versus absolute expiry?**

Idle expiry limits inactivity; absolute expiry limits total lifetime despite activity. The server checks both in the example.

**Follow-up:** why does browser cookie persistence not determine server validity?

**Q9. What do Secure, HttpOnly and SameSite do?**

They constrain transport, ordinary script cookie access and cross-site sending respectively. None alone proves authorization or complete XSS/CSRF protection.

**Follow-up:** can HttpOnly cookies be sent by script-initiated fetch?

**Q10. Why use a __Host- cookie name?**

In supporting browsers its prefix requires Secure, Path=/ and no Domain, helping enforce a host-only configuration.

**Follow-up:** why does the explicit loopback HTTP launcher use a different cookie configuration?

**Q11. What is CSRF?**

An unwanted action can be induced while a browser automatically sends credentials. Bind mutations to the intended origin/session using appropriate controls.

**Follow-up:** explain why both a cookie and the correct synchronizer token are required for logout here.

**Q12. Why is CORS not authentication?**

It governs browser response access under origin policy. Non-browser callers still reach the API, and resource permissions need server checks.

**Follow-up:** can a non-browser client forge Origin?

**Q13. Session versus JWT: which scales better?**

Compare the whole design: authoritative state, lookup/crypto cost, keys, revocation, freshness and failure requirements. Both can support multiple instances when those boundaries are designed.

**Follow-up:** which specific bottleneck did your project measure?

**Q14. What are the parts of a signed JWT?**

Protected header, claims payload and signature/MAC in compact form. The first two are base64url encoded and readable.

**Follow-up:** why is reading sub from the payload not authentication?

**Q15. Which JWT claims do you verify?**

The accepted profile defines required claims; common checks include trusted issuer, intended audience, subject, expiry/not-before and purpose, alongside algorithm/key constraints.

**Follow-up:** what happens with a correctly signed token for another API?

**Q16. HS256 versus RS256?**

HMAC uses shared signing/verifying secret material. Asymmetric signatures let APIs verify with public keys while the issuer retains private signing authority.

**Follow-up:** what risk follows giving every service an HMAC signing secret?

**Q17. What is kid?**

A key identifier used within an established trust/key-selection policy. It is not proof that any supplied key or endpoint is trusted.

**Follow-up:** how would unknown-key bursts and key rotation affect a JWKS cache?

**Q18. Access token versus refresh token?**

The access credential goes to the resource API; the refresh credential goes to the token service to renew access. Their exposure and lifetimes differ.

**Follow-up:** why does the example reject a refresh token at /api/me?

**Q19. How does refresh rotation detect reuse?**

Consume a credential, issue a successor and retain enough history to recognize a later use of the consumed credential. Apply the family's revocation policy.

**Follow-up:** how is consumption/successor creation coordinated across instances?

**Q20. What happens if two tabs refresh together?**

Under this strict policy one request rotates, while reuse by the other revokes the family. Coordinate refresh attempts and define retry/recovery behavior.

**Follow-up:** what if the winning response is lost?

**Q21. How does JWT logout work?**

Deleting client storage alone does not invalidate a copied token. Use short expiry and, when required, authoritative revocation/introspection/session-version checks.

**Follow-up:** why did access still work after refresh-family logout in the verified example?

**Q22. What is OAuth 2.0?**

A delegated-access framework where a client obtains scoped credentials for a resource without collecting the owner's password for that external service.

**Follow-up:** name the resource owner, client, authorization server and resource server in your project.

**Q23. Why authorization code with PKCE?**

A short-lived code is redeemed with a verifier whose challenge was bound to the authorization request. Intercepting the code alone is insufficient.

**Follow-up:** where does a BFF keep the verifier?

**Q24. state versus nonce versus PKCE?**

state correlates/binds the browser transaction, nonce binds an OIDC ID token to its request, and PKCE binds code redemption to a verifier.

**Follow-up:** why must a state record also be bound to the initiating browser/session?

**Q25. Is client ID a secret?**

No. Confidential clients separately authenticate where required; public distributed clients cannot reliably keep an embedded secret confidential.

**Follow-up:** does PKCE remove confidential-client authentication?

**Q26. OAuth versus OIDC?**

OAuth concerns resource access. OIDC adds authentication information such as an ID token that the client must validate under its profile.

**Follow-up:** why should the API reject an unrelated ID token as an access credential?

**Q27. JWS versus JWE?**

JWS protects integrity/authenticity of signed/MACed content; JWE encrypts/authenticates content under its key/profile. Neither supplies resource permissions by itself.

**Follow-up:** why can an encrypted bearer token still be replayed?

**Q28. What is HKDF used for here?**

It derives context-specific key material from input secret material. The checked Auth.js implementation uses it for encryption-key derivation; it is not password hashing.

**Follow-up:** what breaks when secret/salt/context or required output length differ?

**Q29. What does a BFF change?**

The backend can own provider exchanges and raw token storage while the browser uses a local session. It still needs CSRF, XSS prevention, authorization and refresh coordination.

**Follow-up:** what new risk appears in an unrestricted forwarding proxy?

**Q30. What would you test beyond a successful login?**

Wrong credentials, cookie policy, fixation, expiry boundaries, forged/mis-scoped tokens, CSRF, refresh replay/races, logout limits and provider callback binding.

**Follow-up:** which browser, crash, distributed and provider checks remain unverified in this chapter?

---

## 7.23 Practice tasks

### Task 1: Draw the identity path

Trace login and a later authenticated request. Mark every untrusted value and the exact step that establishes subject.

**Checkpoint:** a body userId or decoded JWT is not the trusted principal.

### Task 2: Explain the password verifier

Explain salt, cost, stored output, password whitespace and the final comparison. Identify which claims would require a timing/performance experiment.

**Checkpoint:** derivation and comparison are separate; no endpoint-wide constant-time or throughput result was measured.

### Task 3: Design a session lifecycle

Specify login regeneration, idle/absolute limits, logout and revoke-all behavior for a two-device user.

**Checkpoint:** invalidating one presented session is different from revoking every session.

### Task 4: Change token purpose

Try a token with the same signing key but a different audience or type. Predict the result before running the crypto group.

**Checkpoint:** cryptographic validity does not override recipient/purpose policy.

### Task 5: Analyze a refresh race

Draw R0, R1 and two overlapping attempts. Explain why the successful request's successor becomes unusable under the selected policy.

**Checkpoint:** choose client/BFF coordination and a deliberate recovery policy rather than removing all replay checks.

### Task 6: Specify immediate logout

Design an extension that invalidates already issued access tokens immediately. Identify the state lookup/cache consistency requirement.

**Checkpoint:** setting a refresh-family revoked flag alone is insufficient.

### Task 7: Rebuild the OAuth trace

List authorization request, browser callback and token exchange inputs. Place state, challenge, verifier and applicable client authentication correctly.

**Checkpoint:** the authorization request carries the challenge; code redemption carries the verifier.

### Task 8: Separate OIDC identity from API access

Explain which credential authenticates the user to the client, which calls the resource API, and how an external subject maps to a local user.

**Checkpoint:** validate issuer/client binding and relevant nonce; do not treat an email string or unrelated ID token as universal authority.

### Task 9: Debug a framework cookie

Given a five-part encrypted session cookie, propose a version-aware investigation before attempting a custom decoder.

**Checkpoint:** identify the session strategy, alg/enc, supported server API and derivation inputs. Do not equate a framework JWE cookie with this demo's RS256 access token.

### Task 10: Defend your resume claim

Give a three-minute answer for the authentication mechanism you actually built: credential lifecycle, trust checks, storage, logout and one failure case.

**Checkpoint:** distinguish implemented evidence, local model behavior and a proposed production improvement.

---

## Exit checklist

- [ ] I can distinguish authentication, authorization and identity proofing.
- [ ] I can trace password verification without plaintext storage or decryption.
- [ ] I can explain salt, pepper, work factor and bounded input.
- [ ] I can distinguish safe byte comparison from whole-endpoint timing guarantees.
- [ ] I can trace session issuance, lookup, fixation prevention and logout.
- [ ] I can explain idle expiry, absolute expiry and browser cookie lifetime separately.
- [ ] I can explain cookie attributes and the origin/site distinction.
- [ ] I can identify where CSRF follows automatically sent credentials.
- [ ] I can compare complete session and JWT designs.
- [ ] I can distinguish decoding from verified JWT identity.
- [ ] I can specify trusted keys, algorithms, issuer, audience, time and purpose checks.
- [ ] I can distinguish access, refresh, ID and local session credentials.
- [ ] I can explain atomic refresh rotation and strict reuse detection.
- [ ] I can explain legitimate refresh races and uncertain responses.
- [ ] I can state the limits of logout for already issued access tokens.
- [ ] I can trace OAuth roles and authorization code with PKCE.
- [ ] I can distinguish state, nonce, verifier and challenge.
- [ ] I can explain OAuth versus OIDC and safe external identity mapping.
- [ ] I can distinguish JWS, JWE and context-specific HKDF derivation.
- [ ] I can investigate Auth.js/NextAuth using its actual version/configuration.
- [ ] I can explain the BFF boundary and its remaining security responsibilities.
- [ ] I can run all 86 checks and state what the local examples do not establish.

---

## Next

[**M8: API Security, Authorization and Multi-Tenancy**](/docs/resume-skills/api-security-authorization-multi-tenancy). Use the verified principal to enforce ownership, roles/scopes and tenant boundaries on every relevant data path. Expand CSRF/CORS/XSS, injection, safe ingestion, secrets and negative authorization checks.

M9 then applies credential/signature verification, replay protection and durable state to webhooks, payments and reliable integrations.

### Sources and reproducible evidence

Research checked on **14 October 2026**. Local execution used Node.js v22.14.0 and the isolated pinned jose 6.2.12 package.

- OWASP: [authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), [password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) and [session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
- [Set-Cookie browser contract](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).
- [JWT, RFC 7519](https://www.rfc-editor.org/rfc/rfc7519.html), [JWT BCP, RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html), and [JWE, RFC 7516](https://www.rfc-editor.org/rfc/rfc7516.html).
- [OAuth security BCP, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html), [PKCE, RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html), and [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html).
- [jose project](https://github.com/panva/jose), [jwtVerify](https://github.com/panva/jose/blob/main/docs/jwt/verify/functions/jwtVerify.md), and [claim verification options](https://github.com/panva/jose/blob/main/docs/types/interfaces/JWTClaimVerificationOptions.md).
- [Node crypto API](https://nodejs.org/api/crypto.html), with behavior verified on the recorded local runtime rather than assumed from the latest documentation version.
- [Auth.js JWT documentation](https://authjs.dev/reference/core/jwt) and [inspected current source](https://raw.githubusercontent.com/nextauthjs/next-auth/main/packages/core/src/jwt.ts); no historical project package version was inferred from them.
- Preserved source/evidence: examples/resume-skills/module-7-authentication/password.mjs, identity.mjs, server.mjs, oauth-model.mjs, start.mjs, verify.mjs and the three verify-group files.
- package.json/package-lock.json pin the isolated dependency; results.json, group results and verification-output.txt preserve checked outcomes. validation-summary.json records site validation and remaining limits.
