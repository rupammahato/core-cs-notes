"""Audit published P0 material and preserve the earlier 121 handbook files."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
notes = ROOT / 'Product Analytics Notes'
chapter_path = notes / 'product-analytics-handbook-part-2-module-0-product-thinking-requirements-design.md'
roadmap_path = notes / 'product-analytics-handbook-part-1-master-roadmap.md'
chapter = chapter_path.read_text(encoding='utf-8')
roadmap = roadmap_path.read_text(encoding='utf-8')
proof = json.loads((BASE / 'verification-results.json').read_text())
output = json.loads((BASE / 'worksheet-output.json').read_text())
blocks = [json.loads(block) for block in re.findall(r'```json\n(.*?)\n```', chapter, re.S)]
assert len(blocks) == 3
assert blocks == [output['ranking'], output['traceability'], output['draft_change']]
assert proof['total'] == 53 and all(row['passed'] for row in proof['checks'])
assert proof['observations'] == output
assert '53 local checks passed' in chapter and proof['python'] in chapter
questions = re.findall(r'^### Q(\d+)\.', chapter, re.M)
assert list(map(int, questions)) == list(range(1, 31))
practice = chapter.split('## 0.19 Practice tasks and answer checkpoints')[1].split('### Answer checkpoints')[0]
assert [int(n) for n in re.findall(r'^(\d+)\. ', practice, re.M)] == list(range(1, 13))
assert len(re.findall(r'^- \[ \]', chapter, re.M)) == 14
assert not re.search(r'^- \[x\]', chapter, re.M)
assert '30-minute mock' in chapter
for text in (chapter, roadmap):
    assert len(re.findall(r'^```', text, re.M)) % 2 == 0
syllabus = json.loads((BASE.parent / 'roadmap/syllabus.json').read_text())
assert [row['label'] for row in syllabus] == [f'P{i}' for i in range(6)]
available = [row for row in syllabus if row['status'] == 'Available']
assert syllabus[0]['status'] == 'Available'
assert len(list(notes.glob('*.md'))) == len(available) + 1
assert all(row['status'] in ('Available', 'Planned') for row in syllabus)
assert not any('/docs/product-analytics/' + row['slug'] in chapter + roadmap
               for row in syllabus if row['status'] == 'Planned')
research = json.loads((BASE.parent / 'roadmap/research.json').read_text())
for source in research['sources']:
    assert source['url'] in chapter + roadmap
assert len(research['sources']) == 10

# Derive routes using the same filename transformations as the sync script.
routes = set()
for folder in (ROOT / 'study-guide/content/docs').iterdir():
    if folder.is_dir():
        for file in folder.rglob('*.md'):
            routes.add('/docs/' + folder.name + ('' if file.stem == 'index' else '/' + file.stem))
links = set(re.findall(r'\]\((/docs/[^)#]+)(?:#[^)]*)?\)', chapter + roadmap))
assert links <= routes, sorted(links - routes)
generated = ROOT / 'study-guide/content/docs/product-analytics'
assert (generated / 'index.md').exists()
assert (generated / 'product-foundations/product-thinking-requirements-design.md').exists()

# Compare committed blobs in one batch, preserving CRLF-sensitive evidence.
folders = ['DSA Notes', 'OOP Notes', 'OS Notes', 'DBMS Notes', 'CN Notes', 'Resume Skills Notes', 'System Design Notes']
entries = {}
tree = subprocess.check_output(['git', 'ls-tree', '-r', '-z', 'HEAD', '--', *folders], cwd=ROOT).decode()
for entry in tree.strip('\0').split('\0'):
    meta, path = entry.split('\t', 1)
    if path.endswith('.md'):
        entries[path] = meta.split()[2]
oids = list(dict.fromkeys(entries.values()))
raw = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=ROOT,
                              input=('\n'.join(oids) + '\n').encode())
blobs = {}; pos = 0
for oid in oids:
    end = raw.index(b'\n', pos)
    size = int(raw[pos:end].split()[2])
    blobs[oid] = raw[end + 1:end + 1 + size]
    pos = end + size + 2
for path, oid in entries.items():
    assert (ROOT / path).read_bytes() == blobs[oid], path
assert len(entries) == 121
summary = {'verified_date': '2026-10-18', 'runtime_checks': proof['total'],
           'questions': len(questions), 'practice_tasks': 12, 'mock_minutes': 30,
           'unchecked_learning_items': 14, 'exact_output_blocks': len(blocks),
           'research_sources': len(research['sources']), 'internal_links_resolve': len(links),
           'authored_track_files': len(available) + 1, 'remaining_sections': [row['label'] for row in syllabus if row['status'] == 'Planned'],
           'existing_handbooks_unchanged': len(entries),
           'note_lines': sum(len(p.read_text(encoding='utf-8').splitlines()) for p in notes.glob('*.md')),
           'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in notes.glob('*.md')},
           'manual_work_completed': False,
           'scope': 'Content, recorded output fidelity, route coverage and unchanged-source audit; not a fresh run of historical runtime suites.'}
(BASE / 'content-validation.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
