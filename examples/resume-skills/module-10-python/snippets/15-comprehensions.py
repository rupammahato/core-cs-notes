seen = []
def mark(x):
    seen.append(x)
    return x * x
eager = [mark(x) for x in range(3)]
print(eager, seen)
seen.clear()
lazy = (mark(x) for x in range(3))
print(seen)
print(next(lazy), seen)
print(sum(lazy), seen)
