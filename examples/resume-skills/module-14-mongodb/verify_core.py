from datetime import datetime,timezone
from decimal import Decimal
from bson import ObjectId,Decimal128,BSON,json_util
from pymongo.errors import WriteError,DuplicateKeyError,BulkWriteError
from db import make_client,database
from catalog import prepare,product_filter,InvalidRequest
from checks import Checks,equal,require
checks=Checks('core'); observed={}
with make_client() as client:
    db=database(client); prepare(db)
    base=db.products.find_one({'tenant_id':1})
    def invalid(change):
        doc={**base,**change}; doc.pop('_id',None)
        try: db.products.insert_one(doc)
        except WriteError as e: equal(e.code,121)
        else: raise AssertionError('invalid document accepted')
    checks.check('server validator rejects negative stock',lambda:invalid({'sku':'negative','available':-1}))
    checks.check('server validator rejects string stock',lambda:invalid({'sku':'string','available':'5'}))
    checks.check('server validator rejects boolean stock despite Python bool being an int subclass',lambda:invalid({'sku':'boolean','available':True}))
    def required():
        doc=dict(base);doc.pop('_id');doc.pop('currency')
        try: db.products.insert_one(doc)
        except WriteError as e: equal(e.code,121)
        else: raise AssertionError('required field accepted')
    checks.check('required field is enforced by the server',required)
    def unique():
        doc=dict(base);doc.pop('_id')
        try: db.products.insert_one(doc)
        except DuplicateKeyError as e: equal(e.code,11000)
        else: raise AssertionError('duplicate accepted')
        equal(db.products.count_documents({'sku':'basic'}),2)
    checks.check('compound unique index scopes SKU uniqueness to tenant',unique)
    def identifier():
        equal(db.products.find_one({'_id':str(base['_id'])}),None)
        equal(db.products.find_one({'_id':ObjectId(str(base['_id']))})['_id'],base['_id'])
    checks.check('ObjectId and its hexadecimal string are different BSON values',identifier)
    def types():
        stamp=datetime(2026,10,14,6,30,0,123456,tzinfo=timezone.utc)
        db.values.insert_one({'_id':1,'amount':Decimal128(Decimal('125.50')),'at':stamp})
        row=db.values.find_one({'_id':1})
        equal(row['amount'].to_decimal(),Decimal('125.50'));equal(row['at'].microsecond,123000)
        equal(row['at'].tzinfo,timezone.utc)
        observed['typed_values']={'decimal':str(row['amount'].to_decimal()),'date':row['at'].isoformat()}
    checks.check('Decimal128 and aware BSON date round-trip with millisecond precision',types)
    def ejson():
        row=db.products.find_one({'tenant_id':1})
        equal(json_util.loads(json_util.dumps(row))['_id'],row['_id'])
    checks.check('Extended JSON preserves ObjectId across serialization',ejson)
    def boundary():
        for sku in ({'$ne':None},['basic'],None):
            try: product_filter(1,sku)
            except InvalidRequest: pass
            else: raise AssertionError('operator-shaped SKU accepted')
        literal=product_filter(1,'{"$ne":null}')
        equal(db.products.find_one(literal),None)
        equal(db.products.count_documents({'tenant_id':1,'sku':{'$ne':None}}),1)
    checks.check('query builder rejects operator objects and keeps string input literal',boundary)
    def privileges():
        equal(db.products.count_documents({}),2);equal(db.products.count_documents(product_filter(1,'basic')),1)
        observed['tenant_filter_required']=True
    checks.check('collection access does not supply per-request tenant isolation',privileges)
    def reference():
        db.references.insert_one({'_id':1,'product_id':ObjectId(),'tenant_id':1})
        equal(db.references.count_documents({}),1)
        observed['dangling_reference_accepted']=True
    checks.check('a reference field does not create foreign-key enforcement',reference)
    def nulls():
        db.nulls.insert_many([{'_id':1,'label':None},{'_id':2},{'_id':3,'label':'x'}])
        equal(sorted(x['_id'] for x in db.nulls.find({'label':None})),[1,2])
        equal([x['_id'] for x in db.nulls.find({'label':{'$exists':False}})],[2])
        equal([x['_id'] for x in db.nulls.find({'label':{'$type':10}})],[1])
        observed['null_query_ids']=[1,2]
    checks.check('null equality includes missing fields while exists and type distinguish them',nulls)
    def unique_null():
        db.unique_null.create_index('email',unique=True)
        db.unique_null.insert_one({'_id':1})
        try: db.unique_null.insert_one({'_id':2,'email':None})
        except DuplicateKeyError as e: equal(e.code,11000)
        else: raise AssertionError('missing and null unique key accepted')
    checks.check('single-field unique index treats missing and null as a shared null key',unique_null)
    def replacement():
        db.ops.insert_one({'_id':1,'keep':'yes','count':1})
        result=db.ops.update_one({'_id':1},{'$inc':{'count':2},'$set':{'label':'updated'}})
        equal((result.matched_count,result.modified_count),(1,1));equal(db.ops.find_one({'_id':1})['keep'],'yes')
        db.ops.replace_one({'_id':1},{'count':9})
        equal(db.ops.find_one({'_id':1}),{'_id':1,'count':9})
    checks.check('operator update preserves other fields while replacement removes them',replacement)
    def addset():
        db.ops.update_one({'_id':1},{'$addToSet':{'tags':'x'}});db.ops.update_one({'_id':1},{'$addToSet':{'tags':'x'}})
        equal(db.ops.find_one({'_id':1})['tags'],['x'])
    checks.check('addToSet prevents repeat insertion of the same scalar member',addset)
    def upsert():
        key={'tenant_id':1,'external_id':'source-7'}
        first=db.ingestion.update_one(key,{'$set':{'value':4},'$setOnInsert':{'created':'fixture'}},upsert=True)
        second=db.ingestion.update_one(key,{'$set':{'value':5}},upsert=True)
        require(first.upserted_id is not None);equal(second.upserted_id,None);equal(second.matched_count,1)
        equal(db.ingestion.count_documents(key),1)
    checks.check('sequential upsert reports insert then matched update',upsert)
    def partial_bulk():
        good={**base,'sku':'bulk-good'};good.pop('_id')
        bad={**base,'sku':'bulk-bad','available':-1};bad.pop('_id')
        later={**base,'sku':'bulk-later'};later.pop('_id')
        try: db.products.insert_many([good,bad,later],ordered=True)
        except BulkWriteError as e: equal(e.details['nInserted'],1)
        else: raise AssertionError('bulk invalid document accepted')
        equal(db.products.count_documents({'sku':'bulk-good'}),1);equal(db.products.count_documents({'sku':'bulk-later'}),0)
    checks.check('ordered batch can leave earlier documents committed after a later validation failure',partial_bulk)
checks.save(observations=observed,scope='Real MongoDB BSON adapters validators CRUD and unique indexes; no application authentication')
