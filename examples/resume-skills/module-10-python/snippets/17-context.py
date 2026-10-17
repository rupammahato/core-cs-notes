from contextlib import contextmanager
@contextmanager
def resource():
    print('open')
    try:
        yield 'handle'
    finally:
        print('close')
try:
    with resource() as handle:
        print(handle)
        raise ValueError('failed')
except ValueError:
    print('propagated')
