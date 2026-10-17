count = 10
def broken():
    count += 1
try:
    broken()
except UnboundLocalError:
    print('local read before binding')
def counter():
    value = 0
    def next_value():
        nonlocal value
        value += 1
        return value
    return next_value
next_value = counter()
print(next_value(), next_value(), count)
