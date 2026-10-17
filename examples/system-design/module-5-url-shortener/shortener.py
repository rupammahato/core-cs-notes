"""Local URL-shortener authority, scoped operation replay and immutable link targets."""
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock
from urllib.parse import urlsplit
import json
import math
import re
import secrets
import sqlite3
import string

ALPHABET = string.ascii_letters+string.digits
CODE_LENGTH = 8
ALLOWED_HOSTS = {'example.com', 'www.example.com', 'docs.python.org'}


class Error(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    tenant: str
    owner: str


TOKENS = {'lesson-alice': Principal('alpha','alice'), 'lesson-bob': Principal('alpha','bob'),
          'lesson-beta': Principal('beta','alice')}


def random_code():
    return ''.join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def valid_code(code):
    return type(code) is str and re.fullmatch(r'[A-Za-z0-9]{8}', code) is not None


def validate_url(url):
    if type(url) is not str or not url.isascii() or not 1<=len(url)<=2048:
        raise Error(400,'invalid_url')
    if any(ord(char)<=32 or ord(char)==127 for char in url) or '\\' in url or re.search(r'%0[ad]',url,re.I):
        raise Error(400,'invalid_url')
    try:
        parsed = urlsplit(url)
        allowed = parsed.scheme == 'https' and parsed.hostname in ALLOWED_HOSTS and parsed.port in (None,443)
        allowed = allowed and parsed.username is None and parsed.password is None
    except ValueError:
        allowed = False
    if not allowed:
        raise Error(400,'destination_not_allowed')
    return url  # Preserve exact path/query/fragment; no semantic URL deduplication.


@dataclass(frozen=True)
class Link:
    code: str
    url: str
    expires_at: float
    disabled: int


class Store:
    def __init__(self, path, code_factory=random_code):
        self.db = sqlite3.connect(path,timeout=5,isolation_level=None,check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock, self.code_factory = RLock(), code_factory
        self.reads, self.collisions = 0, 0
        self.db.executescript('''PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS links(
            code TEXT PRIMARY KEY COLLATE BINARY,url TEXT NOT NULL,
            tenant TEXT NOT NULL,owner TEXT NOT NULL,created_at REAL NOT NULL,
            expires_at REAL NOT NULL,disabled INTEGER NOT NULL CHECK(disabled IN (0,1))
          ) STRICT;
          CREATE TABLE IF NOT EXISTS operations(
            tenant TEXT NOT NULL,owner TEXT NOT NULL,key TEXT NOT NULL,
            fingerprint TEXT NOT NULL,response TEXT NOT NULL,
            PRIMARY KEY(tenant,owner,key)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS counts(
            code TEXT NOT NULL,bucket INTEGER NOT NULL,total INTEGER NOT NULL CHECK(total>=0),
            PRIMARY KEY(code,bucket),FOREIGN KEY(code) REFERENCES links(code)
          ) STRICT;''')

    def create(self, principal, key, url, ttl_seconds, now, fail_after_insert=False):
        if not all(type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,64}',value)
                   for value in (principal.tenant,principal.owner,key)):
            raise Error(400,'invalid_operation_identity')
        validate_url(url)
        if type(ttl_seconds) is not int or not 1<=ttl_seconds<=86400:
            raise Error(400,'invalid_ttl')
        if not math.isfinite(now) or now<0:
            raise ValueError('invalid authoritative time')
        digest = sha256(json.dumps([url,ttl_seconds],separators=(',',':')).encode()).hexdigest()
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                old = self.db.execute('SELECT * FROM operations WHERE tenant=? AND owner=? AND key=?',
                    (principal.tenant,principal.owner,key)).fetchone()
                if old:
                    if old['fingerprint'] != digest:
                        raise Error(409,'operation_conflict')
                    result, replayed = json.loads(old['response']), True
                else:
                    for _ in range(5):
                        code = self.code_factory()
                        if not valid_code(code):
                            raise ValueError('code factory returned invalid code')
                        inserted = self.db.execute('''INSERT INTO links VALUES(?,?,?,?,?,?,0)
                            ON CONFLICT(code) DO NOTHING''',
                            (code,url,principal.tenant,principal.owner,now,now+ttl_seconds)).rowcount
                        if inserted:
                            break
                        self.collisions += 1
                    else:
                        raise Error(503,'code_allocation_exhausted')
                    if fail_after_insert:
                        raise RuntimeError('owned fault after link insertion')
                    result = {'code':code,'url':url,'expires_at':now+ttl_seconds}
                    self.db.execute('INSERT INTO operations VALUES(?,?,?,?,?)',
                        (principal.tenant,principal.owner,key,digest,json.dumps(result,separators=(',',':'))))
                    replayed = False
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise
        return result,replayed

    def lookup(self, code):
        with self.lock:
            self.reads += 1
            row = self.db.execute('SELECT code,url,expires_at,disabled FROM links WHERE code=?',(code,)).fetchone()
            if row is None:
                raise Error(404,'not_found')
            return Link(**dict(row))

    def owned(self, principal, code):
        with self.lock:
            row = self.db.execute('SELECT code,url,expires_at,disabled FROM links WHERE tenant=? AND owner=? AND code=?',
                (principal.tenant,principal.owner,code)).fetchone()
            if row is None:
                raise Error(404,'not_found')
            return dict(row)

    def disable(self, principal, code):
        with self.lock:
            changed = self.db.execute('UPDATE links SET disabled=1 WHERE tenant=? AND owner=? AND code=?',
                (principal.tenant,principal.owner,code)).rowcount
            if not changed:
                raise Error(404,'not_found')

    def close(self):
        self.db.close()
