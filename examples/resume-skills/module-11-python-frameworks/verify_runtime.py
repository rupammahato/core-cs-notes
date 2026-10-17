import asyncio
from contextlib import asynccontextmanager
from threading import get_ident
from typing import Annotated
from flask import Flask, g, request
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel
from checks import Checks, equal, require
from flask_app import create_app as flask_factory
from fastapi_app import create_app as fastapi_factory, principal
from domain import Principal

checks = Checks('runtime')
observed = {}

def outside_context():
    try:
        request.path
    except RuntimeError:
        return
    raise AssertionError('request proxy usable outside context')
checks.check('Flask request proxy requires a request context', outside_context)

def contexts():
    app = Flask('contexts')
    @app.get('/<value>')
    def view(value):
        old = getattr(g, 'value', None)
        g.value = value
        return {'old': old, 'current': g.value}
    client = app.test_client()
    equal(client.get('/first').json, {'old': None, 'current': 'first'})
    equal(client.get('/second').json, {'old': None, 'current': 'second'})
checks.check('Flask g is not persistent cross-request storage', contexts)

def factories():
    first, second = flask_factory(), flask_factory()
    first.extensions['catalog'].close()
    equal(second.extensions['catalog'].closed, False)
checks.check('Flask factory creates independent application state', factories)

def flask_async():
    app = Flask('flask-async')
    cleanup = []
    @app.before_request
    def before():
        g.wsgi_thread = get_ident()
    @app.get('/')
    async def view():
        started = asyncio.Event()
        async def pending():
            try:
                started.set()
                await asyncio.Event().wait()
            finally:
                cleanup.append('cancelled')
        asyncio.create_task(pending())
        await started.wait()
        return {'different_thread': get_ident() != g.wsgi_thread,
                'context_available': hasattr(g, 'wsgi_thread')}
    response = app.test_client().get('/')
    equal(response.status_code, 200)
    equal(response.json, {'different_thread': True, 'context_available': True})
    equal(cleanup, ['cancelled'])
    observed['flask_async'] = response.json
    observed['flask_pending_task'] = cleanup
checks.check('Flask async bridge preserves context and cancels unfinished spawned task', flask_async)

app = FastAPI()
loop_thread = {}
@asynccontextmanager
async def lifespan(application):
    loop_thread['id'] = get_ident()
    yield
app.router.lifespan_context = lifespan

def sync_dep(): return get_ident()
async def async_dep(): return get_ident()
def ordinary_helper(): return get_ident()

@app.get('/async')
async def async_route(worker: Annotated[int, Depends(sync_dep)],
                      loop: Annotated[int, Depends(async_dep)]):
    return {'route_on_loop': get_ident() == loop_thread['id'],
            'sync_dependency_off_loop': worker != loop_thread['id'],
            'async_dependency_on_loop': loop == loop_thread['id'],
            'ordinary_helper_on_loop': ordinary_helper() == loop_thread['id']}
@app.get('/sync')
def sync_route(): return {'route_off_loop': get_ident() != loop_thread['id']}

with TestClient(app) as client:
    async_result = client.get('/async').json()
    checks.check('FastAPI async route and async dependency run on loop thread',
                 lambda: require(async_result['route_on_loop'] and async_result['async_dependency_on_loop']))
    checks.check('FastAPI def dependency is dispatched off loop',
                 lambda: equal(async_result['sync_dependency_off_loop'], True))
    checks.check('ordinary def helper called directly stays on caller thread',
                 lambda: equal(async_result['ordinary_helper_on_loop'], True))
    checks.check('FastAPI def route is dispatched off loop',
                 lambda: equal(client.get('/sync').json(), {'route_off_loop': True}))
    observed['fastapi_dispatch'] = async_result

calls = []
cache_app = FastAPI()
def shared():
    calls.append('call')
    return object()
@cache_app.get('/cached')
async def cached(a: Annotated[object, Depends(shared)], b: Annotated[object, Depends(shared)]):
    return {'same': a is b}
@cache_app.get('/uncached')
async def uncached(a: Annotated[object, Depends(shared)],
                   b: Annotated[object, Depends(shared, use_cache=False)]):
    return {'same': a is b}
with TestClient(cache_app) as client:
    def cache_check():
        calls.clear()
        equal(client.get('/cached').json(), {'same': True})
        equal(len(calls), 1)
        client.get('/cached')
        equal(len(calls), 2)
    checks.check('dependency cache is reused within a request and reset for next request', cache_check)
    def uncached_check():
        calls.clear()
        equal(client.get('/uncached').json(), {'same': False})
        equal(len(calls), 2)
    checks.check('use_cache=False requests a separate dependency invocation', uncached_check)

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

class Public(BaseModel):
    value: int
response_app = FastAPI()
@response_app.get('/invalid', response_model=Public)
async def invalid(): return {'value': 'not-an-integer'}
@response_app.get('/direct', response_model=Public)
async def direct(): return JSONResponse({'value': 1, 'private': 'fixture'})
with TestClient(response_app, raise_server_exceptions=False) as client:
    checks.check('invalid response model is a server error, not a client validation error',
                 lambda: equal(client.get('/invalid').status_code, 500))
    checks.check('direct Response bypasses response-model field filtering',
                 lambda: equal(client.get('/direct').json(), {'value': 1, 'private': 'fixture'}))

background_app = FastAPI()
sent = []
def fail_background(): raise RuntimeError('fixture background failure')
@background_app.get('/')
async def accepted(tasks: BackgroundTasks):
    tasks.add_task(fail_background)
    return {'accepted': True}
async def record_background_send(scope, receive, send):
    async def wrapped(message):
        if message['type'] in ('http.response.start','http.response.body'):
            sent.append(dict(message))
        await send(message)
    await background_app(scope, receive, wrapped)
def failed_background():
    try:
        with TestClient(record_background_send) as client:
            client.get('/')
    except RuntimeError:
        pass
    else:
        raise AssertionError('background failure not observed')
    equal(sent[0]['status'], 200)
    require(any(m['type']=='http.response.body' and b'accepted' in m.get('body',b'') for m in sent))
    observed['background_failure_status_already_sent'] = sent[0]['status']
checks.check('background failure occurs after a successful response was sent to transport', failed_background)

def override():
    app = fastapi_factory()
    with TestClient(app) as client:
        app.dependency_overrides[principal] = lambda: Principal('test-user', 'alpha')
        try:
            equal(client.get('/api/products/basic').status_code, 200)
        finally:
            app.dependency_overrides.clear()
        equal(client.get('/api/products/basic').status_code, 401)
    equal(app.state.catalog.closed, True)
checks.check('test dependency override can be restored and lifespan resource closes', override)
checks.save(observations=observed, transport='In-process framework clients / ASGI send instrumentation; no sockets')
