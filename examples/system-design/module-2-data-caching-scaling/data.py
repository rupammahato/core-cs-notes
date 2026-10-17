"""Real SQLite query/index/pagination probe; supplied scope is NOT authentication."""
from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True)
class Scope:
    tenant: str
    owner: str


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    content: str
    created_at: int
    revision: int


class Missing(Exception):
    pass


class Stale(Exception):
    pass


class Notes:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.reads = 0
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS notes (
                tenant TEXT NOT NULL, owner TEXT NOT NULL, id TEXT NOT NULL,
                title TEXT NOT NULL, content TEXT NOT NULL,
                created_at INTEGER NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
                PRIMARY KEY(tenant,id)
            ) STRICT;
        ''')

    def seed(self):
        # 4 tenants x 10 owners x 300 notes; timestamps deliberately have ties.
        rows = [(f't{t}', f'u{u}', f'n{u:02}_{i:04}', f'Note {i}', 'private text', i // 3, 1)
                for t in range(4) for u in range(10) for i in range(300)]
        with self.db:
            self.db.executemany('INSERT INTO notes VALUES(?,?,?,?,?,?,?)', rows)
        return len(rows)

    def add_listing_index(self):
        self.db.execute('''CREATE INDEX notes_owner_recent
            ON notes(tenant,owner,created_at DESC,id DESC)''')
        self.db.execute('ANALYZE')

    @staticmethod
    def query(scope, limit=20, cursor=None, offset=0):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('limit must be an integer in 1..100')
        if type(offset) is not int or offset < 0:
            raise ValueError('offset must be a nonnegative integer')
        if cursor is not None and offset:
            raise ValueError('choose cursor or offset')
        sql = 'SELECT id,title,created_at,revision FROM notes WHERE tenant=? AND owner=?'
        parameters = [scope.tenant, scope.owner]
        if cursor is not None:
            if not isinstance(cursor, tuple) or len(cursor) != 2 or type(cursor[0]) is not int or not isinstance(cursor[1], str):
                raise ValueError('cursor must be (created_at,id)')
            sql += ' AND (created_at,id) < (?,?)'
            parameters.extend(cursor)
        sql += ' ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?'
        return sql, [*parameters, limit, offset]

    def listing(self, scope, limit=20, cursor=None, offset=0):
        sql, parameters = self.query(scope, limit, cursor, offset)
        return [dict(row) for row in self.db.execute(sql, parameters)]

    def profile(self, scope, limit=20, cursor=None, offset=0):
        sql, parameters = self.query(scope, limit, cursor, offset)
        plan = [row['detail'] for row in self.db.execute('EXPLAIN QUERY PLAN '+sql, parameters)]
        instructions = 0

        def progress():
            nonlocal instructions
            instructions += 1
            return 0

        self.db.set_progress_handler(progress, 1)
        try:
            rows = [dict(row) for row in self.db.execute(sql, parameters)]
        finally:
            self.db.set_progress_handler(None, 0)
        return {'plan': plan, 'sqlite_vm_instructions': instructions, 'rows': rows}

    def get(self, scope, identity):
        self.reads += 1
        row = self.db.execute('''SELECT id,title,content,created_at,revision FROM notes
            WHERE tenant=? AND owner=? AND id=?''', (scope.tenant, scope.owner, identity)).fetchone()
        if row is None:
            raise Missing('not found')
        return Note(**dict(row))

    def replace(self, scope, identity, revision, title):
        # This repository probe accepts trusted, already validated write inputs.
        with self.db:
            changed = self.db.execute('''UPDATE notes SET title=?,revision=revision+1
                WHERE tenant=? AND owner=? AND id=? AND revision=?''',
                (title, scope.tenant, scope.owner, identity, revision)).rowcount
            if not changed:
                self.get(scope, identity)
                raise Stale('revision changed')
        return self.get(scope, identity)

    def close(self):
        self.db.close()
