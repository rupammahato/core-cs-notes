"""Replace only generated source/trace blocks in the authored Markdown chapters."""
import hashlib
import json
from fixtures import BASE, CASES, MODES

ROOT = BASE.parents[1]
NOTES = ROOT / 'Machine Coding Notes'


def replace(path, marker, body):
    start, end = f'<!-- BEGIN {marker} -->', f'<!-- END {marker} -->'
    text = path.read_text(encoding='utf-8')
    assert text.count(start) == text.count(end) == 1
    before, rest = text.split(start)
    _, after = rest.split(end)
    path.write_text(before + start + '\n\n' + body + '\n\n' + end + after, encoding='utf-8')


def source_section(mode):
    source = (BASE / 'machines.hpp').read_text(encoding='utf-8')
    return source.split(f'// BEGIN {mode}\n')[1].split(f'// END {mode}')[0].rstrip()


def trace_markdown(item, output):
    lines = []
    for command, response in zip(item['commands'], output):
        lines.extend([command, json.dumps(response, separators=(',', ':'))])
    return '\n\n'.join([
        f"### {item['id']}. {item['title']}",
        '**Worked explanation:** ' + item['reasoning'],
        f"Run `python examples/machine-coding/verify.py --trace {item['id']}` after compiling with the verifier.",
        '**Verified transcript** (command, then JSON response):',
        '```text\n' + '\n'.join(lines) + '\n```',
        '**Common trap:** ' + item['trap'],
        '**Interview follow-up:** ' + item['follow_up'],
    ])


def build():
    proof = json.loads((BASE / 'verification-results.json').read_text(encoding='utf-8'))
    assert proof['worked_traces'] == 32 and all(check['passed'] for check in proof['checks'])
    for name, expected in proof['source_sha256'].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == expected, name
    outputs = json.loads((BASE / 'observations.json').read_text(encoding='utf-8'))
    for part, mode in enumerate(MODES, 3):
        path, = NOTES.glob(f'*-part-{part}-*.md')
        selected = [item for item in CASES if item['mode'] == mode]
        assert len(selected) == 4
        replace(path, 'MODEL', '```cpp\n' + source_section(mode) + '\n```')
        replace(path, 'TRACES', '\n\n'.join(trace_markdown(item, outputs[item['id']]) for item in selected))
    path, = NOTES.glob('*-part-2-*.md')
    replace(path, 'COMMON', '```cpp\n' + (BASE / 'common.hpp').read_text(encoding='utf-8').rstrip() + '\n```')
    print('Inserted eight exact compiled classes, the shared header and 32 recorded traces.')


if __name__ == '__main__':
    build()
