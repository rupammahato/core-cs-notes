"""Run independent expectations and mutation cases against actual NumPy/pandas operations."""
from pathlib import Path
import json
import platform
import numpy as np
import pandas as pd
from analysis import analyze,load_sources,numpy_examples

BASE=Path(__file__).resolve().parent
jobs,attempts,workspaces=load_sources()
checks=[]


def check(group,name,actual,expected):
    assert actual==expected,(name,actual,expected)
    checks.append({'group':group,'name':name,'passed':True})


def rejects(group,name,function,exception=ValueError):
    try:function()
    except exception:checks.append({'group':group,'name':name,'passed':True})
    else:raise AssertionError(name)


report,prepared=analyze(jobs,attempts,workspaces)
arr=numpy_examples()
for name,key,value in [('shape','shape',[2,3]),('fixed dtype','dtype','int64'),
    ('broadcasting','broadcast_product',[[20,60,120],[2,6,12]]),('column reduction','column_sums',[11,22,33]),
    ('row reduction','row_sums',[60,6]),('weighted rows','weighted_rows',[200,20]),
    ('matrix-vector product','matrix_vector',[200,20]),('basic slice changes original','original_after_slice_edit',[1,99,3,4]),
    ('advanced indexing copy','fancy_copy_after_edit',[-1,3])]:check('numpy',name,arr[key],value)
rejects('numpy','incompatible trailing shapes',lambda:np.ones((2,3))*np.ones((2,)))
base=np.arange(6);check('numpy','slice shares memory',np.shares_memory(base,base[1:3]),True)
check('numpy','fancy indexing does not share memory',np.shares_memory(base,base[[1,3]]),False)
for name,key,value in [('raw rows','raw_job_rows',10),('job deduplication','deduplicated_jobs',9),
    ('raw attempt rows','raw_attempt_rows',10),('attempt deduplication','deduplicated_attempts',9),
    ('date issues retained','date_issue_jobs',['0007','0008']),('known boundary exclusions','excluded_known_date_jobs',['0001','0006']),
    ('cohort keys','selected_job_ids',['0002','0003','0004','0005','0009']),('selected count','selected_jobs',5),
    ('completed count','completed_jobs',4),('completed share','completion_share',0.8),
    ('known billing subtotal','known_billed_cents',290),('missing billing count','missing_billed_jobs',2),
    ('complete bill withheld','complete_billed_cents',None),('provider subtotal','known_provider_cents',110),
    ('complete provider amount','complete_provider_cents',110),('unknown dimension retained','unmapped_selected_jobs',['0009']),
    ('orphan source identity','orphan_attempts',['a09']),('unassigned known amount','orphan_cost_cents',7),
    ('bad join row inflation','wrong_direct_join_rows',6),('bad join amount inflation','wrong_direct_join_billed_cents',490)]:
    check('reconciliation',name,report[key],value)
check('grain','job IDs keep leading zeros',prepared['jobs'][0]['job_id'],'0001')
check('time','offset timestamp normalized before month filter',prepared['jobs'][0]['occurred_utc'],'2026-09-30T19:00:00+00:00')
check('time','unparseable timestamp remains unavailable',prepared['jobs'][7]['occurred_utc'],None)
check('zero','explicit zero remains a numeric zero',prepared['jobs'][2]['billed_cents'],0)
check('zero','blank remains missing',prepared['jobs'][3]['billed_cents'],None)
check('group','free plan zero with missing count',next(r for r in report['by_plan'] if r['plan']=='free'),
      {'plan':'free','jobs':2,'known_billed_cents':0,'missing_billed_jobs':1,'known_provider_cents':35})
