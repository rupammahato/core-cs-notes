"""Compile real C++, check contracts, and compare histories with simpler Python models."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import os
import random
import re
import shutil
import subprocess
import sys
from fixtures import BASE, CASES, MODES

BUILD = BASE / '.build'
EXE = BUILD / ('machines.exe' if os.name == 'nt' else 'machines')
FLAGS = ['-std=c++17', '-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O2']
CHECKS = []
COMMANDS = 0


def ok(value=None):
    return {'ok': True, 'result': value}


def err(message):
    return {'ok': False, 'error': message}


def quote(value):
    return json.dumps(value, ensure_ascii=True)


def run(mode, commands):
    global COMMANDS
    result = subprocess.run([str(EXE), mode], input='\n'.join(commands) + '\n',
                            text=True, capture_output=True, check=True, timeout=30)
    assert not result.stderr, result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(rows) == len(commands), (mode, len(rows), len(commands))
    COMMANDS += len(rows)
    return rows


def compare(name, mode, commands, expected):
    actual = run(mode, commands)
    for i, (want, got) in enumerate(zip(expected, actual)):
        assert want == got, (name, i, commands[i], want, got)
    CHECKS.append({'name': name, 'passed': True, 'commands': len(commands)})
    return actual


def randomized_models():
    rng = random.Random(20261021)
    commands, expected, data, stack = [], [], {}, []
    for _ in range(400):
        action = rng.choice(['SET', 'ERASE', 'GET', 'BEGIN', 'COMMIT', 'ROLLBACK'])
        key, value = rng.choice('abcd'), rng.choice(['', 'one', 'two words'])
        result = None
        if action == 'SET': command = f'SET {key} {quote(value)}'; data[key] = value
        elif action == 'ERASE': command = f'ERASE {key}'; result = key in data; data.pop(key, None)
        elif action == 'GET': command = f'GET {key}'; result = data.get(key)
        elif action == 'BEGIN': command = action; stack.append(data.copy())
        else:
            command = action
            if not stack:
                commands.append(command); expected.append(err('no transaction')); continue
            snapshot = stack.pop()
            if action == 'ROLLBACK': data = snapshot
        commands.extend([command, 'STATE']); expected.extend([ok(result), ok({'data': data.copy(), 'depth': len(stack)})])
    compare('random KV histories against snapshot model', 'kv', commands, expected)

    commands, expected, accepted, now = ['INIT 3 7'], [ok()], [], 0
    # Oracle retains the complete accepted log and scans it; it does not prune a deque.
    for _ in range(500):
        now += rng.randrange(3); key = rng.choice('abc'); passed_time = now if rng.random() > .15 else -1
        command = f'ALLOW {key} {passed_time}'
        if passed_time == -1: result = err('invalid time')
        else:
            allowed = sum(k == key and passed_time - 7 < at <= passed_time for k, at in accepted) < 3
            if allowed: accepted.append((key, passed_time))
            result = ok(allowed)
        commands.append(command); expected.append(result)
    compare('random limiter against full accepted log', 'limiter', commands, expected)

    commands, expected, subs = [], [], []
    for i in range(300):
        action = rng.choice(['SUB', 'OFF', 'PUB']); sid = 's' + str(rng.randrange(12)); topic = rng.choice(['a', 'b'])
        if action == 'SUB':
            behavior = rng.choice(['record', 'throw', 'off', 'add', 'recursive']); target = 's' + str(rng.randrange(12))
            command = f'SUB {sid} {topic} {behavior} {target}'
            if any(s[0] == sid for s in subs): result = err('duplicate subscription')
            else: subs.append((sid, topic, behavior, target)); result = ok()
        elif action == 'OFF':
            command = f'OFF {sid}'; found = any(s[0] == sid for s in subs)
            subs = [s for s in subs if s[0] != sid]; result = ok(found)
        else:
            command = f'PUB {topic} p{i}'; events, callbacks = [], []
            for ident, subscribed_topic, behavior, target in list(subs):
                if subscribed_topic != topic: continue
                events.append(f'{ident}:p{i}'); failed = behavior in ['throw', 'recursive']
                if behavior == 'off': subs = [s for s in subs if s[0] != target]
                if behavior == 'add':
                    if any(s[0] == target for s in subs): failed = True
                    else: subs.append((target, topic, 'record', '-'))
                callbacks.append(ident + (':error' if failed else ':ok'))
            result = ok({'events': events, 'callbacks': callbacks})
        commands.extend([command, 'STATE']); expected.extend([result, ok([s[0] for s in subs])])
    compare('random event lifecycle against list snapshot model', 'bus', commands, expected)

    commands, expected, tasks, statuses, now, seq = [], [], {}, {}, 0, 0
    for _ in range(350):
        action = rng.choice(['ADD', 'CANCEL', 'ADVANCE']); ident = 'j' + str(rng.randrange(100))
        if action == 'ADD':
            due = now + rng.randrange(10); priority = rng.randrange(4); fail = rng.choice([True, False])
            command = f'ADD {ident} {due} {priority} ' + ('fail' if fail else 'ok')
            if ident in statuses: result = err('duplicate task')
            else:
                tasks[ident] = (due, -priority, seq, fail); statuses[ident] = 'scheduled'; seq += 1; result = ok()
        elif action == 'CANCEL':
            command = f'CANCEL {ident}'; cancelled = statuses.get(ident) == 'scheduled'
            if cancelled: statuses[ident] = 'cancelled'
            result = ok(cancelled)
        else:
            now += rng.randrange(5); command = f'ADVANCE {now}'; executed = []
            # Full sort each advance, rather than the C++ priority queue/lazy tombstones.
            due_jobs = sorted((task, ident) for ident, task in tasks.items() if statuses[ident] == 'scheduled' and task[0] <= now)
            for task, ident in due_jobs:
                statuses[ident] = 'failed' if task[3] else 'succeeded'; executed.append(ident + ':' + statuses[ident])
            result = ok(executed)
        commands.extend([command, 'STATE']); expected.extend([result, ok(statuses.copy())])
    compare('random scheduler against sorted pending jobs', 'scheduler', commands, expected)

    rooms, bookings, commands, expected = {'A': 2, 'B': 4, 'C': 4}, {}, [], []
    for _ in range(350):
        action = rng.choice(['BOOK', 'MOVE', 'CANCEL']); ident = 'm' + str(rng.randrange(20))
        if action == 'CANCEL':
            command = f'CANCEL {ident}'; result = ok(ident in bookings); bookings.pop(ident, None)
        else:
            start = rng.randrange(20); end = start + rng.randrange(5); people = rng.randrange(1, 6)
            command = f'{action} {ident} {start} {end} {people}'
            if action == 'BOOK' and ident in bookings: result = err('duplicate booking')
            elif action == 'MOVE' and ident not in bookings: result = err('unknown booking')
            elif start == end: result = err('invalid interval')
            else:
                candidates = []
                for room, capacity in rooms.items():
                    occupied = set()
                    for other, booking in bookings.items():
                        if other != ident and booking[0] == room: occupied.update(range(booking[1], booking[2]))
                    # Integer fixture times permit an independent discrete-slot overlap oracle.
                    if capacity >= people and not occupied.intersection(range(start, end)): candidates.append((capacity, room))
                if not candidates: result = err('no room')
                else:
                    room = min(candidates)[1]; bookings[ident] = [room, start, end, people]; result = ok(room)
        commands.extend([command, 'STATE']); expected.extend([result, ok({k: list(v) for k, v in bookings.items()})])
    compare('random room allocation against occupied slots', 'booking', commands, expected)

    documents, commands, expected = {}, [], []
    def words(text): return Counter(re.findall(r'[a-z0-9]+', text.lower()))
    for _ in range(400):
        action = rng.choice(['PUT', 'ERASE', 'FIND']); ident = 'd' + str(rng.randrange(20))
        text = rng.choice(['RED blue red', 'node.js api2', '', 'blue; api2 API2', 'missing'])
        if action == 'PUT': command = f'PUT {ident} {quote(text)}'; documents[ident] = text; result = ok()
        elif action == 'ERASE': command = f'ERASE {ident}'; result = ok(ident in documents); documents.pop(ident, None)
        else:
            mode = rng.choice(['AND', 'OR']); command = f'FIND {mode} {quote(text)}'; query = set(words(text)); matches = []
            for doc, body in documents.items():
                frequencies = words(body); intersection = query.intersection(frequencies)
                if query and (query.issubset(frequencies) if mode == 'AND' else intersection):
                    matches.append([doc, sum(frequencies[t] for t in query)])
            result = ok(sorted(matches, key=lambda item: (-item[1], item[0])))
        commands.append(command); expected.append(result)
    compare('random inverted index against full document scan', 'search', commands, expected)

    commands, expected, configs = [], [], {}
    def bucket(tenant, flag, user):
        payload = ''.join(str(len(part)) + ':' + part for part in [tenant, flag, user]).encode('ascii')
        value = 0x811c9dc5
        for byte in payload: value = ((value ^ byte) * 0x01000193) & 0xffffffff
        return value % 10000
    for _ in range(400):
        tenant, flag, user = rng.choice(['a', 'ab', 'b']), rng.choice(['c', 'bc']), 'u' + str(rng.randrange(80))
        if rng.random() < .5:
            version, percent = rng.randrange(1, 10), rng.choice([0, 10, 50, 100]); command = f'UPDATE {tenant} {flag} {version} {percent}'
            old = configs.get((tenant, flag))
            if old and version < old[0]: result = err('stale version')
            elif old and version == old[0] and percent != old[1]: result = err('version conflict')
            elif old and (version, percent) == old: result = ok(False)
            else: configs[tenant, flag] = (version, percent); result = ok(True)
        else:
            command = f'EVAL {tenant} {flag} {user}'; policy = configs.get((tenant, flag))
            result = ok(bool(policy and bucket(tenant, flag, user) < policy[1] * 100))
        commands.append(command); expected.append(result)
    compare('random flags against fixed-width reference hash and versions', 'flags', commands, expected)
    commands, expected = [], []
    # Stable cohorts: increasing percentage must retain every previously enabled identity.
    enabled_before = set()
    for version, percent in enumerate([0, 5, 25, 50, 100], 1):
        commands.append(f'UPDATE t f {version} {percent}'); expected.append(ok(True))
        enabled_now = set()
        for user in range(200):
            ident = 'u' + str(user); enabled = bucket('t', 'f', ident) < percent * 100
            commands.append(f'EVAL t f {ident}'); expected.append(ok(enabled))
            if enabled: enabled_now.add(ident)
        assert enabled_before <= enabled_now; enabled_before = enabled_now
    compare('stable flag cohorts over five increasing percentages', 'flags', commands, expected)
    compare('length-prefix flag bucket separation', 'flags', ['BUCKET ab c u', 'BUCKET a bc u'],
            [ok(bucket('ab', 'c', 'u')), ok(bucket('a', 'bc', 'u'))])

    # The change contract permits any feasible subset, so validate the returned coins
    # and update the oracle with that permitted choice, not a copied DP tie-break.
    commands = []
    for _ in range(250):
        action = rng.choice(['SELECT tea', 'SELECT snack', 'INSERT 1', 'INSERT 3', 'INSERT 4', 'INSERT 10', 'VEND', 'CANCEL'])
        commands.extend([action, 'STATE'])
    rows = run('vending', commands); cash = Counter({3: 2, 4: 1}); escrow = Counter(); selected = None
    stock = {'tea': 2, 'snack': 1}; prices = {'tea': 4, 'snack': 7}
    for i in range(0, len(commands), 2):
        parts = commands[i].split(); result = rows[i]; credit = sum(coin * count for coin, count in escrow.items())
        if parts[0] == 'SELECT':
            if stock[parts[1]] == 0: assert result == err('out of stock')
            else: assert result == ok(); selected = parts[1]
        elif parts[0] == 'INSERT':
            coin = int(parts[1]); assert result == ok(); escrow[coin] += 1
        elif parts[0] == 'CANCEL':
            assert result == ok(sorted(escrow.elements())); escrow.clear(); selected = None
        elif selected is None: assert result == err('select item first')
        elif credit < prices[selected]: assert result == err('insufficient credit')
        else:
            change = credit - prices[selected]; available = cash + escrow; denoms = [1, 3, 4, 10]
            feasible = any(sum(d * n for d, n in zip(denoms, counts)) == change
                           for counts in itertools.product(*(range(min(available[d], change // d) + 1) for d in denoms)))
            if not feasible: assert result == err('exact change unavailable')
            else:
                assert result['ok']; returned = Counter(result['result']); assert sum(result['result']) == change
                assert all(d in denoms and n <= available[d] for d, n in returned.items())
                cash = available - returned; stock[selected] -= 1; escrow.clear(); selected = None
        assert rows[i + 1] == ok({'stock': stock.copy(), 'cash': sum(d * n for d, n in cash.items()),
                                 'credit': sum(d * n for d, n in escrow.items()), 'selected': selected})
    CHECKS.append({'name': 'random vending transitions against exhaustive bounded change', 'passed': True, 'commands': len(commands)})


def verify():
    BUILD.mkdir(exist_ok=True)
    compiler = shutil.which('g++')
    assert compiler, 'Install a C++17 g++ compiler and add it to PATH.'
    logs = []
    for source, output in [('main.cpp', EXE), ('api_tests.cpp', BUILD / ('api-tests.exe' if os.name == 'nt' else 'api-tests'))]:
        command = [compiler, *FLAGS, str(BASE / source), '-o', str(output)]
        result = subprocess.run(command, text=True, capture_output=True, timeout=90)
        logs.append({'source': source, 'command': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        assert result.returncode == 0, result.stderr
        assert not result.stderr, result.stderr
    (BASE / 'compile-output.json').write_text(json.dumps(logs, indent=2) + '\n', encoding='utf-8')
    CHECKS.append({'name': 'both C++17 targets compile with warnings as errors', 'passed': True})
    api = subprocess.run([str(BUILD / ('api-tests.exe' if os.name == 'nt' else 'api-tests'))], text=True, capture_output=True, check=True, timeout=10)
    api_results = json.loads(api.stdout)
    assert api_results['passed'] == 14, api_results
    CHECKS.append({'name': 'direct callback lifecycle, nonstandard exceptions and reentrancy', 'passed': True, 'assertions': api_results['passed']})
    observations = {}
    for item in CASES:
        observations[item['id']] = compare(item['id'] + ': ' + item['title'], item['mode'], item['commands'], item['expected'])
    malformed = ['"unterminated', 'SET "a"x b', 'x\\y', '"bad\\q"', '', 'X\tY', 'X' * 4097, 'x\x01']
    errors = ['malformed quote', 'malformed quote', 'quote token explicitly', 'invalid escape', 'empty command',
              'ASCII input required', 'line too long', 'ASCII input required']
    for mode in MODES:
        compare('parser rejects malformed input in ' + mode, mode, malformed, [err(message) for message in errors])
    compare('integer overflow and partial integers do not mutate', 'booking',
            ['BOOK x 0 999999999999999999999999 2', 'BOOK x 0 1x 2', 'BOOK x 0 1 2 extra', 'STATE'],
            [err('invalid integer'), err('invalid integer'), err('wrong arity'), ok({})])
    compare('vending credit bound and unsupported coin preserve escrow', 'vending',
            ['INSERT 10'] * 100 + ['INSERT 1', 'INSERT -1', 'CANCEL', 'STATE'],
            [ok()] * 100 + [err('credit limit'), err('unsupported coin'), ok([10] * 100),
                           ok({'stock': {'snack': 1, 'tea': 2}, 'cash': 10, 'credit': 0, 'selected': None})])
    compare('time range and negative priority validation', 'scheduler',
            ['ADD a -1 0 ok', 'ADD a 1000000000001 0 ok', 'ADD a 0 -1 ok', 'STATE'],
            [err('invalid time'), err('invalid time'), err('invalid priority'), ok({})])
    compare('quoted spaces escaped quotes and backslashes round-trip', 'kv',
            [r'SET "a b" "x\"y\\z"', 'GET "a b"', 'SET "" bad', 'GET "a b"'],
            [ok(), ok('x"y\\z'), err('empty identifier'), ok('x"y\\z')])
    randomized_models()
    for arguments in [[], ['unknown']]:
        result = subprocess.run([str(EXE), *arguments], text=True, capture_output=True, timeout=5)
        assert result.returncode == 2 and not result.stdout and result.stderr
    CHECKS.append({'name': 'invalid runner invocation exits with status 2', 'passed': True})
    (BASE / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n', encoding='utf-8')
    source_files = ['common.hpp', 'machines.hpp', 'main.cpp', 'api_tests.cpp', 'fixtures.py', 'verify.py']
    proof = {'verified_date': '2026-10-21', 'python': sys.version.split()[0],
             'compiler': subprocess.check_output([compiler, '--version'], text=True).splitlines()[0],
             'flags': FLAGS, 'checks': CHECKS, 'total': len(CHECKS), 'commands_checked': COMMANDS,
             'direct_api_assertions': api_results['passed'], 'worked_traces': len(CASES),
             'source_sha256': {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest() for name in source_files},
             'boundaries': ['Single-threaded in-memory exercises; no durability or distributed guarantees.',
                            'No performance benchmark, sanitizer run, allocation-failure injection or real hardware experiment.',
                            'Randomized tests use one recorded seed and finite histories; not a proof for all inputs.']}
    (BASE / 'verification-results.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: proof[key] for key in ['total', 'commands_checked', 'direct_api_assertions', 'worked_traces', 'compiler']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', choices=[item['id'] for item in CASES])
    args = parser.parse_args()
    if args.trace:
        item = next(item for item in CASES if item['id'] == args.trace)
        assert EXE.exists(), 'Run verify.py first to compile the runner.'
        for command, response in zip(item['commands'], run(item['mode'], item['commands'])):
            print(command)
            print(json.dumps(response, separators=(',', ':')))
    else:
        verify()
