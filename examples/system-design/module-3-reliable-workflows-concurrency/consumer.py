"""Separate durable inbox and local projection effect; no external provider involved."""
import json
import sqlite3
from workflow import Conflict, canonical, fingerprint, identifiers


class Consumer:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS inbox (
            tenant TEXT NOT NULL,event_id TEXT NOT NULL,fingerprint TEXT NOT NULL,
            PRIMARY KEY(tenant,event_id)
          ) STRICT;
          CREATE TABLE IF NOT EXISTS projection (
            tenant TEXT NOT NULL,note_id TEXT NOT NULL,owner TEXT NOT NULL,
            title TEXT NOT NULL,revision INTEGER NOT NULL CHECK(revision>0),
            PRIMARY KEY(tenant,note_id)
          ) STRICT;
        ''')

    def accept(self, raw, fail_after_effect=False):
        event = json.loads(raw)
        fields = {'type', 'schema', 'tenant', 'owner', 'event_id', 'note_id', 'title', 'revision'}
        if type(event) is not dict or set(event) != fields or event['type'] != 'NoteCreated':
            raise ValueError('unsupported event contract')
        if type(event['schema']) is not int or event['schema'] != 1 or type(event['revision']) is not int or event['revision'] != 1:
            raise ValueError('unsupported schema or revision')
        identifiers(event['tenant'], event['owner'], event['event_id'], event['note_id'])
        if type(event['title']) is not str or not event['title'].strip() or '\0' in event['title'] or len(event['title'])>120:
            raise ValueError('invalid title')
        digest = fingerprint(event)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old = self.db.execute('SELECT fingerprint FROM inbox WHERE tenant=? AND event_id=?',
                                  (event['tenant'], event['event_id'])).fetchone()
            if old:
                if old['fingerprint'] != digest:
                    raise Conflict('event identity reused with different payload')
                replayed = True
            else:
                self.db.execute('INSERT INTO inbox VALUES(?,?,?)', (event['tenant'], event['event_id'], digest))
                self.db.execute('INSERT INTO projection VALUES(?,?,?,?,?)',
                    (event['tenant'], event['note_id'], event['owner'], event['title'], event['revision']))
                if fail_after_effect:
                    raise RuntimeError('owned fault after consumer effect')
                replayed = False
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
        return {'event_id': event['event_id'], 'replayed': replayed}

    def close(self):
        self.db.close()
