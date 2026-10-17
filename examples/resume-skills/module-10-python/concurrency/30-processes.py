import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
def squares(n):
    return os.getpid(), sum(x * x for x in range(n))
def append_copy(values):
    values.append('child')
    return values
if __name__ == '__main__':
    context = multiprocessing.get_context('spawn')
    original = ['parent']
    with ProcessPoolExecutor(max_workers=2, mp_context=context) as pool:
        rows = list(pool.map(squares, [5, 9]))
        copied = pool.submit(append_copy, original).result(timeout=10)
    assert all(pid != os.getpid() for pid, value in rows)
    assert original == ['parent'] and copied == ['parent', 'child']
    print('method:', context.get_start_method())
    print('results:', [value for pid, value in rows])
    print('parent:', original, 'child:', copied)
