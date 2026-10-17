"""Read-only local API with fixed synthetic token-to-principal mappings."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlsplit
import json
from store import Principal

TOKENS = {'fixture-alice-a': Principal('tenant-a', 'alice'), 'fixture-bob-a': Principal('tenant-a', 'bob'),
          'fixture-alice-b': Principal('tenant-b', 'alice')}


@contextmanager
def http_fixture(service):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send_json(self, status, value):
            data = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlsplit(self.path)
            requests.append(url.path)  # Do not log the synthetic authorization header.
            authorization = self.headers.get('Authorization', '')
            principal = TOKENS.get(authorization[7:]) if authorization.startswith('Bearer ') else None
            if principal is None:
                return self.send_json(401, {'error': 'Unauthorized'})
            try:
                query = parse_qs(url.query, keep_blank_values=True)
                if url.path in ('/search', '/answer'):
                    if set(query) != {'q'} or len(query['q']) != 1:
                        raise ValueError('Only one q parameter is accepted')
                    if url.path == '/search':
                        hits, cached = service.search(principal, query['q'][0])
                        return self.send_json(200, {'hits': hits, 'cache_hit': cached})
                    return self.send_json(200, service.answer(principal, query['q'][0]))
                if url.path.startswith('/source/') and not query:
                    return self.send_json(200, service.store.source(principal, url.path.removeprefix('/source/')))
                return self.send_json(404, {'error': 'Not found'})
            except PermissionError:
                return self.send_json(404, {'error': 'Source unavailable'})
            except ValueError:
                return self.send_json(400, {'error': 'Invalid query'})

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, name='m23-owned-http')
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()
