"""
Views for projects app.
See .ai/coding-rules.md: Views stay thin - validate request, call service, return response.
"""
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer, ProjectCreateSerializer, ProjectDetailSerializer
from .services import (
    create_project_service, update_project_service, delete_project_service,
    get_user_projects_service, get_project_by_id_service
)
from .permissions import IsTeamMember, IsProjectOwnerOrTeamLeadOrReadOnly


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Project management.
    """
    permission_classes = [IsAuthenticated, IsProjectOwnerOrTeamLeadOrReadOnly]
    
    def get_queryset(self):
        # Users can only see projects they own or are team members of
        return get_user_projects_service(self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return ProjectDetailSerializer
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        return create_project_service(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            owner=self.request.user,
            team=serializer.validated_data['team'],
            status=serializer.validated_data.get('status', 'planning')
        )
    
    def perform_update(self, serializer):
        return update_project_service(serializer.instance, **serializer.validated_data)
    
    def perform_destroy(self, instance):
        return delete_project_service(instance)


class MyProjectsView(generics.ListAPIView):
    """
    Get all projects for the current user.
    """
    serializer_class = ProjectDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return get_user_projects_service(self.request.user)
