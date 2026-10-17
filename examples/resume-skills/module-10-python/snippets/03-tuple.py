value = (['a'],)
try:
    value[0] += ['b']
except TypeError:
    print('assignment rejected')
print(value)
try:
    hash(value)
except TypeError:
    print('unhashable')
