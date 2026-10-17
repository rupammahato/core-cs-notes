import express, { type Request, type Response, type NextFunction } from 'express';
import { randomUUID } from 'node:crypto';
import { RuleError, type Principal, type NotesService, type Trace, type Note } from './notes.js';

// Fixed allowlist for loopback lessons. These published tokens are NOT production credentials.
export const lessonTokens = new Map<string, Principal>([
  ['lesson-alice', { tenant: 'alpha', owner: 'alice' }],
  ['lesson-bob', { tenant: 'alpha', owner: 'bob' }],
  ['lesson-other-tenant', { tenant: 'beta', owner: 'alice' }],
]);
type Context = { who: Principal; trace: Trace; requestId: string };
class HttpError extends Error {
  constructor(public readonly status: number, public readonly code: string) { super(code); }
}
export function createApp(service: NotesService, observe: (id: string, event: string) => void = () => {},
                          tokens: ReadonlyMap<string, Principal> = lessonTokens) {
  const app = express();
  app.disable('x-powered-by');
  app.set('etag', false); // Deliberate revision tags below; avoid automatic tags for error JSON.
  app.use((req, res, next) => {
    const requestId = randomUUID();
    const trace: Trace = event => observe(requestId, event);
    res.locals.context = { requestId, trace };
    res.set('X-Request-Id', requestId).set('Cache-Control', 'no-store');
    trace('http.received');
    next();
  });
  app.use('/notes', (req, res, next) => {
    const raw = req.get('authorization') ?? '';
    const who = raw.startsWith('Bearer ') ? tokens.get(raw.slice(7)) : undefined;
    if (!who) {
      res.set('WWW-Authenticate', 'Bearer');
      return next(new HttpError(401, 'unauthorized'));
    }
    res.locals.context.who = { ...who }; // Never take tenant/owner from body or forwarded headers.
    res.locals.context.trace('identity.allowlist_verified');
    next();
  });
  app.use('/notes', (req, _res, next) => {
    if ((req.method === 'POST' || req.method === 'PUT') && !req.is('application/json')) {
      return next(new HttpError(415, 'json_required'));
    }
    next();
  }, express.json({ limit: '8kb', strict: true }));
  function context(res: Response): Context { return res.locals.context as Context; }
  function send(res: Response, note: Note, status: number): void {
    context(res).trace('controller.response');
    res.status(status).set('ETag', '"' + note.revision + '"').json(note);
  }
  app.post('/notes', async (req, res) => {
    const { who, trace } = context(res);
    trace('controller.create');
    const result = service.create(who, req.get('Idempotency-Key') ?? '', req.body, trace);
    res.set('Location', '/notes/' + result.note.id).set('Idempotency-Replayed', String(result.replayed));
    send(res, result.note, 201);
  });
  app.get('/notes/:id', async (req, res) => {
    const { who, trace } = context(res);
    trace('controller.get');
    send(res, service.get(who, req.params.id, trace), 200);
  });
  app.put('/notes/:id', async (req, res) => {
    const { who, trace } = context(res);
    const condition = req.get('If-Match');
    if (condition === undefined) throw new HttpError(428, 'revision_required');
    // This small API accepts exactly one strong numeric tag; not the full HTTP tag grammar.
    if (!/^"[1-9][0-9]*"$/.test(condition)) throw new HttpError(400, 'invalid_revision');
    trace('controller.replace');
    send(res, service.replace(who, req.params.id, Number(condition.slice(1, -1)), req.body, trace), 200);
  });
  app.use((_req, _res, next) => next(new HttpError(404, 'not_found')));
  app.use((error: unknown, _req: Request, res: Response, _next: NextFunction) => {
    let status = 500, code = 'internal_error';
    if (error instanceof HttpError) { status = error.status; code = error.code; }
    else if (error instanceof RuleError) {
      const mapping = { invalid: [400, 'invalid_input'], missing: [404, 'not_found'],
        conflict: [409, 'operation_conflict'], stale: [412, 'stale_revision'] } as const;
      [status, code] = mapping[error.code];
    } else if (error && typeof error === 'object' && 'type' in error) {
      if (error.type === 'entity.too.large') { status = 413; code = 'body_too_large'; }
      if (error.type === 'entity.parse.failed') { status = 400; code = 'invalid_json'; }
    }
    context(res).trace('http.error.' + status);
    res.status(status).json({ error: code });
  });
  return app;
}
