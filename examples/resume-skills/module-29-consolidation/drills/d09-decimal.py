from decimal import Decimal
import json

print(json.dumps({'binary_float': str(0.1 + 0.2), 'decimal': str(Decimal('0.1') + Decimal('0.2'))}))
