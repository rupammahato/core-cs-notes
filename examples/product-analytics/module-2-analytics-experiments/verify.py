"""Run the SQLite worksheet and test time, identity, denominator and experiment boundaries."""
from copy import deepcopy
import json
import math
from pathlib import Path
import platform
import random
import sqlite3
from analytics import activity, dataset, demo, experiment, percentage, report, timestamp

BASE = Path(__file__).resolve().parent
case = json.loads((BASE/'case.json').read_text())
checks = []


def check(group,name,actual,expected):
    assert actual == expected,(name,actual,expected)
    checks.append({'group':group,'name':name,'passed':True})


def rejects(group,name,function):
    try:
        function()
    except ValueError:
        checks.append({'group':group,'name':name,'passed':True})
    else:
        raise AssertionError(name)


def open_once(changed):
    with dataset(changed):
        pass


def initial_report(changed):
    with dataset(changed) as (db,_):
        return report(db,changed['event_cutoff'],changed['initial_knowledge_cutoff'])


check('time','equivalent timezone normalization',timestamp('2026-10-01T05:30:00+05:30'),timestamp('2026-10-01T00:00:00Z'))
for value in ['2026-10-01T00:00:00','not-a-date','2026-10-01T00:00:00.1Z',None]:
    rejects('time','invalid timestamp '+repr(value),lambda value=value:timestamp(value))
check('denominator','empty ratio is undefined',percentage(0,0),None)
check('denominator','two of five',percentage(2,5),'40.000000')
output = demo(case)
check('intake','exact duplicate report ignored',output['intake']['duplicate_reports_ignored'],1)
check('intake','unique stored events',output['intake']['stored_events'],28)
first=output['initial']; revised=output['revised']
for name,field,value in [('mature activation denominator','eligible',5),('immature users excluded','immature_excluded',2),
                         ('users with starts','started',5),('ordered complete users','completed',2),
                         ('activation rate','rate_pct','40.000000'),('conditional last-step rate','start_to_complete_pct','40.000000')]:
    check('funnel',name,first['activation'][field],value)
check('late-data','activation remains fixed after late D7 return',revised['activation'],first['activation'])
for name,key,value in [('mature retention denominator','eligible',5),('initial returns','returned',2),('initial retention','rate_pct','40.000000')]:
    check('retention',name,first['retention'][key],value)
check('late-data','late return changes numerator',revised['retention']['returned'],3)
check('late-data','revised exact D7 retention',revised['retention']['rate_pct'],'60.000000')
check('retention','first cohort counts',revised['retention']['cohorts']['2026-10-01'],{'eligible':3,'returned':1,'rate_pct':'33.333333'})
check('retention','second cohort counts',revised['retention']['cohorts']['2026-10-02'],{'eligible':2,'returned':2,'rate_pct':'100.000000'})
check('activity','two events are one active user',output['activity_oct_8'],{'events':2,'active_users':1})
with dataset(case) as (db,_):
    rows=report(db,case['event_cutoff'],case['initial_knowledge_cutoff'])
    check('identity','alias does not add signup users',rows['visible_signup_users'],7)
    check('funnel','per-user completion truth table',[(r['subject'],r['completed']) for r in rows['users']],
          [('u1',1),('u2',0),('u3',0),('u4',0),('u5',1),('u6',1),('u7',0)])
    check('maturity','converted immature user still excluded',next(r for r in rows['users'] if r['subject']=='u6')['activation_mature'],0)
    check('retention','D1 measures another interval',report(db,case['event_cutoff'],case['revised_knowledge_cutoff'],1)['retention']['returned'],2)
    check('activity','late event absent in initial day',activity(db,'2026-10-09',case['event_cutoff'],case['initial_knowledge_cutoff']),{'events':1,'active_users':1})
    check('activity','late event included in revised day',activity(db,'2026-10-09',case['event_cutoff'],case['revised_knowledge_cutoff']),{'events':2,'active_users':2})
    rejects('time','incomplete activity day',lambda:activity(db,'2026-10-11',case['event_cutoff'],case['revised_knowledge_cutoff']))
    rejects('time','knowledge cannot precede event cutoff',lambda:report(db,case['event_cutoff'],'2026-10-10T00:00:00Z'))
    for day in [-1,True,1.5,366]:
        rejects('time','invalid retention day '+repr(day),lambda day=day:report(db,case['event_cutoff'],case['initial_knowledge_cutoff'],day))
try:
    db.execute('SELECT 1')
except sqlite3.ProgrammingError:
    check('cleanup','in-memory database closed',True,True)
else:
    raise AssertionError('Database left open')

changed=deepcopy(case)
next(e for e in changed['events'] if e['id']=='c4')['occurred_at']='2026-10-02T23:59:59Z'
check('boundaries','one second before conversion-window end counts',initial_report(changed)['activation']['completed'],3)
changed=deepcopy(case);changed['events']=[e for e in changed['events'] if e['id']!='c5']
check('boundaries','orphan early success does not complete funnel',initial_report(changed)['activation']['completed'],1)
next(e for e in changed['events'] if e['id']=='early5')['operation']='op5'
check('boundaries','same operation before start still does not complete',initial_report(changed)['activation']['completed'],1)
changed=deepcopy(case);next(e for e in changed['events'] if e['id']=='c5')['occurred_at']='2026-10-02T01:00:00Z'
check('boundaries','equal whole-second timestamps use nondecreasing order',initial_report(changed)['activation']['completed'],2)
changed=deepcopy(case);changed['users'][-1]['internal']=False
check('exclusion','internal flag changes denominator intentionally',initial_report(changed)['activation']['eligible'],6)
changed=deepcopy(case);changed['events']=[]
check('empty','no signup cohort has undefined activation',initial_report(changed)['activation']['rate_pct'],None)
check('empty','no cohort has undefined retention',initial_report(changed)['retention']['rate_pct'],None)
for seed in [1,17,42]:
    changed=deepcopy(case);random.Random(seed).shuffle(changed['events'])
    check('ordering','arrival list order does not change report '+str(seed),demo(changed),output)

