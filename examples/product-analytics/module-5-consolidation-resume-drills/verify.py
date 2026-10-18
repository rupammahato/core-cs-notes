"""Fresh isolated drills plus explicit source/coverage audits; no grading of resume truth."""
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
expected=json.loads((BASE/'expected-output.json').read_text(encoding='utf-8'))
coverage=json.loads((BASE/'coverage.json').read_text(encoding='utf-8'))
stories=json.loads((BASE/'story-map.json').read_text(encoding='utf-8'))
catalog_path=ROOT/'examples/resume-skills/module-28-resume-deep-dives/resume-evidence.json'
catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
checks=[];observations={};workers=[]
def record(group,name):
    checks.append({'group':group,'name':name,'passed':True})

files=sorted((BASE/'drills').glob('*.py'))
assert len(files)==12 and list(expected)==[f'D{i:02}' for i in range(1,13)]
dependencies=[ROOT/'examples/product-analytics'/folder/name for folder,name in [
    ('module-0-product-thinking','case.json'),('module-0-product-thinking','workshop.py'),
    ('module-1-pricing-unit-economics','economics.py'),
    ('module-4-marketing-measurement-data-visualization','case.json'),
    ('module-4-marketing-measurement-data-visualization','measurement.py')]]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [*files,*dependencies,catalog_path]}
for index,path in enumerate(files,1):
    key=f'D{index:02}'
    result=subprocess.run([sys.executable,'-I','-B',str(path)],cwd=ROOT,capture_output=True,
                          text=True,timeout=20,check=True)
    assert not result.stderr,(key,result.stderr)
    value=json.loads(result.stdout)
    assert value==expected[key],(key,value,expected[key])
    observations[key]=value
    workers.append({'id':key,'source':path.relative_to(BASE).as_posix(),'exit_code':result.returncode,
                    'source_sha256':before[path]})
    record('isolated-output',key+' matches independent expected answer')

syllabus=json.loads((BASE.parent/'roadmap/syllabus.json').read_text(encoding='utf-8'))
assert len(coverage)==6
for row,planned in zip(coverage,syllabus):
    assert row['id']==planned['label'] and row['route']=='/docs/product-analytics/'+planned['slug']
    assert row['title']==planned['title']
    chapter=ROOT/row['chapter']
    assert chapter.exists() and f"part-{planned['part']}-" in chapter.name
    assert row['id'] in chapter.read_text(encoding='utf-8'),row['id']
    record('coverage',row['id']+' canonical chapter and syllabus mapping')

expected_projects={'neosophical','datsol','10x','zyke','load-balancer','megalith','membition'}
assert {row['project_id'] for row in stories}==expected_projects
assert len(catalog['sources'])==2
for story in stories:
    assert story['evidence_class']=='resume-reported' and not story['original_impact_verified']
    for source in catalog['sources']:
        matches=[row for row in source['excerpts'] if row['project_id']==story['project_id']]
        assert len(matches)==1
        assert matches[0]['evidence_class']=='resume-reported'
        assert not matches[0]['original_code_or_metrics_reproduced']
        assert matches[0]['page']>=1 and matches[0]['anchor'] and matches[0]['text']
    record('catalogue',story['project_id']+' appears in both resume sources as an unverified self-report')
fingerprints={}
for source in catalog['sources']:
    path=ROOT/source['file']
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==source['sha256'],source['file']
    fingerprints[source['file']]=digest
    record('source-fingerprint',source['file']+' matches the existing evidence catalogue')
assert all(hashlib.sha256(path.read_bytes()).hexdigest()==digest for path,digest in before.items())
assert len(checks)==27
proof={'verified_date':'2026-10-18','python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
       'total':len(checks),'isolated_output_checks':12,'source_and_coverage_checks':15,
       'checks':checks,'observations':observations,'workers':workers,'all_workers_exited':True,
       'source_fingerprints':fingerprints,'catalogue_sha256':before[catalog_path],
       'input_and_dependency_sources_unchanged':True,
       'dependency_sha256':{path.relative_to(ROOT).as_posix():before[path] for path in dependencies},
       'external_services_called':False,'persistent_listener_started':False,
       'sqlite_scope':'D07 uses a real in-memory database and closes it before its worker exits',
       'historical_suites_rerun':False,
       'scope':'Fresh synthetic output drills plus curriculum/source provenance checks; not original resume impact, full historical suites or learner interview assessment.'}
(BASE/'drill-output.json').write_text(json.dumps(observations,indent=2)+'\n',encoding='utf-8')
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'isolated_drills':12,'source_and_coverage_audits':15,
                  'python':proof['python'],'sqlite':proof['sqlite'],'workers_exited':True},indent=2))
