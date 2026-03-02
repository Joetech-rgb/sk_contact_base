from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Allow read-only access to everyone,
    but write access only to admin users.
    """

    def has_permission(self, request, view):
        # Read permissions for any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only for staff/admin
        return request.user and request.user.is_staff


class IsAdminUser(BasePermission):
    """
    Allow access only to admin users
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission:
    - Admins can access everything
    - Users can only access objects they own
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        return hasattr(obj, 'created_by') and obj.created_by == request.user
