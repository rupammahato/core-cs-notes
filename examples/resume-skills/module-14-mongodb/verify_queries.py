from datetime import datetime,timezone,timedelta
from bson import ObjectId
from pymongo.errors import OperationFailure
from db import make_client,database
from catalog import prepare
from queries import revenue_pipeline,scoped_lookup_pipeline
from pagination import page
from checks import Checks,equal,require
checks=Checks('queries'); observed={}
with make_client() as client:
    db=database(client);prepare(db)
    db.variants.insert_many([
        {'_id':'cross','variants':[{'color':'red','stock':0},{'color':'blue','stock':5}]},
        {'_id':'same','variants':[{'color':'red','stock':2}]}])
    def dotted_array():
        ids=sorted(r['_id'] for r in db.variants.find({'variants.color':'red','variants.stock':{'$gte':1}}))
        equal(ids,['cross','same']);observed['dotted_array_ids']=ids
    checks.check('separate dotted array predicates can match different elements',dotted_array)
    def elem():
        ids=[r['_id'] for r in db.variants.find({'variants':{'$elemMatch':{'color':'red','stock':{'$gte':1}}}})]
        equal(ids,['same']);observed['elem_match_ids']=ids
    checks.check('elemMatch requires the conditions to hold on the same element',elem)
    checks.check('array membership query matches a scalar contained in tags',lambda:equal(db.products.count_documents({'tags':'backend'}),1))
    def projection():
        row=db.products.find_one({'tenant_id':1},{'_id':0,'sku':1,'attributes.color':1})
        equal(row,{'sku':'basic','attributes':{'color':'blue'}})
    checks.check('projection limits returned fields without changing tenant scope',projection)
    def mixed():
        try: list(db.products.find({},{'sku':1,'available':0}))
        except OperationFailure as e: equal(e.code,31254)
        else: raise AssertionError('mixed projection accepted')
    checks.check('mixed inclusion and exclusion projection is rejected except the id exception',mixed)
    db.reports.insert_many([
        {'_id':1,'tenant_id':1,'status':'paid','total_minor':500,'items':[{'sku':'A','quantity':2,'unit_price_minor':100},{'sku':'B','quantity':1,'unit_price_minor':300}]},
        {'_id':2,'tenant_id':1,'status':'paid','total_minor':400,'items':[{'sku':'A','quantity':4,'unit_price_minor':100}]},
        {'_id':3,'tenant_id':1,'status':'pending','total_minor':100,'items':[{'sku':'A','quantity':1,'unit_price_minor':100}]},
        {'_id':4,'tenant_id':2,'status':'paid','total_minor':9900,'items':[{'sku':'A','quantity':99,'unit_price_minor':100}]}])
    def revenue():
        rows=list(db.reports.aggregate(revenue_pipeline(1)))
        equal(rows,[{'_id':'A','quantity':6,'revenue_minor':600},{'_id':'B','quantity':1,'revenue_minor':300}]);observed['dashboard']=rows
    checks.check('scoped aggregation unwinds items and groups actual quantity and revenue',revenue)
    def double_count():
        wrong=list(db.reports.aggregate([{'$match':{'tenant_id':1,'status':'paid'}},{'$unwind':'$items'},{'$group':{'_id':None,'total':{'$sum':'$total_minor'}}}]))[0]['total']
        correct=list(db.reports.aggregate([{'$match':{'tenant_id':1,'status':'paid'}},{'$group':{'_id':None,'total':{'$sum':'$total_minor'}}}]))[0]['total']
        equal((wrong,correct),(1400,900));observed['unwind_total_trap']={'wrong':wrong,'correct':correct}
    checks.check('unwind duplicates order-level totals if summed at item granularity',double_count)
    db.refs.insert_one({'_id':1,'tenant_id':1,'sku':'basic'})
    def unsafe_lookup():
        rows=list(db.refs.aggregate([{'$match':{'tenant_id':1}},{'$lookup':{'from':'products','localField':'sku','foreignField':'sku','as':'product'}}]))
        equal(len(rows[0]['product']),2)
    checks.check('outer tenant match alone does not scope a foreign lookup',unsafe_lookup)
    def safe_lookup():
        row=list(db.refs.aggregate(scoped_lookup_pipeline(1)))[0]
        equal(len(row['product']),1);equal(row['product'][0]['tenant_id'],1)
    checks.check('lookup pipeline includes tenant and SKU on the foreign collection',safe_lookup)
    stamp=datetime(2026,10,14,tzinfo=timezone.utc)
    db.feed.insert_many([{'_id':ObjectId(f'{i:024x}'),'tenant_id':1,'created_at':stamp} for i in range(1,7)]+[{'_id':ObjectId('f'*24),'tenant_id':2,'created_at':stamp}])
    db.feed.create_index([('tenant_id',1),('created_at',-1),('_id',-1)])
    def pagination():
        got=[];after=None
        while True:
            rows=page(db.feed,1,after=after,limit=2)
            if not rows:break
            got.extend(int(str(r['_id']),16) for r in rows)
            after=(rows[-1]['created_at'],rows[-1]['_id'])
        equal(got,[6,5,4,3,2,1]);observed['cursor_ids']=got
    checks.check('keyset pagination uses a stable id tie-breaker and preserves tenant filter',pagination)
    def insert_between():
        first=page(db.feed,1,limit=2);last=first[-1]
        db.feed.insert_one({'_id':ObjectId(f'{7:024x}'),'tenant_id':1,'created_at':stamp+timedelta(seconds=1)})
        second=page(db.feed,1,after=(last['created_at'],last['_id']),limit=2)
        equal([int(str(r['_id']),16) for r in second],[4,3])
    checks.check('newer insert between pages does not shift this keyset continuation',insert_between)
    def dot_update():
        db.nested.insert_one({'_id':1,'settings':{'color':'blue','size':'M'}})
        db.nested.update_one({'_id':1},{'$set':{'settings.color':'red'}})
        equal(db.nested.find_one({'_id':1})['settings'],{'color':'red','size':'M'})
        db.nested.update_one({'_id':1},{'$set':{'settings':{'color':'green'}}})
        equal(db.nested.find_one({'_id':1})['settings'],{'color':'green'})
    checks.check('dot update preserves siblings while assigning an embedded object replaces it',dot_update)
checks.save(observations=observed,scope='Actual MongoDB array queries aggregation lookup and cursor pagination')
