PRAGMA foreign_keys=ON;
CREATE TABLE raw_changes(
 ingest_seq INTEGER PRIMARY KEY AUTOINCREMENT,
 delivery_id TEXT UNIQUE NOT NULL,
 stream TEXT NOT NULL CHECK(stream IN ('orders','customers')),
 tenant_id TEXT NOT NULL,
 entity_id TEXT NOT NULL,
 source_version INTEGER NOT NULL CHECK(source_version>0),
 payload_json TEXT NOT NULL CHECK(json_valid(payload_json))
);
CREATE TABLE dim_customer(
 tenant_id TEXT NOT NULL, customer_sk TEXT NOT NULL, customer_id TEXT NOT NULL,
 valid_from TEXT NOT NULL, valid_to TEXT, plan TEXT NOT NULL, is_unknown INTEGER NOT NULL,
 PRIMARY KEY(tenant_id,customer_sk), UNIQUE(tenant_id,customer_id,valid_from),
 CHECK(valid_to IS NULL OR valid_to>valid_from)
);
CREATE TABLE fact_orders(
 tenant_id TEXT NOT NULL,order_id TEXT NOT NULL,customer_id TEXT NOT NULL,
 customer_sk TEXT NOT NULL,order_day TEXT NOT NULL,billed_cents INTEGER,
 status TEXT NOT NULL CHECK(status IN ('paid','cancelled')),source_version INTEGER NOT NULL,
 PRIMARY KEY(tenant_id,order_id),
 FOREIGN KEY(tenant_id,customer_sk) REFERENCES dim_customer(tenant_id,customer_sk),
 CHECK(billed_cents IS NULL OR billed_cents>=0)
);
CREATE TABLE runs(
 run_id TEXT PRIMARY KEY, lower_seq INTEGER NOT NULL, upper_seq INTEGER NOT NULL,
 mode TEXT NOT NULL, metric_version TEXT NOT NULL
);
CREATE TABLE mart_daily(
 run_id TEXT NOT NULL REFERENCES runs,tenant_id TEXT NOT NULL,order_day TEXT NOT NULL,
 plan TEXT NOT NULL,paid_orders INTEGER NOT NULL,known_bill_cents INTEGER NOT NULL,
 missing_bills INTEGER NOT NULL,complete_bill_cents INTEGER,
 PRIMARY KEY(run_id,tenant_id,order_day,plan)
);
CREATE TABLE pipeline_state(
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),committed_seq INTEGER NOT NULL,
 active_run TEXT REFERENCES runs
);
INSERT INTO pipeline_state VALUES(1,0,NULL);
CREATE TABLE order_lines(
 tenant_id TEXT NOT NULL,order_id TEXT NOT NULL,line_id TEXT NOT NULL,line_cents INTEGER NOT NULL,
 PRIMARY KEY(tenant_id,line_id)
);
