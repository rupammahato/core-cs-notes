# Resume Skills Placement Handbook — Part 15
# Module 13: PostgreSQL in a Backend

**Module 13 · 5–6 hours · Tier 1 · Requires: M6–M8, M10; DBMS SQL, keys, indexes and transactions**

---

## Why this module matters

PostgreSQL is where independent backend processes meet shared state. An application can have correct Python syntax, clean controllers and valid JSON while still overselling inventory, leaking another tenant's rows or exhausting its database connections. Understanding the database boundary lets you explain how a backend preserves rules when requests overlap and failures interrupt work.

Interview follow-ups move beyond “PostgreSQL is a relational database”: What does a transaction actually protect? Why did an update wait? Can two requests both buy the last item? Does a pool clear session settings? Why did the planner ignore an index?

> **Put durable rules in constraints, express state transitions in SQL, own the transaction boundary and measure the queries the application actually sends.**

This chapter connects the existing [DBMS handbook](/docs/dbms) to application code. The worked system is a tenant-scoped inventory reservation with idempotency and a transactional outbox. Separate database sessions reproduce snapshots, contention, write skew and a deadlock; they are actual PostgreSQL operations rather than a simulated scheduler.

**Verification: 60 checks passed — 19 core, 14 concurrency, eight pool, seven query-plan and 12 reservation-service checks.** These are named checks, some containing several assertions. No HTTP server or payment provider is involved in this module.

### Recorded environment

| Component | Executed version / setting |
| --- | --- |
| PostgreSQL server | 18.4, 64-bit Windows |
| Python | CPython 3.12.10, 64-bit Windows |
| Psycopg / psycopg-binary | 3.3.4 / 3.3.4 |
| psycopg-pool | 3.3.1 |
| Client libpq | 18.3; reported as 180003, independently of server version |
| typing_extensions / tzdata | 4.16.0 / 2026.4 |
| Fixture isolation | Read Committed by default; explicit alternatives in concurrency checks |
| Host authentication / TLS | SCRAM-SHA-256 on loopback; TLS disabled for this local fixture |
| Durability settings observed | fsync=on, synchronous_commit=on; no power-loss/crash test |

Research uses PostgreSQL 18 documentation. The Psycopg documentation is maintained independently of the installed package; the recorded run used the exact pins above. Examples here use synchronous Psycopg, not an async driver or an ORM. The same database rules still matter behind Express, FastAPI or Django.

### Run the examples

From the repository root, with the prepared environment and installed PostgreSQL 18 binaries:

```powershell
./examples/resume-skills/module-13-postgresql/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-13-postgresql/verify.py
```

To recreate the dependency environment, select Python 3.12 first. With python referring to it:

```powershell
python -m venv examples/resume-skills/module-13-postgresql/.venv
./examples/resume-skills/module-13-postgresql/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-13-postgresql/requirements.lock.txt
./examples/resume-skills/module-13-postgresql/.venv/Scripts/python.exe -m pip check
```

The default binary directory is `C:/Program Files/PostgreSQL/18/bin`. Set `M13_PG_BIN` to another directory containing initdb, postgres and pg_ctl if needed. The lock records package versions, without hashes; installation normally needs package access. This run installed from cached wheels with --no-index. The venv and wheelhouse are ignored; global Python packages were not changed.

The aggregate verifier initializes its own temporary cluster, starts postgres on an ephemeral 127.0.0.1 port and verifies the connected server's data_directory. Each group gets a fresh database. Public fixture passwords authenticate only this owned cluster. The application role has no superuser, database-creation or role-creation privileges; a separate fixture owner performs setup.

After child processes and pools finish, the verifier stops that owned cluster and removes its validated temporary directory. It never connects to the machine's existing PostgreSQL service. **The recorded run confirms listener_stopped=true and temporary_cluster_removed=true. Port 3000 remains stopped.** Individual group files expect the runner's explicit M13 connection environment; use verify.py for a clean aggregate run.

---

## 13.1 What is PostgreSQL, and where does it sit?

**PostgreSQL is a database server that stores and queries data, enforces relational constraints and coordinates concurrent transactions.** SQL is the language used to describe many of those operations. Psycopg is a Python client driver. An ORM is an application abstraction that produces database operations; none of these terms are interchangeable.

```text
client -> HTTP server -> route/authentication/authorization
       -> application service -> pool lease -> driver
       -> PostgreSQL session -> SQL planning/execution
       -> tables/indexes/transaction machinery -> result rows
       -> application response
```

The HTTP server decides what endpoint runs. The service decides whether a reservation is permitted. PostgreSQL makes the relevant writes and constraints hold against other database sessions. Moving validation into a controller cannot by itself coordinate two different application replicas.

### Cluster, database, schema and role

| Term | Meaning for this example |
| --- | --- |
| Cluster | One initialized PostgreSQL installation's data directory and server instance; contains databases |
| Database | Connection target; each verifier group gets a separate database |
| Schema | Namespace within a database; tables are named lesson.products, lesson.reservations, etc. |
| Role | Database identity/privileges; m13_app performs application queries |
| Connection/session | One client conversation with the server; carries transaction and session state |
| Table / index | Stored rows / an access structure supporting certain operations |

A schema is not automatically a tenant boundary. Two tables can be in different schemas while the same role has access to both. Here all tenants share tables, and tenant_id participates in keys and predicates. The application role can deliberately perform an unscoped SELECT: the verifier observes two products rather than the one returned by a tenant predicate. Grants control allowed operations, not which tenant a request belongs to.

