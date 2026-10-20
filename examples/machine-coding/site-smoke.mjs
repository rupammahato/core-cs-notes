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
  return (await Promise.all(entries.map(entry => entry.isDirectory()
    ? markdownFiles(path.join(directory, entry.name))
    : entry.name.endsWith('.md') ? [path.join(directory, entry.name)] : []))).flat();
}
const files = await markdownFiles(content);
const routes = ['/', ...files.map(file => {
  const parts = path.relative(content, file).split(path.sep);
  const slug = path.basename(file, '.md');
  return '/docs/' + parts[0] + (slug === 'index' ? '' : '/' + slug);
})];
assert.equal(new Set(routes).size, routes.length);
const sections = ['transactional-key-value-store', 'sliding-window-rate-limiter',
  'event-bus-and-callback-lifecycle', 'virtual-time-task-scheduler',
  'vending-machine-and-exact-change', 'meeting-room-booking',
  'in-memory-document-search', 'feature-flag-evaluator'];
const plain = html => html.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&#x27;/g, "'");
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
  const retained = new Map(), results = [];
  for (let offset = 0; offset < routes.length; offset += 4) {
    results.push(...await Promise.all(routes.slice(offset, offset + 4).map(async route => {
      const response = await fetch(origin + route, { signal: AbortSignal.timeout(20000) });
      assert.equal(response.status, 200, route);
      const html = await response.text();
      if (route === '/' || route.startsWith('/docs/machine-coding')) retained.set(route, html);
      return { route, status: response.status };
    })));
    if (results.length % 20 === 0 || results.length === routes.length)
      console.log('Routes checked: ' + results.length + '/' + routes.length);
  }
  const chapterRoute = '/docs/machine-coding/consolidation-and-mocks';
  const chapter = plain(retained.get(chapterRoute));
  const roadmap = retained.get('/docs/machine-coding');
  const method = plain(retained.get('/docs/machine-coding/solving-method-and-test-harness'));
  const worked = sections.map(slug => plain(retained.get('/docs/machine-coding/' + slug)));
  const cards = [...retained.get('/').matchAll(/<a\b[^>]*href="\/docs\/machine-coding"[^>]*>([\s\S]*?)<\/a>/g)]
    .map(match => plain(match[1]).replace(/\s+/g, ' '));
  const subjectMeta = JSON.parse(await readFile(path.join(content, 'machine-coding/meta.json'), 'utf8'));
  const assertions = {
    routeCount: routes.length === 175,
    machineCodingPages: [...retained.keys()].filter(route => route.startsWith('/docs/machine-coding')).length === 11,
    chapterTitle: chapter.includes('Consolidation and Mocks'),
    traceCoverage: Array.from({ length: 32 }, (_, i) => 'T' + String(i + 1).padStart(2, '0') + '.').every(id => worked.some(text => text.includes(id))),
    workedSections: worked.every(text => ['Worked explanation', 'Verified transcript', 'Common trap', 'Interview follow-up'].every(label => text.includes(label))),
    interviewAnswers: worked.every(text => text.includes('Q1.') && text.includes('Q8.') && text.includes('Practice tasks')),
    modelListings: worked.every(text => text.includes('Complete model implementation') && text.includes('class ')),
    parserContract: method.includes('4,096 printable ASCII bytes') && method.includes('Shared support code') && method.includes('std::from_chars'),
    transactionCounterexample: worked[0].includes('A nested commit is still inside its parent'),
    limiterBoundary: worked[1].includes('expires exactly at the boundary'),
    callbackLifecycle: worked[2].includes('Unsubscribe changes the next dispatch') && worked[2].includes('Recursive publish is isolated'),
    schedulerOrdering: worked[3].includes('Time, priority, then insertion order') && worked[3].includes('Cancelled heap entries are skipped'),
    vendingCounterexample: worked[4].includes('Bounded exact change defeats a greedy choice') && worked[4].includes('Impossible change leaves the whole session intact'),
    bookingPreservation: worked[5].includes('A failed move preserves the original reservation'),
    indexReplacement: worked[6].includes('Replacement removes stale postings'),
    versionConflicts: worked[7].includes('Retries and conflicting versions differ') && worked[7].includes('non-cryptographic'),
    finalMocks: chapter.includes('Mock A') && chapter.includes('Mock B') && chapter.includes('60 minutes') && chapter.includes('Scoring rubric'),
    oralCoverage: chapter.includes('O01.') && chapter.includes('O30.') && chapter.includes('Ten confusable pairs'),
    roadmapLinks: [...sections, 'solving-method-and-test-harness', 'consolidation-and-mocks'].every(slug => roadmap.includes('/docs/machine-coding/' + slug)),
    evidenceAndScope: plain(roadmap).includes('57 verification groups passed') && plain(roadmap).includes('No performance benchmark'),
    homeCard: cards.some(card => card.includes('11 chapters') && card.includes('4 groups')),
    sidebarGroups: subjectMeta.pages.length === 5 && worked.every(text => ['Method & State', 'Callbacks & Scheduling', 'Worked Applications'].every(label => text.includes(label))),
    searchFilter: (await readFile(path.join(site, 'components/search-dialog.tsx'), 'utf8')).includes("value: 'machine-coding'"),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const missingResponse = await fetch(origin + '/docs/machine-coding/no-such-chapter', { signal: AbortSignal.timeout(20000) });
  assert.equal(missingResponse.status, 404);
  await missingResponse.text();
  const search = {};
  for (const [tag, query, slug] of [
    ['machine-coding', 'Harness', 'solving-method-and-test-harness'],
    ['machine-coding', 'Transactional', 'transactional-key-value-store'],
    ['machine-coding', 'Limiter', 'sliding-window-rate-limiter'],
    ['machine-coding', 'Callback', 'event-bus-and-callback-lifecycle'],
    ['machine-coding', 'Scheduler', 'virtual-time-task-scheduler'],
    ['machine-coding', 'Vending', 'vending-machine-and-exact-change'],
    ['machine-coding', 'Meeting', 'meeting-room-booking'],
    ['machine-coding', 'Document', 'in-memory-document-search'],
    ['machine-coding', 'Flag', 'feature-flag-evaluator'],
    ['machine-coding', 'Mocks', 'consolidation-and-mocks'],
    ['analytics-engineering', 'CDC', 'ingestion-cdc-and-canonical-state'],
    ['product-casebook', 'Canary', 'experiments-ai-and-launch-decisions'],
    ['probability-statistics', 'Wilson', 'estimation-and-confidence-intervals'],
    ['sql-interview', 'Session', 'windows-and-time-series'],
    ['product-analytics', 'Confusable', 'consolidation-resume-drills'],
    ['system-design', 'Analytics', 'analytics-event-pipeline'],
    ['resume-skills', 'Consolidation', 'consolidation-interview-drills'],
  ]) {
    const response = await fetch(origin + '/api/search?query=' + encodeURIComponent(query) + '&tag=' + tag,
      { signal: AbortSignal.timeout(30000) });
    assert.equal(response.status, 200);
    const items = await response.json(), expected = '/docs/' + tag + '/' + slug;
    assert.ok(items.length && items.some(item => item.url.split('#')[0] === expected), JSON.stringify({ tag, query, expected, items }));
    assert.ok(items.every(item => item.url.split('#')[0] === '/docs/' + tag || item.url.startsWith('/docs/' + tag + '/')));
    search[tag + ':' + query] = { status: response.status, results: items.length, indexed: true, scoped: true };
    console.log('Scoped search passed: ' + tag + ':' + query);
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
console.log(JSON.stringify({ routesChecked: evidence.routes.length, contentAssertions: Object.keys(evidence.assertions).length,
  scopedSearchQueries: Object.keys(evidence.search).length, temporaryServerClosed: true }));
