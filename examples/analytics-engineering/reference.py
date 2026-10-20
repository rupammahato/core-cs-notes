"""Independent Python map/date oracle; executes no SQL and reads no saved answers."""
from collections import defaultdict
import json


def expected(changes):
    identities=defaultdict(list)
    for change in changes:
        key=(change['stream'],change['tenant_id'],change['entity_id'],change['source_version'])
        identities[key].append(change)
    blocked={key[:3] for key,values in identities.items() if len({json.dumps(v['payload'],sort_keys=True) for v in values})>1}
    valid=[values[0] for key,values in identities.items() if key[:3] not in blocked]
    history=defaultdict(dict)
    orders={}
    for change in valid:
        key=(change['tenant_id'],change['entity_id'])
        p=change['payload']
        if change['stream']=='customers':
            day=p['effective_from'];old=history[key].get(day)
            if old is None or change['source_version']>old['source_version']:history[key][day]=change
        elif key not in orders or change['source_version']>orders[key]['source_version']:
            orders[key]=change
    dimensions=[]
    for (tenant,customer),versions in sorted(history.items()):
        dates=sorted(versions)
        for index,day in enumerate(dates):
            dimensions.append({'tenant_id':tenant,'customer_id':customer,'valid_from':day,
                               'valid_to':dates[index+1] if index+1<len(dates) else None,
                               'plan':versions[day]['payload']['plan']})
    facts=[];groups={}
    for (tenant,order),change in sorted(orders.items()):
        p=change['payload']
        if p['op']=='D':continue
        versions=history.get((tenant,p['customer_id']),{})
        applicable=[day for day in versions if day<=p['order_day']]
        plan=versions[max(applicable)]['payload']['plan'] if applicable else 'Unknown'
        facts.append({'tenant_id':tenant,'order_id':order,'customer_id':p['customer_id'],
                      'order_day':p['order_day'],'billed_cents':p['billed_cents'],
                      'status':p['status'],'source_version':change['source_version'],'plan':plan})
        if p['status']!='paid':continue
        key=(tenant,p['order_day'],plan)
        if key not in groups:groups[key]={'paid_orders':0,'known_bill_cents':0,'missing_bills':0}
        group=groups[key];group['paid_orders']+=1
        if p['billed_cents'] is None:group['missing_bills']+=1
        else:group['known_bill_cents']+=p['billed_cents']
    mart=[]
    for (tenant,day,plan),group in sorted(groups.items()):
        mart.append({'tenant_id':tenant,'order_day':day,'plan':plan,**group,
                     'complete_bill_cents':None if group['missing_bills'] else group['known_bill_cents']})
    return {'facts':facts,'dimensions':dimensions,'mart':mart,'blocked':sorted(blocked)}
