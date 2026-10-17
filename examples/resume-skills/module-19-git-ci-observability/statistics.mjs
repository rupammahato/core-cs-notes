export function percentile(values, fraction) {
  if (!(fraction > 0 && fraction <= 1)) throw new RangeError('fraction must be in (0,1]');
  if (!values.length) return null;
  if (values.some(value => !Number.isFinite(value) || value < 0)) throw new RangeError('finite nonnegative samples required');
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.ceil(fraction * sorted.length) - 1];
}

export function summarize(samples, elapsedSeconds) {
  if (!Number.isFinite(elapsedSeconds) || elapsedSeconds <= 0) throw new RangeError('positive measurement duration required');
  const values = samples.map(sample => sample.latency_ms);
  const successful = samples.filter(sample => sample.status >= 200 && sample.status < 300 && !sample.error).length;
  const round = value => value === null ? null : Number(value.toFixed(3));
  return {
    attempts: samples.length, successful, failed: samples.length - successful,
    error_ratio: samples.length ? (samples.length - successful) / samples.length : 0,
    elapsed_seconds: round(elapsedSeconds),
    attempted_rps: round(samples.length / elapsedSeconds), successful_rps: round(successful / elapsedSeconds),
    mean_ms: values.length ? round(values.reduce((a, b) => a + b, 0) / values.length) : null,
    p50_ms: round(percentile(values, .50)), p95_ms: round(percentile(values, .95)), p99_ms: round(percentile(values, .99)),
    percentile_method: 'nearest rank across all completed attempts, including HTTP failures and client errors',
  };
}

export function errorBudget(total, good, target) {
  if (!Number.isInteger(total) || total <= 0 || !Number.isInteger(good) || good < 0 || good > total || !(target > 0 && target < 1)) {
    throw new RangeError('invalid SLI inputs');
  }
  const observedError = (total - good) / total;
  return { total, good, bad: total - good, target, observed_good_ratio: good / total,
    allowed_bad: Number((total * (1 - target)).toFixed(6)),
    burn_rate: Number((observedError / (1 - target)).toFixed(6)) };
}
