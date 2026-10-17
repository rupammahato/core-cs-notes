def bad(value, items=[]):
    items.append(value)
    return items
first = bad('a')
second = bad('b')
print(first, second, first is second)
def good(value, items=None):
    if items is None:
        items = []
    items.append(value)
    return items
print(good('a'), good('b'))
