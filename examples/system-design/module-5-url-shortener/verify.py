"""Real local HTTP/SQLite shortener verification; never follow or fetch destinations."""
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier,Thread
import json
import math
import platform
import sqlite3

from shortener import Store,Error,TOKENS,validate_url,random_code,valid_code
from service import Service
from http_api import make_server
from estimates import calculate

BASE = Path(__file__).resolve().parent
checks,observations = [],{}
URL = 'https://example.com/guide?topic=system-design#intro'


def check(group,name,condition):
    assert condition,name
    checks.append({'group':group,'name':name,'passed':True})


def raises(group,name,expected,action):
    try:
        action()
    except expected as error:
        check(group,name,True)
        return error
    raise AssertionError(name)


class Codes:
    def __init__(self,*values):
        self.values = iter(values)
    def __call__(self):
        return next(self.values)


def main():
    for url in ('javascript:alert(1)','http://example.com/x','https://evil.example/x',
                'https://example.com@evil.example/x','https://user:pw@example.com/x',
                'https://example.com:444/x','https://example.com:bad/x','https://example.com/\r\nLocation:x',
                'https://example.com/%0d%0aX:y','https://example.com\\@evil.example/x',
                'https://example.com/space here','https://example.com/'+'x'*2048):
        raises('validation','destination rejected '+repr(url[:80]),Error,lambda url=url:validate_url(url))
    check('validation','exact accepted path query and fragment preserved',validate_url(URL)==URL)
    check('validation','explicit HTTPS default port accepted',validate_url('https://example.com:443/x')=='https://example.com:443/x')
    check('validation','approved documentation host accepted',validate_url('https://docs.python.org/3/')=='https://docs.python.org/3/')
    sample = [random_code() for _ in range(20)]
    check('validation','default code generator produces valid base62-shaped codes',all(valid_code(code) for code in sample))
    owned,servers = [],[]
    ports = []
    with TemporaryDirectory(prefix='placement-s0-') as directory:
        directory = Path(directory)

        def store(name,*codes):
            value = Store(directory/name,Codes(*codes) if codes else random_code)
            owned.append(value)
            return value

        def close(value):
            value.close()
            owned.remove(value)

        try:
            alice,bob,beta = TOKENS['lesson-alice'],TOKENS['lesson-bob'],TOKENS['lesson-beta']
            case_store = store('case-sensitive.sqlite','AAAAAAAA','aaaaaaaa')
            upper,_ = case_store.create(alice,'upper',URL,10,0)
            lower,_ = case_store.create(alice,'lower','https://example.com/lower',10,0)
            check('authority','database code namespace distinguishes letter case',upper['code']!=lower['code'] and
                case_store.lookup('AAAAAAAA').url==URL and case_store.lookup('aaaaaaaa').url=='https://example.com/lower')
            authority = store('authority.sqlite','AAAAAAAA','AAAAAAAA','BBBBBBBB','CCCCCCCC','DDDDDDDD')
            first,replay = authority.create(alice,'one',URL,10,0)
            check('authority','new create stores a non-replay result',not replay and first['code']=='AAAAAAAA')
            other,replay = authority.create(alice,'two','https://example.com/other',20,0)
            check('authority','forced collision retries another code',other['code']=='BBBBBBBB' and authority.collisions==1)
            check('authority','collision never overwrites original destination',authority.lookup('AAAAAAAA').url==URL)
            again,replay = authority.create(alice,'one',URL,10,5)
            check('authority','retry returns original outcome and expiry',replay and again==first and again['expires_at']==10)
            conflict = raises('authority','changed URL under operation key conflicts',Error,lambda:authority.create(alice,'one','https://example.com/changed',10,5))
            check('authority','changed-intent conflict is explicit',conflict.status==409)
            raises('authority','changed lifetime under operation key conflicts',Error,lambda:authority.create(alice,'one',URL,11,5))
            owner,_ = authority.create(bob,'one',URL,10,0)
            tenant,_ = authority.create(beta,'one',URL,10,0)
            check('authority','owner and tenant operation scopes are separate',len({first['code'],owner['code'],tenant['code']})==3)
            raises('authority','wrong owner cannot manage link',Error,lambda:authority.owned(bob,first['code']))
            raises('authority','wrong tenant cannot disable link',Error,lambda:authority.disable(beta,first['code']))
            raises('authority','boolean lifetime rejected',Error,lambda:authority.create(alice,'bad',URL,True,0))
            raises('authority','zero lifetime rejected',Error,lambda:authority.create(alice,'bad',URL,0,0))
            raises('authority','too-long lifetime rejected',Error,lambda:authority.create(alice,'bad',URL,86401,0))
            raises('authority','invalid operation key rejected',Error,lambda:authority.create(alice,'bad\n',URL,10,0))
            close(authority)
            authority = store('authority.sqlite')
            reopened,replay = authority.create(alice,'one',URL,10,9)
            check('authority','original successful operation survives reopen',replay and reopened==first)
            check('authority','global link identity survives reopen',authority.lookup(first['code']).url==URL)
            exhausted = store('exhausted.sqlite',*(['XXXXXXXX']*6))
            exhausted.create(alice,'first',URL,10,0)
            error = raises('authority','allocation attempts are bounded',Error,lambda:exhausted.create(alice,'second',URL,10,0))
            check('authority','exhaustion is a retryable service failure',error.status==503 and exhausted.collisions==5)
            check('authority','exhaustion leaves one link and no false outcome',exhausted.db.execute('SELECT count(*) FROM links').fetchone()[0]==1 and exhausted.db.execute('SELECT count(*) FROM operations').fetchone()[0]==1)
            fault = store('fault.sqlite','FAULT000','FAULT001')
            raises('authority','fault after allocation rolls back',RuntimeError,lambda:fault.create(alice,'op',URL,10,0,fail_after_insert=True))
            check('authority','rollback leaves no orphan link',fault.db.execute('SELECT count(*) FROM links').fetchone()[0]==0)
            check('authority','rollback leaves no successful operation record',fault.db.execute('SELECT count(*) FROM operations').fetchone()[0]==0)
            recovered,replay = fault.create(alice,'op',URL,10,0)
            check('authority','retry after rollback creates normally',not replay and recovered['code']=='FAULT001')
            observations['allocation'] = {'forced_collision_count':1,'original_code':first['code'],
                'collision_retry_code':other['code'],'original_preserved':True,'replay_survives_reopen':True,
                'exhausted_candidate_attempts':5,'post_rollback_new_code':recovered['code']}

            clock = {'now':0.0}
            cache = Service(authority,lambda:clock['now'],cache_ttl=20,cache_capacity=2)
            reads = authority.reads
            check('cache_expiry','cold resolution returns canonical destination',cache.resolve(first['code'],False)==URL)
            check('cache_expiry','warm resolution returns same destination',cache.resolve(first['code'],False)==URL)
            check('cache_expiry','warm hit avoids authority read',authority.reads-reads==1 and cache.metrics['cache_hits']==1)
            clock['now']=9.999
            check('cache_expiry','link remains valid just before absolute expiry',cache.resolve(first['code'],False)==URL)
            clock['now']=10
            gone = raises('cache_expiry','expiry enforced at equality even with long cache TTL',Error,lambda:cache.resolve(first['code'],False))
            check('cache_expiry','known expired code reports gone',gone.status==410)
            expired_replay,replay = authority.create(alice,'one',URL,10,11)
            check('cache_expiry','create retry cannot renew an expired link',replay and expired_replay['expires_at']==10)
            check('cache_expiry','missing code reports not found',raises('cache_expiry','missing lookup has declared error',Error,lambda:cache.resolve('MISSING0',False)).status==404)
            raises('cache_expiry','malformed code is not a path or query',Error,lambda:cache.resolve('../x',False))
            clock['now']=0
            cache.resolve(other['code'],False)
            cache.resolve(owner['code'],False)
            cache.resolve(tenant['code'],False)
            check('cache_expiry','local cache capacity is bounded',len(cache.cache)==2 and cache.metrics['evictions']>=1)
            # Two caches over distinct connections: local disable does not broadcast.
            left_store = store('visibility.sqlite','VISIBLE0')
            visible,_ = left_store.create(alice,'visible',URL,60,0)
            right_store = store('visibility.sqlite')
            left = Service(left_store,lambda:clock['now'])
            right = Service(right_store,lambda:clock['now'])
            left.resolve(visible['code'],False)
            right.resolve(visible['code'],False)
            left.disable(alice,visible['code'])
            check('cache_expiry','local disable invalidates warmed cache',raises('cache_expiry','disabled local resolution fails',Error,lambda:left.resolve(visible['code'],False)).status==410)
            check('cache_expiry','independent warmed cache can still serve old active state',right.resolve(visible['code'],False)==URL)
            clock['now']=2
            check('cache_expiry','independent cache observes disable after TTL',raises('cache_expiry','remote cache refresh finds disabled state',Error,lambda:right.resolve(visible['code'],False)).status==410)
            observations['expiry_and_disable'] = {'expires_at':10,'before_expiry':302,'at_expiry':410,
                'expired_create_retry_expires_at':expired_replay['expires_at'],'local_disable':410,
                'other_cache_before_refresh':302,'other_cache_after_refresh':410,
                'invalidation_broadcast_implemented':False}

            analytics_store = store('analytics.sqlite','ANALYTIC')
            analytic,_ = analytics_store.create(alice,'a',URL,1000,0)
            clock['now']=0
            analytics = Service(analytics_store,lambda:clock['now'],analytics_capacity=2)
            for _ in range(5):
                analytics.resolve(analytic['code'])
            check('analytics','queue bound does not suppress redirect decisions',analytics.metrics['redirect_decisions']==5)
            check('analytics','analytics admission drops excess rather than grows without bound',analytics.queue.qsize()==2 and analytics.metrics['analytics_dropped']==3)
            check('analytics','bounded batch persists accepted aggregate',analytics.flush_analytics()==2)
            check('analytics','statistics identify recorded decisions rather than visits',analytics.statistics(alice,analytic['code'])['recorded_redirect_decisions']==2)
            check('analytics','flushed queue has no unfinished tasks',analytics.queue.unfinished_tasks==0)
            analytics.resolve(analytic['code'])
            check('analytics','controlled analytics write failure is isolated',analytics.flush_analytics(fail=True)==0 and analytics.metrics['analytics_write_dropped']==1)
            check('analytics','failed analytics batch rolls back its count',analytics.statistics(alice,analytic['code'])['recorded_redirect_decisions']==2)
            check('analytics','redirect still works after analytics failure',analytics.resolve(analytic['code'],False)==URL)
            raises('analytics','other owner cannot read statistics',Error,lambda:analytics.statistics(bob,analytic['code']))
            clock['now']=180
            check('analytics','statistics window excludes old minute buckets',analytics.statistics(alice,analytic['code'])['recorded_redirect_decisions']==0)
            analytics.flush_analytics()
            check('analytics','flush prunes old durable buckets',analytics_store.db.execute('SELECT count(*) FROM counts').fetchone()[0]==0)
            analytics.resolve(analytic['code'])
            clock['now']=360
            check('analytics','late queued events cannot resurrect expired analytics buckets',analytics.flush_analytics()==0 and analytics.metrics['analytics_stale_dropped']==1)
            observations['analytics'] = {'initial_redirect_decisions':5,'queue_capacity':2,'initial_enqueued':2,
                'initial_overflow_dropped':3,'initial_recorded':2,'write_failure_dropped':1,
                'expired_buckets_pruned':True,'late_event_dropped':True,'unique_human_visits_measured':False}

            # Force simultaneous global-code collision, then same-operation retry.
            def competing(name,same_operation):
                base = store(name)
                barrier = Barrier(2)
                def worker(index):
                    db = Store(directory/name,Codes('RACE0000','RACE000'+str(index)))
                    try:
                        barrier.wait(timeout=5)
                        principal = alice if same_operation else (alice if index==1 else bob)
                        key = 'shared_operation' if same_operation else 'op_'+str(index)
                        return db.create(principal,key,URL,60,0),db.collisions
                    finally:
                        db.close()
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures=[pool.submit(worker,index) for index in (1,2)]
                    results=[future.result(timeout=10) for future in futures]
                return base,results
            race,results = competing('race.sqlite',False)
            check('concurrency','competing creators receive different globally unique codes',len({value[0][0]['code'] for value in results})==2)
            check('concurrency','collision loser retries instead of overwriting',sum(value[1] for value in results)==1)
            check('concurrency','two successful intents persist two links and outcomes',race.db.execute('SELECT count(*) FROM links').fetchone()[0]==race.db.execute('SELECT count(*) FROM operations').fetchone()[0]==2)
            duplicate,results = competing('duplicate.sqlite',True)
            check('concurrency','concurrent same operation receives same code and outcome',results[0][0][0]==results[1][0][0])
            check('concurrency','one concurrent retry reports replay',sorted(value[0][1] for value in results)==[False,True])
            check('concurrency','same operation allocates only one link',duplicate.db.execute('SELECT count(*) FROM links').fetchone()[0]==1)
            observations['concurrency'] = {'forced_same_candidate_two_intents':{'links':2,'collisions':1},
                'same_operation_two_callers':{'links':1,'replay_flags':[False,True]},
                'independent_connections_per_race':2,'worker_calls_completed':4}

            api_store = store('api.sqlite','HTTP0000','HTTP0001','HTTP0002')
            clock['now']=100
            api = Service(api_store,lambda:clock['now'])
            server=make_server(api)
            thread=Thread(target=server.serve_forever,kwargs={'poll_interval':0.05})
            thread.start()
            servers.append((server,thread))
            def call(method,path,body=None,token='lesson-alice',extra=None,raw=False):
                headers={'Authorization':'Bearer '+token} if token else {}
                if body is not None:
                    headers['Content-Type']='application/json'
                headers.update(extra or {})
                payload=body if raw else None if body is None else json.dumps(body).encode()
                connection=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                try:
                    connection.request(method,path,body=payload,headers=headers)
                    response=connection.getresponse()
                    result={'status':response.status,'headers':dict(response.getheaders()),'body':response.read()}
                finally:
                    connection.close()
                if result['body']:
                    result['json']=json.loads(result['body'])
                return result
            created=call('POST','/api/links',{'url':URL,'ttl_seconds':10},extra={'Idempotency-Key':'create','Host':'attacker.example'})
            code=created['json']['code']
            check('http','authenticated create returns 201',created['status']==201)
            check('http','trusted configured base ignores untrusted Host',created['json']['short_url']=='https://short.example/r/'+code)
            check('http','create Location points to owned management resource',created['headers']['Location']=='/api/links/'+code)
            check('http','new create reports non-replay',created['headers']['Idempotency-Replayed']=='false')
            repeated=call('POST','/api/links',{'url':URL,'ttl_seconds':10},extra={'Idempotency-Key':'create'})
            check('http','HTTP retry returns exact original create representation',repeated['status']==201 and repeated['json']==created['json'] and repeated['headers']['Idempotency-Replayed']=='true')
            conflict=call('POST','/api/links',{'url':URL,'ttl_seconds':11},extra={'Idempotency-Key':'create'})
            check('http','HTTP changed-intent retry maps to conflict',conflict['status']==409)
            redirect=call('GET','/r/'+code,token='')
            check('http','public redirect requires no management credential',redirect['status']==302)
            check('http','redirect Location preserves target exactly',redirect['headers']['Location']==URL)
            check('http','redirect has empty response body',redirect['body']==b'')
            check('http','redirect explicitly prevents downstream caching',redirect['headers']['Cache-Control']=='no-store')
            check('http','redirect does not disclose owner metadata',all(name not in redirect['headers'] for name in ('X-Owner','X-Tenant')))
            decision_count=api.metrics['redirect_decisions']
            head=call('HEAD','/r/'+code,token='')
            check('http','HEAD returns redirect headers without a body',head['status']==302 and head['body']==b'' and head['headers']['Location']==URL)
            check('http','HEAD is excluded from analytics decisions',api.metrics['redirect_decisions']==decision_count)
            check('http','POST to redirect route is rejected',call('POST','/r/'+code,token='')['status']==405)
            managed=call('GET','/api/links/'+code)
            check('http','owner can read management state',managed['status']==200 and managed['json']['disabled']==0)
            check('http','other owner cannot read management state',call('GET','/api/links/'+code,token='lesson-bob')['status']==404)
            check('http','other tenant cannot disable code',call('DELETE','/api/links/'+code,token='lesson-beta')['status']==404)
            check('http','other owner cannot read analytics',call('GET','/api/links/'+code+'/stats',token='lesson-bob')['status']==404)
            check('http','management requires credentials',call('GET','/api/links/'+code,token='')['status']==401)
            check('http','unknown management token rejected',call('GET','/api/links/'+code,token='forged')['status']==401)
            check('http','missing create key rejected',call('POST','/api/links',{'url':URL})['status']==400)
            check('http','unknown create field rejected',call('POST','/api/links',{'url':URL,'owner':'bob'},extra={'Idempotency-Key':'bad'})['status']==400)
            check('http','malformed JSON rejected safely',call('POST','/api/links',b'{',extra={'Idempotency-Key':'bad'},raw=True)['status']==400)
            check('http','wrong content type rejected',call('POST','/api/links',{'url':URL},extra={'Content-Type':'text/plain','Idempotency-Key':'bad'})['status']==415)
            check('http','oversized JSON body rejected',call('POST','/api/links',{'url':'https://example.com/'+'x'*5000},extra={'Idempotency-Key':'bad'})['status']==413)
            check('http','unapproved destination rejected',call('POST','/api/links',{'url':'https://evil.example/'},extra={'Idempotency-Key':'bad'})['status']==400)
            api.flush_analytics()
            stats=call('GET','/api/links/'+code+'/stats')
            check('http','owned analytics expose recorded decisions',stats['status']==200 and stats['json']['recorded_redirect_decisions']==1)
            clock['now']=110
            expired=call('GET','/r/'+code,token='')
            check('http','absolute expiration produces HTTP 410',expired['status']==410)
            check('http','unknown public code produces HTTP 404',call('GET','/r/MISSING0',token='')['status']==404)
            check('http','unknown route produces HTTP 404',call('GET','/unknown',token='')['status']==404)
            new=call('POST','/api/links',{'url':URL},extra={'Idempotency-Key':'new'})
            new_code=new['json']['code']
            call('GET','/r/'+new_code,token='')
            check('http','owner disable returns empty 204',call('DELETE','/api/links/'+new_code)['status']==204)
            check('http','repeat disable has same effect/status',call('DELETE','/api/links/'+new_code)['status']==204)
            check('http','local disable affects warmed redirect immediately',call('GET','/r/'+new_code,token='')['status']==410)
            check('http','original create replay does not reactivate disabled link',call('POST','/api/links',{'url':URL},extra={'Idempotency-Key':'new'})['json']==new['json'] and call('GET','/r/'+new_code,token='')['status']==410)
            observations['http_contract']={'create':created['status'],'short_url':created['json']['short_url'],
                'replay':repeated['headers']['Idempotency-Replayed'],'redirect':redirect['status'],
                'location':redirect['headers']['Location'],'cache_control':redirect['headers']['Cache-Control'],
                'head':head['status'],'expires_at':created['json']['expires_at'],'at_expiry':expired['status'],
                'disable':204,'after_disable':410,'destination_requests_made':0}
        finally:
            for server,thread in servers:
                ports.append(server.server_port)
                server.shutdown(); server.server_close(); thread.join(timeout=5)
                assert not thread.is_alive()
            for value in owned:
                value.close()
    check('cleanup','temporary database directory removed after connections close',not directory.exists())
    check('cleanup','all owned HTTP serving threads stopped',all(not thread.is_alive() for _,thread in servers))
    estimate=calculate()
    check('estimates','namespace cardinality equals 62 to the selected length',estimate['namespace_size']==62**8)
    check('estimates','annual create population uses explicit assumption',estimate['new_links_in_period']==3650000)
    check('estimates','storage arithmetic uses stated logical record bytes',estimate['logical_link_storage_bytes']==3650000*512)
    check('estimates','collision probability is bounded and nonzero',0<estimate['probability_at_least_one_collision_approx']<1)
    check('estimates','per-draw collision and population-pair probability differ',estimate['next_draw_collision_probability_at_end']<estimate['probability_at_least_one_collision_approx'])
    check('estimates','eight-character entropy matches selected alphabet',math.isclose(estimate['code_entropy_bits'],8*math.log2(62)))
    raises('estimates','invalid workload assumption rejected',ValueError,lambda:calculate(creates_per_day=0))
    raises('estimates','overfull namespace rejected',ValueError,lambda:calculate(length=1))
    observations['estimates']=estimate
    counts={}
    for row in checks:
        counts[row['group']]=counts.get(row['group'],0)+1
    proof={'label':'S0','module':5,'verified_date':'2026-10-16','python':platform.python_version(),
        'sqlite':sqlite3.sqlite_version,'os':platform.system()+' '+platform.release(),
        'total':len(checks),'counts':counts,'checks':checks,'observations':observations,
        'cleanup':{'sqlite_connections_closed':True,'temporary_database_directory_removed':True,
            'temporary_http_servers_closed':True,'fixture_ports':ports,'concurrent_worker_calls_completed':4,'port_3000_used':False},
        'scope':'Real local SQLite allocation/replay/rollback and two-connection collision/duplicate races; real loopback HTTP create/manage/GET/HEAD redirect/expiry/disable/stats without following destinations. Process-local bounded cache, injected expiry clock and explicitly lossy in-memory analytics with durable bounded-age aggregates. Estimates are hypothetical. No production auth/TLS, unrestricted destination validation, Redis/CDN, durable analytics delivery, multi-host cache coherence, PostgreSQL isolation or throughput capacity verified.'}
    (BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'total':proof['total'],'counts':counts,'observations':observations,'cleanup':proof['cleanup']},indent=2))


if __name__=='__main__':
    main()
