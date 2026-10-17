"""Validate the authored notes/site; never leave a persistent preview server."""
from pathlib import Path
import json,os,re,subprocess,tempfile

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SITE=ROOT/'study-guide'
NODE=Path(r'C:/Program Files/nodejs/node.exe')
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
content=json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
font=Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env=dict(os.environ)
if font.exists():env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES']=str(font)
build=subprocess.run([str(NODE),'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
(BASE/'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
build.check_returncode()
print(build.stdout,flush=True)
smoke=subprocess.run([str(NODE),str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site=json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
net=subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners=[line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped={str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'])}
if not all(stopped.values()):raise RuntimeError('Requested/test listener remains open')
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
diff.check_returncode()
chapter=ROOT/'Resume Skills Notes'/content['chapter']
sources=['cache.py','store.py','jobs.py','ingestion.py']
text=chapter.read_text(encoding='utf-8')
if not all((BASE/name).read_text(encoding='utf-8') in text for name in sources):raise RuntimeError('Embedded source changed')
whitespace=[p.name for p in [chapter,*BASE.glob('*.py'),*BASE.glob('*.md'),*BASE.glob('*.mjs')] if re.search(r'[\t ]+$',p.read_text(encoding='utf-8'),re.M)]
if whitespace:raise RuntimeError('Trailing whitespace '+str(whitespace))
core=[]
for name in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes'):
    files=list((ROOT/name).glob('*.md'))
    core.append({'subject':name,'files':len(files),'lines':sum(p.read_text(encoding='utf-8').count('\n') for p in files)})
summary={'module':15,'title':'Caching, Background Jobs and Data Ingestion','verified_date':'2026-10-14',
         'runtime':proof['runtime'],'sqlite_version':proof['sqlite_version'],'packages':proof['packages'],
         'checks':{'counts':proof['counts'],'total':proof['total'],'all_passed':all(c['passed'] for g in proof['groups'] for c in g['checks'])},
         'temporary_directory_removed':proof['temporary_directory_removed'],'content':content,
         'website':{'build_passed':True,'static_pages':91,'routes_checked':len(site['routes']),
                    'all_routes_200':all(r['status']==200 for r in site['routes']),'assertions':site['assertions'],
                    'search':site['search'],'temporary_server_closed':site['temporaryServerClosed'],
                    'cached_font_fixture_used':font.exists()},
         'ports_stopped':stopped,'git_diff_check_passed':True,'trailing_whitespace_files':whitespace,
         'core_handbooks':core,'next_module':'M16: Docker Fundamentals',
         'scope':proof['scope']+'; no HTTP/provider/cloud delivery, cross-process cache, OCR, hostile-parser sandbox, crash/power-loss or load test'}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':proof['total'],'routes':len(site['routes']),'ports_stopped':stopped,'next':summary['next_module']},indent=2))
