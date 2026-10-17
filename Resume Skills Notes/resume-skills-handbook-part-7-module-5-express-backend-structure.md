# Resume Skills Placement Handbook — Part 7
# Module 5: Express.js and Backend Application Structure

**Module 5 · 3–4 hours · Tier 1 · Requires: M0-M4**

---

## Why this module matters

M4 explained what Node supplies. Express adds a convenient way to match requests, compose middleware and send responses. Your application still needs to decide what input is valid, who may act, which rules apply and how state changes safely.

An interviewer can start with “What is middleware?” and follow with “Why did your validator never run?”, “Which error handler sees this rejection?” or “Why did your API expose a private database field?”

> **Treat an Express application as an ordered request-processing stack. Know which handler runs next, who owns completion/error handling, and which layer establishes each fact.**

The chapter builds a small public quote API and traces both success and failure through its layers. It uses the familiar product/quote problem from M0 so the new framework behavior is easier to isolate.

**Verification:** sixteen isolated runtime examples passed on **Express 5.3.0 / Node.js v22.14.0**, including a suite of **39 API checks**. Five additional TypeScript boundary checks passed using **TypeScript 7.0.2** and **@types/express 5.0.6**. The installed body-parser version is **2.3.0**. These are the recorded versions, not a promise that every older/newer tutorial behaves identically.

### Run the examples

From the repository root:

```powershell
node examples/resume-skills/module-5-express/verify.mjs
node examples/resume-skills/module-5-express/verify.mjs 09-async-five
node examples/resume-skills/module-5-express/verify-api.mjs
node examples/resume-skills/module-5-express/start.mjs
```

The manual API listens on **127.0.0.1:3105**; stop it with Ctrl+C. It is separate from the notes website on port 3000.

After starting it, a manual request is:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3105/api/quotes -ContentType application/json -Body '{"productId":7,"quantity":2}'
```

Dependencies are installed only in the example folder. For a fresh checkout with npm available, install the pinned lockfile there:

```powershell
npm --prefix examples/resume-skills/module-5-express ci --ignore-scripts --no-audit --no-fund
```

The full verifier also uses the TypeScript compiler already installed under study-guide/node_modules. Runtime examples alone can be checked with verify-runtime.mjs.

The runner sets the example working directory so companion imports resolve. No database, external API or credentials are required. Runtime examples bind temporary loopback listeners and close them; they are not deployed services.

---

## 5.1 What Express is, and why it exists

Express is a web application framework for Node.js. It supplies routing, middleware composition and request/response conveniences.

| Without a framework | With Express | Application responsibility remains |
| --- | --- | --- |
| Inspect method/path manually | app.get/post and Router | Design the endpoint contract |
| Wire handler steps yourself | Ordered middleware stack | Choose order and stopping conditions |
| Set headers/serialize JSON manually | res.status/json and other helpers | Select allowed response fields |
| Build your own failure dispatch | next(error) and error middleware | Classify/map/log failures |
| Parse supported body formats yourself | Built-in JSON/form/raw/text middleware | Validate shape, values and permissions |

Express does not choose a database, establish a user identity automatically or enforce business transactions. Its flexibility lets an application choose those components.

**Interview line:** “Express organizes HTTP handling on Node. It matches routes and composes middleware, while my application implements validation, authorization, domain rules and data access.”

References: [Express API overview](https://expressjs.com/en/5x/api/) and [FAQ on application structure/database choices](https://expressjs.com/en/starter/faq/).

---

## 5.2 Application, server and process are different objects

Calling express() creates an application function with framework capabilities. It is not yet a listening network server.

Node's HTTP server can use that function as its request listener. app.listen is a convenience for creating/listening with an HTTP server; it returns the server object.

```text
OS process
  -> Node runtime
      -> HTTP server listening on address/port
          -> Express application handles requests
              -> router/middleware/controller/service
```

Keeping createApp separate from the launcher is useful:

- Tests can supply a repository and choose an available port.
- Importing application code does not unexpectedly bind a port.
- Startup/shutdown can own network and other process resources.
- Application construction is reusable without equating it to deployment.

A modular monolith can contain all the layers in one process. Files named controller and service do not create independent services or network hops.

M4's constraints still apply: Express handlers can block the JavaScript thread, and supported asynchronous waits can overlap.

---

## 5.3 Middleware: order, continuation and termination

### The contract

A normal middleware receives request, response and next. It can inspect/change request-scoped information, end the response, advance the stack, or forward an error.

A handler that neither responds nor advances can leave the request waiting. Express does not guess which response you meant.

### next is a call, not a return statement

**Verified example 01-order: next advances the stack but does not return from the caller**

```javascript
import { requestApp } from './http-helper.mjs';
const trace = [];
const result = await requestApp(app => {
  app.use((req, res, next) => {
    trace.push('before');
    next();
    trace.push('after');
  });
  app.get('/', (req, res) => { trace.push('route'); res.json({ ok: true }); });
});
console.log(result.status, trace.join(','));
```

Actual output:

```text
200 before,route,after
```


Code after next still runs when that call returns. Use return when you must stop executing the current branch.

For example, after sending a validation error, return from that function instead of continuing into the normal success path. Otherwise the same code can attempt a second response.

### next is not await next

**Verified example 14-next-not-await: next is not an asynchronous join**

```javascript
import { requestApp } from './http-helper.mjs';
const trace = [];
const result = await requestApp(app => {
  app.use((req, res, next) => {
    trace.push('outer-before');
    const returned = next();
    trace.push('outer-after');
    console.log('next returned', typeof returned);
  });
  app.get('/', async (req, res) => {
    trace.push('route-before');
    await Promise.resolve();
    trace.push('route-after');
    res.json({ ok: true });
  });
});
console.log(result.status, trace.join(','));
```

Actual output:

```text
next returned undefined
200 outer-before,route-before,outer-after,route-after
```


The async route reaches await and yields. The outer middleware's after code runs before the route's continuation.

This is not the promise-based downstream join used by some other middleware frameworks. To observe response completion, use the relevant response lifecycle events rather than assuming code after next means “the response is finished.”

### Ending a response stops the ordinary path when you do not advance

**Verified example 02-end: A response without next stops ordinary stack traversal**

```javascript
import { requestApp } from './http-helper.mjs';
let reached = false;
const result = await requestApp(app => {
  app.use((req, res) => res.status(403).json({ error: 'blocked' }));
  app.get('/', (req, res) => { reached = true; res.json({ ok: true }); });
});
console.log(result.status, reached, result.body.error);
```

Actual output:

```text
403 false blocked
```


The later route is not reached. Sending a response does not magically stop all JavaScript statements in the current function, so the handler must still control its own branches.

### next route is a special routing instruction

**Verified example 03-next-route: next route skips the remaining callbacks of this route**

```javascript
import { requestApp } from './http-helper.mjs';
const result = await requestApp(app => {
  app.get('/choice', (req, res, next) => next('route'),
    (req, res) => res.send('unreachable'));
  app.get('/choice', (req, res) => res.send('fallback'));
}, '/choice');
console.log(result.status, result.body);
```

Actual output:

```text
200 fallback
```


Within a route callback chain, next('route') skips the remaining callbacks of that route and proceeds to the next matching route.

It is not a general substitute for next(error), nor a universal instruction for every app.use middleware location. Use the route-level contract deliberately.

Reference: [Using middleware](https://expressjs.com/en/guide/using-middleware/).

### Why order belongs in the design

```text
Request ID / observation
  -> applicable identity checks
  -> route/body parsing
  -> validation
  -> applicable resource permission checks
  -> controller/service
  -> response

