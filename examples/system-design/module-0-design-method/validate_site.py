"""Validate A0 fidelity and the handbook using an owned temporary site process."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SITE=ROOT/'study-guide'
NODE=shutil.which('node')
assert NODE
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
content=json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
roadmap=json.loads((BASE.parent/'roadmap/content-validation.json').read_text(encoding='utf-8'))
roadmap_proof=json.loads((BASE.parent/'roadmap/verification-results.json').read_text(encoding='utf-8'))
assert proof['total']==sum(proof['counts'].values())==len(proof['checks'])==62
assert all(check['passed'] for check in proof['checks'])
assert all(check['passed'] for check in roadmap_proof['checks'])
chapter=ROOT/'System Design Notes'/content['chapter']
text=chapter.read_text(encoding='utf-8')
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',text,re.M)]==list(range(1,31))
assert len(re.findall(r'^- \[ \]',text,re.M))==12
assert len(re.findall(r'^\d+\. ',text.split('## 20. Practice tasks')[1].split('---')[0],re.M))==10
assert len(text.split())==content['words'] and text.count('\n')==content['lines']
assert all((BASE/name).read_text(encoding='utf-8') in text for name in content['source_fidelity'])
fidelity={name:json.dumps(proof['observations'][name],ensure_ascii=False,indent=2) in text for name in ('estimates','sensitivity','objectives','baseline')}
fidelity['versions']=all(proof[name] in text for name in ('python','sqlite','os'))
assert all(fidelity.values()),fidelity
assert content['mock_minutes']==45
assert not re.search(r'\{\{[A-Z_]+\}\}',text)
content['result_fidelity']=fidelity
(BASE/'content-validation.json').write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
sync=subprocess.run([NODE,'scripts/sync-notes.mjs'],cwd=SITE,capture_output=True,text=True,encoding='utf-8',timeout=30)
sync.check_returncode()
print(sync.stdout,flush=True)
meta=json.loads((SITE/'content/docs/system-design/meta.json').read_text(encoding='utf-8'))
assert meta['pages']==['index','foundations']
copied=(SITE/'content/docs/system-design/foundations/design-method-estimation.md').read_text(encoding='utf-8')
assert text.split('## Why this module exists',1)[1] in copied
font=Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env=dict(os.environ)
if font.exists():
    env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES']=str(font)
build=subprocess.run([NODE,'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
(BASE/'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
build.check_returncode()
print(build.stdout,flush=True)
completed=[int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',build.stdout) if done==total]
source_files=[]
for folder in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes','System Design Notes'):
    source_files.extend((ROOT/folder).glob('*.md'))
assert completed and completed[-1]==len(source_files)+5
smoke=subprocess.run([NODE,str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site=json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
net=subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners=[line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped={str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'])}
assert all(stopped.values()),stopped
assert proof['cleanup']['temporary_database_directory_removed'] and proof['cleanup']['sqlite_connections_closed'] and proof['cleanup']['concurrent_worker_calls_completed']==4
assert not proof['cleanup']['persistent_listener_started'] and not list(BASE.glob('a0-*'))
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
diff.check_returncode()
files=[chapter,*(path for path in BASE.rglob('*') if '__pycache__' not in path.parts and path.is_file() and path.suffix in ('.py','.mjs','.md'))]
whitespace=[str(path) for path in files if re.search(r'[\t ]+$',path.read_text(encoding='utf-8'),re.M)]
assert not whitespace,whitespace
assert not list(BASE.glob('*.tmp.*'))
core=[]
for folder in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes'):
    paths=list((ROOT/folder).glob('*.md'))
    core.append({'subject':folder,'files':len(paths),'lines':sum(path.read_text(encoding='utf-8').count('\n') for path in paths)})
assert sum(e['files'] for e in core[:-1])==69 and sum(e['lines'] for e in core[:-1])==51671
assert core[-1]['files']==31 and core[-1]['lines']==37575
architecture=list((ROOT/'System Design Notes').glob('*.md'))
arch_lines=sum(path.read_text(encoding='utf-8').count('\n') for path in architecture)
assert len(architecture)==roadmap['available_files']
assert f'**System Design: {len(architecture)} files, {arch_lines:,} lines.**' in (ROOT/'README.md').read_text(encoding='utf-8')
summary={'label':'A0','module':0,'verified_date':proof['verified_date'],'python':proof['python'],'sqlite':proof['sqlite'],'os':proof['os'],'checks':{'counts':proof['counts'],'total':proof['total'],'all_passed':True},'roadmap_document_checks':roadmap_proof['total'],'content':content,'cleanup':proof['cleanup'],'website':{'build_passed':True,'static_pages':completed[-1],'routes_checked':len(site['routes']),'all_routes_200':all(route['status']==200 for route in site['routes']),'assertions':site['assertions'],'search':site['search'],'next_route_status':site['nextRouteStatus'],'temporary_server_closed':site['temporaryServerClosed'],'cached_font_fixture_used':font.exists()},'ports_stopped':stopped,'existing_handbooks':core,'system_design':{'files':len(architecture),'lines':arch_lines,'published_foundations':['A0']},'git_diff_check_passed':True,'trailing_whitespace_files':whitespace,'next':'A1: Application architecture and service boundaries','scope':proof['scope']}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':62,'static_pages':completed[-1],'routes':len(site['routes']),'ports_stopped':stopped,'next':summary['next']},indent=2))
