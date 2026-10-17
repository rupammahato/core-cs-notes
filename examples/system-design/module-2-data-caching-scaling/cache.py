"""Bounded process-local cache with TTL, single-flight and local invalidation fencing."""
from collections import OrderedDict
import asyncio
import math


class Churn(Exception):
    pass


class CacheAside:
    def __init__(self, loader, clock, ttl=10, capacity=128):
        if not math.isfinite(ttl) or ttl <= 0 or type(capacity) is not int or capacity < 1:
            raise ValueError('positive finite TTL and capacity required')
        self.loader, self.clock, self.ttl, self.capacity = loader, clock, ttl, capacity
        self.entries = OrderedDict()
        self.pending = {}
        self.epoch = 0
        self.stats = {'hits': 0, 'misses': 0, 'loads': 0, 'coalesced': 0, 'expired': 0,
                      'evictions': 0, 'fenced': 0, 'invalidations': 0}

    @staticmethod
    def key(scope, identity):
        return scope.tenant, scope.owner, identity

    def invalidate(self, scope, identity):
        self.entries.pop(self.key(scope, identity), None)
        # A single global epoch avoids an ever-growing per-key generation map.
        # It conservatively fences unrelated in-flight loads too.
        self.epoch += 1
        self.stats['invalidations'] += 1

    async def _load(self, key, scope, identity, epoch):
        task_key = key, epoch
        try:
            self.stats['loads'] += 1
            value = await self.loader(scope, identity)
            if epoch != self.epoch:
                self.stats['fenced'] += 1
                return value
            # TTL begins at cache insertion, not at the database snapshot time.
            self.entries[key] = self.clock()+self.ttl, value
            self.entries.move_to_end(key)
            while len(self.entries) > self.capacity:
                self.entries.popitem(last=False)
                self.stats['evictions'] += 1
            return value
        finally:
            self.pending.pop(task_key, None)

    async def get(self, scope, identity):
        key = self.key(scope, identity)
        for _ in range(2):  # Bounded retry if a local write invalidates an active load.
            entry = self.entries.get(key)
            if entry is not None:
                expiry, value = entry
                if self.clock() < expiry:
                    self.entries.move_to_end(key)
                    self.stats['hits'] += 1
                    return value
                self.entries.pop(key)
                self.stats['expired'] += 1
            self.stats['misses'] += 1
            epoch = self.epoch
            task_key = key, epoch
            task = self.pending.get(task_key)
            if task is None:
                task = asyncio.create_task(self._load(key, scope, identity, epoch))
                # A cancelled waiter must not create an unobserved task exception.
                task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
                self.pending[task_key] = task
            else:
                self.stats['coalesced'] += 1
            value = await asyncio.shield(task)  # One cancelled caller does not cancel shared work.
            if epoch == self.epoch:
                return value
        raise Churn('local invalidation changed twice; caller must retry within its deadline')

    async def close(self):
        tasks = list(self.pending.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.entries.clear()
