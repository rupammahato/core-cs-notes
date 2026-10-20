"""Independent reference projections, changed scenarios and rejected contradictions."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import math
import platform
from statistics import NormalDist
from compute import BASE, calculate, fixture

checks=[]
sources=[BASE/'fixture.json',BASE/'compute.py',BASE/'verify.py']
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
data=fixture(); actual=calculate(data)


def matches(got,want):
    if isinstance(want,dict): return all(k in got and matches(got[k],v) for k,v in want.items())
    if isinstance(want,list): return len(got)==len(want) and all(matches(a,b) for a,b in zip(got,want))
    if isinstance(want,bool) or want is None: return got is want
    if isinstance(want,(int,float,F)): return math.isclose(got,float(want),rel_tol=1e-9,abs_tol=1e-12)
    return got==want


def check(group,name,got,want):
    assert matches(got,want),(name,got,want)
    checks.append({'group':group,'name':name,'passed':True})


references={
 'C01':{'baseline_completed':780,'interrupted_not_completed':160,'scenario_additional_completed':80,'scenario_total_completed':860,'scenario_lift_pp':8},
 'C02':{'baseline_ranking':[{'id':'onboarding','score':400},{'id':'admin','score':270},{'id':'notifications','score':250}],
        'lower_confidence_ranking':[{'id':'admin','score':270},{'id':'notifications','score':250},{'id':'onboarding','score':160}]},
 'C03':{'baseline_completion_pct':66,'scenario_extra_completions':70,'scenario_completion_pct':73,'verified_pass_coverage_pct':F(200,3),'unknown_criteria':1,'supplied_critical_gate_passed':False},
 'C04':{'before_overall_pct':78,'after_overall_pct':66,'after_standardized_to_before_mix_pct':78,'observed_change_pp':-12},
 'C05':{'client_after_late_receipts':900,'still_unreconciled':100,'duplicate_server_deliveries':300,'naive_event_value_cents':6500000,'canonical_order_value_cents':5000000},
 'C06':{'before_ctr_pct':30,'after_ctr_pct':45,'before_useful_per_session_pct':20,'after_useful_per_session_pct':18,'before_useful_per_click_pct':F(200,3),'after_useful_per_click_pct':40},
 'C07':{'stage_conversion_pct':[70,F(400,7),75,60],'useful_activation_pct':18,'scenario_extra_useful':45,'scenario_lift_pp':4.5},
 'C08':{'previous_mature_retention_pct':30,'new_naive_all_signup_pct':18,'new_mature_retention_pct':30,'new_revised_mature_retention_pct':35,'immature_signups':400},
 'C09':{'conversion_difference_pp':4,'standardized_incremental_conversions':40,'scenario_incremental_contribution_cents':15000,'cost_per_incremental_conversion_cents':125,'unsubscribe_increase_pp':3,'supplied_guardrail_passed':False},
 'C10':{'net_collected_cents':1800,'known_variable_cost_cents':1390,'scenario_contribution_cents':410,'scenario_contribution_margin_pct':F(205,9),'cost_per_useful_job_cents':F(139,8),'net_collection_floor_at_unchanged_cost_cents':2780},
 'C11':{'baseline_unit_contribution_cents':4000,'discounted_unit_contribution_cents':2000,'baseline_total_contribution_cents':400000,'scenario_total_contribution_cents':360000,'required_volume_multiplier':2},
 'C12':{'platform_denominator_cac_cents':400,'deduplicated_new_customer_cac_cents':500,'activated_customer_cac_cents':750,'static_payback_months':1.5,'lifetime_value_cents':None},
 'C13':{'requests':100,'available_slots':60,'matches':45,'completed':40,'match_rate_pct':45,'fulfillment_rate_pct':40,'completion_given_match_pct':F(800,9),'unmatched_by_zone':{'A':15,'B':22,'C':18},'capacity_only_ceiling_after_added_slots':80},
 'C14':{'capacity_per_hour':45,'load_to_capacity':F(4,3),'fluid_backlog_after_busy_period':60,'agents_for_target_utilization':5,'fluid_clearance_hours_at_later_arrival_rate':4},
 'C15':{'old':{'precision_pct':10,'recall_pct':50,'missed_fraud':100,'modeled_prevention_minus_review_cents':980000},'new':{'precision_pct':18,'recall_pct':45,'missed_fraud':110,'modeled_prevention_minus_review_cents':890000}},
 'C16':{'observed_conversion_difference_pp':5,'srm_chi_square':20,'srm_asymptotic_p':2*NormalDist().cdf(-math.sqrt(20)),'supplied_srm_gate_passed':False,'assignment_verified':False},
 'C17':{'old_conditional_grounded_correct_pct':80,'new_conditional_grounded_correct_pct':80,'old_all_question_grounded_correct_pct':72,'new_all_question_grounded_correct_pct':76,'new_cost_per_grounded_correct_cents':F(450,19),'supplied_permission_gate_passed':False},
 'C18':{'canary_bad_unique_requests':30,'canary_good_pct':97,'previous_budget_burn_ratio':F(4,5),'canary_budget_burn_ratio':3,'combined_budget_burn_ratio':1,'supplied_canary_gate_passed':False},
}
for key,want in references.items(): check('reference',key+' independent arithmetic projection',actual[key],want)


def changed(name,key,updates,want):
    sample=deepcopy(data);sample[key].update(updates)
    check('changed-scenario',name,calculate(sample)[key],want)


changed('No assumed draft recovery creates no forecast lift','C01',{'assumed_recovery_share':0},{'scenario_total_completed':780,'scenario_lift_pp':0})
changed('Low onboarding confidence changes ranking','C02',{'lower_onboarding_confidence':0},{'lower_confidence_ranking':[{'id':'admin','score':270},{'id':'notifications','score':250},{'id':'onboarding','score':0}]})
changed('Repairing the supplied critical failure changes only that gate','C03',{'critical_failures':0,'verified_passes':5},{'supplied_critical_gate_passed':True,'unknown_criteria':1,'scenario_completion_pct':73})
changed('Same device mix restores same pooled rate','C04',{'after_mobile_users':400,'after_mobile_completed':240,'after_desktop_users':600,'after_desktop_completed':540},{'observed_change_pp':0})
changed('All missing client identities arrive consistently','C05',{'late_unique':300},{'still_unreconciled':0})
changed('Empty funnel has no invented activation rate','C07',{'eligible_mature':0,'started':0,'uploaded':0,'answered':0,'useful':0,'assumed_extra_uploads':0},{'useful_activation_pct':None,'scenario_extra_useful':None})
changed('Fully mature new cohort removes denominator discrepancy','C08',{'new_mature':1000,'new_returns':300,'late_valid_returns':0},{'new_naive_all_signup_pct':30,'new_mature_retention_pct':30})
changed('Exact declared unsubscribe boundary passes','C09',{'treatment_unsubscribed':30},{'unsubscribe_increase_pp':1,'supplied_guardrail_passed':True})
changed('Failed attempts remain an explicit cost sensitivity','C10',{'failed_attempts':0},{'known_variable_cost_cents':1150,'scenario_contribution_cents':650})
changed('Zero discounted contribution has no finite volume remedy','C11',{'discount_share':.4},{'discounted_unit_contribution_cents':0,'required_volume_multiplier':None})
changed('No spare capacity leaves clearance time undefined','C14',{'later_arrivals_per_hour':45},{'fluid_clearance_hours_at_later_arrival_rate':None})
changed('Configured allocation explains the supplied assignment counts','C16',{'planned_treatment_share':.45},{'srm_chi_square':0,'srm_asymptotic_p':1,'supplied_srm_gate_passed':True,'assignment_verified':False})
changed('Overlap changes union without changing marginal error counts','C18',{'canary_both':0},{'canary_bad_unique_requests':35,'canary_budget_burn_ratio':3.5})

invalid=[
 ('Interrupted population exceeds eligible users','C01',{'interrupted':1001}),
 ('Pass/fail criterion states overlap their total','C03',{'verified_passes':6,'critical_failures':1}),
 ('Client receipt partitions exceed the server set','C05',{'late_unique':301}),
 ('Useful sessions exceed clicked sessions','C06',{'after_useful':451}),
 ('Funnel stages increase','C07',{'uploaded':701}),
 ('Retention returns exceed mature users','C08',{'new_returns':601}),
 ('Unit margin target is impossible','C10',{'target_contribution_margin':1}),
 ('Bad-request overlap exceeds its marginal set','C18',{'canary_both':21}),
]
for name,key,updates in invalid:
    sample=deepcopy(data);sample[key].update(updates)
    try: calculate(sample)
    except ValueError: check('invalid-input',name,True,True)
    else: raise AssertionError(name)
snapshot=json.loads((BASE/'prior-notes-snapshot.json').read_text(encoding='utf-8'))
check('preservation','All 144 earlier handbook bytes preserved',len(snapshot)==144 and all(hashlib.sha256((BASE.parents[1]/name).read_bytes()).hexdigest()==digest for name,digest in snapshot.items()),True)
check('preservation','Input/calculation/verifier sources unchanged during run',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},hashes)
proof={'verified_date':'2026-10-21','python':platform.python_version(),'total':len(checks),'breakdown':dict(Counter(c['group'] for c in checks)),
       'checks':checks,'source_sha256':hashes,'scope':'Synthetic aggregate arithmetic and declared gate rules, selected scenario changes and contradictions. Does not verify actual users, assignment, model labels, causal effects or whether an authored product recommendation is optimal.',
       'external_services_called':False,'real_experiments_run':False,'deployments_performed':False}
(BASE/'results.json').write_text(json.dumps(actual,indent=2)+'\n',encoding='utf-8')
(BASE/'verification-results.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:proof[k] for k in ['verified_date','python','total','breakdown']},indent=2))
