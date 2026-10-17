from functools import wraps
calls = []
def trace(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        calls.append(fn.__name__)
        return fn(*args, **kwargs)
    return wrapper
@trace
def total(a, b=2):
    return a + b
print(total(3), total.__name__, calls)
print(total.__wrapped__(4, 5))
