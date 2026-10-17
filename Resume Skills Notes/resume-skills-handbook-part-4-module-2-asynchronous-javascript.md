# Resume Skills Placement Handbook — Part 4
# Module 2: Asynchronous JavaScript

**Module 2 · 3–4 hours · Tier 1 · Requires: M0 and M1**

---

## Why this module matters

An API handler often needs to wait for a database, another service or a file. During that wait, other requests should make progress. Yet adding async to a function does not make its expensive computation stop blocking, and adding Promise.all does not make a group of writes atomic.

This module builds the execution timeline that sits underneath Node.js and backend frameworks.

> **For every asynchronous operation, ask: when does it start, who observes its completion, what depends on its result, and what happens if it fails or is no longer needed?**

That question explains both output-prediction puzzles and real incidents: an early success response, a missing error handler, an overloaded connection pool, duplicate payment attempts or inconsistent shared state.

**Verification:** all 28 numbered snippets ran in separate Node.js **v22.14.0** processes. They use **ES modules**, except example 19, which explicitly uses **CommonJS**. Captured source, actual output and the verifier are preserved in examples/resume-skills/module-2-async-javascript/. The fetch example uses a temporary IPv4 loopback server, not an external endpoint.

### Scope and execution context

- M1 covered values, closures, receivers and mutation. Scheduling does not replace those rules.
- This chapter covers asynchronous composition and the basic scheduling model.
- M4 will cover Node internals: V8, libuv, event-loop phases, native work, streams and worker threads.
- Browser tasks/rendering and Node phases are related models, not interchangeable diagrams.
- Output checks establish the stated runtime/context behavior. They are not latency benchmarks or proof of distributed correctness.

### How to run the examples

From the repository root:

```powershell
node examples/resume-skills/module-2-async-javascript/verify.mjs
node examples/resume-skills/module-2-async-javascript/verify.mjs 25-bounded
```

The first command checks all cases. The second checks one case and prints its output. Each case has a five-second process timeout. No packages, credentials or internet access are required.

---

## 2.1 What asynchronous actually means

### Synchronous work and waiting are different

In synchronous control flow, the next statement runs after the called function returns. If that call blocks the executing thread until a slow operation completes, that thread cannot execute another handler in the meantime.

An asynchronous API lets the caller continue before the operation's result is ready. The result arrives through a callback, promise, event or another protocol. This describes the relationship between starting and observing completion; it does not tell you which operating-system mechanism performs the work.

```text
Request A: execute handler -> start I/O -> suspend dependent continuation
                                           |
Request B:                  execute handler -> start its I/O
                                           |
A's I/O ready -> schedule A's continuation -> consume result -> respond
```

This is a conceptual trace. It does not imply a dedicated thread per request or say that every I/O operation uses a worker thread.

### Concurrency vs parallelism

| Term | Meaning in this chapter |
| --- | --- |
| Concurrency | Several operations are in progress during overlapping periods |
| Parallelism | Work actually executes simultaneously on different execution resources |
| Non-blocking wait | Waiting does not occupy the JavaScript thread with a blocking call |
| Throughput | Completed work per unit time |
| Latency | Time taken by one operation or request |

Within one ordinary JavaScript execution context, callbacks do not execute simultaneously. Host I/O can still progress outside that context. Worker threads/processes introduce other execution contexts, covered in M4.

**Interview line:** “Async lets me express work whose result arrives later. Concurrency depends on starting overlapping operations; CPU parallelism needs suitable execution resources. Neither follows merely from the async keyword.”

### Callbacks are functions, not a scheduling guarantee

A function that accepts a callback may invoke it immediately, later or repeatedly; read its contract. Array.map calls its callback synchronously. An HTTP event listener runs when the host delivers an event.

**Verified example 01-callback: A callback does not become the caller's return value**

```javascript
function lookup(id, callback) {
  queueMicrotask(() => callback(null, { id }));
}
const result = lookup(7, (error, row) => {
  if (error) throw error;
  console.log('callback', row.id);
  return row;
});
console.log('returned', typeof result);
```

Actual output:

```text
returned undefined
callback 7
```


Returning row from the callback returns to whoever invokes that callback. It cannot retroactively change lookup's earlier return value.

**Backend mistake:** a handler returns a local variable immediately after starting a callback-based database call. The variable still lacks the result.

---

## 2.2 Promises: represent and compose outcomes

### States and resolution

A promise is pending, fulfilled or rejected. Fulfilled/rejected are settled states.

“Resolved” is more subtle: a promise can be locked to another promise's eventual outcome while still pending. Do not use resolved as an unconditional synonym for fulfilled.

A promise represents an outcome; it is not a thread, queue or lazy task definition.

### The executor runs synchronously

**Verified example 02-executor: The executor runs now; handlers run later**

```javascript
console.log('start');
const p = new Promise((resolve, reject) => {
  console.log('executor');
  resolve(7);
  reject(new Error('ignored settlement'));
  console.log('executor continues');
});
p.then(value => console.log('then', value));
console.log('end');
```

Actual output:

```text
start
executor
executor continues
end
then 7
```


Creating the promise calls its executor now. Calling resolve does not stop the executor's remaining statements. The later reject cannot replace the outcome selected by the earlier resolve.

Reaction handlers attached with then/catch run asynchronously, even when the promise is already settled.

**Common trap:** putting a large loop inside new Promise executes that loop synchronously. Wrapping it did not offload it.

### Adopting another promise

**Verified example 03-adoption: Resolved can still be pending**

```javascript
let release;
const inner = new Promise(resolve => { release = resolve; });
const outer = new Promise(resolve => {
  resolve(inner);
  console.log('adopted inner');
});
let observed = false;
outer.then(value => { observed = true; console.log('value', value); });
await Promise.resolve();
console.log('observed before release', observed);
release(42);
await outer;
```

Actual output:

```text
adopted inner
observed before release false
value 42
```


outer follows inner. It cannot fulfill with 42 until inner does. The initial resolve(inner) fixed that relationship without immediately producing a fulfilled value.

This distinction matters when tracing nested promises: separate selecting an outcome source from that source becoming available.

For constructor and resolution details, see [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise).

### When should you construct a promise?

Use an existing promise API when available. Construct one to adapt a callback/event contract or manually control settlement where that is actually needed.

Avoid an async promise executor. Its returned promise is ignored by the constructor; a rejection after an await does not automatically reject the outer promise. Use an async function directly, or a synchronous executor that explicitly resolves/rejects the adapted operation.

Also avoid wrapping a promise API merely to forward its result: it adds another error path without changing the capability.

---

