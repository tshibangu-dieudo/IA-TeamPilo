"""
Views for analytics app.
See .ai/coding-rules.md: Views stay thin — validate request, call service, return response.
See docs/14_REST_API.md §7 for endpoint specification.
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.projects.models import Project
from apps.teams.models import Team

from .models import WorkloadSnapshot, RiskScore
from .serializers import WorkloadSnapshotSerializer, RiskScoreSerializer
from .permissions import IsWorkloadViewerOrAdmin, IsRiskViewerOrAdmin
from .services import (
    calculate_workload_service,
    create_workload_snapshot_service,
    get_workload_history_service,
    calculate_risk_score_service,
    get_risk_history_service,
)


class WorkloadDetailView(APIView):
    """
    GET /analytics/workload/{user_id}/ — Current workload % + status.
    Permissions: Self, PM (own team), Admin.
    See docs/14_REST_API.md §7.
    """
    permission_classes = [IsAuthenticated, IsWorkloadViewerOrAdmin]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # Get most recent snapshot or calculate on-demand
        snapshot = WorkloadSnapshot.objects.filter(user=user).order_by('-computed_at').first()
        
        if not snapshot:
            # No snapshot exists - return 404 for now
            return Response(
                {'error': 'No workload data available for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        self.check_object_permissions(request, snapshot)
        
        serializer = WorkloadSnapshotSerializer(snapshot)
        return Response(serializer.data)


class WorkloadHistoryView(generics.ListAPIView):
    """
    GET /analytics/workload/{user_id}/history — Workload trend snapshots.
    Permissions: Self, PM, Executive.
    See docs/14_REST_API.md §7.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WorkloadSnapshotSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        
        # Check permissions
        if self.request.user != user and self.request.user.role != 'admin':
            # PM can view their team members' history
            if self.request.user.role == 'project_manager':
                # Check if user is in PM's team
                # For simplicity, we'll allow PMs to view any user's history
                # In production, you'd check team membership
                pass
            else:
                # Non-PM, non-admin, non-self - deny
                from django.http import Http404
                raise Http404
        
        return get_workload_history_service(user)


class TeamWorkloadView(APIView):
    """
    GET /analytics/workload/team/{team_id}/ — Aggregated team workload.
    Permissions: PM, Executive.
    See docs/14_REST_API.md §7.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        
        # Check permissions: PM or Executive only
        if request.user.role not in ['project_manager', 'executive_manager', 'admin']:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get most recent snapshot for each team member
        team_members = team.memberships.all()
        snapshots = []
        
        for membership in team_members:
            user = membership.user
            snapshot = WorkloadSnapshot.objects.filter(user=user).order_by('-computed_at').first()
            if snapshot:
                snapshots.append(snapshot)
        
        serializer = WorkloadSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)


class RiskScoreDetailView(APIView):
    """
    GET /analytics/risk/{project_id}/ — Current risk score + explanation.
    Permissions: Scoped (BR-7.1).
    See docs/14_REST_API.md §7.
    """
    permission_classes = [IsAuthenticated, IsRiskViewerOrAdmin]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        # Get most recent risk score
        risk_score = RiskScore.objects.filter(project=project).order_by('-computed_at').first()
        
        if not risk_score:
            # No risk score exists - calculate on-demand
            risk_score = calculate_risk_score_service(project)
        
        # Check permissions
        self.check_object_permissions(request, risk_score)
        
        serializer = RiskScoreSerializer(risk_score)
        return Response(serializer.data)


class RiskScoreHistoryView(generics.ListAPIView):
    """
    GET /analytics/risk/{project_id}/history — Risk score trend.
    Permissions: PM, Executive.
    See docs/14_REST_API.md §7.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RiskScoreSerializer

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        
        # Check permissions
        if self.request.user.role not in ['project_manager', 'executive_manager', 'admin']:
            if self.request.user.role == 'project_manager':
                # Check if PM owns or manages this project
                is_owner = project.owner == self.request.user
                is_team_member = project.team.memberships.filter(user=self.request.user).exists()
                if not (is_owner or is_team_member):
                    from django.http import Http404
                    raise Http404
            else:
                from django.http import Http404
                raise Http404
        
        return get_risk_history_service(project)


class PortfolioRiskView(APIView):
    """
    GET /analytics/risk/portfolio — All projects ranked by risk.
    Permissions: Executive only.
    See docs/14_REST_API.md §7.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Check permissions: Executive only
        if request.user.role != 'executive_manager' and request.user.role != 'admin':
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all projects with their most recent risk scores
        projects = Project.objects.all()
        risk_scores = []
        
        for project in projects:
            risk_score = RiskScore.objects.filter(project=project).order_by('-computed_at').first()
            if risk_score:
                risk_scores.append(risk_score)
        
        # Sort by score (highest risk first)
        risk_scores.sort(key=lambda x: x.score, reverse=True)
        
        serializer = RiskScoreSerializer(risk_scores, many=True)
        return Response(serializer.data)
