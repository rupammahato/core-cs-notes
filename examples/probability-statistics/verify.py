"""Independent finite enumeration, algebraic references and selected boundaries."""
from collections import Counter
from fractions import Fraction as F
from itertools import combinations, permutations, product
import hashlib
import json
import math
import platform
from statistics import NormalDist, correlation, linear_regression, quantiles
from compute import BASE, bayes, binomial, calculate, mean_interval, quantile, regression, student_cdf, student_quantile, welch, wilson

checks = []
sources = [BASE/'compute.py', BASE/'verify.py']
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
actual = calculate()


def near(a, b, tolerance=1e-8):
    if isinstance(b, dict):
        return all(k in a and near(a[k], value, tolerance) for k, value in b.items())
    if isinstance(b, list):
        return len(a) == len(b) and all(near(x, y, tolerance) for x, y in zip(a, b))
    if isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)
    return a == b


def check(group, name, got, want, tolerance=1e-8):
    assert near(got, want, tolerance), (name, got, want)
    checks.append({'group': group, 'name': name, 'passed': True})


def example(key, values):
    check('worked-example', key + ' independent reference projection', actual[key], values)


def t4_cdf(x):
    u = x/math.sqrt(x*x+4)
    return .5+.75*u-.25*u**3


def root(fn, target, low=0., high=20.):
    for _ in range(70):
        mid = (low+high)/2
        if fn(mid) < target:
            low = mid
        else:
            high = mid
    return (low+high)/2


def trapezoid_t_cdf(x, df):
    # A fixed-grid trapezoid reference, distinct from adaptive Simpson integration.
    n = 100000
    step = abs(x)/n
    factor = math.gamma((df+1)/2)/math.gamma(df/2)/math.sqrt(df*math.pi)
    def density(v):
        return factor/(1+v*v/df)**((df+1)/2)
    area = step*(.5*density(0)+sum(density(i*step) for i in range(1, n))+.5*density(abs(x)))
    return .5+math.copysign(area, x)


example('E01', {'outcomes': 36, 'at_least_one_six': float(F(11, 36)), 'both_six': float(F(1, 36)), 'exactly_one_six': float(F(10, 36))})
example('E02', {'unordered_committees': len(list(combinations(range(5), 3))), 'ordered_roles': len(list(permutations(range(5), 3)))})
balls = ['R', 'R', 'R', 'B', 'B']
example('E03', {'two_red_without_replacement': sum(balls[i] == balls[j] == 'R' for i, j in combinations(range(5), 2))/10,
                 'two_red_with_replacement': sum(a == b == 'R' for a, b in product(balls, repeat=2))/25})
example('E04', {'shared_birthday_probability': float(1-F(math.perm(365, 23), 365**23))})
example('E05', {'expected_draws_to_collect_all': sum((-1)**(k+1)*math.comb(3, k)*F(3, k) for k in range(1, 4))})
cards = list(product(['red', 'black'], range(1, 14), range(2)))
red = [card for card in cards if card[0] == 'red']
kings = [card for card in cards if card[1] == 13]
example('E06', {'king_given_red': sum(card[1] == 13 for card in red)/len(red), 'red_given_king': sum(card[0] == 'red' for card in kings)/len(kings)})
example('E07', {'fraud_given_alert': 90/585, 'true_alerts_per_10000': 90, 'false_alerts_per_10000': 495})
example('E08', {'error_probability': 190/10000, 'server_B_given_error': 120/190})
flags = [(a, b, a != b) for a, b in product([False, True], repeat=2)]
example('E09', {'P_A': sum(a for a, _, _ in flags)/4, 'P_B': sum(b for _, b, _ in flags)/4,
                 'P_C': sum(c for _, _, c in flags)/4, 'P_all_three': 0., 'product_of_marginals': 1/8,
                 'P_A_and_B': sum(a and b for a, b, _ in flags)/4,
                 'P_A_and_C': sum(a and c for a, _, c in flags)/4,
                 'P_B_and_C': sum(b and c for _, b, c in flags)/4})
example('E10', {'two_conditionally_independent_alerts': 8100/10575, 'duplicate_of_same_alert': 90/585})
mass = Counter()
for bits in product([0, 1], repeat=10):
    mass[sum(bits)] += F(1, 5)**sum(bits)*F(4, 5)**(10-sum(bits))
example('E11', {'P_X_equals_3': float(mass[3]), 'mean': float(sum(k*p for k, p in mass.items())),
                 'variance': float(sum((k-2)**2*p for k, p in mass.items()))})
