"""
Views for teams app.
See .ai/coding-rules.md: Views stay thin - validate request, call service, return response.
"""
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Team, Skill, TeamMembership
from .serializers import (
    TeamSerializer, TeamDetailSerializer, SkillSerializer,
    TeamMembershipSerializer, TeamMembershipCreateSerializer
)
from .services import (
    create_team_service, add_team_member_service, remove_team_member_service,
    update_team_member_role_service, create_skill_service, get_user_teams_service
)
from .permissions import IsTeamMember, IsTeamLead, IsTeamLeadOrReadOnly, CanManageTeamMembership


class TeamViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Team management.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see teams they are members of
        user = self.request.user
        user_team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
        return Team.objects.filter(id__in=user_team_ids)
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return TeamDetailSerializer
        return TeamSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = create_team_service(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', '')
        )
        # Creator becomes team lead
        add_team_member_service(team, request.user, role='lead')
        return Response(
            TeamDetailSerializer(team).data,
            status=status.HTTP_201_CREATED,
        )


class SkillViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Skill management.
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        return create_skill_service(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', '')
        )


class TeamMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TeamMembership management.
    """
    permission_classes = [IsAuthenticated, CanManageTeamMembership]
    
    def get_queryset(self):
        # Only show memberships for teams the user is a member of
        user = self.request.user
        user_team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
        return TeamMembership.objects.filter(team_id__in=user_team_ids)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TeamMembershipCreateSerializer
        return TeamMembershipSerializer
    
    def perform_create(self, serializer):
        return add_team_member_service(
            team=serializer.validated_data['team'],
            user=serializer.validated_data['user'],
            role=serializer.validated_data.get('role', 'member')
        )
    
    def perform_update(self, serializer):
        return update_team_member_role_service(
            team=serializer.instance.team,
            user=serializer.instance.user,
            new_role=serializer.validated_data.get('role', serializer.instance.role)
        )
    
    def perform_destroy(self, instance):
        return remove_team_member_service(instance.team, instance.user)


class MyTeamsView(generics.ListAPIView):
    """
    Get all teams for the current user.
    """
    serializer_class = TeamDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return get_user_teams_service(self.request.user)
