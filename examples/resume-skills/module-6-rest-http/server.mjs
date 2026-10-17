import { createServer } from 'node:http';
import { createHash, randomUUID } from 'node:crypto';

class ApiError extends Error {
  constructor(status, code, detail, headers = {}) {
    super(detail);
    Object.assign(this, { status, code, headers });
  }
}
const fail = (status, code, detail, headers) => {
  throw new ApiError(status, code, detail, headers);
};
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const etag = task => '"' + createHash('sha256').update(JSON.stringify(task)).digest('hex') + '"';

function tags(header) {
  if (header === '*') return ['*'];
  const result = [];
  let rest = header.trim();
  while (rest) {
    const match = /^(W\/)?"[\x21\x23-\x7e\x80-\xff]*"/.exec(rest);
    if (!match) fail(400, 'invalid_condition', 'Use an entity-tag list or *.');
    result.push(match[0]);
    rest = rest.slice(match[0].length).trimStart();
    if (!rest) return result;
    if (!rest.startsWith(',')) fail(400, 'invalid_condition', 'Invalid entity-tag list.');
    rest = rest.slice(1).trimStart();
    if (!rest) fail(400, 'invalid_condition', 'Trailing comma is not allowed.');
  }
  if (!result.length) fail(400, 'invalid_condition', 'Condition cannot be empty.');
  return result;
}

function validateTask(input, partial = false) {
  if (!object(input)) fail(422, 'invalid_task', 'Task input must be an object.');
  const keys = Object.keys(input);
  if (keys.some(key => !['title', 'completed'].includes(key)))
    fail(422, 'unknown_field', 'Only title and completed are writable.');
  if (partial && !keys.length) fail(422, 'empty_patch', 'Supply at least one writable field.');
  const result = {};
  if (!partial || Object.hasOwn(input, 'title')) {
    if (typeof input.title !== 'string' || !input.title.trim() || input.title.trim().length > 80)
      fail(422, 'invalid_title', 'title must contain 1 to 80 characters after trimming.');
    result.title = input.title.trim();
  }
  if (!partial || Object.hasOwn(input, 'completed')) {
    if (typeof input.completed !== 'boolean')
      fail(422, 'invalid_completed', 'completed must be a boolean.');
    result.completed = input.completed;
  }
  return result;
}

async function jsonBody(req) {
  if (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity')
    fail(415, 'unsupported_encoding', 'Compressed request bodies are not supported.');
  const media = (req.headers['content-type'] ?? '').split(';').map(s => s.trim().toLowerCase());
  if (media[0] !== 'application/json' ||
      media.slice(1).some(s => !/^charset="?utf-8"?$/.test(s)))
    fail(415, 'unsupported_media_type', 'Send application/json encoded as UTF-8.');
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size <= 2048) chunks.push(chunk);
  }
  if (size > 2048) fail(413, 'body_too_large', 'JSON body exceeds 2048 bytes.');
  try {
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
  } catch {
    fail(400, 'invalid_json', 'Body must contain valid UTF-8 JSON.');
  }
}

