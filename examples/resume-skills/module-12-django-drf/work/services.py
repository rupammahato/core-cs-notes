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
