from collections import deque
items = [3, 1, 2]
print(items.sort(), items)
print(items[-1], items[::2])
queue = deque(['a', 'b'])
print(queue.popleft(), list(queue))
rows = [('first', 2), ('second', 1), ('third', 2)]
print(sorted(rows, key=lambda row: row[1]))
print(sorted(set(['api', 'db', 'api'])))
