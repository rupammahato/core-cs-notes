"""Validate the completed architecture companion and build/smoke its site once."""
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
analytics = BASE.parent/'module-18-analytics-event-pipeline'
revision = BASE.parent/'consolidation'
runtime = json.loads((analytics/'verification-results.json').read_text(encoding='utf-8'))
audit = json.loads((revision/'verification-results.json').read_text(encoding='utf-8'))
assert runtime['total']==len(runtime['checks'])==sum(runtime['counts'].values())==78
assert audit['total']==len(audit['checks'])==sum(audit['counts'].values())==204
assert all(c['passed'] for proof in (runtime,audit) for c in proof['checks'])
assert runtime['verified_date']==audit['verified_date']=='2026-10-18'
assert runtime['cleanup']['concurrent_worker_calls_completed']==4
assert all(runtime['cleanup'][key] for key in ('temporary_database_directory_removed','sqlite_connections_closed','temporary_http_servers_closed'))
assert not runtime['cleanup']['port_3000_used']
assert not audit['observations']['fresh_historical_runtime_reruns']
sources = []
for subject in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes','System Design Notes'):
    sources.extend((ROOT/subject).glob('*.md'))
valid_routes = {'/docs/system-design','/docs/resume-skills','/docs/system-design/consolidation'}
for folder,subject in [('Resume Skills Notes','resume-skills'),('System Design Notes','system-design')]:
    for source in (ROOT/folder).glob('*.md'):
        match = re.search(r'module-\d+-(.+)\.md$',source.name)
        if match:
            valid_routes.add('/docs/'+subject+'/'+match[1])
