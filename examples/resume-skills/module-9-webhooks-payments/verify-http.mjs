import { once } from 'node:events';
import { sign } from './webhook.mjs';
import { openStore } from './store.mjs';
import { endpoints, orders, fixtureEvent } from './fixtures.mjs';
import { createWebhookServer } from './server.mjs';
import { assert, check, save } from './checks.mjs';

async function using(options, fn) {
  const store = openStore(':memory:', options); store.seed(orders);
  const server = createWebhookServer({ endpoints, store });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  const base = 'http://127.0.0.1:' + server.address().port;
  async function request({
    path = '/webhooks/alpha', method = 'POST', raw = Buffer.from(JSON.stringify(fixtureEvent())),
    secret = endpoints.alpha.secrets[0], eventId = 'http-event', headers = {},
  } = {}) {
    const response = await fetch(base + path, {
      method, headers: {
        'Content-Type': 'application/json', 'X-Razorpay-Signature': sign(raw, secret),
        'X-Razorpay-Event-Id': eventId, ...headers,
      }, ...(method === 'GET' ? {} : { body: raw }), signal: AbortSignal.timeout(4000),
    });
    assert.equal(response.headers.get('cache-control'), 'no-store');
    return { status: response.status, headers: response.headers, body: await response.json() };
  }
  try { await fn({ store, request }); }
  finally {
    const closed = once(server, 'close'); server.close(); server.closeAllConnections(); await closed;
    store.close();
  }
}
const error = (response, expected, code) => {
  assert.equal(response.status, expected); assert.deepEqual(response.body, { code });
  return { status: expected, code };
};
const zero = store => {
  assert.equal(store.snapshot().inbox.length, 0); assert.equal(store.snapshot().ledger.length, 0);
};
await using({}, async ({ store, request }) => {
  for (const [name, options, expected, code] of [
    ['wrong signature', { secret: 'wrong' }, 401, 'invalid_signature'],
    ['missing signature', { headers: { 'X-Razorpay-Signature': '' } }, 401, 'invalid_signature'],
    ['malformed signature', { headers: { 'X-Razorpay-Signature': 'zz'.repeat(32) } }, 401, 'invalid_signature'],
    ['missing event ID', { eventId: '' }, 400, 'invalid_event_id'],
    ['oversize event ID', { eventId: 'x'.repeat(81) }, 400, 'invalid_event_id'],
    ['unsupported type', { headers: { 'Content-Type': 'text/plain' } }, 415, 'unsupported_body_format'],
    ['compressed content', { headers: { 'Content-Encoding': 'gzip' } }, 415, 'unsupported_body_format'],
    ['oversize body', { raw: Buffer.alloc(16385, 65) }, 413, 'body_too_large'],
    ['signed malformed JSON', { raw: Buffer.from('{') }, 400, 'invalid_json'],
    ['signed invalid UTF-8', { raw: Buffer.from([0xff]) }, 400, 'invalid_json'],
    ['wrong account', { raw: Buffer.from(JSON.stringify(fixtureEvent({ endpoint: 'beta' }))) }, 403, 'account_mismatch'],
    ['missing payment fields', { raw: Buffer.from(JSON.stringify({ entity: 'event', account_id: 'acc_alpha', event: 'payment.captured' })) }, 400, 'invalid_payment'],
    ['wrong status for event', { raw: Buffer.from(JSON.stringify(fixtureEvent({ type: 'payment.authorized', extra: { payload: fixtureEvent().payload } }))) }, 400, 'invalid_payment'],
    ['unknown route', { path: '/webhooks/not-configured' }, 404, 'not_found'],
  ]) await check('HTTP rejects ' + name + ' before inbox effects', async () => {
    const result = error(await request(options), expected, code); zero(store); return result;
  });
  await check('HTTP method policy includes Allow', async () => {
    const response = await request({ method: 'GET' });
    error(response, 405, 'method_not_allowed'); assert.equal(response.headers.get('allow'), 'POST'); zero(store);
    return { status: 405, allow: 'POST' };
  });
  await check('signature checked before parsing invalid bytes', async () => {
    const response = await request({ raw: Buffer.from('{'), secret: 'wrong' });
    error(response, 401, 'invalid_signature'); zero(store); return { status: 401 };
  });
  await check('raw formatting change breaks otherwise equivalent JSON signature', async () => {
    const compact = Buffer.from(JSON.stringify(fixtureEvent()));
    const pretty = Buffer.from(JSON.stringify(fixtureEvent(), null, 2));
    error(await request({ raw: pretty, headers: { 'X-Razorpay-Signature': sign(compact, endpoints.alpha.secrets[0]) } }), 401, 'invalid_signature');
    zero(store); return { status: 401 };
  });
  await check('acknowledgment follows inbox commit but precedes worker effect', async () => {
    const response = await request();
    assert.equal(response.status, 202); assert.equal(response.body.state, 'pending');
    assert.equal(store.snapshot().inbox.length, 1); assert.equal(store.snapshot().ledger.length, 0);
    store.processNext(); assert.equal(store.snapshot().ledger.length, 1);
    return { ack: 202, inboxAtAck: 1, ledgerAtAck: 0, ledgerAfterWorker: 1 };
  });
  await check('overlapping same-delivery requests retain one inbox row and one grant', async () => {
    const responses = await Promise.all([1, 2].map(() => request({ eventId: 'concurrent' })));
    assert.deepEqual(responses.map(r => r.status), [202, 202]);
    assert.equal(responses.filter(r => r.body.duplicate).length, 1);
    assert.equal(store.snapshot().inbox.filter(r => r.event_id === 'concurrent').length, 1);
    store.processNext(); assert.equal(store.snapshot().ledger.length, 1);
    return { responses: [202, 202], deliveryRows: 1, totalLedgerRows: 1 };
  });
  await check('same raw payload under changed unsigned delivery header is business-idempotent', async () => {
    const response = await request({ eventId: 'changed-header' }); assert.equal(response.status, 202);
    store.processNext(); assert.equal(store.snapshot().ledger.length, 1);
    return { status: 202, ledgerRows: 1, alphaCredits: store.snapshot().balances[0].credits };
  });
  await check('configured old secret permits delayed retry', async () => {
    const response = await request({ eventId: 'old-secret', secret: endpoints.alpha.secrets[1] });
    assert.equal(response.status, 202); store.processNext();
    return { status: 202, ledgerRows: store.snapshot().ledger.length };
  });
  await check('endpoint secret cannot authenticate another configured account', async () => {
    error(await request({ path: '/webhooks/beta', eventId: 'bad-account', raw: Buffer.from(JSON.stringify(fixtureEvent({ endpoint: 'beta' }))) }), 401, 'invalid_signature');
    return { status: 401 };
  });
  await check('tenant header cannot reroute trusted provider-order mapping', async () => {
    const response = await request({ eventId: 'tenant-header', headers: { 'X-Tenant-Id': 'beta' } });
    assert.equal(response.status, 202); store.processNext();
    assert.equal(store.snapshot().balances.some(r => r.tenant === 'beta'), false);
    return { alphaCredits: store.snapshot().balances[0].credits, betaCredited: false };
  });
  await check('unsupported signed event is durably ignored without granting', async () => {
    const raw = Buffer.from(JSON.stringify({ entity: 'event', account_id: 'acc_alpha', event: 'customer.updated' }));
    const response = await request({ raw, eventId: 'ignored' });
    assert.equal(response.status, 202); assert.equal(response.body.state, 'ignored');
    assert.equal(store.snapshot().ledger.length, 1);
    return { ack: 202, state: 'ignored', ledgerRows: 1 };
  });
});
let failBefore = true;
await using({ onPhase: phase => {
  if (phase === 'before-inbox-insert' && failBefore) { failBefore = false; throw new Error('database unavailable'); }
} }, async ({ store, request }) => {
  await check('failed inbox persistence returns 503 and retry can accept', async () => {
    error(await request(), 503, 'temporarily_unavailable'); zero(store);
    const retried = await request(); assert.equal(retried.status, 202);
    assert.equal(store.snapshot().inbox.length, 1);
    return { first: 503, retry: 202, inboxRows: 1 };
  });
});
let failAfter = true;
await using({ onPhase: phase => {
  if (phase === 'after-inbox-commit' && failAfter) { failAfter = false; throw new Error('lost acknowledgment'); }
} }, async ({ store, request }) => {
  await check('post-commit acknowledgment failure leaves retryable durable acceptance', async () => {
    error(await request(), 503, 'temporarily_unavailable');
    assert.equal(store.snapshot().inbox.length, 1);
    const retry = await request(); assert.equal(retry.status, 202); assert.equal(retry.body.duplicate, true);
    store.processNext(); assert.equal(store.snapshot().ledger.length, 1);
    return { first: 503, retry: 202, duplicate: true, ledgerRows: 1 };
  });
});
await save('http');
console.log('All temporary HTTP listeners closed.');
