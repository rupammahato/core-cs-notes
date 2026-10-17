"""Bounded local redirect cache and explicitly lossy in-memory analytics admission."""
from collections import Counter, OrderedDict
from queue import Queue, Empty, Full
from threading import RLock
import math

from shortener import Error, valid_code


class Service:
    def __init__(self, store, clock, cache_ttl=2, cache_capacity=128, analytics_capacity=4):
        if not math.isfinite(cache_ttl) or cache_ttl<=0 or any(type(value) is not int or value<1
            for value in (cache_capacity,analytics_capacity)):
            raise ValueError('invalid cache or analytics bounds')
        self.store,self.clock,self.cache_ttl,self.capacity = store,clock,cache_ttl,cache_capacity
        self.cache,self.metrics = OrderedDict(),Counter()
        self.queue,self.lock = Queue(maxsize=analytics_capacity),RLock()

    def resolve(self, code, record=True):
        if not valid_code(code):
            raise Error(404,'not_found')
        with self.lock:  # Serializes local lookup/fill and local disable/invalidation.
            now = self.clock()
            entry = self.cache.get(code)
            if entry is not None and now<entry[0]:
                link = entry[1]
                self.cache.move_to_end(code)
                self.metrics['cache_hits'] += 1
            else:
                self.cache.pop(code,None)
                self.metrics['cache_misses'] += 1
                link = self.store.lookup(code)
                if not link.disabled and now<link.expires_at:
                    self.cache[code] = min(now+self.cache_ttl,link.expires_at),link
                    while len(self.cache)>self.capacity:
                        self.cache.popitem(last=False)
                        self.metrics['evictions'] += 1
            if link.disabled or self.clock()>=link.expires_at:
                self.cache.pop(code,None)
                raise Error(410,'link_gone')
            if record:
                self.metrics['redirect_decisions'] += 1
                try:
                    self.queue.put_nowait((code,math.floor(self.clock()/60)))
                    self.metrics['analytics_enqueued'] += 1
                except Full:
                    self.metrics['analytics_dropped'] += 1
            return link.url

    def disable(self, principal, code):
        with self.lock:
            self.store.disable(principal,code)
            self.cache.pop(code,None)

    def flush_analytics(self, limit=8, fail=False):
        if type(limit) is not int or not 1<=limit<=100:
            raise ValueError('batch limit must be 1..100')
        with self.lock,self.store.lock:
            batch = []
            while len(batch)<limit:
                try:
                    batch.append(self.queue.get_nowait())
                except Empty:
                    break
            cutoff = math.floor(self.clock()/60)-2
            try:
                self.store.db.execute('BEGIN IMMEDIATE')
                self.store.db.execute('DELETE FROM counts WHERE bucket<?',(cutoff,))
                applied = 0
                for code,bucket in batch:
                    if bucket>=cutoff:
                        self.store.db.execute('''INSERT INTO counts VALUES(?,?,1)
                            ON CONFLICT(code,bucket) DO UPDATE SET total=total+1''',(code,bucket))
                        applied += 1
                if fail:
                    raise RuntimeError('owned analytics write fault')
                self.store.db.execute('COMMIT')
                self.metrics['analytics_recorded'] += applied
                self.metrics['analytics_stale_dropped'] += len(batch)-applied
                return applied
            except Exception:
                if self.store.db.in_transaction:
                    self.store.db.execute('ROLLBACK')
                self.metrics['analytics_write_dropped'] += len(batch)
                return 0  # Best effort: batch is lost, rather than blocking redirect recovery.
            finally:
                for _ in batch:
                    self.queue.task_done()

    def statistics(self, principal, code):
        with self.lock,self.store.lock:
            self.store.owned(principal,code)
            cutoff = math.floor(self.clock()/60)-2
            total = self.store.db.execute('SELECT coalesce(sum(total),0) FROM counts WHERE code=? AND bucket>=?',
                (code,cutoff)).fetchone()[0]
            return {'code':code,'recorded_redirect_decisions':total,'window_start':cutoff*60}
