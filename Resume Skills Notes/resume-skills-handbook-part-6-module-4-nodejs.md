# Resume Skills Placement Handbook — Part 6
# Module 4: Node.js — What It Is and How It Works

**Module 4 · 4–5 hours · Tier 1 · Requires: M0, M1 and M2; M3 is useful for later typed applications**

---

## Why this module matters

The resume says Node.js and Express. An interviewer can start with “What is Node?” and quickly reach “Why did your server stop responding while only one request was doing expensive work?”

A useful answer connects the runtime to the application: where JavaScript executes, where waiting happens, which resource is shared, and how the response reaches the client.

> **Node.js supplies the runtime capabilities for a backend. Your application supplies routes, permissions, business rules and data operations. Its ability to overlap I/O does not remove CPU, memory, downstream-capacity or correctness limits.**

This chapter answers the original Node.js example directly, then develops the internals and a small working server.

**Verification:** twenty numbered cases ran in isolated Node.js **v22.14.0** processes. Nineteen use ES modules; example 03 uses CommonJS. Example 20 runs sixteen real loopback HTTP checks. Source, fixtures and actual outputs are preserved in examples/resume-skills/module-4-nodejs/.

### How to run the material

From the repository root:

```powershell
node examples/resume-skills/module-4-nodejs/verify.mjs
node examples/resume-skills/module-4-nodejs/verify.mjs 11-backpressure
node examples/resume-skills/module-4-nodejs/verify-server.mjs
node examples/resume-skills/module-4-nodejs/start.mjs
```

The final command manually starts the learning server on **127.0.0.1:3104**. Stop it with Ctrl+C. It is separate from the notes website on port 3000. If 3104 is occupied, choose another manual port in start.mjs.

The verifier sets each case's working directory to the example folder so relative fixture imports resolve. Some cases require their companion fixture/module files; use the preserved runner rather than copying only those statements elsewhere.

No packages, external APIs, credentials or database are required.

---

## 4.1 What Node.js is

### The direct answer

Node.js is an open-source, cross-platform JavaScript runtime built around the V8 engine and host capabilities such as networking, files, timers and processes. It allows JavaScript applications to run outside a browser, including backend servers and command-line programs.

It is not a programming language, a database or a web framework.

| Name | Responsibility |
| --- | --- |
| JavaScript | Language semantics: values, functions, scope, objects, promises |
| V8 | Executes JavaScript and manages engine-level execution/memory |
| Node.js | Embeds the engine and provides runtime APIs/integration |
| Express | Web framework built on Node's capabilities |
| Your backend application | Routes, validation, permissions, rules and orchestration |
| PostgreSQL/MongoDB | Separate data systems with their own execution and storage guarantees |

A Node application can be an HTTP server, but Node itself is a runtime. An HTTP listener is one capability the program chooses to use.

### What “outside the browser” means

**Verified example 01-host: Node supplies host capabilities around V8**

```javascript
console.log(process.release.name, typeof process.pid);
console.log('versions', Boolean(process.versions.v8), Boolean(process.versions.uv));
console.log('DOM globals', typeof window, typeof document);
```

Actual output:

```text
node number
versions true true
DOM globals undefined undefined
```


The JavaScript engine does not provide a page or DOM by itself. Node exposes process and other server/runtime facilities. It also implements selected web-compatible APIs, such as fetch, without becoming a browser.

A script using document.querySelector cannot assume document exists in Node. Conversely, browser code cannot assume it can read arbitrary local server files using Node's filesystem APIs.

