import { createTelemetry } from './telemetry.mjs';
import { createApplication } from './app.mjs';
const telemetry = createTelemetry();
const app = await createApplication(telemetry, { release: process.env.RELEASE ?? 'fixture', unhealthy: process.env.FIXTURE_UNHEALTHY === '1' });
console.log(JSON.stringify({ event: 'ready', port: app.port, dependency_port: app.dependencyPort }));
let stopping = false;
async function stop() { if (stopping) return; stopping = true; await app.close(); await telemetry.close(); }
process.on('SIGTERM', stop);
process.on('SIGINT', stop);
// Host verifier can request cooperative shutdown on Windows through owned stdin.
process.stdin.resume(); process.stdin.on('data', data => { if (data.toString().trim() === 'stop') stop().then(() => process.stdin.pause()); });
