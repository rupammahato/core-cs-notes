"""Independent Python loops/maps/date arithmetic; no SQL execution or saved SQL outputs."""
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone

def expected(fixture,p):
    t=fixture['tables'];customers={r[0]:{'tenant':r[1],'signup':r[2]} for r in t['customers']}
    ids=sorted(k for k,v in customers.items() if v['tenant']==p['tenant'])
    all_paid=[r for r in t['orders'] if r[1] in ids and r[3]=='paid']
    paid=[r for r in all_paid if p['start']<=r[2]<p['end']]
    by_customer={cid:[r for r in paid if r[1]==cid] for cid in ids}
    by_order={r[0]:r for r in paid}
    def known(values):
        present=[v for v in values if v is not None]
        return sum(present) if present else None
    def pct(n,d):return round(100.0*n/d,6) if d else None
    def utc(ts):return datetime.fromtimestamp(ts,timezone.utc)
    def day(ts):return utc(ts).strftime('%Y-%m-%d')
    def epoch(s):return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())
    def days(start,end):
        at=datetime.fromisoformat(start);stop=datetime.fromisoformat(end)
        while at<stop:
            yield at.strftime('%Y-%m-%d');at+=timedelta(days=1)
    def plan_at(cid,ts):
        history=[r for r in t['plan_history'] if r[0]==cid and r[1]<=ts]
        return max(history,key=lambda r:r[1])[2] if history else 'Unmapped'
    payloads=defaultdict(set);deliveries=defaultdict(list)
    for row in t['raw_events']:
        key=(row[2],row[1]);payloads[key].add((row[3],row[4],row[6]));deliveries[key].append(row)
    canonical=[]
    for key,rows in deliveries.items():
        first=min(rows,key=lambda r:(r[5],r[0]))
        if len(payloads[key])==1 and first[3] in customers and customers[first[3]]['tenant']==first[2]:canonical.append(first)
    def events(cutoff):
        return [r for r in canonical if r[2]==p['tenant'] and r[4]<p['event_cutoff'] and r[5]<cutoff]
    current=events(p['knowledge_cutoff'])
    activity=[r for r in current if r[6]=='activity']
    settled=defaultdict(int);payment_count=Counter();refunded=defaultdict(int)
    for row in t['payments']:
        if row[3]=='succeeded':settled[row[1]]+=row[2];payment_count[row[1]]+=1
    for row in t['refunds']:refunded[row[1]]+=row[2]
    results={}
    results['Q01']=[{'customer_id':cid,'paid_orders':len(by_customer[cid])} for cid in ids]
    results['Q02']=[{'customer_id':cid} for cid in ids if not by_customer[cid]]
    results['Q03']=[];results['Q04']=[]
    for cid in ids:
        rows=by_customer[cid]
        if not rows:continue
        values=[r[4] for r in rows];missing=values.count(None);subtotal=known(values)
        results['Q03'].append({'customer_id':cid,'known_bill_cents':subtotal,'missing_bills':missing,'complete_bill_cents':None if missing else subtotal})
        order_ids={r[0] for r in rows}
        results['Q04'].append({'customer_id':cid,'known_bill_cents':subtotal,'item_count':sum(r[1] in order_ids for r in t['items'])})
    results['Q05']=[{'order_id':r[0],'confirmed_payments':payment_count[r[0]],'confirmed_cents':settled[r[0]],
                     'bill_gap_cents':None if r[4] is None else r[4]-settled[r[0]]} for r in sorted(paid)]
    categories=defaultdict(int);bought=defaultdict(set)
    for row in t['items']:
        if row[1] in by_order:
            categories[row[2]]+=row[3];bought[by_order[row[1]][1]].add(row[2])
    results['Q06']=[{'category':key,'line_cents':categories[key]} for key in sorted(categories)]
    results['Q07']=[{'customer_id':cid} for cid in ids if {'books','software'}<=bought[cid]]
    exclusions={r[0] for r in t['exclusions'] if r[0] is not None}
    results['Q08']=[{'customer_id':cid} for cid in ids if cid not in exclusions]
    totals={r['customer_id']:r['complete_bill_cents'] for r in results['Q03'] if r['complete_bill_cents'] is not None}
    tiers=sorted(set(totals.values()),reverse=True)[:2]
    results['Q09']=[{'customer_id':cid,'bill_cents':totals[cid],'revenue_rank':tiers.index(totals[cid])+1}
                    for cid in sorted(totals,key=lambda cid:(-totals[cid],cid)) if totals[cid] in tiers]
    results['Q10']=[]
    for cid in ids:
        if by_customer[cid]:
            row=max(by_customer[cid],key=lambda r:(r[2],r[0]))
            results['Q10'].append({'customer_id':cid,'order_id':row[0],'billed_cents':row[4]})
    results['Q11']=[];results['Q12']=[];running=0;missing=0
    for date in days(p['report_start_day'],p['report_end_day']):
        today=[r for r in paid if day(r[2])==date]
        contribution=sum(r[4] or 0 for r in today);running+=contribution;missing+=sum(r[4] is None for r in today)
        results['Q11'].append({'day':date,'known_contribution':contribution,'running_known':running,'running_missing':missing,'complete_running':None if missing else running})
        lower=epoch(date)-6*86400;upper=epoch(date)+86400
        window=[r for r in all_paid if lower<=r[2]<upper]
        results['Q12'].append({'day':date,'rolling_known':sum(r[4] or 0 for r in window),'rolling_missing':sum(r[4] is None for r in window)})
    results['Q13']=[];prev=None
    for month in ['2026-08-01','2026-09-01','2026-10-01']:
        count=sum(day(r[2])[:7]==month[:7] for r in all_paid)
        results['Q13'].append({'month':month,'paid_orders':count,'previous_count':prev,'change_pct':None if not prev else round(100.0*(count-prev)/prev,6)});prev=count
    results['Q14']=[]
    for cid in ids:
        active=sorted({day(r[4]) for r in activity if r[3]==cid});groups=[]
        for date in active:
            if not groups or epoch(date)-epoch(groups[-1][-1])!=86400:groups.append([])
            groups[-1].append(date)
        for group in groups:
            if len(group)>=2:results['Q14'].append({'customer_id':cid,'start_day':group[0],'end_day':group[-1],'days':len(group)})
    results['Q15']=[];previous=None;session=None
    for row in sorted([r for r in activity if r[3]==p['customer']],key=lambda r:(r[4],r[1])):
        if previous is None or row[4]-previous>1800:
            session={'session_id':len(results['Q15'])+1,'start_utc':utc(row[4]).strftime('%Y-%m-%d %H:%M:%S'),'events':0};results['Q15'].append(session)
        session['events']+=1;previous=row[4]
    results['Q16']=[{'order_id':r[0],'plan':plan_at(r[1],r[2])} for r in sorted(paid)]
    eligible=[cid for cid in ids if customers[cid]['signup']+7*86400<=p['event_cutoff']]
    funnel=[]
    for cid in eligible:
        start=customers[cid]['signup'];starts=[r[4] for r in current if r[3]==cid and r[6]=='onboard_start' and start<=r[4]<start+7*86400]
        first=min(starts) if starts else None
        completed=first is not None and any(r[3]==cid and r[6]=='activate' and first<=r[4]<start+7*86400 for r in current)
        funnel.append((cid,first is not None,completed))
    results['Q17']=[{'eligible_users':len(eligible),'started_users':sum(r[1] for r in funnel),'completed_users':sum(r[2] for r in funnel),'completion_pct':pct(sum(r[2] for r in funnel),len(eligible))}]
    def retained(cid,offset,cutoff):
        start=customers[cid]['signup']+offset*86400
        return any(r[3]==cid and r[6]=='activity' and start<=r[4]<start+86400 for r in events(cutoff))
    cohorts=defaultdict(list)
    for cid in ids:
        if customers[cid]['signup']+2*86400<=p['event_cutoff']:cohorts[day(customers[cid]['signup'])].append(cid)
    results['Q18']=[]
    for cohort,cids in sorted(cohorts.items()):
        returned=sum(retained(cid,1,p['knowledge_cutoff']) for cid in cids)
        results['Q18'].append({'cohort':cohort,'eligible_users':len(cids),'returned_users':returned,'retention_pct':pct(returned,len(cids))})
    mature=[cid for cid in ids if customers[cid]['signup']+8*86400<=p['event_cutoff']]
    results['Q19']=[]
    for label,cutoff in [('initial',p['knowledge_cutoff']),('revised',p['later_knowledge'])]:
        returned=sum(retained(cid,7,cutoff) for cid in mature)
        results['Q19'].append({'label':label,'eligible_users':len(mature),'returned_users':returned,'retention_pct':pct(returned,len(mature))})
    returned=sum(any(r[3]==cid and customers[cid]['signup']+86400<=r[4]<customers[cid]['signup']+8*86400 for r in activity) for cid in mature)
    results['Q20']=[{'eligible_users':len(mature),'returned_users':returned,'retention_pct':pct(returned,len(mature))}]
    end=epoch(p['activity_day'])+86400
    results['Q21']=[{'dau':len({r[3] for r in activity if end-86400<=r[4]<end}),
                     'active_7d':len({r[3] for r in activity if end-7*86400<=r[4]<end})}]
    eligible_first=[];repeated=0
    for cid in ids:
        history=[r for r in all_paid if r[1]==cid and r[2]<p['event_cutoff']]
        if not history:continue
        first=min(r[2] for r in history)
        if first+7*86400<=p['event_cutoff']:
            eligible_first.append(cid);repeated+=any(first<r[2]<first+7*86400 for r in history)
    results['Q22']=[{'mature_first_purchasers':len(eligible_first),'repeat_purchasers':repeated,'repeat_pct':pct(repeated,len(eligible_first))}]
    mature_carts=[r for r in t['carts'] if r[1] in ids and r[2]+3600<=p['event_cutoff']]
    converted=sum(any(o[5]==r[0] and o[1]==r[1] and r[2]<=o[2]<r[2]+3600 for o in all_paid) for r in mature_carts)
    results['Q23']=[{'mature_carts':len(mature_carts),'converted_carts':converted,'abandoned_carts':len(mature_carts)-converted,'abandonment_pct':pct(len(mature_carts)-converted,len(mature_carts))}]
    segments=defaultdict(list)
    for row in funnel:segments[plan_at(row[0],customers[row[0]]['signup'])].append(row)
    results['Q24']=[{'plan':plan,'eligible_users':len(rows),'completed_users':sum(r[2] for r in rows),'completion_pct':pct(sum(r[2] for r in rows),len(rows))} for plan,rows in sorted(segments.items())]
    results['Q25']=[{'event_id':key[1],'deliveries':len(rows),'payloads':len(payloads[key]),'kind':'exact-repeat' if len(payloads[key])==1 else 'conflict'}
                     for key,rows in sorted(deliveries.items()) if key[0]==p['tenant'] and len(rows)>1]
    results['Q26']=[]
    for r in sorted(t['raw_events']):
        owner=customers.get(r[3]);owner_tenant=owner['tenant'] if owner else None
        if (r[2]==p['tenant'] or owner_tenant==p['tenant']) and owner_tenant!=r[2]:
            results['Q26'].append({'delivery_id':r[0],'issue':'unknown-customer' if owner is None else 'tenant-mismatch'})
    results['Q27']=[{'order_id':r[0],'confirmed_cents':settled[r[0]],'refund_cents':refunded[r[0]],
                     'confirmed_net_cents':settled[r[0]]-refunded[r[0]],'bill_gap_cents':None if r[4] is None else r[4]-settled[r[0]]} for r in sorted(paid)]
    results['Q28']=[{'paid_orders':len(paid),'confirmed_cents':sum(settled[r[0]] for r in paid),
                     'refund_cents':sum(refunded[r[0]] for r in paid),'confirmed_net_cents':sum(settled[r[0]]-refunded[r[0]] for r in paid),
                     'missing_bills':sum(r[4] is None for r in paid)}]
    results['Q29']=[]
    for r in sorted(paid):
        lines=[i[3] for i in t['items'] if i[1]==r[0]]
        issue='missing-bill' if r[4] is None else 'missing-items' if not lines else 'line-bill-mismatch' if sum(lines)!=r[4] else None
        if issue:results['Q29'].append({'order_id':r[0],'issue':issue})
    results['Q30']=[{'order_id':r[0]} for r in sorted(t['orders'],key=lambda r:(r[2],r[0])) if r[1] in ids and r[1]==p['customer'] and p['start']<=r[2]<p['end']]
    return results
