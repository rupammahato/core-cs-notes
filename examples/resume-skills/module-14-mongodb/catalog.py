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
