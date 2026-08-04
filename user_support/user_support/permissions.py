from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    """
    Разрешает доступ только пользователям с is_superuser = True.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)