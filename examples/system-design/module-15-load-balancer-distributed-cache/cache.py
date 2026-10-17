"""Local model of placement, health, bounded replicated cache and guarded fills."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
from bisect import bisect_left
from collections import OrderedDict
from threading import RLock
import hashlib
import json
import re
import uuid
from runtime import Database, Error, document, identity, number, require


def digest(value):
    return int.from_bytes(hashlib.sha256(value.encode()).digest(),'big')


class Ring:
    def __init__(self,nodes,vnodes=32):
        if type(nodes) is not list or not 1<=len(nodes)<=8:
            raise Error(400,'invalid_membership')
        for node in nodes:
            identity(node)
        if len(set(nodes))!=len(nodes):
            raise Error(400,'duplicate_member')
        number(vnodes,1,128)
        self.nodes = sorted(nodes)
        self.points = sorted((digest(f'{node}:{i}'),node) for node in self.nodes for i in range(vnodes))
        self.positions = [point for point,_ in self.points]

    def owners(self,key,count=2):
        number(count,1,8)
        start = bisect_left(self.positions,digest(key))
        result = []
        for offset in range(len(self.points)):
            node = self.points[(start+offset)%len(self.points)][1]
            if node not in result:
                result.append(node)
            if len(result)==min(count,len(self.nodes)):
                break
        return result


class Router:
    def __init__(self,nodes):
        Ring(nodes)
        self.lock = RLock()
        self.nodes = {node:{'healthy':True,'draining':False,'active':0} for node in nodes}
        self.tokens = {}

    def begin(self):
        with self.lock:
            eligible = [node for node,state in self.nodes.items() if state['healthy'] and not state['draining'] and state['active']<2]
            if not eligible:
                raise Error(503,'no_application_capacity')
            node = min(eligible,key=lambda n:(self.nodes[n]['active'],n))
            token = uuid.uuid4().hex
            self.tokens[token] = node
            self.nodes[node]['active'] += 1
            return token,node

    def end(self,token):
        with self.lock:
            node = self.tokens.pop(token,None)
            if node is None:
                return False
            self.nodes[node]['active'] -= 1
            return True

    def state(self,node,*,healthy=None,draining=None):
        with self.lock:
            if node not in self.nodes:
                raise Error(404,'backend_not_found')
            for key,value in [('healthy',healthy),('draining',draining)]:
                if value is not None:
                    if type(value) is not bool:
                        raise Error(400,'invalid_backend_state')
                    self.nodes[node][key] = value


class Source(Database):
    schema = '''CREATE TABLE IF NOT EXISTS records(tenant TEXT,owner TEXT,key TEXT,version INTEGER,
        value TEXT,deleted INTEGER,PRIMARY KEY(tenant,owner,key));'''

    def record(self,scope):
        row = self.db.execute('SELECT * FROM records WHERE tenant=? AND owner=? AND key=?',scope).fetchone()
        return dict(row) if row else None

    def head(self,scope):
        row = self.db.execute('SELECT version,deleted FROM records WHERE tenant=? AND owner=? AND key=?',scope).fetchone()
        return dict(row) if row else None

    def put(self,scope,expected_version,value,deleted=False):
        for part in scope:
            identity(part)
        number(expected_version)
        if type(value) is not str or len(value)>256 or type(deleted) is not bool:
            raise Error(400,'invalid_value')
        with self.transaction():
            old = self.record(scope)
            if (old['version'] if old else 0)!=expected_version:
                raise Error(409,'version_conflict')
            if old is None and self.db.execute('SELECT count(*) FROM records').fetchone()[0]>=128:
                raise Error(503,'lesson_source_retention_cap')
            if deleted and (old is None or old['deleted']):
                raise Error(404,'record_not_found')
            self.db.execute('INSERT INTO records VALUES(?,?,?,?,?,?) ON CONFLICT(tenant,owner,key) DO UPDATE SET version=excluded.version,value=excluded.value,deleted=excluded.deleted',
                (*scope,expected_version+1,'' if deleted else value,int(deleted)))
            return self.record(scope)


class Cache:
    def __init__(self,nodes,capacity=4):
        number(capacity,1,32)
        self.lock,self.capacity,self.epoch = RLock(),capacity,1
        self.ring = Ring(nodes)
        self.nodes = {node:{'healthy':True,'generation':1,'entries':OrderedDict()} for node in nodes}
        self.loads,self.probes = 0,0

    def key(self,scope):
        for part in scope:
            identity(part)
        return json.dumps(list(scope),separators=(',',':'))

    def targets(self,key):
        return [n for n in self.ring.owners(key,len(self.ring.nodes)) if self.nodes[n]['healthy']][:2]

    def ticket(self,source,scope):
        with self.lock:
            key = self.key(scope)
            row = source.record(scope)
            return {'scope':scope,'row':row,'epoch':self.epoch,
                'targets':[(n,self.nodes[n]['generation']) for n in self.targets(key)]}

    def fill(self,source,ticket,now):
        number(now)
        with self.lock:
            key = self.key(ticket['scope'])
            current = source.record(ticket['scope'])
            targets = [(n,self.nodes[n]['generation']) for n in self.targets(key)]
            if not current or current['deleted'] or current!=ticket['row'] or ticket['epoch']!=self.epoch or ticket['targets']!=targets:
                return False
            for node,_ in targets:
                entries = self.nodes[node]['entries']
                entries[key] = {'version':current['version'],'value':current['value'],'expires':now+1000}
                entries.move_to_end(key)
                while len(entries)>self.capacity:
                    entries.popitem(last=False)
            return bool(targets)

    def get(self,source,scope,now):
        number(now)
        with self.lock:
            key = self.key(scope)
            # A canonical version/deletion probe on EVERY read is intentional.
            self.probes += 1
            row = source.head(scope)
            if not row or row['deleted']:
                raise Error(404,'record_not_found')
            for node in self.targets(key):
                entries = self.nodes[node]['entries']
                hit = entries.get(key)
                if hit and hit['expires']>now and hit['version']==row['version']:
                    entries.move_to_end(key)
                    return {'value':hit['value'],'version':hit['version'],'cache':'hit','cache_node':node}
                if hit:
                    del entries[key]
            self.loads += 1
            ticket = self.ticket(source,scope)
            current = ticket['row']
            if not current or current['deleted']:
                raise Error(404,'record_not_found')
            self.fill(source,ticket,now)
            return {'value':current['value'],'version':current['version'],'cache':'miss','cache_node':None}

    def invalidate(self,scope):
        with self.lock:
            key = self.key(scope)
            for state in self.nodes.values():
                state['entries'].pop(key,None)

    def health(self,node,healthy):
        with self.lock:
            if node not in self.nodes or type(healthy) is not bool:
                raise Error(400,'invalid_cache_health')
            state = self.nodes[node]
            if healthy and not state['healthy']:
                # Rejoin starts cold; old bytes are not resynchronized replicas.
                state['entries'].clear()
                state['generation'] += 1
            state['healthy'] = healthy

    def membership(self,nodes):
        ring = Ring(nodes)
        with self.lock:
            if ring.nodes==self.ring.nodes:
                return self.epoch
            self.nodes = {n:self.nodes.get(n,{'healthy':True,'generation':1,'entries':OrderedDict()}) for n in ring.nodes}
            self.ring = ring
            self.epoch += 1
            # Cold epoch simplifies cleanup; no online data migration claim.
            for state in self.nodes.values():
                state['entries'].clear()
            return self.epoch


def estimates():
    return {'requests_per_second':10000,'assumed_mean_request_seconds':0.02,'mean_inflight':200,
        'assumed_cache_hit_ratio':0.9,'hypothetical_payload_misses_per_second':1000,
        'fixture_version_probes_per_second_at_that_load':10000,'hot_key_fraction':0.6,
        'hot_key_requests_per_second':6000,'keys_for_placement_comparison':2000,'measured_capacity':False}


def dispatch(source,user,method,path,raw,headers,cache,router,clock):
    tenant,owner = require(user)
    match = re.fullmatch(r'/items/([A-Za-z0-9_-]{1,64})',path)
    if not match:
        raise Error(404,'unknown_route')
    token,backend = router.begin()
    try:
        scope = (tenant,owner,match[1])
        if method=='GET':
            return 200,dict(cache.get(source,scope,clock()),application_backend=backend)
        if method in ('PUT','DELETE'):
            fields = ['expected_version','value'] if method=='PUT' else ['expected_version']
            value = document(raw,fields)
            with cache.lock:
                result = source.put(scope,value['expected_version'],value.get('value',''),method=='DELETE')
                cache.invalidate(scope)
            return 200,{'version':result['version'],'deleted':bool(result['deleted']),'application_backend':backend}
        raise Error(404,'unknown_route')
    finally:
        router.end(token)
