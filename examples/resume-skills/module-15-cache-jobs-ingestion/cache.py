from collections import OrderedDict
from concurrent.futures import Future
from copy import deepcopy
from threading import RLock,Condition
from time import monotonic

class TTLCache:
    """Bounded, process-local cache; never a Redis implementation."""
    def __init__(self,*,capacity=32,ttl=10,negative_ttl=2,clock=monotonic):
        if type(capacity) is not int or capacity<1 or ttl<=0 or negative_ttl<=0:
            raise ValueError('invalid cache configuration')
        self.capacity,self.ttl,self.negative_ttl,self.clock=capacity,ttl,negative_ttl,clock
        self.entries=OrderedDict();self.flights={};self.epoch=0
        self.lock=RLock();self.changed=Condition(self.lock)
        self.stats={'hits':0,'loads':0,'waits':0}

    def invalidate(self,key):
        with self.lock:
            self.entries.pop(key,None)
            self.epoch+=1  # Conservative: any invalidation fences all current fills.

    def get_or_load(self,key,loader,*,wait_seconds=5):
        with self.lock:
            entry=self.entries.get(key)
            if entry is not None and self.clock()<entry[0]:
                self.entries.move_to_end(key);self.stats['hits']+=1
                return deepcopy(entry[1])
            self.entries.pop(key,None)
            future=self.flights.get(key)
            if future is None:
                future=Future();self.flights[key]=future;leader=True;epoch=self.epoch
                self.stats['loads']+=1
            else:
                leader=False;self.stats['waits']+=1;self.changed.notify_all()
        if not leader:
            return deepcopy(future.result(timeout=wait_seconds))
        try:
            value=loader()
            saved=deepcopy(value)
            with self.lock:
                if self.epoch==epoch:
                    duration=self.negative_ttl if value is None else self.ttl
                    self.entries[key]=(self.clock()+duration,saved)
                    while len(self.entries)>self.capacity:self.entries.popitem(last=False)
            future.set_result(saved)
            return deepcopy(saved)
        except BaseException as error:
            future.set_exception(error)
            raise
        finally:
            with self.lock:self.flights.pop(key,None)

def cache_key(tenant_id,resource_id,representation='summary-v1'):
    if type(tenant_id) is not int or tenant_id<1 or type(resource_id) is not str:
        raise ValueError('invalid cache scope')
    return ('catalog',tenant_id,resource_id,representation)
