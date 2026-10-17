"""Scoped SQLite policies and private text-upload quarantine; trusted lesson principals."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from threading import RLock
from uuid import uuid4
import math
import re
import sqlite3


class Denied(Exception):
    def __init__(self, status, code, retry_after=None):
        self.status, self.code, self.retry_after = status, code, retry_after
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    tenant: str
    user: str


# Published lesson credentials, NOT production authentication.
TOKENS = {'lesson-alice': Principal('alpha', 'alice'), 'lesson-bob': Principal('alpha', 'bob'),
          'lesson-viewer': Principal('alpha', 'eve'), 'lesson-beta': Principal('beta', 'alice')}


class Store:
    def __init__(self, database, vault):
        self.db = sqlite3.connect(database, timeout=5, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = RLock()  # Prevent interleaved use of this connection by HTTP threads.
        self.vault = Path(vault).resolve()
        self.vault.mkdir(exist_ok=True)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS members(tenant TEXT,user TEXT,role TEXT,active INTEGER,
            PRIMARY KEY(tenant,user));
          CREATE TABLE IF NOT EXISTS notes(tenant TEXT,owner TEXT,id TEXT,title TEXT,
            PRIMARY KEY(tenant,id));
          CREATE TABLE IF NOT EXISTS quota(tenant TEXT,action TEXT,window INTEGER,used INTEGER CHECK(used>=0),
            PRIMARY KEY(tenant,action,window));
          CREATE TABLE IF NOT EXISTS uploads(tenant TEXT,owner TEXT,id TEXT,name TEXT,size INTEGER,
            digest TEXT,state TEXT CHECK(state IN ('pending','ready','rejected')),PRIMARY KEY(tenant,id));
        ''')

    def seed(self):
        with self.lock:
            self.db.executemany('INSERT INTO members VALUES(?,?,?,1)',
                [('alpha','alice','editor'), ('alpha','bob','editor'), ('alpha','eve','viewer'), ('beta','alice','editor')])
            self.db.executemany('INSERT INTO notes VALUES(?,?,?,?)',
                [('alpha','alice','shared_id','PRIVATE_ALPHA_NOTE'), ('alpha','bob','bob_note','PRIVATE_BOB_NOTE'),
                 ('beta','alice','shared_id','PRIVATE_BETA_NOTE')])

    def authorize(self, principal, action):
        with self.lock:
            row = self.db.execute('SELECT role,active FROM members WHERE tenant=? AND user=?',
                                  (principal.tenant, principal.user)).fetchone()
            allowed = {'viewer': {'read'}, 'editor': {'read', 'upload'}}
            if row is None or row['active'] != 1 or action not in allowed.get(row['role'], set()):
                raise Denied(403, 'forbidden')

    def note(self, principal, identity):
        with self.lock:
            self.authorize(principal, 'read')
            row = self.db.execute('SELECT id,title FROM notes WHERE tenant=? AND owner=? AND id=?',
                                 (principal.tenant, principal.user, identity)).fetchone()
            if row is None:
                raise Denied(404, 'not_found')
            return dict(row)

    def listing(self, principal):
        with self.lock:
            self.authorize(principal, 'read')
            return [dict(row) for row in self.db.execute('SELECT id,title FROM notes WHERE tenant=? AND owner=? ORDER BY id LIMIT 20',
                (principal.tenant, principal.user))]

    def take_quota(self, principal, action, now, limit=1000, seconds=10):
        if not math.isfinite(now) or now<0 or type(limit) is not int or limit<1 or type(seconds) is not int or seconds<1:
            raise ValueError('invalid quota configuration')
        window = math.floor(now/seconds)
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                self.db.execute('DELETE FROM quota WHERE window<?', (window-1,))
                self.db.execute('INSERT OR IGNORE INTO quota VALUES(?,?,?,0)', (principal.tenant, action, window))
                changed = self.db.execute('UPDATE quota SET used=used+1 WHERE tenant=? AND action=? AND window=? AND used<?',
                    (principal.tenant, action, window, limit)).rowcount
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise
        if not changed:
            raise Denied(429, 'quota_exceeded', max(1, math.ceil((window+1)*seconds-now)))

    def stage(self, principal, name, mime, body, byte_budget=2048):
        self.authorize(principal, 'upload')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_. -]{0,63}\.txt', name) or '..' in name:
            raise Denied(400, 'invalid_filename')
        if mime != 'text/plain':
            raise Denied(415, 'text_required')
        if not 1 <= len(body) <= 1024:
            raise Denied(413, 'invalid_upload_size')
        identity = uuid4().hex
        path = self.vault/identity  # No user path or original filename is used for storage.
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                self.authorize(principal, 'upload')
                retained = self.db.execute('SELECT coalesce(sum(size),0) FROM uploads WHERE tenant=?', (principal.tenant,)).fetchone()[0]
                if retained+len(body)>byte_budget:
                    raise Denied(429, 'storage_quota_exceeded')
                with path.open('xb') as file:
                    file.write(body)
                self.db.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?,?)',
                    (principal.tenant, principal.user, identity, name, len(body), sha256(body).hexdigest(), 'pending'))
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                path.unlink(missing_ok=True)
                raise
        return {'id': identity, 'state': 'pending'}

    def approve(self, tenant, identity):
        # Internal validator; no public approval route. NOT an antivirus scanner.
        with self.lock:
            row = self.db.execute('SELECT * FROM uploads WHERE tenant=? AND id=?', (tenant, identity)).fetchone()
            if row is None:
                raise Denied(404, 'not_found')
            if row['state'] != 'pending':
                return row['state']
            body = (self.vault/row['id']).read_bytes()
            valid = len(body) == row['size'] and sha256(body).hexdigest() == row['digest']
            try:
                text = body.decode('utf-8', errors='strict')
                valid = valid and '\0' not in text
            except UnicodeDecodeError:
                valid = False
            state = 'ready' if valid else 'rejected'
            self.db.execute('UPDATE uploads SET state=? WHERE tenant=? AND id=?', (state, tenant, identity))
            return state

    def download(self, principal, identity):
        with self.lock:
            self.authorize(principal, 'read')
            row = self.db.execute('SELECT * FROM uploads WHERE tenant=? AND owner=? AND id=?',
                (principal.tenant, principal.user, identity)).fetchone()
            if row is None:
                raise Denied(404, 'not_found')
            if row['state'] != 'ready':
                raise Denied(409, 'upload_not_ready')
            return row['name'], (self.vault/row['id']).read_bytes()

    def close(self):
        self.db.close()
