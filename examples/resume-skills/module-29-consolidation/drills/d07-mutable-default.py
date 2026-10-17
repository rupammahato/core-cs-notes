import json

def add(value, items=[]):
    items.append(value)
    return items

first = add('a')
second = add('b')
print(json.dumps({'first': first, 'second': second, 'same': first is second}))
