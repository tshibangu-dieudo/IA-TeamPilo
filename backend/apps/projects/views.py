from rest_framework import viewsets
from .models import Project


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Project management.
    """
    queryset = Project.objects.all()
