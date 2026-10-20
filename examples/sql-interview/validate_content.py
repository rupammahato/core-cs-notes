"""Audit authored query fidelity, coverage, source preservation and local links."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from build_book import groups, table
from lab import BASE, connect, load_fixture, parameters
from reference import expected

ROOT = BASE.parents[1]
NOTES = ROOT / 'SQL Interview Notes'
checks = []


def check(name, condition):
    assert condition, name
    checks.append({'name': name, 'passed': True})


def read_json(name):
    return json.loads((BASE / name).read_text(encoding='utf-8'))


proof = read_json('verification-results.json')
output = read_json('query-output.json')
problems = read_json('problems.json')
files = sorted(NOTES.glob('*.md'))
texts = {path.name: path.read_text(encoding='utf-8') for path in files}
book = '\n'.join(texts.values())
check('Seven complete chapters', len(files) == 7)
check('Thirty numbered problem definitions', [p['id'] for p in problems] == [f'Q{n:02}' for n in range(1, 31)])
check('Runtime checks all passed', proof['total'] == 86 == len(proof['checks']) and all(c['passed'] for c in proof['checks']))
check('Runtime check breakdown', Counter(c['group'] for c in proof['checks']) == {
    'query-output': 30, 'insertion-order': 30, 'mutation': 12, 'counterexample': 6,
    'constraint': 4, 'query-plan': 3, 'preservation': 1})
check('Independent reference agrees with saved actual rows', output == proof['observations'] == expected(load_fixture(), parameters()))
check('Runtime source hashes still match', all(hashlib.sha256((BASE / name).read_bytes()).hexdigest() == value
                                               for name, value in proof['source_sha256'].items()))
check('Runtime resources closed and scope explicit', proof['connections_closed'] == 16 and not any(
    proof[key] for key in ['persistent_database_created', 'persistent_listener_started', 'external_services_called', 'postgresql_executed']))

for group, part, slug, *_ in groups:
    text = texts[f'sql-interview-handbook-part-{part}-{slug}.md']
    selected = [p for p in problems if p['group'] == group]
    check(f'{group}: ordered question coverage', re.findall(r'^## (Q\d{2})\.', text, re.M) == [p['id'] for p in selected])
    for problem in selected:
        key = problem['id']
        section = text.split(f'## {key}. ', 1)[1].split('\n## ', 1)[0]
        sql = (BASE / problem['query']).read_text(encoding='utf-8').rstrip()
        check(key + ': exact executed SQL', f'```sql\n{sql}\n```' in section)
        check(key + ': actual output rendered', '### Verified output\n\n' + table(output[key]) in section)
        check(key + ': complete teaching explanation', all(problem[field] in section for field in [
            'title', 'prompt', 'hint', 'reasoning', 'trap', 'follow_up']))

method = texts['sql-interview-handbook-part-2-dataset-and-solving-method.md']
fixture = load_fixture()
db = connect()
try:
    for name, rows in fixture['tables'].items():
        columns = [row['name'] for row in db.execute(f'PRAGMA table_info({name})')]
        display = [{column + ' (UTC)' if column.endswith('_ts') else column:
                    datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if column.endswith('_ts') else value
                    for column, value in zip(columns, values)} for values in rows]
        check(name + ': complete fixture shown', f'### {name}\n\n' + table(display) in method)
finally:
    db.close()

snapshot = read_json('prior-notes-snapshot.json')
check('All 128 previous handbooks byte-identical', len(snapshot) == 128 and all(
    hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in snapshot.items()))
routes = set()
content = ROOT / 'study-guide/content/docs'
for file in content.rglob('*.md'):
    subject = file.relative_to(content).parts[0]
    routes.add('/docs/' + subject + ('' if file.stem == 'index' else '/' + file.stem))
check('All 135 handbook routes generated', len(routes) == 135)
for file in files:
    slug = file.stem.split('-part-', 1)[1].split('-', 1)[1]
    generated = list((content / 'sql-interview').rglob(('index' if slug == 'master-roadmap' else slug) + '.md'))
    check(file.stem + ': generated body matches authored note', len(generated) == 1 and
          generated[0].read_text(encoding='utf-8').split('---\n\n', 1)[1].strip() == texts[file.name].split('\n\n', 2)[2].strip())
links = re.findall(r'\]\((/docs/[^)#\s]+)', book)
check('Every new-book documentation link resolves', all(link.rstrip('/') in routes for link in links))
check('Ten primary research sources linked', len(read_json('research.json')['sources']) == 10 and all(
    row['url'] in book for row in read_json('research.json')['sources']))
check('Learner and authoring checklists kept separate', len(re.findall(r'^- \[ \]', book, re.M)) == 27 and len(re.findall(r'^- \[x\]', book, re.M)) == 4)
revision = texts['sql-interview-handbook-part-7-consolidation-and-mocks.md']
check('Twenty-four oral checks', re.findall(r'^\| (O\d{2}) \|', revision, re.M) == [f'O{n:02}' for n in range(1, 25)])
check('Twelve diagnosis cards', re.findall(r'^\| (D\d{2}) \|', revision, re.M) == [f'D{n:02}' for n in range(1, 13)])
check('Twelve practice tasks', len(re.findall(r'^\d+\. ', revision, re.M)) == 12)
check('Two 45-minute mocks', len(re.findall(r'^## \d+\. Mock [AB]: .+, 45 minutes$', revision, re.M)) == 2)
check('Eighteen confusable pairs', len(revision.split('## 2. Eighteen confusable pairs')[1].split('## 3.')[0].strip().splitlines()) == 20)
check('Six actual counterexamples preserved', len(read_json('counterexamples.json')) == 6)
check('UTC cohort and snapshot boundaries documented', 'UTC-midnight cohort anchors' in method and 'snapshot' in method and 'PostgreSQL' in method)
check('No trailing whitespace or replacement characters in new notes', all(
    '\ufffd' not in text and all(line == line.rstrip() for line in text.splitlines()) for text in texts.values()))
lines = sum(len(text.splitlines()) for text in texts.values())
check('Root catalogue matches actual chapter and line counts', f'| **SQL Interview Lab** | 7 | {lines:,} |' in (ROOT / 'README.md').read_text(encoding='utf-8'))
result = {'verified_date': '2026-10-20', 'checks': checks, 'total': len(checks), 'chapters': 7,
          'lines': lines, 'query_problems': 30, 'prior_handbooks_unchanged': 128,
          'scope': 'Content fidelity and source audits; not additional runtime query checks or learner completion.'}
(BASE / 'content-validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'checks'}, indent=2))
