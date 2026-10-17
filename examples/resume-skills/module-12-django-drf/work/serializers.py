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
