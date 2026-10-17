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
