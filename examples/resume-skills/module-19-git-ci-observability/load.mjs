import http from 'node:http';
import { performance, monitorEventLoopDelay } from 'node:perf_hooks';
import { summarize } from './statistics.mjs';

export function attempt(url, { deadlineMs = 500, headers = {} } = {}) {
  const started = performance.now();
  return new Promise(resolve => {
    const controller = new AbortController();
    const deadline = setTimeout(() => controller.abort(), deadlineMs);
    let completed = false;
    const finish = result => {
      if (completed) return;
      completed = true; clearTimeout(deadline);
      resolve({ ...result, latency_ms: performance.now() - started });
    };
    const request = http.get(url, { agent: false, headers, signal: controller.signal }, response => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', chunk => { body += chunk; });
      response.on('end', () => finish({ status: response.statusCode, error: null, body, headers: response.headers }));
      response.on('error', error => finish({ status: 0, error: error.code ?? 'RESPONSE_ERROR', body: '' }));
    });
    request.on('error', error => finish({ status: 0, error: error.name === 'AbortError' ? 'DEADLINE' : (error.code ?? 'CLIENT_ERROR'), body: '' }));
  });
}

export async function runLoad(url, { requests = 60, concurrency = 4, warmup = 6, deadlineMs = 500 } = {}) {
  if (!Number.isInteger(requests) || requests < 1 || !Number.isInteger(concurrency) || concurrency < 1 || concurrency > requests) {
    throw new RangeError('bounded positive request count and concurrency required');
  }
  for (let i = 0; i < warmup; i++) await attempt(url, { deadlineMs });
  const delay = monitorEventLoopDelay({ resolution: 10 }); delay.enable();
  const cpuStart = process.cpuUsage();
  const started = performance.now();
  let next = 0;
  const samples = [];
  await Promise.all(Array.from({ length: concurrency }, async () => {
    while (next < requests) { next++; samples.push(await attempt(url, { deadlineMs })); }
  }));
  const elapsed = (performance.now() - started) / 1000;
  delay.disable();
  const cpu = process.cpuUsage(cpuStart);
  return { configuration: { model: 'closed: each slot starts again only after its previous attempt ends', requests, concurrency, warmup, deadline_ms: deadlineMs, keepalive: false },
    summary: summarize(samples, elapsed), samples,
    local_process: { cpu_user_ms: cpu.user / 1000, cpu_system_ms: cpu.system / 1000,
      rss_end_bytes: process.memoryUsage().rss, event_loop_samples: delay.count,
      event_loop_p99_ms: delay.count ? delay.percentile(99) / 1e6 : null,
      scope: 'load generator and both fixture HTTP services share this Node process' } };
}
