CREATE EXTENSION vector;

CREATE TABLE documents (
    tenant_id text NOT NULL,
    document_id text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    deleted boolean NOT NULL DEFAULT false,
    PRIMARY KEY (tenant_id, document_id)
);

CREATE TABLE chunks (
    tenant_id text NOT NULL,
    document_id text NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    revision integer NOT NULL,
    space_key text NOT NULL,
    content text NOT NULL,
    embedding vector(3) NOT NULL,
    PRIMARY KEY (tenant_id, document_id, ordinal),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES documents (tenant_id, document_id) ON DELETE CASCADE,
    CHECK (vector_norm(embedding) > 0)
);

CREATE INDEX chunks_tenant_document ON chunks (tenant_id, document_id);
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY document_scope ON documents
    USING (tenant_id = current_setting('app.tenant', true))
    WITH CHECK (tenant_id = current_setting('app.tenant', true));
CREATE POLICY chunk_scope ON chunks
    USING (tenant_id = current_setting('app.tenant', true))
    WITH CHECK (tenant_id = current_setting('app.tenant', true));
GRANT SELECT, INSERT, UPDATE, DELETE ON documents, chunks TO m24_app;
