"""Exercise actual state transitions, independent connections and loopback HTTP."""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Thread
import json
import platform
import socket
import sqlite3
import sys
from algorithms import FixedWindow, SlidingCounter, SlidingLog, compare
from estimates import calculate
from http_api import Context, server
from limiter import Policy, PolicyConflict, Store, StoreFull, scope_key

BASE = Path(__file__).resolve().parent
checks, observations, stores, ports = [], {}, [], []


def check(group, name, condition):
    assert condition, (group, name)
    checks.append({'group': group, 'name': name, 'passed': True})


def raises(group, name, expected, action):
    try:
        action()
    except expected:
        check(group, name, True)
    else:
        raise AssertionError(name)


def open_store(path, **kwargs):
    store = Store(path, **kwargs)
    stores.append(store)
    return store


observations['algorithms'] = compare()
trace = observations['algorithms']
check('algorithms', 'fixed window admits six across one-ms boundary', sum(trace['fixed'][:6]) == 6)
check('algorithms', 'sliding log rejects boundary burst', trace['sliding_log'][3:6] == [False]*3)
check('algorithms', 'exact sliding interval releases equality cutoff', trace['sliding_log'][-1])
check('algorithms', 'sliding counter rejects immediate new-window burst', trace['sliding_counter'][3:6] == [False]*3)
exact, approximate = SlidingLog(3, 1000), SlidingCounter(3, 1000)
for _ in range(3):
    exact.allow(999)
    approximate.allow(999)
counter_example = [approximate.allow(1500), exact.allow(1500)]
check('algorithms', 'weighted approximation can admit while exact log denies', counter_example == [True, False])
observations['algorithms']['counterexample_at_1500'] = {'counter_allowed': counter_example[0], 'exact_log_allowed': counter_example[1]}
gap = SlidingCounter(2, 1000)
gap.allow(0)
check('algorithms', 'skipped windows discard stale previous traffic', gap.allow(3000) and gap.previous == 0)
log = SlidingLog(2, 1000)
log.allow(0)
log.allow(0)
check('algorithms', 'denial does not grow exact log', not log.allow(1) and len(log.events) == 2)
check('algorithms', 'log prunes before admitting', log.allow(1000) and list(log.events) == [1000])

