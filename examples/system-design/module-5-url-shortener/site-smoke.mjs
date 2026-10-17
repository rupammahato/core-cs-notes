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
  const chapterUrl = '/docs/system-design/url-shortener';
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
    title: chapter.includes('S0: URL Shortener'),
    q30: chapter.includes('Q30.'),
    verifiedChecks: chapter.includes('118 local checks passed'),
    exactCode: chapterText.includes('ON CONFLICT(code) DO NOTHING') && chapterText.includes('class Service') && chapterText.includes('secrets.choice'),
    evidence: chapter.includes('destination_requests_made') && chapter.includes('forced_collision_count') && chapter.includes('unique_human_visits_measured'),
    architecture: chapter.includes('Smallest architecture and end-to-end traces') && chapter.includes('Growth stages: add a component'),
    scope: chapter.includes('No external destination request is made') && chapter.includes('not immediate global revocation'),
    next: chapter.includes('Next: S1') && chapter.includes('Rate limiter'),
    workedGroup: chapter.includes('Worked Systems'),
    roadmapLink: roadmap.includes(chapterUrl) && roadmap.includes('S0 available'),
    allFoundations: roadmap.includes('all five foundations authored'),
    predecessor: pages.find(page => page.route === '/docs/system-design/secure-observable-operations').html.includes(chapterUrl),
    homeCard: cards.some(card => card.includes('System Design') && card.includes((available.length + 1) + ' chapters') && card.includes('2 groups')),
    bankRetained: roadmap.includes('Q01') && roadmap.includes('Q60'),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const nextEntry = syllabus.find(entry => entry.label === 'S1');
  const future = await fetch(origin + '/docs/system-design/' + nextEntry.slug);
  assert.equal(future.status, nextEntry.status === 'Available' ? 200 : 404);
  const searchEvidence = {};
  for (const [tag, query, expected] of [['system-design', 'Shortener', chapterUrl], ['resume-skills', 'Consolidation', '/docs/resume-skills/consolidation-interview-drills']]) {
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
