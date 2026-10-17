"""Run inside the owned Linux fixture; no host services or credentials are used."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import collections, json, os, re, signal, socket, ssl, subprocess, time
import urllib.request, urllib.error

BASE = Path('/opt/fixture')
RUN = Path('/run/m17')
checks, commands, observations = [], [], {}
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def command(args, *, release='v1', as_node=False, success=True):
    if as_node:
        args = ['runuser', '-u', 'node', '--', 'env', 'PM2_HOME=/run/m17/pm2', 'RELEASE='+release, *args]
    result = subprocess.run(args, cwd=BASE, capture_output=True, text=True, timeout=40)
    commands.append({'args':args, 'code':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr})
    if success and result.returncode:
        raise RuntimeError(str(args)+'\n'+result.stdout+result.stderr)
    return result

def check(group, name, condition, evidence=None):
    entry = {'group':group, 'name':name, 'passed':bool(condition)}
    if evidence is not None: entry['evidence'] = evidence
    checks.append(entry)
    print(('PASS ' if condition else 'FAIL ')+group+'/'+name, flush=True)
    if not condition: raise AssertionError(name+' '+str(evidence))

def request(path, *, port=8080, data=None, headers=None, tls=None):
    req = urllib.request.Request(('https' if tls else 'http')+'://127.0.0.1:'+str(port)+path, data=data, headers=headers or {})
    client = opener if not tls else urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=tls))
    try: response = client.open(req, timeout=7)
    except urllib.error.HTTPError as error: response = error
    with response:
        body = response.read().decode('utf-8')
        try: body = json.loads(body)
        except ValueError: pass
        return {'status':response.status, 'body':body, 'headers':dict(response.headers)}

def until(fn, seconds=12):
    end, last = time.monotonic()+seconds, None
    while time.monotonic()<end:
        try:
            last=fn()
            if last: return last
        except (OSError, ValueError): pass
        time.sleep(.1)
    raise AssertionError('Condition deadline: '+str(last))

def processes():
    return json.loads(command(['pm2','jlist'],as_node=True).stdout)

def pids():
    return sorted(p['pid'] for p in processes() if p['name']=='m17-api' and p['pm2_env']['status']=='online')

def events():
    path=RUN/'logs/api-out.log'
    entries=[]
    if path.exists():
        for line in path.read_text().splitlines():
            try: entries.append(json.loads(line))
            except ValueError: pass
    return entries

def listen_check():
    ip=socket.gethostbyname(socket.gethostname())
    probe=socket.socket(); probe.settimeout(.5)
    code=probe.connect_ex((ip,9000)); probe.close()
    return {'container_ip':ip,'connect_code':code}

nginx_started=False
try:
    observations['versions'] = {
        'node':command(['node','--version']).stdout.strip(),
        'pm2':json.loads((BASE/'node_modules/pm2/package.json').read_text())['version'],
        'nginx':command(['nginx','-v']).stderr.strip(),
        'openssl':command(['openssl','version']).stdout.strip(),
        'linux':command(['uname','-sr']).stdout.strip(),
        'debian':Path('/etc/debian_version').read_text().strip(),
    }
    command(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
             '-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1',
             '-keyout',str(RUN/'tls/key.pem'),'-out',str(RUN/'tls/cert.pem')])
    (RUN/'tls/key.pem').chmod(0o600)
    config=RUN/'nginx.conf'; config.write_text((BASE/'nginx.conf').read_text())
    valid=command(['nginx','-t','-c',str(config)])
    check('nginx','configuration_valid',valid.returncode==0)
    command(['pm2','start','ecosystem.config.cjs'],as_node=True)
    until(lambda:len(pids())==2)
    command(['nginx','-c',str(config)]); nginx_started=True
    until(lambda:request('/api/ready')['status']==200)
    echo=request('/api/echo')['body']
    observations['first_echo']=echo
    check('linux','application_is_nonroot',echo['uid']==1000,echo['uid'])
    check('linux','working_directory_explicit',echo['cwd']=='/opt/fixture',echo['cwd'])
    protected=RUN/'private.txt'; protected.write_text('fixture-only'); protected.chmod(0o600)
    denied=command(['node','-e',"try{require('fs').readFileSync('/run/m17/private.txt');process.exit(2)}catch(e){console.log(e.code);process.exit(e.code==='EACCES'?0:3)}"],as_node=True)
    check('linux','mode_600_denies_other_user',denied.stdout.strip()=='EACCES')
    directory=RUN/'no-traverse'; directory.mkdir(mode=0o700)
    (directory/'public.txt').write_text('not reachable'); (directory/'public.txt').chmod(0o644)
    denied=command(['node','-e',"try{require('fs').readFileSync('/run/m17/no-traverse/public.txt');process.exit(2)}catch(e){console.log(e.code);process.exit(e.code==='EACCES'?0:3)}"],as_node=True)
    check('linux','directory_search_permission_required',denied.stdout.strip()=='EACCES')
    snapshot=command(['node','-e',"const c=require('child_process').spawn(process.execPath,['-e',\"setTimeout(()=>console.log(process.env.RELEASE),100)\"],{stdio:['ignore','pipe','inherit']});process.env.RELEASE='parent-changed';c.stdout.pipe(process.stdout)"],as_node=True,release='inherited-v1')
    check('linux','child_environment_is_snapshot',snapshot.stdout.strip()=='inherited-v1')
    bound=listen_check(); observations['loopback']=bound
    check('linux','app_not_reachable_via_container_ip',bound['connect_code']!=0,bound)

    check('nginx','static_file_served',request('/static/index.txt')['body']=='m17-static-ok\n')
    strip=request('/api/echo?x=1'); keep=request('/keep/echo?x=1')
    observations['uri_rewrite']={'strip':strip['body']['url'],'preserve':keep['body']['url']}
    check('nginx','proxy_pass_with_uri_replaces_prefix',strip['body']['url']=='/echo?x=1')
    check('nginx','proxy_pass_without_uri_preserves_path',keep['body']['url']=='/keep/echo?x=1')
    spoof=request('/api/echo',headers={'X-Forwarded-For':'203.0.113.77','X-Forwarded-Proto':'https','X-Request-ID':'client-chosen'})
    forwarded=spoof['body']['headers']; observations['forwarded_headers']=forwarded
    check('nginx','single_ingress_overwrites_forwarded_headers',forwarded['forwarded_for']=='127.0.0.1' and forwarded['forwarded_proto']=='http' and re.fullmatch('[a-f0-9]{32}',forwarded['request_id']) is not None)
    small=request('/api/echo',data=b'hello')
    check('nginx','small_request_body_reaches_app',small['status']==200 and small['body']['body']=='hello')
    large=request('/api/echo',data=b'x'*2048)
    check('nginx','body_limit_rejects_at_proxy',large['status']==413)
    missing=request('/api/missing')
    check('nginx','application_404_preserved',missing['status']==404 and missing['body']['error']=='route not found')
    timeout=request('/api/slow?ms=1500')
    check('nginx','silent_upstream_returns_504',timeout['status']==504)
    time.sleep(.6)

    trusted=ssl.create_default_context(cafile=str(RUN/'tls/cert.pem'))
    secure=request('/api/echo',port=8443,tls=trusted)
    check('tls','fixture_certificate_explicitly_trusted',secure['status']==200)
    check('tls','terminated_tls_forwarded_as_https',secure['body']['headers']['forwarded_proto']=='https')
    rejected=False
    try: request('/api/echo',port=8443,tls=ssl.create_default_context())
    except urllib.error.URLError as error: rejected=isinstance(error.reason,ssl.SSLCertVerificationError)
    check('tls','untrusted_self_signed_certificate_rejected',rejected)
    check('tls','private_key_restricted',oct((RUN/'tls/key.pem').stat().st_mode & 0o777)=='0o600')

    workers=pids(); observations['initial_workers']=workers
    check('pm2','two_distinct_cluster_workers',len(workers)==2 and len(set(workers))==2,workers)
    seen={request('/api/echo')['body']['pid'] for _ in range(20)}
    check('pm2','requests_reach_both_workers',seen==set(workers),sorted(seen))
    counters=collections.defaultdict(list)
    for _ in range(10):
        item=request('/api/counter')['body']; counters[item['pid']].append(item['counter'])
    observations['worker_counters']=dict(counters)
    check('pm2','worker_memory_is_independent',len(counters)==2 and all(values[0]==1 for values in counters.values()),dict(counters))
    killed=workers[0]; before={p['pm_id']:p['pm2_env']['restart_time'] for p in processes()}
    os.kill(killed,signal.SIGKILL)
    recovered=until(lambda:(current if len(current:=pids())==2 and killed not in current else None))
    after={p['pm_id']:p['pm2_env']['restart_time'] for p in processes()}
    check('pm2','crashed_worker_replaced',killed not in recovered and any(after[key]>before[key] for key in before),{'killed':killed,'replacement_pids':recovered})

    command(['pm2','restart','m17-api'],as_node=True,release='v2')
    preserved={request('/api/echo')['body']['release'] for _ in range(6)}
    check('pm2','restart_retains_environment_without_update',preserved=={'v1'},sorted(preserved))
    command(['pm2','restart','m17-api','--update-env'],as_node=True,release='v2')
    updated={request('/api/echo')['body']['release'] for _ in range(6)}
    check('pm2','update_env_changes_new_workers',updated=={'v2'},sorted(updated))

    before_reload=pids()
    previous_ids={e.get('id') for e in events() if e['event']=='request_start'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        long_request=pool.submit(request,'/drain/slow?ms=1600')
        start=until(lambda:next((event for event in reversed(events()) if event['event']=='request_start' and event.get('path')=='/slow' and event.get('id') not in previous_ids),None))
        reload_future=pool.submit(command,['pm2','reload','m17-api'],as_node=True,release='v2')
        samples=[]
        while not reload_future.done():
            try: samples.append(request('/api/echo')['status'])
            except OSError: samples.append(0)
            time.sleep(.05)
        reload_future.result()
        drained=long_request.result()
    after_reload=pids(); observations['reload']={'before':before_reload,'after':after_reload,'sample_statuses':samples,'drained_request':drained['body']}
    check('lifecycle','reload_replaces_all_workers',len(after_reload)==2 and not set(before_reload)&set(after_reload))
    check('lifecycle','sampled_requests_succeed_during_reload',len(samples)>0 and all(status==200 for status in samples),{'samples':len(samples),'statuses':sorted(set(samples))})
    check('lifecycle','active_request_finishes_during_reload',drained['status']==200 and drained['body']['pid'] in before_reload)
    timeline=events(); old_pid=drained['body']['pid']; reqid=start['id']
    finished=next(i for i,e in enumerate(timeline) if e['event']=='request_finish' and e.get('id')==reqid)
    stopped=next(i for i,e in enumerate(timeline) if i>finished and e['event']=='shutdown_complete' and e['pid']==old_pid)
    check('lifecycle','finish_logged_before_worker_exit',finished<stopped,{'old_pid':old_pid,'finish_index':finished,'shutdown_index':stopped})
    check('lifecycle','normal_reload_has_no_forced_shutdown',not any(e['event']=='shutdown_forced' for e in timeline))

    master=int((RUN/'nginx.pid').read_text())
    invalid=RUN/'invalid.conf'; invalid.write_text(config.read_text().replace('worker_processes 1;','unknown_directive yes;'))
    bad=command(['nginx','-t','-c',str(invalid)],success=False)
    check('nginx','invalid_candidate_rejected',bad.returncode!=0)
    check('nginx','live_config_survives_failed_validation',request('/api/echo')['status']==200 and int((RUN/'nginx.pid').read_text())==master)
    config.write_text(config.read_text().replace('X-Fixture-Release v1','X-Fixture-Release v2'))
    command(['nginx','-t','-c',str(config)]); command(['nginx','-s','reload','-c',str(config)])
    until(lambda:request('/api/echo')['headers'].get('X-Fixture-Release')=='v2')
    check('nginx','valid_reload_keeps_master_and_applies_config',int((RUN/'nginx.pid').read_text())==master)
    logtext=(RUN/'access.log').read_text()
    check('nginx','request_id_and_upstream_timing_logged',forwarded['request_id']+' 200 200 ' in logtext)
    command(['pm2','save'],as_node=True,release='v2')
    dump=json.loads((RUN/'pm2/dump.pm2').read_text())
    check('pm2','save_records_application_list',len(dump)==2 and all(p['name']=='m17-api' for p in dump))
    command(['pm2','stop','m17-api'],as_node=True,release='v2')
    check('nginx','stopped_application_returns_502',request('/api/echo')['status']==502)
    command(['pm2','delete','m17-api'],as_node=True,release='v2')
    command(['pm2','resurrect'],as_node=True,release='v2')
    until(lambda:len(pids())==2 and request('/api/ready')['status']==200)
    restored=request('/api/echo')['body']
    check('pm2','resurrect_restores_saved_processes',restored['release']=='v2' and len(pids())==2)
    observations['process_table']=command(['ps','-eo','pid,ppid,user,args']).stdout
    observations['sockets']=command(['ss','-lntp']).stdout
finally:
    command(['pm2','kill'],as_node=True,success=False)
    if nginx_started:
        command(['nginx','-s','quit','-c',str(RUN/'nginx.conf')],success=False)
    commands_path=BASE/'linux-command-output.json'
    commands_path.write_text(json.dumps(commands,indent=2)+'\n')
    for source,target in [('logs/api-out.log','application-output.txt'),('logs/api-error.log','application-error-output.txt'),('access.log','nginx-access-output.txt'),('error.log','nginx-error-output.txt')]:
        p=RUN/source
        if p.exists(): (BASE/target).write_text(p.read_text())

counts=dict(sorted(collections.Counter(c['group'] for c in checks).items()))
result={'checks':checks,'counts':counts,'total':len(checks),'observations':observations,
        'scope':'Real Linux Nginx and PM2 inside an owned Docker network namespace. No systemd boot, public DNS/CA, cloud deployment or load benchmark.'}
(BASE/'linux-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'counts':counts,'total':len(checks),'versions':observations['versions']},indent=2),flush=True)
