from datetime import datetime, timezone
import json

value = datetime.fromisoformat('2026-10-16T10:00:00+05:30')
print(json.dumps({'utc': value.astimezone(timezone.utc).isoformat()}))
