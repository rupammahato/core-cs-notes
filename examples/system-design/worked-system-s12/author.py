"""Generate S12 from authored prose, exact source and verified local observations."""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
FOLDER = BASE.parent/'module-17-multi-tenant-rag'
OUTPUTS = ['versioned_ingestion','atomic_ingestion','retrieval_isolation','permission_races',
    'generation_budget','validation_unknown','concurrency','deletion','http_contract','evaluation','estimates']
proof = json.loads((FOLDER/'verification-results.json').read_text(encoding='utf-8'))
chapter = (FOLDER/'lesson.md').read_text(encoding='utf-8')
for tag,path in [('RUNTIME',BASE.parent/'worked-systems-s4-s6/runtime.py'),('CORE',FOLDER/'rag.py')]:
    chapter = chapter.replace('{{'+tag+'_CODE}}','```python\n'+path.read_text(encoding='utf-8')+'```')
for name in OUTPUTS:
    chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}','```json\n'+json.dumps(proof['observations'][name],ensure_ascii=False,indent=2)+'\n```')
for tag,value in [('DATE',proof['verified_date']),('PYTHON',proof['python']),('SQLITE',proof['sqlite']),('OS',proof['os']),
    ('TOTAL',str(proof['total'])),('COUNTS',', '.join(f"{count} {name.replace('_',' ')}" for name,count in proof['counts'].items()))]:
    chapter = chapter.replace('{{'+tag+'}}',value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-19-module-17-multi-tenant-rag.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
dependency = '../module-16-multi-tenant-saas/saas.py'
metadata = {'label':'S12','chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),
    'questions':30,'practice_tasks':10,'unchecked_learning_items':12,
    'source_fidelity':['../worked-systems-s4-s6/runtime.py','rag.py'],
    'dependency_fidelity':[{'path':dependency,'sha256':hashlib.sha256((FOLDER/dependency).read_bytes()).hexdigest()}],
    'output_fidelity':OUTPUTS,'mock_minutes':45,'verified_checks':proof['total'],
    'next':'S13: Analytics event pipeline and dashboard'}
(FOLDER/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata,indent=2))
