# Resume Skills Placement Handbook — Part 14
# Module 12: Django and Django REST Framework

**Module 12 · 4–5 hours · Tier 2; core depth for Django roles · Requires: M6-M8, M10; DBMS models, SQL and transactions**

---

## Why this module matters

Django adds conventions and integrated tools to the Python backend picture: projects/apps, models, migrations, routing, middleware, authentication and administration. Django REST Framework adds API-oriented requests, serializers, views, permissions and pagination on top of Django.

An interviewer can move quickly from “What is Django?” to “When does a QuerySet execute?”, “Why did this endpoint issue 100 queries?”, “Do object permissions filter a list?”, or “What if an on_commit callback fails after the row changed?”

> **Framework conventions organize the application; query shape determines database work; explicit authorization and transaction boundaries preserve the domain's rules.**

This chapter builds a small tenant-scoped task API, measures its ORM behavior and verifies negative permissions, migrations and rollback paths. It connects the framework to the CS/DBMS material instead of treating ORM methods as magic.

**Verification: 76 checks passed — 15 ORM, 14 transaction, nine framework and 38 real HTTP checks.** Three additional management checks passed: Django system checks, model/migration drift detection and pending-migration detection.

### Recorded environment

| Component | Actual version |
| --- | --- |
| Python | CPython 3.12.10, 64-bit Windows |
| Django / DRF | 5.1.3 / 3.15.2 |
| SQLite | 3.49.1, through Python's sqlite3/Django backend |
| asgiref / sqlparse / tzdata | 3.12.1 / 0.5.5 / 2026.4 |

The examples use an isolated environment installed from cached wheels. **Django 5.1 is now unsupported; these are historical teaching pins, not a production deployment recommendation.** Version-matched documentation supports interpretation of this run; supported releases must be selected separately for a real application. The [Django 5.1 documentation](https://docs.djangoproject.com/en/5.1/ref/models/querysets/) explicitly marks that release unsupported.

### Run the examples

From the repository root, with the prepared environment:

```powershell
./examples/resume-skills/module-12-django-drf/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-12-django-drf/verify.py
```

To recreate the recorded environment, select Python 3.12 first. With python referring to it:

```powershell
python -m venv examples/resume-skills/module-12-django-drf/.venv
./examples/resume-skills/module-12-django-drf/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-12-django-drf/requirements.lock.txt
./examples/resume-skills/module-12-django-drf/.venv/Scripts/python.exe -m pip check
```

Installation normally needs package access; this machine used cached wheels with --no-index. The environment/wheelhouse are ignored and global packages were not changed. The lock is a package-version snapshot, not a hash-verified portable lock.

The verifier creates a fresh file-backed SQLite database for each group, applies real migrations, seeds deterministic fixtures and runs each group in a fresh process. It starts one temporary loopback WSGI listener for HTTP checks, then stops it. Its owned temporary database directory is removed after child processes finish. No persistent server is started; port 3000 remains stopped.

The settings require M12_DATABASE explicitly, so importing this example cannot silently connect to an existing project database. The verifier supplies that path. Run the aggregate verifier rather than individual groups against a previously seeded database.

---

## 12.1 What are Django and DRF?

**Django is a Python web framework with integrated application conventions and components, including an ORM, migrations, URL routing, middleware, templates, authentication and admin tooling. DRF is an API toolkit built on Django.** It does not replace Django or the database.

| Layer | Responsibility |
| --- | --- |
| Python / CPython | Language and interpreter execution |
| WSGI/ASGI server | Network/protocol handling and application invocation |
| Django | HTTP application framework and integrated components |
| DRF | API request/response handling, serializers, views and permissions |
| Application service | Business transitions and invariants |
| Django ORM | Translate data operations into backend SQL/results |
| Database | Shared persisted state, constraints, transactions and locks |

Django can serve HTML or JSON and supports WSGI/ASGI application interfaces. This chapter exercises synchronous DRF views through a development/test WSGI server. An asgi.py entry point is included but not exercised by the HTTP suite; core Django async support does not automatically make every extension or ORM call safe in async code. Reference: [Django overview](https://docs.djangoproject.com/en/6.0/intro/overview/), [Django async support](https://docs.djangoproject.com/en/5.1/topics/async/).

### Model–View–Template

- **Model:** persistence/domain data representation and ORM behavior.
- **View:** receives a request and coordinates the response.
- **Template:** presentation rendering, commonly HTML.

Django's view performs much of what MVC discussions call controller work. Naming differs; responsibilities matter more than forcing a perfect acronym equivalence. An API returning DRF Response data does not need an HTML template for every route.

### Project versus app

A project configures one Django installation/application deployment: settings, root URLs and server entry points. An app groups a responsibility/domain, such as work/tasks. One project can contain many apps; an app is not a separate process or network service.

The runnable example is organized as:

```text
module-12-django-drf/
  manage.py
  config/
    settings.py    root configuration
    urls.py        URL/router inclusion
    wsgi.py        exercised server entry point
    asgi.py        included entry point, not exercised here
  work/
    models.py      persisted structures and constraints
    migrations/    generated schema history
    serializers.py input/output adaptation
    authentication.py / permissions.py
    services.py    transactional business transition
    views.py       ViewSet, pagination and small probe views
    middleware.py  correlation trace
  fixtures.py / bootstrap.py / verify*.py
```

---

## 12.2 Trace one request through Django and DRF

```text
HTTP client -> WSGI server -> Django handler
  -> middleware request side
  -> root URLconf / router resolution
  -> DRF view dispatch
  -> wrap request, authenticate, check view permissions/throttles
  -> action: scoped query / object permissions / serializer / service
  -> DRF Response and selected renderer
  -> middleware response side
  -> server sends response
```

Parsing and validation happen when the relevant view path accesses/validates input. Error and streaming paths can alter the details. This is a mechanism map, not a claim that every line executes for every request.

Django URL patterns are resolved in order; include delegates part of the path to another URLconf. reverse builds a URL from a named pattern, reducing hard-coded coupling. Reference: [URL dispatcher](https://docs.djangoproject.com/en/5.1/topics/http/urls/).

### Complete URL setup: config/urls.py

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from work.views import TaskViewSet, health, SessionProbe
router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')
urlpatterns = [path('health/',health), path('api/',include(router.urls)),
               path('session-probe/',SessionProbe.as_view())]
```

The router maps collection and detail URLs to ViewSet actions. The framework check resolves PATCH on task detail to partial_update and resolves the completion URL to task-complete. That demonstrates registration, not authorization; permissions are checked later by the view.

### DRF request and response are additional abstractions

DRF Request wraps the underlying Django HttpRequest and provides parsed request.data, query_params and the DRF authentication context. Response holds unrendered response data for the chosen renderer. A Django JsonResponse can also serve JSON, but does not by itself add DRF's dispatch/serializer/permission machinery. References: [DRF requests](https://www.django-rest-framework.org/api-guide/requests/), [responses](https://www.django-rest-framework.org/api-guide/responses/).

Django AuthenticationMiddleware primarily integrates Django session authentication. The custom DRF bearer authentication here occurs during DRF dispatch. Do not assume outer Django middleware already has the final DRF bearer principal before the view runs.

### Middleware wraps application flow

Configured middleware forms nested request/response processing. Order matters: session middleware must establish session state before authentication middleware uses it. Short-circuit responses and framework exception conversion complicate a simplistic “every hook always runs” story. Reference: [Django middleware](https://docs.djangoproject.com/en/6.0/topics/http/middleware/).

Complete middleware source:

```python
from uuid import uuid4
from threading import Lock

class TraceLog:
    def __init__(self):
        self.rows = []
        self.lock = Lock()
    def add(self, request_id, event):
        with self.lock:
            self.rows.append((request_id,event))
    def trace(self, request_id):
        with self.lock:
            return [event for rid,event in self.rows if rid==request_id]

trace_log = TraceLog()  # Bounded test workload only, not a production telemetry store.

class CorrelationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.request_id = uuid4().hex
        trace_log.add(request.request_id,'middleware-in')
        response = self.get_response(request)
        trace_log.add(request.request_id,'middleware-out')
        response['X-Request-ID'] = request.request_id
        response['Cache-Control'] = 'no-store'
        return response
    def process_view(self, request, view_func, view_args, view_kwargs):
        trace_log.add(request.request_id,'view-resolved')
```

Actual trace for the tested ordinary health request:

```json
[
  "middleware-in",
  "view-resolved",
  "middleware-out"
]
```

The log is a locked in-memory test fixture with a bounded test workload, not a production telemetry system. A request ID supports correlation; it is not an identity, permission or secret.

---

## 12.3 Models, relationships and database constraints

The task API has two tenants. Alice and Bob are editors in alpha; Reader is a viewer in alpha; Eve is an editor in beta. Members can read their tenant's tasks. Editors can create tasks and modify/delete only tasks they own. Task creation binds the owner on the server.

```text
Tenant --< Membership >-- User
   |
   +--< Project --< Task >-- User (owner)
   |                 |
   +--< Tag >--------+   many-to-many
                     |
                     +--< AuditEvent
```

Task tenancy is derived from its project, avoiding a separate redundant task tenant column. Tags also have tenant ownership. Ordinary foreign keys ensure referenced rows exist; they do not automatically prove two related rows belong to the same tenant.

### Complete models: work/models.py

```python
from django.conf import settings
from django.db import models
from django.db.models import Q

class Tenant(models.Model):
    slug = models.SlugField(unique=True)

class Membership(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=12, choices=[('editor','Editor'),('viewer','Viewer')])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['tenant','user'], name='one_tenant_membership')]

class Project(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['tenant','name'], name='unique_project_name')]

