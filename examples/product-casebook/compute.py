"""Explicit calculations over synthetic case aggregates; not automatic product advice."""
from copy import deepcopy
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent


def fixture():
    return json.loads((BASE/'fixture.json').read_text(encoding='utf-8'))


def count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('Count must be a nonnegative integer')


def subset(n, d):
    count(n); count(d)
    if n > d:
        raise ValueError('Subset exceeds its declared population')


def share(value, inclusive=True):
    if not math.isfinite(value) or not (0 <= value <= 1 if inclusive else 0 < value < 1):
        raise ValueError('Invalid probability/share')


def ratio(n, d):
    return n/d if d else None


def pct(n, d):
    return 100*n/d if d else None


def calculate(data=None):
    data = deepcopy(data) if data is not None else fixture()
    r = {}
    p = data['C01']
    subset(p['interrupted'], p['eligible'])
    subset(p['interrupted_completed'], p['interrupted'])
    subset(p['uninterrupted_completed'], p['eligible']-p['interrupted'])
    share(p['assumed_recovery_share'])
    base = p['interrupted_completed']+p['uninterrupted_completed']
    unmet = p['interrupted']-p['interrupted_completed']
    recovered = unmet*p['assumed_recovery_share']
    r['C01'] = {'baseline_completed': base, 'interrupted_not_completed': unmet,
                'scenario_additional_completed': recovered, 'scenario_total_completed': base+recovered,
                'scenario_lift_pp': pct(recovered, p['eligible'])}
    p = data['C02']
    def ranking(lower=False):
        rows = []
        for row in p['candidates']:
            count(row['reach']); share(row['confidence'])
            if row['effort'] <= 0 or row['impact'] < 0:
                raise ValueError('Positive effort and nonnegative impact required')
            confidence = p['lower_onboarding_confidence'] if lower and row['id'] == 'onboarding' else row['confidence']
            share(confidence)
            rows.append({'id':row['id'], 'score':row['reach']*row['impact']*confidence/row['effort']})
        if len({row['id'] for row in rows}) != len(rows):
            raise ValueError('Candidate identities must be unique')
        return sorted(rows, key=lambda row:(-row['score'], row['id']))
    r['C02'] = {'baseline_ranking': ranking(), 'lower_confidence_ranking': ranking(True)}
    p = data['C03']
    subset(p['mobile_completed'], p['mobile_users']); subset(p['desktop_completed'], p['desktop_users'])
    subset(p['verified_passes'], p['criteria']); count(p['critical_failures']); share(p['assumed_mobile_lift'])
    if p['verified_passes']+p['critical_failures'] > p['criteria']:
        raise ValueError('Mutually exclusive supplied pass/fail states exceed criteria')
    total = p['mobile_users']+p['desktop_users']
    completed = p['mobile_completed']+p['desktop_completed']
    extra = min(p['mobile_users']*p['assumed_mobile_lift'], p['mobile_users']-p['mobile_completed'])
    r['C03'] = {'baseline_completion_pct': pct(completed, total), 'scenario_extra_completions': extra,
                'scenario_completion_pct': pct(completed+extra, total),
                'verified_pass_coverage_pct': pct(p['verified_passes'], p['criteria']),
                'unknown_criteria': p['criteria']-p['verified_passes']-p['critical_failures'],
                'supplied_critical_gate_passed': p['critical_failures'] == 0}
    p = data['C04']
    for period in ['before','after']:
        for device in ['mobile','desktop']:
            subset(p[f'{period}_{device}_completed'], p[f'{period}_{device}_users'])
    before_total = p['before_mobile_users']+p['before_desktop_users']
    after_total = p['after_mobile_users']+p['after_desktop_users']
    before_rate = ratio(p['before_mobile_completed']+p['before_desktop_completed'], before_total)
    after_rate = ratio(p['after_mobile_completed']+p['after_desktop_completed'], after_total)
    mobile_rate = ratio(p['after_mobile_completed'], p['after_mobile_users'])
    desktop_rate = ratio(p['after_desktop_completed'], p['after_desktop_users'])
    standardized = (p['before_mobile_users']*mobile_rate+p['before_desktop_users']*desktop_rate)/before_total if before_total and mobile_rate is not None and desktop_rate is not None else None
    r['C04'] = {'before_overall_pct': None if before_rate is None else before_rate*100,
                'after_overall_pct': None if after_rate is None else after_rate*100,
                'after_standardized_to_before_mix_pct': None if standardized is None else standardized*100,
                'observed_change_pp': None if before_rate is None or after_rate is None else (after_rate-before_rate)*100}
    p = data['C05']
    for value in p.values(): count(value)
    if p['client_unique_received']+p['late_unique'] > p['server_paid_orders'] or p['raw_server_events'] < p['server_paid_orders']:
        raise ValueError('Declared disjoint reconciliation sets do not reconcile')
    r['C05'] = {'client_after_late_receipts': p['client_unique_received']+p['late_unique'],
                'still_unreconciled': p['server_paid_orders']-p['client_unique_received']-p['late_unique'],
                'duplicate_server_deliveries': p['raw_server_events']-p['server_paid_orders'],
                'naive_event_value_cents': p['raw_server_events']*p['order_price_cents'],
                'canonical_order_value_cents': p['server_paid_orders']*p['order_price_cents']}
    p = data['C06']
    for period in ['before','after']:
        subset(p[f'{period}_useful'], p[f'{period}_clicks']); subset(p[f'{period}_clicks'], p['sessions_per_period'])
    r['C06'] = {'before_ctr_pct': pct(p['before_clicks'],p['sessions_per_period']),
                'after_ctr_pct': pct(p['after_clicks'],p['sessions_per_period']),
                'before_useful_per_session_pct': pct(p['before_useful'],p['sessions_per_period']),
                'after_useful_per_session_pct': pct(p['after_useful'],p['sessions_per_period']),
                'before_useful_per_click_pct': pct(p['before_useful'],p['before_clicks']),
                'after_useful_per_click_pct': pct(p['after_useful'],p['after_clicks'])}
    p = data['C07']
    stages = [p[k] for k in ['eligible_mature','started','uploaded','answered','useful']]
    for first, second in zip(stages, stages[1:]): subset(second, first)
    count(p['assumed_extra_uploads'])
    if p['uploaded']+p['assumed_extra_uploads'] > p['started']:
        raise ValueError('Scenario uploads exceed eligible starters')
    later = ratio(p['useful'],p['uploaded'])
    extra = None if later is None else p['assumed_extra_uploads']*later
    r['C07'] = {'stage_conversion_pct': [pct(b,a) for a,b in zip(stages,stages[1:])],
                'useful_activation_pct': pct(p['useful'],p['eligible_mature']),
                'scenario_extra_useful': extra, 'scenario_lift_pp': None if extra is None else pct(extra,p['eligible_mature'])}
    p = data['C08']
    for period in ['previous','new']:
        subset(p[f'{period}_returns'],p[f'{period}_mature']); subset(p[f'{period}_mature'],p[f'{period}_signups'])
    subset(p['late_valid_returns'],p['new_mature']-p['new_returns'])
    r['C08'] = {'previous_mature_retention_pct': pct(p['previous_returns'],p['previous_mature']),
                'new_naive_all_signup_pct': pct(p['new_returns'],p['new_signups']),
                'new_mature_retention_pct': pct(p['new_returns'],p['new_mature']),
                'new_revised_mature_retention_pct': pct(p['new_returns']+p['late_valid_returns'],p['new_mature']),
                'immature_signups': p['new_signups']-p['new_mature']}
    p = data['C09']
    for arm in ['control','treatment']:
        subset(p[f'{arm}_converted'],p[f'{arm}_users']); subset(p[f'{arm}_unsubscribed'],p[f'{arm}_users'])
    if not p['control_users'] or not p['treatment_users']:
        raise ValueError('Positive arm denominators required for standardized contrast')
    incremental = p['treatment_converted']-p['treatment_users']*p['control_converted']/p['control_users']
    unsub_pp = pct(p['treatment_unsubscribed'],p['treatment_users'])-pct(p['control_unsubscribed'],p['control_users'])
    r['C09'] = {'conversion_difference_pp': pct(p['treatment_converted'],p['treatment_users'])-pct(p['control_converted'],p['control_users']),
                'standardized_incremental_conversions': incremental,
                'scenario_incremental_contribution_cents': incremental*p['contribution_per_conversion_cents']-p['delivery_cost_cents'],
                'cost_per_incremental_conversion_cents': ratio(p['delivery_cost_cents'],incremental) if incremental>0 else None,
                'unsubscribe_increase_pp': unsub_pp, 'supplied_guardrail_passed': unsub_pp<=p['allowed_unsubscribe_increase_pp']}
    p = data['C10']
    for key in ['price_cents','refund_cents','useful_jobs','failed_attempts','cost_per_attempt_cents','payment_cost_cents','storage_cost_cents']: count(p[key])
    subset(p['refund_cents'],p['price_cents']); share(p['target_contribution_margin'])
    if p['target_contribution_margin'] == 1: raise ValueError('Target margin must be below one')
    collected = p['price_cents']-p['refund_cents']
    cost = (p['useful_jobs']+p['failed_attempts'])*p['cost_per_attempt_cents']+p['payment_cost_cents']+p['storage_cost_cents']
    r['C10'] = {'net_collected_cents': collected, 'known_variable_cost_cents': cost,
                'scenario_contribution_cents': collected-cost, 'scenario_contribution_margin_pct': pct(collected-cost,collected),
                'cost_per_useful_job_cents': ratio(cost,p['useful_jobs']),
                'net_collection_floor_at_unchanged_cost_cents': cost/(1-p['target_contribution_margin'])}
    p = data['C11']
    for key in ['price_cents','variable_cost_cents','baseline_units','scenario_units']: count(p[key])
    share(p['discount_share'])
    before = p['price_cents']-p['variable_cost_cents']
    after = p['price_cents']*(1-p['discount_share'])-p['variable_cost_cents']
    r['C11'] = {'baseline_unit_contribution_cents': before,'discounted_unit_contribution_cents':after,
                'baseline_total_contribution_cents':before*p['baseline_units'],
                'scenario_total_contribution_cents':after*p['scenario_units'],
                'required_volume_multiplier': before/after if before>0 and after>0 else None}
    p = data['C12']
    for value in p.values(): count(value)
    subset(p['activated_new_customers'],p['deduplicated_new_customers'])
    if p['platform_claimed_acquisitions'] < p['deduplicated_new_customers']: raise ValueError('This fixture models overclaim, not underclaim')
    cac = ratio(p['spend_cents'],p['activated_new_customers'])
    r['C12'] = {'platform_denominator_cac_cents':ratio(p['spend_cents'],p['platform_claimed_acquisitions']),
                'deduplicated_new_customer_cac_cents':ratio(p['spend_cents'],p['deduplicated_new_customers']),
                'activated_customer_cac_cents':cac,
                'static_payback_months':ratio(cac,p['assumed_monthly_contribution_cents']) if cac is not None else None,
                'lifetime_value_cents':None}
    p = data['C13']
    for zone in p['zones']:
        subset(zone['matches'],zone['requests']); subset(zone['matches'],zone['slots'])
    requests=sum(z['requests'] for z in p['zones']); slots=sum(z['slots'] for z in p['zones']); matches=sum(z['matches'] for z in p['zones'])
    subset(p['completed'],matches); count(p['assumed_added_slots'])
    r['C13'] = {'requests':requests,'available_slots':slots,'matches':matches,'completed':p['completed'],
                'match_rate_pct':pct(matches,requests),'fulfillment_rate_pct':pct(p['completed'],requests),
                'completion_given_match_pct':pct(p['completed'],matches),
                'unmatched_by_zone':{z['id']:z['requests']-z['matches'] for z in p['zones']},
                'capacity_only_ceiling_after_added_slots':min(requests,slots+p['assumed_added_slots'])}
    p = data['C14']
    for key in ['agents','service_per_agent_per_hour','arrivals_per_hour','busy_hours','later_arrivals_per_hour']: count(p[key])
    share(p['target_utilization'],False)
    if p['service_per_agent_per_hour'] == 0: raise ValueError('Service capacity must be positive')
    capacity=p['agents']*p['service_per_agent_per_hour']; backlog=max(0,p['arrivals_per_hour']-capacity)*p['busy_hours']
    spare=capacity-p['later_arrivals_per_hour']
    r['C14'] = {'capacity_per_hour':capacity,'load_to_capacity':ratio(p['arrivals_per_hour'],capacity),
                'fluid_backlog_after_busy_period':backlog,
                'agents_for_target_utilization':math.ceil(p['arrivals_per_hour']/(p['service_per_agent_per_hour']*p['target_utilization'])),
                'fluid_clearance_hours_at_later_arrival_rate':backlog/spare if spare>0 else None}
    p = data['C15']
    for value in p.values(): count(value)
    for version in ['old','new']:
        subset(p[f'{version}_true_alerts'],p[f'{version}_alerts']); subset(p[f'{version}_true_alerts'],p['actual_fraud'])
    r['C15']={}
    for version in ['old','new']:
        caught=p[f'{version}_true_alerts']; alerts=p[f'{version}_alerts']
        r['C15'][version]={'precision_pct':pct(caught,alerts),'recall_pct':pct(caught,p['actual_fraud']),
                          'missed_fraud':p['actual_fraud']-caught,
                          'modeled_prevention_minus_review_cents':caught*p['assumed_prevented_loss_per_caught_cents']-alerts*p['review_cost_cents']}
    p = data['C16']
    for arm in ['control','treatment']: subset(p[f'{arm}_converted'],p[f'{arm}_assigned'])
    share(p['planned_treatment_share'],False); share(p['srm_threshold'],False)
    total=p['control_assigned']+p['treatment_assigned']
    if not total or not p['control_assigned'] or not p['treatment_assigned']: raise ValueError('Positive assignment counts required')
    expected_t=total*p['planned_treatment_share']; expected_c=total-expected_t
    chi=(p['control_assigned']-expected_c)**2/expected_c+(p['treatment_assigned']-expected_t)**2/expected_t
    tail=math.erfc(math.sqrt(chi/2))
    r['C16']={'observed_conversion_difference_pp':pct(p['treatment_converted'],p['treatment_assigned'])-pct(p['control_converted'],p['control_assigned']),
               'srm_chi_square':chi,'srm_asymptotic_p':tail,'supplied_srm_gate_passed':tail>=p['srm_threshold'],
               'assignment_verified':False}
    p = data['C17']
    for version in ['old','new']:
        subset(p[f'{version}_grounded_correct'],p[f'{version}_answered']); subset(p[f'{version}_answered'],p['questions'])
        subset(p[f'{version}_permission_failures'],p['questions'])
    count(p['new_total_cost_cents'])
    r['C17']={'old_conditional_grounded_correct_pct':pct(p['old_grounded_correct'],p['old_answered']),
              'new_conditional_grounded_correct_pct':pct(p['new_grounded_correct'],p['new_answered']),
              'old_all_question_grounded_correct_pct':pct(p['old_grounded_correct'],p['questions']),
              'new_all_question_grounded_correct_pct':pct(p['new_grounded_correct'],p['questions']),
              'new_cost_per_grounded_correct_cents':ratio(p['new_total_cost_cents'],p['new_grounded_correct']),
              'supplied_permission_gate_passed':p['new_permission_failures']==0}
    p = data['C18']
    subset(p['previous_bad'],p['previous_requests']); subset(p['canary_error'],p['canary_requests']); subset(p['canary_slow'],p['canary_requests'])
    subset(p['canary_both'],min(p['canary_error'],p['canary_slow'])); share(p['slo_good_share'],False)
    bad=p['canary_error']+p['canary_slow']-p['canary_both']; subset(bad,p['canary_requests'])
    budget_share=1-p['slo_good_share']
    before_burn=ratio(p['previous_bad'],p['previous_requests']*budget_share)
    canary_burn=ratio(bad,p['canary_requests']*budget_share)
    r['C18']={'canary_bad_unique_requests':bad,'canary_good_pct':pct(p['canary_requests']-bad,p['canary_requests']),
              'previous_budget_burn_ratio':before_burn,'canary_budget_burn_ratio':canary_burn,
              'combined_budget_burn_ratio':ratio(p['previous_bad']+bad,(p['previous_requests']+p['canary_requests'])*budget_share),
              'supplied_canary_gate_passed':canary_burn is not None and canary_burn<=p['canary_burn_stop_above']}
    return r


def displayed(value):
    if isinstance(value,dict): return {str(k):displayed(v) for k,v in value.items()}
    if isinstance(value,list): return [displayed(v) for v in value]
    if isinstance(value,float): return float(f'{value:.6g}') if 0<abs(value)<.000001 else round(value,6)
    return value


if __name__=='__main__':
    import sys
    results=calculate()
    if len(sys.argv)>1:
        key=sys.argv[1].upper()
        if key not in results: raise SystemExit('Choose C01 through C18')
        print(json.dumps(displayed(results[key]),indent=2))
    else:
        (BASE/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
        print('Recorded all 18 synthetic case calculations.')
