import json
from datetime import datetime, timezone, timedelta
from quote_service import (InvalidRequest, ProductNotFound, Principal, parse_body,
                           make_quote, public_response)

results = []
NOW = datetime(2026, 10, 14, 6, 30, tzinfo=timezone.utc)
PRINCIPAL = Principal('user-1', 'alpha')
VALID = b'{"product_id":"basic","quantity":2}'

def check(name, fn):
    fn()
    results.append({'name': name, 'passed': True})

def equal(actual, expected):
    if actual != expected:
        raise AssertionError((actual, expected))

def rejected(raw, expected=InvalidRequest):
    try:
        parse_body(raw)
    except expected:
        return
    raise AssertionError('request was accepted')

def quote():
    return make_quote(PRINCIPAL, parse_body(VALID), now=NOW)

def projection():
    offset_now = datetime(2026, 10, 14, 12, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    value = json.loads(public_response(make_quote(PRINCIPAL, parse_body(VALID), now=offset_now)))
    equal(value, {'product_id': 'basic', 'quantity': 2, 'total_paise': 25000,
                  'currency': 'INR', 'created_at': '2026-10-14T06:30:00+00:00'})
    equal(set(value) & {'tenant_id', 'internal_cost_paise', 'user_id'}, set())

def invalid_numbers():
    for value in ('0', '-1', '2.0', 'null', 'NaN', 'Infinity'):
        rejected(('{"product_id":"basic","quantity":' + value + '}').encode())

def missing_or_shape():
    for raw in (b'{}', b'[]', b'null', b'{"quantity":2}',
                b'{"product_id":"","quantity":2}', b'{"product_id":7,"quantity":2}'):
        rejected(raw)

def cross_tenant():
    body = parse_body(b'{"product_id":"team","quantity":1}')
    try:
        make_quote(PRINCIPAL, body, now=NOW)
    except ProductNotFound:
        pass
    else:
        raise AssertionError('cross-tenant product was visible')
    equal(make_quote(Principal('user-2', 'beta'), body, now=NOW).total_paise, 25000)

def malformed():
    for raw in (b'{', b'{"product_id":"basic","quantity":2} trailing'):
        rejected(raw)
    try:
        parse_body(b'{')
    except InvalidRequest as exc:
        equal(type(exc.__cause__).__name__, 'JSONDecodeError')

def naive_clock():
    try:
        make_quote(PRINCIPAL, parse_body(VALID), now=datetime(2026, 10, 14))
    except ValueError:
        return
    raise AssertionError('naive timestamp accepted')

def valid_total():
    equal(quote().total_paise, 25000)
    for quantity in (1, 100):
        body = parse_body(json.dumps({'product_id': 'basic', 'quantity': quantity}).encode())
        equal(make_quote(PRINCIPAL, body, now=NOW).total_paise, 12500 * quantity)

check('trusted price and validated quantity determine total', valid_total)
check('public projection excludes internal fields and normalizes UTC', projection)
check('string quantity rejected', lambda: rejected(b'{"product_id":"basic","quantity":"2"}'))
check('boolean quantity rejected despite bool subclassing int', lambda: rejected(b'{"product_id":"basic","quantity":true}'))
check('zero negative float null and non-finite quantities rejected', invalid_numbers)
check('quantity cap enforced', lambda: rejected(b'{"product_id":"basic","quantity":101}'))
check('missing fields invalid identifier and non-object bodies rejected', missing_or_shape)
check('client price and tenant injection rejected', lambda: rejected(b'{"product_id":"basic","quantity":2,"total_paise":1,"tenant_id":"beta"}'))
check('tenant catalog boundary enforced', cross_tenant)
check('malformed JSON rejected with cause preserved', malformed)
check('duplicate JSON keys rejected', lambda: rejected(b'{"product_id":"basic","quantity":1,"quantity":2}'))
check('invalid UTF-8 rejected', lambda: rejected(bytes([255])))
check('body byte limit enforced before parsing', lambda: rejected(b' ' * 4097))
check('naive internal clock rejected', naive_clock)
print(json.dumps({'checks': results, 'public_response': json.loads(public_response(quote()))}, sort_keys=True))
