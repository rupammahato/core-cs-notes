"""Audit P4 numerical/browser evidence, citations, routes and prior-note preservation."""
import hashlib
import json
from pathlib import Path
import re
import runpy

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
p3=runpy.run_path(str(BASE.parent/'module-3-python-excel-analysis/validate_content.py'))
p0=p3['p0']
chapter_path=ROOT/'Product Analytics Notes/product-analytics-handbook-part-6-module-4-marketing-measurement-data-visualization.md'
chapter=chapter_path.read_text(encoding='utf-8')
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
output=json.loads((BASE/'measurement-output.json').read_text(encoding='utf-8'))
browser=json.loads((BASE/'browser-validation.json').read_text(encoding='utf-8'))
research=json.loads((BASE/'research.json').read_text(encoding='utf-8'))
assert proof['total']==79 and all(row['passed'] for row in proof['checks'])
assert proof['observations']==output and proof['database_closed']
assert not proof['external_services_called'] and not proof['persistent_listener_started']
assert browser['total']==36 and all(row['passed'] for row in browser['checks'])
assert browser['server_closed'] and browser['browser_closed'] and not browser['external_requests']
assert browser['d3']=='7.9.0' and browser['browser']=='155.0.8059.84'
assert proof['source_sha256']==hashlib.sha256((BASE/'case.json').read_bytes()).hexdigest()
for value in ['79 Python checks passed','36 browser checks passed','Python 3.13.15',
              'SQLite 3.50.4','Chrome 155.0.8059.84','D3 7.9.0','Playwright 1.62.1',
              '30-minute mock','No ad account','not a complete screen-reader',
              'hand-defined attribution', 'P5: Product and Analytics Resume Drills and Revision']:
    assert value in chapter,value
blocks=[json.loads(block) for block in re.findall(r'```json\n(.*?)\n```',chapter,re.S)]
assert len(blocks)==5
assert blocks[0]==output['platform_report']['blended_metrics']
assert blocks[1]==output['ledger']
assert blocks[2]==output['last_eligible_click_7d']['by_campaign_net_cents']
assert blocks[3]==output['click_7d_else_view_1d']['by_campaign_net_cents']
assert blocks[4]==output['independent_claim_overlap']
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',chapter,re.M)]==list(range(1,31))
practice=chapter.split('## 4.27 Practice tasks and answer checkpoints')[1].split('### Answer checkpoints')[0]
assert [int(n) for n in re.findall(r'^(\d+)\. ',practice,re.M)]==list(range(1,13))
assert len(re.findall(r'^- \[ \]',chapter,re.M))==14
assert not re.search(r'^- \[x\]',chapter,re.M)
assert len(re.findall(r'^```',chapter,re.M))%2==0
links=set(re.findall(r'\]\((/docs/[^)#]+)(?:#[^)]*)?\)',chapter))
assert links<=p0['routes'],links-p0['routes']
assert len(research['sources'])==14
for source in research['sources']:
    assert source['url'] in chapter
assert all(row['status']=='Available' for row in p0['syllabus'][:5])
assert p0['syllabus'][5]['status'] in ('Available','Planned')
snapshot=json.loads((BASE/'prior-notes-snapshot.json').read_text(encoding='utf-8'))
for part,module in [(2,'0-product-thinking-requirements-design'),(3,'1-pricing-unit-economics'),
                    (4,'2-product-analytics-experiments')]:
    key=f'Product Analytics Notes/product-analytics-handbook-part-{part}-module-{module}.md'
    assert hashlib.sha256((ROOT/key).read_bytes()).hexdigest()==snapshot[key],key
old='**Next planned: P4, Marketing Measurement and Data Visualization**\u2014campaign vocabulary, attribution, denominators, chart selection, D3 and treemaps. P4 has no live chapter link until authored.'
new='Continue with [P4: Marketing Measurement and Data Visualization](/docs/product-analytics/marketing-measurement-data-visualization)\u2014campaign vocabulary, attribution, denominators, chart selection, D3 and treemaps.'
assert new in p3['chapter']
p3key='Product Analytics Notes/product-analytics-handbook-part-5-module-3-python-excel-analysis.md'
assert hashlib.sha256((ROOT/p3key).read_bytes().replace(new.encode(),old.encode())).hexdigest()==snapshot[p3key]
generated=ROOT/'study-guide/content/docs/product-analytics/marketing/marketing-measurement-data-visualization.md'
assert generated.exists()
package=json.loads((BASE/'package.json').read_text(encoding='utf-8'))
lock=json.loads((BASE/'package-lock.json').read_text(encoding='utf-8'))
assert package['dependencies']['d3']==lock['packages']['node_modules/d3']['version']=='7.9.0'
assert package['devDependencies']['playwright']==lock['packages']['node_modules/playwright']['version']=='1.62.1'
assert '/node_modules/d3/dist/d3.min.js' in (BASE/'index.html').read_text(encoding='utf-8')
assert 'node_modules/' in (BASE/'.gitignore').read_text(encoding='utf-8')
summary={'verified_date':'2026-10-18','fresh_python_checks':79,'fresh_browser_checks':36,
         'questions':30,'practice_tasks':12,'mock_minutes':30,'unchecked_learning_items':14,
         'exact_output_blocks':len(blocks),'research_sources':14,'internal_links_resolve':len(links),
         'authored_track_files':len(p0['available'])+1,
         'remaining_sections':[row['label'] for row in p0['syllabus'] if row['status']=='Planned'],
         'original_handbooks_unchanged':len(p0['entries']),'P0_P1_P2_unchanged_this_section':True,
         'P3_only_continuation_changed':True,'historical_runtime_suites_rerun':False,
         'note_lines':p0['summary']['note_lines'],'chapter_sha256':hashlib.sha256(chapter_path.read_bytes()).hexdigest(),
         'example_source_sha256':{name:hashlib.sha256((BASE/name).read_bytes()).hexdigest()
                                 for name in ['case.json','measurement.py','verify.py','chart.js','index.html',
                                              'verify-browser.mjs','package.json','package-lock.json']},
         'scope':'P4 source/output/browser and prior-note audit; no vendor output parity, causal lift or personal practice verification.'}
(BASE/'content-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
