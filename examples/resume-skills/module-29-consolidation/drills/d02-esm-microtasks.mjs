const trace = ['sync'];
process.nextTick(() => trace.push('nextTick'));
Promise.resolve().then(() => trace.push('promise'));
queueMicrotask(() => trace.push('microtask'));
setImmediate(() => console.log(JSON.stringify(trace)));
