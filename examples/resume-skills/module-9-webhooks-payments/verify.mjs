import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const exec = promisify(execFile), cwd = fileURLToPath(new URL('.', import.meta.url));
let passed = 0, sqlite;
const groups = [];
for (const group of ['core', 'http', 'reconciliation', 'recovery']) {
  const { stdout, stderr } = await exec(process.execPath, ['verify-' + group + '.mjs'], {
    cwd, windowsHide: true, timeout: 60000, maxBuffer: 1_000_000,
  });
  if (stderr && !/^\(node:\d+\) ExperimentalWarning: SQLite is an experimental feature and might change at any time\r?\n\(Use `node --trace-warnings \.\.\.` to show where the warning was created\)\r?\n?$/.test(stderr))
    throw new Error(stderr);
  await writeFile(new URL('./' + group + '-verification-output.txt', import.meta.url), stdout);
  await writeFile(new URL('./' + group + '-verification-stderr.txt', import.meta.url), stderr);
  process.stdout.write(stdout);
  const result = JSON.parse(await readFile(new URL('./' + group + '-results.json', import.meta.url), 'utf8'));
  passed += result.passed; groups.push({ group, passed: result.passed });
  if (result.sqlite) { if (sqlite && sqlite !== result.sqlite) throw new Error('SQLite version mismatch'); sqlite = result.sqlite; }
}
await writeFile(new URL('./results.json', import.meta.url), JSON.stringify({
  node: process.version, sqlite, passed, groups,
}, null, 2) + '\n');
console.log('Verified ' + passed + ' checks across core, real HTTP, reconciliation fixtures and file/process recovery.');
console.log('Expected experimental node:sqlite warnings preserved separately.');
