"""Hypothetical object/processing workload; no load or cloud cost benchmark."""
def calculate():
    daily, size, days = 10000, 2*1024*1024, 30
    return {'uploads_per_day':daily, 'assumed_mean_bytes_per_upload':size,
        'average_incoming_MiB_per_second':round(daily*size/86400/1024**2, 3),
        'selected_peak_multiplier':10, 'hypothetical_peak_uploads_per_second':round(daily/86400*10,3),
        'raw_30_day_storage_GiB':round(daily*size*days/1024**3,3),
        'assumed_derived_fraction':0.25, 'derived_30_day_storage_GiB':round(daily*size*days*0.25/1024**3,3),
        'assumed_CPU_seconds_per_processing_job':2,
        'average_required_CPU_cores_at_full_utilization':round(daily*2/86400,3),
        'selected_downloads_per_upload':5, 'daily_download_GiB':round(daily*size*5/1024**3,3),
        'unfinished_sessions_per_day':1000, 'assumed_parts_per_session':4,
        'assumed_MiB_per_part':8, 'one_day_unfinished_parts_GiB':31.25,
        'fixture_max_upload_bytes':1024, 'measured_capacity':False}
