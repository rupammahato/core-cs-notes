import assert from 'node:assert/strict';
import { mkdtemp, rm, readFile, writeFile, access } from 'node:fs/promises';
import { tmpdir, platform, release } from 'node:os';
import path from 'node:path';
import { once } from 'node:events';
import { DatabaseSync } from 'node:sqlite';
import ts from 'typescript';
import { parse } from 'acorn';
import { NotesService, RuleError } from './dist/notes.js';
import { SqliteNotes } from './dist/sqlite.js';
import { createApp } from './dist/http.js';

const checks = [], observations = {}, servers = [], repositories = [];
function check(group, name, work) { work(); checks.push({ group, name, passed: true }); }
const directory = await mkdtemp(path.join(tmpdir(), 'placement-a1-'));
let sequence = 0;
const who = { tenant: 'alpha', owner: 'alice' };
const initial = { title: 'Transactions', content: 'Atomic state changes' };
const updated = { title: 'Transactions revised', content: 'One authoritative commit' };
function repo(file, hook) {
  const value = new SqliteNotes(path.join(directory, file), () => 'note_' + ++sequence, hook);
  repositories.push(value);
  return value;
}
function closeRepository(value) { value.close(); repositories.splice(repositories.indexOf(value), 1); }
async function listen(app) {
  const server = app.listen(0, '127.0.0.1');
  servers.push(server);
  await once(server, 'listening');
  return 'http://127.0.0.1:' + server.address().port;
}
let httpPort;
try {
  // Parse emitted JavaScript to check the actual runtime dependency graph.
  const allowed = { 'notes.ts': [], 'sqlite.ts': ['./notes.js'], 'http.ts': ['./notes.js'],
    'composition.ts': ['./notes.js', './sqlite.js', './http.js'] };
  observations.dependencies = {};
  for (const [name, expected] of Object.entries(allowed)) {
    const source = await readFile(new URL('dist/' + name.replace('.ts', '.js'), import.meta.url), 'utf8');
    const ast = parse(source, { ecmaVersion: 'latest', sourceType: 'module' });
    const imports = ast.body.filter(item => item.type === 'ImportDeclaration').map(item => item.source.value);
    observations.dependencies[name] = imports;
    check('boundaries', name + ' local import direction', () => {
      assert.deepEqual(imports.filter(item => item.startsWith('.')).sort(), [...expected].sort());
      if (name === 'notes.ts') assert.ok(imports.every(item => item === 'node:buffer'));
    });
  }
  const storage = repo('notes.sqlite');
  const service = new NotesService(storage);
  let result = service.create(who, 'direct_create', initial);
  const directId = result.note.id;
  check('service_repository', 'direct use case without HTTP', () => assert.equal(result.note.revision, 1));
  check('service_repository', 'new operation reports non-replay', () => assert.equal(result.replayed, false));
  check('service_repository', 'direct read returns committed value', () => assert.deepEqual(service.get(who, directId), result.note));
  check('service_repository', 'body cannot assign owner', () => assert.throws(() => service.create(who, 'bad', { ...initial, owner: 'bob' }), RuleError));
  check('service_repository', 'blank title rejected', () => assert.throws(() => service.create(who, 'bad', { ...initial, title: ' ' }), RuleError));
  check('service_repository', 'NUL title rejected before SQLite', () => assert.throws(() => service.create(who, 'bad', { ...initial, title: '\0' }), error => error.code === 'invalid'));
  check('service_repository', 'trailing newline is not an operation identifier', () => assert.throws(() => service.create(who, 'key\n', initial), error => error.code === 'invalid'));
  check('service_repository', 'multibyte content limit uses bytes', () => assert.throws(() => service.create(who, 'bad', { ...initial, content: '\u20ac'.repeat(1366) }), RuleError));
  check('service_repository', '120 Unicode code points accepted', () => assert.equal(service.create(who, 'unicode_title', { ...initial, title: '\u{1f600}'.repeat(120) }).note.title.length, 240));
  check('service_repository', 'unsafe revision rejected', () => assert.throws(() => service.replace(who, directId, Number.MAX_SAFE_INTEGER + 1, initial), RuleError));
  check('service_repository', 'same operation different input conflicts', () => assert.throws(() => service.create(who, 'direct_create', updated), error => error.code === 'conflict'));
  result = service.replace(who, directId, 1, updated);
  check('service_repository', 'replace advances revision', () => assert.equal(result.revision, 2));
  check('service_repository', 'replay returns original outcome after edit', () => assert.deepEqual(service.create(who, 'direct_create', initial).note, { id: directId, ...initial, revision: 1 }));
  check('service_repository', 'replay does not revert current note', () => assert.deepEqual(service.get(who, directId), result));
  check('service_repository', 'stale direct edit rejected', () => assert.throws(() => service.replace(who, directId, 1, initial), error => error.code === 'stale'));
  closeRepository(storage);
  const reopened = repo('notes.sqlite');
  const reopenedService = new NotesService(reopened);
  check('service_repository', 'reopen persists note state', () => assert.equal(reopenedService.get(who, directId).revision, 2));
  check('service_repository', 'reopen persists operation outcome', () => assert.equal(reopenedService.create(who, 'direct_create', initial).replayed, true));
  observations.persistence = { currentRevision: reopenedService.get(who, directId).revision,
    replayRevision: reopenedService.create(who, 'direct_create', initial).note.revision, reopened: true };

  let shouldFail = true;
  const faulted = repo('rollback.sqlite', () => { if (shouldFail) throw new Error('owned injected fault'); });
  const faultService = new NotesService(faulted);
  check('transactions', 'failure after insert escapes transaction', () => assert.throws(() => faultService.create(who, 'fault', initial), /owned injected fault/));
  const audit = new DatabaseSync(path.join(directory, 'rollback.sqlite'));
  let afterFailure;
  try { afterFailure = { notes: audit.prepare('SELECT count(*) AS n FROM notes').get().n,
    operations: audit.prepare('SELECT count(*) AS n FROM operations').get().n }; }
  finally { audit.close(); }
  check('transactions', 'rollback removes inserted note', () => assert.equal(afterFailure.notes, 0));
  check('transactions', 'rollback leaves no saved operation', () => assert.equal(afterFailure.operations, 0));
  shouldFail = false;
  check('transactions', 'retry after rollback creates normally', () => assert.equal(faultService.create(who, 'fault', initial).replayed, false));
  observations.rollback = { afterFailure, retryCreated: true };

  const traces = new Map();
  const origin = await listen(createApp(reopenedService, (id, event) => {
    if (!traces.has(id)) traces.set(id, []);
    traces.get(id).push(event);
  }));
  httpPort = Number(new URL(origin).port);
  async function call(method, route, body, headers = {}, token = 'lesson-alice', raw = false) {
    const response = await fetch(origin + route, { method, headers: {
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...headers },
      body: body === undefined ? undefined : raw ? body : JSON.stringify(body), signal: AbortSignal.timeout(5000) });
    return { status: response.status, headers: Object.fromEntries(response.headers), body: await response.json() };
  }
  const created = await call('POST', '/notes', initial, { 'Idempotency-Key': 'http_create' });
  const id = created.body.id, route = '/notes/' + id;
  check('http', 'create status 201', () => assert.equal(created.status, 201));
  check('http', 'create body revision 1', () => assert.deepEqual(created.body, { id, ...initial, revision: 1 }));
  check('http', 'create resource location', () => assert.equal(created.headers.location, route));
  check('http', 'strong revision validator', () => assert.equal(created.headers.etag, '"1"'));
  check('http', 'private result not cached', () => assert.equal(created.headers['cache-control'], 'no-store'));
  check('http', 'trace correlation present', () => assert.match(created.headers['x-request-id'], /^[a-f0-9-]{36}$/));
  check('http', 'new create replay header false', () => assert.equal(created.headers['idempotency-replayed'], 'false'));
  observations.create = created;
  observations.createTrace = traces.get(created.headers['x-request-id']);
  check('http', 'trace crosses intended responsibilities in order', () => assert.deepEqual(observations.createTrace,
    ['http.received', 'identity.allowlist_verified', 'controller.create', 'service.create.validated',
     'repository.transaction.begin', 'repository.note.inserted', 'repository.operation.saved',
     'repository.transaction.commit', 'controller.response']));
  const get = await call('GET', route);
  check('http', 'get returns current representation', () => { assert.equal(get.status, 200); assert.deepEqual(get.body, created.body); });
  const replay = await call('POST', '/notes', initial, { 'Idempotency-Key': 'http_create' });
  check('http', 'retry returns same body and location', () => { assert.equal(replay.status, 201); assert.deepEqual(replay.body, created.body); assert.equal(replay.headers.location, route); });
  check('http', 'retry header indicates replay', () => assert.equal(replay.headers['idempotency-replayed'], 'true'));
  const conflict = await call('POST', '/notes', updated, { 'Idempotency-Key': 'http_create' });
  check('http', 'operation conflict maps to 409', () => { assert.equal(conflict.status, 409); assert.deepEqual(conflict.body, { error: 'operation_conflict' }); });
  const replaced = await call('PUT', route, updated, { 'If-Match': '"1"' });
  check('http', 'conditional replacement succeeds', () => { assert.equal(replaced.status, 200); assert.equal(replaced.body.revision, 2); assert.equal(replaced.headers.etag, '"2"'); });
  const stale = await call('PUT', route, initial, { 'If-Match': '"1"' });
  check('http', 'stale edit maps to 412', () => { assert.equal(stale.status, 412); assert.deepEqual(stale.body, { error: 'stale_revision' }); });
  const replayAfterEdit = await call('POST', '/notes', initial, { 'Idempotency-Key': 'http_create' });
  check('http', 'create retry after edit retains original response', () => assert.deepEqual(replayAfterEdit.body, created.body));
  const afterReplayGet = await call('GET', route);
  check('http', 'GET after replay still shows latest revision', () => { assert.equal(afterReplayGet.status, 200); assert.deepEqual(afterReplayGet.body, replaced.body); });
  for (const [label, token] of [['owner', 'lesson-bob'], ['tenant', 'lesson-other-tenant']]) {
    const hiddenRead = await call('GET', route, undefined, {}, token);
    const hiddenWrite = await call('PUT', route, initial, { 'If-Match': '"2"' }, token);
    check('http', label + ' cannot read note', () => { assert.equal(hiddenRead.status, 404); assert.deepEqual(hiddenRead.body, { error: 'not_found' }); });
    check('http', label + ' cannot edit note', () => assert.equal(hiddenWrite.status, 404));
    const ownCreate = await call('POST', '/notes', initial, { 'Idempotency-Key': 'http_create' }, token);
    check('http', label + ' has separate operation scope', () => { assert.equal(ownCreate.status, 201); assert.notEqual(ownCreate.body.id, id); });
  }
  const absent = await call('GET', '/notes/absent');
  check('http', 'absent representation matches invisible representation', () => assert.deepEqual(absent.body, { error: 'not_found' }));
  const unauth = await call('GET', route, undefined, {}, '');
  check('http', 'missing credential is 401 with challenge', () => { assert.equal(unauth.status, 401); assert.equal(unauth.headers['www-authenticate'], 'Bearer'); });
  const badToken = await call('GET', route, undefined, {}, 'forged');
  check('http', 'unknown allowlist token rejected', () => assert.equal(badToken.status, 401));
  const spoofed = await call('GET', route, undefined, { 'X-Tenant': 'alpha', 'X-Owner': 'alice' }, 'lesson-bob');
  check('http', 'identity headers cannot override principal', () => assert.equal(spoofed.status, 404));
  const malformed = await call('POST', '/notes', '{', { 'Idempotency-Key': 'bad_json' }, 'lesson-alice', true);
  check('http', 'invalid JSON maps to safe 400', () => { assert.equal(malformed.status, 400); assert.deepEqual(malformed.body, { error: 'invalid_json' }); });
  const oversize = await call('POST', '/notes', { ...initial, content: 'x'.repeat(9000) }, { 'Idempotency-Key': 'oversize' });
  check('http', 'parser rejects oversized transport body', () => assert.equal(oversize.status, 413));
  const contentType = await call('POST', '/notes', 'hello', { 'Content-Type': 'text/plain' });
  check('http', 'unsupported media type maps to 415', () => assert.equal(contentType.status, 415));
  const noKey = await call('POST', '/notes', initial);
  check('http', 'missing operation identity rejected', () => assert.equal(noKey.status, 400));
  const injected = await call('POST', '/notes', { ...initial, tenant: 'beta' }, { 'Idempotency-Key': 'inject' });
  check('http', 'unknown body fields rejected', () => assert.equal(injected.status, 400));
  const bytes = await call('POST', '/notes', { ...initial, content: '\u20ac'.repeat(1366) }, { 'Idempotency-Key': 'bytes' });
  check('http', 'domain byte limit enforced below parser limit', () => assert.equal(bytes.status, 400));
  const missingCondition = await call('PUT', route, initial);
  check('http', 'missing precondition maps to 428', () => assert.equal(missingCondition.status, 428));
  for (const condition of ['W/"2"', '*', '"2", "3"', '"9007199254740992"']) {
    const value = await call('PUT', route, initial, { 'If-Match': condition });
    check('http', 'unsupported or unsafe condition ' + condition, () => assert.equal(value.status, 400));
  }
  const parallel = await Promise.all([call('PUT', route, initial, { 'If-Match': '"2"' }), call('PUT', route, updated, { 'If-Match': '"2"' })]);
  check('http', 'two same-revision requests produce one winner', () => assert.deepEqual(parallel.map(item => item.status).sort(), [200, 412]));
  const latest = await call('GET', route);
  check('http', 'parallel edits advance revision once', () => assert.equal(latest.body.revision, 3));
  const unknown = await call('GET', '/unknown');
  check('http', 'unknown route maps to 404', () => assert.equal(unknown.status, 404));
  const badRepo = repo('http-fault.sqlite', () => { throw new Error('secret SQL details'); });
  const errorOrigin = await listen(createApp(new NotesService(badRepo)));
  const internal = await fetch(errorOrigin + '/notes', { method: 'POST', headers: { Authorization: 'Bearer lesson-alice', 'Content-Type': 'application/json', 'Idempotency-Key': 'fault' }, body: JSON.stringify(initial) });
  const errorBody = await internal.json();
  check('http', 'async route rejection reaches Express error middleware', () => assert.equal(internal.status, 500));
  check('http', 'internal error hides exception details', () => assert.deepEqual(errorBody, { error: 'internal_error' }));
  observations.contracts = { replay: { status: replay.status, replayed: replay.headers['idempotency-replayed'], sameId: replay.body.id === id },
    conflict: conflict.status, replacement: { status: replaced.status, revision: replaced.body.revision },
    stale: stale.status, replayAfterEdit: replayAfterEdit.body.revision,
    parallelRequestStatuses: parallel.map(item => item.status).sort(), finalRevision: latest.body.revision,
    missingCredential: unauth.status, crossOwner: spoofed.status, internalError: { status: internal.status, body: errorBody } };
} finally {
  for (const server of servers) { server.closeAllConnections(); await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve())); }
  for (const repository of repositories) repository.close();
  await rm(directory, { recursive: true, force: true }); // Exact directory returned by our mkdtemp.
}
let directoryRemoved = false;
try { await access(directory); } catch (error) { if (error.code === 'ENOENT') directoryRemoved = true; else throw error; }
const counts = {};
for (const item of checks) counts[item.group] = (counts[item.group] ?? 0) + 1;
const result = { label: 'A1', verified_date: new Date().toISOString().slice(0, 10), node: process.version,
  sqlite: process.versions.sqlite, typescript: ts.version,
  express: JSON.parse(await readFile(new URL('node_modules/express/package.json', import.meta.url))).version,
  os: platform() + ' ' + release(), total: checks.length, counts, checks, observations,
  cleanup: { temporaryDatabaseDirectoryRemoved: directoryRemoved, sqliteConnectionsClosed: true,
    temporaryListenersClosed: servers.every(server => !server.listening), fixturePort: httpPort },
  scope: 'Loopback Express HTTP, fixed public lesson-token allowlist, real file-backed synchronous SQLite, direct service calls and AST dependency checks. Parallel requests run in one Node process; no distributed concurrency, OAuth/TLS, durable events, proxies, production capacity or microservices deployment verified.' };
assert.ok(directoryRemoved);
await writeFile(new URL('verification-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ total: result.total, counts, observations, cleanup: result.cleanup }, null, 2));
