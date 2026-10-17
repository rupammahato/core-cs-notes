import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const exec = promisify(execFile), cwd = fileURLToPath(new URL('.', import.meta.url));
let total = 0;
const groups = [];
for (const group of ['policy', 'http', 'sql']) {
  const { stdout, stderr } = await exec(process.execPath, ['verify-' + group + '.mjs'], {
    cwd, windowsHide: true, timeout: 90000, maxBuffer: 1_000_000,
  });
  if (stderr) {
    const lines = stderr.split(/\r?\n/).filter(Boolean);
    const expectedSqlWarning = group === 'sql' && lines.length === 2 &&
      /^\(node:\d+\) ExperimentalWarning: SQLite is an experimental feature and might change at any time$/.test(lines[0]) &&
      lines[1] === '(Use `node --trace-warnings ...` to show where the warning was created)';
    if (!expectedSqlWarning) throw new Error(stderr);
    await writeFile(new URL('./sql-verification-stderr.txt', import.meta.url), stderr);
    console.log('Recorded expected experimental node:sqlite warning.');
  }
  await writeFile(new URL('./' + group + '-verification-output.txt', import.meta.url), stdout);
  process.stdout.write(stdout);
  const result = JSON.parse(await readFile(new URL('./' + group + '-results.json', import.meta.url), 'utf8'));
  total += result.passed;
  groups.push({ group, passed: result.passed, ...(result.sqlite ? { sqlite: result.sqlite } : {}) });
}
await writeFile(new URL('./results.json', import.meta.url), JSON.stringify({
  node: process.version, jose: '6.2.12', passed: total, groups,
}, null, 2) + '\n');
console.log('Verified ' + total + ' checks across policy, real HTTP and SQLite groups.');
