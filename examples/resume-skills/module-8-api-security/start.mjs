import { createFixtureAuth } from './fixture-auth.mjs';
import { createRepository } from './repository.mjs';
import { createDocumentService } from './service.mjs';
import { createSecurityServer } from './server.mjs';

const auth = await createFixtureAuth();
const service = createDocumentService({ repository: createRepository() });
const server = createSecurityServer({
  authenticate: auth.authenticate, service, allowedOrigins: ['http://127.0.0.1:3108'],
});
server.listen(3108, '127.0.0.1', () => {
  console.log('Security learning API: http://127.0.0.1:3108');
  // Explicitly public, generated learning credentials; never use real identities here.
  console.log('Alice fixture bearer (expires after 300 seconds): ' + auth.tokens.alice);
  console.log('Dana fixture bearer (expires after 300 seconds): ' + auth.tokens.dana);
});
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => {
  server.close(() => process.exit());
  server.closeIdleConnections();
  setTimeout(() => { server.closeAllConnections(); process.exit(1); }, 3000).unref();
});
