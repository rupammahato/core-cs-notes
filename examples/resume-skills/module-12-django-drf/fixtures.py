from django.contrib.auth import get_user_model
from work.models import Tenant, Membership, Project, Tag, Task

def seed():
    users = {name:get_user_model().objects.create_user(username=name, password=None)
             for name in ('alice','bob','reader','eve')}
    alpha, beta = Tenant.objects.create(slug='alpha'), Tenant.objects.create(slug='beta')
    for name in ('alice','bob','reader'):
        Membership.objects.create(user=users[name], tenant=alpha,
                                  role='viewer' if name=='reader' else 'editor')
    Membership.objects.create(user=users['eve'],tenant=beta,role='editor')
    p1 = Project.objects.create(tenant=alpha,name='Core')
    p2 = Project.objects.create(tenant=alpha,name='Tools')
    p3 = Project.objects.create(tenant=beta,name='Core')
    api = Tag.objects.create(tenant=alpha,label='api')
    orm = Tag.objects.create(tenant=alpha,label='orm')
    other = Tag.objects.create(tenant=beta,label='beta-only')
    for index in range(6):
        task = Task.objects.create(project=p1 if index<3 else p2,
                                   owner=users['alice'] if index<4 else users['bob'],
                                   title='Task '+str(index+1))
        task.tags.add(api,orm) if index%2==0 else task.tags.add(api)
    task = Task.objects.create(project=p3,owner=users['eve'],title='Beta secret')
    task.tags.add(other)
