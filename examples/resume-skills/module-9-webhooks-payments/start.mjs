import { fileURLToPath } from 'node:url';
import { openStore } from './store.mjs';
import { createWebhookServer } from './server.mjs';
import { endpoints, orders } from './fixtures.mjs';

const store = openStore(fileURLToPath(new URL('./demo.sqlite', import.meta.url)));
store.seed(orders);
const server = createWebhookServer({ endpoints, store });
const timer = setInterval(() => {
  try {
    const result = store.processNext();
    if (result.outcome !== 'idle') console.log('Worker:', result);
  } catch (error) { console.error('Worker requires retry/review:', error.message); }
}, 250);
server.listen(3109, '127.0.0.1', () => console.log('Webhook fixture: http://127.0.0.1:3109/webhooks/alpha'));
server.on('error', error => { clearInterval(timer); store.close(); console.error(error.message); process.exitCode = 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => {
  clearInterval(timer);
  server.close(() => { store.close(); process.exit(); });
  server.closeIdleConnections();
  setTimeout(() => { server.closeAllConnections(); process.exit(1); }, 3000).unref();
});
