import { once } from 'node:events';
import { writeSync } from 'node:fs';
import { openStore } from './store.mjs';

const [filename, mode] = process.argv.slice(2);
const store = openStore(filename, { onPhase: phase => {
  if (phase === mode) { writeSync(1, 'PHASE ' + phase + '\n'); process.exit(77); }
} });
if (mode === 'compete') {
  const go = once(process.stdin, 'data');
  writeSync(1, 'READY\n');
  await go;
}
const result = store.processOne('alpha', 'durable-event');
store.close();
writeSync(1, JSON.stringify(result) + '\n');
