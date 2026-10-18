"""Verify worksheet arithmetic and malformed-evidence handling, without a product server."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import platform
from workshop import change_impact, demo, rank_backlog, rice_score, trace_report

BASE = Path(__file__).resolve().parent
case = json.loads((BASE / 'case.json').read_text(encoding='utf-8'))
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


for name, args, expected in [
    ('draft score', (120, 2, '0.8', 2), '96'),
    ('status score ties draft', (120, 1, '0.8', 1), '96'),
    ('AI score', (80, 2, '0.5', 4), '20'),
    ('zero reach', (0, 2, '0.8', 2), '0'),
    ('zero confidence', (120, 2, 0, 2), '0'),
    ('full confidence', (120, 2, 1, 2), '120'),
    ('confidence sensitivity', (120, 2, '0.5', 2), '60'),
    ('effort sensitivity', (120, 2, '0.8', 4), '48')]:
    check('arithmetic', name, rice_score(*args), Decimal(expected))
for name, args in [
    ('negative reach', (-1, 1, 1, 1)), ('zero impact', (1, 0, 1, 1)),
    ('negative impact', (1, -1, 1, 1)), ('negative confidence', (1, 1, '-0.1', 1)),
    ('confidence over one', (1, 1, '1.01', 1)), ('zero effort', (1, 1, 1, 0)),
    ('negative effort', (1, 1, 1, -1)), ('boolean estimate', (True, 1, 1, 1)),
    ('NaN', ('NaN', 1, 1, 1)), ('infinity', (1, 'Infinity', 1, 1)),
    ('non-numeric input', ('many', 1, 1, 1))]:
    rejects('input', name, lambda args=args: rice_score(*args))
ranking = rank_backlog(case['features'])
check('ranking', 'mandatory is separate', [r['id'] for r in ranking['mandatory']], ['secure-entry'])
check('ranking', 'stable equal-score tie', [r['id'] for r in ranking['discretionary']], ['resume-draft', 'status-page', 'ai-summary'])
check('ranking', 'input order cannot break ties', rank_backlog(list(reversed(case['features']))), ranking)
features = deepcopy(case['features']); features[1]['confidence'] = '0.5'
check('ranking', 'lower confidence changes ordering', [r['id'] for r in rank_backlog(features)['discretionary']], ['status-page', 'resume-draft', 'ai-summary'])
features = deepcopy(case['features']); features[0]['reach'] = 0
check('ranking', 'zero-score protection stays mandatory', rank_backlog(features)['mandatory'][0]['id'], 'secure-entry')
rejects('ranking', 'duplicate feature ID', lambda: rank_backlog(case['features'] + [case['features'][0]]))
features = deepcopy(case['features']); features[0]['mandatory'] = 'false'
rejects('ranking', 'string is not a mandatory flag', lambda: rank_backlog(features))
report = trace_report(case['requirements'], case['checks'])
for name, key, expected in [
    ('eight acceptance criteria', 'criteria', 8), ('five supplied passes', 'supplied_passes', 5),
    ('exact supplied pass fraction', 'passed_fraction', '0.625'),
    ('pending IDs remain visible', 'unresolved', ['AC06', 'AC07', 'AC08']),
    ('pending is not ready', 'worksheet_ready', False)]:
    check('traceability', name, report[key], expected)
complete = deepcopy(case['checks'])
for row in complete:
    row['status'] = 'passed'
check('traceability', 'all supplied states passed', trace_report(case['requirements'], complete)['worksheet_ready'], True)
complete[0]['status'] = 'failed'
check('traceability', 'one failed criterion blocks readiness', trace_report(case['requirements'], complete)['worksheet_ready'], False)
check('traceability', 'failed criterion stays visible', trace_report(case['requirements'], complete)['unresolved'], ['AC01'])
rejects('traceability', 'empty scope is not success', lambda: trace_report([], []))
rejects('traceability', 'duplicate requirement ID', lambda: trace_report(case['requirements'] + [case['requirements'][0]], case['checks']))
rejects('traceability', 'missing check link', lambda: trace_report(case['requirements'], case['checks'][:-1]))
rejects('traceability', 'duplicate check ID', lambda: trace_report(case['requirements'], case['checks'] + [case['checks'][0]]))
extra = {'id': 'T99', 'method': 'automated', 'status': 'passed'}
rejects('traceability', 'unmapped check cannot inflate coverage', lambda: trace_report(case['requirements'], case['checks'] + [extra]))
requirements = deepcopy(case['requirements']); requirements[0]['criteria'][0]['id'] = 'AC08'
rejects('traceability', 'duplicate criterion ID', lambda: trace_report(requirements, case['checks']))
requirements = deepcopy(case['requirements']); requirements[0]['criteria'] = []
rejects('traceability', 'empty acceptance criteria', lambda: trace_report(requirements, case['checks']))
requirements = deepcopy(case['requirements']); requirements[0]['frames'] = []
rejects('traceability', 'missing flow link', lambda: trace_report(requirements, case['checks']))
requirements = deepcopy(case['requirements']); requirements[0]['metrics'] = []
rejects('traceability', 'missing metric link', lambda: trace_report(requirements, case['checks']))
states = deepcopy(case['checks']); states[0]['status'] = 'looks good'
rejects('traceability', 'unknown check status', lambda: trace_report(case['requirements'], states))
states = deepcopy(case['checks']); states[0]['method'] = 'telepathy'
rejects('traceability', 'unknown check method', lambda: trace_report(case['requirements'], states))
impact = change_impact(case['requirements'], 'R02')
for name, key, expected in [
    ('draft criteria', 'criteria', ['AC03', 'AC04']), ('draft checks', 'checks', ['T03', 'T04']),
    ('draft frames', 'frames', ['F03-draft', 'F04-saved']), ('draft metric', 'metrics', ['draft_restore_success'])]:
    check('change', name, impact[key], expected)
rejects('change', 'unknown requirement', lambda: change_impact(case['requirements'], 'R99'))
snapshot = deepcopy(case)
output = demo(case)
check('boundaries', 'worksheet does not mutate source evidence', case, snapshot)
check('boundaries', 'synthetic input label retained', output['evidence_kind'], case['evidence_kind'])
check('boundaries', 'scope does not claim application validation', 'no application was tested' in output['traceability']['scope'], True)
proof = {'verified_date': '2026-10-18', 'python': platform.python_version(),
         'os': platform.platform(), 'total': len(checks), 'checks': checks,
         'observations': output, 'persistent_listener_started': False,
         'external_services_called': False,
         'scope': 'Executed offline arithmetic, ranking, input validation, supplied-evidence traceability and change-impact checks. No real product, users, Figma account or Notion workspace tested.'}
(BASE / 'verification-results.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
(BASE / 'worksheet-output.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': len(checks), 'observations': output}, indent=2))
