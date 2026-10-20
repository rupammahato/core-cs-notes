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
const subjectMeta = JSON.parse(await readFile(path.join(content, 'product-casebook/meta.json'), 'utf8'));
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
      if (route === '/' || route.startsWith('/docs/product-casebook')) retained.set(route, html);
      return { route, status: response.status };
    })));
    if (results.length % 16 === 0 || results.length === routes.length)
      console.log('Routes checked: ' + results.length + '/' + routes.length);
  }
  const chapterRoute = '/docs/product-casebook/consolidation-and-mocks';
  const chapter = retained.get(chapterRoute);
  const roadmap = retained.get('/docs/product-casebook');
  const method = retained.get('/docs/product-casebook/case-method-and-evidence');
  const home = retained.get('/');
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/product-casebook"[^>]*>([\s\S]*?)<\/a>/g)]
    .map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const sections = ['product-sense-and-prioritization', 'metrics-and-root-cause-analysis',
    'growth-activation-and-retention', 'pricing-and-business-models',
    'marketplaces-and-operations', 'experiments-ai-and-launch-decisions'];
  const worked = sections.map(slug => retained.get('/docs/product-casebook/' + slug));
  const assertions = {
    routeCount: routes.length === 154,
    chapterTitle: chapter.includes('Consolidation and Mocks'),
    caseCoverage: Array.from({ length: 18 }, (_, i) => 'C' + String(i + 1).padStart(2, '0') + '.').every(id => worked.some(html => html.includes(id))),
    completeCaseSections: worked.every(html => ['Evidence status and complete fixture inputs', 'Metric and decision contract', 'Verified calculation output', 'Compare options', 'Worked recommendation', 'Engineering and architecture implications'].every(label => html.includes(label))),
    answeredFollowUps: worked.every(html => html.includes('F1.') && html.includes('F4.') && html.includes('Practice task')),
    methodFramework: method.includes('evidence ledger') && method.includes('Metric') && method.includes('decision and delivery memo'),
    finalMocks: chapter.includes('Mock A') && chapter.includes('Mock B') && chapter.includes('45 minutes'),
    revisionCoverage: chapter.includes('O30') && chapter.includes('D12') && chapter.includes('Twenty confusable pairs'),
    metricResults: worked[1].includes('after_standardized_to_before_mix_pct') && worked[1].includes('5000000'),
    growthResults: worked[2].includes('new_revised_mature_retention_pct') && worked[2].includes('supplied_guardrail_passed'),
    pricingResults: worked[3].includes('2780') && worked[3].includes('lifetime_value_cents'),
    operationsResults: worked[4].includes('fluid_backlog_after_busy_period') && worked[4].includes('890000'),
    launchResults: worked[5].includes('canary_bad_unique_requests') && worked[5].includes('assignment_verified'),
    scopeBoundaries: roadmap.includes('does not grade product judgment automatically') && worked.every(html => html.includes('does not verify the source labels')),
    roadmapLinks: sections.every(slug => roadmap.includes('/docs/product-casebook/' + slug)) && roadmap.includes(chapterRoute),
    roadmapEvidence: roadmap.includes('41 checks passed') && roadmap.includes('Authoring status: complete'),
    homeCard: cards.some(card => card.includes('9 chapters') && card.includes('4 groups')),
    sidebarGroups: subjectMeta.pages.length === 5 && worked.every(html => html.includes('Method') && html.includes('Operations') && html.includes('Revision')),
    sourceContainsSearchFilter: (await readFile(path.join(site, 'components/search-dialog.tsx'), 'utf8')).includes("value: 'product-casebook'"),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const missingResponse = await fetch(origin + '/docs/product-casebook/no-such-chapter', { signal: AbortSignal.timeout(20000) });
  assert.equal(missingResponse.status, 404);
  await missingResponse.text();
  const search = {};
  for (const [tag, query, expected] of [
    ['product-casebook', 'Evidence', '/docs/product-casebook/case-method-and-evidence'],
    ['product-casebook', 'Interrupted', '/docs/product-casebook/product-sense-and-prioritization'],
    ['product-casebook', 'Checkout', '/docs/product-casebook/metrics-and-root-cause-analysis'],
    ['product-casebook', 'Retention', '/docs/product-casebook/growth-activation-and-retention'],
    ['product-casebook', 'Credits', '/docs/product-casebook/pricing-and-business-models'],
    ['product-casebook', 'Marketplace', '/docs/product-casebook/marketplaces-and-operations'],
    ['product-casebook', 'Canary', '/docs/product-casebook/experiments-ai-and-launch-decisions'],
    ['product-casebook', 'Mocks', chapterRoute],
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
