import { once } from 'node:events';
import { createFixtureAuth } from './fixture-auth.mjs';
import { createRepository } from './repository.mjs';
import { createDocumentService } from './service.mjs';
import { createSecurityServer } from './server.mjs';
import { assert, check, save } from './checks.mjs';

let clock = 1_000_000;
const auth = await createFixtureAuth({ now: () => clock });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
const snapshot = repo => JSON.stringify([repo.list('alpha'), repo.list('beta')]);
async function using(options, fn) {
  const repository = createRepository(), audit = [];
  const service = createDocumentService({ repository, ...options });
  const server = createSecurityServer({
    authenticate: auth.authenticate, service, now: () => clock, importLimit: 1000,
    onAudit: event => audit.push(event), ...options,
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  const base = 'http://127.0.0.1:' + server.address().port;
  async function request(url, actor = 'alice', method = 'GET', body, headers = {}) {
    const token = auth.tokens[actor] ?? actor;
    const response = await fetch(base + url, {
      method, headers: {
        ...(actor === null ? {} : { Authorization: 'Bearer ' + token }),
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }), ...headers,
      },
      ...(body === undefined ? {} : { body: typeof body === 'string' || body instanceof Uint8Array ? body : JSON.stringify(body) }),
      signal: AbortSignal.timeout(4000),
    });
    const text = await response.text();
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
    return { status: response.status, headers: response.headers, text,
      body: response.headers.get('content-type')?.startsWith('application/json') && text ? JSON.parse(text) : null };
  }
  let timeout;
  try {
    await Promise.race([fn({ request, repository, audit }), new Promise((_, reject) => {
      timeout = setTimeout(() => reject(new Error('HTTP scenario deadline exceeded')), 12000);
    })]);
  } finally {
    clearTimeout(timeout);
    const closed = once(server, 'close'); server.close(); server.closeAllConnections(); await closed;
    assert.equal(server.listening, false);
  }
}
function status(response, expected) { assert.equal(response.status, expected); return response; }
function error(response, expected, code) {
  status(response, expected); assert.equal(response.body.code, code);
  assert.equal(response.body.requestId, response.headers.get('x-request-id'));
  if (expected === 401) assert.match(response.headers.get('www-authenticate'), /^Bearer /);
  return { status: response.status, code };
}
const alpha = '/tenants/alpha/documents', beta = '/tenants/beta/documents';
await using({}, async ({ request, repository, audit }) => {
  await check('anonymous request rejected', async () => error(await request(alpha, null), 401, 'unauthenticated'));
  await check('forged bearer credential rejected', async () => error(await request(alpha, 'forged'), 401, 'unauthenticated'));
  await check('cross-tenant reads and unknown tenant concealed', async () => {
    const before = snapshot(repository);
    error(await request(beta + '/1', 'alice'), 404, 'not_found');
    error(await request(beta, 'alice'), 404, 'not_found');
    error(await request(beta, 'alice', 'POST', { title: 'Denied' }), 404, 'not_found');
    error(await request(beta + '/1', 'alice', 'PATCH', { title: 'Denied' }, { 'If-Match': '"v1"' }), 404, 'not_found');
    error(await request(beta + '/bulk-delete', 'alice', 'POST', { ids: [1] }), 404, 'not_found');
    error(await request(beta + '/1/download', 'alice'), 404, 'not_found');
    error(await request(alpha + '/1', 'carol'), 404, 'not_found');
    error(await request('/tenants/unknown/documents', 'alice'), 404, 'not_found');
    assert.equal(snapshot(repository), before);
    return { aliceBetaPaths: 6, carolAlpha: 404, unknown: 404, stateUnchanged: true };
  });
  await check('ownership and sharing distinguish private and tenant documents', async () => {
    status(await request(alpha + '/1', 'alice'), 200);
    error(await request(alpha + '/1', 'bob'), 404, 'not_found');
    status(await request(alpha + '/2', 'bob'), 200);
    error(await request(alpha + '/1', 'dana'), 404, 'not_found');
    status(await request(beta + '/2', 'dana'), 200);
    return { ownerPrivate: 200, viewerPrivate: 404, viewerShared: 200, sameUserOtherTenantAdmin: 200 };
  });
  await check('projection excludes content and private server fields', async () => {
    const response = status(await request(alpha + '/1'), 200);
    assert.deepEqual(Object.keys(response.body).sort(), ['id', 'ownerId', 'title', 'version', 'visibility']);
    assert.equal(response.text.includes('PRIVATE-OPERATOR-NOTE'), false);
    return { fields: Object.keys(response.body).sort() };
  });
  await check('list filters permissions before pagination', async () => {
    const page = status(await request(alpha + '?limit=1', 'bob'), 200);
    assert.deepEqual(page.body.items.map(row => row.id), [2]);
    assert.equal(page.body.nextAfter, null);
    assert.deepEqual((await request(alpha, 'alice')).body.items.map(row => row.id), [1, 2]);
    return { bobIds: [2], bobNext: null, aliceIds: [1, 2] };
  });
  await check('continuation and search do not reveal private rows', async () => {
    assert.deepEqual((await request(alpha + '?after=1', 'bob')).body.items.map(row => row.id), [2]);
    assert.deepEqual((await request(alpha + '?after=2', 'bob')).body.items, []);
    assert.deepEqual((await request(alpha + '?q=private', 'bob')).body.items, []);
    return { after1: [2], after2: [], privateSearch: [] };
  });
  await check('query parameters have an explicit allowlist and bounds', async () => {
    for (const query of ['limit=6', 'limit=1&limit=2', 'tenantId=beta', 'after=-1', 'q=' + 'x'.repeat(81)])
      error(await request(alpha + '?' + query), 400, 'invalid_query');
    return { rejectedQueries: 5 };
  });
  await check('tenant header cannot redirect authorized path context', async () => {
    const response = status(await request(alpha + '/1', 'alice', 'GET', undefined, { 'X-Tenant-Id': 'beta' }), 200);
    assert.equal(response.body.title, 'Alpha private');
    return { title: response.body.title };
  });
  await check('claimed role and user headers do not bypass ownership', async () => {
    const before = snapshot(repository);
    error(await request(alpha + '/2', 'alice', 'PATCH', { title: 'Taken' }, {
      'If-Match': '"v1"', 'X-Role': 'admin', 'X-User-Id': 'bob',
    }), 403, 'forbidden');
    assert.equal(snapshot(repository), before);
    return { status: 403, stateUnchanged: true };
  });
  await check('signed role and tenant claims do not replace current membership', async () => {
    const token = await auth.issue('alice', 'docs:read docs:write', { role: 'admin', tenantId: 'beta' });
    error(await request(beta + '/1', token), 404, 'not_found');
    error(await request(alpha + '/2', token, 'PATCH', { title: 'Taken' }, { 'If-Match': '"v1"' }), 403, 'forbidden');
    return { otherTenant: 404, roleEscalation: 403 };
  });
  await check('scope ceiling restricts an otherwise capable editor', async () => {
    const before = snapshot(repository);
    error(await request(alpha, 'aliceReadOnly', 'POST', { title: 'Denied' }), 403, 'scope_required');
    assert.equal(snapshot(repository), before); return { status: 403, stateUnchanged: true };
  });
  await check('write scope does not upgrade viewer role', async () => {
    const before = snapshot(repository);
    error(await request(alpha, 'bob', 'POST', { title: 'Denied' }), 403, 'forbidden');
    error(await request(alpha + '/2', 'bob', 'PATCH', { title: 'Denied' }, { 'If-Match': '"v1"' }), 403, 'forbidden');
    assert.equal(snapshot(repository), before); return { create: 403, editOwn: 403, stateUnchanged: true };
  });
  await check('mass assignment attempts cannot alter server-owned fields', async () => {
    const before = snapshot(repository);
    for (const extra of [{ ownerId: 'bob' }, { tenantId: 'beta' }, { internalNote: 'expose' }, { role: 'admin' }])
      error(await request(alpha, 'alice', 'POST', { title: 'Denied', ...extra }), 400, 'unknown_field');
    assert.equal(snapshot(repository), before); return { rejectedInputs: 4, stateUnchanged: true };
  });
  await check('creation assigns owner and tenant on the server', async () => {
    const response = status(await request(alpha, 'alice', 'POST', { title: ' New document ' }), 201);
    assert.equal(response.headers.get('location'), alpha + '/3');
    assert.equal(response.body.ownerId, 'alice'); assert.equal(response.body.visibility, 'private');
    assert.equal(repository.get('alpha', 3).tenantId, 'alpha');
    assert.equal(repository.get('beta', 3), undefined);
    return { id: response.body.id, ownerId: response.body.ownerId, visibility: response.body.visibility };
  });
  await check('owner edit requires condition and preserves server fields', async () => {
    error(await request(alpha + '/3', 'alice', 'PATCH', { title: 'Changed' }), 428, 'condition_required');
    const changed = status(await request(alpha + '/3', 'alice', 'PATCH', { title: 'Changed' }, { 'If-Match': '"v1"' }), 200);
    assert.equal(changed.headers.get('etag'), '"v2"');
    assert.equal(changed.body.ownerId, 'alice');
    const before = snapshot(repository);
    error(await request(alpha + '/3', 'alice', 'PATCH', { title: 'Stale' }, { 'If-Match': '"v1"' }), 412, 'stale_version');
    assert.equal(snapshot(repository), before);
    return { status: 200, tag: '"v2"', staleStatus: 412 };
  });
  await check('property-level permission restricts visibility changes', async () => {
    const before = snapshot(repository);
    error(await request(alpha + '/3', 'alice', 'PATCH', { visibility: 'tenant' }, { 'If-Match': '"v2"' }), 403, 'visibility_change_forbidden');
    assert.equal(snapshot(repository), before);
    status(await request(beta + '/2', 'dana', 'PATCH', { visibility: 'tenant' }, { 'If-Match': '"v1"' }), 200);
    return { editor: 403, tenantAdmin: 200, editorStateUnchanged: true };
  });
  await check('bulk failure has no partial deletion', async () => {
    const before = snapshot(repository);
    error(await request(alpha + '/bulk-delete', 'alice', 'POST', { ids: [1, 2] }), 403, 'forbidden');
    assert.equal(snapshot(repository), before);
    error(await request(alpha + '/bulk-delete', 'alice', 'POST', { ids: [1, 999] }), 404, 'not_found');
    assert.equal(snapshot(repository), before);
    error(await request(alpha + '/bulk-delete', 'alice', 'POST', { ids: [1, 1] }), 400, 'invalid_ids');
    assert.equal(snapshot(repository), before);
    return { forbidden: 403, missing: 404, duplicate: 400, stateUnchanged: true };
  });
  await check('authorized bulk deletion stays within selected tenant', async () => {
    status(await request(beta + '/bulk-delete', 'dana', 'POST', { ids: [1, 2] }), 204);
    assert.equal(repository.list('beta').length, 0);
    assert.equal(repository.list('alpha').length, 3);
    return { betaRemaining: 0, alphaRemaining: 3 };
  });
  await check('download has independent object authorization and safe type', async () => {
    error(await request(alpha + '/1/download', 'bob'), 404, 'not_found');
    const response = status(await request(alpha + '/1/download'), 200);
    assert.equal(response.text, 'Alpha private');
    assert.equal(response.headers.get('content-type'), 'text/plain; charset=utf-8');
    assert.equal(response.headers.get('content-disposition'), 'attachment; filename="document-1.txt"');
    return { denied: 404, allowed: 200, attachment: true, nosniff: true };
  });
  await check('audit records correlate decisions without body or credential values', async () => {
    const response = await request(alpha + '/1');
    const event = audit.find(event => event.requestId === response.headers.get('x-request-id'));
    assert.equal(event.subject, 'alice'); assert.equal(event.tenant, 'alpha'); assert.equal(event.status, 200);
    const serialized = JSON.stringify(audit);
    for (const secret of [auth.tokens.alice, 'PRIVATE-OPERATOR-NOTE', 'Alpha private', 'Bearer '])
      assert.equal(serialized.includes(secret), false);
    assert.ok(audit.some(event => event.status === 403));
    return { correlated: true, denialRecorded: true, credentialOrBodyLogged: false };
  });
});
await using({}, async ({ request, repository }) => {
  await check('cache cannot mix same local ID across tenants or viewers', async () => {
    assert.equal((await request(alpha + '/1', 'alice')).body.title, 'Alpha private');
    assert.equal((await request(beta + '/1', 'dana')).body.title, 'Beta shared');
    error(await request(alpha + '/1', 'bob'), 404, 'not_found');
    return { alpha1: 'Alpha private', beta1: 'Beta shared', otherViewer: 404 };
  });
  await check('current membership and object policy checked before cache hit', async () => {
    status(await request(beta + '/2', 'dana'), 200);
    repository.setRole('beta', 'dana', 'viewer');
    error(await request(beta + '/2', 'dana'), 404, 'not_found');
    status(await request(alpha + '/2', 'bob'), 200);
    repository.setRole('alpha', 'bob', null);
    error(await request(alpha + '/2', 'bob'), 404, 'not_found');
    return { downgradedPrivate: 404, removedMembership: 404 };
  });
  await check('unknown membership role fails closed', async () => {
    repository.setRole('alpha', 'alice', 'superuser');
    error(await request(alpha + '/1'), 404, 'not_found');
    return { status: 404 };
  });
});
await using({}, async ({ request, repository }) => {
  const origin = { Origin: 'https://app.example.test' };
  await check('preflight advertises an allowed route without exposing data', async () => {
    const response = status(await request(alpha + '/1', null, 'OPTIONS', undefined, {
      ...origin, 'Access-Control-Request-Method': 'PATCH',
      'Access-Control-Request-Headers': 'Authorization, Content-Type, If-Match',
    }), 204);
    assert.equal(response.text, '');
    assert.equal(response.headers.get('access-control-allow-origin'), origin.Origin);
    assert.equal(response.headers.get('access-control-allow-credentials'), null);
    assert.equal(response.headers.get('access-control-allow-methods'), 'GET, PATCH');
    assert.ok(response.headers.get('vary').includes('Access-Control-Request-Headers'));
    return { status: 204, allowOrigin: origin.Origin, credentials: false };
  });
  await check('origin allowlist rejects null and suffix tricks', async () => {
    for (const value of ['null', 'https://attacker.example.test', 'https://app.example.test.evil'])
      error(await request(alpha, 'alice', 'GET', undefined, { Origin: value }), 403, 'origin_rejected');
    return { rejectedOrigins: 3 };
  });
  await check('preflight rejects unsupported method or header', async () => {
    for (const extra of [
      { 'Access-Control-Request-Method': 'DELETE' },
      { 'Access-Control-Request-Method': 'PATCH', 'Access-Control-Request-Headers': 'X-Role' },
    ]) error(await request(alpha + '/1', null, 'OPTIONS', undefined, { ...origin, ...extra }), 403, 'preflight_rejected');
    return { rejectedPreflights: 2 };
  });
  await check('allowed Origin does not establish identity or tenant permission', async () => {
    const anonymous = await request(alpha, null, 'GET', undefined, origin);
    error(anonymous, 401, 'unauthenticated');
    assert.equal(anonymous.headers.get('access-control-allow-origin'), origin.Origin);
    error(await request(beta + '/1', 'alice', 'GET', undefined, origin), 404, 'not_found');
    return { anonymous: 401, nonmember: 404 };
  });
  await check('non-browser request still requires real authorization', async () => {
    status(await request(alpha + '/1'), 200);
    error(await request(beta + '/1'), 404, 'not_found');
    return { own: 200, otherTenant: 404 };
  });
  await check('disallowed-origin mutation has no effect', async () => {
    const before = snapshot(repository);
    error(await request(alpha, 'alice', 'POST', { title: 'Denied' }, { Origin: 'https://attacker.example.test' }), 403, 'origin_rejected');
    assert.equal(snapshot(repository), before); return { status: 403, stateUnchanged: true };
  });
});
const importHeaders = { 'Content-Type': 'text/plain; charset=utf-8', 'X-File-Name': 'notes.txt' };
await using({}, async ({ request, repository }) => {
  for (const [name, data, headers, expected, code] of [
    ['path filename', Buffer.from('hello'), { 'X-File-Name': '../notes.txt' }, 400, 'invalid_filename'],
    ['active extension', Buffer.from('<script>x</script>'), { 'X-File-Name': 'page.html' }, 400, 'invalid_filename'],
    ['oversize text', Buffer.alloc(1025, 65), {}, 413, 'body_too_large'],
    ['invalid UTF-8', Buffer.from([0xff]), {}, 400, 'invalid_utf8'],
    ['NUL content', Buffer.from([65, 0]), {}, 400, 'invalid_text'],
    ['compressed body', Buffer.from('hello'), { 'Content-Encoding': 'gzip' }, 415, 'unsupported_body_format'],
    ['unsupported MIME', Buffer.from('hello'), { 'Content-Type': 'application/pdf' }, 415, 'unsupported_body_format'],
  ]) await check('import rejects ' + name + ' without storing a row', async () => {
    const before = snapshot(repository);
    error(await request(alpha + '/import', 'alice', 'POST', data, { ...importHeaders, ...headers }), expected, code);
    assert.equal(snapshot(repository), before); return { status: expected, stateUnchanged: true };
  });
  await check('import authorizes before payload processing', async () => {
    const before = snapshot(repository);
    error(await request(alpha + '/import', 'bob', 'POST', Buffer.from('hello'), importHeaders), 403, 'forbidden');
    error(await request(beta + '/import', 'alice', 'POST', Buffer.from('hello'), importHeaders), 404, 'not_found');
    assert.equal(snapshot(repository), before); return { viewer: 403, nonmember: 404, stateUnchanged: true };
  });
  await check('text import records server ownership and opaque storage metadata', async () => {
    const response = status(await request(alpha + '/import', 'alice', 'POST', Buffer.from('Placement café'), importHeaders), 201);
    const row = repository.get('alpha', response.body.id);
    assert.equal(row.ownerId, 'alice'); assert.equal(row.visibility, 'private'); assert.equal(row.content, 'Placement café');
    assert.match(row.storageKey, /^[a-f0-9-]{36}$/);
    assert.equal(Object.hasOwn(response.body, 'storageKey'), false);
    error(await request(alpha + '/' + response.body.id + '/download', 'bob'), 404, 'not_found');
    return { id: response.body.id, ownerId: row.ownerId, visibility: row.visibility, publicStorageKey: false };
  });
  await check('markup remains text in authorized attachment response', async () => {
    const markup = '<script>alert("demo")</script>';
    const response = status(await request(alpha + '/import', 'alice', 'POST', Buffer.from(markup), {
      ...importHeaders, 'X-File-Name': 'markup.txt',
    }), 201);
    const download = status(await request(alpha + '/' + response.body.id + '/download'), 200);
    assert.equal(download.text, markup);
    assert.equal(download.headers.get('content-type'), 'text/plain; charset=utf-8');
    assert.match(download.headers.get('content-disposition'), /^attachment;/);
    return { bytesPreserved: true, type: 'text/plain', attachment: true };
  });
});
await using({ importLimit: 2 }, async ({ request }) => {
  clock = 1_008_500;
  await check('HTTP import budget keys verified tenant and subject', async () => {
    for (let i = 0; i < 2; i++) status(await request(beta + '/import', 'dana', 'POST', Buffer.from('hello'), importHeaders), 201);
    const blocked = await request(beta + '/import', 'dana', 'POST', Buffer.from('hello'), importHeaders);
    error(blocked, 429, 'import_rate_limited'); assert.equal(blocked.headers.get('retry-after'), '2');
    status(await request(beta + '/import', 'carol', 'POST', Buffer.from('hello'), importHeaders), 201);
    status(await request(alpha + '/1', 'alice'), 200);
    return { exhausted: 429, retryAfterSeconds: 2, otherSubject: 201, reads: 200 };
  });
  clock = 1_010_000;
  await check('HTTP import budget resets next window', async () => {
    status(await request(beta + '/import', 'dana', 'POST', Buffer.from('hello'), importHeaders), 201);
    return { status: 201 };
  });
});
clock = 1_000_000;
for (const action of ['update', 'bulk-delete']) {
  const entered = deferred(), release = deferred();
  await using({ beforeCommit: async event => {
    if (event.action === action) { entered.resolve(); await release.promise; }
  } }, async ({ request, repository }) => {
    await check('membership revoked while ' + action + ' awaits prevents commit', async () => {
      const pending = action === 'update'
        ? request(alpha + '/1', 'alice', 'PATCH', { title: 'Should not commit' }, { 'If-Match': '"v1"' })
        : request(alpha + '/bulk-delete', 'alice', 'POST', { ids: [1] });
      await entered.promise;
      const before = snapshot(repository);
      repository.setRole('alpha', 'alice', null); release.resolve();
      error(await pending, 404, 'not_found'); assert.equal(snapshot(repository), before);
      return { status: 404, documentsUnchanged: true };
    });
  });
}
const entered = deferred(), release = deferred();
await using({ beforeRead: async event => {
  if (event.tenant === 'alpha') { entered.resolve(); await release.promise; }
} }, async ({ request }) => {
  await check('overlapping tenant requests keep local context and role', async () => {
    const pending = request(alpha + '/2', 'dana');
    await entered.promise;
    const betaResult = status(await request(beta + '/2', 'dana'), 200);
    release.resolve();
    const alphaResult = status(await pending, 200);
    assert.equal(betaResult.body.title, 'Beta private'); assert.equal(alphaResult.body.title, 'Alpha shared');
    return { alpha: alphaResult.body.title, beta: betaResult.body.title };
  });
});
await using({}, async ({ request }) => {
  clock = 1_300_000;
  await check('expired identity rejected before tenant access', async () =>
    error(await request(alpha + '/1'), 401, 'unauthenticated'));
});
clock = 1_000_000;
await save('http');
console.log('All temporary HTTP listeners closed.');
