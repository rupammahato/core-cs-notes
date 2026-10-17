"""Generate the three independently authored lessons with exact shared/local code."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SPECS = [
    ('S4',9,11,'booking-reservations','booking.py','Ticket Booking and Limited-Inventory Reservation',
     ['holds','late_payment','http_contract','estimates'],'S5: Chat and real-time messaging'),
    ('S5',10,12,'chat-messaging','chat.py','Chat and Real-Time Messaging',
     ['durability','hints_and_permissions','concurrency','http_contract','estimates'],'S6: Social feed and photo sharing'),
    ('S6',11,13,'social-feed-photo-sharing','feed.py','Social Feed and Photo Sharing',
     ['fanout','visibility_and_pagination','concurrency','http_contract','estimates'],'S7: Background job scheduler and worker platform'),
]

for label,module,part,slug,source,title,outputs,next_section in SPECS:
    folder = BASE.parent/f'module-{module}-{slug}'
    proof = json.loads((folder/'verification-results.json').read_text(encoding='utf-8'))
    chapter = (folder/'lesson.md').read_text(encoding='utf-8')
    for tag,path in [('RUNTIME',BASE/'runtime.py'),('CORE',folder/source)]:
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
        'questions':30,'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':['../worked-systems-s4-s6/runtime.py',source],
        'output_fidelity':outputs,'mock_minutes':45,'verified_checks':proof['total'],'next':next_section}
    (folder/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metadata,indent=2))
