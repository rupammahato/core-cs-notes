from decimal import Decimal
from threading import Lock

# Hypothetical USD per million tokens; these are not any provider's prices.
RATES = {'input': Decimal('2'), 'cached_input': Decimal('0.5'), 'output': Decimal('8')}


def estimated_cost(input_tokens, cached_tokens, output_tokens, rates=RATES):
    if any(type(value) is not int or value < 0 for value in (input_tokens, cached_tokens, output_tokens)):
        raise ValueError('Nonnegative integer usage required')
    if cached_tokens > input_tokens:
        raise ValueError('Cached input is a subset of input')
    return ((input_tokens - cached_tokens) * rates['input'] + cached_tokens * rates['cached_input']
            + output_tokens * rates['output']) / Decimal(1000000)


class BudgetLedger:
    """In-process admission example; production reconciliation requires durable storage."""
    def __init__(self, available):
        self.available = Decimal(available)
        self.reservations = {}
        self.settled = {}
        self.lock = Lock()

    def reserve(self, request_id, amount):
        amount = Decimal(amount)
        with self.lock:
            if not amount.is_finite() or amount <= 0 or request_id in self.reservations or request_id in self.settled:
                raise ValueError('Invalid reservation')
            if amount > self.available:
                raise PermissionError('Budget exceeded')
            self.available -= amount
            self.reservations[request_id] = amount

    def settle(self, request_id, actual):
        actual = Decimal(actual)
        with self.lock:
            if not actual.is_finite() or actual < 0:
                raise ValueError('Invalid cost')
            if request_id in self.settled:
                if self.settled[request_id] != actual:
                    raise ValueError('Conflicting settlement')
                return
            reserved = self.reservations[request_id]
            # If actual exceeds the estimate, record the liability, even if balance becomes negative.
            self.available += reserved - actual
            del self.reservations[request_id]
            self.settled[request_id] = actual