sections = []
for folder in (analytics,revision):
    meta = json.loads((folder/'content-validation.json').read_text(encoding='utf-8'))
    chapter = (ROOT/'System Design Notes'/meta['chapter']).read_text(encoding='utf-8')
    assert len(chapter.split())==meta['words'] and chapter.count('\n')==meta['lines']
    assert [int(n) for n in re.findall(r'^## (\d+)\.',chapter,re.M)]==list(range(1,23))
    assert len(re.findall(r'^- \[ \]',chapter,re.M))==12
    assert len(re.findall(r'^\d+\. ',chapter.split('## 20. Practice tasks')[1].split('---')[0],re.M))==10
    assert '{{' not in chapter
    assert all((folder/name).read_text(encoding='utf-8') in chapter for name in meta['source_fidelity'])
    assert set(re.findall(r'\]\((/docs/[^)]+)\)',chapter))<=valid_routes
    mock = chapter.split('| Segment | Minutes |')[1].split('| **Total** | **45** |')[0]
    assert sum(int(n) for n in re.findall(r'^\| [^|]+ \| (\d+) \|$',mock,re.M))==45
    if folder==analytics:
        assert [int(n) for n in re.findall(r'^### Q(\d+)\.',chapter,re.M)]==list(range(1,31))
        fidelity = {name:json.dumps(runtime['observations'][name],indent=2) in chapter for name in meta['output_fidelity']}
        assert all(fidelity.values())
        meta['result_fidelity'] = fidelity
        (folder/'content-validation.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    else:
        assert re.findall(r'^### (Q\d{2})\.',chapter,re.M)==[f'Q{i:02}' for i in range(1,61)]
        assert meta['verified_document_checks']==204 and meta['all_teaching_links_resolve']
    sections.append(meta)
roadmap = json.loads((BASE.parent/'roadmap/content-validation.json').read_text(encoding='utf-8'))
roadmap_proof = json.loads((BASE.parent/'roadmap/verification-results.json').read_text(encoding='utf-8'))
syllabus = json.loads((BASE.parent/'roadmap/syllabus.json').read_text(encoding='utf-8'))
assert roadmap['available_files']==roadmap['planned_files']==21
assert all(entry['status']=='Available' for entry in syllabus) and len(syllabus)==20
assert all(c['passed'] for c in roadmap_proof['checks'])
sync = subprocess.run([NODE,'scripts/sync-notes.mjs'],cwd=SITE,capture_output=True,text=True,encoding='utf-8',timeout=30)
sync.check_returncode()
print(sync.stdout,flush=True)
meta = json.loads((SITE/'content/docs/system-design/meta.json').read_text(encoding='utf-8'))
assert meta['pages']==['index','foundations','worked-systems','revision']
worked = json.loads((SITE/'content/docs/system-design/worked-systems/meta.json').read_text(encoding='utf-8'))
assert worked['pages']==[entry['slug'] for entry in syllabus if entry['label'].startswith('S')]
assert json.loads((SITE/'content/docs/system-design/revision/meta.json').read_text(encoding='utf-8'))['pages']==['consolidation']
for section in sections:
    copied = (SITE/f"content/docs/system-design/{section['group']}/{section['slug']}.md").read_text(encoding='utf-8')
    original = (ROOT/'System Design Notes'/section['chapter']).read_text(encoding='utf-8')
    assert original.split('## Why this module exists',1)[1] in copied
font = Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env = dict(os.environ)
if font.exists():
    env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES']=str(font)
if '--reuse-build' in sys.argv:
    build_id = SITE/'.next/BUILD_ID'
    assert build_id.is_file()
    inputs = sources+[SITE/'package.json',SITE/'package-lock.json',SITE/'next.config.mjs']
    for folder in ('app','components','lib','scripts'):
        inputs.extend(path for path in (SITE/folder).rglob('*') if path.is_file())
    assert all(path.stat().st_mtime_ns<=build_id.stat().st_mtime_ns for path in inputs if path.exists())
    output = (BASE/'site-build-output.txt').read_text(encoding='utf-8')
    assert 'Compiled successfully' in output and 'Finalizing page optimization' in output
else:
    build = subprocess.run([NODE,'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,
        capture_output=True,text=True,encoding='utf-8',timeout=240)
    output = build.stdout+'\n'+build.stderr
    (BASE/'site-build-output.txt').write_text(output,encoding='utf-8')
    build.check_returncode()
    print(build.stdout,flush=True)
completed = [int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',output) if done==total]
assert completed and completed[-1]==len(sources)+5==126
smoke = subprocess.run([NODE,str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,
    capture_output=True,text=True,encoding='utf-8',timeout=120)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site = json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
assert len(site['routes'])==58 and all(route['status']==200 for route in site['routes'])
net = subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners = [line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped = {str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'],*runtime['cleanup']['fixture_ports'])}
assert all(stopped.values()),stopped
subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,check=True)
owned = [path for folder in (analytics,revision,BASE) for path in folder.rglob('*')
         if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.md','.mjs','.json')]
owned += [ROOT/'System Design Notes'/section['chapter'] for section in sections]
assert not [str(path) for path in owned if re.search(r'[\t ]+$',path.read_text(encoding='utf-8'),re.M)]
assert not list(analytics.glob('*.sqlite*'))
preserved = []
for folder in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes','Resume Skills Notes'):
    files = list((ROOT/folder).glob('*.md'))
    preserved.append({'subject':folder,'files':len(files),'lines':sum(path.read_text(encoding='utf-8').count('\n') for path in files)})
assert sum(e['files'] for e in preserved[:-1])==69 and sum(e['lines'] for e in preserved[:-1])==51671
assert preserved[-1]['files']==31 and preserved[-1]['lines']==37575
architecture = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(path.read_text(encoding='utf-8').count('\n') for path in architecture)
assert len(architecture)==21
assert f'**System Design: 21 files, {lines:,} lines.**' in (ROOT/'README.md').read_text(encoding='utf-8')
plan = (ROOT/'Architecture-System-Design-Notes-Plan.md').read_text(encoding='utf-8')
assert '- [ ]' not in plan.split('## 8. Progress')[1]
assert 'all 21 Architecture and System Design files are available' in plan
summary = {'verified_date':'2026-10-18','authoring_complete':True,'authored_track_files':21,
    'foundations':5,'worked_systems':14,'consolidation':1,'new_runtime_checks':78,
    'fresh_document_helper_checks':204,'historical_recorded_teaching_assertions':1600,
    'historical_runtime_suite_freshly_rerun':False,'new_sections':sections,
    'website':{'build_passed':True,'static_pages':126,'routes_checked':58,'all_routes_200':True,
        'assertions':site['assertions'],'search':site['search'],'temporary_server_closed':site['temporaryServerClosed'],
        'cached_font_fixture_used':font.exists()},'ports_stopped':stopped,'preserved_handbooks':preserved,
    'architecture_lines':lines,'all_learning_checklists_automatically_completed':False,
    'later_track':'Separate product/analytics P0-P5; optional enrichment designs are not required architecture files',
    'next':'Revision and manual practice'}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:summary[key] for key in ('authoring_complete','authored_track_files','new_runtime_checks','fresh_document_helper_checks','ports_stopped','next')},indent=2))
