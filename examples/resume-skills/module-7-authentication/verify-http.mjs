import { once } from 'node:events';
import { hashPassword } from './password.mjs';
import { createIdentity } from './identity.mjs';
import { createAuthServer } from './server.mjs';
import { assert, check, save } from './checks.mjs';

let clock = 10_000_000;
const password = 'placement-demo-password';
const identity = await createIdentity({ passwordRecord: await hashPassword(password), now: () => clock });
const server = createAuthServer({ identity });
server.listen(0, '127.0.0.1');
await once(server, 'listening');
const base = 'http://127.0.0.1:' + server.address().port;
const credentials = { email: 'learner@example.test', password };
async function request(path, method = 'GET', value, headers = {}) {
  const requestHeaders = {
    ...(method === 'POST' ? { Origin: 'https://app.example.test' } : {}),
    ...(value === undefined ? {} : { 'Content-Type': 'application/json' }), ...headers,
  };
  if (headers.Origin === null) delete requestHeaders.Origin;
  const response = await fetch(base + path, {
    method, headers: requestHeaders,
    ...(value === undefined ? {} : { body: typeof value === 'string' ? value : JSON.stringify(value) }),
    signal: AbortSignal.timeout(8000),
  });
  const text = await response.text();
  assert.equal(response.headers.get('cache-control'), 'no-store');
  return { status: response.status, headers: response.headers, body: text ? JSON.parse(text) : null, text };
}
function status(response, expected) { assert.equal(response.status, expected); return response; }
function error(response, expected, code) {
  status(response, expected); assert.deepEqual(response.body, { code });
  if (expected === 401) assert.ok(response.headers.get('www-authenticate'));
  assert.equal(response.headers.get('set-cookie'), null);
  return { status: response.status, code };
}
function cookieOf(response) { return response.headers.get('set-cookie').split(';')[0]; }
try {
  await check('missing session returns 401', async () =>
    error(await request('/session/me'), 401, 'unauthenticated'));
  await check('forged session rejected', async () =>
    error(await request('/session/me', 'GET', undefined, { Cookie: '__Host-sid=' + 'x'.repeat(43) }), 401, 'unauthenticated'));
  await check('missing login Origin rejected', async () =>
    error(await request('/session/login', 'POST', credentials, { Origin: null }), 403, 'origin_rejected'));
  await check('untrusted login Origin rejected', async () =>
    error(await request('/session/login', 'POST', credentials, { Origin: 'https://attacker.example.test' }), 403, 'origin_rejected'));
  await check('null login Origin rejected', async () =>
    error(await request('/session/login', 'POST', credentials, { Origin: 'null' }), 403, 'origin_rejected'));
  await check('unsupported login format rejected', async () =>
    error(await request('/session/login', 'POST', '{}', { 'Content-Type': 'text/plain' }), 415, 'unsupported_body_format'));
  await check('malformed login JSON rejected', async () =>
    error(await request('/session/login', 'POST', '{'), 400, 'invalid_json_object'));
  await check('login body bound enforced', async () =>
    error(await request('/session/login', 'POST', { ...credentials, padding: 'x'.repeat(2100) }), 413, 'body_too_large'));
  await check('unknown login field rejected', async () =>
    error(await request('/session/login', 'POST', { ...credentials, role: 'admin' }), 400, 'invalid_input'));
  await check('oversize password rejected', async () =>
    error(await request('/session/login', 'POST', { ...credentials, password: 'x'.repeat(257) }), 400, 'invalid_input'));
  await check('wrong password and unknown account share public failure', async () => {
    const wrong = await request('/session/login', 'POST', { ...credentials, password: 'incorrect-demo-password' });
    const unknown = await request('/session/login', 'POST', { ...credentials, email: 'unknown@example.test' });
    error(wrong, 401, 'invalid_credentials'); error(unknown, 401, 'invalid_credentials');
    assert.deepEqual(wrong.body, unknown.body);
    return { wrongPassword: 401, unknownAccount: 401, sameBody: true };
  });
  const login = status(await request('/session/login', 'POST', credentials), 200);
  const sessionCookie = cookieOf(login);
  await check('login sets host-only secure HttpOnly SameSite cookie', async () => {
    const set = login.headers.get('set-cookie');
    assert.match(set, /^__Host-sid=[A-Za-z0-9_-]{43};/);
    for (const flag of ['Path=/', 'HttpOnly', 'SameSite=Lax', 'Max-Age=120', 'Secure']) assert.ok(set.includes(flag));
    assert.equal(set.includes('Domain='), false);
    assert.deepEqual(Object.keys(login.body).sort(), ['authenticated', 'csrfToken']);
    return { name: '__Host-sid', secure: true, httpOnly: true, sameSite: 'Lax', domainAttribute: false };
  });
  await check('session credential resolves public user without password', async () => {
    const me = status(await request('/session/me', 'GET', undefined, { Cookie: sessionCookie }), 200);
    assert.deepEqual(Object.keys(me.body.user).sort(), ['email', 'id', 'name']);
    assert.equal(me.body.user.id, 'user-1');
    assert.equal(me.body.csrfToken, login.body.csrfToken);
    return { userId: me.body.user.id, passwordExposed: false };
  });
  await check('duplicate named session cookies rejected', async () =>
    error(await request('/session/me', 'GET', undefined, { Cookie: sessionCookie + '; ' + sessionCookie }), 400, 'ambiguous_cookie'));
  await check('GET logout rejected with Allow', async () => {
    const response = status(await request('/session/logout'), 405);
    assert.equal(response.headers.get('allow'), 'POST'); return { status: 405, allow: 'POST' };
  });
  await check('logout requires CSRF token', async () =>
    error(await request('/session/logout', 'POST', undefined, { Cookie: sessionCookie }), 403, 'csrf_rejected'));
  await check('logout rejects cross-origin request despite correct CSRF', async () =>
    error(await request('/session/logout', 'POST', undefined, {
      Cookie: sessionCookie, 'X-CSRF-Token': login.body.csrfToken, Origin: 'https://attacker.example.test',
    }), 403, 'origin_rejected'));
  await check('re-login rotates cookie and invalidates prior session', async () => {
    const again = status(await request('/session/login', 'POST', credentials, { Cookie: sessionCookie }), 200);
    assert.notEqual(cookieOf(again), sessionCookie);
    error(await request('/session/me', 'GET', undefined, { Cookie: sessionCookie }), 401, 'unauthenticated');
    const clear = status(await request('/session/logout', 'POST', undefined, {
      Cookie: cookieOf(again), 'X-CSRF-Token': again.body.csrfToken,
    }), 204);
    assert.match(clear.headers.get('set-cookie'), /^__Host-sid=; Path=\/; HttpOnly; SameSite=Lax; Max-Age=0; Secure$/);
    assert.equal(clear.text, '');
    error(await request('/session/me', 'GET', undefined, { Cookie: cookieOf(again) }), 401, 'unauthenticated');
    return { rotated: true, oldSessionValid: false, logout: 204, newSessionAfterLogoutValid: false };
  });

  const liveSession = cookieOf(status(await request('/session/login', 'POST', credentials), 200));
  const pair = status(await request('/tokens/login', 'POST', credentials), 200).body;
  await check('token login returns distinct access and refresh credentials', async () => {
    assert.equal(pair.accessToken.split('.').length, 3);
    assert.match(pair.refreshToken, /^[A-Za-z0-9_-]{43}$/);
    assert.equal(pair.tokenType, 'Bearer'); assert.equal(pair.expiresIn, 60);
    return { accessParts: 3, refreshCharacters: 43, expiresInSeconds: 60 };
  });
  await check('bearer request verifies user and challenge scheme', async () => {
    const me = status(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + pair.accessToken }), 200);
    assert.equal(me.body.user.id, 'user-1');
    const denied = await request('/api/me');
    error(denied, 401, 'invalid_access_token');
    assert.equal(denied.headers.get('www-authenticate'), 'Bearer realm="placement-demo"');
    return { valid: 200, missing: 401, challenge: 'Bearer' };
  });
  await check('refresh credential cannot be used as access credential', async () =>
    error(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + pair.refreshToken }), 401, 'invalid_access_token'));
  await check('access credential cannot be used as refresh credential', async () =>
    error(await request('/tokens/refresh', 'POST', { refreshToken: pair.accessToken }), 401, 'invalid_refresh_token'));
  await check('cookie alone does not authenticate bearer route', async () =>
    error(await request('/api/me', 'GET', undefined, { Cookie: liveSession }), 401, 'invalid_access_token'));
  await check('bearer alone does not authenticate session route', async () =>
    error(await request('/session/me', 'GET', undefined, { Authorization: 'Bearer ' + pair.accessToken }), 401, 'unauthenticated'));
  await check('ambiguous bearer value rejected', async () =>
    error(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + pair.accessToken + ', another' }), 401, 'invalid_access_token'));
  const refreshed = status(await request('/tokens/refresh', 'POST', { refreshToken: pair.refreshToken }), 200).body;
  await check('refresh endpoint rotates opaque credential', async () => {
    assert.notEqual(refreshed.refreshToken, pair.refreshToken);
    status(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + refreshed.accessToken }), 200);
    return { successorDistinct: true, accessValid: true };
  });
  await check('refresh reuse rejects descendant but existing access remains valid', async () => {
    error(await request('/tokens/refresh', 'POST', { refreshToken: pair.refreshToken }), 401, 'refresh_reuse');
    error(await request('/tokens/refresh', 'POST', { refreshToken: refreshed.refreshToken }), 401, 'invalid_refresh_token');
    status(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + refreshed.accessToken }), 200);
    return { reused: 401, descendant: 401, issuedAccess: 200 };
  });

  const concurrent = status(await request('/tokens/login', 'POST', credentials), 200).body;
  await check('concurrent refresh has one winner then conservative family revocation', async () => {
    const responses = await Promise.all([1, 2].map(() => request('/tokens/refresh', 'POST', { refreshToken: concurrent.refreshToken })));
    assert.deepEqual(responses.map(r => r.status).sort(), [200, 401]);
    const winner = responses.find(r => r.status === 200);
    error(await request('/tokens/refresh', 'POST', { refreshToken: winner.body.refreshToken }), 401, 'invalid_refresh_token');
    return { statuses: [200, 401], winnerSuccessorRevoked: true };
  });
  const logoutPair = status(await request('/tokens/login', 'POST', credentials), 200).body;
  await check('token logout revokes refresh family without immediate access revocation', async () => {
    const logout = status(await request('/tokens/logout', 'POST', { refreshToken: logoutPair.refreshToken }), 204);
    assert.equal(logout.text, '');
    error(await request('/tokens/refresh', 'POST', { refreshToken: logoutPair.refreshToken }), 401, 'invalid_refresh_token');
    status(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + logoutPair.accessToken }), 200);
    return { logout: 204, refresh: 401, issuedAccess: 200 };
  });
  clock += 60_000;
  await check('access expiry enforced on actual HTTP route', async () =>
    error(await request('/api/me', 'GET', undefined, { Authorization: 'Bearer ' + logoutPair.accessToken }), 401, 'invalid_access_token'));
  await check('unknown route returns 404', async () =>
    error(await request('/missing'), 404, 'not_found'));
  await check('query-based token transport rejected', async () =>
    error(await request('/api/me?access_token=anything'), 400, 'unexpected_query'));
} finally {
  const closed = once(server, 'close');
  server.close(); server.closeAllConnections(); await closed;
  assert.equal(server.listening, false);
}
await save('http');
console.log('All temporary HTTP listeners closed.');
