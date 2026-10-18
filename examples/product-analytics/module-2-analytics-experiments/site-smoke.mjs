import assert from 'node:assert/strict';
import { createServer } from 'node:net';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const base = path.dirname(fileURLToPath(import.meta.url));
const site = path.resolve(base, '../../../study-guide');
const content = path.join(site, 'content/docs');
async function markdownFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(entries.map(entry => entry.isDirectory()
    ? markdownFiles(path.join(directory, entry.name))
    : entry.name.endsWith('.md') ? [path.join(directory, entry.name)] : []));
  return files.flat();
}
const files = await markdownFiles(content);
const syllabus = JSON.parse(await readFile(path.join(base, '../roadmap/syllabus.json'), 'utf8'));
const available = syllabus.filter(row => row.status === 'Available');
const plannedSection = syllabus.find(row => row.status === 'Planned');
const productMeta = JSON.parse(await readFile(path.join(content, 'product-analytics/meta.json'), 'utf8'));
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
      if (route === '/' || route.startsWith('/docs/product-analytics')) retained.set(route, html);
      return { route, status: response.status };
    })));
    if (results.length % 16 === 0 || results.length === routes.length)
      console.log('Routes checked: ' + results.length + '/' + routes.length);
  }
  const chapterRoute = '/docs/product-analytics/product-analytics-experiments';
  const chapter = retained.get(chapterRoute);
  const roadmap = retained.get('/docs/product-analytics');
  const home = retained.get('/');
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/product-analytics"[^>]*>([\s\S]*?)<\/a>/g)]
    .map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const predecessor = retained.get('/docs/product-analytics/pricing-unit-economics');
  const assertions = {
    chapterTitle: chapter.includes('P2: Product Analytics and Experiments'),
    chapterEvidence: chapter.includes('95 local checks passed') && chapter.includes('SQLite 3.50.4') && chapter.includes('Python 3.13.15'),
    questionBank: chapter.includes('Q1.') && chapter.includes('Q30.'),
    interviewMock: chapter.includes('30-minute mock'),
    computedMetrics: chapter.includes('40.000000') && chapter.includes('60.000000'),
    experimentEvidence: chapter.includes('0.373272') && chapter.includes('7.626728') && chapter.includes('assignment_verified'),
    evidenceBoundaries: chapter.includes('No vendor account') && chapter.includes('randomized deployment'),
    sidebarGroup: chapter.includes('Analytics') && chapter.includes('Experiments'),
    roadmapLink: roadmap.includes(chapterRoute),
    predecessorLink: predecessor.includes(chapterRoute),
    remainingPlanned: roadmap.includes('P3') && roadmap.includes('P5') && roadmap.includes('Planned'),
    homeCard: cards.some(card => card.includes((available.length + 1) + ' chapters') && card.includes((productMeta.pages.length - 1) + ' groups')),
    sourceContainsSearchFilter: (await readFile(path.join(site, 'components/search-dialog.tsx'), 'utf8')).includes("value: 'product-analytics'"),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  let plannedStatus = null;
  if (plannedSection) {
    const planned = await fetch(origin + '/docs/product-analytics/' + plannedSection.slug,
      { signal: AbortSignal.timeout(20000) });
    assert.equal(planned.status, 404);
    plannedStatus = planned.status;
    await planned.text();
  }
  const search = {};
  for (const [tag, query, expected] of [
    ['product-analytics', 'Retention', chapterRoute],
    ['product-analytics', 'Pricing', '/docs/product-analytics/pricing-unit-economics'],
    ['product-analytics', 'RICE', '/docs/product-analytics/product-thinking-requirements-design'],
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
  evidence = { verified_date: '2026-10-18', node: process.version, port,
    routes: results, assertions, plannedChapterStatus: plannedStatus, search };
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
