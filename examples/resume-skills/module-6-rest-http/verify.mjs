import assert from 'node:assert/strict';
import { once } from 'node:events';
import { request as httpRequest } from 'node:http';
import { writeFile } from 'node:fs/promises';
import { createTaskServer } from './server.mjs';

const results = [];
const check = async (name, fn) => {
  const observed = await fn();
  results.push({ name, passed: true, observed });
  console.log('PASS ' + name + (observed === undefined ? '' : ': ' + JSON.stringify(observed)));
};
const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};
async function using(options, fn) {
  const server = createTaskServer(options);
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = 'http://127.0.0.1:' + server.address().port;
  const request = async (url = '/v1/tasks', method = 'GET', body, headers = {}) => {
    const response = await fetch(base + url, {
      method, headers: { ...(body === undefined ? {} : { 'Content-Type': 'application/json' }), ...headers },
      ...(body === undefined ? {} : { body: typeof body === 'string' || body instanceof Uint8Array ? body : JSON.stringify(body) }),
      signal: AbortSignal.timeout(4000),
    });
    const text = await response.text();
    return { status: response.status, headers: response.headers, text, body: text ? JSON.parse(text) : null };
  };
  try { await fn(request, server); }
  finally {
    const closed = once(server, 'close');
    server.close();
    server.closeAllConnections();
    await closed;
    assert.equal(server.listening, false);
  }
}
const status = (response, expected) => { assert.equal(response.status, expected); return response; };
const error = (response, expected, code) => {
  status(response, expected);
  assert.equal(response.headers.get('content-type'), 'application/problem+json');
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(response.body.status, expected);
  assert.equal(response.body.code, code);
  assert.equal(response.body.type, 'about:blank');
  assert.equal(response.body.requestId, response.headers.get('x-request-id'));
  assert.equal(response.body.instance, 'urn:uuid:' + response.body.requestId);
  return { status: response.status, code: response.body.code };
};
const input = (title, completed = false) => ({ title, completed });