function listTasks(tasks, params) {
  for (const key of params.keys()) {
    if (!['limit', 'completed', 'order', 'cursor'].includes(key) || params.getAll(key).length !== 1)
      fail(400, 'invalid_query', 'Unknown or repeated query parameter.');
  }
  const limitText = params.get('limit') ?? '2';
  if (!/^[1-5]$/.test(limitText)) fail(400, 'invalid_limit', 'limit must be 1 to 5.');
  const limit = Number(limitText);
  const completed = params.get('completed');
  if (completed !== null && !['true', 'false'].includes(completed))
    fail(400, 'invalid_filter', 'completed must be true or false.');
  const order = params.get('order') ?? 'asc';
  if (!['asc', 'desc'].includes(order)) fail(400, 'invalid_order', 'order must be asc or desc.');
  let after = null;
  const cursor = params.get('cursor');
  if (cursor !== null) {
    try {
      const bytes = Buffer.from(cursor, 'base64url');
      if (!cursor || cursor.length > 512 || bytes.toString('base64url') !== cursor) throw Error();
      const parsed = JSON.parse(bytes.toString('utf8'));
      if (!object(parsed) || Object.keys(parsed).sort().join(',') !== 'after,completed,order' ||
          !Number.isSafeInteger(parsed.after) || parsed.after < 1 ||
          parsed.completed !== completed || parsed.order !== order) throw Error();
      after = parsed.after;
    } catch {
      fail(400, 'invalid_cursor', 'Cursor must match this filter and ordering.');
    }
  }
  const rows = [...tasks.values()]
    .filter(task => completed === null || task.completed === (completed === 'true'))
    .filter(task => after === null || (order === 'asc' ? task.id > after : task.id < after))
    .sort((a, b) => order === 'asc' ? a.id - b.id : b.id - a.id);
  const items = rows.slice(0, limit);
  let next = null;
  if (rows.length > limit) {
    const token = Buffer.from(JSON.stringify({
      after: items.at(-1).id, completed, order,
    })).toString('base64url');
    const query = new URLSearchParams({ limit: String(limit), order });
    if (completed !== null) query.set('completed', completed);
    query.set('cursor', token);
    next = '/v1/tasks?' + query;
  }
  return { items, next };
}

