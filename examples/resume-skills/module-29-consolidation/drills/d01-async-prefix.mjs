const trace = ['before'];
async function work() { trace.push('inside'); return 42; }
const pending = work();
trace.push('after');
trace.push(await pending);
console.log(JSON.stringify(trace));
