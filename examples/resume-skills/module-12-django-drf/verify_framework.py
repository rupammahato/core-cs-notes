from bootstrap import prepare
prepare()
from django.contrib.auth import get_user_model
from django.test import Client
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import resolve, reverse
from rest_framework.test import APIClient
from rest_framework import serializers
from work.middleware import trace_log
from work.models import Task, Membership
from checks import Checks,equal,require

checks=Checks('framework')
observed={}

def migrations():
    executor=MigrationExecutor(connection)
    equal(executor.migration_plan(executor.loader.graph.leaf_nodes()),[])
    require(('work','0001_initial') in executor.loader.applied_migrations)
checks.check('initial model migration is applied with no pending migration plan',migrations)

def routes():
    equal(reverse('task-list'),'/api/tasks/')
    equal(resolve('/api/tasks/1/complete/').url_name,'task-complete')
    equal(resolve('/api/tasks/1/').func.actions['patch'],'partial_update')
checks.check('router maps URL names and HTTP actions to the ViewSet',routes)

def middleware():
    response=Client().get('/health/')
    equal(response.status_code,200)
    equal(trace_log.trace(response['X-Request-ID']),['middleware-in','view-resolved','middleware-out'])
    equal(response['Cache-Control'],'no-store')
    observed['middleware_trace']=trace_log.trace(response['X-Request-ID'])
checks.check('Django middleware wraps a resolved view and adds response metadata',middleware)

def anonymous():
    response=APIClient().get('/api/tasks/')
    equal(response.status_code,401)
    equal(response['WWW-Authenticate'],'Bearer')
checks.check('real authentication path rejects anonymous API access',anonymous)

def session():
    client=APIClient(enforce_csrf_checks=True)
    client.force_login(get_user_model().objects.get(username='alice'))  # Test login fixture, not password verification.
    equal(client.post('/session-probe/',{},format='json').status_code,403)
    response=client.get('/session-probe/')
    equal(response.status_code,200)
    token=response.data['csrf']
    equal(client.post('/session-probe/',{},format='json',HTTP_X_CSRFTOKEN=token).status_code,200)
    observed['session_csrf']={'missing_token':403,'valid_token':200}
checks.check('SessionAuthentication rejects unsafe authenticated requests without CSRF and accepts valid token',session)

def inactive():
    user=get_user_model().objects.get(username='alice')
    user.is_active=False
    user.save(update_fields=['is_active'])
    try: equal(APIClient().get('/api/tasks/',HTTP_AUTHORIZATION='Bearer alice-demo').status_code,401)
    finally:
        user.is_active=True
        user.save(update_fields=['is_active'])
checks.check('inactive credential subject rejected',inactive)

def removed_membership():
    membership=Membership.objects.get(user__username='reader')
    membership.delete()
    try: equal(APIClient().get('/api/tasks/',HTTP_AUTHORIZATION='Bearer reader-demo').status_code,401)
    finally: Membership.objects.create(user_id=membership.user_id,tenant_id=membership.tenant_id,role='viewer')
checks.check('fixture token does not bypass current database membership',removed_membership)

def default_serializer():
    class Loose(serializers.Serializer):
        title=serializers.CharField()
        status=serializers.CharField(read_only=True)
    value=Loose(data={'title':123,'status':'done','unknown':'ignored'})
    require(value.is_valid())
    equal(dict(value.validated_data),{'title':'123'})
    observed['default_serializer']={'numeric_title_coerced':'123','unknown_and_readonly_ignored':True}
checks.check('default serializer can coerce values and ignore unknown/read-only input',default_serializer)

def relation_scope():
    # Show that plain foreign keys/M2M references do not enforce tenant semantics.
    task=Task.objects.get(pk=1)
    from work.models import Tag
    beta_tag=Tag.objects.get(tenant__slug='beta')
    task.tags.add(beta_tag)
    try:
        require(task.tags.filter(pk=beta_tag.pk).exists())
        response=APIClient().get('/api/tasks/1/',HTTP_AUTHORIZATION='Bearer alice-demo')
        equal(response.status_code,200)
        require('beta-only' not in response.data['tags'])
    finally: task.tags.remove(beta_tag)
checks.check('M2M foreign keys permit cross-tenant link but API prefetch filters its disclosure',relation_scope)
checks.save(observations=observed,transport='In-process Django/DRF clients; session/CSRF uses force_login fixture')
