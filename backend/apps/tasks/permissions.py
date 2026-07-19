"""
Permission classes for tasks app.
See .ai/coding-rules.md: Permission checks happen server-side in DRF permission classes.
See .ai/business-rules.md BR-7.1 for data-visibility scope.
"""
from rest_framework import permissions


class IsProjectMemberOrReadOnly(permissions.BasePermission):
    """
    Grants read access to any authenticated project team member.
    Write access requires the user to be the project owner (PM role)
    or a direct team member.
    BR-7.1: scope violations return 404 (handled in view querysets), not 403.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is a Task — project membership check
        project = obj.project
        is_team_member = project.team.memberships.filter(user=request.user).exists()
        is_owner = project.owner == request.user

        if request.method in permissions.SAFE_METHODS:
            return is_team_member or is_owner

        # Write operations: PM owner only
        return is_owner


class IsTaskAssigneeOrProjectOwner(permissions.BasePermission):
    """
    Allows the task's assignee and the project owner (PM) to update task status.
    See docs/14_REST_API.md §6: PATCH /tasks/{id}/status — Assignee, PM.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is a Task
        is_assignee = obj.assignee == request.user
        is_project_owner = obj.project.owner == request.user
        return is_assignee or is_project_owner


class IsProjectOwner(permissions.BasePermission):
    """
    Only the project owner (PM) may perform dependency management and task creation.
    See docs/14_REST_API.md §6: POST /tasks/{id}/dependencies — PM.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj may be a Task or a TaskDependency
        project = getattr(obj, 'project', None) or getattr(obj, 'task', None).project
        return project.owner == request.user
