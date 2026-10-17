"""Generate S7-S9 with exact shared runtime, local source and observed outputs."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SPECS = [
    ('S7',12,14,'job-scheduler-workers','scheduler.py',
     ['effect_recovery','retry_deadline','admission','scheduling','http_contract','estimates'],'S8: Checkout, payments and credit ledger'),
    ('S8',13,15,'checkout-payments-credit-ledger','checkout.py',
     ['payment_recovery','binding','concurrency','rollback_reconciliation','http_contract','estimates'],'S9: Search and autocomplete'),
    ('S9',14,16,'search-autocomplete','search.py',
     ['permissions','version_fences','retrieval','rollback_rebuild','http_contract','estimates'],'S10: Load balancer and distributed cache'),
]

for label,module,part,slug,source,outputs,next_section in SPECS:
    folder = BASE.parent/f'module-{module}-{slug}'
    proof = json.loads((folder/'verification-results.json').read_text(encoding='utf-8'))
    chapter = (folder/'lesson.md').read_text(encoding='utf-8')
    for tag,path in [('RUNTIME',BASE.parent/'worked-systems-s4-s6/runtime.py'),('CORE',folder/source)]:
        chapter = chapter.replace('{{'+tag+'_CODE}}','```python\n'+path.read_text(encoding='utf-8')+'```')
    for name in outputs:
        chapter = chapter.replace('{{'+name.upper()+'_OUTPUT}}','```json\n'+json.dumps(proof['observations'][name],ensure_ascii=False,indent=2)+'\n```')
    for tag,value in [('DATE',proof['verified_date']),('PYTHON',proof['python']),('SQLITE',proof['sqlite']),('OS',proof['os']),
        ('TOTAL',str(proof['total'])),('COUNTS',', '.join(f"{count} {name.replace('_',' ')}" for name,count in proof['counts'].items()))]:
        chapter = chapter.replace('{{'+tag+'}}',value)
    assert '{{' not in chapter,(label,'unfilled template')
    filename = f'system-design-handbook-part-{part}-module-{module}-{slug}.md'
    (ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
    metadata = {'label':label,'chapter':filename,'words':len(chapter.split()),'lines':chapter.count('\n'),
        'questions':30,'practice_tasks':10,'unchecked_learning_items':12,
        'source_fidelity':['../worked-systems-s4-s6/runtime.py',source],'output_fidelity':outputs,
        'mock_minutes':45,'verified_checks':proof['total'],'next':next_section}
    (folder/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metadata,indent=2))
