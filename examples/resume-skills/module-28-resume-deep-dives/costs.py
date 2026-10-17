"""Synthetic pricing arithmetic, not provider rates or a payment ledger."""
from decimal import Decimal, ROUND_HALF_UP


def normalized_cost(usage, rate, units_per_rate):
    if any(type(value) is not str for value in (usage, rate, units_per_rate)):
        raise ValueError('Use decimal strings, not binary floats')
    quantity, price, divisor = map(Decimal, (usage, rate, units_per_rate))
    if not all(value.is_finite() for value in (quantity, price, divisor)) or quantity < 0 or price < 0 or divisor <= 0:
        raise ValueError('Invalid usage/rate/unit')
    return quantity * price / divisor


def settle_estimate(lines):
    total = sum((normalized_cost(*line) for line in lines), Decimal('0'))
    return {'unrounded_usd': str(total), 'settled_usd': str(total.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)), 'scope': 'Synthetic usage arithmetic; no provider call, billing reconciliation or ledger debit.'}


def relative_growth(before, after):
    before, after = Decimal(before), Decimal(after)
    if not before.is_finite() or not after.is_finite() or before <= 0 or after < 0:
        raise ValueError('Positive baseline and nonnegative finite result required')
    return (after - before) / before * 100
