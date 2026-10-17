import { hashPassword } from './password.mjs';
import { createIdentity } from './identity.mjs';
import { createAuthServer } from './server.mjs';

// Public fixture credentials, solely for this loopback learning service.
const identity = await createIdentity({ passwordRecord: await hashPassword('placement-demo-password') });
const server = createAuthServer({
  identity, trustedOrigin: 'http://127.0.0.1:3107', secureCookies: false,
});
server.listen(3107, '127.0.0.1', () => console.log('Auth learning API: http://127.0.0.1:3107'));
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => {
  server.close(() => process.exit());
  server.closeIdleConnections();
  setTimeout(() => { server.closeAllConnections(); process.exit(1); }, 3000).unref();
});
