from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
import json
print(0.1 + 0.2 == 0.3)
print(Decimal('0.1') + Decimal('0.2') == Decimal('0.3'))
print(Decimal('2.675').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
text = '₹'
raw = text.encode('utf-8')
print(len(text), len(raw), raw.decode('utf-8') == text)
stamp = datetime.fromisoformat('2026-10-14T12:00:00+05:30')
print(stamp.astimezone(timezone.utc).isoformat())
print(json.dumps({'amount_paise': 12500}, sort_keys=True))