await using({}, async request => {
  await check('empty collection', async () => {
    const response = status(await request(), 200);
    assert.deepEqual(response.body, { items: [], next: null });
    return response.body;
  });
  for (const [name, method, body, headers, expected, code] of [
    ['missing media type', 'POST', '{}', { 'Content-Type': '' }, 415, 'unsupported_media_type'],
    ['unsupported media type', 'POST', '{}', { 'Content-Type': 'text/plain' }, 415, 'unsupported_media_type'],
    ['unsupported charset', 'POST', '{}', { 'Content-Type': 'application/json; charset=latin1' }, 415, 'unsupported_media_type'],
    ['compressed input rejected', 'POST', '{}', { 'Content-Encoding': 'gzip' }, 415, 'unsupported_encoding'],
    ['malformed JSON', 'POST', '{', {}, 400, 'invalid_json'],
    ['invalid UTF-8', 'POST', Buffer.from([0xff]), {}, 400, 'invalid_json'],
    ['oversize body', 'POST', JSON.stringify(input('x'.repeat(2100))), {}, 413, 'body_too_large'],
    ['array is not a task', 'POST', '[]', {}, 422, 'invalid_task'],
    ['null is not a task', 'POST', 'null', {}, 422, 'invalid_task'],
    ['unknown field rejected', 'POST', { ...input('A'), ownerId: 'someone' }, {}, 422, 'unknown_field'],
    ['blank title rejected', 'POST', input('   '), {}, 422, 'invalid_title'],
    ['boolean string rejected', 'POST', { title: 'A', completed: 'false' }, {}, 422, 'invalid_completed'],
    ['creation requires key', 'POST', input('A'), {}, 400, 'invalid_key'],
    ['key format checked', 'POST', input('A'), { 'Idempotency-Key': 'bad key' }, 400, 'invalid_key'],
  ]) await check(name, async () => error(await request('/v1/tasks', method, body, headers), expected, code));

  const created = await request('/v1/tasks', 'POST', input('  Learn HTTP  '), { 'Idempotency-Key': 'create-a' });
  let taskTag = created.headers.get('etag');
  await check('create returns resource location and strong validator', async () => {
    status(created, 201);
    assert.deepEqual(created.body, { id: 1, title: 'Learn HTTP', completed: false });
    assert.equal(created.headers.get('location'), '/v1/tasks/1');
    assert.match(taskTag, /^"[a-f0-9]{64}"$/);
    return { status: created.status, location: created.headers.get('location'), task: created.body };
  });
  await check('normalized same-key retry replays original creation', async () => {
    const retry = status(await request('/v1/tasks', 'POST', { completed: false, title: 'Learn HTTP' }, { 'Idempotency-Key': 'create-a' }), 201);
    assert.deepEqual(retry.body, created.body);
    assert.equal(retry.headers.get('idempotency-replayed'), 'true');
    assert.equal(retry.headers.get('etag'), taskTag);
    assert.equal((await request()).body.items.length, 1);
    return { id: retry.body.id, replayed: true, total: 1 };
  });
  await check('key reused with different input conflicts', async () =>
    error(await request('/v1/tasks', 'POST', input('Different'), { 'Idempotency-Key': 'create-a' }), 409, 'key_conflict'));
  await check('GET identifies stored resource and cache policy', async () => {
    const response = status(await request('/v1/tasks/1'), 200);
    assert.deepEqual(response.body, created.body);
    assert.equal(response.headers.get('etag'), taskTag);
    assert.equal(response.headers.get('cache-control'), 'private, no-cache');
    return { id: response.body.id, cache: response.headers.get('cache-control') };
  });
  await check('HEAD has same validator and no body', async () => {
    const response = status(await request('/v1/tasks/1', 'HEAD'), 200);
    assert.equal(response.text, '');
    assert.equal(response.headers.get('etag'), taskTag);
    return { status: response.status, bytes: response.text.length };
  });
  await check('weak If-None-Match matches among a tag list', async () => {
    const response = status(await request('/v1/tasks/1', 'GET', undefined, { 'If-None-Match': '"other", W/' + taskTag }), 304);
    assert.equal(response.text, '');
    assert.equal(response.headers.get('etag'), taskTag);
    return { status: response.status, bytes: response.text.length };
  });
  await check('If-None-Match star matches existing item', async () => {
    const response = status(await request('/v1/tasks/1', 'GET', undefined, { 'If-None-Match': '*' }), 304);
    assert.equal(response.text, '');
    return 304;
  });
  await check('nonmatching validator returns representation', async () =>
    status(await request('/v1/tasks/1', 'GET', undefined, { 'If-None-Match': '"other"' }), 200).status);
  await check('malformed validator rejected', async () =>
    error(await request('/v1/tasks/1', 'GET', undefined, { 'If-None-Match': 'abc' }), 400, 'invalid_condition'));
  await check('update without precondition rejected', async () =>
    error(await request('/v1/tasks/1', 'PATCH', { completed: true }), 428, 'condition_required'));
  await check('weak If-Match cannot protect a write', async () =>
    error(await request('/v1/tasks/1', 'PATCH', { completed: true }, { 'If-Match': 'W/' + taskTag }), 412, 'stale_version'));
  await check('PUT requires complete writable representation', async () =>
    error(await request('/v1/tasks/1', 'PUT', { title: 'Replacement' }, { 'If-Match': taskTag }), 422, 'invalid_completed'));
  await check('PATCH rejects empty document', async () =>
    error(await request('/v1/tasks/1', 'PATCH', {}, { 'If-Match': taskTag }), 422, 'empty_patch'));
  await check('PATCH null is invalid in this custom format', async () =>
    error(await request('/v1/tasks/1', 'PATCH', { title: null }, { 'If-Match': taskTag }), 422, 'invalid_title'));
  const oldTag = taskTag;
  await check('PATCH keeps omitted fields and changes validator', async () => {
    const response = status(await request('/v1/tasks/1', 'PATCH', { completed: true }, { 'If-Match': '"other", ' + taskTag }), 200);
    assert.deepEqual(response.body, { id: 1, title: 'Learn HTTP', completed: true });
    taskTag = response.headers.get('etag');
    assert.notEqual(taskTag, oldTag);
    return response.body;
  });
  await check('stale editor cannot overwrite newer state', async () => {
    const response = await request('/v1/tasks/1', 'PUT', input('Stale'), { 'If-Match': oldTag });
    error(response, 412, 'stale_version');
    assert.equal((await request('/v1/tasks/1')).body.completed, true);
    return { status: response.status, completed: true };
  });
  await check('replay retains original POST result after later edit', async () => {
    const response = status(await request('/v1/tasks', 'POST', input('Learn HTTP'), { 'Idempotency-Key': 'create-a' }), 201);
    assert.equal(response.body.completed, false);
    assert.equal((await request('/v1/tasks/1')).body.completed, true);
    return { replayCompleted: false, currentCompleted: true };
  });
  await check('PUT replaces writable state', async () => {
    const response = status(await request('/v1/tasks/1', 'PUT', input('Replacement'), { 'If-Match': taskTag }), 200);
    assert.equal(response.headers.get('etag'), null);
    taskTag = (await request('/v1/tasks/1')).headers.get('etag');
    assert.deepEqual(response.body, { id: 1, title: 'Replacement', completed: false });
    return response.body;
  });
  await check('same PUT state keeps content-derived validator', async () => {
    const response = status(await request('/v1/tasks/1', 'PUT', input('Replacement'), { 'If-Match': taskTag }), 200);
    assert.equal(response.headers.get('etag'), null);
    assert.equal((await request('/v1/tasks/1')).headers.get('etag'), taskTag);
    return { status: response.status, sameValidatorOnGet: true };
  });
  await check('normalized PUT omits response validators; GET supplies current tag', async () => {
    const response = status(await request('/v1/tasks/1', 'PUT', input('  Replacement  '), { 'If-Match': taskTag }), 200);
    assert.equal(response.body.title, 'Replacement');
    assert.equal(response.headers.get('etag'), null);
    const current = status(await request('/v1/tasks/1'), 200);
    assert.equal(current.headers.get('etag'), taskTag);
    return { title: response.body.title, putValidator: null, getValidatorPresent: true };
  });
  await check('DELETE removes once and returns no body', async () => {
    const response = status(await request('/v1/tasks/1', 'DELETE', undefined, { 'If-Match': taskTag }), 204);
    assert.equal(response.text, '');
    assert.equal(response.headers.get('content-type'), null);
    return { status: response.status, bytes: 0 };
  });
  await check('repeated DELETE returns 404 with same final absence', async () =>
    error(await request('/v1/tasks/1', 'DELETE', undefined, { 'If-Match': taskTag }), 404, 'not_found'));
  await check('OPTIONS advertises methods and patch format', async () => {
    const response = status(await request('/v1/tasks/1', 'OPTIONS'), 204);
    assert.equal(response.headers.get('accept-patch'), 'application/json');
    assert.equal(response.headers.get('allow'), 'GET, HEAD, PUT, PATCH, DELETE, OPTIONS');
    assert.equal(response.text, '');
    return { allow: response.headers.get('allow'), patch: response.headers.get('accept-patch') };
  });
  await check('405 includes Allow', async () => {
    const response = await request('/v1/tasks', 'DELETE');
    const observed = error(response, 405, 'method_not_allowed');
    assert.equal(response.headers.get('allow'), 'GET, HEAD, POST, OPTIONS');
    return observed;
  });
  await check('unknown route is 404', async () => error(await request('/v2/tasks'), 404, 'not_found'));
  await check('invalid identifier is 400', async () => error(await request('/v1/tasks/01'), 400, 'invalid_id'));
  await check('malformed percent encoding is 400', async () => error(await request('/v1/tasks/%ZZ'), 400, 'invalid_path'));
  await check('unknown item query rejected', async () => error(await request('/v1/tasks/2?extra=1'), 400, 'invalid_query'));
});

