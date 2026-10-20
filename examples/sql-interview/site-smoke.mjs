import assert from 'node:assert/strict';
import { createServer } from 'node:net';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const base = path.dirname(fileURLToPath(import.meta.url));
const site = path.resolve(base, '../../study-guide');
const content = path.join(site, 'content/docs');
async function markdownFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(entries.map(entry => entry.isDirectory()
    ? markdownFiles(path.join(directory, entry.name))
    : entry.name.endsWith('.md') ? [path.join(directory, entry.name)] : []));
  return files.flat();
}
const files = await markdownFiles(content);
const subjectMeta = JSON.parse(await readFile(path.join(content, 'sql-interview/meta.json'), 'utf8'));
const routes = ['/', ...files.map(file => {
  const parts = path.relative(content, file).split(path.sep);
  const slug = path.basename(file, '.md');
  return '/docs/' + parts[0] + (slug === 'index' ? '' : '/' + slug);
})];
assert.equal(new Set(routes).size, routes.length);
const probe = createServer();
probe.listen(0, '127.0.0.1');
await once(probe, 'listening');
const port = probe.address().port;
assert.notEqual(port, 3000);
await new Promise(resolve => probe.close(resolve));
const child = spawn(process.execPath,
  [path.join(site, 'node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', String(port)],
  { cwd: site, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
let stdout = '', stderr = '', timer, evidence;
child.stderr.on('data', chunk => { stderr += chunk; });
const origin = 'http://127.0.0.1:' + port;
try {
  await new Promise((resolve, reject) => {
    timer = setTimeout(() => reject(new Error('Readiness timeout: ' + stdout + stderr)), 20000);
    child.stdout.on('data', chunk => { stdout += chunk; if (stdout.includes('Ready in')) resolve(); });
    child.once('error', reject);
    child.once('exit', code => reject(new Error('Early site exit: ' + code + stderr)));
  });
  clearTimeout(timer);
  console.log('Owned preview ready on loopback port ' + port);
  const retained = new Map();
  const results = [];
  for (let offset = 0; offset < routes.length; offset += 4) {
    results.push(...await Promise.all(routes.slice(offset, offset + 4).map(async route => {
      const response = await fetch(origin + route, { signal: AbortSignal.timeout(20000) });
      assert.equal(response.status, 200, route);
      const html = await response.text();
      if (route === '/' || route.startsWith('/docs/sql-interview')) retained.set(route, html);
      return { route, status: response.status };
    })));
    if (results.length % 16 === 0 || results.length === routes.length)
      console.log('Routes checked: ' + results.length + '/' + routes.length);
  }
  const chapterRoute = '/docs/sql-interview/consolidation-and-mocks';
  const chapter = retained.get(chapterRoute);
  const roadmap = retained.get('/docs/sql-interview');
  const home = retained.get('/');
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/sql-interview"[^>]*>([\s\S]*?)<\/a>/g)]
    .map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const sections = ['joins-grain-and-null-semantics', 'windows-and-time-series',
    'funnels-cohorts-and-retention', 'reconciliation-and-query-plans'];
  const worked = sections.map(slug => retained.get('/docs/sql-interview/' + slug));
  const method = retained.get('/docs/sql-interview/dataset-and-solving-method');
  const assertions = {
    routeCount: routes.length === 136,
    chapterTitle: chapter.includes('Consolidation and Mocks'),
    questionCoverage: Array.from({ length: 30 }, (_, i) => 'Q' + String(i + 1).padStart(2, '0') + '.').every(id => worked.some(html => html.includes(id))),
    workedQueriesAndOutputs: worked.every(html => html.includes('Worked query') && html.includes('Verified output') && html.includes('Interview follow-up')),
    finalMocks: chapter.includes('Mock A') && chapter.includes('Mock B') && chapter.includes('45 minutes'),
    revisionCoverage: chapter.includes('O24') && chapter.includes('D12') && chapter.includes('confusable pairs'),
    actualMetrics: worked[2].includes('33.333333') && worked[2].includes('retention'),
    planEvidence: worked[3].includes('orders_customer_time') && worked[3].includes('Actual plan evidence'),
    sourceRows: method.includes('o11') && method.includes('delivery_id') && method.includes('UTC-midnight'),
    evidenceBoundary: method.includes('full supplied snapshot') && method.includes('No cross-engine result parity'),
    roadmapLinks: sections.every(slug => roadmap.includes('/docs/sql-interview/' + slug)) && roadmap.includes(chapterRoute),
    roadmapEvidence: roadmap.includes('86 local checks passed') && roadmap.includes('Authoring status: complete'),
    homeCard: cards.some(card => card.includes('7 chapters') && card.includes('3 groups')),
    sidebarGroups: subjectMeta.pages.length === 4 && worked.every(html => html.includes('Worked Problems') && html.includes('Revision')),
    sourceContainsSearchFilter: (await readFile(path.join(site, 'components/search-dialog.tsx'), 'utf8')).includes("value: 'sql-interview'"),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const missingResponse = await fetch(origin + '/docs/sql-interview/no-such-chapter', { signal: AbortSignal.timeout(20000) });
  assert.equal(missingResponse.status, 404);
  await missingResponse.text();
  const search = {};
  for (const [tag, query, expected] of [
    ['sql-interview', 'Session', '/docs/sql-interview/windows-and-time-series'],
    ['sql-interview', 'Retention', '/docs/sql-interview/funnels-cohorts-and-retention'],
    ['sql-interview', 'Reconciliation', '/docs/sql-interview/reconciliation-and-query-plans'],
    ['sql-interview', 'NULL', '/docs/sql-interview/joins-grain-and-null-semantics'],
    ['sql-interview', 'Mocks', chapterRoute],
    ['product-analytics', 'Confusable', '/docs/product-analytics/consolidation-resume-drills'],
    ['system-design', 'Analytics', '/docs/system-design/analytics-event-pipeline'],
    ['resume-skills', 'Consolidation', '/docs/resume-skills/consolidation-interview-drills'],
  ]) {
    const response = await fetch(origin + '/api/search?query=' + encodeURIComponent(query) + '&tag=' + tag,
      { signal: AbortSignal.timeout(30000) });
    assert.equal(response.status, 200);
    const items = await response.json();
    assert.ok(items.length && items.some(item => item.url.split('#')[0] === expected));
    assert.ok(items.every(item => item.url.split('#')[0] === '/docs/' + tag || item.url.startsWith('/docs/' + tag + '/')));
    search[tag + ':' + query] = { query, status: response.status, results: items.length, indexed: true, scoped: true };
    console.log('Scoped search passed: ' + tag);
  }
  evidence = { verified_date: '2026-10-20', node: process.version, port,
    routes: results, assertions, missingChapterStatus: missingResponse.status, search };
} finally {
  clearTimeout(timer);
  if (child.exitCode === null && child.signalCode === null) {
    const exited = once(child, 'exit');
    child.kill();
    await exited;
  }
  console.log('Owned preview process closed');
}
let stillResponding = false;
try { await fetch(origin, { signal: AbortSignal.timeout(2000) }); stillResponding = true; } catch {}
assert.equal(stillResponding, false);
evidence.temporaryServerClosed = true;
await writeFile(path.join(base, 'site-validation.json'), JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify({ routesChecked: evidence.routes.length, assertions: evidence.assertions,
  search: evidence.search, temporaryServerClosed: true }, null, 2));
