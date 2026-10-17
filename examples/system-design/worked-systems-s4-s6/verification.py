"""Owned fixture lifecycle and evidence recording for the three worked systems."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from threading import Barrier, Thread
import json
import platform
import socket
import sqlite3
from runtime import Error, server


class Fixture:
    def __init__(self,label,base):
        self.label,self.base = label,Path(base)
        self.temporary = TemporaryDirectory(prefix='placement-'+label.lower()+'-verify-')
        self.root = Path(self.temporary.name).resolve()
        self.items,self.servers,self.threads,self.ports,self.checks = [],[],[],[],[]
        self.observations,self.worker_calls = {},0

    def __enter__(self):
        return self

    def store(self,factory,name='main'):
        value = factory(self.root/(name+'.sqlite'))
        self.items.append(value)
        return value

    def check(self,group,name,value):
        assert value,(self.label,group,name)
        self.checks.append({'group':group,'name':name,'passed':True})

    def denied(self,group,name,status,action):
        try:
            action()
        except Error as error:
            self.check(group,name,error.status == status)
        else:
            raise AssertionError(name)

    def fault(self,group,name,action,condition):
        try:
            action()
        except sqlite3.IntegrityError:
            self.check(group,name,condition())
        else:
            raise AssertionError('Missing injected database fault: '+name)

    def race(self,factory,actions):
        barrier = Barrier(len(actions))
        def run(action):
            value = factory() if factory else None
            try:
                barrier.wait(timeout=5)
                return action(value) if factory else action()
            finally:
                if value is not None:
                    value.close()
        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            result = list(pool.map(run,actions))
        self.worker_calls += len(actions)
        return result

    def serve(self,factory,dispatch):
        api = server(factory,dispatch)
        thread = Thread(target=api.serve_forever,name=self.label+'-owned-http')
        thread.start()
        self.servers.append(api)
        self.threads.append(thread)
        self.ports.append(api.server_port)
        return api.server_port

    def request(self,port,method,path,value=None,token='lesson-alice',headers=None):
        raw = value if type(value) is bytes else json.dumps(value).encode() if value is not None else None
        configured = {'Authorization':'Bearer '+token} if token else {}
        configured.update(headers or {})
        connection = HTTPConnection('127.0.0.1',port,timeout=3)
        try:
            connection.request(method,path,body=raw,headers=configured)
            response = connection.getresponse()
            return response.status,dict(response.getheaders()),json.loads(response.read())
        finally:
            connection.close()

    def __exit__(self,*_):
        for api in self.servers:
            api.shutdown()
            api.server_close()
        for thread in self.threads:
            thread.join(timeout=5)
            assert not thread.is_alive()
        for item in self.items:
            item.close()
        assert self.root.parent == Path(gettempdir()).resolve()
        assert self.root.name.startswith('placement-'+self.label.lower()+'-verify-')
        self.temporary.cleanup()

    def report(self,scope):
        for item in self.items:
            try:
                item.db.execute('SELECT 1')
            except sqlite3.ProgrammingError:
                continue
            raise AssertionError('Connection left open')
        self.check('cleanup','tracked SQLite connections closed',True)
        self.check('cleanup','owned temporary directory removed',not self.root.exists())
        for port in self.ports:
            with socket.socket() as probe:
                probe.settimeout(1)
                self.check('cleanup','owned HTTP listener closed',probe.connect_ex(('127.0.0.1',port)) != 0)
        self.check('cleanup','port 3000 unused',3000 not in self.ports)
        assert len({(item['group'],item['name']) for item in self.checks}) == len(self.checks)
        result = {'label':self.label,'verified_date':'2026-10-17','python':platform.python_version(),
            'sqlite':sqlite3.sqlite_version,'os':platform.system(),'total':len(self.checks),
            'counts':dict(Counter(item['group'] for item in self.checks)),
            'checks':self.checks,'observations':self.observations,
            'cleanup':{'fixture_ports':self.ports,'temporary_database_directory_removed':not self.root.exists(),
                'sqlite_connections_closed':True,'temporary_http_servers_closed':True,
                'concurrent_worker_calls_completed':self.worker_calls,'port_3000_used':False},'scope':scope}
        (self.base/'verification-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({key:result[key] for key in ('label','total','counts','cleanup')},indent=2))
