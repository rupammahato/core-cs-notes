def stream():
    print('start')
    try:
        yield 10
        yield 20
    finally:
        print('cleanup')
gen = stream()
print('created')
print(next(gen))
gen.close()
print(list(gen))