await using({}, async request => {
  for (let id = 1; id <= 5; id++)
    status(await request('/v1/tasks', 'POST', input('Task ' + id, id % 2 === 0), { 'Idempotency-Key': 'page-' + id }), 201);
  for (const [query, code] of [
    ['limit=0', 'invalid_limit'], ['limit=100', 'invalid_limit'],
    ['completed=yes', 'invalid_filter'], ['order=random', 'invalid_order'],
    ['limit=1&limit=2', 'invalid_query'], ['extra=1', 'invalid_query'],
    ['cursor=not-a-cursor', 'invalid_cursor'],
  ]) await check('query rejects ' + query, async () => error(await request('/v1/tasks?' + query), 400, code));
  const first = status(await request('/v1/tasks?limit=2'), 200);
  await check('first page has bounded items and next link', async () => {
    assert.deepEqual(first.body.items.map(t => t.id), [1, 2]);
    assert.equal(first.headers.get('link'), '<' + first.body.next + '>; rel="next"');
    return { ids: first.body.items.map(t => t.id), hasNext: true };
  });
  await check('keyset continuation survives deletion before cursor', async () => {
    const item = await request('/v1/tasks/1');
    status(await request('/v1/tasks/1', 'DELETE', undefined, { 'If-Match': item.headers.get('etag') }), 204);
    const second = status(await request(first.body.next), 200);
    assert.deepEqual(second.body.items.map(t => t.id), [3, 4]);
    return { ids: second.body.items.map(t => t.id) };
  });
  await check('keyset walk sees later insertion without duplicating earlier IDs', async () => {
    status(await request('/v1/tasks', 'POST', input('Inserted'), { 'Idempotency-Key': 'insert-later' }), 201);
    const second = await request(first.body.next);
    const third = status(await request(second.body.next), 200);
    assert.deepEqual(third.body.items.map(t => t.id), [5, 6]);
    assert.equal(third.body.next, null);
    return { ids: third.body.items.map(t => t.id), snapshot: false };
  });
  await check('filter and descending order compose', async () => {
    const response = status(await request('/v1/tasks?completed=true&order=desc&limit=1'), 200);
    assert.deepEqual(response.body.items.map(t => t.id), [4]);
    const next = status(await request(response.body.next), 200);
    assert.deepEqual(next.body.items.map(t => t.id), [2]);
    assert.equal(next.body.next, null);
    return { first: [4], next: [2] };
  });
  await check('cursor cannot switch ordering', async () =>
    error(await request(first.body.next.replace('order=asc', 'order=desc')), 400, 'invalid_cursor'));
  await check('cursor cannot switch filter', async () =>
    error(await request(first.body.next + '&completed=true'), 400, 'invalid_cursor'));
});

