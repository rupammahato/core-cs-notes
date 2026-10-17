from dataclasses import dataclass
from contextlib import contextmanager
from hashlib import sha256
import re
import sqlite3
from ingestion import extract_document, make_chunks


@dataclass(frozen=True)
class Principal:
    tenant: str
    user: str


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS documents (
                  tenant TEXT, document_id TEXT, owner TEXT NOT NULL, version INTEGER NOT NULL,
                  digest TEXT NOT NULL, config TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
                  PRIMARY KEY(tenant, document_id));
                CREATE TABLE IF NOT EXISTS chunks (
                  rowid INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE NOT NULL, tenant TEXT NOT NULL,
                  document_id TEXT NOT NULL, version INTEGER NOT NULL, page INTEGER NOT NULL,
                  start INTEGER NOT NULL, end INTEGER NOT NULL, text TEXT NOT NULL);
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(text);
                CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, epoch INTEGER NOT NULL);
                INSERT OR IGNORE INTO state VALUES (1, 0);
            ''')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=3)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def publish(self, principal, document_id, version, name, data, size=24, overlap=6, fail_after_insert=False):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', document_id) or type(version) is not int or version < 1:
            raise ValueError('Invalid document/version')
        segments = extract_document(name, data)
        config, chunks = make_chunks(principal.tenant, document_id, version, segments, size, overlap)
        digest = sha256(data).hexdigest()
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            old = connection.execute('SELECT * FROM documents WHERE tenant=? AND document_id=?',
                                     (principal.tenant, document_id)).fetchone()
            if old:
                if old['owner'] != principal.user or old['deleted']:
                    raise PermissionError('Document unavailable')
                if version < old['version']:
                    return 'stale'
                if version == old['version']:
                    if (digest, config) == (old['digest'], old['config']):
                        return 'duplicate'
                    raise Conflict('Same version has different content/configuration')
            self._remove_chunks(connection, principal.tenant, document_id)
            for chunk in chunks:
                cursor = connection.execute('INSERT INTO chunks(chunk_id,tenant,document_id,version,page,start,end,text) VALUES(?,?,?,?,?,?,?,?)',
                    (chunk['chunk_id'], principal.tenant, document_id, version, chunk['page'], chunk['start'], chunk['end'], chunk['text']))
                connection.execute('INSERT INTO search_index(rowid,text) VALUES(?,?)', (cursor.lastrowid, chunk['text']))
                if fail_after_insert:
                    raise RuntimeError('Controlled publication failure')
            connection.execute('''INSERT INTO documents(tenant,document_id,owner,version,digest,config) VALUES(?,?,?,?,?,?)
                ON CONFLICT(tenant,document_id) DO UPDATE SET version=excluded.version,digest=excluded.digest,config=excluded.config''',
                (principal.tenant, document_id, principal.user, version, digest, config))
            connection.execute('UPDATE state SET epoch=epoch+1 WHERE id=1')
        return 'published'

    @staticmethod
    def _remove_chunks(connection, tenant, document_id):
        ids = connection.execute('SELECT rowid FROM chunks WHERE tenant=? AND document_id=?', (tenant, document_id)).fetchall()
        connection.executemany('DELETE FROM search_index WHERE rowid=?', [(row['rowid'],) for row in ids])
        connection.execute('DELETE FROM chunks WHERE tenant=? AND document_id=?', (tenant, document_id))

    def delete(self, principal, document_id):
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT * FROM documents WHERE tenant=? AND document_id=? AND owner=?',
                                     (principal.tenant, document_id, principal.user)).fetchone()
            if not row:
                raise PermissionError('Document unavailable')
            if row['deleted']:
                return 'already-deleted'
            self._remove_chunks(connection, principal.tenant, document_id)
            connection.execute('UPDATE documents SET deleted=1 WHERE tenant=? AND document_id=?', (principal.tenant, document_id))
            connection.execute('UPDATE state SET epoch=epoch+1 WHERE id=1')
        return 'deleted'

    @staticmethod
    def query_expression(query):
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200:
            raise ValueError('Query length must be 1..200')
        terms = list(dict.fromkeys(re.findall(r'\w+', query.lower())))[:12]
        if not terms:
            raise ValueError('At least one search term required')
        return ' OR '.join('"' + term + '"' for term in terms)

    def search(self, principal, query, limit=5):
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('Limit must be 1..10')
        expression = self.query_expression(query)
        with self.connect() as connection:
            connection.execute('BEGIN')
            epoch = connection.execute('SELECT epoch FROM state WHERE id=1').fetchone()['epoch']
            rows = connection.execute('''SELECT c.*, bm25(search_index) AS score FROM search_index
                JOIN chunks c ON c.rowid=search_index.rowid
                JOIN documents d ON d.tenant=c.tenant AND d.document_id=c.document_id
                WHERE search_index MATCH ? AND d.tenant=? AND d.owner=? AND d.deleted=0 AND d.version=c.version
                ORDER BY score ASC, c.chunk_id ASC LIMIT ?''', (expression, principal.tenant, principal.user, limit)).fetchall()
        return epoch, [dict(row) for row in rows]

    def source(self, principal, chunk_id):
        with self.connect() as connection:
            row = connection.execute('''SELECT c.* FROM chunks c JOIN documents d
                ON d.tenant=c.tenant AND d.document_id=c.document_id
                WHERE c.chunk_id=? AND d.tenant=? AND d.owner=? AND d.deleted=0 AND d.version=c.version''',
                (chunk_id, principal.tenant, principal.user)).fetchone()
        if not row:
            raise PermissionError('Source unavailable')
        return dict(row)

    def epoch(self):
        with self.connect() as connection:
            return connection.execute('SELECT epoch FROM state WHERE id=1').fetchone()['epoch']
