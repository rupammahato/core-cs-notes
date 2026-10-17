from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from threading import Event,Thread
import json,os,signal,socket
import psycopg
from psycopg_pool import ConnectionPool,PoolTimeout
from psycopg.conninfo import make_conninfo

def start():
    password=Path(os.environ['DB_PASSWORD_FILE']).read_text().strip()
    info=make_conninfo(host=os.environ['DB_HOST'],dbname=os.environ['DB_NAME'],user=os.environ['DB_USER'],
        password=password,port=5432,connect_timeout=1,options='-c statement_timeout=1500',application_name='m16-api')
    pool=ConnectionPool(info,min_size=1,max_size=2,timeout=0.5,max_waiting=4,kwargs={'autocommit':True},open=False)
    pool.open();pool.wait(timeout=10)
    stopped=Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,format,*args):pass
        def send_json(self,status,data):
            body=json.dumps(data).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            if self.path=='/live':return self.send_json(200,{'status':'live'})
            if self.path=='/':return self.send_json(200,{'service':'module-16','message':os.getenv('APP_MESSAGE','docker-lesson'),'hostname':socket.gethostname(),'uid':os.getuid()})
            try:
                with pool.connection() as conn:
                    if self.path=='/ready':
                        conn.execute('SELECT 1').fetchone();return self.send_json(200,{'status':'ready'})
                    if self.path=='/items':
                        rows=conn.execute('SELECT id,value FROM lesson.items ORDER BY id').fetchall()
                        return self.send_json(200,{'items':[{'id':row[0],'value':row[1]} for row in rows]})
            except (psycopg.Error,PoolTimeout):return self.send_json(503,{'error':'database_unavailable'})
            return self.send_json(404,{'error':'not_found'})
        def do_POST(self):
            if self.path!='/items':return self.send_json(404,{'error':'not_found'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 1<=length<=2048:raise ValueError('body size')
                payload=json.loads(self.rfile.read(length))
                if type(payload) is not dict:raise ValueError('object required')
                key,value=payload.get('request_key'),payload.get('value')
                if type(key) is not str or type(value) is not str or not 1<=len(key)<=80 or not 1<=len(value)<=80:
                    raise ValueError('invalid strings')
            except (ValueError,UnicodeError):return self.send_json(400,{'error':'invalid_input'})
            try:
                with pool.connection() as conn:
                    with conn.transaction():
                        row=conn.execute('INSERT INTO lesson.items(request_key,value) VALUES(%s,%s) ON CONFLICT(request_key) DO NOTHING RETURNING id,value',(key,value)).fetchone()
                        replayed=row is None
                        if replayed:
                            row=conn.execute('SELECT id,value FROM lesson.items WHERE request_key=%s',(key,)).fetchone()
                            if row[1]!=value:return self.send_json(409,{'error':'idempotency_conflict'})
                    return self.send_json(200 if replayed else 201,{'id':row[0],'value':row[1],'replayed':replayed})
            except (psycopg.Error,PoolTimeout):return self.send_json(503,{'error':'database_unavailable'})
    server=ThreadingHTTPServer(('0.0.0.0',8080),Handler)
    server.daemon_threads=False  # server_close waits for owned request threads.
    server.block_on_close=True
    for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,lambda *_:stopped.set())
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    print(json.dumps({'event':'started','uid':os.getuid()}),flush=True)
    try:stopped.wait()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);pool.close()
        print(json.dumps({'event':'shutdown_complete'}),flush=True)

if __name__=='__main__':start()
