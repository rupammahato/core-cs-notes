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
