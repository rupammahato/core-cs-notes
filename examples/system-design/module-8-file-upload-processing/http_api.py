"""Owned local control API plus separate bearer-capability object PUT."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import sqlite3
from uploads import Error, Uploads

CREDENTIALS = {'lesson-alice':('tenant-a','alice'), 'lesson-bob':('tenant-a','bob'),
               'lesson-other':('tenant-b','alice')}


def server(database, root, secret, clock):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, value=None, raw=None):
            data = raw if raw is not None else json.dumps(value or {}).encode()
            self.send_response(status)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Type', 'text/plain; charset=utf-8' if raw is not None else 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            if raw is not None:
                self.send_header('Content-Disposition', 'attachment; filename="download.txt"')
            self.end_headers()
            self.wfile.write(data)
            self.close_connection = True

        def body(self, limit):
            length = self.headers.get('Content-Length', '0')
            if self.headers.get('Transfer-Encoding') or not length.isascii() or not length.isdigit() or len(length)>8 or int(length)>limit:
                raise Error(413, 'body_size_or_framing')
            data = self.rfile.read(int(length))
            if len(data) != int(length):
                raise Error(400, 'incomplete_body')
            return data

        def handle_request(self):
            item = None
            try:
                object_route = re.fullmatch(r'/objects/([a-f0-9]{32})', self.path)
                file_route = re.fullmatch(r'/api/files/([a-f0-9]{32})(/complete|/download)?', self.path)
                if object_route and self.command == 'PUT':
                    if self.headers.get('Content-Type') != 'text/plain':
                        raise Error(415, 'unsupported_declared_type')
                    raw = self.body(1024)
                    item = Uploads(database, root, secret)
                    created = item.upload(object_route[1], self.headers.get('X-Lesson-Upload',''), raw, clock())
                    return self.reply(201 if created else 200, {'stored':True})
                if not ((self.path == '/api/files' and self.command == 'POST') or file_route):
                    raise Error(404, 'unknown_route')
                identity = CREDENTIALS.get(self.headers.get('Authorization','').removeprefix('Bearer '))
                if not identity or not self.headers.get('Authorization','').startswith('Bearer '):
                    raise Error(401, 'lesson_credential_required')
                item = Uploads(database, root, secret)
                if self.path == '/api/files':
                    data = json.loads(self.body(2048))
                    result = item.create(*identity, self.headers.get('Idempotency-Key',''), data, clock())
                    return self.reply(201, result)
                file_id, action = file_route.groups()
                if self.body(0):
                    raise Error(400, 'body_not_accepted')
                if self.command == 'POST' and action == '/complete':
                    return self.reply(202, {'state':item.complete(*identity,file_id,clock())})
                if self.command == 'GET' and action == '/download':
                    return self.reply(200, raw=item.download(*identity,file_id))
                if self.command == 'DELETE' and action is None:
                    item.delete(*identity,file_id)
                    return self.reply(200, {'state':'deleted'})
                if self.command == 'GET' and action is None:
                    row = item.owned(*identity,file_id)
                    return self.reply(200, {'id':row['id'],'state':row['state'],'reason':row['reason']})
                raise Error(404, 'unknown_route')
            except Error as error:
                self.reply(error.status, {'error':error.reason})
            except (ValueError, UnicodeError):
                self.reply(400, {'error':'malformed_input_or_object'})
            except sqlite3.Error:
                self.reply(503, {'error':'metadata_unavailable'})
            finally:
                if item is not None:
                    item.close()

        do_POST = handle_request
        do_PUT = handle_request
        do_GET = handle_request
        do_DELETE = handle_request
    return ThreadingHTTPServer(('127.0.0.1', 0), Handler)
