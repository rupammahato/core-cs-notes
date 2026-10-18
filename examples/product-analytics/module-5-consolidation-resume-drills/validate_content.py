"""Final product-track content, output, links and source-preservation audit."""
import hashlib
import json
from pathlib import Path
import re
import runpy

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
p4=runpy.run_path(str(BASE.parent/'module-4-marketing-measurement-data-visualization/validate_content.py'))
p0=p4['p0']
chapter_path=ROOT/'Product Analytics Notes/product-analytics-handbook-part-7-module-5-consolidation-resume-drills.md'
chapter=chapter_path.read_text(encoding='utf-8')
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
output=json.loads((BASE/'drill-output.json').read_text(encoding='utf-8'))
research=json.loads((BASE/'research.json').read_text(encoding='utf-8'))
assert proof['total']==27 and proof['isolated_output_checks']==12 and proof['source_and_coverage_checks']==15
assert all(row['passed'] for row in proof['checks']) and proof['observations']==output
assert proof['all_workers_exited'] and len(proof['workers'])==12
assert all(row['exit_code']==0 for row in proof['workers'])
assert not proof['external_services_called'] and not proof['persistent_listener_started']
assert proof['input_and_dependency_sources_unchanged'] and not proof['historical_suites_rerun']
for value in ['27 local checks passed','12 isolated output drills','15 source/coverage audits',
              'Python 3.13.15','SQLite 3.50.4','not the truth of original business-impact claims',
              'fully authored','manual','45 minutes']:
    assert value in chapter,value
blocks=[json.loads(block) for block in re.findall(r'```json\n(.*?)\n```',chapter,re.S)]
assert len(blocks)==12 and blocks==list(output.values())
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',chapter,re.M)]==list(range(1,61))
assert [int(n) for n in re.findall(r'^### D(\d+)\.',chapter,re.M)]==list(range(1,13))
assert [int(n) for n in re.findall(r'^### S(\d+)\.',chapter,re.M)]==list(range(1,8))
for prefix,count in [('C',30),('B',16),('T',24)]:
    assert [int(n) for n in re.findall(r'^\| '+prefix+r'(\d+) \|',chapter,re.M)]==list(range(1,count+1))
practice=chapter.split('## 5.13 Practice tasks and answer checkpoints')[1].split('### Answer checkpoints')[0]
assert [int(n) for n in re.findall(r'^(\d+)\. ',practice,re.M)]==list(range(1,13))
assert len(re.findall(r'^- \[ \]',chapter,re.M))==18
assert not re.search(r'^- \[x\]',chapter,re.M)
for part in ['5.11 Mock A','5.12 Mock B']:
    mock=chapter.split('## '+part)[1].split('\n## ')[0]
    intervals=[(int(a),int(b)) for a,b in re.findall(r'^\| (\d+)\u2013(\d+) \|',mock,re.M)]
    assert intervals[0][0]==0 and intervals[-1][1]==45
    assert all(a<b for a,b in intervals) and all(left[1]==right[0] for left,right in zip(intervals,intervals[1:]))
assert len(research['sources'])==2 and research['remaining_authoring_sections']==[]
for row in research['sources']:
    assert row['url'] in chapter
for name in research['internal_sources']:
    assert (ROOT/name).exists(),name
notes=ROOT/'Product Analytics Notes'
texts={p:p.read_text(encoding='utf-8') for p in notes.glob('*.md')}
assert len(texts)==7 and len(p0['available'])==6
assert all(row['status']=='Available' for row in p0['syllabus'])
links=set()
for path,text in texts.items():
    assert len(re.findall(r'^```',text,re.M))%2==0,path
    assert '**Next planned:' not in text,path
    links.update(re.findall(r'\]\((/docs/[^)#]+)(?:#[^)]*)?\)',text))
assert links<=p0['routes'],links-p0['routes']
questions=sum(len(re.findall(r'^### Q\d+\.',text,re.M)) for text in texts.values())
assert questions==210
learning_items=sum(len(re.findall(r'^- \[ \]',text,re.M)) for text in texts.values())
assert learning_items==88
for path,text in texts.items():
    if 'master-roadmap' in path.name:continue
    tasks=re.split(r'## \d+\.\d+ Practice tasks and answer checkpoints',text)[1].split('### Answer checkpoints')[0]
    assert [int(n) for n in re.findall(r'^(\d+)\. ',tasks,re.M)]==list(range(1,13)),path