Failure at a step -> error handling
No matching response -> terminal 404 handling
```

The exact placement of identity/body parsing depends on the operation, but every prerequisite must be established before the code relying on it. The learning API has no authentication; later M7/M8 add it.

---

## 5.4 Routing, params, queries and mounted routers

### Match a method and route path

A path such as /products/:productId captures a URL segment. It does not turn the segment into an integer automatically.

The query string is not part of the route path. A URL's query and body are separate input sources, each requiring its own contract.

| Source | Example | What to establish |
| --- | --- | --- |
| req.params | productId from /products/7 | Representation/range and resource permission |
| req.query | page/sort/search controls | Shape, duplicates, defaults and bounds |
| req.body | JSON/form payload | Parsing, allowed fields and values |
| req.get/header APIs | Content-Type, request headers | Intended semantics and trust policy |
| res.locals | Per-response application data | Which earlier step established it |

Do not use a generic “look anywhere for id” helper if it hides whether a caller controls the path, query or body version.

### A Router is a mountable stack

**Verified example 05-mounted-path: Mounted routers expose distinct URL views**

```javascript
import express from 'express';
import { requestApp } from './http-helper.mjs';
const result = await requestApp(app => {
  const router = express.Router();
  router.get('/items/:id', (req, res) => res.json({
    id: req.params.id, q: req.query.q,
    baseUrl: req.baseUrl, url: req.url, originalUrl: req.originalUrl
  }));
  app.use('/api', router);
}, '/api/items/7?q=blue');
console.log(JSON.stringify(result.body));
```

Actual output:

```text
{"id":"7","q":"blue","baseUrl":"/api","url":"/items/7?q=blue","originalUrl":"/api/items/7?q=blue"}
```


At this mount:

- baseUrl identifies the matched mount prefix.
- url is the current request URL as seen within that router.
- originalUrl retains the original URL.
- params.id is the string 7, not the number 7.

These views are useful for routing and diagnosis. None is a permission check.

Reference: [Request API](https://expressjs.com/en/5x/api/request/) and [Router API](https://expressjs.com/en/5x/api/router/).

### Query data can have unexpected shape

**Verified example 06-query: Repeated query keys need a deliberate input policy**

```javascript
import { requestApp } from './http-helper.mjs';
const result = await requestApp(app => {
  app.set('query parser', 'simple');
  app.get('/', (req, res) => res.json(req.query));
}, '/?q=a&q=b&a%5Bb%5D=1');
console.log(Array.isArray(result.body.q), result.body.q.length,
  typeof result.body.q === 'string', result.body['a[b]']);
```

Actual output:

```text
true 2 false 1
```


With this parser, repeated q values become an array. Bracket syntax is not interpreted as a nested object by the simple parser in this example.

Decide whether to reject repeated keys, accept a list, or choose another documented policy. Do not assume every req.query property is a single string.

In Express 5, treat req.query as a getter-derived input view rather than a place to assign normalized values. Put validated values in a separate application-owned structure.

### Parent router parameters are not automatic tenant authorization

**Verified example 13-merge-params: Nested router parameters require an explicit inheritance choice**

```javascript
import express from 'express';
import { requestApp } from './http-helper.mjs';
function configure(mergeParams) {
  return app => {
    const router = express.Router({ mergeParams });
    router.get('/items/:itemId', (req, res) => res.json(req.params));
    app.use('/orgs/:orgId', router);
  };
}
console.log('default', JSON.stringify((await requestApp(configure(false), '/orgs/7/items/9')).body));
console.log('merged', JSON.stringify((await requestApp(configure(true), '/orgs/7/items/9')).body));
```

Actual output:

```text
default {"itemId":"9"}
merged {"orgId":"7","itemId":"9"}
```


mergeParams preserves parent route parameter values in the child router. It does not establish that the caller belongs to organization 7 or may access item 9.

Reference: [Router options](https://expressjs.com/en/5x/api/express/).

---

## 5.5 Body parsing is a separate step from validation

### Choose the parser for the contract

| Middleware | Result for matched input | Important limit |
| --- | --- | --- |
| express.json | Parsed JSON value under its configured policy | Does not validate your DTO |
| express.urlencoded | Parsed URL-encoded form data | Parser options/shape still matter |
| express.raw | Buffer of body bytes | Use only where raw bytes are required |
| express.text | Decoded text | Text is not a validated command |
| Multipart middleware | Form fields/files according to its contract | JSON parsing does not implement uploads |

These parsers consume body data. Their placement, content-type match, size limits and compression policy affect later handlers.

### Register the parser before the consumer

**Verified example 07-parser-order: A parser registered after a completed route cannot populate that route's body**

```javascript
import express from 'express';
import { requestApp } from './http-helper.mjs';
const options = { method: 'POST', headers: { 'content-type': 'application/json' },
  body: '{"name":"Ada"}' };
const before = await requestApp(app => {
  app.post('/', (req, res) => res.json({ type: typeof req.body }));
  app.use(express.json());
}, '/', options);
const after = await requestApp(app => {
  app.use(express.json());
  app.post('/', (req, res) => res.json({ name: req.body.name }));
}, '/', options);
console.log(before.body.type, after.body.name);
```

Actual output:

```text
undefined Ada
```


The first route completes before the later parser can run. Express 5 does not populate req.body with a useful DTO simply because the header says application/json.

### Valid JSON can still be invalid application input

**Verified example 08-parser-not-validator: JSON parsing accepts shapes and values the application may reject**

```javascript
import express from 'express';
import { requestApp } from './http-helper.mjs';
function configure(app) {
  app.use(express.json());
  app.post('/', (req, res) => res.json({
    array: Array.isArray(req.body), quantityType: typeof req.body.quantity
  }));
}
const array = await requestApp(configure, '/', { method: 'POST',
  headers: { 'content-type': 'application/json' }, body: '[]' });
const string = await requestApp(configure, '/', { method: 'POST',
  headers: { 'content-type': 'application/json' }, body: '{"quantity":"2"}' });
