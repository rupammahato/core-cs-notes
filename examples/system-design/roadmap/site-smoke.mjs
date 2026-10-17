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
  const chapterUrl = '/docs/system-design';
  const catalogue = JSON.parse(await readFile(new URL('../../resume-skills/module-29-consolidation/module-catalogue.json', import.meta.url), 'utf8'));
  const routes = ['/', '/docs/dsa', '/docs/oop', '/docs/os', '/docs/dbms', '/docs/cn', '/docs/resume-skills', ...catalogue.map(entry => entry.route), '/docs/resume-skills/consolidation-interview-drills', chapterUrl];
  assert.equal(new Set(routes).size, 38);
  const pages = await Promise.all(routes.map(async route => {
    const response = await fetch(origin + route, { signal: AbortSignal.timeout(20000) });
    assert.equal(response.status, 200, route);
    return { route, status: response.status, html: await response.text() };
  }));
  const chapter = pages.find(page => page.route === chapterUrl).html;
  const home = pages.find(page => page.route === '/').html;
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/system-design"[^>]*>([\s\S]*?)<\/a>/g)].map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const assertions = {
    roadmapTitle: chapter.includes('Master Roadmap') && chapter.includes('System Design'),
    bank: chapter.includes('Q01') && chapter.includes('Q60') && chapter.includes('Resume-specific architecture questions'),
    labels: chapter.includes('A0') && chapter.includes('A4') && chapter.includes('S0') && chapter.includes('S13'),
    statusBoundary: chapter.includes('Only this roadmap is authored') && chapter.includes('not yet implemented in this companion'),
    prerequisites: chapter.includes('Requires in this track') && chapter.includes('Numeric module / part'),
    computedEstimates: chapter.includes('77') && chapter.includes('105 active hours'),
    next: chapter.includes('Next: A0') && chapter.includes('How to approach a design question'),
    homeCard: cards.some(card => card.includes('System Design') && card.includes('1 chapter') && card.includes('0 groups')),
    resumeRoadmapLink: pages.find(page => page.route === '/docs/resume-skills').html.includes(chapterUrl),
    noFutureLink: !chapter.includes('href="/docs/system-design/design-method-estimation"'),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  const future = await fetch(origin + '/docs/system-design/design-method-estimation');
  assert.equal(future.status, 404);
  const searchEvidence = {};
  for (const [tag, query, expected] of [['system-design', 'reservation', chapterUrl], ['resume-skills', 'Consolidation', '/docs/resume-skills/consolidation-interview-drills']]) {
    const response = await fetch(origin + '/api/search?query=' + encodeURIComponent(query) + '&tag=' + tag);
    assert.equal(response.status, 200);
    const results = await response.json();
    assert.ok(results.length > 0 && results.some(item => item.url.split('#')[0] === expected));
    assert.ok(results.every(item => item.url === '/docs/' + tag || item.url.startsWith('/docs/' + tag + '/') || item.url.startsWith('/docs/' + tag + '#')));
    searchEvidence[tag] = { status: response.status, results: results.length, indexed: true, scoped: true };
  }
  evidence = { port, routes: pages.map(({ route, status }) => ({ route, status })), assertions, futureRouteStatus: future.status, search: searchEvidence };
} finally {
  clearTimeout(timer);
  if (child.exitCode === null && child.signalCode === null) { const exited = once(child, 'exit'); child.kill(); await exited; }
}
evidence.temporaryServerClosed = true;
await writeFile(outputPath, JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence));
