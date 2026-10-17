"""Fresh document/provenance and manual-helper audit, not historical runtime reruns."""
from pathlib import Path
import hashlib
import json
import platform
import re
from revision import QUESTIONS, DEMO, MOCK, review

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
meta = json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
catalogue = json.loads((BASE/'catalogue.json').read_text(encoding='utf-8'))
answers = json.loads((BASE/'answers.json').read_text(encoding='utf-8'))
text = (ROOT/'System Design Notes'/meta['chapter']).read_text(encoding='utf-8')
checks = []


def check(group,name,value):
    assert value,(group,name)
    checks.append({'group':group,'name':name,'passed':True})


check('catalogue','all foundations and fourteen systems in numeric order',
    [e['label'] for e in catalogue]==[f'A{i}' for i in range(5)]+[f'S{i}' for i in range(14)]
    and [e['module'] for e in catalogue]==list(range(19)))
routes = {'/docs/system-design','/docs/system-design/consolidation','/docs/resume-skills'}|{e['route'] for e in catalogue}
for path in (ROOT/'Resume Skills Notes').glob('*.md'):
    match = re.search(r'module-\d+-(.+)\.md$',path.name)
    if match:
        routes.add('/docs/resume-skills/'+match[1])
for entry in catalogue:
    label = entry['label']
    folder = BASE.parent/entry['example']
    chapter = ROOT/'System Design Notes'/entry['chapter']
    body = chapter.read_text(encoding='utf-8')
    proof_path = folder/'verification-results.json'
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    content = json.loads((folder/'content-validation.json').read_text(encoding='utf-8'))
    check('provenance',label+' chapter/proof hashes current',
        hashlib.sha256(chapter.read_bytes()).hexdigest()==entry['chapter_sha256']
        and hashlib.sha256(proof_path.read_bytes()).hexdigest()==entry['proof_sha256'])
    check('provenance',label+' recorded receipts internally consistent',
        proof['total']==len(proof['checks'])==sum(proof['counts'].values())==entry['recorded_assertions']
        and all(c['passed'] for c in proof['checks']) and proof['verified_date']==entry['verified_date'])
    check('teaching',label+' exact source fidelity',all((folder/source).read_text(encoding='utf-8') in body for source in content['source_fidelity']))
    questions = re.findall(r'^### Q(\d+)\.',body,re.M)
    check('teaching',label+' thirty sequential Q&As',[int(q) for q in questions]==list(range(1,31)))
    check('teaching',label+' ten tasks and unchecked learning',len(re.findall(r'^- \[ \]',body,re.M))==12
        and len(re.findall(r'^\d+\. ',body.split('## 20. Practice tasks')[1].split('---')[0],re.M))==10)
    check('links',label+' local teaching links resolve',set(re.findall(r'\]\((/docs/[^)]+)\)',body))<=routes)
check('catalogue','recorded teaching assertion sum preserved',sum(e['recorded_assertions'] for e in catalogue)==meta['historical_recorded_assertions']==1600)
check('catalogue','all planned files exist and syllabus available',len(list((ROOT/'System Design Notes').glob('*.md')))==21
    and all(e['status']=='Available' for e in json.loads((BASE.parent/'roadmap/syllabus.json').read_text(encoding='utf-8'))))
check('bank','all original prompts/checkpoints preserved',hashlib.sha256((ROOT/'Architecture-System-Design-Question-Bank.md').read_bytes()).hexdigest()==meta['source_bank_sha256'])
check('bank','sixty ordered bank drill headings',re.findall(r'^### (Q\d{2})\.',text,re.M)==[f'Q{i:02}' for i in range(1,61)])
for q in QUESTIONS:
    check('bank',q['id']+' prompt checkpoint expansion present',q['question'] in text and q['checkpoints'] in text and answers[q['id']] in text and len(answers[q['id']].split())>=40)
