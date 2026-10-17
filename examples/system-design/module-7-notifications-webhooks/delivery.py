"""Durable local event fan-out and leased delivery queue; one SQLite authority."""
from contextlib import contextmanager
import json
import re
import sqlite3
import uuid


class Conflict(ValueError):
    pass


def identity(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
        raise ValueError('invalid lesson identity')
    return value


def clock(value):
    if type(value) is not int or not 0 <= value <= 10**15:
        raise ValueError('invalid server milliseconds')
    return value


def envelope(tenant, event_id, message):
    identity(tenant)
    identity(event_id)
    if type(message) is not str or not 1 <= len(message) <= 200:
        raise ValueError('message must contain 1..200 characters')
    return json.dumps({'version': 1, 'tenant': tenant, 'event_id': event_id,
                       'type': 'practice.reminder', 'message': message},
                      sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


class Queue:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=0.3, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.executescript('''
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS subscriptions(
                    tenant TEXT, id TEXT, endpoint TEXT, enabled INTEGER NOT NULL,
                    PRIMARY KEY(tenant,id));
                CREATE TABLE IF NOT EXISTS events(
                    tenant TEXT, id TEXT, body BLOB NOT NULL, PRIMARY KEY(tenant,id));
                CREATE TABLE IF NOT EXISTS deliveries(
                    id TEXT PRIMARY KEY, tenant TEXT, event_id TEXT, subscription TEXT,
                    status TEXT NOT NULL CHECK(status IN ('pending','inflight','succeeded','failed','skipped')),
                    due INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    lease_until INTEGER NOT NULL DEFAULT 0, token TEXT, reason TEXT,
                    UNIQUE(tenant,event_id,subscription),
                    FOREIGN KEY(tenant,event_id) REFERENCES events(tenant,id),
                    FOREIGN KEY(tenant,subscription) REFERENCES subscriptions(tenant,id));
                CREATE INDEX IF NOT EXISTS delivery_due ON deliveries(status,due,lease_until);
                CREATE TABLE IF NOT EXISTS attempts(
                    delivery TEXT, number INTEGER, token TEXT NOT NULL, started INTEGER,
                    outcome TEXT, PRIMARY KEY(delivery,number));
                CREATE TABLE IF NOT EXISTS cooldowns(
                    tenant TEXT, endpoint TEXT, until_ms INTEGER, PRIMARY KEY(tenant,endpoint));
            ''')
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def subscribe(self, tenant, subscription, endpoint, enabled=True):
        for value in (tenant, subscription, endpoint):
            identity(value)
        if type(enabled) is not bool:
            raise ValueError('enabled must be boolean')
        with self.transaction():
            old = self.db.execute('SELECT endpoint FROM subscriptions WHERE tenant=? AND id=?',
                                  (tenant, subscription)).fetchone()
            if old and old['endpoint'] != endpoint:
                raise Conflict('endpoint immutable in this lesson')
            count = self.db.execute('SELECT count(*) FROM subscriptions WHERE tenant=?', (tenant,)).fetchone()[0]
            if not old and count >= 8:
                raise ValueError('eight subscriptions per lesson tenant')
            self.db.execute('INSERT INTO subscriptions VALUES(?,?,?,?) ON CONFLICT(tenant,id) DO UPDATE SET enabled=excluded.enabled',
                            (tenant, subscription, endpoint, int(enabled)))

    def enqueue(self, tenant, event_id, message, now):
        body = envelope(tenant, event_id, message)
        clock(now)
        with self.transaction():
            old = self.db.execute('SELECT body FROM events WHERE tenant=? AND id=?', (tenant, event_id)).fetchone()
            if old:
                if old['body'] != body:
                    raise Conflict('event ID reused with different content')
                return False  # Stable replay: do not fan out to newly added subscribers.
            if self.db.execute('SELECT count(*) FROM events').fetchone()[0] >= 256:
                raise ValueError('lesson event retention cap reached')
            self.db.execute('INSERT INTO events VALUES(?,?,?)', (tenant, event_id, body))
            for row in self.db.execute('SELECT id FROM subscriptions WHERE tenant=? AND enabled=1', (tenant,)):
                self.db.execute('INSERT INTO deliveries(id,tenant,event_id,subscription,status,due) VALUES(?,?,?,?,?,?)',
                                (uuid.uuid4().hex, tenant, event_id, row['id'], 'pending', now))
            return True

    def claim(self, now, lease_ms=2000):
        clock(now)
        if type(lease_ms) is not int or not 1 <= lease_ms <= 60000:
            raise ValueError('invalid lease')
        with self.transaction():
            # Count a crashed claim as an attempt; preserve its ambiguous outcome.
            self.db.execute("UPDATE attempts SET outcome='lease_expired' WHERE outcome IS NULL AND delivery IN (SELECT id FROM deliveries WHERE status='inflight' AND lease_until<=?)", (now,))
            self.db.execute("UPDATE deliveries SET status='failed',reason='attempts_exhausted' WHERE status='inflight' AND lease_until<=? AND attempts>=3", (now,))
            self.db.execute('''UPDATE deliveries SET status='skipped',reason='opted_out'
                WHERE (status='pending' OR (status='inflight' AND lease_until<=?))
                AND EXISTS(SELECT 1 FROM subscriptions s WHERE s.tenant=deliveries.tenant
                    AND s.id=deliveries.subscription AND s.enabled=0)''', (now,))
            row = self.db.execute('''SELECT d.*,s.endpoint,e.body FROM deliveries d
                JOIN subscriptions s ON s.tenant=d.tenant AND s.id=d.subscription
                JOIN events e ON e.tenant=d.tenant AND e.id=d.event_id
                LEFT JOIN cooldowns c ON c.tenant=d.tenant AND c.endpoint=s.endpoint
                WHERE d.attempts<3 AND d.due<=? AND s.enabled=1
                    AND (d.status='pending' OR (d.status='inflight' AND d.lease_until<=?))
                    AND coalesce(c.until_ms,0)<=? ORDER BY d.due,d.id LIMIT 1''', (now, now, now)).fetchone()
            if row is None:
                return None
            job = dict(row)
            job.update(token=uuid.uuid4().hex, attempts=row['attempts']+1, lease_until=now+lease_ms)
            self.db.execute("UPDATE deliveries SET status='inflight',attempts=?,lease_until=?,token=? WHERE id=?",
                            (job['attempts'], job['lease_until'], job['token'], job['id']))
            self.db.execute('INSERT INTO attempts VALUES(?,?,?,?,NULL)', (job['id'], job['attempts'], job['token'], now))
            return job

    def finish(self, job, status, now, jitter_ms, retry_after_ms=0):
        clock(now)
        if status is not None and (type(status) is not int or not 100 <= status <= 599):
            raise ValueError('invalid transport status')
        cap = min(8000, 500 * 2**(job['attempts']-1))
        if type(jitter_ms) is not int or not 0 <= jitter_ms <= cap:
            raise ValueError('jitter outside attempt cap')
        if type(retry_after_ms) is not int or not 0 <= retry_after_ms <= 86400000:
            raise ValueError('retry hint outside lesson policy')
        with self.transaction():
            current = self.db.execute("SELECT token,lease_until FROM deliveries WHERE id=? AND status='inflight'", (job['id'],)).fetchone()
            if not current or current['token'] != job['token'] or current['lease_until'] <= now:
                return False  # Fence local state; cannot undo an external HTTP effect.
            retryable = status is None or status in (408, 429) or status >= 500
            if status is not None and 200 <= status < 300:
                state, reason = 'succeeded', 'endpoint_accepted'
            elif retryable and job['attempts'] < 3:
                state, reason = 'pending', 'retry_scheduled'
            else:
                state, reason = 'failed', 'attempts_exhausted' if retryable else 'permanent_response'
            due = now + max(jitter_ms, retry_after_ms)
            if status == 429:
                self.db.execute('''INSERT INTO cooldowns VALUES(?,?,?)
                    ON CONFLICT(tenant,endpoint) DO UPDATE SET until_ms=max(until_ms,excluded.until_ms)''',
                    (job['tenant'], job['endpoint'], due))
            self.db.execute('UPDATE deliveries SET status=?,reason=?,due=?,token=NULL,lease_until=0 WHERE id=?',
                            (state, reason, due, job['id']))
            self.db.execute('UPDATE attempts SET outcome=? WHERE delivery=? AND number=? AND token=?',
                            (str(status) if status is not None else 'transport_unknown', job['id'], job['attempts'], job['token']))
            return True

    def inspect(self, tenant, delivery_id):
        return self.db.execute('SELECT * FROM deliveries WHERE tenant=? AND id=?', (identity(tenant), identity(delivery_id))).fetchone()