await using({}, async request => {
  const created = await request('/v1/tasks', 'POST', input('Original'), { 'Idempotency-Key': 'race' });
  await check('two concurrent editors produce one winner and one 412', async () => {
    const responses = await Promise.all(['Editor A', 'Editor B'].map(title =>
      request('/v1/tasks/1', 'PATCH', { title }, { 'If-Match': created.headers.get('etag') })));
    assert.deepEqual(responses.map(r => r.status).sort(), [200, 412]);
    const winner = responses.find(r => r.status === 200);
    assert.deepEqual((await request('/v1/tasks/1')).body, winner.body);
    return { statuses: responses.map(r => r.status).sort(), storedMatchesWinner: true };
  });
});

await using({}, async (request, server) => {
  const created = await request('/v1/tasks', 'POST', input('Before'), { 'Idempotency-Key': 'split' });
  await check('write checks current state after a slow request body finishes', async () => {
    const arrived = once(server, 'request');
    let slow;
    const finished = new Promise((resolve, reject) => {
      slow = httpRequest({
        host: '127.0.0.1', port: server.address().port, path: '/v1/tasks/1', method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'If-Match': created.headers.get('etag') },
      }, response => {
        const chunks = [];
        response.on('data', chunk => chunks.push(chunk));
        response.on('end', () => resolve({
          status: response.statusCode, body: JSON.parse(Buffer.concat(chunks).toString()),
        }));
        response.on('error', reject);
      });
      slow.on('error', reject);
      slow.setTimeout(4000, () => slow.destroy(new Error('slow-body test deadline')));
      slow.write('{"title":');
    });
    await arrived;
    const fast = status(await request('/v1/tasks/1', 'PATCH', { title: 'Fast editor' }, {
      'If-Match': created.headers.get('etag'),
    }), 200);
    slow.end('"Slow editor"}');
    const response = await finished;
    assert.equal(response.status, 412);
    assert.equal(response.body.code, 'stale_version');
    assert.deepEqual((await request('/v1/tasks/1')).body, fast.body);
    return { fast: 200, slow: 412, title: fast.body.title };
  });
});

