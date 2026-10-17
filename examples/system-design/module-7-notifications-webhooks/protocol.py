"""Custom lesson HMAC protocol and transactional receiver. Not a vendor SDK."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import re
import sqlite3
from delivery import envelope, identity


def sign(secret, timestamp, delivery, raw):
    identity(delivery)
    return hmac.new(secret, str(timestamp).encode()+b'.'+delivery.encode()+b'.'+raw, hashlib.sha256).hexdigest()


def authenticate(secret, timestamp, delivery, raw, signature, now_ms):
    if not re.fullmatch(r'[0-9]{1,12}', timestamp or '') or abs(now_ms//1000-int(timestamp)) > 30:
        raise ValueError('timestamp outside 30-second tolerance')
    identity(delivery)
    if not re.fullmatch(r'[a-f0-9]{64}', signature or '') or not hmac.compare_digest(sign(secret, timestamp, delivery, raw), signature):
        raise ValueError('signature mismatch')


def receive(path, endpoint, tenant, delivery, raw):
    body = json.loads(raw)
    if (type(body) is not dict or set(body) != {'version','tenant','event_id','type','message'}
        or type(body['version']) is not int or body['version'] != 1
        or body['tenant'] != tenant or body['type'] != 'practice.reminder'):
        raise ValueError('invalid event scope/schema')
    if envelope(body['tenant'], body['event_id'], body['message']) != raw:
        raise ValueError('noncanonical lesson envelope')
    db = sqlite3.connect(path, timeout=0.3, isolation_level=None)
    try:
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT digest FROM receipts WHERE endpoint=? AND delivery=?', (endpoint, delivery)).fetchone()
        digest = hashlib.sha256(raw).hexdigest()
        if old:
            if old[0] != digest:
                raise ValueError('delivery identity reused with different content')
            db.execute('COMMIT')
            return False
        db.execute('INSERT INTO receipts VALUES(?,?,?)', (endpoint, delivery, digest))
        db.execute('INSERT INTO effects VALUES(?,?,?)', (endpoint, delivery, body['message']))
        db.execute('COMMIT')
        return True
    except BaseException:
        if db.in_transaction:
            db.execute('ROLLBACK')
        raise
    finally:
        db.close()


def initialize(path):
    db = sqlite3.connect(path)
    try:
        db.executescript('''CREATE TABLE receipts(endpoint TEXT,delivery TEXT,digest TEXT,PRIMARY KEY(endpoint,delivery));
            CREATE TABLE effects(endpoint TEXT,delivery TEXT,message TEXT,PRIMARY KEY(endpoint,delivery));''')
    finally:
        db.close()


def server(path, registry, now, controls):
    # Registry/controls belong to the harness; no public endpoint-registration API.
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, **headers):
            self.send_response(status)
            self.send_header('Content-Length', '0')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            for name, value in headers.items():
                self.send_header(name.replace('_','-'), value)
            self.end_headers()
            self.close_connection = True

        def do_POST(self):
            entry = registry.get(self.path)
            if not entry:
                return self.reply(404)
            length = self.headers.get('Content-Length', '')
            if self.headers.get('Transfer-Encoding') or not length.isdigit() or not 0 < int(length) <= 4096:
                return self.reply(400)
            raw = self.rfile.read(int(length))
            endpoint, tenant, secret = entry
            delivery = self.headers.get('X-Lesson-Delivery', '')
            try:
                authenticate(secret, self.headers.get('X-Lesson-Timestamp'), delivery, raw,
                             self.headers.get('X-Lesson-Signature'), now())
            except ValueError:
                return self.reply(401)
            planned = controls.get(endpoint, [])
            action = planned.pop(0) if planned else 200
            if type(action) is int and not 200 <= action < 300:
                return self.reply(action, **({'Retry_After':'2'} if action == 429 else {}))
            try:
                receive(path, endpoint, tenant, delivery, raw)
            except (ValueError, UnicodeError):
                return self.reply(400)
            except sqlite3.Error:
                return self.reply(503)
            if action == 'drop_after_commit':
                self.close_connection = True  # Real socket closes before any HTTP status.
                return
            self.reply(action)
    return ThreadingHTTPServer(('127.0.0.1', 0), Handler)
