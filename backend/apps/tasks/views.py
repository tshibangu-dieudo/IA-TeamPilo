"""
Views for tasks app.
See .ai/coding-rules.md: Views stay thin — validate request, call service, return response.
See docs/14_REST_API.md §6 for endpoint specification.
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.projects.models import Project
from .models import Task, TaskDependency
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskStatusUpdateSerializer,
    TaskDependencySerializer,
    TaskStatusHistorySerializer,
    AddDependencySerializer,
)
from .permissions import (
    IsProjectMemberOrReadOnly,
    IsTaskAssigneeOrProjectOwner,
    IsProjectOwner,
)
from .services import (
    create_task_service,
    update_task_service,
    update_task_status_service,
    get_tasks_for_project_service,
    get_task_by_id_service,
    get_tasks_for_user_service,
    add_task_dependency_service,
    remove_task_dependency_service,
    get_task_status_history_service,
)


def _get_scoped_project(project_id, user):
    """
    Return a Project the user is entitled to see, or 404.
    BR-7.1: scope violations return 404 to avoid leaking existence.
    """
    project = get_object_or_404(Project, id=project_id)
    is_owner = project.owner == user
    is_member = project.team.memberships.filter(user=user).exists()
    if not (is_owner or is_member):
        from django.http import Http404
        raise Http404
    return project


class ProjectTaskListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/projects/{project_id}/tasks/  — list tasks for a project.
    POST /api/projects/{project_id}/tasks/  — create a task (PM only).
    See docs/14_REST_API.md §6.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        project = _get_scoped_project(self.kwargs['project_id'], self.request.user)
        return get_tasks_for_project_service(project)

    def create(self, request, *args, **kwargs):
        project = _get_scoped_project(self.kwargs['project_id'], request.user)

        # Only the project owner (PM) may create tasks
        if project.owner != request.user:
            return Response(
                {'error': 'Only the project owner may create tasks.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = create_task_service(
            project=project,
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            priority=serializer.validated_data.get('priority', 'medium'),
            estimated_effort_hours=serializer.validated_data['estimated_effort_hours'],
            deadline=serializer.validated_data['deadline'],
            assignee=serializer.validated_data.get('assignee'),
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/tasks/{id}/  — task detail (scoped).
    PATCH  /api/tasks/{id}/  — update task fields (PM only).
    DELETE /api/tasks/{id}/  — delete task (PM only).
    See docs/14_REST_API.md §6.
    """
    permission_classes = [IsAuthenticated, IsProjectMemberOrReadOnly]
    serializer_class = TaskSerializer

    def get_object(self):
        task = get_object_or_404(Task, id=self.kwargs['pk'])
        self.check_object_permissions(self.request, task)
        return task

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TaskUpdateSerializer
        return TaskSerializer

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = TaskUpdateSerializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        updated_task = update_task_service(task, request.user, **serializer.validated_data)
        return Response(TaskSerializer(updated_task).data)


class TaskStatusUpdateView(APIView):
    """
    PATCH /api/tasks/{id}/status/  — update status (Assignee or PM).
    See docs/14_REST_API.md §6.
    BR-3.1: blocked_reason required when status == 'blocked'.
    """
    permission_classes = [IsAuthenticated, IsTaskAssigneeOrProjectOwner]

    def get_object(self, pk):
        task = get_object_or_404(Task, id=pk)
        self.check_object_permissions(self.request, task)
        return task

    def patch(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_task = update_task_status_service(
                task=task,
                new_status=serializer.validated_data['status'],
                changed_by=request.user,
                blocked_reason=serializer.validated_data.get('blocked_reason', ''),
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(TaskSerializer(updated_task).data)


class TaskDependencyListCreateView(APIView):
    """
    GET  /api/tasks/{id}/dependencies/  — list dependencies (scoped).
    POST /api/tasks/{id}/dependencies/  — add a prerequisite (PM only).
    See docs/14_REST_API.md §6.
    """
    permission_classes = [IsAuthenticated]

    def _get_task(self, pk, user):
        task = get_object_or_404(Task, id=pk)
        # scope: PM or team member
        _get_scoped_project(str(task.project_id), user)
        return task

    def get(self, request, pk):
        task = self._get_task(pk, request.user)
        deps = TaskDependency.objects.filter(task=task).select_related('depends_on_task')
        return Response(TaskDependencySerializer(deps, many=True).data)

    def post(self, request, pk):
        task = self._get_task(pk, request.user)

        # Only the project owner (PM) may add dependencies
        if task.project.owner != request.user:
            return Response(
                {'error': 'Only the project owner may manage task dependencies.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AddDependencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        depends_on_task = get_object_or_404(
            Task, id=serializer.validated_data['depends_on_task_id']
        )

        try:
            dependency = add_task_dependency_service(task, depends_on_task)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(
            TaskDependencySerializer(dependency).data,
            status=status.HTTP_201_CREATED,
        )


class TaskDependencyDeleteView(APIView):
    """
    DELETE /api/tasks/{task_id}/dependencies/{dep_task_id}/
    Remove a prerequisite dependency (PM only).
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, dep_pk):
        task = get_object_or_404(Task, id=pk)

        if task.project.owner != request.user:
            return Response(
                {'error': 'Only the project owner may remove task dependencies.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        depends_on_task = get_object_or_404(Task, id=dep_pk)
        remove_task_dependency_service(task, depends_on_task)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskStatusHistoryView(generics.ListAPIView):
    """
    GET /api/tasks/{id}/history/  — status change history (scoped).
    See docs/14_REST_API.md §6.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskStatusHistorySerializer

    def get_queryset(self):
        task = get_object_or_404(Task, id=self.kwargs['pk'])
        # Scope check
        _get_scoped_project(str(task.project_id), self.request.user)
        return get_task_status_history_service(task)


class MyTasksView(generics.ListAPIView):
    """
    GET /api/tasks/me/  — current user's assigned tasks.
    See docs/14_REST_API.md §6 (US-3.3).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return get_tasks_for_user_service(self.request.user)
