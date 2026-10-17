from rest_framework.permissions import BasePermission, SAFE_METHODS

class WorkspaceRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth and (request.method in SAFE_METHODS or request.auth.role=='editor'))

class OwnerForWrite(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.owner_id==request.user.id
