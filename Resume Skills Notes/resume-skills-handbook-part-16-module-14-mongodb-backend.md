# Resume Skills Placement Handbook — Part 16
# Module 14: MongoDB in a Backend

**Module 14 · 5–6 hours · Tier 1 · Requires: M6–M8, M10; DBMS data models/indexes/transactions; M13 for the relational comparison**

---

## Why this module matters

MongoDB is useful when a backend's data naturally forms documents with nested fields and bounded related information. A catalog item can have category-specific attributes; an order can preserve its purchased item and price as a snapshot. The document model changes how you choose boundaries, query arrays and coordinate updates. It does not remove the need for schema design, authorization or correctness under concurrency.

An interviewer can start with “What is MongoDB?” and move to “Embed or reference?”, “Can this update oversell stock?”, “Why did these array conditions match?”, “How does a dashboard double-count orders?”, or “Why does a transaction callback run twice?”

> **Model around access patterns and atomicity boundaries; build query structure on the server; scope every data path; verify document and index behavior on the actual engine.**

This chapter builds a tenant-scoped catalog and purchase service, then connects it to array queries, dashboard aggregations, keyset pagination and real query plans. Use the [DBMS handbook](/docs/dbms) for the broader theory and [M13: PostgreSQL](/docs/resume-skills/postgresql-backend) to compare application boundaries.

**Verification: 65 checks passed — 17 core, 12 query/aggregation, ten index, six atomic-update, 15 transaction/service and five pool/cursor checks.** Named checks can contain multiple assertions. All database operations run against real MongoDB, not an in-memory mock.

### Recorded environment

| Component | Executed version / configuration |
| --- | --- |
| MongoDB Community server | 7.0.28, 64-bit Windows |
| Storage engine | WiredTiger |
| Python | CPython 3.12.10, 64-bit Windows |
| PyMongo / dnspython | 4.10.1 / 2.8.0 |
| Deployment used | Newly initialized single-member replica set, m14_fixture |
| Network | 127.0.0.1, ephemeral non-default port |
| Authentication / TLS | Disabled for this owned local fixture; no credentials or remote transport tested |
| Transaction options in purchase | snapshot read concern; majority write concern |

These are recorded teaching versions, not a claim that they are the latest releases. Server explanations use version-7.0 documentation, and driver transaction details use the matching PyMongo 4.10.1 documentation. A single-member replica set permits transaction checks but provides no multi-node failover or replicated-failure evidence.

### Run the examples

From the repository root, with the prepared environment:

```powershell
./examples/resume-skills/module-14-mongodb/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-14-mongodb/verify.py
```

To recreate dependencies, select Python 3.12 first. With python referring to it:

```powershell
python -m venv examples/resume-skills/module-14-mongodb/.venv
./examples/resume-skills/module-14-mongodb/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-14-mongodb/requirements.lock.txt
./examples/resume-skills/module-14-mongodb/.venv/Scripts/python.exe -m pip check
```

MongoDB server binaries must be installed separately. M14_MONGOD defaults to `C:/Program Files/MongoDB/Server/7.0/bin/mongod.exe`. Set that environment variable to another mongod executable if needed. The dependency lock pins package versions without hashes; installation normally needs package access. This run used cached wheels with --no-index. The environment/wheelhouse are ignored, and global packages were not changed. PyMongo supplies its own bson package; do not install the unrelated standalone bson distribution into this environment.

The aggregate verifier creates a new temporary dbPath, launches its owned hidden process on loopback, verifies the server's dbPath/port and initializes its replica set. Each group gets a fresh database. The existing MongoDB Windows service is never used. Individual verify-group files expect the explicit M14 environment supplied by verify.py; use the aggregate runner for a clean run.

The successful run records owned_dbpath_verified=true, graceful_shutdown=true, listener_stopped=true and temporary_cluster_removed=true. The test process and its data directory are gone after verification. **Port 3000 remains stopped.** No Atlas account, HTTP server, payment provider or notification dispatcher is involved.

---

## 14.1 What is MongoDB, and how does it work in a backend?

**MongoDB is a document database server. It stores BSON documents in collections and provides queries, indexes, aggregations and transactions.** PyMongo is the Python driver; mongosh is an interactive shell/client; an ODM is an application abstraction for documents. MongoDB Atlas is a managed deployment service, not another name for BSON or the driver.

```text
HTTP request -> framework route -> authenticate/authorize
             -> validate scalar inputs -> application service
             -> MongoClient topology/pool -> server command
             -> collection/index/transaction -> BSON result
             -> application serialization -> HTTP response
```

The framework decides which handler runs. The service selects trusted tenant context and a business transition. The driver communicates with the server and adapts values. MongoDB evaluates filters and performs writes against shared state. A Python lock in one web worker cannot coordinate every other application replica.

| Term | Meaning |
| --- | --- |
| Document | One BSON record, possibly containing embedded objects and arrays |
| Collection | Group of documents and associated indexes/validation rules |
| Database | Namespace containing collections |
| _id | Document identifier; typically an ObjectId when the driver generates it |
| Replica set | Members maintaining replicated data, with primary/election behavior |
| Sharded cluster | Deployment distributing data across shards via a shard-key strategy |
| MongoClient | Driver object managing topology, monitoring and connection pools |
| ClientSession | Logical context for sequential session/transaction operations |

The fixture has a single primary and no secondary. Production replica topology, election and routing behavior need their own tests. Do not equate “the transaction worked locally” with “the service survived failover.”

### BSON is richer than plain JSON

BSON supports types such as ObjectId, dates, binary data and Decimal128 in addition to familiar strings, objects, arrays and numbers. A string that looks like an ObjectId is still a different value. The verifier queries an _id using its hexadecimal string and gets no document; converting that same string to ObjectId finds it.