References: [Node introduction](https://nodejs.org/learn/getting-started/introduction-to-nodejs) and [V8 introduction](https://nodejs.org/learn/getting-started/the-v8-javascript-engine).

### Thirty-second interview answer

“Node.js is a JavaScript runtime, not a framework. It uses V8 to execute JavaScript and provides networking, file and process APIs. A backend built with it can overlap supported I/O operations while its JavaScript handlers run in short execution segments. CPU-heavy JavaScript still blocks that executing thread, so workload and resource limits matter.”

---

## 4.2 Why use it in a backend?

A backend receives requests, validates inputs, checks identity/permissions, calls data systems or other services, applies rules and returns results. Many such requests spend substantial time waiting for external operations.

Node's asynchronous APIs can make that waiting overlap. A shared language can also help teams reuse knowledge and selected code across frontend and backend, although shared source does not establish runtime validation or service compatibility.

| Workload characteristic | Why Node can be useful | What still needs design |
| --- | --- | --- |
| Many network waits | Supported I/O can overlap | Connection pools, deadlines and capacity |
| API aggregation | Promise-based composition | Required/optional dependencies and partial failure |
| Streaming transfers | Stream APIs connect producers/consumers | Backpressure, errors and client disconnects |
| Persistent connections/events | Event-driven networking APIs | Connection lifecycle, fan-out and state |
| JavaScript/TypeScript team | Familiar language and tooling | Runtime boundaries and deployment discipline |
| Command-line tooling | Files/process/package ecosystem | Input handling and portability |

This is workload reasoning, not a claim that Node is always faster than another runtime. Compare actual implementations under a defined load when performance determines a choice.

A backend built with another language can also use asynchronous I/O. Node's benefit must be explained in terms of the application, team and constraints.

---

## 4.3 Runtime architecture: V8, native APIs, libuv and OS

### The conceptual layers

```text
Application JavaScript / Express handlers
                |
       Node's JavaScript-facing APIs
                |
    Native bindings and supporting libraries
       |                          |
       |                          +--> libuv worker pool for supported work
       |
       +--> OS networking / I/O event mechanisms
                |
      Completion/readiness delivered
                |
       JavaScript continuation/callback

V8 executes JavaScript segments and handles engine responsibilities.
libuv supplies event-loop/I/O infrastructure; it is not the JS engine.
```

This is a responsibility diagram, not a claim that every Node API passes through exactly the same native path. Different APIs use different supporting libraries and operating-system mechanisms.

### What runs where?

| Operation | Typical execution path in this model |
| --- | --- |
| A handler's loop, JSON.parse/stringify, ordinary regex | JavaScript/native work on the calling thread; can block its loop |
| Socket network I/O | OS readiness/completion mechanisms integrated with the event loop |
| Promise then/await continuation | JavaScript microtask processing; not automatically a worker-pool job |
| Many asynchronous filesystem operations | libuv filesystem work, commonly using its worker pool |
| Async PBKDF2 and selected crypto operations | Native work using the worker pool |
| DNS lookup via dns.lookup | OS name resolution using a worker-pool path |
| DNS resolve APIs | A different asynchronous DNS path; do not equate all DNS APIs |
| Your JavaScript in a Worker | Another JavaScript execution context/thread |

Network I/O is not normally “one worker-pool thread waiting per socket.” Windows and Unix platforms have different underlying mechanisms, so use the readiness/completion description rather than a single OS-specific story.

The [libuv design overview](https://docs.libuv.org/en/v1.x/design.html), [Node filesystem API](https://nodejs.org/download/release/v22.14.0/docs/api/fs.html) and [DNS API](https://nodejs.org/download/release/v22.14.0/docs/api/dns.html) explain the relevant paths.

### The internal worker pool is a bounded shared resource

libuv's pool has a default size of four unless configured otherwise. It is shared across event loops that use that pool in the process. Pool work can queue even while the main JavaScript loop remains able to execute short callbacks.

Increasing UV_THREADPOOL_SIZE is not a universal optimization. More threads consume resources and can increase contention. First establish that pool queueing is relevant and measure the workload.

A JavaScript Worker is not a slot in this internal pool. Creating Workers does not give each one a private filesystem/crypto pool.

Reference: [libuv thread-pool documentation](https://docs.libuv.org/en/v1.x/threadpool.html).

**Verified example 19-native-work: A native asynchronous operation still returns through JavaScript**

```javascript
import { pbkdf2 } from 'node:crypto';
import { promisify } from 'node:util';
console.log('start');
// Tiny iteration count for API tracing, not a password-storage policy.
const pending = promisify(pbkdf2)('demo', 'salt', 1, 16, 'sha256');
console.log('submitted');
const key = await pending;
console.log('result', Buffer.isBuffer(key), key.length);
```

Actual output:

```text
start
submitted
result true 16
```


The output shows immediate submission followed by a later result. It does not measure which native thread executed the derivation or establish a password-storage policy. The API's documented implementation supplies the pool explanation.

Reference: [Node crypto](https://nodejs.org/download/release/v22.14.0/docs/api/crypto.html).

---

## 4.4 Build a small HTTP server and trace a request

### What the server implements

| Route | Behavior |
| --- | --- |
| GET /health | Small JSON health response |
| GET /api/info | Await a file/dependency read, return UTF-8 byte count |
| GET /download | Stream one fixed fixture file to the response |
| Other method | 405 with Allow: GET |
| Unknown route | 404 |
| Draining mode | Reject newly handled requests with 503 |

The file is selected by the application, not a caller-provided filesystem path. This is a public loopback learning application, with no authentication, database or writable order state.

The health route is a simple readiness-style response for this demonstration. It does not check every dependency or implement a separate production liveness policy.

The fixture is 79,872 bytes. Its size gives the transfer several chunks under the chosen read high-water mark; it is not a memory or throughput benchmark.

### Complete server.mjs

```javascript
import { createServer } from 'node:http';
import { open, readFile } from 'node:fs/promises';
import { pipeline } from 'node:stream/promises';

export const sampleFile = new URL('./fixtures/download.txt', import.meta.url);

function json(response, status, body, headers = {}) {
  response.writeHead(status, { 'content-type': 'application/json; charset=utf-8', ...headers });
  response.end(JSON.stringify(body));
}

export function createStudyServer({
  filePath = sampleFile,
  loadRecord = () => readFile(filePath, 'utf8'),
} = {}) {
  let draining = false;
  async function handle(request, response) {
    if (draining) {
      request.resume();
      json(response, 503, { error: 'draining' }, { connection: 'close' });
      return;
    }
    const { pathname } = new URL(request.url, 'http://localhost');
    if (request.method !== 'GET') {
      request.resume();
      json(response, 405, { error: 'method_not_allowed' }, { allow: 'GET' });
      return;
    }
    if (pathname === '/health') {
      json(response, 200, { status: 'ok' });
      return;
    }
    if (pathname === '/api/info') {
      const text = await loadRecord();
      if (!response.destroyed) json(response, 200, { bytes: Buffer.byteLength(text, 'utf8') });
      return;
    }
    if (pathname === '/download') {
      // Open before headers so a missing file can still become a JSON 404.
      const file = await open(filePath, 'r');
      try {
        const stat = await file.stat();
        response.writeHead(200, {
          'content-type': 'text/plain; charset=utf-8',
          'content-length': String(stat.size),
          'content-disposition': 'attachment; filename="study.txt"',
        });
        // Keep ownership of the descriptor here; always close it in finally.
        await pipeline(file.createReadStream({ autoClose: false, highWaterMark: 16 * 1024 }), response);
      } finally {
        await file.close();
      }
      return;
    }
    json(response, 404, { error: 'not_found' });
  }

  const server = createServer((request, response) => {
    request.on('error', () => response.destroy());
    response.on('error', () => {}); // pipeline/handle owns the operation's failure.
    void handle(request, response).catch(error => {
      if (response.destroyed || response.writableEnded) return;
      if (response.headersSent) {
        response.destroy(); // A completed/partial response cannot be replaced with JSON.
        return;
      }
      if (error.code === 'ENOENT') json(response, 404, { error: 'file_missing' });
      else json(response, 500, { error: 'internal_error' });
    });
  });
  return { server, beginDrain() { draining = true; } };
}
```

start.mjs binds the listener; the verifier instead uses an available ephemeral loopback port.

### Trace GET /api/info

```text
Client sends HTTP request
  -> Node HTTP layer parses request metadata
  -> request event invokes our listener with IncomingMessage/ServerResponse
  -> handler checks draining/method/path
  -> loadRecord starts its asynchronous operation
  -> handler continuation waits; JavaScript can serve other work
  -> read completes; promise continuation resumes
  -> Buffer.byteLength calculates byte count
  -> response headers/body are written
  -> response ends
```

The request object is a readable stream; the response object is writable. Node does not automatically parse a JSON request body just because the content type says JSON.

Express adds routing/middleware conveniences in M5. It does not replace the runtime or make synchronous work non-blocking.

Reference: [Node HTTP API](https://nodejs.org/download/release/v22.14.0/docs/api/http.html).

### Why the event listener explicitly owns rejection

createServer receives a callback. It does not make the promise from an arbitrary async request listener become an HTTP error response automatically.

The wrapper calls handle and attaches a catch. Before headers are sent, the error can become a deliberate JSON response. After a partial response starts, replacing it with a fresh 500 JSON body is no longer valid; the example closes that response instead.

This implements one explicit application error contract. A production service also needs diagnostic logging and operational policies.

---

## 4.5 How one server handles multiple requests

### Single JavaScript execution context, overlapping waits

```text
Request A: enter -> start dependency -> wait ------------------> resume -> end
Request B:         enter -> start dependency -> wait ---------> resume -> end
Health:                            enter -> respond
```

A and B are both in flight. That does not require their JavaScript statements to execute simultaneously or require a fresh application thread per request.

The verifier injects a gate-controlled dependency. It waits until two handlers have reached that dependency, then checks /health before releasing either.

**Verified example 20-http: The learning HTTP server passes its route and concurrency checks**

```javascript
await import('./verify-server.mjs');
```

Actual output:

```text
PASS HTTP health
PASS HTTP async-file-info
PASS HTTP streamed-download
PASS HTTP fixed-file-selection
PASS HTTP unknown-route
PASS HTTP method-and-allow
PASS HTTP draining-response
PASS HTTP two-requests-in-flight
PASS HTTP health-progresses-during-wait
PASS HTTP drain-stops-new-work
PASS HTTP in-flight-work-completes
PASS HTTP listener-closed
PASS HTTP missing-file-before-headers
PASS HTTP missing-file-async-read
PASS HTTP async-failure-mapped
PASS HTTP healthy-after-request-failure
Verified 16 HTTP checks
```


These checks establish observed overlap and health progress during a controlled asynchronous wait. They do not show that health remains responsive during a long synchronous CPU loop.

### What the checks cover

- Successful JSON routes and exact byte counts.
- The streamed download's body, length and content type.
- Fixed file selection despite an irrelevant query parameter.
- Unknown route and unsupported method/Allow.
- Two operations simultaneously waiting.
- Health progress while those operations remain waiting.
- New work refused during draining while accepted work completes.
- Listener closure and request-error isolation.
- Missing files before response headers.
- An async dependency rejection mapped to a generic error response.

No latency/throughput claim follows from sixteen passing functional checks.

---

## 4.6 Blocking, non-blocking and two different bottlenecks

### Synchronous vs asynchronous file APIs

**Verified example 05-files: A promise-based file read has a later result**

```javascript
import { readFile } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
const file = new URL('./fixtures/download.txt', import.meta.url);
const bytes = readFileSync(file); // Synchronous baseline.
console.log('sync', Buffer.isBuffer(bytes), bytes.length);
const pending = readFile(file, 'utf8');
console.log('submitted', typeof pending.then);
const text = await pending;
console.log('async', text.startsWith('Node.js'), Buffer.byteLength(text));
```

Actual output:

```text
sync true 79872
submitted function
async true 79872
```


readFileSync returns bytes only after completing its synchronous call. The promise-based call returns an eventual result instead.

readFile still loads the whole file into memory. “Async” and “streaming” are different properties.

A small synchronous read at startup has different impact from performing a large synchronous read in every request. Judge where it runs, size, frequency and the resulting delay.

### Event-loop blocking

While a handler performs a large loop, parses/stringifies a huge JSON value or executes an expensive regular expression, that JavaScript context cannot service another ordinary callback.

Adding async to that function or putting the work inside a Promise executor does not move it elsewhere. M2 already demonstrated this at the language-control-flow level.

### Worker-pool saturation

A large number of costly pool jobs can queue behind occupied workers. That is different from a busy JavaScript loop.

| Symptom hypothesis | Evidence to investigate |
| --- | --- |
| Long synchronous JavaScript work | CPU profile, event-loop delay, request traces |
| Pool jobs queueing | Timings of relevant filesystem/crypto/DNS work and controlled load |
| Database pool exhaustion | Checkout wait time, active connections, slow queries |
| Too much network fan-out | In-flight count, timeout/error rate, downstream capacity |
| Memory pressure | RSS, heap/external memory, allocation/GC behavior |

An idle-looking JavaScript loop does not prove the whole application has spare capacity.

### Chunking is cooperative scheduling, not parallel execution

**Verified example 07-yield: Host-level yielding lets other callbacks progress**

```javascript
import { setImmediate as yieldToLoop } from 'node:timers/promises';
setImmediate(() => console.log('observer'));
let total = 0;
for (let chunk = 0; chunk < 3; chunk++) {
  total += chunk;
  console.log('chunk', chunk);
  await yieldToLoop();
}
console.log('total', total);
```

Actual output:

```text
chunk 0
observer
chunk 1
chunk 2
total 3
```


The observer can run between chunks because setImmediate yields to host scheduling. Each chunk still executes on the same JavaScript thread.

Repeated await Promise.resolve can stay within a microtask drain and is not an equivalent guarantee of an I/O turn.

Use Workers/processes for suitable CPU offloading, and a bounded queue/pool so offloading does not create an unbounded backlog.

Reference: [Don't Block the Event Loop or Worker Pool](https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop).

---
## 4.7 Event-loop phases and scheduling context

### What the loop coordinates

Node uses event-loop machinery to process ready work and invoke callbacks. The loop does not execute all requests simultaneously; it coordinates progress across short JavaScript execution segments and supported external operations.

| Phase/category | Relevant responsibility |
| --- | --- |
| Timers | Eligible timeout/interval callbacks |
| Pending callbacks | Certain deferred system callbacks |
| Idle/prepare | Internal work |
| Poll | I/O processing and waiting under the loop's rules |
| Check | setImmediate callbacks |
| Close callbacks | Certain closing-resource callbacks |

This is a responsibility table, not a guarantee that every iteration visits useful work in every category or a complete callback ordering algorithm.

Modern libuv timer scheduling changed around Node 20. Avoid applying an old diagram's exact timer/immediate order to a different runtime without checking its rules.

### Predict inside a named I/O callback

**Verified example 06-io-order: Ordering inside a file-I/O callback**

```javascript
import { readFile } from 'node:fs';
readFile(new URL('./fixtures/download.txt', import.meta.url), error => {
  if (error) throw error;
  console.log('I/O callback');
  setTimeout(() => console.log('timer'), 0);
  setImmediate(() => console.log('immediate'));
  process.nextTick(() => console.log('nextTick'));
  Promise.resolve().then(() => console.log('promise'));
  queueMicrotask(() => console.log('microtask'));
});
```

Actual output:

```text
I/O callback
nextTick
promise
microtask
immediate
timer
```


In this file-I/O callback:

1. The synchronous callback prints I/O callback.
2. The next-tick queue is processed before the shown promise/queueMicrotask work.
3. The promise reaction was queued before the standalone microtask.
4. The immediate scheduled in this I/O context runs before the timer scheduled there.

This is not the same context as top-level ES-module evaluation. M2 demonstrated that top-level ESM and CommonJS can give different promise/nextTick ordering.

**Interview procedure:** ask for Node version, module mode and the location where the work is scheduled before ranking callbacks.

### Timers are not exact deadlines

setTimeout(fn, 0) does not interrupt the running JavaScript segment. Node applies its delay rules and executes an eligible callback when scheduling permits.

setImmediate does not mean “run before every other callback.” Its phase and the scheduling context matter. At top level, do not promise one universal immediate-versus-timer order.

Long nextTick chains or microtask chains can postpone host progress. Use bounded scheduling and host-level yielding when appropriate.

References: [Node event-loop guide](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick), [timers](https://nodejs.org/download/release/v22.14.0/docs/api/timers.html) and [process scheduling context](https://nodejs.org/download/release/v22.14.0/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick).

### EventEmitter is not a background execution engine

**Verified example 02-events: EventEmitter listeners run synchronously**

```javascript
import { EventEmitter } from 'node:events';
const bus = new EventEmitter();
bus.on('job', () => console.log('listener'));
console.log('before emit');
console.log('had listener', bus.emit('job'));
console.log('after emit');
bus.once('done', () => console.log('once'));
bus.emit('done');
bus.emit('done');
try { bus.emit('error', new Error('unhandled event')); }
catch (error) { console.log('caught', error.message); }
```

Actual output:

```text
before emit
listener
had listener true
after emit
once
caught unhandled event
```


emit invokes registered listeners synchronously. A listener can schedule later work, but EventEmitter itself does not move the listener to another thread or automatically await its returned promise.

An error event without an appropriate error listener has special failure behavior. Here emit throws while our try/catch is active.

For a later host-triggered error, a try/catch around the earlier registration is not enough. Handle the API's error events and own any asynchronous work its listener starts.

Reference: [Node events](https://nodejs.org/download/release/v22.14.0/docs/api/events.html).

---

## 4.8 Modules, packages and npm

### CommonJS and ES modules

| Concern | CommonJS | ES modules |
| --- | --- | --- |
| Typical explicit extension | .cjs | .mjs |
| Load syntax | require | Static import or dynamic import |
| Export syntax | module.exports / exports | export |
| Standard local module helpers | require, module, filename/dirname helpers | import.meta and module URLs |
| Binding behavior | Exported values/objects follow ordinary JS access | Imported named bindings are live bindings |
| Top-level await | Not standard CJS top-level syntax | Supported in ESM |

A .js file's interpretation depends on package settings and version-sensitive detection rules. Prefer an explicit package type/extension policy.

Do not memorize “require can never load ESM” as a timeless rule. Interoperability depends on Node version, package exports and whether the ESM graph can be loaded synchronously. Know the system your project uses.

### CommonJS caching and a destructured snapshot

Fixture fixtures/counter.cjs:

```javascript
module.exports = { count: 0, increment() { this.count++; } };
```

**Verified example 03-commonjs: CommonJS caches the exported object for this resolved file**

Context: **CommonJS**; the other cases use ES modules.

```javascript
const first = require('./fixtures/counter.cjs');
const { count: snapshot } = first;
const second = require('./fixtures/counter.cjs');
second.increment();
console.log(first === second, first.count, snapshot);
console.log(typeof module.exports, typeof require);
```

Actual output:

```text
true 1 0
object function
```


Both requires resolve to the same cached exported object in this process. The separately destructured primitive snapshot does not become a live property accessor.

A cache is not an instruction to reload the file on each request. Changing disk contents does not automatically reload an already-loaded module.

### ES-module live bindings

Fixture fixtures/counter.mjs:

```javascript
export let count = 0;
export function increment() { count++; }
```

**Verified example 04-esm: ES-module imports observe live bindings**

```javascript
import { count, increment } from './fixtures/counter.mjs';
console.log('before', count);
increment();
console.log('after', count);
const first = await import('./fixtures/counter.mjs');
const second = await import('./fixtures/counter.mjs');
console.log(first === second, typeof require);
```

Actual output:

```text
before 0
after 1
true undefined
```


The imported count observes changes to the exported binding. Repeated imports of the same resolved module URL here share its module instance.

Different module identities, loaders, Workers or processes can have different instances. Do not treat module caching as shared durable state.

**Backend connection:** storing currentUser in a module-global variable can mix requests. Module scope is not request scope.

References: [CommonJS](https://nodejs.org/download/release/v22.14.0/docs/api/modules.html), [ES modules](https://nodejs.org/download/release/v22.14.0/docs/api/esm.html) and [packages](https://nodejs.org/download/release/v22.14.0/docs/api/packages.html).

### Node vs npm

Node executes the program. npm manages package installation and scripts; it is not the engine or event loop.

| File/concept | Role |
| --- | --- |
| package.json | Package metadata, scripts, dependency declarations and module policy |
| package-lock.json | Recorded resolved dependency tree/integrity metadata for npm |
| node_modules | Installed package contents |
| dependencies | Declared packages used by the application/package |
| devDependencies | Development/build tooling according to the project |
| npm run script-name | Run a named project script |
| npm ci | Install from a compatible lockfile for a clean installation |

A build tool may be a devDependency but still be required during the build stage. “Development dependency” does not mean its code cannot run during installation/build.

### Minimal illustrative package metadata

```json
{
  "name": "node-placement-learning",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node start.mjs",
    "verify": "node verify.mjs"
  }
}
```

The preserved examples use explicit .mjs/.cjs extensions and direct Node commands, so no installation is needed to run them.

A lockfile improves repeatability of the resolved package tree. It does not guarantee identical native binaries or behavior across every platform, Node/npm version and installation policy.

npm ci requires an existing compatible lockfile and fails on relevant manifest/lock mismatches instead of silently updating the lock. Its clean-install behavior can replace installed contents; understand the command before applying it to an existing environment.

References: [package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/), [package-lock.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/) and [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/).

---

## 4.9 Buffers: bytes, text and ownership

### Network and files carry bytes

A Buffer represents byte data and is based on Uint8Array. A JavaScript string is text represented through its own string semantics; its length is not necessarily its UTF-8 byte length.

**Verified example 08-buffer: Buffers are bytes; subarray shares storage**

```javascript
const bytes = Buffer.from('é', 'utf8');
console.log('string units', 'é'.length, 'bytes', bytes.length);
const original = Buffer.from([1, 2, 3]);
const view = original.subarray(0, 2);
const copy = Buffer.from(original);
view[0] = 9;
console.log(original[0], copy[0], Buffer.isBuffer(view));
```

Actual output:

```text
string units 1 bytes 2
9 1 true
```


é occupies one JavaScript UTF-16 code unit here but two bytes in UTF-8. Content-Length and binary protocols need byte counts, not an arbitrary string.length.

Buffer.subarray creates a view sharing storage. Buffer.from(existingBuffer) copies its bytes. The mutation in the example therefore reaches original but not copy.

### Allocation and encodings

- Buffer.from(text, encoding) encodes text.
- buffer.toString(encoding) decodes bytes as text.
- Buffer.alloc(size) creates zero-filled bytes.
- Buffer.allocUnsafe(size) may expose uninitialized contents until overwritten; do not send unwritten bytes as application data.

Choose an encoding deliberately. Binary data should not be converted to UTF-8 merely because a string is convenient.

Reference: [Node Buffer](https://nodejs.org/download/release/v22.14.0/docs/api/buffer.html).

### Chunk boundaries are not character boundaries

**Verified example 09-decoder: UTF-8 characters can cross chunk boundaries**

```javascript
import { StringDecoder } from 'node:string_decoder';
const bytes = Buffer.from('€', 'utf8');
const a = bytes.subarray(0, 1);
const b = bytes.subarray(1);
console.log('naive matches', a.toString('utf8') + b.toString('utf8') === '€');
const decoder = new StringDecoder('utf8');
const text = decoder.write(a) + decoder.write(b) + decoder.end();
console.log('decoder matches', text === '€');
```

Actual output:

```text
naive matches false
decoder matches true
```


Decoding each arbitrary chunk separately can replace an incomplete multibyte character with replacement text. A decoder retains incomplete bytes until the next chunk.

A stream configured for a text encoding can handle this decoding boundary for supported APIs. StringDecoder exposes the mechanism directly here.

Character decoding still does not supply application framing. A TCP chunk need not equal one JSON object, line or application message. Use a suitable parser/framing protocol and input-size limits.

Reference: [StringDecoder](https://nodejs.org/download/release/v22.14.0/docs/api/string_decoder.html).

---

## 4.10 Streams and backpressure

### Four useful stream roles

| Role | Capability | Example |
| --- | --- | --- |
| Readable | Produces chunks | File read, incoming HTTP request |
| Writable | Accepts chunks | File write, outgoing HTTP response |
| Duplex | Can read and write | Socket |
| Transform | Reads input and produces transformed output | Compression |

Streaming permits incremental processing; it does not promise zero buffering or zero memory use.

### Connect a pipeline

**Verified example 10-pipeline: A pipeline connects chunk producers and consumers**

```javascript
import { Readable, Transform, Writable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
const chunks = [];
const upper = new Transform({
  transform(chunk, encoding, callback) {
    callback(null, chunk.toString('utf8').toUpperCase());
  }
});
const sink = new Writable({
  write(chunk, encoding, callback) {
    chunks.push(Buffer.from(chunk));
    callback();
  }
});
await pipeline(Readable.from([Buffer.from('node '), Buffer.from('streams')]), upper, sink);
console.log(Buffer.concat(chunks).toString('utf8'));
```

Actual output:

```text
NODE STREAMS
```


This transform uses ASCII input, so its simple chunk-by-chunk uppercasing is sufficient for the demonstration. It is not a general multibyte text transformation; example 09 explains that boundary.

The sink deliberately collects output to verify it. A real large-file destination would write onward rather than retaining every chunk.

### Backpressure is feedback from a slower consumer

```text
Fast producer -> writable's pending data grows -> write returns false
      |
      +--> stop producing additional writes
                  |
              drain event
                  |
              resume producing
```

A false return does not mean the chunk was rejected. It was accepted into the stream's flow/buffering machinery, and the producer should pause before adding more.

Resending that same chunk merely because write returned false can duplicate data.

**Verified example 11-backpressure: A false write return asks the producer to pause**

```javascript
import { Writable } from 'node:stream';
import { once } from 'node:events';
import { finished } from 'node:stream/promises';
let text = '';
const sink = new Writable({
  highWaterMark: 3,
  write(chunk, encoding, callback) {
    setImmediate(() => { text += chunk.toString(); callback(); });
  }
});
console.log('write returned', sink.write('abc'));
await once(sink, 'drain');
console.log('buffered after drain', sink.writableLength);
const complete = finished(sink, { cleanup: true });
sink.end('d');
await complete;
console.log(text);
```

Actual output:

```text
write returned false
buffered after drain 0
abcd
```


With highWaterMark three and an asynchronous write callback, the three-byte chunk reaches the threshold. After drain, the producer can continue.

highWaterMark is a flow-control threshold, not a universal hard memory cap. It can be measured in bytes or objects depending on stream mode; other stream/OS/application buffers also consume memory.

### Why prefer pipeline for complete flows?

pipeline coordinates backpressure and completion/error handling across the supplied stages. Ordinary pipe also handles flow pressure, but a complete error/cleanup policy needs care.

**Verified example 12-pipeline-error: Pipeline rejects and destroys streams on a write failure**

```javascript
import { Readable, Writable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
const source = Readable.from([Buffer.from('a'), Buffer.from('b')]);
const sink = new Writable({
  write(chunk, encoding, callback) {
    callback(chunk.toString() === 'b' ? new Error('bad chunk') : null);
  }
});
try { await pipeline(source, sink); }
catch (error) { console.log(error.message); }
console.log('destroyed', source.destroyed, sink.destroyed);
```

Actual output:

```text
bad chunk
destroyed true true
```


The failing write rejects the awaited pipeline, and its streams are destroyed. Do not respond with success before the awaited flow has actually completed.

When the destination is an HTTP response, pipeline may destroy the underlying response/socket on failure. A new JSON error response may then be impossible. Validate/open resources before sending headers where practical, and handle partial-transfer outcomes deliberately.

### Compression is another transform

**Verified example 13-compression: A transform can change byte representation**

```javascript
import { Readable, Writable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { createGzip, gunzip } from 'node:zlib';
import { promisify } from 'node:util';
const original = Buffer.from('streamed content');
const output = [];
await pipeline(Readable.from([original]), createGzip(), new Writable({
  write(chunk, encoding, callback) { output.push(Buffer.from(chunk)); callback(); }
}));
const restored = await promisify(gunzip)(Buffer.concat(output));
console.log('round trip', restored.equals(original));
```

Actual output:

```text
round trip true
```


The round trip verifies byte correctness, not an assumed compression ratio or CPU cost. Compression can save network bytes while adding CPU/native-pool work.

### Trace the real file download

```text
Open fixed file
  -> obtain metadata from the opened handle
  -> set response headers
  -> read chunks
  -> pipeline writes to response
  -> downstream pressure slows upstream reads
  -> completion/error
  -> finally closes owned file handle
```

The server does not read the entire download into a Buffer first. The verification client does collect the small fixture to compare exact bytes; distinguish the client's test behavior from the server's transfer implementation.

The learning contract assumes a stable regular fixture file during transfer. It does not implement range requests, authorization or concurrent file-update policies.

Node streams and Web Streams are different APIs. For example, a fetch response body may use Web Streams rather than exposing Node's pipe directly; use documented adapters where needed.

Reference: [Node stream API](https://nodejs.org/download/release/v22.14.0/docs/api/stream.html).

---

## 4.11 Worker threads, processes, cluster and jobs

### Choose the execution and ownership model

| Mechanism | Executes your JavaScript? | State/lifecycle point |
| --- | --- | --- |
| Main JavaScript context | Yes | Shared handler context in that instance |
| libuv internal pool | Runs supported native work | Shared bounded pool; not arbitrary JS task submission |
| Worker thread | Yes, in another execution context | Same process; ordinary message data is cloned unless shared/transferred deliberately |
| Child process | Yes if you launch Node, or another program | Separate process address space/lifecycle |
| Cluster worker | Node application in a child process | Can share server listening arrangements; ordinary app memory is separate |
| Durable job queue | Defines delivery/ownership, not one CPU mechanism | Can survive process loss according to its storage/delivery design |

A queue and a Worker are not competing synonyms. A durable queue may deliver a job that an application executes in a Worker or separate service.

### Complete CPU worker fixture

fixtures/sum-worker.mjs:

```javascript
import { parentPort, workerData, isMainThread } from 'node:worker_threads';
if (!Number.isSafeInteger(workerData.count) || workerData.count < 0) {
  throw new RangeError('count');
}
let sum = 0;
for (let i = 0; i < workerData.count; i++) sum += i;
workerData.tags.push('worker');
parentPort.postMessage({ sum, isMainThread, pid: process.pid, tags: workerData.tags });
```

The verifier supplies a small trusted count. A real job interface needs workload/range limits and an appropriate numeric policy; this example is an execution-model demonstration.

**Verified example 14-worker: A worker executes JavaScript in another thread of this process**

```javascript
import { Worker, isMainThread } from 'node:worker_threads';
const input = { count: 100000, tags: ['main'] };
const worker = new Worker(new URL('./fixtures/sum-worker.mjs', import.meta.url), {
  workerData: input, execArgv: []
});
const exited = new Promise(resolve => worker.once('exit', resolve));
const result = await new Promise((resolve, reject) => {
  worker.once('message', resolve);
  worker.once('error', reject);
});
console.log('sum', result.sum);
console.log('threads', isMainThread, result.isMainThread, 'same PID', result.pid === process.pid);
console.log('cloned tags', input.tags.length, result.tags.length);
console.log('exit', await exited);
```

Actual output:

```text
sum 4999950000
threads true false same PID true
cloned tags 1 2
exit 0
```


The same PID establishes the same process. The worker has its own JavaScript context and can execute CPU work in parallel with other execution resources when the OS schedules it.

workerData was cloned. Pushing a tag in the worker does not push it into the main thread's array.

execArgv: [] prevents the runner's --input-type flag from being inherited by a worker launched from a file. A real application should choose required worker flags explicitly.

### Handle worker failure

**Verified example 15-worker-error: A worker failure has an explicit error and exit path**

```javascript
import { Worker } from 'node:worker_threads';
const worker = new Worker(new URL('./fixtures/sum-worker.mjs', import.meta.url), {
  workerData: { count: -1, tags: [] }, execArgv: []
});
const exited = new Promise(resolve => worker.once('exit', resolve));
const error = await new Promise(resolve => worker.once('error', resolve));
console.log(error.name, await exited);
```

Actual output:

```text
RangeError 1
```


The worker's thrown error is observed through its error event, and its nonzero exit is observed separately. Without an owner/error policy, offloading simply moves an unhandled failure elsewhere.

### Offloading has costs

- Worker startup and initialization take resources.
- Large messages can cost time/memory to clone.
- Transferable data can change ownership; shared memory requires synchronization.
- More active workers than the machine/downstream can support can worsen latency.
- The process still needs admission limits, cancellation policy and cleanup.
- Threads within one process do not provide the full isolation of separate processes.

Use a bounded reusable pool for frequent CPU tasks rather than blindly spawning one Worker per incoming request. A Worker is usually unnecessary merely to wait on an asynchronous socket operation.

Reference: [Node worker_threads](https://nodejs.org/download/release/v22.14.0/docs/api/worker_threads.html).

### Child processes

**Verified example 16-child: A child process has a different process identity**

```javascript
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const childCode = 'console.log(process.pid !== Number(process.argv[1]))';
const { stdout, stderr } = await promisify(execFile)(
  process.execPath, ['--input-type=module', '--eval', childCode, String(process.pid)],
  { windowsHide: true, timeout: 2000 }
);
console.log('separate process', stdout.trim(), 'stderr bytes', stderr.length);
```

Actual output:

```text
separate process true stderr bytes 0
```


This launches the same Node executable as a separate process with an argument array and no shell. Its ordinary memory and environment copy are separate from the parent's runtime state.

execFile collects output for this tiny command. spawn is useful when output should be consumed as streams; exec runs a command through a shell and has a different parsing/quoting boundary.

Reference: [Node child_process](https://nodejs.org/download/release/v22.14.0/docs/api/child_process.html).

### Cluster and horizontal replicas

Cluster uses child processes with supported server-listening arrangements. Multiple independent replicas behind a load balancer are another deployment pattern.

In either case, ordinary module variables, in-memory sessions and caches are not automatically shared across processes. A global variable in worker A cannot enforce a global inventory/rate/idempotency invariant for worker B.

Use suitable shared data/coordination and account for per-process connection-pool multiplication. Four processes each opening twenty database connections can consume up to eighty connections.

Reference: [Node cluster](https://nodejs.org/download/release/v22.14.0/docs/api/cluster.html).

---
## 4.12 Configuration, errors, cleanup and shutdown

### Environment values are not validated configuration

**Verified example 17-config: Environment variables need parsing and validation**

```javascript
function parsePort(value) {
  if (typeof value !== 'string' || !/^[1-9]\d{0,4}$/.test(value)) {
    throw new Error('port format');
  }
  const port = Number(value);
  if (port > 65535) throw new Error('port range');
  return port;
}
process.env.LEARNING_PORT = '3104';
console.log(typeof process.env.LEARNING_PORT, parsePort(process.env.LEARNING_PORT));
for (const value of ['0', '70000', '31oops', undefined]) {
  try { parsePort(value); }
  catch (error) { console.log(error.message); }
}
```

Actual output:

```text
string 3104
port format
port range
port format
port format
```


Environment variables supply strings. A typed declaration or a call to Number does not enforce a port policy by itself.

This parser deliberately requires decimal ports from one through 65535 without leading zeroes. Port zero is useful for asking the OS for an available test port, but is outside this manual configuration policy. That is a contract choice, not a contradiction.

Parse important configuration once near startup and report a useful failure before accepting traffic. Do not log complete environment contents or credentials as a debugging shortcut.

### Choose the error mechanism the API uses

| Mechanism | Handling pattern |
| --- | --- |
| Synchronous throw | try/catch on the active stack |
| Promise rejection | await with catch or an owned rejection handler |
| Error-first callback | Inspect error before using the result |
| EventEmitter error event | Register the appropriate error listener |
| Stream flow failure | Await/handle pipeline and cleanup |
| Worker error/exit | Observe failure and define job/restart policy |
| Process startup/listen failure | Handle the listener error and fail startup appropriately |

One try/catch around setup does not catch every future asynchronous error.

A process-wide uncaught-exception hook is not permission to keep serving in an unknown state. Separate expected request failures from failures requiring process shutdown/restart under supervision.

### Active resources determine liveness

**Verified example 18-liveness: An unreferenced timer does not keep the process alive**

```javascript
new Promise(() => {}); // No active operation owns this pending promise.
setTimeout(() => console.log('timer fired'), 10000).unref();
console.log('main complete');
```

Actual output:

```text
main complete
```


The pending promise has no active operation behind it, and the unreferenced timer does not require the loop to remain alive. The timer callback therefore does not print.

An unreferenced timer can still fire if other work keeps the process alive; unref is not cancel. Clear a timer to cancel it.

Likewise, setting process.exitCode does not close a listening server. Conversely, immediate process.exit can cut off pending output/cleanup. Own and close the resources that should end before termination.

Reference: [Node process](https://nodejs.org/download/release/v22.14.0/docs/api/process.html) and [timers](https://nodejs.org/download/release/v22.14.0/docs/api/timers.html).

### Manual launcher with a bounded shutdown attempt

Complete start.mjs:

```javascript
import { createStudyServer } from './server.mjs';

const app = createStudyServer();
const port = 3104;
app.server.listen(port, '127.0.0.1', () => {
  console.log('Node learning server: http://127.0.0.1:' + port);
});
app.server.on('error', error => {
  console.error(error.code ?? error.name);
  process.exitCode = 1;
});
let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  app.beginDrain();
  const deadline = setTimeout(() => {
    app.server.closeAllConnections();
    process.exitCode = 1;
  }, 5000);
  deadline.unref();
  app.server.close(error => {
    clearTimeout(deadline);
    if (error) process.exitCode = 1;
  });
}
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
```

The first shutdown signal marks the application draining, stops accepting new connections through server.close, and gives accepted work a bounded opportunity to complete. The deadline can close remaining HTTP connections; it does not undo completed writes.

The logical drain behavior and listener closure were verified through the HTTP checks. Actual OS signal delivery/forced-deadline behavior is not part of those checks; test it on the deployment OS. Windows and Unix signal behavior differ.

### Full-service shutdown sequence

```text
Stop announcing readiness / enter draining
  -> stop accepting new work
  -> wait for accepted work within a deadline
  -> close database/client pools, Workers and timers you own
  -> finish required cleanup/log flushing
  -> allow process termination
```

The tiny launcher only owns an HTTP listener and per-request file resources. A larger application has more owners to coordinate.

In Node v22, server.close handles idle HTTP connections under its documented behavior. Upgraded protocols, long-lived sessions and other resource types need their own shutdown policy.

M17 will connect this lifecycle to reverse proxies, process managers and deployments.

---

## 4.13 Diagnose a slow Node service

### Begin with the observed symptom

“Node is slow” is not a diagnosis. Establish whether the delay is in accepting/scheduling work, application computation, pool checkout, network waiting, database execution or output transfer.

| Observation | Useful investigation | Avoid assuming |
| --- | --- | --- |
| Unrelated routes slow together | Event-loop delay, CPU/GC profile, shared resource queues | Every delay is a database issue |
| Particular crypto/filesystem work slows | Pool contention and operation timings | The JS loop must be blocked |
| Low CPU but high request latency | Dependency timing, queues, timeouts and connection pools | More CPU alone will fix it |
| High memory during downloads | Buffering, retained references, slow-consumer pressure | Async readFile is streaming |
| Worker-heavy service gets slower | Startup/serialization, oversubscription, job queues | More Workers always help |
| Errors rise as replicas increase | Downstream limits and per-replica pools | Horizontal scaling is free capacity everywhere |

Node's performance APIs include event-loop delay monitoring and event-loop utilization. ELU describes loop active/idle behavior; it is not a replacement for whole-process CPU measurement.

process.memoryUsage includes different views such as heap, RSS and external/array-buffer-related memory. A low heapUsed alone does not establish low total memory use.

References: [performance APIs](https://nodejs.org/download/release/v22.14.0/docs/api/perf_hooks.html) and [process memory APIs](https://nodejs.org/download/release/v22.14.0/docs/api/process.html#processmemoryusage).

### Measure a change under a defined workload

Record runtime/version, hardware, payload size, concurrency/arrival pattern, dependency behavior, duration and error rate.

Compare latency percentiles as well as throughput. A higher completion rate with many failed/timed-out requests is not automatically an improvement.

The chapter's gates establish causality in functional examples. They do not produce a production benchmark. M19 will build the fuller observability/performance method.

---

## 4.14 When Node is a good fit, and when to change the approach

### Start from requirements

| Situation | Reasonable direction |
| --- | --- |
| Many supported I/O waits and modest handler computation | Node can be a practical runtime choice |
| Large file/proxy transfers | Streaming with pressure/error/lifecycle handling |
| Frequent costly CPU jobs | Bounded Workers/processes or a compute service |
| Work must survive API-process loss | Durable job ownership and retry/idempotency design |
| Strong process isolation required | Separate processes/services, with operational costs |
| Global shared state/invariants | Appropriate shared data/coordination; not module globals |
| Team/domain library advantage in another stack | Consider that advantage alongside workload needs |

A CPU-heavy requirement does not always require rewriting the whole backend. Keep the API orchestration layer and offload the compute boundary when that fits.

Nor should every task be offloaded: a tiny computation can cost less than serializing a message and managing a Worker.

**Interview answer structure:** describe the workload, explain the chosen execution model, name its limits, identify the first likely bottleneck, and state how you would verify the choice.

---

## 4.15 Resume connection: a Node/Express load balancer

The load-balancer project on the resume is an opportunity to connect runtime knowledge to routing and proxy architecture. The following is a reasoning framework, not a claim that every feature below exists in the project's actual code.

### Request path to explain

```text
Client
  -> Node HTTP / Express entry point
  -> validate routing inputs and applicable policy
  -> choose an eligible upstream
  -> start/obtain an upstream connection
  -> forward request with deliberate protocol/header handling
  -> stream upstream response toward client
  -> handle completion, failure, timeout or disconnect
```

Node provides networking and stream capabilities. The application decides server eligibility, selection, retries, health behavior and ownership of each connection.

### Questions to prepare

| Interview follow-up | What a strong explanation includes |
| --- | --- |
| Why Node here? | I/O-heavy proxying and team/tooling fit, with limits |
| How is an upstream selected? | Actual algorithm/data structure and health policy |
| Why consistent hashing? | What affinity/remapping requirement it addresses |
| What does a failed health check change? | Eligibility, recovery policy and behavior for in-flight work |
| Does request forwarding buffer the whole body? | Actual stream/buffering path and pressure handling |
| What if the upstream is slow? | Shared deadlines, connection capacity and cleanup |
| Can a request be retried safely? | Method/business idempotency and whether data was already sent/committed |
| What if the client disconnects? | Upstream cancellation/resource ownership |
| How are multiple replicas coordinated? | Shared configuration/state assumptions |
| What does the performance claim measure? | Workload, errors, latency and baseline method |

If the implementation uses a sorted ring of virtual nodes, distinguish lookup cost from ring construction/update cost. Do not quote an algorithmic complexity without matching it to the actual data structure.

A lightweight routing decision does not mean zero proxy overhead. There can be extra network hops, buffering/copying, connection setup, TLS work, serialization, logs and failure-handling costs.

Health checks are observations that can become stale. A healthy result is not a guarantee that the next request succeeds.

### Design checks to connect later

- In-flight fan-out and downstream connection limits.
- Backpressure on both upload and download paths.
- Header/protocol handling, including any unsupported upgrades.
- Timeout/cancellation behavior before and after response headers.
- Per-process state vs shared configuration.
- Draining connections during deployments.
- Evidence for remapping/throughput claims from the actual project.

M27 and architecture S10 will develop the distributed design. This chapter establishes the runtime mechanisms needed to defend it.

---

## Must remember

1. Node is a runtime; JavaScript is the language and Express is a framework.
2. V8 executes JavaScript; libuv provides event-loop/I/O infrastructure.
3. A Node process contains more than one possible thread.
4. Ordinary handlers in one JavaScript context execute in segments, not simultaneously.
5. Overlapping I/O waits permit many requests to be in flight.
6. Not all asynchronous operations use the internal worker pool.
7. Promise continuations do not automatically offload JavaScript.
8. Pool saturation and event-loop blocking are different bottlenecks.
9. Large JSON/regex/loop work can delay unrelated callbacks.
10. Timer thresholds and exact callback order depend on context/version.
11. EventEmitter emit invokes listeners synchronously.
12. Module caches are not request-local, cross-process or durable state.
13. Node executes code; npm manages packages/scripts.
14. Buffers represent bytes; string length may not equal byte length.
15. Buffer views can share storage, and chunks can split characters.
16. Async readFile still buffers the complete file.
17. A false write return asks the producer to pause, not resend the chunk.
18. highWaterMark is a pressure threshold, not a total-memory guarantee.
19. pipeline owns flow completion/error handling; partial HTTP responses need care.
20. Worker threads run JavaScript in other contexts within the process.
21. Child/cluster processes do not share ordinary application memory.
22. A durable queue supplies work ownership, not necessarily CPU parallelism.
23. Configuration strings need explicit policy/validation.
24. Shutdown must coordinate admission, accepted work and resource closure.
25. Passing examples does not establish production performance or readiness.

---

## Common wrong answers

| Wrong claim | Correction |
| --- | --- |
| “Node is a JavaScript framework.” | It is a runtime; Express is a framework |
| “V8 supplies the filesystem and HTTP server.” | Those are host/runtime capabilities |
| “Node has only one thread in the whole process.” | Main JS context, native/runtime threads and explicit Workers differ |
| “Single-threaded means one request at a time.” | I/O waits can overlap |
| “Every async call gets a worker thread.” | APIs use different paths; sockets usually use OS event mechanisms |
| “Promise.all moves my loop to the pool.” | It composes outcomes, not arbitrary CPU offloading |
| “More pool threads always improve throughput.” | Capacity, contention and workload must be measured |
| “Async readFile uses constant memory.” | It returns the entire file; streaming is separate |
| “EventEmitter callbacks are always deferred.” | emit invokes listeners synchronously |
| “nextTick is simply the next event-loop iteration.” | It has a separate scheduling mechanism |
| “setImmediate always beats a timer everywhere.” | Context/version matter |
| “Module variables are safe per-request storage.” | They can be shared across requests in that instance |
| “A module cache synchronizes replicas.” | Each process/context can have separate instances |
| “String length is the HTTP byte length.” | Encoding determines byte count |
| “Buffer.subarray makes an independent copy.” | It shares storage |
| “Every chunk is a full character/message.” | Decoding and framing boundaries need handling |
| “write false means the write failed.” | It signals pressure after acceptance |
| “highWaterMark strictly caps total process memory.” | Other buffers/allocations exist and thresholds are not a universal hard cap |
| “A pipeline failure can always become JSON 500.” | The response/socket may already be partial or destroyed |
| “A Worker is libuv's internal worker.” | They are different execution mechanisms |
| “Spawn one Worker for every request.” | Startup, serialization and unbounded concurrency can dominate |
| “A background promise is a durable job.” | Process loss can discard in-process work |
| “A health check guarantees the next request succeeds.” | It is a potentially stale observation |
| “Setting exitCode closes the server.” | Active resources still need closure |
| “A functional test proves the throughput claim.” | Performance needs its own defined measurement |

---

## Interview Q&A bank

**Q1. What is Node.js?**
A JavaScript runtime using V8 and host capabilities for networking, files, processes and more.
**Follow-up:** Language, framework or server? Runtime; a program can use it to implement a server.

**Q2. Node vs V8 vs Express?**
V8 executes JavaScript, Node embeds it with runtime APIs, and Express structures web handlers on Node.
**Follow-up:** Who implements your permission rules? The application.

**Q3. Why use Node in a backend?**
It can suit applications with many supported I/O waits and modest handler computation, with useful JavaScript/TypeScript tooling.
**Follow-up:** Is it universally fastest? No; define and measure the workload.

**Q4. How can it handle many clients?**
Supported I/O can remain in flight while short JavaScript continuations run as work becomes ready.
**Follow-up:** Does each request get a new application thread? Not inherently.

**Q5. What does single-threaded mean here?**
One ordinary JavaScript context runs one execution segment at a time. The process can still contain native threads and Workers.
**Follow-up:** Is a logical workflow race-free? No; M2's read/await/write race still applies.

**Q6. What does libuv do?**
It supplies cross-platform event-loop/I/O infrastructure and a pool for supported work.
**Follow-up:** Does it execute every promise callback in a worker? No.

**Q7. Which operations use the pool?**
Many filesystem operations, selected crypto/compression work and OS DNS lookup paths are examples.
**Follow-up:** Is every DNS API the same? No; lookup and resolve differ.

**Q8. Event-loop blocking vs pool saturation?**
Blocking prevents that loop's JavaScript callbacks progressing. Pool saturation queues jobs behind occupied native workers.
**Follow-up:** What evidence distinguishes them? Profiles, loop metrics and relevant operation/queue timings.

**Q9. Does async fix CPU-heavy code?**
No. Its synchronous work still runs on the executing thread.
**Follow-up:** Options? Suitable chunking or bounded Workers/processes/compute services.

**Q10. Why can a large JSON operation hurt unrelated routes?**
It can occupy the calling thread while parsing/stringifying, delaying other callbacks.
**Follow-up:** Does an async function annotation change that? No.

**Q11. What are event-loop phases?**
Categories coordinating timers, certain pending callbacks, I/O polling, immediates and close callbacks, with internal stages too.
**Follow-up:** Are all runtime versions' exact orders identical? No.

**Q12. Timer vs immediate order?**
It depends on where they are scheduled and the runtime rules. The supplied I/O-callback case runs immediate before its timer.
**Follow-up:** Can you promise that at top level? No.

**Q13. nextTick vs promises?**
Node has separate scheduling mechanisms, and top-level ESM differs from CJS; callback location matters.
**Follow-up:** What context do you ask for before tracing output?

**Q14. Does emit schedule listeners later?**
Ordinary EventEmitter listeners are invoked synchronously by emit.
**Follow-up:** What about a listener starting an async operation? That operation still needs completion/error ownership.

**Q15. CommonJS vs ESM?**
They have different loading/export syntax and module semantics. Use explicit extensions/package policy and understand version-specific interoperability.
**Follow-up:** Are named ESM imports live bindings? Yes.

**Q16. What does module caching imply?**
Repeated loads of the same resolved module identity can reuse its instance in the relevant loader/context.
**Follow-up:** Is that state durable or shared across cluster processes? No.

**Q17. package.json vs lockfile?**
The manifest declares metadata/scripts/dependencies; the lock records resolved package-tree details for npm.
**Follow-up:** Why use npm ci in suitable CI setups? It checks compatible locked installation inputs and performs a clean install.

**Q18. What is a Buffer?**
A byte-data representation based on Uint8Array, useful for files, networks and binary formats.
**Follow-up:** Does a string's length give UTF-8 byte length? Not generally.

**Q19. Why can per-chunk UTF-8 decoding fail?**
An encoded character can span chunks; a decoder must retain incomplete bytes.
**Follow-up:** Does fixing character decoding also parse JSON messages? No.

**Q20. What is backpressure?**
Feedback that slows production when a consumer cannot keep up.
**Follow-up:** What does write false mean? Pause additional writes; do not resend the accepted chunk.

**Q21. What does highWaterMark control?**
A buffering/flow threshold for the stream and its mode.
**Follow-up:** Is it a hard cap on all application memory? No.

**Q22. Why pipeline?**
It coordinates flow, backpressure and completion/error propagation across stages.
**Follow-up:** What if the destination is an HTTP response? A failure may destroy the response/socket, preventing a replacement JSON error.

**Q23. Worker thread vs libuv worker pool?**
A Worker runs your JavaScript in another context/thread. The internal pool handles supported native operations.
**Follow-up:** Is the filesystem pool private to each Worker? No; the underlying pool is shared within the process.

**Q24. Worker vs child process?**
Workers share a process with distinct JS contexts and explicit sharing/transfer options; child processes have separate process identity/address space.
**Follow-up:** Is a worker's ordinary message object automatically shared? No, it is normally cloned.

**Q25. Why use a reusable worker pool?**
It bounds CPU task concurrency and avoids repeated startup cost.
**Follow-up:** Can too many workers worsen latency? Yes.

**Q26. Cluster vs shared memory?**
Cluster uses separate child processes and supported listening arrangements; ordinary module variables are not automatically shared.
**Follow-up:** What happens to database connection totals as process count grows?

**Q27. Worker vs durable queue?**
One is an execution mechanism; the other addresses work ownership/delivery across failures.
**Follow-up:** Can a queue consumer use Workers? Yes.

**Q28. How do you shut down gracefully?**
Stop admission/readiness, drain accepted work within a budget, close owned resources and define forced-deadline behavior.
**Follow-up:** Does cancellation or socket closure undo an external write? No.

**Q29. How do you diagnose slow Node requests?**
Trace time across scheduling, CPU, pool checkout, dependencies and output; use relevant loop/profile/memory/queue evidence.
**Follow-up:** Is low CPU proof of spare downstream capacity? No.

**Q30. How would you defend Node for your load balancer?**
Explain the actual proxy I/O path, selection logic, bounds, pressure and failure handling, then support performance claims with reproducible evidence.
**Follow-up:** Which parts are runtime capabilities and which did you implement?

---

## Practice

1. **Draw the architecture.** Place V8, Node APIs, libuv, sockets, filesystem work and a Worker on a responsibility diagram.
2. **Trace scheduling.** Explain example 06, then compare it with M2's top-level ESM/CommonJS traces.
3. **Show overlap.** Run the HTTP verifier and explain why the gate-controlled health check establishes progress during waiting rather than CPU parallelism.
4. **Change the endpoint.** Add a synchronous expensive calculation to /api/info on a private learning copy. Describe the expected effect on unrelated requests and how you would measure it.
5. **Repair pressure handling.** Explain what would happen if a producer ignores write false or resends the same chunk.
6. **Decode correctly.** Split another multibyte string at every byte boundary and compare naive decoding with StringDecoder.
7. **Bound compute work.** Design a two-Worker task pool with admission limits, job IDs, error handling and shutdown. State who owns an unfinished job.
8. **Review shared state.** An app stores session/current-tenant data in a module variable. Explain cross-request and multi-process failure modes.
9. **Design a slow-download policy.** Specify timeouts, client-disconnect cleanup, partial-response behavior and graceful draining. Separate policies from what this small example has verified.
10. **Prepare the resume defence.** Draw your actual load-balancer path. Mark unknown details that need code/measurement evidence before making claims.

### Answer checkpoints

- **1:** do not route every network wait through a pool thread or label libuv as the JS engine.
- **2:** distinguish an I/O callback from top-level module evaluation.
- **3:** both requests are pending at a controlled wait while health completes; that says nothing about executing two JS loops at once.
- **4:** measure loop/request latency under a defined load rather than asserting an invented slowdown.
- **5:** ignoring pressure can grow buffering; resending can duplicate bytes.
- **6:** preserve decoder state between chunks; message framing remains separate.
- **7:** a pool bounds execution but is not durable unless another mechanism preserves work.
- **8:** module scope is neither request scope nor shared durable state across replicas.
- **9:** closing a socket is not rollback, and partial responses cannot always be replaced.
- **10:** distinguish implemented facts, hypotheses and proposed improvements.

---

## Exit checklist

- [ ] I can explain JavaScript, V8, Node.js, Express and the application separately.
- [ ] I can explain why Node can suit I/O-heavy backends without promising universal speed.
- [ ] I can draw the runtime/OS/pool responsibility picture.
- [ ] I know that asynchronous APIs can use different execution paths.
- [ ] I can distinguish event-loop blocking, pool contention and downstream queues.
- [ ] I can trace a real HTTP request through the learning server.
- [ ] I can explain overlapping waits without claiming simultaneous JS handlers.
- [ ] I can label event-loop predictions with runtime/module/callback context.
- [ ] I understand synchronous EventEmitter invocation and its error contract.
- [ ] I can explain module caching, live bindings and scope limits.
- [ ] I can explain package manifests, lockfiles and installation/script roles.
- [ ] I can distinguish bytes, strings, views and independent copies.
- [ ] I can explain split characters and application framing.
- [ ] I can demonstrate write false, drain and pipeline error behavior.
- [ ] I can distinguish asynchronous whole-file reads from streaming transfers.
- [ ] I can compare Workers, native pool work, processes, cluster and durable jobs.
- [ ] I can explain worker cloning/error/exit behavior.
- [ ] I can validate configuration and own resource cleanup.
- [ ] I can describe graceful draining and its verification limits.
- [ ] I can diagnose a bottleneck with evidence rather than a runtime slogan.
- [ ] I can defend the runtime choices in the actual resume project.
- [ ] I can run all twenty cases and explain the sixteen HTTP checks.

---

## Next

[M5: Express.js and Backend Application Structure](/docs/resume-skills/express-backend-structure) builds routing and middleware on the runtime model, with body parsing, validation, controllers/services/data access, and deliberate error handling.

Keep the boundaries established here: a framework organizes handlers; it does not remove event-loop blocking, downstream limits, stream pressure or the need for authoritative state rules.

### Sources and reproducible evidence

- [Node introduction](https://nodejs.org/learn/getting-started/introduction-to-nodejs), [V8](https://nodejs.org/learn/getting-started/the-v8-javascript-engine), [event loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) and [blocking/pool guidance](https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop).
- [libuv design](https://docs.libuv.org/en/v1.x/design.html) and [thread pool](https://docs.libuv.org/en/v1.x/threadpool.html).
- Version-matched Node v22.14.0 APIs: [HTTP](https://nodejs.org/download/release/v22.14.0/docs/api/http.html), [filesystem](https://nodejs.org/download/release/v22.14.0/docs/api/fs.html), [events](https://nodejs.org/download/release/v22.14.0/docs/api/events.html), [timers](https://nodejs.org/download/release/v22.14.0/docs/api/timers.html), [process](https://nodejs.org/download/release/v22.14.0/docs/api/process.html), [DNS](https://nodejs.org/download/release/v22.14.0/docs/api/dns.html) and [crypto](https://nodejs.org/download/release/v22.14.0/docs/api/crypto.html).
- [CommonJS](https://nodejs.org/download/release/v22.14.0/docs/api/modules.html), [ESM](https://nodejs.org/download/release/v22.14.0/docs/api/esm.html), [packages](https://nodejs.org/download/release/v22.14.0/docs/api/packages.html), [Buffer](https://nodejs.org/download/release/v22.14.0/docs/api/buffer.html), [StringDecoder](https://nodejs.org/download/release/v22.14.0/docs/api/string_decoder.html) and [streams](https://nodejs.org/download/release/v22.14.0/docs/api/stream.html).
- [Workers](https://nodejs.org/download/release/v22.14.0/docs/api/worker_threads.html), [child processes](https://nodejs.org/download/release/v22.14.0/docs/api/child_process.html), [cluster](https://nodejs.org/download/release/v22.14.0/docs/api/cluster.html) and [performance APIs](https://nodejs.org/download/release/v22.14.0/docs/api/perf_hooks.html).
- npm: [package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/), [lockfile](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/) and [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/).
- Preserved artifacts: examples/resume-skills/module-4-nodejs/cases.json, verify.mjs, results.json, verification-output.txt, server.mjs, start.mjs, verify-server.mjs, http-verification-output.txt and fixtures/. The numbered snippets embed captured source/output; complete server/worker/launcher code is also shown.
- Tests establish the described behavior on Node v22.14.0. They do not establish throughput, exact timing across hosts/versions, signal delivery on every OS, client-abort behavior or production readiness.