export function createTaskServer({
  now = Date.now,
  beforeCreate = async () => {},
  onReplay = () => {},
  idempotencyTtlMs = 60_000,
} = {}) {
  const tasks = new Map();
  const requests = new Map();
  let nextId = 1;
  let windowId = null;
  let used = 0;

  const server = createServer(async (req, res) => {
    const requestId = randomUUID();
    res.setHeader('X-Request-Id', requestId);
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, body, headers = {}) => {
      res.writeHead(status, {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }),
        ...headers,
      });
      res.end(req.method === 'HEAD' || body === undefined ? undefined : JSON.stringify(body));
    };
    try {
      const url = new URL(req.url, 'http://localhost');
      let pathname;
      try { pathname = decodeURIComponent(url.pathname); }
      catch { fail(400, 'invalid_path', 'Path encoding is invalid.'); }
      const collection = pathname === '/v1/tasks';
      const limited = pathname === '/v1/limited';
      const match = /^\/v1\/tasks\/([^/]+)$/.exec(pathname);
      if (!collection && !limited && !match) fail(404, 'not_found', 'Route does not exist.');
      let id;
      if (match) {
        if (!/^[1-9]\d*$/.test(match[1]) || !Number.isSafeInteger(Number(match[1])))
          fail(400, 'invalid_id', 'Task ID must be a positive safe integer.');
        id = Number(match[1]);
      }
      const allow = collection ? 'GET, HEAD, POST, OPTIONS'
        : limited ? 'GET, HEAD, OPTIONS' : 'GET, HEAD, PUT, PATCH, DELETE, OPTIONS';
      if (req.method === 'OPTIONS') return send(204, undefined, {
        Allow: allow, ...(match ? { 'Accept-Patch': 'application/json' } : {}),
      });
      if (!allow.split(', ').includes(req.method))
        fail(405, 'method_not_allowed', 'Method is not supported on this route.', { Allow: allow });
      if (!collection && url.search)
        fail(400, 'invalid_query', 'This route has no query parameters.');
      if (collection && !['GET', 'HEAD'].includes(req.method) && url.search)
        fail(400, 'invalid_query', 'Creation has no query parameters.');

      if (limited) {
        const current = Math.floor(now() / 10_000);
        if (current !== windowId) { windowId = current; used = 0; }
        if (used >= 2) fail(429, 'rate_limited', 'Demo global budget exhausted.', {
          'Retry-After': String(Math.max(1, Math.ceil(((current + 1) * 10_000 - now()) / 1000))),
        });
        used++;
        return send(200, { remaining: 2 - used });
      }

      if (collection && ['GET', 'HEAD'].includes(req.method)) {
        const page = listTasks(tasks, url.searchParams);
        return send(200, page, page.next ? { Link: '<' + page.next + '>; rel="next"' } : {});
      }
      if (collection) {
        const input = validateTask(await jsonBody(req));
        const key = req.headers['idempotency-key'];
        if (typeof key !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(key))
          fail(400, 'invalid_key', 'Supply an Idempotency-Key with 1 to 64 letters, digits, _ or -.');
        // A single loopback demo scope. Production scope must use verified identity.
        const scopedKey = 'demo:POST:/v1/tasks:' + key;
        const fingerprint = JSON.stringify(input);
        for (const [storedKey, record] of requests)
          if (record.done && record.expiresAt <= now()) requests.delete(storedKey);
        const prior = requests.get(scopedKey);
        if (prior) {
          if (prior.fingerprint !== fingerprint)
            fail(409, 'key_conflict', 'This key was used with different task input.');
          onReplay();
          const saved = await prior.promise;
          return send(201, saved.task, {
            Location: saved.location, ETag: etag(saved.task), 'Idempotency-Replayed': 'true',
          });
        }
        const record = { fingerprint, done: false };
        // Defer the operation so the record is reserved before beforeCreate can yield.
        record.promise = Promise.resolve().then(async () => {
          await beforeCreate();
          const task = { id: nextId++, ...input };
          tasks.set(task.id, task);
          record.done = true;
          record.expiresAt = now() + idempotencyTtlMs;
          return { task, location: '/v1/tasks/' + task.id };
        });
        requests.set(scopedKey, record);
        try {
          const saved = await record.promise;
          return send(201, saved.task, { Location: saved.location, ETag: etag(saved.task) });
        } catch (error) {
          requests.delete(scopedKey);
          throw error;
        }
      }

      const input = ['GET', 'HEAD', 'DELETE'].includes(req.method) ? null
        : validateTask(await jsonBody(req), req.method === 'PATCH');
      const task = tasks.get(id);
      if (!task) fail(404, 'not_found', 'Task does not exist.');
      const currentTag = etag(task);
      if (['GET', 'HEAD'].includes(req.method)) {
        const condition = req.headers['if-none-match'];
        const headers = { ETag: currentTag, 'Cache-Control': 'private, no-cache' };
        if (condition !== undefined && tags(condition).some(tag => tag === '*' || tag.replace(/^W\//, '') === currentTag))
          return send(304, undefined, headers);
        return send(200, task, headers);
      }
      const condition = req.headers['if-match'];
      if (condition === undefined) fail(428, 'condition_required', 'Send the ETag in If-Match.');
      // Comparison and write have no await between them in this one-process store.
      if (!tags(condition).some(tag => tag === '*' || tag === currentTag))
        fail(412, 'stale_version', 'Task changed; fetch it and reconcile before retrying.');
      if (req.method === 'DELETE') {
        tasks.delete(id);
        return send(204);
      }
      const updated = { id, ...(req.method === 'PATCH' ? task : {}), ...input };
      tasks.set(id, updated);
      // PUT normalizes/builds the stored representation, so omit response validators.
      return send(200, updated, req.method === 'PATCH' ? { ETag: etag(updated) } : {});
    } catch (error) {
      if (res.headersSent) { res.destroy(); return; }
      const known = error instanceof ApiError;
      const status = known ? error.status : 500;
      send(status, {
        type: 'about:blank',
        title: {
          400: 'Bad Request', 404: 'Not Found', 405: 'Method Not Allowed',
          409: 'Conflict', 412: 'Precondition Failed', 413: 'Content Too Large',
          415: 'Unsupported Media Type', 422: 'Unprocessable Content',
          428: 'Precondition Required', 429: 'Too Many Requests', 500: 'Internal Server Error',
        }[status],
        status,
        detail: known ? error.message : 'Unexpected server failure.',
        instance: 'urn:uuid:' + requestId,
        code: known ? error.code : 'internal_error',
        requestId,
      }, { 'Content-Type': 'application/problem+json', ...(known ? error.headers : {}) });
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
    }
  });
  server.requestTimeout = 10_000;
  server.headersTimeout = 5_000;
  return server;
}
