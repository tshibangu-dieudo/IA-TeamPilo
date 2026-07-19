"""
Business logic for projects app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
"""
from django.db import models
from .models import Project


def create_project_service(name, description, start_date, end_date, owner, team, status='planning'):
    """
    Create a new project.
    """
    project = Project.objects.create(
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        status=status,
        owner=owner,
        team=team
    )
    return project


def update_project_service(project, **kwargs):
    """
    Update an existing project.
    """
    for key, value in kwargs.items():
        setattr(project, key, value)
    project.save()
    return project


def delete_project_service(project):
    """
    Delete a project.
    """
    project.delete()


def get_user_projects_service(user):
    """
    Get all projects for a user (owned projects and team projects).
    """
    # Get user's team memberships
    from teams.models import TeamMembership
    user_team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
    
    # Get projects owned by user or in user's teams
    return Project.objects.filter(
        models.Q(owner=user) | models.Q(team_id__in=user_team_ids)
    ).select_related('owner', 'team').distinct()


def get_team_projects_service(team):
    """
    Get all projects for a specific team.
    """
    return Project.objects.filter(team=team).select_related('owner')


def get_project_by_id_service(project_id):
    """
    Get a project by ID.
    """
    try:
        return Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return None
