"""Fault-injected local delivery lifecycle, actual signed HTTP and owned cleanup."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Thread
import json
import platform
import socket
import sqlite3
from delivery import Conflict, Queue, envelope
from estimates import calculate
from protocol import initialize, server, sign
from worker import run_once

BASE = Path(__file__).resolve().parent
checks, observations, queues, ports = [], {}, [], []


def check(group, name, condition):
    assert condition, (group, name)
    checks.append({'group':group, 'name':name, 'passed':True})


def raises(group, name, exception, action):
    try:
        action()
    except exception:
        check(group, name, True)
    else:
        raise AssertionError(name)


temporary = TemporaryDirectory(prefix='placement-s2-verify-')
directory = Path(temporary.name)
api, api_thread = None, None


def queue(name):
    item = Queue(directory/(name+'.sqlite'))
    queues.append(item)
    return item


def rows(path, sql, parameters=()):
    db = sqlite3.connect(path)
    try:
        return db.execute(sql, parameters).fetchall()
    finally:
        db.close()


try:
    q = queue('intake')
    for name, action in [
        ('empty tenant', lambda:q.enqueue('', 'e', 'hello', 0)),
        ('delimiter identity', lambda:q.enqueue('t/a', 'e', 'hello', 0)),
        ('oversized event identity', lambda:q.enqueue('t', 'e'*65, 'hello', 0)),
        ('empty message', lambda:q.enqueue('t', 'e', '', 0)),
        ('oversized message', lambda:q.enqueue('t', 'e', 'x'*201, 0)),
        ('nonstring message', lambda:q.enqueue('t', 'e', {}, 0)),
        ('negative time', lambda:q.enqueue('t', 'e', 'hello', -1)),
        ('boolean time', lambda:q.enqueue('t', 'e', 'hello', True)),
        ('nonboolean preference', lambda:q.subscribe('t', 's', 'a', 1)),
        ('invalid lease', lambda:q.claim(0, 0))]:
        raises('validation', name, ValueError, action)
    check('validation', 'invalid intake creates no events', q.db.execute('SELECT count(*) FROM events').fetchone()[0] == 0)
    q.subscribe('t', 'enabled', 'a')
    q.subscribe('t', 'disabled', 'b', False)
    check('intake', 'new event accepted durably', q.enqueue('t', 'e', 'hello', 0))
    check('intake', 'only enabled subscription materialized', q.db.execute('SELECT count(*) FROM deliveries').fetchone()[0] == 1)
    check('intake', 'equivalent retry recognized', not q.enqueue('t', 'e', 'hello', 0))
    q.subscribe('t', 'later', 'c')
    check('intake', 'retry does not refanout newly added subscription', not q.enqueue('t', 'e', 'hello', 1) and q.db.execute('SELECT count(*) FROM deliveries').fetchone()[0] == 1)
    raises('intake', 'same event ID with changed message conflicts', Conflict, lambda:q.enqueue('t', 'e', 'changed', 1))
    check('intake', 'changed intent leaves original bytes intact', q.db.execute('SELECT body FROM events').fetchone()[0] == envelope('t', 'e', 'hello'))
    raises('intake', 'subscription target immutable', Conflict, lambda:q.subscribe('t', 'enabled', 'different'))
    check('intake', 'event scope includes tenant', q.enqueue('other', 'e', 'different', 0))
    q.close()
    q = queue('intake')
    check('intake', 'close/reopen preserves original event replay', not q.enqueue('t', 'e', 'hello', 10))
    job = q.claim(0)
    check('intake', 'cross-tenant status lookup returns no row', q.inspect('other', job['id']) is None)
    check('intake', 'owner-scoped status lookup finds row', q.inspect('t', job['id'])['status'] == 'inflight')
    rollback = queue('rollback')
    rollback.subscribe('t', 'a', 'a')
    rollback.subscribe('t', 'b', 'b')
    rollback.db.execute("CREATE TRIGGER inject_failure BEFORE INSERT ON deliveries WHEN NEW.subscription='b' BEGIN SELECT RAISE(ABORT,'injected'); END")
    raises('intake', 'fanout insert fault aborts event transaction', sqlite3.IntegrityError, lambda:rollback.enqueue('t', 'e', 'hello', 0))
    check('intake', 'fanout fault leaves no event', rollback.db.execute('SELECT count(*) FROM events').fetchone()[0] == 0)
    check('intake', 'fanout fault leaves no partial deliveries', rollback.db.execute('SELECT count(*) FROM deliveries').fetchone()[0] == 0)
    limited = queue('bounded')
    for i in range(8):
        limited.subscribe('t', 's'+str(i), 'a')
    raises('intake', 'fanout subscription cap enforced', ValueError, lambda:limited.subscribe('t', 'ninth', 'a'))
    retained = queue('retained')
    for i in range(256):
        retained.enqueue('t', 'e'+str(i), 'hello', 0)
    raises('intake', 'event retention cap rejects new work', ValueError, lambda:retained.enqueue('t', 'overflow', 'hello', 0))
    check('intake', 'existing outcome replay works at capacity', not retained.enqueue('t', 'e0', 'hello', 0))
    observations['intake'] = {'event_and_delivery_transaction_rollback':True,
        'stable_retry_refans_out':False, 'disabled_at_acceptance_materialized':False,
        'tenant_scoped_status':True, 'close_reopen_replay':True,
        'maximum_subscriptions_per_tenant':8, 'lesson_event_retention_cap':256}

    racing = queue('racing')
    racing.subscribe('t', 's', 'a')
    racing.close()
    barrier = Barrier(2)
    def concurrent_enqueue(_):
        item = Queue(directory/'racing.sqlite')
        try:
            barrier.wait(timeout=5)
            return item.enqueue('t', 'same', 'hello', 0)
        finally:
            item.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted = list(pool.map(concurrent_enqueue, range(2)))
    check('concurrency', 'two equivalent producers create one event', sum(accepted) == 1)
    check('concurrency', 'two producers create one delivery', rows(directory/'racing.sqlite', 'SELECT count(*) FROM deliveries')[0][0] == 1)
    barrier = Barrier(2)
    def concurrent_claim(_):
        item = Queue(directory/'racing.sqlite')
        try:
            barrier.wait(timeout=5)
            return item.claim(0)
        finally:
            item.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(concurrent_claim, range(2)))
    check('concurrency', 'one live delivery has one claim owner', sum(item is not None for item in claimed) == 1)
    check('concurrency', 'one durable attempt exists after race', rows(directory/'racing.sqlite', 'SELECT count(*) FROM attempts')[0][0] == 1)
    observations['concurrency'] = {'queue_worker_calls':4, 'new_events':sum(accepted),
        'live_claims':sum(item is not None for item in claimed), 'winner_order_assumed':False}

    leases = queue('leases')
    leases.subscribe('t', 's', 'a')
    leases.enqueue('t', 'e', 'hello', 0)
    old = leases.claim(0)
    check('leases', 'claim records attempt before network I/O', old['attempts'] == 1 and leases.db.execute('SELECT outcome FROM attempts').fetchone()[0] is None)
    check('leases', 'unexpired lease is not reclaimable', leases.claim(1999) is None)
    check('leases', 'completion at lease equality is fenced', not leases.finish(old, 200, 2000, 0))
    new = leases.claim(2000)
    check('leases', 'lease expiry equality permits reclaim', new['id'] == old['id'] and new['attempts'] == 2)
    check('leases', 'reclaim changes fencing token', new['token'] != old['token'])
    check('leases', 'stale worker cannot update reclaimed delivery', not leases.finish(old, 200, 2001, 0))
    check('leases', 'current worker can finish', leases.finish(new, 202, 2001, 0))
    check('leases', 'accepted 202 reaches succeeded state', leases.inspect('t', new['id'])['status'] == 'succeeded')
    check('leases', 'completed delivery cannot be claimed', leases.claim(5000) is None)
    check('leases', 'expired attempt retains ambiguity', leases.db.execute('SELECT outcome FROM attempts WHERE number=1').fetchone()[0] == 'lease_expired')
    crash = queue('crashes')
    crash.subscribe('t', 's', 'a')
    crash.enqueue('t', 'e', 'hello', 0)
    crash_jobs = [crash.claim(time) for time in (0, 2000, 4000)]
    check('leases', 'three crashes consume three bounded claims', [item['attempts'] for item in crash_jobs] == [1, 2, 3])
    check('leases', 'crashed last attempt becomes terminal on recovery poll', crash.claim(6000) is None and crash.inspect('t', crash_jobs[0]['id'])['status'] == 'failed')
    check('leases', 'crash recovery preserves three attempt records', crash.db.execute('SELECT count(*) FROM attempts').fetchone()[0] == 3)
    preferences = queue('preferences')
    preferences.subscribe('t', 's', 'a')
    preferences.enqueue('t', 'before', 'hello', 0)
    preferences.subscribe('t', 's', 'a', False)
    check('leases', 'opt-out is rechecked before claim', preferences.claim(0) is None)
    check('leases', 'queued optional notification becomes skipped', preferences.db.execute('SELECT status FROM deliveries').fetchone()[0] == 'skipped')
    preferences.subscribe('t', 's', 'a', True)
    check('leases', 're-enable does not resurrect skipped intent', preferences.claim(1) is None)
    observations['leases'] = {'lease_ms':2000, 'at_1999_reclaimable':False,
        'at_2000_reclaimable':True, 'stale_worker_completion_accepted':False,
        'new_worker_202_state':'succeeded', 'three_crashes_terminal':True,
        'opted_out_before_claim_state':'skipped', 'external_effects_fenced_by_lease':False}

    retry = queue('retry')
    retry.subscribe('t', 'one', 'a')
    retry.subscribe('t', 'two', 'b')
    retry.enqueue('t', 'e', 'hello', 0)
    first = retry.claim(0)
    other_endpoint = 'b' if first['endpoint'] == 'a' else 'a'
    check('retry', '429 schedules retry', retry.finish(first, 429, 0, 100, 2000))
    check('retry', 'provider hint is floor above jitter', retry.inspect('t', first['id'])['due'] == 2000)
    second = retry.claim(0)
    check('retry', 'other endpoint is not blocked by cooldown', second['endpoint'] == other_endpoint)
    retry.finish(second, 400, 0, 0)
    check('retry', '400 is permanent', retry.inspect('t', second['id'])['status'] == 'failed')
    retry.enqueue('t', 'another', 'hello', 1)
    another_other = retry.claim(1)
    check('retry', 'cooldown blocks new deliveries to same endpoint', another_other['endpoint'] == other_endpoint)
    retry.finish(another_other, 200, 1, 0)
    check('retry', 'no endpoint-a admission before cooldown equality', retry.claim(1999) is None)
    retry.subscribe('other', 's', first['endpoint'])
    retry.enqueue('other', 'e', 'hello', 1)
    isolated = retry.claim(1)
    check('retry', 'cooldown is tenant scoped', isolated['tenant'] == 'other')
    retry.finish(isolated, 200, 1, 0)
    after = retry.claim(2000)
    check('retry', 'endpoint resumes at cooldown equality', after['endpoint'] == first['endpoint'])
    retry.finish(after, 503, 2000, 100)
    check('retry', 'retry due uses completion time plus selected jitter', retry.inspect('t', after['id'])['due'] == 2100)
    terminal = queue('terminal')
    terminal.subscribe('t', 's', 'a')
    terminal.enqueue('t', 'e', 'hello', 0)
    statuses = [503, 408, None]
    for number, status in enumerate(statuses):
        attempt = terminal.claim(number*1000)
        terminal.finish(attempt, status, number*1000, 500)
    check('retry', 'retryable failures stop after three claims', terminal.inspect('t', attempt['id'])['status'] == 'failed')
    check('retry', 'terminal retries do not loop forever', terminal.claim(10000) is None)
    check('retry', 'unknown transport is recorded separately', terminal.db.execute('SELECT outcome FROM attempts WHERE number=3').fetchone()[0] == 'transport_unknown')
    redirect = queue('redirect')
    redirect.subscribe('t', 's', 'a')
    redirect.enqueue('t', 'e', 'hello', 0)
    redirect_job = redirect.claim(0)
    redirect.finish(redirect_job, 302, 0, 0)
    check('retry', 'redirect response is permanent and not followed', redirect.inspect('t', redirect_job['id'])['status'] == 'failed')
    observations['retry'] = {'retryable_statuses':[408,429,'5xx','transport_unknown'],
        'permanent_examples':[302,400], 'maximum_attempts':3,
        'first_attempt_jitter_cap_ms':500, 'second_attempt_jitter_cap_ms':1000,
        '429_hint_ms':2000, 'same_endpoint_blocked_before_ms':2000,
        'other_endpoint_and_tenant_continue':True, 'dead_letter_state':'failed'}

    receiver_path = directory/'receiver.sqlite'
    initialize(receiver_path)
    controls, server_clock = {}, [0]
    secret = b'published-lesson-secret-a'
    receiver_registry = {'/hooks/a':('a','t',secret), '/hooks/b':('b','t',b'published-lesson-secret-b')}
    api = server(receiver_path, receiver_registry, lambda:server_clock[0], controls)
    api_thread = Thread(target=api.serve_forever, name='s2-owned-receiver')
    api_thread.start()
    ports.append(api.server_port)
    registry = {('t','a'):(api.server_port,'/hooks/a',secret), ('t','b'):(api.server_port,'/hooks/b',b'published-lesson-secret-b')}
    raw = envelope('t', 'signed', 'R\u00e9sum\u00e9 reminder')
    def request(delivery='signed-delivery', body=raw, stamp='0', signature=None, path='/hooks/a', extra=None):
        headers = {'X-Lesson-Delivery':delivery, 'X-Lesson-Timestamp':stamp,
            'X-Lesson-Signature':signature if signature is not None else sign(secret, stamp, delivery, body)}
        headers.update(extra or {})
        connection = HTTPConnection('127.0.0.1', api.server_port, timeout=2)
        try:
            connection.request('POST', path, body=body, headers=headers)
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()
    check('http', 'valid signed unicode bytes accepted', request() == 200)
    check('http', 'duplicate signed delivery acknowledged again', request() == 200)
    check('http', 'duplicate produces one receiver effect', rows(receiver_path, "SELECT count(*) FROM effects WHERE delivery='signed-delivery'")[0][0] == 1)
    check('http', 'tampered raw body fails HMAC before processing', request(body=raw+b' ', signature=sign(secret, '0', 'signed-delivery', raw)) == 401)
    check('http', 'wrong signing secret fails', request(signature='0'*64) == 401)
    check('http', 'changed delivery header is signed', request(delivery='different', signature=sign(secret, '0', 'signed-delivery', raw)) == 401)
    server_clock[0] = 31000
    check('http', '31-second old signature rejected', request(stamp='0') == 401)
    server_clock[0] = 30000
    check('http', '30-second tolerance equality accepted', request(stamp='0') == 200)
    server_clock[0] = 0
    check('http', '31-second future signature rejected', request(stamp='31') == 401)
    check('http', 'nonnumeric timestamp rejected', request(stamp='bad') == 401)
    check('http', 'other endpoint secret cannot be reused', request(path='/hooks/b') == 401)
    check('http', 'signed tenant mismatch rejected', request(delivery='wrong-tenant', body=envelope('other','e','hello')) == 400)
    check('http', 'signed malformed JSON rejected', request(body=b'{') == 400)
    check('http', 'oversized declared body rejected before reading', request(body=b'', extra={'Content-Length':'4097'}) == 400)
    check('http', 'unknown endpoint is 404', request(path='/unknown') == 404)
    check('http', 'same signed delivery with changed payload rejected', request(body=envelope('t','changed','hello')) == 400)
    before_effects = rows(receiver_path, 'SELECT count(*) FROM effects')[0][0]
    check('http', 'rejected inputs did not add receiver effects', before_effects == 1)
    # Force effect insert failure to prove receipt and effect share a transaction.
    db = sqlite3.connect(receiver_path)
    db.execute("CREATE TRIGGER inject_effect_failure BEFORE INSERT ON effects WHEN NEW.delivery='rollback' BEGIN SELECT RAISE(ABORT,'injected'); END")
    db.commit()
    db.close()
    check('http', 'receiver DB fault yields 503', request(delivery='rollback') == 503)
    check('http', 'receiver fault rolls back receipt', not rows(receiver_path, "SELECT 1 FROM receipts WHERE delivery='rollback'"))
    db = sqlite3.connect(receiver_path)
    db.execute('DROP TRIGGER inject_effect_failure')
    db.close()
    check('http', 'retry after rollback can apply effect', request(delivery='rollback') == 200)
    with ThreadPoolExecutor(max_workers=2) as pool:
        receiver_race = list(pool.map(lambda _:request(delivery='racing-receiver'), range(2)))
    check('http', 'concurrent receiver duplicates both acknowledged', receiver_race == [200,200])
    check('http', 'concurrent receiver duplicates apply one effect', rows(receiver_path, "SELECT count(*) FROM effects WHERE delivery='racing-receiver'")[0][0] == 1)

    network = queue('network')
    network.subscribe('t','s','a')
    network.enqueue('t','lost-ack','hello',0)
    controls['a'] = ['drop_after_commit',200]
    first_send = run_once(network, registry, 0, jitter=lambda cap:500)
    check('network', 'real connection closes without status after effect commits', first_send['status'] is None)
    check('network', 'lost acknowledgement schedules retry', network.inspect('t',first_send['delivery_id'])['status'] == 'pending')
    check('network', 'receiver effect exists before retry', rows(receiver_path, 'SELECT count(*) FROM effects WHERE delivery=?', (first_send['delivery_id'],))[0][0] == 1)
    check('network', 'retry is not claimable before due', network.claim(499) is None)
    server_clock[0] = 500
    second_send = run_once(network, registry, 500, jitter=lambda cap:0)
    check('network', 'retry uses same stable delivery identity', second_send['delivery_id'] == first_send['delivery_id'])
    check('network', 'retry acknowledged and sender succeeds', second_send['status'] == 200 and network.inspect('t',first_send['delivery_id'])['status'] == 'succeeded')
    check('network', 'two HTTP attempts produce one transactional effect', rows(receiver_path, 'SELECT count(*) FROM effects WHERE delivery=?', (first_send['delivery_id'],))[0][0] == 1)
    check('network', 'both ambiguous and successful attempts persisted', [row[0] for row in network.db.execute('SELECT outcome FROM attempts ORDER BY number')] == ['transport_unknown','200'])
    throttled = queue('network-429')
    throttled.subscribe('t','s','a')
    throttled.enqueue('t','limited','hello',500)
    controls['a'] = [429,200]
    limited_send = run_once(throttled,registry,500,jitter=lambda cap:10)
    check('network', 'actual HTTP 429 parsed as delay-seconds', limited_send['status'] == 429 and limited_send['retry_after_ms'] == 2000)
    check('network', 'HTTP hint determines durable due time', throttled.inspect('t',limited_send['delivery_id'])['due'] == 2500)
    check('network', 'provider cooldown blocks early real retry', throttled.claim(2499) is None)
    server_clock[0] = 2500
    check('network', 'real delivery resumes after provider delay', run_once(throttled,registry,2500,jitter=lambda cap:0)['status'] == 200)
    order = queue('ordering')
    order.subscribe('t','s','a')
    order.enqueue('t','earlier','earlier',2500)
    controls['a'] = [503,200,200]
    earlier = run_once(order,registry,2500,jitter=lambda cap:500)
    order.enqueue('t','later','later',2501)
    server_clock[0] = 2501
    later = run_once(order,registry,2501,jitter=lambda cap:0)
    server_clock[0] = 3000
    run_once(order,registry,3000,jitter=lambda cap:0)
    observed_order = [row[0] for row in rows(receiver_path,'SELECT message FROM effects WHERE delivery IN (?,?) ORDER BY rowid',(earlier['delivery_id'],later['delivery_id']))]
    check('network', 'retry allows a later event to arrive first', observed_order == ['later','earlier'])
    check('network', 'idle worker makes no HTTP call', run_once(order,registry,4000) is None)
    observations['http_contract'] = {'valid_and_duplicate_statuses':[200,200],
        'tampered_bytes_status':401, 'old_signature_status':401,
        'signed_wrong_tenant_status':400, 'receiver_transaction_rollback_tested':True,
        'concurrent_duplicate_requests':2, 'concurrent_duplicate_effects':1,
        'production_vendor_protocol_implemented':False}
    observations['lost_ack_and_ordering'] = {'first_HTTP_outcome':'transport_unknown',
        'receiver_effects_before_retry':1, 'second_HTTP_status':second_send['status'],
        'attempts':2, 'stable_delivery_id':True, 'receiver_effects_after_retry':1,
        'sender_final_state':'succeeded', 'actual_429_retry_after_ms':limited_send['retry_after_ms'],
        'observed_independent_event_order':observed_order, 'human_read_or_inbox_delivery_proven':False}
    estimated = calculate()
    for name, expected in [('deliveries_per_day',400000),('attempts_per_day',440000),
        ('average_attempts_per_second',5.093),('hypothetical_peak_attempts_per_second',101.852),
        ('planning_mean_inflight_at_peak',20.37),('backlog_after_one_hour_at_100_deliveries_per_second',360000),
        ('drain_seconds_at_150_service_and_100_new_per_second',7200)]:
        check('estimates',name,estimated[name] == expected)
    check('estimates','workload is not a capacity measurement',not estimated['measured_capacity'])
    observations['estimates'] = estimated
finally:
    if api is not None:
        api.shutdown()
        api.server_close()
    if api_thread is not None:
        api_thread.join(timeout=5)
        assert not api_thread.is_alive()
    for item in queues:
        item.close()
    temporary.cleanup()

closed = True
for item in queues:
    try:
        item.db.execute('SELECT 1')
    except sqlite3.ProgrammingError:
        continue
    closed = False
check('cleanup','all tracked queue connections closed',closed)
check('cleanup','owned database directory removed',not directory.exists())
for port in ports:
    with socket.socket() as probe:
        probe.settimeout(1)
        check('cleanup','owned receiver listener closed',probe.connect_ex(('127.0.0.1',port)) != 0)
check('cleanup','port 3000 unused',3000 not in ports)
assert len({(item['group'],item['name']) for item in checks}) == len(checks)
proof = {'label':'S2','verified_date':'2026-10-17','python':platform.python_version(),
    'sqlite':sqlite3.sqlite_version,'os':platform.system(), 'total':len(checks),
    'counts':dict(Counter(item['group'] for item in checks)), 'checks':checks, 'observations':observations,
    'cleanup':{'fixture_ports':ports,'temporary_database_directory_removed':not directory.exists(),
        'sqlite_connections_closed':closed,'temporary_http_servers_closed':True,
        'concurrent_worker_calls_completed':6,'port_3000_used':False},
    'scope':'Local Python/SQLite durable queue plus owned signed loopback HTTP receiver. No external messages, SMTP/SMS/push integration, vendor account, broker, production authentication/TLS, crash-power-loss, distributed clock/failover or load benchmark. At-least-once attempts are bounded; receiver effect dedupe is a local transactional record, not universal exactly-once delivery.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':proof['total'],'counts':proof['counts'],'cleanup':proof['cleanup']},indent=2))