console.log(array.status, array.body.array);
console.log(string.status, string.body.quantityType);
```

Actual output:

```text
200 true
200 string
```


An array is accepted by the JSON parser's object/array policy. A quantity string is still a string. Neither result satisfies the quote API's contract.

In this installed parser, an explicitly empty JSON body can be parsed as an empty object; an unparsed body can remain undefined. The API checks cover both absent media type and empty declared-JSON input. Validate the result rather than guessing its shape from the header alone.

The parser's strict option is not your business schema. Under its strict object/array policy, a scalar such as null is rejected even though null is syntactically valid JSON.

### Raw bytes cannot be reconstructed by serializing parsed JSON

**Verified example 15-raw-body: Raw parsing preserves bytes; prior JSON parsing does not restore them**

```javascript
import express from 'express';
import { requestApp } from './http-helper.mjs';
const body = ' { "a": 1 } ';
const options = { method: 'POST', headers: { 'content-type': 'application/json' }, body };
const raw = await requestApp(app => {
  app.post('/', express.raw({ type: 'application/json' }), (req, res) =>
    res.json({ buffer: Buffer.isBuffer(req.body), exact: req.body.toString('utf8') === body }));
}, '/', options);
const parsed = await requestApp(app => {
  app.use(express.json());
  app.post('/', express.raw({ type: 'application/json' }), (req, res) =>
    res.json({ buffer: Buffer.isBuffer(req.body), exact: JSON.stringify(req.body) === body }));
}, '/', options);
console.log('raw', raw.body.buffer, raw.body.exact);
console.log('after JSON', parsed.body.buffer, parsed.body.exact);
```

Actual output:

```text
raw true true
after JSON false false
```


Whitespace was preserved by raw parsing but lost when comparing a parsed-and-reserialized object with the original bytes.

This matters for signature verification contracts that depend on exact payload bytes. Register the required raw-body path before incompatible global parsing, or use a documented raw-capture mechanism. M9 will add actual webhook verification and replay handling; this snippet performs no signature verification.

Reference: [Express parser APIs](https://expressjs.com/en/5x/api/express/) and [body-parser behavior/options](https://expressjs.com/en/resources/middleware/body-parser/).

---
## 5.6 Validate and normalize at the boundary

### The quote request contract

| Field | Accepted representation | Rule |
| --- | --- | --- |
| productId in a path | Decimal string without leading zeroes | Positive safe integer after conversion |
| productId in JSON | Number | Positive safe integer |
| quantity in JSON | Number | Integer from one through ten |
| Extra JSON fields | Not accepted | Reject rather than accidentally assigning them |

The path and JSON representations intentionally differ. URL segments arrive as text; JSON has a numeric representation. A number annotation does not convert one into the other.

### Complete validation.mjs

```javascript
import { AppError } from './errors.mjs';

export function parseProductId(value) {
  if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value)) {
    throw new AppError(400, 'invalid_product_id');
  }
  const id = Number(value);
  if (!Number.isSafeInteger(id)) throw new AppError(400, 'invalid_product_id');
  return id;
}

export function parseQuote(input) {
  if (typeof input !== 'object' || input === null || Array.isArray(input)) {
    throw new AppError(400, 'invalid_body');
  }
  if (Object.keys(input).some(key => key !== 'productId' && key !== 'quantity')) {
    throw new AppError(400, 'unknown_fields');
  }
  const { productId, quantity } = input;
  if (typeof productId !== 'number' || !Number.isSafeInteger(productId) || productId < 1) {
    throw new AppError(400, 'invalid_product_id');
  }
  if (typeof quantity !== 'number' || !Number.isSafeInteger(quantity) ||
      quantity < 1 || quantity > 10) {
    throw new AppError(400, 'invalid_quantity');
  }
  return { productId, quantity };
}
```


The returned object contains only accepted fields. It is placed in application-owned response locals rather than treating the raw body as trustworthy throughout the stack.

This code expects JSON-decoded data from the parser. It is not a universal sanitizer for arbitrary JavaScript objects, proxies or getters.

### Validation, permissions and business rules are different

| Question | Responsibility |
| --- | --- |
| Is the body valid JSON under the parser policy? | Body parser |
| Is quantity an allowed integer? | Boundary validation |
| Does the product exist? | Application/data lookup |
| Can this caller access this product/tenant? | Authentication/authorization path, added later |
| Is requested quantity available? | Business rule |
| Can stock be allocated atomically? | Authoritative state operation/transaction, if allocation is implemented |

The chosen quantity cap is part of this teaching API's input policy. A product-specific purchasing cap might belong in a service rule instead.

The sample returns a quote; it does not allocate stock, create an order or charge a payment. Repeating a quote does not reserve inventory.

---

## 5.7 Controllers, services and data access

### A responsibility model, not a folder quota

```text
HTTP route/middleware
  -> controller: adapt HTTP to an application call
      -> service: apply application rules
          -> repository/adapter: retrieve authoritative data
      <- application result
  <- selected public response
```

| Layer | Knows about HTTP? | What to keep there |
| --- | --- | --- |
| Router/middleware | Yes | Method/path matching, parsing, boundary prerequisites |
| Controller | Yes | Read accepted input, call service, form response |
| Service | Preferably independent of req/res | Rules and operation orchestration |
| Repository/adapter | No need for req/res | Data query/persistence interface |
| Composition root | Wires collaborators | Construct adapters, services, controllers and app |

For a tiny application, several responsibilities can fit in one file. Split when it clarifies ownership, change boundaries or tests. Express does not require a controllers/services/repositories directory tree.

### Repository: explicit data boundary

Complete repository.mjs:

```javascript
export function createProductRepository() {
  const products = new Map([
    [7, { id: 7, name: 'Keyboard', unitPricePaise: 25000, stock: 4, internalCostPaise: 13000 }],
    [8, { id: 8, name: 'Mouse', unitPricePaise: 15000, stock: 0, internalCostPaise: 7000 }],
  ]);
  return {
    async findById(id, trace = []) {
      trace.push('repository');
      await Promise.resolve(); // Simulated async contract, not database I/O.
      const row = products.get(id);
      return row ? { ...row } : undefined;
    },
  };
}
```


This adapter uses seeded process memory. Its await simulates an asynchronous interface; it is not database I/O or evidence of database performance.

It returns a copy of the flat record so callers do not directly hold the stored object. That does not make arbitrary nested data deeply immutable.

### Service: authoritative values and business rules

Complete service.mjs:

```javascript
import { AppError } from './errors.mjs';

export function createProductService(repository) {
  async function find(id, trace) {
    trace.push('service');
    const row = await repository.findById(id, trace);
    if (!row) throw new AppError(404, 'product_not_found');
    return row;
  }
  return {
    async getProduct(id, trace = []) {
      const row = await find(id, trace);
      return { id: row.id, name: row.name, unitPricePaise: row.unitPricePaise, stock: row.stock };
    },
    async quote(input, trace = []) {
      const row = await find(input.productId, trace);
      if (input.quantity > row.stock) throw new AppError(409, 'insufficient_stock');
      const totalPaise = row.unitPricePaise * input.quantity;
      if (!Number.isSafeInteger(totalPaise)) throw new Error('invalid stored price calculation');
      return {
        productId: row.id, quantity: input.quantity,
        unitPricePaise: row.unitPricePaise, totalPaise,
      };
    },
  };
}
```


The quote uses the repository's price. The client cannot lower it by supplying unitPricePaise; the validator rejects that extra field before this layer runs.

The service selects the product fields it exposes. An internalCostPaise field remains in the repository record but is absent from the product response.

The quote input is expected to have passed its caller's boundary validation. A future CLI/job caller must establish that contract too, rather than passing an unchecked object simply because it bypasses HTTP.

### Controller: adapt the transport

Complete controllers.mjs:

```javascript
export function createProductControllers(service) {
  return {
    async getProduct(request, response) {
      response.locals.trace.push('controller');
      const product = await service.getProduct(response.locals.productId, response.locals.trace);
      response.json({ product, requestId: response.locals.requestId });
    },
    async quote(request, response) {
      response.locals.trace.push('controller');
      const quote = await service.quote(response.locals.quoteInput, response.locals.trace);
      response.json({ quote, requestId: response.locals.requestId });
    },
  };
}
```


Controllers receive request/response objects because they belong at the HTTP edge. The service does not need those framework objects to calculate a quote.

Passing a trace array here is teaching instrumentation, not a requirement of service design. A larger application may use an explicit operation context or observability mechanism appropriate to its needs.

### Dependency injection in plain functions

createProductService(repository) receives an adapter instead of constructing a hard-coded database connection internally. The application factory supplies the default in-memory adapter; tests can inject a failing or gate-controlled one.

This makes a useful question testable: “If data access rejects, does the route return one controlled failure and keep the app alive?”

It does not require a dependency-injection container, nor does replacing the adapter automatically preserve transactional semantics. A real database adapter must implement the required guarantees.

---

## 5.8 Compose the working Express application

### Complete app.mjs

```javascript
import express from 'express';
import { randomUUID } from 'node:crypto';
import { AppError, publicError } from './errors.mjs';
import { parseProductId, parseQuote } from './validation.mjs';
import { createProductRepository } from './repository.mjs';
import { createProductService } from './service.mjs';
import { createProductControllers } from './controllers.mjs';

