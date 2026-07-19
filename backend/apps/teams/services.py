"""
Business logic for teams app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
"""
from .models import Team, Skill, TeamMembership


def create_team_service(name, description=''):
    """
    Create a new team.
    """
    team = Team.objects.create(name=name, description=description)
    return team


def add_team_member_service(team, user, role='member'):
    """
    Add a user to a team with a specific role.
    """
    membership, created = TeamMembership.objects.get_or_create(
        team=team,
        user=user,
        defaults={'role': role}
    )
    
    if not created:
        membership.role = role
        membership.save()
    
    return membership


def remove_team_member_service(team, user):
    """
    Remove a user from a team.
    """
    try:
        membership = TeamMembership.objects.get(team=team, user=user)
        membership.delete()
        return True
    except TeamMembership.DoesNotExist:
        return False


def update_team_member_role_service(team, user, new_role):
    """
    Update a team member's role.
    """
    try:
        membership = TeamMembership.objects.get(team=team, user=user)
        membership.role = new_role
        membership.save()
        return membership
    except TeamMembership.DoesNotExist:
        return None


def create_skill_service(name, description=''):
    """
    Create a new skill.
    """
    skill, created = Skill.objects.get_or_create(
        name=name,
        defaults={'description': description}
    )
    return skill


def get_user_teams_service(user):
    """
    Get all teams a user is a member of.
    """
    memberships = TeamMembership.objects.filter(user=user).select_related('team')
    return [membership.team for membership in memberships]


def get_team_members_service(team):
    """
    Get all members of a team.
    """
    return TeamMembership.objects.filter(team=team).select_related('user')
