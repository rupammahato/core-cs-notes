import { createServer } from 'node:http';

export async function startOrigin() {
  const state = { version: 1, counts: {}, held: new Set(), failing: true };
  const server = createServer((request, response) => {
    const url = new URL(request.url, 'http://fixture');
    const key = url.pathname + url.search;
    state.counts[key] = (state.counts[key] || 0) + 1;
    if (url.pathname === '/held') {
      state.held.add(response);
      response.on('close', () => state.held.delete(response));
      return;
    }
    if (url.pathname === '/unstable' && state.failing) {
      response.writeHead(503); response.end('Temporary fixture failure'); return;
    }
    if (!['/items', '/isr', '/unstable'].includes(url.pathname)) {
      response.writeHead(404); response.end(); return;
    }
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify({ version: state.version }));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  function release() {
    for (const response of state.held) {
      response.writeHead(200, { 'Content-Type': 'application/json' }); response.end('{"ready":true}');
    }
    state.held.clear();
  }
  return { state, port, url: `http://127.0.0.1:${port}`, release,
    async close() { release(); await new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }); },
  };
}
