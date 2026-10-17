import { readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const allCases = JSON.parse(readFileSync(new URL('./cases.json', import.meta.url), 'utf8'));
const requested = process.argv[2];
const selected = requested ? allCases.filter(item => item.id === requested) : allCases;
assert.ok(selected.length, 'Unknown case ID: ' + requested);
const results = [];
for (const item of selected) {
  const result = spawnSync(process.execPath, ['--input-type=' + (item.mode ?? 'module'), '--eval', item.source], {
    encoding: 'utf8', timeout: 10000, windowsHide: true,
    cwd: fileURLToPath(new URL('./', import.meta.url)),
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, item.id + ': ' + result.stderr);
  assert.equal(result.stderr, '', item.id + ': unexpected stderr');
  const output = result.stdout.trimEnd();
  assert.equal(output, item.expected.join('\n'), item.id + ': output mismatch');
  results.push({ id: item.id, title: item.title, mode: item.mode, source: item.source, output });
  console.log('PASS ' + item.id + ' - ' + item.title);
  if (requested) console.log(output);
}
console.log('Verified ' + selected.length + ' snippets in their recorded module modes; Node ' + process.version);
if (!requested) {
  writeFileSync(fileURLToPath(new URL('./results.json', import.meta.url)),
    JSON.stringify({ node: process.version, mode: 'Per-case: module or commonjs', cases: results }, null, 2) + '\n');
}
