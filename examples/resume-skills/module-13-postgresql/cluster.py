"""Provision only a newly created temporary PostgreSQL cluster, never a service."""
from contextlib import contextmanager
from pathlib import Path
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import psycopg
from psycopg import sql

OWNER='m13_owner'
OWNER_PASSWORD='public-local-admin-demo'
APP_PASSWORD='public-local-app-demo'

@contextmanager
def temporary_cluster():
    binary=Path(os.environ.get('M13_PG_BIN',r'C:/Program Files/PostgreSQL/18/bin'))
    suffix='.exe' if os.name=='nt' else ''
    base=Path(tempfile.gettempdir()).resolve()
    target=Path(tempfile.mkdtemp(prefix='placement-m13-',dir=base)).resolve()
    data=target/'data'
    log=target/'postgres.log'
    password=target/'initial-password.txt'
    password.write_text(OWNER_PASSWORD+'\n',encoding='utf-8')
    started=False
    process=None
    log_stream=None
    safe_to_remove=True
    evidence={'existing_service_touched':False}
    def command(name,args,timeout=60):
        result=subprocess.run([str(binary/(name+suffix)),*args],capture_output=True,
                              text=True,encoding='utf-8',timeout=timeout,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode:
            raise RuntimeError({'command':name,'stdout':result.stdout,'stderr':result.stderr})
        return result
    try:
        init=command('initdb',['-D',str(data),'-U',OWNER,'--pwfile',str(password),
                              '--auth-host=scram-sha-256','--auth-local=trust','--encoding=UTF8','--locale=C'])
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0))
            port=probe.getsockname()[1]
        with (data/'postgresql.conf').open('a',encoding='utf-8') as config:
            config.write("\nlisten_addresses='127.0.0.1'\nport="+str(port)+"\nmax_connections=30\nshared_buffers='32MB'\ndeadlock_timeout='100ms'\ntimezone='UTC'\nlog_min_messages=warning\n")
        safe_to_remove=False
        # Direct native launch avoids pg_ctl start's nested restricted-token creation on Windows.
        log_stream=log.open('wb')
        process=subprocess.Popen([str(binary/('postgres'+suffix)),'-D',str(data)],
                                 stdout=log_stream,stderr=subprocess.STDOUT,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        params={'host':'127.0.0.1','port':port,'dbname':'postgres','user':OWNER,
                'password':OWNER_PASSWORD,'sslmode':'disable','connect_timeout':5}
        deadline=time.monotonic()+15
        while True:
            if process.poll() is not None:
                safe_to_remove=True
                raise RuntimeError('Native PostgreSQL exited: '+log.read_text(encoding='utf-8',errors='replace'))
            try:
                ready=psycopg.connect(**params,autocommit=True)
                ready.close()
                started=True
                break
            except psycopg.OperationalError:
                if time.monotonic()>deadline: raise RuntimeError('PostgreSQL readiness deadline')
                time.sleep(0.05)
        with psycopg.connect(**params,autocommit=True) as conn:
            actual=Path(conn.execute("SELECT current_setting('data_directory')").fetchone()[0]).resolve()
            if actual!=data.resolve(): raise RuntimeError('Unexpected server data directory')
            version=conn.execute('SHOW server_version').fetchone()[0]
            conn.execute(sql.SQL('CREATE ROLE m13_app LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Literal(APP_PASSWORD)))
        evidence.update(port=port,server_version=version,isolated_data_directory_verified=True,
                        initdb_stdout=init.stdout,host_authentication='scram-sha-256',tls='disabled for loopback fixture')
        yield params,evidence
    finally:
        if started or (data/'postmaster.pid').exists():
            stop=command('pg_ctl',['-D',str(data),'-m','fast','-w','stop'])
            safe_to_remove=True
            evidence['stop_stdout']=stop.stdout
        if process is not None and process.poll() is None and safe_to_remove:
            process.wait(timeout=10)
        if log_stream is not None: log_stream.close()
        if log.exists(): evidence['server_log']=log.read_text(encoding='utf-8',errors='replace')
        if 'port' in evidence:
            with socket.socket() as probe:
                probe.settimeout(1)
                if probe.connect_ex(('127.0.0.1',evidence['port']))==0:
                    raise RuntimeError('Owned PostgreSQL listener did not stop')
            evidence['listener_stopped']=True
        if not safe_to_remove: raise RuntimeError('Cluster startup/stop incomplete; preserving files at '+str(target))
        if target.parent!=base or not target.name.startswith('placement-m13-'):
            raise RuntimeError('Refusing unexpected cleanup path')
        shutil.rmtree(target)
        evidence['temporary_cluster_removed']=not target.exists()
