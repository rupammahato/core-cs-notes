"""Small, explicit teaching calculations. Standard library only; no external data."""
from collections import Counter
from fractions import Fraction as F
from itertools import combinations, product
import json
import math
from pathlib import Path
from statistics import NormalDist, mean, median, variance, pvariance, covariance

BASE = Path(__file__).resolve().parent
NORMAL = NormalDist()


def probability(p):
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError('Probability must lie in [0, 1]')


def binomial(n, k, p):
    probability(p)
    if not isinstance(n, int) or n < 0 or not isinstance(k, int):
        raise ValueError('Integer count required')
    return math.comb(n, k) * p**k * (1-p)**(n-k) if 0 <= k <= n else 0


def bayes(prior, sensitivity, false_positive):
    for p in [prior, sensitivity, false_positive]:
        probability(p)
    evidence = prior*sensitivity + (1-prior)*false_positive
    if not evidence:
        raise ValueError('Conditioning event has zero probability')
    return prior*sensitivity/evidence


def quantile(values, q):
    probability(q)
    if not values:
        raise ValueError('Nonempty observations required')
    ordered = sorted(values)
    location = (len(ordered)-1)*q
    low = math.floor(location)
    high = math.ceil(location)
    return ordered[low] + (location-low)*(ordered[high]-ordered[low])


def wilson(k, n, level=.95):
    if not isinstance(n, int) or not isinstance(k, int) or n <= 0 or not 0 <= k <= n:
        raise ValueError('Require integer 0 <= k <= n and n > 0')
    if not 0 < level < 1:
        raise ValueError('Require confidence level in (0, 1)')
    z = NORMAL.inv_cdf((1+level)/2)
    p = k/n
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return max(0., center-half), min(1., center+half)


def student_cdf(t, df):
    """Adaptive Simpson integration of the t density; tested in the book's range."""
    if not math.isfinite(t) or not math.isfinite(df) or df < 1:
        raise ValueError('Require finite t and df >= 1 for this teaching integrator')
    constant = math.exp(math.lgamma((df+1)/2)-math.lgamma(df/2))/math.sqrt(df*math.pi)
    def density(x):
        return constant*(1+x*x/df)**(-(df+1)/2)
    def integrate(a, b, fa, fm, fb, whole, tolerance, depth):
        middle = (a+b)/2
        left_mid = density((a+middle)/2)
        right_mid = density((middle+b)/2)
        left = (middle-a)*(fa+4*left_mid+fm)/6
        right = (b-middle)*(fm+4*right_mid+fb)/6
        delta = left+right-whole
        if abs(delta) <= 15*tolerance:
            return left+right+delta/15
        if depth == 0:
            raise ArithmeticError('Integration tolerance not achieved')
        return integrate(a, middle, fa, left_mid, fm, left, tolerance/2, depth-1) + integrate(
            middle, b, fm, right_mid, fb, right, tolerance/2, depth-1)
    upper = abs(t)
    if not upper:
        return .5
    fa, fm, fb = density(0), density(upper/2), density(upper)
    area = integrate(0, upper, fa, fm, fb, upper*(fa+4*fm+fb)/6, 1e-11, 22)
    return min(1., max(0., .5+math.copysign(area, t)))


def student_quantile(p, df):
    if not .5 < p < 1:
        raise ValueError('This helper accepts upper-half quantiles only')
    low, high = 0., 1.
    while student_cdf(high, df) < p:
        high *= 2
        if high > 1024:
            raise ValueError('Quantile outside teaching range')
    for _ in range(50):
        mid = (low+high)/2
        if student_cdf(mid, df) < p:
            low = mid
        else:
            high = mid
    return (low+high)/2


