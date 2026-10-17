"""Bounded owned-loopback adapter; redirects are never followed."""
from http.client import HTTPConnection, HTTPException
import secrets
from protocol import sign


def post(job, endpoint, now):
    port, path, secret = endpoint
    if type(port) is not int or not 1024 <= port <= 65535 or not path.startswith('/hooks/'):
        raise ValueError('invalid owned lesson endpoint')
    timestamp = now//1000
    headers = {'Content-Type':'application/json', 'X-Lesson-Delivery':job['id'],
               'X-Lesson-Timestamp':str(timestamp),
               'X-Lesson-Signature':sign(secret, timestamp, job['id'], job['body'])}
    connection = HTTPConnection('127.0.0.1', port, timeout=0.25)
    try:
        connection.request('POST', path, body=job['body'], headers=headers)
        response = connection.getresponse()
        value = response.getheader('Retry-After', '')
        # Selected lesson contract: decimal delay-seconds up to one day, not HTTP-date.
        retry_ms = int(value)*1000 if value.isascii() and value.isdigit() and len(value) <= 5 and int(value) <= 86400 else 0
        # Fixture receiver has no body; don't buffer an arbitrary response body.
        return response.status, retry_ms
    except (OSError, HTTPException):
        return None, 0  # Unknown outcome; receiver may already have committed.
    finally:
        connection.close()


def run_once(queue, registry, now, completed_at=None, jitter=None):
    job = queue.claim(now)
    if job is None:
        return None
    status, retry_ms = post(job, registry[(job['tenant'], job['endpoint'])], now)
    cap = min(8000, 500 * 2**(job['attempts']-1))
    delay = (jitter or (lambda maximum: secrets.randbelow(maximum+1)))(cap)
    finished = now if completed_at is None else completed_at()
    updated = queue.finish(job, status, finished, delay, retry_ms)
    return {'delivery_id':job['id'], 'attempt':job['attempts'], 'status':status,
            'queue_update_accepted':updated, 'retry_after_ms':retry_ms}
