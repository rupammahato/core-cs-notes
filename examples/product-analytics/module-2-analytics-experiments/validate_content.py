"""Audit P2 output fidelity, current route coverage and prior teaching-content preservation."""
import hashlib
import json
from pathlib import Path
import re
import runpy

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
prior = runpy.run_path(str(BASE.parent/'module-1-pricing-unit-economics/validate_content.py'))
p0 = prior['prior']
chapter_path = ROOT/'Product Analytics Notes/product-analytics-handbook-part-4-module-2-product-analytics-experiments.md'
chapter = chapter_path.read_text(encoding='utf-8')
proof = json.loads((BASE/'verification-results.json').read_text())
output = json.loads((BASE/'analytics-output.json').read_text())
case = json.loads((BASE/'case.json').read_text())
assert proof['total']==95 and all(row['passed'] for row in proof['checks'])
assert proof['observations']==output
assert '95 local checks passed' in chapter and proof['python'] in chapter and proof['sqlite'] in chapter
blocks=[json.loads(block) for block in re.findall(r'```json\n(.*?)\n```',chapter,re.S)]
assert len(blocks)==4
assert blocks[0]==case['events'][0]
assert blocks[1]==output['initial']['activation']
assert blocks[2]==output['revised']['retention']
assert blocks[3]=={key:output['experiment'][key] for key in blocks[3]}
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',chapter,re.M)]==list(range(1,31))
practice=chapter.split('## 2.23 Practice tasks and answer checkpoints')[1].split('### Answer checkpoints')[0]
assert [int(n) for n in re.findall(r'^(\d+)\. ',practice,re.M)]==list(range(1,13))
assert len(re.findall(r'^- \[ \]',chapter,re.M))==14
assert not re.search(r'^- \[x\]',chapter,re.M)
assert '30-minute mock' in chapter and len(re.findall(r'^```',chapter,re.M))%2==0
links=set(re.findall(r'\]\((/docs/[^)#]+)(?:#[^)]*)?\)',chapter))
assert links <= p0['routes'],links-p0['routes']
research=json.loads((BASE/'research.json').read_text())
assert len(research['sources'])==11
for row in research['sources']:
    assert row['url'] in chapter
assert not proof['external_services_called'] and not proof['persistent_listener_started'] and proof['database_closed']
assert all(row['status']=='Available' for row in p0['syllabus'][:3])
snapshot=json.loads((BASE/'prior-notes-snapshot.json').read_text())
p0_key='Product Analytics Notes/product-analytics-handbook-part-2-module-0-product-thinking-requirements-design.md'
p1_key='Product Analytics Notes/product-analytics-handbook-part-3-module-1-pricing-unit-economics.md'
assert hashlib.sha256((ROOT/p0_key).read_bytes()).hexdigest()==snapshot[p0_key]
old='**Next planned: P2, Product Analytics and Experiments**\u2014tracking plans, funnels, cohorts, retention, activation and causal limits. P2 has no live chapter link until authored.'
new='Continue with [P2: Product Analytics and Experiments](/docs/product-analytics/product-analytics-experiments)\u2014tracking plans, funnels, cohorts, retention, activation and causal limits.'
assert new in prior['chapter']
assert hashlib.sha256(prior['chapter'].replace(new,old).encode()).hexdigest()==snapshot[p1_key]
generated=ROOT/'study-guide/content/docs/product-analytics/analytics/product-analytics-experiments.md'
assert generated.exists()
summary={'verified_date':'2026-10-18','fresh_runtime_checks':proof['total'],'questions':30,'practice_tasks':12,
         'mock_minutes':30,'unchecked_learning_items':14,'exact_output_blocks':len(blocks),
         'research_sources':len(research['sources']),'internal_links_resolve':len(links),
         'authored_track_files':len(p0['available'])+1,'remaining_sections':[row['label'] for row in p0['syllabus'] if row['status']=='Planned'],
         'original_handbooks_unchanged':len(p0['entries']),'P0_unchanged_this_section':True,
         'P1_only_continuation_changed':True,'historical_runtime_suites_rerun':False,
         'note_lines':p0['summary']['note_lines'],'chapter_sha256':hashlib.sha256(chapter_path.read_bytes()).hexdigest(),
         'example_source_sha256':{name:hashlib.sha256((BASE/name).read_bytes()).hexdigest()
                                 for name in ['analytics.py','metrics.sql','tracking-plan.json','case.json','verify.py']},
         'scope':'P2 content/output/source and prior-teaching preservation audit, not vendor output parity or a real experiment validation.'}
(BASE/'content-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
