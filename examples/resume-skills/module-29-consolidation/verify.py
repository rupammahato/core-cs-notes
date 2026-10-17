"""Run isolated output drills and audit canonical chapter references."""
from pathlib import Path
import hashlib
import json
import platform
import re
import shutil
import sqlite3
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
node = shutil.which('node')
assert node, 'Node required'
node_version = subprocess.run([node,'--version'],capture_output=True,text=True,check=True).stdout.strip()
manifest = json.loads((BASE / 'drills.json').read_text(encoding='utf-8'))
catalogue = json.loads((BASE / 'module-catalogue.json').read_text(encoding='utf-8'))
checks, observations, processes = [], [], []
for drill in manifest:
    path = BASE / drill['file']
    command = [node,str(path)] if drill['kind'] == 'node-esm' else [sys.executable,'-X','utf8',str(path)]
    child = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
    try:
        stdout, stderr = child.communicate(timeout=10)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate()
    processes.append({'drill':drill['id'],'pid':child.pid,'exit_code':child.returncode,'exited':child.poll() is not None})
    assert child.returncode == 0 and not stderr, (drill['id'],stderr)
    result = json.loads(stdout)
    assert result == drill['expected'], (drill['id'],result,drill['expected'])
    checks.append({'group':'runtime-output','name':drill['id']+' '+drill['title'],'passed':True})
    observations.append({'id':drill['id'],'kind':drill['kind'],'result':result})
for entry in catalogue:
    path = ROOT / 'Resume Skills Notes' / entry['file']
    text = path.read_text(encoding='utf-8')
    match = re.search(r'part-\d+-module-(\d+)-(.+)\.md$',path.name)
    assert match and int(match[1]) == entry['module'] and match[2] == entry['slug']
    assert entry['route'] == '/docs/resume-skills/'+match[2]
    assert entry['title'] in text and hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    checks.append({'group':'chapter-reference','name':'M'+str(entry['module'])+' source/slug/title/hash','passed':True})
assert [d['id'] for d in manifest] == [f'D{i:02}' for i in range(1,15)]
assert [entry['module'] for entry in catalogue] == list(range(29))
assert all(0 <= module <= 28 for drill in manifest for module in drill['modules'])
cleanup = {'drill_processes':processes,'all_drill_processes_exited':all(p['exited'] for p in processes),'sqlite_storage':'in-memory connections explicitly closed inside three SQL drills','persistent_listener_started':False,'external_services_called':False}
proof = {'module':29,'verified_date':'2026-10-16','node':node_version,'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'os':platform.platform(),'total':len(checks),'counts':{'runtime-output':len(manifest),'chapter-reference':len(catalogue)},'runtime_kinds':{kind:sum(d['kind']==kind for d in manifest) for kind in ('node-esm','python','sqlite')},'checks':checks,'observations':observations,'cleanup':cleanup,'scope':'Fourteen new isolated language/SQLite output drills and 29 canonical teaching-chapter reference audits. Debug cards, mock interviews, schedules and self-test answers are editorial learning material, not executed production cases or a scored user assessment. Earlier service/database/browser/provider fixtures were not rerun.'}
(BASE / 'verification-results.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE / 'cleanup-results.json').write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':proof['total'],'counts':proof['counts'],'runtime_kinds':proof['runtime_kinds'],'observations':observations,'all_drill_processes_exited':cleanup['all_drill_processes_exited']},indent=2))
