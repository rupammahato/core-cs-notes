"""Real loopback policy/drain/saturation tests plus explicit offline SLI exercises."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Event, Thread
import json
import platform
import sqlite3

from policy import Store, Principal, TOKENS, Denied
from server import Runtime, make_server
from indicators import analyze, sample_workload, percentile, capacity_plan

BASE = Path(__file__).resolve().parent
checks, observations = [], {}


def check(group, name, condition):
    assert condition, name
    checks.append({'group': group, 'name': name, 'passed': True})


def raises(group, name, expected, action):
    try:
        action()
    except expected:
        check(group, name, True)
    else:
        raise AssertionError(name)


def main():
    owned_servers, stores = [], []
    with TemporaryDirectory(prefix='placement-a4-') as directory:
        directory = Path(directory)
        database, vault = directory/'notes.sqlite', directory/'private-vault'
        store = Store(database, vault)
        stores.append(store)
        store.seed()
        runtime = Runtime()
        clock = {'now': 0.0}

        def start(state, quota_limit=1000):
            server = make_server(store, state, lambda: clock['now'], quota_limit)
            thread = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05})
            thread.start()
            owned_servers.append((server, thread))
            return server

        def call(server, state, method, path, body=None, token='lesson-alice', extra=None):
            headers = {'Authorization': 'Bearer '+token} if token else {}
            headers.update(extra or {})
            connection = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            try:
                connection.request(method, path, body=body, headers=headers)
                response = connection.getresponse()
                result = {'status': response.status, 'headers': dict(response.getheaders()), 'body': response.read()}
            finally:
                connection.close()
            identity = result['headers']['X-Request-Id']
            with state.condition:
                assert state.condition.wait_for(lambda: any(row['trace_id'] == identity for row in state.logs), timeout=2)
            if result['headers']['Content-Type'] == 'application/json':
                result['json'] = json.loads(result['body'])
            return result

        server = start(runtime)
        fixture_ports = []
        try:
            first = call(server, runtime, 'GET', '/notes/shared_id')
            check('http_policy', 'owned note is readable', first['status'] == 200 and first['json']['title'] == 'PRIVATE_ALPHA_NOTE')
            check('http_policy', 'private response disables caching', first['headers']['Cache-Control'] == 'no-store')
            check('http_policy', 'response forbids MIME sniffing', first['headers']['X-Content-Type-Options'] == 'nosniff')
            check('http_policy', 'server-generated correlation ID has fixed hex shape', len(first['headers']['X-Request-Id']) == 32 and int(first['headers']['X-Request-Id'], 16)>0)
            beta = call(server, runtime, 'GET', '/notes/shared_id', token='lesson-beta')
            check('http_policy', 'same resource ID resolves inside verified tenant', beta['status'] == 200 and beta['json']['title'] == 'PRIVATE_BETA_NOTE')
            bob = call(server, runtime, 'GET', '/notes/shared_id', token='lesson-bob')
            absent = call(server, runtime, 'GET', '/notes/absent')
            check('http_policy', 'cross-owner response matches absent resource', bob['status'] == absent['status'] == 404 and bob['json'] == absent['json'])
            spoofed = call(server, runtime, 'GET', '/notes/shared_id', token='lesson-bob', extra={'X-Tenant':'alpha','X-Owner':'alice'})
            check('http_policy', 'identity headers do not override principal', spoofed['status'] == 404)
            listed = call(server, runtime, 'GET', '/notes', token='lesson-bob')
            check('http_policy', 'list query remains owner-scoped', listed['json']['notes'] == [{'id':'bob_note','title':'PRIVATE_BOB_NOTE'}])
            viewer = call(server, runtime, 'GET', '/notes', token='lesson-viewer')
            check('http_policy', 'viewer can list without gaining other-owner content', viewer['status'] == 200 and viewer['json']['notes'] == [])
            forbidden = call(server, runtime, 'POST', '/uploads', b'x', token='lesson-viewer', extra={'X-Filename':'x.txt','Content-Type':'text/plain'})
            check('http_policy', 'read-only role cannot upload', forbidden['status'] == 403)
            for token in ('', 'forged'):
                denied = call(server, runtime, 'GET', '/notes', token=token)
                check('http_policy', 'unknown or missing lesson credential rejected '+repr(token), denied['status'] == 401 and denied['headers']['WWW-Authenticate'] == 'Bearer')
            with store.lock:
                store.db.execute("UPDATE members SET active=0 WHERE tenant='alpha' AND user='alice'")
            revoked = call(server, runtime, 'GET', '/notes/shared_id')
            check('http_policy', 'current membership revocation blocks next request', revoked['status'] == 403)
            with store.lock:
                store.db.execute("UPDATE members SET active=1,role='unknown' WHERE tenant='alpha' AND user='alice'")
            denied_role = call(server, runtime, 'GET', '/notes')
            check('http_policy', 'unknown role denies by default', denied_role['status'] == 403)
            with store.lock:
                store.db.execute("UPDATE members SET role='editor' WHERE tenant='alpha' AND user='alice'")
            raises('http_policy', 'missing membership denies direct store caller', Denied,
                lambda: store.listing(Principal('missing', 'alice')))
            original_note = store.note

            def injected_failure(*_):
                raise RuntimeError('private_database_failure_details')

            store.note = injected_failure
            try:
                internal = call(server, runtime, 'GET', '/notes/shared_id')
            finally:
                store.note = original_note
            check('http_policy', 'unexpected failure returns a safe public error', internal['status'] == 500 and internal['json'] == {'error':'internal_error'})
            correlated = call(server, runtime, 'GET', '/notes/shared_id?secret=private_query_value',
                extra={'X-Request-Id':'attacker_supplied_id'})
            check('http_policy', 'untrusted correlation header cannot set internal request ID', correlated['status'] == 200 and correlated['headers']['X-Request-Id'] != 'attacker_supplied_id')
            observations['authorization'] = {'owned_note': first['status'], 'other_owner': bob['status'],
                'spoofed_headers': spoofed['status'], 'read_only_upload': forbidden['status'],
                'revoked_membership': revoked['status'], 'same_id_other_tenant_title': beta['json']['title']}

            def upload(name, body=b'private uploaded text', mime='text/plain', token='lesson-alice'):
                return call(server, runtime, 'POST', '/uploads', body, token, {'X-Filename':name,'Content-Type':mime})

            staged = upload('study.txt')
            identity = staged['json']['id']
            check('uploads', 'accepted upload starts pending', staged['status'] == 202 and staged['json']['state'] == 'pending')
            check('uploads', 'server chooses an opaque storage key', len(identity) == 32 and (vault/identity).is_file() and not (vault/'study.txt').exists())
            pending = call(server, runtime, 'GET', '/uploads/'+identity)
            check('uploads', 'pending upload cannot be downloaded', pending['status'] == 409)
            hidden = call(server, runtime, 'GET', '/uploads/'+identity, token='lesson-beta')
            check('uploads', 'different tenant cannot read upload metadata', hidden['status'] == 404)
            check('uploads', 'internal text validator approves expected bytes', store.approve('alpha', identity) == 'ready')
            ready = call(server, runtime, 'GET', '/uploads/'+identity)
            check('uploads', 'approved bytes download through scoped handler', ready['status'] == 200 and ready['body'] == b'private uploaded text')
            check('uploads', 'download forces attachment disposition', ready['headers']['Content-Disposition'] == 'attachment; filename="study.txt"')
            check('uploads', 'download uses generic binary MIME', ready['headers']['Content-Type'] == 'application/octet-stream')
            check('uploads', 'approval is stable when repeated', store.approve('alpha', identity) == 'ready')
            for name in ('../escape.txt', 'bad.html', 'bad..txt'):
                result = upload(name)
                check('uploads', 'unsafe or unsupported filename rejected '+name, result['status'] == 400)
            check('uploads', 'unsupported MIME claim rejected', upload('image.txt', mime='image/png')['status'] == 415)
            check('uploads', 'transport body bound rejects oversized content', upload('large.txt', b'x'*1025)['status'] == 413)
            check('uploads', 'empty upload rejected', upload('empty.txt', b'')['status'] == 413)
            malformed = upload('invalid.txt', b'\xff\x00')
            malformed_id = malformed['json']['id']
            check('uploads', 'unvalidated bytes remain quarantined', malformed['status'] == 202)
            check('uploads', 'strict decoding rejects invalid text', store.approve('alpha', malformed_id) == 'rejected')
            check('uploads', 'rejected upload remains unavailable', call(server, runtime, 'GET', '/uploads/'+malformed_id)['status'] == 409)
            tampered = upload('tampered.txt', b'original')
            tampered_id = tampered['json']['id']
            (vault/tampered_id).write_bytes(b'changed!')
            check('uploads', 'approval checks staged byte digest', store.approve('alpha', tampered_id) == 'rejected')
            check('uploads', 'path-like download ID cannot become a disk path', call(server, runtime, 'GET', '/uploads/../escape.txt')['status'] == 404)
            check('uploads', 'no file is written outside private vault', not (directory/'escape.txt').exists())
            check('uploads', 'large valid upload fits remaining retained-byte budget', upload('bulk.txt', b'a'*1024)['status'] == 202)
            storage_full = upload('bulk2.txt', b'b'*1024)
            check('uploads', 'tenant retained-byte budget rejects excess', storage_full['status'] == 429 and storage_full['json']['error'] == 'storage_quota_exceeded')
            with store.lock:
                retained = store.db.execute("SELECT sum(size) FROM uploads WHERE tenant='alpha'").fetchone()[0]
            check('uploads', 'rejected excess leaves retained bytes within budget', retained<=2048)
            observations['uploads'] = {'accepted_state': staged['json']['state'], 'before_approval': pending['status'],
                'after_approval': ready['status'], 'other_tenant': hidden['status'],
                'invalid_text_state': 'rejected', 'tampered_bytes_state': 'rejected',
                'over_byte_budget': storage_full['status'], 'retained_bytes': retained,
                'antivirus_executed': False}

            quota_runtime = Runtime()
            quota_server = start(quota_runtime, 2)
            with store.lock:
                store.db.execute('DELETE FROM quota')
            clock['now'] = 9.9
            a = call(quota_server, quota_runtime, 'GET', '/notes')
            b = call(quota_server, quota_runtime, 'GET', '/notes', token='lesson-bob')
            c = call(quota_server, quota_runtime, 'GET', '/notes')
            check('quotas', 'tenant users share a request budget', [a['status'],b['status'],c['status']] == [200,200,429])
            check('quotas', 'quota response states a retry delay', c['headers']['Retry-After'] == '1')
            check('quotas', 'another tenant has a separate budget', call(quota_server, quota_runtime, 'GET', '/notes', token='lesson-beta')['status'] == 200)
            clock['now'] = 10
            d = call(quota_server, quota_runtime, 'GET', '/notes')
            e = call(quota_server, quota_runtime, 'GET', '/notes')
            check('quotas', 'fixed window resets at explicit boundary', d['status'] == e['status'] == 200)
            observations['quota_window'] = {'limit_per_tenant_per_10_seconds': 2,
                'before_boundary_statuses': [a['status'],b['status'],c['status']],
                'after_boundary_statuses': [d['status'],e['status']],
                'accepted_near_boundary': 4, 'retry_after_seconds': int(c['headers']['Retry-After'])}
            # Separate connections synchronize admission for a remaining single quota slot.
            with store.lock:
                store.db.execute('DELETE FROM quota')
            barrier = Barrier(2)

            def quota_race():
                other = Store(database, vault)
                try:
                    barrier.wait(timeout=5)
                    try:
                        other.take_quota(TOKENS['lesson-alice'], 'race', 20, limit=1)
                        return 200
                    except Denied as error:
                        return error.status
                finally:
                    other.close()

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(quota_race) for _ in range(2)]
                competing = sorted(future.result(timeout=10) for future in futures)
            check('quotas', 'two connections cannot both take final quota slot', competing == [200,429])
            check('quotas', 'authoritative counter increments once', store.db.execute("SELECT used FROM quota WHERE action='race'").fetchone()[0] == 1)
            raises('quotas', 'zero quota limit rejected', ValueError,
                lambda: store.take_quota(TOKENS['lesson-alice'], 'read', 0, limit=0))
            observations['quota_race'] = {'independent_connections': 2, 'statuses': competing, 'stored_used': 1}

            lifecycle = Runtime(capacity=1)
            drain_server = start(lifecycle)
            check('lifecycle', 'live process reports liveness', call(drain_server, lifecycle, 'GET', '/livez')['status'] == 200)
            check('lifecycle', 'ready process reports readiness', call(drain_server, lifecycle, 'GET', '/readyz')['status'] == 200)
            lifecycle.database_available = False
            check('lifecycle', 'dependency failure removes readiness', call(drain_server, lifecycle, 'GET', '/readyz')['status'] == 503)
            check('lifecycle', 'dependency failure does not falsely kill liveness', call(drain_server, lifecycle, 'GET', '/livez')['status'] == 200)
            check('lifecycle', 'unready process rejects application work', call(drain_server, lifecycle, 'GET', '/notes')['status'] == 503)
            lifecycle.database_available = True
            lifecycle.hold = Event()
            with ThreadPoolExecutor(max_workers=1) as executor:
                active = executor.submit(call, drain_server, lifecycle, 'GET', '/notes/shared_id')
                with lifecycle.condition:
                    assert lifecycle.condition.wait_for(lambda: lifecycle.active == 1, timeout=2)
                overload = call(drain_server, lifecycle, 'GET', '/notes')
                check('lifecycle', 'capacity gate rejects work above active bound', overload['status'] == 503 and overload['json']['error'] == 'overloaded')
                lifecycle.drain()
                check('lifecycle', 'drain withdraws readiness', call(drain_server, lifecycle, 'GET', '/readyz')['status'] == 503)
                check('lifecycle', 'draining process remains live', call(drain_server, lifecycle, 'GET', '/livez')['status'] == 200)
                check('lifecycle', 'drain rejects new application work', call(drain_server, lifecycle, 'GET', '/notes')['status'] == 503)
                lifecycle.hold.set()
                completed = active.result(timeout=5)
            check('lifecycle', 'accepted request completes during drain', completed['status'] == 200)
            check('lifecycle', 'drain reaches zero active application requests', lifecycle.active == 0)
            observations['drain'] = {'initial_ready': 200, 'dependency_unready': 503,
                'liveness_during_dependency_failure': 200, 'over_capacity': overload['status'],
                'new_work_during_drain': 503, 'already_accepted_work': completed['status'], 'active_after_drain': lifecycle.active,
                'operating_system_signal_sent': False}

            saturation = Runtime(capacity=2)
            burst_server = start(saturation)
            saturation.hold = Event()
            with ThreadPoolExecutor(max_workers=8) as executor:
                admitted = [executor.submit(call, burst_server, saturation, 'GET', '/notes/shared_id') for _ in range(2)]
                with saturation.condition:
                    assert saturation.condition.wait_for(lambda: saturation.active == 2, timeout=2)
                rejected = [executor.submit(call, burst_server, saturation, 'GET', '/notes') for _ in range(6)]
                rejected_results = [future.result(timeout=5) for future in rejected]
                saturation.hold.set()
                admitted_results = [future.result(timeout=5) for future in admitted]
            statuses = [row['status'] for row in admitted_results+rejected_results]
            check('saturation', 'controlled burst admits exactly two held requests', statuses.count(200) == 2)
            check('saturation', 'controlled burst explicitly rejects six excess requests', statuses.count(503) == 6)
            check('saturation', 'observed peak application work respects bound', saturation.peak == 2)
            check('saturation', 'all eight requests are counted', sum(saturation.counts.values()) == 8)
            check('saturation', 'all admitted work drains after release', saturation.active == 0)
            observations['saturation'] = {'offered_requests': 8, 'accepted_completed': statuses.count(200),
                'overload_responses': statuses.count(503), 'peak_active_application_work': saturation.peak,
                'test_shape': 'two accepted requests held; six excess requests offered; then release',
                'throughput_capacity_measured': False}

            trace_id = first['headers']['X-Request-Id']
            trace = next(row for row in runtime.traces if row['trace_id'] == trace_id)
            check('telemetry', 'request trace follows actual local boundaries', trace['events'] == ['http.received','identity.lesson_allowlist','authorization.current_membership','quota.accepted','store.completed','http.response_written'])
            check('telemetry', 'log schema permits only selected metadata', all(set(row) == {'trace_id','method','route','status','duration_ms'} for row in runtime.logs))
            encoded_logs = json.dumps(list(runtime.logs))
            check('telemetry', 'logs omit lesson credentials and private contents', all(secret not in encoded_logs for secret in ('lesson-alice','PRIVATE_ALPHA_NOTE','private uploaded text')))
            check('telemetry', 'logs omit raw resource paths and filenames', 'shared_id' not in encoded_logs and 'study.txt' not in encoded_logs)
            check('telemetry', 'logs omit query values and internal failure details', all(value not in encoded_logs for value in ('private_query_value','private_database_failure_details','attacker_supplied_id')))
            check('telemetry', 'resource metrics use bounded route templates', all(key[1] in {'/notes','/notes/:id','/uploads','/uploads/:id','/unmatched','/livez','/readyz'} for key in runtime.counts))
            check('telemetry', 'metric dimensions omit principal and resource identities', all(len(key) == 3 for key in runtime.counts))
            check('telemetry', 'local durations use nonnegative monotonic interval', all(row['duration_ms']>=0 for row in runtime.logs))
            check('telemetry', 'in-memory diagnostic buffers are bounded', runtime.logs.maxlen == runtime.traces.maxlen == 128)
            observations['telemetry'] = {'trace_events': trace['events'],
                'log_fields': sorted(runtime.logs[0]), 'metric_labels': ['method','route_template','status_class'],
                'diagnostic_buffer_limit': 128, 'private_content_logged': False,
                'otel_exporter_or_prometheus_server_started': False}
        finally:
            for state in (runtime, locals().get('lifecycle'), locals().get('saturation')):
                if state is not None and state.hold is not None:
                    state.hold.set()
            for owned, thread in owned_servers:
                fixture_ports.append(owned.server_port)
                owned.shutdown()
                owned.server_close()
                thread.join(timeout=5)
                assert not thread.is_alive()
            for owned in stores:
                owned.close()
    check('cleanup', 'temporary files and private vault removed after connections close', not directory.exists())
    check('cleanup', 'all owned HTTP serving threads stopped', all(not thread.is_alive() for _,thread in owned_servers))
    samples = sample_workload()
    objective = analyze(samples)
    check('indicators', 'authored SLI eligibility denominator is explicit', objective['eligible'] == 1000 and objective['excluded'] == 3)
    check('indicators', 'successful but slow responses fail good-event condition', objective['good'] == 970 and objective['bad'] == 30)
    check('indicators', 'eligible rate limits remain in denominator', sum(sample['status'] == 429 and sample['eligible'] for sample in samples) == 5)
    check('indicators', 'error budget and burn calculated consistently', objective['allowed_bad'] == 10 and objective['remaining_budget'] == -20 and objective['burn_rate'] == 3)
    check('indicators', 'tail percentiles reveal slow results despite healthy p95', objective['p95_ms'] == 50 and objective['p99_ms'] == 350)
    check('indicators', 'bad-event fraction fails selected objective', not objective['objective_passed'])
    good = [{'eligible':True,'status':200,'latency_ms':1,'leak':False}]
    check('indicators', 'all-good sample passes quantitative objective', analyze(good)['objective_passed'])
    leaked = deepcopy(good)
    leaked[0]['leak'] = True
    leak_result = analyze(leaked)
    check('indicators', 'confidentiality violation fails separate invariant gate', leak_result['good_fraction'] == 1 and not leak_result['objective_passed'] and not leak_result['invariant_passed'])
    check('indicators', 'empty denominator does not report healthy objective', analyze([])['good_fraction'] is None and not analyze([])['objective_passed'])
    check('indicators', 'percentile convention is nearest rank', percentile([1,2,3,100],0.95) == 100)
    raises('indicators', 'negative latency rejected', ValueError, lambda: analyze([dict(good[0],latency_ms=-1)]))
    raises('indicators', 'boolean eligibility required', ValueError, lambda: analyze([dict(good[0],eligible=1)]))
    raises('indicators', 'perfect target rejected by budget exercise', ValueError, lambda: analyze(good,target='1'))
    plan = capacity_plan()
    check('planning', 'steady-state in-flight estimate uses explicit units', plan['estimated_mean_in_flight'] == 10)
    check('planning', 'instance pools share a database connection budget', plan['application_connection_ceiling'] == 80 and not plan['pool_ceiling_fits_budget'])
    check('planning', 'hypothetical instance cost uses stated rate and hours', plan['assumed_instance_hours'] == 2880 and plan['hypothetical_instance_cost'] == 288)
    check('planning', 'cost exclusions remain explicit', len(plan['cost_excludes']) == 6)
    raises('planning', 'invalid planning instance count rejected', ValueError, lambda: capacity_plan(instances=0))
    observations['objectives'] = {'authored_sample_result': objective, 'one_success_with_leak': leak_result,
                                'production_slo_measured': False}
    observations['planning'] = plan
    counts = {}
    for item in checks:
        counts[item['group']] = counts.get(item['group'],0)+1
    proof = {'label':'A4','verified_date':'2026-10-16','python':platform.python_version(),
        'sqlite':sqlite3.sqlite_version,'os':platform.system()+' '+platform.release(),
        'total':len(checks),'counts':counts,'checks':checks,'observations':observations,
        'cleanup':{'sqlite_connections_closed':True,'temporary_database_directory_removed':True,
                   'temporary_http_servers_closed':True,'fixture_ports':fixture_ports,
                   'concurrent_quota_worker_calls_completed':2,'port_3000_used':False},
        'scope':'Real loopback HTTP authorization with published lesson tokens, current SQLite membership/scoped reads, two-connection atomic fixed-window quotas, private text-upload quarantine, application readiness/drain/admission and bounded diagnostic records. Dependency failure and held work are controlled flags/barriers. SLI samples and capacity/cost inputs are authored offline exercises. No production authentication/TLS, antivirus/object storage, Kubernetes/signal rollout, OTel/Prometheus backend, production SLO or throughput capacity verified.'}
    (BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'total':proof['total'],'counts':counts,'observations':observations,'cleanup':proof['cleanup']},indent=2))


if __name__ == '__main__':
    main()
