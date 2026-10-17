"""Offline hypothetical load/placement arithmetic; no capacity or shard deployment test."""
from collections import Counter
from hashlib import sha256
import math


def demand(read_qps, hit_fraction, instances, pool_per_instance, db_budget, utilization=0.7):
    if type(read_qps) is not int or read_qps < 0 or not 0 <= hit_fraction <= 1:
        raise ValueError('invalid workload')
    if type(instances) is not int or instances < 1 or type(pool_per_instance) is not int or pool_per_instance < 1:
        raise ValueError('positive instance and pool counts required')
    if type(db_budget) is not int or db_budget < 1 or not 0 < utilization <= 1:
        raise ValueError('invalid database budget or utilization')
    return {'read_qps': read_qps, 'assumed_hit_fraction': hit_fraction,
            'estimated_db_read_qps': round(read_qps*(1-hit_fraction), 6),
            'maximum_application_connections': instances*pool_per_instance,
            'application_connection_budget': math.floor(db_budget*utilization)}


def place(tenant, shards):
    if type(shards) is not int or shards < 1:
        raise ValueError('positive shard count required')
    return int.from_bytes(sha256(tenant.encode('utf-8')).digest()[:8], 'big') % shards


def placement_demo(shards=4):
    # Each tenant has one synthetic request weight, not a measured trace.
    weights = {f'tenant_{i:03}': 1 for i in range(100)}
    weights['tenant_000'] = 901  # One tenant supplies 90.1% of the 1000 requests.
    by_shard = Counter()
    for tenant, weight in weights.items():
        by_shard[place(tenant, shards)] += weight
    moved = sum(place(tenant, shards) != place(tenant, shards+1) for tenant in weights)
    return {'tenants': len(weights), 'synthetic_requests': sum(weights.values()),
            'hot_tenant_requests': weights['tenant_000'],
            'requests_by_shard': {str(i): by_shard[i] for i in range(shards)},
            'tenants_remapped_on_modulo_resize': moved, 'remap_denominator_tenants': len(weights)}
