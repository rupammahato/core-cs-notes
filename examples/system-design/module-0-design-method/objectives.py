"""Offline good-event classification over explicitly authored samples."""
from math import isfinite


def assess(samples, deadline_ms=200, goal=0.99):
    if type(deadline_ms) not in (int, float) or not isfinite(deadline_ms) or deadline_ms <= 0 or type(goal) not in (int, float) or not isfinite(goal) or not 0 < goal <= 1:
        raise ValueError('Invalid objective')
    eligible, good, violations = 0, 0, 0
    for sample in samples:
        if any(type(sample.get(field)) is not bool for field in ('eligible', 'correct', 'violates_invariant')):
            raise ValueError('Explicit boolean classification required')
        duration = sample.get('duration_ms')
        if duration is not None and (type(duration) not in (int, float) or not isfinite(duration) or duration < 0):
            raise ValueError('Invalid duration')
        violations += int(sample['violates_invariant'])
        if sample['eligible']:
            eligible += 1
            good += int(sample['correct'] and not sample['violates_invariant'] and duration is not None and duration <= deadline_ms)
    ratio = good / eligible if eligible else None
    met = ratio is not None and ratio >= goal
    return {'eligible_events': eligible, 'good_events': good, 'bad_events': eligible - good,
            'good_fraction': ratio, 'goal': goal, 'deadline_ms': deadline_ms,
            'objective_met': met, 'invariant_violations': violations,
            'design_gate_passed': met and violations == 0,
            'scope': 'Offline classifier over hand-authored samples, not measured service availability, latency or production monitoring.'}
