from pathlib import Path
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
import psycopg
from psycopg import sql
from cluster import temporary_cluster

BASE=Path(__file__).resolve().parent
if sys.flags.optimize: raise SystemExit('Run without -O for verification.')
versions={name:metadata.version(name) for name in ('psycopg','psycopg-binary','psycopg-pool','typing_extensions','tzdata')}
if versions['psycopg']!='3.3.4' or versions['psycopg-pool']!='3.3.1':
    raise SystemExit('Install the recorded requirements.lock.txt versions first.')
groups=sys.argv[1:] or ['core','concurrency','pool','plans','service']
if any(group not in ('core','concurrency','pool','plans','service') for group in groups):
    raise SystemExit('Unknown verification group')
rows=[]
outputs=[]
cluster_evidence={}
try:
    with temporary_cluster() as (params,cluster_evidence):
        with psycopg.connect(**params,autocommit=True) as admin:
            for group in groups:
                name='m13_'+group
                admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
                env=dict(os.environ,M13_HOST='127.0.0.1',M13_PORT=str(params['port']),
                         M13_DATABASE=name,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
                result=subprocess.run([sys.executable,'-X','utf8',str(BASE/('verify_'+group+'.py'))],
                                      cwd=BASE,env=env,text=True,encoding='utf-8',capture_output=True,timeout=90)
                if result.returncode or result.stderr:
                    raise AssertionError({'group':group,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
                data=json.loads((BASE/(group+'-results.json')).read_text(encoding='utf-8'))
                if not all(row['passed'] for row in data['checks']): raise AssertionError(data)
                rows.append(data)
                outputs.append(result.stdout.replace('\r\n','\n'))
finally:
    (BASE/'cluster-results.json').write_text(json.dumps(cluster_evidence,indent=2)+'\n',encoding='utf-8')
    (BASE/'postgres-server-output.txt').write_text(cluster_evidence.get('server_log',''),encoding='utf-8')
counts={g['group']:g['total'] for g in rows}
evidence={'runtime':sys.version,'libpq_version':psycopg.pq.version(),'packages':versions,
          'server_version':cluster_evidence['server_version'],'cluster':cluster_evidence,
          'counts':counts,'total':sum(counts.values()),'groups':rows}
(BASE/'verification-results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
text='\n'.join(outputs)+'\nPASS total: '+str(evidence['total'])+'\n'
(BASE/'verification-output.txt').write_text(text,encoding='utf-8')
print(text,end='')
