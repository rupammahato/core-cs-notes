"""Reproduce local Git, delivery, telemetry and measurement checks without a remote runner."""
from pathlib import Path
import collections,json,os,re,shutil,socket,subprocess,sys,tempfile
import yaml
from git_lab import run_lab
from pipeline import run_pipeline_lab

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
NODE=shutil.which('node')
if not NODE:raise RuntimeError('Node is required')
head_before=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
node=subprocess.run([NODE,str(BASE/'verify.mjs')],cwd=BASE,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE/'node-verification-output.txt').write_text(node.stdout+'\n'+node.stderr,encoding='utf-8');node.check_returncode()
node_result=json.loads((BASE/'node-results.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='.run-',dir=BASE) as temporary:
    scratch=Path(temporary).resolve()
    if scratch.parent!=BASE:raise RuntimeError('Fixture path escaped workspace')
    git_result=run_lab(scratch)
    (BASE/'git-results.json').write_text(json.dumps(git_result,indent=2)+'\n',encoding='utf-8')
    pipeline=run_pipeline_lab(scratch,git_result['observations']['release_revision'])
    workflows=[]
    def check(name,condition):
        workflows.append({'group':'workflow','name':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)
    workflow=yaml.safe_load((BASE/'ci.example.yml').read_text(encoding='utf-8'))
    pins=json.loads((BASE/'action-pins.json').read_text(encoding='utf-8'))
    steps=workflow['jobs']['verify-and-package']['steps']
    check('yaml_parses_with_intended_events',set(workflow['on'])=={'push','pull_request','workflow_dispatch'})
    check('token_permissions_are_read_only',workflow['permissions']=={'contents':'read'})
    actions=[step['uses'] for step in steps if 'uses' in step]
    check('actions_match_resolved_official_commit_pins',all(value=='actions/'+name+'@'+pins[name]['sha'] and re.fullmatch('[a-f0-9]{40}',pins[name]['sha']) for value,name in zip(actions,('checkout','setup-node','upload-artifact'))) and len(actions)==3)
    runs=[step['run'] for step in steps if 'run' in step]
    check('test_and_check_gates_precede_packaging',runs==['npm ci --ignore-scripts','npm run check','npm test','node verify.mjs','python3 build_artifact.py --revision "$GITHUB_SHA"'])
    check('checkout_does_not_persist_credentials',steps[0]['with']['persist-credentials'] is False)
    contracts_text=(BASE/'contract-test-output.txt').read_text(encoding='utf-8')
    names=re.findall(r'^ok \d+ - (.+)$',contracts_text,re.M)
    if len(names)!=3 or '# fail 0' not in contracts_text:raise RuntimeError('HTTP contract evidence missing')
    contracts=[{'group':'contracts','name':name,'passed':True} for name in names]
    checks=git_result['checks']+node_result['checks']+pipeline['checks']+workflows+contracts
head_after=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
assert head_before==head_after
closed={**node_result['cleanup']['loopback_ports_closed'],**pipeline['ports_closed']}
for port in closed:
    probe=socket.socket();probe.settimeout(.5);closed[port]=probe.connect_ex(('127.0.0.1',int(port)))!=0;probe.close()
assert all(closed.values())
cleanup={'loopback_ports_closed':closed,'scratch_repositories_releases_and_directory_removed':not scratch.exists(),
         'main_repository_head_unchanged':head_before==head_after,'remote_github_actions_run':False,
         'external_deployment_performed':False,'docker_started':False}
assert cleanup['scratch_repositories_releases_and_directory_removed']
result={'module':19,'verified_date':'2026-10-14','python':sys.version,'node':node_result['node'],
        'git':subprocess.run(['git','--version'],capture_output=True,text=True,check=True).stdout.strip(),
        'pyyaml':yaml.__version__,'dependencies':node_result['dependencies'],
        'checks':checks,'total':len(checks),'counts':dict(sorted(collections.Counter(c['group'] for c in checks).items())),
        'observations':{'git':git_result['observations'],'node':node_result['observations'],
                        'pipeline':{key:pipeline[key] for key in ('runs','selected_before_rollback','selected_after_rollback','artifact_sha256','boundary')},'action_pins':pins},
        'cleanup':cleanup,
        'scope':'Disposable local Git repositories/remotes; actual local source-bundle gates and candidate HTTP; official in-memory OpenTelemetry traces, custom metrics/logs and short same-process closed-model load runs. No hosted Actions, production release or capacity benchmark.'}
(BASE/'verification-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(BASE/'cleanup-results.json').write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
(BASE/'release-artifact.sha256').write_text(pipeline['artifact_sha256']+'  release-artifact.zip\n',encoding='utf-8')
print(json.dumps({'checks':result['total'],'counts':result['counts'],'versions':{'node':result['node'],'git':result['git'],'pyyaml':result['pyyaml']},'normal_load':node_result['observations']['load']['normal']['summary'],'cleanup':cleanup},indent=2))
