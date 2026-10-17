late = [lambda: i for i in range(3)]
early = [lambda i=i: i for i in range(3)]
print([fn() for fn in late])
print([fn() for fn in early])
