"""Offline USD teaching arithmetic. No provider, payment, ledger or accounting integration."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP, localcontext
import json
from pathlib import Path


def amount(value):
    if type(value) is not str:
        raise ValueError('Use decimal strings')
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError('Invalid decimal') from None
    if not result.is_finite() or not 0 <= result <= Decimal('1000000000000'):
        raise ValueError('Amount outside teaching range')
    if result.as_tuple().exponent < -12:
        raise ValueError('At most twelve decimal places')
    return result


def count(value, positive=False):
    if type(value) is not int or not (1 if positive else 0) <= value <= 10**12:
        raise ValueError('Expected bounded integer quantity')
    return value


def shown(value):
    with localcontext() as ctx:
        ctx.prec = 60
        return None if value is None else format(value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP), 'f')


def rate_index(rates):
    result = {}
    for row in rates:
        key = tuple(row[field] for field in ('provider', 'model', 'version', 'unit'))
        if not all(type(field) is str and field.strip() for field in key) or key in result:
            raise ValueError('Invalid or duplicate tariff identity')
        if row['currency'] != 'USD':
            raise ValueError('Explicit currency conversion required')
        amount(row['price']); count(row['per'], positive=True)
        result[key] = row
    return result


def attempt_cost(attempt, rates):
    prefix = tuple(attempt[field] for field in ('provider', 'model', 'rate_version'))
    if not any(key[:3] == prefix for key in rates):
        raise ValueError('Unknown provider/model/rate version')
    if attempt['usage'] is None:
        return None
    total = Decimal(0)
    units = set()
    with localcontext() as ctx:
        ctx.prec = 60
        for line in attempt['usage']:
            if line['unit'] in units:
                raise ValueError('Duplicate usage unit within one attempt')
            units.add(line['unit'])
            key = (*prefix, line['unit'])
            if key not in rates:
                raise ValueError('No matching usage tariff')
            rate = rates[key]
            total += Decimal(count(line['quantity'])) * amount(rate['price']) / count(rate['per'], positive=True)
    return total


def aggregate(jobs, attempts, rates):
    by_job = {}
    for job in jobs:
        if type(job['id']) is not str or not job['id'].strip() or job['id'] in by_job:
            raise ValueError('Invalid or duplicate job ID')
        if job['status'] not in ('success', 'failed'):
            raise ValueError('Use a closed cohort of final jobs')
        by_job[job['id']] = job
    by_attempt = {}; duplicates = 0
    for attempt in attempts:
        key = attempt['id']
        if type(key) is not str or not key.strip() or attempt['job'] not in by_job:
            raise ValueError('Invalid attempt identity or job link')
        if attempt['status'] not in ('success', 'failed', 'timeout'):
            raise ValueError('Unknown attempt status')
        if key in by_attempt:
            if by_attempt[key] != attempt:
                raise ValueError('Conflicting duplicate attempt report')
            duplicates += 1
        else:
            by_attempt[key] = attempt
    tariffs = rate_index(rates)
    rows = []; known = Decimal(0); unknown = []; by_provider = {}
    for job in jobs:
        linked = [row for row in by_attempt.values() if row['job'] == job['id']]
        if not linked:
            raise ValueError('Missing attempt evidence for job')
        if job['status'] == 'success' and not any(row['status'] == 'success' for row in linked):
            raise ValueError('Successful job needs a successful attempt')
        subtotal = Decimal(0); missing = []
        for attempt in linked:
            cost = attempt_cost(attempt, tariffs)
            if cost is None:
                missing.append(attempt['id']); unknown.append(attempt['id'])
            else:
                with localcontext() as ctx:
                    ctx.prec = 60
                    subtotal += cost
                    by_provider[attempt['provider']] = by_provider.get(attempt['provider'], Decimal(0)) + cost
        with localcontext() as ctx:
            ctx.prec = 60
            known += subtotal
        rows.append({'id': job['id'], 'status': job['status'], 'known_cost_usd': shown(subtotal),
                     'total_cost_usd': None if missing else shown(subtotal), 'unknown_attempts': missing})
    successes = sum(job['status'] == 'success' for job in jobs)
    with localcontext() as ctx:
        ctx.prec = 60
        per_success = known / successes if successes and not unknown else None
    return {'jobs': len(jobs), 'successful_jobs': successes, 'unique_attempts': len(by_attempt),
            'duplicate_reports_ignored': duplicates, 'known_cost_usd': shown(known),
            'total_cost_usd': None if unknown else shown(known),
            'cost_per_success_usd': shown(per_success), 'unknown_attempts': unknown,
            'provider_known_cost_usd': {key: shown(value) for key, value in sorted(by_provider.items())},
            'job_costs': rows}


def margins(revenue, cogs, other_variable='0', fixed='0'):
    revenue, cogs, other_variable, fixed = map(amount, (revenue, cogs, other_variable, fixed))
    gross = revenue - cogs
    contribution = gross - other_variable
    with localcontext() as ctx:
        ctx.prec = 60
        gross_pct = gross / revenue * 100 if revenue else None
        contribution_pct = contribution / revenue * 100 if revenue else None
    return {'revenue_usd': shown(revenue), 'cogs_usd': shown(cogs), 'gross_profit_usd': shown(gross),
            'gross_margin_pct': shown(gross_pct), 'other_variable_usd': shown(other_variable),
            'contribution_usd': shown(contribution), 'contribution_margin_pct': shown(contribution_pct),
            'scenario_after_fixed_usd': shown(contribution - fixed)}


def price_for_margin(cost, target):
    cost, target = amount(cost), amount(target)
    if target >= 1:
        raise ValueError('Target margin must be below one')
    with localcontext() as ctx:
        ctx.prec = 60
        price = cost / (1 - target)
    return {'unrounded_usd': format(price, 'f'),
            'cent_price_usd': format(price.quantize(Decimal('0.01'), rounding=ROUND_CEILING), 'f')}


def break_even(fixed, price, variable):
    fixed, price, variable = map(amount, (fixed, price, variable))
    if price <= variable:
        return None
    with localcontext() as ctx:
        ctx.prec = 60
        return int((fixed / (price - variable)).to_integral_value(rounding=ROUND_CEILING))


def credit_service_value(consumed, pack_price, pack_credits):
    """Simple single-pack allocation, not a revenue-recognition or credit-ledger engine."""
    with localcontext() as ctx:
        ctx.prec = 60
        value = Decimal(count(consumed)) * amount(pack_price) / count(pack_credits, positive=True)
    return shown(value)


def ideal_retry_cost(attempt_usd, success_probability):
    """Unlimited independent equal-cost attempts until success; no time/budget cap."""
    cost, probability = amount(attempt_usd), amount(success_probability)
    if not 0 < probability <= 1:
        raise ValueError('Success probability must be in (0, 1]')
    with localcontext() as ctx:
        ctx.prec = 60
        return shown(cost / probability)


def demo(case):
    initial = aggregate(case['jobs'], case['attempts'], case['rates'])
    reconciled = [{**row, 'usage': case['reconciled_usage'][row['id']]}
                  if row['id'] in case['reconciled_usage'] else row for row in case['attempts']]
    final = aggregate(case['jobs'], reconciled, case['rates'])
    cogs = amount(final['total_cost_usd']) + amount(case['other_delivery_cost_usd'])
    revenue = Decimal(final['successful_jobs']) * amount(case['price_per_success_usd'])
    return {'scope': case['scope'], 'before_reconciliation': initial, 'after_reconciliation': final,
            'cohort_margin': margins(str(revenue), str(cogs), case['allocated_payment_fees_usd']),
            'target_price': price_for_margin('0.06', '0.60'),
            'break_even_successes': break_even('1000', '0.20', '0.07'),
            'ideal_retry_cost_usd': ideal_retry_cost('0.04', '0.8'),
            'credit_values': {'standard_20_credits_usd': credit_service_value(20, '10', 1000),
                              'discounted_20_credits_usd': credit_service_value(20, '8', 1000),
                              'promotional_20_credits_usd': credit_service_value(20, '0', 1000)}}


if __name__ == '__main__':
    case = json.loads(Path(__file__).with_name('case.json').read_text(encoding='utf-8'))
    print(json.dumps(demo(case), indent=2))
