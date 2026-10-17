"""Generate final revision chapter and a provenance catalogue of 19 teaching chapters."""
from pathlib import Path
import hashlib
import json
import re
from revision import QUESTIONS, DEMO, MOCK, review

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
entries = json.loads((BASE.parent/'roadmap/syllabus.json').read_text(encoding='utf-8'))[:-1]
answers = json.loads((BASE/'answers.json').read_text(encoding='utf-8'))
assert set(answers)=={q['id'] for q in QUESTIONS}
catalogue = []
for entry in entries:
    folder = {0:'module-0-design-method',1:'module-1-application-architecture'}.get(entry['module'],f"module-{entry['module']}-{entry['slug']}")
    example = BASE.parent/folder
    meta = json.loads((example/'content-validation.json').read_text(encoding='utf-8'))
    proof = json.loads((example/'verification-results.json').read_text(encoding='utf-8'))
    chapter = ROOT/'System Design Notes'/entry['file']
    catalogue.append({'label':entry['label'],'module':entry['module'],'part':entry['part'],'title':entry['title'],
        'route':'/docs/system-design/'+entry['slug'],'chapter':entry['file'],'example':folder,
        'recorded_assertions':proof['total'],'verified_date':proof['verified_date'],
        'runtime':{k:proof[k] for k in ('python','node','typescript','sqlite','os') if k in proof},
        'scope':proof.get('scope','See the chapter and its verification artifact for exact evidence boundaries.'),
        'source_fidelity':meta['source_fidelity'],
        'chapter_sha256':hashlib.sha256(chapter.read_bytes()).hexdigest(),
        'proof_sha256':hashlib.sha256((example/'verification-results.json').read_bytes()).hexdigest()})
(BASE/'catalogue.json').write_text(json.dumps(catalogue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lookup = {e['label']:e for e in catalogue}


def cards(low,high):
    result = []
    for q in QUESTIONS[low-1:high]:
        labels = list(dict.fromkeys(re.findall(r'\b[AS]\d+\b',q['mapping'])))
        links = ', '.join(f"[{label}]({lookup[label]['route']})" for label in labels)
        result.append(f"### {q['id']}. {q['question']}\n\n**Original checkpoints:** {q['checkpoints']}\n\n{answers[q['id']]}\n\nRevisit: {links}.\n")
    return '\n'.join(result)


table = '| Chapter | Teaching route | Recorded local assertions | Original verification date |\n| --- | --- | --- | --- |\n'
table += '\n'.join(f"| {e['label']} | [{e['title']}]({e['route']}) | {e['recorded_assertions']} | {e['verified_date']} |" for e in catalogue)
chapter = (BASE/'lesson.md').read_text(encoding='utf-8')
replacements = {'REVISION_CODE':'```python\n'+(BASE/'revision.py').read_text(encoding='utf-8')+'```',
    'SCORE_OUTPUT':'```json\n'+json.dumps(review(DEMO),indent=2)+'\n```',
    'CONCEPT_CARDS':cards(1,24),'SYSTEM_CARDS':cards(25,38),'FAILURE_CARDS':cards(39,52),'RESUME_CARDS':cards(53,60),
    'MOCK_TIMING':'\n'.join(f'| {name} | {minutes} |' for name,minutes in MOCK),
    'CATALOGUE_TABLE':table,'RECORDED_CHECKS':f"{sum(e['recorded_assertions'] for e in catalogue):,}"}
for tag,value in replacements.items():
    chapter = chapter.replace('{{'+tag+'}}',value)
assert '{{' not in chapter
filename = 'system-design-handbook-part-21-consolidation.md'
(ROOT/'System Design Notes'/filename).write_text(chapter,encoding='utf-8')
metadata = {'label':'Revision','chapter':filename,'slug':'consolidation','group':'revision',
    'words':len(chapter.split()),'lines':chapter.count('\n'),'bank_drills':60,'failure_cards':14,
    'self_test_questions':24,'confusable_pairs':24,'mock_scenarios':6,'mock_minutes':45,
    'timing_minutes':{'seven_day':840,'three_day':450,'final_review':120},
    'practice_tasks':10,'unchecked_learning_items':12,'source_fidelity':['revision.py'],
    'catalogue_teaching_chapters':len(catalogue),'historical_recorded_assertions':sum(e['recorded_assertions'] for e in catalogue),
    'source_bank_sha256':hashlib.sha256((ROOT/'Architecture-System-Design-Question-Bank.md').read_bytes()).hexdigest(),
    'scope':'Revision content, provenance inventory and manually supplied scoring; no automatic learner grading or fresh execution of historical engines.'}
(BASE/'content-validation.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:metadata[k] for k in ('label','words','lines','bank_drills','mock_scenarios','historical_recorded_assertions')},indent=2))
