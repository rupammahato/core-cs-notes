import math
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from openai import APIStatusError


def retry_delay(header, attempt, now=None, random_value=None):
    if header is not None:
        try:
            delay = float(header)
        except ValueError:
            try:
                date = parsedate_to_datetime(header)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                delay = (date - (now or datetime.now(timezone.utc))).total_seconds()
            except (ValueError, TypeError, OverflowError):
                delay = float('nan')
        if math.isfinite(delay) and delay >= 0:
            return delay
    jitter = random.random() if random_value is None else random_value
    return min(4.0, 0.25 * 2 ** (attempt - 1)) * (0.5 + 0.5 * jitter)


def retry_read_only(operation, max_attempts=3, budget_seconds=2.0, sleep=time.sleep, clock=time.monotonic):
    deadline = clock() + budget_seconds
    for attempt in range(1, max_attempts + 1):
        if clock() >= deadline:
            raise TimeoutError('Retry budget exhausted')
        try:
            return operation(deadline - clock())
        except APIStatusError as error:
            # This sample retries only known pre-completion HTTP failures of a read-only request.
            code = error.code
            transient = error.status_code in (429, 500, 502, 503, 504)
            if not transient or code in ('insufficient_quota', 'billing_hard_limit_reached') or attempt == max_attempts:
                raise
            delay = retry_delay(error.response.headers.get('retry-after'), attempt)
            if delay >= deadline - clock():
                raise TimeoutError('Server retry hint exceeds remaining budget') from error
            sleep(delay)
    raise ValueError('max_attempts must be positive')
