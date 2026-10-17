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