check('pivot','plan/status count matrix',report['pivot_counts'],{'Unmapped':{'completed':1,'failed':0},'free':{'completed':1,'failed':1},'paid':{'completed':2,'failed':0}})
check('alignment','labels pair the right values',report['index_alignment']['label_sum'],{'a':11,'b':22})
check('alignment','discarding labels changes pairing',report['index_alignment']['positional_sum'],[21,12])
series=pd.Series([pd.NA,pd.NA],dtype='Int64')
check('missing','default sum can look like zero',int(series.sum()),0)
check('missing','min_count preserves all-missing state',pd.isna(series.sum(min_count=1)),True)
rejects('missing','pd.NA has no boolean truth',lambda:bool(pd.NA),TypeError)
left=pd.DataFrame({'key':[pd.NA]});right=pd.DataFrame({'key':[pd.NA],'value':[9]})
check('join','pandas matches null keys if not rejected',len(left.merge(right,on='key')),1)
frame=pd.DataFrame({'value':[1,2]});shallow=frame.copy(deep=False);shallow.loc[0,'value']=8
check('copy','pandas 3 shallow copy protects original',int(frame.loc[0,'value']),1)
check('copy','pandas 3 shallow copy receives change',int(shallow.loc[0,'value']),8)
changed=jobs.copy();changed.loc[changed['job_id'].eq('0003'),'billed_cents']=''
r,_=analyze(changed,attempts,workspaces)
check('mutation','zero to missing increases missing count',r['missing_billed_jobs'],3)
check('mutation','zero to missing keeps known subtotal',r['known_billed_cents'],290)
changed=jobs.copy();changed.loc[changed['job_id'].isin(['0004','0005']),'billed_cents']='0'
check('mutation','filling both missing bills enables complete total',analyze(changed,attempts,workspaces)[0]['complete_billed_cents'],290)
changed=jobs.copy();changed.loc[changed['job_id'].eq('0002'),'billed_cents']=''
check('mutation','all-missing paid subtotal is unavailable',next(g for g in analyze(changed,attempts,workspaces)[0]['by_plan'] if g['plan']=='paid')['known_billed_cents'],None)
changed=attempts.copy();changed.loc[changed['attempt_id'].eq('a02'),'cost_cents']=''
r,_=analyze(jobs,changed,workspaces)
check('mutation','partial cost keeps known lines',r['known_provider_cents'],100)
check('mutation','partial cost exposes incomplete job',r['missing_cost_jobs'],1)
check('mutation','partial cost withholds complete total',r['complete_provider_cents'],None)
changed=attempts.loc[~attempts['job_id'].eq('0005')].copy()
check('mutation','no matching attempt is not a known zero',analyze(jobs,changed,workspaces)[0]['missing_cost_jobs'],1)
changed=attempts.copy();changed.loc[changed['attempt_id'].eq('a09'),'cost_cents']=''
check('mutation','unknown orphan amount remains visible',analyze(jobs,changed,workspaces)[0]['orphan_missing_cost_lines'],1)
r,_=analyze(jobs,attempts,workspaces,end='2026-10-20T00:00:00Z')
check('time','exclusive changed endpoint',r['selected_jobs'],3)
check('time','reduced period can have complete bill',r['complete_billed_cents'],290)
for label,field,value in [('negative amount','billed_cents','-1'),('non-numeric amount','billed_cents','bad'),
                          ('fractional cent','billed_cents','1.5'),('excessive amount','billed_cents','1000000001'),
                          ('missing key','job_id',''),('unknown state','status','pending')]:
    changed=jobs.copy();changed.loc[0,field]=value
    rejects('validation',label,lambda changed=changed:analyze(changed,attempts,workspaces))
changed=jobs.copy();changed.loc[len(changed)-1,'billed_cents']='999'
rejects('validation','conflicting duplicate job',lambda:analyze(changed,attempts,workspaces))
changed=attempts.copy();changed.loc[len(changed)-1,'cost_cents']='999'
rejects('validation','conflicting duplicate attempt',lambda:analyze(jobs,changed,workspaces))
changed=pd.concat([workspaces,workspaces.iloc[[0]]],ignore_index=True)
rejects('validation','duplicate dimension key',lambda:analyze(jobs,attempts,changed))
changed=workspaces.copy();changed.loc[0,'plan']=''
rejects('validation','blank dimension value',lambda:analyze(jobs,attempts,changed))
rejects('validation','naive report boundary',lambda:analyze(jobs,attempts,workspaces,start='2026-10-01'))
rejects('validation','reversed report interval',lambda:analyze(jobs,attempts,workspaces,start='2026-12-01T00:00:00Z'))
changed=jobs.copy();changed.loc[0,'occurred_at']='2026-10-01T00:30:00'
check('validation','naive source timestamp is audited, not guessed',analyze(changed,attempts,workspaces)[0]['date_issue_jobs'],['0001','0007','0008'])
for original,loaded in zip((jobs,attempts,workspaces),load_sources()):pd.testing.assert_frame_equal(original,loaded)
check('preservation','raw CSV-derived frames remain unchanged',True,True)
output={'scope':'Synthetic source reconciliation; cents are integer amounts, not a revenue or causal-impact claim','numpy':arr,'analysis':report}
proof={'verified_date':'2026-10-18','python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
       'total':len(checks),'checks':checks,'observations':output,'external_services_called':False,
       'scope':'Actual NumPy/pandas source reconciliation and mutated data cases; Excel engine checks are separate.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
(BASE/'analysis-output.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
(BASE/'prepared-inputs.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'runtime':{k:proof[k] for k in ['python','numpy','pandas']},'analysis':report},indent=2))
