from concurrent.futures import ThreadPoolExecutor
from threading import Barrier,Event
from cache import TTLCache,cache_key
from checks import Checks,equal,require,rejects

checks=Checks('cache');observed={}
def reuse():
    calls=[];cache=TTLCache()
    def load():calls.append(1);return {'value':7}
    equal(cache.get_or_load('a',load),{'value':7});equal(cache.get_or_load('a',load),{'value':7});equal(len(calls),1)
checks.check('hit reuses a loaded value without another primary read',reuse)
def expiry():
    now=[0];cache=TTLCache(clock=lambda:now[0]);calls=[]
    def load():calls.append(1);return len(calls)
    equal(cache.get_or_load('a',load),1);now[0]=10;equal(cache.get_or_load('a',load),2)
    observed['expiry']={'deadline':10,'loads':len(calls)}
checks.check('manual monotonic clock expires at the exact configured boundary',expiry)
def negative():
    now=[0];calls=[];cache=TTLCache(clock=lambda:now[0])
    def load():calls.append(1);return None
    cache.get_or_load('a',load);now[0]=1;cache.get_or_load('a',load);equal(len(calls),1)
    now[0]=2;cache.get_or_load('a',load);equal(len(calls),2)
checks.check('negative lookup uses its shorter independent TTL',negative)
def scoped():
    cache=TTLCache();equal(cache.get_or_load(cache_key(1,'same'),lambda:'alpha'),'alpha')
    equal(cache.get_or_load(cache_key(2,'same'),lambda:'beta'),'beta')
    require(cache_key(1,'same','v1')!=cache_key(1,'same','v2'))
checks.check('tenant and representation participate in cache identity',scoped)
checks.check('invalid trusted scope including boolean tenant is rejected',lambda:rejects(ValueError,lambda:cache_key(True,'a')))
def capacity():
    cache=TTLCache(capacity=2)
    for key in ('a','b','a','c'):cache.get_or_load(key,lambda:key)
    equal(list(cache.entries),['a','c'])
checks.check('bounded entries evict the least recently used member',capacity)
def copying():
    source={'items':[1]};cache=TTLCache();first=cache.get_or_load('a',lambda:source)
    first['items'].append(2);source['items'].append(3)
    equal(cache.get_or_load('a',lambda:None),{'items':[1]})
checks.check('caller and loader mutations cannot modify the saved value',copying)
def collapse():
    cache=TTLCache();gate=Barrier(8);entered=Event();release=Event();calls=[]
    def load():calls.append(1);entered.set();require(release.wait(5));return 9
    def worker(_):gate.wait(5);return cache.get_or_load('a',load)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(worker,i) for i in range(8)]
        try:
            require(entered.wait(5))
            with cache.changed:require(cache.changed.wait_for(lambda:cache.stats['waits']==7,timeout=5))
        finally:release.set()
        equal([future.result(5) for future in futures],[9]*8)
    equal(len(calls),1);observed['single_flight']={'callers':8,'loads':1,'waiting_followers':cache.stats['waits']}
checks.check('eight coordinated callers share one load with seven observed waiters',collapse)
def failed_loader():
    cache=TTLCache()
    def fail():raise ValueError('source unavailable')
    rejects(ValueError,lambda:cache.get_or_load('a',fail))
    equal(cache.get_or_load('a',lambda:5),5);equal(cache.flights,{})
checks.check('failed load clears its flight and is not cached',failed_loader)
def late_fill():
    cache=TTLCache();entered=Event();release=Event();source=[1]
    def load():
        old=source[0];entered.set();require(release.wait(5));return old
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(cache.get_or_load,'a',load)
        try:require(entered.wait(5));source[0]=2;cache.invalidate('a')
        finally:release.set()
        equal(future.result(5),1)
    equal(cache.get_or_load('a',lambda:source[0]),2)
    observed['invalidation_race']={'in_flight_response':1,'next_read':2,'old_value_repopulated':False}
checks.check('invalidation generation prevents a late old load from repopulating cache',late_fill)
checks.save(observations=observed,scope='Process-local algorithm with manual TTL clock and actual threads; no Redis/network test')
