from decimal import Decimal
import json
control=Decimal(20)/100;treatment=Decimal(24)/100
print(json.dumps({'control_pct':str(control*100),'treatment_pct':str(treatment*100),
 'absolute_lift_pp':str((treatment-control)*100),
 'relative_lift_pct':str((treatment/control-1)*100)}))
