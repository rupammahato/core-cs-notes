"""Audit case reasoning/fixture/output fidelity, coverage, links and previous notes."""
from collections import Counter
import hashlib
import json
import re
from build_book import case_markdown,START,END
from compute import BASE,calculate,displayed,fixture

ROOT=BASE.parents[1]
NOTES=ROOT/'Product Casebook Notes'
checks=[]


def check(name,condition):
    assert condition,name
    checks.append({'name':name,'passed':True})


def read_json(name):
    return json.loads((BASE/name).read_text(encoding='utf-8'))


files=sorted(NOTES.glob('*.md'))
texts={int(p.stem.split('-part-')[1].split('-')[0]):p.read_text(encoding='utf-8') for p in files}
book='\n'.join(texts.values())
cases=read_json('cases.json');proof=read_json('verification-results.json');results=read_json('results.json');inputs=fixture()
check('Nine sequential authored chapters',sorted(texts)==list(range(1,10)))
check('Eighteen sequential case definitions',[c['id'] for c in cases]==[f'C{n:02}' for n in range(1,19)])
check('Three cases per worked chapter',Counter(c['chapter'] for c in cases)=={part:3 for part in range(3,9)})
check('All 41 runtime checks passed',proof['total']==41==len(proof['checks']) and all(c['passed'] for c in proof['checks']))
check('Runtime breakdown matches claims',proof['breakdown']=={'reference':18,'changed-scenario':13,'invalid-input':8,'preservation':2})
check('Fresh calculation equals recorded output',calculate()==results)
check('Verified input and calculation sources unchanged',all(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest for name,digest in proof['source_sha256'].items()))
check('No real external operation claimed',not any(proof[k] for k in ['external_services_called','real_experiments_run','deployments_performed']))
for part in range(3,9):
    selected=[c for c in cases if c['chapter']==part];text=texts[part]
    check(f'Part {part}: case coverage in order',re.findall(r'^## (C\d{2})\.',text,re.M)==[c['id'] for c in selected])
    check(f'Part {part}: one marker pair',text.count(START)==text.count(END)==1)
    for case in selected:
        key=case['id'];section=text.split(f'## {key}. ',1)[1].split('\n## ',1)[0]
        check(key+': complete authored reasoning rendered',all(case[field] in section for field in [
            'title','prompt','framing','evidence','metric_contract','analysis','recommendation','change_mind','architecture','exercise']))
        check(key+': clarifications, options and four answered follow-ups',len(case['clarify'])==3 and len(case['options'])==3 and len(case['follow_ups'])==4 and
              all(value in section for value in case['clarify']+case['options']) and
              all(row['question'] in section and row['answer'] in section for row in case['follow_ups']))
        check(key+': complete fixture input shown','```json\n'+json.dumps(inputs[key],indent=2)+'\n```' in section)
        check(key+': actual output shown','```json\n'+json.dumps(displayed(results[key]),indent=2)+'\n```' in section)
        check(key+': generated block agrees with authored source and proof',case_markdown(case,inputs[key],results[key]) in text)

snapshot=read_json('prior-notes-snapshot.json')
check('All 144 earlier handbooks byte-identical',len(snapshot)==144 and all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in snapshot.items()))
content=ROOT/'study-guide/content/docs';routes=set()
for path in content.rglob('*.md'):
    subject=path.relative_to(content).parts[0]
    routes.add('/docs/'+subject+('' if path.stem=='index' else '/'+path.stem))
check('All 153 handbook routes generated',len(routes)==153)
for path in files:
    slug=path.stem.split('-part-',1)[1].split('-',1)[1]
    generated=list((content/'product-casebook').rglob(('index' if slug=='master-roadmap' else slug)+'.md'))
    check(path.stem+': generated body equals source',len(generated)==1 and generated[0].read_text(encoding='utf-8').split('---\n\n',1)[1].strip()==path.read_text(encoding='utf-8').split('\n\n',2)[2].strip())
check('Every new handbook documentation link resolves',all(url.rstrip('/') in routes for url in re.findall(r'\]\((/docs/[^)#\s]+)',book)))
research=read_json('research.json')
check('Thirteen primary chapter sources recorded',len(research['sources'])==13 and all(row['url'] in book for row in research['sources']))
revision=texts[9]
check('Thirty final oral checks',re.findall(r'^\| (O\d{2}) \|',revision,re.M)==[f'O{n:02}' for n in range(1,31)])
check('Twelve diagnosis cards',re.findall(r'^\| (D\d{2}) \|',revision,re.M)==[f'D{n:02}' for n in range(1,13)])
check('Twenty confusable pairs',len(revision.split('## 1. Twenty confusable pairs')[1].split('## 2.')[0].strip().splitlines())==22)
check('Two 45-minute mocks',len(re.findall(r'^## \d+\. Mock [AB]: .+, 45 minutes$',revision,re.M))==2)
check('Seventy-two rendered interviewer questions',len(re.findall(r'^\*\*F[1-4]\. ',book,re.M))==72)
check('Eighteen rendered case practice tasks',len(re.findall(r'^### Practice task$',book,re.M))==18)
check('Authoring checked, learner practice unchecked',len(re.findall(r'^- \[x\]',book,re.M))==3 and len(re.findall(r'^- \[ \]',book,re.M))==54)
check('Judgment is not claimed to be automatically verified','does not grade product judgment automatically' in texts[1] and 'cannot assess empathy' in revision)
check('Unavailable future value stays unknown',results['C12']['lifetime_value_cents'] is None and 'LTV remains unknown' in texts[6])
check('No replacement characters or trailing whitespace','\ufffd' not in book and all(line==line.rstrip() for line in book.splitlines()))
lines=sum(len(text.splitlines()) for text in texts.values())
check('Root catalogue matches actual counts',f'| **Product Casebook** | 9 | {lines:,} |' in (ROOT/'README.md').read_text(encoding='utf-8'))
result={'verified_date':'2026-10-21','total':len(checks),'checks':checks,'chapters':9,'lines':lines,
        'worked_cases':18,'answered_follow_ups':72,'case_practice_tasks':18,'final_oral_checks':30,
        'earlier_handbooks_byte_identical':144,'scope':'Content/source/coverage audits, separate from runtime arithmetic checks and manual product judgment.'}
(BASE/'content-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
