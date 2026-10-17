"""Deterministic, single-process comparisons; caller supplies nondecreasing ms."""
from collections import deque


class FixedWindow:
    def __init__(self, limit, window_ms):
        self.limit, self.window_ms = limit, window_ms
        self.bucket, self.count = None, 0

    def allow(self, now):
        bucket = now // self.window_ms
        if bucket != self.bucket:
            self.bucket, self.count = bucket, 0
        if self.count >= self.limit:
            return False
        self.count += 1
        return True


class SlidingLog:
    def __init__(self, limit, window_ms):
        self.limit, self.window_ms = limit, window_ms
        self.events = deque()

    def allow(self, now):
        # Exact chosen interval: (now - window, now]. Denials are not stored.
        while self.events and self.events[0] <= now - self.window_ms:
            self.events.popleft()
        if len(self.events) >= self.limit:
            return False
        self.events.append(now)
        return True


class SlidingCounter:
    def __init__(self, limit, window_ms):
        self.limit, self.window_ms = limit, window_ms
        self.bucket, self.current, self.previous = None, 0, 0

    def allow(self, now):
        bucket, offset = divmod(now, self.window_ms)
        if bucket != self.bucket:
            self.previous = self.current if self.bucket == bucket - 1 else 0
            self.bucket, self.current = bucket, 0
        # Integer weighted estimate; approximation assumes uniform old traffic.
        weighted = self.current * self.window_ms
        weighted += self.previous * (self.window_ms - offset)
        if weighted + self.window_ms > self.limit * self.window_ms:
            return False
        self.current += 1
        return True


def compare():
    timeline = [999, 999, 999, 1000, 1000, 1000, 1999]
    result = {'times_ms': timeline}
    for name, factory in [('fixed', FixedWindow), ('sliding_log', SlidingLog),
                          ('sliding_counter', SlidingCounter)]:
        limiter = factory(3, 1000)
        result[name] = [limiter.allow(now) for now in timeline]
    return result
