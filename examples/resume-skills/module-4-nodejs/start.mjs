import { createStudyServer } from './server.mjs';

const app = createStudyServer();
const port = 3104;
app.server.listen(port, '127.0.0.1', () => {
  console.log('Node learning server: http://127.0.0.1:' + port);
});
app.server.on('error', error => {
  console.error(error.code ?? error.name);
  process.exitCode = 1;
});
let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  app.beginDrain();
  const deadline = setTimeout(() => {
    app.server.closeAllConnections();
    process.exitCode = 1;
  }, 5000);
  deadline.unref();
  app.server.close(error => {
    clearTimeout(deadline);
    if (error) process.exitCode = 1;
  });
}
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
