import express from 'express';
import { createServer } from 'node:http';

export async function requestApp(configure, route = '/', options = {}) {
  const app = express();
  app.disable('x-powered-by');
  configure(app);
  const server = createServer(app);
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  try {
    const response = await fetch('http://127.0.0.1:' + server.address().port + route, {
      ...options, headers: { connection: 'close', ...options.headers },
      signal: AbortSignal.timeout(2000),
    });
    const text = await response.text();
    const body = text && response.headers.get('content-type')?.includes('application/json')
      ? JSON.parse(text) : text;
    return { status: response.status, headers: Object.fromEntries(response.headers), text, body };
  } finally {
    await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  }
}
