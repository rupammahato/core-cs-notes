import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

function run(script, args = []) {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL(script, import.meta.url)), ...args], {
    encoding: 'utf8', windowsHide: true, timeout: 60000,
  });
  assert.ifError(result.error);
  process.stdout.write(result.stdout);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stderr, '');
}
run('./verify-runtime.mjs', process.argv[2] ? [process.argv[2]] : []);
if (!process.argv[2]) run('./verify-types.mjs');
