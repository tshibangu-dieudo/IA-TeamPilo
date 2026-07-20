from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import models
from django.http import Http404

from apps.projects.models import Project
from .models import Recommendation
from .serializers import RecommendationSerializer
from .permissions import IsRecommendationProjectOwner
from .services import (
    generate_recommendations_for_project_service,
    accept_recommendation_service,
    dismiss_recommendation_service
)


class RecommendationViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing AI-driven task reassignment recommendations.
    Supported operations:
      - GET /api/recommendations/ (list pending)
      - GET /api/recommendations/{id}/ (detail)
      - GET /api/recommendations/project/{project_id}/ (list recommendations for project)
      - POST /api/recommendations/generate/ (trigger AI detection and recommendation creation)
      - PATCH /api/recommendations/{id}/accept/ (apply suggested reassignments)
      - PATCH /api/recommendations/{id}/dismiss/ (archive recommendation)
    """
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated, IsRecommendationProjectOwner]

    def get_queryset(self):
        """
        Filter recommendations based on role-based visibility rules (BR-7.1, BR-7.2).
        PM sees recommendations for projects they own.
        Executives see all recommendations.
        Team Members see recommendations for projects they belong to.
        """
        user = self.request.user
        
        # Scoped queryset base
        base_qs = Recommendation.objects.all().select_related(
            'project', 'task', 'current_assignee', 'suggested_assignee'
        )

        if user.role in ['admin', 'executive_manager']:
            return base_qs
            
        elif user.role == 'project_manager':
            # Retrieve team IDs where the PM is the lead
            from apps.teams.models import TeamMembership
            managed_teams = TeamMembership.objects.filter(user=user, role='lead').values_list('team_id', flat=True)
            
            # Show if they own the project or lead the project's team
            return base_qs.filter(
                models.Q(project__owner=user) | 
                models.Q(project__team_id__in=managed_teams)
            ).distinct()
            
        else:
            # Team Member: only see recommendations within projects they belong to
            from apps.teams.models import TeamMembership
            user_teams = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
            return base_qs.filter(project__team_id__in=user_teams).distinct()

    def list(self, request, *args, **kwargs):
        """
        Override list to default to status=pending, allowing query parameter overrides.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        status_param = request.query_params.get('status', 'pending')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='project/(?P<project_id>[^/.]+)')
    def project_recommendations(self, request, project_id=None):
        """
        GET /api/recommendations/project/{project_id}/
        List all recommendations related to a specific project.
        """
        # Validate that project exists and is in user scope
        project = get_object_or_404(Project, id=project_id)
        
        # Scope validation: return 404 (Http404) if user is not authorized to see project (BR-7.1)
        user = request.user
        if user.role not in ['admin', 'executive_manager']:
            if user.role == 'project_manager':
                is_owner = project.owner == user
                is_lead = project.team.memberships.filter(user=user, role='lead').exists()
                if not (is_owner or is_lead):
                    raise Http404("Project not found or outside user scope.")
            else:
                is_member = project.team.memberships.filter(user=user).exists()
                if not is_member:
                    raise Http404("Project not found or outside user scope.")

        recos = self.get_queryset().filter(project=project)
        
        status_param = request.query_params.get('status')
        if status_param:
            recos = recos.filter(status=status_param)
            
        serializer = self.get_serializer(recos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        POST /api/recommendations/generate/
        Trigger AI recommendation generation for a project.
        """
        project_id = request.data.get('project_id')
        if not project_id:
            return Response(
                {"error": "project_id is required in the request body."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        project = get_object_or_404(Project, id=project_id)
        
        # Scope validation: PM must manage/own project (BR-7.1)
        user = request.user
        if user.role not in ['admin', 'executive_manager']:
            if user.role == 'project_manager':
                is_owner = project.owner == user
                is_lead = project.team.memberships.filter(user=user, role='lead').exists()
                if not (is_owner or is_lead):
                    raise Http404("Project not found or outside user scope.")
            else:
                raise Http404("Project not found or outside user scope.")

        generated_recos = generate_recommendations_for_project_service(project)
        serializer = self.get_serializer(generated_recos, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def accept(self, request, pk=None):
        """
        PATCH /api/recommendations/{id}/accept/
        Apply task reassignment.
        """
        recommendation = self.get_object()
        self.check_object_permissions(request, recommendation)
        
        try:
            updated_reco = accept_recommendation_service(recommendation, request.user)
            serializer = self.get_serializer(updated_reco)
            return Response(serializer.data)
        except ValueError as err:
            return Response({"error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def dismiss(self, request, pk=None):
        """
        PATCH /api/recommendations/{id}/dismiss/
        Dismiss/reject the recommendation.
        """
        recommendation = self.get_object()
        self.check_object_permissions(request, recommendation)
        
        try:
            updated_reco = dismiss_recommendation_service(recommendation, request.user)
            serializer = self.get_serializer(updated_reco)
            return Response(serializer.data)
        except ValueError as err:
            return Response({"error": str(err)}, status=status.HTTP_400_BAD_REQUEST)
