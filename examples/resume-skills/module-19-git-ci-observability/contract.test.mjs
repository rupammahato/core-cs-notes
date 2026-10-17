import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { createTelemetry } from './telemetry.mjs';
import { createApplication } from './app.mjs';
import { attempt } from './load.mjs';
const telemetry = createTelemetry();
const app = await createApplication(telemetry);
const url = 'http://127.0.0.1:' + app.port;
after(async () => { await app.close(); await telemetry.close(); });
test('success contract over real HTTP', async () => {
  const response = await attempt(url + '/work?delay=1');
  assert.equal(response.status, 200);
  const body = JSON.parse(response.body);
  assert.equal(body.result, 'computed'); assert.equal(body.release, 'v1');
  assert.match(body.request_id, /^[a-f0-9-]{36}$/); assert.match(body.trace_id, /^[a-f0-9]{32}$/);
});
test('invalid input is rejected at the API boundary', async () => {
  const response = await attempt(url + '/work?delay=999');
  assert.equal(response.status, 400); assert.equal(JSON.parse(response.body).error, 'delay must be 0..200ms');
});
test('dependency failure has a stable public error contract', async () => {
  const response = await attempt(url + '/work?delay=1&fail=1');
  assert.equal(response.status, 503); assert.equal(JSON.parse(response.body).error, 'dependency unavailable');
  assert.ok(!response.body.includes('stack'));
});
