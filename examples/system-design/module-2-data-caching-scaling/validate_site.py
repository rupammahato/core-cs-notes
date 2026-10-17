"""Verify A2 evidence fidelity, authored navigation and an owned production preview."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SITE = ROOT/'study-guide'
NODE = shutil.which('node')
assert NODE
proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
content = json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
roadmap = json.loads((BASE.parent/'roadmap/content-validation.json').read_text(encoding='utf-8'))
roadmap_proof = json.loads((BASE.parent/'roadmap/verification-results.json').read_text(encoding='utf-8'))
assert proof['total'] == sum(proof['counts'].values()) == len(proof['checks']) == 91
assert all(item['passed'] for item in proof['checks'])
assert all(item['passed'] for item in roadmap_proof['checks'])
chapter = ROOT/'System Design Notes'/content['chapter']
text = chapter.read_text(encoding='utf-8')
assert [int(n) for n in re.findall(r'^### Q(\d+)\.', text, re.M)] == list(range(1, 31))
assert len(re.findall(r'^- \[ \]', text, re.M)) == 12
assert len(re.findall(r'^\d+\. ', text.split('## 20. Practice tasks')[1].split('---')[0], re.M)) == 10
assert len(text.split()) == content['words'] and text.count('\n') == content['lines']
assert all((BASE/name).read_text(encoding='utf-8') in text for name in content['source_fidelity'])
fidelity = {name: json.dumps(proof['observations'][name], ensure_ascii=False, indent=2) in text for name in content['output_fidelity']}
fidelity['versions'] = all(proof[name] in text for name in ('python', 'sqlite', 'os'))
assert all(fidelity.values()), fidelity
assert content['mock_minutes'] == 45
assert not re.search(r'\{\{[A-Z_]+\}\}', text)
mock = text.split('| Segment | Minutes |')[1].split('A defensible short answer:')[0]
assert sum(int(value) for value in re.findall(r'^\| [^|]+ \| (\d+) \|$', mock, re.M)) == 45
valid_routes = {'/docs/system-design', '/docs/resume-skills', '/docs/resume-skills/consolidation-interview-drills'}
for folder, subject in [('Resume Skills Notes', 'resume-skills'), ('System Design Notes', 'system-design')]:
    for file in (ROOT/folder).glob('*.md'):
        match = re.search(r'module-\d+-(.+)\.md$', file.name)
        if match:
            valid_routes.add('/docs/'+subject+'/'+match[1])
internal_links = set(re.findall(r'\]\((/docs/[^)]+)\)', text))
assert internal_links <= valid_routes, internal_links-valid_routes
content['result_fidelity'] = fidelity
content['authored_internal_links'] = len(internal_links)
(BASE/'content-validation.json').write_text(json.dumps(content, indent=2)+'\n', encoding='utf-8')
sync = subprocess.run([NODE, 'scripts/sync-notes.mjs'], cwd=SITE, capture_output=True, text=True, encoding='utf-8', timeout=30)
sync.check_returncode()
print(sync.stdout, flush=True)
meta = json.loads((SITE/'content/docs/system-design/meta.json').read_text(encoding='utf-8'))
assert meta['pages'] == ['index', 'foundations']
group = json.loads((SITE/'content/docs/system-design/foundations/meta.json').read_text(encoding='utf-8'))
assert group['pages'] == ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling']
copied = (SITE/'content/docs/system-design/foundations/data-caching-scaling.md').read_text(encoding='utf-8')
assert text.split('## Why this module exists', 1)[1] in copied
font = Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env = dict(os.environ)
if font.exists():
    env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES'] = str(font)
build = subprocess.run([NODE, 'node_modules/next/dist/bin/next', 'build', '--webpack'], cwd=SITE, env=env,
    capture_output=True, text=True, encoding='utf-8', timeout=180)
(BASE/'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr, encoding='utf-8')
build.check_returncode()
print(build.stdout, flush=True)
completed = [int(total) for done, total in re.findall(r'\((\d+)/(\d+)\)', build.stdout) if done == total]
source_files = []
for folder in ('DSA Notes', 'OOP Notes', 'OS Notes', 'DBMS Notes', 'CN Notes', 'Resume Skills Notes', 'System Design Notes'):
    source_files.extend((ROOT/folder).glob('*.md'))
assert completed and completed[-1] == len(source_files)+5
smoke = subprocess.run([NODE, str(BASE/'site-smoke.mjs'), str(SITE), str(BASE/'site-validation.json')], cwd=ROOT,
    capture_output=True, text=True, encoding='utf-8', timeout=60)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr, encoding='utf-8')
smoke.check_returncode()
site = json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
net = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, check=True)
listeners = [line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped = {str(port): not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000, site['port'])}
assert all(stopped.values()), stopped
assert all(proof['cleanup'][name] for name in ('temporary_database_directory_removed', 'sqlite_connections_closed', 'async_cache_tasks_closed'))
assert not proof['cleanup']['persistent_listener_started']
diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
diff.check_returncode()
files = [chapter, *(path for path in BASE.rglob('*') if '__pycache__' not in path.parts
    and path.is_file() and path.suffix in ('.py', '.mjs', '.md'))]
whitespace = [str(path) for path in files if re.search(r'[\t ]+$', path.read_text(encoding='utf-8'), re.M)]
assert not whitespace, whitespace
assert not list(BASE.glob('*.sqlite*')) and not list(BASE.glob('*.tmp.*'))
core = []
for folder in ('DSA Notes', 'OOP Notes', 'OS Notes', 'DBMS Notes', 'CN Notes', 'Resume Skills Notes'):
    paths = list((ROOT/folder).glob('*.md'))
    core.append({'subject': folder, 'files': len(paths), 'lines': sum(path.read_text(encoding='utf-8').count('\n') for path in paths)})
assert sum(item['files'] for item in core[:-1]) == 69 and sum(item['lines'] for item in core[:-1]) == 51671
assert core[-1]['files'] == 31 and core[-1]['lines'] == 37575
architecture = list((ROOT/'System Design Notes').glob('*.md'))
arch_lines = sum(path.read_text(encoding='utf-8').count('\n') for path in architecture)
assert len(architecture) == roadmap['available_files'] == 4
assert f'**System Design: {len(architecture)} files, {arch_lines:,} lines.**' in (ROOT/'README.md').read_text(encoding='utf-8')
plan = (ROOT/'Architecture-System-Design-Notes-Plan.md').read_text(encoding='utf-8')
assert plan.count('- [x] A2 authored') == 1
assert '91 checks' in plan and 'Next: **A3:' in plan
summary = {'label': 'A2', 'module': 2, 'verified_date': proof['verified_date'],
    'runtime': {name: proof[name] for name in ('python', 'sqlite', 'os')},
    'checks': {'counts': proof['counts'], 'total': proof['total'], 'all_passed': True},
    'roadmap_document_checks': roadmap_proof['total'], 'content': content, 'cleanup': proof['cleanup'],
    'website': {'build_passed': True, 'static_pages': completed[-1], 'routes_checked': len(site['routes']),
        'all_routes_200': all(route['status'] == 200 for route in site['routes']), 'assertions': site['assertions'],
        'search': site['search'], 'next_route_status': site['nextRouteStatus'],
        'temporary_server_closed': site['temporaryServerClosed'], 'cached_font_fixture_used': font.exists()},
    'ports_stopped': stopped, 'existing_handbooks': core,
    'system_design': {'files': len(architecture), 'lines': arch_lines, 'published_foundations': ['A0', 'A1', 'A2']},
    'git_diff_check_passed': True, 'trailing_whitespace_files': whitespace,
    'next': content['next'], 'scope': proof['scope']}
(BASE/'validation-summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'checks': proof['total'], 'static_pages': completed[-1], 'routes': len(site['routes']),
    'ports_stopped': stopped, 'next': summary['next']}, indent=2))
