"""Transactional external-ID upserts with explicit timestamp and patch semantics."""
from datetime import datetime, timezone
import json


def utc_timestamp(value, naive_offset=None):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValueError('Timestamp must be text')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        if naive_offset is None:
            raise ValueError('Naive timestamp requires an explicit source offset policy')
        parsed = parsed.replace(tzinfo=timezone(naive_offset))
    return parsed.astimezone(timezone.utc).isoformat()


def merge_patch(old, patch):
    result = dict(old)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_patch(result[key], value)
        else:
            # Arrays replace explicitly. Omitted fields survive; null is a stored value.
            result[key] = value
    return result


def initialize(db):
    db.executescript('''
        CREATE TABLE records (
            tenant TEXT NOT NULL, source TEXT NOT NULL, external_id TEXT NOT NULL,
            observed_at TEXT, payload TEXT NOT NULL,
            PRIMARY KEY(tenant,source,external_id)
        );
        CREATE UNIQUE INDEX dated_identity ON records(tenant,source,observed_at)
            WHERE observed_at IS NOT NULL;
    ''')


def sync_batch(db, tenant, source, rows, naive_offset=None):
    if not tenant or not source:
        raise ValueError('Tenant and source required')
    with db:
        for row in rows:
            identity = row.get('external_id')
            patch = row.get('patch')
            if not isinstance(identity, str) or not identity or not isinstance(patch, dict):
                raise ValueError('Stable external ID and object patch required')
            timestamp = utc_timestamp(row.get('timestamp'), naive_offset)
            old = db.execute('SELECT payload,observed_at FROM records WHERE tenant=? AND source=? AND external_id=?', (tenant, source, identity)).fetchone()
            if timestamp:
                other = db.execute('SELECT external_id FROM records WHERE tenant=? AND source=? AND observed_at=? AND external_id!=?', (tenant, source, timestamp, identity)).fetchone()
                if other:
                    raise ValueError('Conflicting external-ID/timestamp identities')
            payload = merge_patch(json.loads(old[0]) if old else {}, patch)
            retained_time = timestamp if timestamp is not None else old[1] if old else None
            db.execute('''INSERT INTO records VALUES (?,?,?,?,?)
                ON CONFLICT(tenant,source,external_id) DO UPDATE SET
                    observed_at=excluded.observed_at,payload=excluded.payload''',
                (tenant, source, identity, retained_time, json.dumps(payload, sort_keys=True)))
