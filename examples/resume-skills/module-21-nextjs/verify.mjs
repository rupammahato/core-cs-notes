import assert from 'node:assert/strict';
import { createServer, connect } from 'node:net';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import path from 'node:path';
import { chromium } from 'playwright-core';
import { startOrigin } from './origin.mjs';

const base = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const checks = [], observations = {}, pageErrors = [];
const check = (group, name, condition) => {
  assert.ok(condition, name); checks.push({ group, name, passed: true }); console.log(`PASS ${group}: ${name}`);
};
const until = async predicate => {
  const deadline = Date.now() + 15000;
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error('Observation deadline');
    await new Promise(resolve => setTimeout(resolve, 20));
  }
};
const extract = (html, id) => {
  const match = html.match(new RegExp(`data-testid="${id}"[^>]*>([\\s\\S]*?)</(?:p|output)>`));
  assert.ok(match, id);
  return match[1].replace(/<!--.*?-->/g, '').replaceAll('&quot;', '"').replaceAll('&amp;', '&');
};
const walk = directory => readdirSync(directory, { withFileTypes: true }).flatMap(entry =>
  entry.isDirectory() ? walk(path.join(directory, entry.name)) : [path.join(directory, entry.name)]);
const origin = await startOrigin();
const probe = createServer(); probe.listen(0, '127.0.0.1'); await once(probe, 'listening');
const port = probe.address().port; await new Promise(resolve => probe.close(resolve));
const privateMarker = 'M21_SYNTHETIC_SERVER_MARKER_5dc1';
const controlKey = 'M21_LOCAL_TEST_CONTROL_9ad2';
const env = { ...process.env, NEXT_TELEMETRY_DISABLED: '1', M21_ORIGIN: origin.url,
  M21_PRIVATE_MARKER: privateMarker, M21_CONTROL_KEY: controlKey };
