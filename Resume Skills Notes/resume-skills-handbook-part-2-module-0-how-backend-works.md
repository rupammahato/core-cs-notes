# Resume Skills Placement Handbook — Part 2
# Module 0: How a Backend Works

**Module 0 · 2–3 hours · Tier 1 · Requires: no backend framework knowledge**

---

## Why this module matters

A resume can list Node.js, Express, Django, FastAPI, PostgreSQL and AWS while the candidate still struggles with one question: **what happens when a user clicks a button?**

The missing piece is usually the picture connecting the names. A language expresses the rules. A runtime executes them. A framework organizes request handling. A database manages persistent records. A deployment gives the running application somewhere to execute and an address clients can reach.

This module builds that picture before teaching any particular framework.

> **A backend receives input from outside its trust boundary, applies the application's rules using authoritative state, and returns a result. Its architecture describes where those rules and state live, how requests reach them, and what happens when something fails.**

**Verification:** the example in §0.7 was executed on Node.js v22.14.0. Thirteen real loopback HTTP cases passed, including invalid input, missing resources, a wrong method and a forged client price. The source and verifier are preserved in examples/resume-skills/module-0-backend/. No external service or database was used.

---

## 0.1 Frontend and backend: two responsibilities

### What is the frontend?

The part that presents information and lets the user interact: a product card, login form, search box, loading indicator or error message.

In a browser application, much of that behavior runs in the browser. But **frontend does not mean every line must execute in the browser**: server-rendered frameworks can generate the initial UI on a server.

### What is the backend?

The application behavior on the server side: deciding what a caller may do, applying business rules, reading or changing records, coordinating external services and preparing responses.

It may be one process, several services or functions managed by a hosting platform. It does not have to be a separate repository from the UI.

```text
User clicks "Get price"
        |
        v
Frontend: collect quantity, show loading state
        |
        | HTTP request: productId=7, quantity=2
        v
Backend: validate -> read stored price -> calculate quote
        |
        | HTTP response: totalPaise=50000
        v
Frontend: display INR 500.00
```

**The division is about responsibility and trust.** The frontend can preview a total for responsiveness. The backend must calculate or verify the authoritative total before accepting an order.

### Why the same application needs both

| Responsibility | Frontend example | Backend example |
| --- | --- | --- |
| Present information | Render a product card | Return the product fields |
| Gather input | Quantity selector | Validate the received quantity |
| Guide the user | Disable an unavailable button | Enforce availability even if called directly |
| Identify the caller | Send the session credential | Verify it using the server's authentication mechanism |
| Apply policy | Hide another user's documents | Reject access to documents the caller does not own |
| Handle outcomes | Show success/error/retry UI | Return a stable result and meaningful error |

A browser, mobile app, CLI tool or another service can all be clients of the same backend. The backend cannot assume every request came from your page.

**Practice checkpoint:** explain why hiding a delete button is useful UI behavior but insufficient authorization.

---

## 0.2 Why a backend exists

Imagine that the browser sends this when buying two notebooks:

```json
{"productId":7,"quantity":2,"unitPricePaise":1}
```

If the server trusts the supplied price, it charges two paise. The browser is under the caller's control: the caller can modify JavaScript, change a request, or send a new one without opening the page.

The backend instead looks up the current authoritative price, applies discounts according to policy, and computes the amount itself.

### Four jobs that belong across the server-side boundary

| Job | Concrete reason |
| --- | --- |
| **Protect credentials and privileged access** | A payment secret or privileged database credential must not be shipped to a public client |
| **Enforce policy** | The UI cannot grant itself permission by claiming role=admin |
| **Coordinate shared state** | Two customers can request the same final seat at the same time |
| **Integrate services reliably** | A payment callback or background import can happen after the browser closes |

Client validation remains useful: it catches typos quickly and improves feedback. Server validation is required because clients can bypass their UI.

[OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) explicitly recommends permission checks on every request. We will implement protected-resource checks in M8; this chapter's example exposes only public demonstration data.

### Does every website need an application backend?

No. A portfolio made of static files may need only static hosting. A shared booking, payment or private-document application needs authoritative rules somewhere.

Managed platforms sometimes let clients call database or storage APIs directly. That moves enforcement into server-side rules and services; it does not make client assertions trustworthy.

**Interview line:** “The backend is where the application enforces shared rules and access to authoritative data. The frontend collects input and presents outcomes, but every caller can bypass its UI, so important checks must run on the server side.”

---

## 0.3 The vocabulary: do not confuse the layers

### Language, engine, runtime, library and framework

