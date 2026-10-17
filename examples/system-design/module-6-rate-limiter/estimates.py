"""Hypothetical planning units, not measured throughput or memory usage."""
def calculate():
    requests_day, peak_factor = 8640000, 10
    active_keys, logical_bytes = 1000000, 128
    return {'requests_per_day': requests_day,
            'average_requests_per_second': requests_day / 86400,
            'selected_peak_factor': peak_factor,
            'hypothetical_peak_decisions_per_second': requests_day / 86400 * peak_factor,
            'active_scope_keys': active_keys,
            'assumed_logical_bytes_per_bucket': logical_bytes,
            'logical_bucket_storage_MB': active_keys * logical_bytes / 10**6,
            'three_replicated_logical_copies_MB': 3 * active_keys * logical_bytes / 10**6,
            'sliding_log_example_keys': 100000,
            'sliding_log_events_per_key': 60,
            'assumed_bytes_per_event': 16,
            'sliding_log_event_payload_MB': 100000 * 60 * 16 / 10**6,
            'local_instances': 4,
            'local_capacity_each': 30,
            'possible_aggregate_initial_burst': 4 * 30,
            'measured_capacity': False}
