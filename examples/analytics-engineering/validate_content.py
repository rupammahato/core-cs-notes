"""Documentation, executed-model, trace, link and source-preservation audits."""
from collections import Counter
import hashlib
import json
import re
from build_book import START,END,displayed,lesson_markdown
from warehouse import BASE,fixture

ROOT=BASE.parents[1];NOTES=ROOT/'Analytics Engineering Notes';checks=[]


def check(name,condition):
    assert condition,name
    checks.append({'name':name,'passed':True})


def read_json(name):
    return json.loads((BASE/name).read_text(encoding='utf-8'))


files=sorted(NOTES.glob('*.md'))
texts={int(p.stem.split('-part-')[1].split('-')[0]):p.read_text(encoding='utf-8') for p in files}
book='\n'.join(texts.values());lessons=read_json('lessons.json');proof=read_json('verification-results.json');output=read_json('observations.json')
check('Ten sequential chapters',sorted(texts)==list(range(1,11)))
check('Thirty-two sequential trace definitions',[row['id'] for row in lessons]==[f'L{n:02}' for n in range(1,33)])
check('Four traces per teaching module',Counter(row['chapter'] for row in lessons)=={part:4 for part in range(2,10)})
check('All 74 runtime checks passed',proof['total']==74==len(proof['checks']) and all(row['passed'] for row in proof['checks']))
check('Runtime breakdown sum matches total',sum(proof['breakdown'].values())==74 and proof['breakdown']['quality']==24 and proof['breakdown']['independent-reference']==9)
check('All verified sources still match',all(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest for name,digest in proof['source_sha256'].items()))
check('Four owned connections closed',proof['connections_opened']==proof['connections_closed']==4)
check('Execution boundaries explicit',not any(proof[key] for key in ['persistent_database_created','external_services_called','dbt_executed','airflow_executed']))
for part in range(2,10):
    selected=[row for row in lessons if row['chapter']==part];text=texts[part]
    check(f'Part {part}: traces in order',re.findall(r'^### (L\d{2})\.',text,re.M)==[row['id'] for row in selected])
    check(f'Part {part}: eight interview answers',re.findall(r'^### Q(\d+)\.',text,re.M)==[str(n) for n in range(1,9)])
    check(f'Part {part}: four practice tasks',re.findall(r'^([1-4])\. ',text,re.M)==['1','2','3','4'])
    check(f'Part {part}: one marker pair',text.count(START)==text.count(END)==1)
    for lesson in selected:
        key=lesson['id'];section=text.split(f'### {key}. ',1)[1].split('\n### L',1)[0].split(END,1)[0]
        check(key+': complete teaching text',all(lesson[field] in section for field in ['title','question','reasoning','trap','follow_up']))
        check(key+': recorded output faithfully displayed','```json\n'+json.dumps(displayed(output[key]),indent=2)+'\n```' in section)
        check(key+': exact generated trace',lesson_markdown(lesson,output[key]) in text)
        if lesson.get('model'):
            check(key+': actual SQL source printed unchanged','```sql\n'+(BASE/lesson['model']).read_text(encoding='utf-8').rstrip()+'\n```' in section)
check('Three executed model SQL listings',sum('model' in row for row in lessons)==3)
data=fixture();envelopes=[row for batch in data['batches'] for row in batch]
check('Complete 25-envelope source fixture shown',len(envelopes)==25 and all(
    row['delivery_id'] in texts[2] and json.dumps(row['payload'],sort_keys=True,separators=(',',':')) in texts[2] for row in envelopes))
check('Complete illustrative line input shown',json.dumps(data['illustrative_order_lines'],indent=2) in texts[2])
snapshot=read_json('prior-notes-snapshot.json')
check('All 153 earlier handbooks byte-identical',len(snapshot)==153 and all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in snapshot.items()))
content=ROOT/'study-guide/content/docs';routes=set()
for path in content.rglob('*.md'):
    subject=path.relative_to(content).parts[0]
    routes.add('/docs/'+subject+('' if path.stem=='index' else '/'+path.stem))
check('All 163 handbook routes generated',len(routes)==163)
for path in files:
    slug=path.stem.split('-part-',1)[1].split('-',1)[1]
    generated=list((content/'analytics-engineering').rglob(('index' if slug=='master-roadmap' else slug)+'.md'))
    check(path.stem+': generated body equals source',len(generated)==1 and generated[0].read_text(encoding='utf-8').split('---\n\n',1)[1].strip()==path.read_text(encoding='utf-8').split('\n\n',2)[2].strip())
check('Every documentation bridge resolves',all(url.rstrip('/') in routes for url in re.findall(r'\]\((/docs/[^)#\s]+)',book)))
research=read_json('research.json')
check('Twelve primary sources recorded and linked',len(research['sources'])==12 and all(row['url'] in book for row in research['sources']))
revision=texts[10]
check('Thirty final oral checks',re.findall(r'^\| (O\d{2}) \|',revision,re.M)==[f'O{n:02}' for n in range(1,31)])
check('Twelve diagnosis cards',re.findall(r'^\| (D\d{2}) \|',revision,re.M)==[f'D{n:02}' for n in range(1,13)])
check('Twenty confusable pairs',len(revision.split('## 1. Twenty confusable pairs')[1].split('## 2.')[0].strip().splitlines())==22)
check('Two 45-minute mocks',len(re.findall(r'^## \d+\. Mock [AB]: .+, 45 minutes$',revision,re.M))==2)
check('Learner checklists remain unchecked',len(re.findall(r'^- \[ \]',book,re.M))==31 and len(re.findall(r'^- \[x\]',book,re.M))==3)
check('Full-recompute and dbt boundaries stated','rebuilds full candidate dimensions' in texts[1] and 'No dbt engine or adapter runs' in texts[5])
check('Current-table and failure limits stated','Current fact/dimension tables are not immutable historical generations' in texts[8] and 'not a process-kill, power-loss or concurrent-reader experiment' in texts[7])
check('No trailing whitespace or replacement characters','\ufffd' not in book and all(line==line.rstrip() for line in book.splitlines()))
lines=sum(len(text.splitlines()) for text in texts.values())
check('Root catalogue matches actual lines',f'| **Analytics Engineering** | 10 | {lines:,} |' in (ROOT/'README.md').read_text(encoding='utf-8'))
result={'verified_date':'2026-10-21','total':len(checks),'checks':checks,'chapters':10,'lines':lines,
        'executed_traces':32,'module_interview_qas':64,'practice_tasks':32,'final_oral_checks':30,
        'earlier_handbooks_byte_identical':153,'scope':'Content/source/coverage fidelity, separate from 74 runtime checks and manual learner work.'}
(BASE/'content-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
