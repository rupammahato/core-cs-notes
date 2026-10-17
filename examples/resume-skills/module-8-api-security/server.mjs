import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { ApiError, createBudget, fail } from './security.mjs';

async function bytes(req, mediaType, maximum) {
  const parts = (req.headers['content-type'] ?? '').split(';').map(s => s.trim().toLowerCase());
  if (parts[0] !== mediaType || parts.slice(1).some(s => !/^charset="?utf-8"?$/.test(s)) ||
      (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity'))
    fail(415, 'unsupported_body_format');
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size <= maximum) chunks.push(chunk);
  }
  if (size > maximum) fail(413, 'body_too_large');
  return Buffer.concat(chunks);
}
async function json(req) {
  const data = await bytes(req, 'application/json', 2048);
  try { return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(data)); }
  catch { fail(400, 'invalid_json'); }
}
export function createSecurityServer({
  authenticate, service, now = Date.now, importLimit = 3,
  allowedOrigins = ['https://app.example.test'], onAudit = () => {},
}) {
  const origins = new Set(allowedOrigins);
  const importBudget = createBudget({ now, limit: importLimit });
  const server = createServer(async (req, res) => {
    const requestId = randomUUID();
    let principal, tenant, action = 'route';
    res.setHeader('X-Request-Id', requestId);
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Vary', 'Origin');
    const send = (status, data, headers = {}) => {
      res.writeHead(status, {
        ...(data === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }),
        ...headers,
      });
      res.end(data === undefined ? undefined : JSON.stringify(data));
    };
    try {
      const origin = req.headers.origin;
      if (origin !== undefined) {
        if (!origins.has(origin)) fail(403, 'origin_rejected');
        res.setHeader('Access-Control-Allow-Origin', origin);
        res.setHeader('Access-Control-Expose-Headers', 'ETag, X-Request-Id');
      }
      const url = new URL(req.url, 'http://localhost');
      const match = /^\/tenants\/([a-z][a-z0-9-]{0,15})\/documents(?:\/(bulk-delete|import|[1-9]\d*)(\/download)?)?$/.exec(url.pathname);
      if (!match || (match[3] && !/^[1-9]\d*$/.test(match[2]))) fail(404, 'not_found');
      tenant = match[1];
      const suffix = match[2];
      const item = suffix && /^[1-9]\d*$/.test(suffix);
      const id = item ? Number(suffix) : undefined;
      if (item && !Number.isSafeInteger(id)) fail(400, 'invalid_id');
      action = !suffix ? (req.method === 'POST' ? 'create' : 'list')
        : suffix === 'import' ? 'import' : suffix === 'bulk-delete' ? 'bulk-delete'
          : match[3] ? 'download' : req.method === 'PATCH' ? 'update' : 'get';
      const methods = !suffix ? ['GET', 'POST']
        : item ? (match[3] ? ['GET'] : ['GET', 'PATCH']) : ['POST'];
      if (req.method === 'OPTIONS') {
        const requestedMethod = req.headers['access-control-request-method'];
        const requested = (req.headers['access-control-request-headers'] ?? '')
          .split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
        if (!origin || !requestedMethod) fail(400, 'invalid_preflight');
        if (!methods.includes(requestedMethod) ||
            requested.some(name => !['authorization', 'content-type', 'if-match', 'x-file-name'].includes(name)))
          fail(403, 'preflight_rejected');
        return send(204, undefined, {
          'Access-Control-Allow-Methods': methods.join(', '),
          'Access-Control-Allow-Headers': requested.join(', '),
          'Access-Control-Max-Age': '60',
          Vary: 'Origin, Access-Control-Request-Method, Access-Control-Request-Headers',
        });
      }
      if (!methods.includes(req.method)) fail(405, 'method_not_allowed', { Allow: methods.join(', ') + ', OPTIONS' });
      principal = await authenticate(req.headers.authorization);
      if (action !== 'list' && url.search) fail(400, 'unexpected_query');

      if (action === 'list') {
        for (const name of url.searchParams.keys())
          if (!['after', 'limit', 'q'].includes(name) || url.searchParams.getAll(name).length !== 1)
            fail(400, 'invalid_query');
        const after = url.searchParams.get('after') ?? '0', limit = url.searchParams.get('limit') ?? '2';
        if (!/^(0|[1-9]\d*)$/.test(after) || !/^[1-5]$/.test(limit)) fail(400, 'invalid_query');
        return send(200, await service.list(principal, tenant, {
          after: Number(after), limit: Number(limit), query: url.searchParams.get('q') ?? '',
        }));
      }
      if (action === 'get' || action === 'download') {
        const result = await service.get(principal, tenant, id, action === 'download');
        if (action === 'download') {
          res.writeHead(200, {
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': 'attachment; filename="' + result.filename + '"',
          });
          return res.end(result.content);
        }
        return send(200, result, { ETag: '"v' + result.version + '"' });
      }
      if (action === 'create') {
        service.mayCreate(principal, tenant);
        const result = await service.create(principal, tenant, await json(req));
        return send(201, result, { Location: '/tenants/' + tenant + '/documents/' + result.id });
      }
      if (action === 'update') {
        const result = await service.update(principal, tenant, id, await json(req), req.headers['if-match']);
        return send(200, result, { ETag: '"v' + result.version + '"' });
      }
      if (action === 'bulk-delete') {
        const input = await json(req);
        if (!input || typeof input !== 'object' || Array.isArray(input) ||
            Object.keys(input).join(',') !== 'ids') fail(400, 'invalid_ids');
        await service.bulkDelete(principal, tenant, input.ids);
        return send(204);
      }
      service.mayCreate(principal, tenant);
      importBudget(tenant, principal.subject);
      const data = await bytes(req, 'text/plain', 1024);
      const result = await service.importText(principal, tenant, req.headers['x-file-name'], data);
      return send(201, result, { Location: '/tenants/' + tenant + '/documents/' + result.id });
    } catch (error) {
      if (res.headersSent) { res.destroy(); return; }
      const known = error instanceof ApiError;
      send(known ? error.status : 500, {
        code: known ? error.code : 'internal_error', requestId,
      }, known ? error.headers : {});
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
      // Best-effort audit example. Do not retain credentials, titles or request bodies.
      try { onAudit({ requestId, subject: principal?.subject ?? null, tenant: tenant ?? null, action, status: res.statusCode }); }
      catch { /* A production audit sink needs its own durability/failure policy. */ }
    }
  });
  server.requestTimeout = 10_000;
  server.headersTimeout = 5000;
  return server;
}
