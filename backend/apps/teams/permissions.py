"""
Permission classes for teams app.
See .ai/coding-rules.md: Permission checks happen server-side in DRF permission classes.
See .ai/business-rules.md: Access control by role.
"""
from rest_framework import permissions


class IsTeamMember(permissions.BasePermission):
    """
    Only team members can access team-specific resources.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the team
        if hasattr(obj, 'team'):
            team = obj.team
        else:
            team = obj
        
        return team.memberships.filter(user=request.user).exists()


class IsTeamLead(permissions.BasePermission):
    """
    Only team leads can perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a lead of the team
        if hasattr(obj, 'team'):
            team = obj.team
        else:
            team = obj
        
        membership = team.memberships.filter(user=request.user).first()
        return membership and membership.role == 'lead'


class IsTeamLeadOrReadOnly(permissions.BasePermission):
    """
    Team leads can edit, team members can read.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the team
        if hasattr(obj, 'team'):
            team = obj.team
        else:
            team = obj
        
        membership = team.memberships.filter(user=request.user).first()
        if not membership:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return membership.role == 'lead'


class CanManageTeamMembership(permissions.BasePermission):
    """
    Only team leads can manage team memberships.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a lead of the team
        membership = obj.team.memberships.filter(user=request.user).first()
        return membership and membership.role == 'lead'
