from pathlib import Path
from collections import Counter
from cache import Cache, Ring, Router, Source, digest, dispatch, estimates
from runtime import Error
from verification import Fixture

BASE = Path(__file__).resolve().parent
with Fixture('S10',BASE) as h:
    s = h.store(Source)
    ring = Ring(['a','b','c'])
    reordered = Ring(['c','a','b'])
    extended = Ring(['a','b','c','d'])
    keys = ['key'+str(n) for n in range(2000)]
    old = [ring.owners(k,1)[0] for k in keys]
    new = [extended.owners(k,1)[0] for k in keys]
    moved = [i for i in range(len(keys)) if old[i]!=new[i]]
    removed = Ring(['a','c'])
    modulo_old = [digest(k)%3 for k in keys]
    modulo_new = [digest(k)%4 for k in keys]
    h.check('placement','membership order deterministic',all(ring.owners(k)==reordered.owners(k) for k in keys))
    h.check('placement','replicas are distinct physical nodes',all(len(set(ring.owners(k)))==2 for k in keys))
    h.check('placement','all configured nodes receive sample keys',set(old)=={'a','b','c'})
    h.check('placement','addition moves only to added node',bool(moved) and all(new[i]=='d' for i in moved))
    h.check('placement','removal preserves unaffected primaries',all(removed.owners(k,1)[0]==owner for k,owner in zip(keys,old) if owner!='b'))
    h.check('placement','single node does not duplicate replica',Ring(['a']).owners('x',2)==['a'])
    for name,nodes in [('empty ring',[]),('duplicate nodes',['a','a']),('invalid node',['bad:name']),('too many nodes',[str(i) for i in range(9)])]:
        h.denied('bounds',name,400,lambda nodes=nodes:Ring(nodes))
    h.denied('bounds','boolean vnode count',400,lambda:Ring(['a'],True))
    h.observations['placement']={'sample_keys':len(keys),'old_primary_counts':dict(sorted(Counter(old).items())),
        'added_node_primary_moves':len(moved),'movement_denominator':'all 2000 sampled keys',
        'moved_fraction':len(moved)/len(keys),'modulo_index_moves':sum(a!=b for a,b in zip(modulo_old,modulo_new)),
        'only_added_node_receives_moved_primaries':True,'virtual_nodes_per_physical_node':32,'throughput_benchmark':False}
    r = Router(['app_a','app_b'])
    first = r.begin()
    second = r.begin()
    h.check('routing','least active sends second elsewhere',first[1]!=second[1])
    r.state(first[1],draining=True)
    h.check('routing','drain preserves active ownership',r.nodes[first[1]]['active']==1)
    third = r.begin()
    h.check('routing','drain avoids new dispatch',third[1]==second[1])
    h.denied('routing','capacity exhausted returns unavailable',503,r.begin)
    h.check('routing','finish draining request',r.end(first[0]) and r.nodes[first[1]]['active']==0)
    h.check('routing','double finish harmless',not r.end(first[0]))
    r.state(second[1],healthy=False)
    h.denied('routing','no healthy nondraining backend',503,r.begin)
    h.check('routing','unhealthy backend active calls may finish',r.end(second[0]) and r.end(third[0]))
    r.state(first[1],draining=False)
    recovery = r.begin()
    h.check('routing','recovered eligibility',recovery[1]==first[1] and r.end(recovery[0]))
    h.observations['routing']={'initial_two_backends_distinct':True,'drain_keeps_inflight':True,
        'new_requests_skip_draining':True,'per_backend_inflight_cap':2,'all_unavailable_status':503,
        'upstream_network_requests_executed':False}
    c = Cache(['a','b','c'])
    scope = ('t1','alice','item')
    s.put(scope,0,'v1')
    h.check('cache','first read misses',c.get(s,scope,0)['cache']=='miss')
    h.check('cache','second read hits',c.get(s,scope,1)['cache']=='hit')
    h.check('cache','two cache copies populated',sum(c.key(scope) in x['entries'] for x in c.nodes.values())==2)
    h.check('cache','every read probes source',c.probes==2)
    h.check('cache','TTL before boundary hits',c.get(s,scope,999)['cache']=='hit')
    h.check('cache','TTL at boundary misses',c.get(s,scope,1000)['cache']=='miss')
    pending = c.ticket(s,scope)
    s.put(scope,1,'v2') # Deliberately omit invalidation to test the version probe.
    h.check('coherence','lost invalidation cannot return old value',c.get(s,scope,1001)['value']=='v2')
    h.check('coherence','late old-version fill rejected',not c.fill(s,pending,1002))
    h.denied('coherence','stale source CAS conflicts',409,lambda:s.put(scope,1,'lost'))
    pending = c.ticket(s,scope)
    s.put(scope,2,'',True)
    h.denied('coherence','delete hides old cached copies',404,lambda:c.get(s,scope,1003))
    h.check('coherence','late fill after delete rejected',not c.fill(s,pending,1004))
    s.put(scope,3,'v4')
    h.check('coherence','explicit recreation advances version',c.get(s,scope,1005)['version']==4)
    h.denied('bounds','boolean expected version',400,lambda:s.put(scope,True,'bad'))
    h.denied('bounds','oversize cached value',400,lambda:s.put(scope,4,'x'*257))
    h.denied('isolation','another owner has no record',404,lambda:c.get(s,('t1','bob','item'),1006))
    s.put(('t2','alice','item'),0,'other tenant')
    h.check('isolation','tenant cache key separated',c.get(s,('t2','alice','item'),1007)['value']=='other tenant' and c.get(s,scope,1007)['value']=='v4')
    h.observations['coherence']={'first_read':'miss','second_read':'hit','TTL_boundary_ms':1000,
        'value_after_lost_invalidation':'v2','old_version_fill_accepted':False,'delete_read_status':404,
        'delete_fill_accepted':False,'recreated_version':4,'source_version_probe_on_every_read':True}
    primary = c.targets(c.key(scope))[0]
    before = c.ticket(s,scope)
    c.health(primary,False)
    h.check('failure','read from surviving populated copy',c.get(s,scope,1008)['cache']=='hit')
    h.check('failure','old target-set fill rejected',not c.fill(s,before,1008))
    s.put(scope,4,'v5')
    c.get(s,scope,1009)
    c.health(primary,True)
    h.check('failure','rejoin clears old values',not c.nodes[primary]['entries'] and c.nodes[primary]['generation']==2)
    same_version = c.ticket(s,scope)
    c.health(primary,False)
    c.health(primary,True)
    h.check('failure','old incarnation fill rejected',not c.fill(s,same_version,1010))
    h.check('failure','rejoined topology reads current value',c.get(s,scope,1011)['value']=='v5')
    before = c.ticket(s,scope)
    h.check('membership','same config no epoch change',c.membership(['c','b','a'])==1)
    h.check('membership','new config advances epoch',c.membership(['a','b','c','d'])==2)
    h.check('membership','old epoch fill rejected',not c.fill(s,before,1012))
    h.check('membership','membership epoch starts cold',all(not x['entries'] for x in c.nodes.values()))
    for node in list(c.nodes):
        c.health(node,False)
    h.check('failure','all caches down falls back to source',c.get(s,scope,1013)['value']=='v5')
    h.check('failure','unavailable caches not filled',all(not x['entries'] for x in c.nodes.values()))
    h.observations['failure_rejoin']={'surviving_copy_read':'hit','rejoined_cache_cleared':True,
        'first_rejoined_generation':2,'second_rejoined_generation':3,'new_membership_epoch':2,'old_epoch_fill_accepted':False,
        'all_caches_down_source_value':'v5','automatic_failure_detector':False,'network_replication_executed':False}
    small = Cache(['one'],2)
    for name in ('a','b'):
        s.put(('t1','alice',name),0,name)
        small.get(s,('t1','alice',name),0)
    small.get(s,('t1','alice','a'),1)
    s.put(('t1','alice','c'),0,'c')
    small.get(s,('t1','alice','c'),2)
    h.check('eviction','LRU preserves recently read key',small.key(('t1','alice','a')) in small.nodes['one']['entries'])
    h.check('eviction','LRU removes older key',small.key(('t1','alice','b')) not in small.nodes['one']['entries'])
    h.check('eviction','capacity respected',len(small.nodes['one']['entries'])==2)
    concurrent = Cache(['one'])
    scope2 = ('t1','alice','race')
    s.put(scope2,0,'old')
    results = h.race(lambda:Source(h.root/'main.sqlite'),[lambda x:concurrent.get(x,scope2,0),lambda x:concurrent.get(x,scope2,0)])
    h.check('concurrency','two cold reads coalesce locally',sorted(x['cache'] for x in results)==['hit','miss'] and concurrent.loads==1)
    def update(source,value):
        try:
            return source.put(scope2,1,value)['version']
        except Error as error:
            return error.status
    result = h.race(lambda:Source(h.root/'main.sqlite'),[lambda x:update(x,'left'),lambda x:update(x,'right')])
    h.check('concurrency','competing CAS has one winner',sorted(result)==[2,409])
    h.observations['concurrency']={'cold_reader_results':sorted(x['cache'] for x in results),'coalesced_payload_loads':1,
        'competing_source_update_results':sorted(result),'singleflight_scope':'one process, coarse shared lock'}
    before = s.record(scope2)
    s.db.execute("CREATE TRIGGER stop_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','source update rollback retains version and value',lambda:s.put(scope2,2,'fault'),lambda:s.record(scope2)==before)
    s.db.execute('DROP TRIGGER stop_update')
    s.close()
    s = h.store(Source)
    h.check('atomicity','source survives reopen with cold cache',Cache(['one']).get(s,scope2,0)['value']==before['value'])
    http_cache,http_router = Cache(['a','b','c']),Router(['app_a','app_b'])
    port = h.serve(lambda:Source(h.root/'main.sqlite'),lambda src,u,m,p,b,hd:dispatch(src,u,m,p,b,hd,http_cache,http_router,lambda:5000))
    put = h.request(port,'PUT','/items/http',{'expected_version':0,'value':'hello'})
    h.check('http','source write',put[0]==200 and put[2]['version']==1)
    h.check('http','cold read',h.request(port,'GET','/items/http')[2]['cache']=='miss')
    h.check('http','warm read',h.request(port,'GET','/items/http')[2]['cache']=='hit')
    h.check('http','other owner hidden',h.request(port,'GET','/items/http',token='lesson-bob')[0]==404)
    h.check('http','other tenant hidden',h.request(port,'GET','/items/http',token='lesson-other')[0]==404)
    h.check('http','anonymous denied',h.request(port,'GET','/items/http',token=None)[0]==401)
    h.check('http','body tenant override rejected',h.request(port,'PUT','/items/x',{'expected_version':0,'value':'x','tenant':'t2'})[0]==400)
    h.check('http','stale version conflicts',h.request(port,'PUT','/items/http',{'expected_version':0,'value':'bad'})[0]==409)
    h.check('http','delete source',h.request(port,'DELETE','/items/http',{'expected_version':1})[2]['deleted'])
    h.check('http','deleted read hidden',h.request(port,'GET','/items/http')[0]==404)
    h.check('http','router slots released on errors',all(v['active']==0 for v in http_router.nodes.values()))
    h.observations['http_contract']={'PUT':200,'first_GET':'miss','second_GET':'hit','foreign_owner':404,
        'foreign_tenant':404,'anonymous':401,'stale_write':409,'deleted_GET':404,'real_loopback_HTTP':True,
        'application_backend_is_label_not_network_proxy':True}
    h.observations['estimates'] = estimates()
h.report('Deterministic placement sample, in-process least-active routing/drain labels, bounded copied LRU caches, guarded fill/version/delete/epoch checks, controlled failure/rejoin, four competing calls, SQLite rollback/reopen and actual edge HTTP. No network proxy, distributed membership, Redis replication, automatic detector, quorum or throughput benchmark.')
