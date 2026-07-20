"""
Permission classes for analytics app.
See .ai/coding-rules.md: Permission checks happen server-side in DRF permission classes.
See .ai/business-rules.md BR-7.1 for data-visibility scope.
"""
from rest_framework import permissions


class IsWorkloadViewerOrAdmin(permissions.BasePermission):
    """
    Grants access to workload data based on role:
    - User can view their own workload
    - Project Manager can view workload of their team members
    - Administrator can view all workload
    - Team Member can only see aggregate team workload, not individual (enforced in views)
    BR-7.1: scope violations return 404.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is a WorkloadSnapshot
        is_self = obj.user == request.user
        is_admin = request.user.role == 'admin'
        
        # PM can view workload of their team members
        if request.user.role == 'project_manager':
            is_team_member = obj.project.team.memberships.filter(user=request.user).exists()
            if is_team_member:
                return True
        
        return is_self or is_admin


class IsRiskViewerOrAdmin(permissions.BasePermission):
    """
    Grants access to risk score data based on role:
    - Project Manager can view risk of their projects
    - Executive Manager can view all projects (read-only)
    - Administrator can view all
    BR-7.1: scope violations return 404.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is a RiskScore
        project = obj.project
        is_admin = request.user.role == 'admin'
        is_executive = request.user.role == 'executive_manager'
        is_pm_owner = project.owner == request.user
        is_pm_team = project.team.memberships.filter(user=request.user).exists()
        
        # PM can view risk of projects they own or manage
        if request.user.role == 'project_manager':
            return is_pm_owner or is_pm_team
        
        # Executive can view all projects (read-only)
        if is_executive and request.method in permissions.SAFE_METHODS:
            return True
        
        return is_admin


class IsTeamMemberOrReadOnly(permissions.BasePermission):
    """
    Grants read access to authenticated team members.
    Write access requires admin or PM role.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write operations: admin or PM only
        return request.user.role in ['admin', 'project_manager']
