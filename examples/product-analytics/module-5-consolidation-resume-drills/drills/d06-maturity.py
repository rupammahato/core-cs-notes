from datetime import datetime,timedelta,timezone
from decimal import Decimal
import json
cohorts={'u1':'2026-10-01','u2':'2026-10-02','u3':'2026-10-08'}
cutoff=datetime(2026,10,10,tzinfo=timezone.utc)
mature=[key for key,date in cohorts.items() if datetime.fromisoformat(date).replace(tzinfo=timezone.utc)+timedelta(days=7)<cutoff]
returned={'u1'}
n=len(returned.intersection(mature))
print(json.dumps({'mature_users':len(mature),'returned_mature_users':n,
 'rate_pct':format(Decimal(n)/len(mature)*100,'.6f'),
 'wrong_all_users_pct':format(Decimal(n)/len(cohorts)*100,'.6f')}))
