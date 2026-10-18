"""An offline product worksheet, not a product implementation or release approval."""
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path


def number(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a numeric estimate')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('Expected a finite numeric estimate') from None
    if not result.is_finite():
        raise ValueError('Expected a finite numeric estimate')
    return result


def rice_score(reach, impact, confidence, effort):
    """Reach uses the same period; effort uses the same person-time unit."""
    reach, impact, confidence, effort = map(number, (reach, impact, confidence, effort))
    if reach < 0 or impact <= 0 or not 0 <= confidence <= 1 or effort <= 0:
        raise ValueError('Invalid RICE estimate range')
    return reach * impact * confidence / effort


def unique(rows, label):
    result = {}
    for row in rows:
        identifier = row.get('id')
        if not isinstance(identifier, str) or not identifier.strip() or identifier in result:
            raise ValueError('Missing or duplicate ' + label + ' ID')
        result[identifier] = row
    return result


def rank_backlog(features):
    unique(features, 'feature')
    scored = []
    for feature in features:
        if type(feature['mandatory']) is not bool:
            raise ValueError('mandatory must be boolean')
        score = rice_score(*(feature[key] for key in ('reach', 'impact', 'confidence', 'effort')))
        scored.append({'id': feature['id'], 'score': str(score), 'mandatory': feature['mandatory']})
    mandatory = sorted((row for row in scored if row['mandatory']), key=lambda row: row['id'])
    discretionary = sorted((row for row in scored if not row['mandatory']),
                           key=lambda row: (-Decimal(row['score']), row['id']))
    return {'mandatory': mandatory, 'discretionary': discretionary}


def trace_report(requirements, checks):
    """Summarize supplied check states. No check is executed by this function."""
    if not requirements:
        raise ValueError('At least one requirement is needed')
    unique(requirements, 'requirement')
    by_check = unique(checks, 'check')
    for row in checks:
        if row['method'] not in ('automated', 'manual'):
            raise ValueError('Unknown check method')
        if row['status'] not in ('passed', 'failed', 'pending'):
            raise ValueError('Unknown check status')
    criteria = []
    for requirement in requirements:
        if not requirement['criteria']:
            raise ValueError('A requirement needs acceptance criteria')
        if not requirement['frames'] or not requirement['metrics']:
            raise ValueError('A requirement needs flow and measurement links')
        for criterion in requirement['criteria']:
            if criterion['check'] not in by_check:
                raise ValueError('Unresolved check: ' + criterion['check'])
            check = by_check[criterion['check']]
            criteria.append({'id': criterion['id'], 'requirement': requirement['id'],
                             'check': check['id'], 'method': check['method'], 'status': check['status']})
    unique(criteria, 'criterion')
    used = {row['check'] for row in criteria}
    if used != set(by_check):
        raise ValueError('Unmapped checks cannot inflate criterion coverage')
    passed = sum(row['status'] == 'passed' for row in criteria)
    unresolved = [row['id'] for row in criteria if row['status'] != 'passed']
    return {'criteria': len(criteria), 'supplied_passes': passed,
            'passed_fraction': str(Decimal(passed) / len(criteria)),
            'unresolved': unresolved, 'worksheet_ready': not unresolved,
            'scope': 'Supplied synthetic evidence states; no application was tested or approved.'}


def change_impact(requirements, requirement_id):
    by_requirement = unique(requirements, 'requirement')
    if requirement_id not in by_requirement:
        raise ValueError('Unknown requirement')
    requirement = by_requirement[requirement_id]
    return {'requirement': requirement_id,
            'criteria': sorted(row['id'] for row in requirement['criteria']),
            'checks': sorted({row['check'] for row in requirement['criteria']}),
            'frames': sorted(set(requirement['frames'])),
            'metrics': sorted(set(requirement['metrics']))}


def demo(case):
    return {'evidence_kind': case['evidence_kind'], 'ranking': rank_backlog(case['features']),
            'traceability': trace_report(case['requirements'], case['checks']),
            'draft_change': change_impact(case['requirements'], 'R02')}


if __name__ == '__main__':
    case = json.loads(Path(__file__).with_name('case.json').read_text(encoding='utf-8'))
    print(json.dumps(demo(case), indent=2))
