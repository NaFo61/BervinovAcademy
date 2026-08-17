from rest_framework.permissions import BasePermission


class IsMentorOrAdmin(BasePermission):
    """Доступ только менторам и администраторам."""

    message = "Доступно только менторам и администраторам."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in ("mentor", "admin")
        )


class IsAdminRole(BasePermission):
    """Доступ только администраторам школы."""

    message = "Доступно только администраторам."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "admin"
        )
