"""Small, explicit vector-space contract; numbers here are authored fixtures."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Space:
    model: str
    revision: str
    dimensions: int
    preprocessing: str
    metric: str = 'cosine'

    @property
    def key(self):
        return f'{self.model}:{self.revision}:{self.dimensions}:{self.preprocessing}:{self.metric}'

    def validate(self, values, space_key):
        if space_key != self.key:
            raise ValueError('Incompatible embedding space')
        if len(values) != self.dimensions:
            raise ValueError('Wrong dimensions')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError('Expected finite numbers')
        if self.metric == 'cosine' and not any(values):
            raise ValueError('Cosine requires a nonzero vector')
        return [float(v) for v in values]


SPACE = Space('authored-fixture', 'v1', 3, 'identity')


def dot(a, b):
    if len(a) != len(b):
        raise ValueError('Wrong dimensions')
    return sum(x * y for x, y in zip(a, b))


def normalize(a):
    norm = math.sqrt(dot(a, a))
    if norm == 0:
        raise ValueError('Zero norm')
    return [x / norm for x in a]


def cosine(a, b):
    return dot(normalize(a), normalize(b))


def l2(a, b):
    if len(a) != len(b):
        raise ValueError('Wrong dimensions')
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def literal(values):
    return '[' + ','.join(str(float(v)) for v in values) + ']'


def recall_at_k(expected, actual):
    if not expected:
        raise ValueError('Ground truth must be nonempty')
    return len(set(expected) & set(actual)) / len(set(expected))
