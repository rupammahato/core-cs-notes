"""Deterministic deadline/retry exercise; injected transport must honor each budget."""
import math


class Transient(Exception):
    pass


class Permanent(Exception):
    pass


class Deadline(Exception):
    pass


def retry(call, clock, sleep, random_fraction, *, total=1.0, per_attempt=0.4,
          attempts=3, base=0.1, cap=0.5, retry_safe=False):
    values = (total, per_attempt, base, cap)
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError('positive finite durations required')
    if type(attempts) is not int or not 1 <= attempts <= 10:
        raise ValueError('attempt count must be 1..10')
    deadline, trace = clock()+total, []
    for number in range(1, attempts+1):
        remaining = deadline-clock()
        if remaining <= 0:
            raise Deadline('end-to-end deadline exhausted')
        budget = min(per_attempt, remaining)
        trace.append({'attempt': number, 'budget': round(budget, 6)})
        try:
            result = call(budget)
        except Transient:
            if not retry_safe or number == attempts:
                raise
            fraction = random_fraction()
            if not 0 <= fraction <= 1:
                raise ValueError('jitter fraction must be 0..1')
            delay = min(cap, base*2**(number-1))*fraction
            remaining = deadline-clock()
            if remaining <= 0 or delay >= remaining:
                raise Deadline('retry delay would consume remaining deadline')
            trace[-1]['backoff'] = round(delay, 6)
            sleep(delay)
        else:
            if clock() >= deadline:
                raise Deadline('response arrived outside caller deadline')
            return {'result': result, 'trace': trace}
    raise AssertionError('unreachable')
