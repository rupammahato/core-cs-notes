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
const subjectMeta = JSON.parse(await readFile(path.join(content, 'analytics-engineering/meta.json'), 'utf8'));
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
      if (route === '/' || route.startsWith('/docs/analytics-engineering')) retained.set(route, html);
      return { route, status: response.status };
    })));
    if (results.length % 16 === 0 || results.length === routes.length)
      console.log('Routes checked: ' + results.length + '/' + routes.length);
  }
  const chapterRoute = '/docs/analytics-engineering/consolidation-and-mocks';
  const chapter = retained.get(chapterRoute);
  const roadmap = retained.get('/docs/analytics-engineering');
  const home = retained.get('/');
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/analytics-engineering"[^>]*>([\s\S]*?)<\/a>/g)]
    .map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const sections = ['warehouse-foundations-and-dataset', 'dimensional-modeling-and-history',
    'ingestion-cdc-and-canonical-state', 'transformations-and-dbt-workflows',
    'incremental-refreshes-and-backfills', 'quality-observability-and-publication',
    'semantic-metrics-and-consumption', 'production-architecture-and-performance'];
  const worked = sections.map(slug => retained.get('/docs/analytics-engineering/' + slug));
  const assertions = {
    routeCount: routes.length === 164,
    chapterTitle: chapter.includes('Consolidation and Mocks'),
    traceCoverage: Array.from({ length: 32 }, (_, i) => 'L' + String(i + 1).padStart(2, '0') + '.').every(id => worked.some(html => html.includes(id))),
    workedTraceSections: worked.every(html => ['Worked explanation', 'Verified output', 'Common trap', 'Interview follow-up'].every(label => html.includes(label))),
    moduleInterviewAnswers: worked.every(html => html.includes('Q1.') && html.includes('Q8.') && html.includes('Practice tasks')),
    completeFixture: worked[0].includes('Complete supplied raw-change fixture') && worked[0].includes('o1-extra-field') && worked[0].includes('bad-b'),
    historicalModel: worked[1].includes('Exact model SELECT executed') && worked[1].includes('LEAD') && worked[1].includes('customer_sk'),
    cdcEvidence: worked[2].includes('o2_current_fact_count') && worked[2].includes('o2-old-again'),
    toolBoundary: worked[3].includes('No dbt engine or adapter runs') && worked[3].includes('Illustrative dbt SQL'),
    refreshCounterexample: worked[4].includes('2700') && worked[4].includes('3200') && worked[4].includes('skipped_delivery_ids'),
    recoveryBoundary: worked[5].includes('last_good_rows_unchanged') && worked[5].includes('not a process-kill, power-loss or concurrent-reader experiment'),
    metricResult: worked[6].includes('541.666667') && worked[6].includes('472.222222'),
    actualPlanEvidence: worked[7].includes('probe_tenant_day') && worked[7].includes('measured_scan_or_cost'),
    finalMocks: chapter.includes('Mock A') && chapter.includes('Mock B') && chapter.includes('45 minutes'),
    revisionCoverage: chapter.includes('O30') && chapter.includes('D12') && chapter.includes('Twenty confusable pairs'),
    roadmapLinks: sections.every(slug => roadmap.includes('/docs/analytics-engineering/' + slug)) && roadmap.includes(chapterRoute),
    roadmapEvidence: roadmap.includes('74 checks passed') && roadmap.includes('Authoring status: complete'),
    fullRebuildScope: roadmap.includes('rebuilds full candidate dimensions') && roadmap.includes('not production incremental compute savings'),
    homeCard: cards.some(card => card.includes('10 chapters') && card.includes('4 groups')),
    sidebarGroups: subjectMeta.pages.length === 5 && worked.every(html => html.includes('Warehouse Foundations') && html.includes('Refreshes') && html.includes('Operations')),
    sourceContainsSearchFilter: (await readFile(path.join(site, 'components/search-dialog.tsx'), 'utf8')).includes("value: 'analytics-engineering'"),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const missingResponse = await fetch(origin + '/docs/analytics-engineering/no-such-chapter', { signal: AbortSignal.timeout(20000) });
  assert.equal(missingResponse.status, 404);
  await missingResponse.text();
  const search = {};
  for (const [tag, query, expected] of [
    ['analytics-engineering', 'Warehouse', '/docs/analytics-engineering/warehouse-foundations-and-dataset'],
    ['analytics-engineering', 'History', '/docs/analytics-engineering/dimensional-modeling-and-history'],
    ['analytics-engineering', 'CDC', '/docs/analytics-engineering/ingestion-cdc-and-canonical-state'],
    ['analytics-engineering', 'dbt', '/docs/analytics-engineering/transformations-and-dbt-workflows'],
    ['analytics-engineering', 'Backfills', '/docs/analytics-engineering/incremental-refreshes-and-backfills'],
    ['analytics-engineering', 'Quality', '/docs/analytics-engineering/quality-observability-and-publication'],
    ['analytics-engineering', 'Metrics', '/docs/analytics-engineering/semantic-metrics-and-consumption'],
    ['analytics-engineering', 'Performance', '/docs/analytics-engineering/production-architecture-and-performance'],
    ['analytics-engineering', 'Mocks', chapterRoute],
    ['product-casebook', 'Canary', '/docs/product-casebook/experiments-ai-and-launch-decisions'],
    ['probability-statistics', 'Wilson', '/docs/probability-statistics/estimation-and-confidence-intervals'],
    ['sql-interview', 'Session', '/docs/sql-interview/windows-and-time-series'],
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
  evidence = { verified_date: '2026-10-21', node: process.version, port,
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