class Tag(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    label = models.CharField(max_length=40)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['tenant','label'], name='unique_tenant_tag')]

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=80)
    status = models.CharField(max_length=8, choices=[('todo','Todo'),('done','Done')], default='todo')
    revision = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['id']
        constraints = [models.UniqueConstraint(fields=['project','title'], name='unique_project_task_title'),
                       models.CheckConstraint(condition=Q(revision__gte=0), name='nonnegative_task_revision'),
                       models.CheckConstraint(condition=Q(status__in=['todo','done']), name='valid_task_status')]

class AuditEvent(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='events')
    kind = models.CharField(max_length=20)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['task','kind'], name='one_task_event_kind')]
```

| Mechanism | Rule it establishes here |
| --- | --- |
| ForeignKey | Referenced project/user/tenant exists, with configured deletion behavior |
| ManyToManyField | Relation rows connect tasks and tags |
| UniqueConstraint | Duplicate project/title or task/event-kind is rejected |
| CheckConstraint | Task revision is nonnegative; status belongs to the allowed set |
| choices | Application/model field vocabulary; a separate DB check enforces status on direct SQL writes |
| default ordering | This model declares ID order; the API also orders explicitly |

The transaction verifier bypasses serializers with ORM updates and confirms database rejection of invalid status, negative revision and duplicate keys. Constraints protect shared state across valid write paths; a serializer's earlier check alone cannot replace them. Reference: [constraints](https://docs.djangoproject.com/en/5.1/ref/models/constraints/).

The framework verifier deliberately adds a beta tag to an alpha task through the ORM and shows that foreign keys allow it. The API's tenant-filtered prefetch prevents disclosing that tag. All writers still need semantic relation checks; filtering output does not repair invalid stored relationships.

The audit record is a small transaction fixture with cascade deletion, not an immutable compliance ledger or a fully implemented outbox.

---

## 12.4 Migrations: model state and schema history

A Python model definition is not the database schema by itself. makemigrations compares the model state with migration history and writes operations. migrate applies the migration graph to a selected database and records applied migrations. It does not merely rerun every model declaration on every request. Reference: [Django migrations](https://docs.djangoproject.com/en/5.1/topics/migrations/).

| Command | Purpose |
| --- | --- |
| makemigrations work | Generate model-state change operations |
| migrate | Apply pending operations to the configured database |
| showmigrations | Inspect migration status |
| sqlmigrate work 0001 | Inspect backend SQL for one migration |
| makemigrations work --check --dry-run | Detect model changes missing migration files |
| migrate --check | Detect pending migrations |
| check | Run configured Django system checks |

The example generated work/migrations/0001_initial.py with Django and applied it to each fresh database. The verifier confirms the initial app migration is recorded and the migration plan is empty. Recorded management output:

```json
[
  {
    "command": [
      "check"
    ],
    "stdout": "System check identified no issues (0 silenced).\n"
  },
  {
    "command": [
      "makemigrations",
      "work",
      "--check",
      "--dry-run"
    ],
    "stdout": "No changes detected in app 'work'\n"
  },
  {
    "command": [
      "migrate",
      "--check"
    ],
    "stdout": ""
  }
]
```

These checks establish this example's model/history alignment and local migration application. They do not certify a production schema, a large backfill, zero downtime or application compatibility during rolling deployment.

Keep model changes and their migration files together in version control. Review generated operations before applying them. Editing an already-applied migration's meaning can make different environments disagree about what the recorded history represents.

### Data migrations and deployment are additional work

A data migration should use the migration framework's historical model state, rather than assuming today's imported model matches an older schema. Large data changes need batching, restart policy, lock/runtime assessment and application-version compatibility.

For a required field on a large existing table, think in stages: introduce a compatible field, backfill under a defined policy, switch application behavior, then enforce the final constraint. Backend DDL/locking behavior matters; this chapter only verifies creation of a fresh SQLite schema.

---

## 12.5 QuerySets: what is lazy, what executes, what caches?

A QuerySet describes a query and can be refined before execution. Evaluating it produces data. The database work occurs at evaluation or terminal operations, not automatically at every line that mentions a manager. Reference: [QuerySet API](https://docs.djangoproject.com/en/5.1/ref/models/querysets/).

| Operation | Typical result / boundary |
| --- | --- |
| objects.filter(...) | A refined QuerySet |
| exclude/order_by/select_related | Another query description |
| get(...) | One model instance or a not-found/multiple-result exception |
| list/iteration/len/bool | Evaluation of the QuerySet |
| count/exists | Targeted database operation on an unevaluated QuerySet |
| update/delete/create | Immediate write operation |
| values/values_list | Project selected fields when evaluated |
| annotate | Add computed/aggregate expressions to the query |

Ordinary slicing can remain lazy; stepped slicing can evaluate. Logging/repr or a boolean check can trigger database work. Do not assume debugging is always query-free.

### The cache belongs to that QuerySet

The verifier constructs/filters/slices a QuerySet with zero queries, then observes one query when iterating it. Reiterating an evaluated QuerySet uses its result cache with zero new queries. Calling all on it returns a fresh clone that executes a new query in the tested path.

This is not a global ORM cache or a synchronized view of later database writes. Long-lived cached results can become stale. iterator bypasses normal QuerySet result caching; the verifier observes two database executions across two iterator passes.

Use count/exists when that is the information needed, but consider the full flow. A fresh exists followed by later iteration can cause two queries, while an already-evaluated result cache may satisfy some operations without another query. The tests deliberately use fresh QuerySets for their count/exists case.

### SQL is still the mechanism

The verifier uses a database execution wrapper and confirms adversarial title text is a bound parameter, not interpolated SQL. Standard ORM lookup values are parameterized; concatenated raw SQL/expressions still need care. Do not treat str(query) output as evidence of how parameters were bound at execution. Reference: [Django security](https://docs.djangoproject.com/en/5.1/topics/security/).

Q expressions compose conditions such as OR. F expressions refer to database field values, enabling updates such as revision = revision + 1 in SQL. They do not automatically refresh an already-loaded Python object or create a larger multi-row transaction.

---

## 12.6 N+1 queries, joins and prefetching

N+1 is a query-shape problem: one query loads a collection, then accessing a relation causes another query for each item. A serializer/template can trigger those accesses implicitly.

The fixture has six alpha tasks. The first experiment reads each task's project name and owner username. That is one task query plus six project and six owner fetches in the naive path, even though some rows share the same project/owner.

select_related joins suitable single-valued relations such as ForeignKey/OneToOne and populates those objects from the query. prefetch_related executes separate related queries and joins the results in Python, suitable for many-to-many/reverse collections. Reference: [QuerySet related loading](https://docs.djangoproject.com/en/5.1/ref/models/querysets/), [database optimization](https://docs.djangoproject.com/en/5.1/topics/db/optimization/).

### Executed excerpt: verify_orm.py

This excerpt uses that verifier's existing imports/check collector and six-row fixture; it is not a standalone script.

```python
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

