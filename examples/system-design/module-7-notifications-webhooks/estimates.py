"""Hypothetical workload and failure amplification, not a load benchmark."""
def calculate():
    events, fanout, extra_attempt_fraction = 100000, 4, 0.10
    deliveries = events * fanout
    attempts = deliveries * (1+extra_attempt_fraction)
    return {'events_per_day':events, 'average_targets_per_event':fanout,
        'deliveries_per_day':deliveries, 'selected_extra_attempt_fraction':extra_attempt_fraction,
        'attempts_per_day':int(attempts), 'average_attempts_per_second':round(attempts/86400, 3),
        'selected_peak_factor':20, 'hypothetical_peak_attempts_per_second':round(attempts/86400*20, 3),
        'assumed_mean_attempt_seconds':0.2, 'planning_mean_inflight_at_peak':round(attempts/86400*20*0.2, 3),
        'backlog_after_one_hour_at_100_deliveries_per_second':360000,
        'drain_seconds_at_150_service_and_100_new_per_second':7200,
        'seven_day_event_payload_GB_at_1024_bytes':round(events*7*1024/10**9, 4),
        'maximum_attempts_per_delivery_in_fixture':3, 'measured_capacity':False}
