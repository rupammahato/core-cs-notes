"""Independent expected arithmetic, attribution boundaries and publication cases."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
import platform
import sqlite3
from measurement import BASE, build, campaign_report, attribute, claim_overlap, ratio, unique, instant, DigestStore

checks=[]
def check(group,name,actual,expected):
    assert actual==expected,(name,actual,expected)
    checks.append({'group':group,'name':name,'passed':True})

def rejects(group,name,call):
    try:call()
    except (ValueError,TypeError):checks.append({'group':group,'name':name,'passed':True})
    else:raise AssertionError(name+' did not reject')

source=(BASE/'case.json').read_bytes();case=json.loads(source);before=deepcopy(case)
output=build(case);report=output['platform_report'];metrics=report['blended_metrics']
for name,expected in [('ctr_pct',1.333333),('cpm_cents',1000.0),('cpc_cents',75.0),
                      ('purchase_credit_rate_pct',2.0),('cost_per_purchase_credit_cents',3750.0),('reported_roas',2.666667)]:
    check('metrics',name,metrics[name],expected)
for name,expected in [('spend_cents',15000),('impressions',15000),('clicks',200),
                      ('conversion_credits',4.0),('attributed_value_cents',40000)]:
    check('totals',name,report['totals'][name]['complete'],expected)
check('metrics','Wrong mean of CTR percentages',report['wrong_unweighted_ctr_pct'],1.5)
check('dedupe','Exact repeated campaign removed',len(report['campaigns']),2)
for name,expected in [('orders',4),('new_customers_supplied',3),('gross_cents',47000),('refund_cents',5000),
                      ('net_cents',42000),('blended_net_revenue_per_media_spend',2.8),
                      ('media_spend_per_supplied_new_customer_cents',5000.0)]:
    check('ledger',name,output['ledger'][name],expected)
check('attribution','Click-only allocation',output['last_eligible_click_7d']['by_campaign_net_cents'],
      {'A':5000,'B':10000,'Unattributed':27000})
check('attribution','Click then view fallback allocation',output['click_7d_else_view_1d']['by_campaign_net_cents'],
      {'A':20000,'B':10000,'Unattributed':12000})
check('attribution','Post-order touch not used',output['click_7d_else_view_1d']['assignments'][1]['touch_id'],'t4')
check('attribution','Click takes priority over later view',output['click_7d_else_view_1d']['assignments'][2]['touch_id'],'t6')
for name in ['last_eligible_click_7d','click_7d_else_view_1d']:
    check('attribution',name+' conserves net ledger',sum(output[name]['by_campaign_net_cents'].values()),42000)
    check('attribution',name+' one assignment per order',len({r['order_id'] for r in output[name]['assignments']}),4)
for name,expected in [('claim_rows',4),('unique_claimed_orders',3),('summed_claim_value_cents',40000),
                      ('unique_claimed_net_cents',30000),('overlap_cents',10000)]:
    check('claims',name,output['independent_claim_overlap'][name],expected)
orders=case['orders'][:1];touches=[case['touches'][0]];campaigns=report['campaigns']
check('boundary','Exactly seven days included',attribute(orders,touches,campaigns)['assignments'][0]['touch_id'],'t1')
changed=deepcopy(touches);changed[0]['at']='2026-10-03T11:59:59Z'
check('boundary','One second outside window excluded',attribute(orders,changed,campaigns)['assignments'][0]['touch_id'],None)
changed=deepcopy(touches);changed[0]['at']='2026-10-10T12:00:01Z'
check('boundary','Future click excluded',attribute(orders,changed,campaigns)['assignments'][0]['touch_id'],None)
changed=deepcopy(touches);changed[0]['at']='2026-10-10T12:00:00Z'
check('boundary','Same instant click included',attribute(orders,changed,campaigns)['assignments'][0]['touch_id'],'t1')
changed=deepcopy(touches);changed[0]['kind']='view';changed[0]['at']='2026-10-09T12:00:00Z'
check('boundary','Exactly one-day view included',attribute(orders,changed,campaigns,view_days=1)['assignments'][0]['touch_id'],'t1')
changed[0]['at']='2026-10-09T11:59:59Z'
check('boundary','Outside one-day view excluded',attribute(orders,changed,campaigns,view_days=1)['assignments'][0]['touch_id'],None)
changed=deepcopy(case);changed['touches'].append(deepcopy(changed['touches'][0]))
check('dedupe','Repeated touch does not double credit',build(changed)['last_eligible_click_7d'],output['last_eligible_click_7d'])
changed=deepcopy(case);changed['orders'].append(deepcopy(changed['orders'][0]))
check('dedupe','Repeated order does not double money',build(changed)['ledger'],output['ledger'])
changed=deepcopy(case);changed['campaigns']=changed['campaigns'][:2];changed['campaigns'][1]['spend_cents']=None
r=build(changed)
check('missing','Known spend subtotal remains',r['platform_report']['totals']['spend_cents']['known'],10000)
check('missing','Missing spend row visible',r['platform_report']['totals']['spend_cents']['missing_rows'],1)
check('missing','Incomplete spend withheld',r['platform_report']['totals']['spend_cents']['complete'],None)
check('missing','Incomplete spend withholds ROAS',r['platform_report']['blended_metrics']['reported_roas'],None)
check('missing','Incomplete spend withholds acquisition ratio',r['ledger']['media_spend_per_supplied_new_customer_cents'],None)
for row in changed['campaigns']:row['spend_cents']=None
check('missing','All-missing known subtotal remains unknown',build(changed)['platform_report']['totals']['spend_cents']['known'],None)
changed=deepcopy(case);changed['campaigns']=changed['campaigns'][:2];changed['campaigns'][1]['conversion_credits']='0.5'
check('metrics','Fractional conversion credit preserved',build(changed)['platform_report']['totals']['conversion_credits']['complete'],2.5)
check('metrics','Zero denominator is undefined',ratio(1,0),None)
check('metrics','Known zero numerator is zero',ratio(0,10),0.0)
check('metrics','Missing numerator is unknown',ratio(None,10),None)
check('metrics','Empty report is not known zero spend',campaign_report([])['totals']['spend_cents']['complete'],None)
for field,value in [('spend_cents',-1),('clicks',True),('impressions',1.5),('conversion_credits','NaN'),('conversion_credits','bad')]:
    changed=deepcopy(case);changed['campaigns']=changed['campaigns'][:2];changed['campaigns'][0][field]=value
    rejects('validation','Reject '+field+' '+str(value),lambda:build(changed))
for collection,key,field,value in [('campaigns','campaign_id','spend_cents',999),('orders','order_id','gross_cents',999),
                                 ('touches','touch_id','kind','view')]:
    changed=deepcopy(case);extra=deepcopy(changed[collection][0]);extra[field]=value;changed[collection].append(extra)
    rejects('validation','Conflicting '+key,lambda:build(changed))
for field,value in [('currency','EUR'),('timezone','Europe/London')]:
    changed=deepcopy(case);changed['contract'][field]=value
    rejects('validation','Explicit normalization required for '+field,lambda:build(changed))
changed=deepcopy(case);changed['orders'][0]['refund_cents']=10001
rejects('validation','Refund cannot exceed gross under this schema',lambda:build(changed))
changed=deepcopy(case);changed['touches'][0]['campaign_id']='unknown'
rejects('validation','Unknown campaign',lambda:build(changed))
rejects('validation','Naive timestamp',lambda:instant('2026-10-10T00:00:00'))
rejects('validation','Nonpositive attribution window',lambda:attribute(orders,touches,campaigns,click_days=0))
rejects('validation','Duplicate claim',lambda:claim_overlap(case['orders'],case['independent_claims']+[case['independent_claims'][0]]))
rejects('validation','Claim without canonical order',lambda:claim_overlap(case['orders'],[{'campaign_id':'A','order_id':'missing'}]))
store=DigestStore()
try:
    check('publication','Initial publish',store.publish('demo:USD:UTC:2026-10-11',1,{'net':42000}),'published')
    check('publication','Retry is duplicate',store.publish('demo:USD:UTC:2026-10-11',1,{'net':42000}),'duplicate')
    check('publication','One row after retry',store.db.execute('SELECT count(*) FROM digest').fetchone()[0],1)
    rejects('publication','Conflicting same revision',lambda:store.publish('demo:USD:UTC:2026-10-11',1,{'net':43000}))
    check('publication','Conflict preserves published body',json.loads(store.db.execute('SELECT body FROM digest').fetchone()[0]),{'net':42000})
    check('publication','New revision replaces snapshot',store.publish('demo:USD:UTC:2026-10-11',2,{'net':43000}),'published')
    rejects('publication','Stale revision rejected',lambda:store.publish('demo:USD:UTC:2026-10-11',1,{'net':42000}))
    check('publication','Revision remains latest',store.db.execute('SELECT revision FROM digest').fetchone()[0],2)
    rejects('publication','Invalid revision',lambda:store.publish('demo',0,{}))
finally:store.close()
check('preservation','Input objects unchanged',case,before)
check('preservation','Input file unchanged',(BASE/'case.json').read_bytes(),source)
proof={'verified_date':'2026-10-18','python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
       'total':len(checks),'checks':checks,'observations':output,'source_sha256':hashlib.sha256(source).hexdigest(),
       'external_services_called':False,'persistent_listener_started':False,'database_closed':True,
       'scope':'Actual synthetic arithmetic, hand-defined attribution, overlap and in-memory SQLite publication; no vendor parity, causal lift or delivery claim.'}
(BASE/'measurement-output.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'python':proof['python'],'sqlite':proof['sqlite'],'metrics':metrics,
                  'ledger':output['ledger'],'overlap':output['independent_claim_overlap']},indent=2))
