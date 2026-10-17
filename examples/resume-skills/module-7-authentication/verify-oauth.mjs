import { createOAuthModel, pkceS256 } from './oauth-model.mjs';
import { assert, check, rejected, save } from './checks.mjs';

await check('PKCE S256 matches RFC 7636 Appendix B vector', async () => {
  const result = pkceS256('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk');
  assert.equal(result, 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM');
  return result;
});
await check('PKCE rejects short verifier', async () =>
  rejected(async () => pkceS256('short'), 'invalid_verifier'));
const model = createOAuthModel();
const flow = model.start('browser-A');
const response = model.authorize(flow.request);
await check('authorization request carries challenge rather than verifier', async () => {
  assert.equal(flow.request.codeChallengeMethod, 'S256');
  assert.equal(Object.hasOwn(flow.request, 'verifier'), false);
  assert.equal(flow.request.codeChallenge, pkceS256(flow.verifier));
  return { method: 'S256', verifierInAuthorizationRequest: false };
});
await check('unregistered redirect rejected', async () =>
  rejected(async () => model.authorize({ ...flow.request, redirectUri: 'https://attacker.example.test/callback' }), 'invalid_authorization_request'));
await check('wrong client rejected during authorization', async () =>
  rejected(async () => model.authorize({ ...flow.request, clientId: 'other' }), 'invalid_authorization_request'));
await check('plain challenge method rejected by model policy', async () =>
  rejected(async () => model.authorize({ ...flow.request, codeChallengeMethod: 'plain' }), 'invalid_authorization_request'));
await check('unknown state rejected', async () =>
  rejected(async () => model.callback({ ...response, state: 'unknown' }, 'browser-A'), 'invalid_state'));
await check('callback bound to initiating browser session', async () =>
  rejected(async () => model.callback(response, 'browser-B'), 'invalid_state'));
const exchangeInput = model.callback(response, 'browser-A');
await check('valid callback consumes state once', async () =>
  rejected(async () => model.callback(response, 'browser-A'), 'invalid_state'));
await check('intercepted code without correct verifier rejected', async () =>
  rejected(async () => model.exchange({ ...exchangeInput, verifier: 'x'.repeat(43) }), 'invalid_grant'));
await check('token exchange requires same redirect URI', async () =>
  rejected(async () => model.exchange({ ...exchangeInput, redirectUri: 'https://app.example.test/another' }), 'invalid_grant'));
await check('token exchange requires same client ID', async () =>
  rejected(async () => model.exchange({ ...exchangeInput, clientId: 'other' }), 'invalid_grant'));
await check('valid code and verifier produce modeled delegation', async () => {
  const result = model.exchange(exchangeInput);
  assert.deepEqual(result, { delegatedSubject: 'provider-user-1', scope: 'tasks:read' }); return result;
});
await check('authorization code cannot be exchanged twice', async () =>
  rejected(async () => model.exchange(exchangeInput), 'invalid_grant'));

let clock = 0;
const timed = createOAuthModel({ now: () => clock });
const pending = timed.start('browser-A'), callback = timed.authorize(pending.request);
clock = 30_000;
await check('authorization code expiry enforced', async () =>
  rejected(async () => timed.exchange({ code: callback.code, verifier: pending.verifier, ...pending.request }), 'invalid_grant'));
clock = 60_000;
await check('browser transaction expiry enforced', async () =>
  rejected(async () => timed.callback(callback, 'browser-A'), 'invalid_state'));
await save('oauth');
