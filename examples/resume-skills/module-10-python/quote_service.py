"""Pure application boundary; no framework, persistence or authentication."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json

class InvalidRequest(ValueError):
    pass

class ProductNotFound(LookupError):
    pass

@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str

@dataclass(frozen=True)
class QuoteInput:
    product_id: str
    quantity: int

@dataclass(frozen=True)
class Price:
    amount_paise: int
    currency: str
    internal_cost_paise: int

@dataclass(frozen=True)
class Quote:
    tenant_id: str
    product_id: str
    quantity: int
    total_paise: int
    currency: str
    created_at: datetime

# Trusted local fixtures, scoped by tenant. No client-provided price.
CATALOG = {
    ('alpha', 'basic'): Price(12500, 'INR', 7000),
    ('beta', 'team'): Price(25000, 'INR', 14000),
}

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRequest('duplicate JSON key')
        result[key] = value
    return result

def reject_constant(value):
    raise InvalidRequest('non-finite JSON number')

def parse_body(raw: bytes) -> QuoteInput:
    if len(raw) > 4096:
        raise InvalidRequest('body too large')
    try:
        body = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidRequest('invalid UTF-8 JSON') from exc
    if type(body) is not dict or set(body) != {'product_id', 'quantity'}:
        raise InvalidRequest('expected product_id and quantity only')
    product_id, quantity = body['product_id'], body['quantity']
    if type(product_id) is not str or not 1 <= len(product_id) <= 80:
        raise InvalidRequest('invalid product_id')
    if type(quantity) is not int or not 1 <= quantity <= 100:
        raise InvalidRequest('quantity must be an integer from 1 to 100')
    return QuoteInput(product_id, quantity)

def make_quote(principal: Principal, request: QuoteInput, *, now: datetime) -> Quote:
    # principal comes from trusted authentication middleware in a later module.
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('clock must supply an aware timestamp')
    price = CATALOG.get((principal.tenant_id, request.product_id))
    if price is None:
        raise ProductNotFound('product not found')
    return Quote(principal.tenant_id, request.product_id, request.quantity,
                 price.amount_paise * request.quantity, price.currency,
                 now.astimezone(timezone.utc))

def public_response(quote: Quote) -> bytes:
    # Explicit allowlist; dataclasses.asdict is not an API disclosure policy.
    body = {'product_id': quote.product_id, 'quantity': quote.quantity,
            'total_paise': quote.total_paise, 'currency': quote.currency,
            'created_at': quote.created_at.isoformat()}
    return json.dumps(body, sort_keys=True, allow_nan=False).encode('utf-8')
