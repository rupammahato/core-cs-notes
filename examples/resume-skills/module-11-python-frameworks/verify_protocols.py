import asyncio
from io import BytesIO, StringIO
import json
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator
from checks import Checks, equal
from protocols import wsgi_app, asgi_app

checks = Checks('protocols')
observed = {}
def wsgi():
    environ = {}
    setup_testing_defaults(environ)
    environ.update(REQUEST_METHOD='GET', PATH_INFO='/probe', QUERY_STRING='',
                   **{'wsgi.input': BytesIO(), 'wsgi.errors': StringIO()})
    started = []
    def start_response(status, headers, exc_info=None):
        started.append((status, headers))
    result = validator(wsgi_app)(environ, start_response)
    try:
        body = b''.join(result)
    finally:
        result.close()
    equal(started[0][0], '200 OK')
    equal(json.loads(body), {'method':'GET','path':'/probe'})
    observed['wsgi'] = {'status':started[0][0], 'body':json.loads(body)}
checks.check('WSGI callable returns byte iterable and response metadata', wsgi)
async def asgi():
    events = iter([{'type':'http.request','body':b'ab','more_body':True},
                   {'type':'http.request','body':b'c','more_body':False}])
    sent = []
    async def receive(): return next(events)
    async def send(message): sent.append(message)
    await asgi_app({'type':'http','method':'POST','path':'/probe'}, receive, send)
    equal([m['type'] for m in sent], ['http.response.start','http.response.body'])
    equal(sent[0]['status'], 200)
    equal(json.loads(sent[1]['body']), {'method':'POST','path':'/probe','bytes':3})
    observed['asgi'] = {'status':sent[0]['status'],'body':json.loads(sent[1]['body'])}
checks.check('ASGI callable receives chunk events and sends response events', lambda: asyncio.run(asgi()))
checks.save(observations=observed, transport='In-process protocol calls; no network listener')
