class InvalidQuantity(ValueError):
    pass
def parse(text):
    try:
        return int(text)
    except ValueError as exc:
        raise InvalidQuantity('quantity must be an integer') from exc
try:
    parse('many')
except InvalidQuantity as exc:
    print(str(exc))
    print(type(exc.__cause__).__name__)
