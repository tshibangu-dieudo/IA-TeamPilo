from rest_framework import viewsets
from .models import Team, Skill, TeamMembership


class TeamViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Team management.
    """
    queryset = Team.objects.all()


class SkillViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Skill management.
    """
    queryset = Skill.objects.all()


class TeamMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TeamMembership management.
    """
    queryset = TeamMembership.objects.all()
