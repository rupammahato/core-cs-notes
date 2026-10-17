"""Hypothetical workload and random-code arithmetic, not measured capacity."""
import math


def calculate(creates_per_day=10000,redirects_per_day=1000000,days=365,length=8,record_bytes=512):
    if any(type(value) is not int or value<1 for value in (creates_per_day,redirects_per_day,days,length,record_bytes)):
        raise ValueError('positive integer assumptions required')
    if length>32:
        raise ValueError('code exercise length bound exceeded')
    population,space = creates_per_day*days,62**length
    if population>space:
        raise ValueError('hypothetical population exceeds namespace')
    expected_pairs = population*(population-1)/(2*space)
    return {'assumed_creates_per_day':creates_per_day,'assumed_redirects_per_day':redirects_per_day,
            'average_create_qps':creates_per_day/86400,'average_redirect_qps':redirects_per_day/86400,
            'assumed_peak_multiplier':10,'assumed_peak_redirect_qps':redirects_per_day/86400*10,
            'assumed_days':days,'new_links_in_period':population,'code_length':length,'alphabet_size':62,
            'namespace_size':space,'code_entropy_bits':length*math.log2(62),
            'expected_collision_pairs_approx':expected_pairs,
            'probability_at_least_one_collision_approx':-math.expm1(-expected_pairs),
            'next_draw_collision_probability_at_end':population/space,
            'assumed_logical_record_bytes':record_bytes,'logical_link_storage_bytes':population*record_bytes,
            'storage_excludes':['operation outcomes','indexes','replicas','backups','analytics'],
            'automatic_code_reuse_implemented':False}
