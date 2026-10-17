import http from 'node:http';
import { once } from 'node:events';
import { readFile } from 'node:fs/promises';

export async function createFixtureServer() {
  const held = new Set(), requests = [], events = [];
  let errorEnabled = true;
  function json(res, status, body) {
    if (res.destroyed) return;
    res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' });
    res.end(JSON.stringify(body));
  }
  function releaseSlow() {
    for (const res of held) json(res, 200, { items: [{ id: 'slow', title: 'Slow result' }] });
    held.clear();
  }
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://fixture.invalid');
    if (req.method === 'POST' && url.pathname === '/fixture/release-slow') { releaseSlow(); return json(res, 200, { released: true }); }
    if (req.method === 'POST' && url.pathname === '/fixture/recover') { errorEnabled = false; return json(res, 200, { recovered: true }); }
    if (req.method !== 'GET') return json(res, 405, { error: 'method not allowed' });
    if (url.pathname === '/api/topics') {
      const query = url.searchParams.get('q') ?? '';
      requests.push({ query });
      res.on('close', () => { if (!res.writableEnded) { events.push({ event: 'client-disconnected', query }); held.delete(res); } });
      if (query === 'slow') { held.add(res); events.push({ event: 'slow-held' }); return; }
      if (query === 'error' && errorEnabled) return json(res, 503, { error: 'injected service failure' });
      if (query === 'malformed') return json(res, 200, { items: 'wrong-shape' });
      if (query === 'empty') return json(res, 200, { items: [] });
      if (query === 'html') return json(res, 200, { items: [{ id: 'html', title: '<img src=x onerror=alert(1)>' }] });
      const title = query === 'fast' ? 'Fast result' : query === 'error' ? 'Recovered result' : 'Node.js';
      return json(res, 200, { items: [{ id: query || 'node', title }] });
    }
    if (url.pathname === '/favicon.ico') { res.writeHead(204); res.end(); return; }
    try {
      if (url.pathname === '/') {
        const mode = url.searchParams.get('production') === '1' ? 'production' : 'development';
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
        res.end('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>M20 React lab</title><link rel="stylesheet" href="/styles.css"></head><body><div id="root"></div><script src="/app.' + mode + '.js" defer></script></body></html>');
        return;
      }
      const paths = { '/app.development.js': ['dist/app.development.js', 'text/javascript'], '/app.production.js': ['dist/app.production.js', 'text/javascript'], '/styles.css': ['styles.css', 'text/css'] };
      if (!(url.pathname in paths)) return json(res, 404, { error: 'not found' });
      const [file, type] = paths[url.pathname];
      const body = await readFile(new URL('./' + file, import.meta.url));
      res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' }); res.end(body);
    } catch { json(res, 500, { error: 'build the fixture first' }); }
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  return { port: server.address().port, requests, events, heldCount: () => held.size, releaseSlow,
    recover: () => { errorEnabled = false; },
    close: async () => { releaseSlow(); await new Promise((resolve, reject) => {
      server.close(error => error ? reject(error) : resolve()); server.closeAllConnections();
    }); },
  };
}
