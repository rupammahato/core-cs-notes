'use strict';
const http = require('node:http');
const { randomUUID } = require('node:crypto');
const port = Number(process.env.PORT || 9000);
const release = process.env.RELEASE || 'v1';
let draining = false, counter = 0;
const log = (event, fields = {}) => console.log(JSON.stringify({ event, pid: process.pid, ...fields }));
const server = http.createServer(async (req, res) => {
  const id = req.headers['x-request-id'] || randomUUID();
  const url = new URL(req.url, 'http://fixture.invalid');
  const reply = (status, body) => {
    if (res.destroyed) return;
    res.writeHead(status, { 'content-type': 'application/json', 'x-request-id': id });
    res.end(JSON.stringify(body));
  };
  log('request_start', { id, path: url.pathname });
  res.on('finish', () => log('request_finish', { id, status: res.statusCode }));
  if (url.pathname === '/live') return reply(200, { live: true });
  if (url.pathname === '/ready') return reply(draining ? 503 : 200, { ready: !draining });
  if (draining) return reply(503, { error: 'draining' });
  if (req.method === 'GET' && url.pathname === '/slow') {
    const ms = Number(url.searchParams.get('ms') || 600);
    if (!Number.isInteger(ms) || ms < 0 || ms > 2000) return reply(400, { error: 'bad delay' });
    await new Promise(resolve => setTimeout(resolve, ms));
    return reply(200, { pid: process.pid, release, delayed_ms: ms });
  }
  if (req.method === 'GET' && url.pathname === '/counter') {
    return reply(200, { pid: process.pid, counter: ++counter });
  }
  if (req.method === 'POST' && url.pathname === '/echo') {
    let bytes = 0, chunks = [];
    for await (const chunk of req) {
      bytes += chunk.length;
      if (bytes > 2048) { reply(413, { error: 'body too large' }); req.resume(); return; }
      chunks.push(chunk);
    }
    return reply(200, { bytes, body: Buffer.concat(chunks).toString('utf8') });
  }
  if (req.method === 'GET' && ['/echo', '/keep/echo'].includes(url.pathname)) {
    return reply(200, {
      pid: process.pid, uid: process.getuid(), cwd: process.cwd(), release,
      url: req.url, remote: req.socket.remoteAddress,
      headers: { host: req.headers.host, forwarded_for: req.headers['x-forwarded-for'],
        forwarded_proto: req.headers['x-forwarded-proto'], request_id: id },
    });
  }
  reply(404, { error: 'route not found' });
});
server.requestTimeout = 5000;
server.headersTimeout = 3000;
server.keepAliveTimeout = 1000;
server.timeout = 6000;
server.on('clientError', (_error, socket) => socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n'));
function shutdown(signal) {
  if (draining) return;
  draining = true;
  log('shutdown_start', { signal });
  const deadline = setTimeout(() => {
    log('shutdown_forced'); server.closeAllConnections(); process.exit(1);
  }, 4000);
  deadline.unref();
  server.close(() => {
    clearTimeout(deadline); log('shutdown_complete'); process.exit(0);
  });
  server.closeIdleConnections();
}
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
server.listen(port, '127.0.0.1', () => {
  log('listening', { port, release, uid: process.getuid() });
  if (process.send) process.send('ready');
});
