# Resume Skills Placement Handbook — Part 13
# Module 11: Flask, FastAPI and Python Request Handling

**Module 11 · 4–5 hours · Tier 2; core depth for Python backend roles · Requires: M6, M10; M7-M8 for authentication/authorization boundaries**

---

## Why this module matters

Knowing Python syntax does not explain what receives an HTTP connection, when a route runs, which thread executes a blocking function, or who closes a request resource. Framework questions become easier when you can trace those responsibilities separately.

An interviewer may start with “Flask versus FastAPI?” and then ask “What is ASGI?”, “Does async Flask handle unlimited requests?”, “Where does Pydantic validate?”, “What if a background task fails?” or “Can a dependency keep a database session alive during streaming?”

> **A framework adapts a server protocol into application calls. Input, execution, resource lifetime and response serialization each need an explicit contract.**

This module builds the same quote/product domain behind Flask and FastAPI adapters, then verifies their request paths and execution models. It also lays out how to build an ingestion API without confusing request-local tasks with durable jobs.

**Verification: 80 checks passed — two protocol checks, ten Pydantic checks, 52 real HTTP checks and 16 framework-runtime checks.**

### Recorded environment

| Component | Executed version |
| --- | --- |
| Interpreter | CPython 3.12.10, 64-bit Windows |
| Flask / Werkzeug | 3.0.3 / 3.1.2 |
| FastAPI / Starlette | 0.142.2 / 1.7.0 |
| Pydantic / pydantic-core | 2.13.5 / 2.46.5 |
| Uvicorn / HTTPX | 0.54.0 / 0.28.1 |
| AnyIO / asgiref | 4.15.1 / 3.12.1 |

M10 used CPython 3.13.15. This module uses a separate Python 3.12 environment because compatible cached binary wheels were available locally. Dependencies were installed offline into the example's ignored `.venv`; global packages were not changed.

These are reproducible teaching pins, **not a recommendation to deploy this historical Flask stack**. Official Flask stable documentation currently targets 3.1.x and FastAPI's release notes include newer versions. Current deployment choices require current supported/security-reviewed dependencies. Version-sensitive cleanup and TestClient behavior below are tied to the executed stack, not assumed universal. References: [Flask changes](https://flask.palletsprojects.com/en/stable/changes/), [FastAPI releases](https://fastapi.tiangolo.com/release-notes/).

### Run the examples

From the repository root, using the prepared environment:

```powershell
./examples/resume-skills/module-11-python-frameworks/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-11-python-frameworks/verify.py
```

To recreate it elsewhere, first select a Python 3.12 interpreter. With `python` referring to that interpreter:

```powershell
python -m venv examples/resume-skills/module-11-python-frameworks/.venv
./examples/resume-skills/module-11-python-frameworks/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-11-python-frameworks/requirements.lock.txt
./examples/resume-skills/module-11-python-frameworks/.venv/Scripts/python.exe -m pip check
```

Installation normally needs a package index. This machine used cached wheels with `--no-index --find-links`; the local wheelhouse and environment are ignored, while package pins and verification source are preserved. The lock is an exact package-version snapshot, not a cryptographically hashed cross-platform lock.

The HTTP verifier starts Werkzeug and Uvicorn on automatically selected **loopback** ports, runs requests, stops its own listeners and checks that they are closed. Werkzeug is used only as a development/test WSGI server. No persistent server is started, and port 3000 stays stopped.

The pinned Starlette TestClient emits one known deprecation warning about its HTTPX adapter. The aggregate verifier recognizes that warning and preserves it in `expected-warning-output.txt`; other unexpected stderr fails verification. No HTTPX2 migration was performed.

---

## 11.1 What does each layer do?

**Flask and FastAPI are Python web frameworks. WSGI and ASGI are interfaces between servers and applications. Uvicorn is an ASGI server. Pydantic parses/validates and serializes data models.** Your service code still owns pricing, permissions and durable state.

```text
Client
  |
HTTP connection / reverse proxy
  |
Application server: socket handling, protocol adaptation, concurrency policy
  |
WSGI or ASGI application interface
  |
Framework: routing, request handling, dependencies/hooks, errors, responses
  |
Application service: trusted identity, business rules, data access
  |
Database / queue / external provider
```

This is an architectural map, not a deployed system measurement. A reverse proxy such as Nginx may sit in front, but it does not run your Python business function merely because it forwarded the request.

| Question | Owning layer |
| --- | --- |
| Who accepts the TCP connection? | Server/proxy |
| Which function handles POST /api/quotes? | Framework router |
| Is quantity an allowed integer? | Configured input validation |
| Whose tenant/product may be used? | Authentication plus application authorization/data access |
| Does a quote create an order? | Domain contract/persistence |
| Is a sync handler offloaded? | Framework/server execution model |
| Which fields reach the client? | Response serialization policy |
| Will work survive a process restart? | Durable job/state design |

A framework's convenient API does not erase the underlying interface. You should be able to explain both the user-facing route and the call made by the server.

---

## 11.2 WSGI versus ASGI

### WSGI: an application callable and a byte iterable

A WSGI server calls an application with `environ` and `start_response`. The application supplies status/headers and returns an iterable yielding response-body bytes. The server handles transmission and must manage the iterable's lifecycle. Reference: [WSGI, PEP 3333](https://peps.python.org/pep-3333/).

WSGI does not mean “one request for the entire machine.” A server can use threads, worker processes or other supported strategies. A conventional synchronous worker slot remains occupied by its active request. Worker policy is a server/deployment choice, not a universal WSGI thread count.

### ASGI: scope plus asynchronous receive/send

