"""Canonical ownership and an idempotent local result table, separate from checkpoints."""
import sqlite3
from domain import NOTES


class Repository:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def setup(self):
        self.conn.executescript('''
            CREATE TABLE jobs(job_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, user TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE sources(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, revision INTEGER NOT NULL, text TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE attempts(job_id TEXT NOT NULL, node TEXT NOT NULL);
            CREATE TABLE results(job_id TEXT PRIMARY KEY, draft_hash TEXT NOT NULL, answer TEXT NOT NULL);
        ''')
        self.conn.executemany('INSERT INTO sources(id,tenant,revision,text) VALUES (:id,:tenant,:revision,:text)', NOTES)
        self.conn.commit()

    def create_job(self, job_id, principal):
        with self.conn:
            self.conn.execute('INSERT INTO jobs(job_id,tenant,user) VALUES (?,?,?)', (job_id, principal.tenant, principal.user))

    def authorize(self, job_id, principal):
        row = self.conn.execute('SELECT * FROM jobs WHERE job_id=?', (job_id,)).fetchone()
        if not row or row['revoked'] or not principal.can_read or (row['tenant'], row['user']) != (principal.tenant, principal.user):
            raise PermissionError('Job unavailable')
        return principal.tenant + ':' + job_id

    def retrieve(self, job_id, principal, question):
        self.authorize(job_id, principal)
        terms = set(question.lower().split())
        rows = self.conn.execute('SELECT id,tenant,revision,text FROM sources WHERE tenant=? AND deleted=0 ORDER BY id', (principal.tenant,))
        return [dict(row) for row in rows if terms.intersection(row['text'].lower().split())][:2]

    def attempt(self, job_id, node):
        with self.conn:
            self.conn.execute('INSERT INTO attempts VALUES (?,?)', (job_id, node))

    def current(self, principal, evidence):
        for note in evidence:
            row = self.conn.execute('SELECT tenant,revision,text,deleted FROM sources WHERE id=?', (note['id'],)).fetchone()
            if not row or row['deleted'] or row['tenant'] != principal.tenant or row['revision'] != note['revision'] or row['text'] != note['text']:
                return False
        return bool(evidence)

    def commit_result(self, job_id, principal, evidence, expected_hash, answer):
        # Validate source state and insert under one SQLite write transaction.
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            self.authorize(job_id, principal)
            if not self.current(principal, evidence):
                self.conn.rollback()
                return False
            self.conn.execute('INSERT INTO results VALUES (?,?,?) ON CONFLICT(job_id) DO NOTHING', (job_id, expected_hash, answer))
            row = self.conn.execute('SELECT draft_hash,answer FROM results WHERE job_id=?', (job_id,)).fetchone()
            if tuple(row) != (expected_hash, answer):
                raise ValueError('Idempotency key reused for a different result')
            self.conn.commit()
            return True
        except BaseException:
            self.conn.rollback()
            raise