temporary = TemporaryDirectory(prefix='placement-s1-verify-')
directory = Path(temporary.name)
api, api_thread = None, None
try:
    store = open_store(directory/'quota.sqlite')
    policy = Policy(3, 1)
    def decide(subject='alice', now=0, cost=1, chosen=policy, tenant='a', route='read'):
        return store.decide(tenant, subject, route, chosen, now, cost)

    for name, action in [
        ('zero capacity', lambda: Policy(0, 1)),
        ('boolean capacity', lambda: Policy(True, 1)),
        ('fractional rate', lambda: Policy(3, 0.5)),
        ('zero rate', lambda: Policy(3, 0)),
        ('unbounded rate', lambda: Policy(3, 1000001)),
        ('empty identity', lambda: scope_key('a', '', 'read')),
        ('control identity', lambda: scope_key('a', 'alice\n', 'read')),
        ('unicode identity', lambda: scope_key('a', '\u00e9', 'read')),
        ('oversized route', lambda: scope_key('a', 'alice', 'r'*81)),
        ('negative time', lambda: decide(now=-1)),
        ('boolean time', lambda: decide(now=True)),
        ('zero cost', lambda: decide(cost=0)),
        ('cost above burst', lambda: decide(cost=4)),
        ('fractional cost', lambda: decide(cost=1.5))]:
        raises('validation', name, ValueError, action)
    check('validation', 'rejected inputs create no buckets', store.db.execute('SELECT count(*) FROM buckets').fetchone()[0] == 0)
    check('validation', 'tuple key avoids delimiter collision', scope_key('a:b', 'c', 'read') != scope_key('a', 'b:c', 'read'))

    initial = [decide() for _ in range(4)]
    check('bucket', 'initial burst capped at capacity', [d.allowed for d in initial] == [True, True, True, False])
    check('bucket', 'remaining counts whole post-charge tokens', [d.remaining for d in initial] == [2, 1, 0, 0])
    check('bucket', 'empty bucket retry is one second', initial[-1].retry_ms == 1000)
    partial = decide(now=999)
    check('bucket', 'partial refill does not round up', not partial.allowed and partial.retry_ms == 1)
    equality = decide(now=1000)
    check('bucket', 'exact refill equality permits one request', equality.allowed and equality.remaining == 0)
    rollback = decide(now=500)
    check('bucket', 'backward clock does not create credit', not rollback.allowed and rollback.effective_ms == 1000)
    check('bucket', 'backward-clock retry includes catch-up interval', rollback.retry_ms == 1500)
    resumed = decide(now=2000)
    check('bucket', 'refill resumes at previous high-water plus interval', resumed.allowed)
    far = decide(now=10**12)
    check('bucket', 'large forward jump caps credit', far.allowed and far.remaining == 2)
    weighted = decide(subject='weighted', chosen=Policy(5, 2), cost=3)
    check('bucket', 'weighted request debits server-selected cost', weighted.allowed and weighted.remaining == 2)
    denied = decide(subject='weighted', chosen=Policy(5, 2), cost=3)
    check('bucket', 'weighted denial computes missing credit', not denied.allowed and denied.retry_ms == 500)
    weighted_after = decide(subject='weighted', chosen=Policy(5, 2), cost=3, now=500)
    check('bucket', 'weighted cost refills using configured rate', weighted_after.allowed and weighted_after.remaining == 0)
    tiny = decide(subject='fraction', chosen=Policy(1, 3))
    fraction = decide(subject='fraction', chosen=Policy(1, 3), now=333)
    check('bucket', 'integer refill retains 999 milli-tokens', not fraction.allowed and fraction.retry_ms == 1)
    check('bucket', 'ceil retry reaches sufficient credit', decide(subject='fraction', chosen=Policy(1, 3), now=334).allowed)
    observations['bucket'] = {'initial': [d.json() for d in initial],
        'at_999_ms': partial.json(), 'at_1000_ms': equality.json(),
        'clock_back_to_500_ms': rollback.json(), 'weighted_denial': denied.json(),
        'forward_jump_capped': far.json()}

    # Isolate clock timelines by scope; skew between callers is a documented boundary.
    scope = open_store(directory/'scope.sqlite')
    p = Policy(1, 1)
    check('scope_lifecycle', 'first scoped admission succeeds', scope.decide('t1', 'alice', 'read', p, 0).allowed)
    check('scope_lifecycle', 'same identity shares exhausted quota', not scope.decide('t1', 'alice', 'read', p, 0).allowed)
    check('scope_lifecycle', 'subject isolation', scope.decide('t1', 'bob', 'read', p, 0).allowed)
    check('scope_lifecycle', 'tenant isolation', scope.decide('t2', 'alice', 'read', p, 0).allowed)
    check('scope_lifecycle', 'route-class isolation', scope.decide('t1', 'alice', 'write', p, 0).allowed)
    before = [tuple(row) for row in scope.db.execute('SELECT * FROM buckets ORDER BY scope')]
    raises('scope_lifecycle', 'active policy mismatch requires migration', PolicyConflict,
           lambda: scope.decide('t1', 'alice', 'read', Policy(2, 1), 0))
    check('scope_lifecycle', 'policy rejection rolls back state', before == [tuple(row) for row in scope.db.execute('SELECT * FROM buckets ORDER BY scope')])
    scope.close()
    reopened = open_store(directory/'scope.sqlite')
    check('scope_lifecycle', 'close/reopen retains depleted bucket', not reopened.decide('t1', 'alice', 'read', p, 0).allowed)
    capped = open_store(directory/'capped.sqlite', max_keys=1)
    capped.decide('t', 'a', 'read', Policy(2, 1), 0)
    capped.decide('t', 'a', 'read', Policy(2, 1), 0)
    raises('scope_lifecycle', 'new active scope rejected at cardinality cap', StoreFull,
           lambda: capped.decide('t', 'b', 'read', Policy(2, 1), 1))
    check('scope_lifecycle', 'existing depleted scope is not evicted for new key', not capped.decide('t', 'a', 'read', Policy(2, 1), 1).allowed)
    # Last denied decision above sets expiry=2001; no reset before safe full refill.
    raises('scope_lifecycle', 'cleanup does not evict before conservative idle expiry', StoreFull,
           lambda: capped.decide('t', 'b', 'read', Policy(2, 1), 2000))
    admitted_new = capped.decide('t', 'b', 'read', Policy(2, 1), 2001)
    check('scope_lifecycle', 'idle cleanup frees scope at equality', admitted_new.allowed)
    check('scope_lifecycle', 'physical bucket count stays bounded', capped.db.execute('SELECT count(*) FROM buckets').fetchone()[0] == 1)
    observations['scope_lifecycle'] = {'scope_parts': ['trusted tenant', 'authenticated subject', 'server route class'],
        'reopen_preserves_quota': True, 'active_policy_change_rejected': True,
        'max_keys_demonstrated': 1, 'safe_idle_cleanup_ms': 2001,
        'new_scope_after_cleanup': admitted_new.json()}

    # Deliberately broken read/check/write: both workers see the one remaining slot.
    broken_path = directory/'broken.sqlite'
    seed = sqlite3.connect(broken_path)
    seed.execute('CREATE TABLE counter(value INTEGER)')
    seed.execute('INSERT INTO counter VALUES(0)')
    seed.commit()
    seed.close()
    barrier = Barrier(2)
    def unsafe(_):
        db = sqlite3.connect(broken_path, timeout=2)
        try:
            old = db.execute('SELECT value FROM counter').fetchone()[0]
            barrier.wait(timeout=5)
            if old < 1:
                db.execute('UPDATE counter SET value=?', (old+1,))
                db.commit()
                return True
            return False
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        unsafe_results = list(pool.map(unsafe, range(2)))
    check('concurrency', 'broken precheck admits both final-slot contenders', sum(unsafe_results) == 2)
    db = sqlite3.connect(broken_path)
    lost = db.execute('SELECT value FROM counter').fetchone()[0]
    db.close()
    check('concurrency', 'lost update hides over-admission', lost == 1)
    race_path = directory/'race.sqlite'
    seed_store = open_store(race_path)
    seed_store.close()
    barrier = Barrier(2)
    def atomic(_):
        worker = Store(race_path)
        try:
            barrier.wait(timeout=5)
            return worker.decide('t', 'same-user', 'write', Policy(1, 1), 0).allowed
        finally:
            worker.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        safe_results = list(pool.map(atomic, range(2)))
    check('concurrency', 'atomic authority admits exactly one contender', sum(safe_results) == 1)
    race_after = open_store(race_path)
    check('concurrency', 'winning charge persists for next caller', not race_after.decide('t', 'same-user', 'write', Policy(1, 1), 0).allowed)
    lock_store = open_store(race_path)
    lock_store.db.execute('BEGIN IMMEDIATE')
    try:
        raises('concurrency', 'real writer contention reaches bounded dependency failure', sqlite3.OperationalError,
               lambda: race_after.decide('t', 'other-user', 'write', Policy(1, 1), 0))
    finally:
        lock_store.db.execute('ROLLBACK')
    check('concurrency', 'store recovers after writer lock release', race_after.decide('t', 'other-user', 'write', Policy(1, 1), 0).allowed)
    observations['concurrency'] = {'independent_worker_calls': 4,
        'unsafe_admitted': sum(unsafe_results), 'unsafe_persisted_count': lost,
        'atomic_admitted': sum(safe_results), 'atomic_denied': safe_results.count(False),
        'real_lock_timeout_observed': True, 'winner_order_assumed': False}

    # Two fresh local authorities multiply a nominal shared quota.
    local_a, local_b = open_store(directory/'local-a.sqlite'), open_store(directory/'local-b.sqlite')
    local_results = [s.decide('t', 'u', 'r', Policy(1, 1), 0).allowed for s in (local_a, local_b)]
    check('concurrency', 'independent local stores double global burst', sum(local_results) == 2)

    clock = [0]
    http_path = directory/'http.sqlite'
    schema = open_store(http_path)
    schema.close()
    context = Context(http_path, lambda: clock[0])
    api = server(context)
    ports.append(api.server_port)
    api_thread = Thread(target=api.serve_forever, name='s1-owned-http')
    api_thread.start()
    def request(method='GET', path='/api/read', token='lesson-alice', extra=None, body=None):
        conn = HTTPConnection('127.0.0.1', api.server_port, timeout=3)
        headers = {'Authorization': 'Bearer '+token} if token else {}
        headers.update(extra or {})
        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            conn.close()
    check('http', 'unknown route returns 404', request(path='/other')[0] == 404)
    check('http', 'missing identity returns 401', request(token='')[0] == 401)
    check('http', 'unknown identity returns 401', request(token='forged')[0] == 401)
    check('http', 'unexpected body rejected before quota', request('POST', '/api/write', body='x')[0] == 400)
    attempts = [request() for _ in range(4)]
    check('http', 'real HTTP burst has three successes then 429', [x[0] for x in attempts] == [200, 200, 200, 429])
    last = attempts[-1]
    check('http', '429 carries integer Retry-After', last[1].get('Retry-After') == '1')
    check('http', '429 is explicitly no-store', last[1].get('Cache-Control') == 'no-store')
    check('http', 'successful response is also no-store', attempts[0][1].get('Cache-Control') == 'no-store')
    check('http', 'remaining is post-charge informational value', [x[1].get('X-Lesson-Quota-Remaining') for x in attempts] == ['2', '1', '0', '0'])
    check('http', 'rotated credential cannot reset stable subject quota', request(token='lesson-alice-rotated')[0] == 429)
    check('http', 'untrusted forwarded identity cannot reset quota', request(extra={'X-Forwarded-For': '198.51.100.4', 'X-Tenant': 'new', 'X-Cost': '0'})[0] == 429)
    check('http', 'another subject has own quota', request(token='lesson-bob')[0] == 200)
    check('http', 'another tenant has own quota', request(token='lesson-other-tenant')[0] == 200)
    check('http', 'query string does not create arbitrary scope', request(path='/api/read?fresh=1')[0] == 404)
    clock[0] = 999
    check('http', 'subsecond retry rounds up', request()[1].get('Retry-After') == '1')
    clock[0] = 1000
    check('http', 'request resumes after exact refill', request()[0] == 200)
    context.fail_work = True
    work_failure = request('POST', '/api/write')
    check('http', 'downstream failure follows charged admission', work_failure[0] == 500 and work_failure[1].get('X-Lesson-Quota-Remaining') == '2')
    context.fail_work = False
    check('http', 'failed work was not automatically refunded', request('POST', '/api/write')[1].get('X-Lesson-Quota-Remaining') == '1')
    context.unavailable = True
    open_result, closed_result = request(), request('POST', '/api/write')
    check('http', 'read route chosen fail-open continues work', open_result[0] == 200)
    check('http', 'fail-open response exposes degraded mode', open_result[1].get('X-Lesson-Quota') == 'degraded-open')
    check('http', 'fail-open does not invent remaining quota', 'X-Lesson-Quota-Remaining' not in open_result[1])
    check('http', 'write route chosen fail-closed returns 503', closed_result[0] == 503)
    check('http', 'outage is not misreported as 429', closed_result[2]['error'] == 'quota authority unavailable')
    context.unavailable = False
    check('http', 'recovered authority retains previous exhausted read state', request()[0] == 429)
    # Real DB lock, rather than only injection, exercises HTTP dependency fallback.
    locker = open_store(http_path)
    locker.db.execute('BEGIN IMMEDIATE')
    try:
        check('http', 'real contention triggers read fallback', request()[1].get('X-Lesson-Quota') == 'degraded-open')
        check('http', 'real contention triggers write 503', request('POST', '/api/write')[0] == 503)
    finally:
        locker.db.execute('ROLLBACK')
    observations['http_contract'] = {'burst_statuses': [x[0] for x in attempts],
        'denied_retry_after_seconds': last[1]['Retry-After'],
        'denied_cache_control': last[1]['Cache-Control'],
        'read_outage': {'status': open_result[0], 'mode': open_result[1]['X-Lesson-Quota']},
        'write_outage': {'status': closed_result[0], 'body': closed_result[2]},
        'failed_work_remaining': work_failure[1]['X-Lesson-Quota-Remaining'],
        'real_lock_fallback_tested': True, 'client_time_or_cost_trusted': False}

    calculated = calculate()
    for name, expected in [('average_requests_per_second', 100), ('hypothetical_peak_decisions_per_second', 1000),
                           ('logical_bucket_storage_MB', 128), ('three_replicated_logical_copies_MB', 384),
                           ('sliding_log_event_payload_MB', 96), ('possible_aggregate_initial_burst', 120)]:
        check('estimates', name, calculated[name] == expected)
    check('estimates', 'calculation makes no throughput claim', calculated['measured_capacity'] is False)
    observations['estimates'] = calculated
