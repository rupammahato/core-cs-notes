CREATE SCHEMA lesson;
CREATE TABLE lesson.tenants (id integer PRIMARY KEY, name text NOT NULL);
CREATE TABLE lesson.products (
    tenant_id integer NOT NULL REFERENCES lesson.tenants(id),
    sku text NOT NULL,
    available integer NOT NULL CHECK (available >= 0),
    unit_price_minor bigint NOT NULL CHECK (unit_price_minor >= 0),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    PRIMARY KEY (tenant_id, sku)
);
CREATE TABLE lesson.reservations (
    id uuid PRIMARY KEY,
    tenant_id integer NOT NULL,
    request_key text NOT NULL,
    sku text NOT NULL,
    quantity integer NOT NULL CHECK (quantity BETWEEN 1 AND 10),
    status text NOT NULL CHECK (status IN ('pending','reserved')),
    total_minor bigint,
    currency text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT reservation_request_unique UNIQUE (tenant_id, request_key),
    CONSTRAINT reservation_product_fk FOREIGN KEY (tenant_id, sku) REFERENCES lesson.products(tenant_id, sku),
    CHECK ((status='pending' AND total_minor IS NULL AND currency IS NULL) OR
           (status='reserved' AND total_minor IS NOT NULL AND total_minor>=0 AND currency IS NOT NULL))
);
CREATE TABLE lesson.outbox (
    reservation_id uuid PRIMARY KEY REFERENCES lesson.reservations(id),
    payload jsonb NOT NULL,
    delivered_at timestamptz
);
CREATE TABLE lesson.accounts (id integer PRIMARY KEY, balance integer NOT NULL);
CREATE TABLE lesson.doctors (id integer PRIMARY KEY, on_call boolean NOT NULL);
CREATE TABLE lesson.jobs (id integer PRIMARY KEY, status text NOT NULL);
CREATE TABLE lesson.values_demo (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label text UNIQUE,
    amount numeric(12,2),
    happened_at timestamptz,
    metadata jsonb
);
CREATE TABLE lesson.sequence_demo (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, note text);
INSERT INTO lesson.tenants VALUES (1,'alpha'),(2,'beta');
INSERT INTO lesson.products VALUES (1,'basic',10,12500,'INR'),(2,'beta-only',10,25000,'INR');
INSERT INTO lesson.accounts VALUES (1,100),(2,100);
INSERT INTO lesson.doctors VALUES (1,true),(2,true);
INSERT INTO lesson.jobs VALUES (1,'ready'),(2,'ready');
GRANT USAGE ON SCHEMA lesson TO m13_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA lesson TO m13_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA lesson TO m13_app;