| Term | What it means | Example in this handbook |
| --- | --- | --- |
| **Language** | Syntax and semantics used to express a program | JavaScript, Python, C++ |
| **Engine/interpreter implementation** | Software that executes a language's operations | V8 for JavaScript; CPython for Python |
| **Runtime environment** | Execution facilities around the program, including available APIs | Node.js provides server-side JavaScript APIs such as HTTP and file access |
| **Library** | Reusable functions/types your program calls | A validation library or database client |
| **Framework** | Conventions and machinery that organize an application and call your handlers | Express, Django, FastAPI |
| **Application** | Your product's specific rules and flows | Candidate invitation or booking service |
| **DBMS** | Software managing stored data, queries and concurrency | PostgreSQL, MongoDB |
| **Hosting/deployment** | The environment where the application runs | A VM, container platform or serverless service |

These are roles, not mutually exclusive marketing categories. A package can contain both library utilities and framework behavior.

### Node.js vs Express

```text
JavaScript             language in which a handler is written
    |
Node.js                executes it; exposes HTTP/network/file APIs
    |
Express                adds routing and middleware conveniences
    |
Your application       owns prices, permissions and business workflows
```

Node.js can serve HTTP without Express. Express does not replace Node.js.

Similarly, FastAPI organizes Python API handling and normally runs through an ASGI server. PostgreSQL does not execute your FastAPI route; the application sends it database operations.

### An API is a contract, not necessarily a web URL

An **application programming interface** defines how software requests a capability and receives a result.

A web API often expresses that contract using HTTP endpoints. A library method is also an API. Not every API is REST, HTTP or JSON.

For this module, think in concrete terms: “GET this path with these inputs, and receive this response shape or one of these errors.”

**Exit condition for this section:** place JavaScript, Node.js, Express, your service code and PostgreSQL in the correct order without treating them as interchangeable tools.

---

## 0.4 What exactly is a server?

“Server” is overloaded. State which meaning you intend.

| Meaning | Example |
| --- | --- |
| Physical/virtual machine | A VM with CPU, memory, network interface and disk |
| Running software process | A Node.js process listening for requests |
| A service role | The catalog service, possibly spread across several processes |
| A protocol participant | An HTTP server responding to an HTTP client |

Running a server means starting software that waits for incoming work. The source file sitting on disk is not handling traffic; a process executing that file can.

### Address, port, path and operation

```text
http://127.0.0.1:3100/api/products/7
|      |         |   |
scheme address   port application path

GET /api/products/7
 ^        ^
method    path used by the application router
```

- The address gets a connection to the intended host/interface.
- The transport port helps the OS deliver it to a listening endpoint.
- The HTTP method and path help the application select an operation.
- The path is not another port and does not have to be a file on disk.

The example binds to **127.0.0.1**, the IPv4 loopback address, so it is reachable from the same machine. It is not an internet deployment.

“Listen on 0.0.0.0” means listen on all IPv4 interfaces. It is a binding instruction, not the public URL a user should type. Firewalls, routing and proxies still determine reachability.

### Web server vs application server

These are responsibilities that can overlap.

```text
Browser --HTTPS--> Nginx --HTTP--> application process --> database
                   |                |
                   |                routes and business rules
                   static files, proxying, TLS termination
```

A reverse proxy accepts a request and forwards it to an upstream service. Node's HTTP server can also accept HTTP directly. You do not need Nginx to prove that the tiny example works.

