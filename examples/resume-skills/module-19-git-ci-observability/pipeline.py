"""Exercise real local gates and owned candidate processes; no external deployment."""
from pathlib import Path
import json,os,queue,shutil,socket,subprocess,threading,urllib.request
from release import FILES,package,extract_verified,promote

BASE=Path(__file__).resolve().parent
NODE=shutil.which('node')

def run_pipeline_lab(scratch,revision):
    checks=[];commands=[];runs=[];ports=[]
    pointer=scratch/'current.json'
    def check(name,condition,evidence=None):
        checks.append({'group':'pipeline','name':name,'passed':bool(condition),'evidence':evidence})
        if not condition:raise AssertionError(name)
    def run(args,cwd=BASE):
        result=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',timeout=30)
        commands.append({'args':args,'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        result.check_returncode();return result
    def gate(stages):
        events=[]
        for name,fn in stages:
            try:fn();events.append({'stage':name,'status':'passed'})
            except Exception as error:
                events.append({'stage':name,'status':'failed','error_type':type(error).__name__});break
        runs.append(events);return events
    def smoke(candidate,release,unhealthy=False):
        env=dict(os.environ,RELEASE=release,FIXTURE_UNHEALTHY='1' if unhealthy else '0')
        child=subprocess.Popen([NODE,str(candidate/'serve.mjs')],cwd=candidate,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        output=queue.Queue()
        def read_ready():output.put(child.stdout.readline())
        reader=threading.Thread(target=read_ready);reader.start()
        ready=None;stderr=''
        try:
            line=output.get(timeout=10);ready=json.loads(line)
            if ready.get('event')!='ready':raise RuntimeError('Candidate did not become listen-ready')
            ports.extend([ready['port'],ready['dependency_port']])
            with urllib.request.urlopen('http://127.0.0.1:'+str(ready['port'])+'/health',timeout=3) as response:
                body=json.loads(response.read())
                if response.status!=200 or body!={'ready':True,'release':release}:raise RuntimeError('Candidate health mismatch')
            with urllib.request.urlopen('http://127.0.0.1:'+str(ready['port'])+'/work?delay=1',timeout=3) as response:
                body=json.loads(response.read())
                if response.status!=200 or body.get('release')!=release or body.get('result')!='computed':raise RuntimeError('Candidate useful route failed')
        finally:
            if child.poll() is None:
                child.stdin.write('stop\n');child.stdin.flush()
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
            reader.join(timeout=2)
            stderr=child.stderr.read()
            commands.append({'candidate':candidate.name,'ready':ready,'exit_code':child.returncode,'stderr':stderr})
            child.stdin.close();child.stdout.close();child.stderr.close()
            if child.returncode!=0:raise RuntimeError('Candidate shutdown failed')
    syntax=gate([('syntax',lambda:[run([NODE,'--check',name]) for name in FILES if name.endswith('.mjs')])])
    check('syntax_gate_executes_successfully',syntax[-1]['status']=='passed')
    contracts=run([NODE,'--test','contract.test.mjs'])
    (BASE/'contract-test-output.txt').write_text(contracts.stdout+'\n'+contracts.stderr,encoding='utf-8')
    check('real_http_contract_suite_passes','# pass 3' in contracts.stdout and '# fail 0' in contracts.stdout)
    v1=scratch/'release-v1.zip';m1,h1=package(BASE,v1,revision,'v1')
    c1=scratch/'candidate-v1';extract_verified(v1,h1,c1)
    smoke(c1,'v1');promote(pointer,m1,h1)
    check('known_good_release_smoked_before_selection',json.loads(pointer.read_text())['release']=='v1')
    before=pointer.read_bytes()
    failure=scratch/'intentional-failure.test.mjs'
    failure.write_text("import {test} from 'node:test';import assert from 'node:assert/strict';test('intentional gate failure',()=>assert.equal(1,2));\n")
    blocked_artifact=scratch/'must-not-exist.zip'
    blocked=gate([('test',lambda:run([NODE,'--test',str(failure)])),('package',lambda:package(BASE,blocked_artifact,revision,'broken'))])
    check('failed_test_gate_blocks_packaging',blocked==[{'stage':'test','status':'failed','error_type':'CalledProcessError'}] and not blocked_artifact.exists() and pointer.read_bytes()==before)
    archive=scratch/'release-v2.zip';manifest,sha=package(BASE,archive,revision,'v2')
    corrupt=scratch/'corrupt.zip';corrupt.write_bytes(archive.read_bytes()+b'changed')
    blocked=gate([('integrity',lambda:extract_verified(corrupt,sha,scratch/'must-not-extract')),('promote',lambda:promote(pointer,manifest,sha))])
    check('digest_mismatch_blocks_extraction_and_selection',blocked[0]['status']=='failed' and len(blocked)==1 and not (scratch/'must-not-extract').exists() and pointer.read_bytes()==before)
    bad_candidate=scratch/'candidate-unhealthy';extract_verified(archive,sha,bad_candidate)
    blocked=gate([('smoke',lambda:smoke(bad_candidate,'v2',True)),('promote',lambda:promote(pointer,manifest,sha))])
    check('unhealthy_candidate_keeps_last_good_release',blocked[0]['status']=='failed' and len(blocked)==1 and pointer.read_bytes()==before)
    candidate=scratch/'candidate-v2'
    successful=gate([('integrity',lambda:extract_verified(archive,sha,candidate)),('smoke',lambda:smoke(candidate,'v2')),('promote',lambda:promote(pointer,manifest,sha))])
    selected=json.loads(pointer.read_text())
    check('validated_candidate_selected_with_revision_and_digest',all(e['status']=='passed' for e in successful) and selected=={'release':'v2','revision':revision,'artifact_sha256':sha})
    promote(pointer,m1,h1)
    check('local_rollback_reselects_retained_good_artifact',json.loads(pointer.read_text())['release']=='v1')
    closed={}
    for port in ports:
        probe=socket.socket();probe.settimeout(.5);closed[str(port)]=probe.connect_ex(('127.0.0.1',port))!=0;probe.close()
    check('all_candidate_processes_and_ports_close',all(closed.values()))
    shutil.copyfile(archive,BASE/'release-artifact.zip')
    (BASE/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    result={'checks':checks,'total':len(checks),'runs':runs,'selected_before_rollback':selected,
            'selected_after_rollback':json.loads(pointer.read_text()),'artifact_sha256':sha,'manifest':manifest,
            'ports_closed':closed,'commands':commands,
            'boundary':'Candidate source bundle resolves locked dependencies from module node_modules; no remote runner or external deployment. Pointer replacement does not reroute a running server.'}
    (BASE/'pipeline-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
