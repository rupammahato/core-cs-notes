import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
export { assert };
export const results = [];
export async function check(name, fn) {
  const observed = await fn();
  results.push({ name, passed: true, observed });
  console.log('PASS ' + name + (observed === undefined ? '' : ': ' + JSON.stringify(observed)));
}
export async function denied(fn, status, code) {
  await assert.rejects(fn, error => error.status === status && error.code === code);
  return { status, code };
}
export async function save(group, extra = {}) {
  await writeFile(new URL('./' + group + '-results.json', import.meta.url), JSON.stringify({
    node: process.version, passed: results.length, ...extra, checks: results,
  }, null, 2) + '\n');
  console.log('Verified ' + results.length + ' ' + group + ' checks.');
}
