from uuid import uuid4
from threading import Lock

class TraceLog:
    def __init__(self):
        self.rows = []
        self.lock = Lock()
    def add(self, request_id, event):
        with self.lock:
            self.rows.append((request_id,event))
    def trace(self, request_id):
        with self.lock:
            return [event for rid,event in self.rows if rid==request_id]

trace_log = TraceLog()  # Bounded test workload only, not a production telemetry store.

class CorrelationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.request_id = uuid4().hex
        trace_log.add(request.request_id,'middleware-in')
        response = self.get_response(request)
        trace_log.add(request.request_id,'middleware-out')
        response['X-Request-ID'] = request.request_id
        response['Cache-Control'] = 'no-store'
        return response
    def process_view(self, request, view_func, view_args, view_kwargs):
        trace_log.add(request.request_id,'view-resolved')
