"""Explicit planning arithmetic; capacity values are assumptions, not measurements."""
from dataclasses import asdict, dataclass, replace
from math import ceil, isfinite


@dataclass(frozen=True)
class Workload:
    users: int = 100000
    reads_per_user_day: int = 30
    writes_per_user_day: int = 3
    seconds_per_day: int = 86400
    peak_factor: float = 8
    mean_request_ms: float = 150
    creation_fraction_of_writes: float = 0.4
    record_bytes: int = 2048
    retention_days: int = 365
    physical_copies: int = 3
    storage_overhead_factor: float = 1.5
    read_response_bytes: int = 4096
    write_response_bytes: int = 512
    assumed_instance_qps: float = 100
    target_utilization: float = 0.65


def estimate(workload=Workload()):
    values = asdict(workload)
    zero_allowed = {'reads_per_user_day', 'writes_per_user_day', 'creation_fraction_of_writes'}
    if any(type(value) not in (int, float) or not isfinite(value) or value < 0 or (value == 0 and name not in zero_allowed) for name, value in values.items()):
        raise ValueError('Finite numeric assumptions with valid positive/zero bounds required')
    if workload.creation_fraction_of_writes > 1 or workload.target_utilization >= 1 or workload.peak_factor < 1 or workload.storage_overhead_factor < 1 or workload.reads_per_user_day + workload.writes_per_user_day == 0:
        raise ValueError('Invalid fraction/utilization')
    for name in ('users', 'reads_per_user_day', 'writes_per_user_day', 'seconds_per_day', 'record_bytes', 'retention_days', 'physical_copies', 'read_response_bytes', 'write_response_bytes'):
        if type(values[name]) is not int:
            raise ValueError('Count/byte/time-unit fields must be integers')
    reads = workload.users * workload.reads_per_user_day
    writes = workload.users * workload.writes_per_user_day
    avg = (reads + writes) / workload.seconds_per_day
    peak = avg * workload.peak_factor
    new_records = writes * workload.creation_fraction_of_writes
    records = new_records * workload.retention_days
    logical_bytes = records * workload.record_bytes
    planned_bytes = logical_bytes * workload.physical_copies * workload.storage_overhead_factor
    target = workload.assumed_instance_qps * workload.target_utilization
    response_bandwidth = (reads * workload.read_response_bytes + writes * workload.write_response_bytes) / workload.seconds_per_day * workload.peak_factor
    return {'assumptions': values, 'reads_per_day': reads, 'writes_per_day': writes,
            'average_qps': avg, 'assumed_peak_qps': peak,
            'mean_in_flight_at_assumed_peak': peak * workload.mean_request_ms / 1000,
            'new_records_per_day': new_records, 'retained_records': records,
            'logical_storage_bytes': logical_bytes, 'planned_physical_storage_bytes': planned_bytes,
            'planned_physical_storage_decimal_gb': planned_bytes / 10**9,
            'planned_physical_storage_gib': planned_bytes / 2**30,
            'peak_response_payload_bytes_per_second': response_bandwidth,
            'target_qps_per_instance': target, 'healthy_instances': ceil(peak / target),
            'fleet_for_one_failed_instance': ceil(peak / target) + 1,
            'scope': 'Calculated scenario only. Per-instance capacity, peak multiplier, copies/overhead and retained-creation rate are assumptions; no benchmark or actual replication.'}


def sensitivity(workload=Workload()):
    scenarios = {'baseline': workload, 'double_users': replace(workload, users=workload.users * 2),
                 'double_mean_time': replace(workload, mean_request_ms=workload.mean_request_ms * 2),
                 'double_record_size': replace(workload, record_bytes=workload.record_bytes * 2)}
    return {name: {field: result[field] for field in ('assumed_peak_qps', 'mean_in_flight_at_assumed_peak', 'planned_physical_storage_bytes', 'healthy_instances')}
            for name, scenario in scenarios.items() for result in [estimate(scenario)]}
