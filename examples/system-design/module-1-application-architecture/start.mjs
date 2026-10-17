import { compose } from './dist/composition.js';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const directory = await mkdtemp(path.join(tmpdir(), 'placement-a1-manual-'));
const system = compose(path.join(directory, 'notes.sqlite'));
const server = system.app.listen(0, '127.0.0.1');
await once(server, 'listening');
console.log('Lesson API: http://127.0.0.1:' + server.address().port + '/notes');
console.log('Published loopback credential: Authorization: Bearer lesson-alice');
console.log('Temporary database is removed on Ctrl+C. Port 3000 is not used.');
let stopping = false;
async function stop() {
  if (stopping) return;
  stopping = true;
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
  system.close();
  await rm(directory, { recursive: true, force: true });
}
process.once('SIGINT', stop);
process.once('SIGTERM', stop);
