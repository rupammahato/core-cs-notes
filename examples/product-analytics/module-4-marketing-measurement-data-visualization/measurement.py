"""Synthetic marketing measurement; explicit contracts, not vendor attribution parity."""
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parent


def instant(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Need an aware timestamp')
    return parsed


def nonnegative(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('Need nonnegative integer units')
    return value


def ratio(numerator, denominator, multiplier=1):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(float(Decimal(str(numerator))*Decimal(str(multiplier))/Decimal(str(denominator))), 6)


def unique(rows, key):
    result = {}
    for source in rows:
        row = deepcopy(source)
        identity = row.get(key)
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError('Missing identity')
        if identity in result and row != result[identity]:
            raise ValueError('Conflicting identity')
        result[identity] = row
    return list(result.values())


def campaign_report(rows):
    rows = unique(rows, 'campaign_id')
    measures = ['spend_cents', 'impressions', 'clicks', 'attributed_value_cents']
    for row in rows:
        for key in measures:
            if row[key] is not None:
                nonnegative(row[key])
        credit = row['conversion_credits']
        if credit is not None:
            try:
                number = Decimal(credit)
            except (InvalidOperation, TypeError):
                raise ValueError('Invalid conversion credit') from None
            if not number.is_finite() or number < 0:
                raise ValueError('Invalid conversion credit')
            row['conversion_credits'] = number
    totals = {}
    for key in measures + ['conversion_credits']:
        values = [row[key] for row in rows if row[key] is not None]
        known = sum(values) if values else None
        totals[key] = {'known':float(known) if isinstance(known, Decimal) else known,
                       'missing_rows':sum(row[key] is None for row in rows),
                       'complete':known if len(values)==len(rows) and values else None}
    def metrics(values):
        s,i,c,n,v = (values[key] for key in measures[:3]+['conversion_credits',measures[3]])
        return {'ctr_pct':ratio(c,i,100), 'cpm_cents':ratio(s,i,1000),
                'cpc_cents':ratio(s,c), 'purchase_credit_rate_pct':ratio(n,c,100),
                'cost_per_purchase_credit_cents':ratio(s,n), 'reported_roas':ratio(v,s)}
    return {'campaigns':[{**row,'conversion_credits':float(row['conversion_credits']) if row['conversion_credits'] is not None else None,
                         'metrics':metrics(row)} for row in rows],
            'totals':{key:{**value,'complete':float(value['complete']) if isinstance(value['complete'],Decimal) else value['complete']}
                      for key,value in totals.items()},
            'blended_metrics':metrics({key:value['complete'] for key,value in totals.items()}),
            'wrong_unweighted_ctr_pct':round(sum(metrics(row)['ctr_pct'] for row in rows)/len(rows),6)
                 if rows and all(metrics(row)['ctr_pct'] is not None for row in rows) else None}


def attribute(orders, touches, campaigns, click_days=7, view_days=None):
    if type(click_days) is not int or click_days <= 0 or (view_days is not None and (type(view_days) is not int or view_days<=0)):
        raise ValueError('Use positive whole-day windows')
    orders = unique(orders, 'order_id'); touches = unique(touches, 'touch_id')
    campaign_ids = {row['campaign_id'] for row in campaigns}
    for touch in touches:
        if touch['campaign_id'] not in campaign_ids or touch['kind'] not in ['click','view']:
            raise ValueError('Unknown touch campaign or kind')
        if not touch.get('customer_id'):
            raise ValueError('Missing touch customer')
        instant(touch['at'])
    results=[]
    for order in orders:
        nonnegative(order['gross_cents']); nonnegative(order['refund_cents'])
        if order['refund_cents']>order['gross_cents'] or not order.get('customer_id') or type(order['is_first_purchase']) is not bool:
            raise ValueError('Invalid order contract')
        occurred=instant(order['at'])
        eligible=[touch for touch in touches if touch['customer_id']==order['customer_id'] and
                  touch['kind']=='click' and timedelta(0)<=occurred-instant(touch['at'])<=timedelta(days=click_days)]
        if not eligible and view_days is not None:
            eligible=[touch for touch in touches if touch['customer_id']==order['customer_id'] and
                      touch['kind']=='view' and timedelta(0)<=occurred-instant(touch['at'])<=timedelta(days=view_days)]
        selected=max(eligible,key=lambda touch:(instant(touch['at']),touch['touch_id'])) if eligible else None
        results.append({'order_id':order['order_id'],'campaign_id':selected['campaign_id'] if selected else 'Unattributed',
                        'touch_id':selected['touch_id'] if selected else None,
                        'net_cents':order['gross_cents']-order['refund_cents']})
    by_campaign={key:sum(row['net_cents'] for row in results if row['campaign_id']==key)
                 for key in sorted(campaign_ids|{'Unattributed'})}
    return {'assignments':results,'by_campaign_net_cents':by_campaign,
            'total_net_cents':sum(row['net_cents'] for row in results)}


def claim_overlap(orders, claims):
    order_values={row['order_id']:row['gross_cents']-row['refund_cents'] for row in unique(orders,'order_id')}
    identities=[(row['campaign_id'],row['order_id']) for row in claims]
    if len(identities)!=len(set(identities)) or any(order not in order_values for _,order in identities):
        raise ValueError('Duplicate claim or unknown order')
    claimed={order for _,order in identities}
    combined=sum(order_values[order] for _,order in identities)
    deduplicated=sum(order_values[order] for order in claimed)
    return {'claim_rows':len(identities),'unique_claimed_orders':len(claimed),
            'summed_claim_value_cents':combined,'unique_claimed_net_cents':deduplicated,
            'overlap_cents':combined-deduplicated}


class DigestStore:
    """In-memory atomic publication model; no scheduler, Telegram or ad account."""
    def __init__(self):
        self.db=sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE digest (key TEXT PRIMARY KEY, revision INTEGER, body TEXT)')

    def publish(self,key,revision,payload):
        if not key or type(revision) is not int or revision<1:
            raise ValueError('Invalid digest identity/revision')
        body=json.dumps(payload,sort_keys=True)
        with self.db:
            old=self.db.execute('SELECT revision,body FROM digest WHERE key=?',(key,)).fetchone()
            if old:
                if revision<old[0] or (revision==old[0] and body!=old[1]):
                    raise ValueError('Stale or conflicting digest revision')
                if revision==old[0]:return 'duplicate'
            self.db.execute('INSERT INTO digest VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET revision=excluded.revision,body=excluded.body',
                            (key,revision,body))
        return 'published'

    def close(self):
        self.db.close()


def build(case):
    contract=case['contract']
    if contract['currency']!='USD' or contract['timezone']!='UTC':
        raise ValueError('This fixture accepts one USD/UTC contract; normalize other inputs explicitly')
    instant(contract['as_of'])
    report=campaign_report(case['campaigns'])
    orders=unique(case['orders'],'order_id')
    clicks=attribute(orders,case['touches'],report['campaigns'])
    views=attribute(orders,case['touches'],report['campaigns'],view_days=1)
    new_customers={row['customer_id'] for row in orders if row['is_first_purchase']}
    spend=report['totals']['spend_cents']['complete']
    return {'scope':case['scope'],'contract':contract,'platform_report':report,
            'ledger':{'orders':len(orders),'new_customers_supplied':len(new_customers),
                      'gross_cents':sum(row['gross_cents'] for row in orders),
                      'refund_cents':sum(row['refund_cents'] for row in orders),
                      'net_cents':clicks['total_net_cents'],
                      'blended_net_revenue_per_media_spend':ratio(clicks['total_net_cents'],spend),
                      'media_spend_per_supplied_new_customer_cents':ratio(spend,len(new_customers))},
            'last_eligible_click_7d':clicks,'click_7d_else_view_1d':views,
            'independent_claim_overlap':claim_overlap(orders,case['independent_claims'])}


if __name__=='__main__':
    source=(BASE/'case.json').read_bytes()
    output=build(json.loads(source))
    (BASE/'measurement-output.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_sha256':hashlib.sha256(source).hexdigest(),'output':output},indent=2))