export function createApp({ repository = createProductRepository(), onComplete = () => {} } = {}) {
  const app = express();
  app.disable('x-powered-by');
  app.set('query parser', 'simple');

  app.use((request, response, next) => {
    response.locals.requestId = randomUUID();
    response.locals.trace = ['request'];
    response.set('X-Request-Id', response.locals.requestId);
    response.once('finish', () => onComplete({
      requestId: response.locals.requestId, status: response.statusCode,
      path: request.originalUrl, trace: [...response.locals.trace],
    }));
    next();
  });

  app.get('/health', (request, response) => {
    response.locals.trace.push('health');
    response.json({ status: 'ok', requestId: response.locals.requestId });
  });

  const controller = createProductControllers(createProductService(repository));
  const router = express.Router();
  router.use((request, response, next) => {
    response.locals.trace.push('router');
    next();
  });

  router.get('/products/:productId', (request, response, next) => {
    response.locals.trace.push('validate-id');
    response.locals.productId = parseProductId(request.params.productId);
    next();
  }, controller.getProduct);

  router.post('/quotes', (request, response, next) => {
    response.locals.trace.push('media-type');
    if (!request.get('content-type') || request.is('application/json') === false) {
      throw new AppError(415, 'json_required');
    }
    next();
  }, express.json({ limit: '1kb', strict: true, inflate: false }),
  (request, response, next) => {
    response.locals.trace.push('parsed', 'validate-body');
    response.locals.quoteInput = parseQuote(request.body);
    next();
  }, controller.quote);

  // Explicit method policy for known routes; this also overrides automatic OPTIONS.
  router.all('/products/:productId', (request, response) => {
    response.set('Allow', 'GET, HEAD');
    throw new AppError(405, 'method_not_allowed');
  });
  router.all('/quotes', (request, response) => {
    response.set('Allow', 'POST');
    throw new AppError(405, 'method_not_allowed');
  });

  app.use('/api', router);
  app.use((request, response) => {
    response.locals.trace.push('not-found');
    response.status(404).json({ error: { code: 'route_not_found' }, requestId: response.locals.requestId });
  });

  app.use((error, request, response, next) => {
    response.locals.trace.push('error');
    if (response.headersSent) return next(error);
    const { status, code } = publicError(error);
    response.status(status).json({ error: { code }, requestId: response.locals.requestId });
  });
  return app;
}
```


This is the composition root and HTTP policy layer. It constructs collaborators, registers middleware/routes and returns the app without binding a port.

### Trace a successful quote

Actual captured trace:

```text
request > router > media-type > parsed > validate-body > controller > service > repository
```

The steps establish:

1. A server-generated request ID and per-response trace.
2. The /api router context.
3. The required JSON media type.
4. Successful parsing within the one-kilobyte policy.
5. A normalized request shape/value.
6. The application operation and data lookup.
7. A selected quote response after completion.

Request IDs help correlate observations; they are not authentication credentials. The application generates its own ID rather than using a caller's assertion as authority.

### Scope the parser deliberately

Only POST /api/quotes gets this JSON parser. Consequently a malformed body sent to an unknown route produces the chosen route-not-found response, rather than a parser error from an unrelated global parser.

That is a policy choice. Another app may intentionally parse a broader scope. Explain why the parser is placed where it is, and verify the resulting outcomes.

The parser uses:

- limit one kilobyte for this small JSON contract.
- strict object/array policy before schema validation.
- inflate false, so compressed bodies are not accepted by this endpoint.

The endpoint maps oversized input to 413 and its unsupported encoding policy to 415. These values are verified, not inferred from the middleware name.

### The method policy is application code

GET routes can implicitly serve HEAD when a separate HEAD route has not taken precedence. The controller can still execute; omitting the response body does not necessarily avoid data access or computation.

The explicit router.all handlers provide the example's 405/Allow behavior. They also intercept OPTIONS; this is not a claim that Express automatically produces this policy for every route. M6 will expand method/OPTIONS contracts, and M8 will connect browser CORS behavior.

### Observe finish accurately

The test observer captures trace/status on response finish. That indicates completion of the response-writing lifecycle, not proof that the remote client received or processed every byte.

A disconnected request may follow a different close/error lifecycle. The hook is deliberately small and non-throwing in the tests. Full logging, aborted-request handling and metrics belong in the later operational chapters.

---

## 5.9 Error handling: distinguish dispatch from policy

### Entering the error path

**Verified example 04-error-mode: next error skips ordinary middleware and reaches an error handler**

```javascript
import { requestApp } from './http-helper.mjs';
const trace = [];
const result = await requestApp(app => {
  app.use((req, res, next) => next(new Error('failed')));
  app.use((req, res) => { trace.push('ordinary'); res.send('wrong'); });
  app.use((error, req, res, next) => {
    trace.push('error');
    res.status(503).json({ message: error.message });
  });
});
console.log(result.status, trace.join(','), result.body.message);
```

Actual output:

```text
503 error failed
```


An error passed to next skips ordinary middleware until an appropriate error handler is found.

Error middleware uses four parameters: error, request, response, next. Its position and signature matter. Put it after the routes it must handle.

### Express 5 observes returned promise rejection

**Verified example 09-async-five: Express 5 forwards a returned async-handler rejection**

```javascript
import { requestApp } from './http-helper.mjs';
const result = await requestApp(app => {
  app.get('/', async (req, res) => {
    await Promise.resolve();
    throw new Error('async failure');
  });
  app.use((error, req, res, next) => res.status(500).json({ message: error.message }));
});
console.log(result.status, result.body.message);
```

Actual output:

```text
500 async failure
```


The async function returns a promise, and Express 5 forwards its rejection. The sample controller functions likewise return their async operation to the router.

Do not start an unrelated promise, forget to return/await it and expect Express to discover it. M2's completion-ownership rule still applies.

### Later callback errors still need a bridge

**Verified example 10-callback-error: A later callback must explicitly forward its error**

```javascript
import { requestApp } from './http-helper.mjs';
const result = await requestApp(app => {
  app.get('/', (req, res, next) => {
    setImmediate(() => {
      try { throw new Error('callback failure'); }
      catch (error) { next(error); }
    });
  });
  app.use((error, req, res, next) => res.status(500).json({ message: error.message }));
});
console.log(result.status, result.body.message);
```

Actual output:

```text
500 callback failure
```


The later callback is outside the original synchronous route call stack. The explicit catch/next forwards that failure.

Prefer promise-based APIs when suitable, then return/await their work. Where callbacks remain, use their documented error path.

Reference: [Express error-handling guide](https://expressjs.com/en/guide/error-handling/).

### Mapping errors is an application decision

Complete errors.mjs:

```javascript
export class AppError extends Error {
  constructor(status, code) {
    super(code);
    this.name = 'AppError';
    this.status = status;
    this.code = code;
  }
}

