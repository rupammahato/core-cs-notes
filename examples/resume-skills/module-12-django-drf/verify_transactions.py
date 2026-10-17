from bootstrap import prepare
prepare()
from django.db import transaction, IntegrityError, connection
from django.db.models import F
from work.models import Task, AuditEvent
from work.services import complete_task
from checks import Checks, equal, require

checks = Checks('transactions')
observed = {}

def complete():
    callbacks = []
    equal(complete_task(task_id=1,tenant_id=1,owner_id=1,after_commit=callbacks.append),True)
    task = Task.objects.get(pk=1)
    equal((task.status,task.revision),('done',1))
    equal(AuditEvent.objects.filter(task_id=1,kind='completed').count(),1)
    equal(callbacks,[1])
checks.check('conditional completion and audit insert commit together',complete)

def retry():
    callbacks = []
    equal(complete_task(task_id=1,tenant_id=1,owner_id=1,after_commit=callbacks.append),False)
    equal(Task.objects.get(pk=1).revision,1)
    equal(AuditEvent.objects.filter(task_id=1).count(),1)
    equal(callbacks,[])
checks.check('sequential completion retry does not repeat revision audit or callback',retry)

def rollback():
    try:
        complete_task(task_id=2,tenant_id=1,owner_id=1,fail_after_update=True)
    except RuntimeError as exc:
        equal(str(exc),'injected before audit insert')
    else:
        raise AssertionError('failure did not occur')
    task = Task.objects.get(pk=2)
    equal((task.status,task.revision),('todo',0))
    equal(AuditEvent.objects.filter(task_id=2).count(),0)
checks.check('injected failure after SQL update rolls back status revision and audit',rollback)

def scope_guards():
    equal(complete_task(task_id=2,tenant_id=2,owner_id=1),False)
    equal(complete_task(task_id=2,tenant_id=1,owner_id=2),False)
    equal(Task.objects.get(pk=2).status,'todo')
checks.check('service transition filters tenant and owner',scope_guards)

def callback_scope():
    calls=[]
    with transaction.atomic():
        transaction.on_commit(lambda:calls.append('after'))
        equal(calls,[])
    equal(calls,['after'])
    observed['on_commit_timing']=['inside: no callback','after commit: callback']
checks.check('on_commit runs after the outer transaction commits',callback_scope)

def discarded():
    calls=[]
    try:
        with transaction.atomic():
            transaction.on_commit(lambda:calls.append('unexpected'))
            raise ValueError('rollback')
    except ValueError: pass
    equal(calls,[])
checks.check('rolled-back on_commit callbacks are discarded',discarded)

def savepoint():
    before=Task.objects.get(pk=3).title
    with transaction.atomic():
        Task.objects.filter(pk=3).update(title='Outer change')
        try:
            with transaction.atomic():
                Task.objects.filter(pk=3).update(status='done')
                raise ValueError('inner rollback')
        except ValueError: pass
        equal(Task.objects.get(pk=3).status,'todo')
        equal(Task.objects.get(pk=3).title,'Outer change')
    Task.objects.filter(pk=3).update(title=before)
checks.check('nested atomic savepoint rolls back inner work while outer work continues',savepoint)

def constraint(fn):
    try:
        with transaction.atomic(): fn()
    except IntegrityError: return
    raise AssertionError('constraint did not reject')
checks.check('database rejects invalid task status',lambda:constraint(lambda:Task.objects.filter(pk=2).update(status='bad')))
checks.check('database rejects negative revision',lambda:constraint(lambda:Task.objects.filter(pk=2).update(revision=-1)))
checks.check('database rejects duplicate project task title',lambda:constraint(lambda:Task.objects.create(project_id=1,owner_id=1,title='Task 1')))
checks.check('database rejects duplicate task event kind',lambda:constraint(lambda:AuditEvent.objects.create(task_id=1,kind='completed')))

def stale():
    task=Task.objects.get(pk=4)
    equal(task.revision,0)
    Task.objects.filter(pk=4).update(revision=F('revision')+1)
    equal(task.revision,0)
    task.refresh_from_db()
    equal(task.revision,1)
    Task.objects.filter(pk=4).update(revision=0)
checks.check('SQL F update does not refresh an already-loaded Python object',stale)

def python_state():
    task=Task.objects.get(pk=5)
    try:
        with transaction.atomic():
            task.status='done'
            task.save(update_fields=['status'])
            raise ValueError('rollback')
    except ValueError: pass
    equal(task.status,'done')
    equal(Task.objects.get(pk=5).status,'todo')
    task.refresh_from_db()
    equal(task.status,'todo')
checks.check('database rollback does not rewind Python model attributes',python_state)

def callback_failure():
    def fail(task_id): raise RuntimeError('after commit failure')
    try:
        complete_task(task_id=6,tenant_id=1,owner_id=2,after_commit=fail)
    except RuntimeError as exc: equal(str(exc),'after commit failure')
    else: raise AssertionError('callback failure not observed')
    equal(Task.objects.get(pk=6).status,'done')
    equal(AuditEvent.objects.filter(task_id=6).count(),1)
    observed['callback_failure']={'database_committed':True,'callback_failed':True}
checks.check('on_commit failure cannot undo the already-committed business transaction',callback_failure)
checks.save(observations=observed,backend=connection.vendor,
            scope='SQLite transactions and sequential retries; no PostgreSQL row-lock or competing-writer test')