const cli = path.join(base, 'node_modules/next/dist/bin/next');
let child, browser, buildChild, serverLog = '', buildLog = '', proof;
const url = `http://127.0.0.1:${port}`;
const http = async (route, options) => {
  const response = await fetch(url + route, { ...options, signal: AbortSignal.timeout(20000) });
  return { response, text: await response.text() };
};
try {
  buildChild = spawn(process.execPath, [cli, 'build'], { cwd: base, env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  buildChild.stdout.on('data', data => { buildLog += data; });
  buildChild.stderr.on('data', data => { buildLog += data; });
  const [code] = await once(buildChild, 'exit');
  writeFileSync(path.join(base, 'fixture-build-output.txt'), buildLog);
  assert.equal(code, 0, buildLog);
  check('build', 'next14_production_build_and_types_pass', true);
  const manifest = JSON.parse(readFileSync(path.join(base, '.next/prerender-manifest.json')));
  check('build', 'public_topic_paths_are_prebuilt', !!manifest.routes['/catalog/node'] && !!manifest.routes['/catalog/react']);
  check('build', 'cookie_dashboard_is_not_prerendered', !manifest.routes['/dashboard']);
  check('build', 'isr_manifest_has_one_second_revalidation', manifest.routes['/isr'].initialRevalidateSeconds === 1);
  observations.build = { next: require('next/package.json').version, prebuiltTopics: ['/catalog/node', '/catalog/react'],
    dashboardPrerendered: !!manifest.routes['/dashboard'], isrRevalidateSeconds: manifest.routes['/isr'].initialRevalidateSeconds };
  child = spawn(process.execPath, [cli, 'start', '-H', '127.0.0.1', '-p', String(port)],
    { cwd: base, env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Next readiness deadline')), 20000);
    child.stdout.on('data', data => { serverLog += data; if (serverLog.includes('Ready in')) { clearTimeout(timer); resolve(); } });
    child.stderr.on('data', data => { serverLog += data; });
    child.once('error', error => { clearTimeout(timer); reject(error); });
    child.once('exit', code => { clearTimeout(timer); reject(new Error('Next exited: ' + code)); });
  });
  const home = await http('/');
  check('rendering', 'initial_html_contains_server_topics', home.response.status === 200 && home.text.includes('Server-rendered topics') && home.text.includes('Node.js'));
  check('rendering', 'client_component_has_initial_html_preview', home.text.includes('HTML preview') && home.text.replace(/<!--.*?-->/g, '').includes('Increment home counter'));
  check('boundary', 'private_marker_not_in_document_or_rsc_props', !home.text.includes(privateMarker) && home.text.includes('Server configured:'));
  const jsFiles = walk(path.join(base, '.next/static')).filter(file => file.endsWith('.js'));
  check('boundary', 'private_marker_absent_from_all_browser_javascript', jsFiles.length > 0 && jsFiles.every(file => !readFileSync(file, 'utf8').includes(privateMarker)));
  const staticA = await http('/catalog/node'), staticB = await http('/catalog/node');
  observations.static = { first: extract(staticA.text, 'static-stamp'), second: extract(staticB.text, 'static-stamp') };
  check('rendering', 'prebuilt_topic_stamp_reused_across_requests', observations.static.first === observations.static.second);
  check('routing', 'unknown_prebuilt_topic_returns_404', (await http('/catalog/unknown')).response.status === 404);
  const visitorA = await http('/dashboard', { headers: { Cookie: 'demo_label=Ada' } });
  const visitorB = await http('/dashboard', { headers: { Cookie: 'demo_label=Lin' } });
  observations.dynamic = { labels: [extract(visitorA.text, 'visitor'), extract(visitorB.text, 'visitor')],
    stampsDiffer: extract(visitorA.text, 'dynamic-stamp') !== extract(visitorB.text, 'dynamic-stamp') };
  check('rendering', 'request_cookie_changes_display_data', observations.dynamic.labels[0].includes('Ada') && observations.dynamic.labels[1].includes('Lin'));
  check('rendering', 'dynamic_render_stamp_changes_between_requests', observations.dynamic.stampsDiffer);
  check('middleware', 'dashboard_matcher_adds_response_header', visitorA.response.headers.get('x-m21-middleware') === 'seen');
  const topic = await http('/api/topics/node');
  check('api', 'route_handler_returns_valid_topic', topic.response.status === 200 && JSON.parse(topic.text).title === 'Node.js');
  check('api', 'route_handler_explicitly_disables_http_caching', topic.response.headers.get('cache-control') === 'no-store');
  check('middleware', 'api_outside_matcher_still_runs', topic.response.headers.get('x-m21-middleware') === null && topic.response.status === 200);
  check('api', 'route_handler_unknown_resource_is_404', (await http('/api/topics/unknown')).response.status === 404);
  check('api', 'route_handler_unsupported_method_is_405', (await http('/api/topics/node', { method: 'POST' })).response.status === 405);
  const jsonPost = value => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
  const echo = await http('/api/echo', jsonPost({ message: ' hello ' }));
  check('api', 'app_post_parses_and_trims_valid_json', echo.response.status === 200 && JSON.parse(echo.text).message === 'hello' && JSON.parse(echo.text).persisted === false);
  check('api', 'app_post_rejects_wrong_content_type', (await http('/api/echo', { method: 'POST', body: 'hello' })).response.status === 415);
  check('api', 'app_post_rejects_malformed_json', (await http('/api/echo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' })).response.status === 400);
  for (const [name, value] of [['blank', { message: ' ' }], ['wrong_type', { message: 1 }], ['extra_fields', { message: 'ok', role: 'admin' }], ['oversized_field', { message: 'x'.repeat(81) }]]) {
    check('api', `app_post_rejects_${name}`, (await http('/api/echo', jsonPost(value))).response.status === 422);
  }
  const legacy = await http('/api/legacy-echo', jsonPost({ message: ' hello ' }));
  check('pages_api', 'pages_handler_has_same_valid_contract', legacy.response.status === 200 && legacy.text === echo.text);
  const legacyGet = await http('/api/legacy-echo');
  check('pages_api', 'pages_handler_returns_405_and_allow', legacyGet.response.status === 405 && legacyGet.response.headers.get('allow') === 'POST');
  check('pages_api', 'pages_handler_validates_runtime_body', (await http('/api/legacy-echo', jsonPost({ message: false }))).response.status === 422);
  check('pages_api', 'pages_parser_rejects_malformed_json', (await http('/api/legacy-echo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' })).response.status === 400);
  check('pages_api', 'pages_parser_enforces_configured_body_limit', (await http('/api/legacy-echo', jsonPost({ message: 'x'.repeat(1500) }))).response.status === 413);
  const cacheRead = async () => JSON.parse(extract((await http('/cache')).text, 'cache-values'));
  const first = await cacheRead();
  const countsFirst = { ...origin.state.counts };
  check('cache', 'duplicate_gets_deduplicated_in_one_render', countsFirst['/items?kind=cached'] === 1 && countsFirst['/items?kind=live'] === 1);
  origin.state.version = 2;
  const second = await cacheRead();
  check('cache', 'force_cache_reuses_public_data_across_requests', second.cachedA === 1 && second.cachedB === 1 && origin.state.counts['/items?kind=cached'] === 1);
  check('cache', 'no_store_refetches_on_next_request', second.liveA === 2 && second.liveB === 2 && origin.state.counts['/items?kind=live'] === 2);
  check('cache', 'invalidation_rejects_missing_fixture_key', (await http('/api/revalidate', { method: 'POST' })).response.status === 403);
  const invalidate = await http('/api/revalidate', { method: 'POST', headers: { 'x-fixture-key': controlKey } });
  check('cache', 'authorized_fixture_control_invalidates_tag', invalidate.response.status === 200);
  const third = await cacheRead();
  check('cache', 'next_visit_refetches_invalidated_tag', third.cachedA === 2 && third.cachedB === 2 && origin.state.counts['/items?kind=cached'] === 2);
  observations.cache = { first, afterOriginChange: second, afterTagInvalidation: third,
    originCalls: { cached: origin.state.counts['/items?kind=cached'], live: origin.state.counts['/items?kind=live'] } };
  origin.state.version = 3;
  const isrValues = [];
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    const value = Number(extract((await http('/isr')).text, 'isr-version')); isrValues.push(value);
    if (value === 3) break;
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  check('cache', 'isr_eventually_serves_revalidated_version', isrValues.at(-1) === 3);
  observations.isr = { versionsObserved: [...new Set(isrValues)], finalVersion: isrValues.at(-1), intervalSeconds: 1 };
  const executablePath = process.env.M21_BROWSER || ['C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
  assert.ok(executablePath, 'Installed Chromium browser or M21_BROWSER required');
  browser = await chromium.launch({ executablePath, headless: true });
  observations.browser = { executable: executablePath, version: browser.version(), headless: true };
  const noJs = await browser.newContext({ javaScriptEnabled: false });
  const noJsPage = await noJs.newPage(); await noJsPage.goto(url);
  check('hydration', 'server_html_readable_without_javascript', await noJsPage.getByRole('heading', { name: 'Placement topic explorer' }).isVisible());
  await noJsPage.getByRole('button', { name: 'Increment home counter' }).click();
  check('hydration', 'html_preview_has_no_client_handler_without_js', await noJsPage.getByRole('region', { name: 'home counter' }).locator('output').textContent() === '0');
  await noJs.close();
  const context = await browser.newContext({ viewport: { width: 1360, height: 1000 } });
  const page = await context.newPage(); page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(url); await page.getByTestId('home counter-hydrated').filter({ hasText: 'Hydrated' }).waitFor();
  await page.getByRole('button', { name: 'Increment home counter' }).click();
  await page.waitForFunction(() => document.querySelector('output')?.textContent === '1');
  check('hydration', 'hydrated_client_handler_updates_existing_screen', await page.getByRole('region', { name: 'home counter' }).locator('output').textContent() === '1');
  await page.getByRole('button', { name: 'Look up topic' }).click();
  await page.getByRole('status').filter({ hasText: 'Node.js' }).waitFor();
  check('browser_api', 'client_island_calls_same_origin_route_handler', await page.getByRole('form', { name: 'Topic lookup' }).getByRole('status').textContent() === 'Node.js');
  await page.getByLabel('Topic slug').fill('unknown'); await page.getByRole('button', { name: 'Look up topic' }).click();
  await page.getByRole('status').filter({ hasText: 'Topic unavailable' }).waitFor();
  check('browser_api', 'client_island_renders_api_failure', await page.getByRole('form', { name: 'Topic lookup' }).getByRole('status').textContent() === 'Topic unavailable');
  const desktop = await page.getByTestId('cards').evaluate(element => getComputedStyle(element).gridTemplateColumns);
  check('tailwind', 'compiled_md_grid_has_two_desktop_columns', desktop.split(' ').length === 2);
  await page.screenshot({ path: path.join(base, 'browser-desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  const mobile = await page.getByTestId('cards').evaluate(element => getComputedStyle(element).gridTemplateColumns);
  check('tailwind', 'base_grid_has_one_mobile_column', mobile.split(' ').length === 1);
  check('tailwind', 'mobile_document_has_no_horizontal_overflow', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({ path: path.join(base, 'browser-mobile.png'), fullPage: true });
  observations.layout = { desktopColumns: desktop, mobileColumns: mobile, widths: [1360, 390] };
  await page.goto(url + '/dashboard'); await page.getByTestId('layout counter-hydrated').filter({ hasText: 'Hydrated' }).waitFor();
  await page.getByRole('button', { name: 'Increment layout counter' }).click();
  await page.waitForFunction(() => document.querySelector('output')?.textContent === '1');
  await page.evaluate(() => { window.m21DocumentMarker = 'same-document'; });
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await page.getByRole('heading', { name: 'Settings', exact: true }).waitFor();
  check('routing', 'link_navigation_keeps_browser_document', await page.evaluate(() => window.m21DocumentMarker) === 'same-document');
  check('routing', 'shared_layout_preserves_client_state', await page.getByRole('region', { name: 'layout counter' }).locator('output').textContent() === '1');
  await page.reload(); await page.getByTestId('layout counter-hydrated').filter({ hasText: 'Hydrated' }).waitFor();
  check('routing', 'full_reload_resets_in_memory_layout_state', await page.getByRole('region', { name: 'layout counter' }).locator('output').textContent() === '0');
  const navigation = page.goto(url + '/stream', { waitUntil: 'domcontentloaded' });
  await until(() => origin.state.held.size > 0);
  await page.getByRole('status').filter({ hasText: 'Waiting for held topic' }).waitFor();
  check('streaming', 'suspense_fallback_visible_before_origin_reply', origin.state.held.size > 0);
  origin.release(); await navigation;
  await page.getByTestId('stream-result').waitFor();
  check('streaming', 'resolved_server_chunk_replaces_fallback', await page.getByTestId('stream-result').textContent() === 'Deferred topic ready');
  await page.goto(url + '/broken'); await page.getByRole('button', { name: 'Try again' }).waitFor();
  check('errors', 'server_failure_reaches_segment_error_boundary', await page.getByRole('main').getByRole('alert').textContent() === 'The server could not load this topic.');
  check('boundary', 'private_failure_details_not_rendered_in_production', !(await page.content()).includes('M21_PRIVATE_FAILURE_DETAILS'));
  origin.state.failing = false; await page.getByRole('button', { name: 'Try again' }).click();
  await page.getByRole('heading', { name: 'Recovered server content' }).waitFor();
  check('errors', 'reset_recovers_after_origin_is_repaired', await page.getByRole('heading', { name: 'Recovered server content' }).isVisible());
  check('browser', 'no_uncaught_page_exceptions', pageErrors.length === 0);
  observations.pageErrors = pageErrors;
  await context.close();
  const counts = Object.fromEntries([...new Set(checks.map(item => item.group))].sort().map(group => [group, checks.filter(item => item.group === group).length]));
  proof = { module: 21, verified_date: '2026-10-15', node: process.version,
    dependencies: Object.fromEntries(['next', 'react', 'react-dom', 'tailwindcss', 'typescript', 'playwright-core'].map(name => [name, require(`${name}/package.json`).version])),
    checks, counts, total: checks.length, observations,
    scope: 'Actual Next.js 14 production build/server, App and Pages APIs, same-origin browser DOM, controlled local origin, cache/tag/ISR, streaming, error recovery and compiled Tailwind 3. No hosted Edge/CDN, real login/database, Server Actions, production deployment or full accessibility/performance audit.' };
} finally {
  if (browser) await browser.close();
  for (const process of [child, buildChild]) {
    if (process && process.exitCode === null && process.signalCode === null) { const exited = once(process, 'exit'); process.kill(); await exited; }
  }
  await origin.close();
  writeFileSync(path.join(base, 'fixture-server-output.txt'), serverLog);
}
const isClosed = port => new Promise(resolve => {
  const socket = connect({ host: '127.0.0.1', port });
  socket.once('connect', () => { socket.destroy(); resolve(false); });
  socket.once('error', () => resolve(true));
});
proof.cleanup = { browser_closed: true, loopback_ports_closed: { [port]: await isClosed(port), [origin.port]: await isClosed(origin.port) }, docker_started: false };
assert.ok(Object.values(proof.cleanup.loopback_ports_closed).every(Boolean));
writeFileSync(path.join(base, 'verification-results.json'), JSON.stringify(proof, null, 2) + '\n');
writeFileSync(path.join(base, 'cleanup-results.json'), JSON.stringify(proof.cleanup, null, 2) + '\n');
console.log(JSON.stringify({ counts: proof.counts, total: proof.total, cleanup: proof.cleanup }));
