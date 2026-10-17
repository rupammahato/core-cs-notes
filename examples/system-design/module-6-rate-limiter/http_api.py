"""Owned loopback lesson API. Published bearer credentials are demo identity only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sqlite3
import time
from limiter import Policy, PolicyConflict, Store, StoreFull


CREDENTIALS = {'lesson-alice': ('tenant-a', 'alice'),
               'lesson-alice-rotated': ('tenant-a', 'alice'),
               'lesson-bob': ('tenant-a', 'bob'),
               'lesson-other-tenant': ('tenant-b', 'alice')}
ROUTES = {('GET', '/api/read'): ('read', True),
          ('POST', '/api/write'): ('write', False)}


class Context:
    def __init__(self, path, clock=None):
        self.path = path
        self.clock = clock or (lambda: time.time_ns() // 1000000)
        self.policy = Policy()
        self.unavailable = False  # Harness-controlled outage, never a request header.
        self.fail_work = False


def server(context):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_json(self, status, body, extra=None):
            raw = json.dumps(body, separators=(',', ':')).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Connection', 'close')
            for name, value in (extra or {}).items():
                self.send_header(name, str(value))
            self.end_headers()
            self.wfile.write(raw)
            self.close_connection = True

        def handle_request(self):
            route = ROUTES.get((self.command, self.path))
            if route is None:
                return self.send_json(404, {'error': 'unknown route'})
            identity = CREDENTIALS.get(self.headers.get('Authorization', '').removeprefix('Bearer '))
            if not identity or not self.headers.get('Authorization', '').startswith('Bearer '):
                return self.send_json(401, {'error': 'lesson credential required'})
            # No body, client-selected cost or untrusted forwarded identity in this API.
            if self.headers.get('Transfer-Encoding') is not None or self.headers.get('Content-Length', '0') != '0':
                return self.send_json(400, {'error': 'body not accepted'})
            route_name, fail_open = route
            headers = {}
            store = None
            try:
                if context.unavailable:
                    raise sqlite3.OperationalError('injected dependency outage')
                store = Store(context.path)
                decision = store.decide(*identity, route_name, context.policy, context.clock())
            except (sqlite3.OperationalError, StoreFull):
                if not fail_open:
                    return self.send_json(503, {'error': 'quota authority unavailable'},
                                          {'X-Lesson-Quota': 'unavailable'})
                headers['X-Lesson-Quota'] = 'degraded-open'
            except PolicyConflict:
                return self.send_json(503, {'error': 'policy migration required'})
            else:
                headers = {'X-Lesson-Quota': 'enforced',
                           'X-Lesson-Quota-Remaining': decision.remaining}
                if not decision.allowed:
                    headers['Retry-After'] = max(1, (decision.retry_ms + 999) // 1000)
                    return self.send_json(429, {'error': 'rate limit exceeded'}, headers)
            finally:
                if store is not None:
                    store.close()
            # Admission is charged even if the subsequent work fails. No refund here.
            return self.send_json(500 if context.fail_work else 200,
                                  {'work': 'failed' if context.fail_work else 'completed'}, headers)

        do_GET = handle_request
        do_POST = handle_request

    return ThreadingHTTPServer(('127.0.0.1', 0), Handler)
