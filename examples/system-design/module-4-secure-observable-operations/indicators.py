"""Offline authored SLI samples and hypothetical capacity/cost arithmetic."""
from fractions import Fraction
import math


def percentile(values, quantile):
    if not 0<quantile<=1 or any(not math.isfinite(value) or value<0 for value in values):
        raise ValueError('invalid percentile inputs')
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(quantile*len(ordered))-1]  # Explicit nearest-rank convention.


def analyze(samples, target='0.99', threshold_ms=200):
    target = Fraction(target)
    if not 0<target<1 or not math.isfinite(threshold_ms) or threshold_ms<0:
        raise ValueError('invalid objective')
    for sample in samples:
        if type(sample['eligible']) is not bool or type(sample['leak']) is not bool:
            raise ValueError('explicit eligibility and invariant flags required')
        if type(sample['status']) is not int or not 100<=sample['status']<=599:
            raise ValueError('invalid status')
        if not math.isfinite(sample['latency_ms']) or sample['latency_ms']<0:
            raise ValueError('invalid latency')
    eligible = [sample for sample in samples if sample['eligible']]
    good = sum(sample['status'] == 200 and sample['latency_ms']<=threshold_ms for sample in eligible)
    bad, total = len(eligible)-good, len(eligible)
    budget = (1-target)*total
    invariant = not any(sample['leak'] for sample in samples)
    return {'eligible': total, 'excluded': len(samples)-total, 'good': good, 'bad': bad,
            'good_fraction': good/total if total else None,
            'allowed_bad': float(budget), 'remaining_budget': float(budget-bad),
            'burn_rate': float(Fraction(bad,total)/(1-target)) if total else None,
            'p95_ms': percentile([sample['latency_ms'] for sample in eligible], 0.95),
            'p99_ms': percentile([sample['latency_ms'] for sample in eligible], 0.99),
            'invariant_passed': invariant,
            'objective_passed': bool(total) and bad<=budget and invariant}


def sample_workload():
    groups = [(970, True, 200, 50), (20, True, 200, 350),
              (5, True, 503, 20), (5, True, 429, 5), (3, False, 401, 5)]
    return [{'eligible': eligible, 'status': status, 'latency_ms': latency, 'leak': False}
            for count, eligible, status, latency in groups for _ in range(count)]


def capacity_plan(qps=200, mean_service_ms=50, instances=4, pool=20,
                  db_budget=60, hours=720, assumed_hourly_cost='0.10'):
    if type(qps) is not int or qps<0 or not math.isfinite(mean_service_ms) or mean_service_ms<0:
        raise ValueError('invalid workload')
    if any(type(value) is not int or value<1 for value in (instances, pool, db_budget, hours)):
        raise ValueError('positive counts required')
    rate = Fraction(assumed_hourly_cost)
    if rate<0:
        raise ValueError('negative assumed price')
    return {'assumed_qps': qps, 'assumed_mean_service_ms': mean_service_ms,
            'estimated_mean_in_flight': qps*mean_service_ms/1000,
            'application_connection_ceiling': instances*pool, 'selected_db_budget': db_budget,
            'pool_ceiling_fits_budget': instances*pool<=db_budget,
            'assumed_instance_hours': instances*hours,
            'hypothetical_instance_cost': float(rate*instances*hours),
            'cost_excludes': ['database', 'storage', 'network', 'logs', 'backups', 'provider calls']}
