"""Trusted backend supplies tenant; transaction-local scope prevents pool leakage."""
from vectors import SPACE, literal


def scoped(conn, tenant):
    if tenant not in ('alpha', 'beta'):
        raise PermissionError('Unknown authenticated tenant')
    conn.execute("SELECT set_config('app.tenant', %s, true)", (tenant,))


def publish(conn, tenant, document, revision, chunks, space_key=SPACE.key):
    prepared = [(content, SPACE.validate(vector, space_key)) for content, vector in chunks]
    with conn.transaction():
        scoped(conn, tenant)
        row = conn.execute('SELECT revision, deleted FROM documents WHERE tenant_id=%s AND document_id=%s FOR UPDATE',
                           (tenant, document)).fetchone()
        if row is None or row[1] or row[0] != revision:
            return False
        conn.execute('DELETE FROM chunks WHERE tenant_id=%s AND document_id=%s', (tenant, document))
        for ordinal, (content, vector) in enumerate(prepared):
            conn.execute('INSERT INTO chunks VALUES (%s,%s,%s,%s,%s,%s,%s::vector)',
                         (tenant, document, ordinal, revision, space_key, content, literal(vector)))
    return True


def search(conn, tenant, vector, top_k=5, min_similarity=-1, space_key=SPACE.key):
    values = SPACE.validate(vector, space_key)
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        raise ValueError('top_k outside application limit')
    if not -1 <= min_similarity <= 1:
        raise ValueError('Bad cosine threshold')
    query = literal(values)
    with conn.transaction():
        scoped(conn, tenant)
        # Exact search in this small teaching table: no ANN index is created here.
        rows = conn.execute('''
            SELECT c.document_id, c.ordinal, c.content, 1 - (c.embedding <=> %s::vector) AS similarity
            FROM chunks c JOIN documents d USING (tenant_id, document_id)
            WHERE c.tenant_id=%s AND c.space_key=%s AND NOT d.deleted AND c.revision=d.revision
              AND c.embedding <=> %s::vector <= %s
            ORDER BY c.embedding <=> %s::vector, c.document_id, c.ordinal LIMIT %s
        ''', (query, tenant, space_key, query, 1 - min_similarity, query, top_k)).fetchall()
    return [{'document': r[0], 'ordinal': r[1], 'content': r[2], 'similarity': round(r[3], 6)} for r in rows]


def delete_document(conn, tenant, document):
    with conn.transaction():
        scoped(conn, tenant)
        conn.execute('UPDATE documents SET deleted=true, revision=revision+1 WHERE tenant_id=%s AND document_id=%s',
                     (tenant, document))
        conn.execute('DELETE FROM chunks WHERE tenant_id=%s AND document_id=%s', (tenant, document))
