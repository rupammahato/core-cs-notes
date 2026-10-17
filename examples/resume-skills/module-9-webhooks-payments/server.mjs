import { createServer } from 'node:http';
import { receive, IntegrationError, fail } from './webhook.mjs';

export function createWebhookServer({ endpoints, store }) {
  const server = createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, value, headers = {}) => {
      res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', ...headers });
      res.end(JSON.stringify(value));
    };
    try {
      const match = /^\/webhooks\/(alpha|beta)$/.exec(req.url);
      if (!match || !endpoints[match[1]]) fail(404, 'not_found');
      if (req.method !== 'POST') return send(405, { code: 'method_not_allowed' }, { Allow: 'POST' });
      const media = (req.headers['content-type'] ?? '').split(';').map(s => s.trim().toLowerCase());
      if (media[0] !== 'application/json' || media.slice(1).some(s => !/^charset="?utf-8"?$/.test(s)) ||
          (req.headers['content-encoding'] && req.headers['content-encoding'] !== 'identity'))
        fail(415, 'unsupported_body_format');
      let size = 0;
      const chunks = [];
      for await (const chunk of req) {
        size += chunk.length;
        if (size <= 16384) chunks.push(chunk);
      }
      if (size > 16384) fail(413, 'body_too_large');
      const result = receive({
        endpointId: match[1], endpoints, store, raw: Buffer.concat(chunks),
        signature: req.headers['x-razorpay-signature'], eventId: req.headers['x-razorpay-event-id'],
      });
      // Commit of the local inbox happened before acknowledgment; business work is separate.
      return send(202, result);
    } catch (error) {
      const known = error instanceof IntegrationError;
      const status = known ? error.status : 503;
      send(status, { code: known ? error.code : 'temporarily_unavailable' },
        status === 401 ? { 'WWW-Authenticate': 'Webhook-HMAC realm="local-fixture"' } : {});
    } finally {
      if (!req.readableEnded && !req.destroyed) req.resume();
    }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 5000;
  return server;
}
