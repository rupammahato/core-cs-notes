from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
barrier = Barrier(2, timeout=5)
state = {'value': 0}
def unsafe():
    old = state['value']
    barrier.wait()  # Both threads read before either writes.
    state['value'] = old + 1
with ThreadPoolExecutor(max_workers=2) as pool:
    jobs = [pool.submit(unsafe) for _ in range(2)]
    for job in jobs:
        job.result(timeout=10)
print('unsynchronized:', state['value'])
state['value'] = 0
lock = Lock()
def safe():
    for _ in range(1000):
        with lock:
            state['value'] += 1
with ThreadPoolExecutor(max_workers=2) as pool:
    jobs = [pool.submit(safe) for _ in range(2)]
    for job in jobs:
        job.result(timeout=10)
print('locked:', state['value'])
