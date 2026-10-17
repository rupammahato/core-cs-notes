from bootstrap import prepare
prepare()
from types import SimpleNamespace
from django.db import connection, transaction
from django.db.models import Count, Q
from django.core.exceptions import ValidationError
from django.test.utils import CaptureQueriesContext
from work.models import Task, Membership
from work.serializers import TaskSerializer
from checks import Checks, equal, require

checks = Checks('orm')
observed = {}
def tasks(): return Task.objects.filter(project__tenant__slug='alpha').order_by('id')

def lazy():
    with CaptureQueriesContext(connection) as log:
        qs = tasks().filter(status='todo')[:2]
    equal(len(log),0)
    with CaptureQueriesContext(connection) as log:
        equal(len(list(qs)),2)
    equal(len(log),1)
checks.check('QuerySet construction/filter/slice are lazy until iteration',lazy)

def cache():
    qs = tasks()
    list(qs)
    with CaptureQueriesContext(connection) as log:
        equal(len(list(qs)),6)
    equal(len(log),0)
checks.check('evaluated QuerySet reuses its own result cache',cache)

def clone():
    qs = tasks()
    list(qs)
    with CaptureQueriesContext(connection) as log:
        equal(len(list(qs.all())),6)
    equal(len(log),1)
checks.check('all clone performs a fresh query despite original cache',clone)

def count_exists():
    with CaptureQueriesContext(connection) as log:
        equal(tasks().count(),6)
        equal(tasks().exists(),True)
    equal(len(log),2)
checks.check('count and exists execute their own queries on fresh QuerySets',count_exists)

def iterators():
    qs = tasks()
    with CaptureQueriesContext(connection) as log:
        list(qs.iterator())
        list(qs.iterator())
    equal(len(log),2)
checks.check('iterator bypasses normal result cache on repeated passes',iterators)

def nplus():
    with CaptureQueriesContext(connection) as log:
        baseline = [(t.title,t.project.name,t.owner.username) for t in tasks()]
    naive = len(log)
    with CaptureQueriesContext(connection) as log:
        optimized = [(t.title,t.project.name,t.owner.username) for t in tasks().select_related('project','owner')]
    equal(baseline,optimized)
    equal((naive,len(log)),(13,1))
    observed['single_valued_relations'] = {'rows':6,'naive_queries':naive,'select_related_queries':len(log)}
checks.check('select_related removes measured FK N+1 while preserving values',nplus)

def many():
    with CaptureQueriesContext(connection) as log:
        baseline = [sorted(tag.label for tag in t.tags.all()) for t in tasks()]
    naive = len(log)
    with CaptureQueriesContext(connection) as log:
        optimized = [sorted(tag.label for tag in t.tags.all()) for t in tasks().prefetch_related('tags')]
    equal(baseline,optimized)
    equal((naive,len(log)),(7,2))
    observed['many_to_many'] = {'rows':6,'naive_queries':naive,'prefetch_queries':len(log)}
checks.check('prefetch_related removes measured M2M N+1 using two queries',many)

def serialize():
    membership = Membership.objects.get(user__username='alice',tenant__slug='alpha')
    request = SimpleNamespace(auth=membership)
    with CaptureQueriesContext(connection) as log:
        data = TaskSerializer(tasks().select_related('project','owner').prefetch_related('tags'),
                              many=True,context={'request':request}).data
    equal(len(log),2)
    equal(len(data),6)
    require(all('owner_name' in row and 'tags' in row for row in data))
    observed['optimized_serializer_queries'] = len(log)
checks.check('serializer relation traversal stays within measured query budget',serialize)

def aggregate():
    with CaptureQueriesContext(connection) as log:
        rows = list(tasks().annotate(tag_count=Count('tags')).values_list('id','tag_count'))
    equal([count for pk,count in rows],[2,1,2,1,2,1])
    equal(len(log),1)
checks.check('annotate aggregation runs in SQL',aggregate)

def values():
    with CaptureQueriesContext(connection) as log:
        rows = list(tasks().values('id','title'))
    equal(len(log),1)
    equal(set(rows[0]),{'id','title'})
checks.check('values explicitly projects dictionary fields',values)

def logic():
    equal(list(tasks().filter(Q(title='Task 1')|Q(title='Task 6')).values_list('id',flat=True)),[1,6])
checks.check('Q expressions compose OR filters',logic)

def parameterized():
    text = "' OR 1=1 --"
    captured = []
    def wrapper(execute,sql,params,many,context):
        captured.append((sql,params))
        return execute(sql,params,many,context)
    with connection.execute_wrapper(wrapper):
        equal(tasks().filter(title=text).count(),0)
    require(any(params and text in params and text not in sql for sql,params in captured))
checks.check('ORM lookup keeps adversarial text in bound parameters',parameterized)

def deferred():
    with CaptureQueriesContext(connection) as log:
        equal([t.title for t in tasks().only('id')],['Task '+str(i) for i in range(1,7)])
    equal(len(log),7)
    observed['deferred_title_queries'] = len(log)
checks.check('only can introduce extra queries when deferred fields are read',deferred)

def clean():
    owner = Task.objects.get(pk=1).owner
    item = Task(project_id=1,owner=owner,title='x'*81)
    try:
        with transaction.atomic():
            item.save()
            equal(Task.objects.get(pk=item.pk).title,'x'*81)
            try: item.full_clean()
            except ValidationError: pass
            else: raise AssertionError('full_clean accepted oversized title')
            raise RuntimeError('rollback fixture')
    except RuntimeError:
        pass
checks.check('save does not automatically call full_clean; SQLite accepts oversized varchar',clean)

def sqlite_lock():
    equal(connection.features.has_select_for_update,False)
    with CaptureQueriesContext(connection) as log, transaction.atomic():
        list(tasks().select_for_update()[:1])
    require(all('FOR UPDATE' not in row['sql'].upper() for row in log))
    observed['sqlite_select_for_update'] = {'supported':False,'for_update_emitted':False}
checks.check('SQLite select_for_update is not a row-lock test',sqlite_lock)
checks.save(observations=observed,backend=connection.vendor)
