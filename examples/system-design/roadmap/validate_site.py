"""Build/smoke-test the new roadmap subject with an owned temporary preview."""
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
assert proof['total']==17 and all(check['passed'] for check in proof['checks'])
sync=subprocess.run([NODE,'scripts/sync-notes.mjs'],cwd=SITE,capture_output=True,text=True,encoding='utf-8',timeout=30)
sync.check_returncode()
print(sync.stdout,flush=True)
generated=SITE/'content/docs/system-design'
assert sorted(path.name for path in generated.iterdir())==['index.md','meta.json']
meta=json.loads((generated/'meta.json').read_text(encoding='utf-8'))
assert meta['pages']==['index'] and meta['root'] is True and meta['title']=='System Design'
source=(ROOT/'System Design Notes'/content['chapter']).read_text(encoding='utf-8')
copied=(generated/'index.md').read_text(encoding='utf-8')
assert source.split('## 0. What is available now',1)[1] in copied
tags=(SITE/'components/search-dialog.tsx').read_text(encoding='utf-8')
assert tags.count("{ name: 'System Design', value: 'system-design' }")==1
font=Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env=dict(os.environ)
if font.exists():
    env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES']=str(font)
build=subprocess.run([NODE,'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
(BASE/'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
build.check_returncode()
print(build.stdout,flush=True)
completed=[int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',build.stdout) if done==total]
assert completed and completed[-1]==106
smoke=subprocess.run([NODE,str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site=json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
assert len(site['routes'])==38 and site['futureRouteStatus']==404
net=subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners=[line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped={str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'])}
assert all(stopped.values()),stopped
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
diff.check_returncode()
core=[]
for folder in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes'):
    files=list((ROOT/folder).glob('*.md'))
    core.append({'subject':folder,'files':len(files),'lines':sum(path.read_text(encoding='utf-8').count('\n') for path in files)})
assert sum(e['files'] for e in core[:-1])==69 and sum(e['lines'] for e in core[:-1])==51671
assert core[-1]['files']==31 and core[-1]['lines']==37575
assert len(list((ROOT/'System Design Notes').glob('*.md')))==1
assert source.count('\n')==content['lines']==402
assert '**System Design: 1 file, 402 lines.**' in (ROOT/'README.md').read_text(encoding='utf-8')
files=[ROOT/'System Design Notes'/content['chapter'],*(path for path in BASE.rglob('*') if '__pycache__' not in path.parts and path.is_file() and path.suffix in ('.py','.mjs','.md'))]
whitespace=[str(path) for path in files if re.search(r'[\t ]+$',path.read_text(encoding='utf-8'),re.M)]
assert not whitespace,whitespace
summary={'checked_date':proof['checked_date'],'roadmap':content,'document_checks':{'total':proof['total'],'all_passed':True},'website':{'build_passed':True,'static_pages':completed[-1],'routes_checked':len(site['routes']),'all_routes_200':all(route['status']==200 for route in site['routes']),'assertions':site['assertions'],'search':site['search'],'unpublished_a0_status':site['futureRouteStatus'],'temporary_server_closed':site['temporaryServerClosed'],'cached_font_fixture_used':font.exists()},'ports_stopped':stopped,'existing_handbooks':core,'git_diff_check_passed':True,'trailing_whitespace_files':whitespace,'next':'A0: How to approach a design question','scope':proof['scope']}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'document_checks':17,'static_pages':106,'routes':38,'unpublished_a0_status':404,'ports_stopped':stopped,'next':summary['next']},indent=2))
