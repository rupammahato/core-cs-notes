"""Check consolidation content, reference fidelity and the owned handbook preview."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SITE = ROOT / 'study-guide'
NODE = shutil.which('node')
assert NODE
proof = json.loads((BASE / 'verification-results.json').read_text(encoding='utf-8'))
content = json.loads((BASE / 'content-validation.json').read_text(encoding='utf-8'))
bank = json.loads((BASE / 'revision-bank.json').read_text(encoding='utf-8'))
catalogue = json.loads((BASE / 'module-catalogue.json').read_text(encoding='utf-8'))
assert proof['total'] == sum(proof['counts'].values()) == len(proof['checks']) == 43
assert proof['counts'] == {'runtime-output':14,'chapter-reference':29}
assert all(check['passed'] for check in proof['checks'])
chapter = ROOT / 'Resume Skills Notes' / content['chapter']
text = chapter.read_text(encoding='utf-8')
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',text,re.M)] == list(range(1,61))
assert [int(n) for n in re.findall(r'^### D(\d+)\.',text,re.M)] == list(range(1,15))
assert [int(n) for n in re.findall(r'^### B(\d+)\.',text,re.M)] == list(range(1,17))
assert [int(n) for n in re.findall(r'^### S(\d+)\.',text,re.M)] == list(range(1,25))
assert len(bank['pairs']) == 36 and len(bank['rapid_fire']) == 60 and len(bank['debugging']) == 16 and len(bank['self_test']) == 24
assert {q['module'] for q in bank['rapid_fire']} == set(range(29))
assert text.count('**Recorded output and explanation (read after predicting):**') == 14
assert text.count('**Answer checkpoints (read after answering):**') == 40
assert '<details>' not in text
assert len(re.findall(r'^- \[ \]',text,re.M)) == 12
assert len(re.findall(r'^\d+\. ',text.split('## 20. Practice tasks')[1].split('---')[0],re.M)) == 10
assert content['words'] == len(text.split()) and content['lines'] == text.count('\n')
assert all((BASE / name).read_text(encoding='utf-8') in text for name in content['source_fidelity'])
fidelity = {item['id']:json.dumps(item['result'],ensure_ascii=False,indent=2) in text for item in proof['observations']}
fidelity['versions'] = all(proof[name] in text for name in ('node','python','sqlite','os'))
assert all(fidelity.values())
assert all(entry['route'] in text and (ROOT / 'Resume Skills Notes' / entry['file']).exists() for entry in catalogue)
route_set = {entry['route'] for entry in catalogue}
assert set(re.findall(r'\]\((/docs/resume-skills/[^)]+)\)',text)) <= route_set
assert {name:sum(minutes for _,minutes in values) for name,values in bank['timing'].items()} == {'backend_mock':45,'ai_mock':45,'two_hour_route':120}
assert len(bank['self_test'])*2 == content['self_test_maximum'] == 48
assert not re.search(r'\{\{[A-Z_]+\}\}',text)
content['result_fidelity'] = fidelity
content['all_module_routes_present'] = True
(BASE / 'content-validation.json').write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
sync = subprocess.run([NODE,'scripts/sync-notes.mjs'],cwd=SITE,capture_output=True,text=True,encoding='utf-8',timeout=30)
sync.check_returncode()
print(sync.stdout,flush=True)
font = Path(tempfile.gettempdir()) / 'placement-site-validation/font-responses.cjs'
env = dict(os.environ)
if font.exists():
    env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES'] = str(font)
build = subprocess.run([NODE,'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
(BASE / 'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
build.check_returncode()
print(build.stdout,flush=True)
completed = [int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',build.stdout) if done==total]
assert completed and completed[-1] == 105
smoke = subprocess.run([NODE,str(BASE / 'site-smoke.mjs'),str(SITE),str(BASE / 'site-validation.json')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE / 'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site = json.loads((BASE / 'site-validation.json').read_text(encoding='utf-8'))
assert len(site['routes']) == 33
net = subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners = [line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped = {str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'])}
assert all(stopped.values()),stopped
assert proof['cleanup']['all_drill_processes_exited'] and len(proof['cleanup']['drill_processes'])==14
assert not proof['cleanup']['persistent_listener_started'] and not proof['cleanup']['external_services_called']
diff = subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
diff.check_returncode()
sources = [chapter,*(p for p in BASE.rglob('*') if '__pycache__' not in p.parts and p.is_file() and p.suffix in ('.py','.md','.mjs'))]
whitespace = [p.name for p in sources if re.search(r'[\t ]+$',p.read_text(encoding='utf-8'),re.M)]
assert not whitespace,whitespace
assert not list(BASE.glob('*.tmp.*')) and not (BASE / 'integrate.py').exists()
core = []
for name in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes'):
    files = list((ROOT / name).glob('*.md'))
    core.append({'subject':name,'files':len(files),'lines':sum(p.read_text(encoding='utf-8').count('\n') for p in files)})
assert sum(item['files'] for item in core)==69 and sum(item['lines'] for item in core)==51671
notes = list((ROOT / 'Resume Skills Notes').glob('*.md'))
lines = sum(p.read_text(encoding='utf-8').count('\n') for p in notes)
assert len(notes)==31
assert f'Resume Skills: 31 files, {lines:,} lines.' in (ROOT / 'README.md').read_text(encoding='utf-8')
roadmap = (ROOT / 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md').read_text(encoding='utf-8')
assert '| Authored handbook | 31 files:' in roadmap and '- [ ] M29: Consolidation and interview drills' in roadmap
summary = {'module':29,'title':'Consolidation and Interview Drills','verified_date':proof['verified_date'],'node':proof['node'],'python':proof['python'],'sqlite':proof['sqlite'],'os':proof['os'],'checks':{'counts':proof['counts'],'total':proof['total'],'all_passed':True},'cleanup':proof['cleanup'],'content':content,'dependency_check':(BASE / 'dependency-check.txt').read_text(encoding='utf-8').strip(),'website':{'build_passed':True,'static_pages':completed[-1],'routes_checked':len(site['routes']),'all_routes_200':all(r['status']==200 for r in site['routes']),'assertions':site['assertions'],'search':site['search'],'temporary_server_closed':site['temporaryServerClosed'],'cached_font_fixture_used':font.exists()},'ports_stopped':stopped,'git_diff_check_passed':True,'trailing_whitespace_files':whitespace,'core_handbooks':core,'resume_handbook':{'files':len(notes),'lines':lines,'groups':11,'main_sequence_authored':True,'learner_mastery_asserted':False},'next':'Architecture companion roadmap, then A0: How to approach a design question','scope':proof['scope']}
(BASE / 'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':proof['total'],'routes':len(site['routes']),'static_pages':completed[-1],'ports_stopped':stopped,'main_sequence_authored':True,'next':summary['next']},indent=2))
