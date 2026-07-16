"""
Permission classes for role-based access control.
See .ai/coding-rules.md: Permission checks happen server-side in DRF permission classes.
See .ai/business-rules.md: Access control by role.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Only administrators can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsProjectManager(permissions.BasePermission):
    """
    Only project managers can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'pm'


class IsTeamMember(permissions.BasePermission):
    """
    Only team members can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'member'


class IsExecutive(permissions.BasePermission):
    """
    Only executive managers can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'executive'


class IsAdminOrProjectManager(permissions.BasePermission):
    """
    Administrators and project managers can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'pm']


class IsAdminOrExecutive(permissions.BasePermission):
    """
    Administrators and executive managers can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'executive']


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: only owners can edit, others can read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class IsAdminOrOwner(permissions.BasePermission):
    """
    Object-level permission: admins or owners can access.
    """
    def has_object_permission(self, request, view, obj):
        # Check authentication first
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'admin':
            return True
        return obj == request.user
