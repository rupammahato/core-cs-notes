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
