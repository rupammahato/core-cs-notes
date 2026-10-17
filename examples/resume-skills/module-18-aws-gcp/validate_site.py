"""Validate the cloud notes/source and site without using cloud accounts or Docker."""
from pathlib import Path
import json,os,re,shutil,subprocess,tempfile

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SITE=ROOT/'study-guide'
NODE=shutil.which('node')
if not NODE:raise RuntimeError('Node executable missing')
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
content=json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
assert proof['total']==53 and all(c['passed'] for c in proof['checks'])
chapter=ROOT/'Resume Skills Notes'/content['chapter'];text=chapter.read_text(encoding='utf-8')
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',text,re.M)]==list(range(1,31))
assert len(re.findall(r'^- \[ \]',text,re.M))==12
assert len(re.findall(r'^\d+\. ',text.split('## 18. Practice tasks')[1].split('---')[0],re.M))==10
assert all((BASE/name).read_text(encoding='utf-8') in text for name in content['source_fidelity'])
for name in ('iam-read-object-policy.json','ec2-trust-policy.json'):json.loads((BASE/name).read_text(encoding='utf-8'))
result_fidelity={
    'versions':all(value in text for value in proof['versions'].values()),
    'sdk_json':(BASE/'task-request.json').read_text(encoding='utf-8') in text,
    'cache':json.dumps(proof['observations']['cache'],indent=2) in text,
    'delivery':json.dumps(proof['observations']['delivery'],indent=2) in text,
}
assert all(result_fidelity.values()),result_fidelity
content['result_fidelity']=result_fidelity
(BASE/'content-validation.json').write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')

sync=subprocess.run([NODE,'scripts/sync-notes.mjs'],cwd=SITE,capture_output=True,text=True,encoding='utf-8',timeout=30)
sync.check_returncode();print(sync.stdout,flush=True)
font=Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env=dict(os.environ)
if font.exists():env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES']=str(font)
build=subprocess.run([NODE,'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
(BASE/'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
build.check_returncode();print(build.stdout,flush=True)
completed=[int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',build.stdout) if done==total]
if not completed:raise RuntimeError('No completed static-page count recorded')
smoke=subprocess.run([NODE,str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site=json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
net=subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners=[line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
ports=(3000,site['port'],*(int(port) for port in proof['cleanup']['loopback_ports_closed']))
stopped={str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in ports}
if not all(stopped.values()):raise RuntimeError('Requested/test listener remains open')
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);diff.check_returncode()
whitespace=[p.name for p in [chapter,*BASE.glob('*.py'),*BASE.glob('*.md'),*BASE.glob('*.mjs')] if re.search(r'[\t ]+$',p.read_text(encoding='utf-8'),re.M)]
if whitespace:raise RuntimeError('Trailing whitespace '+str(whitespace))
core=[]
for name in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes'):
    files=list((ROOT/name).glob('*.md'))
    core.append({'subject':name,'files':len(files),'lines':sum(p.read_text(encoding='utf-8').count('\n') for p in files)})
assert sum(item['files'] for item in core)==69 and sum(item['lines'] for item in core)==51671
summary={'module':18,'title':'AWS and GCP Fundamentals for This Resume','verified_date':'2026-10-14',
         'python':proof['python'],'os':proof['os'],'versions':proof['versions'],
         'checks':{'counts':proof['counts'],'total':proof['total'],'all_passed':True},
         'cleanup':proof['cleanup'],'content':content,
         'website':{'build_passed':True,'static_pages':completed[-1],'routes_checked':len(site['routes']),
                    'all_routes_200':all(r['status']==200 for r in site['routes']),'assertions':site['assertions'],
                    'search':site['search'],'temporary_server_closed':site['temporaryServerClosed'],'cached_font_fixture_used':font.exists()},
         'ports_stopped':stopped,'git_diff_check_passed':True,'trailing_whitespace_files':whitespace,
         'core_handbooks':core,'next_module':'M19: Git, CI/CD, Testing, Observability and Performance','scope':proof['scope']}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':proof['total'],'routes':len(site['routes']),'static_pages':completed[-1],'ports_stopped':stopped,'next':summary['next_module']},indent=2))
