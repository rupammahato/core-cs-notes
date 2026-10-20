"""Insert verified worked examples while preserving authored chapter prose."""
import hashlib
import json
from pathlib import Path
from compute import BASE, displayed

ROOT = BASE.parents[1]
NOTES = ROOT/'Probability Statistics Notes'
START = '<!-- BEGIN WORKED EXAMPLES -->'
END = '<!-- END WORKED EXAMPLES -->'


def case_markdown(case, result):
    key = case['id']
    return '\n\n'.join([
        f"### {key}. {case['title']}", case['question'], f"**Hint:** {case['hint']}",
        f"**Worked reasoning:** {case['derivation']}",
        f'Run `python examples/probability-statistics/compute.py {key}` from the repository root.',
        '**Verified output** (six-decimal presentation; full precision in results.json):',
        '```json\n'+json.dumps(displayed(result), indent=2)+'\n```',
        f"**Common trap:** {case['trap']}", f"**Interview follow-up:** {case['follow_up']}",
    ])


def build():
    proof = json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
    assert proof['total'] == 71 and all(row['passed'] for row in proof['checks'])
    assert all(hashlib.sha256((BASE/name).read_bytes()).hexdigest() == digest for name, digest in proof['source_sha256'].items())
    cases = json.loads((BASE/'cases.json').read_text(encoding='utf-8'))
    results = json.loads((BASE/'results.json').read_text(encoding='utf-8'))
    assert [c['id'] for c in cases] == [f'E{n:02}' for n in range(1, 36)]
    for part in range(2, 9):
        selected = [case for case in cases if case['chapter'] == part]
        assert len(selected) == 5
        path, = NOTES.glob(f'*-part-{part}-*.md')
        source = path.read_text(encoding='utf-8')
        assert source.count(START) == source.count(END) == 1
        before, rest = source.split(START)
        _, after = rest.split(END)
        section = 6 if part <= 5 else 7 if part == 6 else 8
        content = f'## {section}. Worked examples\n\n'+'\n\n'.join(case_markdown(case, results[case['id']]) for case in selected)
        path.write_text(before+START+'\n\n'+content+'\n\n'+END+after, encoding='utf-8')
    print('Inserted all 35 verified worked examples into seven authored modules.')


if __name__ == '__main__':
    build()
