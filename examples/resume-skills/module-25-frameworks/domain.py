"""Small application contracts shared by the actual framework examples."""
from dataclasses import dataclass
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class Principal:
    tenant: str
    user: str
    can_read: bool = True


NOTES = [
    {'id': 'alpha-session', 'tenant': 'alpha', 'revision': 1,
     'text': 'Session records keep login state on the server. A cookie carries a session identifier.'},
    {'id': 'alpha-index', 'tenant': 'alpha', 'revision': 1,
     'text': 'An index helps locate rows. Index maintenance adds work to writes.'},
    {'id': 'beta-session', 'tenant': 'beta', 'revision': 1,
     'text': 'Session records for beta contain private deployment procedures.'},
]


def retrieve(principal, topic, limit=2):
    if not principal.can_read or principal.tenant not in ('alpha', 'beta'):
        raise PermissionError('Read permission denied')
    if not isinstance(topic, str) or not topic.strip() or len(topic) > 100:
        raise ValueError('Bad topic')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 3:
        raise ValueError('Bad result limit')
    terms = set(topic.lower().split())
    return [dict(note) for note in NOTES if note['tenant'] == principal.tenant
            and terms.intersection(note['text'].lower().split())][:limit]


class Answer(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    answer: str = Field(min_length=1)
    citations: list[str] = Field(min_length=1)


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    approved: bool
    draft_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


def draft_hash(job_id, draft, evidence):
    payload = {'job': job_id, 'draft': draft,
               'sources': [(row['id'], row['revision']) for row in evidence]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def accept_citations(answer, evidence):
    allowed = {note['id'] for note in evidence}
    if not set(answer.citations).issubset(allowed):
        raise ValueError('Citation outside supplied evidence')
    return answer
