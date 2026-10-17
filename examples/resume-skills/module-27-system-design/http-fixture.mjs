import http from 'node:http';
import net from 'node:net';

export const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
export async function listen(server) {
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  return server.address().port;
}
export async function close(server) {
  server.closeAllConnections();
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
}
export async function portClosed(port) {
  return new Promise(resolve => {
    const socket = net.connect({ host: '127.0.0.1', port });
    socket.once('connect', () => { socket.destroy(); resolve(false); });
    socket.once('error', () => resolve(true));
  });
}
export async function backend(id) {
  const state = { ready: true, calls: 0, mutations: 0, holds: [], timers: new Set(), arrived: deferred() };
  const server = http.createServer((req, res) => {
    if (req.url === '/ready') { res.writeHead(state.ready ? 200 : 503); res.end(); return; }
    state.calls++;
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.once('end', () => {
      const respond = () => {
        if (res.destroyed) return;
        res.writeHead(req.url === '/fail' ? 503 : 200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ id, tenant: req.headers['x-fixture-tenant'], body: Buffer.concat(chunks).toString(), credentialForwarded: !!req.headers.authorization, spoofForwarded: !!req.headers['x-tenant'], connectionSecretForwarded: !!req.headers['x-secret'], contentType: req.headers['content-type'] ?? null }));
      };
      if (req.url === '/mutate') { state.mutations++; req.socket.destroy(); return; }
      if (req.url === '/hold') { const gate = deferred(); state.holds.push(gate); state.arrived.resolve(); gate.promise.then(respond); return; }
      if (req.url === '/slow') { const timer = setTimeout(() => { state.timers.delete(timer); respond(); }, 400); state.timers.add(timer); return; }
      respond();
    });
  });
  const port = await listen(server);
  return { id, origin: `http://127.0.0.1:${port}`, port, server, state, dispose: () => { for (const timer of state.timers) clearTimeout(timer); for (const gate of state.holds) gate.resolve(); } };
}
export function request(port, path = '/work', { method = 'GET', body = '', headers = {}, signal } = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path, method, agent: false, signal, headers: { authorization: 'Bearer public-alpha-demo', 'content-length': Buffer.byteLength(body), ...headers } }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.once('end', () => { const text = Buffer.concat(chunks).toString(); resolve({ status: res.statusCode, headers: res.headers, body: text ? JSON.parse(text) : null }); });
      res.once('error', reject);
    });
    req.once('error', reject);
    req.end(body);
  });
}