An ASGI application receives connection/request metadata in `scope` and exchanges protocol events through awaitable `receive` and `send` functions. HTTP request bodies can arrive in chunks; HTTP response messages are sent separately. ASGI defines protocols for HTTP, WebSockets and lifespan. Reference: [ASGI specification](https://asgi.readthedocs.io/en/stable/specs/main.html).

ASGI permits async coordination; it does not turn synchronous CPU work into non-blocking work. The application still must avoid blocking its event-loop thread and use bounded resources.

### Executed protocol examples: protocols.py

These tiny applications demonstrate call shapes only. The ASGI example supports HTTP, not lifespan or WebSockets. Neither is a production server, HTTP parser, authenticated API or safe unbounded upload handler.

```python
"""Tiny protocol examples, not production servers or complete HTTP applications."""
import json

def wsgi_app(environ, start_response):
    body = json.dumps({'method': environ['REQUEST_METHOD'], 'path': environ['PATH_INFO']}).encode()
    start_response('200 OK', [('Content-Type','application/json'), ('Content-Length',str(len(body)))])
    return [body]

async def asgi_app(scope, receive, send):
    if scope['type'] != 'http':
        raise ValueError('HTTP-only teaching example')
    size = 0
    while True:
        event = await receive()
        if event['type'] == 'http.disconnect':
            return
        size += len(event.get('body', b''))
        if not event.get('more_body', False):
            break
    body = json.dumps({'method': scope['method'], 'path': scope['path'], 'bytes':size}).encode()
    await send({'type':'http.response.start', 'status':200,
                'headers':[(b'content-type',b'application/json')]})
    await send({'type':'http.response.body', 'body':body, 'more_body':False})
```

The verifier invokes WSGI through the standard-library validator and invokes ASGI with two request-body events. These are in-process protocol checks, separate from the 52 socket-level framework checks.

Observed results:

```json
{
  "wsgi": {
    "status": "200 OK",
    "body": {
      "method": "GET",
      "path": "/probe"
    }
  },
  "asgi": {
    "status": 200,
    "body": {
      "method": "POST",
      "path": "/probe",
      "bytes": 3
    }
  }
}
```

| Aspect | WSGI | ASGI |
| --- | --- | --- |
| Typical call shape | callable(environ, start_response) | async callable(scope, receive, send) |
| HTTP input | Environment and input stream | Metadata scope and request events |
| HTTP output | Status/headers plus iterable of bytes | Response-start/body events |
| Framework here | Flask | FastAPI |
| Async handler implications | Flask bridges within a WSGI request | Async endpoints can suspend on the server loop |
| WebSockets | Not provided by WSGI itself | Protocol supported by ASGI; server/app must implement it |

Wrapping a WSGI app in an ASGI adapter allows interoperability; it does not automatically rewrite its blocking internals into an async-native application.

---

## 11.3 Shared application: schemas, identity and tenant-scoped catalog

The examples expose these small operations:

| Request | Purpose |
| --- | --- |
| GET /health | Public liveness-style fixture |
| POST /api/quotes | Validate quantity; calculate a non-persisted quote |
| GET /api/products/{product_id} | Fetch a product visible to the authenticated tenant |
| GET /api/products?limit=1 | List that tenant's products with a bounded limit |
| GET /openapi.json and /docs | FastAPI schema/docs routes in this example |

The tokens `alpha-demo-token` and `beta-demo-token` are public opaque fixtures. They are not JWTs, real credentials or an implementation of production login/revocation. M7 supplies the authentication concepts; here the fixture lets tests focus on the framework boundary.

The request cannot choose its own tenant or price. The service scopes the catalog lookup using the principal returned by authentication. Schema validation alone would not enforce that ownership rule.

### Complete shared source: domain.py

The instrumented Lease is a fake request resource used to observe cleanup. Audit is a locked in-memory test log. Catalog is an in-memory read fixture. None is a database transaction, durable ledger, connection pool or job broker.

```python
"""Shared domain and schemas; opaque bearer values are public test fixtures."""
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from pydantic import BaseModel, ConfigDict, Field

class QuoteIn(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=100)

class ProductOut(BaseModel):
    product_id: str
    amount_paise: int
    currency: str

class QuoteOut(BaseModel):
    product_id: str
    quantity: int
    total_paise: int
    currency: str
    created_at: datetime

@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str

TOKENS = {'alpha-demo-token': Principal('u-alpha', 'alpha'),
          'beta-demo-token': Principal('u-beta', 'beta')}

class Unauthenticated(Exception):
    pass

class ProductNotFound(Exception):
    pass

def authenticate(header):
    parts = (header or '').split()
    if len(parts) != 2 or parts[0].lower() != 'bearer' or parts[1] not in TOKENS:
        raise Unauthenticated()
    return TOKENS[parts[1]]

class Audit:
    def __init__(self):
        self.rows = []
        self.lock = Lock()
    def add(self, request_id, event):
        with self.lock:
            self.rows.append((request_id, event))
    def trace(self, request_id):
        with self.lock:
            return [event for rid, event in self.rows if rid == request_id]

class Catalog:
    def __init__(self):
        self.rows = {('alpha', 'basic'): {'product_id': 'basic', 'amount_paise': 12500,
                     'currency': 'INR', 'internal_cost_paise': 7000},
                     ('beta', 'team'): {'product_id': 'team', 'amount_paise': 25000,
                     'currency': 'INR', 'internal_cost_paise': 14000}}
        self.closed = False
    def product(self, principal, product_id):
        if self.closed:
            raise RuntimeError('catalog closed')
        value = self.rows.get((principal.tenant_id, product_id))
        if value is None:
            raise ProductNotFound()
        return dict(value)
    def products(self, principal, limit):
        return [dict(value) for (tenant, key), value in sorted(self.rows.items())
                if tenant == principal.tenant_id][:limit]
    def close(self):
        self.closed = True

class Lease:
    """Instrumented request resource, not a database session."""
    def __init__(self, audit, request_id):
        self.audit, self.request_id, self.closed = audit, request_id, False
        audit.add(request_id, 'lease-open')
    def close(self):
        if self.closed:
            raise RuntimeError('lease closed twice')
        self.closed = True
        self.audit.add(self.request_id, 'lease-close')

def build_quote(catalog, principal, body, now):
    price = catalog.product(principal, body.product_id)
    return {'product_id': body.product_id, 'quantity': body.quantity,
            'total_paise': price['amount_paise'] * body.quantity,
            'currency': price['currency'], 'created_at': now.astimezone(timezone.utc),
            'internal_cost_paise': price['internal_cost_paise'],
            'tenant_id': principal.tenant_id}

FIXED_NOW = datetime(2026, 10, 14, 6, 30, tzinfo=timezone.utc)
```

The service includes internal fields so response filtering can be tested meaningfully. Production code may choose an explicit domain-to-response mapper instead; a public schema is not permission to return arbitrary internal state.

QuoteIn is strict and forbids extra keys. ProductOut and QuoteOut deliberately use Pydantic's default extra-ignore behavior when validating the service output. These are different input/output policies chosen for this example.

The fixed aware UTC clock makes responses reproducible. This chapter's service is a transient quote calculation; it does not lock a price, reserve stock, charge a payment or persist anything. The application trusts validated QuoteIn and the supplied principal on its internal path; constructing arbitrary objects or bypassing validation does not create a secure entry point.

---

## 11.4 Flask request lifecycle, contexts and blueprints

Flask adapts a WSGI request into its request objects, routing and view calls. A simplified successful flow is:

```text
server calls Flask WSGI app
  -> create/push application and request contexts
  -> match route
  -> before_request hooks
  -> route/view function
  -> convert return value to Response
  -> after_request hooks
  -> return WSGI response
  -> teardown/context cleanup
```

Routing errors, early hook responses, error handlers and streaming introduce additional details. Reference: [Flask application lifecycle](https://flask.palletsprojects.com/en/stable/lifecycle/).

### request, current_app and g are context-local accessors

`request` represents the active request; `current_app` resolves the active application; `g` stores data on the current application context. They are convenient proxies, not a single process-global request object. In ordinary request handling, the application context accompanies the request and is popped afterwards. See [request context](https://flask.palletsprojects.com/en/stable/reqcontext/).

The runtime verifier establishes that `request.path` outside a request context raises RuntimeError and that a value placed in g by one ordinary request is absent in the next. Manually extended application contexts have their own lifetime; do not turn the ordinary request observation into “g is always tied only to one HTTP request.”

Use a request-local holder for a checked principal or resource handle. Use shared external storage for information that must survive requests/processes. Passing a context proxy into a later job is not a reliable way to pass identity; pass explicit verified IDs and recheck authorization as appropriate.

### Blueprint versus application factory

A Blueprint collects routes/hooks under a reusable organizational unit. It is registered on an application, possibly with a prefix. It is not an independently running server or a separate process.

An application factory constructs/configures the Flask app and registers its components. It supports explicit configuration, independent tests and cleaner extension initialization. Complete setup before serving; changing routes/configuration in one live worker does not configure every other worker. References: [blueprints](https://flask.palletsprojects.com/en/stable/blueprints/), [application factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/).

### Complete adapter: flask_app.py

```python
from uuid import uuid4
from flask import Flask, Blueprint, g, request, jsonify, current_app
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException
from domain import (Audit, Catalog, Lease, QuoteIn, QuoteOut, ProductOut,
                    Unauthenticated, ProductNotFound, authenticate, build_quote, FIXED_NOW)

api = Blueprint('api', __name__, url_prefix='/api')

@api.before_request
def prepare():
    g.request_id = uuid4().hex
    current_app.extensions['audit'].add(g.request_id, 'before')
    g.lease = Lease(current_app.extensions['audit'], g.request_id)
    try:
        g.principal = authenticate(request.headers.get('Authorization'))
    except Unauthenticated:
        return jsonify(error='unauthenticated'), 401, {'WWW-Authenticate': 'Bearer'}

@api.post('/quotes')
def quote():
    if not request.is_json:
        return jsonify(error='expected_json'), 415
    body = QuoteIn.model_validate(request.get_json())
    current_app.extensions['audit'].add(g.request_id, 'route')
    value = build_quote(current_app.extensions['catalog'], g.principal, body,
                        current_app.config['CLOCK']())
    return jsonify(QuoteOut.model_validate(value).model_dump(mode='json'))

@api.get('/products/<product_id>')
def product(product_id):
    current_app.extensions['audit'].add(g.request_id, 'route')
    value = current_app.extensions['catalog'].product(g.principal, product_id)
    return jsonify(ProductOut.model_validate(value).model_dump(mode='json'))

@api.get('/products')
def products():
    text = request.args.get('limit', '10')
    if not text.isascii() or not text.isdecimal() or not 1 <= int(text) <= 10:
        return jsonify(error='invalid_limit'), 400
    values = current_app.extensions['catalog'].products(g.principal, int(text))
    return jsonify(items=[ProductOut.model_validate(v).model_dump(mode='json') for v in values])

def create_app(*, clock=lambda: FIXED_NOW):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=4096, CLOCK=clock)
    app.extensions['audit'] = Audit()
    app.extensions['catalog'] = Catalog()
    app.register_blueprint(api)

    @app.get('/health')
    def health():
        return {'status': 'ok', 'framework': 'flask'}

    @app.after_request
    def after(response):
        if hasattr(g, 'request_id'):
            app.extensions['audit'].add(g.request_id, 'after')
            response.headers['X-Request-ID'] = g.request_id
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.teardown_request
    def cleanup(error):
        if hasattr(g, 'lease'):
            g.lease.close()
        if hasattr(g, 'request_id'):
            app.extensions['audit'].add(g.request_id, 'teardown')

    @app.errorhandler(ValidationError)
    def invalid(error):
        # Do not echo the whole rejected body or validation internals.
        return jsonify(error='invalid_body'), 422

    @app.errorhandler(ProductNotFound)
    def missing(error):
        return jsonify(error='product_not_found'), 404

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()  # Preserve status and protocol headers such as Allow.
        response.data = app.json.dumps({'error': error.name.lower().replace(' ', '_')})
        response.content_type = 'application/json'
        return response

    return app
```

### Trace a successful request

1. The WSGI server invokes the Flask application.
2. The matched API Blueprint's before hook creates a request ID and instrumented lease.
3. The hook maps the fixture credential to a principal; invalid credentials return a 401 early.
4. The route checks JSON media type, parses JSON and explicitly invokes QuoteIn.model_validate.
5. The shared service scopes product lookup to that principal's tenant and calculates the quote.
6. QuoteOut validates/selects public output fields and converts datetime to its JSON representation.
7. The after hook adds metadata; teardown closes the request lease.

Actual successful trace recorded by the HTTP verifier:

```json
["before","lease-open","route","after","lease-close","teardown"]
```

The hook's early 401 is a real response path; teardown still owns the lease it opened. The verifier checks that every observed opened lease closes once, including rejected paths. It also asserts that invalid 422 bodies do not reach the business-route marker.

### Hooks, error handling and cleanup have different jobs

| Mechanism | Job in this adapter |
| --- | --- |
| Blueprint before_request | Establish request-local metadata/resource and fixture identity |
| Route | Adapt HTTP input to the shared service |
| ValidationError handler | Convert configured input-validation failure to 422 |
| ProductNotFound handler | Convert unavailable tenant-scoped product to 404 |
| HTTPException handler | JSON error body while preserving status/protocol headers |
| after_request | Add response metadata |
| teardown_request | Release the opened request resource |

Do not use teardown to decide whether the public response should have succeeded; it is a cleanup boundary. A handled exception need not appear as an unhandled teardown error. Do not equate “no exception argument” with a committed database transaction.

The HTTPException handler preserves the original response so a 405 retains Allow. Catching every exception and returning a generic successful dict would hide errors and break HTTP semantics. See [Flask error handling](https://flask.palletsprojects.com/en/stable/errorhandling/).

### Flask does not force one validation library

This adapter chooses Pydantic explicitly. Flask's JSON parser alone does not check quantity bounds, business rules or ownership. Another application can use a different validation approach while keeping the same domain invariants.

MAX_CONTENT_LENGTH is configured for this test app and the oversized-body HTTP check returns 413. A deployment still needs server/proxy read limits and timeouts; a small application-level configuration is not a complete ingress policy.

---

## 11.5 FastAPI request handling, routers and dependencies

FastAPI uses Starlette's ASGI machinery for requests/routing and integrates Pydantic models into parsing/validation, serialization and schema generation. It does not replace the ASGI server or your database layer.

A simplified route flow is:

```text
ASGI server invokes app
  -> middleware / route matching
  -> read/parse declared inputs
  -> solve dependency graph and validate values
  -> invoke endpoint with resolved arguments
  -> validate/serialize ordinary return value using response model
  -> send response and finish scoped cleanup/background work
```

This is a conceptual map, not a universal ordering for every failure. For example, a malformed JSON body may fail before a principal dependency runs. Do not claim dependency-based authentication prevents all body parsing. Put ingress budgets at the appropriate outer boundary.

References: [request bodies](https://fastapi.tiangolo.com/tutorial/body/), [dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/).

### Complete adapter: fastapi_app.py

```python
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from domain import (Audit, Catalog, Lease, Principal, QuoteIn, QuoteOut, ProductOut,
                    Unauthenticated, ProductNotFound, authenticate, build_quote, FIXED_NOW)

bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix='/api')

def principal(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    try:
        header = None if credentials is None else credentials.scheme + ' ' + credentials.credentials
        return authenticate(header)
    except Unauthenticated:
        raise HTTPException(401, 'unauthenticated', headers={'WWW-Authenticate': 'Bearer'})

async def lease(request: Request):
    value = Lease(request.app.state.audit, request.state.request_id)
    try:
        yield value
    finally:
        value.close()

async def require_json(request: Request):
    media = request.headers.get('content-type', '').split(';', 1)[0].strip().lower()
    if media != 'application/json' and not (media.startswith('application/') and media.endswith('+json')):
        raise HTTPException(415, 'expected_json')

PrincipalDep = Annotated[Principal, Depends(principal)]
LeaseDep = Annotated[Lease, Depends(lease, scope='function')]

@router.post('/quotes', response_model=QuoteOut, dependencies=[Depends(require_json)])
async def quote(body: QuoteIn, request: Request, who: PrincipalDep, resource: LeaseDep):
    request.app.state.audit.add(request.state.request_id, 'route')
    return build_quote(request.app.state.catalog, who, body, request.app.state.clock())

@router.get('/products/{product_id}', response_model=ProductOut)
async def product(product_id: str, request: Request, who: PrincipalDep, resource: LeaseDep):
    request.app.state.audit.add(request.state.request_id, 'route')
    return request.app.state.catalog.product(who, product_id)

@router.get('/products', response_model=list[ProductOut])
async def products(request: Request, who: PrincipalDep, resource: LeaseDep,
                   limit: Annotated[int, Query(ge=1, le=10)] = 10):
    return request.app.state.catalog.products(who, limit)

def create_app(*, clock=lambda: FIXED_NOW):
    audit = Audit()
    @asynccontextmanager
    async def lifespan(app):
        app.state.catalog = Catalog()
        app.state.clock = clock
        audit.add('application', 'startup')
        try:
            yield
        finally:
            app.state.catalog.close()
            audit.add('application', 'shutdown')

    app = FastAPI(title='Placement Quote API', lifespan=lifespan)
    app.state.audit = audit
    app.include_router(router)

    @app.middleware('http')
    async def request_metadata(request, call_next):
        request.state.request_id = uuid4().hex
        audit.add(request.state.request_id, 'before')
        response = await call_next(request)
        audit.add(request.state.request_id, 'after')
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse({'detail': [{'loc': list(e['loc']), 'type': e['type']}
                                       for e in error.errors()]}, status_code=422)

    @app.exception_handler(ProductNotFound)
    async def missing(request, error):
        return JSONResponse({'error': 'product_not_found'}, status_code=404)

    @app.get('/health')
    async def health():
        return {'status': 'ok', 'framework': 'fastapi'}

    return app
```

APIRouter groups routes and shared declarations before inclusion in the app. It does not create another listening server. Dependencies are functions FastAPI resolves and calls; Depends is a declaration, not a manually created global service singleton.

### Read a route signature as an input map

| Declaration here | Source / meaning |
| --- | --- |
| product_id: str in matching path | Path value |
| limit: Annotated[int, Query(...)] | Parsed query value with declared bounds |
| body: QuoteIn | Declared body model |
| request: Request | Framework request object |
| who: PrincipalDep | Result of the credential/principal dependency |
| resource: LeaseDep | Function-scoped yield dependency result |

Explicit Header/Cookie/Body/Query declarations are useful when inference would be unclear. Query/path values arrive as transport text, so parsing a query integer is a different policy from accepting a quoted JSON quantity. References: [path parameters](https://fastapi.tiangolo.com/tutorial/path-params/), [query parameters](https://fastapi.tiangolo.com/tutorial/query-params/).

### What each dependency owns

HTTPBearer extracts bearer credentials and advertises a security scheme. The principal dependency performs this example's token-to-principal lookup and raises 401 with a challenge. It does not verify a JWT merely because the OpenAPI schema says bearer.

The lease dependency opens a request resource and closes it in finally. Its explicit function scope is chosen to finish before the endpoint response is sent. The resource is not needed by a stream or background task here.

The media-type dependency expresses the adapter's JSON policy. It does not replace streaming read budgets or strict duplicate-key parsing. The response model selects expected public fields for ordinary return values.

### Actual successful trace

```json
["before","lease-open","route","lease-close","after"]
```

The lease closes before this middleware's after marker on the pinned function-scoped path. Do not memorize that as the order for every dependency scope or framework version. The explicit scope tests below make the difference visible.

The factory/lifespan opens one catalog fixture per application lifespan, records startup, and closes it at shutdown. In a real deployment, each worker process has its own application lifespan; a resource created there is not a cross-worker singleton. See [lifespan events](https://fastapi.tiangolo.com/advanced/events/).

---

## 11.6 Validation, coercion and response models

M10 established that annotations alone do not validate values. FastAPI's declared request model causes the framework to invoke Pydantic validation; the Flask adapter calls Pydantic directly. It is that execution path, not the annotation by itself, which establishes the input model.

### Parsing policy must be explicit

Pydantic's default parsing can coerce some values, such as a numeric string into an integer. Strict mode changes those rules. Our QuoteIn requires a Python integer, rejects bool/float/string values and forbids unknown fields. The verifier checks accepted endpoints and rejected boundaries. See [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/).

| Body quantity | Strict QuoteIn result in this stack |
| --- | --- |
| 1 or 100 | Accepted |
| true | Rejected |
| 2.0 | Rejected |
| "2" | Rejected |
| 0 or 101 | Rejected |
| null or omitted | Rejected |

These are observed policies for this schema. They are not a promise that every int annotation in every model has identical coercion behavior.

Strictness also depends on the input representation/type. A strict datetime field can accept an ISO timestamp through JSON validation even when the equivalent Python-object string is rejected, because JSON has no native datetime type. The validation verifier tests that distinction. Choose the documented rule appropriate to the input path instead of saying “strict means no parsing ever.”

Pydantic v2 uses model_validate, model_validate_json, model_dump and model_dump_json. model_construct intentionally bypasses validation and is inappropriate for untrusted input. A Pydantic model is not a database model merely because both use the word model. Reference: [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/).

### Schema validation is only one boundary

A valid product ID is not proof that the principal owns it. A valid tenant_id field is not permission to select that tenant. A positive quantity is not proof of available inventory. The domain/data layer owns those rules.

The two adapters use normal JSON parsing. Their model validation does **not** detect duplicate JSON keys already collapsed by a parser. M10's strict raw-body parser showed a different explicit policy. If ambiguous keys matter, implement that policy before ordinary model construction and test the actual framework body path.

The FastAPI example does not implement a general streamed request-body cap. Its field limits do not prevent allocating a large body before validation. Add and test ingress/server/application read budgets before treating it as an upload API.

### Separate input and output schemas

Input answers “what may the client request?” Output answers “what may the application disclose?” The shared service returns internal cost and tenant fields, but the tested responses exclude them.

For ordinary return values, FastAPI's response_model validates and filters output; a response-model mismatch is a server error, not a 422 client-input error. The verifier observes a 500 for deliberately invalid output. Reference: [response models](https://fastapi.tiangolo.com/tutorial/response-model/).

Returning a Response/JSONResponse directly gives control of the outgoing response and bypasses this automatic response-model processing. The runtime verifier deliberately returns an extra private fixture field through a direct JSONResponse and observes it. Response schemas are therefore not a universal disclosure firewall for every code path.

The Flask adapter uses explicit output-model validation and JSON-mode dumping. Either approach still needs review of the fields selected and the caller's permissions.

---

## 11.7 Middleware, dependency graphs and cleanup scope

Middleware wraps requests/responses for cross-cutting behavior such as correlation IDs or timing. A dependency describes something needed by a route or another dependency, such as a principal, validated query model or resource. A domain service should remain callable without an HTTP request object where practical. Reference: [FastAPI middleware](https://fastapi.tiangolo.com/tutorial/middleware/).

| Mechanism | Good use | Incomplete substitution |
| --- | --- | --- |
| Middleware | Request metadata, outer instrumentation | Does not replace resource-specific authorization |
| Dependency | Resolve principal/resource/configured parameter | Does not persist work across restart |
| Router/Blueprint | Organize routes and common declarations | Does not isolate a process/tenant |
| Service | Business action and invariant | Does not automatically parse HTTP |
| Repository/transaction | Shared data access and atomicity | Does not determine HTTP response contracts alone |

### Dependency caching is request-local

When the same dependency is requested multiple times within one resolution graph, FastAPI normally reuses its result for that request. This avoids duplicate principal lookup or resource construction. It is not a cross-request cache, Redis replacement or global singleton.

The runtime verifier requests one dependency twice and observes one call and identical results; a second request causes another call. With use_cache=False on one declaration, the tested path obtains a separate invocation. Overrides used by tests must be restored so a fake authenticated user does not leak into later tests. See [dependency overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/).

### Yield introduces a lifecycle, not a transaction by itself

A yield dependency can open a resource, provide it and close it in finally. FastAPI manages the surrounding context; do not apply contextmanager yourself and then expect Depends to receive the yielded value automatically.

Cleanup timing has changed across FastAPI releases. This chapter explicitly verifies function and request scopes on 0.142.2. See [dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/).

The following excerpt comes directly from verify_runtime.py; it uses the verifier's existing imports/check collector and is not a standalone replacement application.

```python
scope_app = FastAPI()
events = []
async def resource():
    events.append('enter')
    try:
        yield 'resource'
    finally:
        events.append('exit')
def background(): events.append('background')
@scope_app.get('/function')
async def function_scope(tasks: BackgroundTasks,
                         value: Annotated[str, Depends(resource, scope='function')]):
    events.append('route')
    tasks.add_task(background)
    return {'ok': True}
@scope_app.get('/request')
async def request_scope(tasks: BackgroundTasks,
                        value: Annotated[str, Depends(resource, scope='request')]):
    events.append('route')
    tasks.add_task(background)
    return {'ok': True}
async def record_send(scope, receive, send):
    async def wrapped(message):
        if message['type'] == 'http.response.body' and not message.get('more_body', False):
            events.append('body-send')
        await send(message)
    await scope_app(scope, receive, wrapped)
with TestClient(record_send) as client:
    def function_check():
        events.clear()
        equal(client.get('/function').status_code, 200)
        equal(events, ['enter','route','exit','body-send','background'])
        observed['function_scope'] = list(events)
    checks.check('function-scoped yield resource closes before response body send', function_check)
    def request_check():
        events.clear()
        equal(client.get('/request').status_code, 200)
        equal(events, ['enter','route','body-send','background','exit'])
        observed['request_scope'] = list(events)
    checks.check('request-scoped cleanup follows body and background on pinned stack', request_check)

```

Observed ordering on the pinned stack:

```json
{
  "function_scope": [
    "enter",
    "route",
    "exit",
    "body-send",
    "background"
  ],
  "request_scope": [
    "enter",
    "route",
    "body-send",
    "background",
    "exit"
  ]
}
```

body-send records invocation of the ASGI send boundary for the final body message. It is not proof that the physical client received/processed the body, and the in-process client waits for background processing to finish before returning.

A function-scoped session cannot be used later by a streaming generator that needs it after response creation. A request-scoped resource may last through response sending, increasing retention during slow streaming. Pick the scope for actual use, then verify streaming/error behavior with the installed version. This chapter does not implement or test a streamed database response.

Background work should acquire its own resources from explicit IDs/data rather than capture a request-owned session whose scope may already have ended. Even if one pinned ordering happens to keep it alive, that is a fragile ownership design.

### Application lifespan is different again

Use lifespan for worker-owned long-lived resources such as a compatible HTTP client or pool, with explicit startup/failure/shutdown behavior. Use request scope for per-request transactions/leases. Use shared durable storage for cross-worker state. FastAPI's test client needs context-manager use to exercise the lifespan, as the verifier does.

---

## 11.8 def versus async def: trace the actual executor

The important question is not which spelling sounds faster. Ask where the function executes and whether the work blocks that executor.

| Code path | Observed/documented execution model |
| --- | --- |
| FastAPI async endpoint | Runs on the event-loop thread; suspends at compatible awaits |
| FastAPI def endpoint | Framework dispatches it through the thread-pool mechanism |
| FastAPI def dependency | Framework dispatches it through the thread-pool mechanism |
| FastAPI async dependency | Runs in the async execution path |
| Ordinary def helper called inside async endpoint | Runs directly on the caller's thread unless explicitly offloaded |
| Flask async view under its ordinary WSGI bridge | Async loop/thread bridge within the active WSGI request |

References: [FastAPI concurrency guide](https://fastapi.tiangolo.com/async/), [Starlette thread pool](https://starlette.dev/threadpool/), [Flask async support](https://flask.palletsprojects.com/en/stable/async-await/).

The verifier records the loop thread during lifespan, compares route/dependency/helper thread identities and observes:

```json
{
  "route_on_loop": true,
  "sync_dependency_off_loop": true,
  "async_dependency_on_loop": true,
  "ordinary_helper_on_loop": true
}
```

It separately observes the synchronous route executing off the loop thread. These checks establish dispatch boundaries; they are not throughput benchmarks or proof that thread offload makes CPU work scale across cores.

### Blocking database or HTTP client inside async code

Calling a blocking client directly inside async def occupies the loop thread until it returns. The framework does not inspect arbitrary helpers and automatically offload them. Options include a compatible async client, a def route/dependency for suitable blocking work, or explicit bounded thread offload. Check the client/session's concurrency safety and ownership before sharing it.

A finite thread pool can also saturate. Thread capacity, database connections, provider quotas and request concurrency must be considered together. Increasing one limit does not remove a downstream bottleneck and can increase resource pressure.

CPU-heavy parsing has a different profile. M10's GIL/build/process discussion still applies. Async can overlap waits; it does not supply multicore Python computation by itself. Native libraries/process workers or durable jobs may be appropriate after profiling.

### What Flask async support changes

Flask's async extra permits coroutine views. Under the ordinary WSGI model, a request still occupies its serving capacity while the bridged coroutine runs. The view can overlap compatible I/O internally; that is not the same as an async-native server admitting unlimited additional requests.

The runtime check records access to the request context from the bridged view and a different thread from the WSGI caller. It starts a pending child task, waits until it is running, returns the response and observes the pending task's cancellation cleanup:

```json
{
  "flask_async": {
    "context_available": true,
    "different_thread": true
  },
  "pending_task_cleanup": [
    "cancelled"
  ]
}
```

That behavior is the reason asyncio.create_task inside a conventional Flask async view is not a durable background-job solution. An ASGI adapter/alternative deployment can change loop lifetime; it still does not make in-memory work restart-safe. Explain the actual deployment instead of applying one blanket claim to every Flask arrangement.

---

## 11.9 BackgroundTasks versus durable jobs

FastAPI's BackgroundTasks schedules work associated with a response, executed within the application process after that response's body is sent through the application transport. It is useful for small best-effort work whose lifecycle fits that process. It is not a persisted queue, retry scheduler or guarantee of eventual completion. References: [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/), [Starlette background tasks](https://starlette.dev/background/).

| Work | Suitable direction |
| --- | --- |
| Small non-critical local follow-up | In-process background task, with failure handling |
| Long document extraction or embedding job | Durable job ownership and worker execution |
| Payment/credit transition | Transactional state/idempotency, with recovery |
| Guaranteed notification after a committed change | Outbox/queue pattern plus delivery policy |
| CPU work needed before responding | Bounded computation/offload with a deadline, or change API contract |

### What if a background task fails?

The runtime verifier instruments ASGI send, then deliberately fails a background task. It observes status 200 and the accepted body already sent to that transport before the error reaches the test caller. The later exception cannot turn an already-sent successful response into a reliable client-visible failure.

Recorded observation:

```json
{"background_failure_status_already_sent":200}
```

This is in-process send instrumentation, not a real remote side effect. It demonstrates the boundary that matters: response success and follow-up completion are separate facts.

For important work, persist ownership before acknowledging acceptance, then execute with idempotency, retries, deadlines and observable failure state. Do not pass request proxies or request-owned sessions to a later worker. Pass identifiers and acquire worker-owned resources. M9's outbox and uncertain-outcome reasoning applies; M15 will develop jobs further.

---

## 11.10 HTTP contracts and failure paths

Framework defaults are starting points. Define a consistent application contract and deliberately preserve protocol requirements such as Allow and WWW-Authenticate.

| Case in these adapters | Flask observation | FastAPI observation |
| --- | --- | --- |
| Missing/unknown fixture credential | 401 plus Bearer challenge | 401 plus Bearer challenge |
| Valid body with inaccessible product | 404 | 404 |
| Invalid strict body values/extra fields | 422 via our handler | 422 via request-validation handler |
| Malformed JSON | 400 | 422 |
| Explicit text/plain quote body | 415 | 415 |
| Invalid query limit | 400 via our parsing policy | 422 via declared query validation |
| Wrong HTTP method | 405 retaining Allow | 405 retaining Allow |
| Oversized Flask JSON body | 413 with configured limit | General body cap not implemented here |
| Invalid response model in runtime probe | Not a Flask route in that probe | 500 |

These are actual tested policies, including choices made in our adapters. “Flask returns 400, FastAPI returns 422” is not a universal rule for every possible validation implementation.

The Flask products list returns an items envelope; the FastAPI example returns a list through list[ProductOut]. That difference is an authoring choice, not a framework restriction. Align it if you expose both implementations behind one public contract.

### Keep rejected input out of error responses and logs

Validation errors may include rejected input values. The FastAPI handler selects only locations/types; the test submits a secret fixture string and verifies that it is absent from the response. Flask uses a generic invalid_body error. A real logging policy also needs redaction and correlation without credentials/body dumps.

Do not catch an internal output/DB failure and relabel it as the client's bad request. Distinguish client contract errors, access failures, not-found results, dependency failures and application bugs.

### Authentication dependency ordering is not an ingress firewall

A dependency can reject credentials before the endpoint executes, but the framework may parse a declared body first. Use server/proxy/application budgets for body size and time. Uniform error-disclosure policy needs an explicitly tested implementation; this chapter only claims the paths actually exercised.

---

## 11.11 OpenAPI and interactive docs

FastAPI generates an OpenAPI document describing declared operations, schemas, parameter locations, responses and security declarations. Swagger UI is a client-facing documentation interface using that schema; it is not another backend execution engine.

The HTTP test fetches /openapi.json and confirms the quote operation, integer quantity bound, forbidden-extra schema policy and HTTPBearer security scheme. It also confirms /docs responds. This is schema/HTML verification; the external JavaScript assets and an interactive browser session were not exercised.

Generated docs are useful for discovery, contracts and client generation. They do not prove permission correctness, idempotency, transaction isolation or actual deployment behavior. A bearer scheme in OpenAPI describes credential transport, not whether your implementation verifies a JWT correctly.

Flask can also expose OpenAPI through additional tooling; its absence from this small adapter is a deliberate scope choice. Neither framework requires hand-maintaining a different business domain just to document it.

---

## 11.12 Architectural understanding: build an ingestion API

This is a proposed build path, not an implemented production system or a claim about a resume project's exact architecture. It extends M10's document-processing design into framework responsibilities.

### Requirement

A tenant-authenticated user submits a document. The API validates the request, records durable work and returns a job ID. Workers extract/process it; the user polls authorized job status. The system must tolerate retries and worker restarts.

```text
POST /documents
  -> ingress limits / media checks
  -> authenticate principal
  -> authorize tenant/workspace
  -> validate metadata and storage reference
  -> transaction: document/job state + outbox intent
  -> 202 with server-owned job ID

outbox delivery -> durable queue -> worker
  -> verify document/job ownership
  -> acquire worker-owned resources
  -> extract / batch / bounded external API work
  -> idempotent result writes and progress
  -> completion/failure status

GET /jobs/{id}
  -> authenticate -> tenant/owner-scoped lookup -> public status schema
```

An HTTP 202 represents accepted work under the documented contract, not completed extraction. A row saying queued is insufficient if the queue message can be lost independently. Decide how state and dispatch intent stay consistent, for example the transactional outbox developed in M9.

### Place the framework mechanisms

| Responsibility | Flask approach | FastAPI approach |
| --- | --- | --- |
| Organize endpoints | Blueprint | APIRouter |
| Resolve principal | Before hook/decorator with explicit policy | Principal dependency/security declaration |
| Validate request | Explicit schema/parser invocation | Declared model/dependencies plus explicit additional policy |
| Request resource | Context-local handle and teardown | Yield dependency with chosen scope |
| Application resource | Explicit factory/extension lifecycle | Lifespan-managed worker resource |
| Public response | Explicit mapper/schema serialization | Response model or deliberate explicit response |
| Durable processing | Shared job/storage/queue design | Same shared job/storage/queue design |

The worker/domain code should not import Flask request or depend on a live FastAPI Request to find its tenant. Make identity/job IDs explicit and recheck durable ownership at the worker boundary.

### Build one correct slice at a time

1. Implement a pure submission/status service with a documented state model.
2. Add a thin framework adapter with real negative auth/validation tests.
3. Add actual database constraints/transactions and tenant-scoped queries.
4. Establish recoverable dispatch and idempotent worker execution.
5. Add bounded parsing/provider work and cancellation/deadline policy.
6. Verify duplicate submission, crash after commit, redelivery and cross-tenant status access.
7. Measure queue age, error rates, resource saturation and request latency separately.

The quote adapters implement step two's boundary pattern with an in-memory read domain; they do not implement this ingestion pipeline or its durability. The later database/job modules provide its prerequisites.

### Failure prompt: API returns 202, process stops immediately

If the work exists only as BackgroundTasks or a created coroutine, it may disappear. If durable job state and dispatch intent committed together, another dispatcher/worker can recover it. The answer depends on persisted state and ownership, not on whether the route was declared async.

---

## 11.13 Choosing a framework and defending the resume

Flask is useful when a team wants a small explicit foundation, has an established Flask ecosystem, or mainly uses synchronous libraries and conventional request handling. FastAPI is useful when typed API declarations, generated schemas, dependency composition and ASGI-native I/O fit the application. Both can build substantial systems; neither eliminates data modelling, security or operational work.

| Decision factor | Questions to ask |
| --- | --- |
| Existing code/team | Which conventions and extensions already work well? |
| I/O libraries | Async-compatible clients, blocking clients, session safety? |
| API contracts | How will schemas, validation and docs be maintained? |
| Long-lived connections | Does the server/application support the required protocol? |
| CPU work | Where will computation run, with what budgets? |
| Durability | Which work must survive request/process lifetime? |
| Operation | Worker count, connection pools, graceful shutdown, logs and metrics? |

No framework wins every workload. This module ran correctness and execution-boundary checks, not comparative benchmarks. Do not infer a throughput ranking from the names or these tests.

For a resume explanation, describe the framework actually used, one request flow, the service/data boundaries, sync/async choices and one verified failure case. If you propose changing Flask to FastAPI, say what requirement motivates that change. Do not invent process pools, ASGI deployment, Pydantic schemas or durable queues that the project's code has not established.

A useful two-minute structure is: requirement -> request trace -> authority/invariant -> execution/resource choice -> failure/recovery -> evidence. That structure works with either framework and prepares you for Django's additional conventions in M12.

---

## 11.14 Must remember

1. Flask/FastAPI, WSGI/ASGI and an application server answer different questions.
2. A server's worker policy determines serving capacity; the interface name alone does not give a thread count.
3. Flask request/current_app/g resolve through contexts; ordinary request state is not durable storage.
4. Factories, Blueprints and APIRouters organize setup and routes; they do not create process isolation.
5. Pydantic validation executes only on the configured path; annotations or model_construct are not a substitute.
6. Strict body fields and parsed query parameters can intentionally use different coercion policies.
7. Valid schema values still need trusted identity, authorization and domain checks.
8. FastAPI dispatches registered def routes/dependencies; a directly called helper stays on its caller's thread.
9. Yield scope and lifespan are different resource lifetimes; background workers need their own resources.
10. Ordinary return values and direct Response objects have different serialization paths.
11. A successful response can precede background failure; important work needs durable ownership.
12. Generated OpenAPI and passing local checks do not establish production security, performance or recovery.

---

## 11.15 Common wrong answers

| Wrong answer | Better explanation |
| --- | --- |
| Flask is the Python runtime | Python is the language; CPython executes it; Flask is a framework |
| Uvicorn and FastAPI are the same thing | Uvicorn serves the ASGI application; FastAPI supplies framework behavior |
| WSGI means one request for the whole deployment | Worker/thread/process policy belongs to the server/deployment |
| ASGI automatically makes every operation non-blocking | Blocking calls still occupy their executing thread |
| Flask async views free the ordinary WSGI worker immediately | The request still occupies serving capacity while its bridged view runs |
| g is a permanent global dictionary | It belongs to the active application context |
| A Blueprint is a separate server | It groups registrations in a Flask application |
| A factory makes state shared between workers | Each constructed app/worker has its own ordinary memory |
| A Pydantic model is an ORM table | Validation/serialization and persistence modelling are separate |
| int annotations always reject quoted numbers | Coercion depends on the validation configuration/input path |
| A valid tenant_id lets a client choose its tenant | Authorization must bind tenant context to a trusted principal |
| Every def function called by FastAPI is offloaded | Framework-dispatched routes/dependencies differ from ordinary direct calls |
| More threads always solve latency | Thread capacity, GIL context, pools and downstream limits still matter |
| Depends caches data forever | Normal dependency caching is scoped to a request resolution |
| A yield dependency always closes at the same universal moment | Scope/version/response behavior matter and must be verified |
| A response model filters a direct JSONResponse too | Direct responses bypass that automatic processing path |
| BackgroundTasks guarantees eventual work | It is in-process response-associated execution |
| A background failure can change the already-sent status | Response sending and task completion are separate boundaries |
| OpenAPI bearer means verified JWT authentication | The schema describes the declared mechanism; implementation must verify credentials |
| Returning 202 means the job is finished | It expresses acceptance under the documented contract |

---

## 11.16 Interview Q&A

These prompts select useful fundamentals and follow-ups for Python backend work. They are not measured company-question frequency rankings.

**Q1. What is Flask? What is FastAPI?**

They are Python web frameworks that map requests to application behavior and responses. Flask uses the WSGI application model here; FastAPI uses ASGI and integrates typed declarations, dependencies and Pydantic schemas. Neither is the Python interpreter or database.

**Follow-up:** Which process actually accepts the network connection?

**Q2. Why do we need a server in addition to a framework?**

The server manages connections/protocol handling and invokes the application's interface. The framework handles higher-level routing/request adaptation. Separating the interface lets server and framework choices vary within compatible contracts.

**Follow-up:** Where would a reverse proxy sit?

**Q3. Explain WSGI in one minute.**

A WSGI server invokes a callable with environ and start_response. The application supplies status/headers and a byte iterable; the server sends the body and manages iteration/closure. Serving concurrency depends on the server's worker strategy.

**Follow-up:** Why does WSGI not imply one request for the entire machine?

**Q4. Explain ASGI and how it differs.**

ASGI supplies a scope and asynchronous receive/send event interfaces. It supports protocols such as HTTP, WebSockets and lifespan. It enables cooperative async execution while leaving blocking/CPU work and resource budgets as application concerns.

**Follow-up:** What does more_body mean in a request event?

**Q5. What happens from a Flask request arriving to a response leaving?**

The server calls Flask, contexts are established, routing/hooks select and prepare work, the view returns a value, Flask builds a response, after hooks modify it, and teardown releases context-owned resources. Error/streaming paths need additional attention.

**Follow-up:** What if before_request returns a response early?

**Q6. Why can request and g be imported without being one global request?**

They are context-local accessors. They resolve the active request/application context rather than storing all users' data in one ordinary shared object. Outside the relevant context, access can fail.

**Follow-up:** Why should a later job receive explicit IDs rather than a request proxy?

**Q7. Application context versus request context?**

The application context exposes the active app and g; the request context exposes request/session information and ordinarily accompanies an application context. Their lifetimes matter, especially when manually extended or used outside HTTP handling.

**Follow-up:** Is g a cross-request cache in the ordinary flow?

**Q8. Blueprint versus application factory?**

A Blueprint collects routes/hooks for registration. A factory constructs/configures the app and registers components. They solve organization/setup problems; neither is a new server or a shared-state synchronization mechanism.

**Follow-up:** Why should route registration finish before serving requests?

**Q9. How would you validate JSON in Flask?**

Check transport/media/size policy, parse the body, then invoke a selected validator/schema and map errors deliberately. Flask's JSON parser does not by itself enforce quantity bounds, trusted pricing or tenant authorization.

**Follow-up:** Which part of this adapter excludes boolean quantities?

**Q10. How does FastAPI decide path, query and body inputs?**

It combines the route path and signature/declarations. Matching path names are path parameters; declared query inputs come from query text; a Pydantic body model supplies structured body validation. Dependencies inject resolved values rather than client-selected principal objects.

**Follow-up:** Why might limit=1 parse while JSON quantity="1" is rejected here?

**Q11. What does Pydantic add beyond a type hint?**

When invoked, it parses/validates data according to model configuration and supplies serialization/schema behavior. A type hint alone does not execute that process. Use explicit policies for strictness, extra fields and input representation.

**Follow-up:** What does model_construct bypass?

**Q12. Is strict validation identical for JSON and Python objects?**

Not for every type. The verifier demonstrates a datetime string accepted by strict JSON validation but rejected by strict Python-object validation. JSON's available value types and documented parsing rules matter.

**Follow-up:** Why is a blanket “strict means no parsing” explanation incomplete?

**Q13. Does a schema prevent cross-tenant access?**

No. A schema can validate an ID's shape; the application must bind identity to a trusted principal and scope every relevant lookup/write. This catalog lookup uses the authenticated tenant instead of a client tenant field.

**Follow-up:** What would the database query's tenant predicate look like?

**Q14. What is dependency injection in FastAPI?**

Routes/dependencies declare required values, and FastAPI resolves the dependency graph and invokes the functions. This centralizes principal/resource/configuration acquisition while keeping the service's business rule separate.

**Follow-up:** Why is Depends not simply a global singleton constructor?

**Q15. How does dependency caching work?**

Normal resolution can reuse the same dependency result within a request. A later request resolves again. use_cache=False changes the selected invocation's reuse behavior; test the actual dependency graph rather than assuming arbitrary global caching.

**Follow-up:** Why restore dependency overrides after a test?

**Q16. How do yield dependencies manage resources?**

They acquire before yielding and clean up in a finally path managed by the framework. Choose a scope appropriate to when the resource is used. Cleanup does not automatically mean transaction commit or rollback.

**Follow-up:** What if a streaming generator still needs a function-scoped session?

**Q17. What belongs in lifespan instead of a request dependency?**

Worker-owned long-lived resources such as compatible clients/pools can be created/closed at startup/shutdown. Request-owned sessions/leases have a smaller scope. Each worker's ordinary memory remains separate.

**Follow-up:** What does TestClient need to exercise lifespan?

**Q18. Middleware versus dependency?**

Middleware wraps the HTTP exchange for cross-cutting behavior. A dependency resolves a route requirement with declared graph/lifecycle semantics. Both can contribute to security, but neither removes the need for object-level authorization in data operations.

**Follow-up:** Why does a request ID not establish authentication?

**Q19. When should a FastAPI route be def or async def?**

Choose for the actual client/workload. Async fits compatible awaited I/O; registered def handlers run through a thread-pool path for blocking execution. CPU work, pool capacity, session safety and durable work require separate decisions.

**Follow-up:** Can a blocking library call inside async def still stall the loop?

**Q20. Are ordinary def helpers automatically offloaded?**

No. A direct helper call executes on the caller's thread. Framework dispatch of registered sync endpoints/dependencies is a different mechanism. The runtime verifier checks both cases using thread identity.

**Follow-up:** Where would you explicitly offload a suitable blocking operation?

**Q21. What does Flask's async extra enable?**

It allows coroutine views/hooks through an async bridge in the ordinary WSGI model. A view can overlap suitable I/O internally, while the active request still occupies serving capacity. It does not make the deployment async-native by syntax alone.

**Follow-up:** What happened to the pending child task when our view returned?

**Q22. How do response models help?**

For ordinary FastAPI return values, they validate/serialize/filter the public result. They help separate output from internal data. Deliberately invalid output is a server error, and direct Response objects bypass this automatic path.

**Follow-up:** Why did the direct JSONResponse probe expose the private fixture field?

**Q23. What does OpenAPI provide, and what does it not prove?**

It describes declared operations, schemas, inputs/responses and security declarations for tools and humans. It does not verify actual permissions, transaction behavior, throughput or runtime deployment correctness.

**Follow-up:** Does an HTTPBearer schema prove JWT verification?

**Q24. How would you design error handling?**

Define client/domain/internal error categories and public contracts, preserve protocol headers/status, and avoid leaking raw input/internal details. Do not turn output-validation or DB bugs into successful responses or arbitrary client errors.

**Follow-up:** Why retain the original 405 response's Allow header?

**Q25. Why do malformed JSON and invalid models sometimes have different statuses?**

They fail at different parsing/validation boundaries and frameworks/adapters choose different mappings. This example records 400 versus 422 for malformed JSON, while both map strict model failures to 422.

**Follow-up:** Would you standardize these adapters behind one public API?

**Q26. What is BackgroundTasks useful for?**

Small process-local follow-up work associated with a response, with explicit failure handling. It provides neither durable ownership nor automatic guaranteed retries after a restart.

**Follow-up:** What if the process stops immediately after the response?

**Q27. Can a failed background task change a response already sent?**

It cannot reliably change the already-sent status/body. Our instrumented test observes a 200/body before the failure. Client-visible acceptance and follow-up completion are separate facts.

**Follow-up:** Where would you record a durable job's failure state?

**Q28. How would you build a reliable ingestion endpoint?**

Authenticate and authorize, validate bounded input, persist document/job ownership and dispatch intent consistently, then return a job ID. Workers acquire their own resources and write idempotent tenant-scoped results with recovery.

**Follow-up:** What if results commit before a queue acknowledgement is sent?

**Q29. What tests would you add beyond a happy-path request?**

Invalid values/types/media, missing credentials, cross-tenant access, output disclosure, method/error headers, cleanup on failures, lifespan and execution-boundary tests. Add actual DB/retry/restart tests when those features exist.

**Follow-up:** Which checks here use real sockets, and which are in-process?

**Q30. How would you choose Flask versus FastAPI for a project?**

Start with team/code ecosystem, library execution model, API contracts, protocol needs and operational constraints. Explain one request and failure path. Neither framework name is evidence of a universal speedup or durable architecture.

**Follow-up:** Which requirement would justify changing your current framework?

---

## 11.17 Practice tasks and answer checkpoints

### 1. Draw both request paths

Trace POST /api/quotes through the WSGI/Flask path and the ASGI/FastAPI path. Identify the server, framework, validator, service and output boundary.

**Checkpoint:** Server interface differs; trusted pricing and tenant ownership remain in the shared domain. Use the recorded lifecycle markers rather than inventing a universal hook order.

### 2. Standardize the public contract

Make both product-list responses use the same envelope and define one policy for invalid query/body errors.

**Checkpoint:** These are application choices. Update declared output schemas, error handlers and real HTTP tests together; preserve Allow and authentication challenges.

### 3. Protect another catalog operation

Add a tenant-scoped product-detail field or operation. Try selecting another tenant through the body, query and path.

**Checkpoint:** Principal-derived tenant context scopes data access. Merely forbidding one body field is not authorization on every route.

### 4. Explain strictness by experiment

Add two models with different coercion policies and test quoted numbers, booleans, floats and JSON/Python datetime inputs.

**Checkpoint:** Specify the exact model configuration and validation entry point. Do not assume one keyword establishes identical behavior for every type/transport.

### 5. Repair a blocking async route

An async endpoint calls a blocking client directly. Choose a compatible async client, registered sync route/dependency or bounded explicit offload and explain the decision.

**Checkpoint:** Include client/session safety, timeout behavior, thread-pool/downstream limits and CPU versus I/O work. Thread identity alone is not a performance benchmark.

### 6. Change the resource scope

Imagine returning a streamed response that accesses the yielded resource after the endpoint returns. Compare function/request scope and test the actual send/error/disconnect path.

**Checkpoint:** A closed resource cannot support later streaming. A longer-lived resource can tie up capacity for slow consumers. This is a new exercise; streaming is not already verified by this chapter.

### 7. Demonstrate the disclosure bypass

Use the deliberate direct-response probe to explain why a public response model is insufficient if another path returns arbitrary JSONResponse data.

**Checkpoint:** Every outgoing path needs an explicit field/permission policy. Restore safe serialization rather than adding a misleading annotation.

### 8. Replace best-effort work with a durable contract

An endpoint returns 202 and starts document extraction in BackgroundTasks. Specify the minimum persisted job/outbox/result state needed for restart recovery.

**Checkpoint:** Acceptance follows durable ownership. Workers have retry/idempotency and their own resources; in-memory tasks and request contexts are not the recovery mechanism.

### 9. Add a cleanup failure test

Inject a domain/dependency failure after a request resource opens and assert its close path executes once. Decide how an actual database transaction should commit/rollback independently.

**Checkpoint:** Resource release and transaction success are separate invariants. Avoid double-close and avoid inferring commit from a teardown exception argument.

### 10. Defend the framework choice aloud

Explain the framework used by a real project in two minutes, then describe one alternative and the requirement that would motivate it.

**Checkpoint:** Ground implementation claims in actual project code/evidence. Keep hypothetical architecture improvements clearly labelled and do not invent benchmark results.

---

## 11.18 Exit checklist

- [ ] I can distinguish a framework, application server, reverse proxy and interface standard.
- [ ] I can explain WSGI's callable/byte iterable and ASGI's scope/events.
- [ ] I can trace Flask hooks, contexts, errors and resource teardown.
- [ ] I can explain Blueprint/factory versus APIRouter/lifespan responsibilities.
- [ ] I can map a FastAPI signature to path/query/body/dependency inputs.
- [ ] I can configure strict input validation and distinguish it from authorization.
- [ ] I can explain dependency caching, overrides and explicit yield scope.
- [ ] I can distinguish request resources from worker/application resources.
- [ ] I can trace def/async def execution and ordinary helper calls.
- [ ] I can explain Flask's ordinary WSGI async bridge and child-task lifetime.
- [ ] I can separate response-model serialization from direct responses.
- [ ] I can preserve HTTP error headers and avoid rejected-input disclosure.
- [ ] I can explain what OpenAPI describes without overstating its guarantees.
- [ ] I can distinguish response-associated BackgroundTasks from durable work.
- [ ] I can draw the ingestion API/job/status design and its restart path.
- [ ] I can run the 80 checks and state the limits of each evidence group.

---

## 11.19 Sources and reproducible evidence

Research checked on **14 October 2026**. Executed versions are recorded at the start and in verification-results.json. Current documentation and the teaching package snapshot are different contexts.

| Topic | Primary documentation |
| --- | --- |
| Server/application contract | [WSGI PEP 3333](https://peps.python.org/pep-3333/), [ASGI specification](https://asgi.readthedocs.io/en/stable/specs/main.html) |
| Flask flow/setup | [Lifecycle](https://flask.palletsprojects.com/en/stable/lifecycle/), [request context](https://flask.palletsprojects.com/en/stable/reqcontext/), [factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/), [blueprints](https://flask.palletsprojects.com/en/stable/blueprints/) |
| Flask execution/errors | [Async support](https://flask.palletsprojects.com/en/stable/async-await/), [errors](https://flask.palletsprojects.com/en/stable/errorhandling/), [deployment](https://flask.palletsprojects.com/en/stable/deploying/), [changes](https://flask.palletsprojects.com/en/stable/changes/) |
| FastAPI contracts | [Bodies](https://fastapi.tiangolo.com/tutorial/body/), [path](https://fastapi.tiangolo.com/tutorial/path-params/), [query](https://fastapi.tiangolo.com/tutorial/query-params/), [response models](https://fastapi.tiangolo.com/tutorial/response-model/) |
| Dependency/lifecycle | [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/), [yield scope](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), [lifespan](https://fastapi.tiangolo.com/advanced/events/), [middleware](https://fastapi.tiangolo.com/tutorial/middleware/) |
| Execution/background | [FastAPI async](https://fastapi.tiangolo.com/async/), [thread pool](https://starlette.dev/threadpool/), [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/), [Starlette background tasks](https://starlette.dev/background/) |
| Validation/testing | [Pydantic strictness](https://docs.pydantic.dev/latest/concepts/strict_mode/), [models](https://docs.pydantic.dev/latest/concepts/models/), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [dependency overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/), [release notes](https://fastapi.tiangolo.com/release-notes/) |

### Verification map

All files are under examples/resume-skills/module-11-python-frameworks/.

| Group | Checks | Actual boundary |
| --- | --- | --- |
| protocols | 2 | Standard-library-validated WSGI call; ASGI receive/send event fixture |
| validation | 10 | Real Pydantic coercion/strictness/bounds/model operations |
| http | 52 | Real loopback HTTP against Flask/Werkzeug and FastAPI/Uvicorn; 25 Flask and 27 FastAPI checks |
| runtime | 16 | Real framework in-process clients, thread identity, ASGI send instrumentation, cleanup/background failure |
| Total | **80** | Named checks; some include several related assertions/fixtures |

Implementation: protocols.py, domain.py, flask_app.py and fastapi_app.py. Verification: verify.py, verify_protocols.py, verify_validation.py, verify_http.py, verify_runtime.py, servers.py and checks.py. Package snapshots: requirements.txt and requirements.lock.txt.

Machine-readable results and captured transcripts preserve what ran. The expected TestClient deprecation warning is saved separately. The HTTP harness closes its listeners; the runtime tests use no sockets. Dependency installation and pip check succeeded in the isolated environment.

No production deployment, throughput benchmark, free-threaded Python comparison, database, durable queue, real login/JWT validation, external API call or actual ingestion worker is claimed. The catalog/credentials/leases are local fixtures. The architecture is a build exercise; the quoted cleanup/send order is for the recorded stack.

---

## Next

Continue to [M12: Django and Django REST Framework](/docs/resume-skills/django-django-rest-framework). It will add project/app structure, URL-to-view flow, middleware, ORM/migrations, serializers, viewsets/routers, permissions and transaction boundaries.

Revisit [M10: Python Fundamentals](/docs/resume-skills/python-fundamentals) for the language/execution foundation, [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) for trusted ownership, and [M9: Webhooks and Payments](/docs/resume-skills/webhooks-payments-reliable-integrations) for durable effects/recovery. The [master roadmap](/docs/resume-skills) shows the remaining branches.
