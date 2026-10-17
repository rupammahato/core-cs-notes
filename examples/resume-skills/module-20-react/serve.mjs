import { createFixtureServer } from './server.mjs';
const fixture = await createFixtureServer();
console.log('React teaching lab: http://127.0.0.1:' + fixture.port);
console.log('Use ?strict=1 or ?strict=1&production=1 for the lifecycle comparison. Ctrl+C stops it.');
let stopping = false;
async function stop() { if (stopping) return; stopping = true; await fixture.close(); }
process.on('SIGINT', stop); process.on('SIGTERM', stop);
