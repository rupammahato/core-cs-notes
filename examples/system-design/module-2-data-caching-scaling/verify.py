"""Named data/cache checks with real SQLite and deterministic async interleavings."""
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import FrozenInstanceError
import asyncio
import json
import platform
import sqlite3

from data import Notes, Scope, Missing, Stale
from cache import CacheAside, Churn
from scaling import demand, place, placement_demo

BASE = Path(__file__).resolve().parent
checks, observations = [], {}


def check(group, name, condition):
    assert condition, name
    checks.append({'group': group, 'name': name, 'passed': True})


def raises(group, name, error, action):
    try:
        action()
    except error:
        check(group, name, True)
    else:
        raise AssertionError(name)


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


async def cache_checks(source, other):
    scope = Scope('t0', 'u0')
    caches = []

    def cache(loader, clock=None, **options):
        item = CacheAside(loader, clock or Clock(), **options)
        caches.append(item)
        return item

    async def load(who, identity):
        return source.get(who, identity)

    try:
        clock = Clock()
        item = cache(load, clock, ttl=10)
        start_reads = source.reads
        first = await item.get(scope, 'n00_0001')
        check('cache_basics', 'cold read loads authoritative row', first.revision == 1)
        check('cache_basics', 'cold read makes one database call', source.reads-start_reads == 1)
        again = await item.get(scope, 'n00_0001')
        check('cache_basics', 'warm result equals cold result', again == first)
        check('cache_basics', 'warm read avoids database call', source.reads-start_reads == 1)
        check('cache_basics', 'hit counted', item.stats['hits'] == 1)
        clock.now = 9.999
        await item.get(scope, 'n00_0001')
        check('cache_basics', 'entry valid just before TTL boundary', source.reads-start_reads == 1)
        clock.now = 10
        await item.get(scope, 'n00_0001')
        check('cache_basics', 'entry expires exactly at TTL boundary', source.reads-start_reads == 2)
        check('cache_basics', 'expiration counted', item.stats['expired'] == 1)
        check('cache_basics', 'scoped keys include tenant and owner', item.key(scope, 'same') != item.key(Scope('t1', 'u0'), 'same') and item.key(scope, 'same') != item.key(Scope('t0', 'u1'), 'same'))
        source.replace(Scope('t1', 'u0'), 'n00_0001', 1, 'other tenant private note')
        before_beta = source.reads
        beta = await item.get(Scope('t1', 'u0'), 'n00_0001')
        check('cache_basics', 'same ID in another tenant causes separate load', beta.title == 'other tenant private note' and beta.revision == 2 and source.reads-before_beta == 1)
        try:
            await item.get(Scope('t0', 'u1'), 'n00_0001')
        except Missing:
            check('cache_basics', 'cached Alice-like scope cannot satisfy different owner', True)
        else:
            raise AssertionError('cross-owner read')
        check('cache_basics', 'missing result is not cached', item.key(Scope('t0', 'u1'), 'n00_0001') not in item.entries)
        check('cache_basics', 'failure releases in-flight task', not item.pending)
        raises('cache_basics', 'immutable values cannot be changed by a caller', FrozenInstanceError, lambda: setattr(first, 'title', 'corrupt'))
        small = cache(load, capacity=2)
        await small.get(scope, 'n00_0001')
        await small.get(scope, 'n00_0002')
        await small.get(scope, 'n00_0001')
        await small.get(scope, 'n00_0003')
        check('cache_basics', 'entry capacity enforced', len(small.entries) == 2)
        check('cache_basics', 'least recently used entry evicted', small.key(scope, 'n00_0002') not in small.entries)
        check('cache_basics', 'recently touched entry retained', small.key(scope, 'n00_0001') in small.entries)
        check('cache_basics', 'eviction counted', small.stats['evictions'] == 1)
        observations['ttl_and_scope'] = {'database_calls_for_cold_warm_before_expiry_after_expiry': 2,
            'ttl_seconds': 10, 'expires_at_equal_time': True, 'owner_miss_not_cached': True,
            'bounded_cache_entries': len(small.entries), 'evictions': small.stats['evictions']}

        entered, release = asyncio.Event(), asyncio.Event()

        async def paused(who, identity):
            snapshot = source.get(who, identity)
            entered.set()
            await release.wait()
            return snapshot

        shared = cache(paused)
        before = source.reads
        waiters = [asyncio.create_task(shared.get(scope, 'n00_0004')) for _ in range(10)]
        await asyncio.wait_for(entered.wait(), 2)
        release.set()
        results = await asyncio.gather(*waiters)
        check('single_flight', 'ten simultaneous misses return equal values', len(results) == 10 and all(value == results[0] for value in results))
        check('single_flight', 'ten misses perform one database load', source.reads-before == 1)
        check('single_flight', 'nine callers coalesce', shared.stats['coalesced'] == 9)
        check('single_flight', 'shared task removed after success', not shared.pending)
        observations['single_flight'] = {'callers': 10, 'database_reads': source.reads-before,
            'coalesced': shared.stats['coalesced'], 'stats': dict(shared.stats)}

        # Reproduce naive cache-aside stale refill with an actual old SQLite snapshot.
        entered, release = asyncio.Event(), asyncio.Event()
        naive_entries = {}

        async def naive_read():
            if 'note' not in naive_entries:
                snapshot = source.get(scope, 'n00_0010')
                entered.set()
                await release.wait()
                naive_entries['note'] = snapshot
            return naive_entries['note']

        old_reader = asyncio.create_task(naive_read())
        await asyncio.wait_for(entered.wait(), 2)
        committed = source.replace(scope, 'n00_0010', 1, 'committed revision 2')
        naive_entries.pop('note', None)
        release.set()
        old = await old_reader
        stale_again = await naive_read()
        check('invalidation', 'naive writer commits revision 2', committed.revision == 2)
        check('invalidation', 'naive old reader installs revision 1 after deletion', old.revision == stale_again.revision == 1)
        check('invalidation', 'authoritative state differs from stale cache', source.get(scope, 'n00_0010').revision == 2)
        observations['naive_refill'] = {'committed_revision': committed.revision,
            'old_reader_revision': old.revision, 'next_cached_revision': stale_again.revision,
            'timeline': ['reader captures revision 1', 'writer commits revision 2',
                         'writer deletes cache entry', 'reader fills revision 1 after invalidation']}

        entered, release = asyncio.Event(), asyncio.Event()
        calls = 0

        async def paused_once(who, identity):
            nonlocal calls
            calls += 1
            snapshot = source.get(who, identity)
            if calls == 1:
                entered.set()
                await release.wait()
            return snapshot

        fenced = cache(paused_once)
        old_reader = asyncio.create_task(fenced.get(scope, 'n00_0011'))
        await asyncio.wait_for(entered.wait(), 2)
        source.replace(scope, 'n00_0011', 1, 'revision 2 with local fence')
        fenced.invalidate(scope, 'n00_0011')
        newer = await fenced.get(scope, 'n00_0011')
        check('invalidation', 'post-invalidation caller does not join old pending load', newer.revision == 2 and calls == 2)
        release.set()
        resolved = await old_reader
        check('invalidation', 'old in-flight value cannot refill local cache', fenced.stats['fenced'] == 1)
        check('invalidation', 'overlapping reader retries to current cached revision', resolved.revision == 2)
        check('invalidation', 'next local cache read remains revision 2', (await fenced.get(scope, 'n00_0011')).revision == 2)
        check('invalidation', 'generation is one scalar not per-key tombstones', fenced.epoch == 1)
        observations['fenced_refill'] = {'post_invalidation_reader': newer.revision,
            'overlapping_reader': resolved.revision, 'database_loads': calls, 'stats': dict(fenced.stats)}

        # Two independent caches and SQLite connections have no invalidation broadcast.
        clock = Clock()
        left = cache(load, clock, ttl=10)

        async def other_load(who, identity):
            return other.get(who, identity)

        right = cache(other_load, clock, ttl=10)
        await left.get(scope, 'n00_0012')
        await right.get(scope, 'n00_0012')
        source.replace(scope, 'n00_0012', 1, 'shared database, separate caches')
        left.invalidate(scope, 'n00_0012')
        current = await left.get(scope, 'n00_0012')
        still_old = await right.get(scope, 'n00_0012')
        check('multi_cache', 'writing instance observes its invalidated key freshly', current.revision == 2)
        check('multi_cache', 'other instance cache stays stale without broadcast', still_old.revision == 1)
        check('multi_cache', 'second connection sees committed state when bypassing cache', other.get(scope, 'n00_0012').revision == 2)
        clock.now = 10
        after_expiry = await right.get(scope, 'n00_0012')
        check('multi_cache', 'other cache refreshes at TTL expiry', after_expiry.revision == 2)
        observations['two_caches'] = {'writer_cache_revision': current.revision,
            'other_cache_before_expiry': still_old.revision,
            'other_cache_after_expiry': after_expiry.revision, 'invalidation_broadcast': False}

        entered, release = asyncio.Event(), asyncio.Event()

        async def cancellable_load(who, identity):
            snapshot = source.get(who, identity)
            entered.set()
            await release.wait()
            return snapshot

        cancellation = cache(cancellable_load)
        first_waiter = asyncio.create_task(cancellation.get(scope, 'n00_0013'))
        await asyncio.wait_for(entered.wait(), 2)
        first_waiter.cancel()
        try:
            await first_waiter
        except asyncio.CancelledError:
            pass
        check('single_flight', 'cancelled caller does not cancel shared loader', len(cancellation.pending) == 1 and not next(iter(cancellation.pending.values())).cancelled())
        second_waiter = asyncio.create_task(cancellation.get(scope, 'n00_0013'))
        release.set()
        check('single_flight', 'another caller receives result after first cancels', (await second_waiter).revision == 1)
        check('single_flight', 'one load despite waiter cancellation', cancellation.stats['loads'] == 1)

        should_fail = True

        async def failing_load(who, identity):
            if should_fail:
                raise RuntimeError('database unavailable')
            return source.get(who, identity)

        failures = cache(failing_load)
        try:
            await failures.get(scope, 'n00_0014')
        except RuntimeError:
            check('single_flight', 'loader failure propagates instead of cached success', True)
        else:
            raise AssertionError('loader failure')
        check('single_flight', 'failed load removes pending task and cache entry', not failures.pending and not failures.entries)
        should_fail = False
        check('single_flight', 'next attempt succeeds after load failure', (await failures.get(scope, 'n00_0014')).revision == 1)

        churn_cache = None

        async def churning_load(who, identity):
            snapshot = source.get(who, identity)
            churn_cache.invalidate(who, identity)
            return snapshot

        churn_cache = cache(churning_load)
        try:
            await churn_cache.get(scope, 'n00_0015')
        except Churn:
            check('invalidation', 'repeated invalidation ends with bounded churn outcome', True)
        else:
            raise AssertionError('unbounded invalidation retry')
        check('invalidation', 'churn retry bound is two loads', churn_cache.stats['loads'] == 2)
        check('invalidation', 'churn does not install invalidated data', not churn_cache.entries and not churn_cache.pending)
        for bad in (0, -1, float('inf'), float('nan')):
            raises('cache_basics', f'invalid TTL {bad} rejected', ValueError, lambda bad=bad: CacheAside(load, Clock(), ttl=bad))
        raises('cache_basics', 'zero capacity rejected', ValueError, lambda: CacheAside(load, Clock(), capacity=0))
    finally:
        for item in caches:
            await item.close()
    check('cleanup', 'all async cache tasks and entries cleared', all(not item.pending and not item.entries for item in caches))