snapshot=json.loads((BASE/'prior-notes-snapshot.json').read_text(encoding='utf-8'))
unchanged=[]
for name,digest in snapshot.items():
    if 'master-roadmap' in name or 'part-6-' in name:continue
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    unchanged.append(name)
assert len(unchanged)==4
old='**Next planned: P5, Product and Analytics Resume Drills and Revision**\u2014decision stories, evidence, confusable pairs, stakeholder situations and final mocks. P5 has no live chapter link until authored.'
new='Continue with [P5: Product and Analytics Resume Drills and Revision](/docs/product-analytics/consolidation-resume-drills)\u2014decision stories, evidence, confusable pairs, stakeholder situations and final mocks.'
key='Product Analytics Notes/product-analytics-handbook-part-6-module-4-marketing-measurement-data-visualization.md'
raw=(ROOT/key).read_bytes()
assert new.encode() in raw
assert hashlib.sha256(raw.replace(new.encode(),old.encode())).hexdigest()==snapshot[key]
generated=ROOT/'study-guide/content/docs/product-analytics/revision/consolidation-resume-drills.md'
assert generated.exists()
roadmap=(notes/'product-analytics-handbook-part-1-master-roadmap.md').read_text(encoding='utf-8')
assert '| Planned |' not in roadmap and '- [ ]' not in roadmap
assert 'No planned authoring sections remain' in roadmap
readme=(ROOT/'README.md').read_text(encoding='utf-8')
assert '210 Q&As' in readme and '72 practice tasks' in readme and '488 recorded checks' in readme
assert f"| {p0['summary']['note_lines']:,} |" in readme
recorded_python_checks=sum(json.loads((BASE.parent/folder/'verification-results.json').read_text(encoding='utf-8'))['total']
                           for folder in ['module-0-product-thinking','module-1-pricing-unit-economics',
                                          'module-2-analytics-experiments','module-3-python-excel-analysis',
                                          'module-4-marketing-measurement-data-visualization'])
recorded_excel_checks=json.loads((BASE.parent/'module-3-python-excel-analysis/native-excel-validation.json').read_text(encoding='utf-8-sig'))['total']
recorded_browser_checks=json.loads((BASE.parent/'module-4-marketing-measurement-data-visualization/browser-validation.json').read_text(encoding='utf-8'))['total']
recorded_total=recorded_python_checks+recorded_excel_checks+recorded_browser_checks+proof['total']
assert recorded_total==488
summary={'verified_date':'2026-10-18','fresh_checks':27,'isolated_output_checks':12,'source_and_coverage_checks':15,
         'questions':60,'practice_tasks':12,'story_cards':7,'confusable_pairs':30,'diagnosis_cards':16,
         'self_test_questions':24,'final_mocks':2,'final_mock_minutes_each':45,'unchecked_learning_items':18,
         'exact_output_blocks':12,'research_sources':2,'all_product_internal_links_resolve':len(links),
         'authored_track_files':7,'available_sections':6,'remaining_sections':[],
         'track_questions':questions,'track_practice_tasks':72,'track_unchecked_learning_items':learning_items,
         'recorded_track_checks':recorded_total,'check_breakdown':{'P0_P4_python_sqlite':recorded_python_checks,
         'P3_native_excel':recorded_excel_checks,'P4_browser':recorded_browser_checks,'P5_isolated_outputs':12,'P5_source_audits':15},'original_handbooks_unchanged':len(p0['entries']),
         'P0_P1_P2_P3_unchanged_this_section':True,'P4_only_continuation_changed':True,
         'historical_runtime_suites_rerun':False,'note_lines':p0['summary']['note_lines'],
         'chapter_sha256':hashlib.sha256(chapter_path.read_bytes()).hexdigest(),
         'example_source_sha256':{p.relative_to(BASE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [BASE/'verify.py',BASE/'coverage.json',BASE/'story-map.json',
                                           BASE/'expected-output.json',*sorted((BASE/'drills').glob('*.py'))]},
         'scope':'Completed authoring and final content/source audit; learner practice and original business-impact corroboration remain separate.'}
(BASE/'content-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
