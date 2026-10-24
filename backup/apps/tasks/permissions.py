from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    message = "You do not have access to this task."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or request.user.role == "admin" or obj.owner_id == request.user.id
