import { createServer } from 'node:http';
import { AuthError } from './identity.mjs';

async function body(req) {
  if ((req.headers['content-type'] ?? '').split(';')[0].trim().toLowerCase() !== 'application/json' ||
      (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity'))
    throw new AuthError(415, 'unsupported_body_format');
  const chunks = [];
  let bytes = 0;
  for await (const chunk of req) {
    bytes += chunk.length;
    if (bytes <= 2048) chunks.push(chunk);
  }
  if (bytes > 2048) throw new AuthError(413, 'body_too_large');
  try {
    const value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error();
    return value;
  } catch { throw new AuthError(400, 'invalid_json_object'); }
}
function fields(value, allowed) {
  if (Object.keys(value).some(key => !allowed.includes(key)) ||
      allowed.some(key => typeof value[key] !== 'string' || !value[key]))
    throw new AuthError(400, 'invalid_input');
  if (value.password && Buffer.byteLength(value.password, 'utf8') > 256)
    throw new AuthError(400, 'invalid_input');
  return value;
}
function cookieToken(header, name) {
  const matches = (header ?? '').split(';').map(s => s.trim()).filter(s => s.startsWith(name + '='));
  if (matches.length > 1) throw new AuthError(400, 'ambiguous_cookie');
  return matches[0]?.slice(name.length + 1);
}
export function createAuthServer({
  identity, trustedOrigin = 'https://app.example.test', secureCookies = true,
} = {}) {
  if (!identity) throw new TypeError('Supply the identity service.');
  const cookieName = secureCookies ? '__Host-sid' : 'sid';
  const cookie = (token, clear = false) =>
    cookieName + '=' + token + '; Path=/; HttpOnly; SameSite=Lax; Max-Age=' +
    (clear ? '0' : '120') + (secureCookies ? '; Secure' : '');
  const server = createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, value, headers = {}) => {
      res.writeHead(status, {
        ...(value === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }),
        ...headers,
      });
      res.end(value === undefined ? undefined : JSON.stringify(value));
    };
    try {
      const url = new URL(req.url, 'http://localhost');
      const routes = {
        '/session/login': 'POST', '/session/me': 'GET', '/session/logout': 'POST',
        '/tokens/login': 'POST', '/tokens/refresh': 'POST', '/tokens/logout': 'POST',
        '/api/me': 'GET',
      };
      const method = routes[url.pathname];
      if (!method) throw new AuthError(404, 'not_found');
      if (req.method !== method) return send(405, { code: 'method_not_allowed' }, { Allow: method });
      if (url.search) throw new AuthError(400, 'unexpected_query');
      if (method === 'POST' && req.headers.origin !== trustedOrigin)
        throw new AuthError(403, 'origin_rejected');

      if (url.pathname === '/session/login' || url.pathname === '/tokens/login') {
        const input = fields(await body(req), ['email', 'password']);
        const subject = await identity.login(input.email, input.password);
        if (url.pathname === '/session/login') {
          const prior = cookieToken(req.headers.cookie, cookieName);
          const session = identity.makeSession(subject, prior);
          return send(200, { authenticated: true, csrfToken: session.csrf }, {
            'Set-Cookie': cookie(session.token),
          });
        }
        return send(200, {
          accessToken: await identity.issueAccess(subject),
          refreshToken: identity.makeRefresh(subject),
          tokenType: 'Bearer', expiresIn: 60,
        });
      }
      if (url.pathname === '/session/me')
        return send(200, identity.sessionView(cookieToken(req.headers.cookie, cookieName)));
      if (url.pathname === '/session/logout') {
        identity.logoutSession(cookieToken(req.headers.cookie, cookieName), req.headers['x-csrf-token']);
        return send(204, undefined, { 'Set-Cookie': cookie('', true) });
      }
      if (url.pathname === '/tokens/refresh') {
        const { refreshToken } = fields(await body(req), ['refreshToken']);
        const rotated = identity.rotateRefresh(refreshToken);
        return send(200, {
          accessToken: await identity.issueAccess(rotated.subject),
          refreshToken: rotated.refreshToken, tokenType: 'Bearer', expiresIn: 60,
        });
      }
      if (url.pathname === '/tokens/logout') {
        const { refreshToken } = fields(await body(req), ['refreshToken']);
        identity.revokeRefresh(refreshToken);
        return send(204);
      }
      const authorization = req.headers.authorization ?? '';
      const match = /^Bearer ([^\s,]+)$/i.exec(authorization);
      if (!match) throw new AuthError(401, 'invalid_access_token');
      return send(200, await identity.accessView(match[1]));
    } catch (error) {
      const known = error instanceof AuthError;
      const status = known ? error.status : 500;
      send(status, { code: known ? error.code : 'internal_error' }, status === 401 ? {
        'WWW-Authenticate': req.url === '/api/me' ? 'Bearer realm="placement-demo"' : 'Session realm="placement-demo"',
      } : {});
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
    }
  });
  server.requestTimeout = 10_000;
  server.headersTimeout = 5000;
  return server;
}
