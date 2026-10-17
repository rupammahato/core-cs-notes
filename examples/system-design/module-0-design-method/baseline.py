"""Small persistent repository probe, not an authenticated HTTP service."""
import hashlib
import json
import re
import sqlite3
from uuid import uuid4


class Conflict(Exception):
    pass


class NotFound(Exception):
    pass


class StaleVersion(Exception):
    pass


class Notes:
    def __init__(self, path, id_factory=lambda: str(uuid4())):
        self.db = sqlite3.connect(path, timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.id_factory = id_factory

    def close(self):
        self.db.close()

    def initialize(self):
        self.db.executescript('''
            CREATE TABLE notes (
                tenant TEXT NOT NULL, id TEXT NOT NULL, owner TEXT NOT NULL,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
                content TEXT NOT NULL CHECK(length(CAST(content AS BLOB)) <= 4096),
                revision INTEGER NOT NULL CHECK(revision > 0), PRIMARY KEY(tenant,id)
            );
            CREATE TABLE operations (
                tenant TEXT NOT NULL, owner TEXT NOT NULL, operation_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL, note_id TEXT NOT NULL, response TEXT NOT NULL,
                PRIMARY KEY(tenant,owner,operation_id),
                FOREIGN KEY(tenant,note_id) REFERENCES notes(tenant,id)
            );
        ''')

    @staticmethod
    def identity(*values):
        if any(type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) for value in values):
            raise ValueError('Invalid identity')

    @staticmethod
    def payload(title, content):
        if type(title) is not str or not title.strip() or len(title) > 120 or type(content) is not str or len(content.encode('utf-8')) > 4096:
            raise ValueError('Invalid title/content')

    @staticmethod
    def representation(row):
        return {field: row[field] for field in ('id', 'title', 'content', 'revision')}

    def create(self, tenant, owner, operation_id, title, content, fail_after_insert=False):
        self.identity(tenant, owner, operation_id)
        self.payload(title, content)
        fingerprint = hashlib.sha256(json.dumps([title, content], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        with self.db:
            # Serialize the read-dedupe/create sequence for this SQLite probe.
            self.db.execute('BEGIN IMMEDIATE')
            prior = self.db.execute('SELECT * FROM operations WHERE tenant=? AND owner=? AND operation_id=?', (tenant, owner, operation_id)).fetchone()
            if prior:
                if prior['fingerprint'] != fingerprint:
                    raise Conflict('Operation identity reused for different input')
                return {'replayed': True, 'note': json.loads(prior['response'])}
            note_id = self.id_factory()
            self.identity(note_id)
            self.db.execute('INSERT INTO notes VALUES (?,?,?,?,?,1)', (tenant, note_id, owner, title, content))
            if fail_after_insert:
                raise RuntimeError('Injected interruption before operation record')
            note = self.get(tenant, owner, note_id)
            self.db.execute('INSERT INTO operations VALUES (?,?,?,?,?,?)', (tenant, owner, operation_id, fingerprint, note_id, json.dumps(note)))
        return {'replayed': False, 'note': note}

    def get(self, tenant, owner, note_id):
        self.identity(tenant, owner, note_id)
        row = self.db.execute('SELECT * FROM notes WHERE tenant=? AND owner=? AND id=?', (tenant, owner, note_id)).fetchone()
        if not row:
            raise NotFound('No visible note')
        return self.representation(row)

    def update(self, tenant, owner, note_id, expected_revision, title, content):
        self.identity(tenant, owner, note_id)
        self.payload(title, content)
        if type(expected_revision) is not int or expected_revision < 1:
            raise ValueError('Positive integer expected revision required')
        with self.db:
            changed = self.db.execute('''UPDATE notes SET title=?,content=?,revision=revision+1
                WHERE tenant=? AND owner=? AND id=? AND revision=?''',
                (title, content, tenant, owner, note_id, expected_revision)).rowcount
            if not changed:
                self.get(tenant, owner, note_id)  # Preserve the same invisible-resource outcome.
                raise StaleVersion('Expected revision no longer current')
            note = self.get(tenant, owner, note_id)
        return note
