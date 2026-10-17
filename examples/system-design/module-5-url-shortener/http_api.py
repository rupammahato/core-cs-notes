"""Owned loopback shortener API; redirects are returned without fetching destinations."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
import json

from shortener import Error,TOKENS


def make_server(service, public_base='https://short.example'):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self,*_):
            pass  # No URLs, credentials or query strings in routine logs.

        def handle_api(self):
            status,body,headers = 500,{'error':'internal_error'},{}
            path = urlsplit(self.path).path
            try:
                if path.startswith('/r/'):
                    if self.command not in ('GET','HEAD'):
                        headers['Allow'] = 'GET, HEAD'
                        raise Error(405,'method_not_allowed')
                    target = service.resolve(path[3:],record=self.command == 'GET')
                    status,body,headers['Location'] = 302,None,target
                elif path == '/api/links' or path.startswith('/api/links/'):
                    token = self.headers.get('Authorization','')
                    principal = TOKENS.get(token[7:]) if token.startswith('Bearer ') else None
                    if principal is None:
                        headers['WWW-Authenticate'] = 'Bearer'
                        raise Error(401,'unauthorized')
                    if path == '/api/links' and self.command == 'POST':
                        if self.headers.get('Content-Type') != 'application/json':
                            raise Error(415,'json_required')
                        sizes = self.headers.get_all('Content-Length',[])
                        if self.headers.get('Transfer-Encoding') is not None or len(sizes)!=1 or not sizes[0].isascii() or not sizes[0].isdigit():
                            raise Error(411,'fixed_length_required')
                        length = int(sizes[0])
                        if not 1<=length<=4096:
                            raise Error(413,'body_too_large')
                        try:
                            payload = json.loads(self.rfile.read(length))
                        except (ValueError,UnicodeError):
                            raise Error(400,'invalid_json')
                        if type(payload) is not dict or set(payload) not in ({'url'},{'url','ttl_seconds'}):
                            raise Error(400,'invalid_fields')
                        result,replayed = service.store.create(principal,self.headers.get('Idempotency-Key',''),
                            payload['url'],payload.get('ttl_seconds',3600),service.clock())
                        body = dict(result,short_url=public_base+'/r/'+result['code'])
                        status = 201
                        headers.update({'Location':'/api/links/'+result['code'],'Idempotency-Replayed':str(replayed).lower()})
                    elif path.startswith('/api/links/'):
                        suffix = path[len('/api/links/'):]
                        if self.command == 'GET' and suffix.endswith('/stats'):
                            body,status = service.statistics(principal,suffix[:-6]),200
                        elif self.command == 'GET':
                            body,status = service.store.owned(principal,suffix),200
                        elif self.command == 'DELETE' and '/' not in suffix:
                            service.disable(principal,suffix)
                            body,status = None,204
                        else:
                            raise Error(405,'method_not_allowed')
                    else:
                        raise Error(405,'method_not_allowed')
                else:
                    raise Error(404,'not_found')
            except Error as error:
                status,body = error.status,{'error':error.code}
            except Exception:
                status,body = 500,{'error':'internal_error'}
            encoded = b'' if body is None else json.dumps(body).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(encoded)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            for name,value in headers.items():
                self.send_header(name,value)
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(encoded)

        do_GET = do_HEAD = do_POST = do_DELETE = handle_api

    class Server(ThreadingHTTPServer):
        daemon_threads = False
        block_on_close = True

    return Server(('127.0.0.1',0),Handler)
