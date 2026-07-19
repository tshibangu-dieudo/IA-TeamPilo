"""
Serializers for tasks app.
See .ai/coding-rules.md: Views stay thin — serializers handle data validation.
See docs/14_REST_API.md §6 for request/response shapes.
"""
from rest_framework import serializers

from .models import Task, TaskDependency, TaskStatusHistory


class TaskStatusHistorySerializer(serializers.ModelSerializer):
    """Read-only serializer for status history entries."""
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model = TaskStatusHistory
        fields = [
            'id', 'previous_status', 'new_status',
            'changed_by', 'changed_by_username', 'changed_at',
        ]
        read_only_fields = ['id', 'changed_at']


class TaskDependencySerializer(serializers.ModelSerializer):
    """Serializer for task dependency relationships."""
    depends_on_task_title = serializers.CharField(
        source='depends_on_task.title', read_only=True
    )

    class Meta:
        model = TaskDependency
        fields = ['id', 'task', 'depends_on_task', 'depends_on_task_title', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    """
    Full serializer for Task — used for list and detail responses.
    """
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'project_name', 'assignee', 'assignee_username',
            'title', 'description', 'priority', 'status',
            'estimated_effort_hours', 'deadline',
            'blocked_reason', 'blocked_at', 'unassigned_since',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'blocked_at', 'unassigned_since', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used when creating a task.
    project is injected from the URL — not supplied in the body.
    """
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority',
            'estimated_effort_hours', 'deadline', 'assignee',
        ]

    def validate_estimated_effort_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("Estimated effort hours must be greater than zero.")
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for partial task updates (PATCH).
    Does not expose status — use TaskStatusUpdateSerializer for that.
    """
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority',
            'estimated_effort_hours', 'deadline', 'assignee',
        ]

    def validate_estimated_effort_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("Estimated effort hours must be greater than zero.")
        return value


class TaskStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for PATCH /tasks/{id}/status.
    See docs/14_REST_API.md §6.
    BR-3.1: blocked_reason required when status == 'blocked'.
    """
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('waiting_on_dependency', 'Waiting on Dependency'),
        ('done', 'Done'),
    ]

    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    blocked_reason = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if attrs['status'] == 'blocked' and not attrs.get('blocked_reason', '').strip():
            raise serializers.ValidationError(
                {'blocked_reason': 'blocked_reason is required when status is "blocked".'}
            )
        return attrs


class AddDependencySerializer(serializers.Serializer):
    """
    Serializer for POST /tasks/{id}/dependencies.
    See docs/14_REST_API.md §6.
    """
    depends_on_task_id = serializers.UUIDField()
