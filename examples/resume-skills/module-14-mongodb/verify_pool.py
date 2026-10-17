from threading import Event,Thread
from pymongo import monitoring
from pymongo.errors import WaitQueueTimeoutError,InvalidOperation
from db import make_client,database
from checks import Checks,equal,require

class Commands(monitoring.CommandListener):
    def __init__(self):self.names=[];self.hold=False;self.entered=Event();self.release=Event()
    def started(self,event):
        self.names.append(event.command_name)
        if self.hold and event.command_name=='find':
            self.hold=False;self.entered.set()
            if not self.release.wait(timeout=5):raise RuntimeError('pool fixture release deadline')
    def succeeded(self,event):pass
    def failed(self,event):pass

checks=Checks('pool');observed={};monitor=Commands()
with make_client(listeners=[monitor],max_pool_size=1,wait_ms=50) as client:
    client.admin.command('ping');db=database(client);db.rows.insert_many([{'_id':i} for i in range(5)])
    def lazy():
        monitor.names.clear();cursor=db.rows.find({}).sort('_id').batch_size(2)
        equal(monitor.names.count('find'),0)
        rows=list(cursor);equal([r['_id'] for r in rows],[0,1,2,3,4])
        equal(monitor.names.count('find'),1);equal(monitor.names.count('getMore'),2)
        observed['cursor_commands']={'find':monitor.names.count('find'),'getMore':monitor.names.count('getMore')}
    checks.check('cursor construction is lazy and iteration issues real find and getMore commands',lazy)
    def close_cursor():
        monitor.names.clear();cursor=db.rows.find({}).batch_size(2);next(cursor);cursor.close()
        equal(monitor.names.count('killCursors'),1)
    checks.check('explicit close releases a still-open server cursor',close_cursor)
    def pool_bound():
        monitor.hold=True;outcome=[]
        def worker():
            try:outcome.append(db.rows.find_one({'_id':0}))
            except Exception as e:outcome.append(e)
        thread=Thread(target=worker,daemon=True);thread.start()
        try:
            require(monitor.entered.wait(timeout=5),'command never checked out a connection')
            try:db.rows.find_one({'_id':1})
            except WaitQueueTimeoutError:observed['exhaustion']='WaitQueueTimeoutError'
            else:raise AssertionError('second borrower unexpectedly acquired max-size-one pool')
        finally:
            monitor.release.set();thread.join(timeout=6)
        require(not thread.is_alive());equal(outcome,[{'_id':0}])
    checks.check('held real command exhausts max-size-one pool and bounds another checkout',pool_bound)
    checks.check('pool serves requests again after its held connection is released',lambda:equal(db.rows.find_one({'_id':1}),{'_id':1}))
    observed['pool_max']=1
try:client.admin.command('ping')
except InvalidOperation:checks.check('closed MongoClient rejects subsequent operations',lambda:None)
else:raise AssertionError('closed client accepted work')
checks.save(observations=observed,scope='Actual synchronous PyMongo command monitoring pool checkout pressure cursor cleanup and client close')
