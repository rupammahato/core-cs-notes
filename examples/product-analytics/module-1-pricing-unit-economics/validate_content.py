"""Verify the P1 teaching material, exact computed outputs and continuation updates."""
import hashlib
import json
from pathlib import Path
import re
import runpy

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
# Reuse the P0 output, route, structure and original-handbook preservation audit.
prior = runpy.run_path(str(BASE.parent / 'module-0-product-thinking/validate_content.py'))
chapter_path = ROOT / 'Product Analytics Notes/product-analytics-handbook-part-3-module-1-pricing-unit-economics.md'
chapter = chapter_path.read_text(encoding='utf-8')
proof = json.loads((BASE / 'verification-results.json').read_text())
output = json.loads((BASE / 'economics-output.json').read_text())
assert proof['total'] == 88 and all(row['passed'] for row in proof['checks'])
assert proof['observations'] == output
assert '88 local checks passed' in chapter and proof['python'] in chapter
blocks = [json.loads(block) for block in re.findall(r'```json\n(.*?)\n```', chapter, re.S)]
assert len(blocks) == 4
for block, key in zip(blocks[:2], ['before_reconciliation', 'after_reconciliation']):
    assert block == {field: output[key][field] for field in block}
assert blocks[2] == output['cohort_margin']
assert blocks[3] == output['target_price']
assert [int(n) for n in re.findall(r'^### Q(\d+)\.', chapter, re.M)] == list(range(1,31))
practice = chapter.split('## 1.19 Practice tasks and answer checkpoints')[1].split('### Answer checkpoints')[0]
assert [int(n) for n in re.findall(r'^(\d+)\. ', practice, re.M)] == list(range(1,13))
assert len(re.findall(r'^- \[ \]', chapter, re.M)) == 14
assert not re.search(r'^- \[x\]', chapter, re.M)
assert '30-minute mock' in chapter
assert len(re.findall(r'^```', chapter, re.M)) % 2 == 0
links = set(re.findall(r'\]\((/docs/[^)#]+)(?:#[^)]*)?\)', chapter))
assert links <= prior['routes'], links - prior['routes']
research = json.loads((BASE / 'research.json').read_text())
assert len(research['sources']) == 8
for row in research['sources']:
    assert row['url'] in chapter
assert not proof['external_services_called'] and not proof['persistent_listener_started']
syllabus = prior['syllabus']
assert syllabus[1]['status'] == 'Available'
assert all(row['status'] in ('Available', 'Planned') for row in syllabus)
assert not any('/docs/product-analytics/' + row['slug'] in chapter + prior['chapter'] + prior['roadmap']
               for row in syllabus if row['status'] == 'Planned')
old = '**Next planned: P1, Pricing and Unit Economics**\u2014value, credits, usage, provider cost, failed/retried work and the Zyke case. P1 is not yet authored, so it has no live chapter link.'
new = 'Continue with [P1: Pricing and Unit Economics](/docs/product-analytics/pricing-unit-economics)\u2014value, credits, usage, provider cost, failed/retried work and the Zyke case.'
snapshot = json.loads((BASE / 'prior-notes-snapshot.json').read_text())
prior_key = 'Product Analytics Notes/product-analytics-handbook-part-2-module-0-product-thinking-requirements-design.md'
assert new in prior['chapter']
assert hashlib.sha256(prior['chapter'].replace(new, old).encode()).hexdigest() == snapshot[prior_key]
generated = ROOT / 'study-guide/content/docs/product-analytics/economics/pricing-unit-economics.md'
assert generated.exists()
summary = {'verified_date':'2026-10-18','runtime_checks':proof['total'],'questions':30,'practice_tasks':12,
           'mock_minutes':30,'unchecked_learning_items':14,'exact_output_blocks':len(blocks),
           'research_sources':len(research['sources']),'internal_links_resolve':len(links),
           'authored_track_files':len(prior['available'])+1,'remaining_sections':[row['label'] for row in syllabus if row['status']=='Planned'],
           'existing_handbooks_unchanged':len(prior['entries']),
           'P0_only_continuation_changed':True,'historical_runtime_suites_rerun':False,
           'note_lines':prior['summary']['note_lines'],
           'chapter_sha256':hashlib.sha256(chapter_path.read_bytes()).hexdigest(),
           'scope':'P1 output/content/source audit and current P0 teaching-content preservation; not a production billing or accounting validation.'}
(BASE / 'content-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