## 2.3 Chaining and ownership of completion

### Every then returns a new promise

A handler's result determines the next promise:

| Handler behavior | Next promise |
| --- | --- |
| Return an ordinary value | Fulfills with that value |
| Return no value | Fulfills with undefined |
| Return a promise/thenable | Adopts its eventual outcome |
| Throw an exception | Rejects with that exception |
| No matching handler supplied | Passes through the original value or rejection |

**Verified example 04-chain: Returning values and promises sequences a chain**

```javascript
const value = await Promise.resolve(2)
  .then(n => n + 1)
  .then(n => Promise.resolve(n * 4));
console.log(value);
```

Actual output:

```text
12
```


The second step cannot calculate its result until the first step provides n. Returning the inner promise joins its outcome into the chain.

### Missing return means missing dependency

**Verified example 05-floating: A missing return disconnects completion**

```javascript
let release;
const gate = new Promise(resolve => { release = resolve; });
let saved = false;
let child;
await Promise.resolve().then(() => {
  child = gate.then(() => { saved = true; });
  // Missing: return child;
});
console.log('outer complete', saved);
release();
await child;
console.log('child complete', saved);
```

Actual output:

```text
outer complete false
child complete true
```


The gate deliberately controls completion. There is no flaky assumption about which timer happens first.

The outer operation is complete while saved remains false because it never adopted child. We separately await child here so the demonstration retains ownership of it; an accidental application version often loses that reference too.

**Backend connection:** if an endpoint reports “saved” before the save promise completes, a later failure cannot be communicated through that already-sent response.

Use one of three deliberate choices:

1. Await completion before responding.
2. Return/adopt the promise so the caller owns completion.
3. Hand work to a separately owned mechanism with an explicit failure policy.

Attaching a logging catch prevents one kind of unobserved rejection, but it does not make the work durable. In-process work can disappear when the process exits. Durable jobs are M15.

The [MDN promise guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises) discusses floating promises and composition.

---

## 2.4 Error paths: reject, recover and clean up

### Error handling changes the result contract

**Verified example 06-errors: Throws reject the next promise; catch can recover**

```javascript
const value = await Promise.resolve(7)
  .then(() => { throw new Error('invalid'); })
  .then(() => console.log('skipped'))
  .catch(error => { console.log('caught', error.message); return 0; })
  .then(n => n + 1);
console.log('recovered', value);
try {
  await Promise.resolve().then(
    () => { throw new Error('handler failed'); },
    () => console.log('same then rejection handler')
  );
} catch (error) { console.log('downstream', error.message); }
```

Actual output:

```text
caught invalid
recovered 1
downstream handler failed
```


The first catch converts failure into a successful value 0. The next then therefore runs.

A rejection handler supplied as the second argument of a particular then handles rejection of that then's input promise. It does not catch an exception thrown by that same then's fulfillment handler; the exception rejects the newly returned promise.

Use a downstream catch when it must observe those handler failures.

### Catch is not automatically “logging only”

These are different policies:

| Policy | Consequence |
| --- | --- |
| Catch and return fallback | Operation now fulfills with fallback |
| Catch and throw | Failure continues with the same/new reason |
| Catch and return undefined | Failure becomes successful undefined |
| Catch and start another unreturned promise | New completion/error can be disconnected |

Do not turn a required database failure into an apparently successful empty result unless the API contract deliberately permits that representation.

### finally is for cleanup

**Verified example 07-finally: Cleanup preserves a result unless cleanup fails**

```javascript
console.log(await Promise.resolve(7).finally(() => 99));
try {
  await Promise.reject(new Error('original')).finally(() => {});
} catch (error) { console.log(error.message); }
try {
  await Promise.resolve(7).finally(() => { throw new Error('cleanup'); });
} catch (error) { console.log(error.message); }
```

Actual output:

```text
7
original
cleanup
```


A normal finally callback preserves the earlier outcome. Its ordinary return value is ignored. If cleanup throws or returns a rejected promise, the resulting promise rejects with that cleanup failure instead.

An asynchronous cleanup returned from finally is awaited by the resulting chain. Consequently cleanup also affects completion latency.

**Practical concern:** a cleanup failure can hide the original error. Decide which information to preserve when releasing a resource itself fails.

See [MDN finally](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/finally).

### Exceptions across callback boundaries

A synchronous try/catch only handles exceptions thrown while its protected call stack is active. It does not stay around waiting to catch an exception thrown inside a later timer callback.

Likewise, if a promise executor schedules a callback that later throws, that later throw is outside the executor's synchronous invocation. Catch and reject inside the callback when adapting such an API.

Unhandled rejection behavior depends on runtime/configuration. Keep ownership of every promise and handle failures at the relevant boundary; a global rejection listener is not a replacement for request-specific handling.

---

## 2.5 async/await: the same outcome model with direct syntax

### What async changes

Calling an async function returns a promise. A returned value fulfills that promise; an uncaught exception rejects it.

Its synchronous prefix executes immediately. Await suspends that async function's continuation while control returns to its caller. It does not suspend the entire process.

**Verified example 08-await: Await yields even for a non-promise value**

```javascript
async function run() {
  console.log('inside before');
  const value = await 7;
  console.log('inside after', value);
  return value + 1;
}
console.log('outside before');
const p = run();
console.log('outside after', p instanceof Promise);
console.log('result', await p);
```

Actual output:

```text
outside before
inside before
outside after true
inside after 7
result 8
```


Awaiting even the value 7 schedules a later continuation. The caller logs outside after before the function logs inside after.

An async function without an await can still execute all its body synchronously before returning the promise to its caller.

See [MDN async functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function) and [await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await).

### Catch the operation you actually await

**Verified example 09-return-await: A local catch needs to observe the rejection**

```javascript
function fail() { return Promise.reject(new Error('failed')); }
async function forwarded() {
  try { return fail(); }
  catch { return 'local fallback'; }
}
async function observed() {
  try { return await fail(); }
  catch { return 'local fallback'; }
}
try { await forwarded(); }
catch (error) { console.log('caller', error.message); }
console.log(await observed());
```

Actual output:

```text
caller failed
local fallback
```


forwarded returns a rejected promise without observing its rejection inside the local try block. The caller's catch observes it.

observed awaits inside the protected block, so the rejection becomes an exception at that await and the local catch returns the fallback.

Do not memorize “return await is always bad.” It can be necessary for a local catch/finally boundary to encompass the eventual operation. Avoid performance folklore without a relevant measurement.

### Top-level await

ES modules permit top-level await; classic scripts do not. CommonJS is a different module context. Top-level await can delay dependent module evaluation, so initialization dependencies deserve care.

