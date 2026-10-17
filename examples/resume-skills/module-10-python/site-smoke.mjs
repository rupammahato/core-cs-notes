import assert from 'node:assert/strict';
import { createServer } from 'node:net';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';

const [siteRoot, outputPath] = process.argv.slice(2);
const probe = createServer(); probe.listen(0, '127.0.0.1'); await once(probe, 'listening');
const port = probe.address().port;
await new Promise(resolve => probe.close(resolve));
const child = spawn(process.execPath, [
  path.join(siteRoot, 'node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', String(port),
], { cwd: siteRoot, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
let stdout = '', stderr = '', timer, evidence;
child.stderr.on('data', chunk => { stderr += chunk; });
try {
  await new Promise((resolve, reject) => {
    timer = setTimeout(() => reject(new Error('Site readiness deadline')), 20000);
    child.stdout.on('data', chunk => { stdout += chunk; if (stdout.includes('Ready in')) resolve(); });
    child.once('error', reject);
    child.once('exit', code => reject(new Error('Site exited: ' + code + stderr)));
  });
  clearTimeout(timer);
  const chapterUrl = '/docs/resume-skills/python-fundamentals';
  const routes = [
    '/', '/docs/resume-skills', '/docs/resume-skills/how-backend-works',
    '/docs/resume-skills/javascript-fundamentals', '/docs/resume-skills/asynchronous-javascript',
    '/docs/resume-skills/typescript-fundamentals', '/docs/resume-skills/nodejs',
    '/docs/resume-skills/express-backend-structure', '/docs/resume-skills/rest-apis-http',
    '/docs/resume-skills/authentication-sessions-jwt-oauth', '/docs/resume-skills/api-security-authorization-multi-tenancy', '/docs/resume-skills/webhooks-payments-reliable-integrations', chapterUrl, '/docs/dbms',
  ];
  const pages = await Promise.all(routes.map(async route => {
    const response = await fetch('http://127.0.0.1:' + port + route, { signal: AbortSignal.timeout(20000) });
    const html = await response.text(); assert.equal(response.status, 200, route);
    return { route, status: response.status, html };
  }));
  const chapter = pages.find(p => p.route === chapterUrl).html;
  const assertions = {
    title: chapter.includes('Python Fundamentals for Backend Interviews'),
    q30: chapter.includes('Q30.'), implementation: chapter.includes('make_quote'),
    totalChecks: chapter.includes('44 checks'),
    concurrency: chapter.includes('Bound both active work and queued work'),
    architecture: chapter.includes('Architectural understanding: a document-processing backend'),
    nextFrameworks: chapter.includes('M11: Flask, FastAPI'), group: chapter.includes('Python Backend'),
    roadmapLink: pages.find(p => p.route === '/docs/resume-skills').html.includes(chapterUrl),
    previousLink: pages.find(p => p.route === '/docs/resume-skills/webhooks-payments-reliable-integrations').html.includes(chapterUrl),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const response = await fetch('http://127.0.0.1:' + port + '/api/search?query=python&tag=resume-skills');
  assert.equal(response.status, 200);
  const search = await response.json();
  assert.ok(search.some(item => item.url === chapterUrl));
  assert.ok(search.every(item => item.url.startsWith('/docs/resume-skills')));
  evidence = {
    port, routes: pages.map(({ route, status }) => ({ route, status })), assertions,
    search: { status: response.status, results: search.length, chapterIndexed: true, scoped: true },
  };
} finally {
  clearTimeout(timer);
  if (child.exitCode === null && child.signalCode === null) {
    const exited = once(child, 'exit'); child.kill(); await exited;
  }
}
evidence.temporaryServerClosed = true;
await writeFile(outputPath, JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence));
console.log('Temporary website process stopped.');
