"""Own one new loopback replica-set process; never connect to a Windows service."""
from contextlib import contextmanager
from pathlib import Path
import os,socket,subprocess,tempfile,time,shutil
from pymongo import MongoClient
from pymongo.errors import AutoReconnect,ConnectionFailure,ServerSelectionTimeoutError

@contextmanager
def temporary_cluster():
    base=Path(tempfile.gettempdir()).resolve()
    target=Path(tempfile.mkdtemp(prefix='placement-m14-',dir=base)).resolve()
    data=target/'data'; data.mkdir()
    log=target/'mongod.log'
    binary=Path(os.environ.get('M14_MONGOD',r'C:/Program Files/MongoDB/Server/7.0/bin/mongod.exe'))
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0)); port=probe.getsockname()[1]
    uri=f'mongodb://127.0.0.1:{port}/?directConnection=true&replicaSet=m14_fixture'
    process=None; bootstrap=None; verified=False
    evidence={'port':port,'existing_service_touched':False,'authentication':'disabled for owned loopback fixture','tls':False,'replica_set_members':1}
    try:
        process=subprocess.Popen([str(binary),'--dbpath',str(data),'--port',str(port),
            '--bind_ip','127.0.0.1','--replSet','m14_fixture','--wiredTigerCacheSizeGB','0.25',
            '--logpath',str(log),'--logappend'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        bootstrap=MongoClient(f'mongodb://127.0.0.1:{port}/?directConnection=true',
            serverSelectionTimeoutMS=500,connectTimeoutMS=500,socketTimeoutMS=3000)
        deadline=time.monotonic()+20
        while True:
            if process.poll() is not None: raise RuntimeError('Owned mongod exited during startup')
            try: bootstrap.admin.command('ping'); break
            except (ConnectionFailure,ServerSelectionTimeoutError):
                if time.monotonic()>deadline: raise RuntimeError('MongoDB startup deadline')
                time.sleep(0.05)
        options=bootstrap.admin.command('getCmdLineOpts')['parsed']
        if Path(options['storage']['dbPath']).resolve()!=data.resolve() or options['net']['port']!=port:
            raise RuntimeError('Unexpected MongoDB target')
        verified=True
        bootstrap.admin.command({'replSetInitiate':{'_id':'m14_fixture','members':[{'_id':0,'host':f'127.0.0.1:{port}'}]}})
        deadline=time.monotonic()+25
        while not bootstrap.admin.command('hello').get('isWritablePrimary'):
            if time.monotonic()>deadline: raise RuntimeError('Primary election deadline')
            time.sleep(0.05)
        evidence.update(server_version=bootstrap.server_info()['version'],owned_dbpath_verified=True,
                        writable_primary=True,storage_engine=bootstrap.admin.command('serverStatus')['storageEngine']['name'])
        yield uri,evidence
    finally:
        if process is not None and process.poll() is None:
            if verified and bootstrap is not None:
                try: bootstrap.admin.command({'shutdown':1,'force':True})
                except (AutoReconnect,ConnectionFailure): pass
                try: process.wait(timeout=12); evidence['graceful_shutdown']=True
                except subprocess.TimeoutExpired:
                    process.terminate(); process.wait(timeout=10); evidence['graceful_shutdown']=False
            else:
                process.terminate(); process.wait(timeout=10)
        if bootstrap is not None: bootstrap.close()
        with socket.socket() as probe:
            probe.settimeout(1)
            if probe.connect_ex(('127.0.0.1',port))==0: raise RuntimeError('Owned listener still open')
        evidence['listener_stopped']=True
        if log.exists(): evidence['server_log']=log.read_text(encoding='utf-8',errors='replace')
        if target.parent!=base or not target.name.startswith('placement-m14-'):
            raise RuntimeError('Refusing unexpected cleanup target')
        shutil.rmtree(target)
        evidence['temporary_cluster_removed']=not target.exists()
