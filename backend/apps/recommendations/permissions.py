"""
Permission classes for recommendations app.
See .ai/coding-rules.md: Permission checks happen server-side in DRF permission classes.
See .ai/business-rules.md: Access control by role.
"""
from rest_framework import permissions


class IsRecommendationProjectOwner(permissions.BasePermission):
    """
    Only the project owner PM can accept or dismiss recommendations (BR-7.2).
    Team members and executives can view recommendations in SAFE_METHODS.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Safe methods: allow project owner or team members/execs depending on scope
        if request.method in permissions.SAFE_METHODS:
            is_owner = obj.project.owner == request.user
            is_team_member = obj.project.team.memberships.filter(user=request.user).exists()
            is_executive = request.user.role in ['executive_manager', 'admin']
            return is_owner or is_team_member or is_executive
            
        # Write actions (accept/dismiss): must be project owner PM (BR-7.2)
        return obj.project.owner == request.user