def mean_interval(values):
    if len(values) < 2:
        raise ValueError('At least two observations required')
    se = math.sqrt(variance(values)/len(values))
    if not se:
        raise ValueError('Zero sample variance needs a separate model')
    critical = student_quantile(.975, len(values)-1)
    return {'mean': mean(values), 'sample_sd': math.sqrt(variance(values)), 'se': se,
            'df': len(values)-1, 'critical': critical,
            'low': mean(values)-critical*se, 'high': mean(values)+critical*se}


def welch(a, b):
    if min(len(a), len(b)) < 2:
        raise ValueError('Each independent sample needs at least two observations')
    va, vb = variance(a)/len(a), variance(b)/len(b)
    if va+vb == 0:
        raise ValueError('Zero variance needs a separate model')
    se = math.sqrt(va+vb)
    df = (va+vb)**2/(va*va/(len(a)-1)+vb*vb/(len(b)-1))
    delta = mean(b)-mean(a)
    critical = student_quantile(.975, df)
    return {'difference_B_minus_A': delta, 'se': se, 't': delta/se, 'df': df,
            'two_sided_p': 2*(1-student_cdf(abs(delta/se), df)),
            'ci_low': delta-critical*se, 'ci_high': delta+critical*se}


def regression(x, y):
    if len(x) != len(y) or len(x) < 3 or not pvariance(x) or not pvariance(y):
        raise ValueError('Need equal, nonconstant paired samples of length >= 3')
    mx, my = mean(x), mean(y)
    sxx = sum((v-mx)**2 for v in x)
    syy = sum((v-my)**2 for v in y)
    sxy = sum((a-mx)*(b-my) for a, b in zip(x, y))
    slope = sxy/sxx
    intercept = my-slope*mx
    residuals = [b-(intercept+slope*a) for a, b in zip(x, y)]
    sse = sum(v*v for v in residuals)
    return {'slope': slope, 'intercept': intercept, 'r': sxy/math.sqrt(sxx*syy),
            'r_squared': 1-sse/syy, 'sse': sse, 'residuals': residuals}


