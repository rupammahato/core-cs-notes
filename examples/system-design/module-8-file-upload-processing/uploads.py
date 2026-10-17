"""Local metadata authority plus immutable object store and fenced processing."""
from contextlib import contextmanager
import base64
import hashlib
import hmac
import json
import re
import sqlite3
import uuid
from objects import Objects


class Error(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


def identity(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
        raise Error(400, 'invalid_identity')
    return value


def milliseconds(now):
    if type(now) is not int or not 0 <= now <= 10**15:
        raise Error(400, 'invalid_server_time')
    return now


class Uploads:
    def __init__(self, database, root, secret):
        self.objects, self.secret = Objects(root), secret
        self.db = sqlite3.connect(database, isolation_level=None, timeout=0.3)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.executescript('''CREATE TABLE IF NOT EXISTS uploads(
                id TEXT PRIMARY KEY, tenant TEXT, owner TEXT, operation TEXT,
                name TEXT, size INTEGER, digest TEXT, expires INTEGER,
                state TEXT, result_key TEXT, reason TEXT,
                UNIQUE(tenant,owner,operation));
                CREATE INDEX IF NOT EXISTS upload_expiry ON uploads(state,expires);
                CREATE TABLE IF NOT EXISTS jobs(
                    id TEXT PRIMARY KEY REFERENCES uploads(id), state TEXT, attempts INTEGER,
                    token TEXT, until_ms INTEGER);
                PRAGMA foreign_keys=ON;''')
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

    def owned(self, tenant, owner, file_id):
        for value in (tenant, owner, file_id):
            identity(value)
        row = self.db.execute('SELECT * FROM uploads WHERE tenant=? AND owner=? AND id=?',
                              (tenant, owner, file_id)).fetchone()
        if row is None:
            raise Error(404, 'not_found')
        return row

    def capability(self, row):
        raw = json.dumps([row[key] for key in ('id','tenant','owner','size','digest','expires')], separators=(',', ':')).encode()
        payload = base64.urlsafe_b64encode(raw).decode()
        signature = hmac.new(self.secret, b'PUT\n'+payload.encode(), hashlib.sha256).hexdigest()
        return payload+'.'+signature

    def create(self, tenant, owner, operation, data, now):
        for value in (tenant, owner, operation):
            identity(value)
        milliseconds(now)
        if (type(data) is not dict or set(data) != {'name','size','sha256','mime'}
            or type(data['name']) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,70}\.txt', data['name'])
            or '..' in data['name'] or data['mime'] != 'text/plain'
            or type(data['size']) is not int or not 1 <= data['size'] <= 1024
            or type(data['sha256']) is not str or not re.fullmatch(r'[a-f0-9]{64}', data['sha256'])):
            raise Error(400, 'invalid_upload_contract')
        with self.transaction():
            row = self.db.execute('SELECT * FROM uploads WHERE tenant=? AND owner=? AND operation=?',
                                  (tenant, owner, operation)).fetchone()
            replay = row is not None
            if row:
                if (row['name'],row['size'],row['digest']) != (data['name'],data['size'],data['sha256']):
                    raise Error(409, 'changed_create_intent')
            else:
                if self.db.execute('SELECT count(*) FROM uploads').fetchone()[0] >= 128:
                    raise Error(503, 'lesson_metadata_cap')
                file_id = uuid.uuid4().hex
                self.db.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                    (file_id,tenant,owner,operation,data['name'],data['size'],data['sha256'],now+10000,'uploading',None,None))
                row = self.owned(tenant, owner, file_id)
            return {'id':row['id'], 'expires_ms':row['expires'],
                    'upload_path':'/objects/'+row['id'], 'capability':self.capability(row), 'replay':replay}

    def upload(self, file_id, capability, raw, now):
        identity(file_id)
        milliseconds(now)
        with self.transaction():
            row = self.db.execute('SELECT * FROM uploads WHERE id=?', (file_id,)).fetchone()
            if (row is None or type(capability) is not str or not capability.isascii()
                or len(capability)>2048 or not hmac.compare_digest(self.capability(row), capability)):
                raise Error(403, 'invalid_upload_capability')
            if row['state'] in ('deleted','expired') or now >= row['expires']:
                raise Error(410, 'upload_expired_or_deleted')
            if row['state'] != 'uploading':
                raise Error(409, 'upload_already_completed')
            if type(raw) is not bytes or len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['digest']:
                raise Error(422, 'size_or_checksum_mismatch')
            return self.objects.put('raw', row['id'], raw)

    def complete(self, tenant, owner, file_id, now):
        milliseconds(now)
        with self.transaction():
            row = self.owned(tenant, owner, file_id)
            if row['state'] in ('deleted','expired'):
                raise Error(410, 'gone')
            if row['state'] in ('quarantined','processing','ready'):
                return row['state']
            if row['state'] != 'uploading':
                raise Error(409, 'terminal_processing_result')
            if now >= row['expires']:
                raise Error(410, 'upload_window_expired')
            try:
                raw = self.objects.read('raw', row['id'])
            except FileNotFoundError:
                raise Error(409, 'object_missing') from None
            if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['digest']:
                raise Error(422, 'stored_object_mismatch')
            self.db.execute("UPDATE uploads SET state='quarantined' WHERE id=?", (file_id,))
            self.db.execute("INSERT INTO jobs VALUES(?,'pending',0,NULL,0)", (file_id,))
            return 'quarantined'

    def claim(self, now):
        milliseconds(now)
        with self.transaction():
            self.db.execute("UPDATE uploads SET state='failed',reason='attempts_exhausted' WHERE id IN (SELECT id FROM jobs WHERE state='inflight' AND until_ms<=? AND attempts>=3) AND state='processing'", (now,))
            self.db.execute("UPDATE jobs SET state='failed',token=NULL WHERE state='inflight' AND until_ms<=? AND attempts>=3", (now,))
            row = self.db.execute('''SELECT u.*,j.attempts FROM jobs j JOIN uploads u ON u.id=j.id
                WHERE j.attempts<3 AND (j.state='pending' OR (j.state='inflight' AND j.until_ms<=?))
                AND u.state IN ('quarantined','processing') ORDER BY u.id LIMIT 1''', (now,)).fetchone()
            if row is None:
                return None
            job = dict(row)
            job.update(token=uuid.uuid4().hex, until_ms=now+2000, attempts=row['attempts']+1)
            self.db.execute("UPDATE jobs SET state='inflight',attempts=?,token=?,until_ms=? WHERE id=?",
                            (job['attempts'],job['token'],job['until_ms'],job['id']))
            self.db.execute("UPDATE uploads SET state='processing' WHERE id=?", (job['id'],))
            return job

    def inspect_content(self, job):
        # Deterministic text policy, NOT antivirus or a safe general document parser.
        raw = self.objects.read('raw', job['id'])
        if len(raw) != job['size'] or hashlib.sha256(raw).hexdigest() != job['digest']:
            return None, 'stored_object_mismatch'
        try:
            text = raw.decode('utf-8')
        except UnicodeError:
            return None, 'unsupported_utf8'
        if '\x00' in text or '[BLOCKED]' in text:
            return None, 'lesson_content_policy'
        result = json.dumps({'characters':len(text), 'lines':len(text.splitlines()),
                             'source_sha256':job['digest']}, sort_keys=True).encode()
        return result, None

    def publish(self, job, result, reason, now):
        milliseconds(now)
        with self.transaction():
            current = self.db.execute('SELECT u.state,j.token,j.until_ms FROM uploads u JOIN jobs j ON j.id=u.id WHERE u.id=?', (job['id'],)).fetchone()
            if not current or current['state'] != 'processing' or current['token'] != job['token'] or current['until_ms'] <= now:
                return False
            key = None
            if reason is None:
                key = job['id']+'.'+job['token']
                self.objects.put('derived', key, result)
            self.db.execute('UPDATE uploads SET state=?,result_key=?,reason=? WHERE id=?',
                            ('ready' if reason is None else 'rejected',key,reason,job['id']))
            self.db.execute("UPDATE jobs SET state='succeeded',token=NULL WHERE id=?", (job['id'],))
            return True

    def delete(self, tenant, owner, file_id):
        with self.transaction():
            self.owned(tenant, owner, file_id)
            self.db.execute("UPDATE uploads SET state='deleted',result_key=NULL WHERE id=?", (file_id,))
            self.db.execute("UPDATE jobs SET state='cancelled',token=NULL WHERE id=?", (file_id,))

    def download(self, tenant, owner, file_id):
        with self.transaction():
            row = self.owned(tenant, owner, file_id)
            if row['state'] in ('deleted','expired'):
                raise Error(410, 'gone')
            if row['state'] != 'ready':
                raise Error(409, 'not_ready')
            try:
                raw = self.objects.read('raw', file_id)
            except (FileNotFoundError,ValueError):
                raise Error(503, 'ready_object_missing_or_corrupt') from None
            if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['digest']:
                raise Error(503, 'ready_object_missing_or_corrupt')
            return raw

    def cleanup(self, now):
        milliseconds(now)
        removed = 0
        # Every legitimate object write/publish also holds this DB write authority.
        with self.transaction():
            self.db.execute("UPDATE uploads SET state='expired' WHERE state='uploading' AND expires<=?", (now,))
            live = {row['id']:row for row in self.db.execute("SELECT * FROM uploads WHERE state NOT IN ('deleted','expired')")}
            for area, file in self.objects.inventory():
                key = file.name
                keep = (key in live if area == 'raw' else any(row['state'] == 'ready' and row['result_key'] == key for row in live.values()))
                if not keep:
                    self.objects.remove_owned(area, file)
                    removed += 1
        return removed
