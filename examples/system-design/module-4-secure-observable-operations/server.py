"""Owned loopback HTTP lesson; Python http.server is not a production web server."""
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Condition
from time import perf_counter, time
from urllib.parse import urlsplit
from uuid import uuid4
import json

from policy import Denied, TOKENS


class Runtime:
    def __init__(self, capacity=2):
        self.condition = Condition()
        self.started = self.database_available = True
        self.draining = False
        self.active, self.peak, self.capacity = 0, 0, capacity
        self.logs, self.traces = deque(maxlen=128), deque(maxlen=128)
        self.counts = Counter()
        self.hold = None  # Owned test barrier, never exposed as a request parameter.

    def ready(self):
        with self.condition:
            return self.started and self.database_available and not self.draining

    def enter(self):
        with self.condition:
            if not self.ready():
                raise Denied(503, 'not_ready')
            if self.active >= self.capacity:
                raise Denied(503, 'overloaded', 1)
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.condition.notify_all()

    def leave(self):
        with self.condition:
            self.active -= 1
            self.condition.notify_all()

    def drain(self):
        with self.condition:
            self.draining = True
            self.condition.notify_all()

    def record(self, trace_id, method, route, status, elapsed, events):
        with self.condition:
            self.counts[(method, route, str(status//100)+'xx')] += 1
            self.logs.append({'trace_id': trace_id, 'method': method, 'route': route,
                              'status': status, 'duration_ms': round(elapsed*1000, 3)})
            self.traces.append({'trace_id': trace_id, 'events': events})


def make_server(store, runtime, clock=time, quota_limit=1000):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Suppress standard raw-URL/header logging; structured records below.

        def handle_request(self):
            start, trace_id, events = perf_counter(), uuid4().hex, ['http.received']
            path = urlsplit(self.path).path
            route = '/unmatched'
            if path in ('/livez', '/readyz', '/notes', '/uploads'):
                route = path
            elif path.startswith('/notes/'):
                route = '/notes/:id'
            elif path.startswith('/uploads/'):
                route = '/uploads/:id'
            status, headers, body, entered = 500, {}, {'error': 'internal_error'}, False
            try:
                if path == '/livez' and self.command == 'GET':
                    status, body = 200, {'alive': True}
                elif path == '/readyz' and self.command == 'GET':
                    status = 200 if runtime.ready() else 503
                    body = {'ready': status == 200}
                else:
                    runtime.enter()
                    entered = True
                    raw = self.headers.get('Authorization', '')
                    principal = TOKENS.get(raw[7:]) if raw.startswith('Bearer ') else None
                    if principal is None:
                        headers['WWW-Authenticate'] = 'Bearer'
                        raise Denied(401, 'unauthorized')
                    events.append('identity.lesson_allowlist')
                    action = 'upload' if path == '/uploads' and self.command == 'POST' else 'read'
                    store.authorize(principal, action)
                    events.append('authorization.current_membership')
                    store.take_quota(principal, action, clock(), quota_limit)
                    events.append('quota.accepted')
                    if runtime.hold is not None and self.command == 'GET' and route == '/notes/:id':
                        if not runtime.hold.wait(timeout=5):
                            raise Denied(503, 'fixture_wait_expired')
                    if self.command == 'GET' and path == '/notes':
                        body, status = {'notes': store.listing(principal)}, 200
                    elif self.command == 'GET' and route == '/notes/:id':
                        body, status = store.note(principal, path[len('/notes/'):]), 200
                    elif self.command == 'POST' and path == '/uploads':
                        if self.headers.get('Transfer-Encoding') is not None:
                            raise Denied(400, 'fixed_length_required')
                        sizes = self.headers.get_all('Content-Length', [])
                        if len(sizes) != 1 or not sizes[0].isascii() or not sizes[0].isdigit():
                            raise Denied(411, 'length_required')
                        size = int(sizes[0])
                        if not 1<=size<=1024:
                            raise Denied(413, 'invalid_upload_size')
                        payload = self.rfile.read(size)
                        if len(payload) != size:
                            raise Denied(400, 'incomplete_body')
                        body = store.stage(principal, self.headers.get('X-Filename', ''), self.headers.get('Content-Type', ''), payload)
                        status = 202
                    elif self.command == 'GET' and route == '/uploads/:id':
                        name, body = store.download(principal, path[len('/uploads/'):])
                        headers.update({'Content-Type': 'application/octet-stream',
                                        'Content-Disposition': 'attachment; filename="'+name+'"'})
                        status = 200
                    else:
                        raise Denied(404, 'not_found')
                    events.append('store.completed')
            except Denied as error:
                status, body = error.status, {'error': error.code}
                if error.retry_after is not None:
                    headers['Retry-After'] = str(error.retry_after)
                events.append('request.rejected')
            except Exception:
                events.append('request.internal_error')
            encoded = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
            try:
                self.send_response(status)
                self.send_header('Content-Type', headers.pop('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(encoded)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('X-Request-Id', trace_id)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(encoded)
                events.append('http.response_written')
            finally:
                if entered:
                    runtime.leave()
                runtime.record(trace_id, self.command, route, status, perf_counter()-start, events)

        def setup(self):
            super().setup()
            self.connection.settimeout(3)  # Socket timeout, not a complete production deadline.

        do_GET = do_POST = handle_request

    class Server(ThreadingHTTPServer):
        daemon_threads = False
        block_on_close = True

    return Server(('127.0.0.1', 0), Handler)
