import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const exec = promisify(execFile);
const cwd = fileURLToPath(new URL('.', import.meta.url));
let total = 0;
const groups = [];
for (const group of ['crypto', 'http', 'oauth']) {
  const { stdout, stderr } = await exec(process.execPath, ['verify-' + group + '.mjs'], {
    cwd, windowsHide: true, timeout: 60000, maxBuffer: 1_000_000,
  });
  if (stderr) throw new Error(stderr);
  await writeFile(new URL('./' + group + '-verification-output.txt', import.meta.url), stdout);
  process.stdout.write(stdout);
  const data = JSON.parse(await readFile(new URL('./' + group + '-results.json', import.meta.url), 'utf8'));
  total += data.passed; groups.push({ group, passed: data.passed });
}
await writeFile(new URL('./results.json', import.meta.url), JSON.stringify({
  node: process.version, jose: '6.2.12', passed: total, groups,
}, null, 2) + '\n');
console.log('Verified ' + total + ' checks across password/session/JWT/JWE, HTTP and OAuth model groups.');
