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
