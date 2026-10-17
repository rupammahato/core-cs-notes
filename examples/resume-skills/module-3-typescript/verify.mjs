import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, existsSync, realpathSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve, dirname, basename, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const directory = dirname(fileURLToPath(import.meta.url));
const compiler = process.env.PLACEMENT_TSC_PATH ??
  resolve(directory, '../../../study-guide/node_modules/typescript/bin/tsc');
assert.ok(existsSync(compiler), 'Install the study-guide dependencies or set PLACEMENT_TSC_PATH to TypeScript bin/tsc.');
const compilerVersion = spawnSync(process.execPath, [compiler, '--version'], {
  encoding: 'utf8', windowsHide: true, timeout: 10000,
});
assert.ifError(compilerVersion.error);
assert.equal(compilerVersion.status, 0, compilerVersion.stderr);
const allCases = JSON.parse(readFileSync(join(directory, 'cases.json'), 'utf8'));
const requested = process.argv[2];
const selected = requested ? allCases.filter(item => item.id === requested) : allCases;
assert.ok(selected.length, 'Unknown case ID: ' + requested);
const compilerOptions = {
  target: 'ES2022', module: 'NodeNext', moduleResolution: 'NodeNext',
  lib: ['ES2022', 'DOM'], types: [], strict: true,
  noUncheckedIndexedAccess: true, exactOptionalPropertyTypes: true,
  noEmitOnError: true, outDir: './out',
};
const temporaryRoot = realpathSync(tmpdir());
const workspace = mkdtempSync(join(temporaryRoot, 'placement-m3-'));
const results = [];
try {
  for (const item of selected) {
    const caseDir = join(workspace, item.id);
    mkdirSync(caseDir);
    writeFileSync(join(caseDir, 'input.mts'), item.source + '\n');
    writeFileSync(join(caseDir, 'tsconfig.json'),
      JSON.stringify({ compilerOptions, files: ['./input.mts'] }, null, 2));
    const compiled = spawnSync(process.execPath, [compiler, '--project', join(caseDir, 'tsconfig.json'), '--pretty', 'false'], {
      cwd: caseDir, encoding: 'utf8', windowsHide: true, timeout: 10000,
    });
    assert.ifError(compiled.error);
    assert.equal(compiled.stderr, '', item.id + ': unexpected compiler stderr');
    const diagnosticCodes = [...new Set([...compiled.stdout.matchAll(/error TS(\d+):/g)].map(match => Number(match[1])))].sort((a, b) => a - b);
    const emittedPath = join(caseDir, 'out/input.mjs');
    const diagnostics = compiled.stdout.replaceAll(caseDir, '<case>').trimEnd();
    if (item.kind === 'reject') {
      assert.notEqual(compiled.status, 0, item.id + ': unexpectedly accepted');
      assert.deepEqual(diagnosticCodes, [...item.expectedCodes].sort((a, b) => a - b), item.id + ': diagnostic mismatch\n' + diagnostics);
      assert.equal(existsSync(emittedPath), false, item.id + ': emitted despite noEmitOnError');
      results.push({ ...item, diagnosticCodes, diagnostics, emitted: false });
      console.log('PASS ' + item.id + ' - rejected: ' + diagnosticCodes.map(code => 'TS' + code).join(','));
      if (requested) console.log(diagnostics);
    } else {
      assert.equal(compiled.status, 0, item.id + ': ' + diagnostics);
      assert.equal(diagnosticCodes.length, 0);
      const emittedJavaScript = readFileSync(emittedPath, 'utf8');
      const executed = spawnSync(process.execPath, [emittedPath], {
        encoding: 'utf8', windowsHide: true, timeout: 5000,
      });
      assert.ifError(executed.error);
      assert.equal(executed.status, 0, item.id + ': ' + executed.stderr);
      assert.equal(executed.stderr, '', item.id + ': unexpected runtime stderr');
      const output = executed.stdout.trimEnd();
      assert.equal(output, item.expectedOutput.join('\n'), item.id + ': output mismatch');
      results.push({ ...item, diagnosticCodes, output, emittedJavaScript });
      console.log('PASS ' + item.id + ' - compiled and ran');
      if (requested) console.log(output);
    }
  }
  const version = compilerVersion.stdout.trim();
  console.log('Verified ' + selected.length + ' TypeScript cases; ' + version + '; Node ' + process.version);
  if (!requested) writeFileSync(join(directory, 'results.json'),
    JSON.stringify({ compilerVersion: version, node: process.version, compilerOptions, cases: results }, null, 2) + '\n');
} finally {
  // Only remove the exact temporary directory this invocation created.
  const resolvedWorkspace = realpathSync(workspace);
  assert.equal(dirname(resolvedWorkspace), temporaryRoot);
  assert.ok(basename(resolvedWorkspace).startsWith('placement-m3-'));
  rmSync(resolvedWorkspace, { recursive: true, force: true });
}
