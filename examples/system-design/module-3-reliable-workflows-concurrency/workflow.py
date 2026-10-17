"""Local durable operations/outbox/leases and scarce-stock transitions using SQLite."""
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4
import json
import math
import re
import sqlite3


class Conflict(Exception):
    pass


class Missing(Exception):
    pass


class Unavailable(Exception):
    pass


def identifiers(*values):
    if not all(type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) for value in values):
        raise ValueError('invalid identifier')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def fingerprint(value):
    return sha256(canonical(value).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Claim:
    tenant: str
    event_id: str
    worker: str
    generation: int
    payload: str
    lease_until: float
    attempt: int


class Workflow:
    def __init__(self, path, id_factory=lambda: str(uuid4())):
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.id_factory = id_factory
        self.db.executescript('''PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS notes (
            tenant TEXT NOT NULL, owner TEXT NOT NULL, id TEXT NOT NULL,
            title TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
            PRIMARY KEY(tenant,id)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS operations (
            tenant TEXT NOT NULL, owner TEXT NOT NULL, key TEXT NOT NULL,
            kind TEXT NOT NULL, fingerprint TEXT NOT NULL, response TEXT NOT NULL,
            PRIMARY KEY(tenant,owner,key)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS outbox (
            tenant TEXT NOT NULL, event_id TEXT NOT NULL, note_id TEXT NOT NULL,
            payload TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('ready','leased','done','dead')),
            due REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3, generation INTEGER NOT NULL DEFAULT 0,
            worker TEXT, lease_until REAL, PRIMARY KEY(tenant,event_id),
            FOREIGN KEY(tenant,note_id) REFERENCES notes(tenant,id)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS stock (
            tenant TEXT NOT NULL, item TEXT NOT NULL, remaining INTEGER NOT NULL CHECK(remaining>=0),
            PRIMARY KEY(tenant,item)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS reservations (
            tenant TEXT NOT NULL, id TEXT NOT NULL, owner TEXT NOT NULL, item TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity>0), state TEXT NOT NULL CHECK(state IN ('active','released')),
            PRIMARY KEY(tenant,id), FOREIGN KEY(tenant,item) REFERENCES stock(tenant,item)
          ) STRICT;''')

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def operation(self, tenant, owner, key, kind, request, action):
        identifiers(tenant, owner, key)
        digest = fingerprint([kind, 1, request])
        with self.transaction():
            old = self.db.execute('SELECT * FROM operations WHERE tenant=? AND owner=? AND key=?',
                                  (tenant, owner, key)).fetchone()
            if old:
                if old['kind'] != kind or old['fingerprint'] != digest:
                    raise Conflict('operation key reused with different intent')
                return json.loads(old['response']), True
            result = action()
            self.db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?)',
                            (tenant, owner, key, kind, digest, canonical(result)))
        return result, False

    def create_note(self, tenant, owner, key, title, fail_after_note=False):
        if type(title) is not str or not title.strip() or '\0' in title or len(title)>120:
            raise ValueError('invalid title')

        def action():
            note_id, event_id = self.id_factory(), self.id_factory()
            identifiers(note_id, event_id)
            self.db.execute('INSERT INTO notes VALUES(?,?,?,?,1)', (tenant, owner, note_id, title))
            if fail_after_note:
                raise RuntimeError('owned fault after note insertion')
            event = {'type': 'NoteCreated', 'schema': 1, 'tenant': tenant, 'owner': owner,
                     'event_id': event_id, 'note_id': note_id, 'title': title, 'revision': 1}
            self.db.execute('''INSERT INTO outbox(tenant,event_id,note_id,payload,state,due)
                               VALUES(?,?,?,?,'ready',0)''', (tenant, event_id, note_id, canonical(event)))
            return {'id': note_id, 'title': title, 'revision': 1}

        return self.operation(tenant, owner, key, 'create_note', {'title': title}, action)

    def claim(self, worker, now, lease=5):
        identifiers(worker)
        if not math.isfinite(now) or not math.isfinite(lease) or lease<=0:
            raise ValueError('finite clock and positive lease required')
        with self.transaction():
            self.db.execute('''UPDATE outbox SET state='dead',worker=NULL,lease_until=NULL
                WHERE state='leased' AND lease_until<=? AND attempts>=max_attempts''', (now,))
            row = self.db.execute('''SELECT * FROM outbox WHERE attempts<max_attempts AND
                ((state='ready' AND due<=?) OR (state='leased' AND lease_until<=?))
                ORDER BY due,tenant,event_id LIMIT 1''', (now, now)).fetchone()
            if row is None:
                return None
            generation, attempt = row['generation']+1, row['attempts']+1
            self.db.execute('''UPDATE outbox SET state='leased',worker=?,lease_until=?,
                generation=?,attempts=? WHERE tenant=? AND event_id=?''',
                (worker, now+lease, generation, attempt, row['tenant'], row['event_id']))
            return Claim(row['tenant'], row['event_id'], worker, generation, row['payload'], now+lease, attempt)

    def acknowledge(self, claim, now):
        if not math.isfinite(now):
            raise ValueError('finite clock required')
        with self.transaction():
            return self.db.execute('''UPDATE outbox SET state='done',worker=NULL,lease_until=NULL
                WHERE tenant=? AND event_id=? AND state='leased' AND worker=?
                AND generation=? AND lease_until>?''',
                (claim.tenant, claim.event_id, claim.worker, claim.generation, now)).rowcount == 1

    def fail(self, claim, now, delay=1):
        if not math.isfinite(now) or not math.isfinite(delay) or delay<0:
            raise ValueError('finite time and nonnegative retry delay required')
        with self.transaction():
            return self.db.execute('''UPDATE outbox SET state=CASE WHEN attempts>=max_attempts
                THEN 'dead' ELSE 'ready' END,due=?,worker=NULL,lease_until=NULL
                WHERE tenant=? AND event_id=? AND state='leased' AND worker=?
                AND generation=? AND lease_until>?''',
                (now+delay, claim.tenant, claim.event_id, claim.worker, claim.generation, now)).rowcount == 1

    def reserve(self, tenant, owner, key, item, quantity=1, fail_after_decrement=False):
        identifiers(item)
        if type(quantity) is not int or not 1 <= quantity <= 100:
            raise ValueError('quantity must be 1..100')

        def action():
            changed = self.db.execute('''UPDATE stock SET remaining=remaining-?
                WHERE tenant=? AND item=? AND remaining>=?''', (quantity, tenant, item, quantity)).rowcount
            if not changed:
                raise Unavailable('stock unavailable')
            if fail_after_decrement:
                raise RuntimeError('owned fault after stock decrement')
            identity = self.id_factory()
            identifiers(identity)
            self.db.execute("INSERT INTO reservations VALUES(?,?,?,?,?,'active')", (tenant, identity, owner, item, quantity))
            return {'reservation_id': identity, 'item': item, 'quantity': quantity}

        return self.operation(tenant, owner, key, 'reserve', {'item': item, 'quantity': quantity}, action)

    def release(self, tenant, owner, key, reservation_id):
        identifiers(reservation_id)

        def action():
            row = self.db.execute('SELECT * FROM reservations WHERE tenant=? AND owner=? AND id=?',
                                  (tenant, owner, reservation_id)).fetchone()
            if row is None:
                raise Missing('reservation not found')
            if row['state'] == 'active':
                self.db.execute("UPDATE reservations SET state='released' WHERE tenant=? AND id=?", (tenant, reservation_id))
                self.db.execute('UPDATE stock SET remaining=remaining+? WHERE tenant=? AND item=?',
                                (row['quantity'], tenant, row['item']))
            return {'reservation_id': reservation_id, 'state': 'released'}

        return self.operation(tenant, owner, key, 'release', {'reservation_id': reservation_id}, action)

    def close(self):
        self.db.close()
