import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { gzipSync } from 'node:zlib';
import { createApp } from './app.mjs';
import { createProductRepository } from './repository.mjs';

const matrix = JSON.parse(await readFile(new URL('./http-cases.json', import.meta.url), 'utf8'));
const completed = [];
function record(id, details = {}) {
  completed.push({ id, ...details });
  console.log('PASS API ' + id);
}
async function listen(app) {
  const server = createServer(app);
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return { server, base: 'http://127.0.0.1:' + server.address().port };
}
async function close(server) {
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
}
async function request(base, item) {
  const headers = { connection: 'close', ...item.headers };
  let body = item.body;
  let method = item.method ?? 'GET';
  if (Object.hasOwn(item, 'json')) {
    headers['content-type'] = 'application/json';
    body = JSON.stringify(item.json);
    method = 'POST';
  }
  if (Object.hasOwn(item, 'gzip')) {
    headers['content-type'] = 'application/json';
    headers['content-encoding'] = 'gzip';
    body = gzipSync(JSON.stringify(item.gzip));
    method = 'POST';
  }
  const response = await fetch(base + item.route, {
    method, headers, body, signal: AbortSignal.timeout(2000),
  });
  const text = await response.text();
  return {
    status: response.status, headers: Object.fromEntries(response.headers), text,
    body: text ? JSON.parse(text) : undefined,
  };
}
const traces = [];
const original = createProductRepository();
let calls = 0;
const repository = {
  async findById(id, trace) { calls++; return original.findById(id, trace); },
};
const main = await listen(createApp({ repository, onComplete: entry => traces.push(entry) }));
const ids = new Set();
try {
  for (const item of matrix) {
    const before = calls;
    const response = await request(main.base, item);
    assert.equal(response.status, item.status, item.id);
    assert.equal(calls - before, item.repoDelta, item.id + ': data-access boundary');
    const requestId = response.headers['x-request-id'];
    assert.match(requestId, /^[0-9a-f-]{36}$/);
    assert.ok(!ids.has(requestId));
    ids.add(requestId);
    if (item.method !== 'HEAD') {
      assert.ok(response.headers['content-type'].startsWith('application/json'));
      assert.equal(response.body.requestId, requestId);
    }
    if (item.code) assert.deepEqual(response.body.error, { code: item.code });
    if (item.allow) assert.equal(response.headers.allow, item.allow);
    if (item.check === 'health') assert.equal(response.body.status, 'ok');
    if (item.check === 'product') {
      assert.deepEqual(response.body.product, { id: 7, name: 'Keyboard', unitPricePaise: 25000, stock: 4 });
      assert.ok(!Object.hasOwn(response.body.product, 'internalCostPaise'));
    }
    if (item.check === 'head') assert.equal(response.text, '');
    if (item.check === 'quote') {
      assert.deepEqual(response.body.quote, { productId: 7, quantity: 2, unitPricePaise: 25000, totalPaise: 50000 });
    }
    if (item.check === 'unchanged') {
      assert.equal(response.body.quote.totalPaise, 100000);
      assert.equal((await original.findById(7)).stock, 4);
    }
    const trace = traces.find(entry => entry.requestId === requestId);
    assert.ok(trace, item.id + ': completion observation');
    assert.equal(trace.status, response.status);
    record(item.id, { status: response.status, code: item.code, trace: trace.trace });
  }
  const quote = completed.find(item => item.id === 'authoritative-quote');
  const malformed = completed.find(item => item.id === 'malformed-json');
  assert.deepEqual(quote.trace, ['request', 'router', 'media-type', 'parsed', 'validate-body', 'controller', 'service', 'repository']);
  assert.deepEqual(malformed.trace, ['request', 'router', 'media-type', 'error']);
  record('middleware-success-and-failure-traces');
  console.log('TRACE quote: ' + quote.trace.join(' > '));
  console.log('TRACE malformed: ' + malformed.trace.join(' > '));
} finally { await close(main.server); }

const failed = await listen(createApp({
  repository: { async findById() { throw new Error('private adapter failure'); } },
}));
try {
  const response = await request(failed.base, { route: '/api/products/7' });
  assert.equal(response.status, 500);
  assert.deepEqual(response.body.error, { code: 'internal_error' });
  assert.ok(!response.text.includes('private adapter failure'));
  record('async-repository-failure-hidden');
  assert.equal((await request(failed.base, { route: '/health' })).status, 200);
  record('request-failure-does-not-kill-app');
} finally { await close(failed.server); }

let release, ready;
const gate = new Promise(resolve => { release = resolve; });
const bothReady = new Promise(resolve => { ready = resolve; });
let active = 0;
const concurrent = await listen(createApp({
  repository: {
    async findById(id, trace) {
      trace.push('repository');
      active++;
      if (active === 2) ready();
      try { await gate; return { id, unitPricePaise: 25000, stock: 4 }; }
      finally { active--; }
    },
  },
}));
const joined = Promise.allSettled([1, 2].map(quantity => request(concurrent.base, {
  route: '/api/quotes', json: { productId: 7, quantity },
})));
let timer;
try {
  await Promise.race([bothReady, new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error('concurrent requests did not arrive')), 2000);
  })]);
  clearTimeout(timer);
  assert.equal(active, 2);
  assert.equal((await request(concurrent.base, { route: '/health' })).status, 200);
  assert.equal(active, 2);
  record('health-progresses-during-async-work');
  release();
  const results = await joined;
  assert.ok(results.every(result => result.status === 'fulfilled'));
  const responses = results.map(result => result.value);
  assert.deepEqual(responses.map(response => response.body.quote.quantity), [1, 2]);
  assert.deepEqual(responses.map(response => response.body.quote.totalPaise), [25000, 50000]);
  assert.notEqual(responses[0].body.requestId, responses[1].body.requestId);
  assert.equal(active, 0);
  record('request-locals-stay-independent');
} finally {
  clearTimeout(timer);
  release();
  await joined;
  await close(concurrent.server);
}
record('listeners-closed');
await writeFile(new URL('./http-results.json', import.meta.url),
  JSON.stringify({ node: process.version, checks: completed }, null, 2) + '\n');
console.log('Verified ' + completed.length + ' Express API checks');