def main():
    with TemporaryDirectory(prefix='placement-a2-') as directory:
        path = Path(directory)/'notes.sqlite'
        source = Notes(path)
        other = None
        try:
            check('queries', 'seed exact workload rows', source.seed() == 12000)
            scope = Scope('t0', 'u0')
            before = source.profile(scope)
            source.add_listing_index()
            after = source.profile(scope)
            check('queries', 'index preserves listing result', before['rows'] == after['rows'])
            check('queries', 'listing returns bounded page', len(after['rows']) == 20)
            check('queries', 'pre-index plan needs temporary ordering', any('TEMP B-TREE' in line for line in before['plan']))
            check('queries', 'new plan selects owner/recent index', any('notes_owner_recent' in line for line in after['plan']))
            check('queries', 'new plan avoids temporary ordering', not any('TEMP B-TREE' in line for line in after['plan']))
            check('queries', 'indexed fixture uses fewer SQLite VM instructions', after['sqlite_vm_instructions'] < before['sqlite_vm_instructions'])
            check('queries', 'descending timestamp and ID order stable', [(row['created_at'], row['id']) for row in after['rows']] == sorted([(row['created_at'], row['id']) for row in after['rows']], reverse=True))
            observations['index'] = {'seed_rows': 12000, 'matching_owner_rows': 300,
                'before': {key: before[key] for key in ('plan', 'sqlite_vm_instructions')},
                'after': {key: after[key] for key in ('plan', 'sqlite_vm_instructions')},
                'same_results': before['rows'] == after['rows'], 'page_size': len(after['rows'])}
            all_rows = source.listing(scope, 100)+source.listing(scope, 100, offset=100)+source.listing(scope, 100, offset=200)
            pages, cursor = [], None
            while True:
                page = source.listing(scope, 20, cursor)
                if not page:
                    break
                pages.extend(page)
                cursor = page[-1]['created_at'], page[-1]['id']
            check('pagination', 'keyset visits all 300 scoped notes', len(pages) == 300)
            check('pagination', 'keyset has no duplicate identities with timestamp ties', len({row['id'] for row in pages}) == 300)
            check('pagination', 'keyset order equals authoritative full scoped order', pages == all_rows)
            prior = source.listing(scope, 100, offset=100)[-1]
            boundary = prior['created_at'], prior['id']
            seek = source.profile(scope, 20, boundary)
            offset = source.profile(scope, 20, offset=200)
            check('pagination', 'deep offset and keyset return identical rows', seek['rows'] == offset['rows'])
            check('pagination', 'keyset skips less VM work for deep page', seek['sqlite_vm_instructions'] < offset['sqlite_vm_instructions'])
            check('pagination', 'other owner listing stays in its namespace', all(row['id'].startswith('n01_') for row in source.listing(Scope('t0', 'u1'))))
            check('pagination', 'unknown tenant listing is empty', source.listing(Scope('absent', 'u0')) == [])
            raises('pagination', 'zero page limit rejected', ValueError, lambda: source.listing(scope, 0))
            raises('pagination', 'oversized page limit rejected', ValueError, lambda: source.listing(scope, 101))
            raises('pagination', 'boolean page limit rejected', ValueError, lambda: source.listing(scope, True))
            raises('pagination', 'negative offset rejected', ValueError, lambda: source.listing(scope, offset=-1))
            raises('pagination', 'cursor and offset combination rejected', ValueError, lambda: source.listing(scope, cursor=boundary, offset=1))
            raises('pagination', 'malformed cursor rejected', ValueError, lambda: source.listing(scope, cursor=('bad', 2)))
            observations['pagination'] = {'notes_visited': len(pages), 'unique_ids': len({row['id'] for row in pages}),
                'cursor': list(boundary), 'offset_rows_skipped': 200, 'same_deep_page': True,
                'offset_vm_instructions': offset['sqlite_vm_instructions'], 'keyset_vm_instructions': seek['sqlite_vm_instructions']}
            first_page = source.listing(scope, 20)
            boundary = first_page[-1]['created_at'], first_page[-1]['id']
            with source.db:
                source.db.execute('INSERT INTO notes VALUES(?,?,?,?,?,?,?)',
                    ('t0', 'u0', 'n00_new', 'newest note', 'inserted between pages', 1000, 1))
            offset_next = source.listing(scope, 20, offset=20)
            keyset_next = source.listing(scope, 20, cursor=boundary)
            previous_ids = {row['id'] for row in first_page}
            offset_duplicates = previous_ids & {row['id'] for row in offset_next}
            keyset_duplicates = previous_ids & {row['id'] for row in keyset_next}
            check('pagination', 'new insert shifts offset into an already visited row', offset_duplicates == {first_page[-1]['id']})
            check('pagination', 'immutable-order keyset avoids that duplicate', not keyset_duplicates)
            check('pagination', 'newer insert is outside continuation cursor', 'n00_new' not in {row['id'] for row in keyset_next})
            observations['pagination_drift'] = {'inserted_between_pages': 'n00_new',
                'offset_duplicate_ids': sorted(offset_duplicates), 'keyset_duplicate_ids': sorted(keyset_duplicates),
                'continuation_includes_newer_insert': False,
                'snapshot_guarantee': False}
            raises('queries', 'cross-owner canonical read is missing', Missing, lambda: source.get(Scope('t0', 'u1'), 'n00_0001'))
            raises('queries', 'cross-owner replacement is missing', Missing, lambda: source.replace(Scope('t0', 'u1'), 'n00_0001', 1, 'bad'))
            source.replace(scope, 'n00_0020', 1, 'edited')
            raises('queries', 'stale replacement is rejected by SQL predicate', Stale, lambda: source.replace(scope, 'n00_0020', 1, 'old'))
            other = Notes(path)
            check('queries', 'second SQLite connection sees committed edit', other.get(scope, 'n00_0020').revision == 2)
            asyncio.run(cache_checks(source, other))
        finally:
            if other is not None:
                other.close()
            source.close()
    check('cleanup', 'temporary database directory removed after closing connections', not Path(directory).exists())
    high = demand(10000, 0.95, 20, 20, 200)
    cold = demand(10000, 0, 20, 20, 200)
    check('scaling_models', 'assumed 95 percent hits leave 500 database reads per second', high['estimated_db_read_qps'] == 500)
    check('scaling_models', 'cold cache drives all reads to database', cold['estimated_db_read_qps'] == 10000)
    check('scaling_models', 'horizontal replicas multiply connection ceilings', high['maximum_application_connections'] == 400)
    check('scaling_models', 'headroom budget computed explicitly', high['application_connection_budget'] == 140)
    check('scaling_models', 'example pool ceiling exceeds selected budget', high['maximum_application_connections'] > high['application_connection_budget'])
    raises('scaling_models', 'hit fraction outside bounds rejected', ValueError, lambda: demand(1, 1.1, 1, 1, 10))
    raises('scaling_models', 'negative request count rejected', ValueError, lambda: demand(-1, 0.5, 1, 1, 10))
    raises('scaling_models', 'zero instances rejected', ValueError, lambda: demand(1, 0.5, 0, 1, 10))
    raises('scaling_models', 'zero shards rejected', ValueError, lambda: place('tenant', 0))
    placement = placement_demo()
    check('scaling_models', 'synthetic shard load sums to request count', sum(placement['requests_by_shard'].values()) == placement['synthetic_requests'] == 1000)
    check('scaling_models', 'one hot tenant stays on one shard', max(placement['requests_by_shard'].values()) >= 901)
    check('scaling_models', 'modulo resize remaps a nonzero proper subset', 0 < placement['tenants_remapped_on_modulo_resize'] < 100)
    check('scaling_models', 'hash placement is deterministic', place('tenant_000', 4) == place('tenant_000', 4))
    observations['scaling'] = {'warm_assumption': high, 'cold_assumption': cold,
        'cold_to_warm_db_demand_ratio': cold['estimated_db_read_qps']/high['estimated_db_read_qps'],
        'placement': placement}
    counts = {}
    for item in checks:
        counts[item['group']] = counts.get(item['group'], 0)+1
    result = {'label': 'A2', 'verified_date': '2026-10-16', 'python': platform.python_version(),
        'sqlite': sqlite3.sqlite_version, 'os': platform.system()+' '+platform.release(),
        'total': len(checks), 'counts': counts, 'checks': checks, 'observations': observations,
        'cleanup': {'sqlite_connections_closed': True, 'temporary_database_directory_removed': True,
                    'async_cache_tasks_closed': True, 'persistent_listener_started': False},
        'scope': 'Real local SQLite index plans, VM instruction counts, scoped keyset queries and conditional writes. Deterministic asyncio interleavings over process-local caches and two SQLite connections. TTL uses an injected clock; scaling/placement are hypothetical arithmetic. No Redis, HTTP/authentication, replicated database, sharded deployment, network partition or production throughput verified.'}
    (BASE/'verification-results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'total': result['total'], 'counts': counts, 'observations': observations, 'cleanup': result['cleanup']}, indent=2))


if __name__ == '__main__':
    main()
