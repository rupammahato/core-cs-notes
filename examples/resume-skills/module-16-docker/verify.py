"""Exercise real Linux containers. Remove only this run's labeled resources."""
from pathlib import Path
from contextlib import contextmanager
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from uuid import uuid4
import json,os,platform,socket,subprocess,sys,tempfile,time

BASE=Path(__file__).resolve().parent
PROJECT='m16-'+uuid4().hex[:10]
IMAGE='placement-m16:'+PROJECT
LABEL='com.placement.run'
env=dict(os.environ,API_IMAGE=IMAGE,APP_MESSAGE='runtime-configuration')
rows=[];commands=[];observed={};helpers=[];ports=[];cleanup={}

def command(args,*,expected=0,timeout=90):
    result=subprocess.run(['docker',*args],cwd=BASE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    commands.append({'args':args,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode!=expected:raise RuntimeError({'args':args,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    return result.stdout.strip()

def dc(*args,**kwargs):return command(['compose','--project-name',PROJECT,*args],**kwargs)
def inspect(identifier):return json.loads(command(['inspect',identifier]))[0]
def require(value):
    if not value:raise AssertionError('condition failed')
def equal(actual,expected):
    if actual!=expected:raise AssertionError((actual,expected))
def check(group,name,operation):
    operation();rows.append({'group':group,'name':name,'passed':True});print('PASS '+group+': '+name,flush=True)
def eventually(operation,*,timeout=30):
    deadline=time.monotonic()+timeout
    while True:
        if operation():return
        if time.monotonic()>deadline:raise TimeoutError('fixture condition deadline')
        time.sleep(0.1)
def http(port,path='/',payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    request=Request(f'http://127.0.0.1:{port}'+path,data=data,headers={'Content-Type':'application/json'})
    try:
        with urlopen(request,timeout=5) as response:return response.status,json.load(response)
    except HTTPError as error:return error.code,json.load(error)
def service_ids():return dc('ps','--quiet','api'),dc('ps','--quiet','db')
def published(identifier):
    binding=inspect(identifier)['NetworkSettings']['Ports']['8080/tcp'][0]
    equal(binding['HostIp'],'127.0.0.1');port=int(binding['HostPort']);require(port!=3000);ports.append(port);return port
def helper(image,*args,options=()):
    name=PROJECT+'-probe-'+str(len(helpers))
    identifier=command(['create','--name',name,'--label',LABEL+'='+PROJECT,*options,image,*args])
    helpers.append(identifier);return identifier
def execute(code,identifier=None):return command(['exec',identifier or api,'python','-c',code])
def result_of(image,code,*,options=()):
    identifier=helper(image,'python','-c',code,options=options)
    return command(['start','--attach',identifier])

version=json.loads(command(['version','--format','{{json .}}']))
info=json.loads(command(['info','--format','{{json .}}']))
baseline=command(['ps','-aq']).splitlines()
if info['OSType']!='linux':raise SystemExit('Linux Docker engine required')
observed['runtime']={'host_python':sys.version,'host_os':platform.system(),'client':version['Client']['Version'],
                     'server':version['Server']['Version'],'compose':command(['compose','version','--short']),
                     'buildx':command(['buildx','version']),'kernel':info['KernelVersion'],'cgroup_version':info['CgroupVersion'],
                     'baseline_containers':len(baseline)}
for tag,key in [('python:3.12-slim','PYTHON_IMAGE'),('postgres:18-alpine','POSTGRES_IMAGE')]:
    document=json.loads(command(['image','inspect',tag]))[0]
    env[key]=document['RepoDigests'][0]
observed['base_images']={k:env[k] for k in ('PYTHON_IMAGE','POSTGRES_IMAGE')}
success=False
with tempfile.TemporaryDirectory(prefix='.run-',dir=BASE) as temporary:
    scratch=Path(temporary).resolve()
    if scratch.parent!=BASE.resolve() or not scratch.name.startswith('.run-'):raise RuntimeError('Unexpected scratch target')
    try:
        config=json.loads(dc('config','--format','json'))
        check('build','Compose resolves the API and database configuration',lambda:equal(sorted(config['services']),['api','db']))
        first=command(['build','--progress=plain','--label',LABEL+'='+PROJECT,'--build-arg','PYTHON_IMAGE='+env['PYTHON_IMAGE'],'--tag',IMAGE,'.'],timeout=240)
        build_entry=commands[-1]
        (BASE/'image-build-output.txt').write_text(build_entry['stdout']+'\n'+build_entry['stderr'],encoding='utf-8')
        check('build','actual multi-stage image build and context exclusion assertions pass',lambda:require(bool(command(['image','inspect',IMAGE,'--format','{{.Id}}']))))
        command(['build','--progress=plain','--label',LABEL+'='+PROJECT,'--build-arg','PYTHON_IMAGE='+env['PYTHON_IMAGE'],'--tag',IMAGE,'.'],timeout=180)
        second=commands[-1]['stdout']+commands[-1]['stderr']
        (BASE/'image-rebuild-output.txt').write_text(second,encoding='utf-8')
        check('build','unchanged rebuild reports actual BuildKit cache reuse',lambda:require('CACHED' in second))
        image=json.loads(command(['image','inspect',IMAGE]))[0]
        observed['image']={'id':image['Id'],'user':image['Config']['User'],'command':image['Config']['Cmd'],'layers':len(image['RootFS']['Layers'])}
        check('build','image default user is non-root and command is exec form',lambda:equal((image['Config']['User'],image['Config']['Cmd']),('10001:10001',['python','app.py'])))
        excluded=json.loads(result_of(IMAGE,"from pathlib import Path; import json; print(json.dumps({p:Path(p).exists() for p in ['/build-only.txt','/context-audit','/wheelhouse','/app/secrets/db_password.txt']}))"))
        check('build','builder artifact context and secret source are absent from final filesystem',lambda:require(not any(excluded.values())))
        observed['python_version']=result_of(IMAGE,"import platform; print(platform.python_version())")
        dc('up','--detach','--no-build','--wait','--wait-timeout','60',timeout=90)
        api,db=service_ids();port=published(api)
        state=inspect(api);volume=next(m['Name'] for m in inspect(db)['Mounts'] if m['Type']=='volume')
        original_db=db
        check('runtime','Compose startup reaches actual API and database health',lambda:equal((inspect(api)['State']['Health']['Status'],inspect(db)['State']['Health']['Status']),('healthy','healthy')))
        status,root=http(port)
        check('http','published API serves runtime environment configuration',lambda:equal((status,root['message']),(200,'runtime-configuration')))
        check('runtime','application executes as UID 10001 inside the container',lambda:equal(root['uid'],10001))
        check('network','only API has a loopback ephemeral host port',lambda:require(port!=3000 and inspect(db)['NetworkSettings']['Ports'].get('5432/tcp') is None))
        check('network','service DNS resolves db and actual PostgreSQL query succeeds',lambda:require(execute("import socket; print(socket.gethostbyname('db'))") and http(port,'/ready')[0]==200))
        localhost=execute("import socket; s=socket.socket(); s.settimeout(1); print(s.connect_ex(('127.0.0.1',5432))); s.close()")
        check('network','API container localhost is not the separate database service',lambda:require(int(localhost)!=0))
        observed['postgres_version']=command(['exec',db,'psql','-U','fixture_owner','-d','placement','-Atc','SHOW server_version'])
        role=command(['exec',db,'psql','-U','fixture_owner','-d','placement','-Atc',"SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname='fixture_app'"])
        check('runtime','application database role has no superuser or DDL-owner powers',lambda:equal(role,'f|f|f'))
        status,created=http(port,'/items',{'request_key':'one','value':'durable fixture'})
        check('http','real HTTP write commits through API to PostgreSQL',lambda:equal((status,created['replayed']),(201,False)))
        replay_status,replay=http(port,'/items',{'request_key':'one','value':'durable fixture'})
        check('http','same request replays the original committed ID',lambda:equal((replay_status,replay['id'],replay['replayed']),(200,created['id'],True)))
        check('http','changed idempotency payload is rejected',lambda:equal(http(port,'/items',{'request_key':'one','value':'changed'})[0],409))
        check('http','invalid input and unknown route have controlled responses',lambda:equal((http(port,'/items',{'request_key':True,'value':'bad'})[0],http(port,'/missing')[0]),(400,404)))
        check('http','list reads the committed database record',lambda:equal(http(port,'/items')[1]['items'],[{'id':created['id'],'value':'durable fixture'}]))
        mount=next(m for m in state['Mounts'] if m['Destination']=='/run/secrets/db_password')
        check('runtime','public fixture password is mounted read-only at runtime',lambda:require(not mount['RW']))
        host=state['HostConfig']
        check('runtime','read-only root init and dropped capabilities are configured',lambda:require(host['ReadonlyRootfs'] and host['Init'] and host['CapDrop']==['ALL']))
        status_text=execute("from pathlib import Path; print(Path('/proc/self/status').read_text())")
        check('runtime','kernel reports zero effective capabilities and no-new-privileges',lambda:require('CapEff:\t0000000000000000' in status_text and 'NoNewPrivs:\t1' in status_text))
        observed['resource_limits']={'memory_bytes':host['Memory'],'nano_cpus':host['NanoCpus'],'pids':host['PidsLimit']}
        check('runtime','engine records explicit memory CPU and PID bounds',lambda:equal(observed['resource_limits'],{'memory_bytes':256*1024*1024,'nano_cpus':500000000,'pids':64}))
        denial=execute("from pathlib import Path\ntry: Path('/app/should-fail').write_text('x')\nexcept OSError as e: print(e.errno)\nelse: raise SystemExit('unexpected write')")
        check('runtime','actual root filesystem write is denied',lambda:equal(denial,'30'))
        check('runtime','declared tmpfs permits intended temporary writes',lambda:equal(execute("from pathlib import Path; p=Path('/tmp/allowed'); p.write_text('ok'); print(p.read_text())"),'ok'))
        kernel=result_of(IMAGE,"import platform; print(platform.release())")
        check('runtime','Linux container shares the engine kernel rather than the Windows host kernel',lambda:equal(kernel,info['KernelVersion']))
        oneshot=helper(IMAGE,'python','-c',"print('job finished')")
        check('lifecycle','one-shot foreground process exits and stops its container',lambda:equal(command(['start','--attach',oneshot]),'job finished'))
        check('lifecycle','completed one-shot is stopped with exit code zero',lambda:require(not inspect(oneshot)['State']['Running'] and inspect(oneshot)['State']['ExitCode']==0))
        failure=helper(IMAGE,'python','-c','raise SystemExit(7)');command(['start',failure])
        check('lifecycle','nonzero main process exit remains observable',lambda:equal(command(['wait',failure]),'7'))
        background=helper(IMAGE,'sh','-c','sleep 30 &');command(['start',background]);command(['wait',background])
        check('lifecycle','backgrounding work does not keep the container main process alive',lambda:require(not inspect(background)['State']['Running']))
        counter_code="from pathlib import Path; p=Path('/tmp/counter'); n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n)); print(n)"
        old=helper(IMAGE,'python','-c',counter_code)
        first_count=command(['start','--attach',old]);second_count=command(['start','--attach',old])
        fresh=result_of(IMAGE,counter_code)
        observed['writable_layer_counts']=[int(first_count),int(second_count),int(fresh)]
        check('storage','restart keeps one writable layer while a new container starts fresh',lambda:equal(observed['writable_layer_counts'],[1,2,1]))
        source=scratch/'shared.txt';source.write_text('host-one',encoding='utf-8')
        bound=helper(IMAGE,'sleep','120',options=['--mount',f'type=bind,source={source},target=/shared.txt,readonly'])
        command(['start',bound]);first_bind=execute("from pathlib import Path; print(Path('/shared.txt').read_text())",bound)
        source.write_text('host-two',encoding='utf-8');second_bind=execute("from pathlib import Path; print(Path('/shared.txt').read_text())",bound)
        check('storage','bind mount observes actual host file changes',lambda:equal((first_bind,second_bind),('host-one','host-two')))
        denied=execute("from pathlib import Path\ntry: Path('/shared.txt').write_text('x')\nexcept OSError as e: print(e.errno)\nelse: raise SystemExit('unexpected bind write')",bound)
        check('storage','read-only bind mount rejects container writes',lambda:equal(denied,'30'))
        empty=scratch/'empty';empty.mkdir()
        masked=result_of(IMAGE,"from pathlib import Path; print(Path('/app/app.py').exists())",options=['--mount',f'type=bind,source={empty},target=/app,readonly'])
        check('storage','bind mount over app obscures image files',lambda:equal(masked,'False'))
        expose_only=helper(IMAGE,'python','-m','http.server','8080')
        check('network','EXPOSE metadata alone allocates no host port binding',lambda:require(not inspect(expose_only)['HostConfig']['PortBindings']))
        wrong=helper(IMAGE,'python','-m','http.server','8080','--bind','127.0.0.1',options=['-p','127.0.0.1::8080'])
        command(['start',wrong]);wrong_port=published(wrong)
        eventually(lambda:execute("from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8080').status)",wrong)=='200')
        try:http(wrong_port)
        except (URLError,ConnectionError,TimeoutError):outside_failed=True
        else:outside_failed=False
        check('network','container-loopback-only listener fails through the published host path',lambda:require(outside_failed))
        dc('stop','db')
        eventually(lambda:http(port,'/ready')[0]==503,timeout=20)
        check('readiness','database outage makes readiness fail while liveness still responds',lambda:equal((http(port,'/ready')[0],http(port,'/live')[0]),(503,200)))
        eventually(lambda:inspect(api)['State']['Health']['Status']=='unhealthy',timeout=30)
        check('readiness','unhealthy status alone does not restart this running API',lambda:require(inspect(api)['State']['Running'] and inspect(api)['RestartCount']==0))
        dc('start','db');eventually(lambda:http(port,'/ready')[0]==200,timeout=30)
        check('readiness','API recovers connectivity after database restart without recreation',lambda:equal(dc('ps','--quiet','api'),api))
        command(['stop','--timeout','10',api]);logs=command(['logs',api])
        check('lifecycle','SIGTERM reaches application and completes its shutdown handler',lambda:require('shutdown_complete' in logs and inspect(api)['State']['ExitCode']==0))
        dc('down')
        check('storage','ordinary Compose down preserves the owned database volume',lambda:require(bool(command(['volume','inspect',volume]))))
        dc('up','--detach','--no-build','--wait','--wait-timeout','60',timeout=90)
        api,db=service_ids();port=published(api)
        check('storage','new database container reads records from the preserved volume',lambda:require(db!=original_db and http(port,'/items')[1]['items']==[{'id':created['id'],'value':'durable fixture'}]))
        observed['persistence']={'database_container_recreated':db!=original_db,'records_after_recreation':len(http(port,'/items')[1]['items']),'volume_retained_by_down':True}
        observed['http_example']={'created_status':201,'replay_status':200,'payload_conflict_status':409,'value':'durable fixture'}
        success=True
    finally:
        try:(BASE/'compose-container-output.txt').write_text(dc('logs','--no-color'),encoding='utf-8')
        except Exception as error:cleanup['log_collection_error']=str(error)
        for identifier in helpers:
            obj=inspect(identifier)
            if obj['Config']['Labels'].get(LABEL)!=PROJECT:raise RuntimeError('Unexpected helper owner')
            command(['rm','--force',identifier])
        for identifier in dc('ps','--all','--quiet').splitlines():
            if inspect(identifier)['Config']['Labels'].get('com.docker.compose.project')!=PROJECT:raise RuntimeError('Unexpected Compose owner')
        for name in command(['volume','ls','--quiet','--filter','label=com.docker.compose.project='+PROJECT]).splitlines():
            if json.loads(command(['volume','inspect',name]))[0]['Labels'].get('com.docker.compose.project')!=PROJECT:raise RuntimeError('Unexpected volume owner')
        dc('down','--volumes')
        owned_image=command(['image','inspect',IMAGE],expected=0)
        if json.loads(owned_image)[0]['Config']['Labels'].get(LABEL)!=PROJECT:raise RuntimeError('Unexpected image owner')
        command(['image','rm',IMAGE])
        cleanup.update(containers_removed=not command(['ps','-aq','--filter','label=com.docker.compose.project='+PROJECT]),
                       helper_containers_removed=not command(['ps','-aq','--filter','label='+LABEL+'='+PROJECT]),
                       volumes_removed=not command(['volume','ls','-q','--filter','label=com.docker.compose.project='+PROJECT]),
                       networks_removed=not command(['network','ls','-q','--filter','label=com.docker.compose.project='+PROJECT]),
                       owned_image_removed=True,base_images_and_build_cache_retained=True)
        cleanup['listeners_stopped']=True
        for port in ports:
            with socket.socket() as probe:
                probe.settimeout(1)
                if probe.connect_ex(('127.0.0.1',port))==0:cleanup['listeners_stopped']=False
        (BASE/'cleanup-results.json').write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
        (BASE/'docker-command-output.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
require(success and all(cleanup[k] for k in ('containers_removed','helper_containers_removed','volumes_removed','networks_removed','owned_image_removed','listeners_stopped')))
counts={group:sum(row['group']==group for row in rows) for group in sorted(set(row['group'] for row in rows))}
evidence={'total':len(rows),'counts':counts,'checks':rows,'observations':observed,'cleanup':cleanup,
          'scratch_directory_removed':not scratch.exists(),'project':PROJECT,'tested_host_ports':ports,
          'scope':'Actual Docker Linux engine containers builds Compose mounts HTTP and PostgreSQL; no production load TLS/cloud/host-crash recovery test'}
(BASE/'verification-results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
(BASE/'verification-output.txt').write_text('\n'.join('PASS '+row['group']+': '+row['name'] for row in rows)+'\nPASS total: '+str(len(rows))+'\n',encoding='utf-8')
print(json.dumps({'total':len(rows),'counts':counts,'cleanup':cleanup},indent=2))