```

Recorded measurements:

```json
{
  "single_valued_relations": {
    "rows": 6,
    "naive_queries": 13,
    "select_related_queries": 1
  },
  "many_to_many": {
    "rows": 6,
    "naive_queries": 7,
    "prefetch_queries": 2
  },
  "optimized_serializer_queries": 2,
  "deferred_title_queries": 7
}
```

The optimized serializer test uses select_related(project, owner) plus prefetch_related(tags) and observes two queries for its six-row serialization. This excludes authentication, pagination and other endpoint work; it is not the total query count of the HTTP list request.

### Optimization can introduce another problem

only/defer can reduce initial selected columns but cause extra queries when deferred fields are later accessed. The verifier's only(id) followed by title reads issues seven queries for six tasks. Optimize for what the actual serializer/template consumes.

A filtered related-manager query can differ from the prefetched access pattern and execute again. Prefetching everything can also use too much memory or disclose relationships that were not correctly scoped. The API uses a tenant-filtered Prefetch for tags.

Fewer queries are not automatically lower latency: joins increase row width, large prefetch sets use memory, and indexes/data distribution affect costs. This chapter measures query counts and equivalent returned values, not throughput, execution plans or universal performance rankings.

---

## 12.7 Validation, serialization and the database are separate boundaries

A DRF serializer converts input into validated_data and converts instances into output representations. is_valid performs configured validation; save calls create/update behavior. A ModelSerializer derives useful fields/behavior from a model, but it is not a database transaction or a tenant permission policy. Reference: [DRF serializers](https://www.django-rest-framework.org/api-guide/serializers/).

| Boundary | Question |
| --- | --- |
| Parser | Can this media/body be interpreted? |
| Serializer | Are allowed fields and values valid under this input contract? |
| Authentication/permissions | Who is acting; may they do it to this object? |
| Service | Which business transition is allowed? |
| Database | Which shared invariants/relationships must always hold? |
| Output representation | Which fields/related rows may be disclosed? |

### Complete serializer: work/serializers.py

```python
from collections.abc import Mapping
from rest_framework import serializers
from .models import Task, Project

class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='label')
    class Meta:
        model = Task
        fields = ['id','project','project_name','owner_name','title','status','revision','tags','created_at']
        read_only_fields = ['id','status','revision','created_at']
        # Domain uniqueness also has a DB constraint; duplicates are mapped in the view.
        validators = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.fields['project'].queryset = (Project.objects.filter(tenant_id=request.auth.tenant_id)
                                          if request and request.auth else Project.objects.none())

    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            raise serializers.ValidationError('Expected a JSON object')
        writable = {name for name, field in self.fields.items() if not field.read_only}
        forbidden = set(data) - writable
        if forbidden:
            raise serializers.ValidationError({name:'Unknown or server-managed field' for name in sorted(forbidden)})
        return super().to_internal_value(data)
```

Only project and title are writable. The related project field's queryset is scoped to the authenticated membership's tenant. Owner is assigned by perform_create; status/revision changes belong to the completion service. Tags and derived names are read-only.

The custom to_internal_value rejects unknown and server-managed input fields. This is intentional: the framework test demonstrates that a simple default serializer can ignore unknown/read-only input and coerce an integer title to text. Do not transfer M11's strict Pydantic policy to every DRF field merely because both are called serializers/models.

Recorded default-serializer observation:

```json
{
  "numeric_title_coerced": "123",
  "unknown_and_readonly_ignored": true
}
```

Use explicit field lists rather than publishing every model field automatically. Fields/source traversal can create N+1 queries, and related querysets can become authorization paths. Review both the input and output sides.

### save does not call full_clean automatically

The ORM test saves an 81-character title through a model directly. SQLite accepts the oversized varchar value in this configuration, but explicit full_clean rejects it. The fixture transaction is rolled back afterwards. In contrast, the real HTTP serializer rejects that oversized title before saving.

Database checks/uniqueness still reject the specific invalid writes they enforce. Model field validation, serializer validation and DB constraints overlap but are not identical. Reference: [model instance validation](https://docs.djangoproject.com/en/5.1/ref/models/instances/).

Bulk/query updates do not behave like calling every model instance's save method. Do not place a critical invariant only in a save override or signal while leaving other writers able to bypass it; decide which database/application boundary owns it.

---

## 12.8 Authentication, sessions, permissions and tenant scope

Authentication identifies the caller and attaches request.user/request.auth. Permissions decide whether the request or object operation is allowed. Query scoping determines which rows can be found. Those mechanisms complement each other; none automatically substitutes for all the others.

### Complete local credential fixture: work/authentication.py

```python
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .models import Membership

# Public opaque fixtures; no JWT, password verification or production token store.
TOKENS = {b'alice-demo':('alice','alpha'), b'bob-demo':('bob','alpha'),
          b'reader-demo':('reader','alpha'), b'eve-demo':('eve','beta')}

class FixtureBearer(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts)!=2 or parts[0].lower()!=b'bearer' or parts[1] not in TOKENS:
            raise AuthenticationFailed('Invalid fixture credential')
        username, tenant = TOKENS[parts[1]]
        try:
            user = get_user_model().objects.get(username=username, is_active=True)
            membership = Membership.objects.select_related('tenant').get(user=user, tenant__slug=tenant)
        except (get_user_model().DoesNotExist, Membership.DoesNotExist):
            raise AuthenticationFailed('Invalid fixture credential')
        return user, membership
    def authenticate_header(self, request):
        return 'Bearer'