A pending promise alone is not a general guarantee that Node remains running. Active runtime handles and unfinished top-level module evaluation have their own lifecycle behavior; do not use an unresolved promise as a background-job supervisor.

---

## 2.6 Sequential and concurrent work

### Choose from dependencies

Use sequential composition when B needs A's result, when order is a business rule, or when the resource requires it. Start independent operations before joining them when overlap is permitted.

**Verified example 11-concurrency: Starting operations determines overlap**

```javascript
let active = 0;
let peak = 0;
async function work(id) {
  active++;
  peak = Math.max(peak, active);
  await Promise.resolve();
  active--;
  return id;
}
const sequential = [];
for (const id of [1, 2, 3]) sequential.push(await work(id));
console.log('sequential', sequential.join(','), 'peak', peak);
peak = 0;
const concurrent = await Promise.all([1, 2, 3].map(work));
console.log('concurrent', concurrent.join(','), 'peak', peak);
```

Actual output:

```text
sequential 1,2,3 peak 1
concurrent 1,2,3 peak 3
```


Both versions perform the same three logical operations. The second starts them before waiting, so three are in progress.

The example measures overlapping calls, not CPU parallelism or network speed.

For independent operations with durations a, b and c, a sequential critical path is roughly a+b+c; ideal overlap approaches max(a,b,c). Real limits, contention, setup and shared bottlenecks can change either estimate. Do not advertise a measured speedup from this conceptual arithmetic.

### Promise.all does not start functions for you

Calling work(id) starts that function. Promise.all observes the values/promises supplied to it.

Passing function objects without invoking them merely treats those functions as ordinary values. Starting a thousand calls in map before Promise.all already created a thousand in-flight operations; the join adds no concurrency limit.

### forEach is not an asynchronous join

**Verified example 10-foreach: forEach ignores callback promises**

```javascript
let release;
const gate = new Promise(resolve => { release = resolve; });
const values = [];
const pending = [];
await [1, 2].forEach(id => {
  pending.push((async () => {
    await gate;
    values.push(id);
  })());
  return pending.at(-1); // forEach ignores this promise.
});
console.log('after forEach', values.length);
release();
await Promise.all(pending);
console.log('after explicit join', values.join(','));
```

Actual output:

```text
after forEach 0
after explicit join 1,2
```


forEach returns undefined and ignores callback return values. Awaiting that undefined does not wait for the callback operations.

Use:

- A for...of loop with await for sequential dependency.
- Promise.all(items.map(work)) for permitted independent overlap.
- A bounded pool for large collections or constrained downstream capacity.

Filter with an async predicate has a related trap: promises are truthy objects, so ordinary filter does not wait for the predicate's boolean result. First await predicate results, then filter using those booleans.

---

## 2.7 Choose the promise combinator by the contract

| Method | Successful result | Failure behavior | Empty input |
| --- | --- | --- | --- |
| all | All fulfillment values in input order | Rejects when an input rejection determines the result | Fulfills with [] |
| allSettled | Status/value-or-reason for every input, in input order | Input rejections become outcome records | Fulfills with [] |
| any | First fulfillment value | Rejects with AggregateError if all reject | Rejects with AggregateError |
| race | First settlement's value or reason | A rejection can win | Remains pending |

None of these methods automatically cancels losing or remaining operations. “First” means the outcome observed by the composition machinery, not a universal ranking of wall-clock completion timestamps.

### all: require every result

**Verified example 12-all-order: all preserves input order, not completion order**

```javascript
let firstDone, secondDone;
const first = new Promise(resolve => { firstDone = resolve; });
const second = new Promise(resolve => { secondDone = resolve; });
const combined = Promise.all([first, second]);
secondDone('B');
firstDone('A');
console.log((await combined).join(','));
console.log(JSON.stringify(await Promise.all([])));
```

Actual output:

```text
A,B
[]
```


Output order follows the input iterable even when completion order differs. This supports combining named dependencies without confusing their positions.

**Verified example 13-all-failure: all rejecting does not cancel another operation**

```javascript
let release;
let completed = false;
const slow = new Promise(resolve => { release = resolve; })
  .then(() => { completed = true; return 'saved'; });
try { await Promise.all([Promise.reject(new Error('required failed')), slow]); }
catch (error) { console.log(error.message, completed); }
release();
await slow;
console.log('later side effect', completed);
```

Actual output:

```text
required failed false
later side effect true
```


The aggregate rejection is not rollback. slow remains alive and later performs its side effect.

**Backend connection:** Promise.all of independent INSERT/UPDATE operations is not a database transaction. One failure can coexist with other committed writes.

Reference: [MDN all](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all).

### allSettled: inspect every outcome

**Verified example 14-settled: allSettled records each outcome**

```javascript
const results = await Promise.allSettled([
  Promise.resolve('profile'),
  Promise.reject(new Error('recommendations unavailable'))
]);
console.log(JSON.stringify(results.map(result =>
  result.status === 'fulfilled'
    ? { status: result.status, value: result.value }
    : { status: result.status, reason: result.reason.message }
)));
```

Actual output:

```text
[{"status":"fulfilled","value":"profile"},{"status":"rejected","reason":"recommendations unavailable"}]
```


Useful for reporting each ingestion item, independent notifications or partial-result dashboards. The method helps collect outcomes; you still decide which failures invalidate the overall request.

Reference: [MDN allSettled](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled).

### any: one success is sufficient

**Verified example 15-any: any ignores rejections until a success or total failure**

```javascript
console.log(await Promise.any([
  Promise.reject(new Error('replica A')),
  Promise.resolve('replica B')
]));
try {
  await Promise.any([Promise.reject('A'), Promise.reject('B')]);
} catch (error) { console.log(error.name, error.errors.join(',')); }
try { await Promise.any([]); }
catch (error) { console.log('empty', error.name, error.errors.length); }
```

Actual output:

```text
replica B
AggregateError A,B
empty AggregateError 0
```


Early failures do not defeat a later success. AggregateError.errors follows input order for the rejected inputs.

Possible use: equivalent read replicas where one acceptable success is enough. Multiple writes are not automatically safe candidates: redundant operations may create redundant side effects.

Reference: [MDN any](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/any).

### race: one settlement decides

**Verified example 16-race: race observes the first settlement and is asynchronous**

```javascript
let synchronous = true;
const p = Promise.race([Promise.resolve('ready')])
  .then(value => console.log(value, synchronous));
synchronous = false;
await p;
try {
  await Promise.race([Promise.reject(new Error('fast failure')), Promise.resolve('ok')]);
} catch (error) { console.log(error.message); }
let emptySettled = false;
Promise.race([]).then(() => { emptySettled = true; });
await Promise.resolve();
console.log('empty settled', emptySettled);
```