[Nginx's guide](https://nginx.org/en/docs/beginners_guide.html) shows both static serving and proxying. This diagram is an illustrative deployment; it is not the topology used by the loopback example.

**Link back:** CN Module 5 explains ports and sockets; OS Module 1 explains programs vs processes. Here those ideas meet.

---

## 0.5 The complete request lifecycle

Use one scenario consistently: get a quote for two notebooks.

### High-level trace

```text
1. UI collects product ID and quantity
2. Client constructs an HTTP request
3. Network/proxy path delivers it to the application
4. Runtime exposes method, target, headers and body to a handler
5. Router selects the operation
6. Boundary checks validate the input
7. Authentication/authorization run if the operation requires them
8. Application reads authoritative state
9. Business logic produces a result or state change
10. Handler maps the result into an HTTP status, headers and body
11. Client receives the response and updates the UI
```

The ordering of detailed checks depends on the operation. For example, avoid revealing private-resource existence before access checks. The important point is that each responsibility has a deliberate place.

### Request/response sequence

```text
Client          HTTP handler       Application logic      Data access
  |                  |                    |                   |
  | GET quote ------>|                    |                   |
  |                  | validate input     |                   |
  |                  |------------------->|                   |
  |                  |                    | lookup product -->|
  |                  |                    |<-- stored price --|
  |                  |                    | calculate total   |
  |                  |<-- quote result ---|                   |
  |<-- 200 + JSON ---|                    |                   |
```

These columns may be ordinary functions inside **one process**. A layered diagram does not imply four deployed services.

### What happens before the handler?

For a cold public HTTPS request, name resolution and transport/TLS setup may precede HTTP handling. Existing connections and caches can shorten that path.

The local example uses an explicit IP and plain HTTP, so it does not demonstrate DNS or TLS.

For the full network story, revise [CN's URL walkthrough](/docs/cn/url-walkthrough). This module concentrates on what the application does once a request reaches it.

### What if the browser times out?

A timeout means the client did not receive the expected result within its deadline. It does **not** prove that server-side work never happened.

For a quote, retrying is simple because no reservation or payment occurs. For a payment, an uncertain result needs operation identity and reconciliation. That is why M9 and architecture A3 cover idempotency.

---

## 0.6 HTTP at the application boundary

The request needs more than a path.

| Part | Purpose | Example |
| --- | --- | --- |
| Method | Express the intended operation semantics | GET |
| Target | Identify a resource/operation and query inputs | /api/quote?productId=7&quantity=2 |
| Headers | Carry metadata and credentials where applicable | Accept: application/json |
| Body | Carry an optional payload | JSON in many create/update APIs |

The response similarly contains a status, headers and an optional body.

### A readable HTTP/1.1-style exchange

This is an explanatory representation of the tested operation; it is not a packet capture.

```http
GET /api/quote?productId=7&quantity=2 HTTP/1.1
Host: 127.0.0.1:3100
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Cache-Control: no-store

{"productId":7,"quantity":2,"totalPaise":50000,"currency":"INR","reserved":false}
```

The server also adds transport-related headers as appropriate. Their precise order and connection handling are not the teaching point.

**JSON is a representation.** A JavaScript object in memory and JSON bytes on the connection are different things. Serialization produces the bytes; the client parses them back into its own data representation.

[MDN's HTTP-message guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages) explains message structure. [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) defines method and response semantics; M6 will develop the API-design consequences.

### Route parameters, query parameters and bodies

| Input position | Typical purpose | Example |
| --- | --- | --- |
| Path parameter | Resource identity | /api/products/7 |
| Query parameter | Filtering, pagination or other operation inputs | quantity=2 |
| Request body | Structured operation payload | An order with several line items |

There is no magic trust advantage to any of these positions. All caller-controlled inputs need appropriate validation.

The example uses GET for a **read-only quote**. Creating an order or reserving inventory would need a state-changing operation and additional correctness rules. A quote is not a reservation.

---

## 0.7 A backend you can actually run

This is deliberately a small server with no framework or package installation. Read the control flow now; M1/M4 will teach the JavaScript and Node mechanisms in detail.

### Files and commands

From the repository root:

```powershell
node examples/resume-skills/module-0-backend/verify.mjs
node examples/resume-skills/module-0-backend/server.mjs
```

The verifier starts its own server on an available loopback port and closes it when finished. The manual server uses port 3100; stop it with Ctrl+C after exploring.

Open these URLs while the manual server is running:

```text
http://127.0.0.1:3100/health
http://127.0.0.1:3100/api/products/7
http://127.0.0.1:3100/api/quote?productId=7&quantity=2
```

### Server code

The code below is the complete preserved server, not a separate untested version.

```javascript
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

export function createDemoServer({ trace = () => {} } = {}) {
  // Process memory, not a database. Each new server starts with the same seed.
  const products = new Map([
    [7, { id: 7, name: 'Notebook', unitPricePaise: 25000, stock: 4 }],
  ]);

  function findProduct(rawId) {
    if (!/^[1-9][0-9]*$/.test(rawId ?? '')) {
      return { status: 400, error: 'invalid_product_id' };
    }
    const id = Number(rawId);
    if (!Number.isSafeInteger(id)) {
      return { status: 400, error: 'invalid_product_id' };
    }
    const product = products.get(id);
    return product
      ? { product }
      : { status: 404, error: 'product_not_found' };
  }

  return createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    trace('receive ' + req.method + ' ' + url.pathname);
    function send(status, data, headers = {}) {
      res.writeHead(status, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store',
        ...headers,
      });
      res.end(JSON.stringify(data));
      trace('respond ' + status);
    }

    const productMatch = /^\/api\/products\/([^/]+)$/.exec(url.pathname);
    const knownRoute = url.pathname === '/health' ||
      url.pathname === '/api/quote' || productMatch;
    if (!knownRoute) return send(404, { error: 'route_not_found' });
    if (req.method !== 'GET') {
      return send(405, { error: 'method_not_allowed' }, { Allow: 'GET' });
    }
    if (url.pathname === '/health') return send(200, { ok: true });

    trace('route ' + (productMatch ? 'product' : 'quote'));
    const found = findProduct(productMatch ? productMatch[1] : url.searchParams.get('productId'));
    if (found.error) return send(found.status, { error: found.error });
    trace('repository product=' + found.product.id);
    if (productMatch) return send(200, found.product);

    const rawQuantity = url.searchParams.get('quantity');
    if (!/^[1-9][0-9]*$/.test(rawQuantity ?? '')) {
      return send(400, { error: 'invalid_quantity' });
    }
    const quantity = Number(rawQuantity);
    if (!Number.isSafeInteger(quantity)) {
      return send(400, { error: 'invalid_quantity' });
    }
    if (quantity > found.product.stock) {
      return send(409, { error: 'insufficient_stock' });
    }
    // Price comes from our stored record. A client-supplied price is not used.
    const totalPaise = found.product.unitPricePaise * quantity;
    trace('service totalPaise=' + totalPaise);
    return send(200, {
      productId: found.product.id, quantity, totalPaise,
      currency: 'INR', reserved: false,
    });
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const server = createDemoServer({ trace: console.log });
  server.listen(3100, '127.0.0.1', () => {
    console.log('Demo listening at http://127.0.0.1:3100');
  });
}
```

### Read it in four passes

**Pass 1 — receiving.** createServer registers the handler; listen starts accepting connections. The callback receives request/response objects.

**Pass 2 — routing.** We recognize the path and then check the method. An unknown path returns route_not_found; a known path with POST returns method_not_allowed.

**Pass 3 — rules.** IDs/quantities must be positive decimal safe integers. A valid missing product is different from an invalid ID. The quote reads the price from the stored record and checks current stock.

**Pass 4 — responding.** send chooses the status and headers, serializes the data, and ends the response. Returning a value from the callback alone would not send an HTTP response.

The request-handler mechanism is documented in [Node's HTTP transaction guide](https://nodejs.org/fr/learn/modules/anatomy-of-an-http-transaction). The source above is our original learning example.

### The price-tampering case

The verifier requests:

```text
/api/quote?productId=7&quantity=2&unitPricePaise=1
```

Actual parsed response:

```json
{"productId":7,"quantity":2,"totalPaise":50000,"currency":"INR","reserved":false}
```

The supplied price does not participate in the calculation. The API contract uses productId and quantity; its authoritative record holds 25000 paise per notebook.

Ignoring this extra field is a deliberate demonstration choice. Production contracts can reject unknown fields. The security property here is that a client cannot override the authoritative price.

### The request trace

Captured by the verifier:

```text
receive GET /api/quote
route quote
repository product=7
service totalPaise=50000
respond 200
```

“Repository” and “service” describe logical responsibilities. Here they execute inside the same callback/process; the map lookup is not a database network request.

### Actual verification output

```text
PASS health -> 200
PASS stored product -> 200
PASS invalid ID -> 400
PASS unknown product -> 404
PASS unknown route -> 404
PASS unsupported method -> 405
PASS missing quantity -> 400
PASS zero quantity -> 400
PASS fractional quantity -> 400
PASS unsafe integer ID -> 400
PASS unavailable quantity -> 409
PASS forged price ignored -> 200
PASS quote does not reserve stock -> 200
TRACE receive GET /api/quote -> route quote -> repository product=7 -> service totalPaise=50000 -> respond 200
Verified 13 HTTP cases; Node v22.14.0
```

The verifier asserts statuses, parsed response bodies, JSON content type, the Allow header on 405, the quote trace and unchanged stock after quoting. An unexpected result fails the run.

### What this proves — and its limits

It demonstrates HTTP handling, route/method distinction, input checks, server-controlled computation and response serialization.

The store is a seeded in-memory map. There is no durable database, authentication, order, inventory reservation, payment or production hardening. The health endpoint shows the handler is responsive; it does not prove database readiness or end-to-end health.

Thirteen passing cases verify those cases. They are not a claim that arbitrary input, production load or every failure is handled.

---

## 0.8 Validation, business rules and error handling

These are related but different.

| Concern | Question | Example |
| --- | --- | --- |
| **Validation** | Is this a structurally acceptable input? | quantity must be a positive integer |
| **Authentication** | Who is making the request? | Verify a session credential |
| **Authorization** | May this caller perform this action on this resource? | May this user read this private document? |
| **Business rule** | Is the operation allowed by the product's current rules/state? | Requested quantity exceeds availability |
| **Unexpected failure** | Did a dependency or program fail outside the expected operation result? | Database connection lost |

A syntactically valid quantity can still be unavailable. An authenticated user can still lack permission.

### The example's error contract

| Request | Status | Body error |
| --- | --- | --- |
| GET /api/products/seven | 400 | invalid_product_id |
| GET /api/products/99 | 404 | product_not_found |
| GET /api/missing | 404 | route_not_found |
| POST /api/products/7 | 405 | method_not_allowed |
| Quote without quantity | 400 | invalid_quantity |
| Quote for five units when four are available | 409 | insufficient_stock |

These mappings are the chosen contract for this demonstration. HTTP allows design choices, and another API might express an availability failure differently. Be consistent and explain the meaning.

### Expected rejection vs crash

A customer requesting an unavailable quantity is not a reason to crash the process. Return a deliberate response.

An unexpected exception should be logged and mapped to a safe error response where possible. Do not leak secrets or internal stack traces. Framework error handling is taught in M5/M11.

Do not say “a 500 means the database is down.” It describes a server-side failure category; the underlying cause needs logs and traces.

**Practice checkpoint:** which check catches quantity=0, which catches a request for another user's document, and which catches a valid request for the last unavailable item?

---

## 0.9 Where state lives

A system may contain several kinds of state.

```text
Browser UI state        selected quantity, current loading indicator
Application memory      this example's products map
Persistent database     durable product/order records in a real application
Cache                   a reusable copy with an expiry/update policy
Object storage          uploaded files or generated documents
Queue                   pending work and its delivery/progress state
External provider       payment outcome or message-delivery state
```

### HTTP statelessness is not “the application stores nothing”

HTTP does not automatically preserve your application's user session across requests. Applications add identity/session mechanisms and store whatever product state they need.

“Stateless application instance” usually means a request can be handled without relying on irreplaceable state stored only in that instance. Shared databases or session stores can still hold state.

### Why process memory is not a durable store

If we changed the demo's map:

- Restarting the process would lose that change and recreate the seed.
- A second independently started process would have its own map.
- Scaling to two processes would not automatically synchronize their records.

The example performs only reads, so unchanged stock after a quote is intentional. To build real booking, move inventory correctness into a shared authoritative store and use atomic operations/transactions.

**Link back:** DBMS Modules 7–9 cover storage, transactions and recovery. Architecture S4 will use those guarantees to prevent overselling.

### A database client is not the database

The application uses client code to send operations through a connection to a DBMS. A connection pool reuses a bounded set of connections; it is not a second copy of all the data.

M13 teaches the practical PostgreSQL version. Keep this distinction now so “the backend queries the database” means a specific interaction.

---

## 0.10 Layers, services and deployment

A growing application often separates responsibilities:

```text
HTTP/controller layer     translate request/response
          |
Service/application layer enforce the use case and business rules
          |
Repository/data layer     read/write records
```

This can be three files in one process. Extracting a class or function does not create a microservice.

### Why make the separation?

- A business rule can be tested without constructing an HTTP request.
- A use case can be invoked from an API or a worker.
- Storage-specific operations are easier to locate.
- Input/output concerns do not bury the main rule.

For a tiny example, putting these responsibilities together can be clearer. Introduce boundaries when they make ownership and change easier to reason about.

### Three architectural views

| View | What it shows | Example |
| --- | --- | --- |
| Logical | Responsibilities and dependencies | Controller -> quote service -> product repository |
| Runtime | Processes and communications | API process -> database process |
| Deployment | Where runtime components run | Two containers on a VM behind a proxy |

A useful diagram says which view it shows. Otherwise three boxes might accidentally be interpreted as three machines.

### What “deployed” means

A deployment makes a specific application version run in an environment with configuration, dependencies and a way to receive traffic.

The essential questions are:

1. Which process starts, and who restarts it if it exits?
2. Where do configuration and secrets come from?
3. How do clients reach the right application?
4. Where does durable state live?
5. How do we observe failures and roll back?

AWS, Docker, Nginx and CI/CD answer parts of those questions. They are not substitutes for the application's business rules.

---

## 0.11 Concurrency, slow operations and background work

### Latency vs throughput

- **Latency:** how long a particular operation takes.
- **Throughput:** how many operations complete per unit time.
- **Concurrency:** how many operations are in progress at once.

These are not interchangeable measurements. Many requests can be waiting on I/O even while only one JavaScript callback is executing on a given event-loop thread.

Do not infer “one request at a time” merely because Node executes ordinary JavaScript callbacks on one event-loop thread. M2/M4 will unpack the runtime.

### When should work leave the request?

Consider uploading a PDF that needs parsing and embedding.

```text
Request path:
validate upload -> record job -> return accepted job ID

Worker path:
claim job -> parse -> process -> save result -> update job status
```

This allows the client to check progress without holding one request open for the entire workflow. It adds new responsibilities: durable job creation, retries, duplicate handling and failure status.

Returning “accepted” is not the same as completing the work.

For a short read-only quote, a queue would add unnecessary complexity. Choose asynchronous work because the operation needs its properties.

### Availability checks can race

```text
Request A: reads stock = 1
Request B: reads stock = 1
Request A: decides "available"
Request B: decides "available"
```

If both then sell the item without an atomic state change, both can succeed incorrectly. A “check” and its later “update” are separate operations unless a mechanism ties them together.

Our quote reserves nothing, so it makes no promise that inventory remains available for a later purchase. This is why the response explicitly says reserved=false.

**Next architectural skill:** identify the invariant before choosing a lock, transaction or queue. For booking: the same unit must not be allocated twice.

---

## 0.12 Connecting this to your resume

Use these as explanation structures, not claims that the underlying implementations have been inspected.

| Documented work | Request/data flow to be able to explain | Likely follow-up |
| --- | --- | --- |
| Express load balancer | Client -> routing decision -> selected backend -> proxied response | How are nodes selected and failures detected? |
| Next.js/FastAPI BFF | Browser -> server-side proxy -> authenticated upstream -> response | Which credential crosses each boundary? |
| Candidate portal | Invite -> verification -> scoped operation -> stored assessment | How is expiry/revocation enforced? |
| AI document corpus | Upload -> queued processing -> stored vectors -> retrieval | What happens when a worker retries? |
| Payment/credit flow | Order -> provider outcome -> verified event -> ledger effect | How are duplicate events prevented from charging twice? |
| HR data import | External rows -> validation/matching -> stored records -> UI | How do partial batches and timestamps affect correctness? |

A good explanation names the **input, authority, rule, state and outcome**. Merely listing the frameworks leaves all five unanswered.

### The 30-second “what does your backend do?” template

“My backend receives [operation] from [client]. It verifies [identity/input], applies [rule] using [authoritative store], and returns [result]. Slow work goes through [job mechanism] where needed. The main correctness risk is [failure/race], which is handled by [mechanism].”

Fill in only details supported by your implementation or documented experience. M28 will turn these into project-specific answers.

---

## 0.13 Confusable pairs

| Pair | The distinction to remember |
| --- | --- |
| Frontend vs backend | Presentation/interaction vs server-side authority and application rules; server-rendered UI can cross the simple location boundary |
| Language vs runtime | Program semantics vs environment executing the program and exposing APIs |
| Node.js vs Express | Runtime vs framework built on it |
| API vs endpoint | A contract/interface vs a particular network operation entry point |
| Process vs machine | Executing program instance vs the host providing resources |
| Port vs route | Transport endpoint selection vs application operation selection |
| Web server vs application server | HTTP/static/proxy duties vs product logic; roles can overlap |
| Controller vs service | Protocol translation vs use-case rules |
| Repository vs database | Application data-access boundary vs the actual data-management system |
| Validation vs authorization | Acceptable input shape/value vs permission for caller/action/resource |
| Authentication vs authorization | Identity vs permission |
| Quote vs reservation | Current information vs a state change allocating a resource |
| Cache vs source of truth | Reusable copy vs authoritative record |
| Accepted vs completed | Work recorded for processing vs the requested effect finished |
| Latency vs throughput | Duration per operation vs completions per unit time |
| HTTP stateless vs stateless instance | Protocol/session behavior vs where an application instance keeps irreplaceable state |
| Layer vs microservice | Logical responsibility vs independently communicating/deployable service boundary |

---

## Must remember

1. A server-side boundary exists because callers control their clients.
2. Frontend validation improves feedback; authoritative checks still run server-side.
3. Node.js can serve HTTP directly; Express adds application structure/conveniences.
4. The process handles requests, not the source file sitting on disk.
5. The method and path together participate in selecting an operation.
6. JSON serialization turns in-memory data into response bytes.
7. A value returned from a handler is not automatically an HTTP response in Node's raw HTTP API.
8. A valid input can still violate a business rule or a permission.
9. A quote is not a reservation; checking availability is not allocating inventory.
10. Process-local memory does not automatically survive restart or synchronize across replicas.
11. Logical layers can all live in one process.
12. A client timeout does not prove that a server-side effect never happened.
13. A queue changes completion and failure handling; it does not remove that work.
14. A health response is evidence about the checks it actually performs.
15. Start a system explanation with inputs, rules, authoritative state and outcomes.

---

## Common wrong answers

| Wrong answer | Better reasoning |
| --- | --- |
| “The backend is the database.” | It is application behavior that may use a database and other services |
| “Node.js is a programming language.” | JavaScript is the language; Node.js is a runtime environment |
| “Express is required to create an HTTP server.” | Node provides HTTP APIs; Express makes common application tasks easier |
| “The UI prevents users changing the price.” | Requests can bypass the UI; the server chooses/verifies authoritative pricing |
| “Logged in means permitted.” | Authorization must check the action and resource |
| “Three layers means three microservices.” | Layers can be functions/files inside one process |
| “GET means there can be no side effects at all.” | Safe-method semantics concern requested effects; logs/metrics can still be recorded |
| “The request timed out, so retrying a payment is safe.” | The outcome can be uncertain; use idempotency and reconciliation |
| “HTTP is stateless, so no data is stored.” | Application data/session state can exist independently of protocol statelessness |
| “The map is our production database.” | It is volatile process-local state in this teaching example |
| “200 on /health proves every dependency is healthy.” | Only checks performed by that endpoint are established |
| “500 tells me which dependency broke.” | Logs/traces and the actual failure context identify the cause |

---

## Interview Q&A bank

**Q1. What is a backend?**
Server-side application behavior that receives requests, enforces rules/permissions, coordinates state/services and returns results.
**Follow-up:** Can the frontend and backend live in the same repository? Yes; repository layout does not define the trust boundary.

**Q2. Why not put every rule in the frontend?**
The caller controls the client and can bypass its UI. Shared correctness, privileged access and durable effects need authoritative server-side enforcement.
**Follow-up:** Why keep client validation? Fast feedback and usability.

**Q3. Is a server a machine or a program?**
Both uses exist. In request handling, I usually mean a running process/service listening for work; a machine hosts that process.
**Follow-up:** Can one machine run several servers? Yes, subject to resources and endpoint configuration.

**Q4. What is Node.js, and where does Express fit?**
Node.js executes JavaScript outside the browser with server-side APIs. Express is a framework that organizes routing and middleware on top of that runtime.
**Follow-up:** Can Node serve HTTP alone? The example does.

**Q5. What happens when a request reaches a backend?**
The runtime exposes the request, the router selects an operation, checks run, business logic accesses authoritative state, and the handler produces a response.
**Follow-up:** Which checks can be skipped? Only those irrelevant to a deliberately public operation, not because the UI already did them.

**Q6. What is an API?**
A software contract describing how to request capabilities and interpret results. A web endpoint is one way to expose it.
**Follow-up:** Is every API REST? No.

**Q7. What is an endpoint?**
An entry point for an operation. In an HTTP API it is commonly described with a method and route, such as GET /api/products/7.
**Follow-up:** Does the URL point to a source file? It can be dispatched to code rather than a file.

**Q8. How are route and port different?**
The port participates in transport delivery to a listening endpoint; the route is interpreted by the application to choose behavior.
**Follow-up:** Can several routes share a port? Yes.

**Q9. Is JSON a JavaScript object?**
JSON is a data representation. An object in memory is serialized into JSON bytes and parsed into a client's own data structures.
**Follow-up:** Does sending JSON make an API REST? No.

**Q10. What are validation and business logic?**
Validation checks whether input is acceptable; business logic applies the product's rules using context/state. A positive quantity is valid but may be unavailable.
**Follow-up:** Where does authorization fit? It checks caller permission for the action/resource.

**Q11. Why does the server ignore the supplied price?**
Price is authoritative server data; accepting a caller's override would let that caller set their own charge.
**Follow-up:** Can the client send a price preview? Yes, but it must not become authoritative.

**Q12. Why is a quote not a booking?**
It reports a current calculation and changes no allocation state. A booking must atomically claim the resource and define expiry/payment behavior.
**Follow-up:** What race occurs between checking and booking? Another caller can consume the resource.

**Q13. Why use a database instead of a map?**
A real DBMS can supply persistence, shared access, queries, constraints and concurrency/recovery mechanisms. The exact guarantees depend on the engine/configuration.
**Follow-up:** Does every application need one? No; choose it for the state and correctness needs.

**Q14. Is the application stateless if it uses a database?**
An instance can avoid relying on local irreplaceable state while using a shared persistent database. That differs from claiming the whole system has no state.
**Follow-up:** Where are sessions stored? It depends on the session/token design.

**Q15. What does a reverse proxy do?**
It accepts requests on behalf of upstream services and forwards them. It can also handle duties such as TLS termination and routing.
**Follow-up:** Must it be a separate machine? No.

**Q16. Why have controller, service and repository layers?**
They separate protocol concerns, product rules and storage access, making responsibilities easier to change/test.
**Follow-up:** Must a tiny service have all three classes? No; keep the separation useful.

**Q17. What if the client times out?**
The server may still have completed or be executing the work. The caller needs a way to establish the outcome for operations with effects.
**Follow-up:** What makes a retry safe? Defined idempotency and outcome handling.

**Q18. When should work run in a background job?**
When delayed/asynchronous completion and durable processing fit the operation, such as document ingestion. Record progress and define retry/failure behavior.
**Follow-up:** Does returning accepted prove success? It proves acceptance under the stated contract, not completion.

**Q19. What does deploying a backend involve?**
Run a version with configuration/dependencies, connect durable state, expose it appropriately and provide restart/monitoring/rollback mechanisms.
**Follow-up:** Is installing Node enough? It provides a runtime, not those application/deployment decisions.

**Q20. What did this example verify?**
Thirteen loopback request cases verified the chosen API contract and server-controlled quote computation. They did not exercise a database, authentication, payments or production scale.
**Follow-up:** How would you extend the verification? Add the important new failure/permission/concurrency cases as those features are introduced.

---

## Practice

1. **Draw the path.** A browser asks for its private documents. Mark client, handler, identity check, permission check, data access and response.
2. **Place the names.** Label Python, FastAPI, an ASGI server, PostgreSQL and a reverse proxy on one logical/runtime diagram.
3. **Predict the result.** Before running the verifier, name the status for invalid ID, missing product, unsupported method and unavailable quantity.
4. **Change the price input.** Request quantity=2 with unitPricePaise=1. Explain the actual total from the authoritative record.
5. **Extend the rule.** Add a per-request maximum quantity of three. Decide the error contract, then add a verifier case. State which existing outcomes change.
6. **Find the trust mistake.** A private-document endpoint accepts ownerId from the query and reads that owner's documents. Explain the missing authority check.
7. **Design the next step.** Add actual inventory reservation on paper. State the invariant, authoritative store and atomic operation before discussing a framework.

### Answer checkpoints

- **1/6:** derive identity from a verified mechanism and authorize the requested resource; a caller's ownerId assertion cannot grant access.
- **3:** this example maps them to 400, 404, 405 and 409 respectively.
- **4:** totalPaise=50000; the extra caller-supplied price is unused.
- **5:** structural validation and a product-specific limit need deliberate ordering; retain valid normal cases and test the limit boundary.
- **7:** two callers must not both allocate the same stock. The read/check/write boundary needs a shared atomicity mechanism.

Do not mark a practice task finished because the diagram looks plausible. Trace a successful call and one failure through it.

---

## Exit checklist

- [ ] I can explain frontend/backend responsibilities without equating frontend with browser-only execution.
- [ ] I can place language, runtime, framework, application and DBMS correctly.
- [ ] I can distinguish a process, machine, port and route.
- [ ] I can trace an HTTP request through validation, rules, data access and response.
- [ ] I can explain why client validation and client prices are not authoritative.
- [ ] I can distinguish validation, authentication, authorization and business rules.
- [ ] I can run the example and explain all thirteen outcomes.
- [ ] I understand what the example has not verified.
- [ ] I can explain why a quote is not a reservation.
- [ ] I can explain process-local memory vs shared durable state.
- [ ] I can distinguish logical layers from deployed services.
- [ ] I can describe latency, throughput and concurrency.
- [ ] I can explain a client timeout without assuming the server did nothing.
- [ ] I can describe one resume flow using input, authority, rule, state and outcome.

---

## Next

[M1: JavaScript Fundamentals for Interviews](/docs/resume-skills/javascript-fundamentals) builds the language model needed for Node.js: types and references, scope/hoisting, closures, this, objects/prototypes and short output-prediction drills.

After API/data basics are in place, architecture A0/A1 will turn this request picture into a design method; URL shortening will be the first worked system.

### Sources and verification artifacts

- [MDN: introduction to server-side programming](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Introduction) and [client/server overview](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Client-Server_overview): introductory context.
- [MDN: HTTP messages](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages) and [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html): message and method/status semantics.
- [Node.js: HTTP transaction anatomy](https://nodejs.org/fr/learn/modules/anatomy-of-an-http-transaction) and [HTTP API](https://nodejs.org/api/http.html): request-handler APIs; the executable example was specifically verified on v22.14.0.
- [Nginx beginner's guide](https://nginx.org/en/docs/beginners_guide.html): static-serving/proxy responsibilities.
- [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): request/resource permission checks.
- Preserved files: examples/resume-skills/module-0-backend/server.mjs, verify.mjs and verification-output.txt.
