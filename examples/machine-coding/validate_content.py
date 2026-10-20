"""Audit the book's executable evidence, coverage, links and protected prior notes."""
import hashlib
import json
import re
from build_book import NOTES, ROOT, source_section, trace_markdown
from fixtures import BASE, CASES, MODES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append({'name': name, 'passed': True})

    proof = json.loads((BASE / 'verification-results.json').read_text(encoding='utf-8'))
    observations = json.loads((BASE / 'observations.json').read_text(encoding='utf-8'))
    check('runtime proof and complete trace inventory', proof['total'] == 57 and proof['commands_checked'] == 5900
          and proof['direct_api_assertions'] == 14 and all(row['passed'] for row in proof['checks'])
          and set(observations) == {f'T{i:02}' for i in range(1, 33)})
    check('all tested sources unchanged', all(digest(BASE / name) == value for name, value in proof['source_sha256'].items()))
    files = sorted(NOTES.glob('*.md'))
    check('eleven ordered chapters', len(files) == 11 and sorted(int(re.search(r'part-(\d+)', p.name)[1]) for p in files) == list(range(1, 12)))
    texts = {path: path.read_text(encoding='utf-8') for path in files}
    for part, mode in enumerate(MODES, 3):
        path, = NOTES.glob(f'*-part-{part}-*.md'); text = texts[path]
        selected = [item for item in CASES if item['mode'] == mode]
        check(mode + ': exact compiled class', '```cpp\n' + source_section(mode) + '\n```' in text)
        check(mode + ': four exact recorded transcripts', len(selected) == 4 and all(
            observations[item['id']] == item['expected'] and trace_markdown(item, observations[item['id']]) in text for item in selected))
        check(mode + ': eight answered questions', re.findall(r'^### Q(\d+)\.', text, re.M) == [str(i) for i in range(1, 9)]
              and all(len(section.split()) >= 16 for section in re.split(r'^### Q\d+\.[^\n]*\n', text, flags=re.M)[1:]))
        check(mode + ': four learner practice tasks', len(re.findall(r'^- \[ \]', text, re.M)) == 4)
        check(mode + ': reasoning and architecture', all(word.lower() in text.lower() for word in ['Complexity', 'Architecture follow-up', 'invariant', 'Complete model implementation']))
    method, = NOTES.glob('*-part-2-*.md')
    check('complete compiled support header in method chapter', '```cpp\n' + (BASE / 'common.hpp').read_text(encoding='utf-8').rstrip() + '\n```' in texts[method])
    final, = NOTES.glob('*-part-11-*.md')
    final_text = texts[final]
    check('thirty answered oral checks', re.findall(r'^### O(\d+)\.', final_text, re.M) == [f'{i:02}' for i in range(1, 31)])
    check('two complete timed mocks with rubric', all(label in final_text for label in ['Mock A', 'Mock B', '60 minutes', 'Scoring rubric'])
          and final_text.count('**Acceptance tests:**') == final_text.count('**Expected design:**') == 2)
    check('learner tasks remain unchecked', not any(re.search(r'^- \[[xX]\]', text, re.M) for text in texts.values()))
    check('balanced code fences and no replacement characters', all(text.count('```') % 2 == 0 and '\ufffd' not in text for text in texts.values()))
    check('no trailing whitespace', all(line == line.rstrip() for text in texts.values() for line in text.splitlines()))
    snapshot = json.loads((BASE / 'prior-notes-snapshot.json').read_text(encoding='utf-8'))
    check('all 163 prior handbook files byte-identical', len(snapshot) == 163 and all(digest(ROOT / name) == value for name, value in snapshot.items()))
    content = ROOT / 'study-guide/content/docs'
    generated = list(content.rglob('*.md'))
    routes = {'/docs/' + p.relative_to(content).parts[0] + ('' if p.stem == 'index' else '/' + p.stem) for p in generated}
    check('174 unique generated handbook routes', len(generated) == len(routes) == 174)
    new_generated = list((content / 'machine-coding').rglob('*.md'))
    check('eleven generated machine-coding pages', len(new_generated) == 11)
    links = {link for text in texts.values() for link in re.findall(r'\]\((/docs/[^)]+)\)', text)}
    check('every handbook bridge resolves', links and all(link.split('#')[0] in routes for link in links))
    meta = json.loads((content / 'machine-coding/meta.json').read_text(encoding='utf-8'))
    check('machine-coding subject and four groups', meta['title'] == 'Machine Coding' and meta['root'] and len(meta['pages']) == 5)
    check('search subject filter registered', "value: 'machine-coding'" in (ROOT / 'study-guide/components/search-dialog.tsx').read_text(encoding='utf-8'))
    line_count = sum(len(text.splitlines()) for text in texts.values())
    check('README catalogue matches actual chapter/line counts', f'| **Machine Coding** | 11 | {line_count:,} |' in (ROOT / 'README.md').read_text(encoding='utf-8'))
    research = json.loads((BASE / 'research.json').read_text(encoding='utf-8'))
    all_text = '\n'.join(texts.values())
    check('five primary-source references appear in book', len(research['sources']) == 5 and all(row['url'] in all_text for row in research['sources']))
    check('scope and evidence boundaries stated', all(label in all_text for label in ['No performance benchmark', 'single-threaded', 'editorial practice', 'allocation-failure', 'Informational']))
    result = {'verified_date': '2026-10-21', 'total': len(checks), 'checks': checks, 'chapters': len(files),
              'lines': line_count, 'implementations': 8, 'worked_traces': 32, 'interview_answers': 64,
              'practice_tasks': 32, 'oral_checks': 30, 'mocks': 2, 'protected_prior_files': len(snapshot),
              'internal_bridge_routes': sorted(links), 'source_sha256': {str(path.relative_to(ROOT)): digest(path) for path in files}}
    (BASE / 'content-validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['total', 'chapters', 'lines', 'protected_prior_files']}))


if __name__ == '__main__':
    validate()
