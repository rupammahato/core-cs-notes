from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.errors import OperationFailure
from db import make_client,database
from catalog import prepare,InvalidRequest
from purchase import purchase,OutOfStock,IdempotencyConflict
from checks import Checks,equal,require
checks=Checks('transactions');observed={}
with make_client() as client,make_client() as other:
    db=database(client);other_db=database(other);prepare(db)
    def transfer():
        db.accounts.insert_many([{'_id':1,'balance':100},{'_id':2,'balance':100}])
        with client.start_session() as s:
            with s.start_transaction():
                db.accounts.update_one({'_id':1},{'$inc':{'balance':-10}},session=s)
                db.accounts.update_one({'_id':2},{'$inc':{'balance':10}},session=s)
        equal([r['balance'] for r in db.accounts.find({}).sort('_id')],[90,110])
    checks.check('multi-document transaction commits the complete transfer',transfer)
    def rollback():
        try:
            with client.start_session() as s:
                with s.start_transaction():
                    db.accounts.update_one({'_id':1},{'$inc':{'balance':-10}},session=s)
                    raise ValueError('injected before credit')
        except ValueError:pass
        equal([r['balance'] for r in db.accounts.find({}).sort('_id')],[90,110])
    checks.check('transaction exception rolls back its partial transfer',rollback)
    def snapshot():
        db.snapshots.insert_one({'_id':1,'value':100})
        with client.start_session() as s:
            with s.start_transaction(read_concern=ReadConcern('snapshot')):
                first=db.snapshots.find_one({'_id':1},session=s)['value']
                other_db.snapshots.update_one({'_id':1},{'$set':{'value':200}})
                second=db.snapshots.find_one({'_id':1},session=s)['value']
        equal((first,second),(100,100));equal(db.snapshots.find_one({'_id':1})['value'],200)
        observed['snapshot_reads']=[first,second]
    checks.check('snapshot transaction retains its read view after another session commits',snapshot)
    def conflict_retry():
        db.counters.insert_one({'_id':1,'value':0});attempts=[];errors=[]
        def callback(s):
            value=db.counters.find_one({'_id':1},session=s)['value'];attempts.append(value)
            if len(attempts)==1: other_db.counters.update_one({'_id':1},{'$inc':{'value':1}})
            try:db.counters.update_one({'_id':1},{'$inc':{'value':1}},session=s)
            except OperationFailure as e:
                errors.append({'code':e.code,'transient':e.has_error_label('TransientTransactionError')});raise
            return value
        with client.start_session() as s:
            final=s.with_transaction(callback,read_concern=ReadConcern('snapshot'),write_concern=WriteConcern('majority'))
        equal(attempts,[0,1]);equal(final,1);equal(db.counters.find_one({'_id':1})['value'],2)
        equal(errors,[{'code':112,'transient':True}]);observed['real_transaction_retry']={'read_values':attempts,'failures':errors,'final_value':2}
    checks.check('real transient write conflict causes callback retry and fresh reads',conflict_retry)
    key={'tenant_id':1,'sku':'basic'}
    def buy(**changes):return purchase(client,db,**{'tenant_id':1,'request_key':'purchase-1','sku':'basic','quantity':2,**changes})
    result={}
    def successful():
        result.update(buy());equal(result['total_minor'],25000);equal(result['currency'],'INR');equal(result['replayed'],False)
        equal(db.products.find_one(key)['available'],8);equal(db.orders.count_documents({}),1);equal(db.outbox.count_documents({}),1)
        row=db.orders.find_one({'tenant_id':1,'request_key':'purchase-1'});equal(row['item']['unit_price_minor'],12500)
        observed['purchase']={k:result[k] for k in ('total_minor','currency','replayed')}
    checks.check('purchase commits trusted price snapshot stock order and outbox together',successful)
    def replay():
        replayed=buy();equal(replayed['order_id'],result['order_id']);equal(replayed['replayed'],True)
        equal(db.products.find_one(key)['available'],8);equal(db.outbox.count_documents({}),1)
    checks.check('same-key replay returns original result without repeating stock or outbox',replay)
    def changed():
        try:buy(quantity=1)
        except IdempotencyConflict:pass
        else:raise AssertionError('changed payload accepted')
        equal(db.products.find_one(key)['available'],8)
    checks.check('same key with changed quantity is a conflict',changed)
    def tenant():
        second=buy(tenant_id=2,quantity=1);equal(second['total_minor'],25000)
        equal(db.products.find_one({'tenant_id':2,'sku':'basic'})['available'],9)
        equal(db.products.find_one(key)['available'],8)
    checks.check('same key and SKU in another tenant form an independent operation',tenant)
    def invalid():
        for quantity in (True,'1',1.5,0,11,None):
            try:buy(request_key='invalid',quantity=quantity)
            except InvalidRequest:pass
            else:raise AssertionError('invalid accepted')
        equal(db.orders.count_documents({'request_key':'invalid'}),0)
    checks.check('invalid quantity shapes and bounds fail before writes',invalid)
    def insufficient():
        try:buy(request_key='later',quantity=10)
        except OutOfStock:pass
        else:raise AssertionError('insufficient accepted')
        equal(db.orders.count_documents({'request_key':'later'}),0);equal(db.products.find_one(key)['available'],8)
    checks.check('unavailable stock rolls back the unique pending gate',insufficient)
    def injected():
        try:buy(request_key='injected',fail_after_stock=True)
        except RuntimeError as e:require('injected' in str(e))
        else:raise AssertionError('failure missing')
        equal(db.products.find_one(key)['available'],8);equal(db.orders.count_documents({'request_key':'injected'}),0)
        equal(db.outbox.count_documents({}),2)
    checks.check('failure after decrement rolls back stock order and outbox',injected)
    def race(same_key):
        db.orders.delete_many({});db.outbox.delete_many({});db.products.update_one(key,{'$set':{'available':1}})
        gate=Barrier(2)
        def worker(i):
            gate.wait(timeout=5)
            try:return buy(request_key='same' if same_key else 'last-'+str(i),quantity=1)
            except OutOfStock:return 'unavailable'
        with ThreadPoolExecutor(max_workers=2) as workers:outcomes=list(workers.map(worker,[1,2]))
        equal(db.products.find_one(key)['available'],0);equal(db.orders.count_documents({}),1);equal(db.outbox.count_documents({}),1)
        if same_key:
            require(all(isinstance(r,dict) for r in outcomes));equal(sorted(r['replayed'] for r in outcomes),[False,True]);equal(outcomes[0]['order_id'],outcomes[1]['order_id'])
        else:equal(sum(r=='unavailable' for r in outcomes),1)
        observed['same_key_race' if same_key else 'last_unit_race']={'stock':0,'orders':1,'outbox':1,'outcome':'one new and one replay' if same_key else 'one reserved and one unavailable'}
    checks.check('barrier-started distinct-key purchases cannot both consume the last unit',lambda:race(False))
    checks.check('barrier-started duplicate purchases create one order and one replay',lambda:race(True))
    checks.check('committed replay still succeeds when stock is zero',lambda:equal(buy(request_key='same',quantity=1)['replayed'],True))
    def restocked():
        db.products.update_one(key,{'$set':{'available':10}})
        equal(buy(request_key='later',quantity=10)['replayed'],False);equal(db.products.find_one(key)['available'],0)
    checks.check('rolled-back unavailable key can succeed after later restock',restocked)
checks.save(observations=observed,scope='Real single-member replica-set transactions and concurrent service calls; no failover or HTTP/provider delivery')