for label,field,value in [('unknown event','name','clicked_secret'),('unknown user','subject','missing'),
                          ('bad schema','version',2),('boolean schema','version',True),
                          ('missing ID','id',''),('signup operation','operation','not-applicable')]:
    changed=deepcopy(case);changed['events'][0][field]=value
    rejects('ingest',label,lambda changed=changed:open_once(changed))
changed=deepcopy(case);changed['events'][7]['operation']=None
rejects('ingest','generation requires operation',lambda:open_once(changed))
changed=deepcopy(case);changed['events'][0]['received_at']='2026-09-30T23:59:59Z'
rejects('ingest','receipt-before-occurrence rejected by fixture',lambda:open_once(changed))
changed=deepcopy(case);changed['events'][0]['properties']['email']='private@example.test'
rejects('ingest','unapproved property rejected',lambda:open_once(changed))
changed=deepcopy(case);changed['events'][0]['properties']['device']='unknown'
rejects('ingest','unapproved property value rejected',lambda:open_once(changed))
changed=deepcopy(case);changed['events'][-1]['properties']['device']='desktop'
rejects('ingest','conflicting duplicate not silently dropped',lambda:open_once(changed))
changed=deepcopy(case);changed['users'].append(changed['users'][0])
rejects('identity','duplicate canonical user',lambda:open_once(changed))
changed=deepcopy(case);changed['aliases']['anon-1']='missing'
rejects('identity','alias to missing canonical user',lambda:open_once(changed))
changed=deepcopy(case);changed['aliases']['u1']='u2'
rejects('identity','canonical user cannot be an alias',lambda:open_once(changed))

exp=output['experiment']
for name,key,value in [('control rate','control_rate_pct','20.000000'),('treatment rate','treatment_rate_pct','24.000000'),
                       ('absolute percentage points','absolute_lift_pp','4.000000'),('relative percentage','relative_lift_pct','20.000000'),
                       ('normal count rule','normal_approximation_adequate_for_fixture',True),
                       ('approximate interval','approx_95_ci_pp',['0.373272','7.626728']),
                       ('balanced assignment statistic','srm_chi_square',0.0),('balanced assignment p','srm_p_value',1.0),
                       ('no assignment proof','assignment_verified',False)]:
    check('experiment',name,exp[key],value)
check('experiment','pooled two-sided p reference',abs(exp['two_sided_p_value']-0.030837167828904336)<1e-12,True)
check('experiment','equal rates give p one',experiment(1000,200,1000,200)['two_sided_p_value'],1.0)
check('experiment','swapping groups reverses lift',experiment(1000,240,1000,200)['absolute_lift_pp'],'-4.000000')
check('experiment','swapping groups preserves two-sided p',experiment(1000,240,1000,200)['two_sided_p_value'],exp['two_sided_p_value'])
small=experiment(10,2,10,3)
check('experiment','small-count interval withheld',small['approx_95_ci_pp'],None)
check('experiment','small-count p withheld',small['two_sided_p_value'],None)
check('experiment','zero baseline has undefined relative lift',experiment(100,0,100,10)['relative_lift_pct'],None)
check('experiment','all successes do not create zero-width normal interval',experiment(100,100,100,100)['approx_95_ci_pp'],None)
check('srm','imbalance statistic',output['imbalanced_assignment']['srm_chi_square'],100.0)
check('srm','imbalance triggers declared guard',output['imbalanced_assignment']['srm_flag_at_0_001'],True)
check('srm','imbalanced p is tiny not silently rounded zero',0<output['imbalanced_assignment']['srm_p_value']<1e-20,True)
check('srm','allocation follows expected share',experiment(1000,200,600,144,0.375)['srm_chi_square'],0.0)
check('srm','tiny expected counts withhold approximation',experiment(1,0,1,1)['srm_p_value'],None)
for args in [(0,0,100,20),(100,101,100,20),(True,0,100,20),(100,-1,100,20),(100,20,100.5,20)]:
    rejects('experiment-input',repr(args),lambda args=args:experiment(*args))
for share in [0,1,True,float('nan'),float('inf')]:
    rejects('experiment-input','invalid allocation '+repr(share),lambda share=share:experiment(100,20,100,20,share))
snapshot=deepcopy(case);demo(case)
check('boundary','input event evidence unchanged',case,snapshot)
check('boundary','synthetic scope retained',output['scope'],case['scope'])
proof={'verified_date':'2026-10-18','python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
       'os':platform.platform(),'total':len(checks),'checks':checks,'observations':output,
       'external_services_called':False,'persistent_listener_started':False,'database_closed':True,
       'scope':'Real local SQLite on synthetic events, input/time/identity/cohort checks and aggregate normal-approximation/SRM arithmetic. No vendor account, customer telemetry or real experiment.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
(BASE/'analytics-output.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'python':proof['python'],'sqlite':proof['sqlite'],
                  'activation':first['activation'],'initial_D7':first['retention']['rate_pct'],
                  'revised_D7':revised['retention']['rate_pct'],'experiment':exp},indent=2))
