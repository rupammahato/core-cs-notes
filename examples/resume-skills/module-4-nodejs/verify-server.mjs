import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createStudyServer, sampleFile } from './server.mjs';

let checks = 0;
function check(name, assertion) {
  assertion();
  checks++;
  console.log('PASS HTTP ' + name);
}
async function listen(app) {
  await new Promise((resolve, reject) => {
    app.server.once('error', reject);
    app.server.listen(0, '127.0.0.1', resolve);
  });
  return 'http://127.0.0.1:' + app.server.address().port;
}
async function request(base, route, options = {}) {
  const response = await fetch(base + route, {
    ...options, headers: { connection: 'close' }, signal: AbortSignal.timeout(2000),
  });
  return { status: response.status, headers: response.headers, text: await response.text() };
}
async function close(app) {
  await new Promise((resolve, reject) => app.server.close(error => error ? reject(error) : resolve()));
}
const expected = await readFile(sampleFile, 'utf8');
const app = createStudyServer();
const base = await listen(app);
try {
  const health = await request(base, '/health');
  check('health', () => { assert.equal(health.status, 200); assert.deepEqual(JSON.parse(health.text), { status: 'ok' }); });
  const info = await request(base, '/api/info');
  check('async-file-info', () => { assert.equal(info.status, 200); assert.equal(JSON.parse(info.text).bytes, Buffer.byteLength(expected)); });
  const download = await request(base, '/download');
  check('streamed-download', () => {
    assert.equal(download.status, 200);
    assert.equal(download.text, expected);
    assert.equal(Number(download.headers.get('content-length')), Buffer.byteLength(expected));
    assert.ok(download.headers.get('content-type').startsWith('text/plain'));
  });
  const fixed = await request(base, '/download?file=ignored');
  check('fixed-file-selection', () => assert.equal(fixed.text, expected));
  const absent = await request(base, '/missing');
  check('unknown-route', () => { assert.equal(absent.status, 404); assert.equal(JSON.parse(absent.text).error, 'not_found'); });
  const method = await request(base, '/health', { method: 'POST' });
  check('method-and-allow', () => { assert.equal(method.status, 405); assert.equal(method.headers.get('allow'), 'GET'); });
  app.beginDrain();
  const draining = await request(base, '/health');
  check('draining-response', () => { assert.equal(draining.status, 503); assert.equal(JSON.parse(draining.text).error, 'draining'); });
} finally { await close(app); }

let release, bothReady;
const gate = new Promise(resolve => { release = resolve; });
const ready = new Promise(resolve => { bothReady = resolve; });
let active = 0;
let peak = 0;
const overlapping = createStudyServer({
  loadRecord: async () => {
    active++;
    peak = Math.max(peak, active);
    if (active === 2) bothReady();
    try { await gate; return 'record'; }
    finally { active--; }
  },
});
const overlapBase = await listen(overlapping);
const joined = Promise.allSettled([
  request(overlapBase, '/api/info'), request(overlapBase, '/api/info'),
]);
let timer;
try {
  await Promise.race([ready, new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error('requests did not overlap')), 2000);
  })]);
  clearTimeout(timer);
  check('two-requests-in-flight', () => { assert.equal(active, 2); assert.equal(peak, 2); });
  const health = await request(overlapBase, '/health');
  check('health-progresses-during-wait', () => { assert.equal(health.status, 200); assert.equal(active, 2); });
  overlapping.beginDrain();
  const denied = await request(overlapBase, '/api/info');
  check('drain-stops-new-work', () => { assert.equal(denied.status, 503); assert.equal(active, 2); });
  release();
  const results = await joined;
  check('in-flight-work-completes', () => {
    assert.ok(results.every(result => result.status === 'fulfilled' &&
      result.value.status === 200 && JSON.parse(result.value.text).bytes === 6));
    assert.equal(active, 0);
  });
} finally {
  clearTimeout(timer);
  release();
  await joined;
  await close(overlapping);
}
check('listener-closed', () => assert.equal(overlapping.server.listening, false));

const missing = createStudyServer({ filePath: new URL('./fixtures/does-not-exist.txt', import.meta.url) });
const missingBase = await listen(missing);
try {
  const download = await request(missingBase, '/download');
  check('missing-file-before-headers', () => { assert.equal(download.status, 404); assert.equal(JSON.parse(download.text).error, 'file_missing'); });
  const info = await request(missingBase, '/api/info');
  check('missing-file-async-read', () => { assert.equal(info.status, 404); assert.equal(JSON.parse(info.text).error, 'file_missing'); });
} finally { await close(missing); }

const failed = createStudyServer({ loadRecord: async () => { throw new Error('private detail'); } });
const failedBase = await listen(failed);
try {
  const info = await request(failedBase, '/api/info');
  check('async-failure-mapped', () => { assert.equal(info.status, 500); assert.deepEqual(JSON.parse(info.text), { error: 'internal_error' }); });
  const health = await request(failedBase, '/health');
  check('healthy-after-request-failure', () => assert.equal(health.status, 200));
} finally { await close(failed); }
console.log('Verified ' + checks + ' HTTP checks');
