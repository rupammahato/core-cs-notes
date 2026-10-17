from typing import TypedDict
class Body(TypedDict):
    quantity: int
def echo(quantity: int) -> int:
    return quantity
body: Body = {'quantity': 'many'}
print(echo(body['quantity']))
print(isinstance(body, dict))
print(echo.__annotations__['quantity'] is int)
