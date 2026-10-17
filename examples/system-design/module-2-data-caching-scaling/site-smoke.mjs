import assert from 'node:assert/strict';
import { createServer } from 'node:net';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const [siteRoot, outputPath] = process.argv.slice(2);
const probe = createServer();
probe.listen(0, '127.0.0.1');
await once(probe, 'listening');
const port = probe.address().port;
await new Promise(resolve => probe.close(resolve));
const child = spawn(process.execPath, [path.join(siteRoot, 'node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', String(port)], { cwd: siteRoot, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
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
  const origin = 'http://127.0.0.1:' + port;
  const chapterUrl = '/docs/system-design/data-caching-scaling';
  const catalogue = JSON.parse(await readFile(new URL('../../resume-skills/module-29-consolidation/module-catalogue.json', import.meta.url), 'utf8'));
  const syllabus = JSON.parse(await readFile(new URL('../roadmap/syllabus.json', import.meta.url), 'utf8'));
  const available = syllabus.filter(entry => entry.status === 'Available');
  const routes = ['/', '/docs/dsa', '/docs/oop', '/docs/os', '/docs/dbms', '/docs/cn', '/docs/resume-skills', ...catalogue.map(entry => entry.route), '/docs/resume-skills/consolidation-interview-drills', '/docs/system-design', ...available.map(entry => '/docs/system-design/' + entry.slug)];
  assert.equal(new Set(routes).size, routes.length);
  const pages = await Promise.all(routes.map(async route => {
    const response = await fetch(origin + route, { signal: AbortSignal.timeout(20000) });
    assert.equal(response.status, 200, route);
    return { route, status: response.status, html: await response.text() };
  }));
  const chapter = pages.find(page => page.route === chapterUrl).html;
  const chapterText = chapter.replace(/<[^>]+>/g, '');
  const roadmap = pages.find(page => page.route === '/docs/system-design').html;
  const home = pages.find(page => page.route === '/').html;
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/system-design"[^>]*>([\s\S]*?)<\/a>/g)].map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const assertions = {
    title: chapter.includes('A2: Data, Caching and Scaling'),
    q30: chapter.includes('Q30.'),
    verifiedChecks: chapter.includes('91 local checks passed'),
    exactCode: chapterText.includes('notes_owner_recent') && chapterText.includes('class CacheAside') && chapterText.includes('asyncio.shield'),
    evidence: chapter.includes('sqlite_vm_instructions') && chapter.includes('offset_duplicate_ids') && chapter.includes('invalidation_broadcast'),
    architecture: chapter.includes('Partitioning, sharding and hot tenants') && chapter.includes('Read replicas, failover and lag'),
    scope: chapter.includes('cache is process-local Python memory') && chapter.includes('not a frozen snapshot'),
    next: chapter.includes('Next: A3') && chapter.includes('Reliable workflows and concurrency'),
    foundationGroup: chapter.includes('Foundations'),
    roadmapLink: roadmap.includes(chapterUrl) && roadmap.includes('A0'+String.fromCharCode(0x2013)+'A2 available'),
    predecessor: pages.find(page => page.route === '/docs/system-design/application-architecture-service-boundaries').html.includes(chapterUrl),
    homeCard: cards.some(card => card.includes('System Design') && card.includes((available.length + 1) + ' chapters') && card.includes('1 group')),
    bankRetained: roadmap.includes('Q01') && roadmap.includes('Q60'),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const nextEntry = syllabus.find(entry => entry.label === 'A3');
  const future = await fetch(origin + '/docs/system-design/' + nextEntry.slug);
  assert.equal(future.status, nextEntry.status === 'Available' ? 200 : 404);
  const searchEvidence = {};
  for (const [tag, query, expected] of [['system-design', 'Caching', chapterUrl], ['resume-skills', 'Consolidation', '/docs/resume-skills/consolidation-interview-drills']]) {
    const response = await fetch(origin + '/api/search?query=' + encodeURIComponent(query) + '&tag=' + tag);
    assert.equal(response.status, 200);
    const results = await response.json();
    assert.ok(results.length > 0 && results.some(item => item.url.split('#')[0] === expected));
    assert.ok(results.every(item => item.url === '/docs/' + tag || item.url.startsWith('/docs/' + tag + '/') || item.url.startsWith('/docs/' + tag + '#')));
    searchEvidence[tag] = { status: response.status, results: results.length, indexed: true, scoped: true };
  }
  evidence = { port, routes: pages.map(({ route, status }) => ({ route, status })), assertions, nextRouteStatus: future.status, search: searchEvidence };
} finally {
  clearTimeout(timer);
  if (child.exitCode === null && child.signalCode === null) { const exited = once(child, 'exit'); child.kill(); await exited; }
}
evidence.temporaryServerClosed = true;
await writeFile(outputPath, JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence));
