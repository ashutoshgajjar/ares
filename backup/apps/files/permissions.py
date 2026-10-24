from rest_framework.permissions import BasePermission


class IsFileOwnerOrAdmin(BasePermission):
    message = "You do not have access to this file."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_superuser
            or request.user.role == "admin"
            or obj.user_id == request.user.id
        )
