"""Execute pricing arithmetic and adversarial evidence cases using invented USD rates."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import platform
from economics import aggregate, amount, attempt_cost, break_even, count, credit_service_value, demo, ideal_retry_cost, margins, price_for_margin, rate_index, shown

BASE = Path(__file__).resolve().parent
case = json.loads((BASE / 'case.json').read_text())
checks = []


def check(group, name, actual, expected):
    assert actual == expected, (name, actual, expected)
    checks.append({'group': group, 'name': name, 'passed': True})


def rejects(group, name, function):
    try:
        function()
    except ValueError:
        checks.append({'group': group, 'name': name, 'passed': True})
    else:
        raise AssertionError(name)


tariffs = rate_index(case['rates'])
for name, index, expected in [('text input/output', 0, '0.006'), ('one image', 1, '0.04'),
                              ('failed attempt still costs', 2, '0.0018'),
                              ('two images', 8, '0.08')]:
    check('normalization', name, attempt_cost(case['attempts'][index], tariffs), Decimal(expected))
check('normalization', 'missing usage stays unknown', attempt_cost(case['attempts'][9], tariffs), None)
zero = deepcopy(case['attempts'][0]); zero['usage'] = []
check('normalization', 'explicit empty usage is zero', attempt_cost(zero, tariffs), Decimal(0))
check('normalization', 'micro-cost is not rounded to cents', shown(Decimal('0.000001')), '0.000001')
check('normalization', 'round-half-up display', shown(Decimal('0.0000005')), '0.000001')
for value in ['-1', 'NaN', 'Infinity', 'bad', '1000000000001', '0.0000000000001', 0.1, True]:
    rejects('validation', 'invalid amount ' + repr(value), lambda value=value: amount(value))
for value in [-1, True, 1.5, '1', 10**12 + 1]:
    rejects('validation', 'invalid quantity ' + repr(value), lambda value=value: count(value))
rejects('validation', 'zero tariff basis', lambda: count(0, positive=True))
check('validation', 'allowed upper amount', amount('1000000000000'), Decimal('1000000000000'))
for label, field, value in [('mixed currency', 'currency', 'EUR'), ('invalid denominator', 'per', 0), ('negative price', 'price', '-1')]:
    changed = deepcopy(case['rates']); changed[0][field] = value
    rejects('tariff', label, lambda changed=changed: rate_index(changed))
rejects('tariff', 'duplicate identity', lambda: rate_index(case['rates'] + [case['rates'][0]]))
for label, field, value in [('unknown model', 'model', 'missing'), ('unknown pricing version', 'rate_version', 'teaching-v2')]:
    changed = deepcopy(case['attempts'][0]); changed[field] = value
    rejects('tariff', label, lambda changed=changed: attempt_cost(changed, tariffs))
changed = deepcopy(case['attempts'][0]); changed['usage'][0]['unit'] = 'seconds'
rejects('tariff', 'wrong unit', lambda: attempt_cost(changed, tariffs))
changed = deepcopy(case['attempts'][0]); changed['usage'].append(changed['usage'][0])
rejects('tariff', 'duplicate usage category', lambda: attempt_cost(changed, tariffs))

initial = aggregate(case['jobs'], case['attempts'], case['rates'])
for name, field, expected in [('closed cohort size', 'jobs', 5), ('product successes', 'successful_jobs', 3),
    ('deduplicated attempts', 'unique_attempts', 10), ('duplicate reports', 'duplicate_reports_ignored', 1),
    ('known subtotal', 'known_cost_usd', '0.231800'), ('total withheld', 'total_cost_usd', None),
    ('unit cost withheld', 'cost_per_success_usd', None), ('missing evidence visible', 'unknown_attempts', ['a10'])]:
    check('cohort', name, initial[field], expected)
output = demo(case); final = output['after_reconciliation']
check('cohort', 'reconciled provider cost', final['total_cost_usd'], '0.233800')
check('cohort', 'cost per successful customer action includes failures', final['cost_per_success_usd'], '0.077933')
check('cohort', 'partial failed job cost retained', final['job_costs'][2]['total_cost_usd'], '0.046000')
check('cohort', 'timeout cost retained after reconciliation', final['job_costs'][4]['total_cost_usd'], '0.002000')
check('cohort', 'provider aggregation', final['provider_known_cost_usd'], {'image-demo':'0.200000','text-demo':'0.033800'})
check('cohort', 'zero jobs has no unit cost', aggregate([], [], case['rates'])['cost_per_success_usd'], None)
failed = deepcopy(case['jobs'])
for row in failed: row['status'] = 'failed'
check('cohort', 'zero successes has no unit cost', aggregate(failed, case['attempts'], case['rates'])['cost_per_success_usd'], None)
changed = deepcopy(case['attempts']); changed[-1]['usage'][0]['quantity'] += 1
rejects('evidence', 'conflicting replay rejected', lambda: aggregate(case['jobs'], changed, case['rates']))
changed = deepcopy(case['attempts']); changed[0]['job'] = 'unknown'
rejects('evidence', 'orphan attempt rejected', lambda: aggregate(case['jobs'], changed, case['rates']))
changed = deepcopy(case['jobs']); changed[0]['status'] = 'pending'
rejects('evidence', 'unclosed cohort rejected', lambda: aggregate(changed, case['attempts'], case['rates']))
rejects('evidence', 'duplicate job ID rejected', lambda: aggregate(case['jobs']+[case['jobs'][0]], case['attempts'], case['rates']))
rejects('evidence', 'missing job evidence rejected', lambda: aggregate(case['jobs'], [], case['rates']))
changed = deepcopy(case['attempts']); changed[0]['status'] = 'cancelled'
rejects('evidence', 'unknown attempt state rejected', lambda: aggregate(case['jobs'], changed, case['rates']))
changed = deepcopy(case['attempts'])
for row in changed:
    if row['job'] == 'g1': row['status'] = 'failed'
rejects('evidence', 'unsupported success rejected', lambda: aggregate(case['jobs'], changed, case['rates']))

margin = output['cohort_margin']
for name, field, expected in [('revenue assumption', 'revenue_usd','0.600000'), ('delivery includes infrastructure', 'cogs_usd','0.248800'),
    ('gross profit', 'gross_profit_usd','0.351200'), ('gross margin', 'gross_margin_pct','58.533333'),
    ('payment fee allocation', 'other_variable_usd','0.050000'), ('contribution', 'contribution_usd','0.301200'),
    ('contribution ratio', 'contribution_margin_pct','50.200000')]:
    check('margin', name, margin[field], expected)
check('margin', 'zero revenue gives undefined percentage', margins('0','1')['gross_margin_pct'], None)
check('margin', 'loss stays negative', margins('1','2')['gross_margin_pct'], '-100.000000')
check('margin', '100 percent markup is 50 percent margin', margins('0.20','0.10')['gross_margin_pct'], '50.000000')
check('margin', 'use ratio of totals, not mean percentages', margins('10.10','2.08')['gross_margin_pct'], '79.405941')
check('margin', 'fixed cost reduces scenario result', margins('1','0.2','0.1','2')['scenario_after_fixed_usd'], '-1.300000')
check('pricing', '60 percent gross margin floor', price_for_margin('0.06','0.60')['cent_price_usd'], '0.15')
check('pricing', 'round price floor upwards', price_for_margin('0.061','0.60')['cent_price_usd'], '0.16')
check('pricing', 'zero target margin', price_for_margin('0.06','0')['cent_price_usd'], '0.06')
rejects('pricing', '100 percent target rejected', lambda: price_for_margin('0.06','1'))
rejects('pricing', 'negative target rejected', lambda: price_for_margin('0.06','-0.1'))
check('pricing', 'break-even rounds up', break_even('1000','0.20','0.07'), 7693)
check('pricing', 'zero contribution has no finite break-even', break_even('1000','0.07','0.07'), None)
check('pricing', 'negative contribution has no finite break-even', break_even('1000','0.06','0.07'), None)
check('pricing', 'zero fixed positive contribution', break_even('0','0.20','0.07'), 0)
check('credits', 'standard pack allocation', credit_service_value(20,'10',1000),'0.200000')
check('credits', 'discount affects realized unit value', credit_service_value(20,'8',1000),'0.160000')
check('credits', 'promotion has zero paid-pack value', credit_service_value(20,'0',1000),'0.000000')
check('credits', 'zero consumption', credit_service_value(0,'10',1000),'0.000000')
rejects('credits', 'zero pack size rejected', lambda: credit_service_value(20,'10',0))
snapshot = deepcopy(case); demo(case)
check('retry', '80 percent success changes effective cost', ideal_retry_cost('0.04','0.8'),'0.050000')
check('retry', '50 percent success doubles effective cost', ideal_retry_cost('0.04','0.5'),'0.080000')
check('retry', 'certain success', ideal_retry_cost('0.04','1'),'0.040000')
rejects('retry', 'zero success probability', lambda: ideal_retry_cost('0.04','0'))
rejects('retry', 'probability above one', lambda: ideal_retry_cost('0.04','1.1'))
check('pricing', 'one fewer success does not cover fixed costs', Decimal('0.13')*7692, Decimal('999.96'))
check('pricing', 'break-even count covers fixed costs', Decimal('0.13')*7693, Decimal('1000.09'))
check('boundary', 'input evidence remains unchanged', case, snapshot)
check('boundary', 'invented scope retained', output['scope'], case['scope'])
proof={'verified_date':'2026-10-18','python':platform.python_version(),'os':platform.platform(),
       'total':len(checks),'checks':checks,'observations':output,
       'external_services_called':False,'persistent_listener_started':False,
       'scope':'Offline synthetic USD cost arithmetic, evidence deduplication, missing-usage handling, margin, pricing and single-pack credit allocation. No production providers, ledger, payment integration or accounting reconciliation.'}
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
(BASE/'economics-output.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'python':proof['python'],'cohort_margin':margin,
                  'reconciled_provider_cost':final['total_cost_usd'],'cost_per_success':final['cost_per_success_usd']},indent=2))