const entered = deferred(), release = deferred(), replayEntered = deferred();
let creations = 0;
await using({
  beforeCreate: async () => { creations++; entered.resolve(); await release.promise; },
  onReplay: () => replayEntered.resolve(),
}, async request => {
  const owner = request('/v1/tasks', 'POST', input('Once'), { 'Idempotency-Key': 'pending' });
  await entered.promise;
  const retry = request('/v1/tasks', 'POST', input('Once'), { 'Idempotency-Key': 'pending' });
  await replayEntered.promise;
  await check('different input conflicts while same-key operation is pending', async () =>
    error(await request('/v1/tasks', 'POST', input('Other'), { 'Idempotency-Key': 'pending' }), 409, 'key_conflict'));
  await check('unrelated GET progresses while creation is pending', async () => {
    const response = status(await request(), 200);
    assert.equal(response.body.items.length, 0);
    return { items: 0 };
  });
  release.resolve();
  await check('overlapping same-key requests share one operation', async () => {
    const [a, b] = await Promise.all([owner, retry]);
    status(a, 201); status(b, 201);
    assert.deepEqual(a.body, b.body);
    assert.equal(creations, 1);
    assert.equal((await request()).body.items.length, 1);
    assert.equal(b.headers.get('idempotency-replayed'), 'true');
    return { statuses: [a.status, b.status], creations, total: 1 };
  });
});

let clock = 0;
await using({ now: () => clock, idempotencyTtlMs: 60_000 }, async request => {
  await request('/v1/tasks', 'POST', input('Expires'), { 'Idempotency-Key': 'ttl' });
  clock = 59_999;
  await check('retained key deduplicates before expiry', async () => {
    assert.equal((await request('/v1/tasks', 'POST', input('Expires'), { 'Idempotency-Key': 'ttl' })).body.id, 1);
    return { id: 1, atMs: clock };
  });
  clock = 60_000;
  await check('expired key can create again', async () => {
    const response = status(await request('/v1/tasks', 'POST', input('Expires'), { 'Idempotency-Key': 'ttl' }), 201);
    assert.equal(response.body.id, 2);
    assert.equal((await request()).body.items.length, 2);
    return { id: response.body.id, atMs: clock, total: 2 };
  });
});

let attempts = 0;
await using({ beforeCreate: async () => { if (++attempts === 1) throw new Error('private database detail'); } }, async request => {
  await check('unexpected failure returns private problem and permits retry', async () => {
    const failed = await request('/v1/tasks', 'POST', input('Retry'), { 'Idempotency-Key': 'failure' });
    error(failed, 500, 'internal_error');
    assert.equal(failed.text.includes('database'), false);
    assert.equal((await request()).body.items.length, 0);
    const retried = status(await request('/v1/tasks', 'POST', input('Retry'), { 'Idempotency-Key': 'failure' }), 201);
    assert.equal(retried.body.id, 1);
    return { first: 500, retry: 201, attempts, total: 1 };
  });
});

let rateClock = 8500;
await using({ now: () => rateClock }, async request => {
  await check('fixed-window budget allows two requests', async () => {
    const a = status(await request('/v1/limited'), 200), b = status(await request('/v1/limited'), 200);
    assert.deepEqual([a.body.remaining, b.body.remaining], [1, 0]);
    return { remaining: [1, 0] };
  });
  await check('exhausted budget returns 429 and rounded-up Retry-After', async () => {
    const response = await request('/v1/limited');
    error(response, 429, 'rate_limited');
    assert.equal(response.headers.get('retry-after'), '2');
    return { status: response.status, retryAfterSeconds: 2 };
  });
  await check('rate limiting one route does not block task reads', async () => status(await request(), 200).status);
  rateClock = 10_000;
  await check('next fixed window resets budget', async () => {
    const response = status(await request('/v1/limited'), 200);
    assert.equal(response.body.remaining, 1);
    return { atMs: rateClock, remaining: 1 };
  });
});

await writeFile(new URL('./results.json', import.meta.url), JSON.stringify({
  node: process.version, passed: results.length, checks: results,
}, null, 2) + '\n');
console.log('Verified ' + results.length + ' HTTP checks; all temporary listeners closed.');