```

These public opaque values select a fixture user/tenant pair. Each request still checks the current active user and database membership; tests reject an inactive user and a removed membership. This is not a JWT verifier, password/login flow, refresh-token system or production credential store.

The authenticate_header method supplies a Bearer challenge for authentication failures. DRF's 401/403 behavior depends on authentication/permission classes and their challenge semantics; do not memorize one status for every authentication setup. Reference: [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/).

### View permission versus object permission

Complete permission source:

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS

class WorkspaceRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth and (request.method in SAFE_METHODS or request.auth.role=='editor'))

class OwnerForWrite(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.owner_id==request.user.id
```

WorkspaceRole handles read versus editor write capability at the view level. OwnerForWrite restricts writes to the object's owner. Tenant visibility is handled by get_queryset and related-field querysets, not by those two permission methods alone.

| Operation | Required mechanism in this API |
| --- | --- |
| List | Authenticated membership; tenant-filtered queryset |
| Retrieve | Same scoped queryset; generic object-permission path |
| Create | Editor role; tenant-scoped project input; owner bound server-side |
| Update/delete | Scoped object lookup plus owner-write permission |
| Complete custom action | get_object plus owner permission, then scoped service transition |
| Related tags | Tenant-filtered prefetch; writers also need semantic checks |

DRF does not normally run object permissions for every row of a list. Generic object permissions also are not automatically a create-time check on an object that does not exist yet. Enforce list scoping, related-object input rules and creation policy explicitly. Reference: [DRF permissions and their limitations](https://www.django-rest-framework.org/api-guide/permissions/).

If you override get_object or perform a manual lookup in a custom view, preserve the object-permission check. The completion action uses self.get_object deliberately; the HTTP tests reject another owner's action and hide another tenant's object.

### Session authentication and CSRF

Browser session cookies can be attached automatically, so unsafe session-authenticated requests need CSRF protection. DRF's SessionAuthentication enforces CSRF for its authenticated unsafe requests; merely seeing CsrfViewMiddleware in settings is not a complete account of every DRF path.

The in-process test uses APIClient(enforce_csrf_checks=True) and force_login to establish a real Django session fixture. A POST without a CSRF token fails; a token obtained from the session probe permits the POST. force_login bypasses password verification for the test and is not evidence of a real login implementation.

Recorded result:

```json
{
  "missing_token": 403,
  "valid_token": 200
}
```

The task API uses its fixture bearer class; the separate session probe tests SessionAuthentication without doing business writes. No browser interaction, production cookie/TLS deployment or password verification is claimed. Credential transport and endpoint policy determine CSRF exposure; a framework name does not decide it.

---

## 12.9 APIView, generic views, ViewSets and routers

| Abstraction | What it adds |
| --- | --- |
| Django view | HttpRequest to HttpResponse coordination |
| DRF APIView | API dispatch, request/response handling, authentication/permission/error integration |
| GenericAPIView plus mixins | Reusable queryset/serializer/object lookup and CRUD behavior |
| ModelViewSet | Common create/list/retrieve/update/partial_update/destroy actions |
| Router | URL/action registration conventions |
| Custom action | Additional explicitly routed operation, with its own policy |

A router organizes routes; it does not authorize them. A ModelViewSet exposes multiple behaviors, so review the entire action surface instead of checking one GET. References: [generic views](https://www.django-rest-framework.org/api-guide/generic-views/), [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/), [routers](https://www.django-rest-framework.org/api-guide/routers/).

### Complete view source: work/views.py

```python
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import JsonResponse
from django.middleware.csrf import get_token
from rest_framework import viewsets, permissions, authentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Task, Tag
from .serializers import TaskSerializer
from .permissions import WorkspaceRole, OwnerForWrite
from .services import complete_task

class TaskPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 5

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, WorkspaceRole, OwnerForWrite]
    pagination_class = TaskPagination

    def get_queryset(self):
        return (Task.objects.filter(project__tenant_id=self.request.auth.tenant_id)
                .select_related('project','owner').prefetch_related(
                    Prefetch('tags', queryset=Tag.objects.filter(tenant_id=self.request.auth.tenant_id)))
                .order_by('id'))

    def _save(self, serializer, **extra):
        try:
            with transaction.atomic():
                serializer.save(**extra)
        except IntegrityError:
            # After the failed atomic block, recognize the known title conflict.
            instance = serializer.instance
            project = serializer.validated_data.get('project', getattr(instance,'project',None))
            title = serializer.validated_data.get('title', getattr(instance,'title',None))
            duplicate = Task.objects.filter(project=project, title=title)
            if instance is not None:
                duplicate = duplicate.exclude(pk=instance.pk)
            if duplicate.exists():
                raise ValidationError({'title':'Already used in this project'})
            raise  # Unknown integrity failures remain server errors.

    def perform_create(self, serializer):
        self._save(serializer, owner=self.request.user)

    def perform_update(self, serializer):
        self._save(serializer)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()  # Scoped lookup plus object permission check.
        if not isinstance(request.data, dict) or request.data:
            raise ValidationError('Expected an empty JSON object')
        changed = complete_task(task_id=task.pk, tenant_id=request.auth.tenant_id, owner_id=request.user.id)
        task.refresh_from_db()
        return Response({'changed':changed,'status':task.status,'revision':task.revision})

def health(request):
    return JsonResponse({'status':'ok','framework':'django-drf'})

class SessionProbe(APIView):
    """No business writes; demonstrates real session authentication/CSRF enforcement."""
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response({'csrf':get_token(request)})
    def post(self, request):
        return Response({'accepted':True})
```

### Trace task creation

1. Middleware attaches a request ID; routing selects the ViewSet's create action.
2. DRF authentication resolves the active fixture user and membership.
3. Permissions reject a viewer's write before creating data.
4. The serializer accepts only project/title and resolves project through its tenant-scoped queryset.
5. perform_create passes owner=request.user; the client cannot select the owner.
6. The save runs in an atomic block, with the database's uniqueness constraint as the final shared-state guard.
7. A known project/title conflict is recognized after the failed block rolls back and mapped to a validation response. Unknown integrity errors remain server errors.
8. The serializer/renderer constructs the public 201 representation.

The view catches IntegrityError outside the inner atomic block, so its follow-up conflict query does not run inside a broken transaction. The conflict check is only error mapping; the DB constraint is what rejects the duplicate.

### Update and completion are different actions

PATCH can update allowed supplied fields while retaining omitted required fields. PUT follows this serializer's full-update requirements, and the test rejects PUT without project. Neither spelling authorizes a write by itself.

Direct status/revision assignment is rejected. complete is a business transition with an empty-object input contract. It calls get_object for the scoped lookup/permission check and then the service for the atomic state change. A custom action that queries Task.objects.get unscoped would bypass this design.

### Pagination bounds output, not the whole workload

This API uses ordered page-number pagination with a default page size and cap. The HTTP suite observes six alpha records, two IDs on the first page, the next two on page two, and a capped five-row response for an oversized page-size request.

Recorded first-page shape:

```json
{
  "count": 6,
  "first_page_ids": [
    1,
    2
  ]
}
```

Pagination still has count/query/serialization costs, and deep offset pages can be expensive at scale. Page-number, limit-offset and cursor approaches have different navigation/stability trade-offs; M6 supplies the broader API reasoning. Reference: [DRF pagination](https://www.django-rest-framework.org/api-guide/pagination/).

---

## 12.10 Transactions, conditional updates and on_commit

Django uses autocommit by default. atomic groups database operations; an error leaving a block triggers rollback of that block's work. Nested blocks ordinarily use savepoints. The database backend still determines locking/isolation behavior. Reference: [Django transactions](https://docs.djangoproject.com/en/5.1/topics/db/transactions/).

### Complete business transition: work/services.py

```python
from django.db import transaction
from django.db.models import F
from .models import Task, AuditEvent

@transaction.atomic
def complete_task(*, task_id, tenant_id, owner_id, after_commit=None, fail_after_update=False):
    # One conditional SQL UPDATE determines the transition. This is not a row-lock demo.
    changed = Task.objects.filter(pk=task_id, project__tenant_id=tenant_id,
                                  owner_id=owner_id, status='todo').update(
                                      status='done', revision=F('revision')+1)
    if changed:
        if fail_after_update:
            raise RuntimeError('injected before audit insert')
        AuditEvent.objects.create(task_id=task_id, kind='completed')
        if after_commit:
            transaction.on_commit(lambda: after_commit(task_id))
    return bool(changed)
```

The SQL predicate includes task ID, tenant, owner and todo status. One conditional UPDATE determines whether this request actually transitions the row; F increments revision in the database. The audit insert is inside the same transaction. A sequential retry after done changes nothing and adds no second audit/callback.

The transaction suite injects a failure after the update but before audit insertion and confirms status/revision roll back and no audit exists. The separate database constraints reject invalid direct writes and duplicate event kinds.

Actual HTTP completion observations:

```json
{
  "first_completion": {
    "changed": true,
    "status": "done",
    "revision": 1
  },
  "repeated_completion": {
    "changed": false,
    "status": "done",
    "revision": 1
  }
}
```

These tests establish the local transaction and sequential retry behavior. They do not exercise competing writers, PostgreSQL isolation, worker crashes, distributed delivery or a full task-state reconciliation scheme.

### Database state and Python state can disagree after a write/rollback

A QuerySet update does not refresh an instance already loaded in memory. The test increments revision through F, observes the old instance value, then refreshes it from the database.

Similarly, rolling back a transaction does not rewind attributes on a Python object you mutated. The suite observes an in-memory done value while a fresh DB read returns todo, then refreshes the instance. Do not publish/log an unrefreshed object as proof of committed state.

### on_commit schedules a callback after success; it is not durable dispatch

A callback registered inside atomic runs after the outer transaction commits. Callbacks registered in rolled-back work are discarded. The suite tests both and also confirms an inner savepoint can roll back while the outer transaction continues.

Most importantly, a failing on_commit callback cannot undo the already-committed database change. The verifier deliberately fails one and observes the task and audit already persisted:

```json
{
  "database_committed": true,
  "callback_failed": true
}
```

If a notification/job matters, do not assume on_commit alone guarantees it will be delivered. A process can stop after commit and before/during callback execution. M9's durable outbox addresses the dispatch-intent gap; an on_commit hook can be a best-effort wake-up, with a recoverable dispatcher reading persisted intent.

### select_for_update requires the actual backend

On PostgreSQL, row-locking queries can be part of a transactional design; details require the real engine and isolation policy. On this SQLite backend, the feature flag is false and the verifier observes no FOR UPDATE emitted. Calling that method here is not evidence of PostgreSQL locking correctness. Reference: [SQLite backend limitations](https://docs.djangoproject.com/en/5.1/ref/databases/#sqlite-notes).

```json
{
  "supported": false,
  "for_update_emitted": false
}
```

The completion service deliberately uses a conditional UPDATE rather than presenting an ineffective SQLite row-lock example. Even then, a production concurrency claim needs engine-specific competing-transaction tests. M13 will move to PostgreSQL's actual connection/transaction/query behavior.

---

## 12.11 Architectural understanding: build a small team task system

The runnable API already implements a narrow slice: tenant membership, projects/tasks/tags, scoped CRUD, owner-write policy and an atomic completion/audit transition. It is not a complete project-management product.

A useful extension exercise is a team task system with assignments, notifications and status history. Start with invariants before adding framework components.

| Invariant | Owning boundary |
| --- | --- |
| A caller sees only permitted workspace/project data | Authentication, membership and scoped query paths |
| Client input cannot select arbitrary owner/tenant/status | Serializer and server-assigned fields |
| A completion transition has its matching event | Transaction and database constraints |
| Concurrent edits do not silently erase a required version | Explicit optimistic version/locking policy |
| A committed notification intent can be recovered | Durable outbox/job ownership |
| Read endpoints stay within a resource budget | Query shape, pagination, indexes and measured access plans |

### Draw the build path

```text
HTTP server -> Django middleware -> DRF router/ViewSet
                                  |
                        identity and permission rules
                                  |
                     serializer / related object scope
                                  |
                          application service
                                  |
                     transaction + constraints
                         /                 \
                 task/history          outbox intent
                                             |
                                      dispatcher/queue
                                             |
                                    notification worker
```

The runnable code covers task persistence and a simple audit record. It does not implement the outbox/queue/notification half. The diagram is a proposed extension, not a deployed resume-project claim.

### Extend in a reviewable order

1. **Define policy:** workspace membership, project membership, read/write roles and assignment rules. Decide whether peers can read each other's tasks; the current example allows same-tenant reads.
2. **Strengthen shared data:** add the necessary constraints/indexes and migration/backfill strategy. Plain FK existence does not enforce every cross-tenant relation rule.
3. **Define concurrent editing:** current ordinary PATCH has no optimistic version check. If lost updates matter, make the expected revision part of the contract and perform a conditional write, or use verified locking on the target database.
4. **Persist notification intent:** save the event/outbox intent with the business transition, then let a recoverable worker deliver it idempotently.
5. **Optimize measured reads:** align related loading with serializer fields and pagination. Move heavy exports/processing into bounded worker paths.
6. **Verify failures:** duplicate requests, peer/cross-tenant access, conflicting edits, rollback before event insertion, restart after commit and notification retries.

### Failure prompt: status changed, notification failed

An on_commit callback failure leaves the task update committed, as the test demonstrates. Returning an error at that point can make the client retry even though the transition already occurred. A stable state/action contract plus persisted delivery intent lets the application report/repair the two outcomes separately.

### Failure prompt: list permissions look correct, detail leaks data

A scoped list does not protect an unscoped custom detail/action lookup. The current ViewSet derives its queryset from trusted membership and uses get_object for the action. A future export/search/background worker must preserve the same ownership policy through its own data path.

### Failure prompt: permission checks are correct but the endpoint is slow

Serializers may lazily fetch project, owner and tags for every task. Capture actual queries, inspect the values accessed, apply suitable select/prefetch/projection, and then measure latency/query plans on real data. Adding a cache before understanding the query/policy can cache an authorization mistake.

---

## 12.12 Choosing Django and connecting it to the resume

Django is useful when an application benefits from integrated ORM/migrations, user/admin conventions and a consistent ecosystem for data-backed workflows. DRF adds reusable API patterns. Flask or FastAPI can offer a different balance of explicit composition, typed API declaration and execution model, as M11 showed.

| Decision | Questions to defend |
| --- | --- |
| Integrated components | Which Django conventions saved real work? |
| Data model | Why these relationships/constraints instead of duplicated state? |
| API abstraction | Why ViewSet/generic views instead of a custom APIView? |
| Query behavior | What SQL/query count does the serializer actually cause? |
| Authorization | Where are tenant, related-object and owner rules enforced? |
| Work lifetime | Which work belongs in the request versus a durable worker? |
| Database | Which engine-specific behaviors were verified? |

A useful resume explanation is: requirement -> URL/action trace -> serializer/policy -> database operation -> failure behavior -> evidence. Explain the framework actually used. Do not infer that a resume project used a ViewSet, row locks, optimized prefetches or an outbox merely because this module teaches them.

The tested server is development/test WSGI, the credentials are public fixtures, and the database is SQLite. Core Django offers async support, but this pinned synchronous DRF path was not an ASGI/async benchmark. When a role asks about async Django, explain sync/async adaptation, safe ORM access and transaction boundaries for the installed release instead of treating async def as automatic offload.

---

## 12.13 Must remember

1. Django, DRF, the application server and database have different responsibilities.
2. Project/app and router/ViewSet organize code; they do not imply process or tenant isolation.
3. A model declaration, serializer rule and database constraint are different enforcement points.
4. makemigrations records model-state changes; migrate applies migration history to a selected DB.
5. QuerySets are usually lazy until evaluation/terminal operations; caching belongs to a particular QuerySet.
6. Serializers/templates can trigger hidden relation queries; measure the complete access pattern.
7. select_related and prefetch_related solve different relation-loading shapes.
8. Default serializer coercion/read-only handling is a policy, not identical to strict Pydantic validation.
9. Object permissions do not automatically filter lists or authorize creation.
10. Related-object input and output loading both need trusted tenant scope.
11. atomic protects database operations; it does not rewind Python object attributes.
12. on_commit is after-commit execution, not a durable notification guarantee.
13. Backend row-locking/isolation claims need the actual database; SQLite does not verify PostgreSQL FOR UPDATE.
14. Correctness, query counts, latency and distributed recovery are separate evidence categories.

---

## 12.14 Common wrong answers

| Wrong answer | Better explanation |
| --- | --- |
| DRF replaces Django | It builds API abstractions on Django |
| Every Django view renders an HTML template | API views can produce data responses without templates |
| A Django app is a separate server | It is an application/domain organization unit |
| Declaring a model updates the existing database immediately | Migration generation/application establish schema changes |
| makemigrations compares models directly to all live table details | It reasons from models and migration state/history |
| Model save always runs full_clean | It does not automatically perform full model validation |
| All QuerySet operations are lazy | Terminal reads/writes and evaluation execute work |
| QuerySet caching is global and always fresh | It is local to that evaluated object and can be stale |
| ORM use means no N+1 problem | Relation access in serializers/templates can cause it |
| select_related works identically for every many-to-many collection | Prefetch normally handles those collection shapes |
| only always improves performance | Accessing deferred fields can introduce extra queries |
| A ModelSerializer automatically rejects every unknown/read-only input | Default behavior can ignore it; this example adds explicit rejection |
| Object permissions filter every list row | Lists need explicit queryset filtering |
| Create automatically checks the new object's object permission | Creation policy/related scope/server assignment need explicit enforcement |
| Foreign keys prove same-tenant ownership | They establish references; semantic ownership can require more |
| A router adds authorization | It adds URL/action registration |
| atomic rewinds a mutated Python object | It rolls back DB work; refresh/reset Python state deliberately |
| on_commit makes enqueue/delivery durable | The process can fail after commit and before callback completion |
| select_for_update on SQLite proves production row locks | This backend does not emit the locking clause here |
| F refreshes every loaded model instance | A SQL update does not automatically refresh those objects |
| Adding async def makes every DRF/ORM path non-blocking | Verify core/framework/library execution and supported APIs |

---

## 12.15 Interview Q&A

These are selected fundamentals and follow-ups for Django backend work, not measured company-question frequency rankings.

**Q1. What is Django, and why add DRF?**

Django supplies an integrated web framework and data/application tooling. DRF adds API-oriented requests, serializers, views, permissions and pagination. DRF runs on Django; the server and database still have separate responsibilities.

**Follow-up:** Which parts would a plain JsonResponse view lack automatically?

**Q2. Explain Django's MVT structure.**

Models represent persisted data/ORM behavior, views coordinate requests and templates render presentation. The view handles much of MVC's controller responsibility. JSON APIs do not require an HTML template for every endpoint.

**Follow-up:** Where should a multi-write business transition live?

**Q3. Project versus app?**

A project contains deployment/application configuration such as settings and root URLs. An app organizes a domain/responsibility and its components. Neither app naming nor a package boundary creates an independent process or service.

**Follow-up:** Why can multiple apps share one database/application deployment?

**Q4. Trace an HTTP request to a DRF action.**

The server invokes Django, middleware wraps the request, URL resolution selects the view, DRF dispatch resolves authentication/permissions and the action handles serializers/queries/services. A Response is rendered and returns through middleware to the server.

**Follow-up:** At what point does this fixture's DRF bearer principal exist?

**Q5. Why does middleware order matter?**

Middleware can depend on state established earlier and can short-circuit or wrap later work. For example, session state is needed by Django authentication integration. Error/response processing is not a substitute for domain permission checks.

**Follow-up:** Is a request ID evidence that the user is authenticated?

**Q6. What do URLconf, include, reverse and a router do?**

URLconf maps paths to views; include delegates routing; reverse builds named URLs. DRF routers register ViewSet action conventions. These help organization/coupling, not authorization.

**Follow-up:** How does PATCH map to partial_update in the tested router?

**Q7. Model definition versus database schema?**

The model is Python metadata/behavior describing persisted structures. Migrations record schema-state changes and apply them to a selected database. The database ultimately enforces the constraints it actually has.

**Follow-up:** What happens if code changes but the migration is not applied?

**Q8. makemigrations versus migrate?**

makemigrations generates change operations from model/migration state. migrate applies the dependency graph to a database. Review history/operations and detect both missing migration files and unapplied migrations.

**Follow-up:** Why must data migrations use the relevant historical model state?

**Q9. Does save validate the whole model?**

It does not automatically call full_clean. The example directly saves an oversized title that SQLite accepts, while full_clean and the HTTP serializer reject it. DB constraints enforce their own distinct rules.

**Follow-up:** Why is a save override alone a weak shared-state invariant?

**Q10. What does QuerySet laziness mean?**

Many operations build/refine a query description before SQL executes. Evaluation and terminal reads/writes cause database work. Iteration, len, bool, list and some debugging operations can cross that boundary.

**Follow-up:** Why can logging a QuerySet unexpectedly issue a query?

**Q11. How does QuerySet caching work?**

An evaluated QuerySet can reuse its own results. That is not a global cache or proof of current database state. A fresh clone/query can execute again; iterator bypasses ordinary result caching.

**Follow-up:** What did the zero-query repeat versus one-query clone test establish?

**Q12. get versus filter, count versus len, exists versus bool?**

get asks for one instance and can raise for zero/multiple matches; filter describes a collection. count/exists can answer targeted questions without loading every object, while len/bool can evaluate results. Consider whether the same data is needed afterwards.

**Follow-up:** When can an exists check followed by iteration add unnecessary work?

**Q13. What is N+1, and how would you find it?**

A collection fetch is followed by relation fetches per item. Capture actual queries while exercising the serializer/template access pattern, then compare returned values and query counts after an appropriate loading change.

**Follow-up:** Why did six tasks produce 13 queries in the FK example?

**Q14. select_related versus prefetch_related?**

select_related uses suitable SQL joins for single-valued relations. Prefetch performs separate queries and associates collection results in Python. Match the method to relationship shape and scoped access requirements.

**Follow-up:** Why did prefetching tags use two queries instead of one?

**Q15. Can only or defer make things slower?**

Yes, if later code accesses deferred fields and triggers additional per-instance queries. The only(id) example reads six titles and issues seven queries. Optimize for actual field usage rather than a smaller initial SELECT alone.

**Follow-up:** What other resource cost can large prefetching introduce?

**Q16. Serializer versus ModelSerializer?**

A Serializer declares adaptation/validation explicitly. ModelSerializer derives useful fields and create/update behavior from a Django model. It still needs a reviewed input/output field policy, related querysets and authorization boundaries.

**Follow-up:** What does serializer.save do after is_valid?

**Q17. Are DRF serializers strict like the previous Pydantic model?**

Not automatically. Field coercion and unknown/read-only handling depend on configuration/implementation. The simple serializer test converts a numeric title to text and ignores other fields; the task serializer deliberately adds rejection rules.

**Follow-up:** Why should server-managed fields be an explicit policy?

**Q18. DRF Request/Response versus Django's objects?**

DRF wraps HttpRequest with API parsing/authentication conveniences and holds response data for renderer selection. A Django JsonResponse can emit JSON but does not automatically provide DRF's serializer/permission/dispatch behavior.

**Follow-up:** When is request.data parsing triggered in your action?

**Q19. APIView versus generic views versus ModelViewSet?**

APIView gives explicit API dispatch; generics/mixins provide common queryset/serializer/CRUD behavior; ModelViewSet bundles standard actions for router registration. Choose the abstraction that keeps policy and behavior understandable.

**Follow-up:** Which extra operations become exposed by choosing a full ModelViewSet?

**Q20. Authentication versus authorization in DRF?**

Authentication establishes user/auth context. View/object permissions decide allowed actions. Scoped querysets decide visible rows, and related-field querysets constrain input references. Use all relevant layers for the domain policy.

**Follow-up:** What does authenticate_header change about this fixture's failures?

**Q21. Why are object permissions insufficient for list endpoints?**

They are not normally invoked for every returned list row. Filter the queryset by trusted tenant/ownership policy. Keep detail/custom-action lookups scoped as well rather than protecting one route only.

**Follow-up:** Where would an unscoped export leak the same data?

**Q22. How do you protect creation and related object assignment?**

Authorize the create action, constrain related querysets to trusted scope and assign identity-owned fields server-side. There is no existing object for a generic create-time object-permission check to protect automatically.

**Follow-up:** How does this serializer reject a project from beta?

**Q23. How does session authentication interact with CSRF?**

Unsafe authenticated browser-session requests need CSRF protection because cookies can be attached automatically. DRF SessionAuthentication enforces its policy; the test enables CSRF checks explicitly and uses a real session fixture plus token.

**Follow-up:** What does force_login prove, and what does it bypass?

**Q24. What does pagination solve?**

It bounds/manages result delivery and navigation under a defined ordering. It does not eliminate count/query cost, tenant filtering or expensive deep offsets. Choose page/offset/cursor behavior for the public contract.

**Follow-up:** How can inserts affect page-number navigation between requests?

**Q25. What does atomic do, including nesting?**

It groups database work and rolls back failed blocks. Nested blocks ordinarily use savepoints, allowing an inner rollback while the outer transaction can continue if errors are handled outside the inner block. Backend semantics still matter.

**Follow-up:** Why catch the integrity failure outside the failed inner atomic block?

**Q26. Why use F expressions, and what stays stale?**

They express field-based computation in SQL, avoiding a Python read/increment/write for that update. Already-loaded Python instances are not automatically refreshed, and rollback does not rewind mutated attributes.

**Follow-up:** When would you call refresh_from_db?

**Q27. Is on_commit a reliable queue?**

No. It runs callbacks after commit, discards rolled-back registrations and can fail after business state has committed. Important delivery needs durable intent/ownership and recovery, such as an outbox.

**Follow-up:** Why can a callback error make a client retry an already-completed transition?

**Q28. What does select_for_update guarantee here?**

On the tested SQLite backend it emits no FOR UPDATE and does not establish PostgreSQL row locks. Lock/isolation claims require the target engine and competing-transaction tests. The service uses a conditional UPDATE and verifies local sequential behavior.

**Follow-up:** What would you verify when moving this transition to PostgreSQL?

**Q29. Does Django async support make every DRF view and ORM call non-blocking?**

No. Core support, middleware adaptation, extension dispatch, client libraries and ORM/transaction APIs must be assessed for the installed version. This chapter's HTTP evidence is a synchronous DRF WSGI path, not an async benchmark.

**Follow-up:** Where would a blocking operation affect an ASGI loop?

**Q30. How would you defend Django for a team-task project?**

Explain the requirements, integrated components chosen, one URL-to-query/service flow, authorization boundaries and a measured failure/performance case. Distinguish the actual implementation from proposed jobs, concurrency control or architecture improvements.

**Follow-up:** Which evidence would justify claiming the endpoint is correct and fast?

---

## 12.16 Practice tasks and answer checkpoints

### 1. Recreate the request trace

Draw GET /api/tasks/ and POST /api/tasks/2/complete/ from the server through Django/DRF to SQL and the response. Mark authentication, view permission, object permission and transaction boundaries.

**Checkpoint:** Lists need tenant-filtered querysets; completion uses get_object and a service. Middleware correlation does not establish the DRF principal.

### 2. Review a migration change

Propose adding a required task priority to an existing large table. Describe model state, migration operations, backfill and compatible application rollout.

**Checkpoint:** Do not assume generating a migration applies it or guarantees zero downtime. Consider staged enforcement, historical models and the target backend's DDL/locking behavior.

### 3. Predict QuerySet execution

Before running verify_orm.py through the aggregate runner, predict which construction, repeated iteration, clone, count/exists and iterator operations cause queries.

**Checkpoint:** Distinguish one evaluated object's cache from a fresh query and from uncached iterator access. Explain why later writes need not update the old results.

### 4. Change a serializer's data needs

Add a related field to task output and capture the new query count before optimizing it. Compare actual values between naive and optimized paths.

**Checkpoint:** Choose select_related versus prefetch for the relationship and access pattern. Query count alone is not a latency benchmark or authorization policy.

### 5. Protect writable tag assignment

Extend creation/update to accept tag IDs. Attempt an alpha task with a beta tag, duplicate IDs and nonexistent IDs.

**Checkpoint:** Scope the writable related queryset and define validation/transaction behavior. Existing foreign keys and output filtering do not establish a valid stored same-tenant relation by themselves.

### 6. Add an export action safely

Design a CSV export of filtered tasks with an explicit resource budget and ownership policy. Decide whether it should be a request response or durable job.

**Checkpoint:** Reuse the authorized data scope, bound rows/memory/time and define worker ownership if asynchronous. A new custom lookup can bypass the existing ViewSet safeguards if careless.

### 7. Add concurrent-edit control

Current PATCH has no expected-version contract. Design one using revision/If-Match or a documented alternative, and define a stale-write response.

**Checkpoint:** The expected version must participate in the actual shared-state transition. Merely displaying revision in JSON does not prevent lost updates. Verify on the target database.

### 8. Extend the failure injection

Fail after the task update and before the audit write, then fail an after-commit delivery attempt. Compare persisted state and client retry implications.

**Checkpoint:** The first failure rolls back the transaction. The second occurs after business commit; it needs recoverable dispatch/reconciliation rather than pretending the DB rolled back.

### 9. Move the transaction to PostgreSQL

List the connection, migration, constraint, competing-transaction and query-plan checks you need before making production locking/performance claims.

**Checkpoint:** SQLite's passing tests do not establish PostgreSQL row locks, isolation or SQL plans. M13 provides the engine-specific next step.

### 10. Defend one real resume request

Explain a Django/DRF request actually present in your project, its validation/permission/data path and one failure case. Identify which improvements from these notes are only proposals.

**Checkpoint:** Ground claims in available code/tests and measurement. Do not invent a ViewSet, optimized query count, outbox or benchmark for a project whose evidence does not show it.

---

## 12.17 Exit checklist

- [ ] I can distinguish Django, DRF, WSGI/ASGI server and database responsibilities.
- [ ] I can explain MVT and project/app organization.
- [ ] I can trace URL resolution, middleware, DRF dispatch and rendering.
- [ ] I can explain model state, migrations and actual schema application.
- [ ] I can distinguish serializer validation, model validation and DB constraints.
- [ ] I can predict QuerySet evaluation/cache/clone behavior.
- [ ] I can measure and repair a serializer's N+1 access pattern.
- [ ] I can explain select_related, prefetch_related, values, Q and F.
- [ ] I can review deferred-field and prefetch memory/query trade-offs.
- [ ] I can implement view/object permissions without missing lists/creation.
- [ ] I can scope related input and output to trusted tenant context.
- [ ] I can explain APIView/generics/ViewSet/router responsibilities.
- [ ] I can distinguish session authentication/CSRF from the bearer fixture.
- [ ] I can explain PATCH/PUT, pagination and business actions.
- [ ] I can reason about atomic rollback, savepoints and stale Python objects.
- [ ] I can explain why on_commit is not durable delivery.
- [ ] I can state the SQLite/production-engine boundary honestly.
- [ ] I can run the 76 checks and explain each group's evidence limits.

---

## 12.18 Sources and reproducible evidence

Research checked on **14 October 2026**. Version-matched Django 5.1 references explain the historical execution snapshot; that release is unsupported. The notes do not prescribe it for a deployment.

| Topic | Primary references |
| --- | --- |
| Framework/request flow | [Django overview](https://docs.djangoproject.com/en/6.0/intro/overview/), [URL dispatcher](https://docs.djangoproject.com/en/5.1/topics/http/urls/), [middleware](https://docs.djangoproject.com/en/6.0/topics/http/middleware/), [async support](https://docs.djangoproject.com/en/5.1/topics/async/) |
| Models/data | [QuerySets](https://docs.djangoproject.com/en/5.1/ref/models/querysets/), [model instances](https://docs.djangoproject.com/en/5.1/ref/models/instances/), [constraints](https://docs.djangoproject.com/en/5.1/ref/models/constraints/), [migrations](https://docs.djangoproject.com/en/5.1/topics/migrations/) |
| Correctness/performance | [Transactions](https://docs.djangoproject.com/en/5.1/topics/db/transactions/), [database optimization](https://docs.djangoproject.com/en/5.1/topics/db/optimization/), [SQLite notes](https://docs.djangoproject.com/en/5.1/ref/databases/#sqlite-notes), [security](https://docs.djangoproject.com/en/5.1/topics/security/) |
| DRF boundaries | [Requests](https://www.django-rest-framework.org/api-guide/requests/), [responses](https://www.django-rest-framework.org/api-guide/responses/), [serializers](https://www.django-rest-framework.org/api-guide/serializers/), [authentication](https://www.django-rest-framework.org/api-guide/authentication/), [permissions](https://www.django-rest-framework.org/api-guide/permissions/) |
| DRF organization/testing | [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/), [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/), [routers](https://www.django-rest-framework.org/api-guide/routers/), [pagination](https://www.django-rest-framework.org/api-guide/pagination/), [testing](https://www.django-rest-framework.org/api-guide/testing/) |

### Verification map

All sources/evidence are under examples/resume-skills/module-12-django-drf/.

| Group | Named checks | Actual boundary |
| --- | --- | --- |
| ORM | 15 | Real Django queries against SQLite; query-count/value/parameter checks |
| Transactions | 14 | Real DB constraints/atomic rollback/savepoints/conditional updates/callback behavior |
| Framework | 9 | Applied migration graph, URL/actions, middleware, real authentication, session/CSRF fixture and relation rules |
| HTTP | 38 | Real loopback requests to the Django/DRF WSGI application; allowed/rejected writes and sequential retries |
| Total | **76** | Named checks; some include multiple assertions/fixtures |
| Additional management checks | 3 | check, makemigrations --check --dry-run, migrate --check |

Project/implementation: manage.py, config/, work/ and the generated initial migration. Verification: fixtures.py, bootstrap.py, checks.py, verify.py and four verify-group files. Recorded evidence: group/aggregate JSON results, verification-output.txt, dependency install/check output and site/content validation artifacts.

Each group gets a fresh migrated file-backed SQLite database. The aggregate runner closes child processes before removing its verified-owned temporary directory; removal is recorded. The HTTP listener is stopped and probed closed. No production credentials, real login/password verification, external API, production server, PostgreSQL instance or durable notification worker is used.

The query measurements are fixture-specific counts, not a benchmark. Concurrency/crash recovery, ASGI serving and streamed ingress/export are not verified by this module. The DATA_UPLOAD_MAX_MEMORY_SIZE setting is not claimed as a fully tested general DRF streaming-body cap; real ingress paths need their own budget checks. The proposed task-system extensions remain design exercises.

---

## Next

Continue to [M13: PostgreSQL in a Backend](/docs/resume-skills/postgresql-backend). It connects application schemas and transactions to actual PostgreSQL connections, pools, parameterized SQL, row locking/isolation, indexes, query plans and constraints.

Revisit [M10: Python Fundamentals](/docs/resume-skills/python-fundamentals), [M11: Flask/FastAPI](/docs/resume-skills/flask-fastapi-python-request-handling), [M8: API Security](/docs/resume-skills/api-security-authorization-multi-tenancy) and [M9: Webhooks and Payments](/docs/resume-skills/webhooks-payments-reliable-integrations) for the shared execution, authorization and recovery boundaries. The [master roadmap](/docs/resume-skills) shows the remaining sections.
