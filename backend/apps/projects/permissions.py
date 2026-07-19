"""
Permission classes for projects app.
See .ai/coding-rules.md: Permission checks happen server-side in DRF permission classes.
See .ai/business-rules.md: Access control by role.
"""
from rest_framework import permissions


class IsProjectOwner(permissions.BasePermission):
    """
    Only project owners can access their projects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTeamMember(permissions.BasePermission):
    """
    Only team members can access team projects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the project's team
        return obj.team.memberships.filter(user=request.user).exists()


class IsProjectOwnerOrTeamLead(permissions.BasePermission):
    """
    Project owners or team leads can perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is project owner
        if obj.owner == request.user:
            return True
        
        # Check if user is team lead
        membership = obj.team.memberships.filter(user=request.user).first()
        return membership and membership.role == 'lead'


class IsProjectOwnerOrReadOnly(permissions.BasePermission):
    """
    Project owners can edit, team members can read.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is member of the team
        if not obj.team.memberships.filter(user=request.user).exists():
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.owner == request.user


class IsProjectOwnerOrTeamLeadOrReadOnly(permissions.BasePermission):
    """
    Project owners or team leads can edit, team members can read.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is member of the team
        if not obj.team.memberships.filter(user=request.user).exists():
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is project owner or team lead
        if obj.owner == request.user:
            return True
        
        membership = obj.team.memberships.filter(user=request.user).first()
        return membership and membership.role == 'lead'
