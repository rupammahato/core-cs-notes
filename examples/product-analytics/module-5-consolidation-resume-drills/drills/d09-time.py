from datetime import datetime,timezone
import json
parse=lambda value:datetime.fromisoformat(value.replace('Z','+00:00'))
start=parse('2026-10-01T00:00:00Z');end=parse('2026-11-01T00:00:00Z')
rows={'offset':parse('2026-10-01T00:30:00+05:30'),'middle':parse('2026-10-15T00:00:00Z'),'endpoint':end}
print(json.dumps({'included':[key for key,value in rows.items() if start<=value<end],
 'offset_utc':rows['offset'].astimezone(timezone.utc).isoformat(),
 'end_excluded':not(start<=end<end)}))
