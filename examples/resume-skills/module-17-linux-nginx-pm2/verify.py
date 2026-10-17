"""Build, exercise and remove only a uniquely labeled Linux deployment fixture."""
from pathlib import Path
import collections, json, os, shutil, socket, ssl, subprocess, tempfile, time, uuid
import urllib.request, urllib.error

BASE=Path(__file__).resolve().parent
run_id='m17-'+uuid.uuid4().hex[:10]
image='placement-m17:'+run_id
container=run_id
label='placement.module17.run'
commands=[]
created=False
build_created=False
ports=[]
host_checks=[]
failure=None
scratch=Path(tempfile.mkdtemp(prefix='.run-',dir=BASE)).resolve()
if scratch.parent!=BASE:raise RuntimeError('Scratch escaped fixture directory')

def command(args, *, success=True, timeout=300):
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    commands.append({'args':args,'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if success and result.returncode:raise RuntimeError(str(args)+'\n'+result.stdout+result.stderr)
    return result

def inspect(kind,name):
    return json.loads(command(['docker',kind,'inspect',name]).stdout)[0]

def check(name,condition,evidence=None):
    host_checks.append({'group':'host','name':name,'passed':bool(condition),'evidence':evidence})
    if not condition:raise AssertionError(name+' '+str(evidence))

try:
    engine=json.loads(command(['docker','info','--format','{{json .}}']).stdout)
    base=inspect('image','node:22-bookworm-slim')
    digest=next(d for d in base['RepoDigests'] if d.startswith('node@'))
    build=command(['docker','build','--build-arg','NODE_IMAGE='+digest,'--label',label+'='+run_id,'-t',image,str(BASE)])
    build_created=True
    (BASE/'image-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
    command(['docker','run','-d','--init','--name',container,'--label',label+'='+run_id,
             '-p','127.0.0.1::8080','-p','127.0.0.1::8443',image])
    created=True
    details=inspect('container',container)
    bindings=details['NetworkSettings']['Ports']
    for key in ('8080/tcp','8443/tcp'):ports.append(int(bindings[key][0]['HostPort']))
    check('only_proxy_ports_published_on_loopback',set(bindings)=={'8080/tcp','8443/tcp'} and all(b['HostIp']=='127.0.0.1' for entries in bindings.values() for b in entries),bindings)
    output_path=BASE/'verification-output.txt'
    with output_path.open('w',encoding='utf-8') as output:
        worker=subprocess.Popen(['docker','exec',container,'python3','/opt/fixture/verify_linux.py'],stdout=output,stderr=subprocess.STDOUT)
        try:
            end=time.monotonic()+90
            received=False
            while time.monotonic()<end and worker.poll() is None:
                try:
                    with urllib.request.urlopen('http://127.0.0.1:'+str(ports[0])+'/static/index.txt',timeout=1) as response:
                        received=response.status==200 and response.read()==b'm17-static-ok\n'
                    if received:break
                except (OSError,urllib.error.URLError):time.sleep(.1)
            check('actual_http_through_published_proxy',received)
            command(['docker','cp',container+':/run/m17/tls/cert.pem',str(scratch/'cert.pem')])
            context=ssl.create_default_context(cafile=str(scratch/'cert.pem'))
            with urllib.request.urlopen('https://127.0.0.1:'+str(ports[1])+'/api/echo',context=context,timeout=5) as response:
                secure=json.loads(response.read())
            check('actual_tls_through_published_proxy',secure['headers']['forwarded_proto']=='https',secure['headers'])
            if worker.wait(timeout=120):raise RuntimeError(output_path.read_text(encoding='utf-8'))
        finally:
            if worker.poll() is None:worker.terminate();worker.wait(timeout=10)
    linux=json.loads(command(['docker','exec',container,'cat','/opt/fixture/linux-results.json']).stdout)
    for name in ('linux-results.json','linux-command-output.json','application-output.txt','application-error-output.txt','nginx-access-output.txt','nginx-error-output.txt'):
        command(['docker','cp',container+':/opt/fixture/'+name,str(BASE/name)])
    checks=linux['checks']+host_checks
    proof={'run_id':run_id,'verified_date':'2026-10-14','checks':checks,
           'counts':dict(sorted(collections.Counter(c['group'] for c in checks).items())),
           'total':len(checks),'observations':linux['observations'],
           'docker':{'client':command(['docker','version','--format','{{.Client.Version}}']).stdout.strip(),
                     'engine':engine['ServerVersion'],'base_image':digest,'published_ports':ports},'scope':linux['scope']}
except BaseException as error:
    failure=error
finally:
    if created:
        details=inspect('container',container)
        if details['Config']['Labels'].get(label)!=run_id:raise RuntimeError('Container ownership mismatch')
        if failure:
            for name in ('linux-command-output.json','application-output.txt','application-error-output.txt','nginx-access-output.txt','nginx-error-output.txt'):
                command(['docker','cp',container+':/opt/fixture/'+name,str(BASE/name)],success=False)
        command(['docker','rm','-f',container])
    if build_created:
        details=inspect('image',image)
        if details['Config']['Labels'].get(label)!=run_id:raise RuntimeError('Image ownership mismatch')
        command(['docker','image','rm',image])
    shutil.rmtree(scratch)
    container_absent=not command(['docker','ps','-aq','--filter','label='+label+'='+run_id]).stdout.strip()
    image_absent=not command(['docker','images','-q','--filter','label='+label+'='+run_id]).stdout.strip()
    ports_closed={}
    for port in ports:
        probe=socket.socket();probe.settimeout(.5)
        ports_closed[str(port)]=probe.connect_ex(('127.0.0.1',port))!=0;probe.close()
    cleanup={'container_removed':container_absent,'owned_image_removed':image_absent,'scratch_removed':not scratch.exists(),
             'ports_closed':ports_closed,'public_base_image_and_build_cache_retained':True}
    (BASE/'cleanup-results.json').write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
    (BASE/'docker-command-output.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
if failure:raise failure
if not (container_absent and image_absent and all(ports_closed.values())):raise RuntimeError('Fixture cleanup incomplete')
proof['cleanup']=cleanup
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':proof['total'],'counts':proof['counts'],'versions':proof['observations']['versions'],'cleanup':cleanup},indent=2))
