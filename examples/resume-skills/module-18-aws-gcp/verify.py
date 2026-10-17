"""Offline SDK/crypto + real loopback HTTP/SQLite; never contacts cloud APIs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from importlib import metadata
from types import SimpleNamespace
import base64,collections,copy,json,platform,socket,sys,tempfile,threading,time
import urllib.request,urllib.error
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from google.auth import crypt,jwt
from google.cloud import tasks_v2
from task_request import build_request,AUDIENCE,SERVICE_ACCOUNT
from worker import Store,TokenVerifier,AuthenticationError,AuthorizationError,make_server
from cache_demo import PublicCache

BASE=Path(__file__).resolve().parent
checks,observations,servers,threads=[],{},[],[]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def check(group,name,condition,evidence=None):
    item={'group':group,'name':name,'passed':bool(condition)}
    if evidence is not None:item['evidence']=evidence
    checks.append(item)
    print(('PASS ' if condition else 'FAIL ')+group+'/'+name,flush=True)
    if not condition:raise AssertionError(name+' '+str(evidence))

def rejected(fn,types=(ValueError,)):
    try:fn()
    except types:return True
    return False

def start(server):
    servers.append(server)
    thread=threading.Thread(target=server.serve_forever)
    thread.start();threads.append(thread)
    return server.server_address[1]

def request(port,path,*,data=None,headers=None):
    req=urllib.request.Request('http://127.0.0.1:'+str(port)+path,data=data,headers=headers or {})
    try:response=opener.open(req,timeout=8)
    except urllib.error.HTTPError as error:response=error
    with response:
        raw=response.read()
        return response.status,dict(response.headers),json.loads(raw)

def key_pair(key_id='fixture-key'):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    public=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
    return crypt.RSASigner.from_string(private,key_id=key_id),public.decode()

signer,public=key_pair();other_signer,_=key_pair()
unknown_signer,_=key_pair('unknown')
cert_requests=[]
def fixture_transport(url,method='GET',**kwargs):
    if url!='https://www.googleapis.com/oauth2/v1/certs' or method!='GET':
        raise AssertionError('Unexpected certificate request')
    cert_requests.append({'url':url,'method':method,'served_from':'in-memory fixture public key'})
    return SimpleNamespace(status=200,data=json.dumps({'fixture-key':public}).encode())

verifier=TokenVerifier(fixture_transport,AUDIENCE,SERVICE_ACCOUNT)
now=int(time.time())
claims={'iss':'https://accounts.google.com','aud':AUDIENCE,'iat':now-10,'exp':now+3600,
        'sub':'fixture-subject-not-google-issued','email':SERVICE_ACCOUNT,'email_verified':True}
def token(changes=None,*,key=signer,header=None):
    payload={**claims,**(changes or {})}
    return jwt.encode(key,payload,header=header).decode()
valid_token=token()
auth={'Authorization':'Bearer '+valid_token,'Content-Type':'application/json'}

def authenticate(value):return verifier.verify('Bearer '+value)

with tempfile.TemporaryDirectory(prefix='.run-',dir=BASE) as temporary:
    scratch=Path(temporary).resolve()
    if scratch.parent!=BASE:raise RuntimeError('Scratch escaped fixture directory')
    ports=[]
    try:
        request_message=build_request('tenant-a','job-1','hello')
        wire=tasks_v2.CreateTaskRequest.serialize(request_message)
        restored=tasks_v2.CreateTaskRequest.deserialize(wire)
        sdk_json=json.loads(tasks_v2.CreateTaskRequest.to_json(restored))
        (BASE/'task-request.json').write_text(json.dumps(sdk_json,indent=2)+'\n',encoding='utf-8')
        check('sdk','protobuf_body_roundtrip',json.loads(restored.task.http_request.body)=={'tenant_id':'tenant-a','job_id':'job-1','value':'hello'})
        check('sdk','json_wire_body_is_base64_once',json.loads(base64.b64decode(sdk_json['task']['httpRequest']['body']))['value']=='hello')
        check('sdk','stable_task_name_for_same_job',build_request('tenant-a','job-1','hello').task.name==restored.task.name)
        check('sdk','tenant_scoped_task_names',build_request('tenant-b','job-1','hello').task.name!=restored.task.name)
        check('sdk','explicit_audience_and_identity',restored.task.http_request.oidc_token.audience==AUDIENCE and restored.task.http_request.oidc_token.service_account_email==SERVICE_ACCOUNT)
        check('sdk','post_and_dispatch_deadline',restored.task.http_request.http_method==tasks_v2.HttpMethod.POST and restored.task.dispatch_deadline.total_seconds()==30)
        check('sdk','insecure_target_rejected',rejected(lambda:build_request('tenant-a','job-1','hello',target='http://worker.example.test/tasks/import')))
        check('sdk','query_audience_rejected_by_worker_contract',rejected(lambda:build_request('tenant-a','job-1','hello',audience=AUDIENCE+'?token=x')))
        check('sdk','bounded_payload_contract',rejected(lambda:build_request('tenant-a','job-1',False)))
        observations['sdk']={'task_name':restored.task.name,'audience':AUDIENCE,'body':json.loads(restored.task.http_request.body),'wire_bytes':len(wire),'api_called':False}

        check('auth','valid_signed_fixture_identity',authenticate(valid_token)['email']==SERVICE_ACCOUNT)
        denied=(AuthenticationError,AuthorizationError)
        check('auth','untrusted_signature_rejected',rejected(lambda:authenticate(token(key=other_signer)),denied))
        parts=valid_token.split('.')
        forged={**claims,'email':'attacker@example.test'}
        parts[1]=base64.urlsafe_b64encode(json.dumps(forged).encode()).rstrip(b'=').decode()
        check('auth','tampered_payload_rejected',rejected(lambda:authenticate('.'.join(parts)),denied))
        for name,changes in [
            ('wrong_audience',{'aud':'https://other.example.test'}),('wrong_issuer',{'iss':'https://issuer.example.test'}),
            ('expired',{'iat':now-500,'exp':now-100}),('future_issued_at',{'iat':now+300}),
            ('unauthorized_service_account',{'email':'other@placement-fixture.iam.gserviceaccount.com'}),
            ('unverified_email',{'email_verified':False}),
        ]:check('auth',name+'_rejected',rejected(lambda:authenticate(token(changes)),denied))
        unknown_token=token(key=unknown_signer)
        check('auth','unknown_key_id_rejected',jwt.decode_header(unknown_token)['kid']=='unknown' and rejected(lambda:authenticate(unknown_token),denied))
        no_iat=dict(claims);no_iat.pop('iat')
        check('auth','missing_iat_rejected',rejected(lambda:authenticate(jwt.encode(signer,no_iat).decode()),denied))
        check('auth','missing_bearer_rejected',rejected(lambda:verifier.verify(None),denied))
        unsigned=base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b'=').decode()+'.'+valid_token.split('.')[1]+'.'
        check('auth','unsigned_algorithm_rejected',rejected(lambda:authenticate(unsigned),denied))
        check('auth','malformed_token_rejected',rejected(lambda:authenticate('invalid-token'),denied))
        observations['authentication']={'signature':'RS256','trusted_key_source':'in-memory generated fixture public key',
                                         'google_token_issued':False,'google_certificates_fetched':False,'expected_caller':SERVICE_ACCOUNT}

        store=Store(scratch/'jobs.sqlite3')
        for tenant,job,value in [('tenant-a','job-1','hello'),('tenant-a','job-before','before'),
                                 ('tenant-a','job-after','after'),('tenant-a','job-concurrent','concurrent'),('tenant-b','job-1','other-tenant')]:
            store.seed(tenant,job,value)
        worker_port=start(make_server(store,verifier));ports.append(worker_port)
        payload=lambda job,value,tenant='tenant-a':json.dumps({'tenant_id':tenant,'job_id':job,'value':value}).encode()
        post=lambda body,headers=auth:request(worker_port,'/tasks/import',data=body,headers=headers)
        check('worker','spoofed_task_headers_do_not_authenticate',post(payload('job-1','hello'),{'X-CloudTasks-TaskName':'fake','Content-Type':'application/json'})[0]==401)
        check('worker','signed_wrong_caller_forbidden',post(payload('job-1','hello'),{'Authorization':'Bearer '+token({'email':'other@example.test'})})[0]==403)
        first=post(payload('job-1','hello'));replay=post(payload('job-1','hello'))
        check('worker','first_delivery_commits_before_success',first[0]==201 and ('tenant-a','job-1','hello') in store.effects())
        check('worker','same_job_replays_without_extra_effect',replay[0]==200 and len([r for r in store.effects() if r[:2]==('tenant-a','job-1')])==1)
        check('worker','changed_payload_conflicts',post(payload('job-1','changed'))[0]==409)
        check('worker','wrong_tenant_cannot_select_job',post(payload('job-before','before','tenant-b'))[0]==404)
        check('worker','unknown_job_rejected',post(payload('unknown','hello'))[0]==404)
        check('worker','malformed_json_rejected',post(b'{')[0]==400)
        check('worker','unexpected_fields_rejected',post(b'{"job_id":"job-1"}')[0]==400)
        check('worker','oversized_body_rejected',post(b'x'*4097)[0]==413)
        check('worker','wrong_method_rejected',request(worker_port,'/tasks/import')[0]==405)
        store.faults[('tenant-a','job-before')]='before_commit'
        before=post(payload('job-before','before'))
        empty_before=not any(r[:2]==('tenant-a','job-before') for r in store.effects())
        retry_before=post(payload('job-before','before'))
        check('worker','precommit_failure_retry_applies_once',before[0]==503 and empty_before and retry_before[0]==201)
        store.faults[('tenant-a','job-after')]='after_commit'
        after=post(payload('job-after','after'));retry_after=post(payload('job-after','after'))
        check('worker','postcommit_failed_ack_retry_replays',after[0]==503 and retry_after[0]==200 and len([r for r in store.effects() if r[:2]==('tenant-a','job-after')])==1)
        with ThreadPoolExecutor(max_workers=8) as pool:
            concurrent=list(pool.map(lambda _:post(payload('job-concurrent','concurrent'))[0],range(16)))
        check('worker','concurrent_duplicates_have_one_effect',concurrent.count(201)==1 and concurrent.count(200)==15 and len([r for r in store.effects() if r[:2]==('tenant-a','job-concurrent')])==1,dict(collections.Counter(concurrent)))
        other=post(payload('job-1','other-tenant','tenant-b'))
        check('worker','same_job_id_distinct_tenant_is_separate',other[0]==201 and len([r for r in store.effects() if r[1]=='job-1'])==2)
        worker=servers.pop(0);thread=threads.pop(0)
        worker.shutdown();worker.server_close();thread.join()
        reopened=Store(scratch/'jobs.sqlite3');new_port=start(make_server(reopened,verifier));ports.append(new_port)
        persisted=request(new_port,'/tasks/import',data=payload('job-1','hello'),headers=auth)
        check('worker','recreated_http_worker_replays_persisted_result',persisted[0]==200 and len(reopened.effects())==5)
        observations['delivery']={'first':first[0],'replay':replay[0],'before_commit_attempts':[before[0],retry_before[0]],
                                  'after_commit_attempts':[after[0],retry_after[0]],'concurrent_status_counts':dict(collections.Counter(concurrent)),
                                  'effects':reopened.effects(),'recreated_worker_status':persisted[0]}

        mode={'version':'v1','control':'public, max-age=30','vary':'Accept-Language','cookie':False,'status':200,'calls':0}
        class Origin(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                mode['calls']+=1
                body=json.dumps({'path':self.path,'version':mode['version'],'call':mode['calls'],
                                 'language':self.headers.get('Accept-Language',''),
                                 'identity':self.headers.get('Authorization') or self.headers.get('Cookie')}).encode()
                self.send_response(mode['status']);self.send_header('Content-Type','application/json')
                self.send_header('Cache-Control',mode['control']);self.send_header('Vary',mode['vary'])
                if mode['cookie']:self.send_header('Set-Cookie','fixture=public-example')
                self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        origin_port=start(ThreadingHTTPServer(('127.0.0.1',0),Origin));ports.append(origin_port)
        clock=[100.0];cache=PublicCache(lambda:clock[0])
        def fetch_origin(path,headers):
            req=urllib.request.Request('http://127.0.0.1:'+str(origin_port)+path,headers=headers)
            try:response=opener.open(req,timeout=5)
            except urllib.error.HTTPError as error:response=error
            with response:return response.status,dict(response.headers),response.read()
        class Edge(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                status,headers,body,state=cache.fetch(self.path,dict(self.headers),fetch_origin)
                self.send_response(status)
                for key,value in headers.items():
                    if key.lower() not in ('content-length','date','server'):self.send_header(key,value)
                self.send_header('X-Fixture-Cache',state);self.send_header('Content-Length',str(len(body)))
                self.end_headers();self.wfile.write(body)
        edge_port=start(ThreadingHTTPServer(('127.0.0.1',0),Edge));ports.append(edge_port)
        a=request(edge_port,'/public?lang=en');b=request(edge_port,'/public?lang=en')
        check('cache','anonymous_hit_skips_real_origin',a[1]['X-Fixture-Cache']=='MISS' and b[1]['X-Fixture-Cache']=='HIT' and a[2]['call']==b[2]['call'])
        es=request(edge_port,'/public?lang=es')
        check('cache','query_variant_is_separate',es[1]['X-Fixture-Cache']=='MISS' and es[2]['path']=='/public?lang=es')
        language=request(edge_port,'/public?lang=en',headers={'Accept-Language':'fr'})
        check('cache','vary_header_variant_is_separate',language[1]['X-Fixture-Cache']=='MISS' and language[2]['language']=='fr')
        alice=request(edge_port,'/public?lang=en',headers={'Authorization':'Bearer fixture-alice'})
        bob=request(edge_port,'/public?lang=en',headers={'Authorization':'Bearer fixture-bob'})
        check('cache','authorization_bypasses_shared_cache',alice[1]['X-Fixture-Cache']==bob[1]['X-Fixture-Cache']=='BYPASS' and alice[2]['identity']!=bob[2]['identity'])
        cookie=request(edge_port,'/public?lang=en',headers={'Cookie':'fixture-user=alice'})
        check('cache','cookie_request_bypasses_shared_cache',cookie[1]['X-Fixture-Cache']=='BYPASS')
        private=request(edge_port,'/private')
        check('cache','unlisted_route_bypasses_cache',private[1]['X-Fixture-Cache']=='BYPASS')
        unknown=request(edge_port,'/public?tenant=tenant-a')
        check('cache','unlisted_query_bypasses_cache',unknown[1]['X-Fixture-Cache']=='BYPASS')
        for label,control in [('no_store','no-store'),('private','private, max-age=30')]:
            cache.invalidate_public();mode['control']=control
            one=request(edge_port,'/public');two=request(edge_port,'/public')
            check('cache',label+'_response_not_stored',one[1]['X-Fixture-Cache']==two[1]['X-Fixture-Cache']=='BYPASS' and one[2]['call']!=two[2]['call'])
        mode['control']='public, max-age=30';mode['cookie']=True;cache.invalidate_public()
        check('cache','set_cookie_response_not_stored',request(edge_port,'/public')[1]['X-Fixture-Cache']=='BYPASS')
        mode['cookie']=False;mode['status']=503;cache.invalidate_public()
        check('cache','error_response_not_stored',request(edge_port,'/public')[1]['X-Fixture-Cache']=='BYPASS')
        mode['status']=200;mode['vary']='X-Unmodeled';cache.invalidate_public()
        check('cache','unmodeled_vary_response_not_stored',request(edge_port,'/public')[1]['X-Fixture-Cache']=='BYPASS')
        mode['vary']='Accept-Language';cache.invalidate_public()
        old=request(edge_port,'/public');mode['version']='v2'
        stale=request(edge_port,'/public');clock[0]+=31;fresh=request(edge_port,'/public')
        check('cache','ttl_bounds_stale_version',old[2]['version']==stale[2]['version']=='v1' and stale[1]['X-Fixture-Cache']=='HIT' and fresh[2]['version']=='v2' and fresh[1]['X-Fixture-Cache']=='MISS')
        mode['version']='v3';cache.invalidate_public();invalidated=request(edge_port,'/public')
        check('cache','local_invalidation_fetches_new_version',invalidated[2]['version']=='v3' and invalidated[1]['X-Fixture-Cache']=='MISS')
        observations['cache']={'first_state':a[1]['X-Fixture-Cache'],'second_state':b[1]['X-Fixture-Cache'],
                               'same_origin_call':a[2]['call']==b[2]['call'],'stale_version':stale[2]['version'],
                               'after_expiry':fresh[2]['version'],'after_local_invalidation':invalidated[2]['version'],
                               'origin_calls':mode['calls'],'clock':'injected monotonic time; expiry advanced 31 seconds'}
    finally:
        for server in servers:server.shutdown();server.server_close()
        for thread in threads:thread.join(timeout=10)
    closed={}
    for port in ports:
        probe=socket.socket();probe.settimeout(.5);closed[str(port)]=probe.connect_ex(('127.0.0.1',port))!=0;probe.close()
    assert all(closed.values()) and all(not t.is_alive() for t in threads)

cleanup={'loopback_ports_closed':closed,'server_threads_stopped':True,'scratch_database_and_directory_removed':not scratch.exists(),
         'generated_private_keys_written_to_disk':False,'cloud_resources_created':False,'docker_started':False}
assert cleanup['scratch_database_and_directory_removed']
result={'module':18,'verified_date':'2026-10-14','python':sys.version,'os':platform.system(),
        'versions':{name:metadata.version(name) for name in ('google-auth','google-cloud-tasks','cryptography','requests')},
        'checks':checks,'total':len(checks),'counts':dict(sorted(collections.Counter(c['group'] for c in checks).items())),
        'observations':observations,'cleanup':cleanup,
        'scope':'Offline official SDK serialization and Google-auth verification against generated local trust; actual loopback HTTP and SQLite. No AWS/GCP API, live Google-issued identity, real CDN/ALB, queue delivery or cloud resources.'}
(BASE/'verification-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(BASE/'cleanup-results.json').write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
(BASE/'certificate-transport-results.json').write_text(json.dumps({'calls':len(cert_requests),'all_served_from_fixture':True,'example':cert_requests[0]},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':result['total'],'counts':result['counts'],'versions':result['versions'],'cleanup':cleanup},indent=2))
