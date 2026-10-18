"""Check P3 output fidelity, evidence boundaries, routes and prior-note preservation."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import zipfile
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
p2 = runpy.run_path(str(BASE.parent/'module-2-analytics-experiments/validate_content.py'))
p0 = p2['p0']
chapter_path = ROOT/'Product Analytics Notes/product-analytics-handbook-part-5-module-3-python-excel-analysis.md'
chapter = chapter_path.read_text(encoding='utf-8')
proof = json.loads((BASE/'verification-results.json').read_text())
output = json.loads((BASE/'analysis-output.json').read_text())
native = json.loads((BASE/'native-excel-validation.json').read_text(encoding='utf-8-sig'))
artifact = json.loads((BASE/'workbook-validation.json').read_text())
research = json.loads((BASE/'research.json').read_text())
assert proof['total']==72 and all(row['passed'] for row in proof['checks'])
assert proof['observations']==output and not proof['external_services_called']
assert native['total']==38 and all(row['passed'] for row in native['checks'])
assert not native['formula_errors'] and native['original_file_unchanged']
assert native['disposable_copy_used'] and not native['native_pivottable_created']
assert artifact['artifact_formula_checks']=='passed' and len(artifact['mutations'])==6
assert artifact['restored_original_inputs']
assert artifact['baseline_summary']==[5,4,290,2,'n.a.',110,0,110,0.8]
for value in ['72 Python checks passed','38 native Excel checks','30-minute mock',
              'Python 3.12.14','NumPy 2.3.5','pandas 3.0.1', 'build 20430',
              'No native PivotTable is included', 'SUMIFS', 'raw: ']:
    assert value.lower() in chapter.lower(),value
blocks=[json.loads(block) for block in re.findall(r'```json\n(.*?)\n```',chapter,re.S)]
assert len(blocks)==4
assert blocks[0]==output['numpy']
assert blocks[1]==output['analysis']['index_alignment']
assert blocks[2]==output['analysis']['pivot_counts']
assert blocks[3]=={key:output['analysis'][key] for key in blocks[3]}
assert [int(n) for n in re.findall(r'^### Q(\d+)\.',chapter,re.M)]==list(range(1,31))
practice=chapter.split('## 3.26 Practice tasks and answer checkpoints')[1].split('### Answer checkpoints')[0]
assert [int(n) for n in re.findall(r'^(\d+)\. ',practice,re.M)]==list(range(1,13))
assert len(re.findall(r'^- \[ \]',chapter,re.M))==14
assert not re.search(r'^- \[x\]',chapter,re.M)
assert len(re.findall(r'^```',chapter,re.M))%2==0
links=set(re.findall(r'\]\((/docs/[^)#]+)(?:#[^)]*)?\)',chapter))
assert links<=p0['routes'],links-p0['routes']
assert len(research['sources'])==13
for source in research['sources']:
    assert source['url'] in chapter
assert all(row['status']=='Available' for row in p0['syllabus'][:4])
snapshot=json.loads((BASE/'prior-notes-snapshot.json').read_text())
for part,module in [(2,'0-product-thinking-requirements-design'),(3,'1-pricing-unit-economics')]:
    key=f'Product Analytics Notes/product-analytics-handbook-part-{part}-module-{module}.md'
    assert hashlib.sha256((ROOT/key).read_bytes()).hexdigest()==snapshot[key],key
old='**Next planned: P3, Python and Excel for Analysis**\u2014dataframes, joins, missing values, dates, formulas, lookups, pivots and reconciliation. P3 has no live chapter link until authored.'
new='Continue with [P3: Python and Excel for Analysis](/docs/product-analytics/python-excel-analysis)\u2014dataframes, joins, missing values, dates, formulas, lookups, pivots and reconciliation.'
assert new in p2['chapter']
assert hashlib.sha256(p2['chapter'].replace(new,old).encode()).hexdigest()==snapshot['Product Analytics Notes/product-analytics-handbook-part-4-module-2-product-analytics-experiments.md']
generated=ROOT/'study-guide/content/docs/product-analytics/analysis/python-excel-analysis.md'
assert generated.exists()
workbook=BASE/artifact['workbook']
assert workbook.exists()
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(workbook) as z:
    assert not any('pivotTable' in name for name in z.namelist())
    cells={cell.attrib['r']:cell for cell in ET.fromstring(z.read('xl/worksheets/sheet2.xml')).findall('.//s:c',ns)}
    assert cells['A6'].attrib['t']=='str' and cells['A6'].find('s:v',ns).text=='0001'
    assert cells['C6'].attrib['t']=='str' and cells['C6'].find('s:v',ns).text=='raw: 2026-10-01T00:30:00+05:30'
    assert cells['D6'].attrib['t']=='d'
    assert len([name for name in z.namelist() if re.match(r'xl/tables/table\d+\.xml$',name)])==3
summary={'verified_date':'2026-10-18','fresh_python_checks':72,'fresh_native_excel_checks':38,
         'artifact_mutation_scenarios':6,'native_pivottable_created':False,'questions':30,
         'practice_tasks':12,'mock_minutes':30,'unchecked_learning_items':14,'exact_output_blocks':len(blocks),
         'research_sources':13,'internal_links_resolve':len(links),'authored_track_files':len(p0['available'])+1,
         'remaining_sections':[row['label'] for row in p0['syllabus'] if row['status']=='Planned'],
         'original_handbooks_unchanged':len(p0['entries']),'P0_P1_unchanged_this_section':True,
         'P2_only_continuation_changed':True,'historical_runtime_suites_rerun':False,
         'note_lines':p0['summary']['note_lines'],'chapter_sha256':hashlib.sha256(chapter_path.read_bytes()).hexdigest(),
         'workbook_sha256':hashlib.sha256(workbook.read_bytes()).hexdigest(),
         'example_source_sha256':{name:hashlib.sha256((BASE/name).read_bytes()).hexdigest()
                                 for name in ['analysis.py','verify.py','jobs.csv','attempts.csv','workspaces.csv',
                                              'requirements.txt','build-workbook.mjs','verify-excel.ps1']},
         'scope':'P3 outputs, native formulas, structure, sources and preservation audit; manual PivotTable and personal practice remain uncompleted.'}
(BASE/'content-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