export function publicError(error) {
  if (error instanceof AppError) return { status: error.status, code: error.code };
  if (error?.type === 'entity.parse.failed') return { status: 400, code: 'invalid_json' };
  if (error?.type === 'entity.too.large') return { status: 413, code: 'body_too_large' };
  if (error?.type === 'encoding.unsupported' || error?.type === 'charset.unsupported') {
    return { status: 415, code: 'unsupported_encoding' };
  }
  if (error instanceof URIError) return { status: 400, code: 'invalid_path' };
  return { status: 500, code: 'internal_error' };
}
```


Known application/parser failures get deliberate public codes. Unexpected adapter/program failures become internal_error without exposing their private message/stack.

A production service still needs an internal diagnostic record with appropriate request correlation. A generic client response alone is not observability.

If headers were already sent, the final middleware delegates to the remaining/default error handling rather than attempting to write a second JSON response. A partial response is not replaceable as if nothing had been sent.

### Route 404 vs application 404

**Verified example 11-head-and-notfound: HEAD can use GET; a missing route is not an error-handler event**

```javascript
import { requestApp } from './http-helper.mjs';
let errorCalls = 0;
function configure(app) {
  app.get('/hello', (req, res) => res.json({ ok: true }));
  app.use((error, req, res, next) => { errorCalls++; res.status(500).send('error'); });
}
const head = await requestApp(configure, '/hello', { method: 'HEAD' });
const missing = await requestApp(configure, '/missing');
console.log('HEAD', head.status, head.text.length, Number(head.headers['content-length']) > 0);
console.log('missing', missing.status, 'error calls', errorCalls);
```

Actual output:

```text
HEAD 200 0 true
missing 404 error calls 0
```


An unmatched route falls through the ordinary stack. It is not automatically a thrown error for error middleware to catch. The main app has a terminal ordinary middleware for its JSON route-not-found response.

By contrast, a matched product route whose record is missing throws the application's AppError and reaches error middleware with a 404 policy. Same status, different control-flow cause.

Reference: [Express FAQ on 404 and error handlers](https://expressjs.com/en/starter/faq/).

---

## 5.10 Apply TypeScript without pretending it validates HTTP

### Describe the raw body as unknown

The default body type in common Express declarations can be permissive. Merely writing a handler annotation with a desired DTO does not make the wire payload conform to it.

This companion example explicitly uses unknown for ReqBody and an optional validated value in locals.

Complete typed/typed-boundary.ts:

```typescript
import express, { type RequestHandler } from 'express';

type QuoteInput = { productId: number; quantity: number };
type Reply = { input: QuoteInput } | { error: string };
type Locals = { quoteInput?: QuoteInput };
type Handler = RequestHandler<Record<string, string>, Reply, unknown, Record<string, unknown>, Locals>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export const validate: Handler = (request, response, next) => {
  const body = request.body; // unknown, not an already-trusted DTO.
  if (!isRecord(body) ||
      Object.keys(body).some(key => key !== 'productId' && key !== 'quantity')) {
    response.status(400).json({ error: 'invalid_body' });
    return;
  }
  const { productId, quantity } = body;
  if (typeof productId !== 'number' || !Number.isSafeInteger(productId) || productId < 1 ||
      typeof quantity !== 'number' || !Number.isSafeInteger(quantity) ||
      quantity < 1 || quantity > 10) {
    response.status(400).json({ error: 'invalid_values' });
    return;
  }
  response.locals.quoteInput = { productId, quantity };
  next();
};

export const respond: Handler = (request, response) => {
  const input = response.locals.quoteInput;
  if (!input) {
    response.status(500).json({ error: 'validation_missing' });
    return;
  }
  response.json({ input });
};

export function createTypedApp() {
  const app = express();
  app.post('/typed', express.json({ limit: '1kb' }), validate, respond);
  return app;
}
```

### Read the handler type by responsibility

| Generic slot | What it describes here |
| --- | --- |
| Params | Path parameter map |
| ResBody | Intended success/error response union |
| ReqBody | unknown before runtime validation |
| ReqQuery | Query input description |
| Locals | Application-owned per-response data |

The validator executes checks and constructs QuoteInput. The responding handler checks that the validated value actually exists.

Express types do not prove the registration order of every middleware chain. The verifier deliberately mounts respond without validate and observes a controlled validation_missing response.

### The checker rejects unsafe use of unknown

Intentionally invalid typed/unsafe.ts:

```typescript
import type { RequestHandler } from 'express';

const unsafe: RequestHandler<Record<string, string>, unknown, unknown> = (request, response) => {
  response.json(request.body.quantity);
};
```

Actual compiler diagnostic:

```text
typed/unsafe.ts(4,17): error TS18046: 'request.body' is of type 'unknown'.
```

### Actual combined type/runtime verification

```text
PASS typed boundary compiles
PASS unknown request body rejected TS18046
PASS typed runtime accepts validated input
PASS typed runtime rejects wrong value type
PASS missing middleware detected at runtime
Verified 5 TypeScript boundary checks; Version 7.0.2
```

The evidence has two parts: compiler acceptance/rejection and real requests against the emitted JavaScript. Neither alone supplies authentication, authorization or database atomicity.

This typed companion demonstrates the input boundary only. The main quote API supplies the fuller error/method/service contract shown earlier; do not assume every feature was duplicated in the small typed companion.

---
## 5.11 Express 4 vs 5: label the version

### Important tutorial differences

| Concern | Express 5 point to remember |
| --- | --- |
| Returned promise rejection | Automatically forwarded to the error path; Express 4 needs explicit forwarding/wrapping |
| String-path wildcards | Use named wildcards; braces support optional segments |
| Query input | Getter-based; simple parser is the documented default |
| Unparsed body | Can be undefined; do not assume a DTO or a universal empty-object default |
| Response signatures | Prefer res.status(code).json(body); old overloads were removed |
| Runtime requirement | Express 5 requires Node 18 or newer; this chapter verified Node 22.14.0 |

The 5.x behavior below was executed on 5.3.0. The 4.x comparison is documentation-based; Express 4 was not installed/run as a second test target.

### Verify the current string-path syntax

**Verified example 12-path-five: Express 5 string paths use named wildcards and braces**

```javascript
import express from 'express';
import { requestApp } from './http-helper.mjs';
try { express().get('*', (req, res) => res.end()); }
catch (error) { console.log('bare wildcard rejected', error instanceof TypeError); }
function wildcard(app) {
  app.get('/{*splat}', (req, res) => res.json({ parts: req.params.splat ?? [] }));
}
console.log(JSON.stringify((await requestApp(wildcard, '/a/b')).body));
console.log(JSON.stringify((await requestApp(wildcard, '/')).body));
function optional(app) {
  app.get('/docs{/:page}', (req, res) => res.json({ page: req.params.page ?? 'index' }));
}
console.log((await requestApp(optional, '/docs')).body.page,
  (await requestApp(optional, '/docs/intro')).body.page);