example('E12', {'expected_trials_including_success': 4., 'P_T_greater_3': 27/64})
example('E13', {'P_at_least_2': sum(math.exp(-1)/math.factorial(k) for k in range(2, 31)), 'expected_arrivals_in_half_hour': 1.})
example('E14', {'mean_wait_minutes': 2., 'P_wait_greater_4': math.exp(-2), 'P_wait_greater_6_given_greater_2': math.exp(-2)})
example('E15', {'P_X_greater_130': 1-NormalDist(100, 15).cdf(130), 'P_X_equals_130': 0., 'z_score': 2.})
values = [2, 3, 3, 4, 100]
ss = sum(F(v)**2 for v in values)-F(sum(values)**2, len(values))
example('E16', {'mean': sum(values)/5, 'median': 3, 'population_variance': float(ss/5), 'sample_variance': float(ss/4)})
q1, _, q3 = quantiles(list(range(1, 9)), method='inclusive')
example('E17', {'Q1_linear': q1, 'Q3_linear': q3, 'IQR': q3-q1, 'p95_nearest_rank': 8})
observations = [1]*2+[0]*8+[1]*90+[0]*10
example('E18', {'pooled_rate': sum(observations)/len(observations), 'unweighted_segment_average': .55})
example('E19', {'ordered_samples': 9, 'mean_of_sample_means': 2., 'variance_of_sample_means': 8/2, 'population_variance': 8.})
example('E20', {'unordered_samples': 6, 'mean_of_sample_means': 3., 'variance_without_replacement': 5/2*(2/3), 'variance_with_replacement': 2.5, 'variance_correction': 2/3})
z = root(lambda v: .5*(1+math.erf(v/math.sqrt(2))), .975)
example('E21', {'se': 1., 'z_critical': z, 'ci_low': 50-z, 'ci_high': 50+z})
critical4 = root(t4_cdf, .975)
example('E22', {'mean': 10., 'sample_sd': math.sqrt(2.5), 'se': math.sqrt(.5), 'critical': critical4,
                 'low': 10-critical4/math.sqrt(2), 'high': 10+critical4/math.sqrt(2)})
example('E23', {'wilson_low': 0., 'wilson_high': z*z/(20+z*z), 'wald_low': 0., 'wald_high': 0.})
example('E24', {'ordered_index_resamples': 27, 'mean_frequencies': {0: 8, 2: 12, 4: 6, 6: 1},
                 'percentile_95_low': 0., 'percentile_95_high': 4.7, 'exact_empirical_bootstrap_se': math.sqrt(8/3)})
mass = Counter()
for bits in product([0, 1], repeat=10):
    mass[sum(bits)] += F(1, 10)**sum(bits)*F(9, 10)**(10-sum(bits))
example('E25', {'wilson': {'covering_counts': [0, 1, 2], 'coverage': float(sum(mass[k] for k in [0, 1, 2]))},
                 'wald': {'covering_counts': [1, 2, 3, 4], 'coverage': float(sum(mass[k] for k in [1, 2, 3, 4]))}})
example('E26', {'included_counts': [0, 1, 2, 8, 9, 10], 'two_sided_probability_ordered_p': sum(sum(bits) <= 2 or sum(bits) >= 8 for bits in product([0, 1], repeat=10))/1024})
a, b = actual['E27']['A'], actual['E27']['B']
ma, mb = sum(a)/len(a), sum(b)/len(b)
va = (sum(v*v for v in a)-sum(a)**2/len(a))/(len(a)-1)/len(a)
vb = (sum(v*v for v in b)-sum(b)**2/len(b))/(len(b)-1)/len(b)
df = (va+vb)**2/(va*va/(len(a)-1)+vb*vb/(len(b)-1))
t = (mb-ma)/math.sqrt(va+vb)
critical = root(lambda x: trapezoid_t_cdf(x, df), .975)
example('E27', {'difference_B_minus_A': mb-ma, 'se': math.sqrt(va+vb), 't': t, 'df': df,
                 'two_sided_p': 2*(1-trapezoid_t_cdf(t, df)), 'ci_low': mb-ma-critical*math.sqrt(va+vb), 'ci_high': mb-ma+critical*math.sqrt(va+vb)})
t = 2.4/math.sqrt(1.3/5)
example('E28', {'paired_differences': [2, 1, 3, 2, 4], 'mean': 2.4, 'se': math.sqrt(1.3/5), 't': t,
                 'two_sided_p': 2*(1-t4_cdf(t)), 'low': 2.4-critical4*math.sqrt(1.3/5), 'high': 2.4+critical4*math.sqrt(1.3/5)})
example('E29', {'balanced_assignments': math.comb(6, 3), 'absolute_difference_at_least_observed': 2, 'exact_two_sided_p': 1/10})
za, zb = NormalDist().inv_cdf(.975), NormalDist().inv_cdf(.8)
# Independent power-equation root: retain the declared normal approximation.
required = root(lambda n: (math.sqrt(n)*.03-za*math.sqrt(2*.215*.785))/math.sqrt(.2*.8+.23*.77), zb, 1., 10000.)
example('E30', {'approx_n_per_arm_unrounded': required, 'approx_n_per_arm_ceiling': math.ceil(required),
                 'independent_20_null_tests_family_error': float(1-F(19, 20)**20), 'bonferroni_20_test_threshold': .0025})