check('structure','all 22 sections ordered',[int(i) for i in re.findall(r'^## (\d+)\.',text,re.M)]==list(range(1,23)))
check('structure','all 24 self-tests ordered',re.findall(r'^### (T\d{2})\.',text,re.M)==[f'T{i:02}' for i in range(1,25)])
check('structure','fourteen failure cards',re.findall(r'^\| (F\d{2}) /',text,re.M)==[f'F{i:02}' for i in range(1,15)])
pairs = text.split('## 5. Twenty-four confusable pairs')[1].split('## 6.')[0]
check('structure','twenty-four confusable pairs',len(re.findall(r'^\| ',pairs,re.M))-2==24)
check('structure','six distinct mock prompts',re.findall(r'^\*\*Mock (M\d)',text,re.M)==[f'M{i}' for i in range(1,7)])
check('structure','ten practice tasks',len(re.findall(r'^\d+\. ',text.split('## 20. Practice tasks')[1].split('---')[0],re.M))==10)
check('structure','twelve learning items remain unchecked',len(re.findall(r'^- \[ \]',text,re.M))==12 and not re.search(r'^- \[x\]',text,re.M))
check('fidelity','exact helper source and demo output', (BASE/'revision.py').read_text(encoding='utf-8') in text and json.dumps(review(DEMO),indent=2) in text)
check('fidelity','chapter footprint and no placeholders',len(text.split())==meta['words'] and text.count('\n')==meta['lines'] and '{{' not in text)
check('links','all consolidation internal links resolve',set(re.findall(r'\]\((/docs/[^)]+)\)',text))<=routes)
check('timing','standard mock sums 45',sum(n for _,n in MOCK)==45)
check('timing','seven day route sums 840',7*120==meta['timing_minutes']['seven_day']==840)
check('timing','three day route sums 450',3*150==meta['timing_minutes']['three_day']==450)
check('timing','two hour route sums 120',20+30+45+15+10==meta['timing_minutes']['final_review']==120)
demo = review(DEMO)
check('helper','partial score denominator and unassessed count',demo['manual_points']==12 and demo['maximum_for_assessed']==24 and demo['assessed']==8 and demo['unassessed']==52)
check('helper','weakest question mapped first',demo['next_cards'][0]['id']=='Q23' and demo['next_cards'][0]['revisit']==['A4','S11'])
check('helper','empty worksheet not graded',review({})['maximum_for_assessed']==0 and review({})['unassessed']==60 and not review({})['automatically_graded'])
full = review({q['id']:3 for q in QUESTIONS})
check('helper','full manual maximum and no weak cards',full['manual_points']==180 and full['next_cards']==[] and not full['interview_outcome_predicted'])
for name,scores in [('unknown question',{'Q61':1}),('boolean score',{'Q01':True}),('negative score',{'Q01':-1}),
    ('score above rubric',{'Q01':4}),('fractional score',{'Q01':1.5}),('unfilled null',{'Q01':None})]:
    try:
        review(scores)
    except ValueError:
        check('helper',name+' rejected',True)
    else:
        raise AssertionError(name)
check('boundaries','authoring learner and historical evidence distinguished',
    'not a claim that every historical runtime/engine was freshly executed today' in text
    and 'It is not your score' in text and 'P0–P5 remains later work' in text)
proof = {'label':'Revision','verified_date':'2026-10-18','python':platform.python_version(),
    'kind':'document-provenance-and-manual-helper-audit','total':len(checks),'checks':checks,
    'counts':{group:sum(c['group']==group for c in checks) for group in sorted({c['group'] for c in checks})},
    'observations':{'teaching_chapters':19,'authored_track_files':21,'bank_drills':60,'self_tests':24,'failure_cards':14,
        'mock_scenarios':6,'recorded_historical_assertions':1600,'fresh_historical_runtime_reruns':False,'manual_demo':demo},
    'scope':'Fresh source/provenance/link/structure audit and real manual-score helper execution. Historical teaching receipts are audited, not rerun; no learner mastery or production guarantee.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
meta.update(verified_document_checks=proof['total'],all_teaching_links_resolve=True)
(BASE/'content-validation.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'label':'Revision','fresh_document_helper_checks':proof['total'],'recorded_teaching_assertions':1600,'authored_files':21},indent=2))
