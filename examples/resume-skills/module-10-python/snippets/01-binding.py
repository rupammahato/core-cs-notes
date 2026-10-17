def change(items):
    items.append('accepted')
    items = ['local']
a = ['request']
b = a
change(a)
print(a, b, a is b)
x = 4
y = x
x += 1
print(x, y)
