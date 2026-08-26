from rest_framework.permissions import BasePermission

from accounts.models import UserRole, UserStatus


class IsAuthenticatedActive(BasePermission):
    """Authenticated and not suspended/deleted."""

    message = "Your account is not active."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and user.status == UserStatus.ACTIVE
        )


class HasRole(BasePermission):
    """Server-side RBAC gate. Subclass with `roles`."""

    roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role in self.roles or request.user.is_superuser)
        )


class IsAdmin(HasRole):
    roles = (UserRole.ADMIN, UserRole.SUPER_ADMIN)


class IsModerator(HasRole):
    roles = (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)


class IsDesigner(HasRole):
    roles = (UserRole.DESIGNER,)


class IsBrand(HasRole):
    roles = (UserRole.BRAND,)


class IsCreatorOrUser(HasRole):
    roles = (UserRole.USER, UserRole.CREATOR)
