export function estimate({ users = 100000, requestsPerUserDay = 20, peakFactor = 10,
  meanServiceMs = 120, assumedBackendQps = 80, utilization = 0.7, responseBytes = 20480 } = {}) {
  if (![users, requestsPerUserDay, peakFactor, meanServiceMs, assumedBackendQps, responseBytes].every(v => Number.isFinite(v) && v > 0) || !(utilization > 0 && utilization < 1)) throw new Error('Bad capacity assumptions');
  const requestsPerDay = users * requestsPerUserDay;
  const averageQps = requestsPerDay / 86400, peakQps = averageQps * peakFactor;
  const targetPerBackendQps = assumedBackendQps * utilization;
  const healthyBackends = Math.ceil(peakQps / targetPerBackendQps);
  return { assumptions: { users, requestsPerUserDay, peakFactor, meanServiceMs, assumedBackendQps, utilization, responseBytes },
    requestsPerDay, averageQps, peakQps, meanInFlightAtPeak: peakQps * meanServiceMs / 1000,
    targetPerBackendQps, healthyBackends, fleetForOneFailure: healthyBackends + 1,
    responseBytesPerSecondAtPeak: peakQps * responseBytes,
    scope: 'Calculated planning scenario; per-backend capacity is an assumption, not a benchmark.' };
}
