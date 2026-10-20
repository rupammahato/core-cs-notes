"""Audit handbook coverage, recorded output fidelity, links and source preservation."""
from collections import Counter
import hashlib
import json
import re
from build_book import case_markdown, START, END
from compute import BASE, calculate, displayed

ROOT = BASE.parents[1]
NOTES = ROOT/'Probability Statistics Notes'
checks = []


def check(name, condition):
    assert condition, name
    checks.append({'name': name, 'passed': True})


def read_json(name):
    return json.loads((BASE/name).read_text(encoding='utf-8'))


files = sorted(NOTES.glob('*.md'))
texts = {int(path.stem.split('-part-')[1].split('-')[0]): path.read_text(encoding='utf-8') for path in files}
book = '\n'.join(texts.values())
cases = read_json('cases.json')
proof = read_json('verification-results.json')
results = read_json('results.json')
check('Nine sequential authored chapters', sorted(texts) == list(range(1, 10)))
check('Thirty-five sequential case specifications', [c['id'] for c in cases] == [f'E{n:02}' for n in range(1, 36)])
check('Five worked cases per module', Counter(c['chapter'] for c in cases) == {n: 5 for n in range(2, 9)})
check('All 71 runtime checks passed', proof['total'] == 71 == len(proof['checks']) and all(c['passed'] for c in proof['checks']))
check('Runtime breakdown accurate', proof['breakdown'] == {'worked-example': 35, 'numerical-reference': 9, 'published-table': 3, 'boundary': 12, 'invalid-input': 10, 'preservation': 2})
check('Fresh calculations match recorded raw output', json.loads(json.dumps(calculate())) == results)
check('Verified calculation sources still match', all(hashlib.sha256((BASE/name).read_bytes()).hexdigest() == digest for name, digest in proof['source_sha256'].items()))
check('No simulation or service execution claimed', not proof['random_simulation_used'] and not proof['external_services_called'])

for part in range(2, 9):
    selected = [c for c in cases if c['chapter'] == part]
    text = texts[part]
    check(f'F{part-1}: case IDs once in order', re.findall(r'^### (E\d{2})\.', text, re.M) == [c['id'] for c in selected])
    check(f'F{part-1}: eight interview Q&As', re.findall(r'^### Q(\d+)\.', text, re.M) == [str(n) for n in range(1, 9)])
    check(f'F{part-1}: four practice tasks', re.findall(r'^([1-4])\. ', text, re.M) == ['1', '2', '3', '4'])
    check(f'F{part-1}: one generated-example marker pair', text.count(START) == text.count(END) == 1)
    for case in selected:
        key = case['id']
        section = text.split(f'### {key}. ', 1)[1].split('\n### E', 1)[0].split(END, 1)[0]
        check(key + ': exact prompt, hint, derivation, trap and follow-up', all(case[field] in section for field in ['title', 'question', 'hint', 'derivation', 'trap', 'follow_up']))
        check(key + ': displayed JSON equals actual calculation', '```json\n'+json.dumps(displayed(results[key]), indent=2)+'\n```' in section)
        check(key + ': generated example matches authored source and verified output', case_markdown(case, results[key]) in text)

snapshot = read_json('prior-notes-snapshot.json')
check('135 earlier handbooks remain byte-identical', len(snapshot) == 135 and all(
    hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest for name, digest in snapshot.items()))
routes = set()
content = ROOT/'study-guide/content/docs'
for file in content.rglob('*.md'):
    subject = file.relative_to(content).parts[0]
    routes.add('/docs/'+subject+('' if file.stem == 'index' else '/'+file.stem))
check('All 144 handbook routes generated', len(routes) == 144)
for file in files:
    slug = file.stem.split('-part-', 1)[1].split('-', 1)[1]
    generated = list((content/'probability-statistics').rglob(('index' if slug == 'master-roadmap' else slug)+'.md'))
    text = file.read_text(encoding='utf-8')
    check(file.stem + ': generated body matches authored note', len(generated) == 1 and
          generated[0].read_text(encoding='utf-8').split('---\n\n', 1)[1].strip() == text.split('\n\n', 2)[2].strip())
check('New-book documentation links resolve', all(link.rstrip('/') in routes for link in re.findall(r'\]\((/docs/[^)#\s]+)', book)))
research = read_json('research.json')
check('Twenty primary chapter sources recorded and linked', len(research['sources']) == 20 and all(row['url'] in book for row in research['sources']))
revision = texts[9]
check('Thirty final oral checks', re.findall(r'^\| (O\d{2}) \|', revision, re.M) == [f'O{n:02}' for n in range(1, 31)])
check('Ten diagnosis cards', re.findall(r'^\| (D\d{2}) \|', revision, re.M) == [f'D{n:02}' for n in range(1, 11)])
check('Twenty confusable pairs', len(revision.split('## 1. Twenty confusable pairs')[1].split('## 2.')[0].strip().splitlines()) == 22)
check('Two 45-minute mocks', len(re.findall(r'^## \d+\. Mock [AB]: .+, 45 minutes$', revision, re.M)) == 2)
check('Learner checklists not marked completed', len(re.findall(r'^- \[ \]', book, re.M)) == 29 and len(re.findall(r'^- \[x\]', book, re.M)) == 3)
check('Empirical bootstrap boundary explicit', 'not an exact confidence-coverage guarantee' in texts[6] and 'not exact confidence coverage' in (BASE/'README.md').read_text(encoding='utf-8'))
check('Sequential and causal boundaries explicit', 'not their calculated error rate' in texts[7] and 'not a randomized treatment/control analysis' in texts[8])
check('No replacement characters or trailing whitespace', '\ufffd' not in book and all(line == line.rstrip() for line in book.splitlines()))
lines = sum(len(text.splitlines()) for text in texts.values())
check('Root catalogue matches actual counts', f'| **Probability & Statistics** | 9 | {lines:,} |' in (ROOT/'README.md').read_text(encoding='utf-8'))
result = {'verified_date': '2026-10-21', 'total': len(checks), 'checks': checks, 'chapters': 9,
          'lines': lines, 'worked_examples': 35, 'module_interview_qas': 56, 'practice_tasks': 28,
          'oral_checks': 30, 'prior_handbooks_unchanged': 135,
          'scope': 'Documentation fidelity, source preservation and coverage audits, separate from 71 runtime checks.'}
(BASE/'content-validation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'checks'}, indent=2))
