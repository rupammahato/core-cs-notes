"""NumPy/pandas teaching analysis over synthetic CSV data, with explicit grain and gaps."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent


def unique_rows(frame, key):
    if frame[key].isna().any() or frame[key].eq('').any():
        raise ValueError('Missing identity')
    for _,group in frame.groupby(key,dropna=False):
        if group.nunique(dropna=False).gt(1).any():
            raise ValueError('Conflicting repeated identity')
    return frame.drop_duplicates(key).copy()


def cents(series):
    missing=series.eq('')|series.isna()
    if (~missing & ~series.str.fullmatch(r'\d+',na=False)).any():
        raise ValueError('Use nonnegative whole-cent strings or explicit blank')
    result=pd.to_numeric(series.mask(missing),errors='raise').astype('Int64')
    if result.dropna().gt(10**9).any():
        raise ValueError('Amount outside teaching range')
    return result


def numpy_examples():
    usage=np.array([[10,20,30],[1,2,3]],dtype=np.int64)
    rates=np.array([2,3,4],dtype=np.int64)
    original=np.array([1,2,3,4],dtype=np.int64)
    view=original[1:3];view[0]=99
    fancy=original[[0,2]];fancy[0]=-1
    return {'shape':list(usage.shape),'dtype':str(usage.dtype),'broadcast_product':(usage*rates).tolist(),
            'column_sums':usage.sum(axis=0).tolist(),'row_sums':usage.sum(axis=1).tolist(),
            'weighted_rows':(usage*rates).sum(axis=1).tolist(),'matrix_vector':(usage@rates).tolist(),
            'original_after_slice_edit':original.tolist(),'fancy_copy_after_edit':fancy.tolist()}


def analyze(jobs,attempts,workspaces,start='2026-10-01T00:00:00Z',end='2026-11-01T00:00:00Z'):
    jobs=jobs.copy();attempts=attempts.copy();workspaces=workspaces.copy()
    raw_jobs,raw_attempts=len(jobs),len(attempts)
    jobs=unique_rows(jobs,'job_id');attempts=unique_rows(attempts,'attempt_id')
    if workspaces['workspace_id'].isna().any() or workspaces['workspace_id'].eq('').any() or workspaces['workspace_id'].duplicated().any():
        raise ValueError('Workspace dimension needs one nonblank row per key')
    if not workspaces['plan'].isin(['paid','free']).all():
        raise ValueError('Missing or unknown plan')
    if not jobs['status'].isin(['completed','failed']).all():
        raise ValueError('Use final job states')
    if jobs['workspace_id'].isna().any() or jobs['workspace_id'].eq('').any() or attempts['job_id'].isna().any() or attempts['job_id'].eq('').any():
        raise ValueError('Missing relationship key')
    jobs['billed_cents']=cents(jobs['billed_cents'])
    attempts['cost_cents']=cents(attempts['cost_cents'])
    aware=jobs['occurred_at'].str.contains(r'(?:Z|[+-]\d{2}:\d{2})$',regex=True,na=False)
    jobs['occurred_utc']=pd.to_datetime(jobs['occurred_at'].where(aware),format='ISO8601',errors='coerce',utc=True)
    bad_dates=jobs.loc[jobs['occurred_utc'].isna(),'job_id'].tolist()
    start,end=pd.Timestamp(start),pd.Timestamp(end)
    if start.tzinfo is None or end.tzinfo is None or start>=end:
        raise ValueError('Need an ordered timezone-aware report interval')
    grouped=attempts.groupby('job_id',dropna=False).agg(
        known_cost_cents=('cost_cents',lambda s:s.sum(min_count=1)),
        missing_cost_lines=('cost_cents',lambda s:int(s.isna().sum())))
    facts=jobs.merge(grouped,on='job_id',how='left',validate='one_to_one')
    facts['missing_cost']=facts['missing_cost_lines'].isna()|facts['missing_cost_lines'].gt(0)
    facts=facts.merge(workspaces,on='workspace_id',how='left',validate='many_to_one',indicator='dimension_match')
    facts['plan']=facts['plan'].fillna('Unmapped')
    in_period=facts['occurred_utc'].ge(start)&facts['occurred_utc'].lt(end)
    selected=facts.loc[in_period].copy()
    known_bill=selected['billed_cents'].sum(min_count=1)
    known_cost=selected['known_cost_cents'].sum(min_count=1)
    missing_bills=int(selected['billed_cents'].isna().sum())
    missing_costs=int(selected['missing_cost'].sum())
    orphan=attempts.loc[~attempts['job_id'].isin(jobs['job_id'])].copy()
    groups=[]
    for plan,group in selected.groupby('plan',dropna=False,observed=True,sort=True):
        billed=group['billed_cents'].sum(min_count=1)
        cost=group['known_cost_cents'].sum(min_count=1)
        groups.append({'plan':str(plan),'jobs':len(group),'known_billed_cents':None if pd.isna(billed) else int(billed),
                       'missing_billed_jobs':int(group['billed_cents'].isna().sum()),
                       'known_provider_cents':None if pd.isna(cost) else int(cost)})
    pivot=pd.crosstab(selected['plan'],selected['status']).reindex(columns=['completed','failed'],fill_value=0)
    # Deliberately wrong join: repeat job-level billing once per matching attempt.
    inflated=selected.drop(columns=['known_cost_cents','missing_cost_lines','missing_cost']).merge(attempts,on='job_id',how='left')
    left=pd.Series([20,10],index=['b','a']);right=pd.Series([1,2],index=['a','b'])
    aligned=left+right
    report={'raw_job_rows':raw_jobs,'deduplicated_jobs':len(jobs),'raw_attempt_rows':raw_attempts,
            'deduplicated_attempts':len(attempts),'date_issue_jobs':bad_dates,
            'excluded_known_date_jobs':facts.loc[~in_period & facts['occurred_utc'].notna(),'job_id'].tolist(),
            'selected_job_ids':selected['job_id'].tolist(),'selected_jobs':len(selected),
            'completed_jobs':int(selected['status'].eq('completed').sum()),
            'completion_share':None if selected.empty else float(selected['status'].eq('completed').mean()),
            'known_billed_cents':None if pd.isna(known_bill) else int(known_bill),
            'missing_billed_jobs':missing_bills,
            'complete_billed_cents':None if missing_bills or pd.isna(known_bill) else int(known_bill),
            'known_provider_cents':None if pd.isna(known_cost) else int(known_cost),
            'missing_cost_jobs':missing_costs,
            'complete_provider_cents':None if missing_costs or pd.isna(known_cost) else int(known_cost),
            'unmapped_selected_jobs':selected.loc[selected['dimension_match'].eq('left_only'),'job_id'].tolist(),
            'orphan_attempts':orphan['attempt_id'].tolist(),'orphan_cost_cents':int(orphan['cost_cents'].sum()),
            'orphan_missing_cost_lines':int(orphan['cost_cents'].isna().sum()),
            'wrong_direct_join_rows':len(inflated),'wrong_direct_join_billed_cents':int(inflated['billed_cents'].sum()),
            'by_plan':groups,'pivot_counts':{str(index):{str(k):int(v) for k,v in row.items()} for index,row in pivot.to_dict(orient='index').items()},
            'index_alignment':{'label_sum':{k:int(v) for k,v in aligned.items()},
                               'positional_sum':(left.to_numpy()+right.to_numpy()).tolist()}}
    def scalar(value):
        if pd.isna(value):return None
        if isinstance(value,pd.Timestamp):return value.isoformat()
        if isinstance(value,np.integer):return int(value)
        return value
    prepared={'jobs':[{key:scalar(row[key]) for key in ['job_id','workspace_id','occurred_at','occurred_utc','status','billed_cents']}
                       for _,row in jobs.iterrows()],
              'attempts':[{key:scalar(row[key]) for key in ['attempt_id','job_id','cost_cents']} for _,row in attempts.iterrows()],
              'workspaces':workspaces.to_dict(orient='records'),'start':start.isoformat(),'end':end.isoformat()}
    return report,prepared


def load_sources():
    return tuple(pd.read_csv(BASE/name,dtype='string',keep_default_na=False)
                 for name in ['jobs.csv','attempts.csv','workspaces.csv'])


if __name__=='__main__':
    report,prepared=analyze(*load_sources())
    output={'scope':'Synthetic source reconciliation; cents are integer amounts, not a revenue or causal-impact claim',
            'numpy':numpy_examples(),'analysis':report}
    (BASE/'analysis-output.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    (BASE/'prepared-inputs.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,indent=2))
