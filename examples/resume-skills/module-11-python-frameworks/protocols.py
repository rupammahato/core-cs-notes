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
