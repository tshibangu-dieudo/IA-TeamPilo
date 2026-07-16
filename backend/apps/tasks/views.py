from rest_framework import viewsets
from .models import Task, TaskDependency, TaskStatusHistory


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Task management.
    """
    queryset = Task.objects.all()


class TaskDependencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TaskDependency management.
    """
    queryset = TaskDependency.objects.all()


class TaskStatusHistoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TaskStatusHistory management.
    """
    queryset = TaskStatusHistory.objects.all()
