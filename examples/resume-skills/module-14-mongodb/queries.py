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
