"""
Permission classes for the chat app.
See .ai/business-rules.md BR-7.1 and docs/14_REST_API.md §10.

Chat endpoints are accessible to: PM, Executive, Admin.
Team Members cannot use the chat assistant (docs/12 §5 route table).
"""
from rest_framework.permissions import BasePermission


class CanAccessChat(BasePermission):
    """
    Allows access to users with role: pm, executive, admin.
    Returns 403 for authenticated users without the right role.
    """
    allowed_roles = {'pm', 'executive', 'admin'}

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) in self.allowed_roles
        )
