import assert from 'node:assert/strict';
import { writeFile, readFile } from 'node:fs/promises';
import { createConnection } from 'node:net';
import { createTelemetry } from './telemetry.mjs';
import { createApplication } from './app.mjs';
import { attempt, runLoad } from './load.mjs';
import { percentile, summarize, errorBudget } from './statistics.mjs';

const checks = [], observations = {};
const check = (group, name, fn) => { fn(); checks.push({ group, name, passed: true }); console.log('PASS ' + group + '/' + name); };
const telemetry = createTelemetry();
const app = await createApplication(telemetry);
const base = 'http://127.0.0.1:' + app.port;
const ports = [app.port, app.dependencyPort];
try {
  const known = Array.from({ length: 100 }, (_, i) => i + 1);
  check('statistics', 'nearest_rank_reference_percentiles', () => assert.deepEqual([percentile(known, .5), percentile(known, .95), percentile(known, .99)], [50, 95, 99]));
  check('statistics', 'percentile_does_not_mutate_input', () => { const data = [30, 1, 5]; percentile(data, .5); assert.deepEqual(data, [30, 1, 5]); });
  check('statistics', 'empty_samples_have_no_latency_claim', () => assert.equal(summarize([], 1).p99_ms, null));
  check('statistics', 'invalid_measurement_samples_rejected', () => assert.throws(() => percentile([1, Infinity], .99), RangeError));
  const synthetic = [{ status: 200, error: null, latency_ms: 1 }, { status: 503, error: null, latency_ms: 100 }, { status: 0, error: 'DEADLINE', latency_ms: 50 }, { status: 201, error: null, latency_ms: 2 }];
  const summary = summarize(synthetic, 2);
  check('statistics', 'http_errors_and_timeouts_count_as_failures', () => assert.deepEqual([summary.attempts, summary.successful, summary.failed, summary.error_ratio], [4, 2, 2, .5]));
  check('statistics', 'attempted_and_successful_rates_differ', () => assert.deepEqual([summary.attempted_rps, summary.successful_rps], [2, 1]));
  check('statistics', 'failure_latency_retained_in_distribution', () => assert.equal(summary.p99_ms, 100));
  const budget = errorBudget(1000, 995, .999);
  check('statistics', 'slo_budget_reference_example', () => assert.deepEqual([budget.bad, budget.allowed_bad, budget.burn_rate], [5, 1, 5]));
  observations.statistics = { known_sample_count: known.length, known: { p50: 50, p95: 95, p99: 99 }, synthetic_summary: summary, synthetic_slo: budget };

  const success = await attempt(base + '/work?delay=1');
  const body = JSON.parse(success.body);
  check('http', 'successful_response_contains_release_and_result', () => assert.deepEqual([success.status, body.release, body.result], [200, 'v1', 'computed']));
  const bad = await attempt(base + '/work?delay=-1');
  check('http', 'invalid_input_returns_400', () => assert.equal(bad.status, 400));
  const missing = await attempt(base + '/not-a-real-route');
  check('http', 'unknown_route_returns_404', () => assert.equal(missing.status, 404));
  const failed = await attempt(base + '/work?delay=1&fail=1');
  check('http', 'dependency_failure_returns_safe_503', () => assert.deepEqual([failed.status, JSON.parse(failed.body).error], [503, 'dependency unavailable']));
  const spans = telemetry.spans().filter(span => span.trace_id === body.trace_id);
  check('tracing', 'three_real_sdk_spans_per_work_request', () => assert.equal(spans.length, 3));
  const gateway = spans.find(span => span.name === 'gateway GET /work');
  const client = spans.find(span => span.kind === 2);
  const dependency = spans.find(span => span.name === 'dependency GET /compute');
  check('tracing', 'client_and_dependency_parent_relationships', () => { assert.equal(client.parent_span_id, gateway.span_id); assert.equal(dependency.parent_span_id, client.span_id); });
  check('tracing', 'root_context_and_distinct_span_ids', () => { assert.equal(gateway.parent_span_id, null); assert.equal(new Set(spans.map(s => s.span_id)).size, 3); });
  const traceId = '11111111111111111111111111111111', parentId = '2222222222222222';
  const incoming = JSON.parse((await attempt(base + '/work?delay=1', { headers: { traceparent: '00-' + traceId + '-' + parentId + '-01' } })).body);
  const incomingGateway = telemetry.spans().find(span => span.trace_id === traceId && span.name === 'gateway GET /work');
  check('tracing', 'valid_w3c_parent_propagates', () => { assert.equal(incoming.trace_id, traceId); assert.equal(incomingGateway.parent_span_id, parentId); });
  const invalid = JSON.parse((await attempt(base + '/work?delay=1', { headers: { traceparent: '00-00000000000000000000000000000000-0000000000000000-01' } })).body);
  check('tracing', 'zero_trace_context_is_replaced', () => assert.notEqual(invalid.trace_id, '00000000000000000000000000000000'));
  check('tracing', 'dependency_failure_marks_trace_error', () => {
    const failureTrace = JSON.parse(failed.body).trace_id;
    assert.equal(telemetry.spans().filter(span => span.trace_id === failureTrace && span.status === 2).length, 3);
  });
  const concurrent = await Promise.all(Array.from({ length: 8 }, () => attempt(base + '/work?delay=5')));
  check('tracing', 'concurrent_requests_keep_distinct_context', () => {
    const ids = concurrent.map(response => JSON.parse(response.body).trace_id);
    assert.equal(new Set(ids).size, 8);
    for (const id of ids) assert.equal(telemetry.spans().filter(span => span.trace_id === id).length, 3);
  });
  check('logs', 'response_log_and_trace_are_correlated', () => assert.ok(app.logs.some(log => log.request_id === body.request_id && log.trace_id === body.trace_id && log.release === 'v1')));
  const secret = 'M19_CANARY_DO_NOT_LOG';
  await attempt(base + '/work?delay=1&token=' + secret, { headers: { Authorization: 'Bearer ' + secret, Cookie: 'session=' + secret } });
  check('logs', 'allowlisted_log_fields_omit_credentials_and_query', () => assert.ok(!JSON.stringify(app.logs).includes(secret)));
  await attempt(base + '/unknown/123'); await attempt(base + '/unknown/456');
  const metrics = app.metrics();
  check('metrics', 'bounded_route_status_labels', () => { assert.ok(Object.keys(metrics.requests).every(key => /^(\/work|\/health|unmatched)\|[245]xx$/.test(key))); assert.ok(!JSON.stringify(metrics.requests).includes('123')); });
  check('metrics', 'histogram_count_matches_counters', () => assert.equal(metrics.histogram.count, Object.values(metrics.requests).reduce((a, b) => a + b, 0)));
  check('metrics', 'cumulative_buckets_are_monotone', () => {
    const buckets = Object.values(metrics.histogram.cumulative_buckets);
    // Object integer-key ordering is not numeric bucket order; inspect explicitly.
    const ordered = [.01, .05, .1, .5, 1, 'Inf'].map(key => metrics.histogram.cumulative_buckets[key]);
    assert.ok(ordered.every((n, i) => i === 0 || n >= ordered[i - 1])); assert.equal(ordered.at(-1), metrics.histogram.count); assert.ok(buckets.length === 6);
  });
  check('metrics', 'active_work_returns_to_zero', () => assert.equal(metrics.active, 0));
  observations.trace = spans;
  observations.log = app.logs.find(log => log.request_id === body.request_id);
  observations.metrics_before_load = metrics;

  const normal = await runLoad(base + '/work?delay=10');
  check('load', 'measured_attempt_count_excludes_warmup', () => assert.equal(normal.summary.attempts, 60));
  check('load', 'normal_samples_are_all_successful', () => assert.deepEqual([normal.summary.successful, normal.summary.failed], [60, 0]));
  check('load', 'reported_percentiles_derive_from_raw_samples', () => assert.equal(normal.summary.p95_ms, Number(percentile(normal.samples.map(s => s.latency_ms), .95).toFixed(3))));
  const errors = await runLoad(base + '/work?delay=1&fail=1', { requests: 12, concurrency: 3, warmup: 0 });
  check('load', 'failure_run_has_zero_successful_throughput', () => assert.deepEqual([errors.summary.failed, errors.summary.successful_rps], [12, 0]));
  const deadlines = await runLoad(base + '/work?delay=100', { requests: 4, concurrency: 2, warmup: 0, deadlineMs: 10 });
  check('load', 'client_deadlines_remain_in_failed_attempts', () => assert.ok(deadlines.samples.every(sample => sample.error === 'DEADLINE') && deadlines.summary.failed === 4));
  observations.load = { normal: { configuration: normal.configuration, summary: normal.summary, local_process: normal.local_process }, errors: errors.summary, deadlines: deadlines.summary };
  await writeFile(new URL('./load-results.json', import.meta.url), JSON.stringify({ normal, errors, deadlines }, null, 2) + '\n');
  await writeFile(new URL('./application-log-output.json', import.meta.url), JSON.stringify(app.logs, null, 2) + '\n');
} finally {
  await app.close();
  await writeFile(new URL('./trace-output.json', import.meta.url), JSON.stringify(telemetry.spans(), null, 2) + '\n');
  await telemetry.close();
}
async function closed(port) {
  return new Promise(resolve => {
    const socket = createConnection({ host: '127.0.0.1', port });
    socket.once('connect', () => { socket.destroy(); resolve(false); });
    socket.once('error', () => resolve(true));
  });
}
const portsClosed = Object.fromEntries(await Promise.all(ports.map(async port => [port, await closed(port)])));
assert.ok(Object.values(portsClosed).every(Boolean));
const dependencies = JSON.parse(await readFile(new URL('./package.json', import.meta.url), 'utf8')).dependencies;
const counts = Object.fromEntries([...new Set(checks.map(c => c.group))].sort().map(group => [group, checks.filter(c => c.group === group).length]));
const result = { node: process.version, dependencies, checks, total: checks.length, counts, observations, cleanup: { loopback_ports_closed: portsClosed } };
await writeFile(new URL('./node-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ total: checks.length, counts, normal_load: observations.load.normal.summary, portsClosed }, null, 2));
