"""
Serializers for notifications app.
See docs/14_REST_API.md §9 for the expected response shape.
"""
from rest_framework import serializers
from .models import Notification


class NotificationProjectSerializer(serializers.Serializer):
    """Minimal project representation nested inside a notification."""
    id = serializers.UUIDField()
    name = serializers.CharField()


class NotificationTaskSerializer(serializers.Serializer):
    """Minimal task representation nested inside a notification."""
    id = serializers.UUIDField()
    title = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):
    """
    Full notification serializer.
    Response shape per docs/14_REST_API.md §9:
      id, notification_type, title, message, is_read, read_at, created_at,
      project (id + name | null), task (id + title | null).
    """
    project = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'read_at',
            'created_at',
            'project',
            'task',
        ]
        read_only_fields = fields

    def get_project(self, obj):
        if obj.project_id is None:
            return None
        return NotificationProjectSerializer(obj.project).data

    def get_task(self, obj):
        if obj.task_id is None:
            return None
        return NotificationTaskSerializer(obj.task).data
