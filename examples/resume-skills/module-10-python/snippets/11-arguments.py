def route(resource, /, *, limit=20, **options):
    return resource, limit, sorted(options)
print(route('orders', limit=5, trace=True))
try:
    route(resource='orders')
except TypeError:
    print('positional-only argument required')
try:
    route('orders', 5)
except TypeError:
    print('limit must be keyword')