Fixed schema-qualified identifiers make the intended object explicit. Unqualified names use search_path; allowing an untrusted actor to create objects in a searched schema can affect object resolution. Do not turn request input directly into a schema or search_path. References: [client/server concepts](https://www.postgresql.org/docs/18/tutorial-arch.html), [schemas and search path](https://www.postgresql.org/docs/18/ddl-schemas.html).

### Why choose PostgreSQL for a backend?

A reservation, membership or billing application often needs related entities, joins, constraints, atomic changes and concurrent updates. PostgreSQL makes those requirements available in one engine, while also supporting JSON data where appropriate. The decision should follow the access patterns and invariants, the operating constraints and the team's experience.

A database product does not supply your authorization policy, HTTP error contract or external-service reliability. Nor is a relational database limited to a single application process: independent clients share the database's transaction machinery. M14 will compare document modeling; avoid claiming either model is always faster or always scales better.

---

## 13.2 Connections, credentials and transaction ownership

Connecting selects a host, port, database and role, authenticates, then creates a session used for commands and results. Reconnecting for every tiny query adds setup work. Keeping unlimited sessions creates another problem: each application worker can multiply the total connection demand. A pool reuses a bounded number of sessions.

### Complete fixture connection module: db.py

This is the exact verified source. prepare() belongs to setup; application calls use the less privileged role.

```python
from pathlib import Path
import os
import psycopg
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
from cluster import OWNER, OWNER_PASSWORD, APP_PASSWORD

BASE=Path(__file__).resolve().parent

def connection_info(*,admin=False,name='m13-app'):
    if os.environ['M13_HOST']!='127.0.0.1': raise RuntimeError('Loopback fixture only')
    return make_conninfo(host=os.environ['M13_HOST'],port=os.environ['M13_PORT'],
                         dbname=os.environ['M13_DATABASE'],user=OWNER if admin else 'm13_app',
                         password=OWNER_PASSWORD if admin else APP_PASSWORD,
                         sslmode='disable',connect_timeout=5,application_name=name)

def connect(*,admin=False,autocommit=True,name='m13-app'):
    return psycopg.connect(connection_info(admin=admin,name=name),autocommit=autocommit)

def prepare():
    with connect(admin=True,name='m13-setup') as conn:
        conn.execute((BASE/'schema.sql').read_text(encoding='utf-8'),prepare=False)

def make_pool(*,max_size=2,min_size=1,timeout=1,reset=None,name='m13-pool'):
    pool=ConnectionPool(connection_info(name=name),min_size=min_size,max_size=max_size,
                        timeout=timeout,max_waiting=4,kwargs={'autocommit':True},
                        reset=reset,open=False)
    pool.open()
    pool.wait(timeout=5)
    return pool
```

The loopback guard and explicit environment keys prevent this fixture from silently choosing an unrelated database. Production configuration needs its own secret source, least-privilege grants and verified transport. Disabling TLS here is a deliberate local setting, not a remote deployment default. With libpq, verify-full validates the certificate chain and host identity when configured with appropriate trust material. Reference: [libpq SSL modes](https://www.postgresql.org/docs/18/libpq-ssl.html).

### Autocommit does not mean “no transactions exist”

In autocommit mode, statements outside an explicit transaction commit individually. `with conn.transaction():` groups several statements into one atomic unit. The reservation service requires an idle autocommit connection so it can own the entire business transaction. It refuses to run inside somebody else's transaction rather than accidentally returning before the caller's eventual commit.

With Psycopg's default non-autocommit connection, even a SELECT normally begins an implicit transaction. Leaving that connection idle retains transaction state until commit/rollback. Catching a SQL error in Python does not automatically repair an aborted PostgreSQL transaction.

The core verifier records this sequence:

```text
non-autocommit SELECT -> INTRANS
constraint violation -> INERROR
another SELECT       -> 25P02 (failed transaction)
rollback             -> IDLE
next SELECT          -> succeeds
```

Use context managers deliberately. A nested transaction context can create a savepoint; rolling back that savepoint lets an outer transaction continue. The check deliberately triggers a uniqueness error inside a savepoint and completes outer work. This does not mean any arbitrary caught exception is safe to ignore.

Reference: [Psycopg transaction management](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

### A useful request boundary

1. Authenticate and derive trusted tenant context.
2. Validate request shape and inexpensive bounds.
3. Acquire a pool lease within a deadline.
4. Begin the smallest transaction that contains the invariant.
5. Execute SQL and inspect affected rows/results.
6. Commit or roll back, release the lease, then respond.

Avoid holding a transaction and row locks while waiting for a user, sending email or calling a payment provider. A response must not report committed success merely because an UPDATE completed inside an open transaction.

---

## 13.3 Parameterized SQL and real data types

Parameterization keeps **values** separate from SQL structure. With Psycopg, use %s placeholders and pass a sequence of values; do not quote the placeholder or interpolate with f-strings, Python %, concatenation or format(). The driver adapts Python values for PostgreSQL.

```python
# conn is an application connection supplied by the fixture.
row = conn.execute(
    'SELECT available FROM lesson.products WHERE tenant_id=%s AND sku=%s',
    (1, 'basic'),
).fetchone()
```

The core check binds hostile text containing SQL-like syntax, reads the same text back and confirms products still exist. The test proves that path treats the input as a value. It does not establish that every future dynamically composed query is safe.

A value placeholder cannot become a table or column name. `SELECT %s` with 'available' returns that text literal. When structure must vary, select from an application-owned allowlist and compose identifiers with psycopg.sql.Identifier. The verifier checks Identifier composition selects the actual available column. Identifier quoting makes syntax safe; the allowlist and authorization decide what a caller may select.

Reference: [Psycopg parameters and identifier composition](https://www.psycopg.org/psycopg3/docs/basic/params.html).

### Model values, not just strings

| Requirement | Useful representation | Boundary to explain |
| --- | --- | --- |
| Stock quantity | integer with a nonnegative constraint | Reject booleans/coerced strings at the request boundary |
| Fixed minor-unit price | bigint plus currency | Currency/rounding policy must define the unit; avoid binary float arithmetic |
| Decimal amount | numeric with explicit precision/scale + Python Decimal | Define overflow/rounding policy; serialize intentionally |
| Event instant | timestamptz + aware datetime | Display timezone can differ from storage semantics |
| Date only | date | Birthdays/calendar dates need not be instants |
| Flexible metadata | jsonb + Jsonb adapter | Retain relational keys/constraints for core invariants |
| Resource identifier | uuid | Unpredictability does not grant authorization |

Actual adapter round-trip: numeric amount **125.50**, aware timestamp **2026-10-14T06:30:00+00:00** and a JSON object. A separate jsonb containment query runs on PostgreSQL. Reservation amounts use integer minor units: 12500 × 2 = 25000 INR minor units. The input never supplies the price.

Timestamptz represents an instant and renders using the session timezone; it does not retain the original timezone name. A calendar appointment requiring “9am in Europe/London” needs that business timezone represented separately. The fixture fixes the session timezone to UTC for reproducible evidence. Reference: [PostgreSQL date/time types](https://www.postgresql.org/docs/18/datatype-datetime.html).

JSONB can support structured metadata queries, but a bag of JSON does not automatically enforce tenant ownership or replace all relational modeling. Keep fields used for joins, uniqueness, stock arithmetic and stable ordering explicit. An API's JSON response also needs an intentional Decimal/datetime encoding policy; this module tests database adapters rather than an HTTP serializer.

---

## 13.4 Schema design: express the durable rules

This is the complete executed schema.sql. The accounts, doctors, jobs and value tables support independent teaching checks; the reservation system uses tenants, products, reservations and outbox.

```sql
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
```

### Read the constraints as requirements

- A product is identified by **(tenant_id, sku)**. Two tenants may have the same SKU; one tenant cannot have duplicate SKU rows.
- Stock cannot become negative. This is a final database guard, not a replacement for an intentional conditional update.
- A reservation's product reference includes its tenant. A foreign key on sku alone would neither identify this composite key nor preserve that relationship.
- **(tenant_id, request_key)** is unique. Independent backend replicas cannot both commit new reservation rows for the same tenant/key.
- A reserved row needs a nonnegative total and a non-null currency. A pending row has neither.
- Each reservation can have one outbox row because reservation_id is its primary key.

The tenant-specific foreign key prevents a cross-tenant relationship; it does not stop a caller from choosing a different tenant_id. The service expects trusted tenant context supplied by authorization. Row-level security is not enabled in this fixture. The application role has broad table DML grants for these lessons, so it is not a substitute for per-request ownership enforcement.

### Validation and constraints solve different races

Application validation can produce friendly errors and reject malformed inputs before acquiring a connection. A preflight “does this key exist?” query can improve a response but cannot guarantee uniqueness: another transaction may insert between that read and the write. The unique constraint arbitrates at the shared database.

Verified failures include CHECK 23514, UNIQUE 23505, NOT NULL 23502 and foreign key 23503. Name constraints that application logic must distinguish. A known reservation_product_fk failure can become an unavailable-product outcome; an unrelated foreign-key failure should surface as a bug rather than being silently relabeled.

A CHECK expression accepts true or unknown, so a check such as available >= 0 needs NOT NULL when null is invalid. Ordinary UNIQUE permits multiple nulls by default, verified in values_demo. PostgreSQL also supports NULLS NOT DISTINCT when the requirement treats nulls as equal. Primary keys already include uniqueness and non-null requirements. Reference: [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html).

### Indexes and generated IDs are separate decisions

Primary/unique constraints create supporting unique indexes. A foreign key does **not** automatically create an index on its referencing columns. The fixture inspects reservation indexes and finds only the id primary-key index and the tenant/request-key unique index, without a referencing SKU index. Add a suitable referencing index when actual delete/update checks or application queries justify its maintenance cost.

Identity/sequence allocation is not gapless. The verifier allocates id 1 inside a rolled-back transaction; the next allocation is 2. An ID is not a count of committed rows or a legal invoice-number workflow. Use UUIDs or identities for their identifier properties, and model any regulated numbering requirement separately.

---

## 13.5 Build the reservation transition

The operation accepts a trusted tenant, an idempotency key, a SKU and an integer quantity from 1 to 10. It must either commit the stock change, completed reservation and outbox intent together, or commit none of them. A replay must return the original result without consuming stock again.

### Exact verified service: reservation.py

```python
from uuid import uuid4
from psycopg.errors import ForeignKeyViolation
from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

class InvalidRequest(ValueError): pass
class OutOfStock(Exception): pass
class IdempotencyConflict(Exception): pass

# Values are bound separately. Fixed schema-qualified identifiers are application-owned.
CLAIM = """
INSERT INTO lesson.reservations (id, tenant_id, request_key, sku, quantity, status)
VALUES (%s,%s,%s,%s,%s,'pending')
ON CONFLICT ON CONSTRAINT reservation_request_unique DO NOTHING
RETURNING id
"""
TAKE_STOCK = """
UPDATE lesson.products SET available=available-%s
WHERE tenant_id=%s AND sku=%s AND available >= %s
RETURNING unit_price_minor, currency
"""

def reserve(conn,*,tenant_id,request_key,sku,quantity,after_claim=None,fail_after_stock=False):
    # tenant_id is trusted authenticated context; this function does not authenticate it.
    if type(tenant_id) is not int or tenant_id<=0:
        raise InvalidRequest('invalid tenant')
    if type(quantity) is not int or not 1<=quantity<=10:
        raise InvalidRequest('quantity must be an integer from 1 to 10')
    if type(request_key) is not str or not 1<=len(request_key)<=80:
        raise InvalidRequest('invalid request key')
    if type(sku) is not str or not 1<=len(sku)<=80:
        raise InvalidRequest('invalid sku')
    if not conn.autocommit or conn.info.transaction_status!=TransactionStatus.IDLE:
        raise ValueError('reserve requires an idle autocommit connection and owns its transaction')
    try:
        with conn.transaction():
            claimed=conn.execute(CLAIM,(uuid4(),tenant_id,request_key,sku,quantity)).fetchone()
            if claimed is None:
                row=conn.execute('SELECT id,sku,quantity,total_minor,currency,status FROM lesson.reservations WHERE tenant_id=%s AND request_key=%s',
                                 (tenant_id,request_key)).fetchone()
                if row is None or row[5]!='reserved': raise RuntimeError('incomplete reservation state')
                if (row[1],row[2])!=(sku,quantity): raise IdempotencyConflict('key reused with different payload')
                return {'reservation_id':str(row[0]),'quantity':row[2], 'total_minor':row[3],
                        'currency':row[4],'replayed':True}
            reservation_id=claimed[0]
            if after_claim: after_claim(conn)  # Deterministic test coordination; not an HTTP option.
            product=conn.execute(TAKE_STOCK,(quantity,tenant_id,sku,quantity)).fetchone()
            if product is None: raise OutOfStock('stock unavailable')
            if fail_after_stock: raise RuntimeError('injected before reservation/outbox completion')
            total=product[0]*quantity
            conn.execute("UPDATE lesson.reservations SET status='reserved',total_minor=%s,currency=%s WHERE id=%s",
                         (total,product[1],reservation_id))
            conn.execute('INSERT INTO lesson.outbox (reservation_id,payload) VALUES (%s,%s)',
                         (reservation_id,Jsonb({'tenant_id':tenant_id,'reservation_id':str(reservation_id),'kind':'reserved'})))
            return {'reservation_id':str(reservation_id),'quantity':quantity,'total_minor':total,
                    'currency':product[1],'replayed':False}
    except ForeignKeyViolation as error:
        if error.diag.constraint_name=='reservation_product_fk':
            raise OutOfStock('stock unavailable') from error
        raise
```

### Trace a new reservation

```text
validate trusted tenant/key/SKU/quantity
BEGIN
  INSERT pending reservation with tenant/key uniqueness
  UPDATE product SET available=available-quantity
    WHERE tenant/SKU match AND available >= quantity
    RETURNING trusted price/currency
  UPDATE reservation to reserved with computed total
  INSERT outbox intent
COMMIT
return reservation result
```

The function returns from inside the context, but Python exits the transaction context before completing that return. A commit error can still prevent a successful result. The explicit idle/autocommit precondition keeps this boundary visible to the caller.

The stock predicate and decrement are one database statement. At Read Committed, a competing update may wait for the row and then recheck its condition against the updated version. A zero-row result is meaningful: there was no matching product with enough available stock. Do not select stock into Python, subtract from a stale value and write that absolute value back.

The price comes from RETURNING on the product row that is updated. A client-supplied total is not trusted. The reservation preserves the committed price/currency for later replays even if the catalog subsequently changes. This example snapshots the current reservation total; it does not implement tax, discounts, FX or payment capture.

### Why the idempotency gate comes first

ON CONFLICT names the exact tenant/key constraint and attempts a pending row. If a concurrent transaction has inserted the same key, PostgreSQL can wait for its outcome. When that other transaction commits, DO NOTHING returns no inserted row. The following SELECT, under Read Committed, can see the now-committed reservation and return its original result.

A single statement's snapshot and conflict handling are not the same as a later statement's snapshot. This design deliberately uses a later SELECT. Do not copy it into another isolation level without handling that level's visibility/retry behavior. It also assumes completed reservation rows are retained during the supported replay window and that writers obey the service's state transition.

Reusing the key with another SKU/quantity raises IdempotencyConflict. Tenant scope is included in both the key and lookup. A successful replay bypasses stock work, including when the product is now sold out. Moving the gate after the stock check would reject a valid retry just because the original request consumed the final unit.

ON CONFLICT is not “ignore all database errors.” It only handles the specified conflict; the foreign key and other constraints still apply. Reference: [INSERT, ON CONFLICT and RETURNING](https://www.postgresql.org/docs/18/sql-insert.html).

### Rollback is part of the feature

If quantity exceeds stock, the exception leaves the transaction and rolls back the pending claim. The same key can succeed after a later restock. If failure is injected after decrementing stock, the decrement, reservation and outbox all roll back. Catching a constraint error outside the transaction ensures rollback occurs before mapping the named error.

The schema permits pending rows because they exist during this transition. It does not force every database writer to complete the workflow before commit. A direct writer could commit a pending row; a duplicate then raises the explicit incomplete-state invariant error. This is one reason to control write paths and grant only the capabilities each real service needs.

The test hooks after_claim and fail_after_stock coordinate or interrupt the fixture. They are not API request options. An endpoint must never let a caller inject server execution hooks.

### Actual reservation evidence

```json
{
  "successful_reservation": {
    "quantity": 2,
    "total_minor": 25000,
    "currency": "INR",
    "replayed": false
  },
  "last_unit_race": {
    "wait_observed": true,
    "blocked_statement": "conditional stock UPDATE",
    "remaining_stock": 0,
    "reservations": 1,
    "outbox_rows": 1,
    "outcome": "one reserved and one unavailable"
  },
  "same_key_race": {
    "wait_observed": true,
    "blocked_statement": "idempotency INSERT",
    "remaining_stock": 0,
    "reservations": 1,
    "outbox_rows": 1,
    "outcome": "one new and one replay"
  }
}
```

The two races use separate sessions and observe pg_blocking_pids before releasing the blocker. For the last-unit race, the observed blocked statement is the conditional product UPDATE. The setup uses a compatible non-key row lock so the competitor can pass its foreign-key check and reach that stock statement. One request commits, the other gets unavailable; stock ends at zero with one reservation and one outbox row.

For the duplicate-key race, the observed wait occurs at the reservation INSERT. An ordinary observer cannot see the uncommitted pending row. After the first transaction commits, the second returns a replay of the same reservation ID. The checks do not depend on sleeping for an assumed duration or guessing which thread ran first.

### What the outbox guarantees here

The same transaction stores both the reservation and an intent to notify another component. If it commits, a later worker can find that intent; if it rolls back, neither survives. A direct email call inside the transaction would not roll back an already sent email.

This module inserts outbox rows but has no dispatcher. A future worker still needs bounded claiming, retry/backoff, poison-event handling, idempotent downstream effects and a delivery policy. “Send, then mark delivered” can send twice if the worker crashes between those steps. “Mark, then send” can lose the effect. The outbox provides a durable handoff point, not universal exactly-once delivery. Revisit [M9: Webhooks and reliable integrations](/docs/resume-skills/webhooks-payments-reliable-integrations).

---

## 13.6 Transactions, MVCC and isolation in application terms

A transaction groups database operations into a commit/rollback unit. Atomicity prevents half of that unit from being committed. Isolation determines how concurrent transactions interact. Neither property makes every read-modify-write algorithm correct automatically.

PostgreSQL uses MVCC: queries can read row versions visible to their snapshots while other transactions change data. An ordinary SELECT does not read another transaction's uncommitted update. It often proceeds while a row writer holds a lock, reading the visible committed version. That is distinct from a locking SELECT, and ordinary reads can still encounter conflicts with certain table/DDL locks.

### Recorded snapshot experiment

An observer reads account balance 100. Another session commits a change to 200. The observer reads again within its transaction:

| Isolation used | First / second read | Interpretation |
| --- | --- | --- |
| Read Committed | 100 / 200 | Each statement obtains a new snapshot |
| Repeatable Read | 100 / 100 | The transaction retains its snapshot |

PostgreSQL treats Read Uncommitted like Read Committed. Its Repeatable Read is stronger than the minimum SQL-standard definition in some respects, including preventing phantoms, but it still allows serialization anomalies. Serializable adds checks that can abort a transaction whose concurrent execution cannot be serialized; the application must be prepared to retry. Reference: [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html).

### Lost update: the transaction can be valid and the algorithm wrong

```text
initial balance = 100
A reads 100; plans absolute value 90
B reads 100; plans absolute value 80
A writes 90 and commits
B writes 80 and commits
final = 80; A's deduction was overwritten
```

That is the observed Read Committed fixture. By contrast, SQL relative updates balance=balance-10 and balance=balance-20 preserve both deductions and end at **70**. The database coordinates updates to the same row; it cannot infer that two arbitrary absolute replacement values came from stale arithmetic.

Another technique is optimistic concurrency: update only if a revision still equals the revision read earlier, increment it atomically and inspect the affected-row count. The fixture demonstrates compare-and-set using an expected balance: the first update affects one row and the stale writer zero. A proper revision column avoids the ABA problem where a business value changes and later returns to its old value.

Choose the technique from the invariant. A single conditional statement is excellent for a per-product stock limit. A multi-row decision can require explicit locking or Serializable with full-transaction retries. Raising isolation everywhere without retry handling creates a different failure mode.

### Write skew: two different rows can break one shared rule

Two doctors are initially on call. The invariant is “at least one remains on call.” Both transactions count two on-call doctors from their snapshots; each switches a different doctor off. Under the fixture's Repeatable Read schedule, both commit and **zero** remain. No single row was overwritten; the broken rule spans the set.

The Serializable fixture deliberately overlaps a competing change. The first attempt receives a real **40001**. The service retries the whole transaction, reads the new count of one and refuses the final switch-off. Recorded result: **two attempts, one doctor remaining, final change not allowed**.

A suitable common lock can also serialize such a decision, but every competing writer must use the protocol. Locking only the row you eventually change does not necessarily protect a predicate over other rows. Define the rule first, then choose the shared point of coordination.

---

## 13.7 Row locks, waiting, timeouts and deadlocks

`SELECT ... FOR UPDATE` locks selected rows against conflicting row operations until the transaction ends. Use it when application work genuinely needs to read and then decide before writing. The stock service instead expresses its simple invariant in one conditional UPDATE; adding a preliminary locking read is unnecessary there.

The row-lock verifier holds a lock in session A, starts an UPDATE in session B and observes the actual blocking relationship. An ordinary observer reads balance 100 while B waits. Once A releases its transaction, B completes and balance becomes 101. The observer's visible row version and B's lock wait are separate facts.

| Tool | Useful behavior | Verified local observation |
| --- | --- | --- |
| FOR UPDATE | Wait for a conflicting row lock | Competing writer was blocked, then completed |
| NOWAIT | Fail instead of waiting for that row lock | SQLSTATE 55P03 |
| SKIP LOCKED | Omit currently locked rows from the selection | Held job 1; another worker selected job 2 |
| lock_timeout | Bound lock acquisition wait | 100ms setting triggered 55P03 |
| statement_timeout | Bound a statement's execution budget | 50ms setting canceled pg_sleep(5), 57014 |

These are functional outcomes, not exact timing assertions. A statement budget, connection-establishment timeout, pool-acquisition timeout and HTTP deadline bound different parts of a request. Arrange budgets so work has time to roll back and release resources before the outer request deadline expires.

### SKIP LOCKED is a work-distribution tool

A worker can select eligible jobs in a transaction with FOR UPDATE SKIP LOCKED, mark a bounded batch claimed and commit. It avoids waiting behind a job already claimed by another worker, but the selected set is deliberately incomplete. It is inappropriate for a report that promises a complete consistent list of all pending jobs.

Do not hold that claim transaction open during a slow external call. A durable lease/expiry and recovery protocol must handle worker crashes after claim. This fixture verifies selecting job 2 while job 1 is locked; it does not implement a crash-safe job system or fairness guarantee.

### Actual deadlock

```text
A locks account 1       B locks account 2
A requests account 2 -> waits for B
B requests account 1 -> waits for A
cycle -> PostgreSQL aborts one transaction with 40P01
survivor completes after the victim releases its locks
```

The fixture creates this cycle and checks one aborted transaction and one committed increment. It never assumes which session PostgreSQL will choose as victim. Use a consistent lock order, keep transactions short and still handle deadlock retries; ordering in one code path cannot prove every other writer follows it.

Monitor wait events and blockers rather than labeling all slow queries “missing indexes.” pg_stat_activity and pg_blocking_pids help distinguish execution from waiting. Log request correlation, database application_name, operation and SQLSTATE without copying secrets or unrestricted parameter values. References: [explicit locking](https://www.postgresql.org/docs/18/explicit-locking.html), [statistics and activity monitoring](https://www.postgresql.org/docs/18/monitoring-stats.html).

---

## 13.8 Retry the transaction, not its final statement

The exact verified retry helper is below. The callback must contain the complete database decision, including reads. The pool supplies idle autocommit connections as configured in db.py.

```python
from psycopg.errors import SerializationFailure, DeadlockDetected

def serializable(pool,operation,*,attempts=3,on_retry=None):
    if type(attempts) is not int or attempts<1: raise ValueError('attempts must be positive')
    for attempt in range(attempts):
        try:
            with pool.connection() as conn:
                with conn.transaction():
                    conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                    return operation(conn)
        except (SerializationFailure,DeadlockDetected) as error:
            if on_retry: on_retry(error.sqlstate)
            if attempt+1==attempts: raise
    raise AssertionError('unreachable')
```

A serialization failure invalidates the decision based on the old reads. Retrying just the last UPDATE would preserve that stale decision. The helper leaves the transaction context, rolls back and begins a fresh attempt. Both statement-time and commit-time failures can be caught outside the context.

This teaching helper has a bounded attempt count and deterministic immediate retries. A real service should also fit retries inside a request deadline, add bounded backoff/jitter where appropriate and track retry/exhaustion rates. Those production scheduling policies are design additions, not implemented here. The callback cannot safely send an email or charge a provider on every attempt because database rollback cannot undo that external effect.

### Classify errors before deciding to retry

| Observed error | Meaning here | Sensible response |
| --- | --- | --- |
| 40001 | Serialization failure | Roll back, rerun the whole safe transaction within a bounded policy |
| 40P01 | Deadlock victim | Same whole-transaction boundary; investigate lock ordering |
| 23505 | Unique violation | Interpret the named constraint; not automatically transient |
| 23503 / 23514 / 23502 | FK/check/non-null violation | Known domain mapping or defect; blind retry usually changes nothing |
| 55P03 | Lock unavailable / lock timeout | Bounded failure or explicit policy; do not retry forever |
| 57014 | Query canceled | Check the cause/deadline; not permission to restart expensive work indefinitely |
| 25P02 | Transaction already failed | Roll back before more commands; find the original error |
| PoolTimeout | Client pool acquisition failed | Handle pressure/deadline; this is not a PostgreSQL SQLSTATE |

Use structured SQLSTATE and diagnostic constraint names rather than English error-message matching. This run verified these classifications against real failures; the retry helper specifically catches SerializationFailure and DeadlockDetected. Reference: [PostgreSQL error codes](https://www.postgresql.org/docs/18/errcodes-appendix.html).

A connection failure during COMMIT introduces another question: did the server commit before the acknowledgment was lost? A missing response is not proof of rollback. A retained idempotency key and durable result can support reconciliation/replay on a new connection. This module tests replay after committed success and rollback after injected application failure; it does not inject network loss during COMMIT or claim that retry.py resolves ambiguous outcomes.

---

## 13.9 Pools: bounded reuse, not extra database capacity

A pool lease temporarily gives code a connection. With max_size=2, two simultaneous borrowers use distinct PostgreSQL sessions; a third borrower waits up to its acquisition timeout. The fixture holds both leases, observes PoolTimeout for the third and then verifies the pool works after release.

Returning a lease permits reuse of a session: max_size=1 reuses the same backend in the check. It does not create a new logical clean-room session every time. A transaction exception rolls back its partial write, and the tested lease is returned idle, but arbitrary session settings need their own policy.

### Session state can outlive a request

The verifier sets a nonlocal application_name and observes it on the next lease. By contrast, a SET LOCAL setting inside a transaction expires at its end. A reset callback issuing RESET ALL clears the **tested configuration setting**. That is not evidence that RESET ALL erases every kind of session state, temporary table, advisory lock or prepared statement.

Prefer transaction-local request settings, explicit reset rules and consistent connection configuration. If a design uses role switching or tenant context in database state, test that one request cannot inherit another's context. This fixture demonstrates the risk with application_name and does not implement database tenant context or row-level security.

### Count connections across processes

```text
3 application replicas × 2 worker processes × pool max_size 2
= up to 12 application client connections
+ migrations, jobs, monitoring and operational headroom
```

This is capacity arithmetic, not a load test. Doubling web workers can double independent pool limits. A larger pool can shift waiting into an overloaded database rather than improve throughput. Measure lease duration, queued borrowers, acquisition timeouts, active sessions, lock waits and query latency before tuning.

Create the pool at the relevant process's application lifecycle boundary and close it on shutdown. Do not open a fresh pool per request or share a pre-fork connection as if it were independent sessions. Release a lease before unrelated network work; stream/export designs need explicit ownership if database work outlives ordinary response handling.

An external pooler such as PgBouncer is a separate layer. Its pooling mode can change which session features remain stable across transactions. No external pooler or async pool is installed/exercised here. Reference: [Psycopg connection pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html).

---

## 13.10 Indexes and query plans: begin with a query shape

An index trades storage and write maintenance for useful access paths. “Add indexes to all columns” ignores both the queries and the cost of maintaining them. Start with predicates, joins, ordering, result size and the actual data distribution.

The fixture asks for the latest 20 open events for tenant 7:

```sql
SELECT id, created_at, payload
FROM lesson.events
WHERE tenant_id = 7 AND status = 'open'
ORDER BY created_at DESC, id DESC
LIMIT 20;

CREATE INDEX events_lookup
ON lesson.events (tenant_id, status, created_at DESC, id DESC);
```

This index puts equality-filtered fields first and then the ordered fields, including a deterministic tie-breaker. It can locate the relevant range and produce the desired order without a separate Sort. The payload is not included, so the recorded plan is an Index Scan, not an asserted index-only scan.

A useful B-tree rule is to design around leading equality predicates and the following range/order. Avoid turning it into “an index is never useful without its first column”: PostgreSQL 18 supports B-tree skip scan for suitable distributions, and the planner makes a cost decision. Reference: [multicolumn indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html).

### Exact executed plan verifier: verify_plans.py

The aggregate runner supplies its fresh database. This source contains fixture setup, the actual query, natural before/after plans and mutation checks.

```python
from db import prepare,connect
from checks import Checks,equal,require
prepare()
checks=Checks('plans')
observed={}
QUERY="""SELECT id,created_at,payload FROM lesson.events
WHERE tenant_id=%s AND status=%s ORDER BY created_at DESC,id DESC LIMIT 20"""

def nodes(plan):
    yield plan
    for child in plan.get('Plans',[]): yield from nodes(child)

def summary(document):
    keys=['Node Type','Index Name','Plan Rows','Actual Rows','Actual Loops',
          'Rows Removed by Filter','Shared Hit Blocks','Shared Read Blocks']
    return [{key:node[key] for key in keys if key in node} for node in nodes(document['Plan'])]

with connect(admin=True) as conn:
    conn.execute('CREATE TABLE lesson.events (id bigint PRIMARY KEY,tenant_id int NOT NULL,status text NOT NULL,created_at timestamptz NOT NULL,payload text NOT NULL)')
    conn.execute("""INSERT INTO lesson.events SELECT g,(g%100)+1,
        CASE WHEN (g/100)%10<2 THEN 'open' ELSE 'closed' END,
        TIMESTAMPTZ '2026-01-01 00:00:00+00'+g*INTERVAL '1 second',repeat('x',200)||g::text
        FROM generate_series(1,50000) AS g""")
    conn.execute('ANALYZE lesson.events')
    conn.execute('SET max_parallel_workers_per_gather=0')  # Simplify this fixture's plan tree.
    before=conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+QUERY,(7,'open')).fetchone()[0][0]
    expected=conn.execute(QUERY,(7,'open')).fetchall()
    checks.check('unindexed selective ordered fixture naturally scans and sorts',
                 lambda:require(any(n['Node Type']=='Seq Scan' for n in nodes(before['Plan'])) and any(n['Node Type']=='Sort' for n in nodes(before['Plan']))))
    conn.execute('CREATE INDEX events_lookup ON lesson.events (tenant_id,status,created_at DESC,id DESC)')
    conn.execute('ANALYZE lesson.events')
    after=conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+QUERY,(7,'open')).fetchone()[0][0]
    checks.check('composite index preserves the actual result rows',lambda:equal(conn.execute(QUERY,(7,'open')).fetchall(),expected))
    checks.check('planner naturally uses the composite index without a Sort node',
                 lambda:require(any(n.get('Index Name')=='events_lookup' for n in nodes(after['Plan'])) and all(n['Node Type']!='Sort' for n in nodes(after['Plan']))))
    broad=conn.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM lesson.events WHERE status='closed'").fetchone()[0][0]
    checks.check('broad fixture still naturally chooses a sequential scan',
                 lambda:require(any(n['Node Type']=='Seq Scan' for n in nodes(broad['Plan']))))
    observed.update(fixture_rows=conn.execute('SELECT count(*) FROM lesson.events').fetchone()[0],
                    matching_rows=conn.execute("SELECT count(*) FROM lesson.events WHERE tenant_id=7 AND status='open'").fetchone()[0],
                    result_limit=len(expected),before=summary(before),after=summary(after),broad=summary(broad),
                    raw_before=before,raw_after=after,raw_broad=broad,
                    planner_settings={'enable_seqscan':conn.execute('SHOW enable_seqscan').fetchone()[0],'max_parallel_workers_per_gather':0})
    def plain():
        conn.execute('EXPLAIN UPDATE lesson.accounts SET balance=balance+1 WHERE id=1').fetchall()
        equal(conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],100)
    checks.check('plain EXPLAIN does not execute the UPDATE',plain)
    def analyze_write():
        try:
            with conn.transaction():
                conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) UPDATE lesson.accounts SET balance=balance+1 WHERE id=1').fetchall()
                equal(conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],101)
                raise ValueError('rollback fixture mutation')
        except ValueError: pass
        equal(conn.execute('SELECT balance FROM lesson.accounts WHERE id=1').fetchone()[0],100)
    checks.check('EXPLAIN ANALYZE executes the UPDATE; explicit transaction rollback restores it',analyze_write)
    def concurrent_index():
        from psycopg.errors import ActiveSqlTransaction
        try:
            with conn.transaction(): conn.execute('CREATE INDEX CONCURRENTLY not_created ON lesson.events(status)')
        except ActiveSqlTransaction as error: equal(error.sqlstate,'25001')
        else: raise AssertionError('concurrent index accepted transaction block')
    checks.check('CREATE INDEX CONCURRENTLY is rejected inside a transaction block',concurrent_index)
checks.save(observations=observed,scope='Actual PostgreSQL plans on a 50000-row fixture; counts/plans, not a benchmark')
```

### Actual before/after evidence

The fixture has **50,000 rows**, of which **100** match tenant 7/open. The query returns 20. Statistics are collected with ANALYZE. enable_seqscan stays on; parallel workers are disabled only to simplify this teaching plan tree. The index path is chosen naturally, without a forced-index setting.

Recorded plan summaries, with timing omitted:

```json
{
  "before": [
    {
      "Node Type": "Limit",
      "Plan Rows": 20,
      "Actual Rows": 20,
      "Actual Loops": 1,
      "Shared Hit Blocks": 1713,
      "Shared Read Blocks": 0
    },
    {
      "Node Type": "Sort",
      "Plan Rows": 104,
      "Actual Rows": 20,
      "Actual Loops": 1,
      "Shared Hit Blocks": 1713,
      "Shared Read Blocks": 0
    },
    {
      "Node Type": "Seq Scan",
      "Plan Rows": 104,
      "Actual Rows": 100,
      "Actual Loops": 1,
      "Rows Removed by Filter": 49900,
      "Shared Hit Blocks": 1713,
      "Shared Read Blocks": 0
    }
  ],
  "after": [
    {
      "Node Type": "Limit",
      "Plan Rows": 20,
      "Actual Rows": 20,
      "Actual Loops": 1,
      "Shared Hit Blocks": 23,
      "Shared Read Blocks": 3
    },
    {
      "Node Type": "Index Scan",
      "Index Name": "events_lookup",
      "Plan Rows": 97,
      "Actual Rows": 20,
      "Actual Loops": 1,
      "Shared Hit Blocks": 23,
      "Shared Read Blocks": 3
    }
  ],
  "broad": [
    {
      "Node Type": "Seq Scan",
      "Plan Rows": 40102,
      "Actual Rows": 40000,
      "Actual Loops": 1,
      "Rows Removed by Filter": 10000,
      "Shared Hit Blocks": 1713,
      "Shared Read Blocks": 0
    }
  ]
}
```

Before the index, the sequential scan returns 100 matches and removes 49,900 rows by filtering, then a Sort and Limit produce 20 rows. After the index, events_lookup returns the 20 requested rows without a Sort. The verifier separately compares the full actual result rows before and after so the plan change does not hide a correctness change.

The broad query asks for all closed events: **40,000 of 50,000 rows**. It still uses a sequential scan. Reading most rows through an index can cost more than a sequential pass; the selective ordered query and broad query have different work requirements.

### Read a plan without making up a benchmark

- **Plan Rows** is an estimate; **Actual Rows** is observed output per execution of that node. Consider loops when interpreting repeated inner work.
- **Rows Removed by Filter** shows inspected rows rejected at that node, distinct from returned rows.
- **Cost** is the planner's relative work estimate in configured units, not milliseconds.
- **Buffers** report block activity. A shared-buffer miss does not by itself prove physical disk access; the OS cache can intervene.
- Parent totals can include child work; do not sum every nested node as independent work.

Raw plans, including timings, are preserved in plans-results.json. One warm local fixture run cannot establish production throughput, tail latency or a universal speedup. The useful evidence here is the result equivalence and changed access path. Reference: [using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html).

### EXPLAIN ANALYZE really executes the statement

Plain EXPLAIN UPDATE leaves the fixture balance at 100. EXPLAIN ANALYZE UPDATE changes it to 101 inside the transaction; an explicit rollback restores 100. Never treat ANALYZE as a harmless preview for writes. A rollback can undo transactional row changes, but it does not promise to reverse sequence allocation or external effects from every possible function.

### Choose index families and query semantics deliberately

B-tree supports common equality/range/order access. GIN can support suitable JSONB/array containment operations. Partial indexes can target a useful subset, and expression indexes can support a matching expression. Each needs query/operator compatibility and an evaluation of storage/write overhead. This module executes the composite B-tree example; it does not benchmark GIN, partial or expression indexes. Reference: [index types](https://www.postgresql.org/docs/18/indexes-types.html).

For large paginated lists, reason about a stable cursor such as (created_at,id), not only a huge OFFSET. Match tenant filters, ordering and the next-page predicate to the index and define behavior under concurrent inserts. An index never repairs a missing tenant condition or supplies application authorization.

---

## 13.11 Migrations and operating the database boundary

A schema is a deployed contract shared by application versions. A migration is a versioned change to that contract. Development schema.sql initializes fresh databases for this lesson; it is not a production migration history or a command to rerun against existing data.

### A safe compatibility sequence

Suppose reservations need a new required business field:

1. Add a compatible nullable field or another representation that old code can tolerate.
2. Deploy code that handles both old and new rows and starts populating the new field.
3. Backfill existing rows in bounded work, observing load and lock behavior.
4. Validate the intended invariant, then enforce the stricter requirement.
5. Remove obsolete readers/writers only after their deployment window has closed.

This is a design sequence, not an executed online-migration demonstration. A default or ALTER TABLE can have version- and operation-specific rewrite/lock behavior. Check the exact statement, data size and PostgreSQL version instead of promising “migrations never block.” Ordinary CREATE TABLE rolls back in the fixture. CREATE INDEX CONCURRENTLY deliberately fails inside a transaction block with 25001; it requires a separately planned execution path. Concurrent index creation has its own waits and failure/invalid-index caveats, rather than being lock-free. Reference: [CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html).

The fixture separates owner DDL from application DML: m13_app cannot create a table in lesson. Real deployment grants should be narrowed to the actual tables/operations; the broad lesson grants are for multiple experiments. Grants on existing objects also require a policy for objects created by later migrations.

### MVCC creates maintenance responsibilities

Updates/deletes leave old row versions until they are no longer needed and vacuum can reclaim reusable space. Long-lived transactions can retain an old horizon and interfere with cleanup. ANALYZE collects planner statistics; it does not create an index or guarantee a particular plan. Autovacuum/autoanalyze need observation and suitable configuration for real workloads.

When an endpoint slows, check the complete path: pool acquisition, blocked transactions, plan/row estimates, growing work per request, long transactions and maintenance health. Do not run VACUUM FULL as a reflex; it is a different operation with stronger disruption implications. Reference: [routine vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html).

A durable service also needs a backup/restore policy and recovery objectives. A replica is not an independent historical backup: unintended changes can propagate. A backup is useful only if restoration and the required recovery point are exercised. This module neither provisions replication nor tests backup recovery. Reference: [backup and restore](https://www.postgresql.org/docs/18/backup.html).

---

## 13.12 Architectural understanding: build an inventory reservation system

Start by stating requirements: reserve bounded stock for an authenticated tenant, return a stable result for retries, reject changed payloads on the same key and retain a durable notification intent. Separate these from later features such as payment, expiry, cancellation and fulfillment.

```text
HTTP ingress
  -> authenticate + authorize + derive tenant
  -> validate request + idempotency key
  -> bounded application pool
  -> reserve() transaction
       products <-> reservations -> outbox
  -> committed result / controlled error

proposed dispatcher -> claim outbox work -> downstream consumer/provider
proposed reconciler -> investigate ambiguous provider/delivery outcomes
```

### Step-by-step build path

**Step 1: define the data rules.** Product key includes tenant; inventory is nonnegative; the request key is unique per tenant; a reserved row carries a trusted price snapshot. Decide whether a reservation is immediately permanent or a temporary hold. This implementation only models the former transition and does not release stock automatically.

**Step 2: implement one transaction.** Use the tenant/key insert as the replay gate, conditional stock UPDATE as the per-product concurrency point and one commit for reservation/outbox. Test malformed input, unavailable inventory and failure after decrement.

**Step 3: put an API around it.** Derive tenant from authenticated authorization context, acquire a lease and invoke the service. Define controlled responses for unavailable stock and payload/key conflicts, and avoid exposing internal SQL/constraint details. This chapter provides the database service; the HTTP adapter and authentication are proposed extensions.

**Step 4: test overlap.** Separate connections are necessary. Prove the competitor reached the intended wait using database observations, then release the blocker and assert final state. The included tests cover both distinct-key last-unit contention and same-key replay contention.

**Step 5: add reliable background work.** A dispatcher needs claim ownership, deadlines, retries and duplicate-tolerant effects. Claim a bounded batch; do external work outside a long-held row transaction; reconcile crashes and ambiguous acknowledgments. The outbox's delivered_at column is only a starting point for that policy.

**Step 6: handle lifecycle extensions.** Cancellation/expiry must be a guarded state transition that restores stock once, not a repeated “increment stock” endpoint. A payment integration needs its own provider idempotency key, verified events and reconciliation. A database transaction cannot atomically commit a payment provider's state along with local rows.

**Step 7: operate from evidence.** Track reservation outcomes, key conflicts, pool waits, lock waits, rollback/retry rates, dispatcher lag and query plans. Plan connection limits across replicas/workers and preserve space for maintenance. Add indexes for measured read/worker queries rather than assuming the lesson schema serves every future access path.

### Failure reasoning

| Failure point | Database result in this implementation | Follow-up responsibility |
| --- | --- | --- |
| Invalid quantity before transaction | No writes | Return validation failure |
| Product absent / insufficient stock | Pending claim rolled back | Return unavailable; later retry can succeed after restock |
| Exception after stock UPDATE | All service changes rolled back | Record failure without claiming a reservation |
| Two requests for the final unit | One reservation, one unavailable | Controlled domain response |
| Same key concurrently | One new result, one replay | Preserve key/result for its supported retry window |
| Same key, changed payload | Conflict; no extra stock effect | Require a new operation/key rather than mutating history |
| Lost response after commit | Outcome may be uncertain to client | Reconcile/replay using durable key; network loss not injected here |
| Worker crashes after downstream send | Delivery may be duplicated | Idempotent consumer/provider protocol; worker not implemented here |

This design scales application replicas without relying on a process-local mutex. It still has contention on a popular product's row, finite database capacity and operational work. Partitioning, sharding or caching is not an automatic next step: first measure the bottleneck and preserve the invariant when changing its coordination point.

---

## 13.13 Connect this module to a resume discussion

If a resume lists PostgreSQL, be ready to name the entities, important keys and one query you actually used. Explain how the application acquired connections, where transactions began/ended and which constraint protected a rule. If an ORM generated the query, explain the generated SQL/access pattern rather than saying “the framework handles it.”

For a backend project, a defensible explanation follows: requirement -> schema/key -> query/transition -> concurrent failure -> verification -> operational limit. Use this fixture to practice that explanation, but do not describe these local checks as production traffic or invent a latency improvement from one plan run.

If your project stored embeddings, metadata or documents in PostgreSQL, separate that extension's indexing/retrieval behavior from ordinary relational constraints and transactions. Later AI/vector modules will cover those choices. PostgreSQL on a resume does not imply experience running every extension or operating a replicated cluster.

### Must remember

1. A database role is not the request's tenant; tenant scope belongs in trusted context and every relevant data path.
2. Parameter binding protects values; dynamic identifiers need deliberate composition and permission checks.
3. A transaction does not repair stale read-modify-write arithmetic by itself.
4. Read Committed snapshots change per statement; Repeatable Read can still allow write skew.
5. Serializable/deadlock retries rerun the complete safe transaction after rollback.
6. A unique tenant/key gate plus retained result supports idempotency; changed payloads are conflicts.
7. Return from a pool lease is not proof that all session state was erased.
8. EXPLAIN ANALYZE executes; inspect real rows/loops/filters and treat timings as scoped evidence.
9. Indexes are query-shaped tradeoffs, and a sequential scan can be correct.
10. A local outbox commit is a durable intent, not proof of downstream delivery.

### Common wrong answers

| Claim | Correction |
| --- | --- |
| “We checked stock, so another request cannot take it.” | A separated read and write race unless the transition is coordinated. |
| “Repeatable Read makes all business decisions serializable.” | The disjoint-row write-skew fixture commits a broken cross-row rule. |
| “A retry means repeat the UPDATE.” | Reread and recompute the whole transaction after a serialization failure. |
| “Catch the database exception and continue.” | An aborted transaction needs rollback or a correctly scoped savepoint. |
| “The unique precheck prevents duplicates.” | The shared unique constraint settles concurrent inserts. |
| “Foreign keys add every index we need.” | The referencing side is not automatically indexed. |
| “Pool max_size=20 means only 20 total connections.” | Independent processes/replicas multiply pool limits. |
| “The index reduced production latency by this ratio.” | The fixture establishes a plan/result change, not a production benchmark. |
| “Outbox means exactly-once email.” | A dispatcher crash can duplicate downstream delivery. |

---

## 13.14 Interview questions and follow-ups

These are curated questions covering the mechanisms in this chapter, not measured company-frequency rankings. Practice a short answer, then defend it using a query, trace or failure case.

**Q1. What is PostgreSQL, and how is it different from SQL and Psycopg?**

PostgreSQL is the database server/engine. SQL expresses database operations. Psycopg is the Python driver that connects, sends commands and adapts values/results. An ORM sits in the application and generates operations against a database.

*Follow-up:* Draw where each sits between an HTTP route and a stored row.

**Q2. What happens when a backend queries PostgreSQL?**

It acquires a connection, sends SQL and bound values, and the server plans/executes the operation under the session's transaction rules. The driver returns adapted results/errors. The service interprets them, commits or rolls back and releases its lease before reporting the outcome.

*Follow-up:* Distinguish connection wait, lock wait and actual query execution.

**Q3. What is the difference between a database, schema and role?**

A database is the connection target containing objects; a schema is a namespace within it; a role controls database identity/privileges. Neither a schema name nor a role automatically identifies an authenticated application's tenant.

*Follow-up:* Why can m13_app read both tenants without a predicate?

**Q4. Why use a connection pool?**

To reuse sessions and bound application connection demand and acquisition waiting. It does not make the database infinitely concurrent. A bounded pool can expose pressure through queueing/timeouts while protecting the server from uncontrolled session creation.

*Follow-up:* Calculate the limit for several replicas with multiple worker processes.

**Q5. Does releasing a pooled connection clear all request state?**

No. The fixture shows a nonlocal SET persisting to the next lease. SET LOCAL expires with its transaction. A reset callback can clear specified state, but the tested RESET ALL configuration cleanup is not a universal session reset guarantee.

*Follow-up:* How would you test against tenant-context leakage?

**Q6. How do parameterized queries prevent injection?**

They separate values from SQL syntax so input is adapted as data. With Psycopg, pass values separately to %s placeholders. Dynamic identifiers are SQL structure; use an allowlist plus Identifier composition instead of treating them as ordinary values.

*Follow-up:* What does SELECT %s return when bound to 'available'?

**Q7. Why are validation and database constraints both needed?**

Validation rejects malformed input early and supports a clear API contract. Constraints protect shared persisted rules against concurrent requests and alternate writers. A uniqueness precheck is racy; the unique constraint settles the concurrent insert.

*Follow-up:* Which named constraint would you map to an idempotency conflict?

**Q8. How does the schema preserve tenant-product relationships?**

Products have a composite tenant/SKU key, and reservations reference that complete pair. This rejects a tenant-1 reservation for tenant-2's product. It still requires trusted tenant context and scoped queries; the foreign key does not authenticate the caller.

*Follow-up:* Which reads/writes must carry tenant predicates?

**Q9. What does ON CONFLICT do?**

It provides an alternative action for the specified unique/exclusion conflict rules. This service names the tenant/request-key unique constraint and does nothing on a duplicate, then reads the committed result. It does not suppress check or foreign-key errors.

*Follow-up:* Why can that insert wait for an uncommitted competing insert?

**Q10. Why not use a float for money?**

Binary floating-point can introduce representation/rounding differences. Choose an explicit numeric/Decimal policy or integer minor units with currency and bounds. This service uses trusted integer prices and snapshots the total; different currencies and tax rules still need a domain policy.

*Follow-up:* How would you serialize Decimal to JSON without accidental precision loss?

**Q11. What does timestamptz retain?**

An instant, displayed in the session timezone; it does not preserve the original timezone name. For recurring local-time business rules, retain the relevant named timezone separately. Use aware application datetimes and an explicit API representation.

*Follow-up:* Is a birthday best modeled as an instant?

**Q12. What does a transaction guarantee?**

Its database changes commit or roll back as a unit, with concurrent behavior governed by isolation. It cannot roll back an email or automatically correct a stale decision. Commit acknowledgment is also distinct from the client having merely executed an UPDATE.

*Follow-up:* Which three writes must commit together in reserve()?

**Q13. What is MVCC?**

It lets transactions read versions visible to their snapshots rather than exposing another transaction's unfinished changes. An ordinary read can see the previous committed row while a writer waits/holds a row lock. Conflicting writes still require coordination.

*Follow-up:* Why did the observer read 100 during the lock-wait fixture?

**Q14. How do Read Committed and Repeatable Read differ here?**

Read Committed takes a new snapshot for each statement: the fixture reads 100 then 200 after another commit. Repeatable Read retains its transaction snapshot and reads 100 twice. A stable snapshot alone does not enforce every multi-row business invariant.

*Follow-up:* What happens when a conflicting write cannot use that snapshot safely?

**Q15. How can a lost update happen inside transactions?**

Two requests read 100, calculate different absolute balances and later overwrite the row with stale replacements. The fixture ends at 80. SQL relative updates preserve both deductions and end at 70; a revision-based compare-and-set can instead detect a stale writer.

*Follow-up:* Why is an expected business value weaker than a monotonic revision?

**Q16. What is write skew?**

Transactions read a shared condition but update different rows, so no direct same-row overwrite occurs while their combined writes break the condition. In Repeatable Read, two doctors each see two on-call people and both switch off; the fixture ends with zero.

*Follow-up:* Which common lock or Serializable retry protocol would protect the rule?

**Q17. Why must Serializable failures retry the whole transaction?**

The failed attempt's reads/decision may no longer be valid. Roll back, start a fresh transaction, reread and recompute. The fixture receives 40001, retries once and refuses the second switch-off after seeing one doctor remaining.

*Follow-up:* What makes an external provider call unsafe inside that retry callback?

**Q18. When would you use SELECT FOR UPDATE?**

When a transaction needs to lock selected rows while making a related decision before writing. Keep the scope short. For a simple stock limit, one conditional UPDATE can express and coordinate the transition without a preliminary locking read.

*Follow-up:* Does an ordinary SELECT wait behind the same row lock?

**Q19. Explain NOWAIT and SKIP LOCKED.**

NOWAIT returns an error rather than waiting for a conflicting row lock. SKIP LOCKED omits locked rows, useful for independent work claiming. It provides an intentionally incomplete view and is unsuitable for a complete report.

*Follow-up:* How does a claimed job recover if its worker dies?

**Q20. What causes a deadlock, and how do you respond?**

A cycle of sessions waits for resources held by one another. PostgreSQL aborts a victim with 40P01. Reduce risk with consistent lock ordering and short transactions, and retry a safe complete transaction under a bounded policy.

*Follow-up:* Why shouldn't the test assume a particular victim?

**Q21. Why is a transaction unusable after some SQL errors?**

The failure aborts the transaction; later commands receive 25P02 until rollback. A deliberately scoped savepoint can isolate a recoverable error so outer work continues. Catching the Python exception alone does not perform that rollback.

*Follow-up:* Where should reserve() catch its named foreign-key error?

**Q22. Why might PostgreSQL ignore an index?**

The planner estimates a sequential scan is cheaper for the query/data/settings, or the index does not support its shape well enough. The fixture's broad query returns 40,000 of 50,000 rows and naturally scans despite the new selective-query index.

*Follow-up:* Which estimates and actual rows would you compare first?

**Q23. How do you choose columns for a composite index?**

Begin with the important predicates, join/order requirements and distribution. The example uses tenant/status equality followed by created_at/id ordering. Measure the resulting plan and write cost. PostgreSQL 18 skip scan means simplistic absolute left-prefix claims need qualification.

*Follow-up:* Why include id after created_at?

**Q24. What is the difference between EXPLAIN and EXPLAIN ANALYZE?**

EXPLAIN reports an estimated plan; ANALYZE executes and reports observed work. The write fixture changes balance under ANALYZE and rolls it back explicitly. Its plan costs are not elapsed milliseconds, and one run's timings are not production performance evidence.

*Follow-up:* Which effects might rollback still not reverse?

**Q25. Are primary keys and foreign keys automatically indexed?**

Primary/unique constraints create supporting unique indexes. PostgreSQL does not automatically add an index on every referencing foreign-key column. Add one when its query or referential-action workload justifies it; inspect actual indexes rather than assume.

*Follow-up:* What indexes exist on lesson.reservations?

**Q26. Why are identity IDs allowed to have gaps?**

Sequence allocations are not rolled back like table rows. The fixture rolls back id 1 and next receives 2. Identifiers need uniqueness, not necessarily gaplessness; committed-row counts and business numbering policies must be modeled separately.

*Follow-up:* Can the largest ID tell you how many reservations committed?

**Q27. What does autovacuum have to do with a backend?**

MVCC leaves obsolete versions needing cleanup and statistics maintenance. Long-lived transactions can prevent old versions becoming removable. A backend that forgets transaction boundaries can create operating problems even if its individual SELECT looks cheap.

*Follow-up:* How would you investigate idle-in-transaction sessions and stale estimates?

**Q28. How would you roll out a schema change safely?**

Plan compatibility across old/new application versions, add compatible structure, populate it in bounded work, validate and then tighten/remove obsolete structure. Assess exact lock/rewrite behavior. Concurrent index creation needs special execution because it cannot run in a transaction block.

*Follow-up:* What happens if a concurrent index build fails?

**Q29. How does this reservation avoid overselling and duplicate effects?**

A tenant/key unique insert gates replay; a conditional relative stock UPDATE coordinates availability; reservation/outbox commit together. A concurrent duplicate waits and replays, while different-key requests for the last unit yield one reservation and one unavailable result.

*Follow-up:* Why must replay still work after inventory becomes zero?

**Q30. What would you add before calling this a complete production system?**

An authorized HTTP boundary, deployment-specific credentials/TLS, supported operating configuration, versioned migrations, monitoring/recovery, outbox delivery/reconciliation and any required cancellation/payment lifecycle. Exercise those boundaries explicitly. The completed evidence here covers real local PostgreSQL behavior, not those future integrations.

*Follow-up:* Describe one crash window and the durable state used to recover from it.

---

## 13.15 Practice tasks and checkpoints

1. **Trace a request.** Draw HTTP -> service -> pool -> driver -> PostgreSQL -> commit -> response. Label the trusted tenant source and every timeout. *Checkpoint:* distinguish lease acquisition, execution and commit rather than calling all of them “query time.”
2. **Defend the schema.** Explain every reservation constraint, then attempt a cross-tenant product relation in the isolated fixture. *Checkpoint:* it fails because of the composite FK, while an unscoped SELECT still proves authorization is separate.
3. **Break the arithmetic.** Reproduce the two stale absolute writes, then use relative SQL updates. *Checkpoint:* explain the observed 80 versus 70 without claiming transactions were absent.
4. **Observe blocking.** Hold a row lock, start a competitor and inspect pg_blocking_pids before releasing it. *Checkpoint:* prove the competitor waited on the intended operation rather than relying on a sleep.
5. **Compare isolation.** Narrate the 100/200 and 100/100 snapshots, then the two-doctor write skew. *Checkpoint:* name the difference between a stable snapshot and a serializable outcome.
6. **Extend retry policy.** Design bounded jitter/deadline handling around retry.py and specify safe callback rules. *Checkpoint:* reread the invariant on each attempt; never retry every database error blindly.
7. **Test a pool leak.** Set session state, return a lease and inspect the next borrower; compare SET LOCAL. *Checkpoint:* state exactly what your cleanup resets and what remains outside that evidence.
8. **Explain an index.** Read verify_plans.py and draw the equality range plus ordered suffix. *Checkpoint:* preserve result rows, show the natural plan change and explain the broad sequential scan without inventing throughput metrics.
9. **Design cancellation.** Add a proposed guarded reserved -> canceled transition restoring stock once, with two concurrent cancel requests. *Checkpoint:* define constraints, state predicates and replay semantics before coding; current module does not implement cancellation.
10. **Design a dispatcher.** Specify claim ownership, expiry, retries and the send-before-mark crash window. *Checkpoint:* show how a duplicate downstream effect is handled and which outcomes need reconciliation.

### Exit checklist

- [ ] I can explain database/schema/role/session without confusing them with an API tenant.
- [ ] I can bind values and safely select approved dynamic identifiers.
- [ ] I can justify composite keys, named constraints and money/time types.
- [ ] I can trace reserve() through new, replay, conflicting-payload and rollback outcomes.
- [ ] I can explain the two observed reservation races and their final state.
- [ ] I can distinguish Read Committed, Repeatable Read and Serializable using the fixtures.
- [ ] I can explain lost updates, write skew, row waits and deadlocks.
- [ ] I can retry the complete safe transaction within a bounded policy.
- [ ] I can budget pool connections across processes and avoid inherited session context.
- [ ] I can interpret EXPLAIN/ANALYZE evidence and state its performance limits.
- [ ] I can separate a committed outbox intent from downstream delivery.
- [ ] I can describe a migration/recovery plan without claiming it was exercised here.

These boxes represent your learning progress; authoring and verification do not check them for you.

---

## Sources and verification map

Research refreshed for this module on **14 October 2026**. Official documentation supplies mechanism/API references; local artifacts supply the recorded observations.

| Topic | Primary reference |
| --- | --- |
| Client/server architecture | [PostgreSQL tutorial architecture](https://www.postgresql.org/docs/18/tutorial-arch.html) |
| Schemas, search path and object resolution | [Schemas](https://www.postgresql.org/docs/18/ddl-schemas.html) |
| Constraints and null/uniqueness semantics | [Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) |
| Data representation | [Data types](https://www.postgresql.org/docs/18/datatype.html), [date/time](https://www.postgresql.org/docs/18/datatype-datetime.html) |
| Driver parameters and transactions | [Psycopg parameters](https://www.psycopg.org/psycopg3/docs/basic/params.html), [transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) |
| Pool behavior | [Psycopg connection pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) |
| Isolation and locking | [Isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [explicit locks](https://www.postgresql.org/docs/18/explicit-locking.html) |
| Insert/upsert and diagnostics | [INSERT](https://www.postgresql.org/docs/18/sql-insert.html), [SQLSTATE codes](https://www.postgresql.org/docs/18/errcodes-appendix.html) |
| Access paths and planning | [Multicolumn indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html), [index types](https://www.postgresql.org/docs/18/indexes-types.html), [EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) |
| Migrations and maintenance | [CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html), [vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html) |
| Operations and secure connections | [Statistics/activity](https://www.postgresql.org/docs/18/monitoring-stats.html), [libpq TLS](https://www.postgresql.org/docs/18/libpq-ssl.html), [backup/restore](https://www.postgresql.org/docs/18/backup.html) |

### Verification map

All implementation and evidence files are under examples/resume-skills/module-13-postgresql/.

| Group | Named checks | Actual boundary |
| --- | --- | --- |
| Core | 19 | Live role/authentication, adapters, parameterization, constraints, savepoints and transaction state |
| Concurrency | 14 | Separate sessions, snapshots, observed lock waits, real write skew/serialization failure/deadlock |
| Pool | 8 | Real Psycopg leases, capacity timeout, rollback, reuse and tested session setting cleanup |
| Plans | 7 | 50,000-row fixture, natural plans, result equivalence, EXPLAIN mutation and concurrent-index transaction rejection |
| Service | 12 | Atomic reservation/outbox, tenant/key scoping, replay, rollback and coordinated two-session races |
| Total | **60** | Named checks; multiple assertions may support one check |

Implementation: cluster.py, db.py, schema.sql, reservation.py and retry.py. Test support: checks.py and coordination.py. Execution: verify.py and the five verify-group files. Results: group JSON, verification-results.json, verification-output.txt, cluster-results.json and postgres-server-output.txt. Dependency, content and site validation are recorded alongside them.

Each group uses a fresh database in the runner-owned cluster. SCRAM rejects an incorrect fixture password. Existing PostgreSQL services/databases are untouched. After the run, the owned listener is stopped and temporary cluster removed. Expected server error lines record intentionally rejected operations, not unexplained suite failures.

The examples do not verify HTTP/authentication, remote TLS, production load, PgBouncer, replication, crash/power-loss recovery, backup restoration, provider payments or actual outbox delivery. The architectural additions above are explicitly proposed work. The observed fsync/synchronous_commit settings are not a substitute for durability/recovery testing.

---

## Next

Continue to [M14: MongoDB in a Backend](/docs/resume-skills/mongodb-backend) for document modeling, embedding versus references, query/index shape, aggregation, update atomicity, driver connections and the tradeoffs against relational storage.

Revisit [M12: Django and DRF](/docs/resume-skills/django-django-rest-framework) to connect ORM behavior with actual database work, [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) for trusted authorization context and [M9: Webhooks and Payments](/docs/resume-skills/webhooks-payments-reliable-integrations) for external-effect recovery. The [master roadmap](/docs/resume-skills) shows the remaining sections.
