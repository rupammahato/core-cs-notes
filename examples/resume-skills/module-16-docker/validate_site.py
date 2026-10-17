"""Validate the authored Docker notes without starting the Docker engine."""
from pathlib import Path
import json,os,re,subprocess,tempfile

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SITE=ROOT/'study-guide'
NODE=Path(r'C:/Program Files/nodejs/node.exe')
proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
content=json.loads((BASE/'content-validation.json').read_text(encoding='utf-8'))
engine=json.loads((BASE/'engine-session-results.json').read_text(encoding='utf-8'))
font=Path(tempfile.gettempdir())/'placement-site-validation/font-responses.cjs'
env=dict(os.environ)
if font.exists():env['NEXT_FONT_GOOGLE_MOCKED_RESPONSES']=str(font)
build=subprocess.run([str(NODE),'node_modules/next/dist/bin/next','build','--webpack'],cwd=SITE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
(BASE/'site-build-output.txt').write_text(build.stdout+'\n'+build.stderr,encoding='utf-8')
build.check_returncode();print(build.stdout,flush=True)
completed=[int(total) for done,total in re.findall(r'\((\d+)/(\d+)\)',build.stdout) if done==total]
if not completed:raise RuntimeError('No completed static-page count recorded')
smoke=subprocess.run([str(NODE),str(BASE/'site-smoke.mjs'),str(SITE),str(BASE/'site-validation.json')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
(BASE/'site-verification-output.txt').write_text(smoke.stdout+'\n'+smoke.stderr,encoding='utf-8')
smoke.check_returncode()
site=json.loads((BASE/'site-validation.json').read_text(encoding='utf-8'))
net=subprocess.run(['netstat','-ano','-p','TCP'],capture_output=True,text=True,check=True)
listeners=[line.split()[1] for line in net.stdout.splitlines() if 'LISTENING' in line]
stopped={str(port):not any(local.endswith(':'+str(port)) for local in listeners) for port in (3000,site['port'])}
if not all(stopped.values()):raise RuntimeError('Requested/test listener remains open')
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);diff.check_returncode()
chapter=ROOT/'Resume Skills Notes'/content['chapter'];text=chapter.read_text(encoding='utf-8')
if not all((BASE/name).read_text(encoding='utf-8') in text for name in content['source_fidelity']):raise RuntimeError('Embedded source changed')
whitespace=[p.name for p in [chapter,*BASE.glob('*.py'),*BASE.glob('*.md'),*BASE.glob('*.mjs')] if re.search(r'[\t ]+$',p.read_text(encoding='utf-8'),re.M)]
if whitespace:raise RuntimeError('Trailing whitespace '+str(whitespace))
core=[]
for name in ('DSA Notes','OOP Notes','OS Notes','DBMS Notes','CN Notes'):
    files=list((ROOT/name).glob('*.md'))
    core.append({'subject':name,'files':len(files),'lines':sum(p.read_text(encoding='utf-8').count('\n') for p in files)})
summary={'module':16,'title':'Docker Fundamentals','verified_date':'2026-10-14',
         'runtime':proof['observations']['runtime'],'base_images':proof['observations']['base_images'],
         'container_python':proof['observations']['python_version'],'postgres_version':proof['observations']['postgres_version'],
         'checks':{'counts':proof['counts'],'total':proof['total'],'all_passed':all(c['passed'] for c in proof['checks'])},
         'cleanup':proof['cleanup'],'scratch_directory_removed':proof['scratch_directory_removed'],'engine_session':engine,'content':content,
         'website':{'build_passed':True,'static_pages':completed[-1],'routes_checked':len(site['routes']),
                    'all_routes_200':all(r['status']==200 for r in site['routes']),'assertions':site['assertions'],
                    'search':site['search'],'temporary_server_closed':site['temporaryServerClosed'],'cached_font_fixture_used':font.exists()},
         'ports_stopped':stopped,'git_diff_check_passed':True,'trailing_whitespace_files':whitespace,
         'core_handbooks':core,'next_module':'M17: Linux Deployment, Nginx and PM2','scope':proof['scope']}
(BASE/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':proof['total'],'routes':len(site['routes']),'static_pages':completed[-1],'ports_stopped':stopped,'engine_restored_stopped':engine['engine_restored_stopped'],'next':summary['next_module']},indent=2))
