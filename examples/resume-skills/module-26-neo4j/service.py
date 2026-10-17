"""Fixed parameterized queries; principal comes from a trusted backend boundary."""
from dataclasses import dataclass
import re
from neo4j import Query


@dataclass(frozen=True)
class Principal:
    tenant: str
    can_read: bool = True
    can_write: bool = False


def authorize(principal, write=False):
    if principal.tenant not in ('alpha', 'beta') or not principal.can_read or (write and not principal.can_write):
        raise PermissionError('Graph operation denied')


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9_-]{1,50}', value):
        raise ValueError('Invalid application identifier')
    return value


def prerequisites(driver, principal, concept_id, depth=2, limit=10):
    authorize(principal)
    identifier(concept_id)
    if isinstance(depth, bool) or not isinstance(depth, int) or depth not in (1, 2, 3):
        raise ValueError('Depth outside application limit')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('Result limit outside application limit')
    # Only the allowlisted integer controls query structure; all data are parameters.
    query = Query(f'''CYPHER 5
        MATCH p=(root:Concept {{tenant:$tenant,id:$id}})-[:REQUIRES*1..{depth}]->(candidate:Concept)
        WHERE candidate <> root
          AND all(n IN nodes(p) WHERE n.tenant=$tenant)
          AND all(r IN relationships(p) WHERE r.tenant=$tenant)
        RETURN candidate.id AS id, candidate.title AS title, min(length(p)) AS hops
        ORDER BY hops,id LIMIT $limit''', timeout=2)
    with driver.session(database='neo4j') as session:
        return session.run(query, tenant=principal.tenant, id=concept_id, limit=limit).data()


def evidence(driver, principal, concept_id):
    authorize(principal)
    identifier(concept_id)
    query = Query('''CYPHER 5
        MATCH (d:Document {tenant:$tenant})-[r:EXPLAINS]->(c:Concept {tenant:$tenant,id:$id})
        WHERE r.tenant=$tenant AND NOT d.deleted AND d.revision=r.source_revision
        RETURN d.id AS document, d.revision AS revision, d.text AS text
        ORDER BY document LIMIT 10''', timeout=2)
    with driver.session(database='neo4j') as session:
        return session.run(query, tenant=principal.tenant, id=concept_id).data()


def upsert_concept(driver, principal, concept_id, title):
    authorize(principal, write=True)
    identifier(concept_id)
    if not isinstance(title, str) or not 1 <= len(title) <= 100:
        raise ValueError('Bad title')
    def write(tx):
        result = tx.run('''CYPHER 5 MERGE (c:Concept {tenant:$tenant,id:$id})
            ON CREATE SET c.created_by='fixture'
            SET c.title=$title RETURN c.id AS id,c.title AS title''',
            tenant=principal.tenant, id=concept_id, title=title)
        return result.single().data()
    with driver.session(database='neo4j') as session:
        return session.execute_write(write)