Actual output:

```text
ready false
fast failure
empty settled false
```


Even an already-fulfilled input is observed asynchronously. An empty race never settles by itself; the example checks its state without awaiting it forever.

Possible use: an operation versus a deadline. That decides how long the caller waits; cancellation requires a separate mechanism.

Reference: [MDN race](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/race).

---
## 2.8 Call stack, microtasks and host scheduling

### A useful browser-level picture

A synchronous JavaScript execution segment runs to completion. At a microtask checkpoint, queued microtasks are processed, including new microtasks added during that drain. Promise reactions and queueMicrotask callbacks use microtasks.

A browser has host tasks for events and timers, and opportunities to render. This is a teaching model, not a claim that there is one universal FIFO task queue for every event source.

```text
Run current synchronous segment
        |
Microtask checkpoint
  -> queued promise reaction
  -> queued queueMicrotask callback
  -> additional microtasks queued by those callbacks
        |
Host can continue with subsequent work
  (such as a ready timer task; rendering follows browser rules)
```

**Verified example 17-microtasks: New microtasks drain before a later timer callback**

```javascript
console.log('A');
setTimeout(() => console.log('timer'), 0);
Promise.resolve().then(() => {
  console.log('promise');
  queueMicrotask(() => console.log('nested'));
});
queueMicrotask(() => console.log('microtask'));
console.log('B');
```

Actual output:

```text
A
B
promise
microtask
nested
timer
```


Trace it:

1. A and B are synchronous.
2. The promise handler was queued before the standalone microtask.
3. The promise handler queues nested at the end of the microtask work.
4. The microtask drain finishes before the later timer callback.

A timer delay is a scheduling threshold, not an appointment at an exact millisecond. Busy JavaScript, other callbacks and host rules can delay it.

**Starvation:** repeatedly scheduling more microtasks can keep the drain busy and postpone timers/I/O/rendering. Repeated await Promise.resolve() is therefore not a dependable way to yield to host I/O or browser rendering.

For the browser checkpoint model, see [MDN microtasks](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide).

### Node has additional scheduling rules

Node has event-loop phases and a separate next-tick queue. process.nextTick is not “the next event-loop iteration.” Module evaluation context also matters.

**Verified example 18-esm-tick: Node ES-module top-level scheduling**

```javascript
console.log('sync');
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
```

Actual output:

```text
sync
promise
microtask
nextTick
```


**Verified example 19-cjs-tick: Node CommonJS top-level scheduling**

Context: **CommonJS**, unlike the other snippets.

```javascript
console.log('sync');
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
```

Actual output:

```text
sync
nextTick
promise
microtask
```


These are the same statements in different top-level module contexts. ES-module evaluation is already being processed asynchronously, which affects the relative queues here.

**Do not generalize these two traces to every callback location.** A top-level ESM observation does not imply that promises always precede nextTick in a timer or I/O callback.

