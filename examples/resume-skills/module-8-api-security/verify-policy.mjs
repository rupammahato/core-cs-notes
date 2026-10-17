import { allowed, writable, safeFilename, textContent, escapeHtmlText, createBudget } from './security.mjs';
import { assert, check, denied, save } from './checks.mjs';

const shared = { ownerId: 'other', visibility: 'tenant' };
const ownPrivate = { ownerId: 'alice', visibility: 'private' };
const otherPrivate = { ownerId: 'other', visibility: 'private' };
for (const [role, expected] of [
  ['viewer', [true, true, false, false, false, false, false]],
  ['editor', [true, true, false, true, true, false, true]],
  ['admin', [true, true, true, true, true, true, true]],
  ['unexpected', [false, false, false, false, false, false, false]],
]) await check(role + ' permission matrix', async () => {
  const actual = [
    allowed(role, 'alice', 'read', shared), allowed(role, 'alice', 'read', ownPrivate),
    allowed(role, 'alice', 'read', otherPrivate), allowed(role, 'alice', 'create'),
    allowed(role, 'alice', 'update', ownPrivate), allowed(role, 'alice', 'update', shared),
    allowed(role, 'alice', 'delete', ownPrivate),
  ];
  assert.deepEqual(actual, expected);
  assert.equal(allowed(role, 'alice', 'unrecognized-action', ownPrivate), false);
  return actual;
});
await check('unknown writable properties rejected', async () =>
  denied(async () => writable({ title: 'A', ownerId: 'attacker' }), 400, 'unknown_field'));
await check('prototype property rejected without polluting objects', async () => {
  await denied(async () => writable(JSON.parse('{"title":"A","__proto__":{"polluted":true}}')), 400, 'unknown_field');
  assert.equal({}.polluted, undefined); return { rejected: true, polluted: false };
});
await check('create normalizes title and defaults visibility', async () => {
  assert.deepEqual(writable({ title: ' A ' }), { title: 'A', visibility: 'private' });
  return { title: 'A', visibility: 'private' };
});
await check('empty patch rejected', async () => denied(async () => writable({}, true), 400, 'empty_patch'));
await check('filename accepts narrow text display name', async () => {
  assert.equal(safeFilename('notes-1.txt'), 'notes-1.txt'); return 'notes-1.txt';
});
for (const name of ['../notes.txt', '..\\notes.txt', 'notes.pdf', 'notes.txt.exe', '.hidden.txt', 'a\0.txt'])
  await check('unsafe filename rejected ' + JSON.stringify(name), async () =>
    denied(async () => safeFilename(name), 400, 'invalid_filename'));
await check('UTF-8 content preserves ordinary text', async () => {
  assert.equal(textContent(Buffer.from('Placement café')), 'Placement café'); return 'Placement café';
});
await check('invalid UTF-8 rejected', async () =>
  denied(async () => textContent(Buffer.from([0xff])), 400, 'invalid_utf8'));
await check('NUL-bearing text rejected', async () =>
  denied(async () => textContent(Buffer.from([65, 0, 66])), 400, 'invalid_text'));
await check('text size checked at service boundary', async () =>
  denied(async () => textContent(Buffer.alloc(1025, 65)), 413, 'body_too_large'));
await check('HTML text context escapes metacharacters', async () => {
  const escaped = escapeHtmlText('<script>alert("x")</script>&');
  assert.equal(escaped, '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;&amp;');
  return escaped;
});
let clock = 8500;
const budget = createBudget({ now: () => clock, limit: 2 });
await check('attempt budget scoped by verified tenant and subject', async () => {
  budget('alpha', 'alice'); budget('alpha', 'alice');
  await denied(async () => budget('alpha', 'alice'), 429, 'import_rate_limited');
  budget('alpha', 'bob'); budget('beta', 'alice');
  return { exhausted: ['alpha', 'alice'], otherSubjectAllowed: true, otherTenantAllowed: true };
});
await check('rate-limit delay rounds up and next window resets', async () => {
  try { budget('alpha', 'alice'); assert.fail('Expected denial'); }
  catch (error) { assert.equal(error.headers['Retry-After'], '2'); }
  clock = 10000; budget('alpha', 'alice');
  return { retryAfterSeconds: 2, newWindowAllowed: true };
});
await save('policy');
