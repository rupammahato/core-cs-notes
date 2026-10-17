from pathlib import Path
import importlib.metadata as metadata
import json,os,subprocess,sys,tempfile,sqlite3

BASE=Path(__file__).resolve().parent
if sys.flags.optimize:raise SystemExit('Run without -O')
groups=sys.argv[1:] or ['cache','jobs','formats','ingestion']
if any(g not in ('cache','jobs','formats','ingestion') for g in groups):raise SystemExit('Unknown group')
rows=[];outputs=[]
with tempfile.TemporaryDirectory(prefix='placement-m15-') as temporary:
    target=Path(temporary).resolve()
    if target.parent!=Path(tempfile.gettempdir()).resolve() or not target.name.startswith('placement-m15-'):
        raise RuntimeError('Unexpected temporary target')
    for group in groups:
        env=dict(os.environ,M15_DATABASE=str(target/(group+'.sqlite3')),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-X','utf8',str(BASE/('verify_'+group+'.py'))],cwd=BASE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)
        if result.returncode or result.stderr:raise AssertionError({'group':group,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        data=json.loads((BASE/(group+'-results.json')).read_text(encoding='utf-8'))
        if not all(r['passed'] for r in data['checks']):raise AssertionError(data)
        rows.append(data);outputs.append(result.stdout.replace('\r\n','\n'))
counts={g['group']:g['total'] for g in rows}
evidence={'runtime':sys.version,'sqlite_version':sqlite3.sqlite_version,
          'packages':{name:metadata.version(name) for name in ('openpyxl','et-xmlfile','defusedxml','pypdf')},
          'counts':counts,'total':sum(counts.values()),'groups':rows,
          'temporary_directory_removed':not target.exists(),'persistent_listener_started':False,
          'scope':'Local cache algorithm, SQLite job/import engine, real parser libraries; no Redis or Cloud Tasks service'}
(BASE/'verification-results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
text='\n'.join(outputs)+'\nPASS total: '+str(evidence['total'])+'\n'
(BASE/'verification-output.txt').write_text(text,encoding='utf-8');print(text,end='')
