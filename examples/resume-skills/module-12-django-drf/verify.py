from pathlib import Path
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE=Path(__file__).resolve().parent
if sys.flags.optimize: raise SystemExit('Run without -O for verification.')
versions={name:metadata.version(name) for name in ('Django','djangorestframework','asgiref','sqlparse','tzdata')}
if versions['Django']!='5.1.3' or versions['djangorestframework']!='3.15.2':
    raise SystemExit('Install the recorded requirements.lock.txt versions first.')
temp_base=Path(tempfile.gettempdir()).resolve()
temp_path=Path(tempfile.mkdtemp(prefix='placement-m12-',dir=temp_base)).resolve()
rows=[]
outputs=[]
try:
    for group in ('orm','transactions','framework','http'):
        env=dict(os.environ,M12_DATABASE=str(temp_path/(group+'.sqlite3')),
                 PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-X','utf8',str(BASE/('verify_'+group+'.py'))],
                              cwd=BASE,env=env,text=True,encoding='utf-8',capture_output=True,timeout=90)
        if result.returncode or result.stderr:
            raise AssertionError({'group':group,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        data=json.loads((BASE/(group+'-results.json')).read_text(encoding='utf-8'))
        if not all(row['passed'] for row in data['checks']): raise AssertionError(data)
        rows.append(data)
        outputs.append(result.stdout.replace('\r\n','\n'))
    env=dict(os.environ,M12_DATABASE=str(temp_path/'orm.sqlite3'),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    commands=[['check'],['makemigrations','work','--check','--dry-run'],['migrate','--check']]
    command_results=[]
    for args in commands:
        result=subprocess.run([sys.executable,str(BASE/'manage.py'),*args],cwd=BASE,env=env,
                              capture_output=True,text=True,encoding='utf-8',timeout=30)
        if result.returncode or result.stderr: raise AssertionError({'command':args,'stdout':result.stdout,'stderr':result.stderr})
        command_results.append({'command':args,'passed':True,'stdout':result.stdout})
finally:
    # Remove only the new directory directly below the resolved temp base.
    if temp_path.parent!=temp_base or not temp_path.name.startswith('placement-m12-'):
        raise RuntimeError('Refusing unexpected cleanup path')
    shutil.rmtree(temp_path)
counts={g['group']:g['total'] for g in rows}
import sqlite3
evidence={'runtime':sys.version,'sqlite':sqlite3.sqlite_version,'packages':versions,
          'counts':counts,'total':sum(counts.values()),'groups':rows,
          'management_commands':command_results,'temporary_databases_removed':not temp_path.exists()}
(BASE/'verification-results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
text='\n'.join(outputs)+'\nPASS total: '+str(evidence['total'])+'\n'
(BASE/'verification-output.txt').write_text(text,encoding='utf-8')
print(text,end='')
