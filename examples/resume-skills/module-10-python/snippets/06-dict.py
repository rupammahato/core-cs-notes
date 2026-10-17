data = {'a': 1, 'b': 2}
data['a'] = 3
print(list(data))
del data['a']
data['a'] = 4
print(list(data))
print({('tenant', 7): 'row'}[('tenant', 7)])
try:
    data[[]] = 1
except TypeError:
    print('list key rejected')