def calculate():
    r = {}
    dice = list(product(range(1, 7), repeat=2))
    r['E01'] = {'outcomes': len(dice), 'at_least_one_six': sum(6 in pair for pair in dice)/len(dice),
                'both_six': 1/36, 'exactly_one_six': sum(pair.count(6) == 1 for pair in dice)/36}
    r['E02'] = {'unordered_committees': math.comb(5, 3), 'ordered_roles': math.perm(5, 3)}
    r['E03'] = {'two_red_without_replacement': math.comb(3, 2)/math.comb(5, 2), 'two_red_with_replacement': (3/5)**2}
    r['E04'] = {'people': 23, 'shared_birthday_probability': 1-math.prod((365-i)/365 for i in range(23))}
    r['E05'] = {'categories': 3, 'expected_draws_to_collect_all': sum(3/k for k in range(1, 4))}
    r['E06'] = {'red_cards': 26, 'red_kings': 2, 'king_given_red': 2/26, 'red_given_king': 2/4}
    r['E07'] = {'true_alerts_per_10000': 90, 'false_alerts_per_10000': 495,
                'fraud_given_alert': bayes(.01, .90, .05)}
    r['E08'] = {'error_probability': .7*.01+.3*.04, 'server_B_given_error': .3*.04/(.7*.01+.3*.04)}
    outcomes = list(product([0, 1], repeat=2))
    r['E09'] = {'P_A': .5, 'P_B': .5, 'P_C': .5,
                'P_A_and_B': .25, 'P_A_and_C': .25, 'P_B_and_C': .25,
                'P_all_three': sum(a and b and (a != b) for a, b in outcomes)/4,
                'product_of_marginals': .5**3}
    r['E10'] = {'two_conditionally_independent_alerts': bayes(.01, .9**2, .05**2),
                'duplicate_of_same_alert': bayes(.01, .9, .05)}
    r['E11'] = {'P_X_equals_3': binomial(10, 3, .2), 'mean': 10*.2, 'variance': 10*.2*.8}
    r['E12'] = {'expected_trials_including_success': 1/.25, 'P_T_greater_3': .75**3}
    r['E13'] = {'expected_arrivals_in_half_hour': 2*.5, 'P_at_least_2': 1-math.exp(-1)*(1+1)}
    r['E14'] = {'mean_wait_minutes': 1/.5, 'P_wait_greater_4': math.exp(-.5*4),
                'P_wait_greater_6_given_greater_2': math.exp(-.5*6)/math.exp(-.5*2)}
    r['E15'] = {'mean': 100, 'sd': 15, 'threshold': 130, 'z_score': 2.,
                'P_X_greater_130': .5*math.erfc(2/math.sqrt(2)), 'P_X_equals_130': 0.}
    values = [2, 3, 3, 4, 100]
    r['E16'] = {'values': values, 'mean': mean(values), 'median': median(values),
                'population_variance': pvariance(values), 'sample_variance': variance(values)}
    values = list(range(1, 9))
    r['E17'] = {'values': values, 'Q1_linear': quantile(values, .25), 'Q3_linear': quantile(values, .75),
                'IQR': quantile(values, .75)-quantile(values, .25), 'p95_nearest_rank': sorted(values)[math.ceil(.95*len(values))-1]}
    r['E18'] = {'small_segment_rate': 2/10, 'large_segment_rate': 90/100,
                'pooled_rate': (2+90)/(10+100), 'unweighted_segment_average': (.2+.9)/2}
    means = [mean(row) for row in product([0, 0, 6], repeat=2)]
    r['E19'] = {'ordered_samples': len(means), 'mean_of_sample_means': mean(means),
                'variance_of_sample_means': pvariance(means), 'population_variance': pvariance([0, 0, 6])}
    means = [mean(row) for row in combinations([0, 2, 4, 6], 2)]
    r['E20'] = {'unordered_samples': len(means), 'mean_of_sample_means': mean(means),
                'variance_without_replacement': pvariance(means), 'variance_with_replacement': pvariance([0, 2, 4, 6])/2,
                'variance_correction': (4-2)/(4-1)}
    z = NORMAL.inv_cdf(.975)
    r['E21'] = {'known_sigma': 10, 'n': 100, 'sample_mean': 50, 'se': 1.,
                'z_critical': z, 'ci_low': 50-z, 'ci_high': 50+z}
    r['E22'] = {'values': [8, 9, 10, 11, 12], **mean_interval([8, 9, 10, 11, 12])}
    low, high = wilson(0, 20)
    r['E23'] = {'successes': 0, 'n': 20, 'wilson_low': low, 'wilson_high': high,
                'wald_low': 0., 'wald_high': 0.}
    means = [mean(row) for row in product([0, 0, 6], repeat=3)]
    r['E24'] = {'original_values': [0, 0, 6], 'ordered_index_resamples': len(means),
                'mean_frequencies': dict(sorted(Counter(means).items())),
                'percentile_95_low': quantile(means, .025), 'percentile_95_high': quantile(means, .975),
                'exact_empirical_bootstrap_se': math.sqrt(pvariance(means))}
    coverage = {}
    for method in ['wilson', 'wald']:
        total = 0.
        accepted = []
        for k in range(11):
            if method == 'wilson':
                low, high = wilson(k, 10)
            else:
                p = k/10
                half = z*math.sqrt(p*(1-p)/10)
                low, high = p-half, p+half
            if low-1e-14 <= .1 <= high+1e-14:
                total += binomial(10, k, .1)
                accepted.append(k)
        coverage[method] = {'true_p': .1, 'n': 10, 'coverage': total, 'covering_counts': accepted}
    r['E25'] = coverage
    observed = binomial(10, 8, F(1, 2))
    tail_counts = [k for k in range(11) if binomial(10, k, F(1, 2)) <= observed]
    r['E26'] = {'heads': 8, 'n': 10, 'included_counts': tail_counts,
                'two_sided_probability_ordered_p': float(sum(binomial(10, k, F(1, 2)) for k in tail_counts))}
    a, b = [10, 12, 9, 11, 13], [13, 15, 14, 16, 12, 18]
    r['E27'] = {'A': a, 'B': b, **welch(a, b)}
    before, after = [10, 20, 30, 40, 50], [12, 21, 33, 42, 54]
    differences = [b-a for a, b in zip(before, after)]
    interval = mean_interval(differences)
    t = interval['mean']/interval['se']
    r['E28'] = {'before': before, 'after': after, 'paired_differences': differences,
                **interval, 't': t, 'two_sided_p': 2*(1-student_cdf(abs(t), 4))}
    values = [1, 2, 3, 4, 5, 6]
    assignments = list(combinations(range(6), 3))
    differences = [mean([values[i] for i in range(6) if i not in chosen])-mean([values[i] for i in chosen]) for chosen in assignments]
    extreme = sum(abs(delta) >= 3 for delta in differences)
    r['E29'] = {'observed_B_minus_A': 3., 'balanced_assignments': len(assignments),
                'absolute_difference_at_least_observed': extreme, 'exact_two_sided_p': extreme/len(assignments)}
    p0, p1 = .2, .23
    pbar = (p0+p1)/2
    n = (z*math.sqrt(2*pbar*(1-pbar))+NORMAL.inv_cdf(.8)*math.sqrt(p0*(1-p0)+p1*(1-p1)))**2/(p1-p0)**2
    r['E30'] = {'baseline': p0, 'alternative': p1, 'alpha_two_sided': .05, 'target_power': .8,
                'approx_n_per_arm_unrounded': n, 'approx_n_per_arm_ceiling': math.ceil(n),
                'independent_20_null_tests_family_error': 1-.95**20, 'bonferroni_20_test_threshold': .05/20}
    x, y = [1, 2, 3, 4, 5], [2, 4, 5, 4, 5]
    fit = regression(x, y)
    r['E31'] = {'x': x, 'y': y, **fit}
    r['E32'] = {'x': [-2, -1, 0, 1, 2], 'y': [4, 1, 0, 1, 4], **regression([-2, -1, 0, 1, 2], [4, 1, 0, 1, 4])}
    r['E33'] = {'A_easy': 81/90, 'B_easy': 19/20, 'A_hard': 1/10, 'B_hard': 16/80,
                'A_overall': 82/100, 'B_overall': 35/100,
                'A_equal_mix': (.9+.1)/2, 'B_equal_mix': (.95+.2)/2}
    theta = covariance(x, y)/variance(x)
    adjusted = [v-theta*(u-mean(x)) for u, v in zip(x, y)]
    r['E34'] = {'theta': theta, 'raw_mean': mean(y), 'adjusted_mean': mean(adjusted),
                'raw_sample_variance': variance(y), 'adjusted_sample_variance': variance(adjusted),
                'descriptive_variance_reduction': 1-variance(adjusted)/variance(y)}
    r['E35'] = {'training_n': len(x), 'training_mse': fit['sse']/len(x),
                'residual_variance_estimate': fit['sse']/(len(x)-2),
                'prediction_at_x_6': fit['intercept']+fit['slope']*6,
                'out_of_sample_mse': None}
    return r


def displayed(value):
    """Six-place presentation; raw outputs are saved separately."""
    if isinstance(value, dict):
        return {str(k): displayed(v) for k, v in value.items()}
    if isinstance(value, list):
        return [displayed(v) for v in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


if __name__ == '__main__':
    import sys
    results = calculate()
    if len(sys.argv) > 1:
        key = sys.argv[1].upper()
        if key not in results:
            raise SystemExit('Choose E01 through E35')
        print(json.dumps(displayed(results[key]), indent=2))
    else:
        (BASE/'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
        print('Recorded all 35 computed examples in results.json')
