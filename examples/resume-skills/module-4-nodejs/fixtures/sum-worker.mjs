import { parentPort, workerData, isMainThread } from 'node:worker_threads';
if (!Number.isSafeInteger(workerData.count) || workerData.count < 0) {
  throw new RangeError('count');
}
let sum = 0;
for (let i = 0; i < workerData.count; i++) sum += i;
workerData.tags.push('worker');
parentPort.postMessage({ sum, isMainThread, pid: process.pid, tags: workerData.tags });
