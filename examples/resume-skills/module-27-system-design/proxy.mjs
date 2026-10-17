import http from 'node:http';
import { Pool } from './pool.mjs';
import { routeKey } from './ring.mjs';

const identities = new Map([['Bearer public-alpha-demo', 'alpha'], ['Bearer public-beta-demo', 'beta']]);
const paths = new Set(['/work', '/slow', '/fail', '/mutate', '/hold']);

function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let bytes = 0;
    req.on('data', chunk => { bytes += chunk.length; if (bytes <= limit) chunks.push(chunk); });
    req.once('end', () => bytes > limit ? reject(Object.assign(new Error('Body limit'), { status: 413 })) : resolve(Buffer.concat(chunks)));
    req.once('aborted', () => reject(new Error('Client aborted')));
    req.once('error', reject);
  });
}

export function createProxy(backends, { strategy = 'hash', maxInFlight = 4, deadlineMs = 150, maxBody = 1024, maxResponse = 4096 } = {}) {
  const pool = new Pool(backends, { strategy });
  const agent = new http.Agent({ keepAlive: true, maxSockets: maxInFlight });
  const metrics = { active: 0, admitted: 0, rejected: 0, attempts: 0, timeouts: 0, cancelled: 0 };
  const server = http.createServer(async (req, res) => {
    let upstream;
    let timer;
    let node;
    let released = false;
    const send = (status, value) => {
      if (res.destroyed || res.writableEnded) return;
      const body = Buffer.from(JSON.stringify(value));
      res.writeHead(status, { 'content-type': 'application/json', 'content-length': body.length });
      res.end(body);
    };
    const tenant = identities.get(req.headers.authorization);
    if (!tenant) { req.resume(); send(401, { error: 'Fixture identity required' }); return; }
    if (!['GET', 'POST'].includes(req.method)) { req.resume(); send(405, { error: 'Method not allowed' }); return; }
    if (!paths.has(req.url)) { req.resume(); send(404, { error: 'Unknown fixed route' }); return; }
    const affinity = req.headers['x-route-key'] ?? req.url;
    if (typeof affinity !== 'string' || !/^[a-zA-Z0-9/_-]{1,80}$/.test(affinity)) { req.resume(); send(400, { error: 'Invalid affinity key' }); return; }
    if (metrics.active >= maxInFlight) { req.resume(); metrics.rejected++; send(503, { error: 'Admission limit' }); return; }
    metrics.active++;
    metrics.admitted++;
    const release = () => {
      if (released) return;
      released = true;
      clearTimeout(timer);
      metrics.active--;
      if (node) node.active--;
    };
    res.once('finish', release);
    res.once('close', () => {
      if (!res.writableFinished && upstream) { metrics.cancelled++; upstream.destroy(); }
      release();
    });
    // One absolute deadline includes request buffering, socket acquisition and response buffering.
    timer = setTimeout(() => { metrics.timeouts++; send(504, { error: 'Request deadline' }); upstream?.destroy(); }, deadlineMs);
    try {
      const body = await readBody(req, maxBody);
      if (released || res.writableEnded || res.destroyed) return;
      const key = routeKey(tenant, affinity);
      node = pool.choose(key);
      if (!node) { send(503, { error: 'No eligible backend' }); return; }
      node.active++;
      metrics.attempts++;
      res.setHeader('x-backend-id', node.id);
      res.setHeader('x-primary-id', pool.ring.owner(key));
      res.setHeader('x-ring-version', pool.ring.version);
      // A fresh header allowlist prevents forwarding credentials, spoofed identity or hop-by-hop headers.
      const headers = { 'x-fixture-tenant': tenant, 'content-length': body.length };
      const nominated = new Set(String(req.headers.connection ?? '').toLowerCase().split(',').map(value => value.trim()));
      if (req.headers['content-type'] && !nominated.has('content-type')) headers['content-type'] = req.headers['content-type'];
      upstream = http.request(new URL(req.url, node.origin), { method: req.method, headers, agent }, incoming => {
        let size = 0;
        const chunks = [];
        incoming.on('data', chunk => {
          size += chunk.length;
          if (size > maxResponse) { send(502, { error: 'Upstream body limit' }); upstream.destroy(); }
          else chunks.push(chunk);
        });
        incoming.once('end', () => {
          if (res.destroyed || res.writableEnded) return;
          pool.observe(node.id, incoming.statusCode < 500);
          const response = Buffer.concat(chunks);
          res.writeHead(incoming.statusCode, { 'content-type': incoming.headers['content-type'] ?? 'application/octet-stream', 'content-length': response.length });
          res.end(response);
        });
        incoming.once('error', () => send(502, { error: 'Upstream response interrupted' }));
      });
      upstream.once('error', () => {
        if (!res.destroyed && !res.writableEnded) { pool.observe(node.id, false); send(502, { error: 'Upstream transport failure' }); }
      });
      upstream.end(body);
    } catch (error) { send(error.status ?? 400, { error: error.message }); }
  });
  server.headersTimeout = 1000;
  server.requestTimeout = 1000;
  return { server, pool, metrics, destroyAgent: () => agent.destroy() };
}

export async function probeOnce(pool) {
  await Promise.all(pool.nodes.map(node => new Promise(resolve => {
    let done = false;
    const finish = ok => { if (!done) { done = true; clearTimeout(timer); pool.observe(node.id, ok); resolve(); } };
    const req = http.get(new URL('/ready', node.origin), { agent: false }, res => { res.resume(); res.once('end', () => finish(res.statusCode === 200)); res.once('error', () => finish(false)); });
    const timer = setTimeout(() => { finish(false); req.destroy(); }, 200);
    req.once('error', () => finish(false));
  })));
}
