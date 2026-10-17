"""Audit roadmap mappings, prerequisites and exact question-bank fidelity."""
from pathlib import Path
import hashlib
import json
import platform
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
content=json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
entries=json.loads((BASE/'syllabus.json').read_text(encoding='utf-8'))
questions=json.loads((BASE/'questions.json').read_text(encoding='utf-8'))
provenance=json.loads((BASE/'source-provenance.json').read_text(encoding='utf-8'))
text=(ROOT/'System Design Notes'/content['chapter']).read_text(encoding='utf-8')
checks=[]
def check(name,condition):
    if not condition:
        raise AssertionError(name)
    checks.append({'name':name,'passed':True})

labels=[e['label'] for e in entries]
index={label:i for i,label in enumerate(labels)}
check('Five foundations, fourteen worked designs, one consolidation',labels==[f'A{i}' for i in range(5)]+[f'S{i}' for i in range(14)]+['Revision'])
check('Teaching modules and part mapping cover 0-18 and 2-20',[(e['module'],e['part']) for e in entries[:-1]]==[(i,i+2) for i in range(19)] and entries[-1]['part']==21 and entries[-1]['module'] is None)
check('Planned filenames and slugs are unique',len({e['file'] for e in entries})==len({e['slug'] for e in entries})==20)
check('Planned filenames match sync-compatible numeric convention',all(e['file']==f"system-design-handbook-part-{e['part']}-module-{e['module']}-{e['slug']}.md" for e in entries[:-1]) and entries[-1]['file']=='system-design-handbook-part-21-consolidation.md')
check('Every prerequisite exists and precedes its section',all(prerequisite in index and index[prerequisite]<index[e['label']] for e in entries for prerequisite in e['prerequisites']))
pending={e['label']:set(e['prerequisites']) for e in entries}
order=[]
while pending:
    ready=[label for label,dependencies in pending.items() if not dependencies]
    if not ready:
        break
    for label in ready:
        order.append(label)
        del pending[label]
    for dependencies in pending.values():
        dependencies.difference_update(ready)
check('Dependency graph is acyclic and all sections reachable',len(order)==20 and not pending)
hours=[sum(e['hours'][i] for e in entries) for i in (0,1)]
check('Estimated hour arithmetic and range ordering agree',hours==content['estimated_active_hours']==[77,105] and all(0<e['hours'][0]<=e['hours'][1] for e in entries) and f'**{hours[0]}–{hours[1]} active hours**' in text)
available=[e for e in entries if e['status']=='Available']
check('Published sources match availability; future sections remain planned',len(list((ROOT/'System Design Notes').glob('*.md')))==1+len(available)==content['available_files'] and all((ROOT/'System Design Notes'/e['file']).exists()==(e['status']=='Available') for e in entries))
check('All 60 question IDs appear once and in order',[q['id'] for q in questions]==[f'Q{i:02}' for i in range(1,61)] and re.findall(r'^\| (Q\d{2}) \|',text,re.M)==[q['id'] for q in questions])
source=ROOT/provenance['question_bank']['file']
source_text=source.read_text(encoding='utf-8')
check('Question source checksum and exact rows preserved',hashlib.sha256(source.read_bytes()).hexdigest()==provenance['question_bank']['sha256'] and all(q['source_row'] in source_text and q['source_row'] in text for q in questions))
check('System prompts Q25-Q38 map to S0-S13',[q['mapping'] for q in questions[24:38]]==[f'S{i}' for i in range(14)])
check('Failure prompts Q39-Q52 map to S0-S13',[q['mapping'] for q in questions[38:52]]==[f'S{i}' for i in range(14)])
check('Every question architecture target exists',all(label in index for q in questions for label in re.findall(r'\b[AS]\d+\b',q['mapping'])))
resume_files={int(match[1]):path for path in (ROOT/'Resume Skills Notes').glob('*.md') if (match:=re.search(r'module-(\d+)-',path.name))}
check('All resume prerequisites reference existing modules',all(module in resume_files for e in entries for module in e['resume_modules']))
valid_routes={'/docs/resume-skills','/docs/system-design'}|{'/docs/resume-skills/'+re.search(r'module-\d+-(.+)\.md$',path.name)[1] for path in resume_files.values()}|{'/docs/system-design/'+e['slug'] for e in available}
linked=set(re.findall(r'\]\((/docs/[^)]+)\)',text))
check('Internal links point only to available content',linked<=valid_routes and len(linked)>20)
check('Twenty learning items remain unchecked',len(re.findall(r'^- \[ \]',text,re.M))==20 and not re.search(r'^- \[x\]',text,re.M))
check('Content footprint and completed/planned boundaries agree',len(text.split())==content['words'] and text.count('\n')==content['lines'] and 'No planned architecture teaching chapter remains unfinished.' in text and len(available)==20 and all(e['status']=='Available' for e in entries) and content['planned_files']==len(entries)+1==21)
proof={'checked_date':'2026-10-18','python':platform.python_version(),'total':len(checks),'checks':checks,'observations':{'foundations':5,'worked_systems':14,'consolidation':1,'planned_files':21,'available_files':content['available_files'],'question_groups':[24,14,14,8],'questions':len(questions),'prerequisite_order':order,'estimated_active_hours':hours,'existing_content_links':len(linked)},'scope':'Roadmap/document consistency only. No architecture implementation, runtime guarantee, production metric or learner mastery verified by this roadmap audit; each available chapter retains its own scope.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