x, y = [1, 2, 3, 4, 5], [2, 4, 5, 4, 5]
slope, intercept = linear_regression(x, y)
example('E31', {'slope': slope, 'intercept': intercept, 'r': correlation(x, y), 'r_squared': .6, 'sse': 2.4})
example('E32', {'r': 0., 'r_squared': 0., 'slope': 0., 'intercept': 2., 'sse': 14.})
example('E33', {'A_easy': .9, 'B_easy': .95, 'A_hard': .1, 'B_hard': .2, 'A_overall': .82, 'B_overall': .35, 'A_equal_mix': .5, 'B_equal_mix': .575})
example('E34', {'theta': .6, 'raw_mean': 4., 'adjusted_mean': 4., 'raw_sample_variance': 1.5, 'adjusted_sample_variance': .6, 'descriptive_variance_reduction': .6})
example('E35', {'training_mse': .48, 'residual_variance_estimate': .8, 'prediction_at_x_6': 5.8, 'out_of_sample_mse': None})

for df in [1, 2, 4]:
    for t in [-3., 0., 2.]:
        reference = .5+math.atan(t)/math.pi if df == 1 else .5+t/(2*math.sqrt(t*t+2)) if df == 2 else t4_cdf(t)
        check('numerical-reference', f't CDF df={df} t={t}', student_cdf(t, df), reference)
for df, value in [(4, 2.776), (9, 2.262), (11, 2.201)]:
    check('published-table', f'NIST 0.975 quantile df={df}', student_quantile(.975, df), value, 5e-4)
for n in [1, 5, 20]:
    check('boundary', f'Binomial PMF sums to one n={n}', sum(binomial(n, k, .3) for k in range(n+1)), 1.)
    check('boundary', f'Wilson all-success/zero symmetry n={n}', wilson(n, n)[0], 1-wilson(0, n)[1])
check('boundary', 'Bayes prior sensitivity scenario', bayes(.1, .9, .05), 2/3)
check('boundary', 'Zero-prior alert remains zero posterior', bayes(0., .9, .05), 0.)
check('boundary', 'Quantile endpoints', [quantile([4, 1, 9], 0), quantile([4, 1, 9], 1)], [1., 9.])
check('boundary', 'Welch swaps direction and preserves two-sided p',
      {'difference': welch(b, a)['difference_B_minus_A'], 'p': welch(b, a)['two_sided_p']},
      {'difference': -actual['E27']['difference_B_minus_A'], 'p': actual['E27']['two_sided_p']})
check('boundary', 'Regression response shift changes only intercept',
      {k: regression(x, [v+10 for v in y])[k] for k in ['slope', 'intercept', 'r']},
      {'slope': .6, 'intercept': 12.2, 'r': math.sqrt(.6)})
check('boundary', 'Regression normal equations', [sum(actual['E31']['residuals']), sum(v*e for v, e in zip(x, actual['E31']['residuals']))], [0., 0.])
invalid = [
    ('Out-of-range probability', lambda: bayes(-.1, .9, .05)),
    ('Impossible conditioning event', lambda: bayes(0., 1., 0.)),
    ('Empty quantile input', lambda: quantile([], .5)),
    ('Invalid Wilson counts', lambda: wilson(21, 20)),
    ('Invalid confidence level', lambda: wilson(2, 20, 1.)),
    ('Insufficient mean sample', lambda: mean_interval([1])),
    ('Degenerate mean sample', lambda: mean_interval([1, 1])),
    ('Degenerate regression predictor', lambda: regression([1, 1, 1], [1, 2, 3])),
    ('Invalid t degrees of freedom', lambda: student_cdf(1., 0.)),
    ('Invalid binomial trial count', lambda: binomial(-1, 0, .5)),
]
for name, fn in invalid:
    try:
        fn()
    except ValueError:
        check('invalid-input', name, True, True)
    else:
        raise AssertionError(name)
snapshot = json.loads((BASE/'prior-notes-snapshot.json').read_text(encoding='utf-8'))
check('preservation', 'All 135 previous handbooks remain byte-identical',
      all(hashlib.sha256((BASE.parents[1]/name).read_bytes()).hexdigest() == digest for name, digest in snapshot.items()), True)
check('preservation', 'Calculation and verifier sources unchanged during run',
      {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, hashes)
proof = {'verified_date': '2026-10-21', 'python': platform.python_version(), 'total': len(checks),
         'breakdown': dict(Counter(c['group'] for c in checks)), 'checks': checks, 'source_sha256': hashes,
         'examples': 35, 'numerical_tolerance': '1e-8 default; published three-decimal t table 5e-4',
         'scope': 'Synthetic finite examples, independent reference projections, closed-form CDFs, alternative quadrature, published critical values and selected boundaries. Not production statistical software certification or real experiment evidence.',
         'random_simulation_used': False, 'external_services_called': False}
(BASE/'results.json').write_text(json.dumps(actual, indent=2)+'\n', encoding='utf-8')
(BASE/'verification-results.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key: proof[key] for key in ['verified_date', 'python', 'total', 'breakdown', 'examples']}, indent=2))
