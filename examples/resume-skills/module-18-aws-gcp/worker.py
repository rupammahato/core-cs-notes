"""Teaching worker: injected token verifier, real HTTP and transactional SQLite."""
import json, sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from google.auth import exceptions
from google.oauth2 import id_token

class AuthenticationError(Exception):pass
class AuthorizationError(Exception):pass

class TokenVerifier:
    def __init__(self, request, audience, service_account):
        self.request=request
        self.audience=audience
        self.service_account=service_account

    def verify(self, authorization):
        if not authorization or not authorization.startswith('Bearer '):
            raise AuthenticationError('Bearer token required')
        token=authorization[7:]
        if not token or len(token)>8192:raise AuthenticationError('Invalid token length')
        try:
            claims=id_token.verify_oauth2_token(token,self.request,audience=self.audience,clock_skew_in_seconds=0)
        except (ValueError,exceptions.GoogleAuthError) as error:
            raise AuthenticationError('Token verification failed') from error
        if claims.get('email_verified') is not True or claims.get('email')!=self.service_account:
            raise AuthorizationError('Caller service account not allowed')
        return claims

class Store:
    def __init__(self,path):
        self.path=str(path)
        self.faults={}
        with closing(self.connect()) as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS jobs(
              tenant TEXT NOT NULL,id TEXT NOT NULL,value TEXT NOT NULL,
              state TEXT NOT NULL DEFAULT 'pending',PRIMARY KEY(tenant,id));
            CREATE TABLE IF NOT EXISTS effects(
              tenant TEXT NOT NULL,id TEXT NOT NULL,value TEXT NOT NULL,
              PRIMARY KEY(tenant,id),FOREIGN KEY(tenant,id) REFERENCES jobs(tenant,id));
            ''')

    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def seed(self,tenant,job,value):
        db=self.connect()
        try:
            with db:db.execute('INSERT INTO jobs(tenant,id,value) VALUES(?,?,?)',(tenant,job,value))
        finally:db.close()

    def apply(self,payload):
        if type(payload) is not dict or set(payload)!={'tenant_id','job_id','value'}:
            return 400,{'error':'invalid payload'}
        tenant,job,value=(payload[k] for k in ('tenant_id','job_id','value'))
        if not all(type(v) is str and 1<=len(v)<=80 for v in (tenant,job,value)):
            return 400,{'error':'invalid fields'}
        db=self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT value FROM jobs WHERE tenant=? AND id=?',(tenant,job)).fetchone()
            if row is None:return 404,{'error':'job not found'}
            if row[0]!=value:return 409,{'error':'job payload changed'}
            done=db.execute('SELECT value FROM effects WHERE tenant=? AND id=?',(tenant,job)).fetchone()
            if done:return 200,{'status':'replayed','job_id':job}
            # Faults are controlled by the verifier, never by request headers/body.
            fault=self.faults.pop((tenant,job),None)
            if fault=='before_commit':return 503,{'error':'injected pre-commit failure'}
            db.execute('INSERT INTO effects(tenant,id,value) VALUES(?,?,?)',(tenant,job,value))
            db.execute("UPDATE jobs SET state='complete' WHERE tenant=? AND id=?",(tenant,job))
            db.commit()
            if fault=='after_commit':return 503,{'error':'injected acknowledgement failure'}
            return 201,{'status':'applied','job_id':job}
        finally:
            if db.in_transaction:db.rollback()
            db.close()

    def effects(self):
        db=self.connect()
        try:return db.execute('SELECT tenant,id,value FROM effects ORDER BY tenant,id').fetchall()
        finally:db.close()

def make_server(store,verifier):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup();self.connection.settimeout(3)
        def log_message(self,*args):pass
        def reply(self,status,body):
            raw=json.dumps(body).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):self.reply(405,{'error':'POST required'})
        def do_POST(self):
            if self.path!='/tasks/import':return self.reply(404,{'error':'route not found'})
            try:verifier.verify(self.headers.get('Authorization'))
            except AuthenticationError:return self.reply(401,{'error':'unauthenticated'})
            except AuthorizationError:return self.reply(403,{'error':'caller forbidden'})
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError:return self.reply(400,{'error':'invalid length'})
            if not 0<length<=4096:return self.reply(413,{'error':'body length limit'})
            try:payload=json.loads(self.rfile.read(length))
            except (ValueError,OSError):return self.reply(400,{'error':'invalid JSON'})
            try:status,body=store.apply(payload)
            except sqlite3.OperationalError:return self.reply(503,{'error':'storage unavailable'})
            self.reply(status,body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=False
    return server
