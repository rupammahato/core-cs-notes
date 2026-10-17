import { createServer } from 'node:http';
import { open, readFile } from 'node:fs/promises';
import { pipeline } from 'node:stream/promises';

export const sampleFile = new URL('./fixtures/download.txt', import.meta.url);

function json(response, status, body, headers = {}) {
  response.writeHead(status, { 'content-type': 'application/json; charset=utf-8', ...headers });
  response.end(JSON.stringify(body));
}

export function createStudyServer({
  filePath = sampleFile,
  loadRecord = () => readFile(filePath, 'utf8'),
} = {}) {
  let draining = false;
  async function handle(request, response) {
    if (draining) {
      request.resume();
      json(response, 503, { error: 'draining' }, { connection: 'close' });
      return;
    }
    const { pathname } = new URL(request.url, 'http://localhost');
    if (request.method !== 'GET') {
      request.resume();
      json(response, 405, { error: 'method_not_allowed' }, { allow: 'GET' });
      return;
    }
    if (pathname === '/health') {
      json(response, 200, { status: 'ok' });
      return;
    }
    if (pathname === '/api/info') {
      const text = await loadRecord();
      if (!response.destroyed) json(response, 200, { bytes: Buffer.byteLength(text, 'utf8') });
      return;
    }
    if (pathname === '/download') {
      // Open before headers so a missing file can still become a JSON 404.
      const file = await open(filePath, 'r');
      try {
        const stat = await file.stat();
        response.writeHead(200, {
          'content-type': 'text/plain; charset=utf-8',
          'content-length': String(stat.size),
          'content-disposition': 'attachment; filename="study.txt"',
        });
        // Keep ownership of the descriptor here; always close it in finally.
        await pipeline(file.createReadStream({ autoClose: false, highWaterMark: 16 * 1024 }), response);
      } finally {
        await file.close();
      }
      return;
    }
    json(response, 404, { error: 'not_found' });
  }

  const server = createServer((request, response) => {
    request.on('error', () => response.destroy());
    response.on('error', () => {}); // pipeline/handle owns the operation's failure.
    void handle(request, response).catch(error => {
      if (response.destroyed || response.writableEnded) return;
      if (response.headersSent) {
        response.destroy(); // A completed/partial response cannot be replaced with JSON.
        return;
      }
      if (error.code === 'ENOENT') json(response, 404, { error: 'file_missing' });
      else json(response, 500, { error: 'internal_error' });
    });
  });
  return { server, beginDrain() { draining = true; } };
}
