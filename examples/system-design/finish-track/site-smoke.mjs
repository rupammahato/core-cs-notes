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
const deadline = AbortSignal.timeout(90000);
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
  console.log('Preview ready on owned loopback port ' + port);
  const origin = 'http://127.0.0.1:' + port;
  const chapterUrl = '/docs/system-design/analytics-event-pipeline';
  const catalogue = JSON.parse(await readFile(new URL('../../resume-skills/module-29-consolidation/module-catalogue.json', import.meta.url), 'utf8'));
  const syllabus = JSON.parse(await readFile(new URL('../roadmap/syllabus.json', import.meta.url), 'utf8'));
  const available = syllabus.filter(entry => entry.status === 'Available');
  const routes = ['/', '/docs/dsa', '/docs/oop', '/docs/os', '/docs/dbms', '/docs/cn', '/docs/resume-skills', ...catalogue.map(entry => entry.route), '/docs/resume-skills/consolidation-interview-drills', '/docs/system-design', ...available.map(entry => '/docs/system-design/' + entry.slug)];
  assert.equal(new Set(routes).size, routes.length);
  const pages = [];
  // Bound parallel HTML decoding instead of loading every long handbook at once.
  for (let offset = 0; offset < routes.length; offset += 6) {
    pages.push(...await Promise.all(routes.slice(offset, offset + 6).map(async route => {
    const response = await fetch(origin + route, { signal: AbortSignal.any([deadline, AbortSignal.timeout(20000)]) });
    assert.equal(response.status, 200, route);
    return { route, status: response.status, html: await response.text() };
    })));
    console.log('Routes checked: ' + pages.length + '/' + routes.length);
  }
  const chapter = pages.find(page => page.route === chapterUrl).html;
  const chapterText = chapter.replace(/<[^>]+>/g, '');
  const roadmap = pages.find(page => page.route === '/docs/system-design').html;
  const home = pages.find(page => page.route === '/').html;
  const cards = [...home.matchAll(/<a\b[^>]*href="\/docs\/system-design"[^>]*>([\s\S]*?)<\/a>/g)].map(match => match[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' '));
  const revisionUrl = '/docs/system-design/consolidation';
  const revision = pages.find(page => page.route === revisionUrl).html;
  const predecessor = pages.find(page => page.route === '/docs/system-design/multi-tenant-rag').html;
  const assertions = {
    analyticsTitle: chapter.includes('S13: Analytics Event Pipeline and Dashboard'),
    analyticsEvidence: chapter.includes('78 local checks passed') && chapter.includes('historical_inclusion_decisions_reused') && chapter.includes('Q30.'),
    revisionTitle: revision.includes('Consolidation and Design Mocks'),
    revisionBank: revision.includes('Q01.') && revision.includes('Q60.') && revision.includes('T24.'),
    revisionBoundaries: revision.includes('recorded local assertions') && revision.includes('automatically_graded') && revision.includes('It is not your score'),
    architecture: chapter.includes('Smallest architecture') && chapter.includes('45-minute mock'),
    predecessor: predecessor.includes(chapterUrl),
    analyticsFinish: chapter.includes(revisionUrl),
    groups: chapter.includes('Worked Systems') && revision.includes('Revision'),
    roadmapLinks: roadmap.includes(chapterUrl) && roadmap.includes(revisionUrl),
    allFoundations: roadmap.includes('all five foundations authored'),
    allPublished: available.length === 20 && syllabus.every(entry => entry.status === 'Available'),
    completion: roadmap.includes('No planned architecture teaching chapter remains unfinished.'),
    homeCard: cards.some(card => card.includes('System Design') && card.includes('21 chapters') && card.includes('3 groups')),
    bankRetained: roadmap.includes('Q01') && roadmap.includes('Q60'),
  };
  assert.ok(Object.values(assertions).every(Boolean), JSON.stringify(assertions));
  console.log('Navigation/content assertions passed');
  const searchEvidence = {};
  for (const [tag, query, expected] of [['system-design', 'Analytics', chapterUrl], ['system-design', 'Consolidation', revisionUrl], ['resume-skills', 'Consolidation', '/docs/resume-skills/consolidation-interview-drills']]) {
    const response = await fetch(origin + '/api/search?query=' + encodeURIComponent(query) + '&tag=' + tag, { signal: AbortSignal.any([deadline, AbortSignal.timeout(30000)]) });
    assert.equal(response.status, 200);
    const results = await response.json();
    assert.ok(results.length > 0 && results.some(item => item.url.split('#')[0] === expected));
    assert.ok(results.every(item => item.url === '/docs/' + tag || item.url.startsWith('/docs/' + tag + '/') || item.url.startsWith('/docs/' + tag + '#')));
    searchEvidence[tag+':'+query] = { status: response.status, results: results.length, indexed: true, scoped: true };
    console.log('Scoped search passed: ' + tag);
  }
  evidence = { port, routes: pages.map(({ route, status }) => ({ route, status })), assertions, search: searchEvidence };
} finally {
  clearTimeout(timer);
  if (child.exitCode === null && child.signalCode === null) { const exited = once(child, 'exit'); child.kill(); await exited; }
  console.log('Owned preview process closed');
}
evidence.temporaryServerClosed = true;
await writeFile(outputPath, JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence));
