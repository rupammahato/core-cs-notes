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
