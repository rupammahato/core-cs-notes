"""Request-body construction only: no Pinecone SDK, HTTP service or inference."""
import re
from vectors import SPACE


def namespace_for(authenticated_tenant):
    # Demonstration registry; caller is a trusted authentication layer.
    registry = {'alpha': 'tenant-alpha-space-v1', 'beta': 'tenant-beta-space-v1'}
    if authenticated_tenant not in registry:
        raise PermissionError('No tenant namespace')
    return registry[authenticated_tenant]


def record_id(document, revision, ordinal):
    if not re.fullmatch(r'[a-z0-9_-]{1,40}', document):
        raise ValueError('Bad document identifier')
    if revision < 1 or ordinal < 0:
        raise ValueError('Bad revision/ordinal')
    return f'{document}:r{revision}:c{ordinal}'


def upsert_body(tenant, document, revision, ordinal, vector, space_key=SPACE.key):
    values = SPACE.validate(vector, space_key)
    return {'namespace': namespace_for(tenant), 'vectors': [{
        'id': record_id(document, revision, ordinal), 'values': values,
        'metadata': {'document_id': document, 'revision': revision, 'space_key': space_key, 'status': 'ready'},
    }]}


def query_body(tenant, vector, top_k=10, space_key=SPACE.key):
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        raise ValueError('top_k outside application limit')
    return {'namespace': namespace_for(tenant), 'vector': SPACE.validate(vector, space_key),
            'topK': top_k, 'includeMetadata': True, 'includeValues': False,
            'filter': {'$and': [{'status': {'$eq': 'ready'}}, {'space_key': {'$eq': space_key}}]}}


def delete_body(tenant, document, revision, ordinals):
    if not ordinals:
        raise ValueError('Explicit record IDs required')
    return {'namespace': namespace_for(tenant),
            'ids': [record_id(document, revision, ordinal) for ordinal in ordinals]}
