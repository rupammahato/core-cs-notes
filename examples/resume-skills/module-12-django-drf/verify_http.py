from bootstrap import prepare
prepare()
from contextlib import contextmanager
import json
import socket
from threading import Thread
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler
from django.core.wsgi import get_wsgi_application
from socketserver import ThreadingMixIn
from work.models import Task, AuditEvent
from checks import Checks,equal,require

checks=Checks('http')
observed={}
class Quiet(WSGIRequestHandler):
    def log_message(self,*args): pass
class ThreadedServer(ThreadingMixIn,WSGIServer):
    daemon_threads=True

@contextmanager
def listener():
    server=ThreadedServer(('127.0.0.1',0),Quiet,allow_reuse_address=False)
    server.set_app(get_wsgi_application())
    thread=Thread(target=server.serve_forever,kwargs={'poll_interval':0.05},daemon=True)
    thread.start()
    try: yield 'http://127.0.0.1:'+str(server.server_port)
    finally:
        server.shutdown()
        thread.join(5)
        server.server_close()
        require(not thread.is_alive(),'WSGI listener still running')

with listener() as base:
    opener=build_opener(ProxyHandler({}))
    def request(method,path,body=None,token='alice-demo',raw=None,media='application/json'):
        headers={}
        if token is not None: headers['Authorization']='Bearer '+token
        data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        if data is not None: headers['Content-Type']=media
        req=Request(base+path,data=data,headers=headers,method=method)
        try: response=opener.open(req,timeout=5)
        except HTTPError as error: response=error
        with response:
            payload=response.read()
            return response.status,dict(response.headers),json.loads(payload) if payload and 'json' in response.headers.get('Content-Type','') else None
    def status(response,expected): equal(response[0],expected)
    checks.check('public Django health view responds',lambda:status(request('GET','/health/',token=None),200))
    checks.check('anonymous list rejected',lambda:status(request('GET','/api/tasks/',token=None),401))
    checks.check('unknown token rejected',lambda:status(request('GET','/api/tasks/',token='wrong'),401))
    def challenge():
        value=request('GET','/api/tasks/',token=None)
        equal(value[1]['WWW-Authenticate'],'Bearer')
    checks.check('401 retains authentication challenge',challenge)
    def listing():
        value=request('GET','/api/tasks/')
        status(value,200)
        equal(value[2]['count'],6)
        equal([r['id'] for r in value[2]['results']],[1,2])
        require(all(r['title']!='Beta secret' for r in value[2]['results']))
        observed['list_shape']={'count':value[2]['count'],'first_page_ids':[r['id'] for r in value[2]['results']]}
    checks.check('list is tenant-scoped ordered and paginated',listing)
    checks.check('second page has stable next records',lambda:equal([r['id'] for r in request('GET','/api/tasks/?page=2')[2]['results']],[3,4]))
    checks.check('page-size request is capped',lambda:equal(len(request('GET','/api/tasks/?page_size=100')[2]['results']),5))
    checks.check('invalid page returns 404',lambda:status(request('GET','/api/tasks/?page=99'),404))
    checks.check('cross-tenant detail hidden',lambda:status(request('GET','/api/tasks/7/'),404))
    checks.check('viewer can read tenant tasks',lambda:status(request('GET','/api/tasks/',token='reader-demo'),200))
    def viewer_write():
        before=Task.objects.count()
        status(request('POST','/api/tasks/',{'project':1,'title':'blocked'},token='reader-demo'),403)
        equal(Task.objects.count(),before)
    checks.check('viewer cannot create and produces no database row',viewer_write)
    def peer_write():
        original=Task.objects.get(pk=1).title
        status(request('PATCH','/api/tasks/1/',{'title':'stolen'},token='bob-demo'),403)
        equal(Task.objects.get(pk=1).title,original)
    checks.check('same-tenant peer cannot modify another owner task',peer_write)
    def peer_delete():
        status(request('DELETE','/api/tasks/1/',token='bob-demo'),403)
        require(Task.objects.filter(pk=1).exists())
    checks.check('same-tenant peer cannot delete another owner task',peer_delete)
    checks.check('read policy permits same-tenant peer detail',lambda:status(request('GET','/api/tasks/5/'),200))
    def owner_update():
        status(request('PATCH','/api/tasks/1/',{'title':'Owner update'}),200)
        equal(Task.objects.get(pk=1).title,'Owner update')
    checks.check('owner may update allowed field',owner_update)
    def foreign_project():
        status(request('PATCH','/api/tasks/1/',{'project':3}),400)
        equal(Task.objects.get(pk=1).project_id,1)
    checks.check('related project assignment is tenant-scoped',foreign_project)
    def forbidden(field,value):
        before=Task.objects.get(pk=1)
        status(request('PATCH','/api/tasks/1/',{field:value}),400)
        after=Task.objects.get(pk=1)
        equal((after.owner_id,after.status,after.revision),(before.owner_id,before.status,before.revision))
    checks.check('client cannot assign owner',lambda:forbidden('owner',2))
    checks.check('client cannot directly set status',lambda:forbidden('status','done'))
    checks.check('client cannot directly set revision',lambda:forbidden('revision',99))
    checks.check('unknown field rejected',lambda:status(request('POST','/api/tasks/',{'project':1,'title':'x','tenant_id':2}),400))
    checks.check('missing title rejected',lambda:status(request('POST','/api/tasks/',{'project':1}),400))
    checks.check('blank title rejected',lambda:status(request('POST','/api/tasks/',{'project':1,'title':''}),400))
    checks.check('oversized title rejected by serializer',lambda:status(request('POST','/api/tasks/',{'project':1,'title':'x'*81}),400))
    checks.check('malformed JSON rejected',lambda:status(request('POST','/api/tasks/',raw=b'{'),400))
    checks.check('unsupported media rejected',lambda:status(request('POST','/api/tasks/',raw=b'text',media='text/plain'),415))
    def duplicate():
        before=Task.objects.count()
        status(request('POST','/api/tasks/',{'project':1,'title':'Task 2'}),400)
        equal(Task.objects.count(),before)
    checks.check('database uniqueness conflict maps to 400 without extra row',duplicate)
    created={}
    def create():
        response=request('POST','/api/tasks/',{'project':1,'title':'Created by API'})
        status(response,201)
        created['id']=response[2]['id']
        task=Task.objects.get(pk=created['id'])
        equal((task.owner.username,task.project.tenant.slug,task.status),('alice','alpha','todo'))
        require('owner_id' not in response[2] and 'password' not in response[2])
    checks.check('create binds owner server-side and returns public schema',create)
    checks.check('partial update retains required relation',lambda:status(request('PATCH','/api/tasks/'+str(created['id'])+'/',{'title':'Patched API task'}),200))
    checks.check('full update requires project',lambda:status(request('PUT','/api/tasks/'+str(created['id'])+'/',{'title':'Incomplete PUT'}),400))
    def complete():
        value=request('POST','/api/tasks/2/complete/',{})
        status(value,200)
        equal(value[2],{'changed':True,'status':'done','revision':1})
        equal(AuditEvent.objects.filter(task_id=2,kind='completed').count(),1)
        observed['first_completion']=value[2]
    checks.check('custom action commits status revision and audit',complete)
    def repeated():
        value=request('POST','/api/tasks/2/complete/',{})
        status(value,200)
        equal(value[2],{'changed':False,'status':'done','revision':1})
        equal(AuditEvent.objects.filter(task_id=2,kind='completed').count(),1)
        observed['repeated_completion']=value[2]
    checks.check('sequential action retry does not duplicate effect',repeated)
    checks.check('custom action applies owner permission',lambda:status(request('POST','/api/tasks/2/complete/',{},token='bob-demo'),403))
    checks.check('custom action hides other tenant object',lambda:status(request('POST','/api/tasks/2/complete/',{},token='eve-demo'),404))
    def unexpected():
        status(request('POST','/api/tasks/3/complete/',{'status':'done'}),400)
        equal(Task.objects.get(pk=3).status,'todo')
    checks.check('action rejects unexpected input before changing state',unexpected)
    def destroy():
        status(request('DELETE','/api/tasks/'+str(created['id'])+'/'),204)
        require(not Task.objects.filter(pk=created['id']).exists())
    checks.check('owner deletion returns 204 and removes row',destroy)
    def method():
        value=request('PUT','/api/tasks/',{})
        status(value,405)
        require('GET' in value[1]['Allow'] and 'POST' in value[1]['Allow'])
    checks.check('method rejection preserves Allow',method)
    checks.check('unknown URL returns 404',lambda:status(request('GET','/missing/'),404))
    def metadata():
        value=request('GET','/api/tasks/')
        equal(value[1]['Cache-Control'],'no-store')
        equal(len(value[1]['X-Request-ID']),32)
    checks.check('middleware response headers survive DRF dispatch',metadata)
with socket.socket() as probe:
    probe.settimeout(1)
    require(probe.connect_ex(('127.0.0.1',int(base.rsplit(':',1)[1])))!=0,'listener remains open')
checks.save(observations=observed,port=int(base.rsplit(':',1)[1]),listener_closed=True,
            transport='Real loopback HTTP against Django development/test WSGI server; sequential requests')
