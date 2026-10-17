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
