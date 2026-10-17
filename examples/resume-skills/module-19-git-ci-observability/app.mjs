import http from 'node:http';
import { once } from 'node:events';
import { randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { context, propagation, SpanKind, SpanStatusCode, trace } from '@opentelemetry/api';

export async function createApplication(telemetry, { release = 'v1', unhealthy = false } = {}) {
  const logs = [], requests = {}, bounds = [.01, .05, .1, .5, 1];
  const histogram = { count: 0, sum_seconds: 0, cumulative_buckets: Object.fromEntries([...bounds, 'Inf'].map(bound => [bound, 0])) };
  let active = 0;
  function send(res, status, body) {
    if (res.destroyed) return;
    res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(body));
  }
  const dependency = http.createServer((req, res) => {
    const parent = propagation.extract(context.active(), req.headers);
    context.with(parent, () => telemetry.tracer.startActiveSpan('dependency GET /compute', { kind: SpanKind.SERVER }, async span => {
      const url = new URL(req.url, 'http://fixture.invalid');
      await new Promise(resolve => setTimeout(resolve, Number(url.searchParams.get('delay'))));
      const status = url.searchParams.get('fail') === '1' ? 503 : 200;
      span.setAttribute('http.response.status_code', status);
      if (status >= 500) span.setStatus({ code: SpanStatusCode.ERROR });
      send(res, status, { result: status === 200 ? 'computed' : 'unavailable' }); span.end();
    }));
  });
  dependency.listen(0, '127.0.0.1'); await once(dependency, 'listening');
  const dependencyPort = dependency.address().port;
  const gateway = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://fixture.invalid');
    if (url.pathname === '/metrics') return send(res, 200, { requests, active, histogram });
    const route = ['/work', '/health'].includes(url.pathname) ? url.pathname : 'unmatched';
    const requestId = randomUUID(), started = performance.now();
    const parent = propagation.extract(context.active(), req.headers);
    context.with(parent, () => telemetry.tracer.startActiveSpan('gateway GET ' + route, { kind: SpanKind.SERVER }, async span => {
      let status = 500;
      const traceId = trace.getSpan(context.active()).spanContext().traceId;
      active++;
      try {
        if (req.method !== 'GET') { status = 405; return send(res, status, { error: 'method not allowed' }); }
        if (route === '/health') { status = unhealthy ? 503 : 200; return send(res, status, { ready: !unhealthy, release }); }
        if (route !== '/work') { status = 404; return send(res, status, { error: 'route not found' }); }
        const delay = Number(url.searchParams.get('delay') ?? 5);
        if (!Number.isInteger(delay) || delay < 0 || delay > 200) { status = 400; return send(res, status, { error: 'delay must be 0..200ms' }); }
        const fail = url.searchParams.get('fail') === '1' ? '1' : '0';
        const result = await telemetry.tracer.startActiveSpan('gateway HTTP dependency', { kind: SpanKind.CLIENT }, async child => {
          try {
            const headers = {}; propagation.inject(context.active(), headers);
            return await new Promise((resolve, reject) => {
              const request = http.get({ hostname: '127.0.0.1', port: dependencyPort, path: '/compute?delay=' + delay + '&fail=' + fail, headers, agent: false }, response => {
                response.resume(); response.on('end', () => {
                  child.setAttribute('http.response.status_code', response.statusCode);
                  if (response.statusCode >= 500) child.setStatus({ code: SpanStatusCode.ERROR });
                  resolve(response.statusCode);
                });
                response.on('error', reject);
              });
              request.setTimeout(1000, () => request.destroy(new Error('dependency timeout')));
              request.on('error', reject);
            });
          } catch (error) { child.setStatus({ code: SpanStatusCode.ERROR }); throw error; }
          finally { child.end(); }
        });
        status = result;
        send(res, status, { request_id: requestId, trace_id: traceId, release,
          ...(status === 200 ? { result: 'computed' } : { error: 'dependency unavailable' }) });
      } catch {
        status = 503; send(res, status, { error: 'dependency unavailable', request_id: requestId, trace_id: traceId, release });
      } finally {
        const duration = (performance.now() - started) / 1000;
        const key = route + '|' + Math.floor(status / 100) + 'xx';
        requests[key] = (requests[key] ?? 0) + 1;
        histogram.count++; histogram.sum_seconds += duration;
        for (const bound of bounds) if (duration <= bound) histogram.cumulative_buckets[bound]++;
        histogram.cumulative_buckets.Inf++;
        active--;
        logs.push({ event: 'request_complete', request_id: requestId, trace_id: traceId, route, status, duration_ms: duration * 1000, release });
        span.setAttribute('http.route', route); span.setAttribute('http.response.status_code', status);
        if (status >= 500) span.setStatus({ code: SpanStatusCode.ERROR });
        span.end();
      }
    }));
  });
  gateway.listen(0, '127.0.0.1'); await once(gateway, 'listening');
  return { port: gateway.address().port, dependencyPort, logs,
    metrics: () => structuredClone({ requests, active, histogram }),
    close: async () => {
      for (const server of [gateway, dependency]) await new Promise((resolve, reject) => {
        server.close(error => error ? reject(error) : resolve()); server.closeIdleConnections();
      });
    },
  };
}
