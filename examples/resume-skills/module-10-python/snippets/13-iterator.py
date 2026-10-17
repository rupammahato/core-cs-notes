values = [1, 2]
it = iter(values)
print(iter(it) is it, next(it))
print(list(it), list(it))
print(list(values), list(values))
try:
    next(it)
except StopIteration:
    print('exhausted')
