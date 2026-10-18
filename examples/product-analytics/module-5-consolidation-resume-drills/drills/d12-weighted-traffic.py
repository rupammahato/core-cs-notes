from decimal import Decimal
import json
traffic={'k1':900,'k2':20,**{f'k{i}':10 for i in range(3,11)}}
moved={'k1'}
print(json.dumps({'keys':len(traffic),'moved_keys':len(moved),'requests':sum(traffic.values()),
 'moved_requests':sum(traffic[key] for key in moved),
 'moved_key_pct':float(Decimal(len(moved))/len(traffic)*100),
 'moved_traffic_pct':float(Decimal(sum(traffic[key] for key in moved))/sum(traffic.values())*100)}))
