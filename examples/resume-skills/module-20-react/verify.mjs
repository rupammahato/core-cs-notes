import assert from 'node:assert/strict';
import { readFile, writeFile, access } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createConnection } from 'node:net';
import { chromium } from 'playwright-core';
import { createFixtureServer } from './server.mjs';

const checks = [], observations = {}, pageErrors = [];
async function check(group, name, fn) { await fn(); checks.push({ group, name, passed: true }); console.log('PASS ' + group + '/' + name); }
async function until(fn) {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) { if (fn()) return; await new Promise(resolve => setTimeout(resolve, 10)); }
  throw new Error('Fixture condition deadline');
}
const candidates = [process.env.M20_BROWSER, 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].filter(Boolean);
let executablePath;
for (const path of candidates) { try { await access(path); executablePath = path; break; } catch {} }
if (!executablePath) throw new Error('Set M20_BROWSER to a Chromium-based browser executable');
const fixture = await createFixtureServer();
let browser;
const base = 'http://127.0.0.1:' + fixture.port;
try {
  browser = await chromium.launch({ executablePath, headless: true });
  observations.browser = { version: browser.version(), executable: executablePath, headless: true };
  const context = await browser.newContext({ viewport: { width: 1360, height: 1000 } });
  async function pageAt(query = '') {
    const page = await context.newPage();
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.goto(base + '/' + query);
    await page.getByRole('heading', { name: 'React fundamentals lab' }).waitFor();
    await page.waitForFunction(() => window.M20?.activeSubscriptions() === 1);
    return page;
  }
  const page = await pageAt();
  async function text(id, expected, target = page) {
    await target.waitForFunction(([id, value]) => document.querySelector('[data-testid="' + id + '"]')?.textContent === value, [id, expected]);
  }
  const events = type => page.evaluate(type => window.M20.events.filter(event => event.type === type), type);
  await check('accessibility', 'document_language_and_main_landmark', async () => { assert.equal(await page.locator('html').getAttribute('lang'), 'en'); assert.equal(await page.getByRole('main').count(), 1); });
  await page.getByRole('button', { name: 'Three replacements', exact: true }).click();
  await check('state', 'three_snapshot_replacements_increment_once', async () => text('count', '1'));
  observations.snapshot = (await events('snapshot'))[0];
  await check('state', 'setter_does_not_rewrite_current_handler_snapshot', () => assert.deepEqual(observations.snapshot, { type: 'snapshot', before: 0, afterInHandler: 0 }));
  await page.getByRole('button', { name: 'Reset count', exact: true }).click(); await text('count', '0');
  await page.getByRole('button', { name: 'Capture callback', exact: true }).click();
  await page.getByRole('button', { name: 'Three updaters', exact: true }).click();
  await check('state', 'three_pure_updaters_increment_three_times', () => text('count', '3'));
  await page.getByRole('button', { name: 'Run captured callback', exact: true }).click();
  await check('state', 'stored_closure_keeps_its_render_snapshot', () => text('captured', '0'));
  await page.getByRole('button', { name: 'Increment ref', exact: true }).click();
  await check('state', 'ref_mutation_does_not_publish_ui_state', () => text('published-ref', '0'));
  await page.getByRole('button', { name: 'Publish ref', exact: true }).click();
  await check('state', 'event_can_read_and_publish_current_ref', () => text('published-ref', '1'));
  await page.getByRole('button', { name: 'Update nested theme', exact: true }).click();
  await check('state', 'immutable_update_changes_rendered_nested_value', () => text('profile', 'Rupam: dark'));
  observations.immutable = (await events('immutable-update'))[0];
  await check('state', 'previous_object_and_nested_identity_remain_distinct', () => assert.deepEqual(observations.immutable, { type: 'immutable-update', previousTheme: 'light', sameObject: false, sameNested: false }));

  await page.getByLabel('Alpha draft', { exact: true }).fill('Alpha edited');
  const originalInput = await page.getByLabel('Alpha draft', { exact: true }).elementHandle();
  await page.getByRole('button', { name: 'Reverse rows', exact: true }).click();
  await check('identity', 'stable_key_keeps_draft_with_logical_item', async () => assert.equal(await page.getByLabel('Alpha draft', { exact: true }).inputValue(), 'Alpha edited'));
  await check('identity', 'stable_reorder_reuses_the_input_dom_node', async () => assert.ok(await page.evaluate(element => element === document.getElementById('draft-stable-a'), originalInput)));
  await page.getByLabel('Key strategy', { exact: true }).selectOption('index');
  await page.getByLabel('Alpha draft', { exact: true }).fill('Alpha edited');
  await page.getByRole('button', { name: 'Reverse rows', exact: true }).click();
  observations.indexCounterexample = { alpha: await page.getByLabel('Alpha draft', { exact: true }).inputValue(), beta: await page.getByLabel('Beta draft', { exact: true }).inputValue() };
  await check('identity', 'index_counterexample_misassigns_draft_after_reorder', () => assert.deepEqual(observations.indexCounterexample, { alpha: 'Beta', beta: 'Alpha edited' }));
  await page.getByLabel('Ada note', { exact: true }).fill('Ada owned');
  await page.getByRole('button', { name: 'Unrelated parent update', exact: true }).click();
  await check('identity', 'same_type_position_key_preserves_editor_state', async () => assert.equal(await page.getByLabel('Ada note', { exact: true }).inputValue(), 'Ada owned'));
  await page.getByRole('button', { name: 'Switch person', exact: true }).click();
  await check('identity', 'new_key_resets_editor_state', async () => assert.equal(await page.getByLabel('Lin note', { exact: true }).inputValue(), ''));
  await page.getByLabel('Lin note', { exact: true }).fill('Lin owned');
  await page.getByRole('button', { name: 'Switch person', exact: true }).click();
  await check('identity', 'previously_unmounted_key_does_not_cache_old_state', async () => assert.equal(await page.getByLabel('Ada note', { exact: true }).inputValue(), ''));

  await check('effects', 'ordinary_mount_has_one_active_subscription', async () => { assert.equal((await events('subscription-setup')).length, 1); assert.equal(await page.evaluate(() => window.M20.activeSubscriptions()), 1); });
  await page.getByRole('button', { name: 'Same dependency update', exact: true }).click();
  await check('effects', 'unchanged_dependency_does_not_reconnect', async () => assert.equal((await events('subscription-setup')).length, 1));
  await page.getByLabel('Subscription topic', { exact: true }).selectOption('node');
  await page.waitForFunction(() => window.M20.events.some(event => event.type === 'subscription-setup' && event.topic === 'node'));
  observations.effectTransition = await page.evaluate(() => window.M20.events.filter(event => event.type.startsWith('subscription-')));
  await check('effects', 'changed_dependency_cleans_old_before_new_setup', () => assert.deepEqual(observations.effectTransition, [
    { type: 'subscription-setup', topic: 'react' }, { type: 'subscription-cleanup', topic: 'react' }, { type: 'subscription-setup', topic: 'node' },
  ]));
  await page.getByRole('button', { name: 'Unmount subscription', exact: true }).click();
  await check('effects', 'conditional_unmount_releases_external_resource', async () => { await page.waitForFunction(() => window.M20.activeSubscriptions() === 0); });
  await page.getByRole('button', { name: 'Mount subscription', exact: true }).click();
  await check('effects', 'remount_creates_one_new_subscription', async () => { await page.waitForFunction(() => window.M20.activeSubscriptions() === 1); assert.equal((await events('subscription-setup')).length, 3); });

  await page.getByLabel('Display name', { exact: true }).fill('   ');
  await page.getByRole('button', { name: 'Save name', exact: true }).click();
  await check('forms', 'blank_trimmed_value_has_visible_error', async () => { await page.getByRole('alert').filter({ hasText: 'Enter a display name.' }).waitFor(); });
  await check('accessibility', 'invalid_input_links_its_error', async () => { assert.equal(await page.getByLabel('Display name', { exact: true }).getAttribute('aria-invalid'), 'true'); assert.equal(await page.getByLabel('Display name', { exact: true }).getAttribute('aria-describedby'), 'name-error'); });
  await page.getByLabel('Display name', { exact: true }).fill('  Rupam  ');
  await check('forms', 'controlled_field_reflects_typed_value', async () => assert.equal(await page.getByLabel('Display name', { exact: true }).inputValue(), '  Rupam  '));
  await page.getByLabel('Display name', { exact: true }).press('Enter');
  await check('forms', 'enter_submits_trimmed_value_without_navigation', async () => { await page.getByRole('status').filter({ hasText: 'Saved: Rupam' }).waitFor(); assert.equal(page.url(), base + '/'); });
  await check('forms', 'successful_submit_clears_invalid_state', async () => assert.equal(await page.getByLabel('Display name', { exact: true }).getAttribute('aria-invalid'), 'false'));
  await page.getByLabel('Filter subjects', { exact: true }).fill('node');
  await check('forms', 'derived_filter_and_sibling_count_agree', async () => { await text('subject-count', '1 visible'); assert.deepEqual(await page.getByRole('list', { name: 'Filtered subjects', exact: true }).getByRole('listitem').allTextContents(), ['Node.js']); });
  await page.getByLabel('React only', { exact: true }).check();
  await check('forms', 'controlled_checkbox_combines_with_filter', async () => { assert.ok(await page.getByLabel('React only', { exact: true }).isChecked()); await text('subject-count', '0 visible'); });
  await page.getByRole('button', { name: 'Focus input', exact: true }).click();
  await check('accessibility', 'ref_focus_reaches_named_input', async () => assert.ok(await page.getByLabel('Focus target', { exact: true }).evaluate(element => element === document.activeElement)));
  const replacements = page.getByRole('button', { name: 'Three replacements', exact: true });
  await replacements.focus(); await replacements.press('Space');
  await check('accessibility', 'native_button_supports_keyboard_activation', () => text('count', '4'));

  await page.getByRole('button', { name: 'Toggle context theme', exact: true }).click();
  await check('sharing', 'provider_update_reaches_context_consumer', () => text('context-theme', 'Theme: dark'));
  const memoBefore = (await events('memo-child-commit')).length;
  await page.getByRole('button', { name: 'Memo parent update', exact: true }).click();
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(resolve)));
  await check('sharing', 'memo_skips_child_commit_for_unchanged_props_in_this_run', async () => assert.equal((await events('memo-child-commit')).length, memoBefore));
  await page.getByRole('button', { name: 'Change memo prop', exact: true }).click();
  await page.waitForFunction(() => window.M20.events.some(event => event.type === 'memo-child-commit' && event.label === 'Node'));
  await check('sharing', 'changed_prop_updates_memo_child_and_derived_value', async () => { assert.equal((await events('memo-child-commit')).length, memoBefore + 1); await text('memo-derived', 'Derived: NODE'); });
  await page.getByRole('button', { name: 'Pick Node', exact: true }).click();
  await check('sharing', 'stable_callback_requests_parent_state_update', () => text('picked', 'Picked: 1'));

  const topics = page.getByRole('region', { name: 'API state and cleanup', exact: true });
  async function search(target, query) {
    await target.getByLabel('Topic query', { exact: true }).fill(query);
    await target.getByRole('button', { name: 'Search topics', exact: true }).click();
  }
  await check('api', 'idle_ui_does_not_fetch_before_query', async () => { assert.equal(fixture.requests.length, 0); await topics.getByText('Enter a query.', { exact: true }).waitFor(); });
  await search(topics, 'slow'); await until(() => fixture.heldCount() === 1);
  await check('api', 'held_request_displays_loading_and_busy_state', async () => { await topics.getByText('Loading topics…', { exact: true }).waitFor(); assert.equal(await topics.locator('[aria-live]').getAttribute('aria-busy'), 'true'); });
  await search(topics, 'node'); await topics.getByRole('list', { name: 'Topic results' }).waitFor();
  await check('api', 'successful_http_response_renders_items', async () => assert.deepEqual(await topics.getByRole('listitem').allTextContents(), ['Node.js']));
  await until(() => fixture.events.some(event => event.event === 'client-disconnected' && event.query === 'slow'));
  await check('api', 'query_change_aborts_old_browser_fetch', () => assert.ok(fixture.events.some(event => event.event === 'client-disconnected' && event.query === 'slow')));
  await search(topics, 'empty');
  await check('api', 'empty_success_has_distinct_ui', async () => { await topics.getByText('No topics found.', { exact: true }).waitFor(); });
  await search(topics, 'error');
  await check('api', 'http_503_is_checked_and_rendered_as_error', async () => { await topics.getByRole('alert').filter({ hasText: 'Could not load topics.' }).waitFor(); });
  await topics.getByRole('button', { name: 'Recover fixture API', exact: true }).click();
  await topics.getByRole('button', { name: 'Retry topics', exact: true }).click();
  await check('api', 'retry_uses_current_query_and_recovers', async () => { await topics.getByText('Recovered result', { exact: true }).waitFor(); });
  await search(topics, 'malformed');
  await check('api', 'invalid_success_payload_fails_runtime_contract', async () => { await topics.getByRole('alert').filter({ hasText: 'Could not load topics.' }).waitFor(); });
  await search(topics, 'html');
  await check('api', 'api_text_is_rendered_as_text_not_raw_html', async () => { await topics.getByText('<img src=x onerror=alert(1)>', { exact: true }).waitFor(); assert.equal(await topics.locator('img').count(), 0); });
  await search(topics, 'slow'); await until(() => fixture.heldCount() === 1);
  await topics.getByRole('button', { name: 'Unmount topic panel', exact: true }).click();
  await until(() => fixture.heldCount() === 0);
  await check('api', 'unmount_aborts_pending_request_and_removes_view', async () => assert.equal(await topics.getByLabel('Topic query', { exact: true }).count(), 0));

  const racePage = await pageAt('?ignoreAbort=1');
  const raceTopics = racePage.getByRole('region', { name: 'API state and cleanup', exact: true });
  await search(raceTopics, 'slow'); await until(() => fixture.heldCount() === 1);
  await search(raceTopics, 'fast'); await raceTopics.getByText('Fast result', { exact: true }).waitFor();
  const slowResponse = racePage.waitForResponse(response => response.url().endsWith('/api/topics?q=slow') && response.status() === 200);
  await raceTopics.getByRole('button', { name: 'Release held API reply', exact: true }).click(); await slowResponse;
  await racePage.waitForFunction(() => window.M20.events.some(event => event.type === 'ignored-result' && event.query === 'slow'));
  await check('api', 'inactive_result_is_ignored_even_when_transport_does_not_abort', async () => assert.deepEqual(await raceTopics.getByRole('listitem').allTextContents(), ['Fast result']));
  observations.race = { newer_visible: await raceTopics.getByRole('listitem').allTextContents(),
    events: await racePage.evaluate(() => window.M20.events.filter(event => event.type.startsWith('request-') || event.type === 'ignored-result')) };

  const strictDev = await pageAt('?strict=1');
  const strictEvents = await strictDev.evaluate(() => window.M20.events.filter(event => event.type.startsWith('subscription-')));
  await check('strict', 'development_root_strict_mode_probes_setup_cleanup_setup', () => assert.deepEqual(strictEvents, [
    { type: 'subscription-setup', topic: 'react' }, { type: 'subscription-cleanup', topic: 'react' }, { type: 'subscription-setup', topic: 'react' },
  ]));
  await check('strict', 'development_probe_leaves_one_active_resource', async () => assert.equal(await strictDev.evaluate(() => window.M20.activeSubscriptions()), 1));
  const strictProd = await pageAt('?strict=1&production=1');
  const productionEvents = await strictProd.evaluate(() => window.M20.events.filter(event => event.type.startsWith('subscription-')));
  await check('strict', 'production_build_has_no_extra_development_effect_probe', () => assert.deepEqual(productionEvents, [{ type: 'subscription-setup', topic: 'react' }]));
  observations.strict = { development: strictEvents, production: productionEvents };

  await page.getByLabel('Key strategy', { exact: true }).selectOption('stable');
  await page.getByLabel('Filter subjects', { exact: true }).fill(''); await page.getByLabel('React only', { exact: true }).uncheck();
  await page.screenshot({ path: fileURLToPath(new URL('./browser-desktop.png', import.meta.url)), fullPage: true });
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobilePage = await mobile.newPage(); mobilePage.on('pageerror', error => pageErrors.push(error.message));
  await mobilePage.goto(base); await mobilePage.getByRole('heading', { name: 'React fundamentals lab' }).waitFor();
  await check('accessibility', 'narrow_viewport_has_no_horizontal_overflow', async () => assert.ok(await mobilePage.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)));
  await mobilePage.screenshot({ path: fileURLToPath(new URL('./browser-mobile.png', import.meta.url)), fullPage: true });
  await mobile.close();
  await page.evaluate(() => window.M20.unmount());
  await check('effects', 'root_unmount_releases_subscription_and_dom', async () => { await page.waitForFunction(() => window.M20.activeSubscriptions() === 0 && document.getElementById('root').childNodes.length === 0); });
  await check('browser', 'no_uncaught_react_or_application_exceptions', () => assert.deepEqual(pageErrors, []));
  observations.api = { requests: fixture.requests, server_events: fixture.events };
  observations.pageErrors = pageErrors;
  await context.close();
} finally {
  if (browser) await browser.close();
  await fixture.close();
}
const portClosed = await new Promise(resolve => {
  const socket = createConnection({ host: '127.0.0.1', port: fixture.port });
  socket.once('connect', () => { socket.destroy(); resolve(false); }); socket.once('error', () => resolve(true));
});
assert.ok(portClosed);
const pkg = JSON.parse(await readFile(new URL('./package.json', import.meta.url), 'utf8'));
const counts = Object.fromEntries([...new Set(checks.map(check => check.group))].sort().map(group => [group, checks.filter(check => check.group === group).length]));
const result = { module: 20, verified_date: '2026-10-15', node: process.version, dependencies: pkg.dependencies,
  tools: pkg.devDependencies, checks, counts, total: checks.length, observations,
  cleanup: { browser_closed: true, loopback_ports_closed: { [fixture.port]: portClosed }, docker_started: false },
  scope: 'Actual headless installed Chrome, development/production React bundles, browser DOM/keyboard and same-origin local HTTP. No screen-reader audit, framework SSR/hydration, real authentication/backend or performance benchmark.' };
await writeFile(new URL('./verification-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n');
await writeFile(new URL('./cleanup-results.json', import.meta.url), JSON.stringify(result.cleanup, null, 2) + '\n');
console.log(JSON.stringify({ total: checks.length, counts, browser: observations.browser, cleanup: result.cleanup }, null, 2));
