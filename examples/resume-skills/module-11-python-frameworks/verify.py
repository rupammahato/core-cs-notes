from pathlib import Path
import importlib.metadata as metadata
import json
import os
import subprocess
import sys

BASE = Path(__file__).resolve().parent
if sys.flags.optimize:
    raise SystemExit('Run without -O for verification.')
packages = ['Flask','Werkzeug','fastapi','starlette','pydantic','pydantic-core',
            'uvicorn','httpx','anyio','asgiref']
versions = {name: metadata.version(name) for name in packages}
expected = {'Flask':'3.0.3','fastapi':'0.142.2','pydantic':'2.13.5',
            'starlette':'1.7.0','uvicorn':'0.54.0','httpx':'0.28.1'}
if any(versions[name] != value for name, value in expected.items()):
    raise SystemExit('Install requirements.lock.txt for the recorded verification stack: ' + repr(versions))
rows, output, warnings = [], [], []
env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
for group in ('protocols','validation','http','runtime'):
    result = subprocess.run([sys.executable,'-X','utf8',str(BASE / ('verify_' + group + '.py'))],
                            cwd=BASE, env=env, text=True, encoding='utf-8',
                            capture_output=True, timeout=90)
    if result.returncode:
        raise AssertionError({'group':group,'stdout':result.stdout,'stderr':result.stderr})
    if result.stderr:
        # Pinned Starlette still supports this deprecated httpx test-client adapter.
        lines = result.stderr.strip().splitlines()
        expected_warning = (group == 'runtime' and len(lines) == 2
          and 'StarletteDeprecationWarning: Using '+chr(96)+'httpx'+chr(96) in lines[0]
          and 'from starlette.testclient import TestClient as TestClient' in lines[1])
        if not expected_warning:
            raise AssertionError({'unexpected_stderr':result.stderr})
        warnings.append({'group':group,'stderr':result.stderr})
    data = json.loads((BASE / (group + '-results.json')).read_text(encoding='utf-8'))
    if not all(row['passed'] for row in data['checks']):
        raise AssertionError(data)
    rows.append(data)
    output.append(result.stdout.replace('\r\n','\n'))
counts = {row['group']:row['total'] for row in rows}
evidence = {'runtime':sys.version,'packages':versions,'counts':counts,
            'total':sum(counts.values()),'groups':rows,'expected_warnings':warnings}
(BASE / 'verification-results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
text = '\n'.join(output) + '\nPASS total: ' + str(evidence['total']) + '\n'
(BASE / 'verification-output.txt').write_text(text,encoding='utf-8')
(BASE / 'expected-warning-output.txt').write_text('\n'.join(w['stderr'] for w in warnings),encoding='utf-8')
print(text,end='')
