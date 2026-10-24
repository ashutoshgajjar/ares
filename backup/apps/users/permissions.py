from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Administrator permissions are required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_superuser or request.user.role == "admin"))


class IsAdminOrSelf(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == "admin":
            return True
        return obj.pk == request.user.pk