ObjectId is a 12-byte identifier containing a timestamp component plus other generation components. It is not an authorization token, a secret or a strict global chronological ordering guarantee. Use an explicit business timestamp and tie-breaker when the API promises ordered pagination. Reference: [BSON types and ObjectId](https://www.mongodb.com/docs/v7.0/reference/bson-types/).

---

## 14.2 Model documents from access patterns

Start with the operations: fetch a catalog item, find items by tenant/category/attributes, create an order with a price snapshot, list recent orders and aggregate paid quantities. Then choose what changes together and what can grow independently.

### Embed or reference?

| Question | Embedding is attractive when… | References are attractive when… |
| --- | --- | --- |
| Read pattern | Related data is usually read with the parent | The entity is queried independently or shared widely |
| Lifecycle | Child data belongs to and changes with the parent | Related records have independent ownership/lifetimes |
| Size | The embedded set is bounded | The child set can grow without a practical bound |
| Updates | Related fields benefit from one-document atomicity | One shared canonical value changes frequently |
| Duplication | A historical snapshot is intentional | Duplicated current values would create costly consistency work |

A product's attributes and bounded tags fit inside its document. An order embeds the purchased SKU/quantity/unit price as a historical snapshot. It references the live product by tenant/SKU when placing the order, but later catalog price changes should not rewrite what the customer purchased.

Do not embed every order ever placed into a customer document. Unbounded growth creates size, update and indexing problems. MongoDB has a 16 MiB BSON document limit; using separate documents for a growing history avoids making one ever-expanding record the unit of every update. This limit is documented, not tested by generating a near-limit payload here. Reference: [embedding related data](https://www.mongodb.com/docs/manual/data-modeling/embedding/).

### References do not create foreign keys

The core verifier inserts a document containing a nonexistent product_id successfully. A reference field is data; MongoDB does not automatically enforce a relational foreign-key rule. Decide which service owns creation/deletion, how it checks scope and whether transaction or reconciliation work is required.

Likewise, an ODM's schema or reference declaration is not proof of server-level referential integrity. If the system needs strong arbitrary relationships and frequent joins, relational modeling can be simpler. Document embedding trades some coordination for deliberate duplication; it should follow the workload rather than a claim that joins are always bad. Reference: [data modeling](https://www.mongodb.com/docs/manual/data-modeling/).

### Tenant scope is part of identity

This catalog uses a unique index on (tenant_id, sku). Two tenants can both own 'basic'; one tenant cannot insert a duplicate. Orders use (tenant_id, request_key) for replay identity. Queries, updates, pagination and lookup pipelines must preserve tenant scope. A collection is not a per-request tenant boundary: the unscoped fixture reads both tenants, while a scoped filter reads one.

---

## 14.3 Flexible schema, server validation and value types

Flexible schema means documents can differ by default. It does not mean the application has no assumptions. Mixing stock strings, numbers and booleans can produce different matching/arithmetic behavior; allowing missing tenant or currency fields can break business rules.

### Exact catalog/schema setup: catalog.py

```python
from datetime import datetime,timezone
from pymongo import ASCENDING

PRODUCT_SCHEMA={'bsonType':'object','required':['tenant_id','sku','available','unit_price_minor','currency','revision','updated_at'],
    'properties':{'tenant_id':{'bsonType':'int','minimum':1},'sku':{'bsonType':'string','minLength':1},
        'available':{'bsonType':'int','minimum':0},'unit_price_minor':{'bsonType':['int','long'],'minimum':0},
        'currency':{'enum':['INR','USD']},'revision':{'bsonType':'int','minimum':0},
        'updated_at':{'bsonType':'date'},'attributes':{'bsonType':'object'},
        'tags':{'bsonType':'array','items':{'bsonType':'string'}}}}

def prepare(db):
    db.create_collection('products',validator={'$jsonSchema':PRODUCT_SCHEMA},validationAction='error',validationLevel='strict')
    db.products.create_index([('tenant_id',ASCENDING),('sku',ASCENDING)],unique=True,name='tenant_sku_unique')
    db.create_collection('orders')
    db.orders.create_index([('tenant_id',ASCENDING),('request_key',ASCENDING)],unique=True,name='tenant_request_unique')
    db.create_collection('outbox')
    now=datetime(2026,10,14,6,30,tzinfo=timezone.utc)
    db.products.insert_many([
        {'tenant_id':1,'sku':'basic','available':10,'unit_price_minor':12500,'currency':'INR','revision':0,'updated_at':now,'attributes':{'color':'blue'},'tags':['backend','book']},
        {'tenant_id':2,'sku':'basic','available':10,'unit_price_minor':25000,'currency':'INR','revision':0,'updated_at':now,'attributes':{'color':'red'},'tags':['book']}])

class InvalidRequest(ValueError): pass

def product_filter(tenant_id,sku):
    # The caller supplies an authenticated tenant; this helper does not authenticate it.
    if type(tenant_id) is not int or tenant_id<1: raise InvalidRequest('invalid tenant')
    if type(sku) is not str or not 1<=len(sku)<=80: raise InvalidRequest('invalid SKU')
    return {'tenant_id':tenant_id,'sku':sku}
```

The products collection has a strict/error $jsonSchema validator. It requires typed fields and nonnegative stock/price/revision. It allows category-specific attributes and extra fields because additionalProperties is not disabled. The validator is intentionally focused; it is not a complete order lifecycle policy or a general cross-document rule engine.

The server rejects negative stock, string stock, boolean stock and missing currency with error code **121**. Python's bool is an int subclass, but the application uses exact type checks and the BSON validator separately rejects a boolean for an int field. Compound uniqueness rejects a same-tenant SKU duplicate with **11000**, while the other tenant's same SKU remains valid.

Orders and outbox are created without full document validators in this fixture. Their business shape is maintained by purchase.py and the unique/identifier indexes. A direct alternate writer could commit malformed/pending orders; the replay helper detects incomplete state. A production design must control alternate writers and evolve validation for its actual lifecycle. Reference: [server schema validation](https://www.mongodb.com/docs/v7.0/core/schema-validation/).

### Dates, money and serialization

The typed-value fixture round-trips Decimal128 **125.50** and an aware UTC date. Python's input microseconds 123456 become 123000 because BSON dates have millisecond precision. The connection's CodecOptions returns timezone-aware UTC datetimes; input/output timezone policy should be explicit.

For the purchase, prices are integer minor units with a currency and trusted bounds. Decimal128 is another representation with a different conversion/rounding policy; neither removes the need to define currency units, tax and overflow behavior. Avoid treating a binary float as an exact currency amount.

Extended JSON preserves BSON-specific type information. The fixture serializes/deserializes an ObjectId with bson.json_util. Raw explain documents also contain BSON timestamps, so recorded plan artifacts use Extended JSON rather than silently converting every unknown value to an arbitrary string. An ordinary HTTP API may instead expose a documented string ID and ISO timestamp; that is an intentional response contract, not a lossless BSON round-trip.

```json
{
  "typed_values": {
    "decimal": "125.50",
    "date": "2026-10-14T06:30:00.123000+00:00"
  },
  "tenant_filter_required": true,
  "dangling_reference_accepted": true,
  "null_query_ids": [
    1,
    2
  ]
}
```

---

## 14.4 CRUD and safe query construction

A filter is an executable query structure, not merely a JSON bag. A caller-supplied object containing $ne or $gt can change the query when copied directly into a filter. Construct allowed filters on the server from validated scalar values.

```python
# db is supplied by the isolated runner; tenant comes from trusted context.
query = product_filter(1, 'basic')
product = db.products.find_one(query, {'_id': 0, 'sku': 1, 'available': 1})
result = db.products.update_one(query, {'$set': {'attributes.color': 'green'}})
```

product_filter rejects a dictionary, list or null SKU. A string containing '{"$ne":null}' stays a string and matches no fixture SKU. A deliberately constructed operator filter does match, demonstrating why type validation and ownership of query structure matter. Authentication/authorization must establish tenant_id before this helper runs. The fixture has no database authentication and does not verify an HTTP login.

### Read, update, replace and delete

| Operation | What to inspect |
| --- | --- |
| insert_one / insert_many | inserted ID(s), validation/duplicate errors; batch partial results |
| find_one | A document or None; scope/projection |
| find | Cursor; iteration/batches and cleanup |
| update_one | matched_count versus modified_count; optional upserted_id |
| find_one_and_update | Atomically choose/change one document and return the selected before/after version |
| replace_one | Replaces the document body, preserving identifier rules |
| delete_one / delete_many | Scope and affected count; design lifecycle/replay consequences |

$set changes selected fields; $inc changes a numeric value relative to the current one. The core fixture increments count and retains a sibling field, then replace_one removes that sibling. Assigning settings.color with dot notation preserves settings.size; assigning the whole settings object removes the old size. Make the intended replacement boundary explicit.

matched_count can be one while modified_count is zero if the stored value already equals the requested value. A zero match can mean stale revision, unavailable stock, missing object or wrong tenant; the service decides which distinction is appropriate to expose.

An upsert inserts when no filter match exists, otherwise updates. The sequential ingestion fixture reports an upserted_id on the first call, then a matched update and one document on the second. Concurrent identity requires a suitable unique index: “we used upsert” alone is not proof that every competing call shares one logical record. $setOnInsert can initialize fields only for the insert path.

### A batch is not a transaction

An ordered insert_many sends three documents: valid, invalid, valid. The second fails validation; the first remains committed and the third is not inserted. Bulk ordering controls progress/error behavior; it does not provide all-or-nothing atomicity across the batch. Import systems need a policy for partial progress, idempotency, row errors and restart checkpoints. M15 will connect this to ingestion.

### Projection and null semantics

Projection can reduce returned fields, but it does not add tenant filtering or make an unsafe query authorized. Inclusion and exclusion generally cannot be mixed, except the _id exclusion special case. The query fixture exercises both a valid nested projection and a rejected mixed projection.

In the fixture, {label: None} matches both an explicit null and a missing label. $exists:false finds only the missing field; $type:10 finds the explicit BSON null. A single-field unique index permits only one null/missing index key, demonstrated by a missing email followed by an explicit null duplicate. A partial unique index on string email values later permits excluded missing/null documents while enforcing actual indexed strings.

For dynamic collection names that overlap driver methods, use bracket access such as db['aggregate']; db.aggregate refers to a database method in this driver. Keep collection selection application-owned rather than accepting an unrestricted client-provided name.

---

## 14.5 Arrays and embedded objects: understand what matches

Suppose one product has these variants:

```json
{
  "variants": [
    {"color": "red", "stock": 0},
    {"color": "blue", "stock": 5}
  ]
}
```

The query wants a red variant with stock:

```python
# These two predicates may match different array elements.
unsafe_meaning = {
    'variants.color': 'red',
    'variants.stock': {'$gte': 1},
}
# This requires at least one element satisfying both predicates.
same_element = {
    'variants': {'$elemMatch': {'color': 'red', 'stock': {'$gte': 1}}},
}
```

The dotted query matches the document above because one element is red and another has stock. $elemMatch does not match it. The verifier has a second document with a red in-stock variant; the dotted query returns cross and same, while $elemMatch returns only same. This is a correctness issue before it becomes an index issue. Reference: [$elemMatch](https://www.mongodb.com/docs/v7.0/reference/operator/query/elemmatch/).

Querying tags:'backend' matches a document whose tags array contains that scalar. $addToSet avoids adding the same scalar twice, but does not automatically repair preexisting duplicates or supply business uniqueness across arbitrary fields of embedded objects. Use appropriate update/filter rules for the actual identity.

An array index becomes multikey and can create several index entries for a document. More array elements can therefore mean more index maintenance even though the collection has the same document count. Do not let an unbounded event/review array grow just because the first few reads were convenient.

---

## 14.6 Single-document atomicity and stale decisions

An update to one document is atomic, including changes to multiple embedded fields. The engine evaluates the filter for a matching transition. Separate reads and subsequent absolute writes are still a race; an atomic write can faithfully apply a stale replacement value.

### Exact atomicity verifier: verify_atomic.py

```python
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from db import make_client,database
from catalog import prepare
from checks import Checks,equal,require
checks=Checks('atomic'); observed={}
with make_client() as client:
    db=database(client);prepare(db)
    key={'tenant_id':1,'sku':'basic'}
    def stale():
        a=db.products.find_one(key)['available'];b=db.products.find_one(key)['available']
        db.products.update_one(key,{'$set':{'available':a-1}})
        db.products.update_one(key,{'$set':{'available':b-2}})
        equal(db.products.find_one(key)['available'],8);observed['stale_absolute_final']=8
    checks.check('two stale read-modify-set decisions can overwrite a stock decrement',stale)
    def increments():
        db.products.update_one(key,{'$set':{'available':10}})
        gate=Barrier(2)
        def worker(amount):
            gate.wait(timeout=5)
            return db.products.update_one(key,{'$inc':{'available':-amount}}).modified_count
        with ThreadPoolExecutor(max_workers=2) as workers:equal(sorted(workers.map(worker,[1,2])),[1,1])
        equal(db.products.find_one(key)['available'],7);observed['relative_final']=7
    checks.check('independent concurrent increment operations preserve both decrements',increments)
    def last_unit():
        db.products.update_one(key,{'$set':{'available':1}});gate=Barrier(2)
        def worker(_):
            gate.wait(timeout=5)
            return db.products.update_one({**key,'available':{'$gte':1}},{'$inc':{'available':-1}}).modified_count
        with ThreadPoolExecutor(max_workers=2) as workers:results=sorted(workers.map(worker,[1,2]))
        equal(results,[0,1]);equal(db.products.find_one(key)['available'],0)
        observed['last_unit']={'modified_counts':results,'stock':0}
    checks.check('conditional single-document stock update permits one last-unit winner',last_unit)
    def revision():
        db.products.update_one(key,{'$set':{'revision':0,'available':10}})
        expected=db.products.find_one(key)['revision']
        first=db.products.update_one({**key,'revision':expected},{'$set':{'available':9},'$inc':{'revision':1}})
        second=db.products.update_one({**key,'revision':expected},{'$set':{'available':8},'$inc':{'revision':1}})
        equal((first.matched_count,second.matched_count),(1,0));equal(db.products.find_one(key)['available'],9)
    checks.check('revision predicate rejects a stale optimistic writer',revision)
    def multivalue():
        db['aggregate'].insert_one({'_id':1,'remaining':2,'items':[]})
        result=db['aggregate'].update_one({'_id':1,'remaining':{'$gte':1}},{'$inc':{'remaining':-1},'$push':{'items':'reserved'}})
        equal(result.modified_count,1);equal(db['aggregate'].find_one({'_id':1}),{'_id':1,'remaining':1,'items':['reserved']})
    checks.check('one document update changes embedded state and counter together',multivalue)
    def unguarded_multi():
        db.accounts.insert_many([{'_id':1,'balance':100},{'_id':2,'balance':100}])
        try:
            db.accounts.update_one({'_id':1},{'$inc':{'balance':-10}})
            raise ValueError('application failure before second write')
        except ValueError:pass
        equal([r['balance'] for r in db.accounts.find({}).sort('_id')],[90,100])
        observed['without_transaction_balances']=[90,100]
    checks.check('independent document writes do not roll back after an application failure',unguarded_multi)
checks.save(observations=observed,scope='Real writes and barrier-started concurrent requests; no claim of observed internal lock scheduling')
```

### Read the observed results

```json
{
  "stale_absolute_final": 8,
  "relative_final": 7,
  "last_unit": {
    "modified_counts": [
      0,
      1
    ],
    "stock": 0
  },
  "without_transaction_balances": [
    90,
    100
  ]
}
```

Two stale reads see stock 10; writing absolute values 9 then 8 loses the first deduction and ends at 8. Two concurrent $inc operations for -1 and -2 preserve both deductions and end at 7.

For the last unit, include available >= 1 in the same filter as the decrement. Barrier-started independent threads return modified counts [0,1], with stock zero. There is one winner because the predicate ceases to match after the successful atomic transition. The fixture verifies the final result; it does not inspect an internal lock wait or claim a particular thread won.

Revision-based optimistic concurrency gives another useful contract: read revision, update only if it still matches, increment it atomically, then inspect matched_count. A stale writer gets zero matches instead of silently overwriting a newer decision. The database validator's nonnegative stock rule remains a final guard alongside the intentional filter.

The embedded-state example changes remaining and appends an item in one document update. By contrast, independent account-document writes leave [90,100] after an application exception interrupts the transfer. Single-document atomicity does not turn two documents or update_many into one all-or-nothing unit. Reference: [atomicity and transactions](https://www.mongodb.com/docs/v7.0/core/write-operations-atomicity/).

---

## 14.7 Multi-document transactions and a purchase service

When an invariant spans stock, a separate order and a separate outbox document, use a transaction or redesign the boundary with an equally explicit consistency protocol. MongoDB supports transactions on replica sets and sharded clusters; a plain standalone mongod is not sufficient for these transaction examples.

A session is a logical operation context, not the same as pinning one general-purpose socket for all application work. Start a separate session for each independent transaction; ClientSession is not safe for concurrent operations. Pass session= to every operation intended to participate. This implementation uses the explicit API available in PyMongo 4.10.1 rather than newer-version convenience methods.

### Exact service: purchase.py

```python
from datetime import datetime,timezone
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.errors import DuplicateKeyError
from catalog import product_filter,InvalidRequest

class OutOfStock(Exception): pass
class IdempotencyConflict(Exception): pass

def purchase(client,db,*,tenant_id,request_key,sku,quantity,fail_after_stock=False):
    scope=product_filter(tenant_id,sku)
    if type(quantity) is not int or not 1<=quantity<=10: raise InvalidRequest('invalid quantity')
    if type(request_key) is not str or not 1<=len(request_key)<=80: raise InvalidRequest('invalid request key')
    key={'tenant_id':tenant_id,'request_key':request_key}
    order_id=ObjectId()
    created_at=datetime.now(timezone.utc)
    def replay(row):
        if row.get('status')!='reserved': raise RuntimeError('incomplete order state')
        if (row['item']['sku'],row['item']['quantity'])!=(sku,quantity):
            raise IdempotencyConflict('key reused with different payload')
        return {'order_id':str(row['_id']),'total_minor':row['total_minor'],'currency':row['currency'],'replayed':True}
    def operation(session):
        existing=db.orders.find_one(key,session=session)
        if existing: return replay(existing)
        # The unique gate is part of the same transaction as stock and outbox.
        db.orders.insert_one({'_id':order_id,**key,'status':'pending'},session=session)
        product=db.products.find_one_and_update({**scope,'available':{'$gte':quantity}},
            {'$inc':{'available':-quantity,'revision':1}},return_document=ReturnDocument.AFTER,session=session)
        if product is None: raise OutOfStock('stock unavailable')
        if fail_after_stock: raise RuntimeError('injected after stock update')
        total=product['unit_price_minor']*quantity
        db.orders.update_one({'_id':order_id,'tenant_id':tenant_id},{'$set':{
            'status':'reserved','item':{'sku':sku,'quantity':quantity,'unit_price_minor':product['unit_price_minor']},
            'total_minor':total,'currency':product['currency'],'created_at':created_at}},session=session)
        db.outbox.insert_one({'_id':order_id,'tenant_id':tenant_id,'kind':'order.reserved','delivered_at':None},session=session)
        return {'order_id':str(order_id),'total_minor':total,'currency':product['currency'],'replayed':False}
    try:
        with client.start_session() as session:
            return session.with_transaction(operation,read_concern=ReadConcern('snapshot'),write_concern=WriteConcern('majority'),max_commit_time_ms=3000)
    except DuplicateKeyError as error:
        # Outside the aborted transaction. Map only the expected tenant/key gate.
        if error.details.get('keyPattern')!={'tenant_id':1,'request_key':1}: raise
        existing=db.orders.with_options(read_concern=ReadConcern('majority')).find_one(key)
        if existing is None: raise
        return replay(existing)
```

### Trace the transition

```text
validate trusted tenant + key + scalar SKU + integer quantity
start session / with_transaction
  look for committed order by tenant/key -> return original result if replay
  otherwise INSERT pending order with unique tenant/key
  conditional stock find_one_and_update -> trusted price snapshot
  complete order with item/total/currency
  insert outbox intent using order ID
commit -> return result
```

The order ID and creation time are selected once outside the callback so automatic reexecution keeps a stable operation identity. All writes, including the unique gate, carry session=. If stock is unavailable or the injected failure occurs after decrement, the transaction rolls back; no pending claim remains.

A duplicate key can terminate an attempt. The handler catches DuplicateKeyError outside the transaction and recognizes only the expected tenant/request-key keyPattern. It then reads the durable result and checks the payload. An unrelated unique conflict is not silently treated as a replay. Existing completed orders must be retained during the supported retry window; concurrent deletion or alternate malformed writers violate this service's assumptions.

A replay checks the original SKU/quantity and returns the stored total. It works after stock becomes zero because it does not attempt another stock decrement. The price comes from the product returned by the conditional update, not from a client-supplied amount. This is a one-item purchase/reservation example; payment, tax, cancellation, expiration and multi-item checkout are separate design work.

### Real retry and snapshot evidence

The snapshot fixture reads 100, another client commits 200, and the original snapshot reads 100 again. The external read after the transaction sees 200. A different fixture deliberately reads a counter, changes it through another client and then tries to write from the stale transaction. It gets real code **112**, labeled **TransientTransactionError**. with_transaction reexecutes the callback; its reads are 0 then 1, and the final counter is 2.

No mock error is substituted. The callback rereads the decision on its new attempt. Calling a provider or sending an email inside it could repeat an external effect; the database cannot undo that effect when an attempt aborts.

```json
{
  "snapshot_reads": [
    100,
    100
  ],
  "real_transaction_retry": {
    "read_values": [
      0,
      1
    ],
    "failures": [
      {
        "code": 112,
        "transient": true
      }
    ],
    "final_value": 2
  },
  "purchase": {
    "total_minor": 25000,
    "currency": "INR",
    "replayed": false
  },
  "last_unit_race": {
    "stock": 0,
    "orders": 1,
    "outbox": 1,
    "outcome": "one reserved and one unavailable"
  },
  "same_key_race": {
    "stock": 0,
    "orders": 1,
    "outbox": 1,
    "outcome": "one new and one replay"
  }
}
```

The service races use two barrier-started calls against the live replica set. Different keys competing for stock one produce one completed order and one unavailable result. Identical keys produce one new result and one replay of the same ID. Both cases finish with stock zero, one order and one outbox document. Unlike M13's lock-observation fixture, these tests assert concurrent-call outcomes without claiming they observed a specific internal blocking statement.

### Retry scope and time budgets

with_transaction can retry the complete callback for TransientTransactionError and retry commit for UnknownTransactionCommitResult. The installed 4.10.1 helper has its documented 120-second retry window; max_commit_time_ms=3000 bounds a commit command, not the entire service/request. A production HTTP boundary needs a deadline/retry policy compatible with its selected driver API; this fixture is not a three-second end-to-end purchase guarantee. Reference: [version-matched session/transaction API](https://pymongo.readthedocs.io/en/4.10.1/api/pymongo/client_session.html).

Driver retryable writes, a whole-transaction retry and application idempotency are different mechanisms. A driver retry concerns a supported operation/protocol; the tenant/key record preserves the business result across a later request. Do not replace explicit business idempotency with “the driver retries.” The suite injects neither a lost commit acknowledgment nor a primary failover.

The outbox commits a durable intent with the order, not an actual delivered notification. A future dispatcher can crash after sending but before marking delivered, so downstream duplicate handling and reconciliation remain necessary. Revisit [M9: Reliable integrations](/docs/resume-skills/webhooks-payments-reliable-integrations).

---

## 14.8 Indexes: query shape, examined work and tradeoffs

MongoDB normally creates an _id index for a collection. Other access paths need deliberately chosen indexes. An index costs disk/cache space and maintenance on writes; adding one to every field is not a workload model.

The plan fixture asks for the most recent 20 open events for one tenant. Its compound index is:

```python
db.events.create_index(
    [('tenant_id', 1), ('status', 1), ('created_at', -1), ('_id', -1)],
    name='tenant_status_latest',
)
```

Equality fields identify a range; the following fields provide the desired sort and deterministic tie-breaker. The usual Equality–Sort–Range guideline is a starting point, not permission to ignore selectivity, prefixes, range bounds, collation and the actual plan. An index that supports one query need not be good for another. Reference: [compound indexes](https://www.mongodb.com/docs/v7.0/core/indexes/index-types/index-compound/).

### Exact plan/index verifier: verify_indexes.py

```python
from datetime import datetime,timezone,timedelta
from pymongo.errors import OperationFailure,DuplicateKeyError
from db import make_client,database
from checks import Checks,equal,require
checks=Checks('indexes');observed={}

def nodes(value):
    if isinstance(value,dict):
        if 'stage' in value: yield value
        for child in value.values(): yield from nodes(child)
    elif isinstance(value,list):
        for child in value: yield from nodes(child)

def summary(doc):
    stats=doc['executionStats']
    return {'stages':sorted(set(n['stage'] for n in nodes(doc['queryPlanner']['winningPlan']))),
            'returned':stats['nReturned'],'keys_examined':stats['totalKeysExamined'],'documents_examined':stats['totalDocsExamined']}

with make_client() as client:
    db=database(client)
    stamp=datetime(2026,1,1,tzinfo=timezone.utc)
    db.events.insert_many([{'_id':g,'tenant_id':(g%100)+1,'status':'open' if (g//100)%10<2 else 'closed',
        'created_at':stamp+timedelta(seconds=g),'payload':'x'*200} for g in range(1,30001)])
    filt={'tenant_id':7,'status':'open'};ordering={'created_at':-1,'_id':-1}
    command={'find':'events','filter':filt,'sort':ordering,'limit':20}
    before=db.command({'explain':command,'verbosity':'executionStats'})
    expected=list(db.events.find(filt).sort(list(ordering.items())).limit(20))
    checks.check('unindexed selective ordered query naturally scans and sorts',lambda:require({'COLLSCAN','SORT'}<=set(summary(before)['stages'])))
    db.events.create_index([('tenant_id',1),('status',1),('created_at',-1),('_id',-1)],name='tenant_status_latest')
    after=db.command({'explain':command,'verbosity':'executionStats'})
    checks.check('compound index preserves the actual selected documents',lambda:equal(list(db.events.find(filt).sort(list(ordering.items())).limit(20)),expected))
    checks.check('natural compound index plan avoids a blocking sort',lambda:require('IXSCAN' in summary(after)['stages'] and 'SORT' not in summary(after)['stages']))
    checks.check('selective indexed query examines fewer documents in the fixture',lambda:require(summary(after)['documents_examined']<summary(before)['documents_examined']))
    covered=db.command({'explain':{**command,'projection':{'_id':1,'created_at':1}},'verbosity':'executionStats'})
    checks.check('covered indexed projection returns rows without fetching documents',lambda:require(summary(covered)['returned']==20 and summary(covered)['documents_examined']==0))
    broad=db.command({'explain':{'find':'events','filter':{'status':'closed'}},'verbosity':'executionStats'})
    checks.check('broad query naturally uses collection scan despite the selective-query index',lambda:require('COLLSCAN' in summary(broad)['stages']))
    observed.update(fixture_rows=db.events.count_documents({}),matching_rows=db.events.count_documents(filt),before=summary(before),after=summary(after),covered=summary(covered),broad=summary(broad),raw_before=before,raw_after=after,raw_covered=covered,raw_broad=broad)
    def multikey():
        db.tags.insert_many([{'_id':i,'tags':['rare'] if i==1 else ['common']} for i in range(1000)])
        db.tags.create_index('tags')
        plan=db.command({'explain':{'find':'tags','filter':{'tags':'rare'}},'verbosity':'executionStats'})
        require(any(n.get('isMultiKey') is True for n in nodes(plan['queryPlanner']['winningPlan'])))
        equal(plan['executionStats']['nReturned'],1)
    checks.check('array index is multikey and supports a selective member query',multikey)
    def parallel_arrays():
        db.parallel_arrays.insert_one({'_id':1,'a':[1,2],'b':[3,4]})
        try: db.parallel_arrays.create_index([('a',1),('b',1)])
        except OperationFailure as e: equal(e.code,171)
        else: raise AssertionError('parallel-array index accepted')
    checks.check('compound multikey index rejects independent parallel array fields',parallel_arrays)
    def unique_multikey():
        db.unique_tags.create_index('tags',unique=True)
        db.unique_tags.insert_one({'_id':1,'tags':['x','x']})
        try: db.unique_tags.insert_one({'_id':2,'tags':['x']})
        except DuplicateKeyError as e:equal(e.code,11000)
        else:raise AssertionError('duplicate across documents accepted')
        equal(db.unique_tags.find_one({'_id':1})['tags'],['x','x'])
    checks.check('unique multikey index constrains separate documents not repeated array entries within one',unique_multikey)
    def partial():
        db.contacts.create_index('email',unique=True,partialFilterExpression={'email':{'$type':'string'}})
        db.contacts.insert_many([{'_id':1},{'_id':2},{'_id':3,'email':None},{'_id':4,'email':'a@example.test'}])
        try:db.contacts.insert_one({'_id':5,'email':'a@example.test'})
        except DuplicateKeyError as e:equal(e.code,11000)
        else:raise AssertionError('partial duplicate accepted')
        equal(db.contacts.count_documents({}),4)
    checks.check('partial unique index permits excluded missing values and rejects duplicate indexed email',partial)
checks.save(observations=observed,scope='Actual unhinted query plans on 30000 rows plus multikey/partial constraints; not a benchmark')
```

### Actual unhinted plan results

There are **30,000 events** and **60** matches for tenant 7/open. Both before and after queries return the same 20 documents. The ordinary query includes payload and therefore fetches documents. A separate covered projection asks only for _id/created_at, which are in the index.

```json
{
  "fixture_rows": 30000,
  "matching_rows": 60,
  "before": {
    "stages": [
      "COLLSCAN",
      "SORT"
    ],
    "returned": 20,
    "keys_examined": 0,
    "documents_examined": 30000
  },
  "after": {
    "stages": [
      "FETCH",
      "IXSCAN",
      "LIMIT"
    ],
    "returned": 20,
    "keys_examined": 20,
    "documents_examined": 20
  },
  "covered": {
    "stages": [
      "IXSCAN",
      "LIMIT",
      "PROJECTION_COVERED"
    ],
    "returned": 20,
    "keys_examined": 20,
    "documents_examined": 0
  },
  "broad": {
    "stages": [
      "COLLSCAN"
    ],
    "returned": 24000,
    "keys_examined": 0,
    "documents_examined": 30000
  }
}
```

The unindexed path examines all 30,000 documents and sorts. The indexed path examines 20 keys and 20 documents without a blocking SORT. The covered query examines 20 keys and **zero documents**, while still returning 20 results. This last assertion matters: zero documents examined is not meaningful proof of coverage if a query simply returned nothing.

The broad status='closed' query returns **24,000** documents and naturally uses COLLSCAN. The selective-query index does not make a broad scan inherently wrong. All these are natural plans without hint(); the suite separately checks result equivalence.

### Read explain without overclaiming

| Field / stage | Interpretation |
| --- | --- |
| nReturned | Actual returned rows/documents at the relevant execution scope |
| totalDocsExamined | Documents inspected, including those filtered out |
| totalKeysExamined | Index entries inspected; not the same as documents returned |
| COLLSCAN | Collection scan |
| IXSCAN | Index traversal; may still require a FETCH |
| FETCH | Retrieve document data beyond the index keys |
| SORT | Sorting work represented in the plan, potentially avoidable for a matching indexed order |
| Covered projection | Required data can be produced from the index; the fixture verifies zero document fetches |

Read full nested plans when diagnosing filters, bounds and sorting; the summary extracts only stage names and counts. Raw explains, including timings and server/cluster metadata, are preserved. These local fixture counts establish work/access-path differences, not production throughput or a latency multiplier. Reference: [explain results](https://www.mongodb.com/docs/v7.0/reference/explain-results/).

### Multikey, unique and partial behavior

The selective tags fixture naturally uses an index marked isMultiKey. A compound index on independent array fields a and b is rejected with code 171 when the document has both arrays. Do not assume every combination of nested array fields supports the same compound index design.

A unique multikey index prevents the same key appearing in different documents. It does not deduplicate an array inside one document: ['x','x'] is accepted in one fixture document, while another document containing 'x' is rejected. That is different from application-level uniqueness among a parent's child entries. References: [multikey indexes](https://www.mongodb.com/docs/v7.0/core/indexes/index-types/index-multikey/), [unique indexes](https://www.mongodb.com/docs/v7.0/core/index-unique/).

A partial unique email index with a string-type predicate allows documents excluded from that predicate, such as missing/null email, while rejecting duplicate indexed strings. It is not a general “make every missing value unique” switch; the predicate defines which documents participate.

TTL indexes support background expiration. They do not delete at the exact deadline and should not be the authorization check for an expired session/token. Compare expiry during the protected operation. This module does not execute a TTL-deletion experiment. Removing idempotency records also removes replay history; retention must follow the business retry/reconciliation window. Reference: [TTL behavior](https://www.mongodb.com/docs/v7.0/core/index-ttl/).

---

## 14.9 Aggregation: reason about scope and granularity

An aggregation pipeline transforms a stream of documents through stages. $match filters; $unwind expands array elements; $group changes granularity; $sort orders results; $project shapes output; $lookup brings in related collection data. Stage order affects both meaning and work.

The dashboard fixture has two paid tenant-1 orders with totals 500 and 400, a pending tenant-1 order and a large paid tenant-2 order. Its item-level question is: “For this tenant's paid orders, what quantity and revenue belongs to each SKU?” It must filter the intended tenant/status and sum quantity × snapshot price at item granularity.

### Exact reusable pipelines: queries.py

```python
from catalog import InvalidRequest

def revenue_pipeline(tenant_id):
    if type(tenant_id) is not int or tenant_id<1: raise InvalidRequest('invalid tenant')
    return [
        {'$match':{'tenant_id':tenant_id,'status':'paid'}},
        {'$unwind':'$items'},
        {'$group':{'_id':'$items.sku','quantity':{'$sum':'$items.quantity'},
            'revenue_minor':{'$sum':{'$multiply':['$items.quantity','$items.unit_price_minor']}}}},
        {'$sort':{'revenue_minor':-1,'_id':1}},
    ]

def scoped_lookup_pipeline(tenant_id):
    if type(tenant_id) is not int or tenant_id<1: raise InvalidRequest('invalid tenant')
    return [
        {'$match':{'tenant_id':tenant_id}},
        {'$lookup':{'from':'products','let':{'wanted_sku':'$sku','wanted_tenant':'$tenant_id'},
            'pipeline':[{'$match':{'$expr':{'$and':[{'$eq':['$sku','$$wanted_sku']},
                                                     {'$eq':['$tenant_id','$$wanted_tenant']}]}}}],
            'as':'product'}},
    ]
```

### The unwind double-counting trap

After unwinding items, an order with two items appears twice. Summing its **order-level** total at that stage counts it twice. The fixture's wrong calculation returns **1400**, while summing once per order returns **900**. The item-level pipeline instead sums each item's quantity × unit price and returns A: quantity 6/revenue 600, B: quantity 1/revenue 300.

Before adding a group, name what one input document represents and what one output document will represent. “Group by day” alone is incomplete if earlier stages changed one order into many item rows. Mixed currencies also need an explicit grouping/conversion policy; do not add INR and USD minor-unit amounts into one unspecified revenue number.

### A lookup can cross the tenant boundary

The fixture's outer collection has one tenant-1 reference to sku basic. A $lookup matching only SKU joins both tenant-1 and tenant-2 products, even though the outer pipeline already matched tenant 1. The guarded pipeline carries both wanted_sku and wanted_tenant into the foreign match, and returns only one product.

A lookup returns related documents in an array; the application must define whether zero, one or many matches are allowed. Here the tenant/SKU unique index supports the intended one-product relationship, but it does not automatically supply the missing tenant predicate. A lookup is also not a foreign-key constraint. Reference: [$lookup](https://www.mongodb.com/docs/v7.0/reference/operator/aggregation/lookup/).

```json
{
  "dotted_array_ids": [
    "cross",
    "same"
  ],
  "elem_match_ids": [
    "same"
  ],
  "dashboard": [
    {
      "_id": "A",
      "quantity": 6,
      "revenue_minor": 600
    },
    {
      "_id": "B",
      "quantity": 1,
      "revenue_minor": 300
    }
  ],
  "unwind_total_trap": {
    "wrong": 1400,
    "correct": 900
  },
  "cursor_ids": [
    6,
    5,
    4,
    3,
    2,
    1
  ]
}
```

Filter early when semantics permit, project what the API needs and inspect plans for expensive pipelines. An early tenant $match does not remove the need to scope later joins. Repeated dashboards may justify precomputed summaries later, but those introduce freshness, update and reconciliation rules; they are not implemented here.

---

## 14.10 Pagination, cursors, connections and budgets

A large skip/offset requires advancing past earlier results and can shift when new records arrive. Keyset pagination continues after a stable tuple. For descending created_at/_id ordering, the next page selects earlier timestamps or the same timestamp with a smaller ID, while retaining tenant_id.

### Exact pagination helper: pagination.py

```python
from datetime import datetime
from bson import ObjectId
from catalog import InvalidRequest

ORDER=[('created_at',-1),('_id',-1)]

def page_filter(tenant_id,*,after=None):
    if type(tenant_id) is not int or tenant_id<1: raise InvalidRequest('invalid tenant')
    result={'tenant_id':tenant_id}
    if after is not None:
        stamp,identifier=after
        if not isinstance(stamp,datetime) or stamp.tzinfo is None or not isinstance(identifier,ObjectId):
            raise InvalidRequest('invalid cursor tuple')
        result['$or']=[{'created_at':{'$lt':stamp}}, {'created_at':stamp,'_id':{'$lt':identifier}}]
    return result

def page(collection,tenant_id,*,after=None,limit=20):
    if type(limit) is not int or not 1<=limit<=100: raise InvalidRequest('invalid limit')
    return list(collection.find(page_filter(tenant_id,after=after)).sort(ORDER).limit(limit))
```

Six same-timestamp fixture documents paginate as IDs **6,5,4,3,2,1**, without omission or duplication. A tenant-2 document is excluded. After the first page, a newly inserted later item does not shift this continuation: the next page still returns 4,3.

This is not a snapshot across all page requests. Updates/deletes, mutable sort fields and other insertion positions need a declared contract. A transport cursor must be validated, carry the correct sort/filter context and obey authorization; the example accepts a typed internal tuple and does not implement a signed HTTP cursor token.

### Exact connection configuration: db.py

```python
import os
from pymongo import MongoClient
from bson.codec_options import CodecOptions
from datetime import timezone

CODEC=CodecOptions(tz_aware=True,tzinfo=timezone.utc)

def make_client(*,listeners=None,max_pool_size=4,wait_ms=500):
    port=int(os.environ['M14_PORT'])
    if not 1024<=port<=65535 or port==27017: raise RuntimeError('Explicit non-default fixture port required')
    return MongoClient(f'mongodb://127.0.0.1:{port}/?directConnection=true&replicaSet=m14_fixture',
        appname='placement-m14',maxPoolSize=max_pool_size,waitQueueTimeoutMS=wait_ms,
        serverSelectionTimeoutMS=3000,connectTimeoutMS=1000,socketTimeoutMS=5000,
        event_listeners=listeners or [])

def database(client):
    name=os.environ['M14_DATABASE']
    if not name.startswith('m14_'): raise RuntimeError('Fixture database prefix required')
    return client.get_database(name,codec_options=CODEC)
```

Create and reuse an appropriate MongoClient per process. PyMongo manages pools per server plus topology monitoring connections; maxPoolSize is not an entire deployment's socket count. More web workers/replicas create more clients/pools, and reading from additional members can use their pools too. Bound application concurrency as well as acquisition waiting.

The client is thread-safe; an individual ClientSession is not for concurrent use. The service concurrency tests share a client while starting separate sessions. Forked children need their own clients; do not inherit a parent's active driver client as an independent connection pool. Reference: [PyMongo client/pool FAQ](https://pymongo.readthedocs.io/en/4.10.1/faq.html).

### Real cursor and pool evidence

The command listener observes no find when a cursor is merely constructed. Iterating five rows with batch size two issues **one find and two getMore commands**. Closing a still-open cursor sends killCursors. Returning a cursor object does not mean its database work is finished or that its exceptions have already occurred.

For pool pressure, the fixture holds one actual command after checkout through a controlled listener gate. With maxPoolSize=1, another borrower gets WaitQueueTimeoutError; after the first is released, queries work again. Closing the client rejects subsequent operations. These are driver behavior checks, not a throughput benchmark or a recommendation to block production command listeners.

```json
{
  "cursor_commands": {
    "find": 1,
    "getMore": 2
  },
  "exhaustion": "WaitQueueTimeoutError",
  "pool_max": 1
}
```

| Budget | Which phase it concerns |
| --- | --- |
| serverSelectionTimeoutMS | Finding a suitable server |
| connectTimeoutMS | Establishing a network connection |
| waitQueueTimeoutMS | Waiting for a pooled connection |
| socketTimeoutMS | Waiting for socket I/O during an operation |
| Server maxTimeMS | Server execution budget for supported commands |
| Application deadline | Whole request, retries, cleanup and response budget |

These settings are not interchangeable. The fixture's settings prevent tests from waiting indefinitely at several boundaries, while its child-process deadlines bound each test group. Production deadlines/retry policies are a separate integration decision. Avoid list(cursor) for an unbounded export; stream/process bounded batches and own cursor cleanup, response cancellation and backpressure explicitly.

---

## 14.11 Architectural understanding: build a catalog and order dashboard

Start with requirements: tenant-specific catalog data with variable attributes, a bounded-stock purchase, stable retry results, preserved purchased prices and a paid-order dashboard. Choose explicit document boundaries and consistency rules before selecting driver method names.

```text
HTTP ingress -> authentication/tenant authorization -> validated DTO
  -> catalog query / purchase service / dashboard query
  -> shared process MongoClient and bounded driver pools
  -> products: live stock, price, attributes
  -> orders: tenant/key + purchased item snapshot
  -> outbox: durable event intent

proposed worker -> bounded outbox claim -> downstream effect -> delivery record
proposed ingestion -> validated batches -> stable source keys -> checkpoints
```

### Build path

**Step 1: define the aggregate boundaries.** Keep bounded attributes/tags with products. Keep a purchased item snapshot with its order. A growing order history belongs in separate documents. Define whether stock means immediate purchase or a temporary hold; this service models a reserved purchase without expiry/release behavior.

**Step 2: encode stable identities.** Create tenant/SKU and tenant/request-key unique indexes. Add product validation for types/ranges. State which paths can write orders and how malformed direct writes are prevented. Plan compatible schema evolution rather than assuming old documents all have new fields.

**Step 3: implement the write transition.** Use one transaction for the pending unique gate, conditional stock update, completed order and outbox intent. Supply session= consistently. A single conditional document update suffices for stock alone; the multi-document business invariant explains the transaction.

**Step 4: add the API boundary.** Authenticate, derive the tenant, validate scalar values and map known domain outcomes. Operator objects, arbitrary collection names and user-supplied pipeline stages should not be copied into server query structure. The HTTP adapter is proposed work; the verified implementation is the database service.

**Step 5: verify negative and overlapping paths.** Exercise duplicate payload changes, insufficient stock, injected failure and concurrent callers. Keep state assertions independent of which thread wins. Preserve replay records through the agreed retry window.

**Step 6: implement reads around actual access patterns.** Use scoped filters and stable cursors for lists. Keep tenant scope on foreign lookup stages. For dashboards, choose item versus order granularity and currency grouping deliberately. Inspect natural plans on representative data and keep result equivalence checks alongside plan changes.

**Step 7: add ingestion and asynchronous effects.** Imports need source-key uniqueness, malformed-row handling, bounded batches and checkpoints. Outbox dispatch needs ownership, deadlines, duplicate-tolerant downstream work and crash reconciliation. M15 will develop these concepts; current code does not deliver outbox messages or run a long-lived import worker.

**Step 8: deploy and observe.** Select supported versions, authenticated least-privilege database access, verified TLS, topology-aware URI configuration, monitoring and backup/restore procedures. Watch pool wait, server selection, examined work, conflicts/retries, rejected documents and dispatcher lag. The test's unauthenticated single-node loopback setup is deliberately an isolated harness, not a remote deployment recipe.

### Failure reasoning

| Scenario | Verified behavior / design response |
| --- | --- |
| Negative/string/boolean stock | Product server validator rejects the write |
| Operator-shaped SKU | Query helper rejects the input structure |
| Stale absolute stock replacement | Can lose a prior deduction; use conditional relative/revision update |
| One last unit, distinct request keys | One purchase succeeds, one is unavailable |
| Same key concurrently | One completed order and one replay |
| Changed quantity on same key | Idempotency conflict; no extra stock deduction |
| Failure after decrement | Transaction rolls stock/order/outbox back |
| Ordered import batch hits a bad row | Earlier row remains; later row is skipped |
| Lookup only matches SKU | Can return another tenant's product |
| Primary/network failure or ambiguous commit | Requires recovery/reconciliation policy; not fault-injected here |
| Outbox worker crashes after sending | Duplicate downstream effect possible; dispatcher not implemented here |

---

## 14.12 Consistency, scale and relational tradeoffs

Read preference chooses **where** a read can run. Read concern describes its visibility/consistency guarantees. Write concern describes the required acknowledgment for a write. A secondary read can be stale; choosing majority write concern does not automatically make every subsequent arbitrary read the newest possible read.

This purchase uses snapshot read concern and majority commit acknowledgment on one member. It proves the requested local transaction semantics, not survival of a node failure or a globally serializable business workflow. References: [read concern](https://www.mongodb.com/docs/v7.0/reference/read-concern/), [write concern](https://www.mongodb.com/docs/v7.0/reference/write-concern/).

Replication maintains copies and supports availability/election behavior; sharding distributes data. Choosing a shard key affects routing, distribution and hot spots. Tenant scoping, uniqueness and transaction requirements must be reviewed against that choice. Sharding cannot eliminate contention if every purchase still updates the same popular product document. No sharded deployment or multi-member failover is provisioned here. Reference: [sharding](https://www.mongodb.com/docs/v7.0/sharding/).

### Schema evolution still exists

Add a schema_version where multiple representations genuinely need explicit handling. Deploy compatible readers/writers, backfill in bounded batches and tighten validators only after understanding existing documents and alternate writers. Defaults, missing fields and indexes remain part of the deployed contract. Flexible schema changes the tooling; it does not remove migration planning.

| Requirement | Relational / PostgreSQL considerations | MongoDB considerations |
| --- | --- | --- |
| Rich related entities and arbitrary joins | Tables, foreign keys, constraints and joins are a natural fit | References/lookups need explicit relationship/lifecycle rules |
| Bounded object read/write as one unit | Model with related rows or suitable JSON fields | Embedded document can be one read/atomic write boundary |
| Variable category attributes | JSONB or typed relational structures depending on queries | Nested fields are natural, but need validation/index planning |
| Multi-entity atomic change | Transaction boundary across rows/tables | Transaction boundary across documents/collections on supported topology |
| Historical purchase snapshot | Preserve snapshot fields in order/line rows | Preserve embedded item snapshot in the order |
| Efficient queries | Query shape, data distribution, indexes and plans matter | The same discipline applies; document storage is not automatic speed |

Avoid “MongoDB has no joins,” “NoSQL means no transactions,” “SQL cannot store JSON” and “MongoDB scales automatically.” State the workload, integrity requirements, operating environment and team's ability to own the consistency rules. The simpler system is the one whose required guarantees can be explained and verified.

### Connect to your resume

For a MongoDB project, name a real document shape and why its boundaries were chosen. Explain one important compound index, one aggregation stage and how tenant scope reaches a lookup. Describe actual duplicate/partial-failure handling rather than claiming an ODM or flexible schema solved it.

An ODM such as Mongoose adds application conventions, casting and validation around the Node driver; it does not replace the database's atomicity or server-side indexes. This chapter runs PyMongo and does not claim a Mongoose validation/query was exercised. Use the local checks as practice evidence, not invented production traffic or a measured latency improvement.

### Must remember

1. BSON types matter: an ObjectId is different from its string; dates have millisecond precision.
2. Flexible schema still needs a model, validation and compatible evolution.
3. Embed bounded related data; reference independently growing/shared entities.
4. Construct approved query structure from validated input and trusted tenant context.
5. $elemMatch binds conditions to one array element; separate dotted predicates may not.
6. Atomic document writes do not fix stale read-then-set decisions or make batches atomic.
7. Transactions require the correct topology and session participation on every intended operation.
8. A callback may rerun; preserve identity and keep external side effects outside it.
9. Inspect actual keys/documents examined and result equivalence before making index claims.
10. $unwind changes granularity; later $lookup needs its own tenant scope.
11. MongoClient reuses per-server pools; cursors are lazy and need bounded consumption/cleanup.
12. Idempotency retention, outbox delivery and ambiguous outcomes are business protocols.

---

## 14.13 Interview questions and follow-ups

These questions are selected for foundational coverage and common backend discussion patterns. They are not measured company-frequency rankings. Give a short answer first, then use an example or failure case.

**Q1. What is MongoDB?**

A document database server storing BSON documents in collections, with query, index, aggregation and transaction capabilities. The driver, shell and ODM are separate clients/abstractions. A backend still owns authorization, input validation and domain transitions.

*Follow-up:* Where does MongoClient sit in an HTTP request trace?

**Q2. What is BSON, and how is it different from JSON?**

BSON is the database's binary document representation with additional types such as ObjectId, dates and Decimal128. Ordinary JSON serialization may not preserve those types; use an intentional API representation or Extended JSON when lossless type transport is required.

*Follow-up:* Why didn't a string _id query find the ObjectId document?

**Q3. What does an ObjectId tell you?**

It is a 12-byte generated identifier with a timestamp component and other generation data. It does not prove ownership, provide a secret or guarantee strict global creation ordering. A list API should define its explicit sort and tie-breaker.

*Follow-up:* Why use created_at plus _id for the feed?

**Q4. Does MongoDB have no schema?**

Documents are flexible by default, but applications still assume shapes/types. Server validators can reject invalid writes. This catalog requires nonnegative integer stock and typed tenant/price/currency fields while allowing flexible attributes.

*Follow-up:* Which assumptions remain outside the product validator?

**Q5. When should you embed related data?**

When it is bounded, usually accessed with the parent and benefits from the same lifecycle/atomic document boundary. The order's purchased item/price is an intentional embedded snapshot. An unbounded lifetime order history should be separate documents.

*Follow-up:* What happens when the embedded set keeps growing?

**Q6. When should you reference instead?**

When the related entity has independent queries/lifecycle, is shared or grows separately. References require a defined consistency and deletion policy; simply storing product_id does not create a foreign key. Choose the boundary from requirements, not a slogan about joins.

*Follow-up:* How would you prevent dangling or cross-tenant relationships?

**Q7. How do you prevent NoSQL query injection?**

Build allowed filters/operators on the server and validate input types. Reject an operator-shaped object where a scalar SKU is expected. Keep collection selection, sorting and pipeline structure controlled, and derive tenant scope from authorization rather than request-provided identity.

*Follow-up:* Why does a dictionary containing $ne differ from a literal string?

**Q8. Is collection access enough for multi-tenancy?**

No. The fixture can read both tenants with an unscoped query. Tenant must participate in relevant identities, reads, writes, pagination and foreign lookup predicates. Database access permissions do not establish which application's user owns a row/document.

*Follow-up:* How did an outer tenant match still leak a foreign product?

**Q9. How do update_one and replace_one differ?**

An operator update modifies selected fields and can preserve siblings. Replacement substitutes the document body subject to identifier rules. Assigning an entire embedded object also replaces its previous subfields, unlike a dotted $set on one subfield.

*Follow-up:* Distinguish matched_count and modified_count.

**Q10. Does upsert guarantee one logical record under concurrency?**

Not by itself. It chooses insert or update from a filter; a stable identity and suitable unique index protect concurrent uniqueness. The sequential example shows inserted then matched results, without claiming it alone proves concurrent ingestion correctness.

*Follow-up:* What belongs in $setOnInsert versus $set?

**Q11. How do null and missing fields differ?**

Equality to null can match explicit null and missing fields. $exists:false isolates missing fields; $type can select BSON null. A normal single-field unique index gives missing/null a shared null key; a partial index can deliberately exclude certain documents.

*Follow-up:* Why does a required-field validator matter alongside uniqueness?

**Q12. Why use $elemMatch?**

To require one array element to satisfy all specified conditions. Separate dotted predicates can be satisfied by different elements; the red/out-of-stock plus blue/in-stock product incorrectly matches a naive red-and-stock query.

*Follow-up:* What did the two fixture queries return?

**Q13. What does single-document atomicity mean?**

One write to a document, including several embedded fields, applies atomically. It does not combine separate commands/documents into one unit or infer that an absolute replacement came from a stale read. Put transition conditions in the update filter.

*Follow-up:* Why can two read-then-$set calls still lose a deduction?

**Q14. How would you reserve the last item safely?**

Use a filter carrying trusted tenant/SKU and available >= quantity, with a relative $inc decrement in the same operation. Inspect its match/returned document. The fixture yields one successful update and one no-match when stock is one.

*Follow-up:* What additional boundary is needed for a separate order and outbox?

**Q15. How does optimistic concurrency work?**

Read a revision, include that revision in the update filter and increment it with the successful state change. A stale writer receives zero matches and can reread or report conflict. A revision is clearer than comparing a mutable business value that might change back.

*Follow-up:* Where do you distinguish conflict from an unauthorized/missing object?

**Q16. Is update_many or insert_many an all-or-nothing transaction?**

No. Atomicity is per document unless a transaction supplies the larger boundary. An ordered batch can commit earlier documents and stop on a later error; the fixture inserts one valid product, rejects the next and never reaches the third.

*Follow-up:* How should an import resume safely after partial progress?

**Q17. When do you need a MongoDB transaction?**

When the required atomic rule spans multiple documents/collections and embedding does not provide the right boundary. The purchase needs stock, order and outbox together. Use supported replica/sharded topology and pass the transaction's session to each operation.

*Follow-up:* What happens if one operation forgets session=?

**Q18. Can a transaction callback execute twice?**

Yes. with_transaction may reexecute it for a transient transaction error. The real conflict fixture reads 0, gets code 112, retries and reads 1. Put the complete database decision inside it and keep nonrollbackable external effects outside.

*Follow-up:* Which identity values are created before the purchase callback?

**Q19. What if commit's result is unknown?**

A lost acknowledgment is not proof the server rolled back. The driver distinguishes commit retry from whole-transaction retry; the business operation also needs retained idempotency results and reconciliation. This suite does not inject a lost commit acknowledgment.

*Follow-up:* Why doesn't retrying an email behave like retrying a database commit?

**Q20. What does max_commit_time_ms bound?**

A commit command's server budget, not the whole request or all retries. The selected driver's with_transaction helper has its own documented retry window. Choose an API/deadline policy that matches the service's response budget rather than adding timeout values together blindly.

*Follow-up:* Which timeout applies while waiting for a pool connection?

**Q21. How do compound indexes work?**

They order index keys by the specified fields, supporting compatible prefixes, filters and sorts. Begin with the important query shape and measure it. The example uses tenant/status equality followed by created_at/_id order and avoids a blocking sort.

*Follow-up:* Why can the broad closed-events query still scan the collection?

**Q22. What are multikey indexes?**

Indexes on array values that can store multiple keys for a document. They support member queries but have compound-array restrictions and maintenance costs. A unique multikey index prevents conflicts between documents; it does not deduplicate repeated entries within one array.

*Follow-up:* Why was the independent a/b array compound index rejected?

**Q23. What is a covered query?**

The index can provide all required query/output information without fetching documents. The fixture returns 20 rows, examines 20 keys and zero documents. Inspect both actual results and fetch work; zero fetches alone could describe an empty result.

*Follow-up:* Why does asking for payload require a fetch in the ordinary query?

**Q24. What should you inspect in explain?**

The winning execution structure, index bounds, blocking sort, returned count, keys examined and documents examined. Compare results and work before/after changes. Local timings are evidence about that run, not a production latency claim.

*Follow-up:* What might a high examined-to-returned ratio suggest?

**Q25. How does aggregation differ from find?**

Aggregation composes transformations such as match, unwind, group and lookup. Each stage can change shape or granularity. It supports dashboards but requires deliberate tenant/currency scope and attention to work, just like ordinary queries.

*Follow-up:* Why did summing order totals after unwind yield 1400 instead of 900?

**Q26. How do you make a lookup tenant-safe?**

Scope both the outer documents and the foreign match. The guarded fixture passes wanted tenant/SKU into a lookup pipeline; SKU alone matches both tenants' basic product. A join operator does not infer the authorization relationship.

*Follow-up:* What should the service do with zero or several joined products?

**Q27. Why prefer keyset pagination for some large feeds?**

It continues after a stable ordered tuple rather than skipping an ever-growing prefix. Include a tie-breaker and preserve filters/tenant scope. It is not automatically a snapshot across requests; mutable sort fields and concurrent changes need a defined contract.

*Follow-up:* Why didn't a newer insert shift the fixture's second page?

**Q28. How should MongoClient and cursors be managed?**

Reuse an appropriate client per process; it owns per-server pools and monitoring. Keep sessions sequential. Cursors execute lazily and may issue getMore during iteration; consume bounded data and close abandoned cursors. Close the client at lifecycle shutdown.

*Follow-up:* What did the batch-size-two command listener observe?

**Q29. Are replication and sharding the same?**

Replication maintains copies and supports availability/elections. Sharding distributes data and introduces shard-key/routing choices. Neither removes query design, hot-document contention or integrity work. The single-member fixture proves neither multi-node failover nor sharded operation.

*Follow-up:* Which query/uniqueness rules would constrain a shard key?

**Q30. Why choose MongoDB instead of PostgreSQL?**

Explain the actual bounded document reads/writes, flexible attributes and intended snapshots, then compare relational constraints/joins, multi-entity consistency and operational needs. Avoid universal speed/scale claims. Either engine requires good queries, explicit authorization and tested failure boundaries.

*Follow-up:* Which requirement would make you reconsider the document model?

---

## 14.14 Practice tasks and checkpoints

1. **Trace the backend boundary.** Draw request, trusted tenant, query builder, client pool, server and response serialization. *Checkpoint:* distinguish client, session, connection, collection and document.
2. **Defend an embedded model.** Compare product attributes, order item snapshots and unbounded order history. *Checkpoint:* state access/lifecycle/size rules for each boundary.
3. **Exercise schema/type failures.** Reproduce negative/string/boolean stock rejection and ObjectId/string mismatch. *Checkpoint:* distinguish application validation, server validation and BSON adaptation.
4. **Find an array bug.** Run separate dotted predicates and $elemMatch against the two variant documents. *Checkpoint:* explain why cross matches only the dotted version.
5. **Reproduce stock races.** Compare stale $set, relative $inc and the conditional last-unit transition. *Checkpoint:* assert final state without assuming which thread wins.
6. **Trace a real retry.** Read the counter-conflict fixture and explain both callback reads and error label. *Checkpoint:* keep all decision reads in the transaction and external effects out.
7. **Read the plan change.** Identify the ordinary versus covered projection and broad query. *Checkpoint:* compare actual documents/results and examined work without reporting a production speedup.
8. **Audit a dashboard.** Explain order/item granularity, the 1400/900 trap and tenant scope inside lookup. *Checkpoint:* design a currency-aware grouped result before adding more stages.
9. **Extend a list API.** Design cursor transport validation and test deletion/mutable-sort behavior between pages. *Checkpoint:* state the pagination consistency contract; the current helper uses only an internal typed tuple.
10. **Design import/dispatch recovery.** Specify stable source keys, partial-batch checkpoints, outbox ownership and a send-before-mark crash. *Checkpoint:* define restart/replay rules before writing a worker; current code implements neither long-lived worker.

### Exit checklist

- [ ] I can explain BSON, documents, collections, clients and sessions.
- [ ] I can justify embedding/references using access, lifecycle and growth.
- [ ] I can distinguish application validation from server validators/indexes.
- [ ] I can construct scoped filters without accepting operator-shaped input.
- [ ] I can explain null/missing, projection and replacement boundaries.
- [ ] I can demonstrate $elemMatch and multikey behavior.
- [ ] I can distinguish atomic document writes from stale decisions and batch partial progress.
- [ ] I can trace purchase replay, conflicts, rollback and concurrent outcomes.
- [ ] I can explain callback retries and the selected driver's timeout scope.
- [ ] I can interpret index/covered-query work and aggregation granularity.
- [ ] I can preserve tenant scope in pagination and foreign lookups.
- [ ] I can state the fixture's topology/security/recovery limits without inventing deployment experience.

These boxes track your study progress; authoring and passing tests do not check them for you.

---

## Sources and verification map

Research refreshed on **14 October 2026**. Server-specific references use MongoDB 7.0; PyMongo API/retry behavior uses the executed 4.10.1 documentation.

| Topic | Primary reference |
| --- | --- |
| Document modeling / embedding | [Data modeling](https://www.mongodb.com/docs/manual/data-modeling/), [embedding](https://www.mongodb.com/docs/manual/data-modeling/embedding/) |
| BSON and schema rules | [BSON types](https://www.mongodb.com/docs/v7.0/reference/bson-types/), [schema validation](https://www.mongodb.com/docs/v7.0/core/schema-validation/) |
| Atomicity and arrays | [Atomic operations/transactions](https://www.mongodb.com/docs/v7.0/core/write-operations-atomicity/), [$elemMatch](https://www.mongodb.com/docs/v7.0/reference/operator/query/elemmatch/) |
| Index design | [Compound](https://www.mongodb.com/docs/v7.0/core/indexes/index-types/index-compound/), [multikey](https://www.mongodb.com/docs/v7.0/core/indexes/index-types/index-multikey/), [unique](https://www.mongodb.com/docs/v7.0/core/index-unique/) |
| Plans and expiry | [Explain results](https://www.mongodb.com/docs/v7.0/reference/explain-results/), [TTL](https://www.mongodb.com/docs/v7.0/core/index-ttl/) |
| Joining documents | [$lookup](https://www.mongodb.com/docs/v7.0/reference/operator/aggregation/lookup/) |
| Driver lifecycle / transactions | [PyMongo 4.10.1 FAQ](https://pymongo.readthedocs.io/en/4.10.1/faq.html), [session API](https://pymongo.readthedocs.io/en/4.10.1/api/pymongo/client_session.html) |
| Consistency and distribution | [Read concern](https://www.mongodb.com/docs/v7.0/reference/read-concern/), [write concern](https://www.mongodb.com/docs/v7.0/reference/write-concern/), [sharding](https://www.mongodb.com/docs/v7.0/sharding/) |

### Verification map

Implementation and artifacts are under examples/resume-skills/module-14-mongodb/.

| Group | Named checks | Actual boundary |
| --- | --- | --- |
| Core | 17 | BSON/Extended JSON, validators, compound uniqueness, query input, null/missing, CRUD and partial batches |
| Queries | 12 | Arrays, projection, aggregation granularity, tenant-scoped lookup and keyset continuation |
| Indexes | 10 | Natural 30,000-document plans, result equivalence, coverage, multikey/parallel-array/partial uniqueness |
| Atomic | 6 | Stale replacements, concurrent relative/conditional writes, revisions and separate-document failure |
| Transactions | 15 | Commit/rollback/snapshot, real transient retry, purchase replay/rollback and concurrent outcomes |
| Pool | 5 | Actual commands, cursor batches/close, real checked-out pool pressure, recovery and closed client |
| Total | **65** | Named checks, some with multiple assertions |

Implementation: cluster.py, db.py, catalog.py, purchase.py, queries.py and pagination.py. Test support: checks.py. Execution: verify.py plus six verify-group files. Evidence: group JSON, verification-results.json, verification-output.txt, cluster-results.json and mongodb-server-output.txt. Dependency, chapter/source and website validation artifacts are recorded alongside them.

Each group gets a fresh database in the runner-owned replica set. The dbPath/port are checked before use; the existing Windows service is untouched. The owned listener stops and validated temporary directory is removed after children finish. Expected rejection/error evidence is distinct from a suite failure.

No application authentication, database role enforcement, remote TLS, Atlas connection, HTTP endpoint, multi-member failover, sharding, crash/power-loss/backup restoration, provider payment or outbox delivery is verified. TTL behavior and the production architecture extensions are documented/design material, not executed examples. Query timings are not a load benchmark.

---

## Next

Continue to [M15: Caching, Background Jobs and Data Ingestion](/docs/resume-skills/caching-background-jobs-data-ingestion) to connect database access to cache freshness, bounded asynchronous work, retries, idempotent workers and restartable imports.

Revisit [M13: PostgreSQL](/docs/resume-skills/postgresql-backend) for relational constraints/transaction comparisons, [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) for trusted tenant scope and [M9: Reliable integrations](/docs/resume-skills/webhooks-payments-reliable-integrations) for replay/reconciliation. The [master roadmap](/docs/resume-skills) shows the remaining sections.
