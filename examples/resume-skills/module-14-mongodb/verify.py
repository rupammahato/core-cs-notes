from pathlib import Path
import importlib.metadata as metadata
import json,os,subprocess,sys
from pymongo import MongoClient
from cluster import temporary_cluster
BASE=Path(__file__).resolve().parent
if sys.flags.optimize: raise SystemExit('Run without -O')
versions={name:metadata.version(name) for name in ('pymongo','dnspython')}
if versions['pymongo']!='4.10.1': raise SystemExit('Install requirements.lock.txt')
groups=sys.argv[1:] or ['core','queries','indexes','atomic','transactions','pool']
if any(g not in ('core','queries','indexes','atomic','transactions','pool') for g in groups): raise SystemExit('Unknown group')
rows=[]; outputs=[]; cluster_evidence={}
try:
    with temporary_cluster() as (uri,cluster_evidence):
        for group in groups:
            env=dict(os.environ,M14_PORT=str(cluster_evidence['port']),M14_DATABASE='m14_'+group,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
            result=subprocess.run([sys.executable,'-X','utf8',str(BASE/('verify_'+group+'.py'))],cwd=BASE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)
            if result.returncode or result.stderr: raise AssertionError({'group':group,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
            data=json.loads((BASE/(group+'-results.json')).read_text(encoding='utf-8'))
            if not all(r['passed'] for r in data['checks']): raise AssertionError(data)
            rows.append(data); outputs.append(result.stdout.replace('\r\n','\n'))
finally:
    log=cluster_evidence.pop('server_log','')
    (BASE/'mongodb-server-output.txt').write_text(log,encoding='utf-8')
    (BASE/'cluster-results.json').write_text(json.dumps(cluster_evidence,indent=2)+'\n',encoding='utf-8')
counts={g['group']:g['total'] for g in rows}
evidence={'runtime':sys.version,'packages':versions,'server_version':cluster_evidence['server_version'],
          'cluster':cluster_evidence,'counts':counts,'total':sum(counts.values()),'groups':rows}
(BASE/'verification-results.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
text='\n'.join(outputs)+'\nPASS total: '+str(evidence['total'])+'\n'
(BASE/'verification-output.txt').write_text(text,encoding='utf-8')
print(text,end='')
