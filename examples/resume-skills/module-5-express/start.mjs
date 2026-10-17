import { createServer } from 'node:http';
import { createApp } from './app.mjs';

const server = createServer(createApp());
server.listen(3105, '127.0.0.1', () => {
  console.log('Express learning API: http://127.0.0.1:3105');
});
server.on('error', error => {
  console.error(error.code ?? error.name);
  process.exitCode = 1;
});
let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  const deadline = setTimeout(() => {
    server.closeAllConnections();
    process.exitCode = 1;
  }, 5000);
  deadline.unref();
  server.close(error => {
    clearTimeout(deadline);
    if (error) process.exitCode = 1;
  });
}
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
