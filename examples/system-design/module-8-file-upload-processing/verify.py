"""Real local files, metadata transactions, guarded publication and loopback HTTP."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from threading import Barrier, Thread
import hashlib
import json
import platform
import socket
import sqlite3
import uuid
from estimates import calculate
from http_api import server
from uploads import Error, Uploads

BASE = Path(__file__).resolve().parent
checks, observations, stores, ports = [], {}, [], []
SECRET = b'published-local-upload-lesson-secret'


def check(group, name, condition):
    assert condition, (group,name)
    checks.append({'group':group,'name':name,'passed':True})


def denied(group, name, status, action):
    try:
        action()
    except Error as error:
        check(group,name,error.status == status)
    else:
        raise AssertionError(name)


def contract(raw=b'hello\n', **changes):
    value = {'name':'notes.txt','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mime':'text/plain'}
    value.update(changes)
    return value


temporary = TemporaryDirectory(prefix='placement-s3-verify-')
directory = Path(temporary.name).resolve()
assert directory.parent == Path(gettempdir()).resolve() and directory.name.startswith('placement-s3-verify-')
api, api_thread = None, None


def store(name='main'):
    value = Uploads(directory/(name+'.sqlite'),directory/(name+'-objects'),SECRET)
    stores.append(value)
    return value


def prepared(item, operation, raw=b'hello\n', now=0):
    value = item.create('tenant-a','alice',operation,contract(raw),now)
    item.upload(value['id'],value['capability'],raw,now)
    item.complete('tenant-a','alice',value['id'],now)
    return value


try:
    main = store()
    for name,data in [('path filename',contract(name='../notes.txt')),
        ('absolute filename',contract(name='C:\\notes.txt')),('unsupported extension',contract(name='notes.exe')),
        ('empty filename',contract(name='')),('wrong MIME',contract(mime='text/html')),
        ('empty size',contract(size=0)),('oversized size',contract(size=1025)),
        ('boolean size',contract(size=True)),('bad digest',contract(sha256='0'*63)),
        ('unknown JSON field',contract(extra='x'))]:
        denied('validation',name,400,lambda data=data:main.create('tenant-a','alice','invalid',data,0))
    denied('validation','empty operation key',400,lambda:main.create('tenant-a','alice','',contract(),0))
    denied('validation','negative time',400,lambda:main.create('tenant-a','alice','time',contract(),-1))
    check('validation','invalid contracts create no metadata',main.db.execute('SELECT count(*) FROM uploads').fetchone()[0] == 0)
    try:
        main.objects.path('raw','../escape')
    except ValueError:
        check('validation','object traversal rejected',True)
    else:
        raise AssertionError('object path escaped')
    outside = directory/'outside.txt'
    outside.write_bytes(b'owned sentinel outside object areas')
    try:
        main.objects.remove_owned('raw',outside)
    except ValueError:
        check('validation','cleanup outside owned object areas rejected',outside.exists())
    else:
        raise AssertionError('unsafe cleanup accepted')
    first = main.create('tenant-a','alice','create',contract(),0)
    retry = main.create('tenant-a','alice','create',contract(),500)
    check('intake','equivalent create replays original ID',first['id'] == retry['id'] and retry['replay'])
    check('intake','create retry does not extend capability expiry',retry['expires_ms'] == first['expires_ms'] == 10000)
    check('intake','create retry returns original capability',retry['capability'] == first['capability'])
    denied('intake','changed idempotent intent conflicts',409,lambda:main.create('tenant-a','alice','create',contract(name='new.txt'),0))
    other_owner = main.create('tenant-a','bob','create',contract(),0)
    check('intake','operation scope includes owner',other_owner['id'] != first['id'])
    other_tenant = main.create('tenant-b','alice','create',contract(),0)
    check('intake','operation scope includes tenant',other_tenant['id'] != first['id'])
    denied('intake','other owner cannot inspect metadata',404,lambda:main.owned('tenant-a','bob',first['id']))
    denied('intake','other tenant cannot complete file',404,lambda:main.complete('tenant-b','alice',first['id'],0))
    denied('intake','missing object prevents completion',409,lambda:main.complete('tenant-a','alice',first['id'],0))
    denied('intake','invalid capability cannot write',403,lambda:main.upload(first['id'],'forged',b'hello\n',0))
    denied('intake','non-ASCII capability rejected cleanly',403,lambda:main.upload(first['id'],'\u00e9',b'hello\n',0))
    denied('intake','capability bound to exact target',403,lambda:main.upload(other_owner['id'],first['capability'],b'hello\n',0))
    denied('intake','declared checksum enforced',422,lambda:main.upload(first['id'],first['capability'],b'other\n',0))
    denied('intake','declared size enforced',422,lambda:main.upload(first['id'],first['capability'],b'hello',0))
    check('intake','valid bytes installed immutably',main.upload(first['id'],first['capability'],b'hello\n',0))
    check('intake','same-byte PUT retry does not replace object',not main.upload(first['id'],first['capability'],b'hello\n',1))
    try:
        main.objects.put('raw',first['id'],b'changed')
    except ValueError:
        check('intake','immutable object rejects different bytes',main.objects.read('raw',first['id']) == b'hello\n')
    else:
        raise AssertionError('object overwritten')
    denied('intake','uploaded bytes remain unavailable before completion',409,lambda:main.download('tenant-a','alice',first['id']))
    main.close()
    main = store()
    check('intake','close/reopen retains original upload intent',main.create('tenant-a','alice','create',contract(),100)['id'] == first['id'])
    check('intake','completion enters quarantine',main.complete('tenant-a','alice',first['id'],100) == 'quarantined')
    check('intake','completion replay is stable',main.complete('tenant-a','alice',first['id'],101) == 'quarantined')
    check('intake','completion creates one durable job',main.db.execute('SELECT count(*) FROM jobs').fetchone()[0] == 1)
    denied('intake','post-completion upload cannot change pinned version',409,lambda:main.upload(first['id'],first['capability'],b'hello\n',102))
    observations['intake'] = {'create_replay_preserves_id_and_expiry':True,
        'upload_window_ms':10000,'same_byte_upload_replay':True,
        'wrong_target_capability_status':403,'wrong_checksum_status':422,
        'before_processing_download_status':409,'complete_replay_job_count':1,
        'post_completion_PUT_status':409,'client_filename_used_as_disk_key':False}

    rollback = store('completion-rollback')
    original = rollback.create('tenant-a','alice','op',contract(),0)
    rollback.upload(original['id'],original['capability'],b'hello\n',0)
    rollback.db.execute("CREATE TRIGGER fail_job BEFORE INSERT ON jobs BEGIN SELECT RAISE(ABORT,'injected'); END")
    try:
        rollback.complete('tenant-a','alice',original['id'],0)
    except sqlite3.IntegrityError:
        check('processing','job insert failure rolls back quarantine transition',rollback.owned('tenant-a','alice',original['id'])['state'] == 'uploading')
    else:
        raise AssertionError('missing injected completion failure')
    check('processing','completion rollback keeps uploaded object for retry',rollback.objects.read('raw',original['id']) == b'hello\n')
    rollback.db.execute('DROP TRIGGER fail_job')
    rollback.complete('tenant-a','alice',original['id'],0)
    job = main.claim(100)
    check('processing','worker claims quarantined source',job['id'] == first['id'] and main.owned('tenant-a','alice',first['id'])['state'] == 'processing')
    result,reason = main.inspect_content(job)
    check('processing','text processor derives bounded summary',json.loads(result)['characters'] == 6 and reason is None)
    denied('processing','processing source cannot yet download',409,lambda:main.download('tenant-a','alice',first['id']))
    check('processing','current worker publishes ready result',main.publish(job,result,reason,101))
    check('processing','ready download is original checked bytes',main.download('tenant-a','alice',first['id']) == b'hello\n')
    check('processing','duplicate worker result cannot republish',not main.publish(job,result,reason,102))
    ready_row = main.owned('tenant-a','alice',first['id'])
    check('processing','ready metadata references actual derived bytes',main.objects.read('derived',ready_row['result_key']) == result)
    for label,raw,expected in [('bad-utf8',b'\xff','unsupported_utf8'),('nul',b'a\x00b','lesson_content_policy'),('marker',b'[BLOCKED]','lesson_content_policy')]:
        item = store(label)
        value = prepared(item,label,raw)
        selected = item.claim(0)
        artifact,why = item.inspect_content(selected)
        item.publish(selected,artifact,why,1)
        check('processing',label+' is rejected with explicit reason',item.owned('tenant-a','alice',value['id'])['state'] == 'rejected' and why == expected)
        denied('processing',label+' never downloadable',409,lambda:item.download('tenant-a','alice',value['id']))
    lost = store('artifact-rollback')
    value = prepared(lost,'op')
    selected = lost.claim(0)
    artifact,why = lost.inspect_content(selected)
    lost.db.execute("CREATE TRIGGER fail_ready BEFORE UPDATE OF state ON uploads WHEN NEW.state='ready' BEGIN SELECT RAISE(ABORT,'injected'); END")
    try:
        lost.publish(selected,artifact,why,1)
    except sqlite3.IntegrityError:
        check('processing','artifact write can survive rolled-back metadata publish',len(list((lost.objects.root/'derived').iterdir())) == 1)
    else:
        raise AssertionError('missing injected publication failure')
    check('processing','failed publication stays processing',lost.owned('tenant-a','alice',value['id'])['state'] == 'processing')
    check('processing','collector removes unreferenced artifact while retaining source',lost.cleanup(2) == 1 and lost.objects.path('raw',value['id']).exists())
    lost.db.execute('DROP TRIGGER fail_ready')
    check('processing','retry can recreate artifact and publish correctly',lost.publish(selected,artifact,why,3) and lost.download('tenant-a','alice',value['id']) == b'hello\n')
    observations['processing'] = {'completed_state':'quarantined','claimed_state':'processing',
        'accepted_state':'ready','rejected_examples':['unsupported_utf8','lesson_content_policy'],
        'completion_job_transaction_rollback':True,'artifact_survives_metadata_rollback':True,
        'orphan_artifact_collected':True,'publication_retry_succeeds':True,
        'antivirus_or_general_document_safety_proven':False}

    lease = store('leases')
    value = prepared(lease,'op')
    old = lease.claim(0)
    artifact,why = lease.inspect_content(old)
    check('lifecycle','unexpired job cannot be claimed',lease.claim(1999) is None)
    check('lifecycle','lease equality fences publication',not lease.publish(old,artifact,why,2000))
    renewed = lease.claim(2000)
    check('lifecycle','expired claim gets a new token',renewed['id'] == old['id'] and renewed['token'] != old['token'])
    check('lifecycle','old token cannot publish after reclaim',not lease.publish(old,artifact,why,2001))
    check('lifecycle','new owner publishes one artifact',lease.publish(renewed,artifact,why,2001) and len(list((lease.objects.root/'derived').iterdir())) == 1)
    deletion = store('deletion')
    value = prepared(deletion,'op')
    selected = deletion.claim(0)
    artifact,why = deletion.inspect_content(selected)
    deletion.delete('tenant-a','alice',value['id'])
    check('lifecycle','delete fences a previously computed result',not deletion.publish(selected,artifact,why,1))
    check('lifecycle','deleted source physically collected',deletion.cleanup(2) == 1)
    denied('lifecycle','still-unexpired capability cannot recreate deleted source',410,lambda:deletion.upload(value['id'],value['capability'],b'hello\n',3))
    denied('lifecycle','deleted metadata remains tombstoned',410,lambda:deletion.download('tenant-a','alice',value['id']))
    deletion.delete('tenant-a','alice',value['id'])
    check('lifecycle','repeated delete and cleanup are harmless',deletion.cleanup(4) == 0)
    abandoned = store('abandoned')
    value = abandoned.create('tenant-a','alice','op',contract(),0)
    abandoned.upload(value['id'],value['capability'],b'hello\n',9999)
    denied('lifecycle','completion at upload-expiry equality is too late',410,lambda:abandoned.complete('tenant-a','alice',value['id'],10000))
    check('lifecycle','sweeper expires abandoned metadata and removes bytes',abandoned.cleanup(10000) == 1 and abandoned.owned('tenant-a','alice',value['id'])['state'] == 'expired')
    old_intent = abandoned.create('tenant-a','alice','op',contract(),20000)
    check('lifecycle','expired create replay does not renew upload window',old_intent['expires_ms'] == 10000 and old_intent['id'] == value['id'])
    denied('lifecycle','expired replay capability remains expired',410,lambda:abandoned.upload(value['id'],old_intent['capability'],b'hello\n',20000))
    crashed = store('crashed')
    value = prepared(crashed,'op')
    attempts = [crashed.claim(now)['attempts'] for now in (0,2000,4000)]
    check('lifecycle','three crashed claims consume bounded attempt budget',attempts == [1,2,3])
    check('lifecycle','expired third attempt becomes failed',crashed.claim(6000) is None and crashed.owned('tenant-a','alice',value['id'])['state'] == 'failed')
    orphan = store('orphans')
    orphan.objects.put('raw',uuid.uuid4().hex,b'orphan')
    orphan.objects.put('derived',uuid.uuid4().hex+'.'+uuid.uuid4().hex,b'orphan')
    check('lifecycle','inventory collector removes metadata-free objects',orphan.cleanup(0) == 2)
    main.objects.path('raw',first['id']).unlink()
    denied('lifecycle','missing ready object is availability failure, not success',503,lambda:main.download('tenant-a','alice',first['id']))
    check('lifecycle','cleanup does not touch outside-area sentinel',outside.read_bytes() == b'owned sentinel outside object areas')
    observations['lifecycle'] = {'lease_ms':2000,'stale_publication_accepted':False,
        'post_delete_publication_accepted':False,'late_capability_resurrection_status':410,
        'expiry_equality_ms':10000,'abandoned_state_after_sweep':'expired',
        'expired_replay_renews_window':False,'three_crashes_state':'failed',
        'ready_but_missing_source_status':503,'arbitrary_external_cloud_writes_coordinated':False}

    limited = store('metadata-limit')
    for number in range(128):
        limited.create('tenant-a','alice','op'+str(number),contract(),0)
    denied('validation','finite metadata cap rejects new work',503,lambda:limited.create('tenant-a','alice','overflow',contract(),0))
    check('validation','original replay still works at metadata capacity',limited.create('tenant-a','alice','op0',contract(),1)['replay'])

    runtime = store('http')
    runtime.close()
    server_clock = [0]
    api = server(directory/'http.sqlite',directory/'http-objects',SECRET,lambda:server_clock[0])
    api_thread = Thread(target=api.serve_forever,name='s3-owned-http')
    api_thread.start()
    ports.append(api.server_port)
    def request(method,path,body=None,token='lesson-alice',extra=None):
        headers = {'Authorization':'Bearer '+token} if token else {}
        headers.update(extra or {})
        connection = HTTPConnection('127.0.0.1',api.server_port,timeout=3)
        try:
            connection.request(method,path,body=body,headers=headers)
            response = connection.getresponse()
            return response.status,dict(response.getheaders()),response.read()
        finally:
            connection.close()
    create_body = json.dumps(contract()).encode()
    check('http','intake requires authentication',request('POST','/api/files',create_body,token='')[0] == 401)
    check('http','intake requires operation key',request('POST','/api/files',create_body)[0] == 400)
    check('http','malformed JSON returns 400',request('POST','/api/files',b'{',extra={'Idempotency-Key':'bad'})[0] == 400)
    initial = request('POST','/api/files',create_body,extra={'Idempotency-Key':'http-create'})
    value = json.loads(initial[2])
    file_id = value['id']
    base = '/api/files/'+file_id
    check('http','create responds 201',initial[0] == 201)
    repeat = request('POST','/api/files',create_body,extra={'Idempotency-Key':'http-create'})
    check('http','real create replay retains ID',json.loads(repeat[2])['id'] == file_id and json.loads(repeat[2])['replay'])
    check('http','metadata response is no-store',initial[1].get('Cache-Control') == 'no-store')
    check('http','other owner status is hidden',request('GET',base,token='lesson-bob')[0] == 404)
    check('http','other tenant delete is hidden',request('DELETE',base,token='lesson-other')[0] == 404)
    check('http','missing bytes block complete',request('POST',base+'/complete')[0] == 409)
    check('http','raw object is not publicly downloadable',request('GET',value['upload_path'],token='')[0] == 404)
    put_headers = {'Content-Type':'text/plain','X-Lesson-Upload':value['capability']}
    check('http','PUT requires upload capability',request('PUT',value['upload_path'],b'hello\n',token='',extra={'Content-Type':'text/plain'})[0] == 403)
    check('http','PUT declared type restricted',request('PUT',value['upload_path'],b'',token='',extra={'Content-Type':'text/html'})[0] == 415)
    check('http','oversized declared body rejected before reading',request('PUT',value['upload_path'],b'',token='',extra={**put_headers,'Content-Length':'1025'})[0] == 413)
    check('http','actual wrong checksum returns 422',request('PUT',value['upload_path'],b'other\n',token='',extra=put_headers)[0] == 422)
    with ThreadPoolExecutor(max_workers=2) as pool:
        puts = list(pool.map(lambda _:request('PUT',value['upload_path'],b'hello\n',token='',extra=put_headers)[0],range(2)))
    check('concurrency','two actual PUTs create then replay without overwrite',sorted(puts) == [200,201])
    check('http','uploaded but unprocessed object denied',request('GET',base+'/download')[0] == 409)
    with ThreadPoolExecutor(max_workers=2) as pool:
        completed = list(pool.map(lambda _:request('POST',base+'/complete')[0],range(2)))
    check('concurrency','two actual completions are accepted idempotently',completed == [202,202])
    runtime = store('http')
    check('concurrency','concurrent completion creates one durable job',runtime.db.execute('SELECT count(*) FROM jobs').fetchone()[0] == 1)
    barrier = Barrier(2)
    def claim_worker(_):
        worker = Uploads(directory/'http.sqlite',directory/'http-objects',SECRET)
        try:
            barrier.wait(timeout=5)
            return worker.claim(0)
        finally:
            worker.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim_worker,range(2)))
    selected = next(item for item in claims if item is not None)
    check('concurrency','independent connections produce one live processing claim',sum(item is not None for item in claims) == 1)
    artifact,why = runtime.inspect_content(selected)
    runtime.publish(selected,artifact,why,1)
    download = request('GET',base+'/download')
    check('http','READY download returns exact accepted source',download[0] == 200 and download[2] == b'hello\n')
    check('http','download is attachment',download[1].get('Content-Disposition') == 'attachment; filename="download.txt"')
    check('http','download disables MIME sniffing',download[1].get('X-Content-Type-Options') == 'nosniff')
    check('http','download served as UTF-8 plain text',download[1].get('Content-Type') == 'text/plain; charset=utf-8')
    check('http','private download is no-store',download[1].get('Cache-Control') == 'no-store')
    check('http','other owner cannot download READY file',request('GET',base+'/download',token='lesson-bob')[0] == 404)
    check('http','completed upload capability cannot overwrite READY',request('PUT',value['upload_path'],b'hello\n',token='',extra=put_headers)[0] == 409)
    check('http','delete tombstones immediately',request('DELETE',base)[0] == 200)
    check('http','new download after delete is gone',request('GET',base+'/download')[0] == 410)
    check('http','late PUT cannot resurrect tombstoned object',request('PUT',value['upload_path'],b'hello\n',token='',extra=put_headers)[0] == 410)
    check('http','delete replay remains successful',request('DELETE',base)[0] == 200)
    check('http','cleanup removes deleted source and result',runtime.cleanup(2) == 2)
    observations['concurrency'] = {'concurrent_call_count':6,'PUT_statuses_sorted':sorted(puts),
        'completion_statuses':completed,'durable_processing_jobs':1,
        'live_claims':sum(item is not None for item in claims),'winner_order_assumed':False}
    observations['http_contract'] = {'create_status':initial[0], 'PUT_without_owner_bearer_allowed_with_capability':True,
        'before_ready_download_status':409,'ready_download_status':download[0],
        'content_type':download[1]['Content-Type'],'content_disposition':download[1]['Content-Disposition'],
        'cache_control':download[1]['Cache-Control'],'nosniff':True,
        'after_delete_download_status':410,'late_PUT_after_delete_status':410,
        'real_S3_or_multipart_protocol_implemented':False}
    estimated = calculate()
    for name,expected in [('average_incoming_MiB_per_second',0.231),('hypothetical_peak_uploads_per_second',1.157),
        ('raw_30_day_storage_GiB',585.938),('derived_30_day_storage_GiB',146.484),
        ('average_required_CPU_cores_at_full_utilization',0.231),('daily_download_GiB',97.656),('one_day_unfinished_parts_GiB',31.25)]:
        check('estimates',name,estimated[name] == expected)
    check('estimates','calculations make no capacity claim',not estimated['measured_capacity'])
    observations['estimates'] = estimated
finally:
    if api is not None:
        api.shutdown()
        api.server_close()
    if api_thread is not None:
        api_thread.join(timeout=5)
        assert not api_thread.is_alive()
    for item in stores:
        item.close()
    assert directory.parent == Path(gettempdir()).resolve() and directory.name.startswith('placement-s3-verify-')
    temporary.cleanup()

closed = True
for item in stores:
    try:
        item.db.execute('SELECT 1')
    except sqlite3.ProgrammingError:
        continue
    closed = False
check('cleanup','all tracked metadata connections closed',closed)
check('cleanup','owned temporary directory removed',not directory.exists())
for port in ports:
    with socket.socket() as probe:
        probe.settimeout(1)
        check('cleanup','owned HTTP listener closed',probe.connect_ex(('127.0.0.1',port)) != 0)
check('cleanup','port 3000 not used',3000 not in ports)
assert len({(item['group'],item['name']) for item in checks}) == len(checks)
proof = {'label':'S3','verified_date':'2026-10-17','python':platform.python_version(),
    'sqlite':sqlite3.sqlite_version,'os':platform.system(),'total':len(checks),
    'counts':dict(Counter(item['group'] for item in checks)), 'checks':checks,'observations':observations,
    'cleanup':{'fixture_ports':ports,'temporary_database_directory_removed':not directory.exists(),
        'sqlite_connections_closed':closed,'temporary_http_servers_closed':True,
        'concurrent_worker_calls_completed':6,'port_3000_used':False},
    'scope':'Owned local files/SQLite and actual loopback HTTP only. Immutable 1 KiB text objects, custom bearer capability and deterministic content policy; no S3 emulation, multipart transfer, antivirus, general document safety, external uploads, production authentication/TLS, distributed locking/clock, power-loss guarantee or load benchmark. Local writes and inventory cleanup share the SQLite write authority; cloud direct uploads require a different coordination protocol.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':proof['total'],'counts':proof['counts'],'cleanup':proof['cleanup']},indent=2))