```

Actual output:

```text
bare wildcard rejected true
{"parts":["a","b"]}
{"parts":[]}
index intro
```


A bare wildcard path is rejected during registration in this example. The named wildcard including root returns an array of segments, while the optional segment uses braces.

A pathless app.use terminal middleware avoids needing a wildcard string for the common JSON 404 fallback.

### Async migration caveat

Automatic rejection forwarding is not automatic success response generation. A fulfilled handler that neither sends nor advances can still leave a request waiting.

In an Express 4 project, a promise-aware wrapper or explicit catch(next) is needed for asynchronous errors. Preserve ownership of the returned operation and avoid forwarding the same error twice. A migration should review routes, parser behavior and response signatures alongside error handling.

Reference: [Official Express 5 migration guide](https://expressjs.com/en/guide/migrating-5/).

---

## 5.12 Verify the actual boundary and failure contracts

### What this API does

| Request/situation | Outcome in the verified application |
| --- | --- |
| Health / known product / valid quote | 200 with deliberate JSON fields |
| HEAD product | 200 with no response body; handler/data access still executes |
| Invalid text or unsafe path ID | 400 invalid_product_id before repository access |
| Malformed JSON or parser-rejected scalar | 400 invalid_json |
| Explicit empty JSON body in this parser | 400 invalid_product_id because required ID is missing |
| Array body | 400 invalid_body |
| Invalid quantity representation/range | 400 invalid_quantity |
| Caller price/tenant extra fields | 400 unknown_fields |
| Missing product record | 404 product_not_found |
| Valid quantity exceeding stock | 409 insufficient_stock |
| Wrong/missing required media type | 415 json_required |
| Compressed body under this endpoint policy | 415 unsupported_encoding |
| Body above the byte limit | 413 body_too_large |
| Unknown route, even with malformed JSON here | 404 route_not_found because its scoped parser never ran |
| Unsupported method on known API route | 405 plus explicit Allow |
| Malformed path encoding | 400 invalid_path |
| Unexpected repository rejection | 500 internal_error with private detail omitted |
| Two waiting requests | Independent locals; health can progress while they wait |

The tests also verify unique server-generated request IDs, header/body correlation, selected product fields, authoritative totals and unchanged stock after a quote.

### Run the application suite

**Verified example 16-api: The layered API passes its HTTP and boundary checks**

```javascript
await import('./verify-api.mjs');
```

Actual output:

```text
PASS API health
PASS API product-projection
PASS API implicit-head
PASS API authoritative-quote
PASS API quote-does-not-reserve
PASS API zero-path-id
PASS API partial-path-id
PASS API unsafe-path-id
PASS API missing-product
PASS API wrong-media-type
PASS API missing-media-type
PASS API empty-json-body
PASS API malformed-json
PASS API array-body
PASS API primitive-json-policy
PASS API missing-fields
PASS API string-product-id
PASS API string-quantity
PASS API zero-quantity
PASS API fractional-quantity
PASS API policy-limit
PASS API caller-price-rejected
PASS API caller-tenant-rejected
PASS API insufficient-stock
PASS API zero-stock
PASS API valid-upper-bound-stock-conflict
PASS API quote-missing-product
PASS API json-byte-limit
PASS API compressed-body-policy
PASS API unknown-route-not-parsed
PASS API quote-method-allow
PASS API product-method-allow
PASS API malformed-path-encoding
PASS API middleware-success-and-failure-traces
TRACE quote: request > router > media-type > parsed > validate-body > controller > service > repository
TRACE malformed: request > router > media-type > error
PASS API async-repository-failure-hidden
PASS API request-failure-does-not-kill-app
PASS API health-progresses-during-async-work
PASS API request-locals-stay-independent
PASS API listeners-closed
Verified 39 Express API checks
```


The gate-controlled requests establish overlap and independent request state. They do not establish CPU parallelism or a production throughput figure.

### Test the boundary that matters

Each matrix case checks the repository-call count. Parser/shape/value failures must not reach the repository; a missing record or stock rule needs a lookup and therefore does.

That is stronger evidence than checking only a status code: it verifies that invalid input did not accidentally proceed into data work.

A status-only test could miss a handler that performs a side effect and then returns an error. For future mutations, verify the relevant state invariant as well.

### What has not been tested or implemented?

- Authentication, resource/tenant authorization or browser-session protections.
- A real database, atomic stock changes, payment or order persistence.
- Global rate limits, durable retries or background jobs.
- Partial-response errors, client-abort behavior or OS signal delivery.
- Every parser format, proxy configuration or deployment environment.
- Throughput, latency percentiles or production resource limits.

The example has a small JSON byte limit and explicit validation, but those facts do not establish all of the above.

---

## 5.13 Startup, testing seams and process ownership

### Complete start.mjs

```javascript
import { createServer } from 'node:http';
import { createApp } from './app.mjs';

