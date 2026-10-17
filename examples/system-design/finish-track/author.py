"""Generate the last worked chapter, then the final revision chapter."""
from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
folder = BASE.parent/'module-18-analytics-event-pipeline'
proof = json.loads((folder/'verification-results.json').read_text(encoding='utf-8'))
chapter = (folder/'lesson.md').read_text(encoding='utf-8')
outputs = ['time_metrics','recovery','rebuild','privacy','http_contract','estimates']
for tag,path in [('RUNTIME',BASE.parent/'worked-systems-s4-s6/runtime.py'),('CORE',folder/'pipeline.py')]:
    chapter = chapter.replace('{{'+tag+'_CODE}}','```python\n'+path.read_text(encoding='utf-8')+'```')
for name in outputs:
    chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}','```json\n'+json.dumps(proof['observations'][name],indent=2)+'\n```')
for tag,value in [('DATE',proof['verified_date']),('PYTHON',proof['python']),('SQLITE',proof['sqlite']),('OS',proof['os']),
    ('TOTAL',str(proof['total'])),('COUNTS',', '.join(f"{count} {name.replace('_',' ')}" for name,count in proof['counts'].items()))]:
    chapter = chapter.replace('{{'+tag+'}}',value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-20-module-18-analytics-event-pipeline.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
meta = {'label':'S13','chapter':filename,'slug':'analytics-event-pipeline','group':'worked-systems',
    'words':len(chapter.split()),'lines':chapter.count('\n'),'questions':30,'practice_tasks':10,
    'unchecked_learning_items':12,'source_fidelity':['../worked-systems-s4-s6/runtime.py','pipeline.py'],
    'output_fidelity':outputs,'mock_minutes':45,'verified_checks':proof['total'],'next':'Consolidation and design mocks'}
(folder/'content-validation.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print(json.dumps(meta,indent=2))
subprocess.run([sys.executable,'-X','utf8',str(BASE.parent/'consolidation/author.py')],cwd=ROOT,check=True)