The version-matched [Node process documentation](https://nodejs.org/download/release/v22.14.0/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick) explicitly documents this distinction.

### What not to memorize

- “Timers always run before setImmediate” is not a universal top-level guarantee.
- A timer scheduled with zero delay does not run in the current synchronous segment.
- Browser tasks are not a copy of Node's phase diagram.
- Node/libuv version changes can affect timer/immediate interactions.
- Repeating a sample many times does not turn an unspecified ordering into a guarantee.

M4 will trace timers, poll and check phases using labeled contexts. The [Node event-loop guide](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) describes the libuv timer change associated with Node 20.

---

## 2.9 Async does not remove CPU blocking

**Verified example 20-cpu: async does not offload synchronous CPU work**

```javascript
setTimeout(() => console.log('timer'), 0);
async function calculate() {
  console.log('CPU start');
  let total = 0;
  for (let i = 0; i < 100000; i++) total += i;
  console.log('CPU end', total);
  return total;
}
const p = calculate();
console.log('caller regained control');
await p;
```

Actual output:

```text
CPU start
CPU end 4999950000
caller regained control
timer
```


The caller regains control only after the entire loop finishes. calculate has no suspension point.

Even if the loop came after await, it would block the JavaScript thread while that continuation runs. Await controls where waiting can suspend a function; it does not split arbitrary computation across cores.

### Choose a response to the actual bottleneck

| Work/problem | Direction to investigate |
| --- | --- |
| Waiting for supported network/file operations | Use suitable asynchronous APIs |
| Heavy CPU calculation | Worker threads/processes or a separate compute service |
| Many small CPU chunks | Deliberate host-level yielding, with a latency budget |
| Large response or file transfer | Streaming and backpressure, M4 |
| Too many downstream operations | Bounded concurrency, queueing and capacity limits |
| Slow database query | Query/schema/index/pool investigation, not merely async syntax |

In Node, a deliberately awaited setImmediate from node:timers/promises can let host phases progress between chunks. It still executes later chunks on the same thread and does not create CPU parallelism.

A browser may use workers for computation and has separate rendering constraints. Do not prescribe Node-only yield APIs in browser code.

**Interview line:** “Non-blocking I/O helps while waiting. CPU-bound JavaScript still occupies the executing JavaScript thread. I would measure the bottleneck and choose offloading or bounded chunking as appropriate.”

---

## 2.10 Timeouts, cancellation and uncertain outcomes

### Separate three meanings

| Mechanism | What it establishes | What it does not establish |
| --- | --- | --- |
| Stop awaiting a result | Caller no longer waits through that path | Underlying operation has stopped |
| Abort a supported operation | A cancellation request reaches that API | Every downstream side effect was undone |
| Roll back a transaction | Changes inside that transaction are reverted under its rules | An unrelated external payment/email was reversed |

### Racing a deadline is not cancellation

**Verified example 21-timeout-race: A timeout race leaves underlying work alive**

```javascript
let release;
let completed = false;
const work = new Promise(resolve => { release = resolve; })
  .then(() => { completed = true; return 'committed'; });
let timer;
const deadline = new Promise((_, reject) => {
  timer = setTimeout(() => reject(new Error('deadline')), 1);
});
try { await Promise.race([work, deadline]); }
catch (error) { console.log(error.message, completed); }
finally { clearTimeout(timer); }
release();
console.log(await work, completed);
```

Actual output:

```text
deadline false
committed true
```


The timeout wins before we release work. Yet work later completes and commits its simulated effect.

The finally clears the deadline timer if it is no longer needed. Clearing a timer is cleanup, not reversal of the competing work.

The example uses a manually released gate so it demonstrates causality rather than relying on approximate “slow timer versus fast timer” measurements.

**Payment connection:** after a client timeout, “no response” is not proof that the server did nothing. A blind retry of a non-idempotent action can duplicate it. Later chapters use idempotency keys, status lookup and explicit uncertain outcomes.

### Cancellation needs API support

**Verified example 22-abort: Cancel an operation that supports AbortSignal**

```javascript
import { setTimeout as sleep } from 'node:timers/promises';
const controller = new AbortController();
const pending = sleep(10000, 'done', { signal: controller.signal });
const observed = pending.catch(error => {
  console.log(error.name, controller.signal.aborted);
});
controller.abort(new Error('caller left'));
await observed;
console.log('reason', controller.signal.reason.message);
```

Actual output:

```text
AbortError true
reason caller left
```


The signal is an input to the timer operation. Calling abort requests cancellation and that API rejects with AbortError. The supplied signal reason records why the caller canceled.

Simply creating an AbortController does nothing to an operation that never receives or checks its signal.

For the timer behavior and error contract, see [Node v22.14.0 timers](https://nodejs.org/download/release/v22.14.0/docs/api/timers.html#cancelling-timers).

### A deadline signal can have a different reason from the API error

**Verified example 23-deadline-signal: Deadline signals and API errors are distinct**

```javascript
import { setTimeout as sleep } from 'node:timers/promises';
const signal = AbortSignal.timeout(5);
try {
  await sleep(10000, 'done', { signal });
} catch (error) {
  console.log('operation error', error.name);
  console.log('signal reason', signal.reason.name);
}
```

Actual output:

```text
operation error AbortError
signal reason TimeoutError
```


For this Node timer API, the rejected operation has name AbortError while signal.reason is a TimeoutError. Read the API's error contract rather than assuming every cancellation-aware API emits the same error name.

The long sleep supplies an active operation until it is aborted. AbortSignal.timeout by itself is not a general process-liveness mechanism.

Node also offers AbortSignal.any to combine signals, such as a request cancellation and an operation deadline. Availability differs by runtime/version. Check the [version-matched globals documentation](https://nodejs.org/download/release/v22.14.0/docs/api/globals.html#class-abortsignal).

### End-to-end deadline thinking

For a request with several steps, define an overall budget. Giving each retry or sequential step a fresh full timeout can exceed that budget many times over.

At each boundary ask:

1. How much budget remains?
2. Does the library support cancellation?
3. Can the server still finish after the caller stops waiting?
4. Is the operation safe to retry?
5. Who records/reconciles an uncertain result?

Cancellation is cooperative. It cannot preempt a JavaScript loop that never gives the host an opportunity to deliver the signal. A remote service may already have accepted a write by the time cancellation arrives.

Retries need a deliberate failure classification, bounded attempts, backoff/jitter and an idempotency policy. Those reliability mechanisms return in M9/M15 and architecture A3.

---

## 2.11 Fetch has transport, HTTP and body boundaries

A successful fetch promise gives a Response, not necessarily a successful business operation.

**Verified example 24-fetch: HTTP failure is different from fetch rejection**

```javascript
import { createServer } from 'node:http';
const server = createServer((request, response) => {
  response.writeHead(404, { 'content-type': 'application/json', connection: 'close' });
  response.end(JSON.stringify({ error: 'not_found' }));
});
await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', resolve);
});
try {
  const url = 'http://127.0.0.1:' + server.address().port + '/missing';
  const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
  console.log('fetch fulfilled', response.status, response.ok);
  console.log('body', (await response.json()).error);
  try {
    await response.json();
  } catch (error) { console.log('second read', error.name); }
} finally {
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
}
```

Actual output:

```text
fetch fulfilled 404 false
body not_found
second read TypeError
```


The server intentionally returns 404. Fetch fulfills with that response; response.ok is false. A network-level failure or cancellation is a different path that can reject fetch itself.

Reading the response body is another asynchronous operation. JSON parsing can fail, and a body cannot ordinarily be consumed twice. A successful JSON parse still does not validate the application's required data shape.

### Handler decision path

```text
Start fetch with a suitable signal
        |
Fetch rejects? -> classify transport/cancellation failure
        |
Receive Response
        |
Check status/ok -> map upstream HTTP outcome deliberately
        |
Read body -> handle read/parse failure
        |
Validate shape -> apply application rules
        |
Produce own response contract
```

**Resume connection:** calling an LLM, payment API or internal service requires all of these boundaries. “The request completed” does not mean valid output, sufficient permissions or a successful transaction.

The local example proves the 404/body-consumption behavior. It does not exercise TLS, DNS, remote retry handling or every transport failure.

Reference: [MDN Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch).

---

## 2.12 Build a bounded asynchronous worker pool

### Why a join is not capacity control

Suppose an ingestion endpoint receives 20,000 records. Starting every embedding, HTTP or database call at once can exceed connection pools, memory limits, provider capacity or quotas.

A bounded pool allows at most k work calls to remain in flight. It is separate from:

- A rate limit, such as requests per minute.
- A distributed limit across many processes.
- A durable queue.
- Backpressure on an incoming stream.
- Database transaction atomicity.

### Contract of this learning implementation

- Input is a finite, dense array which the caller does not mutate during execution.
- work returns a value or promise, or throws.
- limit is a positive integer.
- Every item produces a fulfilled/rejected outcome record in original input order.
- Individual failures do not stop remaining items.
- The returned promise settles after all items have been processed.
- There is no built-in cancellation, retry, rate window or persistence.

**Verified example 25-bounded: A bounded worker pool collects outcomes in input order**

```javascript
async function mapSettledLimit(items, limit, work) {
  if (!Number.isInteger(limit) || limit < 1) throw new RangeError('limit');
  const results = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (cursor < items.length) {
      const index = cursor++;
      try {
        const value = await work(items[index], index);
        results[index] = { status: 'fulfilled', value };
      } catch (reason) {
        results[index] = { status: 'rejected', reason };
      }
    }
  }
  await Promise.all(Array.from(
    { length: Math.min(limit, items.length) }, () => worker()
  ));
  return results;
}
let active = 0;
let peak = 0;
const results = await mapSettledLimit([1, 2, 3, 4, 5], 2, async id => {
  active++;
  peak = Math.max(peak, active);
  try {
    await Promise.resolve();
    if (id === 3) throw new Error('bad row');
    return id * 10;
  } finally { active--; }
});
console.log('peak', peak, 'active at end', active);
console.log(results.map(result => result.status === 'fulfilled'
  ? result.value : result.reason.message).join(','));
console.log('empty', (await mapSettledLimit([], 2, () => 0)).length);
try { await mapSettledLimit([1], 0, () => 0); }
catch (error) { console.log(error.name); }
```

Actual output:

```text
peak 2 active at end 0
10,20,bad row,40,50
empty 0
RangeError
```


### Walk through the mechanism

```text
cursor = next unclaimed input index

worker 1: claim index -> await work -> record outcome -> claim next
worker 2: claim index -> await work -> record outcome -> claim next
...
worker k: claim index -> await work -> record outcome -> claim next

join workers -> return results in original index slots
```

The cursor increment happens in a synchronous segment before await. In this one JavaScript context, two workers do not interleave inside that increment. That is not a shared-memory algorithm for multiple worker threads.

Each worker awaits the current item's work before claiming another, which establishes the limit. A synchronously thrown error is caught by the same per-item catch as a rejected promise.

The test demonstrates peak two, successful ordering, one rejected item, zero active work at completion, empty input and invalid limit.

### What would change in production?

- **Cancellation:** stop claiming new items and pass a signal to active operations; define whether to wait for their cleanup.
- **Fail-fast:** define whether rejection stops new claims. Active operations still need ownership and may already have side effects.
- **Retries:** avoid monopolizing slots indefinitely; preserve an attempt budget and idempotency.
- **Huge input:** consume an iterator/stream and emit bounded results instead of keeping every result in memory.
- **Fairness:** avoid one tenant occupying every slot.
- **Multiple replicas:** a local limit of two per process is not a global limit of two.
- **Observability:** track active count, queue length, failures, duration and cancellation.

This implementation deliberately collects all outcomes. It is useful for learning and a small finite batch; the listed extensions require explicit contracts.

### Capacity estimate

If average service time is 0.2 seconds, concurrency 10 suggests an idealized completion capacity around 10/0.2 = 50 operations/second while slots stay occupied. This is a planning estimate, not a guarantee: timeouts, contention, long tails, downstream queues and provider rate limits matter.

A provider permitting 60 calls/minute can still reject a burst from a pool with only two active calls. Rate and concurrency control solve different constraints.

---

## 2.13 Logical races and adapting callbacks

### One thread does not make a workflow atomic

**Verified example 26-lost-update: One JavaScript thread can still have a logical race**

```javascript
let stock = 2;
async function reserve() {
  const read = stock;
  await Promise.resolve();
  stock = read - 1;
}
await Promise.all([reserve(), reserve()]);
console.log('two reservations; stored stock', stock);
stock = 2;
await reserve();
await reserve();
console.log('sequential stored stock', stock);
```

Actual output:

```text
two reservations; stored stock 1
sequential stored stock 0
```


Both calls read stock=2 before either writes. Each later writes 1. Two successful reservations were attempted, but the stored stock reflects only one decrement.

```text
A reads 2
B reads 2
A suspends / B suspends
A writes 1
B writes 1
```

Await splits the read-modify-write workflow into separate execution segments. The absence of simultaneous JavaScript instructions does not preserve the business invariant.

Running these two calls sequentially repairs this particular local trace. It does not coordinate separate requests handled by different processes or machines. Real inventory needs a suitable authoritative atomic operation/transaction/constraint, covered in DBMS, M13 and the booking design.

An in-process mutex may coordinate one process; it is not automatically distributed coordination.

### Convert a callback API once, near its boundary

**Verified example 27-adapter: Adapt an error-first callback at the boundary**

```javascript
function legacyLookup(id, callback) {
  queueMicrotask(() => {
    if (id !== 7) callback(new Error('missing'));
    else callback(null, { id });
  });
}
function lookup(id) {
  return new Promise((resolve, reject) => {
    legacyLookup(id, (error, row) => {
      if (error) { reject(error); return; }
      resolve(row);
    });
  });
}
console.log((await lookup(7)).id);
try { await lookup(8); }
catch (error) { console.log(error.message); }
```

Actual output:

```text
7
missing
```


The adapter translates the error-first convention into promise rejection/fulfillment. Consumers can then use one promise-based composition model.

Node's util.promisify supports conventional compatible error-first APIs, with receiver and custom-signature considerations. Prefer the library's native promise API when it supplies one.

Do not assume every callback API is one-shot error-first: event streams, progress callbacks and multiple success values may need a different abstraction.

Reference: [Node util.promisify](https://nodejs.org/download/release/v22.14.0/docs/api/util.html#utilpromisifyoriginal).

---

## 2.14 Apply the model to a backend aggregation endpoint

Imagine a profile page that requires a user profile but can render without recommendations.

### State the contract before picking a combinator

| Dependency | Requirement | Failure policy |
| --- | --- | --- |
| Profile | Required | Fail the overall operation |
| Recommendations | Optional | Return a visible unavailable state |
| Both | Independent after authorization | May start concurrently |

The real application must verify identity and authorize the profile first. The following demonstration starts after that boundary; it does not implement authentication.

**Verified example 28-aggregate: Required and optional dependencies need different contracts**

```javascript
async function profile() { return { id: 7 }; }
async function recommendations() { throw new Error('upstream unavailable'); }
async function summary() {
  const [user, suggestions] = await Promise.all([
    profile(),
    recommendations().then(
      value => ({ status: 'ok', items: value }),
      () => ({ status: 'unavailable', items: [] })
    )
  ]);
  return { user, suggestions };
}
console.log(JSON.stringify(await summary()));
```

Actual output:

```text
{"user":{"id":7},"suggestions":{"status":"unavailable","items":[]}}
```


The optional call converts its own failure into a deliberate result shape. The required call keeps its rejection behavior, so the all join still fails if the profile fails.

“Unavailable” is distinguishable from “successfully returned no suggestions.” Silently replacing every error with an empty array would erase that distinction.

### Build path for a real endpoint

1. Validate inputs and establish identity/permission.
2. Establish a request deadline and cancellation ownership.
3. Start independent required/optional calls under capacity limits.
4. Check transport, HTTP, body and schema boundaries.
5. Map optional failures according to the product contract.
6. Await required completion and cleanup.
7. Return one response; retain enough logs/metrics to diagnose degraded results.

**Architecture connection:** parallel calls can reduce the critical path, but they increase fan-out and can amplify downstream load. Partial failure, shared deadlines and bounded capacity are design decisions, not syntax preferences.

### Resume connections

| Resume area | Why M2 matters |
| --- | --- |
| Node/Express APIs | Completion ownership and error propagation |
| Data ingestion | Per-item outcomes, bounds and duplicate work |
| AI/embedding calls | Deadlines, quotas, cancellation and validation |
| Payments/webhooks | Uncertain outcomes; retry/idempotency boundaries |
| React/Next data fetching | Stale responses, cancellation and dependency order |
| Distributed architecture | Partial failure and independently progressing operations |

For stale UI responses, a newer request can finish before an older one. Cancellation or a request-version check can prevent obsolete results from replacing current state. React-specific integration belongs in M20; the underlying race begins here.

---

## Must remember

1. Async describes later completion; it does not imply CPU parallelism.
2. A callback can be synchronous or asynchronous according to its API.
3. Returning from a later callback does not return from the original caller.
4. A promise executor runs synchronously.
5. Resolved can mean adopting a still-pending promise.
6. Every then creates a new promise.
7. Return/adopt dependent work so its completion stays connected.
8. A catch that returns a value converts failure into fulfillment.
9. A normal finally preserves the earlier outcome; failed cleanup can replace it.
10. An async function's prefix runs immediately.
11. Await suspends its continuation, not the whole process.
12. Awaiting a non-promise still yields to a later continuation.
13. forEach does not join callback promises.
14. Calling operations starts them; Promise.all joins their outcomes.
15. all preserves input order and does not roll back or cancel.
16. any needs one fulfillment; race accepts the first settlement.
17. Microtasks can queue more microtasks and starve host work.
18. Node ordering depends on context; label ESM/CommonJS.
19. A timeout race stops waiting, not necessarily the work.
20. Cancellation requires API cooperation and is not rollback.
21. HTTP errors can arrive through a fulfilled fetch promise.
22. A local concurrency limit is neither a rate limit nor a global limit.
23. Async workflows can race across await even on one JavaScript thread.
24. Every unfinished operation needs an owner and a failure policy.

---

## Common wrong answers

| Wrong claim | Correction |
| --- | --- |
| “Async means a new thread runs my function.” | Synchronous segments still run in their execution context |
| “Promise executor runs later.” | It runs during construction |
| “Resolved always means fulfilled.” | Resolution can adopt a pending promise |
| “resolve stops the executor.” | Remaining synchronous statements still run |
| “I started the promise, so my caller will wait.” | The caller must adopt/await/join it |
| “catch just logs and keeps the rejection.” | Returning normally recovers the chain |
| “The rejection argument of then catches that then's success handler.” | The thrown error rejects the next promise |
| “finally replaces success with whatever it returns.” | Ordinary returns are ignored; failures can replace the outcome |
| “return await is always pointless.” | Local error/cleanup boundaries can require it |
| “await forEach waits for every async callback.” | forEach ignores returned promises |
| “Promise.all runs my function objects.” | It observes supplied values; calls start functions |
| “all cancels the rest on failure.” | Other operations keep running |
| “all is a transaction.” | Composed promises do not provide rollback |
| “race always picks the first success.” | A rejection can win; any seeks fulfillment |
| “A zero-delay timer runs immediately.” | It runs later under host scheduling rules |
| “nextTick always wins in every context.” | Top-level ESM and CJS traces differ |
| “await Promise.resolve guarantees an I/O turn.” | It can continue within a microtask drain |
| “Timeout means the write did not happen.” | The write may still finish or already be committed |
| “AbortController cancels any promise.” | The underlying operation must support the signal |
| “fetch rejects on every 404/500.” | HTTP errors normally produce a Response |
| “Two active calls enforce a per-minute quota.” | Concurrency and rate are different limits |
| “Single-threaded means race-free.” | Read/await/write sequences can lose updates |
| “A logging catch makes a durable job.” | Process exit can still lose in-process work |

---

## Interview Q&A bank

**Q1. What is asynchronous programming?**
It lets the caller proceed before an operation's result is ready, then observe completion through a defined mechanism.
**Follow-up:** Does it always imply another thread? No; inspect the host/API.

**Q2. Concurrency vs parallelism?**
Concurrency is overlapping progress; parallelism is simultaneous execution on separate resources.
**Follow-up:** What does example 11 measure? In-flight calls, not CPU parallelism.

**Q3. What is a promise?**
An object representing an eventual outcome, with composition methods and pending/fulfilled/rejected states.
**Follow-up:** Is it lazy? Not inherently; creating/calling the underlying operation may start work immediately.

**Q4. When does the executor run?**
Synchronously during construction; reaction handlers run asynchronously.
**Follow-up:** Does resolve terminate it? No.

**Q5. Resolved vs fulfilled?**
Resolution can lock a promise to another pending outcome. Fulfilled means it has successfully settled with a value.
**Follow-up:** Explain example 03's false output.

**Q6. What does then return?**
A new promise determined by the handler's return, adoption or throw.
**Follow-up:** What if the handler returns nothing? Successful undefined unless it throws.

**Q7. Why must you return a dependent promise?**
So the outer completion and failure include that operation.
**Follow-up:** What is a floating promise? Work disconnected from the expected ownership/composition path.

**Q8. Does catch always preserve failure?**
No. Returning normally recovers; throwing continues failure.
**Follow-up:** Why can an empty catch cause a false success response?

**Q9. What does finally do?**
It provides cleanup while normally preserving the earlier outcome; throwing/rejecting cleanup changes the result.
**Follow-up:** Can asynchronous cleanup delay completion? Yes, if returned/adopted.

**Q10. What does async/await change?**
It expresses promise-based control flow directly. An async call returns a promise, and await suspends that function's continuation.
**Follow-up:** Does its prefix run now? Yes.

**Q11. Does await block Node?**
Waiting at await allows other work to progress; synchronous computation before/after it can still block the JavaScript thread.
**Follow-up:** Why doesn't async fix a huge loop?

**Q12. Why use return await inside try/catch?**
It lets that local catch observe eventual rejection instead of only forwarding the promise.
**Follow-up:** Trace example 09.

**Q13. Why does await forEach fail as a join?**
forEach returns undefined and ignores callback promises.
**Follow-up:** Give sequential and bounded alternatives.

**Q14. When should calls be sequential?**
When results, ordering rules or resource constraints require it.
**Follow-up:** Is independent automatically unlimited? No.

**Q15. What does Promise.all guarantee?**
All fulfillment values in input order, or a rejected aggregate when an input rejection determines it.
**Follow-up:** Are other writes rolled back? No.

**Q16. allSettled vs all?**
allSettled collects every input's outcome; all represents a requirement that all succeed.
**Follow-up:** Does collecting all outcomes decide the business failure policy? No.

**Q17. any vs race?**
any seeks the first fulfillment and fails only if all reject. race follows the first settlement, including rejection.
**Follow-up:** What happens for empty input? any rejects; race remains pending.

**Q18. What is a microtask?**
A deferred unit processed at a microtask checkpoint, used by promise reactions and queueMicrotask.
**Follow-up:** Can repeatedly adding microtasks delay timers? Yes.

**Q19. Can I always rank nextTick before promises?**
No. Context matters; the supplied top-level ES-module and CommonJS traces differ.
**Follow-up:** What details do you request before predicting output? Runtime/version, module mode and scheduling location.

**Q20. Is setTimeout(fn, 0) immediate?**
No. It schedules later host work subject to readiness and the host's scheduling rules.
**Follow-up:** Is setImmediate vs timer ordering universal at top level? No.

**Q21. Is Promise.race a cancellation primitive?**
No. It selects an observed outcome; losing work can continue.
**Follow-up:** How would you request cancellation? Pass an AbortSignal to an API that supports it.

**Q22. Does cancellation mean rollback?**
No. It requests stopping supported work, and remote side effects may already exist.
**Follow-up:** What makes a retry safe after uncertainty? A defined idempotency/reconciliation contract.

**Q23. Why does fetch fulfill for 404?**
Fetch completion and HTTP success are separate; inspect status/ok before interpreting the body.
**Follow-up:** Can body parsing fail separately? Yes.

**Q24. What is bounded concurrency?**
A cap on simultaneously in-flight operations.
**Follow-up:** Why is it not a rate limit? A short operation can create many calls per unit time even under a low in-flight cap.

**Q25. Can single-threaded JavaScript have a race?**
Yes. Another continuation can run between an earlier read and later write across await.
**Follow-up:** Why doesn't a local mutex solve multi-process inventory?

**Q26. How would you combine required and optional upstream calls?**
State their failure contracts, start permitted independent work together, preserve required failures and expose optional degradation deliberately.
**Follow-up:** What budget applies? An overall deadline with capacity and cancellation ownership.

---

## Practice

1. **Trace the queues.** Add a second nested queueMicrotask to example 17. Predict the output before running it.
2. **Repair completion.** Return child in example 05. Explain why the controlling release must now be triggered independently before the joined await can finish.
3. **Choose a policy.** Three independent notifications must each appear in a delivery report. Choose a combinator and define per-recipient status.
4. **Write two versions.** Load a profile, then use its organization ID for permissions. Explain why starting permissions before the ID exists is not a valid optimization.
5. **Bound a batch.** Modify example 25 to use limit three. Keep result order and per-item failures; demonstrate that the peak never exceeds three.
6. **Design cancellation.** On paper, add a signal to the bounded pool. Define unstarted-item status, active-operation behavior and what the caller awaits.
7. **Explain uncertainty.** A checkout timed out after sending a payment request. List what is known, what remains unknown and what evidence is needed before retrying.
8. **Find the race.** Add a stock-positive check to example 26 with initial stock one. Can both calls report success? Draw the interleaving.
9. **Classify failures.** For a remote AI call, distinguish network rejection, HTTP 429, invalid JSON, wrong schema and a valid refusal/degraded response.
10. **Defend an architecture.** A dashboard calls eight services. Explain required/optional dependencies, shared deadline, fan-out limits and degradation telemetry.

### Answer checkpoints

- **2:** blindly awaiting the repaired outer chain before releasing its gate creates a dependency cycle in this artificial demonstration.
- **3:** allSettled can collect outcomes; reporting still needs meaningful recipient/error classifications.
- **4:** organization identity is a dependency. Independent work after that value becomes available can overlap.
- **5:** test the active count and retain finally decrementing it on both success and failure.
- **6:** cancellation is a contract change; “reject now” does not prove active operations have stopped.
- **7:** no response proves only a missing observed response. Query status/use idempotency according to the payment contract.
- **8:** both can read one, pass the check and later write zero. A check separated from its write is not an atomic reservation.
- **9:** each boundary needs a deliberate policy; successful parsing is not semantic validation.
- **10:** independently multiplying concurrency in each request and each replica can overload downstreams.

---

## Exit checklist

- [ ] I can distinguish asynchronous waiting, concurrency and parallelism.
- [ ] I can explain why callbacks do not provide a delayed synchronous return.
- [ ] I can trace executor vs promise-handler execution.
- [ ] I can distinguish resolution from fulfillment.
- [ ] I can connect dependent work using return/await.
- [ ] I can explain catch recovery and finally failure.
- [ ] I can use a local await when a local catch must observe rejection.
- [ ] I can repair async forEach and async filter mistakes.
- [ ] I can choose sequential, concurrent or bounded composition.
- [ ] I know all four combinators and their empty-input behavior.
- [ ] I can trace the stated microtask example.
- [ ] I label Node version, module context and callback location before predicting order.
- [ ] I can explain why CPU work remains blocking inside async.
- [ ] I can distinguish timeout, cancellation and rollback.
- [ ] I can distinguish fetch, HTTP, body and schema errors.
- [ ] I can implement and explain the bounded pool's contract and limits.
- [ ] I can reproduce a lost update across await.
- [ ] I can map required/optional dependencies to explicit outcomes.
- [ ] I can run all 28 examples and explain what they have not verified.

---

## Next

[M3: TypeScript Fundamentals](/docs/resume-skills/typescript-fundamentals) builds on JavaScript runtime behavior to understand what static types check, what disappears at runtime, and why external data still needs validation.

M4 then connects this asynchronous model to Node.js internals. The architecture track will use these ideas for service fan-out, deadlines, capacity and reliable workflows after the API/data prerequisites.

### Sources and reproducible evidence

- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise), [promise composition](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises), [async functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function) and [await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await).
- [MDN all](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all), [allSettled](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled), [any](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/any), [race](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/race) and [finally](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/finally).
- [MDN microtasks](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide) and [Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch).
- [Node v22.14.0 process](https://nodejs.org/download/release/v22.14.0/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), [timers](https://nodejs.org/download/release/v22.14.0/docs/api/timers.html), [globals/AbortSignal](https://nodejs.org/download/release/v22.14.0/docs/api/globals.html#class-abortsignal) and [util.promisify](https://nodejs.org/download/release/v22.14.0/docs/api/util.html#utilpromisifyoriginal).
- [Node event-loop guide](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick): phase/version context; a fuller Node-specific treatment follows in M4.
- Original source/verification: examples/resume-skills/module-2-async-javascript/cases.json, verify.mjs, results.json and verification-output.txt. Every numbered example embeds its preserved source and actual captured output.
