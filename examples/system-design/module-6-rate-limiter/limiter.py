"""SQLite token-bucket authority. Local teaching fixture, not Redis emulation."""
from dataclasses import asdict, dataclass
import json
import sqlite3


class PolicyConflict(ValueError):
    pass


class StoreFull(RuntimeError):
    pass


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('integer outside lesson bounds')
    return value


@dataclass(frozen=True)
class Policy:
    capacity: int = 3
    rate: int = 1  # Whole tokens per second; balance uses milli-tokens.

    def __post_init__(self):
        integer(self.capacity, 1, 1000000)
        integer(self.rate, 1, 1000000)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    remaining: int
    retry_ms: int
    effective_ms: int

    def json(self):
        return asdict(self)


def scope_key(tenant, subject, route):
    parts = (tenant, subject, route)
    if any(type(part) is not str or not 1 <= len(part) <= 80
           or not part.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in part)
           for part in parts):
        raise ValueError('invalid canonical scope')
    # Tuple encoding avoids delimiter collisions; values come from trusted auth/routes.
    return json.dumps(parts, separators=(',', ':'))


class Store:
    def __init__(self, path, max_keys=128):
        self.max_keys = integer(max_keys, 1, 1000000)
        self.db = sqlite3.connect(path, isolation_level=None, timeout=0.2)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.executescript('''
            CREATE TABLE IF NOT EXISTS buckets(
                scope TEXT PRIMARY KEY,
                capacity INTEGER NOT NULL,
                rate INTEGER NOT NULL,
                credit INTEGER NOT NULL CHECK(credit >= 0),
                last_ms INTEGER NOT NULL,
                expires_ms INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS bucket_expiry ON buckets(expires_ms);
            ''')
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def decide(self, tenant, subject, route, policy, now_ms, cost=1):
        key = scope_key(tenant, subject, route)
        integer(now_ms, 0, 10**15)
        integer(cost, 1, policy.capacity)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            # Recreating an idle bucket is safe only after it would be fully refilled.
            self.db.execute('DELETE FROM buckets WHERE expires_ms <= ?', (now_ms,))
            row = self.db.execute('SELECT * FROM buckets WHERE scope=?', (key,)).fetchone()
            if row and (row['capacity'], row['rate']) != (policy.capacity, policy.rate):
                raise PolicyConflict('explicit policy migration required')
            if row is None:
                count = self.db.execute('SELECT count(*) FROM buckets').fetchone()[0]
                if count >= self.max_keys:
                    raise StoreFull('active scope cap reached')
                credit, effective = policy.capacity * 1000, now_ms
            else:
                effective = max(now_ms, row['last_ms'])
                # Clamp elapsed before multiplication; no unbounded balance or FP drift.
                elapsed = min(effective - row['last_ms'],
                              (policy.capacity * 1000 + policy.rate - 1) // policy.rate)
                credit = min(policy.capacity * 1000, row['credit'] + elapsed * policy.rate)
            needed = cost * 1000
            allowed = credit >= needed
            if allowed:
                credit -= needed
            wait = 0 if allowed else (needed - credit + policy.rate - 1) // policy.rate
            # Clock rollback can freeze refill until the stored high-water time.
            retry = wait + max(0, effective - now_ms) if not allowed else 0
            idle = (policy.capacity * 1000 + policy.rate - 1) // policy.rate
            self.db.execute('''INSERT INTO buckets VALUES(?,?,?,?,?,?)
                ON CONFLICT(scope) DO UPDATE SET credit=excluded.credit,
                last_ms=excluded.last_ms, expires_ms=excluded.expires_ms''',
                (key, policy.capacity, policy.rate, credit, effective, effective + idle))
            self.db.execute('COMMIT')
            return Decision(allowed, credit // 1000, retry, effective)
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
