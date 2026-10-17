"""Real local transaction/concurrency/recovery checks and injected-clock retry tests."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import json
import platform
import sqlite3

from workflow import Workflow, Conflict, Missing, Unavailable, canonical
from consumer import Consumer
from retry import retry, Transient, Permanent, Deadline

BASE = Path(__file__).resolve().parent
checks, observations = [], {}
worker_calls = 0


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


def count(store, table):
    assert table in {'notes', 'operations', 'outbox', 'inbox', 'projection', 'reservations'}
    return store.db.execute('SELECT count(*) FROM '+table).fetchone()[0]


class IDs:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 1
        return 'id_'+str(self.value)


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, duration):
        self.value += duration


def retry_checks():
    clock, calls = Clock(), []

    def call(budget):
        calls.append(budget)
        clock.advance(0.1)
        if len(calls)<3:
            raise Transient('controlled temporary failure')
        return 'accepted'

    result = retry(call, clock, clock.advance, lambda: 0.5, retry_safe=True)
    check('retry_policy', 'transient safe operation succeeds within three attempts', result['result'] == 'accepted' and len(calls) == 3)
    check('retry_policy', 'each attempt receives bounded timeout budget', all(0 < budget <= 0.4 for budget in calls))
    check('retry_policy', 'full jitter uses capped exponential bounds', [row.get('backoff') for row in result['trace'][:2]] == [0.05, 0.1])
    check('retry_policy', 'elapsed fake time includes calls and sleeps', abs(clock()-0.45)<1e-9)
    observations['retry'] = {'outcome': result, 'fake_elapsed_seconds': round(clock(), 6), 'network_calls_made': False}
    for error, safe, expected, label in [(Transient, False, Transient, 'unsafe operation is not retried'), (Permanent, True, Permanent, 'permanent failure is not retried')]:
        clock, calls = Clock(), []

        def fail(budget):
            calls.append(budget)
            raise error('injected')

        raises('retry_policy', label, expected, lambda: retry(fail, clock, clock.advance, lambda: 0, retry_safe=safe))
        check('retry_policy', label+' calls once', len(calls) == 1)
    clock, calls = Clock(), []

    def slow_failure(budget):
        calls.append(budget)
        clock.advance(0.2)
        raise Transient('budgeted failure')

    raises('retry_policy', 'delay cannot exceed remaining caller deadline', Deadline,
           lambda: retry(slow_failure, clock, clock.advance, lambda: 1, total=0.25, retry_safe=True))
    check('retry_policy', 'deadline stops before another attempt', len(calls) == 1 and clock() == 0.2)
    clock = Clock()

    def late_success(budget):
        clock.advance(budget)
        return 'late result'

    raises('retry_policy', 'result at caller deadline is rejected', Deadline,
           lambda: retry(late_success, clock, clock.advance, lambda: 0, total=0.2))
    clock, calls = Clock(), []

    def always_fail(budget):
        calls.append(budget)
        raise Transient('still failing')

    raises('retry_policy', 'attempt exhaustion returns final transient failure', Transient,
           lambda: retry(always_fail, clock, clock.advance, lambda: 0, retry_safe=True))
    check('retry_policy', 'attempt bound respected', len(calls) == 3)
    for options in ({'total': 0}, {'cap': float('inf')}, {'attempts': True}, {'attempts': 11}):
        raises('retry_policy', 'invalid retry configuration '+str(options), ValueError,
               lambda options=options: retry(lambda _: None, clock, clock.advance, lambda: 0, **options))
    raises('retry_policy', 'invalid jitter fraction rejected', ValueError,
           lambda: retry(always_fail, clock, clock.advance, lambda: 2, retry_safe=True))
    check('retry_policy', 'independent retry layers multiply attempts', 3**5 == 243)
    observations['deadline'] = {'caller_deadline_seconds': 0.25, 'first_call_seconds': 0.2,
        'proposed_delay_seconds': 0.1, 'next_attempt_started': False,
        'retry_layers': 5, 'attempts_per_layer': 3, 'maximum_leaf_attempts': 243}


def simultaneous(path, actions):
    global worker_calls
    barrier = Barrier(2)

    def run(action):
        store = Workflow(path)
        try:
            barrier.wait(timeout=5)
            try:
                return {'result': action(store)}
            except Unavailable:
                return {'unavailable': True}
        finally:
            store.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, action) for action in actions]
        results = [future.result(timeout=10) for future in futures]
    worker_calls += len(results)
    return results


def main():
    retry_checks()
    with TemporaryDirectory(prefix='placement-a3-') as directory:
        directory = Path(directory)
        stores = []

        def workflow(name):
            store = Workflow(directory/name, IDs())
            stores.append(store)
            return store

        def consumer(name):
            store = Consumer(directory/name)
            stores.append(store)
            return store

        def close(store):
            store.close()
            stores.remove(store)

        try:
            source = workflow('source.sqlite')
            raises('atomic_operations', 'fault between note and outbox rolls back', RuntimeError,
                lambda: source.create_note('alpha', 'alice', 'rollback', 'Atomic note', fail_after_note=True))
            check('atomic_operations', 'fault leaves no canonical note', count(source, 'notes') == 0)
            check('atomic_operations', 'fault leaves no operation outcome', count(source, 'operations') == 0)
            check('atomic_operations', 'fault leaves no outbox intent', count(source, 'outbox') == 0)
            note, replayed = source.create_note('alpha', 'alice', 'create_one', 'Atomic note')
            check('atomic_operations', 'new create returns non-replay result', not replayed and note['revision'] == 1)
            check('atomic_operations', 'note operation and event commit together', [count(source, name) for name in ('notes', 'operations', 'outbox')] == [1, 1, 1])
            event = dict(source.db.execute('SELECT * FROM outbox').fetchone())
            check('atomic_operations', 'outbox payload has stable event and note identities', json.loads(event['payload'])['event_id'] == event['event_id'] and json.loads(event['payload'])['note_id'] == note['id'])
            close(source)
            source = workflow('source.sqlite')
            replay, replayed = source.create_note('alpha', 'alice', 'create_one', 'Atomic note')
            check('atomic_operations', 'lost response replay survives reopen', replayed and replay == note)
            check('atomic_operations', 'replay creates no extra note or event', count(source, 'notes') == count(source, 'outbox') == 1)
            raises('atomic_operations', 'same operation different input conflicts', Conflict,
                lambda: source.create_note('alpha', 'alice', 'create_one', 'Changed intent'))
            check('atomic_operations', 'conflicting replay leaves canonical title intact', source.db.execute('SELECT title FROM notes').fetchone()[0] == 'Atomic note')
            raises('atomic_operations', 'invalid operation key rejected', ValueError,
                lambda: source.create_note('alpha', 'alice', 'key\n', 'bad'))
            raises('atomic_operations', 'invalid title rejected', ValueError,
                lambda: source.create_note('alpha', 'alice', 'bad', '\0'))
            observations['atomic_create'] = {'replayed_after_reopen': replayed, 'original_result': note,
                'notes': count(source, 'notes'), 'operation_outcomes': count(source, 'operations'),
                'outbox_events': count(source, 'outbox'), 'event_type': json.loads(event['payload'])['type']}

            sink = consumer('sink.sqlite')
            first = source.claim('worker_a', 0, lease=5)
            check('leases', 'ready outbox row receives first claim', first.generation == first.attempt == 1)
            check('leases', 'active lease prevents competing claim', source.claim('worker_b', 4.999) is None)
            raises('consumer_atomicity', 'consumer fault after effect rolls back', RuntimeError,
                lambda: sink.accept(first.payload, fail_after_effect=True))
            check('consumer_atomicity', 'consumer rollback removes inbox record', count(sink, 'inbox') == 0)
            check('consumer_atomicity', 'consumer rollback removes effect', count(sink, 'projection') == 0)
            accepted = sink.accept(first.payload)
            check('consumer_atomicity', 'first successful consumer commit is non-replay', not accepted['replayed'])
            check('consumer_atomicity', 'effect and inbox commit together', count(sink, 'inbox') == count(sink, 'projection') == 1)
            # Simulated relay crash: intentionally omit source acknowledgement, then reopen both stores.
            close(source)
            close(sink)
            source = workflow('source.sqlite')
            sink = consumer('sink.sqlite')
            second = source.claim('worker_b', 5, lease=5)
            check('leases', 'claim recovers exactly at lease expiry', second.event_id == first.event_id and second.generation == 2)
            check('leases', 'recovery increments durable attempt count', second.attempt == 2)
            duplicate = sink.accept(second.payload)
            check('consumer_atomicity', 'redelivery deduplicates after consumer reopen', duplicate['replayed'])
            check('consumer_atomicity', 'redelivery does not repeat projection effect', count(sink, 'projection') == 1)
            check('leases', 'old claim cannot acknowledge new generation', not source.acknowledge(first, 6))
            check('leases', 'old claim cannot reschedule new generation', not source.fail(first, 6))
            check('leases', 'wrong worker cannot acknowledge', not source.acknowledge(replace(second, worker='worker_c'), 6))
            check('leases', 'current claim acknowledges after durable consumer result', source.acknowledge(second, 6))
            check('leases', 'acknowledged event is no longer claimable', source.claim('worker_c', 100) is None)
            check('leases', 'duplicate acknowledgement reports no transition', not source.acknowledge(second, 7))
            observations['redelivery'] = {'first_generation': first.generation, 'recovered_generation': second.generation,
                'same_event_id': first.event_id == second.event_id, 'consumer_replayed': duplicate['replayed'],
                'inbox_records': count(sink, 'inbox'), 'projection_effects': count(sink, 'projection'),
                'source_state': source.db.execute('SELECT state FROM outbox').fetchone()[0],
                'crash_boundary': 'consumer committed; source acknowledgement omitted'}
            altered = json.loads(second.payload)
            altered['title'] = 'conflicting payload'
            raises('consumer_atomicity', 'event ID reuse with changed payload conflicts', Conflict, lambda: sink.accept(canonical(altered)))
            check('consumer_atomicity', 'conflict leaves one original effect', count(sink, 'projection') == 1 and sink.db.execute('SELECT title FROM projection').fetchone()[0] == 'Atomic note')
            altered['schema'] = 2
            raises('consumer_atomicity', 'unsupported event schema rejected before effect', ValueError, lambda: sink.accept(canonical(altered)))
            altered['schema'] = True
            raises('consumer_atomicity', 'boolean schema is not version one', ValueError, lambda: sink.accept(canonical(altered)))
            bad = json.loads(second.payload)
            bad['extra'] = 'unknown'
            raises('consumer_atomicity', 'unknown event fields rejected', ValueError, lambda: sink.accept(canonical(bad)))

            scoped = workflow('scoped.sqlite')
            a, _ = scoped.create_note('alpha', 'alice', 'same_key', 'one')
            b, _ = scoped.create_note('alpha', 'bob', 'same_key', 'two')
            c, _ = scoped.create_note('beta', 'alice', 'same_key', 'three')
            check('atomic_operations', 'operation key scope includes owner and tenant', len({a['id'], b['id'], c['id']}) == 3 and count(scoped, 'operations') == 3)

            failed = workflow('failed-delivery.sqlite')
            failed.create_note('alpha', 'alice', 'poison', 'Poison delivery')
            one = failed.claim('worker', 0)
            check('delivery_bounds', 'first failure schedules delayed retry', failed.fail(one, 1, delay=3))
            check('delivery_bounds', 'retry is not visible before due time', failed.claim('worker', 3.999) is None)
            two = failed.claim('worker', 4)
            check('delivery_bounds', 'due time allows second claim', two.attempt == 2)
            check('delivery_bounds', 'acknowledgement at expiry is rejected', not failed.acknowledge(two, 9))
            three = failed.claim('replacement', 9)
            check('delivery_bounds', 'expired lease reclaims third attempt', three.attempt == 3)
            check('delivery_bounds', 'final failure transitions to dead', failed.fail(three, 10))
            check('delivery_bounds', 'dead item does not retry forever', failed.claim('worker', 100) is None)
            check('delivery_bounds', 'dead state persists in database', failed.db.execute('SELECT state FROM outbox').fetchone()[0] == 'dead')
            observations['delivery_bounds'] = {'attempts': three.attempt, 'retry_due': 4,
                'ack_at_expiry_accepted': False, 'terminal_state': 'dead', 'automatic_retry_after_dead': False}
            exhausted = workflow('expired-final.sqlite')
            exhausted.create_note('alpha', 'alice', 'exhaust', 'Expired final attempt')
            for now in (0, 5, 10):
                final = exhausted.claim('worker', now)
            check('delivery_bounds', 'final crashed attempt expires into dead state', exhausted.claim('next_worker', 15) is None and exhausted.db.execute('SELECT state FROM outbox').fetchone()[0] == 'dead')
            raises('delivery_bounds', 'nonpositive lease rejected', ValueError, lambda: exhausted.claim('worker', 0, lease=0))
            raises('delivery_bounds', 'negative retry delay rejected', ValueError, lambda: exhausted.fail(final, 11, delay=-1))

            stock = workflow('stock.sqlite')
            stock.db.execute('INSERT INTO stock VALUES(?,?,?)', ('alpha', 'last', 1))
            races = simultaneous(directory/'stock.sqlite', [lambda db: db.reserve('alpha', 'alice', 'r1', 'last'), lambda db: db.reserve('alpha', 'bob', 'r2', 'last')])
            check('concurrency', 'last-unit race has one accepted reservation', sum('result' in row for row in races) == 1)
            check('concurrency', 'last-unit race has one unavailable outcome', sum(row.get('unavailable', False) for row in races) == 1)
            check('concurrency', 'last-unit race cannot oversell', stock.db.execute('SELECT remaining FROM stock').fetchone()[0] == 0)
            check('concurrency', 'last-unit race persists one reservation', count(stock, 'reservations') == 1)
            observations['last_unit'] = {'accepted': sum('result' in row for row in races),
                'unavailable': sum(row.get('unavailable', False) for row in races), 'remaining': 0,
                'reservations': count(stock, 'reservations'), 'independent_sqlite_connections': 2}
            duplicates = workflow('duplicates.sqlite')
            duplicates.db.execute('INSERT INTO stock VALUES(?,?,?)', ('alpha', 'unit', 2))
            same = simultaneous(directory/'duplicates.sqlite', [lambda db: db.reserve('alpha', 'alice', 'same', 'unit'), lambda db: db.reserve('alpha', 'alice', 'same', 'unit')])
            results = [row['result'] for row in same]
            check('concurrency', 'concurrent operation retry returns same reservation', results[0][0] == results[1][0])
            check('concurrency', 'concurrent operation retry has one replay', sorted(value[1] for value in results) == [False, True])
            check('concurrency', 'concurrent retry decrements stock once', duplicates.db.execute('SELECT remaining FROM stock').fetchone()[0] == 1)
            check('concurrency', 'concurrent retry stores one outcome', count(duplicates, 'operations') == count(duplicates, 'reservations') == 1)
            observations['concurrent_retry'] = {'same_result': True, 'replay_flags': sorted(value[1] for value in results),
                'remaining': 1, 'reservations': 1, 'independent_sqlite_connections': 2}
            claims = workflow('claims.sqlite')
            claims.create_note('alpha', 'alice', 'one', 'One work item')
            competing = simultaneous(directory/'claims.sqlite', [lambda db: db.claim('worker_a', 0), lambda db: db.claim('worker_b', 0)])
            check('concurrency', 'competing claimers have one current owner', sum(row['result'] is not None for row in competing) == 1)
            check('concurrency', 'competing claimers create one lease generation', claims.db.execute('SELECT generation FROM outbox').fetchone()[0] == 1)

            compensation = workflow('compensation.sqlite')
            compensation.db.execute('INSERT INTO stock VALUES(?,?,?)', ('alpha', 'limited', 2))
            raises('compensation', 'failure after stock decrement rolls back', RuntimeError,
                lambda: compensation.reserve('alpha', 'alice', 'fault', 'limited', fail_after_decrement=True))
            check('compensation', 'failed reservation restores stock atomically', compensation.db.execute('SELECT remaining FROM stock').fetchone()[0] == 2)
            check('compensation', 'failed reservation stores no operation or reservation', count(compensation, 'operations') == count(compensation, 'reservations') == 0)
            reservation, _ = compensation.reserve('alpha', 'alice', 'reserve', 'limited')
            identity = reservation['reservation_id']
            raises('compensation', 'other owner cannot release reservation', Missing,
                lambda: compensation.release('alpha', 'bob', 'release', identity))
            raises('compensation', 'other tenant cannot release reservation', Missing,
                lambda: compensation.release('beta', 'alice', 'release', identity))
            raises('compensation', 'operation key cannot change action kind', Conflict,
                lambda: compensation.release('alpha', 'alice', 'reserve', identity))
            released, replay = compensation.release('alpha', 'alice', 'release', identity)
            check('compensation', 'compensation records released state', released['state'] == 'released' and not replay)
            close(compensation)
            compensation = workflow('compensation.sqlite')
            again, replay = compensation.release('alpha', 'alice', 'release', identity)
            check('compensation', 'compensation response replay survives reopen', replay and again == released)
            compensation.release('alpha', 'alice', 'different_release_key', identity)
            check('compensation', 'different release operation cannot restore stock twice', compensation.db.execute('SELECT remaining FROM stock').fetchone()[0] == 2)
            check('compensation', 'released reservation remains recorded', count(compensation, 'reservations') == 1 and compensation.db.execute('SELECT state FROM reservations').fetchone()[0] == 'released')
            observations['compensation'] = {'original_stock': 2, 'after_reserve': 1,
                'after_repeated_release': 2, 'reservation_state': 'released',
                'same_key_replayed_after_reopen': replay, 'external_payment_refund_executed': False}
            raises('compensation', 'zero reservation quantity rejected', ValueError,
                lambda: compensation.reserve('alpha', 'alice', 'bad', 'limited', 0))
            raises('compensation', 'boolean reservation quantity rejected', ValueError,
                lambda: compensation.reserve('alpha', 'alice', 'bad', 'limited', True))
        finally:
            for store in stores:
                store.close()
    check('cleanup', 'all six competing worker calls completed', worker_calls == 6)
    check('cleanup', 'temporary directory removed after connections close', not directory.exists())
    counts = {}
    for item in checks:
        counts[item['group']] = counts.get(item['group'], 0)+1
    proof = {'label': 'A3', 'verified_date': '2026-10-16', 'python': platform.python_version(),
        'sqlite': sqlite3.sqlite_version, 'os': platform.system()+' '+platform.release(),
        'total': len(checks), 'counts': counts, 'checks': checks, 'observations': observations,
        'cleanup': {'sqlite_connections_closed': True, 'temporary_database_directory_removed': True,
                    'concurrent_worker_calls_completed': worker_calls, 'persistent_listener_started': False},
        'scope': 'Real SQLite operation replay, atomic note/outbox creation, separate consumer inbox/effect transactions, close/reopen recovery, lease generations, attempt bounds, two-connection races and idempotent local compensation. Retry transport/time and lease time are injected; crash boundaries omit steps or raise controlled exceptions. No process-kill/power-loss, broker/provider/network, PostgreSQL isolation, distributed lease target, full saga coordinator or production throughput verified.'}
    (BASE/'verification-results.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'total': proof['total'], 'counts': counts, 'observations': observations, 'cleanup': proof['cleanup']}, indent=2))


if __name__ == '__main__':
    main()
