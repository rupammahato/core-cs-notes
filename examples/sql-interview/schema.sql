PRAGMA foreign_keys=ON;
CREATE TABLE customers(
 customer_id TEXT PRIMARY KEY NOT NULL,
 tenant_id TEXT NOT NULL,
 signup_ts INTEGER NOT NULL CHECK(typeof(signup_ts)='integer')
);
CREATE TABLE carts(
 cart_id TEXT PRIMARY KEY NOT NULL,
 customer_id TEXT NOT NULL REFERENCES customers,
 created_ts INTEGER NOT NULL
);
CREATE TABLE orders(
 order_id TEXT PRIMARY KEY NOT NULL,
 customer_id TEXT NOT NULL REFERENCES customers,
 ordered_ts INTEGER NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('paid','cancelled')),
 billed_cents INTEGER CHECK(billed_cents>=0),
 cart_id TEXT REFERENCES carts
);
CREATE TABLE items(
 item_id TEXT PRIMARY KEY NOT NULL,
 order_id TEXT NOT NULL REFERENCES orders,
 category TEXT NOT NULL,
 line_cents INTEGER NOT NULL CHECK(line_cents>=0)
);
CREATE TABLE payments(
 payment_id TEXT PRIMARY KEY NOT NULL,
 order_id TEXT NOT NULL REFERENCES orders,
 amount_cents INTEGER NOT NULL CHECK(amount_cents>=0),
 status TEXT NOT NULL CHECK(status IN ('succeeded','pending','failed'))
);
CREATE TABLE refunds(
 refund_id TEXT PRIMARY KEY NOT NULL,
 order_id TEXT NOT NULL REFERENCES orders,
 amount_cents INTEGER NOT NULL CHECK(amount_cents>=0)
);
CREATE TABLE plan_history(
 customer_id TEXT NOT NULL REFERENCES customers,
 effective_ts INTEGER NOT NULL,
 plan TEXT NOT NULL,
 PRIMARY KEY(customer_id,effective_ts)
);
CREATE TABLE exclusions(customer_id TEXT);
CREATE TABLE raw_events(
 delivery_id TEXT PRIMARY KEY NOT NULL,
 event_id TEXT NOT NULL,
 tenant_id TEXT NOT NULL,
 customer_id TEXT NOT NULL,
 event_ts INTEGER NOT NULL,
 ingested_ts INTEGER NOT NULL,
 event_name TEXT NOT NULL
);
-- Conflicting identities are quarantined, not arbitrarily overwritten.
CREATE VIEW canonical_events AS
WITH payloads AS (
 SELECT DISTINCT tenant_id,event_id,customer_id,event_ts,event_name FROM raw_events
), valid_ids AS (
 SELECT tenant_id,event_id FROM payloads
 GROUP BY tenant_id,event_id HAVING COUNT(*)=1
), ranked AS (
 SELECT r.*,ROW_NUMBER() OVER (
  PARTITION BY r.tenant_id,r.event_id ORDER BY ingested_ts,delivery_id
 ) AS delivery_rank
 FROM raw_events r JOIN valid_ids v USING(tenant_id,event_id)
 JOIN customers c ON c.customer_id=r.customer_id AND c.tenant_id=r.tenant_id
)
SELECT delivery_id,event_id,tenant_id,customer_id,event_ts,ingested_ts,event_name
FROM ranked WHERE delivery_rank=1;
