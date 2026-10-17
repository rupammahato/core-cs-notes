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
