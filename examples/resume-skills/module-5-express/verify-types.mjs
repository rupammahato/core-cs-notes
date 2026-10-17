import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { requestApp } from './http-helper.mjs';

const directory = dirname(fileURLToPath(import.meta.url));
const compiler = process.env.PLACEMENT_TSC_PATH ??
  resolve(directory, '../../../study-guide/node_modules/typescript/bin/tsc');
function compile(project) {
  const result = spawnSync(process.execPath, [compiler, '--project', project, '--pretty', 'false'], {
    cwd: directory, encoding: 'utf8', windowsHide: true, timeout: 10000,
  });
  assert.ifError(result.error);
  assert.equal(result.stderr, '');
  return result;
}
const accepted = compile('tsconfig.json');
assert.equal(accepted.status, 0, accepted.stdout);
console.log('PASS typed boundary compiles');
const rejected = compile('tsconfig.reject.json');
assert.notEqual(rejected.status, 0);
const codes = [...new Set([...rejected.stdout.matchAll(/error TS(\d+):/g)].map(match => Number(match[1])))];
assert.deepEqual(codes, [18046]);
console.log('PASS unknown request body rejected TS18046');
const { createTypedApp, respond } = await import('./dist/typed-boundary.js');
const options = body => ({ method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
const valid = await requestApp(app => app.use(createTypedApp()), '/typed', options({ productId: 7, quantity: 2 }));
assert.equal(valid.status, 200);
assert.deepEqual(valid.body, { input: { productId: 7, quantity: 2 } });
console.log('PASS typed runtime accepts validated input');
const invalid = await requestApp(app => app.use(createTypedApp()), '/typed', options({ productId: 7, quantity: '2' }));
assert.equal(invalid.status, 400);
assert.deepEqual(invalid.body, { error: 'invalid_values' });
console.log('PASS typed runtime rejects wrong value type');
const bypass = await requestApp(app => app.post('/typed', respond), '/typed', { method: 'POST' });
assert.equal(bypass.status, 500);
assert.deepEqual(bypass.body, { error: 'validation_missing' });
console.log('PASS missing middleware detected at runtime');
const version = spawnSync(process.execPath, [compiler, '--version'], { encoding: 'utf8', windowsHide: true });
assert.equal(version.status, 0);
writeFileSync(resolve(directory, 'type-results.json'), JSON.stringify({
  compilerVersion: version.stdout.trim(), node: process.version,
  diagnosticCodes: codes, diagnostics: rejected.stdout.trimEnd(),
  acceptedSource: readFileSync(resolve(directory, 'typed/typed-boundary.ts'), 'utf8'),
  rejectedSource: readFileSync(resolve(directory, 'typed/unsafe.ts'), 'utf8'),
  emittedJavaScript: readFileSync(resolve(directory, 'dist/typed-boundary.js'), 'utf8'),
  runtime: { valid: { status: valid.status, body: valid.body }, invalid: { status: invalid.status, body: invalid.body },
    missingMiddleware: { status: bypass.status, body: bypass.body } },
}, null, 2) + '\n');
console.log('Verified 5 TypeScript boundary checks; ' + version.stdout.trim());
