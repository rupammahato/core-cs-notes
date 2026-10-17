"""Verify S4-S6 fidelity and preservation, then build/smoke the expanded site once."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SITE = ROOT/'study-guide'
NODE = shutil.which('node')
assert NODE
specs = [('S4','module-9-booking-reservations',57,2),('S5','module-10-chat-messaging',59,4),
         ('S6','module-11-social-feed-photo-sharing',67,4)]
valid_routes = {'/docs/system-design','/docs/resume-skills'}
source_files = []
for folder in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes','System Design Notes'):
    source_files.extend((ROOT/folder).glob('*.md'))
for folder,subject in [('Resume Skills Notes','resume-skills'),('System Design Notes','system-design')]:
    for file in (ROOT/folder).glob('*.md'):
        match = re.search(r'module-\d+-(.+)\.md$',file.name)
        if match:
            valid_routes.add('/docs/'+subject+'/'+match[1])
sections,fixture_ports,owned_files = [],[],[]
for label,name,total,workers in specs:
    folder = BASE.parent/name
    proof = json.loads((folder/'verification-results.json').read_text(encoding='utf-8'))
    content = json.loads((folder/'content-validation.json').read_text(encoding='utf-8'))
    assert proof['total'] == sum(proof['counts'].values()) == len(proof['checks']) == total
    assert all(item['passed'] for item in proof['checks'])
    chapter = ROOT/'System Design Notes'/content['chapter']
    text = chapter.read_text(encoding='utf-8')
    assert [int(n) for n in re.findall(r'^### Q(\d+)\.',text,re.M)] == list(range(1,31))
    assert len(re.findall(r'^- \[ \]',text,re.M)) == 12
    assert len(re.findall(r'^\d+\. ',text.split('## 20. Practice tasks')[1].split('---')[0],re.M)) == 10
    assert len(text.split()) == content['words'] and text.count('\n') == content['lines']
    assert all((folder/name).read_text(encoding='utf-8') in text for name in content['source_fidelity'])
    fidelity = {name:json.dumps(proof['observations'][name],ensure_ascii=False,indent=2) in text for name in content['output_fidelity']}
    fidelity['versions'] = all(proof[name] in text for name in ('python','sqlite','os'))
    assert all(fidelity.values()),(label,fidelity)
    assert not re.search(r'\{\{[A-Z_]+\}\}',text)
    mock = text.split('| Segment | Minutes |')[1].split('A defensible short answer:')[0]
    assert sum(int(value) for value in re.findall(r'^\| [^|]+ \| (\d+) \|$',mock,re.M)) == content['mock_minutes'] == 45
    links = set(re.findall(r'\]\((/docs/[^)]+)\)',text))
    assert links <= valid_routes,(label,links-valid_routes)
    content.update(result_fidelity=fidelity,authored_internal_links=len(links))
    (folder/'content-validation.json').write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
    assert all(proof['cleanup'][key] for key in ('temporary_database_directory_removed','sqlite_connections_closed','temporary_http_servers_closed'))
    assert not proof['cleanup']['port_3000_used']
    assert proof['cleanup']['concurrent_worker_calls_completed'] == workers
    fixture_ports.extend(proof['cleanup']['fixture_ports'])
    sections.append({'label':label,'checks':total,'counts':proof['counts'],'runtime':{key:proof[key] for key in ('python','sqlite','os')},
                     'content':content,'cleanup':proof['cleanup'],'scope':proof['scope']})
    owned_files.extend([chapter,*(path for path in folder.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.md','.mjs'))])
roadmap = json.loads((BASE.parent/'roadmap/content-validation.json').read_text(encoding='utf-8'))
roadmap_proof = json.loads((BASE.parent/'roadmap/verification-results.json').read_text(encoding='utf-8'))
assert roadmap['available_files'] == 13 and all(item['passed'] for item in roadmap_proof['checks'])
sync = subprocess.run([NODE,'scripts/sync-notes.mjs'],cwd=SITE,capture_output=True,text=True,encoding='utf-8',timeout=30)
sync.check_returncode()
print(sync.stdout,flush=True)
meta = json.loads((SITE/'content/docs/system-design/meta.json').read_text(encoding='utf-8'))
assert meta['pages'] == ['index','foundations','worked-systems']
worked = json.loads((SITE/'content/docs/system-design/worked-systems/meta.json').read_text(encoding='utf-8'))
assert worked['pages'] == ['url-shortener','rate-limiter','notifications-webhooks','file-upload-processing','booking-reservations','chat-messaging','social-feed-photo-sharing']
for section in sections:
    slug = re.search(r'module-\d+-(.+)\.md$',section['content']['chapter'])[1]
    copied = (SITE/f'content/docs/system-design/worked-systems/{slug}.md').read_text(encoding='utf-8')
    original = (ROOT/'System Design Notes'/section['content']['chapter']).read_text(encoding='utf-8')
    assert original.split('## Why this module exists',1)[1] in copied
font = Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env = dict(os.environ)
if font.exists():
    env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES'] = str(font)
if '--reuse-build' in sys.argv:
    built = SITE/'.next/BUILD_ID'
    assert built.is_file()
    inputs = list(source_files)+[SITE/'package.json',SITE/'package-lock.json',SITE/'next.config.mjs']
    for folder in ('app','components','lib','scripts'):
        inputs.extend(path for path in (SITE/folder).rglob('*') if path.is_file())
    assert all(path.stat().st_mtime_ns <= built.stat().st_mtime_ns for path in inputs if path.exists())
    output = (BASE/'site-build-output.txt').read_text(encoding='utf-8')
    assert 'Compiled successfully' in output and 'Finalizing page optimization' in output
else:
    build = subprocess.run([NODE,'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,
        capture_output=True,text=True,encoding='utf-8',timeout=180)
    output = build.stdout+'\n'+build.stderr
    (BASE/'site-build-output.txt').write_text(output,encoding='utf-8')
    build.check_returncode()
    print(build.stdout,flush=True)
completed = [int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',output) if done==total]
assert completed and completed[-1] == len(source_files)+5
smoke = subprocess.run([NODE,str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,
    capture_output=True,text=True,encoding='utf-8',timeout=120)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site = json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
net = subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners = [line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped = {str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'],*fixture_ports)}
assert all(stopped.values()),stopped
subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,check=True)
owned_files.extend(path for path in BASE.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.md','.mjs'))
assert not [str(path) for path in owned_files if re.search(r'[\t ]+$',path.read_text(encoding='utf-8'),re.M)]
for _,folder,_,_ in specs:
    assert not list((BASE.parent/folder).glob('*.sqlite*'))
core = []
for folder in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes'):
    files = list((ROOT/folder).glob('*.md'))
    core.append({'subject':folder,'files':len(files),'lines':sum(path.read_text(encoding='utf-8').count('\n') for path in files)})
assert sum(item['files'] for item in core[:-1])==69 and sum(item['lines'] for item in core[:-1])==51671
assert core[-1]['files']==31 and core[-1]['lines']==37575
architecture = list((ROOT/'System Design Notes').glob('*.md'))
arch_lines = sum(path.read_text(encoding='utf-8').count('\n') for path in architecture)
assert len(architecture)==13
assert f'**System Design: 13 files, {arch_lines:,} lines.**' in (ROOT/'README.md').read_text(encoding='utf-8')
plan = (ROOT/'Architecture-System-Design-Notes-Plan.md').read_text(encoding='utf-8')
for marker in ('S4 ticket booking/reservations','S5 chat/messaging','S6 social feed/photo sharing'):
    assert plan.count('- [x] '+marker+' authored')==1
assert '- [ ] Remaining worked teaching chapters S7-S13 written.' in plan and 'Next: **S7:' in plan
summary = {'labels':['S4','S5','S6'],'verified_date':'2026-10-17','total_checks':sum(item['checks'] for item in sections),
    'sections':sections,'roadmap_document_checks':roadmap_proof['total'],
    'website':{'build_passed':True,'static_pages':completed[-1],'routes_checked':len(site['routes']),
        'all_routes_200':all(route['status']==200 for route in site['routes']),'assertions':site['assertions'],
        'search':site['search'],'next_route_status':site['nextRouteStatus'],'temporary_server_closed':site['temporaryServerClosed'],
        'cached_font_fixture_used':font.exists()},'ports_stopped':stopped,'existing_handbooks':core,
    'system_design':{'files':13,'lines':arch_lines,'published_worked_systems':[f'S{i}' for i in range(7)]},
    'git_diff_check_passed':True,'next':'S7: Background job scheduler and worker platform'}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':summary['total_checks'],'static_pages':completed[-1],'routes':len(site['routes']),
    'ports_stopped':stopped,'next':summary['next']},indent=2))
