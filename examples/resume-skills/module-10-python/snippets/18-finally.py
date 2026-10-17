def broken():
    try:
        raise ValueError('lost')
    finally:
        return 'masked'
print(broken())
