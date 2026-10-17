import { mkdtemp, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFile, spawn } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { once } from 'node:events';
import { openStore } from './store.mjs';
import { receive, sign } from './webhook.mjs';
import { endpoints, orders, fixtureEvent } from './fixtures.mjs';
import { assert, check, save } from './checks.mjs';

const exec = promisify(execFile);
const base = await realpath(tmpdir());
const directory = await mkdtemp(path.join(base, 'placement-m9-'));
const createdPath = await realpath(directory);
const worker = fileURLToPath(new URL('./recovery-worker.mjs', import.meta.url));
const prepare = filename => {
  const store = openStore(filename); store.seed(orders);
  const raw = Buffer.from(JSON.stringify(fixtureEvent()));
  receive({ endpointId: 'alpha', endpoints, store, raw, signature: sign(raw, endpoints.alpha.secrets[0]), eventId: 'durable-event' });
  store.close();
};
const warningOnly = stderr => /^\(node:\d+\) ExperimentalWarning: SQLite is an experimental feature and might change at any time\r?\n\(Use `node --trace-warnings \.\.\.` to show where the warning was created\)\r?\n?$/.test(stderr);
async function crashed(filename, mode) {
  let result;
  try {
    result = await exec(process.execPath, [worker, filename, mode], { windowsHide: true, timeout: 10000 });
    assert.fail('Expected worker exit 77');
  } catch (error) {
    assert.equal(error.code, 77);
    assert.ok(error.stdout.includes('PHASE ' + mode));
    assert.ok(warningOnly(error.stderr));
    await writeFile(new URL('./' + mode + '-worker-stderr.txt', import.meta.url), error.stderr);
  }
}
function startCompetitor(filename) {
  const child = spawn(process.execPath, [worker, filename, 'compete'], {
    windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'],
  });
  let output = '', stderr = '', readyResolve, readyReject;
  const ready = new Promise((resolve, reject) => { readyResolve = resolve; readyReject = reject; });
  child.stdout.on('data', chunk => { output += chunk; if (output.includes('READY')) readyResolve(); });
  child.stderr.on('data', chunk => { stderr += chunk; });
  child.on('error', readyReject);
  const done = new Promise((resolve, reject) => child.once('exit', code => {
    if (code !== 0) { readyReject(new Error('Worker exited ' + code)); reject(new Error(stderr)); }
    else resolve({ output, stderr });
  }));
  // Attach a handler immediately, including while waiting for readiness.
  done.catch(() => {});
  return { child, ready, done };
}
let sqlite;
try {
  await check('inbox persists across close and reopen before any worker', async () => {
    const filename = path.join(directory, 'acceptance.sqlite'); prepare(filename);
    const store = openStore(filename);
    try {
      sqlite = store.sqlite();
      assert.deepEqual(store.configuration(), { journal: 'delete', synchronous: 2, foreignKeys: 1 });
      assert.equal(store.snapshot().inbox[0].state, 'pending');
      assert.equal(store.snapshot().ledger.length, 0);
      store.processNext(); assert.equal(store.snapshot().balances[0].credits, 100);
      return { pendingSurvived: true, afterWorkerCredits: 100 };
    } finally { store.close(); }
  });
  await check('process exit before effect commit recovers pending receipt with zero partial credit', async () => {
    const filename = path.join(directory, 'before.sqlite'); prepare(filename);
    await crashed(filename, 'after-ledger-write');
    const store = openStore(filename);
    try {
      const state = store.snapshot();
      assert.equal(state.ledger.length, 0); assert.equal(state.payments.length, 0);
      assert.equal(state.outbox.length, 0); assert.equal(state.inbox[0].state, 'pending');
      assert.equal(state.orders[0].state, 'pending');
      store.processNext(); assert.equal(store.snapshot().ledger.length, 1);
      assert.equal(store.snapshot().balances[0].credits, 100);
      return { workerExit: 77, beforeRetryLedgerRows: 0, receipt: 'pending', afterRetryCredits: 100 };
    } finally { store.close(); }
  });
  await check('process exit after commit preserves one grant and one outbox row', async () => {
    const filename = path.join(directory, 'after.sqlite'); prepare(filename);
    await crashed(filename, 'after-effect-commit');
    const store = openStore(filename);
    try {
      const state = store.snapshot();
      assert.equal(state.ledger.length, 1); assert.equal(state.outbox.length, 1);
      assert.equal(state.inbox[0].state, 'processed');
      store.processOne('alpha', 'durable-event');
      assert.equal(store.snapshot().balances[0].credits, 100);
      assert.equal(store.snapshot().ledger.length, 1);
      return { workerExit: 77, receipt: 'processed', ledgerRows: 1, outboxRows: 1, afterRetryCredits: 100 };
    } finally { store.close(); }
  });
  await check('two ready independent worker processes commit a single grant', async () => {
    const filename = path.join(directory, 'compete.sqlite'); prepare(filename);
    const workers = [startCompetitor(filename), startCompetitor(filename)];
    let deadline;
    try {
      await Promise.race([Promise.all(workers.map(w => w.ready)), new Promise((_, reject) => {
        deadline = setTimeout(() => reject(new Error('Worker readiness deadline')), 10000);
      })]); clearTimeout(deadline);
      for (const w of workers) w.child.stdin.end('GO\n');
      const finished = await Promise.race([Promise.all(workers.map(w => w.done)), new Promise((_, reject) => {
        deadline = setTimeout(() => reject(new Error('Worker completion deadline')), 10000);
      })]); clearTimeout(deadline);
      const outcomes = finished.map((result, index) => {
        assert.ok(warningOnly(result.stderr));
        const line = result.output.split('\n').find(line => line.startsWith('{'));
        return JSON.parse(line);
      });
      assert.equal(outcomes.filter(result => result.reason === 'granted').length, 1);
      const store = openStore(filename);
      try {
        assert.equal(store.snapshot().ledger.length, 1); assert.equal(store.snapshot().outbox.length, 1);
        assert.equal(store.snapshot().balances[0].credits, 100);
        return { workerProcesses: 2, grants: 1, ledgerRows: 1, outboxRows: 1, credits: 100 };
      } finally { store.close(); }
    } finally {
      clearTimeout(deadline);
      for (const w of workers) if (w.child.exitCode === null && w.child.signalCode === null) {
        const exited = once(w.child, 'exit'); w.child.kill(); await exited;
      }
    }
  });
} finally {
  const resolved = await realpath(directory);
  const relative = path.relative(base, resolved);
  if (resolved !== createdPath || !relative.startsWith('placement-m9-') || path.isAbsolute(relative) ||
      relative.includes(path.sep) || relative.startsWith('..')) throw new Error('Unsafe temporary cleanup target');
  await rm(resolved, { recursive: true, force: false });
}
await save('recovery', { sqlite, temporaryDirectoryRemoved: true });
