MISSING = object()
data = {'limit': 0, 'note': None}
print(data.get('limit') or 20)
print(20 if data.get('limit') is None else data['limit'])
print(data.get('note', MISSING) is None)
print(data.get('unknown', MISSING) is MISSING)
print(bool([]), bool('False'))