finally:
    if api is not None:
        api.shutdown()
        api.server_close()
    if api_thread is not None:
        api_thread.join(timeout=5)
        assert not api_thread.is_alive()
    for store in stores:
        store.close()
    temporary.cleanup()

closed_connections = True
for store in stores:
    try:
        store.db.execute('SELECT 1')
    except sqlite3.ProgrammingError:
        continue
    closed_connections = False
check('cleanup', 'all tracked SQLite connections closed', closed_connections)
check('cleanup', 'owned temporary directory removed', not directory.exists())
for port in ports:
    with socket.socket() as probe:
        probe.settimeout(1)
        check('cleanup', 'owned HTTP listener closed', probe.connect_ex(('127.0.0.1', port)) != 0)
check('cleanup', 'port 3000 not used', 3000 not in ports)
counts = dict(Counter(item['group'] for item in checks))
assert len({(item['group'], item['name']) for item in checks}) == len(checks)
proof = {'label': 'S1', 'verified_date': '2026-10-17', 'python': platform.python_version(),
    'sqlite': sqlite3.sqlite_version, 'os': platform.system(), 'counts': counts,
    'total': len(checks), 'checks': checks, 'observations': observations,
    'cleanup': {'fixture_ports': ports, 'temporary_database_directory_removed': not directory.exists(),
        'sqlite_connections_closed': closed_connections, 'temporary_http_servers_closed': True,
        'concurrent_worker_calls_completed': 4, 'port_3000_used': False},
    'scope': 'Local Python/SQLite and loopback HTTP. No Redis, production authentication/TLS, distributed clock authority, multi-region failover or capacity benchmark. Denials do not charge tokens; successful admissions charge even if work fails. Fail-open intentionally relaxes enforcement.'}
(BASE/'verification-results.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'total': len(checks), 'counts': counts, 'cleanup': proof['cleanup']}, indent=2))
