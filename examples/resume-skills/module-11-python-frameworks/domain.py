"""Shared domain and schemas; opaque bearer values are public test fixtures."""
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from pydantic import BaseModel, ConfigDict, Field

class QuoteIn(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=100)

class ProductOut(BaseModel):
    product_id: str
    amount_paise: int
    currency: str

class QuoteOut(BaseModel):
    product_id: str
    quantity: int
    total_paise: int
    currency: str
    created_at: datetime

@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str

TOKENS = {'alpha-demo-token': Principal('u-alpha', 'alpha'),
          'beta-demo-token': Principal('u-beta', 'beta')}

class Unauthenticated(Exception):
    pass

class ProductNotFound(Exception):
    pass

def authenticate(header):
    parts = (header or '').split()
    if len(parts) != 2 or parts[0].lower() != 'bearer' or parts[1] not in TOKENS:
        raise Unauthenticated()
    return TOKENS[parts[1]]

class Audit:
    def __init__(self):
        self.rows = []
        self.lock = Lock()
    def add(self, request_id, event):
        with self.lock:
            self.rows.append((request_id, event))
    def trace(self, request_id):
        with self.lock:
            return [event for rid, event in self.rows if rid == request_id]

class Catalog:
    def __init__(self):
        self.rows = {('alpha', 'basic'): {'product_id': 'basic', 'amount_paise': 12500,
                     'currency': 'INR', 'internal_cost_paise': 7000},
                     ('beta', 'team'): {'product_id': 'team', 'amount_paise': 25000,
                     'currency': 'INR', 'internal_cost_paise': 14000}}
        self.closed = False
    def product(self, principal, product_id):
        if self.closed:
            raise RuntimeError('catalog closed')
        value = self.rows.get((principal.tenant_id, product_id))
        if value is None:
            raise ProductNotFound()
        return dict(value)
    def products(self, principal, limit):
        return [dict(value) for (tenant, key), value in sorted(self.rows.items())
                if tenant == principal.tenant_id][:limit]
    def close(self):
        self.closed = True

class Lease:
    """Instrumented request resource, not a database session."""
    def __init__(self, audit, request_id):
        self.audit, self.request_id, self.closed = audit, request_id, False
        audit.add(request_id, 'lease-open')
    def close(self):
        if self.closed:
            raise RuntimeError('lease closed twice')
        self.closed = True
        self.audit.add(self.request_id, 'lease-close')

def build_quote(catalog, principal, body, now):
    price = catalog.product(principal, body.product_id)
    return {'product_id': body.product_id, 'quantity': body.quantity,
            'total_paise': price['amount_paise'] * body.quantity,
            'currency': price['currency'], 'created_at': now.astimezone(timezone.utc),
            'internal_cost_paise': price['internal_cost_paise'],
            'tenant_id': principal.tenant_id}

FIXED_NOW = datetime(2026, 10, 14, 6, 30, tzinfo=timezone.utc)
