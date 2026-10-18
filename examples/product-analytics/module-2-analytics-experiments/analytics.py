"""A real local SQLite event worksheet and aggregate experiment arithmetic."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import math
from pathlib import Path
import sqlite3
from statistics import NormalDist

BASE = Path(__file__).resolve().parent


def timestamp(value):
    if type(value) is not str:
        raise ValueError('Timestamp must be a string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('Invalid timestamp') from None
    if result.tzinfo is None or result.utcoffset() is None or result.microsecond:
        raise ValueError('Use timezone-aware whole-second timestamps')
    return int(result.timestamp())


def percentage(numerator, denominator):
    return None if denominator == 0 else format(Decimal(numerator)*100/Decimal(denominator), '.6f')


@contextmanager
def dataset(case):
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
          CREATE TABLE users(id TEXT PRIMARY KEY, internal INTEGER NOT NULL);
          CREATE TABLE events(id TEXT PRIMARY KEY, subject TEXT REFERENCES users(id), name TEXT,
            occurred INTEGER, received INTEGER, operation TEXT, version INTEGER, properties TEXT);
        ''')
        users = {}
        for user in case['users']:
            if type(user['id']) is not str or not user['id'].strip() or user['id'] in users or type(user['internal']) is not bool:
                raise ValueError('Invalid user registry')
            users[user['id']] = user
            db.execute('INSERT INTO users VALUES (?,?)', (user['id'], int(user['internal'])))
        aliases = case['aliases']
        if any(alias in users or not alias or target not in users for alias,target in aliases.items()):
            raise ValueError('Aliases must map directly to an existing canonical user')
        plan = json.loads((BASE/'tracking-plan.json').read_text())
        duplicates = 0
        for event in case['events']:
            if type(event['id']) is not str or not event['id'].strip():
                raise ValueError('Missing event identity')
            subject = aliases.get(event['subject'], event['subject'])
            if subject not in users or event['name'] not in plan['events'] or type(event['version']) is not int or event['version'] != 1:
                raise ValueError('Unknown subject, event or schema version')
            operation = event['operation']
            if event['name'] == 'signup_completed':
                if operation is not None:
                    raise ValueError('Signup has no generation operation')
            elif type(operation) is not str or not operation.strip():
                raise ValueError('Generation events require operation identity')
            occurred, received = map(timestamp, (event['occurred_at'], event['received_at']))
            if received < occurred:
                raise ValueError('Fixture policy rejects receipt before occurrence')
            props = event['properties']
            if type(props) is not dict or any(key not in plan['allowed_properties'] or value not in plan['allowed_properties'][key]
                                             for key,value in props.items()):
                raise ValueError('Unknown property or value')
            normalized = (subject,event['name'],occurred,operation,event['version'],json.dumps(props,sort_keys=True))
            old = db.execute('SELECT subject,name,occurred,operation,version,properties FROM events WHERE id=?',(event['id'],)).fetchone()
            if old is not None:
                if tuple(old) != normalized:
                    raise ValueError('Conflicting duplicate event')
                duplicates += 1
                db.execute('UPDATE events SET received=MIN(received,?) WHERE id=?',(received,event['id']))
            else:
                db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',
                           (event['id'],subject,event['name'],occurred,received,operation,event['version'],normalized[-1]))
        db.commit()
        yield db, {'duplicate_reports_ignored':duplicates,'stored_events':db.execute('SELECT COUNT(*) FROM events').fetchone()[0]}
    finally:
        db.close()


def parameters(event_cutoff, knowledge_cutoff, retention_day):
    if type(retention_day) is not int or not 0 <= retention_day <= 365:
        raise ValueError('Retention day must be a bounded integer')
    event, knowledge = timestamp(event_cutoff), timestamp(knowledge_cutoff)
    if knowledge < event:
        raise ValueError('Knowledge cutoff must reach the event cutoff')
    return {'event_cutoff':event,'knowledge_cutoff':knowledge,'retention_day':retention_day}


def report(db, event_cutoff, knowledge_cutoff, retention_day=7):
    params = parameters(event_cutoff,knowledge_cutoff,retention_day)
    rows = [dict(row) for row in db.execute((BASE/'metrics.sql').read_text(),params)]
    mature = [row for row in rows if row['activation_mature']]
    retained = [row for row in rows if row['retention_mature']]
    cohorts = {}
    for row in retained:
        day = datetime.fromtimestamp(row['signup'],timezone.utc).date().isoformat()
        bucket = cohorts.setdefault(day,{'eligible':0,'returned':0})
        bucket['eligible'] += 1; bucket['returned'] += row['retained']
    for bucket in cohorts.values():
        bucket['rate_pct'] = percentage(bucket['returned'],bucket['eligible'])
    start = sum(row['started'] for row in mature)
    complete = sum(row['completed'] for row in mature)
    returns = sum(row['retained'] for row in retained)
    return {'visible_signup_users':len(rows),
            'activation':{'eligible':len(mature),'immature_excluded':len(rows)-len(mature),
                          'started':start,'completed':complete,'rate_pct':percentage(complete,len(mature)),
                          'start_to_complete_pct':percentage(complete,start)},
            'retention':{'day':retention_day,'eligible':len(retained),'returned':returns,
                         'rate_pct':percentage(returns,len(retained)),'cohorts':cohorts},'users':rows}


def activity(db, day, event_cutoff, knowledge_cutoff):
    params = parameters(event_cutoff,knowledge_cutoff,0)
    try:
        start = datetime.strptime(day,'%Y-%m-%d').replace(tzinfo=timezone.utc)
    except (ValueError,TypeError):
        raise ValueError('Expected a UTC calendar date') from None
    end = start + timedelta(days=1)
    if end.timestamp() > params['event_cutoff']:
        raise ValueError('Activity day has not fully elapsed')
    row = db.execute('''SELECT COUNT(*) AS events, COUNT(DISTINCT e.subject) AS active_users
      FROM events e JOIN users u ON u.id=e.subject WHERE u.internal=0
      AND e.name='generation_succeeded' AND e.occurred>=? AND e.occurred<?
      AND e.received<=?''',(int(start.timestamp()),int(end.timestamp()),params['knowledge_cutoff'])).fetchone()
    return dict(row)


def experiment(control_n, control_k, treatment_n, treatment_k, treatment_share=0.5):
    for n,k in [(control_n,control_k),(treatment_n,treatment_k)]:
        if type(n) is not int or type(k) is not int or not 0 < n <= 10**9 or not 0 <= k <= n:
            raise ValueError('Need bounded assigned counts and binary outcomes')
    if isinstance(treatment_share,bool) or not isinstance(treatment_share,(int,float)) or not math.isfinite(treatment_share) or not 0 < treatment_share < 1:
        raise ValueError('Invalid expected allocation')
    c, t = control_k/control_n, treatment_k/treatment_n
    difference = t-c
    normal_ok = min(control_k,control_n-control_k,treatment_k,treatment_n-treatment_k) >= 10
    ci = p_value = None
    if normal_ok:
        se = math.sqrt(c*(1-c)/control_n + t*(1-t)/treatment_n)
        z = NormalDist().inv_cdf(0.975)
        ci = [format((difference-z*se)*100,'.6f'),format((difference+z*se)*100,'.6f')]
        pooled = (control_k+treatment_k)/(control_n+treatment_n)
        null_se = math.sqrt(pooled*(1-pooled)*(1/control_n+1/treatment_n))
        p_value = math.erfc(abs(difference/null_se)/math.sqrt(2))
    total = control_n+treatment_n
    expected_c,expected_t = total*(1-treatment_share),total*treatment_share
    chi = (control_n-expected_c)**2/expected_c + (treatment_n-expected_t)**2/expected_t
    srm_p = math.erfc(math.sqrt(chi/2)) if min(expected_c,expected_t)>=5 else None
    return {'control_rate_pct':format(c*100,'.6f'),'treatment_rate_pct':format(t*100,'.6f'),
            'absolute_lift_pp':format(difference*100,'.6f'),
            'relative_lift_pct':None if c==0 else format(difference/c*100,'.6f'),
            'normal_approximation_adequate_for_fixture':normal_ok,'approx_95_ci_pp':ci,
            'two_sided_p_value':p_value,'srm_chi_square':chi,'srm_p_value':srm_p,
            'srm_flag_at_0_001':None if srm_p is None else srm_p<0.001,
            'assignment_verified':False,'scope':'Aggregate synthetic counts; no randomized deployment, power plan or causal effect verified.'}


def demo(case):
    with dataset(case) as (db,intake):
        first = report(db,case['event_cutoff'],case['initial_knowledge_cutoff'])
        revised = report(db,case['event_cutoff'],case['revised_knowledge_cutoff'])
        return {'scope':case['scope'],'intake':intake,
                'initial':{'activation':first['activation'],'retention':first['retention']},
                'revised':{'activation':revised['activation'],'retention':revised['retention']},
                'activity_oct_8':activity(db,'2026-10-08',case['event_cutoff'],case['revised_knowledge_cutoff']),
                'experiment':experiment(1000,200,1000,240),
                'imbalanced_assignment':experiment(1000,200,600,144)}


if __name__ == '__main__':
    case = json.loads((BASE/'case.json').read_text())
    print(json.dumps(demo(case),indent=2))
