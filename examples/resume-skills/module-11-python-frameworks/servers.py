"""Owned temporary loopback listeners; no persistent development server."""
from contextlib import contextmanager
import socket
from threading import Thread
import time
import uvicorn
from werkzeug.serving import make_server, WSGIRequestHandler

class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass

@contextmanager
def flask_server(app):
    server = make_server('127.0.0.1', 0, app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port)
    finally:
        server.shutdown()
        thread.join(5)
        server.server_close()
        if thread.is_alive():
            raise AssertionError('WSGI listener did not stop')

@contextmanager
def fastapi_server(app):
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port,
                             log_level='error', access_log=False, lifespan='on'))
    errors = []
    def serve():
        try:
            server.run(sockets=[sock])
        except BaseException as exc:
            errors.append(repr(exc))
    thread = Thread(target=serve, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            if errors or not thread.is_alive() or time.monotonic() > deadline:
                raise AssertionError(('ASGI startup failed', errors))
            time.sleep(0.01)
        yield 'http://127.0.0.1:' + str(port)
    finally:
        server.should_exit = True
        thread.join(10)
        sock.close()
        if thread.is_alive() or errors:
            raise AssertionError(('ASGI server did not stop cleanly', errors))

def assert_port_closed(url):
    port = int(url.rsplit(':', 1)[1])
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1', port)) == 0:
            raise AssertionError('listener still active: ' + url)
