import { createTaskServer } from './server.mjs';

const server = createTaskServer();
server.listen(3106, '127.0.0.1', () => console.log('Task API: http://127.0.0.1:3106/v1/tasks'));
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.once(signal, () => {
    server.close(() => process.exit());
    server.closeIdleConnections();
    setTimeout(() => { server.closeAllConnections(); process.exit(1); }, 3000).unref();
  });
}