const server = createServer(createApp());
server.listen(3105, '127.0.0.1', () => {
  console.log('Express learning API: http://127.0.0.1:3105');
});
server.on('error', error => {
  console.error(error.code ?? error.name);
  process.exitCode = 1;
});
let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  const deadline = setTimeout(() => {
    server.closeAllConnections();
    process.exitCode = 1;
  }, 5000);
  deadline.unref();
  server.close(error => {
    clearTimeout(deadline);
    if (error) process.exitCode = 1;
  });
}
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
```

The launcher owns the listening server and a bounded shutdown attempt. Its syntax was checked; the HTTP verification suite uses ephemeral listeners and explicitly closes them.

M4 explains the difference between closing a listener, draining accepted work, canceling operations and rolling back state. M17 will handle deployment/readiness integration in more depth.

### Why the application factory helps

createApp accepts a repository and completion observer. The tests inject:

- A normal in-memory adapter.
- An adapter that rejects to verify failure mapping.
- An adapter controlled by a gate to verify concurrency and request isolation.

These are useful seams because they express real application dependencies. Do not create a layer merely to mock an implementation detail with no meaningful contract.

A service can also be called from a job or CLI if its input/error contract is respected. Keeping req/res at the edge makes that reuse easier.

---

## 5.14 Architecture and resume connections

### Follow the same path in each project

| Resume flow | Request boundary | Application responsibility | Data/integration boundary |
| --- | --- | --- | --- |
| Multi-tenant document access | Parse/validate IDs | Verify identity and resource/tenant permission | Scope the actual query and retrieval |
| Payment or signed webhook | Preserve required bytes | Verify sender, duplicates and state transition | Authoritative transaction/provider state |
| AI/RAG request | Validate request/budgets | Authorize documents and orchestrate retrieval/generation | Upstream status/schema/capacity handling |
| Load-balancer/proxy request | Routing inputs/protocol policy | Choose eligible upstream and own failure behavior | Connections, pressure and downstream deadlines |
| Data ingestion | Decode/validate file or event | Per-record rules and operation outcomes | Bounded data writes/jobs and idempotency |

These are design prompts, not claims about uninspected implementation details. Use the actual project code/evidence when describing what you built.

### Common architectural mistake: HTTP objects everywhere

Passing req into the repository couples data access to URL/body conventions. A later job runner then needs to invent a fake request or duplicate logic.

Prefer accepted application inputs and explicit operation context at that boundary. Keep HTTP status/serialization at an appropriate edge, while allowing service failures to be mapped consistently.

### Another mistake: folder names stand in for design

A controller/service/repository split is useful when responsibilities and dependencies are clear. It is not automatically clean architecture, a distributed system or proof of isolation.

Start with one comprehensible application. Separate deployment units only when requirements justify network boundaries, independent scaling/ownership or failure isolation.

### Security and reliability continue in later modules

A valid product ID proves its representation, not ownership. Rejecting a tenantId field prevents one bad input path, but real tenancy still requires scoped authorization and data access.

CORS configuration is not user authentication. Request validation is not an inventory transaction. Express error handling is not durable retry ownership.

M6-M9 and the architecture companion add those contracts in dependency order.

---

## Must remember

1. Express is an HTTP framework on Node, not a new execution model.
2. An application is distinct from a listening server and OS process.
3. Middleware runs according to registration, matching and control flow.
4. next does not return from your function.
5. next does not await an async downstream handler.
6. A response branch still needs to stop its own execution deliberately.
7. next('route') and next(error) have different meanings.
8. Params, query, body and headers are separate untrusted inputs.
9. A Router is a mountable stack, not automatic permissions.
10. mergeParams preserves parent parameters; it does not authorize them.
11. Parse before consuming, then validate the parser result.
12. JSON parsing does not enforce a DTO, integer rule or allowed field list.
13. Raw-byte contracts can be broken by prior JSON parsing.
14. Put normalized data in an application-owned request-scoped structure.
15. Controllers adapt HTTP; services apply rules; adapters access data.
16. Select response fields with executable code, not a narrower type name.
17. Express 5 forwards returned promise rejection, not forgotten work.
18. Later callbacks still need explicit error ownership.
19. Error middleware has four parameters and must be placed appropriately.
20. An unmatched route and a missing domain record can take different 404 paths.
21. Do not replace a partial response with a fresh JSON response.
22. TypeScript does not prove middleware order or validate the wire payload.
23. A quote is not a reservation, transaction or order.
24. Test whether rejected inputs reached downstream work, not only their status.
25. Framework/version/adapter assumptions belong in the explanation.

---

## Common wrong answers

| Wrong claim | Correction |
| --- | --- |
| “Express replaces Node's event loop.” | It organizes handlers on the same runtime |
| “express() starts listening.” | Constructing the app and binding a server are separate |
| “next is a return statement.” | Statements after next can execute |
| “await next waits for the route.” | Express next is not a downstream promise join |
| “Sending JSON stops the current function.” | JavaScript control flow still needs return/branch discipline |
| “A handler that returns a value becomes an HTTP response.” | The response must be written through the framework contract |
| “Path ID 7 arrives as a number.” | Named path values are text until normalized |
| “Query values are always single strings.” | Repeated/parser-specific shapes need a policy |
| “mergeParams proves tenant access.” | It only preserves parameter values |
| “Content-Type means req.body is ready.” | A matching parser must run first |
| “express.json validates my request object.” | It parses under its format policy |
| “Parser strict means my business schema.” | Object/array policy is not field/value validation |
| “Parsed JSON can recreate exact signed bytes.” | Whitespace/representation can differ |
| “`Partial<User>` is a safe update contract.” | Select editable fields and enforce runtime/permission rules |
| “Every rule belongs in the controller.” | Domain rules should have a clear application boundary |
| “A repository needs the entire req object.” | It can accept deliberate data/query inputs |
| “Express 5 catches every future asynchronous failure.” | It observes the returned promise; unrelated callbacks/work still need ownership |
| “404 always goes to error middleware.” | An unmatched route normally falls through |
| “Error handlers need only three parameters.” | Their four-argument signature matters |
| “An internal exception message belongs in the client response.” | Expose deliberate public errors and keep diagnostics appropriately internal |
| “HEAD necessarily avoids controller/data work.” | A GET handler may still execute |
| “A typed middleware chain proves validation ran.” | Types do not establish registration order |
| “One successful quote means stock is reserved.” | This application does not mutate stock |
| “Many layers mean many microservices.” | The layers can live in one process |
| “Functional checks prove production throughput.” | Performance requires a defined measurement |

---

## Interview Q&A bank

**Q1. What is Express?**
A web framework that organizes HTTP routing, middleware and response handling on Node.js.
**Follow-up:** What does it not supply automatically? Your identity, permission, business and data guarantees.

**Q2. app vs server?**
The app handles HTTP requests; a Node HTTP server listens and invokes it. The process owns runtime resources.
**Follow-up:** Why keep creation separate from listen? Testing, configuration and lifecycle ownership.

**Q3. What is middleware?**
A function participating in the matched request-processing stack, with access to req, res and continuation/error control.
**Follow-up:** What if it neither responds nor advances? The request may remain pending.

**Q4. Does next end the current function?**
No. Code after the call can still run.
**Follow-up:** How do you avoid a second response after validation failure? Return or otherwise terminate that branch.

**Q5. Does next await an async route?**
No. It advances dispatch; it is not an asynchronous downstream join.
**Follow-up:** Which example proves that? The outer-after trace precedes route-after in example 14.

**Q6. next route vs next error?**
The special route instruction skips remaining callbacks of that route; an error enters error-handling dispatch.
**Follow-up:** Are they interchangeable app.use control signals? No.

**Q7. app.use vs app.get/post?**
use registers middleware at a matching scope; method routes select a method/path contract.
**Follow-up:** Why is registration order relevant?

**Q8. Params vs query vs body?**
They represent path captures, query controls and parsed payload respectively.
**Follow-up:** Does Express convert every path number or validate query shape? No.

**Q9. What is Router?**
A mountable routing/middleware stack used to group HTTP behavior.
**Follow-up:** What do baseUrl and originalUrl help explain? Mount context and the original request URL.

**Q10. What does mergeParams do?**
It preserves parent router parameters in the child context, subject to parameter-conflict rules.
**Follow-up:** Does it prove the caller belongs to that organization? No.

**Q11. Why can a query value be an array?**
The chosen parser can represent repeated keys that way.
**Follow-up:** How do you normalize it? Apply an explicit duplicate/list policy after checking shape.

**Q12. What does express.json do?**
It parses matching body data under its format, size and encoding policies.
**Follow-up:** Does it prove quantity is a positive integer? No.

**Q13. Why can req.body be undefined or empty?**
Parser placement, media type, absence of data and parser/version behavior matter.
**Follow-up:** What is the robust approach? Validate the actual parsed result.

**Q14. How do you handle file uploads?**
Use a suitable multipart/streaming contract and enforce its field/file/resource rules.
**Follow-up:** Is JSON middleware a multipart parser? No.

**Q15. Why preserve raw body bytes?**
Some integrity/signature contracts operate on the exact transmitted payload representation.
**Follow-up:** Does JSON.stringify recover original whitespace? No.

**Q16. Where should validation live?**
At the input boundary before code relies on normalized data; application rules and permissions still have their own responsibilities.
**Follow-up:** What if a service is called by a job instead of HTTP? That caller must establish the input contract too.

**Q17. Controller vs service vs repository?**
Controller adapts HTTP; service owns application rules/orchestration; repository handles a deliberate data interface.
**Follow-up:** Must these be separate deployments? No.

**Q18. Why inject a repository?**
It makes the data dependency explicit and allows meaningful failure/concurrency verification or another adapter.
**Follow-up:** Does swapping an adapter guarantee transaction behavior? No.

**Q19. How does Express 5 handle async errors?**
A rejected returned promise is forwarded to error dispatch.
**Follow-up:** What if the handler starts but does not return the failing promise? It needs separate ownership/forwarding.

**Q20. What about later callback errors?**
Use the callback API's error path and forward to next or adapt it into an owned promise.
**Follow-up:** Will an earlier setup try/catch remain active? No.

**Q21. How do you define error middleware?**
Use the four-parameter signature after the routes it should handle and apply a deliberate error-response policy.
**Follow-up:** What if headers were already sent? Delegate/handle the partial response rather than writing a replacement.

**Q22. How do you handle 404?**
Use terminal ordinary middleware for unmatched routes. Domain failures can independently map to 404 through the error path.
**Follow-up:** Why distinguish the causes for diagnosis?

**Q23. Does Express automatically choose your 405/Allow policy?**
No. This example adds explicit known-route method handling; it also affects OPTIONS behavior.
**Follow-up:** Does implicit HEAD necessarily avoid executing GET logic? No.

**Q24. What changes when moving from Express 4 to 5?**
Review promise-error forwarding, path syntax, query/body behavior and removed response overloads.
**Follow-up:** Which version was actually run here? Express 5.3.0; the v4 comparison is documentation-based.

**Q25. Does typing ReqBody validate incoming data?**
No. Use unknown before validation and establish the runtime shape/value.
**Follow-up:** Can the compiler prove validate ran before respond? Not from these handler types.

**Q26. How do you avoid leaking private row fields?**
Construct a deliberate public response object; a narrower interface or Pick type alone does not remove runtime properties.
**Follow-up:** Which field is omitted here? internalCostPaise.

**Q27. What do the API checks establish?**
The documented response contracts, parser/validator boundaries, error mapping and controlled concurrent request isolation.
**Follow-up:** Do they establish stock reservation or throughput? No.

**Q28. How would you explain your backend architecture?**
Trace one request through validation, identity/permission, application rules, data/integration work and response/failure handling, using actual project evidence.
**Follow-up:** Which steps are framework features and which did you implement?

---

## Practice

1. **Trace the stack.** Predict examples 01 and 14 without running them. Explain why code after next has different timing relative to a suspended route.
2. **Repair a response branch.** A validator sends 400 and then calls next. Explain the possible second-response problem and fix the branch.
3. **Design a query contract.** Accept a single page value with a bounded positive integer policy. Decide how repeated keys are handled.
4. **Extend the product response.** Add a public category field while keeping internal cost absent. Verify serialized output.
5. **Test parser order.** Move the JSON parser after the quote handler in a private learning copy. Explain the changed failure path.
6. **Separate validation and rules.** Add a product-specific purchase limit. Decide where the policy lives and distinguish it from the generic input quantity bound.
7. **Add a failure case.** Inject a repository timeout/rejection. Verify the public code, request correlation and absence of private exception text.
8. **Use TypeScript deliberately.** Extend the typed companion with a permitted note field. Keep raw input unknown and test invalid types and missing middleware.
9. **Plan an order mutation.** Explain what must change to turn a quote into an actual reservation, including transaction/concurrency and retry behavior.
10. **Defend a resume flow.** Map one real endpoint to middleware/controller/service/data responsibilities. Mark unknown implementation details for evidence gathering.

### Answer checkpoints

- **1:** next itself is not a promise join.
- **2:** terminate the current branch after its response; do not advance into success processing.
- **3:** a parser-produced array should not silently become a scalar.
- **4:** inspect actual JSON, not just the declared response type.
- **5:** the consumer cannot rely on a parser that never ran before it.
- **6:** product data/rules belong at an authoritative application boundary.
- **7:** check both response policy and downstream/lifecycle effects.
- **8:** a successful compile is not the entire boundary test.
- **9:** the existing stock check is a quote rule, not an atomic allocation.
- **10:** distinguish verified implementation, reasonable hypothesis and proposed design.

---

## Exit checklist

- [ ] I can explain Express vs Node and app vs listening server.
- [ ] I can trace middleware matching and registration order.
- [ ] I can distinguish next, return, next route and next error.
- [ ] I can explain why next is not an async downstream join.
- [ ] I can prevent a branch from sending twice or leaving a request hanging.
- [ ] I can distinguish path, query, body, headers and application locals.
- [ ] I can explain mounted URL views and mergeParams.
- [ ] I can define a policy for repeated query keys.
- [ ] I can choose/place parsers and explain their size/format/encoding limits.
- [ ] I can distinguish parsing, validation, permissions and business rules.
- [ ] I can explain why exact payload bytes may need preservation.
- [ ] I can normalize input and select public output fields.
- [ ] I can separate controller/service/data responsibilities without treating folders as deployments.
- [ ] I can inject and verify a meaningful data dependency.
- [ ] I can handle returned promises and callback errors correctly for the stated version.
- [ ] I can explain error middleware, partial responses and the two 404 paths.
- [ ] I can describe the explicit method/HEAD policy.
- [ ] I can explain the TypeScript boundary and middleware-order limit.
- [ ] I can run sixteen runtime examples, 39 API checks and five typed boundary checks.
- [ ] I can state why the quote is not an order/reservation.
- [ ] I can identify which authentication, database and operational guarantees remain for later modules.

---

## Next

[**M6: REST APIs and HTTP in Application Design**](/docs/resume-skills/rest-apis-http). Build on these routes to design resource contracts, methods/status codes, pagination, filtering, versioning, retries/idempotency and rate-limit behavior.

Then M7/M8 add identity and authorization. The architecture track will reuse the same explicit boundaries for worked systems after the API/data prerequisites.

### Sources and reproducible evidence

- Express guides: [routing](https://expressjs.com/en/guide/routing/), [middleware](https://expressjs.com/en/guide/using-middleware/), [error handling](https://expressjs.com/en/guide/error-handling/), [migration to 5](https://expressjs.com/en/guide/migrating-5/) and [FAQ](https://expressjs.com/en/starter/faq/).
- APIs: [Express/parser factories](https://expressjs.com/en/5x/api/express/), [application](https://expressjs.com/en/5x/api/application/), [request](https://expressjs.com/en/5x/api/request/), [response](https://expressjs.com/en/5x/api/response/) and [router](https://expressjs.com/en/5x/api/router/).
- [body-parser documentation](https://expressjs.com/en/resources/middleware/body-parser/) and [Express releases](https://github.com/expressjs/express/releases).
- The isolated package.json/package-lock.json pin Express 5.3.0 and @types/express 5.0.6. Type checking used the workspace's TypeScript 7.0.2; execution used Node v22.14.0.
- Preserved examples: examples/resume-skills/module-5-express/cases.json, verify-runtime.mjs, results.json and runtime-verification-output.txt. verify.mjs runs runtime and typed checks together.
- API evidence: http-cases.json, verify-api.mjs, http-results.json and http-verification-output.txt, alongside the complete application source.
- Typed evidence: typed/, tsconfig files, verify-types.mjs, type-results.json and type-verification-output.txt. The intentionally invalid source is checked for its expected TS18046 diagnostic.
- Verification establishes the recorded behavior, not all versions, deployment environments or production guarantees.
