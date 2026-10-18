from decimal import Decimal
import json
costs=[60,60,60,120]
states=['success','success','success','failed']
successes=states.count('success')
print(json.dumps({'all_cost_cents':sum(costs),'successes':successes,
 'cost_per_success_cents':float(Decimal(sum(costs))/successes),
 'wrong_success_only_cents':float(Decimal(sum(c for c,s in zip(costs,states) if s=='success'))/successes)}))
